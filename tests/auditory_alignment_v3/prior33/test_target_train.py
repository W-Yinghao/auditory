"""M7 target-supervised adaptation tests (PUBLIC_PRIOR_DESIGN.md §2.12, §4.3, §6.1, §6.6 M7; §7.1 items 7d / 7e and 11 for the
target stage; record interface private/auditory_alignment_v3/aln34/prior33_interfaces_M11.md):
  - the generator: every declared substitution applies exactly once, drift (a broken, duplicated or kept anchor, a forbidden call)
    fails, the output is byte-identical for the same source sha256 (also from a fresh process), and undoing the declared
    substitutions on the generated functions gives back local_train.py's functions exactly (the A_LOCAL recipe is otherwise
    unchanged); every label is a numbered design item or an "engineering:" one, and the resume cadence is its own engineering
    substitution (not part of design item 5);
  - the shared head is the envelope head alone: a rich block whose projection files are missing or altered cannot fail it;
  - strict donor loading through the generated copy (public and private), the opened new-channel rows train, and refusals;
  - the outer test (test participants, test content, competing-talker pieces) is never read by fitting or checkpoint selection:
    perturbing all of it leaves the training log and both checkpoints bit-identical (public and private);
  - both checkpoints are written, chosen by their two rules, survive an interrupted run (exact resume on CPU), and both are
    evaluated; gainsel "unavailable" (no finite gain-rule score) end to end through run_target and the analysis;
  - tiny CPU runs of run_target on the fixture write records that prior33.analysis.normalise accepts (public J* through
    core.load_rows as run.py patches it, public S, public CS_SINGLE S, private NCE donor arm, private CS_SINGLE S and donor arm),
    with declarations that match the dataset and objective; missing dependencies, wrong manifests, refused donors, rows that
    break the equal-budget guard and rows that fail binding or core.new_record are technical_failed records;
  - member checkpoints written by run_donor (scale-4 fixture, max_steps 3) feed run_target: J*, AP, XM and S of one cell;
  - every arm of a cell gets the identical budget (batch stream, steps, epochs, validation set, prototype initialisation).
Synthetic data only (fixtures.py: scale 1; scale 4 for the run_donor integration, which needs the §2.6 batch geometry), CPU,
about 4-5 minutes."""
import copy
import hashlib
import inspect
import json
import os
import re
import subprocess
import sys

import numpy as np
import pytest
import torch

from auditory_alignment import train as T1
from auditory_alignment_v2.temporal import build_encoder
from auditory_alignment_v3 import core
from auditory_alignment_v3.prior33 import analysis as A
from auditory_alignment_v3.prior33 import contract as C
from auditory_alignment_v3.prior33 import donor_train as DT
from auditory_alignment_v3.prior33 import fit_target as FT
from auditory_alignment_v3.prior33 import gen_fit_target as GEN
from auditory_alignment_v3.prior33 import losses as L
from auditory_alignment_v3.prior33 import model as M
from auditory_alignment_v3.prior33 import run_donor as RD
from auditory_alignment_v3.prior33 import run_target as RT
from auditory_alignment_v3.prior33 import sampler as SM
from auditory_alignment_v3.prior33 import select as SEL
from auditory_alignment_v3.prior33 import target_train as TT
from auditory_alignment_v3.prior33 import views as V

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fixtures import make_synthetic_manifest, synthetic_kids  # noqa: E402

GEOM = {"architecture": "lag_local_tokens", "channel_map": "name_indexed_signed_v1", "window": "full", "input_samples": [0, 38], "fs": 64,
        "projection_dim": 32}
P33_TARGET_FILES = [("auditory_alignment_v3", "core.py"), ("auditory_alignment_v3", "local_train.py")] + \
    [("auditory_alignment_v3/prior33", f) for f in ("contract.py", "views.py", "model.py", "losses.py", "select.py", "gen_fit_target.py",
                                                     "fit_target.py", "target_train.py", "run_target.py")] + \
    [("auditory_alignment_v3", "calib.py"), ("auditory_alignment_v3/aln3_reference", "calibration.py")]     # design §6.3
P33_DONOR_FILES = [("auditory_alignment_v3", "core.py"), ("auditory_alignment_v3", "local_train.py")] + \
    [("auditory_alignment_v3/prior33", f) for f in ("contract.py", "views.py", "model.py", "losses.py", "sampler.py", "select.py",
                                                     "donor_train.py", "run_donor.py")]
CADENCE = "engineering: resume at every validation (A_LOCAL: every 20 epochs)"
ENGINEERING = {"engineering: signature", "engineering: return (enc, head, bt)", CADENCE}


class Preempted(Exception):
    pass


# ---------------------------------------------------------------------------------------------------------- fixtures and rows
@pytest.fixture(scope="module")
def fx(tmp_path_factory):
    return make_synthetic_manifest(tmp_path_factory.mktemp("m7_fx"))


@pytest.fixture(scope="module")
def man(fx):
    return V.open_manifest(fx["manifest_path"], fx["manifest_sha256"])


@pytest.fixture(autouse=True)
def one_thread():
    """Bit-identical comparisons between runs: one intra-op thread for this module's tests (restored afterwards)."""
    n = torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(n)


@pytest.fixture
def registered(monkeypatch):
    """The §6.3 registry entries of prior33_target (registry.py is edited only at deployment) and a CPU device name."""
    monkeypatch.setitem(core.FAMILY_CODE, "prior33_target", P33_TARGET_FILES)
    monkeypatch.setitem(core.FAMILY_GROUP, SEL.TARGET, "prior33_target")
    monkeypatch.setattr(torch.cuda, "get_device_name", lambda *a, **k: "cpu (test)")


def _eid(*parts):
    return "ALN3X_" + hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()[:16]


def group_row(fx, ds, obj="NCE", seed=3401):
    spec = {"stage": "donor_group", "block": "core", "queue_tier": 1, "objective": obj, "members": list(SEL.GROUP_MEMBERS[SEL.DONOR]),
            "donor_seed": seed, "sampler_seed": seed, "lambda_rule": SEL.LAMBDA_RULE, "manifest_sha256": fx["manifest_sha256"],
            "budget": {"epoch_equivalents": 30, "continuation": "group_wsd_any_last3_ext10_limit60_v1"}, **GEOM}
    return {"experiment_id": _eid("G", ds, obj, seed), "family_id": SEL.DONOR, "dataset": ds, "subject_fold": None, "content_fold": None,
            "seed": seed, "spec": spec, "logical_dependencies": ["frozen_manifest"]}


def target_row(fx, ds, sf, cf, member=None, group=None, obj="NCE", seed=3401, **kw):
    private = ds == "private_bdf"
    cell = next(c for c in fx["manifest"]["cells"] if c["dataset"] == ds and c["subject_fold"] == sf and c["content_fold"] == (cf or 0))
    spec = {"stage": "target", "block": "core", "queue_tier": 1, "logical_family": RT.LOGICAL_FAMILY, "card": RT.CARD,
            "execution_contract": C.CONTRACT, "manifest_sha256": fx["manifest_sha256"], "seed_scope": "breadth", "objective": obj,
            "variant": member or "S", "member": member, "init": "donor" if group else "random",
            "donor_group": group["experiment_id"] if group else None, "donor_seed": group["seed"] if group else None,
            "sampler_seed": group["seed"] if group else None, "target_seed": seed, "recipe": TT.RECIPE, "epochs": 200, "nce": L.NCE_TAG,
            "selection": dict(TT.SELECTION), "split_hash": cell["split_hash"], "target": "current_class" if private else "envelope",
            "target_contract": fx["manifest"]["target_contract"], **GEOM}
    if private:
        spec.update(training_task="current_class", private_input=V.PRIVATE_INPUT)
    spec.update(kw)
    return {"experiment_id": _eid("T", ds, sf, cf, member, spec["donor_group"], obj, seed, sorted(kw.items())), "family_id": SEL.TARGET,
            "dataset": ds, "subject_fold": sf, "content_fold": None if private else cf, "seed": seed, "spec": spec,
            "logical_dependencies": [group["experiment_id"]] if group else [], "job_kind": "train"}


def donor_state(fx, target, seed=3401):
    """A donor member as its group builds it (the donor-union seen set, SparrKULee row order), after one AdamW step."""
    enc = M.build_shared(C.BIOSEMI64, fx["manifest"]["seen"][target], seed)
    g = torch.Generator().manual_seed(seed)
    opt = torch.optim.AdamW(enc.parameters(), lr=1e-2, weight_decay=1e-4)
    (enc(torch.randn(8, 64, C.L_IN, generator=g)) * torch.randn(8, 32, generator=g)).sum().backward()
    opt.step()
    return {k: v.detach().clone() for k, v in enc.state_dict().items()}


