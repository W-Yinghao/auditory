"""BC_PROBE_PLAN_20261014 P1-P4 (one GPU): C evaluation-path equivalence at zero residual; train / evaluation query
consistency of the B dense models; training-side lag scan; query sensitivity. Cell: FAU NCE, subject fold 0, content fold 0,
seed 3401. Writes private/auditory_alignment_v3/probe_bc/probe_gpu.json."""
import json, os, sys, time
sys.path.insert(0, "/home/infres/yinwang/EEG_auditory")
import numpy as np, torch
from auditory_alignment import evaluate as ev1
from auditory_alignment_v3 import run as R3, core, fm_dense, fm_complement, policy_models
from auditory_alignment_v3.run_complement import base_row

OUTD = os.path.join(core.OUT, "probe_bc"); os.makedirs(OUTD, exist_ok=True)
rows = R3.all_rows(); core.load_rows = lambda: rows; dev = torch.device("cuda")
CELL = dict(dataset="fau", subject_fold=0, content_fold=0, seed=3401)
RNG = 20261014
res = {"cell": CELL, "started": time.strftime("%F %T")}


def pick(fam, **spec):
    c = [r for r in rows if r["family_id"] == fam and all(r[k] == v for k, v in CELL.items()) and all(r["spec"].get(k) == v for k, v in spec.items())]
    assert len(c) == 1, (fam, spec, len(c))
    return c[0]


def pol(r):
    return {"chosen_row": r, "chosen_checkpoint": os.path.relpath(os.path.join(core.OUT, "ckpt", r["experiment_id"] + "_best.pt"), core.REPO), "candidate_family": r["family_id"]}


def rec(r):
    return json.load(open(os.path.join(core.OUT, "units", f"{r['experiment_id']}.json")))


def save():
    json.dump(res, open(os.path.join(OUTD, "probe_gpu.json"), "w"), indent=1)


def free():
    import gc
    gc.collect(); torch.cuda.empty_cache()


# ------------------------------------------------------------------ P1: C evaluation path at zero residual vs the A_LOCAL record
c_row = pick("C_COMPLEMENT", objective="NCE", architecture="reve", variant="residual_pretrained_frozen")
l_row = base_row(c_row, rows)
m = policy_models.build_chosen(pol(c_row), dev)
model = m["base"].model
with torch.no_grad():
    model.res.residual[-1].weight.zero_(); model.res.residual[-1].bias.zero_()
ev = fm_complement.evaluate_complement(m["bound"], model, m["head"], m["bt"], m["coh"], m["record"]["objective_calibration"], m["grid"])
L = rec(l_row)["eval"]["per_participant"]
d1 = {}
for pid, lv in L.items():
    cv = ev["per_participant"].get(pid)
    if cv is None:
        d1.setdefault("missing_participants", []).append("<id>"); continue
    for k in ("unified/regular", "unified/mismatched_eeg", "unified/hard", "native/regular", "native/mismatched_eeg", "native/hard"):
        for mt in ("top1", "top5", "mrr", "rank_pct", "logloss_bits"):
            d1[f"{k}/{mt}"] = max(d1.get(f"{k}/{mt}", 0.0), abs(cv[k][mt] - lv[k][mt]))
res["P1"] = {"c_unit": c_row["experiment_id"], "local_unit": l_row["experiment_id"], "n_participants": len(L), "max_abs_diff": d1,
             "max_abs_diff_all": max(v for k, v in d1.items() if k != "missing_participants"),
             "n_candidates_equal": all(ev["per_participant"][p]["unified/regular"]["n_candidates"] == L[p]["unified/regular"]["n_candidates"] for p in L if p in ev["per_participant"])}
print("P1", json.dumps({k: v for k, v in res["P1"].items() if k != "max_abs_diff"}), flush=True); save()
m = model = ev = None; free()

