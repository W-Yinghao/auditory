"""Metadata-only cohort, scope, split and quartet support freeze."""
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold
from .runtime import digest,write_json,require_slurm,safe_run


def make_splits(members,legacy_folds,seed=63011):
    groups=set(members.split_group_id.astype(str));mapping={}
    folds=[]
    for legacy in legacy_folds['folds']:
        number=int(legacy['outer_fold'])
        train=sorted(groups&set(map(str,legacy['train_groups'])))
        test=sorted(groups&set(map(str,legacy['test_groups'])))
        if set(train)&set(test) or set(train)|set(test)!=groups:raise ValueError('OUTER_IDENTITY_MAPPING')
        for g in test:
            if g in mapping:raise ValueError('DUPLICATE_OUTER_TEST_IDENTITY')
            mapping[g]=number
        inner=[]
        garray=np.asarray(train)
        for j,(a,b) in enumerate(GroupKFold(n_splits=3).split(np.zeros((len(train),1)),groups=garray)):
            inner.append(dict(inner_fold=j,fit_groups=garray[a].tolist(),validation_groups=garray[b].tolist(),
                support=len(a)>=12 and len(b)>=4))
        nval=max(5,math.ceil(.2*len(train)))
        ordered=sorted(train,key=lambda g:hashlib.sha256(f'{seed}|{number}|{g}'.encode()).hexdigest())
        val=sorted(ordered[:nval]);fit=sorted(set(train)-set(val))
        folds.append(dict(outer_fold=number,train_groups=train,test_groups=test,inner_folds=inner,
            R3_fit_groups=fit,R3_validation_groups=val,
            outer_support=len(train)>=20 and len(test)>=4,
            N2R_support=all(x['support'] for x in inner),
            R3_support=len(train)>=21 and len(fit)>=16 and len(val)>=5))
    if len(folds)!=5 or set(mapping)!=groups:raise ValueError('INCOMPLETE_OUTER_FOLDS')
    return dict(folds=folds,group_to_outer_fold=mapping,inner_seed=seed,
        inner_hash_rule='SHA256 UTF8 seed|outer_fold|identity_id; ascending hexadecimal',population='P_MATCH_bal')


def validate_bags(frame,cells):
    if not frame.trial_id.is_unique or frame.trial_id.isna().any():raise ValueError('DUPLICATE_OR_MISSING_TRIAL')
    if not frame.stimulus_local_id.isin([0,1]).all():raise ValueError('BAD_LABEL')
    group_cols=['candidate_id','split_group_id','record_id','segment_id','A_half','previous_code','previous_run_bin','stimulus_local_id']
    for _,part in frame.groupby('bag_id'):
        if len(part)!=8 or not part.k.eq(8).all():raise ValueError('BAG_K')
        if any(part[c].nunique(dropna=False)!=1 for c in group_cols):raise ValueError('BAG_MIXED_CELL')
        counts=part.physical_block_id.value_counts()
        if len(counts)<2 or counts.max()>4:raise ValueError('BAG_BLOCK_QUOTA')
    b=frame.drop_duplicates('bag_id')
    keys=['candidate_id','A_half','previous_code','previous_run_bin']
    counts=b.groupby(keys+['stimulus_local_id'],dropna=False).size().unstack(fill_value=0)
    if set(counts.columns)!={0,1} or not counts[0].eq(counts[1]).all():raise ValueError('UNBALANCED_CELL_BAGS')
    halves=b.groupby(['candidate_id','A_half','stimulus_local_id']).size().unstack(fill_value=0)
    if (halves<2).any().any():raise ValueError('HALF_MIN_BAGS')
    group_halves=b.groupby('split_group_id').A_half.agg(lambda x:set(x))
    if not group_halves.map(lambda x:x=={0,1}).all():raise ValueError('MISSING_HALF')
    expected=cells[(cells.candidate_id.isin(frame.candidate_id))&(cells.paired_bag_count>0)]
    actual=set(map(tuple,b[keys].drop_duplicates().to_numpy()))
    wanted=set(map(tuple,expected[keys].drop_duplicates().to_numpy()))
    if actual!=wanted or not expected.source_threshold_ok.all():raise ValueError('ELIGIBLE_CELL_COVERAGE')
    return dict(bags=len(b),trials=len(frame),identity_groups=frame.split_group_id.nunique(),all_bags_k8=True,exact_matched_cells_preserved=True)


