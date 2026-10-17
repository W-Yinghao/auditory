"""E34_PUBLIC_PRIOR donor training (module M5; private/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN.md §2.6-§2.10, §2.14, §2.15,
§2.16, §4.3, §6.1 `donor_train.py`, §6.6 M5; contract aln33_env64_125ms_v1): one lockstep donor-group unit, its group-synchronous
stable-then-decay horizon, the calibrated donor-dev selection score, the member checkpoints and the per-validation resume.

Interface (design §6.6 M5)
  train_donor_group(row, manifest, dev, ckpt_prefix, log, max_steps=None, *, upstream=None, cleanup=True) -> log
      Trains every member of the group row in lockstep on ONE batch stream (sampler.DonorSampler): identical initialisation
      (model.build_shared from donor_seed for every member), one Batch per step for every member, equal steps; XM's view 2 is the
      sampler's derangement (sampler.derangement / xm_view, its own generator). Fills `log` with the group-record fields (below)
      and returns it. ckpt_prefix = <out>/ckpt/<gid>. max_steps caps the main-run steps (probes only; the record says truncated).
      upstream: resolve_upstreams(row, out) (run_donor passes it; resolved here from ckpt_prefix when omitted). cleanup=True
      deletes the two resume files once `log` is filled (standalone callers, probes); run_donor passes cleanup=False and deletes
      them with remove_resume_files only after core.write_record has written the complete record, so a failure between the end
      of training and the record never discards the trajectory (the retry finds a resume marked done and only redoes the
      post-training scores and the record).
  remove_resume_files(out, gid)        deletes ckpt/<gid>_resume.pt and ckpt/<gid>_wsd_resume.pt (and their .tmp files).
  dev_scores(u_fit, y_fit, u_q, y_cand, own, other=None) -> {ce_bits, gain, r_own, tau, n_cand, ...}
      §2.10: ridge U -> standardised y on the fixed fit segments (relative penalty 1e-2 * mean diag(U^T U), intercept, no search),
      unified score S(q, c) = mean over the 8 dimensions of the Pearson r over the segment's 250 ticks (ev1._zt semantics),
      CE = min over tau in logspace(-3, 2, 41) * sd(S) of the mean -log2 softmax(S(q, .) / tau)[own(q)] (bits), the gain sensitivity
      mean S(q, own) - S(q, o(q)), r_own = mean S(q, own), tau* and the candidate count.
  GroupWSD(anchors_per_ep_eq, ...)    the schedule state machine: constant lr, linear decay to 0 over the final 3 ep-eq of the
      current horizon H (H0 = 30); at each decay start H - 3 the group extends H by 10 ep-eq for ALL members when any contract
      member (AP, XP, J1, J025; never XM) has the first minimum of its stable-phase CE_dev curve within its last 3 stable-phase
      validations (improving(); a flat curve does not improve); the first extension also runs the 30-ep-eq decay as a side branch
      from the saved stable state (the exact equal-update _h30 models); the compute limit L (60; spec.budget.continuation) makes a
      still-firing trigger at L - 3 decay to L, set ceiling_reached_while_improving and retain the stable states (a registered
      continuation, limit 90, resumes from them); rich and CSX groups adopt the realised H* of their core group
      (spec.horizon_from), with the same side branch and the core's ceiling flag, and run no trigger of their own.
  resolve_upstreams(row, out)          the horizon group (record, H*, stream hashes; rich: the core AP _best.pt), the continuation
      source (record, retained stable states); MissingDependency when a file or record is absent.
  DevValidator(manifest, device, env_head)  the fixed §2.10 score set (sampler.selection_sets): the fit segments, the dev queries
      with their unique content candidates, and (descriptive, after training only) the bridge_cal queries and candidates.

Files (select.py names them): ckpt/<gid>_m<M>_best.pt (min CE_dev over all validations, side branch included),
_gainsel_best.pt (max dev gain), _h30_best.pt (min CE_dev over the fixed 30-ep-eq recipe: stable validations <= 27 ep-eq and the
30-ep-eq decay, main run or side branch), ckpt/<gid>_m<M>_stable<L-3>.pt (only at the compute limit while improving; never
offloaded), ckpt/<gid>_resume.pt (every validation; tmp + os.replace) and ckpt/<gid>_wsd_resume.pt (the stable snapshot while a
side branch runs); both resume files are deleted at the end of the unit (by run_donor after the record is written, or by
train_donor_group with cleanup=True). Every file holds only tensors, dicts, lists, strings and numbers
(torch.load(weights_only=True) reads them); member checkpoints keep the encoder state under "enc" (model.load_donor and
build_target_encoder accept that form), the fixed audio head under "head" and the bandwidths under "sigma".

Group record fields written into `log` (prior33_interfaces_M11.md; select.py pins members[M]["best"]["ce_dev"]):
  members[M] = {best | h30 | gainsel: {ce_dev, gain, bridge_cal_ce, bridge_cal, ep_eq, step, branch, phase, r_own, tau, n_cand,
               ...}, identical {best_h30, best_gainsel, h30_gainsel}, steps, updates, nonfinite_steps, side_branch, loss, lambda,
               sigma, curve, checkpoints}
  horizon_ep_eq (H*), ceiling_reached_while_improving, compute_limit_ep_eq, trigger_log, side_branch, schedule, budget,
  steps_by_phase, ep_eq_used, stream {hash_log, final, final_step, core_check}, shares (strata, presentations, families), xm,
  timing (member_train_s per member), flop_proxy (per member), joint_extra_compute, compute_this_run, compute_inherited, terms,
  selection, selection_level, sampler, score_sets, retained_states, rich_readout (rich groups), truncated, resumed, inherited
  (continuations), determinism. run_donor adds joint_choice (select.joint_choice), gain_rule and the runner fields.

Interpretations (each is a deviation of the M5 summary)
- Budget: steps_at(E) = ceil(E * anchors_per_ep_eq / 256) for integer E (anchors_per_ep_eq = 8 N_SK from the manifest), so
  steps_at(30) = manifest budget.S0 (asserted); validations at every integer ep-eq of the branch (the decay ends are integers).
  No validation at step 0. The lr of step t in a decay [a, b) = [steps_at(H - 3), steps_at(H)) is 1e-3 * (b - t) / (b - a) (so
  the step after the last one would have lr 0).
- Trigger: a member "improves" when the first minimum of its stable-phase CE_dev curve (main run, constant lr, ep-eq 1 .. H - 3;
  non-finite = +inf) lies within the last 3 entries, i.e. min(last 3) < min(all earlier entries): a tie with an earlier entry does
  not count, so a flat curve (e.g. a collapsed encoder, which scores about log2(n_cand), the same value at every validation while
  its weights stay put) never extends the group.
  The design's "the best ... lies within the last 3" is ambiguous on ties; the inherited contract settles it (EXECUTION §7:
  开发曲线仍有改进可以按统一规则续训; yaml budget.continue_when_donor_dev_improves): a flat curve does not improve. No tolerance is
  applied (the rule names none). With 3 or fewer entries the earlier part is empty and any finite value counts (never reached: the
  first decision sees 27 entries). The side branch runs exactly once, at the first extension (always at H = 30). The rich and CSX
  groups run the side branch when H* > 30, so APR / APC / XPC also have equal-update _h30 models; their stable states are retained
  when their core group reached its ceiling.
- h30 candidates: a validation is eligible when it is on the side branch, or on the main run before any extension at ep-eq <= 30;
  main-run validations after the first extension are not (they are not on the 30-ep-eq recipe). Ties keep the earlier validation;
  the first validation is always taken, so every checkpoint exists even if a member's scores are non-finite (+inf / -inf).
- Gain rule (sensitivity of the lambda choice; run_donor records it): the joint member whose _gainsel_best.pt has the higher dev
  gain, J025 only when higher by >= 1e-4 (gain units), ties to J1 (GAIN_RULE). bridge_cal_ce: the same calibrated CE on the
  bridge_cal queries against the bridge_cal content candidates, the ridge refitted on the fit segments, computed once per distinct
  checkpoint state after training (descriptive; the training loop never reads bridge_cal).
- Montage masks: the sampler zeroes every unread (piece, channel) cell and every channel outside the montage subset in both views,
  so the encoder is called without mask= (identical output and gradient; tested); validation windows have the masked cells zeroed
  from the bank masks.
- CS bandwidths: losses.calibrate_sigma on the initial encoder (identical for every member) over sampler.calibration_batches()
  (seed + 99, one batch per stratum, drawn like training batches), stratum-weighted: sigma_u from [u1; u2], sigma_v from the audio
  rows; for APR also per rich head on the rows whose rich target is present (strata without such rows are left out and the weights
  renormalised). Computed for NCE groups as well (diagnostics only: cs_diag, kernel statistics).
- Validation diagnostics (every validation, every member): u_eff_rank and kernel_u (auditory_alignment.train helpers) on the dev
  queries, true / mismatched dev CS (ev1.test_cs_dependence at the group bandwidths, fixed generator), and the training-loss means
  of the interval (total and per term), grad-norm mean, nonfinite count, lr.
- Non-finite steps: a member whose EEG outputs, loss or gradient norm is non-finite skips that step's update (no optimiser
  step, counted in nonfinite_steps); its step count still advances (equal steps).
- Continuation (spec.continuation_of): the run starts from the source's retained stable states at L_src - 3 (models, optimisers,
  sampler and derangement generators, curves, best states, counters), re-applies the decision at that validation under its own
  limit, and continues; it therefore follows exactly the trajectory a run with the larger limit would have followed. Its
  checkpoints start as copies of the inherited best states. The source must be a complete, untruncated record of the same
  family, members, dataset, seed, objective and block that reached its ceiling while improving under a smaller limit (the
  sampler's own state check adds dataset, seed, block and manifest); run_donor records whether the source's code_hash equals this
  unit's (dependency.continuation.code_hash_equal; recorded, not refused: a later fix may legitimately change the code).
- Compute (EXECUTION §7: joint 同时算两种损失，报告实际GPU时间/FLOPs代理，不能声称计算完全相同; design §2.9): timing.member_train_s holds
  every member's synchronised step seconds by phase (both views' forward, the loss terms, backward, clip and AdamW;
  torch.cuda.synchronize before and after each member's step on CUDA, where the step already synchronises on its finite checks),
  so a joint member's second term shows as its difference to AP and XP (joint_extra_compute). flop_proxy counts matmul and
  convolution FLOPs with torch.utils.flop_counter (elementwise, reduction, indexing and cdist ops are not counted), measured once
  per process on each stratum's calibration batch: the encoder's forward + backward per window (the shared encoder; for APR the
  trunk, the envelope projection and both rich heads) and each member's loss terms forward + backward at the batch shape (unit
  rows from a fixed generator; XM on a fixed cyclic derangement view), so flops_per_step[M][stratum] = 512 windows x encoder +
  loss terms, and train_flops_proxy[M] = the sum over strata of the realised group steps (main run and side branch) x
  flops_per_step; validation: forward FLOPs per window (full SparrKULee montage) x validation windows.
- Continuation compute: counters, timing and FLOP totals of a continuation record are cumulative over the inherited trajectory
  (they continue the source's). compute_inherited holds the part restored from the source's stable state and compute_this_run the
  part this version ran (primary groups: compute_this_run = the totals, compute_inherited = None), so compute summed over records
  uses compute_this_run.
- lambda: 1.0 and 0.25 for J1 and J025, None for every other member (records and checkpoints). identical: members[M].identical
  says which of _best / _h30 / _gainsel hold the same validation (§7.1 item 11, "identical epochs are recorded as identical").
- Resume consistency: a validation writes its checkpoint files before the resume save that follows it. A resume therefore
  rewrites every recorded best checkpoint from the resume file and removes this group's stable files when the resumed state has
  retained none (a fresh start removes stale ones too), so a replayed validation that is not bit-exact (CUDA) never leaves a file
  holding a state the record does not name.
- Upstream checks for adopted horizons: the horizon group must be a complete DONOR record of the same (dataset, objective, seed)
  and compute limit and of the same version (a primary group adopts a primary core group; a continuation adopts the continuation
  of its source's core group), with an integer H* on the grid 30 + 10 k; a rich group asserts its stream hash against the core
  record at every 1,000 steps and at the end (StreamMismatch, i.e. technical_failed).
- Bandwidths are calibrated at the start of every process and then replaced by the values a resume file or a retained stable
  state carries (the record says whether they were equal), so a resumed run or a continuation uses exactly its source's sigma.
- Repeatability: on the CPU a resumed run equals the uninterrupted one bit for bit (tested). On CUDA (determinism field):
  cudnn.deterministic (benchmark off), torch.use_deterministic_algorithms(True, warn_only=True) with CUBLAS_WORKSPACE_CONFIG
  ":4096:8" (set when absent, before the process's first cuBLAS call) and no NaN fill of uninitialised memory, so the window
  gather's backward uses the sorted (deterministic) accumulation; a resume on the same GPU model is then expected to repeat the
  weights exactly (to be confirmed by the §7.2 probe, M12), a resume on another model of the pool (V100, A30, A40, L40S) is not,
  and every resume entry records the device. warn_only keeps an op without a deterministic kernel from failing the unit (it warns).
- Non-finite numbers: bridge_cal is scored without o(q), so its sub-dict carries no gain; run_donor writes every remaining
  non-finite number of the record as null (counted in nonfinite_to_null) except members[M].best.ce_dev, which select.py pins as a
  JSON number (NaN only when every validation of that member was non-finite).
- select.py is imported here and by run_donor at run time (checkpoint names, compute limit, lambda rule): the prior33_donor and
  prior33_rich_donor code groups must hash it (a deviation from design §6.3, for M9). rich.py is imported only when the group
  trains APR, so the core and CSX groups never execute it.
"""
from __future__ import annotations

