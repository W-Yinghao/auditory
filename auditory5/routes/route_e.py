"""E0 descriptive native-layout within-record block decoding; E1 unavailable."""
import json,pickle,warnings,traceback
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import softmax
from sklearn.neural_network import MLPClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.model_selection import GroupKFold
from auditory5.provenance import ROOT,require_slurm,write_json,digest
from auditory5.contracts import FitScope
from auditory5.probes import (bin_20ms,fit_probe,CandidateTabularScaler,CandidateWeightedPCA,
    candidate_class_weights,fit_temperature,weighted_log_loss_nats)
from auditory5.metrics import classification_metrics,candidate_log_losses_bits
from auditory5.statistics import paired_cluster_bootstrap


def _mlp(x,y,groups,alpha):
    head=MLPClassifier(hidden_layer_sizes=(32,),activation='relu',solver='lbfgs',alpha=alpha,
                       max_iter=5000,max_fun=250000,tol=1e-6,random_state=11)
    with warnings.catch_warnings():
        warnings.simplefilter('error',ConvergenceWarning)
        head.fit(x,y,sample_weight=candidate_class_weights(y,groups))
    return head


def _logits(head,x):
    # sklearn's final identity logits, avoiding probability clipping for calibration.
    a=x
    for w,b in zip(head.coefs_[:-1],head.intercepts_[:-1]):a=np.maximum(0,a@w+b)
    d=(a@head.coefs_[-1]+head.intercepts_[-1]).ravel()
    return np.column_stack((np.zeros(len(d)),d))


def fit_small_readout(x,y,groups,scope):
    scope.assert_fit_groups(groups);alphas=[.01,.1,1.,10.];oof={a:np.full((len(x),2),np.nan) for a in alphas}
    for tr,va in GroupKFold(3).split(x,y,groups):
        inner=FitScope(tuple(np.unique(groups[tr])),tuple(np.unique(groups[va])),tuple(scope.test_groups))
        scale=CandidateTabularScaler().fit(x[tr],groups[tr],inner)
        pca=CandidateWeightedPCA(32).fit(scale.transform(x[tr]),groups[tr],inner)
        a,b=pca.transform(scale.transform(x[tr])),pca.transform(scale.transform(x[va]))
        for alpha in alphas:oof[alpha][va]=_logits(_mlp(a,y[tr],groups[tr],alpha),b)
    weights=candidate_class_weights(y,groups);alpha=min(alphas,key=lambda a:(weighted_log_loss_nats(oof[a],y,weights),-a))
    temperature=fit_temperature(oof[alpha],y,groups,scope)['temperature']
    scale=CandidateTabularScaler().fit(x,groups,scope);pca=CandidateWeightedPCA(32).fit(scale.transform(x),groups,scope)
    head=_mlp(pca.transform(scale.transform(x)),y,groups,alpha)
    return {'scale':scale,'pca':pca,'head':head,'temperature':temperature,'alpha':alpha,'scope_hash':scope.hash}


def small_predict(model,x):
    logits=_logits(model['head'],model['pca'].transform(model['scale'].transform(x)))
    return {'raw':softmax(logits,axis=1),'calibrated':softmax(logits/model['temperature'],axis=1)}


def block_folds(rows):
    groups=rows.filter_block_id.astype(str).to_numpy();y=rows.stimulus_local_id.to_numpy(int)
    good=[g for g in np.unique(groups) if set(y[groups==g])=={0,1}]
    keep=np.isin(groups,good)
    # Four test folds plus >=3 training blocks for inner grouped calibration.
    if len(good)<4 or any(np.sum(keep&(y==k))<40 for k in [0,1]):return keep,[]
    splits=list(GroupKFold(4).split(np.zeros((int(keep.sum()),1)),y[keep],groups[keep]))
    return keep,splits


def family_is_complete(support, family):
    """No aggregate over only numerically successful records of one head."""
    eligible=[row for row in support if row['status']=='PASS']
    return bool(eligible) and all(row.get('families',{}).get(family)=='PASS' for row in eligible)


