import numpy as np
import pytest
from auditory_alignment_v3.aln35 import bridge_factor_analyze as A
from auditory_alignment_v3.prior33 import bridge as BR


def test_fast_score_is_original_unified_correlation():
    r = np.random.default_rng(88)
    U = r.normal(size=(5, 250, 32)).astype(np.float32)
    Y = r.normal(size=(9, 250, 8)).astype(np.float32)
    B = r.normal(size=(33, 8)); mu = np.arange(8) / 9.; sd = np.arange(8) + 1.
    old = BR.FrozenBridge('NCE', B, mu, sd, alpha_uni=.1).scores(U, np.empty(0), Y, 'unified')
    assert np.allclose(old, A.unified_scores(B, U, Y, mu, sd), rtol=1e-12, atol=1e-12)


def test_fixed_alpha_listener_fold_does_not_see_other_fold_targets():
    r = np.random.default_rng(77)
    X = r.normal(size=(48, 5)); Y = r.normal(size=(48, 3)); f = np.repeat([0, 1], 24)
    _, first = A.fixed_alpha_folds(X, Y, f, .3)
    changed = Y.copy(); changed[f == 1] += 100.
    _, second = A.fixed_alpha_folds(X, changed, f, .3)
    assert np.array_equal(first[0], second[0])
    assert not np.allclose(first[1], second[1])


def test_common_coverage_refuses_equal_counts_with_different_query_identity():
    rows = []
    for arm in ('AP', 'XM'):
        for bridge in ('B_donor', 'B_bridgecal'):
            for temperature_rule in ('fixed_one', 'source_fold_calibrated'):
                rows.append({'dataset': 'dtu', 'identity': 'fixture1', 'content_fold': 0,
                             'arm': arm, 'bridge': bridge, 'temperature_rule': temperature_rule,
                             'query_ids_sha256': 'fixture_same_real_ids', 'candidate_ids_sha256': 'fixture_candidates',
                             'true_candidates_sha256': 'fixture_own', 'n_queries': 3, 'n_candidates': 4})
    folds = [{'query_fold': f, 'query_ids_sha256': 'fixture_source' + str(f), 'by_pool_size': {}} for f in (0, 1)]
    entries = [{'query_results': rows, 'calibration': {'B_donor': {'folds': folds}, 'B_bridgecal': {'folds': folds}}}]
    assert A.verify_common_queries(entries)['status'] == 'PASS'
    rows[-1]['query_ids_sha256'] = 'fixture_different_real_ids'
    with pytest.raises(AssertionError, match='unpaired real queries'): A.verify_common_queries(entries)
