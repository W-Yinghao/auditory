from auditory_v21.closure_audit import _has_calibration_receipt, _scope_check, ci_crosses_zero


def test_ci_crosses_zero_requires_a_finite_ordered_interval():
    assert ci_crosses_zero(-0.1, 0.2)
    assert ci_crosses_zero(0.0, 0.2)
    assert not ci_crosses_zero(0.1, 0.2)
    assert not ci_crosses_zero("missing", 0.2)


def test_scope_check_requires_disjoint_train_and_test_and_keeps_validation():
    good = _scope_check({
        "train_groups": ["a", "b"],
        "validation_groups": ["c"],
        "test_groups": ["d"],
        "scope_hash": "abc",
    })
    assert good["status"] == "PASS"
    assert good["train"] == 2
    assert good["validation"] == 1
    assert good["test"] == 1
    assert good["overlap"] == 0
    assert good["scope_hash"]

    overlap = _scope_check({
        "train_groups": ["a", "b"],
        "validation_groups": ["b"],
        "test_groups": ["d"],
        "scope_hash": "abc",
    })
    assert overlap["status"] == "INVALID"
    assert overlap["overlap"] == 1


def test_scope_check_does_not_treat_missing_test_as_complete():
    result = _scope_check({"train_groups": ["a"], "validation_groups": [], "scope_hash": "abc"})
    assert result["status"] == "INVALID"
    assert result["test"] == 0


def test_scope_check_rejects_string_group_containers():
    result = _scope_check({"train_groups": "a", "test_groups": ["b"]})
    assert result["status"] == "INVALID"


def test_scope_check_accepts_saved_fit_groups_alias_and_outer_hash():
    result = _scope_check({"fit_groups": ["a"], "validation_groups": [], "test_groups": ["b"]},
                          scope_hash="outer-hash")
    assert result["status"] == "PASS"
    assert result["scope_hash"]


def test_calibration_receipt_accepts_nested_post_pre_fit_scopes():
    receipt = {
        "post": {"temperature": 1.2, "fit_scopes": {
            "scope_hash": "post", "fit_groups": ["a"]}},
        "pre": {"temperature": 0.9, "fit_scopes": {
            "scope_hash": "pre", "fit_groups": ["a"]}},
    }
    assert _has_calibration_receipt(receipt)


def test_hash_item_retains_status_expected_and_actual(tmp_path):
    from auditory_v21.closure_audit import _check_one_hash
    path = tmp_path / 'artifact.txt'
    path.write_text('fixture')
    counters = dict(checked=0, matched=0, mismatched=0, unresolved=0)
    records = []
    _check_one_hash(tmp_path, 'run', 'input', 'artifact', 'old-hash', path, counters, records)
    assert counters['mismatched'] == 1
    assert records[0]['status'] == 'MISMATCH'
    assert records[0]['expected_sha256'] == 'old-hash'
    assert len(records[0]['actual_sha256']) == 64
