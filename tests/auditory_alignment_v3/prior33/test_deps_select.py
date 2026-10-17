"""M8 synthetic tests (PUBLIC_PRIOR_DESIGN.md §7.1 items 11 and 13; §2.9, §2.10, §4.1-§4.3, §6.5): select.py slots, the joint
lambda rule and the pinned donor-group record interface; deps.py upstreams, plan checks, readiness, transitive blocking,
checkpoint owners, queue order and the queue_v3_prior files, on a synthetic plan with donor -> bridge -> target / zero-shot
chains, rich and CSX groups, held rows, failed rows and continuation versions. The queue files are also read by the live
readers' own code (watch_anyhost.sh unclaimed(), ckpt_offload.py queued() and EID, aln3_gpu_pool.sbatch's read lines), taken
verbatim from the repository and run read-only against a temporary directory. CPU only; every file lives in a pytest
temporary directory (never the live pool, units or queue files).

M8 review fixes (tests in the sections marked M8 review): one-shot iterables are read once (check_plan, write_queue and the
single-row functions); a horizon group of the row's own execution version (compute limit, continuation depth, the continuation
of the source's horizon group); the pinned version label spec.version ('continuation_<depth>' on continuation groups and their
rows, none on primary rows) and the continuation_of label of slot rows; no access-block XM row and no slot row on J1 / J025;
unresolved J* rows waiting but not listed in the queue; ckpt_deps on a prebuilt index without a pass over it. Round 3: the low
items (c)-(i) (one bridge per slot, no CSX group for fau, panel rows private_bdf only, the §4.3 seed fields, a continuation in its
source's block, variant = member, no empty members list) and names_limit kept in deps.py with select's regex."""
import ast
import glob
import hashlib
import itertools
import json
import math
import os
import re
import subprocess
import sys

import pytest

from auditory_alignment_v3.prior33 import deps as D
from auditory_alignment_v3.prior33 import select as S

CORE = ("AP", "XP", "J1", "J025", "XM")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LIVE = os.path.join(REPO, "private", "auditory_alignment_v3")
POOL_SBATCH = os.path.join(REPO, "slurm", "aln3_gpu_pool.sbatch")
DEL = object()
V1, V2 = "continuation_1", "continuation_2"  # the pinned spec.version labels (deps.version_label) of continuation depths 1 and 2


# ----------------------------------------------------------------------------------------------------------- synthetic plan
def _mk(fam, ds, spec, deps, sf, cf, seed, prefix="ALN3X_"):
    e = prefix + hashlib.sha256(json.dumps([fam, ds, sf, cf, seed, spec], sort_keys=True).encode()).hexdigest()[:16]
    return {"dataset": ds, "subject_fold": sf, "content_fold": cf, "seed": seed, "seed_scope": "breadth" if seed == 3401 else "panel",
            "experiment_id": e, "family_id": fam, "job_kind": "eval" if fam == S.ZEROSHOT else "train", "spec": spec,
            "registered": "synthetic test", "logical_dependencies": list(deps), "status": "registered_extension"}


def variant(row, deps=None, top=None, **spec):
    """A copy of `row` with spec fields changed (DEL removes one), new logical_dependencies / top-level fields, and a new id."""
    r = json.loads(json.dumps(row))
    for k, v in spec.items():
        if v is DEL:
            r["spec"].pop(k, None)
        else:
            r["spec"][k] = v
    if deps is not None:
        r["logical_dependencies"] = list(deps)
    r.update(top or {})
    body = json.dumps({k: v for k, v in r.items() if k != "experiment_id"}, sort_keys=True)
    r["experiment_id"] = "ALN3X_" + hashlib.sha256(body.encode()).hexdigest()[:16]
    return r


class Plan:
    def __init__(self):
        self.rows, self.n = [], {}

    def add(self, name, fam, ds, spec, deps=(), sf=None, cf=None, seed=3401):
        r = _mk(fam, ds, spec, deps, sf, cf, seed)
        assert r["experiment_id"] not in {x["experiment_id"] for x in self.rows}, name
        self.rows.append(r)
        self.n[name] = r
        return r

    def __getitem__(self, name):
        return self.n[name]

    def id(self, name):
        return self.n[name]["experiment_id"]

    def ids(self, *names):
        return [self.id(x) for x in names]

    def group(self, name, ds, fam=S.DONOR, block="core", obj="NCE", seed=3401, members=None, limit=60, deps=("frozen_manifest",), **kw):
        spec = {"stage": "donor_group", "block": block, "queue_tier": D.BLOCK_TIER[block], "objective": obj,
                "members": list(members or S.GROUP_MEMBERS[fam]), "donor_seed": seed, "sampler_seed": seed, "lambda_rule": S.LAMBDA_RULE,
                "budget": {"epoch_equivalents": 30, "continuation": f"group_wsd_any_last3_ext10_limit{limit}_v1"}, **kw}
        return self.add(name, fam, ds, spec, deps, seed=seed)

    def bridge(self, name, g, member, **kw):
        G = self[g]
        spec = {"stage": "bridge", "block": G["spec"]["block"], "queue_tier": G["spec"]["queue_tier"], "objective": G["spec"]["objective"],
                "donor_seed": G["seed"], "donor_group": G["experiment_id"], "member": member, "bridge": "ridge_u_to_stdenv8_v1", **kw}
        return self.add(name, S.BRIDGE, G["dataset"], spec, [G["experiment_id"]], seed=G["seed"])

    def target(self, name, g, member, sf, cf, ds=None, block=None, obj="NCE", seed=3401, member_key=True, **kw):
        G = self[g] if g else None
        block = block or (G["spec"]["block"] if G else "core")
        spec = {"stage": "target", "block": block, "queue_tier": D.BLOCK_TIER[block], "objective": G["spec"]["objective"] if G else obj,
                "variant": member or "S", "init": "donor" if G else "random", "donor_group": G["experiment_id"] if G else None,
                "donor_seed": G["seed"] if G else None, "target_seed": seed, **kw}
        if member_key:
            spec["member"] = member
        return self.add(name, S.TARGET, G["dataset"] if G else ds, spec, [G["experiment_id"]] if G else [], sf, cf, seed)

    def zeroshot(self, name, g, b, member, sf, cf, mode="A", block=None, deps=None, **kw):
        G = self[g]
        block = block or (G["spec"]["block"] if mode == "A" else "access")
        spec = {"stage": "zero_shot", "block": block, "queue_tier": D.BLOCK_TIER[block], "objective": G["spec"]["objective"],
                "mode": mode, "variant": "zero_shot__no_target_supervised_fit" + D.ZS_SUFFIX[mode], "member": member,
                "donor_seed": G["seed"], "donor_group": G["experiment_id"], "bridge": self.id(b), "job_kind": "eval", **kw}
        return self.add(name, S.ZEROSHOT, G["dataset"], spec, self.ids(g, b) if deps is None else deps, sf, cf, G["seed"])


def build():
    P = Plan()
    P.group("Gf", "fau")
    P.group("Gd", "dtu")
    for m, k in (("AP", "BfAP"), ("XP", "BfXP"), ("J*", "BfJ"), ("XM", "BfXM")):
        P.bridge(k, "Gf", m)
    P.bridge("BdAP", "Gd", "AP")
    P.target("TfS", None, None, 0, 0, ds="fau")
    P.target("TfS1", None, "S", 1, 0, ds="fau")
    for m, k in (("AP", "TfAP"), ("J*", "TfJ"), ("XM", "TfXM")):
        P.target(k, "Gf", m, 0, 0)
    P.target("TdAP", "Gd", "AP", 2, 1)
    P.zeroshot("ZfAP", "Gf", "BfAP", "AP", 0, 0)
    P.zeroshot("ZfJ", "Gf", "BfJ", "J*", 0, 0)
    P.zeroshot("ZfXM", "Gf", "BfXM", "XM", 0, 0)
    P.zeroshot("ZfJ_B", "Gf", "BfJ", "J*", 0, 0, mode="B")  # access block
    P.group("Gp", "private_bdf", block="panel", seed=3407)
    P.bridge("BpJ", "Gp", "J*")
    P.target("TpJ", "Gp", "J*", 0, None, seed=3407)
    P.target("TpS", None, None, 0, None, ds="private_bdf", block="panel", seed=3407)
    P.group("R", "fau", fam=S.RICH_DONOR, block="rich", deps=("frozen_manifest", "rich_cache", P.id("Gf")), horizon_from=P.id("Gf"),
            rich_targets={"ss": "whisper_logmel_pca4_sk_v1", "sc": "flux_pca4_v1"}, loss_weights=[1, 0.5, 0.5])
    P.bridge("BR", "R", "APR")
    P.target("TR", "R", "APR", 0, 0)
    P.zeroshot("ZR", "R", "BR", "APR", 0, 0)
    P.group("X", "dtu", fam=S.CSX_DONOR, block="csx", deps=("frozen_manifest", P.id("Gd")), horizon_from=P.id("Gd"), extra_strata=["fau_cs"])
    P.bridge("BX", "X", "APC")
    P.target("TX", "X", "APC", 2, 1)
    # registered continuation version of Gf (§2.10, make_plan_ext_prior33.py --continuation): new ids, its own limit 90, the
    # pinned label spec.version = "continuation_1" (depth 1) on the group and its rows. On the downstream rows
    # spec.continuation_of / version are version labels (prior33.analysis), never upstreams
    P.group("C", "fau", limit=90, deps=(P.id("Gf"),), continuation_of=P.id("Gf"), version=V1)
    P.bridge("BC", "C", "J*", continuation_of=P.id("BfJ"), version=V1)
    P.target("TC", "C", "J*", 0, 0, continuation_of=P.id("TfJ"), version=V1)
    P.zeroshot("ZC", "C", "BC", "J*", 0, 0, continuation_of=P.id("ZfJ"), version=V1)
    return P


@pytest.fixture
def P():
    return build()


# --------------------------------------------------------------------------------------------------------------- fs helpers
def _touch(p):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").close()


def complete(out, row, **extra):
    p = S.record_path(str(out), row["experiment_id"])
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        json.dump({"experiment_id": row["experiment_id"], "status": "complete", "row": row, **extra}, f)


def group_record(row, **ce):
    """A donor-group record in the pinned layout of select.py: the stored row and members[M]['best']['ce_dev']."""
    rec = {"experiment_id": row["experiment_id"], "status": "complete", "row": row,
           "members": {m: {"steps": 1000, "nonfinite_steps": 0, "best": {"ce_dev": v, "gain": 0.01, "ep_eq": 27}} for m, v in ce.items()}}
    if "J1" in ce and "J025" in ce:
        rec["joint_choice"] = S.joint_choice(rec)
    return rec


def complete_group(out, row, j1=4.0, j025=3.5):
    rec = group_record(row, **{m: (j1 if m == "J1" else j025 if m == "J025" else 4.2) for m in S.group_members(row)})
    p = S.record_path(str(out), row["experiment_id"])
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        json.dump(rec, f)
    return rec


def ckpt(out, gid, *members, kind="best"):
    for m in members:
        _touch(S.member_ckpt(str(out), gid, m, kind))


def fail(out, eid):
    _touch(os.path.join(str(out), "pool", D.QUEUE, f"{eid}.failed"))


def write_ext(out, prior_rows, n_fill=3):
    """plan_ext.jsonl = fillers of other families, the prior rows (one more filler in the middle); returns ALL (plan rows that
    are not in plan_ext, then the extension rows), as make_queue builds it."""
    fill = [_mk("A_LOCAL", "fau", {"architecture": "lag_local_tokens", "k": i}, [], 0, 0, 3401) for i in range(n_fill + 1)]
    mid = len(prior_rows) // 2
    ext = fill[:n_fill] + prior_rows[:mid] + fill[n_fill:] + prior_rows[mid:]
    with open(os.path.join(str(out), "plan_ext.jsonl"), "w") as f:
        f.write("".join(json.dumps(r) + "\n" for r in ext))
    plan = [_mk("A_LOCAL", "dtu", {"k": i}, ["local_base_same_fold"], 0, 0, 3401, prefix="ALN3_") for i in range(5)]
    return plan + ext, ext