# ------------------------------------------------------------------ models for P2-P4
specs = {"B_reve_frozen_dense_query": ("B_DENSE", dict(objective="NCE", architecture="reve", adaptation="pretrained_frozen", readout="dense_query")),
         "B_reve_frozen_phase_linear": ("B_DENSE", dict(objective="NCE", architecture="reve", adaptation="pretrained_frozen", readout="channel_phase_linear")),
         "B_reve_random_phase_linear": ("B_DENSE", dict(objective="NCE", architecture="reve", adaptation="random_full", readout="channel_phase_linear")),
         "B_cbramod_frozen_phase_linear": ("B_DENSE", dict(objective="NCE", architecture="cbramod", adaptation="pretrained_frozen", readout="channel_phase_linear"))}


def ridge_r(Xf, Yf, Xa, Ya, Xb, Yb, alphas=np.logspace(-3, 3, 7)):
    mx, my, sy = Xf.mean(0), Yf.mean(0), Yf.std(0) + 1e-8
    Xf, Xa, Xb = Xf - mx, Xa - mx, Xb - mx
    Yf, Ya, Yb = (Yf - my) / sy, (Ya - my) / sy, (Yb - my) / sy
    G, H = Xf.T @ Xf, Xf.T @ Yf
    def corr(P, Y):
        P = P - P.mean(0); Y = Y - Y.mean(0)
        return float(np.mean((P * Y).sum(0) / (np.sqrt((P ** 2).sum(0) * (Y ** 2).sum(0)) + 1e-12)))
    best = None
    for a in alphas:
        B = np.linalg.solve(G + a * len(Xf) * np.eye(G.shape[0]), H)
        ra = corr(Xa @ B, Ya)
        if best is None or ra > best[0]:
            best = (ra, a, B)
    return corr(Xb @ best[2], Yb), float(best[1])


def reps_of(get_u, get_va, bt):
    rng = np.random.default_rng(RNG)
    fit = rng.choice(bt.fit, size=min(300, len(bt.fit)), replace=False); es = rng.choice(bt.es, size=min(160, len(bt.es)), replace=False)
    out = {}
    for name, idx in (("fit", fit), ("es", es)):
        e0 = np.array([bt.coh_segments[i]["e0"] for i in idx]); s0 = bt.s0_true[idx]
        U = get_u(e0); _, A = get_va(s0)
        out[name] = (np.asarray(U, np.float64), np.asarray(A, np.float64))
    return out


def lag_scan(R, max_lag=43):
    (Uf, Af), (Ue, Ae) = R["fit"], R["es"]
    h = len(Ue) // 2; T = Uf.shape[1]
    curve = {}
    for D in range(-max_lag, max_lag + 1):
        k = np.arange(max(0, -D), T - max(0, D))
        f = lambda U, A: (U[:, k].reshape(-1, U.shape[-1]), A[:, k + D].reshape(-1, A.shape[-1]))
        Xf, Yf = f(Uf, Af); Xa, Ya = f(Ue[:h], Ae[:h]); Xb, Yb = f(Ue[h:], Ae[h:])
        curve[D] = ridge_r(Xf, Yf, Xa, Ya, Xb, Yb)[0]
    k = np.arange(T)
    Xf, Yf = Uf.reshape(-1, Uf.shape[-1]), Af.reshape(-1, Af.shape[-1])
    nulls = []
    for s in range(1, 6):
        Ar = np.roll(Ae, s, axis=0)
        nulls.append(ridge_r(Xf, Yf, Ue[:h].reshape(-1, Ue.shape[-1]), Ar[:h].reshape(-1, Ar.shape[-1]), Ue[h:].reshape(-1, Ue.shape[-1]), Ar[h:].reshape(-1, Ar.shape[-1]))[0])
    peak = max(curve, key=curve.get)
    return {"curve": curve, "peak_lag_steps": int(peak), "peak_r": curve[peak], "r_lag0": curve[0], "null_mean": float(np.mean(nulls)), "null_max": float(np.max(nulls))}


