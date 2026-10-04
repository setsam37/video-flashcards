import os,threading,uuid
from concurrent.futures import ThreadPoolExecutor
import pytest
from pydantic import SecretStr
from app.database import DatabaseUnavailable
from app.worker import run_once,WorkspaceWorker
from app.auth import workspace
from app.storage import repository_for
from app.jobs import JobQueue
from test_hosting import settings

def test_worker_database_outage_propagates_instead_of_attempting_failure_write(repo):
    queue=JobQueue(repo);job=queue.enqueue('lesson','prepare',[],False)
    failures=[]
    def fail(*args):failures.append(args)
    queue.fail=fail
    def outage(job):raise DatabaseUnavailable()
    with pytest.raises(DatabaseUnavailable):run_once(queue,{'prepare':outage})
    assert failures==[]
    assert queue.get(job.id).status=='running'
    # The supervisor restarts a worker on propagated database failure; its
    # startup recovery exposes a retry without losing completed material.
    assert queue.recover_interrupted()==1
    assert queue.get(job.id).status=='retryable'

def test_lost_postgres_lease_fences_old_handler_writes_and_job_status(tmp_path,monkeypatch):
    url=os.environ.get('TEST_DATABASE_URL')
    if not url:pytest.skip('Disposable PostgreSQL is supplied by CI')
    import psycopg
    config=settings(tmp_path).model_copy(update={'database_url':SecretStr(url),'video_uploads_enabled':False})
    scoped=workspace(config,'fencing-'+uuid.uuid4().hex)
    repo=repository_for(scoped);result=repo.import_handoff('fencing','C842vFY5kRo')
    started=threading.Event();release=threading.Event()
    def prepare(job,repo,provider):
        old=threading.current_thread().name.startswith('old-worker')
        if old:
            started.set();assert release.wait(20)
        source=repo.get_source(job.lecture_id)
        repo.save_source(source.model_copy(update={'title':'obsolete owner' if old else 'successor result'}))
    monkeypatch.setattr('app.syllabus.build.prepare_lecture',prepare)
    first=WorkspaceWorker(config);second=WorkspaceWorker(config)
    with ThreadPoolExecutor(max_workers=1,thread_name_prefix='old-worker') as pool:
        pending=pool.submit(first.tick)
        try:
            assert started.wait(20)
            with psycopg.connect(url,autocommit=True) as db:
                assert db.execute('SELECT pg_terminate_backend(%s)',(first.lease.connection.info.backend_pid,)).fetchone()[0]
            second.tick()
            assert JobQueue(repo).get(result['job_id']).status=='retryable'
            JobQueue(repo).retry(result['job_id']);second.tick()
            release.set()
            with pytest.raises(DatabaseUnavailable):pending.result(timeout=20)
            assert repo.get_source(result['lecture_id']).title=='successor result'
            assert JobQueue(repo).get(result['job_id']).status=='succeeded'
        finally:release.set();first.close();second.close()