def read_lines(p):
    with open(p) as f:
        return f.read().splitlines()


def bash(script, *args):
    return subprocess.run(["bash", "-c", script, "_", *args], capture_output=True, text=True, check=True).stdout.splitlines()


# ------------------------------------------------------------------------------------------ the live readers, taken verbatim
def _live_text(path):
    if not os.path.exists(path):
        pytest.skip(f"{path} is not in this checkout")
    with open(path) as f:
        return f.read()


def live_bash_function(path, name):
    m = re.search(rf"^{name}\(\) \{{.*?^\}}", _live_text(path), re.S | re.M)
    assert m, f"{name}() not found in {path}"
    return m.group(0)


def live_line(path, pattern):
    m = re.search(pattern, _live_text(path))
    assert m, f"{pattern!r} not found in {path}"
    return m.group(0)


def live_offload():
    """ckpt_offload.py's EID regex and queued() source, read from the live file (never imported: it is the running daemon)."""
    src = _live_text(os.path.join(LIVE, "ckpt_offload.py"))
    eid = fn = None
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "EID" for t in node.targets):
            eid = re.compile(ast.literal_eval(node.value.args[0]))
        elif isinstance(node, ast.FunctionDef) and node.name == "queued":
            fn = ast.get_source_segment(src, node)
    assert eid is not None and fn is not None
    return eid, fn


def live_offload_queued(out):
    ns = {"glob": glob, "OUT": str(out)}
    exec(compile(live_offload()[1], "ckpt_offload.queued", "exec"), ns)  # noqa: S102 (read-only function on a temp dir)
    return ns["queued"]()


def live_unclaimed(out, q):
    fn = live_bash_function(os.path.join(LIVE, "watch_anyhost.sh"), "unclaimed")
    return int(bash(f'OUT="$1"\n{fn}\nunclaimed "$2"', str(out), q)[0])


# ----------------------------------------------------------------------------------------------------- families and slots
def test_families_stages_members_and_weights(P):
    assert set(S.FAMILIES) == {r["family_id"] for r in P.rows}
    assert [S.stage_of(P[k]) for k in ("Gf", "R", "X", "BfAP", "TfS", "ZfJ")] == ["donor_group"] * 3 + ["bridge", "target", "zero_shot"]
    with pytest.raises(ValueError):
        S.stage_of(variant(P["BfAP"], stage="target"))
    with pytest.raises(ValueError):
        S.stage_of({"experiment_id": "x", "family_id": "A_LOCAL", "spec": {}})
    assert S.group_members(P["Gf"]) == CORE and S.group_members(P["R"]) == ("APR",) and S.group_members(P["X"]) == ("APC", "XPC")
    assert S.group_members(variant(P["X"], members=DEL)) == ("APC", "XPC")  # family default (§2.6)
    for g, ms in (("Gf", ["AP", "AP"]), ("Gf", ["AP", "J*"]), ("Gf", ["QQ"]), ("Gf", "AP"), ("Gf", ["APR"]),
                  ("R", ["AP", "XP"]), ("X", ["APC", "APR"]), ("X", [["APC"]])):  # members of another family's set (§2.6)
        with pytest.raises(ValueError):
            S.group_members(variant(P[g], members=ms))
    sub = variant(P["X"], members=["APC"])  # a subset trains (group_members), but a plan group trains the whole set
    assert S.group_members(sub) == ("APC",)
    with pytest.raises(ValueError, match="trains"):
        D.check_row(sub, P.rows + [sub])
    # a group registered under another lambda rule is refused, never resolved under this one
    g = variant(P["Gf"], lambda_rule="min_dev_gain_tie0_lambda025")
    b = variant(P["BfJ"], deps=[g["experiment_id"]], donor_group=g["experiment_id"])
    for fn in (lambda: S.group_members(g), lambda: S.group_row(b, P.rows + [g, b]), lambda: D.check_row(g, P.rows + [g]),
               lambda: D.check_row(b, P.rows + [g, b])):
        with pytest.raises(ValueError, match="lambda_rule"):
            fn()
    assert S.group_members(variant(P["Gf"], lambda_rule=DEL)) == CORE  # absent: nothing to compare
    # §4.1 queue weights; integers (bash arithmetic in the pool)
    assert D.WEIGHTS == {S.DONOR: 8, S.CSX_DONOR: 8, S.RICH_DONOR: 8, S.BRIDGE: 6, S.TARGET: 3, S.ZEROSHOT: 2}
    assert all(D.weight_of(r) == D.WEIGHTS[r["family_id"]] for r in P.rows)


def test_slot_of_and_group_row(P):
    assert S.slot_of(P["BfJ"]) == (P.id("Gf"), "J*") and S.slot_of(P["ZR"]) == (P.id("R"), "APR")
    assert S.slot_of(P["TpJ"]) == (P.id("Gp"), "J*") and S.slot_of(P["BX"]) == (P.id("X"), "APC")
    assert S.slot_of(P["TfS"]) is None and S.slot_of(P["TfS1"]) is None and S.slot_of(P["Gf"]) is None
    assert S.slot_of(variant(P["BfJ"], member="Jstar")) == (P.id("Gf"), "J*")
    assert S.slot_of(variant(P["TfAP"], member=DEL)) == (P.id("Gf"), "AP")  # no member key: a variant that is a slot name
    assert S.group_row(P["TfAP"], P.rows) is P["Gf"] and S.group_row(P["Gf"], P.rows) is P["Gf"]
    assert S.group_row(P["TfS"], P.rows) is None
    assert S.group_row(P["ZC"], {r["experiment_id"]: r for r in P.rows}) is P["C"]  # rows may be a mapping
    for b in (variant(P["TfS"], donor_group=P.id("Gf")),  # scratch with a donor
              variant(P["TfAP"], member=None),  # init donor without a member
              variant(P["BfAP"], donor_group=None), variant(P["BfAP"], member="QQ"), variant(P["TfAP"], init="frozen")):
        with pytest.raises(ValueError):
            S.slot_of(b)
    for g, m in (("Gf", "APR"), ("X", "J*"), ("R", "AP")):  # slot not trained by its group
        with pytest.raises(ValueError):
            S.group_row(variant(P["BfAP"], donor_group=P.id(g), member=m), P.rows)
    with pytest.raises(ValueError):
        S.group_row(variant(P["TfAP"], donor_group=P.id("BfAP")), P.rows)  # a bridge is not a donor group


# ------------------------------------------------------------------------------------------------------------- lambda rule
def test_lambda_rule_hand_cases():
    assert S.LAMBDA_RULE == "min_dev_ce_tie1e-4_lambda1" and S.LAMBDA_TIE_BITS == 1e-4
    lc = S.lambda_choice
    assert lc(4.0, 3.9) == "J025" and lc(3.9, 4.0) == "J1" and lc(4.0, 4.0) == "J1"
    assert lc(4.0, 4.0 - 0.99e-4) == "J1" and lc(4.0, 4.0 - 1.01e-4) == "J025"  # |d| < 1e-4 bits is a tie -> J1
    assert lc(4.0 - 1.01e-4, 4.0) == "J1" and lc(4.0 - 0.5e-4, 4.0) == "J1"
    assert lc(math.nan, 4.0) == "J025" and lc(4.0, math.nan) == "J1" and lc(math.nan, math.nan) == "J1"  # non-finite = +inf
    assert lc(math.inf, 3.0) == "J025" and lc(math.inf, math.inf) == "J1" and lc(-math.inf, 3.0) == "J025"


def test_member_of_applies_the_lambda_rule(P):
    gid = P.id("Gf")
    rec = group_record(P["Gf"], AP=5, XP=5, J1=4.0, J025=3.5, XM=6)
    del rec["joint_choice"]
    assert S.member_of(P["BfJ"], rec) == "J025" and S.member_of(P["TfJ"], rec) == "J025" and S.member_of(P["ZfJ"], rec) == "J025"
    rec["members"]["J025"]["best"]["ce_dev"] = 4.0 - 5e-5
    assert S.member_of(P["BfJ"], rec) == "J1"  # tie -> J1
    rec["members"]["J025"]["best"]["ce_dev"] = 4.2
    assert S.member_of(P["BfJ"], rec) == "J1"
    rec["members"]["J025"]["best"]["ce_dev"] = 3
    assert S.member_of(P["BfJ"], rec) == "J025"  # a JSON integer is a number
    assert S.member_of(P["BfAP"], rec) == "AP" and S.member_of(P["BfAP"], None) == "AP" and S.member_of(P["BfXM"], rec) == "XM"
    assert S.member_of(P["TfS"], rec) is None and S.member_of(P["TfS1"], None) is None
    with pytest.raises(ValueError):
        S.member_of(P["Gf"], rec)
    for broken in ({"experiment_id": gid, "members": {"J1": {"best": {"ce_dev": 4.0}}}},  # J025 missing
                   {"experiment_id": gid, "members": {"J1": {"best": {"ce_dev": 4.0}}, "J025": {"best": {"ce_dev": "3.0"}}}},  # a string
                   {"experiment_id": gid, "members": {"J1": {"best": {"ce_dev": True}}, "J025": {"best": {"ce_dev": 3.0}}}},
                   {"experiment_id": gid, "members": {"J1": {"best": {}}, "J025": {"best": {"ce_dev": 3.0}}}},
                   {"experiment_id": gid, "members": {"J1": {"best_ce_dev": 4.0}, "J025": {"best_ce_dev": 3.0}}},  # flat: not pinned
                   {"experiment_id": gid, "members": {"J1": {"best": {"CE_dev": 4.0}}, "J025": {"best": {"CE_dev": 3.0}}}},
                   {"experiment_id": gid, "members": {"J1": {"best": 4.0}, "J025": {"best": 3.0}}},  # best as a scalar
                   {"experiment_id": gid}, None):
        with pytest.raises(S.SelectionError):
            S.member_of(P["BfJ"], broken)
    other = {**rec, "experiment_id": P.id("Gd")}  # the record of another group
    for row in (P["BfJ"], P["BfAP"]):
        with pytest.raises(S.SelectionError):
            S.member_of(row, other)
    short = json.loads(json.dumps(rec))
    short["row"]["spec"]["members"] = ["AP", "XP", "J1", "XM"]  # the recorded group lacks J025
    with pytest.raises(S.SelectionError):
        S.member_of(P["BfJ"], short)
    rule = json.loads(json.dumps(rec))
    rule["row"]["spec"]["lambda_rule"] = "min_dev_gain_tie0_lambda025"  # recorded under another rule: refused for every slot
    for row in (P["BfJ"], P["BfAP"]):
        with pytest.raises(S.SelectionError, match="lambda rule"):
            S.member_of(row, rule)


