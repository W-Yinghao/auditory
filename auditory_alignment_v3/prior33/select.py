"""E34_PUBLIC_PRIOR (ALN3.4, contract aln33_env64_125ms_v1): donor slots, donor-group rows and the joint lambda rule.

PUBLIC_PRIOR_DESIGN.md §2.9-§2.11, §4.1-§4.3 and §6.1 (`select.py`: light, stdlib json/math/os/re only; hashed into
prior33_bridge, prior33_target and prior33_zeroshot). The queue module deps.py (not hashed) and the bridge / target / zero-shot
runners resolve slots through this module, so the lambda rule has a single implementation.

Rows (plan_ext.jsonl rows written by make_plan_ext_prior33.py, §4.3):
  family_id      ALN32_PUBLIC_AUDIO_PRIOR_ + DONOR (core and panel) | RICH_DONOR | CSX_DONOR | BRIDGE | TARGET | ZEROSHOT
  spec.stage     donor_group | bridge | target | zero_shot (optional here, but it must agree with the family)
  donor group    spec.members (default: the §2.6 members of the family; when given, distinct members of that set),
                 spec.lambda_rule (when given, LAMBDA_RULE), spec.budget.continuation (the compute limit, below)
  bridge         spec.donor_group, spec.member
  target         spec.init (random | donor), spec.donor_group, spec.member ("S" or absent for target_from_scratch)
  zero-shot      spec.donor_group, spec.member, spec.bridge
  When a row has no `member` key, a `variant` that is a slot name is used instead.
Slots (§2.11, one bridge per slot): (donor-group id, name) with name in AP XP J* XM APR APC XPC; the concrete tags J1 and J025
are accepted as names too. "J*" (aliases Jstar, J_star) is resolved per group by the lambda rule. Donor-group rows and
from-scratch targets have no slot.

Lambda rule (§2.9; LAMBDA_RULE "min_dev_ce_tie1e-4_lambda1"): J* is the joint member, J1 (lambda = 1) or J025 (lambda = 0.25),
whose `_best.pt` has the lower donor-dev retrieval cross-entropy CE_dev (bits). |CE(J1) - CE(J025)| < 1e-4 is a tie, and ties
go to J1. A non-finite CE_dev counts as +inf (worse than any finite value); two non-finite values tie. A group row or a group
record that names another lambda rule is refused (ValueError / SelectionError), never resolved under this one.

PINNED donor-group record interface. §2.10 says only that the record holds "the joint choice under both rules" and, per member,
"the scores under both rules"; this module fixes the fields it reads. run_donor.py / donor_train.py (M5) write them, build
`joint_choice` with joint_choice(), and check a record written by train_donor_group / run_donor with check_group_record() in
their synthetic tests (a layout drift would otherwise leave every J* row of the group unresolvable):
  experiment_id                   the group id
  row                             the group row, as core.new_record stores it (row.spec.members and row.spec.lambda_rule are read)
  members[M]["best"]["ce_dev"]    for every member M: CE_dev in bits of <gid>_m<M>_best.pt, a JSON number (int or float; NaN and
                                  Infinity are allowed and count as +inf). member_of reads it for M = J1 and J025
  joint_choice                    optional; as returned by joint_choice(record): {"rule": LAMBDA_RULE, "member": "J1" | "J025",
                                  "ce_dev": {"J1": ..., "J025": ...}, "tie_bits": 1e-4}. M5 records the gain-rule sensitivity
                                  under other keys (e.g. "gain_rule"), never read here. When "rule" is LAMBDA_RULE, "member" must
                                  equal the choice member_of makes from the recorded CE_dev values (SelectionError otherwise)
Files (§2.10, §2.11; M5 and M6 name them with these functions): ckpt/<gid>_m<M>_best.pt, _gainsel_best.pt and _h30_best.pt
(member_ckpt); the stable states kept at the compute limit L, ckpt/<gid>_m<M>_stable<L-3>.pt (stable_ckpt, retained_states);
ckpt/<bid>_bridge.npz (bridge_npz). The compute limit L of a group (compute_limit) is the integer after "limit" in
spec.budget.continuation (§4.3: "group_wsd_any_last3_ext10_limit60_v1"), DEFAULT_LIMIT_EP_EQ when the field names none; a
continuation version (make_plan_ext_prior33.py --continuation) writes its own, larger limit there (e.g. "..._limit90_v1").

Entry points: run every prior33 entry point as a module (python -m auditory_alignment_v3.prior33.<name>). A prior33 file run by
path puts prior33/ at sys.path[0], where this file would shadow the standard library's `select` (imported by subprocess through
selectors); the guard below then hands the standard-library module to the importer instead of this one.
"""
from __future__ import annotations

