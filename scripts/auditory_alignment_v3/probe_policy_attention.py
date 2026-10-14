"""Engineering probe for the D_ATTENTION policy arms (ADDENDUM_04; 2 epochs, scratch dir probe_out): dense_fm_policy x
alignment_plus_selection (two selection-weight candidates, choice by es 2AFC accuracy), complement_policy x selection_only
(SELECTION_CE -> NCE policy cell, selection-only checkpoint rule, residual starts at the lag base), and a learned_temporal
derived record; code_group attention_policy; attention windows evaluated."""
import json, sys
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
from auditory_alignment_v3 import run as R3, core, registry, fm_dense, run_attention_policy as RAP
fm_dense.WARMUP, fm_dense.UNFREEZE_EVERY = 1, 1
registry.POLICY_GROUP["D_ATTENTION"] = "attention_policy"  # probe process only
S = "/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v3/probe_out"
rows = R3.all_rows(); core.load_rows = lambda: rows
pick = lambda arm, task, integ: next(r for r in rows if r["family_id"] == "D_ATTENTION" and r["spec"].get("architecture") == arm and r["dataset"] == "dtu"
                                     and r["seed"] == 3401 and r["subject_fold"] == 0 and r["content_fold"] == 0 and r["spec"]["training_task"] == task
                                     and r["spec"]["integrator"] == integ and r["spec"]["objective"] in ("NCE", "SELECTION_CE"))
for arm, task in (("dense_fm_policy", "alignment_plus_selection"), ("complement_policy", "selection_only")):
    r = pick(arm, task, "mean_score")
    R3.run_unit(r, S, epochs=2)
    rec = json.load(open(f"{S}/units/{r['experiment_id']}.json"))
    assert rec["status"] == "complete" and rec["code_group"] == "attention_policy", rec.get("error")
    aw = rec["eval"]["attention_windows"]
    print(arm, task, "chosen", rec["policy"]["chosen"], rec["policy"]["chosen_spec"], "| sel weight", rec.get("chosen_sel_weight"),
          "| init diff", rec.get("init_max_abs_diff_vs_base"), "| windows", aw["window_counts"], "| rule", rec["selection_rule"],
          f"| {rec['total_seconds']} s, gpu {rec['gpu_peak_allocated_mb']} MB", flush=True)
    if arm == "complement_policy" and rec["policy"]["chosen_spec"]["variant"] != "concat_pretrained":
        assert rec["init_max_abs_diff_vs_base"] < 1e-5
    if task == "alignment_plus_selection":
        assert len(rec["candidates"]) == 2 and rec["chosen_sel_weight"] in (0.1, 1.0)
    lt = pick(arm, task, "learned_temporal")
    R3.run_unit(lt, S)
    rl = json.load(open(f"{S}/units/{lt['experiment_id']}.json"))
    assert rl["status"] == "complete" and rl["shared_model_with"] == r["experiment_id"] and rl["code_group"] == "attention_policy"
print("D_ATTENTION POLICY PROBES PASSED")
