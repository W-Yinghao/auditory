"""E34_PUBLIC_PRIOR zero-shot evaluation (module M6; private/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN.md §2.13, §2.11, §6.1
`zeroshot.py`, §6.6 M6, §7.1 item 9; contract aln33_env64_125ms_v1; inherited PUBLIC_PRIOR_EXECUTION_v3_3.md §6 "已预处理缓存与zero-shot
命名": 声音桥、温度、任务head不得用目标标签或query风险重拟合; 私有任务...不报告speech-zero-shot).

evaluate_zero_shot(row, manifest, dev, enc, bridge) runs the §2.13 procedure for one zero-shot row (modes A, B, C, C_partial):
  - the view is views.target_view of EVERY participant of the target cohort in the row's access mode (the Federici phantom as
    test_only), the loader of the adapted rows, so the stimulus-defined test pool pool_of("test", "ss") (n_test_candidates,
    pool_sha256) is the adapted row's of the same cell;
  - views.TickBatcher with train_p = set() (forced, not derived from the fold): no target training participant, no training and no
    early-stopping segment (asserted, with ev1's own selection of train_segs and early-stopping queries);
  - queries are the fold's participants (+ test_only sessions) only, as ev1.evaluate_continuous selects them (asserted);
  - the encoder is the donor member with names it never saw closed (zero weight, never read; bridge.donor_encoder,
    model.load_donor open_new=False); the audio head is the manifest's fixed head; kernel dependence uses the donor sigma;
  - ev1.Readouts -> the bridge's FrozenBridge (B_uni, tau(n) at the target pool size), ev1.Reps -> views.TickReps, ev1._ridge ->
    a function that raises, all inside try/finally; ev2.evaluate_continuous (unchanged) computes the full ev1 metric set
    (regular, hard and mismatched-EEG retrieval, split halves, attention 2AFC for FAU and DTU, kernel dependence), then again with
    the sensitivity bridge B_uni_cal and tau_cal(n) (eval_uni_cal). Nothing is fitted or calibrated on target labels or query risk.
The private cohort is never evaluated here (speech zero-shot is not computed for it: design §2.12, contract §6).

Imports: hashed into prior33_zeroshot with contract, views, model, select, bridge and run_zeroshot (§6.3); no other prior33 file
(sampler, losses, deps) is imported by the zero-shot path.

Interpretations (each is a deviation of the M6 summary):
- `enc` is the donor member's SharedEncoder or its checkpoint / state dict (the design's donor_state); the target-layout encoder is
  rebuilt from its state, so the caller's module is not changed.
- The two evaluations (B_uni, B_uni_cal) share one computation of the test representations: ev1.Reps is a TickReps subclass that
  memoises u / va per (unit, index list); the values are those of TickReps (the frozen-evaluation test compares with plain
  TickReps).
- Mode names: canonical_mode copies deps.zero_shot_mode (deps.py is not hashed and is not imported here); the cohort must be in
  contract.ZS_COHORTS[mode].
- The native readout of an NCE encoder never trained against v (slots XP, XM, XPC) is recorded as not applicable
  (native_readout.applicable = False); ev1's native metrics stay in the record (prior33.analysis drops them for those slots).
- SELECTION_LEVEL is the zero-shot level text of prior33.analysis (SELECTION_LEVEL["zero_shot"]; the test pins the two).
"""
from __future__ import annotations

import numpy as np
import torch

from auditory_alignment import evaluate as ev1
from auditory_alignment_v3 import core

from . import bridge as BR
from . import contract as C
from . import model as M
from . import views as V

SELECTION_LEVEL = "donor dev (the donor checkpoint and the joint λ are chosen on donor dev; no target-side selection)"
VIEW_RULE = "all_participants_trainp_empty_v1"       # §4.3 zero-shot spec.view
PRIVATE_NO_ZS = ("speech zero-shot is not computed for the private cohort (design §2.12: only EEG parameters transfer and a new "
                 "task head is trained; inherited contract §6: 私有任务只迁移EEG参数，训练类别头，不报告speech-zero-shot)")
