"""Zero-fit recovery for a scheduler-timeout synthetic run.

This module is deliberately a barriered recovery path.  It can only consume
the completed A2 receipts/statistics already on disk; it never calls a
world generator, opens a model, or evaluates a classifier.  A timeout is
reported as budget limitation, with the unfinished families retained in their
prespecified denominators.
"""

import json
import re
from pathlib import Path

from .provenance import ROOT, digest, finish, object_hash, require_slurm, write_json


PACKETS = ("A2", "N1", "N2", "N3", "G0")
A2_MECHANISMS = ("null", "predictable_nuisance", "individual_stimulus")
N1_MECHANISMS = ("PRIOR_ONLY", "BACKGROUND_KEY", "ADDITIVE_NOISE", "INDEPENDENT_BACKGROUND")
N2_MECHANISMS = ("MEAN_SUFFICIENT", "COVARIANCE_SIGNAL", "TIME_DRIFT")
N3_MECHANISMS = ("HISTORY_ONLY", "EEG_INCREMENT", "NEAR_DETERMINISTIC_HISTORY")


def _error(code):
    raise ValueError(code)


def validate_timeout_gate(original, scheduler_terminal):
    """Require an exact scheduler TIMEOUT for the original run.

    ``scheduler_terminal`` is kept as an explicit argument so a caller cannot
    accidentally accept a terminal receipt for another job.
    """
    original = Path(original).resolve()
    start_path = original / "start.json"
    if not start_path.is_file():
        _error("SYNTHETIC_TIMEOUT_START_MISSING")
    start = json.loads(start_path.read_text())
    job_id = str(start.get("job_id", ""))
    if not job_id.isdigit():
        _error("SYNTHETIC_TIMEOUT_JOB_ID_MISSING")
    terminal = Path(scheduler_terminal).resolve() / (job_id + ".txt")
    if terminal.is_symlink() or not terminal.is_file():
        _error("SYNTHETIC_TIMEOUT_TERMINAL_NOT_CONFIRMED")
    fields = dict(re.findall(r'([A-Za-z][A-Za-z0-9_]*)=([^\s]+)', terminal.read_text()))
    if fields.get('JobId') != job_id or fields.get('JobState') != 'TIMEOUT':
        _error("SYNTHETIC_TIMEOUT_TERMINAL_NOT_CONFIRMED")
    if (original / "completion.json").exists():
        _error("SYNTHETIC_TIMEOUT_ORIGINAL_COMPLETION_EXISTS")
    # A family barrier or classifier world results means this is no longer the
    # narrowly defined pre-barrier recovery case.
    if (original / "heads" / "family_status.json").exists() or (original / "world_results.json").exists():
        _error("SYNTHETIC_TIMEOUT_FAMILY_BARRIER_EXISTS")
    return start, terminal


def _expected_planned(planned):
    if not isinstance(planned, list) or len(planned) != 660:
        _error("SYNTHETIC_TIMEOUT_PLANNED_WORLD_COUNT")
    ids = [row.get("id") for row in planned]
    if any(not isinstance(value, str) for value in ids) or len(set(ids)) != len(ids):
        _error("SYNTHETIC_TIMEOUT_PLANNED_WORLD_IDS")
    expected = {"A2": 300, "N1": 120, "N2": 90, "N3": 90, "G0": 60}
    for packet, count in expected.items():
        if sum(row.get("packet") == packet for row in planned) != count:
            _error("SYNTHETIC_TIMEOUT_PLANNED_PACKET_COUNTS")
    mechanisms = dict(A2=A2_MECHANISMS, N1=N1_MECHANISMS, N2=N2_MECHANISMS,
        N3=N3_MECHANISMS, G0=('feature_injection',))
    expected_keys = {(packet, mechanism, index, f'{packet}_{mechanism}_{index:03d}')
        for packet, names in mechanisms.items() for mechanism in names
        for index in range(100 if packet=='A2' else 60 if packet=='G0' else 30)}
    actual_keys = {(r.get('packet'),r.get('mechanism'),r.get('world_index'),r.get('id')) for r in planned}
    if actual_keys != expected_keys:
        _error('SYNTHETIC_TIMEOUT_PLANNED_MECHANISM_COVERAGE')
    return planned


