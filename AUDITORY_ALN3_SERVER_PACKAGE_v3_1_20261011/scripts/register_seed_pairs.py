#!/usr/bin/env python3
"""Expand role references against the existing plan, NOT a training/job generator.

Reports which seed rows were already registered in v3.0 and which roles require
server binding. Reads no performance results and performs no cluster actions.
"""
from pathlib import Path
import argparse,json,hashlib
import yaml

def canonical(r):
    # Training identity as described in the original core plan, independent of seed.
    d={k:v for k,v in r.items() if k not in {'experiment_id','seed','seed_scope','status'}}
    return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def matches(row,selector):
    for k,v in selector.items():
        actual=row.get(k,row['spec'].get(k))
        if actual not in (v if isinstance(v,list) else [v]):return False
    return True

def register(plan,rules):
    seeds=rules['seeds']
    if len(seeds)!=len(set(seeds)):raise ValueError('Seed list contains duplicates')
    breadth=[r for r in plan if r['seed']==seeds[0]]
    registered={(canonical(r),r['seed']):r['experiment_id'] for r in plan}
    roles=[];unique_required=set()
    for panel in rules['panels']:
        for role in panel['roles']:
            found=[r for r in breadth if matches(r,role['selector'])]
            if not found:raise ValueError(f"Role matches no core row: {panel['id']}/{role['role']}")
            refs=[]
            for row in found:
                key=canonical(row)
                for s in seeds:unique_required.add((key,s))
                refs.append({'reference_3401_id':row['experiment_id'],'dataset':row['dataset'],
                    'subject_fold':row['subject_fold'],'content_fold':row['content_fold'],
                    'spec':row['spec'], 'existing_registered_seed_ids':{str(s):registered.get((key,s)) for s in seeds},
                    'status':'requires_live_completion_and_execution_contract_binding'})
            roles.append({'panel_id':panel['id'],'role':role['role'],'reference_rows':refs})
    return {'version':'ALN3.1','not_a_submission':True,'live_completed_jobs_checked':False,
            'required_seed_values':seeds,'n_unique_logical_seed_requirements':len(unique_required),
            'n_requirements_present_in_old_registration':sum(k in registered for k in unique_required),
            'n_requirements_needing_registration_binding':sum(k not in registered for k in unique_required),
            'note':'Numbers are role requirements, not new GPU fits. Reuse depends on full real execution contracts.',
            'roles':roles}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan',type=Path,required=True);p.add_argument('--rules',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise SystemExit('Refuse overwrite; use new registration file')
    plan=[json.loads(s) for s in a.plan.read_text().splitlines() if s.strip()]
    out=register(plan,yaml.safe_load(a.rules.read_text()));a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='roles'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
