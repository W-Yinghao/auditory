#!/usr/bin/env python3
"""Local structural/provenance validation. No external calls or EEG claims."""
from pathlib import Path
import ast, hashlib, json, re, sys
import yaml

ROOT=Path(__file__).resolve().parents[1]
def validate():
    errors=[]; counts={}
    for p in ROOT.rglob('*.py'):
        if '__pycache__' not in str(p):
            try:ast.parse(p.read_text())
            except SyntaxError as e:errors.append(f"syntax: {p.relative_to(ROOT)}: {e}")
    counts['python_sources']=len(list(ROOT.rglob('*.py')))
    for p in (ROOT/'configs').glob('*.yaml'):
        if not isinstance(yaml.safe_load(p.read_text()),dict):errors.append(f"bad config {p}")
    cards=json.loads((ROOT/'plans/comparison_cards.json').read_text())
    if len({c['id'] for c in cards})!=len(cards):errors.append('duplicate comparison id')
    for c in cards:
        for field in ('id','kind','question','reference','candidates','datasets','depends_on','output','status'):
            if field not in c:errors.append(f"missing card field {field}")
        if c.get('performance_entry_gate') is not None:errors.append('performance gate found')
    counts['comparison_cards']=len(cards)
    src=json.loads((ROOT/'SOURCE_INDEX.json').read_text())
    items=[{'package_path':src['B01']['package_copy'],'sha256':src['B01']['sha256']}]+src['P33']['inherited_files']
    for item in items:
        if hashlib.sha256((ROOT/item['package_path']).read_bytes()).hexdigest()!=item['sha256']:
            errors.append(f"source bytes changed: {item['package_path']}")
    counts['source_and_inherited_hashes']=len(items)
    for p in ROOT.rglob('*.md'):
        if p.parts[-2]=='sources':continue
        text=re.sub(r'```.*?```','',p.read_text(),flags=re.S)
        for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)',text):
            target=link.split('#')[0]
            if not target or target.startswith(('http:','https:','mailto:','sandbox:')):continue
            if not (p.parent/target).exists():errors.append(f"broken local link {p.relative_to(ROOT)} -> {target}")
    sums=ROOT/'SHA256SUMS'
    if sums.exists():
        manifest_paths=[]
        for line in sums.read_text().splitlines():
            digest,rel=line.split('  ',1);manifest_paths.append(rel)
            f=ROOT/rel
            if not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest()!=digest:errors.append(f"checksum mismatch {rel}")
        actual={str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and p.name!='SHA256SUMS' and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts}
        if actual!=set(manifest_paths):errors.append('manifest file list differs')
        counts['checksum_entries']=len(manifest_paths)
    return {'ok':not errors,'errors':errors,'counts':counts,'scope':'local artifact validation, not EEG/data/cluster validation'}
if __name__=='__main__':
    result=validate();print(json.dumps(result,ensure_ascii=False,indent=2));sys.exit(0 if result['ok'] else 1)
