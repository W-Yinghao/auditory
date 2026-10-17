"""E34_PUBLIC_PRIOR queue dependencies: upstreams, plan checks, readiness, blocking, checkpoint owners, queue order and the
prior queue files.

PUBLIC_PRIOR_DESIGN.md §4.1 (dependencies, tiers, weights), §2.10 (horizon, continuation), §6.1 / §6.6 M8 (deps.py) and §6.5
(queue lines and counters). Light (stdlib json/os/re/collections.abc) and NOT part of any code hash: make_queue.py imports it
for write_queue (the refresher rebuilds the queue every 10 min) and ckpt_offload.py for ckpt_deps. Slots, the lambda rule, the
compute limit and every file name come from select.py; names_limit (whether a row names its compute limit, a queue-side plan
check only) lives here, so a later change of it re-hashes no family (select.py is hashed into all five prior33 code groups; its
regex is copied as _LIMIT, which the tests compare with select's).

`rows` is a sequence or any other iterable of plan rows (materialised once, so a generator or itertools.chain(plan, new) is
read exactly once), or a dict experiment_id -> row (index(rows)). Nothing is cached between calls: a list is indexed on every
call (about 1 ms per 10^4 rows); a caller that runs many rows against one plan (ckpt_offload.deps_of: its `by`, or
deps.index(rows) built once per pass) passes the dict instead.

Upstreams (direct, in order): the experiment ids among the row's logical_dependencies (other strings are symbolic tokens, e.g.
the frozen manifest or the rich cache, and are skipped; a token that starts like an id, "ALN3_" or "ALN3X_" in any case, must
be a well-formed id), then the id fields of its spec: donor groups spec.horizon_from and spec.continuation_of; bridge and
target rows spec.donor_group; zero-shot rows spec.donor_group and spec.bridge. In a bridge row spec.bridge is the method name;
on bridge, target and zero-shot rows spec.continuation_of and spec.version are version labels (prior33.analysis), never
upstreams. Every upstream must be a row of `rows` (ValueError otherwise; a self-dependency or a cycle is a ValueError too).

Plan consistency (check_row, check_plan; write_queue applies it to every prior row before writing anything). Pinned here from
§2.6, §2.10, §2.13, §2.15, §2.16 and §4.1-§4.3; make_plan_ext_prior33.py (M9) runs check_plan on the plan plus its new rows:
  every row     spec.block one of BLOCK_TIER; spec.queue_tier, when present, the block's tier; every upstream a prior row; the
                dataset a target cohort (TARGETS), private_bdf in block panel (§4.1: the panel is private_bdf only); seeds (§4.3;
                a field that is absent or null is not compared): the row seed is spec.target_seed on a target row and
                spec.donor_seed on any other row, spec.sampler_seed = spec.donor_seed, and spec.target_seed is null on donor-group,
                bridge and zero-shot rows
  plan level    (check_plan and write_queue only: properties of several rows) unique prior experiment ids, one bridge row per
                slot (§2.11: one bridge per slot), no dependency cycle
  donor group   DONOR in block core or panel, RICH_DONOR in rich, CSX_DONOR in csx, the CSX group only for a CSX target
                (CSX_TARGETS, §2.16, §4.1: none for fau); spec.members the family's §2.6 set (absent or null: the family default;
                an empty list is refused, not read as the default); spec.lambda_rule (when present) select.LAMBDA_RULE. Its
                upstreams are donor groups named by
                  spec.horizon_from      required for RICH_DONOR and CSX_DONOR (continuations included) and refused for DONOR:
                                         a DONOR group of the same (dataset, spec.objective, seed); the row adopts its H*
                  spec.continuation_of   optional: a group of the same family, block, (dataset, objective, seed) and members,
                                         whose retained stable states the row resumes from; the row then names its own compute
                                         limit in spec.budget.continuation, above the source's (select.compute_limit)
                and nothing else (a donor-group upstream named by neither field is refused, not guessed). The horizon group
                belongs to the row's own execution version: the same compute limit and continuation depth, and a continuation
                adopts the continuation of its source's horizon group (§2.10, §2.15, §2.16: equal updates)
  versions      the continuation depth of a group is the number of spec.continuation_of links behind it; spec.version is the
                one version label (version_label): absent on a primary group and on its bridge, target and zero-shot rows,
                'continuation_<depth>' on a continuation group and on each of its slot rows (as make_plan_ext_prior33.py
                --continuation writes it; prior33.analysis derives the same names). spec.execution_version is refused. On a slot
                row spec.continuation_of is a label: refused on rows of a primary group, and when present on a row of a
                continuation group it names the row continued (same family, slot name and cell, on the group's source)
  slot row      a bridge / target / zero-shot row with a slot: the slot's group trains the slot's member(s) (select.group_row);
                the slot is never a lambda candidate (J1, J025: rows name J*, which the lambda rule resolves); a spec.variant
                that is a slot or member name names the same slot as spec.member (select reads member first, the runners and
                prior33.analysis the slot; other variant strings, such as the §2.13 zero-shot names, are descriptive); the row
                has the group's dataset and spec.objective, and its donor seed (bridge and zero-shot rows: row seed;
                spec.donor_seed, when present, on every slot row). Block by the group's block: core -> bridge, target core,
                zero-shot core (mode A) or access (modes B, C, C_partial; slots AP, XP, J* only: ACCESS_SLOTS); panel ->
                bridge, target panel; rich -> rich; csx -> csx. Upstreams exactly: bridge and target the group; zero-shot the
                group and spec.bridge (required, a bridge row of the same slot). A zero-shot row's spec.mode (as
                prior33.analysis reads it) and its dataset are a pair of ZS_COHORTS (= contract.ZS_COHORTS)
  from scratch  a target without a slot: block core or panel, no upstreams, always primary (no version label, no
                spec.continuation_of); a spec.variant that is a slot or member name is S

ready(row) = every upstream has units/<up>.json and the files the row reads from it exist:
  bridge / target / zero-shot <- its donor group   ckpt/<gid>_m<M>_best.pt, M = select.member_of (J* by the lambda rule)
  zero-shot                   <- its bridge        ckpt/<bid>_bridge.npz
  rich donor group            <- horizon_from      ckpt/<core>_mAP_best.pt (donor-side readout) and the record (H*)
  CSX donor group             <- horizon_from      the record only (H*)
  continuation donor group    <- continuation_of   select.retained_states(source): ckpt/<src>_m<M>_stable<L-3>.pt for every
                                                   source member, L = select.compute_limit(source)

Queue states (exclusive, in this order): done (units/<eid>.json exists), failed (pool/queue_v3_prior/<eid>.failed, the pool's
terminal marker, and no record), blocked (an upstream is failed, transitively through upstreams that are not done), ready,
waiting (everything else: an upstream record is missing, a file the row reads is missing, or a complete group record cannot
resolve J*, the last also reported as 'unresolved'). remaining = ready + waiting (running rows count as ready); blocked rows
count neither as waiting nor as remaining (§6.5, risk 15). Neither blocked nor unresolved rows are listed in
queue_v3_prior.txt (write_queue), so no worker can claim them.
"""
from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping

from . import select as S

QUEUE = "queue_v3_prior"
EXT_OFFSET = 100000  # run.py: a queue index >= 100000 addresses row (index - 100000) of plan_ext.jsonl
EID = re.compile(r"^ALN3X?_[0-9a-f]{16}$")
ID_LIKE = re.compile(r"^aln3x?_", re.IGNORECASE)  # a dependency token starting like this must be a well-formed id (EID)
# §4.1 queue weights (GB of the worker's memory budget CAP); the probe (§7.2 item 8) may reset them here (file not hashed)
WEIGHTS = {S.DONOR: 8, S.CSX_DONOR: 8, S.RICH_DONOR: 8, S.BRIDGE: 6, S.TARGET: 3, S.ZEROSHOT: 2}
STAGE_RANK = {"donor_group": 0, "bridge": 1, "target": 2, "zero_shot": 3}
BLOCK_TIER = {"core": 1, "access": 2, "panel": 3, "rich": 4, "csx": 4}  # §4.1 (tiers: a resource order, not gates)
GROUP_BLOCKS = {S.DONOR: ("core", "panel"), S.RICH_DONOR: ("rich",), S.CSX_DONOR: ("csx",)}
SLOT_BLOCKS = {("core", "bridge"): ("core",), ("core", "target"): ("core",), ("core", "zero_shot"): ("core", "access"),
               ("panel", "bridge"): ("panel",), ("panel", "target"): ("panel",),
               ("rich", "bridge"): ("rich",), ("rich", "target"): ("rich",), ("rich", "zero_shot"): ("rich",),
               ("csx", "bridge"): ("csx",), ("csx", "target"): ("csx",), ("csx", "zero_shot"): ("csx",)}  # (group block, stage)
SCRATCH_BLOCKS = ("core", "panel")
ACCESS_SLOTS = ("AP", "XP", S.JOINT)  # §4.1: the access block's zero-shot rows (modes B, C, C_partial) cover AP, XP and J* only
TARGETS = ("fau", "dtu", "federici", "private_bdf")  # §3.3, §4.1: the target cohorts (every row's dataset)
CSX_TARGETS = ("dtu", "federici", "private_bdf")  # §2.16, §4.1: CSX groups (no CSX group for fau: fau_cs is its own cohort)
PANEL_DATASET = "private_bdf"  # §4.1: the panel block is private_bdf only
_LIMIT = re.compile(r"limit(\d+)")  # copy of select._LIMIT (select.compute_limit's parse; the test compares the patterns)
# zero-shot access modes (§2.13); copies of contract.ZS_SUFFIX / ZS_COHORTS (contract.py needs numpy; the test compares them)
ZS_SUFFIX = {"A": "__fixed_input_preprocessing", "B": "__fau_noica_target_z", "C": "__source_statistics_only",
             "C_partial": "__source_statistics_partial"}
ZS_COHORTS = {"A": ("fau", "dtu", "federici"), "B": ("fau",), "C": ("fau", "dtu"), "C_partial": ("federici",)}
_MODE_ALIASES = {"a": "A", "b": "B", "c": "C", "c_partial": "C_partial", "c-partial": "C_partial", "cpartial": "C_partial"}
# spec fields holding upstream ids, per stage (§4.3; a bridge row's spec.bridge is the method name, not an id)
REF_FIELDS = {"donor_group": ("horizon_from", "continuation_of"), "bridge": ("donor_group",), "target": ("donor_group",),
              "zero_shot": ("donor_group", "bridge")}
COUNTERS = (".remaining", ".waiting", ".blocked")  # queue_v3_prior.<counter>: never *.txt (offload glob queue_v3_*.txt)


def _rows(rows):
    """`rows` as the public functions read it: a dict, list or tuple as given (another mapping copied into a dict), any other
    iterable materialised once as a list, so a generator or another one-shot iterable is read exactly once (M8 review:
    check_plan and write_queue read it twice and saw nothing the second time)."""
    if isinstance(rows, (dict, list, tuple)):
        return rows
    if isinstance(rows, Mapping):
        return dict(rows)
    if rows is None or isinstance(rows, (str, bytes)):
        raise TypeError(f"rows: plan rows (a sequence or iterable) or a mapping experiment_id -> row, not {type(rows).__name__}")
    return list(rows)


def index(rows):
    """experiment_id -> row (the first row of each id); a dict is returned as it is (no copy, no pass over it)."""
    rows = _rows(rows)
    if isinstance(rows, dict):
        return rows
    by = {}
    for r in rows:
        by.setdefault(r["experiment_id"], r)
    return by


