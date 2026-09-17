"""Fixed-source v2 report assembly; no models, fitting or new effect bootstrap.

Every source role has an explicit run. Missing values stay missing; pending or
failed families cannot be replaced by a favorable completed subset. Public
outputs contain only pre-existing aggregate quantities and logical aliases.
"""
from dataclasses import dataclass, field
import json
from pathlib import Path
import re

import numpy as np
import pandas as pd

from .provenance import ROOT, digest, object_hash, write_json, require_slurm, finish

PACKETS = ("G0", "A2", "C2_R", "C2_S", "N1", "N2", "N3", "E0_R")
SOURCES = {
    "support": ("S1_support_004", "SUPPORT"), "tests": ("tests_010", "GATES"),
    "tests_retained": ("tests_009", "GATES"), "plan": ("plan_004", "PLAN"),
    "g0_legacy": ("G0_001", "G0"), "g0_metadata": ("G0_metadata_002", "G0"),
    "g0_readouts": ("G0_readouts_001", "G0"), "a2_core": ("A2_core_001", "A2"),
    "a2_residual_failed": ("A2_residual_001", "A2"),
    "a2_residual": ("A2_residual_recovered_001", "A2"),
    "n1": ("N1_core_001", "N1"), "n2": ("N2_core_001", "N2"),
    "n3": ("N3_core_001", "N3"), "c2s": ("C2S_core_001", "C2_S"),
    "c2r": ("C2R_core_001", "C2_R"), "e0r": ("E0R_core_001", "E0_R"),
    "synthetic": ("synthetic_001", "SYNTHETIC"), "metrics": ("metrics_001", "METRICS"),
    "postflight": ("postflight_002", "AUDIT"), "resources": ("resources_002", "RESOURCES"),
    "postflight_retained": ("postflight_001", "AUDIT"),
    "fit_accounting": ("fit_accounting_001", "FIT_AUDIT"), "tests_supplement": ("tests_011", "GATES"),
}
PRIMARY_ROLE = dict(G0="g0_readouts", A2="a2_core", C2_R="c2r", C2_S="c2s", N1="n1", N2="n2", N3="n3", E0_R="e0r")
COMPLETE_EFFECT_STATUSES = {"G0_READOUTS_COMPLETE", "A2_CORE_RECORDED", "OUTPUT_FINALIZATION_REPAIRED",
    "CORE_MATRIX_RECORDED", "C2S_LINEAR_MATRIX_COMPLETE", "COMPLETE_REPAIRED_CORE",
    "MECHANISM_AUDIT_COMPLETE", "NUMERICAL_INCOMPLETE", "FIXED_PREDICTION_METRICS_COMPLETE", "PASS",
    "FIT_ACCOUNTING_COMPLETE", "FIT_ACCOUNTING_PARTIAL", "WITHIN_BUDGET", "ACCOUNTING_PARTIAL",
    "ACCOUNTING_UNAVAILABLE", "BUDGET_EXCEEDED", "UPPER_BOUND_OVER_BUDGET"}
EFFECT_COLUMNS = "packet analysis_id primary_or_secondary representation population_id overlap_definition_hash unit model_base model_augmented readout_family calibration n_candidates n_records n_trials n_bags coverage_numerator coverage_denominator estimate ci_lower ci_upper bootstrap_scope raw_effect capacity_control_margin support_status implementation_status control_status scientific_status source_run code_hash descriptive_screen notes".split()
METRIC_COLUMNS = "packet analysis_id representation population_id model readout_family calibration metric estimate ci_lower ci_upper n_candidates n_records n_trials n_bags unit aggregation bootstrap_scope source_run code_hash notes".split()
CONTROL_COLUMNS = "packet control representation population_id readout_family calibration status estimate ci_lower ci_upper n_candidates n_trials source_run notes".split()
NUMERIC_COLUMNS = "packet representation readout_family source_run scope planned_fits attempted_fits completed_fits unresolved_fits reused_fits new_fits status selected_budget extended_members code_hash notes".split()
ELIGIBILITY_COLUMNS = "packet stage representation outer_fold n_candidates n_records n_trials n_bags count_required support_status source_run overlap_definition_hash notes".split()


def number(value):
    if value is None or value == "":
        return None
    result = float(value)
    if not np.isfinite(result):
        return None
    return result


def truth(value):
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if value in ("True", "true", "1", 1):
        return True
    if value in ("False", "false", "0", 0):
        return False
    return None


def screen(estimate, lower, upper, threshold):
    """Descriptive direction only; scientific promotion has separate controls."""
    values = [number(v) for v in (estimate, lower, upper)]
    if any(v is None for v in values):
        return "NOT_EVALUABLE"
    e, lo, hi = values
    if lo > hi or not lo - 1e-10 <= e <= hi + 1e-10:
        # Percentile intervals need not contain the point estimate. Only an
        # inverted interval is a schema error; keep the other case explicit.
        if lo > hi:
            raise ValueError("REPORT_INVERTED_INTERVAL")
    if e <= 0:
        return "NEGATIVE_SCREEN"
    if lo > 0 and e < threshold:
        return "SMALL_SIGNAL"
    if lo > 0 and e >= threshold:
        return "SUPPORTED_SIGNAL"
    return "MIXED"


@dataclass
class Source:
    role: str
    run: str
    packet: str
    summary: dict = field(default_factory=dict)
    complete: bool = False
    implementation: str = "NOT_RUN"
    execution: str = "NOT_STARTED"
    code_hash: str | None = None
    job_id: str | None = None  # Private provenance only; never a public column.
    issues: list = field(default_factory=list)


class Reader:
    def __init__(self):
        self.hashes, self.public_hashes, self.errors, self.sources = {}, [], [], {}
        self.cache = {}

    def read(self, path, alias, kind="json"):
        path = Path(path)
        before = digest(path)
        if alias in self.cache:
            old_hash, old_path, value = self.cache[alias]
            if before != old_hash or str(path) != old_path:
                raise ValueError("REPORT_SOURCE_ALIAS_CHANGED")
            return value
        if kind == "json":
            value = json.loads(path.read_text())
        elif kind == "csv":
            try:
                # Literal 'null' is a synthetic mechanism, never a missing cell.
                value = pd.read_csv(path, keep_default_na=False).to_dict("records")
            except pd.errors.EmptyDataError:
                value = []
        elif kind == "jsonl":
            value = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        else:
            raise ValueError("REPORT_READER_KIND")
        if digest(path) != before:
            raise ValueError("REPORT_SOURCE_CHANGED_DURING_READ")
        self.hashes[str(path)] = before
        self.public_hashes.append(dict(logical_alias=alias, sha256=before, bytes=path.stat().st_size))
        self.cache[alias] = before, str(path), value
        return value

    def issue(self, source, code, error=None):
        source.issues.append(code)
        self.errors.append(dict(source_run=source.run, role=source.role, code=code,
            exception_class=type(error).__name__ if error else None, detail=str(error) if error else None))

    def source(self, role):
        run, packet = SOURCES[role]
        value = Source(role, run, packet)
        self.sources[role] = value
        private = ROOT / "private/auditory_next_v2" / run
        try:
            if (private / "start.json").exists():
                start = self.read(private / "start.json", role + "/start")
                value.job_id = str(start["job_id"]) if start.get("job_id") is not None else None
                value.code_hash = object_hash(start["source_hashes"]) if "source_hashes" in start else None
                value.execution = "STARTED_NO_COMPLETION"
            completion = private / "completion.json"
            if completion.exists():
                value.summary = self.read(completion, role + "/completion")
                value.complete = True
                value.execution = str(value.summary.get("status", "UNKNOWN_COMPLETION_STATUS"))
                value.code_hash = value.summary.get("source_snapshot_hash", value.code_hash)
                published = ROOT / "results/auditory_next_v2" / run / "summary.json"
                if published.exists():
                    if object_hash(self.read(published, role + "/summary")) != object_hash(value.summary):
                        raise ValueError("REPORT_PRIVATE_PUBLIC_COMPLETION_CONFLICT")
                s = value.execution
                if s in ("IMPLEMENTATION_FAIL", "INPUT_INTEGRITY_FAILURE", "PERMISSION_ANOMALIES"):
                    value.implementation = "BUG"
                elif s in ("NUMERICAL_INCOMPLETE", "INCOMPLETE_PRIMARY_MATRIX", "OPTIMIZATION_UNRESOLVED"):
                    value.implementation = "NUMERICAL_FAILURE"
                elif s in ("BUDGET_LIMITED", "TIMEOUT"):
                    value.implementation = "BUDGET_LIMITED"
                else:
                    value.implementation = "PASS"
            failure = private / "failure.json"
            if failure.exists():
                failed = self.read(failure, role + "/failure")
                trace = failed.get("traceback", "")
                self.issue(value, "RETAINED_FAILURE", trace)
                if not value.complete:
                    value.execution = "FAILED"
                    value.implementation = "NUMERICAL_FAILURE" if any(word in trace for word in (
                        "OPTIMIZATION", "ConvergenceWarning", "nonfinite", "NONFINITE", "NUMERICAL")) else "BUG"
            return value
        except (OSError, ValueError, KeyError, TypeError) as error:
            self.issue(value, "SOURCE_RECEIPT_SCHEMA_FAILURE", error)
            value.complete, value.implementation = False, "BUG"
            return value

    def table(self, role, name, *, required=False, kind="csv", completed=True, private=False):
        source = self.sources[role]
        if completed and (not source.complete or source.execution not in COMPLETE_EFFECT_STATUSES):
            return [] if kind == "csv" else None
        path = ROOT / ("private" if private else "results") / "auditory_next_v2" / source.run / name
        if not path.exists():
            if required:
                self.issue(source, "MISSING_REQUIRED_AGGREGATE:" + name)
                source.implementation = "BUG" if source.complete else source.implementation
            return [] if kind == "csv" else None
        try:
            return self.read(path, role + "/" + name, kind)
        except (OSError, ValueError, KeyError, TypeError) as error:
            self.issue(source, "AGGREGATE_SCHEMA_FAILURE:" + name, error)
            source.implementation = "BUG"
            return [] if kind == "csv" else None


def base_effect(reader, role, analysis, row, *, representation=None, family=None,
                population=None, unit="bits/trial", primary=False, model_base=None, model_augmented=None, notes=""):
    source = reader.sources[role]
    return dict(packet=source.packet, analysis_id=analysis, primary_or_secondary="primary" if primary else "secondary",
        representation=representation or row.get("mode", row.get("representation")),
        population_id=population or row.get("population"), overlap_definition_hash=source.summary.get("overlap_definition_hash"),
        unit=unit, model_base=model_base or row.get("first"), model_augmented=model_augmented or row.get("second"),
        readout_family=family or row.get("family"), calibration=row.get("calibration", row.get("probability_mode")),
        n_candidates=number(row.get("n_candidates")), n_records=number(row.get("n_records")),
        n_trials=number(row.get("n_trials")), n_bags=number(row.get("n_bags")),
        coverage_numerator=number(row.get("coverage_numerator")), coverage_denominator=number(row.get("coverage_denominator")),
        estimate=number(row.get("estimate")), ci_lower=number(row.get("ci_lower")), ci_upper=number(row.get("ci_upper")),
        bootstrap_scope=row.get("bootstrap_scope", row.get("ci_scope", row.get("uncertainty", "fixed OOF; no pipeline refits"))),
        raw_effect=None, capacity_control_margin=None, source_run=source.run, code_hash=source.code_hash,
        notes=notes or "未由源聚合提供的记录/试次/覆盖计数保留空值；不从trial推算人数。")


