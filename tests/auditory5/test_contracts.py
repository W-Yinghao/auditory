import unittest
import numpy as np
from auditory5.contracts import (FitScope,CandidateScaler,EEGTrainingView,check_direct_sample_overlap,
    require_shared_coordinates,validate_history_context,canonical_records)
from auditory5.manifest import IdentityGraph


class ContractTests(unittest.TestCase):
    def test_identity_component_disjoint(self):
        g=IdentityGraph();g.union('HA:a','CI:b','same_name');g.union('CI:b','CI:c','same_person_other_task')
        m=g.groups();self.assertEqual(len(set(m.values())),1)
        with self.assertRaises(ValueError):FitScope((m['HA:a'],),test_groups=(m['CI:c'],))
    def test_train_groups_only(self):
        s=FitScope(('a','b'),('c',),('d',))
        with self.assertRaises(ValueError):s.assert_fit_groups(['a','c'])
        with self.assertRaises(ValueError):s.assert_fit_groups(['d'])
    def test_test_eeg_and_label_mutation(self):
        rng=np.random.default_rng(1);train=[rng.normal(size=(3,2,8)),rng.normal(size=(30,2,8))]
        scope=FitScope(('a','b'),test_groups=('heldout',))
        a=CandidateScaler().fit(train,['a','b'],scope)
        test=rng.normal(size=(4,2,8));labels=np.array([0,1,0,1]);test[:]=1e9;labels[:]=1
        b=CandidateScaler().fit(train,['a','b'],scope)
        np.testing.assert_array_equal(a.center,b.center);np.testing.assert_array_equal(a.scale,b.scale)
        self.assertEqual(a.scope_hash,b.scope_hash)
    def test_candidate_scaler_not_trial_weighted(self):
        a=np.zeros((1,2,3));b=np.ones((100,2,3))*10
        s=CandidateScaler().fit([a,b],['a','b'],FitScope(('a','b')))
        np.testing.assert_allclose(s.center,[5,5]);np.testing.assert_allclose(s.scale,[5,5])
    def test_no_raw_overlap(self):
        check_direct_sample_overlap([('r','s',0,100)],[('r','s',100,200)])
        with self.assertRaises(ValueError):check_direct_sample_overlap([('r','s',0,100)],[('r','s',99,200)])
    def test_no_fold_embedding_concat(self):
        with self.assertRaises(ValueError):require_shared_coordinates(['fold1','fold2'])
    def test_no_clinical_to_ssl(self):
        v=EEGTrainingView(np.zeros((1,2,3)),[dict(stimulus_local_id=0,split_group_id='g',trial_id='t',MUSS=99,name='synthetic')])
        self.assertEqual(set(v[0]),{'X','stimulus_local_id','split_group_id','trial_id'})
    def test_history_target_not_feature(self):
        with self.assertRaises(ValueError):validate_history_context(['history_target','previous_run_length'])
    def test_canonical_only(self):
        rows=[dict(record_id='a',canonical_record_id='a'),dict(record_id='b',canonical_record_id='a')]
        self.assertEqual(len(canonical_records(rows)),1)


if __name__=='__main__':unittest.main()
