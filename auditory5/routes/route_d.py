"""Strictly nested low-dimensional clinical readouts in fold-specific coordinates."""
import itertools,json,pickle
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from auditory5.provenance import ROOT,require_slurm,write_json,object_hash,digest
from auditory5.contracts import FitScope
from auditory5.head_geometry import decompose_head,max_softmax_difference
from auditory5.probes import fit_probe,CandidateWeightedPCA
from auditory5.statistics import paired_cluster_bootstrap

COLUMNS=['age_months','log1p_device_duration_months','better_ear_4freq_source_units']
ALPHA_C=(.1,1.,10.);ALPHA_EEG=(1.,10.,100.,'drop')


def grouped_ridge_predict(train_groups,test_groups,y,penalties):
    """Groupwise L2 penalties; drop removes columns exactly, intercept unpenalized."""
    xs=[];zs=[];alphas=[]
    for name,alpha in penalties.items():
        if alpha=='drop':continue
        x=np.asarray(train_groups[name],float);z=np.asarray(test_groups[name],float)
        if x.ndim!=2 or z.ndim!=2 or x.shape[1]!=z.shape[1] or not np.isfinite(x).all() or not np.isfinite(z).all():raise ValueError('clinical feature shape/finite contract')
        mu=x.mean(axis=0);scale=x.std(axis=0);scale[scale<1e-12]=1
        xs.append((x-mu)/scale);zs.append((z-mu)/scale);alphas.extend([float(alpha)]*x.shape[1])
    if not xs:return np.repeat(float(np.mean(y)),len(next(iter(test_groups.values()))))
    x=np.concatenate(xs,axis=1);z=np.concatenate(zs,axis=1);target=np.asarray(y,float);center=target.mean()
    coef=np.linalg.solve(x.T@x+np.diag(alphas),x.T@(target-center))
    return np.clip(center+z@coef,0,100)


def penalty_grid(model):
    if model=='D0_mean':return [{}]
    names={'D1_C':['C'],'D2_CV':['C','V'],'D3_CVN':['C','V','N'],'D4_CN':['C','N'],
           'D5_CFULL':['C','FULL'],'D7_CPRE':['C','PRE']}.get(model)
    if model.startswith('D6_CRANDOM_'):names=['C','V',model.removeprefix('D6_C')]
    if names is None:raise ValueError('unknown clinical model')
    return [dict(zip(names,values)) for values in itertools.product(*(ALPHA_C if n=='C' else ALPHA_EEG for n in names))]


def choose_penalties(inner,model):
    """Each inner fold has independently trained encoder/head/projection features."""
    options=[]
    for penalties in penalty_grid(model):
        losses=[]
        for fold in inner:
            p=grouped_ridge_predict(fold['train'],fold['test'],fold['y_train'],penalties)
            losses.extend(abs(fold['y_test']-p))
        dims=sum(inner[0]['train'][name].shape[1] for name,a in penalties.items() if name!='C' and a!='drop')
        strength=sum(float(a) for a in penalties.values() if a!='drop')
        options.append((float(np.mean(losses)),dims,-strength,penalties))
    minimum=min(x[0] for x in options)
    winner=min((x for x in options if x[0]<=minimum+1e-12),key=lambda x:(x[1],x[2]))
    return winner[3],{'inner_mae':winner[0],'EEG_dimensions':winner[1],'grid_size':len(options)}


def candidate_means(z,y,groups,wanted,trial_ids,budget=40,repetitions=20):
    result=[]
    for g in wanted:
        byclass=[]
        for c in [0,1]:
            ix=np.flatnonzero((groups==g)&(y==c))
            if len(ix)<budget:raise ValueError('D support changed below40/class')
            # Stable by identity and class, shared across encoders/folds and pre/post.
            rng=np.random.default_rng(int(object_hash({'group':str(g),'class':c,'seed':20260917})[:8],16))
            weights=np.zeros(len(ix))
            for _ in range(repetitions):weights[rng.choice(len(ix),budget,replace=False)]+=1/(budget*repetitions)
            byclass.append(weights@z[ix])
        result.append(byclass)
    return np.asarray(result)


