"""E34_PUBLIC_PRIOR donor sampler (module M3; private/auditory_alignment_v3/aln34/PUBLIC_PRIOR_DESIGN.md §2.2, §2.5, §2.6, §2.10,
§2.11, §2.14, §3.1, §3.2, §3.4, §6.1 `sampler.py`, §6.6 M3; contract aln33_env64_125ms_v1): the shared lockstep batch stream of a
donor group, the XM derangement, the stream hash and exact resume, the fixed selection sets and the bridge rows. Manifest schema:
tests/auditory_alignment_v3/prior33/fixtures.py; banks and guards: views.py.

DonorSampler(manifest, donor_set, block, seed, device) draws, per step, from ONE generator (seed = sampler_seed = donor_seed):
  1. a stratum k with the manifest weights of the donor set (batches are single-stratum);
  2. 32 eligible listener segments of k: a uniform participant, then a uniform segment of that participant (the ALN Batcher's
     participant balance), redrawn while its (presentation, s) is already in the batch;
  3. per segment a partner, uniform over the other listeners of the same (presentation, s, role) (never the listener, never an
     excluded HC / HC-v twin);
  4. per segment one phase phi ~ U{0..30}; ticks j = phi + 31 a (a = 0..7), shared by both listeners;
  5. the montage subset: u ~ U[0, 1) and m ~ U{0, 1, 2}; for a 64-channel cohort (SparrKULee, DTU) with u < 0.5 only the channels
     of AUG_SUBSETS[m] (FAU / Federici / private montage within BioSemi-64) are kept, the others are zeroed in both views.
  next_batch() -> Batch (x1, x2, y, rich, rich_mask, keys, part1, part2, fam_s, stratum, chan_mask, seg_ids, + context fields
  below). Every member of a group trains on the same Batch object (§2.6 lockstep); M5 owns that loop.
  derangement(batch) -> (perm, stats): the XM permutation of the 32 segments from the separate generator seed + 7; xm_view(batch,
  perm) builds XM's view 2 (X2[pi], X1's keys). stream_hash(), hash_log, state(), load_state(st), calibration_batches().
selection_sets(manifest) -> the §2.10 / §2.11 fixed SparrKULee sets; bridge_rows(manifest, donor_set, root=None) -> the §2.11
bridge-fit rows (it reads the donor cohorts' tables: a caller that holds a cache root must pass it as root=). montage_masks(layout)
-> the augmentation masks of a 64-channel layout. check_leave_target_out(target, key, ds) (key: the donor-set key core | rich |
csx, block panel mapping to core; ds: that manifest donor-set entry) and check_donor_rows(idx, stratum, cohort, rows,
participants, excluded, loaded=None): the construction checks that DonorSampler and bridge_rows share.

Data-use guards (enforced in code at construction; tests in tests/auditory_alignment_v3/prior33/test_views_sampler.py): the
target cohort never appears among the strata (leave-target-out, §3.1), private_bdf is never a donor, fau_cs only in the CSX block;
every eligible row is a manifest pool row of role fit and the stratum's kind (ss; fau_cs: cs), outside the donor set's excluded
(overlapping) presentations, with >= 1 partner, of a donor participant that is not test_only (Federici phantom), not a DTU HI
listener and not a restricted SparrKULee participant; its EEG span meets no shared-audio span; the recounted eligible counts equal
the manifest n_segments and the weights equal their shares; the partner candidates agree with the manifest n_partners; every
stratum holds >= 32 distinct (presentation, s) (a design batch); the rich donor set equals the core one (§2.15) and the CSX one is
the core strata, with the core's n_segments and excluded presentations, plus fau_cs (§2.16). The fixed selection and bridge rows
meet no shared-audio span either, and no fixed SparrKULee set (validation fit segments, dev queries and their candidates, bridge_cal
queries and the bridge_cal candidate pool) holds a presentation that any donor set excludes (fail closed; Interpretations). The
bridge-fit rows are re-checked as defense in depth: the donor set for leave-target-out (check_leave_target_out, the sampler's own
check) and every row against the eligible-row rules above (check_donor_rows, with the cohort table's participants). The banks
load only role slabs (views.DonorBank), and the sampler's own banks only the fit pieces its strata can draw.

Interpretations (each is a deviation of the M3 summary)
- donor_set is the target cohort name (the donor-group row's dataset: manifest.donor_sets[target]); a donor-set dict or the list of
  strata is accepted when it identifies exactly one manifest entry. block "panel" uses the core donor set (the manifest has core,
  rich, csx); "rich" draws the core pools with the rich targets added (no extra random draw, so its stream equals the core's).
- Participant balance with distinct (presentation, s): candidate (participant, segment) pairs are drawn in chunks of 64
  (rng.integers participants, rng.random segment positions) and taken in order while distinct; leftover draws of a chunk are
  discarded. A stratum that cannot fill a batch within 200,000 candidates raises.
- Partner ids are integers code * 10**6 + table position (views.participant_ids), unique across cohorts.
- Banks: a sampler that builds its own banks loads, per cohort, the fit pieces of its eligible rows only (DonorBank pieces=: a
  core or rich group does not load FAU's competing-talker trials, 0.50 of the 0.86 GB FAU fit slab, which only CSX draws); any
  further role in bank_roles (SparrKULee dev, bridge_cal, control_artefact) is loaded whole. A bank passed in (banks=) is used as
  given and must hold every eligible row (a "segments" bank is refused: training draws any eligible row). The bank contents never
  change a draw: the stream depends on the manifest only.
- chan_mask is bool [2, 256, C] (view 1, view 2): a channel is read when it is in the montage subset and not a masked
  (piece, channel) cell; x1 / x2 are zero wherever it is False (masked cells are zero in the caches already).
- Batch.y is the RMS-normalised 2-8 Hz envelope window (float32); the shared fixed head divides by sigma (mu = 0). Rich block only:
  rich = {"ss": [256, 32] (8 samples x 4 dims, sample-major), "sc": [256, 8]} float32 with NaN rows where absent, and rich_mask
  bool [256] (stream available and window finite): rich.rich_loss present = {"env": True, "ss": rich_mask, "sc": rich_mask}.
- Extra Batch fields after the twelve design fields: partner_ids (segment rows of view 2), cohort, layout (the per-call row order
  for the model), ticks [32, 8], montage (subset name or None), step (-1 for calibration batches).
- XM (§2.6): up to 100 uniformly random derangements are drawn (a permutation redrawn until it has no fixed point), and the kept
  draw minimises the hard-constraint violations (family(pi(i)) = family(i), partner(pi(i)) = listener(i)), then maximises the
  same-condition pairs; the loop stops early at a draw without violations whose pairs are all same-condition. If no draw meets
  the hard constraints, the kept permutation is instead the exact assignment optimum (scipy linear_sum_assignment) of the cost
  XM_W_HARD * n * violations + [different condition] + U[0, 1/(n + 1)) per pair (the tie-break drawn from the same derangement
  generator), with the diagonal forbidden: it meets the hard constraints whenever any permutation does, and otherwise has the
  fewest violations, so violations remain only on infeasible batches (small strata), as §2.6 intends. The literal rule (best of
  100 random draws) missed an existing permutation in 36.6 % of batches with the real FAU structure (8 single-talker families x 81
  listeners; M3 review), 2.9 % for fau_cs and 1.8 % for SparrKULee. stats: method ("random_draw" | "assignment"), feasible (a
  permutation meeting both hard constraints exists for the batch; exact), constraints_met (the kept permutation meets them; equal
  to feasible by construction), violations (+ _family, _partner), same_condition (+ _fraction), draws, rejected_with_fixed_points,
  fixed_points (always 0), n_segments.
- XM partner constraint, twin-aware: HC N and HC-v N (manifest partner_exclusions) count as one listener, so XM never pairs them
  either (§2.5 avoids that pair in partner sampling so that either identity hypothesis is leakage-safe; XM's view 2 is a partner
  too). It can only add violations, on Federici batches. Conditions are views.condition_key() classes (the presentation's
  condition with SparrKULee's noise condition and SNR, when the manifest carries them; not the stimulus-specific noise file). XM
  view-2 rows: segment pi(i)'s 8 anchors in anchor order (their own ticks), with X1's keys.
- Stream hash: a sha256 chain h_t = sha256(h_{t-1} | stratum | segment rows | partner rows | ticks | montage index), h_0 =
  sha256("prior33_donor_stream_v1"); it covers only the draws, so the core and rich groups of a (target, objective, seed) agree,
  and its state is 32 bytes (exact resume). hash_log keeps [step, digest] every 1,000 steps. The resume state (schema v2) also
  holds the derangement generator; a v1 state (before the assignment fallback) is refused.
- calibration_batches(): one batch per stratum (strata order) from the separate generator seed + 99 (§2.8), drawn by the same rule
  (augmentation included unless augment=False); the main stream, its hash and its step are untouched.
- selection_sets(): o(q) of the gain score (§2.10 "a fixed other dev segment of the same listener") is the next query of the same
  listener in (piece, s) order, cyclically, with different content; -1 when the listener has none. Dev candidates are the unique
  (presentation, s) of the dev queries (§2.10); bridge_cal candidates the unique (presentation, s) of the bridge_cal pool (the τ
  pools of §2.11 draw from them). The roles fit / dev / bridge_cal are checked disjoint by participant and by family.
- Fixed sets vs overlap exclusions (fail closed): §3.2 gives one dev / bridge_cal definition (and one validation fit set) to all
  four donor sets, while §3.4.1 and the inherited contract §2 (整个目标队列从供体预训练与供体开发/桥接中排除; any overlap with target
  content is excluded from the source) exclude target-overlapping content from donor development and calibration as well. The
  shared sets are therefore checked against the SparrKULee presentations that ANY donor set excludes, and a hit raises: C6 must
  draw these sets outside every target's excluded presentations (a design gap reported to the lead, not filtered per target,
  because §2.10 makes the score set identical for every group of a seed).
- bridge_rows(): the manifest's fit rows of the donor set (bridge.fit_rows[target], core strata), with one montage choice per row
  (u, m as in training, one pair per row in row order; applied for 64-channel cohorts with u < 0.5) from a generator seeded by
  SeedSequence([BRIDGE_SEED, BRIDGE_MONTAGE_TAG]), not by BRIDGE_SEED itself, which the design gives C6 for drawing the rows (the
  montage draws would otherwise replay that stream). CSX slots (APC, XPC) use the core donor set's rows and fau_cs rows are
  refused, so the paired AP / APC and XP / XPC bridges are fitted on identical rows (not stated in the design). bridge_rows reads
  the cohort tables (runs.json / pieces.json, as DonorBank does; root= as there) for the participant rules of check_donor_rows; a
  row that the sampler could not draw (role, kind, partner, participant, presentation, shared audio, family clock) raises. The
  cache root is root=, else the manifest's (views.manifest_root): a caller that holds a root must pass it (bridge.bridge_banks and
  bridge.fit_bridge receive one and must pass root=root, or a plain-dict manifest fails closed and a Manifest whose .root differs
  would have its rows checked against another root's tables; M3 review round 3, reported to the lead for M6).
- check_donor_rows, compared with the former DonorSampler._check_rows: rows outside the segment table raise ValueError (a negative
  row no longer wraps as a numpy index, a too-large one no longer raises IndexError), and the restricted-participant rule runs
  before the table lookup, so a restricted SparrKULee participant missing from the table raises RestrictedAccess (a
  PermissionError), not ValueError. Both fail closed; the eligible rows and the batch stream are unchanged.
"""
from __future__ import annotations

