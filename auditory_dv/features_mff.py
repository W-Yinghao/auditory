"""D2 continuous spectral features (6 log band powers + 3 log Hjorth, per channel) for every MFF cohort record."""
from __future__ import annotations

import numpy as np

from auditory_d2.data import RecordStore, record_scale
from auditory_d2.spectral import record_feature_matrix

from .mff import MffCohort
from .runtime import ROOT, cfg, open_run, save_npz_atomic, write_json_atomic


def cmd_features_mff(args, config) -> dict:
    run = open_run("features_mff", args.run, config, args=vars(args))
    co = MffCohort(config, args.prepare_run)
    feats = np.full((len(co.rec), 128, 9), np.nan)
    windows = np.zeros(len(co.rec), np.int64)
    for r in co.rec.itertuples():
        store = RecordStore(ROOT, cfg(config, "sources.d1_mff_run"), str(r.record_id))
        if store.n_channels != 128 or store.starts.size == 0:
            continue
        feats[int(r.rec)] = record_feature_matrix(store, record_scale(store))
        windows[int(r.rec)] = int(min(store.starts.size, 400))
    save_npz_atomic(run["private"] / "features_mff.npz", cont=feats, windows=windows)
    summary = {"records": int(len(co.rec)), "with_features": int(np.isfinite(feats[:, 0, 0]).sum()),
               "windows_median": float(np.median(windows[windows > 0]))}
    write_json_atomic(run["public"] / "summary_features_mff.json", summary, private=False)
    return summary