import copy
import math
import os
import re
import time

import numpy as np
import torch

from auditory_alignment.evaluate import LN2, _zt
from auditory_alignment.train import _eff_rank, _kernel_stats, _save_resume

from . import contract as C
from . import losses as L
from . import model as MD
from . import sampler as SM
from . import select as SEL
from . import views as V

# ---------------------------------------------------------------------------------------------------------- constants (§2.6-§2.10, §4.3)
LR, WEIGHT_DECAY, CLIP = 1e-3, 1e-4, 5.0
TEMPERATURE = C.TAU
BANDWIDTH_MULTIPLIER = 1.0
LAMBDA = {"J1": 1.0, "J025": 0.25}
KIND = {"AP": "audio_pair", "XP": "cross_person", "J1": "joint", "J025": "joint", "XM": "xm", "APR": "rich", "APC": "audio_pair",
        "XPC": "cross_person"}
TRIGGER_MEMBERS = ("AP", "XP", "J1", "J025")              # XM never triggers; it follows the group horizon
H0, EXT, LAST = 30, 10, 3
DECAY = SEL.DECAY_EP_EQ                                   # 3 ep-eq; the stable state kept at the limit L is the one at L - 3
CONTINUATION_RULE = "group_wsd_any_last3_ext10_limit60_v1"
_RULE = re.compile(r"^group_wsd_any_last(\d+)_ext(\d+)_limit(\d+)_v1$")
TAU_GRID = np.logspace(-3, 2, 41)
REL_RIDGE = 1e-2
SELECTION = {"primary": "donor_dev_ce_calibrated_v1", "sensitivity": "donor_dev_gain_v1"}
GAIN_RULE, GAIN_TIE = "max_dev_gain_gainsel_tie1e-4_lambda1", 1e-4
SELECTION_LEVEL = "donor dev: SparrKULee participants and content families disjoint from donor fit (new listeners, new content)"
BATCH = {"segments": SM.N_SEG, "anchors": C.N_ANCHORS, "views": 2}
MONTAGE_AUG, CONTROL = "subset3_p05_v1", "xm_task_state_matched_derangement_v1"
RICH_TARGETS, RICH_LOSS_WEIGHTS = {"ss": "whisper_logmel_pca4_sk_v1", "sc": "flux_pca4_v1"}, [1.0, 0.5, 0.5]
OPTIMIZER = {"name": "AdamW", "lr": LR, "weight_decay": WEIGHT_DECAY, "clip": CLIP}
CKPT_FORMAT, RESUME_FORMAT = "prior33_donor_member_v1", "prior33_donor_group_resume_v1"
WSD_FORMAT, STABLE_FORMAT = "prior33_donor_wsd_snapshot_v1", "prior33_donor_stable_state_v1"
CS_DIAG_SEED = 20261019                                   # fixed generator of the dev cs_diag subsample (same for every member)
FLOP_SEED, FLOP_WINDOWS = 20261020, 4                     # FLOP proxy: generator of the synthetic loss rows; windows per encoder count
CUBLAS_CONFIG = ":4096:8"                                 # CUBLAS_WORKSPACE_CONFIG for deterministic cuBLAS (set when absent)
VAL_CHUNK = {"cuda": 64, "cpu": 8}                        # validation segments per forward chunk (x 250 ticks)
KINDS = ("best", "gainsel", "h30")
GROUP_BLOCK = {SEL.DONOR: ("core", "panel"), SEL.RICH_DONOR: ("rich",), SEL.CSX_DONOR: ("csx",)}
TERMS = {
    "NCE": {"audio_pair": {"rows": "2B = 512 EEG rows (both views) against the B = 256 audio rows; audio->EEG: 256 queries over the 512 "
                                   "EEG rows (2 positives each)",
                           "averaging": "(mean over the 512 EEG->audio queries + mean over the 256 audio->EEG queries) / 2",
                           "function": "losses.nce_audio_pair"},
            "cross_person": {"rows": "B = 256 view-1 rows against B = 256 view-2 rows (bipartite, both directions)",
                             "averaging": "(mean over the 256 1->2 queries + mean over the 256 2->1 queries) / 2",
                             "function": "losses.nce_cross_person (XM: view 2 = X2[pi] with X1's keys)"}},
    "CS_SINGLE": {"audio_pair": {"rows": "2B = 512 rows (u_r, v_a(r)), v repeated", "averaging": "one full-kernel estimate per batch",
                                 "function": "losses.cs_audio_pair"},
                  "cross_person": {"rows": "2B = 512 rows ([u1; u2], [u2; u1]), sigma_u on both sides",
                                   "averaging": "one full-kernel estimate per batch", "function": "losses.cs_cross_person"}}}


class MissingDependency(RuntimeError):
    """An upstream record or file that the donor group reads is absent."""


class StreamMismatch(RuntimeError):
    """A rich group's batch stream differs from its core group's (§2.15: technical_failed)."""


