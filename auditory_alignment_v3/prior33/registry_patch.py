"""E34_PUBLIC_PRIOR (ALN3.4) registry.py / run.py additions, module M9 (PUBLIC_PRIOR_DESIGN.md §6.3; §6.5 live-edit step 2):
the blocks the two UNAPPLIED patches add, the generator of the patch files, and the checks their apply recipes run before the
atomic rename. Not imported by any unit and not part of any code hash. Stdlib only, plus prior33/select.py (stdlib); the import
tests import auditory_alignment_v3.core (and with it torch) exactly as a unit does, in the recipe's own fresh process.

Patches (private/auditory_alignment_v3/aln34/prior33_patches/; generated against COPIES of the live files, never applied here):
  registry.prior33.patch  appends registry_block() after FAMILY_GROUP: FAMILY_CODE.update (the five prior33 code groups) and
                          FAMILY_GROUP.update (the six ALN32_PUBLIC_AUDIO_PRIOR_* families)
  run.prior33.patch       inserts run_block() right after the RUNNER literal: RUNNER.update (code group -> prior33.<runner>)
Each header carries the live sha256 of the copy it was generated against, the patched sha256, the apply recipe in the M10 format
(`# apply (` ... `#   mv -f`, the lines tests/auditory_alignment_v3/prior33/infra/run_harness.sh extracts and runs) and a
rollback. Order (§6.5 step 2): registry first, then run.py (check-run refuses until the registry carries the families).

Design delta (§6.3): prior33_donor and prior33_rich_donor also hash prior33/select.py. run_donor.py / donor_train.py (M5) import it
at run time (select.joint_choice, member_ckpt / stable_ckpt / retained_states, compute_limit; select.py docstring), so without it
an edit of select.py would change donor behaviour and the recorded joint choice without changing their code_hash (M8 review,
item 1). Every other list is §6.3's.

Checks (repo root: python -B -m auditory_alignment_v3.prior33.registry_patch check-registry FILE | check-run FILE
[--units DIR] [--allow-unrecorded NAME ...]):
  check-registry FILE  FILE is the patched copy of registry.py (any name; loaded with SourceFileLoader):
    - collisions and drift: every live entry of FAMILY_CODE, FAMILY_GROUP and POLICY_GROUP is unchanged; the added keys are
      exactly GROUPS and FAMILIES, none of them is defined by the live registry, and their values equal group_files() / FAMILIES;
    - import test: with FILE injected as auditory_alignment_v3.registry, auditory_alignment_v3.core and auditory_alignment_v3.run
      import (the package must be this repository's), and core uses FILE's dictionaries;
    - code hashes: core.code_hash of every existing family, and the hash of every existing code group (POLICY_GROUP groups
      included), equals its value under the live registry; every prior33 family's code_hash is computable (files exist);
    - latest unit records (§6.3 "against its latest unit record"; record_problems): the code_hash of the latest record
      (units/*.json, by mtime) of every code group, and of every (family, code group) pair (the family is the record's
      row.family_id), equals the patched registry's. Fails closed: a missing units directory, one without any record carrying
      code_group / code_hash, and an existing code group or family without any record are problems, unless that group or
      family is named with --allow-unrecorded (for a group or family registered by another lane that has never run; confirm
      that first). --units DIR replaces the live units directory (sandboxes, tests) under the same rules;
    - import closure (static, ast): every auditory_alignment_v3 module that a group's runner reaches through module-level import
      chains must be in the group's file list, unless NOT_HASHED by design (registry.py, run.py, prior33/deps.py) or an inert
      package __init__.py; modules reached only through imports inside functions, and ALN2 modules outside core.V2_DEPS (the
      existing families' convention), are printed as notes.
  check-run FILE       FILE is the patched copy of run.py: the live registry already carries the six families with these groups
                       (registry patch first); FILE imports as auditory_alignment_v3.run; every live RUNNER entry, EXT_OFFSET and
                       LOCAL_ / PRIVATE_ / FM_FAMILIES are unchanged; the added keys are exactly RUNNERS (no collision); every prior33
                       family's code group has a runner module that this repository holds; and, as §6.3 asks of both edits (run.py
                       is in no code hash, so this re-checks the state the registry patch left), every family's core.code_hash
                       equals its group's hash and the latest-record comparison above passes (same options, same fail-closed
                       rules; the prior33 groups and families are compared only once they have records).
  write-patches        regenerate both patch files from fresh copies of the live files (when a live file has changed; review the
                       diff of the patch before applying it).
Exit status 0 = no problem; 1 = problems (printed); 2 = usage.
"""
from __future__ import annotations

import argparse
import ast
import difflib
import hashlib
import importlib
import importlib.machinery
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import time

from . import select as S

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
PY = "/home/infres/yinwang/anaconda3/envs/eeg2025/bin/python"
PKG = "auditory_alignment_v3"
TARGET = {"registry": "auditory_alignment_v3/registry.py", "run": "auditory_alignment_v3/run.py"}
PATCH_DIR = "private/auditory_alignment_v3/aln34/prior33_patches"
PATCH = {k: f"{PATCH_DIR}/{k}.prior33.patch" for k in TARGET}
BACKUP_DIR = "private/auditory_alignment_v3"     # §6.3: private/auditory_alignment_v3/{registry,run}.py.before_prior33_<date>
UNITS = "private/auditory_alignment_v3/units"
MARK = "E34_PUBLIC_PRIOR"                        # first word of both added blocks (an already patched file is refused)

