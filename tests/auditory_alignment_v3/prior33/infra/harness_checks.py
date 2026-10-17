"""Python checks of tests/auditory_alignment_v3/prior33/infra/run_harness.sh (M10; PUBLIC_PRIOR_DESIGN.md §6.5, §7.1 item 15).

  make_queue   <patched make_queue.py>
      Runs the PATCHED copy of make_queue.py as a script against a sandbox OUT: a fake auditory_alignment_v3 package (core with
      OUT = the sandbox, registry, the runner modules make_queue imports; every fake function raises if called) whose prior33
      is the real package (symlink), so the real prior33.deps.write_queue writes the prior queue. Cases: a normal pass (prior
      files equal a direct deps.write_queue call; fm / small written by the generic path with no prior row in them; held ids and
      held families respected); the .remaining marker: 'held' while open prior rows are held or unbound and nothing is left in
      scope (families unbound, all six families held, the target family held after everything else is done), 0 for a complete
      lane and when the held rows are done or failed; an inconsistent plan and a failing prior33 import (prior files empty,
      counters 'unknown', fm / small still written, exit status 0).
  ckpt_offload <patched ckpt_offload.py> <unpatched copy>
      Imports both copies (the module body has no side effects) with fake runner modules and checks NO_DEPS / HANDLED /
      P33_FAMILIES (only the six prior families added), the other constants unchanged, deps_of on prior rows (owners from
      prior33.deps.ckpt_deps, no reason), an unknown prior family and a malformed prior row (fail closed), and that the unpatched
      copy fails closed on them. Then it runs the real one_pass() of both copies on sandbox trees (every path constant of the
      module redirected into the sandbox before the pass; all_rows replaced by the sandbox plan): a normal prior queue, make_queue's
      error state (queue_v3_prior.txt empty, .remaining 'unknown'), the error state with a dependent claimed, a blocked zero-shot
      row (its bridge failed), a held target and a complete lane. A done donor group's _best.pt files must stay on home while any
      of its dependents is without a record, whatever the queue file says; _bridge.npz and _stable files never move.

Prints "ok ..." / "FAIL ..." lines and exits 1 on any failure. CPU only; never reads or writes the live pool, queue, units or
ckpt files (the patched modules' live path constants are overridden before any pass and checked to be outside the repo)."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
PRIOR33 = os.path.join(REPO, "auditory_alignment_v3", "prior33")
PRE = "ALN32_PUBLIC_AUDIO_PRIOR_"
SIX = [PRE + x for x in ("DONOR", "CSX_DONOR", "RICH_DONOR", "BRIDGE", "TARGET", "ZEROSHOT")]
FAILS = []


def check(cond, what):
    print(("ok   " if cond else "FAIL ") + what, flush=True)
    if not cond:
        FAILS.append(what)
    return cond


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def read(path):
    with open(path) as f:
        return f.read()


# ------------------------------------------------------------------------------------------- synthetic plan (passes check_plan)
def _mk(fam, ds, spec, deps, sf=None, cf=None, seed=3401):
    e = "ALN3X_" + hashlib.sha256(json.dumps([fam, ds, sf, cf, seed, spec], sort_keys=True).encode()).hexdigest()[:16]
    return {"dataset": ds, "subject_fold": sf, "content_fold": cf, "seed": seed, "seed_scope": "breadth", "experiment_id": e,
            "family_id": fam, "job_kind": "eval" if fam == PRE + "ZEROSHOT" else "train", "spec": spec,
            "registered": "M10 infra harness (synthetic)", "logical_dependencies": list(deps), "status": "registered_extension"}


def prior_plan(with_jstar=False):
    """name -> row: core group G (fau) with bridge B, donor target T, from-scratch target TS and zero-shot Z (and, with_jstar,
    a J* target TJ); rich group R with bridge BR; core group Gd (dtu) with CSX group X and its bridge BX."""
    from auditory_alignment_v3.prior33 import deps as D
    from auditory_alignment_v3.prior33 import select as S
    n = {}

    def group(name, ds, fam, block, horizon=None, deps=("frozen_manifest",), **kw):
        spec = {"stage": "donor_group", "block": block, "queue_tier": D.BLOCK_TIER[block], "objective": "NCE",
                "members": list(S.GROUP_MEMBERS[fam]), "donor_seed": 3401, "sampler_seed": 3401, "lambda_rule": S.LAMBDA_RULE,
                "budget": {"epoch_equivalents": 30, "continuation": "group_wsd_any_last3_ext10_limit60_v1"}, **kw}
        if horizon:
            spec["horizon_from"] = n[horizon]["experiment_id"]
            deps = tuple(deps) + (n[horizon]["experiment_id"],)
        n[name] = _mk(fam, ds, spec, deps)

    def bridge(name, g, member):
        G = n[g]
        spec = {"stage": "bridge", "block": G["spec"]["block"], "queue_tier": G["spec"]["queue_tier"], "objective": "NCE",
                "donor_seed": 3401, "donor_group": G["experiment_id"], "member": member, "bridge": "ridge_u_to_stdenv8_v1"}
        n[name] = _mk(S.BRIDGE, G["dataset"], spec, [G["experiment_id"]])

    def target(name, g, member, ds=None):
        if g:
            G = n[g]
            spec = {"stage": "target", "block": G["spec"]["block"], "queue_tier": G["spec"]["queue_tier"], "objective": "NCE",
                    "variant": member, "init": "donor", "donor_group": G["experiment_id"], "donor_seed": 3401, "target_seed": 3401,
                    "member": member}
            n[name] = _mk(S.TARGET, G["dataset"], spec, [G["experiment_id"]], 0, 0)
        else:
            spec = {"stage": "target", "block": "core", "queue_tier": 1, "objective": "NCE", "variant": "S", "init": "random",
                    "donor_group": None, "donor_seed": None, "target_seed": 3401, "member": None}
            n[name] = _mk(S.TARGET, ds, spec, [], 0, 0)

    def zeroshot(name, g, b, member):
        G = n[g]
        spec = {"stage": "zero_shot", "block": G["spec"]["block"], "queue_tier": G["spec"]["queue_tier"], "objective": "NCE",
                "mode": "A", "variant": "zero_shot__no_target_supervised_fit" + D.ZS_SUFFIX["A"], "member": member, "donor_seed": 3401,
                "donor_group": G["experiment_id"], "bridge": n[b]["experiment_id"], "job_kind": "eval"}
        n[name] = _mk(S.ZEROSHOT, G["dataset"], spec, [G["experiment_id"], n[b]["experiment_id"]], 0, 0)

    group("G", "fau", S.DONOR, "core")
    bridge("B", "G", "AP")
    target("T", "G", "AP")
    if with_jstar:
        target("TJ", "G", "J*")
    target("TS", None, None, ds="fau")
    zeroshot("Z", "G", "B", "AP")
    group("R", "fau", S.RICH_DONOR, "rich", horizon="G", deps=("frozen_manifest", "rich_cache"),
          rich_targets={"ss": "whisper_logmel_pca4_sk_v1", "sc": "flux_pca4_v1"}, loss_weights=[1, 0.5, 0.5])
    bridge("BR", "R", "APR")
    group("Gd", "dtu", S.DONOR, "core")
    group("X", "dtu", S.CSX_DONOR, "csx", horizon="Gd", extra_strata=["fau_cs"])
    bridge("BX", "X", "APC")
    D.check_plan(list(n.values()))
    return n


def filler(k):
    return _mk("A_LOCAL", "fau", {"architecture": "lag_local_tokens", "window": "full", "objective": "NCE", "k": k}, [], 0, 0)


# ----------------------------------------------------------------------------------------------------- fake package
FAKE_FUNCS = {"run_complement": ("base_ready", "base_row"), "policy": ("resolve",), "run_attention": ("twin_ready", "twin_row"),
              "run_distill": ("teachers_ready", "candidates"), "run_e_complement": ("base_ready", "base_row"),
              "run_transfer": ("donor_ready", "local_donor_row"), "complement32": ("base_ready", "base_row"),
              "residual32": ("base_ready", "base_row"), "run_attention_policy": ("lag_twin_ready", "lag_twin_row"),
              "run_coverage_policy": ("lag_base_ready", "lag_base_row")}


def fake_package(root, out, family_group, with_prior33=True):
    pkg = os.path.join(root, "auditory_alignment_v3")
    write(os.path.join(pkg, "__init__.py"), "")
    write(os.path.join(pkg, "core.py"), f"OUT = {out!r}\nFAMILY_GROUP = {family_group!r}\n\n\ndef load_rows():\n    return []\n")
    write(os.path.join(pkg, "registry.py"), "POLICY_GROUP = {}\n")
    for m, fns in FAKE_FUNCS.items():
        write(os.path.join(pkg, f"{m}.py"), "".join(f"def {f}(*a, **k):\n    raise AssertionError('fake {m}.{f} called')\n\n\n"
                                                    for f in fns))
    if with_prior33:
        os.symlink(PRIOR33, os.path.join(pkg, "prior33"))
    return root


DRIVER = """import runpy, sys
sys.path.insert(0, sys.argv[1])
import auditory_alignment_v3  # the fake package: cached, so make_queue's sys.path.insert(0, REPO) cannot replace it
assert auditory_alignment_v3.__file__.startswith(sys.argv[1]), auditory_alignment_v3.__file__
sys.argv = [sys.argv[2]]
runpy.run_path(sys.argv[0], run_name="__main__")
"""


def run_make_queue(patched, fake_root, out):
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONSTARTUP")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    r = subprocess.run([sys.executable, "-B", "-c", DRIVER, fake_root, patched], cwd=out, env=env, capture_output=True,
                       text=True, timeout=300)
    return r.returncode, r.stdout, r.stderr


PRIOR_FILES = ("queue_v3_prior.txt", "queue_v3_prior_weights.txt", "queue_v3_prior.remaining", "queue_v3_prior.waiting",
               "queue_v3_prior.blocked")


def sandbox_out(base, rows_ext, hold_fams=(), held_ids=()):
    out = os.path.join(base, "out")
    for d in ("units", "ckpt", "pool/queue_v3_prior", "governance", "logs"):
        os.makedirs(os.path.join(out, d), exist_ok=True)
    write(os.path.join(out, "plan_ext.jsonl"), "".join(json.dumps(r) + "\n" for r in rows_ext))
    write(os.path.join(out, "families_on_hold.json"), json.dumps(list(hold_fams)))
    if held_ids:
        write(os.path.join(out, "governance", "held_executions.json"), json.dumps({"ids": list(held_ids)}))
    return out


def check_make_queue(patched, base):
    sys.path.insert(0, REPO)
    from auditory_alignment_v3.prior33 import deps as D
    from auditory_alignment_v3.prior33 import select as S
    n = prior_plan()
    fill = [filler(k) for k in range(3)]
    prior_rows = list(n.values())
    ext = fill[:2] + prior_rows[:5] + fill[2:] + prior_rows[5:]
    fg = {f: "x" for f in SIX} | {"A_LOCAL": "local"}
    held = n["T"]["experiment_id"]

    # 1. normal pass
    b1 = os.path.join(base, "mq_normal")
    out = sandbox_out(b1, ext, hold_fams=[], held_ids=[held])
    g = n["G"]["experiment_id"]
    write(S.record_path(out, g), json.dumps({"experiment_id": g, "status": "complete", "row": n["G"]}))
    write(S.member_ckpt(out, g, "AP"), "")
    write(os.path.join(out, "pool", "queue_v3_prior", f"{n['Gd']['experiment_id']}.failed"), "")
    rc, so, se = run_make_queue(patched, fake_package(os.path.join(b1, "fake"), out, fg), out)
    check(rc == 0, f"make_queue (patched): normal pass exits 0 (stderr tail: {se[-400:]!r})")
    lines = so.splitlines()
    check(any(ln.startswith("small 3 ") for ln in lines) and any(ln.startswith("fm 0 ") for ln in lines),
          "make_queue (patched): the generic path still writes small (3 filler rows) and fm (0)")
    pl = [ln for ln in lines if ln.startswith("prior ")]
    # states: G done, Gd failed, B / TS / R ready, Z / BR waiting, X / BX blocked (Gd failed), T held (out of scope)
    check(len(pl) == 1 and "'ready': 3, 'waiting': 2, 'blocked': 2, 'done': 1, 'failed': 1" in pl[0],
          f"make_queue (patched): one prior summary line with the expected states {pl}")
    small = read(os.path.join(out, "queue_v3_small.txt")).splitlines()
    check(sorted(ln.split("|")[0] for ln in small) == sorted(r["experiment_id"] for r in fill)
          and all(len(ln.split("|")) == 2 for ln in small), "make_queue (patched): queue_v3_small.txt = the filler rows, two fields")
    check(read(os.path.join(out, "queue_v3_fm.txt")) == "", "make_queue (patched): queue_v3_fm.txt holds no prior row")
    got = {f: read(os.path.join(out, f)) for f in PRIOR_FILES}
    D.write_queue(out, ext, held={held}, bound=set(SIX), ext=ext)  # the same call, in process (deterministic output)
    want = {f: read(os.path.join(out, f)) for f in PRIOR_FILES}
    check(got == want, "make_queue (patched): prior files equal deps.write_queue(O, ALL, held=HELD|hold, bound=..., ext=EXT)")
    q = got["queue_v3_prior.txt"].splitlines()
    ids = [ln.split("|")[0] for ln in q]
    check(all(len(ln.split("|")) == 3 for ln in q) and len(q) == 7, f"make_queue (patched): 7 three-field prior lines ({len(q)})")
    check(held not in ids and n["X"]["experiment_id"] not in ids
          and got["queue_v3_prior.blocked"].split() == [n["X"]["experiment_id"], n["BX"]["experiment_id"]],
          "make_queue (patched): the held id is out of scope; the failed group's dependents are blocked, not listed")
    pos = {r["experiment_id"]: 100000 + j for j, r in enumerate(ext)}
    check(all(int(ln.split("|")[1]) == pos[ln.split("|")[0]] for ln in q), "make_queue (patched): idx = 100000 + plan_ext position")
    check(got["queue_v3_prior.remaining"].strip() == "5" and got["queue_v3_prior.waiting"].strip() == "2",
          f"make_queue (patched): remaining 5, waiting 2 ({got['queue_v3_prior.remaining']!r}, {got['queue_v3_prior.waiting']!r})")
    check(not [f for f in os.listdir(out) if "tmp" in f], "make_queue (patched): no tmp files left")

    # 2. a held family (families_on_hold.json)
    b2 = os.path.join(base, "mq_hold")
    out = sandbox_out(b2, ext, hold_fams=[PRE + "TARGET"])
    rc, so, _ = run_make_queue(patched, fake_package(os.path.join(b2, "fake"), out, fg), out)
    q = read(os.path.join(out, "queue_v3_prior.txt")).splitlines()
    check(rc == 0 and len(q) == len(prior_rows) - 2 and not {n["T"]["experiment_id"], n["TS"]["experiment_id"]} & {ln.split("|")[0] for ln in q},
          "make_queue (patched): a family in families_on_hold.json is out of the prior queue")

    # 3. the .remaining marker: 'held' (paused) versus 0 (complete)
    def done(out, keys):
        for k in keys:
            write(S.record_path(out, n[k]["experiment_id"]), json.dumps({"experiment_id": n[k]["experiment_id"], "status": "complete"}))

    def marker(name, fgroup, hold_fams=(), held_ids=(), done_keys=(), failed_keys=()):
        bx = os.path.join(base, name)
        out = sandbox_out(bx, ext, hold_fams=hold_fams, held_ids=held_ids)
        done(out, done_keys)
        for k in failed_keys:
            write(os.path.join(out, "pool", "queue_v3_prior", f"{n[k]['experiment_id']}.failed"), "")
        rc, so, se = run_make_queue(patched, fake_package(os.path.join(bx, "fake"), out, fgroup), out)
        rem = read(os.path.join(out, "queue_v3_prior.remaining")) if os.path.exists(os.path.join(out, "queue_v3_prior.remaining")) else None
        pl = [ln for ln in so.splitlines() if ln.startswith("prior ")]
        return rc, rem, read(os.path.join(out, "queue_v3_prior.txt")), pl, se, out

    every = list(n)
    rc, rem, qtxt, pl, se, _ = marker("mq_unbound", {"A_LOCAL": "local"})
    check(rc == 0 and qtxt == "" and rem == "held\n" and pl and "paused=10" in pl[0],
          f"make_queue (patched): families unbound (before the registry edit): prior queue empty, .remaining 'held' ({rem!r}, {pl}, {se[-200:]!r})")
    rc, rem, qtxt, pl, _, _ = marker("mq_allheld", fg, hold_fams=SIX)
    check(rc == 0 and qtxt == "" and rem == "held\n", f"make_queue (patched): all six families held: .remaining 'held' ({rem!r})")
    rc, rem, qtxt, pl, _, _ = marker("mq_paused_target", fg, hold_fams=[PRE + "TARGET"], done_keys=[k for k in every if k not in ("T", "TS")])
    check(rc == 0 and rem == "held\n" and len(qtxt.splitlines()) == len(prior_rows) - 2,
          f"make_queue (patched): target family held, everything else done: .remaining 'held', not 0 ({rem!r})")
    rc, rem, qtxt, pl, _, _ = marker("mq_complete", fg, done_keys=every)
    check(rc == 0 and rem == "0\n" and len(qtxt.splitlines()) == len(prior_rows),
          f"make_queue (patched): every prior row done, nothing held: .remaining 0 (lane complete) ({rem!r})")
    rc, rem, qtxt, pl, _, _ = marker("mq_held_done", fg, hold_fams=[PRE + "TARGET"], done_keys=every)
    check(rc == 0 and rem == "0\n", f"make_queue (patched): the held rows are done themselves: .remaining 0 ({rem!r})")
    rc, rem, qtxt, pl, _, _ = marker("mq_held_failed", fg, held_ids=[n["T"]["experiment_id"]], done_keys=[k for k in every if k != "T"],
                                     failed_keys=["T"])
    check(rc == 0 and rem == "0\n", f"make_queue (patched): the only held row carries a .failed marker: .remaining 0 ({rem!r})")

    # 4. an inconsistent plan and 5. a failing prior33 import: empty prior files, 'unknown' counters, fm / small unaffected
    bad = json.loads(json.dumps(n["B"]))
    bad["spec"]["block"] = "csx2"
    bad["experiment_id"] = "ALN3X_" + "e" * 16
    for name, rows, with_p33, expect in (("mq_planerror", ext + [bad], True, "ValueError"),
                                         ("mq_importerror", ext, False, "ModuleNotFoundError")):
        bx = os.path.join(base, name)
        out = sandbox_out(bx, rows)
        for f in PRIOR_FILES:  # a previous, valid prior queue must not survive the error
            write(os.path.join(out, f), "stale\n")
        rc, so, se = run_make_queue(patched, fake_package(os.path.join(bx, "fake"), out, fg, with_prior33=with_p33), out)
        files = {f: read(os.path.join(out, f)) for f in PRIOR_FILES}
        check(rc == 0 and f"prior queue error {expect}" in so, f"make_queue (patched): {name}: error printed, exit 0 ({so.splitlines()[-1:]}, {se[-300:]!r})")
        check(files == {"queue_v3_prior.txt": "", "queue_v3_prior_weights.txt": "", "queue_v3_prior.blocked": "",
                        "queue_v3_prior.remaining": "unknown\n", "queue_v3_prior.waiting": "unknown\n"},
              f"make_queue (patched): {name}: prior files empty, .remaining / .waiting 'unknown' (never 0)")
        check(len(read(os.path.join(out, "queue_v3_small.txt")).splitlines()) == 3 and os.path.exists(os.path.join(out, "queue_v3_fm.txt")),
              f"make_queue (patched): {name}: the small and fm queues are still written")


# ----------------------------------------------------------------------------------------------------- ckpt_offload
def load_module(path, name):
    from importlib.machinery import SourceFileLoader  # any file name (the unpatched copy has no .py suffix)
    spec = importlib.util.spec_from_loader(name, SourceFileLoader(name, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


OLD = 1_700_000_000  # an mtime far older than MIN_AGE


def offload_tree(base, name, n, done, failed=(), claimed=(), held=(), queue="real"):
    """A sandbox OUT for one_pass: plan_ext = the prior plan, unit records and checkpoint files of the done rows (donor groups:
    _best / _gainsel_best / _h30_best per member and a _stable57 state; bridges: _bridge.npz; targets: _best.pt), .failed markers,
    claims, and the prior queue written by deps.write_queue (queue='real', held rows out of scope as make_queue passes them) or
    make_queue's error state (queue='error')."""
    from auditory_alignment_v3.prior33 import deps as D
    from auditory_alignment_v3.prior33 import select as S
    out = os.path.join(base, name, "out")
    for d in ("units", "ckpt", "pool/queue_v3_prior", "logs"):
        os.makedirs(os.path.join(out, d), exist_ok=True)
    rows = list(n.values())
    write(os.path.join(out, "plan_ext.jsonl"), "".join(json.dumps(r) + "\n" for r in rows))
    for k in done:
        r = n[k]
        e = r["experiment_id"]
        rec = {"experiment_id": e, "status": "complete", "row": r}
        if S.stage_of(r) == "donor_group":
            rec["members"] = {m: {"best": {"ce_dev": 1.0 + i}} for i, m in enumerate(S.group_members(r))}
            for m in S.group_members(r):
                for kind in ("best", "gainsel", "h30"):
                    write(S.member_ckpt(out, e, m, kind), "x")
                write(S.stable_ckpt(out, e, m), "x")
        elif S.stage_of(r) == "bridge":
            write(S.bridge_npz(out, e), "x")
        else:
            write(os.path.join(out, "ckpt", f"{e}_best.pt"), "x")
        write(S.record_path(out, e), json.dumps(rec))
    for k in failed:
        write(os.path.join(out, "pool", "queue_v3_prior", n[k]["experiment_id"] + ".failed"), "")
    for k in claimed:
        write(os.path.join(out, "pool", "queue_v3_prior", n[k]["experiment_id"] + ".claim", "job"), "9999\n")
    for p in os.listdir(os.path.join(out, "ckpt")):
        os.utime(os.path.join(out, "ckpt", p), (OLD, OLD))
    if queue == "real":
        D.write_queue(out, rows, held={n[k]["experiment_id"] for k in held}, bound=set(SIX), ext=rows)
    else:  # make_queue.prior_queue's except branch
        for suf, txt in ((".txt", ""), ("_weights.txt", ""), (".blocked", ""), (".remaining", "unknown\n"), (".waiting", "unknown\n")):
            write(os.path.join(out, "queue_v3_prior" + suf), txt)
    return out, rows


