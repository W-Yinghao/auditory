"""Slurm resource accounting for the auditory-next v2 round.

This module does not inspect EEG or fit models.  The public output is an
aggregate budget record; job identifiers and per-job accounting stay private.
The ``.tmp`` suffix is intentional until the parent agent's contract review.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable, Mapping

from .provenance import finish as provenance_finish


SACCT_FORMAT = "JobIDRaw,JobName,State,ElapsedRaw,AllocCPUS,AllocTRES,TimelimitRaw"
EXPLICIT_PROBES = {
    "996755": {"run": "adapter_probe_001", "cpus": 2, "gpu": 0, "time_limit_seconds": 600},
    "996758": {"run": "adapter_probe_002", "cpus": 2, "gpu": 0, "time_limit_seconds": 600},
}
ACTIVE_STATES = {
    "PENDING", "RUNNING", "CONFIGURING", "COMPLETING", "RESIZING",
    "SUSPENDED", "STAGE_OUT", "STOPPED",
}
GPU_CORE_RUNS = {"N1_core", "N2_core", "N3_core", "C2R_core", "E0R_core"}
_MISSING = {"", "-", "N/A", "NA", "UNKNOWN", "UNAVAILABLE", "UNK", "NONE"}


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _job_id(value: Any) -> str | None:
    value = _text(value)
    # The round uses ordinary jobs.  Array-step and .batch/.extern rows are
    # intentionally not silently converted to their parent job.
    return value if re.fullmatch(r"[0-9]+(?:_[0-9]+)?", value) else None


def _number(value: Any, *, integer: bool = False) -> int | float | None:
    value = _text(value)
    if value.upper() in _MISSING:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number < 0:
        return None
    return int(number) if integer else number


def _boolish(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    value = _text(value).lower()
    if value in {"true", "yes", "1", "started", "running"}:
        return True
    if value in {"false", "no", "0", "not_started", "pending"}:
        return False
    return None


def parse_duration_seconds(value: Any) -> int | None:
    """Parse Slurm raw seconds or common elapsed/time-limit notation."""
    raw = _text(value)
    if raw.upper() in _MISSING or raw.upper() in {"UNLIMITED", "INFINITE"}:
        return None
    number = _number(raw, integer=True)
    if number is not None:
        return number
    days = 0
    if "-" in raw:
        day_text, raw = raw.split("-", 1)
        if not day_text.isdigit():
            return None
        days = int(day_text)
    parts = raw.split(":")
    try:
        if len(parts) == 3:
            hours, minutes, seconds = (int(part) for part in parts)
        elif len(parts) == 2:
            hours, minutes, seconds = 0, int(parts[0]), int(parts[1])
        else:
            return None
    except ValueError:
        return None
    if minutes >= 60 or seconds >= 60 or hours < 0:
        return None
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def parse_timelimit_seconds(value: Any) -> int | None:
    """Parse sacct TimelimitRaw (numeric values are minutes, not seconds)."""
    raw = _text(value)
    if raw.upper() in _MISSING or raw.upper() in {"UNLIMITED", "INFINITE"}:
        return None
    number = _number(raw, integer=False)
    if number is not None:
        return int(number * 60)
    # Non-numeric site-formatted limits are already clock durations.
    return parse_duration_seconds(raw)


def parse_gpu_count(alloc_tres: Any) -> int | None:
    """Return GPU count from AllocTRES without generic/typed double counting."""
    if _text(alloc_tres).upper() in _MISSING | {'(NULL)', 'NULL', '(NONE)'}:
        return None
    raw = _text(alloc_tres)
    if raw.upper() in _MISSING:
        return None
    generic: int | None = None
    typed_total = 0
    typed_seen = False
    for token in _text(alloc_tres).split(","):
        key, separator, value = token.partition("=")
        if not separator:
            continue
        key = key.strip().lower()
        count = _number(value, integer=True)
        if count is None:
            continue
        if key == "gres/gpu":
            generic = count
        elif key.startswith("gres/gpu:"):
            typed_seen = True
            typed_total += count
    if typed_seen:
        return typed_total
    # A non-empty AllocTRES with no GPU TRES is a valid CPU-only allocation;
    # the absence of the token is therefore an observed zero, not missing.
    return 0 if generic is None else generic


def parse_sacct_rows(text: str, requested_ids: Iterable[str] | None = None) -> list[dict[str, Any]]:
    """Parse ``sacct -P -n`` output, retaining only exact allocation rows."""
    requested = None if requested_ids is None else {_job_id(value) for value in requested_ids}
    requested.discard(None) if requested is not None else None
    rows: list[dict[str, Any]] = []
    for line in _text(text).splitlines():
        fields = line.rstrip("\r").split("|")
        if len(fields) < 7:
            continue
        jid = _job_id(fields[0])
        if jid is None or (requested is not None and jid not in requested):
            continue
        # Exact requested IDs only: job.batch, job.extern and other steps have
        # a suffix and therefore fail _job_id or do not equal the request.
        rows.append({
            "job_id": jid,
            "job_name": fields[1].strip(),
            "state": fields[2].strip(),
            "elapsed_seconds": parse_duration_seconds(fields[3]),
            "allocated_cpus": _number(fields[4], integer=True),
            "gpu_count": parse_gpu_count(fields[5]),
            "time_limit_seconds": parse_timelimit_seconds(fields[6]),
            "alloc_tres": fields[5].strip(),
        })
    return rows


def parse_scontrol_row(text: str, requested_id: str | None = None) -> dict[str, Any] | None:
    """Parse one ``scontrol show job ID -o`` record."""
    fields = dict(re.findall(r"([A-Za-z][A-Za-z0-9_]*)=([^\s]+)", text))
    jid = _job_id(fields.get("JobId") or fields.get("JobID") or requested_id)
    if jid is None or (requested_id is not None and jid != _job_id(requested_id)):
        return None
    tres = next((fields[key] for key in ('AllocTRES','TRES','ReqTRES','TresPerNode')
                 if fields.get(key,'').upper() not in _MISSING | {'(NULL)','NULL','(NONE)'}), '')
    # scontrol commonly spells GRES as gres:gpu[:type]:N rather than the
    # sacct gres/gpu=N spelling.  Convert only this resource token.
    gpu = parse_gpu_count(tres)
    if gpu == 0 and "gres:gpu" in tres.lower():
        typed = re.findall(r"gres:gpu(?::[^,:=]+)*:(\d+)", tres.lower())
        gpu = sum(int(value) for value in typed) if typed else None
    return {
        "job_id": jid, "job_name": fields.get("JobName", ""),
        "state": fields.get("JobState", "UNKNOWN").split("+", 1)[0],
        "elapsed_seconds": parse_duration_seconds(fields.get("RunTime")),
        "allocated_cpus": _number(fields.get("NumCPUs"), integer=True),
        "gpu_count": gpu,
        "time_limit_seconds": parse_duration_seconds(fields.get("TimeLimit")),
        "alloc_tres": tres, "accounting_source": "scontrol",
    }


def _merge_record(records: dict[str, dict[str, Any]], job_id: Any, *, run: Any = None,
                  source: str, cpus: Any = None, gpu: Any = None,
                  time_limit_seconds: Any = None, state: Any = None,
                  started: Any = None, completion_elapsed_seconds: Any = None,
                  completion_status: Any = None) -> None:
    jid = _job_id(job_id)
    if jid is None:
        return
    row = records.setdefault(jid, {
        "job_id": jid, "run": "", "sources": [],
        "requested_cpus": None, "requested_gpu": None,
        "requested_time_limit_seconds": None,
        "controller_state": None, "controller_started": None,
        "completion_elapsed_seconds": None, "completion_status": None,
    })
    if source not in row["sources"]:
        row["sources"].append(source)
    if _text(run) and not row["run"]:
        row["run"] = _text(run)
    for key, value in (("requested_cpus", _number(cpus, integer=True)),
                       ("requested_gpu", _number(gpu, integer=True)),
                       ("requested_time_limit_seconds", parse_duration_seconds(time_limit_seconds))):
        if value is not None and row[key] is None:
            row[key] = value
    if _text(state) and row["controller_state"] is None:
        row["controller_state"] = _text(state)
    started_value = _boolish(started)
    if started_value is not None and row["controller_started"] is None:
        row["controller_started"] = started_value
    elapsed = parse_duration_seconds(completion_elapsed_seconds)
    if elapsed is not None and row["completion_elapsed_seconds"] is None:
        row["completion_elapsed_seconds"] = elapsed
    if _text(completion_status) and row["completion_status"] is None:
        row["completion_status"] = _text(completion_status)


def missing_request_defaults(run: Any) -> dict[str, Any]:
    """Conservative requested-resource defaults for receipts lacking a ledger.

    Explicit controller values always win.  The named GPU families mirror the
    frozen controller allocation; all other runs use the historical CPU
    wrapper default and no GPU, with the default basis recorded privately.
    """
    label = _text(run)
    stem = label.rsplit("_", 1)[0] if "_" in label else label
    if stem in GPU_CORE_RUNS:
        return {"cpus": 2, "gpu": 1, "time_limit_seconds": 21600,
                "basis": "frozen_gpu_core_wrapper"}
    return {"cpus": 2, "gpu": 0, "time_limit_seconds": 1800,
            "basis": "historical_cpu_wrapper_default"}


def discover_job_records(root: str | Path, controller_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Discover and de-duplicate v2 jobs from private receipts/controllers."""
    root = Path(root)
    v2 = root / "private" / "auditory_next_v2"
    records: dict[str, dict[str, Any]] = {}
    for start in sorted(v2.glob("*/start.json")):
        try:
            payload = json.loads(start.read_text())
        except (OSError, ValueError):
            continue
        completion = {}
        completion_path = start.parent / "completion.json"
        if completion_path.exists():
            try:
                completion = json.loads(completion_path.read_text())
            except (OSError, ValueError):
                completion = {}
        _merge_record(records, payload.get("job_id"), run=payload.get("run"),
                      source=f"start:{start.parent.name}",
                      completion_elapsed_seconds=completion.get("elapsed_seconds"),
                      completion_status=completion.get("status"))

    # Controller notes may be JSON or a one-line .job_id receipt.
    for note in sorted(v2.glob("*/controller_note*.json")):
        try:
            payload = json.loads(note.read_text())
        except (OSError, ValueError):
            continue
        if isinstance(payload, Mapping):
            _merge_record(records, payload.get("job_id"), run=payload.get("run"),
                          source=f"controller_note:{note.parent.name}",
                          cpus=payload.get("cpus"), gpu=payload.get("gpu"),
                          time_limit_seconds=payload.get("time_limit_seconds"),
                          state=payload.get("state"), started=payload.get("started"))
    for note in sorted(v2.glob("*/controller_note.job_id")):
        try:
            value = note.read_text().strip()
        except OSError:
            continue
        _merge_record(records, value, source=f"controller_note_job_id:{note.parent.name}")

    controller = Path(controller_path) if controller_path else v2 / "controller_jobs.json"
    if controller.exists():
        try:
            payload = json.loads(controller.read_text())
        except (OSError, ValueError):
            payload = {}
        jobs = payload.get("jobs", []) if isinstance(payload, Mapping) else payload
        for job in jobs if isinstance(jobs, list) else []:
            if isinstance(job, Mapping):
                _merge_record(records, job.get("job_id"), run=job.get("run"),
                              source="controller_jobs.json",
                              cpus=job.get("cpus", job.get("requested_cpus")),
                              gpu=job.get("gpu", job.get("requested_gpu")),
                              time_limit_seconds=job.get("time_limit_seconds"),
                              state=job.get("state"), started=job.get("started"))

    for jid, info in EXPLICIT_PROBES.items():
        _merge_record(records, jid, run=info["run"], source="explicit_probe",
                      cpus=info["cpus"], gpu=info["gpu"],
                      time_limit_seconds=info["time_limit_seconds"])
    for row in records.values():
        defaults = missing_request_defaults(row["run"])
        row["request_default_basis"] = defaults["basis"]
        if row["requested_cpus"] is None:
            row["requested_cpus"] = defaults["cpus"]
        if row["requested_gpu"] is None:
            row["requested_gpu"] = defaults["gpu"]
        if row["requested_time_limit_seconds"] is None:
            row["requested_time_limit_seconds"] = defaults["time_limit_seconds"]
    return [records[jid] for jid in sorted(records)]


