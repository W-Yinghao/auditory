import torch
from auditory_alignment_v3.aln34 import prior_private_loo as P


def test_strict_full_state_rebuild_restores_donor_seen_channels():
    names=P.C.PRIVATE_LAYOUT
    source=P.M.build_shared(names,list(P.M.VOCAB),8)
    restored=P.M.build_shared(names,names,92)
    restored.load_state_dict(source.state_dict(),strict=True)
    source.eval();restored.eval();x=torch.randn(2,len(names),P.C.L_IN)
    with torch.no_grad():torch.testing.assert_close(source(x),restored(x),rtol=0,atol=0)
    assert torch.equal(source.spatial.seen,restored.spatial.seen)


def test_process_bindings_restore_after_failure(tmp_path,monkeypatch):
    from auditory_alignment import data
    old=(P.core.OUT,P.L.BASE,P.L.PLAN,P.L.rebuild,data.load_private)
    try:
        with P.bindings(tmp_path/'source',tmp_path/'eval',tmp_path/'scores'):
            assert P.L.rebuild is P.rebuild
            raise RuntimeError('fixture')
    except RuntimeError:pass
    assert (P.core.OUT,P.L.BASE,P.L.PLAN,P.L.rebuild,data.load_private)==old
