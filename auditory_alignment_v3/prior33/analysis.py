"""ALN3.4 card E34_PUBLIC_PRIOR, module M11: the frozen analysis of the ALN3.3 public auditory prior
(logical family ALN32_PUBLIC_AUDIO_PRIOR, execution contract aln33_env64_125ms_v1).

Specification: private/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN.md §5 (the analysis, frozen with the execution record),
§4.3 (ids and spec fields), §2.10-§2.13 (record schemas), §6.6 M11 and the Revision log (F5 pool equality, F6 frozen analysis /
seed fields / panel, F7 the two selection rules). Not part of any training code hash. Reads plan rows and unit records only:
CPU, numpy, no torch.

  load_records(rows, units_dir)  every plan row of the six ALN32_PUBLIC_AUDIO_PRIOR_* families, plus the E_LOCAL
                                 lag_local_tokens full rows (the PANEL's different-input-contract reference) -> one normalised
                                 unit per row (missing and technical_failed units kept with their status), carrying its
                                 execution version, selection level and member check
  identity_values(units, ...)    configuration x identity values: the mean over that identity's usable units (content folds,
                                 outer folds; Federici records -> subject_uid via reaggregate/entity_manifest.csv, HC / CI / HC-v
                                 independent, the phantom excluded and counted; the FAU always-train TH half is never tested)
  run_families(units, ...)       the §5.4 analysis -> aggregate JSON, Markdown tables, per-identity tables (0600, 0700 dir)

Freeze gate (§5.1). The live units directory is read only when frozen_check passes: the sha256 of every code file the analysis
depends on (CODE_FILES: analysis.py, its tests, prior33/select.py, prior33/contract.py, sci_r1/stats.py,
auditory_alignment/aggregate.py) and the manifest sha256 of every E34 plan row are listed in E34_PUBLIC_PRIOR_EXECUTION_RECORD.md
(the full hash, or a prefix of at least 16 hex digits). load_records and main both apply it. `--allow-unfrozen` is a dry run on
scratch inputs: it needs explicit --plan and --units that are not the live plan files or inside the live units directory,
refuses plan rows that have a record in the live units directory (existence check; nothing is opened), and writes nothing under
docs/, results/ or private/auditory_alignment_v3/ (os.path.commonpath on resolved paths).

Execution versions (§2.10). Derived from the donor-group rows, never from a downstream row's own fields: a DONOR (core / panel)
group is 'primary', or 'continuation_k' when it is the k-th link of a spec.continuation_of chain; a RICH_DONOR / CSX_DONOR group
takes the version of the core group named by its spec.horizon_from (whose H* it adopts; deps.py requires the field), and a
disagreement with its own continuation chain is noted. Bridge, target and zero-shot rows take the version of their
spec.donor_group; S rows are always 'primary' (a continuation never re-registers them), so INIT at a continuation version
pairs the continuation arms with the primary S rows, the only cross-version pair. spec.version / spec.execution_version and a
downstream row's spec.continuation_of are labels: listed per version, never keys. Every version is analysed and rendered.

Statistics (§5.5). auditory_alignment_v3.sci_r1.stats, imported unchanged: bootstrap-t with per-replicate studentisation,
B = 4,000, percentile intervals as the secondary column. Pointwise intervals are on each member's own paired identities.
Simultaneous 95 % intervals: max-t over the members of a declared family that have pairs, on the identities common to them
(the family set: its n, the members in the max-t and the declared count are reported), sharing replicate b of the identity
resampling, seeded by group_seed(family label, endpoint). Own-identity summaries use the same seed, so a member whose own
identities are the family set has identical pointwise intervals in both views. The identity is the resampling unit: seeds,
folds, content folds, cells and repeated zero-shot evaluations never add to n. One donor member model serves every cell of its
target, so those cells are not independent samples; every interval conditions on the fitted donors and targets
(bootstrap_scope conditional_on_available_fitted_models_not_full_training_population). No p-values; no per-identity
best-method baseline.

Contrasts. Within-identity paired differences on matched cells, positive = the candidate is better: for risks (log-losses,
NLL, rank percentile) Δ = R(reference) − R(candidate); for AUC, accuracies, top-1, gains and kernel_cs_diff Δ = candidate −
reference (DIRECTION; printed with every endpoint). Cell pairs are matched on dataset, subject_fold, content_fold, split_hash,
spec.target, spec.target_contract (the §4.3 sha of standardiser, P and filters), the record's target_contract (a separate
key), input-access mode, evaluation version (code hash), manifest, execution version and seed (donor_seed and target_seed
separately); only the family's declared independent variable may differ, and a mismatched cell pair is excluded with its
reason. A side is 'missing' when its plan row has no complete record (or lacks the evaluation), 'unregistered' when no plan
row exists; both are listed separately, identities enter on their remaining units with the counts, nothing is zero-filled.

Engineering checks (§2.13, §5.8). Pools: in every cell the complete mode-T units are the reference and must agree with each
other; a zero-shot unit whose participant set, candidate / query counts or n_test_candidates differ from them, or whose cell's
mode-T units disagree, is excluded with the reason from every family and summary; a cell without a complete mode-T unit leaves
its zero-shot units unverified (listed). Members: the member_resolved a downstream unit records must equal select.member_of(row,
donor-group record) (J* by the lambda rule; other slots their own tag); a disagreeing unit, or a J* unit whose group record
cannot resolve J*, is excluded the same way. Selection levels (§1 item 8, §2.10, §2.12): counted per configuration and checked
against the stage's declared level (SELECTION_LEVEL); levels are never pooled (modes are separate configurations, mode T is
never contrasted with zero-shot, the primary / gain-selected / B_uni_cal evaluations are separate views).

Record interface (records written through core.new_record / core.write_record by run_donor, run_bridge, run_target and
run_zeroshot; slot semantics and the pinned donor-group record are prior33.select's, the zero-shot mode names prior33.contract's):
  row       family_id, dataset, subject_fold, content_fold, seed; spec: stage, member (else a slot-name variant), init, mode
            (zero-shot: A | B | C | C_partial, or the full §2.13 name), block, seed_scope, donor_seed, target_seed, split_hash,
            manifest_sha256, target, target_contract, donor_group, bridge, objective; donor groups: members, continuation_of,
            horizon_from, budget.continuation [, version | execution_version | continuation_of on any row: labels only]
  record    status; code_hash (or eval_version); target_contract (the runner's value); selection_level; member_resolved
            (optional; J* -> J1 / J025); eval = the ev1 / ev2 evaluation (per_participant, readout.n_test_candidates; private:
            native_calibration.per_participant[child].positive_affine {nll_bits, auc_score} from calib.private_variants)
  target    eval_gainsel (the gain-selected checkpoint, same structure as eval), or gainsel = "identical" (same epoch)
  zero-shot eval_uni_cal (the B_uni_cal sensitivity bridge, same structure as eval)
  donor     members[M][kind][field], kind best | h30 | gainsel, field ce_dev | gain | bridge_cal_ce | ep_eq (select pins
            members[M].best.ce_dev; flat members[M].<kind>_<field> accepted), members[M].steps / nonfinite_steps,
            joint_choice {rule, member} (select.joint_choice) and the gain-rule choice (gain_rule {member} or a member tag),
            horizon_ep_eq, ceiling_reached_while_improving. Descriptive: the lambda rule is recomputed with select
  bridge    alpha_uni, alpha_nat, tau_cal, bridge_cal_r and artefact_probe scalars. Descriptive
  Every scalar of a donor-group / bridge record whose key path names a selection quantity is also copied to the JSON.

Usage: python -m auditory_alignment_v3.prior33.analysis   (the frozen run: one CPU Slurm job)
       python -m auditory_alignment_v3.prior33.analysis --allow-unfrozen --plan P.jsonl --units DIR --res DIR --docs DIR
              --priv DIR   (dry run on scratch inputs)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import time
from collections import Counter, defaultdict

import numpy as np

import auditory_alignment.aggregate as AGG  # unit_rows: the ALN3 per-participant endpoint flattening, unchanged
from auditory_alignment_v3.prior33 import contract as C
from auditory_alignment_v3.prior33 import select as SEL
from auditory_alignment_v3.sci_r1 import stats as S  # identity bootstrap-t / max-t machinery, unchanged

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(REPO, "private", "auditory_alignment_v3")
UNITS = os.path.join(OUT, "units")
PLAN = os.path.join(REPO, "AUDITORY_ALN3_SERVER_PACKAGE_v3_20261010", "plans", "units.jsonl")
PLAN_EXT = os.path.join(OUT, "plan_ext.jsonl")
ENTITY_MANIFEST = os.path.join(OUT, "reaggregate", "entity_manifest.csv")
EXEC_RECORD = os.path.join(OUT, "aln34", "E34_PUBLIC_PRIOR_EXECUTION_RECORD.md")
RES = os.path.join(REPO, "results", "auditory_alignment_v3", "public_prior")
DOCS = os.path.join(REPO, "docs", "auditory_alignment_v3")
PRIV = os.path.join(OUT, "prior33", "agg")
TESTS = os.path.join(REPO, "tests", "auditory_alignment_v3", "prior33", "test_analysis.py")
JSON_NAME, MD_NAME, PRIV_NAME = "public_prior.json", "PUBLIC_PRIOR_RESULTS.md", "per_identity.json"
DESIGN = "private/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN.md §5"
CARD, LOGICAL_FAMILY = "E34_PUBLIC_PRIOR", "ALN32_PUBLIC_AUDIO_PRIOR"

# ------------------------------------------------------------------------------------------------ frozen design constants
EVAL_STAGES = ("target", "zero_shot", "reference")
SLOT_STAGES = ("bridge", "target", "zero_shot")
PUBLIC = tuple(C.ZS_COHORTS["A"])                      # fau, dtu, federici
PRIVATE = "private_bdf"
COHORTS = PUBLIC + (PRIVATE,)
OBJECTIVES = ("NCE", "CS_SINGLE")
BREADTH_SEED, PANEL_SEEDS = 3401, (3407, 3413)
ALL_SEEDS = (BREADTH_SEED,) + PANEL_SEEDS
PRIMARY_VERSION, NATIVE_VERSION = "primary", "aln3_native"
ZS_MODES = tuple(C.ZS_SUFFIX)                          # A (primary), B, C, C_partial
ACCESS = {c: tuple(m for m in ZS_MODES if m != "A" and c in C.ZS_COHORTS[m]) for c in PUBLIC}  # fau B, C; dtu C; federici C_partial
ACCESS_SLOTS = ("AP", "XP", SEL.JOINT)
REFERENCE_SLOT = "E_LOCAL"                             # private local native: E_LOCAL lag_local_tokens full (ALN3 contract)
NATIVE_NA_SLOTS = ("XP", "XM", "XPC")                  # NCE encoders never trained against v: native readout n/a in zero-shot (§2.11)
FAMILIES = (  # name, {mode: cohorts}, members (reference slot, candidate slot), declared independent variable, allowed field differences
    ("INIT", {"T": COHORTS}, (("S", "AP"), ("S", "XP"), ("S", "J*"), ("S", "XM")),
     "initialisation: donor pretraining with this supervision vs scratch at the same target budget (S → XM: donor-EEG exposure "
     "without stimulus-locked pairing)", ("donor_seed",)),
    ("SUPERVISION", {"T": COHORTS, "A": PUBLIC}, (("AP", "XP"), ("AP", "J*"), ("XP", "J*")),
     "donor supervision type; AP → J* and XP → J* are OBJECTIVES §4's two separate paired differences", ()),
    ("CONTROL", {"T": COHORTS, "A": PUBLIC}, (("XM", "AP"), ("XM", "XP"), ("XM", "J*")),
     "stimulus-locked supervision vs exposure-matched mismatched-partner pretraining on the same donor EEG", ()),
    ("RICH", {"T": COHORTS, "A": PUBLIC}, (("AP", "APR"),),
     "spectral targets added to audio pairing (rich block), identical batches and equal updates", ()),
    ("CSX", {"T": ("dtu", "federici", PRIVATE), "A": ("dtu", "federici")}, (("AP", "APC"), ("XP", "XPC")),
     "competing-talker anchors added to the donor pool (CSX block)", ()),
)
FAMILY_MEMBERS = {f[0]: f[2] for f in FAMILIES}
FAMILY_BLOCK = {"INIT": "core", "SUPERVISION": "core", "CONTROL": "core", "RICH": "rich", "CSX": "csx"}
PANEL_FAMILIES = ("INIT", "SUPERVISION", "CONTROL")
PANEL_SLOTS = ("S", "AP", "XP", SEL.JOINT, "XM")
REF_ALLOW = ("split_hash", "target_hash", "record_target_contract", "eval_version", "manifest_sha256", "donor_seed", "version")
PAIR_FIELDS = (  # (unit field, label, show the two values in the reason)
    ("split_hash", "split_hash", False), ("target", "spec target", True), ("target_hash", "spec target_contract", True),
    ("record_target_contract", "record target_contract", True), ("eval_version", "evaluation version", True),
    ("manifest_sha256", "manifest sha256", True))

PRIMARY = "unified/regular/logloss_bits"
CONT_SECONDARY = ("unified/gain_bits", "unified/mismatched_eeg/logloss_bits", "unified/regular/top1", "unified/regular/rank_pct",
                  "unified/hard_gain_bits", "native/regular/logloss_bits")
ATTENTION, KCS = "attention/unified/accuracy", "kernel_cs_diff"
PRIV_PRIMARY, PRIV_SECONDARY = ("NLL", "AUC"), ("hist_gain", "twin_sens")
# risks ("lower": Δ = reference − candidate) and higher-is-better endpoints ("higher": Δ = candidate − reference); §5.4
DIRECTION = {PRIMARY: "lower", "unified/gain_bits": "higher", "unified/mismatched_eeg/logloss_bits": "lower",
             "unified/regular/top1": "higher", "unified/regular/rank_pct": "lower", "unified/hard_gain_bits": "higher",
             "native/regular/logloss_bits": "lower", ATTENTION: "higher", KCS: "higher",
             "NLL": "lower", "AUC": "higher", "hist_gain": "higher", "twin_sens": "higher"}
DIR_TEXT = {"lower": "ref − cand", "higher": "cand − ref"}
LABEL = {PRIMARY: "R", "unified/gain_bits": "gain", "unified/mismatched_eeg/logloss_bits": "R_mm", "unified/regular/top1": "top1",
         "unified/regular/rank_pct": "rank_pct", "unified/hard_gain_bits": "hard_gain", "native/regular/logloss_bits": "R_native",
         ATTENTION: "att_acc", KCS: "kernel_cs_diff", "NLL": "NLL", "AUC": "AUC", "hist_gain": "hist_gain", "twin_sens": "twin_sens"}
SELECTION_LEVEL = {  # the level each stage declares (§1 item 8, §2.10, §2.12; zero-shot units use the donor-dev selection) and
    # the phrase a record's selection_level must contain to count as that level
    "donor_group": ("donor dev: SparrKULee participants and content families disjoint from donor fit (new listeners, new "
                    "content)", r"donor[ -]dev"),
    "target": ("training identities, held-out early-stopping content (not new listeners)", r"early[ -]stopping"),
    "target_private": ("training children, last 20 % of each child's physical blocks", r"last 20"),
    "zero_shot": ("donor dev (the donor checkpoint and the joint λ are chosen on donor dev; no target-side selection)",
                  r"donor[ -]dev"),
}
DESIGN_ROWS = {  # §4.1 rows of the primary version per (block, stage); access is a maximum (mode-C rows only where supported)
    ("core", "donor_group"): 8, ("core", "bridge"): 32, ("core", "target"): 300, ("core", "zero_shot"): 200,
    ("access", "zero_shot"): 210, ("panel", "donor_group"): 4, ("panel", "bridge"): 16, ("panel", "target"): 100,
    ("rich", "donor_group"): 8, ("rich", "bridge"): 8, ("rich", "zero_shot"): 50, ("rich", "target"): 60,
    ("csx", "donor_group"): 6, ("csx", "bridge"): 12, ("csx", "zero_shot"): 60, ("csx", "target"): 80}
DESIGN_ROWS_MAX = frozenset({("access", "zero_shot")})
MEMBER_EXCLUDE = ("disagrees", "unverifiable")
FAU_ALWAYS_TRAIN_TH = frozenset("301 302 304 311 314 315 317 319 321 322 325 327 330 331".split())  # never tested (§3.3)
EXPECTED_IDENTITIES = {"fau": {"TH": 14, "HA": 29, "CI": 24}, "dtu": {"NH": 22, "HI": 22},
                       "federici": {"HC": 37, "CI": 33, "HC-v": 16}, PRIVATE: {"HA": 55, "NH": 9}}  # §5.2
MIN_N = 5
BOOTSTRAP_SCOPE = "conditional_on_available_fitted_models_not_full_training_population"
GAINSEL_KEYS = ("eval_gainsel", "gainsel_eval")
UNI_CAL_KEYS = ("eval_uni_cal", "eval_b_uni_cal", "eval_cal")
RESOLVED_KEYS = ("member_resolved", "resolved_member", "slot_member")
MODE_ALIASES = {"a": "A", "b": "B", "c": "C", "c_partial": "C_partial", "c-partial": "C_partial", "cpartial": "C_partial"}
DONOR_KEYS = re.compile(r"ce_dev|gain|best|h30|lambda|joint|j_star|jstar|horizon|ep_eq|ceiling|trigger|nonfinite|tau|bridge_cal", re.I)
BRIDGE_KEYS = re.compile(r"bridge_cal|alpha|tau|r_bar|rbar|artefact|artifact|n_pairs|corr|bridge_seconds", re.I)
SKIP_KEYS = frozenset({"row", "bound_row", "spec", "curve", "curves", "log", "eval"})
CKPT_KINDS = {"best": ("best",), "h30": ("h30", "h30_best"), "gainsel": ("gainsel", "gainsel_best")}
CKPT_FIELDS = {"ce_dev": ("ce_dev", "ce_dev_bits"), "gain": ("gain", "gain_dev"),
               "bridge_cal_ce": ("bridge_cal_ce", "ce_bridge_cal", "bridge_cal_ce_bits", "bridge_cal"),
               "ep_eq": ("ep_eq", "position_ep_eq", "best_ep_eq")}
GAIN_RULE_KEYS = ("gain_rule", "joint_choice_gain", "joint_choice_sensitivity", "lambda_choice_gain")
HORIZON_KEYS = ("horizon_ep_eq", "h_star_ep_eq", "H_star", "h_star", "horizon", "ep_eq_used")
BRIDGE_FIELDS = {"alpha_uni": ("alpha_uni",), "alpha_nat": ("alpha_nat",), "tau_cal": ("tau_cal",),
                 "bridge_seconds": ("bridge_seconds",), "n_pairs": ("n_pairs",),
                 "bridge_cal_r": ("bridge_cal_r", "bridge_cal_corr", "r_bridge_cal", "bridge_cal_r_bar")}
LAMBDA_TAGS = {1.0: "J1", 0.25: "J025"}
LIMIT = re.compile(r"limit(\d+)")
HEX = re.compile(r"(?<![0-9a-f])[0-9a-f]{16,64}(?![0-9a-f])")
CHILD_PATTERN = re.compile(r"\bchild\d+\b")
STATEMENTS = (
    "Every contrast is a within-identity paired difference on matched cells, written so that positive = the candidate is "
    "better: for risks (log-losses, NLL, rank percentile) Δ = R(reference) − R(candidate); for AUC, accuracies, top-1, gains "
    "and kernel_cs_diff Δ = candidate − reference. Each endpoint carries its direction (ref − cand or cand − ref).",
    "R = `unified/regular/logloss_bits`, the candidate cross-entropy (bits per 5-s query) of the true test segment among all test "
    "candidates under the unified readout (mode T: training-side ridge and temperature; zero-shot: the frozen donor bridge and "
    "τ(n)). Private task: positive-affine calibrated natural-distribution NLL (bits, primary) and AUC (co-primary).",
    "Each test identity counts once: seeds, folds, content folds, cells and repeated zero-shot evaluations never add to n. One "
    "donor member model serves every cell of its target; it is a fixed upstream, so its cells are not independent samples, and "
    "every interval conditions on the fitted donors and targets (bootstrap_scope: " + BOOTSTRAP_SCOPE + ").",
    "Intervals: bootstrap-t over identities (B = 4,000; sci_r1.stats unchanged), percentile intervals as the secondary column. "
    "Pointwise intervals (n) are on each member's own paired identities. Families (cohort × objective × mode × seed × version) "
    "carry simultaneous 95 % intervals by max-t over the members that have pairs, sharing the replicate indices, on the "
    "identities common to them (family n, printed with the members in the max-t); secondary endpoints, the B_uni_cal "
    "sensitivity, ACCESS, SELECTION, levels and the native reference are pointwise.",
    "An identity bootstrap does not contain the training randomness, and 3 seeds do not estimate the seed distribution precisely.",
    "Tables outside the panel are seed 3401 only. Donor and target seeds are recorded separately (d = donor_seed, t = target_seed; "
    "S has no donor, zero-shot rows have no target seed).",
    "Zero-shot access modes A (primary), B, C and C-partial are separate configurations and are never pooled; mode T and zero-shot "
    "values are never contrasted with each other. Selection levels are declared per configuration: mode T = training "
    "identities with held-out early-stopping content (not new listeners); private = training children, last 20 % of blocks; "
    "zero-shot = the donor-dev selection (new listeners, new content).",
    "Execution versions are derived from the donor-group rows: `primary`, or `continuation_k` for a registered continuation "
    "(§2.10), reported as its own version; S rows are never re-registered, so INIT at a continuation version uses the primary S "
    "rows.",
    "Missing units (a plan row without a complete record) and unregistered sides (no plan row) are listed separately, with their "
    "status, and identities enter on their remaining units; nothing is zero-filled. A mismatched cell pair, and a unit failing "
    "the pool or member check, is excluded with its reason.",
    "No p-values are computed or reported, and there is no per-identity best-method baseline. Effects are shown with their size "
    "and scope; cells are not counted by interval sign.",
)
ESTIMANDS = (
    ("INIT", "Donor pretraining with this supervision vs scratch, at the same target budget; S → XM is donor-EEG exposure without "
             "stimulus-locked pairing. INIT > 0 shows that the pretrained initialisation lowers risk at this budget; it does not by "
             "itself separate transferable sound structure from easier optimisation (S → XM and CONTROL separate the two partly)."),
    ("SUPERVISION", "AP → J* and XP → J* are the two separate paired differences of OBJECTIVES §4; AP → XP compares the supervision "
                    "types. No max over arms, no per-identity best method. 'Both supervisions contribute' needs both AP → J* and "
                    "XP → J* above 0 at the λ chosen on donor dev; a gain at one λ or in one mode only is reported with that scope."),
    ("CONTROL", "Stimulus-locked supervision vs exposure-matched mismatched pretraining on the same donor EEG. Without CONTROL > 0, a "
                "gain of that arm over scratch is reported as possibly an exposure or optimisation effect."),
    ("RICH / CSX", "Data-and-target additions at equal updates; gains that appear only with more data or more targets are reported "
                   "as such, not as a loss-function advantage."),
    ("ACCESS", "Dependence of zero-shot values on the stimulus-informed ICA and on target statistics (descriptive), not a method "
               "comparison. Mode-A values carry the declared target-side preprocessing access; FAU CI values in modes B and C are "
               "not interpretable as neural tracking (§2.13)."),
    ("SELECTION", "Sensitivity of the checkpoint-selection rule (risk-selected → gain-selected), and the donor-side selection "
                  "quantities as recorded (descriptive)."),
    ("PANEL", "The established private_transfer role at seeds 3401, 3407 and 3413. E_LOCAL lag_local_tokens full (250 Hz native, "
              "0.5–45 Hz, ALN3 recipe) is a different-input-contract reference, descriptive, not an initialisation contrast."),
    ("All", "These statements describe estimands; they are not a list of permitted sentences, and interpretation may change "
            "with new evidence (design §5.6)."),
)


# ------------------------------------------------------------------------------------------------ small helpers
def _num(x):
    """float of a JSON number (NaN / inf kept, to be excluded upstream with a reason); None for anything else."""
    if isinstance(x, (bool, np.bool_)) or not isinstance(x, (int, float, np.integer, np.floating)):
        return None
    return float(x)


def _diff(ref, cand, direction):
    return ref - cand if direction == "lower" else cand - ref


def _position(lo, hi):
    return "above 0" if lo > 0 else ("below 0" if hi < 0 else "contains 0")


def _s(x):
    return "-" if x is None else str(x)


def ckey(c):
    cohort, obj, mode, slot, d, t, version = c
    return f"{cohort}|{obj}|{mode}|{slot}|d{_s(d)}|t{_s(t)}|{version}"


def cfg(cohort, objective, mode, slot, seed, version=PRIMARY_VERSION):
    """Configuration key (cohort, objective, mode, slot, donor_seed, target_seed, version): donor and target seeds are
    separate fields; S has no donor seed, zero-shot rows have no target seed."""
    if slot == REFERENCE_SLOT:
        return (cohort, objective, "T", slot, None, seed, NATIVE_VERSION)
    if mode == "T":
        return (cohort, objective, "T", slot, None if slot == SEL.SCRATCH else seed, seed, version)
    return (cohort, objective, mode, slot, seed, None, version)


def config_of(u):
    return (u["cohort"], u["objective"], u["mode"], u["slot"], u["donor_seed"], u["target_seed"], u["version"])


def cell_of(u):
    return (u["subject_fold"], u["content_fold"])


def _cellsort(c):
    return tuple(-1 if x is None else x for x in c)


def _group(cohort, g):
    if g is None:
        return None
    g = str(g)
    return g if cohort == "federici" else g.upper()


def primaries(cohort):
    return PRIV_PRIMARY if cohort == PRIVATE else (PRIMARY,)


def secondaries(cohort, objective):
    if cohort == PRIVATE:
        return PRIV_SECONDARY
    out = CONT_SECONDARY + ((ATTENTION,) if cohort in ("fau", "dtu") else ())
    return out + ((KCS,) if objective == "CS_SINGLE" else ())


def _vsuffix(version):
    return "" if version == PRIMARY_VERSION else f"|{version}"


def family_label(fam, cohort, objective, mode, seed, version=PRIMARY_VERSION):
    return f"{fam}|{cohort}|{objective}|{mode}|s{seed}" + _vsuffix(version)


def _seed_label(seed):
    return "seed 3401 only" if seed == BREADTH_SEED else f"panel seed {seed}"


def canon_mode(m):
    if m is None:
        raise ValueError("zero-shot row without spec.mode")
    s = str(m).strip()
    if s in C.ZS_SUFFIX:
        return s
    if s.lower() in MODE_ALIASES:
        return MODE_ALIASES[s.lower()]
    for k, suf in C.ZS_SUFFIX.items():
        if s.endswith(suf):
            return k
    raise ValueError(f"unknown zero-shot mode {m!r}")


def _first(d, keys):
    if not isinstance(d, dict):
        return None
    for k in keys:
        v = d.get(k)
        if v is not None:
            return v
    return None


def _scalar(v):
    """A recorded descriptive value: a finite or non-finite number, a bool, a short string; {ce|ce_bits|value|member: x} -> x."""
    if isinstance(v, dict):
        v = _first(v, ("ce", "ce_bits", "value", "member"))
    if isinstance(v, (bool, np.bool_)):
        return bool(v)
    x = _num(v)
    if x is not None:
        return x
    return v if isinstance(v, str) and len(v) <= 64 else None


# ------------------------------------------------------------------------------------------------ rows and versions
def load_rows(paths=None):
    """Plan rows of the given JSONL files (default: the ALN3 units.jsonl and plan_ext.jsonl). A missing file raises."""
    rows = []
    for p in (paths if paths is not None else (PLAN, PLAN_EXT)):
        with open(p) as f:
            rows += [json.loads(line) for line in f if line.strip()]
    return rows


def load_entity_manifest(path=None):
    """Federici record_uid -> (subject_uid, condition, entity_type), as bc_interim.load_manifest."""
    with open(path or ENTITY_MANIFEST) as f:
        return {r["record_uid"]: (r["subject_uid"], r["condition"], r["entity_type"]) for r in csv.DictReader(f)}


def analysed(row):
    f, s = row.get("family_id", ""), row.get("spec") or {}
    if f in SEL.STAGE:
        return True
    return (f == "E_LOCAL" and row.get("dataset") == PRIVATE and s.get("architecture") == "lag_local_tokens"
            and s.get("window", "full") == "full" and s.get("projection_dim", 32) == 32 and row.get("seed") in ALL_SEEDS
            and s.get("objective") in OBJECTIVES)


def read_unit(units_dir, eid):
    """units/<eid>.json (complete), else units/<eid>.FAILED.json (core.write_record's failure file), else None."""
    for name in (f"{eid}.json", f"{eid}.FAILED.json"):
        p = os.path.join(units_dir, name)
        if os.path.exists(p):
            with open(p) as f:
                return json.load(f)
    return None


def _explicit_label(row):
    s = row.get("spec") or {}
    v = s.get("version", s.get("execution_version"))
    return None if v is None else str(v)


def _version_label(depth):
    return PRIMARY_VERSION if depth == 0 else f"continuation_{depth}"


def execution_versions(rows):
    """experiment_id -> {"version", "explicit", "notes"} for every E34 row of `rows` (module docstring, 'Execution versions').
    Raises ValueError on a continuation / horizon cycle."""
    by = {}
    for r in rows:
        by.setdefault(r.get("experiment_id"), r)
    depth, notes = {}, defaultdict(list)

    def is_group(e):
        g = by.get(e) if isinstance(e, str) else None
        return g is not None and SEL.STAGE.get(g.get("family_id")) == "donor_group"

    def gdepth(gid, stack=()):
        if gid in depth:
            return depth[gid]
        if gid in stack:
            raise ValueError(f"continuation / horizon cycle through donor group {gid}")
        g, stack = by[gid], stack + (gid,)
        s = g.get("spec") or {}
        cont, hor = s.get("continuation_of") or None, s.get("horizon_from") or None
        d_cont = None
        if cont is not None:
            if is_group(cont):
                d_cont = gdepth(cont, stack) + 1
            else:
                d_cont = 1
                notes[gid].append(f"continuation source {cont} is not a donor-group plan row: taken as a first continuation")
        d = d_cont if d_cont is not None else 0
        if g.get("family_id") in (SEL.RICH_DONOR, SEL.CSX_DONOR):
            if hor is not None and is_group(hor):
                d_hor = gdepth(hor, stack)
                if d_cont is not None and d_cont != d_hor:
                    notes[gid].append(f"continuation chain gives {_version_label(d_cont)} but the horizon source {hor} is "
                                      f"{_version_label(d_hor)}: the horizon source's version is used (equal updates)")
                d = d_hor
            else:
                notes[gid].append(f"rich / CSX group without a donor-group horizon_from ({hor}): version from its own "
                                  "continuation chain")
        depth[gid] = d
        return d

    out = {}
    for r in rows:
        e, st = r.get("experiment_id"), SEL.STAGE.get(r.get("family_id"))
        if st is None or e in out:
            continue
        ex, extra = _explicit_label(r), []
        if st == "donor_group":
            v = _version_label(gdepth(e))
        else:
            sl = SEL.slot_of(r)
            if sl is None:
                v = PRIMARY_VERSION  # target_from_scratch: never re-registered by a continuation (§2.10)
            elif is_group(sl[0]):
                v = _version_label(gdepth(sl[0]))
                gx = _explicit_label(by[sl[0]])
                if ex is not None and gx is not None and ex != gx:
                    extra.append(f"spec.version label {ex!r} differs from its donor group's {gx!r} (labels are not keys)")
            else:
                v = PRIMARY_VERSION
                extra.append(f"donor group {sl[0]} is not a donor-group plan row: execution version taken as primary")
        out[e] = {"version": v, "explicit": ex, "notes": notes.get(e, []) + extra}
    return out


# ------------------------------------------------------------------------------------------------ freeze gate (§5.1)
def code_files():
    """Code the analysis's behaviour depends on (its sha256 must be listed in the execution record)."""
    return {"auditory_alignment_v3/prior33/analysis.py": os.path.abspath(__file__),
            "tests/auditory_alignment_v3/prior33/test_analysis.py": TESTS,
            "auditory_alignment_v3/prior33/select.py": SEL.__file__,
            "auditory_alignment_v3/prior33/contract.py": C.__file__,
            "auditory_alignment_v3/sci_r1/stats.py": S.__file__,
            "auditory_alignment/aggregate.py": AGG.__file__}


def code_sha256():
    out = {}
    for k, p in code_files().items():
        try:
            with open(p, "rb") as f:
                out[k] = hashlib.sha256(f.read()).hexdigest()
        except OSError:
            out[k] = None
    return out


def _listed(sha, tokens):
    """The sha256 (full) is listed when the record holds it or a prefix of >= 16 hex digits of it."""
    sha = str(sha).lower() if sha else ""
    return bool(sha) and any(sha.startswith(t) for t in tokens)


def frozen_check(rows=None, record_path=None):
    """Design §5.1: is every analysis code file's sha256, and the manifest sha256 of every E34 row of `rows`, listed in the
    execution record? -> {"ok", "problems", "files", "manifests", ...}."""
    record_path = record_path or EXEC_RECORD
    shas = code_sha256()
    present = os.path.exists(record_path)
    text = ""
    if present:
        with open(record_path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    tokens = set(HEX.findall(text.lower()))
    files = {k: {"sha256": v, "listed": _listed(v, tokens)} for k, v in shas.items()}
    e34 = [r for r in rows or () if r.get("family_id") in SEL.STAGE]
    man = Counter((r.get("spec") or {}).get("manifest_sha256") for r in e34)
    manifests = {str(m): {"rows": n, "listed": _listed(m, tokens)} for m, n in man.items() if m}
    rel = os.path.relpath(record_path, REPO)
    problems = [] if present else [f"the execution record {rel} is absent"]
    problems += [f"{k}: " + ("file unreadable" if f["sha256"] is None else f"sha256 {f['sha256'][:16]}… not listed in the record")
                 for k, f in files.items() if not f["listed"] and present]
    problems += [f"manifest sha256 {m[:16]}… of {v['rows']} E34 plan rows not listed in the record"
                 for m, v in sorted(manifests.items()) if not v["listed"] and present]
    a = "auditory_alignment_v3/prior33/analysis.py"
    return {"execution_record": rel, "present": present, "ok": not problems, "problems": problems, "files": files,
            "manifests": manifests, "e34_rows": len(e34), "e34_rows_without_manifest": man.get(None, 0),
            "analysis_sha256": shas[a], "analysis_sha256_listed": files[a]["listed"]}


def _inside(path, root):
    p, r = os.path.realpath(path), os.path.realpath(root)
    try:
        return os.path.commonpath([p, r]) == r
    except ValueError:
        return False


def dry_run_problems(units, plans, outputs):
    """Why a dry run (--allow-unfrozen) with these paths is refused (§5.1): it reads neither the live units directory nor the
    live plan files, and writes nothing under docs/, results/ or private/auditory_alignment_v3/. `outputs` {flag: path}."""
    probs = []
    if not units:
        probs.append("--units is required (a scratch units directory)")
    elif _inside(units, UNITS):
        probs.append(f"--units {units} is the live units directory or inside it")
    if not plans:
        probs.append("--plan is required (scratch plan files)")
    else:
        live = {os.path.realpath(p) for p in (PLAN, PLAN_EXT)}
        probs += [f"--plan {p} is a live plan file" for p in plans if os.path.realpath(p) in live]
    roots = (os.path.join(REPO, "docs"), os.path.join(REPO, "results"), OUT)
    for flag, p in outputs.items():
        if not p:
            probs.append(f"{flag} is required (a scratch directory)")
            continue
        probs += [f"{flag} {p} is inside {os.path.relpath(r, REPO)} (publication or live private tree)" for r in roots if _inside(p, r)]
    return probs


def live_records(rows):
    """E34 rows of `rows` with a record in the live units directory (existence only; nothing is opened)."""
    return [r["experiment_id"] for r in rows if r.get("family_id") in SEL.STAGE
            and any(os.path.exists(os.path.join(UNITS, f"{r['experiment_id']}{x}")) for x in (".json", ".FAILED.json"))]


# ------------------------------------------------------------------------------------------------ records
def load_records(rows, units_dir=None, loader=None):
    """Plan rows (any families; the analysed ones are selected here) -> one normalised unit per analysed row, in row order.
    `loader(eid)` -> record or None replaces the units-directory reader (tests). Missing records are kept as status 'missing'.
    The live units directory is read only when frozen_check(rows) passes (RuntimeError otherwise; design §5.1)."""
    rows = list(rows)
    if loader is None:
        units_dir = units_dir or UNITS
        if _inside(units_dir, UNITS):
            fz = frozen_check(rows)
            if not fz["ok"]:
                raise RuntimeError("the live units directory is read only by the frozen analysis (design §5.1): "
                                   + "; ".join(fz["problems"]))

        def read(e):
            return read_unit(units_dir, e)
    else:
        read = loader
    by, seen, sel = {}, set(), []
    for r in rows:
        by.setdefault(r.get("experiment_id"), r)
        if analysed(r):
            e = r["experiment_id"]
            if e in seen:
                raise ValueError(f"plan row {e} appears twice")
            seen.add(e)
            sel.append(r)
    vers = execution_versions(rows)
    grec = {r["experiment_id"]: read(r["experiment_id"]) for r in sel if SEL.STAGE.get(r.get("family_id")) == "donor_group"}
    units = []
    for r in sel:
        e = r["experiment_id"]
        rec = grec[e] if e in grec else read(e)
        group = None
        if SEL.STAGE.get(r.get("family_id")) in SLOT_STAGES:
            sl = SEL.slot_of(r)
            if sl is not None:
                g = by.get(sl[0])
                g = g if g is not None and SEL.STAGE.get(g.get("family_id")) == "donor_group" else None
                group = (g, grec.get(sl[0]) if g is not None else None)
        units.append(normalise(r, rec, vers.get(e), group))
    return units


def _level_kind(stage, cohort):
    if stage == "target":
        return "target_private" if cohort == PRIVATE else "target"
    return stage if stage in ("zero_shot", "donor_group") else None


def _level_status(kind, text):
    if kind is None:
        return "no declared level"
    if not text:
        return "missing"
    return "as declared" if re.search(SELECTION_LEVEL[kind][1], text, re.I) else "unexpected"


def normalise(row, rec, ver=None, group=None):
    """One plan row + its record (or None) -> the unit dict used by every analysis step (no raw record kept). `ver` is the
    row's execution_versions entry; `group` = (donor-group row or None, its record or None) for the member check."""
    s, f, eid = row.get("spec") or {}, row.get("family_id", ""), row["experiment_id"]
    if rec is not None and rec.get("experiment_id") not in (None, eid):
        raise ValueError(f"record {rec.get('experiment_id')} filed under plan row {eid}")
    stage = "reference" if f == "E_LOCAL" else SEL.stage_of(row)
    if ver is None:
        ver = {"version": NATIVE_VERSION if stage == "reference" else PRIMARY_VERSION, "explicit": _explicit_label(row), "notes": []}
    u = {"eid": eid, "family_id": f, "stage": stage, "status": "missing" if rec is None else str(rec.get("status") or "unknown"),
         "cohort": row.get("dataset"), "subject_fold": row.get("subject_fold"),
         "content_fold": 0 if row.get("content_fold") is None else row.get("content_fold"),
         "objective": s.get("objective"), "block": "aln3_native" if stage == "reference" else s.get("block"),
         "seed_scope": s.get("seed_scope", row.get("seed_scope")), "row_seed": row.get("seed"), "split_hash": s.get("split_hash"),
         "manifest_sha256": s.get("manifest_sha256"), "donor_group": s.get("donor_group"), "bridge": s.get("bridge"),
         "member_spec": s.get("member", s.get("members")), "readout_seeds": s.get("readout_seeds"), "slot": None, "mode": None,
         "donor_seed": None, "target_seed": None, "spec_donor_seed": s.get("donor_seed"),
         "version": ver["version"], "version_label": ver.get("explicit"), "row_continuation_of": s.get("continuation_of"),
         "compute_limit": None, "target": s.get("target"), "target_hash": s.get("target_contract"), "record_target_contract": None,
         "eval_version": None, "member_resolved": None, "member_expected": None, "member_check": None, "member_check_detail": None,
         "selection_level": None, "level_status": None, "views": {}, "view_status": {}, "extra": None, "donor": None,
         "bridge_info": None, "notes": list(ver.get("notes") or [])}
    sl = None
    if stage == "reference":
        u.update(slot=REFERENCE_SLOT, mode="T", target_seed=row.get("seed"))
    elif stage in ("target", "zero_shot"):
        sl = SEL.slot_of(row)
        u["slot"] = SEL.SCRATCH if sl is None else sl[1]
        if stage == "target":
            u["mode"], u["target_seed"] = "T", s.get("target_seed", row.get("seed"))
            u["donor_seed"] = None if sl is None else s.get("donor_seed")
            if sl is not None and u["donor_seed"] is None:
                u["notes"].append("donor-initialised target row without spec.donor_seed")
        else:
            u["mode"], u["donor_seed"] = canon_mode(s.get("mode")), s.get("donor_seed", row.get("seed"))
    elif stage == "bridge":
        sl = SEL.slot_of(row)
        u["slot"], u["donor_seed"] = sl[1], s.get("donor_seed", row.get("seed"))
    else:
        u["donor_seed"] = s.get("donor_seed", row.get("seed"))
        m = LIMIT.search(str((s.get("budget") or {}).get("continuation") or ""))
        u["compute_limit"] = int(m.group(1)) if m else None
    if rec is None:
        return u
    u["record_target_contract"] = rec.get("target_contract")
    u["eval_version"] = rec.get("eval_version") or rec.get("code_hash")
    lv = rec.get("selection_level")
    u["selection_level"] = lv if lv is None or isinstance(lv, str) else json.dumps(lv, sort_keys=True)
    if u["status"] != "complete":
        return u
    probe = stage != "reference" and (rec.get("truncated") or rec.get("epochs_override") is not None
                                       or (rec.get("dependency") or {}).get("truncated"))
    u["level_status"] = _level_status(_level_kind(stage, u["cohort"]), u["selection_level"])
    if sl is not None:
        u["member_resolved"], u["member_expected"], u["member_check"], u["member_check_detail"] = _member_check(row, rec, sl, group)
    if stage in EVAL_STAGES:
        parse = _private_view if u["cohort"] == PRIVATE else _continuous_view
        try:
            u["views"]["primary"] = parse(rec["eval"], u)
        except (KeyError, TypeError, AttributeError) as ex:
            u["status"] = "complete_unparseable"
            u["notes"].append(f"eval not parseable ({type(ex).__name__}: {ex})")
            return u
        extra = {}
        if stage == "target":
            extra["gainsel"] = _gainsel(rec)
        elif stage == "zero_shot":
            ev = _first(rec, UNI_CAL_KEYS)
            if ev is None:
                ev = ((rec.get("sensitivity") or {}).get("B_uni_cal") or (rec.get("evals") or {}).get("B_uni_cal")
                      or (rec.get("evals") or {}).get("uni_cal"))
            extra["uni_cal"] = ("evaluated" if isinstance(ev, dict) else "absent", ev)
        for view, (st, ev) in extra.items():
            if st == "identical":
                u["views"][view] = u["views"]["primary"]
            elif st == "evaluated":
                try:
                    u["views"][view] = parse(ev, u)
                except (KeyError, TypeError, AttributeError) as ex:
                    st = "unparseable"
                    u["notes"].append(f"{view} evaluation not parseable ({type(ex).__name__}: {ex})")
            u["view_status"][view] = st
    elif stage == "donor_group":
        u["extra"] = _scalars(rec, DONOR_KEYS)
        u["donor"] = _donor_table(row, rec)
    elif stage == "bridge":
        u["extra"] = _scalars(rec, BRIDGE_KEYS)
        u["bridge_info"] = _bridge_info(rec)
    if probe:
        u["status"] = "probe_truncated"
        u["notes"].append("probe budget or truncated donor: excluded from production comparisons; parsed views retained for engineering checks")
    return u


def _member_check(row, rec, sl, group):
    """(member used, expected member, status, detail) of a complete slot unit. Expected: the slot's own tag; for J*,
    select.member_of(row, donor-group record) (the lambda rule). Status: agrees | derived (the unit records no member; the
    expected one is used) | disagrees | unverifiable (J*: no complete group record, or select cannot resolve it) | unchecked
    (no donor-group context: normalise called outside load_records)."""
    gid, name = sl
    recorded = _first(rec, RESOLVED_KEYS)
    if recorded is None and isinstance(rec.get("member"), str) and rec["member"] in SEL.MEMBER_TAGS:
        recorded = rec["member"]
    source = "the slot"
    if name != SEL.JOINT:
        exp, why = (name if name in SEL.MEMBER_TAGS else None), f"slot {name} is not a member tag"
    elif group is None:
        return recorded, None, "unchecked", "no donor-group context"
    elif group[0] is None:
        exp, why = None, f"donor group {gid} is not a donor-group plan row"
    elif not isinstance(group[1], dict) or group[1].get("status") != "complete":
        exp, why = None, f"the record of donor group {gid} is " + ("missing" if group[1] is None else "not complete")
    else:
        source = "the lambda rule on the donor-group record"
        try:
            exp, why = SEL.member_of(row, group[1]), None
        except (SEL.SelectionError, ValueError) as ex:
            exp, why = None, f"select.member_of raised {type(ex).__name__}: {ex}"
    if exp is None:
        return recorded, None, "unverifiable", why
    if recorded is None:
        return exp, exp, "derived", f"no member recorded by the unit; {exp} from {source}"
    if recorded == exp:
        return recorded, exp, "agrees", None
    return recorded, exp, "disagrees", f"the unit records member {recorded}; {source} gives {exp}"


def _gainsel(rec):
    g = rec.get("gainsel")
    if isinstance(g, str) and g.strip().lower() == "identical":
        return "identical", None
    if isinstance(g, dict):
        if g.get("identical") is True or str(g.get("status", "")).lower() == "identical":
            return "identical", None
        if isinstance(g.get("eval"), dict):
            return "evaluated", g["eval"]
    ev = _first(rec, GAINSEL_KEYS)
    if ev is None:
        ev = (rec.get("evals") or {}).get("gainsel")
    return ("evaluated", ev) if isinstance(ev, dict) else ("absent", None)


def _scalars(rec, pat, prefix="", depth=0):
    """Descriptive copy of a donor-group / bridge record: scalars (numbers, booleans, short strings) whose key path matches."""
    out = {}
    if depth > 4 or not isinstance(rec, dict):
        return out
    for k, v in rec.items():
        if str(k) in SKIP_KEYS:
            continue
        path = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(_scalars(v, pat, path + "/", depth + 1))
        elif isinstance(v, (list, tuple)) or not pat.search(path):
            continue
        elif isinstance(v, (bool, np.bool_)):
            out[path] = bool(v)
        elif _num(v) is not None:
            out[path] = _num(v) if math.isfinite(_num(v)) else None
        elif isinstance(v, str) and len(v) <= 64:
            out[path] = v
    return out


def _tag(v):
    """A recorded joint choice -> member tag (J1 / J025 also from the lambda values 1 / 0.25)."""
    v = _first(v, ("member", "choice")) if isinstance(v, dict) else v
    x = _num(v)
    if x is not None:
        return LAMBDA_TAGS.get(x, str(v))
    return v if isinstance(v, str) else None


def _donor_table(row, rec):
    """The fixed donor-side SELECTION table of one donor-group record (§5.4): per member, CE_dev / gain / bridge_cal CE / ep-eq
    of the _best, _h30 and _gainsel checkpoints; the group horizon and ceiling flag; for groups with J1 and J025 the lambda rule
    recomputed by select (min CE_dev of _best, tie 1e-4 -> J1) beside the recorded choices under both rules."""
    try:
        members = list(SEL.group_members(row))
        err = None
    except ValueError as ex:
        recm = rec.get("members")
        members, err = (sorted(recm) if isinstance(recm, dict) else []), str(ex)
    recm = rec.get("members") if isinstance(rec.get("members"), dict) else {}
    tab = {}
    for M in members:
        e = recm.get(M) if isinstance(recm.get(M), dict) else {}
        r = {}
        for kind, kkeys in CKPT_KINDS.items():
            d = _first(e, kkeys)
            for q, qkeys in CKPT_FIELDS.items():
                v = _first(d, qkeys) if isinstance(d, dict) else None
                if v is None:
                    v = _first(e, tuple(f"{k}_{x}" for k in kkeys for x in qkeys))
                r[f"{kind}/{q}"] = _scalar(v)
        r["steps"], r["nonfinite_steps"] = _scalar(e.get("steps")), _scalar(e.get("nonfinite_steps"))
        tab[M] = r
    out = {"members": tab, "member_error": err, "horizon_ep_eq": _scalar(_first(rec, HORIZON_KEYS)),
           "ceiling_reached_while_improving": _scalar(rec.get("ceiling_reached_while_improving")), "lambda": None}
    if all(m in members for m in SEL.JOINT_CANDIDATES):
        lam = {"rule": SEL.LAMBDA_RULE}
        try:
            c1, c2 = SEL.member_best_ce(rec, "J1"), SEL.member_best_ce(rec, "J025")
            lam.update(ce_dev={"J1": c1, "J025": c2}, choice=SEL.lambda_choice(c1, c2), error=None)
        except SEL.SelectionError as ex:
            lam.update(ce_dev=None, choice=None, error=str(ex))
        jc = rec.get("joint_choice")
        lam["recorded_primary"] = _tag(jc) if jc is not None else None
        if isinstance(jc, dict) and jc.get("rule") not in (None, SEL.LAMBDA_RULE):
            lam["recorded_primary_rule"] = str(jc.get("rule"))
        lam["recorded_gain_rule"] = _tag(_first(rec, GAIN_RULE_KEYS))
        lam["gainsel_gain"] = {m: tab[m]["gainsel/gain"] for m in SEL.JOINT_CANDIDATES}
        lam["check"] = ("not recorded" if lam["recorded_primary"] is None else "rule not recomputable" if lam["choice"] is None
                        else "agrees" if lam["recorded_primary"] == lam["choice"] else "disagrees")
        out["lambda"] = lam
    return out


def _bridge_info(rec):
    out = {k: _scalar(_first(rec, keys)) for k, keys in BRIDGE_FIELDS.items()}
    ap = rec.get("artefact_probe") or rec.get("artifact_probe")
    if isinstance(ap, dict):
        out.update({f"artefact_probe/{k}": _scalar(v) for k, v in sorted(ap.items()) if _scalar(v) is not None})
    return out


def _tolerant_rows(ev):
    """auditory_alignment.aggregate.unit_rows with guards: a derived endpoint is skipped when one of its inputs is absent."""
    out = {}
    for pid, r in ev["per_participant"].items():
        row = {"group": r.get("group")}
        for k, v in r.items():
            if isinstance(v, dict):
                for m, x in v.items():
                    if isinstance(x, (int, float)) and not isinstance(x, bool) and m not in ("n_candidates", "n_queries", "n_rows", "draws"):
                        row[f"{k}/{m}"] = float(x)
            elif isinstance(v, (int, float)) and not isinstance(v, bool) and k not in ("n", "n_segments"):
                row[k] = float(v)
        for rd in ("native", "unified"):
            reg = row.get(f"{rd}/regular/logloss_bits")
            if reg is None:
                continue
            mm, rr, mr, hd = (row.get(f"{rd}/mismatched_eeg/logloss_bits"), row.get(f"{rd}/regular/rank_pct"),
                              row.get(f"{rd}/mismatched_eeg/rank_pct"), row.get(f"{rd}/hard/logloss_bits"))
            if mm is not None:
                row[f"{rd}/gain_bits"] = mm - reg
            if rr is not None and mr is not None:
                row[f"{rd}/rank_gain"] = mr - rr
            if hd is not None:
                row[f"{rd}/hard_gain_bits"] = float(np.log2(1 + AGG.K_HARD)) - hd
        if "kernel_dependence/cs_true_minus_mismatched" in row:
            row["kernel_cs_diff"] = row["kernel_dependence/cs_true_minus_mismatched"]
        out[pid] = row
    for pid, r in (ev.get("attention_2afc") or {}).items():
        for rd, v in r.items():
            if not isinstance(v, dict):
                continue
            out.setdefault(pid, {"group": (ev["per_participant"].get(pid) or {}).get("group")})
            if "accuracy" in v:
                out[pid][f"attention/{rd}/accuracy"] = v["accuracy"]
            if "mean_margin" in v:
                out[pid][f"attention/{rd}/margin"] = v["mean_margin"]
    return out


def _continuous_view(ev, u):
    pp = ev["per_participant"]
    try:
        rows = AGG.unit_rows({"eval": ev})
    except (KeyError, TypeError) as ex:
        rows = _tolerant_rows(ev)
        u["notes"].append(f"unit_rows raised {type(ex).__name__} {ex}; derived endpoints with missing inputs were skipped")
    na = u["mode"] != "T" and u["objective"] == "NCE" and u["slot"] in NATIVE_NA_SLOTS
    view = {"rows": {}, "groups": {p: v.get("group") for p, v in pp.items()}, "counts": {},
            "n_test_candidates": (ev.get("readout") or {}).get("n_test_candidates"), "native_not_applicable": na}
    for p, v in pp.items():
        rg = v.get("unified/regular")
        view["counts"][p] = (rg.get("n_candidates"), rg.get("n_queries")) if isinstance(rg, dict) else None
    for p, r in rows.items():
        view["rows"][p] = {m: x for m, x in r.items() if m != "group" and not (na and m.startswith("native/"))}
    return view


def _private_view(ev, u):
    """Per child: NLL / AUC (positive-affine, calib.private_variants), hist_gain, twin_sens (bc_interim.child_values semantics)."""
    pp = ev["per_participant"]
    nc = (ev.get("native_calibration") or {}).get("per_participant") or {}
    if not nc:
        u["notes"].append("no native_calibration block: positive-affine NLL / AUC unavailable")
    view = {"rows": {}, "groups": {}, "counts": {}, "n_test_candidates": None, "native_not_applicable": False}
    for c, v in pp.items():
        pa = (nc.get(c) or {}).get("positive_affine") or {}
        d = {k: _num(pa.get(src)) for k, src in (("NLL", "nll_bits"), ("AUC", "auc_score"))}
        hg, ht = _num(v.get("hist_gain_bits")), _num(v.get("hist_gain_twin_bits"))
        if hg is not None:
            d["hist_gain"] = hg
            if ht is not None:
                d["twin_sens"] = hg - ht
        view["rows"][c] = {k: x for k, x in d.items() if x is not None}
        view["groups"][c] = v.get("group")
        view["counts"][c] = (v.get("n") if v.get("n") is not None else pa.get("n"),)
    return view


# ------------------------------------------------------------------------------------------------ identities
def unit_identities(u, view, manifest):
    """One unit's evaluation view -> ({identity: {group, values}}, info). Federici records -> subject_uid (records of one
    subject averaged; non-human entities excluded and counted); FAU always-train TH ids never tested (excluded, counted);
    non-finite values excluded and counted per endpoint."""
    v = u["views"].get(view)
    info = {"phantom_records": 0, "phantom_entities": set(), "always_train_th": 0, "nonfinite": Counter()}
    if v is None:
        return {}, info
    acc, grp = defaultdict(lambda: defaultdict(list)), {}
    for pid, vals in v["rows"].items():
        if u["cohort"] == "federici":
            if pid not in manifest:
                raise KeyError(f"Federici record {pid!r} of {u['eid']} is not in the entity manifest")
            ident, g, kind = manifest[pid]
            if kind != "human":
                info["phantom_records"] += 1
                info["phantom_entities"].add(ident)
                continue
        else:
            ident, g = str(pid), _group(u["cohort"], v["groups"].get(pid))
            if u["cohort"] == "fau" and ident in FAU_ALWAYS_TRAIN_TH:
                info["always_train_th"] += 1
                continue
        grp[ident] = g
        acc[ident]  # noqa: B018 (an identity with no finite value is still listed)
        for m, x in vals.items():
            x = _num(x)
            if x is None:
                continue
            if not math.isfinite(x):
                info["nonfinite"][m] += 1
                continue
            acc[ident][m].append(x)
    return {i: {"group": grp[i], "values": {m: float(np.mean(xs)) for m, xs in acc[i].items()}} for i in grp}, info


def _sig(v):
    """Pool signature of an evaluation view: (participants, per-participant candidate / query counts, n_test_candidates)."""
    return (frozenset(v["rows"]), tuple(sorted(v["counts"].items(), key=lambda kv: str(kv[0]))), v.get("n_test_candidates"))


def _sig_diff(a, b):
    """What differs between pool signatures a (the unit) and b (the reference); counts only, never participant ids."""
    out = []
    if a[0] != b[0]:
        out.append(f"participant set ({len(a[0])} vs {len(b[0])}: {len(a[0] - b[0])} only in the unit, {len(b[0] - a[0])} "
                   "only in the reference)")
    if a[1] != b[1]:
        ca, cb = dict(a[1]), dict(b[1])
        out.append(f"candidate / query counts ({sum(1 for p in set(ca) | set(cb) if ca.get(p) != cb.get(p))} participants)")
    if a[2] != b[2]:
        out.append(f"n_test_candidates ({a[2]} vs {b[2]})")
    return out


class _Ctx:
    """Index (configuration -> cell -> unit), the engineering exclusions (member and pool checks), cached per-unit identity
    values, pairing and family runs, and the per-identity store."""

    def __init__(self, units, manifest):
        self.units, self.manifest = list(units), manifest or {}
        self.index, self.notes = defaultdict(dict), []
        self._ids, self.unit_info, self.diffs = {}, {}, {}
        self.excluded = {}  # eid -> reason: excluded from every family and summary
        for u in self.units:
            if u["stage"] not in EVAL_STAGES:
                continue
            c, cell = config_of(u), cell_of(u)
            old = self.index[c].get(cell)
            if old is None:
                self.index[c][cell] = u
            elif u["status"] == "complete" and old["status"] == "complete":
                raise ValueError(f"ambiguous duplicate units {old['eid']} and {u['eid']} for {ckey(c)} cell {list(cell)}: "
                                 "deduplicate by provenance, never by score")
            elif u["status"] == "complete":
                self.notes.append(f"{old['eid']} ({old['status']}) not used: complete unit {u['eid']} has the same configuration "
                                  f"{ckey(c)} and cell {list(cell)}")
                self.index[c][cell] = u
            else:
                self.notes.append(f"{u['eid']} ({u['status']}) not used: unit {old['eid']} has the same configuration {ckey(c)} "
                                  f"and cell {list(cell)}")
        self.index = dict(self.index)
        for u in self.units:
            if u["status"] == "complete" and u["stage"] in EVAL_STAGES and u.get("member_check") in MEMBER_EXCLUDE:
                self.exclude(u, f"member check {u['member_check']}: {u['member_check_detail']}")
        self.pool = _pool_check(self)

    def exclude(self, u, why):
        self.excluded[u["eid"]] = f"{self.excluded[u['eid']]}; {why}" if u["eid"] in self.excluded else why

    def ids(self, u, view):
        k = (u["eid"], view)
        if k not in self._ids:
            self._ids[k], self.unit_info[k] = unit_identities(u, view, self.manifest)
        return self._ids[k]

    def status(self, u, view):
        if u is None:
            return "unregistered"
        if u["status"] != "complete":
            return u["status"]
        if u["eid"] in self.excluded:
            return "excluded"
        if u["views"].get(view) is None:
            return f"{view} evaluation {u['view_status'].get(view, 'absent')}"
        return "complete"

    def paired(self, rc, cc, metric, allow=(), views=("primary", "primary")):
        """Within-identity paired differences of `metric` between two configurations, on matched cells only.
        -> ({identity: diff}, {identity: n matched units}, {identity: group}, pairing info)."""
        R, Cd = self.index.get(rc, {}), self.index.get(cc, {})
        info = {"cells_matched": 0, "cells_missing": [], "cells_unregistered": [], "cells_excluded": []}
        per, grp, seen = defaultdict(list), {}, Counter()
        for cell in sorted(set(R) | set(Cd), key=_cellsort):
            ur, uc = R.get(cell), Cd.get(cell)
            sr, sc = self.status(ur, views[0]), self.status(uc, views[1])
            present = set()
            for u, st, v in ((ur, sr, views[0]), (uc, sc, views[1])):
                if st == "complete":
                    present |= set(self.ids(u, v))
            for i in present:
                seen[i] += 1
            if "unregistered" in (sr, sc):
                info["cells_unregistered"].append({"cell": list(cell), "reference": sr, "candidate": sc})
                continue
            if "excluded" in (sr, sc):
                sides = [("reference", ur, sr)] + ([] if uc is ur else [("candidate", uc, sc)])
                info["cells_excluded"].append({"cell": list(cell), "reason": "; ".join(
                    f"{side} unit {u['eid']} excluded: {self.excluded[u['eid']]}" for side, u, st in sides if st == "excluded")})
                continue
            if sr != "complete" or sc != "complete":
                info["cells_missing"].append({"cell": list(cell), "reference": sr, "candidate": sc})
                continue
            why = _pair_check(ur, uc, views, allow)
            if why:
                info["cells_excluded"].append({"cell": list(cell), "reason": why})
                continue
            info["cells_matched"] += 1
            ir, ic = self.ids(ur, views[0]), self.ids(uc, views[1])
            for i in sorted(set(ir) & set(ic)):
                x, y = ir[i]["values"].get(metric), ic[i]["values"].get(metric)
                if x is None or y is None:
                    continue
                per[i].append(_diff(x, y, DIRECTION[metric]))
                grp[i] = ir[i]["group"]
        diffs = {i: float(np.mean(v)) for i, v in per.items()}
        info["n_paired"] = len(diffs)
        info["identities_unpaired"] = sum(1 for i in seen if i not in diffs)
        info["identities_partial"] = sum(1 for i, v in per.items() if len(v) < seen[i])
        return diffs, {i: len(v) for i, v in per.items()}, grp, info

    def family(self, label, metric, specs, allow=(), simultaneous=True, views=("primary", "primary"), keep_pairing=True):
        """specs [(member name, reference configuration, candidate configuration)] -> family result (one endpoint)."""
        Ys, infos = {}, {}
        store = self.diffs.setdefault(f"{label}|{metric}", {})
        for name, rc, cc in specs:
            d, nu, grp, info = self.paired(rc, cc, metric, allow, views)
            Ys[name], infos[name] = d, info
            store[name] = {i: {"diff": d[i], "n_units": nu[i], "group": grp.get(i)} for i in sorted(d)}
        res = family_stats(label, metric, Ys, simultaneous, [n for n, _, _ in specs])
        res.update(label=label, endpoint=LABEL[metric], endpoint_key=metric, direction=DIRECTION[metric],
                   direction_text=DIR_TEXT[DIRECTION[metric]], views=list(views))
        for name, rc, cc in specs:
            m, p = res["members"][name], infos[name]
            m["reference"], m["candidate"] = ckey(rc), ckey(cc)
            m["pairing"] = p if keep_pairing else {k: (len(v) if isinstance(v, list) else v) for k, v in p.items()}
            if not Ys[name]:
                m["status"] = self._why_empty(p, rc, cc, metric)
        return res

    def _why_empty(self, info, rc, cc, metric):
        if metric.startswith("native/") and rc[2] != "T" and rc[1] == "NCE" and (rc[3] in NATIVE_NA_SLOTS or cc[3] in NATIVE_NA_SLOTS):
            return "not applicable: native readout of an encoder never trained against v (design §2.11)"
        nr, nc = len(self.index.get(rc, {})), len(self.index.get(cc, {}))
        if not nr or not nc:
            return f"not registered (reference {nr} units, candidate {nc} units)"
        if not info["cells_matched"]:
            return (f"no matched cell pair ({len(info['cells_missing'])} missing, {len(info['cells_excluded'])} excluded, "
                    f"{len(info['cells_unregistered'])} unregistered)")
        return "endpoint not available in the matched cells"


def _short(x):
    return "None" if x is None else (str(x)[:12] + ("…" if len(str(x)) > 12 else ""))


def _pair_check(ur, uc, views, allow):
    """None when the two complete units form a valid cell pair; otherwise the reason (only `allow` fields may differ)."""
    if ur is uc:  # a within-record contrast (SELECTION): same unit, two evaluations
        return None
    why = [f"{lab} differs" + (f" ({_short(ur.get(f))} vs {_short(uc.get(f))})" if show else "")
           for f, lab, show in PAIR_FIELDS if f not in allow and ur.get(f) != uc.get(f)]
    if "mode" not in allow and ur["mode"] != uc["mode"]:
        why.append("input-access mode differs")
    if "version" not in allow and ur["version"] != uc["version"]:
        why.append(f"execution version differs ({ur['version']} vs {uc['version']})")
    if ur["target_seed"] != uc["target_seed"]:
        why.append("target_seed differs")
    if "donor_seed" not in allow and ur["donor_seed"] != uc["donor_seed"]:
        why.append("donor_seed differs")
    if why:
        return "; ".join(why)
    vr, vc = ur["views"][views[0]], uc["views"][views[1]]
    if set(vr["rows"]) != set(vc["rows"]):
        return "participant sets differ"
    bad = sum(1 for p in set(vr["counts"]) | set(vc["counts"]) if vr["counts"].get(p) != vc["counts"].get(p))
    if bad:
        return f"candidate / query counts differ ({bad} participants)"
    if vr.get("n_test_candidates") != vc.get("n_test_candidates"):
        return f"n_test_candidates differ ({vr.get('n_test_candidates')} vs {vc.get('n_test_candidates')})"
    return None


def _pool_check(ctx):
    """§2.13 / §5.8: in every cell the complete mode-T units are the reference (they must agree with each other); every
    zero-shot unit must test the same participants with the same candidate / query counts and n_test_candidates. A differing
    zero-shot unit, or every zero-shot unit of a cell whose mode-T units disagree, is excluded (ctx.exclude); without a complete
    mode-T unit the cell's zero-shot units are unverified and listed."""
    cells = defaultdict(lambda: {"T": [], "Z": []})
    for c, cl in ctx.index.items():
        if c[3] == REFERENCE_SLOT:
            continue
        for cell, u in cl.items():
            if u["status"] == "complete" and u["views"].get("primary") is not None:
                cells[(u["cohort"], cell)]["T" if u["mode"] == "T" else "Z"].append(u)
    out = {"reference": "the cell's complete mode-T units (they must agree with each other)", "cells_checked": 0,
           "cells_with_t_and_zero_shot": 0, "zero_shot_units_checked": 0, "zero_shot_units_verified": 0,
           "cells_t_disagree": [], "zero_shot_units_excluded": [], "zero_shot_units_unverified": []}
    for (cohort, cell), d in sorted(cells.items(), key=lambda kv: (str(kv[0][0]), _cellsort(kv[0][1]))):
        out["cells_checked"] += 1
        tsig = defaultdict(list)
        for u in d["T"]:
            tsig[_sig(u["views"]["primary"])].append(ckey(config_of(u)))
        if len(tsig) > 1:
            sigs = list(tsig)
            out["cells_t_disagree"].append({
                "cohort": cohort, "cell": list(cell),
                "differs_in": sorted({x.split(" (")[0] for a in sigs for b in sigs if a is not b for x in _sig_diff(a, b)}),
                "groups": [{"configurations": sorted(tsig[s]), "n_participants": len(s[0]), "n_test_candidates": s[2]} for s in sigs]})
        if not d["Z"]:
            continue
        out["cells_with_t_and_zero_shot"] += bool(d["T"])
        for z in sorted(d["Z"], key=lambda u: ckey(config_of(u))):
            out["zero_shot_units_checked"] += 1
            entry = {"cohort": cohort, "cell": list(cell), "configuration": ckey(config_of(z)), "eid": z["eid"]}
            if not tsig:
                out["zero_shot_units_unverified"].append({**entry, "reason": "no complete mode-T unit in the cell"})
                continue
            if len(tsig) > 1:
                why = "the cell's mode-T units disagree with each other, so its zero-shot pool cannot be verified"
            else:
                diff = _sig_diff(_sig(z["views"]["primary"]), next(iter(tsig)))
                if not diff:
                    out["zero_shot_units_verified"] += 1
                    continue
                why = "zero-shot pool differs from the cell's mode-T units: " + "; ".join(diff)
            ctx.exclude(z, why)
            out["zero_shot_units_excluded"].append({**entry, "reason": why})
    return out


def identity_values(units, manifest=None, view="primary", _ctx=None):
    """{configuration: {"identities": {identity: {group, n_units, cells, values}}, "info": {...}}}: per identity and
    configuration the mean over that identity's complete, non-excluded units (content folds, outer folds; records -> subject)."""
    ctx = _ctx if _ctx is not None else _Ctx(units, manifest)
    out = {}
    for c in sorted(ctx.index, key=ckey):
        per, grp, cells = defaultdict(lambda: defaultdict(list)), {}, defaultdict(list)
        info = {"units": 0, "units_excluded": 0, "phantom_records": 0, "phantom_entities": set(), "always_train_th": 0,
                "nonfinite": Counter()}
        for cell in sorted(ctx.index[c], key=_cellsort):
            u = ctx.index[c][cell]
            if u["status"] != "complete" or u["views"].get(view) is None:
                continue
            if u["eid"] in ctx.excluded:
                info["units_excluded"] += 1
                continue
            ids = ctx.ids(u, view)
            ui = ctx.unit_info[(u["eid"], view)]
            info["units"] += 1
            info["phantom_records"] += ui["phantom_records"]
            info["phantom_entities"] |= ui["phantom_entities"]
            info["always_train_th"] += ui["always_train_th"]
            info["nonfinite"].update(ui["nonfinite"])
            for i, d in ids.items():
                grp[i] = d["group"]
                cells[i].append(list(cell))
                per[i]  # noqa: B018
                for m, x in d["values"].items():
                    per[i][m].append(x)
        if info["units"]:
            out[c] = {"identities": {i: {"group": grp[i], "n_units": len(cells[i]), "cells": cells[i],
                                         "values": {m: float(np.mean(x)) for m, x in per[i].items()}} for i in sorted(grp)},
                      "info": info}
    return out


# ------------------------------------------------------------------------------------------------ statistics
SUMM_KEYS = ("est", "se", "ci_low", "ci_high", "pct_low", "pct_high")


def _summ(y, idx):
    """sci_r1.stats.summary of identity values y with replicate indices idx -> (JSON-ready summary, raw summary or None)."""
    y = np.asarray(y, dtype=float)
    if len(y) < 3:
        return ({"est": float(y.mean())} if len(y) else {}) | {"note": "fewer than 3 identities: no interval"}, None
    s = S.summary(y, idx=idx)
    return {k: float(s[k]) for k in SUMM_KEYS}, s


def family_stats(label, metric, Ys, simultaneous=True, declared=None):
    """Ys {member: {identity: paired difference}} -> per member the pointwise summary on its own paired identities (n,
    est, se, bootstrap-t ci, percentile pct) and, if `simultaneous`, the family's max-t over the members that have pairs on
    their common identities (res["maxt"]: declared members, members in the max-t, family n, crit; per member "family_set").
    Replicate indices: S.draws(n, B, group_seed(label, metric)) for every summary, so they are shared within the family set."""
    names = list(declared) if declared is not None else list(Ys)
    seed = S.group_seed(label, metric)
    res = {"metric": metric, "simultaneous": bool(simultaneous), "members": {}}
    for n in names:
        y = Ys.get(n) or {}
        ids = sorted(y)
        r = res["members"][n] = {"n_paired": len(ids), "n": len(ids)}
        if ids:
            r.update(_summ([y[i] for i in ids], S.draws(len(ids), S.NB, seed) if len(ids) >= 3 else None)[0])
    if not simultaneous:
        return res
    present = [n for n in names if Ys.get(n)]
    common = sorted(set.intersection(*(set(Ys[n]) for n in present))) if present else []
    mx = {"declared_members": names, "n_declared": len(names), "members": [], "n_members": 0, "n": len(common), "crit": None}
    if len(common) >= 3:
        idx = S.draws(len(common), S.NB, seed)
        items, summ = {}, {}
        for n in present:
            summ[n], s = _summ([Ys[n][i] for i in common], idx)
            items[n] = (s["est"], s["se"], s["T"])
        fm = S.family_maxt(items)
        mx.update(members=list(items), n_members=int(fm["n_members"]), crit=float(fm["crit"]))
        for n, iv in fm["intervals"].items():
            res["members"][n]["family_set"] = {"n": len(common), **summ[n], "sim_low": float(iv["sim_low"]),
                                               "sim_high": float(iv["sim_high"]), "sim_position": _position(iv["sim_low"], iv["sim_high"])}
    elif present:
        mx["note"] = f"{len(common)} identities common to the members with pairs: no simultaneous interval (3 needed)"
    else:
        mx["note"] = "no member has paired identities"
    for n in names:
        if n not in mx["members"]:
            res["members"][n]["family_note"] = "not in the max-t: no paired identities" if not Ys.get(n) else mx.get("note")
    res["maxt"], res["n_common"] = mx, len(common)
    return res


# ------------------------------------------------------------------------------------------------ analysis sections
def _versions_order(units):
    vs = {u["version"] for u in units if u["stage"] != "reference"} | {PRIMARY_VERSION}

    def key(v):
        m = re.fullmatch(r"continuation_(\d+)", v)
        return (0, 0, "") if v == PRIMARY_VERSION else ((1, int(m.group(1)), "") if m else (2, 0, v))
    return sorted(vs, key=key)


def _versions_info(units, versions):
    out = []
    for v in versions:
        us = [u for u in units if u["version"] == v]
        out.append({"version": v, "donor_groups": sum(u["stage"] == "donor_group" for u in us),
                    "units": dict(sorted(Counter(u["stage"] for u in us).items())),
                    "compute_limits": sorted({u["compute_limit"] for u in us if u["compute_limit"] is not None}),
                    "explicit_labels": dict(sorted(Counter(u["version_label"] for u in us if u["version_label"] is not None).items())),
                    "downstream_rows_with_continuation_of": sum(1 for u in us if u["stage"] in SLOT_STAGES and u["row_continuation_of"])})
    return out


def _families(ctx, versions):
    fams, secs = {}, {}
    for version in versions:
        for fam, modes, members, declared, allow in FAMILIES:
            for mode, cohorts in modes.items():
                for cohort in cohorts:
                    seeds = ALL_SEEDS if (fam in PANEL_FAMILIES and cohort == PRIVATE and mode == "T") else (BREADTH_SEED,)
                    for obj in OBJECTIVES:
                        for seed in seeds:
                            specs = [(f"{r}->{c}", cfg(cohort, obj, mode, r, seed, PRIMARY_VERSION if r == SEL.SCRATCH else version),
                                      cfg(cohort, obj, mode, c, seed, version)) for r, c in members]
                            al = tuple(allow)
                            if version != PRIMARY_VERSION:
                                if not any(cc in ctx.index for _, _, cc in specs) and not any(
                                        rc in ctx.index and rc[6] == version for _, rc, _ in specs):
                                    continue
                                if any(rc[6] != version for _, rc, _ in specs):
                                    al += ("version",)  # INIT: the primary S rows (never re-registered, §2.10)
                            label = family_label(fam, cohort, obj, mode, seed, version)
                            head = {"family": fam, "block": "panel" if seed in PANEL_SEEDS else FAMILY_BLOCK[fam], "cohort": cohort,
                                    "objective": obj, "mode": mode, "seed_context": seed, "seed_label": _seed_label(seed),
                                    "version": version, "reference_version": PRIMARY_VERSION if "version" in al else version,
                                    "declared_variable": declared, "allowed_differences": list(al)}
                            for metric in primaries(cohort):
                                r = ctx.family(label, metric, specs, al, True)
                                if mode != "T":
                                    r["sensitivity_uni_cal"] = ctx.family(f"{label}|uni_cal", metric, specs, al, False, ("uni_cal", "uni_cal"))
                                fams[f"{label}|{LABEL[metric]}"] = {**head, **r}
                            secs[label] = {**head, "endpoints": {LABEL[m]: ctx.family(f"{label}|sec", m, specs, al, False, keep_pairing=False)
                                                                 for m in secondaries(cohort, obj)}}
    return fams, secs


def _access(ctx, versions):
    out = {}
    for version in versions:
        for cohort, modes in ACCESS.items():
            for mode in modes:
                for obj in OBJECTIVES:
                    specs = [(slot, cfg(cohort, obj, "A", slot, BREADTH_SEED, version), cfg(cohort, obj, mode, slot, BREADTH_SEED, version))
                             for slot in ACCESS_SLOTS]
                    if version != PRIMARY_VERSION and not any(rc in ctx.index or cc in ctx.index for _, rc, cc in specs):
                        continue
                    label = f"ACCESS|{cohort}|{obj}|A->{mode}|s{BREADTH_SEED}" + _vsuffix(version)
                    out[f"{label}|R"] = {"family": "ACCESS", "block": "access", "cohort": cohort, "objective": obj, "mode": f"A->{mode}",
                                         "version": version, "seed_label": _seed_label(BREADTH_SEED),
                                         "declared_variable": "input-access mode (descriptive)", "allowed_differences": ["mode"],
                                         **ctx.family(label, PRIMARY, specs, ("mode",), False)}
    return out


def _selection(ctx):
    target = {}
    for c in sorted(ctx.index, key=ckey):
        cohort, obj, mode, slot, d, t, version = c
        if mode != "T" or slot == REFERENCE_SLOT:
            continue
        st = Counter(u["view_status"].get("gainsel", "absent") if u["status"] == "complete" else "unit not complete"
                     for u in ctx.index[c].values())
        label = f"SELECTION|{cohort}|{obj}|T|{slot}|d{_s(d)}t{_s(t)}" + _vsuffix(version)
        entry = {"family": "SELECTION", "configuration": ckey(c), "cohort": cohort, "objective": obj, "slot": slot, "version": version,
                 "seed_label": _seed_label(t), "gainsel_status": dict(sorted(st.items())), "endpoints": {}}
        for metric in primaries(cohort):
            entry["endpoints"][LABEL[metric]] = ctx.family(label, metric, [("risk->gain", c, c)], (), False, ("primary", "gainsel"))
        target[label] = entry
    groups, bridges = [], []
    for u in ctx.units:
        base = {"eid": u["eid"], "family_id": u["family_id"], "block": u["block"], "cohort": u["cohort"], "objective": u["objective"],
                "donor_seed": u["donor_seed"], "version": u["version"], "status": u["status"], "values": u["extra"] or {}}
        if u["stage"] == "donor_group":
            dt = u["donor"] or {}
            groups.append({**base, "compute_limit": u["compute_limit"], "members": dt.get("members") or {},
                           "member_error": dt.get("member_error"), "horizon_ep_eq": dt.get("horizon_ep_eq"),
                           "ceiling_reached_while_improving": dt.get("ceiling_reached_while_improving"), "lambda": dt.get("lambda")})
        elif u["stage"] == "bridge":
            bridges.append({**base, "donor_group": u["donor_group"], "slot": u["slot"], "member_resolved": u["member_resolved"],
                            "member_check": u["member_check"], "fields": u["bridge_info"] or {}})
    return {"target_side": target, "donor_groups": groups, "bridges": bridges}


def _joint(ctx):
    """J* resolution per donor group (the lambda rule recomputed by select, the recorded choices) and the member check of
    every downstream unit (module docstring)."""
    groups = {}
    for u in ctx.units:
        if u["stage"] == "donor_group" and (u["donor"] or {}).get("lambda") is not None:
            groups[u["eid"]] = {"cohort": u["cohort"], "objective": u["objective"], "donor_seed": u["donor_seed"], "block": u["block"],
                                "version": u["version"], "status": u["status"], "lambda": u["donor"]["lambda"],
                                "downstream": defaultdict(Counter), "members_used": Counter()}
    checks, failures = Counter(), []
    for u in ctx.units:
        if u["status"] != "complete" or u["member_check"] is None:
            continue
        checks[u["member_check"]] += 1
        if u["member_check"] in MEMBER_EXCLUDE:
            failures.append({"eid": u["eid"], "stage": u["stage"], "configuration": ckey(config_of(u)) if u["stage"] in EVAL_STAGES else None,
                             "cell": [u["subject_fold"], u["content_fold"]], "donor_group": u["donor_group"], "slot": u["slot"],
                             "status": u["member_check"], "detail": u["member_check_detail"]})
        if u["slot"] == SEL.JOINT:
            g = groups.setdefault(u["donor_group"], {"cohort": u["cohort"], "objective": u["objective"], "donor_seed": u["donor_seed"],
                                                     "block": None, "version": u["version"], "status": "not a complete donor-group unit",
                                                     "lambda": None, "downstream": defaultdict(Counter), "members_used": Counter()})
            g["downstream"][u["stage"]][u["member_check"]] += 1
            g["members_used"][u["member_resolved"] or "unknown"] += 1
    out = {gid: {**g, "downstream": {k: dict(sorted(v.items())) for k, v in sorted(g["downstream"].items())},
                 "members_used": dict(sorted(g["members_used"].items()))} for gid, g in sorted(groups.items(), key=lambda kv: str(kv[0]))}
    for gid, g in out.items():
        lam = g["lambda"] or {}
        if lam.get("check") == "disagrees":
            ctx.notes.append(f"donor group {gid}: recorded joint choice {lam.get('recorded_primary')} differs from the lambda rule "
                             f"recomputed by select ({lam.get('choice')}); downstream units are checked against the rule")
        if len([m for m in g["members_used"] if m in SEL.JOINT_CANDIDATES]) > 1:
            ctx.notes.append(f"donor group {gid}: its J* units used more than one member {g['members_used']}")
    return {"groups": out, "checks": dict(sorted(checks.items())), "failures": failures}


def _levels(ctx):
    out = {}
    iv = identity_values(ctx.units, ctx.manifest, "primary", _ctx=ctx)
    for c, d in iv.items():
        ids, prim = d["identities"], primaries(c[0])
        r = {"cohort": c[0], "objective": c[1], "mode": c[2], "slot": c[3], "donor_seed": c[4], "target_seed": c[5], "version": c[6],
             "n": len(ids), "endpoints": {}}
        for m in prim + secondaries(c[0], c[1]):
            have = [i for i in ids if m in ids[i]["values"]]
            if not have:
                continue
            y = [ids[i]["values"][m] for i in have]
            e = {"n": len(have), **_summ(y, S.draws(len(y), S.NB, S.group_seed("levels", ckey(c), m)) if len(y) >= 3 else None)[0]}
            if m in prim:
                gs = defaultdict(list)
                for i in have:
                    gs[str(ids[i]["group"])].append(ids[i]["values"][m])
                e["groups"] = {}
                for g in sorted(gs):
                    x = gs[g]
                    e["groups"][g] = ({"n": len(x), **_summ(x, S.draws(len(x), S.NB, S.group_seed("levels", ckey(c), m, g)))[0]}
                                      if len(x) >= MIN_N else {"n": len(x)})
            r["endpoints"][LABEL[m]] = e
        out[ckey(c)] = r
    return out


def _seed_stats(ests):
    e = [x for x in ests if x is not None]
    return {"mean": float(np.mean(e)) if e else None, "range": [float(min(e)), float(max(e))] if e else None,
            "sd": float(np.std(e, ddof=1)) if len(e) >= 2 else None, "n_seeds_with_estimate": len(e)}


def _three_seed(per_seed):
    """per_seed {seed: {identity: within-seed difference}} -> ({identity: mean over seeds} or None, status)."""
    have = [s for s in ALL_SEEDS if per_seed.get(s)]
    if len(have) < len(ALL_SEEDS):
        return None, {"three_seed_status": f"incomplete common seed set: available {have}, missing "
                                            f"{[s for s in ALL_SEEDS if s not in have]}"}
    ids = set.intersection(*(set(per_seed[s]) for s in ALL_SEEDS))
    union = set.union(*(set(per_seed[s]) for s in ALL_SEEDS))
    return ({i: float(np.mean([per_seed[s][i] for s in ALL_SEEDS])) for i in sorted(ids)},
            {"three_seed_status": "complete common seed set", "identities_without_all_seeds": len(union - ids)})


def _panel(ctx, fams, versions):
    """PANEL (private_bdf, mode T), per execution version: per-seed families (computed with the others), the three-seed
    identity means (ADDENDUM_11: per-seed estimates, mean, range, SD; max-t on the seed-mean identity values) and the E_LOCAL
    native reference (pointwise)."""
    three, native, native3 = {}, {}, {}
    for version in versions:
        if version != PRIMARY_VERSION and not any(c[0] == PRIVATE and c[2] == "T" and c[6] == version for c in ctx.index):
            continue
        vs = _vsuffix(version)
        for fam in PANEL_FAMILIES:
            names = [f"{r}->{c}" for r, c in FAMILY_MEMBERS[fam]]
            for obj in OBJECTIVES:
                for metric in PRIV_PRIMARY:
                    rows, Y3 = {}, {}
                    for n in names:
                        ests, per_seed = {}, {}
                        for seed in ALL_SEEDS:
                            lab = family_label(fam, PRIVATE, obj, "T", seed, version)
                            ests[seed] = fams.get(f"{lab}|{LABEL[metric]}", {}).get("members", {}).get(n, {}).get("est")
                            per_seed[seed] = {i: v["diff"] for i, v in ctx.diffs.get(f"{lab}|{metric}", {}).get(n, {}).items()}
                        y3, st = _three_seed(per_seed)
                        rows[n] = {"per_seed": {str(s): ests[s] for s in ALL_SEEDS}, **_seed_stats(list(ests.values())), **st}
                        if y3:
                            Y3[n] = y3
                    label = f"PANEL3|{fam}|{PRIVATE}|{obj}|T{vs}"
                    res = family_stats(label, metric, Y3, True, names)
                    ctx.diffs[f"{label}|{metric}"] = {n: {i: {"diff": d} for i, d in y.items()} for n, y in Y3.items()}
                    for n in names:
                        rows[n]["three_seed"] = res["members"][n] if Y3.get(n) else {"note": "not computed (incomplete common seed set)"}
                    three[f"{label}|{metric}"] = {"family": fam, "objective": obj, "mode": "T", "endpoint": LABEL[metric],
                                                  "direction_text": DIR_TEXT[DIRECTION[metric]], "label": label, "version": version,
                                                  "maxt": res["maxt"], "members": rows}
        slots = PANEL_SLOTS if version == PRIMARY_VERSION else tuple(s for s in PANEL_SLOTS if s != SEL.SCRATCH)
        for obj in OBJECTIVES:
            for metric in PRIV_PRIMARY:
                per = defaultdict(dict)
                for seed in ALL_SEEDS:
                    ref = cfg(PRIVATE, obj, "T", REFERENCE_SLOT, seed)
                    specs = [(f"E_LOCAL->{slot}", ref, cfg(PRIVATE, obj, "T", slot, seed, version)) for slot in slots]
                    label = f"NATIVE_REF|{PRIVATE}|{obj}|T|s{seed}{vs}"
                    native[f"{label}|{metric}"] = {"family": "NATIVE_REF", "objective": obj, "seed_label": _seed_label(seed),
                                                   "version": version, "declared_variable": "different input contract (descriptive reference)",
                                                   **ctx.family(label, metric, specs, REF_ALLOW, False)}
                    for n, _, _ in specs:
                        per[n][seed] = {i: v["diff"] for i, v in ctx.diffs[f"{label}|{metric}"][n].items()}
                Y3, st3 = {}, {}
                for n, ps in per.items():
                    y3, st3[n] = _three_seed(ps)
                    if y3:
                        Y3[n] = y3
                label = f"NATIVE_REF3|{PRIVATE}|{obj}|T{vs}"
                res = family_stats(label, metric, Y3, False, list(per))
                native3[f"{label}|{metric}"] = {"family": "NATIVE_REF3", "objective": obj, "endpoint": LABEL[metric], "version": version,
                                                "members": {n: {**st3[n], **(res["members"][n] if Y3.get(n) else {})} for n in per}}
    return {"three_seed": three, "native_reference": native, "native_reference_three_seed": native3}


def _coverage(ctx):
    texts = sorted({u["selection_level"] for u in ctx.units if u["status"] == "complete" and u["selection_level"]})
    codes = {t: f"L{i + 1}" for i, t in enumerate(texts)}
    legend = {t: {"code": codes[t], "text": t, "units": 0, "stages": Counter(), "status": Counter()} for t in texts}
    table = defaultdict(lambda: {"counts": Counter(), "levels": Counter(), "level_status": Counter(), "views": defaultdict(Counter)})
    not_complete = []
    for u in ctx.units:
        k = (u["stage"], u["block"] or "-", u["cohort"] or "-", u["objective"] or "-", u["mode"] or "-", u["slot"] or "-",
             _s(u["donor_seed"]), _s(u["target_seed"]), u["version"])
        t, st = table[k], u["status"]
        t["counts"]["registered"] += 1
        t["counts"][st if st in ("complete", "technical_failed", "missing") else "other"] += 1
        if st != "complete":
            not_complete.append({"eid": u["eid"], "stage": u["stage"], "block": u["block"], "cohort": u["cohort"], "objective": u["objective"],
                                 "mode": u["mode"], "slot": u["slot"], "version": u["version"], "cell": [u["subject_fold"], u["content_fold"]],
                                 "status": st})
            continue
        t["counts"]["excluded"] += u["eid"] in ctx.excluded
        lv = u["selection_level"]
        t["levels"][codes.get(lv, "none")] += 1
        t["level_status"][u["level_status"]] += 1
        if lv:
            legend[lv]["units"] += 1
            legend[lv]["stages"][u["stage"]] += 1
            legend[lv]["status"][u["level_status"]] += 1
        for view, vs in u["view_status"].items():
            t["views"][view][vs] += 1
    fields = ("stage", "block", "cohort", "objective", "mode", "slot", "donor_seed", "target_seed", "version")
    cnt = ("registered", "complete", "technical_failed", "missing", "other", "excluded")
    rows = [{**dict(zip(fields, k)), **{x: table[k]["counts"][x] for x in cnt},
             "selection_levels": dict(sorted(table[k]["levels"].items())),
             "selection_level_status": dict(sorted(table[k]["level_status"].items())),
             "sensitivity_views": {v: dict(sorted(c.items())) for v, c in sorted(table[k]["views"].items())}}
            for k in sorted(table, key=lambda k: tuple(map(str, k)))]
    reg = Counter((u["block"], u["stage"]) for u in ctx.units if u["version"] == PRIMARY_VERSION and u["stage"] != "reference")
    design = [{"block": b, "stage": s, "registered": reg.get((b, s), 0), "design": n, "design_is_maximum": (b, s) in DESIGN_ROWS_MAX}
              for (b, s), n in DESIGN_ROWS.items()]
    design += [{"block": b, "stage": s, "registered": n, "design": None, "design_is_maximum": False}
               for (b, s), n in sorted(reg.items(), key=lambda kv: tuple(map(str, kv[0]))) if (b, s) not in DESIGN_ROWS]
    iv = identity_values(ctx.units, ctx.manifest, "primary", _ctx=ctx)
    idents, ph_ent, ph_rec, th = {}, defaultdict(set), Counter(), Counter()
    for c, d in iv.items():
        ids = d["identities"]
        idents[ckey(c)] = {"n": len(ids), "groups": dict(sorted(Counter(str(x["group"]) for x in ids.values()).items())),
                           "expected": EXPECTED_IDENTITIES.get(c[0]), "units": d["info"]["units"],
                           "units_excluded": d["info"]["units_excluded"],
                           "units_per_identity": {str(k): v for k, v in sorted(Counter(x["n_units"] for x in ids.values()).items())}}
        ph_ent[c[0]] |= d["info"]["phantom_entities"]
        ph_rec[c[0]] += d["info"]["phantom_records"]
        th[c[0]] += d["info"]["always_train_th"]
    nonfinite = [{"eid": eid, "view": view, "endpoint": m, "count": n} for (eid, view), info in sorted(ctx.unit_info.items())
                 for m, n in sorted(info["nonfinite"].items())]
    unit_notes = [{"eid": u["eid"], "note": n} for u in ctx.units for n in u["notes"]]
    return {"by_configuration": rows, "not_complete": not_complete, "design_rows": design, "identities": idents,
            "expected_identities": EXPECTED_IDENTITIES,
            "selection_levels": [{**v, "stages": dict(sorted(v["stages"].items())), "status": dict(sorted(v["status"].items()))}
                                 for v in legend.values()],
            "selection_levels_declared": {k: v[0] for k, v in SELECTION_LEVEL.items()},
            "phantom": {"entities_excluded": {k: len(v) for k, v in ph_ent.items()}, "record_evaluations_excluded": dict(ph_rec)},
            "fau_always_train_th_in_test": dict(th), "nonfinite_excluded": nonfinite, "unit_notes": unit_notes}


def _pairing_lists(*groups):
    """Cell pairs excluded / missing / unregistered, over the families (incl. their B_uni_cal sensitivity), access and the
    native reference; one entry per (family label, member, cell)."""
    out, seen = {"excluded": [], "missing": [], "unregistered": []}, set()

    def add(f, view):
        for name, m in f.get("members", {}).items():
            p = m.get("pairing") or {}
            for kind, key in (("excluded", "cells_excluded"), ("missing", "cells_missing"), ("unregistered", "cells_unregistered")):
                lst = p.get(key)
                for e in lst if isinstance(lst, list) else ():
                    k = (kind, f["label"], name, tuple(e["cell"]))
                    if k not in seen:
                        seen.add(k)
                        out[kind].append({"family": f["label"], "member": name, "view": view, **e})
    for entries in groups:
        for f in entries.values():
            add(f, "primary")
            if f.get("sensitivity_uni_cal"):
                add(f["sensitivity_uni_cal"], "uni_cal")
    return out


def privacy_scan(texts, child_ids):
    """Names of the texts that contain a private child id or the child-id pattern."""
    ids = sorted({str(c) for c in child_ids if c})
    pat = re.compile(r"(?<![A-Za-z0-9_])(?:" + "|".join(map(re.escape, ids)) + r")(?![A-Za-z0-9_])") if ids else None
    return [name for name, txt in texts.items() if CHILD_PATTERN.search(txt) or (pat is not None and pat.search(txt))]


def _jl(x):
    """JSON-ready copy: numpy scalars -> python, non-finite floats -> None, sets sorted, bootstrap replicate arrays dropped
    (the 'T' arrays of sci_r1.stats summaries; a 'T' key holding anything else, e.g. the declared mode T, is kept)."""
    if isinstance(x, dict):
        return {str(k): _jl(v) for k, v in x.items() if not (k == "T" and isinstance(v, np.ndarray))}
    if isinstance(x, (list, tuple)):
        return [_jl(v) for v in x]
    if isinstance(x, (set, frozenset)):
        return sorted(_jl(v) for v in x)
    if isinstance(x, np.ndarray):
        return _jl(x.tolist())
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, (float, np.floating)):
        return float(x) if math.isfinite(float(x)) else None
    return x


def _write_text(path, text, private=False):
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, mode=0o700 if private else 0o777, exist_ok=True)
    if private:
        os.chmod(d, 0o700)
    tmp = path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600 if private else 0o644)
    with os.fdopen(fd, "w") as f:
        f.write(text)
    os.replace(tmp, path)
    if private:
        os.chmod(path, 0o600)