def make_features(payload,head,clinical,train_ids,test_ids):
    """Fit every projection in current training identities, return <=8 EEG features."""
    groups=payload['groups'].astype(str);y=payload['y'];post=payload['post'].astype(float);pre=payload['pre'].astype(float)
    ids=list(train_ids)+list(test_ids);m=np.isin(groups,train_ids)
    scope=FitScope(tuple(train_ids),test_groups=tuple(test_ids))
    scope.assert_fit_groups(groups[m]);mu=np.mean([post[groups==g].mean(axis=0) for g in train_ids],axis=0)
    w,b=head.effective_linear_head();geometry=decompose_head(torch.from_numpy(w),torch.from_numpy(b),torch.from_numpy(mu))
    if geometry.rank!=1:raise ValueError('D_DEGENERATE_HEAD: binary visible rank must equal1 for main readout')
    # Every actual stored feature is checked, in bounded batches.
    maximum=0.
    for start in range(0,len(post),2048):maximum=max(maximum,float(max_softmax_difference(torch.from_numpy(post[start:start+2048]),geometry)))
    if maximum>=1e-10:raise ValueError('D_FIXED_HEAD_INVARIANCE_FAIL')
    u=geometry.visible_basis.numpy();null_projector=geometry.p_null.numpy()
    centered=post-mu;null=centered@null_projector
    nullpca=CandidateWeightedPCA(3).fit(null[m],groups[m],scope)
    fullpca=CandidateWeightedPCA(4).fit(post[m],groups[m],scope)
    prepca=CandidateWeightedPCA(4).fit(pre[m],groups[m],scope)
    if nullpca.rank_<3 or fullpca.rank_<4 or prepca.rank_<4:raise ValueError('D projection rank insufficient for frozen feature dimensions')
    summaries=candidate_means(post,y,groups,ids,payload['trial_ids']);premeans=candidate_means(pre,y,groups,ids,payload['trial_ids'])
    delta=summaries-mu
    features={'C':clinical.loc[ids,COLUMNS].to_numpy(float),
        'V':(delta@u).reshape(len(ids),-1),
        'N':((delta@null_projector-nullpca.mean_)@nullpca.components_.T).reshape(len(ids),-1),
        'FULL':((summaries-fullpca.mean_)@fullpca.components_.T).reshape(len(ids),-1),
        'PRE':((premeans-prepca.mean_)@prepca.components_.T).reshape(len(ids),-1)}
    random_bases=[]
    for k in range(20):
        rng=np.random.default_rng(20260917+k);q,r=np.linalg.qr(null_projector@rng.normal(size=(post.shape[1],3)))
        if np.min(abs(np.diag(r)))<1e-10:raise ValueError('degenerate random null projection')
        random_bases.append(q);features['RANDOM_'+str(k)]=(delta@q).reshape(len(ids),-1)
    n=len(train_ids);split={'train':{k:v[:n] for k,v in features.items()},'test':{k:v[n:] for k,v in features.items()},
        'y_train':clinical.loc[train_ids,'MUSS_source_percentage'].to_numpy(float),'y_test':clinical.loc[test_ids,'MUSS_source_percentage'].to_numpy(float)}
    artifacts={'center':mu,'visible_basis':u,'null_pca':nullpca,'full_pca':fullpca,'pre_pca':prepca,
               'random_bases':random_bases,'features':features,'ids':ids,'scope_hash':scope.hash,
               'head_singular_values':np.linalg.svd(w-w.mean(axis=0),compute_uv=False),'rank':geometry.rank,
               'svd_threshold':geometry.threshold,'max_abs_prob_difference_float64':maximum}
    return split,artifacts


def _payload(directory):
    completion=json.loads((directory/'completion.json').read_text())
    if completion['status']!='PASS':raise ValueError('Representation not complete')
    with np.load(directory/'features.npz',allow_pickle=False) as source:payload={k:source[k] for k in source.files}
    with (directory/'probe_post.pkl').open('rb') as f:head=pickle.load(f)
    return payload,head,completion


