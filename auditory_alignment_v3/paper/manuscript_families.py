"""Manuscript v2 (2026-10-22) contrast families, frozen BEFORE any output of the new systems exists (manuscript §4.5: "The
additional external method families and their contrasts are fixed before new outputs are examined and reported separately
from internal ablations"). Earlier fixed ALN4.1 families (results/auditory_alignment_v3/aln41/r2/contrasts.json) keep their
scope and are not enlarged here.

Statistics for every family: person = unit; per-person values averaged over seeds (and support draws / content folds) first;
paired person bootstrap, B = 4000, bootstrap-t familywise max-|T*| simultaneous 95% intervals (aln41.analysis.family); only
people with every member available enter (coverage reported). Differences are oriented so that positive favours the
proposed temporal CS (TCS) unless stated.

`python -m auditory_alignment_v3.paper.manuscript_families` writes the JSON once (0444) and refuses to change it.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from .. import core

OUT = Path(core.REPO) / 'results/auditory_alignment_v3/paper/manuscript_v2/FAMILIES_v1.json'
EXT = ('mTRF', 'VLAAI', 'TCLIP', 'MINDMIX')          # Table 2 external systems
ENC = ('B0', 'REVE', 'MMB')                          # Table 3-5 transferred encoders (B0 = CBraMod EEG-only), MMB = MindMix aligned EEG branch
ALIGN = ('B0', 'CALRA', 'TNCE', 'THSIC', 'GCS', 'TCS_WRONG')   # Table 6 matched alignment rows other than TCS


def families():
    F = []
    for cohort in ('dtu', 'fau'):
        F.append({'id': f'T2_ACC:{cohort}', 'table': 2, 'endpoint': 'attention20_acc', 'unit': '20-s two-candidate accuracy',
                  'members': [f'TCS-{x}' for x in EXT], 'people': f'{cohort} all held-out people; hearing groups reported descriptively'})
        F.append({'id': f'T2_NLL:{cohort}', 'table': 2, 'endpoint': 'attention20_nll_bits', 'unit': 'bits/decision (lower is better)',
                  'members': [f'{x}-TCS' for x in EXT], 'people': f'{cohort} all held-out people'})
    F.append({'id': 'T3_FROZEN:private', 'table': 3, 'endpoint': ['current_auc', 'content_hist_bits'], 'unit': 'AUC; bits/trial',
              'members': [f'{e}:TCS-{x}' for e in ('current_auc', 'content_hist_bits') for x in ENC], 'people': '64 children'})
    F.append({'id': 'T3_FT:private', 'table': 3, 'endpoint': ['ft_auc', 'ft_nll_bits'], 'unit': 'AUC; bits/trial',
              'members': [f'ft_auc:TCS-{x}' for x in ENC] + [f'ft_nll_bits:{x}-TCS' for x in ENC], 'people': '64 children'})
    F.append({'id': 'T4_XS:bapa', 'table': 4, 'endpoint': ['transfer_auc', 'refit_auc'], 'unit': 'syllable child AUC',
              'members': [f'{e}:TCS-{x}' for e in ('transfer', 'refit') for x in ENC], 'people': '24 syllable-task children'})
    F.append({'id': 'T4_AGE:private', 'table': 4, 'endpoint': 'age_abs_err', 'unit': 'months (positive = TCS better)',
              'members': [f'{x}-TCS' for x in ENC + ('MEAN', 'RAW')], 'people': '64 children'})
    F.append({'id': 'T5_SUPPORT:private', 'table': 5, 'endpoint': 'query NLL gain over U0 at U30 (bits/trial)', 'unit': 'bits/trial',
              'members': [f'{x}:{m}' for x in ENC + ('TCS', 'TNCE') for m in ('delta_U30-U0', 'cal_U30-U0', 'delta_U30-cal_U30')],
              'people': '64 children'})
    for cohort in ('dtu', 'fau'):
        for e in ('content_direct_r', 'content_r'):
            F.append({'id': f'T6_{e}:{cohort}', 'table': 6, 'endpoint': e, 'unit': 'envelope r', 'members': [f'TCS-{x}' for x in ALIGN],
                      'people': cohort})
        F.append({'id': f'T6_TIME:{cohort}', 'table': 6, 'endpoint': 'time_fixed_loss', 'unit': 'W0->W2 fixed-readout loss in r (positive = TCS loses less)',
                  'members': [f'{x}-TCS' for x in ALIGN], 'people': cohort})
    F.append({'id': 'T6_CHILD:private', 'table': 6, 'endpoint': 'content_hist_bits', 'unit': 'bits/trial', 'members': [f'TCS-{x}' for x in ALIGN],
              'people': '64 children'})
    return F


def main():
    body = {'version': 'MANUSCRIPT_V2_FAMILIES_v1', 'families': families(),
            'statistics': 'person bootstrap B=4000, bootstrap-t familywise max-|T*| simultaneous 95%; seeds averaged within person first',
            'systems': {'EXT': EXT, 'ENC': ENC, 'ALIGN': ALIGN}}
    if OUT.exists():
        old = json.loads(OUT.read_text()); assert all(old[k] == json.loads(json.dumps(v)) for k, v in body.items()), 'frozen families drift'
        print('unchanged', OUT); return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({**body, 'created': datetime.now().astimezone().isoformat(),
                               'note': 'written before any output of mTRF/VLAAI/TCLIP/MindMix-FAU/REVE/MMB/CALRA/THSIC existed'}, indent=1) + '\n')
    os.chmod(OUT, 0o444); print('written', OUT)


if __name__ == '__main__':
    main()
