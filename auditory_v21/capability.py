"""Same finite-budget pipeline on development/evaluation worlds, no EEG."""
import json
import time
import numpy as np
import pandas as pd
from scipy.special import xlogy
from .estimator import fit_pipeline,risk,weights
from .worlds import generate
from .runtime import write_json,require_slurm,digest
from .fit_ledger import FitLedger


def per_group_loss(z,y,groups):
    return np.array([risk(z[groups==g],y[groups==g],np.ones(np.sum(groups==g))) for g in sorted(set(groups))])


def interval(values,seed=21199,n_boot=400):
    values=np.asarray(values,float);rng=np.random.default_rng(seed)
    means=values[rng.integers(0,len(values),size=(n_boot,len(values)))].mean(axis=1)
    return dict(estimate=float(values.mean()),ci_lower=float(np.quantile(means,.025)),ci_upper=float(np.quantile(means,.975)))


def oracle_increment(joint,base,groups):
    # Expected log-loss improvement given the fully observed generator state.
    eps=np.finfo(float).eps
    joint=np.clip(joint,eps,1-eps);base=np.clip(base,eps,1-eps)
    kl=xlogy(joint,joint/base)+xlogy(1-joint,(1-joint)/(1-base))
    return float(np.dot(weights(groups),kl)/np.log(2))


def score_world(data,fitted,n_boot,bootstrap_seed=21199):
    e=data['roles']['E'];y=data['y'][e];g=data['groups'][e]
    scores={name:per_group_loss(z,y,g) for name,z in fitted['baseline'].items()}
    scores.update({name:per_group_loss(value['logit'],y,g) for name,value in fitted['enhanced'].items()})
    packet=data['packet'];pairs=[('H','HP'),('H','Hnoise'),('H','Hdup'),('Hnoise','HP'),('Hdup','HP')] if packet=='N3' else [
        ('HP','HPB'),('HB','HPB'),('HPBnoise','HPB'),('HPP','HPB')]
    rows=[]
    for first,second in pairs:
        row=dict(packet=packet,world=data['world'],seed=data['seed'],dimension=data['dimension'],rate=data['rate'],
                 first=first,second=second,**interval(scores[first]-scores[second],seed=bootstrap_seed,n_boot=n_boot),
                 test_groups=len(scores[first]),test_trials=len(y),units='bits_per_trial',ci_scope='fixed_predictions_identity_bootstrap')
        if first in fitted['baseline'] and second in ('HP','HPB'):
            row['oracle_expected_gain_bits']=oracle_increment(data['oracle']['joint'][e],data['oracle'][first][e],g)
        rows.append(row)
    return rows,{name:float(v.mean()) for name,v in scores.items()}


def run(root,private,public,report,config):
    require_slurm()
    if config['phase']!='SYNTHETIC_DEVELOPMENT_ONLY':raise ValueError('INDEPENDENT_EVALUATION_NOT_LOCKED')
    plan=config['development'];algorithm=config['algorithm']
    catalog=[]
    for seed_index,seed in enumerate(plan['seeds']):
        for dimension in plan['dimensions']:
            for packet in ('N1','N3'):
                for world in plan[packet+'_worlds']:
                    catalog.append(dict(seed=seed,dimension=dimension,packet=packet,world=world,
                                        rate=plan['positive_rates'][seed_index],head_fits=9 if packet=='N1' else 4))
    if len(catalog)!=plan['world_count'] or sum(c['head_fits'] for c in catalog)!=plan['total_head_fits']:
        raise ValueError('EXACT_DEVELOPMENT_FIT_CATALOG_MISMATCH')
    write_json(private/'fit_catalog.json',catalog)
    counts={'worlds_complete':0,'worlds_failed':0}
    ledger=FitLedger(private/'fit_events.jsonl',dict(head=plan['total_head_fits'],
        calibration=plan['base_temperature_fits'],transform=plan['transform_fits']))
    effects=[];execution=[]
    for number,case in enumerate(catalog):
        world_dir=private/f'world_{number:03d}';world_dir.mkdir(mode=0o700)
        write_json(world_dir/'start.json',case)
        ledger.begin_world(number,dict(head=case['head_fits'],calibration=3 if case['packet']=='N1' else 1,transform=7))
        started=time.time()
        try:
            data=generate(case['packet'],case['world'],case['seed'],case['dimension'],case['rate'],plan['samples_per_group_cycle'])
            fitted=fit_pipeline(data['h'],data['p'],data['b'],data['noise'],data['y'],data['groups'],data['roles'],
                                packet=case['packet'],lam=algorithm['lambda_l2'],maxiter=algorithm['maxiter'],fit_observer=ledger)
            ledger.complete_world()
            rows,losses=score_world(data,fitted,plan['bootstrap_replicates']);effects.extend(rows)
            np.savez_compressed(world_dir/'test_predictions.npz',y=data['y'][data['roles']['E']],
                groups=data['groups'][data['roles']['E']],**fitted['baseline'],
                **{k:v['logit'] for k,v in fitted['enhanced'].items()})
            write_json(world_dir/'fit_receipts.json',fitted['head_receipts'])
            write_json(world_dir/'prediction_receipt.json',dict(sha256=digest(world_dir/'test_predictions.npz'),
                N1_both_directions_share_joint_key='HPB' if case['packet']=='N1' else None))
            choices={name:dict(selected=v['selected'],candidate_names=v['candidate_names'],selection_losses=v['selection_losses']) for name,v in fitted['enhanced'].items()}
            record=dict(**case,status='FINITE_BUDGET_ESTIMATOR',head_completed=fitted['head_fits'],role_counts=fitted['role_counts'],
                        selected=choices,losses=losses,seconds=time.time()-started)
            counts['worlds_complete']+=1
        except Exception as exc:
            import traceback
            (world_dir/'traceback.txt').write_text(traceback.format_exc())
            record=dict(**case,status='FAILED',exception_type=type(exc).__name__,seconds=time.time()-started)
            counts['worlds_failed']+=1
        record['fit_counts']={kind:dict(values) for kind,values in ledger.world_counts.items()}
        write_json(world_dir/'completion.json',record);execution.append(record)
        write_json(private/'progress.json',dict(**counts,fit_counts=ledger.summary(),worlds_total=len(catalog),last_completed_index=number))
        print(json.dumps(dict(world=number,packet=case['packet'],mechanism=case['world'],status=record['status'],seconds=record['seconds'])),flush=True)
    pd.DataFrame(effects).to_csv(public/'development_effects.csv',index=False)
    write_json(public/'development_execution.json',execution)
    (report/'DEVELOPMENT_REPORT.md').write_text('# 合成开发记录\n\n仅用于检查预先描述的首个新估计器；这些世界不是独立能力评估，不产生真实任务许可。采用相同fit/transform/calibration/selection程序与冻结身份角色。真实输入规模的已知可观测低秩信号为能力夹具，不是微弱真实信号检出功效证明。\n')
    return dict(status='DEVELOPMENT_COMPLETE' if not counts['worlds_failed'] else 'DEVELOPMENT_WITH_FAILURES',
                **counts,fit_counts=ledger.summary(),worlds_total=len(catalog),capability_status='NOT_EVALUATED_INDEPENDENTLY',real_gate_open=False,
                participant_fits=0,new_encoder_fits=0)
