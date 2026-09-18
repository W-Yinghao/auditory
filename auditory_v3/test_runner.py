"""Run only relevant tests, count actual fit attempts via the shared ledger."""
import contextlib
import json
import os
import xml.etree.ElementTree as ET
import pytest
from .linear import set_fit_ledger
from .runtime import Ledger,write_json


def run_tests(root,private,public,report,config,args):
    packet=args['packet']
    common=['test_linear.py','test_statistics.py','test_support.py']
    extra={'P0':['test_pca.py'], 'N2R':['test_bags.py','test_n2r_capability.py','test_n2r_execution.py'],
           'R3':['test_objectives.py','test_representation_data.py','test_train_contract.py','test_r3_evaluate.py','test_r3_execution.py','test_deterministic_pool.py']}[packet]
    set_fit_ledger(Ledger(private))
    with (private/'pytest.log').open('w') as f,contextlib.redirect_stdout(f),contextlib.redirect_stderr(f):
        status=pytest.main(['-q','--import-mode=importlib','-p','no:cacheprovider','--basetemp='+str(private/'tmp'),'--junitxml='+str(private/'tests.xml')]+['tests/auditory_v3/'+s for s in common+extra])
    tree=ET.parse(private/'tests.xml').getroot()
    counts={kind:len(tree.findall('.//'+kind)) for kind in ('testcase','failure','error','skipped')}
    attempts=[]
    if (private/'fit_events.jsonl').exists():attempts=[json.loads(line) for line in (private/'fit_events.jsonl').read_text().splitlines()]
    summary=dict(status='PASS' if status==0 and not any(counts[k] for k in ('failure','error','skipped')) else 'FAIL',packet=packet,tests=counts,head_attempts=sum(x['is_start'] and x['kind']=='head' for x in attempts),scope='synthetic contract tests, not real scientific capability',new_participant_model_fits=0)
    write_json(public/'test_receipt.json',summary)
    return summary