def collect_effects(reader):
    rows = []
    for r in reader.table("a2_core", "repeatability_aggregate.csv", required=True):
        if r.get("status") != "COMPUTED":
            continue
        primary = r.get("mode") == "R_SIM" and r.get("endpoint") == "post_delta" and r.get("metric") == "cosine"
        rows.append(base_effect(reader, "a2_core", r["endpoint"] + "_" + r["metric"], r,
            unit="cosine_difference" if r["metric"] == "cosine" else "projected_inner_product",
            family="matching", population="common_Omega_equal_candidate", primary=primary,
            model_base="different_identity", model_augmented="matched_identity"))
    for r in reader.table("a2_residual", "residual_aggregate.csv", required=True):
        if str(r.get("outer_fold")) != "ALL":
            continue
        rows.append(base_effect(reader, "a2_residual", "residual_audit_" + r["quantity"] + "_" + r["metric"], r,
            unit="cosine_difference" if r["metric"] == "cosine" else "projected_inner_product",
            family="fixed_background_ridge_audit", population="common_Omega_equal_candidate", notes="仅诊断；恢复输出复用原20次ridge，没有新拟合。"))
    for role in ("n1", "n3"):
        for r in reader.table(role, "paired_effects.csv", required=True):
            primary = role == "n1" and (r.get("mode"), r.get("population"), r.get("family"), r.get("calibration"), r.get("first"), r.get("second")) == (
                "R_SIM", "P_nat", "mlp32", "temperature", "HP", "HPB")
            rows.append(base_effect(reader, role, r["first"] + "_minus_" + r["second"], r, primary=primary))
    for r in reader.table("n3", "selected_family_effects.csv", required=True):
        primary = (r.get("mode"), r.get("population"), r.get("calibration"), r.get("first"), r.get("second")) == (
            "R_SIM", "P_nat", "temperature", "H", "HP")
        rows.append(base_effect(reader, "n3", "selected_" + r["first"] + "_minus_" + r["second"], r,
            family="training_OOF_selected", primary=primary))
    for r in reader.table("n2", "paired_gains.csv", required=True):
        if str(r.get("outer_fold")) != "ALL":
            continue
        primary = (r.get("mode"), r.get("window"), r.get("family"), r.get("calibration"), r.get("effect")) == (
            "R_SIM", "post", "logistic", "temperature", "gain_mu_var")
        rows.append(base_effect(reader, "n2", r["window"] + "_" + r["effect"], r,
            population="P_bal", unit="bits/bag", primary=primary))
    for r in reader.table("c2s", "spatial_gains.csv", required=True):
        name = r["statistic"]
        if name.startswith("CE_"):
            continue
        pairs = dict(G_crossmean=("S0", "S1"), G_midline=("S1", "S2"),
            crossmean_matched_width_margin=("S0_DUP_S1", "S1"), complete_spatial_matched_width_margin=("S0_DUP_S2", "S2"),
            S0_minus_FULL20=("S0", "FULL20"), S2_minus_FULL20=("S2", "FULL20"))
        first, second = pairs[name]
        rows.append(base_effect(reader, "c2s", name, r, representation="L0", population="P_bal", family="logistic",
            primary=name in ("G_crossmean", "G_midline") and r.get("calibration") == "calibrated", model_base=first, model_augmented=second))
    for r in reader.table("c2r", "single_joint_gains.csv", required=True):
        name = r["statistic"]
        if name.startswith("CE_"):
            continue
        rows.append(base_effect(reader, "c2r", name, r, population="P_bal",
            primary=(r.get("representation"), r.get("family"), r.get("probability_mode"), name) == ("R_SIM", "mlp32", "calibrated", "T_C"),
            model_base="min(L,R)" if name == "T_C" else None, model_augmented="LR"))
    for r in reader.table("e0r", "e0_aggregate.json", required=True, kind="json") or []:
        interval = r["J_bits_interval"]
        rows.append(base_effect(reader, "e0r", r["task"] + "_J", dict(r, **interval,
            n_candidates=interval.get("n_candidates", interval.get("n_clusters")), n_records=r["complete_pairs"]), representation="native128",
            population="within_record_class_balanced_paired_records", primary=r["family"] == "MLP32" and r["calibration"] == "calibrated",
            model_base="binary_prior", model_augmented="target_task_readout", notes="完整任务对的记录内可读性；不是E1、跨儿童迁移或全CI群体结论。"))
    keys = [(r["packet"], r["analysis_id"], r["representation"], r["population_id"], r["readout_family"], r["calibration"]) for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("REPORT_DUPLICATE_EXPLICIT_EFFECT_SOURCE")
    for r in rows:
        if r["ci_lower"] is not None and r["ci_upper"] is not None and r["ci_lower"] > r["ci_upper"]:
            raise ValueError("REPORT_INVERTED_EFFECT_INTERVAL")
        raw = [v for v in rows if all(v[k] == r[k] for k in ("packet", "analysis_id", "representation", "population_id", "readout_family")) and v["calibration"] == "raw"]
        r["raw_effect"] = raw[0]["estimate"] if len(raw) == 1 else None
    return rows


class OneRole:
    """A corrupt aggregate blocks its source, while other named sources survive."""
    def __init__(self, reader, role):
        self.reader, self.role, self.sources = reader, role, reader.sources

    def table(self, role, name, **kwargs):
        if role != self.role:
            return [] if kwargs.get("kind", "csv") == "csv" else None
        return self.reader.table(role, name, **kwargs)


def isolated_effects(reader):
    result = []
    for role in ("a2_core", "a2_residual", "n1", "n2", "n3", "c2s", "c2r", "e0r"):
        try:
            result.extend(collect_effects(OneRole(reader, role)))
        except (KeyError, TypeError, ValueError) as error:
            reader.issue(reader.sources[role], "EFFECT_ADAPTER_FAILURE", error)
            reader.sources[role].implementation = "BUG"
    return result


def balanced_prior_information(row):
    """Exact J=1-CE algebra only for the balanced binary target population."""
    if row.get("population_id") != "P_bal" or row.get("metric") != "ce_bits":
        return None
    estimate = number(row.get("estimate"))
    if estimate is None:
        return None
    lower, upper = number(row.get("ci_lower")), number(row.get("ci_upper"))
    if lower is not None and upper is not None and lower > upper:
        raise ValueError("REPORT_INVERTED_METRIC_INTERVAL")
    return dict(row, metric="J_bits", estimate=1 - estimate,
        ci_lower=None if upper is None else 1 - upper, ci_upper=None if lower is None else 1 - lower,
        unit="bits/bag" if row.get("packet") == "N2" else "bits/trial",
        notes=str(row.get("notes", "")) + " P_bal二分类先验CE=1，J及区间仅精确代数变换；无新bootstrap/fit。")


def collect_metrics(reader):
    result = []
    def add(role, analysis, row, metric, value, *, lower=None, upper=None, unit=None, model=None, family=None,
            representation=None, population=None, calibration=None, n_candidates=None, n_records=None, notes=""):
        s = reader.sources[role]
        result.append(dict(packet=s.packet, analysis_id=analysis, representation=representation or row.get("mode"),
            population_id=population or row.get("population"), model=model or row.get("view"),
            readout_family=family or row.get("family"), calibration=calibration or row.get("calibration", row.get("probability")),
            metric=metric, estimate=number(value), ci_lower=number(lower), ci_upper=number(upper),
            n_candidates=number(n_candidates if n_candidates is not None else row.get("n_candidates")),
            n_records=number(n_records if n_records is not None else row.get("n_records")),
            n_trials=number(row.get("n_trials", row.get("trials"))), n_bags=number(row.get("n_bags")),
            unit=unit or ("bits" if metric in ("ce_bits", "J_bits") else "unitless"),
            aggregation=row.get("aggregation", "source aggregate; no new pooling"),
            bootstrap_scope=row.get("bootstrap_scope", "source fixed predictions; no refit"),
            source_run=s.run, code_hash=s.code_hash, notes=notes))
    enriched = reader.table("metrics", "metrics_enriched.csv", required=True)
    packet_alias = dict(G0_within="G0", G0_bridge="G0", N1="N1", N2="N2", N3="N3", N3_selected="N3")
    for r in enriched:
        packet = packet_alias[r["packet"]]
        add("metrics", r["packet"] + "_" + r.get("window", "") + "_" + r.get("bank", ""), r,
            r["metric"], r["estimate"], lower=r.get("ci_lower"), upper=r.get("ci_upper"),
            notes="补充表从固定外预测计算；保留原packet与source_run，未重拟合。")
        result[-1]["packet"] = packet
        result[-1]["source_run"] = r["source_run"]
        original = [s for s in reader.sources.values() if s.run == r["source_run"]]
        if len(original) != 1:
            raise ValueError("REPORT_ENRICHED_SOURCE_NOT_DECLARED")
        result[-1]["code_hash"] = original[0].code_hash
        result[-1]["notes"] += " 补充派生来源=" + reader.sources["metrics"].run
        result[-1]["n_bags" if packet == "N2" else "n_trials"] = number(r.get("n_observations"))
        if packet == "N3" and r["packet"] == "N3_selected":
            result[-1]["readout_family"] = "training_OOF_selected"
        if r["metric"] == "ce_bits":
            result[-1]["unit"] = "bits/bag" if packet == "N2" else "bits/trial"
        information = balanced_prior_information(result[-1])
        if information is not None:
            result.append(information)
    enriched_packets = {r["packet"] for r in enriched}
    for role, name, tag, selector in (("g0_readouts", "g0_within_child_metrics.csv", "within_child", "mode"),
            ("g0_readouts", "g0_bridge_metrics.csv", "offline_bridge", "bank")):
        for r in reader.table(role, name, required=True):
            if str(r.get("outer_fold")) != "ALL" or ("G0_within" if tag == "within_child" else "G0_bridge") in enriched_packets:
                continue
            for metric, lo, hi in (("ce_bits", "ce_ci_lower", "ce_ci_upper"), ("bacc", "bacc_ci_lower", "bacc_ci_upper")):
                add(role, tag, r, metric, r.get(metric), lower=r.get(lo), upper=r.get(hi),
                    representation=r.get(selector), population="P_bal", family="logistic",
                    n_records=r.get("n_records", r.get("n_clusters")),
                    notes="源诊断以记录为cluster；未报告的候选人数为空，不以cluster/trial替代儿童计数。")
    for r in reader.table("g0_legacy", "shared_metrics_reproduction.csv", required=True):
        for metric in ("ce_bits", "J_bits", "bacc", "auroc", "brier"):
            add("g0_legacy", "legacy_refit_probe_" + r["branch"] + "_" + r["window"], r, metric, r.get(metric),
                population="P_bal", family="legacy_logistic_probe", n_candidates=r.get("candidates"),
                notes="旧共享表复算；这是冻结表征后的logistic probe，不是原监督CNN head。")
    for r in reader.table("g0_legacy", "supervised_original_head.csv", required=True):
        for metric in ("ce_bits_stable", "bacc", "auroc", "brier"):
            add("g0_legacy", "original_head_" + r["role"] + "_fold" + str(r["outer_fold"]), r, metric, r.get(metric),
                family="original_supervised_head", population="P_bal", calibration="raw", n_candidates=r.get("candidates"),
                notes="训练组分数仅优化诊断；与OUTER_SHARED及重新拟合probe分列，不进行跨训练折平均。")
    for r in reader.table("c2s", "classification_metrics.csv", required=True):
        for metric in ("ce_bits", "J_bits", "bacc", "auroc", "brier"):
            add("c2s", "six_view_spatial", r, metric, r.get(metric), representation="L0", population="P_bal", family="logistic")
    geometry = reader.table("c2s", "geometry_aggregate.json", kind="json") or {}
    for key in ("max_reconstruction_error", "max_full_epoch_reconstruction_error", "max_19dim_reconstruction_error"):
        if key in geometry:
            add("c2s", "exact_spatial_reconstruction", {}, key, geometry[key], unit="microvolt absolute error",
                representation="L0", family="algebra", n_records=geometry.get("records"))
    for r in reader.table("c2r", "single_joint_gains.csv", required=True):
        if r["statistic"].startswith("CE_"):
            add("c2r", "complete_repaired_readout_matrix", r, "ce_bits", r["estimate"], lower=r.get("ci_lower"), upper=r.get("ci_upper"),
                model=r["statistic"][3:], representation=r["representation"], calibration=r["probability_mode"], population="P_bal")
    for r in reader.table("e0r", "e0_aggregate.json", required=True, kind="json") or []:
        j = r["J_bits_interval"]
        add("e0r", r["task"], r, "J_bits", j["estimate"], lower=j["ci_lower"], upper=j["ci_upper"],
            representation="native128", population="within_record_class_balanced_paired_records", n_records=r["complete_pairs"],
            n_candidates=j.get("n_candidates", j.get("n_clusters")), notes="完整配对记录，未提供trial数/其他指标则留空；E1关闭。")
        add("e0r", r["task"], r, "ce_bits", r["mean_CE_bits"], lower=1-j["ci_upper"], upper=1-j["ci_lower"],
            representation="native128", population="within_record_class_balanced_paired_records", n_records=r["complete_pairs"],
            n_candidates=j.get("n_candidates", j.get("n_clusters")), notes="CE区间由同一J=1-CE区间作精确代数变换，无新bootstrap。")
    return result


def collect_eligibility(reader):
    result = []
    s = reader.sources["support"]
    if s.complete:
        for packet in ("A2", "N1", "N3"):
            r = s.summary.get(packet, {})
            result.append(dict(packet=packet, stage="frozen_metadata", n_candidates=r.get("candidates", r.get("test_candidates")),
                count_required=25 if packet == "A2" else 20, support_status=r.get("status"), source_run=s.run,
                notes="历史在QC前构造；元数据/标签支持选择已先于新EEG效应冻结。"))
        for r in s.summary.get("N2", []):
            result.append(dict(packet="N2", stage="k=" + str(r.get("k")), n_candidates=r.get("candidates"),
                n_bags=r.get("bags"), n_trials=r.get("trials_used"), support_status=r.get("status"), count_required=20, source_run=s.run))
        r = s.summary.get("N2_common_4_8_16", {})
        result.append(dict(packet="N2", stage="common_k4_8_16_support_only", n_candidates=r.get("candidates"),
            support_status=r.get("status"), source_run=s.run, notes="只计共同支持，不表示已拟合各k曲线。"))
    for role, packet in (("g0_metadata", "G0"), ("a2_core", "A2"), ("c2s", "C2_S"), ("c2r", "C2_R"), ("e0r", "E0_R")):
        source = reader.sources[role]
        if not source.complete:
            continue
        r = source.summary
        if packet == "G0":
            result.append(dict(packet=packet, stage="refined_temporal_support", n_candidates=r.get("temporal_supported_groups"),
                n_records=r.get("temporal_supported_records"), source_run=source.run,
                notes="替代G0_001临时时间角色和桥接支持规则；旧指标复现仍保留。"))
        elif packet == "C2_S":
            support = r.get("support", {})
            result.append(dict(packet=packet, stage="same_P1_P2_trial_pool", n_candidates=support.get("candidates"),
                n_trials=support.get("trials"), count_required=20, support_status=support.get("status"), source_run=source.run,
                notes="whole-record QC决定共同入选，selection_isolation=False。"))
            for fold in support.get("outer_counts", []):
                result.append(dict(packet=packet, stage="outer_support", outer_fold=fold.get("outer_fold"),
                    n_candidates=fold.get("test", fold.get("test_candidates")), source_run=source.run,
                    notes="训练人数=" + str(fold.get("train", fold.get("train_candidates")))))
        elif packet == "E0_R":
            audit = getattr(reader, 'e0_support', {})
            for key in ("records_requested", "records_with_block_support"):
                result.append(dict(packet=packet, stage=key, n_records=audit.get(key, r.get(key)), source_run=source.run,
                    notes="混合MFF来源，原native128；不把record数当儿童数。"))
            if audit:
                for key in ('legacy_linear_records_complete', 'legacy_linear_complete_pairs',
                        'mlp_records_all_required_heads_stable', 'mlp_records_available_for_primary_aggregation'):
                    result.append(dict(packet=packet, stage=key, n_records=audit[key], support_status='DESCRIPTIVE_ONLY',
                        source_run=audit['legacy_linear_source_run'] if key.startswith('legacy_') else source.run,
                        notes='完整配对计数为每任务记录数；神经记录全部头稳定与整族主聚合许可分开，0聚合许可不等于0信号。'))
                continue
            for family in ('linear', 'MLP32'):
                complete = r.get('family_status', {}).get(family) in ('COMPLETE_REUSED', 'COMPLETE_REPAIRED')
                result.append(dict(packet=packet, stage=family + '_records_complete_for_aggregation',
                    n_records=r.get('records_with_block_support') if complete else None,
                    support_status='DESCRIPTIVE_ONLY', source_run=source.run,
                    notes='全族完成记录数；最终任务效应另限完整配对，不把未提供数值记0。'))
        else:
            result.append(dict(packet=packet, stage="main_frozen_cohort", n_candidates=r.get("candidates"),
                overlap_definition_hash=r.get("overlap_definition_hash"), source_run=source.run,
                support_status=r.get("support_status"), notes="全模型共同队列；不合并不同encoder坐标。"))
    return result


SYNTHETIC_MECHANISMS = {
    "G0": ("null", "injected"), "A2": ("null", "predictable_nuisance", "individual_stimulus"),
    "N1": ("PRIOR_ONLY", "BACKGROUND_KEY", "ADDITIVE_NOISE", "INDEPENDENT_BACKGROUND"),
    "N2": ("MEAN_SUFFICIENT", "COVARIANCE_SIGNAL", "TIME_DRIFT"),
    "N3": ("HISTORY_ONLY", "EEG_INCREMENT", "NEAR_DETERMINISTIC_HISTORY"),
}
SYNTHETIC_FAMILIES = {"G0": ("logistic",), "N1": ("mlp32",), "N2": ("logistic",),
    "N3": ("logistic", "mlp32"),
    "A2": tuple(condition + "__" + component for condition in ("zero", "fixed", "fitted") for component in ("delta", "residual"))}
SYNTHETIC_EXPECTATIONS = {
    "G0": "null不应稳定优于先验；injected应出现可检测的先验减读出CE，固定单世界门槛0.01 bits/trial。",
    "A2": "null下固定非零W可制造残差重复性；W=0/固定W/训练拟合W共享draw。真实nuisance可重复但不是刺激特异信息；个体刺激世界应有未校正差异。单世界T门槛0.05，另核对四项恒等式。",
    "N1": "BACKGROUND_KEY/ADDITIVE_NOISE预期背景辅助；PRIOR_ONLY/INDEPENDENT_BACKGROUND不应稳定制造增量。单世界主增量>=0.005且CI下界>0，noise margin下界>0；合成预算未覆盖真实HB/HPP/donor全控制。",
    "N2": "COVARIANCE_SIGNAL应有分布增量；MEAN_SUFFICIENT/TIME_DRIFT不能冒充均值或时间之外的分布增量。单世界主增量>=0.01且CI下界>0，duplicate margin下界>0；RFF只次要诊断。",
    "N3": "EEG_INCREMENT预期正增量；HISTORY_ONLY/NEAR_DETERMINISTIC_HISTORY不能稳定产生额外EEG收益。每族单世界主增量>=0.005且CI下界>0，noise margin下界>0；两族共享draw。",
}


def synthetic_control_audit(rows, packet):
    """Coverage is an execution result, not a recovery/FPR acceptance rule.

    The frozen protocol supplies per-world direction/control screens but no
    across-world minimum recovery rate or maximum false-positive rate. Do not
    invent one after observing the rates. Therefore automatic scientific
    promotion remains blocked; the separate interpretation document explains
    mechanisms without inventing a rate gate, even when every world ran.
    """
    own = [r for r in rows if r.get("packet") == packet]
    expected = {(m, f) for m in SYNTHETIC_MECHANISMS[packet] for f in SYNTHETIC_FAMILIES[packet]}
    keys = [(r.get("mechanism"), r.get("family")) for r in own]
    count = 100 if packet == "A2" else 30
    coverage = bool(own) and len(keys) == len(expected) and set(keys) == expected and all(
        number(r.get("n_planned")) == count and number(r.get("n_evaluable")) == count and
        number(r.get("n_unknown")) == 0 for r in own)
    return dict(execution_status="COMPLETE" if coverage else "FAILED" if own else "MISSING",
        interpretation_status="DIRECTION_INTERPRETATION_SEPARATE_NO_RATE_GATE" if coverage else "NUMERICALLY_UNRESOLVED_WORLD_COVERAGE" if own else "NOT_EVALUABLE",
        scientific_control_status="MISSING", automatic_scientific_support=False,
        expected_behavior=SYNTHETIC_EXPECTATIONS[packet],
        rate_acceptance_threshold=None,
        notes="完整分母只证明执行完整；保留所有恢复率/FPR倾向及Monte Carlo区间。方案未冻结跨世界通过率阈值，不事后添加，也不以完成代替机制识别。")


def history_stratum_support_audit(rows, descriptions):
    """Validate zero-refit support metadata without imposing a new quota."""
    key_fields = ("mode", "population", "previous_run_bin")
    count_fields = ("class0_trials", "class1_trials", "n_candidates", "n_candidates_both_classes", "n_trials")
    def key(row):
        return tuple(str(row.get(k, "")) for k in key_fields)
    required = {key(row) for row in descriptions}
    if not rows or not required or not required.issubset({key(row) for row in rows}):
        return dict(status="MISSING", notes="新增支持表尚未覆盖旧固定头分层描述的全部mode/population/run-bin。")
    if len({key(row) for row in rows}) != len(rows):
        return dict(status="FAILED", notes="支持表存在重复分层键，不能合并或挑选。")
    zeros, partial = 0, 0
    for row in rows:
        counts = [number(row.get(k)) for k in count_fields]
        if any(v is None or v < 0 or v != int(v) for v in counts):
            return dict(status="FAILED", notes="两类/候选/试次支持计数缺失或非非负整数。")
        n0, n1, n, both, trials = counts
        if n0 + n1 != trials or both > n or n > trials or both > min(n0, n1):
            return dict(status="FAILED", notes="两类计数、候选数与总试次数不一致。")
        zeros += n0 == 0 or n1 == 0
        partial += both < n
    return dict(status="COMPLETE", notes=f"支持计数已核对；{zeros}个层存在全层单类/空格，{partial}个层不是每候选都有两类。只描述稀疏支持，不新增排除或配额。")


def family_selection_summary(rows):
    """Count saved OOF selections; never select a family again from test risk."""
    if not rows:
        return []
    expected = {(m, p, v, f) for m in ('R_SIM', 'L0') for p in ('P_nat', 'P_bal')
                for v in ('H', 'HP', 'HB', 'HBP', 'Hnoise') for f in range(5)}
    keys = [(r['mode'], r['population'], r['view'], r['outer_fold']) for r in rows]
    if len(keys) != len(set(keys)) or set(keys) != expected:
        raise ValueError('N3_SELECTION_FROZEN_FOLD_COVERAGE')
    counts = {}
    for row in rows:
        if row['family'] not in ('logistic', 'mlp32') or (row['mode'] == 'L0' and row['family'] != 'logistic'):
            raise ValueError('N3_SELECTION_UNDECLARED_FAMILY')
        key = (row['mode'], row['population'], row['view'], row['family'])
        counts[key] = counts.get(key, 0) + 1
    return [dict(zip(('mode', 'population', 'view', 'family'), key), n_outer_folds=value,
        selector='saved inner OOF raw CE; no new selection') for key, value in sorted(counts.items())]


def read_family_selection(reader):
    try:
        return family_selection_summary(reader.table('n3', 'training_family_selection.json', kind='json') or [])
    except (ValueError, TypeError, KeyError) as error:
        source = reader.sources['n3']
        code = 'AGGREGATE_SCHEMA_FAILURE:training_family_selection.json'
        if code not in source.issues:
            reader.issue(source, code, error)
        source.implementation = 'BUG'
        return []


def resource_state_for_source(source, rows):
    """Use the exact start-receipt job, not run names or reservation elapsed.

    resources_001/resource_usage.json has job_id, state, accounting_source and
    active_reservation. Only measured sacct/scontrol states establish a hard
    terminal state; requested_fallback/UNAVAILABLE is not such evidence.
    Completed run receipts survive a later failure of a shared multi-run job.
    """
    result = dict(execution=source.execution, implementation=source.implementation, evidence="NO_CONFIRMED_JOB_STATE")
    if source.complete:
        return dict(result, evidence="RUN_RECEIPT_ALREADY_COMPLETE")
    job = str(source.job_id or "").strip()
    if not re.fullmatch(r"[0-9]+(?:_[0-9]+)?", job):
        return dict(result, evidence="START_JOB_ID_UNAVAILABLE")
    matching = [r for r in rows if str(r.get("job_id", "")).strip() == job]
    measured = [r for r in matching if r.get("accounting_source") in ("sacct", "scontrol")]
    if not measured:
        return result
    states = {str(r.get("state") or "").strip().upper().split(" ", 1)[0].rstrip("+") for r in measured}
    if len(states) != 1:
        return dict(result, evidence="CONFLICTING_EXACT_JOB_STATES")
    state = states.pop()
    active_states = {"PENDING", "RUNNING", "CONFIGURING", "COMPLETING", "RESIZING", "SUSPENDED", "REQUEUED"}
    if state in active_states:
        return dict(result, execution=state, evidence="EXACT_JOB_ACTIVE")
    if state not in TERMINAL_BLOCKED and state != "COMPLETED":
        return result
    if any(truth(r.get("active_reservation")) is True for r in measured):
        return dict(result, evidence="TERMINAL_STATE_ACTIVE_RESERVATION_CONFLICT")
    if state in ("TIMEOUT", "OUT_OF_MEMORY"):
        return dict(execution=state, implementation="BUDGET_LIMITED", evidence="EXACT_JOB_TERMINAL")
    if state == "COMPLETED":
        return dict(execution="JOB_COMPLETED_WITHOUT_RUN_COMPLETION", implementation="BUG",
            evidence="EXACT_JOB_FINISHED_BUT_REQUIRED_RUN_RECEIPT_MISSING")
    return dict(result, execution=state, evidence="EXACT_JOB_TERMINAL")


def collect_controls(reader, effects):
    controls = []
    def add(packet, control, status, role, row=None, notes=""):
        r = row or {}
        controls.append(dict(packet=packet, control=control, status=status, source_run=reader.sources[role].run,
            representation=r.get("mode", r.get("representation")), population_id=r.get("population", r.get("population_id")),
            readout_family=r.get("family", r.get("readout_family")), calibration=r.get("calibration", r.get("probability_mode")),
            estimate=number(r.get("estimate")), ci_lower=number(r.get("ci_lower")),
            ci_upper=number(r.get("ci_upper")), n_candidates=number(r.get("n_candidates")), n_trials=number(r.get("n_trials")), notes=notes))
    def complete(role):
        s = reader.sources[role]
        return s.complete and s.implementation == "PASS"
    for packet in PACKETS:
        add(packet, "frozen_implementation_contracts", "COMPLETE" if complete("tests") else "MISSING", "tests",
            notes="主real-head gate固定tests_010；tests_011只补充实现验收，不改已拟合源。")
        p = reader.sources["postflight"]
        add(packet, "legacy_integrity_and_private_permissions", "COMPLETE" if complete("postflight") and
            p.summary.get("legacy_changed") == 0 and p.summary.get("legacy_missing") == 0 and p.summary.get("permission_anomalies") == 0 else
            "FAILED" if p.complete else "MISSING", "postflight")
        if packet != "G0":
            primary = [r for r in effects if r["packet"] == packet and r["primary_or_secondary"] == "primary"]
            expected = 2 if packet in ("C2_S", "E0_R") else 1
            add(packet, "complete_prespecified_primary_aggregates", "COMPLETE" if len(primary) == expected and all(
                r[k] is not None for r in primary for k in ("estimate", "ci_lower", "ci_upper")) else "MISSING", PRIMARY_ROLE[packet])
    synthetic = reader.table("synthetic", "synthetic_rates.csv", required=True)
    for packet in ("G0", "A2", "N1", "N2", "N3"):
        audit = synthetic_control_audit(synthetic, packet)
        add(packet, "prespecified_synthetic_execution_coverage", audit["execution_status"], "synthetic", notes=audit["notes"])
        add(packet, "prespecified_synthetic_direction_and_controls", audit["scientific_control_status"], "synthetic",
            notes=audit["interpretation_status"] + "; " + audit["expected_behavior"] + " " + audit["notes"])
    for name, role in (("legacy_shared_table_reproduction", "g0_legacy"), ("refined_dependency_and_common_QC_mapping", "g0_metadata"),
                       ("within_child_and_offline_bridge", "g0_readouts")):
        add("G0", name, "COMPLETE" if complete(role) else "MISSING", role)
    selection = read_family_selection(reader)
    add('N3', 'saved_training_OOF_family_selection', 'COMPLETE' if selection else 'MISSING', 'n3',
        notes='逐视图保存的选族覆盖全部五个外折；选族不同的比较不自动构成嵌套容量比较。')
    for analysis in ("post_delta_cosine", "pre_delta_cosine", "post_minus_pre_cosine", "common_response_cosine"):
        own = [r for r in effects if r["packet"] == "A2" and r["analysis_id"] == analysis and r["representation"] == "R_SIM"]
        add("A2", analysis, "COMPLETE" if len(own) == 1 and own[0]["estimate"] is not None else "MISSING", "a2_core",
            own[0] if own else None, notes="控制是否已执行与控制效应方向分开；post-pre是统计量之差。")
    add("A2", "saved_residual_four_term_audit", "COMPLETE" if complete("a2_residual") else "MISSING", "a2_residual",
        notes="原output-only失败保留；恢复只重建聚合，没有新的ridge/PCA/scaler拟合。")
    quality = reader.sources["a2_residual"].summary.get("quality_status", [])
    add("A2", "fixed_quality_summary_in_background", "MISSING" if not quality or "FEATURE_TASK_HAS_NO_FIXED_QUALITY_ARRAY" in quality else "COMPLETE",
        "a2_residual", notes="已有固定feature任务没有quality数组时保留限制，不能称已完成质量背景控制。")
    for role in ("n1", "n3"):
        family_rows = reader.table(role, "numerical_status.csv", required=True)
        if family_rows and any(truth(r.get("complete")) is not True for r in family_rows):
            reader.sources[role].implementation = "NUMERICAL_FAILURE"
        add(reader.sources[role].packet, "complete_required_head_families", "COMPLETE" if family_rows and
            all(truth(r.get("complete")) is True for r in family_rows) else "FAILED" if family_rows else "MISSING", role)
        coverage = reader.table(role, "calibration_coverage.json", kind="json") or []
        add(reader.sources[role].packet, "declared_inner_OOF_calibration", "COMPLETE" if coverage and all(
            r.get("status") == "PARTIAL_COVERAGE_ENCODER_ISOLATED_INNER_OOF" for r in coverage) else "MISSING", role,
            notes="仅已声明encoder-unseen内折子集；这是部分覆盖，未覆盖训练组不假装拥有OOF。")
    donors = reader.table("n1", "donor_controls.csv")
    fixed = [r for r in donors if r.get("control") == "fixed_head_donor"]
    matched = [r for r in donors if r.get("control") == "matched_training_donor_vs_same_support_reference"]
    add("N1", "two_fixed_head_donor_assignments", "COMPLETE" if len(fixed) == 2 else "MISSING", "n1",
        notes="禁止按当前标签匹配；仅冻结donor共同集合，分布失配诊断不等于因果必要性。")
    add("N1", "matched_donor_training_same_support_reference", "COMPLETE" if len(matched) == 1 else "MISSING", "n1")
    for r in donors:
        add("N1", r["control"] + ":" + r["first"] + "-" + r["second"], "COMPLETE", "n1", r, notes="OOD/输入构造诊断；不替换主试次池。")
    for packet, ids, role in (("N1", ("HPP_minus_HPB", "HPBnoise_minus_HPB", "HB_minus_HPB"), "n1"),
                             ("N3", ("selected_HB_minus_HBP", "selected_H_minus_Hnoise"), "n3")):
        for name in ids:
            own = [r for r in effects if r["packet"] == packet and r["analysis_id"] == name and r["representation"] == "R_SIM" and
                r["population_id"] == "P_nat" and r["calibration"] == "temperature" and
                r["readout_family"] == ("mlp32" if packet == "N1" else "training_OOF_selected")]
            add(packet, name, "COMPLETE" if len(own) == 1 else "MISSING", role, own[0] if own else None)
    strata = reader.table("n3", "history_run_strata.csv")
    add("N3", "fixed_history_strata_description", "COMPLETE" if strata else "MISSING", "n3",
        notes="同一冻结头按过去run分层；不逐层重新选最优模型。")
    support = reader.table("metrics", "history_stratum_support.csv")
    stratum_audit = history_stratum_support_audit(support, strata)
    add("N3", "stratum_two_class_support_counts", stratum_audit["status"], "metrics", notes=stratum_audit["notes"])
    n2 = reader.sources["n2"]
    if n2.complete and n2.summary.get("completed_fits") != n2.summary.get("readout_fits"):
        n2.implementation = "NUMERICAL_FAILURE"
    for name in ("post_mv_vs_dup", "pre_gain_mu_var", "post_minus_pre_gain_mu_var_post_minus_pre"):
        own = [r for r in effects if r["packet"] == "N2" and r["analysis_id"] == name and r["representation"] == "R_SIM" and
               r["readout_family"] == "logistic" and r["calibration"] == "temperature"]
        add("N2", name, "COMPLETE" if len(own) == 1 else "MISSING", "n2", own[0] if own else None,
            notes="同bag的pre/post窗口长度不同；差异不是纯因果响应。")
    sensitivity = reader.table("n2", "test_sensitivity_averaged_effects.csv")
    add("N2", "ten_frozen_test_regroupings", "COMPLETE" if n2.summary.get("test_sensitivity", {}).get("status") == "SENSITIVITY_RECORDED" and sensitivity else "MISSING",
        "n2", notes="只重组测试袋，平均后再做原固定预测统计；没有新模型拟合。")
    for r in sensitivity:
        add("N2", "regrouping_average_" + str(r.get("window", "")) + "_" + str(r.get("effect", "")), "COMPLETE", "n2", r)
    geometry = reader.table("c2s", "geometry_aggregate.json", kind="json") or {}
    add("C2_S", "full_twenty_channel_reconstruction_and_numeric_isolation", "COMPLETE" if geometry.get("status") == "PASS" else "MISSING", "c2s",
        notes="19个有效自由度；右侧原始数值扰动不改左局部；whole-record QC仍使selection_isolation=False。")
    for name in ("crossmean_matched_width_margin", "complete_spatial_matched_width_margin"):
        own = [r for r in effects if r["packet"] == "C2_S" and r["analysis_id"] == name and r["calibration"] == "calibrated"]
        add("C2_S", name, "COMPLETE" if len(own) == 1 else "MISSING", "c2s", own[0] if own else None)
    interventions = reader.table("c2r", "fixed_head_interventions.csv")
    for name in ("G_R_given_L", "G_L_given_R", "J_joint", "duplicate_margin", "expanded_margin", "capacity_margin"):
        own = [r for r in effects if r["packet"] == "C2_R" and r["analysis_id"] == name and
            r["representation"] == "R_SIM" and r["readout_family"] == "mlp32" and r["calibration"] == "calibrated"]
        add("C2_R", name, "COMPLETE" if len(own) == 1 else "MISSING", "c2r", own[0] if own else None,
            notes="固定主表示及校准；重复列和MLP64容量对照不替换主T_C。")
    add("C2_R", "complete_fixed_head_replacement_matrix", c2_intervention_status(interventions,
        reader.sources["c2r"].summary.get("missing_controls", [])), "c2r",
        notes="L/R/LL/RR零置换、同类及异类替换是OOD诊断，不是解剖因果干预。")
    add("C2_R", "parallel_repair_and_inherited_raw_isolation", "MISSING", "c2r",
        notes="原修复回执明确仍缺完整L0/R_SUP平行修复及继承raw-isolation审计；不以C2-S替代独立branch路线。")
    add("E0_R", "same_requested_native128_records_complete_family", "COMPLETE" if complete("e0r") and
        reader.sources["e0r"].summary.get("core_status") == "COMPLETE_REPAIRED_MATRIX" else "MISSING", "e0r",
        notes="完整有块支持记录都需通过；只成功部分记录时无MLP聚合。")
    add("E0_R", "E1_transfer", "NOT_APPLICABLE", "e0r", notes="E1明确关闭；原bapa安全候选16<20，E0不替代迁移。")
    return controls


def c2_intervention_status(rows, missing_controls):
    """The fixed SIM repair must retain every model/side/replacement cell."""
    if not rows:
        return "MISSING"
    expected = {('R_SIM', probability, family, model, kind + '_' + side)
        for probability in ('raw', 'calibrated') for family in ('linear', 'mlp32')
        for model in ('C_LR', 'C_LL', 'C_RR')
        for kind in ('zero', 'same_class', 'opposite_class') for side in ('first', 'second')}
    keys = [tuple(row.get(k) for k in ('representation', 'probability_mode', 'family', 'model', 'intervention')) for row in rows]
    complete = len(keys) == len(set(keys)) and set(keys) == expected
    donors_complete = not any('donor support' in str(reason) for reason in missing_controls)
    return 'COMPLETE' if complete and donors_complete and all(row.get('status', 'PASS') == 'PASS' for row in rows) else 'FAILED'


def route_status(reader, effects, controls):
    rows = []
    for packet in PACKETS:
        source = reader.sources[PRIMARY_ROLE[packet]]
        own = [r for r in effects if r["packet"] == packet]
        primary = [r for r in own if r["primary_or_secondary"] == "primary"]
        count = source.summary.get("candidates", source.summary.get("support", {}).get("candidates"))
        if count is None and primary:
            counts = {r["n_candidates"] for r in primary if r["n_candidates"] is not None}
            count = next(iter(counts)) if len(counts) == 1 else None
        supported = source.summary.get("support_status", source.summary.get("support", {}).get("status"))
        if packet in ("N1", "N2", "N3") and reader.sources["support"].complete:
            support = reader.sources["support"].summary.get(packet, {})
            if packet == "N2":
                support = next((r for r in support if r.get("k") == 8), {})
            supported = support.get("status")
            count = count if count is not None else support.get("candidates", support.get("test_candidates"))
        if packet == "G0":
            supported = "SUFFICIENT_FOR_SCREEN" if reader.sources["g0_readouts"].execution == "G0_READOUTS_COMPLETE" else None
        if packet == "E0_R" and source.summary.get("records_with_block_support"):
            supported = "DESCRIPTIVE_ONLY"
        if (packet in ('C2_R', 'E0_R') and source.complete and
                source.summary.get('core_status') == 'INCOMPLETE_PRIMARY_MATRIX' and supported is None):
            supported = 'DESCRIPTIVE_ONLY'
            # Completed fitting proves input availability, never a child count.
            # Counts absent from the source receipt remain unknown.
        if supported in ("SUPPORT_INSUFFICIENT", "SUPPORT_INSUFFICIENT_FOR_E1"):
            supported = "INSUFFICIENT"
        if supported not in ("SUFFICIENT_FOR_SCREEN", "DESCRIPTIVE_ONLY", "INSUFFICIENT"):
            supported = "SUFFICIENT_FOR_SCREEN" if count is not None and count >= (25 if packet == "A2" else 20) else "BLOCKED_INPUT"
        own_controls = [r for r in controls if r["packet"] == packet and r["status"] != "NOT_APPLICABLE"]
        control = "FAILED" if any(r["status"] == "FAILED" for r in own_controls) else "MISSING" if not own_controls or any(
            r["status"] == "MISSING" for r in own_controls) else "COMPLETE"
        floor = .05 if packet == "A2" else .005 if packet in ("N1", "N3") else 0. if packet == "C2_S" else .01
        descriptions = [screen(r["estimate"], r["ci_lower"], r["ci_upper"], floor) for r in primary]
        descriptive = descriptions[0] if descriptions and len(set(descriptions)) == 1 else "MIXED" if descriptions else "NOT_EVALUABLE"
        scientific = descriptive if source.implementation == "PASS" and supported == "SUFFICIENT_FOR_SCREEN" and control == "COMPLETE" else "NOT_EVALUABLE"
        if scientific in ("SUPPORTED_SIGNAL", "SMALL_SIGNAL") and not positive_controls_satisfied(packet, primary, effects):
            scientific = "MIXED"
        if packet in ("G0", "E0_R"):
            scientific, descriptive = "NOT_EVALUABLE", "DIAGNOSTIC_ONLY"
        pending = [r["control"] for r in own_controls if r["status"] in ("MISSING", "FAILED")]
        rows.append(dict(packet=packet, implementation_status=source.implementation, support_status=supported,
            control_status=control, scientific_status=scientific, descriptive_screen=descriptive,
            execution_status=source.execution, source_run=source.run, n_candidates=count,
            primary_representation="R_SIM" if packet not in ("C2_S", "E0_R") else "L0" if packet == "C2_S" else "native128",
            primary_threshold=floor if packet not in ("G0", "E0_R") else None, primary_rows=len(primary),
            pending_controls="|".join(pending), notes=";".join(source.issues), code_hash=source.code_hash))
    by_packet = {r["packet"]: r for r in rows}
    for effect in effects:
        status = by_packet[effect["packet"]]
        effect.update({k: status[k] for k in ("implementation_status", "support_status", "control_status", "scientific_status")})
        effect["descriptive_screen"] = screen(effect["estimate"], effect["ci_lower"], effect["ci_upper"],
            status["primary_threshold"] if status["primary_threshold"] is not None else 0.) if effect["unit"] != "projected_inner_product" else "SCALE_DIAGNOSTIC"
        if effect['packet'] == 'E0_R':
            effect['descriptive_screen'] = 'DIAGNOSTIC_ONLY'
    return rows


def isolated_metrics(reader):
    rows = []
    for role in ("metrics", "g0_readouts", "g0_legacy", "c2s", "c2r", "e0r"):
        try:
            rows.extend(collect_metrics(OneRole(reader, role)))
        except (KeyError, TypeError, ValueError) as error:
            reader.issue(reader.sources[role], "METRIC_ADAPTER_FAILURE", error)
            reader.sources[role].implementation = "BUG"
    enriched = {r["analysis_id"].split("_")[1] for r in rows if r["analysis_id"].startswith(("G0_within_", "G0_bridge_"))}
    return [r for r in rows if not (r["packet"] == "G0" and
        ((r["analysis_id"] == "within_child" and "within" in enriched) or
         (r["analysis_id"] == "offline_bridge" and "bridge" in enriched)))]


def attach_capacity_margins(effects):
    mapping = {("N1", "HP_minus_HPB"): "HPP_minus_HPB", ("N2", "post_gain_mu_var"): "post_mv_vs_dup",
        ("C2_R", "T_C"): "capacity_margin", ("C2_S", "G_crossmean"): "crossmean_matched_width_margin",
        ("C2_S", "G_midline"): "complete_spatial_matched_width_margin"}
    for row in effects:
        target = mapping.get((row["packet"], row["analysis_id"]))
        matches = [r for r in effects if r["analysis_id"] == target and all(r[k] == row[k] for k in
            ("packet", "representation", "population_id", "readout_family", "calibration"))]
        row["capacity_control_margin"] = matches[0]["estimate"] if len(matches) == 1 else None


def positive_controls_satisfied(packet, primary, effects):
    """Numerical promotion rules are stricter than having a control CSV."""
    if packet == "A2":
        # Shared-predictor and quality controls require interpretation; an
        # automatically positive cosine alone cannot establish stimulus origin.
        return False
    targets = {"N1": ("HB_minus_HPB", "HPP_minus_HPB", "HPBnoise_minus_HPB"),
        "N2": ("post_mv_vs_dup", "post_minus_pre_gain_mu_var_post_minus_pre"),
        "N3": ("selected_HB_minus_HBP",), "C2_R": ("capacity_margin",),
        "C2_S": ("crossmean_matched_width_margin", "complete_spatial_matched_width_margin")}.get(packet, ())
    if not primary or not targets:
        return False
    reference = primary[0]
    candidates = [r for r in effects if r["packet"] == packet and all(r[k] == reference[k] for k in
        ("representation", "population_id", "readout_family", "calibration"))]
    for target in targets:
        matches = [r for r in candidates if r["analysis_id"] == target]
        if len(matches) != 1 or matches[0]["estimate"] is None or matches[0]["estimate"] <= 0:
            return False
    if any(r["raw_effect"] is None or r["raw_effect"] <= 0 for r in primary):
        return False
    if packet == "N3":
        noise = [r for r in candidates if r["analysis_id"] == "selected_H_minus_Hnoise"]
        if len(noise) != 1 or noise[0]["estimate"] is None or noise[0]["estimate"] >= reference["estimate"]:
            return False
    return True


SYNTHETIC_COLUMNS = "packet mechanism family rate_role rate_question n_planned n_evaluable n_positive n_unknown n_numerical_failure observed_positive_fraction_of_planned positive_rate_among_evaluable identified_rate_lower identified_rate_upper monte_carlo_ci_lower monte_carlo_ci_upper monte_carlo_ci_definition unknowns_are_not_negative main_estimate_mean_among_evaluable main_estimate_n_evaluable units source_run status execution_coverage interpretation_status automatic_scientific_support expected_behavior rate_acceptance_threshold notes".split()
FIT_COUNT_FIELDS = "head_fit_attempts_total head_fit_completed_total head_fit_attempts_lower_bound head_fit_completed_lower_bound fit_attempts fit_completed fit_unresolved fit_numerical_failures fit_attempt_records fit_attempts_lower_bound fit_completed_lower_bound fit_reused readout_fit_attempts transform_fit_attempts neural_fit_attempts ridge_fit_attempts test_fit_count_lower_bound test_fit_count_unknown test_fit_completion_count test_fit_completion_unknown_count inflight_fit_unknown model_file_count prediction_file_count source_run_count plan_runs_excluded unknown_fit_units model_artifact_count prediction_artifact_count model_summary_hash prediction_summary_hash status receipt_schema_version".split()
COVERAGE_COLUMNS = "field attempted_units present_count missing_count coverage_fraction source_run".split()
RESOURCE_FIELDS = "jobs accounted_jobs missing_jobs ongoing_jobs actual_cpu_core_hours actual_gpu_hours actual_cpu_core_hours_lower_bound actual_gpu_hours_lower_bound reservation_upper_cpu_core_hours reservation_upper_gpu_hours max_cpu_core_hours max_gpu_hours cpu_actual_complete gpu_actual_complete cpu_lower_bound_complete gpu_lower_bound_complete upper_bound_complete budget_status".split()


def collect_auxiliary(reader):
    synthetic = []
    source = reader.sources["synthetic"]
    rates = reader.table("synthetic", "synthetic_rates.csv", required=True)
    for row in rates:
        audit = synthetic_control_audit(rates, row["packet"])
        synthetic.append(dict(row, source_run=source.run, status=source.execution,
            execution_coverage=audit["execution_status"], interpretation_status=audit["interpretation_status"],
            automatic_scientific_support=False, expected_behavior=audit["expected_behavior"], rate_acceptance_threshold=None,
            notes=audit["notes"] + " 固定600机制draw；A2共享W条件与N3两族不是新增独立世界；另列60个G0注入fixture。"))
    if not synthetic:
        for packet in ("A2", "N1", "N2", "N3", "G0"):
            synthetic.append(dict(packet=packet, source_run=source.run, status=source.execution,
                notes="本次未获得可评价机制聚合；不能把未知世界计为阴性。"))
    fit_source = reader.sources["fit_accounting"]
    counts = reader.table("fit_accounting", "fit_counts.csv", required=True)
    coverage = reader.table("fit_accounting", "receipt_field_coverage.csv", required=True)
    counts = [{k: r.get(k) for k in FIT_COUNT_FIELDS} | {"source_run": fit_source.run} for r in counts]
    coverage = [{k: r.get(k) for k in COVERAGE_COLUMNS if k != "source_run"} | {"source_run": fit_source.run} for r in coverage]
    resource_source = reader.sources["resources"]
    resource = [dict(metric=k, value=resource_source.summary.get(k),
        unit="CPU core hours" if "cpu" in k and "hours" in k else "GPU hours" if "gpu" in k and "hours" in k else "count" if k.endswith("jobs") or k == "jobs" else None,
        status=resource_source.execution, source_run=resource_source.run,
        notes="actual缺失保持未知；reservation upper为保守资源上界，不是已测实际使用。") for k in RESOURCE_FIELDS]
    numerical = []
    for role, source in reader.sources.items():
        if source.packet not in PACKETS and role not in ("synthetic", "tests", "tests_retained", "tests_supplement", "fit_accounting"):
            continue
        r = source.summary
        attempted = r.get("head_fits_attempted", r.get("readout_fits", r.get("head_fits")))
        completed = r.get("head_fits_completed", r.get("completed_fits"))
        if role == "a2_residual":
            attempted, completed = r.get("new_readout_fits"), r.get("new_readout_fits")
        numerical.append(dict(packet=source.packet, source_run=source.run, scope="source_summary_not_per_fit_count",
            attempted_fits=attempted, completed_fits=completed, reused_fits=r.get("reused_readout_fits"),
            new_fits=r.get("new_readout_fits"), selected_budget=r.get("selected_budget"),
            extended_members=r.get("extended_members"), status=source.implementation,
            code_hash=source.code_hash, notes="原失败回执保留；启动/完成的精确计数以独立fit_accounting为准，不从计划推算执行。"))
    for role in ("n1", "n3"):
        for row in reader.table(role, "numerical_status.csv"):
            numerical.append(dict(packet=reader.sources[role].packet, source_run=reader.sources[role].run,
                representation=row.get("mode"), readout_family=row.get("family"), scope="complete_family:" + str(row.get("population")),
                planned_fits=row.get("fit_count"), status="PASS" if truth(row.get("complete")) is True else "NUMERICAL_FAILURE",
                notes="fit_count为此族清单大小；不凭complete标志制造逐fit字段。"))
    if counts:
        r = counts[0]
        numerical.append(dict(packet="ALL", source_run=fit_source.run, scope="independent_receipt_accounting",
            attempted_fits=r.get("head_fit_attempts_total"), completed_fits=r.get("head_fit_completed_total"),
            unresolved_fits=r.get("fit_unresolved"), reused_fits=r.get("fit_reused"), status=r.get("status"),
            notes="只接受独立台账明确head总量，缺失留空；fit_attempts可能含transform，不直接对7778头预算。复用不是新fit，完整字段覆盖另表。"))
    return synthetic, counts, coverage, resource, numerical


def csv_write(path, rows, columns):
    """A required empty table still has its declared header; no private columns."""
    frame = pd.DataFrame(rows).reindex(columns=columns)
    for column in frame:
        for value in frame[column]:
            if isinstance(value, str) and re.search(r"(?:^|[\s\"'])/(?:home|projects|tmp|private|scratch|mnt)/", value):
                raise ValueError("REPORT_PUBLIC_ABSOLUTE_PATH")
    frame.to_csv(path, index=False, na_rep="")


def fmt(value):
    v = number(value)
    return "未提供" if v is None else f"{v:.6g}"


def markdown_table(rows, columns, limit=None):
    selected = rows if limit is None else rows[:limit]
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in selected:
        cells = []
        for column in columns:
            value = row.get(column)
            value = "未提供" if value is None or value == "" else str(value)
            cells.append(value.replace("|", "/").replace("\n", " "))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def packet_text(packet, reader, status, effects, controls):
    rows = [r for r in effects if r["packet"] == packet]
    primary = [r for r in rows if r["primary_or_secondary"] == "primary"]
    own = [r for r in controls if r["packet"] == packet]
    source = reader.sources[PRIMARY_ROLE[packet]]
    overview = (f"{packet}：实现 `{status['implementation_status']}`；支持 `{status['support_status']}`；"
        f"对照 `{status['control_status']}`；科学状态 `{status['scientific_status']}`。"
        f"固定来源 `{source.run}`；执行状态 `{source.execution}`。\n\n")
    descriptions = {
        "G0": "共享旧表的重新拟合 logistic probe 与原 R_SUP CNN head 分开报告；原头的 TRAIN_DIAGNOSTIC 分数仅说明优化，不是外层泛化。G0_metadata_002 替代早期时间角色/桥接支持，不替代已复算旧指标。同儿童的后块预测和共享外儿童预测具有不同训练对象，不能只按准确率大小宣称迁移成功。因果/offline 桥接使用共同 QC 试次，仍是处理敏感性。微弱 bAcc/AUC 不保证 CE 优于先验，J 的负值保留。",
        "A2": "共同 Ω、配额和候选集合由完整事件链、QC 与块支持冻结；所有候选使用同一 Ω/q，20 次固定无放回抽样先平均再做候选 bootstrap。主表示始终 R_SIM，R_SUP 是次要平行证据。post-minus-pre 是匹配统计量之差，不将不同宽度的 L0 向量补零相减。共同响应不能简单视为纯伪迹；残差重复性也可能由共享预测项及交叉内积产生，四项代数恒等式与合成反例单列。输出恢复只复用已保存的20次ridge，无新头/PCA/scaler拟合。",
        "C2_R": "这是旧独立左/右 encoder 特征上的完整读出矩阵数值修复。目标、候选/类权重和 alpha 网格继承；优化器改为全批 float64 Adam，全部神经成员先1000步，任一不稳则全族统一2000步，四个最终alpha都先拟合，随后才按最终预算的内层OOF选alpha。旧LBFGS失败保留，不视为神经科学阴性。T_C每次bootstrap都重新取两侧总体CE均值的min；重复列与MLP64容量对照不能省略。置零/替换是OOD诊断，不能声称解剖因果作用。",
        "C2_S": "这是新的20通道观测对象：L8/R8/M4的五种空间成分在共同平均参考下含19个有效自由度；精确重建只证明代数完备性。S0→S1检验跨组均值差，S1→S2检验中线局部信息，两者须与匹配宽度重复列比较；FULL20为参考。局部成分数值不依赖对侧原始数值，但完整记录QC决定入选，selection_isolation=False。主L0 logistic六视图完整矩阵独立于C2-R；次要MLP处于预算限制。",
        "N1": "主量为 R_SIM/P_nat/MLP32/temperature 的 HP−HPB，背景增益需达到0.005 bits/trial且区间下界>0；还需 HB−HPB>0并超过PP和噪声扩维对照。raw、自然先验与平衡先验分列。donor冻结时不使用当前标签；固定头替换及匹配训练donor对照保留同支持参考，其变化可能反映输入分布失配，不能直接解释为背景的因果必要性。",
        "N2": "主对象固定 R_SIM/P_bal/logistic、k=8同一袋上的HMU−HMUVAR，量级0.01 bits/bag；需要超过重复均值列、pre与H_BAG解释。10次测试重组不重新拟合，必须先按候选平均后评价方向。k=4/8/16共同支持审计只说明支持；未运行的k曲线不得作图或宣称已完成。pre与post窗长度不同，二者差异不是纯因果响应。",
        "N3": "主结果使用每个视图的训练OOF选族，禁止事后替换为某固定族。H基线风险与H→HP、HB→HBP、H→Hnoise并列；0.005 bits/trial主增量还须在H+pre以外成立。负增益表示当前有限读出下预测风险上升，可能包含扩维代价和OOF选择不同模型族的容量差异；噪声扩维也受损时尤其不能写成“EEG负信息”或“脑内无信息”。历史稀疏/结构空格只描述，不能补造两类支持。",
        "E0_R": "这是预定同日配对中的native128、记录内独立块目标任务可读性维护。全套有块支持记录的MLP族都数值稳定后才允许整族聚合，不能挑成功记录。旧linear精确复用，不计为新fit。纯音与bapa分别报告J及CE；混合MFF不是全CI群体。即使目标任务可读，也不证明跨儿童、跨任务迁移或临床效度；E1保持关闭。",
    }
    text = overview + descriptions[packet] + "\n\n"
    if packet == 'C2_R':
        text += '内折仅重新拟合读出与其缩放，outer encoder保持冻结，inner_encoder_refitted=False；这不是编码器在内外折都重新训练的完整嵌套验证。容量控制的margin与主T_C并列，不由替换诊断改变主结论。\n\n'
    if packet == 'E0_R':
        summary = source.summary
        text += ('训练时按记录内filter block/class加权；最终测试CE沿用旧classification_metrics的记录内candidate/class平衡，再按完整配对记录汇总，'
            '不声称最终评分按block等权。E0不设本轮其他路线的0.01 bits推进阈值，J及区间只作描述。\n\n')
        audit = getattr(reader, 'e0_support', {})
        if audit:
            text += (f"记录流：请求{audit['records_requested']}，有块支持{audit['records_with_block_support']}；旧linear完整{audit['legacy_linear_records_complete']}记录，"
                f"任务汇总只用{audit['legacy_linear_complete_pairs']}个完整配对。新MLP每记录所有64个规定头均稳定的记录数为{audit['mlp_records_all_required_heads_stable']}，"
                f"整族门限允许进入主聚合的记录数为{audit['mlp_records_available_for_primary_aggregation']}。"
                f"头部稳定{audit['stable_heads']}/{audit['required_heads']}，未解决{audit['unresolved_heads']}；0聚合许可不是阴性效应。\n\n")
            legacy = [dict(task=row['task'], calibration=row['calibration'], complete_pairs=row['complete_pairs'],
                ce_bits=row['mean_CE_bits'], **row['J_bits_interval']) for row in audit['legacy_linear_results']]
            text += ('保留旧E0_native_003的完整linear结果（零重拟合，不替代新MLP主矩阵；estimate为J bits/trial）：\n\n' +
                markdown_table(legacy, ['task','calibration','complete_pairs','ce_bits','estimate','ci_lower','ci_upper']) + '\n\n')
        else:
            text += '记录流计数未提供，不能从拟合头数倒推儿童或记录数。\n\n'
        text += '任务J只用完整配对，不代表全部有块支持记录的均值；旧linear、单条记录数值完成及全族科学可评价保持分开。\n\n'
    if packet == "A2":
        s = reader.sources["a2_core"].summary
        text += "冻结 Ω=" + json.dumps(s.get("omega"), ensure_ascii=False) + "；共同候选数=" + str(s.get("candidates", "未提供")) + "。未入 Ω 的上下文不参与主估计，不由次要结果补回。\n\n"
    if packet == "G0":
        text += "旧共享表复算最大误差=" + fmt(reader.sources["g0_legacy"].summary.get("max_shared_metric_error")) + "。"
        text += "原within_receipts中的n_calibration存在记录元数据错误，本报告不使用它；实际训练样本数应以原生fit start的n或时间角色核对，不能用校准参数字典长度。温度记录数是应用到各头的次数，不是独立校准参数数。\n\n"
    if packet == "C2_S":
        geometry = reader.sources["c2s"].summary.get("geometry", {})
        text += "源几何回执：post重建最大误差=" + fmt(geometry.get("max_reconstruction_error")) + "；全epoch=" + fmt(geometry.get("max_full_epoch_reconstruction_error")) + "；19维=" + fmt(geometry.get("max_19dim_reconstruction_error")) + " μV。\n\n"
    if packet == 'N3':
        selection = read_family_selection(reader)
        text += '保存的训练OOF选族（折数，不是人数）：\n\n' + markdown_table(selection,
            ['mode', 'population', 'view', 'family', 'n_outer_folds']) + '\n\n'
        text += 'H与增强视图若选中不同模型族，主风险差同时包含选族/容量变化；固定族结果保留作诊断，不能事后替代主比较。\n\n'
    text += "主预设效应（空表表示尚无合格主聚合，不能当作零）：\n\n"
    text += markdown_table(primary, ["analysis_id", "readout_family", "estimate", "ci_lower", "ci_upper", "n_candidates", "unit", "descriptive_screen"]) + "\n\n"
    text += "固定对照执行状态：\n\n" + markdown_table(own, ["control", "population_id", "readout_family", "calibration", "status", "estimate", "ci_lower", "ci_upper", "source_run"]) + "\n\n"
    text += "全部表示、raw/temperature及诊断混合校准在paired_effects与metrics_aggregate保留。区间是固定OOF候选cluster bootstrap，并非重拟合整条pipeline。缺失字段表示源聚合未提供；未由试次或记录数倒推儿童人数。\n"
    return text


FIGURE_CONTRASTS = {
    'C2_R': {'T_C':'Joint vs best single side (primary)', 'duplicate_margin':'Repeated-side control',
        'expanded_margin':'Wider single-side control', 'capacity_margin':'All capacity controls'},
    'C2_S': {'G_crossmean':'Add cross-group mean (primary)', 'G_midline':'Add midline (primary)',
        'crossmean_matched_width_margin':'Cross-group mean: width control',
        'complete_spatial_matched_width_margin':'Full spatial features: width control'},
    'A2': {'post_delta_cosine':'Unadjusted (primary)', 'pre_delta_cosine':'Pre window',
        'residual_audit_P_cosine':'Predicted background (diagnostic)', 'residual_audit_R_cosine':'Residual (diagnostic)'},
    'N1': {'HP_minus_HPB':'Add pre to H + post (primary)', 'HB_minus_HPB':'Add post to H + pre',
        'HPP_minus_HPB':'Repeated post vs post + pre', 'HPBnoise_minus_HPB':'Noise pre vs actual pre'},
    'N2': {'post_gain_mu_var':'Post: add variance (primary)', 'post_mv_vs_dup':'Post: repeated mean control',
        'pre_gain_mu_var':'Pre: add variance', 'post_minus_pre_gain_mu_var_post_minus_pre':'Post gain minus pre gain'},
    'N3': {'selected_H_minus_HP':'H vs H + post (primary)', 'selected_HB_minus_HBP':'H + pre vs H + pre + post',
        'selected_H_minus_Hnoise':'H vs H + noise'},
}


def figure_rows(effects, packet):
    selected = []
    for row in effects:
        if row['packet'] != packet or any(row.get(k) is None for k in ('estimate','ci_lower','ci_upper')):
            continue
        # N2's emitted logistic aggregates require the entire linear family;
        # a withheld secondary MLP cannot hide these measured primary values.
        linear_secondary_failure = (packet=='N2' and row.get('readout_family')=='logistic'
            and row.get('implementation_status')=='NUMERICAL_FAILURE' and row.get('source_run')=='N2_core_001')
        if row.get('implementation_status')!='PASS' and not linear_secondary_failure:
            continue
        if packet in FIGURE_CONTRASTS:
            representation = 'L0' if packet == 'C2_S' else 'R_SIM'
            if row.get('analysis_id') not in FIGURE_CONTRASTS[packet] or row.get('representation') != representation:
                continue
            if packet != 'A2':
                selector = {'C2_R': ('P_bal', 'calibrated', 'mlp32'),
                    'C2_S': ('P_bal', 'calibrated', 'logistic'),
                    'N1': ('P_nat', 'temperature', 'mlp32'),
                    'N2': ('P_bal', 'temperature', 'logistic'),
                    'N3': ('P_nat', 'temperature', 'training_OOF_selected')}[packet]
                if tuple(row.get(k) for k in ('population_id', 'calibration', 'readout_family')) != selector:
                    continue
        elif row.get('primary_or_secondary')!='primary':
            continue
        selected.append(row)
    order = list(FIGURE_CONTRASTS.get(packet, {}))
    return sorted(selected,key=lambda r:order.index(r['analysis_id'])) if order else selected


def make_figures(report, effects):
    """One aggregate-only figure per packet; no participant-level points."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    outputs = []
    for packet in PACKETS:
        rows = figure_rows(effects,packet)
        if not rows:
            continue
        fig, ax = plt.subplots(figsize=(8, max(2.4, .6 * len(rows) + 1.5)))
        labels = []
        for i, row in enumerate(rows):
            lo, hi, e = row["ci_lower"], row["ci_upper"], row["estimate"]
            ax.plot([lo, hi], [i, i], color="#2563a6", linewidth=2)
            ax.plot(e, i, "o", color="#2563a6", markersize=5)
            labels.append(FIGURE_CONTRASTS.get(packet,{}).get(row['analysis_id'],row['analysis_id']))
        ax.axvline(0, color="black", linewidth=.8)
        ax.set_yticks(range(len(rows)), labels)
        ax.set_xlabel(rows[0]["unit"] + " (fixed OOF, 95% cluster interval)")
        ax.set_title(packet + " / primary and required controls" +
            ('\nComplete linear family; secondary MLP unresolved' if packet=='N2' and
             any(r['implementation_status']=='NUMERICAL_FAILURE' for r in rows) else ''))
        ax.invert_yaxis()
        ax.grid(axis="x", alpha=.2)
        fig.tight_layout()
        for suffix in ("png", "pdf"):
            path = report / (packet + "_primary." + suffix)
            fig.savefig(path, dpi=180, bbox_inches="tight")
            outputs.append(path)
        plt.close(fig)
    return outputs


REPORT_FILES = {"G0": "G0_DIAGNOSTIC_REPORT.md", "A2": "A2_REPORT.md", "N1": "N1_CONTEXT_REPORT.md",
    "N2": "N2_DISTRIBUTION_REPORT.md", "N3": "N3_SEQUENCE_REPORT.md", "E0_R": "E0_REPAIR_REPORT.md"}
STATUS_COLUMNS = "packet implementation_status support_status control_status scientific_status descriptive_screen execution_status source_run n_candidates primary_representation primary_threshold primary_rows pending_controls notes code_hash".split()
TERMINAL_BLOCKED = {"FAILED", "TIMEOUT", "OUT_OF_MEMORY", "CANCELLED", "NODE_FAIL", "BUDGET_LIMITED", "JOB_COMPLETED_WITHOUT_RUN_COMPLETION"}


def delivery_round_complete(sources, assembly_errors=()):
    """Terminal scientific failures may close; integrity and budget must pass."""
    required = [role for role in SOURCES if role not in ("tests_retained", "a2_residual_failed", "tests_supplement", "postflight_retained")]
    integrity = sources['postflight']
    integrity_ok = integrity.complete and integrity.execution == 'PASS' and all(
        integrity.summary.get(k) == 0 for k in ('legacy_changed', 'legacy_missing', 'permission_anomalies'))
    budget = sources['resources']
    budget_ok = budget.complete and budget.summary.get('budget_status') in ('WITHIN_CONSERVATIVE_BOUND', 'WITHIN_BUDGET')
    return bool(not assembly_errors and integrity_ok and budget_ok and all(
        sources[role].complete or sources[role].execution in TERMINAL_BLOCKED for role in required))


def evidence_overview(reader, effects, metrics):
    """Short interpretation from fixed aggregates; missing packets stay pending."""
    def ready(packet):
        source = reader.sources[PRIMARY_ROLE[packet]]
        return source.complete and source.implementation == "PASS"
    def one(packet, analysis, **selectors):
        rows = [r for r in effects if r.get("packet") == packet and r.get("analysis_id") == analysis and
            all(r.get(k) == value for k, value in selectors.items())]
        return rows[0] if len(rows) == 1 and all(rows[0].get(k) is not None for k in ("estimate", "ci_lower", "ci_upper")) else None
    def interval(row):
        return "待定" if row is None else f"{fmt(row['estimate'])}（95% CI {fmt(row['ci_lower'])} 至 {fmt(row['ci_upper'])}）"
    lines = ["当前证据解读只使用下列固定完成来源，方向性描述不覆盖后面的四轴状态；待定项不填零，也不当阴性。"]
    if ready("G0"):
        selected = [r for r in metrics if r.get("packet") == "G0" and r.get("metric") == "bacc" and
            r.get("calibration") == "temperature" and ((r.get("representation") == "R_SIM" and
            (r.get("analysis_id", "").startswith("G0_within_") or r.get("analysis_id") == "within_child")) or
            r.get("analysis_id", "").startswith("G0_bridge_") or r.get("analysis_id") == "offline_bridge")]
        values = "；".join(str(r["analysis_id"]) + "/" + str(r.get("representation") or "source-defined")
            + " bAcc=" + fmt(r.get("estimate")) for r in selected)
        lines.append("G0：" + (values or "聚合指标待定") + "。这是同儿童和共同试次处理敏感性的描述，不能据轻微准确率变化声称迁移或处理优越性；CE与平衡先验J仍须并读。")
    else:
        lines.append("G0：固定读出来源尚未完整可评价，待定。")
    main = one("A2", "post_delta_cosine", representation="R_SIM") if ready("A2") else None
    if main:
        common = one("A2", "common_response_cosine", representation="R_SIM")
        predictor = one("A2", "residual_audit_P_cosine", representation="R_SIM")
        residual = one("A2", "residual_audit_R_cosine", representation="R_SIM")
        decision = "当前未校正实现未达到0.05且区间下界>0的推进条件。" if main["estimate"] < .05 or main["ci_lower"] <= 0 else "主量达到预定数值条件，仍须限制pre/背景解释，不能直接宣布支持。"
        lines.append("A2：主R_SIM未校正T=" + interval(main) + "；共同响应=" + interval(common) + "；背景预测P=" + interval(predictor) + "；残差=" + interval(residual) + "。" + decision + "共享预测项本身可重复，残差不能替代未校正主终点；SUP次要结果不换主。")
    else:
        lines.append("A2：完整主聚合待定，不能从残差或次要表示补出主结论。")
    spatial = [one("C2_S", name, calibration="calibrated") for name in ("G_crossmean", "G_midline")]
    if ready("C2_S") and all(spatial):
        margins = [one("C2_S", name, calibration="calibrated") for name in ("crossmean_matched_width_margin", "complete_spatial_matched_width_margin")]
        passed = all(row and row["ci_lower"] > 0 for row in spatial + margins)
        lines.append("C2-S：跨组均值增量=" + interval(spatial[0]) + "；中线增量=" + interval(spatial[1]) + " bits/trial。" +
            ("数值方向仍需与全部控制结合解释。" if passed else "当前两个成分未共同通过正增量及重复列对照，不支持据该线性实现推进空间增量主张。") + "精确重建说明代数完备性，不是预测收益；不能替代C2-R。")
    else:
        lines.append("C2-S：完整共同试次线性矩阵待定。")
    selector = dict(representation="R_SIM", population_id="P_nat", readout_family="training_OOF_selected", calibration="temperature")
    n3 = one("N3", "selected_H_minus_HP", **selector) if ready("N3") else None
    if n3:
        pre = one("N3", "selected_HB_minus_HBP", **selector)
        noise = one("N3", "selected_H_minus_Hnoise", **selector)
        decision = "当前训练OOF选族实现未达到0.005且区间下界>0的EEG增量推进条件。" if n3["estimate"] < .005 or n3["ci_lower"] <= 0 else "主量方向积极，但合成识别、pre和噪声对照仍限制推进。"
        lines.append("N3：H→HP=" + interval(n3) + "；HB→HBP=" + interval(pre) + "；H→Hnoise=" + interval(noise) + " bits/trial。" + decision + "负增益及噪声扩维代价反映有限读出风险和所选模型容量，不能称EEG负信息或无脑内信息。")
    else:
        lines.append("N3：完整训练OOF选族主聚合待定，不能以某一固定族替代。")
    for packet in ("N1", "N2", "C2_R", "E0_R"):
        primary = [r for r in effects if r.get("packet") == packet and r.get("primary_or_secondary") == "primary"]
        expected = 2 if packet == "E0_R" else 1
        source = reader.sources[PRIMARY_ROLE[packet]]
        linear_primary_only = (packet == 'N2' and source.complete and source.execution == 'CORE_MATRIX_RECORDED'
            and source.implementation == 'NUMERICAL_FAILURE' and len(primary) == 1
            and primary[0].get('readout_family') == 'logistic')
        if not (ready(packet) or linear_primary_only) or len(primary) != expected or any(r.get(k) is None for r in primary for k in ("estimate", "ci_lower", "ci_upper")):
            source = reader.sources[PRIMARY_ROLE[packet]]
            state = '本轮数值未完成' if source.complete and source.implementation == 'NUMERICAL_FAILURE' else '待定'
            lines.append(f"{packet}：{state}（{source.execution}）；完整族未完成/无合格聚合时不能给科学阴性。")
            continue
        values = "；".join(r["analysis_id"] + "=" + interval(r) for r in primary)
        floor = .005 if packet == "N1" else .01
        conclusion = "当前固定实现未达到预定数值推进条件；必要控制仍须完整解释。" if any(r["estimate"] < floor or r["ci_lower"] <= 0 for r in primary) else "主量达到数值条件，必要对照和合成识别仍须核对，不能仅凭完成作阳性判断。"
        if packet == "E0_R":
            conclusion = "只评价目标任务记录内可读性；E1关闭，不作跨任务/儿童迁移结论。"
        if linear_primary_only:
            conclusion += ' 这里仅描述源程序按完整族规则输出的logistic主矩阵；次要MLP32数值未解决，整包四轴仍保留NUMERICAL_FAILURE/NOT_EVALUABLE，不选取神经族的成功子集。'
        if packet == 'N2':
            history = [r for r in metrics if r.get('packet') == 'N2' and r.get('analysis_id') == 'N2_post_'
                and r.get('representation') == 'R_SIM' and r.get('readout_family') == 'logistic'
                and r.get('calibration') == 'temperature' and r.get('model') == 'H'
                and r.get('metric') in ('ce_bits','bacc')]
            if history:
                conclusion += ' 不含EEG的H_BAG基线：'+ '；'.join(r['metric']+'='+fmt(r['estimate']) for r in history)+ '。高准确率须先与此历史基线比较，不能归为EEG分布收益。'
            if primary[0]['estimate'] < .01 or primary[0]['ci_lower'] <= 0:
                conclusion += ' 当前固定k=8均值加方差线性实现未触发本轮预定的集合网络推进条件；这不排除未检验的表示或分布特征。'
        lines.append(packet + "：" + values + "。" + conclusion)
    return "\n\n".join(lines) + "\n\n"


def write_reports(reader, report, statuses, effects, metrics, controls, coverage, numerical, resource, source_rows):
    texts = {s["packet"]: packet_text(s["packet"], reader, s, effects, controls) for s in statuses}
    for packet in PACKETS:
        own = [r for r in metrics if r["packet"] == packet and r["metric"] in ("ce_bits", "J_bits", "bacc") and
            ((packet == "G0" and (r["analysis_id"].startswith(("G0_within_", "G0_bridge_")) or
                r["analysis_id"] in ("within_child", "offline_bridge"))) or
             (packet != "G0" and r["representation"] in ("R_SIM", "L0", "native128") and
                r["calibration"] in ("temperature", "calibrated")))]
        texts[packet] += "\n\n预设风险与准确率（固定来源，不按大小筛选；未提供AUROC/Brier/区间时保持空值）：\n\n" + markdown_table(
            own, ["analysis_id", "representation", "population_id", "model", "readout_family", "calibration", "metric", "estimate", "ci_lower", "ci_upper", "n_candidates", "n_records"])
    for packet, filename in REPORT_FILES.items():
        (report / filename).write_text(texts[packet], encoding="utf-8")
    (report / "C2_REPAIR_AND_GEOMETRY_REPORT.md").write_text(texts["C2_R"] + "\n\n" + texts["C2_S"], encoding="utf-8")
    closed = ("旧结论保持冻结，本轮没有新的临床终点或B/D重新选型。固定来源为Auditory5的S4_final_001/metrics_aggregate.csv及AUDITORY5_FINAL_STATUS_v1.md。"
        "旧B完整控制后的R_SIM条件历史增益为−0.002169 bits/trial（60个候选组），未达到原0.01 bits门槛；"
        "旧D的R_SIM临床增量为0.108730源量表分，95%区间[−0.142199,0.387963]（51个候选组），未达到原0.5源量表单位门槛。"
        "这些是已有阴性筛查，不能由本轮新N3估计对象改写。旧C/E数值失败不是科学阴性，修复前后源回执均保留。\n\n"
        "E1跨任务迁移保持关闭：原bapa安全候选支持16，低于20；E0记录内目标可读性不替代E1。MFF来源混合，不能整体称CI样本。"
        "本轮已见数据下的探索不能把已有候选重新描述为未触碰外部验证。\n\n"
        "下一步只可针对已缺证据推进：A2须限制共享背景预测项解释；C2-R须先完成预定整族与继承隔离控制；N1/N3须解释先验、pre和容量代价；N2须在相同bag预算与共同队列验证分布增量。"
        "已完成且增量阴性的具体估计器不因改名或扩大网络重新成为原假设的确认性检验。\n")
    closed += ('\n重新启动旧B需要新的证据证明固定历史对象有可靠、超出刺激与序列先验的可读增量；本轮N3改变了目标，不能充当旧B复现。'
        '重新启动旧D需要先获得可靠且解释明确的EEG测量对象，并解决量表单位和同期性，再冻结临床增量检验及独立评价队列。'
        '当前结果不否定所有历史效应或EEG临床信息，但不授权继续旧阈值、null空间和临床终点搜索。\n')
    (report / "CLOSED_ROUTES.md").write_text(closed, encoding="utf-8")
    metadata = ("候选身份簇仍不是完全确证的独立儿童；不能用epoch、record、GUID或散列ID推断独立人数。既有来源链接与歧义保留。\n\n"
        "HA事件数字literal的声学含义、是否使用声码处理、确切刺激/设备设置仍未被本轮证明。临床自由文本已有佩戴/历史线索，不能笼统写所有设备历史未知；"
        "但这些线索不能精确锚定到每个EEG段的设备开关、佩戴或状态。个别访视中的佩戴变化/不适线索不授权无锚点裁剪EEG。\n\n"
        "EEG与临床量表的精确同期性、部分量表0–40数值在百分制标题下的单位解释仍需源证据，不能把文件名或采集日期近似当作确认。"
        "MFF包括明确CI/CIHA及未判定来源；历史normal字样只作为literal来源，不自动 adjudicate 为正常听力。E1支持不足保持关闭。\n\n"
        "报告只展示聚合，真实路径、精确日期、姓名、候选/记录/试次ID与详细异常留在受限产物。后续public_audit是列、文本路径和已知ID的检查，"
        "不是OCR、彻底匿名化证明或外部发布许可。\n")
    (report / "REMAINING_METADATA_QUESTIONS.md").write_text(metadata, encoding="utf-8")
    intro = evidence_overview(reader, effects, metrics)
    retained = reader.sources.get('postflight_retained')
    if retained and retained.complete:
        intro += (f"交付修订：首版postflight_001记录{retained.summary.get('permission_anomalies', '未知')}项日志权限异常；"
            f"本版固定复核为{reader.sources['postflight'].run}，状态{reader.sources['postflight'].execution}。"
            "final_001的旧round_complete字段只检查来源终态，未阻止权限失败，不能作为最终验收依据；"
            "本版要求旧文件、private权限及资源预算通过后才允许round_complete。原失败回执和首版报告保留。\n\n")
    intro += ("本报告从固定版本的完成回执和公开聚合表组装，没有加载模型、读取EEG、重新拟合或重做效应bootstrap。"
        "主R_SIM与次要R_SUP/R_RAND/L0分列，不选择最好表示。实现、支持、对照、科学四轴独立；descriptive_screen仅描述已观察主量方向，"
        "不覆盖NOT_EVALUABLE，也不以阴性掩盖未完成。\n\n"
        "主real-head gate固定tests_010；tests_009的literal-null解析错误尝试保留。tests_011仅补充当前模块实现验收，"
        "独立check-module不冒充全部真实分析gate。计划固定plan_004，共同支持固定S1_support_004。"
        "原A2残差失败是输出文件独占写入冲突；恢复只重建保存统计，不消耗新的20次ridge拟合。\n\n")
    intro += markdown_table(statuses, ["packet", "implementation_status", "support_status", "control_status", "scientific_status", "descriptive_screen"]) + "\n\n"
    for packet in PACKETS:
        intro += texts[packet] + "\n\n"
    intro += ("拟合回执与预算：\n\n" + markdown_table(numerical, ["packet", "source_run", "scope", "attempted_fits", "completed_fits", "reused_fits", "status"]) +
        "\n\n§15.2逐fit字段覆盖来自独立fit_accounting，不由本报告补造；attempt与completed分开，transform另列，recovery reuse不是新head预算。"
        "没有原生记录的预测hash、校准scope、资源等字段保持缺失，源run层hash不冒充逐fit原生字段。\n\n" +
        markdown_table(coverage, ["field", "attempted_units", "present_count", "missing_count", "coverage_fraction"]) + "\n\n" +
        markdown_table(resource, ["metric", "value", "unit", "status"]) +
        "\n\n历史sacct缺失时actual资源未知，不置0；资源保守上界与实际量分列。600合成机制draw的假阳性倾向/恢复率及未知世界固定分母见synthetic_summary；"
        "A2共用draw的W条件、N3同世界两族不算新儿童。合成机制检验不能直接声称真实样本功效。完整分母不代表正负世界已按预期区分；"
        "方案没有冻结跨世界恢复率/FPR验收阈值，本报告不事后新增。机制方向的定性复核见SYNTHETIC_INTERPRETATION.md；该复核不将数值未解决世界或未覆盖控制改为PASS，也不因完成自动支撑科学阳性。\n\n"
        "固定来源与保留失败：\n\n" + markdown_table(source_rows, ["role", "source_run", "execution_status", "implementation_status", "issues"]) +
        "\n\n来源精确SHA256在source_hashes.csv的逻辑别名下；真实路径映射和异常细节仅保存在private。"
        "各packet图只画预设主比较及必要对照的总体点和完整区间，不画个体点，不隐藏负值；缺输入不绘制零值替代图。\n\n" + closed)
    (report / "NEXT_ROUND_REPORT.md").write_text(intro, encoding="utf-8")


def run(config, registry, site, dest, public, report):
    """Assemble a new immutable report from the explicit SOURCES above.

    Missing/incomplete runs produce an IN_PROGRESS delivery with blank metrics.
    Reporting errors are private and block evaluation; no alternative run is
    selected. This is zero-fit assembly, not an independent model validation.
    """
    require_slurm()
    dest, public, report = map(lambda p: Path(p).resolve(), (dest, public, report))
    if dest.parent != ROOT / "private/auditory_next_v2" or public != ROOT / "results/auditory_next_v2" / dest.name or report != ROOT / "reports/auditory_next_v2" / dest.name:
        raise ValueError("REPORT_OUTPUT_SCOPE")
    if Path(site["root"]).resolve() != ROOT or not (dest / "start.json").is_file():
        raise ValueError("REPORT_RUN_PROVENANCE_REQUIRED")
    if (public / "route_status.csv").exists() or (dest / "completion.json").exists():
        raise FileExistsError("REPORT_REQUIRES_NEW_RUN")
    reader = Reader()
    for role in SOURCES:
        reader.source(role)
    resource_rows = reader.table("resources", "resource_usage.json", kind="json", private=True) or []
    resource_state_evidence = {}
    for source in reader.sources.values():
        audit = resource_state_for_source(source, resource_rows)
        source.execution, source.implementation = audit["execution"], audit["implementation"]
        resource_state_evidence[source.role] = dict(audit, start_job_id=source.job_id)
    for name in ("docs/AUDITORY5_FINAL_STATUS_v1.md", "docs/AUDITORY_NEXT_GATE_COVERAGE_FINAL_v2.md",
                 "docs/AUDITORY_NEXT_REPRODUCTION_v2.md", "docs/AUDITORY_NEXT_SEED_DECISION_v2.md",
                 "docs/AUDITORY_NEXT_SYNTHETIC_INTERPRETATION_v2.md", "AUDITORY_NEXT_ROUND_SERVER_PLAN_v2.md",
                 "results/auditory5_v1/S4_final_001/metrics_aggregate.csv"):
        path = ROOT / name
        if path.is_file():
            value = digest(path)
            reader.hashes[str(path)] = value
            reader.public_hashes.append(dict(logical_alias="protocol/" + path.name, sha256=value, bytes=path.stat().st_size))
    effects = isolated_effects(reader)
    attach_capacity_margins(effects)
    metrics = isolated_metrics(reader)
    assembly_errors = []
    reader.e0_support = {}
    if reader.sources['e0r'].complete:
        try:
            from .repair_support_report import read_repair_support
            reader.e0_support = read_repair_support(ROOT, reader)
        except (OSError, ValueError, TypeError, KeyError) as error:
            reader.issue(reader.sources['e0r'], 'E0_RECORD_FLOW_ADAPTER_FAILURE', error)
            reader.sources['e0r'].implementation = 'BUG'
            assembly_errors.append('E0_RECORD_FLOW_ADAPTER_FAILURE')
    try:
        eligibility = collect_eligibility(reader)
    except (ValueError, TypeError, KeyError) as error:
        eligibility = []
        reader.issue(reader.sources["support"], "ELIGIBILITY_ADAPTER_FAILURE", error)
        reader.sources["support"].implementation = "BUG"
        assembly_errors.append("ELIGIBILITY_ADAPTER_FAILURE")
    try:
        controls = collect_controls(reader, effects)
    except (ValueError, TypeError, KeyError) as error:
        reader.errors.append(dict(code="CONTROL_ADAPTER_FAILURE", exception_class=type(error).__name__, detail=str(error)))
        controls = [dict(packet=p, control="report_control_adapter", status="FAILED", notes="源聚合解析失败，详细错误仅private。") for p in PACKETS]
        assembly_errors.append("CONTROL_ADAPTER_FAILURE")
    synthetic, fit_counts, coverage, resources, numerical = collect_auxiliary(reader)
    enrichment = reader.table('fit_accounting', 'receipt_enrichment_coverage.csv', required=True)
    supplement_columns = {
        "candidate_influence_aggregate.csv": "packet source_run mode population family window calibration first second n_candidates estimate leave_one_out_min leave_one_out_max all_leave_one_out_positive positive_candidates negative_candidates max_absolute_share scope".split(),
        "temperature_bounds.csv": "packet source_run mode bank population family window n_temperatures parameter_records_are_independent calibration_record_scope lower_bound upper_bound lower_touch_count upper_touch_count minimum_temperature maximum_temperature mixture_primary".split(),
        "history_stratum_support.csv": "mode population previous_run_bin class0_trials class1_trials n_candidates n_candidates_both_classes n_trials".split(),
    }
    supplements = {name: reader.table("metrics", name) for name in supplement_columns}
    n3_selections = read_family_selection(reader)
    for packet in ("N1", "N2", "N3"):
        enriched = [r for r in reader.sources["metrics"].summary.get("sources", []) if r.get("packet") == packet]
        complete = len(enriched) == 1 and enriched[0].get("status") == "PASS"
        controls.append(dict(packet=packet, control="fixed_prediction_metrics_and_influence", status="COMPLETE" if complete and
            any(r.get("packet") == packet for r in supplements["candidate_influence_aggregate.csv"]) else "MISSING",
            source_run=reader.sources["metrics"].run, notes="AUROC/Brier、留一候选影响及校准边界只从固定预测派生；不重新拟合。"))
    # Verify every consumed source again before publishing a stable as-of view.
    changed = [path for path, value in reader.hashes.items() if not Path(path).is_file() or digest(path) != value]
    if changed:
        reader.errors.append(dict(code="INPUT_CHANGED_DURING_ASSEMBLY", paths=changed))
        controls.extend(dict(packet=p, control="source_hash_stability", status="FAILED", notes="报告读取期间来源发生变化，禁止科学判定。") for p in PACKETS)
        assembly_errors.append("INPUT_CHANGED_DURING_ASSEMBLY")
    statuses = route_status(reader, effects, controls)
    # A source's malformed required artifact is an implementation issue even
    # when its original modeling receipt was complete. Other packets retain
    # their own independent evidence and status.
    assembly_errors.extend("SOURCE_AGGREGATE_FAILURE:" + role for role, source in reader.sources.items()
        if any(issue.startswith(("EFFECT_ADAPTER_FAILURE", "METRIC_ADAPTER_FAILURE", "AGGREGATE_SCHEMA_FAILURE",
            "MISSING_REQUIRED_AGGREGATE")) for issue in source.issues))
    source_rows = [dict(role=s.role, source_run=s.run, packet=s.packet, execution_status=s.execution,
        implementation_status=s.implementation, completed_receipt=s.complete, code_hash=s.code_hash, issues=";".join(s.issues)) for s in reader.sources.values()]
    outputs = {
        "route_status.csv": (statuses, STATUS_COLUMNS), "eligibility_aggregate.csv": (eligibility, ELIGIBILITY_COLUMNS),
        "metrics_aggregate.csv": (metrics, METRIC_COLUMNS), "paired_effects.csv": (effects, EFFECT_COLUMNS),
        "controls_aggregate.csv": (controls, CONTROL_COLUMNS), "numerical_status.csv": (numerical, NUMERIC_COLUMNS),
        "synthetic_summary.csv": (synthetic, SYNTHETIC_COLUMNS),
        "resource_usage.csv": (resources, "metric value unit status source_run notes".split()),
        "fit_counts.csv": (fit_counts, FIT_COUNT_FIELDS + ["source_run"]),
        "receipt_field_coverage.csv": (coverage, COVERAGE_COLUMNS),
        "receipt_enrichment_coverage.csv": (enrichment,
            'field attempted_units native_count alias_count derived_count inherited_count unknown_count'.split()),
        "n3_training_family_selection.csv": (n3_selections,
            'mode population view family n_outer_folds selector'.split()),
        "source_status.csv": (source_rows, "role source_run packet execution_status implementation_status completed_receipt code_hash issues".split()),
        "source_hashes.csv": (reader.public_hashes, "logical_alias sha256 bytes".split()),
    }
    # Supplements stay aggregate-only and keep explicit, fixed source roles.
    for name, columns in supplement_columns.items():
        outputs[name] = supplements[name], columns
    # Source hashes include the supplements as well.
    outputs["source_hashes.csv"] = reader.public_hashes, "logical_alias sha256 bytes".split()
    for name, (rows, columns) in outputs.items():
        csv_write(public / name, rows, columns)
    if reader.e0_support:
        write_json(public / 'e0_support_summary.json', reader.e0_support)
    figure_status = "COMPLETE_OR_NO_COMPLETED_PRIMARY_EFFECTS"
    try:
        make_figures(report, effects)
    except (ImportError, ValueError, RuntimeError, OSError) as error:
        figure_status = "OPTIONAL_FIGURE_FAILURE"
        reader.errors.append(dict(code=figure_status, exception_class=type(error).__name__, detail=str(error)))
    write_reports(reader, report, statuses, effects, metrics, controls, coverage, numerical, resources, source_rows)
    seed_decision = ROOT/'docs/AUDITORY_NEXT_SEED_DECISION_v2.md'
    if seed_decision.is_file():
        (report/'SEED_REPLICATION_DECISION.md').write_text(seed_decision.read_text())
    synthetic_interpretation = ROOT/'docs/AUDITORY_NEXT_SYNTHETIC_INTERPRETATION_v2.md'
    if synthetic_interpretation.is_file():
        (report/'SYNTHETIC_INTERPRETATION.md').write_text(synthetic_interpretation.read_text())
    (report/'FIT_RECEIPT_ENRICHMENT.md').write_text(
        '逐模型补充回执只读取保存的训练与优化记录。原生字段、明确别名、计算派生、运行层继承和未知分列；'
        '不以任务名称替代feature scope hash，不以标签数组hash替代标签映射hash，不把作业资源记为逐fit资源。'
        '模型文件集合hash与最终模型hash的语义保持区别；更新前最后梯度不冒充更新后诊断。完整字段值与来源路径仅在private。\n\n'+
        markdown_table(enrichment, 'field attempted_units native_count alias_count derived_count inherited_count unknown_count'.split()))
    write_json(dest / "source_paths_and_hashes.json", reader.hashes)
    write_json(dest / "report_errors.json", reader.errors)
    write_json(dest / "resource_state_evidence.json", resource_state_evidence)
    write_json(dest / "report_binding.json", dict(config_hash=object_hash(config), registry_hash=object_hash(registry),
        source_roles={k: v[0] for k, v in SOURCES.items()}, source_status=source_rows, model_reads=0, new_head_fits=0,
        new_encoder_fits=0, new_bootstrap_fits=0, readonly_legacy=True))
    required_roles = [r for r in SOURCES if r not in ("tests_retained", "a2_residual_failed", "tests_supplement", "postflight_retained")]
    pending = [r for r in required_roles if not reader.sources[r].complete and reader.sources[r].execution not in TERMINAL_BLOCKED]
    state = "IN_PROGRESS" if pending else "REPORT_ASSEMBLY_ISSUES" if assembly_errors else "FIXED_SOURCE_REPORT_ASSEMBLED"
    summary = finish(dest, public, dict(status=state, delivery_status="REQUIRED_TABLES_AND_REPORTS_WRITTEN",
        round_complete=delivery_round_complete(reader.sources, assembly_errors),
        packets=len(PACKETS), pending_source_roles=pending, report_assembly_issues=assembly_errors,
        terminal_blocked_source_roles=[r for r in required_roles if reader.sources[r].execution in TERMINAL_BLOCKED],
        source_failures=[r for r in SOURCES if reader.sources[r].implementation in ("BUG", "NUMERICAL_FAILURE", "BUDGET_LIMITED")],
        scientifically_evaluable_packets=[r["packet"] for r in statuses if r["scientific_status"] != "NOT_EVALUABLE"],
        all_packages_scientifically_complete=all(r["control_status"] in ("COMPLETE", "NOT_APPLICABLE") and
            r["implementation_status"] == "PASS" and r["support_status"] != "BLOCKED_INPUT" for r in statuses),
        figures=figure_status, new_head_fits=0, new_encoder_fits=0, model_reads=0,
        uncertainty="fixed OOF candidate/record cluster bootstrap inherited; no pipeline refit",
        publication_scope="local aggregate research outputs; external release not authorized"))
    manifest = []
    for folder, prefix in ((public, "results"), (report, "reports")):
        for path in sorted(folder.iterdir()):
            if path.is_file() and path.name != "output_manifest.json":
                manifest.append(dict(logical_alias=prefix + "/" + path.name, sha256=digest(path), bytes=path.stat().st_size))
    write_json(public / "output_manifest.json", dict(status="MANIFEST_WRITTEN", files=manifest,
        excludes="this manifest's own hash to avoid self-reference", source_hashes_table="source_hashes.csv",
        public_audit="separate post-report scan required; not OCR or proof of anonymization"))
    return summary
