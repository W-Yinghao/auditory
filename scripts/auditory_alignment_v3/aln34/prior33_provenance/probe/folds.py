"""Read-only: reproduce the ALN2/ALN3 subject folds (auditory_alignment.data._folds, seed 20261005, n=5) from file listings and
participants.tsv only (no EEG read). Prints per-fold counts by group; public ids are printed, private only counts."""
import glob, json, os, collections
import numpy as np
REPO = "/home/infres/yinwang/EEG_auditory"
PUB = "/projects/EEG-foundation-model/auditory_public"
def _folds(ids_by_group, seed=20261005, n=5):
    rng = np.random.default_rng(seed); out = {}
    for g in sorted(ids_by_group):
        ids = sorted(ids_by_group[g])
        for p_, i in enumerate(rng.permutation(len(ids))):
            out[ids[i]] = p_ % n
    return out
res = {}
# FAU
STAGEB = f"{PUB}/derived/c3_preproc_v1/fau_tud_stageB"
split = json.load(open(f"{REPO}/private/auditory_c3/public/fau_tud/th_split.json"))
ids = {"th": sorted(split["heldout_half"]), "ha": sorted(os.path.basename(p)[:-3] for p in glob.glob(f"{STAGEB}/ha/*.h5")),
       "ci": sorted(os.path.basename(p)[:-3] for p in glob.glob(f"{STAGEB}/ci/*.h5"))}
f = _folds(ids)
res["fau"] = {"dev_always_train_th": sorted(split["selection_half"]),
              "folds": {k: {g: sorted(s for s in ids[g] if f[s] == k) for g in ids} for k in range(5)}}
# DTU
import csv
part = list(csv.DictReader(open(f"{PUB}/dtu_snhl/ds-eeg-snhl/ds-eeg-snhl/participants.tsv"), delimiter="\t"))
hs = {r["participant_id"]: r["hearing_status"] for r in part}
subs = sorted(os.path.basename(p)[:-5] for p in glob.glob(f"{REPO}/private/auditory_c3/public/dtu_v2/*.json"))
g = {k: [s for s in subs if hs[s] == k] for k in ("nh", "hi")}
f = _folds(g)
res["dtu"] = {"n": len(subs), "folds": {k: {gg: sorted(s for s in g[gg] if f[s] == k) for gg in g} for k in range(5)}}
# Federici (ALN2 identity rule: HC and HC-v share the file-number identity)
FED = f"{PUB}/derived/c3_preproc_v1/federici_ci_children"
people = []
for grp in ("HC", "CI", "HC-v", "Artifact"):
    for p in sorted(glob.glob(f"{FED}/{grp}/*.h5")):
        fid = os.path.basename(p)[:-3]
        people.append((grp, fid, fid if grp in ("HC", "HC-v") else f"{grp}:{fid}"))
idents = {"hc": sorted({q[2] for q in people if q[0] in ("HC", "HC-v")}), "ci": sorted({q[2] for q in people if q[0] == "CI"})}
f = _folds(idents)
fo = {k: collections.Counter() for k in range(5)}
merged = 0
for grp, fid, ident in people:
    if grp == "Artifact": continue
    fo[f[ident]][grp] += 1
hcv = {fid for grp, fid, _ in people if grp == "HC-v"}; hc = {fid for grp, fid, _ in people if grp == "HC"}
res["federici"] = {"n_by_group": dict(collections.Counter(q[0] for q in people)), "n_identity_strata": {k: len(v) for k, v in idents.items()},
                   "hcv_ids_sharing_hc_number": len(hcv & hc), "hcv_ids": sorted(hcv),
                   "fold_counts": {k: dict(v) for k, v in fo.items()},
                   "folds_ids": {k: {grp: sorted(fid for gg, fid, ident in people if gg == grp and gg != "Artifact" and f[ident] == k) for grp in ("HC", "CI", "HC-v")} for k in range(5)}}
# Federici alternative: HC-v separate identities (ALN3.1 rule), same seed/stratification would change the assignment
idents2 = {"hc": sorted({f"{q[0]}:{q[1]}" for q in people if q[0] == "HC"}), "hcv": sorted({f"{q[0]}:{q[1]}" for q in people if q[0] == "HC-v"}),
           "ci": sorted({f"CI:{q[1]}" for q in people if q[0] == "CI"})}
f2 = _folds(idents2)
fo2 = {k: collections.Counter() for k in range(5)}
for grp, fid, _ in people:
    if grp == "Artifact": continue
    fo2[f2[f"{grp}:{fid}"]][grp] += 1
res["federici_alt_separate_hcv_strata"] = {k: dict(v) for k, v in fo2.items()}
print(json.dumps(res, indent=1))
