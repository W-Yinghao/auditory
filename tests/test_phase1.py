import unittest
import numpy as np
from phase1_core import epoch_grid, reference, baseline, block_bootstrap_scores, waveform_comparison, ear_reference_valid


class Phase1Checks(unittest.TestCase):
    def test_impulse_stays_at_event_zero_and_both_endpoints(self):
        offsets, decimate, times = epoch_grid(1000, -.2, .5, 4)
        self.assertEqual(len(offsets), 701)
        self.assertEqual(len(times), 176)
        signal = np.zeros(5000); signal[2345] = 1
        epoch = signal[2345+offsets][decimate]
        self.assertEqual(times[np.argmax(epoch)], 0)
        self.assertEqual(times[0], -.2); self.assertEqual(times[-1], .5)

    def test_baseline_does_not_include_trigger_sample(self):
        offsets, _, times = epoch_grid(1000, -.2, .5, 1)
        data = np.ones((2,len(times)))*7
        data[:,times==0] = 1007
        corrected = baseline(data,times,[-.2,0])
        np.testing.assert_array_equal(corrected[:,times<0],0)
        np.testing.assert_array_equal(corrected[:,times==0],1000)

    def test_reference_removes_shared_unknown_acquisition_reference(self):
        rng = np.random.default_rng(24)
        x = rng.normal(size=(6,500))
        common = rng.normal(size=500)*100
        a,b = reference(x,[0,1,2,3],[4,5])
        aa,bb = reference(x+common,[0,1,2,3],[4,5])
        np.testing.assert_allclose(a,aa,atol=1e-12)
        np.testing.assert_allclose(b,bb,atol=1e-12)
        np.testing.assert_allclose(a.mean(axis=0),0,atol=1e-12)

    def test_joint_block_resampling_preserves_paired_condition_offset(self):
        blocks = np.repeat(np.arange(10),20)
        codes = np.tile(np.repeat([1,2],10),10)
        score = (blocks.astype(float)*50 + (codes==2)*3)[:,None]
        boot = block_bootstrap_scores(score,codes,blocks,500,np.random.default_rng(42))
        np.testing.assert_allclose(boot[:,2,0],3,atol=1e-12)
        self.assertGreater(np.std(boot[:,0,0]),10)

    def test_block_bootstrap_constant_score_has_zero_error(self):
        codes = np.tile([1,2],40); blocks=np.repeat(np.arange(8),10)
        boot=block_bootstrap_scores(np.ones((80,2))*4,codes,blocks,500,np.random.default_rng(3))
        np.testing.assert_array_equal(boot[:,:2],4)
        np.testing.assert_array_equal(boot[:,2],0)

    def test_similarity_distinguishes_shape_from_amplitude(self):
        x=np.linspace(-1,1,100)
        r,rmse=waveform_comparison(x,2*x)
        self.assertAlmostEqual(r,1)
        self.assertGreater(rmse,.5)

    def test_reference_saturation_cannot_enter_matched_trial_comparison(self):
        self.assertFalse(ear_reference_valid([True,True],[False,True],False))
        self.assertTrue(ear_reference_valid([True,False],[False,True],False))
        self.assertFalse(ear_reference_valid([True,True],[False,False],True))


if __name__ == '__main__': unittest.main()
