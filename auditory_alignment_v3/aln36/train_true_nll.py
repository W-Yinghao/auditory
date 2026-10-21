"""ALN3.6 trainers: the two parent recipes with the checkpoint rule replaced by source-ES true-query NLL.

fit_local = local_train.fit_continuous on the local_aligned1000 path (the GridBatcher that local_support.run patches in);
fit_cb    = fm_aligned32.fit_aligned32 with recipe full_onestep_v1 (every backbone group open from the first epoch, LLRD 1).
Optimiser, schedule, batches, objective, audio head, validation cadence, resume and update ledger are unchanged.
Declared differences only (package docs/04 §4.4.1):
  - the batcher class is passed in; ALN3.6 passes a subclass that installs the frozen legal source fit/ES sets;
  - candidates = the initial state plus every registered validation point (local: every 5th epoch and the last;
    CB: every epoch); the selected state minimises SourceRisk (native retrieval NLL, bits/query, on the frozen
    source-ES queries against the frozen deduplicated source-ES audio pool; temperature fitted on a frozen
    source-fit calibration set, never on ES); ties keep the earlier state;
  - the inherited es_loss - mismatch gain, CS diagnostics and the ES-profiled NLL are recorded as diagnostics only;
  - branches the two parents never use (selection task, anchored head, CS/FMCA objectives, aln3/warm-up recipes) are
    removed and asserted absent.
"""
from __future__ import annotations

import math
import os
import time

import numpy as np
import torch
from scipy.optimize import minimize_scalar

from auditory_alignment.train import Objective, _eff_rank, _kernel_stats, _save_resume, cs_diag
from auditory_alignment_v2.audio_targets import build_head, target_stats
from auditory_alignment_v2.temporal import build_encoder, describe
from auditory_alignment_v2.train import N_SEL, ROWS
from auditory_alignment_v2.foundation_adapter import Backbone
from ..fm_aligned import POST_S, PRE_S, AlignedFM
from ..fm_aligned32 import _ledger_epoch, _ledger_final, _ledger_init, _ledger_save, _ledger_step
from ..fm_dense import block_groups

LN2 = math.log(2.0)
SELECTION_RULE = ('argmin over {initial state, registered validations} of source-ES true-query native NLL (bits/query); '
                  'temperature fitted per candidate on the frozen source-fit calibration queries; ties keep the earlier state')


def native_scores(Uq, Vc):
    """Uq [nq, T, d], Vc [nc, T, d] -> [nq, nc]; the NCE native score of auditory_alignment.evaluate.Readouts.scores."""
    return np.einsum('qtd,ctd->qc', Uq, Vc) / Uq.shape[1]


def nll_bits(S, own, tau):
    z = S / tau
    z = z - z.max(1, keepdims=True)
    return float(np.mean(np.log(np.exp(z).sum(1)) - z[np.arange(len(z)), own]) / LN2)


def fit_tau(S, own):
    """One scalar temperature minimising the candidate NLL of these (calibration) queries."""
    sd = float(S.std()) + 1e-12
    res = minimize_scalar(lambda lt: nll_bits(S, own, math.exp(lt)), bounds=(math.log(sd * 1e-4), math.log(sd * 1e3)),
                          method='bounded', options={'xatol': 1e-5})
    return float(math.exp(res.x))


