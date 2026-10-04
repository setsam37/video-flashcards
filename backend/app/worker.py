def run_once(queue,handlers):
    job=queue.claim()
    if not job:return False
    try:
        handlers[job.kind](job)
        queue.update(job.id,status='succeeded')
    except Exception as error:
        queue.fail(job.id,getattr(error,'code','processing_failed'),getattr(error,'public_message','Processing failed. Retry the job or check local configuration.'))
    return True

class WorkspaceWorker:
    def __init__(self,config):
        self.config=config;self.workspaces={}

    def tick(self):
        import re
        from .storage import repository_for
        from .database import AccountRegistry
        from .jobs import JobQueue
        from .providers.openai_provider import OpenAIProvider
        from .syllabus.build import prepare_lecture
        from .cards.service import generate_job
        paths=[self.config.data_dir]
        if self.config.app_mode=='hosted':
            accounts=self.config.data_dir/'accounts'
            if self.config.database_url.get_secret_value():
                paths=[accounts/id for id in AccountRegistry(self.config.database_url.get_secret_value()).list()]
            else:paths=sorted(p for p in accounts.iterdir() if p.is_dir() and not p.is_symlink() and re.fullmatch('[a-f0-9]{64}',p.name) and (p/'study.sqlite').is_file()) if accounts.exists() else []
        worked=False
        for path in paths:
            if path not in self.workspaces:
                config=self.config.model_copy(update={'data_dir':path,'workspace_id':path.name if self.config.app_mode=='hosted' else 'root'}).prepare()
                repo=repository_for(config);queue=JobQueue(repo);queue.recover_interrupted()
                self.workspaces[path]=(repo,queue,OpenAIProvider(config))
            repo,queue,provider=self.workspaces[path]
            handlers={'prepare':lambda job:prepare_lecture(job,repo,provider),'generate':lambda job:generate_job(job,repo,provider)}
            worked=run_once(queue,handlers) or worked
        return worked

def main():
    import time
    import threading
    from .config import Config
    from .database import DatabaseUnavailable
    config=Config().prepare();worker=WorkspaceWorker(config)
    def heartbeat():
        while True:
            pending=config.data_dir/'worker-heartbeat.tmp'
            pending.write_text(str(time.time()));pending.replace(config.data_dir/'worker-heartbeat');time.sleep(2)
    threading.Thread(target=heartbeat,daemon=True).start()
    while True:
        try:
            if not worker.tick():time.sleep(2)
        except DatabaseUnavailable:time.sleep(5)

if __name__=='__main__':main()
