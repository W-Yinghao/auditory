import numpy as np
import pandas as pd
import pytest
from auditory5.contracts import FitScope
from auditory5.routes.route_c import fit_paired_readouts,VIEWS,screen,summarize_losses

def test_c_linear_fallback_retains_all_five_paired_views_and_no_nonlinear_claim():
    rng=np.random.default_rng(42);groups=np.repeat(['a','b','c','d','e','f'],40)
    y=np.tile([0,1],120);left=rng.normal(size=(240,3));right=rng.normal(size=(240,3))
    models=fit_paired_readouts(left,right,y,groups,FitScope(tuple(np.unique(groups)),test_groups=('test',)),linear_only=True)
    assert set(models)=={('linear',v) for v in VIEWS}
    assert all(m.evidence['hidden_width']==0 for m in models.values())
    assert screen([],['nonlinear solver failure'])['status']=='NEED_CONTROLS'

def test_completed_linear_matrix_aggregates_only_when_explicitly_declared_partial():
    rows=[dict(representation='L0',family='linear',model=model,intervention='none',probability_mode='calibrated',
               split_group_id=g,ce_bits=.9+.01*i) for g in ['a','b','c','d'] for i,model in enumerate(VIEWS)]
    frame=pd.DataFrame(rows)
    gains,_=summarize_losses(frame,families=('linear',))
    assert gains and all(r['family']=='linear' for r in gains)
    with pytest.raises(ValueError,match='CAPACITY'):summarize_losses(frame)
