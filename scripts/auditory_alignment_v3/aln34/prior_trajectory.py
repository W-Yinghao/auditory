"""Saved-state source-development diagnostics; CPU Slurm, no training mutation."""
from datetime import datetime
import json
import os
from pathlib import Path
import numpy as np
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from auditory_alignment_v3 import core
from auditory_alignment_v3.aln34 import learning_budget as B

assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
base=Path(core.OUT);note=base/'aln34/PRIOR_TRAJECTORY_NOTE_20261017.md'
rows={r['experiment_id']:r for r in [json.loads(x) for x in (base/'plan_ext.jsonl').read_text().splitlines()]}
groups=[];finished=set()
for eid,r in sorted(rows.items()):
    if r['spec'].get('stage')!='donor_group':continue
    path=base/'units'/f'{eid}.json'
    if not path.exists():continue
    rec=json.loads(path.read_text())
    if rec.get('status')!='complete' or rec.get('truncated'):continue
    finished.add(eid)
    groups.append({'id':eid,'row':r,'status':'complete','record_sha256':B.sha(path),
                   'mtime':datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(),
                   'epoch_equivalents':rec['ep_eq_used'],'horizon':rec['horizon_ep_eq'],
                   'members':{m:{'curve':v['curve'],'counts':{'main':{'updates':v['updates'],'nonfinite':v['nonfinite_steps']},
                               'side':v['side_branch']}} for m,v in rec['members'].items()}})
for claim in sorted((base/'pool/queue_v3_prior').glob('*.claim')):
    eid=claim.name.removesuffix('.claim')
    if eid in finished or rows[eid]['spec'].get('stage')!='donor_group':continue
    path=base/'ckpt'/f'{eid}_resume.pt'
    if not path.is_file():continue
    state=torch.load(path,map_location='cpu',weights_only=False);r=rows[eid]
    group={'id':eid,'row':r,'status':'running_saved_state','mtime':datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(),
           'epoch_equivalents':state['group_state']['E'],'horizon':state['wsd']['H'],'members':{}}
    for member,curve in state['curves'].items():
        group['members'][member]={'curve':curve,'counts':state['members'][member]['counts']}
    groups.append(group);del state
result={'time':datetime.now().astimezone().isoformat(),'job':os.environ['SLURM_JOB_ID'],'groups':groups,
        'source_sha256':B.sha(__file__),'note_sha256':B.sha(note),'evidence_level':'source development only; no downstream prior result'}
root=Path(core.REPO)/'results/auditory_alignment_v3/aln34/prior_diagnostics';root.mkdir(parents=True,exist_ok=True)
target=root/(datetime.now().strftime('%Y%m%dT%H%M%S')+'.json');B.write(target,result)
fig,axes=plt.subplots(max(1,len(groups)),1,figsize=(9,3.1*max(1,len(groups))),squeeze=False)
summaries=[]
for group,ax in zip(groups,axes[:,0]):
    rr=group['row'];summaries.append({'id':group['id'],'dataset':rr['dataset'],'objective':rr['spec']['objective'],'status':group['status'],'members':{}})
    for member,value in group['members'].items():
        curves=value['curve']
        # The saved donor schema nests validation metrics under dev.  Keep the
        # original curve in the snapshot; normalize only this plotting view.
        finite=[dict(x,ce_dev=x['dev']['ce_bits']) for x in curves
                if np.isfinite(x['dev']['ce_bits'])]
        assert finite, f'No finite source-development CE for {group["id"]}/{member}'
        if not finite:continue
        best=min(finite,key=lambda x:x['ce_dev'])
        summaries[-1]['members'][member]={'first':finite[0]['ce_dev'],'latest':finite[-1]['ce_dev'],
            'best':best['ce_dev'],'best_ep_eq':best['ep_eq'],'counts':value['counts']}
        main=[x for x in finite if x['branch']=='main'];side=[x for x in finite if x['branch']=='side']
        line=ax.plot([x['ep_eq'] for x in main],[x['ce_dev'] for x in main],label=member,lw=1.5)[0]
        if side:ax.plot([x['ep_eq'] for x in side],[x['ce_dev'] for x in side],color=line.get_color(),ls='--',lw=1.)
    ax.set_title(f"Leave-{rr['dataset']}-out · {rr['spec']['objective']} · seed{rr['seed']} · H{group['horizon']} · {group['status']}")
    ax.set_ylabel('Donor-dev CE (bits)');ax.set_xlabel('Epoch equivalents');ax.grid(alpha=.2);ax.legend(ncol=5,fontsize=8)
fig.tight_layout();fig.savefig(target.with_suffix('.png'),dpi=180);fig.savefig(target.with_suffix('.pdf'));plt.close(fig)
B.write(root/'latest_summary.json',{'time':result['time'],'job':result['job'],'snapshot':str(target),'summaries':summaries})
print(json.dumps({'snapshot':str(target),'summaries':summaries}),flush=True)
