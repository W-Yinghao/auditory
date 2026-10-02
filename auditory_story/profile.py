"""P1 (02_SERVER_EXECUTION section 5; 03_METHOD_SPEC sections 2-6): per outer unit (seed, fold)

  1. child x class-equal standardisation + whitened PCA-32 of the frozen M_o trial embeddings (training pool only),
     history scaling and the frozen population model q0 (FP64);
  2. the conditional and pooled summary arms, 3000 fixed Adam steps each, episodes of 4 training children x
     (32 support + 32 query) per class from physically disjoint 60-s block groups, direction alternating every step;
     same initial weights and episode stream for both arms; checkpoints every 100 steps (model, optimiser, RNG,
     sampler state) and SIGUSR1/SIGTERM-safe exit;
  3. label-free outputs of the fixed step-3000 model: all-trial clinical summaries (exact streaming phi means,
     classes weighted 1/2), split-half summaries for E5 and E3 query predictions on the outer-test children.

No clinical value is passed to anything in this module.
"""
from __future__ import annotations

import json
import math
import signal

import numpy as np

from . import transform as tf
from .runtime import ProvenanceError, mark_done, save_npz_atomic, stable_int, torch_save_atomic, unit_done, write_json_atomic

STOP = {"flag": False, "signal": None}


def _handler(signum, _frame):
    STOP["flag"], STOP["signal"] = True, int(signum)


def install_signal_handlers() -> None:
    signal.signal(signal.SIGUSR1, _handler)
    signal.signal(signal.SIGTERM, _handler)


class Preempted(RuntimeError):
    pass


class NumericalFailure(RuntimeError):
    pass


# ---------------------------------------------------------------------- episode sampling

class EpisodeSampler:
    """cells[child][(group, cls)] -> guard-respecting row indices. Direction d = step % 2: support from group d,
    query from group 1 - d. Children sampled uniformly without replacement; trials without replacement."""

    def __init__(self, cells: dict, eligible: list[int], per_class: int, children_per_batch: int, seed: int):
        if not eligible:
            raise ProvenanceError("NO_EPISODE_ELIGIBLE_TRAINING_CHILD")
        self.cells, self.eligible = cells, sorted(int(c) for c in eligible)
        self.per_class, self.batch = int(per_class), min(int(children_per_batch), len(self.eligible))
        self.rng = np.random.default_rng(seed % (2 ** 63))

    def sample(self, step: int):
        d = step % 2
        kids = self.rng.choice(self.eligible, size=self.batch, replace=False)
        sup = np.zeros((self.batch, 2, self.per_class), np.int64)
        qry = np.zeros((self.batch, 2 * self.per_class), np.int64)
        for b, c in enumerate(kids):
            for k in (0, 1):
                sup[b, k] = self.rng.choice(self.cells[int(c)][(d, k)], self.per_class, replace=False)
                qry[b, k * self.per_class:(k + 1) * self.per_class] = self.rng.choice(self.cells[int(c)][(1 - d, k)],
                                                                                      self.per_class, replace=False)
        qcond = np.repeat(np.array([0, 1]), self.per_class)[None, :].repeat(self.batch, 0)
        return kids, sup, qry, qcond, d

    def state(self) -> dict:
        return self.rng.bit_generator.state

    def set_state(self, state: dict) -> None:
        self.rng.bit_generator.state = state


def cells_of(tt, children) -> dict:
    out = {}
    g = tt[tt.guard_ok & tt.child.isin(children)]
    for c in children:
        sub = g[g.child == c]
        out[int(c)] = {(int(gr), int(k)): sub.index[(sub.group == gr) & (sub.cls == k)].to_numpy(np.int64)
                       for gr in (0, 1) for k in (0, 1)}
    return out


# ---------------------------------------------------------------------- unit preparation (label-free transforms)

