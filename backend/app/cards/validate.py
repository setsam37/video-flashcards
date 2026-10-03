import hashlib,re
from ..models import Card
from ..syllabus.selection import deepest_topic

def stable_id(text):return hashlib.sha256(text.encode()).hexdigest()[:24]
def normalized(text):return re.sub(r'\s+',' ',text.casefold()).strip()
def in_selection(time,selected):return any(i.start<=time<i.end for i in selected)

def validate_candidate(candidate,points,segments,selected,*,lecture_id,nodes):
    evidence={s.id:s for s in segments};allowed={p.id:p for p in points}
    if not candidate.front.strip() or not candidate.back.strip():raise ValueError('Empty question or answer')
    if not candidate.point_ids or any(id not in allowed or allowed[id].visual_gap for id in candidate.point_ids):raise ValueError('Unknown or visual-only teaching point')
    ids=list(dict.fromkeys(candidate.source_segment_ids))
    if not ids or any(id not in evidence for id in ids):raise ValueError('Unknown evidence')
    if candidate.primary_segment_id not in ids:raise ValueError('Primary evidence must be cited')
    primary=evidence[candidate.primary_segment_id]
    if not in_selection(primary.start,selected):raise ValueError('Primary evidence is outside the selection')
    if not any(allowed[id].primary_segment_id==primary.id for id in candidate.point_ids):raise ValueError('Primary evidence does not match the teaching point')
    cited=sorted([evidence[id] for id in ids],key=lambda s:s.start)
    cardid=stable_id(lecture_id+':'+','.join(sorted(candidate.point_ids))+':'+normalized(candidate.front))
    return Card(id=cardid,lecture_id=lecture_id,topic_id=deepest_topic(nodes,primary.start),point_ids=candidate.point_ids,front=candidate.front.strip(),back=candidate.back.strip(),primary_time=primary.start,source_start=cited[0].start,source_end=max(s.end for s in cited),source_segment_ids=ids,source_excerpt=' '.join(s.text for s in cited))
