import json
import pytest
from auditory_v21.fit_ledger import FitLedger


def test_failed_calls_are_persisted_and_consume_budget(tmp_path):
    path=tmp_path/'fits.jsonl';ledger=FitLedger(path,{'head':1})
    ledger.begin_world(0,{'head':1})
    ledger('start','head','base',{})
    ledger('failed','head','base',{'exception_type':'TestError'})
    with pytest.raises(RuntimeError,match='BUDGET_EXCEEDED'):
        ledger('start','head','retry',{})
    assert ledger.summary()['head']==dict(attempts=1,completed=0,failed=1)
    assert [json.loads(line)['event'] for line in path.read_text().splitlines()]==['start','failed']
    with pytest.raises(ValueError,match='INCOMPLETE'):ledger.complete_world()


def test_world_budget_and_completion_are_distinct_from_round_budget(tmp_path):
    ledger=FitLedger(tmp_path/'fits.jsonl',{'head':2})
    for world in (0,1):
        ledger.begin_world(world,{'head':1})
        ledger('start','head','base',{});ledger('completed','head','base',{})
        ledger.complete_world()
        with pytest.raises(RuntimeError,match='BUDGET_EXCEEDED'):ledger('start','head','extra',{})
    assert ledger.summary()['head']['completed']==2
