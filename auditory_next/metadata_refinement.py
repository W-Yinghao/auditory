"""Supersede provisional G0 metadata gates without rerunning old EEG effects."""
import json
import numpy as np
import pandas as pd
from .provenance import ROOT,digest,write_json,finish
from .temporal import freeze_temporal_roles


def run(config,registry,site,dest,public,report,support_run):
    support_run=support_run or registry['support_run']
    root=ROOT/'private/auditory_next_v2'
    old=root/'G0_001';support=root/support_run
    for path in (old,support):
        if json.loads((path/'completion.json').read_text())['status']!='PASS':raise ValueError('METADATA_INPUT_GATE')
    events=pd.read_parquet(support/'full_event_history.parquet')
    records=pd.read_parquet(ROOT/'private/auditory5_v1/data/manifest_001/records.parquet',columns=['record_id','n_samples','original_fs'])
    roles,counts=freeze_temporal_roles(events,records)
    counts['supported']=counts.conservative_group_valid
    roles=roles.rename(columns={'temporal_role':'G0_role'})
    good=set(counts.loc[counts.supported,'record_id'])
    roles['G0_supported']=roles.record_id.isin(good)
    roles.to_parquet(dest/'G0_temporal_roles.parquet',index=False)
    counts.to_parquet(dest/'G0_temporal_support.parquet',index=False)
    hashes={x['path']:x['sha256'] for x in json.loads((old/'additional_inputs.json').read_text())}
    bridge=[];mappings=[]
    for record,rows in events.groupby('record_id',sort=True):
        path=ROOT/'results/phase1_epochs_001'/record/'epochs.npz'
        if not path.exists():
            bridge.append(dict(record_id=record,status='NOT_COMPARABLE',reason='MISSING_OFFLINE_BANK'));continue
        if digest(path)!=hashes[str(path)]:raise ValueError('OFFLINE_SOURCE_CHANGED')
        with np.load(path,allow_pickle=False) as olddata:
            ordinals=olddata['event_indices_1based'].astype(int)
            if len(np.unique(ordinals))!=len(ordinals):raise ValueError('OFFLINE_DUPLICATE_EVENT')
            lookup={int(o):i for i,o in enumerate(ordinals)}
            accepted=olddata['accepted']
            # Phase1 accepted[:,0] is the common average-reference condition.
            if accepted.ndim==2:accepted=accepted[:,0]
            expected=rows[rows.accepted & rows.stimulus_local_id.isin([0,1])]
            shared=[];missing=0;qc_rejected=0
            for _,row in expected.iterrows():
                ordinal=int(str(row.trial_id).rsplit(':e',1)[-1]);j=lookup.get(ordinal)
                if j is None:missing+=1;continue
                if int(olddata['samples_0based'][j])!=int(row.onset_sample) or str(olddata['codes'][j])!=str(row.event_literal):
                    raise ValueError('OFFLINE_SHARED_EVENT_MISMATCH')
                if not bool(accepted[j]):qc_rejected+=1;continue
                shared.append(dict(trial_id=str(row.trial_id),record_id=record,split_group_id=str(row.split_group_id),
                                   stimulus_local_id=int(row.stimulus_local_id),offline_index=j))
            mapping=pd.DataFrame(shared)
            class_counts=mapping.stimulus_local_id.value_counts().to_dict() if len(mapping) else {}
            enough=all(class_counts.get(k,0)>=20 for k in (0,1))
            bridge.append(dict(record_id=record,split_group_id=str(rows.split_group_id.iloc[0]),
                status='COMMON_QC_MAPPING_VERIFIED' if enough else 'INSUFFICIENT_SUPPORT',
                common_trials=len(mapping),omitted_offline_edge_events=missing,offline_QC_rejects=qc_rejected,
                class0=class_counts.get(0,0),class1=class_counts.get(1,0)))
            if len(mapping):mappings.append(mapping)
    pd.concat(mappings,ignore_index=True).to_parquet(dest/'offline_common_mapping.parquet',index=False)
    pd.DataFrame(bridge).to_parquet(dest/'offline_bridge_support.parquet',index=False)
    write_json(dest/'input_hashes.json',dict(support_run=support_run,history_sha256=digest(support/'full_event_history.parquet'),
               old_diagnostic_receipt_sha256=digest(old/'completion.json'),offline_hashes=hashes))
    summary=dict(status='PASS',supersedes='G0_001 temporal-role and offline-bridge metadata only',
        temporal_supported_records=int(counts.supported.sum()),temporal_supported_groups=int(counts.loc[counts.supported,'split_group_id'].nunique()),
        bridge_statuses=pd.Series([x['status'] for x in bridge]).value_counts().to_dict(),
        bridge_common_trials=sum(x.get('common_trials',0) for x in bridge),new_readout_fits=0,new_encoder_fits=0,
        numerical_dependency_scope='causal filter + complete past-code run + epoch baseline; role boundary',
        selection_isolation=False,old_effects_reused_from='G0_001')
    (report/'G0_METADATA_REFINEMENT.md').write_text('# G0 metadata refinement\n\n'
        'Temporal calibration/test roles now use the complete preceding-run dependency from S1_support_004. '
        'Dependencies may cross internal blocks on the same temporal side; none may cross the calibration/test boundary. '
        'Whole-record offline QC selection is shared, so numerical dependency isolation does not imply selection isolation.\n\n'
        'The offline bridge uses the exact common event intersection after both QC masks. Expected edge omissions do not make a record incomparable. '
        'Every shared event must match original event ordinal, sample and code. This supersedes the provisional G0_001 rule requiring all causal accepted trials to be present offline. '
        'Old metric reproduction, original supervised-head diagnostics and spatial algebra checks remain referenced without refitting.\n')
    return finish(dest,public,summary)
