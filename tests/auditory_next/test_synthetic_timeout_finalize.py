"""Pure gate/denominator tests for synthetic timeout recovery.

These tests deliberately do not call the Slurm-only ``run`` entry point.
"""

import json
from pathlib import Path

import pytest

from auditory_next.synthetic_timeout_finalize import (
    _a2_ids,
    _load_and_validate_a2,
    _a2_rate_rows,
    unknown_rate_rows,
    validate_timeout_gate,
)


def _planned():
    counts = {"A2": 300, "N1": 120, "N2": 90, "N3": 90, "G0": 60}
    mechanisms = {
        "A2": ("null", "predictable_nuisance", "individual_stimulus"),
        "N1": ("PRIOR_ONLY", "BACKGROUND_KEY", "ADDITIVE_NOISE", "INDEPENDENT_BACKGROUND"),
        "N2": ("MEAN_SUFFICIENT", "COVARIANCE_SIGNAL", "TIME_DRIFT"),
        "N3": ("HISTORY_ONLY", "EEG_INCREMENT", "NEAR_DETERMINISTIC_HISTORY"),
        "G0": ("feature_injection",),
    }
    rows = []
    for packet, count in counts.items():
        each = count // len(mechanisms[packet])
        for mechanism in mechanisms[packet]:
            for index in range(each):
                rows.append({"packet": packet, "mechanism": mechanism, 'world_index': index,
                             "id": f"{packet}_{mechanism}_{index:03d}"})
    return rows


def _a2_outcomes():
    rows = []
    for mechanism in ("null", "predictable_nuisance", "individual_stimulus"):
        for condition in ("zero", "fixed", "fitted"):
            for component in ("delta", "residual"):
                for index in range(100):
                    rows.append({"packet": "A2", "mechanism": mechanism,
                                 "world_id": f"A2_{mechanism}_{index:03d}",
                                 "family": f"{condition}__{component}",
                                 "status": "EVALUATED", "screen": False,
                                 "expected_positive": mechanism == "individual_stimulus"})
    return rows


def _gate(tmp_path, *, terminal="TIMEOUT", job="42", completion=False, barrier=None):
    original = tmp_path / "original"
    terminal_dir = tmp_path / "scheduler_terminal"
    original.mkdir()
    terminal_dir.mkdir()
    (original / "start.json").write_text(json.dumps({"run": "synthetic_001", "job_id": job}))
    (terminal_dir / f"{job}.txt").write_text(f'JobId={job} JobState={terminal} RunTime=02:00:00 TimeLimit=02:00:00')
    if completion:
        (original / "completion.json").write_text("{}")
    if barrier == "family":
        (original / "heads").mkdir()
        (original / "heads" / "family_status.json").write_text("{}")
    elif barrier == "world":
        (original / "world_results.json").write_text("[]")
    return original, terminal_dir


def test_timeout_gate_requires_exact_job_and_terminal(tmp_path):
    original, terminal_dir = _gate(tmp_path)
    assert validate_timeout_gate(original, terminal_dir)[0]["job_id"] == "42"

    wrong = tmp_path / "wrong"
    wrong.mkdir()
    (wrong / "99.txt").write_text("TIMEOUT")
    with pytest.raises(ValueError, match="TERMINAL_NOT_CONFIRMED"):
        validate_timeout_gate(original, wrong)

    for invalid in ('JobId=99 JobState=TIMEOUT', 'JobState=TIMEOUT', 'JobId=42 JobState=CANCELLED', 'TIMEOUT'):
        (terminal_dir / "42.txt").write_text(invalid)
        with pytest.raises(ValueError, match="TERMINAL_NOT_CONFIRMED"):
            validate_timeout_gate(original, terminal_dir)


