def run_once(queue,handlers):
    job=queue.claim()
    if not job:return False
    try:
        handlers[job.kind](job)
        queue.update(job.id,status='succeeded')
    except Exception as error:
        queue.fail(job.id,getattr(error,'code','processing_failed'),getattr(error,'public_message','Processing failed. Retry the job or check local configuration.'))
    return True

def main():
    import time
    from .config import Config
    from .storage import Repository
    from .jobs import JobQueue
    from .providers.openai_provider import OpenAIProvider
    from .syllabus.build import prepare_lecture
    from .cards.service import generate_job
    config=Config().prepare();repo=Repository(config.data_dir/'study.sqlite');queue=JobQueue(repo);provider=OpenAIProvider(config)
    queue.recover_interrupted()
    handlers={'prepare':lambda job:prepare_lecture(job,repo,provider),'generate':lambda job:generate_job(job,repo,provider)}
    while True:
        if not run_once(queue,handlers):time.sleep(2)

if __name__=='__main__':main()