# ------------------------------------------------------------------------------------------------ entry point
def run_families(units, manifest=None, out_json=None, out_md=None, out_private=None, meta=None):
    """The frozen §5 analysis on normalised units (load_records). Returns the public aggregate (also written to `out_json`, and
    rendered to `out_md`); per-identity values and paired differences go to `out_private` only (0600 in a 0700 directory).
    Public outputs are privacy-scanned before they are written; a hit writes no public file and raises ValueError."""
    if S.NB != 4000:
        raise RuntimeError(f"sci_r1.stats.NB = {S.NB}; the frozen analysis uses B = 4,000")
    units = list(units)
    ctx = _Ctx(units, manifest)
    versions = _versions_order(units)
    fams, secs = _families(ctx, versions)
    access, panel = _access(ctx, versions), _panel(ctx, fams, versions)
    selection, joint = _selection(ctx), _joint(ctx)
    levels, coverage = _levels(ctx), _coverage(ctx)
    pl = _pairing_lists(fams, access, panel["native_reference"])
    excluded = [{"eid": u["eid"], "stage": u["stage"], "configuration": ckey(config_of(u)), "cell": [u["subject_fold"], u["content_fold"]],
                 "reason": ctx.excluded[u["eid"]]} for u in units if u["eid"] in ctx.excluded]
    m = {"design": DESIGN, "card": CARD, "logical_family": LOGICAL_FAMILY, "execution_contract": C.CONTRACT,
         "code_sha256": code_sha256(), "n_boot": int(S.NB), "stats_seed_base": int(S.SEED), "bootstrap_scope": BOOTSTRAP_SCOPE,
         "bootstrap": "bootstrap-t over identities with per-replicate studentisation (sci_r1.stats); pointwise on each member's own "
                      "paired identities; family simultaneous 95 % intervals by max-t over the members with pairs, on their common "
                      "identities, sharing the replicate indices, seeded by group_seed(family label, endpoint)",
         "primary_endpoints": {"continuous": PRIMARY, PRIVATE: list(PRIV_PRIMARY)},
         "directions": {LABEL[k]: DIR_TEXT[v] for k, v in DIRECTION.items()},
         "statements": list(STATEMENTS), "families_declared": [{"family": f[0], "modes": {k: list(v) for k, v in f[1].items()},
                                                                "members": [f"{r}->{c}" for r, c in f[2]], "declared_variable": f[3],
                                                                "allowed_differences": list(f[4])} for f in FAMILIES],
         "access_declared": {k: list(v) for k, v in ACCESS.items()},
         "manifest_sha256_seen": sorted({u["manifest_sha256"] for u in units if u.get("manifest_sha256")}),
         "versions_order": versions, "versions": _versions_info(units, versions),
         "n_units": len(units), "n_complete": sum(u["status"] == "complete" for u in units), "n_excluded": len(excluded),
         "generated": time.strftime("%Y-%m-%d %H:%M %Z"), "slurm_job": os.environ.get("SLURM_JOB_ID", "local"),
         "dry_run": False, "privacy_scan": "not run", **(meta or {})}
    out = {"meta": m, "coverage": coverage,
           "pairing": {"cell_pairs_excluded": pl["excluded"], "cell_pairs_missing": pl["missing"],
                       "cell_pairs_unregistered": pl["unregistered"], "pool_check": ctx.pool, "member_check": joint["checks"],
                       "member_check_failures": joint["failures"], "units_excluded": excluded},
           "families": fams, "secondary": secs, "access": access, "selection": selection, "panel": panel,
           "joint_resolution": joint["groups"], "levels": levels, "notes": list(ctx.notes)}
    child_ids = {p for u in units if u["cohort"] == PRIVATE for v in u["views"].values() for p in v["rows"]}
    if out_private:
        private = {"meta": {k: m[k] for k in ("design", "card", "code_sha256", "generated", "dry_run")},
                   "identity_values": {view: {ckey(c): d["identities"] for c, d in identity_values(units, manifest, view, _ctx=ctx).items()}
                                       for view in ("primary", "gainsel", "uni_cal")},
                   "paired_differences": ctx.diffs}
        _write_text(out_private, json.dumps(_jl(private), indent=1, allow_nan=False), private=True)
    m["privacy_scan"] = "PASS (no private child id and no child-id pattern in the public outputs)"
    js, md = json.dumps(_jl(out), indent=1, allow_nan=False), render_markdown(out)
    bad = privacy_scan({"json": js, "markdown": md}, child_ids)
    if bad:
        raise ValueError(f"privacy scan failed for {bad}: no public output written")
    if out_json:
        _write_text(out_json, js)
    if out_md:
        _write_text(out_md, md)
    return out


