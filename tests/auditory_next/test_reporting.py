"""Synthetic, zero-fit report contracts; execute through the Slurm gate only."""
import json
from pathlib import Path

import pandas as pd
import pytest

from auditory_next import reporting as r


def sources():
    return {role: r.Source(role, run, packet) for role, (run, packet) in r.SOURCES.items()}


def test_screen_missing_is_not_negative_and_intervals_are_validated():
    assert r.screen(-.1, None, .2, .005) == "NOT_EVALUABLE"
    assert r.screen(-.1, -.2, -.01, .005) == "NEGATIVE_SCREEN"
    assert r.screen(.002, .001, .004, .005) == "SMALL_SIGNAL"
    assert r.screen(.02, -.01, .04, .005) == "MIXED"
    assert r.screen(.02, .01, .04, .005) == "SUPPORTED_SIGNAL"
    with pytest.raises(ValueError, match="INVERTED"):
        r.screen(.02, .04, .01, .005)


def test_reader_empty_csv_literal_null_and_hash_change(tmp_path):
    reader = r.Reader()
    empty = tmp_path / "empty.csv"
    empty.write_text("")
    assert reader.read(empty, "fixture/empty", "csv") == []
    table = tmp_path / "mechanisms.csv"
    table.write_text("mechanism,estimate\nnull,\n")
    rows = reader.read(table, "fixture/mechanisms", "csv")
    assert rows == [{"mechanism": "null", "estimate": ""}]
    assert len(reader.public_hashes) == 2
    assert reader.read(table, "fixture/mechanisms", "csv") == rows
    assert len(reader.public_hashes) == 2
    table.write_text("mechanism,estimate\nnull,0.1\n")
    with pytest.raises(ValueError, match="SOURCE_ALIAS_CHANGED"):
        reader.read(table, "fixture/mechanisms", "csv")


def test_missing_sources_preserve_all_four_axes():
    reader = r.Reader()
    reader.sources = sources()
    statuses = r.route_status(reader, [], [])
    assert len(statuses) == 8
    for row in statuses:
        assert row["implementation_status"] == "NOT_RUN"
        assert row["support_status"] == "BLOCKED_INPUT"
        assert row["control_status"] == "MISSING"
        assert row["scientific_status"] == "NOT_EVALUABLE"
        assert row["n_candidates"] is None
    assert not r.delivery_round_complete(reader.sources)


def test_n2_complete_linear_primary_remains_visible_with_secondary_numerical_failure():
    reader=r.Reader(); reader.sources=sources()
    source=reader.sources['n2']; source.complete=True
    source.execution='CORE_MATRIX_RECORDED'; source.implementation='NUMERICAL_FAILURE'
    effect=dict(packet='N2', primary_or_secondary='primary', analysis_id='post_gain_mu_var',
        readout_family='logistic',estimate=-.01,ci_lower=-.02,ci_upper=0.)
    text=r.evidence_overview(reader,[effect],[])
    assert 'post_gain_mu_var=-0.01' in text
    assert '次要MLP32数值未解决' in text
    assert source.implementation=='NUMERICAL_FAILURE'


def test_figures_keep_prespecified_controls_and_do_not_substitute_better_families():
    base=dict(packet='N3',representation='R_SIM',population_id='P_nat',calibration='temperature',
        readout_family='training_OOF_selected',implementation_status='PASS',estimate=-.05,ci_lower=-.06,ci_upper=-.04)
    rows=[dict(base,analysis_id=k) for k in reversed(list(r.FIGURE_CONTRASTS['N3']))]
    rows.append(dict(base,analysis_id='selected_H_minus_HP',readout_family='mlp32',estimate=.2))
    got=r.figure_rows(rows,'N3')
    assert [x['analysis_id'] for x in got]==list(r.FIGURE_CONTRASTS['N3'])
    assert all(x['estimate']==-.05 for x in got)
    n2=dict(base,packet='N2',population_id='P_bal',readout_family='logistic',source_run='N2_core_001',
        analysis_id='post_gain_mu_var',implementation_status='NUMERICAL_FAILURE')
    assert r.figure_rows([n2],'N2')==[n2]
    assert r.figure_rows([dict(n2,readout_family='mlp32')],'N2')==[]


