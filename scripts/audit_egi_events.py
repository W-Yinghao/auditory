"""Bounded EGI v2-7 event scan. Layout checked against EEGLAB readegihdr/readegi."""
import csv,json,os,struct,traceback
from collections import Counter
from pathlib import Path
import numpy as np
from audit_mff import table,dump,j
from audit_other_eeg import token
BASE=Path(__file__).resolve().parents[1]
def read_header(f):
 h=f.read(30);ver=struct.unpack('>i',h[:4])[0];sf,nc,_,_,_=struct.unpack('>5h',h[20:]);cats=[]
 if ver not in range(2,8):raise ValueError('unsupported_version')
 def val(fmt):return struct.unpack(fmt,f.read(struct.calcsize(fmt)))[0]
 if ver&1:
  for _ in range(val('>h')):cats.append(f.read(val('>B')).decode(errors='replace'))
  nt=val('>h');ns=val('>i')
 else:nt=1;ns=val('>i')
 ne=val('>h');codes=[f.read(4).decode(errors='replace') for _ in range(ne)]
 return dict(version=ver,sfreq=sf,n_channels=nc,n_segments=nt,n_samples=ns,n_event_channels=ne,categories=cats,event_codes=codes,offset=f.tell(),dtype={2:'>i2',4:'>f4',6:'>f8'}[ver&6])
def main():
 assert os.environ.get('SLURM_JOB_ID')
 out=BASE/'results/egi_events_001';out.mkdir(exist_ok=False);priv=BASE/'private/egi_events_001';priv.mkdir(mode=0o700,exist_ok=False)
 rows=list(csv.DictReader((BASE/'private/inventory_001/file_path_map.csv').open()));summaries=[];epochs=[];errors=[]
 with (out/'event_ledger.csv').open('w') as ef:
  ew=csv.writer(ef);ew.writerow(['file_id','segment_1based','sample_in_segment_0based','time_in_segment_s','event_code_token','event_value'])
  for r in rows:
   p=Path(r['absolute_path']);fid=r['file_id']
   if p.suffix.lower()!='.raw' or p.name.startswith('._'):continue
   try:
    with p.open('rb') as f:h=read_header(f)
    size=np.dtype(h['dtype']).itemsize;nf=h['n_channels']+h['n_event_channels'];payload=size*nf*h['n_samples'];segmented=bool(h['version']&1)
    expected=h['offset']+h['n_segments']*(payload+(6 if segmented else 0))
    if expected!=p.stat().st_size:raise ValueError('binary_length_mismatch')
    counts=Counter();nonfinite=0
    for si in range(h['n_segments']):
     offset=h['offset']+si*(payload+(6 if segmented else 0));cat='';start=''
     if segmented:
      with p.open('rb') as f:f.seek(offset);cat,start=struct.unpack('>hi',f.read(6))
      offset+=6
      epochs.append({'file_id':fid,'segment_1based':si+1,'category_index_1based':cat,'category_token':token(h['categories'][cat-1]) if 1<=cat<=len(h['categories']) else 'out_of_range','segment_start_native':start,'segment_start_unit':'not_established','n_samples':h['n_samples'],'sampling_rate_hz':h['sfreq'],'data_level':'segmented_export_average_status_unconfirmed','clinical_label_status':'not_linked'})
     a=np.memmap(p,dtype=h['dtype'],mode='r',offset=offset,shape=(h['n_samples'],nf))
     for first in range(0,h['n_samples'],16384):
      ev=np.array(a[first:first+16384,h['n_channels']:]);nonfinite+=int(np.sum(~np.isfinite(ev)))
      # Preserve every nonzero event sample; do not collapse multi-sample pulses.
      ii,jj=np.nonzero(ev)
      for i,k in zip(ii,jj):
       code=token(h['event_codes'][k]);counts[code]+=1;ew.writerow([fid,si+1,first+int(i),(first+int(i))/h['sfreq'],code,float(ev[i,k])])
     del a
    summaries.append({'file_id':fid,'version':h['version'],'n_segments':h['n_segments'],'n_samples_per_segment':h['n_samples'],'sampling_rate_hz':h['sfreq'],'n_nonzero_event_samples':sum(counts.values()),'event_code_nonzero_counts':j(counts),'nonfinite_event_values':nonfinite,'bytes_match_layout':True,'status':'event_channels_fully_scanned'})
    if len(summaries)%25==0:print(j({'files_done':len(summaries)}),flush=True)
   except Exception as e:errors.append({'file_id':fid,'error':repr(e),'trace':traceback.format_exc()})
 table(out/'file_summary.csv',summaries);table(out/'segmented_epoch_ledger.csv',epochs);dump(priv/'errors.json',errors)
 dump(out/'summary.json',{'job_id':os.environ['SLURM_JOB_ID'],'raw_files_event_scanned':len(summaries),'segmented_epoch_entries':len(epochs),'nonzero_event_samples':sum(r['n_nonzero_event_samples'] for r in summaries),'errors':len(errors),'notice':'All nonzero event samples preserved. Event code semantics and links to MFF processing versions require verification.'})
if __name__=='__main__':main()
