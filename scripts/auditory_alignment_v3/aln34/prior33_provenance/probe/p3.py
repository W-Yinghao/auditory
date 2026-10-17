"""Read-only: .npy headers (shape/dtype) of SparrKULee preprocessed EEG and envelopes -> hours per stimulus, listeners per stimulus,
EEG hours whose stimulus is heard by >= 2 participants (cross-person eligible pool, before any split). No pickles, no dataset code."""
import collections, glob, os, re, sys
import numpy as np
D = "/projects/EEG-foundation-model/auditory_public/sparrkulee_nm000238_v1.0.0/derivatives"
FLAG = {("006", "shortstories01", "06"), ("017", "shortstories01", "03"), ("048", "varyingStories05", "04")}
runs = sorted(glob.glob(f"{D}/preprocessed_eeg/sub-*/ses-*/*_eeg.npy"))
per_stim = collections.defaultdict(lambda: [0, set()]); tot = 0; flagged = 0; nrun = 0; shapes = collections.Counter(); bad = []
for p in runs:
    b = os.path.basename(p)
    m = re.match(r"sub-(\d+)_ses-([A-Za-z0-9]+)_task-[A-Za-z]+_run-(\d+)_desc-preproc-audio-(.+)_eeg\.npy$", b)
    if not m:
        bad.append(b); continue
    sub, ses, run, stim = m.groups()
    a = np.load(p, mmap_mode="r", allow_pickle=False)
    shapes[(a.shape[0], str(a.dtype))] += 1
    if (sub, ses, run) in FLAG:
        flagged += 1; continue
    T = a.shape[1]; tot += T; nrun += 1
    per_stim[stim][0] += T; per_stim[stim][1].add(sub)
fs = 64
elig = sum(T for T, s in per_stim.values() if len(s) >= 2)
print("runs", len(runs), "used", nrun, "flagged", flagged, "unparsed", len(bad), bad[:3], "shapes", dict(shapes))
print(f"EEG hours used {tot / fs / 3600:.1f}; in stimuli heard by >=2 participants {elig / fs / 3600:.1f} ({100 * elig / tot:.1f} %)")
print("5-s windows (all used EEG)", tot // (5 * fs), "| eligible", elig // (5 * fs))
env = sorted(glob.glob(f"{D}/preprocessed_stimuli/*_envelope*.npy"))
el = {}
for p in env:
    a = np.load(p, mmap_mode="r", allow_pickle=False); el[os.path.basename(p)] = a.shape
print("envelope files", len(env), "total h", round(sum(s[0] for s in el.values()) / fs / 3600, 2), "shape example", next(iter(el.items())))
top = sorted(per_stim.items(), key=lambda kv: -kv[1][0])[:6]
print("top stimuli by EEG hours:", [(k, round(v[0] / fs / 3600, 1), len(v[1])) for k, v in top])
lis = sorted(len(v[1]) for v in per_stim.values())
print("stimuli", len(per_stim), "listeners per stimulus quantiles", np.quantile(lis, [0, .25, .5, .75, 1]).tolist())
pairs = sum(len(v[1]) * (len(v[1]) - 1) // 2 for v in per_stim.values())
print("distinct listener pairs summed over stimuli", pairs)