def _a2_ids():
    return {f"A2_{mechanism}_{index:03d}" for mechanism in A2_MECHANISMS for index in range(100)}


def _validate_a2_receipts(original, hashes):
    worlds = Path(original) / "worlds"
    starts = sorted(worlds.glob("A2_*/ridge_start.json"))
    if len(starts) != 300 or {path.parent.name for path in starts} != _a2_ids():
        _error("SYNTHETIC_TIMEOUT_A2_RIDGE_START_COVERAGE")
    seen = set()
    for start_path in starts:
        completion = start_path.with_name("ridge_completion.json")
        if not completion.is_file():
            _error("SYNTHETIC_TIMEOUT_A2_RIDGE_COMPLETION_MISSING")
        start = json.loads(start_path.read_text())
        done = json.loads(completion.read_text())
        fit_id = str(start.get("fit_id", ""))
        world_id = start_path.parent.name
        if fit_id != world_id + "__ridge__background_audit" or done.get("fit_id") != fit_id:
            _error("SYNTHETIC_TIMEOUT_A2_RIDGE_ID_MISMATCH")
        if done.get("status") != "PASS":
            _error("SYNTHETIC_TIMEOUT_A2_RIDGE_NOT_PASS")
        if any(done.get(k) != value for k, value in start.items()) or start.get('family') != 'ridge' or start.get('alpha') != 10.:
            _error('SYNTHETIC_TIMEOUT_A2_RIDGE_RECEIPT_CHANGED')
        seen.add(world_id)
        for path in (start_path, completion):
            hashes[str(path)] = digest(path)
    if len(seen) != 300:
        _error("SYNTHETIC_TIMEOUT_A2_RIDGE_DUPLICATE")


def _validate_prepared_hashes(original, hashes):
    path = Path(original) / "prepared_input_hashes.json"
    if not path.is_file():
        _error("SYNTHETIC_TIMEOUT_PREPARED_HASHES_MISSING")
    recorded = json.loads(path.read_text())
    if not isinstance(recorded, dict):
        _error("SYNTHETIC_TIMEOUT_PREPARED_HASHES_SCHEMA")
    a2 = []
    for raw_path, expected in recorded.items():
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = Path(original) / candidate
        if candidate.name == "world.pkl" and candidate.parent.name in _a2_ids():
            if candidate.is_symlink() or candidate.resolve() != (Path(original)/'worlds'/candidate.parent.name/'world.pkl').resolve():
                _error('SYNTHETIC_TIMEOUT_A2_INPUT_PATH_SCOPE')
            a2.append((candidate.resolve(), str(expected)))
    if len(a2) != 300 or len({str(path) for path, _ in a2}) != 300:
        _error("SYNTHETIC_TIMEOUT_A2_INPUT_HASH_COVERAGE")
    for candidate, expected in a2:
        if not candidate.is_file() or digest(candidate) != expected:
            _error("SYNTHETIC_TIMEOUT_A2_INPUT_HASH_CHANGED")
        hashes[str(candidate)] = expected
    hashes[str(path)] = digest(path)


