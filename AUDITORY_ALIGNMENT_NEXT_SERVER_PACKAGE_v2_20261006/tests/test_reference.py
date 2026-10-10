from __future__ import annotations
import sys
import unittest
from pathlib import Path
import torch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from reference.temporal_and_selection import crop_windows,TimeTokenEncoder,two_stream_selection_loss,query_nll_bits,permuted_query_gain_identity


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(4)

    def test_half_open_crop(self):
        x=torch.arange(30,dtype=torch.float64).reshape(1,1,30)
        out=crop_windows(x,torch.tensor([10]),2,7)
        self.assertTrue(torch.equal(out.flatten(),torch.arange(12,17,dtype=torch.float64)))

    def test_missing_support_rejected(self):
        with self.assertRaises(ValueError):
            crop_windows(torch.zeros(1,2,20),torch.tensor([2]),-3,5)

    def test_outside_tensor_values_do_not_change_local_output(self):
        m=TimeTokenEncoder(2).double().eval()
        x=torch.randn(2,2,100,dtype=torch.float64)
        a=torch.tensor([20,40]); x2=x.clone()
        for i,aa in enumerate(a.tolist()):
            mask=torch.ones(100,dtype=torch.bool);mask[aa:aa+10]=False
            x2[i,:,mask]=500
        self.assertTrue(torch.allclose(m(crop_windows(x,a,0,10)),m(crop_windows(x2,a,0,10)),atol=0,rtol=0))

    def test_outside_input_gradient_zero(self):
        m=TimeTokenEncoder(2).double()
        x=torch.randn(1,2,100,dtype=torch.float64,requires_grad=True)
        m(crop_windows(x,torch.tensor([40]),0,15)).square().mean().backward()
        self.assertTrue(torch.equal(x.grad[:,:,:40],torch.zeros_like(x.grad[:,:,:40])))
        self.assertTrue(torch.equal(x.grad[:,:,55:],torch.zeros_like(x.grad[:,:,55:])))
        self.assertGreater(x.grad[:,:,40:55].abs().sum().item(),0)

    def test_token_time_axis_preserved(self):
        y=TimeTokenEncoder(3,output=7)(torch.randn(4,3,23))
        self.assertEqual(tuple(y.shape),(4,23,7))

    def test_candidate_swap_symmetry(self):
        s=torch.randn(9,2,dtype=torch.float64)
        y=torch.tensor([0,1,0,1,0,1,1,0,1])
        self.assertTrue(torch.allclose(two_stream_selection_loss(s,y,.4),two_stream_selection_loss(s.flip(1),1-y,.4),atol=1e-12,rtol=1e-12))

    def test_selection_gradient_finite(self):
        s=torch.randn(10,2,dtype=torch.float64,requires_grad=True)
        two_stream_selection_loss(s,torch.arange(10)%2).backward()
        self.assertTrue(torch.isfinite(s.grad).all())
        self.assertGreater(s.grad.abs().sum().item(),0)

    def test_gain_identity(self):
        s=torch.randn(17,11,dtype=torch.float64)
        y=torch.arange(17)%11;perm=torch.randperm(17)
        a,b=permuted_query_gain_identity(s,y,perm,.7)
        self.assertAlmostEqual(a.item(),b.item(),places=12)

    def test_uniform_risk(self):
        nll=query_nll_bits(torch.zeros(4,8,dtype=torch.float64),torch.arange(4))
        self.assertTrue(torch.allclose(nll,torch.full((4,),3.,dtype=torch.float64)))

    def test_negative_gain_is_not_clipped(self):
        s=torch.tensor([[0.,3.],[3.,0.]],dtype=torch.float64)
        gain,_=permuted_query_gain_identity(s,torch.tensor([0,1]),torch.tensor([1,0]))
        self.assertLess(gain.item(),0)


if __name__=='__main__':
    unittest.main()
