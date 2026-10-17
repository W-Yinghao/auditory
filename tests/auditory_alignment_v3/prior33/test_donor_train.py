"""M5 donor-training tests (PUBLIC_PRIOR_DESIGN.md §7.1 items 8, 10a-10f and 11, the M5 task list): lockstep members see identical
batches, equal steps, the group trigger (XM never triggers; a flat curve never extends) and the compute-limit continuation flag
with its retained stable states, the side branch reproducing the 30-ep-eq decay exactly, resume (in the middle of a side branch
too, and after a pre-emption between a validation's files and its resume save) giving identical outputs, the adopted horizon of
rich / CSX groups and the rich stream-hash check, the continuation following the larger-limit trajectory, the member losses being
the registered terms, the lambda rule recorded, the checkpoint naming (select.py helpers), CE_dev on hand cases, the spec checks,
the version and identity checks of adopted horizons and continuations, both objectives (NCE, CS_SINGLE), the compute record
(synchronised member seconds, per-member FLOP proxy, the joint's extra compute, the continuation split), tiny real-like runs on the
scale-4 fixture (CPU, max_steps small) that write valid strict-JSON records through run_donor.run, those records read back by
select, deps.ready and analysis._donor_table, and a real-stack chain (core groups with side branch, ceiling, a failure after
training, a continuation and a rich group checked against a real core record) under an open-file audit.

Two kinds of tests:
- schedule mechanics with fast fakes (FakeSampler: a seeded stream of small random batches with exact state / load_state and a
  hash chain; FakeValidator: scripted CE_dev / gain values per (member, branch, step) that also records a hash of every
  member's weights at every validation; TinyEncoder: a linear stand-in for the encoder, since the mechanics do not depend on the
  architecture); the members, their losses, AdamW, the schedule, the checkpoints and the resume files are the real ones;
- the real stack (DonorSampler, DevValidator, SharedEncoder, losses, rich, run_donor) on fixtures.make_synthetic_manifest(scale=4),
  with the fixed sets cut to 6 fit segments and 8 dev / bridge_cal queries (2 and 2 in the chain; monkeypatched
  sampler.selection_sets; candidates unchanged) to keep the CPU validations short; the real resume test uses a copy of the
  manifest whose budget declares 1 ep-eq = 2 steps (anchors_per_ep_eq 512), the chain one with 1 ep-eq = 0.5 steps
  (anchors_per_ep_eq 128: 30 ep-eq = 15 steps; everything else, the sha included, unchanged).
Synthetic data only, CPU only; about 3-9 minutes (load-dependent), peak RSS about 1 GB."""
import contextlib
import copy
import hashlib
import json
import math
import os
import sys
import types

import numpy as np
import pytest
import torch

from auditory_alignment_v3 import core
from auditory_alignment_v3.prior33 import contract as C
from auditory_alignment_v3.prior33 import donor_train as DT
from auditory_alignment_v3.prior33 import losses as L
from auditory_alignment_v3.prior33 import model as MD
from auditory_alignment_v3.prior33 import run_donor as RD
from auditory_alignment_v3.prior33 import sampler as SM
from auditory_alignment_v3.prior33 import select as SEL
from auditory_alignment_v3.prior33 import views as V

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fixtures import make_synthetic_manifest  # noqa: E402

torch.set_num_threads(1)
CORE5 = SEL.GROUP_MEMBERS[SEL.DONOR]
LAYOUT = C.VOCAB[:4]
_ORIG_SETS = SM.selection_sets

# ---------------------------------------------------------------------------------------------------------- open-file audit hook
_OPENED = None                       # a list while opened_files() is active (as in test_views_sampler.py)


def _audit(event, args):
    if _OPENED is not None and event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
        _OPENED.append(os.path.abspath(os.fsdecode(args[0])))


sys.addaudithook(_audit)


@contextlib.contextmanager
def opened_files():
    global _OPENED
    _OPENED = []
    try:
        yield _OPENED
    finally:
        _OPENED = None


def _strict_json(text):
    """json.loads that refuses NaN / Infinity tokens (a strict parser)."""
    def bad(token):
        raise ValueError(f"non-standard JSON token {token}")
    return json.loads(text, parse_constant=bad)


# ---------------------------------------------------------------------------------------------------------- fakes
class TinyEncoder(torch.nn.Module):
    """A linear stand-in for SharedEncoder (same call signature, layout and seen_names): fast schedule-mechanics tests."""

    def __init__(self, seed=11):
        super().__init__()
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(seed)
            self.lin = torch.nn.Linear(len(LAYOUT) * C.L_IN, 32)
        self.layout = tuple(LAYOUT)

    def forward(self, x, layout=None, mask=None):
        return torch.nn.functional.normalize(self.lin(x.float().flatten(1)), dim=1)

    def seen_names(self):
        return list(LAYOUT)


