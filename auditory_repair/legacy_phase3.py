"""Paired repair of original Phase 3 clinical covariates on its exact old folds."""
import importlib.util
import json
from pathlib import Path
import numpy as np
import pandas as pd
from auditory_fseries.models import fit_predict,set_recorder
from .extended import ROOT,dump,sha,repeated_interval


def nested(C,E,y,folds,clinical_alphas,eeg_alphas,bounds,shared=False):
    pred=np.full((5,len(y)),np.nan);selected=[]
    choices=[(float(a),None) for a in clinical_alphas] if E is None else (
        [(float(a),float(a)) for a in clinical_alphas] if shared else
        [(float(a),float(e)) for a in clinical_alphas for e in eeg_alphas if e is not None]+
        [(float(a),None) for a in clinical_alphas])
    for rep,fold,tr,te,inner in folds:
        def fit(a,b,choice):
            ac,az=choice
            return fit_predict(C,np.zeros((len(y),0)),E if E is not None else np.zeros((len(y),0)),y,a,b,
                ('linear',ac,az,False,False),20260918,bounds)[0]
        scores=[float(np.mean([np.abs(y[b]-fit(a,b,choice)).mean() for a,b in inner])) for choice in choices]
        chosen=min(range(len(choices)),key=lambda i:(scores[i],choices[i][0],float('inf') if choices[i][1] is None else choices[i][1]))
        pred[rep,te]=fit(tr,te,choices[chosen]);selected.append(dict(repeat=rep,fold=fold,alpha=choices[chosen]))
    assert np.isfinite(pred).all()
    return pred,selected


