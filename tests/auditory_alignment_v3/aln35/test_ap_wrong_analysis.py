import copy
import pytest
from auditory_alignment_v3.aln35.ap_wrong_analysis import paired_differences, assert_common_query


def private_record(nll, auc, cell=0):
    return {"cell": {"subject_fold": 0, "content_fold": cell}, "view": {"sha": "same"},
            "normalisation_access": {"mode": "same"},
            "eval": {"per_participant": {"identity1": {"group": "HA", "n": 10}},
                     "native_calibration": {"per_participant": {"identity1": {
                         "positive_affine": {"nll_bits": nll, "auc_score": auc, "n": 10}}}}}}


def test_orientation_pairing_and_fold_collapse():
    cells = {(0, i): {"S": private_record(3+i, .5, i), "AP": private_record(1+i, .8, i),
                     "APwrong": private_record(4+i, .3, i)} for i in range(2)}
    values, cov = paired_differences(cells, "private_bdf")
    assert values["NLL"]["AP-S"] == {"identity1": 2.0}
    assert values["NLL"]["APwrong-S"] == {"identity1": -1.0}
    assert values["NLL"]["AP-APwrong"] == {"identity1": 3.0}
    assert values["AUC"]["AP-S"]["identity1"] == pytest.approx(.3)
    assert cov["identity_cell_counts"]["NLL"]["AP-S"] == {"identity1": 2}


def test_missing_arm_keeps_only_available_contrast_without_zero_fill():
    values, cov = paired_differences({(0, 0): {"S": private_record(3, .5), "AP": private_record(2, .6)}}, "private_bdf")
    assert values["NLL"]["AP-S"] == {"identity1": 1.}
    assert values["NLL"]["APwrong-S"] == {}
    assert len(cov["missing"]) == 2


def test_query_or_split_mismatch_refused_and_nonfinite_listed():
    ref = private_record(3, .5)
    bad = copy.deepcopy(ref); bad["eval"]["per_participant"]["identity1"]["n"] = 11
    with pytest.raises(ValueError, match="query counts"):
        assert_common_query(ref, bad, "private_bdf")
    bad = copy.deepcopy(ref); bad["cell"]["subject_fold"] = 1
    with pytest.raises(ValueError, match="split"):
        assert_common_query(ref, bad, "private_bdf")
    values, cov = paired_differences({(0, 0): {"S": ref, "AP": private_record(float("nan"), .6)}}, "private_bdf")
    assert not values["NLL"]["AP-S"]
    assert values["AUC"]["AP-S"]["identity1"] == pytest.approx(.1)
    assert cov["excluded"][0]["reason"] == "missing or nonfinite endpoint"
