"""Subsequent quality decomposition, nonlinear EEG and mixed-archive tests."""
import argparse
import contextlib
import json
import os
import shutil
import time
import traceback
import numpy as np
import pandas as pd
from .extended import ROOT,Counter,dump,sha,options,repeated_interval
from auditory_fseries.models import clinical_block,standardize,fit_predict,make_splits,set_recorder


def kernel_predict(C,Z,y,tr,te,candidate,bounds,counter):
    family,ac,az,bank=candidate
    if az is None:
        p,state=fit_predict(C,np.zeros((len(y),0)),np.zeros((len(y),0)),y,tr,te,
            (family,ac,None,False,False),0,bounds)
        return p,state
    counter(dict(kernel_candidate=list(candidate),train_n=len(tr),test_n=len(te)))
    c,ct,cstate=clinical_block(C[tr],C[te],family=='quadratic')
    z,zt,zstate=standardize(Z[tr],Z[te])
    def dist(a,b):
        return np.maximum(np.sum(a*a,axis=1)[:,None]+np.sum(b*b,axis=1)[None,:]-2*a@b.T,0)
    d=dist(z,z);positive=d[np.triu_indices(len(tr),1)];positive=positive[positive>1e-12]
    bandwidth=float(np.median(positive)) if len(positive) else 1.
    k=np.exp(-d/bandwidth);kt=np.exp(-dist(zt,z)/bandwidth)
    mean_columns=k.mean(axis=0);grand=float(k.mean())
    kc=k-k.mean(axis=1)[:,None]-mean_columns[None,:]+grand
    ktc=kt-kt.mean(axis=1)[:,None]-mean_columns[None,:]+grand
    total=c@c.T/ac+kc/az;cross=ct@c.T/ac+ktc/az
    center=float(y[tr].mean());weights=np.linalg.solve(total+np.eye(len(tr)),y[tr]-center)
    pred=np.clip(center+cross@weights,*bounds)
    assert np.isfinite(pred).all()
    return pred,dict(candidate=candidate,clinical=cstate,eeg=zstate,bandwidth=bandwidth,
        kernel_column_mean=mean_columns,kernel_grand_mean=grand,dual_weights=weights,training_indices=tr,intercept=center)


def select_fit(tr,te,inner,choices,predict,y):
    cache={}
    def call(a,b,c):
        key=(tuple(a),tuple(b),tuple(c))
        if key not in cache:cache[key]=predict(a,b,c)
        return cache[key]
    risks=[sum(np.abs(y[b]-call(a,b,c)[0]).sum() for a,b in inner)/len(tr) for c in choices]
    choice=choices[int(np.argmin(risks))]
    p,state=call(tr,te,choice)
    return p,dict(choice=choice,inner_MAE=float(min(risks)),state=state)


