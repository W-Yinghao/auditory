"""Slurm-only read of saved donor states; never touches a training checkpoint."""
import json
import os
from pathlib import Path
from datetime import datetime
import torch
from auditory_alignment_v3 import core
from auditory_alignment_v3.aln34 import learning_budget as B

assert os.environ.get('SLURM_JOB_ID')
out = Path(core.OUT)
rows = {r['experiment_id']: r for r in [json.loads(x) for x in (out/'plan_ext.jsonl').read_text().splitlines()]}
values = []
for claim in sorted((out/'pool/queue_v3_prior').glob('*.claim')):
    eid = claim.name.removesuffix('.claim'); row = rows[eid]
    p = out/'ckpt'/f'{eid}_resume.pt'
    item = {'id': eid, 'family': row['family_id'], 'job': (claim/'job').read_text().strip(), 'resume_exists': p.exists()}
    if p.is_file():
        r = torch.load(p, map_location='cpu', weights_only=False)
        item['resume_mtime'] = datetime.fromtimestamp(p.stat().st_mtime).astimezone().isoformat()
        if 'group_state' in r:
            g = r['group_state']; w = r['wsd']
            item.update(step=g['step'], epoch_equivalents=g['E'], branch=g['branch'], validations=g['i_val'],
                        horizon=w['H'], compute_limit=w['limit'], done=r['done'],
                        members=r['members_order'], timing=g['timing'])
        else:
            item['resume_keys'] = sorted(r)
        del r
    values.append(item)
result = {'time': datetime.now().astimezone().isoformat(), 'job': os.environ['SLURM_JOB_ID'], 'saved_states': values,
          'interpretation': 'saved validation boundaries only, not live GPU utilization or completed efficacy'}
B.write(out/'aln34/prior_progress.json', result)
for r in values:
    print(json.dumps({k:v for k,v in r.items() if k != 'timing'}))
