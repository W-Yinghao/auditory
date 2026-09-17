"""Audited tabular fitting with a single family-wide numerical extension."""
import json
import pickle
import warnings
import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import ConvergenceWarning
from .readouts import start_fit,advance_fit,stability
from .provenance import digest,object_hash,write_json,require_slurm


def array_hash(array):
    import hashlib
    a=np.ascontiguousarray(array)
    h=hashlib.sha256(str((str(a.dtype),a.shape)).encode());h.update(a.tobytes())
    return h.hexdigest()


class WeightedTransform:
    def __init__(self,max_components=None):self.max_components=max_components

    def fit(self,x,w):
        x=np.asarray(x,float);w=np.asarray(w,float)
        if x.ndim!=2 or w.shape!=(len(x),) or not np.isfinite(x).all() or np.any(w<=0):raise ValueError('TRANSFORM_SCHEMA')
        w=w/w.sum();self.mean=np.sum(x*w[:,None],axis=0)
        v=np.sum((x-self.mean)**2*w[:,None],axis=0)
        self.keep=v>np.finfo(float).eps
        # An intercept-only H is a legitimate baseline. Keep one all-zero
        # coordinate so the same head API can represent the constant prior.
        if not self.keep.any():self.keep[0]=True
        self.scale=np.sqrt(np.maximum(v[self.keep],np.finfo(float).eps))
        z=(x[:,self.keep]-self.mean[self.keep])/self.scale
        self.components=None
        if self.max_components is not None:
            cov=(z*w[:,None]).T@z
            eig,vec=np.linalg.eigh(cov);order=np.argsort(eig)[::-1]
            rank=max(1,int((eig>max(float(eig.max()),1e-12)*1e-10).sum()))
            k=min(self.max_components,len(self.scale),len(x)-1,rank)
            self.components=vec[:,order[:k]].T
            for row in self.components:
                if row[np.argmax(abs(row))]<0:row*=-1
        return self

    def transform(self,x):
        x=np.asarray(x,float)
        if x.ndim!=2 or x.shape[1]!=len(self.mean) or not np.isfinite(x).all():raise ValueError('TRANSFORM_INPUT')
        z=(x[:,self.keep]-self.mean[self.keep])/self.scale
        return z if self.components is None else z@self.components.T


