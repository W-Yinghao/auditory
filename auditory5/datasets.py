"""Immutable EEG-only views from reviewed exports; no clinical fields loaded."""
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd
from auditory5.provenance import ROOT

@dataclass
class EEGDataset:
    X: np.ndarray
    y: np.ndarray
    groups: np.ndarray
    trial_ids: np.ndarray
    record_ids: np.ndarray
    onset_seconds: np.ndarray
    rows: pd.DataFrame

    def subset_groups(self,groups):
        m=np.isin(self.groups,list(groups));return EEGDataset(self.X[m],self.y[m],self.groups[m],self.trial_ids[m],self.record_ids[m],self.onset_seconds[m],self.rows.loc[m].reset_index(drop=True))


def load_dataset(export_run,support,branch='all',window='post',route='general',groups=None):
    bank='P1_CAUSAL20' if branch=='all' else 'P2_SPATIAL_SPLIT'
    if branch not in ['all','left','right'] or window not in ['post','pre','epoch']:raise ValueError('unknown EEG view')
    selected=support[support[route]].sort_values('record_id')
    if groups is not None:selected=selected[selected.split_group_id.isin(groups)]
    arrays=[];frames=[]
    for record in selected.to_dict('records'):
        dest=ROOT/'private/auditory5_v1/data'/export_run/bank/record['record_id']
        rows=pd.read_parquet(dest/'events.parquet');rows=rows[rows.accepted].copy()
        arr=np.load(dest/(branch+'.npy'),mmap_mode='r');indices=rows.stored_epoch_index.to_numpy(int)
        x=np.array(arr[indices],dtype=np.float32)
        if window=='pre':x=x[:,:,:50]
        if window=='post':
            starts=rows.post_start_index.to_numpy(int);x=np.stack([xx[:,start:start+100] for xx,start in zip(x,starts)])
        if not len(x) or not np.isfinite(x).all():raise ValueError('invalid accepted EEG')
        arrays.append(x);frames.append(rows)
    if not arrays:raise ValueError('SUPPORT_INSUFFICIENT: empty selected EEG')
    rows=pd.concat(frames,ignore_index=True)
    # Record metadata stays for downstream grouping/diagnostics, not input tensors.
    forbidden=['MUSS','age_months','duration_months','better_ear_4freq_source_units']
    assert not any(k in rows.columns for k in forbidden)
    assert rows.trial_id.is_unique
    return EEGDataset(np.concatenate(arrays),rows.stimulus_local_id.to_numpy(int),rows.split_group_id.to_numpy(str),
                      rows.trial_id.to_numpy(str),rows.record_id.to_numpy(str),rows.onset_seconds_relative.to_numpy(float),rows)
