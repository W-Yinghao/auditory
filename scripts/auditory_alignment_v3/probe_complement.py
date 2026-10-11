"""Engineering probe C (3 epochs, scratch dir; base = the probe's 2-epoch A_LOCAL unit): zero-init identity, completion, dependency."""
import json, sys
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
from auditory_alignment_v3 import run as R3, fm_dense, run_complement
fm_dense.WARMUP, fm_dense.UNFREEZE_EVERY = 1, 1
S = "/home/infres/yinwang/EEG_auditory/private/auditory_alignment_v3/probe_out"
rows = R3.load_rows(); ok = []
want = [("C_COMPLEMENT", "cbramod", "residual_pretrained_peft"), ("C_COMPLEMENT", "reve", "concat_pretrained"),
        ("C_COMPLEMENT", "cbramod", "residual_random_frozen"), ("C_CAPACITY_CONTROL", "small_capacity_branch", "residual_small_capacity")]
for fam, arch, var in want:
    r = next(r for r in rows if r["family_id"] == fam and r["dataset"] == "fau" and r["seed"] == 3401 and r["subject_fold"] == 0 and r["content_fold"] == 0
             and r["spec"]["architecture"] == arch and r["spec"]["variant"] == var and r["spec"]["objective"] == "NCE")
    assert run_complement.base_ready(r, rows, S) is not None, "probe base missing"
    R3.run_unit(r, S, epochs=3)
    rec = json.load(open(f"{S}/units/{r['experiment_id']}.json")); assert rec["status"] == "complete", rec.get("error")
    assert rec["code_hash"] == R3.code_hash(fam) and rec["dependency"]["local_base_same_fold"]
    if var != "concat_pretrained":
        assert rec["init_max_abs_diff_vs_base"] < 1e-5, rec["init_max_abs_diff_vs_base"]
    ok.append((fam, arch, var, rec.get("init_max_abs_diff_vs_base"), rec["trainable_params"])); print("OK", ok[-1], flush=True)
print("ALL C PROBES PASSED")
