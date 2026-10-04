import hashlib,secrets,time
from .database import Database

COOKIE='recall_session'

class SessionStore:
    def __init__(self,path,database_url=''):
        self.path=path
        self.database=Database(path,database_url,'sessions')
        self.database.initialize('''
            CREATE TABLE IF NOT EXISTS sessions(digest TEXT PRIMARY KEY,sub TEXT NOT NULL,email TEXT NOT NULL,csrf TEXT NOT NULL,expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS oauth_states(digest TEXT PRIMARY KEY,expires REAL NOT NULL);
        ''')

    def connection(self):return self.database.connection()

    def issue(self,sub,email):
        token=secrets.token_urlsafe(32);csrf=secrets.token_urlsafe(32)
        with self.connection() as db:
            db.execute('DELETE FROM sessions WHERE expires<=?',(time.time(),))
            db.execute('INSERT INTO sessions VALUES(?,?,?,?,?)',(self.digest(token),sub,email.lower(),csrf,time.time()+86400))
        return token,csrf

    @staticmethod
    def digest(token):return hashlib.sha256(token.encode()).hexdigest()

    def get(self,token):
        if not token or len(token)>128:return None
        with self.connection() as db:row=db.execute('SELECT sub,email,csrf,expires FROM sessions WHERE digest=? AND expires>?',(self.digest(token),time.time())).fetchone()
        return dict(row) if row else None

    def revoke(self,token):
        if token:
            with self.connection() as db:db.execute('DELETE FROM sessions WHERE digest=?',(self.digest(token),))

    def remember_state(self,state):
        with self.connection() as db:
            db.execute('DELETE FROM oauth_states WHERE expires<=?',(time.time(),))
            db.execute('INSERT INTO oauth_states VALUES(?,?)',(self.digest(state),time.time()+600))

    def consume_state(self,state):
        if not state or len(state)>128:return False
        with self.connection() as db:
            cursor=db.execute('DELETE FROM oauth_states WHERE digest=? AND expires>?',(self.digest(state),time.time()))
            return cursor.rowcount==1
