import numpy as np
import pytest
from auditory_v21.estimator import objective,weights,fit_pipeline,split_roles,validate_roles,validate_encoder_scope,choose,risk


def fixture():
    rng=np.random.default_rng(78);g=np.repeat(np.arange(60).astype(str),12);n=len(g)
    h=rng.normal(size=(n,4));p=rng.normal(size=(n,8));b=rng.normal(size=(n,8));noise=rng.normal(size=(n,8))
    y=np.tile([0,1]*6,60)
    roles=split_roles(g,np.arange(48).astype(str),np.arange(34,48).astype(str),np.arange(48,60).astype(str))
    return h,p,b,noise,y,g,roles


def test_weighted_objective_gradient_and_unpenalized_intercept():
    rng=np.random.default_rng(5);x=rng.normal(size=(20,3));y=np.arange(20)%2;g=np.repeat([0,1,2,3],5)
    theta=rng.normal(size=4);offset=rng.normal(size=20);w=weights(g)
    _,gradient=objective(theta,x,y,w,offset,.01)
    numeric=[]
    for i in range(4):
        step=np.eye(4)[i]*1e-6
        numeric.append((objective(theta+step,x,y,w,offset,.01)[0]-objective(theta-step,x,y,w,offset,.01)[0])/2e-6)
    np.testing.assert_allclose(gradient,numeric,atol=1e-8)


@pytest.mark.parametrize('packet,heads',[('N1',9),('N3',4)])
def test_exact_calibrated_baseline_candidates_and_expected_fit_count(packet,heads,tmp_path):
    from auditory_v21.fit_ledger import FitLedger
    limits=dict(head=heads,calibration=3 if packet=='N1' else 1,transform=7)
    ledger=FitLedger(tmp_path/'fit_events.jsonl',limits);ledger.begin_world(0,limits)
    data=fixture();out=fit_pipeline(*data[:6],data[6],packet=packet,maxiter=40,fit_observer=ledger)
    ledger.complete_world()
    assert ledger.summary()['head']['completed']==heads
    assert out['head_fits']==heads
    for name,fit in out['enhanced'].items():
        baseline=out['baseline']['H' if packet=='N3' else 'HP']
        assert np.array_equal(fit['candidate_test_logits'][0],baseline)
    if packet=='N1':
        np.testing.assert_array_equal(out['enhanced']['HPB']['candidate_test_logits'][1],out['baseline']['HB'])
        assert len({len(f['candidate_names']) for f in out['enhanced'].values()})==1


def test_test_labels_do_not_change_fit_calibration_or_selection():
    data=list(fixture());a=fit_pipeline(*data[:6],data[6],packet='N3',maxiter=30)
    data[4]=data[4].copy();data[4][data[6]['E']]=1-data[4][data[6]['E']]
    b=fit_pipeline(*data[:6],data[6],packet='N3',maxiter=30)
    for key in a['models']:np.testing.assert_array_equal(a['models'][key],b['models'][key])
    assert a['temperatures']==b['temperatures']
    for key in a['enhanced']:assert a['enhanced'][key]['selected']==b['enhanced'][key]['selected']


def test_test_features_do_not_change_any_fitted_parameter():
    data=list(fixture());a=fit_pipeline(*data[:6],data[6],packet='N1',maxiter=30)
    for i in range(4):
        data[i]=data[i].copy();data[i][data[6]['E']]+=13
    b=fit_pipeline(*data[:6],data[6],packet='N1',maxiter=30)
    for key in a['models']:np.testing.assert_array_equal(a['models'][key],b['models'][key])
    for key in a['enhanced']:assert a['enhanced'][key]['selected']==b['enhanced'][key]['selected']
    assert a['temperatures']==b['temperatures']


def test_group_role_overlap_is_rejected():
    *_,g,roles=fixture();roles['D']=roles['A']
    with pytest.raises(ValueError,match='ROLE_GROUP_OVERLAP'):validate_roles(g,roles)


def test_selection_tie_retains_first_baseline():
    z=np.array([-1.,1.]);selected,_=choose([('baseline',z),('duplicate',z)],[0,1],[1,2])
    assert selected==0


def test_group_weight_is_equal_despite_different_trial_counts():
    g=np.array([1,1,1,2]);w=weights(g)
    assert w[g==1].sum()==pytest.approx(w[g==2].sum())
    assert risk(np.zeros(4),np.array([0,0,1,1]),w)==pytest.approx(1.)


def test_omitted_role_rows_are_rejected():
    *_,g,roles=fixture();roles['A']=roles['A'][1:]
    with pytest.raises(ValueError,match='NOT_EXHAUSTIVE'):validate_roles(g,roles)


def test_encoder_must_exclude_calibration_residual_selection_and_test_groups():
    *_,g,roles=fixture()
    receipt=dict(verified_artifact_hashes=True,source_scope_hash='fixture',inner_fold=0,
                 encoder_fit_groups=list(set(g[roles['A']])),encoder_validation_groups=[str(i) for i in range(34,48)])
    validate_encoder_scope(g,roles,receipt)
    receipt['encoder_fit_groups'].append(g[roles['C']][0])
    with pytest.raises(ValueError,match='ENCODER_ROLE_LEAKAGE'):validate_encoder_scope(g,roles,receipt)


def test_stateless_features_require_proven_empty_encoder_and_scaler_scopes():
    *_,g,roles=fixture()
    receipt=dict(verified_artifact_hashes=True,source_scope_hash='fixture',encoder_fit_groups=[],
        scaler_train_groups=[],feature_generation_kind='STATELESS_FIXED_BINNING',stateless_source_verified=True)
    validate_encoder_scope(g,roles,receipt)
    receipt['scaler_train_groups']=[g[roles['B']][0]]
    with pytest.raises(ValueError,match='STATELESS_FEATURE_PROVENANCE_INVALID'):
        validate_encoder_scope(g,roles,receipt)
