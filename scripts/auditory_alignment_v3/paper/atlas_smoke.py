import json, time, numpy as np
from pathlib import Path
from auditory_alignment_v3.paper import cs_atlas as A
from auditory_alignment_v3.aln34 import content_time as CT
print('ref', A.reference_check(np.random.default_rng(1)))
u = [x for x in A.aln41_units() if x['arm']=='TCS' and x['dataset']=='dtu' and x['seed']==3401 and x['content_fold']==0][0]
print(len(A.aln41_units()), 'aln41 units;', len(A.aln34_units()), 'aln34 units')
dest = Path(u['dest']); meta = json.loads((dest/'meta.json').read_text()); rng = np.random.default_rng(0)
t0=time.time()
with np.load(dest/'arrays.npz') as z:
    person, role, seg = z['person'], z['role'], z['segment']; env, hist = z['env'][:,None], z['env_history']; P = z['pca_sf0'].astype(np.float64)
print('load', round(time.time()-t0,1), 's; rows', len(person), 'roles', {r:int((role==r).sum()) for r in set(role.tolist())})
train = np.isin(person, sorted(meta['pca']['0']['train_people'])) & np.isin(role, ('fit','es'))
w,b,_ = CT.fitted(hist[train], env[train], role[train])
targets = {'env': A.standardise(env, train), 'env|history': A.standardise(env-(hist@w+b), train)}
sig_s = {t: A.sigma_rule(y[train], rng) for t,y in targets.items()}
reps = {f'W{k}': P[:,k] for k in range(3)}; sig_u = {r: A.sigma_rule(x[train], rng) for r,x in reps.items()}
p = sorted(q for q,f in meta['folds'].items() if f==0 and q not in set(meta['dev_people']))[0]
ix = np.flatnonzero((person==p)&(role=='test')); print('person', p, 'test rows', len(ix), 'sigmas', sig_u, sig_s)
t0=time.time()
for r,t,v in A.person_cells({k:x[ix] for k,x in reps.items()}, {k:y[ix] for k,y in targets.items()}, seg[ix], sig_u, sig_s):
    print(r, t, {k: (round(x,5) if isinstance(x,float) else x) for k,x in v.items() if k in ('n','n_segments','cs_true','null_mean','null_sd','excess','z')})
print('cells time', round(time.time()-t0,2))
