"""ALN3.1 seed-confirmation panel registration (docs/auditory_alignment_v3/ADDENDUM_03_ALN3_1_SEED_PANEL.md): the extension
file keeps the 300 item-3 rows byte-identical, adds exactly the role x seed rows the v3.0 plan lacks, every new row can resolve
its same-seed dependency, the deferred_redundant set is the complement of the roles within the v3.0 panel, and the dispatcher
exposes plan + extension rows to the runners' lookups. Static checks only (no training)."""
import hashlib
import json
import os

import yaml

from auditory_alignment_v3 import core, run, run_attention, run_complement, run_transfer

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PKG31 = os.path.join(REPO, "AUDITORY_ALN3_SERVER_PACKAGE_v3_1_20261011")
EXT = [json.loads(l) for l in open(os.path.join(core.OUT, "plan_ext.jsonl"))]
PLAN = core.load_rows()
ALL = PLAN + EXT
NEW = EXT[300:]
GOV = json.load(open(os.path.join(core.OUT, "governance", "deferred_redundant_v30_panel.json")))
REG = json.load(open(os.path.join(core.OUT, "governance", "seed_panel_v31_registry.json")))
RULES = yaml.safe_load(open(os.path.join(PKG31, "configs", "seed_confirmation_pairs.yaml")))


SIG_KEYS = ("family_id", "dataset", "job_kind", "base_commit", "seed", "subject_fold", "content_fold", "spec", "logical_dependencies", "status", "seed_scope")


def canonical(r):  # = the package's register_seed_pairs.canonical on plan rows; ignores bookkeeping keys of extension rows
    d = {k: r[k] for k in SIG_KEYS if k not in ("seed", "seed_scope", "status")}
    return hashlib.sha256(json.dumps(d, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def matches(row, selector):
    return all(row.get(k, row["spec"].get(k)) in (v if isinstance(v, list) else [v]) for k, v in selector.items())


def test_block1_unchanged():
    assert len(EXT) >= 300 and all(r["experiment_id"].startswith("ALN3X_") for r in EXT[:300])
    assert hashlib.sha256("".join(json.dumps(x) + "\n" for x in EXT[:300]).encode()).hexdigest().startswith("bbc96cd30c40b27c")


def test_new_rows_are_exactly_the_missing_role_seed_requirements():
    plan_keys = {(canonical(r), r["seed"]) for r in PLAN}
    need = set()
    for panel in RULES["panels"]:
        for role in panel["roles"]:
            for r in [x for x in PLAN if x["seed"] == 3401 and matches(x, role["selector"])]:
                for s in RULES["seeds"]:
                    need.add((canonical(r), s))
    missing = need - plan_keys
    new_keys = {(canonical(r), r["seed"]) for r in NEW}
    assert new_keys == missing and len(NEW) == len(missing) == 950
    assert len({r["experiment_id"] for r in ALL}) == len(ALL)  # no id collision with the plan or block 1
    assert all(r["seed"] in (3407, 3413) and r["seed_scope"] == "panel" and r["status"] == "planned_needs_binding" for r in NEW)
    assert all(r["reference_3401_id"] in {x["experiment_id"] for x in PLAN} and r["panel_roles"] for r in NEW)
    assert REG["n_requirements"] == len(need) == 2565 and REG["n_new_rows"] == 950 and REG["n_present_in_v30_plan"] == 1615


def test_new_row_ids_follow_the_package_signature_rule():
    keys = ("family_id", "dataset", "job_kind", "base_commit", "seed", "subject_fold", "content_fold", "spec", "logical_dependencies", "status", "seed_scope")
    pid = lambda r: "ALN3_" + hashlib.sha256(json.dumps({k: r[k] for k in keys}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]
    assert all(pid(r) == r["experiment_id"] for r in PLAN[:200] + NEW)


def test_new_rows_resolve_their_same_seed_dependencies():
    for r in NEW:
        f = r["family_id"]
        if f.startswith("C_"):
            b = run_complement.base_row(r, ALL); assert b is not None and b["seed"] == r["seed"] and b["family_id"] == "A_LOCAL"
        elif f == "D_ADAPT":
            b = run_complement.base_row({**r, "spec": {**r["spec"], "local_architecture": "lag_local_tokens", "window": "full"}}, ALL)
            assert b is not None and b["seed"] == r["seed"]
        elif f == "D_ATTENTION" and r["spec"]["integrator"] != "mean_score":
            t = run_attention.twin_row(r, ALL); assert t["seed"] == r["seed"] and t["experiment_id"] in {x["experiment_id"] for x in NEW}
        elif f == "E_PUBLIC_TRANSFER":
            d = run_transfer.local_donor_row(r, ALL); assert d is not None and d["seed"] == r["seed"]


def test_deferred_redundant_is_the_role_complement_of_the_v30_panel():
    need = {(x["canonical"], x["seed"]) for x in REG["requirements"]}
    panel = [r for r in PLAN if r["seed_scope"] == "panel"]
    expect = {r["experiment_id"] for r in panel if (canonical(r), r["seed"]) not in need}
    assert set(GOV["ids"]) == expect and len(expect) == 750 and GOV["by_family"] == {"B_DENSE": 300, "C_COMPLEMENT": 300, "A_LOCAL": 150}
    assert not any(os.path.exists(os.path.join(core.OUT, "units", f"{e}.json")) for e in GOV["ids"])
    kept = {r["experiment_id"] for r in panel} - expect
    assert len(kept) == 760 and all((canonical(r), r["seed"]) in need for r in panel if r["experiment_id"] in kept)


def test_dispatcher_exposes_plan_and_extension_rows():
    rows = run.all_rows()
    assert rows[:len(PLAN)] == PLAN and len(rows) == len(PLAN) + len(EXT)
    assert run.ext_rows()[300] == NEW[0] and run.EXT_OFFSET == 100000