def write_group(out, g, states, ce=None, m5=()):
    """A complete donor-group record in the pinned select.py layout, and the members' _best.pt checkpoints ({"enc": state}; members
    in `m5` in donor_train.py's member format, with its provenance fields)."""
    os.makedirs(os.path.join(out, "units"), exist_ok=True)
    os.makedirs(os.path.join(out, "ckpt"), exist_ok=True)
    ce = ce or {}
    rec = {"experiment_id": g["experiment_id"], "row": g, "status": "complete", "code_hash": "synthetic0000000", "code_group": "prior33_donor",
           "members": {m: {"best": {"ce_dev": float(ce.get(m, 3.0))}} for m in SEL.group_members(g)}}
    rec["joint_choice"] = SEL.joint_choice(rec)
    with open(SEL.record_path(out, g["experiment_id"]), "w") as f:
        json.dump(rec, f)
    for m, st in states.items():
        obj = {"enc": st}
        if m in m5:
            obj = {"format": RT.CKPT_FORMAT, "group": g["experiment_id"], "member": m, "kind": "best", "enc": st, "contract": C.CONTRACT,
                   "manifest_sha256": g["spec"]["manifest_sha256"], "objective": g["spec"]["objective"], "donor_seed": g["seed"]}
        torch.save(obj, SEL.member_ckpt(out, g["experiment_id"], m, "best"))
    return rec


def _no_seconds(curve):
    return [{k: v for k, v in c.items() if k != "seconds"} for c in curve]


def _tensors(path):
    sd = torch.load(path, map_location="cpu")
    return {f"{m}.{k}": v for m, d in sd.items() for k, v in (d.items() if isinstance(d, dict) else [("", d)])}


def _same_tensors(a, b):
    return set(a) == set(b) and all(torch.equal(a[k], b[k]) for k in a)