_MODE_ALIASES = {"a": "A", "b": "B", "c": "C", "c_partial": "C_partial", "c-partial": "C_partial", "cpartial": "C_partial"}
FAU_CI_CAVEAT = ("the noica input keeps the CI stimulation artefacts that the stage-B rule removes: mode B and C values for CI users "
                 "do not separate neural tracking from artefact; they are access sensitivities (§2.13)")
SCALE_NOTE = ("the donors were trained on z-scored inputs, so mode C also carries a train/test scale mismatch; this is part of what "
              "mode C measures (§2.13)")
RMS_NOTE = ("the per-stream RMS of the test envelopes is applied in every mode and provably has no effect on any score (μ = 0, "
            "§2.3)")
ACCESS = {  # §2.13 table: EEG input, normalisation, what the input touched in target data
    ("A", "fau"): ("the cached contract input: stage-B trial_XX/eeg_1_20_ica", "z-score per participant x channel over all loaded pieces",
                   "z-score incl. test content; the stage-B ICA rule removes a component when its 1-8 Hz correlation with the presented "
                   "envelopes of all 20 trials peaks within +-3 samples (> 15 dB); CI interpolation (masked)"),
    ("A", "dtu"): ("the cached contract input: trial_NNN/eeg_1_20[:64], CAR over the 64 EEG channels (ours)",
                   "z-score per participant x channel over all loaded pieces", "z-score incl. test content; CAR"),
    ("A", "federici"): ("the cached contract input: the authors' blocks", "z-score per participant x channel over all loaded pieces",
                        "z-score incl. test blocks; the authors' ICA and 2-8 Hz filter"),
    ("B", "fau"): ("eeg_1_20_noica", "as mode A (z-score per participant x channel over all loaded pieces)",
                   "z-score incl. test content; CI interpolation (masked). No stimulus-informed step"),
    ("C", "fau"): ("FAU noica, physical unit", "each channel divided by a donor-derived scale (manifest mode_c)",
                   "nothing beyond fixed filters and the instantaneous CAR"),
    ("C", "dtu"): ("DTU with CAR, physical unit", "each channel divided by a donor-derived scale (manifest mode_c)",
                   "nothing beyond fixed filters and the instantaneous CAR"),
    ("C_partial", "federici"): ("the authors' preprocessed blocks, physical unit", "donor-derived scale (manifest mode_c)",
                                "the authors' ICA (method not ours)"),
}


def canonical_mode(mode):
    """A | B | C | C_partial from a short name, an alias or the full §2.13 name (deps.zero_shot_mode's rule)."""
    s = mode.strip() if isinstance(mode, str) else None
    if s in C.ZS_SUFFIX:
        return s
    if s is not None and s.lower() in _MODE_ALIASES:
        return _MODE_ALIASES[s.lower()]
    for k, suf in C.ZS_SUFFIX.items():
        if s is not None and s.endswith(suf):
            return k
    raise ValueError(f"zero-shot mode {mode!r} is not one of {list(C.ZS_SUFFIX)} (§2.13)")


