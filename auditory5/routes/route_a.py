"""Fold-local conditional-response repeatability and background diagnostics."""
import json,pickle
from pathlib import Path
import numpy as np
import pandas as pd
from auditory5.provenance import ROOT,require_slurm,write_json,object_hash,digest
from auditory5.routes.a_matching import mean_matching_matrices,aggregate_match,bootstrap_match


def fit_axis(x,cap=8,random_projection=False):
    x=np.asarray(x,float);mu=x.mean(axis=0);centered=x-mu
    _,s,v=np.linalg.svd(centered,full_matrices=False);rank=int(np.sum(s>max(x.shape)*np.finfo(float).eps*s[0])) if len(s) and s[0]>0 else 0
    n=min(cap,len(x)-2,rank)
    if n<1:raise ValueError('A_DEGENERATE_TRAINING_CONTRAST')
    if random_projection:
        v=np.linalg.qr(np.random.default_rng(20260917).normal(size=(x.shape[1],n)))[0].T
    else:v=v[:n]
    scale=((x-mu)@v.T).std(axis=0)
    if (scale<=0).any():raise ValueError('A zero training axis scale')
    return {'center':mu,'components':v,'scale':scale,'rank':rank,'fit_candidates':len(x)}


def project(x,axis):return (x-axis['center'])@axis['components'].T/axis['scale']


def summary_features(post,pre,rows,ids,half_column,eligible_column,budget=None,repetitions=1,support_budget=None):
    result={'post_delta':[],'pre_delta':[],'post_mean':[],'pre_mean':[],'quality':[]}
    qualified=[]
    for g in ids:
        own=rows.split_group_id.eq(g).to_numpy()&rows[eligible_column].fillna(False).to_numpy(bool)
        by={(h,c):np.flatnonzero(own&rows[half_column].eq(h).to_numpy()&rows.stimulus_local_id.eq(c).to_numpy()) for h in [0,1] for c in [0,1]}
        if any(len(v)<(support_budget or budget or 1) for v in by.values()):continue
        if any(rows.loc[own&rows[half_column].eq(h).to_numpy(),'A_block_id'].nunique()<4 for h in [0,1]):continue
        pm=np.zeros((repetitions,2,2,post.shape[1]));pr=np.zeros((repetitions,2,2,pre.shape[1]));q=np.zeros((repetitions,2,2))
        for (h,c),ix in by.items():
            seed=int(object_hash({'group':str(g),'half':h,'class':c,'budget':budget,'seed':20260917})[:8],16)
            rng=np.random.default_rng(seed)
            for r in range(repetitions):
                sample=ix if budget is None else rng.choice(ix,budget,replace=False)
                pm[r,h,c]=post[sample].mean(axis=0);pr[r,h,c]=pre[sample].mean(axis=0)
                q[r,h,c]=np.log1p(rows.iloc[sample].all_ptp_uv.to_numpy()).mean()
        qualified.append(g)
        result['post_delta'].append(pm[:,:,1]-pm[:,:,0]);result['pre_delta'].append(pr[:,:,1]-pr[:,:,0])
        result['post_mean'].append(pm.mean(axis=2));result['pre_mean'].append(pr.mean(axis=2));result['quality'].append(q)
    return qualified,{k:np.stack(v,axis=1) for k,v in result.items()} if qualified else {}


def fit_transforms(training):
    means={k:v.mean(axis=(0,2)) for k,v in training.items()} # candidate × feature, averaging reps and halves
    axes={k:fit_axis(means[k]) for k in ['post_delta','pre_delta','post_mean']}
    context_axes={k:fit_axis(means[k],4) for k in ['post_mean','pre_delta','pre_mean']}
    qmu=means['quality'].mean(axis=0);qscale=means['quality'].std(axis=0);qscale[qscale<1e-12]=1
    context=np.c_[*[project(means[k],axis) for k,axis in context_axes.items()],(means['quality']-qmu)/qscale]
    cmean=context.mean(axis=0);cc=context-cmean;target=project(means['post_delta'],axes['post_delta']);ymu=target.mean(axis=0)
    coef=np.linalg.solve(cc.T@cc+10*np.eye(cc.shape[1]),cc.T@(target-ymu))
    return {'axes':axes,'context_axes':context_axes,'quality_mean':qmu,'quality_scale':qscale,
            'context_mean':cmean,'response_mean':ymu,'ridge_coefficient':coef,'ridge_alpha':10,
            'random_axis':fit_axis(means['post_delta'],random_projection=True)}


def transform_summaries(values,transforms):
    axes=transforms['axes'];out={k:project(values[name],axes[name]) for k,name in [('post','post_delta'),('pre','pre_delta'),('background','post_mean')]}
    context=np.concatenate([*[project(values[k],axis) for k,axis in transforms['context_axes'].items()],
        (values['quality']-transforms['quality_mean'])/transforms['quality_scale']],axis=-1)
    prediction=(context-transforms['context_mean'])@transforms['ridge_coefficient']+transforms['response_mean']
    out['background_adjusted']=out['post']-prediction;out['random_projection']=project(values['post_delta'],transforms['random_axis'])
    return out


