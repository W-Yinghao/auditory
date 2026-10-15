#!/usr/bin/env python3
from pathlib import Path
import ast,hashlib,json,sys
import yaml
R=Path(__file__).resolve().parents[1]
errors=[]
required=['START_NOW.md','SERVER_START_PROMPT.md','SERVER_FULL_DOCUMENT.md','SOURCE_INDEX.json','configs/experiments.yaml']
for p in required:
    if not (R/p).exists():errors.append('Missing '+p)
for p in list((R/'src').rglob('*.py'))+list((R/'scripts').glob('*.py'))+list((R/'tests').glob('*.py')):
    try:ast.parse(p.read_text())
    except SyntaxError as e:errors.append(str(e))
for p in (R/'configs').glob('*.yaml'):
    try:yaml.safe_load(p.read_text())
    except Exception as e:errors.append(str(e))
c=yaml.safe_load((R/'configs/experiments.yaml').read_text())
ids=[x['id'] for x in c['families']]
if len(ids)!=len(set(ids)):errors.append('Duplicate logical comparison ID')
if c['inherited'][0]['expected_registered_rows']!=250:errors.append('Inherited row count changed')
if (R/'SHA256SUMS').exists():
    for line in (R/'SHA256SUMS').read_text().splitlines():
        h,name=line.split('  ',1);p=R/name
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=h:errors.append('Checksum '+name)
print(json.dumps({'valid':not errors,'comparison_families':len(ids),'errors':errors},ensure_ascii=False,indent=2))
if errors:raise SystemExit(1)