def quality(private,public,config,counter):
    source=ROOT/'private/auditory_repair/ha_prepare_001'
    ready=json.loads((source/'completion.json').read_text());assert sha(source/'data.npz')==ready['data_sha256']
    with np.load(source/'data.npz',allow_pickle=False) as a:data={k:a[k] for k in a.files}
    n=len(data['groups']);effects=[];metrics=[];all_predictions=[]
    for task in ['A','V_given_A']:
        y=data['A' if task=='A' else 'V'];C=data['C'] if task=='A' else np.c_[data['C'],data['A']]
        with np.load(ROOT/f'private/auditory_repair/ha_extended_001/{task}_complete_oof.npz') as old:
            assert np.array_equal(old['y'],y)
            prediction={model:old[model] for model in ['C_BEST','BEST_CZ','C_Q','BEST_CQZ']}
        for name in ['TECH_Q','TECH_QZ','AMP_Q','AMP_QZ','KERNEL_CZ']:
            prediction[name]=np.full((config['outer_repeats'],n),np.nan)
        for repeat in range(config['outer_repeats']):
            splits=make_splits(data['groups'],{'validation':dict(outer_folds=5,inner_folds=3,seed=config['seed']+repeat)})
            for fold,(tr,te,inner) in enumerate(splits):
                for label,cols in [('TECH',[0,1,3,4,5]),('AMP',[2])]:
                    Q=data['Q'][:,cols]
                    choices=list(dict.fromkeys(options(config,quality=True)+[c for b in config['banks'] for c in options(config,b,quality=True)]))
                    cache={}
                    def pred(a,b,choice):
                        key=(tuple(a),tuple(b),choice)
                        if key not in cache:
                            *head,bank=choice
                            cache[key]=fit_predict(C,Q,data[bank] if bank else np.zeros((n,0)),y,a,b,tuple(head),config['seed']+repeat,config['target_bounds'][task])
                        return cache[key]
                    for model,grid in [(label+'_Q',options(config,quality=True)),(label+'_QZ',choices)]:
                        p,state=select_fit(tr,te,inner,grid,pred,y);prediction[model][repeat,te]=p
                        dump(private/f'{task}_r{repeat}_f{fold}_{model}.json',state)
                choices=[(f,a,None,None) for f in config['clinical_families'] for a in config['clinical_alphas']]
                choices += [(f,a,z,b) for f in config['clinical_families'] for a in config['clinical_alphas'] for z in [.01,.1,1.,10.] for b in config['banks']]
                def pred_kernel(a,b,c):
                    return kernel_predict(C,data[c[3]] if c[3] else np.zeros((n,0)),y,a,b,c,config['target_bounds'][task],counter)
                p,state=select_fit(tr,te,inner,choices,pred_kernel,y);prediction['KERNEL_CZ'][repeat,te]=p
                dump(private/f'{task}_r{repeat}_f{fold}_KERNEL_CZ.json',state)
            print(json.dumps(dict(task=task,repeat=repeat,fit_attempts=counter.n)),flush=True)
        assert all(np.isfinite(v).all() for v in prediction.values())
        contrasts=[('technical_adjusted','TECH_Q','TECH_QZ'),('amplitude_adjusted','AMP_Q','AMP_QZ'),('full_quality','C_Q','BEST_CQZ'),
            ('kernel_vs_clinical','C_BEST','KERNEL_CZ'),('kernel_vs_linear_EEG','BEST_CZ','KERNEL_CZ'),
            ('technical_vs_clinical','C_BEST','TECH_Q'),('amplitude_vs_clinical','C_BEST','AMP_Q')]
        for label,a,b in contrasts:
            d=np.abs(prediction[a]-y)-np.abs(prediction[b]-y)
            effects.append(dict(task=task,contrast=label,baseline=a,augmented=b,**repeated_interval(d,2000,9127)))
        for model,p in prediction.items():
            metrics.append(dict(task=task,model=model,n=n,MAE=float(np.abs(p-y).mean())))
            for repeat in range(5):
                for i in range(n):all_predictions.append(dict(task=task,model=model,repeat=repeat,group=data['groups'][i],y=float(y[i]),prediction=float(p[repeat,i])))
        np.savez(private/f'{task}_complete_oof.npz',y=y,**prediction)
    pd.DataFrame(all_predictions).to_csv(private/'predictions.csv',index=False)
    pd.DataFrame(metrics).to_csv(public/'metrics.csv',index=False);dump(public/'effects.json',effects)
    return dict(status='COMPLETE',n=n,fit_attempts=counter.n,tasks=['A','V_given_A'],subsequent_exploration=True)


def mixed_predict(C,Q,Z,y,tr,te,candidate,seed,bounds):
    # Missing EEG statistics are fitted inside the exact inner/outer training
    # partition; the augmented availability indicators are also shuffled.
    a,b,state=clinical_block(Z[tr],Z[te])
    z=np.zeros((len(y),a.shape[1]));z[tr]=a;z[te]=b
    p,model=fit_predict(C,Q,z,y,tr,te,candidate,seed,bounds)
    model['eeg_missing_transform']=state
    return p,model


