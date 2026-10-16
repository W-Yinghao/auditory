import glob, json, os, h5py, numpy as np
PUB = "/projects/EEG-foundation-model/auditory_public"
out = {}
def attrs(f):
    return {k: (v.tolist() if hasattr(v, "tolist") else str(v))[:80] if isinstance(v, (str, bytes)) else (v.tolist() if hasattr(v, "tolist") else str(v)) for k, v in f.attrs.items()}
p = sorted(glob.glob(f"{PUB}/derived/c3_preproc_v1/dtu_snhl/*.h5"))[0]
with h5py.File(p) as f:
    out["dtu_keys"] = list(f.keys())[:20]; out["dtu_attrs"] = {k: str(v)[:400] for k, v in f.attrs.items()}
tsv = glob.glob(f"{PUB}/dtu_snhl/ds-eeg-snhl/ds-eeg-snhl/sub-001/eeg/*channels.tsv")
out["dtu_channels_tsv"] = open(tsv[0]).read()[:1500] if tsv else None
p = sorted(glob.glob(f"{PUB}/derived/c3_preproc_v1/federici_ci_children/HC/*.h5"))[0]
with h5py.File(p) as f:
    out["fed_keys"] = list(f.keys()); out["fed_attrs"] = {k: str(v)[:400] for k, v in f.attrs.items()}; out["fed_eeg_shape"] = list(f["eeg"].shape)
out["fed_raw_listing"] = sorted(os.listdir(f"{PUB}"))[:40]
p = sorted(glob.glob(f"{PUB}/derived/c3_preproc_v1/fau_tud_stageB/*/*.h5"))[0]
with h5py.File(p) as f:
    out["fau_attrs"] = {k: str(v)[:300] for k, v in f.attrs.items()}
print(json.dumps(out, indent=1))
