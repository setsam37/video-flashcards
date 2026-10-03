from ..models import GenerationResult,CoverageGap
from .validate import validate_candidate,stable_id,normalized,in_selection
from ..syllabus.selection import normalize

def windows(segments,selected):
    chosen=[s for s in segments if in_selection(s.start,selected)]
    batch=[];length=0
    for segment in chosen:
        if batch and length+len(segment.text)>10000:
            yield batch;batch=[];length=0
        batch.append(segment);length+=len(segment.text)
    if batch:yield batch

def generate_selection(lecture_id,selected,nodes,segments,provider):
    selected=normalize(selected);cards={};gaps={};seen_points=set()
    for batch in windows(segments,selected):
        evidence_ids={s.id for s in batch}
        context=[s for s in segments if s.id not in evidence_ids and s.end>batch[0].start-30 and s.start<batch[-1].end+30]
        remaining=max(0,12000-sum(len(s.text) for s in batch));bounded=[]
        for s in context:
            if len(s.text)<=remaining:bounded.append(s);remaining-=len(s.text)
        evidence=batch+bounded
        raw=provider.extract_points(evidence,selected)
        points=[]
        for p in raw:
            if p.primary_segment_id not in evidence_ids or not p.summary.strip():continue
            if not p.source_segment_ids or any(id not in {s.id for s in evidence} for id in p.source_segment_ids):continue
            id=stable_id(lecture_id+':'+p.primary_segment_id+':'+normalized(p.summary))
            if id in seen_points:continue
            seen_points.add(id);p=p.model_copy(update={'id':id})
            if p.visual_gap:gaps[id]=CoverageGap(point_id=id,reason=f'{p.summary}: the explanation depends on visual material not captured in the transcript.')
            else:points.append(p)
        pending=points
        covered=set()
        for attempt in range(2):
            if not pending:break
            for candidate in provider.generate_cards(pending,evidence):
                try:
                    card=validate_candidate(candidate,points,evidence,selected,lecture_id=lecture_id,nodes=nodes)
                    cited=[s for s in evidence if s.id in candidate.source_segment_ids]
                    if not provider.check_support(candidate,cited):continue
                    cards[card.id]=card;covered.update(card.point_ids)
                except ValueError:continue
            pending=[p for p in points if p.id not in covered]
        for p in pending:gaps[p.id]=CoverageGap(point_id=p.id,reason=f'{p.summary}: a supported flashcard could not be generated after one retry.')
    if not cards and not gaps:gaps['empty_'+stable_id(str(selected))]=CoverageGap(point_id='empty_'+stable_id(str(selected)),reason='No substantive teaching points were identified in these selected transcript ranges.')
    return GenerationResult(cards=sorted(cards.values(),key=lambda c:(c.primary_time,c.id)),gaps=list(gaps.values()),completed_intervals=selected)
