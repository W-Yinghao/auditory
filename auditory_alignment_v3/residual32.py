"""ALN3 ADDENDUM_10 ALN32_RESIDUAL: trained residual on a frozen local base with an epoch-0 candidate and cross-person selection.
u = normalise(u_base + r([base tokens, c])), r = ZeroResidualPrediction (package reference; zero last layer), c = context branch
over the B_ALIGNED window: frozen aligned backbone tokens -> LN -> Linear(C*E -> 64), or a small conv over the raw window.
Training groups 1-4 / inner development group 0 of the ADDENDUM_09 grouping (seed 20261014); selection = lowest development
risk over epochs 0..E (epoch 0 = the base, legal). Evaluation: the unchanged ev2.evaluate_continuous."""
from __future__ import annotations

import json
import math
import os
import time
import traceback

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from . import core
from .aln3_reference.readouts import ZeroResidualPrediction

CTX, EPOCHS, LR_, WD, N_SEG, Q = 64, 30, 1e-3, 1e-4, 32, 8
N_GROUPS, GROUP_SEED, DEV_GROUP, PRE_S = 5, 20261014, 0, 0.4
VARIANTS = ("residual_aligned_pretrained", "residual_aligned_random", "residual_small_capacity")


def base_row(row, rows):
    for r in rows:
        s = r["spec"]
        if r["family_id"] == "A_LOCAL" and all(r[k] == row[k] for k in ("dataset", "subject_fold", "content_fold", "seed")) and s.get("architecture") == "lag_local_tokens" \
                and s.get("window") == "full" and s.get("projection_dim", 32) == 32 and s["objective"] == row["spec"]["objective"]:
            return r
    return None


def base_ready(row, rows, out=core.OUT):
    b = base_row(row, rows)
    if b is None:
        return None
    p = os.path.join(out, "units", f"{b['experiment_id']}.json"); ck = os.path.join(out, "ckpt", f"{b['experiment_id']}_best.pt")
    return (b, p, ck) if os.path.exists(p) and os.path.exists(ck) and json.load(open(p)).get("status") == "complete" else None


class FMContext(nn.Module):
    def __init__(self, bb):
        super().__init__()
        self.bb = bb; self.norm = nn.LayerNorm(bb.E); self.lin = nn.Linear(len(bb.channel_names) * bb.E, CTX)
        for p in self.bb.parameters():
            p.requires_grad_(False)

    def forward(self, W):
        with torch.no_grad():
            h = self.bb(W)[:, :, 0]
        return self.lin(self.norm(h).flatten(1))


class SmallContext(nn.Module):
    def __init__(self, n_ch):
        super().__init__()
        self.body = nn.Sequential(nn.Conv1d(n_ch, 32, 5, padding=2), nn.GELU(), nn.Conv1d(32, 32, 5, padding=2), nn.GELU())
        self.lin = nn.Linear(32, CTX)

    def forward(self, W):
        return self.lin(self.body(W).mean(-1))


class ResidualModel(nn.Module):
    def __init__(self, enc, ctx, d):
        super().__init__()
        self.enc, self.ctx = enc, ctx
        for p in self.enc.parameters():
            p.requires_grad_(False)
        self.res = ZeroResidualPrediction(enc.n_tokens * 32, CTX, d)

    def forward(self, P, W):
        with torch.no_grad():
            ub = self.enc(P); tok = self.enc.forward_tokens(P).flatten(1)
        return F.normalize(self.res(ub, tok, self.ctx(W)), dim=-1)


def groups_of(bt):
    parts = sorted(set(bt.coh_segments[i]["p"] for i in list(bt.fit) + list(bt.es)))
    perm = np.random.default_rng(GROUP_SEED).permutation(len(parts))
    return {p: int(perm[i]) % N_GROUPS for i, p in enumerate(parts)}


