"""Engineering probe for the D_COVERAGE complement_policy arm (ADDENDUM_04; 2 epochs, scratch dir probe_out): policy and
same-population lag base resolve; the residual starts at its base; both sampling controls complete; code_group coverage_policy."""
import json, sys
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
from auditory_alignment_v3 import run as R3, core, registry, fm_dense, run_coverage_policy as RCP
fm_dense.WARMUP, fm_dense.UNFREEZE_EVERY = 1, 1
registry.POLICY_GROUP["D_COVERAGE"] = "coverage_policy"  # probe process only
S = "/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v3/probe_out"
rows = R3.all_rows(); core.load_rows = lambda: rows
r = next(r for r in rows if r["family_id"] == "D_COVERAGE" and r["spec"].get("architecture") == "complement_policy" and r["seed"] == 3401
         and r["subject_fold"] == 0 and r["content_fold"] == 0 and r["spec"]["population"] == "TH_HA" and r["spec"]["objective"] == "NCE")
assert RCP.lag_base_ready(r, rows) is not None, "lag base not ready"
R3.run_unit(r, S, epochs=2)
rec = json.load(open(f"{S}/units/{r['experiment_id']}.json"))
assert rec["status"] == "complete" and rec["code_group"] == "coverage_policy", rec.get("error")
var = rec["policy"]["chosen_spec"]["variant"]
for c in RCP.CONTROLS:
    f = rec["fits"][c]; d0 = f.get("init_max_abs_diff_vs_base")
    print(c, "chosen", rec["policy"]["chosen"], var, rec["policy"]["chosen_spec"]["architecture"], "| init diff vs base", d0, "| cap", f["updates_per_epoch_cap"],
          "| n_train_participants", f.get("n_train_participants"), "| steps/epoch", f.get("steps_per_epoch"), flush=True)
    assert var == "concat_pretrained" or d0 < 1e-5
assert rec["fits"]["matched_exposure"]["updates_per_epoch_cap"] and rec["fits"]["full_available"]["updates_per_epoch_cap"] is None
print(f"unit {rec['total_seconds']} s, gpu peak {rec['gpu_peak_allocated_mb']} MB, code_hash {rec['code_hash']}")
print("D_COVERAGE POLICY PROBE PASSED")
