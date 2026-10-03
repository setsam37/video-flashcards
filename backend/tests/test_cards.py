import pytest
from app.models import Interval,TranscriptSegment,SyllabusNode,TeachingPoint,CardCandidate
from app.cards.generate import generate_selection
from app.cards.validate import validate_candidate

def evidence():return [TranscriptSegment(id='s1',start=10,end=20,text='A load balancer distributes requests across servers.'),TranscriptSegment(id='s2',start=310,end=320,text='A different topic.')]
def nodes():return [SyllabusNode(id='chapter',title='Balancing',start=0,end=600)]
def point(id='p',segment='s1',visual=False):return TeachingPoint(id=id,summary='Role of load balancing',primary_segment_id=segment,source_segment_ids=[segment],visual_gap=visual)
class Provider:
    def __init__(self,points=None,supported=True,duplicate=False):self.points=points or [point()];self.supported=supported;self.duplicate=duplicate;self.generations=0
    def extract_points(self,segments,selected):return self.points
    def generate_cards(self,points,segments):
        self.generations+=1
        cards=[CardCandidate(point_ids=[p.id],front='What does a load balancer do?',back='It distributes requests across servers.',primary_segment_id=p.primary_segment_id,source_segment_ids=p.source_segment_ids) for p in points]
        return cards+cards if self.duplicate else cards
    def check_support(self,candidate,segments):return self.supported

def generate(provider):return generate_selection('lesson',[Interval(start=0,end=300)],nodes(),evidence(),provider)

def test_cards_have_real_source_timestamps_and_assignment():
    result=generate(Provider())
    assert len(result.cards)==1
    assert result.cards[0].topic_id=='chapter'
    assert (result.cards[0].source_start,result.cards[0].source_end)==(10,20)
    assert result.cards[0].source_excerpt=='A load balancer distributes requests across servers.'

def test_unselected_point_cannot_become_card():
    result=generate(Provider(points=[point(),point('outside','s2')]))
    assert len(result.cards)==1
    assert result.cards[0].source_segment_ids==['s1']

def test_visual_reference_becomes_explicit_gap():
    result=generate(Provider(points=[point(visual=True)]))
    assert result.cards==[]
    assert len(result.gaps)==1

def test_unsupported_answer_gets_one_retry_then_gap():
    provider=Provider(supported=False);result=generate(provider)
    assert result.cards==[]
    assert len(result.gaps)==1
    assert provider.generations==2

def test_duplicate_candidates_cannot_duplicate_cards():
    assert len(generate(Provider(duplicate=True)).cards)==1

@pytest.mark.parametrize('changes',[{'source_segment_ids':['invented']},{'back':''},{'primary_segment_id':'s2','source_segment_ids':['s2']}])
def test_unknown_evidence_empty_answers_and_context_only_primary_are_rejected(changes):
    candidate=CardCandidate(point_ids=['p'],front='Question',back='Answer',primary_segment_id='s1',source_segment_ids=['s1']).model_copy(update=changes)
    with pytest.raises(ValueError):validate_candidate(candidate,[point()],evidence(),[Interval(start=0,end=300)],lecture_id='lesson',nodes=nodes())

def test_code_and_equations_are_preserved():
    class CodeProvider(Provider):
        def generate_cards(self,points,segments):return [CardCandidate(point_ids=[points[0].id],front='Recall the example',back='```py\nx = 2\n```\nRate = requests / seconds',primary_segment_id='s1',source_segment_ids=['s1'])]
    assert '```py\nx = 2\n```' in generate(CodeProvider()).cards[0].back
