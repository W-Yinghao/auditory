import pytest
import torch
from aln3_reference.readouts import ChannelSpatialProjection, DenseQueryReadout, ZeroResidualPrediction, ChannelPhaseLinearReadout


def case():
    torch.manual_seed(41)
    return torch.randn(2, 4, 5, 8), torch.arange(5.)+.5, torch.linspace(.1, 4.7, 19)


def test_dense_shape_and_finite():
    h,p,q=case(); out=DenseQueryReadout(4,8,7,hidden=32)(h,p,q)
    assert out.shape==(2,19,7) and torch.isfinite(out).all()


def test_dense_batched_times():
    h,p,q=case(); model=DenseQueryReadout(4,8,7,hidden=32)
    torch.testing.assert_close(model(h,p,q),model(h,p.repeat(2,1),q.repeat(2,1)))


def test_dense_responds_to_channels():
    h,p,q=case(); model=DenseQueryReadout(4,8,7,hidden=32)
    h2=h.clone(); h2[:,0]+=2
    assert not torch.allclose(model(h,p,q),model(h2,p,q))


def test_channel_order_matters():
    h,_,_=case(); m=ChannelSpatialProjection(4,8,hidden=32)
    assert not torch.allclose(m(h),m(h[:,[1,0,2,3]]))


def test_signed_contrast_preserved():
    torch.manual_seed(1); m=ChannelSpatialProjection(2,3,hidden=4,spatial_filters=2,projected_dim=3)
    with torch.no_grad():
        m.spatial.copy_(torch.tensor([[1.,-1.],[.2,.4]]))
    s=torch.tensor([1.,2.,3.]).reshape(1,1,1,3)
    h=torch.cat([s,-s],1)
    assert torch.equal(h.mean(1),torch.zeros_like(h.mean(1)))
    assert not torch.allclose(m(h),m(torch.zeros_like(h)))


def test_invalid_channels_do_not_affect_output():
    h,p,q=case(); m=DenseQueryReadout(4,8,7,hidden=32)
    valid=torch.tensor([[True,True,True,False]]).repeat(2,1)
    h2=h.clone(); h2[:,3]+=100
    torch.testing.assert_close(m(h,p,q,valid_channels=valid),m(h2,p,q,valid_channels=valid))


def test_invalid_patch_mask():
    h,p,q=case(); m=DenseQueryReadout(4,8,7,hidden=32)
    with pytest.raises(ValueError): m(h,p,q,valid_patches=torch.zeros(2,5,dtype=torch.bool))


def test_masked_patch_no_gradient():
    h,p,q=case(); h.requires_grad_(); m=DenseQueryReadout(4,8,7,hidden=32)
    valid=torch.ones(2,5,dtype=torch.bool); valid[:,-1]=False
    m(h,p,q,valid_patches=valid).square().sum().backward()
    assert torch.count_nonzero(h.grad[:,:,-1])==0
    assert torch.count_nonzero(h.grad[:,:,:-1])>0


def test_wrong_shape_rejected():
    h,p,q=case()
    with pytest.raises(ValueError): DenseQueryReadout(5,8,7,hidden=32)(h,p,q)


def test_state_roundtrip():
    h,p,q=case(); a=DenseQueryReadout(4,8,7,hidden=32); b=DenseQueryReadout(4,8,7,hidden=32)
    b.load_state_dict(a.state_dict(),strict=True)
    torch.testing.assert_close(a(h,p,q),b(h,p,q))


def test_zero_residual_exact_initialization():
    torch.manual_seed(4); base=torch.randn(2,9,6); l=torch.randn(2,9,5); c=torch.randn(2,9,7)
    m=ZeroResidualPrediction(5,7,6)
    assert torch.equal(m(base,l,c),base)


def test_residual_gradient_and_learning():
    torch.manual_seed(4); base=torch.randn(2,9,6); l=torch.randn(2,9,5); c=torch.randn(2,9,7)
    m=ZeroResidualPrediction(5,7,6); optimizer=torch.optim.SGD(m.parameters(),lr=.1)
    m(base,l,c).square().mean().backward()
    assert torch.count_nonzero(m.residual[-1].weight.grad)>0
    optimizer.step(); optimizer.zero_grad()
    m(base,l,c).square().mean().backward()
    assert torch.count_nonzero(m.residual[0].weight.grad)>0


def test_residual_rejects_misaligned_queries():
    with pytest.raises(ValueError): ZeroResidualPrediction(5,7,6)(torch.zeros(2,9,6),torch.zeros(2,8,5),torch.zeros(2,9,7))


def test_phase_readout_shape():
    h,p,q=case(); out=ChannelPhaseLinearReadout(4,8,7)(h,p,q)
    assert out.shape==(2,19,7)


def test_phase_readout_is_affine_in_tokens():
    h,p,q=case(); g=torch.randn_like(h); m=ChannelPhaseLinearReadout(4,8,7)
    torch.testing.assert_close(m(.3*h+.7*g,p,q),.3*m(h,p,q)+.7*m(g,p,q),atol=1e-6,rtol=1e-5)
