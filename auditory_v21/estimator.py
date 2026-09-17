"""Independent group roles and exactly retained calibrated baseline candidates.

All fitting APIs take explicitly separated role indices. Test labels are never
passed to a fitter or selector. The predictor is a new finite-budget learner.
"""
from dataclasses import dataclass
import hashlib
import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.special import expit


def weights(groups):
    groups=np.asarray(groups)
    _,inv,counts=np.unique(groups,return_inverse=True,return_counts=True)
    return 1.0/counts[inv]/len(counts)


def risk(z,y,w):
    z,y,w=map(lambda x:np.asarray(x,float),(z,y,w))
    if z.shape!=y.shape or w.shape!=y.shape or not all(np.isfinite(a).all() for a in (z,y,w)):
        raise ValueError('RISK_SCHEMA')
    if not np.isin(y,[0,1]).all() or np.any(w<=0):raise ValueError('RISK_LABEL_WEIGHT')
    return float(np.dot(w,np.logaddexp(0,z)-y*z)/w.sum()/np.log(2))


def objective(theta,x,y,w,offset,lam):
    z=offset+x@theta[:-1]+theta[-1]
    value=np.dot(w,np.logaddexp(0,z)-y*z)+lam*np.dot(theta[:-1],theta[:-1])/2
    delta=w*(expit(z)-y)
    return float(value),np.r_[x.T@delta+lam*theta[:-1],delta.sum()]


def fit_head(x,y,g,*,offset=None,lam=.01,maxiter=200):
    x=np.asarray(x,float);y=np.asarray(y,float);g=np.asarray(g)
    if x.ndim!=2 or len(x)!=len(y) or len(y)!=len(g) or not np.isfinite(x).all():
        raise ValueError('FIT_SCHEMA')
    if not np.isin(y,[0,1]).all() or len(np.unique(y))!=2:raise ValueError('FIT_CLASSES')
    offset=np.zeros(len(y)) if offset is None else np.asarray(offset,float)
    if offset.shape!=y.shape or not np.isfinite(offset).all() or lam<=0:raise ValueError('OFFSET_SCHEMA')
    w=weights(g);theta=np.zeros(x.shape[1]+1)
    initial=objective(theta,x,y,w,offset,lam)[0]
    opt=minimize(objective,theta,args=(x,y,w,offset,lam),jac=True,method='L-BFGS-B',
                 options={'maxiter':maxiter,'ftol':1e-12,'gtol':1e-7,'maxls':40})
    final,gradient=objective(opt.x,x,y,w,offset,lam)
    if not np.isfinite(opt.x).all() or not np.isfinite(final) or final>initial+1e-8:
        raise FloatingPointError('NONFINITE_OR_WORSE_THAN_INITIAL')
    return opt.x,dict(status='FINITE_BUDGET_ESTIMATOR',iterations=int(opt.nit),
        optimizer_success=bool(opt.success),optimizer_status=int(opt.status),initial_objective=initial,
        final_objective=final,gradient_norm=float(np.linalg.norm(gradient)),parameter_norm=float(np.linalg.norm(opt.x)),
        maxiter=maxiter,lambda_l2=lam,fit_groups=int(len(np.unique(g))),fit_rows=len(y))


def predict_head(theta,x):
    z=np.asarray(x)@theta[:-1]+theta[-1]
    if not np.isfinite(z).all():raise FloatingPointError('NONFINITE_PREDICTION')
    return z


@dataclass
class Transform:
    mean:np.ndarray
    scale:np.ndarray
    components:np.ndarray|None=None

    @classmethod
    def fit(cls,x,g,pca=None):
        x=np.asarray(x,float)
        if x.ndim!=2 or not np.isfinite(x).all():raise ValueError('TRANSFORM_INPUT')
        w=weights(g);mean=np.sum(x*w[:,None],axis=0)
        scale=np.sqrt(np.maximum(np.sum((x-mean)**2*w[:,None],axis=0),1e-12))
        z=(x-mean)/scale
        components=None
        if pca is not None:
            cov=(z*w[:,None]).T@z
            vals,vecs=np.linalg.eigh(cov)
            order=np.argsort(vals)[::-1][:min(pca,x.shape[1])]
            components=vecs[:,order].T
            for row in components:
                if row[np.argmax(abs(row))]<0:row*=-1
        return cls(mean,scale,components)

    def apply(self,x):
        z=(np.asarray(x,float)-self.mean)/self.scale
        if self.components is not None:
            z=z@self.components.T
            if z.shape[1]<8:z=np.pad(z,((0,0),(0,8-z.shape[1])))
        if not np.isfinite(z).all():raise FloatingPointError('TRANSFORM_NONFINITE')
        return z


def h_basis(h):
    h=np.asarray(h,float)
    pair=[h[:,i]*h[:,j] for i in range(min(8,h.shape[1])) for j in range(i+1,min(8,h.shape[1]))]
    return np.c_[h,h*h,np.column_stack(pair)] if pair else np.c_[h,h*h]


