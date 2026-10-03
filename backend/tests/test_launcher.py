import importlib.util
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
