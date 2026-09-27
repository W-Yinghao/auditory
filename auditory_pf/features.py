"""CPU features: D2 continuous spectra (H16/H17) and fixed-budget pre-stimulus spectra (H2 background)."""
from __future__ import annotations

import numpy as np

from auditory_d2.data import RecordStore, record_scale
from auditory_d2.spectral import record_feature_matrix

from .cohort import Cohort
from .runtime import ROOT, cfg, open_run, save_npz_atomic, write_json_atomic

PRE_BINS = ((5.0, 5.0), (10.0, 10.0), (15.0, 15.0), (20.0, 20.0), (25.0, 45.0))


def prestim_spectrum(x_pre: np.ndarray, rate: float = 250.0) -> np.ndarray:
    """x_pre [n, C, 50] -> [C, 5] log mean power (Hann, 5 Hz bins)."""
    x = x_pre.astype(np.float64)
    x = x - x.mean(-1, keepdims=True)
    w = np.hanning(x.shape[-1])
    spec = np.abs(np.fft.rfft(x * w, axis=-1)) ** 2
    freqs = np.fft.rfftfreq(x.shape[-1], 1.0 / rate)
    power = spec.mean(0)                                           # [C, F]
    out = []
    for lo, hi in PRE_BINS:
        m = (freqs >= lo - 1e-6) & (freqs <= hi + 1e-6)
        out.append(np.log(np.maximum(power[:, m].sum(-1), 1e-20)))
    return np.stack(out, -1)


def cmd_features(args, config) -> dict:
    run = open_run("features", args.run, config, args=vars(args))
    cohort = Cohort(config, args.prepare_run)
    rec = cohort.rec
    n_rec = len(rec)
    stage = ROOT / "private/auditory_gx" / cfg(config, "sources.stage_run") / "epochs"
    pre = int(round(0.2 * 250))
    D = cohort.draw_dev.shape[1]
    prestim = np.full((n_rec, 20, len(PRE_BINS)), np.nan)
    cont = np.full((n_rec, 20, 9), np.nan)
    cont_windows = np.zeros(n_rec, dtype=np.int64)
    for r in rec.itertuples():
        if int(r.rec) in cohort.draw_row:
            with np.load(stage / f"{r.record_id}.npz", allow_pickle=False) as s:
                x = s["x"][s["accepted"].astype(bool)][:, :, :pre]
            per = []
            for d in range(D):
                pos = np.concatenate([cohort.draw_dev[cohort.draw_row[int(r.rec)], d], cohort.draw_std[cohort.draw_row[int(r.rec)], d]])
                per.append(prestim_spectrum(x[pos]))
            prestim[int(r.rec)] = np.mean(per, 0)
        cid = str(r.d1_container_id)
        if cid and cid != "nan":
            store = RecordStore(ROOT, cfg(config, "sources.d1_bdf_run"), cid)
            if store.starts.size:
                scale = record_scale(store)
                cont[int(r.rec)] = record_feature_matrix(store, scale)
                cont_windows[int(r.rec)] = int(min(store.starts.size, 400))
    save_npz_atomic(run["private"] / "features.npz", prestim=prestim, cont=cont, cont_windows=cont_windows)
    summary = {"records": n_rec, "prestim_records": int(np.isfinite(prestim[:, 0, 0]).sum()),
               "cont_records": int(np.isfinite(cont[:, 0, 0]).sum()), "cont_windows_median": float(np.median(cont_windows[cont_windows > 0]))}
    write_json_atomic(run["public"] / "summary_features.json", summary, private=False)
    return summary
