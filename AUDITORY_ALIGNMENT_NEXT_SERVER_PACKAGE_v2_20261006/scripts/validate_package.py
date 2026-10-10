#!/usr/bin/env python3
"""Check package files, JSON, generated plan schemas and Python syntax. No real training."""
from __future__ import annotations
import ast,json,re
from pathlib import Path
from datetime import datetime,timezone
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1]

def main():
    errors=[];checked={}
    for p in ROOT.rglob('*.py'):
        try:ast.parse(p.read_text(encoding='utf-8'))
        except Exception as ex:errors.append(f'{p.relative_to(ROOT)}: {ex}')
    checked['python_syntax_files']=len(list(ROOT.rglob('*.py')))
    for p in ROOT.rglob('*.json'):
        try:json.loads(p.read_text(encoding='utf-8'))
        except Exception as ex:errors.append(f'{p.relative_to(ROOT)}: {ex}')
    checked['json_files']=len(list(ROOT.rglob('*.json')))
    schema=json.loads((ROOT/'schemas/plan_record.schema.json').read_text())
    validator=Draft202012Validator(schema)
    ids=set();n=0
    with (ROOT/'plans/planned_comparisons.jsonl').open(encoding='utf-8') as f:
        for i,line in enumerate(f):
            r=json.loads(line);n+=1
            if r['experiment_id'] in ids:errors.append(f'duplicate id: {r["experiment_id"]}')
            ids.add(r['experiment_id'])
            for ex in validator.iter_errors(r):errors.append(f'plan line {i+1}: {ex.message}')
    checked['plan_records_schema_validated']=n
    required=['README.md','SERVER_START_PROMPT.md','AGENTS_APPEND.md','slurm_unit.template.sh']
    for name in required:
        if not (ROOT/name).is_file():errors.append(f'missing: {name}')
    for p in ROOT.rglob('*.md'):
        for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            if re.match(r'^[a-zA-Z]+:',link) or link.startswith('#'):continue
            path=link.split('#')[0]
            if path and not (p.parent/path).exists():errors.append(f'{p.relative_to(ROOT)} broken link {link}')
    checked['markdown_files']=len(list(ROOT.rglob('*.md')))
    receipt={'scope':'Packaging, syntax and plan validation only; not a dataset, training or clinical validation.',
             'checked':checked,'errors':errors,'successful':not errors}
    (ROOT/'receipts/PACKAGE_VALIDATION.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False,indent=2))
    raise SystemExit(1 if errors else 0)
if __name__=='__main__':main()
