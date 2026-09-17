"""Pure parser/accounting tests for resource_accounting.py."""

from auditory_next.resource_accounting import (
    aggregate_accounting,
    combine_accounting,
    discover_job_records,
    parse_duration_seconds,
    parse_gpu_count,
    parse_scontrol_row,
    parse_timelimit_seconds,
    parse_sacct_rows,
)


def test_archives_require_exact_job_and_actual_terminal_state(tmp_path):
    from auditory_next.resource_accounting import archived_scontrol_rows
    (tmp_path/'42.txt').write_text('JobId=42 JobState=COMPLETED RunTime=00:48:33 TimeLimit=06:00:00 NumCPUs=2 AllocTRES=cpu=2,gres/gpu=1')
    (tmp_path/'43.txt').write_text('JobId=43 JobState=RUNNING RunTime=00:20:00 NumCPUs=2 AllocTRES=cpu=2,gres/gpu=1')
    (tmp_path/'44.txt').write_text('JobId=45 JobState=TIMEOUT RunTime=02:00:00 NumCPUs=2 AllocTRES=cpu=2,gres/gpu=1')
    (tmp_path/'46.txt').write_text('JobState=TIMEOUT RunTime=02:00:00 NumCPUs=2 AllocTRES=cpu=2,gres/gpu=1')
    rows=archived_scontrol_rows(tmp_path,['42','43','44','45','46'])
    assert len(rows)==1 and rows[0]['job_id']=='42'
    assert rows[0]['elapsed_seconds']==2913 and rows[0]['gpu_count']==1
    assert rows[0]['accounting_source']=='scontrol'
    assert len(rows[0]['archive_sha256'])==64


def test_duration_and_typed_gpu_parsers():
    assert parse_duration_seconds("3661") == 3661
    assert parse_duration_seconds("1-02:03:04") == 93784
    assert parse_duration_seconds("00:30:00") == 1800
    assert parse_timelimit_seconds("10") == 600
    assert parse_gpu_count("cpu=2,gres/gpu=1") == 1
    # Slurm may report both a generic and typed GPU TRES; typed entries are
    # authoritative and must not be added to the generic count.
    assert parse_gpu_count("gres/gpu=2,gres/gpu:a40=1") == 1
    assert parse_gpu_count("gres/gpu:a40=1,gres/gpu:a100=2") == 3
    assert parse_gpu_count("cpu=2") == 0
    assert parse_gpu_count("cpu=2,mem=4G") == 0


def test_sacct_keeps_exact_rows_only():
    text = "\n".join([
        "100|main|COMPLETED|60|2|cpu=2,gres/gpu=1|10",
        "100.batch|main.batch|COMPLETED|60|2|cpu=2,gres/gpu=1|10",
        "100.extern|extern|COMPLETED|60|2|cpu=2,gres/gpu=1|10",
        "101|other|RUNNING|00:01:00|4|cpu=4,gres/gpu:a40=1|60",
    ])
    rows = parse_sacct_rows(text, ["100"])
    assert [row["job_id"] for row in rows] == ["100"]
    assert rows[0]["gpu_count"] == 1
    assert rows[0]["time_limit_seconds"] == 600


def test_scontrol_fallback_uses_seconds_runtime_and_minutes_like_clock_limit():
    row = parse_scontrol_row(
        "JobId=500 JobName=readout JobState=RUNNING RunTime=00:01:00 "
        "TimeLimit=01:00:00 NumCPUs=2 AllocTRES=cpu=2,gres:gpu:a40:1", "500")
    assert row["elapsed_seconds"] == 60
    assert row["time_limit_seconds"] == 3600
    assert row["allocated_cpus"] == 2
    assert row["gpu_count"] == 1


def test_pending_zero_alloc_cpu_uses_requested_and_missing_sacct_is_distinct():
    records = [{"job_id": "3", "run": "pending", "sources": [], "requested_cpus": 2,
                "requested_gpu": 0, "requested_time_limit_seconds": 600}]
    measured = [{"job_id": "3", "job_name": "pending", "state": "PENDING",
                 "elapsed_seconds": 0, "allocated_cpus": 0, "gpu_count": 0,
                 "time_limit_seconds": 600, "alloc_tres": "cpu=0,mem=4G"}]
    rows = combine_accounting(records, measured, sacct_available=True)
    assert rows[0]["allocated_cpus"] == 2
    assert rows[0]["upper_cpu_core_hours"] == 1 / 3
    assert rows[0]["bound_basis"] == "sacct_timelimit_active"
    assert rows[0]["accounting_status"] == "ACCOUNTED_WITH_FALLBACK"
    missing = combine_accounting(records, [], sacct_available=False)[0]
    assert missing["accounting_status"] == "UNAVAILABLE"
    assert missing["bound_basis"] == "requested_config_sacct_unavailable"


