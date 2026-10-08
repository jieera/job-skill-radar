import type {Job, Filters, Skill} from './types.ts';
export const defaults:Filters = {market:'all',company:'all',category:'all',seniority:'early',requirement:'all',search:'',skill:''};
export const matchesRequirement = (skill:Skill, requirement:string) => requirement==='all'||skill.evidence.some(e=>e.requirement===requirement);
export function filterJobs(jobs:Job[], f:Filters):Job[] {
  return [...new Map(jobs.map(j=>[j.id,j])).values()].filter(j=>j.active &&
    (f.market==='all'||j.markets.includes(f.market)) && (f.company==='all'||j.source===f.company) &&
    (f.category==='all'||j.categories.includes(f.category)) &&
    (f.seniority==='all'||(f.seniority==='early'?['intern','graduate'].includes(j.seniority):j.seniority===f.seniority)) &&
    (!f.search||`${j.title} ${j.company} ${j.location} ${j.skills.map(s=>s.name).join(' ')}`.toLowerCase().includes(f.search.toLowerCase())) &&
    (!f.skill||j.skills.some(s=>s.name===f.skill&&matchesRequirement(s,f.requirement))));
}
export function ranking(jobs:Job[], requirement:string) {
  const counts = new Map<string,number>();
  for (const job of new Map(jobs.map(j=>[j.id,j])).values()) {
    for (const name of new Set(job.skills.filter(s=>matchesRequirement(s,requirement)).map(s=>s.name))) counts.set(name,(counts.get(name)||0)+1);
  }
  const total=new Set(jobs.map(j=>j.id)).size;
  return [...counts].map(([name,count])=>({name,count,percent:total?count/total*100:0})).sort((a,b)=>b.count-a.count||a.name.localeCompare(b.name));
}
export function csv(jobs:Job[], requirement='all') {
  const cell = (value:unknown) => {let s=String(value??''); if (/^[\s]*[=+@-]/.test(s)) s="'"+s; return '"'+s.replaceAll('"','""')+'"';};
  const header=['id','company','title','markets','location','seniority','categories','skill','requirement','evidence','source_url','last_seen'];
  const rows=jobs.flatMap(j=>{
    const base=[j.id,j.company,j.title,j.markets.join(';'),j.location,j.seniority,j.categories.join(';')];
    const evidence=j.skills.flatMap(s=>s.evidence.filter(e=>requirement==='all'||e.requirement===requirement).map(e=>[...base,s.name,e.requirement,e.text,j.url,j.last_seen]));
    return evidence.length?evidence:[[...base,'','','',j.url,j.last_seen]];
  });
  return '\ufeff'+[header,...rows].map(r=>r.map(cell).join(',')).join('\r\n');
}
