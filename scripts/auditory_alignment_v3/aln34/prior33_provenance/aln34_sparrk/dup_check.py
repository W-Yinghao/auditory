"""Read-only duplicate-EEG check: sha1 of samples 1000..1499 (all 64 rows) of every preprocessed run, plus a near-duplicate check
(max |corr| between row 0 slices of runs of the same presentation)."""
import collections, hashlib, json, os
import numpy as np
D = "/projects/EEG-foundation-model/auditory_public/sparrkulee_nm000238_v1.0.0/derivatives/preprocessed_eeg"
HERE = os.path.dirname(os.path.abspath(__file__)); RT = json.load(open(os.path.join(HERE, "runtable.json")))
h = collections.defaultdict(list); sl = {}; bad = []
for r in RT["runs"]:
    p = f"{D}/sub-{r['sub']}/ses-{r['ses']}/sub-{r['sub']}_ses-{r['ses']}_task-{r['task']}_run-{r['run']}_desc-preproc-audio-{r['stim']}_eeg.npy"
    a = np.load(p, mmap_mode="r", allow_pickle=False); x = np.ascontiguousarray(a[:, 1000:1500])
    if not np.isfinite(x).all(): bad.append(p)
    h[hashlib.sha1(x.tobytes()).hexdigest()].append(f"{r['sub']}:{r['stim']}"); sl[(r["sub"], r["stim"])] = x
dups = {k: v for k, v in h.items() if len(v) > 1}
print("runs", len(RT["runs"]), "distinct slice hashes", len(h), "exact duplicates", dups, "non-finite in slice", len(bad))
by = collections.defaultdict(list)
for (s, st), x in sl.items(): by[st].append((s, x))
mx = 0; arg = None
for st, v in by.items():
    for i in range(len(v)):
        for j in range(i + 1, len(v)):
            c = abs(np.corrcoef(v[i][1].ravel(), v[j][1].ravel())[0, 1])
            if c > mx: mx, arg = c, (st, v[i][0], v[j][0])
print("max |corr| of 64x500 slices between two listeners of the same presentation: %.3f %s" % (mx, arg))
