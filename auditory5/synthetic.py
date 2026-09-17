"""Known generative controls. No real EEG or clinical observations enter here.

Monte Carlo detection uses a floor AND a candidate-bootstrap lower CI >0.
This validates selected estimators; it does not validate the whole EEG pipeline.
"""
from pathlib import Path
import json, warnings
import numpy as np
import torch
from scipy.special import expit
from sklearn.linear_model import LogisticRegression,Ridge
from sklearn.preprocessing import StandardScaler,SplineTransformer
from sklearn.neural_network import MLPClassifier
from sklearn.exceptions import ConvergenceWarning
from auditory5.contracts import FitScope
from auditory5.head_geometry import decompose_head,max_softmax_difference
from auditory5.metrics import candidate_log_losses_bits
from auditory5.probes import candidate_class_weights,CandidateTabularScaler
from auditory5.statistics import paired_cluster_bootstrap,a_candidate_bootstrap
from auditory5.provenance import require_slurm,write_json

SNR_GRID=(.25,.5,1.,2.)
SAMPLE_GRID=(32,48)


def _mc_interval(k,n):
    """Wilson score interval, including k=0 and k=n."""
    z=1.95996398454;p=k/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den;half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return {'successes':int(k),'n':int(n),'rate':float(p),'lower':float(center-half),'upper':float(center+half)}


def _split(groups,rng):
    ids=np.unique(groups);rng.shuffle(ids);n=max(4,int(.6*len(ids)))
    return np.isin(groups,ids[:n])


def _head(x,y,g,tr,hidden=None):
    scope=FitScope(tuple(np.unique(g[tr]).tolist()),test_groups=tuple(np.unique(g[~tr]).tolist()))
    scale=CandidateTabularScaler().fit(x[tr],g[tr],scope);a,b=scale.transform(x[tr]),scale.transform(x[~tr])
    if hidden is None:model=LogisticRegression(C=1,max_iter=1000,tol=1e-7)
    else:model=MLPClassifier(hidden_layer_sizes=(hidden,),activation='relu',solver='lbfgs',alpha=1.,max_iter=600,random_state=11,tol=1e-6)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always',ConvergenceWarning)
        model.fit(a,y[tr],sample_weight=candidate_class_weights(y[tr],g[tr]))
    losses=candidate_log_losses_bits(y[~tr],model.predict_proba(b),g[~tr])
    return np.array([losses[k] for k in sorted(losses)]),sum(issubclass(w.category,ConvergenceWarning) for w in caught)


def _gain(a,b,floor,seed,boot=400):
    s=paired_cluster_bootstrap(a,b,np.arange(len(a)),n_boot=boot,seed=seed)
    return {'effect':s['estimate'],'ci_lower':s['ci_lower'],'ci_upper':s['ci_upper'],
            'screen':bool(s['estimate']>=floor and s['ci_lower']>0)}


def _a_world(rng,snr,positive,n=40,boot=400):
    # Candidate backgrounds are equally present in both classes, hence cancel exactly.
    p=5;prototype=rng.normal(size=p);background=rng.normal(size=(n,p))*3
    interaction=rng.normal(size=(n,p)) if positive else np.zeros((n,p))
    means=np.empty((2,n,2,p))
    for half in range(2):
        for k in range(2):
            means[half,:,k]=background+(2*k-1)*(prototype+interaction)/2+rng.normal(size=(n,p))/(snr*np.sqrt(20))
    delta=means[:,:,1]-means[:,:,0];tr=_split(np.arange(n),rng)
    train=delta[:,tr].mean(axis=0);mu=train.mean(axis=0)
    _,s,v=np.linalg.svd(train-mu,full_matrices=False);keep=min(5,len(train)-2,int((s>max(train.shape)*np.finfo(float).eps*s[0]).sum()))
    scales=np.std((train-mu)@v[:keep].T,axis=0);assert np.all(scales>0)
    x=(delta[0,~tr]-mu)@v[:keep].T/scales;y=(delta[1,~tr]-mu)@v[:keep].T/scales
    stat=a_candidate_bootstrap(x,y,np.arange(len(x)),n_boot=boot,seed=int(rng.integers(2**31)))
    bkg=means.mean(axis=2)
    return {'effect':stat['estimate'],'ci_lower':stat['ci_lower'],'ci_upper':stat['ci_upper'],
            'screen':bool(stat['estimate']>=.05 and stat['ci_lower']>0),
            'background_strength':float(np.mean(bkg[0]*bkg[1])),'convergence_warnings':0}