import sys as _sys

if __name__ == "select":  # imported under the standard library's name: see "Entry points" in the module docstring
    def _hand_back_stdlib_select():
        import importlib.machinery
        import importlib.util
        import os as _os
        me = _os.path.realpath(__file__)
        here = _os.path.dirname(me)
        path = [p for p in _sys.path if isinstance(p, str) and _os.path.realpath(p or _os.curdir) != here]
        spec = importlib.machinery.PathFinder.find_spec("select", path)
        if spec is None or spec.loader is None or (spec.origin and _os.path.realpath(spec.origin) == me):
            raise ImportError("auditory_alignment_v3/prior33/select.py shadows the standard library's select module; run prior33 "
                              "files with python -m auditory_alignment_v3.prior33.<name>")
        mod = importlib.util.module_from_spec(spec)
        _sys.modules["select"] = mod  # the import system returns sys.modules["select"] once this file has run
        spec.loader.exec_module(mod)

    _hand_back_stdlib_select()

import json  # noqa: E402
import math  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402

PREFIX = "ALN32_PUBLIC_AUDIO_PRIOR_"
DONOR = PREFIX + "DONOR"
RICH_DONOR = PREFIX + "RICH_DONOR"
CSX_DONOR = PREFIX + "CSX_DONOR"
BRIDGE = PREFIX + "BRIDGE"
TARGET = PREFIX + "TARGET"
ZEROSHOT = PREFIX + "ZEROSHOT"
FAMILIES = (DONOR, CSX_DONOR, RICH_DONOR, BRIDGE, TARGET, ZEROSHOT)  # the six families of QUEUES["prior"] (§6.5)
DONOR_FAMILIES = (DONOR, RICH_DONOR, CSX_DONOR)
STAGE = {DONOR: "donor_group", RICH_DONOR: "donor_group", CSX_DONOR: "donor_group",
         BRIDGE: "bridge", TARGET: "target", ZEROSHOT: "zero_shot"}
GROUP_MEMBERS = {DONOR: ("AP", "XP", "J1", "J025", "XM"), RICH_DONOR: ("APR",), CSX_DONOR: ("APC", "XPC")}  # §2.6
MEMBER_TAGS = ("AP", "XP", "J1", "J025", "XM", "APR", "APC", "XPC")  # checkpoint member tags M (§2.10)
JOINT = "J*"
JOINT_CANDIDATES = ("J1", "J025")  # lambda = 1.0 (wins ties), lambda = 0.25
SLOTS = ("AP", "XP", JOINT, "XM", "APR", "APC", "XPC")
SCRATCH = "S"  # target_from_scratch
LAMBDA_RULE = "min_dev_ce_tie1e-4_lambda1"
LAMBDA_TIE_BITS = 1e-4
DEFAULT_LIMIT_EP_EQ = 60  # §2.10: the compute limit of this execution version
DECAY_EP_EQ = 3  # the stable state kept at the compute limit L is the one at L - 3 ep-eq (stable57 for 60)
CKPT_SUFFIX = {"best": "_best.pt", "gainsel": "_gainsel_best.pt", "h30": "_h30_best.pt"}
_ALIASES = {"Jstar": JOINT, "JSTAR": JOINT, "J_star": JOINT, "J_STAR": JOINT}
_NAMES = frozenset(SLOTS) | frozenset(MEMBER_TAGS) | frozenset(_ALIASES) | {SCRATCH}
_LIMIT = re.compile(r"limit(\d+)")


class SelectionError(ValueError):
    """A donor-group record cannot resolve a slot: wrong group, missing member, missing or non-numeric CE_dev, another lambda
    rule, a recorded joint choice that disagrees with the rule, unreadable record."""


def _eid(row):
    return row.get("experiment_id", "?") if isinstance(row, dict) else "?"


def stage_of(row):
    """donor_group | bridge | target | zero_shot, from the family (spec.stage, when present, must agree)."""
    fam = row.get("family_id")
    st = STAGE.get(fam) if isinstance(fam, str) else None
    if st is None:
        raise ValueError(f"{_eid(row)}: family {fam!r} is not an E34_PUBLIC_PRIOR family")
    given = (row.get("spec") or {}).get("stage")
    if given is not None and given != st:
        raise ValueError(f"{_eid(row)}: spec.stage {given!r} disagrees with family {fam} ({st})")
    return st


