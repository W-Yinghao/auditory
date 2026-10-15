"""Small numerical checks; no neural information-estimation claim."""
from __future__ import annotations
import numpy as np


def query_content_diagnostic(u: np.ndarray) -> dict:
    """Separate common time template from variation between segments at fixed q.

    u[segments,queries,features]. Descriptive second moments, not a pass threshold,
    a variance-component inferential model, or a measurement of neural signal.
    """
    u = np.asarray(u, dtype=float)
    if u.ndim != 3 or min(u.shape) < 1 or not np.isfinite(u).all():
        raise ValueError('Expected finite [segments,queries,features]')
    grand = u.mean((0,1), keepdims=True)
    template = u.mean(0, keepdims=True)
    total = float(np.mean((u-grand)**2))
    common = float(np.mean((template-grand)**2))
    content = float(np.mean((u-template)**2))
    return {'total_variance':total,'common_query_template_variance':common,
            'fixed_query_between_segment_variance':content,
            'template_fraction':None if total==0 else common/total,
            'content_fraction':None if total==0 else content/total,
            'interpretation':'descriptive_only; compare with same-query EEG exchange and task risk'}


def risk_increment(reference_losses: np.ndarray, candidate_losses: np.ndarray) -> float:
    a,b=np.asarray(reference_losses,float),np.asarray(candidate_losses,float)
    if a.shape!=b.shape or a.size==0 or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Matched finite loss arrays required')
    return float(np.mean(a-b))


def _fit_linear(x, y):
    x=np.asarray(x); return np.linalg.lstsq(np.column_stack([x,np.ones(len(x))]),y,rcond=None)[0]


def _predict(x,w):
    return np.column_stack([x,np.ones(len(x))])@w


def _r(a,b):
    if np.std(a)==0 or np.std(b)==0:return 0.0
    return float(np.corrcoef(a,b)[0,1])


def phase_coordinate_example(seed: int=3401, n_train: int=16000, n_test: int=16000) -> dict:
    """H = sign(phase)*Y + noise. A linear readout without phase interaction fails.

    An aligned feature or explicit H*phase interaction recovers Y. H together
    with phase still retains Y: weak linear readability need not mean total
    information was destroyed. This is a constructed example, not EEG data.
    """
    if min(n_train,n_test)<20:raise ValueError('Use enough synthetic draws')
    rng=np.random.default_rng(seed)
    def draw(n):
        y=rng.normal(size=n);p=rng.choice([-1.,1.],size=n)
        h=p*y+.05*rng.normal(size=n)
        return y,p,h
    yt,pt,ht=draw(n_train);yv,pv,hv=draw(n_test)
    w0=_fit_linear(ht[:,None],yt)
    wa=_fit_linear((ht*pt)[:,None],yt)
    wp=_fit_linear(np.column_stack([ht,pt,ht*pt]),yt)
    return {'data':'SYNTHETIC_ONLY','seed':seed,'n_train':n_train,'n_test':n_test,
            'linear_unaligned_r':_r(_predict(hv[:,None],w0),yv),
            'linear_aligned_r':_r(_predict((hv*pv)[:,None],wa),yv),
            'phase_interaction_r':_r(_predict(np.column_stack([hv,pv,hv*pv]),wp),yv),
            'coverage':'coordinate/readout counterexample, not a model of P6 causation'}