import copy
import hashlib
from dataclasses import dataclass

import numpy as np
import torch
from scipy.optimize import linear_sum_assignment

from . import contract as C
from .views import (COND_FIELDS, DONOR_COHORTS, RESTRICTED, DonorBank, RestrictedAccess, _canon, _guard_restricted, cohort_table,
                    manifest_index, manifest_root, manifest_sha)

N_SEG = 32                                  # listener segments per batch (§2.6)
N_ROWS = N_SEG * C.N_ANCHORS                # 256 anchors; 512 EEG windows over both views
XM_DRAWS = 100
XM_W_HARD = 4.0                             # assignment fallback: a hard violation costs XM_W_HARD * n (> n + 1 = every other term)
XM_RULE = "random100_then_assignment_v1"
AUG_NAMES = tuple(C.AUG_SUBSETS)            # ("fau", "federici", "private_bdf")
BLOCKS = {"core": "core", "panel": "core", "rich": "rich", "csx": "csx"}
DRAW_CHUNK, MAX_CANDIDATES = 64, 200_000
HASH_EVERY = 1000
STATE_SCHEMA = "prior33_donor_sampler_state_v2"
STREAM_TAG = b"prior33_donor_stream_v1"
BRIDGE_MONTAGE_TAG = 0x4D4F4E54             # "MONT": the bridge montage stream is SeedSequence([BRIDGE_SEED, this tag])


def coh_of(stratum):
    return "fau" if stratum == "fau_cs" else stratum


@dataclass(eq=False)
class Batch:
    x1: torch.Tensor                  # float16 [256, C, 38] view 1 (the listener)
    x2: torch.Tensor                  # float16 [256, C, 38] view 2 (the partner: same presentation and ticks)
    y: torch.Tensor                   # float32 [256, 8] envelope windows
    rich: dict | None                 # rich block: {"ss": [256, 32], "sc": [256, 8]} float32, NaN rows where absent
    rich_mask: torch.Tensor | None    # rich block: bool [256]
    keys: torch.Tensor                # int64 [256] packed keys, shared by both views
    part1: torch.Tensor               # int64 [256] participant ids of view 1
    part2: torch.Tensor               # int64 [256] participant ids of view 2
    fam_s: torch.Tensor               # int64 [256] family-clock sample (the key's s field)
    stratum: str
    chan_mask: torch.Tensor           # bool [2, 256, C]
    seg_ids: np.ndarray               # int64 [32] segment-table rows of view 1
    partner_ids: np.ndarray           # int64 [32] segment-table rows of view 2
    cohort: str
    layout: tuple
    ticks: np.ndarray                 # int64 [32, 8] tick indices j
    montage: str | None
    step: int


