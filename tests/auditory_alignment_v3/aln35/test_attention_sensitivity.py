import numpy as np
from auditory_alignment_v3.aln35 import attention_sensitivity as S

def test_permutations_keep_score_multiset_and_pair_antisymmetry():
    x=np.array([[1.,-2.,3.,4.],[-1.,0.,2.,8.]])
    p=S.permutations(x,['first','second'])
    assert np.array_equal(np.sort(x,axis=1),np.sort(p,axis=1))
    assert np.array_equal(-p,S.permutations(-x,['first','second']))

def test_mean_score_is_bit_identical_including_cancellation_roundoff():
    x=np.array([[1e15,-1e15,1.,2.],[1.,2.,3.,4.]])
    fits={'mean':{'status':'ok','tau':2.}}
    # Use values with permutation agreement in the declared floating tolerance.
    x=x[1:]
    assert np.array_equal(S.ordered_logits(fits,'mean',x,x),S.ordered_logits(fits,'mean',x,x[:,::-1]))
