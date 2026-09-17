#!/usr/bin/env python3
"""Read every MFF header, epoch/category entry, event track, and history.

Metadata audit only: MFF storage epochs are not necessarily stimulus trials.
"""
import csv, hashlib, json, os, re, traceback
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from mne.io.egi.general import _get_blocks

BASE=Path(__file__).resolve().parents[1]
def tag(el):return el.tag.rsplit('}',1)[-1]
def nodes(el,name):return [x for x in el.iter() if tag(x)==name]
def value(el,name,default=''):
    found=nodes(el,name);return (found[0].text or '').strip() if found else default
def xml(p):return ET.parse(p).getroot() if p.exists() else None
def j(x):return json.dumps(x,ensure_ascii=False,default=lambda a:a.item() if isinstance(a,np.generic) else str(a))
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str))
def table(p,rows,fields=None):
    fields=fields or sorted(set().union(*(r.keys() for r in rows)))
    with p.open('w') as f:
        w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
def run():
    assert os.environ.get('SLURM_JOB_ID'),'Submit through Slurm'
    out=BASE/'results/mff_001';out.mkdir(exist_ok=False)
    private=BASE/'private/mff_001';private.mkdir(mode=0o700,exist_ok=False)
    rows=list(csv.DictReader((BASE/'private/inventory_001/file_path_map.csv').open()))
    containers=defaultdict(list)
    for r in rows:
        for p in Path(r['absolute_path']).parents:
            if p.suffix.lower()=='.mff':containers[p].append(r);break
    summaries=[]; registry=[]; failures=[]; hist=[]; source_map={}; label_map={}
    safe={'standard','deviant','stad','dev','devi','stm+','stm-','bgin','trsp','din1','din2','din3','din4','sync','sess','cell','boundary'}
    def token(s):
        s=str(s).strip()
        if s.lower() in safe or re.fullmatch(r'[0-9]{1,8}',s):return s
        t='L'+hashlib.sha256(s.encode()).hexdigest()[:12];label_map[t]=s;return t
    ef=(out/'epoch_ledger.csv').open('w');ew=csv.writer(ef)
    ew.writerow(['container_id','storage_epoch_1based','begin_native','end_native','time_unit','duration_s','first_block_1based','last_block_1based','category_tokens','segment_statuses','event_offsets_s','label_status','data_level','source_id','signal_qc_status'])
    sf=(out/'category_segment_ledger.csv').open('w');sw=csv.writer(sf)
    sw.writerow(['container_id','category_token','segment_1based','begin_native','end_native','event_begin_native','time_unit','status','fault_tokens','channel_status','n_averaged_source_segments'])
    vf=(out/'event_ledger.csv').open('w');vw=csv.writer(vf)
    vw.writerow(['container_id','track_file_id','event_1based','code_token','onset_s','duration_native','relative_begin_native','numeric_keys','time_status'])
    try:
      for ci,(p,files) in enumerate(sorted(containers.items(),key=lambda a:str(a[0])),1):
        mid=f'M{ci:04d}';registry.append({'container_id':mid,'path':str(p),'files':[r['file_id'] for r in files]})
        row={'container_id':mid,'read_status':'ok','n_files':len(files),'device_state':'unknown','signal_qc_status':'not_read'}
        summaries.append(row)
        try:
            info=xml(p/'info.xml');record_time=value(info,'recordTime') if info is not None else ''
            unit='ns' if re.search(r'\.\d{9}[+-]',record_time) else 'us';scale=1e9 if unit=='ns' else 1e6
            subject=xml(p/'subject.xml');fields={value(f,'name'):value(f,'data') for f in nodes(subject,'field')} if subject is not None else {}
            patient=fields.get('Patient ID','');key=(record_time,patient) if record_time and patient else (str(p),)
            candidate='R'+hashlib.sha256(j(key).encode()).hexdigest()[:12]
            row['candidate_acquisition_id']=candidate;row['acquisition_status']='candidate_metadata_only'
            registry[-1].update(record_time=record_time,subject_fields=fields,candidate_acquisition_id=candidate)
            history=xml(p/'history.xml');methods=[(x.text or '').strip() for x in nodes(history,'method')] if history is not None else []
            settings=[(x.text or '').strip() for x in nodes(history,'setting')] if history is not None else []
            paths=[(x.text or '').strip() for x in nodes(history,'filePath')] if history is not None else []
            hist.append({'container_id':mid,'methods':methods,'settings':settings,'source_paths':paths})
            row['history_methods']=j(methods)
            row['has_40ms_offset_setting']=any('Offset: 40' in s for s in settings)
            row['has_segmentation_rule']=any('Code is' in s for s in settings)
            cat=xml(p/'categories.xml');segments=[];catcounts=Counter();statuscounts=Counter();averaged=False
            if cat is not None:
                for c in nodes(cat,'cat'):
                    ct=token(value(c,'name'))
                    for si,s in enumerate(nodes(c,'seg'),1):
                        b=int(value(s,'beginTime'));e=int(value(s,'endTime'));ev=value(s,'evtBegin');ev=int(ev) if ev else None
                        keys={value(k,'keyCode'):value(k,'data') for k in nodes(s,'key')};nave=keys.get('#seg','')
                        averaged |= bool(nave)
                        faults=[token(x.text or '') for x in nodes(s,'fault')]
                        channels=[{'attributes':x.attrib,'channels':x.text or ''} for x in nodes(s,'channels')]
                        status=s.get('status','unknown');catcounts[ct]+=1;statuscounts[status]+=1
                        segments.append((b,e,ev,ct,status))
                        sw.writerow([mid,ct,si,b,e,'' if ev is None else ev,unit,status,j(faults),j(channels),nave])
            level='evoked' if averaged or any('averag' in x.lower() for x in methods) else 'epochs' if segments else 'continuous_or_discontinuous'
            row['data_level']=level;row['category_counts']=j(catcounts);row['segment_status_counts']=j(statuscounts);row['n_category_segments']=len(segments)
            ep=xml(p/'epochs.xml');epochs=nodes(ep,'epoch') if ep is not None else []
            durations=[];cat_index=defaultdict(list)
            for s in segments:cat_index[(s[0],s[1])].append(s)
            for ei,e in enumerate(epochs,1):
                b=int(value(e,'beginTime'));end=int(value(e,'endTime'));dur=(end-b)/scale;durations.append(dur)
                matches=cat_index[(b,end)];cs=[s[3] for s in matches];sts=[s[4] for s in matches]
                offsets=[(s[2]-b)/scale if s[2] is not None else None for s in matches]
                ew.writerow([mid,ei,b,end,unit,dur,value(e,'firstBlock'),value(e,'lastBlock'),j(cs),j(sts),j(offsets),'category_metadata' if matches else 'no_category_match',level,'epochs.xml','not_read'])
            row['n_storage_epochs']=len(epochs);row['stored_time_s']=sum(durations)
            row['storage_epoch_min_s']=min(durations) if durations else '';row['storage_epoch_max_s']=max(durations) if durations else ''
            bins=sorted(p.glob('signal*.bin'));row['n_signal_bins']=len(bins)
            if bins:
                block=_get_blocks(str(bins[0]));row.update(sampling_rate_hz=int(block['sfreq']),n_signal_channels=int(block['n_channels']),n_blocks=int(block['n_blocks']),n_samples=int(sum(block['samples_block'])))
                row['binary_xml_duration_difference_s']=row['n_samples']/row['sampling_rate_hz']-row['stored_time_s']
            else:row['read_status']='missing_signal_binary'
            evcounts=Counter();eventtimes=defaultdict(list);keycounts=defaultdict(Counter);duplicates=0;seen=set();outside=0
            origin=datetime.fromisoformat(record_time) if record_time else None
            tracks=[r for r in files if Path(r['absolute_path']).name.startswith('Events_') and Path(r['absolute_path']).suffix=='.xml']
            for f in tracks:
                tr=xml(Path(f['absolute_path']))
                for ei,event in enumerate(nodes(tr,'event'),1):
                    code=token(value(event,'code'));ts=value(event,'beginTime');onset='';status='unresolved'
                    if ts and origin:
                        try:onset=(datetime.fromisoformat(ts)-origin).total_seconds();status='timestamp_relative_to_record'
                        except ValueError:pass
                    k={value(k,'keyCode'):value(k,'data') for k in nodes(event,'key')};numeric={key:val for key,val in k.items() if re.fullmatch(r'[-+]?\d+(\.\d+)?',val)}
                    for key,val in numeric.items():keycounts[code+'|'+token(key)][val]+=1
                    evcounts[code]+=1
                    if onset!='':eventtimes[code].append(onset)
                    pair=(code,onset)
                    if pair in seen:duplicates+=1
                    seen.add(pair)
                    vw.writerow([mid,f['file_id'],ei,code,onset,value(event,'duration'),value(event,'relativeBeginTime'),j(numeric),status])
            row['event_code_counts']=j(evcounts);row['n_events']=sum(evcounts.values());row['n_event_tracks']=len(tracks);row['duplicate_code_timestamp_entries']=duplicates
            row['event_interval_median_s']=j({k:float(np.median(np.diff(sorted(v)))) for k,v in eventtimes.items() if len(v)>1})
            row['numeric_event_key_counts']=j(keycounts)
        except Exception as e:
            row['read_status']='error';row['error_class']=type(e).__name__;failures.append({'container_id':mid,'error':repr(e),'trace':traceback.format_exc()})
        if ci%100==0:print(j({'containers_done':ci}),flush=True)
    finally:ef.close();sf.close();vf.close()
    table(out/'container_index.csv',summaries);dump(private/'registry.json',registry);dump(private/'history.json',hist);dump(private/'label_map.json',label_map);dump(private/'errors.json',failures)
    summary={'job_id':os.environ['SLURM_JOB_ID'],'containers':len(summaries),'read_status':dict(Counter(r['read_status'] for r in summaries)),
      'data_levels':dict(Counter(r.get('data_level','unknown') for r in summaries)),
      'candidate_acquisition_groups':len(set(r.get('candidate_acquisition_id') for r in summaries)),
      'n_storage_epoch_entries':sum(r.get('n_storage_epochs',0) for r in summaries),'n_category_segment_entries':sum(r.get('n_category_segments',0) for r in summaries),
      'n_event_entries':sum(r.get('n_events',0) for r in summaries),'sampling_rates':dict(Counter(str(r.get('sampling_rate_hz')) for r in summaries)),
      'channel_counts':dict(Counter(str(r.get('n_signal_channels')) for r in summaries)),
      'versions_with_40ms_offset_setting':sum(r.get('has_40ms_offset_setting',False) for r in summaries),
      'event_codes':dict(sum((Counter(json.loads(r.get('event_code_counts','{}'))) for r in summaries),Counter())),
      'notice':'Entries include processing versions. Storage epochs can be discontinuous blocks or averaged conditions, not independent trials/children. All signal QC remains not_read.'}
    dump(out/'summary.json',summary);print(j(summary),flush=True)
if __name__=='__main__':run()