# Stable descriptive aliases for callers and pure tests.
discover_jobs = discover_job_records
parse_sacct_output = parse_sacct_rows


def query_sacct(job_ids: Iterable[str]) -> dict[str, Any]:
    """Query exact allocation rows; this is the only scheduler operation."""
    ids = sorted({_job_id(value) for value in job_ids} - {None})
    if not ids:
        return {"available": False, "returncode": None, "rows": [], "stderr": "NO_JOB_IDS"}
    command = ["sacct", "-P", "-n", "-j", ",".join(ids), "--format=" + SACCT_FORMAT]
    try:
        result = subprocess.run(command, text=True, capture_output=True, check=False)
    except OSError as exc:
        return {"available": False, "returncode": None, "rows": [], "stderr": str(exc), "command": command}
    return {
        "available": result.returncode == 0,
        "returncode": result.returncode,
        "rows": parse_sacct_rows(result.stdout, ids),
        "stderr": result.stderr.strip(),
        "command": command,
    }


def query_scontrol(job_ids: Iterable[str]) -> dict[str, Any]:
    """Fallback scheduler lookup for IDs absent/unavailable in sacct."""
    ids = sorted({_job_id(value) for value in job_ids} - {None})
    rows: list[dict[str, Any]] = []
    errors: dict[str, str] = {}
    for jid in ids:
        command = ["scontrol", "show", "job", jid, "-o"]
        try:
            result = subprocess.run(command, text=True, capture_output=True, check=False)
        except OSError as exc:
            errors[jid] = str(exc)
            continue
        if result.returncode != 0:
            errors[jid] = result.stderr.strip() or f"returncode={result.returncode}"
            continue
        row = parse_scontrol_row(result.stdout, jid)
        if row is None:
            errors[jid] = "NO_EXACT_SCONTROL_ROW"
        else:
            rows.append(row)
    return {"available": bool(rows), "rows": rows, "errors": errors,
            "queried_ids": ids}


