"""ADDENDUM_07 §4 engineering probe (scratch dir probe_out_aln32; no performance gate). FAU subject fold 0 / content fold 0:
L1 local_aligned1000 (2 epochs), R1 raw_aligned1000_ridge, F2 reve pretrained_frozen post-only (2 epochs), TRUE_FULL reve
pretrained_full warmup_then_all_v1 lr 3e-4 (7 epochs). Checks: completion, windows / masks / token count, out-of-window perturbation,
post-only zeros, ledger (all groups open from epoch 6 with grad steps and non-zero change), theta_0 rebuild == start snapshot."""
import json, os, sys, time
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
import numpy as np, torch
from auditory_alignment_v3 import run as R3, core, fm_aligned, fm_aligned32, local_support, run_aligned32

S = os.path.join(core.OUT, "probe_out_aln32"); os.makedirs(os.path.join(S, "units"), exist_ok=True); os.makedirs(os.path.join(S, "ckpt"), exist_ok=True)
rows = R3.all_rows(); core.load_rows = lambda: rows; dev = torch.device("cuda")
print("device", torch.cuda.get_device_name(0), flush=True)
res = {}
cell = lambda r: r["dataset"] == "fau" and r["subject_fold"] == 0 and r["content_fold"] == 0


def pick(fam, **kw):
    c = [r for r in rows if r["family_id"] == fam and cell(r) and all(r["spec"].get(k) == v for k, v in kw.items())]
    assert len(c) == 1, (fam, kw, len(c)); return c[0]


REUSE = '--reuse' in sys.argv  # keep units already completed by an earlier probe run (only the checks are repeated)


def go(r, fn, epochs):
    p = os.path.join(S, "units", f"{r['experiment_id']}.json")
    if os.path.exists(p) and not (REUSE and json.load(open(p)).get('status') == 'complete'):
        os.remove(p)
    torch.cuda.reset_peak_memory_stats(); t0 = time.time()
    if not os.path.exists(p):
        fn(r, S, epochs)
    rec = json.load(open(p))
    return rec, {"unit": r["experiment_id"], "status": rec["status"], "error": rec.get("error"), "seconds": round(time.time() - t0, 1),
                 "gpu_peak_allocated_mb": rec.get("gpu_peak_allocated_mb"), "code_group": rec.get("code_group"), "code_hash": rec.get("code_hash"),
                 "n_participants_eval": len(rec.get("eval", {}).get("per_participant", {}))}


# L1 / R1
from auditory_alignment_v2.run import load_cohort
for v, ep in (("local_aligned1000", 2), ("raw_aligned1000_ridge", None)):
    r = pick("ALN32_LOCAL_SUPPORT", variant=v)
    rec, out = go(r, local_support.run, ep)
    out["resolved_config"] = rec.get("resolved_config"); out["ridge_alpha_rel"] = rec.get("ridge_alpha_rel")
    if v == "local_aligned1000" and rec["status"] == "complete":
        b = core.bind(r); coh = load_cohort(b); g = core.grid_samples(coh.fs)
        bt = local_support.batcher_for("aligned1000")(coh, b["spec"], b, dev, g)
        from auditory_alignment_v2.temporal import build_encoder
        enc = build_encoder("lag_local_tokens", coh.n_ch, 32, bt.W, coh.fs).to(dev)
        enc.load_state_dict(torch.load(os.path.join(S, "ckpt", r["experiment_id"] + "_best.pt"), map_location=dev)["enc"]); enc.eval()
        i = bt.es[5]; e0 = bt.coh_segments[i]["e0"]
        e = torch.tensor([e0 + 3, e0 + 300], device=dev)  # one anchor near the segment start, one inside
        x = bt.patches(e)[0]
        out.update({"window_samples": bt.W[0], "n_tokens": int(enc.n_tokens), "zero_before_start": bool((x[0, :, :bt.pre - 3] == 0).all()),
                    "inside_nonzero": bool((x[1] != 0).any(1).all())})
        with torch.no_grad():
            u0 = enc(bt.patches(e)); Eo = bt.E.clone()
            k = int(e[1]) + bt.W[0][1]; bt.E[:, k] += 50; bt.E[:, int(e[1]) + bt.W[0][0] - 1] += 50  # just outside both ends
            u_out = enc(bt.patches(e)); bt.E.copy_(Eo); bt.E[:, int(e[1]) + 10] += 50; u_in = enc(bt.patches(e)); bt.E.copy_(Eo)
        out.update({"outside_perturbation_max_du": float((u_out - u0).abs().max()), "inside_perturbation_max_du": float((u_in - u0).abs().max())})
        bt = coh = enc = None; torch.cuda.empty_cache()
    res[v] = out; print(v, json.dumps(out), flush=True)

