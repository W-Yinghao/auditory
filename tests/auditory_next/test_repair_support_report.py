"""Synthetic receipts only; run under Slurm, with no model fits."""
from copy import deepcopy
import json
import pytest
from auditory_next.repair_support_report import summarize_repair_support, read_repair_support, STABLE, UNRESOLVED


def fixture():
    interval = dict(estimate=-.02, ci_lower=-.03, ci_upper=.01, n_candidates=7, n_bootstrap=2000,
                    seed=20260917, effect="baseline_minus_augmented", gain_definition="baseline - augmented", valid=True)
    legacy = dict(records_requested=18, records_with_block_support=16, records_decoded=11,
        family_status={"linear": "COMPLETE"}, results=[dict(family="linear", calibration=c, task=t,
        complete_pairs=7, mean_CE_bits=1.02, J_bits_interval=deepcopy(interval))
        for c in ("raw", "calibrated") for t in ("puretone", "bapa")])
    cases = [dict(key=f"private_record{r}_fold{f}", record_id=f"private_record{r}", fold=f,
             kind="E0_R", specs=[["MLP32", "native", 32]]) for r in range(16) for f in range(4)]
    members = [dict(key=f'{c["key"]}_{p}_{a}', case=c["key"], family="MLP32", view="native", width=32, part=p, alpha=a)
               for c in cases for p in ("inner0", "inner1", "inner2", "final") for a in (.01, .1, 1., 10.)]
    diagnostics = dict(status="INCOMPLETE_PRIMARY_MATRIX", budget=2000, neural_fits=1024, continuation_fits=0,
        extended_members=1024, initial=[dict(m, status=UNRESOLVED, steps=1000, attempted_budget=1000) for m in members],
        final=[dict(m, status=STABLE if i < 765 else UNRESOLVED, steps=2000, attempted_budget=2000) for i, m in enumerate(members)])
    completion = dict(stage="E0_R", implementation_status="PASS", final_alpha_fits_including_unselected=True,
        status="INCOMPLETE_PRIMARY_MATRIX", core_status="INCOMPLETE_PRIMARY_MATRIX",
        optimization_status="INCOMPLETE_PRIMARY_MATRIX", required_members=1024, stable_members=765,
        new_neural_head_fits=1024, new_linear_head_fits=0, new_encoder_fits=0, selected_budget=2000,
        extended_members=1024, test_predictions_generated=False, incomplete_family_aggregates_withheld=True, results=[])
    return legacy, members, diagnostics, cases, completion


def test_complete_records_do_not_override_family_barrier_or_old_source():
    data = fixture(); before = deepcopy(data)
    result = summarize_repair_support(*data)
    assert result["mlp_records_all_required_heads_stable"] == 11
    assert result["mlp_records_available_for_primary_aggregation"] == 0 and not result["mlp_family_passed"]
    assert (result["stable_heads"], result["unresolved_heads"]) == (765, 259)
    assert result["legacy_linear_records_complete"] == 16 and "private_record" not in json.dumps(result)
    for actual, original in zip(result["legacy_linear_results"], data[0]["results"]):
        assert actual == dict(original, source_run="E0_native_003")
    data[0]["records_decoded"] = 999
    assert summarize_repair_support(*data) == result
    assert before[1:] == data[1:]


@pytest.mark.parametrize("failure", ["missing", "duplicate", "fold", "alpha", "diagnostic", "total", "withheld", "legacy", "record", "barrier"])
def test_malformed_or_partial_receipts_fail_closed(failure):
    legacy, members, diagnostics, cases, completion = fixture()
    if failure == "missing": members.pop()
    elif failure == "duplicate": members[-1] = deepcopy(members[0])
    elif failure == "fold": cases[1]["fold"] = 0
    elif failure == "alpha": members[0]["alpha"] = 99
    elif failure == "diagnostic": diagnostics["final"][0]["case"] = cases[-1]["key"]
    elif failure == "total": completion["stable_members"] = 766
    elif failure == "withheld": completion["test_predictions_generated"] = True
    elif failure == "record": cases[0]["record_id"] = "unexpected_record"
    elif failure == "barrier":
        for d in diagnostics["initial"]: d["status"] = STABLE
    else: legacy["results"].pop()
    with pytest.raises((ValueError, KeyError)):
        summarize_repair_support(legacy, members, diagnostics, cases, completion)


def test_reader_uses_json_and_nonidentifying_aliases(tmp_path):
    data = fixture(); folder = tmp_path / "private/auditory_next_v2/E0R_core_001"
    legacy = tmp_path / "results/auditory5_v1/E0_native_003/summary.json"
    paths = {legacy: data[0], **{folder / name: value for name, value in zip(
        ("member_manifest.json", "family_training_diagnostics.json", "completion.json"), (data[1], data[2], data[4]))}}
    paths.update({folder / "cases" / c["key"] / "case.json": c for c in data[3]})
    for path, value in paths.items():
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value))
    class Reader:
        def read(self, path, alias):
            assert "private_record" not in alias and path.suffix == ".json"
            return json.loads(path.read_text())
    assert read_repair_support(tmp_path, Reader()) == summarize_repair_support(*data)