def _seq(rows):
    return list(rows.values()) if isinstance(rows, dict) else list(rows)


def _prior(row):
    return row.get("family_id") in S.FAMILIES


def _upstreams(by, row):
    e, s = row["experiment_id"], row.get("spec") or {}
    deps = row.get("logical_dependencies") or []
    if not isinstance(deps, (list, tuple)):
        raise ValueError(f"{e}: logical_dependencies {deps!r} is not a list")
    cand = []
    for u in deps:
        if not isinstance(u, str):
            raise ValueError(f"{e}: logical dependency {u!r} is not a string")
        if EID.match(u):
            cand.append(u)
        elif ID_LIKE.match(u):
            raise ValueError(f"{e}: logical dependency {u!r} starts like an experiment id but is not one")
    for k in (REF_FIELDS[S.stage_of(row)] if _prior(row) else ()):
        v = s.get(k)
        if v is None:
            continue
        if not (isinstance(v, str) and EID.match(v)):
            raise ValueError(f"{e}: spec.{k} = {v!r} is not an experiment id")
        cand.append(v)
    ups = []
    for u in cand:
        if u == e:
            raise ValueError(f"{e}: the row depends on itself")
        if u not in by:
            raise ValueError(f"{e}: upstream {u} is not a plan row")
        if u not in ups:
            ups.append(u)
    return ups


def upstreams(row, rows):
    """Direct upstream experiment ids of `row` (module docstring)."""
    return list(_upstreams(index(rows), row))


def names_limit(group):
    """True when the row's spec.budget.continuation names its compute limit explicitly ("..._limit<L>_...", the number that
    select.compute_limit reads); the continuation check requires it. Kept here, not in select.py (module docstring)."""
    return _LIMIT.search(str(((group.get("spec") or {}).get("budget") or {}).get("continuation") or "")) is not None


def version_label(depth):
    """The spec.version label of a donor group of continuation depth `depth` (the number of spec.continuation_of links behind
    it) and of its slot rows: None for a primary group (no label), 'continuation_<depth>' otherwise, as
    make_plan_ext_prior33.py --continuation writes it and prior33.analysis names the execution versions."""
    return None if depth == 0 else f"continuation_{depth}"


def _depth(by, g):
    """Continuation depth of donor-group row g: the number of spec.continuation_of links behind it (each a donor-group plan row);
    ValueError on a cycle or a link that is not a donor-group row of `by`."""
    d, seen = 0, set()
    while True:
        e = g["experiment_id"]
        seen.add(e)
        c = (g.get("spec") or {}).get("continuation_of")
        if c is None:
            return d
        nxt = by.get(c) if isinstance(c, str) else None
        if nxt is None or not _prior(nxt) or S.stage_of(nxt) != "donor_group":
            raise ValueError(f"{e}: continuation source {c!r} is not a donor-group plan row")
        if c in seen:
            raise ValueError(f"dependency cycle through {c} (spec.continuation_of)")
        g, d = nxt, d + 1


class _Ctx:
    """One memoised filesystem view of `out` for a pass over the plan."""

    def __init__(self, rows, out):
        self.by, self.out, self.m = index(rows), out, {}
        self.pool = os.path.join(out, "pool", QUEUE)

    def _memo(self, key, fn):
        if key not in self.m:
            self.m[key] = fn()
        return self.m[key]

    def done(self, e):
        return self._memo(("done", e), lambda: os.path.exists(S.record_path(self.out, e)))

    def failed(self, e):  # a complete record wins over a stale marker
        return self._memo(("failed", e), lambda: not self.done(e) and os.path.exists(os.path.join(self.pool, f"{e}.failed")))

    def exists(self, p):
        return self._memo(("file", p), lambda: os.path.exists(p))

    def record(self, e):
        return self._memo(("rec", e), lambda: S.load_record(self.out, e))

    def ups(self, row):
        return self._memo(("ups", row["experiment_id"]), lambda: _upstreams(self.by, row))


def relation(row, up):
    """How a donor-group row uses a donor-group upstream, from the explicit fields only: 'continuation' when the upstream is
    spec.continuation_of (the row resumes from its retained stable states), 'horizon' when it is spec.horizon_from (the row
    adopts its realised H*). ValueError for a donor-group upstream named by neither field."""
    s, u = row.get("spec") or {}, up["experiment_id"]
    if u == s.get("continuation_of"):
        return "continuation"
    if u == s.get("horizon_from"):
        return "horizon"
    raise ValueError(f"{row['experiment_id']}: donor-group upstream {u} is neither spec.continuation_of nor spec.horizon_from")


def zero_shot_mode(row):
    """Canonical zero-shot mode A | B | C | C_partial of spec.mode: a short name, an alias or the full §2.13 name (as
    prior33.analysis.canon_mode reads it); ValueError otherwise."""
    m = (row.get("spec") or {}).get("mode")
    s = m.strip() if isinstance(m, str) else None
    if s in ZS_SUFFIX:
        return s
    if s is not None and s.lower() in _MODE_ALIASES:
        return _MODE_ALIASES[s.lower()]
    for k, suf in ZS_SUFFIX.items():
        if s is not None and s.endswith(suf):
            return k
    raise ValueError(f"{row.get('experiment_id')}: zero-shot spec.mode {m!r} is not one of {list(ZS_SUFFIX)} (§2.13)")