def _b_world(rng,snr,positive,n=40,boot=400):
    g=np.repeat(np.arange(n),40);c=rng.normal(size=(len(g),2))
    logit=1.2*c[:,0]-.6*c[:,1]+.6*c[:,0]**2
    h=(rng.random(len(g))<expit(logit)).astype(int)
    # Both classes must exist per group before evaluation; deterministic complementary
    # response sampling is unnecessary at these sizes. Failed support is explicit.
    for i in np.unique(g):
        if len(np.unique(h[g==i]))!=2:raise ValueError('synthetic history support missing')
    tr=_split(g,rng)
    spline=SplineTransformer(n_knots=3,degree=3,include_bias=False).fit(c[tr])
    context=np.c_[c,c*c,spline.transform(c)]
    pre=np.c_[c[:,0]**2,c[:,1]]+rng.normal(size=(len(g),2))/snr
    post=.5*pre+(2*h[:,None]-1)*np.array([[1.,-.7]])*(1 if positive else 0)+rng.normal(size=(len(g),2))/snr
    a,wa=_head(context,h,g,tr);b,wb=_head(np.c_[context,post],h,g,tr)
    p,wp=_head(np.c_[context,pre],h,g,tr);q,wq=_head(np.c_[context,pre,post],h,g,tr)
    result=_gain(a,b,.01,int(rng.integers(2**31)),boot)
    support=_gain(p,q,.01,int(rng.integers(2**31)),boot)
    result.update(pre_adjusted_effect=support['effect'],pre_adjusted_lower=support['ci_lower'],convergence_warnings=wa+wb+wp+wq)
    result['screen']=bool(result['screen'] and support['effect']>0 and support['ci_lower']>0 and np.mean(a-b>0)>=.6)
    return result


def _c_world(rng,snr,positive,n=40,boot=400):
    g=np.repeat(np.arange(n),24);bits=rng.integers(0,2,(len(g),2));y=np.logical_xor(bits[:,0],bits[:,1]).astype(int)
    if positive:
        left=(2*bits[:,0]-1)[:,None]+rng.normal(size=(len(g),1))/snr
        right=(2*bits[:,1]-1)[:,None]+rng.normal(size=(len(g),1))/snr
    else:
        left=(2*y-1)[:,None]+rng.normal(size=(len(g),1))/snr;right=left.copy()
    tr=_split(g,rng);views={'L':left,'R':right,'LR':np.c_[left,right],'LL':np.c_[left,left],'RR':np.c_[right,right]}
    losses={};warnings_n=0
    for name,x in views.items():
        losses[name],w=_head(x,y,g,tr,32);warnings_n+=w
    # Both individual gains must be positive, evaluated pairwise, not min of noisy per-child losses.
    ref='L' if losses['L'].mean()<=losses['R'].mean() else 'R'
    s=_gain(losses[ref],losses['LR'],.01,int(rng.integers(2**31)),boot)
    lin_l,w1=_head(left,y,g,tr);lin_lr,w2=_head(views['LR'],y,g,tr)
    s.update(linear_joint_effect=float(np.mean(lin_l-lin_lr)),duplicate_best_loss=float(min(losses['LL'].mean(),losses['RR'].mean())),
             convergence_warnings=warnings_n+w1+w2)
    s['screen']=bool(s['screen'] and losses['LR'].mean()<min(losses['LL'].mean(),losses['RR'].mean()))
    return s


def _ridge_predict(x,y,tr):
    # All preprocessing/alpha choices use training rows. Each row is one candidate.
    best=None;ids=np.flatnonzero(tr)
    for alpha in [.1,1.,10.]:
        errs=[]
        for fold in range(3):
            valid=ids[np.arange(len(ids))%3==fold];fit=ids[np.arange(len(ids))%3!=fold]
            scale=StandardScaler().fit(x[fit]);r=Ridge(alpha=alpha).fit(scale.transform(x[fit]),y[fit])
            errs.extend(abs(y[valid]-np.clip(r.predict(scale.transform(x[valid])),0,100)))
        item=(float(np.mean(errs)),-alpha)
        if best is None or item<best[0]:best=(item,alpha)
    scale=StandardScaler().fit(x[tr]);r=Ridge(alpha=best[1]).fit(scale.transform(x[tr]),y[tr])
    return np.clip(r.predict(scale.transform(x[~tr])),0,100)