def run_pass(mod, out, rows):
    """one_pass() of `mod` with every path constant inside the sandbox; returns (moved names, log text)."""
    dest = os.path.join(os.path.dirname(out), "projects_ckpt")
    for k, v in {"OUT": out, "SRC": out + "/ckpt", "DEST": dest, "MAN": out + "/ckpt_offload_manifest.tsv",
                 "LOG": out + "/logs/ckpt_offload.log", "STOP": out + "/STOP_ckpt_offload", "LOCK": out + "/.ckpt_offload.lock",
                 "MIN_AGE": 0, "MIN_FREE_DEST": 0}.items():
        setattr(mod, k, v)
    assert not any(os.path.realpath(getattr(mod, k)).startswith(REPO + os.sep) for k in ("OUT", "SRC", "DEST", "MAN", "LOG", "STOP", "LOCK"))
    mod.all_rows = lambda: rows
    mod.one_pass(dry=False)
    ck = out + "/ckpt"
    moved = sorted(p for p in os.listdir(ck) if os.path.islink(os.path.join(ck, p)))
    return moved, (read(mod.LOG) if os.path.exists(mod.LOG) else "")


def check_ckpt_offload(patched, unpatched, base):
    root = fake_package(os.path.join(base, "co_fake"), os.path.join(base, "co_out_unused"), {})
    sys.path.insert(0, root)
    import auditory_alignment_v3  # noqa: F401  (the fake package, with the real prior33)
    assert auditory_alignment_v3.__file__.startswith(root)
    from auditory_alignment_v3.prior33 import deps as D
    new, old = load_module(patched, "ckpt_offload_patched"), load_module(unpatched, "ckpt_offload_live_copy")
    check(new.NO_DEPS - old.NO_DEPS == {PRE + "DONOR", PRE + "CSX_DONOR"} and old.NO_DEPS <= new.NO_DEPS,
          "ckpt_offload (patched): NO_DEPS gains exactly the core/panel and CSX donor families")
    check(new.HANDLED - old.HANDLED == {PRE + x for x in ("RICH_DONOR", "BRIDGE", "TARGET", "ZEROSHOT")} and old.HANDLED <= new.HANDLED,
          "ckpt_offload (patched): HANDLED gains exactly the rich donor, bridge, target and zero-shot families")
    check(getattr(new, "P33_FAMILIES", None) == set(SIX) and not hasattr(old, "P33_FAMILIES"),
          "ckpt_offload (patched): P33_FAMILIES = the six prior families")
    same = all(getattr(new, k) == getattr(old, k) for k in ("REPO", "OUT", "SRC", "DEST", "MAN", "LOG", "STOP", "LOCK", "MIN_AGE",
                                                             "MIN_FREE_DEST", "FATAL_ERRNO")) and new.EID.pattern == old.EID.pattern
    check(same, "ckpt_offload (patched): every other constant (paths, EID regex, ages) is unchanged")
    n = prior_plan()
    fill = [filler(0)]
    rows = fill + list(n.values())
    pending = {r["experiment_id"] for r in rows}
    want = set().union(*(D.ckpt_deps(r, rows) for r in n.values()))
    got, why = new.deps_of(pending, rows)
    check(why == "" and got == want == {n[k]["experiment_id"] for k in ("G", "R", "X")},
          f"ckpt_offload (patched): deps_of on prior rows = the owners from prior33.deps.ckpt_deps, no reason ({why!r})")
    eid = new.EID.match(f"{n['G']['experiment_id']}_mJ025_gainsel_best.pt")
    check(eid is not None and eid.group(1) == n["G"]["experiment_id"], "ckpt_offload (patched): member checkpoints map to their group id")
    foo = json.loads(json.dumps(n["B"]))
    foo["family_id"], foo["experiment_id"] = PRE + "FOO", "ALN3X_" + "f" * 16
    _, why = new.deps_of({foo["experiment_id"]}, rows + [foo])
    check("unmodelled family" in why, f"ckpt_offload (patched): an unknown prior family still fails closed ({why!r})")
    broken = json.loads(json.dumps(n["B"]))
    broken["experiment_id"], broken["spec"]["donor_group"] = "ALN3X_" + "a" * 16, "ALN3X_" + "b" * 16
    broken["logical_dependencies"] = [broken["spec"]["donor_group"]]
    _, why = new.deps_of({broken["experiment_id"]}, rows + [broken])
    check(why.startswith("dependency lookup failed"), f"ckpt_offload (patched): a malformed prior row fails the pass closed ({why[:120]!r})")
    _, why = old.deps_of(pending, rows)
    check("unmodelled family ALN32_PUBLIC_AUDIO_PRIOR_" in why,
          "ckpt_offload (live copy, unpatched): fails closed on prior rows (hence the patch and the daemon restart)")

    # the real one_pass on sandbox trees
    n = prior_plan(with_jstar=True)
    G, TS, Gd = (n[k]["experiment_id"] for k in ("G", "TS", "Gd"))

    def of(moved, e):
        return [p for p in moved if p.startswith(e + "_")]

    first = ("G", "B", "TS", "Gd")  # done; T, TJ, Z, R, BR, X and BX still to run
    out, rows = offload_tree(base, "op_normal", n, done=first)
    moved, log = run_pass(new, out, rows)
    check(not of(moved, G), f"one_pass (patched), normal queue: no _best.pt of G while T / TJ / Z / R are pending ({len(of(moved, G))} moved)")
    check(of(moved, TS) == [f"{TS}_best.pt"], "one_pass (patched), normal queue: a done unit without dependents (TS) is offloaded")
    check(len(of(moved, Gd)) == 15, "one_pass (patched), normal queue: Gd's 15 _best.pt files move while its CSX group X is pending "
                                    "(by design: X reads only Gd's record)")
    check(all(p.endswith("_best.pt") for p in moved) and not [p for p in os.listdir(out + "/ckpt") if ("_stable" in p or "_bridge" in p)
                                                               and os.path.islink(os.path.join(out, "ckpt", p))],
          "one_pass (patched): _bridge.npz and _stable states never move")

    out, rows = offload_tree(base, "op_error", n, done=first, queue="error")
    moved, log = run_pass(new, out, rows)
    check(not of(moved, G) and of(moved, TS) == [f"{TS}_best.pt"],
          f"one_pass (patched), make_queue's error state (empty prior queue): G stays on home, TS moves ({len(of(moved, G))} G files moved)")
    out, rows = offload_tree(base, "op_error_claim", n, done=first, claimed=("T",), queue="error")
    moved, _ = run_pass(new, out, rows)
    check(not of(moved, G), "one_pass (patched), error state with T claimed: G stays on home")
    out, rows = offload_tree(base, "op_blocked", n, done=("G", "T", "TJ", "R", "BR", "TS", "Gd", "X", "BX"), failed=("B",))
    moved, _ = run_pass(new, out, rows)
    blk = read(out + "/queue_v3_prior.blocked").split()
    check(blk == [n["Z"]["experiment_id"]] and not of(moved, G),
          "one_pass (patched), Z blocked (its bridge B failed, Z not in the queue file): G stays on home")
    out, rows = offload_tree(base, "op_held", n, done=[k for k in n if k != "T"], held=("T",))
    moved, _ = run_pass(new, out, rows)
    listed = {ln.split("|")[0] for ln in read(out + "/queue_v3_prior.txt").splitlines()}
    check(n["T"]["experiment_id"] not in listed and not of(moved, G),
          "one_pass (patched), T held (out of the queue file) and everything else done: G stays on home until T is done")
    out, rows = offload_tree(base, "op_complete", n, done=list(n))
    best = sorted(p for p in os.listdir(out + "/ckpt") if new.EID.match(p))
    moved, _ = run_pass(new, out, rows)
    check(len(of(moved, G)) == 15 and moved == best and len(best) == 15 + 15 + 3 + 6 + 4,
          f"one_pass (patched), lane complete: every _best.pt moves, G's 15 included ({len(moved)} of {len(best)} files)")

    out, rows = offload_tree(base, "op_unpatched_queued", n, done=first)
    moved, log = run_pass(old, out, rows)
    check(moved == [] and "pass skipped (fail closed): unmodelled family ALN32_PUBLIC_AUDIO_PRIOR_" in log,
          "one_pass (live copy, unpatched), prior rows queued: every pass fails closed, nothing moves")
    out, rows = offload_tree(base, "op_unpatched_error", n, done=first, queue="error")
    moved, _ = run_pass(old, out, rows)
    check(len(of(moved, G)) == 15,
          "one_pass (live copy, unpatched), prior error state: G's files move (fail open), so the restart (step 3) precedes step 5")


def main():
    cmd = sys.argv[1]
    base = tempfile.mkdtemp(prefix=f"{cmd}_", dir=os.environ.get("ALN33_HARNESS_DIR") or None)
    assert not os.path.realpath(base).startswith(REPO + os.sep), base
    if cmd == "make_queue":
        check_make_queue(os.path.abspath(sys.argv[2]), base)
    elif cmd == "ckpt_offload":
        check_ckpt_offload(os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3]), base)
    else:
        raise SystemExit(f"unknown command {cmd}")
    print(f"{cmd}: {len(FAILS)} failure(s)")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
