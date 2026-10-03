from ..models import Interval,SyllabusNode

def normalize(intervals: list[Interval]) -> list[Interval]:
    merged=[]
    for interval in sorted(intervals,key=lambda x:x.start):
        if merged and interval.start<=merged[-1].end:
            merged[-1]=Interval(start=merged[-1].start,end=max(merged[-1].end,interval.end))
        else:merged.append(Interval(start=interval.start,end=interval.end))
    return merged

def subtract(selected: list[Interval],covered: list[Interval]) -> list[Interval]:
    remaining=normalize(selected)
    for cut in normalize(covered):
        output=[]
        for item in remaining:
            if cut.end<=item.start or cut.start>=item.end:output.append(item);continue
            if item.start<cut.start:output.append(Interval(start=item.start,end=cut.start))
            if cut.end<item.end:output.append(Interval(start=cut.end,end=item.end))
        remaining=output
    return remaining

def toggle_node(selected: list[Interval],node: SyllabusNode,checked: bool) -> list[Interval]:
    span=Interval(start=node.start,end=node.end)
    return normalize(selected+[span]) if checked else subtract(selected,[span])

def deepest_topic(nodes: list[SyllabusNode],primary_time: float) -> str:
    containing=[n for n in nodes if n.start<=primary_time<n.end]
    if not containing:raise ValueError('Evidence timestamp is outside the syllabus')
    return min(containing,key=lambda n:(n.end-n.start,n.parent_id is None)).id
