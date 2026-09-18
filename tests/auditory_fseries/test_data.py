import numpy as np
import pytest
from openpyxl import Workbook

from auditory_fseries.data import CANONICAL_CHANNELS, _read_workbook, _source_row_from_clinical_id, record_features


def _fixture(n=80):
    time = np.arange(176, dtype=float) / 250.0
    data = np.empty((n, 20, 176), dtype=np.float64)
    for i in range(n):
        for channel in range(20):
            data[i, channel] = (channel + 1) * np.sin(2 * np.pi * (2 + i / n) * time)
    accepted = np.zeros((n, 3), dtype=bool)
    accepted[:, 0] = True
    codes = np.where(np.arange(n) % 2, 1, 2)
    samples = np.arange(n, dtype=np.int64) * 700
    return data, time, accepted, codes, samples


def test_record_features_has_frozen_shapes_and_deterministic_uniform_selection():
    data, times, accepted, codes, samples = _fixture()
    first = record_features(data, times, accepted, codes, samples, {"duration_s": 12.0})
    second = record_features(data, times, accepted, codes, samples, {"duration_s": 12.0})

    assert first["Z"].shape == (60,)
    assert first["Q"].shape == (4,)
    assert len(first["selected_indices"]) == 80
    np.testing.assert_array_equal(first["selected_indices"], second["selected_indices"])
    np.testing.assert_allclose(first["Z"], second["Z"])
    np.testing.assert_allclose(first["Q"], second["Q"])


def test_selection_and_features_do_not_depend_on_event_code_labels():
    data, times, accepted, codes, samples = _fixture(300)
    reference = record_features(data, times, accepted, codes, samples, {"duration_s": 12.0})
    changed = record_features(data, times, accepted, 3 - codes, samples, {"duration_s": 12.0})

    np.testing.assert_array_equal(reference["selected_indices"], changed["selected_indices"])
    np.testing.assert_allclose(reference["Z"], changed["Z"])
    np.testing.assert_allclose(reference["Q"], changed["Q"])
    assert reference["accepted_count"] == changed["accepted_count"] == 300


def test_selection_uses_sample_then_event_ordinal_tie_break():
    data, times, accepted, codes, samples = _fixture(300)
    samples[:] = 100
    ordinal = np.arange(300, 0, -1)
    result = record_features(data, times, accepted, codes, samples, {"duration_s": 12.0, "ordinal": ordinal})
    assert np.all(np.diff(result["selected_indices"]) < 0)


def test_primary_mask_requires_literal_code_one_or_two_and_minimum_support():
    data, times, accepted, codes, samples = _fixture(80)
    accepted[:, 0] = False
    accepted[:63, 0] = True
    with pytest.raises(ValueError, match="fewer than 64"):
        record_features(data, times, accepted, codes, samples, {"duration_s": 12.0})


def test_nonfinite_accepted_data_is_a_hard_failure():
    data, times, accepted, codes, samples = _fixture()
    data[0, 0, 0] = np.nan
    with pytest.raises(ValueError, match="nonfinite selected epoch data"):
        record_features(data, times, accepted, codes, samples, {"duration_s": 12.0})


def test_canonical_channel_contract_is_explicit():
    assert len(CANONICAL_CHANNELS) == 20
    assert CANONICAL_CHANNELS[0] == "Fp1"
    assert CANONICAL_CHANNELS[-1] == "O2"


def test_workbook_merged_groups_and_missing_pta_are_preserved(tmp_path):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sheet1"
    headers = ["分组", "姓名", "实际月龄", "HA使用时长（月）", "MUSS得分（%）", "IT-MAIS/MAIS得分（%）"]
    headers += [f"{side}耳{freq}Hz({panel})" for panel in ("裸耳", "助听") for side in ("右", "左") for freq in (500, 1000, 2000, 4000)]
    sheet.append(headers)
    sheet.append(["HA", "a", 24, 5, 60, 70] + [10] * 16)
    sheet.append([None, "b", 30, 6, 70, 80] + ["NR"] * 16)
    sheet.append(["NH", "c", 36, 7, 80, 90] + [20] * 16)
    sheet.merge_cells("A2:A3")
    path = tmp_path / "ha.xlsx"
    workbook.save(path)

    rows, _ = _read_workbook(path)
    assert rows[2]["group"] == "HA"
    assert rows[3]["group"] == "HA"
    assert rows[4]["group"] == "NH"
    assert rows[2]["better_unaided_pta"] == 10.0
    assert rows[3]["better_unaided_pta"] is None
    assert rows[3]["better_aided_pta"] is None


def test_clinical_row_id_maps_without_an_off_by_one_adjustment():
    assert _source_row_from_clinical_id("C0091") == 91
    with pytest.raises(ValueError, match="C####"):
        _source_row_from_clinical_id("C91")
