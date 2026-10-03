from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class Model(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)

class Interval(Model):
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    @model_validator(mode='after')
    def ordered(self):
        if self.end <= self.start: raise ValueError('End must follow start')
        return self

class TranscriptSegment(Interval):
    id: str
    text: str = Field(min_length=1)

class ChapterSeed(Interval):
    title: str

class SyllabusNode(Interval):
    id: str
    parent_id: str | None = None
    title: str
    inferred: bool = False

class SyllabusProposal(Interval):
    parent_start: float | None
    title: str
    point_summaries: list[str]
    source_segment_ids: list[str]

class SourceDescriptor(Model):
    lecture_id: str
    title: str
    duration: float = Field(ge=0)
    source_kind: Literal['upload','youtube']
    youtube_id: str | None = None
    media_path: str | None = None
    chapters: list[ChapterSeed] = Field(default_factory=list)

class TeachingPoint(Model):
    id: str
    summary: str
    primary_segment_id: str
    source_segment_ids: list[str]
    visual_gap: bool = False

class CardCandidate(Model):
    point_ids: list[str]
    front: str
    back: str
    source_segment_ids: list[str]
    primary_segment_id: str

class Card(Model):
    id: str
    lecture_id: str
    topic_id: str
    point_ids: list[str]
    front: str
    back: str
    primary_time: float
    source_start: float
    source_end: float
    source_segment_ids: list[str]
    source_excerpt: str

class CoverageGap(Model):
    point_id: str
    reason: str
    primary_time: float | None = None

class GenerationResult(Model):
    cards: list[Card]
    gaps: list[CoverageGap]
    completed_intervals: list[Interval]

class Job(Model):
    id: str
    lecture_id: str
    kind: Literal['prepare','generate']
    stage: Literal['importing','transcribing','syllabus','generating']
    status: Literal['queued','running','succeeded','failed','retryable']
    selected_intervals: list[Interval] = Field(default_factory=list)
    regenerate: bool = False
    completed_units: int = 0
    total_units: int | None = None
    error_code: str | None = None
    error_message: str | None = None

class LectureView(Model):
    id: str
    title: str
    duration: float
    source_kind: str
    youtube_id: str | None
    media_url: str | None
    syllabus: list[SyllabusNode]
    cards: list[Card]
    gaps: list[CoverageGap]
    completed_intervals: list[Interval]
    jobs: list[Job]
