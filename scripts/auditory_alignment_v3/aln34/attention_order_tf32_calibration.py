"""R34_ATTENTION_ORDER note section 11.8 (b): TF32-emulation calibration of the tier-2 QC constant kappa (synthetic EEG, no data read).

For each calibration unit (seed-3401 lag alignment_plus_selection units, FAU / DTU x NCE / CS_SINGLE, subject fold 0, content fold 0):
  reference = the frozen run_attention.attention_windows on a synthetic cohort with the unit's real checkpoint, FP32 on CPU
              (plays the unit record: per-participant margins / accuracies, saved integrators);
  variants  = the same recomputation by attention_order.legacy_attention_scores under
              fp32_repeat (identical computation), tf32_rn / tf32_trunc (every Conv1d input and weight rounded to TF32, 10-bit mantissa,
              round-to-nearest-even or truncation; FP32 accumulation and bias, as cuDNN TF32), and three configuration errors:
              other_candidate (the other selection-weight checkpoint), readout_rng_offset (readout rng seed + 1001 instead of + 1000),
              other_fold (the same configuration's subject-fold-1 checkpoint);
  per variant: attention_order.evaluate_unit + unit_qc against the reference -> tier-1 pass, max |dm| / rms_s, window differences.
kappa rule (note 11.5): kappa = 10 x the largest TF32 ratio, rounded up to the next power of ten; accepted only if every configuration
error type's smallest per-unit ratio is >= 10 x kappa. Output: attention_order_tf32_calibration.json next to this script.
"""
import copy
import json
import math
import os
import sys
import time

import numpy as np
import torch

REPO = "/home/infres/yinwang/EEG_auditory"
sys.path.insert(0, REPO)
from auditory_alignment.data import Cohort  # noqa: E402
from auditory_alignment_v2.audio_targets import build_head, target_stats  # noqa: E402
from auditory_alignment_v2.temporal import build_encoder  # noqa: E402
from auditory_alignment_v3 import core, local_train  # noqa: E402
from auditory_alignment_v3 import run_attention as RA  # noqa: E402
from auditory_alignment_v3.aln34 import attention_order as AO  # noqa: E402

UNITS = {  # eid -> other subject fold's unit of the same configuration
    "ALN3_78e4e8f070635f79": "ALN3_4b30fc195b717b5e",   # fau align+sel CS_SINGLE
    "ALN3_85d3390a5443db7f": "ALN3_ab33eaf58c98781e",   # fau align+sel NCE
    "ALN3_b652c96caa6be728": "ALN3_784e0b4b8e50ef29",   # dtu align+sel CS_SINGLE
    "ALN3_d20ad5328ed7912b": "ALN3_e5f04dea51753023",   # dtu align+sel NCE
}
NCH = {"fau": 31, "dtu": 64}


def synthetic_cohort(ds, seed=0, n_train=6, n_test=3, trials=3, per_trial=8, ss_trials=2, ss_per=4):
    rng = np.random.default_rng(seed)
    fs, C, seg = 128, NCH[ds], 640
    parts = [{"id": f"p{i}", "group": "x", "fold": 1 + i % 3, "dev": False} for i in range(n_train)] + \
            [{"id": f"t{i}", "group": "x", "fold": 0, "dev": False} for i in range(n_test)]
    segs, E, S = [], 0, 0
    for p, part in enumerate(parts):
        for t in range(trials):
            role = "test" if part["fold"] == 0 else ("es" if t == 0 else "fit")
            for j in range(per_trial):
                segs.append({"p": p, "e0": E + j * seg, "s0": S + j * seg, "s0_ign": S + per_trial * seg + 100 + j * seg, "role": role, "kind": "cs",
                             "uid": f"2{t}@{j}", "hard_key": "x", "part": "0", "code": f"2{t}"})
            E += per_trial * seg + 200; S += 2 * per_trial * seg + 300
        for t in range(ss_trials):
            for j in range(ss_per):
                segs.append({"p": p, "e0": E + j * seg, "s0": S + j * seg, "s0_ign": None, "role": "fit" if t else "es", "kind": "ss",
                             "uid": f"1{t}@{j}", "hard_key": "x", "part": "0", "code": f"1{t}"})
            E += ss_per * seg + 200; S += ss_per * seg + 100
    eeg = rng.standard_normal((C, E)).astype(np.float32)
    stim = {"Local": rng.standard_normal((6, S)).astype(np.float32)}
    for s in segs:
        s["feat"] = np.zeros(2)
    return Cohort(fs, C, parts, eeg, stim, segs, {"dataset": ds, "content_fold": 0, "seg_len": seg})


def tf32(x, mode):
    xi = x.detach().contiguous().view(torch.int32)
    if mode == "rn":
        xi = xi + 0x0FFF + ((xi >> 13) & 1)
    return (xi & -8192).view(torch.float32)


class TF32Conv:
    """forward pre-hooks rounding every Conv1d input and (temporarily) weight to TF32."""

    def __init__(self, model, mode):
        self.model, self.mode, self.hooks, self.saved = model, mode, [], []

    def __enter__(self):
        for m in self.model.modules():
            if isinstance(m, torch.nn.Conv1d):
                self.saved.append((m, m.weight.data.clone()))
                m.weight.data = tf32(m.weight.data, self.mode)
                self.hooks.append(m.register_forward_pre_hook(lambda mod, inp: (tf32(inp[0], self.mode),) + tuple(inp[1:])))
        return self

    def __exit__(self, *a):
        for h in self.hooks:
            h.remove()
        for m, w in self.saved:
            m.weight.data = w