def canonical_slot(name):
    """Canonical member / slot name (J* aliases folded); raises ValueError on an unknown name."""
    n = _ALIASES.get(name, name) if isinstance(name, str) else name
    if not isinstance(n, str) or n not in _NAMES:
        raise ValueError(f"unknown member or slot name {name!r}")
    return n


def group_members(group):
    """Member tags trained by a donor-group row: spec.members, else the family's §2.6 members. Raises ValueError unless the
    row is a donor group, its members are distinct members of its family's §2.6 set, and its spec.lambda_rule (when present)
    is LAMBDA_RULE."""
    if stage_of(group) != "donor_group":
        raise ValueError(f"{_eid(group)}: not a donor-group row")
    s, fam = group.get("spec") or {}, group["family_id"]
    rule = s.get("lambda_rule")
    if rule is not None and rule != LAMBDA_RULE:
        raise ValueError(f"{_eid(group)}: spec.lambda_rule {rule!r} is not {LAMBDA_RULE!r}, the rule select.py implements")
    ms = s.get("members")
    if ms is not None and not isinstance(ms, (list, tuple)):
        raise ValueError(f"{_eid(group)}: spec.members {ms!r} is not a list")
    ms = tuple(ms) if ms else GROUP_MEMBERS[fam]
    if any(not isinstance(m, str) or m not in GROUP_MEMBERS[fam] for m in ms) or len(set(ms)) != len(ms):
        raise ValueError(f"{_eid(group)}: members {list(ms)} are not distinct members of {fam} {list(GROUP_MEMBERS[fam])} (§2.6)")
    return ms


def compute_limit(group):
    """Compute limit L (ep-eq) of a donor-group row: the integer after "limit" in spec.budget.continuation; DEFAULT_LIMIT_EP_EQ
    when the field is absent or names no limit (module docstring)."""
    m = _LIMIT.search(str(((group.get("spec") or {}).get("budget") or {}).get("continuation") or ""))
    return int(m.group(1)) if m else DEFAULT_LIMIT_EP_EQ


def names_limit(group):
    """True when spec.budget.continuation names the compute limit explicitly ("..._limit<L>_...")."""
    return _LIMIT.search(str(((group.get("spec") or {}).get("budget") or {}).get("continuation") or "")) is not None


def _slot_name(row):
    s = row.get("spec") or {}
    if "member" in s:
        m = s["member"]
    else:
        v = s.get("variant")
        m = v if isinstance(v, str) and v in _NAMES else None
    return None if m is None else canonical_slot(m)


def slot_of(row):
    """(donor-group id, slot name) of a bridge / target / zero-shot row; None for donor groups and from-scratch targets."""
    st = stage_of(row)
    if st == "donor_group":
        return None
    s = row.get("spec") or {}
    name, gid, init = _slot_name(row), s.get("donor_group"), s.get("init")
    if st == "target" and (init == "random" or (init is None and name in (None, SCRATCH))):
        if gid is not None or name not in (None, SCRATCH):
            raise ValueError(f"{_eid(row)}: from-scratch target with a donor slot (donor_group={gid}, member={name})")
        return None
    if name in (None, SCRATCH) or not gid:
        raise ValueError(f"{_eid(row)}: {st} row without a donor slot (donor_group={gid}, member={name})")
    if st == "target" and init not in (None, "donor"):
        raise ValueError(f"{_eid(row)}: target init {init!r} (expected random or donor)")
    return gid, name


def _lookup(rows, eid):
    if isinstance(rows, dict):
        return rows.get(eid)
    for r in rows:
        if r.get("experiment_id") == eid:
            return r
    return None


def _check_slot(group, name):
    ms = group_members(group)
    need = JOINT_CANDIDATES if name == JOINT else (name,)
    if any(m not in ms for m in need):
        raise ValueError(f"{_eid(group)}: slot {name} needs member(s) {list(need)}; the group trains {list(ms)}")


def group_row(row, rows):
    """The donor-group row owning the row's slot (the row itself for a donor group; None for a from-scratch target), checked
    with group_members (members, lambda rule). `rows` is a sequence of rows or a mapping experiment_id -> row."""
    if stage_of(row) == "donor_group":
        group_members(row)
        return row
    sl = slot_of(row)
    if sl is None:
        return None
    g = _lookup(rows, sl[0])
    if g is None:
        raise ValueError(f"{_eid(row)}: donor group {sl[0]} is not a plan row")
    if stage_of(g) != "donor_group":
        raise ValueError(f"{_eid(row)}: spec.donor_group {sl[0]} is a {stage_of(g)} row")
    _check_slot(g, sl[1])
    return g


