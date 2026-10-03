"""Test-only server: never imported or selectable by production code."""
import sys,tempfile,threading,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import uvicorn
from app.config import Config
from app.main import create_app
from app.models import SourceDescriptor,ChapterSeed,TranscriptSegment,SyllabusProposal,TeachingPoint,CardCandidate
from app.errors import ProcessingError
from app.jobs import JobQueue
from app.worker import run_once
import app.syllabus.build as syllabus
from app.cards.service import generate_job

def import_fixture(url,lecture_id):
    source=SourceDescriptor(lecture_id=lecture_id,title='Systems lecture (test fixture)',duration=900,source_kind='youtube',youtube_id='C842vFY5kRo',chapters=[ChapterSeed(title='Server foundations',start=0,end=600),ChapterSeed(title='Distributed systems',start=600,end=900)])
    segments=[TranscriptSegment(id='s1',start=10,end=25,text='A single server handles the client request.'),TranscriptSegment(id='s2',start=330,end=345,text='A cache stores frequently accessed data to reduce latency.'),TranscriptSegment(id='s3',start=350,end=365,text='A cache miss sends the request to the database.'),TranscriptSegment(id='s4',start=650,end=670,text='A load balancer distributes incoming requests across servers.')]
    return source,segments

class FixtureProvider:
    interrupted=False
    def propose_syllabus(self,segments,chapters):
        return [SyllabusProposal(title='Caching basics',parent_start=0,start=300,end=500,point_summaries=['Cache purpose','Cache misses'],source_segment_ids=['s2','s3'])] if any(s.id=='s2' for s in segments) else []
    def extract_points(self,segments,selected):
        chosen=[s for s in segments if any(i.start<=s.start<i.end for i in selected)]
        if any(s.id=='s4' for s in chosen) and not self.interrupted:
            self.interrupted=True;raise ProcessingError('provider_failed','Test provider interrupted the second chapter.')
        return [TeachingPoint(id=s.id,summary=s.text,primary_segment_id=s.id,source_segment_ids=[s.id]) for s in chosen]
    def generate_cards(self,points,segments):return [CardCandidate(point_ids=[p.id],front='Recall: '+p.summary,back=p.summary,primary_segment_id=p.primary_segment_id,source_segment_ids=p.source_segment_ids) for p in points]
    def check_support(self,candidate,segments):return True

if __name__=='__main__':
    with tempfile.TemporaryDirectory(prefix='recall-e2e-') as folder:
        app=create_app(Config(data_dir=Path(folder)));repo=app.state.repository;queue=JobQueue(repo);provider=FixtureProvider()
        syllabus.import_youtube=import_fixture
        handlers={'prepare':lambda job:syllabus.prepare_lecture(job,repo,provider),'generate':lambda job:generate_job(job,repo,provider)}
        def work():
            while True:
                if not run_once(queue,handlers):time.sleep(.1)
        threading.Thread(target=work,daemon=True).start()
        uvicorn.run(app,host='127.0.0.1',port=8001,log_level='warning')
