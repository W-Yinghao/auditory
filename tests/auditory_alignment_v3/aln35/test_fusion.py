import numpy as np
from auditory_alignment_v3.aln35 import fusion_math as M

def test_selection_gives_each_person_equal_weight_and_no_outer_input():
    people=np.array(['a']+['b']*9);own=np.zeros(10,dtype=int)
    a=np.array([[.9,.1]]+[[.4,.6]]*9)
    b=np.array([[.3,.7]]+[[.6,.4]]*9)
    chosen,risks=M.select({'a':a,'b':b},own,people)
    assert chosen=='a'
    assert np.isclose(risks['a'],(-np.log2(.9)-np.log2(.4))/2)

def test_derangement_preserves_person_pool_and_vectors_without_labels():
    ids=['q0','q1','q2','r0','r1','singleton'];people=np.array(['a']*3+['b']*2+['c'])
    perm,cov=M.derangement(ids,people,351520,'es','same-pool')
    assert perm[-1]==-1 and not cov['c']['valid']
    assert all(i!=j and people[i]==people[j] for i,j in enumerate(perm[:-1]))
    assert set(perm[:3])=={0,1,2} and set(perm[3:5])=={3,4}
    assert np.array_equal(perm,M.derangement(ids,people,351520,'es','same-pool')[0])

def test_temperature_keeps_ranking_and_actual_mixture_includes_direct_endpoints():
    s=np.array([[2.,1.,-3.],[.1,3.,-2.]])
    p=M.probability(s);q=M.probability(-s)
    controls=M.candidate_sets(q,p,q)
    assert np.array_equal(controls['actual_mix'][0],p)
    assert np.array_equal(controls['actual_mix'][1],q)
    for t,value in controls['cb_temperature'].items():
        assert np.array_equal(np.argsort(-value,axis=1),np.argsort(-p,axis=1))
    selected,_=M.select({1:p,.5:p,2:p},np.array([0,1]),np.array(['a','b']))
    assert selected==1
