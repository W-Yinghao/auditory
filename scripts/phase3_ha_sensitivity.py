#!/usr/bin/env python3
"""Post-v1, single prespecified HA penalty sensitivity check."""
import argparse,hashlib,json,os,shutil
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from phase3_ha_science import BASE,CHANNELS,bin_features,splits

def fit_scaled(C,E,y,train,test,ac,ae):
    sc=StandardScaler().fit(C[train]);zc=sc.transform(C[train]);zt=sc.transform(C[test])
    blocks=[zc/np.sqrt(ac)];tests=[zt/np.sqrt(ac)]
    if ae is not None:
        se=StandardScaler().fit(E[train]);blocks.append(se.transform(E[train])/np.sqrt(ae));tests.append(se.transform(E[test])/np.sqrt(ae))
    m=Ridge(alpha=1.0).fit(np.c_[*blocks],y[train]);return m.predict(np.c_[*tests])
def nested_sep(C,E,y,h,folds,target,require_complete=True):
    pred=np.full((max(x[0] for x in folds)+1,len(y)),np.nan);chosen=[]
    pairs=[(float(a),float(e)) for a in h['alpha_clinical'] for e in h['alpha_eeg'][:-1]]+[(float(a),None) for a in h['alpha_clinical']]
    for rep,fold,tr,te,inner in folds:
        best=None
        for ac,ae in pairs:
            vals=[]
            for a,b in inner:
                pp=fit_scaled(C,E,y,a,b,ac,ae);pp=np.clip(pp,*h['prediction_clip']);vals.append(float(np.mean(abs(y[b]-pp))))
            cand=(float(np.mean(vals)),ac,ae)
            key=(cand[0],ac,float('inf') if ae is None else ae)
            if best is None or key<best_key:best=cand;best_key=key
        pp=fit_scaled(C,E,y,tr,te,best[1],best[2]);pp=np.clip(pp,*h['prediction_clip']);pred[rep,te]=pp
        chosen.append({'repeat':int(rep),'outer_fold':int(fold),'alpha_clinical':best[1],'alpha_eeg':('infinity_null_eeg' if best[2] is None else best[2]),'train_indices':[int(x) for x in tr],'test_indices':[int(x) for x in te]})
    if require_complete:assert np.isfinite(pred).all()
    return pred,chosen
