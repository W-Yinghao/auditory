"""Strict trial-ID joins; model-ready arrays have no identifier features."""
import json
from functools import lru_cache
from pathlib import Path
import numpy as np
import pandas as pd
from .runtime import digest,require_slurm,safe_run


def load_support(root,run):
    require_slurm();p=root/'private/auditory_v3'/safe_run(run)
    receipt=json.loads((p/'completion.json').read_text())
    if receipt['status']!='SUPPORT_FROZEN':raise ValueError('SUPPORT_NOT_FROZEN')
    for name,field in [('members.parquet','members_sha256'),('splits.json','splits_sha256')]:
        if digest(p/name)!=receipt[field]:raise ValueError('FROZEN_SUPPORT_CHANGED')
    return pd.read_parquet(p/'members.parquet'),json.loads((p/'splits.json').read_text()),pd.read_parquet(p/'bag_history.parquet'),json.loads((p/'source_registry.json').read_text()),receipt


def feature_loader(members,registry):
    lanes={(lane['task']['mode'],int(lane['task']['outer_fold'])):lane for lane in registry['legacy_features']}
    @lru_cache(maxsize=1)
    def read(mode,fold):
        lane=lanes[(mode,fold)];item=lane['files']['features.npz']
        if digest(item['path'])!=item['sha256']:raise ValueError('LEGACY_ARRAY_CHANGED')
        with np.load(item['path'],allow_pickle=False) as archive:
            arrays={k:archive[k] for k in archive.files}
        ids=pd.Index(arrays['trial_ids'].astype(str))
        if not ids.is_unique:raise ValueError('DUPLICATE_FEATURE_TRIAL')
        ix=ids.get_indexer(members.trial_id.astype(str))
        if (ix<0).any():raise ValueError('P0_MISSING_MATCHED_MEMBER')
        if not np.array_equal(arrays['groups'][ix].astype(str),members.split_group_id.astype(str)) or not np.array_equal(arrays['y'][ix],members.stimulus_local_id):raise ValueError('FEATURE_LABEL_OR_GROUP_ALIGNMENT')
        return {w:arrays[w][ix] for w in ('post','pre')}
    def load(mode,fold,window):
        x=read(mode,int(fold))[window]
        dim=(400 if window=='post' else 200) if mode=='L0' else 64
        if x.shape!=(len(members),dim) or not np.isfinite(x).all():raise ValueError('FEATURE_SHAPE_NONFINITE')
        return x
    return load


def load_epochs(members,registry):
    require_slurm()
    post=np.empty((len(members),20,100),dtype=np.float32)
    pre=np.empty((len(members),20,50),dtype=np.float32)
    covered=np.zeros(len(members),dtype=bool)
    if not np.array_equal(members.index,np.arange(len(members))):raise ValueError('MEMBER_INDEX_NOT_CANONICAL')
    for item in registry['processed_epochs']:
        loc=np.flatnonzero(members.record_id.astype(str).eq(item['record_id']).to_numpy())
        if not len(loc):continue
        if covered[loc].any():raise ValueError('DUPLICATE_EPOCH_SOURCE')
        covered[loc]=True
        info=item['files']['all.npy']
        if digest(info['path'])!=info['sha256']:raise ValueError('EPOCH_ARRAY_CHANGED')
        arr=np.load(info['path'],mmap_mode='r')
        rows=members.iloc[loc]
        for index,row in zip(loc,rows.itertuples(index=False)):
            epoch=arr[int(row.stored_epoch_index)]
            pre[index]=epoch[:,:50]
            start=int(row.post_start_index);post[index]=epoch[:,start:start+100]
    if not covered.all():raise ValueError('MISSING_EPOCH_SOURCE')
    if not np.isfinite(post).all() or not np.isfinite(pre).all():raise ValueError('NONFINITE_MATCHED_EPOCH')
    return post,pre


def l0(post,pre):
    def one(x):
        if x.ndim!=3 or x.shape[1]!=20 or x.shape[2]%5:raise ValueError('L0_INPUT_SHAPE')
        return x.astype(np.float64).reshape(len(x),20,x.shape[2]//5,5).mean(axis=-1).reshape(len(x),-1)
    return one(post),one(pre)


def htrial(members):
    """Frozen explicit previous-history whitelist, 13 coordinates, no target-derived inputs."""
    code=members.previous_code.fillna('unknown').astype(str)
    run=members.previous_run_bin.fillna('unknown').astype(str)
    code=np.where(code.isin(['1','2']),code,'unknown')
    run=np.where(run.isin(['run_1','run_2','run_3_5','run_6_plus']),run,'unknown')
    gap=pd.to_numeric(members.previous_gap_s,errors='coerce').to_numpy(float)
    missing=~np.isfinite(gap);gap=np.where(missing,0,gap)
    if (gap<0).any():raise ValueError('NEGATIVE_PREVIOUS_GAP')
    position=members.position_fraction.to_numpy(float)
    return np.column_stack([(code==v).astype(float) for v in ('1','2','unknown')]+[(run==v).astype(float) for v in ('run_1','run_2','run_3_5','run_6_plus','unknown')]+[np.log1p(gap),missing.astype(float),position,position**2,members.A_half.to_numpy(float)])
