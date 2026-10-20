import numpy as np
import pytest
from auditory_alignment_v3.aln35 import bridge_factor as F


def test_temperature_changes_probability_not_ranking():
    s = np.asarray([[.2, .4, -.8], [.6, .6, .1], [-.2, .3, .1]])
    own = np.asarray([1, 0, 2])
    a, b = F.query_metrics(s, own, 1.), F.query_metrics(s, own, .15)
    for key in ('top1', 'top5', 'mrr', 'rank_pct', 'mean_true_rank_1based'): assert a[key] == b[key]
    assert a['entropy_bits'] > b['entropy_bits']
    assert a['logloss_bits'] == pytest.approx(a['nll_bits_mean_check'])


def test_temperature_and_own_column_validation():
    s = np.asarray([[0., 1.]])
    with pytest.raises(AssertionError): F.query_metrics(s, np.asarray([1]), 0)
    with pytest.raises(AssertionError): F.query_metrics(s, np.asarray([2]), 1)


def test_complete_factor_selection_refuses_missing_fold():
    with pytest.raises(AssertionError): F.selected_rows([])
