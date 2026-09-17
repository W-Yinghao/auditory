import csv,hashlib,json,os,re,traceback
from pathlib import Path
from collections import defaultdict,Counter
from datetime import datetime
from audit_mff import xml,nodes,value,table,dump,j
from audit_other_eeg import token
BASE=Path(__file__).resolve().parents[1]
assert os.environ.get('SLURM_JOB_ID')
out=BASE/'results/mff_recovery_001';out.mkdir(exist_ok=False);priv=BASE/'private/mff_recovery_001';priv.mkdir(mode=0o700,exist_ok=False)
reg=json.loads((BASE/'private/mff_001/registry.json').read_text());history=json.loads((BASE/'private/mff_001/history.json').read_text());index=list(csv.DictReader((BASE/'results/mff_001/container_index.csv').open()));errors=json.loads((BASE/'private/mff_001/errors.json').read_text());byid={r['container_id']:r for r in reg};byname=defaultdict(list);bypath={r['path']:r['container_id'] for r in reg}
for r in reg:byname[Path(r['path']).name].append(r['container_id'])
edges=[];unresolved=[]
for h in history:
 mid=h['container_id'];p=Path(byid[mid]['path'])
 for src in sorted(set(h['source_paths'])):
  name=src.replace('\\','/').rsplit('/',1)[-1];near=str(p.parent/name);candidates=[bypath[near]] if near in bypath else byname.get(name,[])
  candidates=[c for c in candidates if c!=mid]
  if len(candidates)==1:edges.append({'child_container_id':mid,'parent_container_id':candidates[0],'match_status':'candidate','evidence':'history_source_name_same_directory' if near in bypath else 'history_source_name_unique_in_scope'})
  elif name:unresolved.append({'container_id':mid,'source_name':name,'n_candidates':len(candidates)})
# These components reflect documented processing links, not confirmed acquisitions/children.
parent={r['container_id']:r['container_id'] for r in reg}
def root(x):
 while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
 return x
for e in edges:
 a,b=root(e['child_container_id']),root(e['parent_container_id'])
 if a!=b:parent[b]=a
components=Counter(root(x) for x in parent)
table(out/'provenance_edges.csv',edges);table(out/'processing_components.csv',[{'container_id':x,'candidate_processing_component':root(x),'n_versions_in_component':components[root(x)],'identity_status':'not_inferred'} for x in parent])
failed={e['container_id'] for e in errors};recovered=[];newerrors=[]
with (out/'event_ledger_recovered.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['container_id','track_basename','event_1based','code_token','onset_s','duration_native','time_unit','numeric_keys'])
 for mid in sorted(failed):
  p=Path(byid[mid]['path']);rt=byid[mid].get('record_time','');counts=Counter();empty=0;bad=0;origin=datetime.fromisoformat(rt) if rt else None;unit='ns' if re.search(r'\.\d{9}[+-]',rt) else 'us'
  for track in sorted(p.glob('Events_*.xml')):
   if track.stat().st_size==0:empty+=1;continue
   try:
    t=xml(track)
    for ei,e in enumerate(nodes(t,'event'),1):
     code=token(value(e,'code'));ts=value(e,'beginTime');onset=(datetime.fromisoformat(ts)-origin).total_seconds() if ts and origin else ''
     kv={value(k,'keyCode'):value(k,'data') for k in nodes(e,'key')};numeric={k:v for k,v in kv.items() if re.fullmatch(r'[-+]?\d+(\.\d+)?',v)}
     counts[code]+=1;w.writerow([mid,track.name,ei,code,onset,value(e,'duration'),unit,j(numeric)])
   except Exception as e:bad+=1;newerrors.append({'container_id':mid,'track':str(track),'error':repr(e)})
  recovered.append({'container_id':mid,'empty_event_track_files':empty,'bad_nonempty_event_track_files':bad,'n_recovered_event_entries':sum(counts.values()),'event_code_counts':j(counts),'status':'nonempty_tracks_parsed' if bad==0 else 'partial','signal_read_status':'use_topology_validation'})
table(out/'recovery_summary.csv',recovered);dump(priv/'unresolved_lineage.json',unresolved);dump(priv/'errors.json',newerrors)
# Canonical row for each original storage epoch, with no duplication between runs.
table(out/'recovery_rules.csv',[{'rule':'event_ledger_use','value':'Exclude all failed-container rows from mff_001/event_ledger.csv, then append event_ledger_recovered.csv. Do not concatenate unfiltered.'}])
dump(out/'summary.json',{'job_id':os.environ['SLURM_JOB_ID'],'containers_revisited':len(recovered),'empty_event_tracks':sum(r['empty_event_track_files'] for r in recovered),'remaining_nonempty_event_track_failures':sum(r['bad_nonempty_event_track_files'] for r in recovered),'recovered_event_entries':sum(r['n_recovered_event_entries'] for r in recovered),'history_parent_edges':len(edges),'candidate_processing_components':len(components),'components_with_multiple_versions':sum(v>1 for v in components.values()),'unresolved_history_references':len(unresolved),'notice':'History components are provenance candidates. No participant/acquisition count is established by this graph.'})
