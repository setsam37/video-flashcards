def run_once(queue,handlers):
    job=queue.claim()
    if not job:return False
    try:
        handlers[job.kind](job)
        queue.update(job.id,status='succeeded')
    except Exception as error:
        queue.fail(job.id,getattr(error,'code','processing_failed'),getattr(error,'public_message','Processing failed. Retry the job or check local configuration.'))
    return True
