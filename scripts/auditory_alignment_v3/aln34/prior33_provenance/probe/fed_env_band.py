"""Read-only: Federici author-cache envelope band (Welch PSD of the cached env rows) and array shapes."""
import glob, json, os, sys
import numpy as np, h5py
from scipy.signal import welch
FED = "/projects/EEG-foundation-model/auditory_public/derived/c3_preproc_v1/federici_ci_children"
out = {}
for grp in ("HC", "CI", "HC-v", "Artifact"):
    fs_ = sorted(glob.glob(os.path.join(FED, grp, "*.h5")))
    shapes, attrs = set(), None
    P = []
    for p in fs_:
        with h5py.File(p, "r") as f:
            shapes.add((tuple(f["eeg"].shape), tuple(f["env"].shape) if "env" in f else None))
            if attrs is None:
                attrs = {k: (str(v)[:200]) for k, v in f.attrs.items() if k in ("fs", "note", "channels")}
            if "env" in f and len(P) < 40:
                env = f["env"][()].astype(np.float64)
                for e in env:
                    fr, pp = welch(e - e.mean(), fs=100, nperseg=1024); P.append(pp)
    P = np.median(np.array(P), 0); ref = np.median(P[(fr >= 3) & (fr <= 7)]); db = 10 * np.log10(P / ref + 1e-30)
    def edge(rng, thr):
        for i in rng:
            if db[i] < thr: return float(fr[i])
        return None
    inb = np.flatnonzero((fr >= 3) & (fr <= 7))
    out[grp] = {"n_files": len(fs_), "shapes": sorted(map(str, shapes))[:6], "attrs": attrs,
                "env_minus3dB_low": edge(range(inb[0], -1, -1), -3), "env_minus3dB_high": edge(range(inb[-1], len(fr)), -3),
                "env_minus20dB_low": edge(range(inb[0], -1, -1), -20), "env_minus20dB_high": edge(range(inb[-1], len(fr)), -20),
                "env_db_at": {str(h): round(float(db[np.argmin(np.abs(fr - h))]), 1) for h in (0.2, 0.5, 1, 1.5, 2, 8, 9, 10, 12, 15, 20)}}
print(json.dumps(out, indent=1))
