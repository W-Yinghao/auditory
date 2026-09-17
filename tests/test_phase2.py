import unittest
import numpy as np
from phase2_core import agreement_metrics, pair_summary, frontal_variant, balanced_selection, ridge_predict
from phase2_cohort import parse_vendor_start
from datetime import datetime


class Phase2Checks(unittest.TestCase):
    def test_perfect_order_with_large_offset_not_absolute_agreement(self):
        x=np.arange(20,dtype=float)
        equal=agreement_metrics(np.c_[x,x])
        shifted=agreement_metrics(np.c_[x,x+100])
        self.assertAlmostEqual(float(equal['icc_a1']),1.)
        self.assertAlmostEqual(float(shifted['pearson_r']),1.)
        self.assertLess(float(shifted['icc_a1']),.01)
        self.assertAlmostEqual(float(shifted['bias_b_minus_a_uv']),100.)

    def test_icc_expected_value_and_negative_not_clipped(self):
        # Independent manual ANOVA evaluation, n=4,k=2.
        x=np.array([[1,1],[2,3],[4,4],[5,6]],float)
        msr=2*np.sum((x.mean(1)-x.mean())**2)/3
        msc=4*np.sum((x.mean(0)-x.mean())**2)
        mse=np.sum((x-x.mean(1)[:,None]-x.mean(0)+x.mean())**2)/3
        expected=(msr-mse)/(msr+mse+.5*(msc-mse))
        self.assertAlmostEqual(float(agreement_metrics(x)['icc_a1']),expected)
        anti=np.array([[1,6],[2,4],[3,2],[4,1]],float)
        self.assertLess(float(agreement_metrics(anti)['icc_a1']),0.)
        self.assertTrue(np.isnan(agreement_metrics(np.ones((10,2)))['icc_a1']))

    def test_bootstrap_resamples_pairs(self):
        x=np.arange(15,dtype=float)
        s=pair_summary(np.c_[x,x+7],np.random.default_rng(9),200)
        self.assertAlmostEqual(s['bias_b_minus_a_uv_ci_low'],7.)
        self.assertAlmostEqual(s['bias_b_minus_a_uv_ci_high'],7.)

    def test_re_reference_matches_direct_raw_reference(self):
        channels=['Fp1','Fp2','Fz','Cz','Oz','O1','O2','Pz']
        rng=np.random.default_rng(11); raw=rng.normal(size=(9,8,40))
        common=rng.normal(size=(9,1,40))*100
        avg=raw-raw.mean(1,keepdims=True)
        roi,proxy=frontal_variant(avg,channels)
        expected=raw[:,[2,3]].mean(1)-raw[:,2:].mean(1)
        np.testing.assert_allclose(roi,expected,atol=1e-12)
        r2,p2=frontal_variant(raw+common,channels)
        np.testing.assert_allclose(roi,r2,atol=1e-12)
        np.testing.assert_allclose(proxy,p2,atol=1e-12)

    def test_balanced_selection_keeps_conditions_halves_and_qc(self):
        c=np.tile([1,1,1,2],30); b=np.arange(120)>64
        m=np.arange(120)%7!=0
        selected=balanced_selection(c,m,b,np.random.default_rng(2))
        self.assertTrue(np.all(selected<=m))
        for code in (1,2):
            self.assertEqual(np.sum(selected&(c==code)&b),np.sum(selected&(c==code)&~b))
            self.assertEqual(np.sum(selected&(c==code)&b),min(np.sum(m&(c==code)&b),np.sum(m&(c==code)&~b)))

    def test_ridge_train_only_scaling_and_unpenalized_intercept(self):
        train=np.arange(20,dtype=float)[:,None]; y=3+2*train[:,0]
        p=ridge_predict(train,y,np.array([[10.],[1e9]]))
        pfirst=ridge_predict(train,y,np.array([[10.]]))
        self.assertAlmostEqual(p[0],pfirst[0])
        np.testing.assert_allclose(ridge_predict(train,np.full(20,37.),train),37.)
        np.testing.assert_allclose(ridge_predict(train[:,:0],y,train[:3,:0]),y.mean())

    def test_vendor_time_only_requires_dated_vendor_field(self):
        dt,status=parse_vendor_start('08:15','2021-04-09')
        self.assertEqual(dt,datetime(2021,4,9,8,15))
        self.assertEqual(status,'parsed')
        self.assertIsNone(parse_vendor_start('08:15','')[0])
        self.assertIsNone(parse_vendor_start('25:15','2021-04-09')[0])

    def test_ridge_rejects_ambiguous_feature_shapes(self):
        with self.assertRaises(ValueError):
            ridge_predict(np.arange(5.),np.arange(5.),np.arange(2.))


if __name__=='__main__': unittest.main()