def _is_active(state: Any) -> bool:
    state = _text(state).upper().split("+", 1)[0]
    return state in ACTIVE_STATES


def archived_scontrol_rows(folder: Path, requested_ids: Iterable[str]) -> list[dict[str, Any]]:
    """Preserved exact controller outputs can survive Slurm's retention window."""
    rows = []
    terminal = {'COMPLETED','FAILED','TIMEOUT','OUT_OF_MEMORY','CANCELLED','NODE_FAIL','PREEMPTED'}
    for jid in sorted({_job_id(value) for value in requested_ids} - {None}):
        path = Path(folder)/(jid+'.txt')
        if not path.is_file() or path.is_symlink():
            continue
        content = path.read_text()
        if not re.search(r'\bJobId='+re.escape(jid)+r'(?:\s|$)',content):
            continue
        row = parse_scontrol_row(content, jid)
        if row is None or row['state'] not in terminal or row['elapsed_seconds'] is None:
            continue
        row.update(evidence='archived_exact_terminal_scontrol', archive_path=str(path),
            archive_sha256=hashlib.sha256(content.encode()).hexdigest())
        rows.append(row)
    return rows


def combine_accounting(records: Iterable[Mapping[str, Any]], sacct_rows: Iterable[Mapping[str, Any]],
                       *, sacct_available: bool, scontrol_rows: Iterable[Mapping[str, Any]] = (),
                       scontrol_available: bool = False) -> list[dict[str, Any]]:
    """Join scheduler rows and calculate actual usage plus conservative bounds."""
    by_id = {str(row["job_id"]): row for row in sacct_rows if _job_id(row.get("job_id"))}
    by_control_id = {str(row["job_id"]): row for row in scontrol_rows if _job_id(row.get("job_id"))}
    output = []
    for requested in records:
        jid = str(requested["job_id"])
        measured = by_id.get(jid)
        accounting_source = "sacct" if measured is not None else ""
        missing: list[str] = []
        if measured is None and by_control_id.get(jid) is not None:
            measured = by_control_id[jid]
            accounting_source = "scontrol"
        never_started = (measured is None and requested.get("controller_started") is False and
                         _text(requested.get("controller_state")).upper() in {"CANCELLED", "CANCELED"})
        fallback_receipt_elapsed = False
        if measured is None:
            missing.append("sacct_row")
            fallback_elapsed = 0 if never_started else requested.get("completion_elapsed_seconds")
            fallback_receipt_elapsed = fallback_elapsed is not None and not never_started
            measured = {"state": requested.get("controller_state") or
                               requested.get("completion_status") or "UNAVAILABLE",
                        "elapsed_seconds": fallback_elapsed,
                        "allocated_cpus": None, "gpu_count": None,
                        "time_limit_seconds": None, "job_name": "", "alloc_tres": ""}
            accounting_source = "completion_receipt" if fallback_receipt_elapsed else "requested_fallback"
        state = _text(measured.get("state")) or "UNKNOWN"
        active = _is_active(state)
        def choose(field: str, fallback_field: str) -> Any:
            value = measured.get(field)
            # Pending jobs can be reported with AllocCPUS=0 before resources
            # are allocated.  Their authorized controller allocation is the
            # conservative CPU basis for the reservation bound.
            if (field in ("allocated_cpus", "gpu_count") and value == 0 and active and
                    _number(requested.get(fallback_field), integer=True) not in (None, 0)):
                value = None
            if value is None:
                value = requested.get(fallback_field)
                if value is None:
                    missing.append(field)
                else:
                    missing.append(f"{field}:requested_fallback")
            return value
        elapsed = measured.get("elapsed_seconds")
        if elapsed is None and "sacct_row" not in missing:
            missing.append("elapsed_seconds")
        cpus = choose("allocated_cpus", "requested_cpus")
        gpu = choose("gpu_count", "requested_gpu")
        limit = choose("time_limit_seconds", "requested_time_limit_seconds")
        measured_cpu = (0.0 if never_started and cpus is not None else
                        None if elapsed is None or cpus is None else elapsed * cpus / 3600.0)
        measured_gpu = (0.0 if never_started and gpu is not None else
                        None if elapsed is None or gpu is None else elapsed * gpu / 3600.0)
        exact_accounting = accounting_source in {"sacct", "scontrol"}
        actual_cpu = 0.0 if never_started and cpus is not None else measured_cpu if exact_accounting else None
        actual_gpu = 0.0 if never_started and gpu is not None else measured_gpu if exact_accounting else None
        if never_started:
            upper_cpu = 0.0 if cpus is not None else None
        elif cpus is None:
            upper_cpu = None
        elif active or fallback_receipt_elapsed:
            upper_cpu = None if limit is None else limit * cpus / 3600.0
        else:
            upper_cpu = (elapsed * cpus / 3600.0 if elapsed is not None else
                         limit * cpus / 3600.0 if limit is not None else None)
        if never_started:
            upper_gpu = 0.0 if gpu is not None else None
        elif gpu is None:
            upper_gpu = None
        elif active or fallback_receipt_elapsed:
            upper_gpu = None if limit is None else limit * gpu / 3600.0
        else:
            upper_gpu = (elapsed * gpu / 3600.0 if elapsed is not None else
                         limit * gpu / 3600.0 if limit is not None else None)
        output.append({
            "job_id": jid, "run": requested.get("run", ""), "state": state,
            "job_name": measured.get("job_name", ""), "alloc_tres": measured.get("alloc_tres", ""),
            "elapsed_seconds": elapsed, "allocated_cpus": cpus, "gpu_count": gpu,
            "time_limit_seconds": limit, "active_reservation": active,
            "never_started": never_started, "accounting_source": accounting_source,
            "actual_cpu_core_hours": actual_cpu, "actual_gpu_hours": actual_gpu,
            "actual_cpu_core_hours_lower_bound": measured_cpu,
            "actual_gpu_hours_lower_bound": measured_gpu,
            "upper_cpu_core_hours": upper_cpu, "upper_gpu_hours": upper_gpu,
            "missing_fields": sorted(set(missing)),
            "bound_basis": ("controller_never_started" if never_started else
                             "completion_receipt_plus_requested_limit" if fallback_receipt_elapsed else
                             "requested_config_sacct_unavailable" if "sacct_row" in missing else
                             "sacct_timelimit_active" if active and limit is not None else
                             "sacct_elapsed" if elapsed is not None else
                             "requested_config_fallback" if limit is not None else "unknown"),
            "accounting_status": ("UNAVAILABLE" if accounting_source == "requested_fallback" else
                                  "SACCT_ROW_MISSING" if "sacct_row" in missing and accounting_source == "" else
                                  "ACCOUNTED_WITH_FALLBACK" if missing else "ACCOUNTED"),
            "discovery_sources": list(requested.get("sources", [])),
        })
    return output