def _sha_state(enc):
    h = hashlib.sha256()
    for k, v in sorted(enc.state_dict().items()):
        h.update(k.encode())
        h.update(v.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


class FakeSampler:
    """A seeded stream of 4-segment x 8-anchor batches (32 rows, 4 channels) with DonorSampler's batch fields, exact state /
    load_state, a sha256 chain over the draws (logged every `every` steps), a separate derangement generator and xm_view."""

    N_SEG, N_TABLE, N_PRES, N_FAM = 4, 24, 6, 3

    def __init__(self, seed, every=5):
        self.seed, self.every = seed, every
        self.rng, self.xm_rng = np.random.default_rng(seed), np.random.default_rng(seed + 7)
        self.step, self._chain, self.hash_log = 0, hashlib.sha256(b"fake").digest(), []
        pres = np.arange(self.N_TABLE) % self.N_PRES
        self.idx = types.SimpleNamespace(seg={"fake": {"presentation": pres}}, fam=np.arange(self.N_PRES) % self.N_FAM, n_pres=self.N_PRES)
        self.manifest = {"families": [{"id": i, "name": f"fam{i}", "cohort": "fake"} for i in range(self.N_FAM)]}
        self.strata, self.weights = ["fake"], np.ones(1)

    def next_batch(self):
        r = self.rng
        seg = np.sort(r.choice(self.N_TABLE, size=self.N_SEG, replace=False)).astype(np.int64)
        x1 = r.standard_normal((32, len(LAYOUT), C.L_IN)).astype(np.float32)
        x2 = (x1 + 0.5 * r.standard_normal(x1.shape)).astype(np.float32)
        y = r.standard_normal((32, C.N_TGT)).astype(np.float32)
        pres = self.idx.seg["fake"]["presentation"][seg]
        s = (np.repeat(seg, 8) * 1000 + np.tile(np.arange(8) * 31, self.N_SEG)).astype(np.int64)
        keys = C.pack_key(np.repeat(self.idx.fam[pres], 8).astype(np.int64), np.repeat(pres, 8).astype(np.int64), s)
        p1 = np.repeat(10 + 2 * seg, 8).astype(np.int64)
        h = hashlib.sha256(self._chain)
        h.update(seg.tobytes())
        self._chain = h.digest()
        self.step += 1
        if self.step % self.every == 0:
            self.hash_log.append([self.step, self._chain.hex()])
        T = torch.as_tensor
        return types.SimpleNamespace(x1=T(x1), x2=T(x2), y=T(y), keys=T(keys), part1=T(p1), part2=T(p1 + 1), fam_s=T(s), stratum="fake",
                                     chan_mask=torch.ones(2, 32, len(LAYOUT), dtype=torch.bool), seg_ids=seg, partner_ids=seg, cohort="fake",
                                     layout=tuple(LAYOUT), ticks=np.zeros((4, 8), np.int64), montage=None, step=self.step - 1, rich=None,
                                     rich_mask=None)

    def derangement(self, batch):
        n = len(batch.seg_ids)
        perm = self.xm_rng.permutation(n)
        while (perm == np.arange(n)).any():
            perm = self.xm_rng.permutation(n)
        return perm.astype(np.int64), {"method": "random_draw", "draws": 1, "violations": 0, "violations_family": 0, "violations_partner": 0,
                                       "feasible": True, "same_condition_fraction": 1.0}

    xm_view = staticmethod(SM.DonorSampler.xm_view)

    def stream_hash(self):
        return self._chain.hex()

    def state(self):
        return {"rng": copy.deepcopy(self.rng.bit_generator.state), "xm_rng": copy.deepcopy(self.xm_rng.bit_generator.state),
                "step": self.step, "chain": self._chain.hex(), "hash_log": [list(x) for x in self.hash_log]}

    def load_state(self, st):
        self.rng.bit_generator.state = copy.deepcopy(st["rng"])
        self.xm_rng.bit_generator.state = copy.deepcopy(st["xm_rng"])
        self.step, self._chain = int(st["step"]), bytes.fromhex(st["chain"])
        self.hash_log = [[int(a), str(b)] for a, b in st["hash_log"]]


class FakeValidator:
    """Scripted scores: script(member, branch, step) -> (ce_dev, gain). Records the weights hash of every member at every
    validation, keyed (branch, step, member)."""

    n_segments = 0

    def __init__(self, script):
        self.script, self.run, self.hashes, self.calls = script, None, {}, 0

    def validate(self, encs, sigma):
        r = self.run
        self.calls += 1
        out = {}
        for m, enc in encs.items():
            ce, gain = self.script(m, r.branch, r.step)
            self.hashes[(r.branch, r.step, m)] = _sha_state(enc)
            out[m] = {"dev": {"ce_bits": ce, "gain": gain, "r_own": 0.5, "tau": 0.01, "n_cand": 9, "n_q": 9}, "diag": {}}
        return out

    def bridge_cal(self, encs):
        return {k: {"ce_bits": 2.0, "r_own": 0.4, "n_cand": 9} for k in encs}

    def sizes(self):
        return {"rows_sha": {}}


def improving_ce(m, branch, step):        # every member always improves: the trigger fires at every decay start
    return 10.0 - 0.01 * step - (0.001 if branch == "side" else 0.0), 0.01 * step


def flat_ce(m, branch, step):             # best at step 5, never in the last 3: the trigger never fires
    return 10.0 + abs(step - 5), -abs(step - 9)


def xm_only_ce(m, branch, step):          # only XM keeps improving: XM never triggers
    return improving_ce(m, branch, step) if m == "XM" else flat_ce(m, branch, step)


def collapsed_ce(m, branch, step):        # AP collapsed (the same CE_dev at every validation); the others worsen from the start
    return (math.log2(9) if m == "AP" else 5.0 + 0.01 * step), 0.0


P_FIXED = np.linalg.qr(np.random.default_rng(0).standard_normal((32, 8)))[0].astype(np.float32)


def fake_row(gid, fam=SEL.DONOR, limit=60, members=None, **spec):
    return {"experiment_id": gid, "family_id": fam, "dataset": "fau", "subject_fold": None, "content_fold": None, "seed": 11,
            "spec": {"stage": "donor_group", "block": {SEL.DONOR: "core", SEL.RICH_DONOR: "rich", SEL.CSX_DONOR: "csx"}[fam],
                     "objective": "NCE", "members": list(members or SEL.GROUP_MEMBERS[fam]), "donor_seed": 11, "sampler_seed": 11,
                     "budget": {"epoch_equivalents": 30, "continuation": f"group_wsd_any_last3_ext10_limit{limit}_v1"}, **spec}}


def fake_run(out, row, script, *, adopted=None, adopted_ceiling=False, hooks=None, inherit=None, horizon=None, max_steps=None,
             objective="NCE", steps_per_ep_eq=1):
    """A real _GroupRun (real members, losses, AdamW, checkpoints, resume files) on FakeSampler / FakeValidator; 1 ep-eq = 1 step."""
    os.makedirs(os.path.join(out, "ckpt"), exist_ok=True)
    members = SEL.group_members(row)
    _, ext, limit = DT.parse_rule(row)
    smp = FakeSampler(11)
    heads = {"env": MD.SharedFixedHead(np.ones(8), P_FIXED)}
    sigma = {"sigma_u": 1.0, "sigma_v": 1.0}
    mems = {m: DT._Member(m, TinyEncoder(), objective, sigma, (), heads) for m in members}
    wsd = DT.GroupWSD(32 * steps_per_ep_eq, rows=32, limit=limit, ext=ext,
                      trigger=tuple(m for m in DT.TRIGGER_MEMBERS if m in members) if row["family_id"] == SEL.DONOR else (),
                      adopted=adopted, adopted_ceiling=adopted_ceiling)
    val = FakeValidator(script)
    run = DT._GroupRun(row=row, members=mems, sampler=smp, validator=val, wsd=wsd, heads=heads, out=out, device=torch.device("cpu"),
                       sigma=sigma, max_steps=max_steps, hooks=hooks, horizon=horizon, inherit=inherit,
                       scratch=lambda m: TinyEncoder(), meta={"manifest_sha256": "f" * 64})
    val.run = run
    return run, val


class Interrupt(Exception):
    pass


class StopAt(DT._Hooks):
    """Raise after the resume save that follows the validation at (branch, step)."""

    def __init__(self, branch, step):
        self.at = (branch, step)

    def after_save(self, run):
        if (run.branch, run.step) == self.at:
            raise Interrupt(self.at)


class StopBeforeSave(DT._Hooks):
    """Raise after the validation at (branch, step) wrote its checkpoint (and stable) files, before its resume save: a pre-emption
    in that window."""

    def __init__(self, branch, step):
        self.at = (branch, step)

    def before_save(self, run):
        if (run.branch, run.step) == self.at:
            raise Interrupt(self.at)


class RecordBatches(DT._Hooks):
    def __init__(self):
        self.seen = []

    def on_member(self, tag, batch, xm):
        self.seen.append((batch.step, tag, id(batch), None if xm is None else (id(xm), xm.perm.tolist())))


def _enc(path):
    return torch.load(path, map_location="cpu", weights_only=True)["enc"]


def _same_state(a, b):
    return set(a) == set(b) and all(torch.equal(a[k], b[k]) for k in a)


def _strip(entry):
    return {k: v for k, v in entry.items() if k not in ("train",)}


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    """Fake group runs shared by several tests: A limit 30 (always improving -> ceiling at 30), B limit 60 (always improving ->
    extends 30 -> 40 -> 50 -> 60, side branch at 27, ceiling at 57), N limit 60 (never improving -> 30), D limit 70 (always
    improving -> ceiling at 67), X limit 60 (only XM improving)."""
    out = {}
    for name, limit, script in (("A", 30, improving_ce), ("B", 60, improving_ce), ("N", 60, flat_ce), ("D", 70, improving_ce),
                                ("X", 60, xm_only_ce)):
        d = str(tmp_path_factory.mktemp(f"m5_{name}"))
        row = fake_row(f"ALN3X_{name.lower() * 16}", limit=limit)
        run, val = fake_run(d, row, script)
        run.run()
        rec = run.finish()
        left = sorted(f for f in os.listdir(os.path.join(d, "ckpt")) if "resume" in f)       # finish() keeps them for the caller
        removed = DT.remove_resume_files(d, row["experiment_id"])                             # as run_donor does after the record
        out[name] = {"dir": d, "row": row, "run": run, "val": val, "rec": rec, "resume_left": left, "removed": removed}
    return out


# ---------------------------------------------------------------------------------------------------------- GroupWSD logic
def test_budget_and_rule_parsing(fx4):
    """steps_at reproduces the design count (N_SK 86,285 -> 1 ep-eq = 690,280 anchors, S0 = 80,893 steps) and the fixture's S0;
    the rule text is parsed and anything else is refused; the limit must lie on 30 + 10 k."""
    assert DT.steps_at(30, 8 * 86285) == 80893 and DT.steps_at(1, 8 * 86285) == 2697
    b = fx4["manifest"]["budget"]
    assert DT.steps_at(30, b["anchors_per_ep_eq"]) == b["S0"]
    assert DT.parse_rule(fake_row("g", limit=60)) == (3, 10, 60) and DT.parse_rule(fake_row("g", limit=90)) == (3, 10, 90)
    r = fake_row("g")
    del r["spec"]["budget"]
    assert DT.parse_rule(r) == (3, 10, 60)
    for bad in ("group_wsd_v1", "group_wsd_any_last3_ext10_limit60_v2", "group_wsd_all_last3_ext10_limit60_v1"):
        r = fake_row("g")
        r["spec"]["budget"]["continuation"] = bad
        with pytest.raises(ValueError):
            DT.parse_rule(r)
    with pytest.raises(ValueError):
        DT.GroupWSD(256, limit=65)
    with pytest.raises(ValueError):
        DT.GroupWSD(256, adopted=35)
    with pytest.raises(ValueError):
        DT.GroupWSD(256, adopted=40, adopted_ceiling=True)


def test_group_trigger_rule_xm_ignored_and_ceiling():
    """§7.1 10b / 10d at the decision level: any contract member with the first minimum of its stable CE_dev in its last 3 stable
    validations extends the whole group by 10 ep-eq (side branch at the first extension only); XM never triggers; a firing
    trigger at the limit sets the ceiling flag instead; non-finite values count as +inf. A tie with an earlier validation does
    not count (inherited EXECUTION §7 / yaml continue_when_donor_dev_improves: a flat curve does not improve)."""
    assert DT.improving([5, 4, 3, 2.9]) and not DT.improving([1, 4, 3, 2.9]) and not DT.improving([1, 2, 3, 1.0])
    assert DT.improving([3, 2, 2, 2]) and not DT.improving([2, 2, 2, 2]) and DT.improving([1, 2, 3, 1.0 - 1e-12])
    assert not DT.improving([float("nan")] * 5) and DT.improving([float("nan"), 2.0]) and not DT.improving([])
    assert not DT.improving([math.log2(9)] * 27) and not DT.improving([float("nan")] * 24 + [math.inf] * 3)
    assert DT.improving([float("inf")] * 24 + [7.0, 8.0, 9.0])
    # a collapsed encoder (one output for every input): dev_scores gives a finite CE_dev of about log2(n_cand), the same value at
    # every validation while the weights stay put; that flat curve never extends the group, and the trigger log says so
    rng = np.random.default_rng(5)
    Yf, Yc = rng.standard_normal((6, 250, 8)), rng.standard_normal((4, 250, 8))
    col = DT.dev_scores(np.ones((6, 250, 32)), Yf, np.ones((5, 250, 32)), Yc, np.array([0, 1, 2, 3, 0]), np.array([1, -1, 3, 0, 2]))
    assert not col["nonfinite"] and col["ce_bits"] == pytest.approx(2.0, abs=1e-6) and not DT.improving([col["ce_bits"]] * 27)
    worse = [4.0 + 0.1 * i for i in range(27)]
    wf = DT.GroupWSD(256)
    e = wf.decide(27, {"AP": [col["ce_bits"]] * 27, "XP": worse, "J1": worse, "J025": worse})
    assert e["decision"] == "decay" and not e["fires"] and wf.H == 30 and not wf.ceiling
    assert all(v["improving"] is False and v["best_index"] == 0 and v["last_window_start"] == 24 for v in e["members"].values())
    w = DT.GroupWSD(256)
    stale = list(range(27, 0, -1))[::-1]                                # best at the first validation
    up = list(range(27, 0, -1))                                         # strictly decreasing: best at the last
    e = w.decide(27, {"AP": stale, "XP": stale, "J1": stale, "J025": up})
    assert e["decision"] == "extend" and e["side_branch"] and w.H == 40 and w.side == {"status": "active", "start": 27, "end": 30}
    w.end_side()
    e = w.decide(37, {"AP": up + [-k for k in range(1, 11)], "XP": stale, "J1": stale, "J025": stale})
    assert e["decision"] == "extend" and not e["side_branch"] and w.H == 50
    wt = DT.GroupWSD(256)                                               # the same with a flat tail: the minimum came 10 earlier
    wt.decide(27, {"AP": up})
    wt.end_side()
    e = wt.decide(37, {"AP": up + [0] * 10, "XP": stale, "J1": stale, "J025": stale})
    assert e["decision"] == "decay" and not e["fires"] and wt.H == 40 and e["members"]["AP"]["best_index"] == 27
    w2 = DT.GroupWSD(256)
    e = w2.decide(27, {"AP": stale, "XP": stale, "J1": stale, "J025": stale, "XM": up})
    assert e["decision"] == "decay" and not e["fires"] and w2.H == 30 and "XM" not in e["members"]
    w3 = DT.GroupWSD(256, limit=30)
    e = w3.decide(27, {"AP": up})
    assert e["decision"] == "ceiling" and w3.ceiling and w3.H == 30
    with pytest.raises(ValueError):
        w3.decide(26, {"AP": up})
    # lr: constant, then linear to 0 over the final 3 ep-eq of the branch's horizon; phase and h30 eligibility
    w4 = DT.GroupWSD(256)                                              # 1 step per ep-eq
    assert w4.lr_scale(26) == 1.0 and w4.lr_scale(27) == 1.0 and w4.lr_scale(28) == pytest.approx(2 / 3) and w4.lr_scale(29) == pytest.approx(1 / 3)
    with pytest.raises(ValueError):
        w4.lr_scale(30)
    assert w4.phase(27) == "stable" and w4.phase(28) == "decay" and w4.h30_eligible(30) and not w4.h30_eligible(31)
    w4.decide(27, {"AP": up})
    assert w4.phase(28) == "stable" and not w4.h30_eligible(28) and w4.h30_eligible(28, "side") and w4.lr_scale(28, "side") == pytest.approx(2 / 3)
    # adopted horizons (rich / CSX): no own trigger
    wa = DT.GroupWSD(256, trigger=(), adopted=40)
    assert wa.decide(27, {})["decision"] == "extend" and wa.side["status"] == "active" and wa.decide(37, {})["decision"] == "decay"
    wc = DT.GroupWSD(256, trigger=(), adopted=60, adopted_ceiling=True)
    assert [wc.decide(d, {})["decision"] for d in (27, 37, 47)] == ["extend"] * 3 and wc.decide(57, {})["decision"] == "ceiling"
    with pytest.raises(ValueError):
        DT.GroupWSD(256, trigger=())


# ---------------------------------------------------------------------------------------------------------- mechanics (fakes)
def test_lockstep_members_see_identical_batches_and_equal_steps(tmp_path):
    """§7.1 10a: every member receives the same Batch object at every step (XM the derangement view of that batch from the
    separate generator), and every member runs the same number of steps, by phase; two runs with one seed draw one stream."""
    rec_hook = RecordBatches()
    run, _ = fake_run(str(tmp_path / "a"), fake_row("ALN3X_" + "1" * 16, limit=30), flat_ce, hooks=rec_hook)
    run.run()
    rec = run.finish()
    by_step = {}
    for step, tag, bid, xm in rec_hook.seen:
        by_step.setdefault(step, []).append((tag, bid, xm))
    assert len(by_step) == 30 and all([t for t, _, _ in v] == list(CORE5) for v in by_step.values())
    assert all(len({b for _, b, _ in v}) == 1 for v in by_step.values())                  # one Batch object per step for all
    assert all(len({json.dumps(x) for _, _, x in v if x is not None}) == 1 for v in by_step.values())   # one XM view per step
    steps = {m: rec["members"][m]["steps"] for m in CORE5}
    assert set(steps.values()) == {30} and rec["main_steps"] == 30 and rec["steps_by_phase"] == {"stable": 27, "decay": 3, "side": 0}
    assert all(rec["members"][m]["updates"] == 30 and rec["members"][m]["nonfinite_steps"] == 0 for m in CORE5)
    assert len({len(rec["members"][m]["curve"]) for m in CORE5}) == 1
    run2, _ = fake_run(str(tmp_path / "b"), fake_row("ALN3X_" + "1" * 16, limit=30), flat_ce)
    run2.run()
    assert run2.finish()["stream"]["final"] == rec["stream"]["final"]


def test_determinism_switches_for_a_cuda_device_are_set_and_recorded():
    """Review item (GPU resume exactness; CPU host, so the CUDA branch runs with a stand-in device): the unit's process switches
    on cudnn determinism, torch.use_deterministic_algorithms(True, warn_only=True), CUBLAS_WORKSPACE_CONFIG ':4096:8' when unset
    (kept when preset) and no NaN fill of uninitialised memory, and the record's determinism field says so; the CPU branch sets
    nothing. The process-wide switches are restored afterwards."""
    import torch.utils.deterministic as tud

    class CudaLike:
        type = "cuda"
    before = (torch.are_deterministic_algorithms_enabled(), torch.is_deterministic_algorithms_warn_only_enabled(),
              torch.backends.cudnn.deterministic, torch.backends.cudnn.benchmark, tud.fill_uninitialized_memory,
              os.environ.get("CUBLAS_WORKSPACE_CONFIG"))
    try:
        os.environ.pop("CUBLAS_WORKSPACE_CONFIG", None)
        d = DT.determinism(CudaLike())
        os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":16:8"
        d2 = DT.determinism(CudaLike())
    finally:
        torch.use_deterministic_algorithms(before[0], warn_only=before[1])
        torch.backends.cudnn.deterministic, torch.backends.cudnn.benchmark = before[2], before[3]
        tud.fill_uninitialized_memory = before[4]
        if before[5] is None:
            os.environ.pop("CUBLAS_WORKSPACE_CONFIG", None)
        else:
            os.environ["CUBLAS_WORKSPACE_CONFIG"] = before[5]
    assert d["deterministic_algorithms"] and d["warn_only"] and d["cudnn_deterministic"] and not d["cudnn_benchmark"]
    assert d["cublas_workspace_config"] == DT.CUBLAS_CONFIG and d["cublas_workspace_config_preset"] is None
    assert d["fill_uninitialized_memory"] is False and d["device"] == "cuda (name unavailable)"
    assert d2["cublas_workspace_config"] == d2["cublas_workspace_config_preset"] == ":16:8"
    c = DT.determinism(torch.device("cpu"))
    assert c["device_type"] == "cpu" and c["deterministic_algorithms"] is False and not torch.are_deterministic_algorithms_enabled()


def test_identical_initialisation_and_mask_free_forward_is_exact():
    """§2.6: members built from donor_seed are identical (APR's trunk and proj too); the sampler zeroes unread cells, so the
    mask-free forward the loop uses equals the masked forward exactly (value and gradient)."""
    a, b, r = MD.build_shared(C.BIOSEMI64, C.BIOSEMI64, 3401), MD.build_shared(C.BIOSEMI64, C.BIOSEMI64, 3401), \
        MD.build_shared(C.BIOSEMI64, C.BIOSEMI64, 3401, rich=True)
    assert DT._identical(a, b) and DT._identical(a, r)
    x = torch.randn(16, 64, C.L_IN)
    m = torch.rand(16, 64) > 0.3
    x = x.masked_fill(~m[:, :, None], 0).requires_grad_(False)
    u0 = a(x, layout=C.BIOSEMI64)
    u1 = b(x, layout=C.BIOSEMI64, mask=m)
    assert torch.equal(u0, u1)
    u0.sum().backward()
    u1.sum().backward()
    assert all(torch.equal(p.grad, q.grad) for p, q in zip(a.parameters(), b.parameters()))


def test_side_branch_reproduces_the_30_ep_eq_decay_exactly(runs):
    """§7.1 10c: the side branch of B (extended at 27) trains exactly the models of the fixed 30-ep-eq recipe: its states at
    ep-eq 28, 29, 30 equal those of A (limit 30) and N (no extension); B's _h30 checkpoint (the 30-ep-eq decay end, where its
    scores are best) equals A's _best; the main run of B after the first extension (constant lr) is neither h30-eligible nor in
    the side branch. The first decay step runs at the full lr (lr_t = 1e-3 (b - t) / (b - a)), so the states at 28 coincide."""
    A, B, N = runs["A"], runs["B"], runs["N"]
    for step in (28, 29, 30):
        for m in CORE5:
            assert B["val"].hashes[("side", step, m)] == A["val"].hashes[("main", step, m)] == N["val"].hashes[("main", step, m)]
            assert (B["val"].hashes[("main", step, m)] == A["val"].hashes[("main", step, m)]) == (step == 28)   # B's main: stable lr
    for m in CORE5:
        b_h30 = _enc(SEL.member_ckpt(B["dir"], B["row"]["experiment_id"], m, "h30"))
        assert _same_state(b_h30, _enc(SEL.member_ckpt(A["dir"], A["row"]["experiment_id"], m, "best")))
        info = B["rec"]["members"][m]["h30"]
        assert info["branch"] == "side" and info["ep_eq"] == 30 and info["step"] == 30
        cur = B["rec"]["members"][m]["curve"]
        assert [e["ep_eq"] for e in cur if e["branch"] == "side"] == [28, 29, 30]
        assert all(not e["h30_eligible"] and e["phase"] == "stable" for e in cur if e["branch"] == "main" and 28 <= e["ep_eq"] <= 30)
    sb = B["rec"]["side_branch"]
    assert sb["ran"] and sb["start_ep_eq"] == 27 and sb["end_ep_eq"] == 30 and B["rec"]["steps_by_phase"]["side"] == 3
    assert not A["rec"]["side_branch"]["ran"] and not N["rec"]["side_branch"]["ran"]


def test_group_trigger_extends_whole_group_and_xm_never_triggers(runs):
    """§7.1 10b on whole runs: B extends 30 -> 40 -> 50 -> 60 for all members; N decays at 30; X (only XM improving) decays at
    30; every member of a group ends at the same horizon and step count."""
    B, N, X = runs["B"]["rec"], runs["N"]["rec"], runs["X"]["rec"]
    assert [e["decision"] for e in B["trigger_log"]] == ["extend", "extend", "extend", "ceiling"]
    assert [e["ep_eq"] for e in B["trigger_log"]] == [27, 37, 47, 57] and B["horizon_ep_eq"] == 60
    assert N["horizon_ep_eq"] == 30 and [e["decision"] for e in N["trigger_log"]] == ["decay"]
    assert X["horizon_ep_eq"] == 30 and not X["trigger_log"][0]["fires"] and "XM" not in X["trigger_log"][0]["members"]
    for rec, n in ((B, 60), (N, 30), (X, 30)):
        assert {rec["members"][m]["steps"] for m in CORE5} == {n} and rec["main_steps"] == n
    for e in B["trigger_log"] + N["trigger_log"]:                       # the log agrees with the rule it states
        assert all(v["improving"] == (v["best_index"] >= v["last_window_start"]) for v in e["members"].values())


def test_flat_curve_does_not_extend_the_group(tmp_path):
    """Review item (ties): a collapsed contract member (the same CE_dev at every validation) with every other member worsening
    from its first validation does not improve, so the group decays at 30: no extension, no ceiling flag, no retained state and
    therefore no registered continuation."""
    row = fake_row("ALN3X_" + "f1" * 8, limit=60)
    run, _ = fake_run(str(tmp_path / "f"), row, collapsed_ce)
    run.run()
    rec = run.finish()
    assert rec["horizon_ep_eq"] == 30 and rec["ceiling_reached_while_improving"] is False and not rec["side_branch"]["ran"]
    (e,) = rec["trigger_log"]
    assert e["decision"] == "decay" and not e["fires"] and e["members"]["AP"] == {"improving": False, "n_stable": 27, "best_index": 0,
                                                                                  "best_ce": math.log2(9), "last_window_start": 24}
    assert rec["retained_states"] == [] and not any("stable" in f for f in os.listdir(str(tmp_path / "f" / "ckpt")))


def test_compute_limit_sets_the_flag_and_retains_the_stable_states(runs):
    """§7.1 10d: B reaches its limit 60 while the trigger fires at 57: it decays to 60, sets ceiling_reached_while_improving and
    keeps <gid>_m<M>_stable57.pt for every member (select.retained_states names them); N keeps none; A (limit 30) keeps
    stable27."""
    B, N, A = runs["B"], runs["N"], runs["A"]
    assert B["rec"]["ceiling_reached_while_improving"] is True and N["rec"]["ceiling_reached_while_improving"] is False
    files = SEL.retained_states(B["dir"], B["row"])
    assert [os.path.basename(p) for p in files] == [f"{B['row']['experiment_id']}_m{m}_stable57.pt" for m in CORE5]
    assert sorted(os.path.relpath(p, B["dir"]) for p in files) == sorted(B["rec"]["retained_states"])
    for m, p in zip(CORE5, files):
        st = torch.load(p, map_location="cpu", weights_only=True)
        assert st["format"] == DT.STABLE_FORMAT and st["member"] == m and st["ep_eq"] == 57 and st["group_state"]["step"] == 57
        assert st["group_state"]["wsd_pre_decision"]["H"] == 60 and not st["group_state"]["wsd_pre_decision"]["ceiling"]
        assert B["val"].hashes[("main", 57, m)] == _sha_state(_load_into(st["enc"]))
    assert not any("stable" in f for f in os.listdir(os.path.join(N["dir"], "ckpt")))
    assert all(os.path.exists(p) for p in SEL.retained_states(A["dir"], A["row"])) and A["rec"]["ceiling_reached_while_improving"]


def _load_into(state):
    e = TinyEncoder()
    e.load_state_dict(state)
    return e


def test_continuation_follows_the_larger_limit_trajectory(runs, tmp_path):
    """A continuation version (limit 70, continuation_of B) resumes from B's retained stable states and re-decides at 57 under
    its own limit: every main-run state from 58 on, every curve entry and the final checkpoints equal those of D, the same
    group run with limit 70 from the start."""
    B, D = runs["B"], runs["D"]
    out = str(tmp_path / "cont")
    os.makedirs(os.path.join(out, "ckpt"))
    for f in os.listdir(os.path.join(B["dir"], "ckpt")):                 # the continuation reads the source's files from `out`
        os.symlink(os.path.join(B["dir"], "ckpt", f), os.path.join(out, "ckpt", f))
    row = fake_row("ALN3X_" + "c" * 16, limit=70, continuation_of=B["row"]["experiment_id"])
    inherit = {"gid": B["row"]["experiment_id"], "files": dict(zip(CORE5, SEL.retained_states(out, B["row"]))), "code_hash": None}
    run, val = fake_run(out, row, improving_ce, inherit=inherit)
    run.run()
    rec = run.finish()
    assert rec["inherited"]["from"] == B["row"]["experiment_id"] and rec["inherited"]["ep_eq"] == 57
    assert rec["horizon_ep_eq"] == D["rec"]["horizon_ep_eq"] == 70 and rec["ceiling_reached_while_improving"]
    assert [e["decision"] for e in rec["trigger_log"]] == [e["decision"] for e in D["rec"]["trigger_log"]]
    for m in CORE5:
        for step in range(58, 71):
            assert val.hashes[("main", step, m)] == D["val"].hashes[("main", step, m)]
        a, b = rec["members"][m]["curve"], D["rec"]["members"][m]["curve"]
        assert [(_strip(x)["ep_eq"], x["branch"], x["dev"]["ce_bits"]) for x in a] == [(x["ep_eq"], x["branch"], x["dev"]["ce_bits"]) for x in b]
        for kind in DT.KINDS:
            assert _same_state(_enc(SEL.member_ckpt(out, row["experiment_id"], m, kind)),
                               _enc(SEL.member_ckpt(D["dir"], D["row"]["experiment_id"], m, kind)))
        assert rec["members"][m]["steps"] == D["rec"]["members"][m]["steps"] == 70
    assert all(os.path.exists(p) for p in SEL.retained_states(out, row))   # stable67 of the continuation itself
    # the record's counters are cumulative over the inherited trajectory; the split says which part this version ran
    ci, ct = rec["compute_inherited"], rec["compute_this_run"]
    assert ci["from"] == B["row"]["experiment_id"] and (ci["main_steps"], ci["side_steps"], ci["n_validations"]) == (57, 3, 60)
    assert (ct["main_steps"], ct["side_steps"], ct["n_validations"]) == (13, 0, 13) and rec["main_steps"] == 70
    assert ct["member_steps"] == {m: {"main": 13, "side": 0} for m in CORE5} and ci["member_steps"]["AP"] == {"main": 57, "side": 3}
    assert ct["steps_by_phase"] == {"stable": 10, "decay": 3, "side": 0}
    assert D["rec"]["compute_inherited"] is None and D["rec"]["compute_this_run"]["main_steps"] == 70


@pytest.mark.parametrize("branch,step", [("side", 27), ("side", 29), ("main", 27)])
def test_resume_gives_identical_outputs(runs, tmp_path, branch, step):
    """§7.1 10e: an interruption right after the resume save at (branch, step) -- at the side branch's start (the stable
    snapshot is then only in <gid>_wsd_resume.pt), in its middle, right after it ended (the snapshot restored and its file
    removed) or later -- and a restart from the files give the uninterrupted run's batches (stream hash), curves and
    checkpoints. finish() leaves <gid>_resume.pt (marked done) for the caller: a rerun then trains nothing and gives the same
    record fields; remove_resume_files deletes both resume files (a resume after a later main-run save: the real-stack test)."""
    B = runs["B"]
    out = str(tmp_path / "r")
    row = B["row"]
    run, val = fake_run(out, row, improving_ce, hooks=StopAt(branch, step))
    with pytest.raises(Interrupt):
        run.run()
    gid = row["experiment_id"]
    ck = os.path.join(out, "ckpt")
    assert os.path.exists(os.path.join(ck, f"{gid}_resume.pt"))
    assert os.path.exists(os.path.join(ck, f"{gid}_wsd_resume.pt")) == (branch == "side")
    run2, val2 = fake_run(out, row, improving_ce)
    run2.run()
    rec = run2.finish()
    assert rec["stream"]["final"] == B["rec"]["stream"]["final"] and rec["stream"]["hash_log"] == B["rec"]["stream"]["hash_log"]
    assert len(rec["resumed"]) == 1
    for m in CORE5:
        a, b = rec["members"][m], B["rec"]["members"][m]
        assert a["curve"] == b["curve"]
        assert {k: a[k] for k in ("best", "h30", "gainsel", "steps", "updates")} == {k: b[k] for k in ("best", "h30", "gainsel", "steps", "updates")}
        for kind in DT.KINDS:
            assert _same_state(_enc(SEL.member_ckpt(out, gid, m, kind)), _enc(SEL.member_ckpt(B["dir"], gid, m, kind)))
    for k in val2.hashes:
        assert val2.hashes[k] == B["val"].hashes[k]
    assert sorted(f for f in os.listdir(ck) if "resume" in f) == [f"{gid}_resume.pt"]          # kept until the record exists
    run3, val3 = fake_run(out, row, improving_ce)                     # e.g. the record write failed: the retry only finishes
    run3.run()
    rec3 = run3.finish()
    assert val3.calls == 0 and len(rec3["resumed"]) == 2 and rec3["stream"] == rec["stream"]
    assert all(rec3["members"][m]["curve"] == rec["members"][m]["curve"] and rec3["members"][m]["best"] == rec["members"][m]["best"]
               for m in CORE5)
    assert DT.remove_resume_files(out, gid) == [f"{gid}_resume.pt"]
    assert not any(f.endswith(("_resume.pt", "_resume.pt.tmp")) for f in os.listdir(ck))


def test_files_written_before_an_interrupted_save_follow_the_resumed_record(tmp_path):
    """Review item (resume consistency): an attempt is pre-empted after the validation at 27 wrote _best / _h30 (a new minimum)
    and the stable27 states (ceiling at the limit 30) but before its resume save; the replay of that validation is not bit-exact
    (scripted: a worse score, as a CUDA replay may give) and decides 'decay'. The resume rewrites every recorded best checkpoint
    from the resume file and drops the stale stable files, so each checkpoint holds the state its record entry names and no
    stable state is left beside a record without a ceiling."""
    attempt = {"n": 0}

    def script(m, branch, step):
        if step == 27 and attempt["n"] == 0:
            return 1.0, 0.0                                  # first attempt: a new minimum at 27, inside the last 3 -> ceiling
        return 5.0 + 0.01 * abs(step - 10), 0.0              # otherwise the best is at 10: no improvement at 27
    out = str(tmp_path / "p")
    row = fake_row("ALN3X_" + "e7" * 8, limit=30)
    gid = row["experiment_id"]
    run1, val1 = fake_run(out, row, script, hooks=StopBeforeSave("main", 27))
    with pytest.raises(Interrupt):
        run1.run()
    ck = os.path.join(out, "ckpt")
    stale = SEL.retained_states(out, row)
    assert all(os.path.exists(p) for p in stale) and run1.best["AP"]["best"]["info"]["ep_eq"] == 27
    assert _sha_state(_load_into(_enc(SEL.member_ckpt(out, gid, "AP", "best")))) == val1.hashes[("main", 27, "AP")]
    attempt["n"] = 1
    run2, val2 = fake_run(out, row, script)
    run2.run()
    rec = run2.finish()
    assert rec["ceiling_reached_while_improving"] is False and rec["retained_states"] == [] and not any(os.path.exists(p) for p in stale)
    assert [e["decision"] for e in rec["trigger_log"]] == ["decay"] and len(rec["resumed"]) == 1
    hashes = {**val1.hashes, **val2.hashes}                     # CPU: the replayed steps have the same weights
    for m in CORE5:
        for kind in ("best", "h30"):
            info = rec["members"][m][kind]
            assert info["ep_eq"] == 10 and info["branch"] == "main"
            assert _sha_state(_load_into(_enc(SEL.member_ckpt(out, gid, m, kind)))) == hashes[("main", 10, m)]
    assert not any(f.endswith(".tmp") for f in os.listdir(ck))


def test_adopted_horizon_side_branch_ceiling_and_stream_check(runs, tmp_path):
    """§7.1 10f: a CSX group (APC, XPC) adopts H* = 40 -- its own scores keep improving, which would extend a core group to its
    limit, but they never drive its horizon --, runs the 27 -> 30 side branch (its _h30 models) and decays at 37; with an adopted
    ceiling (H* = 60, flag) it retains stable57 and sets the flag. A group checking its stream against a core record passes on
    the core's hash log and raises StreamMismatch on a tampered one."""
    row = fake_row("ALN3X_" + "e" * 16, fam=SEL.CSX_DONOR, horizon_from="ALN3X_" + "b" * 16)
    run, _ = fake_run(str(tmp_path / "x"), row, improving_ce, adopted=40)
    run.run()
    rec = run.finish()
    assert rec["horizon_ep_eq"] == 40 and [e["decision"] for e in rec["trigger_log"]] == ["extend", "decay"]
    assert rec["trigger_log"][0]["members"] is None and rec["side_branch"]["ran"]
    assert all(rec["members"][m]["h30"]["branch"] == "side" and rec["members"][m]["steps"] == 40 for m in ("APC", "XPC"))
    run, _ = fake_run(str(tmp_path / "y"), row, flat_ce, adopted=60, adopted_ceiling=True)
    run.run()
    rec = run.finish()
    assert rec["ceiling_reached_while_improving"] and rec["horizon_ep_eq"] == 60
    assert all(os.path.exists(p) for p in SEL.retained_states(str(tmp_path / "y"), row))
    # stream check (rich groups, §2.15): the reference is the core run's main-stream hash log and final hash
    B = runs["B"]["rec"]
    hor = {"gid": "ALN3X_" + "b" * 16, "hash_log": B["stream"]["hash_log"], "final": B["stream"]["final"],
           "final_step": B["stream"]["final_step"], "check_stream": True}
    run, _ = fake_run(str(tmp_path / "z"), row, flat_ce, adopted=60, adopted_ceiling=True, horizon=hor)
    run.run()
    rec = run.finish()
    assert rec["stream"]["core_check"]["final"] == "equal" and rec["stream"]["core_check"]["checked"] >= len(B["stream"]["hash_log"])
    bad = copy.deepcopy(hor)
    bad["hash_log"][3][1] = "0" * 64
    run, _ = fake_run(str(tmp_path / "w"), row, flat_ce, adopted=60, adopted_ceiling=True, horizon=bad)
    with pytest.raises(DT.StreamMismatch):
        run.run()


def test_nonfinite_member_skips_update_but_keeps_equal_steps(tmp_path, monkeypatch):
    """§2.10: a member whose loss is non-finite skips that step's update (counted in nonfinite_steps); its step count still
    advances with the group and the other members are unaffected."""
    row = fake_row("ALN3X_" + "9" * 16, limit=30, members=["AP", "XP"])
    run, _ = fake_run(str(tmp_path / "n"), row, flat_ce)
    orig = run.members["XP"].loss
    calls = {"n": 0}

    def loss(*a):
        calls["n"] += 1
        out = orig(*a)
        return (out[0] * float("nan"), out[1]) if calls["n"] % 3 == 0 else out
    monkeypatch.setattr(run.members["XP"], "loss", loss)
    run.run()
    rec = run.finish()
    assert rec["members"]["XP"]["nonfinite_steps"] == 10 and rec["members"]["XP"]["updates"] == 20
    assert rec["members"]["AP"]["nonfinite_steps"] == 0 and rec["members"]["AP"]["steps"] == rec["members"]["XP"]["steps"] == 30


def test_checkpoint_naming_and_contents(runs):
    """§2.10 file names through select.py: <gid>_m<M>_{best,gainsel_best,h30_best}.pt for every member, _stable57.pt at the
    ceiling; files load with weights_only=True and hold the encoder under 'enc' with its validation; the offload regex of
    ckpt_offload (design §6.5) owns every _best.pt by <gid> and never matches a stable or resume file."""
    import re
    rx = re.compile(r"^(ALN3X?_[0-9a-f]{16})(?:_[A-Za-z0-9]+)*_best\.pt$")
    B = runs["B"]
    gid = B["row"]["experiment_id"]
    files = sorted(os.listdir(os.path.join(B["dir"], "ckpt")))
    want = sorted([os.path.basename(SEL.member_ckpt(B["dir"], gid, m, k)) for m in CORE5 for k in DT.KINDS] +
                  [os.path.basename(p) for p in SEL.retained_states(B["dir"], B["row"])])
    assert files == want
    for f in files:
        mt = rx.match(f)
        assert (mt is not None and mt.group(1) == gid) == f.endswith("_best.pt")
    for m in CORE5:
        lam = {"J1": 1.0, "J025": 0.25}.get(m)                 # None for every non-joint member (records and checkpoints)
        assert B["rec"]["members"][m]["lambda"] == lam
        for k in DT.KINDS:
            ck = torch.load(SEL.member_ckpt(B["dir"], gid, m, k), map_location="cpu", weights_only=True)
            assert ck["format"] == DT.CKPT_FORMAT and ck["member"] == m and ck["kind"] == k and set(ck["enc"]) == {"lin.weight", "lin.bias"}
            assert ck["validation"] == {kk: v for kk, v in B["rec"]["members"][m][k].items() if kk not in ("bridge_cal_ce", "bridge_cal")}
            assert set(ck["head"]) == {"std.mu", "std.sd", "P"} and ck["sigma"] == {"sigma_u": 1.0, "sigma_v": 1.0} and ck["lambda"] == lam
    # §7.1 item 11: checkpoints holding the same validation are recorded as identical (B: best = gainsel = main 60, h30 = side
    # 30; N: best = h30 = main 5, gainsel = main 9)
    assert all(B["rec"]["members"][m]["identical"] == {"best_h30": False, "best_gainsel": True, "h30_gainsel": False} for m in CORE5)
    assert all(runs["N"]["rec"]["members"][m]["identical"] == {"best_h30": True, "best_gainsel": False, "h30_gainsel": False}
               for m in CORE5)
    # finish() leaves the group's resume file for the caller (run_donor deletes it after the record): the side branch's
    # snapshot file is already gone when the branch ended
    assert B["resume_left"] == [f"{gid}_resume.pt"] and B["removed"] == [f"{gid}_resume.pt"]


# ---------------------------------------------------------------------------------------------------------- scores
def test_dev_scores_hand_cases_and_the_unified_score():
    """§7.1 11: calibrated_ce equals the closed form on hand cases; S(q, c) is the mean over dimensions of the per-segment
    Pearson r over ticks (np.corrcoef), the gain uses o(q), and r_own equals rich.rich_readout's r_bar under the same §2.10
    ridge rule."""
    ce, tau, rel = DT.calibrated_ce(np.array([[1.0, 0.0], [0.0, 1.0]]), [0, 1])
    assert ce == pytest.approx(math.log2(1 + math.exp(-1 / (1e-3 * 0.5))), abs=1e-12) and rel == pytest.approx(1e-3)
    ce, tau, rel = DT.calibrated_ce(np.array([[1.0, 0.0], [1.0, 0.0]]), [0, 1])
    x = 1 / (100 * 0.5)
    assert ce == pytest.approx(0.5 * math.log2((1 + math.exp(-x)) * (1 + math.exp(x))), abs=1e-12) and rel == pytest.approx(100.0)
    rng = np.random.default_rng(3)
    T, d, D = 250, 32, 8
    Uf, Yf = rng.standard_normal((6, T, d)), rng.standard_normal((6, T, D))
    Yf += Uf[..., :D]                                                   # a learnable linear relation
    Uq, Yc = rng.standard_normal((5, T, d)), rng.standard_normal((4, T, D))
    own, other = np.array([0, 1, 2, 3, 0]), np.array([1, -1, 3, 0, 2])
    sc = DT.dev_scores(Uf, Yf, Uq, Yc, own, other)
    X = Uf.reshape(-1, d)
    alpha = 1e-2 * float((X * X).sum(0).mean())
    X1 = np.c_[X, np.ones(len(X))]
    R = alpha * np.eye(d + 1)
    R[-1, -1] = 0
    Bm = np.linalg.solve(X1.T @ X1 + R, X1.T @ Yf.reshape(-1, D))          # ev1._ridge with one alpha (intercept unpenalised)
    P = (np.c_[Uq.reshape(-1, d), np.ones(5 * T)] @ Bm).reshape(5, T, D)
    S = np.array([[np.mean([np.corrcoef(P[q, :, k], Yc[c, :, k])[0, 1] for k in range(D)]) for c in range(4)] for q in range(5)])
    ce_ref = DT.calibrated_ce(S, own)[0]
    assert sc["ce_bits"] == pytest.approx(ce_ref, abs=1e-9) and sc["alpha"] == pytest.approx(alpha)
    assert sc["r_own"] == pytest.approx(S[np.arange(5), own].mean(), abs=1e-9) and sc["n_cand"] == 4 and sc["n_gain"] == 4
    ok = other >= 0
    assert sc["gain"] == pytest.approx((S[np.arange(5), own] - S[np.arange(5), np.maximum(other, 0)])[ok].mean(), abs=1e-9)
    from auditory_alignment_v3.prior33 import rich as R_
    rr = R_.rich_readout(Uf, {"env": Yf}, Uq, {"env": Yc[own]})
    assert rr["env"]["r_bar"] == pytest.approx(sc["r_own"], abs=1e-9)
    bad = DT.dev_scores(Uf, Yf, Uq * np.nan, Yc, own, other)
    assert bad["nonfinite"] and math.isnan(bad["ce_bits"])
    zero = DT.dev_scores(Uf * 0, Yf, Uq, Yc, own, other)                     # all-zero outputs: no readout, never a best checkpoint
    assert zero["nonfinite"] and math.isnan(zero["ce_bits"]) and DT._ce_key(zero["ce_bits"]) == math.inf
    with pytest.raises(ValueError):
        DT.dev_scores(Uf, Yf, Uq, Yc, np.array([0, 1, 2, 3, 4]))


def test_lambda_rule_and_gain_rule_recorded():
    """§2.9: joint_choice (select.joint_choice: lower CE_dev of _best.pt, ties < 1e-4 bits to J1) and the gain-rule sensitivity
    (higher gain of _gainsel_best.pt, by >= 1e-4, ties to J1) as run_donor records them; select.check_group_record accepts it."""
    def rec(ce1, ce2, g1, g2):
        row = fake_row("ALN3X_" + "7" * 16, lambda_rule=SEL.LAMBDA_RULE)
        r = {"experiment_id": row["experiment_id"], "row": row,
             "members": {m: {"best": {"ce_dev": 5.0}, "gainsel": {"gain": 0.1}} for m in CORE5}}
        r["members"]["J1"] = {"best": {"ce_dev": ce1}, "gainsel": {"gain": g1}}
        r["members"]["J025"] = {"best": {"ce_dev": ce2}, "gainsel": {"gain": g2}}
        r["joint_choice"], r["gain_rule"] = SEL.joint_choice(r), RD.gain_rule(r)
        return r
    r = rec(5.0, 4.9, 0.10, 0.20)
    assert r["joint_choice"]["member"] == "J025" and r["gain_rule"]["member"] == "J025" and SEL.check_group_record(r) == "J025"
    r = rec(5.0, 5.0 - 5e-5, 0.10, 0.10 + 5e-5)
    assert r["joint_choice"]["member"] == "J1" and r["gain_rule"]["member"] == "J1" and SEL.check_group_record(r) == "J1"
    r = rec(4.0, 5.0, 0.3, 0.2)
    assert r["joint_choice"]["member"] == "J1" and r["gain_rule"]["member"] == "J1"
    r = rec(float("nan"), 5.0, float("nan"), 0.2)
    assert r["joint_choice"]["member"] == "J025" and r["gain_rule"]["member"] == "J025"
    assert r["gain_rule"]["rule"] == DT.GAIN_RULE and r["joint_choice"]["rule"] == SEL.LAMBDA_RULE


# ---------------------------------------------------------------------------------------------------------- real stack (scale 4)
@pytest.fixture(scope="module")
def fx4(tmp_path_factory):
    return make_synthetic_manifest(str(tmp_path_factory.mktemp("m5_fx4")), scale=4)


@pytest.fixture(scope="module")
def man4(fx4):
    return V.open_manifest(fx4["manifest_path"], fx4["manifest_sha256"])


def _small_sets(man, n_fit=6, n_dev=8, n_cal=8):
    """The fixed sets with the first n fit segments and dev / bridge_cal queries (candidates, own and o(q) unchanged): shorter CPU
    validations."""
    ss = _ORIG_SETS(man)
    dev, cal = ss["dev"], ss["bridge_cal"]
    kd, kc = np.arange(min(n_dev, len(dev["queries"]))), np.arange(min(n_cal, len(cal["queries"])))
    return {**ss, "fit": ss["fit"].take(np.arange(min(n_fit, len(ss["fit"])))), "dev": {"queries": dev["queries"].take(kd), "candidates": dev["candidates"], "own": dev["own"][kd], "other": dev["other"][kd]},
            "bridge_cal": {**cal, "queries": cal["queries"].take(kc), "own": cal["own"][kc], "fold": cal["fold"][kc]}}


@pytest.fixture
def small_sets(monkeypatch):
    monkeypatch.setattr(SM, "selection_sets", _small_sets)


def _registry_entries(mp):
    """The §6.3 registry entries with the select.py delta (not yet applied live) and a CPU device name for core.new_record."""
    files = [("auditory_alignment_v3", "core.py"), ("auditory_alignment_v3", "local_train.py")] + \
            [("auditory_alignment_v3/prior33", f) for f in ("contract.py", "views.py", "model.py", "losses.py", "sampler.py", "select.py",
                                                             "donor_train.py", "run_donor.py")]
    mp.setitem(core.FAMILY_CODE, "prior33_donor", files)
    mp.setitem(core.FAMILY_CODE, "prior33_rich_donor", files + [("auditory_alignment_v3/prior33", "rich.py")])
    for fam in (SEL.DONOR, SEL.CSX_DONOR):
        mp.setitem(core.FAMILY_GROUP, fam, "prior33_donor")
    mp.setitem(core.FAMILY_GROUP, SEL.RICH_DONOR, "prior33_rich_donor")
    mp.setattr(torch.cuda, "get_device_name", lambda *a, **k: "cpu (test)")


@pytest.fixture
def registry(monkeypatch):
    _registry_entries(monkeypatch)


def real_row(fx, man, target="fau", fam=SEL.DONOR, objective="NCE", seed=3401, members=None, limit=60, **kw):
    b = man["budget"]
    spec = {"logical_family": "ALN32_PUBLIC_AUDIO_PRIOR", "card": "E34_PUBLIC_PRIOR", "execution_contract": C.CONTRACT,
            "manifest_sha256": fx["manifest_sha256"], "stage": "donor_group",
            "block": {SEL.DONOR: "core", SEL.RICH_DONOR: "rich", SEL.CSX_DONOR: "csx"}[fam], "seed_scope": "breadth",
            "donor_seed": seed, "sampler_seed": seed, "target_seed": None, "architecture": "lag_local_tokens",
            "channel_map": "name_indexed_signed_v1", "window": "full", "input_samples": [0, 38], "fs": 64, "projection_dim": 32,
            "objective": objective, "target": "envelope", "target_contract": man["target_contract"],
            "members": list(members or SEL.GROUP_MEMBERS[fam]), "donor_set": target, "batch": dict(DT.BATCH),
            "budget": {"epoch_equivalents": 30, "anchors_per_ep_eq": b["anchors_per_ep_eq"], "steps0": b["S0"],
                       "continuation": f"group_wsd_any_last3_ext10_limit{limit}_v1"},
            "optimizer": dict(DT.OPTIMIZER), "temperature": 0.1, "bandwidth_multiplier": 1.0, "selection": dict(DT.SELECTION),
            "lambda_rule": SEL.LAMBDA_RULE, "montage_augmentation": DT.MONTAGE_AUG, "control": DT.CONTROL, **kw}
    body = {"family": fam, "dataset": target, "subject_fold": None, "content_fold": None, "seed": seed, "spec": spec}
    gid = "ALN3X_" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]
    return {"experiment_id": gid, "family_id": fam, "dataset": target, "subject_fold": None, "content_fold": None, "seed": seed,
            "logical_dependencies": ["frozen_manifest"] + [kw[k] for k in ("horizon_from", "continuation_of") if k in kw], "spec": spec}