def nested_single(C,y,h,folds,target):
    E=np.zeros((len(y),0));return nested_sep(C,E,y,dict(h,alpha_eeg=['infinity_null_eeg']),folds,target)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--smoke',action='store_true');args=ap.parse_args();assert os.getenv('SLURM_JOB_ID'),'Slurm required'
    cfg=json.loads((BASE/'configs/phase3_science_v1.json').read_text());h=dict(cfg['ha'],**json.loads((BASE/'configs/phase3_ha_sensitivity_v1.json').read_text()));
    if args.smoke:
        rng=np.random.default_rng(9);C=rng.normal(size=(24,3));E=rng.normal(size=(24,5));y=C[:,0]+E[:,0];hh=dict(h,outer_repeats=2,outer_folds=3,inner_folds=2);fs=splits(len(y),hh,cfg['seed']);p,ch=nested_sep(C,E,y,hh,fs,'MUSS');p2,_=nested_sep(C,E,y+0,hh,fs,'MUSS');assert np.allclose(p,p2)
        one=fs[:1];te=one[0][3];yy=y.copy();yy[te]+=1e6;q,_=nested_sep(C,E,yy,hh,one,'MUSS',False);assert np.allclose(p[0,te],q[0,te]);
        sc=StandardScaler().fit(C);se=StandardScaler().fit(E);m1=Ridge(alpha=1).fit(np.c_[sc.transform(C),se.transform(E)],y);m2=Ridge(alpha=1).fit(np.c_[sc.transform(C)/1,se.transform(E)/1],y);assert np.allclose(m1.predict(np.c_[sc.transform(C),se.transform(E)]),m2.predict(np.c_[sc.transform(C),se.transform(E)]));
        null,_=nested_sep(C,E,y,dict(h,alpha_clinical=[1.0],alpha_eeg=['infinity_null_eeg']),fs,'MUSS');single,_=nested_single(C,y,dict(h,alpha_clinical=[1.0]),fs,'MUSS');assert np.allclose(null,single);print(json.dumps({'job_id':os.environ['SLURM_JOB_ID'],'status':'smoke_pass','heldout_label_invariance':True,'one_penalty_equivalence':True,'infinity_eeg_null_equivalence':True}));return
    out=BASE/'results/phase3_ha_sensitivity_001';priv=BASE/'private/phase3_ha_sensitivity_001';out.mkdir(exist_ok=False,parents=True);priv.mkdir(exist_ok=False,parents=True,mode=0o700)
    cov=pd.read_csv(BASE/'private/phase3_ha_covariates_004/candidate_covariates.csv');elig=pd.read_csv(BASE/'results/phase2_archival_001/candidate_eligibility.csv');elig=elig[elig.eligible.astype(str).str.lower()=='true'];assert len(elig)==53
    cov=cov.merge(elig[['participant_id','recording_id']],on=['participant_id','recording_id'],validate='one_to_one');cov=cov[cov.pta_status=='linked_complete_unaided'].copy();assert len(cov)==50
    f=pd.read_csv(BASE/'results/phase2_measurements_001/features.csv');fixed=f[(f.variant=='hp01_avg20')&(f.condition=='code1')&(f.measurement_status=='measured')][['participant_id','recording_id','mean_uv']];df=cov.merge(fixed,on=['participant_id','recording_id'],validate='one_to_one');assert len(df)==50
    post=[];pre=[];keep=[]
    for i,r in df.iterrows():
        z=bin_features(r.recording_id,'phase1_epochs_001')
        if z is not None:keep.append(i);post.append(z[0]);pre.append(z[1])
    df=df.loc[keep].reset_index(drop=True);post=np.asarray(post);pre=np.asarray(pre);assert len(df)==50 and df.participant_id.nunique()==50;df['duration_log']=np.log1p(df.duration_months.astype(float));y=df.MUSS.astype(float).to_numpy();C=np.c_[df.clinical_age_months,df.duration_log,df.better_unaided_pta].astype(float);folds=splits(len(df),h,cfg['seed']);models={'clinical_age_duration':(np.c_[C[:,0],C[:,1]],None),'clinical_v1_pta':(C,None),'post_separate_penalty':(C,post),'pre_separate_penalty':(C,pre)};results={};private=[]
    for name,(cc,ee) in models.items():
        if ee is None:pred,ch=nested_single(cc,y,h,folds,'MUSS')
        else:pred,ch=nested_sep(cc,ee,y,h,folds,'MUSS')
        results[name]={'pred':pred,'loss':np.abs(pred-y[None,:]).mean(0),'chosen':ch}
        for si,(rep,fold,tr,te,inner) in enumerate(folds):
            for i in te:private.append({'participant_id':df.iloc[i].participant_id,'recording_id':df.iloc[i].recording_id,'model':name,'repeat':rep,'fold':fold,'y':float(y[i]),'pred':float(pred[rep,i])})
    old=pd.read_csv(BASE/'private/phase3_ha_science_001/predictions.csv')
    old=old[(old.target=='MUSS')&(old.model=='clinical')]
    new=pd.DataFrame(private);new=new[new.model=='clinical_v1_pta']
    check=new.merge(old,on=['participant_id','recording_id','repeat','fold'],validate='one_to_one',suffixes=('_new','_old'))
    assert len(check)==250 and np.allclose(check.pred_new,check.pred_old,atol=1e-8) and np.array_equal(check.y_new,check.y_old)
    rng=np.random.default_rng(cfg['seed']+1);public=[]
    for name,v in results.items():
        err=v['pred']-y[None,:];d=v['loss']-results['clinical_v1_pta']['loss'];draw=rng.integers(len(d),size=(h['loss_bootstrap_repetitions'],len(d)));public.append({'model':name,'n_candidates':len(df),'MAE':float(np.abs(err).mean()),'RMSE':float(np.sqrt(np.mean(err**2))),'delta_vs_v1_clinical':float(d.mean()),'delta_CI_fixed_OOF_loss_bootstrap':[float(z) for z in np.quantile(d[draw].mean(1),[.025,.975])],'alpha_pairs':[{'alpha_clinical':x['alpha_clinical'],'alpha_eeg':x['alpha_eeg']} for x in v['chosen']]})
    pd.DataFrame(private).to_csv(priv/'predictions.csv',index=False);(priv/'chosen_pairs.json').write_text(json.dumps({k:v['chosen'] for k,v in results.items()},indent=2));
    for p in [Path(__file__),BASE/'configs/phase3_ha_sensitivity_v1.json',BASE/'docs/PHASE3_HA_SENSITIVITY_PROTOCOL.md']:shutil.copy2(p,priv/p.name)
    (out/'summary.json').write_text(json.dumps({'job_id':os.environ['SLURM_JOB_ID'],'status':'exploratory_sensitivity_completed','same_v1_folds_seed':True,'n_candidates':len(df),'models':public,'config_sha256':hashlib.sha256((BASE/'configs/phase3_ha_sensitivity_v1.json').read_bytes()).hexdigest()},indent=2))
if __name__=='__main__':main()
