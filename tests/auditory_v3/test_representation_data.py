import pandas as pd
import pytest

from auditory_v3.representation_data import QuartetSupportError, quartet_support, sample_quartets


def _frame(groups=16):
    rows = []
    for g in range(groups):
        for cls in (0, 1):
            for j in range(2):
                rows.append({
                    "split_group_id": g, "A_half": 0, "record_id": "r",
                    "segment_id": "s", "previous_code": 1,
                    "previous_run_bin": 0, "class": cls,
                    "physical_block_id": f"{cls}-{j}",
                    "onset_s": g * 100 + cls * 20 + j * 11,
                    "trial_id": f"{g}-{cls}-{j}",
                })
    return pd.DataFrame(rows)


def test_support_and_fixed_exposure_plan():
    frame = _frame()
    support = quartet_support(frame)
    assert len(support) == 16 and support.quartet_eligible.all()
    plan = sample_quartets(frame, epochs=2)
    assert plan["steps_per_epoch"] == 1
    assert len(plan["exposure"]) == 2 * 16
    assert plan["batch_indices"].shape == (2, 1, 64)
    assert all(len(set(batch.tolist())) == 64 for batch in plan["batch_indices"].reshape(2, -1))


def test_unsupported_cell_is_not_silently_dropped():
    frame = _frame()
    frame.loc[frame["split_group_id"] == 0, "physical_block_id"] = "same"
    with pytest.raises(QuartetSupportError) as exc:
        sample_quartets(frame)
    assert not exc.value.support["quartet_eligible"].all()
