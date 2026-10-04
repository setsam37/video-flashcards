from test_hosting import hosted,login
from test_google_login import provider,start,signing_key

PAGES={'Origin':'https://setsam37.github.io'}
VIDEO='https://youtu.be/C842vFY5kRo'

def test_handoff_is_bounded_and_only_accepted_from_the_entry_page(tmp_path):
    app,client=hosted(tmp_path)
    for headers in [{},{'Origin':'https://attacker.example'}]:
        assert client.post('/start',data={'url':VIDEO},headers=headers).status_code==403
    assert client.post('/start',json={'url':VIDEO},headers=PAGES).status_code==415
    assert client.post('/start',data={'url':'x'*4097},headers=PAGES).status_code==413
    assert client.post('/start',data={'url':'https://example.com/video'},headers=PAGES).status_code==422
    assert client.get('/start').status_code==405
    assert not list(tmp_path.glob('accounts/*/study.sqlite'))

def test_pages_handoff_waits_for_google_and_is_imported_once(tmp_path,signing_key):
    app,client=hosted(tmp_path);context=provider(app,signing_key)
    response=client.post('/start',data={'url':VIDEO},headers=PAGES,follow_redirects=False)
    assert response.status_code==303 and response.headers['location']=='/'
    assert not list(tmp_path.glob('accounts/*/study.sqlite'))
    response=client.get(start(client,context),follow_redirects=False)
    session=client.get('/auth/session').json()
    assert session['pending'] is True
    headers={'X-CSRF-Token':session['csrf_token'],'Origin':'https://recall.example'}
    one=client.post('/api/handoff',headers=headers);two=client.post('/api/handoff',headers=headers)
    assert one.status_code==200 and one.json()==two.json()
    assert len(client.get('/api/lectures').json())==1
    assert len(client.get('/api/lectures/'+one.json()['lecture_id']).json()['jobs'])==1
    assert client.get('/auth/session').json()['pending'] is False

def test_already_signed_in_pages_handoff_still_requires_csrf(tmp_path):
    app,client=hosted(tmp_path);headers=login(app,client)
    response=client.post('/start',data={'url':VIDEO},headers=PAGES,follow_redirects=False)
    assert response.headers['location']=='/'
    assert client.post('/api/handoff').status_code==403
    assert client.post('/api/handoff',headers=headers).status_code==200

def test_cross_site_post_without_lax_cookie_returns_to_session_aware_get(tmp_path):
    app,client=hosted(tmp_path);login(app,client)
    token=client.cookies.get('recall_session');client.cookies.clear()
    # Browsers withhold SameSite=Lax session cookies on cross-site POSTs.
    response=client.post('/start',data={'url':VIDEO},headers=PAGES,follow_redirects=False)
    assert response.headers['location']=='/'
    client.cookies.set('recall_session',token,domain='recall.example',path='/')
    session=client.get('/auth/session').json()
    assert session['authenticated'] and session['pending']
