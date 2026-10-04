"""Real PostgreSQL integration checks. CI supplies a disposable database."""
from concurrent.futures import ThreadPoolExecutor
import os,shutil,time,uuid
import pytest
from app.models import SourceDescriptor,TranscriptSegment
from app.storage import Repository
from app.sessions import SessionStore
from app.jobs import JobQueue

def test_database_arguments_preserve_local_sqlite(tmp_path):
    repo=Repository(tmp_path/'study.sqlite',database_url='',workspace_id='root')
    repo.save_source(SourceDescriptor(lecture_id='one',title='Local',duration=60,source_kind='youtube',youtube_id='C842vFY5kRo'))
    assert Repository(repo.path).get_lecture('one').title=='Local'
    store=SessionStore(tmp_path/'auth.sqlite',database_url='')
    token,_=store.issue('local-user','user@example.test')
    assert store.get(token)['sub']=='local-user'

@pytest.fixture
def pg(tmp_path):
    url=os.environ.get('TEST_DATABASE_URL')
    if not url:pytest.skip('Disposable PostgreSQL is supplied by CI')
    account=uuid.uuid4().hex*2
    repo=Repository(tmp_path/'study.sqlite',database_url=url,workspace_id=account)
    yield repo,url,account
    from psycopg import connect,sql
    with connect(url) as db:
        db.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(repo.database.schema)))

def source(id='one'):
    return SourceDescriptor(lecture_id=id,title='Durable lecture',duration=60,source_kind='youtube',youtube_id='C842vFY5kRo')

def test_postgres_survives_local_directory_loss_and_keeps_order(pg):
    repo,url,account=pg
    repo.save_source(source());repo.save_source(source('two'))
    repo.save_transcript('one',[TranscriptSegment(id='s1',start=1,end=3,text='Persist this taught explanation.')])
    repo.save_source(source())
    shutil.rmtree(repo.path.parent)
    reopened=Repository(repo.path,database_url=url,workspace_id=account)
    assert reopened.get_segments('one')[0].id=='s1'
    assert [item['id'] for item in reopened.list_lectures()]==['two','one']

def test_postgres_other_account_cannot_read_same_id(pg,tmp_path):
    repo,url,account=pg;repo.save_source(source())
    other=Repository(tmp_path/'other.sqlite',database_url=url,workspace_id=uuid.uuid4().hex*2)
    try:
        assert other.list_lectures()==[]
        with pytest.raises(KeyError):other.get_source('one')
        other.save_source(source())
        assert len(repo.list_lectures())==1
    finally:
        from psycopg import connect,sql
        with connect(url) as db:db.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(other.database.schema)))

def test_postgres_concurrent_handoff_and_job_claim_are_atomic(pg):
    repo,url,account=pg
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda _:repo.import_handoff('same-handoff','C842vFY5kRo'),range(4)))
    assert all(item==results[0] for item in results)
    assert len(repo.list_lectures())==1
    with ThreadPoolExecutor(max_workers=4) as pool:
        claims=list(pool.map(lambda _:JobQueue(repo).claim(),range(4)))
    assert len([job for job in claims if job])==1
    assert JobQueue(repo).recover_interrupted()==1
    assert JobQueue(repo).get(results[0]['job_id']).status=='retryable'

def test_postgres_transaction_rollback(pg):
    repo,_,_=pg;repo.save_source(source())
    with pytest.raises(RuntimeError):
        with repo.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM sources WHERE id=?',('one',))
            raise RuntimeError('Simulate processing interruption')
    assert repo.get_source('one').title=='Durable lecture'

def test_postgres_generation_reuses_cards_and_rolls_back_failed_replacement(pg):
    from test_generation import seed,run,Provider
    from app.errors import ProcessingError
    repo,_,_=pg
    repo.save_source(source('lesson').model_copy(update={'duration':600}))
    seed(repo);run(repo,[(0,300)]);first=repo.get_lecture('lesson').cards[0]
    run(repo,[(0,600)])
    before=repo.get_lecture('lesson')
    assert first in before.cards and len(before.cards)==2
    with pytest.raises(ProcessingError):run(repo,[(0,600)],Provider(True),True)
    assert repo.get_lecture('lesson').cards==before.cards
    assert repo.get_lecture('lesson').completed_intervals==before.completed_intervals

def test_postgres_sessions_and_one_use_states_survive_restart(pg,tmp_path):
    _,url,_=pg
    store=SessionStore(tmp_path/'auth.sqlite',database_url=url)
    sub=uuid.uuid4().hex;token,_=store.issue(sub,'user@example.test')
    state=uuid.uuid4().hex;store.remember_state(state)
    reopened=SessionStore(tmp_path/'gone'/'auth.sqlite',database_url=url)
    assert reopened.get(token)['sub']==sub
    with ThreadPoolExecutor(max_workers=4) as pool:
        consumed=list(pool.map(lambda _:reopened.consume_state(state),range(4)))
    assert consumed.count(True)==1
    with reopened.connection() as db:
        db.execute('UPDATE sessions SET expires=? WHERE digest=?',(time.time()+1.25,reopened.digest(token)))
    remaining=reopened.get(token)['expires']-time.time()
    assert 0<remaining<1.3
    reopened.revoke(token)
    assert not store.get(token)