def test_pinned_group_record_interface(P):
    """A record as run_donor.py (M5) is to write it (select.py, "PINNED donor-group record interface"): member_of and
    check_group_record resolve it after a JSON round trip; the joint choice it records comes from joint_choice()."""
    gid = P.id("Gf")
    rec = group_record(P["Gf"], AP=5.0, XP=4.9, J1=4.0, J025=3.99995, XM=6.0)
    assert rec["joint_choice"] == {"rule": S.LAMBDA_RULE, "member": "J1", "ce_dev": {"J1": 4.0, "J025": 3.99995}, "tie_bits": 1e-4}
    rt = json.loads(json.dumps(rec))
    assert S.check_group_record(rt, P["Gf"]) == "J1" == S.member_of(P["BfJ"], rt) == S.member_of(P["TfJ"], rt)
    rec2 = group_record(P["Gf"], AP=5.0, XP=4.9, J1=math.nan, J025=3.9, XM=math.inf)  # NaN / Infinity survive json (= +inf)
    rt2 = json.loads(json.dumps(rec2))
    assert rt2["joint_choice"]["member"] == "J025" and S.check_group_record(rt2) == "J025" == S.member_of(P["ZfJ"], rt2)
    rr = group_record(P["R"], APR=4.0)
    assert "joint_choice" not in rr and S.check_group_record(rr, P["R"]) is None  # no joint members: no J*
    assert S.check_group_record(group_record(P["X"], APC=4.0, XPC=4.1)) is None
    # a recorded joint choice in the pinned form must agree with the rule; another form is not read
    assert S.member_of(P["BfJ"], {**rt, "joint_choice": {"ce_dev": "J1", "gain": "J025"}}) == "J1"
    bad_jc = {**rt, "joint_choice": {**rt["joint_choice"], "member": "J025"}}
    with pytest.raises(S.SelectionError, match="disagrees"):
        S.member_of(P["BfJ"], bad_jc)
    # records that do not follow the pinned layout are refused by check_group_record (M5's test catches a drift at once)
    drift = json.loads(json.dumps(rt))
    drift["members"] = {m: {"best": {"CE_dev": v["best"]["ce_dev"]}} for m, v in rt["members"].items()}  # the reviewer's layout
    no_xm = json.loads(json.dumps(rt))
    del no_xm["members"]["XM"]["best"]
    no_row = {k: v for k, v in rt.items() if k != "row"}
    bad_rule = json.loads(json.dumps(rt))
    bad_rule["row"]["spec"]["lambda_rule"] = "other"
    for bad, group, what in ((drift, P["Gf"], r"members\['AP'\]\['best'\]\['ce_dev'\]"), (no_xm, None, "XM"),
                             (no_row, None, "group row"), (rt, P["Gd"], "expected the record of"), (bad_rule, None, "lambda_rule"),
                             (bad_jc, None, "disagrees"), ([], None, "mapping")):
        with pytest.raises(S.SelectionError, match=what):
            S.check_group_record(bad, group)
    with pytest.raises(S.SelectionError):
        S.member_of(P["BfJ"], drift)
    assert S.member_of(P["BfAP"], drift) == "AP"  # only J* reads CE_dev


def test_slot_member_reads_the_group_record(tmp_path, P):
    out, gid = str(tmp_path), P.id("Gf")
    assert S.slot_member((gid, "AP"), P.rows, out) == "AP"  # no record needed
    assert S.slot_member((gid, "J*"), P.rows, out) is None  # the group has not finished
    complete_group(out, P["Gf"], j1=4.0, j025=3.0)
    assert S.slot_member((gid, "J*"), P.rows, out) == "J025" and S.slot_member((gid, "Jstar"), P.rows, out) == "J025"
    with pytest.raises(ValueError):
        S.slot_member((P.id("BfAP"), "AP"), P.rows, out)
    with pytest.raises(ValueError):
        S.slot_member((gid, "APR"), P.rows, out)
    with open(S.record_path(out, gid), "w") as f:
        f.write("{not json")
    with pytest.raises(S.SelectionError):
        S.slot_member((gid, "J*"), P.rows, out)
    with open(S.record_path(out, gid), "w") as f:
        json.dump({"experiment_id": gid, "status": "technical_failed"}, f)
    with pytest.raises(S.SelectionError):
        S.load_record(out, gid)
    assert S.load_record(out, P.id("Gd")) is None


def test_compute_limit_and_retained_states(P):
    assert S.compute_limit(P["Gf"]) == 60 and S.compute_limit(P["C"]) == 90 and S.names_limit(P["C"])
    assert S.compute_limit(variant(P["Gf"], budget={"epoch_equivalents": 30})) == S.DEFAULT_LIMIT_EP_EQ == 60
    assert not S.names_limit(variant(P["Gf"], budget=DEL))
    # M8 review: names_limit is a queue-side check and lives in deps.py (not hashed); its regex is select's (compute_limit's parse)
    assert D._LIMIT.pattern == S._LIMIT.pattern and D._LIMIT.flags == S._LIMIT.flags
    for row in (P["Gf"], P["C"], variant(P["Gf"], budget=DEL), variant(P["Gf"], budget={"continuation": "group_wsd_v1"}),
                variant(P["Gf"], budget={"continuation": None}), variant(P["Gf"], budget={"continuation": "x_limit120_y"})):
        assert D.names_limit(row) == S.names_limit(row)
        assert not D.names_limit(row) or S.compute_limit(row) == int(re.search(r"limit(\d+)", row["spec"]["budget"]["continuation"]).group(1))
    with open(D.__file__) as f:
        src = f.read()
    assert "S.names_limit" not in src and "names_limit(row)" in src  # deps no longer calls select.names_limit
    assert S.retained_states("o", P["Gf"]) == [os.path.join("o", "ckpt", f"{P.id('Gf')}_m{m}_stable57.pt") for m in CORE]
    assert S.retained_states("o", P["C"])[0].endswith(f"{P.id('C')}_mAP_stable87.pt")
    assert S.stable_ckpt("o", P.id("Gf"), "XM") == os.path.join("o", "ckpt", f"{P.id('Gf')}_mXM_stable57.pt")


# --------------------------------------------------------------------------------------------------------------- upstreams
def test_upstreams(P):
    up = lambda k: D.upstreams(P[k], P.rows)  # noqa: E731
    assert up("Gf") == [] and up("Gp") == [] and up("TfS") == [] and up("TpS") == []  # symbolic manifest tokens are not rows
    assert up("BfJ") == P.ids("Gf") and up("TfJ") == P.ids("Gf") and up("ZfJ") == P.ids("Gf", "BfJ")
    assert up("R") == P.ids("Gf") and up("X") == P.ids("Gd") and up("C") == P.ids("Gf") and up("ZC") == P.ids("C", "BC")
    assert P["BfJ"]["spec"]["bridge"] == "ridge_u_to_stdenv8_v1"  # a bridge row's spec.bridge is the method, not an upstream
    assert P["BC"]["spec"]["continuation_of"] == P.id("BfJ") and up("BC") == P.ids("C")  # a version label, not an upstream
    z = variant(P["ZfJ"], deps=["frozen_manifest", "rich_cache", "ALN32_PUBLIC_AUDIO_PRIOR"])  # spec-only references still count
    assert D.upstreams(z, P.rows) == P.ids("Gf", "BfJ")
    z = variant(P["ZfJ"], deps=P.ids("BfJ", "Gf", "BfJ"))
    assert D.upstreams(z, P.rows) == P.ids("BfJ", "Gf")  # deduplicated, logical order first
    good, upper = P.id("Gf"), "ALN3X_ABCDEF0123456789"
    bad_deps = ([good, "ALN3X_" + "0" * 16],  # an id that is not a row
                [good, good[:-1]], [good, upper], [good, "aln3x_" + good[6:]], [good, "ALN3X_" + "g" * 16],  # malformed ids:
                [good, "ALN3_" + "0" * 15],  # 15 digits, upper-case hex, lower-case prefix, not hex
                [good, 7], [good, None])  # not strings
    for deps in bad_deps:
        with pytest.raises(ValueError):
            D.upstreams(variant(P["TfAP"], deps=deps), P.rows)
    with pytest.raises(ValueError, match="not a list"):
        D.upstreams(variant(P["TfAP"], top={"logical_dependencies": good}), P.rows)
    for v in ("core_group_fau", upper, good[:-1]):  # spec reference fields hold ids
        with pytest.raises(ValueError, match="not an experiment id"):
            D.upstreams(variant(P["TfAP"], donor_group=v), P.rows)
    me = variant(P["TfAP"])
    me["logical_dependencies"].append(me["experiment_id"])
    with pytest.raises(ValueError, match="itself"):
        D.upstreams(me, P.rows + [me])


# ------------------------------------------------------------------------------------------------------------- plan checks
def test_check_plan_accepts_the_synthetic_plan(P):
    order = D.check_plan(P.rows)
    assert {r["experiment_id"] for r in order} == {r["experiment_id"] for r in P.rows}
    pos = {r["experiment_id"]: i for i, r in enumerate(order)}
    assert all(pos[u] < pos[r["experiment_id"]] for r in P.rows for u in D.upstreams(r, P.rows))  # upstreams first
    for r in P.rows:
        D.check_row(r, P.rows)
    assert D.relation(P["R"], P["Gf"]) == "horizon" and D.relation(P["C"], P["Gf"]) == "continuation"
    assert [D.zero_shot_mode(P[k]) for k in ("ZfJ", "ZfJ_B")] == ["A", "B"]
    for m, k in (("b", "B"), ("C-partial", "C_partial"), ("zero_shot__no_target_supervised_fit__source_statistics_only", "C")):
        assert D.zero_shot_mode(variant(P["ZfJ_B"], mode=m)) == k


def _core_rich_continuation(P):
    """A registered continuation of the rich group R: it resumes from R's stable states and adopts H* of the core continuation C."""
    return variant(P["R"], deps=P.ids("R", "C"), continuation_of=P.id("R"), horizon_from=P.id("C"),
                   budget={"epoch_equivalents": 30, "continuation": "group_wsd_any_last3_ext10_limit90_v1"}, version=V1)


