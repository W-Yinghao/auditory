"""Read-only channel-identity check of preprocessed rows: per row i, similarity (Pearson r) between its 1-8 Hz channel-correlation
profile C[i, :] in a test run and in a reference (mean over 6 other participants' runs of the same stimulus). A displaced row shows a low
self-similarity and a higher similarity to another reference row. Tests sub-015..018 (raw labels 'P07'/'P03' typo) and 2 controls."""
import json, os
import numpy as np
from scipy.signal import butter, sosfiltfilt
D = "/projects/EEG-foundation-model/auditory_public/sparrkulee_nm000238_v1.0.0/derivatives/preprocessed_eeg"
HERE = os.path.dirname(os.path.abspath(__file__)); RT = json.load(open(os.path.join(HERE, "runtable.json")))
sos = butter(4, [1, 8], btype="band", fs=64, output="sos")
def C(r):
    p = f"{D}/sub-{r['sub']}/ses-{r['ses']}/sub-{r['sub']}_ses-{r['ses']}_task-{r['task']}_run-{r['run']}_desc-preproc-audio-{r['stim']}_eeg.npy"
    x = sosfiltfilt(sos, np.asarray(np.load(p, mmap_mode="r", allow_pickle=False)[:, :300 * 64]), axis=1)
    return np.corrcoef(x)
by = {}
for r in RT["runs"]: by.setdefault(r["stim"], []).append(r)
stim = "audiobook_2_1"
tests = [r for r in by[stim] if r["sub"] in ("015", "016", "017", "018", "001", "007")]
refs = [r for r in by[stim] if r["sub"] in ("002", "003", "004", "005", "008", "009")]
Cr = np.mean([C(r) for r in refs], axis=0); iu = ~np.eye(64, dtype=bool)
for r in tests:
    Ct = C(r); S = np.array([[np.corrcoef(Ct[i][iu[i]], Cr[j][iu[i]])[0, 1] if True else 0 for j in range(64)] for i in range(64)])
    self_ = np.diag(S); best = S.argmax(1)
    print(f"sub-{r['sub']} {stim}: self-similarity median {np.median(self_):.3f} min {self_.min():.3f} (row {self_.argmin()}); rows whose best match is another row: {[(i, int(best[i])) for i in range(64) if best[i] != i]}; rows 24/25 self {self_[24]:.3f}/{self_[25]:.3f}")
