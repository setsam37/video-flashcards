from fastapi.testclient import TestClient
from app.config import Config
from app.main import create_app
from app.models import TranscriptSegment,SyllabusNode,Interval
from app.jobs import JobQueue

def test_browser_lecture_payload_preserves_selection_and_job_contract(repo):
    repo.save_transcript('lesson',[TranscriptSegment(id='seg_000',start=1,end=3,text='Test teaching point')])
    repo.save_syllabus('lesson',[SyllabusNode(id='chapter',start=0,end=600,title='Topic')])
    JobQueue(repo).enqueue('lesson','generate',[Interval(start=0,end=300)],False)
    app=create_app(Config(data_dir=repo.path.parent));app.state.repository=repo
    result=TestClient(app).get('/api/lectures/lesson').json()
    assert result['syllabus'][0]['parent_id'] is None
    assert result['jobs'][0]['selected_intervals']==[{'start':0.0,'end':300.0}]
    assert result['jobs'][0]['status']=='queued'
    assert result['cards']==[]
    assert 'media_path' not in result