def aggregate_accounting(rows: Iterable[Mapping[str, Any]], *, max_cpu_hours: float = 256,
                         max_gpu_hours: float = 32) -> dict[str, Any]:
    rows = list(rows)
    def total(key: str) -> float:
        return float(sum(float(row[key]) for row in rows if row.get(key) is not None))
    def complete(key: str) -> bool:
        return all(row.get(key) is not None for row in rows)
    cpu_actual_complete = complete("actual_cpu_core_hours")
    gpu_actual_complete = complete("actual_gpu_hours")
    cpu_lower_complete = complete("actual_cpu_core_hours_lower_bound")
    gpu_lower_complete = complete("actual_gpu_hours_lower_bound")
    cpu_upper_complete = complete("upper_cpu_core_hours")
    gpu_upper_complete = complete("upper_gpu_hours")
    accounting_complete = bool(rows) and all(not row.get("missing_fields") for row in rows)
    cpu_actual = total("actual_cpu_core_hours") if cpu_actual_complete else None
    gpu_actual = total("actual_gpu_hours") if gpu_actual_complete else None
    cpu_upper = total("upper_cpu_core_hours") if cpu_upper_complete else None
    gpu_upper = total("upper_gpu_hours") if gpu_upper_complete else None
    if not rows or not accounting_complete:
        status = "ACCOUNTING_UNAVAILABLE" if not rows or all(row["accounting_status"] == "UNAVAILABLE" for row in rows) else "ACCOUNTING_PARTIAL"
    elif (cpu_actual is not None and cpu_actual > max_cpu_hours) or (gpu_actual is not None and gpu_actual > max_gpu_hours):
        status = "BUDGET_EXCEEDED"
    elif (cpu_upper is not None and cpu_upper > max_cpu_hours) or (gpu_upper is not None and gpu_upper > max_gpu_hours):
        status = "UPPER_BOUND_OVER_BUDGET"
    else:
        status = "WITHIN_BUDGET"
    budget_status = ('BUDGET_EXCEEDED' if
        total('actual_cpu_core_hours_lower_bound') > max_cpu_hours or total('actual_gpu_hours_lower_bound') > max_gpu_hours else
        'UNKNOWN_UPPER_BOUND' if cpu_upper is None or gpu_upper is None else
        'UPPER_BOUND_OVER_BUDGET' if cpu_upper > max_cpu_hours or gpu_upper > max_gpu_hours else
        'WITHIN_CONSERVATIVE_BOUND')
    return {
        "status": status, "jobs": len(rows),
        "budget_status": budget_status,
        "accounted_jobs": sum(row["accounting_status"] == "ACCOUNTED" for row in rows),
        "missing_jobs": sum(bool(row.get("missing_fields")) for row in rows),
        "ongoing_jobs": sum(bool(row.get("active_reservation")) for row in rows),
        "actual_cpu_core_hours": cpu_actual,
        "actual_gpu_hours": gpu_actual,
        "actual_cpu_core_hours_lower_bound": (total("actual_cpu_core_hours_lower_bound")
                                               if cpu_lower_complete else None),
        "actual_gpu_hours_lower_bound": (total("actual_gpu_hours_lower_bound")
                                          if gpu_lower_complete else None),
        "reservation_upper_cpu_core_hours": cpu_upper,
        "reservation_upper_gpu_hours": gpu_upper,
        "max_cpu_core_hours": float(max_cpu_hours), "max_gpu_hours": float(max_gpu_hours),
        "cpu_actual_complete": cpu_actual_complete, "gpu_actual_complete": gpu_actual_complete,
        "cpu_lower_bound_complete": cpu_lower_complete, "gpu_lower_bound_complete": gpu_lower_complete,
        "upper_bound_complete": cpu_upper_complete and gpu_upper_complete,
    }