@dataclass(eq=False)
class XMView:
    x2: torch.Tensor                  # float16 [256, C, 38] = X2[pi] (anchor rows of segment pi(i))
    part2: torch.Tensor               # int64 [256]
    chan_mask2: torch.Tensor          # bool [256, C]
    keys: torch.Tensor                # X1's keys
    rows: torch.Tensor                # int64 [256] anchor rows taken from view 2
    perm: np.ndarray                  # int64 [32]


@dataclass
class _Draw:
    k: int
    rows: np.ndarray
    partners: np.ndarray
    phases: np.ndarray
    montage: str | None
    m_index: int


def montage_masks(layout):
    """{subset: bool [C]} for a BioSemi-64 layout (FAU∩64 27, Federici∩64 28, private 20 channels); {} for any other layout."""
    lay = tuple(C.canonical(n) for n in layout)
    if len(lay) != 64 or set(lay) != set(C.BIOSEMI64):
        return {}
    return {k: np.array([n in set(C.AUG_SUBSETS[k]) for n in lay], dtype=bool) for k in AUG_NAMES}


def resolve_donor_set(manifest, donor_set, block):
    """(target, manifest block key, donor-set entry) for a target name, a donor-set dict or a strata list."""
    if block not in BLOCKS:
        raise ValueError(f"block {block!r}: one of {sorted(BLOCKS)}")
    key, sets = BLOCKS[block], manifest["donor_sets"]
    if isinstance(donor_set, str):
        if donor_set not in sets:
            raise ValueError(f"no donor set for target {donor_set!r} (manifest targets {sorted(sets)})")
        if key not in sets[donor_set]:
            raise ValueError(f"target {donor_set}: no {key} donor set (§2.16: there is no CSX group for target fau)")
        return donor_set, key, sets[donor_set][key]
    if isinstance(donor_set, dict):
        hit = [t for t, b in sets.items() if key in b and _canon(b[key]) == _canon(donor_set)]
    else:
        hit = [t for t, b in sets.items() if key in b and list(b[key]["strata"]) == list(donor_set)]
    if len(hit) != 1:
        raise ValueError(f"donor_set {donor_set!r} matches {len(hit)} manifest donor sets in block {key}")
    return hit[0], key, sets[hit[0]][key]


def _excluded(ds, stratum):
    return sorted({int(p) for p in (ds.get("excluded_presentations") or {}).get(stratum, ())})


def _check_csx(target, ds, core):
    """§2.16: the CSX donor set is the core strata, with the core's n_segments and excluded presentations, plus fau_cs."""
    strata = [str(s) for s in ds["strata"]]
    if core is None or "fau_cs" not in strata or [s for s in strata if s != "fau_cs"] != [str(s) for s in core["strata"]]:
        raise ValueError(f"target {target}: the CSX donor set must be the core strata plus fau_cs (§2.16)")
    cn, xn = dict(zip(core["strata"], core["n_segments"])), dict(zip(ds["strata"], ds["n_segments"]))
    bad = [s for s in core["strata"] if int(xn[s]) != int(cn[s]) or _excluded(ds, s) != _excluded(core, s)]
    if bad:
        raise ValueError(f"target {target}: the CSX donor set's core strata {bad} differ from the core donor set in n_segments or "
                         "excluded_presentations (§2.16: the AP -> APC and XP -> XPC contrasts need the core pools unchanged)")


class _Stratum:
    """Eligible rows of one stratum, the participant-balanced draw index and the partner candidates."""

    def __init__(self, name, k, rows, S, twins):
        self.name, self.k, self.cohort = name, k, coh_of(name)
        self.rows = np.asarray(sorted(int(r) for r in rows), dtype=np.int64)
        part = S["participant"][self.rows]
        self.participants = sorted({str(p) for p in part})
        by = {p: [] for p in self.participants}
        for r, p in zip(self.rows, part):
            by[str(p)].append(int(r))
        self.part_rows = np.array([r for p in self.participants for r in by[p]], dtype=np.int64)
        self.part_off = np.cumsum([0] + [len(by[p]) for p in self.participants]).astype(np.int64)
        self.n_part = len(self.participants)
        groups = {}
        for r in range(len(S["s"])):
            groups.setdefault((int(S["presentation"][r]), int(S["s"][r]), str(S["role"][r])), []).append(r)
        self.pos = np.full(len(S["s"]), -1, dtype=np.int64)
        self.pos[self.rows] = np.arange(len(self.rows))
        # partner candidates, two-level CSR: eligible row -> partner participants (sorted) -> that participant's rows (a listener
        # may hold two rows of one (presentation, s) when it heard the presentation twice; the partner is uniform over listeners)
        cand, block, row_b = [], [], [0]
        for r in self.rows:
            a = str(S["participant"][r])
            by_p = {}
            for q in groups[(int(S["presentation"][r]), int(S["s"][r]), str(S["role"][r]))]:
                b = str(S["participant"][q])
                if b != a and (a, b) not in twins:
                    by_p.setdefault(b, []).append(q)
            if not by_p:
                raise ValueError(f"stratum {name}: segment row {r} has no valid partner")
            if len(by_p) != int(S["n_partners"][r]):
                raise ValueError(f"stratum {name}: segment row {r}: {len(by_p)} partner listeners, manifest n_partners {int(S['n_partners'][r])}")
            for b in sorted(by_p):
                block.append(len(cand)); cand += by_p[b]
            row_b.append(len(block))
        block.append(len(cand))
        self.cand = np.asarray(cand, dtype=np.int64)
        self.block = np.asarray(block, dtype=np.int64)
        self.row_b = np.asarray(row_b, dtype=np.int64)
        if (self.pos[self.cand] < 0).any():
            raise ValueError(f"stratum {name}: a partner row is not an eligible row of the stratum")
        self.cid = S["presentation"].astype(np.int64) * (1 << 32) + S["s"].astype(np.int64)
        self.n_content = len(set(self.cid[self.rows].tolist()))
        if self.n_content < N_SEG:
            raise ValueError(f"stratum {name}: {self.n_content} distinct (presentation, s) < {N_SEG}: it cannot fill a §2.6 batch")

    def partners(self, rows, u):
        """A uniform partner listener per row from u ~ U[0, 1), then a uniform row of that listener (from the fractional part)."""
        p = self.pos[rows]
        n = self.row_b[p + 1] - self.row_b[p]
        x = u * n
        a = np.minimum(np.floor(x).astype(np.int64), n - 1)
        b = self.row_b[p] + a
        lo, hi = self.block[b], self.block[b + 1]
        return self.cand[lo + np.minimum(((x - a) * (hi - lo)).astype(np.int64), hi - lo - 1)]


