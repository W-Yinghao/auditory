from auditory_v21.real_execution import capability_gate
from auditory_v21.evaluation import CORE_SOURCES


def test_capability_receipt_binds_route_algorithm_inputs_and_sources():
    hashes={key:'frozen' for key in CORE_SOURCES};alg={'id':'fixture'}
    receipt=dict(capability_status='PASS',real_gate_open=True,packet='N1',mode='R_SIM',
        algorithm=alg,input_manifest_hash='manifest',source_hashes=hashes,unevaluable=0)
    assert capability_gate(receipt,hashes,alg,'manifest','N1','R_SIM')=='PASS'
    assert capability_gate(receipt,hashes,alg,'changed','N1','R_SIM')=='INPUT_MANIFEST_CHANGED'
    assert capability_gate(receipt,hashes,alg,'manifest','N3','R_SIM')=='CAPABILITY_SCOPE_MISMATCH'
    changed=dict(hashes);changed['auditory_v21/estimator.py']='different'
    assert capability_gate(receipt,changed,alg,'manifest','N1','R_SIM')=='CAPABILITY_SOURCE_CHANGED'
    receipt['unevaluable']=1
    assert capability_gate(receipt,hashes,alg,'manifest','N1','R_SIM')=='CAPABILITY_INCOMPLETE'


def test_development_completion_is_never_a_real_gate():
    assert capability_gate({'capability_status':'NOT_EVALUATED_INDEPENDENTLY'}, {}, {},'manifest','N1','R_SIM')=='CAPABILITY_NOT_PASS'
