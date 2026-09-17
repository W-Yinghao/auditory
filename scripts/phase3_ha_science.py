#!/usr/bin/env python3
"""Frozen HA Phase-3 exploratory models; production runs require Slurm."""
import argparse,csv,hashlib,json,os,shutil
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
BASE=Path(__file__).resolve().parents[1]
CHANNELS=['Fp1','Fp2','Fz','F3','F4','F7','F8','Cz','C3','C4','T3','T4','Pz','P3','P4','T5','T6','Oz','O1','O2']
def mae(a,b):return float(np.mean(np.abs(a-b)))
def splits(n,h,seed):
    out=[]
    for rep in range(h['outer_repeats']):
        outer=list(KFold(h['outer_folds'],shuffle=True,random_state=seed+rep).split(np.arange(n)))
        for fold,(tr,te) in enumerate(outer):
            assert not set(tr)&set(te)
            inner=[(tr[a],tr[b]) for a,b in KFold(h['inner_folds'],shuffle=True,random_state=seed+1000*rep+fold).split(tr)]
            assert all(not set(a)&set(b) for a,b in inner)
            out.append((rep,fold,tr,te,inner))
    return out
def nested(X,y,h,folds,target,require_complete=True):
    pred=np.full((max(x[0] for x in folds)+1,len(y)),np.nan);chosen=[]
    for si,(rep,fold,tr,te,inner) in enumerate(folds):
        best=None
        for alpha in h['ridge_alphas']:
            scores=[]
            for a,b in inner:
                sc=StandardScaler().fit(X[a]);m=Ridge(alpha=float(alpha)).fit(sc.transform(X[a]),y[a]);pp=m.predict(sc.transform(X[b]));pp=np.clip(pp,0,100) if target=='MUSS' else pp;scores.append(mae(y[b],pp))
            cand=(float(np.mean(scores)),float(alpha))
            if best is None or cand<best:best=cand
        sc=StandardScaler().fit(X[tr]);m=Ridge(alpha=best[1]).fit(sc.transform(X[tr]),y[tr]);p=m.predict(sc.transform(X[te]))
        if target=='MUSS':p=np.clip(p,*h['MUSS_prediction_bounds'])
        pred[rep,te]=p;chosen.append({'repeat':int(rep),'outer_fold':int(fold),'alpha':float(best[1]),'train_indices':[int(x) for x in tr],'test_indices':[int(x) for x in te]})
    if require_complete: assert np.isfinite(pred).all()
    return pred,chosen
