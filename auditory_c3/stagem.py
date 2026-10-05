"""Stage M: minimal preprocessing of FAU/TUD (C3DL_PROTOCOL_v1_FROZEN.md §7). From the published 1 kHz data: drop the
auxiliary audio rows, keep the 30 EEG channels and IO2, realign by the stage-A aux lag, resample_poly to 128 Hz
(anti-aliasing included), linear detrend per trial. No band-pass, re-reference, interpolation or ICA; removed CI
electrodes are zero rows. Valid ranges are copied from stage B so that segments are identical.

Usage: python -m auditory_c3.stagem <grp> <subj>
"""
from __future__ import annotations

import os
import sys

import numpy as np
from scipy.signal import detrend

from .preproc import FAU_CH, H5, OUT as PRE, ROOT, _alignment_table, _rs

OUTM = os.path.join(PRE, "fau_tud_stageM")


def subject(grp, subj):
    import h5py
    out = os.path.join(OUTM, grp, f"{subj}.h5")
    if os.path.exists(out):
        return
    align = _alignment_table(grp)
    B = h5py.File(os.path.join(PRE, "fau_tud_stageB", grp, f"{subj}.h5"), "r")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = out + ".tmp"
    with h5py.File(os.path.join(ROOT, H5[grp]), "r") as f, h5py.File(tmp, "w") as o:
        sg = f["eeg"][subj]
        removed = [int(i) for i in np.atleast_1d(sg["taken_out_indices"][()])] if "taken_out_indices" in sg else []
        o.attrs.update(subject=subj, group=grp, fs=128, channels=FAU_CH, removed_rows=removed, reference="online Cz (recorded)",
                       stage="stage M (minimal): aux dropped, realigned, resample_poly 1000->128, linear detrend per trial")
        for t in sorted([k for k in sg.keys() if k.isdigit()], key=int):
            ds = sg[t]
            x = np.nan_to_num(ds[:31, :].astype(np.float64))
            x[removed] = 0.0
            lag, rr = align[(subj, int(t))]
            if rr >= 0.3 and abs(lag) > 5:  # same realignment rule as stage A
                z = np.zeros_like(x)
                if lag > 0:
                    z[:, :-lag] = x[:, lag:]
                else:
                    z[:, -lag:] = x[:, :lag]
                x = z
            y = detrend(_rs(x, 1000), axis=1)
            y[removed] = 0.0
            name = f"trial_{int(t):02d}"
            g = o.create_group(name)
            for k in ("stimulus", "valid_start", "valid_stop"):
                g.attrs[k] = B[name].attrs[k]
            n = B[name]["eeg_1_20_ica"].shape[1]
            y = y[:, :n] if y.shape[1] >= n else np.pad(y, ((0, 0), (0, n - y.shape[1])))
            g.create_dataset("eeg_min", data=y.astype(np.float32), compression="lzf")
    B.close()
    os.replace(tmp, out)
    print(grp, subj, "done", flush=True)


if __name__ == "__main__":
    subject(sys.argv[1], sys.argv[2])
