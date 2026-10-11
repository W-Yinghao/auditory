#!/usr/bin/env python3
"""Validate plan/schema/source links and local Python syntax. No training/network."""
from pathlib import Path
import argparse,ast,hashlib,json,re
import jsonschema,yaml


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    args=p.parse_args(); root=args.root
    for schema in (root/'schemas').glob('*.json'):
        jsonschema.Draft202012Validator.check_schema(json.loads(schema.read_text()))
    plan=[json.loads(x) for x in (root/'plans/units.jsonl').read_text().splitlines() if x.strip()]
    validator=jsonschema.Draft202012Validator(json.loads((root/'schemas/plan.schema.json').read_text()))
    for row in plan: validator.validate(row)
    assert len(plan)==len({r['experiment_id'] for r in plan})
    py=list(root.rglob('*.py'))
    for path in py: ast.parse(path.read_text(),filename=str(path))
    for path in (root/'configs').glob('*.yaml'): yaml.safe_load(path.read_text())
    links=0
    for path in root.rglob('*.md'):
        for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)',path.read_text()):
            if '://' in link or link.startswith('#'): continue
            if not (path.parent/link.split('#')[0]).exists():
                raise AssertionError(f'Broken link {path.relative_to(root)}: {link}')
            links+=1
    if (root/'SHA256SUMS').exists():
        checks=0
        for line in (root/'SHA256SUMS').read_text().splitlines():
            expected,name=line.split('  ',1)
            assert hashlib.sha256((root/name).read_bytes()).hexdigest()==expected,name
            checks+=1
    else: checks=0
    out={'status':'passed','plan_records_validated':len(plan),'python_sources_parsed':len(py),'local_links_checked':links,
         'checksums_verified':checks,'real_EEG_training_performed':False}
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