# ---------------------------------------------------------------------------------------------------------- the generator
def test_generator_substitutions_drift_and_determinism(tmp_path, monkeypatch):
    src = GEN.read_source()
    sha = GEN.sha256_text(src)
    assert sha == FT.SOURCE_SHA256 and FT.SOURCE == GEN.SOURCE_REL == "auditory_alignment_v3/local_train.py"
    text = GEN.generate(src)
    assert text == GEN.generate(src)                                       # a pure function of the source text
    with open(GEN.OUTPUT, encoding="utf-8") as f:
        committed = f.read()
    assert text == committed and GEN.check()[0] and TT.check_generated()["ok"]
    header = committed.split('"""')[1]
    assert f"(sha256 {sha})" in header                                     # the header names the full source sha256
    assert FT.SUBSTITUTIONS == tuple(f"{fn}: {lab}" for fn, lab, _, _ in GEN.SUBSTITUTIONS)
    labels = {lab for _, lab, _, _ in GEN.SUBSTITUTIONS}
    assert {"1 batcher", "2 encoder", "3 standardiser", "3 head", "4 objective", "5 two checkpoints", "6 batcher", "6 encoder",
            "6 two checkpoints"} <= labels
    # every label is a numbered design item or a declared engineering change; the engineering ones are listed apart
    kinds = {lab: GEN.label_kind(lab) for lab in labels}
    assert {lab for lab, k in kinds.items() if k == "engineering"} == ENGINEERING and set(kinds.values()) == {"design", "engineering"}
    assert FT.ENGINEERING_SUBSTITUTIONS == tuple(f"{fn}: {lab}" for fn, lab, _, _ in GEN.SUBSTITUTIONS if lab in ENGINEERING)
    assert TT.check_generated()["engineering_substitutions"] == list(FT.ENGINEERING_SUBSTITUTIONS)
    assert all(f"  - {fn} / {lab}:" in header for fn, lab, _, _ in GEN.SUBSTITUTIONS)
    # the resume cadence is its own engineering substitution; design item 5's resume entry adds the best_gainsel payload only
    by = {(fn, lab): (a, b) for fn, lab, a, b in GEN.SUBSTITUTIONS}
    for fn in GEN.FUNCTIONS:
        a, b = by[(fn, CADENCE)]
        assert (a.strip(), b.strip()) == ("if (ep + 1) % 20 == 0 and ep + 1 < epochs:", "if ep + 1 < epochs:")
        a5, b5 = by[(fn, "5 resume save (best_gainsel in the resume file)")]
        assert "if " not in a5 + b5 and b5.replace("best_gainsel=list(best_gs),\n                             ", "", 1) == a5
    for bad in ("resume cadence", "7 extra", "engineering: "):              # a label outside the scheme is refused
        subs = tuple((fn, bad if lab == CADENCE else lab, a, b) for fn, lab, a, b in GEN.SUBSTITUTIONS)
        with monkeypatch.context() as m:
            m.setattr(GEN, "SUBSTITUTIONS", subs)
            with pytest.raises(GEN.SubstitutionError, match="neither a design"):
                GEN.generate(src)
    funcs = GEN.function_sources(src)
    for fn, lab, anchor, _ in GEN.SUBSTITUTIONS:
        assert funcs[fn].count(anchor) == 1, (fn, lab)

    def regen(fn, old, new):
        return GEN.generate(src.replace(funcs[fn], funcs[fn].replace(old, new, 1), 1))

    for fn, lab, anchor, _ in GEN.SUBSTITUTIONS:                           # drift: each anchor broken in turn
        with pytest.raises(GEN.SubstitutionError, match=re.escape(f"{fn}: {lab}") + ".*occurs 0 times"):
            regen(fn, anchor, anchor.replace("\n", "  # drift\n", 1))
    with pytest.raises(GEN.SubstitutionError, match="occurs 2 times"):    # an anchor duplicated
        a = GEN.SUBSTITUTIONS[1][2]
        regen("fit_continuous", a, a + a)
    for fn, lab, line in GEN.KEPT:                                         # the private Objective line must stay as it is
        with pytest.raises(GEN.SubstitutionError, match="kept line"):
            regen(fn, line, line.replace("\n", "  # drift\n", 1))
    enc_line = '    enc = build_encoder(spec["architecture"], 20, d, bt.W, 250).to(dev)\n'
    with pytest.raises(GEN.SubstitutionError, match="still contains"):     # a second native private build is refused
        regen("fit_private", enc_line, enc_line + '    _native = build_encoder(spec["architecture"], 20, d, bt.W, 250)\n')
    with pytest.raises(GEN.SubstitutionError, match="no module-level function"):
        GEN.generate(src.replace("\ndef fit_private(", "\ndef fit_private_renamed(", 1))
    # a harmless source edit regenerates (another sha) and the committed copy is then reported stale
    edited = src.replace(funcs["fit_continuous"], funcs["fit_continuous"].replace('    spec = row["spec"]\n', '    spec = row["spec"]  # edit\n', 1), 1)
    p_src, p_out = tmp_path / "local_train.py", tmp_path / "fit_target.py"
    p_src.write_text(edited, encoding="utf-8")
    assert GEN.check(str(p_src), GEN.OUTPUT)[0] is False and GEN.sha256_text(edited) in GEN.generate(edited)
    GEN.write(str(p_src), str(p_out))
    assert GEN.check(str(p_src), str(p_out))[0] and p_out.read_text(encoding="utf-8") == GEN.generate(edited)
    assert GEN.main(["--check", "--source", str(p_src), "--output", str(p_out)]) == 0
    assert GEN.main(["--check", "--output", str(p_out)]) == 1
    env = dict(os.environ, PYTHONPATH=core.REPO, OMP_NUM_THREADS="1")      # a fresh process regenerates the same bytes
    (tmp_path / "cwd").mkdir()
    r = subprocess.run([sys.executable, "-B", "-m", "auditory_alignment_v3.prior33.gen_fit_target", "--check"], cwd=str(tmp_path / "cwd"),
                       env=env, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr


def test_generated_copy_paths_and_unchanged_recipe():
    """§7.1 7d / 7e: no native build in either path, the private Objective is the unpatched class, the continuous path uses
    ContractObjective; undoing the declared substitutions gives back local_train.py's functions exactly."""
    cont, priv = inspect.getsource(FT.fit_continuous_p33), inspect.getsource(FT.fit_private_p33)
    assert "build_encoder(" not in cont + priv and "GridBatcher" not in cont and "250" not in priv and "PrivateBatcher(" not in priv
    assert "build_target_encoder(row, coh.layout, manifest, donor_state)" in cont
    assert "build_target_encoder(row, PRIVATE_LAYOUT, manifest, donor_state)" in priv and "PrivateBatcher64(kids, spec, row, dev)" in priv
    assert FT.Objective is T1.Objective and FT.ContractObjective is L.ContractObjective and "ContractObjective" not in priv
    assert priv.count("Objective(obj_job, enc(P), None, labels0=Y)") == 1 and len(re.findall(r"(?<![A-Za-z_])Objective\(", cont)) == 0
    assert FT.TickBatcher is V.TickBatcher and FT.PrivateBatcher64 is V.PrivateBatcher64 and FT.build_target_encoder is M.build_target_encoder
    assert FT.describe is M.describe and FT.PRIVATE_LAYOUT == C.PRIVATE_LAYOUT
    for s in (cont, priv):                                                 # _best.pt saved and finally loaded; _gainsel_best.pt saved
        assert s.count('ckpt_prefix + "_best.pt"') == 2 and s.count('ckpt_prefix + "_gainsel_best.pt"') == 1
        assert s.count("            if ep + 1 < epochs:\n") == 1 and "% 20" not in s and s.count("best_gainsel=list(best_gs)") == 1
    back = {"fit_continuous": cont, "fit_private": priv}
    for fn, _, a, b in reversed(GEN.SUBSTITUTIONS):
        assert back[fn].count(b) == 1
        back[fn] = back[fn].replace(b, a, 1)
    assert back == GEN.function_sources(GEN.read_source())


def test_shared_head_builds_the_envelope_head_only(fx, man):
    """§2.12 item 3: SharedFixedHead(sigma, P) of the envelope target; the rich block's projection files are never opened (a
    missing or altered rich file cannot fail an envelope target unit), while every envelope check of fixed_heads still holds."""
    stats = FT.manifest_standardiser(man)
    head = FT.shared_head(man, stats, C.N_TGT, TT.D)
    full = M.fixed_heads(man, V.manifest_root(man))
    assert set(full) == {"env", "ss", "sc"} and man.get("rich")             # the fixture manifest has the rich block
    assert torch.equal(head.P, full["env"].P) and torch.equal(head.std.sd, full["env"].std.sd) and not head.std.mu.any()
    assert not any(p.requires_grad for p in head.parameters())             # a fixed head: nothing of it trains
    for k, change in (("P_ss", {"file": "absent_dir/{base}"}), ("P_sc", {"sha256": "0" * 64})):
        broken = copy.deepcopy(dict(man))
        e = broken["rich"][k]
        e.update({f: v.format(base=os.path.basename(e["file"])) for f, v in change.items()})
        bm = V.Manifest(broken, None, None, man.root)
        with pytest.raises((ValueError, FileNotFoundError, OSError)):
            M.fixed_heads(bm, man.root)                                       # the full builder reads the rich files
        assert torch.equal(FT.shared_head(bm, stats, C.N_TGT, TT.D).P, head.P)
    bad = copy.deepcopy(dict(man))
    bad["projection"]["sha256"] = "1" * 64                                    # the envelope P check is kept
    with pytest.raises(ValueError):
        FT.shared_head(V.Manifest(bad, None, None, man.root), stats, C.N_TGT, TT.D)
    with pytest.raises(ValueError):
        FT.shared_head(man, (stats[0], stats[1] * 2), C.N_TGT, TT.D)          # sigma must be the manifest's


# ---------------------------------------------------------------------------------------------------------- strict donor loading
def test_strict_donor_loading_public_and_private(fx, man, tmp_path, monkeypatch):
    built = []
    real = FT.build_target_encoder

    def spy(row, layout, manifest, state):
        enc = real(row, layout, manifest, state)
        built.append({k: v.detach().clone() for k, v in enc.state_dict().items()})
        return enc

    monkeypatch.setattr(FT, "build_target_encoder", spy)
    g = group_row(fx, "fau")
    st = donor_state(fx, "fau")
    row = target_row(fx, "fau", 1, 0, "AP", g)
    log = {}
    enc, head, bt = FT.fit_continuous_p33(TT.bind(row, 1), V.target_view("fau", 0, man), "cpu", str(tmp_path / "fau"), log, manifest=man,
                                          donor_state={"enc": st})
    tm = enc.tensor_map
    assert tm["strict"] and tm["new"] == tm["missing"] == tm["mismatched"] == tm["dropped"] == [] and tm["loaded"] == sorted(st)
    assert tm["opened_rows"] == man["coverage"]["fau"]["unseen"] == ["F9", "F10"] and log["encoder"]["tensor_map"] is tm
    opened = [C.VOCAB_INDEX[n] for n in tm["opened_rows"]]
    for k, v in st.items():                                                 # the encoder starts as the donor (opened rows aside)
        exp = v.clone()
        if k == "spatial.seen":
            exp[opened] = True
        assert torch.equal(built[0][k], exp), k
    assert (built[0]["spatial.W"][opened] == 0).all() and (enc.spatial.W[opened] != 0).any()      # opened at 0, then trained
    assert log["encoder"]["n_tokens"] == 36 and log["encoder"]["fs"] == 64 and log["encoder"]["layout"] == list(C.MONTAGES["fau"])
    bad_pos, bad_extra = dict(st), dict(st)
    bad_pos["branches.0.pos"] = torch.zeros(25, 32)                         # the 128 Hz lag grid
    bad_extra["extra.weight"] = torch.zeros(3)
    native = build_encoder("lag_local_tokens", 31, 32, [(0, 76)], 128).state_dict()
    for state, word in ((bad_pos, "strict load refused"), (bad_extra, "strict load refused"), (donor_state(fx, "dtu"), "seen set"),
                        (native, "not a SharedEncoder state")):
        with pytest.raises(ValueError, match=word):
            TT.adapt_public(row, man, "cpu", str(tmp_path / "refused"), {}, {"enc": state}, epochs=1)
    with pytest.raises(ValueError):                                         # donor arm without a donor / scratch arm with one
        TT.adapt_public(row, man, "cpu", str(tmp_path / "none"), {}, None, epochs=1)
    with pytest.raises(ValueError):
        TT.adapt_public(target_row(fx, "fau", 1, 0), man, "cpu", str(tmp_path / "scr"), {}, {"enc": st}, epochs=1)
    # private: 36 tokens at 64 Hz on the 20-name layout, every name seen by the donor union (nothing opened)
    pg = group_row(fx, "private_bdf")
    pst = donor_state(fx, "private_bdf")
    prow = target_row(fx, "private_bdf", 0, None, "XP", pg)
    kids = V.load_private64(synthetic_kids())
    plog = {}
    penc, pbt, protos = FT.fit_private_p33(TT.bind(prow, 1), kids, "cpu", str(tmp_path / "priv"), plog, manifest=man, donor_state=pst)
    ptm = penc.tensor_map
    assert ptm["strict"] and ptm["new"] == ptm["missing"] == ptm["opened_rows"] == [] and ptm["coverage"]["n_seen"] == 20
    assert all(torch.equal(built[-1][k], v) for k, v in pst.items())
    assert penc.layout == C.PRIVATE_LAYOUT and penc.n_tokens == 36 and plog["encoder"]["fs"] == 64
    assert plog["windows_samples_from_epoch_start"] == [[32, 70]] and protos.shape == (2, 32)
    with pytest.raises(ValueError, match="seen set"):
        FT.fit_private_p33(TT.bind(prow, 1), kids, "cpu", str(tmp_path / "priv2"), {}, manifest=man, donor_state=st)


# ---------------------------------------------------------------------------------------------------------- outer test never used
def _public_perturbation(man, ds, sf, cf):
    """A target_view wrapper that replaces by noise every EEG column outside the cell's training participants' fit / es
    single-talker pieces, and every envelope sample outside the fit / es single-talker streams."""
    _, items = V.cohort_table(man, ds)
    cell = V.manifest_cell(man, ds, sf, cf)
    content = cell["content"]["ss"] if ds == "fau" else cell["content"]
    keep_stim, train = set(map(str, content["fit"])) | set(map(str, content["es"])), set(map(str, cell["train"]))
    cols = [(it["row_offset"], it["row_offset"] + it["T_eeg"]) for it in items if it.get("row_offset") is not None
            and str(it["participant"]) in train and it["kind"] == "ss" and str(it["stimulus"]) in keep_stim]
    keep_streams = {p["stream"] for p in man["presentations"] if p["cohort"] == ds and p["kind"] == "ss" and str(p["stimulus"]) in keep_stim}
    streams, real = V.cohort_streams(man, ds), V.target_view

    def view(cohort, cfold, manifest, mode="A", root=None):
        coh = real(cohort, cfold, manifest, mode, root)
        rng = np.random.default_rng(99)
        keep = np.zeros(coh.eeg.shape[1], bool)
        for a, b in cols:
            keep[a:b] = True
        coh.eeg[:, ~keep] = (5 * rng.standard_normal((coh.eeg.shape[0], int((~keep).sum())))).astype(np.float16)
        env, ke = coh.stim["envelope"], np.zeros(coh.stim["envelope"].shape[1], bool)
        for s in streams:
            if s["stream"] in keep_streams:
                ke[s["offset"]:s["offset"] + s["length"]] = True
        env[:, ~ke] = rng.standard_normal((1, int((~ke).sum()))).astype(np.float32)
        view.n_eeg, view.n_env = int((~keep).sum()), int((~ke).sum())
        return coh
    return view


def test_outer_test_never_used_in_fitting_or_selection(fx, man, tmp_path, monkeypatch):
    row = target_row(fx, "fau", 0, 0)
    runs = {}
    for tag in ("clean", "perturbed"):
        if tag == "perturbed":
            monkeypatch.setattr(V, "target_view", _public_perturbation(man, "fau", 0, 0))
        log, ck = {}, str(tmp_path / f"pub_{tag}")
        runs[tag] = (TT.adapt_public(row, man, "cpu", ck, log, None, epochs=6), log, ck)
    (rc, lc, cc), (rp, lp, cp) = runs["clean"], runs["perturbed"]
    assert V.target_view.n_eeg > 0 and V.target_view.n_env > 0
    assert _no_seconds(lc["curve"]) == _no_seconds(lp["curve"]) and lc["objective_calibration"] == lp["objective_calibration"]
    assert (lc["best_epoch"], lc["best_epoch_gainsel"], lc["optimizer_steps"]) == (lp["best_epoch"], lp["best_epoch_gainsel"], lp["optimizer_steps"])
    for k in TT.CKPT.values():
        assert _same_tensors(_tensors(cc + k), _tensors(cp + k)), k
    ea, eb = rc["eval"], rp["eval"]
    assert ea["readout"]["alpha_unified"] == eb["readout"]["alpha_unified"] and ea["readout"]["tau"] == eb["readout"]["tau"]  # training side
    assert sorted(ea["per_participant"]) == sorted(eb["per_participant"]) == sorted(map(str, V.manifest_cell(man, "fau", 0, 0)["test"]))
    assert any(ea["per_participant"][p] != eb["per_participant"][p] for p in ea["per_participant"])   # it did reach the outer test
    assert set(rc["coverage"]["training_access"]["train_participants"]) == set(map(str, V.manifest_cell(man, "fau", 0, 0)["train"]))
    # private: the test children's input and labels perturbed after load_private64
    prow, sf = target_row(fx, "private_bdf", 1, None), 1
    real = V.load_private64
    runs = {}
    for tag in ("clean", "perturbed"):
        def lp64(kids=None, tag=tag):
            kids = real(kids)
            if tag == "perturbed":
                r = np.random.default_rng(5)
                for k in kids:
                    if k["fold"] == sf:
                        k["x64"] = (4 * r.standard_normal(k["x64"].shape)).astype(np.float32); k["y"] = 1 - k["y"]
            return kids
        monkeypatch.setattr(V, "load_private64", lp64)
        log, ck = {}, str(tmp_path / f"priv_{tag}")
        runs[tag] = (TT.adapt_private(prow, man, "cpu", ck, log, None, epochs=6, kids=synthetic_kids()), log, ck)
    (rc, lc, cc), (rp, lp, cp) = runs["clean"], runs["perturbed"]
    assert _no_seconds(lc["curve"]) == _no_seconds(lp["curve"]) and lc["objective_calibration"] == lp["objective_calibration"]
    for k in TT.CKPT.values():
        assert _same_tensors(_tensors(cc + k), _tensors(cp + k)), k
    pa, pb = rc["eval"]["per_participant"], rp["eval"]["per_participant"]
    assert sorted(pa) == sorted(pb) == sorted(map(str, V.manifest_cell(man, "private_bdf", sf, 0)["test"]))
    assert any(pa[c] != pb[c] for c in pa)


# ---------------------------------------------------------------------------------------------------------- both checkpoints
def _interrupted(fit, monkeypatch, at=5):
    real = FT._save_resume

    def save(path, **kw):
        real(path, **kw)
        if kw["epoch"] == at:
            raise Preempted(path)
    monkeypatch.setattr(FT, "_save_resume", save)
    try:
        with pytest.raises(Preempted):
            fit()
    finally:
        monkeypatch.setattr(FT, "_save_resume", real)


def test_both_checkpoints_rules_and_exact_resume(fx, man, tmp_path, monkeypatch):
    row = target_row(fx, "fau", 2, 1)
    b = TT.bind(row, 10)
    for path in ("public", "private"):
        if path == "public":
            def fit(ck, log):
                return FT.fit_continuous_p33(b, V.target_view("fau", 1, man), "cpu", ck, log, manifest=man, donor_state=None)
        else:
            pb = TT.bind(target_row(fx, "private_bdf", 3, None), 10)

            def fit(ck, log):
                return FT.fit_private_p33(pb, V.load_private64(synthetic_kids()), "cpu", ck, log, manifest=man, donor_state=None)
        ref, ck = {}, str(tmp_path / f"{path}_ref")
        fit(ck, ref)
        curve = ref["curve"]
        es, gs = [c["es_loss"] for c in curve], [c["selection_score"] for c in curve]
        assert [c["epoch"] for c in curve] == [5, 10] and all(c["selection_score"] == c["es_loss"] - c["es_loss_mismatched"] for c in curve)
        assert (ref["best_epoch"], ref["best_es_loss"]) == (curve[int(np.argmin(es))]["epoch"], min(es))
        assert (ref["best_epoch_gainsel"], ref["best_selection_score_gainsel"]) == (curve[int(np.argmin(gs))]["epoch"], min(gs))
        assert ref["selection_curves"] == {"primary": "curve[].es_loss", "gainsel": "curve[].selection_score"}
        assert os.path.exists(ck + "_best.pt") and os.path.exists(ck + "_gainsel_best.pt") and not os.path.exists(ck + "_resume.pt")
        same = ref["best_epoch"] == ref["best_epoch_gainsel"]
        assert _same_tensors(_tensors(ck + "_best.pt"), _tensors(ck + "_gainsel_best.pt")) == same
        ck2, log2 = str(tmp_path / f"{path}_resumed"), {}
        _interrupted(lambda: fit(ck2, {}), monkeypatch)                    # preempted right after the epoch-5 resume save
        assert os.path.exists(ck2 + "_resume.pt") and set(torch.load(ck2 + "_resume.pt", weights_only=False)) >= {"best", "best_gainsel"}
        fit(ck2, log2)
        assert log2["resumed_from_epoch"] == 5 and _no_seconds(log2["curve"]) == _no_seconds(curve)
        assert all(log2[k] == ref[k] for k in ("best_epoch", "best_epoch_gainsel", "best_es_loss", "best_selection_score_gainsel", "optimizer_steps"))
        for k in TT.CKPT.values():
            assert _same_tensors(_tensors(ck + k), _tensors(ck2 + k)), (path, k)


def test_adapt_evaluates_both_checkpoints(fx, man, tmp_path, monkeypatch):
    """When the two rules chose different epochs both checkpoints are evaluated (eval from _best.pt, eval_gainsel from
    _gainsel_best.pt); forced here by replacing the gain-selected file after training."""
    real = FT.fit_continuous_p33

    def forced(b, coh, dev, ck, log, **kw):
        out = real(b, coh, dev, ck, log, **kw)
        assert log["best_epoch"] == log["best_epoch_gainsel"] == 5             # one validation: the rules agree
        sd = torch.load(ck + "_gainsel_best.pt")
        g = torch.Generator().manual_seed(0)
        sd["enc"] = {k: v + 0.2 * torch.randn(v.shape, generator=g) if v.is_floating_point() else v for k, v in sd["enc"].items()}
        torch.save(sd, ck + "_gainsel_best.pt")
        log["best_epoch_gainsel"] = 4
        return out

    monkeypatch.setattr(FT, "fit_continuous_p33", forced)
    log = {}
    res = TT.adapt_public(target_row(fx, "dtu", 0, 1), man, "cpu", str(tmp_path / "forced"), log, None, epochs=5)
    assert res["gainsel"] == "evaluated" and isinstance(res["eval_gainsel"], dict) and not res["selection"]["identical"]
    assert res["selection"]["sensitivity"]["epoch"] == 4 and res["checkpoints"]["gainsel"]["epoch"] == 4
    a, b = res["eval"]["per_participant"], res["eval_gainsel"]["per_participant"]
    assert sorted(a) == sorted(b) and any(a[p] != b[p] for p in a)          # (the easy synthetic unified retrieval may saturate)
    assert res["eval"]["readout"]["n_test_candidates"] == res["eval_gainsel"]["readout"]["n_test_candidates"]


def test_selection_status_identical_evaluated_unavailable(tmp_path):
    """gainsel status from the two best epochs; "unavailable" (no finite gain-rule score: no _gainsel_best.pt) keeps the primary."""
    ck = str(tmp_path / "u")
    with open(ck + "_best.pt", "wb") as f:
        f.write(b"primary")
    log = {"best_epoch": 5, "best_es_loss": 1.0, "best_epoch_gainsel": -1, "best_selection_score_gainsel": float("inf"), "selection_curves": None}
    st, sel = TT._selection(log, ck)
    assert st == "unavailable" and sel["sensitivity"]["checkpoint"] is None and not sel["identical"]
    cks = TT._checkpoints(ck, log, st)
    assert cks["gainsel"] is None and cks["best"] == {"file": "u_best.pt", "epoch": 5, "sha256": hashlib.sha256(b"primary").hexdigest()}
    log["best_epoch_gainsel"] = 5
    st, sel = TT._selection(log, ck)
    assert st == "identical" and sel["identical"]
    with pytest.raises(FileNotFoundError):
        TT._checkpoints(ck, log, st)                                        # a rule that chose an epoch must have written its file
    with open(ck + "_gainsel_best.pt", "wb") as f:
        f.write(b"gain")
    log["best_epoch_gainsel"] = 10
    st, sel = TT._selection(log, ck)
    assert st == "evaluated" and TT._checkpoints(ck, log, st)["gainsel"]["epoch"] == 10 and sel["sensitivity"]["epoch"] == 10


class NanMismatch(L.ContractObjective):
    """Every second loss computed without gradients is NaN. In the generated copy's validation each early-stopping set is
    evaluated with the training pairing and then rolled, so es_loss stays finite while es_loss_mismatched, hence the gain-rule
    score, is NaN at every validation: the gain rule never has a finite score."""
    calls = 0

    def __call__(self, u, v=None, keys=None, labels=None, prototypes=None):
        loss, st = super().__call__(u, v, keys=keys, labels=labels, prototypes=prototypes)
        if torch.is_grad_enabled():
            return loss, st
        NanMismatch.calls += 1
        return (loss * float("nan") if NanMismatch.calls % 2 == 0 else loss), st


def test_gainsel_unavailable_end_to_end(fx, man, tmp_path, monkeypatch, registered):
    """No finite gain-rule score: the generated copy writes no _gainsel_best.pt, the primary result stands, run_target records
    gainsel "unavailable" with no eval_gainsel, and the analysis reads the unit with its primary view (gainsel view absent)."""
    monkeypatch.setattr(FT, "ContractObjective", NanMismatch)
    out, row = str(tmp_path / "out"), target_row(fx, "dtu", 2, 0)
    RT.run(row, out, epochs=10, device="cpu", manifest_path=fx["manifest_path"], rows=[row])
    with open(os.path.join(out, "units", f"{row['experiment_id']}.json")) as f:
        rec = json.load(f)
    ck = os.path.join(out, "ckpt", row["experiment_id"])
    assert NanMismatch.calls > 0 and rec["status"] == "complete" and rec["gainsel"] == "unavailable" and "eval_gainsel" not in rec
    assert [c["epoch"] for c in rec["curve"]] == [5, 10] and all(np.isnan(c["selection_score"]) and np.isfinite(c["es_loss"]) for c in rec["curve"])
    assert rec["best_epoch"] in (5, 10) and rec["best_epoch_gainsel"] == -1 and rec["best_selection_score_gainsel"] == float("inf")
    assert os.path.exists(ck + "_best.pt") and not os.path.exists(ck + "_gainsel_best.pt") and not os.path.exists(ck + "_resume.pt")
    assert rec["checkpoints"]["gainsel"] is None and rec["checkpoints"]["best"]["sha256"] == TT.file_sha256(ck + "_best.pt")
    sel = rec["selection"]
    assert sel["status"] == "unavailable" and sel["sensitivity"]["checkpoint"] is None and not sel["identical"]
    assert sel["primary"]["epoch"] == rec["best_epoch"] and rec["eval"]["readout"]["n_test_candidates"]
    u = A.normalise(row, rec, None, None)
    assert u["status"] == "probe_truncated" and u["views"]["primary"]["rows"] and u["view_status"].get("gainsel") == "absent"


# ---------------------------------------------------------------------------------------------------------- run_target records
def test_tiny_cpu_runs_write_valid_records(fx, man, tmp_path, registered, monkeypatch):
    out = str(tmp_path / "out")
    g, pg, pgc = group_row(fx, "fau"), group_row(fx, "private_bdf"), group_row(fx, "private_bdf", obj="CS_SINGLE")
    states = {m: donor_state(fx, "fau", 3401 + i) for i, m in enumerate(SEL.group_members(g))}
    grec = write_group(out, g, states, ce={"J1": 2.0, "J025": 1.5}, m5=("J025",))   # the lambda rule picks J025
    pgrec = write_group(out, pg, {"XP": donor_state(fx, "private_bdf")})
    pgcrec = write_group(out, pgc, {"AP": donor_state(fx, "private_bdf", 3402)})
    tj, ts = target_row(fx, "fau", 0, 0, "J*", g), target_row(fx, "fau", 0, 0)
    tp = target_row(fx, "private_bdf", 2, None, "XP", pg)
    tcs, tpcs = target_row(fx, "dtu", 4, 0, obj="CS_SINGLE"), target_row(fx, "private_bdf", 0, None, obj="CS_SINGLE")
    tpcd = target_row(fx, "private_bdf", 1, None, "AP", pgc, obj="CS_SINGLE")         # a private CS_SINGLE donor arm
    rows = [g, pg, pgc, tj, ts, tp, tcs, tpcs, tpcd]
    kw = {"device": "cpu", "manifest_path": fx["manifest_path"], "rows": rows}
    members = {id(tj): "J025", id(ts): None, id(tp): "XP", id(tcs): None, id(tpcs): None, id(tpcd): "AP"}
    slots = {id(tj): "J*", id(ts): "S", id(tp): "XP", id(tcs): "S", id(tpcs): "S", id(tpcd): "AP"}
    loaded = []
    monkeypatch.setattr(core, "load_rows", lambda: loaded.append(1) or rows)          # as run.py points it at plan + plan_ext
    for row, group, ep in ((tj, (g, grec), 2), (ts, None, 2), (tp, (pg, pgrec), 2), (tcs, None, 1), (tpcs, None, 1),
                           (tpcd, (pgc, pgcrec), 1)):
        private, nce = row["dataset"] == "private_bdf", row["spec"]["objective"] == "NCE"
        RT.run(row, out, epochs=ep, kids=synthetic_kids() if private else None,
               **{**kw, "rows": None if row is tj else rows})                         # J*: the rows=None path (core.load_rows)
        with open(os.path.join(out, "units", f"{row['experiment_id']}.json")) as f:
            rec = json.load(f)
        ck = os.path.join(out, "ckpt", row["experiment_id"])
        assert rec["status"] == "complete" and rec["code_group"] == "prior33_target" and rec["code_hash"] == core.code_hash(SEL.TARGET)
        assert rec["runner"] == "auditory_alignment_v3" and rec["row"] == row and rec["bound_row"]["spec"]["epochs"] == ep == rec["epochs_override"]
        assert rec["mode"] == "T" and rec["input_mode"] == (V.PRIVATE_INPUT if private else "A")
        assert rec["stage"] == "target" and rec["execution_contract"] == C.CONTRACT
        assert rec["manifest_sha256"] == fx["manifest_sha256"] and rec["split_hash"] == row["spec"]["split_hash"]
        assert rec["target_contract"] == ("current_class" if private else man["target_contract"])
        assert rec["selection_level"] == TT.SELECTION_LEVEL["private" if private else "public"]
        assert rec["member_resolved"] == members[id(row)] and rec["resolved_config"]["objective"] == row["spec"]["objective"]
        assert rec["gainsel"] in ("identical", "evaluated") and ("eval_gainsel" in rec) == (rec["gainsel"] == "evaluated")
        assert rec["selection"]["identical"] == (rec["gainsel"] == "identical") and rec["fit_target"]["ok"]
        assert rec["fit_target"]["substitutions"] == list(FT.SUBSTITUTIONS) and f"fit_continuous: {CADENCE}" in rec["fit_target"]["engineering_substitutions"]
        for k, f in (("best", "_best.pt"), ("gainsel", "_gainsel_best.pt")):
            assert rec["checkpoints"][k]["sha256"] == TT.file_sha256(ck + f)
        assert not os.path.exists(ck + "_resume.pt") and rec["view_sha256"] and rec["pool_sha256"] and rec["normalisation_access"]
        assert rec["tensor_map"]["strict" if group else "init"] in (True, "random") and rec["coverage"]["channels"]["init"] == rec["init"]
        assert rec["resolved_config"]["nce"] == (None if not nce else ("prototype_nce (auditory_alignment.train.Objective)" if private else L.NCE_TAG))
        sc = rec["schedule_check"]
        assert sc["cosine_t_max"] == rec["epochs_completed"] * rec["steps_per_epoch"] and sc["optimizer_steps"] == rec["optimizer_steps"]
        assert sc["realised_over_scheduled"] == rec["optimizer_steps"] / sc["cosine_t_max"] and sc["wrapped"] == (sc["realised_over_scheduled"] > 1)
        decl = rec["declarations"]
        if group:
            dep = rec["dependency"]
            assert dep["donor_group"] == group[0]["experiment_id"] and dep["member"] == rec["member_resolved"]
            assert dep["checkpoint"] == os.path.relpath(SEL.member_ckpt(out, dep["donor_group"], dep["member"]), out)
            assert dep["checkpoint_sha256"] == TT.file_sha256(SEL.member_ckpt(out, dep["donor_group"], dep["member"]))
            assert dep["checkpoint_format"] == (RT.CKPT_FORMAT if row is tj else None)
            assert any(d.startswith(f"the full encoder is loaded strictly from member {dep['member']}") for d in decl)
        else:
            assert rec["dependency"] is None and any("target_from_scratch" in d for d in decl)
        if private:                                       # no envelope coordinates and no external sound statistics declared
            assert rec["envelope_target_contract"] == man["target_contract"] and "native_calibration" in rec["eval"]
            assert rec["encoder"]["layout"] == list(C.PRIVATE_LAYOUT) and rec["encoder"]["n_tokens"] == 36
            assert rec["trainable"]["prototypes"] == (64 if nce else 0) and ("prototypes" in rec["class_head"]) == nce
            assert not any("shared target coordinates" in d or "SparrKULee donor fit" in d or d.startswith("target-stage") for d in decl)
            assert any("does not apply to the private path" in d for d in decl)
            assert any("uses no external sound statistics" in d for d in decl) == (group is None)
            assert any("the class head is new" in d for d in decl) == (group is not None)
        else:
            cf = row["content_fold"]
            assert rec["eval"]["readout"]["n_test_candidates"] == len(V.pool_of(V.target_view(row["dataset"], cf, man), "test", "ss")[1])
            assert rec["objective_calibration"]["sigma_v"] is not None and any("shared target coordinates" in d for d in decl)
            assert any("(external sound statistics)" in d for d in decl) == (group is None)
            assert any(d.startswith(f"target-stage NCE {L.NCE_TAG}") for d in decl) == nce
            assert any(d.startswith("target-stage CS_SINGLE") for d in decl) == (not nce)
            assert any("do not apply to this CS_SINGLE row" in d for d in decl) == (not nce)
            if nce:
                assert rec["objective_calibration"]["nce"] == L.NCE_TAG
        u = A.normalise(row, rec, None, group)                              # the M11 analysis reads the record
        assert u["status"] == "probe_truncated" and u["level_status"] == "as declared" and u["views"]["primary"]["rows"]
        assert u["view_status"]["gainsel"] == rec["gainsel"] and u["record_target_contract"] == rec["target_contract"]
        assert u["member_check"] == (None if group is None else "agrees") and u["slot"] == slots[id(row)]
        assert u["mode"] == "T" and u["target_seed"] == 3401 and u["donor_seed"] == (3401 if group else None)
        if private:
            assert all({"NLL", "AUC"} <= set(v) for v in u["views"]["primary"]["rows"].values())
    assert loaded                                                            # the J* unit resolved its group through core.load_rows

    def failed(row, **extra):
        with pytest.raises(SystemExit):
            RT.run(row, out, epochs=1, **{**kw, **extra})
        p = os.path.join(out, "units", f"{row['experiment_id']}.FAILED.json")
        assert not os.path.exists(p.replace(".FAILED.json", ".json"))
        with open(p) as f:
            rec = json.load(f)
        assert rec["status"] == "technical_failed" and rec["traceback"] and rec["experiment_id"] == row["experiment_id"]
        assert rec["card"] == RT.CARD and rec["stage"] == "target" and rec["row"] == row
        return rec["error"]

    g2 = group_row(fx, "dtu")                                               # a donor group without a record
    assert "dependency" in failed(target_row(fx, "dtu", 0, 0, "AP", g2), rows=rows + [g2])
    write_group(out, g2, {})                                                # ... with a record but no member checkpoint
    assert "checkpoint" in failed(target_row(fx, "dtu", 1, 0, "XM", g2), rows=rows + [g2])
    assert "sha256" in failed(target_row(fx, "fau", 1, 0, manifest_sha256="0" * 64))
    assert "target_seed" in failed(target_row(fx, "fau", 1, 0, target_seed=3407))
    assert "split_hash" in failed(target_row(fx, "fau", 1, 0, split_hash="1" * 64))
    assert "target_contract" in failed(target_row(fx, "fau", 1, 1, target_contract="2" * 64))
    assert "spec.epochs" in failed(target_row(fx, "fau", 1, 1, epochs=100))          # the equal-budget guard (§2.12, §4.3)
    assert "spec.train_population" in failed(target_row(fx, "fau", 2, 1, train_population="TH_ONLY"))
    bad = dict(states["AP"])
    bad["branches.0.pos"] = torch.zeros(25, 32)
    torch.save({"enc": bad}, SEL.member_ckpt(out, g["experiment_id"], "AP"))
    assert "strict load refused" in failed(target_row(fx, "fau", 1, 0, "AP", g))
    write_group(out, g, {"XM": states["XM"]}, ce={"J1": 2.0, "J025": 1.5}, m5=("XM",))
    ck = torch.load(SEL.member_ckpt(out, g["experiment_id"], "XM"))
    torch.save({**ck, "member": "XP"}, SEL.member_ckpt(out, g["experiment_id"], "XM"))   # a checkpoint of another member
    assert "does not belong" in failed(target_row(fx, "fau", 2, 0, "XM", g))
    # failures of TT.bind and core.new_record are records too (§6.1), not exceptions escaping the runner
    nofold = target_row(fx, "fau", 3, 0)
    del nofold["subject_fold"]
    err = failed(nofold)
    assert "KeyError" in err and "subject_fold" in err
    unreg = {**target_row(fx, "fau", 3, 1), "family_id": SEL.TARGET + "_UNREGISTERED"}
    assert "KeyError" in failed(unreg)
    with open(os.path.join(out, "units", f"{unreg['experiment_id']}.FAILED.json")) as f:
        rec = json.load(f)
    assert rec["code_group"] is None and rec["code_hash"] is None and rec["bound_row"]["subject_fold"] == 3
    with open(os.path.join(out, "units", f"{nofold['experiment_id']}.FAILED.json")) as f:
        rec = json.load(f)
    assert rec["code_group"] == "prior33_target" and rec["code_hash"] == core.code_hash(SEL.TARGET) and rec["bound_row"] is None


# ---------------------------------------------------------------------------------------------------------- run_donor -> run_target
def real_group_row(fx, man, target="fau", objective="NCE", seed=3401):
    """A core donor-group row as M9 registers it (§4.3), for run_donor.run on the real stack."""
    b = man["budget"]
    spec = {"logical_family": RT.LOGICAL_FAMILY, "card": RT.CARD, "execution_contract": C.CONTRACT, "manifest_sha256": fx["manifest_sha256"],
            "stage": "donor_group", "block": "core", "queue_tier": 1, "seed_scope": "breadth", "donor_seed": seed, "sampler_seed": seed,
            "target_seed": None, "objective": objective, "target": "envelope", "target_contract": man["target_contract"],
            "members": list(SEL.GROUP_MEMBERS[SEL.DONOR]), "donor_set": target, "batch": dict(DT.BATCH),
            "budget": {"epoch_equivalents": 30, "anchors_per_ep_eq": b["anchors_per_ep_eq"], "steps0": b["S0"],
                       "continuation": "group_wsd_any_last3_ext10_limit60_v1"},
            "optimizer": dict(DT.OPTIMIZER), "temperature": 0.1, "bandwidth_multiplier": 1.0, "selection": dict(DT.SELECTION),
            "lambda_rule": SEL.LAMBDA_RULE, "montage_augmentation": DT.MONTAGE_AUG, "control": DT.CONTROL, **GEOM}
    return {"experiment_id": _eid("RG", target, objective, seed), "family_id": SEL.DONOR, "dataset": target, "subject_fold": None,
            "content_fold": None, "seed": seed, "spec": spec, "logical_dependencies": ["frozen_manifest"], "job_kind": "train"}


def small_selection_sets(orig, n_fit=6, n_dev=8, n_cal=8):
    """Speed only: the donor stage's fixed sets with their first fit segments and dev / bridge_cal queries (candidates unchanged),
    as test_donor_train.py shortens CPU validations (17 s instead of about 2 min for max_steps 3 on the scale-4 fixture)."""
    def small(man):
        ss = orig(man)
        dev, cal = ss["dev"], ss["bridge_cal"]
        kd, kc = np.arange(min(n_dev, len(dev["queries"]))), np.arange(min(n_cal, len(cal["queries"])))
        return {**ss, "fit": ss["fit"].take(np.arange(min(n_fit, len(ss["fit"])))),
                "dev": {"queries": dev["queries"].take(kd), "candidates": dev["candidates"], "own": dev["own"][kd], "other": dev["other"][kd]},
                "bridge_cal": {**cal, "queries": cal["queries"].take(kc), "own": cal["own"][kc], "fold": cal["fold"][kc]}}
    return small


def test_run_donor_member_checkpoints_feed_run_target(tmp_path, monkeypatch, registered):
    """The real chain on the scale-4 fixture (the §2.6 donor batch needs it): run_donor.run trains a core group (max_steps 3) and
    writes its members in donor_train.py's checkpoint format; run_target then runs S, AP, J* and XM of FAU sf0 cf0. Each donor
    arm reads its member checkpoint (format prior33_donor_member_v1, provenance checked), starts exactly from its encoder state
    (the target montage's donor-unseen rows opened at 0), J* resolves by the lambda rule on the group record, the analysis's
    member check agrees, and the four arms train with identical budgets."""
    fx4 = make_synthetic_manifest(str(tmp_path / "fx4"), scale=4)
    man4 = V.open_manifest(fx4["manifest_path"], fx4["manifest_sha256"])
    monkeypatch.setattr(SM, "selection_sets", small_selection_sets(SM.selection_sets))
    monkeypatch.setitem(core.FAMILY_CODE, "prior33_donor", P33_DONOR_FILES)
    monkeypatch.setitem(core.FAMILY_GROUP, SEL.DONOR, "prior33_donor")
    out, g = str(tmp_path / "out"), real_group_row(fx4, man4)
    RD.run(g, out, epochs=3, manifest=man4, device="cpu")
    with open(SEL.record_path(out, g["experiment_id"])) as f:
        grec = json.load(f)
    assert grec["status"] == "complete" and grec["truncated"]["max_steps"] == 3 and grec["joint_choice"]["member"] in SEL.JOINT_CANDIDATES
    arms = {a: target_row(fx4, "fau", 0, 0, None if a == "S" else a, None if a == "S" else g) for a in ("S", "AP", "J*", "XM")}
    rows = [g, *arms.values()]
    starts, real = [], FT.build_target_encoder

    def spy(row, layout, manifest, state):
        enc = real(row, layout, manifest, state)
        starts.append({k: v.detach().clone() for k, v in enc.state_dict().items()})
        return enc

    monkeypatch.setattr(FT, "build_target_encoder", spy)
    budgets = {}
    for arm, row in arms.items():
        RT.run(row, out, epochs=1, device="cpu", manifest_path=fx4["manifest_path"], rows=rows)
        with open(os.path.join(out, "units", f"{row['experiment_id']}.json")) as f:
            rec = json.load(f)
        assert rec["status"] == "complete" and rec["slot"] == arm
        if arm == "S":
            assert rec["dependency"] is None and rec["member_resolved"] is None
        else:
            member = SEL.member_of(row, grec) if arm == "J*" else arm
            dep, tm = rec["dependency"], rec["tensor_map"]
            assert rec["member_resolved"] == dep["member"] == member and (arm != "J*" or member == grec["joint_choice"]["member"])
            assert dep["checkpoint_format"] == RT.CKPT_FORMAT and dep["donor_code_hash"] == grec["code_hash"] and dep["donor_status"] == "complete"
            path = SEL.member_ckpt(out, g["experiment_id"], member, "best")
            assert dep["checkpoint"] == os.path.relpath(path, out) and dep["checkpoint_sha256"] == TT.file_sha256(path)
            saved = torch.load(path, map_location="cpu", weights_only=True)
            assert (saved["format"], saved["group"], saved["member"], saved["kind"]) == (RT.CKPT_FORMAT, g["experiment_id"], member, "best")
            assert tm["strict"] and tm["new"] == tm["missing"] == tm["mismatched"] == [] and tm["opened_rows"] == man4["coverage"]["fau"]["unseen"]
            assert 0.99 < tm["loaded_param_fraction"] < 1 and tm["n_params_opened"] > 0
            opened = [C.VOCAB_INDEX[n] for n in tm["opened_rows"]]
            for k, v in saved["enc"].items():                                # the target stage starts from the member's state
                exp = v.clone()
                if k == "spatial.seen":
                    exp[opened] = True
                if k == "spatial.W":
                    exp[opened] = 0
                assert torch.equal(starts[-1][k], exp), (arm, k)
        u = A.normalise(row, rec, None, None if arm == "S" else (g, grec))
        assert u["status"] == "probe_truncated" and u["member_check"] == (None if arm == "S" else "agrees") and u["views"]["primary"]["rows"]
        budgets[arm] = (rec["epochs_completed"], rec["optimizer_steps"], rec["steps_per_epoch"], rec["n_fit_segments"], rec["n_es_segments"],
                        rec["n_train_participants"], [c["step"] for c in rec["curve"]], rec["coverage"]["n_test_query_participants"],
                        rec["schedule_check"])
    assert len(set(map(json.dumps, budgets.values()))) == 1, budgets


# ---------------------------------------------------------------------------------------------------------- equal budgets
def test_equal_budgets_across_arms(fx, man, tmp_path, monkeypatch):
    """S, AP and XM of one cell: the same epochs, batch stream (every row drawn, in order), early-stopping set, optimiser steps
    and segment counts; private S and AP: the same batches and the same prototype initialisation."""
    seen = []

    class Recording(V.TickBatcher):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self.h = hashlib.sha256(); seen.append(self)

        def rows(self, batch, rng, *a, **k):
            out = super().rows(batch, rng, *a, **k)
            self.h.update(np.concatenate([o.cpu().numpy().astype(np.int64).ravel() for o in out]).tobytes())
            return out

    rng_after_build = []
    real_build = FT.build_target_encoder

    def build(*a):
        enc = real_build(*a)
        rng_after_build.append(torch.get_rng_state().clone())
        return enc

    monkeypatch.setattr(FT, "TickBatcher", Recording)
    monkeypatch.setattr(FT, "build_target_encoder", build)
    g = group_row(fx, "fau")
    arms = {"S": (target_row(fx, "fau", 3, 1), None), "AP": (target_row(fx, "fau", 3, 1, "AP", g), {"enc": donor_state(fx, "fau", 7)}),
            "XM": (target_row(fx, "fau", 3, 1, "XM", g), {"enc": donor_state(fx, "fau", 8)})}
    budget = {}
    for arm, (row, st) in arms.items():
        b, log = TT.bind(row), {}
        assert b["spec"]["epochs"] == TT.EPOCHS == 200
        b = TT.bind(row, 2)
        FT.fit_continuous_p33(b, V.target_view("fau", 1, man), "cpu", str(tmp_path / arm), log, manifest=man, donor_state=st)
        budget[arm] = (seen[-1].h.hexdigest(), log["epochs_completed"], log["steps_per_epoch"], log["optimizer_steps"], log["n_fit_segments"],
                       log["n_es_segments"], log["n_train_participants"], [c["step"] for c in log["curve"]])
    assert len(set(map(json.dumps, budget.values()))) == 1, budget
    assert all(torch.equal(rng_after_build[0], r) for r in rng_after_build)
    gc, cbudget = group_row(fx, "dtu", obj="CS_SINGLE"), {}                  # a CS_SINGLE cell: S, XP and XM
    for arm, (row, st) in {"S": (target_row(fx, "dtu", 1, 1, obj="CS_SINGLE"), None),
                           "XP": (target_row(fx, "dtu", 1, 1, "XP", gc, obj="CS_SINGLE"), {"enc": donor_state(fx, "dtu", 10)}),
                           "XM": (target_row(fx, "dtu", 1, 1, "XM", gc, obj="CS_SINGLE"), {"enc": donor_state(fx, "dtu", 11)})}.items():
        log = {}
        FT.fit_continuous_p33(TT.bind(row, 1), V.target_view("dtu", 1, man), "cpu", str(tmp_path / f"cs{arm}"), log, manifest=man, donor_state=st)
        cbudget[arm] = (seen[-1].h.hexdigest(), log["epochs_completed"], log["steps_per_epoch"], log["optimizer_steps"], log["n_fit_segments"],
                        log["n_es_segments"], log["n_train_participants"], [c["step"] for c in log["curve"]])
    assert len(set(map(json.dumps, cbudget.values()))) == 1, cbudget
    assert all(torch.equal(rng_after_build[0], r) for r in rng_after_build)
    pg, batches, protos = group_row(fx, "private_bdf"), {}, {}
    real_batch = V.PrivateBatcher64.batch

    def batch(self, rng, *a, **k):
        x, y = real_batch(self, rng, *a, **k)
        batches.setdefault(self.tag, hashlib.sha256()).update(x[0].numpy().tobytes() + y.numpy().tobytes())
        return x, y

    monkeypatch.setattr(V.PrivateBatcher64, "batch", batch)
    for arm, row, st in (("S", target_row(fx, "private_bdf", 4, None), None),
                         ("AP", target_row(fx, "private_bdf", 4, None, "AP", pg), donor_state(fx, "private_bdf", 9))):
        monkeypatch.setattr(V.PrivateBatcher64, "tag", arm, raising=False)
        log = {}
        FT.fit_private_p33(TT.bind(row, 2), V.load_private64(synthetic_kids()), "cpu", str(tmp_path / f"p{arm}"), log, manifest=man, donor_state=st)
        protos[arm] = (rng_after_build[-1], log["optimizer_steps"], log["steps_per_epoch"], log["n_fit_trials"], log["n_train_children"])
    assert batches["S"].hexdigest() == batches["AP"].hexdigest()
    assert torch.equal(protos["S"][0], protos["AP"][0]) and protos["S"][1:] == protos["AP"][1:]   # identical prototype draw


# ---------------------------------------------------------------------------------------------------------- rows and cells
def test_rows_cells_and_refusals(fx, man):
    cells = TT.target_cells(man)
    assert len(cells) == 30 and {d: sum(c[0] == d for c in cells) for d in TT.CELL_COUNTS} == TT.CELL_COUNTS
    with pytest.raises(ValueError):
        TT.target_cells({"cells": man["cells"][:-1]})
    g = group_row(fx, "fau")
    assert TT.arm_of(target_row(fx, "fau", 0, 0)) == ("S", "random") and TT.arm_of(target_row(fx, "fau", 0, 0, "J*", g)) == ("J*", "donor")
    assert [TT.check_row(target_row(fx, "fau", 0, 0, m, g if m else None))[0] for m in (None, "AP", "XP", "J*", "XM")] == list(TT.ARMS_CORE)
    for bad in (dict(objective="FMCA"), dict(target_seed=3413), dict(mode="B"), dict(init="donor"), dict(variant="AP")):
        with pytest.raises(ValueError):
            TT.check_row(target_row(fx, "fau", 0, 0, **bad))
    for m, kw in (("J1", {}), ("J025", {}), ("AP", {"variant": "XP"}), ("J*", {"variant": "J1"})):   # λ rule bypass, mislabelled variant
        with pytest.raises(ValueError):
            TT.check_row(target_row(fx, "fau", 0, 0, m, g, **kw))
    assert TT.check_row(target_row(fx, "fau", 0, 0, "XP", g, variant="cross_person_pretrain")) == ("XP", "donor")   # a descriptive name
    for ds, bad in (("private_bdf", dict(target="envelope")), ("fau", dict(recipe="a_local_recipe_v1")), ("fau", dict(nce="dedup_v1")),
                    ("private_bdf", dict(private_input="p250_native")), ("fau", dict(selection={"primary": "min_es_loss_minus_mismatch"})),
                    ("fau", dict(training_task="attended_alignment")), ("private_bdf", dict(nce="dedup_v1")),
                    ("fau", dict(epochs=100)), ("dtu", dict(epochs=True)), ("private_bdf", dict(epochs=50)),       # equal budgets
                    ("fau", dict(train_population="TH_ONLY")), ("federici", dict(train_population="")),
                    ("private_bdf", dict(train_population="HA"))):
        with pytest.raises(ValueError):
            TT.check_row(target_row(fx, ds, 0, None if ds == "private_bdf" else 0, **bad))
    for ds, ok in (("fau", dict(epochs=200)), ("private_bdf", dict(epochs=200)), ("private_bdf", dict(nce=L.NCE_TAG)),
                   ("private_bdf", dict(nce=None)), ("dtu", dict(epochs=None))):
        TT.check_row(target_row(fx, ds, 0, None if ds == "private_bdf" else 0, **ok))
    nofield = target_row(fx, "fau", 0, 0)
    del nofield["spec"]["epochs"]
    assert TT.check_row(nofield) == ("S", "random") and TT.bind(nofield)["spec"]["epochs"] == TT.EPOCHS
    for ds, bad in (("fau", dict(epochs=100)), ("fau", dict(train_population="TH_ONLY"))):   # the library path is guarded too
        with pytest.raises(ValueError, match="spec.epochs|spec.train_population"):
            TT.adapt_public(target_row(fx, ds, 0, 0, **bad), man, "cpu", "unused", {}, None)
    with pytest.raises(ValueError, match="spec.epochs"):
        TT.adapt_private(target_row(fx, "private_bdf", 0, None, epochs=20), man, "cpu", "unused", {}, None, kids=synthetic_kids())
    with pytest.raises(ValueError):
        TT.check_row(g)
    b = TT.bind(target_row(fx, "private_bdf", 0, None))
    assert b["content_fold"] == 0 and b["spec"]["training_task"] == "current_class" and b["spec"]["audio_head"] is None
    pb = TT.bind(target_row(fx, "fau", 0, 0), 3)
    assert pb["spec"]["epochs"] == 3 and pb["spec"]["training_task"] == "paired_alignment" and pb["spec"]["init"] == "random"
    with pytest.raises(ValueError):
        TT.adapt_public(target_row(fx, "private_bdf", 0, None), man, "cpu", "unused", {}, None)
    with pytest.raises(ValueError):
        TT.adapt_private(target_row(fx, "fau", 0, 0), man, "cpu", "unused", {}, None, kids=synthetic_kids())
    kids = synthetic_kids()
    kids[0]["fold"] = (kids[0]["fold"] + 1) % 5                              # hc.folds drift against the frozen cell
    with pytest.raises(ValueError, match="differ from the manifest cell"):
        TT.adapt_private(target_row(fx, "private_bdf", kids[0]["fold"], None), man, "cpu", "unused", {}, None, kids=kids)
    stripped = copy.deepcopy(dict(man))
    for c in stripped["cells"]:
        if c["dataset"] == "private_bdf":
            c.pop("train"), c.pop("test")
    with pytest.raises(ValueError, match="lists no children"):
        TT.adapt_private(target_row(fx, "private_bdf", 0, None), V.Manifest(stripped, None, None, man.root), "cpu", "unused", {}, None,
                         kids=synthetic_kids())