def check_leave_target_out(target, key, ds):
    """§3.1: no stratum of a donor set is the target cohort, private_bdf or another non-donor cohort, and fau_cs only in CSX."""
    for s in (str(x) for x in ds["strata"]):
        c = coh_of(s)
        if c == target or c not in DONOR_COHORTS:
            raise ValueError(f"donor set {target}/{key}: stratum {s} ({c}) breaks leave-target-out (§3.1)")
        if s == "fau_cs" and key != "csx":
            raise ValueError(f"donor set {target}/{key}: the fau_cs stratum belongs to the CSX block only (§2.16)")


def check_donor_rows(idx, s, c, rows, participants, excl, loaded=None):
    """The rules every donor row of stratum s (cohort c) meets (module docstring, Data-use guards): a row of the manifest segment
    table of role fit and the stratum's kind (ss; fau_cs: cs) with >= 1 partner, of a donor participant of the cohort table
    (`participants`: {participant: table record}; donor, not test_only, DTU NH, not the Federici phantom, not restricted), of a
    presentation of the cohort and kind outside `excl` (the donor set's excluded presentations), its EEG span outside every
    shared-audio span, with a packable family clock; `loaded` (DonorSampler: bank.loaded) must hold its piece. DonorSampler
    checks its eligible rows with it, bridge_rows the bridge-fit rows (defense in depth). ValueError (also for rows outside the
    segment table) / RestrictedAccess (a restricted participant, checked before the table lookup: raised also when the table does
    not list it)."""
    S = idx.seg[c]
    kind = "cs" if s == "fau_cs" else "ss"
    rows = np.asarray(rows, dtype=np.int64).reshape(-1)
    if len(rows) == 0:
        raise ValueError(f"stratum {s}: no eligible rows")
    if rows.min() < 0 or rows.max() >= len(S["s"]):
        raise ValueError(f"stratum {s}: rows outside the {c} segment table")
    bad = [int(r) for r in rows if S["role"][r] != "fit" or S["kind"][r] != kind or int(S["n_partners"][r]) < 1]
    if bad:
        raise ValueError(f"stratum {s}: pool rows {bad[:5]} are not fit / {kind} rows with a partner")
    if loaded is not None and not loaded(S["piece"][rows]).all():
        raise ValueError(f"stratum {s}: pool rows outside the bank's fit slab")
    for p in sorted({str(v) for v in S["participant"][rows]}):
        q = participants.get(p)
        if c == "sparrkulee" and p in RESTRICTED:
            raise RestrictedAccess(f"stratum {s}: restricted SparrKULee participant sub-{p} in a pool")
        if q is None:
            raise ValueError(f"stratum {s}: participant {p} is not in the {c} table")
        if not q.get("donor", True) or q.get("test_only") or (c == "dtu" and str(q.get("group")).lower() != "nh") or \
                (c == "federici" and str(q.get("group")) == "Artifact"):
            raise ValueError(f"stratum {s}: participant {p} is not a donor (§3.1: no HI listener, no phantom, no test_only)")
    for p in sorted({int(v) for v in S["presentation"][rows]}):
        if p in excl or idx.cohort[p] != c or idx.kind[p] != kind:
            raise ValueError(f"stratum {s}: presentation {p} is excluded or not a {c} {kind} presentation")
        spans = idx.shared.get(p)
        if spans:
            ss = S["s"][rows[S["presentation"][rows] == p]]
            for a, b in spans:
                if ((a < ss + C.SPAN_EEG) & (ss < b)).any():
                    raise ValueError(f"stratum {s}: a pool segment of presentation {p} meets the shared-audio span [{a}, {b})")
    idx.fs0(S["presentation"][rows], S["s"][rows])       # every row's presentation has a packable family clock


def xm_assignment(fam, lis, par, cond, rng):
    """The XM assignment fallback (module docstring): the derangement pi minimising, lexicographically, the hard violations
    [fam[pi(i)] == fam[i]] + [par[pi(i)] == lis[i]], then the different-condition pairs, then a U[0, 1/(n + 1)) tie-break drawn
    from `rng` (n * n draws) -> (perm int64 [n], minimal number of violations)."""
    fam, lis, par, cond = (np.asarray(a, dtype=np.int64).reshape(-1) for a in (fam, lis, par, cond))
    n = len(fam)
    if n < 2:
        raise ValueError("xm_assignment: >= 2 segments")
    H = (fam[None, :] == fam[:, None]).astype(np.float64) + (par[None, :] == lis[:, None])     # H[i, j]: pi(i) = j
    cost = XM_W_HARD * n * H + (cond[None, :] != cond[:, None]) + rng.random((n, n)) / (n + 1)
    np.fill_diagonal(cost, np.inf)                                                             # no fixed point, ever
    r, c = linear_sum_assignment(cost)
    perm = np.empty(n, dtype=np.int64)
    perm[r] = c
    return perm, int(H[np.arange(n), perm].sum())