def _needs(ctx, row, u):
    """Files that `row` reads from its complete upstream `u`. Raises select.SelectionError when J* cannot be resolved."""
    up = ctx.by[u]
    if not (_prior(row) and _prior(up)):
        return []
    st, su = S.stage_of(row), S.stage_of(up)
    if st != "donor_group":
        if su == "donor_group":
            sl = S.slot_of(row)
            return [] if sl is None or sl[0] != u else [S.member_ckpt(ctx.out, u, S.member_of(row, ctx.record(u)))]
        return [S.bridge_npz(ctx.out, u)] if su == "bridge" and st == "zero_shot" else []
    if su != "donor_group":
        return []
    if relation(row, up) == "horizon":  # rich: the core AP checkpoint for the donor-side readout (§2.15); CSX: the record only
        return [S.member_ckpt(ctx.out, u, "AP")] if row["family_id"] == S.RICH_DONOR else []
    return S.retained_states(ctx.out, up)  # continuation: resume from the source's retained stable states (§2.10)


def _same(a, b, what):
    """(dataset, spec.objective, seed) of two rows agree; ValueError naming `what` otherwise."""
    ka = (a.get("dataset"), (a.get("spec") or {}).get("objective"), a.get("seed"))
    kb = (b.get("dataset"), (b.get("spec") or {}).get("objective"), b.get("seed"))
    if ka != kb:
        raise ValueError(f"{a['experiment_id']}: {what} {b['experiment_id']} has (dataset, objective, seed) {kb}, the row {ka}")


def _check_donor(ctx, row, ups):
    e, s, fam = row["experiment_id"], row.get("spec") or {}, row["family_id"]
    if isinstance(s.get("members"), (list, tuple)) and not s["members"]:
        raise ValueError(f"{e}: spec.members is empty; a group lists the members it trains, or leaves the field out for the "
                         f"family's §2.6 set {list(S.GROUP_MEMBERS[fam])} (select reads [] as that default)")
    ms = S.group_members(row)
    if set(ms) != set(S.GROUP_MEMBERS[fam]):
        raise ValueError(f"{e}: members {list(ms)}; every {fam} group trains {list(S.GROUP_MEMBERS[fam])} (§2.6)")
    if s["block"] not in GROUP_BLOCKS[fam]:
        raise ValueError(f"{e}: {fam} groups belong to block {'/'.join(GROUP_BLOCKS[fam])}, not {s['block']!r} (§4.1)")
    if fam == S.CSX_DONOR and row.get("dataset") not in CSX_TARGETS:
        raise ValueError(f"{e}: a CSX group for {row.get('dataset')!r}; CSX groups exist for {list(CSX_TARGETS)} only (§2.16, §4.1: "
                         "none for fau, whose own cohort the fau_cs stratum is)")
    cont, hor = s.get("continuation_of"), s.get("horizon_from")
    if cont is not None and cont == hor:
        raise ValueError(f"{e}: spec.continuation_of and spec.horizon_from name the same group {cont}")
    if fam == S.DONOR and hor is not None:
        raise ValueError(f"{e}: {S.DONOR} groups run their own horizon trigger; spec.horizon_from {hor} is refused (§2.10)")
    if fam != S.DONOR and hor is None:
        raise ValueError(f"{e}: {fam} groups adopt the realised horizon H* of a {S.DONOR} group: spec.horizon_from is required "
                         f"(§2.10, §2.15, §2.16, §4.3)")
    for u in ups:
        up = ctx.by[u]
        if S.stage_of(up) != "donor_group":
            raise ValueError(f"{e}: upstream {u} is a {S.stage_of(up)} row; a donor group depends only on donor groups")
        rel = relation(row, up)
        S.group_members(up)
        _same(row, up, f"{rel} source")
        if rel == "horizon":
            if up["family_id"] != S.DONOR:
                raise ValueError(f"{e}: horizon group {u} is a {up['family_id']} row (expected {S.DONOR})")
            _check_horizon_version(ctx, row, up)
            continue
        if up["family_id"] != fam:
            raise ValueError(f"{e}: continuation source {u} is a {up['family_id']} row (expected {fam})")
        if (up.get("spec") or {}).get("block") != s["block"]:
            raise ValueError(f"{e}: a continuation in block {s['block']!r} of the {(up.get('spec') or {}).get('block')!r}-block group "
                             f"{u}; a continuation is registered in its source's block (§2.10, §4.1)")
        if set(S.group_members(up)) != set(ms):
            raise ValueError(f"{e}: continuation source {u} trains {list(S.group_members(up))}, the row {list(ms)}")
        if not names_limit(row) or S.compute_limit(row) <= S.compute_limit(up):
            raise ValueError(f"{e}: a continuation names its own compute limit in spec.budget.continuation ('..._limit<L>_...'), "
                             f"above its source's {S.compute_limit(up)} ep-eq")
    _check_label(row, version_label(_depth(ctx.by, row)), "this group")


def _check_horizon_version(ctx, row, up):
    """A rich / CSX group adopts the H* of the core group of its own execution version (§2.10, §2.15, §2.16: the paired
    contrasts with the core members are at equal updates): the same compute limit and continuation depth, and a continuation
    takes the continuation of its source's horizon group (M8 review)."""
    e, u, cont = row["experiment_id"], up["experiment_id"], (row.get("spec") or {}).get("continuation_of")
    lr, lu = S.compute_limit(row), S.compute_limit(up)
    if lr != lu:
        raise ValueError(f"{e}: horizon group {u} has compute limit {lu} ep-eq, the row {lr}: a group adopts the H* of the core "
                         "group of its own execution version (§2.10, §2.15, §2.16)")
    dr, du = _depth(ctx.by, row), _depth(ctx.by, up)
    if dr != du:
        raise ValueError(f"{e}: horizon group {u} is {version_label(du) or 'primary'}, the row {version_label(dr) or 'primary'}: a "
                         "group adopts the H* of the core group of its own execution version (§2.10, §2.15, §2.16)")
    if cont is not None:
        want = (ctx.by[cont].get("spec") or {}).get("horizon_from")  # spec.continuation_of is an upstream, so it is a row
        got = (up.get("spec") or {}).get("continuation_of")
        if got != want:
            raise ValueError(f"{e}: a continuation adopts the H* of the continuation of its source's horizon group {want}; horizon "
                             f"group {u} continues {got}")