def run(config,split_run,representation_plan,modes,output_dir):
    require_slurm();dest=Path(output_dir);dest.mkdir(parents=True,exist_ok=False)
    if not dest.resolve().is_relative_to(ROOT/'private'):raise ValueError('Individual clinical outputs must remain private')
    base=ROOT/config['paths']['private_relative'];split=json.loads((base/'splits'/split_run/'folds.json').read_text())
    support=pd.read_parquet(base/'splits'/split_run/'support.parquet');ids=set(support.loc[support.D,'split_group_id'])
    clinical=pd.read_parquet(base/'data'/split['manifest']/'clinical_index.parquet');clinical=clinical[clinical.clinical_complete&clinical.split_group_id.isin(ids)].set_index('split_group_id')
    if not clinical.index.is_unique or len(clinical)<30:raise ValueError('D_SUPPORT_INSUFFICIENT')
    planpath=Path(representation_plan);plan=json.loads(planpath.read_text());repdir=planpath.parent/'outputs';models=['D0_mean','D1_C','D2_CV','D3_CVN','D4_CN','D5_CFULL','D7_CPRE']+['D6_CRANDOM_'+str(k) for k in range(20)]
    predictions=[];numerics=[];tuning=[]
    for mode in modes:
        for outer in split['folds']:
            of=outer['outer_fold'];train=sorted(ids&set(outer['train_groups']));test=sorted(ids&set(outer['test_groups']))
            payload,head,completion=_payload(repdir/f'outer{of}_all_{mode}')
            if completion['encoder_fit_scope_hash'] is None:raise ValueError('missing encoder scope')
            task=json.loads((repdir/f'outer{of}_all_{mode}'/'task.json').read_text())
            if set(task['fit_groups'])&set(test):raise ValueError('D_OUTER_ENCODER_LEAKAGE')
            inner=[]
            for fold in range(3):
                valid=sorted(g for g in train if outer['D_inner_fold_by_group'][g]==fold);fit=sorted(set(train)-set(valid))
                if mode in ['L0','R_RAND']:
                    if mode=='R_RAND':raise ValueError('D random encoder needs nested train-specific scalers; not implemented; do not reuse outer random features')
                    inner_payload=payload
                    # L0 is deterministic binning; all fitted scaling/PCA/head redone here.
                    eligible=set(support.loc[support.general,'split_group_id'])
                    fit_head=sorted((set(outer['train_groups'])-set(valid))&eligible)
                    mask=np.isin(payload['groups'],fit_head)
                    inner_head=fit_probe(payload['post'][mask],payload['y'][mask],payload['groups'][mask],
                        FitScope(tuple(fit_head),tuple(valid),tuple(test)),seed=11,pca_max_dim=32)
                else:
                    directory=repdir/f'D_outer{of}_inner{fold}_{mode}'
                    inner_payload,inner_head,ic=_payload(directory);it=json.loads((directory/'task.json').read_text())
                    if set(it['fit_groups'])&(set(valid)|set(test)):raise ValueError('D_INNER_ENCODER_LEAKAGE')
                features,artifact=make_features(inner_payload,inner_head,clinical,fit,valid);inner.append(features)
                with (dest/f'{mode}_outer{of}_inner{fold}_projection.pkl').open('xb') as f:pickle.dump(artifact,f)
                numerics.append({'mode':mode,'outer_fold':of,'inner_fold':fold,'rank':artifact['rank'],'max_abs_probability_difference':artifact['max_abs_prob_difference_float64']})
            outer_features,artifact=make_features(payload,head,clinical,train,test)
            with (dest/f'{mode}_outer{of}_projection.pkl').open('xb') as f:pickle.dump(artifact,f)
            numerics.append({'mode':mode,'outer_fold':of,'inner_fold':None,'rank':artifact['rank'],'max_abs_probability_difference':artifact['max_abs_prob_difference_float64']})
            for model in models:
                penalties,info=choose_penalties(inner,model)
                pred=grouped_ridge_predict(outer_features['train'],outer_features['test'],outer_features['y_train'],penalties)
                tuning.append({'mode':mode,'outer_fold':of,'model':model,'penalties':penalties,**info})
                for gid,target,value in zip(test,outer_features['y_test'],pred):predictions.append({'mode':mode,'outer_fold':of,'split_group_id':gid,'model':model,'target':float(target),'prediction':float(value),'absolute_error':float(abs(target-value))})
            print(json.dumps({'D_mode':mode,'completed_outer_fold':of,'clinical_test_groups':len(test)}),flush=True)
    frame=pd.DataFrame(predictions);frame.to_parquet(dest/'clinical_oof.parquet',index=False);write_json(dest/'tuning.json',tuning);write_json(dest/'invariance.json',numerics)
    rows=[]
    for mode in modes:
        f=frame[frame['mode']==mode];errors=f.pivot(index='split_group_id',columns='model',values='absolute_error')
        if len(errors)!=len(ids) or errors.isna().any().any():raise ValueError('D OOF cohort mismatch')
        main=paired_cluster_bootstrap(errors.D2_CV,errors.D3_CVN,errors.index,n_boot=2000)
        vsclinical=paired_cluster_bootstrap(errors.D1_C,errors.D3_CVN,errors.index,n_boot=2000)
        diffs=(errors.D2_CV-errors.D3_CVN).to_numpy();loo=[float(np.delete(diffs,i).mean()) for i in range(len(diffs))]
        target=f.drop_duplicates('split_group_id').target
        rows.append({'mode':mode,'n_candidates':len(errors),'main_D2_minus_D3':main,'clinical_D1_minus_D3':vsclinical,
            'MAE':errors.mean().to_dict(),'leave_one_out_main_gain_range':[min(loo),max(loo)],'ceiling_fraction':float((target==100).mean()),
            'status':'INTERIM_D_NESTED_CORE_COMPLETE','pending_controls':['all-trial/count-QC sensitivity','new stimulus probe on null','float32 inference invariance report'],
            'screen_criteria_met_before_pending_controls':bool(main['estimate']>=.5 and main['ci_lower']>0 and vsclinical['estimate']>0 and min(loo)>0)})
    summary={'stage':'D_nested_clinical_core','status':'INTERIM','modes':rows,'scale':'HA source percentage; EEG/scale concurrence unknown; threshold in source units',
             'independent_confirmation':False,'plan_hash':digest(planpath),'full_routes_complete':False}
    write_json(dest/'aggregate.json',summary);return summary
