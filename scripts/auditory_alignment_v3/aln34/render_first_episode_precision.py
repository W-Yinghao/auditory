"""Display-only precision repair using the unchanged completed diagnostic JSON."""
import json
import os
from pathlib import Path
import shutil
from auditory_alignment_v3.aln34 import learning_budget as B
assert os.environ.get('SLURM_JOB_ID')
root=Path('/home/infres/yinwang/EEG_auditory')
j=root/'results/auditory_alignment_v3/aln34/episode_diagnostics/first_returned.json'
p=root/'docs/auditory_alignment_v3/FIRST_EPISODE_DIAGNOSTIC.md'
before=B.sha(j);r=json.loads(j.read_text())
backup=root/'private/auditory_alignment_v3/aln34/FIRST_EPISODE_DIAGNOSTIC.original_format_20261017.md'
if not backup.exists():shutil.copy2(p,backup)
lines=p.read_text().splitlines();selected=False;fixed=False
for i,line in enumerate(lines):
    if line.startswith('## Whole-pipeline'):selected=True;fixed=False
    if line.startswith('## Fixed outer'):selected=False;fixed=True
    if not line.startswith(('| 0.1 |','| 0.3 |')):continue
    fields=[v.strip() for v in line.strip('|').split('|')]
    if selected:
        x=next(x for x in r['selected'] if (x['support'],x['readout'])==tuple(fields[:2]))
        fields[-1]=f"{x['episode_vs_ordinary_benefit']:+.6e}"
    elif fixed:
        x=next(x for x in r['fixed_candidates'] if x['stage']=='outer' and (x['support'],x['steps'],x['readout'])==tuple(fields[:3]))
        fields[-2]=f"{x['episode_vs_ordinary_risk_benefit']:+.6e}"
        fields[-1]=f"{x['episode_vs_ordinary_mismatch_gain_change']:+.6e}"
    lines[i]='| '+' | '.join(fields)+' |'
lines += ['',f"Display precision updated by CPU job{os.environ['SLURM_JOB_ID']}: tiny differences use scientific notation. Numerical JSON unchanged (SHA256 `{before}`). Original rendering retained. [Weight-space diagnostic](FIRST_EPISODE_WEIGHT_DIAGNOSTIC.md)."]
p.write_text('\n'.join(lines)+'\n');assert B.sha(j)==before
print('Display-only precision PASS; unchanged JSON',before,flush=True)