def sensitivity(U, fs, grid):
    Ue = U
    tot = Ue.reshape(-1, Ue.shape[-1]).var(0).sum()
    within = Ue.var(1).sum(-1).mean()
    a, b = Ue[:, :-1], Ue[:, 1:]
    cos = (a * b).sum(-1) / (np.linalg.norm(a, axis=-1) * np.linalg.norm(b, axis=-1) + 1e-12)
    t_sec = np.arange(Ue.shape[1]) * grid / fs; patch = np.floor(t_sec).astype(int)
    wp = np.mean([Ue[:, patch == p].var(1).sum(-1).mean() for p in np.unique(patch) if (patch == p).sum() > 1])
    return {"within_segment_fraction": float(within / tot), "adjacent_cosine_mean": float(cos.mean()), "within_patch_fraction": float(wp / tot)}


res["P2"], res["P3"], res["P4"] = {}, {}, {}
# local control
lrec = rec(l_row)
from auditory_alignment_v2.run import load_cohort
from auditory_alignment_v2.audio_targets import build_head, target_stats
from auditory_alignment_v2.temporal import build_encoder
b = core.bind(l_row); coh = load_cohort(b); g = core.grid_samples(coh.fs)
bt = fm_dense.DenseBatcher(coh, b["spec"], b, dev, g)
enc = build_encoder("lag_local_tokens", coh.n_ch, 32, bt.W, coh.fs).to(dev)
head = build_head("fixed_features", bt.audio_dim, 32, coh.meta["dataset"], target_stats(bt, np.random.default_rng(b["seed"] + 5))).to(dev)
sd = torch.load(os.path.join(core.OUT, "ckpt", l_row["experiment_id"] + "_best.pt"), map_location=dev); enc.load_state_dict(sd["enc"], strict=True); head.load_state_dict(sd["head"], strict=True)
enc.eval(); head.eval()
reps = ev1.Reps(enc, head, bt, stride=g)
R = reps_of(reps.u, reps.va, bt)
res["P3"]["local"] = lag_scan(R); res["P4"]["local"] = sensitivity(R["es"][0], coh.fs, g)
res["grid_samples"], res["fs"] = int(g), float(coh.fs)
print("P3 local", {k: v for k, v in res["P3"]["local"].items() if k != "curve"}, "P4", res["P4"]["local"], flush=True); save()
enc = head = reps = R = bt = coh = None; free()

for name, (fam, spec) in specs.items():
    r = pick(fam, **spec)
    m = policy_models.build_chosen(pol(r), dev)
    model, bt, g = m["base"].model, m["bt"], m["grid"]
    reps = fm_dense.DenseReps(model, m["head"], bt, g)
    # P2: training path vs evaluation path
    batch = list(np.random.default_rng(RNG).choice(bt.es, size=32, replace=False))
    e0_seg, t, s0, keys = bt.dense_rows(batch, np.random.default_rng(1), anchors=8)
    with torch.no_grad():
        u_tr = model(bt.context(e0_seg), t.float() / bt.fs).float().cpu().numpy()
    u_ev = reps.u(e0_seg.cpu().numpy())
    tt = t.cpu().numpy(); on_grid = bool((tt % g == 0).all())
    u_ev_at = u_ev[np.arange(len(batch))[:, None], tt // g]
    s0_rows = s0.cpu().numpy().reshape(len(batch), 8) - tt
    res["P2"][name] = {"unit": r["experiment_id"], "queries_on_grid": on_grid, "max_abs_u_diff": float(np.abs(u_tr - u_ev_at).max()),
                       "audio_start_equal_segment_s0": bool((s0_rows == bt.s0_true[batch][:, None]).all()),
                       "s0_train_equals_s0_true": bool((bt.s0_train == bt.s0_true).all())}
    R = reps_of(reps.u, reps.va, bt)
    res["P3"][name] = lag_scan(R); res["P4"][name] = sensitivity(R["es"][0], bt.fs, g)
    print(name, "P2", res["P2"][name], "P3", {k: v for k, v in res["P3"][name].items() if k != "curve"}, "P4", res["P4"][name], flush=True); save()
    m = model = reps = R = bt = u_tr = u_ev = None; free()

res["finished"] = time.strftime("%F %T"); save(); print("done")
