"""Run one API and one worker; fail together and forward shutdown to children."""
import os,signal,subprocess,sys,threading,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def stop_process(process,grace):
    descendants=[]
    if os.name=='nt':
        import psutil
        try:descendants=psutil.Process(process.pid).children(recursive=True)
        except psutil.NoSuchProcess:pass
        for child in descendants:
            try:child.terminate()
            except psutil.NoSuchProcess:pass
    def send(sig):
        try:
            if os.name=='posix':os.killpg(process.pid,sig)
            elif process.poll() is None:
                if sig==signal.SIGTERM:process.terminate()
                else:process.kill()
        except ProcessLookupError:pass
    send(signal.SIGTERM)
    try:process.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        send(signal.SIGKILL if os.name=='posix' else signal.SIGTERM);process.kill();process.wait()
    # Also reap subprocesses (e.g. FFmpeg) left in the group after the parent exited.
    if os.name=='posix':send(signal.SIGKILL)
    if descendants:
        _,alive=psutil.wait_procs(descendants,timeout=grace)
        for child in alive:
            try:child.kill()
            except psutil.NoSuchProcess:pass
        psutil.wait_procs(alive,timeout=grace)

def supervise(commands,stop,grace=10):
    processes=[]
    try:
        for command in commands:
            processes.append(subprocess.Popen(command,start_new_session=os.name=='posix'))
        while not stop.wait(.1):
            for process in processes:
                result=process.poll()
                if result is not None:return result or 1
        return 0
    finally:
        for process in processes:stop_process(process,grace)

def commands(config):
    host='0.0.0.0' if config.app_mode=='hosted' else '127.0.0.1'
    return [[sys.executable,'-m','uvicorn','app.main:app','--host',host,'--port',os.environ.get('PORT','8000'),'--no-access-log'],[sys.executable,'-m','app.worker']]

def main():
    sys.path.insert(0,str(ROOT/'backend'))
    from app.config import Config
    config=Config().prepare()
    os.environ['PYTHONPATH']=str(ROOT/'backend')
    os.environ['TMPDIR']=os.environ['TEMP']=os.environ['TMP']=str(config.data_dir/'tmp')
    os.environ['PYTHONUNBUFFERED']='1'
    (config.data_dir/'worker-heartbeat').unlink(missing_ok=True)
    stop=threading.Event()
    for sig in [signal.SIGINT,signal.SIGTERM]:signal.signal(sig,lambda *_:stop.set())
    return supervise(commands(config),stop)

if __name__=='__main__':raise SystemExit(main())