def _fake_core_record(out, row, H=30, ceiling=False, truncated=None):
    """A complete core-group record (as run_donor writes it) for the rich / CSX upstream checks."""
    rec = {"experiment_id": row["experiment_id"], "row": row, "status": "complete", "code_hash": "c" * 16, "horizon_ep_eq": H,
           "ceiling_reached_while_improving": ceiling, "truncated": truncated,
           "stream": {"hash_log": [], "final": "0" * 64, "final_step": 10 ** 9},
           "members": {m: {"best": {"ce_dev": 1.0}} for m in SEL.group_members(row)}}
    os.makedirs(os.path.join(out, "units"), exist_ok=True)
    with open(SEL.record_path(out, row["experiment_id"]), "w") as f:
        json.dump(rec, f)
    return rec


@pytest.fixture(scope="module")
def core_run(fx4, man4, tmp_path_factory):
    """A tiny real core run (target fau, NCE, all five members, max_steps 3) through run_donor.run."""
    mp = pytest.MonkeyPatch()
    try:
        mp.setattr(SM, "selection_sets", _small_sets)
        _registry_entries(mp)
        out = str(tmp_path_factory.mktemp("m5_core"))
        row = real_row(fx4, man4)
        RD.run(row, out, epochs=3, manifest=man4, device="cpu")
        with open(SEL.record_path(out, row["experiment_id"])) as f:
            text = f.read()
        rec = json.loads(text)
    finally:
        mp.undo()
    return {"out": out, "row": row, "rec": rec, "text": text}


