import json
import pytest
from auditory_v21.gates import require_test_gate


def make_receipts(tmp_path,monkeypatch):
    tested=tmp_path/'private/auditory_v21/test_fixture';tested.mkdir(parents=True)
    run=tmp_path/'new';run.mkdir()
    start={'source_hashes':{'auditory_v21/estimator.py':'known_source_hash'}}
    for path in (tested,run):(path/'start.json').write_text(json.dumps(start))
    (tested/'completion.json').write_text(json.dumps({'status':'PASS'}))
    (tested/'config.json').write_text(json.dumps({'algorithm':{'id':'fixed'}}))
    monkeypatch.setenv('AUDITORY_V21_TEST_RUN','test_fixture')
    return run


def test_changed_source_cannot_use_prior_tests(tmp_path,monkeypatch):
    run=make_receipts(tmp_path,monkeypatch)
    require_test_gate(tmp_path,run,{'algorithm':{'id':'fixed'}},match_algorithm=True)
    (run/'start.json').write_text(json.dumps({'source_hashes':{'auditory_v21/estimator.py':'changed'}}))
    with pytest.raises(ValueError,match='SOURCE_HASH_MISMATCH'):
        require_test_gate(tmp_path,run,{'algorithm':{'id':'fixed'}},match_algorithm=True)


def test_changed_algorithm_cannot_use_prior_tests(tmp_path,monkeypatch):
    run=make_receipts(tmp_path,monkeypatch)
    with pytest.raises(ValueError,match='ALGORITHM_CONFIG_MISMATCH'):
        require_test_gate(tmp_path,run,{'algorithm':{'id':'changed'}},match_algorithm=True)