def test_discovery_deduplicates_start_controller_and_explicit_probe(tmp_path):
    v2 = tmp_path / "private" / "auditory_next_v2"
    (v2 / "run_a").mkdir(parents=True)
    (v2 / "run_a" / "start.json").write_text('{"run":"run_a","job_id":"700"}')
    (v2 / "run_b").mkdir()
    (v2 / "run_b" / "controller_note.json").write_text('{"job_id":"700","cpus":2}')
    (v2 / "controller_jobs.json").write_text('{"jobs":[{"job_id":"701","run":"queued","cpus":2,"gpu":1,"time_limit_seconds":60}]}')
    rows = discover_job_records(tmp_path)
    by_id = {row["job_id"]: row for row in rows}
    assert len([row for row in rows if row["job_id"] == "700"]) == 1
    assert by_id["700"]["requested_cpus"] == 2
    assert by_id["701"]["requested_gpu"] == 1
    assert "996755" in by_id and "996758" in by_id


def test_running_reservation_uses_full_limit_and_cpu_includes_gpu_host():
    records = [{"job_id": "1", "run": "x", "sources": [], "requested_cpus": 2,
                "requested_gpu": 1, "requested_time_limit_seconds": 3600}]
    rows = combine_accounting(records, [{"job_id": "1", "job_name": "x", "state": "RUNNING",
        "elapsed_seconds": 60, "allocated_cpus": 2, "gpu_count": 1,
        "time_limit_seconds": 3600, "alloc_tres": "gres/gpu=1"}], sacct_available=True)
    assert rows[0]["actual_cpu_core_hours"] == 2 / 60
    assert rows[0]["upper_cpu_core_hours"] == 2
    assert rows[0]["actual_gpu_hours"] == 1 / 60
    summary = aggregate_accounting(rows)
    assert summary["reservation_upper_cpu_core_hours"] == 2
    assert summary["reservation_upper_gpu_hours"] == 1


def test_missing_sacct_is_unknown_and_never_zero():
    records = [{"job_id": "2", "run": "x", "sources": [], "requested_cpus": 2,
                "requested_gpu": 1, "requested_time_limit_seconds": 600}]
    rows = combine_accounting(records, [], sacct_available=False)
    assert rows[0]["actual_cpu_core_hours"] is None
    assert rows[0]["actual_gpu_hours"] is None
    assert rows[0]["actual_cpu_core_hours_lower_bound"] is None
    assert rows[0]["upper_cpu_core_hours"] == 1 / 3
    assert rows[0]["upper_gpu_hours"] == 1 / 6
    assert rows[0]["accounting_status"] == "UNAVAILABLE"
    assert aggregate_accounting(rows)["status"] == "ACCOUNTING_UNAVAILABLE"


def test_completion_receipt_is_lower_bound_not_exact_accounting():
    records = [{"job_id": "5", "run": "old", "sources": [], "requested_cpus": 2,
                "requested_gpu": 0, "requested_time_limit_seconds": 1800,
                "completion_elapsed_seconds": 120, "completion_status": "PASS"}]
    row = combine_accounting(records, [], sacct_available=False)[0]
    assert row["actual_cpu_core_hours"] is None
    assert row["actual_cpu_core_hours_lower_bound"] == 1 / 15
    assert row["upper_cpu_core_hours"] == 1
    assert row["bound_basis"] == "completion_receipt_plus_requested_limit"


def test_pending_null_allocation_preserves_requested_gpu_reservation():
    row = parse_scontrol_row('JobId=703 JobState=PENDING RunTime=00:00:00 TimeLimit=06:00:00 NumCPUs=2 AllocTRES=(null) ReqTRES=cpu=2,mem=64G,gres/gpu=1','703')
    assert row['gpu_count'] == 1
    request = dict(job_id='703', requested_cpus=2, requested_gpu=1,requested_time_limit_seconds=21600)
    result=combine_accounting([request],[],sacct_available=False,scontrol_rows=[row])[0]
    assert result['upper_gpu_hours'] == 6.
    assert result['actual_gpu_hours'] == 0.
    assert parse_gpu_count('(null)') is None


def test_cancelled_controller_job_without_start_has_zero_usage_and_bound():
    records = [{"job_id": "4", "run": "cancelled", "sources": [], "requested_cpus": 2,
                "requested_gpu": 1, "requested_time_limit_seconds": 21600,
                "controller_state": "CANCELLED", "controller_started": False}]
    row = combine_accounting(records, [], sacct_available=False)[0]
    assert row["never_started"] is True
    assert row["actual_cpu_core_hours"] == 0.0
    assert row["actual_gpu_hours"] == 0.0
    assert row["upper_cpu_core_hours"] == 0.0
    assert row["upper_gpu_hours"] == 0.0
    assert row["bound_basis"] == "controller_never_started"
