"""Move the Transformer-CLIP lane (c3_s35pxclp) to the end of the registry (lowest priority), then record the researcher's route
approval (ROUTE_APPROVED.json), with a backup and a receipt. Researcher, 2026-10-22: "训吧，但是优先级给低一些，优先完成其他的"."""
import hashlib, importlib, json, os, shutil
from datetime import datetime
from pathlib import Path
assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory'); REG = ROOT / 'private/auditory_alignment_v3/aln35/fleet_plugins.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
MOD, NAME = 'auditory_alignment_v3.aln35.paper_ext_clip_fleet', 'c3_s35pxclp'
QUOTE = '训吧，但是优先级给低一些，优先完成其他的'
value = json.loads(REG.read_text()); i = next(k for k, p in enumerate(value['plugins']) if p['module'] == MOD)
assert value['plugins'][i]['name'] == NAME and value['plugins'][i]['sha256'] == sha(importlib.import_module(MOD).__file__)
order_before = [p['name'] for p in value['plugins']]
backup = REG.with_name(f'fleet_plugins_before_clip_reorder_{os.environ["SLURM_JOB_ID"]}_20261022.json'); shutil.copy2(REG, backup)
moved = value['plugins'].pop(i); value['plugins'].append(moved)
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
from auditory_alignment_v3.paper import ext_clip as C
assert not C.APPROVAL.exists()
approval = {'approved': True, 'by': 'researcher', 'quote': QUOTE, 'date': '2026-10-22', 'created': datetime.now().astimezone().isoformat(),
            'route': 'released weights unavailable (README links 404 on 2026-10-22) -> official-code reproduction on public SparrKULee',
            'priority': 'lowest registry position; other paper lanes first', 'plan_sha256': sha(C.OUT / 'plan.json')}
C.APPROVAL.write_text(json.dumps(approval, indent=1, ensure_ascii=False) + '\n'); C.APPROVAL.chmod(0o444)
st = C.fleet_status()
rec = {'status': 'pass', 'job': os.environ['SLURM_JOB_ID'], 'moved': moved, 'from_index': i, 'to_index': len(value['plugins']) - 1,
       'order_before': order_before, 'order_after': [p['name'] for p in value['plugins']], 'backup': str(backup),
       'approval_file': str(C.APPROVAL), 'approval_sha256': sha(C.APPROVAL), 'quote': QUOTE,
       'readiness_after': {k: st.get(k) for k in ('state', 'ready', 'remaining', 'slots')}}
out = Path(__file__).with_name(f'reorder_paper_ext_clip_last_{os.environ["SLURM_JOB_ID"]}_20261022.json'); out.write_text(json.dumps(rec, indent=1, ensure_ascii=False) + '\n')
print(json.dumps({k: rec[k] for k in ('status', 'from_index', 'to_index', 'readiness_after')}, indent=1))
