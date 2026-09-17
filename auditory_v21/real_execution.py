"""One finite real comparison per authorized route, guarded before feature IO."""
import json
import os
import pickle
import traceback
import numpy as np
import pandas as pd
from .runtime import require_slurm,write_json,digest
from .evaluation import CORE_SOURCES,load_cases
from .estimator import fit_pipeline,split_roles,validate_roles
from .fit_ledger import FitLedger
from .capability import per_group_loss,interval
from auditory_next.context_inputs import history_matrix,independent_noise


def capability_gate(receipt,source_hashes,algorithm,manifest_hash,packet,mode):
    if receipt.get('capability_status')!='PASS' or not receipt.get('real_gate_open'):
        return 'CAPABILITY_NOT_PASS'
    if receipt.get('packet')!=packet or receipt.get('mode')!=mode or receipt.get('algorithm')!=algorithm:
        return 'CAPABILITY_SCOPE_MISMATCH'
    if receipt.get('input_manifest_hash')!=manifest_hash:return 'INPUT_MANIFEST_CHANGED'
    if any(receipt.get('source_hashes',{}).get(key)!=source_hashes.get(key) for key in CORE_SOURCES):
        return 'CAPABILITY_SOURCE_CHANGED'
    if receipt.get('unevaluable')!=0:return 'CAPABILITY_INCOMPLETE'
    return 'PASS'


def load_case(case):
    rows_path=case['selected_rows_path']
    if digest(__import__('pathlib').Path(rows_path))!=case['selected_rows_sha256']:
        raise ValueError('PREFLIGHT_SELECTED_ROWS_CHANGED')
    rows=pd.read_json(rows_path) if str(rows_path).endswith('.json') else pd.read_parquet(rows_path)
    rows=rows.sort_values('trial_id').reset_index(drop=True)
    for item in case['feature_file_hashes'].values():
        if digest(__import__('pathlib').Path(item['path']))!=item['sha256'] or not item['hash_match']:
            raise ValueError('FROZEN_FEATURE_HASH_CHANGED')
    folder=__import__('pathlib').Path(case['feature_folder'])
    feature_rows=pd.read_parquet(folder/'feature_rows.parquet')
    if feature_rows.trial_id.duplicated().any():raise ValueError('FEATURE_ROW_DUPLICATE')
    with np.load(folder/'features.npz',allow_pickle=False) as arrays:
        if not np.array_equal(arrays['trial_ids'].astype(str),feature_rows.trial_id.astype(str)):
            raise ValueError('FEATURE_TRIAL_ALIGNMENT')
        if not np.array_equal(arrays['groups'].astype(str),feature_rows.split_group_id.astype(str)) or not np.array_equal(arrays['y'],feature_rows.stimulus_local_id):
            raise ValueError('FEATURE_GROUP_LABEL_ALIGNMENT')
        ix=pd.Series(np.arange(len(feature_rows)),index=feature_rows.trial_id.astype(str)).loc[rows.trial_id.astype(str)].to_numpy(int)
        p=arrays['post'][ix].astype(float);b=arrays['pre'][ix].astype(float)
        if not np.array_equal(arrays['y'][ix],rows.stimulus_local_id.to_numpy()):raise ValueError('SUPPORT_LABEL_ALIGNMENT')
    h,columns=history_matrix(rows)
    if columns!=case['h_columns'] or h.shape[1]!=25:raise ValueError('FROZEN_H_SCHEMA_CHANGED')
    if p.shape[1]!=case['dimensions']['P'] or b.shape[1]!=case['dimensions']['B']:raise ValueError('FROZEN_FEATURE_WIDTH')
    groups=rows.split_group_id.to_numpy(str);y=rows.stimulus_local_id.to_numpy(int)
    roles={k:np.flatnonzero(np.isin(groups,v)) for k,v in case['role_groups'].items()}
    validate_roles(groups,roles)
    return rows,h,p,b,y,groups,roles