def _check_label(row, want, whose):
    """spec.version is the one version label (§2.10, M8 review): `want` (version_label of the group's depth) on the row, no
    label on a primary row; spec.execution_version is refused (prior33.analysis would read it as a second label)."""
    e, s = row["experiment_id"], row.get("spec") or {}
    if s.get("execution_version") is not None:
        raise ValueError(f"{e}: spec.execution_version is not used; the version label is spec.version")
    if s.get("version") != want:
        raise ValueError(f"{e}: spec.version {s.get('version')!r}, but {whose} is {'primary (no label)' if want is None else repr(want)} "
                         "(a continuation of depth k and its bridge, target and zero-shot rows are labelled 'continuation_<k>'; "
                         "primary rows carry no label; §2.10)")


def _check_slot_row(ctx, row, ups):
    e, st, s = row["experiment_id"], S.stage_of(row), row.get("spec") or {}
    blk = s["block"]
    sl = S.slot_of(row)
    _check_variant(row, S.SCRATCH if sl is None else sl[1])
    if sl is None:  # target_from_scratch
        if ups:
            raise ValueError(f"{e}: a from-scratch target reads no other unit, but lists upstreams {ups}")
        if blk not in SCRATCH_BLOCKS:
            raise ValueError(f"{e}: a from-scratch target belongs to block core or panel, not {blk!r} (§4.1)")
        if s.get("continuation_of") is not None:
            raise ValueError(f"{e}: a from-scratch target is never re-registered by a continuation (§2.10): spec.continuation_of "
                             f"{s['continuation_of']!r}")
        _check_label(row, None, "a from-scratch target")
        return
    if sl[1] in S.JOINT_CANDIDATES:
        raise ValueError(f"{e}: slot member {sl[1]} is a lambda candidate: bridge, target and zero-shot rows name {S.JOINT}, which "
                         f"select.member_of resolves by {S.LAMBDA_RULE} (§2.9, §4.1)")
    g = S.group_row(row, ctx.by)  # the slot's group trains the slot's member(s); members and lambda rule checked
    gid, gblk = g["experiment_id"], (g.get("spec") or {}).get("block")
    allowed = SLOT_BLOCKS.get((gblk, st), ())
    if not allowed:
        raise ValueError(f"{e}: the {gblk!r}-block group {gid} has no {st} rows (§4.1)")
    if blk not in allowed:
        raise ValueError(f"{e}: {st} rows of the {gblk!r}-block group {gid} belong to block {'/'.join(allowed)}, not {blk!r} (§4.1)")
    if blk == "access" and sl[1] not in ACCESS_SLOTS:
        raise ValueError(f"{e}: access-block zero-shot rows cover the slots {list(ACCESS_SLOTS)} only, not {sl[1]} (§4.1)")
    _check_label(row, version_label(_depth(ctx.by, g)), f"its group {gid}")
    _check_continued_row(ctx, row, sl, g)
    if row.get("dataset") != g.get("dataset") or s.get("objective") != (g.get("spec") or {}).get("objective"):
        raise ValueError(f"{e}: (dataset, objective) ({row.get('dataset')}, {s.get('objective')}) differs from its group {gid}'s")
    dseed = s.get("donor_seed")
    if (st != "target" and row.get("seed") != g.get("seed")) or (dseed is not None and dseed != g.get("seed")):
        raise ValueError(f"{e}: donor seed (row seed {row.get('seed')}, spec.donor_seed {dseed}) differs from its group {gid}'s seed "
                         f"{g.get('seed')}")
    need = [gid]
    if st == "zero_shot":
        b = s.get("bridge")
        if b is None:
            raise ValueError(f"{e}: spec.bridge (the bridge row of the slot) is required on a zero-shot row (§4.3)")
        br = ctx.by[b]  # spec.bridge is an upstream, so it is a row
        if not _prior(br) or S.stage_of(br) != "bridge" or S.slot_of(br) != sl:
            raise ValueError(f"{e}: spec.bridge {b} is not a bridge row of the slot {sl}")
        need.append(b)
        mode = zero_shot_mode(row)
        if (blk == "access") != (mode != "A"):
            raise ValueError(f"{e}: zero-shot mode {mode} in block {blk!r}: mode A rows belong to core / rich / csx, modes B, C and "
                             f"C_partial to access (§4.1)")
        if row.get("dataset") not in ZS_COHORTS[mode]:
            raise ValueError(f"{e}: zero-shot mode {mode} is defined for {list(ZS_COHORTS[mode])}, not {row.get('dataset')!r} (§2.13)")
    extra = [u for u in ups if u not in need]
    if extra:
        raise ValueError(f"{e}: unexpected upstream(s) {extra}; a {st} row reads only {need}")


def _check_variant(row, name):
    """A spec.variant that is a slot or member name (select.canonical_slot) must name `name`, the slot the row resolves to
    (S for a from-scratch target): select.slot_of reads spec.member first, so a disagreeing variant would label the unit as one
    arm while it loads another (M8 review (h); target_train.check_row refuses the same at run time). A variant that is no slot
    name (the §2.13 zero-shot names, a descriptive name) is not compared."""
    v = (row.get("spec") or {}).get("variant")
    try:
        cv = S.canonical_slot(v) if isinstance(v, str) else None
    except ValueError:
        cv = None
    if cv is not None and cv != name:
        raise ValueError(f"{row['experiment_id']}: spec.variant {v!r} names another slot than the row's {name!r} (spec.member "
                         f"{(row.get('spec') or {}).get('member')!r}); variant and member must agree (§4.3)")