P33_DIR = "auditory_alignment_v3/prior33"
BASE_FILES = (("auditory_alignment_v3", "core.py"), ("auditory_alignment_v3", "local_train.py"))
P33_FILES = {  # §6.3, in hash order; "select.py" in the two donor groups is the design delta (module docstring)
    "prior33_donor": ("contract.py", "views.py", "model.py", "losses.py", "sampler.py", "select.py", "donor_train.py", "run_donor.py"),
    "prior33_rich_donor": ("contract.py", "views.py", "model.py", "losses.py", "sampler.py", "rich.py", "select.py", "donor_train.py",
                           "run_donor.py"),
    "prior33_bridge": ("contract.py", "views.py", "model.py", "losses.py", "sampler.py", "select.py", "bridge.py", "run_bridge.py"),
    "prior33_target": ("contract.py", "views.py", "model.py", "losses.py", "select.py", "gen_fit_target.py", "fit_target.py",
                       "target_train.py", "run_target.py"),
    "prior33_zeroshot": ("contract.py", "views.py", "model.py", "select.py", "bridge.py", "zeroshot.py", "run_zeroshot.py"),
}
EXTRA_FILES = {"prior33_target": (("auditory_alignment_v3", "calib.py"), ("auditory_alignment_v3/aln3_reference", "calibration.py"))}
DESIGN_DELTA = {"prior33_donor": ("select.py",), "prior33_rich_donor": ("select.py",)}  # files added to §6.3's lists
GROUPS = tuple(P33_FILES)
FAMILIES = {S.DONOR: "prior33_donor", S.CSX_DONOR: "prior33_donor", S.RICH_DONOR: "prior33_rich_donor", S.BRIDGE: "prior33_bridge",
            S.TARGET: "prior33_target", S.ZEROSHOT: "prior33_zeroshot"}  # §6.3 (order of select.FAMILIES)
RUNNERS = {"prior33_donor": "prior33.run_donor", "prior33_rich_donor": "prior33.run_donor", "prior33_bridge": "prior33.run_bridge",
           "prior33_target": "prior33.run_target", "prior33_zeroshot": "prior33.run_zeroshot"}  # §6.3 (run.py imports PKG.<value>)
NOT_HASHED = {  # reachable from a runner but outside every code hash by design
    "auditory_alignment_v3/registry.py": "family registry (core.py: not part of any code hash)",
    "auditory_alignment_v3/run.py": "dispatcher (run.py: not part of any code hash)",
    "auditory_alignment_v3/prior33/deps.py": "queue dependencies (design §6.1: light, not hashed)",
}
ALN_PACKAGES = ("auditory_alignment", "auditory_alignment_v2", "auditory_alignment_v3")


class CheckError(RuntimeError):
    """A patch cannot be generated (unexpected live file)."""


# ------------------------------------------------------------------------------------------------------------ the blocks
def group_files(g):
    """FAMILY_CODE value of a prior33 code group: [(dir, file), ...] in hash order."""
    return [*BASE_FILES, *((P33_DIR, f) for f in P33_FILES[g]), *EXTRA_FILES.get(g, ())]


def _q(s):
    return json.dumps(s)


def registry_block():
    """Text appended to registry.py after FAMILY_GROUP (design §6.3, with the select.py delta)."""
    L = ["# E34_PUBLIC_PRIOR (ALN3.4; PUBLIC_PRIOR_DESIGN.md §6.3, module M9): the five prior33 code groups and the six",
         "# ALN32_PUBLIC_AUDIO_PRIOR_* families, appended after FAMILY_GROUP. Each group hashes core.py, local_train.py and its prior33",
         "# files (and V2_DEPS, like every group). Design delta: prior33_donor and prior33_rich_donor also hash prior33/select.py,",
         "# which run_donor.py / donor_train.py import at run time (joint choice, checkpoint and stable-state names); §6.3 lists it for",
         "# the bridge, target and zero-shot groups only. Runners: RUNNER.update in run.py (run.prior33.patch).",
         '_p33 = lambda *fs: [("auditory_alignment_v3", "core.py"), ("auditory_alignment_v3", "local_train.py")] + \\',
         '                   [("auditory_alignment_v3/prior33", f) for f in fs]  # noqa: E731',
         "FAMILY_CODE.update({"]
    w = max(len(_q(g)) for g in GROUPS) + 1
    for g in GROUPS:
        call = "_p33(" + ", ".join(_q(f) for f in P33_FILES[g]) + ")"
        if g in EXTRA_FILES:
            call += " + [" + ", ".join(f"({_q(d)}, {_q(f)})" for d, f in EXTRA_FILES[g]) + "]"
        L.append(f"    {(_q(g) + ':').ljust(w)} {call},")
    L.append("})")
    L.append("FAMILY_GROUP.update({")
    w = max(len(_q(f)) for f in FAMILIES) + 1
    L += [f"    {(_q(f) + ':').ljust(w)} {_q(g)}," for f, g in FAMILIES.items()]
    L.append("})")
    return "\n".join(L) + "\n"


