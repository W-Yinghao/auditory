import csv,json,os,struct,hashlib
from pathlib import Path
from collections import Counter,defaultdict
from audit_mff import dump,table,j
BASE=Path(__file__).resolve().parents[1]
assert os.environ.get('SLURM_JOB_ID')
out=BASE/'results/assets_001';out.mkdir(exist_ok=False);priv=BASE/'private/assets_001';priv.mkdir(mode=0o700,exist_ok=False)
mapping=list(csv.DictReader((BASE/'private/inventory_001/file_path_map.csv').open()));mff=json.loads((BASE/'private/mff_001/registry.json').read_text());known={r['path'] for r in mff}
extra=[]
for base,dirs,files in os.walk('/projects/EEG-foundation-model/auditory'):
 p=Path(base)
 if p.suffix.lower()=='.mff' and str(p) not in known:extra.append({'path':str(p),'n_immediate_files':len(files),'n_immediate_subdirs':len(dirs),'subdirs':dirs})
assets=[];conditions=[];cands=defaultdict(set)
for r in mff:
 p=Path(r['path']);parts=[q.lower() for q in p.parts];cond=next((q for q in parts if q in ('ci-quiet-front','ci-quiet-left','ci-quiet-right','ci-noise-front','ci-noise-left','ci-noise-right','ciha-quiet-front','ciha-quiet-left','ciha-quiet-right','ciha-noise-front','ciha-noise-left','ciha-noise-right')),None)
 if cond:
  pos=parts.index(cond);pk='D'+hashlib.sha256(str(Path(*p.parts[:pos])).encode()).hexdigest()[:12];cands[pk].add(cond)
  conditions.append({'container_id':r['container_id'],'candidate_directory_participant':pk,'condition_clue':cond,'condition_status':'directory_label_not_acquisition_verified'})
for r in mapping:
 p=Path(r['absolute_path']);ext=p.suffix.lower()
 if ext=='.png':
  with p.open('rb') as f:h=f.read(24)
  width,height=struct.unpack('>II',h[16:24]) if h.startswith(b'\x89PNG') else ('','')
  assets.append({'file_id':r['file_id'],'format':'PNG','width':width,'height':height,'filename_type':'screenshot' if 'screen' in p.name.lower() or '屏幕' in p.name else 'other','content_status':'not_all_visually_reviewed'})
 elif ext=='.avi':assets.append({'file_id':r['file_id'],'format':'AVI','bytes':p.stat().st_size,'content_status':'not_reviewed'})
table(out/'visual_assets.csv',assets);table(out/'condition_clues.csv',conditions);dump(priv/'unassigned_mff_directories.json',extra)
dump(out/'summary.json',{'job_id':os.environ['SLURM_JOB_ID'],'mff_directories_without_directly_assigned_files':len(extra),'unassigned_directory_shapes':[{'n_immediate_files':e['n_immediate_files'],'n_immediate_subdirs':e['n_immediate_subdirs']} for e in extra],'asset_formats':dict(Counter(r['format'] for r in assets)),'condition_clue_export_counts':dict(Counter(r['condition_clue'] for r in conditions)),'candidate_directory_groups_with_device_noise_side_labels':len(cands),'candidate_groups_with_both_ci_and_ciha_labels':sum(any(v.startswith('ci-') for v in s) and any(v.startswith('ciha-') for v in s) for s in cands.values()),'notice':'Directory labels are provenance clues. They do not confirm device activation, stimulus intensity, independent children, or visits.'})