def prepare_unit(src, config: dict, seed: int, fold: int) -> dict:
    tt = src.trial_table
    train, test = src.split(seed, fold)
    if set(train) & set(test):
        raise ProvenanceError("OUTER_SCOPES_OVERLAP")
    emb = src.embeddings(seed, fold)
    tr = tt.child.isin(train).to_numpy()
    child, cls = tt.child.to_numpy(), tt.cls.to_numpy()
    sample = np.flatnonzero(tr)[tf.pca_sample(child[tr], cls[tr], int(config["inputs"]["pca_fit_trials_per_child_per_class_max"]),
                                              int(config["inputs"]["pca_seed"]))]
    if set(child[sample]) & set(test):
        raise ProvenanceError("PCA_SAMPLE_CONTAINS_TEST_CHILD")
    proj = tf.fit_projection(emb[sample], child[sample], cls[sample], int(config["inputs"]["projected_dim_max"]),
                             whiten=bool(config["inputs"]["transform_whiten"]))
    e = tf.apply_projection(proj, emb)
    h_raw = tt[["h_run", "h_gap", "h_pos"]].to_numpy(np.float64)
    hs = tf.fit_history(h_raw[tr], child[tr], cls[tr])
    h = tf.apply_history(hs, h_raw)
    pop = tf.fit_population(e[tr], h[tr], cls[tr], child[tr], alpha=float(config["profile"]["population_ridge_weighted_mean_alpha"]),
                            logvar_bounds=tuple(config["profile"]["population_logvar_bounds"]))
    kids = src.children
    cm = np.full((len(kids), 2, e.shape[1]), np.nan, np.float64)            # all accepted trials, per class
    split = np.full((len(kids), 2, 2, e.shape[1]), np.nan, np.float64)      # group x class, guard-respecting trials
    for i, c in enumerate(kids):
        m = child == c
        for k in (0, 1):
            cm[i, k] = e[m & (cls == k)].astype(np.float64).mean(0)
            for g in (0, 1):
                mm = m & (cls == k) & tt.guard_ok.to_numpy() & (tt.group.to_numpy() == g)
                if mm.any():
                    split[i, g, k] = e[mm].astype(np.float64).mean(0)
    # C_MEAN8: PCA-8 of the training-pool-standardised 64-d per-child class means (training children only, no labels)
    flat = cm.reshape(len(kids), -1)
    trk = np.array([c in set(train) for c in kids])
    mu_, sd_ = flat[trk].mean(0), flat[trk].std(0)
    sd_ = np.where(sd_ < 1e-12, 1.0, sd_)
    Z = (flat - mu_) / sd_
    _, _, Vt = np.linalg.svd(Z[trk] - Z[trk].mean(0), full_matrices=False)
    V8 = Vt[:8].T.copy()
    sign = np.sign(V8[np.argmax(np.abs(V8), 0), np.arange(V8.shape[1])])
    V8 *= np.where(sign == 0, 1.0, sign)
    mean8 = (Z - Z[trk].mean(0)) @ V8
    return {"train": train, "test": test, "e": e, "h": h, "proj": proj, "hist": hs, "pop": pop, "class_means": cm,
            "split_class_means": split, "mean8": mean8}


def save_transforms(path, U: dict, children: list[int]) -> None:
    p, hs, pop = U["proj"], U["hist"], U["pop"]
    save_npz_atomic(path, children=np.asarray(children), train=np.asarray(U["train"]), test=np.asarray(U["test"]),
                    proj_mean=p["mean"], proj_sd=p["sd"], proj_components=p["components"], proj_scale=p["scale"],
                    proj_rank=np.int64(p["rank"]), proj_dim=np.int64(p["dim"]), proj_explained=np.float64(p["explained"]),
                    hist_median=hs["median"], hist_mean=hs["mean"], hist_sd=hs["sd"], hist_missing=hs["missing_counts"],
                    pop_coefficients=pop["coefficients"], pop_logvar=pop["logvar"],
                    class_means=U["class_means"], split_class_means=U["split_class_means"], mean8=U["mean8"])


# ---------------------------------------------------------------------- model construction and training

def build_model(pop: dict, config: dict, arm: str, init_seed: int):
    import torch
    from .srp import PopulationResponse, ResponseProfile
    population = PopulationResponse(torch.as_tensor(pop["coefficients"], dtype=torch.float32),
                                    torch.as_tensor(pop["logvar"], dtype=torch.float32))
    torch.manual_seed(init_seed % (2 ** 31))
    pr = config["profile"]
    return ResponseProfile(population, latent_dim=int(pr["latent_dim"]), hidden=int(pr["phi_hidden"]),
                           phi_dim=int(pr["phi_output"]), conditioned=(arm == "conditional"))