class Rows:
    def __init__(self, bt, pre, post):
        from .local_support import masked_windows
        self.bt, self.pre, self.post, self.mw = bt, pre, post, masked_windows
        self.starts = torch.tensor(sorted({s["e0"] for s in bt.coh_segments}), device=bt.dev)

    def windows(self, e):
        return self.mw(self.bt.E, e, -self.pre, self.post, self.starts)


@torch.no_grad()
def dev_risk(model, bt, rw, head, q_units, c_units, cal_units, offs):
    """candidate CE (bits) of q_units' queries among the c_units pool; temperature fitted on cal_units against their own pool."""
    def u_of(units):
        out = []
        for k in range(0, len(units), 16):
            e0 = torch.tensor([bt.coh_segments[i]["e0"] for i in units[k:k + 16]], device=bt.dev)
            e = (e0[:, None] + offs[None]).reshape(-1)
            out.append(model(bt.patches(e), rw.windows(e)).reshape(len(e0), len(offs), -1))
        return torch.cat(out)

    def v_of(units):
        s0 = torch.tensor([bt.coh_segments[i]["s0"] for i in units], device=bt.dev)
        return head(bt.audio((s0[:, None] + offs[None]).reshape(-1))).reshape(len(units), len(offs), -1)

    def scores(qu, cv):
        return torch.einsum("qtd,ctd->qc", qu, cv) / qu.shape[1]

    def pool(units):  # unique stimulus segments (several participants hear the same audio), as the evaluation's candidate pools
        uid = {}
        for i in units:
            uid.setdefault(bt.coh_segments[i]["uid"], i)
        keys = list(uid); return [uid[k] for k in keys], torch.tensor([keys.index(bt.coh_segments[i]["uid"]) for i in units], device=bt.dev)
    cpool, cown = pool(cal_units)
    Sc = scores(u_of(cal_units), v_of(cpool)); own = cown
    sd = float(Sc.std()) + 1e-12; best = None
    for tau in np.logspace(-3, 2, 41) * sd:
        z = Sc / tau; ce = float((torch.logsumexp(z, 1) - z[torch.arange(len(own), device=bt.dev), own]).mean())
        if best is None or ce < best[0]:
            best = (ce, tau)
    dpool, down = pool(q_units)
    Sd = scores(u_of(q_units), v_of(dpool)) / best[1]; ix = torch.arange(len(q_units), device=bt.dev)
    ll = (torch.logsumexp(Sd, 1) - Sd[ix, down]) / math.log(2)
    rank = (Sd > Sd[ix, down][:, None]).float().sum(1) / max(1, len(dpool) - 1)
    return float(ll.mean()), float(rank.mean()), float(best[1])


