from auditory_alignment_v3.aln34 import private_cb_factorial_aggregate as A


def test_direct_factorial_interaction_has_declared_sign():
    vals={'random_full/pre_recipe':{'p':1.},'pretrained_full/pre_recipe':{'p':.8},
          'random_full/random_recipe':{'p':1.1},'pretrained_full/random_recipe':{'p':.7}}
    assert abs(-A.encoded_interaction(vals,'p')-.2)<1e-12


def test_rank_and_probability_interfaces_remain_separate():
    r={'row':{'spec':{'objective':'CS_SINGLE'}},'eval':{'per_participant':{'p':{'hist_gain_bits':.1,'hist_gain_twin_bits':.04}},
       'native_calibration':{'per_participant':{'p':{'positive_affine':{'nll_bits':.8,'auc_score':.7},'class_kernel':{'nll_bits':.9}}}}}}
    assert A.values(r,'affine_nll')=={'p':.8} and A.values(r,'native_nll')=={'p':.9}
    assert A.values(r,'score_auc')=={'p':-.7}
    assert abs(A.values(r,'twin_sensitivity')['p']+.06)<1e-12