def test_tiny_real_run_writes_a_valid_record(core_run, man4):
    """A tiny real-like run (scale-4 fixture, CPU, max_steps 3) through run_donor.run: a complete record with the M11 fields
    (members[M].{best, h30, gainsel}.{ce_dev, gain, bridge_cal_ce, ep_eq}, joint_choice, gain_rule, horizon_ep_eq,
    ceiling_reached_while_improving), accepted by select.check_group_record and select.member_of; every checkpoint named by
    select.py and strictly loadable by model.build_target_encoder (tensor map new / missing empty); no resume file left."""
    out, row, rec = core_run["out"], core_run["row"], core_run["rec"]
    gid = row["experiment_id"]
    assert rec["status"] == "complete" and rec["code_group"] == "prior33_donor" and rec["selection_level"] == DT.SELECTION_LEVEL
    assert rec["target_contract"] == man4["target_contract"] and rec["manifest_sha256"] == man4.sha256 and rec["mode"] == "donor_training"
    for m in CORE5:
        e = rec["members"][m]
        for kind in ("best", "h30", "gainsel"):
            assert all(isinstance(e[kind][f], (int, float)) for f in ("ce_dev", "gain", "bridge_cal_ce", "ep_eq"))
        assert e["steps"] == 3 and e["nonfinite_steps"] == 0 and len(e["curve"]) == 1 and e["sigma"]["sigma_u"] > 0
    assert rec["truncated"]["max_steps"] == 3 and isinstance(rec["horizon_ep_eq"], float) and rec["ceiling_reached_while_improving"] is False
    assert rec["joint_choice"] == SEL.joint_choice(rec) and rec["gain_rule"]["member"] in ("J1", "J025")
    assert rec["record_check"] == {"ok": True, "joint_member": rec["joint_choice"]["member"]}
    assert SEL.check_group_record(rec, row) == rec["joint_choice"]["member"]
    tgt = {"experiment_id": "ALN3X_" + "t" * 16, "family_id": SEL.TARGET, "dataset": "fau", "spec": {"stage": "target", "init": "donor",
           "donor_group": gid, "member": "J*", "target_seed": 3401}, "seed": 3401}
    assert SEL.member_of(tgt, rec) == rec["joint_choice"]["member"]
    names = sorted(os.listdir(os.path.join(out, "ckpt")))
    assert names == sorted(os.path.basename(SEL.member_ckpt(out, gid, m, k)) for m in CORE5 for k in DT.KINDS)
    for m in CORE5:
        state = torch.load(SEL.member_ckpt(out, gid, m, "best"), map_location="cpu", weights_only=True)
        enc = MD.build_target_encoder({**tgt, "spec": {**tgt["spec"], "member": m}}, man4["montages"]["fau"], man4, state)
        assert enc.tensor_map["new"] == [] and enc.tensor_map["missing"] == [] and enc.tensor_map["mismatched"] == []
    assert rec["xm"]["main"]["batches"] == 3 and rec["sampler"]["strata"] == ["sparrkulee", "dtu", "federici"]
    assert rec["flop_proxy"]["forward_flops_per_window"] > 0 and rec["score_sets"]["dev_queries"] == 8
    assert rec["members"]["AP"]["curve"][0]["diag"]["u_eff_rank"] > 1 and "dev_cs_true_nats" in rec["members"]["AP"]["curve"][0]["diag"]
    # strict JSON (no NaN / Infinity tokens; the ALN3 records are archived byte-identically); bridge_cal has no o(q), so no gain
    assert _strict_json(core_run["text"]) == rec and rec["nonfinite_to_null"]["count"] == 0
    for m in CORE5:
        e = rec["members"][m]
        for kind in DT.KINDS:
            assert "gain" not in e[kind]["bridge_cal"] and "n_gain" not in e[kind]["bridge_cal"]
            assert e[kind]["bridge_cal_ce"] == e[kind]["bridge_cal"]["ce_bits"] and math.isfinite(e[kind]["gain"])
        assert e["lambda"] == {"J1": 1.0, "J025": 0.25}.get(m) and e["identical"] == {"best_h30": True, "best_gainsel": True,
                                                                                       "h30_gainsel": True}
    assert rec["resume_cleanup"].startswith("the caller") and rec["determinism"]["device_type"] == "cpu"