# ------------------------------------------------------------------------------------------------ Markdown
def _f(x, signed=True):
    if x is None:
        return "–"
    if isinstance(x, bool):
        return str(x).lower()
    if isinstance(x, (int, float)):
        return (f"{x:+.3f}" if signed else f"{x:.3f}") if math.isfinite(x) else str(x)
    return str(x)


def _g(x):
    """A count or a position (steps, ep-eq): integers without decimals."""
    if x is None:
        return "–"
    if isinstance(x, bool):
        return str(x).lower()
    if isinstance(x, (int, float)) and math.isfinite(x):
        return str(int(x)) if float(x).is_integer() else f"{x:g}"
    return str(x)


NOT_REGISTERED = "not registered (reference 0 units, candidate 0 units)"


def _nothing_registered(f):
    """A declared family (or ACCESS / reference entry) none of whose members has a plan row on either side."""
    return all(m.get("status") == NOT_REGISTERED for m in f["members"].values())


def _iv(r, lo, hi, signed=True):
    if not r or r.get(lo) is None or r.get(hi) is None:
        return "–"
    return f"[{_f(r[lo], signed)}, {_f(r[hi], signed)}]"


def _bt(r, signed=True):
    return "–" if not r or r.get("est") is None else f"{_f(r['est'], signed)} {_iv(r, 'ci_low', 'ci_high', signed)}"