def fit_cases(cases,dest,*,device='cpu',expected_fits=None,legacy=False):
    """Fit every specified case, then extend ALL neural cases if any is unstable.

    Cases contain training inputs only. Test labels and evaluation matrices
    are not arguments. Known numerical failure remains in the entire matrix.
    """
    require_slurm()
    if expected_fits is not None and len(cases)!=expected_fits:raise ValueError('TASK_PLAN_FIT_COUNT_MISMATCH')
    if len({c['id'] for c in cases})!=len(cases):raise ValueError('DUPLICATE_FIT_UNIT')
    dest.mkdir(parents=True,exist_ok=False)
    models={};receipts=[];neural=[]
    for c in cases:
        identifier=c['id'];folder=dest/identifier;folder.mkdir()
        x,y,w=c['x'],c['y'],c['weights'];scope=c['scope']
        if set(scope['fit_groups']) & (set(scope.get('validation_groups',[]))|set(scope.get('test_groups',[]))):
            raise ValueError('HEAD_SCOPE_OVERLAP')
        receipt=dict(fit_id=identifier,family=c['family'],scope=scope,scope_hash=object_hash(scope),
                     feature_hash=array_hash(x),label_hash=array_hash(y),weight_hash=array_hash(w),
                     n_training_observations=len(y),n_features=np.shape(x)[1],seed=11,
                     feature_scope_id=c['feature_scope_id'],objective='legacy_alpha' if legacy else 'new_fixed_lambda_or_C')
        write_json(folder/'start.json',receipt)
        try:
            if c['family']=='logistic':
                head=LogisticRegression(C=c.get('C',1.),solver='lbfgs',max_iter=5000,tol=1e-7,random_state=11)
                with warnings.catch_warnings():
                    warnings.simplefilter('error',ConvergenceWarning)
                    head.fit(x,y,sample_weight=w)
                if not np.isfinite(head.coef_).all():raise ValueError('OPTIMIZATION_NONFINITE')
                models[identifier]=head;receipt['numerical_status']='OPTIMIZATION_STABLE'
                receipt['iterations']=int(head.n_iter_.max())
                with (folder/'model.pkl').open('xb') as f:pickle.dump(head,f)
            else:
                kwargs={'alpha':c['alpha']} if legacy else {'lam':.001}
                state=start_fit(x,y,w,width=c.get('width',32),device=device,fit_scope_hash=receipt['scope_hash'],**kwargs)
                models[identifier]=state;neural.append((c,receipt))
                advance_fit(state,x,y,w,target_steps=1000,fit_scope_hash=receipt['scope_hash'])
                receipt['numerical_status']=stability(state)['status']
                torch.save(state,folder/'adam_1000.pt')
                write_json(folder/'numerics_1000.json',stability(state))
        except (ConvergenceWarning,FloatingPointError,ValueError,RuntimeError) as exc:
            if isinstance(exc,ValueError) and str(exc) not in ('OPTIMIZATION_NONFINITE','FINAL_OPTIMIZATION_NONFINITE'):
                raise
            if isinstance(exc,RuntimeError) and not any(s in str(exc).lower() for s in ('non-finite','nonfinite')):
                raise
            receipt.update(numerical_status='OPTIMIZATION_UNRESOLVED',failure_type=type(exc).__name__,failure_message=str(exc))
            if identifier in models and c['family']!='logistic':torch.save(models[identifier],folder/'failed_state.pt')
        write_json(folder/'initial_receipt.json',receipt)
        receipts.append(receipt)
    extend=any(r['numerical_status']!='OPTIMIZATION_STABLE' for c,r in neural)
    if extend:
        for c,r in neural:
            state=models[c['id']]
            if state.steps!=1000:
                r['extension_status']='NO_RESUMABLE_INITIAL_BUDGET';continue
            try:
                advance_fit(state,c['x'],c['y'],c['weights'],target_steps=2000,fit_scope_hash=r['scope_hash'])
                r['numerical_status']=stability(state)['status']
            except (ValueError,RuntimeError,FloatingPointError) as exc:
                if isinstance(exc,ValueError) and str(exc) not in ('OPTIMIZATION_NONFINITE','FINAL_OPTIMIZATION_NONFINITE'):raise
                if isinstance(exc,RuntimeError) and not any(s in str(exc).lower() for s in ('non-finite','nonfinite')):raise
                r.update(numerical_status='OPTIMIZATION_UNRESOLVED',failure_type=type(exc).__name__,failure_message=str(exc))
            torch.save(state,dest/c['id']/'adam_2000.pt')
            write_json(dest/c['id']/'numerics_2000.json',stability(state))
    for c,r in zip(cases,receipts):
        folder=dest/c['id'];model=models.get(c['id'])
        if c['family']!='logistic' and model is not None:
            r['optimization']=stability(model)
            write_json(folder/'training_curve.json',model.history)
            # Save both optimizer and actual final parameter state for auditing;
            # this is a receipt, never an excuse for a third optimization pass.
            torch.save(model,folder/'adam_state.pt')
        r.update(family_extension_used=extend if c['family']!='logistic' else False,train_only_extension_decision=True)
        write_json(folder/'completion.json',r)
    write_json(dest/'family_status.json',dict(planned_fits=len(cases),actual_fits=len(receipts),
        neural_fits=len(neural),extended_all_neural=extend,complete=all(r['numerical_status']=='OPTIMIZATION_STABLE' for r in receipts)))
    return models,receipts


def predict_logits(model,x):
    if isinstance(model,LogisticRegression):return model.decision_function(x)
    model.model.eval();device=next(model.model.parameters()).device
    result=[]
    with torch.no_grad():
        for first in range(0,len(x),8192):result.append(model.model(torch.as_tensor(x[first:first+8192],dtype=torch.float64,device=device)).cpu().numpy())
    return np.concatenate(result)