def _safe(x):
    if isinstance(x,dict):return {str(k):_safe(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [_safe(v) for v in x]
    if isinstance(x,(float,np.floating)):return float(x) if np.isfinite(x) else None
    if isinstance(x,(np.integer,)):return int(x)
    return x


def run(config,split_run,representation_plan,modes,output_dir):
    require_slurm();dest=Path(output_dir);dest.mkdir(parents=True,exist_ok=False)
    if not dest.resolve().is_relative_to(ROOT/'private'):raise ValueError('A matrices must remain private')
    base=ROOT/config['paths']['private_relative'];split=json.loads((base/'splits'/split_run/'folds.json').read_text())
    support=pd.read_parquet(base/'splits'/split_run/'support.parquet');eligible=set(support.loc[support.A,'split_group_id'])
    repdir=Path(representation_plan).parent/'outputs';output=[]
    analyses=[('alternate20','A_half','A_boundary_eligible',20,20),('early_late20','early_late_half','early_late_boundary_eligible',20,20),
              ('alternate20_common40','A_half','A_boundary_eligible',20,40),('alternate40','A_half','A_boundary_eligible',40,40)]
    for mode in modes:
        mode_cache={}
        for name,half,qual,budget,minimum_support in analyses:
            matrices={k:[] for k in ['post','pre','background','background_adjusted','random_projection']};ids_by_fold=[];details=[]
            for fold in split['folds']:
                directory=repdir/f"outer{fold['outer_fold']}_all_{mode}"
                completion=json.loads((directory/'completion.json').read_text());task=json.loads((directory/'task.json').read_text())
                if completion['status']!='PASS' or set(task['fit_groups'])&set(fold['test_groups']):raise ValueError('A encoder gate or identity leakage')
                with np.load(directory/'features.npz',allow_pickle=False) as f:post=f['post'].astype(float);pre=f['pre'].astype(float);trials=f['trial_ids']
                rows=pd.read_parquet(directory/'feature_rows.parquet')
                if not np.array_equal(trials,rows.trial_id):raise ValueError('A feature/event alignment')
                train_ids,train=summary_features(post,pre,rows,sorted(eligible&set(fold['train_groups'])),half,qual)
                test_ids,test=summary_features(post,pre,rows,sorted(eligible&set(fold['test_groups'])),half,qual,budget,20,minimum_support)
                if len(train_ids)<4 or len(test_ids)<2:
                    details.append({'fold':fold['outer_fold'],'status':'SUPPORT_INSUFFICIENT','train_groups':len(train_ids),'test_groups':len(test_ids)})
                    continue
                transforms=fit_transforms(train);values=transform_summaries(test,transforms);items={}
                for key,value in values.items():
                    items[key]=mean_matching_matrices(value[:,:,0],value[:,:,1]);matrices[key].append(items[key])
                ids_by_fold.append(test_ids)
                with (dest/f'{mode}_{name}_fold{fold["outer_fold"]}.pkl').open('xb') as f:pickle.dump({'transforms':transforms,'fit_groups':train_ids,'test_groups':test_ids,'matching_matrices':items},f)
                details.append({'fold':fold['outer_fold'],'status':'PASS','train_groups':len(train_ids),'test_groups':len(test_ids),
                    'zero_vector_counts':{k:v['undefined_zero_norm_count'] for k,v in items.items()},
                    'norms':{k:v['norm_summary'] for k,v in items.items()},'rank':{k:v['mean_diag_rank'] for k,v in items.items()}})
            stats={};n=sum(len(ids) for ids in ids_by_fold)
            if len(ids_by_fold)==len(split['folds']):
                pre_m=[m['cosine'] for m in matrices['pre']]
                for key,mats in matrices.items():
                    stats[key]=bootstrap_match([m['cosine'] for m in mats],ids_by_fold,n_boot=2000,seed=20260917,
                        paired_matrices=pre_m if key=='post' else None)
                    for metric in ['inner_product','squared_distance']:
                        stats[key][metric]=aggregate_match([m[metric] for m in mats],ids_by_fold,metric)['estimate']
                # Prespecified pairing-offset diagnostic, not an exchangeability p-value.
                rotated=[m['cosine'][:,np.roll(np.arange(len(m['cosine'])),1)] for m in matrices['post']]
                stats['rotated_pairing_diagnostic']=aggregate_match(rotated,ids_by_fold)['estimate']
                loo=[]
                for k,ids in enumerate(ids_by_fold):
                    for j in range(len(ids)):
                        ix=np.delete(np.arange(len(ids)),j);mats=[m['cosine'] for m in matrices['post']];groups=[list(g) for g in ids_by_fold]
                        mats[k]=mats[k][np.ix_(ix,ix)];groups[k]=list(np.asarray(groups[k])[ix]);loo.append(aggregate_match(mats,groups)['estimate'])
                stats['post_leave_one_candidate_out_range']=[min(loo),max(loo)]
                mode_cache[name]=([m['cosine'] for m in matrices['post']],ids_by_fold)
                if name=='alternate40' and 'alternate20_common40' in mode_cache:
                    other,other_ids=mode_cache['alternate20_common40']
                    if other_ids!=ids_by_fold:raise ValueError('A trial-budget common cohort mismatch')
                    stats['budget40_minus20_common_cohort']=bootstrap_match(mode_cache[name][0],ids_by_fold,paired_matrices=other)
            output.append({'mode':mode,'analysis':name,'n_candidates':n,'status':'INTERIM_A_CORE_COMPLETE' if stats and n>=25 else 'SUPPORT_INSUFFICIENT',
                'statistics':stats,'folds':details})
            print(json.dumps({'A_mode':mode,'analysis':name,'n_candidates':n}),flush=True)
    summary=_safe({'stage':'A_repeatability_core','status':'INTERIM','results':output,
        'pending_controls':['independent raw-segment filter-reset sensitivity','additional history/block-position balancing'],
        'claim':'same-session block repetition, not across-day retest or identified auditory ability',
        'bootstrap_scope':'2000 fixed-OOF identity draws within fold; same matrices for paired post-pre difference',
        'plan_hash':digest(representation_plan),'full_route_complete':False})
    write_json(dest/'aggregate.json',summary);return summary