def _pc(r, signed=True):
    return _iv(r, "pct_low", "pct_high", signed)


def _simtxt(m):
    fs = m.get("family_set")
    if not fs:
        return m.get("family_note") or "–"
    return f"{_f(fs.get('est'))} {_iv(fs, 'sim_low', 'sim_high')} {fs.get('sim_position', '')}".rstrip()


def _cnt(x):
    return x if isinstance(x, int) else len(x or ())


def _cov(m):
    p = m.get("pairing") or {}
    t = f"{p.get('cells_matched', 0)} cell pairs, {m.get('n_paired', 0)} identities paired"
    for key, word in (("cells_missing", "missing"), ("cells_excluded", "excluded"), ("cells_unregistered", "unregistered")):
        if _cnt(p.get(key)):
            t += f", {_cnt(p.get(key))} cells {word}"
    if p.get("identities_partial"):
        t += f", {p['identities_partial']} on part of their units"
    if p.get("identities_unpaired"):
        t += f", {p['identities_unpaired']} unpaired"
    for k in ("note", "status"):
        if m.get(k):
            t += f"; {m[k]}"
    return t


def _arrow(name):
    return name.replace("->", " → ")


def _cfgtxt(k):
    return k.replace("|", " · ")


def _family_table(entries, with_sens):
    head = ("| family · objective · mode | reference → candidate | n | Δ [95 % bootstrap-t] | [95 % percentile] | family n | "
            "Δ on the family set [95 % simultaneous] |" + (" B_uni_cal Δ [95 % bootstrap-t] (n) |" if with_sens else "") + " coverage |")
    L = [head, "|" + "---|" * (head.count("|") - 1)]
    for f in entries:
        mx = f.get("maxt") or {}
        for name, m in f["members"].items():
            sens = ""
            if with_sens:
                s = (f.get("sensitivity_uni_cal") or {}).get("members", {}).get(name)
                sens = (" – |" if s is None else f" {_bt(s)} (n {s.get('n', 0)}) |" if s.get("est") is not None
                        else f" {s.get('status') or s.get('note') or '–'} |")
            fn = (m.get("family_set") or {}).get("n", mx.get("n", "–"))
            L.append(f"| {f['family']} · {f['objective']} · {f['mode']} | {_arrow(name)} | {m.get('n', 0)} | {_bt(m)} | {_pc(m)} | {fn} | "
                     f"{_simtxt(m)} |{sens} {_cov(m)} |")
    return L