def run_block():
    """Text inserted into run.py right after the RUNNER literal (design §6.3)."""
    items = [f"{_q(g)}: {_q(m)}" for g, m in RUNNERS.items()]
    return ("# E34_PUBLIC_PRIOR (ALN3.4; PUBLIC_PRIOR_DESIGN.md §6.3, module M9): the prior33 runners, imported as\n"
            "# auditory_alignment_v3.<value>; the rich groups run prior33.run_donor under their own code group (prior33_rich_donor).\n"
            "RUNNER.update({" + ", ".join(items[:3]) + ",\n"
            "               " + ", ".join(items[3:]) + "})\n")


def _assigned(tree, name):
    return [n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]


def patched_text(kind, text):
    """The live file's text with the block added; CheckError for an unexpected live file (already patched, names missing)."""
    if not text.endswith("\n"):
        raise CheckError(f"{TARGET[kind]}: the live file does not end with a newline")
    if MARK in text:
        raise CheckError(f"{TARGET[kind]}: the live file already mentions {MARK} (patched already?)")
    tree = ast.parse(text)
    if kind == "registry":
        for name in ("FAMILY_CODE", "FAMILY_GROUP", "POLICY_GROUP"):
            if len(_assigned(tree, name)) != 1:
                raise CheckError(f"{TARGET[kind]}: expected one top-level assignment of {name}")
        return text + registry_block()
    nodes = _assigned(tree, "RUNNER")
    if len(nodes) != 1:
        raise CheckError(f"{TARGET[kind]}: expected one top-level assignment of RUNNER")
    lines = text.splitlines(keepends=True)
    end = nodes[0].end_lineno
    return "".join(lines[:end]) + run_block() + "".join(lines[end:])


# ------------------------------------------------------------------------------------------------------------ patch files
def _sha(b):
    return hashlib.sha256(b).hexdigest()


def _recipe(kind, live, patched):
    f = TARGET[kind]
    base = os.path.basename(f)
    test = {"registry": "check-registry", "run": "check-run"}[kind]
    what = {"registry": "collisions, code hashes vs the live registry and the latest unit records, import test, import closure",
            "run": "registry patched first, collisions, import test, runner modules present, code hashes vs the latest unit records"}[kind]
    return [
        "# apply (repo root, in the §6.5 order only: live-edit step 2, registry.prior33.patch before run.prior33.patch, both after step 1"
        " has added every prior33 file; refuse if the live sha256 differs: regenerate the patch instead):",
        f"#   F={f}; P={PATCH[kind]}",
        f'#   echo "{live}  $F" | sha256sum -c - &&',
        f"#   cp -p $F {BACKUP_DIR}/{base}.before_prior33_$(date +%Y%m%d) && cp -p $F $F.tmp_prior33 &&",
        f'#   patch --no-backup-if-mismatch $F.tmp_prior33 < $P && echo "{patched}  $F.tmp_prior33" | sha256sum -c - &&',
        f"#   {PY} -B -m auditory_alignment_v3.prior33.registry_patch {test} $F.tmp_prior33 &&   # {what}",
        "#   mv -f $F.tmp_prior33 $F    # atomic rename: readers see the old or the new file, never a partial one",
    ]


