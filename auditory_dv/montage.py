"""Direction B: reference montage x reliability on the MFF lanes (R0 recommendation S1).

CPU `montages`: 128x128 linear operators on the D1 average-referenced HydroCel-128 data (E1..E128):
  avg (identity), mastoid (linked E57/E100), rest (REST, spherical head model), csd (spherical-spline surface Laplacian).
GPU `montage-lane`: for each (montage, lane) retrain the GX shared EEGNet with the GX1 procedure (5 child folds x 3
seeds, inner validation), store held-out trial logits, child AUCs and odd/even-block split-half reliability.
Changing the reference is a linear re-expression of all channels, not a channel selection.
"""
from __future__ import annotations

import json

import numpy as np

from .runtime import ROOT, cfg, open_run, private_dir, save_npz_atomic, task_units, write_json_atomic

MONTAGES = ("avg", "mastoid", "rest", "csd")
MFF_LANES_B = ("mff_puretone", "mff_bapa", "mff_unknown_event")
CHANNELS = [f"E{i}" for i in range(1, 129)]


def build_montages() -> dict:
    import mne
    mont = mne.channels.make_standard_montage("GSN-HydroCel-128")
    info = mne.create_info(CHANNELS, 250.0, "eeg")
    info.set_montage(mont, on_missing="raise")
    eye = np.eye(128)
    out = {"avg": eye.copy()}
    iL, iR = CHANNELS.index("E57"), CHANNELS.index("E100")
    mast = eye.copy()
    mast[:, iL] -= 0.5
    mast[:, iR] -= 0.5
    out["mastoid"] = mast
    raw = mne.io.RawArray(eye.copy(), info, verbose="ERROR")
    sphere = mne.make_sphere_model("auto", "auto", raw.info, verbose="ERROR")
    src = mne.setup_volume_source_space(sphere=sphere, exclude=30.0, pos=15.0, verbose="ERROR")
    fwd = mne.make_forward_solution(raw.info, trans=None, src=src, bem=sphere, eeg=True, meg=False, verbose="ERROR")
    out["rest"] = raw.copy().set_eeg_reference("REST", forward=fwd, verbose="ERROR").get_data()
    out["csd"] = mne.preprocessing.compute_current_source_density(raw.copy(), verbose="ERROR").get_data()
    # a global gain is irrelevant (every record is rescaled by its median |x| afterwards) but the CSD gain can
    # overflow float16; normalise the MNE-derived operators by their spectral norm
    for k in ("rest", "csd"):
        out[k] = out[k] / np.linalg.norm(out[k], 2)
    pos = np.array([mont.get_positions()["ch_pos"][c] for c in CHANNELS])
    check = {"E57_xyz_m": pos[iL].round(4).tolist(), "E100_xyz_m": pos[iR].round(4).tolist(),
             "z_rank_of_E57_among_128_low_is_inferior": int(np.argsort(np.argsort(pos[:, 2]))[iL]),
             "z_rank_of_E100": int(np.argsort(np.argsort(pos[:, 2]))[iR])}
    return out, check


def cmd_montages(args, config) -> dict:
    run = open_run("montages", args.run, config, args=vars(args))
    mats, check = build_montages()
    # linearity self-check on random data for the MNE-derived operators
    import mne
    rng = np.random.default_rng(0)
    x = rng.normal(size=(128, 500))
    x = x - x.mean(0, keepdims=True)
    info = mne.create_info(CHANNELS, 250.0, "eeg")
    info.set_montage(mne.channels.make_standard_montage("GSN-HydroCel-128"))
    raw = mne.io.RawArray(x.copy(), info, verbose="ERROR")
    direct_csd = mne.preprocessing.compute_current_source_density(raw.copy(), verbose="ERROR").get_data()
    a, b = mats["csd"] @ x, direct_csd
    check["csd_operator_scale_free_err"] = float(np.max(np.abs(a / np.linalg.norm(a) - b / np.linalg.norm(b))))
    check["mastoid_operator_err"] = float(np.max(np.abs(mats["mastoid"] @ x - (x - x[[56, 99]].mean(0)))))
    save_npz_atomic(run["private"] / "montages.npz", **{k: v.astype(np.float64) for k, v in mats.items()})
    write_json_atomic(run["public"] / "summary_montages.json", check, private=False)
    return check


