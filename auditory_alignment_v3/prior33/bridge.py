"""E34_PUBLIC_PRIOR source sound bridge (module M6; private/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN.md §2.11, §2.13,
§6.1 `bridge.py`, §6.6 M6; contract aln33_env64_125ms_v1; inherited PUBLIC_PRIOR_EXECUTION_v3_3.md §6 and public_prior_v3_3.yaml
source_sound_bridge: fit donor_fit_only, calibrate donor_development_only, frozen_on_target_zero_shot).

One bridge per slot (donor group, member): every member of a donor set gets the same procedure on the same rows.
  fit rows     the manifest's bridge.fit_rows[target] (C6: 2,000 donor-fit listener segments drawn with the stratum weights, seed
               20261016), every tick (x 250 = 500,000 rows), on the stratum cohort's own layout, with the per-row montage subset of
               sampler.bridge_rows (as in training) and the masked (piece, channel) cells zeroed
  B_uni        ridge with intercept U -> standardised target y / sigma (8 dims; the manifest standardiser, mu = 0), alpha in
               logspace(-4, 8, 13) chosen on the bridge_cal queries by the mean per-dimension Pearson r (the ev1 `corr` criterion);
               B_uni is the donor-fit solution at alpha* (no refit on bridge_cal)
  native       NCE: cosine u . v (no fit); CS_SINGLE: ridge U -> v (32 dims), alpha by MSE on the bridge_cal queries. Not
               applicable (recorded) for NCE encoders never trained against v: XP, XM, XPC
  tau(n)       n in {64, 128, 256, 512, 1024}: the manifest's bridge_cal queries, each scored against its own candidate plus n - 1
               random bridge_cal content segments (seed 20261017); tau = ev1.Readouts.calibrate (unchanged) on that matrix, for the
               unified and the native readout
  B_uni_cal    sensitivity: fitted on the bridge_cal rows uni_cal_sample() fixes, 2,000 participant-balanced segments of the
               manifest's pools.bridge_cal.sparrkulee (the B_uni count; the whole pool when smaller), every tick, full montage;
               alpha by the 2-fold participant split of the manifest (bridge.cal_split) on those rows; its tau cross-fitted on the
               same split (B on fold a's rows, tau on fold b's queries, and vice versa; geometric mean), per pool size. The folds
               share presentations: cross-fitting over listeners only
  artefact     artefact_probe(): the frozen B_uni on the insert-phone control run (SparrKULee role control_artefact): r_own
               against its own envelope and r_other against other segments of its family; descriptive, never used for selection
Output: ckpt/<bid>_bridge.npz (save_bridge / load_bridge; numpy allow_pickle=False; never offloaded) and FrozenBridge, the
ev1.Readouts frozen at the bridge that zeroshot.py hands to ev1.evaluate_continuous. The npz names the sha256 of the donor
checkpoint file it was fitted on (checkpoint_sha256); run_zeroshot.py refuses a bridge fitted on another checkpoint.
Accounting (inherited contract §6: the donor bridge's audio-pair count and compute are counted explicitly): the record's
top-level n_pairs (audio-EEG tick pairs the primary bridge B_uni + tau(n) was fitted or calibrated on: fit rows + bridge_cal
query rows), n_pairs_uni_cal (the sensitivity's fit rows), n_pairs_all (every distinct pair the unit fitted or calibrated on)
and bridge_seconds (wall-clock seconds of fit_bridge; the parts under bridge.seconds); bridge_row_info hands them to the
zero-shot records.

Imports: this file is hashed into prior33_bridge and prior33_zeroshot (§6.3). Its top level imports only contract, views, model and
select of prior33 (the prior33_zeroshot code group); sampler.py and losses.py (prior33_bridge only) are imported inside the
bridge-fitting functions, so a zero-shot unit never executes a file outside its code hash.

Interpretations (the design names the object but not every detail; each is a deviation of the M6 summary):
- Standardised target: y / sigma with the manifest standardiser (mu = 0), i.e. a_mu = 0 and a_sd = sigma, shared by B_uni and
  B_uni_cal (the npz holds one a_mu / a_sd pair). With an unpenalised intercept the ridge prediction is affine-equivariant per
  target column, and the corr criterion and the unified score (ev1._zt z-scores each segment x dimension) are invariant to any
  positive per-dimension affine map: alpha*, every unified score and every tau equal those of ev1's own (mean, SD + 1e-8)
  standardisation of the fit rows.
- Validation rows: alpha (unified and native) of the primary bridge is chosen on the manifest's bridge.cal_queries (300
  participant-balanced bridge_cal segments at design scale, all 250 ticks, full montage, no augmentation, as validation in
  §2.10); tau(n) uses the same queries (§2.11).
- B_uni_cal's "bridge_cal rows" (§2.11 gives no count): uni_cal_sample(), N_UNI_CAL = 2,000 segments of pools.bridge_cal.sparrkulee,
  the bridge_cal pool the tau candidates come from (6,366 listener segments at design scale, §3.2), so that the B_uni vs
  B_uni_cal sensitivity does not also change the bridge's sample size (2,000 x 250 rows each); the whole pool when it holds
  fewer. Drawn here, not by C6: participant-balanced as manifest.py draws bridge.cal_queries (water-filling over the
  participants in sorted order, the remainder to participants drawn by the generator, uniform without replacement within a
  participant), generator SeedSequence([20261016, UNI_CAL_TAG = 0x43414C46]); the same rows for every member (their sha256 is
  uni_cal_rows_sha256). Every row must be a bridge_cal row of a participant of bridge.cal_split. Full montage (the design names
  montage augmentation only for the bridge-fit rows). The rows may overlap the queries; a fold fit never meets the queries it
  calibrates (the folds are disjoint by participant).
- Inherited contract vs design (recorded): public_prior_v3_3.yaml source_sound_bridge.fit = donor_fit_only. The primary B_uni is
  the donor-fit solution at alpha* (never refitted on fit + bridge_cal); B_uni_cal is fitted on bridge_cal, a donor-development
  partition (§3.2), as the design's separately labelled sensitivity: zero-shot records carry it as eval_uni_cal, and it never
  enters primary claims.
- Native readout not applicable: §2.11 names cross_person NCE and XM NCE; XPC NCE (the CSX cross_person member, §2.16) is added
  for the same reason (an NCE encoder never trained against v). prior33.analysis.NATIVE_NA_SLOTS holds the same three slots.
- Slots: only the §2.11 slots select.SLOTS (AP, XP, J*, XM, APR, APC, XPC); a row naming a concrete joint member (J1, J025) is
  refused, so J* is always resolved by the lambda rule on the group record.
- Native ridge alpha grid: ev1.Readouts' native default logspace(-3, 3, 7) (the design names only the MSE criterion).
- tau pools: per query its own candidate plus m - 1 others drawn without replacement, m = min(n, number of bridge_cal content
  segments) (the realised size is recorded; the fixture's pools are smaller than the design's); one generator default_rng(20261017),
  in ascending n and then query order; the same draws serve the unified, the native and the cross-fitted tau of every member.
  Zero-shot uses the table entry whose realised pool size is nearest in log2 to the target's test-pool size (ties: the smaller n).
- tau_cal is tabulated by pool size like tau(n) (a sensitivity evaluation at the target's pool size needs it); the records' scalar
  tau_cal is the entry at n = 256 (N_REF, the centre of the table), the full table is tau_cal_by_pool_size.
- bridge_cal_r = mean over the bridge_cal queries of the unified own score S(q, own) under B_uni (the reconstruction r of §2.10's
  r_own); bridge_cal_corr = the pooled criterion at alpha*.
- Kernel-dependence bandwidths (sigma_u, sigma_v; "kernel dependence uses the donor sigma"): read from the donor checkpoint, else
  from the donor-group record (donor_bandwidths: search order documented there). A CS_SINGLE member without a donor sigma_u is
  refused. Otherwise a missing value falls back to the median off-diagonal distance (losses.calibrate_sigma) of the frozen
  encoder's U (sigma_u) or of the head's v (sigma_v) on 512 seeded bridge-fit rows; the source is recorded.
- Artefact probe: "other audiobook_1 segments" = the unique (presentation, s) content segments of the artefact presentation's
  family (any role: audio only, no other listener's EEG is read) whose family-clock start lies >= SPAN_ENV + NEIGHBOR = 455 samples
  from the query's (no overlapping or neighbouring audio).
- The donor checkpoint must load with torch.load(weights_only=True) (tensors and plain containers / numbers): the state dict, or
  a dict holding it under "enc" (model.load_donor semantics; donor_train.py's format prior33_donor_member_v1); its rich.* heads are
  dropped and listed. Its provenance fields (format, group, member, kind "best", contract, manifest, objective) and its stored
  audio head ("head": the manifest's shared head) are checked when present; the bandwidths are its "sigma" dict.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import time
from dataclasses import dataclass, field

import numpy as np
import torch

from auditory_alignment import evaluate as ev1
from auditory_alignment_v3 import core

from . import contract as C
from . import model as M
from . import select as SEL
from . import views as V

SCHEMA = "prior33_bridge_v1"
METHOD = "ridge_u_to_stdenv8_v1"
FIT_ROWS = "donorfit_2000seg_seed20261016"
ALPHA_RULE = "logspace(-4,8,13)|bridge_cal_corr"
TEMPERATURE_RULE = "bridge_cal_ce_by_poolsize_v1"
SENSITIVITY_RULE = "bridge_cal_fit_2fold_tau_crossfit_v1"
SPEC_RULES = {"bridge": METHOD, "fit_rows": FIT_ROWS, "alpha": ALPHA_RULE, "temperature": TEMPERATURE_RULE,
              "sensitivity": SENSITIVITY_RULE}          # §4.3 bridge spec fields: a row naming another method is refused
UNI_ALPHAS = np.logspace(-4, 8, 13)                    # §2.11 (= ev1.Readouts' unified grid)
NAT_ALPHAS = np.logspace(-3, 3, 7)                     # ev1.Readouts' native default (CS ridge U -> v)
TAU_GRID = "ev1.Readouts.calibrate: logspace(-3, 2, 41) x sd(S)"
POOL_SIZES = (64, 128, 256, 512, 1024)                 # §2.11 tau(n)
N_REF = 256                                            # the records' scalar tau_cal (module docstring)
OBJECTIVES = ("NCE", "CS_SINGLE")
NATIVE_NA_SLOTS = ("XP", "XM", "XPC")                  # NCE encoders never trained against v (§2.11)
VIEWS = ("primary", "uni_cal")                         # B_uni + tau(n); the sensitivity B_uni_cal + tau_cal(n)
CHUNK = 32                                             # segments per encoder pass (32 x 250 = 8,000 windows); read at call time
SIGMA_FALLBACK_ROWS = 512
N_UNI_CAL = 2000                                       # B_uni_cal fit segments (the B_uni count; module docstring)
UNI_CAL_TAG = 0x43414C46                               # "CALF": B_uni_cal rows from SeedSequence([BRIDGE_SEED, this tag])
UNI_CAL_RULE = (f"{N_UNI_CAL} segments of pools.bridge_cal.sparrkulee (all when fewer), participant-balanced (water-filling over "
                f"the participants in sorted order, remainder by the generator, uniform without replacement within a participant), "
                f"SeedSequence([{C.BRIDGE_SEED}, {UNI_CAL_TAG:#x}]); every tick, full montage; folds = bridge.cal_split")
PAIRS_RULE = ("n_pairs: audio-EEG tick pairs (one EEG input window with its own envelope window) the primary bridge was fitted or "
              "calibrated on = bridge-fit rows + bridge_cal query rows; n_pairs_uni_cal: B_uni_cal's fit rows; n_pairs_all: the "
              "fit rows plus the distinct bridge_cal rows (queries and B_uni_cal rows); the tau pools' other-candidate scores and "
              "the artefact probe (descriptive) are not counted")
OTHER_MIN_SEP = C.SPAN_ENV + C.NEIGHBOR                # 455: artefact probe "other" segments (module docstring)
MANIFEST_PATH = os.path.join(V.CACHE_ROOT, "manifest.json")                 # §6.2, as run_donor.py / run_target.py
PRIVATE_MANIFEST = os.path.join(core.OUT, "aln34", "prior33", "manifest.json")  # §6.2: the 0444 copy (cache root CACHE_ROOT)
CKPT_FORMAT = "prior33_donor_member_v1"                                       # donor_train.py member checkpoints
SELECTION_LEVEL = ("donor dev: the slot's donor checkpoint is its min CE_dev _best.pt (J* by the lambda rule on donor dev); the "
                   "bridge alpha and tau(n) come from donor bridge_cal (SparrKULee participants and content disjoint from donor fit "
                   "and dev); no target data")
NORMALISATION_ACCESS = ("donor data only: the donor caches (mode A input, z-scored per donor participant x channel); the bridge reads "
                        "no target-cohort file, row or statistic")
_NPZ_ARRAYS = ("B_uni", "alpha_uni", "a_mu", "a_sd", "B_nat", "alpha_nat", "tau_pool_sizes", "tau_pool_realised", "tau_unified",
               "tau_native", "B_uni_cal", "alpha_uni_cal", "tau_cal", "tau_cal_folds", "sigma_u", "sigma_v", "native_applicable")
_META_TEXT = ("bridge_id", "donor_group", "slot", "member", "target", "manifest_sha256", "target_contract", "checkpoint_sha256",
              "fit_rows_sha256", "cal_rows_sha256", "uni_cal_rows_sha256", "tau_draws_sha256")   # npz text fields = meta values
_NPZ_TEXT = ("schema", "objective", "native") + _META_TEXT + ("meta_json", "info_json")
_SIGMA_DICTS = ("bandwidths", "objective_calibration", "calibration", "sigma", "kernel")

_EV1_READOUTS = ev1.Readouts
if _EV1_READOUTS.__module__ != "auditory_alignment.evaluate" or _EV1_READOUTS.__qualname__ != "Readouts":
    raise ImportError("prior33.bridge must be imported while auditory_alignment.evaluate.Readouts is the original class")


class DependencyError(RuntimeError):
    """An upstream unit (donor group, checkpoint, bridge) is missing or incomplete."""


class ZeroShotAccessError(RuntimeError):
    """Something would be fitted or calibrated on target data in a frozen (zero-shot) evaluation."""


# ---------------------------------------------------------------------------------------------------------- small helpers
def jsonable(o):
    """Recursively JSON-native (numpy scalars / arrays -> Python numbers / lists; tuples -> lists; keys -> str)."""
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, np.ndarray):
        return jsonable(o.tolist())
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if torch.is_tensor(o):
        return jsonable(o.detach().cpu().numpy())
    return o


def sha_json(o):
    return hashlib.sha256(V._canon(jsonable(o)).encode()).hexdigest()


def file_sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def native_applicable(objective, slot):
    """False for NCE encoders never trained against v (cross_person NCE, XM NCE, XPC NCE; §2.11)."""
    return not (objective == "NCE" and SEL.canonical_slot(slot) in NATIVE_NA_SLOTS) if slot is not None else True


def bindable(row):
    """A copy of a plan row that core.bind accepts (subject_fold / content_fold present; bridge rows may carry None)."""
    r = dict(row)
    r.setdefault("subject_fold", None)
    r.setdefault("content_fold", None)
    return r


def fallback_record(row, out, b=None):
    """The record of a unit whose core.bind or core.new_record raised (a row without spec.objective or seed, a family that
    FAMILY_GROUP does not list, no device name): core.new_record's identity fields as far as they can be filled, so that the
    runner still writes the failure as a technical_failed record (§6.1) instead of letting it escape (run_target.py's rule)."""
    os.makedirs(os.path.join(out, "units"), exist_ok=True)
    fam = row.get("family_id")
    try:
        ch = core.code_hash(fam)
    except Exception:  # noqa: BLE001 (an unregistered family: code_hash / code_group stay None)
        ch = None
    try:
        device = torch.cuda.get_device_name(0)
    except Exception:  # noqa: BLE001
        device = None
    spec = row.get("spec") if isinstance(row.get("spec"), dict) else {}
    return {"experiment_id": row["experiment_id"], "row": row, "bound_row": b, "code_hash": ch,
            "code_group": core.FAMILY_GROUP.get(fam) if isinstance(fam, str) else None, "runner": "auditory_alignment_v3",
            "status": "running", "device": device, "target_contract": None, "information_stratum": spec.get("information_stratum")}


def check_spec_rules(row):
    """The §4.3 bridge method fields of a row, when present, must name the method implemented here."""
    s = row.get("spec") or {}
    bad = {k: s[k] for k, v in SPEC_RULES.items() if s.get(k) is not None and s[k] != v}
    if s.get("artefact_probe") is not None and s["artefact_probe"] is not True:
        bad["artefact_probe"] = s["artefact_probe"]
    if bad:
        raise ValueError(f"{row.get('experiment_id')}: bridge spec fields {bad} name another method than {SPEC_RULES} (this code)")


def open_row_manifest(row, path=None, cache_root=None):
    """The frozen manifest of a row, opened only with its spec.manifest_sha256 (views.open_manifest): `path` (cache root
    `cache_root`, else the manifest's own), else the first of MANIFEST_PATH and PRIVATE_MANIFEST that exists and has that sha256
    (cache root views.CACHE_ROOT), as run_donor.py and run_target.py resolve it. spec.target_contract (when the row and the
    manifest both carry it) must equal the manifest's target_contract (full sha, or a prefix of >= 16 hex digits)."""
    s = row.get("spec") or {}
    paths = [path] if path is not None else [PRIVATE_MANIFEST, MANIFEST_PATH]
    try:
        man = V.open_for_row(row, paths=paths, cache_root=cache_root or (None if path else V.CACHE_ROOT),
                             rich_paths=[os.path.join(os.path.dirname(p), V.MANIFEST_RICH) for p in paths])
    except FileNotFoundError as exc:
        raise DependencyError(str(exc)) from exc
    tc, mt = s.get("target_contract"), man.get("target_contract")
    if tc is not None and mt is not None and not (len(str(tc)) >= 16 and str(mt).startswith(str(tc))):
        raise ValueError(f"{row.get('experiment_id')}: spec.target_contract {str(tc)[:16]}... differs from the manifest's "
                         f"{str(mt)[:16]}...")
    return man


# ---------------------------------------------------------------------------------------------------------- donor member
def encoder_state(ckpt):
    """The SharedEncoder state dict of a donor checkpoint (the dict itself, its "enc" entry, or a module's state_dict())."""
    if isinstance(ckpt, torch.nn.Module):
        ckpt = ckpt.state_dict()
    if isinstance(ckpt, dict) and "spatial.W" not in ckpt and isinstance(ckpt.get("enc"), dict):
        ckpt = ckpt["enc"]
    if not isinstance(ckpt, dict) or "spatial.W" not in ckpt or "spatial.seen" not in ckpt:
        raise ValueError("the donor checkpoint holds no SharedEncoder state (spatial.W / spatial.seen)")
    return dict(ckpt)


def check_ckpt_provenance(ckpt, gid, member, row, kind="best"):
    """The provenance fields donor_train.py writes into a member checkpoint (format prior33_donor_member_v1), when present, must
    name this group, member, kind, contract and manifest (as run_target.py checks them). -> the format, or None (no fields)."""
    if not isinstance(ckpt, dict) or "format" not in ckpt:
        return None
    want = {"format": CKPT_FORMAT, "group": gid, "member": member, "kind": kind, "contract": C.CONTRACT}
    bad = {k: (ckpt.get(k), v) for k, v in want.items() if ckpt.get(k) != v}
    ms, rs = ckpt.get("manifest_sha256"), (row.get("spec") or {}).get("manifest_sha256")
    if ms and rs and not (str(ms).startswith(str(rs)) or str(rs).startswith(str(ms))):
        bad["manifest_sha256"] = (str(ms)[:16], str(rs)[:16])
    if ckpt.get("objective") is not None and ckpt["objective"] != (row.get("spec") or {}).get("objective"):
        bad["objective"] = (ckpt["objective"], (row.get("spec") or {}).get("objective"))
    if bad:
        raise ValueError(f"the donor checkpoint does not belong to this slot / contract: {bad}")
    return ckpt["format"]


def check_ckpt_head(ckpt, manifest, root=None):
    """A checkpoint's fixed audio head (donor_train.py stores it under "head"), when present, must be the manifest's shared head
    (std.mu = 0, std.sd = sigma, the stored P): the bridge and the zero-shot rows use exactly the donor's target coordinates."""
    if not isinstance(ckpt, dict) or not isinstance(ckpt.get("head"), dict):
        return False
    ref = M.fixed_heads(manifest, V.manifest_root(manifest, root))["env"].state_dict()
    got = ckpt["head"]
    bad = [k for k in ref if k not in got or tuple(got[k].shape) != tuple(ref[k].shape) or not torch.equal(got[k].float().cpu(), ref[k].float())]
    if bad or set(got) != set(ref):
        raise ValueError(f"the donor checkpoint's audio head differs from the manifest's shared head ({bad or sorted(set(got) ^ set(ref))})")
    return True


def donor_encoder(ckpt, manifest, target, device="cpu", layout=None):
    """A SharedEncoder carrying the donor member's state (strict model.load_donor, open_new=False: names the donor never saw keep
    zero weight and are never read), default row order `layout` (bridge: SparrKULee's; zero-shot: the target layout). The donor's
    seen set must equal manifest.seen[target] (the leave-target-out donor union). -> (encoder in eval mode on device, tensor map)."""
    check_ckpt_head(ckpt, manifest)
    state = encoder_state(ckpt)
    seen = sorted(C.VOCAB[i] for i in torch.nonzero(torch.as_tensor(state["spatial.seen"]).bool()).flatten().tolist())
    exp = (manifest.get("seen") or {}).get(target)
    if exp is not None and seen != sorted(M.names_of(exp)):
        raise ValueError(f"donor encoder: seen set {seen} differs from the manifest's donor union for target {target}")
    lay = M.names_of(layout if layout is not None else C.MONTAGES["sparrkulee"])
    enc = M.build_shared(lay, lay, 0)              # every tensor is replaced by the donor's below
    tmap = M.load_donor(enc, state, lay, open_new=False, strict=True)
    return enc.to(device).eval(), tmap


def _finite_pos(v):
    try:
        x = float(v.item() if torch.is_tensor(v) else v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) and x > 0 else None


def donor_bandwidths(ckpt, group_record=None, member=None):
    """{"sigma_u", "sigma_v", "source"} from the donor run (§2.8: fixed for the run, saved in the checkpoint). Search order, first
    finite positive value per bandwidth: the checkpoint's top level, then its dicts bandwidths / objective_calibration /
    calibration / sigma / kernel; the group record's members[member] (and the same dicts inside it); the group record's top
    level (and the same dicts). Keys sigma_u / sigma_v (or u / v inside the dicts). Missing values are None."""
    cands = []

    def add(src, d):
        if isinstance(d, dict):
            cands.append((src, d))
            for k in _SIGMA_DICTS:
                if isinstance(d.get(k), dict):
                    cands.append((f"{src}.{k}", d[k]))
    add("checkpoint", ckpt if isinstance(ckpt, dict) else None)
    if isinstance(group_record, dict):
        mem = (group_record.get("members") or {}).get(member) if member is not None else None
        add(f"group_record.members.{member}", mem)
        add("group_record", group_record)
    out = {"sigma_u": None, "sigma_v": None, "source": {"sigma_u": None, "sigma_v": None}}
    for key, alt in (("sigma_u", "u"), ("sigma_v", "v")):
        for src, d in cands:
            x = _finite_pos(d.get(key, d.get(alt) if src.split(".")[-1] in _SIGMA_DICTS else None))
            if x is not None:
                out[key], out["source"][key] = x, src
                break
    return out


def load_member(row, rows, out):
    """The donor member a bridge / zero-shot row loads: its group row and complete record, the concrete member (J* by the lambda
    rule), and the member's _best.pt (torch.load weights_only=True). DependencyError when a record or the checkpoint is missing."""
    sl = SEL.slot_of(row)
    if sl is None:
        raise ValueError(f"{row.get('experiment_id')}: the row has no donor slot")
    gid, slot = sl
    if slot not in SEL.SLOTS:
        raise ValueError(f"{row.get('experiment_id')}: member {slot!r} is not a §2.11 slot {list(SEL.SLOTS)} (a concrete joint member "
                         f"would bypass the lambda rule; J* is resolved on the group record)")
    g = SEL.group_row(row, rows)
    s, gs = row.get("spec") or {}, g.get("spec") or {}
    if g.get("dataset") != row.get("dataset") or gs.get("objective") != s.get("objective"):
        raise ValueError(f"{row.get('experiment_id')}: (dataset, objective) differ from donor group {gid}")
    if gs.get("manifest_sha256") and s.get("manifest_sha256") and gs["manifest_sha256"] != s["manifest_sha256"]:
        raise ValueError(f"{row.get('experiment_id')}: donor group {gid} was registered on another manifest")
    if row.get("seed") != g.get("seed") or (s.get("donor_seed") is not None and int(s["donor_seed"]) != int(g["seed"])):
        raise ValueError(f"{row.get('experiment_id')}: donor seed (row {row.get('seed')}, spec {s.get('donor_seed')}) differs from donor "
                         f"group {gid}'s seed {g.get('seed')}")
    rec = SEL.load_record(out, gid)
    if rec is None:
        raise DependencyError(f"donor group {gid}: no complete record units/{gid}.json")
    if rec.get("experiment_id") != gid:
        raise DependencyError(f"the record units/{gid}.json belongs to {rec.get('experiment_id')}")
    if slot == SEL.JOINT:
        SEL.check_group_record(rec, g)          # the pinned record layout and the lambda rule (as run_target.py)
    member = SEL.member_of(row, rec)
    ck = SEL.member_ckpt(out, gid, member, "best")
    if not os.path.exists(ck):
        raise DependencyError(f"donor group {gid}: checkpoint {os.path.basename(ck)} of member {member} is missing")
    try:
        ckpt = torch.load(ck, map_location="cpu", weights_only=True)
    except Exception as ex:  # noqa: BLE001 (re-raised with the contract)
        raise ValueError(f"{os.path.basename(ck)}: the donor checkpoint must load with torch.load(weights_only=True) "
                         f"(tensors and plain containers / numbers): {type(ex).__name__}: {ex}") from None
    fmt = check_ckpt_provenance(ckpt, gid, member, row)
    return {"gid": gid, "slot": slot, "member": member, "group": g, "group_record": rec, "ckpt_path": ck, "ckpt": ckpt,
            "ckpt_sha256": file_sha256(ck), "ckpt_format": fmt}


# ---------------------------------------------------------------------------------------------------------- ridge (ev1 semantics)
def _design(X):
    return np.c_[np.asarray(X, dtype=np.float64), np.ones(len(X))]


def _solve(G, H, a):
    R = a * np.eye(G.shape[0])
    R[-1, -1] = 0
    return np.linalg.solve(G + R, H)


def ridge_err(P, Yv, crit):
    """ev1._ridge's validation error (lower is better): -mean per-dimension Pearson r ('corr') or the mean squared error."""
    if crit == "corr":
        Pc, Yc = P - P.mean(0), Yv - Yv.mean(0)
        return -float(((Pc * Yc).sum(0) / (np.sqrt((Pc ** 2).sum(0) * (Yc ** 2).sum(0)) + 1e-12)).mean())
    if crit == "mse":
        return float(((P - Yv) ** 2).mean())
    raise ValueError(f"ridge criterion {crit!r}")


def ridge_select(X, Y, alphas, Xv, Yv, crit):
    """ev1._ridge(X, Y, alphas, Xv, Yv, crit) (ridge with an unpenalised intercept; the first alpha with the lowest validation
    error) plus the criterion curve -> (B [d + 1, k], alpha, curve [{alpha, err}])."""
    X1, Xv1 = _design(X), _design(Xv)
    Y, Yv = np.asarray(Y, dtype=np.float64), np.asarray(Yv, dtype=np.float64)
    G, H = X1.T @ X1, X1.T @ Y
    best, curve = None, []
    for a in alphas:
        B = _solve(G, H, a)
        err = ridge_err(Xv1 @ B, Yv, crit)
        curve.append({"alpha": float(a), "err": err})
        if best is None or err < best[0]:
            best = (err, float(a), B)
    return best[2], best[1], curve


def ridge_select_2fold(X, Y, fold, alphas, crit="corr"):
    """alpha by a 2-fold split (fit on fold k, error on fold 1 - k, mean of both directions; the first lowest), then the fit on all
    rows at alpha* and the two fold fits at alpha* -> (B_all, alpha, (B_fold0, B_fold1), curve)."""
    fold = np.asarray(fold)
    f = [np.flatnonzero(fold == k) for k in (0, 1)]
    if not (len(f[0]) and len(f[1])) or len(f[0]) + len(f[1]) != len(fold):
        raise ValueError("ridge_select_2fold: two non-empty folds 0 / 1 are required")
    X1, Y = _design(X), np.asarray(Y, dtype=np.float64)
    G = [X1[i].T @ X1[i] for i in f]
    H = [X1[i].T @ Y[i] for i in f]
    best, curve = None, []
    for a in alphas:
        e = [ridge_err(X1[f[1 - k]] @ _solve(G[k], H[k], a), Y[f[1 - k]], crit) for k in (0, 1)]
        err = float(np.mean(e))
        curve.append({"alpha": float(a), "err_fold0_to_fold1": e[0], "err_fold1_to_fold0": e[1], "err": err})
        if best is None or err < best[0]:
            best = (err, float(a))
    a = best[1]
    B_all = _solve(X1.T @ X1, X1.T @ Y, a)
    return B_all, a, tuple(_solve(G[k], H[k], a) for k in (0, 1)), curve


# ---------------------------------------------------------------------------------------------------------- frozen readout
class FrozenBridge(_EV1_READOUTS):
    """auditory_alignment.evaluate.Readouts frozen at a donor bridge (§2.13). ev1.Readouts.__init__ (the training-side fit) is
    bypassed; this class defines every attribute ev1.evaluate_continuous and Readouts.scores read: objective, B_uni, alpha_uni,
    a_mu, a_sd, B_nat / alpha_nat (CS_SINGLE; None for NCE, whose native score is the cosine), tau {"unified", "native"}.
    scores() is ev1's, inherited unchanged; calibrate() raises (nothing is calibrated on target queries)."""

    def __init__(self, objective, B_uni, a_mu, a_sd, *, alpha_uni, B_nat=None, alpha_nat=None, tau=None, view="primary", info=None):
        if objective not in OBJECTIVES:
            raise ValueError(f"FrozenBridge: objective {objective!r} (contract objectives {OBJECTIVES})")
        B = np.asarray(B_uni, dtype=np.float64)
        if B.shape != (M.D_OUT + 1, C.N_TGT) or not np.isfinite(B).all():
            raise ValueError(f"FrozenBridge: B_uni [{M.D_OUT + 1}, {C.N_TGT}] finite expected, got {B.shape}")
        mu, sd = (np.array(v).reshape(-1) for v in (a_mu, a_sd))      # dtype kept (module docstring of zeroshot.py: ev1 parity)
        if mu.dtype.kind != "f" or sd.dtype.kind != "f" or mu.shape != (C.N_TGT,) or sd.shape != (C.N_TGT,) or \
                not (np.isfinite(mu).all() and np.isfinite(sd).all() and (sd > 0).all()):
            raise ValueError("FrozenBridge: a_mu / a_sd float [8], finite, with a_sd > 0 expected")
        self.objective, self.B_uni, self.alpha_uni, self.a_mu, self.a_sd = objective, B, float(alpha_uni), mu, sd
        if objective == "CS_SINGLE":
            Bn = None if B_nat is None else np.asarray(B_nat, dtype=np.float64)
            if Bn is None or Bn.shape != (M.D_OUT + 1, M.D_OUT) or not np.isfinite(Bn).all() or alpha_nat is None:
                raise ValueError(f"FrozenBridge: CS_SINGLE needs the native ridge B_nat [{M.D_OUT + 1}, {M.D_OUT}] and alpha_nat")
            self.B_nat, self.alpha_nat = Bn, float(alpha_nat)
        else:
            self.B_nat, self.alpha_nat = None, None
        self.tau = None
        if tau is not None:
            t = {k: float(tau[k]) for k in ("unified", "native")}
            if not all(math.isfinite(v) and v > 0 for v in t.values()):
                raise ValueError(f"FrozenBridge: temperatures must be finite and > 0, got {t}")
            self.tau = t
        self.view, self.info = view, dict(info or {})

    @classmethod
    def from_bridge(cls, bridge, n_pool, view="primary"):
        """The frozen readout of `bridge` for a test pool of n_pool candidates: B_uni and tau(n) (view "primary") or B_uni_cal and
        tau_cal(n) with the native readout unchanged ("uni_cal"); tau from the table entry nearest in log2 (bridge.entry)."""
        k, n_nom, n_real = bridge.entry(n_pool)
        if view == "primary":
            B, alpha, tu = bridge.B_uni, bridge.alpha_uni, bridge.tau_unified[k]
        elif view == "uni_cal":
            B, alpha, tu = bridge.B_uni_cal, bridge.alpha_uni_cal, bridge.tau_cal[k]
        else:
            raise ValueError(f"FrozenBridge.from_bridge: view {view!r} not in {VIEWS}")
        info = {"bridge_id": bridge.meta.get("bridge_id"), "view": "B_uni" if view == "primary" else "B_uni_cal",
                "n_test_candidates": int(n_pool), "pool_entry": int(n_nom), "pool_entry_realised": int(n_real),
                "native_readout": bridge.native, "native_applicable": bool(bridge.native_applicable)}
        return cls(bridge.objective, B, bridge.a_mu, bridge.a_sd, alpha_uni=alpha, B_nat=bridge.B_nat, alpha_nat=bridge.alpha_nat,
                   tau={"unified": tu, "native": bridge.tau_native[k]}, view=view, info=info)

    def calibrate(self, S, own):
        raise ZeroShotAccessError("FrozenBridge.calibrate: the zero-shot temperature is the donor bridge's tau(n); nothing is "
                                  "calibrated on target queries (§2.13)")


class _TauHolder:
    tau = None


def calibrate_tau(S, own=None):
    """ev1.Readouts.calibrate, unchanged, on candidate score matrices {kind: [nq, n]} with the true column `own` (default 0)."""
    h = _TauHolder()
    nq = len(next(iter(S.values())))
    _EV1_READOUTS.calibrate(h, S, np.zeros(nq, dtype=np.int64) if own is None else np.asarray(own))
    return dict(h.tau)


def pool_draws(own, n_cand, sizes=POOL_SIZES, seed=C.TAU_POOL_SEED):
    """{n: int64 [nq, m]}: per query its own candidate (column 0) plus m - 1 other candidates drawn without replacement, m =
    min(n, n_cand); one generator default_rng(seed), ascending n, then query order (module docstring)."""
    own = np.asarray(own, dtype=np.int64)
    if n_cand < 2 or not len(own) or own.min() < 0 or own.max() >= n_cand:
        raise ValueError(f"pool_draws: {len(own)} queries over {n_cand} candidates")
    rng = np.random.default_rng(seed)
    out = {}
    for n in sizes:
        m = min(int(n), int(n_cand))
        cols = np.empty((len(own), m), dtype=np.int64)
        cols[:, 0] = own
        for q, o in enumerate(own):
            pick = rng.choice(n_cand - 1, size=m - 1, replace=False)
            cols[q, 1:] = pick + (pick >= o)           # skip the own candidate
        out[int(n)] = cols
    return out


def _take(S, cols, rows=None):
    q = np.arange(len(S)) if rows is None else np.asarray(rows)
    return S[q[:, None], cols if rows is None else cols[q]]


# ---------------------------------------------------------------------------------------------------------- bridge data
@dataclass
class BridgeData:
    """One fitted bridge (the npz contents; §2.11 Output). Tables are aligned with pool_sizes."""
    objective: str
    B_uni: np.ndarray
    alpha_uni: float
    a_mu: np.ndarray
    a_sd: np.ndarray
    B_nat: np.ndarray | None
    alpha_nat: float | None
    pool_sizes: np.ndarray
    pool_realised: np.ndarray
    tau_unified: np.ndarray
    tau_native: np.ndarray
    B_uni_cal: np.ndarray
    alpha_uni_cal: float
    tau_cal: np.ndarray
    tau_cal_folds: np.ndarray
    sigma_u: float
    sigma_v: float
    native: str
    native_applicable: bool
    meta: dict = field(default_factory=dict)
    info: dict = field(default_factory=dict)

    def entry(self, n_pool):
        """(index, nominal n, realised n) of the tau table entry nearest in log2 to a test pool of n_pool candidates."""
        n_pool = int(n_pool)
        if n_pool < 1:
            raise ValueError(f"BridgeData.entry: pool size {n_pool}")
        d = np.abs(np.log2(np.asarray(self.pool_realised, dtype=np.float64)) - math.log2(n_pool))
        k = int(np.flatnonzero(d == d.min())[0])
        return k, int(self.pool_sizes[k]), int(self.pool_realised[k])

    def tau(self, n_pool, view="primary"):
        k = self.entry(n_pool)[0]
        return {"unified": float((self.tau_unified if view == "primary" else self.tau_cal)[k]), "native": float(self.tau_native[k])}

    def frozen(self, n_pool, view="primary"):
        return FrozenBridge.from_bridge(self, n_pool, view)


def _check_bridge(b):
    D1 = M.D_OUT + 1
    checks = [(b.objective in OBJECTIVES, f"objective {b.objective!r}"),
              (np.shape(b.B_uni) == (D1, C.N_TGT) and np.isfinite(b.B_uni).all(), "B_uni"),
              (np.shape(b.B_uni_cal) == (D1, C.N_TGT) and np.isfinite(b.B_uni_cal).all(), "B_uni_cal"),
              (np.shape(b.a_mu) == (C.N_TGT,) and np.shape(b.a_sd) == (C.N_TGT,) and bool((np.asarray(b.a_sd) > 0).all()), "a_mu / a_sd"),
              (b.native == ("ridge" if b.objective == "CS_SINGLE" else "cosine"), f"native readout {b.native!r}"),
              (b.objective != "CS_SINGLE" or (b.B_nat is not None and np.shape(b.B_nat) == (D1, M.D_OUT) and b.alpha_nat is not None),
               "B_nat / alpha_nat (CS_SINGLE)"),
              (b.objective == "CS_SINGLE" or b.B_nat is None, "B_nat must be absent for NCE"),
              (len(b.pool_sizes) == len(b.pool_realised) == len(b.tau_unified) == len(b.tau_native) == len(b.tau_cal) > 0, "tau tables"),
              (np.shape(b.tau_cal_folds) == (2, len(b.pool_sizes)), "tau_cal_folds"),
              (all(np.isfinite(t).all() and (np.asarray(t) > 0).all() for t in (b.tau_unified, b.tau_native, b.tau_cal)), "tau > 0"),
              (_finite_pos(b.sigma_u) is not None and _finite_pos(b.sigma_v) is not None, "sigma_u / sigma_v"),
              (all(_finite_pos(a) is not None for a in (b.alpha_uni, b.alpha_uni_cal)), "alpha")]
    bad = [w for ok, w in checks if not ok]
    if bad:
        raise ValueError(f"bridge {b.meta.get('bridge_id')}: invalid {bad}")


def save_bridge(path, bridge):
    """ckpt/<bid>_bridge.npz: the §2.11 keys (objective, B_uni, alpha_uni, a_mu, a_sd, B_nat (CS; an empty [0, 0] array for NCE),
    alpha_nat (NaN for NCE), tau_unified[n], tau_native[n], B_uni_cal, tau_cal, sigma_u, sigma_v, the row lists' sha) plus the pool
    sizes, alpha_uni_cal, tau_cal_folds, the donor checkpoint's sha256 and meta / info JSON; numeric or unicode arrays only (loads
    with allow_pickle=False). Written via a tmp file and os.replace."""
    _check_bridge(bridge)
    m = bridge.meta
    arrs = {"B_uni": np.asarray(bridge.B_uni, np.float64), "alpha_uni": np.float64(bridge.alpha_uni),
            "a_mu": np.asarray(bridge.a_mu, np.float64), "a_sd": np.asarray(bridge.a_sd, np.float64),
            "B_nat": np.zeros((0, 0)) if bridge.B_nat is None else np.asarray(bridge.B_nat, np.float64),
            "alpha_nat": np.float64(np.nan if bridge.alpha_nat is None else bridge.alpha_nat),
            "tau_pool_sizes": np.asarray(bridge.pool_sizes, np.int64), "tau_pool_realised": np.asarray(bridge.pool_realised, np.int64),
            "tau_unified": np.asarray(bridge.tau_unified, np.float64), "tau_native": np.asarray(bridge.tau_native, np.float64),
            "B_uni_cal": np.asarray(bridge.B_uni_cal, np.float64), "alpha_uni_cal": np.float64(bridge.alpha_uni_cal),
            "tau_cal": np.asarray(bridge.tau_cal, np.float64), "tau_cal_folds": np.asarray(bridge.tau_cal_folds, np.float64),
            "sigma_u": np.float64(bridge.sigma_u), "sigma_v": np.float64(bridge.sigma_v),
            "native_applicable": np.bool_(bridge.native_applicable)}
    text = {"schema": SCHEMA, "objective": bridge.objective, "native": bridge.native, **{k: str(m.get(k) or "") for k in _META_TEXT},
            "meta_json": json.dumps(jsonable(m), sort_keys=True), "info_json": json.dumps(jsonable(bridge.info), sort_keys=True)}
    arrs.update({k: np.asarray(v, dtype=np.str_) for k, v in text.items()})
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        np.savez(f, **arrs)
    os.replace(tmp, path)
    return path


def load_bridge(path, expect_id=None):
    """BridgeData from save_bridge's npz (np.load allow_pickle=False; schema, keys and shapes checked)."""
    with np.load(path, allow_pickle=False) as z:
        d = {k: z[k] for k in z.files}
    miss = sorted(set(_NPZ_ARRAYS + _NPZ_TEXT) - set(d))
    if miss or str(d.get("schema")) != SCHEMA:
        raise ValueError(f"{path}: not a {SCHEMA} bridge (schema {d.get('schema')!s}, missing {miss})")
    t = {k: str(d[k]) for k in _NPZ_TEXT}
    meta = json.loads(t["meta_json"])
    if expect_id is not None and t["bridge_id"] != expect_id:
        raise ValueError(f"{path}: bridge {t['bridge_id']!r}, expected {expect_id!r}")
    cs = t["objective"] == "CS_SINGLE"
    b = BridgeData(objective=t["objective"], B_uni=d["B_uni"], alpha_uni=float(d["alpha_uni"]), a_mu=d["a_mu"], a_sd=d["a_sd"],
                   B_nat=d["B_nat"] if cs else None, alpha_nat=float(d["alpha_nat"]) if cs else None, pool_sizes=d["tau_pool_sizes"],
                   pool_realised=d["tau_pool_realised"], tau_unified=d["tau_unified"], tau_native=d["tau_native"],
                   B_uni_cal=d["B_uni_cal"], alpha_uni_cal=float(d["alpha_uni_cal"]), tau_cal=d["tau_cal"],
                   tau_cal_folds=d["tau_cal_folds"], sigma_u=float(d["sigma_u"]), sigma_v=float(d["sigma_v"]), native=t["native"],
                   native_applicable=bool(d["native_applicable"]), meta=meta, info=json.loads(t["info_json"]))
    for k in _META_TEXT:
        if str(meta.get(k) or "") != t[k]:
            raise ValueError(f"{path}: {k} differs between the npz field and its meta")
    _check_bridge(b)
    return b


def accounting(bridge):
    """Audio-pair count and compute of a fitted bridge (inherited contract §6; PAIRS_RULE): n_pairs, n_pairs_uni_cal,
    n_pairs_all, bridge_seconds (None for a bridge without the counts, e.g. one built from parameters in a test)."""
    cnt, sec = bridge.info.get("counts") or {}, bridge.info.get("seconds") or {}
    return {"n_pairs": cnt.get("n_audio_eeg_pairs"), "n_pairs_uni_cal": cnt.get("n_audio_eeg_pairs_uni_cal"),
            "n_pairs_all": cnt.get("n_audio_eeg_pairs_all"), "bridge_seconds": sec.get("total"), "pairs_rule": PAIRS_RULE}


def record_fields(bridge):
    """The bridge record's descriptive fields (M11 interface: alpha_uni, alpha_nat, tau_cal, bridge_cal_r; the tables beside;
    the accounting n_pairs, n_pairs_uni_cal, n_pairs_all and bridge_seconds at the top level)."""
    by = lambda t: {str(int(n)): float(v) for n, v in zip(bridge.pool_sizes, t)}   # noqa: E731
    k_ref = int(np.flatnonzero(np.asarray(bridge.pool_sizes) == N_REF)[0]) if N_REF in list(bridge.pool_sizes) else 0
    bc = bridge.info.get("bridge_cal") or {}
    return jsonable({
        **accounting(bridge),
        "alpha_uni": bridge.alpha_uni, "alpha_nat": bridge.alpha_nat, "alpha_uni_cal": bridge.alpha_uni_cal,
        "tau_cal": float(bridge.tau_cal[k_ref]), "tau_cal_n_ref": int(bridge.pool_sizes[k_ref]),
        "tau_cal_by_pool_size": by(bridge.tau_cal), "tau_unified_by_pool_size": by(bridge.tau_unified),
        "tau_native_by_pool_size": by(bridge.tau_native),
        "tau_pool_sizes": [int(n) for n in bridge.pool_sizes], "tau_pool_realised": [int(n) for n in bridge.pool_realised],
        "bridge_cal_r": bc.get("r_own_unified"), "bridge_cal_corr": bc.get("corr_at_alpha"),
        "sigma_u": bridge.sigma_u, "sigma_v": bridge.sigma_v, "sigma_source": bridge.meta.get("sigma_source"),
        "native_readout": {"kind": bridge.native, "applicable": bridge.native_applicable,
                           "note": None if bridge.native_applicable else "not applicable: an NCE encoder never trained against v (§2.11)"},
        "bridge": {k: bridge.info.get(k) for k in ("method", "rows", "counts", "alpha_curve_unified", "alpha_curve_native",
                                                   "alpha_curve_uni_cal", "bridge_cal", "uni_cal", "seconds")}})


# ---------------------------------------------------------------------------------------------------------- donor rows
def artefact_rows(manifest):
    """Segment-table rows of the SparrKULee insert-phone control run (role control_artefact; §2.11, §3.2)."""
    S = V.manifest_index(manifest).seg.get("sparrkulee")
    return np.zeros(0, dtype=np.int64) if S is None else np.flatnonzero(S["role"] == "control_artefact").astype(np.int64)


def balanced_rows(rows, part_of, n, rng):
    """n of `rows`, participant-balanced: water-filling over the participants (part_of[row]) in sorted order, the remainder to
    participants drawn by rng, uniform without replacement within a participant (manifest.py's rule for bridge.cal_queries);
    every row when there are at most n. -> sorted list of ints."""
    rows = sorted({int(r) for r in rows})
    if len(rows) <= n:
        return rows
    by = {}
    for r in rows:
        by.setdefault(str(part_of[r]), []).append(r)
    ps = sorted(by)
    quota, left = {p: 0 for p in ps}, int(n)
    while left > 0:
        avail = [p for p in ps if quota[p] < len(by[p])]
        share, rem = divmod(left, len(avail))
        if share == 0:
            for i in rng.permutation(len(avail))[:rem]:
                quota[avail[int(i)]] += 1
            break
        for p in avail:
            add = min(share, len(by[p]) - quota[p])
            quota[p] += add
            left -= add
    out = []
    for p in ps:
        out += by[p] if quota[p] == len(by[p]) else [int(x) for x in rng.choice(by[p], quota[p], replace=False)]
    return sorted(out)


def uni_cal_sample(manifest, n=None):
    """B_uni_cal's fit rows (module docstring): N_UNI_CAL participant-balanced segments of pools.bridge_cal.sparrkulee (all when
    fewer), from SeedSequence([BRIDGE_SEED, UNI_CAL_TAG]); folds by bridge.cal_split. Fails closed on a row outside the bridge_cal
    role or a participant outside the split. -> {"set": sampler.SegmentSet (montage None), "fold": int64 per segment,
    "participants": {participant: segments}, "n_pool": pool segments, "split", "rows_sha256", "rule"}."""
    from . import sampler as SM          # prior33_bridge only (module docstring)
    S = V.manifest_index(manifest).seg["sparrkulee"]
    pool = [int(r) for r in manifest["pools"]["bridge_cal"]["sparrkulee"]]
    rng = np.random.default_rng(np.random.SeedSequence([C.BRIDGE_SEED, UNI_CAL_TAG]))
    rows = balanced_rows(pool, S["participant"], N_UNI_CAL if n is None else int(n), rng)
    sset = SM.segment_set(manifest, "sparrkulee", rows)              # restricted participants and shared-audio spans refused
    if not len(sset) or (sset.role != "bridge_cal").any():
        raise ValueError("uni_cal_sample: B_uni_cal rows outside the SparrKULee bridge_cal role")
    split = [[str(p) for p in f] for f in manifest["bridge"].get("cal_split", ())]
    parts = sorted(set(map(str, sset.participant)))
    if len(split) != 2 or set(split[0]) & set(split[1]) or not set(parts) <= set(split[0]) | set(split[1]):
        raise ValueError(f"uni_cal_sample: bridge.cal_split {split} must be two disjoint folds covering the bridge_cal participants {parts}")
    fold = np.asarray([0 if str(p) in set(split[0]) else 1 for p in sset.participant], dtype=np.int64)
    if not ((fold == 0).any() and (fold == 1).any()):
        raise ValueError("uni_cal_sample: both folds of bridge.cal_split need B_uni_cal rows")
    cnt = {p: int((sset.participant.astype(str) == p).sum()) for p in parts}
    return {"set": sset, "fold": fold, "participants": cnt, "n_pool": len(set(pool)), "split": split,
            "rows_sha256": sha_json({"rows": sset.rows, "fold": fold, "split": split, "rule": UNI_CAL_RULE}), "rule": UNI_CAL_RULE}


def bridge_banks(manifest, donor_set, device="cpu", root=None, artefact=True):
    """{cohort: views.DonorBank in "segments" mode}: the EEG spans of the donor set's bridge-fit rows, the bridge_cal queries, the
    B_uni_cal rows (uni_cal_sample) and (artefact=True) the control_artefact run; nothing of the target cohort (leave-target-out)."""
    from . import sampler as SM          # prior33_bridge only (module docstring)
    br = SM.bridge_rows(manifest, donor_set, root=root)
    rows = {}
    for s, sset in br["fit"].items():
        rows.setdefault(SM.coh_of(s), set()).update(int(r) for r in sset.rows)
    rows.setdefault("sparrkulee", set()).update(int(r) for r in br["cal"]["queries"].rows)
    rows["sparrkulee"].update(int(r) for r in uni_cal_sample(manifest)["set"].rows)
    if artefact:
        rows["sparrkulee"].update(int(r) for r in artefact_rows(manifest))
    idx = V.manifest_index(manifest)
    if br["target"] in rows:
        raise ValueError(f"bridge rows of target {br['target']} include its own cohort (leave-target-out, §3.1)")
    banks = {}
    for c, rr in rows.items():
        rr = sorted(rr)
        roles = tuple(r for r in V.BANK_ROLES if r in set(map(str, idx.seg[c]["role"][rr])))
        banks[c] = V.DonorBank(manifest, c, roles, device, root=root, segments=rr)
    return banks


@torch.no_grad()
def encode_segments(enc, bank, sset, *, chunk=None, montage=True):
    """U [n, 250, 32] (float32) and the envelope windows Y [n, 250, 8] of every tick of the segments of `sset` on `bank`: per-call
    layout = the bank cohort's layout; masked (piece, channel) cells and, for bridge rows with a montage subset (montage=True), the
    channels outside the subset are zeroed and closed (as the sampler does in training)."""
    from .sampler import montage_masks   # prior33_bridge only
    n, T, chunk = len(sset), C.SEG_TICKS, int(chunk or CHUNK)
    U = np.empty((n, T, M.D_OUT), dtype=np.float32)
    Y = np.empty((n, T, C.N_TGT), dtype=np.float32)
    subs = [] if sset.montage is None or not montage else list(sset.montage)
    keep = montage_masks(bank.layout) if any(mo is not None for mo in subs) else {}
    if any(mo is not None for mo in subs) and not keep:
        raise ValueError(f"encode_segments: montage subsets on the non-64-channel cohort {bank.cohort}")
    for a, b, x, y in bank.iter_ticks(sset.piece, sset.s, sset.presentation, chunk=chunk):
        m = bank.mask[np.repeat(sset.piece[a:b], T)]
        if subs:
            mm = np.stack([keep[mo] if mo is not None else np.ones(bank.n_ch, dtype=bool) for mo in subs[a:b]])
            m = m & np.repeat(mm, T, axis=0)
        Mt = torch.as_tensor(m, device=bank.device)
        u = enc(x.masked_fill(~Mt[:, :, None], 0), layout=bank.layout, mask=Mt)
        U[a:b] = u.float().reshape(b - a, T, -1).cpu().numpy()
        Y[a:b] = y.float().reshape(b - a, T, -1).cpu().numpy()
    return U, Y


@torch.no_grad()
def segment_targets(bank, pres, s):
    """Envelope windows of every tick of content segments (presentation, s) -> float32 [n, 250, 8] (audio only)."""
    pres, s = np.asarray(pres, dtype=np.int64), np.asarray(s, dtype=np.int64)
    T = C.SEG_TICKS
    y = bank.targets(np.repeat(pres, T), np.repeat(s, T), np.tile(C.TICK_OFFS.astype(np.int64), len(s)))
    return y.float().reshape(len(s), T, -1).cpu().numpy()


@torch.no_grad()
def head_v(head, Y, device, chunk=1 << 16):
    """v = head(y) for envelope windows Y [..., 8] -> float32 [..., 32]."""
    Y = np.asarray(Y, dtype=np.float32)
    flat = Y.reshape(-1, Y.shape[-1])
    out = np.empty((len(flat), M.D_OUT), dtype=np.float32)
    for a in range(0, len(flat), chunk):
        out[a:a + chunk] = head(torch.as_tensor(flat[a:a + chunk], device=device)).float().cpu().numpy()
    return out.reshape(Y.shape[:-1] + (M.D_OUT,))


def grid_edge(S, tau):
    """'lower' / 'upper' when tau is the first / last point of ev1.Readouts.calibrate's grid logspace(-3, 2, 41) x (sd(S) + 1e-12)
    (the minimum lies on the grid edge: e.g. a pool where every own candidate wins), else None."""
    r = float(tau) / (float(np.asarray(S).std()) + 1e-12)
    return "lower" if math.isclose(r, 1e-3, rel_tol=1e-9) else "upper" if math.isclose(r, 1e2, rel_tol=1e-9) else None


def _metric_rows(S, cols, rows, tau):
    Sn = _take(S, cols, rows)
    return ev1._metrics(Sn, np.zeros(len(Sn), dtype=np.int64), tau)


# ---------------------------------------------------------------------------------------------------------- fit
def fit_bridge(enc, manifest, donor_set, objective, *, slot=None, member=None, bridge_id=None, donor_group=None, sigma=None,
               device="cpu", root=None, banks=None, chunk=None, checkpoint_sha256=None):
    """Fit the source sound bridge of one slot on donor data only (module docstring) -> BridgeData.

    enc: the donor member's SharedEncoder (donor_encoder); donor_set: the target cohort of the donor group (its row's dataset;
    CSX and rich slots use the core donor set's rows); sigma: donor_bandwidths() output or None; banks: bridge_banks() output
    (built here when None); checkpoint_sha256: the sha256 of the member checkpoint file enc was loaded from (stored in the meta;
    run_zeroshot.py refuses a bridge whose checkpoint differs from the one it loads)."""
    from . import sampler as SM          # prior33_bridge only (module docstring)
    if objective not in OBJECTIVES:
        raise ValueError(f"fit_bridge: objective {objective!r} (contract objectives {OBJECTIVES})")
    t0 = time.time()
    dev = torch.device(device)
    root = V.manifest_root(manifest, root)
    br = SM.bridge_rows(manifest, donor_set, root=root)
    target, cal = br["target"], br["cal"]
    fit_cohorts = sorted({SM.coh_of(s) for s in br["fit"]})
    if target in fit_cohorts or target == "sparrkulee" or "private_bdf" in fit_cohorts:
        raise ValueError(f"fit_bridge: donor rows of target {target} break leave-target-out (cohorts {fit_cohorts}; §3.1)")
    banks = bridge_banks(manifest, donor_set, dev, root) if banks is None else banks
    head = M.fixed_heads(manifest, root)["env"].to(dev).eval()
    if bool((head.std.mu != 0).any()):
        raise ValueError("fit_bridge: the standardiser mu must be 0 (§2.3)")
    a_mu, a_sd = np.zeros(C.N_TGT), head.std.sd.detach().double().cpu().numpy()
    cs = objective == "CS_SINGLE"
    na = native_applicable(objective, slot)
    enc = enc.to(dev).eval()

    # fit rows: every tick of the manifest's bridge rows, stratum by stratum, with their montage subsets
    Us, Ys, part, pres, mont = [], [], {}, {}, {}
    for s in br["strata"]:
        sset, c = br["fit"][s], SM.coh_of(s)
        U, Y = encode_segments(enc, banks[c], sset, chunk=chunk, montage=True)
        Us.append(U.reshape(-1, M.D_OUT)); Ys.append(Y.reshape(-1, C.N_TGT))
        part.setdefault(c, set()).update(map(str, sset.participant)); pres.setdefault(c, set()).update(map(int, sset.presentation))
        for mo in sset.montage:
            mont[mo or "full"] = mont.get(mo or "full", 0) + 1
    U_fit, Y_fit = np.concatenate(Us), np.concatenate(Ys)
    del Us, Ys
    Az_fit = (Y_fit - a_mu) / a_sd
    t_fit = time.time()

    # bridge_cal queries (full montage) and candidates (audio only)
    cq, cand, own, split = cal["queries"], cal["candidates"], np.asarray(cal["own"], dtype=np.int64), cal["split"]
    Uq3, Yq3 = encode_segments(enc, banks["sparrkulee"], cq, chunk=chunk, montage=False)
    U_cal, Az_cal = Uq3.reshape(-1, M.D_OUT), (Yq3.reshape(-1, C.N_TGT) - a_mu) / a_sd
    A_c = segment_targets(banks["sparrkulee"], cand.presentation, cand.s)
    V_c = head_v(head, A_c, dev)
    n_cand, nq = len(cand), len(cq)

    B_uni, alpha_uni, curve_u = ridge_select(U_fit, Az_fit, UNI_ALPHAS, U_cal, Az_cal, "corr")
    B_nat = alpha_nat = None
    curve_n = None
    V_fit = None
    if cs:
        V_fit = head_v(head, Y_fit, dev)
        V_cal = head_v(head, Yq3, dev).reshape(-1, M.D_OUT)
        B_nat, alpha_nat, curve_n = ridge_select(U_fit, V_fit, NAT_ALPHAS, U_cal, V_cal, "mse")
    t_ridge = time.time()

    # tau(n) on the bridge_cal pools
    ro = FrozenBridge(objective, B_uni, a_mu, a_sd, alpha_uni=alpha_uni, B_nat=B_nat, alpha_nat=alpha_nat)
    S_u, S_n = ro.scores(Uq3, V_c, A_c, "unified"), ro.scores(Uq3, V_c, A_c, "native")
    draws = pool_draws(own, n_cand)
    sizes = np.asarray(POOL_SIZES, dtype=np.int64)
    realised = np.asarray([draws[int(n)].shape[1] for n in sizes], dtype=np.int64)
    tau_u, tau_n, by_n = np.empty(len(sizes)), np.empty(len(sizes)), {}
    for k, n in enumerate(sizes):
        cols = draws[int(n)]
        Su_n, Sn_n = _take(S_u, cols), _take(S_n, cols)
        t = calibrate_tau({"unified": Su_n, "native": Sn_n})
        tau_u[k], tau_n[k] = t["unified"], t["native"]
        by_n[str(int(n))] = {"realised": int(cols.shape[1]), "tau_unified": t["unified"], "tau_native": t["native"],
                             "tau_unified_grid_edge": grid_edge(Su_n, t["unified"]), "tau_native_grid_edge": grid_edge(Sn_n, t["native"]),
                             "unified": _metric_rows(S_u, cols, None, t["unified"]), "native": _metric_rows(S_n, cols, None, t["native"])}
    ix = np.arange(nq)
    bridge_cal = {"n_queries": nq, "n_candidates": n_cand, "r_own_unified": float(S_u[ix, own].mean()),
                  "r_own_native": float(S_n[ix, own].mean()), "corr_at_alpha": -float(min(c["err"] for c in curve_u)), "by_pool_size": by_n}

    # sensitivity bridge B_uni_cal: fitted on the bridge_cal rows of uni_cal_sample (alpha by the 2-fold participant split on
    # them), tau cross-fitted over the same split on the bridge_cal queries
    uc = uni_cal_sample(manifest)
    if uc["split"] != split:
        raise ValueError(f"fit_bridge: the B_uni_cal folds {uc['split']} differ from the query split {split}")
    Uu3, Yu3 = encode_segments(enc, banks["sparrkulee"], uc["set"], chunk=chunk, montage=False)
    U_uc, Az_uc = Uu3.reshape(-1, M.D_OUT), (Yu3.reshape(-1, C.N_TGT) - a_mu) / a_sd
    del Uu3, Yu3
    fold_q = np.asarray(cal["fold"], dtype=np.int64)
    fold_rows = np.repeat(uc["fold"], C.SEG_TICKS)
    B_cal, alpha_cal, B_folds, curve_c = ridge_select_2fold(U_uc, Az_uc, fold_rows, UNI_ALPHAS, "corr")
    n_uc_rows = int(len(U_uc))
    del U_uc, Az_uc
    tau_folds, by_cal, r_cross = np.empty((2, len(sizes))), {}, []
    for a in (0, 1):
        qb = np.flatnonzero(fold_q == 1 - a)
        rf = FrozenBridge(objective, B_folds[a], a_mu, a_sd, alpha_uni=alpha_cal, B_nat=B_nat, alpha_nat=alpha_nat)
        Sa = np.zeros_like(S_u)
        Sa[qb] = rf.scores(Uq3[qb], V_c, A_c, "unified")
        r_cross.append(Sa[qb, own[qb]])
        for k, n in enumerate(sizes):
            Sa_n = _take(Sa, draws[int(n)], qb)
            tau_folds[a, k] = calibrate_tau({"unified": Sa_n})["unified"]
            by_cal.setdefault(str(int(n)), {})[f"tau_fold{a}"] = float(tau_folds[a, k])
            by_cal[str(int(n))][f"tau_fold{a}_grid_edge"] = grid_edge(Sa_n, tau_folds[a, k])
            by_cal[str(int(n))][f"crossfit_fold{1 - a}_queries"] = _metric_rows(Sa, draws[int(n)], qb, tau_folds[a, k])
    tau_cal = np.sqrt(tau_folds[0] * tau_folds[1])
    for k, n in enumerate(sizes):
        by_cal[str(int(n))]["tau_cal"] = float(tau_cal[k])
    uc_rows = {"rule": uc["rule"], "segments": int(len(uc["set"])), "rows": n_uc_rows, "pool_segments": uc["n_pool"],
               "per_participant": uc["participants"], "segments_per_fold": [int((uc["fold"] == k).sum()) for k in (0, 1)],
               "overlap_with_queries": int(len(set(map(int, uc["set"].rows)) & set(map(int, cq.rows)))),
               "rows_sha256": uc["rows_sha256"]}
    uni_cal = {"alpha": alpha_cal, "fold_participants": split, "fit_rows": uc_rows,
               "n_queries_per_fold": [int((fold_q == k).sum()) for k in (0, 1)],
               "r_own_crossfit": float(np.concatenate(r_cross).mean()), "by_pool_size": by_cal,
               "use": "sensitivity only (eval_uni_cal): fitted on bridge_cal, a donor-development partition (§3.2), not on donor "
                      "fit; never a primary claim",
               "note": f"B_uni_cal is fitted on {len(uc['set'])} participant-balanced bridge_cal pool segments (the B_uni count, "
                       f"{N_UNI_CAL}; the whole pool when smaller; full montage); alpha by the 2-fold participant split of "
                       "bridge.cal_split on those rows; its tau is cross-fitted over the same split (B on fold a's rows, tau on "
                       "fold b's queries, and vice versa; geometric mean). The folds share presentations: cross-fitting over "
                       "listeners only (§2.11)."}
    t_tau = time.time()

    # kernel-dependence bandwidths: the donor's (§2.13), else the documented fallback
    sig = dict(sigma or {"sigma_u": None, "sigma_v": None, "source": {"sigma_u": None, "sigma_v": None}})
    src = dict(sig.get("source") or {})
    if cs and sig.get("sigma_u") is None:
        raise ValueError("fit_bridge: a CS_SINGLE member needs the donor's sigma_u (fixed for the run, saved in the checkpoint; §2.8)")
    if sig.get("sigma_u") is None or sig.get("sigma_v") is None:
        from .losses import calibrate_sigma   # prior33_bridge only
        sel = np.sort(np.random.default_rng(C.BRIDGE_SEED).choice(len(U_fit), size=min(SIGMA_FALLBACK_ROWS, len(U_fit)), replace=False))
        if sig.get("sigma_u") is None:
            sig["sigma_u"] = calibrate_sigma(torch.as_tensor(U_fit[sel]))
            src["sigma_u"] = f"fallback: median off-diagonal distance of the frozen encoder's U on {len(sel)} seeded bridge-fit rows"
        if sig.get("sigma_v") is None:
            vv = V_fit[sel] if V_fit is not None else head_v(head, Y_fit[sel], dev)
            sig["sigma_v"] = calibrate_sigma(torch.as_tensor(vv))
            src["sigma_v"] = f"fallback: median off-diagonal distance of the head's v on {len(sel)} seeded bridge-fit rows"

    rows_info = {"fit_rows_name": FIT_ROWS, "montage_seed": br["montage_seed"],
                 "fit_rows_sha256": sha_json({"target": target, "order": br["order"]}),
                 "cal_rows_sha256": sha_json({"queries": cq.rows, "candidates": [[int(p), int(x)] for p, x in zip(cand.presentation, cand.s)],
                                              "own": own, "split": split}),
                 "tau_draws_sha256": hashlib.sha256(b"".join(np.ascontiguousarray(draws[int(n)]).tobytes() for n in sizes)).hexdigest(),
                 "uni_cal_rows_sha256": uc["rows_sha256"], "uni_cal_rows_rule": uc["rule"]}
    meta = {"bridge_id": bridge_id, "donor_group": donor_group, "slot": slot, "member": member, "target": target,
            "manifest_sha256": V.manifest_sha(manifest), "target_contract": manifest.get("target_contract"),
            "checkpoint_sha256": checkpoint_sha256,
            "fit_rows_sha256": rows_info["fit_rows_sha256"], "cal_rows_sha256": rows_info["cal_rows_sha256"],
            "uni_cal_rows_sha256": rows_info["uni_cal_rows_sha256"],
            "tau_draws_sha256": rows_info["tau_draws_sha256"], "strata": list(br["strata"]), "fit_cohorts": fit_cohorts,
            "fit_participants": {c: sorted(v) for c, v in part.items()},
            "cal_participants": sorted(set(map(str, cq.participant))),
            "uni_cal_participants": sorted(uc["participants"]), "sigma_source": src}
    n_cal_union = len(set(map(int, cq.rows)) | set(map(int, uc["set"].rows)))
    info = {"method": {**SPEC_RULES, "standardised_target": "y / sigma (manifest standardiser, mu = 0)", "unified_alphas": UNI_ALPHAS,
                       "native_alphas": NAT_ALPHAS if cs else None, "tau_grid": TAU_GRID, "pool_sizes": sizes,
                       "tau_pool_seed": C.TAU_POOL_SEED, "native_readout": "ridge U -> v" if cs else "cosine u . v (no fit)",
                       "native_applicable": na, "a_mu": a_mu, "a_sd": a_sd},
            "rows": rows_info,
            "counts": {"strata": list(br["strata"]), "fit_segments": {s: len(br["fit"][s]) for s in br["strata"]},
                       "fit_rows": int(len(U_fit)), "fit_participants": {c: len(v) for c, v in part.items()},
                       "fit_presentations": {c: len(v) for c, v in pres.items()}, "montage": mont, "cal_queries": nq,
                       "cal_rows": int(len(U_cal)), "cal_candidates": n_cand, "uni_cal_segments": int(len(uc["set"])),
                       "uni_cal_rows": n_uc_rows, "uni_cal_pool_segments": uc["n_pool"],
                       "n_audio_eeg_pairs": int(len(U_fit) + len(U_cal)), "n_audio_eeg_pairs_uni_cal": n_uc_rows,
                       "n_audio_eeg_pairs_all": int(len(U_fit) + n_cal_union * C.SEG_TICKS), "pairs_rule": PAIRS_RULE,
                       "banks": {c: b.describe() for c, b in banks.items()}},
            "alpha_curve_unified": [{"alpha": c["alpha"], "bridge_cal_corr": -c["err"]} for c in curve_u],
            "alpha_curve_native": None if curve_n is None else [{"alpha": c["alpha"], "bridge_cal_mse": c["err"]} for c in curve_n],
            "alpha_curve_uni_cal": [{"alpha": c["alpha"], "corr_fold0_to_fold1": -c["err_fold0_to_fold1"],
                                     "corr_fold1_to_fold0": -c["err_fold1_to_fold0"], "corr_mean": -c["err"]} for c in curve_c],
            "bridge_cal": bridge_cal, "uni_cal": uni_cal, "sigma": {k: sig[k] for k in ("sigma_u", "sigma_v")},
            "seconds": {"fit_rows": round(t_fit - t0, 2), "ridge": round(t_ridge - t_fit, 2), "tau_and_uni_cal": round(t_tau - t_ridge, 2),
                        "total": round(time.time() - t0, 2), "device": str(dev),
                        "note": "wall-clock seconds of fit_bridge (encoder passes, ridges, temperatures); the artefact probe is "
                                "descriptive and timed by the unit record's total_seconds only"}}
    b = BridgeData(objective=objective, B_uni=B_uni, alpha_uni=alpha_uni, a_mu=a_mu, a_sd=a_sd, B_nat=B_nat, alpha_nat=alpha_nat,
                   pool_sizes=sizes, pool_realised=realised, tau_unified=tau_u, tau_native=tau_n, B_uni_cal=B_cal,
                   alpha_uni_cal=alpha_cal, tau_cal=tau_cal, tau_cal_folds=tau_folds, sigma_u=float(sig["sigma_u"]),
                   sigma_v=float(sig["sigma_v"]), native="ridge" if cs else "cosine", native_applicable=na, meta=jsonable(meta),
                   info=jsonable(info))
    _check_bridge(b)
    return b


# ---------------------------------------------------------------------------------------------------------- artefact probe
@torch.no_grad()
def artefact_probe(enc, bridge, manifest, *, device="cpu", root=None, banks=None, chunk=None):
    """The frozen B_uni on the insert-phone control run (role control_artefact; §2.11): r_own = mean over its segments of the
    unified score against its own envelope; r_other = mean over its segments of the mean score against the other content segments
    of its family >= OTHER_MIN_SEP family-clock samples away. Descriptive; never used for any selection."""
    from . import sampler as SM          # prior33_bridge only
    rows = artefact_rows(manifest)
    base = {"readout": "B_uni (frozen)", "role": "control_artefact", "use": "descriptive (risk 3); never used for any selection",
            "min_separation_samples": OTHER_MIN_SEP}
    if not len(rows):
        return {**base, "status": "absent", "n_segments": 0}
    dev = torch.device(device)
    idx = V.manifest_index(manifest)
    S = idx.seg["sparrkulee"]
    sset = SM.segment_set(manifest, "sparrkulee", rows)
    bank = (banks or {}).get("sparrkulee")
    if bank is None or not bank.loaded(sset.piece).all():
        bank = V.DonorBank(manifest, "sparrkulee", ("control_artefact",), dev, root=root, segments=rows)
    U, Y = encode_segments(enc.to(dev).eval(), bank, sset, chunk=chunk, montage=False)
    pres = sorted(set(int(p) for p in sset.presentation))
    fams = sorted({int(idx.fam[p]) for p in pres})
    out = {**base, "n_segments": int(len(sset)), "presentations": [man_p["stimulus"] for man_p in manifest["presentations"] if
                                                                       int(man_p["id"]) in pres],
           "participants": sorted(set(map(str, sset.participant))), "families": fams}
    ro = FrozenBridge(bridge.objective, bridge.B_uni, bridge.a_mu, bridge.a_sd, alpha_uni=bridge.alpha_uni, B_nat=bridge.B_nat,
                      alpha_nat=bridge.alpha_nat)
    r_own = np.array([ro.scores(U[i:i + 1], None, Y[i:i + 1], "unified")[0, 0] for i in range(len(sset))])
    out.update(r_own=float(r_own.mean()), r_own_per_segment=r_own)
    if any(bool(idx.unknown_clock[p]) for p in pres):
        return jsonable({**out, "status": "computed_own_only", "reason": "the artefact presentation's family clock is unknown"})
    fam_rows = np.flatnonzero(np.isin(idx.fam[S["presentation"]], fams))
    ok = idx.famoff[S["presentation"][fam_rows]] >= 0
    cand = sorted({(int(S["presentation"][r]), int(S["s"][r])) for r in fam_rows[ok]})
    if not cand:
        return jsonable({**out, "status": "computed_own_only", "reason": "no other segment of the family"})
    cp, cs_ = np.array([p for p, _ in cand], dtype=np.int64), np.array([s for _, s in cand], dtype=np.int64)
    cf0 = idx.fs0(cp, cs_)
    qf0 = np.asarray(sset.fs0, dtype=np.int64)
    A_c = segment_targets(bank, cp, cs_)
    Sc = ro.scores(U, None, A_c, "unified")                      # [n_art, n_cand]
    other = np.abs(cf0[None, :] - qf0[:, None]) >= OTHER_MIN_SEP
    used = other.any(1)
    per = np.array([Sc[i, other[i]].mean() if other[i].any() else np.nan for i in range(len(sset))])
    vals = Sc[other]
    out.update(status="computed", r_other=float(np.nanmean(per)) if used.any() else None,
               r_other_sd=float(vals.std()) if vals.size else None, n_other_candidates=int(other.any(0).sum()),
               n_other_pairs=int(other.sum()), n_segments_with_other=int(used.sum()), r_other_per_segment=per)
    if out["r_other"] is not None:
        out["r_own_minus_other"] = float(np.mean(r_own[used] - per[used]))
    return jsonable(out)


def bridge_row_info(bridge):
    """Summary of a loaded bridge for a downstream record (zero-shot dependency), with its accounting (n_pairs, n_pairs_uni_cal,
    n_pairs_all, bridge_seconds; inherited contract §6) and the checkpoint it was fitted on."""
    m = bridge.meta
    return jsonable({"bridge_id": m.get("bridge_id"), "donor_group": m.get("donor_group"), "slot": m.get("slot"),
                     "member": m.get("member"), "objective": bridge.objective, "alpha_uni": bridge.alpha_uni,
                     "alpha_uni_cal": bridge.alpha_uni_cal, "native": bridge.native, "native_applicable": bridge.native_applicable,
                     "tau_pool_sizes": bridge.pool_sizes, "tau_pool_realised": bridge.pool_realised, "sigma_u": bridge.sigma_u,
                     "sigma_v": bridge.sigma_v, "checkpoint_sha256": m.get("checkpoint_sha256"), "fit_rows_sha256": m.get("fit_rows_sha256"),
                     "cal_rows_sha256": m.get("cal_rows_sha256"), "uni_cal_rows_sha256": m.get("uni_cal_rows_sha256"),
                     **accounting(bridge)})
