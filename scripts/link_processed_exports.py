import csv,json,os,re,hashlib
from pathlib import Path
from collections import defaultdict,Counter
from audit_mff import dump,table,j
BASE=Path(__file__).resolve().parents[1]
assert os.environ.get('SLURM_JOB_ID')
out=BASE/'results/processed_link_001';out.mkdir(exist_ok=False)
paths={r['file_id']:Path(r['absolute_path']) for r in csv.DictReader((BASE/'private/inventory_001/file_path_map.csv').open())}
vendor=json.loads((BASE/'private/linkage_001/vendor_identity_records.json').read_text());sets=list(csv.DictReader((BASE/'results/other_eeg_001/set_index.csv').open()));events=list(csv.DictReader((BASE/'results/other_eeg_001/event_ledger.csv').open()));pairs=list(csv.DictReader((BASE/'results/signal_001/bdf_pairing.csv').open()));pairs={r['candidate_acquisition_id']:r for r in pairs};ev=defaultdict(list)
for e in events:
 if e['event_code_token'] in ('1','2'):ev[e['file_id']].append(e['event_code_token'])
def nk(s):
 m=re.match(r'[\u4e00-\u9fff]+',str(s));return m[0] if m else ''
def date(s):
 m=re.search(r'(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})',str(s));return '-'.join([m[1],m[2].zfill(2),m[3].zfill(2)]) if m else ''
rows=[]
for s in sets:
 fid=s['file_id'];p=paths[fid];name=nk(p.parent.name);dt=date(p.parent.name);matches=[v for v in vendor if v['namekey']==name and (not dt or dt==v['date'])]
 row={'file_id':fid,'data_level':s['data_level'],'directory_group_clue':'NH' if 'NH' in p.parts else 'HA' if 'HA' in p.parts else 'unknown','n_raw_acquisition_candidates':len(matches),'link_status':'candidate_only','n_code_1_2_events':len(ev[fid])}
 if len(matches)==1:
  gid=matches[0]['candidate_acquisition_id'];eventfid=pairs[gid]['event_file_id'];a=ev[fid];b=ev[eventfid]
  row.update(candidate_acquisition_id=gid,raw_event_file_id=eventfid,n_raw_code_1_2_events=len(b),exact_stimulus_code_sequence_match=a==b)
  k=0
  for code in b:
   if k<len(a) and a[k]==code:k+=1
  row['processed_code_sequence_is_raw_subsequence']=k==len(a)
 rows.append(row)
table(out/'processed_to_raw_candidates.csv',rows)
dump(out/'summary.json',{'job_id':os.environ['SLURM_JOB_ID'],'n_set_exports':len(rows),'level_by_directory_group':dict(Counter(j([r['data_level'],r['directory_group_clue']]) for r in rows)),'single_raw_candidate':sum(r['n_raw_acquisition_candidates']==1 for r in rows),'exact_code_sequence_matches':sum(r.get('exact_stimulus_code_sequence_match',False) for r in rows),'subsequence_matches':sum(r.get('processed_code_sequence_is_raw_subsequence',False) for r in rows),'notice':'Code sequence agreement supports provenance, not acoustic code meaning or event/data clock correction.'})