def run(private,public,config,counter):
    set_recorder(counter)
    source=ROOT/'private/phase3_ha_science_001/phase3_ha_science.py'
    spec=importlib.util.spec_from_file_location('historical_phase3',source);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    # The copied historical script used __file__.parents[1]; bind its input
    # locator back to the actual workspace without changing the snapshot.
    old.BASE=ROOT
    cfg=json.loads((ROOT/'private/phase3_ha_science_001/phase3_science_v1.json').read_text());h=cfg['ha']
    original=pd.read_csv(ROOT/'private/phase3_ha_covariates_004/candidate_covariates.csv')
    elig=pd.read_csv(ROOT/'results/phase2_archival_001/candidate_eligibility.csv');elig=elig[elig.eligible.astype(str).str.lower()=='true']
    cohort=original.merge(elig[['participant_id','recording_id']],on=['participant_id','recording_id'],validate='one_to_one')
    cohort=cohort[cohort.pta_status=='linked_complete_unaided'].copy()
    features=pd.read_csv(ROOT/'results/phase2_measurements_001/features.csv')
    fixed=features[(features.variant=='hp01_avg20')&(features.condition=='code1')&(features.measurement_status=='measured')][['participant_id','recording_id','mean_uv']]
    cohort=cohort.merge(fixed,on=['participant_id','recording_id'],validate='one_to_one').reset_index(drop=True)
    assert len(cohort)==cohort.participant_id.nunique()==50
    # Use the new direct-workbook parser, not any old sequential clinical-row key.
    from auditory_fseries.data import _read_workbook,_workbook_path,_source_row_from_clinical_id
    workbook_path=_workbook_path(ROOT,{},ROOT/'private/inventory_001/file_path_map.csv');worksheet,_=_read_workbook(workbook_path)
    corrected=[]
    for r in cohort.to_dict('records'):
        row=worksheet[_source_row_from_clinical_id(r['clinical_row_id'])]
        assert float(r['MUSS'])==row['MUSS'] and float(r['clinical_age_months'])==row['age_months'] and float(r['duration_months'])==row['duration_months']
        corrected.append(row['better_unaided_pta'] if row['better_unaided_pta'] is not None else np.nan)
    cohort['corrected_PTA']=corrected;cohort.to_csv(private/'cohort.csv',index=False)
    pairs=[old.bin_features(r,'phase1_epochs_001') for r in cohort.recording_id];assert all(p is not None for p in pairs)
    post=np.array([p[0] for p in pairs]);pre=np.array([p[1] for p in pairs])
    folds=old.splits(len(cohort),h,cfg['seed']);dump(private/'folds.json',[dict(repeat=r,fold=f,train=a,test=b,inner=[dict(train=x,validation=y) for x,y in ins]) for r,f,a,b,ins in folds])
    targets=dict(MUSS=cohort.MUSS.to_numpy(float),age=cohort.clinical_age_months.to_numpy(float),log_duration=np.log1p(cohort.duration_months.to_numpy(float)))
    recorded=pd.read_csv(ROOT/'private/phase3_ha_science_001/predictions.csv')
    metrics=[];effects=[];checks=[];rows=[]
    for target,y in targets.items():
        clinical=[cohort.clinical_age_months.to_numpy(float),np.log1p(cohort.duration_months.to_numpy(float))]
        if target=='age':clinical=clinical[1:]
        elif target=='log_duration':clinical=clinical[:1]
        C_old=np.column_stack(clinical+[cohort.better_unaided_pta.to_numpy(float)])
        C_new=np.column_stack(clinical+[np.array(corrected)])
        bounds=[0,100] if target=='MUSS' else [-1e100,1e100]
        banks={'clinical':None,'clinical_plus_fixed_amplitude':cohort.mean_uv.to_numpy(float)[:,None],
            'clinical_plus_poststim_pattern':post,'clinical_plus_prestim_pattern':pre}
        predictions={}
        for model,E in banks.items():
            p,selected=nested(C_old,E,y,folds,h['ridge_alphas'],[],bounds,shared=True)
            ref=recorded[(recorded.target==target)&(recorded.model==model)].pivot(index='participant_id',columns='repeat',values='pred').loc[cohort.participant_id].to_numpy().T
            difference=float(np.max(np.abs(p-ref)));assert difference<1e-7,'OLD_PREDICTION_REPRODUCTION_FAILED'
            checks.append(dict(target=target,model=model,max_absolute_difference=difference))
            predictions['original_'+model]=p
            p,selected=nested(C_new,E,y,folds,h['ridge_alphas'],[],bounds,shared=True)
            predictions['corrected_'+model]=p;dump(private/f'{target}_{model}_tuning.json',selected)
        if target=='MUSS':
            for model,E in [('post_separate',post),('pre_separate',pre)]:
                p,tuning=nested(C_new,E,y,folds,h['ridge_alphas'],[1,10,100,1000,10000,1000000,None],bounds)
                predictions['corrected_'+model]=p;dump(private/f'{model}_tuning.json',tuning)
            p,_=nested(C_new[:,:-1],None,y,folds,h['ridge_alphas'],[],bounds)
            predictions['age_duration_only']=p
        for model,p in predictions.items():
            metrics.append(dict(target=target,model=model,n=50,MAE=float(np.abs(p-y).mean()),RMSE=float(np.sqrt(np.mean((p-y)**2)))))
            for repeat in range(5):
                for i in range(50):rows.append(dict(target=target,model=model,repeat=repeat,group=cohort.participant_id.iloc[i],y=float(y[i]),prediction=float(p[repeat,i])))
            if model!='corrected_clinical':
                d=np.abs(predictions['corrected_clinical']-y)-np.abs(p-y)
                effects.append(dict(target=target,model=model,baseline='corrected_clinical',**repeated_interval(d,2000,9127)))
        np.savez(private/f'{target}_complete_oof.npz',y=y,**predictions)
        print(json.dumps(dict(legacy_phase3_target=target,fit_attempts=counter.n)),flush=True)
    pd.DataFrame(rows).to_csv(private/'predictions.csv',index=False)
    pd.DataFrame(metrics).to_csv(public/'metrics.csv',index=False);dump(public/'effects.json',effects);dump(public/'old_reproduction.json',checks)
    dump(private/'input_hashes.json',{str(p):sha(p) for p in [source,workbook_path,ROOT/'private/phase3_ha_science_001/predictions.csv',ROOT/'private/phase3_ha_covariates_004/candidate_covariates.csv']})
    return dict(status='COMPLETE',identity_groups=50,corrected_PTA_missing=int(np.isnan(corrected).sum()),fit_attempts=counter.n,
        reproduced_old_task_model_combinations=len(checks),same_original_cohort_and_folds=True,scientific_early_stopping=False)