def member_best_ce(group_record, member):
    """CE_dev (bits) of <gid>_m<member>_best.pt: group_record["members"][member]["best"]["ce_dev"], a JSON number (pinned;
    module docstring). SelectionError when it is missing or not a number."""
    rid = group_record.get("experiment_id", "?") if isinstance(group_record, dict) else "?"
    where = f"group record {rid}: members[{member!r}]['best']['ce_dev']"
    try:
        v = group_record["members"][member]["best"]["ce_dev"]
    except (KeyError, TypeError, IndexError):
        raise SelectionError(f"{where} is missing (the pinned layout of select.py)") from None
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise SelectionError(f"{where} = {v!r} is not a JSON number")
    return float(v)


def lambda_choice(ce_j1, ce_j025, tie=LAMBDA_TIE_BITS):
    """The §2.9 lambda rule: 'J025' only when its CE_dev is lower by at least `tie` bits, otherwise 'J1'."""
    a, b = (float(x) for x in (ce_j1, ce_j025))
    a, b = (x if math.isfinite(x) else math.inf for x in (a, b))
    if a == b or abs(a - b) < tie:
        return "J1"
    return "J025" if b < a else "J1"


def joint_choice(group_record):
    """The J* choice of a donor-group record under LAMBDA_RULE, exactly as member_of makes it: {"rule", "member", "ce_dev",
    "tie_bits"} (JSON-serialisable). run_donor.py records it as the record's `joint_choice` (module docstring). Raises
    SelectionError when the CE_dev of J1 or J025 is missing or not a number."""
    a, b = member_best_ce(group_record, "J1"), member_best_ce(group_record, "J025")
    return {"rule": LAMBDA_RULE, "member": lambda_choice(a, b), "ce_dev": {"J1": a, "J025": b}, "tie_bits": LAMBDA_TIE_BITS}


def _recorded_group(gid, group_record):
    """(members, lambda_rule) of the group row stored in the record (None where absent); SelectionError when malformed."""
    rrow = group_record.get("row")
    rspec = rrow.get("spec") if isinstance(rrow, dict) else None
    if not isinstance(rspec, dict):
        return None, None
    ms, rule = rspec.get("members"), rspec.get("lambda_rule")
    if ms is not None and not isinstance(ms, (list, tuple)):
        raise SelectionError(f"group record {gid}: row.spec.members is {ms!r}")
    if rule is not None and rule != LAMBDA_RULE:
        raise SelectionError(f"group record {gid}: the group was registered under lambda rule {rule!r}, not {LAMBDA_RULE!r}")
    return (list(ms) if ms else None), rule


def _resolve(gid, name, group_record):
    if group_record is None and name != JOINT:
        return name
    if not isinstance(group_record, dict):
        raise SelectionError(f"slot ({gid}, {name}): the donor-group record is required")
    rid = group_record.get("experiment_id")
    if rid is not None and rid != gid:
        raise SelectionError(f"slot ({gid}, {name}): record {rid} belongs to another unit")
    ms, _ = _recorded_group(gid, group_record)
    need = JOINT_CANDIDATES if name == JOINT else (name,)
    if ms and any(m not in ms for m in need):
        raise SelectionError(f"slot ({gid}, {name}): the recorded group members {ms} lack {list(need)}")
    if name != JOINT:
        return name
    choice = joint_choice(group_record)["member"]
    jc = group_record.get("joint_choice")
    if isinstance(jc, dict) and jc.get("rule") == LAMBDA_RULE and jc.get("member") != choice:
        raise SelectionError(f"slot ({gid}, J*): the recorded joint_choice {jc.get('member')!r} disagrees with {LAMBDA_RULE} on the "
                             f"recorded CE_dev values ({choice})")
    return choice


def member_of(row, group_record):
    """Concrete member tag (AP XP J1 J025 XM APR APC XPC) whose checkpoint the row loads; J* resolved by the lambda rule on
    `group_record` (the record of the row's donor group; it may be None for a slot other than J*). None for a from-scratch
    target. Raises ValueError for a donor-group row and SelectionError when the record cannot resolve the slot."""
    if stage_of(row) == "donor_group":
        raise ValueError(f"{_eid(row)}: a donor-group row has no single member")
    sl = slot_of(row)
    if sl is None:
        return None
    return _resolve(sl[0], sl[1], group_record)


