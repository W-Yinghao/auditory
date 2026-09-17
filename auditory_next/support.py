"""Outcome-blind v2 support, complete-chain history and fixed bag partitions."""
from dataclasses import asdict
import json
import pickle
import numpy as np
import pandas as pd

from .provenance import ROOT, digest, object_hash, write_json, finish
from .history import build_h_v2
from .n2_bags import make_n2_bags
from .a2_overlap import freeze_overlap, draw_trials


def qualified_groups(rows, minimum=20, blocks=4):
    result=[]
    for group, part in rows.groupby('split_group_id',sort=True):
        if all((part.stimulus_local_id==label).sum()>=minimum for label in (0,1)) and part.physical_time_block.nunique()>=blocks:
            result.append(str(group))
    return result


def support_status(groups, folds, minimum=20):
    groups=set(groups)
    counts=[dict(outer_fold=f['outer_fold'],train=len(groups & set(f['train_groups'])),test=len(groups & set(f['test_groups']))) for f in folds['folds']]
    return dict(candidates=len(groups), outer_counts=counts, status='SUFFICIENT_FOR_SCREEN' if len(groups)>=minimum and
                all(r['train']>=12 and r['test']>=2 for r in counts) else 'INSUFFICIENT')


def run(config, registry, site, dest, public, report, source_run):
    source_run=source_run or registry['preflight_run']
    gate=ROOT/'private/auditory_next_v2'/source_run
    if json.loads((gate/'completion.json').read_text())['status']!='PASS': raise ValueError('PREFLIGHT_GATE')
    inventory={row['path']:row['sha256'] for row in json.loads((gate/'legacy_input_hashes.json').read_text())}
    planpath=ROOT/registry['legacy_plan']; plan=json.loads(planpath.read_text())
    foldpath=ROOT/registry['legacy_splits']; folds=json.loads(foldpath.read_text())
    support=pd.read_parquet(foldpath.parent/'support.parquet')
    identities=set(folds['outer_fold_by_group'])
    processing={}
    export_bank=ROOT/'private/auditory5_v1/data'/plan['export_run']/'P1_CAUSAL20'
    for config_file in sorted(export_bank.glob('shard_*/config.json')):
        if digest(config_file)!=inventory[str(config_file)]:raise ValueError('PROCESSING_SPEC_CHANGED')
        shard=json.loads(config_file.read_text())
        for rid in shard['selected_record_ids']:processing[rid]=shard['processing']
    pieces=[]; summary=[]; history_checks=[]; common_p2=[]
    for record in support.to_dict('records'):
        if record['split_group_id'] not in identities: continue
        folder=ROOT/'private/auditory5_v1/data'/plan['export_run']/'P1_CAUSAL20'/record['record_id']
        path=folder/'events.parquet'
        if digest(path)!=inventory[str(path)]: raise ValueError('EVENT_INPUT_MUTATED')
        rows=pd.read_parquet(path); s=json.loads((folder/'summary.json').read_text())
        # Do not expose legacy derived current-run or any clinical fields to H.
        fields=['trial_id','record_id','segment_id','onset_sample','event_literal','event_kind','original_fs','segment_position_fraction']
        fields += [c for c in ('storage_gap_before','task_restart_before','sequence_start_complete') if c in rows]
        h=build_h_v2(rows[fields],known_codes=('1','2'))
        for col in ('previous_code','previous_event_id','previous_run_length','previous_gap_s'):
            a,b=rows[col],h[col]
            equal=(a.isna() & b.isna()) | a.eq(b)
            # v1 deliberately blanks previous fields on non-target markers;
            # v2 can describe their incoming chain, then resets future history.
            # Only target-row historical fields are measurement inputs.
            targets=rows.event_kind.eq('target')
            if not equal.loc[targets].all():
                pd.DataFrame({'trial_id':rows.trial_id,'kind':rows.event_kind,'old':a,'rebuilt':b}).loc[targets & ~equal].to_parquet(dest/'history_mismatch.parquet',index=False)
                raise ValueError('HISTORY_REBUILD_DISAGREES_WITH_FULL_CHAIN:'+col)
        keep=['trial_id','record_id','segment_id','candidate_id','split_group_id','stimulus_local_id','accepted',
              'A_boundary_eligible','A_half','A_block_id','time_block_id','stored_epoch_index','post_start_index',
              'onset_seconds_relative','original_fs','segment_position_fraction','event_literal','event_kind']
        merged=rows[keep].copy()
        for column in h:
            if column not in merged: merged[column]=h[column].to_numpy()
        merged['history_chain_complete']=h.previous_run_length.notna().to_numpy() & h.previous_event_id.notna().to_numpy()
        merged['A_boundary_eligible']=merged.A_boundary_eligible.fillna(False).astype(bool)
        merged['accepted']=merged.accepted.astype(bool)
        merged['physical_time_block']=merged.record_id.astype(str)+':'+merged.segment_id.astype(str)+':'+merged.time_block_id.astype(str)
        merged['layout_id']='HA20'
        merged['filter_support_seconds']=float(s['filter_support_seconds'])
        merged['raw_dependency_start']=merged.onset_seconds_relative-.2-float(s['filter_support_seconds'])
        merged['raw_dependency_end']=merged.onset_seconds_relative+.5
        # H dependencies extend back to earliest of the three preceding sounds.
        ordered=merged.sort_values(['segment_id','onset_sample'],kind='stable')
        for _, seg in ordered.groupby('segment_id',sort=False):
            targets=seg[seg.event_kind=='target']
            for lag in (1,2,3):
                earlier=targets.onset_seconds_relative.shift(lag)
                merged.loc[targets.index,'raw_dependency_start']=np.minimum(
                    merged.loc[targets.index,'raw_dependency_start'],earlier.fillna(np.inf))
            # log1p(previous_run_length) can depend on more than three sounds.
            # Include the complete preceding run and the event establishing its
            # start, not merely the last-three-code window.
            run=targets.previous_run_length.to_numpy(float)
            valid=np.isfinite(run)
            starts=np.arange(len(targets))-np.nan_to_num(run,nan=0).astype(int)-1
            starts=np.maximum(starts,0)
            run_onsets=targets.onset_seconds_relative.to_numpy()[starts]
            ix=targets.index[valid]
            merged.loc[ix,'raw_dependency_start']=np.minimum(merged.loc[ix,'raw_dependency_start'],run_onsets[valid])
        merged['selection_dependency_scope']='whole_record_offline_QC'
        # Keep original metadata intact; v2 bag H additionally needs its own
        # complete context within the assigned original alternating block.
        width=float(processing[record['record_id']]['A_block_seconds'])
        merged['v2_context_boundary_eligible']=merged.A_boundary_eligible & (merged.raw_dependency_start>=merged.A_block_id*width)
        pieces.append(merged)
        p2path=folder.parent.parent/'P2_SPATIAL_SPLIT'/record['record_id']/'events.parquet'
        p2=pd.read_parquet(p2path)
        common_p2.extend(sorted(set(rows.loc[rows.accepted,'trial_id']) & set(p2.loc[p2.accepted,'trial_id'])))
        summary.append(dict(n_events=len(rows),n_accepted=int(rows.accepted.sum()),original_fs=s['original_fs'],
                            filter_support_seconds=s['filter_support_seconds'],startup_guard_seconds=s['startup_guard_seconds']))
        history_checks.append(dict(record_id=record['record_id'], n_events=len(rows), target_previous_fields_exact=True,
                                   marker_semantics='v1 blanks incoming history; v2 describes incoming history before resetting'))
    frame=pd.concat(pieces,ignore_index=True)
    if not frame.trial_id.is_unique: raise ValueError('SUPPORT_DUPLICATE_TRIAL')
    frame.to_parquet(dest/'full_event_history.parquet',index=False)
    write_json(dest/'history_checks.json',history_checks)
    write_json(dest/'C2S_common_P1_P2_trials.json',common_p2)
    a2frame=frame.copy()
    a2frame['A_boundary_eligible']=frame.v2_context_boundary_eligible
    frozen=freeze_overlap(a2frame,folds)
    write_json(dest/'A2_overlap.json',asdict(frozen))
    with (dest/'A2_overlap.pkl').open('xb') as f: pickle.dump(frozen,f)
    if frozen.groups:
        draws=draw_trials(frozen)
        np.save(dest/'A2_trial_draws.npy',draws.trial_ids.astype(str),allow_pickle=False)
        write_json(dest/'A2_draw_definition.json',dict(groups=draws.groups,omega=draws.omega,
                   cell_weights=draws.cell_weights,definition_hash=draws.definition_hash,seed=draws.seed))
    arows=[dict(omega='|'.join(r.omega),cells=len(r.omega),candidates=len(r.groups),sufficient=r.sufficient,
                selected=r.omega==frozen.omega,fold_counts=json.dumps(r.fold_counts)) for r in frozen.candidates]
    pd.DataFrame(arows).to_csv(public/'A2_overlap_candidates.csv',index=False)
    eligible=frame[frame.accepted & frame.history_chain_complete & frame.stimulus_local_id.isin([0,1])].copy()
    n1=qualified_groups(eligible)
    write_json(dest/'N1_groups.json',n1)
    n1status=support_status(n1,folds)
    n2_input=frame[frame.accepted & frame.stimulus_local_id.isin([0,1]) & frame.A_half.notna()].copy()
    n2_input['A_half']=n2_input.A_half.astype(int)
    n2_input['A_boundary_eligible']=n2_input.v2_context_boundary_eligible
    n2_input['A_block_id']=n2_input.A_block_id.astype(int)
    n2statuses=[]; n2groups={}
    for k in (1,4,8,16):
        bags,unused=make_n2_bags(n2_input,k=k)
        good=[]
        if len(bags):
            for record,part in bags.groupby('record_id'):
                cells=set(zip(part.A_half,part.stimulus_local_id))
                if cells=={(0,0),(0,1),(1,0),(1,1)}: good.append(record)
            rejected=bags[~bags.record_id.isin(good)][['trial_id']].copy()
            rejected['reason']='record_missing_half_class'; unused=pd.concat([unused,rejected],ignore_index=True)
            bags=bags[bags.record_id.isin(good)].reset_index(drop=True)
        bags.to_parquet(dest/f'N2_k{k}_bags.parquet',index=False)
        unused.to_parquet(dest/f'N2_k{k}_unused.parquet',index=False)
        groups=sorted(bags.split_group_id.unique()) if len(bags) else []
        n2groups[str(k)]=groups
        status=support_status(groups,folds)
        n2statuses.append(dict(k=k,**status,bags=int(bags.bag_id.nunique()) if len(bags) else 0,
                               trials_used=len(bags),trials_unused=len(unused)))
    common=set.intersection(*(set(n2groups[str(k)]) for k in (4,8,16)))
    write_json(dest/'N2_groups.json',dict(by_k=n2groups,common_4_8_16=sorted(common)))
    pd.DataFrame([{k:v for k,v in r.items() if k!='outer_counts'} for r in n2statuses]).to_csv(public/'N2_bag_support.csv',index=False)
    n3=[]; n3folds=[]
    eligible['history_cell']=eligible.previous_code.astype(str)+'|'+eligible.previous_run_bin.astype(str)
    for fold in folds['folds']:
        train=eligible[eligible.split_group_id.isin(fold['train_groups'])]
        omega=[]
        for cell,part in train.groupby('history_cell',sort=True):
            if all((part.stimulus_local_id==k).sum()>=20 and part.loc[part.stimulus_local_id==k,'split_group_id'].nunique()>=5 for k in (0,1)):
                omega.append(cell)
        retained=eligible[eligible.history_cell.isin(omega)]
        groups=qualified_groups(retained,minimum=10)
        tr=sorted(set(groups)&set(fold['train_groups']));te=sorted(set(groups)&set(fold['test_groups']))
        n3folds.append(dict(outer_fold=fold['outer_fold'],omega_H=omega,train_groups=tr,test_groups=te))
        n3.append(dict(outer_fold=fold['outer_fold'],cells=len(omega),training_candidates=len(tr),test_candidates=len(te),
                       retained_training_trials=int((retained.split_group_id.isin(tr)).sum()),retained_test_trials=int((retained.split_group_id.isin(te)).sum())))
    write_json(dest/'N3_outer_support.json',n3folds)
    pd.DataFrame(n3).to_csv(public/'N3_overlap_support.csv',index=False)
    n3test=sum(r['test_candidates'] for r in n3)
    n3status='SUFFICIENT_FOR_SCREEN' if n3test>=20 and all(r['training_candidates']>=12 and r['test_candidates']>=2 for r in n3) else 'INSUFFICIENT'
    aggregates=dict(stage='metadata_support_only',status='PASS',records=len(summary),identity_components=frame.split_group_id.nunique(),
        events=len(frame),accepted=int(frame.accepted.sum()),history_complete_accepted=len(eligible),
        A2=dict(status=frozen.status,candidates=len(frozen.groups),omega=frozen.omega),N1=n1status,N2=n2statuses,
        N2_common_4_8_16=support_status(common,folds),N3=dict(status=n3status,test_candidates=n3test),
        C2S_common_trials=len(common_p2),new_encoder_fits=0,new_readout_fits=0,scientific_effects_viewed=False,
        clinical_inputs=False,source_gate=source_run)
    write_json(dest/'support_definition.json',dict(frozen_before_features=True,metadata_hash=digest(dest/'full_event_history.parquet'),
        config_hash=digest(ROOT/'configs/auditory_next_v2.yaml'),fold_hash=digest(foldpath),source_gate_hash=digest(gate/'completion.json')))
    pd.DataFrame(summary).groupby(['original_fs','filter_support_seconds','startup_guard_seconds']).agg(records=('n_events','size'),events=('n_events','sum')).reset_index().to_csv(public/'filter_support.csv',index=False)
    (report/'SUPPORT_REPORT.md').write_text('# v2 event support freeze\n\nNo EEG effect, model score or clinical label was used in this stage. '
        'H was rebuilt before QC and checked exactly against the original preceding code, trial, run and gap fields. '
        'All 11 allowed A2 regions were counted; thresholds were not relaxed. N2 uses independent new support and each retained record has all four half/class cells. '
        'N3 regions use only outer-training event counts. Identity components are conservative validation groups, not a confirmed child count.\n\n'
        'The numerical support summary is in the corresponding results folder. Donor, temporal-calibration and inner-scope gates remain separate requirements; sufficient counts do not imply a scientific result.\n')
    return finish(dest,public,aggregates)