def _d_world(rng,snr,positive,n=40,boot=400):
    c=rng.normal(size=(2*n,3));z=rng.normal(size=(2*n,5));tr=_split(np.arange(2*n),rng)
    w=torch.tensor([[1.,0,0,0,0],[-1.,0,0,0,0]],dtype=torch.float64)
    geo=decompose_head(w,torch.zeros(2),torch.from_numpy(z[tr].mean(axis=0)))
    error=float(max_softmax_difference(torch.from_numpy(z),geo));assert geo.rank==1 and error<1e-10
    y=np.clip(50+10*c[:,0]-4*c[:,1]+(6*z[:,1] if positive else 0)+rng.normal(size=len(z))*3/snr,0,100)
    vis=z@geo.visible_basis.numpy();nul=z@geo.null_basis.numpy()
    # Train-only null PCA, three directions. No test target selects projection.
    mu=nul[tr].mean(axis=0);_,_,v=np.linalg.svd(nul[tr]-mu,full_matrices=False);nul=(nul-mu)@v[:3].T
    base=np.c_[c,vis];aug=np.c_[base,nul]
    a=abs(y[~tr]-_ridge_predict(base,y,tr));b=abs(y[~tr]-_ridge_predict(aug,y,tr))
    con=abs(y[~tr]-_ridge_predict(c,y,tr));s=_gain(a,b,.5,int(rng.integers(2**31)),boot)
    s.update(clinical_only_gain=float(np.mean(con-b)),softmax_max_error=error,convergence_warnings=0)
    s['screen']=bool(s['screen'] and np.mean(con-b)>0)
    return s


def _e_world(rng,snr,positive,n=40,boot=400):
    g=np.repeat(np.arange(n),32);x=rng.normal(size=(len(g),2));y=(x[:,0]+rng.normal(size=len(g))/snr>0).astype(int)
    # Positive gap world source discards target direction; negative is invertible rotation.
    source=x[:,1:2] if positive else x@np.array([[0.,1.],[-1.,0.]])
    tr=_split(g,rng);a,wa=_head(source,y,g,tr);b,wb=_head(x,y,g,tr)
    s=_gain(a,b,.02,int(rng.integers(2**31)),boot);s['screen']=bool(s['screen'] and 1-b.mean()>=.01)
    s.update(target_information_bits=float(1-b.mean()),convergence_warnings=wa+wb)
    return s

_WORLD={'A':_a_world,'B':_b_world,'C':_c_world,'D':_d_world,'E':_e_world}


def run_synthetic_suite(output_directory,repetitions=100,seed=20260917):
    require_slurm()
    if isinstance(repetitions,bool) or int(repetitions)!=repetitions or repetitions<=0:raise ValueError('positive integer repetitions required')
    dest=Path(output_directory);dest.mkdir(parents=True,exist_ok=False)
    master=np.random.default_rng(seed);summary={'design':'auditory5_synthetic_v2_corrected_before_real_models','seed':seed,
        'repetitions_per_route_condition':repetitions,'snr_grid':list(SNR_GRID),'candidate_grid':list(SAMPLE_GRID),
        'loss_units':'bits; D source-scale MAE; A cosine','bootstrap_repetitions_per_world':400,
        'scope':'selected estimators and generative controls; not full encoder pipeline validation','routes':{}}
    for route,world in _WORLD.items():
        conditions={}
        for label in ['positive','negative']:
            rows=[]
            for rep in range(repetitions):
                snr=SNR_GRID[rep%4];n=SAMPLE_GRID[(rep//4)%2];trial_seed=int(master.integers(2**31))
                try:
                    r=world(np.random.default_rng(trial_seed),snr,label=='positive',n=n)
                    r.update(repetition=rep,snr=snr,n_candidates=n,seed=trial_seed,status='PASS')
                except Exception as exc:r={'repetition':rep,'snr':snr,'n_candidates':n,'seed':trial_seed,'status':'IMPLEMENTATION_FAIL','error':repr(exc)}
                rows.append(r)
            write_json(dest/(route+'_'+label+'_worlds.json'),rows)
            ok=[r for r in rows if r['status']=='PASS'];cells=[]
            for snr in SNR_GRID:
                cell=[r for r in ok if r['snr']==snr]
                if cell:cells.append({'snr':snr,'mean_effect':float(np.mean([r['effect'] for r in cell])),
                    'detection_rate':_mc_interval(sum(r['screen'] for r in cell),len(cell))})
            conditions[label]={'failure_count':len(rows)-len(ok),'convergence_warnings':sum(r.get('convergence_warnings',0) for r in ok),
                'cells':cells,'detection_rate':_mc_interval(sum(r['screen'] for r in ok),len(ok)) if ok else None}
        summary['routes'][route]=conditions
        print(json.dumps({'synthetic_route_completed':route,'worlds':2*repetitions}),flush=True)
    summary['status']='PASS' if all(c['failure_count']==0 for r in summary['routes'].values() for c in r.values()) else 'IMPLEMENTATION_FAIL'
    summary['interpretation']='Negative-world detection rates quantify estimator limitations; PASS means computational completion, not acceptable type-I error or biological validity.'
    write_json(dest/'synthetic_summary.json',summary);return summary
