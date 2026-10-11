"""FAU loader with a selectable stage-B EEG dataset (SCI_R1_PREREG §9, CI contamination sensitivity).

Textual copy of auditory_alignment.data.load_fau (that file is part of the ALN3 code hashes and is not edited) with one change:
the per-trial EEG dataset name is a parameter `key` (default 'eeg_1_20_ica' = the units' input; 'eeg_1_20_noica' = the same
1-20 Hz stage-B copy without the ICA component removal). Participants, folds, segments, targets and per-participant
standardisation are otherwise identical.
"""
from __future__ import annotations

import os

import h5py  # noqa: F401  (imported inside the copied body as well)
import numpy as np

from auditory_alignment.data import (AUDIO_FRAMES, FAU_CF, FAU_KCS, MAX_WIN_S, SEG_S, STAGEB, Cohort, _Bank, _segments_of, _stdz,
                                     fau_panel)


def load_fau(content_fold, kinds=("ss",), stage_dir=STAGEB, key="eeg_1_20_ica"):
    import h5py
    fs, guard = 128, 314
    seg_len = int(SEG_S * fs); margin = int(MAX_WIN_S * fs) + 1 + AUDIO_FRAMES
    dev, panel = fau_panel()
    plist = [{"id": s, "group": "th", "fold": -1, "dev": True} for s in dev] + \
            [{"id": s, "group": g, "fold": f, "dev": False} for s, (g, f) in sorted(panel.items())]
    tf = h5py.File(os.path.join(FAU_KCS, f"fau_cf{content_fold}.h5"), "r")
    targets = ("Ac", "Lz", "Local")
    sbank = {t: _Bank() for t in targets}
    soff = {}

    def stim_off(code, stream):
        key = (code, stream)
        if key not in soff:
            arrs = {t: tf[f"{code}/{stream}/{t}"][()] for t in targets}
            n = min(a.shape[1] for a in arrs.values())
            soff[key] = (sbank["Ac"].add(arrs["Ac"][:, :n]), n)
            for t in ("Lz", "Local"):
                assert sbank[t].add(arrs[t][:, :n]) == soff[key][0]
        return soff[key]
    ebank = _Bank(); segments = []
    for pi, p in enumerate(plist):
        with h5py.File(os.path.join(stage_dir, p["group"], f"{p['id']}.h5"), "r") as f:
            ch = [str(c) for c in f.attrs["channels"]]
            assert len(ch) == 31 and "IO2" not in ch
            trials = [(str(f[t].attrs["stimulus"]), f[t][key][()].astype(np.float64)) for t in sorted(f.keys())]
        trials = [(c, x) for c, x in trials if ("ss" in kinds and c[0] == "1") or ("cs" in kinds and c[0] == "2")]
        xs = _stdz([x for _, x in trials], guard)
        for (code, _), x in zip(trials, xs):
            kind = "ss" if code[0] == "1" else "cs"
            roles = FAU_CF[content_fold][kind]
            role = next(r for r, parts in roles.items() if code[2] in parts)
            sa, na = stim_off(code, "attended")
            si = stim_off(code, "distractor") if kind == "cs" else (None, None)
            n = min(x.shape[1], na, si[1] or na)
            e0 = ebank.add(x)
            for st in _segments_of(guard, n - guard, seg_len, margin):
                segments.append({"p": pi, "e0": e0 + st, "s0": sa + st, "s0_ign": (si[0] + st) if kind == "cs" else None,
                                 "role": role, "kind": kind, "uid": f"{code}@{st}", "hard_key": code[1], "part": code[2],
                                 "code": code})
    stim = {t: b.array() for t, b in sbank.items()}
    for s in segments:  # stimulus summary for hard candidates (Ac mean / SD over the segment)
        a = stim["Ac"][:, s["s0"]:s["s0"] + seg_len]
        s["feat"] = np.r_[a.mean(1), a.std(1)]
    return Cohort(fs, 31, plist, ebank.array(), stim, segments, {"dataset": "fau", "content_fold": content_fold, "seg_len": seg_len})
