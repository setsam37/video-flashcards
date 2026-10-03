from ..models import Interval,GenerationResult
from ..jobs import JobQueue
from ..syllabus.selection import normalize,subtract
from ..errors import ProcessingError
from .generate import generate_selection

def generate_job(job,repository,provider):
    nodes=repository.get_nodes(job.lecture_id);segments=repository.get_segments(job.lecture_id)
    if not nodes or not segments:raise ProcessingError('syllabus_missing','Prepare the syllabus and transcript before generating cards.')
    ranges=normalize(job.selected_intervals)
    if not job.regenerate:ranges=subtract(ranges,repository.get_covered(job.lecture_id))
    units=[]
    for chapter in [n for n in nodes if n.parent_id is None]:
        for span in ranges:
            start=max(chapter.start,span.start);end=min(chapter.end,span.end)
            if start<end:units.append(Interval(start=start,end=end))
    queue=JobQueue(repository);queue.update(job.id,stage='generating',total_units=len(units),completed_units=0)
    combined=GenerationResult(cards=[],gaps=[],completed_intervals=[])
    for index,unit in enumerate(units):
        result=generate_selection(job.lecture_id,[unit],nodes,segments,provider)
        if job.regenerate:
            combined.cards.extend(result.cards);combined.gaps.extend(result.gaps);combined.completed_intervals.extend(result.completed_intervals)
        else:repository.commit_generation(job.lecture_id,[unit],result,False)
        queue.update(job.id,completed_units=index+1)
    if job.regenerate:repository.commit_generation(job.lecture_id,ranges,combined,True)