class DonorSampler:
    """The lockstep donor batch stream of one group (§2.6)."""

    def __init__(self, manifest, donor_set, block, seed, device, *, bank_roles=None, banks=None, root=None):
        self.manifest, self.block, self.seed, self.device, self.root = manifest, block, int(seed), torch.device(device), root
        self.target, self.key, ds = resolve_donor_set(manifest, donor_set, block)
        self.strata = [str(s) for s in ds["strata"]]
        self.weights = np.asarray(ds["weights"], dtype=np.float64)
        self.n_segments = [int(n) for n in ds["n_segments"]]
        self.idx = idx = manifest_index(manifest)
        if len(self.weights) != len(self.strata) or len(self.n_segments) != len(self.strata) or len(set(self.strata)) != len(self.strata):
            raise ValueError(f"donor set {self.target}/{self.key}: strata, weights and n_segments do not align")
        core = manifest["donor_sets"][self.target].get("core")
        if self.key == "rich" and _canon(ds) != _canon(core):
            raise ValueError(f"target {self.target}: the rich donor set must equal the core one (§2.15: same sampler, seed and pools)")
        if self.key == "csx":
            _check_csx(self.target, ds, core)
        check_leave_target_out(self.target, self.key, ds)
        cohorts = []
        for s in self.strata:
            if coh_of(s) not in cohorts:
                cohorts.append(coh_of(s))
        self.cohorts = cohorts
        n = np.asarray(self.n_segments, dtype=np.float64)
        if (n <= 0).any() or abs(self.weights.sum() - 1) > 1e-9 or not np.allclose(self.weights, n / n.sum(), rtol=0, atol=1e-12):
            raise ValueError(f"donor set {self.target}/{self.key}: weights {self.weights.tolist()} are not the shares of {self.n_segments}")
        # eligible rows (manifest only), before any bank: the sampler's own banks load the fit pieces of these rows only
        elig, excls = {}, {}
        for k, s in enumerate(self.strata):
            S = idx.seg[coh_of(s)]
            pool = manifest["pools"]["csx"]["fau_cs"] if s == "fau_cs" else manifest["pools"]["core"][coh_of(s)]
            excls[s] = set(_excluded(ds, s))
            elig[s] = np.asarray([int(r) for r in pool if int(S["presentation"][int(r)]) not in excls[s]], dtype=np.int64)
            if len(elig[s]) != self.n_segments[k]:
                raise ValueError(f"stratum {s}: {len(elig[s])} eligible rows, manifest n_segments {self.n_segments[k]}")
        rich = self.key == "rich"
        banks = dict(banks or {})
        bank_roles = dict(bank_roles or {})
        self.banks = {}
        for c in cohorts:
            b = banks.get(c)
            if b is None:
                roles = tuple(bank_roles.get(c, ("fit",)))
                if "fit" not in roles:
                    raise ValueError(f"bank {c}: needs the fit slab (bank_roles {roles})")
                need = sorted({int(p) for s in self.strata if coh_of(s) == c for p in idx.seg[c]["piece"][elig[s]]})
                b = DonorBank(manifest, c, roles, self.device, rich=rich, root=root, pieces={"fit": need})
            elif b.manifest is not manifest and (manifest_sha(manifest) is None or manifest_sha(b.manifest) != manifest_sha(manifest)):
                raise ValueError(f"bank {c} belongs to another manifest")
            if b.device != self.device:
                raise ValueError(f"bank {c} is on {b.device}, the sampler on {self.device}")
            if "fit" not in b.roles or (rich and b.rich is None) or b.mode == "segments":
                raise ValueError(f"bank {c}: needs the fit slab{' and rich=True' if rich else ''} (not a segments bank)")
            self.banks[c] = b
        twins = {}
        for c, a, b in manifest.get("partner_exclusions", ()):
            twins.setdefault(c, set()).update({(str(a), str(b)), (str(b), str(a))})
        self._twin_group = self._twin_groups(manifest)
        self._strata = []
        for k, s in enumerate(self.strata):
            c = coh_of(s)
            S, bank = idx.seg[c], self.banks[c]
            self._check_rows(s, c, elig[s], S, bank, excls[s])
            self._strata.append(_Stratum(s, k, elig[s], S, twins.get(c, set())))
        self._cdf = np.cumsum(self.weights)
        self._aug = {c: montage_masks(self.banks[c].layout) for c in cohorts}
        self._pid = {c: np.array([self.banks[c].pid[str(p)] for p in idx.seg[c]["participant"]], dtype=np.int64) for c in cohorts}
        self.rng = np.random.default_rng(self.seed)
        self.xm_rng = np.random.default_rng(self.seed + C.XM_SEED_OFFSET)
        self.step = 0
        self._chain = hashlib.sha256(STREAM_TAG).digest()
        self.hash_log = []
        self.config = {"schema": STATE_SCHEMA, "target": self.target, "block": self.block, "donor_set_block": self.key, "seed": self.seed,
                       "strata": list(self.strata), "weights": [float(w) for w in self.weights], "n_segments": list(self.n_segments),
                       "xm_rule": XM_RULE, "manifest_sha256": manifest_sha(manifest)}

    def _twin_groups(self, manifest):
        """{participant id: group id}: HC N and HC-v N (partner_exclusions) share the smallest id of their group (union-find)."""
        parent = {}

        def find(x):
            while parent.get(x, x) != x:
                x = parent[x]
            return x
        for c, a, b in manifest.get("partner_exclusions", ()):
            bank = self.banks.get(c)
            if bank is None or str(a) not in bank.pid or str(b) not in bank.pid:
                continue
            ra, rb = find(bank.pid[str(a)]), find(bank.pid[str(b)])
            if ra != rb:
                parent[max(ra, rb)] = min(ra, rb)
        return {x: find(x) for x in list(parent)}

    # ------------------------------------------------------------------------------------------------ construction checks
    def _check_rows(self, s, c, rows, S, bank, excl):
        check_donor_rows(self.idx, s, c, rows, bank.participants, excl, loaded=bank.loaded)

    # ------------------------------------------------------------------------------------------------ draws
    def _draw(self, rng, k=None, augment=True):
        if k is None:
            u = rng.random()
            k = min(int(np.searchsorted(self._cdf, u * self._cdf[-1], side="right")), len(self._strata) - 1)
        st = self._strata[k]
        rows, used, n = [], set(), 0
        while len(rows) < N_SEG:
            if n >= MAX_CANDIDATES:
                raise RuntimeError(f"stratum {st.name}: {N_SEG} distinct (presentation, s) not found in {n} candidates")
            pa = rng.integers(0, st.n_part, size=DRAW_CHUNK)
            uu = rng.random(DRAW_CHUNK)
            n += DRAW_CHUNK
            lo = st.part_off[pa]
            for r in st.part_rows[lo + (uu * (st.part_off[pa + 1] - lo)).astype(np.int64)]:
                c = int(st.cid[r])
                if c not in used:
                    used.add(c); rows.append(int(r))
                    if len(rows) == N_SEG:
                        break
        rows = np.asarray(rows, dtype=np.int64)
        partners = st.partners(rows, rng.random(N_SEG))
        phases = rng.integers(0, C.ANCHOR_STEP, size=N_SEG).astype(np.int64)
        mu, mi = float(rng.random()), int(rng.integers(0, len(AUG_NAMES)))
        on = augment and bool(self._aug[st.cohort]) and mu < C.AUG_P
        return _Draw(k, rows, partners, phases, AUG_NAMES[mi] if on else None, mi if on else -1)

    def _ticks(self, d):
        return d.phases[:, None] + C.ANCHOR_STEP * np.arange(C.N_ANCHORS, dtype=np.int64)[None]

    def _hash(self, d):
        h = hashlib.sha256(self._chain)
        h.update(self._strata[d.k].name.encode() + b"\0")
        for a in (d.rows, d.partners, self._ticks(d), np.array([d.m_index])):
            h.update(np.ascontiguousarray(a, dtype="<i8").tobytes())
        self._chain = h.digest()

    def _gather(self, d, step):
        st = self._strata[d.k]
        c, bank, S = st.cohort, self.banks[st.cohort], self.idx.seg[st.cohort]
        ticks = self._ticks(d)
        offs = C.TICK_OFFS[ticks].reshape(-1).astype(np.int64)
        rr, qq = np.repeat(d.rows, C.N_ANCHORS), np.repeat(d.partners, C.N_ANCHORS)
        s, pres = S["s"][rr], S["presentation"][rr]
        if not (np.array_equal(S["s"][qq], s) and np.array_equal(S["presentation"][qq], pres)):
            raise AssertionError("partner rows must share (presentation, s)")
        dev = self.device
        x1 = bank.gather(S["piece"][rr], s, offs)
        x2 = bank.gather(S["piece"][qq], s, offs)
        y = bank.targets(pres, s, offs)
        fs = self.idx.fs0(pres, s + offs)
        keys = C.pack_key(self.idx.fam[pres], pres, fs)
        m1, m2 = bank.mask[S["piece"][rr]], bank.mask[S["piece"][qq]]
        if d.montage is not None:
            keep = self._aug[c][d.montage]
            m1, m2 = m1 & keep, m2 & keep
        M = torch.as_tensor(np.stack([m1, m2]), device=dev)
        x1.masked_fill_(~M[0][:, :, None], 0)
        x2.masked_fill_(~M[1][:, :, None], 0)
        rich = rmask = None
        if self.key == "rich":
            ss, sc, rmask = bank.rich_targets(pres, s, offs)
            rich = {"ss": ss, "sc": sc}
        return Batch(x1=x1, x2=x2, y=y, rich=rich, rich_mask=rmask, keys=torch.as_tensor(keys, device=dev),
                     part1=torch.as_tensor(self._pid[c][rr], device=dev), part2=torch.as_tensor(self._pid[c][qq], device=dev),
                     fam_s=torch.as_tensor(fs, device=dev), stratum=st.name, chan_mask=M, seg_ids=d.rows.copy(),
                     partner_ids=d.partners.copy(), cohort=c, layout=tuple(bank.layout), ticks=ticks, montage=d.montage, step=step)

    def _advance(self):
        d = self._draw(self.rng)
        self._hash(d)
        self.step += 1
        if self.step % HASH_EVERY == 0:
            self.hash_log.append([self.step, self._chain.hex()])
        return d

    def next_batch(self):
        """The next batch of the group's stream (one batch per step for every member)."""
        d = self._advance()
        return self._gather(d, self.step - 1)

    def next_draw(self):
        """next_batch() without gathering tensors (the same draws, hash and step): data-use audits over many steps. Returns
        (stratum, segment rows, partner rows, ticks [32, 8], montage)."""
        d = self._advance()
        return self._strata[d.k].name, d.rows, d.partners, self._ticks(d), d.montage

    def calibration_batches(self, augment=True):
        """{stratum: Batch}: one batch per stratum from the separate stream seed + 99 (§2.8 bandwidth calibration)."""
        rng = np.random.default_rng(self.seed + C.CAL_SEED_OFFSET)
        return {st.name: self._gather(self._draw(rng, st.k, augment), -1) for st in self._strata}

    # ------------------------------------------------------------------------------------------------ XM
    def derangement(self, batch, n_draws=XM_DRAWS):
        """XM permutation pi of the batch's segments from the derangement generator: the best of up to n_draws random
        derangements on (hard-constraint violations, -same-condition pairs), or, when none meets the hard constraints, the exact
        assignment optimum (module docstring) -> (perm, stats)."""
        n = len(batch.seg_ids)
        if n < 2:
            raise ValueError("derangement: a batch of >= 2 segments is needed")
        k0 = batch.keys.reshape(n, C.N_ANCHORS)[:, 0].cpu().numpy()
        fam, pres, _ = C.unpack_key(k0)
        tw = self._twin_group
        lis = np.array([tw.get(int(x), int(x)) for x in batch.part1.reshape(n, C.N_ANCHORS)[:, 0].cpu().numpy()], dtype=np.int64)
        par = np.array([tw.get(int(x), int(x)) for x in batch.part2.reshape(n, C.N_ANCHORS)[:, 0].cpu().numpy()], dtype=np.int64)
        cond = self.idx.cond[pres]
        ar = np.arange(n)
        best, tried, rejected = None, 0, 0
        for _ in range(int(n_draws)):
            perm = self.xm_rng.permutation(n)
            while (perm == ar).any():
                perm = self.xm_rng.permutation(n); rejected += 1
            tried += 1
            vf, vp = int((fam[perm] == fam).sum()), int((par[perm] == lis).sum())
            same = int((cond[perm] == cond).sum())
            if best is None or (vf + vp, -same) < best[0]:
                best = ((vf + vp, -same), perm)
            if vf + vp == 0 and same == n:
                break
        perm, method, feasible = best[1], "random_draw", best[0][0] == 0
        if not feasible:                                   # no draw met the hard constraints: the exact assignment optimum
            perm, v_min = xm_assignment(fam, lis, par, cond, self.xm_rng)
            method, feasible = "assignment", v_min == 0
        vf, vp = int((fam[perm] == fam).sum()), int((par[perm] == lis).sum())
        same = int((cond[perm] == cond).sum())
        if (perm == ar).any() or (method == "random_draw" and (vf + vp, -same) != best[0]):
            raise AssertionError("derangement: internal inconsistency")
        stats = {"method": method, "draws": tried, "rejected_with_fixed_points": rejected, "violations": vf + vp,
                 "violations_family": vf, "violations_partner": vp, "feasible": bool(feasible), "constraints_met": vf + vp == 0,
                 "same_condition": same, "same_condition_fraction": same / n, "n_segments": n, "fixed_points": int((perm == ar).sum())}
        return perm.astype(np.int64), stats

    @staticmethod
    def xm_view(batch, perm):
        """XM's view 2: the anchor rows of segment pi(i) of X2, with X1's keys (a structure-preserving mismatch, §2.6)."""
        perm = np.asarray(perm, dtype=np.int64)
        rows = torch.as_tensor((perm[:, None] * C.N_ANCHORS + np.arange(C.N_ANCHORS)[None]).reshape(-1), device=batch.x2.device)
        return XMView(x2=batch.x2[rows], part2=batch.part2[rows], chan_mask2=batch.chan_mask[1][rows], keys=batch.keys, rows=rows,
                      perm=perm)

    # ------------------------------------------------------------------------------------------------ hash, resume, records
    def stream_hash(self):
        return self._chain.hex()

    def state(self):
        """Exact-resume state: both generators, the step, the hash chain and its log (JSON- and torch.save-serialisable)."""
        return {"schema": STATE_SCHEMA, "config": copy.deepcopy(self.config), "step": self.step,
                "rng": copy.deepcopy(self.rng.bit_generator.state), "xm_rng": copy.deepcopy(self.xm_rng.bit_generator.state),
                "chain": self._chain.hex(), "hash_log": [list(x) for x in self.hash_log]}

    def load_state(self, st):
        if st.get("schema") != STATE_SCHEMA:
            raise ValueError(f"load_state: schema {st.get('schema')!r}, expected {STATE_SCHEMA} (configuration)")
        if _canon(st["config"]) != _canon(self.config):
            diff = {k: (st["config"].get(k), v) for k, v in self.config.items() if _canon(st["config"].get(k)) != _canon(v)}
            raise ValueError(f"load_state: the state belongs to another sampler configuration: {diff}")
        self.rng.bit_generator.state = copy.deepcopy(st["rng"])
        self.xm_rng.bit_generator.state = copy.deepcopy(st["xm_rng"])
        self.step, self._chain = int(st["step"]), bytes.fromhex(st["chain"])
        self.hash_log = [[int(a), str(b)] for a, b in st["hash_log"]]

    def describe(self):
        """For the group record: strata, weights, counts, augmentation, partner and XM rules, and what the banks hold."""
        ds = self.manifest["donor_sets"][self.target][self.key]
        return {"target": self.target, "block": self.block, "donor_set_block": self.key, "seed": self.seed, "strata": list(self.strata),
                "weights": [float(w) for w in self.weights], "n_segments": list(self.n_segments),
                "n_participants": {st.name: st.n_part for st in self._strata},
                "excluded_presentations": {s: len(_excluded(ds, s)) for s in self.strata},
                "montage_augmentation": {"p": C.AUG_P, "subsets": {k: len(v) for k, v in C.AUG_SUBSETS.items()},
                                         "cohorts": sorted(c for c, m in self._aug.items() if m)},
                "batch": {"segments": N_SEG, "anchors": C.N_ANCHORS, "views": 2},
                "xm": {"seed": self.seed + C.XM_SEED_OFFSET, "draws": XM_DRAWS, "rule": XM_RULE, "hard_weight": XM_W_HARD,
                       "twin_aware_partner": True, "condition_fields": list(COND_FIELDS)},
                "hc_hcv_excluded_pairs": self.manifest.get("hc_hcv_excluded_pairs"), "stream_hash_every": HASH_EVERY,
                "bank_roles": {c: list(b.roles) for c, b in self.banks.items()}, "banks": {c: b.describe() for c, b in self.banks.items()},
                "manifest_sha256": manifest_sha(self.manifest)}

    def selection_sets(self):
        return selection_sets(self.manifest)

    def bridge_rows(self):
        return bridge_rows(self.manifest, self.target, root=self.root)