# F2 post-only
r = pick("ALN32_POSTONLY_FM", architecture="reve", adaptation="pretrained_frozen")
rec, out = go(r, run_aligned32.run, 2)
if rec["status"] == "complete":
    b = core.bind(r); coh = load_cohort(b); g = core.grid_samples(coh.fs)
    bt = fm_aligned32.PostOnlyAlignedBatcher(coh, b["spec"], b, dev, g)  # the batcher moves the cohort EEG to the GPU (coh.eeg released)
    e0 = torch.tensor([bt.coh_segments[bt.es[0]]["e0"]], device=dev); t = torch.tensor([[0, 300]], device=dev)
    W, Wa = bt.windows(e0, t), fm_aligned.aligned_windows(bt.E, e0, t, bt.pre, bt.post)
    out.update({"post_only_zero_left": bool((W[..., :bt.pre] == 0).all()), "post_equals_aligned": bool(torch.equal(W[..., bt.pre:], Wa[..., bt.pre:])),
                "ledger_groups_open": sum(1 for L in rec["update_ledger"]["groups"] if L["epochs_open"] > 0), "ledger_n_groups": len(rec["update_ledger"]["groups"])})
    bt = coh = None; torch.cuda.empty_cache()
res["post600_zero_left"] = out; print("F2", json.dumps(out), flush=True)

# TRUE_FULL with theta_0 capture
cap = []
Orig = fm_aligned32.AlignedFM


class CaptureFM(Orig):
    def __init__(self, *a, **k):
        super().__init__(*a, **k); cap.append({n: p.detach().cpu().clone() for n, p in self.named_parameters()})


fm_aligned32.AlignedFM = CaptureFM
try:
    r = pick("ALN32_TRUE_FULL", architecture="reve", adaptation="pretrained_full", recipe="warmup_then_all_v1", lr_backbone=3e-4)
    rec, out = go(r, run_aligned32.run, 7)
finally:
    fm_aligned32.AlignedFM = Orig
if rec["status"] == "complete":
    L = rec["update_ledger"]["groups"]
    out.update({"n_groups": len(L), "first_open_epochs": sorted({x["first_open_epoch"] for x in L if x["name"] != "readout"}),
                "readout_first_open": next(x["first_open_epoch"] for x in L if x["name"] == "readout"),
                "all_groups_grad_steps": all(x["grad_steps"] > 0 for x in L), "min_rel_weight_change": min(x["rel_weight_change"] for x in L),
                "max_rel_weight_change": max(x["rel_weight_change"] for x in L),
                "theta0_rebuild_max_abs_diff": max(float((cap[0][n] - cap[1][n]).abs().max()) for n in cap[0]) if len(cap) >= 2 else None,
                "best_epoch": rec.get("best_epoch"), "curve_open_groups": [c["open_groups"] for c in rec["curve"]]})
res["true_full"] = out; print("TRUE_FULL", json.dumps(out), flush=True)
json.dump(res, open(os.path.join(S, "probe_aln32_units.json"), "w"), indent=1)
print("done")
