"""Freeze the cross-stimulus identity -> fold tables (private; identity keys) from the frozen plan's gated records, before
any cross-stimulus readout; the readout's fit_rows() recomputes the same rule and is checked against this table."""
import json, os
from pathlib import Path
from auditory_alignment_v3.aln41 import cross_stim as XS
assert os.environ.get('SLURM_JOB_ID')
plan = XS.read(XS.OUT / 'plan.json')
ids = {l: sorted({r['identity'] for r in plan['records'] if r['lane'] == l}) for l in XS.LANES}
table = {'version': 'ALN42_CROSS_STIM_FOLD_TABLE_v1', 'plan_sha256': XS.sha(XS.OUT / 'plan.json'), 'rule': plan['folds'],
         'bapa': XS.fold_of(ids['mff_bapa']), 'puretone': XS.fold_of(ids['mff_puretone'])}
out = Path('private/auditory_alignment_v3/aln42/intake/cross_stim_fold_table.json')
out.write_text(json.dumps(table, indent=1, sort_keys=True) + '\n'); out.chmod(0o600)
print({k: len(v) for k, v in table.items() if isinstance(v, dict)}, XS.sha(out))