def test_successful_subfamily_cannot_make_failed_matrix_a_scientific_negative():
    reader = r.Reader()
    reader.sources = sources()
    source = reader.sources["n1"]
    source.complete = True
    source.execution = "CORE_MATRIX_RECORDED"
    source.implementation = "NUMERICAL_FAILURE"
    source.summary = {"candidates": 60, "support_status": "SUFFICIENT_FOR_SCREEN"}
    effect = r.base_effect(reader, "n1", "HP_minus_HPB", dict(mode="R_SIM", population="P_nat",
        family="mlp32", calibration="temperature", estimate=-.02, ci_lower=-.03, ci_upper=-.01,
        n_candidates=60, first="HP", second="HPB"), primary=True)
    controls = [dict(packet="N1", control="all_other_controls", status="COMPLETE")]
    result = next(row for row in r.route_status(reader, [effect], controls) if row["packet"] == "N1")
    assert result["descriptive_screen"] == "NEGATIVE_SCREEN"
    assert result["scientific_status"] == "NOT_EVALUABLE"
    assert result["implementation_status"] == "NUMERICAL_FAILURE"


@pytest.mark.parametrize('packet,mode,family', [('C2_R','R_SIM','mlp32'),('C2_S','L0','logistic')])
def test_spatial_figures_include_capacity_controls_without_best_model_selection(packet, mode, family):
    base = dict(packet=packet, representation=mode, population_id='P_bal', calibration='calibrated',
        readout_family=family, implementation_status='PASS', estimate=-.001, ci_lower=-.002, ci_upper=.001)
    rows = [dict(base, analysis_id=name) for name in reversed(list(r.FIGURE_CONTRASTS[packet]))]
    rows += [dict(row, representation='R_SUP', estimate=.1) for row in rows]
    rows += [dict(row, calibration='raw') for row in rows]
    selected = r.figure_rows(rows, packet)
    assert [row['analysis_id'] for row in selected] == list(r.FIGURE_CONTRASTS[packet])
    assert all(row['estimate'] == -.001 and row['representation'] == mode for row in selected)


def test_terminal_budget_reason_can_close_delivery_but_absent_source_cannot():
    items = sources()
    for value in items.values():
        value.complete = True
        value.execution = "PASS"
    items['postflight'].summary = dict(legacy_changed=0, legacy_missing=0, permission_anomalies=0)
    items['resources'].summary = dict(budget_status='WITHIN_CONSERVATIVE_BOUND')
    assert r.delivery_round_complete(items)
    items['postflight'].summary['permission_anomalies'] = 1
    assert not r.delivery_round_complete(items)
    items['postflight'].summary['permission_anomalies'] = 0
    items['resources'].summary['budget_status'] = 'UPPER_BOUND_OVER_BUDGET'
    assert not r.delivery_round_complete(items)
    items['resources'].summary['budget_status'] = 'WITHIN_CONSERVATIVE_BOUND'
    items["synthetic"].complete = False
    items["synthetic"].execution = "RUNNING"
    assert not r.delivery_round_complete(items)
    items["synthetic"].execution = "TIMEOUT"
    items["synthetic"].implementation = "BUDGET_LIMITED"
    assert r.delivery_round_complete(items)
    assert not r.delivery_round_complete(items, ["SOURCE_AGGREGATE_FAILURE"])


