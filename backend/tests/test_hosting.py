import time
import pytest
from fastapi.testclient import TestClient
from app.config import Config
from app.main import create_app

def settings(tmp_path,**extra):
    return Config(_env_file=None,data_dir=tmp_path,app_mode='hosted',public_app_url='https://recall.example',google_client_id='test-client',google_client_secret='test-secret',session_secret='test-only-session-secret-longer-than-32-characters',allowed_emails=['owner@example.test','other@example.test'],openai_api_key='test-key',**extra)

def hosted(tmp_path):
    app=create_app(settings(tmp_path));return app,TestClient(app,base_url='https://recall.example')

def login(app,client,sub='account-one',email='owner@example.test'):
    token,csrf=app.state.sessions.issue(sub,email)
    client.cookies.set('recall_session',token,domain='recall.example',path='/')
    return {'X-CSRF-Token':csrf,'Origin':'https://recall.example'}

def test_hosted_mode_fails_closed_without_credentials(tmp_path):
    with pytest.raises(ValueError,match='hosted|Hosted'):
        create_app(Config(_env_file=None,data_dir=tmp_path,app_mode='hosted'))

def test_signed_out_requests_cannot_read_library_or_upload(tmp_path):
    app,client=hosted(tmp_path)
    assert client.get('/api/lectures').status_code==401
    assert client.get('/api/lectures/anything/media').status_code==401
    assert client.post('/api/lectures/upload',files={'video':('lecture.mp4',b'private')}).status_code==401
    assert not list(tmp_path.rglob('*.mp4'))

def test_each_google_account_owns_a_separate_library_and_media(tmp_path):
    app,one=hosted(tmp_path);two=TestClient(app,base_url='https://recall.example')
    h1=login(app,one);h2=login(app,two,'account-two','other@example.test')
    created=one.post('/api/lectures/upload',files={'video':('lesson.mp4',b'private video')},headers=h1)
    assert created.status_code==200
    id=created.json()['lecture_id'];job=created.json()['job_id']
    assert len(one.get('/api/lectures').json())==1
    assert two.get('/api/lectures').json()==[]
    assert two.get('/api/lectures/'+id).status_code==404
    assert two.get('/api/lectures/'+id+'/media').status_code==404
    assert two.post('/api/jobs/'+job+'/retry',headers=h2).status_code==404
    assert one.get('/api/lectures/'+id+'/media').content==b'private video'

def test_hosted_csrf_and_origin_reject_unauthorized_mutations(tmp_path):
    app,client=hosted(tmp_path);headers=login(app,client)
    body={'url':'https://youtu.be/C842vFY5kRo'}
    assert client.post('/api/lectures/youtube',json=body).status_code==403
    assert client.post('/api/lectures/youtube',json=body,headers={**headers,'Origin':'https://recall.example.attacker.test'}).status_code==403
    assert client.post('/api/lectures/youtube',json=body,headers={**headers,'X-CSRF-Token':'tampered'}).status_code==403
    assert client.post('/api/lectures/youtube',json=body,headers=headers).status_code==200

def test_logout_revokes_replayed_session_and_cookies_are_secure(tmp_path):
    app,client=hosted(tmp_path);headers=login(app,client);token=client.cookies.get('recall_session')
    response=client.post('/auth/logout',headers=headers)
    assert response.status_code==200
    client.cookies.set('recall_session',token,domain='recall.example',path='/')
    assert client.get('/api/lectures').status_code==401

def test_removed_invitation_and_expired_session_cannot_access_library(tmp_path):
    app,client=hosted(tmp_path);login(app,client)
    app.state.config.allowed_emails=['other@example.test']
    assert client.get('/api/lectures').status_code==401
    app.state.config.allowed_emails=['owner@example.test']
    with app.state.sessions.connection() as db:db.execute('UPDATE sessions SET expires=0')
    assert client.get('/api/lectures').status_code==401

def test_only_configured_hosts_are_allowed(tmp_path):
    app,client=hosted(tmp_path);login(app,client)
    assert client.get('/api/lectures',headers={'Host':'attacker.test'}).status_code==400