def access_of(cohort, mode, manifest=None):
    """The §2.13 access declaration of (cohort, mode) for the record (normalisation access)."""
    if (mode, cohort) not in ACCESS:
        raise ValueError(f"zero-shot mode {mode} is not defined for {cohort} (§2.13)")
    eeg, norm, touched = ACCESS[(mode, cohort)]
    out = {"mode": mode, "mode_name": C.ZS_MODE_NAME[mode], "eeg_input": eeg, "cache": C.CACHE_FILE[mode], "normalisation": norm,
           "target_data_touched": touched, "envelope_rms": RMS_NOTE, "target_supervised_fit": "none"}
    if cohort == "fau" and mode in ("B", "C"):
        out["caveat"] = FAU_CI_CAVEAT
    if mode in ("C", "C_partial"):
        out["scale_note"] = SCALE_NOTE
        mc = ((manifest or {}).get("mode_c") or {}).get(cohort) or {}
        if cohort in (mc.get("donors") or []):
            raise ValueError(f"mode {mode}: target cohort {cohort} occurs in its source-statistics donors")
        sc = np.asarray(list((mc.get("scale") or {}).values()), dtype=np.float64)
        out["mode_c"] = {k: mc.get(k) for k in ("supported", "mode", "unit", "basis", "donors", "rule")}
        if sc.size:
            out["mode_c"]["scale_summary"] = {"n": int(sc.size), "min": float(sc.min()), "median": float(np.median(sc)),
                                              "max": float(sc.max())}
    return out


class MemoTickReps(V.TickReps):
    """views.TickReps (offs = TICK_OFFS) whose u / va are memoised per index list in `memo` (shared by the two frozen
    evaluations of one unit; the returned arrays are read-only)."""

    def __init__(self, enc, aud, bt, memo, stride=None, chunk=2048):
        super().__init__(enc, aud, bt, stride=stride, chunk=chunk)
        self._memo = memo

    def u(self, e0s):
        k = ("u", np.asarray(e0s, dtype=np.int64).tobytes())
        if k not in self._memo:
            a = super().u(e0s)
            a.setflags(write=False)
            self._memo[k] = a
        return self._memo[k]

    def va(self, s0s):
        k = ("va", np.asarray(s0s, dtype=np.int64).tobytes())
        if k not in self._memo:
            v, a = super().va(s0s)
            v.setflags(write=False)
            a.setflags(write=False)
            self._memo[k] = (v, a)
        return self._memo[k]


def _ridge_forbidden(*a, **k):
    raise BR.ZeroShotAccessError("ev1._ridge was called during a zero-shot evaluation: nothing may be fitted on target data (§2.13)")


def frozen_evaluate(b, enc, head, bt, coh, frozen, calib, memo=None):
    """ev2.evaluate_continuous (unchanged) with ev1.Readouts -> `frozen` (a bridge.FrozenBridge; it must receive no target training
    segment), ev1.Reps -> MemoTickReps (TickReps semantics), ev1._ridge -> raising, inside try/finally. -> ev2's output."""
    from auditory_alignment_v2 import evaluate as ev2
    if not isinstance(frozen, BR.FrozenBridge) or frozen.tau is None:
        raise TypeError("frozen_evaluate: a FrozenBridge with its temperatures is required")
    memo = {} if memo is None else memo
    calls = {"readouts": 0, "reps": 0}

    def readouts(objective, reps, train_segs, rng, **kw):
        if len(train_segs):
            raise BR.ZeroShotAccessError(f"ev1 handed {len(train_segs)} target training segments to the readout of a zero-shot "
                                         "evaluation (train_p must be empty)")
        if objective != frozen.objective:
            raise ValueError(f"ev1 readout objective {objective!r}; the frozen bridge is {frozen.objective!r}")
        calls["readouts"] += 1
        return frozen

    def reps(enc_, aud_, bt_, **kw):
        if enc_ is not enc or aud_ is not head or bt_ is not bt:
            raise RuntimeError("frozen_evaluate: ev1 built representations of another encoder, head or batcher")
        calls["reps"] += 1
        return MemoTickReps(enc_, aud_, bt_, memo, **kw)

    orig = (ev1.Reps, ev1.Readouts, ev1._ridge)
    ev1.Reps, ev1.Readouts, ev1._ridge = reps, readouts, _ridge_forbidden
    try:
        out = ev2.evaluate_continuous(b, enc, head, bt, coh, calib, None)
    finally:
        ev1.Reps, ev1.Readouts, ev1._ridge = orig
    if calls["readouts"] != 1 or calls["reps"] != 1:
        raise RuntimeError(f"frozen_evaluate: ev1 built {calls['readouts']} readouts and {calls['reps']} representation sets (expected 1)")
    return out