def test_e0_is_descriptive_without_an_imported_increment_threshold():
    reader = r.Reader(); reader.sources = sources()
    source = reader.sources['e0r']
    source.complete = True; source.implementation = 'PASS'
    source.summary = dict(records_with_block_support=16)
    effect = r.base_effect(reader, 'e0r', 'puretone_J',
        dict(estimate=.005, ci_lower=.002, ci_upper=.008, n_candidates=7, family='MLP32', calibration='calibrated'),
        primary=True, representation='native128')
    status = next(row for row in r.route_status(reader, [effect], []) if row['packet']=='E0_R')
    assert status['primary_threshold'] is None
    assert status['descriptive_screen'] == effect['descriptive_screen'] == 'DIAGNOSTIC_ONLY'
    assert status['support_status'] == 'DESCRIPTIVE_ONLY'
    source.implementation = 'NUMERICAL_FAILURE'
    source.summary = dict(core_status='INCOMPLETE_PRIMARY_MATRIX')
    status = next(row for row in r.route_status(reader, [], []) if row['packet']=='E0_R')
    assert status['support_status'] == 'DESCRIPTIVE_ONLY'
    assert status['n_candidates'] is None
    assert status['implementation_status'] == 'NUMERICAL_FAILURE'


def test_c2_interventions_require_complete_fixed_cells_and_no_missing_donors():
    rows = [dict(representation='R_SIM', probability_mode=p, family=f, model=m, intervention=k+'_'+s)
        for p in ('raw','calibrated') for f in ('linear','mlp32') for m in ('C_LR','C_LL','C_RR')
        for k in ('zero','same_class','opposite_class') for s in ('first','second')]
    assert r.c2_intervention_status(rows, ['parallel L0/R_SUP repair']) == 'COMPLETE'
    assert r.c2_intervention_status(rows[:-1], []) == 'FAILED'
    assert r.c2_intervention_status(rows + rows[:1], []) == 'FAILED'
    assert r.c2_intervention_status(rows, ['fold 1 same_class donor support']) == 'FAILED'
    assert r.c2_intervention_status([], []) == 'MISSING'


def test_control_adapter_retains_population_family_and_calibration_from_canonical_effects():
    reader = r.Reader(); reader.sources = sources()
    effect = dict(packet='N1', analysis_id='HPP_minus_HPB', primary_or_secondary='secondary', representation='R_SIM', population_id='P_nat',
        readout_family='mlp32', calibration='temperature', estimate=-.01, ci_lower=-.02, ci_upper=-.001,
        n_candidates=59)
    control = next(row for row in r.collect_controls(reader, [effect]) if row['control']=='HPP_minus_HPB')
    assert control['population_id'] == 'P_nat'
    assert control['readout_family'] == 'mlp32'
    assert control['calibration'] == 'temperature'
    assert control['estimate'] == -.01


def test_empty_source_run_writes_all_required_headers_without_false_completion(tmp_path, monkeypatch):
    monkeypatch.setattr(r, "ROOT", tmp_path)
    monkeypatch.setattr(r, "require_slurm", lambda: None)
    monkeypatch.setattr(r, "make_figures", lambda *args: [])
    dest = tmp_path / "private/auditory_next_v2/report_fixture"
    public = tmp_path / "results/auditory_next_v2/report_fixture"
    report = tmp_path / "reports/auditory_next_v2/report_fixture"
    for directory in (dest, public, report):
        directory.mkdir(parents=True)
    (dest / "start.json").write_text("{}")
    def finish(private, visible, summary):
        (private / "completion.json").write_text(json.dumps(summary))
        (visible / "summary.json").write_text(json.dumps(summary))
        return summary
    monkeypatch.setattr(r, "finish", finish)
    summary = r.run({}, {}, {"root": str(tmp_path)}, dest, public, report)
    assert summary["round_complete"] is False
    assert summary["all_packages_scientifically_complete"] is False
    assert summary["status"] == "IN_PROGRESS"
    assert summary["new_head_fits"] == summary["model_reads"] == 0
    for name in ("route_status.csv", "eligibility_aggregate.csv", "metrics_aggregate.csv", "paired_effects.csv",
                 "controls_aggregate.csv", "numerical_status.csv", "synthetic_summary.csv", "resource_usage.csv", "source_hashes.csv"):
        frame = pd.read_csv(public / name, keep_default_na=False)
        assert len(frame.columns) > 0
    assert pd.read_csv(public / "paired_effects.csv").empty
    status = pd.read_csv(public / "route_status.csv")
    assert set(status.scientific_status) == {"NOT_EVALUABLE"}
    manifest = json.loads((public / "output_manifest.json").read_text())
    assert any(row["logical_alias"] == "reports/NEXT_ROUND_REPORT.md" for row in manifest["files"])
    assert str(tmp_path) not in (report / "NEXT_ROUND_REPORT.md").read_text()