def test_record_shows_the_joint_extra_compute(core_run):
    """EXECUTION §7 (joint 同时算两种损失，报告实际GPU时间/FLOPs代理), design §2.9: synchronised per-member step seconds by phase, a
    per-member FLOP proxy (encoder forward + backward per window x 512 + the member's own loss terms, per stratum), the realised
    group steps per stratum, and the joint members' extra compute against AP and XP (J1 and J025 count the same FLOPs; XM counts
    XP's: the same term on the deranged view)."""
    rec = core_run["rec"]
    mt = rec["timing"]["member_train_s"]
    assert set(mt) == set(CORE5) and all(sum(mt[m].values()) > 0 and mt[m]["side"] == 0 for m in CORE5)
    fp = rec["flop_proxy"]
    per, enc, loss = fp["flops_per_step"], fp["encoder_fwd_bwd_per_window"], fp["loss_fwd_bwd"]
    assert set(enc) == {"shared"} and "error" not in fp
    for s in rec["sampler"]["strata"]:
        assert per["J1"][s] == per["J025"][s] > per["AP"][s] > 0 and per["XM"][s] == per["XP"][s] > 0
        assert all(per[m][s] == 2 * SM.N_ROWS * enc["shared"][s] + loss[m][s] for m in CORE5)
        assert loss["J1"][s] > max(loss["AP"][s], loss["XP"][s]) > 0
    n = fp["steps_by_stratum"]
    assert sum(n.values()) == 3 == rec["main_steps"] and set(n) <= set(rec["sampler"]["strata"])
    assert all(fp["train_flops_proxy"][m] == sum(c * per[m][s] for s, c in n.items()) for m in CORE5)
    assert fp["train_flops_proxy_total"] == pytest.approx(sum(fp["train_flops_proxy"].values()))
    assert fp["validation_flops_proxy"] == fp["forward_flops_per_window"] * rec["timing"]["validation_windows"] > 0
    je = rec["joint_extra_compute"]
    assert je["second_lambda_member"] == "J025" and je["member_steps"] == {"J1": 3, "J025": 3}
    for j in ("J1", "J025"):
        assert je["extra"][j]["vs_AP"]["train_flops_proxy"] == fp["train_flops_proxy"][j] - fp["train_flops_proxy"]["AP"] > 0
        assert je["extra"][j]["vs_XP"]["train_s"] == pytest.approx(je["member_train_s"][j] - je["member_train_s"]["XP"])
    ct = rec["compute_this_run"]
    assert rec["compute_inherited"] is None and ct["main_steps"] == 3 and ct["train_flops_proxy"] == fp["train_flops_proxy"]