def residual_map(h,p,b=None):
    if b is None:
        return np.c_[p,(h[:,:min(4,h.shape[1]),None]*p[:,None,:]).reshape(len(h),-1)]
    return np.c_[p,b,(p[:,:,None]*b[:,None,:]).reshape(len(p),-1)]


def split_roles(groups,outer_train,selection,test,seed=21101):
    """A excludes the entire encoder-held-out pool; split that pool into B/C/D.

    ``selection`` is the frozen D_inner0 encoder validation pool, not just D.
    All B/C/D and E must be absent from the source encoder training scope.
    """
    groups=np.asarray(groups).astype(str)
    selection,test,outer_train=map(lambda s:set(map(str,s)),(selection,test,outer_train))
    if not selection<=outer_train or outer_train&test:raise ValueError('ROLE_SCOPE_OVERLAP')
    eligible=set(groups);heldout=sorted(selection&eligible,
        key=lambda g:hashlib.sha256(f'{seed}|{g}'.encode()).hexdigest())
    nb=max(3,int(len(heldout)*.25));nc=(len(heldout)-nb)//2
    assignments={'A':sorted((outer_train-selection)&eligible),'B':heldout[:nb],
                 'C':heldout[nb:nb+nc],'D':heldout[nb+nc:],'E':sorted(test&eligible)}
    if len(assignments['A'])<12 or min(len(assignments[k]) for k in ('C','D'))<4 or min(len(assignments[k]) for k in ('B','E'))<3:
        raise ValueError('ROLE_SUPPORT_LIMITED')
    return {k:np.flatnonzero(np.isin(groups,v)) for k,v in assignments.items()}


def validate_roles(groups,roles):
    if set(roles)!={'A','B','C','D','E'}:raise ValueError('FIVE_ROLES_REQUIRED')
    seen=set()
    for role in ('A','B','C','D','E'):
        ix=np.asarray(roles[role])
        if ix.ndim!=1 or len(ix)==0 or len(set(ix))!=len(ix) or min(ix)<0 or max(ix)>=len(groups):
            raise ValueError('ROLE_INDEX_SCHEMA')
        own=set(np.asarray(groups)[ix])
        if own&seen:raise ValueError('ROLE_GROUP_OVERLAP')
        seen.update(own)
    assigned=np.concatenate([np.asarray(roles[k]) for k in ('A','B','C','D','E')])
    if len(assigned)!=len(groups) or not np.array_equal(np.sort(assigned),np.arange(len(groups))):
        raise ValueError('ROLE_ROWS_NOT_EXHAUSTIVE')


def validate_encoder_scope(groups,roles,receipt):
    if not receipt or not receipt.get('verified_artifact_hashes') or not receipt.get('source_scope_hash'):
        raise ValueError('ENCODER_PROVENANCE_REQUIRED')
    fit=set(map(str,receipt['encoder_fit_groups']))
    if receipt.get('feature_generation_kind')=='STATELESS_FIXED_BINNING':
        if fit or receipt.get('scaler_train_groups') or not receipt.get('stateless_source_verified'):
            raise ValueError('STATELESS_FEATURE_PROVENANCE_INVALID')
        return
    validation=set(map(str,receipt['encoder_validation_groups']))
    holdout=set().union(*(set(np.asarray(groups)[roles[k]].astype(str)) for k in ('B','C','D')))
    test=set(np.asarray(groups)[roles['E']].astype(str))
    if fit&(holdout|test) or not holdout<=validation:raise ValueError('ENCODER_ROLE_LEAKAGE')
    if receipt.get('inner_fold')!=0:raise ValueError('FROZEN_INNER_ENCODER_FOLD')


def calibrate(z,y,g):
    w=weights(g)
    opt=minimize_scalar(lambda logt:risk(z/np.exp(logt),y,w),bounds=(np.log(.25),np.log(16)),
                        method='bounded',options={'xatol':1e-8,'maxiter':100})
    if not opt.success or not np.isfinite(opt.x) or not np.isfinite(opt.fun):
        raise FloatingPointError('CALIBRATION_OPTIMIZATION_FAILED')
    options=[1.,.25,16.,float(np.exp(opt.x))]
    t=min(options,key=lambda t:risk(z/t,y,w))
    return float(t)


def choose(candidates,y,g):
    scores=[risk(z,y,weights(g)) for _,z in candidates]
    best=min(scores)
    selected=next(i for i,value in enumerate(scores) if value<=best+1e-8)
    return selected,scores


