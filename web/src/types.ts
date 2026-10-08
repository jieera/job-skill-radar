export type Requirement = 'required' | 'preferred' | 'mentioned' | 'unknown';
export type Skill = {name:string; evidence:{text:string; requirement:Requirement}[]};
export type Job = {id:string; source:string; company:string; title:string; location:string; markets:string[]; categories:string[]; seniority:string; url:string; posted_at:string|null; first_seen:string; last_seen:string; updated_at:string; active:boolean; missing_runs:number; skills:Skill[]};
export type Source = {id:string; name:string; market:string; url:string; scope:string; status:'ok'|'partial'|'error'|'pending'; message:string; checked_at:string; last_success:string|null; job_count:number};
export type Snapshot = {schema_version:number; generated_at:string|null; sources:Source[]; jobs:Job[]};
export type Filters = {market:string; company:string; category:string; seniority:string; requirement:string; search:string; skill:string};
