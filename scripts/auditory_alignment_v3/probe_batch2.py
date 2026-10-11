"""Engineering probe D_ADAPT / D_COVERAGE / B_CTRL_ONESTEP / B_LR_PANEL (2 epochs, scratch dir; mechanics only)."""
import json, sys
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
from auditory_alignment_v3 import run as R3, fm_dense
S = "/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v3/probe_out"
rows = R3.load_rows(); ext = [json.loads(l) for l in open("/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v3/plan_ext.jsonl")]
pick = lambda src, fam, **m: next(r for r in src if r["family_id"] == fam and r["dataset"] == m.pop("ds", "fau") and r["seed"] == 3401 and r["subject_fold"] == 0
                                    and r["content_fold"] == 0 and all(r["spec"].get(k) == v for k, v in m.items()))
ok = []
for r in (pick(rows, "D_ADAPT", architecture="lag_local_tokens", adapter="input_spatial", objective="NCE"),
          pick(rows, "D_ADAPT", architecture="lag_local_tokens", adapter="output_low_rank", objective="NCE"),
          pick(rows, "D_COVERAGE", architecture="lag_local_tokens", population="TH_HA", objective="NCE"),
          pick(ext, "B_CTRL_ONESTEP", architecture="cbramod", adaptation="pretrained_peft"),
          pick(ext, "B_LR_PANEL", architecture="reve", adaptation="pretrained_full", lr_multiplier=3.0)):
    R3.run_unit(r, S, epochs=2)
    rec = json.load(open(f"{S}/units/{r['experiment_id']}.json")); assert rec["status"] == "complete", rec.get("error")
    assert rec["code_hash"] == R3.code_hash(r["family_id"])
    f = r["family_id"]
    if f == "D_ADAPT":
        pp = next(iter(rec["eval"]["per_participant"].values())); assert "support_0.1" in pp and "support_0.3" in pp and rec["eval"]["steps"]["chosen"] in (20, 50, 100)
    if f == "D_COVERAGE":
        fa, me = rec["fits"]["full_available"], rec["fits"]["matched_exposure"]
        assert me["steps_per_epoch"] == me["updates_per_epoch_cap"] and fa["steps_per_epoch"] >= me["steps_per_epoch"], (fa["steps_per_epoch"], me["steps_per_epoch"])
    if f == "B_CTRL_ONESTEP":
        assert rec["recipe"] == "aln2_onestep" and rec["warmup_epochs"] == 0 and rec["llrd"] is None
    if f == "B_LR_PANEL":
        assert abs(rec["lr_backbone"] - 3 * fm_dense.LR["pretrained_full"][0]) < 1e-12
    ok.append((f, r["spec"].get("adapter") or r["spec"].get("population") or r["spec"].get("recipe"))); print("OK", ok[-1], flush=True)
print("ALL BATCH-2 PROBES PASSED")
