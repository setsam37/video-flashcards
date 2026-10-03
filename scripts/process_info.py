"""Inspect only the processes created by our launcher; refuse mismatched stop records."""
import argparse,json,time,sys
from pathlib import Path
import psutil
MARKERS={'api':'app.main:app','worker':'app.worker','web':'vite.js'}
sys.stdout.reconfigure(encoding='utf-8')

def snapshot(process,role):
    if not any(MARKERS[role] in arg for arg in process.cmdline()):raise ValueError('Process command does not match the application role.')
    return {'id':process.pid,'executable':process.exe(),'created':process.create_time(),'role':role}

def record_tree(process,role):
    records=[snapshot(process,role)]
    for child in process.children(recursive=True):
        if any(MARKERS[role] in arg for arg in child.cmdline()):records.append(snapshot(child,role))
    return records

def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['inspect','stop']);parser.add_argument('--pid',type=int);parser.add_argument('--role',choices=list(MARKERS));parser.add_argument('--record',type=Path);args=parser.parse_args()
    if args.action=='inspect':
        process=psutil.Process(args.pid)
        for _ in range(10):
            children=process.children(recursive=True)
            if children:break
            time.sleep(.1)
        print(json.dumps(record_tree(process,args.role)));return
    records=json.loads(args.record.read_text(encoding='utf-8-sig'))
    if not isinstance(records,list):records=[records]
    verified=[]
    for record in records:
        try:process=psutil.Process(record['id'])
        except psutil.NoSuchProcess:continue
        current=snapshot(process,record['role'])
        if current!=record:raise ValueError('Process identity changed; refusing to stop it.')
        verified.append(process)
    for process in reversed(verified):
        try:process.terminate()
        except psutil.NoSuchProcess:pass
    _,alive=psutil.wait_procs(verified,timeout=5)
    if alive:raise RuntimeError('An application process did not stop. Keep the process record and retry.')
    args.record.unlink()
    print('Recall stopped. Your lectures and cards remain saved.')
if __name__=='__main__':main()