def _manifest_with_budget(man, anchors):
    """A copy of the opened manifest whose budget declares another ep-eq size (path, sha256 and root unchanged): a short real-stack
    schedule for the CPU tests."""
    b = {**man["budget"], "anchors_per_ep_eq": int(anchors), "S0": DT.steps_at(30, int(anchors))}
    return V.Manifest({**man, "budget": b}, man.path, man.sha256, man.root)


def test_real_resume_and_lockstep_on_the_sampler(fx4, man4, tmp_path, small_sets):
    """Resume on the real stack (manifest copy: 1 ep-eq = 2 steps): a run interrupted after its resume save at ep-eq 2 and
    restarted gives the uninterrupted run's curves, checkpoints and stream; on the real DonorSampler every member sees the same
    Batch object and XM the derangement view of it (view-2 rows a permutation of the batch's view-2 rows, X1's keys)."""
    m2 = _manifest_with_budget(man4, 512)
    row = real_row(fx4, m2, members=["AP", "XM"])
    gid = row["experiment_id"]
    xm_rows = []

    class Check(RecordBatches):
        def on_member(self, tag, batch, xm):
            super().on_member(tag, batch, xm)
            if tag == "XM":
                assert torch.equal(xm.keys, batch.keys) and torch.equal(xm.x2, batch.x2[xm.rows])
                xm_rows.append(sorted(xm.rows.tolist()) == list(range(SM.N_ROWS)))
    hook = Check()
    a, b = str(tmp_path / "a"), str(tmp_path / "b")
    for d in (a, b):
        os.makedirs(os.path.join(d, "ckpt"))
    la = DT.train_donor_group(row, m2, "cpu", os.path.join(a, "ckpt", gid), {}, max_steps=5, _hooks=hook)
    by = {}
    for step, tag, bid, _ in hook.seen:
        by.setdefault(step, set()).add(bid)
    assert len(by) == 5 and all(len(v) == 1 for v in by.values()) and all(xm_rows) and len(xm_rows) == 5
    with pytest.raises(Interrupt):
        DT.train_donor_group(row, m2, "cpu", os.path.join(b, "ckpt", gid), {}, max_steps=5, _hooks=StopAt("main", 4))
    assert os.path.exists(os.path.join(b, "ckpt", f"{gid}_resume.pt"))
    lb = DT.train_donor_group(row, m2, "cpu", os.path.join(b, "ckpt", gid), {}, max_steps=5)
    assert len(lb["resumed"]) == 1 and lb["stream"] == la["stream"]
    for m in ("AP", "XM"):
        assert [_strip(x) for x in lb["members"][m]["curve"]] == [_strip(x) for x in la["members"][m]["curve"]]
        assert [x["train"] for x in lb["members"][m]["curve"]] == [x["train"] for x in la["members"][m]["curve"]]
        for kind in DT.KINDS:
            assert _same_state(_enc(SEL.member_ckpt(a, gid, m, kind)), _enc(SEL.member_ckpt(b, gid, m, kind)))
        assert lb["members"][m]["best"] == la["members"][m]["best"]
    assert [e["ep_eq"] for e in la["members"]["AP"]["curve"]][:2] == [1, 2] and la["members"]["AP"]["curve"][-1]["truncated"]
    assert la["schedule"]["steps_per_ep_eq"] == 2 and la["main_steps"] == 5


def test_rich_and_csx_groups_on_the_real_stack(core_run, fx4, man4, tmp_path, small_sets, registry):
    """A rich group (APR, target fau) adopts H* from its core record, trains the normalised rich loss on the rich block's batches
    (rich targets present on SparrKULee rows) and reports the donor-side rich readout for APR and the core AP; a CSX group (APC,
    XPC, target dtu) samples the core strata plus fau_cs. Both write complete records through run_donor.run (max_steps 2)."""
    out = str(tmp_path / "o")
    core_row = core_run["row"]
    _fake_core_record(out, core_row, H=30)
    os.makedirs(os.path.join(out, "ckpt"), exist_ok=True)
    src = SEL.member_ckpt(core_run["out"], core_row["experiment_id"], "AP", "best")
    os.symlink(src, SEL.member_ckpt(out, core_row["experiment_id"], "AP", "best"))
    rrow = real_row(fx4, man4, fam=SEL.RICH_DONOR, horizon_from=core_row["experiment_id"], rich_targets=dict(DT.RICH_TARGETS),
                    loss_weights=[1, 0.5, 0.5])
    RD.run(rrow, out, epochs=2, manifest=man4, device="cpu")
    with open(SEL.record_path(out, rrow["experiment_id"])) as f:
        rec = json.load(f)
    assert rec["status"] == "complete" and rec["code_group"] == "prior33_rich_donor" and list(rec["members"]) == ["APR"]
    assert rec["dependency"]["horizon"]["H"] == 30 and rec["schedule"]["adopted_horizon"] == 30
    assert rec["rich_readout"]["APR"]["ss"]["r_bar"] is not None and rec["rich_readout"]["AP_core"]["sc"]["n_fit"] > 0
    assert "joint_choice" not in rec and rec["record_check"]["ok"] and rec["sigma"]["rich"]["ss"]["sigma_u"] > 0
    assert any(e["train"].get("train_loss_ss") is not None for e in rec["members"]["APR"]["curve"]) or rec["shares"]["main"]["strata"] == {"federici": {"steps": 2, "share": 1.0}}
    # CSX (target dtu): the core record of the dtu group, members APC / XPC, strata + fau_cs
    drow = real_row(fx4, man4, target="dtu")
    _fake_core_record(out, drow, H=30)
    xrow = real_row(fx4, man4, target="dtu", fam=SEL.CSX_DONOR, horizon_from=drow["experiment_id"], extra_strata=["fau_cs"])
    RD.run(xrow, out, epochs=2, manifest=man4, device="cpu")
    with open(SEL.record_path(out, xrow["experiment_id"])) as f:
        rec = json.load(f)
    assert rec["status"] == "complete" and list(rec["members"]) == ["APC", "XPC"] and rec["sampler"]["strata"][-1] == "fau_cs"
    assert rec["xm"] is None and rec["control"] is None and {rec["members"][m]["steps"] for m in ("APC", "XPC")} == {2}


def test_missing_or_inconsistent_dependencies_are_technical_failed(core_run, fx4, man4, tmp_path, registry):
    """§6.1 run_*.py: a missing horizon record, a truncated (probe) horizon record, a horizon of another compute limit and a
    manifest sha mismatch are written as technical_failed records (never a silent return; core.write_record exits 1)."""
    out = str(tmp_path / "f")
    core_row = core_run["row"]
    rrow = real_row(fx4, man4, fam=SEL.RICH_DONOR, horizon_from=core_row["experiment_id"])
    with pytest.raises(SystemExit):
        RD.run(rrow, out, epochs=1, manifest=man4, device="cpu")
    with open(SEL.record_path(out, rrow["experiment_id"]).replace(".json", ".FAILED.json")) as f:
        rec = json.load(f)
    assert rec["status"] == "technical_failed" and rec["error"].startswith("MissingDependency")
    os.makedirs(os.path.join(out, "units"), exist_ok=True)
    with open(SEL.record_path(out, core_row["experiment_id"]), "w") as f:
        json.dump(core_run["rec"], f)                                      # a truncated (probe) core record
    with pytest.raises(ValueError, match="truncated"):
        DT.resolve_upstreams(rrow, out)
    drow = real_row(fx4, man4, target="dtu", limit=90)
    _fake_core_record(out, drow, H=30)
    xrow = real_row(fx4, man4, target="dtu", fam=SEL.CSX_DONOR, horizon_from=drow["experiment_id"])
    with pytest.raises(ValueError, match="compute limit"):
        DT.resolve_upstreams(xrow, out)
    bad = real_row(fx4, man4, target="dtu", manifest_sha256="0" * 64)
    with pytest.raises(SystemExit):
        RD.run(bad, out, epochs=1, manifest=man4, device="cpu")
    with open(SEL.record_path(out, bad["experiment_id"]).replace(".json", ".FAILED.json")) as f:
        assert "manifest sha256" in json.load(f)["error"]


def test_spec_checks_refuse_other_recipes(fx4, man4):
    """§4.3 fields that this runner implements are checked when present: another temperature, budget, selection rule, block,
    optimiser, batch, member set, target contract or lambda rule is refused before any training."""
    ok = real_row(fx4, man4)
    assert DT.check_spec(ok, man4)["members"] == list(CORE5)
    for k, v in (("temperature", 0.07), ("block", "rich"), ("objective", "FMCA"), ("donor_seed", 3407), ("bandwidth_multiplier", 2.0),
                 ("montage_augmentation", "none"), ("control", "x"), ("target_contract", "0" * 16), ("lambda_rule", "max_gain"),
                 ("members", ["AP", "APR"]), ("batch", {"segments": 16, "anchors": 8, "views": 2}), ("fs", 128),
                 ("optimizer", {"name": "AdamW", "lr": 3e-4}), ("selection", {"primary": "donor_dev_gain_v1"}),
                 ("stratum_weights", [0.5, 0.25, 0.25]), ("donor_set", "dtu")):
        bad = copy.deepcopy(ok)
        bad["spec"][k] = v
        with pytest.raises(ValueError):
            DT.check_spec(bad, man4)
    for k, v in (("epoch_equivalents", 20), ("anchors_per_ep_eq", 1), ("steps0", 1), ("continuation", "group_wsd_v1")):
        bad = copy.deepcopy(ok)
        bad["spec"]["budget"][k] = v
        with pytest.raises(ValueError):
            DT.check_spec(bad, man4)
    bad = copy.deepcopy(ok)
    del bad["spec"]["manifest_sha256"]
    with pytest.raises(ValueError):
        DT.check_spec(bad, man4)


def test_cs_objective_members_train_on_fakes(tmp_path):
    """CS_SINGLE groups: AP (cs_audio_pair at sigma_u / sigma_v), XP / J1 / J025 / XM (cs_cross_person at sigma_u on both sides)
    train with finite losses and every update applied; J members record both terms."""
    row = fake_row("ALN3X_" + "5" * 16, limit=30, objective="CS_SINGLE")
    row["spec"]["objective"] = "CS_SINGLE"
    run, _ = fake_run(str(tmp_path / "cs"), row, flat_ce, objective="CS_SINGLE")
    run.run()
    rec = run.finish()
    for m in CORE5:
        tr = [e["train"] for e in rec["members"][m]["curve"]]
        assert all(math.isfinite(t["train_loss"]) for t in tr) and rec["members"][m]["updates"] == 30
    assert all("train_loss_audio" in e["train"] and "train_loss_cross" in e["train"] for e in rec["members"]["J025"]["curve"])
    assert all("train_loss_audio" not in e["train"] for e in rec["members"]["XM"]["curve"])
    for m, lam in (("J1", 1.0), ("J025", 0.25)):          # the recorded raw terms compose the recorded loss
        for t in (e["train"] for e in rec["members"][m]["curve"]):
            assert t["train_loss"] == pytest.approx(t["train_loss_audio"] + lam * t["train_loss_cross"], rel=1e-12, abs=1e-12)