class SourceRisk:
    """Frozen source-side query/candidate sets (built by the binding, before any production training)."""

    def __init__(self, bt, sets):
        segs = bt.coh_segments
        self.T = np.asarray(sets['anchors'], dtype=np.int64)
        assert len(self.T) and self.T.min() >= 0 and self.T.max() < bt.seg_len
        self.parts = {}
        for name in ('cal', 'es'):
            q, c = sets[name + '_queries'], sets[name + '_candidates']
            uid_of = [segs[i]['uid'] for i in q]
            cand_uid = [segs[i]['uid'] for i in c]
            assert len(set(cand_uid)) == len(cand_uid) and set(uid_of) <= set(cand_uid)
            col = {u: k for k, u in enumerate(cand_uid)}
            self.parts[name] = {'e0': np.array([segs[i]['e0'] for i in q]), 's0': np.array([segs[i]['s0'] for i in c]),
                                'own': np.array([col[u] for u in uid_of]), 'n_queries': len(q), 'n_candidates': len(c)}

    def __call__(self, u_fn, v_fn):
        out = {}
        S = {}
        for name, p in self.parts.items():
            S[name] = native_scores(u_fn(p['e0'], self.T), v_fn(p['s0'], self.T))
        cal, es = self.parts['cal'], self.parts['es']
        tau = fit_tau(S['cal'], cal['own'])
        out['nll_bits'] = nll_bits(S['es'], es['own'], tau)
        out['tau_source_fit'] = tau
        out['cal_nll_bits'] = nll_bits(S['cal'], cal['own'], tau)
        tau_es = fit_tau(S['es'], es['own'])  # diagnostic only, never used for selection
        out['diagnostic_es_profiled_nll_bits'] = nll_bits(S['es'], es['own'], tau_es)
        out['diagnostic_es_profiled_tau'] = tau_es
        order = np.argsort(-S['es'], axis=1)
        rank = np.array([int(np.flatnonzero(order[i] == es['own'][i])[0]) for i in range(len(order))])
        out['es_top1'] = float((rank == 0).mean())
        out['es_rank_pct'] = float((rank / max(1, S['es'].shape[1] - 1)).mean())
        out['uniform_bits'] = math.log2(es['n_candidates'])
        return out

    def describe(self):
        return {'anchors': self.T.tolist(), **{f'{k}_{f}': v[f] for k, v in self.parts.items() for f in ('n_queries', 'n_candidates')}}


def _state_copy(modules):
    return {k: {n: p.detach().clone().cpu() for n, p in m.state_dict().items()} for k, m in modules.items()}


def _rel_change(modules, initial):
    num = den = 0.0
    for k, m in modules.items():
        for n, p in m.named_parameters():
            q = initial[k][n].to(p.device).float()
            num += float(((p.detach().float() - q) ** 2).sum()); den += float((q ** 2).sum())
    return math.sqrt(num) / (math.sqrt(den) + 1e-12)


