"""A2 metadata-only support freezing; no EEG, prediction or clinical inputs.

Cell order is run3_5_pos0, run3_5_pos1, run6plus_pos0, run6plus_pos1.
The 11 regions of size >=2 use one common uniform cell distribution. Selection
uses experimental-label counts across the cohort and is a disclosed design
choice, not source-only deployment. Frozen trial pools must remain private.
"""
from dataclasses import dataclass
from itertools import combinations
import hashlib
import json

import numpy as np

CELLS = ("run3_5_pos0", "run3_5_pos1", "run6plus_pos0", "run6plus_pos1")
TRIALS_PER_CELL = 6
REPETITIONS = 20


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _bool(value, name):
    if not isinstance(value, (bool, np.bool_)):
        raise ValueError("A2_EXPLICIT_BOOLEAN:" + name)
    return bool(value)


def _integer(value, name):
    try:
        valid = not isinstance(value, (bool, np.bool_)) and np.isfinite(float(value)) and int(value) == value
    except (TypeError, ValueError, OverflowError):
        valid = False
    if not valid:
        raise ValueError("A2_INTEGER:" + name)
    return int(value)


@dataclass(frozen=True)
class Trial:
    trial_id: str
    group: str
    half: int
    label: int
    cell: str
    block: tuple


@dataclass(frozen=True)
class RegionSupport:
    omega: tuple
    groups: tuple
    fold_counts: tuple  # (fold_id, n_train, n_test)
    sufficient: bool


@dataclass(frozen=True)
class FrozenOverlap:
    omega: tuple
    cell_weights: tuple
    groups: tuple
    trials: tuple  # eligible Trial records in the selected common region
    candidates: tuple  # all 11 RegionSupport objects, including unsuccessful ones
    status: str
    metadata_hash: str
    definition_hash: str
    trials_per_cell: int = TRIALS_PER_CELL
    repetitions: int = REPETITIONS


@dataclass(frozen=True)
class TrialDraws:
    groups: tuple
    omega: tuple
    cell_weights: tuple
    # [repeat, candidate, half, class, cell, six trial IDs]
    trial_ids: np.ndarray
    definition_hash: str
    seed: int


def _eligible_metadata(events, literal_one):
    rows = events.to_dict("records") if hasattr(events, "to_dict") else list(events)
    required = {"trial_id", "split_group_id", "record_id", "segment_id", "stimulus_local_id",
                "previous_event_id", "previous_code", "previous_run_length", "history_chain_complete",
                "accepted", "A_boundary_eligible", "A_half", "A_block_id", "segment_position_fraction"}
    selected, seen, groups = [], set(), set()
    for row in rows:
        if not required <= set(row):
            raise ValueError("A2_EVENT_SCHEMA")
        tid, group = row["trial_id"], row["split_group_id"]
        if not isinstance(tid, str) or not tid or tid in seen:
            raise ValueError("A2_UNIQUE_TRIAL_ID")
        if not isinstance(group, str) or not group:
            raise ValueError("A2_GROUP_ID")
        seen.add(tid); groups.add(group)
        accepted = _bool(row["accepted"], "accepted")
        boundary = _bool(row["A_boundary_eligible"], "A_boundary_eligible")
        known = _bool(row["history_chain_complete"], "history_chain_complete")
        # These are precomputed past-only fields from the complete chain. Do
        # not inspect history_target/current_run_length or rebuild after QC.
        if not known or row["previous_code"] != literal_one:
            continue
        run = _integer(row["previous_run_length"], "previous_run_length")
        if run < 1 or not isinstance(row["previous_event_id"], str) or not row["previous_event_id"]:
            raise ValueError("A2_COMPLETE_HISTORY_CONTRADICTION")
        if run < 3 or not accepted or not boundary:
            continue
        label, half = (_integer(row[key], key) for key in ("stimulus_local_id", "A_half"))
        if label not in (0, 1) or half not in (0, 1):
            raise ValueError("A2_CLASS_OR_HALF")
        position = float(row["segment_position_fraction"])
        if not np.isfinite(position) or not 0 <= position <= 1:
            raise ValueError("A2_POSITION_FRACTION")
        block = _integer(row["A_block_id"], "A_block_id")
        if block < 0 or any(row[k] is None for k in ("record_id", "segment_id")):
            raise ValueError("A2_BLOCK_PROVENANCE")
        cell = CELLS[(0 if run <= 5 else 2) + int(position >= .5)]
        selected.append(Trial(tid, group, half, label, cell,
                              (str(row["record_id"]), str(row["segment_id"]), block)))
    return tuple(sorted(selected, key=lambda r: r.trial_id)), tuple(sorted(groups))