def _record_readout(x,y,groups,rows,folds,family,task,dest,rid):
    predictions=[]
    for fold,(tr,te) in enumerate(folds):
        scope=FitScope(tuple(np.unique(groups[tr])),test_groups=tuple(np.unique(groups[te])))
        if family=='linear':
            model=fit_probe(x[tr],y[tr],groups[tr],scope,seed=11);probs=model.predict(x[te])
        else:
            model=fit_small_readout(x[tr],y[tr],groups[tr],scope);probs=small_predict(model,x[te])
        with (dest/(rid+'_'+family+'_fold'+str(fold)+'.pkl')).open('xb') as f:
            pickle.dump({'model':model,'scope':scope,'within_record_only':True},f)
        for calibration,prob in probs.items():
            part=rows.iloc[te][['trial_id','record_id','candidate_id','split_group_id','stimulus_local_id','filter_block_id']].copy()
            part['task']=task;part['fold']=fold;part['family']=family;part['calibration']=calibration
            part['p0']=prob[:,0];part['p1']=prob[:,1];predictions.append(part)
    return pd.concat(predictions,ignore_index=True)


def run(config,output_dir,export_run='mff_e0_export_001',validation_run='mff_export_gate_001'):
    require_slurm();dest=Path(output_dir);dest.mkdir(parents=True,exist_ok=False)
    if not dest.resolve().is_relative_to(ROOT/'private'):raise ValueError('E0 individual outputs must remain private')
    base=ROOT/config['paths']['private_relative'];public=ROOT/config['paths']['aggregates_relative']
    gate=json.loads((public/validation_run/'validation.json').read_text())
    if gate['status']!='PASS' or gate['export_run']!=export_run:raise ValueError('MFF export integration mismatch')
    pairs=pd.read_parquet(base/'data/manifest_001/E_existing_pairs.parquet')
    records=pd.read_parquet(base/'data/manifest_001/records.parquet').set_index('record_id')
    ids=sorted(set(pairs.container_a)|set(pairs.container_b));predictions=[];support=[];failures=[]
    for rid in ids:
        folder=base/'data'/export_run/'P1_CAUSAL20'/rid;s=json.loads((folder/'summary.json').read_text())
        if not s['within_record_filter_state_isolation']:raise ValueError('E0 cannot use continuous filter across folds')
        for name,h in s['output_sha256'].items():
            if digest(folder/name)!=h:raise ValueError('E0 export mutated')
        rows=pd.read_parquet(folder/'events.parquet');rows=rows[rows.accepted].reset_index(drop=True)
        keep,folds=block_folds(rows)
        status={'record_id':rid,'candidate_id':records.loc[rid,'candidate_id'],'task':records.loc[rid,'paradigm_id'],
                'accepted_before_block_support':len(rows),'retained_for_decoding':int(keep.sum()),'status':'PASS' if folds else 'SUPPORT_INSUFFICIENT'}
        support.append(status)
        if not folds:continue
        rows=rows.loc[keep].reset_index(drop=True);arrays=np.load(folder/'all.npy',mmap_mode='r')
        epoch=arrays[rows.stored_epoch_index.to_numpy(int)];starts=rows.post_start_index.to_numpy(int)
        x=bin_20ms(np.stack([v[:,j:j+100] for v,j in zip(epoch,starts)]));y=rows.stimulus_local_id.to_numpy(int)
        groups=rows.filter_block_id.astype(str).to_numpy()
        status['families']={}
        for family in ['linear','MLP32']:
            try:
                part=_record_readout(x,y,groups,rows,folds,family,status['task'],dest,rid)
            except (ConvergenceWarning, RuntimeError) as exc:
                # Only known numerical failures are isolated; all data/scope
                # and unexpected implementation errors still stop this run.
                if not isinstance(exc,ConvergenceWarning) and 'CONVERGENCE' not in str(exc):raise
                status['families'][family]='NUMERICAL_FAILURE'
                failures.append({'record_id':rid,'family':family,'traceback':traceback.format_exc()})
                continue
            status['families'][family]='PASS'
            part.to_parquet(dest/(rid+'_'+family+'_oof.parquet'),index=False)
            predictions.append(part)
        print(json.dumps({'E0_completed_record_count':sum(r['status']=='PASS' for r in support),'processed_record_count':len(support)}),flush=True)
    frame=pd.concat(predictions,ignore_index=True) if predictions else pd.DataFrame();frame.to_parquet(dest/'oof_predictions.parquet',index=False)
    pd.DataFrame(support).to_parquet(dest/'support.parquet',index=False)
    write_json(dest/'numerical_failures.json',failures)
    scores=[]
    if len(frame):
        for (rid,family,calibration),r in frame.groupby(['record_id','family','calibration']):
            score=classification_metrics(r.stimulus_local_id.to_numpy(),r[['p0','p1']].to_numpy(),r.candidate_id.to_numpy(),r.trial_id.to_numpy())
            scores.append({'record_id':rid,'candidate_id':r.candidate_id.iloc[0],'task':r.task.iloc[0],'family':family,'calibration':calibration,**score})
    scoreframe=pd.DataFrame(scores);scoreframe.to_parquet(dest/'record_metrics.parquet',index=False);aggregates=[]
    if len(scoreframe):
        for (family,calibration),r in scoreframe.groupby(['family','calibration']):
            if not family_is_complete(support,family):continue
            lookup=r.set_index('record_id');valid=[p for p in pairs.to_dict('records') if p['container_a'] in lookup.index and p['container_b'] in lookup.index]
            for task in ['puretone','bapa']:
                vals=[];gids=[]
                for pair in valid:
                    source=next(i for i in [pair['container_a'],pair['container_b']] if records.loc[i,'paradigm_id']==task)
                    vals.append(float(lookup.loc[source,'ce_bits']));gids.append(pair['participant_id'])
                if not vals:continue
                ci=paired_cluster_bootstrap(np.ones(len(vals)),vals,gids,n_boot=2000)
                aggregates.append({'family':family,'calibration':calibration,'task':task,'complete_pairs':len(valid),
                    'mean_CE_bits':float(np.mean(vals)),'J_bits_interval':ci})
    family_status={family:('COMPLETE' if family_is_complete(support,family) else
        'NUMERICAL_FAILURE' if any(f['family']==family for f in failures) else 'SUPPORT_INSUFFICIENT') for family in ['linear','MLP32']}
    summary={'stage':'E0_native_within_record','status':('E0_PARTIAL_NUMERICAL_FAILURE' if failures else 'DESCRIPTIVE_E0_COMPLETE') if aggregates else ('NUMERICAL_FAILURE' if failures else 'SUPPORT_INSUFFICIENT'),
        'E1_status':'SUPPORT_INSUFFICIENT','E1_reason':'shared-layout bapa safe candidate indices16 <20; no population transfer model',
        'records_requested':len(ids),'records_with_block_support':sum(r['status']=='PASS' for r in support),
        'records_decoded':sum(r['status']=='PASS' and all(v=='PASS' for v in r.get('families',{}).values()) for r in support),
        'family_status':family_status,'numerical_failure_record_heads':len(failures),
        'incomplete_family_aggregates_withheld':True,'results':aggregates,
        'validation_unit':'independently filtered 60s blocks within each record; not held-out children',
        'uncertainty_unit':'fixed OOF paired candidates, 2000 bootstrap; small paired sample',
        'source_groups':'mixed and unknown; not interpreted as all CI','clinical_claim':None,
        'full_E1_complete':False,'known_limitations':['same-session retrospective offline QC','small sample','task-specific literal labels','no source/target transfer inference']}
    write_json(dest/'aggregate.json',summary);return summary
