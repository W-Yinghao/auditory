import numpy as np
from types import SimpleNamespace
from auditory_alignment_v3.aln34 import attention_transfer as T


def test_windows_do_not_cross_people_trials_roles_or_gaps():
    rows=[{'p':0,'code':'a','e0':i*10,'role':'fit'} for i in range(4)]
    rows += [{'p':0,'code':'a','e0':40,'role':'es'}, {'p':0,'code':'b','e0':50,'role':'fit'},
             {'p':1,'code':'a','e0':60,'role':'fit'}, {'p':0,'code':'a','e0':90,'role':'fit'}]
    out=T.windows(rows,10,20)
    assert len(out)==1 and [s['e0'] for s in out[0]]==[0,10,20,30]


def test_order_invariance_and_physical_window_counts():
    rng=np.random.default_rng(3);x=rng.normal(.1,.3,(200,4))
    fits={'mean':T.mean_fit(x),'antisymmetric':T.AO.fit_antisymmetric(x)}
    for name in T.INTEGRATORS:
        z=T.logits(fits,name,x);flip=T.logits(fits,name,-x)
        np.testing.assert_allclose(z,-flip,atol=1e-12)
        assert len(T.AO.order_credit(z,-z))==200
        np.testing.assert_allclose(T.AO.order_logloss_bits(z,-z),np.logaddexp(0,-z)/np.log(2))


def test_no_outer_metric_argument_in_selection_equal_person_weighting():
    candidates={'mean':{'a':{'nll_bits':.5,'n_windows':100},'b':{'nll_bits':1.5,'n_windows':1}},
                'antisymmetric':{'a':{'nll_bits':1.1,'n_windows':100},'b':{'nll_bits':1.1,'n_windows':1}}}
    selected,loss=T.select_integrator(candidates)
    assert selected=='mean' and loss['mean']==1.
    candidates['antisymmetric']=candidates['mean']
    assert T.select_integrator(candidates)[0]=='mean'


def test_zero_mean_scores_remain_ties_and_unavailable_fit_is_explicit():
    x=np.zeros((25,1));fits={'mean':T.mean_fit(x),'antisymmetric':T.AO.fit_antisymmetric(x)}
    z=T.logits(fits,'mean',x)
    assert np.all(T.AO.order_credit(z,-z)==.5)
    assert T.logits(fits,'antisymmetric',x) is None
    assert T.select_integrator({'mean':{'p':{'nll_bits':1.}},'antisymmetric':{}})[0]=='mean'