def test_check_row_refuses_plan_inconsistencies(P):
    rows = P.rows
    gf, gd, R, X = P.id("Gf"), P.id("Gd"), P["R"], P["X"]
    g_cs = variant(P["Gf"], objective="CS_SINGLE")  # the CS core group of the same target
    g_3407 = variant(P["Gf"], top={"seed": 3407}, donor_seed=3407, sampler_seed=3407)
    g_d2 = variant(P["Gd"], tag="g_d2")  # another core group with Gd's (dataset, objective, seed)
    # a CSX group with R's (dataset, objective, seed): itself refused since the M8 review item (d) (§2.16: no CSX group for fau),
    # it stays an upstream row below so that "rich horizon from a CSX group" tests the horizon-family rule alone
    x_fau = variant(X, deps=[gf], horizon_from=gf, top={"dataset": "fau"})
    filler = _mk("A_LOCAL", "fau", {"architecture": "lag_local_tokens"}, [], 0, 0, 3401)
    rc = _core_rich_continuation(P)
    zs_c = variant(P["ZfAP"], deps=[gd, P.id("BdAP")], donor_group=gd, bridge=P.id("BdAP"), mode="C", block="access", queue_tier=2,
                   top={"dataset": "dtu"})  # a DTU mode-C zero-shot row (§2.13)
    for ok in (rc, zs_c):  # valid rows: the rich continuation (horizon from the core continuation) and a DTU mode-C row
        D.check_row(ok, rows + [g_d2, ok])
    with pytest.raises(ValueError, match="CSX group for 'fau'"):
        D.check_row(x_fau, rows + [x_fau])
    extra = [g_cs, g_3407, g_d2, x_fau, filler, rc]
    cases = {
        # rich / CSX horizon source (§2.10, §2.15, §2.16): the reviewer's case first (no horizon_from, no core id at all)
        "rich group without any horizon source": variant(R, deps=["frozen_manifest", "rich_cache"], horizon_from=DEL),
        "CSX group without any horizon source": variant(X, deps=["frozen_manifest"], horizon_from=DEL),
        "rich group naming the core group only in logical_dependencies": variant(R, horizon_from=DEL),
        "rich continuation without a horizon source": variant(rc, deps=P.ids("R"), horizon_from=DEL),
        "rich continuation with a second core group": variant(rc, deps=P.ids("R", "C", "Gf")),
        "rich horizon from another dataset": variant(R, deps=[gd], horizon_from=gd),
        "rich horizon from another objective": variant(R, deps=[g_cs["experiment_id"]], horizon_from=g_cs["experiment_id"]),
        "rich horizon from another seed": variant(R, deps=[g_3407["experiment_id"]], horizon_from=g_3407["experiment_id"]),
        "rich horizon from a CSX group": variant(R, deps=[x_fau["experiment_id"]], horizon_from=x_fau["experiment_id"]),
        "rich horizon from a CSX group of another dataset": variant(R, deps=[X["experiment_id"]], horizon_from=X["experiment_id"]),
        "core group with a horizon source": variant(P["Gf"], deps=[gd], horizon_from=gd),
        "same group as horizon and continuation source": variant(R, deps=[gf], continuation_of=gf),
        # continuation versions (§2.10): explicit source, own family, own larger limit
        "continuation without spec.continuation_of": variant(P["C"], continuation_of=DEL),
        "continuation of another family": variant(X, deps=[gd, g_d2["experiment_id"]], continuation_of=g_d2["experiment_id"],
                                                  budget={"continuation": "group_wsd_any_last3_ext10_limit90_v1"}),
        "continuation without its own limit": variant(P["C"], budget={"epoch_equivalents": 30, "continuation": "group_wsd_v1"}),
        "continuation at the source's limit": variant(P["C"], budget={"continuation": "group_wsd_any_last3_ext10_limit60_v1"}),
        "continuation of another objective": variant(P["C"], deps=[g_cs["experiment_id"]], continuation_of=g_cs["experiment_id"]),
        "donor group with a bridge upstream": variant(P["Gf"], deps=P.ids("BdAP")),
        # members and blocks of donor groups (§2.6, §4.1)
        "rich group with core members": variant(R, members=["AP", "XP"]),
        "core group without XM": variant(P["Gf"], members=["AP", "XP", "J1", "J025"]),
        "core group in the rich block": variant(P["Gf"], block="rich", queue_tier=4),
        "rich group in the core block": variant(R, block="core", queue_tier=1),
        "group under another lambda rule": variant(P["Gf"], lambda_rule="other_rule"),
        # zero-shot bridges (§2.11, §4.3)
        "zero-shot with a second bridge": variant(P["ZfJ"], deps=P.ids("Gf", "BfJ", "BfAP")),
        "zero-shot on another slot's bridge": variant(P["ZfJ"], bridge=P.id("BfAP")),
        "zero-shot without spec.bridge": variant(P["ZfJ"], bridge=DEL),
        "zero-shot whose bridge is a target": variant(P["ZfJ"], deps=P.ids("Gf", "TfJ"), bridge=P.id("TfJ")),
        # tiers and blocks (§4.1)
        "queue_tier disagreeing with the block": variant(P["BX"], queue_tier=1),
        "queue_tier that is a bool": variant(P["Gf"], queue_tier=True),
        "unknown block": variant(P["TfAP"], block="extra", queue_tier=DEL),
        "no block": variant(P["TfAP"], block=DEL, queue_tier=DEL),
        "rich-block target bound to a core slot": variant(P["TfAP"], block="rich", queue_tier=4),
        "csx-block zero-shot bound to a core slot": variant(P["ZfAP"], block="csx", queue_tier=4),
        "core-block target bound to the rich slot": variant(P["TR"], block="core", queue_tier=1),
        "access-block bridge": variant(P["BfAP"], block="access", queue_tier=2),
        "panel-group zero-shot": variant(P["ZfJ"], deps=[P.id("Gp"), P.id("BpJ")], donor_group=P.id("Gp"), bridge=P.id("BpJ"),
                                         block="panel", queue_tier=3, donor_seed=3407, top={"dataset": "private_bdf", "seed": 3407}),
        "mode B in the core block": variant(P["ZfJ"], mode="B"),
        "mode A in the access block": variant(P["ZfJ_B"], mode="A"),
        "mode B for dtu": variant(zs_c, mode="B"),
        "zero-shot of another dataset than its group": variant(P["ZfJ_B"], top={"dataset": "dtu"}),
        "unknown zero-shot mode": variant(P["ZfJ"], mode="D"),
        "zero-shot without spec.mode": variant(P["ZfJ"], mode=DEL),
        "from-scratch target in the rich block": variant(P["TfS"], block="rich", queue_tier=4),
        "from-scratch target with an upstream": variant(P["TfS"], deps=[gf]),
        # bindings (§4.3): the row has its group's dataset, objective and donor seed, and reads only its group (and bridge)
        "target with a second donor group": variant(P["TfAP"], deps=[gf, gd]),
        "continuation bridge listing the primary bridge": variant(P["BC"], deps=P.ids("C", "BfJ")),
        "target of another dataset": variant(P["TfAP"], top={"dataset": "dtu"}),
        "target of another objective": variant(P["TfAP"], objective="CS_SINGLE"),
        "target with another donor seed": variant(P["TfAP"], donor_seed=3407),
        "bridge with another seed": variant(P["BfAP"], top={"seed": 3407}),
        "upstream that is not a prior row": variant(P["TfAP"], deps=[gf, filler["experiment_id"]]),
    }
    passed = []
    for label, row in cases.items():
        try:
            D.check_row(row, rows + extra + [row])
        except ValueError:
            continue
        passed.append(label)
    assert passed == []


def test_check_plan_duplicates_and_cycles(tmp_path, P):
    with pytest.raises(ValueError, match="more than once"):
        D.check_plan(P.rows + [json.loads(json.dumps(P["TfS"]))])
    other = {**_mk("A_LOCAL", "fau", {}, [], 0, 0, 3401), "experiment_id": P.id("TfS")}  # a prior id reused by another family
    for rows in (P.rows + [other], [other] + P.rows):
        with pytest.raises(ValueError, match="more than once"):
            D.check_plan(rows)
    a = P.group("A", "dtu", obj="CS_SINGLE", deps=(), limit=90)
    b = P.group("B", "dtu", obj="CS_SINGLE", limit=120, deps=(a["experiment_id"],), continuation_of=a["experiment_id"])
    a["spec"]["continuation_of"] = b["experiment_id"]  # A <-> B: a continuation cycle (the limit rule already refuses it)
    with pytest.raises(ValueError):
        D.check_plan(P.rows)
    with pytest.raises(ValueError, match="cycle"):
        D._topo(D._Ctx(P.rows, str(tmp_path)), [a, b])


# --------------------------------------------------------------------------------------------- M8 review: plan-check fixes
def _refused(rows, cases):
    """Labels of the cases that check_row accepts (the expectation is an empty list)."""
    passed = []
    for label, row in cases.items():
        try:
            D.check_row(row, rows + [row])
        except ValueError:
            continue
        passed.append(label)
    return passed


def test_one_shot_iterables_are_read_once(tmp_path, P):
    """M8 review: check_plan and write_queue built the index from `rows` and then iterated it again, so a generator (or
    itertools.chain(plan, new), as M9 calls it) validated nothing and wrote an empty queue with .remaining 0, which would stop
    the keeper. Every function now materialises a one-shot iterable once; held, bound and ext too."""
    bad = variant(P["R"], deps=["frozen_manifest", "rich_cache"], horizon_from=DEL)
    with pytest.raises(ValueError, match="horizon_from"):
        D.check_plan(itertools.chain(P.rows, [bad]))  # the reviewer's reproduction: [] before
    ref = [r["experiment_id"] for r in D.check_plan(P.rows)]
    for rows in (iter(P.rows), (r for r in P.rows), itertools.chain(P.rows[:5], P.rows[5:]), D.index(P.rows)):
        assert [r["experiment_id"] for r in D.check_plan(rows)] == ref
    for bad_rows in (None, "ALN3X_0123456789abcdef", b"x"):
        with pytest.raises(TypeError):
            D.check_plan(bad_rows)
    out = {k: str(tmp_path / k) for k in ("list", "gen")}
    for d in out.values():
        os.makedirs(d)
    ALL, ext = write_ext(out["list"], P.rows)
    write_ext(out["gen"], P.rows)
    held = [P.id("TfXM"), S.CSX_DONOR]
    sa = D.write_queue(out["list"], ALL, held=held, bound=set(S.FAMILIES), ext=ext)
    sb = D.write_queue(out["gen"], (r for r in ALL), held=(h for h in held), bound=(f for f in S.FAMILIES), ext=(r for r in ext))
    assert sa == sb and sa["queued"] == len(P.rows) - 4 and sa["remaining"] == sa["queued"]  # X, BX, TX and TfXM held
    files = lambda d: {os.path.basename(p): open(p).read() for p in glob.glob(os.path.join(d, "queue_v3_prior*"))}  # noqa: E731
    assert files(out["gen"]) == files(out["list"]) and len(files(out["list"])) == 5
    row = P["ZC"]  # the single-row functions read a generator once as well
    assert D.upstreams(row, (r for r in P.rows)) == P.ids("C", "BC") and D.ckpt_deps(row, (r for r in P.rows)) == [P.id("C")]
    D.check_row(row, (r for r in P.rows))
    assert D.ready(P["TfS"], (r for r in P.rows), out["list"]) and not D.blocked(row, (r for r in P.rows), out["list"])


def test_horizon_source_is_the_same_execution_version(P):
    """M8 review: _check_donor checked only that spec.horizon_from is a DONOR group of the same (dataset, objective, seed), so a
    group could adopt the H* of a core group of another execution version (§2.10, §2.15, §2.16: APR-AP / APC-AP at equal updates;
    nothing detects it at run time, the stream hashes still match). The horizon group must now have the row's compute limit and
    continuation depth, and a continuation must adopt the continuation of its source's horizon group."""
    R, X, gf = P["R"], P["X"], P.id("Gf")
    rc = _core_rich_continuation(P)  # valid: R's states, H* of the core continuation C
    lim90 = {"epoch_equivalents": 30, "continuation": "group_wsd_any_last3_ext10_limit90_v1"}
    cd = variant(P["Gd"], deps=P.ids("Gd"), continuation_of=P.id("Gd"), budget=lim90, version=V1)  # a DTU core continuation
    xc = variant(X, deps=[X["experiment_id"], cd["experiment_id"]], continuation_of=X["experiment_id"], horizon_from=cd["experiment_id"],
                 budget=lim90, version=V1)  # valid: the CSX continuation adopting H* of the DTU core continuation
    gf2 = variant(P["Gf"], tag="second core group")  # another primary core group with Gf's (dataset, objective, seed)
    cf2 = variant(P["C"], deps=[gf2["experiment_id"]], continuation_of=gf2["experiment_id"])  # its continuation (limit 90)
    rows = P.rows + [rc, cd, xc, gf2, cf2]
    for ok in (rc, xc, R, X):
        D.check_row(ok, rows)
    assert len(D.check_plan(rows)) == len(rows)
    cases = {
        "primary rich group adopting the core continuation's H* (case 1)": variant(R, deps=P.ids("C"), horizon_from=P.id("C")),
        "rich continuation adopting the primary core group's H* (case 2: R's fields copied)": variant(rc, deps=[P.id("R"), gf],
                                                                                                       horizon_from=gf),
        "primary CSX group adopting a DTU core continuation's H* (case 3)": variant(X, deps=[cd["experiment_id"]],
                                                                                    horizon_from=cd["experiment_id"]),
        "CSX continuation adopting the primary core group's H*": variant(xc, deps=[X["experiment_id"], P.id("Gd")],
                                                                         horizon_from=P.id("Gd")),
        "primary rich group at limit 90 adopting the core continuation's H*": variant(R, deps=P.ids("C"), horizon_from=P.id("C"),
                                                                                      budget=lim90),
        "rich continuation adopting the continuation of another core group": variant(rc, deps=[P.id("R"), cf2["experiment_id"]],
                                                                                     horizon_from=cf2["experiment_id"]),
    }
    assert _refused(rows, cases) == []
    msgs = {}
    for label, row in cases.items():
        with pytest.raises(ValueError) as e:
            D.check_row(row, rows + [row])
        msgs[label] = str(e.value)
    assert all("execution version" in m or "continues" in m for m in msgs.values()), msgs


