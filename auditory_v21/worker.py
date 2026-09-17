"""Worker dispatch; failure details stay private."""
import json
from pathlib import Path
import sys
import traceback
from .runtime import ROOT,require_slurm,write_json,finish


def main():
    require_slurm()
    command,private,public,report=sys.argv[1:]
    private,public,report=map(Path,(private,public,report))
    config=json.loads((private/'config.json').read_text())
    try:
        if command=='probe':
            from .probe import run
            result=run(ROOT,private,public,report,config)
        elif command=='stage0':
            from .gates import require_test_gate
            require_test_gate(ROOT,private,config)
            from .existing_review import run as existing
            from .n2_metadata_audit import run as n2
            existing_dir=private/'existing';existing_dir.mkdir(mode=0o700)
            n2_dir=private/'n2';n2_dir.mkdir(mode=0o700)
            result=dict(status='STAGE0_RECORDED',existing=existing(ROOT,existing_dir,public,report,config),
                        n2=n2(ROOT,n2_dir,public,report,config),new_head_fits=0,new_encoder_fits=0)
        elif command=='test':
            import subprocess,os,xml.etree.ElementTree as ET
            if 'tests' not in config:raise ValueError('EXPLICIT_SYNTHETIC_TEST_FIT_BUDGET_REQUIRED')
            env=dict(os.environ,AUDITORY_V21_TEST_LEDGER=str(private/'test_fit_counts.json'),
                     AUDITORY_V21_TEST_MAX_FITS=str(config['tests']['max_synthetic_head_calls']))
            checked=subprocess.run([sys.executable,'-m','pytest','tests/auditory_v21','-q','-p','no:cacheprovider',
                '--basetemp='+str(private/'tmp'),'--junitxml='+str(private/'tests.xml')],capture_output=True,text=True,env=env)
            (private/'pytest.log').write_text(checked.stdout+'\n'+checked.stderr)
            if checked.returncode:raise RuntimeError('TEST_FAILURE_SEE_PRIVATE_LOG')
            counts=json.loads((private/'test_fit_counts.json').read_text())
            if counts['head_attempts']!=config['tests']['expected_synthetic_head_calls'] or counts['head_completed']!=counts['head_attempts']:
                raise ValueError('EXACT_TEST_FIT_CATALOG_MISMATCH')
            tree=ET.parse(private/'tests.xml').getroot()
            result=dict(status='PASS',tests=len(tree.findall('.//testcase')),scope='synthetic module tests; not capability gate',
                        synthetic_test_fits=json.loads((private/'test_fit_counts.json').read_text()),new_participant_model_fits=0)
        elif command=='capability':
            from .gates import require_test_gate
            require_test_gate(ROOT,private,config,match_algorithm=True)
            from .capability import run
            result=run(ROOT,private,public,report,config)
        elif command=='input_preflight':
            from .input_preflight import run
            result=run(ROOT,private,public,report,config)
        elif command in ('n2_design','n2_inputs','closure','evaluation','real','finalize'):
            from .gates import require_test_gate
            require_test_gate(ROOT,private,config,match_algorithm=command in ('evaluation','real'))
            import importlib
            module={'n2_design':'n2_design','n2_inputs':'n2_experiment_inputs','closure':'closure_audit','evaluation':'evaluation','real':'real_execution','finalize':'finalize'}[command]
            result=importlib.import_module('auditory_v21.'+module).run(ROOT,private,public,report,config)
        else: raise ValueError('ESTIMATOR_NOT_FROZEN_REAL_GATE_CLOSED')
        finish(private,public,result)
    except Exception as e:
        (private/'traceback.txt').write_text(traceback.format_exc())
        write_json(private/'failure.json',dict(type=type(e).__name__,message=str(e)))
        write_json(public/'failure.json',dict(status='FAILED',exception_type=type(e).__name__,details='private'))
        raise SystemExit(1)


if __name__=='__main__':main()
