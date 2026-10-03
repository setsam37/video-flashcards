import pytest
from app.models import SourceDescriptor,ChapterSeed,TranscriptSegment,SyllabusProposal
from app.syllabus.build import build_syllabus,prepare_lecture
from app.jobs import JobQueue

def source(chapters=None):return SourceDescriptor(lecture_id='lesson',title='Test',duration=600,source_kind='upload',media_path='video.mp4',chapters=chapters or [])
def segments():return [TranscriptSegment(id='s1',start=0,end=300,text='First concept'),TranscriptSegment(id='s2',start=300,end=600,text='Second concept')]
class Provider:
    def __init__(self,proposals):self.proposals=proposals
    def propose_syllabus(self,segments,chapters):return self.proposals
def proposal(start,end,parent=0,points=None):return SyllabusProposal(title=f'Topic {start}',start=start,end=end,parent_start=parent,point_summaries=points or ['Mechanism','Comparison'],source_segment_ids=['s1'])

def test_instructor_boundaries_and_names_are_preserved():
    chapters=[ChapterSeed(title='Original',start=0,end=600)]
    nodes=build_syllabus(source(chapters),segments(),Provider([proposal(60,180)]))
    assert [(n.title,n.start,n.end) for n in nodes if n.parent_id is None]==[('Original',0,600)]
    assert [(n.start,n.end) for n in nodes if n.parent_id]==[(60,180)]

@pytest.mark.parametrize('child',[proposal(0,119),proposal(0,120,points=['Only one'])])
def test_insubstantial_subtopics_are_not_created(child):
    nodes=build_syllabus(source([ChapterSeed(title='Parent',start=0,end=600)]),segments(),Provider([child]))
    assert len(nodes)==1

def test_overlapping_subtopics_are_rejected():
    nodes=build_syllabus(source([ChapterSeed(title='Parent',start=0,end=600)]),segments(),Provider([proposal(0,200),proposal(100,300)]))
    assert len([n for n in nodes if n.parent_id])==1

def test_valid_chapter_ends_are_kept_and_gaps_are_inferred():
    nodes=build_syllabus(source([ChapterSeed(title='First',start=0,end=200),ChapterSeed(title='Duplicate',start=0,end=300),ChapterSeed(title='Second',start=300,end=600)]),segments(),Provider([]))
    assert [(n.title,n.start,n.end) for n in nodes if not n.inferred]==[('First',0,200),('Second',300,600)]
    assert [(n.start,n.end) for n in nodes if n.inferred]==[(200,300)]

def test_no_chapters_produces_inferred_root():
    nodes=build_syllabus(source(),segments(),Provider([proposal(0,600,parent=None)]))
    assert nodes[0].inferred is True
    assert nodes[0].parent_id is None

def test_preparing_stored_transcript_never_generates_cards(repo):
    repo.save_source(source([ChapterSeed(title='First',start=0,end=600)]));repo.save_transcript('lesson',segments())
    queue=JobQueue(repo);job=queue.enqueue('lesson','prepare',[],False)
    prepare_lecture(job,repo,Provider([]))
    assert repo.get_lecture('lesson').cards==[]
    assert len(repo.get_lecture('lesson').syllabus)==1
    assert all(j.kind=='prepare' for j in repo.get_lecture('lesson').jobs)
