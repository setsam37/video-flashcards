"""One database-backed worker across overlapping free-server deployments.

Use the Supabase session pooler: session advisory locks must stay on the
same PostgreSQL session for the entire worker lifetime.
"""
from .database import DatabaseUnavailable

class WorkerLease:
    def __init__(self,url):self.url=url;self.connection=None
    def acquire(self):
        import psycopg
        if self.connection is not None:
            self.check();return True
        try:
            db=psycopg.connect(self.url,connect_timeout=10,autocommit=True,prepare_threshold=None,options='-c statement_timeout=5000',keepalives_idle=15,keepalives_interval=5,keepalives_count=3)
            try:
                owned=db.execute('SELECT pg_try_advisory_lock(%s)',(1919247212,)).fetchone()[0]
                if not owned:db.close();return False
                self.connection=db;return True
            except Exception:db.close();raise
        except psycopg.Error:raise DatabaseUnavailable() from None
    def check(self):
        import psycopg
        if self.connection is not None:
            try:self.connection.execute('SELECT 1')
            except psycopg.Error:raise DatabaseUnavailable() from None
    def close(self):
        if self.connection is not None:self.connection.close();self.connection=None