@pytest.mark.parametrize("objective", ["NCE", "CS_SINGLE"])
def test_member_losses_are_the_registered_terms(objective):
    """§2.7-§2.9 and §2.14 on one shared batch: AP = L_audio(u1, u2; v), XP = L_cross(u1, u2), J1 = L_audio + L_cross and J025 =
    L_audio + 0.25 L_cross on the same forward pass of the two views, XM = L_cross(u1, enc(X2[pi])) with X1's keys and the
    deranged partners (losses called directly on the members' outputs; identical initial weights); the recorded parts are the
    raw terms."""
    smp = FakeSampler(11)
    b = smp.next_batch()
    perm, _ = smp.derangement(b)
    xm = smp.xm_view(b, perm)
    heads = {"env": MD.SharedFixedHead(np.ones(8), P_FIXED)}
    sigma = {"sigma_u": 0.7, "sigma_v": 0.9}
    with torch.no_grad():
        v = heads["env"](b.y)
    mems = {m: DT._Member(m, TinyEncoder(), objective, sigma, (), heads) for m in CORE5}
    enc = TinyEncoder()
    u1, u2, u2x = enc(b.x1), enc(b.x2), enc(xm.x2)
    assert torch.equal(xm.keys, b.keys) and torch.equal(xm.x2, b.x2[xm.rows]) and not torch.equal(xm.part2, b.part2)
    if objective == "NCE":
        la = L.nce_audio_pair(u1, u2, v, b.keys, DT.TEMPERATURE, unknown_clock=())[0]
        lc = L.nce_cross_person(u1, u2, b.keys, b.part1, b.part2, DT.TEMPERATURE, unknown_clock=())[0]
        lx = L.nce_cross_person(u1, u2x, b.keys, b.part1, xm.part2, DT.TEMPERATURE, unknown_clock=())[0]
    else:
        la, lc, lx = L.cs_audio_pair(u1, u2, v, 0.7, 0.9)[0], L.cs_cross_person(u1, u2, 0.7)[0], L.cs_cross_person(u1, u2x, 0.7)[0]
    want = {"AP": (la, {"loss_audio": la}), "XP": (lc, {"loss_cross": lc}), "J1": (la + 1.0 * lc, {"loss_audio": la, "loss_cross": lc}),
            "J025": (la + 0.25 * lc, {"loss_audio": la, "loss_cross": lc}), "XM": (lx, {"loss_cross": lx})}
    assert float(lx) != float(lc)                                       # the mismatched partner is a different task
    for m in CORE5:
        loss, parts = mems[m].loss(b, v, None, xm)
        total, terms = want[m]
        assert float(loss) == float(total) and {k: parts[k] for k in ("loss_audio", "loss_cross") if k in parts} == \
            {k: float(t) for k, t in terms.items()}
        assert mems[m].lam == {"J1": 1.0, "J025": 0.25}.get(m)


def test_cs_core_and_rich_groups_on_the_real_stack(core_run, fx4, man4, tmp_path, small_sets):
    """CS_SINGLE on the real stack: the core group's bandwidths are calibrated once on the identical initial encoders (seed + 99
    calibration batches, stratum-weighted) and used by every member; the rich group calibrates its own sigma_u / sigma_v per rich
    head and trains the CS rich loss. Losses are finite (max_steps 2)."""
    out = str(tmp_path / "cs")
    os.makedirs(os.path.join(out, "ckpt"))
    row = real_row(fx4, man4, objective="CS_SINGLE")
    log = DT.train_donor_group(row, man4, "cpu", os.path.join(out, "ckpt", row["experiment_id"]), {}, max_steps=2)
    sig = log["sigma"]
    assert sig["sigma_u"] > 0 and sig["sigma_v"] > 0 and log["terms"] == DT.TERMS["CS_SINGLE"] and log["temperature"] is None
    assert all(log["members"][m]["sigma"] == sig for m in CORE5)
    assert all(math.isfinite(e["train"]["train_loss"]) for m in CORE5 for e in log["members"][m]["curve"])
    _fake_core_record(out, row, H=30)                                     # the CS core group's own AP _best.pt is in out/ckpt
    rrow = real_row(fx4, man4, fam=SEL.RICH_DONOR, objective="CS_SINGLE", horizon_from=row["experiment_id"])
    rlog = DT.train_donor_group(rrow, man4, "cpu", os.path.join(out, "ckpt", rrow["experiment_id"]), {}, max_steps=2)
    rs = rlog["sigma"]["rich"]
    assert rs["ss"]["sigma_u"] > 0 and rs["sc"]["sigma_v"] > 0 and rlog["sigma"]["sigma_u"] == pytest.approx(sig["sigma_u"])
    assert all(math.isfinite(e["train"]["train_loss"]) for e in rlog["members"]["APR"]["curve"])
    assert rlog["rich_readout"]["APR"]["env"]["r_bar"] is not None


def test_adopted_horizons_and_continuations_stay_within_one_version(fx4, man4, tmp_path):
    """resolve_upstreams (prior33_open_M8_M10.md, M8 validation item): a rich / CSX group adopts H* only from a core group of
    the same compute limit and version (a primary group from a primary core group; a continuation from the continuation of its
    source's core group); a continuation needs its source's ceiling flag and retained stable states."""
    out = str(tmp_path / "v")
    G = real_row(fx4, man4, target="dtu")
    Gc = real_row(fx4, man4, target="dtu", limit=90, continuation_of=G["experiment_id"])
    G2 = real_row(fx4, man4, target="dtu", seed=3401, members=["AP", "XP", "J1", "J025"])
    Gx = real_row(fx4, man4, target="dtu", limit=90, continuation_of=G2["experiment_id"])
    for r, H, ceil in ((G, 60, True), (Gc, 70, False), (G2, 60, True), (Gx, 70, False)):
        _fake_core_record(out, r, H=H, ceiling=ceil)
    X = real_row(fx4, man4, target="dtu", fam=SEL.CSX_DONOR, horizon_from=G["experiment_id"])
    assert DT.resolve_upstreams(X, out)["horizon"]["H"] == 60
    rec = _fake_core_record(out, X, H=60, ceiling=True)
    assert rec["ceiling_reached_while_improving"]
    Xc = real_row(fx4, man4, target="dtu", fam=SEL.CSX_DONOR, limit=90, continuation_of=X["experiment_id"], horizon_from=Gc["experiment_id"])
    with pytest.raises(DT.MissingDependency, match="retained stable states"):
        DT.resolve_upstreams(Xc, out)
    os.makedirs(os.path.join(out, "ckpt"), exist_ok=True)
    for f in SEL.retained_states(out, X):
        open(f, "wb").close()
    ups = DT.resolve_upstreams(Xc, out)
    assert ups["horizon"]["H"] == 70 and ups["continuation"]["gid"] == X["experiment_id"]
    Xbad = real_row(fx4, man4, target="dtu", fam=SEL.CSX_DONOR, limit=90, continuation_of=X["experiment_id"], horizon_from=Gx["experiment_id"])
    with pytest.raises(ValueError, match="continues"):
        DT.resolve_upstreams(Xbad, out)
    Xp = real_row(fx4, man4, target="dtu", fam=SEL.CSX_DONOR, limit=90, horizon_from=Gc["experiment_id"])
    with pytest.raises(ValueError, match="primary core group"):
        DT.resolve_upstreams(Xp, out)
    Xn = real_row(fx4, man4, target="dtu", fam=SEL.CSX_DONOR, limit=90, continuation_of=Gc["experiment_id"], horizon_from=Gc["experiment_id"])
    with pytest.raises(ValueError):
        DT.resolve_upstreams(Xn, out)                                      # a continuation's source must be a group of its family
    D = real_row(fx4, man4, target="dtu", horizon_from=G["experiment_id"])
    with pytest.raises(ValueError, match="own trigger"):
        DT.resolve_upstreams(D, out)
    # review item: a continuation resumes its source's exact trajectory, so the source must have the same dataset, seed,
    # objective and block (an NCE source is never continued under CS_SINGLE) and must not be a truncated probe record
    for kw, what in ((dict(target="fau"), "dataset"), (dict(seed=3407), "seed"), (dict(objective="CS_SINGLE"), "objective"),
                     (dict(block="panel"), "block")):
        bad = real_row(fx4, man4, **{"target": "dtu", **kw}, limit=90, continuation_of=G["experiment_id"])
        with pytest.raises(ValueError, match=what):
            DT.resolve_upstreams(bad, out)
    Gt = real_row(fx4, man4, target="dtu", members=["AP", "XP"], seed=3413)
    _fake_core_record(out, Gt, H=60, ceiling=True, truncated={"max_steps": 9})
    bad = real_row(fx4, man4, target="dtu", members=["AP", "XP"], seed=3413, limit=90, continuation_of=Gt["experiment_id"])
    with pytest.raises(ValueError, match="truncated"):
        DT.resolve_upstreams(bad, out)


def test_record_feeds_deps_and_the_analysis(core_run, fx4, man4):
    """The written group record and files are what the downstream modules read: deps.ready admits a J* bridge row and a rich group
    (the core AP checkpoint) of this group, and analysis._donor_table (M11) reads members x {_best, _h30, _gainsel} x {CE_dev,
    gain, bridge_cal CE, ep-eq} as numbers and finds the recorded joint choice in agreement with the recomputed lambda rule."""
    from auditory_alignment_v3.prior33 import analysis as A
    from auditory_alignment_v3.prior33 import deps as D
    out, row, rec = core_run["out"], core_run["row"], core_run["rec"]
    gid = row["experiment_id"]
    br = {"experiment_id": "ALN3X_" + "b0" * 8, "family_id": SEL.BRIDGE, "dataset": "fau", "subject_fold": None, "content_fold": None,
          "seed": 3401, "logical_dependencies": [gid],
          "spec": {"stage": "bridge", "block": "core", "objective": "NCE", "donor_group": gid, "member": "J*", "donor_seed": 3401,
                   "bridge": "ridge_u_to_stdenv8_v1"}}
    rr = real_row(fx4, man4, fam=SEL.RICH_DONOR, horizon_from=gid)
    rows = [row, br, rr]
    D.check_row(br, rows)
    assert D.ready(br, rows, out) and D.ready(rr, rows, out)
    t = A._donor_table(row, rec)
    assert t["member_error"] is None and set(t["members"]) == set(CORE5)
    for m in CORE5:
        for kind in ("best", "h30", "gainsel"):
            assert all(isinstance(t["members"][m][f"{kind}/{q}"], float) for q in ("ce_dev", "gain", "bridge_cal_ce", "ep_eq"))
        assert t["members"][m]["steps"] == 3 and t["members"][m]["nonfinite_steps"] == 0
    assert t["lambda"]["check"] == "agrees" and t["lambda"]["recorded_gain_rule"] == rec["gain_rule"]["member"]
    assert t["ceiling_reached_while_improving"] == 0.0 or t["ceiling_reached_while_improving"] is False


# ---------------------------------------------------------------------------------------------------------- real-stack chain
class _FailOnce:
    """Wraps a run_donor helper so that its first call raises (an error after training, before the record is written)."""

    def __init__(self, fn):
        self.fn, self.calls = fn, 0

    def __call__(self, *a, **k):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("injected failure after training (before the record)")
        return self.fn(*a, **k)