def run(root,private,public,report,config):
    require_slurm()
    if config['phase']!='CONDITIONAL_REAL_COMPARISON':raise ValueError('REAL_LOCK_REQUIRED')
    lane=os.environ.get('AUDITORY_V21_LANE','');plan=config['real'];alg=config['algorithm']
    if lane not in plan['lanes']:raise ValueError('FROZEN_REAL_LANE_REQUIRED')
    packet,mode=lane.split('_',1);budget=plan['lanes'][lane]
    if private.name!=budget['run']:raise ValueError('REAL_RUN_NAME_MISMATCH')
    start=json.loads((private/'start.json').read_text())
    manifest=root/'private/auditory_v21'/config['input_preflight_run']/'cases.json'
    cases=sorted([c for c in load_cases(manifest) if c['packet']==packet and c['mode']==mode],key=lambda c:c['outer_fold'])
    cap_path=root/'results/auditory_v21'/budget['capability_run']/'capability_receipt.json'
    cap=json.loads(cap_path.read_text()) if cap_path.exists() else {}
    gate=capability_gate(cap,start['source_hashes'],alg,digest(manifest),packet,mode)
    preflight_completion=json.loads((manifest.parent/'completion.json').read_text())
    source_pass=preflight_completion.get('status')=='PASS' and len(cases)==5 and {c['outer_fold'] for c in cases}==set(range(5)) and all(c['status']=='PASS' for c in cases)
    receipt=dict(packet=packet,mode=mode,primary=budget['primary'],capability_status=cap.get('capability_status','NOT_EVALUATED'),
        support_status='PASS' if source_pass else 'BLOCKED',estimator_id=alg['id'],algorithm=alg,
        source_hashes={p:start['source_hashes'][p] for p in CORE_SOURCES},input_manifest_hash=digest(manifest),
        capability_receipt_hash=digest(cap_path) if cap_path.exists() else None,new_encoder_fits=0,
        planned_heads=budget['heads'],population='P_nat',old_results_unchanged=True)
    if gate!='PASS' or not source_pass:
        receipt.update(status='CONDITIONALLY_STOPPED',reason=gate if gate!='PASS' else 'SOURCE_OR_SUPPORT_BLOCKED',
            new_head_fits=0,finite_prediction_status='NOT_EVALUATED',scientific_effect_status='NOT_EVALUATED',control_status='NOT_EVALUATED')
        write_json(public/'route_decision.json',receipt)
        (report/'REAL_COMPARISON.md').write_text(f'# {lane}\n\nCONDITIONALLY_STOPPED: {receipt["reason"]}. No new real head fitted. This is not a negative EEG finding.\n')
        return receipt
    ledger=FitLedger(private/'fit_events.jsonl',dict(head=budget['heads'],calibration=budget['calibrations'],transform=budget['transforms']))
    write_json(private/'fit_catalog.json',[dict(outer_fold=c['outer_fold'],heads=9 if packet=='N1' else 4) for c in cases])
    predictions=[];folds=[];head_receipts=[]
    for case in cases:
        fold=case['outer_fold'];path=private/f'outer_{fold}';path.mkdir(mode=0o700)
        ledger.begin_world(fold,dict(head=9 if packet=='N1' else 4,calibration=3 if packet=='N1' else 1,transform=7))
        try:
            rows,h,p,b,y,groups,roles=load_case(case)
            noise=independent_noise(rows.trial_id,b.shape[1] if packet=='N1' else p.shape[1],namespace=packet+'_v21_noise',seed=plan['noise_seed'])
            control_receipt=dict(label_independent=True,source_hash=start['source_hashes']['auditory_next/context_inputs.py'],
                noise_seed=plan['noise_seed'],noise_scope='fixed per trial hash normal, no label input')
            fit=fit_pipeline(h,p,b,noise,y,groups,roles,packet=packet,lam=alg['lambda_l2'],maxiter=alg['maxiter'],
                real=True,encoder_receipt=case['encoder_receipt'],control_receipt=control_receipt,fit_observer=ledger)
            ledger.complete_world();e=roles['E']
            prediction=rows.iloc[e][['trial_id','split_group_id','stimulus_local_id']].copy()
            prediction['outer_fold']=fold
            for key,value in fit['baseline'].items():prediction[key]=value
            for key,value in fit['enhanced'].items():prediction[key]=value['logit']
            prediction.to_parquet(path/'predictions.parquet',index=False);predictions.append(prediction)
            with (path/'fitted.pkl').open('wb') as handle:pickle.dump(fit,handle,protocol=5)
            write_json(path/'fit_receipts.json',fit['head_receipts']);head_receipts.extend(fit['head_receipts'])
            folds.append(dict(outer_fold=fold,status='COMPLETE',role_counts=fit['role_counts'],
                selected={k:v['selected'] for k,v in fit['enhanced'].items()},prediction_hash=digest(path/'predictions.parquet')))
        except Exception as exc:
            (path/'traceback.txt').write_text(traceback.format_exc())
            folds.append(dict(outer_fold=fold,status='FAILED',exception_type=type(exc).__name__))
            write_json(private/'fold_execution.json',folds)
            receipt.update(status='REAL_COMPARISON_FAILED',new_head_fits=ledger.summary()['head']['attempts'],
                fit_counts=ledger.summary(),finite_prediction_status='INCOMPLETE',scientific_effect_status='NOT_EVALUABLE',
                control_status='INCOMPLETE',complete_folds=sum(f['status']=='COMPLETE' for f in folds),planned_folds=5)
            write_json(public/'route_decision.json',receipt)
            return receipt
    combined=pd.concat(predictions,ignore_index=True)
    if combined.groupby('split_group_id').outer_fold.nunique().max()!=1 or combined.trial_id.duplicated().any():
        raise ValueError('OOF_IDENTITY_OR_TRIAL_REUSE')
    combined.to_parquet(private/'predictions.parquet',index=False)
    names=['HP','HB','HPB','HPBnoise','HPP'] if packet=='N1' else ['H','HP','Hnoise','Hdup']
    groups=combined.split_group_id.to_numpy(str);y=combined.stimulus_local_id.to_numpy(int)
    losses={name:per_group_loss(combined[name].to_numpy(),y,groups) for name in names}
    pairs=[('HP','HPB'),('HB','HPB'),('HPBnoise','HPB'),('HPP','HPB')] if packet=='N1' else [('H','HP'),('H','Hnoise'),('H','Hdup'),('Hnoise','HP'),('Hdup','HP')]
    effects=[dict(packet=packet,mode=mode,first=a,second=b,**interval(losses[a]-losses[b],seed=plan['bootstrap_seed'],n_boot=plan['bootstrap_replicates']),
        n_groups=len(losses[a]),n_trials=len(combined),units='bits_per_trial',ci_scope='fixed_predictions_identity_bootstrap_no_refit') for a,b in pairs]
    required=pairs if packet=='N1' else [('H','HP'),('Hnoise','HP'),('Hdup','HP')]
    progression=all(row['ci_lower']>0 for row in effects if (row['first'],row['second']) in required)
    receipt.update(status='REAL_COMPARISON_COMPLETE',new_head_fits=len(head_receipts),fit_counts=ledger.summary(),
        finite_prediction_status='PASS',budget_execution_status='COMPLETE',artifact_integrity_status='PASS',
        optimization_diagnostics=dict(optimizer_success=sum(r['optimizer_success'] for r in head_receipts),heads=len(head_receipts)),
        scientific_effect_status='POSITIVE_EXPLORATORY_WITH_CONTROLS' if progression else 'NO_CONTROLLED_INCREMENT_ESTABLISHED',
        control_status='PASS' if progression else 'NO_CLEAR_ADVANTAGE_OVER_ALL_CONTROLS',complete_folds=5,planned_folds=5)
    pd.DataFrame(effects).to_csv(public/'paired_effects_v2_1.csv',index=False)
    pd.DataFrame([dict(view=k,ce_bits=float(v.mean()),n_groups=len(v)) for k,v in losses.items()]).to_csv(public/'risks.csv',index=False)
    write_json(public/'fold_execution.json',folds);write_json(public/'route_decision.json',receipt)
    lines=[f'# {lane} new real comparison','',receipt['scientific_effect_status'],
        '', '| First | Second | Gain bits/trial | 95% fixed-prediction CI |', '|---|---|---:|---|']
    for r in effects:lines.append(f'| {r["first"]} | {r["second"]} | {r["estimate"]:.6f} | [{r["ci_lower"]:.6f}, {r["ci_upper"]:.6f}] |')
    lines+=['','New finite-budget learner on an already explored cohort. Risk differences are not estimates certified as mutual information. No old failure or primary result is replaced.','']
    (report/'REAL_COMPARISON.md').write_text('\n'.join(lines))
    return receipt
