"""Read-only: full-run between-listener EEG similarity for one presentation (audiobook_14_2): channel-wise Pearson r at lag 0
(1-8 Hz), mean over channels, for all listener pairs; flags pairs far above the rest (possible duplicated recordings)."""
import itertools, json, os
import numpy as np
from scipy.signal import butter, sosfiltfilt
D = "/projects/EEG-foundation-model/auditory_public/sparrkulee_nm000238_v1.0.0/derivatives/preprocessed_eeg"
HERE = os.path.dirname(os.path.abspath(__file__)); RT = json.load(open(os.path.join(HERE, "runtable.json")))
sos = butter(4, [1, 8], btype="band", fs=64, output="sos"); stim = "audiobook_14_2"
X = {}
for r in RT["runs"]:
    if r["stim"] == stim:
        p = f"{D}/sub-{r['sub']}/ses-{r['ses']}/sub-{r['sub']}_ses-{r['ses']}_task-{r['task']}_run-{r['run']}_desc-preproc-audio-{r['stim']}_eeg.npy"
        x = sosfiltfilt(sos, np.load(p, allow_pickle=False), axis=1)[:, :r["env_len"]]
        X[r["sub"]] = ((x - x.mean(1, keepdims=True)) / x.std(1, keepdims=True)).astype(np.float32)
res = []
for a, b in itertools.combinations(sorted(X), 2):
    n = min(X[a].shape[1], X[b].shape[1]); res.append(((X[a][:, :n] * X[b][:, :n]).mean(), a, b))
res.sort(reverse=True); v = np.array([x[0] for x in res])
print("pairs", len(res), "mean-over-channels r: median %.4f q95 %.4f max %.4f" % (np.median(v), np.quantile(v, .95), v.max()))
print("top 5:", [(round(float(x[0]), 4), x[1], x[2]) for x in res[:5]])