# ---------------------------------------------------------------------------------------------------------- small helpers
def _py(o):
    """JSON- and weights_only-safe copy: numpy scalars / arrays and tuples become Python numbers and lists."""
    if isinstance(o, dict):
        return {str(k): _py(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_py(v) for v in o]
    if isinstance(o, np.ndarray):
        return _py(o.tolist())
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    return o


def _cpu(o):
    """Detached CPU clones of every tensor in a nested dict / list / tuple."""
    if torch.is_tensor(o):
        return o.detach().to("cpu", copy=True)
    if isinstance(o, dict):
        return {k: _cpu(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_cpu(v) for v in o]
    if isinstance(o, tuple):
        return tuple(_cpu(v) for v in o)
    return o


def _state(module):
    return {k: v.detach().to("cpu", copy=True) for k, v in module.state_dict().items()}


def _save(path, obj):
    torch.save(obj, path + ".tmp")
    os.replace(path + ".tmp", path)


def _load(path, device="cpu"):
    return torch.load(path, map_location=device, weights_only=True)


def _finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _lam(member):
    """The joint weight lambda of a member for records and checkpoints: 1.0 / 0.25 for J1 / J025, None otherwise."""
    return None if member.lam is None else float(member.lam)


def _ce_key(v):
    """Minimisation key of a CE value: NaN, infinities and non-numbers count as +inf."""
    return float(v) if _finite(v) else math.inf


def _gain_key(v):
    return float(v) if _finite(v) else -math.inf


def _sync(device):
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def _clock(device):
    """perf_counter after the device's queued work has finished (synchronised member timing)."""
    _sync(device)
    return time.perf_counter()


def _device_name(device):
    if device.type == "cuda":
        try:
            return torch.cuda.get_device_name(device)
        except Exception:  # noqa: BLE001 (descriptive only)
            return "cuda (name unavailable)"
    return device.type


def determinism(device):
    """Set the deterministic-kernel switches of the process for a CUDA device (module docstring, Repeatability) and return the
    record's determinism field; on the CPU nothing is set (the kernels used here are deterministic). Called before the first
    cuBLAS call of the unit's process (each unit is its own process), so CUBLAS_WORKSPACE_CONFIG takes effect."""
    if device.type != "cuda":
        return {"device_type": device.type, "deterministic_algorithms": bool(torch.are_deterministic_algorithms_enabled()),
                "note": "CPU: deterministic kernels; a resumed run equals the uninterrupted one bit for bit (tested)"}
    preset = os.environ.get("CUBLAS_WORKSPACE_CONFIG")
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", CUBLAS_CONFIG)
    torch.backends.cudnn.deterministic, torch.backends.cudnn.benchmark = True, False
    torch.use_deterministic_algorithms(True, warn_only=True)
    fill = None
    try:
        import torch.utils.deterministic as _tud
        _tud.fill_uninitialized_memory = False
        fill = bool(_tud.fill_uninitialized_memory)
    except Exception:  # noqa: BLE001 (older torch: the switch does not exist)
        pass
    return {"device_type": "cuda", "device": _device_name(device), "cudnn_deterministic": True, "cudnn_benchmark": False,
            "deterministic_algorithms": bool(torch.are_deterministic_algorithms_enabled()),
            "warn_only": bool(torch.is_deterministic_algorithms_warn_only_enabled()),
            "cublas_workspace_config": os.environ.get("CUBLAS_WORKSPACE_CONFIG"), "cublas_workspace_config_preset": preset,
            "fill_uninitialized_memory": fill, "cudnn_allow_tf32": bool(torch.backends.cudnn.allow_tf32),
            "matmul_allow_tf32": bool(torch.backends.cuda.matmul.allow_tf32),
            "note": "a resume on the same GPU model is expected to be exact (to be confirmed by the §7.2 probe); a resume on another "
                    "GPU model is not (resumed[].device)"}


# ---------------------------------------------------------------------------------------------------------- budget and rule
def steps_at(ep_eq, anchors_per_ep_eq, rows=SM.N_ROWS):
    """Stream step at the end of integer ep-eq E: ceil(E * anchors_per_ep_eq / rows) (§2.10: S0 = steps_at(30))."""
    e, a, r = int(ep_eq), int(anchors_per_ep_eq), int(rows)
    if e != ep_eq or e < 0 or a <= 0 or r <= 0:
        raise ValueError(f"steps_at: integer ep-eq >= 0 and positive sizes expected, got {ep_eq!r}, {anchors_per_ep_eq!r}, {rows!r}")
    return -(-e * a // r)


def parse_rule(group):
    """(last, ext, limit) of spec.budget.continuation ('group_wsd_any_last<k>_ext<e>_limit<L>_v1'; absent: 3, 10, 60). The limit
    agrees with select.compute_limit; any other rule text raises (a group never runs a rule it does not name)."""
    s = str((((group.get("spec") or {}).get("budget") or {}).get("continuation")) or CONTINUATION_RULE)
    m = _RULE.match(s)
    if m is None:
        raise ValueError(f"{group.get('experiment_id')}: spec.budget.continuation {s!r} is not a group_wsd_any_last<k>_ext<e>_limit<L>_v1 "
                         f"rule (§2.10, §4.3: {CONTINUATION_RULE})")
    last, ext, limit = (int(g) for g in m.groups())
    if limit != SEL.compute_limit(group):
        raise ValueError(f"{group.get('experiment_id')}: rule limit {limit} disagrees with select.compute_limit")
    return last, ext, limit


def improving(values, last=LAST):
    """§2.10 trigger test of one member: the FIRST minimum of its stable-phase CE_dev curve (non-finite = +inf) is finite and lies
    within its last `last` entries, i.e. min(last entries) < min(earlier entries) (min of none = +inf). A tie with an earlier entry
    does not count, so a flat curve does not improve (module docstring, Trigger)."""
    v = [_ce_key(x) for x in values]
    if not v:
        return False
    i = int(np.argmin(v))                                  # numpy's argmin returns the first minimum
    return math.isfinite(v[i]) and i >= len(v) - int(last)


def _best_pos(values, last=LAST):
    """Where the first minimum lies (the quantity improving() tests), for the trigger log."""
    v = [_ce_key(x) for x in values]
    if not v:
        return {"best_index": None, "best_ce": None, "last_window_start": None}
    i = int(np.argmin(v))
    return {"best_index": i, "best_ce": v[i] if math.isfinite(v[i]) else None, "last_window_start": max(len(v) - int(last), 0)}


class GroupWSD:
    """Group-synchronous stable-then-decay horizon of one donor group (§2.10). Pure logic (no torch): the training loop asks it for
    the lr, the phase and the h30 eligibility of a validation, and for the decision at each decay start."""

    def __init__(self, anchors_per_ep_eq, *, rows=SM.N_ROWS, h0=H0, decay=DECAY, ext=EXT, last=LAST, limit=SEL.DEFAULT_LIMIT_EP_EQ,
                 trigger=TRIGGER_MEMBERS, adopted=None, adopted_ceiling=False):
        self.A, self.rows = int(anchors_per_ep_eq), int(rows)
        self.h0, self.decay, self.ext, self.last, self.limit = int(h0), int(decay), int(ext), int(last), int(limit)
        if not (self.A > 0 and self.rows > 0 and self.h0 > self.decay >= 1 and self.ext >= 1 and self.last >= 1):
            raise ValueError(f"GroupWSD: invalid sizes (A {self.A}, rows {self.rows}, h0 {self.h0}, decay {self.decay}, ext {self.ext})")
        if self.limit < self.h0 or (self.limit - self.h0) % self.ext:
            raise ValueError(f"GroupWSD: the compute limit {self.limit} must be h0 + k * ext ({self.h0} + k * {self.ext}), so that the "
                             f"ceiling decay starts at limit - {self.decay} (the retained stable states, select.retained_states)")
        self.trigger = tuple(trigger)
        self.adopted = None if adopted is None else int(adopted)
        self.adopted_ceiling = bool(adopted_ceiling)
        if self.adopted is not None:
            if adopted != self.adopted or not (self.h0 <= self.adopted <= self.limit) or (self.adopted - self.h0) % self.ext:
                raise ValueError(f"GroupWSD: adopted horizon {adopted!r} is not on {self.h0} + k * {self.ext} within the limit {self.limit}")
            if self.adopted_ceiling and self.adopted != self.limit:
                raise ValueError(f"GroupWSD: an adopted ceiling needs H* = the limit ({self.adopted} vs {self.limit})")
        elif not self.trigger:
            raise ValueError("GroupWSD: a group without an adopted horizon needs trigger members")
        self.H, self.n_ext, self.side, self.ceiling, self.log = self.h0, 0, None, False, []

    def steps_at(self, E):
        return steps_at(E, self.A, self.rows)

    def ep_eq_of(self, step):
        return float(step) * self.rows / self.A

    def horizon(self, branch="main"):
        return self.side["end"] if branch == "side" else self.H

    def lr_scale(self, step, branch="main"):
        """1 in the stable phase; (b - step) / (b - a) in the decay [a, b) of the branch's horizon."""
        H = self.horizon(branch)
        a, b = self.steps_at(H - self.decay), self.steps_at(H)
        if step < a:
            return 1.0
        if not a <= step < b:
            raise ValueError(f"GroupWSD: step {step} outside the {branch} schedule (decay [{a}, {b}))")
        return (b - step) / (b - a)

    def phase(self, E, branch="main"):
        if branch == "side":
            return "side"
        return "stable" if E <= self.H - self.decay else "decay"

    def h30_eligible(self, E, branch="main"):
        return branch == "side" or (self.n_ext == 0 and E <= self.h0)

    def is_decay_start(self, E, branch="main"):
        return branch == "main" and E == self.H - self.decay

    def is_final(self, E, branch="main"):
        return branch == "main" and E == self.H

    def is_side_end(self, E, branch):
        return branch == "side" and self.side is not None and self.side["status"] == "active" and E == self.side["end"]

    def decide(self, E, stable_curves):
        """At the decay start E = H - 3 of the main run: extend (side branch at the first extension), decay, or ceiling (decay to
        the limit, retain the stable states, set the flag). stable_curves: {member: stable-phase CE_dev values in order}."""
        if E != self.H - self.decay:
            raise ValueError(f"GroupWSD.decide at {E}: the decay start is {self.H - self.decay}")
        if self.adopted is None:
            members = {m: {"improving": improving(stable_curves.get(m, ()), self.last), "n_stable": len(stable_curves.get(m, ())),
                           **_best_pos(stable_curves.get(m, ()), self.last)} for m in self.trigger if m in stable_curves}
            if not members:
                raise ValueError(f"GroupWSD.decide: no stable curve of the trigger members {list(self.trigger)}")
            fires = any(v["improving"] for v in members.values())
        else:
            members, fires = None, self.H < self.adopted
        H_before = self.H
        if fires and self.H + self.ext <= self.limit:
            decision, side = "extend", self.n_ext == 0
            if side:
                self.side = {"status": "active", "start": int(E), "end": int(self.H)}
            self.H += self.ext
            self.n_ext += 1
        elif (self.adopted is None and fires) or (self.adopted is not None and self.adopted_ceiling and self.H == self.adopted):
            decision, side = "ceiling", False
            self.ceiling = True
        else:
            decision, side = "decay", False
        entry = {"ep_eq": int(E), "H_before": int(H_before), "H_after": int(self.H), "decision": decision, "side_branch": side,
                 "fires": bool(fires), "limit": self.limit,
                 "rule": ("adopted horizon (horizon_from)" if self.adopted is not None else
                          f"any of {list(self.trigger)} with the first minimum of its stable-phase CE_dev within its last {self.last} "
                          f"stable validations (strictly below every earlier one; ties with an earlier validation do not count)"),
                 "members": members}
        self.log.append(_py(entry))
        return entry

    def end_side(self):
        if self.side is None or self.side["status"] != "active":
            raise ValueError("GroupWSD.end_side: no active side branch")
        self.side = {**self.side, "status": "done"}

    def state(self):
        return _py({"A": self.A, "rows": self.rows, "h0": self.h0, "decay": self.decay, "ext": self.ext, "last": self.last,
                    "limit": self.limit, "trigger": list(self.trigger), "adopted": self.adopted, "adopted_ceiling": self.adopted_ceiling,
                    "H": self.H, "n_ext": self.n_ext, "side": copy.deepcopy(self.side), "ceiling": self.ceiling,
                    "log": copy.deepcopy(self.log)})

    def load_state(self, st):
        """Restore H, extensions, side branch, ceiling and log; the schedule sizes must agree (the limit and the adopted horizon
        stay this object's: a continuation re-decides under its own)."""
        for k in ("A", "rows", "h0", "decay", "ext", "last"):
            if int(st[k]) != getattr(self, k):
                raise ValueError(f"GroupWSD.load_state: {k} {st[k]} differs from {getattr(self, k)}")
        if int(st["H"]) > self.limit:
            raise ValueError(f"GroupWSD.load_state: horizon {st['H']} above the limit {self.limit}")
        self.H, self.n_ext, self.ceiling = int(st["H"]), int(st["n_ext"]), bool(st["ceiling"])
        self.side = copy.deepcopy(st["side"])
        self.log = copy.deepcopy(st["log"])

    def describe(self):
        return {"h0_ep_eq": self.h0, "decay_ep_eq": self.decay, "extension_ep_eq": self.ext, "last_k": self.last,
                "compute_limit_ep_eq": self.limit, "anchors_per_ep_eq": self.A, "rows_per_step": self.rows,
                "steps_per_ep_eq": self.A / self.rows, "steps0": self.steps_at(self.h0), "trigger_members": list(self.trigger),
                "adopted_horizon": self.adopted, "adopted_ceiling": self.adopted_ceiling,
                "lr": "constant 1e-3 from step 0 (no warmup), then linear to 0 over the final 3 ep-eq of the current horizon",
                "rule": f"group_wsd_any_last{self.last}_ext{self.ext}_limit{self.limit}_v1"}


# ---------------------------------------------------------------------------------------------------------- scores (§2.10)
def calibrated_ce(S, own, taus=TAU_GRID):
    """min over tau in taus * sd(S) of the mean candidate cross-entropy -log2 softmax(S / tau)[own] -> (bits, tau*, tau* / sd)."""
    S = np.asarray(S, dtype=np.float64)
    own = np.asarray(own, dtype=np.int64)
    ar = np.arange(len(S))
    sd = float(S.std()) + 1e-12
    best = None
    for t in np.asarray(taus, dtype=np.float64) * sd:
        z = S / t
        z = z - z.max(1, keepdims=True)
        ce = float((np.log(np.exp(z).sum(1)) - z[ar, own]).mean()) / LN2
        if best is None or ce < best[0]:
            best = (ce, float(t))
    return best[0], best[1], best[1] / sd


def dev_scores(u_fit, y_fit, u_q, y_cand, own, other=None, *, rel_ridge=REL_RIDGE, taus=TAU_GRID):
    """The §2.10 donor-dev scores of one member (module docstring). u_fit [n_fit, T, d], y_fit [n_fit, T, D] (standardised targets
    y / sigma, mu = 0), u_q [n_q, T, d], y_cand [n_c, T, D]; own [n_q] the candidate index of each query; other [n_q] the
    candidate index of o(q) (-1: none) or None (no gain)."""
    Uf, Yf, Uq, Yc = (np.asarray(a, dtype=np.float64) for a in (u_fit, y_fit, u_q, y_cand))
    own = np.asarray(own, dtype=np.int64).reshape(-1)
    if Uf.ndim != 3 or Yf.ndim != 3 or Yf.shape[:2] != Uf.shape[:2] or Uq.ndim != 3 or Yc.ndim != 3 \
            or Uq.shape[1:] != Uf.shape[1:] or Yc.shape[1:] != Yf.shape[1:] or len(own) != len(Uq) or not len(Uq):
        raise ValueError(f"dev_scores: shapes u_fit {Uf.shape}, y_fit {Yf.shape}, u_q {Uq.shape}, y_cand {Yc.shape}, own {own.shape}")
    if own.min() < 0 or own.max() >= len(Yc):
        raise ValueError("dev_scores: own indexes the candidates")
    nq, T, d = Uq.shape
    out = {"n_q": int(nq), "n_cand": int(len(Yc)), "n_fit": int(len(Uf)), "rel_ridge": float(rel_ridge)}
    nan = {**out, "ce_bits": math.nan, "gain": math.nan, "r_own": math.nan, "tau": math.nan, "tau_rel": math.nan, "alpha": math.nan,
           "n_gain": 0, "tau_at_grid_edge": False, "nonfinite": True}
    if not (np.isfinite(Uf).all() and np.isfinite(Uq).all() and np.isfinite(Yf).all() and np.isfinite(Yc).all()):
        return nan
    X, Y = Uf.reshape(-1, d), Yf.reshape(-1, Yf.shape[2])
    alpha = float(rel_ridge) * float(np.einsum("nd,nd->d", X, X).mean())
    if not (math.isfinite(alpha) and alpha > 0):          # degenerate (all-zero) outputs: no readout; scored as non-finite (never best)
        return nan
    mx, my = X.mean(0), Y.mean(0)
    Xc = X - mx
    try:
        B = np.linalg.solve(Xc.T @ Xc + alpha * np.eye(d), Xc.T @ (Y - my))
    except np.linalg.LinAlgError:
        return nan
    P = (Uq - mx) @ B + my                                              # [n_q, T, D] reconstruction
    S = np.einsum("qtd,ctd->qc", _zt(P), _zt(Yc)) / (T * Yc.shape[2])    # mean over dimensions of the Pearson r over the ticks
    ce, tau, tau_rel = calibrated_ce(S, own, taus)
    ar = np.arange(nq)
    s_own = S[ar, own]
    gain, n_gain = math.nan, 0
    if other is not None:
        o = np.asarray(other, dtype=np.int64).reshape(-1)
        if len(o) != nq or o.max(initial=-1) >= len(Yc):
            raise ValueError("dev_scores: one o(q) per query, indexing the candidates (-1: none)")
        ok = o >= 0
        n_gain = int(ok.sum())
        if n_gain:
            gain = float((s_own[ok] - S[ar[ok], o[ok]]).mean())
    g = np.asarray(taus, dtype=np.float64)
    return {**out, "ce_bits": float(ce), "gain": gain, "r_own": float(s_own.mean()), "tau": float(tau), "tau_rel": float(tau_rel),
            "alpha": alpha, "n_gain": n_gain, "tau_at_grid_edge": bool(np.isclose(tau_rel, g[0]) or np.isclose(tau_rel, g[-1])),
            "nonfinite": False}


class DevValidator:
    """The fixed §2.10 score set of a seed (identical for every member and group): EEG of the fit segments, dev queries and bridge_cal
    queries from one SparrKULee "segments" bank (full montage, no augmentation, masked cells zero), standardised targets of the fit
    segments and of the dev / bridge_cal candidates, and the fixed audio head rows of the dev queries (cs_diag)."""

    def __init__(self, manifest, device, env_head, *, rich=False, chunk=None, root=None):
        self.device = torch.device(device)
        self.sets = SM.selection_sets(manifest)
        fit, dev, cal = self.sets["fit"], self.sets["dev"], self.sets["bridge_cal"]
        rows = np.unique(np.concatenate([fit.rows, dev["queries"].rows, cal["queries"].rows]))
        self.bank = V.DonorBank(manifest, "sparrkulee", ("fit", "dev", "bridge_cal"), self.device, rich=rich, root=root, segments=rows)
        self.sigma = np.asarray(manifest["standardiser"]["sigma"], dtype=np.float64)
        if self.sigma.shape != (C.N_TGT,) or not (np.isfinite(self.sigma).all() and (self.sigma > 0).all()):
            raise ValueError("DevValidator: the manifest standardiser sigma must be 8 finite positive values")
        self.chunk = int(chunk or VAL_CHUNK.get(self.device.type, 16))
        self.n_segments = len(fit) + len(dev["queries"])          # segments encoded per member and validation
        self.y_fit = self.targets(fit) / self.sigma
        self.y_dev = self.targets(dev["candidates"]) / self.sigma
        self.y_cal = self.targets(cal["candidates"]) / self.sigma
        with torch.no_grad():
            yq = torch.as_tensor(self.targets(dev["queries"]), dtype=torch.float32, device=self.device)
            self.v_dev = env_head(yq.reshape(-1, C.N_TGT)).reshape(len(dev["queries"]), C.SEG_TICKS, -1).double().cpu().numpy()
        n = len(dev["queries"])
        ticks = np.linspace(0, C.SEG_TICKS - 1, 8).round().astype(np.int64)
        self._diag_rows = (np.arange(min(n, 32))[:, None] * C.SEG_TICKS + ticks[None]).reshape(-1)

    def sizes(self):
        fit, dev, cal = self.sets["fit"], self.sets["dev"], self.sets["bridge_cal"]
        return {"fit_segments": len(fit), "dev_queries": len(dev["queries"]), "dev_candidates": len(dev["candidates"]),
                "dev_queries_with_other": int((dev["other"] >= 0).sum()), "bridge_cal_queries": len(cal["queries"]),
                "bridge_cal_candidates": len(cal["candidates"]), "ticks": C.SEG_TICKS, "bank": self.bank.describe(),
                "rows_sha": {k: _rows_sha(v) for k, v in (("fit", fit.rows), ("dev_queries", dev["queries"].rows),
                                                          ("bridge_cal_queries", cal["queries"].rows))}}

    def targets(self, sset, rich=False):
        """Envelope targets [n, 250, 8] of every tick (float64); rich=True: (y_ss [n, 250, 32], y_sc [n, 250, 8]), NaN where absent."""
        n = len(sset)
        offs = np.tile(C.TICK_OFFS.astype(np.int64), n)
        pres, s = np.repeat(sset.presentation, C.SEG_TICKS), np.repeat(sset.s, C.SEG_TICKS)
        if rich:
            ss, sc, ok = self.bank.rich_targets(pres, s, offs)
            ss, sc = ss.clone(), sc.clone()
            ss[~ok], sc[~ok] = float("nan"), float("nan")
            return ss.double().cpu().numpy().reshape(n, C.SEG_TICKS, -1), sc.double().cpu().numpy().reshape(n, C.SEG_TICKS, -1)
        return self.bank.targets(pres, s, offs).double().cpu().numpy().reshape(n, C.SEG_TICKS, C.N_TGT)

    @torch.no_grad()
    def encode(self, encs, sset):
        """{name: u [n, 250, 32] float64} of every encoder on every tick of the segment set (one gather per chunk for all)."""
        out = {k: [] for k in encs}
        for e in encs.values():
            e.eval()
        lay = self.bank.layout
        for i0, i1, x, _ in self.bank.iter_ticks(sset.piece, sset.s, sset.presentation, chunk=self.chunk):
            keep = torch.as_tensor(np.repeat(self.bank.mask[sset.piece[i0:i1]], C.SEG_TICKS, axis=0), device=x.device)
            x.masked_fill_(~keep[:, :, None], 0)
            for name, enc in encs.items():
                out[name].append(enc(x, layout=lay).double().cpu().numpy())
        n = len(sset)
        return {k: np.concatenate(v).reshape(n, C.SEG_TICKS, -1) for k, v in out.items()}

    def validate(self, encs, sigma):
        """{name: {"dev": dev_scores, "diag": {...}}} of the encoders on the fixed set (eval mode, no gradient)."""
        fit, dev = self.sets["fit"], self.sets["dev"]
        Uf, Uq = self.encode(encs, fit), self.encode(encs, dev["queries"])
        return {name: {"dev": dev_scores(Uf[name], self.y_fit, Uq[name], self.y_dev, dev["own"], dev["other"]),
                       "diag": self._diag(Uq[name], sigma)} for name in encs}

    def bridge_cal(self, encs):
        """{name: the calibrated CE of the bridge_cal queries among the bridge_cal content candidates} (descriptive)."""
        fit, cal = self.sets["fit"], self.sets["bridge_cal"]
        Uf, Uc = self.encode(encs, fit), self.encode(encs, cal["queries"])
        return {name: dev_scores(Uf[name], self.y_fit, Uc[name], self.y_cal, cal["own"], None) for name in encs}

    def _diag(self, Uq, sigma):
        from auditory_alignment import evaluate as ev1
        rows = torch.as_tensor(Uq.reshape(-1, Uq.shape[-1]))
        su, sv = sigma.get("sigma_u"), sigma.get("sigma_v")
        if not torch.isfinite(rows).all():
            return {"u_eff_rank": None, "kernel_u": None, "nonfinite": True}
        d = {"u_eff_rank": _eff_rank(rows), "kernel_u": _kernel_stats(rows[torch.as_tensor(self._diag_rows)], su) if su else None}
        if su and sv and len(Uq) >= 2:
            cs = ev1.test_cs_dependence(Uq, self.v_dev, {"sigma_u": su, "sigma_v": sv}, np.random.default_rng(CS_DIAG_SEED))
            d.update({"dev_cs_true_nats": cs["cs_true_nats"], "dev_cs_mismatched_nats": cs["cs_mismatched_nats"],
                      "dev_cs_true_minus_mismatched": cs["cs_true_minus_mismatched"], "dev_cs_rows": cs["n_rows"]})
        return _py(d)


def _rows_sha(rows):
    import hashlib
    return hashlib.sha256(np.ascontiguousarray(np.asarray(rows, dtype=np.int64)).tobytes()).hexdigest()[:16]


# ---------------------------------------------------------------------------------------------------------- bandwidths (§2.8)
@torch.no_grad()
def calibrate_bandwidths(enc, sampler, heads, *, rich=False, multiplier=BANDWIDTH_MULTIPLIER, batches=None):
    """sigma_u (from [u1; u2]) and sigma_v (audio rows) of the initial encoder over one calibration batch per stratum (seed + 99),
    stratum-weighted (losses.calibrate_sigma); rich=True adds sigma_u / sigma_v per rich head on the rows with a present target.
    batches: sampler.calibration_batches() when already drawn (the same batches; the draw uses its own generator)."""
    enc.eval()
    w = dict(zip(sampler.strata, (float(x) for x in sampler.weights)))
    U, Vv, ws, rr = [], [], [], {"ss": ([], [], []), "sc": ([], [], [])}
    per = {}
    for s, b in (sampler.calibration_batches() if batches is None else batches).items():
        if rich:
            from . import rich as R
            uh = R.eeg_heads(enc, b.x1, b.x2, b.layout)
            u1, u2 = uh["env"]
            m = b.rich_mask
            for h in ("ss", "sc"):
                if int(m.sum()) >= 2:
                    rr[h][0].append(torch.cat([uh[h][0][m], uh[h][1][m]]))
                    rr[h][1].append(heads[h](b.rich[h][m]))
                    rr[h][2].append(w[s])
        else:
            u1, u2 = enc(b.x1, layout=b.layout), enc(b.x2, layout=b.layout)
        U.append(torch.cat([u1, u2]))
        Vv.append(heads["env"](b.y))
        ws.append(w[s])
        per[s] = {"rows_u": int(len(U[-1])), "rows_v": int(len(Vv[-1]))}
    out = {"sigma_u": L.calibrate_sigma(U, ws, multiplier), "sigma_v": L.calibrate_sigma(Vv, ws, multiplier), "multiplier": float(multiplier),
           "rule": "median off-diagonal distance of the initial encoder on one calibration batch per stratum (seed + 99), "
                   "stratum-weighted mean (losses.calibrate_sigma); cross_person and XM use sigma_u on both sides",
           "strata": per}
    if rich:
        out["rich"] = {}
        for h, (uu, vv, ww) in rr.items():
            out["rich"][h] = (None if not uu else {"sigma_u": L.calibrate_sigma(uu, ww, multiplier), "sigma_v": L.calibrate_sigma(vv, ww, multiplier),
                                                   "n_strata": len(uu)})
    return _py(out)


# ---------------------------------------------------------------------------------------------------------- members
class _Acc:
    """Training statistics of one member between two validations."""

    def __init__(self):
        self.n, self.loss, self.gn, self.nonfinite, self.parts, self.part_n = 0, 0.0, 0.0, 0, {}, {}

    def add(self, loss, parts, gn):
        self.n += 1
        self.loss += loss
        self.gn += gn
        for k, v in parts.items():
            if v is not None:
                self.parts[k] = self.parts.get(k, 0.0) + float(v)
                self.part_n[k] = self.part_n.get(k, 0) + 1

    def summary(self):
        n = max(self.n, 1)
        return {"train_steps": self.n, "train_loss": self.loss / n if self.n else None, "grad_norm": self.gn / n if self.n else None,
                "nonfinite_steps": self.nonfinite, **{f"train_{k}": v / self.part_n[k] for k, v in sorted(self.parts.items())}}


class _Member:
    """One member of a lockstep group: its encoder, its AdamW state, its loss and its step counts."""

    def __init__(self, tag, enc, objective, sigma, unknown_clock, heads):
        self.tag, self.enc, self.kind, self.lam = tag, enc, KIND[tag], LAMBDA.get(tag)     # lam: None for non-joint members
        if objective not in L.CONTRACT_OBJECTIVES:
            raise ValueError(f"objective {objective!r} is not one of {L.CONTRACT_OBJECTIVES}")
        self.objective, self.sigma, self.uc, self.heads = objective, sigma, unknown_clock, heads
        self.params = list(enc.parameters())
        self.opt = torch.optim.AdamW(self.params, lr=LR, weight_decay=WEIGHT_DECAY)
        self.counts = {"main": {"steps": 0, "updates": 0, "nonfinite": 0}, "side": {"steps": 0, "updates": 0, "nonfinite": 0}}
        self.acc = _Acc()

    def _audio(self, u1, u2, v, keys):
        if self.objective == "NCE":
            return L.nce_audio_pair(u1, u2, v, keys, TEMPERATURE, unknown_clock=self.uc)
        return L.cs_audio_pair(u1, u2, v, self.sigma["sigma_u"], self.sigma["sigma_v"])

    def _cross(self, u1, u2, keys, p1, p2):
        if self.objective == "NCE":
            return L.nce_cross_person(u1, u2, keys, p1, p2, TEMPERATURE, unknown_clock=self.uc)
        return L.cs_cross_person(u1, u2, self.sigma["sigma_u"])

    def loss(self, batch, v, vr, xm):
        """(loss, parts) of this member on the shared batch; None when its EEG outputs are non-finite."""
        lay = batch.layout
        if self.kind == "rich":
            from . import rich as R
            uh = R.eeg_heads(self.enc, batch.x1, batch.x2, lay)
            if not all(torch.isfinite(a).all() and torch.isfinite(b).all() for a, b in uh.values()):
                return None
            return self.rich_terms(uh, batch, vr)
        u1 = self.enc(batch.x1, layout=lay)
        u2 = self.enc(xm.x2 if self.kind == "xm" else batch.x2, layout=lay)
        if not (torch.isfinite(u1).all() and torch.isfinite(u2).all()):
            return None
        return self.terms(u1, u2, batch, v, xm)

    def terms(self, u1, u2, batch, v, xm):
        """(loss, parts) of the member's loss terms on its two EEG views: audio_pair L_audio(u1, u2; v), cross_person L_cross(u1,
        u2), joint L_audio + lambda L_cross (one forward pass of the two views feeds both), XM L_cross(u1, u2 = enc(X2[pi])) with
        X1's keys and the deranged partners."""
        parts, loss = {}, 0.0
        if self.kind in ("audio_pair", "joint"):
            la, sa = self._audio(u1, u2, v, batch.keys)
            loss = loss + la
            parts["loss_audio"] = float(la.detach())
            if "nopos_e2a" in sa:
                parts["nopos_audio"] = sa["nopos_e2a"] + sa["nopos_a2e"]
        if self.kind in ("cross_person", "joint", "xm"):
            keys, p2 = (xm.keys, xm.part2) if self.kind == "xm" else (batch.keys, batch.part2)
            lc, sc = self._cross(u1, u2, keys, batch.part1, p2)
            loss = loss + (self.lam if self.kind == "joint" else 1.0) * lc
            parts["loss_cross"] = float(lc.detach())
            if "nopos_12" in sc:
                parts["nopos_cross"] = sc["nopos_12"] + sc["nopos_21"]
        return loss, parts

    def rich_terms(self, uh, batch, vr):
        """(loss, parts) of APR: the normalised rich loss (rich.rich_loss) of the head pairs uh on the present targets vr."""
        from . import rich as R
        present = {"env": True, "ss": batch.rich_mask, "sc": batch.rich_mask}
        sig = None
        if self.objective == "CS_SINGLE":
            rs = self.sigma.get("rich") or {}
            sig = {"env": (self.sigma["sigma_u"], self.sigma["sigma_v"])}
            for h in ("ss", "sc"):
                if rs.get(h):
                    sig[h] = (rs[h]["sigma_u"], rs[h]["sigma_v"])
        loss, st = R.rich_loss(uh, vr, present, self.objective, sig, keys=batch.keys, unknown_clock=self.uc, temperature=TEMPERATURE)
        return loss, {k: st.get(k) for k in ("loss_env", "loss_ss", "loss_sc", "rows_ss", "rows_sc", "norm")}

    def step(self, batch, v, vr, xm, lr, branch):
        c = self.counts[branch]
        c["steps"] += 1
        for g in self.opt.param_groups:
            g["lr"] = lr
        self.enc.train()
        out = self.loss(batch, v, vr, xm)
        self.opt.zero_grad(set_to_none=True)
        if out is None:
            c["nonfinite"] += 1
            self.acc.nonfinite += 1
            return
        loss, parts = out
        loss.backward()
        gn = float(torch.nn.utils.clip_grad_norm_(self.params, CLIP))
        lf = float(loss.detach())
        if not (math.isfinite(gn) and math.isfinite(lf)):
            c["nonfinite"] += 1
            self.acc.nonfinite += 1
            self.opt.zero_grad(set_to_none=True)
            return
        self.opt.step()
        c["updates"] += 1
        self.acc.add(lf, parts, gn)

    def snapshot(self):
        return {"enc": _state(self.enc), "opt": _cpu(self.opt.state_dict())}

    def restore(self, snap):
        self.enc.load_state_dict(snap["enc"])
        self.opt.load_state_dict(copy.deepcopy(snap["opt"]))


# ---------------------------------------------------------------------------------------------------------- spec and upstreams
def _s0(budget):
    """The manifest's S0 (fixture schema: budget.S0; the §4.3 spec name steps0 accepted); -1 when it names neither."""
    v = budget.get("S0", budget.get("steps0"))
    return -1 if v is None else int(v)


def _close(a, b):
    try:
        return math.isclose(float(a), float(b), rel_tol=1e-12, abs_tol=1e-15)
    except (TypeError, ValueError):
        return False


def check_spec(row, manifest):
    """The §4.3 spec fields this module implements, checked when present (fail closed: a row asking for another recipe raises).
    Returns the resolved configuration."""
    s, fam, eid = row.get("spec") or {}, row["family_id"], row["experiment_id"]
    bad = []

    def want(key, ok, got):
        if not ok:
            bad.append(f"{key}={got!r}")
    if SEL.stage_of(row) != "donor_group":
        raise ValueError(f"{eid}: not a donor-group row")
    members = SEL.group_members(row)
    block = s.get("block")
    want("block", block in GROUP_BLOCK[fam], block)
    objective = s.get("objective")
    want("objective", objective in L.CONTRACT_OBJECTIVES, objective)
    seed = int(row["seed"])
    for k in ("donor_seed", "sampler_seed"):
        if k in s:
            want(k, s[k] == seed, s[k])
    target = row["dataset"]
    if target not in manifest["donor_sets"]:
        bad.append(f"dataset={target!r} (no manifest donor set)")
    sha = s.get("manifest_sha256")
    if not sha:
        bad.append("manifest_sha256 missing")
    elif getattr(manifest, "sha256", None) is not None and not manifest.sha256.startswith(str(sha).lower()):
        bad.append(f"manifest_sha256={str(sha)[:16]} (the opened manifest is {manifest.sha256[:16]})")
    for k, v in MD.GEOMETRY.items():
        if k in s:
            got = list(s[k]) if isinstance(s[k], (list, tuple)) else s[k]
            want(k, got == v, s[k])
    for k, v in (("temperature", TEMPERATURE), ("bandwidth_multiplier", BANDWIDTH_MULTIPLIER)):
        if k in s:
            want(k, _close(s[k], v), s[k])
    if "batch" in s:
        want("batch", isinstance(s["batch"], dict) and all(int(s["batch"].get(k, v)) == v for k, v in BATCH.items()), s["batch"])
    bud = s.get("budget") or {}
    mb = manifest.get("budget") or {}
    if "epoch_equivalents" in bud:
        want("budget.epoch_equivalents", int(bud["epoch_equivalents"]) == H0, bud["epoch_equivalents"])
    if "anchors_per_ep_eq" in bud:
        want("budget.anchors_per_ep_eq", int(bud["anchors_per_ep_eq"]) == int(mb.get("anchors_per_ep_eq", -1)), bud["anchors_per_ep_eq"])
    if "steps0" in bud:
        want("budget.steps0", int(bud["steps0"]) == _s0(mb), bud["steps0"])
    last, ext, limit = parse_rule(row)
    sel = s.get("selection")
    if isinstance(sel, dict):
        for k, v in SELECTION.items():
            if k in sel:
                want(f"selection.{k}", sel[k] == v, sel[k])
    for k, v in (("montage_augmentation", MONTAGE_AUG), ("control", CONTROL)):
        if k in s:
            want(k, s[k] == v, s[k])
    opt = s.get("optimizer")
    if isinstance(opt, dict):
        for k, v in (("name", "AdamW"), ("lr", LR), ("weight_decay", WEIGHT_DECAY), ("clip", CLIP), ("grad_clip", CLIP)):
            if k in opt:
                want(f"optimizer.{k}", (opt[k] == v) if isinstance(v, str) else _close(opt[k], v), opt[k])
    elif opt is not None:
        txt = str(opt).lower().replace(" ", "")
        want("optimizer", "adamw" in txt and "1e-3" in txt and "1e-4" in txt, opt)
    ds = (manifest["donor_sets"].get(target) or {}).get(SM.BLOCKS.get(block, "core")) if block in SM.BLOCKS else None
    if ds is None:
        bad.append(f"no manifest donor set {target}/{block}")
    else:
        if "stratum_weights" in s:
            sw = s["stratum_weights"]
            ref = dict(zip(ds["strata"], ds["weights"]))
            if isinstance(sw, dict):
                ok = set(sw) == set(ref) and all(_close(sw[k], ref[k]) for k in ref)
            else:
                ok = isinstance(sw, (list, tuple)) and len(sw) == len(ref) and all(_close(a, b) for a, b in zip(sw, ds["weights"]))
            want("stratum_weights", ok, sw)
        if "donor_set" in s:
            d = s["donor_set"]
            strata = list(ds["strata"])
            ok = (d == target or (isinstance(d, (list, tuple)) and list(d) == strata)
                  or (isinstance(d, dict) and list(d.get("strata", ())) == strata))
            want("donor_set", ok, d)
    if "target_contract" in s:
        want("target_contract", s["target_contract"] == manifest.get("target_contract"), s["target_contract"])
    if fam == SEL.RICH_DONOR:
        if "rich_targets" in s:
            want("rich_targets", s["rich_targets"] == RICH_TARGETS, s["rich_targets"])
        if "loss_weights" in s:
            want("loss_weights", [float(x) for x in s["loss_weights"]] == RICH_LOSS_WEIGHTS, s["loss_weights"])
        if not manifest.get("rich"):
            bad.append("the manifest has no rich block")
    if fam == SEL.CSX_DONOR and "extra_strata" in s:
        want("extra_strata", list(s["extra_strata"]) == ["fau_cs"], s["extra_strata"])
    if bad:
        raise ValueError(f"{eid}: spec fields this donor runner does not implement: " + "; ".join(bad))
    return {"members": list(members), "block": block, "objective": objective, "seed": seed, "target": target, "rule": [last, ext, limit],
            "limit": limit}


def resolve_upstreams(row, out):
    """{"horizon": {...}} for rich / CSX groups (the core group's record: H*, ceiling flag, stream hashes; rich: the core AP
    _best.pt), {"continuation": {...}} for continuation versions (the source record and its retained stable states). Raises
    MissingDependency for an absent record or file, ValueError for an inconsistent upstream."""
    s, fam, eid = row.get("spec") or {}, row["family_id"], row["experiment_id"]
    hor, cont, ups = s.get("horizon_from"), s.get("continuation_of"), {}
    if fam == SEL.DONOR and hor is not None:
        raise ValueError(f"{eid}: {SEL.DONOR} groups run their own trigger; spec.horizon_from is refused (§2.10)")
    if fam != SEL.DONOR and hor is None:
        raise ValueError(f"{eid}: {fam} groups adopt the core group's realised horizon: spec.horizon_from is required (§2.10)")
    _, _, limit = parse_rule(row)
    hrow = None
    if hor is not None:
        rec = SEL.load_record(out, hor)
        if rec is None:
            raise MissingDependency(f"horizon group {hor}: no complete record units/{hor}.json")
        hrow = rec.get("row") or {}
        if hrow.get("experiment_id") != hor or hrow.get("family_id") != SEL.DONOR:
            raise ValueError(f"{eid}: horizon record {hor} is not a {SEL.DONOR} group record")
        for k in ("dataset", "seed"):
            if hrow.get(k) != row.get(k):
                raise ValueError(f"{eid}: horizon group {hor} has {k} {hrow.get(k)!r}, the row {row.get(k)!r}")
        if (hrow.get("spec") or {}).get("objective") != s.get("objective"):
            raise ValueError(f"{eid}: horizon group {hor} has another objective")
        if SEL.compute_limit(hrow) != limit:
            raise ValueError(f"{eid}: horizon group {hor} has compute limit {SEL.compute_limit(hrow)}, the row {limit} (the same version)")
        if (cont is None) != ((hrow.get("spec") or {}).get("continuation_of") is None):
            raise ValueError(f"{eid}: a {'continuation' if cont else 'primary'} group must adopt the horizon of a "
                             f"{'continuation' if cont else 'primary'} core group ({hor} is not one; prior33_open_M8_M10.md)")
        H = rec.get("horizon_ep_eq")
        if rec.get("truncated") or not isinstance(H, int) or isinstance(H, bool):
            raise ValueError(f"{eid}: horizon group {hor} has no integer realised horizon ({H!r}; truncated runs are probes)")
        st = rec.get("stream") or {}
        ups["horizon"] = {"gid": hor, "H": int(H), "ceiling": bool(rec.get("ceiling_reached_while_improving")), "limit": limit,
                          "code_hash": rec.get("code_hash"), "code_group": rec.get("code_group"),
                          "hash_log": [[int(a), str(b)] for a, b in st.get("hash_log") or ()],
                          "final": st.get("final"), "final_step": st.get("final_step")}
        if fam == SEL.RICH_DONOR:
            ap = SEL.member_ckpt(out, hor, "AP", "best")
            if not os.path.exists(ap):
                raise MissingDependency(f"horizon group {hor}: the core AP checkpoint {os.path.basename(ap)} (donor-side rich readout)")
            ups["core_ap"] = ap
    if cont is not None:
        rec = SEL.load_record(out, cont)
        if rec is None:
            raise MissingDependency(f"continuation source {cont}: no complete record units/{cont}.json")
        srow = rec.get("row") or {}
        if srow.get("experiment_id") != cont or srow.get("family_id") != fam:
            raise ValueError(f"{eid}: continuation source {cont} is not a {fam} group record")
        if set(SEL.group_members(srow)) != set(SEL.group_members(row)):
            raise ValueError(f"{eid}: continuation source {cont} trains other members")
        sspec = srow.get("spec") or {}
        for k, a, b in (("dataset", srow.get("dataset"), row.get("dataset")), ("seed", srow.get("seed"), row.get("seed")),
                        ("objective", sspec.get("objective"), s.get("objective")), ("block", sspec.get("block"), s.get("block"))):
            if a != b:      # a continuation resumes its source's exact trajectory: the same stream, loss and seed
                raise ValueError(f"{eid}: continuation source {cont} has {k} {a!r}, the row {b!r}")
        if rec.get("truncated"):
            raise ValueError(f"{eid}: continuation source {cont} is a truncated (probe) record")
        if not rec.get("ceiling_reached_while_improving"):
            raise ValueError(f"{eid}: continuation source {cont} did not reach its compute limit while improving")
        if SEL.compute_limit(srow) >= limit:
            raise ValueError(f"{eid}: a continuation's limit {limit} must exceed its source's {SEL.compute_limit(srow)}")
        if hrow is not None:      # an adopted-horizon continuation: its horizon group continues its source's horizon group
            want, got = (srow.get("spec") or {}).get("horizon_from"), (hrow.get("spec") or {}).get("continuation_of")
            if got != want:
                raise ValueError(f"{eid}: its horizon group {hor} continues {got}, not the horizon group {want} of its source {cont}")
        files = dict(zip(SEL.group_members(srow), SEL.retained_states(out, srow)))
        miss = [os.path.basename(p) for p in files.values() if not os.path.exists(p)]
        if miss:
            raise MissingDependency(f"continuation source {cont}: retained stable states {miss} are missing")
        ups["continuation"] = {"gid": cont, "files": files, "limit": SEL.compute_limit(srow), "code_hash": rec.get("code_hash"),
                               "code_group": rec.get("code_group")}
    return ups


# ---------------------------------------------------------------------------------------------------------- the group run
class _Hooks:
    """Test seams (never used by the runner): on_member(tag, batch, xm) before each member step, before_save(run) after a
    validation's checkpoint and stable files are written and before its resume save, after_save(run) after each resume save."""

    def on_member(self, tag, batch, xm):
        pass

    def before_save(self, run):
        pass

    def after_save(self, run):
        pass


def _counter(n_pres, n_fam):
    return {"steps": {"stable": 0, "decay": 0, "side": 0}, "strata": {}, "pres": np.zeros(n_pres, dtype=np.int64),
            "fam": np.zeros(n_fam, dtype=np.int64), "segments": 0,
            "xm": {"n": 0, "same_condition_fraction_sum": 0.0, "violations": 0, "violations_family": 0, "violations_partner": 0,
                   "infeasible": 0, "assignment": 0, "draws": 0}}


def _counter_out(c):
    return {**{k: v for k, v in c.items() if k not in ("pres", "fam")}, "pres": c["pres"].tolist(), "fam": c["fam"].tolist()}


def _counter_in(c):
    return {**c, "pres": np.asarray(c["pres"], dtype=np.int64), "fam": np.asarray(c["fam"], dtype=np.int64)}


def _compute_part(timing, counters, member_counts):
    """The compute fields of a trajectory part (the cumulative totals, or the part restored from a continuation's source)."""
    cm, cs = counters["main"], counters["side"]
    return {"steps_by_phase": {**{k: int(v) for k, v in cm["steps"].items()}, "side": int(cs["steps"]["side"])},
            "main_steps": int(sum(cm["steps"].values())), "side_steps": int(cs["steps"]["side"]),
            "strata_steps": {"main": {k: int(v) for k, v in cm["strata"].items()}, "side": {k: int(v) for k, v in cs["strata"].items()}},
            "train_s": {k: float(v) for k, v in timing["train_s"].items()}, "validation_s": float(timing["validation_s"]),
            "n_validations": int(timing["n_validations"]), "validation_windows": int(timing["validation_windows"]),
            "train_member_steps": int(timing["train_member_steps"]),
            "member_train_s": {m: {k: float(x) for k, x in v.items()} for m, v in (timing.get("member_train_s") or {}).items()},
            "member_steps": {m: {b: int(c[b]["steps"]) for b in ("main", "side")} for m, c in member_counts.items()}}


def _minus(a, b):
    """a - b for nested dicts of numbers (a key absent from b counts as 0)."""
    if isinstance(a, dict):
        b = b if isinstance(b, dict) else {}
        return {k: _minus(v, b.get(k)) for k, v in a.items()}
    if isinstance(a, (int, float)) and not isinstance(a, bool):
        return a - (b if isinstance(b, (int, float)) and not isinstance(b, bool) else 0)
    return a


def resume_files(out, gid):
    """ckpt/<gid>_resume.pt and ckpt/<gid>_wsd_resume.pt with their .tmp files (all match the offload guard *_resume.pt*)."""
    base = [os.path.join(out, "ckpt", f"{gid}_resume.pt"), os.path.join(out, "ckpt", f"{gid}_wsd_resume.pt")]
    return base + [p + ".tmp" for p in base]


def remove_resume_files(out, gid):
    """Delete the group's resume files (run_donor calls it after core.write_record wrote the complete record); returns the
    names removed."""
    gone = []
    for p in resume_files(out, gid):
        if os.path.lexists(p):
            os.remove(p)
            gone.append(os.path.basename(p))
    return gone


class _GroupRun:
    """The lockstep loop of one donor group: train to the next ep-eq of the branch, validate every member, update the three
    checkpoints, apply the GroupWSD decision / side-branch end / final decay, save the resume."""

    def __init__(self, *, row, members, sampler, validator, wsd, heads, out, device, sigma, max_steps=None, hooks=None,
                 horizon=None, inherit=None, scratch=None, meta=None):
        self.row, self.gid = row, row["experiment_id"]
        self.members, self.tags = members, list(members)
        self.sampler, self.validator, self.wsd, self.heads, self.out, self.device = sampler, validator, wsd, heads, out, device
        self.sigma, self.max_steps, self.hooks = sigma, max_steps, hooks or _Hooks()
        self.horizon, self.inherit, self.scratch, self.meta = horizon, inherit, scratch, meta or {}
        self.paths = {k: {m: SEL.member_ckpt(out, self.gid, m, k) for m in self.tags} for k in KINDS}
        self.paths["stable"] = {m: SEL.stable_ckpt(out, self.gid, m, wsd.limit - wsd.decay) for m in self.tags}
        self.resume_path = os.path.join(out, "ckpt", f"{self.gid}_resume.pt")
        self.wsd_path = os.path.join(out, "ckpt", f"{self.gid}_wsd_resume.pt")
        idx = sampler.idx
        self.n_pres, self.n_fam = int(idx.n_pres), int(len(sampler.manifest["families"]))
        self.step, self.E, self.branch, self.i_val, self.done = 0, 0, "main", 0, False
        self.curves = {m: [] for m in self.tags}
        self.best = {m: {k: None for k in KINDS} for m in self.tags}
        self.counters = {"main": _counter(self.n_pres, self.n_fam), "side": _counter(self.n_pres, self.n_fam)}
        self.timing = {"train_s": {"stable": 0.0, "decay": 0.0, "side": 0.0}, "validation_s": 0.0, "n_validations": 0,
                       "validation_windows": 0, "train_member_steps": 0,
                       "member_train_s": {m: {"stable": 0.0, "decay": 0.0, "side": 0.0} for m in self.tags}}
        self.inherited_compute = None        # continuations: the counters / timing restored from the source's stable state
        self.snapshot, self.pending, self.truncated, self.retained = None, False, None, []
        self.stream_checks = {"checked": 0, "steps": [], "final": None, "from_step": 0}
        self.ref_hash = {int(a): str(b) for a, b in (horizon or {}).get("hash_log", ())} if (horizon and horizon.get("check_stream")) else None
        self.resumes, self.inherited, self.side_record, self.sigma_restored = [], None, None, None
        self.last_val_step, self.last_lr = None, None
        self.n_val_segments = int(getattr(validator, "n_segments", 0))

    # ------------------------------------------------------------------------------------------------ main loop
    def run(self):
        if os.path.exists(self.resume_path):
            self._load_resume()
        elif self.inherit is not None:
            self._load_inherited()
        if not self.retained:
            self._drop_stale_stable()
        while not self.done:
            if self.pending:
                self.pending = False
                self._post(self.E)
                self.hooks.before_save(self)
                self._save_resume()
                continue
            E_next = self.E + 1
            target = self.wsd.steps_at(E_next)
            if self.branch == "main" and self.max_steps is not None and int(self.max_steps) < target:
                self._train_to(int(self.max_steps))
                if self.last_val_step is None or self.step > self.last_val_step:
                    self._validate(self.wsd.ep_eq_of(self.step), truncated=True)
                self.truncated = {"max_steps": int(self.max_steps), "at_step": self.step, "ep_eq": self.wsd.ep_eq_of(self.step),
                                  "note": "probe run: max_steps caps the main-run steps; not a registered result"}
                self.done = True
                break
            self._train_to(target)
            self._validate(E_next)
            self.E = E_next
            self._post(E_next)
            self.hooks.before_save(self)
            self._save_resume()
        self._finish_stream()
        return self

    def _drop_stale_stable(self):
        """Remove this group's stable files when the state being continued has retained none: they can only stem from an
        attempt that wrote them after its last resume save (or from an earlier run of the same id), so they are not part of
        this trajectory (module docstring, Resume consistency); a ceiling reached again rewrites them."""
        for p in self.paths["stable"].values():
            if os.path.lexists(p):
                os.remove(p)

    def _post(self, E):
        """After the validation at E: the side-branch end, the decision at a decay start, or the end of the final decay."""
        w = self.wsd
        if self.branch == "side":
            if w.is_side_end(E, "side"):
                self._end_side()
            return
        if w.is_decay_start(E):
            pre = w.state()
            entry = w.decide(E, self._stable_curves())
            if entry["decision"] == "extend" and entry["side_branch"]:
                self._start_side(E)
            elif entry["decision"] == "ceiling":
                self._retain(E, pre)
        elif w.is_final(E):
            self.done = True

    def _set_sigma(self, sigma):
        """Bandwidths saved by the run (resume, retained stable state) replace the recomputed ones; equality is recorded."""
        self.sigma_restored = {"equal_to_recomputed": sigma == self.sigma}
        self.sigma = copy.deepcopy(sigma)
        for m in self.tags:
            self.members[m].sigma = self.sigma

    def _stable_curves(self):
        return {m: [e["dev"]["ce_bits"] for e in self.curves[m] if e["branch"] == "main" and e["phase"] == "stable"] for m in self.tags}

    # ------------------------------------------------------------------------------------------------ training
    def _train_to(self, target):
        w, smp, dev = self.wsd, self.sampler, self.device
        hv = self.heads
        while self.step < target:
            t0 = time.time()
            ph = "side" if self.branch == "side" else ("stable" if self.step < w.steps_at(w.H - w.decay) else "decay")
            lr = LR * w.lr_scale(self.step, self.branch)
            self.last_lr = lr
            n_log = len(smp.hash_log)
            batch = smp.next_batch()
            if self.ref_hash is not None and len(smp.hash_log) > n_log:
                self._check_hash(smp.hash_log[-1])
            xm = None
            cnt = self.counters[self.branch]
            if "XM" in self.members:
                perm, xst = smp.derangement(batch)
                xm = smp.xm_view(batch, perm)
                x = cnt["xm"]
                x["n"] += 1
                x["same_condition_fraction_sum"] += float(xst["same_condition_fraction"])
                for k in ("violations", "violations_family", "violations_partner", "draws"):
                    x[k] += int(xst[k])
                x["infeasible"] += int(not xst["feasible"])
                x["assignment"] += int(xst["method"] == "assignment")
            with torch.no_grad():
                v = hv["env"](batch.y)
                vr = None
                if "APR" in self.members:
                    vr = {"env": v, "ss": hv["ss"](batch.rich["ss"]), "sc": hv["sc"](batch.rich["sc"])}
            mt = self.timing["member_train_s"]
            for tag in self.tags:
                self.hooks.on_member(tag, batch, xm)
                t1 = _clock(dev)
                self.members[tag].step(batch, v, vr, xm, lr, self.branch)
                mt[tag][ph] += _clock(dev) - t1
            S = smp.idx.seg[batch.cohort]
            pres = S["presentation"][batch.seg_ids]
            np.add.at(cnt["pres"], pres, 1)
            np.add.at(cnt["fam"], smp.idx.fam[pres], 1)
            cnt["segments"] += len(pres)
            cnt["strata"][batch.stratum] = cnt["strata"].get(batch.stratum, 0) + 1
            cnt["steps"][ph] += 1
            self.step += 1
            self.timing["train_member_steps"] += len(self.tags)
            _sync(dev)
            self.timing["train_s"][ph] += time.time() - t0

    def _check_hash(self, entry):
        st, hx = int(entry[0]), str(entry[1])
        ref = self.ref_hash.get(st)
        if ref is None:
            return
        if ref != hx:
            raise StreamMismatch(f"{self.gid}: stream hash at step {st} differs from the core group {self.horizon['gid']} "
                                 f"({hx[:16]} vs {ref[:16]}; §2.15: the rich group must train on the core group's batches)")
        self.stream_checks["checked"] += 1
        self.stream_checks["steps"].append(st)

    def _finish_stream(self):
        if self.ref_hash is None or self.truncated is not None:
            return
        ref, fs = self.horizon.get("final"), self.horizon.get("final_step")
        if ref is not None and fs is not None and int(fs) == self.step:
            if ref != self.sampler.stream_hash():
                raise StreamMismatch(f"{self.gid}: final stream hash differs from the core group {self.horizon['gid']}")
            self.stream_checks["final"] = "equal"
        else:
            self.stream_checks["final"] = f"not compared (core final step {fs}, this run {self.step})"
        expected = sorted(k for k in self.ref_hash if self.stream_checks["from_step"] < k <= self.step)
        if sorted(set(self.stream_checks["steps"])) != expected:
            raise StreamMismatch(f"{self.gid}: stream hash checks at steps {sorted(set(self.stream_checks['steps']))[:5]} do not cover "
                                 f"the core group's log {expected[:5]}")

    # ------------------------------------------------------------------------------------------------ validation and checkpoints
    def _validate(self, E, truncated=False):
        t0 = time.time()
        w = self.wsd
        res = self.validator.validate({m: self.members[m].enc for m in self.tags}, self.sigma)
        ph, h30 = w.phase(E, self.branch), w.h30_eligible(E, self.branch)
        for m in self.tags:
            mem = self.members[m]
            entry = _py({"i": self.i_val, "group": self.gid, "ep_eq": E, "ep_eq_realised": w.ep_eq_of(self.step), "step": self.step,
                         "branch": self.branch, "phase": ph, "h30_eligible": bool(h30), "truncated": bool(truncated), "H": w.H,
                         "dev": res[m]["dev"], "diag": res[m]["diag"], "train": mem.acc.summary(),
                         "updates": mem.counts[self.branch]["updates"], "nonfinite_total": mem.counts[self.branch]["nonfinite"],
                         "lr_last": self.last_lr})
            mem.acc = _Acc()
            self.curves[m].append(entry)
            self._update_best(m, entry)
        self.i_val += 1
        self.last_val_step = self.step
        _sync(self.device)
        self.timing["validation_s"] += time.time() - t0
        self.timing["n_validations"] += 1
        self.timing["validation_windows"] += len(self.tags) * C.SEG_TICKS * self.n_val_segments

    def _info(self, entry):
        d = entry["dev"]
        return {"ce_dev": d["ce_bits"], "gain": d["gain"], "r_own": d["r_own"], "tau": d["tau"], "n_cand": d["n_cand"],
                "ep_eq": entry["ep_eq"], "ep_eq_realised": entry["ep_eq_realised"], "step": entry["step"], "branch": entry["branch"],
                "phase": entry["phase"], "validation_index": entry["i"], "group": entry["group"], "truncated": entry["truncated"]}

    def _update_best(self, m, entry):
        st = None
        for kind in KINDS:
            if kind == "h30" and not entry["h30_eligible"]:
                continue
            cur = self.best[m][kind]
            if kind == "gainsel":
                better = cur is None or _gain_key(entry["dev"]["gain"]) > _gain_key(cur["info"]["gain"])
            else:
                better = cur is None or _ce_key(entry["dev"]["ce_bits"]) < _ce_key(cur["info"]["ce_dev"])
            if not better:
                continue
            if st is None:
                st = _state(self.members[m].enc)
            self.best[m][kind] = {"info": self._info(entry), "enc": st}
            self._write_ckpt(m, kind)

    def _write_ckpt(self, m, kind):
        b = self.best[m][kind]
        mem = self.members[m]
        _save(self.paths[kind][m], {"format": CKPT_FORMAT, "group": self.gid, "member": m, "kind": kind, "enc": b["enc"],
                                    "head": _state(self.heads["env"]), "sigma": copy.deepcopy(mem.sigma), "objective": mem.objective,
                                    "loss": mem.kind, "lambda": _lam(mem), "validation": copy.deepcopy(b["info"]),
                                    "layout": list(mem.enc.layout), "seen": mem.enc.seen_names(), "rich_heads": m == "APR",
                                    "manifest_sha256": self.meta.get("manifest_sha256"), "donor_seed": int(self.row["seed"]),
                                    "contract": C.CONTRACT})

    # ------------------------------------------------------------------------------------------------ side branch, ceiling, resume
    def _branch_state(self):
        return {"step": self.step, "E": self.E, "sampler": self.sampler.state(), "torch_rng": torch.get_rng_state(),
                "members": {m: self.members[m].snapshot() for m in self.tags}, "last_lr": self.last_lr}

    def _start_side(self, E):
        self.snapshot = self._branch_state()
        _save(self.wsd_path, {"format": WSD_FORMAT, "group": self.gid, "snapshot": self.snapshot})
        self.branch = "side"
        self.side_record = {"start_ep_eq": int(E), "start_step": self.step, "end_ep_eq": int(self.wsd.side["end"])}

    def _end_side(self):
        snap = self.snapshot
        if snap is None:
            raise RuntimeError(f"{self.gid}: the side branch ended without its stable snapshot")
        self.side_record = {**(self.side_record or {}), "end_step": self.step, "stream_hash_at_end": self.sampler.stream_hash(),
                            "counts": {m: dict(self.members[m].counts["side"]) for m in self.tags}}
        for m in self.tags:
            self.members[m].restore(snap["members"][m])
        self.sampler.load_state(snap["sampler"])
        torch.set_rng_state(snap["torch_rng"].cpu())
        self.step, self.E, self.branch = int(snap["step"]), int(snap["E"]), "main"
        self.last_lr = snap.get("last_lr")          # the main run's last lr (a validation without a step since reports it)
        self.wsd.end_side()
        self.snapshot = None

    def _group_state(self):
        return {"step": self.step, "E": self.E, "branch": self.branch, "i_val": self.i_val, "sampler": self.sampler.state(),
                "torch_rng": torch.get_rng_state(), "counters": {k: _counter_out(v) for k, v in self.counters.items()},
                "timing": copy.deepcopy(self.timing), "side_record": copy.deepcopy(self.side_record), "last_val_step": self.last_val_step,
                "last_lr": self.last_lr}

    def _retain(self, E, pre):
        """The compute limit was reached while the trigger fires: keep every member's stable state at L - 3 (§2.10), the state a
        continuation version resumes from (its decision at this validation is re-made under the continuation's limit)."""
        g = {**self._group_state(), "wsd_pre_decision": pre}
        for m in self.tags:
            mem = self.members[m]
            _save(self.paths["stable"][m], {"format": STABLE_FORMAT, "group": self.gid, "member": m, "ep_eq": int(E), "members": list(self.tags),
                                            **mem.snapshot(), "counts": copy.deepcopy(mem.counts), "curve": copy.deepcopy(self.curves[m]),
                                            "best": copy.deepcopy(self.best[m]), "sigma": copy.deepcopy(mem.sigma), "group_state": g})
        self.retained = [os.path.relpath(self.paths["stable"][m], self.out) for m in self.tags]

    def _save_resume(self):
        _save_resume(self.resume_path, format=RESUME_FORMAT, group=self.gid, members_order=list(self.tags), done=self.done,
                     wsd=self.wsd.state(), group_state=self._group_state(), curves=self.curves, best=self.best,
                     members={m: {**self.members[m].snapshot(), "counts": copy.deepcopy(self.members[m].counts)} for m in self.tags},
                     retained=list(self.retained), stream_checks=copy.deepcopy(self.stream_checks), resumes=list(self.resumes),
                     inherited=copy.deepcopy(self.inherited), side_active=self.snapshot is not None, sigma=copy.deepcopy(self.sigma),
                     inherited_compute=copy.deepcopy(self.inherited_compute), code_hash=self.meta.get("code_hash"))
        if self.snapshot is None and os.path.exists(self.wsd_path):   # the side branch has ended and the resume no longer needs it
            os.remove(self.wsd_path)
        self.hooks.after_save(self)

    def _restore_group(self, g):
        self.step, self.E, self.branch, self.i_val = int(g["step"]), int(g["E"]), str(g["branch"]), int(g["i_val"])
        self.sampler.load_state(g["sampler"])
        torch.set_rng_state(g["torch_rng"].cpu())
        self.counters = {k: _counter_in(v) for k, v in g["counters"].items()}
        self.timing = copy.deepcopy(g["timing"])
        mt = self.timing.setdefault("member_train_s", {})
        for m in self.tags:
            mt.setdefault(m, {"stable": 0.0, "decay": 0.0, "side": 0.0})
        self.side_record = copy.deepcopy(g["side_record"])
        self.last_val_step = g.get("last_val_step")
        self.last_lr = g.get("last_lr")

    def _load_resume(self):
        r = _load(self.resume_path)
        if r.get("format") != RESUME_FORMAT or r.get("group") != self.gid or list(r.get("members_order") or ()) != self.tags:
            raise ValueError(f"{self.resume_path}: not this group's resume file")
        self.wsd.load_state(r["wsd"])
        self._set_sigma(r["sigma"])
        self._restore_group(r["group_state"])
        for m in self.tags:
            self.members[m].restore(r["members"][m])
            self.members[m].counts = copy.deepcopy(r["members"][m]["counts"])
        self.curves, self.best = r["curves"], r["best"]
        for m in self.tags:            # the files may be newer than this resume (written by a validation that followed it)
            for kind in KINDS:
                if self.best[m][kind] is not None:
                    self._write_ckpt(m, kind)
        self.retained, self.stream_checks = list(r["retained"]), r["stream_checks"]
        self.inherited_compute = r.get("inherited_compute")
        self.inherited, self.resumes = r["inherited"], list(r["resumes"]) + [{"step": self.step, "ep_eq": self.E, "branch": self.branch,
                                                                              "validations": self.i_val, "time": time.time(),
                                                                              "device": _device_name(self.device),
                                                                              "code_hash": r.get("code_hash"),
                                                                              "resumed_with_code_hash": self.meta.get("code_hash"),
                                                                              "code_hash_equal": (None if r.get("code_hash") is None or self.meta.get("code_hash") is None
                                                                                                  else r["code_hash"] == self.meta["code_hash"])}]
        self.done = bool(r["done"])
        if r["side_active"]:
            if not os.path.exists(self.wsd_path):
                raise MissingDependency(f"{self.gid}: a side branch is active but {os.path.basename(self.wsd_path)} is missing")
            w = _load(self.wsd_path)
            if w.get("format") != WSD_FORMAT or w.get("group") != self.gid:
                raise ValueError(f"{self.wsd_path}: not this group's side-branch snapshot")
            self.snapshot = w["snapshot"]

    def _load_inherited(self):
        """Continuation start: the source's stable states at L_src - 3 (decision pending under this row's limit)."""
        files, src = self.inherit["files"], self.inherit["gid"]
        states = {}
        for m in self.tags:
            st = _load(files[m])
            if st.get("format") != STABLE_FORMAT or st.get("group") != src or st.get("member") != m or list(st.get("members") or ()) != self.tags:
                raise ValueError(f"{files[m]}: not the retained stable state of member {m} of {src}")
            states[m] = st
        g0 = states[self.tags[0]]["group_state"]
        for m, st in states.items():
            g = st["group_state"]
            if (g["step"], g["E"], g["sampler"]["chain"]) != (g0["step"], g0["E"], g0["sampler"]["chain"]) or st["sigma"] != states[self.tags[0]]["sigma"]:
                raise ValueError(f"{src}: the retained stable states of the members disagree")
        self._set_sigma(states[self.tags[0]]["sigma"])
        self.wsd.load_state(g0["wsd_pre_decision"])
        self._restore_group(g0)
        if self.branch != "main" or not self.wsd.is_decay_start(self.E):
            raise ValueError(f"{src}: the retained state is not at a main-run decay start (ep-eq {self.E}, branch {self.branch})")
        for m, st in states.items():
            self.members[m].restore(st)
            self.members[m].counts = copy.deepcopy(st["counts"])
            self.curves[m] = list(st["curve"])
            self.best[m] = st["best"]
            for kind in KINDS:
                if self.best[m][kind] is not None:
                    self._write_ckpt(m, kind)
        self.inherited_compute = {"from": src, "timing": copy.deepcopy(self.timing),
                                  "counters": copy.deepcopy({k: _counter_out(v) for k, v in self.counters.items()}),
                                  "member_counts": {m: copy.deepcopy(st["counts"]) for m, st in states.items()}}
        self.stream_checks["from_step"] = int(self.step)
        self.inherited = {"from": src, "ep_eq": int(self.E), "step": int(self.step), "validations": int(self.i_val),
                          "files": [os.path.relpath(p, self.out) for p in files.values()], "code_hash": self.inherit.get("code_hash")}
        self.pending = True

    # ------------------------------------------------------------------------------------------------ the record
    def finish(self):
        """bridge_cal scores of the distinct checkpoint states and the record fields. The resume files stay: the caller deletes
        them once the record is written (remove_resume_files; module docstring)."""
        bc = self._bridge_cal()
        recm = {}
        for m in self.tags:
            mem = self.members[m]
            kinds, at = {}, {}
            for kind in KINDS:
                b = self.best[m][kind]
                info = dict(b["info"])
                at[kind] = (info["group"], info["validation_index"])
                sc = {k: v for k, v in bc[(m, *at[kind])].items() if k not in ("gain", "n_gain")}   # bridge_cal has no o(q)
                info.update({"bridge_cal_ce": sc["ce_bits"], "bridge_cal": sc})
                kinds[kind] = info
            recm[m] = {**kinds, "identical": {"best_h30": at["best"] == at["h30"], "best_gainsel": at["best"] == at["gainsel"],
                                              "h30_gainsel": at["h30"] == at["gainsel"]},
                       "steps": mem.counts["main"]["steps"], "updates": mem.counts["main"]["updates"],
                       "nonfinite_steps": mem.counts["main"]["nonfinite"], "side_branch": dict(mem.counts["side"]),
                       "loss": mem.kind, "lambda": _lam(mem), "sigma": copy.deepcopy(mem.sigma), "curve": self.curves[m],
                       "checkpoints": {k: os.path.relpath(self.paths[k][m], self.out) for k in KINDS}}
            if mem.kind == "joint":
                recm[m]["term_magnitudes"] = [{"ep_eq": e["ep_eq"], "branch": e["branch"], "loss_audio": e["train"].get("train_loss_audio"),
                                               "loss_cross": e["train"].get("train_loss_cross")} for e in self.curves[m]]
        w, cm, cs = self.wsd, self.counters["main"], self.counters["side"]
        n_main = sum(cm["steps"].values())
        out = {"members": recm, "horizon_ep_eq": (w.H if self.truncated is None else self.truncated["ep_eq"]),
               "ceiling_reached_while_improving": bool(w.ceiling), "compute_limit_ep_eq": w.limit, "trigger_log": w.log,
               "side_branch": ({"ran": True, **self.side_record} if self.side_record else {"ran": False}), "schedule": w.describe(),
               "steps_by_phase": {**cm["steps"], "side": cs["steps"]["side"]}, "main_steps": n_main,
               "ep_eq_used": w.ep_eq_of(n_main), "side_steps": cs["steps"]["side"],
               "stream": {"hash_every": SM.HASH_EVERY, "hash_log": [list(x) for x in self.sampler.hash_log],
                          "final": self.sampler.stream_hash(), "final_step": self.step,
                          "core_check": (None if self.ref_hash is None else {"core_group": self.horizon["gid"], **self.stream_checks,
                                                                              "steps": len(self.stream_checks["steps"])})},
               "shares": {"main": self._shares(cm, n_main), "side": self._shares(cs, cs["steps"]["side"])},
               "xm": ({"main": self._xm(cm), "side": self._xm(cs)} if "XM" in self.members else None),
               "timing": {**self.timing, "train_s": dict(self.timing["train_s"]), "device": str(self.device)},
               "retained_states": list(self.retained), "truncated": self.truncated, "resumed": list(self.resumes),
               "inherited": self.inherited, "sigma": copy.deepcopy(self.sigma), "sigma_restored": self.sigma_restored}
        total = _compute_part(self.timing, self.counters, {m: self.members[m].counts for m in self.tags})
        inh = self.inherited_compute
        if inh is None:
            out["compute_inherited"], out["compute_this_run"] = None, {**total, "note": "a primary group: the whole trajectory"}
        else:
            part = _compute_part(inh["timing"], inh["counters"], inh["member_counts"])
            out["compute_inherited"] = {**part, "from": inh["from"],
                                        "note": "restored from the source's retained stable state; reported in the source's record"}
            out["compute_this_run"] = {**_minus(total, part), "note": "this version's own part of the cumulative totals"}
        return _py(out)

    def resume_files(self):
        return resume_files(self.out, self.gid)

    def _shares(self, c, n_steps):
        man = self.sampler.manifest
        tot = max(int(c["segments"]), 1)
        fams = man["families"]
        return {"steps": int(n_steps), "strata": {k: {"steps": int(v), "share": v / max(n_steps, 1)} for k, v in sorted(c["strata"].items())},
                "presentations": {str(i): int(v) for i, v in enumerate(c["pres"].tolist()) if v},
                "families": {str(i): {"name": fams[i].get("name"), "cohort": fams[i].get("cohort"), "segments": int(v), "share": v / tot}
                             for i, v in enumerate(c["fam"].tolist()) if v},
                "segments": int(c["segments"])}

    @staticmethod
    def _xm(c):
        x = c["xm"]
        n = max(x["n"], 1)
        return {"batches": x["n"], "same_condition_fraction_mean": x["same_condition_fraction_sum"] / n if x["n"] else None,
                "violations": x["violations"], "violations_family": x["violations_family"], "violations_partner": x["violations_partner"],
                "infeasible_batches": x["infeasible"], "assignment_fallback_batches": x["assignment"], "random_draws": x["draws"],
                "rule": SM.XM_RULE, "seed_offset": C.XM_SEED_OFFSET}

    def _bridge_cal(self):
        """{(member, group, validation index): bridge_cal scores} of every distinct checkpoint state (best / gainsel / h30)."""
        encs, keys = {}, {}
        for m in self.tags:
            for kind in KINDS:
                b = self.best[m][kind]
                k = (m, b["info"]["group"], b["info"]["validation_index"])
                if k in keys:
                    continue
                name = f"{m}|{k[1]}|{k[2]}"
                enc = self.scratch(m)
                enc.load_state_dict(b["enc"])
                encs[name], keys[k] = enc, name
        res = self.validator.bridge_cal(encs) if encs else {}
        return {k: res[name] for k, name in keys.items()}


def _identical(a, b):
    sa, sb = a.state_dict(), b.state_dict()
    ks = [k for k in sa if not k.startswith(MD.RICH_PREFIX)]
    return set(ks) == {k for k in sb if not k.startswith(MD.RICH_PREFIX)} and all(torch.equal(sa[k], sb[k]) for k in ks)


def _flop_counter():
    try:
        from torch.utils.flop_counter import FlopCounterMode
        return FlopCounterMode
    except Exception:  # noqa: BLE001 (a proxy only)
        return None


def _flops_per_window(enc, layout, device):
    """Forward FLOPs of one window (torch.utils.flop_counter; None when unavailable): the validation part of the FLOP proxy."""
    try:
        FCM = _flop_counter()
        x = torch.zeros(FLOP_WINDOWS, len(layout), C.L_IN, device=device)
        with torch.no_grad(), FCM(display=False) as fc:
            enc(x, layout=tuple(layout))
        return fc.get_total_flops() / float(FLOP_WINDOWS)
    except Exception:  # noqa: BLE001 (a proxy only)
        return None


def _enc_flops(enc, x, layout, rich_heads):
    """FLOPs of the encoder forward + backward per window on the windows x (a deep copy: the member's weights, gradients and
    optimiser are untouched; the encoder draws no random numbers). rich_heads: trunk, envelope projection and both rich heads."""
    e = copy.deepcopy(enc)
    e.train()
    with _flop_counter()(display=False) as fc:
        if rich_heads:
            z = e.trunk(x, layout)
            r = e.rich(z)
            out = e.project(z).sum() + r["ss"].sum() + r["sc"].sum()
        else:
            out = e(x, layout=layout).sum()
        out.backward()
    return fc.get_total_flops() / float(len(x))


def _loss_flops(mem, b, v, vr, xm, gen):
    """FLOPs of the member's loss terms forward + backward at the batch shape: unit rows from the fixed generator `gen` stand in
    for the encoder outputs (the count depends on the shapes only)."""
    n, dev = len(b.keys), b.keys.device

    def rows():
        return torch.nn.functional.normalize(torch.randn(n, MD.D_OUT, generator=gen), dim=1).to(dev).requires_grad_(True)
    if mem.kind == "rich":
        uh = {h: (rows(), rows()) for h in ("env", "ss", "sc")}
        with _flop_counter()(display=False) as fc:
            loss, _ = mem.rich_terms(uh, b, vr)
            loss.backward()
    else:
        u1, u2 = rows(), rows()
        with _flop_counter()(display=False) as fc:
            loss, _ = mem.terms(u1, u2, b, v, xm)
            loss.backward()
    return fc.get_total_flops()


def flop_table(members, batches, heads):
    """Per-step FLOP proxy of every member on each stratum's calibration batch (module docstring, Compute):
    {encoder_fwd_bwd_per_window: {shared | rich: {stratum: F}}, loss_fwd_bwd: {M: {stratum: F}}, flops_per_step: {M: {stratum:
    512 windows x encoder + loss terms}}}; None when the counter is unavailable, {"error": ...} when counting failed (a proxy: the
    unit never fails for it)."""
    if _flop_counter() is None:
        return None
    try:
        gen = torch.Generator().manual_seed(FLOP_SEED)
        enc_f, loss_f, step_f = {}, {m: {} for m in members}, {m: {} for m in members}
        for s, b in batches.items():
            with torch.no_grad():
                v = heads["env"](b.y)
                vr = None
                if any(mem.kind == "rich" for mem in members.values()):
                    vr = {"env": v, "ss": heads["ss"](b.rich["ss"]), "sc": heads["sc"](b.rich["sc"])}
            xm = SM.DonorSampler.xm_view(b, np.roll(np.arange(len(b.seg_ids)), 1)) if "XM" in members else None
            x = b.x1[:FLOP_WINDOWS]
            for m, mem in members.items():
                arch = "rich" if mem.kind == "rich" else "shared"
                if s not in enc_f.setdefault(arch, {}):
                    enc_f[arch][s] = _enc_flops(mem.enc, x, b.layout, arch == "rich")
                loss_f[m][s] = _loss_flops(mem, b, v, vr, xm, gen)
                step_f[m][s] = 2 * SM.N_ROWS * enc_f[arch][s] + loss_f[m][s]
        return {"encoder_fwd_bwd_per_window": enc_f, "loss_fwd_bwd": loss_f, "flops_per_step": step_f}
    except Exception as ex:  # noqa: BLE001 (a proxy only; recorded)
        return {"error": f"{type(ex).__name__}: {ex}"}


def _part_flops(part, table, fpw):
    """train_flops_proxy {M: F} and validation_flops_proxy of a compute part (realised group steps per stratum x per-step FLOPs)."""
    st = part["strata_steps"]
    n = {s: st["main"].get(s, 0) + st["side"].get(s, 0) for s in sorted(set(st["main"]) | set(st["side"]))}
    per = (table or {}).get("flops_per_step")
    tf = None if per is None else {m: float(sum(c * f[s] for s, c in n.items() if s in f)) for m, f in per.items()}
    return {"steps_by_stratum": n, "train_flops_proxy": tf, "train_flops_proxy_total": None if tf is None else float(sum(tf.values())),
            "validation_flops_proxy": None if fpw is None else float(fpw * part["validation_windows"])}


def _joint_extra(members, timing, fp, mems):
    """joint_extra_compute: the joint members' measured extra compute (their second term) against AP and XP, and the second lambda
    member's own compute (EXECUTION §7, design §2.9)."""
    if not {"J1", "J025"} <= set(members):
        return None
    ts = {m: float(sum(timing["member_train_s"][m].values())) for m in members}
    tf = (fp or {}).get("train_flops_proxy") or {}
    extra = {j: {f"vs_{r}": {"train_s": ts[j] - ts[r], "train_flops_proxy": (tf[j] - tf[r]) if j in tf and r in tf else None}
                 for r in ("AP", "XP") if r in members} for j in ("J1", "J025")}
    return {"second_lambda_member": "J025", "member_steps": {j: mems[j].counts["main"]["steps"] + mems[j].counts["side"]["steps"]
                                                             for j in ("J1", "J025")},
            "member_train_s": ts, "member_train_flops_proxy": tf or None, "extra": extra,
            "second_term": "the cross_person term of J1 and J025 on the same forward pass as their audio term (J - AP: the cross "
                           "term; J - XP: the audio term)",
            "note": "measured, not assumed equal: synchronised member step seconds and the FLOP proxy; J025 (the second lambda) is "
                    "declared extra selection compute (§4.2) and trains like every other member"}


def _rich_readout(run, upstream, manifest):
    """§2.15 donor-side rich readout (descriptive): bridge_cal reconstruction r_bar of y_ss and y_sc (and the envelope) from ridges
    on the fixed fit segments, for APR (its _best.pt) and for the core AP (<core>_mAP_best.pt) of the same group."""
    from . import rich as R
    val = run.validator
    fit, cal = val.sets["fit"], val.sets["bridge_cal"]["queries"]
    rich = manifest["rich"]
    s_ss, s_sc = (np.asarray(rich[k], dtype=np.float64) for k in ("sigma_ss", "sigma_sc"))
    ss_f, sc_f = val.targets(fit, rich=True)
    ss_c, sc_c = val.targets(cal, rich=True)
    y_fit = {"env": val.y_fit, "ss": ss_f / s_ss, "sc": sc_f / s_sc}
    y_cal = {"env": val.targets(cal) / val.sigma, "ss": ss_c / s_ss, "sc": sc_c / s_sc}
    apr = run.scratch("APR")
    apr.load_state_dict(run.best["APR"]["best"]["enc"])
    ap = run.scratch("AP")
    ck = _load(upstream["core_ap"])
    ap.load_state_dict(ck["enc"] if "enc" in ck else ck)
    Uf, Uc = val.encode({"APR": apr, "AP_core": ap}, fit), val.encode({"APR": apr, "AP_core": ap}, cal)
    out = {name: R.rich_readout(Uf[name], y_fit, Uc[name], y_cal) for name in ("APR", "AP_core")}
    out["AP_core_checkpoint"] = os.path.basename(upstream["core_ap"])
    out["note"] = "descriptive; never used for selection (§2.15 Downstream)"
    return _py(out)


def train_donor_group(row, manifest, dev, ckpt_prefix, log, max_steps=None, *, upstream=None, cleanup=True, _hooks=None,
                      _validator=None, code_hash=None):
    """Train one donor-group row (all members in lockstep) and fill `log` with the group-record fields (module docstring).
    cleanup=False leaves the resume files for the caller, which deletes them after writing the record (run_donor)."""
    t_start = time.time()
    dev = torch.device(dev)
    gid, fam = row["experiment_id"], row["family_id"]
    ckdir = os.path.dirname(os.path.abspath(ckpt_prefix))
    out = os.path.dirname(ckdir)
    if os.path.basename(ckpt_prefix) != gid or os.path.basename(ckdir) != "ckpt":
        raise ValueError(f"ckpt_prefix must be <out>/ckpt/{gid}, got {ckpt_prefix}")
    cfg = check_spec(row, manifest)
    members, target, block, seed, objective = cfg["members"], cfg["target"], cfg["block"], cfg["seed"], cfg["objective"]
    last, ext, limit = cfg["rule"]
    if any(SEL.member_ckpt(out, gid, m, "best") != os.path.abspath(ckpt_prefix) + f"_m{m}_best.pt" for m in members):
        raise ValueError("checkpoint names: select.member_ckpt disagrees with ckpt_prefix")
    if upstream is None:
        upstream = resolve_upstreams(row, out)
    hor, cont = upstream.get("horizon"), upstream.get("continuation")
    budget = manifest["budget"]
    wsd = GroupWSD(int(budget["anchors_per_ep_eq"]), last=last, ext=ext, limit=limit,
                   trigger=tuple(m for m in TRIGGER_MEMBERS if m in members) if fam == SEL.DONOR else (),
                   adopted=None if hor is None else hor["H"], adopted_ceiling=bool(hor and hor["ceiling"]))
    if wsd.steps_at(H0) != _s0(budget):
        raise ValueError(f"budget: steps_at(30) = {wsd.steps_at(H0)} differs from the manifest S0 {_s0(budget)}")
    det = determinism(dev)                                 # before the first cuBLAS call of the process
    smp = SM.DonorSampler(manifest, target, block, seed, dev)
    heads = {k: h.to(dev).eval() for k, h in MD.fixed_heads(manifest, getattr(manifest, "root", None) or manifest.get("cache_root")).items()}
    uc = L.unknown_clock_families(manifest)
    seen = [n for n in C.VOCAB if n in set(manifest["seen"][target])]
    if sorted(seen) != sorted(manifest["seen"][target]):
        raise ValueError(f"manifest seen[{target}] holds names outside the vocabulary")
    rich = fam == SEL.RICH_DONOR

    def scratch(m):
        return MD.build_shared(seen, seen, seed, rich=(m == "APR")).to(dev)
    encs = {m: scratch(m) for m in members}
    ref = encs[members[0]]
    if not all(_identical(ref, e) for e in encs.values()):
        raise AssertionError("donor members are not initialised identically")
    cal = smp.calibration_batches()                        # its own generator (seed + 99): the main stream is untouched
    sigma = calibrate_bandwidths(encs["APR"] if rich else ref, smp, heads, rich=rich, batches=cal)
    if rich and objective == "CS_SINGLE" and not all((sigma.get("rich") or {}).get(h) for h in ("ss", "sc")):
        raise ValueError("CS rich heads: no calibration batch has present rich targets (sigma_ss / sigma_sc undefined)")
    validator = _validator or DevValidator(manifest, dev, heads["env"], rich=rich)
    mems = {m: _Member(m, encs[m], objective, sigma, uc, heads) for m in members}
    fpw = _flops_per_window(ref, C.MONTAGES["sparrkulee"], dev)
    ftab = flop_table(mems, cal, heads)
    del cal
    horizon = None if hor is None else {**hor, "check_stream": rich}
    run = _GroupRun(row=row, members=mems, sampler=smp, validator=validator, wsd=wsd, heads=heads, out=out, device=dev, sigma=sigma,
                    max_steps=max_steps, hooks=_hooks, horizon=horizon, inherit=cont, scratch=scratch,
                    meta={"manifest_sha256": getattr(manifest, "sha256", None), "code_hash": code_hash})
    run.run()
    readout = _rich_readout(run, upstream, manifest) if rich else None
    rec = run.finish()
    total = _compute_part(run.timing, run.counters, {m: mems[m].counts for m in members})
    fp = {"forward_flops_per_window": fpw, "validation_windows": run.timing["validation_windows"],
          **(ftab if ftab is not None else {"error": "torch.utils.flop_counter unavailable"}),
          **_part_flops(total, ftab, fpw),
          "counter": "torch.utils.flop_counter: matmul and convolution FLOPs (elementwise, reduction, indexing and cdist ops are not "
                     "counted), counted once per process on each stratum's calibration batch",
          "rule": "train: realised group steps per stratum (main run and side branch) x flops_per_step[M][stratum] = 512 windows x "
                  "encoder forward + backward per window + the member's loss terms forward + backward; validation: encoder forward "
                  "FLOPs per window (full SparrKULee montage) x validation windows; a proxy"}
    for k in ("compute_this_run", "compute_inherited"):
        if rec.get(k) is not None:
            rec[k].update(_part_flops(rec[k], ftab, fpw))
    rec.update({
        "donor_group": {"group": gid, "family": fam, "block": block, "target": target, "objective": objective, "seed": seed,
                        "members": list(members), "lambda": {m: LAMBDA[m] for m in members if m in LAMBDA},
                        "kinds": {m: KIND[m] for m in members}, "horizon_from": (hor or {}).get("gid"),
                        "continuation_of": (cont or {}).get("gid")},
        "budget": {k: budget.get(k) for k in ("N_SK", "anchors_per_ep_eq", "steps_per_ep_eq", "S0", "ep_eq0", "ep_eq_limit")},
        "objective": objective, "temperature": TEMPERATURE if objective == "NCE" else None, "bandwidth_multiplier": BANDWIDTH_MULTIPLIER,
        "optimizer": OPTIMIZER, "batch": BATCH, "montage_augmentation": MONTAGE_AUG, "control": CONTROL if "XM" in members else None,
        "unknown_clock_families": list(uc), "terms": TERMS[objective],
        "joint_extra_compute": _joint_extra(members, run.timing, fp, mems),
        "selection": {**SELECTION, "lambda_rule": SEL.LAMBDA_RULE, "gain_rule": GAIN_RULE, "h30": "min CE_dev over the fixed 30-ep-eq recipe "
                      "(stable validations up to 27 ep-eq and the 30-ep-eq decay, main run or side branch)",
                      "best": "min CE_dev over all validations, side branch included", "gainsel": "max dev gain over all validations",
                      "ties": "the earlier validation; non-finite CE = +inf, non-finite gain = -inf", "tau_grid": "logspace(-3, 2, 41) x sd(S)",
                      "ridge": f"relative penalty {REL_RIDGE} x mean diag(U^T U), intercept, no search"},
        "selection_level": SELECTION_LEVEL, "score_sets": validator.sizes(), "sampler": smp.describe(),
        "flop_proxy": fp, "rich_readout": readout, "determinism": det, "seconds": round(time.time() - t_start, 1),
        "resume_cleanup": "train_donor_group (end of training)" if cleanup else "the caller, after the record is written (run_donor)",
    })
    log.update(_py(rec))
    if cleanup:
        remove_resume_files(out, gid)
    return log
