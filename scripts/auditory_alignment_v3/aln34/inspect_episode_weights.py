from datetime import datetime
import json
import os
from pathlib import Path
import numpy as np
import torch
from auditory_alignment_v3.aln34 import episode_training as E, learning_budget as B
from auditory_alignment_v3 import core
assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
eid='ALN34E_9258613073b62a3b';rp=E.BASE/'units'/f'{eid}.json';record=json.loads(rp.read_text())
plan=json.loads(E.PLAN.read_text());E.verify(plan)
assert record['status']=='complete' and not record['probe'] and record['plan_sha256']==B.sha(E.PLAN)
out={}
for stage,r in record['stages'].items():
    source=Path(r['provenance']['path']);assert B.sha(source)==r['provenance']['checkpoint_sha256']
    ss=torch.load(source,map_location='cpu',weights_only=False);initial=ss['enc'] if 'enc' in ss else ss['model']
    cp={regime:E.STORE/'production'/eid/stage/f'{regime}.pt' for regime in E.REGIMES}
    assert all(B.sha(p)==r['checkpoints'][regime] for regime,p in cp.items())
    state={regime:torch.load(p,map_location='cpu',weights_only=False)['model'] for regime,p in cp.items()}
    assert set(initial)==set(state['ordinary'])==set(state['episode'])
    sums=dict.fromkeys(('source','ordinary_update','episode_update','difference','update_dot'),0.)
    maximum=0.;n=0
    for key,x in initial.items():
        a,b=state['ordinary'][key],state['episode'][key]
        if not x.is_floating_point():
            assert torch.equal(x,a) and torch.equal(x,b);continue
        x,a,b=x.double(),a.double(),b.double();da,db=a-x,b-x;d=b-a
        sums['source']+=float(x.square().sum());sums['ordinary_update']+=float(da.square().sum())
        sums['episode_update']+=float(db.square().sum());sums['difference']+=float(d.square().sum())
        sums['update_dot']+=float((da*db).sum());maximum=max(maximum,float(d.abs().max()));n+=x.numel()
    loss={k:np.asarray(r['training'][k]['losses']) for k in E.REGIMES}
    assert all(len(v)==100 for v in loss.values())
    out[stage]={'float_elements':n,'difference_relative_to_source':np.sqrt(sums['difference']/sums['source']),
                'difference_relative_to_ordinary_update':np.sqrt(sums['difference']/sums['ordinary_update']),
                'update_cosine':sums['update_dot']/np.sqrt(sums['ordinary_update']*sums['episode_update']),
                'maximum_abs_weight_difference':maximum,'maximum_abs_training_loss_difference':float(np.max(np.abs(loss['ordinary']-loss['episode']))),
                'checkpoint_sha256':r['checkpoints'],'source_checkpoint_sha256':r['provenance']['checkpoint_sha256']}
result={'time':datetime.now().astimezone().isoformat(),'job':os.environ['SLURM_JOB_ID'],'id':eid,'record_sha256':B.sha(rp),
        'source_sha256':B.sha(__file__),'note_sha256':B.sha(Path(core.OUT)/'aln34/EPISODE_WEIGHT_DIAGNOSTIC_NOTE_20261017.md'),'stages':out,
        'scope':'one completed bundle; weight-space diagnostics, not functional equivalence or population inference'}
B.write(Path(core.REPO)/'results/auditory_alignment_v3/aln34/episode_diagnostics/first_weights.json',result)
lines=['# First episode continuation: weight-space intervention','',f"{result['time']}; CPU job{result['job']}; `{eid}`.",'',
       'Post hoc diagnosis following the very small ordinary/episode risk differences in the first returned bundle. No training, test-based policy fallback or source edit. Original and continuation SHA256 checks passed for both inner and outer sources.','',
       '| Stage | ‖episode−ordinary‖ / ‖source‖ | ‖episode−ordinary‖ / ‖ordinary−source‖ | Update cosine | Largest weight difference | Largest training-loss difference |',
       '|---|---:|---:|---:|---:|---:|']
for stage,v in out.items():
    lines.append(f"| {stage} | {v['difference_relative_to_source']:.6e} | {v['difference_relative_to_ordinary_update']:.6e} | {v['update_cosine']:.9f} | {v['maximum_abs_weight_difference']:.6e} | {v['maximum_abs_training_loss_difference']:.6e} |")
lines += ['', 'Norms alone do not imply functional equivalence. This is one configuration/fold/content/seed; complete the registered panel and assess actual prediction changes before extending the same episode recipe. Small differences here do not establish that episodic training in general is ineffective. The selected outer100-update risks are worse than the original source in this cell, despite inner selection; preserve those outcomes rather than switching back using outer test.']
(Path(core.REPO)/'docs/auditory_alignment_v3/FIRST_EPISODE_WEIGHT_DIAGNOSTIC.md').write_text('\n'.join(lines)+'\n')
print('Episode weight audit PASS',out,flush=True)