def _maxt_lines(entries, prefix=""):
    out = []
    for f in entries:
        mx = f.get("maxt")
        if not mx:
            continue
        t = (f"- {prefix}{f['family']} · {f['objective']} · {f['mode']} ({f['endpoint']}, {f['direction_text']}): simultaneous over "
             f"{mx['n_members']} of {mx['n_declared']} declared members")
        if mx["members"]:
            t += " (" + ", ".join(map(_arrow, mx["members"])) + ")"
        t += f", family n = {mx['n']}" + (f", crit {mx['crit']:.2f}" if mx.get("crit") is not None else "")
        t += f"; {mx['note']}" if mx.get("note") else ""
        out.append(t + ".")
    return out + ([""] if out else [])


def _level_line(cov, entries):
    """One line per table: the selection levels recorded by the complete units of exactly the configurations the table's
    members pair (codes in §1), per mode (E_LOCAL: the ALN3 reference rows, which declare no level)."""
    keys = {m[k] for f in entries for m in f["members"].values() for k in ("reference", "candidate") if m.get(k)}
    lv, st = defaultdict(Counter), defaultdict(Counter)
    for r in cov["by_configuration"]:
        k = f"{r['cohort']}|{r['objective']}|{r['mode']}|{r['slot']}|d{r['donor_seed']}|t{r['target_seed']}|{r['version']}"
        if r["stage"] in EVAL_STAGES and k in keys:
            md = REFERENCE_SLOT if r["slot"] == REFERENCE_SLOT else f"mode {r['mode']}"
            lv[md].update(r["selection_levels"])
            st[md].update(r["selection_level_status"])
    order = [f"mode {x}" for x in ("T",) + ZS_MODES] + [REFERENCE_SLOT]
    parts = [f"{md}: " + ", ".join(f"{k} ×{n}" for k, n in sorted(lv[md].items())) + " (" +
             ", ".join(f"{k} {n}" for k, n in sorted(st[md].items())) + ")" for md in order if lv[md]]
    return "Selection levels (unit records; codes in §1): " + ("; ".join(parts) or "no complete unit") + "."