def header(kind, live, patched, generated):
    f = TARGET[kind]
    if kind == "registry":
        what = ["# what: appends after FAMILY_GROUP FAMILY_CODE.update({...}) with the five prior33 code groups (prior33_donor,",
                "# prior33_rich_donor, prior33_bridge, prior33_target, prior33_zeroshot; each = core.py + local_train.py + its prior33 files,",
                "# prior33_target also calib.py and aln3_reference/calibration.py) and FAMILY_GROUP.update({...}) binding the six",
                "# ALN32_PUBLIC_AUDIO_PRIOR_* families (DONOR and CSX_DONOR -> prior33_donor). Adds lines only; no existing entry and no",
                "# existing family's code_hash changes. Families bound here run nothing before the plan rows exist (§6.5 step 4).",
                "# design delta (§6.3): prior33_donor and prior33_rich_donor also hash prior33/select.py, which run_donor.py /",
                "# donor_train.py import at run time (select.joint_choice, member_ckpt / stable_ckpt / retained_states, compute_limit)."]
        then = ["# then: nothing to restart (every unit is a fresh process). Check from the repo root:",
                f"#   {PY} -B -c \"from auditory_alignment_v3 import core, run; "
                "print({f: core.code_hash(f) for f in sorted(core.FAMILY_GROUP) if f.startswith('ALN32_PUBLIC_AUDIO_PRIOR_')})\"",
                f"# rollback (before §6.5 step 4 only): cp -p {BACKUP_DIR}/{os.path.basename(f)}.before_prior33_<date> $F.tmp_prior33 && "
                "mv -f $F.tmp_prior33 $F",
                "# on a failed check: nothing is replaced; remove $F.tmp_prior33."]
    else:
        what = ["# what: inserts after the RUNNER literal RUNNER.update({...}): prior33_donor and prior33_rich_donor -> prior33.run_donor,",
                "# prior33_bridge -> prior33.run_bridge, prior33_target -> prior33.run_target, prior33_zeroshot -> prior33.run_zeroshot",
                "# (run_unit imports auditory_alignment_v3.<value> and calls .run(row, out, epochs)). Adds lines only; every existing",
                "# RUNNER entry, LOCAL_FAMILIES, PRIVATE_FAMILIES and FM_FAMILIES stay as they are."]
        then = ["# then: nothing to restart (run.py is read by each unit process). Check from the repo root:",
                f"#   {PY} -B -c \"from auditory_alignment_v3 import run; print({{g: m for g, m in run.RUNNER.items() if g.startswith('prior33_')}})\"",
                f"# rollback (before §6.5 step 4 only): cp -p {BACKUP_DIR}/{os.path.basename(f)}.before_prior33_<date> $F.tmp_prior33 && "
                "mv -f $F.tmp_prior33 $F",
                "# on a failed check: nothing is replaced; remove $F.tmp_prior33."]
    test = {"registry": "check-registry", "run": "check-run"}[kind]
    records = ["# the check fails closed on the latest unit records (units/*.json): a missing or empty units directory, or an existing",
               "# code group or family without any record, is a problem. If such a group or family has never run (registered by another",
               "# lane; confirm that first), rerun the recipe's check line by hand on the $F.tmp_prior33 the failed recipe left, with",
               "# --allow-unrecorded NAME (repeatable), and only when it prints ok run the recipe's last line (mv -f) by hand:",
               f"#   {PY} -B -m auditory_alignment_v3.prior33.registry_patch {test} $F.tmp_prior33 --allow-unrecorded NAME"]
    return "\n".join([
        "# E34_PUBLIC_PRIOR (ALN3.4) integration patch, module M9 (PUBLIC_PRIOR_DESIGN.md §6.3, live-edit step 2). NOT APPLIED.",
        f"# target:         {f}",
        f"# live-sha256:    {live}",
        f"#                 (generated {generated} against a copy of the live file with this sha256)",
        f"# patched-sha256: {patched}",
        *what,
        *_recipe(kind, live, patched),
        *records,
        *then,
        "# tested by: tests/auditory_alignment_v3/prior33/test_plan_prior33.py (applies this patch to a temporary copy of the live file,",
        "# checks the patched module, and runs this recipe verbatim in a sandbox copy of the repository layout)",
    ]) + "\n"


def make_patch(kind, live_path, generated=None):
    """(patch text, patched text, live sha256, patched sha256) for the live file at `live_path` (a copy of it)."""
    with open(live_path, "rb") as f:
        raw = f.read()
    text = raw.decode("utf-8")
    new = patched_text(kind, text)
    live, patched = _sha(raw), _sha(new.encode("utf-8"))
    generated = generated or time.strftime("%Y-%m-%dT%H:%M:%S%z")
    rel = TARGET[kind]
    diff = "".join(difflib.unified_diff(text.splitlines(True), new.splitlines(True), f"a/{rel}", f"b/{rel}"))
    return header(kind, live, patched, generated) + diff, new, live, patched


def header_field(text, name):
    """A header value of a patch file: live-sha256, patched-sha256 or generated."""
    if name == "generated":
        m = re.search(r"^#\s+\(generated (\S+) against", text, re.M)
    else:
        m = re.search(rf"^# {re.escape(name)}:\s*([0-9a-f]{{64}})\s*$", text, re.M)
    return m.group(1) if m else None


def write_patches(out_dir=None, root=REPO, generated=None):
    """Write both patch files (tmp + os.replace), each generated against a fresh copy of the live file. -> {kind: (live, patched)}."""
    out_dir = out_dir or os.path.join(root, PATCH_DIR)
    os.makedirs(out_dir, exist_ok=True)
    res = {}
    with tempfile.TemporaryDirectory(prefix="p33_patch_") as td:
        for kind, rel in TARGET.items():
            copy = os.path.join(td, os.path.basename(rel))
            shutil.copy2(os.path.join(root, rel), copy)
            text, _, live, patched = make_patch(kind, copy, generated)
            dst = os.path.join(out_dir, os.path.basename(PATCH[kind]))
            tmp = f"{dst}.tmp{os.getpid()}"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(text)
            os.replace(tmp, dst)
            res[kind] = (live, patched)
    return res


# ------------------------------------------------------------------------------------------------------------ helpers
def load_source(path, name, register=False):
    """Execute a Python file of any name (e.g. registry.py.tmp_prior33) as module `name` (its package = name's parent)."""
    loader = importlib.machinery.SourceFileLoader(name, path)
    spec = importlib.util.spec_from_loader(name, loader)
    mod = importlib.util.module_from_spec(spec)
    if register:
        sys.modules[name] = mod
    try:
        loader.exec_module(mod)
    except BaseException:
        if register:
            sys.modules.pop(name, None)
        raise
    return mod


def _norm(v):
    return [tuple(x) for x in v] if isinstance(v, (list, tuple)) else v


def group_hash(code, g, v2, root=REPO):
    """core.code_hash's value for code group g of the dictionary `code` (files of code[g] + V2_DEPS, first 16 hex digits)."""
    h = hashlib.sha256()
    for d, f in list(code[g]) + list(v2):
        with open(os.path.join(root, d, f), "rb") as fh:
            h.update(fh.read())
    return h.hexdigest()[:16]