def ci(private,public,config,counter,input_run):
    folder=ROOT/'private/results/auditory_repair'/input_run
    with np.load(folder/'data.npz',allow_pickle=False) as z:raw={k:z[k] for k in z.files}
    frame=pd.read_csv(folder/'cohort.csv').fillna('unknown')
    assert np.array_equal(frame.candidate_group.to_numpy(str),raw['groups'])
    categories=pd.get_dummies(frame[['source_label','protocol_task']],dtype=float).to_numpy()
    clinical=np.c_[raw['C'],categories]
    # Technical metadata excludes waveform correlation/RMSE, which can carry biology.
    technical=raw['Q'][:,[0,1,6,7,8,9,10]]
    metrics=[];effects=[];predictions=[];support=[]
    for task in ['A','V','CAP','SIR']:
        mask=raw[task+'_valid'].astype(bool)&np.isfinite(raw[task])
        ids=raw['groups'][mask];y=raw[task][mask];C=np.c_[clinical[mask],technical[mask]];Q=raw['Q'][mask];Z=raw['Z'][mask]
        assert len(set(ids))==len(ids)
        n=len(y);bounds=config['target_bounds'][task]
        assert n>=10 and np.all((y>=bounds[0])&(y<=bounds[1]))
        counts=frame.loc[mask,'source_label'].value_counts().to_dict()
        support.append(dict(task=task,n=n,source_labels=counts,finite_age_count=int(np.isfinite(raw['C'][mask,0]).sum())))
        oof={name:np.full((5,n),np.nan) for name in ['MEAN','SOURCE_TECH','SOURCE_TECH_Z','SOURCE_TECH_SHUFFLE','ALL_Q','ALL_Q_Z','Z_ONLY']}
        for repeat in range(5):
            cfg={'validation':dict(outer_folds=5,inner_folds=3,seed=config['seed']+repeat)}
            splits=make_splits(ids,cfg)
            for fold,(tr,te,inner) in enumerate(splits):
                cache={}
                def pred(a,b,c):
                    key=(tuple(a),tuple(b),tuple(c))
                    if key not in cache:cache[key]=mixed_predict(C,Q,Z,y,a,b,tuple(c),config['seed']+repeat,bounds)
                    return cache[key]
                grids={}
                for name,q,shuffle in [('SOURCE_TECH_Z',False,False),('SOURCE_TECH_SHUFFLE',False,True),('ALL_Q_Z',True,False)]:
                    grids[name]=[c[:5] for c in options(config,'Z',quality=q,shuffled=shuffle)]
                grids['SOURCE_TECH']=[c[:5] for c in options(config)]
                grids['ALL_Q']=[c[:5] for c in options(config,quality=True)]
                grids['Z_ONLY']=[c[:5] for c in options(config,'Z',clinical=False)]
                oof['MEAN'][repeat,te]=np.clip(y[tr].mean(),*bounds)
                saved={}
                for model,choices in grids.items():
                    p,state=select_fit(tr,te,inner,choices,pred,y);oof[model][repeat,te]=p;saved[model]=state
                dump(private/f'{task}_r{repeat}_f{fold}.json',saved)
        assert all(np.isfinite(p).all() for p in oof.values())
        for model,p in oof.items():
            metrics.append(dict(task=task,model=model,n=n,MAE=float(np.abs(p-y).mean()),RMSE=float(np.sqrt(np.mean((p-y)**2)))))
            for repeat in range(5):
                for i in range(n):predictions.append(dict(task=task,model=model,repeat=repeat,group=ids[i],y=float(y[i]),prediction=float(p[repeat,i])))
        for label,a,b in [('source_technical_increment','SOURCE_TECH','SOURCE_TECH_Z'),('content','SOURCE_TECH_SHUFFLE','SOURCE_TECH_Z'),
            ('full_quality_increment','ALL_Q','ALL_Q_Z'),('EEG_alone','MEAN','Z_ONLY')]:
            effects.append(dict(task=task,contrast=label,**repeated_interval(np.abs(oof[a]-y)-np.abs(oof[b]-y),2000,9127)))
        np.savez(private/f'{task}_complete_oof.npz',groups=ids,y=y,**oof)
        print(json.dumps(dict(task=task,n=n,fit_attempts=counter.n)),flush=True)
    pd.DataFrame(predictions).to_csv(private/'predictions.csv',index=False);pd.DataFrame(metrics).to_csv(public/'metrics.csv',index=False)
    dump(public/'effects.json',effects);dump(public/'target_support.json',support)
    dump(private/'input_binding.json',dict(run=input_run,data_sha256=sha(folder/'data.npz'),cohort_sha256=sha(folder/'cohort.csv')))
    return dict(status='COMPLETE_MIXED_MFF_ARCHIVAL',fit_attempts=counter.n,not_CI_only=True,clinical_validity_unconfirmed=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['test','quality','ci']);parser.add_argument('--run',required=True);parser.add_argument('--input-run');args=parser.parse_args()
    if not os.environ.get('SLURM_JOB_ID'):raise RuntimeError('SLURM_REQUIRED')
    os.umask(0o077);private=ROOT/'private/auditory_repair'/args.run;public=ROOT/'results/auditory_repair'/args.run
    private.mkdir(mode=0o700);public.mkdir(mode=0o700);config=json.loads((ROOT/'configs/auditory_repair_v2.json').read_text())
    hashes={}
    for path in [*sorted((ROOT/'auditory_repair').glob('*.py')),ROOT/'auditory_fseries/models.py',ROOT/'configs/auditory_repair_v2.json',ROOT/'docs/auditory_repair/FOLLOWUP_ADDENDUM.md',ROOT/'tests/auditory_repair/test_followups.py']:
        rel=path.relative_to(ROOT);dest=private/'source'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest);hashes[str(rel)]=sha(path)
    start=dict(job_id=os.environ['SLURM_JOB_ID'],command=args.command,arguments=vars(args),source_hashes=hashes,start_unix=time.time());dump(private/'start.json',start)
    counter=Counter(private,1000 if args.command=='test' else 80000 if args.command=='quality' else 40000);set_recorder(counter)
    try:
        if args.command=='test':
            import pytest
            with (private/'pytest.log').open('w') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                rc=pytest.main(['-q','-p','no:cacheprovider','--import-mode=importlib','--basetemp='+str(private/'tmp'),'tests/auditory_repair/test_followups.py'])
            result=dict(status='PASS' if rc==0 else 'FAIL',fit_attempts=counter.n)
        else:
            tested=ROOT/'private/auditory_repair/followup_tests_001'
            assert json.loads((tested/'completion.json').read_text())['status']=='PASS'
            tested_hash=json.loads((tested/'start.json').read_text())['source_hashes']
            for rel in ['auditory_repair/followups.py','auditory_fseries/models.py']:
                assert tested_hash[rel]==hashes[rel]
            result=quality(private,public,config,counter) if args.command=='quality' else ci(private,public,config,counter,args.input_run)
        counter.handle.flush();result.update(job_id=start['job_id'],elapsed_seconds=time.time()-start['start_unix'])
        dump(private/'completion.json',result);dump(public/'summary.json',result);print(json.dumps(result),flush=True)
        return 0 if result['status']!='FAIL' else 1
    except Exception:
        counter.handle.flush();dump(private/'failure.json',dict(traceback=traceback.format_exc(),fit_attempts=counter.n));dump(public/'failure.json',dict(status='FAILED',fit_attempts=counter.n));return 1
    finally:counter.handle.close()


if __name__=='__main__':raise SystemExit(main())
