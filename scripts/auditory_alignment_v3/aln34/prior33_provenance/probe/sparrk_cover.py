"""Read-only: SparrKULee cross-person coverage. Shapes from .npy headers (mmap, allow_pickle=False), metadata JSON only.
Counts EEG hours (64 Hz) usable against the stimulus envelope (min(T_eeg, T_env)) on content keys heard by >= 2 participants."""
import collections, glob, json, os, re
import numpy as np
D = "/projects/EEG-foundation-model/auditory_public/sparrkulee_nm000238_v1.0.0"
FLAG = {("006", "shortstories01", "06"), ("017", "shortstories01", "03"), ("048", "varyingStories05", "04")}
meta = json.load(open(f"{D}/derivatives/preprocessed_eeg/.save_metadata.json"))
envlen = {}
for p in glob.glob(f"{D}/derivatives/preprocessed_stimuli/*_envelope*.npy"):
    envlen[os.path.basename(p)] = np.load(p, mmap_mode="r", allow_pickle=False).shape
runs = []
for raw, outs in meta.items():
    m = re.match(r"sub-(\d+)_ses-([A-Za-z0-9]+)_task-[A-Za-z]+_run-(\d+)_eeg\.bdf\.gz", raw)
    if not m:
        continue
    for o in outs:
        stim = re.search(r"desc-preproc-audio-(.+)_eeg\.npy$", o).group(1)
        sh = np.load(f"{D}/derivatives/preprocessed_eeg/{o}", mmap_mode="r", allow_pickle=False).shape
        ek = f"{stim}_envelope.npy"
        runs.append({"sub": m.group(1), "ses": m.group(2), "run": m.group(3), "stim": stim, "T_eeg": sh[1], "C": sh[0],
                     "T_env": envlen.get(ek, (None,))[0], "flag": m.groups() in FLAG})
base = lambda s: s.replace("_shifted", "")
lis = collections.defaultdict(set); lis_content = collections.defaultdict(set)
for r in runs:
    if not r["flag"]:
        lis[r["stim"]].add(r["sub"]); lis_content[base(r["stim"])].add(r["sub"])
tot = sum(min(r["T_eeg"], r["T_env"] or 0) for r in runs if not r["flag"]) / 64 / 3600
elig = sum(min(r["T_eeg"], r["T_env"] or 0) for r in runs if not r["flag"] and len(lis[r["stim"]]) >= 2) / 64 / 3600
noenv = [r["stim"] for r in runs if r["T_env"] is None]
cnt = np.array([len(v) for v in lis.values()])
# hours per stimulus (distinct audio)
aud = sum(envlen[f"{k}_envelope.npy"][0] for k in lis if f"{k}_envelope.npy" in envlen) / 64 / 3600
top = sorted(((len(v), k) for k, v in lis.items()), reverse=True)[:6]
ses = collections.Counter(r["ses"] for r in runs)
sub_ses = collections.defaultdict(set)
for r in runs: sub_ses[r["sub"]].add(r["ses"])
print(json.dumps({"runs": len(runs), "flagged": sum(r["flag"] for r in runs), "channels": sorted({r["C"] for r in runs}),
                  "runs_without_envelope": sorted(set(noenv)), "eeg_hours_overlapping_envelope": round(tot, 2),
                  "eeg_hours_on_stimuli_heard_by_ge2": round(elig, 2), "stimuli": len(lis), "stimuli_heard_by_ge2": int((cnt >= 2).sum()),
                  "content_keys_shifted_merged": len(lis_content), "distinct_audio_hours": round(aud, 2), "top_shared": top,
                  "sessions": dict(ses), "sessions_per_subject": dict(collections.Counter(len(v) for v in sub_ses.values())),
                  "shortstories_subjects": sum(1 for v in sub_ses.values() if "shortstories01" in v)}, indent=1))
