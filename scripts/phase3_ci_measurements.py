"""Record-level CI/MFF reproducibility and time-blocked event discrimination.

Record summaries do not assert independent people, CI diagnosis or cortical origin.
"""
import argparse, json, os, shutil
from collections import Counter
from pathlib import Path
import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import roc_auc_score, balanced_accuracy_score
from phase1_prepare import readcsv, table
from phase1_epochs import digest
BASE=Path(__file__).resolve().parents[1]

def bins(x,t,start,end):
    boundaries=np.linspace(start,end,6);features=[];counts=[]
    for lo,hi in zip(boundaries[:-1],boundaries[1:]):
        mask=(t>=lo-1e-10)&(t<hi-1e-10)
        assert mask.any()
        counts.append(int(mask.sum()))
        features.append(x[:,:,mask].mean(axis=2))
    assert len(set(counts))==1 and sum(counts)==int(((t>=start-1e-10)&(t<end-1e-10)).sum())
    return np.concatenate(features,axis=1)

def half_metrics(x,samples,t,sf,minimum):
    out=[];selected=(t>=.05-1e-10)&(t<.25-1e-10)
    block=np.floor(samples/sf/30).astype(int)
    for split,group in [('alternating_30s_blocks',block%2),('early_late_time',(samples>(samples.min()+samples.max())/2).astype(int))]:
        a=np.flatnonzero(group==0);b=np.flatnonzero(group==1);n=min(len(a),len(b))
        row=dict(split=split,n_half_a=len(a),n_half_b=len(b),balanced_trials_per_half=n,status='insufficient_half_trials')
        if n>=minimum:
            # Evenly spaced selections preserve coverage without using amplitudes.
            a=a[np.linspace(0,len(a)-1,n).astype(int)];b=b[np.linspace(0,len(b)-1,n).astype(int)]
            wa=x[a].mean(axis=0);wb=x[b].mean(axis=0)
            aa=wa[:,selected].reshape(-1);bb=wb[:,selected].reshape(-1)
            row.update(status='measured',half_a_mean_uv=float(aa.mean()),half_b_mean_uv=float(bb.mean()),
                waveform_r=float(np.corrcoef(aa,bb)[0,1]) if min(np.std(aa),np.std(bb))>1e-12 else None,
                waveform_rmse_uv=float(np.sqrt(np.mean((aa-bb)**2))))
        out.append(row)
    return out

def decoding(x,codes,samples,t,sf,cfg,mid,variant):
    scores=[];foldrows=[];predrows=[]
    for dev in sorted(set(codes)-{'stad'}):
        sel=np.isin(codes,['stad',dev]);xx=x[sel];yy=(codes[sel]==dev).astype(int);ss=samples[sel]
        order=np.argsort(ss);xx=xx[order];yy=yy[order];ss=ss[order]
        if min(np.bincount(yy,minlength=2))<cfg['minimum_trials_per_code']:continue
        edges=np.linspace(ss.min(),ss.max()+1,cfg['decoder_folds']+1)
        plans=[]
        for fold,(lo,hi) in enumerate(zip(edges[:-1],edges[1:])):
            test=(ss>=lo)&(ss<hi);guard=cfg['decoder_training_embargo_s']*sf
            train=(ss<lo-guard)|(ss>=hi+guard)
            assert not np.any(train&test)
            train_counts=np.bincount(yy[train],minlength=2);test_counts=np.bincount(yy[test],minlength=2)
            plans.append((fold,train,test,train_counts,test_counts))
        for window,(start,end) in cfg['decoding_windows_s'].items():
            features=bins(xx,t,start,end);valid=[]
            for fold,tr,te,nt,nv in plans:
                row=dict(container_id=mid,variant=variant,deviant_literal_code=dev,window=window,fold=fold,
                    train_stad=int(nt[0]),train_deviant=int(nt[1]),test_stad=int(nv[0]),test_deviant=int(nv[1]),
                    status='insufficient_fold_class_support')
                if min(nt)>=10 and min(nv)>=5:
                    model=LinearDiscriminantAnalysis(solver='lsqr',shrinkage='auto').fit(features[tr],yy[tr])
                    decision=model.decision_function(features[te]);pred=model.predict(features[te])
                    auc=float(roc_auc_score(yy[te],decision));bac=float(balanced_accuracy_score(yy[te],pred))
                    row.update(status='measured',auc=auc,balanced_accuracy=bac);valid.append((auc,bac,int(te.sum())))
                    for sample,label,p in zip(ss[te],yy[te],decision):
                        predrows.append(dict(container_id=mid,variant=variant,deviant_literal_code=dev,window=window,fold=fold,sample_0based=int(sample),label=int(label),decision=float(p)))
                foldrows.append(row)
            scores.append(dict(container_id=mid,variant=variant,deviant_literal_code=dev,window=window,
                n_stad=int((yy==0).sum()),n_deviant=int((yy==1).sum()),valid_folds=len(valid),
                status='all_folds_measured' if len(valid)==cfg['decoder_folds'] else 'incomplete_fold_support',
                mean_fold_auc=float(np.mean([v[0] for v in valid])) if valid else None,
                mean_fold_balanced_accuracy=float(np.mean([v[1] for v in valid])) if valid else None))
    return scores,foldrows,predrows