# ---------------------------------------------------------------------------------------------------------- fixed sets
@dataclass(eq=False)
class SegmentSet:
    """Listener segments of one cohort's segment table (all 250 ticks are used: validation, bridge, temperature pools)."""
    cohort: str
    rows: np.ndarray
    piece: np.ndarray
    participant: np.ndarray
    presentation: np.ndarray
    family: np.ndarray
    s: np.ndarray
    fs0: np.ndarray                   # family-clock sample of the segment start
    role: np.ndarray
    montage: np.ndarray | None = None  # bridge rows: subset name or None per segment

    def __len__(self):
        return len(self.rows)

    def keys(self):
        """Packed keys of every tick: int64 [n, 250]."""
        return C.pack_key(self.family[:, None], self.presentation[:, None], self.fs0[:, None] + C.TICK_OFFS[None].astype(np.int64))

    def take(self, i):
        i = np.asarray(i, dtype=np.int64)
        return SegmentSet(self.cohort, self.rows[i], self.piece[i], self.participant[i], self.presentation[i], self.family[i], self.s[i],
                          self.fs0[i], self.role[i], None if self.montage is None else self.montage[i])


def segment_set(manifest, cohort, rows, montage=None):
    idx = manifest_index(manifest)
    S = idx.seg[cohort]
    rows = np.asarray([int(r) for r in rows], dtype=np.int64)
    if len(rows) and (rows.min() < 0 or rows.max() >= len(S["s"])):
        raise ValueError(f"segment rows outside the {cohort} segment table")
    if cohort == "sparrkulee" and set(map(str, S["participant"][rows])) & set(RESTRICTED):
        raise RestrictedAccess("a selection or bridge row of a restricted SparrKULee participant")
    pres = S["presentation"][rows]
    for p in set(pres.tolist()):
        ss = S["s"][rows[pres == p]]
        for a, b in idx.shared.get(p, ()):
            if ((a < ss + C.SPAN_EEG) & (ss < b)).any():
                raise ValueError(f"{cohort}: a selection / bridge segment of presentation {p} meets the shared-audio span [{a}, {b})")
    return SegmentSet(cohort, rows, S["piece"][rows], S["participant"][rows], pres, idx.fam[pres], S["s"][rows], idx.fs0(pres, S["s"][rows]),
                      S["role"][rows], None if montage is None else np.asarray(montage, dtype=object))


