from app.jobs import JobQueue
from app.models import TranscriptSegment

def test_only_one_worker_can_claim_job(repo):
    first=JobQueue(repo);second=JobQueue(repo)
    job=first.enqueue('lesson','prepare',[],False)
    assert first.claim().id == job.id
    assert second.claim() is None

def test_recovery_and_retry_preserve_completed_transcript(repo):
    repo.save_transcript('lesson',[TranscriptSegment(id='s1',start=1,end=2,text='Keep this')])
    queue=JobQueue(repo);job=queue.enqueue('lesson','prepare',[],False);queue.claim()
    assert queue.recover_interrupted() == 1
    assert queue.get(job.id).status == 'retryable'
    assert queue.retry(job.id).status == 'queued'
    assert repo.get_segments('lesson')[0].text == 'Keep this'

def test_duplicate_active_generation_requests_reuse_job(repo):
    queue=JobQueue(repo)
    a=queue.enqueue('lesson','generate',[],False)
    b=queue.enqueue('lesson','generate',[],False)
    assert a.id == b.id
