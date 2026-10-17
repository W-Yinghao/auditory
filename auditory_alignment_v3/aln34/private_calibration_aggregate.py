"""Complete-panel aggregation of frozen-checkpoint leave-self-out calibration.

Never report a favorable available subset as the complete 64-child panel.
Device attempts are selected by a fixed provenance rule, not their effect size.
"""
import json
import os
from pathlib import Path
import time

import numpy as np

from . import private_calibration_loo as L
from . import private_calibration_diagnosis as D
from . import private_calibration_device as R
from ..sci_r1 import stats as S


def select_record(eid, device):
    candidates = [L.BASE/'units'/f'{eid}.json', *sorted(R.BASE.glob(f'*/units/{eid}.json'))]
    checked, attempts = [], []
    for path in candidates:
        if not path.exists():
            continue
        r = json.loads(path.read_text())
        assert r['source_unit'] == eid and r['plan_sha256'] == L.sha(L.PLAN)
        attempts.append({'file':str(path),'sha256':L.sha(path),'device':r['device'],'status':r['status'],
                         'reproduction':r['reproduction']})
        if r['status'] == 'complete':
            assert r['reproduction']['pass']
            # Original complete record first, then matching hardware, then lexical path.
            priority = (0 if path.parent.parent==L.BASE else 1, 0 if r['device']==device else 1, str(path))
            checked.append((priority,path,r))
    if not checked:
        return None, attempts
    _,path,r = min(checked,key=lambda x:x[0])
    return (path,r), attempts


def analyze():
    start=time.time()
    plan=L.load_plan()
    selected,attempts,missing=[],{},[]
    for unit in plan['units']:
        eid=unit['row']['experiment_id']
        pair,attempts[eid]=select_record(eid,unit['recorded_device'])
        if pair is None:
            missing.append(eid)
        else:
            path,r=pair
            assert r['source']==unit
            selected.append((unit,path,r))
    status={'required_units':120,'verified_units':len(selected),'missing_or_unverified':missing,
            'attempts':attempts,'job':os.environ['SLURM_JOB_ID'],'source_plan_sha256':L.sha(L.PLAN)}
    D.write(D.RESULT/'loo_execution_status.json',status)
    if missing:
        print(f'PENDING: {len(selected)}/120 verified units; no partial-panel efficacy aggregation',flush=True)
        return
    values={'|'.join(c):{str(seed):{} for seed in D.E.SEEDS} for c in D.CONFIGS}
    provenance={}
    for unit,path,r in selected:
        row=unit['row'];config='|'.join(D.E.config_of(row));seed=str(row['seed'])
        provenance[row['experiment_id']]={'path':str(path),'sha256':L.sha(path),'device':r['device'],
                                         'calibration':r['calibration'],'calibrators':r['calibrators']}
        for child,methods in r['per_participant'].items():
            assert child not in values[config][seed]
            assert len({v['n'] for v in methods.values()})==1
            assert max(x['auc_score'] for x in methods.values())-min(x['auc_score'] for x in methods.values())<1e-12
            values[config][seed][child]=methods
    sets=[set(values['|'.join(c)][str(seed)]) for c in D.CONFIGS for seed in D.E.SEEDS]
    assert all(x==sets[0] for x in sets) and len(sets[0])==64
    ids=sorted(sets[0])
    comparisons=('original_refit','class_kernel')
    columns=[('|'.join(c),other) for c in D.CONFIGS for other in comparisons]
    matrices={metric:np.array([[np.mean([values[c][str(seed)][child]['leave_self_out'][metric]-
                  values[c][str(seed)][child][other][metric] for seed in D.E.SEEDS]) for c,other in columns]
                  for child in ids]) for metric in D.METRICS}
    stats={m:S.summary(a,B=4000,seed=S.group_seed('S34_PRIVATE_LOO',m)) for m,a in matrices.items()}
    levels={}
    for config in values:
        levels[config]={str(seed):{method:{m:float(np.mean([v[method][m] for v in values[config][str(seed)].values()]))
                    for m in D.METRICS} for method in ('class_kernel','original_refit','leave_self_out')}
                    for seed in D.E.SEEDS}
    result={'status':'complete','n_children':64,'n_units':120,'seeds':D.E.SEEDS,'contrast_columns':columns,
            'delta_direction':'LOO minus reference; negative loss change is better','statistics':stats,'levels':levels,
            'source_plan_sha256':L.sha(L.PLAN),'provenance':provenance,'device_attempt_status':status,
            'job':os.environ['SLURM_JOB_ID'],'seconds':time.time()-start,'code_sha256':D.sha(Path(__file__)),
            'limits':['same already-seen children','positive affine leaves ranking unchanged',
                      'finite-tolerance historical reproduction','removes trial self-reference, not all same-person reference']}
    D.write(D.RESULT/'leave_self_out.json',result)
    D.write(D.BASE/'loo_per_identity.json',values)
    lines=['# Private CS calibration: leave-self-out intervention','',
           f'Complete: 120 frozen checkpoints, all three seeds, 64 paired children. Slurm job {os.environ["SLURM_JOB_ID"]}.',
           '','Each encoder and test reference bank is unchanged. Only calibration scores remove the exact contribution of their own trial when that trial was selected into the reference bank. The positive-affine mapping is then refitted. This tests trial self-reference; same-child references remain.',
           '','All selected attempts passed the original numerical reproduction tolerances. Historical failures and device retries are retained in loo_execution_status.json. The selection rule prefers the original passing record, then original hardware, then lexical path; it never uses the intervention effect.',
           '','Loss changes are LOO minus reference, averaged within child over seeds. Negative means improvement. Simultaneous intervals cover all 16 configuration/reference contrasts separately for each endpoint. Seeds and folds do not increase n.',
           '','| Configuration | Reference | NLL change | Simultaneous 95% interval |','|---|---|---:|---|']
    summ=stats['nll_bits']
    for j,(c,other) in enumerate(columns):
        display=c.replace('|',' / ')
        lines.append(f"| {display} | {other} | {summ['est'][j]:+.6f} | [{summ['band_low'][j]:+.6f}, {summ['band_high'][j]:+.6f}] |")
    lines += ['','Exact simultaneous statistics and all per-seed method levels are in `results/auditory_alignment_v3/aln34/private_calibration/leave_self_out.json`. AUC remains exactly unchanged within every rerun because the mapping is monotone on the same scores.',
              '','This intervention does not establish clinical prediction or history-adjusted EEG benefit. It informs the probability interface used by those separate research questions.']
    (Path(core_root())/'docs/auditory_alignment_v3/PRIVATE_CALIBRATION_LOO_RESULTS.md').write_text('\n'.join(lines)+'\n')
    print('COMPLETE: 120 units / 64 identities / 3 seeds; all contrasts retained',flush=True)


def core_root():
    return D.core.REPO


if __name__=='__main__':
    assert os.environ.get('SLURM_JOB_ID'),'Slurm CPU required'
    analyze()