def bin_features(rid,epoch_run):
    with np.load(BASE/'results'/epoch_run/rid/'epochs.npz',allow_pickle=False) as d:
        x=d['data_uv'].astype(float);t=d['times_s'];codes=d['codes'];mask=d['accepted'][:,0]&(codes==1);ch=[str(v) for v in d['channels']]
    if mask.sum()<40:return None
    arr=x[mask][:,[ch.index(v) for v in CHANNELS],:]
    def bank(start_ms,n):
        bins=[];hits=np.zeros(len(t),int)
        for j in range(n):
            lo=start_ms+50*j;hi=lo+50; sel=(t>=lo/1000.-1e-10)&(t<hi/1000.-1e-10);hits+=sel.astype(int);bins.append(arr[:,:,sel].mean(axis=(0,2)))
        assert np.all(hits<=1) and np.all(hits[(t>=start_ms/1000.-1e-10)&(t<(start_ms+50*n)/1000.-1e-10)]==1)
        return np.concatenate(bins)
    return bank(0,8),bank(-200,4)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--smoke',action='store_true');args=ap.parse_args();assert os.getenv('SLURM_JOB_ID'),'Slurm required'
    cfg=json.loads((BASE/'configs/phase3_science_v1.json').read_text());h=cfg['ha']
    if args.smoke:
        rng=np.random.default_rng(cfg['seed']);X=rng.normal(size=(40,6));y=X[:,0]*2+rng.normal(size=40);hh=dict(h,outer_repeats=2,outer_folds=4,inner_folds=3);fs=splits(len(y),hh,cfg['seed']);p,a=nested(X,y,hh,fs,'MUSS');one=fs[:1];te=one[0][3];y2=y.copy();y2[te]+=1e6;p2,a2=nested(X,y2,hh,one,'MUSS',False);assert np.allclose(p[0,te],p2[0,te]) and np.isfinite(p).all() and all(not set(x['train_indices'])&set(x['test_indices']) for x in a);print(json.dumps({'job_id':os.environ['SLURM_JOB_ID'],'status':'smoke_pass','outer_predictions':int(np.isfinite(p).sum()),'folds_recorded':len(a),'heldout_label_invariance':True}));return
    out=BASE/'results/phase3_ha_science_001';priv=BASE/'private/phase3_ha_science_001';out.mkdir(exist_ok=False,parents=True);priv.mkdir(exist_ok=False,parents=True,mode=0o700)
    cov=pd.read_csv(BASE/'private/phase3_ha_covariates_004/candidate_covariates.csv');elig=pd.read_csv(BASE/'results/phase2_archival_001/candidate_eligibility.csv');elig=elig[elig.eligible.astype(str).str.lower()=='true'];
    assert len(elig)==53 and elig[['participant_id','recording_id']].duplicated().sum()==0 and elig.participant_id.nunique()==53
    cov=cov.merge(elig[['participant_id','recording_id']],on=['participant_id','recording_id'],validate='one_to_one');assert len(cov)==53
    missing_pta_reasons={str(k):int(v) for k,v in cov.loc[cov.pta_status!='linked_complete_unaided','pta_status'].value_counts().items()};cov=cov[cov.pta_status=='linked_complete_unaided'].copy();assert len(cov)==50 and cov.participant_id.nunique()==50
    f=pd.read_csv(BASE/'results/phase2_measurements_001/features.csv');fixed=f[(f.variant=='hp01_avg20')&(f.condition=='code1')&(f.measurement_status=='measured')][['participant_id','recording_id','mean_uv']];df=cov.merge(fixed,on=['participant_id','recording_id'],validate='one_to_one');assert len(df)==50
    post=[];pre=[];keep=[]
    for i,r in df.iterrows():
        z=bin_features(r.recording_id,'phase1_epochs_001')
        if z is not None:keep.append(i);post.append(z[0]);pre.append(z[1])
    df=df.loc[keep].reset_index(drop=True);post=np.asarray(post);pre=np.asarray(pre);assert len(df)>=h['minimum_candidates']
    df['duration_log']=np.log1p(df.duration_months.astype(float));targets={'MUSS':df.MUSS.astype(float).to_numpy(),'age':df.clinical_age_months.astype(float).to_numpy(),'log_duration':df.duration_log.to_numpy()};folds=splits(len(df),h,cfg['seed']);models={};private=[];public=[]
    for target,y in targets.items():
        clinical=np.column_stack(([df.clinical_age_months,df.duration_log,df.better_unaided_pta] if target=='MUSS' else [df.duration_log,df.better_unaided_pta] if target=='age' else [df.clinical_age_months,df.better_unaided_pta])).astype(float)
        banks={'clinical':clinical,'clinical_plus_fixed_amplitude':np.c_[clinical,df.mean_uv.astype(float)],'clinical_plus_poststim_pattern':np.c_[clinical,post],'clinical_plus_prestim_pattern':np.c_[clinical,pre]}
        for name,X in banks.items():
            pred,alpha=nested(X,y,h,folds,target);loss=np.abs(pred-y[None,:]);models[(target,name)]={'loss':loss.mean(0),'pred':pred,'alpha':alpha};
            for si,(rep,fold,tr,te,inner) in enumerate(folds):
                for i in te:private.append({'participant_id':df.iloc[i].participant_id,'recording_id':df.iloc[i].recording_id,'target':target,'model':name,'repeat':rep,'fold':fold,'y':float(y[i]),'pred':float(pred[rep,i])})
    rng=np.random.default_rng(cfg['seed']+1)
    for (target,name),v in models.items():
        d=None;ci=None
        if name!='clinical':d=v['loss']-models[(target,'clinical')]['loss'];draw=rng.integers(len(d),size=(h['loss_bootstrap_repetitions'],len(d)));ci=[float(x) for x in np.quantile(d[draw].mean(1),[.025,.975])]
        allerr=(v['pred']-targets[target][None,:]);den=float(np.sum((targets[target]-targets[target].mean())**2));public.append({'target':target,'model':name,'n_candidates':len(df),'MAE':float(np.abs(allerr).mean()),'RMSE':float(np.sqrt(np.mean(allerr**2))),'R2':float(1-np.mean(np.sum(allerr**2,axis=1)/den)) if den>0 else None,'delta_vs_clinical':float(d.mean()) if d is not None else 0.0,'delta_CI_fixed_OOF_loss_bootstrap':ci,'alpha_counts':{str(k):int(vv) for k,vv in pd.Series([x['alpha'] for x in v['alpha']]).value_counts().items()}})
    pd.DataFrame(private).to_csv(priv/'predictions.csv',index=False);(priv/'fold_assignments.json').write_text(json.dumps({f'{t}:{m}':v['alpha'] for (t,m),v in models.items()},indent=2));
    for p in [BASE/'configs/phase3_science_v1.json',Path(__file__)]:shutil.copy2(p,priv/p.name)
    (out/'summary.json').write_text(json.dumps({'job_id':os.environ['SLURM_JOB_ID'],'status':'exploratory_completed','flow_53_eligible_to_50_pta_to_actual':len(df),'pta_missing_reason_counts':missing_pta_reasons,'targets_models':public,'folds_public':[{k:v for k,v in x.items() if k in ('repeat','outer_fold','alpha')} for x in models[('MUSS','clinical')]['alpha']],'config_sha256':hashlib.sha256((BASE/'configs/phase3_science_v1.json').read_bytes()).hexdigest(),'input_sha256':{str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [BASE/'results/phase2_archival_001/candidate_eligibility.csv',BASE/'private/phase3_ha_covariates_004/candidate_covariates.csv',BASE/'results/phase2_measurements_001/features.csv']}},indent=2))
if __name__=='__main__':main()