def fit_residual(row, b, coh, dev, ckpt_prefix, log, base_ck, d=32, grid=3, epochs=None):
    from auditory_alignment.train import Objective
    from auditory_alignment_v2.audio_targets import build_head, target_stats
    from auditory_alignment_v2.foundation_adapter import Backbone
    from auditory_alignment_v2.temporal import build_encoder
    from .local_train import GridBatcher
    s = row["spec"]; E = epochs or EPOCHS
    bt = GridBatcher(coh, {**b["spec"], "architecture": "lag_local_tokens", "window": "full"}, b, dev, grid)  # bound row (ALN2 fields)
    pre, post = int(round(PRE_S * coh.fs)), int(bt.W[0][1]); rw = Rows(bt, pre, post)
    enc = build_encoder("lag_local_tokens", coh.n_ch, d, bt.W, coh.fs).to(dev)
    sd = torch.load(base_ck, map_location=dev); enc.load_state_dict(sd["enc"], strict=True); enc.eval()
    head = build_head("fixed_features", bt.audio_dim, d, coh.meta["dataset"], target_stats(bt, np.random.default_rng(row["seed"] + 5))).to(dev)
    head.load_state_dict(sd["head"], strict=True); head.eval()
    torch.manual_seed(row["seed"])
    if s["variant"] == "residual_small_capacity":
        ctx = SmallContext(coh.n_ch)
    else:
        bb = Backbone(s["architecture"], coh.meta["dataset"], "pretrained_frozen" if s["variant"] == "residual_aligned_pretrained" else "random_full", coh.fs)
        ctx = FMContext(bb)
    model = ResidualModel(enc, ctx, d).to(dev); model.enc.eval()
    if hasattr(model.ctx, "bb"):
        model.ctx.bb.eval()
    grp = groups_of(bt)
    tr_fit = [i for i in bt.fit if grp[bt.coh_segments[i]["p"]] != DEV_GROUP]; tr_es = [i for i in bt.es if grp[bt.coh_segments[i]["p"]] != DEV_GROUP]
    dv = [i for i in list(bt.fit) + list(bt.es) if grp[bt.coh_segments[i]["p"]] == DEV_GROUP]
    rng_d = np.random.default_rng(GROUP_SEED + 1)
    dv = sorted(rng_d.choice(dv, size=min(300, len(dv)), replace=False).tolist()); cal = sorted(rng_d.choice(tr_es, size=min(300, len(tr_es)), replace=False).tolist())
    assert not set(bt.coh_segments[i]["p"] for i in dv) & set(bt.coh_segments[i]["p"] for i in tr_fit + tr_es)
    step_ = max(grid, (bt.seg_len // Q) // grid * grid); offs = torch.arange(Q, device=dev) * step_
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=LR_, weight_decay=WD)
    obj_job = {"objective": s["objective"], "config": {"temperature": 0.1, "bandwidth_multiplier": 1.0, "fmca_relative_ridge": 1e-3}}
    rng = np.random.default_rng(row["seed"])
    calib = next(bt.epoch_batches(np.random.default_rng(row["seed"] + 99), N_SEG, tr_fit)); r0 = bt.rows(calib, np.random.default_rng(row["seed"] + 98), anchors=Q)
    with torch.no_grad():
        u0 = model(bt.patches(r0[0]), rw.windows(r0[0])); ub0 = enc(bt.patches(r0[0]))
        obj = Objective(obj_job, u0, head(bt.audio(r0[1])))
    log["epoch0_max_abs_diff_vs_base"] = float((u0 - ub0).abs().max())
    rpath = ckpt_prefix + "_resume.pt"; curve, ep0, best = [], 0, None
    trainable = {n: p for n, p in model.named_parameters() if p.requires_grad}
    if os.path.exists(rpath):
        r = torch.load(rpath, map_location=dev, weights_only=False)
        model.load_state_dict(r["model"]); opt.load_state_dict(r["opt"]); rng.bit_generator.state = r["rng"]; torch.set_rng_state(r["torch_rng"].cpu())
        curve, ep0, best = r["curve"], r["epoch"], tuple(r["best"]) if r["best"] else None; log["resumed_from_epoch"] = ep0
    if ep0 == 0:
        model.eval(); dr, rk, tau = dev_risk(model, bt, rw, head, dv, dv, cal, offs)
        curve.append({"epoch": 0, "dev_risk_bits": dr, "dev_rank": rk, "tau": tau, "train_loss": None}); best = (dr, 0)
        torch.save({"model": {n: p.detach().clone() for n, p in model.state_dict().items() if not n.startswith(("enc.", "ctx.bb."))}}, ckpt_prefix + "_best.pt")
    for ep in range(ep0, E):
        model.train(); model.enc.eval()
        if hasattr(model.ctx, "bb"):
            model.ctx.bb.eval()
        tl = []
        for batch in bt.epoch_batches(rng, N_SEG, tr_fit):
            r = bt.rows(batch, rng, anchors=Q)
            u = model(bt.patches(r[0]), rw.windows(r[0])); loss, _ = obj(u, head(bt.audio(r[1])), keys=r[2])
            opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(params, 5.0); opt.step(); tl.append(float(loss))
        model.eval(); dr, rk, tau = dev_risk(model, bt, rw, head, dv, dv, cal, offs)
        curve.append({"epoch": ep + 1, "dev_risk_bits": dr, "dev_rank": rk, "tau": tau, "train_loss": float(np.mean(tl)) if tl else None})
        if dr < best[0]:
            best = (dr, ep + 1)
            torch.save({"model": {n: p.detach().clone() for n, p in model.state_dict().items() if not n.startswith(("enc.", "ctx.bb."))}}, ckpt_prefix + "_best.pt")
        torch.save({"model": model.state_dict(), "opt": opt.state_dict(), "rng": rng.bit_generator.state, "torch_rng": torch.get_rng_state(),
                    "curve": curve, "epoch": ep + 1, "best": list(best)}, rpath + ".tmp")
        os.replace(rpath + ".tmp", rpath)
    if os.path.exists(rpath):
        os.remove(rpath)
    st = torch.load(ckpt_prefix + "_best.pt", map_location=dev)["model"]; model.load_state_dict(st, strict=False); model.eval()
    log.update({"curve": curve, "selected_epoch": best[1], "selected_dev_risk_bits": best[0], "epoch0_selected": best[1] == 0, "epochs": E,
                "n_train_segments": len(tr_fit), "n_dev_segments": len(dv), "n_cal_segments": len(cal), "dev_group": DEV_GROUP, "groups": N_GROUPS,
                "trainable_params": int(sum(p.numel() for p in params)), "window_samples": [-pre, post], "objective_calibration": obj.record()})
    return model, head, bt, rw


class ResReps:
    def __init__(self, model, rw, head, bt, stride, reps_cls, chunk=8):
        self.model, self.rw, self.aud, self.bt, self.chunk = model, rw, head, bt, chunk
        self.offs = np.arange(0, bt.seg_len, stride); self._va = reps_cls(None, head, bt, stride=stride)

    @torch.no_grad()
    def u(self, e0s):
        e0s = np.asarray(e0s); out = []; q = torch.tensor(self.offs, device=self.bt.dev)
        for k in range(0, len(e0s), self.chunk):
            e = (torch.tensor(e0s[k:k + self.chunk], device=self.bt.dev)[:, None] + q[None]).reshape(-1)
            out.append(self.model(self.bt.patches(e), self.rw.windows(e)).reshape(-1, len(self.offs), self.model.res.output_dim).float().cpu().numpy())
        return np.concatenate(out)

    def va(self, s0s):
        return self._va.va(s0s)


def run(row, out, epochs=None):
    from auditory_alignment import evaluate as ev1
    from auditory_alignment_v2 import evaluate as ev2
    from auditory_alignment_v2.run import load_cohort
    path = os.path.join(out, "units", f"{row['experiment_id']}.json")
    rows = core.load_rows(); br = base_ready(row, rows)
    if br is None:
        print("technical_pending (base not complete)", row["experiment_id"]); return
    b = core.bind(row); dev = torch.device("cuda"); t0 = time.time(); rec = core.new_record(row, b, out)
    rec["dependency"] = {"base": br[0]["experiment_id"], "base_code_hash": json.load(open(br[1]))["code_hash"], "base_checkpoint": os.path.relpath(br[2], core.REPO)}
    try:
        coh = load_cohort(b); g = core.grid_samples(coh.fs); log = {}
        model, head, bt, rw = fit_residual(row, b, coh, dev, os.path.join(out, "ckpt", row["experiment_id"]), log, br[2], d=int(row["spec"].get("projection_dim", 32)),
                                           grid=g, epochs=epochs)
        rec.update(log)
        orig = ev1.Reps
        ev1.Reps = lambda enc_, aud, bt_, **kw: ResReps(model, rw, head, bt_, g, orig)
        try:
            t1 = time.time(); rec["eval"] = ev2.evaluate_continuous(b, model, head, bt, coh, log["objective_calibration"], None); rec["eval_seconds"] = round(time.time() - t1, 1)
        finally:
            ev1.Reps = orig
        rec["status"] = "complete"
    except Exception as ex:  # noqa: BLE001
        rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    core.write_record(path, rec, t0)
