import importlib.util,subprocess,sys
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('process_info',Path(__file__).parents[2]/'scripts/process_info.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class Process:
    def __init__(self,pid,command,children=()):self.pid=pid;self.command=command;self.nested=children
    def cmdline(self):return self.command
    def exe(self):return 'python.exe'
    def create_time(self):return float(self.pid)
    def children(self,recursive=False):return self.nested

def test_launch_records_python_wrapper_and_worker_but_not_console_host():
    child=Process(2,['python.exe','-m','app.worker'])
    console=Process(3,['conhost.exe'])
    root=Process(1,['python.exe','-m','app.worker'],[console,child])
    assert [record['id'] for record in module.record_tree(root,'worker')]==[1,2]

def test_launch_rejects_a_root_process_with_a_different_command():
    with pytest.raises(ValueError):module.record_tree(Process(1,['python.exe','another_app.py']),'api')

def select_python(app_root,runtime_expression='$null'):
    powershell=Path('C:/Users/anyor/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')
    if sys.platform!='win32' or not powershell.exists():pytest.skip('PowerShell runtime selection check requires the local Windows test runtime.')
    script=Path(__file__).parents[2]/'scripts/runtime.ps1'
    command=f". '{str(script).replace(chr(39),chr(39)*2)}'; Get-RecallPython -AppRoot '{str(app_root).replace(chr(39),chr(39)*2)}' -Runtime {runtime_expression}"
    result=subprocess.run([str(powershell),'-NoProfile','-Command',command],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    return result.stdout.strip()

def test_fresh_setup_launcher_uses_the_created_virtual_environment(tmp_path):
    python=tmp_path/'.venv/Scripts/python.exe';python.parent.mkdir(parents=True);python.touch()
    assert Path(select_python(tmp_path))==python

def test_explicit_configured_runtime_takes_priority_over_local_environment(tmp_path):
    python=tmp_path/'.venv/Scripts/python.exe';python.parent.mkdir(parents=True);python.touch()
    assert select_python(tmp_path,"([pscustomobject]@{python='configured-python.exe'})")=='configured-python.exe'
