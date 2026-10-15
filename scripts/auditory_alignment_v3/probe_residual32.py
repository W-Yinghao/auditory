"""ADDENDUM_10 §4 engineering probe (scratch probe_out_r32; no performance gate): FAU subject fold 0 / content fold 0, NCE,
residual_aligned_pretrained reve, 3 epochs. Checks: epoch-0 u = base u; dev group disjoint (asserted in the trainer); dev risk for
epochs 0-3; training-path vs evaluation-path u; completion; GPU memory / time."""
import json, os, sys, time
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
import numpy as np, torch
from auditory_alignment_v3 import run as R3, core, residual32 as R32

S = os.path.join(core.OUT, "probe_out_r32"); os.makedirs(os.path.join(S, "units"), exist_ok=True); os.makedirs(os.path.join(S, "ckpt"), exist_ok=True)
rows = R3.all_rows(); core.load_rows = lambda: rows; dev = torch.device("cuda")
r = next(x for x in rows if x["family_id"] == "ALN32_RESIDUAL" and x["dataset"] == "fau" and x["subject_fold"] == 0 and x["content_fold"] == 0
         and x["spec"]["objective"] == "NCE" and x["spec"]["variant"] == "residual_aligned_pretrained" and x["spec"]["architecture"] == "reve")
p = os.path.join(S, "units", f"{r['experiment_id']}.json")
for f in (p, os.path.join(S, "ckpt", r["experiment_id"] + "_resume.pt")):
    if os.path.exists(f):
        os.remove(f)
cap = {}
orig_fit = R32.fit_residual


def fit_capture(*a, **k):
    out = orig_fit(*a, **k); cap["m"] = out; return out


R32.fit_residual = fit_capture
t0 = time.time(); R32.run(r, S, 3)
rec = json.load(open(p))
out = {"unit": r["experiment_id"], "status": rec["status"], "error": rec.get("error"), "seconds": round(time.time() - t0, 1), "gpu_peak_allocated_mb": rec.get("gpu_peak_allocated_mb"),
       "code_group": rec.get("code_group"), "epoch0_max_abs_diff_vs_base": rec.get("epoch0_max_abs_diff_vs_base"),
       "curve": [(c["epoch"], round(c["dev_risk_bits"], 4), round(c["dev_rank"], 4)) for c in rec.get("curve", [])], "selected_epoch": rec.get("selected_epoch"),
       "n_dev_segments": rec.get("n_dev_segments"), "n_train_segments": rec.get("n_train_segments"), "trainable_params": rec.get("trainable_params"),
       "eval_seconds": rec.get("eval_seconds"), "n_participants_eval": len(rec.get("eval", {}).get("per_participant", {})), "traceback": rec.get("traceback", "")[-600:]}
if rec["status"] == "complete":
    from auditory_alignment import evaluate as ev1
    model, head, bt, rw = cap["m"]
    i = bt.es[2]; e0 = bt.coh_segments[i]["e0"]; g = core.grid_samples(bt.fs)
    reps = R32.ResReps(model, rw, head, bt, g, ev1.Reps); u_ev = reps.u([e0])[0]
    offs = torch.tensor([0, 30, 300], device=dev); e = e0 + offs
    with torch.no_grad():
        u_tr = model(bt.patches(e), rw.windows(e)).float().cpu().numpy()
    out["max_abs_u_train_vs_eval"] = float(np.abs(u_tr - u_ev[(offs // g).cpu().numpy()]).max())
json.dump(out, open(os.path.join(S, "probe_residual32.json"), "w"), indent=1); print(json.dumps(out)); print("done")
