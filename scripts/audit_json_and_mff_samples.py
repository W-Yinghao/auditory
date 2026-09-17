import csv,json,os,re,traceback
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
from mne.io.egi.general import _block_r,_get_signalfname
from audit_mff import dump,table,xml,nodes,value,j
from audit_other_eeg import token
from audit_signals import preview
BASE=Path(__file__).resolve().parents[1]
assert os.environ.get('SLURM_JOB_ID')
out=BASE/'results/extra_002';out.mkdir(exist_ok=False);priv=BASE/'private/extra_002';priv.mkdir(mode=0o700,exist_ok=False)
figs=BASE/'figures/mff_002';figs.mkdir(exist_ok=False)
rows=list(csv.DictReader((BASE/'private/inventory_001/file_path_map.csv').open()));settings=[];jsonrows=[];schemas=[];errors=[]
for r in rows:
 p=Path(r['absolute_path'])
 if p.suffix!='.json':continue
 try:
  d=json.loads(p.read_text());fid=r['file_id'];schemas.append({'file_id':fid,'basename':p.name,'keys':list(d),'shapes':{k:len(v) if isinstance(v,(list,dict)) else type(v).__name__ for k,v in d.items()}})
  setting=d.get('OverlapSettings') or {}
  settings.append({'file_id':fid,'ERPType':d.get('ERPType',''),'n_channels_named':len(d.get('ChannelNames') or []),'trigger_tokens':j([token(t) for t in (d.get('TriggerNames') or [])]),'reference':setting.get('Reference',''),'low_cut':setting.get('LowCut',''),'high_cut':setting.get('HighCut',''),'epoch_left_s':setting.get('EpochLeft',''),'epoch_right_s':setting.get('EpochRight',''),'settings_status':'vendor_export_not_reprocessing_verified'})
  for key,entries in d.items():
   if not isinstance(entries,list) or not entries or not isinstance(entries[0],dict):continue
   for idx,e in enumerate(entries,1):
    chans=e.get('DataChannel',[])
    jsonrows.append({'file_id':fid,'array_key':key,'entry_1based':idx,'data_level':'evoked' if 'average' in key.lower() else 'unresolved','trigger_token':token(e.get('TriggerName','')),'n_channels':len(chans),'sample_lengths':j(sorted(set(len(c.get('Points',[])) for c in chans))),'sample_rates':j(sorted(set(c.get('SampleRate','') for c in chans),key=str)),'is_rejected':e.get('IsRejected',''),'start_point':e.get('StartPoint',''),'end_point':e.get('EndPoint',''),'clinical_label_status':'not_linked'})
 except Exception as e:errors.append({'file_id':r['file_id'],'error':repr(e)})
table(out/'vendor_settings.csv',settings);table(out/'vendor_array_ledger.csv',jsonrows);dump(priv/'vendor_schemas.json',schemas)
# Stratify by metadata layout, directory stimulus clues, and preprocessing branch.
registry=json.loads((BASE/'private/probe_001/mff_registry.json').read_text());meta=json.loads((BASE/'private/probe_001/mff_metadata.json').read_text());meta={r['container_id']:r for r in meta}
strata=defaultdict(list)
for r in registry:
 p=Path(r['path']);m=meta[r['container_id']];e=m.get('epochs.xml',{});n=sum(e.get('beginTime',{}).values());cat='categories.xml' in m['basenames']
 layout='category_small' if cat and n<=5 else 'category_many' if cat else 'continuous_or_discontinuous'
 text=str(p).lower();stim='puretone' if ('puretone' in text or 'pure_tone' in text) else 'bapa' if 'bapa' in text else 'ba1ba4' if 'ba1ba4' in text else 'other'
 branch='extra_preprocessing' if '预处理' in p.parts else 'main'
 if m['basenames'].get('signal1.bin',0):strata[(branch,stim,layout)].append(r)
selected=[]
for key,rr in sorted(strata.items()):
 rr=sorted(rr,key=lambda r:meta[r['container_id']]['bytes']);selected.append((key,rr[len(rr)//2]))
qc=[]
for key,r in selected:
 mid=r['container_id'];p=Path(r['path'])
 try:
  sig=_get_signalfname(str(p))['EEG'];binpath=p/sig['signal']
  with binpath.open('rb') as f:
   block=_block_r(f);count=min(block['nsamples'],int(block['sfreq']*4));x=np.empty((block['nc'],count))
   offset=f.tell()
   for c in range(block['nc']):f.seek(offset+c*block['nsamples']*4);x[c]=np.fromfile(f,dtype='<f4',count=count)
  info=xml(p/sig['info']);units=[(v.text or '').strip() for v in nodes(info,'unit')] if info is not None else []
  unit='Native MFF units (uncalibrated)'
  preview(x,block['sfreq'],mid+' | '+' / '.join(key)+' | first stored block',figs/(mid+'.png'),unit)
  qc.append({'container_id':mid,'sampling_stratum':j(key),'n_channels':block['nc'],'sampling_rate_hz':block['sfreq'],'samples_per_channel_examined':count,'n_storage_blocks_examined':1,'all_finite':bool(np.isfinite(x).all()),'flat_channels':int(np.sum(np.ptp(x,axis=1)==0)),'median_channel_p2p_native':float(np.median(np.ptp(x,axis=1))),'status':'bounded_native_signal_preview','stimulus_stratum_status':'directory_clue_only'})
 except Exception as e:errors.append({'container_id':mid,'error':repr(e),'trace':traceback.format_exc()})
table(out/'mff_sample_qc.csv',qc);dump(priv/'errors.json',errors)
dump(out/'summary.json',{'job_id':os.environ['SLURM_JOB_ID'],'vendor_json_files':len(settings),'vendor_array_entries':len(jsonrows),'vendor_array_types':dict(Counter(r['array_key'] for r in jsonrows)),'mff_strata_selected':len(selected),'mff_signal_previews':len(qc),'errors':len(errors),'vendor_settings_combinations':dict(Counter(j([r[k] for k in ('reference','low_cut','high_cut','epoch_left_s','epoch_right_s')]) for r in settings))})
