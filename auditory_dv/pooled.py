"""Direction F (PREPARED, NOT SUBMITTED - needs the user's decision on the 'no channel selection' boundary).

MFF 128-channel epochs are expressed on the 20 HA 10-20 positions (nearest HydroCel electrode to each position) and
pooled with the BDF lane for one shared EEGNet; compared on the same child folds with system-specific models.
"""
from __future__ import annotations

import json
import types

import numpy as np

from .runtime import ROOT, cfg, open_run, save_npz_atomic, stable_int, task_units, write_json_atomic

TEN_TWENTY = {"Fp1": "Fp1", "Fp2": "Fp2", "Fz": "Fz", "F3": "F3", "F4": "F4", "F7": "F7", "F8": "F8", "Cz": "Cz",
              "C3": "C3", "C4": "C4", "T3": "T7", "T4": "T8", "Pz": "Pz", "P3": "P3", "P4": "P4", "T5": "P7",
              "T6": "P8", "Oz": "Oz", "O1": "O1", "O2": "O2"}


def nearest_map() -> list[int]:
    import mne
    from auditory_gx.round3 import HA_CHANNELS
    hc = mne.channels.make_standard_montage("GSN-HydroCel-128").get_positions()["ch_pos"]
    std = mne.channels.make_standard_montage("standard_1020").get_positions()["ch_pos"]
    names = [f"E{i}" for i in range(1, 129)]
    P = np.array([hc[n] for n in names])
    P = P / np.linalg.norm(P, axis=1, keepdims=True)
    out = []
    for ha in HA_CHANNELS:
        q = np.asarray(std[TEN_TWENTY[ha]])
        q = q / np.linalg.norm(q)
        out.append(int(np.argmax(P @ q)))
    return out


def cmd_pooled(args, config) -> dict:
    import torch
    from auditory_gx import train as gxt
    from auditory_pf import gpu
    from auditory_pf.cohort import Cohort
    from auditory_pf.runtime import load_config as pf_load
    from auditory_pf import stats as st
    from .mff import MffCohort, load_mff_lane
    dev = gpu.device()
    run = open_run("pooled", args.run, config, args=vars(args))
    pfc = pf_load(cfg(config, "sources.pf_config_v2"))
    bco = Cohort(pfc, cfg(config, "sources.pf_prepare_v2"))
    blane, gx_config = gpu.load_lane_checked(pfc, bco, dev)
    mco = MffCohort(config, cfg(config, "runs.prepare_mff"))
    mlane, _ = load_mff_lane(config, mco, dev)
    idx20 = torch.as_tensor(nearest_map(), device=dev)
    mx = mlane.x[:, idx20, :]
    del mlane
    x = torch.cat([blane.x, mx])
    y = torch.cat([blane.y, torch.as_tensor(mco.t_y, device=dev)])
    nb = bco.n_trials
    child = np.concatenate([bco.rec.child.to_numpy()[bco.t_record], 10000 + mco.child_of_trial])
    lane = types.SimpleNamespace(x=x, y=y, n_classes=2)
    kids = np.unique(child)
    res = []
    for seed in cfg(config, "mff.seeds"):
        rng = np.random.default_rng(int(seed))
        fold = {}
        for grp in (kids[kids < 10000], kids[kids >= 10000]):
            order = rng.permutation(grp)
            for i, c in enumerate(order):
                fold[int(c)] = i % 5
        for k in range(5):
            path = run["private"] / f"s{seed}_k{k}.json"
            if path.exists():
                continue
            te = np.array([c for c in kids if fold[int(c)] == k])
            out = {}
            for name, pool in (("pooled", kids), ("bdf_only", kids[kids < 10000]), ("mff_only", kids[kids >= 10000])):
                trk = np.array([c for c in pool if fold[int(c)] != k])
                val = np.sort(np.random.default_rng(stable_int("dv_f_val", seed, k, name)).choice(trk, max(1, len(trk) * 15 // 100), replace=False))
                tr_idx = np.flatnonzero(np.isin(child, np.setdiff1d(trk, val)))
                va_idx = np.flatnonzero(np.isin(child, val))
                model, _ = gpu.train_stim(lane, gx_config, tr_idx, va_idx, stable_int("dv_f", seed, k, name) % (2 ** 31 - 1))
                for sysname, test_sys in (("bdf", te[te < 10000]), ("mff", te[te >= 10000])):
                    if (name == "bdf_only" and sysname == "mff") or (name == "mff_only" and sysname == "bdf"):
                        continue
                    aucs = []
                    for c in test_sys:
                        ii = np.flatnonzero(child == c)
                        d = gpu.infer(model, lane, ii)
                        aucs.append(st.auc(y[torch.as_tensor(ii, device=dev)].cpu().numpy(), d))
                    out[f"{name}__{sysname}"] = float(np.nanmean(aucs))
            write_json_atomic(path, out, private=True)
            res.append(out)
    return {"units": len(res)}