def _check_seeds(row):
    """§4.3 seed fields of one row (module docstring): the row seed is spec.target_seed on a target row and spec.donor_seed on
    any other row, spec.sampler_seed = spec.donor_seed, and spec.target_seed is null where not applicable (donor-group, bridge
    and zero-shot rows). Absent or null fields are not compared; a slot row's donor seed is compared with its group's in
    _check_slot_row (M8 review (f))."""
    e, s, st, seed = row["experiment_id"], row.get("spec") or {}, S.stage_of(row), row.get("seed")
    ds, ss, ts = s.get("donor_seed"), s.get("sampler_seed"), s.get("target_seed")
    if st == "target":
        if ts is not None and ts != seed:
            raise ValueError(f"{e}: spec.target_seed {ts!r} differs from the row seed {seed!r} (§4.3: a target row's seed is its "
                             "target_seed)")
    else:
        if ts is not None:
            raise ValueError(f"{e}: spec.target_seed {ts!r} on a {st} row (§4.3: null where not applicable)")
        if ds is not None and ds != seed:
            raise ValueError(f"{e}: spec.donor_seed {ds!r} differs from the row seed {seed!r} (§4.3: a {st} row's seed is its "
                             "donor_seed)")
    if ss is not None and ss != ds:
        raise ValueError(f"{e}: spec.sampler_seed {ss!r} differs from spec.donor_seed {ds!r} (§4.3: sampler_seed = donor_seed)")


def _check_continued_row(ctx, row, sl, g):
    """spec.continuation_of on a bridge / target / zero-shot row is a label (never an upstream): refused on a row of a primary
    group; on a row of a continuation group, when present, it names the row this one continues, i.e. the row of the same
    family, slot name and cell (dataset, folds; zero-shot: mode) on the group's continuation source."""
    e, lab = row["experiment_id"], (row.get("spec") or {}).get("continuation_of")
    if lab is None:
        return
    src = (g.get("spec") or {}).get("continuation_of")
    if src is None:
        raise ValueError(f"{e}: spec.continuation_of {lab!r} on a row of the primary group {g['experiment_id']} (a label of "
                         "continuation rows only; §2.10)")
    prev = ctx.by.get(lab) if isinstance(lab, str) else None
    same = prev is not None and _prior(prev) and prev.get("family_id") == row["family_id"] and S.slot_of(prev) == (src, sl[1]) and \
        all(prev.get(k) == row.get(k) for k in ("dataset", "subject_fold", "content_fold")) and \
        (S.stage_of(row) != "zero_shot" or zero_shot_mode(prev) == zero_shot_mode(row))
    if not same:
        raise ValueError(f"{e}: spec.continuation_of {lab!r} is not the {S.stage_of(row)} row of slot ({src}, {sl[1]}) and of the same "
                         "cell that this row continues (§2.10)")


def _check(ctx, row):
    tier_of(row)  # a known block, and spec.queue_tier (when present) agrees with it
    weight_of(row)
    e, ds = row["experiment_id"], row.get("dataset")
    if ds not in TARGETS:
        raise ValueError(f"{e}: dataset {ds!r} is not a target cohort {list(TARGETS)} (§3.3, §4.3: a row's dataset is its target)")
    if (row.get("spec") or {}).get("block") == "panel" and ds != PANEL_DATASET:
        raise ValueError(f"{e}: a panel-block row for {ds!r}; the panel block is {PANEL_DATASET} only (§4.1)")
    _check_seeds(row)
    ups = ctx.ups(row)
    for u in ups:
        if not _prior(ctx.by[u]):
            raise ValueError(f"{row['experiment_id']}: upstream {u} is a {ctx.by[u].get('family_id')} row, not an E34_PUBLIC_PRIOR row")
    if S.stage_of(row) == "donor_group":
        _check_donor(ctx, row, ups)
    else:
        _check_slot_row(ctx, row, ups)


def check_row(row, rows):
    """Plan consistency of one prior row against its upstream rows (module docstring); ValueError on the first problem. The
    plan-level properties (unique ids, one bridge row per slot, no cycle) need the whole plan: check_plan / write_queue."""
    _check(_Ctx(_rows(rows), "."), row)


def _topo(ctx, rows):
    """Prior rows with their prior upstreams first; ValueError on a dependency cycle."""
    state, order = {}, []
    for r0 in rows:
        if r0["experiment_id"] in state:
            continue
        state[r0["experiment_id"]] = 1
        stack = [(r0, iter(ctx.ups(r0)))]
        while stack:
            node, it = stack[-1]
            for u in it:
                ur = ctx.by[u]
                if not _prior(ur):
                    continue
                if state.get(u) == 1:
                    raise ValueError(f"dependency cycle through {u}")
                if u not in state:
                    state[u] = 1
                    stack.append((ur, iter(ctx.ups(ur))))
                    break
            else:
                stack.pop()
                state[node["experiment_id"]] = 2
                order.append(node)
    return order


def _check_all(ctx, seq):
    prior = [r for r in seq if _prior(r)]
    pids = {r["experiment_id"] for r in prior}
    count = {}
    for r in seq:
        if r.get("experiment_id") in pids:
            count[r["experiment_id"]] = count.get(r["experiment_id"], 0) + 1
    dup = sorted(e for e, c in count.items() if c > 1)
    if dup:
        raise ValueError(f"{len(dup)} prior experiment ids occur more than once in rows (first {dup[0]})")
    for r in prior:
        _check(ctx, r)
    bridges = {}
    for r in prior:  # one bridge per slot (§2.11): a second bridge row of a slot is a second fit of the same bridge
        if S.stage_of(r) == "bridge":
            bridges.setdefault(S.slot_of(r), []).append(r["experiment_id"])
    two = sorted((k, v) for k, v in bridges.items() if len(v) > 1)
    if two:
        (gid, name), ids = two[0]
        raise ValueError(f"slot ({gid}, {name}) has {len(ids)} bridge rows {ids}: one bridge per slot (§2.11, §4.1); {len(two)} "
                         "slot(s) affected")
    return _topo(ctx, prior)