def compare_registries(live, patched):
    """Problems of a patched registry module against the live one: changed or removed live entries, collisions, the added keys
    and their values (pure; no import of core)."""
    probs = []
    for name in ("FAMILY_CODE", "FAMILY_GROUP", "POLICY_GROUP"):
        a, b = getattr(live, name, None), getattr(patched, name, None)
        if not isinstance(a, dict) or not isinstance(b, dict):
            probs.append(f"{name}: not a dict in the live or the patched registry")
            continue
        bad = sorted(k for k in a if k not in b or _norm(b[k]) != _norm(a[k]))
        if bad:
            probs.append(f"{name}: live entries changed or removed: {bad}")
    if probs:
        return probs
    for name, want in (("FAMILY_CODE", set(GROUPS)), ("FAMILY_GROUP", set(FAMILIES))):
        a, b = getattr(live, name), getattr(patched, name)
        clash = sorted(want & set(a))
        if clash:
            probs.append(f"{name}: collision, the live registry already defines {clash}")
        added = set(b) - set(a)
        if added != want - set(a):
            probs.append(f"{name}: added keys {sorted(added)}, expected {sorted(want - set(a))}")
    if set(patched.POLICY_GROUP) != set(live.POLICY_GROUP):
        probs.append("POLICY_GROUP: keys added")
    for g in GROUPS:
        if g in patched.FAMILY_CODE and _norm(patched.FAMILY_CODE[g]) != _norm(group_files(g)):
            probs.append(f"FAMILY_CODE[{g!r}] = {patched.FAMILY_CODE[g]} differs from registry_patch.group_files({g!r})")
    for f, g in FAMILIES.items():
        if patched.FAMILY_GROUP.get(f) != g:
            probs.append(f"FAMILY_GROUP[{f!r}] = {patched.FAMILY_GROUP.get(f)!r}, expected {g!r}")
    return probs


def hash_problems(live, patched, v2, root=REPO):
    """(problems, {group: hash}) for the code hashes: every live family and code group equal under both registries; every new
    group computable."""
    probs, hashes = [], {}
    for g in sorted(live.FAMILY_CODE):
        try:
            a, b = group_hash(live.FAMILY_CODE, g, v2, root), group_hash(patched.FAMILY_CODE, g, v2, root)
        except OSError as ex:
            probs.append(f"code group {g}: unreadable file ({ex})")
            continue
        hashes[g] = b
        if a != b:
            probs.append(f"code group {g}: code_hash {a} under the live registry, {b} under the patched one")
    for f, g in sorted(live.FAMILY_GROUP.items()):
        if patched.FAMILY_GROUP.get(f) != g:
            probs.append(f"family {f}: code group {g} -> {patched.FAMILY_GROUP.get(f)}")
    for g in GROUPS:
        if g not in patched.FAMILY_CODE:
            continue
        try:
            hashes[g] = group_hash(patched.FAMILY_CODE, g, v2, root)
        except OSError as ex:
            probs.append(f"new code group {g}: {ex.filename or ex} is missing (§6.5 step 1 adds every prior33 file first)")
    return probs, hashes


def _family_of(rec):
    """The family of a unit record: row.family_id (core.new_record stores the plan row), else a top-level family_id."""
    row = rec.get("row")
    f = row.get("family_id") if isinstance(row, dict) else None
    f = f if isinstance(f, str) else rec.get("family_id")
    return f if isinstance(f, str) else None


def latest_records(units_dir):
    """The latest record (units/*.json, by mtime; the file name breaks ties) of each code group and of each (family, code group)
    pair -> {"dir", "present", "read", "groups": {group: (mtime, code_hash, file)}, "pairs": {(family, group): (mtime,
    code_hash, file)}, "without": records without a code_group / code_hash, "unreadable": [...]}. Reads JSON only."""
    res = {"dir": units_dir, "present": os.path.isdir(units_dir), "read": 0, "groups": {}, "pairs": {}, "without": 0, "unreadable": []}
    if not res["present"]:
        return res
    for e in os.scandir(units_dir):
        if not e.name.endswith(".json") or not e.is_file():
            continue
        try:
            with open(e.path, encoding="utf-8") as f:
                rec = json.load(f)
        except (OSError, ValueError) as ex:
            res["unreadable"].append(f"{e.name}: {ex!r}")
            continue
        res["read"] += 1
        g, h = (rec.get("code_group"), rec.get("code_hash")) if isinstance(rec, dict) else (None, None)
        if not isinstance(g, str) or not isinstance(h, str):
            res["without"] += 1
            continue
        key = (e.stat().st_mtime, e.name)  # the file name breaks mtime ties deterministically
        for table, k in ((res["groups"], g), (res["pairs"], (_family_of(rec), g))):
            if k not in table or key > (table[k][0], table[k][2]):
                table[k] = (key[0], h, e.name)
    return res


