"""Engineering probe E_PUBLIC_TRANSFER (2 epochs, scratch dir): reve task_partial (ALN2 public donor, strict load) and
lag_local_tokens task_partial (donor = the scratch 2-epoch A_LOCAL FAU fold-0 unit; checks the tensor map and freezing)."""
import json, sys
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
from auditory_alignment_v3 import run as R3
S = "/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v3/probe_out"
rows = R3.load_rows()
pick = lambda **m: next(r for r in rows if r["family_id"] == "E_PUBLIC_TRANSFER" and r["subject_fold"] == 0 and r["seed"] == 3401 and all(r["spec"].get(k) == v for k, v in m.items()))
for r in (pick(source_architecture="reve", adaptation="task_partial", objective="CS_SINGLE"), pick(source_architecture="lag_local_tokens", adaptation="task_partial", objective="NCE")):
    R3.run_unit(r, S, epochs=2)
    rec = json.load(open(f"{S}/units/{r['experiment_id']}.json")); assert rec["status"] == "complete", rec.get("error")
    assert rec["code_hash"] == R3.code_hash("E_PUBLIC_TRANSFER") and "per_participant" in rec["eval"]
    tm = rec["transfer_map"]
    if r["spec"]["source_architecture"] == "lag_local_tokens":
        assert tm["frozen"] == tm["loaded"] and 0 < tm["loaded_param_fraction"] < 1 and not any(k.startswith("branches.0.local.0") for k in tm["loaded"]), tm
    else:
        il = tm["backbone_init_loaded"]; assert il and not il["missing"] and not il["unexpected"] and il["n_tensors"] > 50, il
    print("OK", r["spec"]["source_architecture"], json.dumps(tm)[:300], flush=True)
print("ALL TRANSFER PROBES PASSED")
