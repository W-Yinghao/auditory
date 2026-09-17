"""Known-probability worlds with strong H, imbalance and dependent trial noise."""
import numpy as np
from scipy.optimize import brentq
from scipy.signal import lfilter
from scipy.special import expit
from numpy.polynomial.hermite import hermgauss
from .estimator import split_roles


def normal_expectation(mean,sd,intercept,coefficient=1.):
    nodes,w=hermgauss(30)
    return np.sum(expit(intercept[:,None]+coefficient*(np.asarray(mean)[:,None]+sd*np.sqrt(2)*nodes))*w,axis=1)/np.sqrt(np.pi)


def ar_noise(rng,sizes,dimension,rho=.25):
    parts=[]
    for n in sizes:
        eps=rng.normal(size=(int(n),dimension))*np.sqrt(1-rho*rho)
        initial=rng.normal(size=(1,dimension))*rho
        parts.append(lfilter([1],[1,-rho],eps,axis=0,zi=initial)[0])
    return np.vstack(parts)


def embedding(rng,latent,sizes,dimension):
    x=ar_noise(rng,sizes,dimension)
    # Correlated high-variance subspace survives per-coordinate standardization.
    # Noise is exactly orthogonal, so latent coordinates remain observable and
    # the stated conditional oracle is exact for the generated feature vector.
    # This is a specified identifiability fixture, not a real-data power claim.
    loadings=np.linalg.qr(rng.normal(size=(dimension,8)),mode='reduced')[0]
    x=x-(x@loadings)@loadings.T
    return x+3*latent@loadings.T


def generate(packet,world,seed,dimension,rate,samples_cycle=(107,584,795,914,976),*,
             history_dimension=7,background_dimension=None,role_sample_sizes=None):
    if dimension not in (64,400):raise ValueError('FROZEN_DIMENSION')
    rng=np.random.default_rng(seed)
    background_dimension=dimension if background_dimension is None else int(background_dimension)
    if background_dimension not in (64,200,400) or history_dimension not in (7,25):raise ValueError('FROZEN_INPUT_WIDTH')
    if role_sample_sizes is None:
        sizes=np.resize(np.asarray(samples_cycle,int),60);provided_roles=None
    else:
        if set(role_sample_sizes)!={'A','B','C','D','E'}:raise ValueError('PROFILE_ROLES')
        sizes=np.array([n for role in ('A','B','C','D','E') for n in role_sample_sizes[role]],int)
        if np.any(sizes<1):raise ValueError('PROFILE_TRIAL_SUPPORT')
        provided_roles={};start=0
        for role in ('A','B','C','D','E'):
            stop=start+sum(role_sample_sizes[role]);provided_roles[role]=np.arange(start,stop);start=stop
    groups=np.repeat(np.arange(len(sizes)).astype(str),sizes);n=len(groups)
    h=ar_noise(rng,sizes,7)
    h[:,4]=np.repeat(rng.normal(size=len(sizes)),sizes)
    lp=ar_noise(rng,sizes,8);lb=ar_noise(rng,sizes,8)
    hscore=1.5*h[:,0]+1.2*h[:,1]*h[:,2]+.35*h[:,4]
    weak=world.endswith('_weak');mechanism=world[:-5] if weak else world
    if packet=='N3':
        if mechanism not in ('strong_history_null','strong_history_increment','history_copy','near_deterministic'):
            raise ValueError('N3_WORLD')
        strength=(.3 if weak else .9) if mechanism=='strong_history_increment' else 0.
        signal=strength*lp[:,0]
        if mechanism=='history_copy':lp[:,:7]=h
        if mechanism=='near_deterministic':
            h[:,0]=(rng.random(n)<rate)*2-1
            hscore=18*h[:,0];signal=np.zeros(n);intercept=0.
        else:intercept=brentq(lambda b:expit(b+hscore+signal).mean()-rate,-30,30)
        true=expit(intercept+hscore+signal)
        base=normal_expectation(np.zeros(n),1.,intercept+hscore,strength)
        oracle={'H':base,'joint':true}
    elif packet=='N1':
        if mechanism not in ('trial_key','group_key','additive_background','independent_background','history_only'):
            raise ValueError('N1_WORLD')
        coefficient=.5 if weak else 1.5
        if mechanism in ('trial_key','group_key'):
            key=rng.choice([-1.,1.],size=n if mechanism=='trial_key' else len(sizes))
            if mechanism=='group_key':key=np.repeat(key,sizes)
            lb[:,0]=key
            signal=coefficient*lp[:,0]*key
        elif mechanism=='additive_background':
            original=lp[:,0].copy();lp[:,0]=original+1.5*lb[:,0];signal=1.5*original
        elif mechanism=='independent_background':signal=1.5*lp[:,0]
        else:signal=np.zeros(n)
        intercept=brentq(lambda b:expit(b+hscore+signal).mean()-rate,-30,30)
        hs=intercept+hscore;true=expit(hs+signal)
        if mechanism in ('trial_key','group_key'):
            hp=(expit(hs+coefficient*lp[:,0])+expit(hs-coefficient*lp[:,0]))/2
            hb=normal_expectation(np.zeros(n),1.,hs,coefficient)
        elif mechanism=='additive_background':
            hp=normal_expectation(lp[:,0]/3.25,np.sqrt(2.25/3.25),hs,1.5)
            hb=normal_expectation(np.zeros(n),1.,hs,1.5)
        elif mechanism=='independent_background':
            hp=true.copy();hb=normal_expectation(np.zeros(n),1.,hs,1.5)
        else:hp=true.copy();hb=true.copy()
        oracle={'HP':hp,'HB':hb,'joint':true}
    else:raise ValueError('PACKET')
    y=(rng.random(n)<true).astype(int)
    p=embedding(rng,lp,sizes,dimension);b=embedding(rng,lb,sizes,background_dimension)
    noise=ar_noise(rng,sizes,background_dimension if packet=='N1' else dimension)
    if history_dimension>7:h=np.c_[h,ar_noise(rng,sizes,history_dimension-7)]
    roles=provided_roles if provided_roles is not None else split_roles(groups,np.arange(48).astype(str),np.arange(34,48).astype(str),np.arange(48,60).astype(str))
    return dict(h=h,p=p,b=b,noise=noise,y=y,groups=groups,roles=roles,oracle=oracle,
                packet=packet,world=world,seed=seed,dimension=dimension,rate=rate,
                generator='observable_spiked_latent_subspace; AR0.25; independent identity roles',
                oracle_scope='known conditional probabilities; Gaussian latent marginal quadrature30; not fitted predictors')
