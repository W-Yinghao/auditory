from __future__ import annotations
import copy
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.make_plan import read_json,build_plan,summarize

class PlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.study=read_json(ROOT/'configs/study.json')
        cls.registry=read_json(ROOT/'configs/experiment_families.json')
        cls.rows=build_plan(cls.study,cls.registry)

    def test_complete_fold_seed_sets(self):
        expected={(f,s) for f in self.study['repeats']['subject_folds'] for s in self.study['repeats']['seeds']}
        for family in self.registry['families']:
            got={(r['subject_fold'],r['seed']) for r in self.rows if r['family_id']==family['family_id']}
            self.assertEqual(got,expected)

    def test_deterministic_unique_ids(self):
        self.assertEqual(self.rows,build_plan(self.study,self.registry))
        ids=[r['experiment_id'] for r in self.rows]
        self.assertEqual(len(ids),len(set(ids)))

    def test_no_scientific_gates(self):
        self.assertTrue(all(r['scientific_gate'] is None and r['status']=='planned' for r in self.rows))
        self.assertFalse(self.study['research_policy']['negative_result_led_story'])
        self.assertTrue(self.study['research_policy']['report_unfavorable_comparisons'])

    def test_finetuning_not_dependent_on_frozen_performance(self):
        for r in self.rows:
            if r['family_id']=='B_FM':
                self.assertNotIn('frozen_pass',r['technical_dependencies'])
                self.assertNotIn('score',','.join(r['technical_dependencies']))

    def test_stops_invalid_scientific_gate(self):
        reg=copy.deepcopy(self.registry)
        reg['families'][0]['scientific_gate']='AUC must exceed a cutoff'
        with self.assertRaises(ValueError):build_plan(self.study,reg)

    def test_missing_content_targets_not_fabricated(self):
        self.assertTrue(all(r['spec']['target']=='envelope' for r in self.rows if r['dataset']=='federici'))
        self.assertTrue(all(r['spec']['target']=='current_class' for r in self.rows if r['dataset']=='private_bdf'))

if __name__=='__main__':unittest.main()
