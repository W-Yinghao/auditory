"""Read-only descriptive science on the first returned episode bundle; Slurm CPU."""
from datetime import datetime
import json
import os
from pathlib import Path
import numpy as np
from auditory_alignment_v3.aln34 import episode_training as E, learning_budget as B
from auditory_alignment_v3 import core

assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
note=Path(core.OUT)/'aln34/FIRST_EPISODE_ANALYSIS_NOTE_20261017.md'
eid='ALN34E_9258613073b62a3b';path=E.BASE/'units'/f'{eid}.json'
record=json.loads(path.read_text());plan=json.loads(E.PLAN.read_text());E.verify(plan)
assert record['status']=='complete' and not record['probe'] and record['plan_sha256']==B.sha(E.PLAN)
assert record['unit']==next(u for u in plan['rows'] if u['id']==eid)
row=record['unit']['outer']['row'];table=[];ledgers={}
for stage,v in record['stages'].items():
    ledgers[stage]=v['training']
    a,b=(v['training'][k] for k in ('ordinary','episode'))
    for key in ('encoder_updates','source_ids','support_steps','query_anchors','support_eligible_anchors'):
        assert a[key]==b[key]
    assert a['encoder_updates']==100
    for fraction in ('0.1','0.3'):
        for steps in ('0','5','20'):
            pp={k:v['candidates'][k][fraction][steps]['per_participant'] for k in ('source','ordinary','episode')}
            ids=sorted(pp['source']);assert all(set(p)==set(ids) for p in pp.values())
            for mode in ('native','unified'):
                assert all(pp[k][i][mode]['n_query']==pp['source'][i][mode]['n_query'] for k in pp for i in ids)
                means={k:{m:float(np.mean([p[i][mode][m] for i in ids])) for m in ('true_nll_bits','mismatch_gain_bits')} for k,p in pp.items()}
                table.append({'stage':stage,'support':fraction,'steps':steps,'readout':mode,'n':len(ids),'means':means,
                    'episode_vs_ordinary_risk_benefit':means['ordinary']['true_nll_bits']-means['episode']['true_nll_bits'],
                    'episode_vs_ordinary_mismatch_gain_change':means['episode']['mismatch_gain_bits']-means['ordinary']['mismatch_gain_bits']})
selected=[]
for frac in ('0.1','0.3'):
    pp={r:record['choices'][r][frac]['outer']['per_participant'] for r in ('ordinary','episode')}
    ids=sorted(pp['ordinary']);assert set(ids)==set(pp['episode'])
    for mode in ('native','unified'):
        risks={r:float(np.mean([p[i][mode]['true_nll_bits'] for i in ids])) for r,p in pp.items()}
        selected.append({'support':frac,'readout':mode,'n':len(ids),
             'chosen':{r:record['choices'][r][frac]['chosen'] for r in pp},'risks':risks,
             'episode_vs_ordinary_benefit':risks['ordinary']-risks['episode']})
result={'time':datetime.now().astimezone().isoformat(),'job':os.environ['SLURM_JOB_ID'],'id':eid,
        'row':row,'record_sha256':B.sha(path),'plan_sha256':B.sha(E.PLAN),'note_sha256':B.sha(note),
        'source_sha256':B.sha(__file__),'fixed_candidates':table,'selected':selected,'ledgers':ledgers,
        'scope':'first completion only, one outer person/content/seed cell; descriptive, not a full panel'}
B.write(Path(core.REPO)/'results/auditory_alignment_v3/aln34/episode_diagnostics/first_returned.json',result)
lines=['# First returned ordinary/episode continuation bundle','',f"{result['time']}; CPU job{result['job']}; `{eid}`.",'',
       f"Source: {row['dataset']}, {row['spec']['architecture']}, {row['spec'].get('adaptation','local')}, seed{row['seed']}, person fold{row['subject_fold']}, content fold{row['content_fold']}.",'',
       'Chosen by completion order, not efficacy. One fold/content/seed only, without population intervals. Equal-person risks in bits/query. Source/ordinary/episode share identities and query counts; native/unified stay separate. Every fixed candidate and both inner/outer ledgers are in the JSON. No frozen design or schedule is changed.','',
       '| Source stage | Regime | Updates | Source people | Support steps | Query anchors | Relative parameter change | Seconds |',
       '|---|---|---:|---:|---:|---:|---:|---:|']
for stage,values in ledgers.items():
    for regime,v in values.items():
        lines.append(f"| {stage} | {regime} | {v['encoder_updates']} | {v['source_people']} | {v['support_steps']} | {v['query_anchors']} | {v['relative_parameter_change']:.6f} | {v['seconds']:.1f} |")
lines += ['', '## Whole-pipeline inner-person selected policies, applied to outer people','',
          '| Support | Readout | n | Ordinary choice | Episode choice | Ordinary R | Episode R | Benefit episode−ordinary |',
          '|---|---|---:|---|---|---:|---:|---:|']
for x in selected:
    lines.append(f"| {x['support']} | {x['readout']} | {x['n']} | {x['chosen']['ordinary']} | {x['chosen']['episode']} | {x['risks']['ordinary']:.5f} | {x['risks']['episode']:.5f} | {x['episode_vs_ordinary_benefit']:+.5f} |")
lines += ['', 'Positive benefit means ordinary R minus episode R; it is not the sign of the loss difference. Both selected policies include the original source/0updates and support0steps.','',
          '## Fixed outer candidates (no test selection)','',
          '| Support | Steps | Readout | n | Source R | Ordinary100 R | Episode100 R | Risk benefit | Mismatch-gain change |',
          '|---|---:|---|---:|---:|---:|---:|---:|---:|']
for x in table:
    if x['stage']!='outer':continue
    r={k:v['true_nll_bits'] for k,v in x['means'].items()}
    lines.append(f"| {x['support']} | {x['steps']} | {x['readout']} | {x['n']} | {r['source']:.5f} | {r['ordinary']:.5f} | {r['episode']:.5f} | {x['episode_vs_ordinary_risk_benefit']:+.5f} | {x['episode_vs_ordinary_mismatch_gain_change']:+.5f} |")
lines += ['', 'The full panel and direct group-by-adaptation inference remain pending. Historical filtering and repeated use of the same cohort remain limitations.']
(Path(core.REPO)/'docs/auditory_alignment_v3/FIRST_EPISODE_DIAGNOSTIC.md').write_text('\n'.join(lines)+'\n')
print('First episode diagnostic PASS',selected,flush=True)
