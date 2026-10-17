"""Budget-plan pairing and fixed-state instrumentation; no real cohort in these tests."""
import copy
from pathlib import Path

import pytest
import torch

from auditory_alignment_v3 import core, fm_aligned, fm_aligned32, local_train
from auditory_alignment_v3.aln34 import learning_budget as B


def source_rows():
    rows = []
    for seed in B.SEEDS:
        for sf in range(5):
            for cf in range(2):
                for arch, ads in (("cbramod", ("pretrained_full", "random_full")),
                                  ("reve", ("pretrained_full", "random_full")), ("lag_local_tokens", (None,))):
                    for ad in ads:
                        spec = {"architecture": arch, "objective": "NCE", "variant": "local_aligned1000"}
                        if ad:
                            spec.update(adaptation=ad, recipe="full_onestep_v1", lr_backbone=B.LR[arch], lr_head=1e-3)
                        rows.append({"dataset": "dtu", "seed": seed, "subject_fold": sf, "content_fold": cf,
                                     "family_id": "ALN32_TRUE_FULL" if ad else "ALN32_LOCAL_SUPPORT", "spec": spec,
                                     "experiment_id": f"base_{seed}_{sf}_{cf}_{arch}_{ad}"})
    return rows


def test_complete_pairs_and_reference_coverage():
    rows = source_rows()
    before = copy.deepcopy(rows)
    selected = B.select_baselines(rows + [{**rows[0], "dataset": "fau"}, {**rows[0], "seed": 9999}])
    assert len(selected) == 150
    new = [B.new_row(r, {"code_hash": "known_baseline"}, "a" * 64) for r in selected]
    assert rows == before
    assert len({r["experiment_id"] for r in new}) == 150
    for row in new:
        s = row["spec"]
        assert s["baseline_id"].startswith("base_") and row["experiment_id"] != s["baseline_id"]
        assert s["epochs"] == {"cbramod": 200, "reve": 100, "lag_local_tokens": 400}[s["architecture"]]
    with pytest.raises(ValueError, match="coverage mismatch"):
        B.select_baselines(rows[:-1])
    with pytest.raises(ValueError, match="coverage mismatch"):
        B.select_baselines(rows + [rows[0]])


@pytest.mark.parametrize("local", (False, True))
def test_snapshots_evaluated_without_replacing_selected_state(tmp_path, monkeypatch, local):
    monkeypatch.setattr(core, "code_hash", lambda _: "fixed_code")
    source = source_rows()[-1] if local else source_rows()[0]
    row = B.new_row(source, {"code_hash": "baseline"}, "a" * 64)
    row["spec"].update(baseline_epochs=2, epochs=4)
    row["experiment_id"] = "test_unit"
    ck = tmp_path / "ckpt"
    ck.mkdir()
    model, head = torch.nn.Linear(1, 1, bias=False), torch.nn.Linear(1, 1, bias=False)
    trainer = local_train if local else fm_aligned32
    calls, records, saved = [], [], []
    def original_eval(*args, **kwargs):
        v = float(args[1].weight.item())
        calls.append(v)
        return {"test_value": v}
    original_bind = lambda r: {"spec": {"epochs": 200}, "experiment_id": r["experiment_id"]}
    monkeypatch.setattr(trainer, "_save_resume", lambda p, **payload: saved.append(payload["epoch"]))
    monkeypatch.setattr(core, "write_record", lambda p, r, t: records.append(r))
    monkeypatch.setattr(core, "bind", original_bind)
    monkeypatch.setattr(core if local else fm_aligned, "evaluate_grid" if local else "evaluate_aligned", original_eval)
    captures = []
    with B.instrumentation(row, tmp_path, 4, captures):
        assert core.bind(row)["spec"]["epochs"] == 4
        for epoch in range(1, 5):
            with torch.no_grad():
                model.weight.fill_(epoch); head.weight.fill_(epoch + 10)
            payload = {"epoch": epoch, "step": epoch * 10}
            payload.update({"enc": model.state_dict(), "head": head.state_dict()} if local else {"model": model.state_dict()})
            trainer._save_resume(str(ck / "resume.pt"), **payload)
        with torch.no_grad():
            model.weight.fill_(9); head.weight.fill_(19)
        fn = core.evaluate_grid if local else fm_aligned.evaluate_aligned
        value = fn({}, model, head, None, None, {}, 3)
        assert value["test_value"] == 9
        assert float(model.weight.item()) == 9 and float(head.weight.item()) == 19
        core.write_record("test", {"status": "complete"}, 0)
    assert calls == [9, 1, 2, 4]
    assert saved == [1, 2, 3, 4]  # original resumability is untouched
    assert [x["optimizer_steps"] for x in captures] == [10, 20, 40]
    assert all(Path(x["checkpoint"]).exists() and x["checkpoint_sha256"] for x in captures)
    assert records[0]["trajectory"] == captures and records[0]["truncated"] is False
    assert core.bind is original_bind
    assert (core.evaluate_grid if local else fm_aligned.evaluate_aligned) is original_eval


def test_probes_cannot_overwrite_production(tmp_path, monkeypatch):
    monkeypatch.setattr(core, "FAMILY_CODE", dict(core.FAMILY_CODE))
    monkeypatch.setattr(core, "FAMILY_GROUP", dict(core.FAMILY_GROUP))
    row = B.new_row(source_rows()[0], {"code_hash": "baseline"}, "a" * 64)
    with pytest.raises(ValueError, match="cannot write production"):
        B.run_one(row, B.BASE, probe=True)
    with pytest.raises(ValueError, match="output root differs"):
        B.run_one(row, tmp_path, probe=False)


def test_existing_family_hashes_unchanged(monkeypatch):
    monkeypatch.setattr(core, "FAMILY_CODE", copy.deepcopy(core.FAMILY_CODE))
    monkeypatch.setattr(core, "FAMILY_GROUP", dict(core.FAMILY_GROUP))
    original = {f: core.code_hash(f) for f in core.FAMILY_GROUP}
    B.register()
    assert all(core.code_hash(f) == h for f, h in original.items())
    assert all(core.code_hash(f) for f in B.FAMILIES)


def test_timepoints_follow_actual_budget_with_nearest_integer_epochs():
    assert B.snapshot_epochs(100, 200) == [25, 50, 100, 200]
    assert B.snapshot_epochs(50, 100) == [13, 25, 50, 100]
    assert B.snapshot_epochs(200, 400) == [50, 100, 200, 400]
    assert B.snapshot_epochs(100, 2) == [2]
