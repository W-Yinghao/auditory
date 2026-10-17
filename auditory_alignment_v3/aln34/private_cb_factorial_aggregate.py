"""Paired private initialization/rate factorial, with all four cells retained."""
from collections import defaultdict
from datetime import datetime
import os
from pathlib import Path
import shutil
from .. import core
from . import private_cb_factorial as F,learning_budget as B,new_lane_aggregate as A

METRICS=('affine_nll','score_auc','native_nll','history_gain','twin_sensitivity')
INIT=('random_full','pretrained_full');RATES=('pre_recipe','random_recipe')


def values(rec,metric):
    if rec is None:return None
    pp=rec['eval']['per_participant'];cal=rec['eval']['native_calibration']['per_participant']
    native='temperature' if rec['row']['spec']['objective']=='NCE' else 'class_kernel'
    if metric=='affine_nll':return {p:v['positive_affine']['nll_bits'] for p,v in cal.items()}
    if metric=='score_auc':return {p:-v['positive_affine']['auc_score'] for p,v in cal.items()}
    if metric=='native_nll':return {p:v[native]['nll_bits'] for p,v in cal.items()}
    if metric=='history_gain':return {p:-v['hist_gain_bits'] for p,v in pp.items()}
    if metric=='twin_sensitivity':return {p:-(v['hist_gain_bits']-v['hist_gain_twin_bits']) for p,v in pp.items()}
    raise ValueError(metric)


def encoded_interaction(cells,person):
    # Return a loss-coded contrast so Panel's reference(0)-candidate convention
    # yields init benefit at the random recipe minus init benefit at the pre recipe.
    def benefit(rate):return cells['random_full/'+rate][person]-cells['pretrained_full/'+rate][person]
    return -(benefit('random_recipe')-benefit('pre_recipe'))


def main():
    assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    plan=A.read(F.PLAN);F.verify(plan);sha=B.sha(F.PLAN);panel=A.Panel();audit=[];cells=defaultdict(dict)
    for old in plan['baselines'].values():
        row=old['row'];rec=A.source(row['experiment_id'],old['record_sha256'])
        cell=(row['spec']['objective'],row['seed'],row['subject_fold'])
        cells[cell][row['spec']['adaptation']+'/'+old['rate_cell']]=(row,rec,rec['eval']['per_participant'])
    for row in plan['rows']:
        rec=A.production(F.BASE.name,row,sha,audit)
        old=plan['baselines'][row['spec']['baseline_id']];source=A.source(old['row']['experiment_id'],old['record_sha256'])
        cell=(row['spec']['objective'],row['seed'],row['subject_fold'])
        cells[cell][row['spec']['adaptation']+'/'+row['spec']['rate_cell']]=(row,rec,source['eval']['per_participant'])
    costs=[]
    for cell,items in sorted(cells.items()):
        assert set(items)=={a+'/'+r for a in INIT for r in RATES}
        obj,_,_=cell;scope='private_factorial/'+obj
        counts=[{p:v['n'] for p,v in pop.items()} for _,rec,pop in items.values() if rec is not None]
        assert all(c==counts[0] for c in counts),'different children/trial counts in factorial cells'
        costs.append({'cell':list(cell),'models':{k:{'id':row['experiment_id'],'complete':rec is not None,
                    'steps':rec.get('optimizer_steps') if rec else None,'seconds':rec.get('total_seconds') if rec else None,
                    'device':rec.get('device') if rec else None} for k,(row,rec,_) in items.items()}})
        for metric in METRICS:
            vals={name:values(rec,metric) for name,(_,rec,_) in items.items()}
            for name,(row,_,pop) in items.items():panel.add(scope,name,metric,row,pop,vals[name])
            for rate in RATES:panel.compare('private_bdf',scope,metric,'random_full/'+rate,'pretrained_full/'+rate)
            for init in INIT:panel.compare('private_bdf',scope,metric,init+'/pre_recipe',init+'/random_recipe')
            row,_,pop=next(iter(items.values()));full=all(v is not None for v in vals.values())
            encoded={p:encoded_interaction(vals,p) for p in pop} if full else None
            panel.add(scope,'interaction_reference_zero',metric,row,pop,{p:0. for p in pop})
            panel.add(scope,'initialization_x_rate_interaction',metric,row,pop,encoded)
            panel.compare('private_bdf',scope,metric,'interaction_reference_zero','initialization_x_rate_interaction')
    families=panel.summarise();complete=sum(x['status']=='complete' for x in audit)
    for f in families:
        f['direction']='positive = candidate minus reference' if f['readout'] in ('score_auc','history_gain','twin_sensitivity') else 'positive = reference minus candidate NLL, bits/trial'
        f['interaction_direction']='initialization benefit at historical random recipe minus initialization benefit at historical pretrained recipe'
    result={'time':datetime.now().astimezone().isoformat(),'job':os.environ['SLURM_JOB_ID'],
            'status':'complete' if complete==60 else 'interim','new_complete':complete,'new_planned':60,'reused_complete':60,
            'families':families,'costs':costs,'provenance':audit,'source_sha256':B.sha(__file__),
            'shared_aggregation_sha256':B.sha(A.__file__),'plan_sha256':sha,'design_sha256':B.sha(F.NOTE)}
    root=Path(core.REPO)/'results/auditory_alignment_v3/aln34/private_cb_factorial';target=root/'efficacy.json'
    if target.exists():
        old=root/'history'/(B.sha(target)+'.json');old.parent.mkdir(parents=True,exist_ok=True)
        if not old.exists():shutil.copy2(target,old)
    B.write(target,result)
    lines=['# Private CBraMod initialization × learning-rate factorial','',f"{result['time']}, CPU job{result['job']}; **{result['status']}**. {complete}/60 new crossed cells,60 reused original cells.",'',
           'All four initialization/rate combinations are preserved. The two original rate pairs are fixed; there is no outer-test choice. Encoder training, checkpoint selection and original evaluation interfaces remain unchanged. Same64 previously studied children; no independent clinical replication. Original positive-affine and native probability interfaces remain separate.','']
    for f in families:
        st=f['groups']['all']
        if f['common_identity_n']<3 or 'est' not in st:continue
        lines += [f"## {f['scope']} / {f['readout']} / {f['seed_scope']}",'',
                  f"Complete paired children{f['common_identity_n']}/{f['expected_identity_n']}; {f['direction']}.",'',
                  '| Contrast | Benefit | Simultaneous95% interval |','|---|---:|---:|']
        for j,label in enumerate(f['labels']):lines.append(f"| {label} | {st['est'][j]:+.4f} | [{st['band_low'][j]:+.4f},{st['band_high'][j]:+.4f}] |")
        lines.append('')
    (Path(core.REPO)/'docs/auditory_alignment_v3/PRIVATE_CB_FACTORIAL_RESULTS.md').write_text('\n'.join(lines)+'\n')
    print({'new_complete':complete,'new_planned':60,'reused_complete':60},flush=True)


if __name__=='__main__':main()
