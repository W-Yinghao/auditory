"""H-series CPU preparation (NEXTMAP_H_PROTOCOL_FROZEN.md sections 1 and 4).

h1-prep: MFF children with age (auditory_dv prepare_mff_001), primary record re-staged from the D1 MFF array as 20 mapped
10-20 channels (frozen one-to-one assignment <= 40 mm), re-referenced to their own average (as the BDF D1 average over its
20 scalp channels), GX QC in uV, record scale, clip +-60, float16; seeded 80/80 draws; D2 spectra and spectral-plus
features of the mapped, re-referenced continuous data; 128-channel D2 spectra from auditory_dv features_mff.
h4-features: spectral-plus features (aperiodic exponent/offset, alpha centroid, relative band power) of the 55 HA
primary records. Everything per record stays under private/.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from scipy import signal

from auditory_d2 import spectral as d2s
from auditory_d2.data import RecordStore, record_scale
from auditory_st.features import epoch_qc

from . import representations as rp
from .adapters import AgeSource, st_events
from .runtime import (ROOT, ProvenanceError, cfg, close_run, open_run, require_protocol, save_npz_atomic, stable_int,
                      write_csv_atomic, write_json_atomic)

HA_CHANNELS = ["Fp1", "Fp2", "Fz", "F3", "F4", "F7", "F8", "Cz", "C3", "C4", "T3", "T4", "Pz", "P3", "P4", "T5", "T6",
               "Oz", "O1", "O2"]


# ---------------------------------------------------------------------- spectral-plus features

def welch_mean(windows, rate: float) -> tuple[np.ndarray, np.ndarray]:
    """Mean Welch PSD (2 s Hann, 50% overlap) over windows [C, T] -> (freqs, psd [C, F])."""
    total, n, freqs = None, 0, None
    for w in windows:
        freqs, p = signal.welch(np.asarray(w, np.float64), fs=rate, nperseg=int(round(2 * rate)),
                                noverlap=int(round(rate)), window="hann", axis=-1)
        total = p if total is None else total + p
        n += 1
    if n == 0:
        raise ValueError("NO_WINDOWS")
    return freqs, total / n


def specplus_from_psd(freqs: np.ndarray, psd: np.ndarray, h4: dict) -> np.ndarray:
    """[C, 8]: aperiodic exponent, offset (robust log-log fit), alpha residual centroid, 5 relative band powers."""
    lo, hi = h4["fit_range_hz"]
    alo, ahi = h4["alpha_range_hz"]
    m = (freqs >= lo) & (freqs <= hi)
    x = np.log10(freqs[m])
    out = np.full((psd.shape[0], 3 + len(h4["bands_hz"])), np.nan)
    band_tot = (freqs >= 1) & (freqs <= 40)
    for c in range(psd.shape[0]):
        y = np.log10(np.maximum(psd[c, m], 1e-30))
        keep = np.ones_like(y, dtype=bool)
        for _ in range(int(h4["robust_iterations"])):
            slope, icpt = np.polyfit(x[keep], y[keep], 1)
            resid = y - (slope * x + icpt)
            mad = 1.4826 * np.median(np.abs(resid[keep] - np.median(resid[keep])))
            keep = resid <= float(h4["peak_mad"]) * max(mad, 1e-12)
            if keep.sum() < 5:
                keep = np.ones_like(y, dtype=bool)
                break
        slope, icpt = np.polyfit(x[keep], y[keep], 1)
        am = (freqs >= alo) & (freqs <= ahi)
        ra = np.log10(np.maximum(psd[c, am], 1e-30)) - (slope * np.log10(freqs[am]) + icpt)
        pos = np.clip(ra, 0, None)
        paf = float((freqs[am] * pos).sum() / pos.sum()) if pos.sum() > 0 else np.nan
        tot = psd[c, band_tot].sum()
        rel = [psd[c, (freqs >= b0) & (freqs < b1)].sum() / tot for b0, b1 in h4["bands_hz"]]
        out[c] = [-slope, icpt, paf] + rel
    return out


def store_windows(store: RecordStore, scale: float, max_windows: int, channel_index=None, rereference=False):
    starts = store.starts
    if starts.size > max_windows:
        starts = starts[np.linspace(0, starts.size - 1, max_windows).astype(int)]
    for s0 in starts:
        w = np.asarray(store.read(int(s0)), dtype=np.float64)
        if channel_index is not None:
            w = w[channel_index]
        if rereference:
            w = w - w.mean(0, keepdims=True)
        yield w / scale


def cmd_h4_features(args, config) -> dict:
    require_protocol(config)
    run = open_run("h4_features", args.run, config, args=vars(args))
    src = AgeSource(config)
    h4 = config["h4"]
    feats, done = np.full((len(src.co.rec), 20, 3 + len(h4["bands_hz"])), np.nan), 0
    st = pd.read_csv(ROOT / "private/auditory_st" / cfg(config, "sources.st_scope_run") / "records.csv").set_index("record_id")
    for c in src.main_children:
        r = src.primary(c)
        cid = str(st.loc[str(src.rec.loc[r, "record_id"]), "_d1_container_id"])
        store = RecordStore(ROOT, cfg(config, "sources.d1_bdf_run"), cid)
        f, p = welch_mean(store_windows(store, record_scale(store), int(h4["max_windows"])), store.rate)
        feats[r] = specplus_from_psd(f, p, h4)
        done += 1
    save_npz_atomic(run["private"] / "specplus_ha.npz", specplus=feats)
    summary = {"records": done, "nonfinite_fraction": float(np.mean(~np.isfinite(feats[[src.primary(c) for c in src.main_children]]))),
               "exponent_median": float(np.nanmedian(feats[:, :, 0])), "paf_median_hz": float(np.nanmedian(feats[:, :, 2]))}
    write_json_atomic(run["public"] / "summary_h4_features.json", summary, private=False)
    close_run(config, "h4_features", args.run, "COMPLETED")
    return summary


# ---------------------------------------------------------------------- H1: MFF mapped 20-channel staging

def mapped_channels(config) -> tuple[list[str], dict]:
    from auditory_d2.transfer import match_to_1020
    geo = json.loads((ROOT / "private/auditory_d2/D1_mff_001_geometry.json").read_text())
    key = [k for k, v in geo.items() if len(v["channels"]) == 128]
    if len(key) != 1:
        raise ProvenanceError("MFF_128_LAYOUT_NOT_UNIQUE")
    lay = geo[key[0]]
    keep = [i for i, p in enumerate(lay["xyz_m"]) if p is not None]
    assignment, diag = match_to_1020(np.asarray([lay["xyz_m"][i] for i in keep], float))
    if not diag["eligible"] or diag["max_distance_m"] > float(cfg(config, "h1.max_distance_m")):
        raise ProvenanceError(f"MAPPING_NOT_ELIGIBLE:{diag}")
    names = [lay["channels"][keep[j]] for j in assignment]
    return names, {**diag, "layout": key[0][:8], "targets": HA_CHANNELS}


def restage_mapped(config, gx: dict, record_id: str, names: list[str]) -> dict:
    meta = json.loads((ROOT / "private/auditory_d1" / cfg(config, "sources.d1_mff_run") / "arrays" / f"{record_id}.json").read_text())
    data = np.load(ROOT / "private/auditory_d1" / cfg(config, "sources.d1_mff_run") / "arrays" / f"{record_id}.npy", mmap_mode="r")
    ch = [meta["channels"].index(n) for n in names]
    events = st_events(config, record_id)
    rate = float(meta["rate_hz"])
    pre, post = int(round(0.2 * rate)), int(round(0.6 * rate))
    guard = int(round(float(gx["epoch"]["interval_edge_guard_seconds"]) * rate))
    iv = {int(r["interval_index"]): r for r in meta["intervals"]}
    t = events[(events.event_kind == "target") & (events.exported_index >= 0)]
    keep = [int(r.exported_index) - pre >= int(iv[int(r.exported_interval_index)]["start"]) + guard
            and int(r.exported_index) + post <= int(iv[int(r.exported_interval_index)]["stop"]) - guard for r in t.itertuples()]
    t = t[np.asarray(keep, bool)]
    on = t.exported_index.to_numpy(np.int64)
    ep = np.stack([np.asarray(data[ch, e - pre:e + post], np.float32) for e in on]) if len(on) else np.zeros((0, 20, 200), np.float32)
    ep = ep - ep.mean(1, keepdims=True)                      # 20-channel average reference
    q = gx["qc"]
    acc = np.array([epoch_qc(e, ptp_max=float(q["ptp_max_uv"]), ptp_fraction_max=float(q["ptp_channel_fraction_max"]),
                             flat_ptp=float(q["flat_ptp_uv"]), flat_fraction_max=float(q["flat_channel_fraction_max"]))[0]
                    for e in ep], bool)
    scale = float(np.median(np.abs(ep[acc]))) if acc.any() else 1.0
    if not np.isfinite(scale) or scale <= 1e-6:
        scale = 1.0
    y = (t.stimulus_local_id.to_numpy(np.int64) > 0).astype(np.int64)
    return {"x": rp.stage_transform(ep, scale), "y": y, "accepted": acc, "record_scale": scale, "channel_index": ch,
            "rate": rate, "n_epochs": int(len(on))}


def cmd_h1_prep(args, config) -> dict:
    from auditory_gx.runtime import load_config as gx_load
    require_protocol(config)
    run = open_run("h1_prep", args.run, config, args=vars(args))
    gx = gx_load(cfg(config, "sources.gx_config"))
    h1, h4 = config["h1"], config["h4"]
    dv = ROOT / "private/auditory_dv" / h1["mff_prepare"]
    rec = pd.read_csv(dv / "records.csv")
    ch = pd.read_csv(dv / "children.csv")
    names, diag = mapped_channels(config)
    with np.load(ROOT / "private/auditory_dv/features_mff_001/features_mff.npz", allow_pickle=False) as z:
        cont128 = z["cont"]
    K = int(h1["k_per_class"])
    rows = []
    out_dir = run["private"] / "records"
    for c in ch[ch.has_age.astype(bool)].itertuples():
        r = rec.set_index("rec").loc[int(c.primary_rec)]
        rid = str(r.record_id)
        path = out_dir / f"{rid}.npz"
        if not path.exists():
            st = restage_mapped(config, gx, rid, names)
            acc = st["accepted"]
            n_std, n_dev = int((acc & (st["y"] == 0)).sum()), int((acc & (st["y"] == 1)).sum())
            payload = {"child": np.int64(c.child), "age_months": np.float64(c.age_months), "n_std": np.int64(n_std),
                       "n_dev": np.int64(n_dev), "record_scale": np.float64(st["record_scale"]), "lane": np.asarray(r.lane)}
            if n_std >= K and n_dev >= K:
                pos = {}
                for cls in (0, 1):
                    cand = np.flatnonzero(acc & (st["y"] == cls))
                    rng = np.random.default_rng(stable_int("h1_draw", rid, cls) % (2 ** 63))
                    pos[cls] = np.sort(rng.choice(cand, K, replace=False))
                payload.update(x_std=st["x"][pos[0]], x_dev=st["x"][pos[1]],
                               raw_mu0=rp.raw_bins(st["x"][pos[0]], 5).mean(0), raw_mu1=rp.raw_bins(st["x"][pos[1]], 5).mean(0))
                store = RecordStore(ROOT, cfg(config, "sources.d1_mff_run"), rid)
                idx = np.asarray(st["channel_index"])
                vals = []                                    # D2 record_scale rule on the mapped, re-referenced data
                for s0 in np.random.default_rng(20260919).choice(store.starts, min(24, store.starts.size), replace=False):
                    w = np.asarray(store.read(int(s0)), np.float64)[idx]
                    vals.append(np.abs(w - w.mean(0, keepdims=True)).ravel())
                scale20 = float(np.median(np.concatenate(vals))) if vals else 1.0
                scale20 = scale20 if scale20 > 1e-6 else 1.0
                wins = list(store_windows(store, scale20, int(h4["max_windows"]), idx, rereference=True))
                payload["spec20"] = np.mean([d2s.window_features(w, store.rate) for w in wins], 0)
                f, p = welch_mean(wins, store.rate)
                payload["specplus20"] = specplus_from_psd(f, p, h4)
                payload["spec128"] = cont128[int(c.primary_rec)]
            save_npz_atomic(path, **payload)
        with np.load(path, allow_pickle=False) as z:
            rows.append({"child": int(z["child"]), "record_id": rid, "lane": str(z["lane"]), "age_months": float(z["age_months"]),
                         "n_std": int(z["n_std"]), "n_dev": int(z["n_dev"]), "included": "x_std" in z.files,
                         "identity_group": c.identity_group, "ci_label": bool(c.ci_label)})
    R = pd.DataFrame(rows)
    write_csv_atomic(R, run["private"] / "h1_cohort.csv", private=True)
    inc = R[R.included]
    summary = {"children_with_age": int(len(R)), "included_80_80": int(len(inc)), "by_lane_included": inc.lane.value_counts().to_dict(),
               "ci_label_included": int(inc.ci_label.sum()), "age_range_included": [float(inc.age_months.min()), float(inc.age_months.max())],
               "mapping": {k: (round(v, 4) if isinstance(v, float) else v) for k, v in diag.items()}}
    write_json_atomic(run["public"] / "summary_h1_prep.json", summary, private=False)
    close_run(config, "h1_prep", args.run, "COMPLETED")
    return summary
