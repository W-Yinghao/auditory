"""Read-only: DTU cross-person key coverage from trial attributes (no EEG arrays read)."""
import json, collections, glob, os
import numpy as np, h5py
F = "/projects/EEG-foundation-model/auditory_public/derived/c3_features_v1/dtu"
PRE = "/projects/EEG-foundation-model/auditory_public/derived/c3_preproc_v1/dtu_snhl"
REPO = "/home/infres/yinwang/EEG_auditory"
inv = json.load(open(f"{F}/inventory.json")); cg = json.load(open(f"{F}/kcs_targets_v1/content_groups.json"))["content"]
sha = {(r["file"], r["trial"], r["kind"]): r["sha"] for r in inv}
hi = {r["file"]: r["hi"] for r in inv}
subs = sorted(os.path.basename(p)[:-5] for p in glob.glob(f"{REPO}/private/auditory_c3/public/dtu_v2/*.json"))
key = collections.defaultdict(set); dur = collections.defaultdict(float); n_trials = collections.Counter()
for s in subs:
    with h5py.File(f"{PRE}/{s}.h5", "r") as f:
        for k in sorted(f.keys()):
            g = f[k]; two = str(g.attrs["talkers"]) == "twotalker"
            th = sha.get((s, k, "target"))
            if th is None or th not in cg: continue
            m = sha.get((s, k, "masker")) if two else None
            n_trials[("two" if two else "single", hi[s])] += 1
            kk = (cg[th]["group"], "two" if two else "single", (cg[m]["group"] if m in cg else m[:8]) if two else None, "HI" if hi[s] else "NH")
            key[kk].add(s); dur[kk] += g["eeg_1_20"].shape[1] / 128.0 / 3600 / max(1, 1)
print("trials by (talkers, hi)", dict(n_trials))
for cond in ("single", "two"):
    for grp in ("NH", "HI"):
        ks = [k for k in key if k[1] == cond and k[3] == grp]
        n = np.array([len(key[k]) for k in ks])
        print(cond, grp, "keys", len(ks), "listeners median", float(np.median(n)) if len(n) else None, "keys with >=2 listeners", int((n >= 2).sum()),
              "trials on >=2-listener keys", int(sum(len(key[k]) for k in ks if len(key[k]) >= 2)), "of", int(sum(len(key[k]) for k in ks)))
# relaxed: ignore hearing group (content group + condition + masker group)
k2 = collections.defaultdict(set)
for k, v in key.items(): k2[k[:3]] |= v
n = np.array([len(v) for v in k2.values()])
print("relaxed keys (group, cond, masker) ignoring NH/HI:", len(k2), "median", float(np.median(n)), ">=2", int((n >= 2).sum()))