def check_group_record(group_record, group=None):
    """Raises SelectionError unless `group_record` follows the pinned donor-group record interface (module docstring):
    experiment_id and the stored group row, a valid donor group (members, lambda rule), members[M]["best"]["ce_dev"] a number
    for every member M of the group, and a `joint_choice` (when present in the pinned form) that agrees with the rule.
    `group` (the plan row), when given, must be the recorded group. Returns the J* member, or None for a group without both
    joint members. M5's synthetic tests call it on a record written by train_donor_group / run_donor."""
    if not isinstance(group_record, dict):
        raise SelectionError(f"a donor-group record must be a mapping, got {type(group_record).__name__}")
    gid, rrow = group_record.get("experiment_id"), group_record.get("row")
    if not isinstance(gid, str) or not isinstance(rrow, dict) or rrow.get("experiment_id") != gid:
        raise SelectionError(f"group record {gid!r}: experiment_id and the stored group row (core.new_record) are required")
    if group is not None and group.get("experiment_id") != gid:
        raise SelectionError(f"group record {gid}: expected the record of {group.get('experiment_id')}")
    try:
        ms = group_members(rrow)
    except ValueError as ex:
        raise SelectionError(f"group record {gid}: {ex}") from None
    for m in ms:
        member_best_ce(group_record, m)
    if not all(m in ms for m in JOINT_CANDIDATES):
        return None
    return _resolve(gid, JOINT, group_record)


def record_path(out, eid):
    return os.path.join(out, "units", f"{eid}.json")


def load_record(out, eid):
    """The complete unit record units/<eid>.json, or None while it does not exist. An unreadable record, or one whose status
    is not 'complete' (core.write_record never writes such a file), raises SelectionError."""
    p = record_path(out, eid)
    if not os.path.exists(p):
        return None
    try:
        with open(p) as f:
            rec = json.load(f)
    except (OSError, ValueError) as ex:
        raise SelectionError(f"unreadable record {p}: {ex!r}") from None
    if not isinstance(rec, dict) or rec.get("status") != "complete":
        raise SelectionError(f"record {p} is not a complete unit record")
    return rec


def slot_member(slot, rows, out):
    """Concrete member of a slot (gid, name), J* resolved from units/<gid>.json; None while a J* group record is missing."""
    gid, name = slot
    name = canonical_slot(name)
    g = _lookup(rows, gid)
    if g is None:
        raise ValueError(f"slot {slot}: donor group {gid} is not a plan row")
    if stage_of(g) != "donor_group":
        raise ValueError(f"slot {slot}: {gid} is not a donor-group row")
    _check_slot(g, name)
    if name != JOINT:
        return name
    rec = load_record(out, gid)
    return None if rec is None else _resolve(gid, name, rec)


def member_ckpt(out, gid, member, kind="best"):
    """ckpt/<gid>_m<M>_best.pt (kind best), _gainsel_best.pt (gainsel) or _h30_best.pt (h30)."""
    if member not in MEMBER_TAGS:
        raise ValueError(f"member checkpoints need a concrete member tag, got {member!r}")
    return os.path.join(out, "ckpt", f"{gid}_m{member}{CKPT_SUFFIX[kind]}")


def stable_ckpt(out, gid, member, ep_eq=DEFAULT_LIMIT_EP_EQ - DECAY_EP_EQ):
    """ckpt/<gid>_m<M>_stable<E>.pt: the stable state kept when the compute limit is reached while improving (§2.10); E is the
    group's compute limit minus DECAY_EP_EQ (retained_states)."""
    if member not in MEMBER_TAGS:
        raise ValueError(f"stable states need a concrete member tag, got {member!r}")
    return os.path.join(out, "ckpt", f"{gid}_m{member}_stable{int(ep_eq)}.pt")


def retained_states(out, group):
    """The stable states a group keeps at its compute limit L, one per member: ckpt/<gid>_m<M>_stable<L-3>.pt. A continuation
    version of the group resumes from exactly these files."""
    e = compute_limit(group) - DECAY_EP_EQ
    return [stable_ckpt(out, group["experiment_id"], m, e) for m in group_members(group)]


def bridge_npz(out, bid):
    """ckpt/<bid>_bridge.npz (§2.11)."""
    return os.path.join(out, "ckpt", f"{bid}_bridge.npz")