def _folds(folds, groups):
    folds = folds["folds"] if isinstance(folds, dict) else list(folds)
    if len(folds) != 5:
        raise ValueError("A2_FIVE_FROZEN_OUTER_FOLDS")
    result, seen_folds = [], set()
    for row in folds:
        fold = _integer(row["outer_fold"], "outer_fold")
        train, test = frozenset(row["train_groups"]), frozenset(row["test_groups"])
        if fold in seen_folds or train & test:
            raise ValueError("A2_FOLD_LEAKAGE_OR_DUPLICATE")
        seen_folds.add(fold); result.append((fold, train, test))
    for group in groups:
        if sum(group in test for _, _, test in result) != 1:
            raise ValueError("A2_OUTER_TEST_ASSIGNMENT")
        if any(group not in train | test for _, train, test in result):
            raise ValueError("A2_OUTER_TRAIN_ASSIGNMENT")
    return sorted(result, key=lambda r: r[0])


def freeze_overlap(events, folds, *, literal_one="1"):
    """Freeze Ω using metadata only; never lower quota, cell count or support.

    ``history_chain_complete`` is an explicit caller-audited past-chain flag;
    legacy B's exclusion of run=2 does not mean an unknown chain. Block/embargo
    eligibility must already use the actual frozen filter support. Metadata
    may include rejected events; changing their QC never recomputes history.
    """
    trials, groups = _eligible_metadata(events, literal_one)
    partition = _folds(folds, groups)
    pools = {}
    for row in trials:
        pools.setdefault((row.group, row.half, row.label, row.cell), []).append(row)
    attempts = []
    for size in range(2, 5):
        for omega in combinations(CELLS, size):
            qualified = []
            for group in groups:
                sufficient = True
                for half, label in ((0, 0), (0, 1), (1, 0), (1, 1)):
                    cells = [pools.get((group, half, label, cell), []) for cell in omega]
                    if any(len(pool) < TRIALS_PER_CELL for pool in cells) or len({r.block for pool in cells for r in pool}) < 3:
                        sufficient = False
                        break
                if sufficient:
                    qualified.append(group)
            qualified = tuple(qualified)
            counts = tuple((number, len(set(qualified) & train), len(set(qualified) & test))
                           for number, train, test in partition)
            enough = len(qualified) >= 25 and all(train >= 12 and test >= 2 for _, train, test in counts)
            attempts.append(RegionSupport(tuple(omega), qualified, counts, enough))
    passing = [attempt for attempt in attempts if attempt.sufficient]
    if passing:
        chosen = min(passing, key=lambda a: (-len(a.omega), -len(a.groups), a.omega))
        status = "SUFFICIENT_FOR_SCREEN"
    else:
        chosen = min(attempts, key=lambda a: (-len(a.groups), -len(a.omega), a.omega))
        status = "DESCRIPTIVE_ONLY" if chosen.groups else "INSUFFICIENT"
    selected = tuple(r for r in trials if r.group in set(chosen.groups) and r.cell in chosen.omega)
    metadata_hash = _hash([(r.trial_id, r.group, r.half, r.label, r.cell, r.block) for r in trials])
    definition_hash = _hash(dict(version="A2_overlap_v2", omega=chosen.omega,
        q=[1 / len(chosen.omega)] * len(chosen.omega), quota=6, blocks=3, repetitions=20,
        metadata_hash=metadata_hash, folds=[(f, sorted(a), sorted(b)) for f, a, b in partition]))
    return FrozenOverlap(chosen.omega, tuple([1 / len(chosen.omega)] * len(chosen.omega)), chosen.groups,
                         selected, tuple(attempts), status, metadata_hash, definition_hash)