@pytest.fixture(scope="module")
def chain(fx4, man4, tmp_path_factory):
    """Real-stack donor groups on the scale-4 fixture with a short budget (manifest copy: 1 ep-eq = 0.5 steps, anchors_per_ep_eq
    128, S0 = 15), the trigger forced to fire (DT.improving patched), stream hashes every 3 steps and 2 fit segments / 2 dev and
    bridge_cal queries, all written through run_donor.run into one output tree under the open-file audit:
      G30  core group (AP), limit 30: ceiling at 27 (stable27 kept), H* = 30. Its first attempt fails in run_donor after training
           (an injected error before the record); the retry resumes the finished run.
      G40  core group (AP), limit 40: extends at 27 (side branch 27 -> 30), ceiling at 37 (stable37 kept), H* = 40.
      C40  the continuation of G30 with limit 40: it must follow G40 from 27 on.
      R40  rich group (APR), limit 40, horizon_from G40: its stream is checked against G40's real record."""
    mp = pytest.MonkeyPatch()
    out = str(tmp_path_factory.mktemp("m5_chain"))
    res = {"out": out}
    try:
        mp.setattr(SM, "selection_sets", lambda man: _small_sets(man, n_fit=2, n_dev=2, n_cal=2))
        mp.setattr(SM, "HASH_EVERY", 3)
        mp.setattr(DT, "improving", lambda values, last=DT.LAST: True)
        _registry_entries(mp)
        m128 = _manifest_with_budget(man4, 128)
        rows = {"G30": real_row(fx4, m128, members=["AP"], limit=30), "G40": real_row(fx4, m128, members=["AP"], limit=40)}
        rows["C40"] = real_row(fx4, m128, members=["AP"], limit=40, continuation_of=rows["G30"]["experiment_id"])
        rows["R40"] = real_row(fx4, m128, fam=SEL.RICH_DONOR, limit=40, horizon_from=rows["G40"]["experiment_id"])
        res.update(rows=rows, manifest=m128)
        g30 = rows["G30"]["experiment_id"]
        ck = os.path.join(out, "ckpt")
        with opened_files() as seen:
            mp.setattr(RD, "coverage", _FailOnce(RD.coverage))
            with pytest.raises(SystemExit):
                RD.run(rows["G30"], out, manifest=m128, device="cpu")
            with open(SEL.record_path(out, g30).replace(".json", ".FAILED.json")) as f:
                res["g30_failed"] = json.load(f)
            res["g30_resume_after_failure"] = sorted(f for f in os.listdir(ck) if "resume" in f)
            res["g30_resume_done"] = bool(torch.load(os.path.join(ck, f"{g30}_resume.pt"), map_location="cpu", weights_only=True)["done"])
            RD.run(rows["G30"], out, manifest=m128, device="cpu")
            for name in ("G40", "C40", "R40"):
                RD.run(rows[name], out, manifest=m128, device="cpu")
        res["opened"] = list(seen)
        res["texts"] = {}
        for name, r in rows.items():
            with open(SEL.record_path(out, r["experiment_id"])) as f:
                res["texts"][name] = f.read()
        res["recs"] = {name: json.loads(t) for name, t in res["texts"].items()}
        res["resume_left"] = sorted(f for f in os.listdir(ck) if "resume" in f)
    finally:
        mp.undo()
    return res


def test_real_failure_after_training_keeps_the_trajectory(chain):
    """Review item (resume files): they are deleted only after the complete record is written. The first G30 attempt fails in
    run_donor after training (injected): its .FAILED.json is written and <gid>_resume.pt stays, marked done; the retry resumes
    the finished run, trains nothing, redoes only the post-training scores and writes the complete record; at the end no resume
    file is left anywhere in the tree. Every record of the chain is strict JSON."""
    rec, failed = chain["recs"]["G30"], chain["g30_failed"]
    g30 = chain["rows"]["G30"]["experiment_id"]
    assert failed["status"] == "technical_failed" and "injected failure" in failed["error"]
    assert chain["g30_resume_after_failure"] == [f"{g30}_resume.pt"] and chain["g30_resume_done"] is True
    assert rec["status"] == "complete" and len(rec["resumed"]) == 1 and rec["resumed"][0]["step"] == rec["main_steps"] == 15
    assert rec["timing"]["n_validations"] == 30 == len(rec["members"]["AP"]["curve"]) and rec["resumed"][0]["device"] == "cpu"
    assert chain["resume_left"] == []
    for name, text in chain["texts"].items():
        assert _strict_json(text)["status"] == "complete", name
        assert chain["recs"][name]["record_check"]["ok"] and chain["recs"][name]["resume_cleanup"].startswith("the caller")


def test_real_side_branch_ceiling_and_h30(chain):
    """§7.1 10c-10d on the real stack: G40 extends at 27 (side branch 27 -> 30 from the saved stable state) and reaches its limit
    40 while the trigger fires (ceiling at 37, stable37 kept, H* = 40). The side branch trains exactly the fixed 30-ep-eq recipe:
    G40's side-branch validations equal G30's decay validations (dev scores, the same steps and lr), and G40's _h30_best equals
    G30's _h30_best and _best (G30 trains only that recipe); main-run validations after the extension are not h30-eligible."""
    g30, g40, out = chain["recs"]["G30"], chain["recs"]["G40"], chain["out"]
    id30, id40 = chain["rows"]["G30"]["experiment_id"], chain["rows"]["G40"]["experiment_id"]
    assert [e["decision"] for e in g30["trigger_log"]] == ["ceiling"] and g30["horizon_ep_eq"] == 30
    assert [e["decision"] for e in g40["trigger_log"]] == ["extend", "ceiling"] and g40["horizon_ep_eq"] == 40
    assert g40["ceiling_reached_while_improving"] and g40["side_branch"]["ran"] and g40["side_branch"]["start_ep_eq"] == 27
    assert g30["steps_by_phase"] == {"stable": 14, "decay": 1, "side": 0} and g40["steps_by_phase"] == {"stable": 19, "decay": 1, "side": 1}
    c30, c40 = g30["members"]["AP"]["curve"], g40["members"]["AP"]["curve"]
    side = [e for e in c40 if e["branch"] == "side"]
    dec30 = [e for e in c30 if e["ep_eq"] in (28, 29, 30)]
    assert [(e["ep_eq"], e["step"], e["lr_last"]) for e in side] == [(e["ep_eq"], e["step"], e["lr_last"]) for e in dec30]
    assert [e["dev"] for e in side] == [e["dev"] for e in dec30] and [e["dev"] for e in c40[:27]] == [e["dev"] for e in c30[:27]]
    assert all(not e["h30_eligible"] for e in c40 if e["branch"] == "main" and e["ep_eq"] > 27)
    h30 = _enc(SEL.member_ckpt(out, id40, "AP", "h30"))
    assert _same_state(h30, _enc(SEL.member_ckpt(out, id30, "AP", "h30"))) and _same_state(h30, _enc(SEL.member_ckpt(out, id30, "AP", "best")))
    assert g40["members"]["AP"]["h30"]["ce_dev"] == g30["members"]["AP"]["best"]["ce_dev"]
    for row, e in ((chain["rows"]["G30"], 27), (chain["rows"]["G40"], 37)):
        (p,) = SEL.retained_states(out, row)
        st = torch.load(p, map_location="cpu", weights_only=True)
        assert os.path.basename(p) == f"{row['experiment_id']}_mAP_stable{e}.pt" and st["ep_eq"] == e
        assert st["group_state"]["step"] == DT.steps_at(e, 128) and not st["group_state"]["wsd_pre_decision"]["ceiling"]


def test_real_continuation_follows_the_larger_limit(chain):
    """A continuation on the real stack: C40 (limit 40, continuation_of G30) resumes from G30's retained stable27 state (model,
    AdamW, sampler and derangement generators, sigma, curves, best states), re-decides at 27 under its own limit (extend, with the
    side branch) and follows G40 -- the same group with limit 40 from the start -- exactly: curves, selected checkpoints,
    horizon, ceiling, stream; compute_inherited / compute_this_run split the cumulative counters; the dependency records that the
    source ran under the same code."""
    c40, g40, out = chain["recs"]["C40"], chain["recs"]["G40"], chain["out"]
    idc, id40, id30 = (chain["rows"][k]["experiment_id"] for k in ("C40", "G40", "G30"))
    assert c40["inherited"]["from"] == id30 and c40["inherited"]["ep_eq"] == 27 and c40["sigma"] == g40["sigma"]
    assert [e["decision"] for e in c40["trigger_log"]] == ["extend", "ceiling"]
    assert (c40["horizon_ep_eq"], c40["ceiling_reached_while_improving"]) == (40, True)
    assert c40["stream"]["final"] == g40["stream"]["final"] and c40["stream"]["hash_log"] == g40["stream"]["hash_log"]

    def strip(c):
        return [{k: v for k, v in e.items() if k != "group"} for e in c]
    assert strip(c40["members"]["AP"]["curve"]) == strip(g40["members"]["AP"]["curve"])
    for kind in DT.KINDS:
        a, b = c40["members"]["AP"][kind], g40["members"]["AP"][kind]
        assert {k: v for k, v in a.items() if k != "group"} == {k: v for k, v in b.items() if k != "group"}
        assert _same_state(_enc(SEL.member_ckpt(out, idc, "AP", kind)), _enc(SEL.member_ckpt(out, id40, "AP", kind)))
    assert all(os.path.exists(p) for p in SEL.retained_states(out, chain["rows"]["C40"]))       # its own stable37
    ci, ct = c40["compute_inherited"], c40["compute_this_run"]
    assert ci["from"] == id30 and (ci["main_steps"], ci["side_steps"], ci["n_validations"]) == (14, 0, 27)
    assert (ct["main_steps"], ct["side_steps"], ct["n_validations"]) == (6, 1, 16) and c40["main_steps"] == g40["main_steps"] == 20
    assert ct["member_steps"]["AP"] == {"main": 6, "side": 1} and g40["compute_inherited"] is None
    assert ct["train_flops_proxy"]["AP"] + ci["train_flops_proxy"]["AP"] == pytest.approx(c40["flop_proxy"]["train_flops_proxy"]["AP"])
    assert c40["flop_proxy"]["train_flops_proxy"] == g40["flop_proxy"]["train_flops_proxy"]
    dep = c40["dependency"]["continuation"]
    assert dep["gid"] == id30 and dep["code_hash_equal"] is True and dep["same_code_group"] is True


def test_real_rich_stream_check_against_a_real_core_record(chain, tmp_path, monkeypatch):
    """§2.15 on the real stack: the rich group R40 adopts G40's realised H* = 40 and ceiling flag, and its stream (DonorSampler,
    rich block) is checked against G40's real record at every logged step (every 3 steps here, side branch included) and at the
    end ('equal'); a core record with one altered hash makes the rich group fail with StreamMismatch at that step."""
    r40, g40 = chain["recs"]["R40"], chain["recs"]["G40"]
    cc = r40["stream"]["core_check"]
    assert cc["core_group"] == chain["rows"]["G40"]["experiment_id"] and cc["final"] == "equal"
    assert len(g40["stream"]["hash_log"]) == 6 and cc["checked"] >= 6 and r40["stream"]["hash_log"] == g40["stream"]["hash_log"]
    assert (r40["horizon_ep_eq"], r40["ceiling_reached_while_improving"]) == (40, True) and r40["steps_by_phase"] == g40["steps_by_phase"]
    assert [e["decision"] for e in r40["trigger_log"]] == ["extend", "ceiling"] and r40["trigger_log"][0]["members"] is None
    assert r40["dependency"]["horizon"]["same_code_group"] is False and r40["rich_readout"]["APR"]["ss"]["r_bar"] is not None
    assert set(r40["flop_proxy"]["encoder_fwd_bwd_per_window"]) == {"rich"}
    assert all(r40["flop_proxy"]["encoder_fwd_bwd_per_window"]["rich"][s] > g40["flop_proxy"]["encoder_fwd_bwd_per_window"]["shared"][s]
               for s in r40["sampler"]["strata"])                                                  # + the two rich heads
    monkeypatch.setattr(SM, "selection_sets", lambda man: _small_sets(man, n_fit=2, n_dev=2, n_cal=2))
    monkeypatch.setattr(SM, "HASH_EVERY", 3)
    row = chain["rows"]["R40"]
    ups = DT.resolve_upstreams(row, chain["out"])
    assert ups["horizon"]["hash_log"] == g40["stream"]["hash_log"]
    ups["horizon"]["hash_log"][0][1] = "0" * 64                                                    # G40's hash at step 3
    d = str(tmp_path / "t")
    os.makedirs(os.path.join(d, "ckpt"))
    with pytest.raises(DT.StreamMismatch, match="step 3"):
        DT.train_donor_group(row, chain["manifest"], "cpu", os.path.join(d, "ckpt", row["experiment_id"]), {}, upstream=ups)


def test_donor_runs_never_open_restricted_or_raw_files(chain, fx4):
    """§7.1 item 8 on the donor side: while the chain's donor units ran (sampler, fixed score sets, bandwidths, FLOP proxy,
    training, validation, checkpoints, rich readout, records), no restricted participant's file and no raw file of the fixture
    was opened (open-file audit hook); the caches they read were."""
    root = os.path.abspath(fx4["root"])
    mine = [p for p in chain["opened"] if p.startswith(root)]
    decoys = {os.path.abspath(os.path.join(fx4["root"], f)) for f in fx4["truth"]["restricted_files"]}
    assert mine and decoys and not decoys & set(chain["opened"])
    assert not [p for p in mine if "raw" in p.split(os.sep) or os.path.basename(p).startswith("sub-")
                or any(f"sub-{r}" in p for r in V.RESTRICTED)]
    assert any(p.endswith(os.path.join("sparrkulee", "eeg_f16_tmajor.npy")) for p in mine)
