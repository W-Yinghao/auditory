"""Engineering probe A_LOCAL_FACTORS (2 epochs, scratch output; mechanics only)."""
import json, os, sys
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
from auditory_alignment_v3 import run as R3
S = "/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v3/probe_out"
rows = R3.load_rows(); ok = []
for arch, ds in (("lag_local_capacity_control", "fau"), ("local_unshared_control", "dtu")):
    i, r = next((i, r) for i, r in enumerate(rows) if r["family_id"] == "A_LOCAL_FACTORS" and r["dataset"] == ds and r["seed"] == 3401 and r["subject_fold"] == 0
                and (r["content_fold"] or 0) == 0 and r["spec"]["architecture"] == arch and r["spec"]["objective"] == "NCE")
    R3.run_unit(r, S, epochs=2)
    rec = json.load(open(f"{S}/units/{r['experiment_id']}.json")); assert rec["status"] == "complete", rec.get("error")
    cc = rec["capacity_control"]; assert cc["architecture"] == arch and cc["n_params"] == rec["encoder"]["n_params"], (cc, rec["encoder"])
    assert rec["code_hash"] == R3.code_hash("A_LOCAL_FACTORS")
    ok.append((arch, ds, cc)); print("OK", ok[-1], flush=True)
print("ALL FACTOR PROBES PASSED")
