"""Versioned no-refit repair of finite-logit cross-entropy evaluation.

This module never calls a fitter. It retains the frozen encoder/readout recipe,
all fitted coefficients and every lambda; only the representation of the same
logistic loss is changed from rounded probability to logaddexp on its logits.
"""
import copy
import hashlib
import json
from pathlib import Path
import pickle
import shutil
import contextlib
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
from .runtime import digest,write_json,safe_run
from .gates import require_capability
from .data import load_support,load_epochs
from .evaluate import _view_matrices,_indices,_choose_lambda,_validate_selection,MODEL_NAMES,LAMBDAS,r3_contrasts,_research_status,r3_probe_algorithm_hash
from .r3_execution import audit_checkpoints,checkpoint_feature_loader,_check_sources
from .statistics import hierarchical_weights
from .r3_stable_risk import stable_metrics,paired_logit_contrasts


def scoring_hash():
    h=hashlib.sha256()
    for name in ('r3_stable_risk.py','r3_scoring.py'):
        h.update(name.encode());h.update(Path(__file__).with_name(name).read_bytes())
    return h.hexdigest()


def tests(root,private,public,report,config,args):
    import pytest
    with (private/'pytest.log').open('w') as f,contextlib.redirect_stdout(f),contextlib.redirect_stderr(f):
        status=pytest.main(['-q','--import-mode=importlib','-p','no:cacheprovider','--basetemp='+str(private/'tmp'),'--junitxml='+str(private/'tests.xml'),'tests/auditory_v3/test_r3_stable_risk.py'])
    tree=ET.parse(private/'tests.xml').getroot();counts={x:len(tree.findall('.//'+x)) for x in ('testcase','failure','error','skipped')}
    return dict(status='PASS' if status==0 and not any(counts[x] for x in ('failure','error','skipped')) else 'FAIL',packet='R3_SCORING',tests=counts,scoring_algorithm_sha256=scoring_hash(),new_head_fits=0,new_encoder_fits=0)


def require_scoring_test(root,private,run):
    folder=root/'private/auditory_v3'/safe_run(run);receipt=json.loads((folder/'completion.json').read_text())
    current=json.loads((private/'start.json').read_text())
    if receipt.get('status')!='PASS' or receipt.get('packet')!='R3_SCORING' or receipt.get('scoring_algorithm_sha256')!=scoring_hash() or receipt['config_sha256']!=current['config_sha256']:raise ValueError('STABLE_SCORING_TEST_GATE_REQUIRED')


def _loader(root,private,args,stage):
    require_capability(root,private,args['gate_run'],'R3',args['split_run'])
    require_scoring_test(root,private,args['scoring_test_run'])
    m,s,h,r,support=load_support(root,args['split_run'])
    if support['R3_support']!='SUFFICIENT':raise ValueError('R3_SUPPORT_LIMITED')
    states,bindings,training=audit_checkpoints(root,private,args['representation_run'],stage,args['split_run'],m,s)
    post,pre=load_epochs(m,r)
    return m,s,checkpoint_feature_loader(m,post,pre,s,states,stage),bindings,training


