"""W7 (CS dependence alignment) contrast families, frozen BEFORE any W7 output exists, together with the frozen design document
docs/auditory_alignment_v3/paper/W7_CS_DEPENDENCE_PREREG_FROZEN.md (made 0444 here).

Statistics for every family (as manuscript_families): person = unit; per-person values averaged over seeds (and content folds /
support draws) first; paired person bootstrap, B = 4000, bootstrap-t familywise max-|T*| simultaneous 95% intervals
(aln41.analysis.family); only people with every member available enter (coverage reported). Positive = the first-named system
better; loss-type endpoints (time_fixed_loss, attention20_nll_bits, age_abs_err, query NLL) are sign-flipped accordingly.

`python -m auditory_alignment_v3.paper.w7_families` (Slurm CPU) writes W7_FAMILIES_v1.json and W7_FREEZE_RECEIPT.json once and
refuses to change them.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from .. import core

ROOT = Path(core.REPO)
OUT = ROOT / 'results/auditory_alignment_v3/paper/w7'
DRAFT = ROOT / 'docs/auditory_alignment_v3/paper/W7_CS_DEPENDENCE_DESIGN_PREREG.md'
FROZEN = ROOT / 'docs/auditory_alignment_v3/paper/W7_CS_DEPENDENCE_PREREG_FROZEN.md'
ARMS = ('TCS_RES', 'TCS_PRES', 'TCS_RES_PRES', 'TCS_CCS')
PUBLIC = [(e, c) for e in ('content_direct_r', 'content_r', 'time_fixed_loss', 'attention20_acc', 'attention20_nll_bits') for c in ('dtu', 'fau')]
PRIVATE = [('content_hist_bits', 'private'), ('current_auc', 'private'), ('age_abs_err', 'private')]
LOSS = {'time_fixed_loss', 'attention20_nll_bits', 'age_abs_err'}


def families():
    F = []
    for e, c in PUBLIC + PRIVATE:
        F.append({'id': f'W7_FACT:{e}:{c}', 'endpoint': e, 'cohort': c, 'members': [f'{a}-TCS' for a in ARMS],
                  'sign': 'TCS - arm (positive = arm better)' if e in LOSS else 'arm - TCS (positive = arm better)'})
    F.append({'id': 'W7_ADAPT:private', 'endpoint': 'query NLL bits/trial at U30 (positive = first-named better)', 'cohort': 'private',
              'members': [f'{b}:{m}' for b in ('B0', 'TCS') for m in ('D_CS+cal-D_CE+cal', 'D_CS+cal-cal', 'D_CE+cal-cal')]})
    for c in ('dtu', 'fau'):
        F.append({'id': f'W7_RULE:{c}', 'endpoint': 'attention20_acc', 'cohort': c, 'members': [f'{b}:R-ridge' for b in ('B0', 'TCS', 'TNCE')],
                  'sign': 'R - ridge readout (two-sided)'})
    F.append({'id': 'W7_AUDIT:dtu', 'endpoint': 'per-person CS-QMI and its quantile in the 1,000-permutation null', 'cohort': 'dtu',
              'members': [f'{b}:{k}' for b in ('B0', 'TCS', 'TNCE') for k in ('real', 'noise_eeg', 'wrong_audio', 'identical_rows')],
              'descriptive': True})
    return F


HYPOTHESES = {'H1': 'TCS_RES > TCS on content_r, FAU and DTU (W7_FACT:content_r:*)',
              'H2': 'TCS_PRES < TCS on age_abs_err (W7_FACT:age_abs_err:private) and TCS_PRES not below TCS on DTU attention20_acc',
              'H3': 'TCS_CCS > TCS on content_r, FAU and DTU (W7_FACT:content_r:*); CCS mandatory (researcher)',
              'H4 (secondary)': 'D_CS+cal better than D_CE+cal on query NLL (W7_ADAPT:private)'}


def main():
    assert os.environ.get('SLURM_JOB_ID')
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    body = {'version': 'W7_FAMILIES_v1', 'families': families(), 'hypotheses': HYPOTHESES, 'arms': ARMS,
            'statistics': 'person bootstrap B=4000, bootstrap-t familywise max-|T*| simultaneous 95%; seeds averaged within person first'}
    fam = OUT / 'W7_FAMILIES_v1.json'
    if fam.exists():
        old = json.loads(fam.read_text()); assert all(old[k] == json.loads(json.dumps(v)) for k, v in body.items()), 'frozen families drift'
        print('unchanged', fam); return
    assert not FROZEN.exists(), 'frozen design exists without families'
    assert not any(OUT.glob('*RESULT*')) and not (Path(core.OUT) / 'paper' / 'w7_v1').exists(), 'W7 output exists before freeze'
    OUT.mkdir(parents=True, exist_ok=True)
    now = datetime.now().astimezone().isoformat()
    fam.write_text(json.dumps({**body, 'created': now, 'note': 'written before any W7 output existed'}, indent=1, ensure_ascii=False) + '\n')
    shutil.copyfile(DRAFT, FROZEN)
    for p in (fam, FROZEN):
        os.chmod(p, 0o444)
    DRAFT.write_text(f'# W7 design and pre-registration\n\nFrozen on {now[:16]}: see [W7_CS_DEPENDENCE_PREREG_FROZEN.md](W7_CS_DEPENDENCE_PREREG_FROZEN.md) '
                     f'(sha256 {sha(FROZEN)}). Changes only as appendices frozen before the corresponding results.\n')
    rec = {'frozen_at': now, 'job': os.environ['SLURM_JOB_ID'], 'design': str(FROZEN.relative_to(ROOT)), 'design_sha256': sha(FROZEN),
           'families': str(fam.relative_to(ROOT)), 'families_sha256': sha(fam), 'module_sha256': sha(__file__),
           'authorisation': ['2026-10-22 ~19:50 "都做，你建议的都做，你自己拿主意"',
                             '2026-10-22 ~19:55 "关于W7，必须CCS，其余的按你推荐的来。我记得儿童的是有trial的"'],
           'w7_outputs_at_freeze': 'none'}
    (OUT / 'W7_FREEZE_RECEIPT.json').write_text(json.dumps(rec, indent=1, ensure_ascii=False) + '\n'); os.chmod(OUT / 'W7_FREEZE_RECEIPT.json', 0o444)
    print(json.dumps(rec, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
