"""Append the context-matched VLAAI shim (aln35.paper_ext_ctx_vlaai_fleet; frozen PROTOCOL in
results/.../external_decoders/context_matched) to the coordinator registry, last (lowest priority), with a backup and a receipt."""
import hashlib, importlib, json, os, shutil, stat
from pathlib import Path
assert os.environ.get('SLURM_JOB_ID')
ROOT = Path('/home/infres/yinwang/EEG_auditory'); REG = ROOT / 'private/auditory_alignment_v3/aln35/fleet_plugins.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
MOD, SB = 'auditory_alignment_v3.aln35.paper_ext_ctx_vlaai_fleet', 'slurm/aln35_paper_ext_ctx_vlaai.sbatch'
EXPECT = {'auditory_alignment_v3/paper/ext_context.py': '24c1390fa73a3736755b1a09a9a2adcd7c0cd48faffe8b405b6a60342b129f7a',
          'auditory_alignment_v3/paper/ext_context_vlaai.py': '1da423de47c00a0fabbc766a1712d99364a83453af2cf2e07b2134a7282b1f9e',
          'auditory_alignment_v3/aln35/paper_ext_ctx_vlaai_fleet.py': 'b430661c4a91bcb10ca5eab8b424e74f45bd8f0793b29ce2f50ad8fa6d45135e',
          SB: 'a7d0d89cfab51c3af697389f93a56af802cae20f69abd1a12c3f4f01fbbdb906',
          'results/auditory_alignment_v3/paper/external_decoders/context_matched/PROTOCOL.json': '28d829c6c7eeba5af93c326b13b582886f0d6fd043685643cebb21ca0cda0703'}
assert {p: sha(ROOT / p) for p in EXPECT} == EXPECT, 'reviewed files changed'
import auditory_alignment_v3.paper.ext_context_vlaai as V
plan = V.OUT / 'plan.json'
assert plan.exists() and not (plan.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)), 'plan not frozen 0444'
value = json.loads(REG.read_text())
m = importlib.import_module(MOD); st = m.fleet_status()
assert st['name'] == 'c3_s35pxvctx' and st['lane'] == 's35_paper_ext_vlaai_ctx' and 1 <= st['slots'] <= 2
assert st['state'] == 'ready' and st['submit'][0] == SB and f'#SBATCH --job-name={st["name"]}' in (ROOT / SB).read_text().splitlines()
assert not any(p['module'] == MOD or p['name'] == st['name'] for p in value['plugins'])
entry = dict(module=MOD, sha256=sha(m.__file__), name=st['name'], lane=st['lane'])
backup = REG.with_name(f'fleet_plugins_before_paper_ext_ctx_vlaai_{os.environ["SLURM_JOB_ID"]}_20261022.json'); shutil.copy2(REG, backup)
value['plugins'].append(entry)
tmp = REG.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2) + '\n'); os.replace(tmp, REG)
receipt = {'status': 'pass', 'job': os.environ['SLURM_JOB_ID'], 'entry': entry, 'backup': str(backup), 'position': len(value['plugins']) - 1,
           'readiness': {k: st.get(k) for k in ('state', 'ready', 'remaining', 'slots', 'submit')}, 'plan': str(plan), 'plan_sha256': sha(plan),
           'authorisation': 'researcher 2026-10-22 ~18:40: "两个都做吧，优先级放在现有实验之后" (Table 2 context-matched sensitivity; lowest registry position)',
           'shas': EXPECT}
out = Path(__file__).with_name(f'register_paper_ext_ctx_vlaai_{os.environ["SLURM_JOB_ID"]}_20261022.json'); out.write_text(json.dumps(receipt, indent=1, ensure_ascii=False) + '\n')
print(json.dumps({'entry': entry['name'], 'position': receipt['position'], 'readiness': receipt['readiness']}))
