import importlib.util,sys,time,threading
from pathlib import Path
import psutil
from app.config import Config

spec=importlib.util.spec_from_file_location('serve',Path(__file__).resolve().parents[2]/'scripts/serve.py')
serve=importlib.util.module_from_spec(spec);spec.loader.exec_module(serve)

def command(pid_file,exit_code=None):
    script='import os,time,pathlib;pathlib.Path('+repr(str(pid_file))+').write_text(str(os.getpid()));time.sleep(.4);'
    script+='raise SystemExit('+str(exit_code)+')' if exit_code is not None else 'time.sleep(60)'
    return [sys.executable,'-c',script]

def test_child_failure_stops_and_reaps_the_other_process(tmp_path):
    one=tmp_path/'one';two=tmp_path/'two'
    assert serve.supervise([command(one,7),command(two)],threading.Event(),grace=1)==7
    assert one.exists() and two.exists()
    assert all(not psutil.pid_exists(int(path.read_text())) for path in [one,two])

def test_requested_shutdown_stops_both_processes(tmp_path):
    one=tmp_path/'one';two=tmp_path/'two';stop=threading.Event()
    timer=threading.Timer(1,stop.set);timer.start()
    try:assert serve.supervise([command(one),command(two)],stop,grace=1)==0
    finally:timer.cancel()
    assert all(path.exists() and not psutil.pid_exists(int(path.read_text())) for path in [one,two])

def test_local_supervisor_keeps_the_unauthenticated_library_on_loopback(tmp_path):
    commands=serve.commands(Config(_env_file=None,data_dir=tmp_path))
    api=commands[0]
    assert api[api.index('--host')+1]=='127.0.0.1'
