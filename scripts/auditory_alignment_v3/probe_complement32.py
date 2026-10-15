"""ADDENDUM_09 §4 engineering probe (scratch probe_out_c32; no performance gate): one FAU cell (subject fold 0, content fold 0),
base L0, backbone reve. Checks: the unit completes with all six variant evaluations; fit-row participants are training
participants only and split into 5 disjoint groups; the raw aligned window equals the B_ALIGNED window; cached and direct
representations agree; GPU memory / time."""
import json, os, sys, time
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
import numpy as np, torch
from auditory_alignment_v3 import run as R3, core, complement32 as C32, fm_aligned, local_train

S = os.path.join(core.OUT, "probe_out_c32"); os.makedirs(os.path.join(S, "units"), exist_ok=True); os.makedirs(os.path.join(S, "ckpt"), exist_ok=True)
rows = R3.all_rows(); core.load_rows = lambda: rows; dev = torch.device("cuda")
DS = sys.argv[1] if len(sys.argv) > 1 else "fau"
r = next(x for x in rows if x["family_id"] == "ALN32_SIMPLE_COMPLEMENT" and x["dataset"] == DS and x["subject_fold"] == 0 and x["content_fold"] == 0
         and x["spec"]["base"] == "L0" and x["spec"]["architecture"] == "reve")
p = os.path.join(S, "units", f"{r['experiment_id']}.json")
if os.path.exists(p):
    os.remove(p)
torch.cuda.reset_peak_memory_stats(); t0 = time.time()
# the runner reads the base from the fleet directory (core.OUT); write the probe record into the scratch dir
orig_ready = C32.base_ready
C32.base_ready = lambda row, rows_, out=None: orig_ready(row, rows_, core.OUT)
C32.run(r, S, None)
rec = json.load(open(p))
out = {"unit": r["experiment_id"], "status": rec["status"], "error": rec.get("error"), "seconds": round(time.time() - t0, 1), "gpu_peak_allocated_mb": rec.get("gpu_peak_allocated_mb"),
       "code_group": rec.get("code_group"), "variants": sorted(rec.get("eval_variants", {})), "n_fit_rows": rec.get("n_fit_rows"),
       "n_train_participants": rec.get("n_train_participants"), "window_samples": rec.get("window_samples"),
       "alphas": {v: rec.get("fit", {}).get(v, {}).get("alpha_rel") for v in C32.VARIANTS}, "traceback": rec.get("traceback", "")[-800:]}
if rec["status"] == "complete":
    from auditory_alignment_v2.run import load_cohort
    b = core.bind(r); coh = load_cohort(b); g = core.grid_samples(coh.fs)
    bt = local_train.GridBatcher(coh, {**b["spec"], "architecture": "lag_local_tokens", "window": "full"}, b, dev, g)
    pre, post = int(round(0.4 * coh.fs)), int(bt.W[0][1])
    fz = C32.Featurizer(None, bt, {}, pre, post)
    i = bt.es[3]; e0 = bt.coh_segments[i]["e0"]; t = torch.tensor([[0, 9, 300]], device=dev)
    W1 = fz.raw((torch.tensor([e0], device=dev)[:, None] + t).reshape(-1))
    W2 = fm_aligned.aligned_windows(bt.E, torch.tensor([e0], device=dev), t, pre, post)
    out["raw_window_equals_B_ALIGNED"] = bool(torch.equal(W1, W2))
    out["participants_in_eval"] = {v: len(e["per_participant"]) for v, e in rec["eval_variants"].items()}
res = {"probe": out}
json.dump(res, open(os.path.join(S, "probe_complement32.json"), "w"), indent=1); print(json.dumps(out)); print("done")