def test_version_labels_are_tied_to_the_group(P):
    """M8 review: spec.version and spec.continuation_of on bridge, target and zero-shot rows were labels that nothing compared
    with the group, so an unlabelled continuation row became 'primary' and collided with the primary row of its cell, and a
    mislabelled one formed a phantom version (prior33.analysis). spec.version is now the one pinned label: 'continuation_<depth>'
    on a continuation group and each of its slot rows, absent on primary rows (S rows included); spec.execution_version is
    refused; a slot row's continuation_of label is refused on primary rows and must name the row continued."""
    rc = _core_rich_continuation(P)
    brc = variant(P["BR"], deps=[rc["experiment_id"]], donor_group=rc["experiment_id"], continuation_of=P.id("BR"), version=V1)
    c2 = variant(P["C"], deps=P.ids("C"), continuation_of=P.id("C"),
                 budget={"epoch_equivalents": 30, "continuation": "group_wsd_any_last3_ext10_limit120_v1"}, version=V2)
    tc2 = variant(P["TC"], deps=[c2["experiment_id"]], donor_group=c2["experiment_id"], continuation_of=P.id("TC"), version=V2)
    tfj_sf1 = variant(P["TfJ"], top={"subject_fold": 1})  # a primary J* target of another cell
    rows = P.rows + [rc, brc, c2, tc2, tfj_sf1]
    for ok in (P["C"], P["BC"], P["TC"], P["ZC"], rc, brc, c2, tc2, variant(P["TC"], continuation_of=DEL), P["Gf"], P["TfS"]):
        D.check_row(ok, rows + [ok])
    assert len(D.check_plan(rows)) == len(rows)
    assert D.version_label(0) is None and D.version_label(1) == V1 and D.version_label(2) == V2
    cases = {
        # groups
        "continuation group without its label": variant(P["C"], version=DEL),
        "continuation group with the old integer label": variant(P["C"], version=2),
        "continuation group labelled with another depth": variant(P["C"], version=V2),
        "second continuation labelled as the first": variant(c2, version=V1),
        "primary group with a label": variant(P["Gf"], version=V1),
        "rich continuation without its label": variant(rc, version=DEL),
        "group with spec.execution_version": variant(P["C"], execution_version=V1),
        # slot rows of a continuation group (the reviewer's cases)
        "bridge of C with neither label": variant(P["BC"], version=DEL, continuation_of=DEL),
        "target of C with neither label": variant(P["TC"], version=DEL, continuation_of=DEL),
        "target of C labelled version 7": variant(P["TC"], version=7),
        "target of C labelled another continuation": variant(P["TC"], version=V2),
        "zero-shot of C without the label": variant(P["ZC"], version=DEL),
        "target of C2 labelled as C's": variant(tc2, version=V1),
        "rich continuation bridge without the label": variant(brc, version=DEL),
        "slot row with spec.execution_version": variant(P["TC"], execution_version=V1),
        # slot rows of a primary group
        "primary target labelled with continuation_of": variant(P["TfJ"], version=V1, continuation_of=P.id("TfAP")),
        "primary target labelled version only": variant(P["TfJ"], version=V1),
        "primary target with continuation_of only": variant(P["TfJ"], continuation_of=P.id("TfAP")),
        "primary bridge labelled": variant(P["BfAP"], version=V1),
        "from-scratch target labelled": variant(P["TfS"], version=V1),
        "from-scratch target with continuation_of": variant(P["TfS"], continuation_of=P.id("TfS1")),
        # continuation_of labels that do not name the row continued
        "continuation target naming another slot's row": variant(P["TC"], continuation_of=P.id("TfAP")),
        "continuation target naming a row of another cell": variant(P["TC"], continuation_of=tfj_sf1["experiment_id"]),
        "continuation target naming a bridge": variant(P["TC"], continuation_of=P.id("BfJ")),
        "continuation target naming itself as a continuation row": variant(P["TC"], continuation_of=P.id("TC")),
        "continuation zero-shot naming another mode's row": variant(P["ZC"], continuation_of=P.id("ZfJ_B")),
        "continuation target naming no row": variant(P["TC"], continuation_of="ALN3X_" + "0" * 16),
        "second continuation's target naming the primary row": variant(tc2, continuation_of=P.id("TfJ")),
    }
    assert _refused(rows, cases) == []
    # the pinned labels are the execution versions prior33.analysis derives (no notes on the valid plan)
    from auditory_alignment_v3.prior33 import analysis as A
    vers = A.execution_versions(rows)
    by = D.index(rows)
    for r in rows:
        g = S.group_row(r, by)
        want = A._version_label(D._depth(by, g)) if g is not None else "primary"
        assert vers[r["experiment_id"]]["version"] == want and (r["spec"].get("version") or "primary") == want
        assert not vers[r["experiment_id"]]["notes"], (r["experiment_id"], vers[r["experiment_id"]]["notes"])


def test_access_xm_and_concrete_lambda_members_are_refused(P):
    """M8 review (a), (b): §4.1 access covers the slots AP, XP and J* only (no XM zero-shot row in modes B, C, C_partial); and a
    bridge, target or zero-shot row on the concrete lambda candidates J1 / J025 (select accepts them as slot names) would bypass
    the lambda rule, so they are refused (rows name J*)."""
    ids = P.ids
    for m, b in (("AP", "BfAP"), ("XP", "BfXP"), ("J*", "BfJ")):  # access rows of the three access slots are valid
        ok = variant(P["ZfJ_B"], deps=ids("Gf", b), member=m, bridge=P.id(b))
        D.check_row(ok, P.rows + [ok])
    b1, b025 = variant(P["BfJ"], member="J1"), variant(P["BfJ"], member="J025")
    cases = {
        "access-block XM zero-shot (mode B)": variant(P["ZfJ_B"], deps=ids("Gf", "BfXM"), member="XM", bridge=P.id("BfXM")),
        "access-block XM zero-shot (mode C, dtu)": variant(P["ZfJ_B"], deps=[P.id("Gd"), P.id("BdAP")], donor_group=P.id("Gd"),
                                                           bridge=P.id("BdAP"), member="XM", mode="C", top={"dataset": "dtu"}),
        "J1 bridge": b1, "J025 bridge": b025,
        "J1 target": variant(P["TfJ"], member="J1"), "J025 target by variant": variant(P["TfJ"], member=DEL, variant="J025"),
        "J1 zero-shot on a J1 bridge": variant(P["ZfJ"], deps=[P.id("Gf"), b1["experiment_id"]], member="J1", bridge=b1["experiment_id"]),
        "J025 zero-shot on the J* bridge": variant(P["ZfJ"], member="J025"),
        "J1 continuation target": variant(P["TC"], member="J1"),
    }
    assert _refused(P.rows + [b1, b025], cases) == []
    with pytest.raises(ValueError, match="lambda candidate"):
        D.check_plan(P.rows + [b1])
    with pytest.raises(ValueError, match="access-block"):
        D.check_row(cases["access-block XM zero-shot (mode B)"], P.rows + [cases["access-block XM zero-shot (mode B)"]])
    assert S.slot_of(b1) == (P.id("Gf"), "J1")  # select still names it; deps refuses it as a plan row


def test_m8_low_items_c_to_i_are_refused(tmp_path, P):
    """M8 review low items (c)-(i) (prior33_open_M8_M10.md), each accepted by check_row / check_plan before: (c) a second bridge
    row of a slot (a plan-level property: check_plan and write_queue); (d) a CSX group for fau (§2.16); (e) panel rows for another
    cohort than private_bdf (§4.1); (f) seed fields that disagree with the row seed or with each other (§4.3); (g) a continuation
    in another block than its source; (h) a spec.variant naming another slot than spec.member (select reads the member); (i) an
    empty spec.members that select reads as the family default. make_plan_ext_prior33.py refuses the same at registration; deps
    now refuses them for rows written by any other path."""
    gf, gp = P.id("Gf"), P.id("Gp")
    lim90 = {"epoch_equivalents": 30, "continuation": "group_wsd_any_last3_ext10_limit90_v1"}
    gpc = variant(P["Gp"], block="core", queue_tier=1, top={"seed": 3401, "seed_scope": "breadth"}, donor_seed=3401, sampler_seed=3401)
    valid = [gpc,  # a core private_bdf group (seed 3401)
             variant(P["Gp"], deps=[gp], continuation_of=gp, budget=lim90, version=V1),  # a panel continuation, in block panel
             variant(P["TfAP"], member=DEL),  # the variant alone names the slot
             variant(P["TfAP"], variant="cross_person_pretrain"),  # a descriptive variant is not compared
             variant(P["TfAP"], sampler_seed=3401),  # sampler_seed = donor_seed = the group's seed
             variant(P["TfS"], target_seed=DEL), variant(P["Gf"], donor_seed=DEL, sampler_seed=DEL)]  # absent fields: not compared
    rows = P.rows + valid
    for ok in valid:
        D.check_row(ok, rows)
    assert len(D.check_plan(rows)) == len(rows)
    for ok in (variant(P["BfAP"], sampler_seed=3401, target_seed=None), variant(P["ZfAP"], target_seed=None)):  # null = absent
        D.check_row(ok, P.rows + [ok])
    cases = {
        # (d) CSX groups exist for dtu, federici and private_bdf only; every row's dataset is a target cohort
        "CSX group for fau": (variant(P["X"], deps=[gf], horizon_from=gf, top={"dataset": "fau"}), "CSX group for 'fau'"),
        "row of a non-target cohort": (variant(P["TfS"], top={"dataset": "sparrkulee"}), "not a target cohort"),
        # (e) the panel block is private_bdf only
        "panel donor group for fau": (variant(P["Gp"], top={"dataset": "fau"}), "panel-block row"),
        "panel from-scratch target for fau": (variant(P["TpS"], top={"dataset": "fau"}), "panel-block row"),
        # (f) seeds (§4.3)
        "group with donor and sampler seed 3407, row seed 3401": (variant(P["Gf"], donor_seed=3407, sampler_seed=3407),
                                                                  "spec.donor_seed 3407 differs from the row seed 3401"),
        "group with sampler_seed != donor_seed": (variant(P["Gf"], sampler_seed=3407), "sampler_seed = donor_seed"),
        "group with a target_seed": (variant(P["Gf"], target_seed=3401), "null where not applicable"),
        "target with target_seed != row seed": (variant(P["TfAP"], target_seed=3407), "differs from the row seed"),
        "from-scratch target with target_seed != row seed": (variant(P["TfS"], target_seed=3407), "differs from the row seed"),
        "panel target with target_seed != row seed": (variant(P["TpJ"], target_seed=3413), "differs from the row seed"),
        "bridge with sampler_seed != the group's seed": (variant(P["BfAP"], sampler_seed=3407), "sampler_seed = donor_seed"),
        "bridge with a target_seed": (variant(P["BfAP"], target_seed=3401), "null where not applicable"),
        "zero-shot with a target_seed": (variant(P["ZfAP"], target_seed=3401), "null where not applicable"),
        "target with sampler_seed but no donor_seed": (variant(P["TfAP"], donor_seed=DEL, sampler_seed=3401), "sampler_seed = donor_seed"),
        # (g) a continuation is registered in its source's block
        "core continuation in block panel": (variant(gpc, deps=[gpc["experiment_id"]], continuation_of=gpc["experiment_id"], budget=lim90,
                                                     version=V1, block="panel", queue_tier=3), "its source's block"),
        "panel continuation in block core": (variant(P["Gp"], deps=[gp], continuation_of=gp, budget=lim90, version=V1, block="core",
                                                     queue_tier=1), "its source's block"),
        # (h) variant and member must name one slot
        "target with member AP and variant XP": (variant(P["TfAP"], variant="XP"), "variant and member must agree"),
        "target with member J* and variant J1": (variant(P["TfJ"], variant="J1"), "variant and member must agree"),
        "zero-shot with member AP and variant XM": (variant(P["ZfAP"], variant="XM"), "variant and member must agree"),
        "from-scratch target with variant XP": (variant(P["TfS1"], variant="XP"), "variant and member must agree"),
        # (i) an empty members list is not the family default
        "core group with members []": (variant(P["Gf"], members=[]), "spec.members is empty"),
        "rich group with members []": (variant(P["R"], members=[]), "spec.members is empty"),
    }
    assert _refused(rows, {k: v[0] for k, v in cases.items()}) == []
    for label, (row, needle) in cases.items():  # each is refused by the intended rule, not by another one
        with pytest.raises(ValueError) as e:
            D.check_row(row, rows + [row])
        assert needle in str(e.value), (label, str(e.value))
    # (c) one bridge per slot: a plan-level property (check_plan and write_queue; check_row sees one row and its upstreams)
    dup, alias = variant(P["BfAP"], fit_rows="other"), variant(P["BfJ"], member="Jstar")  # (Gf, AP) again; (Gf, J*) by an alias
    for extra in ([dup], [alias], [dup, alias]):
        with pytest.raises(ValueError, match="bridge rows"):
            D.check_plan(P.rows + extra)
        with pytest.raises(ValueError, match="bridge rows"):
            D.check_plan(iter(P.rows + extra))
    out = str(tmp_path)
    ALL, ext = write_ext(out, P.rows + [dup])
    with pytest.raises(ValueError, match="one bridge per slot"):
        D.write_queue(out, ALL, ext=ext)
    assert not glob.glob(os.path.join(out, "queue_v3_prior*"))  # nothing written for an inconsistent plan


