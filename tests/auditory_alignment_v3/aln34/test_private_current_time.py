from types import SimpleNamespace
import numpy as np
import torch
from auditory_alignment_v3.aln34 import private_current_time as P


def test_whole_block_support_is_disjoint_with_same_query():
    k={'block':np.repeat(np.arange(10),7)}
    s1,q1=P.blocks(k,.1);s3,q3=P.blocks(k,.3)
    assert np.array_equal(q1,q3) and set(s1)<=set(s3) and not set(s3)&set(q3)
    assert len(s1)==7 and len(s3)==21 and len(q1)==49


def test_temporal_mask_uses_absolute_private_sample_coordinates():
    bt=SimpleNamespace(W=[(0,200)],lo=0);x=torch.ones(2,20,200)
    p=P.mask_patches([x],bt,(0,200))[0]
    assert p[:,:,:50].sum()==0 and p[:,:,50:100].min()==1 and p[:,:,100:].sum()==0
    bt=SimpleNamespace(W=[(0,100)],lo=50)
    p=P.mask_patches([x[:,:,:100]],bt,(200,400))[0]
    assert p[:,:,:50].sum()==0 and p[:,:,50:].min()==1


def test_zero_adaptation_returns_exact_query_and_never_reads_query_labels():
    u=np.random.default_rng(1).normal(size=(10,32)).astype('float32')
    q=np.arange(3,10);y=np.zeros(10)
    assert np.array_equal(P.adapt_output(u,y,np.arange(3),q,None,0,1),u[q])