def _write_csv(path: Path, rows: list[Mapping[str, Any]]) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            serial = dict(row)
            for key, value in serial.items():
                if isinstance(value, (list, tuple, dict)):
                    serial[key] = json.dumps(value, sort_keys=True)
            writer.writerow(serial)


def run(config, registry, site, dest, public, report, task_plan):
    """Collect accounting under Slurm and emit private rows/public aggregate."""
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("SLURM_REQUIRED_RESOURCE_ACCOUNTING")
    dest, public, report = Path(dest), Path(public), Path(report)
    root = Path(site.get("root", dest.resolve().parents[2])) if isinstance(site, Mapping) else dest.resolve().parents[2]
    discovered = discover_job_records(root)
    query = query_sacct([row["job_id"] for row in discovered])
    accounted_ids = {str(row["job_id"]) for row in query["rows"]}
    control_ids = [row["job_id"] for row in discovered
                   if not query["available"] or row["job_id"] not in accounted_ids]
    control = query_scontrol(control_ids)
    measured_ids = {str(row['job_id']) for row in control['rows']}
    archived = archived_scontrol_rows(root/'private/auditory_next_v2/scheduler_terminal',
        [jid for jid in control_ids if jid not in measured_ids])
    control['rows'].extend(archived)
    control['available'] = bool(control['rows'])
    control['archived_terminal_rows'] = len(archived)
    rows = combine_accounting(discovered, query["rows"], sacct_available=query["available"],
                              scontrol_rows=control["rows"],
                              scontrol_available=control["available"])
    resources = (task_plan or {}).get("resources", {}) if isinstance(task_plan, Mapping) else {}
    budget = (config or {}).get("budget", {}) if isinstance(config, Mapping) else {}
    max_cpu = float(resources.get("max_cpu_core_hours", budget.get("max_cpu_core_hours", 256)))
    max_gpu = float(resources.get("max_gpu_hours", budget.get("max_gpu_hours", 32)))
    summary = aggregate_accounting(rows, max_cpu_hours=max_cpu, max_gpu_hours=max_gpu)
    summary.update({"accounting_query_available": query["available"],
                    "scontrol_rows": len(control["rows"]), "discovered_jobs": len(discovered),
                    "sacct_rows": len(query["rows"]), "sacct_command_format": SACCT_FORMAT,
                    "scontrol_fallback_attempted": bool(control_ids)})
    dest.mkdir(parents=True, exist_ok=True)
    public.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    (dest / "job_discovery.json").write_text(json.dumps(discovered, indent=2, sort_keys=True))
    (dest / "sacct_query.json").write_text(json.dumps({k: v for k, v in query.items() if k != "rows"}, indent=2, sort_keys=True))
    (dest / "scontrol_query.json").write_text(json.dumps(control, indent=2, sort_keys=True))
    (dest / "resource_usage.json").write_text(json.dumps(rows, indent=2, sort_keys=True))
    _write_csv(dest / "resource_usage.csv", rows)
    (public / "resource_usage.csv").write_text("metric,value\n" + "\n".join(
        f"{key},{json.dumps(value)}" for key, value in summary.items()))
    (report / "resource_accounting.md").write_text(
        "# v2 resource accounting\n\n" + f"Status: `{summary['status']}`\n\n" +
        f"Jobs discovered: {summary['discovered_jobs']}; exact sacct rows: {summary['sacct_rows']}.\n\n" +
        "CPU and GPU totals are aggregate accounting only; unavailable fields remain unknown and are not treated as zero.\n")
    return provenance_finish(dest, public, summary)