# ---------------------------------------------------------------------------------------------------------------- readiness
def test_ready_chain_donor_bridge_target_zeroshot(tmp_path, P):
    out, rows, gf = str(tmp_path), P.rows, P.id("Gf")
    rd = lambda k: D.ready(P[k], rows, out)  # noqa: E731
    assert rd("TfS") and rd("TfS1") and rd("Gf") and rd("Gd") and rd("Gp")
    assert not any(rd(k) for k in ("BfAP", "TfAP", "BfJ", "ZfJ", "R", "X", "C", "BC"))
    complete_group(out, P["Gf"], j1=4.0, j025=3.5)  # record without checkpoints
    assert not rd("BfAP") and not rd("TfAP") and not rd("R")
    ckpt(out, gf, "AP")
    assert rd("BfAP") and rd("TfAP") and rd("R")  # rich: core record (H*) + core AP checkpoint
    assert not rd("ZfAP")  # needs its bridge
    ckpt(out, gf, "J1")
    assert not rd("BfJ") and not rd("TfJ")  # the lambda rule chose J025 (3.5 < 4.0)
    ckpt(out, gf, "J025")
    assert rd("BfJ") and rd("TfJ")
    complete(out, P["BfJ"])
    assert not rd("ZfJ") and not rd("ZfJ_B")  # bridge record without its npz
    _touch(S.bridge_npz(out, P.id("BfJ")))
    assert rd("ZfJ") and rd("ZfJ_B")
    complete_group(out, P["Gd"], j1=1, j025=1)
    assert rd("X")  # CSX: the core record only
    assert not rd("BdAP")
    ckpt(out, P.id("Gd"), "XP", "J1", kind="best")
    ckpt(out, P.id("Gd"), "AP", kind="gainsel")  # a sensitivity checkpoint is not the one a bridge loads
    assert not rd("BdAP")
    ckpt(out, P.id("Gd"), "AP")
    assert rd("BdAP") and rd("TdAP")


def test_ready_tie_loads_j1_and_unresolvable_record(tmp_path, P):
    out, gf = str(tmp_path), P.id("Gf")
    complete_group(out, P["Gf"], j1=4.0, j025=4.0 - 5e-5)  # tie -> J1
    ckpt(out, gf, "J025")
    assert not D.ready(P["BfJ"], P.rows, out)
    ckpt(out, gf, "J1")
    assert D.ready(P["BfJ"], P.rows, out)
    complete(out, P["Gp"], members={"AP": {"best": {"ce_dev": 1.0}}})  # a record without the joint CE values
    ckpt(out, P.id("Gp"), *CORE)
    with pytest.raises(S.SelectionError):
        D.ready(P["BpJ"], P.rows, out)
    assert D.ready(P["TpS"], P.rows, out)


def test_continuation_versions(tmp_path, P):
    out, gf, c = str(tmp_path), P.id("Gf"), P.id("C")
    complete_group(out, P["Gf"], j1=4.0, j025=3.0)
    ckpt(out, gf, *CORE)
    assert not D.ready(P["C"], P.rows, out)  # resumes from the stable states, not from the best checkpoints
    for m in CORE[:-1]:
        _touch(S.stable_ckpt(out, gf, m, 57))
    _touch(S.stable_ckpt(out, gf, "XM", 87))  # wrong ep-eq for a limit-60 source
    assert not D.ready(P["C"], P.rows, out)
    _touch(S.stable_ckpt(out, gf, "XM", 57))
    assert D.ready(P["C"], P.rows, out)
    # the continuation's J* comes from its own record (J1 here), not from the source's (J025)
    complete_group(out, P["C"], j1=3.0, j025=3.2)
    ckpt(out, c, "J025")
    assert not D.ready(P["BC"], P.rows, out) and not D.ready(P["TC"], P.rows, out)
    ckpt(out, c, "J1")
    assert D.ready(P["BC"], P.rows, out) and D.ready(P["TC"], P.rows, out)
    assert D.ckpt_deps(P["C"], P.rows) == [gf] and D.ckpt_deps(P["BC"], P.rows) == [c] and D.ckpt_deps(P["ZC"], P.rows) == [c]
    # a continuation of the limit-90 continuation (limit 120) resumes from stable87
    P.group("C2", "fau", limit=120, deps=(c,), continuation_of=c, version=V2)
    D.check_row(P["C2"], P.rows)
    assert D.relation(P["C2"], P["C"]) == "continuation" and D.ckpt_deps(P["C2"], P.rows) == [c]
    for m in CORE:
        _touch(S.stable_ckpt(out, c, m, 57))
    assert not D.ready(P["C2"], P.rows, out)
    for m in CORE:
        _touch(S.stable_ckpt(out, c, m, 87))
    assert D.ready(P["C2"], P.rows, out)
    # a rich continuation: R's stable states + H* of the core continuation C and C's AP checkpoint
    rc = _core_rich_continuation(P)
    rows = P.rows + [rc]
    complete(out, P["R"], members={"APR": {"best": {"ce_dev": 4.0}}})
    _touch(S.stable_ckpt(out, P.id("R"), "APR", 57))
    assert not D.ready(rc, rows, out)  # C's AP checkpoint is missing
    ckpt(out, c, "AP")
    assert D.ready(rc, rows, out) and D.ckpt_deps(rc, rows) == P.ids("R", "C")
    assert D.blocked(P["ZC"], P.rows, out) is False
    fail(out, c)  # C is complete: a stale marker does not block
    assert not D.blocked(P["ZC"], P.rows, out)


# ----------------------------------------------------------------------------------------------------------------- blocking
def test_blocked_propagates_transitively_from_failed_markers(tmp_path, P):
    out, rows = str(tmp_path), P.rows
    bl = lambda k: D.blocked(P[k], rows, out)  # noqa: E731
    assert not any(bl(k) for k in P.n)
    fail(out, P.id("BfJ"))
    assert bl("ZfJ") and bl("ZfJ_B")
    assert not bl("BfJ") and not bl("ZfAP") and not bl("TfJ") and not bl("Gf")  # a failed row is failed, not blocked
    fail(out, P.id("Gf"))
    down = ("BfAP", "BfXP", "BfJ", "BfXM", "TfAP", "TfJ", "TfXM", "ZfAP", "ZfJ", "ZfXM", "ZfJ_B", "R", "BR", "TR", "ZR", "C", "BC", "TC", "ZC")
    assert all(bl(k) for k in down)  # BR / TR / ZR and the continuation chain are blocked through R and C
    assert not any(bl(k) for k in ("TfS", "TfS1", "Gd", "BdAP", "TdAP", "X", "BX", "TX", "Gp", "BpJ", "TpJ", "TpS"))
    complete(out, P["R"])  # blocking passes only through rows that are not done
    assert not bl("BR") and not bl("TR") and not bl("ZR") and bl("C") and bl("ZC")
    complete_group(out, P["Gf"])  # a complete record wins over a stale marker
    assert not bl("BfAP") and not bl("C") and bl("ZfJ")  # ZfJ is still blocked by its failed bridge


# ---------------------------------------------------------------------------------------------------------- checkpoint owners
def test_ckpt_deps_and_the_live_offload_regex(P):
    cd = lambda k: D.ckpt_deps(P[k], P.rows)  # noqa: E731
    gf = P.id("Gf")
    assert cd("BfAP") == [gf] and cd("BfJ") == [gf] and cd("TfJ") == [gf] and cd("ZfJ") == [gf] and cd("ZfJ_B") == [gf]
    assert cd("TfS") == [] and cd("TpS") == [] and cd("Gf") == [] and cd("Gp") == [] and cd("X") == []
    assert cd("R") == [gf] and cd("BR") == [P.id("R")] and cd("ZR") == [P.id("R")] and cd("BX") == [P.id("X")] and cd("TX") == [P.id("X")]
    assert cd("TpJ") == [P.id("Gp")] and cd("C") == [gf]
    assert D.ckpt_deps(P["ZC"], D.index(P.rows)) == [P.id("C")]  # a prebuilt mapping (ckpt_offload.deps_of's `by`)
    eid, _ = live_offload()  # ckpt_offload.py's own EID regex
    for m in S.MEMBER_TAGS:  # every member checkpoint name maps to its group id
        for kind in S.CKPT_SUFFIX:
            assert eid.match(os.path.basename(S.member_ckpt("o", gf, m, kind))).group(1) == gf
    for p in S.retained_states("o", P["Gf"]) + S.retained_states("o", P["C"]) + [S.bridge_npz("o", P.id("BfJ"))]:
        assert not eid.match(os.path.basename(p))  # stable states and bridge npz files are never offloaded
    with pytest.raises(ValueError):
        S.member_ckpt("o", gf, "J*")


