#!/usr/bin/env python3
"""Small, Slurm-only environment and structure summary after the inventory."""
import csv
import hashlib
import importlib.metadata as md
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import platform
import shutil
import sys
import zipfile

BASE = Path(__file__).resolve().parents[1]
if not os.environ.get('SLURM_JOB_ID'):
    raise SystemExit('Submit through Slurm')
PRIVATE = BASE / 'private' / 'discovery_001'
PRIVATE.mkdir(mode=0o700, exist_ok=False)
OUT = BASE / 'results' / 'discovery_001'
OUT.mkdir(exist_ok=False)
rows = list(csv.DictReader((BASE/'private/inventory_001/file_path_map.csv').open()))
sizes = {r['file_id']:int(r['size_bytes']) for r in csv.DictReader((BASE/'results/inventory_001/file_inventory.csv').open())}
env = {'utc': datetime.now(timezone.utc).isoformat(), 'slurm_job_id': os.environ['SLURM_JOB_ID'],
       'python':sys.version, 'executable':sys.executable, 'hostname':platform.node(),
       'slurm_cpus':os.environ.get('SLURM_CPUS_PER_TASK'), 'affinity_cpus':len(os.sched_getaffinity(0)),
       'packages':{}, 'disk':{}, 'memory':{}}
for pkg in ('numpy','scipy','pandas','mne','h5py','openpyxl','xlrd','matplotlib','pymatreader','pyedflib','python-docx','pypdf'):
    try: env['packages'][pkg]=md.version(pkg)
    except md.PackageNotFoundError: env['packages'][pkg]=None
for alias,p in [('workspace',BASE),('data','/projects/EEG-foundation-model/auditory')]:
    env['disk'][alias]=dict(zip(('total','used','free'), shutil.disk_usage(p)))
for line in Path('/proc/meminfo').read_text().splitlines():
    if line.startswith(('MemTotal:','MemAvailable:')):
        k,v=line.split(':',1); env['memory'][k]=v.strip()
(OUT/'environment.json').write_text(json.dumps(env,indent=2))
groups=defaultdict(lambda: {'count':0,'bytes':0,'suffixes':Counter()})
private_listing=[]
archives=[]
for r in rows:
    p=Path(r['relative_path']); parts=p.parts
    branch='/'.join(parts[:min(2,len(parts)-1)])
    g=groups[branch]; g['count']+=1; g['bytes']+=sizes[r['file_id']]; g['suffixes'][p.suffix.lower()]+=1
    private_listing.append({'file_id':r['file_id'],'relative_path':str(p),'bytes':sizes[r['file_id']]})
    if p.suffix.lower()=='.zip':
        try:
            with zipfile.ZipFile(r['absolute_path']) as z:
                items=[{'name':x.filename,'size':x.file_size,'compressed':x.compress_size} for x in z.infolist()]
            archives.append({'file_id':r['file_id'],'items':items})
        except Exception as e: archives.append({'file_id':r['file_id'],'error':repr(e)})
(PRIVATE/'listing.json').write_text(json.dumps(private_listing,ensure_ascii=False,indent=2))
(PRIVATE/'archives.json').write_text(json.dumps(archives,ensure_ascii=False,indent=2))
public=[]; branch_map=[]
for i,(name,g) in enumerate(sorted(groups.items()),1):
    alias=f'B{i:03d}'; public.append({'branch_id':alias,**g}); branch_map.append({'branch_id':alias,'path':name})
(PRIVATE/'branch_map.json').write_text(json.dumps(branch_map,ensure_ascii=False,indent=2))
(OUT/'structure_summary.json').write_text(json.dumps({'branches':public,'total_bytes':sum(sizes.values()),'n_files':len(rows)},indent=2))
with (OUT/'workspace_manifest.csv').open('w') as f:
    w=csv.writer(f); w.writerow(['path','bytes','sha256'])
    paths=[BASE/'EEG_project_restart_EN_20260916_v1.zip',*sorted((BASE/'server_restart_en_v1').rglob('*'))]
    for p in paths:
        if p.is_file(): w.writerow([str(p.relative_to(BASE)),p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest()])
print(json.dumps({'files':len(rows),'bytes':sum(sizes.values()),'branches':len(groups),'packages':env['packages']},indent=2))
