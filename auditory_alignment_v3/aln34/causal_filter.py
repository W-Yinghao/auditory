"""Native DTU filter sensitivity; independent CPU execution, no legacy mutations."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
from datetime import datetime
import gc
import hashlib
import json
import os
from pathlib import Path
import time

import h5py
import numpy as np
from scipy.signal import butter, sosfilt, sosfiltfilt, sosfreqz

from auditory_alignment import data as D
from .. import sci_r2 as S
from ..sci_r1 import stats as ST

ROOT = Path(D.REPO)
BASE = ROOT/'private/auditory_alignment_v3/aln34/causal_filter_v1'
STORE = Path(D.PUB)/'derived/aln34_dtu_filter_v1'
NOTE = ROOT/'private/auditory_alignment_v3/aln34/CAUSAL_FILTER_DESIGN_20261017.md'
PLAN = BASE/'plan.json'
VARIANTS = ('zero_phase', 'causal_cascade')
LAGS = (-200, 0, 200, 400, 600)
GUARDS = (.5, 2.)


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda: f.read(8*1024*1024), b''): h.update(block)
    return h.hexdigest()


def clean(x):
    if isinstance(x, np.ndarray): return clean(x.tolist())
    if isinstance(x, np.generic): return clean(x.item())
    if isinstance(x, dict): return {k: clean(v) for k,v in x.items() if k != 'T'}
    if isinstance(x, (tuple,list)): return [clean(v) for v in x]
    if isinstance(x, float) and not np.isfinite(x): return None
    return x


def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name(path.name+'.tmp')
    tmp.write_text(json.dumps(clean(value), indent=2, sort_keys=True, allow_nan=False)+'\n')
    os.replace(tmp,path)


def read(p): return json.loads(Path(p).read_text())
def now(): return datetime.now().astimezone().isoformat()
def text(x): return x.decode() if isinstance(x,bytes) else str(x)


def sources():
    return {str(p.relative_to(ROOT)): sha(p) for p in (Path(__file__), NOTE, Path(D.__file__), Path(S.__file__), Path(ST.__file__))}


def native_stride(fs):
    stride = int(round(fs/128))
    if stride < 1 or abs(fs/128-stride) > 1e-10:
        raise ValueError('native sample rate is not an exact multiple of128Hz')
    return stride


def filters(fs): return butter(4, [1.,20.], btype='bandpass', fs=fs, output='sos')


def eeg_channels(channels):
    # The legacy loader explicitly uses eeg_1_20[:64]. Stage-A metadata can
    # also label Biosemi EXG rows as EEG; preserve exactly that first64 access.
    names=[text(c) for c in channels]
    assert len(names)>=64 and len(set(names[:64]))==64
    return names[:64]


def apply_filter(x, sos, variant):
    if variant == 'causal_cascade': return sosfilt(sos, sosfilt(sos,x,axis=-1), axis=-1)
    if variant == 'zero_phase': return sosfiltfilt(sos,x,axis=-1)
    raise ValueError(variant)


def anchor_offsets(fs=128):
    t = np.arange(round(.5*fs), round(4*fs)+1, round(.25*fs))
    w = round(.02*fs)
    assert t[0]+round(min(LAGS)*fs/1000) >= 0
    assert t[-1]+round(max(LAGS)*fs/1000)+w <= round(5*fs)
    return t


def keep_anchors(start, bounds, guard, fs=128):
    t = anchor_offsets(fs)
    lo,hi = bounds
    # Apply the same full-window bounds for all lag cells, not a lag-specific n.
    a = start+t+round(min(LAGS)*fs/1000)
    b = start+t+round(max(LAGS)*fs/1000)+round(.02*fs)
    return t[(a >= lo+round(guard*fs)) & (b <= hi-round(guard*fs))]


def register():
    rows=[]
    for p in sorted((ROOT/'private/auditory_c3/public/dtu_v2').glob('*.json')):
        old=Path(D.DTU_PRE)/(p.stem+'.h5')
        with h5py.File(old,'r') as f:
            raw=Path(D.PUB)/text(f.attrs['source'])
            channels=eeg_channels(f.attrs['channels'])
            recorded_channels=len(f.attrs['channels'])
            trials={k:{'n':int(f[k]['eeg_1_20'].shape[1]),'onset_s':float(f[k].attrs['onset_s']),
                       'end_s':float(f[k].attrs['end_s'])} for k in sorted(f)}
        stat=raw.stat()
        rows.append({'id':p.stem,'old':str(old),'old_sha256':sha(old),'raw':str(raw),
                     'raw_size':stat.st_size,'raw_mtime_ns':stat.st_mtime_ns,'channels':channels,
                     'recorded_channel_count':recorded_channels,'trials':trials})
    assert len(rows)==44,len(rows)
    plan={'version':'ALN34_DTU_FILTER_v1','created':now(),'recordings':rows,'tasks':[[sf,cf] for sf in range(5) for cf in range(2)],
          'sources':sources(),'store':str(STORE),'target_contract':'unchanged DTU Local envelope,128Hz; not causal audio',
          'normalization':'inherited whole-recording EEG, offline; not whole-pipeline causal'}
    if PLAN.exists():
        old=read(PLAN);assert all(old[k]==v for k,v in plan.items() if k!='created')
    else:
        write(PLAN,plan);PLAN.chmod(0o444)
    print('Registered44native recording pairs and10fold tasks',sha(PLAN),flush=True)


def verify(plan): assert plan['sources']==sources(),'frozen causal sensitivity source drift'


def cache_one(row, probe=False):
    import mne
    dest=STORE/('probes/'+os.environ['SLURM_JOB_ID'] if probe else 'production')
    receipt=dest/'receipts'/(row['id']+'.json')
    if receipt.exists():
        value=read(receipt)
        assert value['status']=='complete' and value['row']==row and value['sources']==sources() and value['probe']==probe
        for v in VARIANTS: assert sha(dest/v/(row['id']+'.h5'))==value['output_sha256'][v]
        return value
    started=time.time();p=Path(row['raw']);st=p.stat()
    assert st.st_size==row['raw_size'] and st.st_mtime_ns==row['raw_mtime_ns']
    assert sha(row['old'])==row['old_sha256']
    raw=mne.io.read_raw_bdf(p,preload=False,verbose=False);fs=float(raw.info['sfreq']);stride=native_stride(fs);sos=filters(fs)
    picks=[raw.ch_names.index(c) for c in row['channels']]
    assert len(set(picks))==64
    outputs={};files={};details=[]
    try:
        for v in VARIANTS:
            path=dest/v/(row['id']+'.h5');path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            outputs[v]=path;files[v]=h5py.File(str(path)+'.tmp','w')
        with h5py.File(row['old'],'r') as old:
            for f in files.values():
                for key,value in old.attrs.items(): f.attrs[key]=value
                f.attrs['new_filter_design_sha256']=sha(NOTE)
            names=sorted(row['trials'])[:1] if probe else sorted(row['trials'])
            for key in names:
                trial=row['trials'][key];a=round(trial['onset_s']*fs);b=round(trial['end_s']*fs)
                lo=max(0,a-round(20*fs));hi=min(raw.n_times,b+round(20*fs))
                x=raw.get_data(picks=picks,start=lo,stop=hi)*1e6
                assert np.isfinite(x).all()
                ix=a-lo+stride*np.arange(trial['n']);assert ix.min()>=0 and ix.max()<x.shape[1]
                hashes={}
                for v in VARIANTS:
                    y=apply_filter(x,sos,v)[:,ix].astype(np.float32)
                    assert np.isfinite(y).all() and y.shape==(64,trial['n'])
                    g=files[v].create_group(key)
                    for attr,value in old[key].attrs.items():g.attrs[attr]=value
                    g.create_dataset('eeg_1_20',data=y,compression='lzf')
                    hashes[v]=hashlib.sha256(y.tobytes()).hexdigest()
                    del y
                details.append({'trial':key,'context_native':[lo,hi],'native_trial':[a,b],'output_n':trial['n'],
                                'rounding_error_s':a/fs-trial['onset_s'],'array_sha256':hashes})
                del x
        for f in files.values():f.close()
        files={}
        for v,path in outputs.items():os.replace(str(path)+'.tmp',path)
    finally:
        for f in files.values():f.close()
        raw.close()
    freq=np.linspace(64,fs/2,8193);_,response=sosfreqz(sos,worN=freq,fs=fs)
    stat=p.stat();assert stat.st_size==row['raw_size'] and stat.st_mtime_ns==row['raw_mtime_ns']
    value={'status':'complete','probe':probe,'row':row,'sources':sources(),'raw_sha256':sha(p),'fs_native':fs,'native_stride':stride,
           'filter_sos':sos,'max_folding_amplitude':float(np.max(np.abs(response)**2)),
           'output_sha256':{v:sha(path) for v,path in outputs.items()},'trials':details,
           'seconds':time.time()-started,'job':os.environ['SLURM_JOB_ID']}
    write(receipt,value);print('CACHE',row['id'],round(value['seconds'],1),'probe',probe,flush=True);return value


@contextmanager
def cohort_source(root):
    oldpath,oldstd=D.DTU_PRE,D._stdz
    bounds=[];offset=0
    def stdz(arrs,guard):
        nonlocal offset
        for a in arrs:
            bounds.append((offset,offset+a.shape[1]));offset+=a.shape[1]
        return oldstd(arrs,guard)
    D.DTU_PRE=str(root);D._stdz=stdz
    try:yield bounds
    finally:D.DTU_PRE,D._stdz=oldpath,oldstd


def load_variant(variant,cf):
    with cohort_source(STORE/'production'/variant) as bounds:
        coh=D.load_dtu(cf,kinds=('ss',))
    starts=np.array([a for a,b in bounds]);ends=np.array([b for a,b in bounds])
    assert len(starts) and ends[-1]==coh.eeg.shape[1]
    for seg in coh.segments:
        k=int(np.searchsorted(starts,seg['e0'],side='right')-1)
        assert starts[k]<=seg['e0'] and seg['e0']+coh.meta['seg_len']<=ends[k]
        seg['physical_trial_bounds']=[int(starts[k]),int(ends[k])]
    return coh


def mse_of(stats,w,b):
    pred2=np.einsum('ij,ik,kj->j',w,stats.Sxx,w)+2*b*(stats.Sx@w)+stats.n*b*b
    cross=np.einsum('ij,ij->j',w,stats.Sxy)+b*stats.Sy
    return float(np.maximum(stats.Syy+pred2-2*cross,0).mean()/stats.n)


def analyse_cohort(coh,sf):
    from auditory_alignment_v2.train import train_participants
    train=sorted(train_participants(coh,{},sf))
    test=sorted(i for i,p in enumerate(coh.participants) if p['fold']==sf)
    assert not set(train)&set(test)
    order=np.random.default_rng(S.GROUP_SEED).permutation(len(train));groups={p:int(order[i])%S.N_GROUPS for i,p in enumerate(train)}
    width=round(.02*coh.fs);dim=coh.n_ch*width;out={}
    use=[s for s in coh.segments if (s['p'] in train and s['role'] in ('fit','es')) or (s['p'] in test and s['role']=='test')]
    for guard in GUARDS:
        for lag in LAGS:
            gs=[S.Stats(dim,1) for _ in range(S.N_GROUPS)];ts={p:S.Stats(dim,1) for p in test}
            counts={p:0 for p in test}
            for seg in use:
                tt=keep_anchors(seg['e0'],seg['physical_trial_bounds'],guard,coh.fs)
                if not len(tt):continue
                ix=seg['e0']+tt[:,None]+round(lag*coh.fs/1000)+np.arange(width)[None]
                x=coh.eeg[:,ix].transpose(1,0,2).reshape(len(tt),dim).astype(np.float64)
                y=np.asarray(coh.stim['Local'][5,seg['s0']+tt],np.float64)[:,None]
                if seg['p'] in test:ts[seg['p']].add(x,y);counts[seg['p']]+=1
                else:gs[groups[seg['p']]].add(x,y)
            assert all(g.n>0 for g in gs) and all(s.n>0 for s in ts.values())
            alpha,trace=S.choose(gs);total=S.Stats(dim,1)
            for g in gs:total+=g
            w,b=S.fit(total,alpha)
            out[f'{guard}/{lag}']={'alpha':alpha,'development':trace,'n_training_anchors':total.n,
                'per_participant':{coh.participants[p]['id']:{'r':S.r_of(s,w,b),'mse':mse_of(s,w,b),'n_anchors':s.n,
                    'n_segments':counts[p],'group':coh.participants[p]['group']} for p,s in ts.items()}}
    return {'cells':out,'training_ids':[coh.participants[p]['id'] for p in train],
            'test_ids':[coh.participants[p]['id'] for p in test],'width_samples':width}


def manifest(plan):
    path=BASE/'cache_manifest.json'
    rows=[]
    for r in plan['recordings']:
        p=STORE/'production/receipts'/(r['id']+'.json');v=read(p)
        assert v['status']=='complete' and not v['probe'] and v['row']==r and v['sources']==plan['sources']
        rows.append({'id':r['id'],'receipt_sha256':sha(p),'outputs':v['output_sha256'],'raw_sha256':v['raw_sha256']})
    value={'plan_sha256':sha(PLAN),'recordings':rows}
    if path.exists():assert read(path)==value
    else:write(path,value);path.chmod(0o444)
    return path


def task(plan,sf,cf):
    p=BASE/'units'/f'sf{sf}_cf{cf}.json';mp=manifest(plan)
    if p.exists():
        v=read(p);assert v['status']=='complete' and v['plan_sha256']==sha(PLAN) and v['cache_manifest_sha256']==sha(mp)
        return
    started=time.time();values={}
    for v in VARIANTS:
        coh=load_variant(v,cf);values[v]=analyse_cohort(coh,sf);del coh;gc.collect()
    a,b=(values[v] for v in VARIANTS)
    assert a['training_ids']==b['training_ids'] and a['test_ids']==b['test_ids']
    for key in a['cells']:
        for ident,x in a['cells'][key]['per_participant'].items():
            y=b['cells'][key]['per_participant'][ident]
            assert (x['n_anchors'],x['n_segments'],x['group'])==(y['n_anchors'],y['n_segments'],y['group'])
    write(p,{'status':'complete','subject_fold':sf,'content_fold':cf,'plan_sha256':sha(PLAN),
             'cache_manifest_sha256':sha(mp),'filters':values,'seconds':time.time()-started,'job':os.environ['SLURM_JOB_ID']})
    print('FOLD',sf,cf,'complete',round(time.time()-started,1),flush=True)


def aggregate(plan):
    by={};groups={};done=0
    for sf,cf in plan['tasks']:
        p=BASE/'units'/f'sf{sf}_cf{cf}.json'
        if not p.exists():continue
        rec=read(p);assert rec['status']=='complete' and rec['plan_sha256']==sha(PLAN);done+=1
        for variant,vr in rec['filters'].items():
            for cell,value in vr['cells'].items():
                for ident,row in value['per_participant'].items():
                    groups[ident]=row['group'];by.setdefault(ident,{})[(cf,variant,cell)]=row
    cells=[f'{g}/{l}' for g in GUARDS for l in LAGS]
    expected={(cf,v,k) for cf in (0,1) for v in VARIANTS for k in cells}
    people=sorted(p for p,items in by.items() if set(items)==expected)
    results={}
    for metric in ('r','mse'):
        values={v:np.array([[np.mean([by[p][(cf,v,k)][metric] for cf in (0,1)]) for k in cells] for p in people]) for v in VARIANTS}
        diff=values['causal_cascade']-values['zero_phase']
        if metric=='mse':diff=-diff
        families={}
        for group in ('all','nh','hi'):
            ix=[i for i,p in enumerate(people) if group=='all' or groups[p]==group]
            families[group]={v:clean(ST.summary(x[ix],B=4000,seed=ST.group_seed('causal',metric,v,group)))
                             for v,x in {**values,'causal_benefit':diff}.items()} if len(ix)>=3 else {'n':len(ix)}
        hi=[i for i,p in enumerate(people) if groups[p]=='hi'];nh=[i for i,p in enumerate(people) if groups[p]=='nh']
        families['hi_minus_nh_effect']=clean(ST.contrast(diff[hi],diff[nh],B=4000,seed=ST.group_seed('causal',metric,'interaction'))) if len(hi)>=3 and len(nh)>=3 else {'n_hi':len(hi),'n_nh':len(nh)}
        results[metric]=families
    out={'time':now(),'job':os.environ['SLURM_JOB_ID'],'status':'complete' if done==10 else 'interim','tasks_complete':done,
         'complete_paired_people':len(people),'expected_people':44,'cells':cells,'families':results,'plan_sha256':sha(PLAN)}
    write(ROOT/'results/auditory_alignment_v3/aln34/causal_filter/efficacy.json',out)
    lines=['# Native DTU filter and boundary sensitivity','',f"Snapshot{out['time']}; **{out['status']}**; {done}/10fold tasks; {len(people)}/44pair-complete identities.",'',
           'Two forward passes versus forward/backward filtering share the interior magnitude response. No causal delay is removed. Original sound targets and offline whole-recording normalization remain; this is not an online-causal pipeline or a neural latency estimate. Native sources, hashes, exact sample coordinates and10guard×lag cells are retained. Positive benefit means higher correlation or lower envelope MSE for the causal branch.4000identity bootstrap-t; simultaneous intervals within each metric/contrast10-cell family. Content folds do not increase n.','']
    for metric in ('r','mse'):
        value=results[metric]['all'].get('causal_benefit',{})
        if 'est' not in value:continue
        lines += [f'## {metric}: paired causal benefit','', '| Guard / lag(ms) | Difference | Simultaneous95% interval |','|---|---:|---:|']
        lines += [f"| {k} | {value['est'][i]:+.5f} | [{value['band_low'][i]:+.5f}, {value['band_high'][i]:+.5f}] |" for i,k in enumerate(cells)]
        lines.append('')
    (ROOT/'docs/auditory_alignment_v3/CAUSAL_FILTER_BOUNDARY_RESULTS.md').write_text('\n'.join(lines)+'\n')
    print('AGGREGATE',done,len(people),flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--register',action='store_true');ap.add_argument('--probe',action='store_true')
    ap.add_argument('--run',action='store_true');ap.add_argument('--aggregate',action='store_true');ap.add_argument('--smoke-job')
    a=ap.parse_args();assert os.environ.get('SLURM_JOB_ID');os.umask(0o077)
    if a.register:register();return
    plan=read(PLAN);verify(plan)
    if a.probe:
        row=plan['recordings'][0];value=cache_one(row,True)
        # Real native single-record probe; do not manufacture cross-person efficacy.
        root=STORE/'probes'/os.environ['SLURM_JOB_ID'];key=sorted(row['trials'])[0]
        with h5py.File(root/VARIANTS[0]/(row['id']+'.h5'),'r') as f:x=f[key]['eeg_1_20'][:,:4096].astype(float).T
        inventory=read(Path(D.PUB)/'derived/c3_features_v1/dtu/inventory.json')
        entry=next(r for r in inventory if r['file']==row['id'] and r['trial']==key and r['kind']=='target')
        assert entry.get('sha')
        with h5py.File(Path(D.DTU_KCS)/'dtu_cf0.h5','r') as f:target=f[entry['sha']]['Local'][5,:4096].astype(float)[:,None]
        n=min(len(x),len(target));assert n>256
        x,target=x[64:n-64],target[64:n-64];cut=round(.7*len(x))
        stats=S.Stats(64,1);stats.add(x[:cut],target[:cut]);w,b=S.fit(stats,1.)
        check=S.Stats(64,1);check.add(x[cut:],target[cut:]);assert np.isfinite(mse_of(check,w,b))
        write(BASE/'probes'/os.environ['SLURM_JOB_ID']/'receipt.json',{'status':'pass','plan_sha256':sha(PLAN),'cache_receipt_sha256':sha(root/'receipts'/(row['id']+'.json')),
              'scope':'one real native recording/trial plus existing envelope readout; truncated engineering, not cross-person efficacy',
              'source_n':len(x),'target_sha':entry['sha']})
        return
    if a.run:
        receipt=read(BASE/'probes'/str(a.smoke_job)/'receipt.json')
        assert receipt['status']=='pass' and receipt['plan_sha256']==sha(PLAN)
        import fcntl
        BASE.mkdir(parents=True,exist_ok=True)
        with (BASE/'.production.lock').open('a+') as handle:
            fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            for row in plan['recordings']:cache_one(row)
            manifest(plan)
            for sf,cf in plan['tasks']:task(plan,sf,cf);aggregate(plan)
    elif a.aggregate:aggregate(plan)


if __name__=='__main__':main()
