import time
from app.auth import workspace
from app.storage import Repository
from app.worker import WorkspaceWorker
from test_hosting import settings,hosted

def test_worker_processes_each_accounts_queue_in_its_own_workspace(tmp_path,monkeypatch):
    config=settings(tmp_path);expected=[];visited=[]
    for sub in ['one','two']:
        scoped=workspace(config,sub);repo=Repository(scoped.data_dir/'study.sqlite')
        result=repo.import_handoff(sub,'C842vFY5kRo');expected.append((result['lecture_id'],scoped.data_dir))
    monkeypatch.setattr('app.syllabus.build.prepare_lecture',lambda job,repo,provider:visited.append((job.lecture_id,provider.config.data_dir)))
    worker=WorkspaceWorker(config)
    assert worker.tick() is True
    assert set(visited)==set(expected)
    assert worker.tick() is False
    for _,path in expected:
        assert Repository(path/'study.sqlite').get_lecture(_).jobs[0].status=='succeeded'

def test_hosted_health_reports_missing_or_stale_worker_without_private_settings(tmp_path):
    app,client=hosted(tmp_path)
    assert client.get('/api/health').status_code==503
    heartbeat=tmp_path/'worker-heartbeat';heartbeat.write_text(str(time.time()))
    response=client.get('/api/health');assert response.status_code==200
    assert response.json()=={'status':'ok'}
    heartbeat.write_text(str(time.time()-60))
    assert client.get('/api/health').status_code==503