def excluded_anywhere(manifest, cohort="sparrkulee"):
    """{presentation: sorted ['<target>/<block>', ...]}: the presentations of `cohort` that any donor set of the manifest excludes
    (the C3 overlap exclusion of §3.4)."""
    out = {}
    for t, blocks in manifest["donor_sets"].items():
        for b, ds in blocks.items():
            for s, ps in (ds.get("excluded_presentations") or {}).items():
                if coh_of(s) == cohort:
                    for p in ps:
                        out.setdefault(int(p), set()).add(f"{t}/{b}")
    return {p: sorted(v) for p, v in out.items()}


def _check_shared_set(name, sset, excl):
    bad = sorted({int(p) for p in sset.presentation.tolist()} & set(excl))
    if bad:
        who = sorted({w for p in bad for w in excl[p]})
        raise ValueError(f"fixed SparrKULee set {name}: presentations {bad[:5]} are excluded (overlap with a target, §3.4) for donor "
                         f"sets {who}; the shared fixed sets (§3.2) must avoid every target's excluded presentations (§3.4.1, "
                         "inherited contract §2: target content leaves donor development and calibration too); C6 must redraw them")


def _unique_content(seg):
    """Unique (presentation, s) in first-occurrence order -> (position of each representative, content index of each segment)."""
    first, rep, own = {}, [], []
    for i, k in enumerate(zip(seg.presentation.tolist(), seg.s.tolist())):
        if k not in first:
            first[k] = len(rep); rep.append(i)
        own.append(first[k])
    return np.asarray(rep, dtype=np.int64), np.asarray(own, dtype=np.int64)


def _other_same_listener(q, own):
    """o(q): the next query of the same listener in (piece, s) order, cyclically, whose content differs; -1 if none."""
    out = np.full(len(q), -1, dtype=np.int64)
    by = {}
    for i, p in enumerate(q.participant.tolist()):
        by.setdefault(str(p), []).append(i)
    for idx in by.values():
        idx = sorted(idx, key=lambda i: (int(q.piece[i]), int(q.s[i])))
        for a, i in enumerate(idx):
            for b in range(1, len(idx)):
                j = idx[(a + b) % len(idx)]
                if own[j] != own[i]:
                    out[i] = own[j]
                    break
    return out