def check_plan(rows):
    """check_row for every prior row of `rows`, unique prior ids (across all rows) and no dependency cycle; ValueError on the
    first problem. Returns the prior rows with their upstreams first. make_plan_ext_prior33.py (M9) runs it on the existing
    plan plus its new rows before appending them; `rows` may be any iterable (itertools.chain(plan, new) is read once)."""
    rows = _rows(rows)
    return _check_all(_Ctx(rows, "."), _seq(rows))


def _ready(ctx, row):
    for u in ctx.ups(row):
        if not ctx.done(u):
            return False
        for p in _needs(ctx, row, u):
            if not ctx.exists(p):
                return False
    return True


def ready(row, rows, out):
    """True when every upstream record is complete and every checkpoint / npz the row reads from it exists (module
    docstring). Says nothing about the row itself (done, failed, claimed) and assumes check_row passed. Raises
    select.SelectionError when a complete donor-group record cannot resolve the row's J* slot."""
    return _ready(_Ctx(_rows(rows), out), row)


def _blocked(ctx, row):
    def f():
        seen, stack = set(), list(ctx.ups(row))
        while stack:
            u = stack.pop()
            if u in seen:
                continue
            seen.add(u)
            if ctx.done(u):
                continue
            if ctx.failed(u):
                return True
            if _prior(ctx.by[u]):
                stack.extend(ctx.ups(ctx.by[u]))
        return False
    return ctx._memo(("blocked", row["experiment_id"]), f)


def blocked(row, rows, out):
    """True when an upstream, transitively through upstreams that are not done, carries pool/queue_v3_prior/<eid>.failed."""
    return _blocked(_Ctx(_rows(rows), out), row)


def ckpt_deps(row, rows):
    """Experiment ids owning the *_best.pt files that `row` loads (the checkpoint owners for ckpt_offload.deps_of, which calls
    this only for pending rows, i.e. until every dependent is done): the donor group of a bridge / target / zero-shot row
    (none for a from-scratch target); the horizon (core) group of a rich group (core AP checkpoint); the source of a
    continuation group. Core, panel and CSX groups read no checkpoint of another unit (CSX reads only the core group's record).
    Bridge npz files and stable states are never offloaded and are not listed.

    `rows`: pass the prebuilt index deps.index(plan) (or ckpt_offload.deps_of's own `by`), built once per offload pass. A dict is
    used as given and only the row's own upstream ids are looked up in it (no pass over the plan); a list is indexed on every
    call, O(len(plan)) each (M10 review: 1.3 s per pass for 1,154 pending prior rows in a 10,481-row plan, 0.00 s with the
    index)."""
    by = index(rows)
    ups = _upstreams(by, row)  # validates the references
    if S.stage_of(row) != "donor_group":
        sl = S.slot_of(row)
        return [] if sl is None else [sl[0]]
    out = []
    for u in ups:
        up = by[u]
        if not _prior(up) or S.stage_of(up) != "donor_group":
            continue
        if relation(row, up) == "continuation" or row["family_id"] == S.RICH_DONOR:
            out.append(u)
    return out


def _n(v):
    return -1 if v is None else int(v)


def tier_of(row):
    """§4.1 queue tier of the row's spec.block; spec.queue_tier, when present, must be that tier (ValueError otherwise)."""
    s = row.get("spec") or {}
    b, t = s.get("block"), s.get("queue_tier")
    if b not in BLOCK_TIER:
        raise ValueError(f"{row.get('experiment_id')}: spec.block {b!r} is not one of {list(BLOCK_TIER)} (§4.1)")
    if t is not None and (isinstance(t, bool) or not isinstance(t, int) or t != BLOCK_TIER[b]):
        raise ValueError(f"{row.get('experiment_id')}: spec.queue_tier {t!r} disagrees with block {b!r} (tier {BLOCK_TIER[b]}, §4.1)")
    return BLOCK_TIER[b]


def order_key(row):
    """Queue order (§6.5, §8 item 6): tier, then donor group < bridge < target < zero-shot, then dataset and folds; seed,
    objective, block, slot, mode and the id break ties so the order is deterministic."""
    st, s = S.stage_of(row), row.get("spec") or {}
    sl = S.slot_of(row) if st != "donor_group" else None
    slot = sl[1] if sl else (S.SCRATCH if st == "target" else "")
    return (tier_of(row), STAGE_RANK[st], str(row.get("dataset")), _n(row.get("subject_fold")), _n(row.get("content_fold")),
            _n(row.get("seed")), str(s.get("objective") or ""), str(s.get("block") or ""), slot, str(s.get("mode") or ""),
            row["experiment_id"])


def weight_of(row):
    w = WEIGHTS[row["family_id"]]
    if isinstance(w, bool) or int(w) != w or int(w) < 1:
        raise ValueError(f"WEIGHTS[{row['family_id']}] = {w!r} must be a positive integer (bash arithmetic in the pool)")
    return int(w)


def _positions(out, ext, sel):
    """eid -> queue index (100000 + position in plan_ext.jsonl, as run.py reads it)."""
    if ext is None:
        p = os.path.join(out, "plan_ext.jsonl")
        if not os.path.exists(p):
            raise FileNotFoundError(f"{p} is missing: prior rows are addressed by their plan_ext position (pass ext= in tests)")
        with open(p) as f:
            ids = [json.loads(line)["experiment_id"] for line in f]
    else:
        ids = [r["experiment_id"] for r in ext]
    pos = {}
    for j, e in enumerate(ids):
        if e in pos:
            raise ValueError(f"{e} occurs twice in plan_ext")
        pos[e] = EXT_OFFSET + j
    miss = [r["experiment_id"] for r in sel if r["experiment_id"] not in pos]
    if miss:
        raise ValueError(f"{len(miss)} prior rows are not in plan_ext (first {miss[0]})")
    return pos


