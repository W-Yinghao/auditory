"""Engineering probe D_ATTENTION (+ learned_temporal twin) / E_COMPLEMENT / E_DISTILL (2 epochs, scratch dir; mechanics only).
E_COMPLEMENT base: a completed live E_LOCAL unit, copied (json + best ckpt) into the scratch dir; E_DISTILL teachers are read
from the live result dirs (read-only)."""
import json, os, shutil, sys
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
from auditory_alignment_v3 import run as R3, fm_dense, core
S = "/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v3/probe_out"
fm_dense.WARMUP = 1; fm_dense.UNFREEZE_EVERY = 1
rows = R3.load_rows()
pick = lambda fam, ds="fau", **m: next(r for r in rows if r["family_id"] == fam and r["dataset"] == ds and r["seed"] == 3401 and r["subject_fold"] == 0
                                       and r["content_fold"] in (0, None) and all(r["spec"].get(k) == v for k, v in m.items()))
ok = []
def check(r):
    rec = json.load(open(f"{S}/units/{r['experiment_id']}.json")); assert rec["status"] == "complete", rec.get("error")
    assert rec["code_hash"] == R3.code_hash(r["family_id"]); return rec
# D_ATTENTION: alignment_plus_selection (two selection-weight candidates) + its learned_temporal twin; selection_only
for spec in ({"training_task": "alignment_plus_selection", "objective": "NCE"}, {"training_task": "selection_only", "objective": "SELECTION_CE"}):
    r = pick("D_ATTENTION", architecture="lag_local_tokens", integrator="mean_score", **spec)
    R3.run_unit(r, S, epochs=2); rec = check(r)
    aw = rec["eval"]["attention_windows"]; assert aw["window_counts"]["5"]["train"] > 20 if "5" in aw["window_counts"] else aw["window_counts"][5]["train"] > 20, aw["window_counts"]
    pp = next(iter(aw["per_participant"].values())); assert "5s|native" in pp and pp["5s|native"]["mean_score_accuracy"] is not None, pp
    if spec["training_task"] == "alignment_plus_selection":
        assert rec["chosen_sel_weight"] in (0.1, 1.0) and len(rec["candidates"]) == 2
        tw = pick("D_ATTENTION", architecture="lag_local_tokens", integrator="learned_temporal", **spec)
        R3.run_unit(tw, S, epochs=2); trec = check(tw)
        assert trec["shared_model_with"] == r["experiment_id"] and trec["eval"] == rec["eval"] and trec["resolved_config"]["integrator_primary"] == "learned_temporal"
    ok.append(("D_ATTENTION", spec["training_task"])); print("OK", ok[-1], aw["window_counts"], flush=True)
# E_COMPLEMENT: CS_SINGLE, cbramod residual_pretrained_peft; base copied into the scratch dir
r = pick("E_COMPLEMENT", ds="private_bdf", architecture="cbramod", variant="residual_pretrained_peft", objective="CS_SINGLE")
from auditory_alignment_v3 import run_e_complement
b = run_e_complement.base_row(r, rows)
for src, dst in ((f"{core.OUT}/units/{b['experiment_id']}.json", f"{S}/units/{b['experiment_id']}.json"), (f"{core.OUT}/ckpt/{b['experiment_id']}_best.pt", f"{S}/ckpt/{b['experiment_id']}_best.pt")):
    os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(src, dst)
R3.run_unit(r, S, epochs=2); rec = check(r)
assert rec["init_max_abs_logit_diff_vs_base"] < 1e-4, rec["init_max_abs_logit_diff_vs_base"]
pp = next(iter(rec["eval"]["per_participant"].values())); assert "combined" in pp and "local_only" in pp
assert len(rec["curve"]) == 2 and rec["curve"][-1]["open_groups"] > 0
ok.append(("E_COMPLEMENT", rec["init_max_abs_logit_diff_vs_base"])); print("OK", ok[-1], rec["curve"], flush=True)
# E_DISTILL: auditory_adapted_teacher (ALN2 D_FM_PUBLIC peft teachers), NCE, window early
r = pick("E_DISTILL", ds="private_bdf", teacher_policy="auditory_adapted_teacher", objective="NCE", window="early")
R3.run_unit(r, S, epochs=2); rec = check(r)
assert rec["teacher"]["chosen"] in rec["teacher"]["candidates_best_selection_score"] and len(rec["teacher"]["candidates_best_selection_score"]) == 2
assert 0 < rec["teacher"]["p_teacher_train_mean"] < 1 and [c["distill_weight"] for c in rec["candidates"]] == [0.0, 0.1, 1.0]
assert rec["chosen_candidate"]["distill_weight"] in (0.1, 1.0) and "per_participant" in rec["eval"] and "per_participant" in rec["baseline_lambda0_eval"]
ok.append(("E_DISTILL", rec["teacher"]["chosen"], rec["teacher"]["p_teacher_train_mean"])); print("OK", ok[-1], flush=True)
print("ALL BATCH-3 PROBES PASSED")
