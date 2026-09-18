"""Finite fit catalog and resource reservations; no model fits."""
import csv
import json
from .runtime import write_json
from .data import load_support


def make_plan(root,private,public,report,config,args):
    members,splits,history,registry,receipt=load_support(root,args['split_run'])
    records=[]
    def add(packet,kind,identifier,**kwargs):records.append(dict(packet=packet,kind=kind,fit_id=identifier,**kwargs))
    for mode in config['P0']['representations']:
        for fold in range(5):
            for view in config['P0']['views']:
                for lam in config['readout']['lambda_grid']:add('P0','head',f'{mode}_post_f{fold}_{view}_l{lam}')
            if mode in config['P0']['pre_modes']:
                for view in ('FULL','PC8'):add('P0','head',f'{mode}_pre_f{fold}_{view}_l0.01')
    for view in config['N2R']['views']+config['N2R']['full400_sensitivity']:
        for fold in range(5):
            for inner in range(3):
                for lam in config['readout']['lambda_grid']:add('N2R','head',f'{view}_f{fold}_inner{inner}_l{lam}')
            add('N2R','head',f'{view}_f{fold}_final')
    for objective in config['R3']['objectives']:
        for fold in range(5):
            for stage in ('selection','final'):add('R3','encoder',f'{objective}_f{fold}_{stage}')
            for view in config['R3']['probe_views']:
                for lam in config['readout']['lambda_grid']:add('R3','head',f'{objective}_f{fold}_{view}_selection_l{lam}')
                add('R3','head',f'{objective}_f{fold}_{view}_final')
    for view in config['R3']['common_baselines']:
        for fold in range(5):
            for lam in config['readout']['lambda_grid']:add('R3','head',f'{view}_f{fold}_selection_l{lam}')
            add('R3','head',f'{view}_f{fold}_final')
    for world in config['capability']['N2R']['worlds']:
        for rep in range(20):
            for view in ('HQ','HQV'):
                for inner in range(3):
                    for lam in config['readout']['lambda_grid']:add('N2R_capability','head',f'{world}_{rep}_{view}_inner{inner}_l{lam}')
                add('N2R_capability','head',f'{world}_{rep}_{view}_final')
    for world in config['capability']['P0']['worlds']:
        for rep in range(5):
            for view in ('FULL','PC8'):add('P0_capability','head',f'{world}_{rep}_{view}')
    for objective in config['R3']['objectives']:
        add('R3_capability','synthetic_encoder',objective);add('R3_capability','head',objective+'_probe')
    with (private/'fit_catalog.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=['packet','kind','fit_id']);writer.writeheader();writer.writerows(records)
    counts={}
    for row in records:counts[row['packet']+'_'+row['kind']]=counts.get(row['packet']+'_'+row['kind'],0)+1
    nhead=sum(r['kind']=='head' for r in records)
    assert nhead<3000
    tasks=[dict(task_index=i,objective=objective,outer_fold=fold,seed=11) for i,(objective,fold) in enumerate((o,f) for o in ('SUP','SIM','MATCH') for f in range(5))]
    write_json(private/'representation_tasks.json',dict(tasks=tasks,stages=['selection','final'],split_run=args['split_run'],registry_run=args['registry_run']))
    summary=dict(status='PLAN_FROZEN',fit_catalog_counts=counts,planned_head_calls=nhead,remaining_test_development_recovery_calls=3000-nhead,max_heads=3000,max_formal_encoders=30,max_synthetic_encoders=3,max_cpu_core_hours=160,max_gpu_hours=16,planned_formal_gpu_upper_hours=15,planned_synthetic_gpu_upper_hours=.5,remaining_gpu_recovery_upper_hours=.5,split_run=args['split_run'],new_model_fits=0)
    write_json(public/'fit_catalog_aggregate.json',summary)
    return summary