def _write(path, text):
    tmp = f"{path}.tmp{os.getpid()}"
    try:
        with open(tmp, "w") as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def write_queue(out, rows, held=(), bound=None, ext=None):
    """Write the prior queue files into `out` (each via tmp + os.replace) and return a summary dict. The rows in scope are the
    prior rows that are not held (below); each is done, failed, blocked, ready or waiting (module docstring):
      queue_v3_prior.txt          eid|idx|up1,up2,... for every row in scope except the blocked and the unresolved (below)
                                  ones, in order_key order (the third field is empty without upstreams; idx = 100000 + the
                                  plan_ext position). Done and failed rows stay listed, as in the other queues (the worker skips
                                  them by record / .failed marker)
      queue_v3_prior_weights.txt  'eid weight' per listed row (WEIGHTS)
      queue_v3_prior.remaining    ready + waiting rows (one integer); the keeper stops at 0
      queue_v3_prior.waiting      the waiting rows (one integer)
      queue_v3_prior.blocked      the blocked eids, one per line, in queue order
    Blocked rows cannot start until their failed upstream is cleared, so they are left out of the queue file: the existing
    readers that count rows as not done, not .failed and not claimed (watch_anyhost.sh / keeper.sh unclaimed()) and the
    offload daemon's pending set (ckpt_offload.queued()) never see them. Clearing the marker lists them again at the next
    refresh. held: experiment ids and / or family ids (make_queue passes HELD | families_on_hold). A held row, a row whose
    family is not in `bound` (when given) and, transitively, a row with an upstream that is held and not done are out of
    scope: in no file and no counter. ext: the plan_ext rows in file order (default: read <out>/plan_ext.jsonl). rows, held,
    bound and ext may be one-shot iterables (each is read once). Raises ValueError on an inconsistent plan (check_plan; a row
    in scope missing from plan_ext) before writing anything.

    Unresolved J* rows: a complete donor-group record that cannot resolve a J* slot (select.SelectionError: a record layout that
    is not the pinned one) affects only the rows of that slot. They are 'waiting' (counted in .waiting and .remaining, so the
    keeper keeps running until the record is fixed and the next refresh lists them), are listed with the error under
    'unresolved' in the summary, and get NO line in queue_v3_prior.txt or the weights file: the pool worker admits a listed row
    as soon as its upstream records exist, and such a row would raise SelectionError, end technical_failed three times, get
    .failed and block its dependents. They are not written to .blocked (no upstream failed).

    Caller contract (make_queue.py, §6.5; M10): write_queue(O, ALL, held=HELD | families_on_hold, bound=set(core.FAMILY_GROUP)).
    On any exception it writes queue_v3_prior.txt, queue_v3_prior_weights.txt and queue_v3_prior.blocked empty and the word
    "unknown" into .remaining and .waiting, never "0": the keeper stops at .remaining 0 and treats a missing or non-integer
    value as unknown (keeps running). write_queue itself writes integers only; the M10 make_queue patch may then rewrite a 0
    in .remaining as "held" (the lane is paused: an open prior row is held or unbound), so .remaining reads an integer,
    "held" or "unknown". Only keeper_prior.sh and slurm/aln33_prior_pool.sbatch may serve queue_v3_prior.txt:
    keeper.sh and aln3_gpu_pool.sbatch read 'IFS="|" read -r eid idx', which leaves "idx|ups" in idx on a line with upstreams."""
    rows = _rows(rows)
    held = {h for h in (held or ()) if isinstance(h, str)}
    bound = None if bound is None else set(bound)
    ext = None if ext is None else list(ext)
    ctx = _Ctx(rows, out)
    order = _check_all(ctx, _seq(rows))

    def direct(r):
        return r["experiment_id"] in held or r["family_id"] in held or (bound is not None and r["family_id"] not in bound)

    hold = {}
    for r in order:  # upstreams first
        hold[r["experiment_id"]] = direct(r) or any(not ctx.done(u) and hold[u] for u in ctx.ups(r))
    sel = sorted((r for r in order if not hold[r["experiment_id"]]), key=order_key)
    pos = _positions(out, ext, sel)
    lines, wts, blk, unresolved, fams = [], [], [], {}, {}
    n = dict.fromkeys(("done", "failed", "blocked", "ready", "waiting"), 0)
    for r in sel:
        e = r["experiment_id"]
        if ctx.done(e):
            k = "done"
        elif ctx.failed(e):
            k = "failed"
        elif _blocked(ctx, r):
            k = "blocked"
        else:
            try:
                k = "ready" if _ready(ctx, r) else "waiting"
            except S.SelectionError as ex:  # a group record that cannot resolve J*: waiting, reported, not listed (docstring)
                k, unresolved[e] = "waiting", str(ex)
        n[k] += 1
        if k == "blocked":
            blk.append(e)
            continue
        if e in unresolved:
            continue
        lines.append(f"{e}|{pos[e]}|{','.join(ctx.ups(r))}\n")
        wts.append(f"{e} {weight_of(r)}\n")
        fams[r["family_id"]] = fams.get(r["family_id"], 0) + 1
    rem = n["ready"] + n["waiting"]
    base = os.path.join(out, QUEUE)
    _write(base + "_weights.txt", "".join(wts))
    _write(base + ".blocked", "".join(f"{e}\n" for e in blk))
    _write(base + ".txt", "".join(lines))
    _write(base + ".waiting", f"{n['waiting']}\n")
    _write(base + ".remaining", f"{rem}\n")
    return {"queued": len(lines), "in_scope": len(sel), "held": len(order) - len(sel), **n, "remaining": rem, "families": fams,
            "unresolved": unresolved}
