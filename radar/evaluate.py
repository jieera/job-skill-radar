"""Score independent labels; never treat pending labels as an empty reference."""
import argparse
from collections import Counter
import json
from pathlib import Path
from .analysis import ROOT, extract_skills


def evaluate(rows, reviewer):
    reviewed=[r for r in rows if r['review_status']==f'{reviewer}-reviewed' and r.get('expected_skills') is not None]
    counts=Counter();errors=[]
    for row in reviewed:
        actual={s['name'] for s in extract_skills(row['text'])}; expected=set(row['expected_skills'])
        counts['tp']+=len(actual & expected);counts['fp']+=len(actual-expected);counts['fn']+=len(expected-actual)
        if actual!=expected:
            errors.append({'id':row.get('id',row.get('source_job_id')),'false_positives':sorted(actual-expected),'false_negatives':sorted(expected-actual)})
    precision=counts['tp']/(counts['tp']+counts['fp']) if counts['tp']+counts['fp'] else None
    recall=counts['tp']/(counts['tp']+counts['fn']) if counts['tp']+counts['fn'] else None
    return {'reviewer':reviewer,'reviewed_records':len(reviewed),'languages':dict(Counter(r['language'] for r in reviewed)),
            'categories':dict(Counter(r['category'] for r in reviewed)),'tp':counts['tp'],'fp':counts['fp'],'fn':counts['fn'],
            'precision':precision,'recall':recall,'errors':errors,
            'human_precision_target_met': reviewer=='human' and len(reviewed)>=40 and precision is not None and precision>=0.9}


def main():
    p=argparse.ArgumentParser();p.add_argument('--corpus',type=Path,default=ROOT/'docs/evaluation/corpus.json');p.add_argument('--output',type=Path)
    args=p.parse_args();rows=json.loads(args.corpus.read_text())
    result={'scope':'Curated real-job excerpts, closed skill vocabulary; not a held-out full-description benchmark',
            'agent':evaluate(rows,'agent'),'human':evaluate(rows,'human')}
    text=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if args.output:args.output.write_text(text)
    print(text)


if __name__=='__main__':main()
