"""C3-DL D0 (plan §15.2): definitions and support tables, stimulus side and event metadata only. No EEG values,
no outcomes, no model fitting.

Public P-L (FAU/TUD): segments per stimulus code (5 s, inside the analysis-valid range), content-split support
(participants all heard the same 20 codes), and matched-candidate support for single-speaker attended segments:
candidates = segments of the SAME story (same narrator/recording) from a DIFFERENT part (no shared audio or speech-
model context), ranked by distance of their frozen Ac summaries (per-segment mean and SD of the 5 Ac PCs, z-scored);
coverage at K = 8 within a radius fixed as the 25th percentile of all eligible pair distances.
Private H-Cur (BDF lane): per child, trials per (history bin x class); deviant-after-deviant occurrence (structural
determinism check); per-group history composition; number of physical blocks per record.

Usage: python -m auditory_c3.c3dl_d0
Output: results/auditory_c3/C3DL_D0_support.json (aggregate)
"""
from __future__ import annotations

import collections
import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEAT = "/projects/EEG-foundation-model/auditory_public/derived/c3_features_v1/fau_tud"
SEG_S, FS, GUARD = 5.0, 128, 314
K = 8


def public():
    import h5py
    out = {}
    with h5py.File(os.path.join(FEAT, "pca_k8_128hz_whisper_shallow.h5"), "r") as f:
        codes = sorted(k for k in f.keys() if not k.startswith("_"))
        seg = []
        for c in codes:
            for stream in sorted(f[c].keys()):
                A = f[f"{c}/{stream}/shallow_01_02"][()][:5]
                n = A.shape[1]; L = int(SEG_S * FS)
                starts = list(range(GUARD, n - GUARD - L + 1, L))
                for s in starts:
                    w = A[:, s:s + L]
                    seg.append({"code": c, "stream": stream, "story": c[1], "part": c[2], "cond": "SS" if c[0] == "1" else "CS",
                                "start": s, "feat": np.r_[w.mean(1), w.std(1)]})
    per_code = collections.Counter((s["code"], s["stream"]) for s in seg)
    out["segments_5s"] = {"total": len(seg), "by_condition_stream": dict(collections.Counter(f"{s['cond']}/{s['stream']}" for s in seg)),
                          "per_code_min": min(per_code.values()), "per_code_max": max(per_code.values())}
    # content split support: hold out story parts (same for every participant)
    ss_att = [s for s in seg if s["cond"] == "SS" and s["stream"] == "attended"]
    out["SS_attended"] = {"segments_per_participant": len(ss_att), "by_story": dict(collections.Counter(s["story"] for s in ss_att)),
                          "by_story_part": dict(collections.Counter(f"{s['story']}{s['part']}" for s in ss_att))}
    # matched candidates (stimulus-only)
    F = np.array([s["feat"] for s in ss_att]); F = (F - F.mean(0)) / (F.std(0) + 1e-12)
    D = np.sqrt(((F[:, None] - F[None]) ** 2).sum(-1))
    elig = np.array([[ss_att[i]["story"] == ss_att[j]["story"] and ss_att[i]["part"] != ss_att[j]["part"] for j in range(len(ss_att))] for i in range(len(ss_att))])
    radius = float(np.percentile(D[elig], 25))
    cov, dists = [], []
    for i in range(len(ss_att)):
        d = np.sort(D[i][elig[i]])
        cov.append(int((d <= radius).sum())); dists.append(float(d[:K].mean()) if len(d) >= K else np.nan)
    cov = np.array(cov)
    out["matched_candidates_SS_attended"] = {
        "rule": "same story (narrator), different part; distance on z-scored per-segment mean+SD of Ac PCs; radius = 25th pct of eligible pairs",
        "radius": radius, "K": K, "n_anchor_segments": len(ss_att), "eligible_pool_size_median": float(np.median(elig.sum(1))),
        "fraction_with_ge_K_within_radius": float(np.mean(cov >= K)), "within_radius_count_quantiles": [float(x) for x in np.percentile(cov, [5, 25, 50, 75, 95])],
        "mean_dist_to_K_nearest_median": float(np.nanmedian(dists)),
        "random_pair_distance_median": float(np.median(D[elig]))}
    return out


def private():
    import pandas as pd
    from .private_mi import P, lane_bank
    from .private_mi2 import hist_codes
    rec, bank = lane_bank("bdf_puretone", accepted_only=True)
    pf = pd.read_csv(os.path.join(P, "auditory_pf", "prepare_002", "records.csv"))
    ch = pd.read_csv(os.path.join(P, "auditory_pf", "prepare_002", "children.csv"))
    H = hist_codes(bank["pc"], bank["prl"])
    out = {"children": {}}
    comp = collections.defaultdict(lambda: collections.Counter())
    dd_total = collections.Counter()
    blocks = []
    for _, c in ch.iterrows():
        grp = "HA" if (c.group == "labelled" and bool(c.eligible)) else ("NH" if (c.group == "nh" and bool(c.nh_eligible)) else None)
        if grp is None:
            continue
        stage = "NH" if grp == "NH" else ("HA_0_2" if c.duration_months <= 2 else ("HA_ge13" if c.duration_months >= 13 else "HA_2_13"))
        m = bank["rec"] == int(c.primary_rec)
        y, b, prev = bank["y"][m], H["since_last_deviant"][m], H["prev_class"][m]
        tab = collections.Counter(zip(b.tolist(), y.tolist()))
        dd_total.update({"prev_dev_cur_dev": int(((prev == 1) & (y == 1)).sum()), "prev_dev_cur_std": int(((prev == 1) & (y == 0)).sum())})
        for (bb, yy), n in tab.items():
            comp[stage][(bb, yy)] += n
        with np.load(os.path.join(P, "auditory_gx", "GX_stage_001", "epochs", f"{pf.record_id[int(c.primary_rec)]}.npz")) as s:
            blk = s["block_id"][s["accepted"].astype(bool)]
        blocks.append(len(np.unique(blk)))
        out["children"][stage] = out["children"].get(stage, 0) + 1
        mins = [tab.get((bb, 1), 0) for bb in range(6)]
        out.setdefault("min_deviants_per_bin_by_child", []).append(mins)
    out["deviant_after_deviant"] = dict(dd_total)
    out["structural_determinism_bin0"] = "NOT deterministic (deviant-after-deviant occurs)" if dd_total["prev_dev_cur_dev"] > 0 else "candidate deterministic: verify protocol"
    out["history_composition_by_group"] = {g: {f"bin{bb}_cls{yy}": n for (bb, yy), n in sorted(cnt.items())} for g, cnt in comp.items()}
    md = np.array(out.pop("min_deviants_per_bin_by_child"))
    out["children_with_lt5_deviants_in_bin"] = {f"bin{i}": int((md[:, i] < 5).sum()) for i in range(6)}
    out["blocks_per_record_quantiles"] = [float(x) for x in np.percentile(blocks, [0, 25, 50, 75, 100])]
    return out


def main():
    res = {"plan": "AUDITORY_C3_DEEP_CONDITIONAL_DECODING_PLAN_v1_20261005.md (sha256 ec95e406...)", "public_P_L": public(), "private_H_Cur": private()}
    os.makedirs(os.path.join(REPO, "results", "auditory_c3"), exist_ok=True)
    json.dump(res, open(os.path.join(REPO, "results", "auditory_c3", "C3DL_D0_support.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
