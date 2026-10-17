from types import SimpleNamespace
import numpy as np
import torch
from auditory_alignment_v3.aln34 import prior_science as Q

def test_masks_use_exact_64hz_onset_and_never_invent_pre_event():
    bt=SimpleNamespace(W=[(0,38)],lo=32)
    x=torch.ones(2,20,38)
    masks=[Q.mask64([x],bt,Q.WINDOWS[k])[0] for k in ('0_200','200_400','400_600')]
    assert [int(v[0,0].sum()) for v in masks]==[13,13,12]
    assert torch.equal(sum(masks),x)
    assert torch.equal(Q.mask64([x],bt,None)[0],x)
    assert 'pre' not in Q.WINDOWS

def test_public_absolute_start_access_inside_same_segment():
    offsets=Q.public_offsets()
    for ms in Q.T.CENTERS:
        indices=offsets+round(ms*64/1000)
        assert np.all(indices>=1) and np.all(indices+38<=320)
    assert round(-200*64/1000)+38>0

def test_science_process_bindings_restore_after_exception(tmp_path):
    from auditory_alignment import data
    previous=(Q.core.OUT,Q.P.BASE,Q.P.extract,Q.P.WINDOWS,data.load_private)
    try:
        with Q.bindings(tmp_path/'source',tmp_path/'dest'):
            assert Q.P.extract is Q.private_extract
            assert Q.P.WINDOWS is Q.WINDOWS
            raise RuntimeError('synthetic')
    except RuntimeError:pass
    assert (Q.core.OUT,Q.P.BASE,Q.P.extract,Q.P.WINDOWS,data.load_private)==previous

def test_paired_arm_contrasts_preserve_gain_and_loss_directions():
    from auditory_alignment_v3.aln34 import prior_science_aggregate as G
    panel=G.A.Panel()
    row={'dataset':'dtu','seed':3401,'subject_fold':0,'content_fold':0}
    population={str(i):{'group':'nh' if i<3 else 'hi'} for i in range(6)}
    gains={str(i):.01*(i+1) for i in range(6)}
    for slot in ('S','AP','XP','J*','XM'):
        for metric in ('r','mse'):
            sign=1 if metric=='r' else -1
            v={p:1+(sign*gains[p] if slot!='S' else 0) for p in population}
            panel.add('public/'+slot+'/NCE/model/env/direct','0/0',metric,row,population,v)
    results=G.matched_arms(panel,64)
    assert len(results)==2
    for r in results:
        assert r['paired_n']==6 and len(r['labels'])==4
        np.testing.assert_allclose(r['groups']['all']['est'],np.mean(list(gains.values())))