def test_synthetic_execution_does_not_certify_mechanism_identification():
    # Every world ran, but these counts could indicate complete failure to
    # distinguish the positive and negative mechanisms. Completion cannot pass.
    rows = [dict(packet="N1", mechanism=m, family="mlp32", n_planned=30,
        n_evaluable=30, n_unknown=0, n_positive=30, n_numerical_failure=0)
        for m in r.SYNTHETIC_MECHANISMS["N1"]]
    audit = r.synthetic_control_audit(rows, "N1")
    assert audit["execution_status"] == "COMPLETE"
    assert audit["scientific_control_status"] == "MISSING"
    assert audit["automatic_scientific_support"] is False
    assert audit["rate_acceptance_threshold"] is None
    assert "DIRECTION" in audit["interpretation_status"]
    assert "noise margin" in audit["expected_behavior"]
    # No post-hoc recovery/FPR threshold is introduced for the other extreme.
    for row in rows:
        row["n_positive"] = 0
    assert r.synthetic_control_audit(rows, "N1")["scientific_control_status"] == "MISSING"
    rows[-1]["n_unknown"], rows[-1]["n_evaluable"] = 1, 29
    assert r.synthetic_control_audit(rows, "N1")["execution_status"] == "FAILED"


def test_timeout_uses_exact_start_job_not_run_alias(tmp_path, monkeypatch):
    monkeypatch.setattr(r, "ROOT", tmp_path)
    folder = tmp_path / "private/auditory_next_v2" / r.SOURCES["synthetic"][0]
    folder.mkdir(parents=True)
    (folder / "start.json").write_text(json.dumps({"job_id": "321", "source_hashes": {}}))
    source = r.Reader().source("synthetic")
    assert source.job_id == "321"
    wrong_job = dict(job_id="320", run=source.run, state="TIMEOUT", accounting_source="sacct", active_reservation=False)
    step = dict(wrong_job, job_id="321.batch")
    assert r.resource_state_for_source(source, [wrong_job, step])["implementation"] == "NOT_RUN"
    exact = dict(job_id="321", run="different_shared_job_alias", state="TIMEOUT", accounting_source="scontrol", active_reservation=False)
    result = r.resource_state_for_source(source, [wrong_job, exact])
    assert result["execution"] == "TIMEOUT"
    assert result["implementation"] == "BUDGET_LIMITED"
    source.complete, source.execution, source.implementation = True, "MECHANISM_AUDIT_COMPLETE", "PASS"
    assert r.resource_state_for_source(source, [exact])["implementation"] == "PASS"


@pytest.mark.parametrize("state", ["PENDING", "RUNNING", "UNAVAILABLE", "UNKNOWN", ""])
def test_nonterminal_or_unknown_accounting_never_becomes_timeout(state):
    source = r.Source("synthetic", "synthetic_001", "SYNTHETIC", job_id="321", execution="STARTED_NO_COMPLETION")
    row = dict(job_id="321", state=state, accounting_source="sacct", active_reservation=state in ("PENDING", "RUNNING"))
    result = r.resource_state_for_source(source, [row])
    assert result["execution"] not in r.TERMINAL_BLOCKED
    assert result["implementation"] != "BUDGET_LIMITED"
    # A requested-limit fallback is not measured evidence of a hard timeout.
    unknown = dict(row, state="TIMEOUT", accounting_source="requested_fallback", active_reservation=False)
    assert r.resource_state_for_source(source, [unknown])["execution"] == "STARTED_NO_COMPLETION"


