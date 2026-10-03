from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Config
from app.models import TranscriptSegment,SyllabusNode

@pytest.fixture
def client(repo):
    app=create_app(Config(data_dir=repo.path.parent));app.state.repository=repo
    return TestClient(app)

def test_empty_selection_cannot_start_generation(client):
    assert client.post('/api/lectures/lesson/generate',json={'intervals':[],'regenerate':False}).status_code==422

def test_duplicate_request_returns_same_job(client,repo):
    repo.save_transcript('lesson',[TranscriptSegment(id='s1',start=1,end=2,text='Test')]);repo.save_syllabus('lesson',[SyllabusNode(id='a',start=0,end=600,title='Test')])
    body={'intervals':[{'start':0,'end':600}],'regenerate':False}
    first=client.post('/api/lectures/lesson/generate',json=body)
    second=client.post('/api/lectures/lesson/generate',json=body)
    assert first.status_code==200
    assert first.json()['job_id']==second.json()['job_id']

def test_media_range_supports_seek(client,repo):
    folder=repo.path.parent/'media';folder.mkdir(exist_ok=True);media=folder/'lesson.mp4';media.write_bytes(b'0123456789')
    repo.save_source(repo.get_source('lesson').model_copy(update={'media_path':str(media)}))
    result=client.get('/api/lectures/lesson/media',headers={'Range':'bytes=2-5'})
    assert result.status_code==206
    assert result.content==b'2345'

def test_transcript_without_playback_source_is_rejected(client,repo):
    repo.save_source(repo.get_source('lesson').model_copy(update={'media_path':None}))
    result=client.post('/api/lectures/lesson/transcript',files={'transcript':('x.srt',b'1\n00:00:01,000 --> 00:00:02,000\nTest')})
    assert result.status_code==422

def test_other_origins_cannot_mutate_local_app(client):
    result=client.post('/api/lectures/youtube',json={'url':'https://youtu.be/C842vFY5kRo'},headers={'Origin':'https://example.com'})
    assert result.status_code==403

def test_upload_does_not_preserve_client_path(client,repo):
    result=client.post('/api/lectures/upload',files={'video':('../../evil.mp4',b'video','video/mp4')})
    assert result.status_code==200
    source=repo.get_source(result.json()['lecture_id'])
    assert Path(source.media_path).parent==repo.path.parent/'media'
    assert Path(source.media_path).name!='evil.mp4'
