"""Engineering probe B_LAYER_PROBE (full fit; scratch dir): CBraMod middle on DTU (64 channels) and REVE patch_embedding on
Federici (envelope); checks layer binding, PCA/ridge bookkeeping and the common evaluation."""
import json, sys
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
from auditory_alignment_v3 import run as R3
S = "/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v3/probe_out"
rows = R3.load_rows()
pick = lambda ds, **m: next(r for r in rows if r["family_id"] == "B_LAYER_PROBE" and r["dataset"] == ds and r["subject_fold"] == 0
                             and r["content_fold"] in (0, None) and all(r["spec"].get(k) == v for k, v in m.items()))
for r in (pick("dtu", architecture="cbramod", layer="middle"), pick("fau", architecture="reve", layer="last")):
    R3.run_unit(r, S)
    rec = json.load(open(f"{S}/units/{r['experiment_id']}.json")); assert rec["status"] == "complete", rec.get("error")
    assert rec["code_hash"] == R3.code_hash("B_LAYER_PROBE") and rec["pca_components"] == 256 and 0 < rec["pca_explained_variance"] <= 1
    assert rec["feature_dim"] == 9 * 257 + 1 and rec["n_fit_queries"] == 16 * rec["n_fit_segments"], (rec["feature_dim"], rec["n_fit_queries"], rec["n_fit_segments"])
    assert rec["alpha_rel_chosen"] in [c["alpha_rel"] for c in rec["alpha_curve"]] and "per_participant" in json.dumps(rec["eval"])[:100000]
    print("OK", r["dataset"], r["spec"]["architecture"], rec["layer_binding"], round(rec["pca_explained_variance"], 3), rec["alpha_rel_chosen"],
          [round(c["es_mean_corr"], 3) for c in rec["alpha_curve"]], rec["fit_seconds"], flush=True)
print("ALL LAYER PROBES PASSED")
