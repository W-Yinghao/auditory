"""ALN3.4 R34_FUSION_FUNCTION: the per-unit forward-pass evaluator (the value-producing path of every per-unit output).

Kept apart from aggregation and reporting (complement_function.py) so that a per-unit output names the evaluator source it ran:
each output records the sha256 of this module and of the CLI module as loaded, plus the frozen modules on the path, and the
loaded source of both modules is written once to <results>/code_snapshots/<name>.<sha12>.py (v2; see the analysis note,
Correction 1). The evaluation code itself is unchanged from the v1 version that produced the v1 outputs.

One ALN32_RESIDUAL unit is rebuilt without training (frozen base encoder and fixed audio head from the base checkpoint; context
branch with the random backbone regenerated from the seed; selected-epoch weights from the unit checkpoint). u_base and r are
split per anchor and the base and RS views are scored under one readout contract (auditory_alignment.evaluate.
evaluate_continuous: identical readout / calibration sampling per view). Outputs: layers 1-3 per test identity, development-side
layers and risks, and the reproduction deviations against the saved records. Reference math: the package's
src/aln34_reference/residuals.py, loaded by file path. Frozen modules are imported, never edited."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import resource
import socket
import time
from collections import defaultdict

import numpy as np

from auditory_alignment_v3 import core

REPO = core.REPO
PKG34 = os.path.join(REPO, "AUDITORY_ALN3_SERVER_PACKAGE_v3_4_20261016")
REF_RESIDUALS = os.path.join(PKG34, "src", "aln34_reference", "residuals.py")
RES = os.environ.get("CF_RES", os.path.join(REPO, "results", "auditory_alignment_v3", "aln34", "complement_function"))
UNITS_DIR = os.path.join(RES, "units_v2")  # v2 per-unit outputs (merged); the v1 outputs in units/ are kept, not merged
SEED = 3401
READOUTS = ("unified", "native")
QMETRICS = ("top1", "top5", "mrr", "rank_pct", "logloss_bits")
LAYER12 = ("rel_norm", "coef", "rel_par", "rel_orth", "post_change", "angle_deg")
LAYER3 = ("d_logloss", "frac_rank_changed", "mean_drank", "mean_abs_drank", "top1_gain", "top1_loss", "d_true_score", "d_true_z")
REPRO_TOL = 1e-3  # bits / fraction: engineering tolerance of the re-run against the saved record (float order), not a gate
REPRO_KEYS = ("unified/logloss_bits", "native/logloss_bits", "unified/rank_pct", "native/rank_pct")  # smooth aggregates; a single near-tie
# flip moves top1 / top5 / mrr by 1 / n_queries, so those are reported but not bounded
FROZEN_DEPS = ("auditory_alignment/evaluate.py", "auditory_alignment_v2/evaluate.py", "auditory_alignment_v2/foundation_adapter.py",
               "auditory_alignment_v2/temporal.py", "auditory_alignment_v2/audio_targets.py", "auditory_alignment_v2/run.py",
               "auditory_alignment_v3/core.py", "auditory_alignment_v3/local_train.py", "auditory_alignment_v3/local_support.py",
               "auditory_alignment_v3/residual32.py", "auditory_alignment_v3/aln3_reference/readouts.py")

with open(__file__, "rb") as _fh:
    _SOURCE = _fh.read()  # the source this process loaded (hashed and snapshotted from memory, not re-read from disk)
MODULE_SHA256 = hashlib.sha256(_SOURCE).hexdigest()
_CLI = {}  # the CLI module (complement_function.py) registers its loaded source here; it may run as __main__


def register_cli(source, sha):
    _CLI.update({"source": source, "sha256": sha})


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def code_versions():
    """sha256 of the evaluator and CLI modules as loaded, of the reference math and of the frozen modules on the path."""
    out = {"complement_function_eval.py": MODULE_SHA256}
    if _CLI:
        out["complement_function.py"] = _CLI["sha256"]
    out["reference residuals.py"] = sha256(REF_RESIDUALS)
    for rel in FROZEN_DEPS:
        out[rel] = sha256(os.path.join(REPO, rel))
    return out


def snapshot_code(snap_dir):
    """Write the loaded source of this module (and of the CLI module, if loaded) once to <snap_dir>/<name>.<sha12>.py (0600)."""
    items = [("complement_function_eval", _SOURCE, MODULE_SHA256)]
    if _CLI:
        items.append(("complement_function", _CLI["source"], _CLI["sha256"]))
    os.makedirs(snap_dir, mode=0o700, exist_ok=True)
    out = {}
    for name, src, h in items:
        p = os.path.join(snap_dir, f"{name}.{h[:12]}.py")
        if not os.path.exists(p):
            tmp = f"{p}.tmp{os.getpid()}"
            fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "wb") as f:
                f.write(src)
            os.replace(tmp, p)
        if sha256(p) != h:
            raise RuntimeError(f"code snapshot {p} does not match its hash")
        out[f"{name}.py"] = os.path.relpath(p, REPO)
    return out


def reproduces(u, tol=REPRO_TOL):
    """The one reproduction rule (also applied by the aggregator to stored outputs): a comparable full run whose per-participant
    log-loss and rank_pct match both saved records and whose development risks (selected epoch, epoch 0) match the saved curve."""
    if not u.get("comparable_to_record") or u.get("dev_only"):
        return False
    rp, d = u.get("reproduction") or {}, u.get("dev") or {}
    vals = [(rp.get(v) or {}).get(k) for v in ("base_record", "rs_record") for k in REPRO_KEYS]
    vals += [(d.get("selected") or {}).get("abs_diff"), (d.get("epoch0") or {}).get("abs_diff")]
    return all(x is not None and x <= tol for x in vals) and not (rp.get("participants_missing_in_record") or {})


# ================================================================================================ reference math (package D34)
def reference_residuals(path=REF_RESIDUALS):
    """The package's reference module, loaded by file path (no sys.path change)."""
    spec = importlib.util.spec_from_file_location("aln34_reference_residuals", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def residual_rows(u, r, eps=1e-12):
    """Per-row layer-1/2 quantities with the definitions of aln34_reference.residuals.residual_diagnostics, plus the angle
    between normalise(u) and normalise(u + r). Rows are anchors / queries, not people."""
    u = np.asarray(u, np.float64); r = np.asarray(r, np.float64)
    if u.ndim != 2 or u.shape != r.shape or min(u.shape) == 0 or not (np.isfinite(u).all() and np.isfinite(r).all()):
        raise ValueError("base and residual must be finite, nonempty, equal-shape (rows, features) arrays")
    nu, nr = np.linalg.norm(u, axis=1), np.linalg.norm(r, axis=1)
    coef = np.sum(u * r, axis=1) / np.maximum(nu ** 2, eps ** 2)
    par = coef[:, None] * u
    orth = r - par
    before = u / np.maximum(nu, eps)[:, None]
    after = (u + r) / np.maximum(np.linalg.norm(u + r, axis=1), eps)[:, None]
    cos = np.clip(np.sum(before * after, axis=1), -1.0, 1.0)
    return {"valid": nu > eps, "rel_norm": nr / np.maximum(nu, eps), "coef": coef,
            "rel_par": np.linalg.norm(par, axis=1) / np.maximum(nu, eps), "rel_orth": np.linalg.norm(orth, axis=1) / np.maximum(nu, eps),
            "post_change": np.linalg.norm(after - before, axis=1), "pre_change": nr, "angle_deg": np.degrees(np.arccos(cos))}


def residual_summary(rows):
    """Means in the reference's keys (valid rows; pre-normalisation change over all rows) + angle / tail descriptors."""
    v = rows["valid"]
    mv = lambda a: float(np.mean(a[v])) if v.any() else float("nan")
    q = lambda a, p: float(np.percentile(a[v], p)) if v.any() else float("nan")
    return {"n_rows": int(len(v)), "n_nonzero_base_rows": int(v.sum()), "n_zero_or_tiny_base_rows": int((~v).sum()),
            "relative_residual_norm_mean": mv(rows["rel_norm"]), "relative_parallel_norm_mean": mv(rows["rel_par"]),
            "relative_orthogonal_norm_mean": mv(rows["rel_orth"]), "normalized_change_mean": mv(rows["post_change"]),
            "pre_normalization_change_mean": float(np.mean(rows["pre_change"])),
            "parallel_coef_mean": mv(rows["coef"]), "frac_parallel_coef_le_minus1": float(np.mean(rows["coef"][v] <= -1)) if v.any() else float("nan"),
            "angle_deg_mean": mv(rows["angle_deg"]), "angle_deg_p90": q(rows["angle_deg"], 90), "relative_residual_norm_p90": q(rows["rel_norm"], 90)}


# ================================================================================================ per-query scoring (= ev1._metrics)
def query_ranks(Sc, own):
    """Rank of the true candidate per query, exactly as auditory_alignment.evaluate._metrics (position in argsort(-s))."""
    Sc = np.asarray(Sc); own = np.asarray(own, int)
    order = np.argsort(-Sc, axis=1)
    inv = np.empty_like(order)
    inv[np.arange(len(Sc))[:, None], order] = np.arange(Sc.shape[1])[None]
    return inv[np.arange(len(Sc)), own]


def query_logloss_bits(Sc, own, tau):
    """Per-query candidate cross-entropy in bits, in the score's own dtype exactly as ev1._metrics."""
    z = np.asarray(Sc) / tau
    z = z - z.max(1, keepdims=True)
    return (np.log(np.exp(z).sum(1)) - z[np.arange(len(z)), np.asarray(own, int)]) / np.log(2.0)


def metrics_from_queries(rank, ll, n_cand):
    rank = np.asarray(rank)
    return {"top1": float((rank == 0).mean()), "top5": float((rank < 5).mean()), "mrr": float((1 / (rank + 1)).mean()),
            "rank_pct": float((rank / max(1, n_cand - 1)).mean()), "logloss_bits": float(np.mean(ll))}


def rank_change(rank_b, rank_c, ll_b, ll_c, ts_b, ts_c, tz_b, tz_c):
    """Layer 3 per identity (candidate minus base; d_logloss = base - candidate, positive = candidate better)."""
    rb, rc = np.asarray(rank_b), np.asarray(rank_c)
    d = rc - rb
    return {"d_logloss": float(np.mean(np.asarray(ll_b) - np.asarray(ll_c))), "frac_rank_changed": float(np.mean(d != 0)),
            "mean_drank": float(np.mean(d)), "mean_abs_drank": float(np.mean(np.abs(d))),
            "top1_gain": float(np.mean((rb > 0) & (rc == 0))), "top1_loss": float(np.mean((rb == 0) & (rc > 0))),
            "d_true_score": float(np.mean(np.asarray(ts_c) - np.asarray(ts_b))), "d_true_z": float(np.mean(np.asarray(tz_c) - np.asarray(tz_b)))}


def true_scores(Sc, own):
    Sc = np.asarray(Sc, np.float64); own = np.asarray(own, int); ix = np.arange(len(Sc))
    t = Sc[ix, own]
    z = (t - Sc.mean(1)) / (Sc.std(1) + 1e-12)
    return t, z


# ================================================================================================ rows and records
def all_rows():
    from auditory_alignment_v3 import run as r3
    return r3.all_rows()


def loader(out=None):
    out = out or core.OUT
    cache = {}

    def load(eid):
        if eid not in cache:
            p = os.path.join(out, "units", f"{eid}.json")
            cache[eid] = json.load(open(p)) if os.path.exists(p) else None
        return cache[eid]
    load.cache = cache
    return load


def rs_key(row):
    """Configuration key of an RS row (equals complement_function.ckey(cfg34(row)))."""
    s = row["spec"]
    return "|".join(("RS", row["dataset"], s["objective"], s["architecture"], s["variant"]))


# ================================================================================================ per-unit evaluator (forward passes)
class Limits:
    def __init__(self, tiny=False, max_test_participants=None, max_queries=None, max_readout_segs=400, max_calib_queries=300, max_dev_segments=300):
        self.tiny = tiny
        self.max_test_participants, self.max_queries = max_test_participants, max_queries
        self.max_readout_segs, self.max_calib_queries, self.max_dev_segments = max_readout_segs, max_calib_queries, max_dev_segments
        if tiny:
            self.max_test_participants = self.max_test_participants or 2
            self.max_queries = self.max_queries or 4
            self.max_readout_segs, self.max_calib_queries, self.max_dev_segments = min(max_readout_segs, 24), min(max_calib_queries, 16), min(max_dev_segments, 16)

    def comparable(self):
        return not self.tiny and self.max_test_participants is None and self.max_queries is None and self.max_readout_segs == 400 \
            and self.max_calib_queries == 300 and self.max_dev_segments == 300

    def as_dict(self):
        return dict(vars(self))


def build_unit(eid, device="cuda", rows=None, load=None):
    """Rebuild one RS unit exactly as residual32.fit_residual built it (no training): cohort, batcher, frozen base encoder and
    fixed audio head from the base checkpoint, context branch (random backbone regenerated from the seed), selected-epoch
    weights from the unit checkpoint."""
    import torch
    from auditory_alignment_v2.audio_targets import build_head, target_stats
    from auditory_alignment_v2.foundation_adapter import Backbone
    from auditory_alignment_v2.run import load_cohort
    from auditory_alignment_v2.temporal import build_encoder
    from auditory_alignment_v3 import residual32 as R32
    from auditory_alignment_v3.local_train import GridBatcher
    rows = rows or all_rows(); load = load or loader()
    row = next(r for r in rows if r["experiment_id"] == eid)
    if row["family_id"] != "ALN32_RESIDUAL":
        raise ValueError(f"{eid} is {row['family_id']}, not ALN32_RESIDUAL")
    rec = load(eid)
    if not rec or rec.get("status") != "complete":
        raise ValueError(f"{eid}: record not complete")
    br = R32.base_ready(row, rows)
    if br is None or br[0]["experiment_id"] != rec["dependency"]["base"]:
        raise ValueError(f"{eid}: base dependency not available / differs from the record")
    s = row["spec"]; b = core.bind(row); dev = torch.device(device); d = int(s.get("projection_dim", 32))
    coh = load_cohort(b); g = core.grid_samples(coh.fs)
    bt = GridBatcher(coh, {**b["spec"], "architecture": "lag_local_tokens", "window": "full"}, b, dev, g)
    pre, post = int(round(R32.PRE_S * coh.fs)), int(bt.W[0][1]); rw = R32.Rows(bt, pre, post)
    if [-pre, post] != list(rec["window_samples"]):
        raise ValueError(f"{eid}: window {[-pre, post]} != record {rec['window_samples']}")
    enc = build_encoder("lag_local_tokens", coh.n_ch, d, bt.W, coh.fs).to(dev)
    sd = torch.load(br[2], map_location=dev)
    enc.load_state_dict(sd["enc"], strict=True); enc.eval()
    head = build_head("fixed_features", bt.audio_dim, d, coh.meta["dataset"], target_stats(bt, np.random.default_rng(row["seed"] + 5))).to(dev)
    head.load_state_dict(sd["head"], strict=True); head.eval()
    torch.manual_seed(row["seed"])  # residual32.fit_residual: the context branch is the first random draw after this seed
    if s["variant"] == "residual_small_capacity":
        ctx = R32.SmallContext(coh.n_ch)
    else:
        bb = Backbone(s["architecture"], coh.meta["dataset"], "pretrained_frozen" if s["variant"] == "residual_aligned_pretrained" else "random_full", coh.fs)
        ctx = R32.FMContext(bb)
    model = R32.ResidualModel(enc, ctx, d).to(dev); model.eval()
    st = torch.load(os.path.join(core.OUT, "ckpt", eid + "_best.pt"), map_location=dev)["model"]
    res = model.load_state_dict(st, strict=False)
    if res.unexpected_keys or any(not k.startswith(("enc.", "ctx.bb.")) for k in res.missing_keys):
        raise ValueError(f"{eid}: checkpoint keys do not match the model ({res.unexpected_keys[:3]}, {[k for k in res.missing_keys if not k.startswith(('enc.', 'ctx.bb.'))][:3]})")
    model.eval()
    return {"row": row, "rec": rec, "base_eid": br[0]["experiment_id"], "base_rec": load(br[0]["experiment_id"]), "b": b, "coh": coh, "bt": bt,
            "rw": rw, "enc": enc, "head": head, "model": model, "grid": g, "dev": dev, "d": d}


class SplitReps:
    """Per-anchor (u_base, r, u = normalise(u_base + r)) of an RS model on the evaluation grid; one forward per segment, cached.
    view('base') / view('rs') expose the ev1.Reps interface (u(e0s) -> [n, T, d]); va() is the shared audio side."""

    def __init__(self, model, rw, bt, head, stride, chunk=8):
        from auditory_alignment import evaluate as ev1
        self.model, self.rw, self.bt, self.chunk = model, rw, bt, chunk
        self.offs = np.arange(0, bt.seg_len, stride); self.cache = {}; self.forward_check = None
        self._va = ev1.Reps(None, head, bt, stride=stride)

    def _compute(self, e0s):
        import torch
        import torch.nn.functional as F
        todo = [int(e) for e in e0s if int(e) not in self.cache]
        q = torch.tensor(self.offs, device=self.bt.dev)
        with torch.no_grad():
            for k in range(0, len(todo), self.chunk):
                e0 = torch.tensor(todo[k:k + self.chunk], device=self.bt.dev)
                e = (e0[:, None] + q[None]).reshape(-1)
                P, W = self.bt.patches(e), self.rw.windows(e)
                ub = self.model.enc(P); tok = self.model.enc.forward_tokens(P).flatten(1)
                r = self.model.res.residual(torch.cat((tok, self.model.ctx(W)), -1))
                u = F.normalize(ub + r, dim=-1)
                if self.forward_check is None:  # the decomposition equals the trained forward pass (ResidualModel.forward)
                    self.forward_check = float((self.model(P, W) - u).abs().max())
                T = len(self.offs)
                for j, s0 in enumerate(todo[k:k + self.chunk]):
                    sl = slice(j * T, (j + 1) * T)
                    self.cache[s0] = (ub[sl].float().cpu().numpy(), r[sl].float().cpu().numpy(), u[sl].float().cpu().numpy())

    def triplets(self, e0s):
        self._compute(e0s)
        return tuple(np.stack([self.cache[int(e)][i] for e in e0s]) for i in range(3))

    def view(self, which):
        ix = {"base": 0, "rs": 2}[which]
        outer = self

        class _View:
            def u(self, e0s):
                outer._compute(e0s)
                return np.stack([outer.cache[int(e)][ix] for e in e0s])

            def va(self, s0s):
                return outer._va.va(s0s)
        return _View()

    def va(self, s0s):
        return self._va.va(s0s)


def _pool_of(segs, role, k):
    uids, rows_ = {}, []
    for s in segs:
        if s["role"] == role and s["kind"] == k and s["uid"] not in uids:
            uids[s["uid"]] = len(rows_); rows_.append(s)
    return uids, rows_


def per_query_eval(objective, views, va_reps, bt, coh, subject_fold, seed, limits=None):
    """auditory_alignment.evaluate.evaluate_continuous (regular retrieval) for several representations of the same queries:
    identical readout / calibration sampling per view (rng seed + 1000), per-query scores, ranks and log-losses.
    -> {pid: {view: {readout: {...}}}, 'own', 'e0'}, {view: Readouts}"""
    from auditory_alignment import evaluate as ev1
    limits = limits or Limits()
    segs = coh.segments; kind = "ss"
    train_segs = [s for s in segs if s["p"] in bt.train_p and s["role"] in ("fit", "es") and s["kind"] == bt.kind]
    es_uid, es_rows = _pool_of(segs, "es", kind)
    q_all = [s for s in segs if s["p"] in bt.train_p and s["role"] == "es" and s["kind"] == kind]
    ros = {}
    es_va = None
    for name, reps in views.items():
        rng = np.random.default_rng(seed + 1000)
        ro = ev1.Readouts(objective, reps, train_segs, rng, n_seg=limits.max_readout_segs)
        q_es = [q_all[i] for i in rng.choice(len(q_all), size=min(limits.max_calib_queries, len(q_all)), replace=False)] if q_all else []
        if q_es and len(es_rows) > 1:
            if es_va is None:
                es_va = va_reps.va([r["s0"] for r in es_rows])
            Vc, Ac = es_va
            Uq = reps.u([s["e0"] for s in q_es]); own = np.array([es_uid[s["uid"]] for s in q_es])
            ro.calibrate({"unified": ro.scores(Uq, Vc, Ac, "unified"), "native": ro.scores(Uq, Vc, Ac, "native")}, own)
        ros[name] = ro
    te_uid, te_rows = _pool_of(segs, "test", kind)
    Vc, Ac = va_reps.va([r["s0"] for r in te_rows])
    test_p = sorted({s["p"] for s in segs if s["role"] == "test" and (coh.participants[s["p"]]["fold"] == subject_fold or coh.participants[s["p"]].get("test_only"))})
    if limits.max_test_participants:
        test_p = test_p[:limits.max_test_participants]
    per = {}
    for p in test_p:
        q = [s for s in segs if s["p"] == p and s["role"] == "test" and s["kind"] == kind]
        if not q:
            continue
        q = [q[i] for i in np.argsort([s["e0"] for s in q])]
        if limits.max_queries:
            q = q[:limits.max_queries]
        own = np.array([te_uid[s["uid"]] for s in q]); e0s = [s["e0"] for s in q]
        rec = {"own": own, "e0": np.array(e0s), "n_candidates": len(te_rows)}
        for name, ro in ros.items():
            Uq = views[name].u(e0s); rv = {}
            for rd in READOUTS:
                Sc = ro.scores(Uq, Vc, Ac, rd)
                rank, ll = query_ranks(Sc, own), query_logloss_bits(Sc, own, ro.tau[rd])
                ts, tz = true_scores(Sc, own)
                rv[rd] = {"S": Sc, "rank": rank, "ll": ll, "true": ts, "true_z": tz, "metrics": metrics_from_queries(rank, ll, len(te_rows))}
            rv["P_uni"] = ev1._apply(ro.B_uni, Uq.reshape(-1, Uq.shape[-1])).reshape(Uq.shape[0], Uq.shape[1], -1)
            if objective in ("CS_SINGLE", "CS_MULTI"):
                rv["P_nat"] = ev1._apply(ro.B_nat, Uq.reshape(-1, Uq.shape[-1])).reshape(Uq.shape[0], Uq.shape[1], -1)
            rec[name] = rv
        per[coh.participants[p]["id"]] = rec
    return per, ros


def _zcorr(A, B):
    """mean over target dimensions of the per-segment correlation over anchors (the unified score z-scores over anchors)."""
    Az = (A - A.mean(1, keepdims=True)) / (A.std(1, keepdims=True) + 1e-12)
    Bz = (B - B.mean(1, keepdims=True)) / (B.std(1, keepdims=True) + 1e-12)
    return (Az * Bz).mean(1).mean(-1)


def layer_rows_for(spl, e0s):
    ub, r, _ = spl.triplets(e0s)
    n, T, d = ub.shape
    rows = residual_rows(ub.reshape(-1, d), r.reshape(-1, d))
    return rows, n, T


def _runtime(dev):
    import torch
    out = {"host": socket.gethostname(), "slurm_job": os.environ.get("SLURM_JOB_ID", "local"), "pid": os.getpid(),
           "process_peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)}  # Linux: kB; max over the process lifetime
    if dev.type == "cuda":
        out["gpu_peak_allocated_mb"] = round(torch.cuda.max_memory_allocated() / 2 ** 20)
        out["gpu_peak_reserved_mb"] = round(torch.cuda.max_memory_reserved() / 2 ** 20)
    return out


def evaluate_unit(eid, device="cuda", limits=None, dev_only=False, out_dir=UNITS_DIR, rows=None, load=None, write=True):
    """Layers 1-3 on the outer-test queries (both views under one readout contract, reproduction check against the saved records)
    and layers 1-2 + development risks (epoch 0 and the selected epoch, reproduction check against the saved curve) on the
    development queries. Writes <out_dir>/<eid>.json (+ _queries.npz)."""
    import torch
    from auditory_alignment_v2 import evaluate as ev2
    from auditory_alignment_v3 import residual32 as R32
    limits = limits or Limits()
    t0 = time.time()
    if str(device).startswith("cuda"):
        torch.cuda.reset_peak_memory_stats()
    snap = snapshot_code(os.path.join(os.path.dirname(os.path.abspath(out_dir)), "code_snapshots")) if write else None
    U = build_unit(eid, device, rows, load)
    row, rec, bt, rw, head, model, g, coh = U["row"], U["rec"], U["bt"], U["rw"], U["head"], U["model"], U["grid"], U["coh"]
    t_build = time.time() - t0
    ref = reference_residuals()
    out = {"eid": eid, "cfg": rs_key(row), "base": U["base_eid"], "row": row, "selected_epoch": rec["selected_epoch"], "epoch0_selected": rec.get("epoch0_selected"),
           "limits": limits.as_dict(), "comparable_to_record": limits.comparable(), "dev_only": dev_only, "device": str(U["dev"]),
           "device_name": torch.cuda.get_device_name(0) if U["dev"].type == "cuda" else "cpu", "torch": torch.__version__, "torch_threads": torch.get_num_threads(),
           "code_sha256": code_versions(), "code_snapshot": snap, "output_version": "v2", "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0)),
           "build_seconds": round(t_build, 1)}
    W2 = model.res.residual[2].weight
    out["checkpoint_zero_last_layer"] = bool((W2 == 0).all() and (model.res.residual[2].bias == 0).all())
    spl = SplitReps(model, rw, bt, head, g)
    # ---------------------------------------------------------------- development side (residual32.fit_residual sampling)
    grp = R32.groups_of(bt)
    tr_es = [i for i in bt.es if grp[bt.coh_segments[i]["p"]] != R32.DEV_GROUP]
    dv = [i for i in list(bt.fit) + list(bt.es) if grp[bt.coh_segments[i]["p"]] == R32.DEV_GROUP]
    rng_d = np.random.default_rng(R32.GROUP_SEED + 1)
    dv = sorted(rng_d.choice(dv, size=min(300, len(dv)), replace=False).tolist()); cal = sorted(rng_d.choice(tr_es, size=min(300, len(tr_es)), replace=False).tolist())
    dv, cal = dv[:limits.max_dev_segments], cal[:limits.max_dev_segments]
    step_ = max(g, (bt.seg_len // R32.Q) // g * g); offs = torch.arange(R32.Q, device=bt.dev) * step_
    t1 = time.time()
    dr_sel = R32.dev_risk(model, bt, rw, head, dv, dv, cal, offs)
    saved = {n_: p.detach().clone() for n_, p in model.res.residual[2].named_parameters()}
    with torch.no_grad():
        for p in model.res.residual[2].parameters():
            p.zero_()
        e0_ = torch.tensor([bt.coh_segments[i]["e0"] for i in dv[:4]], device=bt.dev); e_ = (e0_[:, None] + offs[None]).reshape(-1)
        u0 = model(bt.patches(e_), rw.windows(e_)); ub0 = model.enc(bt.patches(e_))
        epoch0_vs_base = float((u0 - ub0).abs().max())
        dr_0 = R32.dev_risk(model, bt, rw, head, dv, dv, cal, offs)
        for n_, p in model.res.residual[2].named_parameters():
            p.copy_(saved[n_])
    curve = {c["epoch"]: c for c in rec["curve"]}
    out["dev"] = {"n_dev_segments": len(dv), "n_cal_segments": len(cal), "anchors_per_segment": int(R32.Q),
                  "selected": {"risk_bits": dr_sel[0], "rank": dr_sel[1], "tau": dr_sel[2], "record_risk_bits": rec["selected_dev_risk_bits"],
                               "abs_diff": abs(dr_sel[0] - rec["selected_dev_risk_bits"])},
                  "epoch0": {"risk_bits": dr_0[0], "rank": dr_0[1], "tau": dr_0[2], "record_risk_bits": curve[0]["dev_risk_bits"], "abs_diff": abs(dr_0[0] - curve[0]["dev_risk_bits"])},
                  "epoch0_max_abs_diff_vs_base": epoch0_vs_base, "epoch0_check_where": f"{min(4, len(dv))} development segments x {R32.Q} anchors, last layer zeroed",
                  "seconds": round(time.time() - t1, 1)}
    dev_e0 = [int(bt.coh_segments[i]["e0"] + o) for i in dv for o in offs.cpu().numpy()]
    # dev anchors are single anchors at e0 + offs (a subset of the evaluation grid): compute them as one-anchor 'segments'
    dsp = SplitReps(model, rw, bt, head, stride=bt.seg_len, chunk=256)  # offs = [0] -> one anchor per e0
    ub_d, r_d, _ = dsp.triplets(dev_e0)
    out["dev"]["layers"] = residual_summary(residual_rows(ub_d[:, 0], r_d[:, 0]))
    out["dev"]["layers_reference"] = ref.residual_diagnostics(ub_d[:, 0], r_d[:, 0])
    out["dev"]["forward_check"] = dsp.forward_check
    del dsp, ub_d, r_d
    if dev_only:
        out["seconds"] = round(time.time() - t0, 1); out["runtime"] = _runtime(U["dev"])
        return _write_unit(out, None, out_dir) if write else out
    # ---------------------------------------------------------------- outer test (one readout contract for both views)
    t2 = time.time()
    obj = ev2.READOUT_OBJ[row["spec"]["objective"]]
    views = {"base": spl.view("base"), "rs": spl.view("rs")}
    per, ros = per_query_eval(obj, views, spl, bt, coh, row["subject_fold"], row["seed"], limits)
    out["readout"] = {v: {"alpha_unified": ro.alpha_uni, "tau": ro.tau} for v, ro in ros.items()}
    repro = {"base": defaultdict(float), "rs": defaultdict(float)}; ids = {}
    Q = defaultdict(list); per_id = {}
    for pid, pr in per.items():
        e0s = list(pr["e0"])
        lrows, n, T = layer_rows_for(spl, e0s)
        lay = {k: float(np.mean(lrows[k][lrows["valid"]])) for k in LAYER12}
        lay["pre_change"] = float(np.mean(lrows["pre_change"]))
        qm = {k: lrows[k].reshape(n, T).mean(1) for k in LAYER12}
        L3 = {}
        for rd in READOUTS:
            a, c = pr["base"][rd], pr["rs"][rd]
            L3[rd] = rank_change(a["rank"], c["rank"], a["ll"], c["ll"], a["true"], c["true"], a["true_z"], c["true_z"])
            for v, recx in (("base", U["base_rec"]), ("rs", rec)):
                sv = recx["eval"]["per_participant"].get(pid, {}).get(f"{rd}/regular")
                if sv is not None:
                    for m in QMETRICS:
                        repro[v][f"{rd}/{m}"] = max(repro[v][f"{rd}/{m}"], abs(pr[v][rd]["metrics"][m] - sv[m]))
                else:
                    ids.setdefault(v, []).append(pid)
        Pb, Pr = pr["base"]["P_uni"], pr["rs"]["P_uni"]
        uni_rel = (np.linalg.norm(Pr - Pb, axis=-1) / (np.linalg.norm(Pb, axis=-1) + 1e-12)).mean(1)
        uni_corr = _zcorr(Pb, Pr)
        L3["unified_prediction"] = {"rel_diff": float(uni_rel.mean()), "zcorr": float(uni_corr.mean())}
        if "P_nat" in pr["base"]:
            Nb, Nr = pr["base"]["P_nat"], pr["rs"]["P_nat"]
            L3["native_prediction"] = {"rel_diff": float((np.linalg.norm(Nr - Nb, axis=-1) / (np.linalg.norm(Nb, axis=-1) + 1e-12)).mean())}
        else:  # NCE: the scored native sound prediction is u itself
            L3["native_prediction"] = {"rel_diff": lay["post_change"]}
        per_id[pid] = {"n_queries": int(n), "anchors_per_query": int(T), "layers": lay, "layer3": L3}
        Q["pid"] += [pid] * n; Q["e0"].append(pr["e0"]); Q["own"].append(pr["own"])
        for rd in READOUTS:
            for v in ("base", "rs"):
                Q[f"rank_{v}_{rd}"].append(pr[v][rd]["rank"]); Q[f"ll_{v}_{rd}"].append(pr[v][rd]["ll"]); Q[f"true_{v}_{rd}"].append(pr[v][rd]["true"])
        for k in LAYER12:
            Q[f"q_{k}"].append(qm[k])
        Q["q_uni_pred_rel_diff"].append(uni_rel); Q["q_uni_pred_zcorr"].append(uni_corr)
    out["per_identity"] = per_id
    allrows, _, _ = layer_rows_for(spl, [int(e) for pr in per.values() for e in pr["e0"]])
    out["test_layers"] = residual_summary(allrows)
    ub_all = np.concatenate([spl.cache[int(e)][0] for pr in per.values() for e in pr["e0"]]); r_all = np.concatenate([spl.cache[int(e)][1] for pr in per.values() for e in pr["e0"]])
    out["test_layers_reference"] = ref.residual_diagnostics(ub_all, r_all)
    out["forward_check"] = spl.forward_check
    out["reproduction"] = {"base_record": dict(repro["base"]), "rs_record": dict(repro["rs"]), "participants_missing_in_record": ids,
                           "max_abs": {v: max(repro[v].values()) if repro[v] else None for v in repro}}
    out["reproduction"]["rule"] = f"max |Δ| <= {REPRO_TOL} on {', '.join(REPRO_KEYS)} vs both records and on both saved dev risks"
    out["reproduction"]["within_tolerance"] = reproduces(out)
    out["test_seconds"] = round(time.time() - t2, 1); out["seconds"] = round(time.time() - t0, 1)
    out["runtime"] = _runtime(U["dev"])
    if U["dev"].type == "cuda":
        out["gpu_peak_allocated_mb"] = out["runtime"]["gpu_peak_allocated_mb"]
    qarr = {k: (np.concatenate(v) if k != "pid" else np.array(v)) for k, v in Q.items()}
    return _write_unit(out, qarr, out_dir) if write else (out, qarr)


# ================================================================================================ output files
def _jl(x):
    if isinstance(x, dict):
        return {str(k): _jl(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jl(v) for v in x]
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, (np.floating, np.integer, np.bool_)):
        return x.item()
    return x


def _write_json(path, obj):
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    tmp = f"{path}.tmp{os.getpid()}"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(_jl(obj), f, indent=1, default=float)
    os.chmod(tmp, 0o600); os.replace(tmp, path)
    return path


def _write_unit(out, qarr, out_dir):
    tag = "" if out["comparable_to_record"] and not out["dev_only"] else (".dev_only" if out["dev_only"] else ".tiny")
    if qarr is not None:
        p = os.path.join(out_dir, f"{out['eid']}{tag}_queries.npz")
        os.makedirs(out_dir, mode=0o700, exist_ok=True)
        tmp = f"{p}.tmp{os.getpid()}.npz"
        np.savez_compressed(tmp, **qarr); os.chmod(tmp, 0o600); os.replace(tmp, p)
        out["queries_file"] = os.path.relpath(p, REPO)
    return _write_json(os.path.join(out_dir, f"{out['eid']}{tag}.json"), out)
