"""Objective checks and synthetic contract tests, always scheduled."""
import json
import subprocess
import sys
import ast
import os
from .provenance import ROOT, digest, write_json, finish


def run(config, registry, site, dest, public, report, source_run):
    from .readouts import objective_parity
    parity=objective_parity()
    write_json(public/'objective_parity.json',parity)
    for path in (dest/'source/auditory_next').glob('*.py'): ast.parse(path.read_text(),filename=str(path))
    env=os.environ.copy();env['AUDITORY_NEXT_TEST_FIT_LEDGER']=str(dest/'test_fit_counts.json')
    p=subprocess.run([sys.executable,'-m','pytest','tests/auditory_next','-q','--disable-warnings',
                      '--junitxml='+str(dest/'tests.xml')],cwd=dest/'source',text=True,capture_output=True,env=env)
    (dest/'pytest.log').write_text(p.stdout+p.stderr)
    if p.returncode: raise ValueError('CONTRACT_TEST_FAILURE_SEE_PRIVATE_LOG')
    import xml.etree.ElementTree as ET
    xml=ET.parse(dest/'tests.xml'); suite=xml.getroot().find('testsuite')
    counts={k:int(suite.attrib[k]) for k in ('tests','errors','failures','skipped')}
    (report/'OBJECTIVE_AND_CONTRACTS.md').write_text('# v2 implementation gates\n\nThe installed sklearn binary MLP objective is weighted mean BCE + alpha/(2 × sum weights) times the sum of squared weight matrices; biases are unpenalized. '
        'The replacement uses explicit L2 and Adam weight_decay=0. New-route lambda=0.001 has a separate, population-normalized meaning. '
        'Objective, logits, penalty and every gradient were compared at identical float64 parameters; a finite-difference check is also recorded. '
        'Passing numerical algebra does not establish convergence of any real-data head. Full required T01–T26 route integration remains a separate gate.\n')
    fits=json.loads((dest/'test_fit_counts.json').read_text())
    return finish(dest,public,dict(status='PASS',scope='implemented module tests and objective parity; not all route gates',
                                  objective_parity=parity,tests=counts,new_encoder_fits=0,synthetic_test_fits=fits,new_readout_fits=sum(fits.values())))


def run_module(config,registry,site,dest,public,report,module):
    """Focused reporting/accounting checks cannot become a full model gate."""
    if module not in ('resource_accounting','fit_accounting','receipt_enrichment','metrics_supplement','postflight','reporting','public_audit','synthetic_timeout_finalize','repair_support_report'):
        raise ValueError('MODULE_CHECK_ALLOWLIST')
    env=os.environ.copy();env['AUDITORY_NEXT_TEST_FIT_LEDGER']=str(dest/'test_fit_counts.json')
    target='tests/auditory_next/test_'+module+'.py'
    p=subprocess.run([sys.executable,'-m','pytest',target,'-q','--disable-warnings',
        '--junitxml='+str(dest/'tests.xml')],cwd=dest/'source',text=True,capture_output=True,env=env)
    (dest/'pytest.log').write_text(p.stdout+p.stderr)
    if p.returncode:raise ValueError('MODULE_TEST_FAILURE_SEE_PRIVATE_LOG')
    import xml.etree.ElementTree as ET
    suite=ET.parse(dest/'tests.xml').getroot().find('testsuite')
    fits=json.loads((dest/'test_fit_counts.json').read_text())
    return finish(dest,public,dict(status='MODULE_PASS',module=module,
        tests={k:int(suite.attrib[k]) for k in ('tests','errors','failures','skipped')},
        new_readout_fits=sum(fits.values()),synthetic_test_fits=fits,full_model_gate=False))