def _load_and_validate_a2(original, hashes):
    path = Path(original) / "A2_world_results.json"
    if not path.is_file():
        _error("SYNTHETIC_TIMEOUT_A2_WORLD_RESULTS_MISSING")
    rows = json.loads(path.read_text())
    if not isinstance(rows, list) or not rows:
        _error("SYNTHETIC_TIMEOUT_A2_WORLD_RESULTS_SCHEMA")
    expected = _a2_ids()
    grouped = {}
    for row in rows:
        if row.get("packet") != "A2" or row.get("world_id") not in expected:
            _error("SYNTHETIC_TIMEOUT_A2_WORLD_ID")
        if row.get("status") not in ("EVALUATED", "UNDEFINED"):
            _error("SYNTHETIC_TIMEOUT_A2_OUTCOME_STATUS")
        if type(row.get("screen")) is not bool and row.get("status") == "EVALUATED":
            _error("SYNTHETIC_TIMEOUT_A2_SCREEN_SCHEMA")
        if row.get('status')=='UNDEFINED' and row.get('screen') is not None:
            _error('SYNTHETIC_TIMEOUT_A2_UNDEFINED_IS_UNKNOWN')
        if row.get('expected_positive') is not (row.get('mechanism')=='individual_stimulus'):
            _error('SYNTHETIC_TIMEOUT_A2_MECHANISM_EXPECTATION')
        key = (row.get("mechanism"), row.get("family"))
        grouped.setdefault(key, []).append(row)
    expected_keys = {(mechanism, condition + "__" + component)
                     for mechanism in A2_MECHANISMS
                     for condition in ("zero", "fixed", "fitted")
                     for component in ("delta", "residual")}
    if set(grouped) != expected_keys or any(len(value) != 100 for value in grouped.values()):
        _error("SYNTHETIC_TIMEOUT_A2_WORLD_RESULT_DUPLICATE_OR_MISSING")
    for value in grouped.values():
        if {row["world_id"] for row in value} != _a2_ids_for_group(value):
            _error("SYNTHETIC_TIMEOUT_A2_WORLD_RESULT_WORLD_COVERAGE")
    hashes[str(path)] = digest(path)
    return rows


def _a2_ids_for_group(rows):
    mechanism = rows[0]["mechanism"]
    return {f"A2_{mechanism}_{index:03d}" for index in range(100)}


def _a2_rate_rows(outcomes):
    from .synthetic_execution import aggregate_rates
    return [dict(row, status='RECOVERED_SAVED_A2_ONLY') for row in aggregate_rates(outcomes)]


def unknown_rate_rows(planned):
    """Return the 15 non-A2 fixed-denominator rows as budget unknowns."""
    _expected_planned(planned)
    from .synthetic_execution import aggregate_rates
    outcomes = []
    for world in planned:
        packet = world['packet']
        if packet=='A2':
            continue
        mechanism = ('null' if world['world_index']<30 else 'injected') if packet=='G0' else world['mechanism']
        families = ('logistic','mlp32') if packet=='N3' else ('mlp32',) if packet=='N1' else ('logistic',)
        for family in families:
            outcomes.append(dict(world_id=world['id'],packet=packet,mechanism=mechanism,family=family,
                status='UNKNOWN_BUDGET',screen=None,expected_positive=mechanism in (
                    'BACKGROUND_KEY','ADDITIVE_NOISE','COVARIANCE_SIGNAL','EEG_INCREMENT','injected')))
    return [dict(row,status='UNKNOWN_BUDGET') for row in aggregate_rates(outcomes)]


