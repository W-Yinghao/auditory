from auditory_alignment_v3.aln34.private_episode_aggregate import observations


def test_metric_sign_is_benefit_and_undefined_auc_stays_missing():
    pp={'a':{'status':'complete','native':{'auc':.6,'nll_bits':.8}},
        'b':{'status':'complete','native':{'auc':None,'nll_bits':.9}},'c':{'status':'no_query'}}
    assert observations(pp,'native/auc',-1.)=={'a':-.6,'b':None}
    assert observations(pp,'native/nll_bits',1.)=={'a':.8,'b':.9}