def fit_pipeline(h,p,b,noise,y,groups,roles,*,packet,lam=.01,maxiter=200,real=False,encoder_receipt=None,control_receipt=None,fit_observer=None):
    """Fit once with A/B/C/D only; return all E candidate and selected logits."""
    if packet not in ('N1','N3'):raise ValueError('PACKET')
    h,p,b,noise=map(lambda a:np.asarray(a,float),(h,p,b,noise))
    y,groups=np.asarray(y),np.asarray(groups)
    if len({len(h),len(p),len(b),len(noise),len(y),len(groups)})!=1:raise ValueError('ROW_ALIGNMENT')
    validate_roles(groups,roles)
    if real:
        validate_encoder_scope(groups,roles,encoder_receipt)
        if not control_receipt or not control_receipt.get('label_independent') or not control_receipt.get('source_hash'):
            raise ValueError('CONTROL_PROVENANCE_REQUIRED')
    a,cal,c,d,e=[np.asarray(roles[k]) for k in ('A','B','C','D','E')]
    # Inspect no E labels; they are used only by the caller's final scoring.
    for ix in (a,cal,c,d):
        if len(np.unique(y[ix]))!=2:raise ValueError('TRAINING_ROLE_CLASSES')
    transforms={};receipts=[];models={};temps={};calibration_fits=0
    def tracked(kind,name,operation):
        if fit_observer is not None:fit_observer('start',kind,name,{})
        try:result=operation()
        except Exception as exc:
            if fit_observer is not None:fit_observer('failed',kind,name,{'exception_type':type(exc).__name__})
            raise
        if fit_observer is not None:
            details=result[1] if kind=='head' else {}
            fit_observer('completed',kind,name,details)
        return result
    def transform(name,x,pca=None):
        t=tracked('transform',name,lambda:Transform.fit(x[a],groups[a],pca=pca));transforms[name]=t
        return t.apply(x)
    hh=transform('H',h);hb=h_basis(hh)
    pp=transform('P',p,pca=8);nn=transform('NOISE',noise,pca=8)
    def base(name,x):
        nonlocal calibration_fits
        theta,receipt=tracked('head',name,lambda:fit_head(x[a],y[a],groups[a],lam=lam,maxiter=maxiter))
        receipt.update(name=name,role='A');receipts.append(receipt);models[name]=theta
        raw=predict_head(theta,x)
        t=tracked('calibration',name,lambda:calibrate(raw[cal],y[cal],groups[cal]));temps[name]=t;calibration_fits+=1
        return raw/t
    def corrections(tag,offsets,x):
        # Two N1 offsets share exactly the same residual input scaling.
        tr=tracked('transform',tag+'_residual',lambda:Transform.fit(x[c],groups[c]));transforms[tag+'_residual']=tr;x=tr.apply(x)
        all_candidates=[]
        # Order all unmodified baselines first, so exact ties prefer them.
        for name,z in offsets:all_candidates.append((name+'_alpha0',z))
        for name,z in offsets:
            theta,receipt=tracked('head',tag+'_'+name,lambda:fit_head(x[c],y[c],groups[c],offset=z[c],lam=lam,maxiter=maxiter))
            receipt.update(name=tag+'_'+name,role='C');receipts.append(receipt);models[tag+'_'+name]=theta
            residual=predict_head(theta,x)
            for alpha in (.5,1.):all_candidates.append((name+f'_alpha{alpha}',z+alpha*residual))
        selected,scores=choose([(name,z[d]) for name,z in all_candidates],y[d],groups[d])
        return dict(selected=all_candidates[selected][0],selection_losses=scores,
                    candidate_names=[name for name,_ in all_candidates],
                    candidate_test_logits=np.stack([z[e] for _,z in all_candidates]),
                    logit=all_candidates[selected][1][e])
    if packet=='N3':
        qh=base('H',hb)
        # H copies have the same raw width as P, and the same fitted PCA width.
        duplicate=np.tile(h,(1,int(np.ceil(p.shape[1]/h.shape[1]))))[:,:p.shape[1]]
        dd=transform('DUPLICATE',duplicate,pca=8)
        fits={name:corrections(name,[('H',qh)],residual_map(hh,x)) for name,x in (('HP',pp),('Hnoise',nn),('Hdup',dd))}
        baseline={'H':qh[e]}
    else:
        bb=transform('B',b,pca=8)
        qhp=base('HP',np.c_[hb,pp]);qhb=base('HB',np.c_[hb,bb]);qhn=base('HBnoise',np.c_[hb,nn])
        fits={name:corrections(name,[('HP',qhp),(other,z)],residual_map(hh,pp,x))
              for name,other,z,x in (('HPB','HB',qhb,bb),('HPBnoise','HBnoise',qhn,nn),('HPP','HP_duplicate',qhp,pp))}
        baseline={'HP':qhp[e],'HB':qhb[e]}
    for result in fits.values():
        if not np.isfinite(result['candidate_test_logits']).all():raise FloatingPointError('NONFINITE_CANDIDATE')
    return dict(packet=packet,baseline=baseline,enhanced=fits,head_receipts=receipts,
                head_fits=len(receipts),calibration_fits=calibration_fits,
                transform_fits=len(transforms),temperatures=temps,models=models,transforms=transforms,
                role_counts={k:dict(groups=int(len(np.unique(groups[ix]))),rows=len(ix)) for k,ix in roles.items()},
                finite_prediction_status='PASS',budget_execution_status='COMPLETE',
                encoder_scope_checked=bool(real),calibration_status='BOUNDED_OPTIMIZATION_COMPLETE',
                estimator_status='FINITE_BUDGET_ESTIMATOR')
