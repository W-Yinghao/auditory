import copy
import pytest
from auditory_alignment_v3.aln35 import episode_lineage_v2 as E


def fixture():
    parent={'source':{'id':'source'},'inner_train_ids':['a'],'inner_dev_ids':['b'],'outer_test_ids':['c']}
    source={'private_parent':parent}
    record={'row':parent['source'],'train_ids':['a'],'status':'complete','probe':False}
    return source,copy.deepcopy(parent),record


def test_compatible_source_allowed_without_new_identity():
    E.validate_legacy(*fixture())


def test_seen_inner_person_cannot_be_relabelled():
    source,parent,record=fixture();record['train_ids']=['a','b']
    with pytest.raises(AssertionError):E.validate_legacy(source,parent,record)


def test_changed_outer_ids_or_probe_rejected():
    source,parent,record=fixture();parent['outer_test_ids']=['x']
    with pytest.raises(AssertionError):E.validate_legacy(source,parent,record)
    source,parent,record=fixture();record['probe']=True
    with pytest.raises(AssertionError):E.validate_legacy(source,parent,record)


def test_process_local_substitution_restored_on_error():
    before=(E.E.BASE,E.E.PLAN,E.E.STORE,E.R.ready,E.R.private_bundle)
    with pytest.raises(RuntimeError):
        with E.execution_context():
            assert E.E.BASE==E.BASE
            raise RuntimeError('check cleanup')
    assert (E.E.BASE,E.E.PLAN,E.E.STORE,E.R.ready,E.R.private_bundle)==before
