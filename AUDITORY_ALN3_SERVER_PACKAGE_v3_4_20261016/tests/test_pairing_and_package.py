from pathlib import Path
import copy, hashlib, json
import pytest
import yaml
from aln34_reference.pairing import audit_pairs

ROOT=Path(__file__).resolve().parents[1]
def row(role='base',seed=3401):
    return dict(record_id=f'{role}-{seed}',role=role,status='complete',dataset='fau',subject_fold=0,content_fold=0,
                seed=seed,split_hash='s',target_hash='t',access_contract='a',evaluation_version='e')

def test_pairs_only_same_contract():
    a=row();b=row('candidate');c=row('candidate',3407)
    out=audit_pairs([a,b,c],'base','candidate')
    assert out['n_pairs']==1 and out['n_missing']==1 and not out['outcomes_used_for_selection']

def test_different_targets_not_paired():
    a=row();b=row('candidate');b['target_hash']='another'
    out=audit_pairs([a,b],'base','candidate')
    assert out['n_pairs']==0 and out['n_missing']==2

def test_missing_metadata_not_silently_paired():
    a=row();del a['split_hash']
    with pytest.raises(ValueError):audit_pairs([a],'base','candidate')

def test_duplicates_rejected_not_selected_by_score():
    a=row();b=copy.deepcopy(a);b['record_id']='new';b['risk']=-100
    with pytest.raises(ValueError):audit_pairs([a,b],'base','candidate')

def test_incomplete_records_do_not_become_zero_effect():
    a=row();b=row('candidate');b['status']='running'
    out=audit_pairs([a,b],'base','candidate')
    assert out['n_pairs']==0 and out['n_missing']==1 and out['incomplete_rows_ignored']==1

def test_null_content_fold_allowed():
    a=row();b=row('candidate');a['content_fold']=b['content_fold']=None
    assert audit_pairs([a,b],'base','candidate')['n_pairs']==1

def test_metrics_cannot_change_pairing():
    a=row();b=row('candidate');p=audit_pairs([a,b],'base','candidate')
    a['risk']=100;b['risk']=-100;b['AUC']=0
    assert audit_pairs([a,b],'base','candidate')==p

def test_cards_distinct_no_perf_gates():
    cards=json.loads((ROOT/'plans/comparison_cards.json').read_text())
    assert len({c['id'] for c in cards})==len(cards)
    assert all(c['performance_entry_gate'] is None and not c['test_based_model_selection'] for c in cards)
    assert all(c['status']=='planned_intent_not_a_server_job' for c in cards)

def test_inherited_bytes_provenance():
    sources=json.loads((ROOT/'SOURCE_INDEX.json').read_text())
    for entry in sources['P33']['inherited_files']:
        assert hashlib.sha256((ROOT/entry['package_path']).read_bytes()).hexdigest()==entry['sha256']

def test_brief_byte_identity_hash():
    src=json.loads((ROOT/'SOURCE_INDEX.json').read_text())['B01']
    assert hashlib.sha256((ROOT/src['package_copy']).read_bytes()).hexdigest()==src['sha256']

def test_yaml_parses_and_public_prior_not_silently_changed():
    for p in (ROOT/'configs').glob('*.yaml'):assert isinstance(yaml.safe_load(p.read_text()),dict)
    old=yaml.safe_load((ROOT/'inherited/public_prior_v3_3.yaml').read_text())
    assert old['execution_contract']=='aln33_env64_125ms_v1'
    assert old['data_contract']['target_duration_ms']==125

def test_no_manuscript_gate_no_remote_claim():
    c=yaml.safe_load((ROOT/'configs/execution.yaml').read_text())
    assert not c['requires_manuscript_decisions'] and not c['requires_new_general_go']
    m=json.loads((ROOT/'PACKAGE_METADATA.json').read_text())
    assert not m['remote_actions_performed'] and not m['real_eeg_experiments_run']
