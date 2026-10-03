import pytest
from pydantic import ValidationError
from app.models import Interval, TranscriptSegment
from app.storage import Repository

def test_reopen_preserves_transcript_ids(repo):
    repo.save_transcript('lesson',[TranscriptSegment(id='s1',start=1,end=4,text='A taught concept')])
    reopened=Repository(repo.path)
    assert reopened.get_segments('lesson')[0].id == 's1'
    assert reopened.get_lecture('lesson').title == 'Synthetic test lesson'

def test_public_lecture_never_exposes_private_media_path(repo):
    assert '/private/' not in repo.get_lecture('lesson').model_dump_json()

@pytest.mark.parametrize('start,end',[(0,0),(-1,5),(5,4),(0,float('inf')),(float('nan'),6)])
def test_invalid_intervals_are_rejected(start,end):
    with pytest.raises(ValidationError): Interval(start=start,end=end)
