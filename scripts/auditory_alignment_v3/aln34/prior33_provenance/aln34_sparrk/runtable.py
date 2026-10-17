"""Read-only SparrKULee run table: preprocessed EEG headers (np.load mmap, allow_pickle=False), envelope headers, events.tsv,
save_metadata.json. No dataset code is run and no pickle is opened. Writes a JSON next to this script (scratchpad)."""
import collections, csv, glob, json, os, re, sys
import numpy as np
D = "/projects/EEG-foundation-model/auditory_public/sparrkulee_nm000238_v1.0.0"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runtable.json")
FLAG = {("006", "shortstories01", "06"), ("017", "shortstories01", "03"), ("048", "varyingStories05", "04")}
meta = json.load(open(f"{D}/derivatives/preprocessed_eeg/.save_metadata.json"))
pre = sorted(glob.glob(f"{D}/derivatives/preprocessed_eeg/sub-*/ses-*/*_eeg.npy"))
pat = re.compile(r"sub-(\d+)_ses-([A-Za-z0-9]+)_task-([A-Za-z]+)_run-(\d+)_desc-preproc-audio-(.+)_eeg\.npy$")
env = {}
for p in sorted(glob.glob(f"{D}/derivatives/preprocessed_stimuli/*.npy")):
    a = np.load(p, mmap_mode="r", allow_pickle=False); env[os.path.basename(p)[:-4]] = {"shape": list(a.shape), "dtype": str(a.dtype)}
runs = []
listed = {o: k for k, v in meta.items() for o in v}
for p in pre:
    rel = os.path.relpath(p, f"{D}/derivatives/preprocessed_eeg")
    m = pat.search(os.path.basename(p)); s, ses, task, run, stim = m.groups()
    a = np.load(p, mmap_mode="r", allow_pickle=False)
    r = {"sub": s, "ses": ses, "task": task, "run": run, "stim": stim, "shape": list(a.shape), "dtype": str(a.dtype),
         "fortran": bool(a.flags.f_contiguous and not a.flags.c_contiguous), "bytes": os.path.getsize(p),
         "in_meta": rel in listed, "raw": listed.get(rel), "flagged": (s, ses, run) in FLAG}
    ek = f"{stim}_envelope"; r["env_len"] = env[ek]["shape"][0] if ek in env else None
    evp = f"{D}/sub-{s}/ses-{ses}/eeg/sub-{s}_ses-{ses}_task-{task}_run-{run}_events.tsv"
    if os.path.exists(evp):
        rows = list(csv.DictReader(open(evp), delimiter="\t")); r["events"] = rows
    else:
        r["events"] = None
    runs.append(r)
missing = sorted(set(listed) - {os.path.relpath(p, f"{D}/derivatives/preprocessed_eeg") for p in pre})
# all listeningActive event files (incl. runs without a preprocessed file)
allev = []
for p in sorted(glob.glob(f"{D}/sub-*/ses-*/eeg/*_task-listeningActive_*_events.tsv")):
    rows = list(csv.DictReader(open(p), delimiter="\t")); allev.append({"file": os.path.basename(p), "rows": rows})
json.dump({"runs": runs, "env": env, "meta_entries": len(meta), "meta_outputs_missing_npy": missing, "events_files": allev,
           "raw_bdf_listening": len(glob.glob(f"{D}/sub-*/ses-*/eeg/*_task-listeningActive_*_eeg.bdf.gz")),
           "raw_bdf_rest": len(glob.glob(f"{D}/sub-*/ses-*/eeg/*_task-restingState_*_eeg.bdf.gz"))}, open(OUT, "w"))
print("runs", len(runs), "meta", len(meta), "missing", missing[:5], len(missing))
