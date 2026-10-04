from pathlib import Path
import json
from .database import Database
from .models import SourceDescriptor,TranscriptSegment,SyllabusNode,Card,Job,CoverageGap,Interval,LectureView

class Repository:
    def __init__(self,path: Path,database_url='',workspace_id='root',worker_fence=None):
        self.path=Path(path)
        self.database=Database(self.path,database_url,'library_'+workspace_id,worker_fence)
        self.database.initialize(f'''
            CREATE TABLE IF NOT EXISTS sources({self.database.order_column}id TEXT PRIMARY KEY,payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS transcripts(lecture_id TEXT PRIMARY KEY REFERENCES sources(id),payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS nodes(lecture_id TEXT PRIMARY KEY REFERENCES sources(id),payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS cards(id TEXT PRIMARY KEY,lecture_id TEXT NOT NULL REFERENCES sources(id),primary_time REAL NOT NULL,payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS gaps(lecture_id TEXT NOT NULL REFERENCES sources(id),point_id TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(lecture_id,point_id));
            CREATE TABLE IF NOT EXISTS covered(lecture_id TEXT PRIMARY KEY REFERENCES sources(id),payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS jobs({self.database.order_column}id TEXT PRIMARY KEY,lecture_id TEXT NOT NULL REFERENCES sources(id),status TEXT NOT NULL,payload TEXT NOT NULL,request_key TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS handoffs(id TEXT PRIMARY KEY,lecture_id TEXT NOT NULL REFERENCES sources(id),job_id TEXT NOT NULL REFERENCES jobs(id));
            ''')

    def connection(self):return self.database.connection()

    def save_source(self,source):
        with self.connection() as db:
            db.execute('INSERT INTO sources(id,payload) VALUES (?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload',(source.lecture_id,source.model_dump_json()))

    def get_source(self,id):
        with self.connection() as db: row=db.execute('SELECT payload FROM sources WHERE id=?',(id,)).fetchone()
        if not row: raise KeyError(id)
        return SourceDescriptor.model_validate_json(row['payload'])

    def _save_list(self,table,id,items):
        with self.connection() as db:
            db.execute(f'INSERT INTO {table} VALUES (?,?) ON CONFLICT(lecture_id) DO UPDATE SET payload=excluded.payload',(id,json.dumps([x.model_dump() for x in items])))

    def _get_list(self,table,id,model):
        with self.connection() as db: row=db.execute(f'SELECT payload FROM {table} WHERE lecture_id=?',(id,)).fetchone()
        return [model.model_validate(x) for x in json.loads(row['payload'])] if row else []

    def save_transcript(self,id,segments): self._save_list('transcripts',id,segments)
    def get_segments(self,id): return self._get_list('transcripts',id,TranscriptSegment)
    def save_syllabus(self,id,nodes): self._save_list('nodes',id,nodes)
    def get_nodes(self,id): return self._get_list('nodes',id,SyllabusNode)
    def get_covered(self,id): return self._get_list('covered',id,Interval)

    def get_lecture(self,id):
        source=self.get_source(id)
        with self.connection() as db:
            cards=[Card.model_validate_json(r['payload']) for r in db.execute('SELECT payload FROM cards WHERE lecture_id=? ORDER BY primary_time,id',(id,))]
            gaps=[CoverageGap.model_validate_json(r['payload']) for r in db.execute('SELECT payload FROM gaps WHERE lecture_id=?',(id,))]
            jobs=[Job.model_validate_json(r['payload']) for r in db.execute('SELECT payload FROM jobs WHERE lecture_id=? ORDER BY rowid',(id,))]
        return LectureView(id=id,title=source.title,duration=source.duration,source_kind=source.source_kind,youtube_id=source.youtube_id,media_url=f'/api/lectures/{id}/media' if source.media_path else None,syllabus=self.get_nodes(id),cards=cards,gaps=gaps,completed_intervals=self.get_covered(id),jobs=jobs)

    def list_lectures(self):
        with self.connection() as db: ids=[r['id'] for r in db.execute('SELECT id FROM sources ORDER BY rowid DESC')]
        return [{'id':id,'title':self.get_source(id).title,'duration':self.get_source(id).duration} for id in ids]

    def handoff_result(self,id):
        with self.connection() as db:row=db.execute('SELECT lecture_id,job_id FROM handoffs WHERE id=?',(id,)).fetchone()
        return dict(row) if row else None

    def import_handoff(self,id,video_id):
        import uuid
        source=SourceDescriptor(lecture_id=uuid.uuid4().hex,title='YouTube lecture',duration=0,source_kind='youtube',youtube_id=video_id)
        job=Job(id=uuid.uuid4().hex,lecture_id=source.lecture_id,kind='prepare',stage='importing',status='queued',selected_intervals=[],regenerate=False)
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            existing=db.execute('SELECT lecture_id,job_id FROM handoffs WHERE id=?',(id,)).fetchone()
            if existing:return dict(existing)
            db.execute('INSERT INTO sources(id,payload) VALUES(?,?)',(source.lecture_id,source.model_dump_json()))
            key=json.dumps([source.lecture_id,'prepare',[],False],sort_keys=True)
            db.execute('INSERT INTO jobs(id,lecture_id,status,payload,request_key) VALUES(?,?,?,?,?)',(job.id,source.lecture_id,'queued',job.model_dump_json(),key))
            db.execute('INSERT INTO handoffs VALUES(?,?,?)',(id,source.lecture_id,job.id))
        return {'lecture_id':source.lecture_id,'job_id':job.id}

    def commit_generation(self,id,intervals,result,regenerate):
        from .syllabus.selection import normalize
        from .cards.validate import in_selection
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            if regenerate:
                for span in intervals:db.execute('DELETE FROM cards WHERE lecture_id=? AND primary_time>=? AND primary_time<?',(id,span.start,span.end))
                for row in db.execute('SELECT point_id,payload FROM gaps WHERE lecture_id=?',(id,)).fetchall():
                    gap=CoverageGap.model_validate_json(row['payload'])
                    if gap.primary_time is not None and in_selection(gap.primary_time,intervals):db.execute('DELETE FROM gaps WHERE lecture_id=? AND point_id=?',(id,row['point_id']))
            for card in result.cards:
                db.execute('INSERT INTO cards VALUES (?,?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,primary_time=excluded.primary_time',(card.id,id,card.primary_time,card.model_dump_json()))
                for point in card.point_ids:db.execute('DELETE FROM gaps WHERE lecture_id=? AND point_id=?',(id,point))
            for gap in result.gaps:db.execute('INSERT INTO gaps VALUES (?,?,?) ON CONFLICT(lecture_id,point_id) DO UPDATE SET payload=excluded.payload',(id,gap.point_id,gap.model_dump_json()))
            row=db.execute('SELECT payload FROM covered WHERE lecture_id=?',(id,)).fetchone()
            old=[Interval.model_validate(x) for x in json.loads(row['payload'])] if row else []
            merged=normalize(old+result.completed_intervals)
            db.execute('INSERT INTO covered VALUES (?,?) ON CONFLICT(lecture_id) DO UPDATE SET payload=excluded.payload',(id,json.dumps([i.model_dump() for i in merged])))

def repository_for(config,worker_fence=None):
    return Repository(config.data_dir/'study.sqlite',database_url=config.database_url.get_secret_value(),workspace_id=config.workspace_id,worker_fence=worker_fence)
