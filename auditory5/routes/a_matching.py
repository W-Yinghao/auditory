"""A matching matrices and fixed-fold identity bootstrap; no embedding pooling."""
import numpy as np


def mean_matching_matrices(first,second):
    a,b=np.asarray(first,float),np.asarray(second,float)
    if a.ndim!=3 or a.shape!=b.shape or min(a.shape)<1 or not np.isfinite(a).all() or not np.isfinite(b).all():raise ValueError('matching [rep,candidate,feature] arrays required')
    dot=np.einsum('rnd,rmd->rnm',a,b);na=np.linalg.norm(a,axis=-1);nb=np.linalg.norm(b,axis=-1);denom=na[:,:,None]*nb[:,None,:]
    cos=np.divide(dot,denom,out=np.full_like(dot,np.nan),where=denom>0)
    matrices={'cosine':cos.mean(axis=0),'inner_product':dot.mean(axis=0),
              'squared_distance':np.maximum(na[:,:,None]**2+nb[:,None,:]**2-2*dot,0).mean(axis=0)}
    rank={}
    for name,m in matrices.items():
        rr=[]
        for i in range(len(m)):
            if not np.isfinite(m[i]).all():rr.append(np.nan)
            else:rr.append(1+np.sum(m[i]<m[i,i] if name=='squared_distance' else m[i]>m[i,i]))
        rank[name]=float(np.mean(rr))
    matrices.update(mean_diag_rank=rank,norm_summary={'first_mean':float(na.mean()),'second_mean':float(nb.mean()),
        'first_sd':float(na.std()),'second_sd':float(nb.std())},undefined_zero_norm_count=int((na==0).sum()+(nb==0).sum()))
    return matrices


def _fold_stat(matrix,ids,metric='cosine'):
    m=np.asarray(matrix,float);ids=np.asarray(ids)
    if m.shape!=(len(ids),len(ids)):raise ValueError('A matrix identity shape mismatch')
    distinct=ids[:,None]!=ids[None,:]
    if not distinct.any() or not np.isfinite(np.diag(m)).all() or not np.isfinite(m[distinct]).all():return float('nan')
    value=float(np.diag(m).mean()-m[distinct].mean())
    return -value if metric=='squared_distance' else value


def aggregate_match(matrices_by_fold,ids_by_fold,metric='cosine',draws=None):
    if metric not in ['cosine','inner_product','squared_distance'] or len(matrices_by_fold)!=len(ids_by_fold) or not len(matrices_by_fold):raise ValueError('invalid A fold schema')
    values=[_fold_stat(m,i,metric) for m,i in zip(matrices_by_fold,ids_by_fold)]
    weights=[len(ids) for ids in ids_by_fold] if draws is None else draws
    valid=np.isfinite(values)
    return {'estimate':float(np.average(values,weights=weights)) if valid.all() else float('nan'),
            'valid_folds':int(valid.sum()),'total_folds':len(values),'fold_statistics':values}


def bootstrap_match(matrices_by_fold,ids_by_fold,n_boot=2000,seed=20260917,paired_matrices=None):
    if n_boot<1:raise ValueError('positive bootstrap count required')
    base=aggregate_match(matrices_by_fold,ids_by_fold)
    if paired_matrices is not None and len(paired_matrices)!=len(matrices_by_fold):raise ValueError('paired fold mismatch')
    paired_base=aggregate_match(paired_matrices,ids_by_fold) if paired_matrices is not None else None
    rng=np.random.default_rng(seed);draws=[];paired=[];weights=[len(i) for i in ids_by_fold]
    for _ in range(n_boot):
        values=[];other=[]
        for k,(m,ids) in enumerate(zip(matrices_by_fold,ids_by_fold)):
            ids=np.asarray(ids);ix=rng.integers(0,len(ids),len(ids))
            values.append(_fold_stat(np.asarray(m)[np.ix_(ix,ix)],ids[ix]))
            if paired_matrices is not None:other.append(_fold_stat(np.asarray(paired_matrices[k])[np.ix_(ix,ix)],ids[ix]))
        current=float(np.average(values,weights=weights)) if np.isfinite(values).all() else np.nan;draws.append(current)
        if paired_matrices is not None:paired.append(current-float(np.average(other,weights=weights)) if np.isfinite(other).all() else np.nan)
    def ci(values):
        v=np.asarray(values);v=v[np.isfinite(v)]
        return [float(x) for x in np.quantile(v,[.025,.975])] if len(v) else [np.nan,np.nan]
    out={'estimate':base['estimate'],'ci95':ci(draws),'n_boot':n_boot,'invalid_replicates':int((~np.isfinite(draws)).sum())}
    if paired_matrices is not None:out.update(paired_estimate=base['estimate']-paired_base['estimate'],paired_ci95=ci(paired),paired_invalid_replicates=int((~np.isfinite(paired)).sum()))
    return out