def train_arm(model, e, h, sampler: EpisodeSampler, config: dict, ckpt_path, train_seed: int) -> dict:
    import torch
    from .srp import balanced_profile_loss
    pr = config["profile"]
    steps, every = int(pr["steps"]), int(pr["checkpoint_every_steps"])
    beta, clip = float(pr["beta_kl_per_latent_dimension"]), float(pr["gradient_clip"])
    opt = torch.optim.Adam(model.parameters(), lr=float(pr["learning_rate"]))
    E, Hh = torch.as_tensor(e), torch.as_tensor(h)
    start, diag, window, initial_loss = 0, [], [], None
    if ckpt_path.exists():
        ck = torch.load(ckpt_path, map_location="cpu", weights_only=False)
        model.load_state_dict(ck["model"])
        opt.load_state_dict(ck["opt"])
        torch.set_rng_state(ck["torch_rng"])
        sampler.set_state(ck["sampler"])
        start, diag, initial_loss = int(ck["step"]), list(ck["diag"]), ck["initial_loss"]
    else:
        torch.manual_seed(train_seed % (2 ** 31))

    def save(step):
        torch_save_atomic({"step": step, "model": model.state_dict(), "opt": opt.state_dict(),
                           "torch_rng": torch.get_rng_state(), "sampler": sampler.state(), "diag": diag,
                           "initial_loss": initial_loss}, ckpt_path)

    for step in range(start, steps):
        model.train()
        kids, sup, qry, qcond, d = sampler.sample(step)
        support = E[torch.as_tensor(sup)]                                   # [B, K, T, D]
        mask = torch.ones(support.shape[:3], dtype=torch.bool)
        q = torch.as_tensor(qry)
        qc = torch.as_tensor(qcond, dtype=torch.long)
        out = model(support, mask, qc, Hh[q])
        losses = balanced_profile_loss(E[q], out, qc, 2, beta=beta)
        opt.zero_grad(set_to_none=True)
        losses["loss"].backward()
        gn = float(torch.nn.utils.clip_grad_norm_(model.parameters(), clip))
        lv = float(losses["loss"])
        if not (math.isfinite(lv) and math.isfinite(gn)):
            save(step)
            raise NumericalFailure(f"NONFINITE_AT_STEP_{step}")
        opt.step()
        if initial_loss is None:
            initial_loss = lv
        window.append((lv, float(losses["nll_per_dimension"]), float(losses["kl_per_latent_dimension"]), gn,
                       float(out.latent_mean.norm(dim=1).mean())))
        if (step + 1) % every == 0 or step + 1 == steps:
            w = np.array(window)
            diag.append({"step": step + 1, "loss": float(w[:, 0].mean()), "query_nll_per_dim": float(w[:, 1].mean()),
                         "kl_per_latent_dim": float(w[:, 2].mean()), "grad_norm_preclip": float(w[:, 3].mean()),
                         "grad_norm_preclip_max": float(w[:, 3].max()), "mu_norm": float(w[:, 4].mean()),
                         "last_loss": lv, "model_training_mode": bool(model.training), "lr": float(opt.param_groups[0]["lr"]),
                         "direction_last": int(d)})
            window = []
            save(step + 1)
        if STOP["flag"]:
            save(step + 1)
            raise Preempted(f"SIGNAL_{STOP['signal']}_AT_STEP_{step + 1}")
    return {"initial_loss": initial_loss, "final_loss": diag[-1]["last_loss"] if diag else None, "diag": diag,
            "steps": steps, "resumed_from": start}


# ---------------------------------------------------------------------- label-free outputs of the fixed model