def fit_local(row, coh, dev, ckpt_prefix, log, batcher_cls, risk_sets, d=32, grid=1):
    spec = row["spec"]
    obj_name = spec["objective"]
    assert obj_name == "NCE" and spec.get("training_task", "paired_alignment") == "paired_alignment"
    assert spec.get("audio_head") == "fixed_features" and spec["architecture"] == "lag_local_tokens"
    n_seg = max(2, ROWS.get(obj_name, 256) // 8)
    torch.manual_seed(row["seed"]); rng = np.random.default_rng(row["seed"])
    bt = batcher_cls(coh, spec, row, dev, grid)
    assert not bt.selection and not bt.wrong
    enc = build_encoder(spec["architecture"], coh.n_ch, d, bt.W, coh.fs).to(dev)
    stats = target_stats(bt, np.random.default_rng(row["seed"] + 5))
    head = build_head(spec.get("audio_head", "trainable_head"), bt.audio_dim, d, coh.meta["dataset"], stats).to(dev)
    params = [p for m in (enc, head) for p in m.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=1e-3, weight_decay=1e-4)
    epochs = int(spec.get("epochs", 200))
    steps_per_epoch = max(1, len(bt.fit) // n_seg)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs * steps_per_epoch)
    calib = next(bt.epoch_batches(np.random.default_rng(row["seed"] + 99), n_seg))
    obj_job = {"objective": obj_name, "config": {"temperature": 0.1, "bandwidth_multiplier": 1.0, "fmca_relative_ridge": 1e-3}}
    with torch.no_grad():
        r0 = bt.rows(calib, np.random.default_rng(row["seed"] + 98))
        obj = Objective(obj_job, enc(bt.patches(r0[0])), head(bt.audio(r0[1])))
    es_rng = np.random.default_rng(12345)
    es_sel = []
    while len(es_sel) < N_SEL:
        got = [b for b, _ in zip(bt.epoch_batches(es_rng, n_seg, bt.es), range(N_SEL - len(es_sel)))]
        if not got:
            break
        es_sel += got
    es_sets = [(bt.rows(b, np.random.default_rng(k)), bt.rows(b, np.random.default_rng(k), roll=True), len(b)) for k, b in enumerate(es_sel)]
    risk = SourceRisk(bt, risk_sets)
    mods = {"enc": enc, "head": head}
    initial = _state_copy(mods)

    @torch.no_grad()
    def u_fn(e0, T):
        idx = torch.as_tensor((np.asarray(e0)[:, None] + T[None]).reshape(-1), device=dev)
        out = [enc(bt.patches(idx[k:k + 4096])) for k in range(0, len(idx), 4096)]
        return torch.cat(out).float().cpu().numpy().reshape(len(e0), len(T), -1)

    @torch.no_grad()
    def v_fn(s0, T):
        idx = torch.as_tensor((np.asarray(s0)[:, None] + T[None]).reshape(-1), device=dev)
        return head(bt.audio(idx)).float().cpu().numpy().reshape(len(s0), len(T), -1)

    def batch_loss(rws):
        u, v = enc(bt.patches(rws[0])), head(bt.audio(rws[1]))
        la, _ = obj(u, v, keys=rws[2])
        return la, u, v

    best, t0, step, curve, ep0 = (math.inf, -1), time.time(), 0, [], 0
    rpath = ckpt_prefix + "_resume.pt"
    if os.path.exists(rpath):
        r = torch.load(rpath, map_location=dev, weights_only=False)
        for k, m in mods.items():
            m.load_state_dict(r[k])
        opt.load_state_dict(r["opt"]); sched.load_state_dict(r["sched"])
        rng.bit_generator.state = r["rng"]; torch.set_rng_state(r["torch_rng"].cpu()); best, step, curve, ep0 = tuple(r["best"]), r["step"], r["curve"], r["epoch"]
        initial = r["initial"]
        log["resumed_from_epoch"] = ep0
    else:
        for m in mods.values():
            m.eval()
        rk = risk(u_fn, v_fn)
        curve.append({"epoch": 0, "step": 0, "candidate": "initial_state", "seconds": 0.0, **{"risk_" + k: v for k, v in rk.items()}})
        best = (rk["nll_bits"], 0)
        torch.save({k: m.state_dict() for k, m in mods.items()}, ckpt_prefix + "_best.pt")
    for ep in range(ep0, epochs):
        for m in mods.values():
            m.train()
        tl, gns, nonfin = [], [], 0
        for batch in bt.epoch_batches(rng, n_seg):
            rws = bt.rows(batch, rng)
            loss, _, _ = batch_loss(rws)
            opt.zero_grad(); loss.backward()
            gn = float(torch.nn.utils.clip_grad_norm_(params, 5.0))
            if not math.isfinite(gn) or not torch.isfinite(loss):
                nonfin += 1; opt.zero_grad(); continue
            opt.step(); sched.step(); step += 1; tl.append(float(loss)); gns.append(gn)
        if ep % 5 == 4 or ep == epochs - 1:
            for m in mods.values():
                m.eval()
            with torch.no_grad():
                el, elr, dm, dx = [], [], [], []
                for (rws, rr, n_b) in es_sets:
                    l_, u, v = batch_loss(rws)
                    lr_, _, vr = batch_loss(rr)
                    el.append(float(l_)); elr.append(float(lr_))
                    if obj.sigma_v is not None:
                        dm.append(cs_diag(u, v, sigma_u=obj.sigma_u, sigma_v=obj.sigma_v)); dx.append(cs_diag(u, vr, sigma_u=obj.sigma_u, sigma_v=obj.sigma_v))
                es_loss, es_mm = float(np.mean(el)), float(np.mean(elr))
                avg = lambda L, k: float(np.mean([x[k] for x in L])) if L else None
                rk = risk(u_fn, v_fn)
                rec = {"epoch": ep + 1, "step": step, "candidate": "validation", "train_loss": float(np.mean(tl)) if tl else None,
                       "es_loss": es_loss, "es_loss_mismatched": es_mm, "diagnostic_gain_score": es_loss - es_mm,
                       "grad_norm": float(np.mean(gns)) if gns else None, "nonfinite_steps": nonfin, "seconds": round(time.time() - t0, 1),
                       "es_cs_true_nats": avg(dm, "cs_qmi_nats"), "es_cs_mismatched_nats": avg(dx, "cs_qmi_nats"),
                       "u_eff_rank": _eff_rank(u), "kernel_u": _kernel_stats(u, obj.sigma_u), "lr": float(sched.get_last_lr()[0]),
                       **{"risk_" + k: v for k, v in rk.items()}}
            curve.append(rec)
            if rk["nll_bits"] < best[0]:
                best = (rk["nll_bits"], ep + 1)
                torch.save({k: m.state_dict() for k, m in mods.items()}, ckpt_prefix + "_best.pt")
            if (ep + 1) % 20 == 0 and ep + 1 < epochs:
                _save_resume(rpath, **{k: m.state_dict() for k, m in mods.items()}, opt=opt.state_dict(), sched=sched.state_dict(),
                             rng=rng.bit_generator.state, torch_rng=torch.get_rng_state(), best=list(best), step=step, curve=curve,
                             epoch=ep + 1, initial=initial)
    last_change = _rel_change(mods, initial)
    if os.path.exists(rpath):
        os.remove(rpath)
    gains = [c for c in curve if c.get("candidate") == "validation"]
    log.update({"objective_calibration": obj.record(), "curve": curve, "best_epoch": best[1], "best_selection_score": best[0],
                "selection_rule": SELECTION_RULE, "selection_object": "source_ES_true_query_native_NLL_bits", "risk_sets": risk.describe(),
                "diagnostic_gain_selected_epoch": min(gains, key=lambda c: c["diagnostic_gain_score"])["epoch"] if gains else None,
                "last_state_relative_weight_change": last_change,
                "epochs_completed": epochs, "optimizer_steps": step, "steps_per_epoch": steps_per_epoch, "n_fit_segments": len(bt.fit),
                "n_es_segments": len(bt.es), "n_train_participants": len(bt.train_p), "train_seconds": round(time.time() - t0, 1),
                "encoder": describe(enc), "windows_samples": [list(w) for w in bt.W], "window_rule": "half_open",
                "audio_head": spec.get("audio_head"), "learning_rate": 1e-3, "weight_decay": 1e-4})
    sd = torch.load(ckpt_prefix + "_best.pt", map_location=dev)
    for k, m in mods.items():
        m.load_state_dict(sd[k]); m.eval()
    return enc, head, bt


def fit_cb(row, coh, dev, ckpt_prefix, log, batcher_cls, risk_sets, epochs, lr, d=32, grid=3, n_seg=32):
    spec = row["spec"]; arch, ad, obj_name = spec["architecture"], spec["adaptation"], spec["objective"]
    recipe = "full_onestep_v1"
    assert arch == "cbramod" and ad == "pretrained_full" and obj_name == "NCE"
    torch.manual_seed(row["seed"]); rng = np.random.default_rng(row["seed"])
    bb = Backbone(arch, coh.meta["dataset"], ad, coh.fs)
    allowed = {id(p) for p in bb.parameters() if p.requires_grad}  # what the adaptation permits (Backbone._apply_adaptation)
    bt = batcher_cls(coh, spec, row, dev, grid)
    model = AlignedFM(bb, d).to(dev)
    stats = target_stats(bt, np.random.default_rng(row["seed"] + 5))
    head = build_head("fixed_features", bt.audio_dim, d, coh.meta["dataset"], stats).to(dev)
    lr_b, lr_h = lr
    E = epochs
    groups_bb = block_groups(bb)
    pg = []
    for kind, i, ps in groups_bb:
        ps = [p for p in ps if id(p) in allowed]
        if ps:
            pg.append({"params": ps, "lr": lr_b * 1.0, "name": f"{kind}{i}"})
    pg.append({"params": list(model.readout.parameters()), "lr": lr_h, "name": "readout"})
    opt = torch.optim.AdamW(pg, weight_decay=1e-4)
    led = _ledger_init(pg, ckpt_prefix)
    rows_ = ROWS.get(obj_name, 256); Q = 8; n_seg = max(2, rows_ // Q)
    steps_per_epoch = max(1, len(bt.fit) // n_seg)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=E * steps_per_epoch)
    obj_job = {"objective": obj_name, "config": {"temperature": 0.1, "bandwidth_multiplier": 1.0, "fmca_relative_ridge": 1e-3}}

    def set_trainable(ep):
        """full_onestep_v1: every group the adaptation allows is open from the first epoch."""
        n_open = len(groups_bb)
        for gi, (kind, i, ps) in enumerate(groups_bb):
            for p in ps:
                p.requires_grad_(id(p) in allowed and gi < n_open)
        return n_open

    def loss_of(e0, t, s0, keys, enc_out=None):
        U = model(bt.windows(e0, t)) if enc_out is None else enc_out
        u = U.reshape(-1, d); v = head(bt.audio(s0))
        la, _ = obj(u, v, keys=keys)
        return la, u, v, U

    calib = next(bt.epoch_batches(np.random.default_rng(row["seed"] + 99), n_seg))
    with torch.no_grad():
        e0, t, s0, keys = bt.dense_rows(calib, np.random.default_rng(row["seed"] + 98), anchors=Q)
        obj = Objective(obj_job, model(bt.windows(e0, t)).reshape(-1, d), head(bt.audio(s0)))
    es_rng = np.random.default_rng(12345); es_sel = []
    while len(es_sel) < N_SEL:
        got = [b for b, _ in zip(bt.epoch_batches(es_rng, n_seg, bt.es), range(N_SEL - len(es_sel)))]
        if not got:
            break
        es_sel += got
    es_sets = [(bt.dense_rows(b, np.random.default_rng(k), anchors=Q), bt.dense_rows(b, np.random.default_rng(k), anchors=Q, roll=True)) for k, b in enumerate(es_sel)]
    risk = SourceRisk(bt, risk_sets)
    mods = {"model": model}
    initial = _state_copy(mods)

    @torch.no_grad()
    def u_fn(e0, T):
        out = []
        tt = torch.as_tensor(T, device=dev)
        for k in range(0, len(e0), 128):
            e = torch.as_tensor(np.asarray(e0[k:k + 128]), device=dev)
            out.append(model(bt.windows(e, tt[None].expand(len(e), -1))).float().cpu().numpy())
        return np.concatenate(out).reshape(len(e0), len(T), -1)

    @torch.no_grad()
    def v_fn(s0, T):
        idx = torch.as_tensor((np.asarray(s0)[:, None] + T[None]).reshape(-1), device=dev)
        return head(bt.audio(idx)).float().cpu().numpy().reshape(len(s0), len(T), -1)

    best, t0, step, curve, ep0 = (math.inf, -1), time.time(), 0, [], 0
    rpath = ckpt_prefix + "_resume.pt"
    if os.path.exists(rpath):
        r = torch.load(rpath, map_location=dev, weights_only=False)
        model.load_state_dict(r["model"]); opt.load_state_dict(r["opt"]); sched.load_state_dict(r["sched"])
        rng.bit_generator.state = r["rng"]; torch.set_rng_state(r["torch_rng"].cpu()); best, step, curve, ep0 = tuple(r["best"]), r["step"], r["curve"], r["epoch"]
        initial = r["initial"]
        log["resumed_from_epoch"] = ep0
    else:
        model.eval()
        rk = risk(u_fn, v_fn)
        curve.append({"epoch": 0, "step": 0, "candidate": "initial_state", "seconds": 0.0, **{"risk_" + k: v for k, v in rk.items()}})
        best = (rk["nll_bits"], 0)
        torch.save({"model": model.state_dict()}, ckpt_prefix + "_best.pt")
    ve = 1
    for ep in range(ep0, E):
        n_open = set_trainable(ep)
        _ledger_epoch(led, pg, ep)
        params = [p for g in pg for p in g["params"] if p.requires_grad]
        model.train(); tl, gns, nonfin = [], [], 0
        for batch in bt.epoch_batches(rng, n_seg):
            e0, t, s0, keys = bt.dense_rows(batch, rng, anchors=Q)
            loss, _, _, _ = loss_of(e0, t, s0, keys)
            opt.zero_grad(); loss.backward()
            gn = float(torch.nn.utils.clip_grad_norm_(params, 5.0))
            if not math.isfinite(gn) or not torch.isfinite(loss):
                nonfin += 1; opt.zero_grad(); continue
            _ledger_step(led, pg); opt.step(); sched.step(); step += 1; tl.append(float(loss)); gns.append(gn)
        if (ep + 1) % ve == 0 or ep == E - 1:
            model.eval()
            with torch.no_grad():
                el, elr, dm, dx = [], [], [], []
                for (a, b) in es_sets:
                    l1, u, v, U = loss_of(*a); l2, _, vr, _ = loss_of(b[0], b[1], b[2], b[3], enc_out=U)
                    el.append(float(l1)); elr.append(float(l2))
                    dm.append(cs_diag(u, v, sigma_u=obj.sigma_u, sigma_v=obj.sigma_v)); dx.append(cs_diag(u, vr, sigma_u=obj.sigma_u, sigma_v=obj.sigma_v))
                rk = risk(u_fn, v_fn)
            es_loss, es_mm = float(np.mean(el)), float(np.mean(elr))
            curve.append({"epoch": ep + 1, "step": step, "candidate": "validation", "open_groups": n_open,
                          "train_loss": float(np.mean(tl)) if tl else None, "es_loss": es_loss,
                          "es_loss_mismatched": es_mm, "diagnostic_gain_score": es_loss - es_mm, "grad_norm": float(np.mean(gns)) if gns else None,
                          "nonfinite_steps": nonfin, "seconds": round(time.time() - t0, 1), "es_cs_true_nats": float(np.mean([x["cs_qmi_nats"] for x in dm])),
                          "es_cs_mismatched_nats": float(np.mean([x["cs_qmi_nats"] for x in dx])), "u_eff_rank": _eff_rank(u),
                          **{"risk_" + k: v for k, v in rk.items()}})
            if rk["nll_bits"] < best[0]:
                best = (rk["nll_bits"], ep + 1); torch.save({"model": model.state_dict()}, ckpt_prefix + "_best.pt")
            _save_resume(rpath, model=model.state_dict(), opt=opt.state_dict(), sched=sched.state_dict(), rng=rng.bit_generator.state,
                         torch_rng=torch.get_rng_state(), best=list(best), step=step, curve=curve, epoch=ep + 1, initial=initial); _ledger_save(led)
    last_change = _rel_change(mods, initial)
    if os.path.exists(rpath):
        os.remove(rpath)
    gains = [c for c in curve if c.get("candidate") == "validation"]
    log.update({"objective_calibration": obj.record(), "curve": curve, "best_epoch": best[1], "best_selection_score": best[0], "epochs_completed": E,
                "selection_rule": SELECTION_RULE, "selection_object": "source_ES_true_query_native_NLL_bits", "risk_sets": risk.describe(),
                "diagnostic_gain_selected_epoch": min(gains, key=lambda c: c["diagnostic_gain_score"])["epoch"] if gains else None,
                "last_state_relative_weight_change": last_change,
                "optimizer_steps": step, "steps_per_epoch": steps_per_epoch, "n_fit_segments": len(bt.fit), "n_es_segments": len(bt.es),
                "n_train_participants": len(bt.train_p), "train_seconds": round(time.time() - t0, 1), "backbone_contract": bb.contract(),
                "readout": "aligned_patch_linear", "readout_params": int(sum(p.numel() for p in model.readout.parameters())), "recipe": recipe,
                "lr_backbone": lr_b, "lr_head": lr_h, "llrd": None, "warmup_epochs": 0,
                "unfreeze_every": None, "val_every": ve, "queries_per_segment": Q,
                "window_s": [-PRE_S, POST_S], "window_native_samples": bt.pre + bt.post, "param_group_lrs": [g["lr"] for g in pg]})
    model.load_state_dict(torch.load(ckpt_prefix + "_best.pt", map_location=dev)["model"]); model.eval()
    log["update_ledger"] = _ledger_final(led, pg, model, row, coh, d)
    return model, head, bt