def record_problems(latest, hashes, reg, allow=(), new_groups=GROUPS, new_families=tuple(FAMILIES)):
    """(problems, notes, info) of the comparison with the latest unit records (§6.3: every existing family's code_hash is
    unchanged, against its latest unit record). `latest`: latest_records(); `hashes`: {code group: code_hash under the patched
    registry}; `reg`: the registry module whose existing groups and families must be covered (the live one; in check-run the
    live one, already patched). Fails closed: a missing units directory, a directory without any record carrying code_group /
    code_hash, an existing code group or family (all of reg's except new_groups / new_families) without a record unless it is
    named in `allow`, an `allow` name that is no existing group or family, and a latest record (per group, and per (family,
    group) pair) whose code_hash differs from `hashes` are problems. The prior33 groups and families have no records before
    their rows run; their records, once they exist, are compared like the others."""
    probs, notes, allow = [], [], set(allow or ())
    d = latest["dir"]
    groups = sorted(g for g in reg.FAMILY_CODE if g not in new_groups)
    fams = sorted(f for f in reg.FAMILY_GROUP if f not in new_families)
    policy = dict(getattr(reg, "POLICY_GROUP", None) or {})
    empty = not latest["present"] or not latest["groups"]
    if empty:   # fails closed whatever --allow-unrecorded names; the per-group / per-family lines would only repeat it
        probs.append(f"the units directory {d} " + ("does not exist" if not latest["present"] else
                     f"holds no unit record with code_group / code_hash ({latest['read']} records read)")
                     + f": none of the {len(groups)} existing code groups and {len(fams)} families can be compared with its latest unit "
                       f"record (§6.3)")
    unknown = sorted(allow - set(groups) - set(fams))
    if unknown:
        probs.append(f"--allow-unrecorded {unknown}: not an existing code group or family of the registry")
    with_rec = {f for f, _ in latest["pairs"] if f is not None}
    for kind, names, have in (() if empty else (("code group", groups, latest["groups"]), ("family", fams, with_rec))):
        for n in names:
            if n in have:
                if n in allow:
                    notes.append(f"--allow-unrecorded {n}: the {kind} has unit records; they are compared")
                continue
            if n in allow:
                notes.append(f"{kind} {n} has no unit record (allowed by --allow-unrecorded): its code_hash is compared with the live "
                             f"registry's only")
            else:
                probs.append(f"{kind} {n} has no unit record in {d}: its code_hash cannot be compared with a latest record (§6.3); if it "
                             f"has never run (registered by another lane), rerun this check with --allow-unrecorded {n}")
    for g, (_, h, name) in sorted(latest["groups"].items()):
        if g not in hashes:
            notes.append(f"records of code group {g!r}, which the registry does not define (latest {name}); not compared")
        elif hashes[g] != h:
            probs.append(f"code group {g}: the latest unit record {name} has code_hash {h}, the patched registry gives {hashes[g]}")
    pairs = 0
    for (f, g), (_, h, name) in sorted(latest["pairs"].items(), key=lambda kv: (str(kv[0][0]), kv[0][1])):
        if f is None or g not in hashes:
            continue
        if f not in reg.FAMILY_GROUP:
            notes.append(f"records of family {f!r} (code group {g}), which the registry does not bind (latest {name}); compared by group")
            continue
        if g not in (reg.FAMILY_GROUP[f], policy.get(f)):
            notes.append(f"family {f}: records under code group {g}, neither its group {reg.FAMILY_GROUP[f]} nor its policy group "
                         f"(latest {name})")
        pairs += 1
        if hashes[g] != h:
            probs.append(f"family {f} (code group {g}): its latest unit record {name} has code_hash {h}, the patched registry gives "
                         f"{hashes[g]}")
    info = {"units": d, "records_read": latest["read"], "without_code_group": latest["without"], "code_groups_required": len(groups),
            "code_groups_compared": sum(g in latest["groups"] for g in groups), "families_required": len(fams),
            "families_compared": sum(f in with_rec for f in fams), "family_group_pairs_compared": pairs,
            "allowed_unrecorded": sorted(allow)}
    return probs, notes + [f"unreadable record {u}" for u in latest["unreadable"]], info


# ------------------------------------------------------------------------------------------------------------ import closure
def module_file(name, root=REPO):
    """Repository file of module `name` (an ALN package module), or None."""
    if name.split(".")[0] not in ALN_PACKAGES:
        return None
    base = os.path.join(root, *name.split("."))
    for p in (base + ".py", os.path.join(base, "__init__.py")):
        if os.path.isfile(p):
            return p
    return None


def _import_nodes(tree):
    """[(node, eager)]: every import statement; eager = executed when the module is imported (not inside a function)."""
    out = []

    def walk(node, eager):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.Import, ast.ImportFrom)):
                out.append((ch, eager))
            elif isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                walk(ch, False)
            else:
                walk(ch, eager)
    walk(tree, True)
    return out


def imports_of(path, modname):
    """[(module, line, eager, kind)] for the imports of a file; kind 'module' (must exist) or 'member' (a name that may be a
    submodule: `from pkg import name`)."""
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), path)
    pkg = modname if os.path.basename(path) == "__init__.py" else modname.rpartition(".")[0]
    out = []
    for node, eager in _import_nodes(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                parts = a.name.split(".")
                out += [(".".join(parts[:i + 1]), node.lineno, eager, "module") for i in range(len(parts))]
            continue
        if node.level:
            base = pkg.split(".") if pkg else []
            if node.level > 1:
                base = base[: len(base) - (node.level - 1)]
            mod = ".".join(base + ([node.module] if node.module else []))
        else:
            mod = node.module or ""
        parts = mod.split(".")
        out += [(".".join(parts[:i + 1]), node.lineno, eager, "module") for i in range(len(parts))]
        out += [(f"{mod}.{a.name}", node.lineno, eager, "member") for a in node.names if a.name != "*"]
    return out


def inert_init(path):
    """A package __init__.py whose top level holds only a docstring and constant assignments (no imports, no calls)."""
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), path)
    for n in tree.body:
        if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant):
            continue
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant):
            continue
        return False
    return True


