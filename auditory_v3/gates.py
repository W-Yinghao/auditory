"""Packet-specific source/receipt checks before any real data fit."""
import json
from pathlib import Path
from .runtime import safe_run

PACKET_SOURCES={
 'P0':['linear','statistics','pca_packet','p0_capability','data','splits','registry'],
 'N2R':['linear','statistics','bags_packet','n2r_execution','n2r_capability','data','splits','registry'],
 'R3':['linear','statistics','objectives','representation_data','train','deterministic_pool','evaluate','r3_execution','r3_training','data','splits','registry'],
}

def require_tests(root,private,test_run,packet):
    test=root/'private/auditory_v3'/safe_run(test_run)
    receipt=json.loads((test/'completion.json').read_text())
    if receipt.get('status')!='PASS' or receipt.get('packet')!=packet:raise ValueError('MATCHING_PACKET_TEST_GATE_REQUIRED')
    reference=json.loads((test/'start.json').read_text())
    now=json.loads((private/'start.json').read_text())
    if reference['config_sha256']!=now['config_sha256']:raise ValueError('TEST_CONFIG_MISMATCH')
    for module in PACKET_SOURCES[packet]:
        key='auditory_v3/'+module+'.py'
        if not reference['source_hashes'].get(key) or reference['source_hashes'][key]!=now['source_hashes'].get(key):raise ValueError('TEST_SOURCE_MISMATCH:'+key)
    if packet=='R3':
        key='auditory5/models/small_cnn.py'
        if not reference['source_hashes'].get(key) or reference['source_hashes'][key]!=now['source_hashes'].get(key):raise ValueError('TEST_CNN_SOURCE_MISMATCH')
    return receipt


def require_capability(root,private,run,packet,split_run):
    folder=root/'private/auditory_v3'/safe_run(run)
    receipt=json.loads((folder/'completion.json').read_text())
    if receipt.get('status')!='PASS' or receipt.get('packet')!=packet:raise ValueError('PACKET_CAPABILITY_NOT_PASS')
    require_tests(root,private,receipt['test_run'],packet)
    ref=json.loads((folder/'start.json').read_text())
    current=json.loads((private/'start.json').read_text())
    for module in PACKET_SOURCES[packet]:
        key='auditory_v3/'+module+'.py'
        if ref['source_hashes'].get(key)!=current['source_hashes'].get(key):raise ValueError('CAPABILITY_SOURCE_MISMATCH:'+key)
    if receipt['split_run']!=split_run:raise ValueError('CAPABILITY_SUPPORT_MISMATCH')
    if packet=='R3':
        key='auditory5/models/small_cnn.py'
        if not ref['source_hashes'].get(key) or ref['source_hashes'][key]!=current['source_hashes'].get(key):raise ValueError('CAPABILITY_CNN_SOURCE_MISMATCH')
    return receipt
