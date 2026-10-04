import hashlib,os,shutil,time
import pytest
from fastapi.testclient import TestClient
from app.config import Config
from app.main import create_app
from app.auth import workspace
from app.jobs import JobQueue
from app.storage import Repository
from app.worker import WorkspaceWorker
from test_hosting import settings,login

def test_free_upload_route_rejects_before_reading_multipart(tmp_path):
    app=create_app(settings(tmp_path,video_uploads_enabled=False))
    client=TestClient(app,base_url='https://recall.example');headers=login(app,client)
    response=client.post('/api/lectures/upload',content=b'unparsed body',headers={**headers,'Content-Type':'multipart/form-data; boundary=invalid'})
    assert response.status_code==413
    assert 'local app' in response.json()['detail']
    assert not list(tmp_path.rglob('*.mp4'))

def test_disabled_uploads_keep_youtube_and_captions_working(tmp_path):
    app=create_app(settings(tmp_path,video_uploads_enabled=False))
    client=TestClient(app,base_url='https://recall.example');headers=login(app,client)
    response=client.post('/api/lectures/youtube',json={'url':'https://youtu.be/C842vFY5kRo'},headers=headers)
    assert response.status_code==200
    id=response.json()['lecture_id'];job=response.json()['job_id']
    scoped=workspace(app.state.config,'account-one');repo=Repository(scoped.data_dir/'study.sqlite')
    JobQueue(repo).fail(job,'captions_unavailable','Attach captions')
    response=client.post(f'/api/lectures/{id}/transcript',files={'transcript':('lesson.srt',b'1\n00:00:01,000 --> 00:00:03,000\nThis is taught.\n')},headers=headers)
    assert response.status_code==200
    assert repo.get_segments(id)[0].text=='This is taught.'
    response=client.post(f'/api/lectures/{id}/transcript',files={'transcript':('lesson.srt',b''),'video':('lecture.mp4',b'private')},headers=headers)
    assert response.status_code==413
    assert not list(tmp_path.rglob('*.mp4'))

def test_free_hosting_requires_durable_encrypted_database(tmp_path):
    with pytest.raises(ValueError,match='database|DATABASE_URL'):
        settings(tmp_path,ephemeral_hosting=True,video_uploads_enabled=False)
    with pytest.raises(ValueError,match='encrypted|TLS|sslmode'):
        settings(tmp_path,database_url='postgresql://postgres:fake@example.test/postgres?sslmode=disable')

def test_database_outage_returns_generic_response_without_credentials(tmp_path,monkeypatch):
    from app.database import DatabaseUnavailable
    app=create_app(settings(tmp_path));client=TestClient(app,base_url='https://recall.example')
    monkeypatch.setattr(app.state.sessions,'get',lambda _:(_ for _ in ()).throw(DatabaseUnavailable()))
    response=client.get('/api/lectures')
    assert response.status_code==503
    assert 'postgres' not in response.text and 'secret' not in response.text

def test_health_reports_video_upload_capability(tmp_path):
    app=create_app(settings(tmp_path));client=TestClient(app,base_url='https://recall.example');login(app,client)
    (tmp_path/'worker-heartbeat').write_text(str(time.time()))
    assert client.get('/api/health').json()['video_uploads_enabled'] is True

def test_free_caption_body_limit_rejects_large_and_chunked_requests(tmp_path):
    app=create_app(settings(tmp_path,video_uploads_enabled=False))
    client=TestClient(app,base_url='https://recall.example');headers=login(app,client)
    response=client.post('/api/lectures/anything/transcript',content=b'',headers={**headers,'Content-Length':str(22*1024**2)})
    assert response.status_code==413
    body=(b'x'*1024**2 for _ in range(22))
    response=client.post('/api/lectures/anything/transcript',content=body,headers={**headers,'Content-Type':'multipart/form-data; boundary=x'})
    assert response.status_code==413

def test_remote_worker_discovers_accounts_after_local_directory_loss(tmp_path,monkeypatch):
    url=os.environ.get('TEST_DATABASE_URL')
    if not url:pytest.skip('Disposable PostgreSQL is supplied by CI')
    from pydantic import SecretStr
    config=settings(tmp_path).model_copy(update={'database_url':SecretStr(url),'video_uploads_enabled':False})
    sub='remote-worker-test';account=hashlib.sha256(sub.encode()).hexdigest()
    scoped=workspace(config,sub)
    from app.storage import repository_for
    repo=repository_for(scoped);result=repo.import_handoff('restarted','C842vFY5kRo')
    JobQueue(repo).claim()
    shutil.rmtree(tmp_path)
    visited=[]
    monkeypatch.setattr('app.syllabus.build.prepare_lecture',lambda job,repo,provider:visited.append(job.lecture_id))
    worker=WorkspaceWorker(config.prepare())
    worker.tick()
    assert JobQueue(repo).get(result['job_id']).status=='retryable'
    JobQueue(repo).retry(result['job_id'])
    assert worker.tick()
    assert visited==[result['lecture_id']]
    assert JobQueue(repo).get(result['job_id']).status=='succeeded'
    worker.close()

def test_remote_workers_do_not_recover_each_others_running_jobs(tmp_path):
    url=os.environ.get('TEST_DATABASE_URL')
    if not url:pytest.skip('Disposable PostgreSQL is supplied by CI')
    from app.worker_lease import WorkerLease
    first=WorkerLease(url);second=WorkerLease(url)
    try:
        assert first.acquire()
        assert not second.acquire()
        first.check();first.close()
        assert second.acquire()
    finally:first.close();second.close()
