"""Explicit fit budget; no real-data model selection or fitting occurs here."""
import json
import numpy as np
import pandas as pd
from .provenance import ROOT,digest,write_json,finish


def run(config,registry,site,dest,public,report,support_run,tests_run):
    support_run=support_run or registry['support_run'];tests_run=tests_run or registry['contract_run']
    for run_name in (support_run,tests_run,registry['diagnostic_run']):
        if json.loads((ROOT/'private/auditory_next_v2'/run_name/'completion.json').read_text())['status']!='PASS':raise ValueError('PLAN_INPUT_GATE')
    support=ROOT/'private/auditory_next_v2'/support_run
    folds=json.loads((ROOT/registry['legacy_splits']).read_text())['folds']
    g0=pd.read_parquet(ROOT/'private/auditory_next_v2'/registry['diagnostic_run']/'G0_temporal_support.parquet')
    n1=set(json.loads((support/'N1_groups.json').read_text()))
    n2=set(json.loads((support/'N2_groups.json').read_text())['by_k']['8'])
    n3=json.loads((support/'N3_outer_support.json').read_text())
    specs=[]
    def add(packet,mode,population,family,view,outer,inner,stage,**kwargs):
        specs.append(dict(packet=packet,mode=mode,population=population,family=family,view=view,outer_fold=outer,
                          inner_fold=inner,fit_stage=stage,neural=family.startswith('mlp'),**kwargs))
    for index in range(300):add('GATES','synthetic','P_bal','nonneural_test','contract_test_allowance',None,None,'test',reserved_index=index)
    add('GATES','R_SIM','P_nat','logistic','integration_smoke',0,0,'integration',C=1.)
    # Every new-route primary and its required pre/duplication/noise controls.
    for packet,views,windows in (
        ('N1',['H','HP','HB','HPB','HPP','HPBnoise'],['paired']),
        ('N2',['H','HMU','HMUVAR','HMUMU','HVAR','HRFF'],['post','pre']),
        ('N3',['H','HP','HB','HBP','Hnoise'],['paired'])):
        for mode in ('R_SIM','L0'):
            families=('logistic','mlp32') if mode=='R_SIM' else ('logistic',)
            populations=('P_bal',) if packet=='N2' else ('P_nat','P_bal')
            for fold in folds:
                groups=(n1 if packet=='N1' else n2) if packet!='N3' else set(n3[fold['outer_fold']]['train_groups'])|set(n3[fold['outer_fold']]['test_groups'])
                for population in populations:
                    for window in windows:
                        for family in families:
                            for view in views:
                                for inner in (0,1,2,None):
                                    val=set() if inner is None else {g for g,i in fold['D_inner_fold_by_group'].items() if i==inner}&groups
                                    if inner is not None and not val:continue
                                    add(packet,mode,population,family,view,fold['outer_fold'],inner,'final' if inner is None else 'inner',
                                        window=window,n_fit_groups=len((set(fold['train_groups'])&groups)-val),n_validation_groups=len(val),C=1. if family=='logistic' else None,lam=.001 if family=='mlp32' else None)
    for fold in folds:
        for inner in (0,1,2,None):
            for view in ('HPB_training_child_donor','HPB_donor_support_reference'):
                add('N1','R_SIM','P_nat','mlp32',view,fold['outer_fold'],inner,'final' if inner is None else 'inner',window='paired',lam=.001)
    for fold in folds:
        for family,views in (('logistic',['L','R','LR','LL','RR']),('mlp32',['L','R','LR','LL','RR']),('mlp64',['L','R'])):
            for view in views:
                for inner in (0,1,2):
                    for penalty in (.01,.1,1.,10.):add('C2_R','R_SIM','P_bal',family,view,fold['outer_fold'],inner,'inner',penalty=penalty)
                finals=(None,) if family=='logistic' else (.01,.1,1.,10.)
                for penalty in finals:add('C2_R','R_SIM','P_bal',family,view,fold['outer_fold'],None,'final_all_alpha' if family!='logistic' else 'final_selected_C',penalty=penalty)
    e0=pd.read_parquet(ROOT/registry['legacy_e0']/'support.parquet')
    e0=e0[e0.status=='PASS']
    write_json(dest/'E0_record_order.json',e0.record_id.astype(str).tolist())
    for record_index in range(len(e0)):
        for outer in range(4):
            for inner in (0,1,2,None):
                for alpha in (.01,.1,1.,10.):add('E0_R','native128','P_bal','mlp32','native',outer,inner,'final_all_alpha' if inner is None else 'inner',record_index=record_index,penalty=alpha)
    for fold in folds:
        for view in ('S0','S1','S2','FULL20','S0_DUP_S1','S0_DUP_S2'):
            for inner in (0,1,2):
                for C in (.01,.1,1.,10.):add('C2_S','L0','P_bal','logistic',view,fold['outer_fold'],inner,'inner',C=C)
            add('C2_S','L0','P_bal','logistic',view,fold['outer_fold'],None,'final_selected_C')
    # G0 C selection uses at most 10 metadata-selected training children per
    # outer fold, followed by all eligible held-out children; no score selection.
    g0maps=[]
    for fold in folds:
        train=g0[g0.supported & g0.split_group_id.isin(fold['train_groups'])].sort_values('record_id').head(10)
        test=g0[g0.supported & g0.split_group_id.isin(fold['test_groups'])].sort_values('record_id')
        g0maps.append(dict(outer_fold=fold['outer_fold'],selection_records=train.record_id.tolist(),test_records=test.record_id.tolist()))
        for mode in ('L0','R_RAND','R_SUP','R_SIM'):
            for i in range(len(train)):
                for C in (.01,.1,1.,10.):add('G0','%s'%mode,'P_bal','logistic','within_child',fold['outer_fold'],None,'training_child_C_selection',record_index=i,C=C)
            for i in range(len(test)):add('G0',mode,'P_bal','logistic','within_child',fold['outer_fold'],None,'heldout_child_calibration',record_index=i)
    write_json(dest/'G0_selection_records.json',g0maps)
    for bank in ('causal','offline'):
        for fold in folds:
            for inner in (0,1,2):
                for C in (.01,.1,1.,10.):add('G0','L0','P_bal','logistic',bank,fold['outer_fold'],inner,'bridge_inner',C=C)
            add('G0','L0','P_bal','logistic',bank,fold['outer_fold'],None,'bridge_final')
    for i in range(60):add('G0','synthetic','P_bal','logistic','feature_injection',None,None,'synthetic',world_index=i)
    for mechanism in ('null','predictable_nuisance','individual_stimulus'):
        for i in range(100):add('A2','synthetic','equal_candidate','ridge','background_audit',None,None,'synthetic',mechanism=mechanism,world_index=i)
    for mode in ('L0','R_RAND','R_SUP','R_SIM'):
        for fold in folds:add('A2',mode,'equal_candidate','ridge','background_audit',fold['outer_fold'],None,'real_train_only_audit')
    for mechanism in ('PRIOR_ONLY','BACKGROUND_KEY','ADDITIVE_NOISE','INDEPENDENT_BACKGROUND'):
        for i in range(30):
            for family,view in (('logistic','H'),('mlp32','HP'),('mlp32','HPB'),('mlp32','HPBnoise')):add('N1','synthetic','P_nat',family,view,None,None,'synthetic',mechanism=mechanism,world_index=i)
    for mechanism in ('MEAN_SUFFICIENT','COVARIANCE_SIGNAL','TIME_DRIFT'):
        for i in range(30):
            for view in ('H','HMU','HMUVAR','HMUMU','HVAR','HRFF'):add('N2','synthetic','P_bal','logistic',view,None,None,'synthetic',mechanism=mechanism,world_index=i)
    for mechanism in ('HISTORY_ONLY','EEG_INCREMENT','NEAR_DETERMINISTIC_HISTORY'):
        for i in range(30):
            for family in ('logistic','mlp32'):
                for view in ('H','HP','Hnoise'):add('N3','synthetic','P_nat',family,view,None,None,'synthetic',mechanism=mechanism,world_index=i)
    table=pd.DataFrame(specs);table.insert(0,'fit_index',np.arange(len(table)))
    if len(table)>8000 or int(table.neural.sum())>3000:raise ValueError('PLAN_EXCEEDS_FROZEN_BUDGET')
    table.to_csv(dest/'TASK_PLAN.csv',index=False);table.to_csv(public/'TASK_PLAN.csv',index=False)
    by=table.groupby(['packet','mode','family']).agg(fits=('fit_index','size'),neural_fits=('neural','sum')).reset_index()
    by.to_csv(public/'fit_budget_summary.csv',index=False)
    resources=dict(max_gpu_hours=32,max_cpu_core_hours=256,max_gpu_concurrent=2,max_cpu_jobs_concurrent=4,
                   reservations={'N1_gpu_hours':6,'N2_gpu_hours':6,'N3_gpu_hours':6,'C2_R_gpu_hours':6,'E0_R_gpu_hours':6,'synthetic_gpu_hours':2},
                   cpu_accounting='sum allocated_cpus * actual elapsed or allocation-time upper bound; includes GPU host CPUs')
    plan=dict(version='auditory_next_task_plan_v2',support_run=support_run,contract_run=tests_run,preflight_run=registry['preflight_run'],
              diagnostic_run=registry['diagnostic_run'],task_csv=str(dest/'TASK_PLAN.csv'),task_csv_hash=digest(dest/'TASK_PLAN.csv'),
              all_readout_fits=len(table),neural_head_fits=int(table.neural.sum()),formal_encoder_fits=0,
              synthetic_worlds=600,resources=resources,inner_policy='reuse only declared D-inner-unseen validation groups; report partial calibration coverage; no unrecorded groups assigned',
              repair_policy='all 4 final alphas fitted before a global 1000/2000 decision; select from terminal-budget inner OOF',
              budget_limited=['N1_L0_MLP','N2_L0_MLP','N3_L0_MLP','C2_R_L0_SUP_full_MLP','C2_S_MLP_secondary','N2_additional_k_head_refits','seed23_replication'],
              implementation_gate='Each packet needs code-matched tests and integration gate before execution; catalog entry is not execution')
    write_json(dest/'plan.json',plan)
    (report/'TASK_PLAN.md').write_text('# v2 fixed fit budget\n\n'+f'The catalog reserves {len(table)} readout fits, including {int(table.neural.sum())} neural heads and zero formal encoders. '
        'All three new routes retain the R_SIM main matrix and controls. L0 parallel logistic fits are reserved; secondary L0 MLP, C2 parallel MLP, extra k head refits and seed replication are budget limited. '
        'These are pre-result resource decisions, not negative outcomes.\n\n'
        'C2/E0 repair fits all four final alpha candidates before choosing the single family-wide stopping budget, so a final-model extension cannot change the selected-estimator rule. '
        'All intermediate final-alpha fits count. G0 C selection uses the first ten eligible training records in immutable opaque-ID order per fold; all supported test records remain evaluated. '
        'This is a bounded calibration-selection sample, not the maximum attainable within-child performance.\n\n'
        'The 600 independent synthetic worlds comprise A2 300, N1 120, N2 90, N3 90; A2 null W conditions share the same world draw. '
        'Partial D-inner calibration coverage is explicit and must not be described as complete-cohort nested validation. No clinical endpoint is used.\n')
    return finish(dest,public,dict(status='PASS',all_readout_fits=len(table),neural_head_fits=int(table.neural.sum()),formal_encoder_fits=0,
                  synthetic_worlds=600,head_fits_executed=0,scope='reserved fit catalog; per-packet implementation gates remain required'))