def draw_trials(frozen, *, seed=20260917):
    """Twenty reproducible block-constrained draws from immutable frozen pools.

    For each candidate/half/class/repeat, draw three distinct original blocks
    uniformly, then one anchor trial uniformly from each. Fill each cell to six
    uniformly without replacement. This guarantees three blocks in the actual
    selected sample, even when one eligible block contains very few trials.
    Re-use across repetitions is allowed; re-use within a half/class draw is not.
    The anchor design is metadata-only and is not uniform over all trial subsets.
    """
    if (frozen.trials_per_cell != 6 or frozen.repetitions != 20 or not 2 <= len(frozen.omega) <= 4 or
            len(set(frozen.omega)) != len(frozen.omega) or not set(frozen.omega) <= set(CELLS)):
        raise ValueError("A2_FROZEN_QUOTA")
    if frozen.cell_weights != tuple([1 / len(frozen.omega)] * len(frozen.omega)):
        raise ValueError("A2_COMMON_CELL_DISTRIBUTION")
    shape = (20, len(frozen.groups), 2, 2, len(frozen.omega), 6)
    output = np.empty(shape, dtype=object)
    cell_index = {cell: i for i, cell in enumerate(frozen.omega)}
    for g, group in enumerate(frozen.groups):
        for half, label in ((0, 0), (0, 1), (1, 0), (1, 1)):
            own = [r for r in frozen.trials if (r.group, r.half, r.label) == (group, half, label)]
            blocks = sorted({r.block for r in own})
            if len(blocks) < 3:
                raise ValueError("A2_DRAW_BLOCK_SUPPORT")
            for repeat in range(20):
                draw_seed = int(_hash((int(seed), frozen.definition_hash, group, half, label, repeat))[:16], 16)
                rng = np.random.default_rng(draw_seed)
                picked = {cell: [] for cell in frozen.omega}
                for b in rng.choice(len(blocks), 3, replace=False):
                    block_rows = [r for r in own if r.block == blocks[b]]
                    chosen = block_rows[int(rng.integers(len(block_rows)))]
                    picked[chosen.cell].append(chosen.trial_id)
                for cell in frozen.omega:
                    remaining = [r.trial_id for r in own if r.cell == cell and r.trial_id not in picked[cell]]
                    need = 6 - len(picked[cell])
                    if len(remaining) < need:
                        raise ValueError("A2_DRAW_CELL_SUPPORT")
                    picked[cell].extend(rng.choice(remaining, need, replace=False).tolist())
                    output[repeat, g, half, label, cell_index[cell]] = picked[cell]
    output.setflags(write=False)
    return TrialDraws(frozen.groups, frozen.omega, frozen.cell_weights, output, frozen.definition_hash, int(seed))


def summarize_draws(features, trial_ids, draws, *, feature_scope_id, candidate_subset=None):
    """One declared encoder coordinate system; no fit or feature-based selection.

    Returns means [repeat,candidate,half,class,feature], delta and common response
    [repeat,candidate,half,feature]. Caller fits transforms using training groups
    only. Features for another fold must be passed in a separate invocation.
    """
    x, ids = np.asarray(features, float), np.asarray(trial_ids, str)
    if not isinstance(feature_scope_id, str) or not feature_scope_id:
        raise ValueError("A2_SINGLE_FEATURE_SCOPE_REQUIRED")
    if x.ndim != 2 or min(x.shape) < 1 or ids.shape != (len(x),) or len(set(ids)) != len(ids) or not np.isfinite(x).all():
        raise ValueError("A2_FEATURE_ALIGNMENT")
    wanted = draws.groups if candidate_subset is None else tuple(candidate_subset)
    if len(set(wanted)) != len(wanted) or not set(wanted) <= set(draws.groups):
        raise ValueError("A2_DRAW_GROUP_SUBSET")
    lookup = {tid: i for i, tid in enumerate(ids)}
    selected = draws.trial_ids[:, [draws.groups.index(g) for g in wanted]]
    if (draws.trial_ids.shape != (20, len(draws.groups), 2, 2, len(draws.omega), 6) or
            draws.cell_weights != tuple([1 / len(draws.omega)] * len(draws.omega))):
        raise ValueError("A2_FROZEN_DRAW_DISTRIBUTION")
    for row in selected.reshape(-1, len(draws.omega) * 6):
        if len(set(row)) != len(row):
            raise ValueError("A2_REPEATED_TRIAL_IN_DRAW")
    if not set(selected.ravel()) <= set(lookup):
        raise ValueError("A2_MISSING_FROZEN_TRIAL_FEATURE")
    index = np.array([lookup[tid] for tid in selected.ravel()], dtype=int).reshape(selected.shape)
    means = np.zeros((20, len(wanted), 2, 2, x.shape[1]))
    # Bounded temporary allocation: at most one repeat/cell, never the entire
    # 20 x candidate x half x class x cell x trial x feature tensor.
    for repeat in range(20):
        for cell, weight in enumerate(draws.cell_weights):
            means[repeat] += weight * x[index[repeat, :, :, :, cell]].mean(axis=-2)
    return dict(groups=wanted, feature_scope_id=feature_scope_id, definition_hash=draws.definition_hash,
                means=means, delta=means[:, :, :, 1] - means[:, :, :, 0],
                common_response=means.mean(axis=3))
