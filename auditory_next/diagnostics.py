"""G0 source reconstruction, original-head diagnostics and temporal roles.

This first diagnostic stage performs no new fits. Temporal readouts and the
single offline bridge are planned from its frozen metadata, never scores.
"""
import json
import pickle
import numpy as np
import pandas as pd
import torch
from scipy.special import softmax
from scipy.signal import sosfilt, group_delay

from auditory5.metrics import classification_metrics
from auditory5.preprocessing import fixed_sos
from .readouts import population_weights, ce_bits
from .provenance import ROOT, digest, write_json, finish
from .c2_spatial import decompose20, reconstruct20, coordinates19, from_coordinates19


def run(config,registry,site,dest,public,report,support_run):
    support_run=support_run or registry['support_run']
    source=ROOT/'private/auditory_next_v2'/support_run
    if json.loads((source/'completion.json').read_text())['status']!='PASS':raise ValueError('SUPPORT_GATE')
    planpath=ROOT/registry['legacy_plan'];plan=json.loads(planpath.read_text())
    inventory={r['path']:r['sha256'] for r in json.loads((ROOT/'private/auditory_next_v2'/registry['preflight_run']/'legacy_input_hashes.json').read_text())}
    original=pd.read_csv(ROOT/registry['legacy_screen']/'stimulus_decoding.csv')
    frames={}; training=[];original_head=[];checks=[]
    for task in plan['tasks']:
        folder=planpath.parent/'outputs'/task['name']
        for filename in ('completion.json','features.npz','feature_rows.parquet'):
            if digest(folder/filename)!=inventory[str(folder/filename)]:raise ValueError('G0_LEGACY_MUTATION')
        if task['mode']!='L0':
            state=torch.load(folder/'encoder.pt',map_location='cpu',weights_only=False)
            meta=state['metadata']; history=meta.get('history',[])
            training.append(dict(task=task['name'],mode=task['mode'],branch=task['branch'],stage=task['stage'],
                outer_fold=task['outer_fold'],inner_fold=task['inner_fold'],selected_epochs=meta.get('selected_epochs'),
                first_loss=history[0].get('loss_nats') if history else None,last_loss=history[-1].get('loss_nats') if history else None,
                final_gradient_norm=history[-1].get('gradient_norm_before_clip_mean') if history else None,
                encoder_effective_rank=meta.get('encoder_effective_rank'),encoder_variance=meta.get('encoder_variance_mean'),
                projector_variance=meta.get('projector_variance_mean'),fit_groups=len(state['scope']['train_groups']),
                monitor_epochs=len(meta.get('monitor_history',[])),original_head_available=task['mode']=='R_SUP'))
        if task['stage']!='outer':continue
        for window in ('post','pre'):
            rows=pd.read_parquet(folder/('stimulus_oof_'+window+'.parquet'))
            frames.setdefault((task['mode'],task['branch'],window),[]).append(rows)
        if task['mode']=='R_SUP' and task['branch']=='all':
            with np.load(folder/'features.npz',allow_pickle=False) as z:
                for role,groups in (('TRAIN_DIAGNOSTIC',state['scope']['train_groups']),('OUTER_SHARED',task['test_groups'])):
                    mask=np.isin(z['groups'].astype(str),groups)
                    if role=='OUTER_SHARED':mask &= np.isin(z['trial_ids'],rows.trial_id.to_numpy())
                    x=z['post'][mask].astype(float);y=z['y'][mask];g=z['groups'][mask].astype(str)
                    w=state['encoder_state']['head.weight'].numpy().astype(float);b=state['encoder_state']['head.bias'].numpy().astype(float)
                    logits=x@w.T+b; prob=softmax(logits,axis=1)
                    metric=classification_metrics(y,prob,g,z['trial_ids'][mask])
                    original_head.append(dict(outer_fold=task['outer_fold'],mode='R_SUP_ORIGINAL_HEAD',role=role,candidates=len(np.unique(g)),trials=len(y),
                        ce_bits_stable=ce_bits(logits[:,1]-logits[:,0],y,population_weights(y,g,'P_bal')),**metric))
    for (mode,branch,window),pieces in frames.items():
        rows=pd.concat(pieces,ignore_index=True)
        if not rows.trial_id.is_unique:raise ValueError('G0_DUPLICATE_OOF')
        for probability in ('raw','calibrated'):
            p=rows[probability+'_probability_class1'].to_numpy()
            metric=classification_metrics(rows.stimulus_local_id.to_numpy(),np.c_[1-p,p],rows.split_group_id.to_numpy(),rows.trial_id.to_numpy())
            prior=original[(original['mode']==mode)&(original.branch==branch)&(original.window==window)&(original.probability==probability)]
            if len(prior)!=1:raise ValueError('G0_OLD_METRIC_UNIQUE')
            errors={k:abs(metric[k]-float(prior.iloc[0][k])) for k in ('ce_bits','J_bits','bacc','auroc','brier')}
            if max(errors.values())>1e-10:raise ValueError('G0_SHARED_METRIC_MISMATCH')
            checks.append(dict(mode=mode,branch=branch,window=window,probability=probability,
                               candidates=rows.split_group_id.nunique(),trials=len(rows),max_error=max(errors.values()),**metric))
    pd.DataFrame(checks).to_csv(public/'shared_metrics_reproduction.csv',index=False)
    pd.DataFrame(training).to_csv(public/'encoder_training_diagnostics.csv',index=False)
    pd.DataFrame(original_head).to_csv(public/'supervised_original_head.csv',index=False)
    events=pd.read_parquet(source/'full_event_history.parquet')
    records=pd.read_parquet(ROOT/'private/auditory5_v1/data/manifest_001/records.parquet',columns=['record_id','n_samples','original_fs']).set_index('record_id')
    temporal=[];temporal_counts=[];bridge=[];spatial=[];external=[]
    for record,rows in events.groupby('record_id',sort=True):
        rows=rows.copy(); duration=float(records.loc[record,'n_samples']/records.loc[record,'original_fs'])
        full_blocks=np.arange(1,int(np.floor(duration/30)))
        boundary=float(full_blocks[int(np.floor(.6*len(full_blocks)))]*30) if len(full_blocks)>1 else None
        roles=np.full(len(rows),'excluded',dtype=object)
        if boundary is not None:
            good=rows.accepted.to_numpy(bool)&rows.stimulus_local_id.isin([0,1]).to_numpy()&rows.time_block_id.isin(full_blocks).to_numpy()
            roles[good & (rows.raw_dependency_end.to_numpy()<=boundary)]='calibration'
            roles[good & (rows.raw_dependency_start.to_numpy()>=boundary)]='test'
        rows['G0_role']=roles
        enough=all(((rows.G0_role==r)&(rows.stimulus_local_id==k)).sum()>=20 for r in ('calibration','test') for k in (0,1)) and all(rows.loc[rows.G0_role==r,'physical_time_block'].nunique()>=3 for r in ('calibration','test'))
        rows['G0_supported']=enough
        temporal.append(rows[['trial_id','record_id','candidate_id','split_group_id','G0_role','G0_supported']])
        temporal_counts.append(dict(record_id=record,split_group_id=str(rows.split_group_id.iloc[0]),supported=bool(enough),boundary_seconds=boundary,
                                     calibration_trials=int((roles=='calibration').sum()),test_trials=int((roles=='test').sum())))
        folder=ROOT/'private/auditory5_v1/data'/plan['export_run']/'P1_CAUSAL20'/record
        s=json.loads((folder/'summary.json').read_text());x=np.load(folder/'all.npy',mmap_mode='r')
        errors=[]
        for first in range(0,len(x),128):
            block=np.asarray(x[first:first+128],float);parts=decompose20(block,s['branch_channels']['all'])
            expected=block-block.mean(axis=1,keepdims=True)
            errors.append(float(np.max(abs(reconstruct20(parts)-expected))))
            errors.append(float(np.max(abs(reconstruct20(from_coordinates19(coordinates19(parts),s['branch_channels']['all']))-expected))))
        spatial.append(dict(record_id=record,stored_epochs=len(x),maximum_reconstruction_error=max(errors),
                            status='PASS' if max(errors)<1e-10 else 'FAIL'))
        offline=ROOT/'results/phase1_epochs_001'/record/'epochs.npz'
        status='NOT_COMPARABLE'; matched=0
        if offline.exists():
            external.append(dict(path=str(offline),sha256=digest(offline)))
            with np.load(offline,allow_pickle=False) as old:
                keys=set(old.files)
                if {'event_indices_1based','samples_0based','codes','times_s','channels','accepted'}<=keys:
                    ordinal=rows.trial_id.str.rsplit(':e',n=1).str[-1].astype(int)
                    lookup={int(o):i for i,o in enumerate(old['event_indices_1based'])}
                    expected=rows[rows.accepted & rows.stimulus_local_id.isin([0,1])]
                    alignment=[]
                    for i,row in expected.iterrows():
                        j=lookup.get(int(ordinal.loc[i]))
                        okay=j is not None and int(old['samples_0based'][j])==int(row.onset_sample) and str(old['codes'][j])==str(row.event_literal)
                        alignment.append(okay)
                    matched=sum(alignment)
                    status='TRIAL_MAPPING_VERIFIED_REFIT_PENDING' if all(alignment) and len(expected) else 'NOT_COMPARABLE'
                    if status.startswith('TRIAL_MAPPING'):
                        mapping=pd.DataFrame({'trial_id':expected.trial_id,'offline_index':[lookup[int(ordinal.loc[i])] for i in expected.index]})
                        mapping.to_parquet(dest/(record+'_offline_mapping.parquet'),index=False)
        bridge.append(dict(record_id=record,status=status,aligned_accepted_trials=matched))
    pd.concat(temporal,ignore_index=True).to_parquet(dest/'G0_temporal_roles.parquet',index=False)
    pd.DataFrame(temporal_counts).to_parquet(dest/'G0_temporal_support.parquet',index=False)
    pd.DataFrame(bridge).to_parquet(dest/'offline_bridge_support.parquet',index=False)
    pd.DataFrame(spatial).to_parquet(dest/'spatial_record_checks.parquet',index=False)
    write_json(dest/'additional_inputs.json',external)
    impulse=[]
    for fs in sorted(events.original_fs.unique()):
        sos=fixed_sos(float(fs));x=np.zeros(int(fs*60));x[0]=1;h=sosfilt(sos,x)
        frequencies=np.array([.5,1,2,4,8,16,30]);delay=sum(group_delay((section[:3],section[3:]),w=frequencies,fs=fs)[1] for section in sos)/fs
        for f,d in zip(frequencies,delay):
            impulse.append(dict(original_fs=fs,frequency_hz=float(f),group_delay_seconds=float(d),
              absolute_impulse_fraction_in_fixed_post=float(np.abs(h[int(.05*fs):int(.45*fs)]).sum()/np.abs(h).sum()),
              impulse_peak_delay_seconds=float(np.argmax(abs(h))/fs)))
    pd.DataFrame(impulse).to_csv(public/'causal_filter_delay.csv',index=False)
    public_summary=dict(status='PASS',scope='G0 reconstruction and metadata gates; temporal heads/bridge/injection pending',
        shared_metric_rows_verified=len(checks),shared_all_branch_candidates=58,max_shared_metric_error=max(r['max_error'] for r in checks),
        encoder_checkpoints_diagnosed=len(training),supervised_original_head_rows=len(original_head),
        temporal_supported_records=sum(r['supported'] for r in temporal_counts),temporal_supported_groups=len(set(r['split_group_id'] for r in temporal_counts if r['supported'])),
        offline_bridge_record_statuses=pd.Series([r['status'] for r in bridge]).value_counts().to_dict(),
        spatial_records_verified=len(spatial),spatial_maximum_reconstruction_error=max(r['maximum_reconstruction_error'] for r in spatial),
        new_readout_fits=0,new_encoder_fits=0)
    (report/'G0_DIAGNOSTIC_REPORT.md').write_text('# G0 first diagnostic stage\n\nAll existing shared metrics are recalculated, including the 58-group all-channel cohort. '
       'The original supervised CNN head is evaluated separately on its actual training groups and held-out groups; the old table describes refitted logistic probes. '
       'These training scores do not measure generalization. Encoder diagnostics and projector diagnostics remain distinct.\n\n'
       'Temporal roles are frozen from complete original 30 s blocks (first 60%, last 40%), with effective causal-filter and three-event context dependencies removed at the boundary. '
       'No within-child readout has been fitted in this stage. The offline bridge reports actual event ordinal/sample/code matching and awaits its prespecified readouts. '
       'Float64 spatial reconstruction is checked on every stored epoch including QC rejects; this is an algebra test, not a neural-source interpretation.\n')
    return finish(dest,public,public_summary)