def _md_coverage(cov):
    cnt = ("registered", "complete", "technical_failed", "missing", "other", "excluded")
    agg = defaultdict(Counter)
    for r in cov["by_configuration"]:
        for x in cnt:
            agg[(r["stage"], r["block"], r["cohort"], r["version"])][x] += r[x]
    L = ["## 1. Coverage", "", "| stage | block | cohort | version | " + " | ".join(cnt) + " |", "|---|---|---|---|" + "---|" * len(cnt)]
    for k in sorted(agg, key=lambda k: tuple(map(str, k))):
        L.append(f"| {k[0]} | {k[1]} | {k[2]} | {k[3]} | " + " | ".join(str(agg[k][x]) for x in cnt) + " |")
    L += ["", "Registered rows of the primary version against the §4.1 design counts (access: a maximum, mode-C rows only "
          "where the manifest supports them):", "", "| block | stage | registered | design |", "|---|---|---|---|"]
    for r in cov["design_rows"]:
        d = "–" if r["design"] is None else (f"≤ {r['design']}" if r["design_is_maximum"] else str(r["design"]))
        L.append(f"| {r['block']} | {r['stage']} | {r['registered']} | {d} |")
    per_cohort = defaultdict(list)
    for k, r in cov["identities"].items():
        per_cohort[k.split("|")[0]].append(r["n"])
    L += ["", f"Units not complete: {len(cov['not_complete'])} (each listed in the JSON, `coverage.not_complete`). Identities per "
          "configuration (primary evaluation; appendix B), against the §5.2 test identities: " + ("; ".join(
              f"{c} {min(v)}–{max(v)} of {sum((EXPECTED_IDENTITIES.get(c) or {}).values()) or '?'}" for c, v in sorted(per_cohort.items())) or "none") + ".",
          "", "Phantom entities excluded from every summary: " + (", ".join(
              f"{c} {n} (record evaluations {cov['phantom']['record_evaluations_excluded'].get(c, 0)})"
              for c, n in cov["phantom"]["entities_excluded"].items() if n) or "none") + ". FAU always-train TH ids found among test "
          f"participants (excluded): {cov['fau_always_train_th_in_test'].get('fau', 0)}. Non-finite values excluded: "
          f"{sum(x['count'] for x in cov['nonfinite_excluded'])} (listed in the JSON, `coverage.nonfinite_excluded`).", "",
          "Selection levels declared (§1 item 8, §2.10, §2.12): " + "; ".join(f"{k}: '{v}'" for k, v in cov["selection_levels_declared"].items())
          + ". Recorded by the complete units:", ""]
    L += [f"- {x['code']} = '{x['text']}': {x['units']} units (" + ", ".join(f"{a} {b}" for a, b in x["stages"].items()) + "; "
          + ", ".join(f"{a} {b}" for a, b in x["status"].items()) + ")" for x in cov["selection_levels"]] or ["- none"]
    miss = Counter()
    views = defaultdict(Counter)
    for r in cov["by_configuration"]:
        miss.update(r["selection_level_status"])
        for v, c in r["sensitivity_views"].items():
            views[v].update(c)
    L += ["", "Selection-level status of the complete units: " + (", ".join(f"{k} {n}" for k, n in sorted(miss.items())) or "none")
          + ". Sensitivity evaluations: " + ("; ".join(f"{v} " + ", ".join(f"{k} {n}" for k, n in sorted(c.items()))
                                                        for v, c in sorted(views.items())) or "none") + " (per configuration in appendix A).", ""]
    return L


