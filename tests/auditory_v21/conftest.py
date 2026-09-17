"""Count and bound synthetic fitting calls, including failed calls."""
import json
import os
from pathlib import Path

COUNTS={'head_attempts':0,'head_completed':0,'temperature_calls':0,'transform_calls':0}


def pytest_sessionstart(session):
    from auditory_v21 import estimator
    fit=estimator.fit_head
    def counted(*args,**kwargs):
        limit=int(os.environ.get('AUDITORY_V21_TEST_MAX_FITS','39'))
        if COUNTS['head_attempts']>=limit:raise RuntimeError('FROZEN_TEST_FIT_BUDGET_EXCEEDED')
        COUNTS['head_attempts']+=1
        result=fit(*args,**kwargs);COUNTS['head_completed']+=1
        return result
    estimator.fit_head=counted
    calibrate=estimator.calibrate
    def count_cal(*args,**kwargs):
        COUNTS['temperature_calls']+=1
        return calibrate(*args,**kwargs)
    estimator.calibrate=count_cal
    transform=estimator.Transform.fit.__func__
    def count_transform(cls,*args,**kwargs):
        COUNTS['transform_calls']+=1
        return transform(cls,*args,**kwargs)
    estimator.Transform.fit=classmethod(count_transform)


def pytest_sessionfinish(session,exitstatus):
    target=os.environ.get('AUDITORY_V21_TEST_LEDGER')
    if target:Path(target).write_text(json.dumps(COUNTS,indent=2)+'\n')