# -------------------------------------------------------------------------------------------------------------------- order
def test_order_key(P):
    order = sorted(P.rows, key=D.order_key)
    keys = [(D.tier_of(r), D.STAGE_RANK[S.stage_of(r)]) for r in order]
    assert keys == sorted(keys)  # tier, then donor < bridge < target < zero-shot
    tier1_donors = [r for r, k in zip(order, keys) if k == (1, 0)]
    assert [r["dataset"] for r in tier1_donors] == ["dtu", "fau", "fau"] and order[:3] == tier1_donors
    t1_targets = [r for r in order if D.tier_of(r) == 1 and S.stage_of(r) == "target"]
    assert [(r["dataset"], r["subject_fold"]) for r in t1_targets] == sorted((r["dataset"], r["subject_fold"]) for r in t1_targets)
    assert order[-1]["family_id"] in (S.ZEROSHOT, S.TARGET) and D.tier_of(order[-1]) == 4
    assert order.index(P["ZfJ_B"]) > max(order.index(P[k]) for k in ("ZfJ", "ZC", "TfS1"))  # access (tier 2) after tier 1
    assert order.index(P["Gp"]) > order.index(P["ZfJ_B"]) and order.index(P["R"]) > order.index(P["TpS"])
    assert D.tier_of(variant(P["BX"], queue_tier=DEL)) == 4  # the tier of the block
    for bad in (variant(P["BX"], queue_tier=1), variant(P["BX"], block=DEL), variant(P["BX"], block="csx2", queue_tier=DEL)):
        with pytest.raises(ValueError):
            D.order_key(bad)
    assert sorted(P.rows, key=D.order_key) == order  # deterministic


# --------------------------------------------------------------------------------------------------------------- queue files
def _expected_states(rows, out, ids):
    st = {}
    by = D.index(rows)
    for e in ids:
        if os.path.exists(S.record_path(out, e)):
            st[e] = "done"
        elif os.path.exists(os.path.join(out, "pool", D.QUEUE, f"{e}.failed")):
            st[e] = "failed"
        elif D.blocked(by[e], rows, out):
            st[e] = "blocked"
        else:
            st[e] = "ready" if D.ready(by[e], rows, out) else "waiting"
    return st


def test_write_queue_lines_weights_and_counters(tmp_path, P):
    out = str(tmp_path)
    ALL, ext = write_ext(out, P.rows)
    gf = P.id("Gf")
    complete_group(out, P["Gf"], j1=4.0, j025=3.5)
    ckpt(out, gf, *CORE)
    complete(out, P["BfJ"])
    _touch(S.bridge_npz(out, P.id("BfJ")))
    fail(out, P.id("BfAP"))  # -> ZfAP blocked
    complete_group(out, P["Gd"])  # held but done: its downstream stays in scope
    held = {S.CSX_DONOR, P.id("TfXM"), P.id("Gd")}
    summ = D.write_queue(out, ALL, held=held)
    lines = read_lines(os.path.join(out, "queue_v3_prior.txt"))
    pos = {r["experiment_id"]: D.EXT_OFFSET + j for j, r in enumerate(ext)}
    by = D.index(ALL)
    got = [ln.split("|") for ln in lines]
    assert all(len(f) == 3 for f in got)  # three fields, also without upstreams (empty third field)
    ids = [f[0] for f in got]
    absent = set(P.ids("X", "BX", "TX", "TfXM", "Gd"))  # X by family, BX / TX transitively (X not done), TfXM / Gd by id
    blocked = set(P.ids("ZfAP"))  # in scope, counted, not listed
    assert set(ids) == {r["experiment_id"] for r in P.rows} - absent - blocked
    assert summ["held"] == len(absent) and summ["queued"] == len(ids) and summ["in_scope"] == len(ids) + len(blocked)
    assert all(int(i) == pos[e] and ups == ",".join(D.upstreams(by[e], ALL)) for e, i, ups in got)
    assert ids == [r["experiment_id"] for r in sorted((by[e] for e in ids), key=D.order_key)]
    assert P.id("BdAP") in ids and P.id("TdAP") in ids
    assert read_lines(os.path.join(out, "queue_v3_prior_weights.txt")) == [f"{e} {D.WEIGHTS[by[e]['family_id']]}" for e in ids]
    st = _expected_states(ALL, out, ids + sorted(blocked))
    cnt = {k: sum(v == k for v in st.values()) for k in ("done", "failed", "blocked", "ready", "waiting")}
    assert {k: summ[k] for k in cnt} == cnt and sum(cnt.values()) == summ["in_scope"]
    assert cnt["done"] == 2 and cnt["failed"] == 1 and cnt["blocked"] == 1 and st[P.id("ZfJ")] == "ready"
    assert st[P.id("C")] == "waiting" and st[P.id("TfS")] == "ready" and st[P.id("R")] == "ready"
    rem = int(read_lines(os.path.join(out, "queue_v3_prior.remaining"))[0])
    wai = int(read_lines(os.path.join(out, "queue_v3_prior.waiting"))[0])
    assert rem == cnt["ready"] + cnt["waiting"] == summ["remaining"] and wai == cnt["waiting"]
    assert read_lines(os.path.join(out, "queue_v3_prior.blocked")) == P.ids("ZfAP")
    # counters never end in .txt: the offload daemon's own queued() sees exactly the listed eids (field 1 of the queue file)
    assert sorted(os.path.basename(p) for p in glob.glob(os.path.join(out, "queue_v3_*.txt"))) == ["queue_v3_prior.txt",
                                                                                                    "queue_v3_prior_weights.txt"]
    assert all(not (D.QUEUE + c).endswith(".txt") and os.path.exists(os.path.join(out, D.QUEUE + c)) for c in D.COUNTERS)
    assert live_offload_queued(out) == set(ids)
    assert not glob.glob(os.path.join(out, "*tmp*"))
    before = {p: open(p, "rb").read() for p in glob.glob(os.path.join(out, "queue_v3_prior*"))}
    D.write_queue(out, ALL, held=held)
    assert {p: open(p, "rb").read() for p in glob.glob(os.path.join(out, "queue_v3_prior*"))} == before  # deterministic
    fail(out, gf)  # a stale marker on a complete row: still done, and nothing new is blocked
    s2 = D.write_queue(out, ALL, held=held)
    assert {k: s2[k] for k in cnt} == cnt and read_lines(os.path.join(out, "queue_v3_prior.blocked")) == P.ids("ZfAP")


def test_queue_lines_parse_in_bash(tmp_path, P):
    out = str(tmp_path)
    ALL, _ = write_ext(out, P.rows)
    D.write_queue(out, ALL)
    q, wf = os.path.join(out, "queue_v3_prior.txt"), os.path.join(out, "queue_v3_prior_weights.txt")
    by = D.index(ALL)
    lines = read_lines(q)
    # the §6.5 three-field read of the prior pool and keeper (M10)
    worker = bash('while IFS="|" read -r eid idx ups; do IFS=, read -ra U <<< "$ups"; echo "$eid $idx ${#U[@]}"; done < "$1"', q)
    assert worker == [f"{ln.split('|')[0]} {ln.split('|')[1]} {len(D.upstreams(by[ln.split('|')[0]], ALL))}" for ln in lines]
    # the live pool's weight reader, verbatim (the prior pool is a copy of aln3_gpu_pool.sbatch): weights are bash integers
    wread = live_line(POOL_SBATCH, r'while read -r e w; do WT\[\$e\]=\$w; done < "\$WF"')
    tot = bash(f'declare -A WT; WF="$1"; {wread}; s=0; for e in "${{!WT[@]}}"; do s=$(( s + ${{WT[$e]}} )); done; echo $s', wf)
    assert int(tot[0]) == sum(D.WEIGHTS[r["family_id"]] for r in P.rows)


def test_old_two_field_reader_must_not_serve_the_prior_queue(tmp_path, P):
    """The live two-field read of keeper.sh / aln3_gpu_pool.sbatch, verbatim: clean on a line without upstreams, but idx keeps
    "|ups" on a line with upstreams (run.py --index would fail and count a try). Hence only keeper_prior.sh and
    aln33_prior_pool.sbatch may serve queue_v3_prior.txt (deps.write_queue docstring)."""
    m = re.search(r"while IFS='\|' read -r eid idx; do", _live_text(POOL_SBATCH))
    if m is None:
        pytest.skip("aln3_gpu_pool.sbatch no longer reads two fields")
    out = str(tmp_path)
    ALL, _ = write_ext(out, P.rows)
    D.write_queue(out, ALL)
    q = os.path.join(out, "queue_v3_prior.txt")
    lines = read_lines(q)
    old = bash(f'{m.group(0)} echo "$eid $idx"; done < "$1"', q)
    assert old == [f"{e} {i}" + (f"|{u}" if u else "") for e, i, u in (ln.split("|") for ln in lines)]
    assert any(ln.endswith("|") for ln in lines) and any(not ln.endswith("|") for ln in lines)


def test_live_readers_at_lane_end(tmp_path, P):
    """The reviewer's lane-end case: a failed dtu core group, everything else done. .remaining is 0 (the keeper stops) and the
    live watcher's unclaimed() counts 0 rows (no false 'keeper seems dead' EVENT), because blocked rows are not listed; the
    offload daemon's queued() keeps only the failed group pending, so the blocked rows pin no checkpoint."""
    out = str(tmp_path)
    ALL, _ = write_ext(out, P.rows)
    q = os.path.join(out, "queue_v3_prior.txt")
    s0 = D.write_queue(out, ALL)  # nothing run yet: the watcher counts every listed row (none done, failed or claimed)
    assert live_unclaimed(out, q) == s0["queued"] == len(P.rows) and s0["remaining"] == len(P.rows)
    _touch(os.path.join(out, "pool", D.QUEUE, f"{P.id('TfS')}.claim", "job"))
    assert live_unclaimed(out, q) == len(P.rows) - 1
    gd = P.id("Gd")
    down = set(P.ids("BdAP", "TdAP", "X", "BX", "TX"))
    fail(out, gd)
    for r in P.rows:
        if r["experiment_id"] not in down | {gd}:
            complete(out, r)
    s = D.write_queue(out, ALL)
    assert s["remaining"] == 0 and s["failed"] == 1 and s["blocked"] == len(down) and s["done"] == len(P.rows) - 1 - len(down)
    assert read_lines(os.path.join(out, "queue_v3_prior.remaining")) == ["0"]
    assert set(read_lines(os.path.join(out, "queue_v3_prior.blocked"))) == down
    listed = {ln.split("|")[0] for ln in read_lines(q)}
    assert not listed & down and listed == {r["experiment_id"] for r in P.rows} - down
    assert live_unclaimed(out, q) == 0
    done_ids = {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(out, "units", "ALN3*.json"))}
    assert live_offload_queued(out) - done_ids == {gd}  # ckpt_offload.one_pass's pending set (no claims)
    os.remove(os.path.join(out, "pool", D.QUEUE, f"{gd}.failed"))  # clearing the marker lists the rows again
    s = D.write_queue(out, ALL)
    assert s["blocked"] == 0 and s["remaining"] == 1 + len(down) and live_unclaimed(out, q) == 1 + len(down)


def test_write_queue_hold_and_binding_propagate(tmp_path, P):
    out = str(tmp_path)
    ALL, _ = write_ext(out, P.rows)
    q = lambda: [ln.split("|")[0] for ln in read_lines(os.path.join(out, "queue_v3_prior.txt"))]  # noqa: E731
    down_f = set(P.ids("BfAP", "BfXP", "BfJ", "BfXM", "TfAP", "TfJ", "TfXM", "ZfAP", "ZfJ", "ZfXM", "ZfJ_B", "R", "BR", "TR", "ZR", "C", "BC", "TC", "ZC"))
    D.write_queue(out, ALL, held=[P.id("Gf")])
    assert set(q()) == {r["experiment_id"] for r in P.rows} - down_f - {P.id("Gf")}
    complete_group(out, P["Gf"])
    D.write_queue(out, ALL, held=[P.id("Gf")])  # a held group that is done no longer holds its dependents
    assert set(q()) == {r["experiment_id"] for r in P.rows} - {P.id("Gf")}
    s = D.write_queue(out, ALL, bound=set(S.FAMILIES) - {S.RICH_DONOR})  # unbound family: R and, transitively, its rows
    assert set(q()) == {r["experiment_id"] for r in P.rows} - set(P.ids("R", "BR", "TR", "ZR")) and s["held"] == 4
    D.write_queue(out, ALL, held={S.TARGET})
    assert not {P.id(k) for k in ("TfS", "TfAP", "TpS", "TR", "TC")} & set(q()) and P.id("BfAP") in q()
    D.write_queue(out, ALL, held=None)
    assert len(q()) == len(P.rows)


