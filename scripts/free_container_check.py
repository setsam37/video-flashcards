"""Real free-hosting checks using a disposable CI database and fake keys."""
import json,os,subprocess,sys,tempfile,time,urllib.request,urllib.error
from pathlib import Path

def docker(*args):return subprocess.check_output(['docker',*args],text=True).strip()
def request(path):
    try:
        with urllib.request.urlopen('http://127.0.0.1:18000'+path,timeout=2) as response:return response.status,json.loads(response.read()) if path.endswith('health') else response.read()
    except urllib.error.HTTPError as error:return error.code,None

def ready():
    for _ in range(60):
        try:
            if request('/api/health')==(200,{'status':'ok'}):return
        except (OSError,TimeoutError):pass
        time.sleep(1)
    raise AssertionError('Container never became healthy')

def database_tls(container):
    # Encrypt connections to the actual disposable PostgreSQL server.
    with tempfile.TemporaryDirectory() as directory:
        cert=Path(directory)/'server.crt';key=Path(directory)/'server.key'
        subprocess.run(['openssl','req','-new','-x509','-nodes','-days','1','-subj','/CN=localhost','-out',str(cert),'-keyout',str(key)],check=True,capture_output=True)
        docker('cp',str(cert),container+':/tmp/recall-ci.crt');docker('cp',str(key),container+':/tmp/recall-ci.key')
        docker('exec','-u','0',container,'chown','postgres:postgres','/tmp/recall-ci.key','/tmp/recall-ci.crt')
        docker('exec','-u','0',container,'chmod','0600','/tmp/recall-ci.key')
    for statement in ["ALTER SYSTEM SET ssl_cert_file='/tmp/recall-ci.crt'","ALTER SYSTEM SET ssl_key_file='/tmp/recall-ci.key'","ALTER SYSTEM SET ssl='on'","SELECT pg_reload_conf()"]:
        docker('exec','-u','postgres',container,'psql','-c',statement)
    import psycopg
    url=os.environ['TEST_DATABASE_URL'].replace('sslmode=disable','sslmode=require')
    with psycopg.connect(url) as db:assert db.execute('SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()').fetchone()[0]
    return url

def main():
    url=database_tls(sys.argv[1])
    env={'APP_MODE':'hosted','PUBLIC_APP_URL':'https://localhost','GOOGLE_CLIENT_ID':'ci-client','GOOGLE_CLIENT_SECRET':'ci-secret','SESSION_SECRET':'ci-only-long-session-secret-32-characters','OPENAI_API_KEY':'ci-fake-key','ALLOWED_EMAILS':'["ci@example.test"]','DATABASE_URL':url,'EPHEMERAL_HOSTING':'true','VIDEO_UPLOADS_ENABLED':'false','DATA_DIR':'/tmp/recall','PORT':'18000'}
    args=['run','-d','--name','recall-check','--network','host','--memory','512m']
    for key,value in env.items():args+=['-e',key+'='+value]
    docker(*args,'recall:check');ready()
    assert request('/')[0]==200
    for path in ['/api/lectures','/api/lectures/private/media']:assert request(path)[0]==401
    assert request('/docs')[0]==404
    docker('exec','recall-check','ffmpeg','-version')
    seed="from app.config import Config;from app.sessions import SessionStore;from app.auth import workspace;from app.storage import repository_for;c=Config();SessionStore(c.data_dir/'auth.sqlite',c.database_url.get_secret_value()).issue('ci-sub','ci@example.test');r=repository_for(workspace(c,'ci-sub'));from app.models import SourceDescriptor;r.save_source(SourceDescriptor(lecture_id='container-check',title='Container persistence check',duration=60,source_kind='youtube',youtube_id='C842vFY5kRo'))"
    docker('exec','recall-check','python','-c',seed)
    # Destroy the writable filesystem by recreating the whole container.
    docker('stop','recall-check');docker('rm','recall-check')
    docker(*args,'recall:check');ready()
    check="from app.config import Config;from app.auth import workspace;from app.storage import repository_for;from app.sessions import SessionStore;c=Config();assert repository_for(workspace(c,'ci-sub')).get_source('container-check').title=='Container persistence check';s=SessionStore(c.data_dir/'auth.sqlite',c.database_url.get_secret_value());\nwith s.connection() as db:assert db.execute('SELECT COUNT(*) AS n FROM sessions WHERE sub=?',('ci-sub',)).fetchone()['n']==1\nprint('Durable library and sessions retained')"
    assert 'retained' in docker('exec','recall-check','python','-c',check)
    worker=docker('exec','recall-check','python','-c',"import psutil;print(next(p.pid for p in psutil.process_iter(['cmdline']) if p.info['cmdline']==['/usr/local/bin/python','-m','app.worker']))")
    docker('exec','recall-check','python','-c',f'import os,signal;os.kill({int(worker)},signal.SIGTERM)')
    for _ in range(30):
        if docker('inspect','-f','{{.State.Running}}','recall-check')=='false':break
        time.sleep(.5)
    else:raise AssertionError('Supervisor left API alive after worker failed')
    assert docker('inspect','-f','{{.State.ExitCode}}','recall-check')!='0'
    print('512 MB container, TLS database, authentication, ephemeral restart persistence, FFmpeg, and worker failure checks passed.')

if __name__=='__main__':main()