def summaries(model, e: np.ndarray, tt, children: list[int]) -> dict:
    import torch
    from .srp import condition_phi_means, encode_from_means
    model.eval()
    child, cls = tt.child.to_numpy(), tt.cls.to_numpy()
    guard, group = tt.guard_ok.to_numpy(), tt.group.to_numpy()
    E = torch.as_tensor(e)
    mu = np.zeros((len(children), model.latent_dim))
    lv = np.zeros_like(mu)
    mu_split = np.full((len(children), 2, model.latent_dim), np.nan)
    for i, c in enumerate(children):
        m = child == c
        means = condition_phi_means(model, [E[torch.as_tensor(np.flatnonzero(m & (cls == k)))] for k in (0, 1)])
        a, b = encode_from_means(model, means[None])
        mu[i], lv[i] = a[0].numpy(), b[0].numpy()
        for g in (0, 1):
            sel = [np.flatnonzero(m & (cls == k) & guard & (group == g)) for k in (0, 1)]
            if all(s.size for s in sel):
                means = condition_phi_means(model, [E[torch.as_tensor(s)] for s in sel])
                mu_split[i, g] = encode_from_means(model, means[None])[0][0].numpy()
    return {"mu": mu, "logvar": lv, "mu_split": mu_split}


def e3_rows(model, e: np.ndarray, h: np.ndarray, tt, test_children: list[int], config: dict, seed: int, fold: int,
            arm: str) -> list[dict]:
    """Held-out children: support 32/class from one block group builds u, query 32/class from the other is scored
    under q0 (u = 0) and the model (u = mu); both directions. Same trial selection for every arm (seed has no arm)."""
    import torch
    model.eval()
    per = int(config["inputs"]["support_per_class"])
    cells = cells_of(tt, test_children)
    E, Hh = torch.as_tensor(e), torch.as_tensor(h)
    rows = []

    def scores(mean, logvar, target):
        nll = 0.5 * (math.log(2 * math.pi) + logvar + (target - mean) ** 2 * torch.exp(-logvar))
        z2 = (target - mean) ** 2 * torch.exp(-logvar)
        return nll.mean(-1), ((target - mean) ** 2).mean(-1), z2.mean(-1)

    with torch.no_grad():
        for c in test_children:
            for d in (0, 1):
                ok = all(cells[c][(g, k)].size >= per for g in (0, 1) for k in (0, 1))
                if not ok:
                    rows.append({"child": int(c), "direction": d, "arm": arm, "supported": False})
                    continue
                rng = np.random.default_rng(stable_int(int(config["inputs"]["evaluation_selection_seed"]), seed, fold, c, d) % (2 ** 63))
                sup = np.stack([rng.choice(cells[c][(d, k)], per, replace=False) for k in (0, 1)])[None]
                qry = np.concatenate([rng.choice(cells[c][(1 - d, k)], per, replace=False) for k in (0, 1)])[None]
                qc = torch.as_tensor(np.repeat(np.array([0, 1]), per)[None, :], dtype=torch.long)
                support = E[torch.as_tensor(sup)]
                mask = torch.ones(support.shape[:3], dtype=torch.bool)
                target = E[torch.as_tensor(qry)]
                qh = Hh[torch.as_tensor(qry)]
                m0, v0 = model.population(qc, qh)
                mu, _ = model.encode(support, mask)
                m1, v1 = model.decode(mu, qc, qh)
                row = {"child": int(c), "direction": d, "arm": arm, "supported": True, "mu_norm": float(mu.norm())}
                for name, (mm, vv) in (("q0", (m0, v0)), ("model", (m1, v1))):
                    nll, se, z2 = scores(mm, vv, target)
                    for k in (0, 1):
                        sel = qc[0] == k
                        row[f"{name}_nll_c{k}"] = float(nll[0, sel].mean())
                        row[f"{name}_mse_c{k}"] = float(se[0, sel].mean())
                        row[f"{name}_z2_c{k}"] = float(z2[0, sel].mean())
                    row[f"{name}_nll"] = 0.5 * (row[f"{name}_nll_c0"] + row[f"{name}_nll_c1"])
                    row[f"{name}_mse"] = 0.5 * (row[f"{name}_mse_c0"] + row[f"{name}_mse_c1"])
                    row[f"{name}_z2"] = 0.5 * (row[f"{name}_z2_c0"] + row[f"{name}_z2_c1"])
                if arm == "conditional":                              # dependence on the known support conditions
                    mu_sw, _ = model.encode(support[:, [1, 0]], mask)
                    m2, v2 = model.decode(mu_sw, qc, qh)
                    nll, _, _ = scores(m2, v2, target)
                    row["swapped_nll"] = float(0.5 * (nll[0, qc[0] == 0].mean() + nll[0, qc[0] == 1].mean()))
                    row["swap_mu_shift"] = float((mu_sw - mu).norm() / max(float(mu.norm()), 1e-12))
                rows.append(row)
    return rows