def test_new_n3_support_table_counts_cover_old_fixed_strata_without_new_exclusion():
    descriptions = [dict(mode="R_SIM", population="P_nat", previous_run_bin="run_2", view=v)
                    for v in ("H", "HP")]
    rows = [dict(mode="R_SIM", population="P_nat", previous_run_bin="run_2",
        class0_trials=7, class1_trials=3, n_candidates=2, n_candidates_both_classes=2, n_trials=10)]
    assert r.history_stratum_support_audit(rows, descriptions)["status"] == "COMPLETE"
    assert r.history_stratum_support_audit([], descriptions)["status"] == "MISSING"
    assert r.history_stratum_support_audit(rows + rows, descriptions)["status"] == "FAILED"
    single_class = [dict(rows[0], class0_trials=0, class1_trials=10, n_candidates_both_classes=0)]
    audit = r.history_stratum_support_audit(single_class, descriptions)
    assert audit["status"] == "COMPLETE"  # Counts complete; no assertion of two-class eligibility.
    assert "单类" in audit["notes"]
    assert r.history_stratum_support_audit([dict(rows[0], n_trials=11)], descriptions)["status"] == "FAILED"


def test_saved_family_choices_keep_capacity_changes_and_reject_missing_folds():
    rows = [dict(mode=m, population=p, view=v, outer_fold=f,
        family='mlp32' if m=='R_SIM' and v=='H' else 'logistic')
        for m in ('R_SIM','L0') for p in ('P_nat','P_bal')
        for v in ('H','HP','HB','HBP','Hnoise') for f in range(5)]
    out = r.family_selection_summary(rows)
    assert next(x for x in out if (x['mode'],x['population'],x['view'])==('R_SIM','P_nat','H'))['family']=='mlp32'
    assert next(x for x in out if (x['mode'],x['population'],x['view'])==('R_SIM','P_nat','HP'))['family']=='logistic'
    assert all(x['n_outer_folds']==5 for x in out)
    for invalid in (rows[:-1], rows+[rows[0]]):
        with pytest.raises(ValueError, match='FROZEN_FOLD_COVERAGE'):
            r.family_selection_summary(invalid)
    with pytest.raises(ValueError, match='UNDECLARED_FAMILY'):
        r.family_selection_summary([dict(x,family='mlp32') for x in rows])


def test_balanced_J_is_exact_algebra_and_never_applied_to_natural_prior():
    ce = dict(packet="N2", population_id="P_bal", metric="ce_bits", estimate=1.02,
        ci_lower=1.01, ci_upper=1.04, source_run="fixed_fixture", bootstrap_scope="fixed OOF")
    result = r.balanced_prior_information(ce)
    assert result["estimate"] == pytest.approx(-.02)
    assert result["ci_lower"] == pytest.approx(-.04)
    assert result["ci_upper"] == pytest.approx(-.01)
    assert result["unit"] == "bits/bag"
    assert result["source_run"] == ce["source_run"]
    assert r.balanced_prior_information(dict(ce, population_id="P_nat")) is None
    assert r.balanced_prior_information(dict(ce, packet="N3"))["unit"] == "bits/trial"


def test_evidence_overview_uses_completed_fixed_effects_and_leaves_missing_pending():
    reader = r.Reader()
    reader.sources = sources()
    row = r.base_effect(reader, "a2_core", "post_delta_cosine", dict(mode="R_SIM",
        estimate=.021234, ci_lower=-.01, ci_upper=.04), unit="cosine_difference", primary=True)
    assert "0.021234" not in r.evidence_overview(reader, [row], [])
    reader.sources["a2_core"].complete = True
    reader.sources["a2_core"].implementation = "PASS"
    overview = r.evidence_overview(reader, [row], [])
    assert "0.021234" in overview
    assert "未达到0.05" in overview
    assert "N1：待定" in overview
    assert "E0_R：待定" in overview
