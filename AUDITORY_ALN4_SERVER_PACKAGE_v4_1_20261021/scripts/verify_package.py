from pathlib import Path
import hashlib,json,sys

root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'MANIFEST.json').read_text())
bad=[]
for row in manifest['files']:
    p=root/row['path']
    if not p.is_file():bad.append({'path':row['path'],'error':'missing'});continue
    digest=hashlib.sha256(p.read_bytes()).hexdigest()
    if digest!=row['sha256'] or p.stat().st_size!=row['bytes']:bad.append({'path':row['path'],'error':'bytes/hash mismatch'})
print(json.dumps({'status':'PASS' if not bad else 'FAIL','checked_files':len(manifest['files']),
                 'scope':'manifest bytes only; not model/data correctness','errors':bad},indent=2))
sys.exit(bool(bad))
