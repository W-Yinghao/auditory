"""Functional diagnostics of the new inner-selected strong-model residuals."""
from datetime import datetime
import os
from pathlib import Path
import shutil
from .. import core, bc_interim
from . import learning_budget as B, new_lane_aggregate as A, science_aggregate as S

FIELDS=('relative_residual','relative_parallel','relative_orthogonal','before_normalization_change',
        'after_normalization_change','angle_radians','mean_abs_calibrated_score_change',
        'probability_total_variation','argmax_change','risk_benefit_vs_local','matched_benefit_vs_wrong_fm')


def selected_values(record,arm,mode):
    key=record['decisions'][mode]['pairs'][arm]['residual'];step=key.split('/')[1]
    stage=record['stages']['outer'];values={}
    for person,d in stage['diagnostics'][arm][key].items():
        comparisons=stage['comparisons'][arm]
        selected=comparisons[key]['per_person'][mode][person]['true_nll_bits']
        local=comparisons['local_direct']['per_person'][mode][person]['true_nll_bits']
        wrong=comparisons['residual_mismatched_fm/'+step]['per_person'][mode][person]['true_nll_bits']
        values[person]={**{k:d[k] for k in FIELDS[:6]},**d[mode],
                        'risk_benefit_vs_local':local-selected,'matched_benefit_vs_wrong_fm':wrong-selected}
    return values,key


def main():
    from . import strong_fusion as F, breadth_fusion as BF
    assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    panel=A.Panel(bc_interim.load_manifest());audits={};decisions=[]
    for module in (F,BF):
        plan=A.read(module.PLAN);module.verify(plan);audit=[];audits[module.BASE.name]=audit
        for unit in plan['rows']:
            source=unit['models']['local']['outer'];row=source['row'];old=A.source(row['experiment_id'],source['record_sha256'])
            record=A.production(module.BASE.name,unit,B.sha(module.PLAN),audit)
            for arm in ('cb_pre','cb_random','reve_pre'):
                for mode in ('native','unified'):
                    vals,key=selected_values(record,arm,mode) if record else ({},None)
                    if key:decisions.append({'unit':unit['id'],'arm':arm,'readout':mode,'selected':key})
                    for field in FIELDS:
                        panel.add('fusion_function/'+arm+'/'+mode,field,'diagnostic',row,old['eval']['per_participant'],
                                  {p:v[field] for p,v in vals.items()} if record else None)
    families,_=S.summaries(panel,{},4000)
    status={k:{'planned':len(v),'complete':sum(x['status']=='complete' for x in v)} for k,v in audits.items()}
    result={'time':datetime.now().astimezone().isoformat(),'job':os.environ['SLURM_JOB_ID'],'units':status,
            'status':'complete' if all(x['complete']==x['planned'] for x in status.values()) else 'interim',
            'families':families,'decisions':decisions,'provenance':audits,'source_sha256':B.sha(__file__),
            'shared_summary_sha256':B.sha(S.__file__),'pairing_sha256':B.sha(A.__file__),'analysis_addendum_sha256':B.sha(A.ADDENDUM)}
    root=Path(core.REPO)/'results/auditory_alignment_v3/aln34/strong_fusion_function';target=root/'function.json'
    if target.exists():
        backup=root/'history'/(B.sha(target)+'.json');backup.parent.mkdir(parents=True,exist_ok=True)
        if not backup.exists():shutil.copy2(target,backup)
    B.write(target,result)
    lines=['# New strong-model fusion: residual function','',f"{result['time']}, CPU job {result['job']}, **{result['status']}**.",'',
           'The residual step is chosen only by the registered inner development rule. Mismatching FM leaves local inputs fixed. This is a test intervention, not proof of a causal mechanism. Full fixed-step trajectories remain in unit records; all direct baseline risks are in the efficacy report.','',
           '| Lane | Complete / registered |','|---|---:|']
    lines += [f"| {k} | {v['complete']} / {v['planned']} |" for k,v in status.items()]
    for family in families:
        st=family['groups']['all']
        if family['common_n']<3 or 'est' not in st:continue
        lines += ['',f"## {family['dataset']} / {family['scope']} / {family['seed_scope']}",'',
                  f"Complete identities {family['common_n']}/{family['expected_n']}.",'',
                  '| Diagnostic | Mean | Simultaneous95% interval |','|---|---:|---:|']
        for j,label in enumerate(family['labels']):lines.append(f"| {label} | {st['est'][j]:.5f} | [{st['band_low'][j]:.5f},{st['band_high'][j]:.5f}] |")
    (Path(core.REPO)/'docs/auditory_alignment_v3/STRONG_FUSION_FUNCTION_RESULTS.md').write_text('\n'.join(lines)+'\n')
    print(status,flush=True)


if __name__=='__main__':main()
