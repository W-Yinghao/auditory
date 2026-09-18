import numpy as np
import pandas as pd
import pytest

from auditory_repair.pta import _complete, pta, source_row_from_clinical_id
from auditory5.splitting import balanced_component_folds


def test_source_row_key_uses_actual_four_digit_row():
    assert source_row_from_clinical_id("C0088") == 88
    assert source_row_from_clinical_id(" C0004 ") == 4
    with pytest.raises(ValueError):
        source_row_from_clinical_id("C88")


def test_pta_preserves_missingness_until_all_four_values_are_present():
    assert pta([10, 20, 30, 40]) == 25.0
    assert pta([10, "NR", 30, 40]) is None


def test_corrected_completeness_requires_finite_pta_and_old_contract_flags():
    row = {
        "pta_status": "linked_complete_unaided",
        "clinical_age_months": "120",
        "duration_months": "30",
        "better_unaided_pta": "40",
        "MUSS": "80",
        "strong_unique_link": "True",
        "eligible_measurement_identity_index": "True",
    }
    assert _complete(row)
    row["better_unaided_pta"] = ""
    assert not _complete(row)


def test_seeded_fold_reconstruction_is_deterministic_and_balances_groups():
    frame = pd.DataFrame(
        {
            "split_group_id": [f"g{i}" for i in range(10)],
            "general": [True] * 10,
            "A": [False] * 10,
            "B": [False] * 10,
            "C": [False] * 10,
            "D": [True] * 10,
        }
    )
    a = balanced_component_folds(frame, 5, 20260917)
    b = balanced_component_folds(frame, 5, 20260917)
    assert a == b
    assert sorted(pd.Series(list(a.values())).value_counts().tolist()) == [2, 2, 2, 2, 2]