def closure(root_module, root=REPO):
    """Static import closure of `root_module` over this repository: {rel: (eager, via)} for every reached ALN module file
    (auditory_alignment_v3 modules are followed; ALN2 modules are recorded, not followed) and the unresolved v3 imports."""
    reached, unresolved = {}, []
    stack = [(root_module, True, "runner")]
    while stack:
        mod, eager, via = stack.pop()
        f = module_file(mod, root)
        if f is None:
            unresolved.append((mod, via))
            continue
        rel = os.path.relpath(f, root).replace(os.sep, "/")
        old = reached.get(rel)
        if old is not None and (old[0] or not eager):
            continue
        reached[rel] = (eager, via)
        if not mod.startswith(PKG):
            continue
        for name, line, e, kind in imports_of(f, mod):
            if name.split(".")[0] not in ALN_PACKAGES:
                continue
            nxt_eager = eager and e
            if module_file(name, root) is not None:
                stack.append((name, nxt_eager, f"{rel}:{line}"))
            elif kind == "module" and name.startswith(PKG):
                unresolved.append((name, f"{rel}:{line}"))
    return reached, unresolved


def closure_problems(code, v2, root=REPO):
    """(problems, notes) of the import closure of every prior33 group's runner against the group's files (module docstring)."""
    probs, notes = [], []
    v2rel = {f"{d}/{f}" for d, f in v2}
    for g in GROUPS:
        if g not in code:
            continue
        runner = f"{PKG}.{RUNNERS[g]}"
        if module_file(runner, root) is None:
            probs.append(f"{g}: runner module {runner} is missing")
            continue
        listed = {f"{d}/{f}" for d, f in code[g]}
        reached, unresolved = closure(runner, root)
        for name, via in unresolved:
            if name.startswith(PKG):
                probs.append(f"{g}: {via} imports {name}, which this repository does not hold")
        for rel, (eager, via) in sorted(reached.items()):
            if rel in listed or rel in NOT_HASHED:
                continue
            if rel.startswith(PKG + "/"):
                if os.path.basename(rel) == "__init__.py" and inert_init(os.path.join(root, rel)):
                    continue
                if eager:
                    probs.append(f"{g}: {rel} is imported at module level ({via}) but not hashed by the group: add it to "
                                 f"registry_patch.P33_FILES[{g!r}] and regenerate the patches, or import it lazily on the path that needs it")
                else:
                    notes.append(f"{g}: {rel} is reachable only through an import inside a function ({via}) and not hashed; hash it "
                                 f"if the group's units execute that code")
            elif rel not in v2rel and os.path.basename(rel) != "__init__.py":
                notes.append(f"{g}: ALN2 module {rel} ({via}) is outside core.V2_DEPS (not hashed; the existing families' convention)")
    return probs, notes


# ------------------------------------------------------------------------------------------------------------ the two checks
def _fresh_package():
    if f"{PKG}.core" in sys.modules or f"{PKG}.registry" in sys.modules or f"{PKG}.run" in sys.modules:
        raise RuntimeError("the import test needs a fresh interpreter (auditory_alignment_v3.core / registry / run already imported)")
    pkg = importlib.import_module(PKG)
    where = os.path.realpath(os.path.dirname(pkg.__file__))
    if where != os.path.realpath(os.path.join(REPO, PKG)):
        raise RuntimeError(f"{PKG} imports from {where}, not from this repository ({REPO}): run from the repository root")
    return pkg


def check_registry(patched_path, units_dir=None, allow=()):
    """check-registry (module docstring) -> (problems, notes, info). `allow`: the --allow-unrecorded names."""
    probs, notes, info = [], [], {}
    live = load_source(os.path.join(REPO, TARGET["registry"]), "_p33_registry_live")
    patched = load_source(patched_path, f"{PKG}.registry")
    probs += compare_registries(live, patched)
    pkg = _fresh_package()
    sys.modules[f"{PKG}.registry"] = patched
    pkg.registry = patched
    core = importlib.import_module(f"{PKG}.core")
    if core.FAMILY_CODE is not patched.FAMILY_CODE or core.FAMILY_GROUP is not patched.FAMILY_GROUP:
        probs.append("import test: auditory_alignment_v3.core did not take the patched registry's dictionaries")
    run = importlib.import_module(f"{PKG}.run")
    if run.FAMILY_GROUP is not patched.FAMILY_GROUP:
        probs.append("import test: auditory_alignment_v3.run did not take the patched registry's FAMILY_GROUP")
    p, hashes = hash_problems(live, patched, core.V2_DEPS)
    probs += p
    for f in sorted(live.FAMILY_GROUP):
        try:
            h = core.code_hash(f)
        except OSError as ex:
            probs.append(f"core.code_hash({f!r}): {ex}")
            continue
        if h != hashes.get(live.FAMILY_GROUP[f]):
            probs.append(f"core.code_hash({f!r}) = {h}, the live registry gives {hashes.get(live.FAMILY_GROUP[f])}")
    new = {}
    for f in FAMILIES:
        try:
            new[f] = core.code_hash(f)
        except (OSError, KeyError) as ex:
            probs.append(f"core.code_hash({f!r}): {ex!r}")
    info["prior33_code_hash"] = new
    p, n, info["records"] = record_problems(latest_records(units_dir or os.path.join(REPO, UNITS)), hashes, live, allow)
    probs += p
    notes += n
    p, n = closure_problems(patched.FAMILY_CODE, core.V2_DEPS)
    probs += p
    notes += n
    return probs, notes, info