def aggregate_saved_a2_statistics(statistics_path, output_csv):
    """Aggregate the existing A2 parquet without loading a model or fitting."""
    import pandas as pd
    import numpy as np
    table = pd.read_parquet(statistics_path)
    required = {"world_id", "mechanism", "condition", "component", "metric", "estimate"}
    if not required.issubset(table.columns):
        _error("SYNTHETIC_TIMEOUT_A2_STATISTICS_SCHEMA")
    rows = []
    expected_components = {
        *((name, 'identity_error') for name in ("max_pair_error", "matching_gain_error")),
        *((name, metric) for name in ("delta", "prediction", "residual")
          for metric in ("cosine", "inner_product")),
        *((name, "decomposition_inner_product") for name in
          ("delta_delta", "minus_delta_prediction", "minus_prediction_delta",
           "prediction_prediction", "residual")),
    }
    seen = set()
    expected_groups = {(m,c,*component) for m in A2_MECHANISMS for c in ('zero','fixed','fitted')
        for component in expected_components}
    for key, group in table.groupby(["mechanism", "condition", "component", "metric"], sort=True):
        seen.add(key)
        if len(group) != 100 or set(group.world_id) != _a2_ids_for_group(group.to_dict("records")):
            _error("SYNTHETIC_TIMEOUT_A2_STATISTIC_WORLD_COVERAGE")
        values = pd.to_numeric(group["estimate"], errors="raise")
        if np.isinf(values.to_numpy(float)).any():
            _error('SYNTHETIC_TIMEOUT_A2_INFINITE_STATISTIC')
        undefined = values.isna()
        if undefined.any() and not (key[1:] == ('zero','prediction','cosine') and undefined.all()):
            _error('SYNTHETIC_TIMEOUT_A2_UNEXPECTED_UNDEFINED_STATISTIC')
        finite = values[~undefined]
        if key[3]=='identity_error' and (finite<0).any():
            _error('SYNTHETIC_TIMEOUT_A2_IDENTITY_ERROR')
        rows.append(dict(zip(("mechanism", "condition", "component", "metric"), key),
            n_planned=100, n_defined=int(finite.size), n_undefined=100 - int(finite.size),
            estimate_mean=float(finite.mean()) if len(finite) else None,
            estimate_max=float(finite.max()) if len(finite) else None,
            scope="saved A2 statistics; no model read or refit"))
    if seen != expected_groups or len(rows) != len(expected_groups):
        _error("SYNTHETIC_TIMEOUT_A2_STATISTIC_GROUP_COVERAGE")
    pd.DataFrame(rows).to_csv(output_csv, index=False)
    return rows


def validate_saved_screens(statistics_path, outcomes):
    """Cross-check saved screen booleans against the saved, frozen-threshold CI."""
    import pandas as pd
    table = pd.read_parquet(statistics_path)
    own = table[table.metric.eq('cosine') & table.component.isin(['delta','residual'])]
    if len(own) != len(outcomes):
        _error('SYNTHETIC_TIMEOUT_A2_SCREEN_STATISTIC_COVERAGE')
    lookup = {(r['world_id'],r['condition']+'__'+r['component']):r for r in own.to_dict('records')}
    if len(lookup) != len(outcomes):
        _error('SYNTHETIC_TIMEOUT_A2_SCREEN_STATISTIC_DUPLICATE')
    for row in outcomes:
        stat = lookup[(row['world_id'],row['family'])]
        evaluable = stat['status']=='EVALUATED' and pd.notna(stat['ci_lower'])
        expected = bool(stat['estimate']>=.05 and stat['ci_lower']>0) if evaluable else None
        if row['screen'] is not expected or (row['status']=='EVALUATED') != evaluable:
            _error('SYNTHETIC_TIMEOUT_A2_SAVED_SCREEN_MISMATCH')


