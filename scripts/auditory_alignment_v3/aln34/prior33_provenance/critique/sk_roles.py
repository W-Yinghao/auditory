import glob, os, re, json, collections, sys
import numpy as np
D = sys.argv[1]
files = sorted(glob.glob(f"{D}/derivatives/preprocessed_eeg/sub-*/ses-*/*_eeg.npy"))
pat = re.compile(r"sub-(\d+)_ses-([A-Za-z]+\d+)_task-([A-Za-z]+)_run-(\d+)_desc-preproc-audio-(.+)_eeg\.npy$")
rows = []
for f in files:
    m = pat.search(os.path.basename(f))
    if not m:
        print("noparse", os.path.basename(f)); continue
    sub, ses, task, run, stim = m.groups()
    a = np.load(f, mmap_mode="r", allow_pickle=False)
    rows.append(dict(sub=sub, ses=ses, task=task, run=run, stim=stim, shape=a.shape, dtype=str(a.dtype)))
print("runs", len(rows), "tasks", collections.Counter(r["task"] for r in rows))
print("dtypes/channels", collections.Counter((r["dtype"], r["shape"][0]) for r in rows))
ses_by_sub = collections.defaultdict(set)
for r in rows: ses_by_sub[r["sub"]].add(r["ses"])
print("participants", len(ses_by_sub), "n sessions per participant", collections.Counter(len(v) for v in ses_by_sub.values()))
multi = {s: sorted(v) for s, v in ses_by_sub.items() if len(v) > 1}
print("multi-session participants", multi)
restricted = {"019", "020", "021", "022", "026"}
FIT = {"shortstories01"} | {f"varyingStories{i:02d}" for i in (1, 2, 3, 4, 8, 9, 10)}
DEV = {"varyingStories05", "varyingStories06"}; CAL = {"varyingStories07"}
def role(ses):
    return "fit" if ses in FIT else "dev" if ses in DEV else "cal" if ses in CAL else "other:" + ses
parts = collections.defaultdict(set); stims = collections.defaultdict(set); hours = collections.Counter()
sub_roles = collections.defaultdict(set)
for r in rows:
    if r["sub"] in restricted: continue
    ro = role(r["ses"]); sub_roles[r["sub"]].add(ro)
    parts[ro].add(r["sub"]); stims[ro].add(r["stim"]); hours[ro] += r["shape"][1] / 64 / 3600
print("roles participants", {k: len(v) for k, v in parts.items()}, "hours", {k: round(v, 1) for k, v in hours.items()})
print("participants in >1 role", {s: v for s, v in sub_roles.items() if len(v) > 1})
fam = lambda s: "audiobook_1" if s.startswith("audiobook_1_") or s == "audiobook_1" else s
for a in ("fit", "dev", "cal"):
    for b in ("fit", "dev", "cal"):
        if a < b:
            inter = {fam(x) for x in stims[a]} & {fam(x) for x in stims[b]}
            print("shared families", a, b, sorted(inter))
for ro in ("dev", "cal"):
    print(ro, "stims", sorted(stims[ro]))
lst = collections.defaultdict(set)
for r in rows:
    if r["sub"] in restricted: continue
    lst[(role(r["ses"]), r["stim"])].add(r["sub"])
single = sorted(k for k, v in lst.items() if len(v) == 1)
print("single-listener (role, stim)", single)
print("restricted runs", sum(r["sub"] in restricted for r in rows), "hours", round(sum(r["shape"][1] for r in rows if r["sub"] in restricted) / 64 / 3600, 2))
print("restricted sessions", sorted({(r["sub"], r["ses"]) for r in rows if r["sub"] in restricted}))
