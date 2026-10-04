"""Private structured storage: SQLite locally, PostgreSQL on free hosting.

SQL passed here is owned by this application, never user supplied. The small
adapter preserves its qmark statements and SQLite's serialized write boundary.
"""
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
import hashlib,re,sqlite3

class DatabaseUnavailable(Exception):
    def __init__(self):super().__init__('The study service is temporarily unavailable. Please try again shortly.')

class PostgresConnection:
    def __init__(self,connection,schema):self.raw=connection;self.schema=schema
    def lock(self):
        number=int.from_bytes(hashlib.sha256(self.schema.encode()).digest()[:8],'big',signed=True)
        self.raw.execute('SELECT pg_advisory_xact_lock(%s)',(number,))
    def execute(self,statement,parameters=()):
        if statement.strip().upper()=='BEGIN IMMEDIATE':
            self.lock();return None
        return self.raw.execute(statement.replace('?','%s'),parameters)
    def executescript(self,script):
        for statement in script.split(';'):
            if statement.strip():self.execute(re.sub(r'\bREAL\b','DOUBLE PRECISION',statement))

class Database:
    def __init__(self,path,database_url='',namespace='root'):
        self.path=Path(path);self.url=database_url
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}',namespace):raise ValueError('Invalid database namespace')
        self.schema='recall_'+hashlib.sha256(namespace.encode()).hexdigest()[:48]
        self.order_column='rowid BIGSERIAL UNIQUE,' if self.url else ''

    def initialize(self,script):
        if self.url:_initialize_postgres(self.url,self.schema,script)
        else:
            self.path.parent.mkdir(parents=True,exist_ok=True)
            with self.connection() as db:db.executescript(script)

    @contextmanager
    def connection(self):
        if self.url:
            import psycopg
            from psycopg.rows import dict_row
            from psycopg import sql
            try:
                with psycopg.connect(self.url,connect_timeout=10,prepare_threshold=None,row_factory=dict_row) as db:
                    db.execute(sql.SQL('SET LOCAL search_path TO {}').format(sql.Identifier(self.schema)))
                    db.execute("SET LOCAL statement_timeout = '30s'")
                    yield PostgresConnection(db,self.schema)
            except psycopg.Error:raise DatabaseUnavailable() from None
        else:
            db=sqlite3.connect(self.path,timeout=30);db.row_factory=sqlite3.Row
            db.execute('PRAGMA foreign_keys=ON');db.execute('PRAGMA journal_mode=WAL')
            try:yield db;db.commit()
            except Exception:db.rollback();raise
            finally:db.close()

@lru_cache(maxsize=256)
def _initialize_postgres(url,schema,script):
    import psycopg
    from psycopg import sql
    try:
        with psycopg.connect(url,connect_timeout=10,prepare_threshold=None) as db:
            adapter=PostgresConnection(db,schema);adapter.lock()
            db.execute(sql.SQL('CREATE SCHEMA IF NOT EXISTS {}').format(sql.Identifier(schema)))
            db.execute(sql.SQL('SET LOCAL search_path TO {}').format(sql.Identifier(schema)))
            adapter.executescript(script)
            roles=['PUBLIC']+[r[0] for r in db.execute("SELECT rolname FROM pg_roles WHERE rolname IN ('anon','authenticated')")]
            for role in roles:
                target=sql.SQL('PUBLIC') if role=='PUBLIC' else sql.Identifier(role)
                db.execute(sql.SQL('REVOKE ALL ON SCHEMA {} FROM {}').format(sql.Identifier(schema),target))
                db.execute(sql.SQL('REVOKE ALL ON ALL TABLES IN SCHEMA {} FROM {}').format(sql.Identifier(schema),target))
                db.execute(sql.SQL('REVOKE ALL ON ALL SEQUENCES IN SCHEMA {} FROM {}').format(sql.Identifier(schema),target))
    except psycopg.Error:raise DatabaseUnavailable() from None

class AccountRegistry:
    def __init__(self,database_url):
        self.database=Database(Path('unused'),database_url,'account_registry')
        self.database.initialize('CREATE TABLE IF NOT EXISTS accounts(id TEXT PRIMARY KEY);')
    def register(self,account):
        if not re.fullmatch('[a-f0-9]{64}',account):raise ValueError('Invalid account identity')
        with self.database.connection() as db:
            db.execute('INSERT INTO accounts(id) VALUES(?) ON CONFLICT(id) DO NOTHING',(account,))
    def list(self):
        with self.database.connection() as db:return [r['id'] for r in db.execute('SELECT id FROM accounts ORDER BY id')]
