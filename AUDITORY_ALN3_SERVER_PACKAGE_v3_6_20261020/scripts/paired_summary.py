#!/usr/bin/env python3
"""Identity-paired simultaneous intervals for already computed risk contrasts.

Input JSON: {families: [{family_id, unit, expected_people: {group:[ids]},
required_seeds:[3401], required_repeats:["0","1"],
contrasts:[{name,group}], rows:[{person_id,group,seed,repeat,contrast,value}]}]}.

Repeats and seeds are averaged within person, never counted as new subjects.
This is a fixed-original-SE max-|z*| interval, not bootstrap-t. Fit randomness
and complete-case omissions are not repaired by resampling.
"""
import argparse
import json
from pathlib import Path
import numpy as np


def summarize_family(family, B=4000, seed=361020):
    if B < 100:
        raise ValueError("bootstrap must have at least 100 replicates")
    expected = family["expected_people"]
    if any(len(v) != len(set(v)) for v in expected.values()):
        raise ValueError("duplicate expected person")
    flat = [person for values in expected.values() for person in values]
    if len(flat) != len(set(flat)):
        raise ValueError("a person cannot belong to two groups in one family")
    contrasts = family["contrasts"]
    names = [c["name"] for c in contrasts]
    if len(names) != len(set(names)) or any(c["group"] not in expected for c in contrasts):
        raise ValueError("contrast names must be unique and groups registered")
    seeds, repeats = family["required_seeds"], [str(v) for v in family["required_repeats"]]
    if not seeds or not repeats or len(set(seeds)) != len(seeds) or len(set(repeats)) != len(repeats):
        raise ValueError("required seeds/repeats must be unique nonempty lists")
    contrast_group = {c["name"]: c["group"] for c in contrasts}
    rows = {}
    for r in family["rows"]:
        c, g, p, s, t = r["contrast"], r["group"], r["person_id"], r["seed"], str(r["repeat"])
        if c not in contrast_group or contrast_group[c] != g or p not in expected[g] or s not in seeds or t not in repeats:
            raise ValueError("row outside registered contrast/group/person/seed/repeat")
        k = (c, g, p, s, t)
        if k in rows:
            raise ValueError("duplicate scientific observation")
        value = float(r["value"])
        if not np.isfinite(value):
            raise ValueError("nonfinite contrast: record missing status outside numeric rows")
        rows[k] = value
    rng = np.random.default_rng(seed)
    coverage, columns, bootstrap = {}, {}, {}
    incomplete = False
    for g, people in expected.items():
        member_names = [c["name"] for c in contrasts if c["group"] == g]
        if not member_names:
            raise ValueError("expected group has no registered contrast")
        complete = [p for p in people if all((c, g, p, s, t) in rows for c in member_names for s in seeds for t in repeats)]
        coverage[g] = {"expected_n": len(people), "complete_n": len(complete),
                       "missing_people": [p for p in people if p not in complete]}
        incomplete |= len(complete) != len(people)
        indices = rng.integers(0, len(complete), size=(B, len(complete))) if complete else None
        for c in member_names:
            values = np.array([np.mean([np.mean([rows[(c, g, p, s, t)] for t in repeats]) for s in seeds]) for p in complete])
            columns[c] = (complete, values)
            bootstrap[c] = values[indices].mean(1) if indices is not None else None
    stats, z = {}, []
    for c in names:
        ids, values = columns[c]
        estimate = float(values.mean()) if len(values) else None
        se = float(values.std(ddof=1) / np.sqrt(len(values))) if len(values) > 1 else None
        regular = se is not None and se > 1e-15
        stats[c] = {"name": c, "group": contrast_group[c], "n": len(values), "estimate": estimate,
                    "se": se, "status": "regular" if regular else "nonregular", "simultaneous_95": None,
                    "identity_values": dict(zip(ids, map(float, values)))}
        if regular:
            z.append(np.abs((bootstrap[c] - estimate) / se))
    critical = float(np.quantile(np.max(np.stack(z), axis=0), .95)) if z else None
    for stat in stats.values():
        if stat["status"] == "regular" and not incomplete:
            half = critical * stat["se"]
            stat["simultaneous_95"] = [stat["estimate"] - half, stat["estimate"] + half]
    status = "incomplete_no_intervals" if incomplete else "regular" if all(s["status"] == "regular" for s in stats.values()) else "partially_nonregular" if z else "nonregular"
    return {"family_id": family["family_id"], "unit": family["unit"], "status": status,
            "coverage": coverage, "required_seeds": seeds, "required_repeats": repeats,
            "method": "fixed_original_SE_max_abs_centered_bootstrap_z", "B": B, "seed": seed,
            "critical": critical, "conditional_on_fitted_models": True,
            "contrasts": [stats[c] for c in names]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--bootstrap", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=361020)
    a = ap.parse_args()
    data = json.loads(a.input.read_text())
    result = {"schema_version": "aln36.paired-summary.reference.v1",
              "families": [summarize_family(f, a.bootstrap, a.seed + i) for i, f in enumerate(data["families"])]}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(a.output.resolve()), "families": len(result["families"]),
                      "states": [f["status"] for f in result["families"]]}))


if __name__ == "__main__":
    main()
