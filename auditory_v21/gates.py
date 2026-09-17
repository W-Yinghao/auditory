"""Fail closed unless the current source matches a successful Slurm test run."""
import json
import os
from .runtime import write_json,digest


def require_test_gate(root,private,config,match_algorithm=False):
    run=os.environ.get('AUDITORY_V21_TEST_RUN','')
    if not run or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in run):
        raise ValueError('EXPLICIT_TEST_RECEIPT_REQUIRED')
    tested=root/'private'/'auditory_v21'/run
    completion=json.loads((tested/'completion.json').read_text())
    if completion.get('status')!='PASS':raise ValueError('TEST_GATE_NOT_PASS')
    current=json.loads((private/'start.json').read_text())['source_hashes']
    reference=json.loads((tested/'start.json').read_text())['source_hashes']
    required=[p for p in current if p.endswith('.py') or p.endswith('ESTIMATOR_CONTRACT_DRAFT.md')]
    if not required or any(current[p]!=reference.get(p) for p in required):
        raise ValueError('TEST_SOURCE_HASH_MISMATCH')
    tested_config=json.loads((tested/'config.json').read_text())
    if match_algorithm and config.get('algorithm')!=tested_config.get('algorithm'):
        raise ValueError('TEST_ALGORITHM_CONFIG_MISMATCH')
    receipt=dict(status='PASS',test_run=run,test_receipt_hash=digest(tested/'completion.json'),
                 source_files_matched=len(required),algorithm_matched=match_algorithm)
    write_json(private/'test_gate.json',receipt)
    return receipt
