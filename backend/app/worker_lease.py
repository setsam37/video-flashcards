"""One database-backed worker across overlapping free-server deployments.

Use the Supabase session pooler: session advisory locks must stay on the
same PostgreSQL session for the entire worker lifetime.
"""
from pathlib import Path
import uuid
from .database import Database,DatabaseUnavailable,WorkerOwnershipLost

class WorkerLease:
    def __init__(self,url):
        self.url=url;self.connection=None;self.token=None
        self.database=Database(Path('unused'),url,'worker_ownership')
        self.database.initialize('CREATE TABLE IF NOT EXISTS ownership(id TEXT PRIMARY KEY,token TEXT NOT NULL);')
    def acquire(self):
        import psycopg
        if self.connection is not None:
            self.check();return True
        try:
            db=psycopg.connect(self.url,connect_timeout=10,autocommit=True,prepare_threshold=None,options='-c statement_timeout=5000',keepalives_idle=15,keepalives_interval=5,keepalives_count=3)
            try:
                owned=db.execute('SELECT pg_try_advisory_lock(%s)',(1919247212,)).fetchone()[0]
                if not owned:db.close();return False
                from psycopg import sql
                token=uuid.uuid4().hex
                with db.transaction():
                    db.execute(sql.SQL('INSERT INTO {}.ownership(id,token) VALUES(%s,%s) ON CONFLICT(id) DO UPDATE SET token=excluded.token').format(sql.Identifier(self.database.schema)),('active',token))
                self.token=token
                self.connection=db;return True
            except Exception:db.close();raise
        except psycopg.Error:raise DatabaseUnavailable() from None
    def check(self):
        import psycopg
        if self.token and self.connection is None:raise WorkerOwnershipLost()
        if self.connection is not None:
            try:self.connection.execute('SELECT 1')
            except psycopg.Error:raise DatabaseUnavailable() from None
    def fence(self,db):
        from psycopg import sql
        # The shared row lock is held through the caller's commit. A successor
        # must update this token before recovering work, so old writes either
        # finish before takeover or fail; they cannot overwrite successor work.
        row=db.raw.execute(sql.SQL('SELECT token FROM {}.ownership WHERE id=%s FOR SHARE').format(sql.Identifier(self.database.schema)),('active',)).fetchone()
        if not self.token or not row or row['token']!=self.token:raise WorkerOwnershipLost()
    def close(self):
        if self.connection is not None:self.connection.close();self.connection=None
