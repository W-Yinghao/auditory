"""Validate frozen lane modules before atomic coordinator registration."""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path

assert os.environ.get('SLURM_JOB_ID')
BASE=Path('/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v3/aln35')
ap=argparse.ArgumentParser();ap.add_argument('modules',nargs='+');args=ap.parse_args()
path=BASE/'fleet_plugins.json';value=json.loads(path.read_text());reports=[]
for name in args.modules:
    assert name.startswith('auditory_alignment_v3.aln35.')
    m=importlib.import_module(name)
    plan=json.loads(m.PLAN.read_text())
    if hasattr(m,'verify'):m.verify(plan)
    else:
        verified,_=m.open_plan()
        assert verified==plan
    status=m.fleet_status();assert isinstance(status,dict)
    assert status['name'].startswith('c3_s35') and status['lane'].startswith('s35_')
    entry=dict(module=name,sha256=hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest(),name=status['name'],lane=status['lane'])
    previous=[p for p in value['plugins'] if p['module']==name]
    assert not previous or previous==[entry],'registered provider changed; requires a new version'
    if not previous:value['plugins'].append(entry)
    reports.append(status)
temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value,indent=2)+'\n');os.replace(temp,path)
receipt=BASE/f'fleet_enrollment_{os.environ["SLURM_JOB_ID"]}.json'
receipt.write_text(json.dumps({'status':'pass','plugins':value,'readiness':reports},indent=2)+'\n')
print(receipt,flush=True)