def run_unit(src, config: dict, seed: int, fold: int, unit_dir) -> dict:
    """All P1 work for one outer unit; each arm is atomic (DONE marker) and resumable from its checkpoint."""
    import torch
    import pandas as pd
    from .runtime import write_parquet_atomic
    torch.set_num_threads(int(config["profile"]["torch_threads"]))
    unit_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    U = prepare_unit(src, config, seed, fold)
    save_transforms(unit_dir / "transforms.npz", U, src.children)
    tt = src.trial_table
    sc = src.support_counts().set_index("child")
    eligible = [c for c in U["train"] if bool(sc.loc[c, "episode_eligible"])]
    cells = cells_of(tt, eligible)
    out = {"seed": seed, "fold": fold, "n_train": len(U["train"]), "n_test": len(U["test"]),
           "episode_eligible_train": len(eligible), "proj_dim": int(U["proj"]["dim"]), "proj_rank": int(U["proj"]["rank"]),
           "proj_explained": U["proj"]["explained"], "population": U["pop"]["info"],
           "history_missing_train": U["hist"]["missing_counts"].tolist(), "arms": {}}
    base = int(config["profile"]["training_seed"])
    for arm in config["profile"]["arms"]:
        adir = unit_dir / arm
        adir.mkdir(mode=0o700, exist_ok=True)
        if unit_done(adir / "DONE.json"):
            out["arms"][arm] = json.loads((adir / "DONE.json").read_text())
            continue
        model = build_model(U["pop"], config, arm, stable_int(base, "init", seed, fold))
        sampler = EpisodeSampler(cells, eligible, int(config["inputs"]["support_per_class"]),
                                 int(config["profile"]["children_per_batch"]), stable_int(base, "episodes", seed, fold))
        info = train_arm(model, U["e"], U["h"], sampler, config, adir / "checkpoint.pt", stable_int(base, "train", seed, fold))
        model.eval()
        z = torch.zeros(1, model.latent_dim)
        qc = torch.zeros(1, 4, dtype=torch.long)
        qh = torch.zeros(1, 4, int(config["profile"]["history_dim"]))
        m_zero, v_zero = model.decode(z, qc, qh)
        p_zero, pv_zero = model.population(qc, qh)
        zero_ok = bool(torch.equal(m_zero, p_zero) and torch.equal(v_zero, pv_zero))
        S = summaries(model, U["e"], tt, src.children)
        rows = e3_rows(model, U["e"], U["h"], tt, U["test"], config, seed, fold, arm)
        torch_save_atomic(model.state_dict(), adir / "final_model.pt")
        save_npz_atomic(adir / "summaries.npz", children=np.asarray(src.children), mu=S["mu"], logvar=S["logvar"],
                        mu_split=S["mu_split"])
        write_parquet_atomic(pd.DataFrame(rows), adir / "e3.parquet")
        write_json_atomic(adir / "diag.json", info, private=True)
        done = {"arm": arm, "initial_loss": info["initial_loss"], "final_loss": info["final_loss"],
                "final_query_nll_per_dim": info["diag"][-1]["query_nll_per_dim"], "final_kl": info["diag"][-1]["kl_per_latent_dim"],
                "final_grad_norm": info["diag"][-1]["grad_norm_preclip"], "steps": info["steps"],
                "resumed_from": info["resumed_from"], "zero_latent_recovers_population": zero_ok,
                "model_training_mode_during_training": all(d["model_training_mode"] for d in info["diag"]),
                "mu_child_sd": float(S["mu"].std(0).mean()), "e3_supported_rows": int(sum(r["supported"] for r in rows))}
        mark_done(adir / "DONE.json", done)
        out["arms"][arm] = done
        print(json.dumps({"unit": f"s{seed}_k{fold}", **done}), flush=True)
    return out
