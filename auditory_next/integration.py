"""One bounded real-input end-to-end integration fit; no scientific selection."""
import json
import numpy as np
import pandas as pd
from .provenance import ROOT,digest,write_json,finish
from .features import LegacyFeatureRegistry,audit_inner_scope
from .context_inputs import history_matrix,fit_context_inputs
from .readouts import population_weights
from .fitting import fit_cases,predict_logits
from .context_execution import candidate_losses


def run(config,registry,site,dest,public,report,task_plan):
    support=ROOT/'private/auditory_next_v2'/task_plan['support_run']
    gate=ROOT/'private/auditory_next_v2'/task_plan['preflight_run']
    planpath=ROOT/registry['legacy_plan']
    folds=json.loads((ROOT/registry['legacy_splits']).read_text())['folds'];fold=folds[0]
    features=LegacyFeatureRegistry.from_files(planpath,gate/'feature_scope_registry.json')
    task=features.resolve_task(stage='D_inner',mode='R_SIM',branch='all',outer_fold=0,inner_fold=0)
    hashes={r['path']:r['sha256'] for r in json.loads((gate/'legacy_input_hashes.json').read_text())}
    for filename in ('features.npz','feature_rows.parquet'):
        path=planpath.parent/'outputs'/task['name']/filename
        if digest(path)!=hashes[str(path)]:raise ValueError('INTEGRATION_FEATURE_CHANGED')
    data=features.load_features(task,planpath.parent/'outputs')
    rows=pd.read_parquet(support/'full_event_history.parquet')
    groups=set(json.loads((support/'N1_groups.json').read_text()))
    rows=rows[rows.accepted&rows.history_chain_complete&rows.stimulus_local_id.isin([0,1])&rows.split_group_id.isin(groups)]
    rows=rows.sort_values('trial_id').reset_index(drop=True)
    lookup=pd.Series(np.arange(len(data['rows'])),index=[r['trial_id'] for r in data['rows']])
    ix=lookup.loc[rows.trial_id].to_numpy(int)
    val={g for g,i in fold['D_inner_fold_by_group'].items() if i==0}&groups
    train=(set(fold['train_groups'])&groups)-val
    audit_inner_scope(features.scope_for(task),val,data['actual_fit_groups'],fold['train_groups'])
    fm=rows.split_group_id.isin(train).to_numpy();vm=rows.split_group_id.isin(val).to_numpy()
    h,_=history_matrix(rows);p=data['zpost'][ix];b=data['zpre'][ix]
    y=rows.stimulus_local_id.to_numpy(int);g=rows.split_group_id.to_numpy(str)
    w=population_weights(y[fm],g[fm],'P_nat')
    t=fit_context_inputs(h[fm],p[fm],b[fm],w,mode='R_SIM')
    x=np.c_[t['H'].transform(h),t['P'].transform(p)]
    scope=dict(fit_groups=sorted(train),validation_groups=sorted(val),test_groups=fold['test_groups'])
    case=dict(id='integration_first_declared_inner',family='logistic',x=x[fm],y=y[fm],weights=w,
              scope=scope,feature_scope_id=data['feature_scope_id'],C=1.)
    write_json(dest/'definition.json',dict(scope=scope,mode='R_SIM',view='HP',C=1.,seed=11,selection='metadata-first outer0 inner0'))
    model,receipt=fit_cases([case],dest/'fit',expected_fits=1)
    if receipt[0]['numerical_status']!='OPTIMIZATION_STABLE':raise ValueError('INTEGRATION_OPTIMIZATION_FAILED')
    pred=rows.loc[vm,['trial_id','split_group_id','stimulus_local_id']].copy()
    pred['logit']=predict_logits(model[case['id']],x[vm])
    pred.to_parquet(dest/'validation_predictions.parquet',index=False)
    candidate_losses(pred,'P_nat').to_parquet(dest/'candidate_losses.parquet',index=False)
    (report/'INTEGRATION.md').write_text('# One end-to-end integration fit\n\n'
        'The fixed first declared inner scope was chosen by metadata order. Loading, train-only transforms, a C=1 logistic readout, '
        'encoder-unseen validation predictions, candidate aggregation and output hashes completed. '
        'This partial-fold engineering check does not select a scientific model or estimate a main effect.\n')
    return finish(dest,public,dict(status='PASS',head_fits=1,neural_head_fits=0,formal_encoder_fits=0,
        fit_groups=len(train),validation_groups=len(val),scope='one fixed real-data engineering integration',
        prediction_hash=digest(dest/'validation_predictions.parquet'),aggregation_hash=digest(dest/'candidate_losses.parquet')))