def _md_checks(out):
    P, q = out["pairing"], out["pairing"]["pool_check"]
    uc = sum(1 for e in P["cell_pairs_missing"] if e["view"] == "uni_cal")
    L = ["## 2. Engineering checks of the analysis (§5.8)", "",
         f"- Cell pairs excluded (pairing-key mismatch or an excluded unit): {len(P['cell_pairs_excluded'])}; with a missing or "
         f"incomplete side (a plan row without a complete record or evaluation): {len(P['cell_pairs_missing'])}, of which {uc} lack "
         f"the B_uni_cal sensitivity evaluation; with an unregistered side (no plan row): {len(P['cell_pairs_unregistered'])}. "
         "All three lists are in the JSON (`pairing`).",
         f"- Pools (§2.13; reference: {q['reference']}): {q['cells_checked']} cells checked, {q['cells_with_t_and_zero_shot']} with "
         f"mode-T and zero-shot units; zero-shot units verified {q['zero_shot_units_verified']} of {q['zero_shot_units_checked']}, "
         f"excluded {len(q['zero_shot_units_excluded'])}, unverified (no complete mode-T unit in the cell) "
         f"{len(q['zero_shot_units_unverified'])}; cells whose mode-T units disagree: {len(q['cells_t_disagree'])}.",
         "- Members (select.member_of; J* by the λ rule on the donor-group record): " + (", ".join(
             f"{k} {n}" for k, n in P["member_check"].items()) or "no slot unit") + ".",
         f"- Units excluded from every family and summary: {len(P['units_excluded'])}.", ""]
    for d in q["cells_t_disagree"]:
        L.append(f"  - mode-T units disagree: {d['cohort']} cell {d['cell']} ({', '.join(d['differs_in'])}): " + "; ".join(
            f"{len(g['configurations'])} configurations with {g['n_participants']} participants, n_test_candidates "
            f"{g['n_test_candidates']}" for g in d["groups"]))
    for e in P["units_excluded"]:
        L.append(f"  - unit excluded: {e['eid']} ({_cfgtxt(e['configuration'])}, cell {e['cell']}): {e['reason']}")
    for e in q["zero_shot_units_unverified"]:
        L.append(f"  - zero-shot unit unverified: {e['eid']} ({_cfgtxt(e['configuration'])}, cell {e['cell']}): {e['reason']}")
    for e in P["cell_pairs_excluded"]:
        L.append(f"  - cell pair excluded: {e['family']} · {_arrow(e['member'])} · cell {e['cell']}: {e['reason']}")
    return L + [""]


def _version_heads(versions, F, pred):
    """Versions with at least one family entry matching `pred` (primary always)."""
    return [v for v in versions if v == PRIMARY_VERSION or any(f["version"] == v and pred(f) for f in F.values())]


def _unregistered_line(entries):
    return ("Declared, nothing registered on either side (listed in the JSON): "
            + ", ".join(f"{f['family']} · {f['objective']} · {f['mode']}" for f in entries) + ".")


def _private_tables(L, out, v, title, fams, seed, h, empty):
    """The private (mode T) family tables of one version and seed: one table per co-primary endpoint (NLL, AUC). Families
    with nothing registered are collapsed into one line; a seed with nothing registered at all goes to `empty`."""
    shown = []
    for metric in PRIV_PRIMARY:
        ent = [f for f in out["families"].values() if f["version"] == v and f["family"] in fams and f["cohort"] == PRIVATE
               and f["seed_context"] == seed and f["endpoint"] == metric]
        live = [f for f in ent if not _nothing_registered(f)]
        if live:
            shown += live
            gone = [f for f in ent if _nothing_registered(f)]
            L += [f"{h} {title} · {PRIVATE} (mode T, {_seed_label(seed)}) · Δ{metric} ({ent[0]['direction_text']})", ""] \
                + _family_table(live, False) + [""] + _maxt_lines(live) + ([_unregistered_line(gone), ""] if gone else [])
    if not shown and any(f["version"] == v and f["family"] in fams and f["cohort"] == PRIVATE and f["seed_context"] == seed
                         for f in out["families"].values()):
        empty.append(f"{PRIVATE} ({_seed_label(seed)})")
    return shown


def _block_section(L, out, versions, title, fams):
    """Core / rich / CSX tables, per execution version: public cohort × objective tables (mode T and A families), then the
    private tables at seed 3401. Declared families with nothing registered are collapsed into one line."""
    F, cov = out["families"], out["coverage"]
    multi = len(versions) > 1
    for v in _version_heads(versions, F, lambda f: f["family"] in fams):
        h, empty = "###", []
        if multi:
            L += [f"### Execution version `{v}`" + (" (INIT: S from the primary rows)" if v != PRIMARY_VERSION and "INIT" in fams else ""), ""]
            h = "####"
        for cohort in PUBLIC:
            for obj in OBJECTIVES:
                ent = [f for f in F.values() if f["version"] == v and f["family"] in fams and f["cohort"] == cohort
                       and f["objective"] == obj and f["seed_context"] == BREADTH_SEED]
                live = [f for f in ent if not _nothing_registered(f)]
                if not live:
                    if ent:
                        empty.append(f"{cohort} · {obj}")
                    continue
                gone = [f for f in ent if _nothing_registered(f)]
                L += [f"{h} {title} · {cohort} · {obj} · ΔR (bits, ref − cand)", ""] + _family_table(live, True) + [""] \
                    + _maxt_lines(live) + ([_unregistered_line(gone)] if gone else []) + [_level_line(cov, live), ""]
        shown = _private_tables(L, out, v, title, fams, BREADTH_SEED, h, empty)
        if shown:
            L += [_level_line(cov, shown), ""]
        if empty:
            L += [f"Nothing registered for {title} (declared families; every member listed in the JSON): " + "; ".join(empty) + ".", ""]


def render_markdown(out):
    m, cov = out["meta"], out["coverage"]
    versions = m["versions_order"]
    L = [f"# Public auditory prior: E34_PUBLIC_PRIOR results ({m['execution_contract']})", ""]
    if m.get("dry_run"):
        L += ["> **Dry run**: code not frozen in the execution record, scratch inputs (design §5.1). Not an E34_PUBLIC_PRIOR "
              "result.", ""]
    fz = m.get("frozen_check") or {}
    L += [f"Generated {m['generated']} (Slurm {m['slurm_job']}) by `python -m auditory_alignment_v3.prior33.analysis` under "
          f"`PUBLIC_PRIOR_DESIGN.md` §5, frozen with the execution record. Units read: {m['n_units']} ({m['n_complete']} complete; "
          f"{m['n_excluded']} excluded by the engineering checks of §2). Code sha256: "
          + ", ".join(f"`{k}` {(v or 'unreadable')[:12]}" for k, v in m["code_sha256"].items()) + ". Manifest sha256 seen: "
          + (", ".join(f"`{x[:16]}`" for x in m["manifest_sha256_seen"]) or "none") + ". Frozen check: "
          + ("not run" if not fz else ("PASS" if fz.get("ok") else "not frozen (" + "; ".join(fz.get("problems", [])) + ")"))
          + f". Privacy scan: {m['privacy_scan']}.", "",
          "Execution versions (derived from the donor-group rows, §2.10): " + "; ".join(
              f"`{x['version']}` ({x['donor_groups']} donor groups; units " + ", ".join(f"{k} {n}" for k, n in x["units"].items())
              + (f"; compute limits {x['compute_limits']}" if x["compute_limits"] else "")
              + (f"; labels {x['explicit_labels']}" if x["explicit_labels"] else "")
              + (f"; {x['downstream_rows_with_continuation_of']} downstream rows carry their own continuation_of (a label)"
                 if x["downstream_rows_with_continuation_of"] else "") + ")" for x in m["versions"]) + ".", "",
          "**Reading the tables.**", ""] + [f"- {s}" for s in m["statements"]] + [
          "- Endpoint directions (Δ): " + ", ".join(f"{k} {v}" for k, v in m["directions"].items()) + ".", ""]
    L += _md_coverage(cov) + _md_checks(out)
    L += ["## 3. Core block (seed 3401 only)", ""]
    _block_section(L, out, versions, "core", PANEL_FAMILIES)
    # 4 access
    L += ["## 4. Access block (descriptive, pointwise; seed 3401 only)", "",
          "| version | cohort · objective | modes | member | n | ΔR = R(A) − R(mode) [95 % bootstrap-t] | [95 % percentile] | coverage |",
          "|---|---|---|---|---|---|---|---|"]
    gone = []
    for f in out["access"].values():
        if _nothing_registered(f):
            gone.append(f"{f['version']} · {f['cohort']} · {f['objective']} · {_arrow(f['mode'])}")
            continue
        for name, mm in f["members"].items():
            L.append(f"| {f['version']} | {f['cohort']} · {f['objective']} | {_arrow(f['mode'])} | {name} | {mm.get('n', 0)} | {_bt(mm)} | "
                     f"{_pc(mm)} | {_cov(mm)} |")
    L += [""] + ([f"Declared, nothing registered in either mode (listed in the JSON): {'; '.join(gone)}.", ""] if gone else [])
    for v in versions:
        for c in PUBLIC:
            ent = [f for f in out["access"].values() if f["version"] == v and f["cohort"] == c and not _nothing_registered(f)]
            if ent:
                L.append(f"{c} ({v}): {_level_line(cov, ent)}")
    L.append("")
    # 5 panel
    L += _panel_md(out["panel"], out, versions)
    # 6 rich, 7 csx
    for i, (fam, title) in enumerate((("RICH", "Rich block"), ("CSX", "CSX block (competing-talker donor extension)"))):
        L += [f"## {6 + i}. {title} (seed 3401 only)", ""]
        _block_section(L, out, versions, fam, (fam,))
    L += _selection_md(out)
    # 9 secondary
    L += ["## 9. Secondary endpoints (pointwise, on each member's own paired identities)", ""]
    for sec in out["secondary"].values():
        eps = list(sec["endpoints"])
        if not any(r["members"][n].get("est") is not None for r in sec["endpoints"].values() for n in r["members"]):
            continue
        L += [f"**{sec['family']} · {sec['cohort']} · {sec['objective']} · {sec['mode']} · {sec['seed_label']}"
              + ("" if sec["version"] == PRIMARY_VERSION else f" · version {sec['version']}") + "**", "",
              "| member | " + " | ".join(f"{e} ({sec['endpoints'][e]['direction_text']})" for e in eps) + " |", "|---|" + "---|" * len(eps)]
        unreg = []
        for n in FAMILY_MEMBERS[sec["family"]]:
            name = f"{n[0]}->{n[1]}"
            rs = [sec["endpoints"][e]["members"][name] for e in eps]
            if all(r.get("est") is None and str(r.get("status") or "").startswith("not registered") for r in rs):
                unreg.append(f"{_arrow(name)} ({rs[0]['status']})")
                continue
            cells = [f"{_bt(r)} pct {_pc(r)} (n {r.get('n', 0)})" if r.get("est") is not None else (r.get("status") or r.get("note") or "–")
                     for r in rs]
            L.append(f"| {_arrow(name)} | " + " | ".join(cells) + " |")
        L += ([f"Not registered: {'; '.join(unreg)}."] if unreg else []) + [""]
    # 10 levels
    L += ["## 10. Levels (pointwise; per-group levels for groups with n ≥ 5)", "",
          "| configuration | n | primary endpoint: est [95 % bootstrap-t] [95 % percentile] | by group: n, est [95 % bootstrap-t] [95 % percentile] |",
          "|---|---|---|---|"]
    for k, r in out["levels"].items():
        for ep in primaries(r["cohort"]):
            e = r["endpoints"].get(LABEL[ep])
            if not e:
                continue
            g = "; ".join(f"{a}: n {b['n']}" + (f", {_bt(b, False)} {_pc(b, False)}" if b.get("est") is not None else "")
                          for a, b in e["groups"].items())
            L.append(f"| {_cfgtxt(k)} | {e['n']} | {LABEL[ep]} {_bt(e, False)} {_pc(e, False)} | {g} |")
    L.append("")
    notes = out["notes"] + [f"{x['eid']}: {x['note']}" for x in cov["unit_notes"]]
    L += ["## 11. Notes", ""] + ([f"- {n}" for n in notes] or ["- none"]) + [""]
    L += ["## Estimands (design §5.4 and §5.6, fixed before any result)", ""] + [f"- **{a}.** {b}" for a, b in ESTIMANDS] + [""]
    cnt = ("registered", "complete", "technical_failed", "missing", "other", "excluded")
    L += ["## Appendix A. Coverage per configuration", "", "| stage | block | cohort | objective | mode | slot | d / t seed | version | "
          + " | ".join(cnt) + " | selection levels | sensitivity evaluations |", "|---|---|---|---|---|---|---|---|" + "---|" * (len(cnt) + 2)]
    for r in cov["by_configuration"]:
        lv = ", ".join(f"{k} ×{n}" for k, n in r["selection_levels"].items()) + (
            " (" + ", ".join(f"{k} {n}" for k, n in r["selection_level_status"].items()) + ")" if r["selection_level_status"] else "")
        sv = "; ".join(f"{v}: " + ", ".join(f"{k} {n}" for k, n in c.items()) for v, c in r["sensitivity_views"].items())
        L.append(f"| {r['stage']} | {r['block']} | {r['cohort']} | {r['objective']} | {r['mode']} | {r['slot']} | {r['donor_seed']} / "
                 f"{r['target_seed']} | {r['version']} | " + " | ".join(str(r[x]) for x in cnt) + f" | {lv or '–'} | {sv or '–'} |")
    L += ["", "## Appendix B. Identities per configuration (primary evaluation)", "",
          "| configuration | identities | by group | expected (§5.2) | units | units excluded | units per identity |", "|---|---|---|---|---|---|---|"]
    for k, r in cov["identities"].items():
        L.append(f"| {_cfgtxt(k)} | {r['n']} | " + ", ".join(f"{g} {n}" for g, n in r["groups"].items()) + " | "
                 + (", ".join(f"{g} {n}" for g, n in (r["expected"] or {}).items()) or "–") + f" | {r['units']} | {r['units_excluded']} | "
                 + ", ".join(f"{a}: {b}" for a, b in r["units_per_identity"].items()) + " |")
    return "\n".join(L + [""])