def test_counters_with_only_failed_or_done_rows(tmp_path):
    P = Plan()
    P.group("G", "fau")
    P.bridge("B", "G", "AP")
    P.zeroshot("Z", "G", "B", "AP", 0, 0)
    P.target("T", "G", "AP", 0, 0)
    out = str(tmp_path)
    ALL, ext = write_ext(out, P.rows)
    pos = {r["experiment_id"]: D.EXT_OFFSET + j for j, r in enumerate(ext)}
    rd = lambda c: read_lines(os.path.join(out, D.QUEUE + c))  # noqa: E731
    queue = lambda: read_lines(os.path.join(out, "queue_v3_prior.txt"))  # noqa: E731
    fail(out, P.id("G"))
    s = D.write_queue(out, ALL)
    assert rd(".remaining") == ["0"] and rd(".waiting") == ["0"] and rd(".blocked") == P.ids("B", "T", "Z")  # keeper may stop
    assert s["failed"] == 1 and s["blocked"] == 3 and s["remaining"] == 0 and queue() == [f"{P.id('G')}|{pos[P.id('G')]}|"]
    os.remove(os.path.join(out, "pool", D.QUEUE, f"{P.id('G')}.failed"))
    s = D.write_queue(out, ALL)
    assert rd(".remaining") == ["4"] and rd(".waiting") == ["3"] and rd(".blocked") == [] and s["ready"] == 1 and len(queue()) == 4
    for k in ("G", "B", "Z", "T"):
        complete(out, P[k])
    s = D.write_queue(out, ALL)
    assert rd(".remaining") == ["0"] and s["done"] == 4 and len(queue()) == 4
    filler, _ = write_ext(out, [])
    s = D.write_queue(out, filler)
    assert s["queued"] == 0 and queue() == [] and rd(".remaining") == ["0"]


def test_write_queue_unresolved_and_plan_errors(tmp_path, P):
    out = str(tmp_path)
    ALL, ext = write_ext(out, P.rows)
    complete(out, P["Gp"], members={"AP": {"best": {"ce_dev": 1.0}}})  # cannot resolve J*
    ckpt(out, P.id("Gp"), *CORE)
    s = D.write_queue(out, ALL)
    assert set(s["unresolved"]) == {P.id("BpJ"), P.id("TpJ")} and s["queued"] == len(P.rows) - 2  # only its J* rows, not listed
    assert all("members['J1']['best']['ce_dev']" in v for v in s["unresolved"].values())
    # the reviewer's drifted layout (members.M.best.CE_dev) leaves every J* row of the group unresolved (waiting, not failed)
    rec = complete_group(out, P["Gf"])
    rec["members"] = {m: {"best": {"CE_dev": 4.0}} for m in CORE}
    del rec["joint_choice"]
    with open(S.record_path(out, P.id("Gf")), "w") as f:
        json.dump(rec, f)
    ckpt(out, P.id("Gf"), *CORE)
    s = D.write_queue(out, ALL)
    assert set(s["unresolved"]) == set(P.ids("BpJ", "TpJ", "BfJ", "TfJ", "ZfJ", "ZfJ_B")) and s["failed"] == 0
    with pytest.raises(S.SelectionError):
        S.check_group_record(rec)
    with pytest.raises(FileNotFoundError):
        D.write_queue(str(tmp_path / "noext"), P.rows)
    os.makedirs(tmp_path / "e")
    assert D.write_queue(str(tmp_path / "e"), P.rows, ext=ext)["queued"] == len(P.rows)  # explicit plan_ext list
    with pytest.raises(ValueError):
        D.write_queue(str(tmp_path / "e"), P.rows, ext=ext[: len(ext) // 2])  # a prior row missing from plan_ext
    os.makedirs(tmp_path / "f")
    for bad in (ALL + [json.loads(json.dumps(P["TfS"]))],  # duplicate prior id
                ALL + [variant(P["R"], deps=["frozen_manifest", "rich_cache"], horizon_from=DEL)],  # rich group without horizon
                ALL + [variant(P["ZfJ"], deps=P.ids("Gf", "BfJ", "BfAP"))]):  # a second bridge
        with pytest.raises(ValueError):
            D.write_queue(str(tmp_path / "f"), bad, ext=ext + bad[len(ALL):])
    assert os.listdir(tmp_path / "f") == []  # nothing is written for an inconsistent plan


def test_unresolved_rows_get_no_queue_line(tmp_path, P):
    """M8 review (residual of round 1 #1): the J* rows of a complete group record that cannot resolve J* were counted as waiting
    but listed with their upstreams, and the §6.5 worker admits a listed row as soon as its upstream records exist: each would
    raise SelectionError, end technical_failed three times, get .failed and block its dependents. They are now waiting rows with
    no queue or weight line (no worker, keeper or watcher sees them as claimable) and not in .blocked; .remaining keeps the keeper
    running until the record is fixed, and the next refresh lists them."""
    out = str(tmp_path)
    ALL, _ = write_ext(out, P.rows)
    q = os.path.join(out, "queue_v3_prior.txt")
    rd = lambda c: read_lines(os.path.join(out, D.QUEUE + c))  # noqa: E731
    gp = P.id("Gp")
    complete(out, P["Gp"], members={"AP": {"best": {"ce_dev": 1.0}}})  # a record that cannot resolve J* (no J1 / J025 CE_dev)
    ckpt(out, gp, *CORE)
    unres = set(P.ids("BpJ", "TpJ"))
    s = D.write_queue(out, ALL)
    listed = [ln.split("|")[0] for ln in read_lines(q)]
    assert set(s["unresolved"]) == unres and not unres & set(listed) and len(listed) == s["queued"] == len(P.rows) - 2
    assert not unres & {ln.split()[0] for ln in rd("_weights.txt")} and not unres & set(rd(".blocked"))
    assert s["waiting"] >= 2 and int(rd(".waiting")[0]) == s["waiting"] and int(rd(".remaining")[0]) == s["remaining"]
    # the §6.5 three-field worker read never sees them (a worker would admit TpJ: its only upstream record exists)
    worker = bash('while IFS="|" read -r eid idx ups; do echo "$eid"; done < "$1"', q)
    assert not unres & set(worker) and D.upstreams(P["TpJ"], ALL) == [gp] and os.path.exists(S.record_path(out, gp))
    # lane end with only the unresolved rows left: .remaining 2 (the keeper keeps running), nothing claimable for the watcher
    for r in P.rows:
        if r["experiment_id"] not in unres | {gp}:
            complete(out, r)
    s = D.write_queue(out, ALL)
    assert s["remaining"] == s["waiting"] == 2 and rd(".remaining") == ["2"] and live_unclaimed(out, q) == 0
    assert set(s["unresolved"]) == unres and rd(".blocked") == []
    complete_group(out, P["Gp"])  # the record is fixed (pinned layout): the next refresh lists them, ready
    s = D.write_queue(out, ALL)
    assert s["unresolved"] == {} and s["ready"] == 2 and unres <= {ln.split("|")[0] for ln in read_lines(q)}
    assert live_unclaimed(out, q) == 2


def test_ckpt_deps_uses_a_prebuilt_index(P):
    """M10 integration note (a): ckpt_deps(row, rows) re-indexed a list on every call (1.3 s per offload pass for 1,154 pending
    rows); with deps.index(rows) built once per pass (or ckpt_offload.deps_of's own `by`) it only looks up the row's own
    upstreams. A mapping that refuses any pass over itself proves it; the answers equal the list's for every row."""

    class NoPass(dict):
        def _no(self, *a):
            raise AssertionError("the index was iterated")
        __iter__ = keys = values = items = __len__ = _no

    idx = D.index(P.rows)
    assert D.index(idx) is idx  # a dict is used as given
    np_idx = NoPass(idx)
    for r in P.rows:
        assert D.ckpt_deps(r, np_idx) == D.ckpt_deps(r, idx) == D.ckpt_deps(r, P.rows)
        assert D.upstreams(r, np_idx) == D.upstreams(r, P.rows)
        D.check_row(r, np_idx)
    last_wins = {r["experiment_id"]: r for r in P.rows}  # ckpt_offload.deps_of's own `by` (last-wins; no duplicates here)
    assert all(D.ckpt_deps(r, last_wins) == D.ckpt_deps(r, P.rows) for r in P.rows)


def test_rows_are_indexed_on_every_call(tmp_path, P):
    """The reviewer's stale-cache case: a list element replaced in place (same list object, same length) is seen at once."""
    rows = list(P.rows)
    assert D.upstreams(P["BfAP"], rows) == P.ids("Gf")
    g2 = variant(P["Gd"], top={"dataset": "federici"})
    rows[rows.index(P["TfS"])] = g2
    b2 = variant(P["BdAP"], deps=[g2["experiment_id"]], donor_group=g2["experiment_id"], top={"dataset": "federici"})
    assert D.upstreams(b2, rows) == [g2["experiment_id"]] and D.ckpt_deps(b2, rows) == [g2["experiment_id"]]
    D.check_row(b2, rows)
    assert D.ready(g2, rows, str(tmp_path)) and not D.ready(b2, rows, str(tmp_path))
    rows.append(b2)
    prior = [r for r in rows if r["family_id"] in S.FAMILIES]
    s = D.write_queue(str(tmp_path), rows, ext=prior)
    assert s["queued"] == len(prior) and P.id("TfS") not in {ln.split("|")[0] for ln in read_lines(tmp_path / "queue_v3_prior.txt")}


# ------------------------------------------------------------------------------------------------------- module boundaries
def test_select_never_shadows_the_stdlib_select():
    """A prior33 file run by path puts prior33/ at sys.path[0]; `import subprocess` (selectors -> select) must still get the
    standard library's select, and the package module stays importable beside it."""
    here = os.path.dirname(os.path.abspath(S.__file__))
    probe = ("import sys, subprocess, select; assert select.__name__ == 'select' and hasattr(select, 'select'), select; "
             "assert not select.__file__.endswith('.py'), select.__file__; "
             "assert subprocess.run([sys.executable, '-c', 'pass']).returncode == 0; "
             "from auditory_alignment_v3.prior33 import select as M; assert M.LAMBDA_RULE and M.__name__.endswith('prior33.select'); "
             "print('ok')")
    env = {**os.environ, "PYTHONPATH": REPO}
    for cmd, cwd in (([sys.executable, "-B", "-c", f"import sys; sys.path.insert(0, {here!r}); " + probe], None),  # file run by path
                     ([sys.executable, "-B", "-c", probe], here)):  # a session started inside prior33/ ('' first on sys.path)
        r = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=cwd)
        assert r.returncode == 0 and r.stdout.strip() == "ok", r.stderr[-2000:]


def test_zero_shot_constants_match_contract():
    from auditory_alignment_v3.prior33 import contract as C
    assert D.ZS_SUFFIX == C.ZS_SUFFIX and D.ZS_COHORTS == C.ZS_COHORTS


def test_modules_stay_light():
    code = "import sys; import auditory_alignment_v3.prior33.deps, auditory_alignment_v3.prior33.select; " \
           "print(sorted(m for m in ('torch', 'numpy', 'scipy', 'auditory_alignment_v3.core', 'auditory_alignment_v3.registry') " \
           "if m in sys.modules))"
    env = {**os.environ, "PYTHONPATH": REPO}
    got = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, text=True, env=env, check=True).stdout.strip()
    assert got == "[]"