def selection_sets(manifest):
    """§2.10 / §2.11 fixed SparrKULee sets: the donor-fit validation segments, the dev queries with their candidates, own and
    gain-score other content, and the bridge_cal queries with the bridge_cal content candidates and the 2-fold participant split.
    Raises when a set touches a presentation that any donor set excludes (module docstring, Interpretations)."""
    idx = manifest_index(manifest)
    S, pools, sel, br = idx.seg["sparrkulee"], manifest["pools"], manifest["selection"], manifest["bridge"]
    fit = segment_set(manifest, "sparrkulee", sel["fit_segments"])
    dq = segment_set(manifest, "sparrkulee", sel["dev_queries"])
    cq = segment_set(manifest, "sparrkulee", br["cal_queries"])
    for name, sset, role, pool in (("fit", fit, "fit", pools["core"]["sparrkulee"]), ("dev", dq, "dev", pools["dev"]["sparrkulee"]),
                                   ("bridge_cal", cq, "bridge_cal", pools["bridge_cal"]["sparrkulee"])):
        if (sset.role != role).any() or not set(sset.rows.tolist()) <= {int(r) for r in pool}:
            raise ValueError(f"selection set {name}: rows outside the SparrKULee {role} pool")
    roles = {r: np.asarray([int(x) for x in pools[k]["sparrkulee"]], dtype=np.int64)
             for r, k in (("fit", "core"), ("dev", "dev"), ("bridge_cal", "bridge_cal"))}
    for a in roles:
        for b in roles:
            if a < b:
                pa, pb = set(map(str, S["participant"][roles[a]])), set(map(str, S["participant"][roles[b]]))
                fa, fb = set(S["family"][roles[a]].tolist()), set(S["family"][roles[b]].tolist())
                if pa & pb or fa & fb:
                    raise ValueError(f"SparrKULee roles {a} / {b} share participants {sorted(pa & pb)[:3]} or families {sorted(fa & fb)[:3]}")
    cal_pool = segment_set(manifest, "sparrkulee", pools["bridge_cal"]["sparrkulee"])
    if (cal_pool.role != "bridge_cal").any():
        raise ValueError("bridge_cal candidate pool contains rows outside its declared role")
    excl = excluded_anywhere(manifest, "sparrkulee")
    for name, sset in (("selection.fit_segments", fit), ("selection.dev_queries", dq), ("bridge.cal_queries", cq),
                       ("pools.bridge_cal (bridge_cal candidates)", cal_pool)):
        _check_shared_set(name, sset, excl)
    rep, own = _unique_content(dq)
    dev = {"queries": dq, "candidates": dq.take(rep), "own": own, "other": _other_same_listener(dq, own)}
    crep, _ = _unique_content(cal_pool)
    cand = cal_pool.take(crep)
    ck = {(int(p), int(s)): i for i, (p, s) in enumerate(zip(cand.presentation, cand.s))}
    cown = np.asarray([ck[(int(p), int(s))] for p, s in zip(cq.presentation, cq.s)], dtype=np.int64)
    split = [[str(p) for p in f] for f in br.get("cal_split", ())]
    qp = set(map(str, cq.participant))
    if len(split) != 2 or set(split[0]) & set(split[1]) or set(split[0]) | set(split[1]) != qp:
        raise ValueError(f"bridge cal_split {split} must be two disjoint folds covering the bridge_cal query participants {sorted(qp)}")
    fold = np.asarray([0 if str(p) in set(split[0]) else 1 for p in cq.participant], dtype=np.int64)
    return {"fit": fit, "dev": dev, "bridge_cal": {"queries": cq, "candidates": cand, "own": cown, "split": split, "fold": fold},
            "excluded_presentations_checked": len(excl)}


def bridge_rows(manifest, donor_set, root=None):
    """§2.11 bridge-fit rows of a donor set (manifest bridge.fit_rows[target], core strata; CSX slots use the same rows) with their
    seeded montage choices (SeedSequence([BRIDGE_SEED, BRIDGE_MONTAGE_TAG])), plus the bridge_cal sets of selection_sets().
    Defense in depth (the rows feed a target's bridge, never its own cohort): the core donor set is checked for leave-target-out
    as DonorSampler checks it, and the rows of every stratum meet the DonorSampler row rules (check_donor_rows, with the
    participants of the cohort table). The tables are read under root=, else the manifest's root: a caller that holds a cache
    root must pass it (module docstring; bridge.bridge_banks / fit_bridge). Without any root it raises ValueError (fail closed)."""
    target, key, ds = resolve_donor_set(manifest, donor_set, "core")
    check_leave_target_out(target, key, ds)
    idx = manifest_index(manifest)
    rows = manifest["bridge"]["fit_rows"][target]
    rng = np.random.default_rng(np.random.SeedSequence([C.BRIDGE_SEED, BRIDGE_MONTAGE_TAG]))
    by, order, pool, aug64 = {}, [], {}, {c: bool(montage_masks(manifest["cohorts"][c]["layout"])) for c in manifest["cohorts"]}
    for stratum, r in rows:
        stratum, r = str(stratum), int(r)
        c = coh_of(stratum)
        if stratum not in ds["strata"] or stratum == "fau_cs":
            raise ValueError(f"bridge row stratum {stratum} is not a core stratum of target {target}")
        S = idx.seg[c]
        if stratum not in pool:
            excl = set(_excluded(ds, stratum))
            pool[stratum] = {int(x) for x in manifest["pools"]["core"][c] if int(S["presentation"][int(x)]) not in excl}
        if r not in pool[stratum]:
            raise ValueError(f"bridge row {stratum}:{r} is not an eligible donor-fit row of target {target}")
        u, m = float(rng.random()), int(rng.integers(0, len(AUG_NAMES)))
        aug = aug64[c] and u < C.AUG_P
        by.setdefault(stratum, ([], [])); by[stratum][0].append(r); by[stratum][1].append(AUG_NAMES[m] if aug else None)
        order.append((stratum, r, AUG_NAMES[m] if aug else None))
    parts = {}
    for stratum, (rr, _) in by.items():                    # the DonorSampler row rules on the bridge rows (defense in depth)
        c = coh_of(stratum)
        if c not in parts:
            try:
                root = manifest_root(manifest, root)
            except ValueError:
                raise ValueError(f"bridge_rows({target}): the cache root is unknown; the participant rules read the donor cohorts' "
                                 "tables, so pass root= (bridge.bridge_banks / fit_bridge hold it) or open the manifest with "
                                 "views.open_manifest") from None
            table, items = cohort_table(manifest, c, root)
            _guard_restricted(c, items, idx.seg[c])
            parts[c] = {str(p["participant"]): p for p in table["participants"]}
        check_donor_rows(idx, stratum, c, rr, parts[c], set(_excluded(ds, stratum)))
    fit = {s: segment_set(manifest, coh_of(s), v[0], montage=v[1]) for s, v in by.items()}
    return {"target": target, "strata": [s for s in ds["strata"] if s in fit], "fit": fit, "order": order, "n_fit_rows": len(rows),
            "cal": selection_sets(manifest)["bridge_cal"], "montage_seed": [C.BRIDGE_SEED, BRIDGE_MONTAGE_TAG]}
