"""HA raw BDF adapter. Paths and all trial-level outputs remain restricted."""
import json,math,tempfile
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd
import pyedflib
from auditory5.events import build_event_history
from auditory5.preprocessing import (CausalPreprocessor,HA_CHANNELS,LEFT_CHANNELS,RIGHT_CHANNELS,
                                    effective_impulse_support,ProcessedChunk,extract_epoch)
from auditory5.provenance import digest,object_hash,write_json


def original_events(record, locator):
    fs=float(record['original_fs']);rid=record['record_id']
    with pyedflib.EdfReader(locator['event_path']) as reader:
        times,durations,codes=reader.readAnnotations()
    rows=[]
    for ordinal,(time,duration,code) in enumerate(zip(times,durations,codes),1):
        literal=str(code).strip();sample=int(np.rint(float(time)*fs))
        if sample<0 or sample>=int(record['n_samples']):raise ValueError('event outside audited recording')
        rows.append({'record_id':rid,'segment_id':rid+':s0','trial_id':rid+':s0:e'+str(ordinal),
            'event_index_1based':ordinal,'event_literal':literal,'stimulus_local_id':{'1':0,'2':1}.get(literal,-1),
            'onset_sample':sample,'onset_seconds_relative':sample/fs,'source_onset_seconds_relative':float(time),
            'event_kind':'target' if literal in ['1','2'] else 'unknown_sound',
            'event_role_evidence':'frozen_literal_target_map' if literal in ['1','2'] else 'unresolved_conservative_history_break',
            'candidate_id':record['candidate_id'],'split_group_id':record['split_group_id'],
            'time_block_id':int((sample/fs)//30),'segment_position_fraction':sample/int(record['n_samples']),
            'label_semantics':'literal_only','code_map_hash':record['code_map_hash'],
            'clinical_assessment_timing_status':'unknown','dynamic_condition_unknown':True})
    return build_event_history(rows,fs,target_codes=['1','2'])


def export_record(record,locator,destination,bank,spec):
    dest=Path(destination);dest.mkdir(parents=True,exist_ok=False)
    fs=float(record['original_fs']);ns=int(record['n_samples']);rid=record['record_id']
    rawpath=Path(locator['signal_path']);before=rawpath.stat()
    events=original_events(record,locator)
    source_hash=digest(rawpath);event_hash=digest(locator['event_path'])
    support=effective_impulse_support(fs)
    assert support.support_seconds<=spec['A_B_embargo_seconds']+1e-12
    branches={'all':HA_CHANNELS} if bank=='P1_CAUSAL20' else {'left':LEFT_CHANNELS,'right':RIGHT_CHANNELS}
    relevant=[c for c in HA_CHANNELS if any(c in names for names in branches.values())]
    with tempfile.TemporaryDirectory(prefix='auditory5-ha-') as tmp:
        tmp=Path(tmp)
        with pyedflib.EdfReader(str(rawpath)) as reader:
            names=reader.getSignalLabels()
            if len(set(names))!=len(names) or not set(HA_CHANNELS)<=set(names):raise ValueError('HA channel contract')
            if not np.all(reader.getSampleFrequencies()==fs) or int(reader.getNSamples()[0])!=ns:raise ValueError('HA source shape changed')
            headers=reader.getSignalHeaders()
            if any(headers[names.index(c)]['dimension']!='uV' for c in relevant):raise ValueError('HA source unit changed')
            raw=np.memmap(tmp/'raw.dat',mode='w+',dtype='float64',shape=(len(names),ns))
            processor=CausalPreprocessor(fs,names,bank=bank,support=support)
            step=processor.decimation_factor;outn=(ns+step-1)//step
            filtered={k:np.memmap(tmp/(k+'.dat'),mode='w+',dtype='float64',shape=(len(v),outn)) for k,v in branches.items()}
            chunk=int(60*fs);written=0
            for start in range(0,ns,chunk):
                stop=min(ns,start+chunk)
                x=np.stack([reader.readSignal(k,start=start,n=stop-start) for k in range(len(names))])
                if not np.isfinite(x).all():raise ValueError('nonfinite source: no implicit repair')
                raw[:,start:stop]=x
                out=processor.process(x,start_sample=start)
                n=len(out.source_samples)
                for key in branches:filtered[key][:,written:written+n]=out.data[key]
                written+=n
            assert written==outn
            source_samples=np.arange(outn,dtype=np.int64)*step
            buffer=ProcessedChunk(data=filtered,source_samples=source_samples,
                guard_valid=source_samples>=support.guard_samples,original_fs=fs,
                processed_fs=processor.processed_fs,decimation_factor=step,grid_origin_sample=0,
                segment_start_sample=0,bank=bank)
            stored=[r for r in events if r['event_kind']=='target' and r['onset_sample']-int(.2*fs)>=0 and r['onset_sample']+int(.5*fs)<=ns]
            count=len(stored);shape_t=int(round(.7*processor.processed_fs));assert shape_t==175
            arrays={k:np.lib.format.open_memmap(dest/(k+'.npy'),mode='w+',dtype='float32',shape=(count,len(v),shape_t)) for k,v in branches.items()}
            bytrial={r['trial_id']:i for i,r in enumerate(stored)}
            rawflat={}
            for key,channels in branches.items():
                fractions=[]
                for c in channels:
                    xx=raw[names.index(c)];n2=ns//int(2*fs)
                    fractions.append(float(np.mean(np.ptp(xx[:n2*int(2*fs)].reshape(n2,int(2*fs)),axis=1)<.5)))
                rawflat[key]=max(fractions)
            for row in events:
                row.update(preprocessing_id=bank,qc_version=spec['QC_version'],original_fs=fs,processed_fs=processor.processed_fs,
                    source_sha256=source_hash,source_event_sha256=event_hash,raw_locator_key=rid,
                    channel_map_hash=object_hash(branches),stored_epoch_index=-1,accepted=False,
                    reject_reason='not_target' if row['event_kind']!='target' else 'incomplete_epoch')
                if row['trial_id'] not in bytrial:continue
                idx=bytrial[row['trial_id']];row['stored_epoch_index']=idx
                epoch=extract_epoch(buffer,row['onset_sample'])
                assert len(epoch.times_s)==shape_t
                row['grid_first_relative_s']=float(epoch.times_s[0])
                row['post_start_index']=int(np.searchsorted(epoch.times_s+1e-10,.05))
                row['pre_stop_index']=int(np.searchsorted(epoch.times_s+1e-10,0))
                assert int(np.sum((epoch.times_s>=.05-1e-10)&(epoch.times_s<.45-1e-10)))==100
                assert row['pre_stop_index']==50
                reasons=list(epoch.reject_reasons);accepted=[]
                lo=row['onset_sample']-int(.2*fs);hi=row['onset_sample']+int(.5*fs)
                for key,channels in branches.items():
                    arrays[key][idx]=epoch.data[key]
                    ptp=float(np.ptp(epoch.data[key],axis=-1).max())
                    rr=[]
                    if ptp>spec['scalp_ptp_max_uv']:rr.append('ptp')
                    if rawflat[key]>=.2:rr.append('persistent_raw_flat')
                    for c in channels:
                        k=names.index(c);x=raw[k,lo:hi];h=headers[k]
                        delta=(h['physical_max']-h['physical_min'])/(h['digital_max']-h['digital_min'])
                        if np.ptp(x)<spec['raw_flat_ptp_min_uv']:rr.append('raw_flat')
                        if np.any((x<=h['physical_min']+delta)|(x>=h['physical_max']-delta)):rr.append('raw_saturation')
                    row[key+'_ptp_uv']=ptp
                    row[key+'_accepted']=not rr and epoch.eligible
                    accepted.append(row[key+'_accepted'])
                    reasons.extend(key+':'+x for x in sorted(set(rr)))
                row['accepted']=all(accepted)
                row['reject_reason']='|'.join(reasons)
                t=row['onset_sample']/fs;width=spec['A_block_seconds'];embargo=spec['A_B_embargo_seconds']
                a_block=int(t//width)
                row['A_block_id']=a_block;row['A_half']=a_block%2
                row['A_boundary_eligible']=(t-.2>=a_block*width+embargo and t+.5<=(a_block+1)*width-embargo)
                middle=ns/fs/2
                row['early_late_half']=int(t>=middle)
                row['early_late_boundary_eligible']=(t+.5<=middle-embargo or t-.2>=middle+embargo)
            for a in arrays.values():a.flush()
        df=pd.DataFrame(events);df.to_parquet(dest/'events.parquet',index=False)
        source_after=rawpath.stat();assert (before.st_size,before.st_mtime_ns)==(source_after.st_size,source_after.st_mtime_ns)
        summary={'record_id':rid,'candidate_id':record['candidate_id'],'split_group_id':record['split_group_id'],
            'bank':bank,'stored_epochs':count,'target_events':sum(r['event_kind']=='target' for r in events),
            'accepted':sum(r['accepted'] for r in events),'source_sha256':source_hash,'source_event_sha256':event_hash,
            'branch_channels':{k:list(v) for k,v in branches.items()},'original_fs':fs,'processed_fs':processor.processed_fs,
            'filter_support_seconds':support.support_seconds,'startup_guard_seconds':support.guard_seconds,
            'persistent_raw_flat_max_fraction':rawflat,'offline_record_qc':True,
            'code_counts':dict(Counter(r['event_literal'] for r in events)),
            'accepted_class_counts':dict(Counter(r['event_literal'] for r in events if r['accepted'])),
            'output_sha256':{p.name:digest(p) for p in dest.glob('*') if p.is_file()}}
        write_json(dest/'summary.json',summary)
        return summary