def run(config, registry, site, dest, public, report, original_run="synthetic_001"):
    """Create a budget-limited recovery run after an externally confirmed timeout."""
    require_slurm()
    dest, public, report = map(lambda value: Path(value).resolve(), (dest, public, report))
    for path, base in ((dest, "private"), (public, "results"), (report, "reports")):
        if not path.is_relative_to(ROOT / base / "auditory_next_v2"):
            _error("SYNTHETIC_TIMEOUT_OUTPUT_ROOT")
    if original_run != "synthetic_001":
        _error("SYNTHETIC_TIMEOUT_ONLY_SYNTHETIC_001")
    original = ROOT / "private/auditory_next_v2" / original_run
    terminal_dir = ROOT / "private/auditory_next_v2" / "scheduler_terminal"
    start, terminal = validate_timeout_gate(original, terminal_dir)
    if config.get('A2',{}).get('effect_floor') != .05:
        _error('SYNTHETIC_TIMEOUT_FROZEN_A2_THRESHOLD')
    if not (dest / "start.json").is_file():
        _error("SYNTHETIC_TIMEOUT_NEW_RUN_START_REQUIRED")
    if (dest / "completion.json").exists() or (dest / "recovery_receipt.json").exists():
        raise FileExistsError("SYNTHETIC_TIMEOUT_DESTINATION_IMMUTABLE")
    planned_path = original / "planned_worlds.json"
    planned = _expected_planned(json.loads(planned_path.read_text()))
    hashes = {str(path): digest(path) for path in (original / "start.json", terminal, planned_path)}
    module = Path(__file__).with_name('synthetic_execution.py')
    legacy_module = original/'source/auditory_next/synthetic_execution.py'
    expected_module = start.get('source_hashes',{}).get('auditory_next/synthetic_execution.py')
    if not expected_module or digest(module)!=expected_module or digest(legacy_module)!=expected_module:
        _error('SYNTHETIC_TIMEOUT_AGGREGATOR_SOURCE_PARITY')
    hashes[str(module)] = hashes[str(legacy_module)] = expected_module
    _validate_a2_receipts(original, hashes)
    _validate_prepared_hashes(original, hashes)
    outcomes = _load_and_validate_a2(original, hashes)
    a2_statistics = original / "A2_all_world_statistics.parquet"
    if not a2_statistics.is_file():
        _error("SYNTHETIC_TIMEOUT_A2_STATISTICS_MISSING")
    hashes[str(a2_statistics)] = digest(a2_statistics)
    validate_saved_screens(a2_statistics, outcomes)
    dest.mkdir(parents=True, exist_ok=True)
    public.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    write_json(dest / "source_file_hashes.json", hashes)
    write_json(dest / "recovery_receipt.json", dict(status="BUDGET_LIMITED",
        original_run=original_run, original_job_id=start["job_id"], terminal_receipt_hash=digest(terminal),
        original_source_snapshot_hash=object_hash(start.get("source_hashes", {})),
        planned_worlds=660, a2_worlds=300, a2_ridge_fits_reused=300, new_head_fits=0,
        new_ridge_fits=0, model_reads=0, generator_calls=0,
        a2_source_statistics_hash=hashes[str(a2_statistics)],
        note="A2 statistics/outcomes were aggregated from saved files; no model was read or refit. Output hashes were first captured during recovery, not at the original A2 write."))
    import pandas as pd
    rates = _a2_rate_rows(outcomes) + unknown_rate_rows(planned)
    if len(rates) != 33:
        _error("SYNTHETIC_TIMEOUT_FIXED_RATE_ROWS")
    pd.DataFrame(rates).to_csv(public / "synthetic_rates.csv", index=False)
    aggregate_saved_a2_statistics(a2_statistics, public / "A2_residual_audit_aggregate.csv")
    if any(not Path(path).is_file() or digest(path)!=value for path,value in hashes.items()):
        _error("SYNTHETIC_TIMEOUT_SOURCES_CHANGED_DURING_READ")
    validate_timeout_gate(original, terminal_dir)
    (report / "SYNTHETIC_TIMEOUT_RECOVERY.md").write_text(
        "# Synthetic timeout recovery\n\n"
        "The original synthetic_001 job was externally confirmed TIMEOUT before the classifier family barrier. "
        "The 300 completed A2 ridge receipts and saved A2 statistics were aggregated without model reads or refits. "
        "N1/N2/N3/G0 remain UNKNOWN_BUDGET in their fixed 30-world denominators; unknown worlds are not assigned "
        "negative outcomes. This report does not recover classifier predictions.\n")
    summary = dict(stage="SYNTHETIC_TIMEOUT_RECOVERY", status="BUDGET_LIMITED_A2_OUTPUTS_RECOVERED",
        implementation_status="BUDGET_LIMITED", original_execution_status="TIMEOUT",
        scientific_status="NOT_EVALUATED_FOR_N1_N2_N3_G0",
        original_run=original_run, planned_worlds=660, rate_rows=33,
        a2_worlds=300, a2_ridge_fits_reused=300, new_head_fits=0, new_ridge_fits=0,
        model_reads=0, generator_calls=0, unknown_budget_worlds=360,
        output_scope="saved A2 descriptive aggregation plus fixed-denominator unknown placeholders")
    return finish(dest, public, summary)
