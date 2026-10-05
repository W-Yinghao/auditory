"""G1: aggregate the TH-half layer selection (MEASUREMENT_AMENDMENT_001 §3) and freeze the measurement specification.

Writes configs/auditory_c3_v1_frozen.json: the package spec with frozen=true, the amendment, the selected Whisper
layer and its XLS-R counterpart, and sha256 of every code/config file the frozen analyses depend on. Refuses to run
if any selection-half subject is missing (never selects on a partial set).

Usage: python -m auditory_c3.freeze
"""
from __future__ import annotations

import datetime as dt
import glob
import hashlib
import json
import os

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEL = os.path.join(REPO, "private", "auditory_c3", "public", "fau_tud")
ROIS = ["frontocentral", "left_temporal", "right_temporal"]


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    split = json.load(open(os.path.join(SEL, "th_split.json")))
    missing = [s for s in split["selection_half"] if not os.path.exists(os.path.join(SEL, "select", f"{s}.json"))]
    if missing:
        raise SystemExit(f"selection incomplete, missing {missing}")
    layers = list(range(3, 33))
    M = np.array([[[json.load(open(os.path.join(SEL, "select", f"{s}.json")))[f"{r}/L{l:02d}"] for l in layers]
                   for r in ROIS] for s in split["selection_half"]])  # (subjects, rois, layers)
    crit = M.mean(axis=(0, 1))
    best = layers[int(np.argmax(crit))]
    xlsr = int(round(best * 24 / 32))
    sel = {"criterion": "mean over 14 TH selection-half subjects and 3 ROIs of bias- and surrogate-corrected "
                        "I(T; L_l,tau | y_Ac) averaged over 0-600 ms, attended stream, all 20 trials",
           "per_layer_mean_bits": dict(zip([f"L{l:02d}" for l in layers], map(float, crit))),
           "per_layer_sd_over_subjects": dict(zip([f"L{l:02d}" for l in layers], map(float, M.mean(1).std(0, ddof=1)))),
           "per_roi_best": {r: layers[int(np.argmax(M[:, i].mean(0)))] for i, r in enumerate(ROIS)},
           "per_subject_best": {s: layers[int(np.argmax(M[j].mean(0)))] for j, s in enumerate(split["selection_half"])},
           "selected_whisper_layer": best, "xlsr_counterpart_layer": xlsr}
    spec = json.load(open(os.path.join(REPO, "AUDITORY_C3_SERVER_PACKAGE_v1_20261003", "config", "measurement_spec.json")))
    spec["frozen"] = True
    files = sorted(glob.glob(os.path.join(REPO, "auditory_c3", "*.py")) + glob.glob(os.path.join(REPO, "auditory_c3", "vendor", "*"))
                   + glob.glob(os.path.join(REPO, "private", "auditory_c3", "vendor_jehn", "*.py"))
                   + glob.glob(os.path.join(REPO, "slurm", "auditory_c3_*.sbatch"))
                   + [os.path.join(REPO, "docs", "auditory_c3", "MEASUREMENT_AMENDMENT_001.md"), os.path.join(SEL, "th_split.json")])
    feat = "/projects/EEG-foundation-model/auditory_public/derived/c3_features_v1/fau_tud"
    frozen = {"frozen_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "gate": "G1",
              "package": "AUDITORY_C3_SERVER_PACKAGE_v1_20261003", "package_zip_sha256": sha(os.path.join(REPO, "AUDITORY_C3_SERVER_PACKAGE_v1_20261003.zip")),
              "measurement_spec": spec, "amendment": "docs/auditory_c3/MEASUREMENT_AMENDMENT_001.md",
              "layer_selection": sel,
              "feature_caches": {os.path.basename(p)[:-10]: json.load(open(p)).get("sha256") for p in sorted(glob.glob(os.path.join(feat, "*.done.json")))},
              "file_sha256": {os.path.relpath(p, REPO): sha(p) for p in files if os.path.isfile(p)}}
    out = os.path.join(REPO, "configs", "auditory_c3_v1_frozen.json")
    if os.path.exists(out):
        raise SystemExit(f"{out} exists: frozen files are never overwritten")
    json.dump(frozen, open(out, "w"), indent=1)
    print("FROZEN", out, sha(out)[:16], "layer", best, "xlsr", xlsr)
    print(json.dumps({k: v for k, v in sel.items() if k.startswith("per_roi") or k.startswith("selected") or k.startswith("xlsr")}))


if __name__ == "__main__":
    main()
