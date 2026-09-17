"""Past-only context views, deterministic noise and outcome-blind donors."""
import hashlib
import numpy as np
import pandas as pd
from .history import history_feature_columns
from .fitting import WeightedTransform


def history_matrix(rows):
    columns=[c for c in history_feature_columns(rows) if c!='layout_id']
    if not columns or any(not pd.api.types.is_numeric_dtype(rows[c]) for c in columns):
        raise ValueError('H_NUMERIC_PREDICTOR_WHITELIST')
    x=rows[columns].to_numpy(float)
    if np.isinf(x).any():raise ValueError('H_INFINITE_INPUT')
    # Missing continuous values have separately frozen missing indicators;
    # zero is a fixed missing placeholder, not a statistic fitted on test data.
    return np.nan_to_num(x,nan=0.),columns


def independent_noise(trial_ids,dimension,*,namespace='Bnoise',seed=11):
    return np.stack([np.random.default_rng(int(hashlib.sha256(f'{seed}|{namespace}|{tid}'.encode()).hexdigest()[:16],16)).normal(size=dimension) for tid in trial_ids])


def context_views(h,p,b,noise,packet):
    if len({len(x) for x in (h,p,b,noise)})!=1:raise ValueError('CONTEXT_INPUT_ALIGNMENT')
    if packet=='N1':
        return {'H':h,'HP':np.c_[h,p],'HB':np.c_[h,b],'HPB':np.c_[h,p,b],
                'HPP':np.c_[h,p,p],'HPBnoise':np.c_[h,p,noise]}
    if packet=='N3':
        return {'H':h,'HP':np.c_[h,p],'HB':np.c_[h,b],'HBP':np.c_[h,b,p],'Hnoise':np.c_[h,noise]}
    raise ValueError('CONTEXT_PACKET')


def fit_context_inputs(h,p,b,weights,*,mode):
    return {key:WeightedTransform(32 if mode=='L0' and key in ('P','B') else None).fit(x,weights)
            for key,x in (('H',h),('P',p),('B',b))}


def donor_indices(queries,pool,*,role):
    """Return pool-relative indices without reading current labels or model scores.

    Index by past-code/run/layout first, rank valid candidates by past-gap
    distance and a query-hash rotation of sorted trial IDs. Same-source raw interval overlap is
    excluded; different sources do not share a relative-time coordinate.
    """
    if role not in ('same_child','training_child'):raise ValueError('DONOR_ROLE')
    required=['trial_id','candidate_id','split_group_id','record_id','segment_id','previous_code',
              'previous_run_bin','layout_id','previous_gap_s','raw_dependency_start','raw_dependency_end','time_block_id']
    if any(c not in queries or c not in pool for c in required):raise ValueError('DONOR_SCHEMA')
    if not queries.trial_id.is_unique or not pool.trial_id.is_unique:raise ValueError('DONOR_DUPLICATE_TRIAL')
    rows=pool[required].reset_index(drop=True)
    arrays={key:rows[key].to_numpy() for key in required}
    bucket={}
    for key,part in rows.groupby(['previous_code','previous_run_bin','layout_id'],sort=False,dropna=False):
        bucket[key]=part.index.to_numpy()
    result=np.full(len(queries),-1,int);counts=np.zeros(len(queries),int)
    for number,q in enumerate(queries[required].itertuples(index=False)):
        ix=bucket.get((q.previous_code,q.previous_run_bin,q.layout_id),np.array([],int))
        if not len(ix):continue
        allowed=arrays['trial_id'][ix]!=q.trial_id
        if role=='same_child':allowed &= arrays['candidate_id'][ix]==q.candidate_id
        else:allowed &= (arrays['candidate_id'][ix]!=q.candidate_id)&(arrays['split_group_id'][ix]!=q.split_group_id)
        same=(arrays['record_id'][ix]==q.record_id)&(arrays['segment_id'][ix]==q.segment_id)
        if role=='same_child':allowed &= ~(same&(arrays['time_block_id'][ix]==q.time_block_id))
        overlap=same&(arrays['raw_dependency_start'][ix]<q.raw_dependency_end)&(arrays['raw_dependency_end'][ix]>q.raw_dependency_start)
        allowed &= ~overlap
        valid=ix[allowed]
        counts[number]=len(valid)
        if not len(valid):continue
        earlier=(arrays['record_id'][valid]==q.record_id)&(arrays['segment_id'][valid]==q.segment_id)&(arrays['raw_dependency_end'][valid]<=q.raw_dependency_start)
        if role=='same_child' and earlier.any():valid=valid[earlier]
        gaps=arrays['previous_gap_s'][valid].astype(float)
        distance=abs(gaps-float(q.previous_gap_s)) if pd.notna(q.previous_gap_s) else np.where(np.isnan(gaps),0.,np.inf)
        if not np.isfinite(distance).any():continue
        tied=valid[distance==np.nanmin(distance)]
        tied=tied[np.argsort(arrays['trial_id'][tied])]
        rotation=int.from_bytes(hashlib.sha256(f'20260917|{q.trial_id}'.encode()).digest()[:8],'big')%len(tied)
        result[number]=tied[rotation]
    return result,counts