def _panel_md(panel, out, versions):
    cov = out["coverage"]
    L = ["## 5. Panel (private_bdf, mode T; seeds 3401, 3407, 3413)", "",
         "Per-seed families are computed like the core families (seed 3401 is the core table). Three-seed: the identity value is "
         "the mean over the three seeds of the within-seed paired difference; a contrast without a complete common seed set lists "
         "the available seeds. The between-seed SD of three estimates is descriptive.", ""]
    multi = len(versions) > 1
    for v in versions:
        if v != PRIMARY_VERSION and not any(e["version"] == v for e in panel["three_seed"].values()):
            continue
        h = "###"
        if multi:
            L += [f"### Execution version `{v}`", ""]
            h = "####"
        ent = [e for e in panel["three_seed"].values() if e["version"] == v]
        none = [e for e in ent if all(r.get("n_seeds_with_estimate", 0) == 0 for r in e["members"].values())]
        ent = [e for e in ent if all(e is not x for x in none)]
        L += [f"{h} Three-seed summary", "",
              "| family · objective | member | endpoint | seed 3401 | seed 3407 | seed 3413 | mean / range / SD | three-seed n | "
              "three-seed Δ [95 % bootstrap-t] | [95 % percentile] | family n | Δ on the family set [95 % simultaneous] |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for e in ent:
            for name, r in e["members"].items():
                t = r.get("three_seed") or {}
                rng = r.get("range")
                fn = (t.get("family_set") or {}).get("n", (e.get("maxt") or {}).get("n", "–"))
                L.append(f"| {e['family']} · {e['objective']} | {_arrow(name)} | {e['endpoint']} | "
                         + " | ".join(_f(r["per_seed"][str(s)]) for s in ALL_SEEDS)
                         + f" | {_f(r.get('mean'))} / " + (f"[{rng[0]:+.3f}, {rng[1]:+.3f}]" if rng else "–") + f" / {_f(r.get('sd'), False)} | "
                         + (f"{t.get('n', 0)} | {_bt(t)} | {_pc(t)} | {fn} | {_simtxt(t)} |" if t.get("est") is not None
                            else f"– | {r.get('three_seed_status', '–')} | – | – | – |"))
        L += [""] + _maxt_lines(ent, "PANEL3 ") + ([
            "No per-seed estimate in any member (listed in the JSON): " + ", ".join(f"{e['family']} · {e['objective']} · {e['endpoint']}"
                                                                           for e in none) + ".", ""] if none else [])
        empty, shown = [], []
        for seed in PANEL_SEEDS:
            shown += _private_tables(L, out, v, "panel", PANEL_FAMILIES, seed, h, empty)
        if empty:
            L += ["Nothing registered for the panel seeds (declared families; every member listed in the JSON): " + "; ".join(empty) + ".", ""]
        L += [f"{h} E_LOCAL native reference", "",
              "Different input contract (250 Hz native, 0.5–45 Hz, ALN3 recipe); descriptive, pointwise; Δ = E_LOCAL → arm in the "
              "positive-is-better convention.", "",
              "| seed | objective | endpoint | member | n | Δ [95 % bootstrap-t] | [95 % percentile] | coverage |", "|---|---|---|---|---|---|---|---|"]
        gone = []
        for e in panel["native_reference"].values():
            if e["version"] != v:
                continue
            if _nothing_registered(e):
                gone.append(f"{e['seed_label']} · {e['objective']} · {e['endpoint']}")
                continue
            for name, mm in e["members"].items():
                L.append(f"| {e['seed_label']} | {e['objective']} | {e['endpoint']} ({e['direction_text']}) | {_arrow(name)} | {mm.get('n', 0)} | "
                         f"{_bt(mm)} | {_pc(mm)} | {_cov(mm)} |")
        L += [""] + ([f"Nothing registered on either side: {'; '.join(gone)}.", ""] if gone else [])
        L += ["| three-seed reference · objective · endpoint | member | status | n | Δ [95 % bootstrap-t] | [95 % percentile] |",
              "|---|---|---|---|---|---|"]
        for e in panel["native_reference_three_seed"].values():
            if e["version"] != v or all(str(mm.get("three_seed_status", "")).startswith("incomplete common seed set: available []")
                                        for mm in e["members"].values()):
                continue
            for name, mm in e["members"].items():
                L.append(f"| {e['objective']} · {e['endpoint']} | {_arrow(name)} | {mm.get('three_seed_status', '–')} | {mm.get('n', 0)} | "
                         f"{_bt(mm)} | {_pc(mm)} |")
        refs = [e for e in panel["native_reference"].values() if e["version"] == v]
        L += ["", _level_line(cov, shown + refs), ""]
    return L


def _selection_md(out):
    sel, J = out["selection"], out["joint_resolution"]
    L = ["## 8. Selection (descriptive, pointwise)", "", "Target side: reference = the risk-selected checkpoint (primary), candidate = "
         "the gain-selected checkpoint, in the positive-is-better convention (positive = the gain-selected checkpoint has lower "
         "risk, or higher AUC). 'identical' = the two rules chose the same epoch (difference exactly 0).", "",
         "| configuration | gain-selected evaluation | endpoint | n | Δ [95 % bootstrap-t] | [95 % percentile] | coverage |",
         "|---|---|---|---|---|---|---|"]
    for e in sel["target_side"].values():
        for ep, r in e["endpoints"].items():
            mm = r["members"]["risk->gain"]
            L.append(f"| {_cfgtxt(e['configuration'])} | " + ", ".join(f"{k} {v}" for k, v in e["gainsel_status"].items())
                     + f" | {ep} ({r['direction_text']}) | {mm.get('n', 0)} | {_bt(mm)} | {_pc(mm)} | {_cov(mm)} |")
    L += ["", f"Donor side ({len(sel['donor_groups'])} donor-group records): per member, the `_best`, `_h30` and `_gainsel` checkpoints "
          "on CE_dev (bits, lower is better), dev gain and the bridge_cal cross-entropy, with their ep-eq positions; '–' = not recorded. "
          "Every recorded selection scalar is also in the JSON (`selection.donor_groups[].values`).", ""]
    for g in sel["donor_groups"]:
        lam = g.get("lambda")
        head = (f"**{g['eid']}** · {g['family_id'].replace(SEL.PREFIX, '')} · {g['cohort']} · {g['objective']} · d{_s(g['donor_seed'])} · "
                f"block {g['block']} · version {g['version']} · {g['status']}")
        if g["status"] != "complete":
            L += [head, ""]
            continue
        L += [head + f" · horizon {_g(g.get('horizon_ep_eq'))} ep-eq · compute limit {_g(g.get('compute_limit'))} · ceiling reached "
              f"while improving: {_g(g.get('ceiling_reached_while_improving'))}" + (f" · members not valid: {g['member_error']}" if g.get("member_error") else ""), "",
              "| member | CE_dev best / h30 / gainsel | gain best / h30 / gainsel | bridge_cal CE best / h30 / gainsel | ep-eq best / h30 / gainsel | steps | non-finite steps |",
              "|---|---|---|---|---|---|---|"]
        for M, r in g["members"].items():
            def trip(q, fmt):
                return " / ".join(fmt(r.get(f"{k}/{q}")) for k in CKPT_KINDS)
            L.append(f"| {M} | {trip('ce_dev', lambda x: _f(x, False))} | {trip('gain', _f)} | {trip('bridge_cal_ce', lambda x: _f(x, False))} | "
                     f"{trip('ep_eq', _g)} | {_g(r.get('steps'))} | {_g(r.get('nonfinite_steps'))} |")
        if lam:
            ce = lam.get("ce_dev") or {}
            L += ["", f"λ (rule {lam['rule']}, recomputed with select): " + (f"CE_dev J1 {_f(ce.get('J1'), False)}, J025 {_f(ce.get('J025'), False)} → "
                  f"{lam['choice']}" if lam.get("choice") else f"not recomputable ({lam.get('error')})") + f"; recorded primary choice "
                  f"{_s(lam.get('recorded_primary'))} ({lam['check']}); recorded gain-rule choice {_s(lam.get('recorded_gain_rule'))} "
                  f"(_gainsel gain J1 {_f(lam['gainsel_gain'].get('J1'))}, J025 {_f(lam['gainsel_gain'].get('J025'))})."]
        L.append("")
    L += [f"Bridges ({len(sel['bridges'])} records; descriptive): ", "",
          "| record | donor group | slot · member | cohort · objective | d seed | version | status | α_uni | α_nat | bridge_cal r | τ_cal | artefact probe |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for b in sel["bridges"]:
        fl = b["fields"]
        ap = "; ".join(f"{k.split('/', 1)[1]} {_f(v, False)}" for k, v in fl.items() if k.startswith("artefact_probe/")) or "–"
        L.append(f"| {b['eid']} | {b['donor_group']} | {b['slot']} · {_s(b['member_resolved'])} ({_s(b['member_check'])}) | {b['cohort']} · "
                 f"{b['objective']} | {_s(b['donor_seed'])} | {b['version']} | {b['status']} | {_f(fl.get('alpha_uni'), False)} | "
                 f"{_f(fl.get('alpha_nat'), False)} | {_f(fl.get('bridge_cal_r'), False)} | {_f(fl.get('tau_cal'), False)} | {ap} |")
    L += ["", "J* resolution and the member check of the downstream J* units:", "",
          "| donor group | cohort · objective · d seed · version | λ rule → | recorded primary | check | downstream J* units | members used |",
          "|---|---|---|---|---|---|---|"]
    for gid, g in J.items():
        lam = g.get("lambda") or {}
        ds = "; ".join(f"{st}: " + ", ".join(f"{k} {n}" for k, n in c.items()) for st, c in g["downstream"].items()) or "–"
        L.append(f"| {gid} | {g['cohort']} · {g['objective']} · d{_s(g['donor_seed'])} · {g['version']} | {_s(lam.get('choice'))} | "
                 f"{_s(lam.get('recorded_primary'))} | {lam.get('check', g['status'])} | {ds} | "
                 + (", ".join(f"{k} {n}" for k, n in g["members_used"].items()) or "–") + " |")
    return L + [""]


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    a.add_argument("--plan", nargs="+", help="plan JSONL files (default: the ALN3 units.jsonl and plan_ext.jsonl)")
    a.add_argument("--units", help=f"units directory (default {os.path.relpath(UNITS, REPO)})")
    a.add_argument("--entity-manifest", help=f"Federici entity manifest (default {os.path.relpath(ENTITY_MANIFEST, REPO)})")
    a.add_argument("--res", help=f"aggregate JSON directory (default {os.path.relpath(RES, REPO)})")
    a.add_argument("--docs", help=f"Markdown directory (default {os.path.relpath(DOCS, REPO)})")
    a.add_argument("--priv", help=f"per-identity directory, 0700 (default {os.path.relpath(PRIV, REPO)})")
    a.add_argument("--allow-unfrozen", action="store_true", help="dry run with code not listed in the execution record: needs "
                   "scratch --plan, --units, --res, --docs and --priv (never the live plan, units or publication paths)")
    args = a.parse_args(argv)
    if args.allow_unfrozen:
        probs = dry_run_problems(args.units, args.plan, {"--res": args.res, "--docs": args.docs, "--priv": args.priv})
        if probs:
            raise SystemExit("--allow-unfrozen (dry run, design §5.1): " + "; ".join(probs))
    rows = load_rows(args.plan or [PLAN, PLAN_EXT])
    if args.allow_unfrozen:
        live = live_records(rows)
        if live:
            raise SystemExit(f"--allow-unfrozen: {len(live)} plan rows have a record in the live units directory (first {live[0]}); "
                             "a dry run never reads E34 records (design §5.1)")
    fz = frozen_check(rows)
    if not fz["ok"] and not args.allow_unfrozen:
        raise SystemExit("refusing to run (design §5.1: the analysis is frozen in the execution record before any record is read): "
                         + "; ".join(fz["problems"]) + ". A dry run needs --allow-unfrozen with scratch --plan, --units, --res, "
                         "--docs and --priv")
    units_dir = args.units or UNITS
    units = load_records(rows, units_dir)
    res, docs, priv = args.res or RES, args.docs or DOCS, args.priv or PRIV
    out = run_families(units, load_entity_manifest(args.entity_manifest), out_json=os.path.join(res, JSON_NAME),
                       out_md=os.path.join(docs, MD_NAME), out_private=os.path.join(priv, PRIV_NAME),
                       meta={"frozen_check": fz, "dry_run": bool(args.allow_unfrozen)})
    c, p = out["coverage"], out["pairing"]
    print("units:", out["meta"]["n_units"], "complete:", out["meta"]["n_complete"], "not complete:", len(c["not_complete"]),
          "excluded:", out["meta"]["n_excluded"], "versions:", out["meta"]["versions_order"])
    print("pairing: excluded", len(p["cell_pairs_excluded"]), "missing", len(p["cell_pairs_missing"]), "unregistered",
          len(p["cell_pairs_unregistered"]), "pool exclusions", len(p["pool_check"]["zero_shot_units_excluded"]))
    print("frozen check:", "PASS" if fz["ok"] else "; ".join(fz["problems"]), "| privacy scan:", out["meta"]["privacy_scan"])


if __name__ == "__main__":
    main()
