"""Read-only: EEG hours per cohort / kind from HDF5 dataset shapes (no samples read)."""
import glob, json, os, collections
import h5py
PUB = "/projects/EEG-foundation-model/auditory_public/derived/c3_preproc_v1"
REPO = "/home/infres/yinwang/EEG_auditory"
out = {}
h = collections.Counter()
for g in ("th", "ha", "ci"):
    for p in glob.glob(f"{PUB}/fau_tud_stageB/{g}/*.h5"):
        with h5py.File(p, "r") as f:
            for t in f:
                code = str(f[t].attrs["stimulus"]); h[(g, "ss" if code[0] == "1" else "cs")] += f[t]["eeg_1_20_ica"].shape[1] / 128 / 3600
out["fau_hours_by_group_kind"] = {f"{k[0]}/{k[1]}": round(v, 2) for k, v in sorted(h.items())}
subs = sorted(os.path.basename(p)[:-5] for p in glob.glob(f"{REPO}/private/auditory_c3/public/dtu_v2/*.json"))
h = collections.Counter()
for s in subs:
    with h5py.File(f"{PUB}/dtu_snhl/{s}.h5", "r") as f:
        for t in f:
            h["two" if str(f[t].attrs["talkers"]) == "twotalker" else "single"] += f[t]["eeg_1_20"].shape[1] / 128 / 3600
out["dtu_hours_by_talkers_44_subjects"] = {k: round(v, 2) for k, v in h.items()}
h = collections.Counter(); nb = collections.Counter()
for g in ("HC", "CI", "HC-v", "Artifact"):
    for p in glob.glob(f"{PUB}/federici_ci_children/{g}/*.h5"):
        with h5py.File(p, "r") as f:
            sh = f["eeg"].shape; h[g] += sh[0] * sh[2] / 100 / 3600; nb[(g, sh[0])] += 1
out["federici_hours_by_group"] = {k: round(v, 2) for k, v in h.items()}
out["federici_blocks_per_file"] = {f"{k[0]}:{k[1]}": v for k, v in sorted(nb.items())}
print(json.dumps(out, indent=1))