def _apply(lane, M, device):
    import torch
    Mt = torch.as_tensor(M, dtype=torch.float32, device=device)
    out = torch.empty_like(lane.x)
    for b in range(0, lane.x.shape[0], 4096):
        xb = lane.x[b:b + 4096].float()
        out[b:b + 4096] = torch.einsum("ij,njt->nit", Mt, xb).clamp(-6e4, 6e4).half()
    # per-record robust rescale (median |x| over the record's trials), as in staging
    for r in np.unique(lane.record):
        sel = torch.as_tensor(np.flatnonzero(lane.record == r), device=device)
        v = out[sel].float()
        scale = float(v.abs().median().item()) or 1.0
        out[sel] = (v / scale).clamp(-60, 60).half()
    return out


def _child_auc(y, s, child, mask=None):
    from auditory_pf import stats as st
    out = {}
    for c in np.unique(child):
        m = child == c
        if mask is not None:
            m = m & mask
        a = st.auc(y[m], s[m])
        if np.isfinite(a):
            out[int(c)] = a
    return out


def run_unit(config, montage: str, lane_name: str, mats, out_path) -> dict:
    import torch
    from auditory_gx import data as gxd
    from auditory_gx import train as gxt
    from auditory_gx.runtime import load_config as gx_load_config
    from auditory_pf import gpu
    from scipy.stats import spearmanr
    dev = gpu.device()
    gx_config = gx_load_config(cfg(config, "sources.gx_config"))
    lane = gxd.load_lane(gx_config, ROOT / "private/auditory_gx" / cfg(config, "sources.stage_run"), lane_name, dev)
    lane.x = _apply(lane, mats[montage], dev)
    y = lane.y.cpu().numpy()
    seeds = [int(v) for v in cfg(config, "montage.seeds")]
    diffs = np.full((len(seeds), len(y)), np.nan, np.float32)
    per_seed = []
    for si, seed in enumerate(seeds):
        folds = gxd.child_folds(lane.n_children, 5, seed)
        for k, f in enumerate(folds):
            test_children = np.asarray(f)
            train_children = np.setdiff1d(np.arange(lane.n_children), test_children)
            inner_tr, inner_val = gxd.split_inner(train_children, 0.15, seed * 10 + k)
            gxt.seed_all(seed * 10 + k)
            model = gxt.build_model(gx_config, lane)
            gxt.fit(model, lane, gxd.idx_of_children(lane, inner_tr), gxd.idx_of_children(lane, inner_val), gx_config, seed=seed * 10 + k)
            te = gxd.idx_of_children(lane, test_children)
            diffs[si, te] = gpu.infer(model, lane, te)
        per_seed.append(float(np.mean(list(_child_auc(y, diffs[si], lane.child).values()))))
    ens = np.nanmean(diffs, 0)
    odd = _child_auc(y, ens, lane.child, lane.parity == 1)
    even = _child_auc(y, ens, lane.child, lane.parity == 0)
    common = sorted(set(odd) & set(even))
    r = spearmanr([odd[c] for c in common], [even[c] for c in common])[0] if len(common) >= 5 else float("nan")
    save_npz_atomic(out_path, diffs=diffs, y=y, child=lane.child, parity=lane.parity)
    return {"montage": montage, "lane": lane_name, "children": int(lane.n_children), "auc_child_mean_per_seed": per_seed,
            "auc_child_mean": float(np.mean(per_seed)), "split_half_spearman": float(r),
            "split_half_spearman_brown": float(2 * r / (1 + r)) if np.isfinite(r) and r > -1 else float("nan"),
            "n_children_reliability": len(common)}


def cmd_montage_lane(args, config) -> dict:
    run = open_run("montage_lane", args.run, config, args=vars(args))
    with np.load(private_dir(config, args.montage_run) / "montages.npz") as z:
        mats = {k: z[k] for k in z.files}
    units = [(m, l) for m in MONTAGES for l in MFF_LANES_B]
    out = []
    for m, l in task_units(units):
        path = run["private"] / f"{m}__{l}.npz"
        res_path = run["private"] / f"{m}__{l}.json"
        if res_path.exists():
            continue
        res = run_unit(config, m, l, mats, path)
        write_json_atomic(res_path, res, private=True)
        print(json.dumps(res), flush=True)
        out.append(res)
    return {"units": len(out)}
