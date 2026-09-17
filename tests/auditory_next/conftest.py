"""Count actual synthetic estimator fits during Slurm contract checks."""
import json
import os
from pathlib import Path

COUNTS={'logistic':0,'neural':0,'ridge':0}


def pytest_sessionstart(session):
    from sklearn.linear_model import LogisticRegression
    from auditory_next import readouts
    old=LogisticRegression.fit
    def counted(self,*args,**kwargs):
        COUNTS['logistic']+=1
        return old(self,*args,**kwargs)
    LogisticRegression.fit=counted
    advance=readouts.advance_fit
    def counted_advance(state,*args,**kwargs):
        if state.steps==0:COUNTS['neural']+=1
        return advance(state,*args,**kwargs)
    readouts.advance_fit=counted_advance
    from auditory_next import a2_residual_audit
    ridge=a2_residual_audit.fit_background
    def counted_ridge(*args,**kwargs):
        COUNTS['ridge']+=1
        return ridge(*args,**kwargs)
    a2_residual_audit.fit_background=counted_ridge


def pytest_sessionfinish(session,exitstatus):
    if os.environ.get('AUDITORY_NEXT_TEST_FIT_LEDGER'):
        Path(os.environ['AUDITORY_NEXT_TEST_FIT_LEDGER']).write_text(json.dumps(COUNTS))
