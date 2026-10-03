import pytest
from app.models import Interval,TranscriptSegment,SyllabusNode,TeachingPoint,CardCandidate,GenerationResult,Card
from app.cards.service import generate_job
from app.jobs import JobQueue
from app.errors import ProcessingError

def seed(repo):
    repo.save_transcript('lesson',[TranscriptSegment(id='s1',start=10,end=20,text='First'),TranscriptSegment(id='s2',start=310,end=320,text='Second')])
    repo.save_syllabus('lesson',[SyllabusNode(id='a',title='First',start=0,end=300),SyllabusNode(id='b',title='Second',start=300,end=600)])
class Provider:
    def __init__(self,fail_second=False):self.fail_second=fail_second
    def extract_points(self,segments,selected):
        chosen=[s for s in segments if any(i.start<=s.start<i.end for i in selected)]
        if self.fail_second and any(s.id=='s2' for s in chosen):raise ProcessingError('provider_failed','Test failure')
        return [TeachingPoint(id=s.id,summary=s.text,primary_segment_id=s.id,source_segment_ids=[s.id]) for s in chosen]
    def generate_cards(self,points,segments):return [CardCandidate(point_ids=[p.id],front='Recall '+p.summary,back=p.summary,primary_segment_id=p.primary_segment_id,source_segment_ids=p.source_segment_ids) for p in points]
    def check_support(self,candidate,segments):return True
def run(repo,ranges,provider=None,regenerate=False):
    job=JobQueue(repo).enqueue('lesson','generate',[Interval(start=a,end=b) for a,b in ranges],regenerate)
    generate_job(job,repo,provider or Provider())

def test_overlapping_generation_reuses_existing_cards(repo):
    seed(repo);run(repo,[(0,300)]);first=repo.get_lecture('lesson').cards[0]
    run(repo,[(0,600)])
    cards=repo.get_lecture('lesson').cards
    assert len(cards)==2
    assert first in cards

def test_failed_regeneration_preserves_all_old_results(repo):
    seed(repo);run(repo,[(0,600)])
    before=repo.get_lecture('lesson')
    with pytest.raises(ProcessingError):run(repo,[(0,600)],Provider(True),True)
    after=repo.get_lecture('lesson')
    assert after.cards==before.cards
    assert after.completed_intervals==before.completed_intervals

def test_partial_new_generation_retains_successful_topic(repo):
    seed(repo)
    with pytest.raises(ProcessingError):run(repo,[(0,600)],Provider(True))
    assert [c.primary_time for c in repo.get_lecture('lesson').cards]==[10]
    run(repo,[(0,600)])
    assert [c.primary_time for c in repo.get_lecture('lesson').cards]==[10,310]

def test_regeneration_replaces_only_selected_primary_times(repo):
    seed(repo);run(repo,[(0,600)])
    untouched=repo.get_lecture('lesson').cards[1]
    run(repo,[(0,300)],regenerate=True)
    assert untouched in repo.get_lecture('lesson').cards
