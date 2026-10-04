"""CI checks with fabricated credentials; never contacts Google or OpenAI."""
import json,subprocess,time,urllib.request,urllib.error

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

def main():
    docker('volume','create','recall-check-data')
    env={'APP_MODE':'hosted','PUBLIC_APP_URL':'https://localhost','GOOGLE_CLIENT_ID':'ci-client','GOOGLE_CLIENT_SECRET':'ci-secret','SESSION_SECRET':'ci-only-long-session-secret-32-characters','OPENAI_API_KEY':'ci-fake-key','ALLOWED_EMAILS':'["ci@example.test"]'}
    args=['run','-d','--name','recall-check','-p','127.0.0.1:18000:8000','-v','recall-check-data:/var/data']
    for key,value in env.items():args+=['-e',key+'='+value]
    docker(*args,'recall:check')
    ready()
    assert request('/')[0]==200
    for path in ['/api/lectures','/api/lectures/private/media']:assert request(path)[0]==401
    assert request('/docs')[0]==404
    docker('exec','recall-check','ffmpeg','-version')
    docker('exec','recall-check','python','-c',"from pathlib import Path;Path('/var/data/persistence-check').write_text('saved');from app.sessions import SessionStore;SessionStore(Path('/var/data/auth.sqlite')).issue('ci-sub','ci@example.test')")
    docker('restart','recall-check');ready()
    assert docker('exec','recall-check','cat','/var/data/persistence-check')=='saved'
    count=docker('exec','recall-check','python','-c',"import sqlite3;print(sqlite3.connect('/var/data/auth.sqlite').execute('SELECT COUNT(*) FROM sessions').fetchone()[0])")
    assert count=='1'
    worker=docker('exec','recall-check','python','-c',"import psutil;print(next(p.pid for p in psutil.process_iter(['cmdline']) if p.info['cmdline']==['/usr/local/bin/python','-m','app.worker']))")
    docker('exec','recall-check','python','-c',f'import os,signal;os.kill({int(worker)},signal.SIGTERM)')
    for _ in range(30):
        if docker('inspect','-f','{{.State.Running}}','recall-check')=='false':break
        time.sleep(.5)
    else:raise AssertionError('Supervisor left API alive after worker failed')
    assert docker('inspect','-f','{{.State.ExitCode}}','recall-check')!='0'
    print('Container startup, FFmpeg, authentication, disk persistence, and worker failure checks passed.')

if __name__=='__main__':main()
