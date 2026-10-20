import copy
import pytest
from auditory_alignment_v3.aln35.ap_wrong_analysis_v2 import REF, make_specs, check_same_queries


def fixture_rows():
    expected = {f"dtu:p{i}": "NH" if i < 3 else "HI" for i in range(6)}
    ledger = {"expected": {ds: expected for ds in ("dtu", "fau", "private_bdf")},
              "required_folds": {ds: {pid: ["content_0", "content_1"] for pid in expected}
                                 for ds in ("dtu", "fau", "private_bdf")}}
    spec = make_specs(ledger)[0]
    rows = []
    for i, (identity, group) in enumerate(expected.items()):
        for fold in ("content_0", "content_1"):
            for arm, value in (("S", 4.), ("AP", 3. - i*.1), ("APwrong", 4.5 + i*.05)):
                rows.append({"dataset": "dtu", "identity": identity, "group": group, "stratum": group,
                    "fold": fold, "seed": 3401, "arm": arm, "window": "full", "metric": spec["metric"],
                    "unit": "bits/query", "value": value, "query_set_id": identity+fold, "analysis_role": "outer_test",
                    "provenance": {"query_ids": [identity+fold+":q1", identity+fold+":q2"], "support_ids": [],
                                   "population_fit_identities": ["source"], "selection_identities": ["source"], "outer_fold": "sf0"},
                    "metadata": {"candidate_order_sha256": "same", "candidate_ids": ["c0", "c1"]}})
    return rows, spec


def test_reference_fixed_se_complete_family_and_fold_average():
    rows, spec = fixture_rows()
    result = REF.analyze(rows, spec)
    assert result["coverage"]["all"]["common_complete_n"] == 6
    assert result["bootstrap"]["original_se_reestimated_per_draw"] is False
    assert result["not_legacy_bootstrap_t"]
    assert result["contrasts"][0]["estimate"] == pytest.approx(1.25)
    assert result["status"] == "regular"
    assert check_same_queries(rows)


def test_missing_one_content_arm_excludes_person_from_whole_family():
    rows, spec = fixture_rows()
    rows = [r for r in rows if not (r["identity"] == "dtu:p2" and r["fold"] == "content_1" and r["arm"] == "APwrong")]
    result = REF.analyze(rows, spec)
    assert result["coverage"]["all"]["common_complete_n"] == 5
    assert "dtu:p2" in result["coverage"]["all"]["excluded_incomplete"]
    assert all(c["groups"]["all"]["n"] == 5 for c in result["contrasts"])
    assert "dtu:p2" not in result["identity_values"]["all"]


def test_expected_people_cannot_be_inferred_from_observed_rows():
    rows, spec = fixture_rows()
    rows = [r for r in rows if r["identity"] != "dtu:p5"]
    result = REF.analyze(rows, spec)
    cover = result["coverage"]["all"]
    assert cover["expected_n"] == 6 and cover["common_complete_n"] == 5
    assert cover["missing_expected_identities"] == ["dtu:p5"]


def test_equal_counts_different_query_or_candidate_ids_rejected():
    rows, _ = fixture_rows()
    bad = copy.deepcopy(rows)
    bad[1]["provenance"]["query_ids"][0] += ":wrong"
    with pytest.raises(ValueError, match="query/candidate IDs"):
        check_same_queries(bad)
    with pytest.raises(REF.ReferenceError, match="query IDs"):
        REF.validate_rows(bad)
    bad = copy.deepcopy(rows)
    bad[1]["metadata"]["candidate_ids"].reverse()
    with pytest.raises(ValueError, match="query/candidate IDs"):
        check_same_queries(bad)


def test_zero_empirical_variance_is_nonregular_not_equivalence():
    rows, spec = fixture_rows()
    for row in rows:
        if row["arm"] == "AP":
            row["value"] = 3.
    result = REF.analyze(rows, spec)
    contrast = result["contrasts"][0]
    assert contrast["estimate"] == 1.
    assert contrast["status"] == "nonregular" and contrast["simultaneous_ci"] is None
