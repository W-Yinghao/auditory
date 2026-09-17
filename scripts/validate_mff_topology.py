"""Independent MFF topology audit using declared EEG streams and block sums."""
import csv,json,os,re,traceback
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
from mne.io.egi.general import _get_blocks,_get_signalfname
from audit_mff import xml,nodes,value,dump,table,j
from audit_other_eeg import token
BASE=Path(__file__).resolve().parents[1]
assert os.environ.get('SLURM_JOB_ID')
out=BASE/'results/mff_validation_001';out.mkdir(exist_ok=False);priv=BASE/'private/mff_validation_001';priv.mkdir(mode=0o700,exist_ok=False)
registry=json.loads((BASE/'private/probe_001/mff_registry.json').read_text());rows=[];rules=[];errors=[]
for r in registry:
 p=Path(r['path']);mid=r['container_id'];row={'container_id':mid,'status':'ok'};rows.append(row)
 try:
  info=xml(p/'info.xml');rt=value(info,'recordTime') if info is not None else '';m=re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.(\d{6}|\d{9})[+-]\d{2}:\d{2}',rt)
  if not m:raise ValueError('record_time_format_not_supported_no_unit_assumed')
  scale=1e6 if len(m[1])==6 else 1e9;row['epoch_time_unit']='us' if scale==1e6 else 'ns'
  sig=_get_signalfname(str(p))['EEG'];row['declared_eeg_binary']=sig['signal'];block=_get_blocks(str(p/sig['signal']));sf=block['sfreq'];counts=block['samples_block'];nc=block['n_channels']
  row.update(n_signal_channels=int(nc),sampling_rate_hz=int(sf),n_blocks=len(counts),n_samples=int(sum(counts)))
  ep=nodes(xml(p/'epochs.xml'),'epoch');badtime=0;badblock=0;badlength=0;prev=-1;allblock=[];maxdiff=0
  for e in ep:
   b=int(value(e,'beginTime'));end=int(value(e,'endTime'));first=int(value(e,'firstBlock'));last=int(value(e,'lastBlock'))
   badtime+=int(not (b<end and b>=prev));prev=end
   if not 1<=first<=last<=len(counts):badblock+=1;continue
   diff=abs((end-b)/scale*sf-sum(counts[first-1:last]));badlength+=diff>1e-5;maxdiff=max(maxdiff,float(diff));allblock.extend(range(first,last+1))
  row.update(n_epochs=len(ep),invalid_epoch_times=badtime,invalid_block_ranges=badblock,epoch_binary_length_mismatches=badlength,max_epoch_length_difference_samples=maxdiff,block_coverage_exact=allblock==list(range(1,len(counts)+1)))
  cats=xml(p/'categories.xml');co=0;nomatch=0;bounds={(int(value(e,'beginTime')),int(value(e,'endTime'))) for e in ep}
  if cats is not None:
   for seg in nodes(cats,'seg'):
    b=int(value(seg,'beginTime'));e=int(value(seg,'endTime'));ev=value(seg,'evtBegin');co+=bool(ev) and not b<=int(ev)<=e;nomatch+=(b,e) not in bounds
  row.update(category_events_outside_segments=int(co),category_segments_without_epoch_match=int(nomatch))
  hist=xml(p/'history.xml');category=''
  if hist is not None:
   for setting in nodes(hist,'setting'):
    text=(setting.text or '').strip();ma=re.search(r'Rules for category "([^"]+)"',text)
    if ma:category=ma[1]
    code=re.fullmatch(r'Code is "([^"]+)"',text)
    if code and category:rules.append({'container_id':mid,'category_token':token(category),'event_code_token':token(code[1]),'evidence':'history_exact_Code_is_rule','semantic_status':'historical_processing_rule_not_acoustic_validation'})
  row['extra_event_track_filenames'] = j([q.name for q in p.glob('*.xml') if q.name.lower().startswith('event') and not q.name.startswith('Events_')])
 except Exception as e:row['status']='error';row['error_class']=type(e).__name__;errors.append({'container_id':mid,'error':repr(e),'trace':traceback.format_exc()})
 if len(rows)%200==0:print(j({'containers_validated':len(rows)}),flush=True)
table(out/'topology.csv',rows);table(out/'historical_event_dictionary.csv',rules);dump(priv/'errors.json',errors)
dump(out/'summary.json',{'job_id':os.environ['SLURM_JOB_ID'],'containers_attempted':len(rows),'status':dict(Counter(r['status'] for r in rows)),'signal_binary_names':dict(Counter(r.get('declared_eeg_binary','') for r in rows)),'bad_epoch_time_containers':sum(r.get('invalid_epoch_times',0)>0 for r in rows),'bad_block_range_containers':sum(r.get('invalid_block_ranges',0)>0 for r in rows),'length_mismatch_containers':sum(r.get('epoch_binary_length_mismatches',0)>0 for r in rows),'incomplete_block_coverage_containers':sum(not r.get('block_coverage_exact',True) for r in rows),'category_time_problem_containers':sum(r.get('category_events_outside_segments',0)>0 for r in rows),'category_match_problem_containers':sum(r.get('category_segments_without_epoch_match',0)>0 for r in rows),'history_rule_pairs':dict(Counter(j([r['category_token'],r['event_code_token']]) for r in rules))})
