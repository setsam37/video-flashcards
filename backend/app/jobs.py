import json,uuid
from .models import Job

class JobQueue:
    def __init__(self,repository): self.repository=repository
    def enqueue(self,lecture_id,kind,intervals,regenerate):
        key=json.dumps([lecture_id,kind,[i.model_dump() for i in intervals],regenerate],sort_keys=True)
        job=Job(id=uuid.uuid4().hex,lecture_id=lecture_id,kind=kind,stage='importing' if kind=='prepare' else 'generating',status='queued',selected_intervals=intervals,regenerate=regenerate)
        with self.repository.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            existing=db.execute("SELECT payload FROM jobs WHERE request_key=? AND status IN ('queued','running','retryable')",(key,)).fetchone()
            if existing: return Job.model_validate_json(existing['payload'])
            db.execute('INSERT INTO jobs(id,lecture_id,status,payload,request_key) VALUES (?,?,?,?,?)',(job.id,lecture_id,job.status,job.model_dump_json(),key))
        return job
    def get(self,id):
        with self.repository.connection() as db: row=db.execute('SELECT payload FROM jobs WHERE id=?',(id,)).fetchone()
        if not row: raise KeyError(id)
        return Job.model_validate_json(row['payload'])
    def update(self,id,**fields):
        with self.repository.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT payload FROM jobs WHERE id=?',(id,)).fetchone()
            if not row: raise KeyError(id)
            data=json.loads(row['payload']);data.update(fields);job=Job.model_validate(data)
            db.execute('UPDATE jobs SET status=?,payload=? WHERE id=?',(job.status,job.model_dump_json(),id))
        return job
    def claim(self):
        with self.repository.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute("SELECT payload FROM jobs j WHERE status='queued' AND NOT EXISTS (SELECT 1 FROM jobs busy WHERE busy.lecture_id=j.lecture_id AND busy.status='running') ORDER BY rowid LIMIT 1").fetchone()
            if not row:return None
            job=Job.model_validate_json(row['payload']).model_copy(update={'status':'running'})
            db.execute('UPDATE jobs SET status=?,payload=? WHERE id=?',(job.status,job.model_dump_json(),job.id))
        return job
    def fail(self,id,code,message):return self.update(id,status='failed',error_code=code,error_message=message)
    def retry(self,id):
        job=self.get(id)
        if job.status not in ['failed','retryable']:raise ValueError('Only failed or interrupted work can be retried')
        return self.update(id,status='queued',error_code=None,error_message=None)
    def recover_interrupted(self):
        with self.repository.connection() as db:
            rows=db.execute("SELECT id,payload FROM jobs WHERE status='running'").fetchall()
            for row in rows:
                job=Job.model_validate_json(row['payload']).model_copy(update={'status':'retryable'})
                db.execute('UPDATE jobs SET status=?,payload=? WHERE id=?',('retryable',job.model_dump_json(),row['id']))
        return len(rows)
