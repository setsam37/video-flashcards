export type Interval={start:number;end:number};
export type SyllabusNode=Interval&{id:string;parent_id:string|null;title:string;inferred:boolean};
export type Card={id:string;lecture_id:string;topic_id:string;point_ids:string[];front:string;back:string;primary_time:number;source_start:number;source_end:number;source_segment_ids:string[];source_excerpt:string};
export type Job={id:string;lecture_id:string;kind:'prepare'|'generate';stage:'importing'|'transcribing'|'syllabus'|'generating';status:'queued'|'running'|'succeeded'|'failed'|'retryable';selected_intervals:Interval[];regenerate:boolean;completed_units:number;total_units:number|null;error_code:string|null;error_message:string|null};
export type LectureView={id:string;title:string;duration:number;source_kind:string;youtube_id:string|null;media_url:string|null;syllabus:SyllabusNode[];cards:Card[];gaps:{point_id:string;reason:string;primary_time?:number|null}[];completed_intervals:Interval[];jobs:Job[]};
export type LectureSummary={id:string;title:string;duration:number};
export type StudyMode='topic'|'all'|'custom';
export type StudyLaunch={mode:StudyMode;intervals:Interval[]};
