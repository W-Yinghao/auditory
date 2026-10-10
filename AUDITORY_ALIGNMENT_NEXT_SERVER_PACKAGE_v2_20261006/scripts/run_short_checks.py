#!/usr/bin/env python3
"""Run short local checks and write an actual receipt, never a real-EEG success claim."""
from __future__ import annotations
import io,json,platform,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import torch

def main():
    suite=unittest.TestLoader().discover(str(ROOT/'tests'),pattern='test_*.py')
    log=io.StringIO()
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    receipt={'scope':'Synthetic tensor/math and plan tests only; not real EEG training, clinical validation or Slurm execution.',
             'python':platform.python_version(),'torch':torch.__version__,'device':'cpu',
             'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'successful':result.wasSuccessful(),
             'log':log.getvalue()}
    out=ROOT/'receipts/SHORT_CHECKS.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(log.getvalue())
    print('Receipt:',out)
    raise SystemExit(0 if result.wasSuccessful() else 1)

if __name__=='__main__':main()
