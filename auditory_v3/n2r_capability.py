"""Bounded synthetic worlds on the exact frozen real metadata template."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import pickle
import numpy as np
import pandas as pd
from scipy.stats import beta
from .bags_packet import H_COLUMNS,validate_member_schema
from .n2r_execution import run_packet,n2r_algorithm_hash
from .runtime import write_json

WORLD_NAMES=('VAR_EXTRA','MEAN_SUFFICIENT','HISTORY_ONLY')
GENERATOR=dict(version=1,latent_dimensions=8,variance_sd_low=.35,variance_sd_high=2.0,
               mean_shift=2.,group_background_sd=.12,bag_background_sd=.20,
               temporal_decay_seconds=30.,observation_noise_sd=.005,
               development_seeds=[50001,50002,50003],evaluation_seeds=list(range(53001,53061)))

def generator_hash():
    h=hashlib.sha256(json.dumps(GENERATOR,sort_keys=True).encode())
    h.update(Path(__file__).read_bytes());h.update(n2r_algorithm_hash().encode())
    return h.hexdigest()

def capability_catalog():
    return pd.DataFrame([dict(world=w,repetition=j,seed=53001+i*20+j,outer_fold=j%5)
                         for i,w in enumerate(WORLD_NAMES) for j in range(20)])

@dataclass
class SyntheticPacket:
    members:pd.DataFrame
    post:np.ndarray
    pre:np.ndarray
    history:pd.DataFrame
    mechanism:str
    seed:int

def synthetic_packet(world,seed,members,history):
    """Preserve every identity, bag, member, half, cell, block and timestamp.

    Numeric EEG is never read. Eight latent coordinates are mixed redundantly
    into 400/200 coordinates, allowing the fixed training PCA8 to retain the
    injected low-dimensional mechanism. Stationary time-correlated bag means
    and identity backgrounds induce correlated repetitions. For the nulls,
    within-bag Gaussian residuals have common covariance: their sample variance
    is independent of their mean and the label. No bag is demeaned.
    HISTORY_ONLY fixes a synthetic H gap field compatible with each template
    label; the label is a deterministic function of that supplied H field.
    """
    if world not in WORLD_NAMES:raise ValueError('UNKNOWN_SYNTHETIC_WORLD')
    frame=validate_member_schema(members);hist=history.copy(deep=True)
    if hist.bag_id.duplicated().any() or set(hist.bag_id)!=set(frame.bag_id):raise ValueError('HISTORY_COVERAGE')
    rng=np.random.default_rng(int(seed));n=len(frame)
    latent=rng.normal(size=(n,8));pre_latent=rng.normal(size=(n,8))
    y=frame.stimulus_local_id.to_numpy(int)
    if world=='VAR_EXTRA':latent*=np.where(y==0,.35,2.)[:,None]
    elif world=='MEAN_SUFFICIENT':latent[:,0]+=(2*y-1)*2.
    else:
        labels=frame.groupby('bag_id',sort=False).stimulus_local_id.first()
        hist['gap_mean']=1.+2.*hist.bag_id.map(labels).to_numpy(float)
        latent[:,0]+=(2*y-1)*2. # response depends only on the provided synthetic H
    # Shared nuisance means cancel from sample variance without demeaning data.
    for _,group in frame.groupby('split_group_id',sort=True):
        background=rng.normal(0,.12,8);pre_background=rng.normal(0,.12,8)
        bag_times=group.groupby('bag_id',sort=True).onset_seconds_relative.mean().sort_values(kind='stable')
        state=rng.normal(0,.2,8);prev=float(bag_times.iloc[0])
        for bag,time in bag_times.items():
            rho=np.exp(-max(0.,float(time)-prev)/30.)
            state=rho*state+np.sqrt(max(0.,1-rho*rho))*rng.normal(0,.2,8)
            ix=group.index[group.bag_id.eq(bag)].to_numpy()
            latent[ix]+=background+state;pre_latent[ix]+=pre_background+state
            prev=float(time)
    mixing=rng.normal(size=(8,400));mixing/=np.linalg.norm(mixing,axis=0)
    pre_mixing=rng.normal(size=(8,200));pre_mixing/=np.linalg.norm(pre_mixing,axis=0)
    post=latent@mixing+rng.normal(0,.005,(n,400))
    pre=pre_latent@pre_mixing+rng.normal(0,.005,(n,200))
    return SyntheticPacket(frame,post,pre,hist,world,int(seed))

def _interval(k,n):
    return [float(beta.ppf(.025,k,n-k+1)) if k else 0.,float(beta.ppf(.975,k+1,n-k)) if k<n else 1.]

def summarize_capability(rows,development=False):
    table=pd.DataFrame(rows);worlds={};expected=1 if development else 20
    for world in WORLD_NAMES:
        part=table.loc[table.world.eq(world)];valid=part.execution.eq('COMPLETE')
        positive=valid & part.gain_bits.gt(.01);hits=valid & part.gain_bits.ge(.005) & part.ci_low.gt(0)
        worlds[world]=dict(expected=expected,attempted=len(part),evaluable=int(valid.sum()),strong_positive=int(positive.sum()),null_screen_hits=int(hits.sum()),strong_positive_binomial95=_interval(int(positive.sum()),expected),null_hit_binomial95=_interval(int(hits.sum()),expected))
    complete=all(x['attempted']==expected and x['evaluable']==expected for x in worlds.values())
    passes=complete and worlds['VAR_EXTRA']['strong_positive']>=(1 if development else 16) and all(worlds[w]['null_screen_hits']<=(0 if development else 2) for w in WORLD_NAMES[1:])
    return dict(status='PASS' if passes else 'CAPABILITY_FAIL',packet='N2R',development=development,complete_denominator=complete,worlds=worlds,generator_sha256=generator_hash(),algorithm_hash=n2r_algorithm_hash(),thresholds=dict(strong_gain_bits=.01,min_strong_worlds=16,null_gain_bits=.005,null_ci_low_positive=True,max_null_hits=2),interpretation='finite defined algorithm capability screen, not general false-positive-rate certification')

def run_worlds(members,history,splits,private,ledger,*,development=False,development_receipt=None):
    if not development:
        if not development_receipt or development_receipt.get('status')!='PASS' or development_receipt.get('generator_sha256')!=generator_hash():raise ValueError('FROZEN_DEVELOPMENT_PASS_REQUIRED')
    catalog=(pd.DataFrame([dict(world=w,repetition=0,seed=50001+i,outer_fold=i) for i,w in enumerate(WORLD_NAMES)]) if development else capability_catalog())
    private=Path(private);catalog.to_csv(private/'world_catalog.csv',index=False)
    write_json(private/'generator_frozen.json',dict(settings=GENERATOR,generator_sha256=generator_hash(),template_trials=len(members),template_bags=members.bag_id.nunique(),template_groups=members.split_group_id.nunique(),no_real_eeg_read=True))
    rows=[]
    for row in catalog.to_dict('records'):
        folder=private/('world_'+str(row['seed']));folder.mkdir(mode=0o700)
        try:
            packet=synthetic_packet(row['world'],row['seed'],members,history)
            out=run_packet(packet.members,packet.post,packet.pre,packet.history,splits,view_names=('HQ','HQV'),outer_folds=[row['outer_fold']],ledger=ledger,context=dict(fit_kind='development' if development else 'capability',seed=row['seed']))
            contrast=out['summary']['contrasts']['HQ_minus_HQV']
            result=dict(row,execution=out['summary']['execution'],gain_bits=contrast['gain_bits'],ci_low=contrast['ci_low'],ci_high=contrast['ci_high'])
            out['predictions'].to_parquet(folder/'predictions.parquet',index=False)
            out['identity_risks'].to_parquet(folder/'identity_risks.parquet',index=False)
            for name in ('models','fit_diagnostics','selections','transforms'):
                with (folder/(name+'.pkl')).open('wb') as f:pickle.dump(out[name],f)
        except Exception as exc:
            import traceback
            (folder/'traceback.txt').write_text(traceback.format_exc())
            result=dict(row,execution='FAILED',gain_bits=None,ci_low=None,ci_high=None,failure_type=type(exc).__name__)
        write_json(folder/'result.json',result);rows.append(result)
        pd.DataFrame(rows).to_csv(private/'world_progress.csv',index=False)
        print(json.dumps(result),flush=True)
    return pd.DataFrame(rows),summarize_capability(rows,development)
