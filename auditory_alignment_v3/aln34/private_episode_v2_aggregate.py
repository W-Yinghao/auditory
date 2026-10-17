"""Complete-child, seed-aware private episode comparisons; no new model fitting."""
from datetime import datetime
import os
from pathlib import Path
import shutil
from . import private_episode_v2 as T, new_lane_aggregate as A, learning_budget as B
from .. import core

METRICS = {'native/auc':-1.,'native/nll_bits':1.,'native/brier':1.,
           'linear/auc':-1.,'linear/nll_bits':1.,'linear/brier':1.,
           'history/history_gain_bits':-1.,'history/history_gain_common_support_bits':-1.}


def observations(per, metric, sign):
    mode, key = metric.split('/')
    return {p:None if v[mode].get(key) is None else sign*v[mode][key]
            for p,v in per.items() if v['status']=='complete'}


def parse(panel,plan,audit):
    sha=B.sha(T.PLAN)
    for unit in plan['rows']:
        row=unit['source'];old=A.source(row['experiment_id'],unit['record_sha256'])
        r=A.production(T.BASE.name,unit,sha,audit)
        for frac in ('0.1','0.3'):
            variants={f'{name}/{step}':None for name in ('source','ordinary','episode') for step in (0,5,20)}
            variants.update(ordinary_selected=None,episode_selected=None)
            if r:
                for name in ('source','ordinary','episode'):
                    for step in (0,5,20):
                        variants[f'{name}/{step}']=r['stages']['outer']['values'][name]['candidates'][frac][str(step)]['per_participant']
                for name in ('ordinary','episode'):variants[name+'_selected']=r['choices'][name][frac]['outer']['per_participant']
            scope='private_episode/'+row['spec']['architecture']+'/'+row['spec']['objective']+'/support_'+frac
            pairs=[('source/0',v) for v in variants if v!='source/0']
            pairs += [(f'ordinary/{s}',f'episode/{s}') for s in (0,5,20)]+[('ordinary_selected','episode_selected')]
            for metric,sign in METRICS.items():
                for name,per in variants.items():panel.add(scope,name,metric,row,old['eval']['per_participant'],None if per is None else observations(per,metric,sign))
                for ref,cand in pairs:panel.compare(row['dataset'],scope,metric,ref,cand)


def main():
    assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    plan=A.read(T.PLAN);T.verify(plan);panel=A.Panel();audit=[];parse(panel,plan,audit)
    families=panel.summarise()
    for f in families:
        metric=f['readout'];f['direction']='positive = candidate improvement; NLL/Brier reference-minus-candidate; AUC/history candidate-minus-reference'
        f['units']='bits/trial' if 'bits' in metric else 'AUC' if metric.endswith('auc') else 'Brier'
    done=sum(x['status']=='complete' for x in audit)
    value={'time':datetime.now().astimezone().isoformat(),'job':os.environ['SLURM_JOB_ID'],'status':'complete' if done==len(audit) else 'interim',
           'complete':done,'planned':len(audit),'failed_markers':sum(x.get('failure_marker',False) for x in audit),
           'plan_sha256':B.sha(T.PLAN),'design_sha256':B.sha(T.NOTE),'source_sha256':B.sha(__file__),
           'shared_aggregation_sha256':B.sha(A.__file__),'analysis_addendum_sha256':B.sha(A.ADDENDUM),'families':families,'provenance':audit}
    value['compatible_v1_reuse']=T.read(T.BASE/'compatibility_reuse.json')
    root=Path(core.REPO)/'results/auditory_alignment_v3/aln34/private_episode_v2';target=root/'efficacy.json'
    if target.exists():
        backup=root/'history'/(B.sha(target)+'.json');backup.parent.mkdir(parents=True,exist_ok=True)
        if not backup.exists():shutil.copy2(target,backup)
    B.write(target,value)
    lines=['# Private child episode continuation v2','',f"{value['time']} · CPU job {value['job']} · **{value['status']}** · {done}/{len(audit)} complete.",'',
           'CS singleton support uses explicitly recorded identity adaptation; all query children remain. Compatible completed v1 NCE results retain their actual execution provenance in per-unit reused_from. All metrics, fixed candidates, coverage and direct HA-minus-NH interaction families are retained in the JSON. Seeds remain within child. The new policy selection is nested; historical recipe choice and full-record unsupervised preprocessing are inherited. No prospective causal-decoding claim.','']
    for f in families:
        st=f['groups']['all']
        if f['readout']!='native/nll_bits' or f['common_identity_n']<3 or 'est' not in st:continue
        lines += [f"## {f['scope']} · {f['seed_scope']}",'',f"Complete paired children {f['common_identity_n']}/{f['expected_identity_n']}.",'',
                  '| Comparison | ΔNLL bits/trial | Simultaneous95% interval |','|---|---:|---:|']
        for j,label in enumerate(f['labels']):lines.append(f"| {label} | {st['est'][j]:+.5f} | [{st['band_low'][j]:+.5f},{st['band_high'][j]:+.5f}] |")
        lines.append('')
    (Path(core.REPO)/'docs/auditory_alignment_v3/PRIVATE_EPISODE_V2_RESULTS.md').write_text('\n'.join(lines)+'\n')
    print({'complete':done,'planned':len(audit)},flush=True)


if __name__=='__main__':main()
