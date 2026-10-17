import glob, os, re, collections, sys
import numpy as np
D = sys.argv[1]
pat = re.compile(r"sub-(\d+)_ses-([A-Za-z]+\d+)_task-([A-Za-z]+)_run-(\d+)_desc-preproc-audio-(.+)_eeg\.npy$")
restricted = {"019", "020", "021", "022", "026"}
FIT = {"shortstories01"} | {f"varyingStories{i:02d}" for i in (1, 2, 3, 4, 8, 9, 10)}
DEV = {"varyingStories05", "varyingStories06"}; CAL = {"varyingStories07"}
role = lambda s: "fit" if s in FIT else "dev" if s in DEV else "cal"
envT = {}
runs = []
for f in sorted(glob.glob(f"{D}/derivatives/preprocessed_eeg/sub-*/ses-*/*_eeg.npy")):
    sub, ses, task, run, stim = pat.search(os.path.basename(f)).groups()
    if sub in restricted: continue
    T = np.load(f, mmap_mode="r", allow_pickle=False).shape[1]
    if stim not in envT:
        envT[stim] = np.load(f"{D}/derivatives/preprocessed_stimuli/{stim}_envelope.npy", mmap_mode="r", allow_pickle=False).shape[0]
    runs.append((sub, role(ses), stim, T, envT[stim]))
# exclusions named in the design
excl = {("051", "audiobook_12_2"), ("011", "audiobook_6_1")}
runs = [r for r in runs if (r[0], r[2]) not in excl and r[2] != "audiobook_1_artefact"]
# audiobook_1 only in fit
runs = [r for r in runs if not (r[2] == "audiobook_1" and r[1] != "fit")]
lst = collections.defaultdict(set)
for r in runs: lst[(r[1], r[2])].add(r[0])
def nseg(T, Te, s_first=128, end_guard=128):
    m = 0; n = 0
    while True:
        s = s_first + 320 * m
        if s + 357 <= T - end_guard and s + 327 <= Te - 41: n += 1; m += 1
        else: return n
out = collections.Counter(); cont = collections.defaultdict(dict)
for sub, ro, stim, T, Te in runs:
    if len(lst[(ro, stim)]) < 2: continue
    n = nseg(T, Te); out[ro] += n
    cont[ro][stim] = max(cont[ro].get(stim, 0), n)
for ro in ("fit", "dev", "cal"):
    print(ro, "listener segments", out[ro], f"({out[ro]*5/3600:.1f} h)", "content segments", sum(cont[ro].values()), f"({sum(cont[ro].values())*5/3600:.2f} h)", "presentations", len(cont[ro]))
print("1 ep-eq anchors", 8 * out["fit"], "steps", 8 * out["fit"] / 256, "S0 steps", 30 * 8 * out["fit"] / 256)
