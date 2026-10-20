"""Independent reproduction against unchanged original actual-mixture outputs."""
import json
import os
from pathlib import Path
import numpy as np
from auditory_alignment_v3.aln35 import fusion_attribution as A

assert os.environ.get('SLURM_JOB_ID')
plan=A.read(A.PLAN);assert plan['sources']==A.sources()
checked=[];largest=0.
for p in sorted((A.BASE/'units').glob('*.json')):
    if p.stem.endswith('_ensemble'):continue
    rec=A.read(p);old=A.read(A.F.BASE/'units'/f'{rec["id"]}.json')
    for mode in ('native','unified'):
        selected=old['decisions'][mode]['pairs']['cb_pre']['probability']
        weight=float(selected.split('/')[1])
        assert rec['modes'][mode]['choices']['actual_mix']['selected']==weight
        ref=old['stages']['outer']['comparisons']['cb_pre'][selected]['per_person'][mode]
        for pid,item in rec['modes'][mode]['per_person'].items():
            delta=abs(item['conditions']['actual_mix']['true_nll_bits']-ref[pid]['true_nll_bits'])
            assert delta<1e-10,(rec['id'],mode,pid,delta)
            largest=max(largest,delta)
    checked.append(rec['id'])
results=A.read(A.RESULTS/'run_1047303/contrasts.json')
coverage={f['family_id']:{g:{k:v[k] for k in ('expected_n','common_complete_n')} for g,v in f['coverage'].items()}
          for f in results['families']}
receipt={'status':'pass','job':os.environ['SLURM_JOB_ID'],'actual_mix_reproduced_units':len(checked),
         'max_person_nll_abs_difference':largest,'source_hashes_unchanged':True,'coverage':coverage}
A.write(A.RESULTS/f'verification_{os.environ["SLURM_JOB_ID"]}.json',receipt)
print(json.dumps(receipt,indent=2),flush=True)
