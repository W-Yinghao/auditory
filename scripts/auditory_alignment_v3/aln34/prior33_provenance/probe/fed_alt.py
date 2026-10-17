"""Read-only: Federici fold option B (HC-v as its own stratum, same _folds seed) vs the ALN2/ALN3 rule; file listings only."""
import glob, os, json
import numpy as np
FED = "/projects/EEG-foundation-model/auditory_public/derived/c3_preproc_v1/federici_ci_children"
def _folds(ids_by_group, seed=20261005, n=5):
    rng = np.random.default_rng(seed); out = {}
    for g in sorted(ids_by_group):
        ids = sorted(ids_by_group[g])
        for p_, i in enumerate(rng.permutation(len(ids))):
            out[ids[i]] = p_ % n
    return out
ppl = [(g, os.path.basename(p)[:-3]) for g in ("HC", "CI", "HC-v") for p in sorted(glob.glob(f"{FED}/{g}/*.h5"))]
A = _folds({"hc": sorted({f for g, f in ppl if g in ("HC", "HC-v")}), "ci": sorted({f"CI:{f}" for g, f in ppl if g == "CI"})})
fa = {(g, f): A[f if g != "CI" else f"CI:{f}"] for g, f in ppl}
B = _folds({"hc": sorted({f"HC:{f}" for g, f in ppl if g == "HC"}), "hcv": sorted({f"HC-v:{f}" for g, f in ppl if g == "HC-v"}),
            "ci": sorted({f"CI:{f}" for g, f in ppl if g == "CI"})})
fb = {(g, f): B[f"{g}:{f}"] for g, f in ppl}
same = {g: all(fa[(gg, f)] == fb[(gg, f)] for gg, f in ppl if gg == g) for g in ("HC", "CI", "HC-v")}
print(json.dumps({"membership_identical": same,
                  "hcv_option_B": {k: sorted(f for g, f in ppl if g == "HC-v" and fb[(g, f)] == k) for k in range(5)},
                  "hcv_with_same_number_hc_in_same_fold_B": sum(fb[("HC-v", f)] == fb[("HC", f)] for g, f in ppl if g == "HC-v")}, indent=1))
