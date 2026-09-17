"""Frozen donor-support controls, including matched training and reference fits."""
import numpy as np
import pandas as pd
from .context_inputs import donor_indices,fit_context_inputs
from .readouts import population_weights


AUX_VIEWS=('HPB_training_child_donor','HPB_donor_support_reference')


def prepare_matched(h,p,b,rows,fitmask,evalmask,scope,feature_scope_id,prefix):
    pool=rows.loc[fitmask].reset_index(drop=True)
    donors,counts=donor_indices(rows,pool,role='training_child')
    available=donors>=0
    count=rows.loc[available].groupby(['split_group_id','stimulus_local_id']).size().unstack(fill_value=0)
    good=set(count.index[(count.get(0,0)>=20)&(count.get(1,0)>=20)])
    mask=available & rows.split_group_id.isin(good).to_numpy()
    train=fitmask&mask;test=evalmask&mask
    if rows.loc[train,'split_group_id'].nunique()<12 or rows.loc[test,'split_group_id'].nunique()<2:
        raise ValueError('N1_MATCHED_DONOR_SUPPORT_INSUFFICIENT')
    y=rows.stimulus_local_id.to_numpy(int);g=rows.split_group_id.to_numpy(str)
    w=population_weights(y[train],g[train],'P_nat')
    donor_b=b[fitmask][np.maximum(donors,0)]
    auxscope={**scope,'fit_groups':sorted(set(g[train]))}
    cases=[];evaluation={};transforms={}
    for view,bb in zip(AUX_VIEWS,(donor_b,b)):
        t=fit_context_inputs(h[train],p[train],bb[train],w,mode='R_SIM')
        x=np.c_[t['H'].transform(h),t['P'].transform(p),t['B'].transform(bb)]
        identifier=prefix+'_mlp32_'+view
        cases.append(dict(id=identifier,family='mlp32',x=x[train],y=y[train],weights=w,scope=auxscope,
                          feature_scope_id=feature_scope_id,width=32))
        evaluation[identifier]=dict(x=x[test],rows=rows.loc[test,['trial_id','record_id','split_group_id','stimulus_local_id']].reset_index(drop=True),view=view)
        transforms[view]=t
    definition=dict(query_trial_ids=rows.trial_id.to_numpy(str),donor_trial_ids=pool.trial_id.to_numpy(str)[np.maximum(donors,0)],
                    donor_available=available,donor_alternative_counts=counts,fit_mask=train,evaluation_mask=test,
                    selection='past code/run/layout, nearest past gap, query-hash rotation; no current labels in donor match',
                    support='>=20 observations of each class per group after donor availability',
                    transforms=transforms)
    return cases,evaluation,definition


def fixed_head_inputs(record):
    """Evaluate original head on unchanged P/H with three B assignments."""
    m=record['common'];same=record['same'][m];cross=record['cross'][m]
    if np.any(same<0) or np.any(cross<0):raise ValueError('DONOR_COMMON_MASK')
    hp=record['hp'][m];pp=record['pp'][m]
    return {'actual_B':np.c_[hp,pp,record['bp_query'][m]],
            'same_child_B':np.c_[hp,pp,record['bp_query'][same]],
            'training_child_B':np.c_[hp,pp,record['bp_fit'][cross]]}
