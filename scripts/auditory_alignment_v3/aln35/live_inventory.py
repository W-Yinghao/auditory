"""Read-only scientific-plan inventory; CPU Slurm required."""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

assert os.environ.get('SLURM_JOB_ID')
ROOT=Path('/home/infres/yinwang/EEG_auditory')
OUT=ROOT/'private/auditory_alignment_v3'
DEST=OUT/'aln35'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
now=datetime.now().astimezone().isoformat()
lanes={}; sources={}
for p in sorted((OUT/'aln34').glob('*/plan.json')):
    plan=read(p);rows=plan.get('rows',[])
    if not rows:continue
    records={}; failed=[]; counts=Counter(); dependencies={}
    for r in rows:
        eid=r.get('id',r.get('experiment_id'))
        record=p.parent/'units'/f'{eid}.json'
        if record.exists():
            value=read(record);state=value.get('status','unknown')
            counts[state]+=1
            records[eid]={'status':state,'record_sha256':sha(record),'truncated':value.get('truncated',False)}
        else:counts['missing']+=1
        if (p.parent/'units'/f'{eid}.FAILED.json').exists():failed.append(eid)
        def collect(value):
            if isinstance(value,dict):
                if 'experiment_id' in value and 'family_id' in value and 'spec' in value:
                    sid=value['experiment_id']
                    possible=[OUT/'ckpt'/f'{sid}_best.pt',p.parent/'ckpt'/f'{sid}_best.pt',
                              OUT/'aln34/data_inner_v1/ckpt'/f'{sid}_best.pt',
                              OUT/'aln34/breadth_inner_v1/ckpt'/f'{sid}_best.pt',
                              OUT/'aln34/private_episode_v2/ckpt'/f'{sid}_best.pt']
                    paths=[str(c) for c in possible if c.is_file()]
                    dependencies[sid]={'row':value,'existing_checkpoint_candidates':paths}
                else:
                    for child in value.values():collect(child)
            elif isinstance(value,list):
                for child in value:collect(child)
        collect(r)
    lanes[p.parent.name]={'plan':str(p),'plan_sha256':sha(p),'registered':len(rows),
                         'counts':dict(counts),'failed_markers':failed,'records':records,
                         'source_checkpoint_availability':dependencies}
for d in ('auditory_alignment_v3/aln34','auditory_alignment_v3/prior33'):
    sources.update({str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/d).glob('*.py'))})
held=OUT/'held_executions.json'
if not held.exists():
    held=OUT/'governance/held_executions.json'
assert held.is_file(), 'resolve real hold list before intake'
queue=subprocess.check_output(['squeue','-u',os.environ['USER'],'-h','-o','%i|%j|%T|%q|%P|%M|%l|%R'],text=True)
value={'snapshot':now,'job':os.environ['SLURM_JOB_ID'],'workspace_git':False,
       'publication_checkout':str(ROOT/'private/github_publish_032/checkout'),
       'remote_main':subprocess.check_output(['git','-C',str(ROOT/'private/github_publish_032/checkout'),'rev-parse','origin/main'],text=True).strip(),
       'core_OUT':str(OUT),'core_sha256':sha(ROOT/'auditory_alignment_v3/core.py'),
       'held_path':str(held),'held_sha256':sha(held),'held_record':read(held),
       'source_hashes':sources,'lanes':lanes,'squeue':queue,
       'checkpoint_scope':'existence check only; each new experiment must bind exact content hashes before execution'}
path=DEST/f'live_inventory_{os.environ["SLURM_JOB_ID"]}.json'
path.write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({'written':str(path),'snapshot':now,'lanes':{k:{a:v[a] for a in ('registered','counts','failed_markers')} for k,v in lanes.items()}},indent=2),flush=True)
