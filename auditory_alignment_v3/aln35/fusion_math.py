"""Source-selected probability controls; no data loading or scheduling."""
import hashlib
import numpy as np

WEIGHTS=(0.,.25,.5,.75,1.)
TEMPERATURES=(1.,.5,2.)
EPSILONS=(0.,.05,.1,.25)
PERM_SEEDS=tuple(range(351520,351530))

def probability(scores,temperature=1.):
    z=np.asarray(scores,dtype=np.float64)/temperature
    assert np.isfinite(z).all() and temperature>0
    z=z-z.max(axis=1,keepdims=True);p=np.exp(z)
    return p/p.sum(axis=1,keepdims=True)

def metrics(p,own,reference):
    assert p.shape==reference.shape and np.isfinite(p).all() and np.allclose(p.sum(1),1)
    index=np.arange(len(p));order=np.argsort(-p,axis=1)
    rank=np.argmax(order==own[:,None],axis=1)
    return dict(true_nll_bits=-np.log2(np.maximum(p[index,own],1e-300)),
        rank_pct=rank/max(1,p.shape[1]-1),top1=(rank==0).astype(float),
        entropy_bits=-(p*np.log2(np.maximum(p,1e-300))).sum(1),
        tv_from_cb=np.abs(p-reference).sum(1)/2)

def risk(p,own,people):
    ll=-np.log2(np.maximum(p[np.arange(len(p)),own],1e-300))
    assert np.isfinite(ll).all()
    return float(np.mean([ll[people==pid].mean() for pid in sorted(set(people))]))

def select(candidates,own,people):
    values={key:risk(p,own,people) for key,p in candidates.items()}
    selected=min(values,key=values.get)
    return selected,values

def candidate_sets(local,cb,repeated=None):
    output={'cb_direct':{1.:cb},
        'cb_temperature':{t:probability(np.log(np.maximum(cb,1e-300)),t) for t in TEMPERATURES},
        'cb_shrink':{e:(1-e)*cb+e/cb.shape[1] for e in EPSILONS},
        'actual_mix':{w:w*local+(1-w)*cb for w in WEIGHTS}}
    if repeated is not None:
        output['cb_repeated']={w:w*repeated+(1-w)*cb for w in WEIGHTS}
    return output

def derangement(query_ids,people,seed,role,pool_hash):
    assert len(query_ids)==len(set(query_ids))==len(people)
    indices=np.arange(len(people));perm=np.full(len(people),-1,dtype=int);coverage={}
    for pid in sorted(set(people)):
        rows=indices[people==pid]
        ordered=sorted(rows,key=lambda i:hashlib.sha256(f'{seed}|{pid}|{role}|{pool_hash}|{query_ids[i]}'.encode()).hexdigest())
        coverage[str(pid)]={'queries':len(rows),'valid':len(rows)>=2}
        if len(rows)>=2:
            target=np.roll(ordered,1)
            perm[ordered]=target
            assert np.all(perm[rows]!=rows)
    return perm,coverage