def freeze_support(root,private,public,report,config,args):
    require_slurm()
    origin=root/'private/auditory_v3'/safe_run(args['registry_run'])
    completion=json.loads((origin/'completion.json').read_text())
    if completion['status']!='SOURCE_REGISTRY_RESOLVED':raise ValueError('REGISTRY_NOT_RESOLVED')
    registry=json.loads((origin/'source_registry.json').read_text())
    for item in registry['sources'].values():
        if digest(item['path'])!=item['sha256']:raise ValueError('REGISTERED_INPUT_CHANGED')
    def path(role):return Path(registry['sources'][role]['path'])
    members=pd.read_parquet(origin/'members_unjoined.parquet')
    columns=['trial_id','record_id','segment_id','candidate_id','split_group_id','stimulus_local_id','A_half','A_block_id','accepted','stored_epoch_index','post_start_index','onset_seconds_relative','previous_code','previous_run_bin','previous_gap_s','position_fraction','filter_support_seconds','history_chain_complete','raw_dependency_start','raw_dependency_end']
    history=pd.read_parquet(path('full_event_history'),columns=columns)
    if not history.trial_id.is_unique:raise ValueError('HISTORY_TRIAL_NONUNIQUE')
    joined=members.merge(history,on='trial_id',how='left',validate='one_to_one',suffixes=('','_history'),indicator=True)
    if not joined['_merge'].eq('both').all():raise ValueError('UNMATCHED_HISTORY_TRIAL')
    for c in set(columns)&set(members.columns)-{'trial_id'}:
        equal=joined[c].eq(joined[c+'_history']) | (joined[c].isna() & joined[c+'_history'].isna())
        if not equal.all():raise ValueError('HISTORY_ALIGNMENT:'+c)
        joined=joined.drop(columns=[c+'_history'])
    joined=joined.drop(columns=['_merge']).sort_values('trial_id').reset_index(drop=True)
    if not joined.accepted.all() or not joined.history_chain_complete.all():raise ValueError('REJECTED_OR_INCOMPLETE_HISTORY')
    joined['epoch_start_s']=joined.onset_seconds_relative-.2
    joined['epoch_end_s']=joined.onset_seconds_relative+.5
    joined['class']=joined.stimulus_local_id
    joined['onset_s']=joined.onset_seconds_relative
    cells=pd.read_parquet(path('common_cell_support'))
    bag_check=validate_bags(joined,cells)
    splits=make_splits(joined,json.loads(path('legacy_outer_folds').read_text()),config['splits']['R3']['inner_seed'])
    joined['outer_fold']=joined.split_group_id.map(splits['group_to_outer_fold'])
    joined.to_parquet(private/'members.parquet',index=False)
    h=pd.read_parquet(path('matched_bag_history'))
    h=h[h.bag_id.isin(joined.bag_id)].copy();h.to_parquet(private/'bag_history.parquet',index=False)
    write_json(private/'splits.json',splits)
    p0=[];private_scopes=[]
    from auditory_v21.input_preflight import _scope_receipt
    scopes=json.loads(path('legacy_scope_registry').read_text())
    lookup={r.get('task',r.get('name')):r for r in scopes}
    planhash=registry['sources']['legacy_representation_plan']['sha256']
    for lane in registry['legacy_features']:
        task=lane['task'];folder=Path(lane['files']['task.json']['path']).parent
        for f in lane['files'].values():
            if digest(f['path'])!=f['sha256']:raise ValueError('LEGACY_FEATURE_CHANGED')
        receipt=_scope_receipt(folder.parent,task['name'],task['mode'],{},lookup.get(task['name'],{}),planhash,task)
        actual=set(receipt['actual_train_groups']);scaled=set(receipt['scaler_train_groups'])
        fold=splits['folds'][int(task['outer_fold'])]
        test=set(fold['test_groups'])
        scope_ok=not ((actual|scaled)&test) and receipt['task_identity_match'] and receipt['plan_hash_match'] and receipt['completion_status']=='PASS'
        if task['mode']!='L0':scope_ok &= receipt['status']=='PASS' and receipt['scope_hash_match']
        rows=pd.read_parquet(folder/'feature_rows.parquet',columns=['trial_id','split_group_id','stimulus_local_id'])
        if not rows.trial_id.is_unique:raise ValueError('FEATURE_ROW_NONUNIQUE')
        check=joined[['trial_id','split_group_id','stimulus_local_id']].merge(rows,on='trial_id',how='left',suffixes=('','_feature'),validate='one_to_one')
        aligned=check.split_group_id.eq(check.split_group_id_feature)&check.stimulus_local_id.eq(check.stimulus_local_id_feature)
        private_scopes.append(dict(task=task['name'],receipt=receipt,missing_trial_ids=check.loc[~aligned,'trial_id'].tolist()))
        p0.append(dict(mode=task['mode'],outer_fold=task['outer_fold'],scope_safe=bool(scope_ok),matched_trials=int(aligned.sum()),required_trials=len(joined),status='SUFFICIENT' if scope_ok and aligned.all() else 'LIMITED'))
    write_json(private/'p0_scope_receipts.json',private_scopes)
    pd.DataFrame(p0).to_csv(public/'P0_input_support.csv',index=False)
    exports=[]
    for item in registry['processed_epochs']:
        fs=item['files'];summary=json.loads(Path(fs['summary.json']['path']).read_text())
        if summary['bank']!='P1_CAUSAL20' or summary['processed_fs']!=250 or len(summary['branch_channels']['all'])!=20:raise ValueError('EPOCH_DEFINITION_CHANGED')
        for name in ('all.npy','events.parquet'):
            if digest(fs[name]['path'])!=fs[name]['sha256'] or fs[name]['sha256']!=summary['output_sha256'][name]:raise ValueError('EPOCH_OUTPUT_HASH_CHANGED')
        events=pd.read_parquet(fs['events.parquet']['path'])
        need=joined[joined.record_id==item['record_id']]
        ev=events.set_index('trial_id').loc[need.trial_id]
        if not ev.accepted.all() or not np.array_equal(ev.stored_epoch_index,need.stored_epoch_index):raise ValueError('EPOCH_INDEX_ALIGNMENT')
        if not ev.pre_stop_index.eq(50).all() or not ev.post_start_index.eq(need.post_start_index.to_numpy()).all():raise ValueError('WINDOW_INDEX_ALIGNMENT')
        exports.append(dict(record_id=item['record_id'],channels=summary['branch_channels']['all'],filter_support_seconds=summary['filter_support_seconds']))
    if any(e['channels']!=exports[0]['channels'] for e in exports):raise ValueError('CHANNEL_ORDER_CHANGED')
    write_json(private/'epoch_contract.json',dict(processed_hz=250,channels=exports[0]['channels'],units='uV',unit_evidence='Executed HA export requires pyedflib physical dimension uV and does not rescale units.',post_shape=[20,100],pre_shape=[20,50],post_interval=[.05,.45],pre_interval=[-.2,0],effective_support_max_seconds=max(e['filter_support_seconds'] for e in exports),offline_record_qc_inherited=True))
    from .representation_data import quartet_support
    minimum=max(config['R3']['minimum_positive_separation_seconds'],max(e['filter_support_seconds'] for e in exports))
    qs=quartet_support(joined,support_s=minimum)
    qs.to_parquet(private/'quartet_cell_support.parquet',index=False)
    quartet_ok=bool(len(qs)>0 and qs.quartet_eligible.all())
    table=[]
    for f in splits['folds']:
        table.append(dict(outer_fold=f['outer_fold'],train_groups=len(f['train_groups']),test_groups=len(f['test_groups']),N2R_min_inner_fit_groups=min(len(x['fit_groups']) for x in f['inner_folds']),N2R_min_inner_validation_groups=min(len(x['validation_groups']) for x in f['inner_folds']),R3_fit_groups=len(f['R3_fit_groups']),R3_validation_groups=len(f['R3_validation_groups']),outer_support=f['outer_support'],N2R_support=f['N2R_support'],R3_split_support=f['R3_support']))
    pd.DataFrame(table).to_csv(public/'input_support_aggregate.csv',index=False)
    write_json(private/'source_registry.json',registry)
    p0ok=all(r['status']=='SUFFICIENT' for r in p0)
    summary=dict(status='SUPPORT_FROZEN',population='P_MATCH_bal',**bag_check,
        P0_support='SUFFICIENT' if p0ok and all(f['outer_support'] for f in splits['folds']) else 'LIMITED',
        N2R_support='SUFFICIENT' if all(f['outer_support'] and f['N2R_support'] for f in splits['folds']) else 'LIMITED',
        R3_support='SUFFICIENT' if quartet_ok and all(f['outer_support'] and f['R3_support'] for f in splits['folds']) else 'LIMITED',
        R3_quartet_cells=len(qs),R3_supported_cells=int(qs.quartet_eligible.sum()),positive_pair_minimum_seconds=minimum,
        members_sha256=digest(private/'members.parquet'),splits_sha256=digest(private/'splits.json'),new_model_fits=0,clinical_values_read=False)
    (report/'SUPPORT_FREEZE.md').write_text('# v3支持冻结\n\n保留原匹配袋、49候选口径与旧身份外折；新内层分折仅使用身份元数据。P0逐lane来源与R3逐格四元组支持分别记录，不将一个包的支持当另一个包的门槛。具体身份、缺项和时间映射仅在private。\n')
    return summary