def _check_purity(bt, coh):
    acc = bt.training_access(coh)
    bad = []
    if not bt.zero_shot or bt.train_p:
        bad.append(f"train_p {sorted(bt.train_p)}")
    if bt.fit or bt.es:
        bad.append(f"{len(bt.fit)} fit / {len(bt.es)} early-stopping segments")
    if acc["train_segs"] or acc["es_queries"] or acc["train_participants"]:
        bad.append(f"ev1 would read {acc['train_segs']} training segments and {acc['es_queries']} early-stopping queries")
    if bad:
        raise BR.ZeroShotAccessError("zero-shot batcher with target training access: " + "; ".join(bad))
    return acc


def evaluate_zero_shot(row, manifest, dev, enc, bridge, *, root=None):
    """The §2.13 zero-shot evaluation of one row (module docstring) -> dict with eval, eval_uni_cal and the record fields (mode,
    access, coverage, purity, view / pool sha256, temperatures used, tensor map)."""
    s = row.get("spec") or {}
    ds = row.get("dataset")
    if ds == "private_bdf":
        raise ValueError(PRIVATE_NO_ZS)
    if ds not in V.TARGET_COHORTS:
        raise ValueError(f"zero-shot target {ds!r} is not a public target cohort {V.TARGET_COHORTS}")
    mode = canonical_mode(s.get("mode"))
    if ds not in C.ZS_COHORTS[mode]:
        raise ValueError(f"zero-shot mode {mode} is defined for {list(C.ZS_COHORTS[mode])}, not {ds!r} (§2.13)")
    if s.get("view") is not None and s["view"] != VIEW_RULE:
        raise ValueError(f"spec.view {s['view']!r}: this code implements {VIEW_RULE!r}")
    if s.get("objective") != bridge.objective:
        raise ValueError(f"row objective {s.get('objective')!r}, bridge objective {bridge.objective!r}")
    bm = bridge.meta or {}
    if bm.get("target") not in (None, ds) or bm.get("manifest_sha256") not in (None, V.manifest_sha(manifest)):
        raise ValueError(f"the bridge was fitted for target {bm.get('target')!r} on manifest {str(bm.get('manifest_sha256'))[:16]}, not "
                         f"{ds!r} on {str(V.manifest_sha(manifest))[:16]}")
    dev = torch.device(dev)
    b = core.bind(BR.bindable(row))
    sf, cf = int(b["subject_fold"]), int(b["content_fold"])
    cell = V.manifest_cell(manifest, ds, sf, cf)
    if s.get("split_hash") is not None and s["split_hash"] != cell.get("split_hash"):
        raise ValueError(f"spec.split_hash {str(s['split_hash'])[:16]}... is not the manifest cell's {str(cell.get('split_hash'))[:16]}...")
    root = V.manifest_root(manifest, root)

    coh = V.target_view(ds, cf, manifest, mode, root=root)          # every participant of the cohort (adapted rows' loader)
    meta, layout, parts = dict(coh.meta), list(coh.layout), coh.participants
    bt = V.TickBatcher(coh, b["spec"], b, dev, manifest, train_p=set())
    acc = _check_purity(bt, coh)
    n_pool = len(V.pool_of(coh, "test", "ss")[1])
    q_ids = {parts[i]["id"] for i in V.test_queries(coh, sf)}
    test_ids = set(map(str, cell["test"])) | set(map(str, cell.get("test_only", ())))
    if not q_ids or not q_ids <= test_ids:
        raise BR.ZeroShotAccessError(f"zero-shot queries {sorted(q_ids - test_ids)[:5]} are not test participants of the cell")

    enc_t, tmap = BR.donor_encoder(enc, manifest, ds, dev, layout=layout)
    head = M.fixed_heads(manifest, root)["env"].to(dev).eval()
    calib = {"sigma_u": float(bridge.sigma_u), "sigma_v": float(bridge.sigma_v)}
    memo, evs, used = {}, {}, {}
    for view in BR.VIEWS:
        fb = BR.FrozenBridge.from_bridge(bridge, n_pool, view)
        out = frozen_evaluate(b, enc_t, head, bt, coh, fb, calib, memo)
        rd = out["readout"]
        if rd["n_test_candidates"] != n_pool:
            raise RuntimeError(f"n_test_candidates {rd['n_test_candidates']} differs from the view's test pool {n_pool}")
        if set(out["per_participant"]) != q_ids:
            raise RuntimeError("the evaluated participants differ from the fold's test queries")
        if rd["tau"] != fb.tau:
            raise RuntimeError("the evaluation's temperatures are not the frozen bridge's")
        rd.update({"frozen": True, **fb.info})
        evs[view], used[view] = BR.jsonable(out), {**fb.info, "tau": fb.tau, "alpha_unified": fb.alpha_uni}

    cov = tmap["coverage"]
    man_cov = (manifest.get("coverage") or {}).get(ds)
    if man_cov is not None and (int(man_cov.get("n_seen", -1)) != cov["n_seen"] or sorted(man_cov.get("unseen") or []) != sorted(cov["unseen"])):
        raise ValueError(f"zero-shot channel coverage {cov} differs from the manifest's {man_cov}")
    pp = evs["primary"]["per_participant"]
    coverage = {"channels": {"n_seen": cov["n_seen"], "n_total": cov["n_total"], "closed_unseen": list(tmap["closed_unseen"]),
                             "rule": "names no donor saw carry zero weight and are never read (§2.4, §2.13)"},
                "masked_channels": {q["id"]: len(q.get("masked") or ()) for q in parts if q["id"] in q_ids and q.get("masked")},
                "participants_loaded": len(parts), "query_participants": len(q_ids),
                "test_only_queries": sorted(q["id"] for q in parts if q["id"] in q_ids and q.get("test_only")),
                "n_test_candidates": n_pool,
                "n_queries": int(sum(r["unified/regular"]["n_queries"] for r in pp.values())),
                "attention_participants": len(evs["primary"].get("attention_2afc") or {}),
                "segments_in_view": meta.get("n_segments"), "segments_meeting_shared_audio": meta.get("n_segments_meeting_shared_audio")}
    purity = {"view": VIEW_RULE, "train_p": [], "train_participants": acc["train_participants"], "train_segs": acc["train_segs"],
              "es_queries": acc["es_queries"], "fit_segments": acc["fit_segments"], "es_segments": acc["es_segments"],
              "readouts": "FrozenBridge (ev1.Readouts.__init__ bypassed; calibrate raises)", "ev1_ridge": "patched to raise",
              "reps": "TickReps (memoised)", "queries": "the fold's participants and test_only sessions (ev1)"}
    return BR.jsonable({
        "eval": evs["primary"], "eval_uni_cal": evs["uni_cal"], "mode": mode, "mode_name": C.ZS_MODE_NAME[mode],
        "normalisation_access": access_of(ds, mode, manifest), "view_sha256": meta.get("view_sha256"), "pool_sha256": meta.get("pool_sha256"),
        "view": {k: meta.get(k) for k in ("dataset", "content_fold", "mode", "cache", "contract", "manifest_sha256", "content_sha256",
                                          "pool_sha256", "view_sha256", "n_segments", "n_participants", "target_starts")},
        "split_hash": cell.get("split_hash"), "coverage": coverage, "zero_shot": purity, "temperatures_used": used,
        "native_readout": {"kind": bridge.native, "applicable": bool(bridge.native_applicable),
                           "note": None if bridge.native_applicable else
                           "not applicable: an NCE encoder never trained against v (§2.11); ev1's native metrics are kept in eval"},
        "kernel_dependence_sigma": calib, "tensor_map": tmap, "bridge": BR.bridge_row_info(bridge)})
