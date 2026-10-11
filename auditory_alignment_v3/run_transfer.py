"""ALN3 E_PUBLIC_TRANSFER (package docs/08 §2-3): public auditory donor -> private current class, private task head retrained.

Donors never contain a private child.
  cbramod / reve   ALN2 public donor donor__<arch>__full__dtu+fau+federici__s<seed>.pt (the D_FM_PUBLIC donors; Federici
                   verified humans only), loaded strictly into the backbone before any adaptation (Backbone init_state);
                   task_partial -> pretrained_partial, task_full -> pretrained_full; repaired channel-aware readout d = 32;
                   learning rates / epochs = the ALN2 private recipe of that adaptation (run_private.fm_recipe).
  lag_local_tokens donor = the ALN3 A_LOCAL lag_local_tokens full unit FAU, subject fold 0, content fold 0, same seed and
                   objective (fixed in advance; not chosen on any transfer result). Tensor map: the local temporal encoder
                   (branches.0.local.1 conv, branches.0.local.2 LayerNorm, branches.0.tok) is loaded; re-initialised: the
                   channel input map branches.0.local.0 (public and private layouts differ), the lag position table
                   branches.0.pos (its lag grid depends on the sampling rate), the token aggregation proj (depends on the
                   token count; maps to the public alignment space) and the private class head. The loaded 3-sample temporal
                   kernels are used as is (12 ms at 250 Hz vs 23 ms at 128 Hz; disclosed). task_partial: loaded tensors
                   frozen; task_full: all trained. Loaded / new tensor names and parameter fractions are recorded.
Training / evaluation: the E_LOCAL / E_GENERIC private protocol (training children only; early-stopping blocks; calib.py
variants).
"""
from __future__ import annotations

import json
import os
import time
import traceback

import torch

from . import core

AD = {"task_partial": "pretrained_partial", "task_full": "pretrained_full"}
TRANSFER_PREFIXES = ("branches.0.local.1.", "branches.0.local.2.", "branches.0.tok.")


def fm_donor(row):
    return os.path.join(core.V2_OUT, "donors", f"donor__{row['spec']['source_architecture']}__full__dtu+fau+federici__s{row['seed']}.pt")


def local_donor_row(row, rows):
    return next((r for r in rows if r["family_id"] == "A_LOCAL" and r["dataset"] == "fau" and r["subject_fold"] == 0 and r["content_fold"] == 0
                 and r["seed"] == row["seed"] and r["spec"]["objective"] == row["spec"]["objective"]
                 and r["spec"]["architecture"] == "lag_local_tokens" and r["spec"].get("window", "full") == "full"), None)


def donor_ready(row, rows, out):
    if row["spec"]["source_architecture"] != "lag_local_tokens":
        return fm_donor(row) if os.path.exists(fm_donor(row)) else None
    d = local_donor_row(row, rows)
    if d is None:
        return None
    p = os.path.join(out, "units", f"{d['experiment_id']}.json"); ck = os.path.join(out, "ckpt", f"{d['experiment_id']}_best.pt")
    return ck if os.path.exists(p) and os.path.exists(ck) and json.load(open(p)).get("status") == "complete" else None


def run(row, out, epochs=None):
    from auditory_alignment import data
    from auditory_alignment_v2 import evaluate as ev2
    from . import calib, local_train
    from .run_private import fm_recipe
    path = os.path.join(out, "units", f"{row['experiment_id']}.json")
    donor = donor_ready(row, core.load_rows(), out)
    if donor is None:
        print("technical_pending (public donor not available)", row["experiment_id"]); return
    s = row["spec"]; src, ad = s["source_architecture"], s["adaptation"]
    b = core.bind(row); d = int(s.get("projection_dim", 32)); dev = torch.device("cuda"); t0 = time.time()
    rec = core.new_record(row, b, out); ck = os.path.join(out, "ckpt", row["experiment_id"])
    rec["donor"] = os.path.relpath(donor, core.REPO)
    try:
        kids = data.load_private(); log = {}
        if src != "lag_local_tokens":
            b["spec"].update({"architecture": src, "adaptation": AD[ad]})
            lr, rf, E = fm_recipe(src, AD[ad], s["objective"]); E = epochs or E
            init = torch.load(donor, map_location="cpu")["net"]
            enc, bt, protos = local_train.fit_private_fm(b, kids, dev, ck, log, lr["lr_backbone"], lr["lr_head"], E, AD[ad], init_state=init, d=d)
            rec["transfer_map"] = {"kind": "strict backbone load before adaptation", "backbone_init_loaded": enc.bb.init_loaded,
                                   "new": "channel-aware readout head (spatial_signed_k8_e32_v1) and private class head"}
            rec["resolved_config"] = {"d": d, "epochs": E, **lr, "recipe_file": os.path.relpath(rf, core.REPO), "backbone_adaptation": AD[ad]}
        else:
            b["spec"]["architecture"] = "lag_local_tokens"; b["spec"]["window"] = "full"
            if epochs is not None:
                b["spec"]["epochs"] = epochs
            dsd = torch.load(donor, map_location="cpu")["enc"]; orig = local_train.build_encoder; tmap = {}

            def build(arch_, n_ch, d_, W, fs):
                enc_ = orig(arch_, n_ch, d_, W, fs); own = enc_.state_dict(); loaded, new = [], []
                for k, v in own.items():
                    if k.startswith(TRANSFER_PREFIXES) and k in dsd and dsd[k].shape == v.shape:
                        own[k] = dsd[k].clone().to(v.device); loaded.append(k)
                    else:
                        new.append(k)
                assert {k.split(".")[3] for k in loaded if k.startswith("branches.0.local.")} == {"1", "2"} and any(k.startswith("branches.0.tok.") for k in loaded), loaded
                enc_.load_state_dict(own, strict=True)
                if ad == "task_partial":
                    for n, p in enc_.named_parameters():
                        if n in loaded:
                            p.requires_grad_(False)
                npar = {n: p.numel() for n, p in enc_.named_parameters()}
                tmap.update({"loaded": loaded, "new": new, "loaded_param_fraction": sum(npar.get(k, 0) for k in loaded) / sum(npar.values()),
                             "frozen": loaded if ad == "task_partial" else []})
                return enc_
            local_train.build_encoder = build
            try:
                enc, bt, protos = local_train.fit_private(b, kids, dev, ck, log, d=d)
            finally:
                local_train.build_encoder = orig
            rec["transfer_map"] = tmap
            rec["resolved_config"] = {"d": d, "epochs": b["spec"]["epochs"], "optimizer": "AdamW", "lr": 1e-3}
        rec.update(log)
        rec["eval"] = ev2.evaluate_private(b, enc, bt, log["objective_calibration"], protos)
        rec["eval"]["native_calibration"] = calib.private_variants(b, enc, bt, protos, log["objective_calibration"])
        rec["status"] = "complete"
    except Exception as ex:  # noqa: BLE001
        rec["status"] = "technical_failed"; rec["error"] = f"{type(ex).__name__}: {ex}"; rec["traceback"] = traceback.format_exc()[-4000:]
    core.write_record(path, rec, t0)
