import time
from urllib.parse import urlparse,parse_qs
import httpx2 as httpx
import pytest
from joserfc import jwt
from joserfc.jwk import RSAKey
from test_hosting import hosted

@pytest.fixture(scope='module')
def signing_key():return RSAKey.generate_key(2048)

def provider(app,signing_key,change=None):
    context={}
    def transport(request):
        if request.url.path.endswith('openid-configuration'):
            return httpx.Response(200,json={'issuer':'https://accounts.google.com','authorization_endpoint':'https://accounts.google.com/authorize','token_endpoint':'https://accounts.google.com/token','jwks_uri':'https://accounts.google.com/keys','id_token_signing_alg_values_supported':['RS256']})
        if request.url.path=='/keys':return httpx.Response(200,json={'keys':[signing_key.as_dict(private=False)]})
        assert request.url.path=='/token'
        claims={'iss':'https://accounts.google.com','aud':'test-client','sub':'google-account-one','iat':int(time.time()),'exp':int(time.time())+600,'nonce':context['nonce'],'email':'owner@example.test','email_verified':True}
        if change:claims.update(change)
        signed=jwt.encode({'alg':'RS256'},claims,signing_key)
        return httpx.Response(200,json={'access_token':'test-access','token_type':'Bearer','expires_in':600,'id_token':signed})
    app.state.oauth.google.client_kwargs['transport']=httpx.MockTransport(transport)
    return context

def start(client,context):
    response=client.get('/auth/login',follow_redirects=False)
    assert response.status_code==302
    query=parse_qs(urlparse(response.headers['location']).query)
    assert query['redirect_uri']==['https://recall.example/auth/callback']
    assert query['code_challenge_method']==['S256']
    context['nonce']=query['nonce'][0]
    return '/auth/callback?code=test-code&state='+query['state'][0]

def test_real_oidc_verification_issues_secure_session_and_rejects_state_replay(tmp_path,signing_key):
    app,client=hosted(tmp_path);context=provider(app,signing_key)
    callback=start(client,context);old_cookie=client.cookies.get('recall_oauth')
    response=client.get(callback,follow_redirects=False)
    assert response.status_code==303 and response.headers['location']=='/'
    cookies=response.headers.get_list('set-cookie')
    assert any('recall_session=' in cookie and all(flag in cookie for flag in ['Secure','HttpOnly','SameSite=lax']) for cookie in cookies)
    assert client.get('/auth/session').json()['email']=='owner@example.test'
    client.cookies.clear();client.cookies.set('recall_oauth',old_cookie,domain='recall.example',path='/')
    replay=client.get(callback,follow_redirects=False)
    assert replay.headers['location']=='/?signin=failed'
    assert client.get('/api/lectures').status_code==401

@pytest.mark.parametrize('change',[{'aud':'wrong-client'},{'iss':'https://attacker.example'},{'exp':int(time.time())-600},{'nonce':'wrong'},{'email_verified':False},{'email':'uninvited@example.test'}])
def test_invalid_google_claims_never_grant_access(tmp_path,signing_key,change):
    app,client=hosted(tmp_path);context=provider(app,signing_key,change)
    response=client.get(start(client,context),follow_redirects=False)
    assert response.status_code in [303,403]
    assert not client.cookies.get('recall_session')
    assert client.get('/api/lectures').status_code==401

def test_invalid_signature_never_grants_access(tmp_path,signing_key):
    app,client=hosted(tmp_path);context=provider(app,RSAKey.generate_key(2048))
    app.state.oauth.google.server_metadata['jwks']={'keys':[signing_key.as_dict(private=False)]}
    # The key endpoint must also keep returning the trusted public key.
    original=app.state.oauth.google.client_kwargs['transport']
    def transport(request):
        if request.url.path=='/keys':return httpx.Response(200,json={'keys':[signing_key.as_dict(private=False)]})
        return original.handle_request(request)
    app.state.oauth.google.client_kwargs['transport']=httpx.MockTransport(transport)
    response=client.get(start(client,context),follow_redirects=False)
    assert response.status_code==303
    assert client.get('/api/lectures').status_code==401
