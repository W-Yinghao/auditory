#!/usr/bin/env python3
import csv,hashlib,json,os,re,struct,traceback
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
from pymatreader import read_mat
import pyedflib
from audit_mff import dump,table,j

BASE=Path(__file__).resolve().parents[1]
def token(x):
    s=str(x).strip()
    return s if re.fullmatch(r'\d{1,8}|boundary|DIN[1-8]|stad|dev|devi|stm[+-]|TRSP|bgin',s) else 'L'+hashlib.sha256(s.encode()).hexdigest()[:12]
def seq(x):
    if isinstance(x,np.ndarray):return list(x.ravel())
    return x if isinstance(x,list) else [x]
def records(x):
    if isinstance(x,dict):
        if not x:return []
        def is_column(v):return isinstance(v,list) or (isinstance(v,np.ndarray) and v.ndim>0)
        size=max((len(v) if is_column(v) else 1) for v in x.values())
        return [{k:(v[i] if is_column(v) and len(v)==size else v) for k,v in x.items()} for i in range(size)]
    return [v for v in seq(x) if isinstance(v,dict)]
def main():
    assert os.environ.get('SLURM_JOB_ID')
    out=BASE/'results/other_eeg_001';out.mkdir(exist_ok=False)
    private=BASE/'private/other_eeg_001';private.mkdir(mode=0o700,exist_ok=False)
    rows=list(csv.DictReader((BASE/'private/inventory_001/file_path_map.csv').open()))
    bypath={str(Path(r['absolute_path'])):r['file_id'] for r in rows}
    sets=[];bdfs=[];raws=[];errors=[];hist=[];private_headers=[];events=[];epochs=[]
    for r in rows:
      p=Path(r['absolute_path']);ext=p.suffix.lower();fid=r['file_id']
      if p.name.startswith('._') or ext not in ('.set','.bdf','.raw'):continue
      row={'file_id':fid,'read_status':'ok'}
      try:
        if ext=='.set':
            sets.append(row);d=read_mat(p);d=d.get('EEG',d)
            sf=float(d['srate']);nc=int(d['nbchan']);nt=int(d['trials']);ns=int(d['pnts'])
            row.update(sampling_rate_hz=sf,n_channels=nc,n_epochs=nt if nt>1 else 0,n_samples_per_epoch_or_continuous=ns,data_level='epochs' if nt>1 else 'preprocessed_continuous',xmin_s=float(d['xmin']),xmax_s=float(d['xmax']),reference=str(d.get('ref','unknown')))
            data=d['data'];comp=p.parent/str(data) if isinstance(data,str) else None
            row['external_data']=comp is not None;row['companion_found']=bool(comp and comp.exists());row['companion_file_id']=bypath.get(str(comp),'')
            if comp and comp.exists():row['companion_size_matches_float32']=comp.stat().st_size==4*nc*nt*ns
            es=records(d.get('event',[]));eps=records(d.get('epoch',[]));ures=records(d.get('urevent',[]))
            row.update(n_events=len(es),n_epoch_metadata=len(eps),n_urevents=len(ures),event_fields=j(list(es[0]) if es else []),epoch_fields=j(list(eps[0]) if eps else []))
            types=Counter();timings=defaultdict(list);oob=0
            for ei,e in enumerate(es,1):
                code=token(e.get('type',''));lat=float(e.get('latency',np.nan));onset=(lat-1)/sf
                types[code]+=1;timings[code].append(onset);oob+=not(0<=onset<ns*nt/sf)
                events.append({'file_id':fid,'event_index_1based':ei,'event_code_token':code,'latency_samples_1based':lat,'onset_s':onset,'event_epoch_1based':j(e.get('epoch','')),'urevent_1based':j(e.get('urevent','')),'source':'EEG.event','event_role':'unknown'})
            for ei,e in enumerate(eps,1):
                latencies=[float(x) for x in seq(e.get('eventlatency',[]))];codes=[token(x) for x in seq(e.get('eventtype',[]))]
                zero=[codes[k] for k,lat in enumerate(latencies) if abs(lat)<=500/sf and k<len(codes)]
                epochs.append({'file_id':fid,'epoch_1based':ei,'event_codes':j(codes),'event_latencies_ms':j(latencies),'zero_codes':j(zero),'zero_label_status':'unique' if len(zero)==1 else 'ambiguous_or_missing','urevent_links':j(e.get('eventurevent',[])),'clinical_label_status':'not_linked'})
            row.update(event_code_counts=j(types),out_of_range_events=oob,event_interval_median_s=j({k:float(np.median(np.diff(v))) for k,v in timings.items() if len(v)>1}))
            hist.append({'file_id':fid,'history':d.get('history',''),'channel_labels':d.get('chanlocs',{}).get('labels',[]) if isinstance(d.get('chanlocs'),dict) else [],'event_examples':es[:3],'epoch_examples':eps[:2]})
        elif ext=='.bdf':
            bdfs.append(row)
            with p.open('rb') as f:
                h=f.read(256);nh=int(h[252:256]);rest=f.read(256*nh)
            labels=[rest[i*16:(i+1)*16].decode(errors='replace').strip() for i in range(nh)]
            recdur=float(h[244:252]);nrec=int(h[236:244]);headerbytes=int(h[184:192]);off=216*nh
            samples=[int(rest[off+i*8:off+(i+1)*8]) for i in range(nh)]
            dims=[rest[96*nh+i*8:96*nh+(i+1)*8].decode(errors='replace').strip() for i in range(nh)]
            group='B'+hashlib.sha256(str(p.parent).encode()).hexdigest()[:12]
            role='event_companion' if 'evt' in p.name.lower() else 'signal'
            row.update(candidate_acquisition_id=group,file_role=role,n_channels=nh,channel_labels=j(labels),physical_dimensions=j(dims),sampling_rates_hz=j(sorted(set(x/recdur for x in samples))),duration_s=nrec*recdur,n_records=nrec,bytes_match_records=p.stat().st_size==headerbytes+nrec*sum(samples)*3)
            private_headers.append({'file_id':fid,'date':h[168:176].decode(errors='replace'),'time':h[176:184].decode(errors='replace'),'subject':h[8:88].decode(errors='replace'),'recording':h[88:168].decode(errors='replace'),'folder':str(p.parent),'candidate_acquisition_id':group})
            ec=Counter();etimes=[]
            with pyedflib.EdfReader(str(p)) as reader:
                onset,duration,desc=reader.readAnnotations()
                for ei,(t,du,de) in enumerate(zip(onset,duration,desc),1):
                    code=token(de);ec[code]+=1;etimes.append(float(t))
                    events.append({'file_id':fid,'event_index_1based':ei,'event_code_token':code,'onset_s':float(t),'duration_s':float(du),'source':'BDF_annotations','event_role':'unknown'})
            row['n_annotations']=sum(ec.values());row['annotation_code_counts']=j(ec)
            row['annotation_interval_median_s']=float(np.median(np.diff(etimes))) if len(etimes)>1 else ''
            row['trigger_channel_candidates']=j([x for x in labels if re.search('status|trigger|stim',x,re.I)])
        else:
            raws.append(row)
            with p.open('rb') as f:h=f.read(36)
            version=struct.unpack('>i',h[:4])[0];sf,nc,gain,bits,vr=struct.unpack('>5h',h[20:30])
            row.update(version=version,sampling_rate_hz=sf,n_channels=nc,gain=gain,bits=bits,value_range=vr)
            if version not in (2,3,4,5,6,7):raise ValueError('Unrecognized EGI version')
            if version&1:row.update(data_level='segmented_binary',epoch_status='requires_segmented_reader')
            else:
                ns,ne=struct.unpack('>ih',h[30:36]);size={2:2,4:4,6:8}[version&6]
                with p.open('rb') as f:f.seek(36);codes=f.read(ne*4)
                row.update(data_level='continuous_binary',n_samples=ns,n_event_channels=ne,duration_s=ns/sf,event_codes=j([token(codes[k*4:(k+1)*4].decode(errors='replace')) for k in range(ne)]),bytes_match_layout=p.stat().st_size==36+4*ne+size*ns*(nc+ne),event_status='header_only')
      except Exception as e:row['read_status']='error';row['error_class']=type(e).__name__;errors.append({'file_id':fid,'error':repr(e),'trace':traceback.format_exc()})
    for name,rr in [('set_index',sets),('bdf_index',bdfs),('egi_raw_index',raws),('event_ledger',events),('epoch_ledger',epochs)]:table(out/(name+'.csv'),rr,fields=None if rr else ['file_id','status'])
    dump(private/'set_history.json',hist);dump(private/'bdf_private_headers.json',private_headers);dump(private/'errors.json',errors)
    summary={'job_id':os.environ['SLURM_JOB_ID'],'sets':len(sets),'set_data_levels':dict(Counter(r.get('data_level','unknown') for r in sets)),'set_epochs':len(epochs),'set_events':sum(r.get('n_events',0) for r in sets),'set_channels':dict(Counter(str(r.get('n_channels')) for r in sets)),'bdfs':len(bdfs),'bdf_roles':dict(Counter(r.get('file_role','unknown') for r in bdfs)),'bdf_candidate_acquisitions':len(set(r.get('candidate_acquisition_id') for r in bdfs)),'bdf_annotations':sum(r.get('n_annotations',0) for r in bdfs),'raws':len(raws),'raw_levels':dict(Counter(r.get('data_level','unknown') for r in raws)),'errors':len(errors)}
    dump(out/'summary.json',summary);print(j(summary))
if __name__=='__main__':main()
