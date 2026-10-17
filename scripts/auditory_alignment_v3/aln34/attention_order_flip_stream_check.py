"""Training-side check of the shared flip stream: saved legacy intercept vs logit(share of label-1 presentations) regenerated
from rng(seed + 4242) and the recorded training window counts (consumption order L x readout x window, fit only with >= 20)."""
import json, os, collections
import numpy as np
from auditory_alignment_v3 import run as r3
rows = r3.all_rows()
OUT = "private/auditory_alignment_v3"
res = collections.defaultdict(list)
for r in rows:
    s = r["spec"]
    if r["family_id"] != "D_ATTENTION" or s.get("integrator") != "mean_score" or r["seed"] != 3401 or s.get("architecture") != "lag_local_tokens":
        continue
    P = os.path.join(OUT, "units", r["experiment_id"] + ".json")
    R = json.load(open(P)) if os.path.exists(P) else {}
    if R.get("status") != "complete":
        continue
    aw = R["eval"]["attention_windows"]
    rng = np.random.default_rng(r["seed"] + 4242)
    for L in (5, 10, 20):
        n = aw["window_counts"][str(L)]["train"]
        for kr in ("unified", "native"):
            if n < 20:
                continue
            u = rng.random(n)
            share1 = float(np.mean(u >= 0.5))   # flip = u < 0.5 -> label 0; label 1 otherwise
            ig = aw["integrators"][f"{L}s|{kr}"]
            res[(s["architecture"], r["dataset"], s["objective"], L, kr)].append((share1, ig["intercept"], float(np.max(np.abs(ig["coef"]))), n))
print("arch ds obj L readout | n_units | corr(b0, logit share) | sign agree | median b0 | median logit(share) | share<0.5 | median max|w|")
for k, v in sorted(res.items(), key=str):
    sh, b0, mw, n = map(np.array, zip(*v))
    lg = np.log(sh / (1 - sh))
    c = float(np.corrcoef(b0, lg)[0, 1]) if len(v) > 2 and np.std(lg) > 0 and np.std(b0) > 0 else float("nan")
    print(k, len(v), f"{c:+.4f}", f"{int(np.sum(np.sign(b0) == np.sign(lg)))}/{len(v)}", f"{np.median(b0):+.4f}", f"{np.median(lg):+.4f}",
          f"{np.mean(sh < 0.5):.2f}", f"{np.median(mw):.3g}", f"max|b0-logit| {np.max(np.abs(b0 - lg)):.2e}")
