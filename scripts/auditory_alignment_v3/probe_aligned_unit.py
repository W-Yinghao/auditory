"""ADDENDUM_06 §4 engineering probe for B_ALIGNED (scratch dir probe_out_aligned, 2 epochs; no performance gate):
units complete with the B_DENSE record fields + readout aligned_patch_linear; training-path vs evaluation-path representations
agree; windows equal the EEG slice and are zero before the segment start; GPU memory / seconds recorded."""
import json, os, sys, time
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
import numpy as np, torch
from auditory_alignment_v3 import run as R3, core, fm_aligned, run_aligned

S = os.path.join(core.OUT, "probe_out_aligned"); os.makedirs(os.path.join(S, "units"), exist_ok=True); os.makedirs(os.path.join(S, "ckpt"), exist_ok=True)
rows = R3.all_rows(); core.load_rows = lambda: rows; dev = torch.device("cuda")
print("device", torch.cuda.get_device_name(0), flush=True)
res = {}
for ds, arch, ad in (("fau", "reve", "pretrained_frozen"), ("federici", "cbramod", "random_full")):
    r = next(x for x in rows if x["family_id"] == "B_ALIGNED" and x["dataset"] == ds and x["subject_fold"] == 0 and x["content_fold"] == 0
             and x["spec"]["architecture"] == arch and x["spec"]["adaptation"] == ad)
    for f in (os.path.join(S, "units", f"{r['experiment_id']}.json"),):
        if os.path.exists(f):
            os.remove(f)
    torch.cuda.reset_peak_memory_stats(); t0 = time.time()
    run_aligned.run(r, S, epochs=2)
    rec = json.load(open(os.path.join(S, "units", f"{r['experiment_id']}.json")))
    out = {"unit": r["experiment_id"], "status": rec["status"], "error": rec.get("error"), "seconds": round(time.time() - t0, 1),
           "eval_seconds": rec.get("eval_seconds"), "gpu_peak_allocated_mb": rec.get("gpu_peak_allocated_mb"), "code_group": rec.get("code_group"),
           "code_hash": rec.get("code_hash"), "readout": rec.get("readout"), "window_s": rec.get("window_s"), "epochs_completed": rec.get("epochs_completed"),
           "per_epoch_seconds": [c["seconds"] for c in rec.get("curve", [])], "n_participants_eval": len(rec.get("eval", {}).get("per_participant", {}))}
    if rec["status"] == "complete":
        from auditory_alignment_v2.run import load_cohort
        from auditory_alignment_v2.foundation_adapter import Backbone
        b = core.bind(r); coh = load_cohort(b); g = core.grid_samples(coh.fs)
        bt = fm_aligned.AlignedBatcher(coh, b["spec"], b, dev, g)
        model = fm_aligned.AlignedFM(Backbone(arch, ds, ad, coh.fs), 32).to(dev)
        model.load_state_dict(torch.load(os.path.join(S, "ckpt", f"{r['experiment_id']}_best.pt"), map_location=dev)["model"], strict=True); model.eval()
        batch = list(np.random.default_rng(20261014).choice(bt.es, size=16, replace=False))
        e0, t, s0, keys = bt.dense_rows(batch, np.random.default_rng(1), anchors=8)
        with torch.no_grad():
            u_tr = model(bt.windows(e0, t)).float().cpu().numpy().reshape(16, 8, -1)
        reps = fm_aligned.AlignedReps(model, None, bt, g); u_ev = reps.u(e0.cpu().numpy())
        tt = t.cpu().numpy(); u_at = u_ev[np.arange(16)[:, None], tt // g]
        W = bt.windows(e0, t).reshape(16, 8, bt.E.shape[0], -1)
        i, j = 3, 0; rel = int(tt[i, j]) - bt.pre + np.arange(bt.pre + bt.post)
        exp = bt.E[:, int(e0[i]) + np.clip(rel, 0, None)].float() * torch.tensor(rel >= 0, device=dev).float()
        out.update({"max_abs_u_train_vs_eval": float(np.abs(u_tr - u_at).max()), "queries_on_grid": bool((tt % g == 0).all()),
                    "window_equals_slice": bool(torch.equal(W[i, j], exp)), "zero_before_start_rows": int((tt - bt.pre < 0).sum()),
                    "window_native_samples": bt.pre + bt.post})
        bt = coh = model = None; torch.cuda.empty_cache()
    res[f"{ds}|{arch}|{ad}"] = out
    print(json.dumps(out), flush=True)
json.dump(res, open(os.path.join(S, "probe_aligned_unit.json"), "w"), indent=1)
print("done")