def check_run(patched_path, units_dir=None, allow=()):
    """check-run (module docstring) -> (problems, notes, info). `allow`: the --allow-unrecorded names."""
    probs, notes, info = [], [], {}
    _fresh_package()
    reg = importlib.import_module(f"{PKG}.registry")
    missing = [f for f, g in FAMILIES.items() if reg.FAMILY_GROUP.get(f) != g]
    missing += [g for g in GROUPS if _norm(reg.FAMILY_CODE.get(g)) != _norm(group_files(g))]
    if missing:
        return [f"the live registry does not carry the prior33 groups / families {missing}: apply registry.prior33.patch first"], notes, info
    core = importlib.import_module(f"{PKG}.core")
    hashes = {}   # §6.3 for this edit too: every family's code_hash, and its latest unit record, as the registry patch left them
    for g in sorted(reg.FAMILY_CODE):
        try:
            hashes[g] = group_hash(reg.FAMILY_CODE, g, core.V2_DEPS)
        except OSError as ex:
            probs.append(f"code group {g}: unreadable file ({ex})")
    for f in sorted(reg.FAMILY_GROUP):
        try:
            h = core.code_hash(f)
        except (OSError, KeyError) as ex:
            probs.append(f"core.code_hash({f!r}): {ex!r}")
            continue
        if h != hashes.get(reg.FAMILY_GROUP[f]):
            probs.append(f"core.code_hash({f!r}) = {h}, its code group {reg.FAMILY_GROUP[f]} hashes to {hashes.get(reg.FAMILY_GROUP[f])}")
    p, n, info["records"] = record_problems(latest_records(units_dir or os.path.join(REPO, UNITS)), hashes, reg, allow)
    probs += p
    notes += n
    live = load_source(os.path.join(REPO, TARGET["run"]), f"{PKG}._p33_run_live")
    patched = load_source(patched_path, f"{PKG}.run", register=True)
    a, b = live.RUNNER, patched.RUNNER
    bad = sorted(k for k in a if b.get(k) != a[k])
    if bad:
        probs.append(f"RUNNER: live entries changed or removed: {bad}")
    clash = sorted(set(RUNNERS) & set(a))
    if clash:
        probs.append(f"RUNNER: collision, the live run.py already defines {clash}")
    added = {k: v for k, v in b.items() if k not in a}
    if added != {k: v for k, v in RUNNERS.items() if k not in a}:
        probs.append(f"RUNNER: added {added}, expected {RUNNERS}")
    for name in ("EXT_OFFSET", "LOCAL_FAMILIES", "PRIVATE_FAMILIES", "FM_FAMILIES"):
        if getattr(live, name, None) != getattr(patched, name, None):
            probs.append(f"{name} differs between the live and the patched run.py")
    for f, g in sorted(core.FAMILY_GROUP.items()):
        if g not in GROUPS:
            continue
        m = b.get(g)
        if m is None or module_file(f"{PKG}.{m}") is None or importlib.util.find_spec(f"{PKG}.{m}") is None:
            probs.append(f"family {f}: code group {g} has no runner module in this repository ({m!r})")
    info["prior33_runners"] = {g: b.get(g) for g in GROUPS}
    return probs, notes, info


def _report(name, probs, notes, info):
    for n in notes:
        print(f"note: {n}")
    for k, v in info.items():
        print(f"{k}: {json.dumps(v, sort_keys=True)}")
    if probs:
        for p in probs:
            print(f"PROBLEM: {p}")
        print(f"{name}: {len(probs)} problem(s); nothing may be replaced")
        return 1
    print(f"{name}: ok")
    return 0


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = a.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("check-registry")
    u = sub.add_parser("check-run")
    for p in (r, u):
        p.add_argument("file")
        p.add_argument("--units", help="unit-record directory (default: the live units directory, read only); the same fail-closed rules")
        p.add_argument("--allow-unrecorded", action="append", default=[], metavar="NAME",
                       help="an existing code group or family without any unit record (never run; confirm first); repeatable")
    w = sub.add_parser("write-patches")
    w.add_argument("--out", help=f"output directory (default {PATCH_DIR})")
    w.add_argument("--generated", help="header timestamp (default: now)")
    args = a.parse_args(argv)
    if args.cmd == "write-patches":
        for kind, (live, patched) in write_patches(args.out, generated=args.generated).items():
            print(f"{kind}: live {live} -> patched {patched}")
        return 0
    if args.cmd == "check-registry":
        return _report("check-registry", *check_registry(args.file, args.units, args.allow_unrecorded))
    return _report("check-run", *check_run(args.file, args.units, args.allow_unrecorded))


if __name__ == "__main__":
    sys.exit(main())
