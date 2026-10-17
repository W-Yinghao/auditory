from datetime import datetime
import json
import os
from pathlib import Path
from auditory_alignment_v3.aln34 import learning_budget as B,strong_fusion as F

assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
eid='ALN34F_6b25803e05105e9f';path=F.BASE/'units'/f'{eid}.json';rec=json.loads(path.read_text())
assert rec['status']=='complete' and not rec['probe'] and rec['plan_sha256']==B.sha(F.PLAN)
rows=[]
for mode in ('native','unified'):
    decision=rec['decisions'][mode];single=decision['strong_single']
    for stage in ('inner','outer'):
        comparisons=rec['stages'][stage]['comparisons']
        first=next(iter(comparisons.values()))
        strong=first['local_direct'] if single=='local' else comparisons[single]['fm_direct']
        sr=F.mean_risk(strong['per_person'][mode])
        for arm,values in comparisons.items():
            lr=F.mean_risk(values['local_direct']['per_person'][mode]);fr=F.mean_risk(values['fm_direct']['per_person'][mode])
            for family,key in decision['pairs'][arm].items():
                selected=values[key]['per_person'][mode];risk=F.mean_risk(selected)
                rows.append({'stage':stage,'mode':mode,'arm':arm,'family':family,'selected':key,'n_people':len(selected),
                             'strong_single':single,'local_risk':lr,'fm_risk':fr,'strong_single_risk':sr,
                             'selected_risk':risk,'benefit_vs_local':lr-risk,'benefit_vs_fm':fr-risk,'benefit_vs_strong_single':sr-risk})
out={'time':datetime.now().astimezone().isoformat(),'job':os.environ['SLURM_JOB_ID'],'unit_id':eid,
     'source_sha256':B.sha(path),'script_sha256':B.sha(__file__),'plan_sha256':rec['plan_sha256'],
     'analysis_note_sha256':B.sha(F.BASE.parent/'FIRST_FUSION_ANALYSIS_NOTE_20261017.md'),'unit':rec['unit'],
     'selection_level':rec['selection_level'],'decisions':rec['decisions'],'rows':rows,
     'interpretation':'first-returned bundle diagnostic; incomplete content/seed panel, no population-effect interval'}
root=Path(F.core.REPO);B.write(root/'results/auditory_alignment_v3/aln34/strong_fusion_function/first_returned.json',out)
lines=['# First returned strong-fusion bundle: diagnostic','',f"{out['time']}; `{eid}`; CPU job{out['job']}.",'',
       'This is the first returned bundle, selected by completion order, not performance. It is not a completed content/seed panel. No population-effect confidence interval is reported. All choices use the registered inner-person development rule; the same choice is applied to outer people. Positive benefit means lower true-query NLL in bits per5s query. Native and unified scores have separate rows. The full fixed-candidate trajectories remain in the original unit.','',
       '| Stage/readout | FM pair | Selected family candidate | n people in this bundle | Direct local R | Direct FM R | Strong single R | Selected R | Benefit vs strong single |','|---|---|---|---:|---:|---:|---:|---:|---:|']
for v in rows:
    lines.append(f"| {v['stage']}/{v['mode']} | {v['arm']} | {v['selected']} | {v['n_people']} | {v['local_risk']:.5f} | {v['fm_risk']:.5f} | {v['strong_single_risk']:.5f} | {v['selected_risk']:.5f} | {v['benefit_vs_strong_single']:+.5f} |")
lines+=['','This inspection does not change the registered candidate set, endpoint, source model or schedule. Complete-identity aggregation and residual-function summaries continue independently.']
(root/'docs/auditory_alignment_v3/FIRST_STRONG_FUSION_DIAGNOSTIC.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'unit':eid,'decisions':rec['decisions'],'outer_rows':[v for v in rows if v['stage']=='outer']},indent=2))
