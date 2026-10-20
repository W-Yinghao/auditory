"""Explicit paired identity contrasts and fixed-original-SE max-|z*| bands.

Standard library only. No fitting, data discovery, subprocesses, network, or writes.
"""

from __future__ import annotations

import json
import math
import random
from collections import defaultdict
from pathlib import Path


class ReferenceError(ValueError):
    """The supplied data or analysis contract cannot be used as declared."""


ROW_REQUIRED = {
    "dataset", "identity", "group", "fold", "seed", "arm", "window", "metric",
    "unit", "value", "query_set_id", "analysis_role",
}
ROW_OPTIONAL = {"stratum", "provenance", "metadata"}
PROVENANCE_FIELDS = {
    "query_ids", "support_ids", "population_fit_identities", "selection_identities",
    "outer_fold", "source_record", "source_sha256", "aggregation_note",
    "source_fold_ids", "source_seed_ids",
}
ID_LIST_FIELDS = {
    "query_ids", "support_ids", "population_fit_identities", "selection_identities",
    "source_fold_ids",
}


def _string(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ReferenceError(f"{name} must be a nonempty string")
    return value


def _finite(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ReferenceError(f"{name} must be a finite number, not a boolean")
    return float(value)


def _unique(values, name, kind=str, allow_empty=False):
    if not isinstance(values, list) or (not values and not allow_empty):
        raise ReferenceError(f"{name} must be a {'possibly empty ' if allow_empty else 'nonempty '}list")
    for value in values:
        if kind is str:
            _string(value, name)
        elif type(value) is not int or value < 0:
            raise ReferenceError(f"{name} must contain nonnegative integer seeds")
    if len(values) != len(set(values)):
        raise ReferenceError(f"{name} contains duplicate entries")
    return values


def _json_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ReferenceError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def parse_json(text):
    try:
        return json.loads(text, object_pairs_hook=_json_no_duplicates,
                          parse_constant=lambda x: (_ for _ in ()).throw(ReferenceError(f"nonfinite JSON token: {x}")))
    except (json.JSONDecodeError, TypeError) as exc:
        raise ReferenceError(f"invalid JSON: {exc}") from exc


def load_rows(path):
    """Read JSONL; blank lines are ignored, duplicate rows are never averaged away."""
    rows = []
    with Path(path).open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if line.strip():
                try:
                    rows.append(parse_json(line))
                except ReferenceError as exc:
                    raise ReferenceError(f"line {number}: {exc}") from exc
    return rows


def validate_rows(rows):
    if not isinstance(rows, list) or not rows:
        raise ReferenceError("input must contain at least one normalized row")
    keys, membership, partitions, query_members = set(), {}, {}, {}
    audit = {"rows": len(rows), "rows_with_explicit_query_ids": 0,
             "rows_with_support_ids": 0, "rows_with_population_fit_ids": 0,
             "rows_with_selection_ids": 0, "provenance_limit":
             "Only supplied IDs are checked; a query_set_id label alone does not prove absence of leakage."}
    for index, row in enumerate(rows):
        label = f"row {index + 1}"
        if not isinstance(row, dict):
            raise ReferenceError(f"{label} is not an object")
        if ROW_REQUIRED - row.keys() or row.keys() - ROW_REQUIRED - ROW_OPTIONAL:
            raise ReferenceError(f"{label}: missing={sorted(ROW_REQUIRED - row.keys())}; "
                                 f"unknown={sorted(row.keys() - ROW_REQUIRED - ROW_OPTIONAL)}")
        for key in ROW_REQUIRED - {"seed", "value"}:
            _string(row[key], f"{label}.{key}")
        _finite(row["value"], f"{label}.value")
        if type(row["seed"]) is not int or row["seed"] < 0:
            raise ReferenceError(f"{label}.seed must be a nonnegative integer")
        if row["analysis_role"] not in {"outer_test", "inner_dev"}:
            raise ReferenceError(f"{label}: unsupported analysis_role")
        _string(row.get("stratum", "__all__"), f"{label}.stratum")
        if "metadata" in row and not isinstance(row["metadata"], dict):
            raise ReferenceError(f"{label}.metadata must be an object")
        person = (row["dataset"], row["identity"])
        member = (row["group"], row.get("stratum", "__all__"))
        if person in membership and membership[person] != member:
            raise ReferenceError(f"{label}: group/stratum changes for identity {row['identity']}")
        membership[person] = member
        key = tuple(row[x] for x in ("dataset", "identity", "fold", "seed", "arm", "window", "metric", "analysis_role"))
        if key in keys:
            raise ReferenceError(f"duplicate normalized row key: {key}")
        keys.add(key)
        prov = row.get("provenance", {})
        if not isinstance(prov, dict) or prov.keys() - PROVENANCE_FIELDS:
            raise ReferenceError(f"{label}: invalid provenance object or unknown provenance fields")
        for name in ID_LIST_FIELDS & prov.keys():
            _unique(prov[name], f"{label}.provenance.{name}", allow_empty=name != "query_ids")
        for name in {"outer_fold", "source_record", "source_sha256", "aggregation_note"} & prov.keys():
            _string(prov[name], f"{label}.provenance.{name}")
        if "source_sha256" in prov and (len(prov["source_sha256"]) != 64 or
                any(x not in "0123456789abcdef" for x in prov["source_sha256"])):
            raise ReferenceError(f"{label}: source_sha256 must be 64 lowercase hex characters")
        if "source_seed_ids" in prov:
            _unique(prov["source_seed_ids"], f"{label}.source_seed_ids", kind=int)
            if prov["source_seed_ids"] != [row["seed"]]:
                raise ReferenceError(f"{label}: a normalized row must not conceal an average across seeds")
        if row["fold"] == "reported_identity_mean":
            if not {"source_fold_ids", "source_seed_ids", "aggregation_note"} <= prov.keys() or not prov["source_fold_ids"]:
                raise ReferenceError(f"{label}: reported_identity_mean requires explicit source fold/seed provenance")
        if set(prov.get("query_ids", [])) & set(prov.get("support_ids", [])):
            raise ReferenceError(f"{label}: support/query ID overlap (leakage)")
        forbidden_sources = ["population_fit_identities"]
        if row["analysis_role"] == "outer_test":
            forbidden_sources.append("selection_identities")
        for source_name in forbidden_sources:
            if row["identity"] in prov.get(source_name, []):
                raise ReferenceError(f"{label}: evaluated identity occurs in {source_name} (leakage)")
        for field, counter in (("query_ids", "rows_with_explicit_query_ids"),
                               ("support_ids", "rows_with_support_ids"),
                               ("population_fit_identities", "rows_with_population_fit_ids"),
                               ("selection_identities", "rows_with_selection_ids")):
            audit[counter] += int(field in prov)
        # Subject fold is membership metadata, not a within-person replicate.
        part_key = (row["dataset"], row["identity"], row["fold"], row["seed"], row["analysis_role"])
        if "outer_fold" in prov:
            if part_key in partitions and partitions[part_key] != prov["outer_fold"]:
                raise ReferenceError(f"{label}: outer_fold differs across paired conditions")
            partitions[part_key] = prov["outer_fold"]
        if "query_ids" in prov:
            qkey = part_key + (row["query_set_id"],)
            query_set = frozenset(prov["query_ids"])
            if qkey in query_members and query_members[qkey] != query_set:
                raise ReferenceError(f"{label}: same query_set_id names different explicit query IDs")
            query_members[qkey] = query_set
    return audit


def validate_spec(spec):
    if not isinstance(spec, dict):
        raise ReferenceError("spec must be an object")
    required = {"family_id", "dataset", "metric", "unit", "required_seeds", "contrasts"}
    optional = {"required_folds", "required_folds_by_identity", "expected_identities", "group_sets",
                "bootstrap", "minimum_n", "analysis_role", "require_full_provenance", "description"}
    if required - spec.keys() or spec.keys() - required - optional:
        raise ReferenceError(f"spec missing={sorted(required - spec.keys())}; unknown={sorted(spec.keys() - required - optional)}")
    for key in ("family_id", "dataset", "metric", "unit"):
        _string(spec[key], f"spec.{key}")
    _unique(spec["required_seeds"], "required_seeds", kind=int)
    if "required_folds" in spec:
        _unique(spec["required_folds"], "required_folds")
    by_id = spec.get("required_folds_by_identity", {})
    if not isinstance(by_id, dict):
        raise ReferenceError("required_folds_by_identity must be an object")
    for identity, folds in by_id.items():
        _string(identity, "required_folds_by_identity key")
        _unique(folds, f"required_folds_by_identity.{identity}")
    if "required_folds" not in spec and not by_id:
        raise ReferenceError("explicit required_folds or required_folds_by_identity is required")
    minimum = spec.get("minimum_n", 3)
    if type(minimum) is not int or minimum < 3:
        raise ReferenceError("minimum_n must be an integer >= 3")
    if spec.get("analysis_role", "outer_test") not in {"outer_test", "inner_dev"}:
        raise ReferenceError("unsupported spec.analysis_role")
    if type(spec.get("require_full_provenance", False)) is not bool:
        raise ReferenceError("require_full_provenance must be boolean")
    boot = spec.get("bootstrap", {})
    if not isinstance(boot, dict) or boot.keys() - {"B", "seed", "alpha", "resampling"}:
        raise ReferenceError("invalid bootstrap settings")
    if boot.get("B", 4000) != 4000 or type(boot.get("B", 4000)) is not int:
        raise ReferenceError("this ALN3.5 exploratory reference fixes B=4000")
    if type(boot.get("seed", 351001)) is not int or boot.get("seed", 351001) < 0:
        raise ReferenceError("bootstrap seed must be a nonnegative integer")
    if boot.get("resampling", "independent") not in {"independent", "stratified"}:
        raise ReferenceError("resampling must be independent or stratified")
    alpha = _finite(boot.get("alpha", .05), "bootstrap.alpha")
    if not 0 < alpha < 1:
        raise ReferenceError("bootstrap.alpha must lie in (0,1)")
    contrasts = spec["contrasts"]
    if not isinstance(contrasts, list) or not contrasts:
        raise ReferenceError("contrasts must be a nonempty list")
    names, groups = set(), set()
    for contrast in contrasts:
        if not isinstance(contrast, dict) or not {"id", "terms"} <= contrast.keys() or contrast.keys() - {"id", "terms", "description"}:
            raise ReferenceError("each contrast must have id and terms, with optional description")
        name = _string(contrast["id"], "contrast.id")
        if name in names:
            raise ReferenceError(f"duplicate contrast id: {name}")
        names.add(name)
        if not isinstance(contrast["terms"], list) or not contrast["terms"]:
            raise ReferenceError(f"contrast {name} has no terms")
        seen = set()
        for term in contrast["terms"]:
            if not isinstance(term, dict) or set(term) != {"group", "arm", "window", "weight"}:
                raise ReferenceError(f"contrast {name}: term requires group,arm,window,weight")
            for key in ("group", "arm", "window"):
                _string(term[key], f"term.{key}")
            if _finite(term["weight"], "term.weight") == 0:
                raise ReferenceError("zero-weight terms must be omitted")
            key = (term["group"], term["arm"], term["window"])
            if key in seen:
                raise ReferenceError(f"contrast {name}: duplicate term {key}; combine weights explicitly")
            seen.add(key)
            groups.add(term["group"])
    sets = spec.get("group_sets", {})
    expected = spec.get("expected_identities", {})
    if not isinstance(sets, dict) or not isinstance(expected, dict):
        raise ReferenceError("group_sets and expected_identities must be objects")
    if sets.keys() - groups or expected.keys() - groups:
        raise ReferenceError("group_sets/expected_identities includes an unused analysis group")
    used_levels, used_people = set(), set()
    for group in sorted(groups):
        levels = _unique(sets.get(group, [group]), f"group_sets.{group}")
        if used_levels & set(levels):
            raise ReferenceError("analysis groups overlap: split pooled and subgroup contrasts into distinct families")
        used_levels.update(levels)
        if group in expected:
            ids = _unique(expected[group], f"expected_identities.{group}", allow_empty=True)
            if used_people & set(ids):
                raise ReferenceError("expected identities overlap between independent analysis groups")
            used_people.update(ids)
    return sorted(groups)


def _mean(values):
    value = math.fsum(values) / len(values)
    if not math.isfinite(value):
        raise ReferenceError("nonfinite arithmetic result; inspect metric scale")
    return value


def _variance(values):
    mean = _mean(values)
    value = math.fsum((x - mean) ** 2 for x in values) / (len(values) - 1)
    if not math.isfinite(value):
        raise ReferenceError("nonfinite variance; inspect metric scale")
    return value


def _quantile(values, q):
    values = sorted(values)
    pos = (len(values) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return values[lo] + (pos - lo) * (values[hi] - values[lo])


def analyze(rows, spec):
    """Compute one predeclared small family; never select a winning arm or time mask."""
    audit = validate_rows(rows)
    groups = validate_spec(spec)
    role = spec.get("analysis_role", "outer_test")
    selected = [r for r in rows if r["dataset"] == spec["dataset"] and
                r["metric"] == spec["metric"] and r["analysis_role"] == role]
    if any(r["unit"] != spec["unit"] for r in selected):
        raise ReferenceError("selected metric has inconsistent units")
    if spec.get("bootstrap", {}).get("resampling", "independent") == "stratified" and any("stratum" not in r for r in selected):
        raise ReferenceError("stratified resampling requires an explicit stratum on every selected row")
    by_person = defaultdict(dict)
    person_group, person_stratum = {}, {}
    for row in selected:
        identity = row["identity"]
        by_person[identity][(row["fold"], row["seed"], row["arm"], row["window"])] = row
        person_group[identity] = row["group"]
        person_stratum[identity] = row.get("stratum", "__all__")
    needed = {g: sorted({(t["arm"], t["window"]) for c in spec["contrasts"]
                        for t in c["terms"] if t["group"] == g}) for g in groups}
    panel, coverage = {}, {}
    for group in groups:
        levels = spec.get("group_sets", {}).get(group, [group])
        observed = sorted(i for i, g in person_group.items() if g in levels)
        supplied = group in spec.get("expected_identities", {})
        candidates = sorted(spec["expected_identities"][group]) if supplied else observed
        wrong = [i for i in candidates if i in person_group and person_group[i] not in levels]
        if wrong:
            raise ReferenceError(f"expected identities have conflicting observed group assignment: {wrong}")
        complete, excluded, values = [], {}, {}
        for identity in candidates:
            folds = spec.get("required_folds_by_identity", {}).get(identity, spec.get("required_folds"))
            if not folds:
                raise ReferenceError(f"no declared required folds for {identity}; do not infer them from observed rows")
            records, missing = by_person.get(identity, {}), []
            for seed in sorted(spec["required_seeds"]):
                for fold in sorted(folds):
                    paired = []
                    for arm, window in needed[group]:
                        record = records.get((fold, seed, arm, window))
                        if record is None:
                            missing.append({"fold": fold, "seed": seed, "arm": arm, "window": window})
                        else:
                            paired.append(record)
                    if len({r["query_set_id"] for r in paired}) > 1:
                        raise ReferenceError(f"{identity}/{fold}/{seed}: compared conditions use different query_set_id")
                    if spec.get("require_full_provenance", False):
                        for record in paired:
                            required = {"query_ids", "support_ids", "population_fit_identities", "selection_identities", "outer_fold"}
                            if not required <= record.get("provenance", {}).keys():
                                raise ReferenceError(f"{identity}: required explicit provenance is missing")
            if missing:
                excluded[identity] = {"reason": "missing_required_cells", "missing_cells": missing}
                continue
            vector = []
            for contrast in spec["contrasts"]:
                terms = [t for t in contrast["terms"] if t["group"] == group]
                if not terms:
                    vector.append(0.0)
                    continue
                seed_values = []
                for seed in sorted(spec["required_seeds"]):
                    fold_values = [math.fsum(t["weight"] * records[(f, seed, t["arm"], t["window"])]["value"]
                                             for t in terms) for f in sorted(folds)]
                    seed_values.append(_mean(fold_values))
                vector.append(_mean(seed_values))
            complete.append(identity)
            values[identity] = vector
        panel[group] = {"identities": complete, "vectors": values,
                        "strata": {i: person_stratum[i] for i in complete}}
        coverage[group] = {
            "row_group_levels": levels, "expected_status": "supplied" if supplied else "not_supplied",
            "expected_n": len(candidates) if supplied else None,
            "observed_n": len(observed), "common_complete_n": len(complete),
            "complete_identities": complete, "missing_expected_identities": sorted(set(candidates) - set(observed)) if supplied else None,
            "excluded_incomplete": excluded, "observed_outside_expected": sorted(set(observed) - set(candidates)) if supplied else [],
        }
    return _bootstrap(panel, coverage, spec, audit, len(selected))


def _bootstrap(panel, coverage, spec, audit, selected_rows):
    boot = spec.get("bootstrap", {})
    stratified = boot.get("resampling", "independent") == "stratified"
    minimum, alpha = spec.get("minimum_n", 3), boot.get("alpha", .05)
    group_names = sorted(panel)
    blocks = {}
    for group in group_names:
        block = defaultdict(list)
        for identity in panel[group]["identities"]:
            key = panel[group]["strata"][identity] if stratified else "__all__"
            block[key].append(panel[group]["vectors"][identity])
        blocks[group] = [block[key] for key in sorted(block)]
    result = []
    for k, contrast in enumerate(spec["contrasts"]):
        active = sorted({t["group"] for t in contrast["terms"]})
        means, component_variances, reasons, components = [], [], [], {}
        for group in active:
            n = len(panel[group]["identities"])
            vals = [v[k] for v in panel[group]["vectors"].values()]
            mean = _mean(vals) if vals else None
            if mean is not None:
                means.append(mean)
            if n < minimum:
                reasons.append(f"{group}: n={n} below minimum_n={minimum}")
            var_est = 0.0
            for index, block in enumerate(blocks[group]):
                block_vals = [v[k] for v in block]
                if len(block_vals) < 2:
                    reasons.append(f"{group}: resampling block {index} has fewer than 2 identities")
                    continue
                sample_variance = _variance(block_vals)
                if sample_variance == 0.0:
                    reasons.append(f"{group}: resampling block {index} has zero empirical contrast variance")
                var_est += (len(block) / n) ** 2 * sample_variance / len(block)
            if not vals or var_est == 0.0:
                reasons.append(f"{group}: no positive empirical sampling variance")
            component_variances.append(var_est)
            components[group] = {"n": n, "mean_contribution": mean,
                                 "estimated_variance_of_mean": var_est if n >= 2 else None,
                                 "resampling_block_sizes": [len(b) for b in blocks[group]]}
        estimate = math.fsum(means) if len(means) == len(active) else None
        se = math.sqrt(math.fsum(component_variances))
        if not math.isfinite(se) or (estimate is not None and not math.isfinite(estimate)):
            raise ReferenceError("nonfinite estimate or standard error")
        result.append({"id": contrast["id"], "description": contrast.get("description"),
                       "estimate": estimate, "original_se": se if se > 0 else None,
                       "status": "nonregular" if reasons else "regular",
                       "nonregular_reasons": sorted(set(reasons)), "simultaneous_ci": None,
                       "groups": components, "terms": contrast["terms"]})
    regular = [k for k, item in enumerate(result) if item["status"] == "regular"]
    critical = None
    if regular:
        rng = random.Random(boot.get("seed", 351001))
        maxima = []
        for _ in range(4000):
            sampled_means = {}
            for group in group_names:
                n = len(panel[group]["identities"])
                totals = [0.0] * len(result)
                if n:
                    for block in blocks[group]:
                        for _ in range(len(block)):
                            vector = block[rng.randrange(len(block))]
                            for k in regular:
                                totals[k] += vector[k] / n
                sampled_means[group] = totals
            maxima.append(max(abs(math.fsum(sampled_means[g][k] for g in group_names) - result[k]["estimate"])
                              / result[k]["original_se"] for k in regular))
        critical = _quantile(maxima, 1 - alpha)
        for k in regular:
            item = result[k]
            half = critical * item["original_se"]
            item["simultaneous_ci"] = [item["estimate"] - half, item["estimate"] + half]
    status = "regular" if len(regular) == len(result) else "nonregular" if not regular else "partially_nonregular"
    return {
        "schema_version": "aln35.reference-result.v1", "reference_only": True,
        "family_id": spec["family_id"], "dataset": spec["dataset"], "metric": spec["metric"],
        "unit": spec["unit"], "analysis_role": spec.get("analysis_role", "outer_test"),
        "estimand": "within-identity weighted condition contrast; equal fold mean, then equal seed mean, then identity mean per independent group",
        "selection": "none; all terms, required cells, groups, and family members are supplied in the spec",
        "method": "identity bootstrap with fixed original SE, max absolute centered z-star",
        "not_legacy_bootstrap_t": True,
        "bootstrap": {"B": 4000, "seed": boot.get("seed", 351001), "alpha": alpha,
                      "resampling": boot.get("resampling", "independent"), "quantile": "linear interpolation (type 7)",
                      "critical_value": critical, "original_se_reestimated_per_draw": False},
        "status": status, "simultaneous_scope": [result[k]["id"] for k in regular],
        "nonregular_warning": "No population equivalence or absence of information follows from zero empirical variance or a missing interval.",
        "coverage": coverage, "validation": dict(audit, selected_rows=selected_rows),
        "contrasts": result,
        "identity_values": {g: {i: {c["id"]: panel[g]["vectors"][i][k] for k, c in enumerate(spec["contrasts"])}
                                for i in panel[g]["identities"]} for g in group_names},
        "spec": spec,
    }