def build(b, coh, ck):
    dev = torch.device("cpu")
    g = core.grid_samples(coh.fs)
    bt = local_train.GridBatcher(coh, b["spec"], b, dev, g)
    torch.manual_seed(b["seed"])
    enc = build_encoder("lag_local_tokens", coh.n_ch, 32, bt.W, coh.fs)
    head = build_head("fixed_features", bt.audio_dim, 32, coh.meta["dataset"], target_stats(bt, np.random.default_rng(b["seed"] + 5)))
    sd = torch.load(ck, map_location="cpu", weights_only=True)
    enc.load_state_dict(sd["enc"]); head.load_state_dict(sd["head"]); enc.eval(); head.eval()
    return enc, head, bt, g


def ck_path(eid, k):
    return os.path.join(AO.OUT, "ckpt", f"{eid}_c{k}_best.pt")


def qc_of(arrays, aw):
    sc = AO.scores_from_arrays(arrays)
    per, _ = AO.evaluate_unit(sc, aw)
    tol2 = dict(AO.QC_TOL2, kappa_rms_s=None)
    q = AO.unit_qc(sc, per, aw, None, AO.QC_TOL, tol2)
    return {"tier1_pass": q["pass"], "n_reasons": q["n_reasons"], "max_errors": q["max_errors"], "first_reasons": q["reasons"][:3]}


def main():
    torch.set_num_threads(2)
    out = {"created": time.strftime("%Y-%m-%d %H:%M:%S %Z"), "torch": torch.__version__, "units": {}}
    for eid, other in UNITS.items():
        t0 = time.time()
        rec = AO.load_record(eid)
        b = copy.deepcopy(rec["bound_row"])
        k = AO.SEL_WEIGHTS.index(rec["chosen_sel_weight"])
        coh = synthetic_cohort(b["dataset"], seed=11)
        # cohort arrays are consumed by Batcher.__init__ (coh.eeg / coh.stim set to None): rebuild per model
        mk = lambda: synthetic_cohort(b["dataset"], seed=11)
        coh = mk(); enc, head, bt, g = build(b, coh, ck_path(eid, k))
        with torch.no_grad():
            aw = json.loads(json.dumps(RA.attention_windows(b, enc, head, bt, coh, g), default=float))
            ref, _ = AO.legacy_attention_scores(b, enc, head, bt, coh, g)
            res = {"fp32_repeat": qc_of(ref, aw)}
            for mode in ("rn", "trunc"):
                with TF32Conv(enc, mode):
                    arr, _ = AO.legacy_attention_scores(b, enc, head, bt, coh, g)
                res[f"tf32_{mode}"] = qc_of(arr, aw)
            b2 = copy.deepcopy(b); b2["seed"] += 1
            arr, _ = AO.legacy_attention_scores(b2, enc, head, bt, coh, g)
            res["readout_rng_offset"] = qc_of(arr, aw)
            coh2 = mk(); enc2, head2, bt2, _ = build(b, coh2, ck_path(eid, 1 - k))
            arr, _ = AO.legacy_attention_scores(b, enc2, head2, bt2, coh2, g)
            res["other_candidate"] = qc_of(arr, aw)
            orec = AO.load_record(other)
            ok_ = AO.SEL_WEIGHTS.index(orec["chosen_sel_weight"])
            coh3 = mk(); enc3, head3, bt3, _ = build(b, coh3, ck_path(other, ok_))
            arr, _ = AO.legacy_attention_scores(b, enc3, head3, bt3, coh3, g)
            res["other_fold"] = qc_of(arr, aw)
        out["units"][eid] = {"dataset": b["dataset"], "objective": b["spec"]["objective"], "chosen_candidate": k, "other_fold_unit": other,
                             "window_counts": aw["window_counts"], "variants": res, "seconds": round(time.time() - t0, 1)}
        print(eid, b["dataset"], b["spec"]["objective"], {v: (r["tier1_pass"], f"{r['max_errors']['margin_over_rms_s']:.2e}", f"{r['max_errors']['margin']:.2e}")
                                                          for v, r in res.items()}, f"{time.time() - t0:.0f}s", flush=True)
    tf = max(u["variants"][v]["max_errors"]["margin_over_rms_s"] for u in out["units"].values() for v in ("tf32_rn", "tf32_trunc"))
    errs = {v: min(u["variants"][v]["max_errors"]["margin_over_rms_s"] for u in out["units"].values()) for v in ("other_candidate", "readout_rng_offset", "other_fold")}
    kappa = 10.0 ** math.ceil(math.log10(10.0 * tf)) if tf > 0 else None
    accepted = kappa is not None and all(e >= 10.0 * kappa for e in errs.values())
    out["summary"] = {"max_tf32_ratio": tf, "min_error_ratio_by_type": errs, "kappa": kappa, "accepted": accepted,
                      "tier1_pass": {v: sum(u["variants"][v]["tier1_pass"] for u in out["units"].values()) for v in
                                     ("fp32_repeat", "tf32_rn", "tf32_trunc", "other_candidate", "readout_rng_offset", "other_fold")},
                      "n_units": len(out["units"])}
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "attention_order_tf32_calibration.json")
    with open(p, "w") as f:
        json.dump(out, f, indent=1)
    os.chmod(p, 0o600)
    print(json.dumps(out["summary"], indent=1))


if __name__ == "__main__":
    main()