@pytest.mark.parametrize("kwargs,code", [
    ({"completion": True}, "ORIGINAL_COMPLETION_EXISTS"),
    ({"barrier": "family"}, "FAMILY_BARRIER_EXISTS"),
    ({"barrier": "world"}, "FAMILY_BARRIER_EXISTS"),
])
def test_timeout_gate_rejects_nonrecoverable_barriers(tmp_path, kwargs, code):
    original, terminal_dir = _gate(tmp_path, **kwargs)
    with pytest.raises(ValueError, match=code):
        validate_timeout_gate(original, terminal_dir)


def test_unknown_rows_keep_fixed_denominator_and_never_negative():
    rows = unknown_rate_rows(_planned())
    assert len(rows) == 15
    assert {row["status"] for row in rows} == {"UNKNOWN_BUDGET"}
    assert all(row["n_planned"] == 30 and row["n_unknown"] == 30 for row in rows)
    assert all(row["n_positive"] == 0 and row["n_numerical_failure"] == 0 for row in rows)
    assert all(row["unknowns_are_not_negative"] and row["main_estimate_mean_among_evaluable"] is None
               for row in rows)


def test_a2_duplicate_or_missing_world_is_rejected(tmp_path):
    path = tmp_path / "A2_world_results.json"
    rows = _a2_outcomes()
    path.write_text(json.dumps(rows))
    assert len(_load_and_validate_a2(tmp_path, {})) == 1800
    rows[-1]["world_id"] = rows[-2]["world_id"]
    path.write_text(json.dumps(rows))
    with pytest.raises(ValueError, match="DUPLICATE_OR_MISSING|WORLD_COVERAGE"):
        _load_and_validate_a2(tmp_path, {})


def test_a2_rates_preserve_one_hundred_world_denominator():
    rows = _a2_rate_rows(_a2_outcomes())
    assert len(rows) == 18
    assert all(row["n_planned"] == 100 and row["n_unknown"] == 0 for row in rows)
    assert all(row["n_numerical_failure"] == 0 for row in rows)
    assert set(row["world_id"] for row in _a2_outcomes()) == _a2_ids()


def test_unknown_a2_ci_envelope_is_not_treated_as_zero_positive_draws():
    rows = [dict(r,status='UNDEFINED',screen=None) for r in _a2_outcomes()]
    out = _a2_rate_rows(rows)
    assert all(r['monte_carlo_ci_lower']==0 and r['monte_carlo_ci_upper']==1 for r in out)
    assert all(r['positive_rate_among_evaluable'] is None and r['n_unknown']==100 for r in out)


def test_saved_statistic_group_validation_includes_identity_errors_and_undefined_zero_norm(tmp_path):
    import pandas as pd
    from auditory_next.synthetic_timeout_finalize import aggregate_saved_a2_statistics
    components = [(n,'identity_error') for n in ('max_pair_error','matching_gain_error')]
    components += [(n,m) for n in ('delta','prediction','residual') for m in ('cosine','inner_product')]
    components += [(n,'decomposition_inner_product') for n in ('delta_delta','minus_delta_prediction',
        'minus_prediction_delta','prediction_prediction','residual')]
    data = [dict(world_id=f'A2_{m}_{i:03d}',mechanism=m,condition=c,component=n,metric=k,
        estimate=float('nan') if (c,n,k)==('zero','prediction','cosine') else 0.)
        for m in ('null','predictable_nuisance','individual_stimulus') for c in ('zero','fixed','fitted')
        for n,k in components for i in range(100)]
    path=tmp_path/'statistics.parquet'; output=tmp_path/'aggregate.csv'
    table=pd.DataFrame(data); table.to_parquet(path)
    result=aggregate_saved_a2_statistics(path,output)
    assert len(result)==117
    assert sum(r['n_undefined'] for r in result)==300
    table.loc[0,'estimate']=float('inf'); table.to_parquet(path)
    with pytest.raises(ValueError,match='INFINITE_STATISTIC'):
        aggregate_saved_a2_statistics(path,output)
    table=pd.DataFrame(data).iloc[:-1]; table.to_parquet(path)
    with pytest.raises(ValueError,match='STATISTIC_WORLD_COVERAGE'):
        aggregate_saved_a2_statistics(path,output)
