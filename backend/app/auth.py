import hashlib,hmac
from urllib.parse import urlparse,parse_qs
from fastapi import APIRouter,Request,HTTPException
from fastapi.responses import JSONResponse,RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.base_client.errors import OAuthError
from joserfc.errors import JoseError
from httpx2 import HTTPError
from .sessions import SessionStore,COOKIE
from .storage import Repository

router=APIRouter(prefix='/auth')

def permitted(config,email):return config.public_signup or email.lower() in config.allowed_emails

def workspace(config,sub):
    return config.model_copy(update={'data_dir':config.data_dir/'accounts'/hashlib.sha256(sub.encode()).hexdigest()}).prepare()

def install_security(app,config):
    hosted=config.app_mode=='hosted'
    if hosted:
        app.state.sessions=SessionStore(config.data_dir/'auth.sqlite')
        oauth=OAuth()
        oauth.register('google',client_id=config.google_client_id,client_secret=config.google_client_secret.get_secret_value(),server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',client_kwargs={'scope':'openid email','code_challenge_method':'S256'})
        app.state.oauth=oauth
    @app.middleware('http')
    async def protect(request,call_next):
        request.state.user=None
        if hosted:
            user=app.state.sessions.get(request.cookies.get(COOKIE))
            if user and permitted(config,user['email']):request.state.user=user
            private=request.url.path.startswith('/api/') and request.url.path!='/api/health' or request.url.path=='/auth/logout'
            if private:
                if not request.state.user:return JSONResponse(status_code=401,content={'detail':'Sign in with Google to open your library.'})
                scoped=workspace(config,user['sub']);request.state.config=scoped;request.state.repository=Repository(scoped.data_dir/'study.sqlite')
                if request.method not in ['GET','HEAD','OPTIONS']:
                    supplied=request.headers.get('X-CSRF-Token','')
                    if not hmac.compare_digest(supplied,user['csrf']):return JSONResponse(status_code=403,content={'detail':'Reload the app before trying again.'})
        origin=request.headers.get('origin')
        if request.method not in ['GET','HEAD','OPTIONS'] and origin:
            try:
                parsed=urlparse(origin)
                allowed=origin==config.public_app_url or (request.url.path=='/start' and origin==config.pages_origin) if hosted else parsed.scheme in ['http','https'] and parsed.hostname in ['127.0.0.1','localhost','testserver'] and parsed.port in [None,8000,5173,request.url.port]
            except ValueError:allowed=False
            if not allowed:return JSONResponse(status_code=403,content={'detail':'Requests from that origin are not accepted.'})
        response=await call_next(request)
        if hosted:
            response.headers['Referrer-Policy']='no-referrer'
            if request.url.path.startswith(('/api/','/auth/')):response.headers['Cache-Control']='no-store'
        return response
    hosts=[urlparse(config.public_app_url).hostname,'127.0.0.1','localhost'] if hosted else ['127.0.0.1','localhost','testserver']
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=hosts)
    if hosted:app.add_middleware(SessionMiddleware,secret_key=config.session_secret.get_secret_value(),session_cookie='recall_oauth',max_age=600,same_site='lax',https_only=True)
    app.include_router(router)

@router.get('/session')
def session(request:Request):
    if request.app.state.config.app_mode=='local':return {'hosted':False,'authenticated':True}
    user=request.state.user
    if not user:return {'hosted':True,'authenticated':False}
    from .handoff import pending_handoff
    pending=pending_handoff(request)
    if pending:
        repo=Repository(workspace(request.app.state.config,user['sub']).data_dir/'study.sqlite')
        pending=not repo.handoff_result(pending['id'])
    return {'hosted':True,'authenticated':True,'email':user['email'],'csrf_token':user['csrf'],'pending':bool(pending)}

@router.get('/login')
async def login(request:Request):
    config=request.app.state.config
    if config.app_mode!='hosted':raise HTTPException(404)
    pending=request.session.get('handoff');request.session.clear()
    if pending:request.session['handoff']=pending
    response=await request.app.state.oauth.google.authorize_redirect(request,config.public_app_url+'/auth/callback',prompt='select_account')
    state=parse_qs(urlparse(response.headers['location']).query)['state'][0]
    request.app.state.sessions.remember_state(state)
    return response

@router.get('/callback')
async def callback(request:Request):
    config=request.app.state.config
    if config.app_mode!='hosted':raise HTTPException(404)
    try:
        state=request.query_params.get('state')
        if not state or '_state_google_'+state not in request.session or not request.app.state.sessions.consume_state(state):
            request.session.clear();return RedirectResponse('/?signin=failed',status_code=303)
        token=await request.app.state.oauth.google.authorize_access_token(request)
        user=token.get('userinfo') or {}
        if user.get('email_verified') is not True or user.get('nonce_supported') is False or not isinstance(user.get('sub'),str) or not user['sub'] or not isinstance(user.get('email'),str) or not permitted(config,user['email']):
            request.session.clear();raise HTTPException(403,'This Google account has not been invited.')
    except (OAuthError,JoseError,HTTPError):
        request.session.clear();return RedirectResponse('/?signin=failed',status_code=303)
    pending=request.session.get('handoff');request.session.clear()
    if pending:request.session['handoff']=pending
    request.app.state.sessions.revoke(request.cookies.get(COOKIE))
    token,_=request.app.state.sessions.issue(user['sub'],user['email'])
    response=RedirectResponse('/',status_code=303)
    response.set_cookie(COOKIE,token,max_age=86400,secure=True,httponly=True,samesite='lax',path='/')
    return response

@router.post('/logout')
def logout(request:Request):
    if request.app.state.config.app_mode!='hosted':raise HTTPException(404)
    request.app.state.sessions.revoke(request.cookies.get(COOKIE));request.session.clear()
    response=JSONResponse({'signed_out':True});response.delete_cookie(COOKIE,path='/',secure=True,httponly=True,samesite='lax');return response
