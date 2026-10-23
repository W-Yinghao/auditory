"""Correction wrapper for the complete-MindMix audit summary (2026-10-22 21:20).

Bug in mindmix_dropkey_audit.py (v1, frozen, sha c6b7587a...) summarize(), repeated in mindmix_dropkey_audit_a1.py (appendum 01): each unit's audit.npz is read into a plain dict
(`Z = {k: z[k] for k in z.files}`) and then passed to unit_quantities(), which iterates `Z.files` -> AttributeError before any
quantity is computed. This wrapper passes unit_quantities a dict subclass that also exposes `.files` (the same key list, in the
same order as the npz); every value, quantity, aggregate and reading rule is v1's / appendum 01's code unchanged. Neither
mindmix_dropkey_audit.py nor mindmix_dropkey_audit_a1.py is edited (both are byte-checked by their fleet shims).

python -m auditory_alignment_v3.paper.mindmix_dropkey_summarize_v2   (CPU, Slurm; after all v1 and appendum units are complete)
"""
from __future__ import annotations

import functools
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

from . import mindmix_dropkey_audit as V, mindmix_dropkey_audit_a1 as A1


class _NpzDict(dict):
    @property
    def files(self):
        return list(self.keys())


def _fixed(fn):
    @functools.wraps(fn)                                               # keeps __doc__ (appendum summarize embeds it)
    def wrapper(Z, pre):
        return fn(_NpzDict(Z), pre)
    return wrapper


def main():
    assert os.environ.get('SLURM_JOB_ID'); os.umask(0o022)
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    orig, orig_a1 = V.unit_quantities, A1.unit_quantities              # the same bug is in both modules' unit_quantities
    V.unit_quantities = _fixed(orig); A1.unit_quantities = _fixed(orig_a1)
    try:
        A1.summarize()
    finally:
        V.unit_quantities, A1.unit_quantities = orig, orig_a1
    rec = {'created': datetime.now().astimezone().isoformat(), 'job': os.environ['SLURM_JOB_ID'],
           'bug': 'v1 and appendum-01 summarize pass a dict to unit_quantities, which iterates Z.files (AttributeError, no output written)',
           'fix': 'dict subclass exposing .files = list(keys); no computation changed',
           'shas': {p: sha(Path(__file__).parent / p) for p in ('mindmix_dropkey_audit.py', 'mindmix_dropkey_audit_a1.py', Path(__file__).name)}}
    out = V.OUT / 'SUMMARY_CORRECTION_RECEIPT.json'; out.write_text(json.dumps(rec, indent=1) + '\n')
    print(json.dumps(rec, indent=1))


if __name__ == '__main__':
    main()