def repair_selection(root,private,public,report,config,args):
    m,s,loader,bindings,training=_loader(root,private,args,'selection')
    original=root/'private/auditory_v3'/safe_run(args['selection_run'])
    completion=json.loads((original/'completion.json').read_text());receipt=json.loads((original/'selection_receipt.json').read_text())
    _check_sources(json.loads((original/'start.json').read_text()),json.loads((private/'start.json').read_text()))
    _validate_selection(m,s,receipt)
    if digest(original/'selection_receipt.json')!=completion['selection_receipt_sha256']:raise ValueError('ORIGINAL_SELECTION_RECEIPT_CHANGED')
    if digest(original/'checkpoint_bindings.json')!=completion['checkpoint_bindings_sha256']:raise ValueError('ORIGINAL_CHECKPOINT_BINDINGS_CHANGED')
    if bindings!=json.loads((original/'checkpoint_bindings.json').read_text()):raise ValueError('ORIGINAL_ENCODERS_CHANGED')
    with (original/'probe_models.pkl').open('rb') as f:models=pickle.load(f)
    if len(models)!=180:raise ValueError('ALL_180_FITTED_HEADS_REQUIRED')
    diagnostics=[];choices=copy.deepcopy(receipt['selections']);lookup={(c['outer_fold'],c['probe']):c for c in choices}
    for fold in s['folds']:
        number=int(fold['outer_fold']);ix=_indices(m,fold['R3_validation_groups'])
        matrices=_view_matrices(m,loader,number,'selection',ix);weights=hierarchical_weights(m.iloc[ix]);y=m.iloc[ix].stimulus_local_id.to_numpy()
        for name in MODEL_NAMES:
            scores={}
            for lam in LAMBDAS:
                item=models[f'fold{number}__{name}__lambda{lam:g}'];model=item['model']
                if sorted(item['fit_groups'])!=sorted(fold['R3_fit_groups']) or sorted(item['validation_groups'])!=sorted(fold['R3_validation_groups']):raise ValueError('SAVED_HEAD_SCOPE_CHANGED')
                z=model.decision_function(item['scaler'].transform(matrices[name]));metric=stable_metrics(y,z,weights)
                scores[lam]=metric['ce_bits']
                diagnostics.append(dict(outer_fold=number,probe=name,lambda_l2=lam,optimizer_success=model.success,stable_validation_ce_bits=metric['ce_bits'],finite_logits=bool(np.isfinite(z).all()),rounded_endpoint_probabilities=int(np.sum((model.predict_proba(item['scaler'].transform(matrices[name]))==0)|(model.predict_proba(item['scaler'].transform(matrices[name]))==1)))))
            chosen=_choose_lambda(scores);entry=lookup[(number,name)]
            entry.update(selected_lambda=chosen,status='PASS' if chosen is not None else 'NUMERICAL_FAIL',validation_ce_bits={str(l):v for l,v in scores.items()})
    repaired=copy.deepcopy(receipt);repaired.update(selections=choices,status='PASS' if all(c['status']=='PASS' for c in choices) else 'COMPLETED_WITH_NUMERICAL_FAILURES',scoring_algorithm_sha256=scoring_hash(),scoring_method='exact_logaddexp_from_saved_finite_logits',scoring_test_run=args['scoring_test_run'],original_selection_run=args['selection_run'],original_selection_receipt_sha256=digest(original/'selection_receipt.json'),fitted_models_sha256=digest(original/'probe_models.pkl'),new_head_fits=0)
    _validate_selection(m,s,repaired)
    write_json(private/'selection_receipt.json',repaired);write_json(private/'checkpoint_bindings.json',bindings)
    pd.DataFrame(diagnostics).to_parquet(private/'scoring_diagnostics.parquet',index=False)
    pd.DataFrame(choices).to_parquet(private/'probe_choices.parquet',index=False)
    summary={k:v for k,v in completion.items() if k not in ('job_id','elapsed_seconds','config_sha256')}
    summary.update(status='PROBES_SELECTED' if repaired['status']=='PASS' else 'COMPLETED_WITH_NUMERICAL_FAILURES',execution='COMPLETE' if repaired['status']=='PASS' else 'NUMERICAL_FAIL',selection_status=repaired['status'],selected_choices=sum(c['status']=='PASS' for c in choices),selection_receipt_sha256=digest(private/'selection_receipt.json'),checkpoint_bindings_sha256=digest(private/'checkpoint_bindings.json'),scoring_algorithm_sha256=scoring_hash(),scoring_test_run=args['scoring_test_run'],original_selection_run=args['selection_run'],new_head_fits=0,reused_fitted_heads=180)
    (report/'SCORING_REPAIR.md').write_text('# Finite-logit CE repair\n\nAll180existingcoefficients andoriginal encodercheckpoints reused. Nohead/encoderfitting, noouter-testinference, noprobabilityclipping orcandidateomission. The same logistic risk is evaluated by logaddexp before probability rounding. Every lambda in every selection grid was rescored. Original probability-based failures remain in their immutable run.\n')
    return summary


def repair_final(root,private,public,report,config,args,original_summary):
    m,s,loader,bindings,training=_loader(root,private,args,'final')
    with (private/'probe_models.pkl').open('rb') as f:models=pickle.load(f)
    metadata=['trial_id','split_group_id','A_half','previous_code','previous_run_bin','stimulus_local_id','outer_fold']
    frame=m[metadata].copy()
    for name in MODEL_NAMES:frame[name]=np.nan
    for fold in s['folds']:
        number=int(fold['outer_fold']);ix=_indices(m,fold['test_groups']);matrices=_view_matrices(m,loader,number,'final',ix)
        for name in MODEL_NAMES:
            saved=models[f'fold{number}__{name}'];model=saved.get('model')
            if model is not None:
                if sorted(saved['fit_groups'])!=sorted(fold['train_groups']) or sorted(saved['test_groups'])!=sorted(fold['test_groups']):raise ValueError('FINAL_HEAD_SCOPE_CHANGED')
                frame.loc[ix,name]=model.decision_function(saved['scaler'].transform(matrices[name]))
    corrected,identities=paired_logit_contrasts(frame,{n:n for n in MODEL_NAMES},r3_contrasts())
    summary=dict(original_summary,**corrected)
    with (private/'fit_diagnostics.pkl').open('rb') as f:diagnostics=pickle.load(f)
    complete=bool(diagnostics.success.all()) and all(x['status']=='PASS' for x in summary['metrics'].values())
    summary.update(execution='COMPLETE' if complete else 'NUMERICAL_FAIL',primary_status='PASS' if summary['contrasts']['SUP_minus_MATCH__Htrial_Zpost']['status']=='PASS' else 'NUMERICAL_FAIL',research=_research_status(summary),incomplete_models=[n for n,x in summary['metrics'].items() if x['status']!='PASS'],scoring_algorithm_sha256=scoring_hash(),scoring_method='exact_logaddexp_from_saved_finite_logits',scoring_test_run=args['scoring_test_run'],postprocessing_additional_head_fits=0)
    summary.pop('research_reason',None)
    if summary['research']=='UNRESOLVED_ALTERNATIVE_EXPLANATION':summary['research_reason']='INCOMPLETE_REQUIRED_CONTROLS' if any(summary['metrics'][n]['status']!='PASS' for n in ('Htrial','L0_post','RAND_post','MATCH__Htrial_Zpre')) else 'PRE_DIAGNOSTIC_REVIEW_REQUIRED'
    write_json(private/'original_probability_summary.json',original_summary)
    frame.to_parquet(private/'logit_predictions.parquet',index=False);identities.to_parquet(private/'stable_identity_risks.parquet',index=False)
    for filename,key,label in [('R3_metrics.csv','metrics','model'),('R3_paired_effects.csv','contrasts','contrast')]:
        shutil.copyfile(public/filename,private/('original_probability_'+filename))
        pd.DataFrame([dict({label:k},**v) for k,v in summary[key].items()]).to_csv(public/filename,index=False)
    return summary