def main():
    assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    ap=argparse.ArgumentParser();ap.add_argument('--smoke',action='store_true');a=ap.parse_args()
    cfgpath=BASE/'configs/phase3_science_v1.json';cfg=json.loads(cfgpath.read_text())['ci']
    source=BASE/'results'/('phase3_ci_smoke_001' if a.smoke else 'phase3_ci_epochs_001')
    out=BASE/'results'/('phase3_ci_measurements_smoke_001' if a.smoke else 'phase3_ci_measurements_001');out.mkdir(exist_ok=False)
    priv=BASE/'private'/out.name;priv.mkdir(mode=0o700,exist_ok=False)
    manifests=readcsv(BASE/'results/phase3_ci_sources_001/source_manifest.csv');expected={r['container_id'] for r in manifests if r['source_status']=='eligible'}
    found={p.parent.name for p in source.glob('M*/summary.json')}
    if not a.smoke:assert found==expected,(len(found),len(expected))
    features=[];halves=[];scores=[];folds=[];predictions=[];records=[]
    for mid in sorted(found):
        folder=source/mid;summary=json.loads((folder/'summary.json').read_text());records.append(summary)
        assert summary['config_sha256']==digest(cfgpath)
        assert summary['epoch_data_sha256']==digest(folder/'epochs_roi.npz')
        with np.load(folder/'epochs_roi.npz',allow_pickle=False) as d:
            x=d['roi_uv'].astype(float);t=d['times_s'];codes=d['event_codes'];samples=d['samples_0based'];accepted=d['accepted'];sf=float(d['sfreq'])
        assert np.isfinite(x).all() and accepted.shape==(len(x),2) and np.all(~accepted[:,1]|accepted[:,0])
        assert len(x)==summary['stored_epochs'] and int(accepted[:,0].sum())==summary['primary_retained']
        ledger=readcsv(folder/'epoch_ledger.csv');assert len(ledger)==summary['target_annotations']
        assert sum(r['roi_epoch_index']!='' for r in ledger)==len(x)
        for col,variant in enumerate(['primary','strict']):
            mask=accepted[:,col];xx=x[mask];cc=codes[mask];ss=samples[mask]
            for code in sorted(set(cc)):
                use=cc==code;n=int(use.sum());wave=xx[use].mean(axis=0)
                f=dict(container_id=mid,variant=variant,event_code=code,n_trials=n,status='measured' if n>=cfg['minimum_trials_per_code'] else 'insufficient_trials')
                for label,start,end in [('main',.05,.25),('late',.25,.4)]:
                    sel=(t>=start-1e-10)&(t<end-1e-10);f[label+'_mean_uv']=float(wave[:,sel].mean())
                features.append(f)
                if n>=cfg['minimum_trials_per_code']:
                    halves.extend(dict(container_id=mid,variant=variant,event_code=code,**v) for v in half_metrics(xx[use],ss[use],t,sf,cfg['minimum_trials_per_code_each_half']))
            if 'stad' in cc:
                ds,df,dp=decoding(xx,cc,ss,t,sf,cfg,mid,variant);scores+=ds;folds+=df;predictions+=dp
        print(json.dumps(dict(container_id=mid,accepted=summary['primary_retained'])),flush=True)
    for name,data in [('features',features),('half_scores',halves),('decoder_scores',scores),('decoder_folds',folds)]:table(out/(name+'.csv'),data)
    table(priv/'decoder_predictions.csv',predictions)
    def stats(values):
        z=np.array([v for v in values if v is not None and np.isfinite(v)],float)
        return dict(n=len(z),median=float(np.median(z)) if len(z) else None,q25=float(np.quantile(z,.25)) if len(z) else None,q75=float(np.quantile(z,.75)) if len(z) else None)
    reliability={}
    for variant in ['primary','strict']:
        for split in ['alternating_30s_blocks','early_late_time']:
            for code in cfg['event_codes']:
                reliability[f'{variant}/{split}/{code}']=stats([r.get('waveform_r') for r in halves if r['variant']==variant and r['split']==split and r['event_code']==code and r['status']=='measured'])
    decoding_summary={}
    for variant in ['primary','strict']:
        for dev in cfg['event_codes'][1:]:
            for window in cfg['decoding_windows_s']:
                decoding_summary[f'{variant}/{dev}/{window}']=stats([r['mean_fold_auc'] for r in scores if r['variant']==variant and r['deviant_literal_code']==dev and r['window']==window and r['status']=='all_folds_measured'])
    summary=dict(job_id=os.environ['SLURM_JOB_ID'],config_sha256=digest(cfgpath),records=len(records),target_annotations=sum(r['target_annotations'] for r in records),stored_epochs=sum(r['stored_epochs'] for r in records),primary_retained=sum(r['primary_retained'] for r in records),strict_retained=sum(r['strict_retained'] for r in records),record_channel_gate_pass=sum(r['record_channel_gate'] for r in records),roi_channel_gate_pass=sum(r['roi_channel_gate'] for r in records),decoder_status_counts=dict(Counter(r['variant']+'/'+r['window']+'/'+r['status'] for r in scores)),reliability_record_level=reliability,decoding_record_level=decoding_summary,scope='MFF source records including unresolved cohort/identity; no independent-child or cortical claim',verification='all epoch arrays finite, manifest coverage, hashes and ledgers reconciled')
    for p in [Path(__file__),cfgpath]:shutil.copy2(p,out/p.name)
    (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if not isinstance(v,dict)},indent=2))
if __name__=='__main__':main()
