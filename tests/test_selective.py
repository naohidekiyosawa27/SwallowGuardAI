import unittest
import numpy as np
from swallowguard.export.int8 import input_range,checked_quantize_input
from swallowguard.export.calibration import representative_indices
from swallowguard.evaluate.selective import range_acceptance,summarize,select_candidate


class NumericGate(unittest.TestCase):
    def test_bad_scale(self):
        for scale in [0.,-1.,float('nan'),float('inf')]:
            with self.subTest(scale=scale),self.assertRaises(ValueError):input_range(scale,0)
    def test_bad_zero_point(self):
        for z in [128,-129,.5,float('nan')]:
            with self.subTest(z=z),self.assertRaises(ValueError):input_range(.1,z)
    def test_boundary_and_nonfinite(self):
        x=np.array([[[-128.],[127.]],[[0.],[127.01]],[[0.],[np.nan]]])
        np.testing.assert_equal(range_acceptance(x,1.,0),[True,False,False])
    def test_zero_point_range(self):
        self.assertEqual(input_range(.5,-10),(-59.,68.5))
    def test_empty_rejected(self):
        with self.assertRaises(ValueError):range_acceptance(np.empty((1,0,1)),1.,0)
    def test_single_sample_nonfinite_rejected(self):
        with self.assertRaises(ValueError):checked_quantize_input(np.array([np.inf]),1.,0)


class CalibrationSelection(unittest.TestCase):
    def setUp(self):
        self.x=np.arange(120,dtype=float).reshape(20,3,2)
        self.s=np.repeat(['s1','s2'],10);self.y=np.tile([0,1],10)
    def test_training_only(self):
        with self.assertRaises(ValueError):representative_indices(self.x,self.s,self.y,partition='validation')
    def test_deterministic_unique_coverage(self):
        a=representative_indices(self.x,self.s,self.y,partition='train',limit=10)
        b=representative_indices(self.x,self.s,self.y,partition='train',limit=10)
        np.testing.assert_equal(a,b);self.assertEqual(len(a),10);self.assertEqual(len(set(a)),10)
        self.assertEqual(set(self.s[a]),set(self.s));self.assertEqual(set(self.y[a]),{0,1})
    def test_extrema_preserved(self):
        a=representative_indices(self.x,self.s,self.y,partition='train',limit=10)
        self.assertTrue({0,9,10,19}.issubset(set(a)))
    def test_insufficient_budget_rejected(self):
        with self.assertRaises(ValueError):representative_indices(self.x,self.s,self.y,partition='train',limit=1)


class SelectiveAccounting(unittest.TestCase):
    def test_abstention_remains_in_denominator(self):
        r=summarize([0,1,1,0],[.1,.9,.8,.2],[.1,.9,np.nan,np.nan],['a','a','b','b'],bootstrap=20)
        self.assertEqual(r['all_windows'],4);self.assertEqual(r['coverage'],.5)
        self.assertEqual(r['accepted_correct_fraction_of_all_windows'],.5)
        self.assertEqual(r['confusion_true_rows_pred_non_swallow_swallow_abstain'],[[1,0,1],[0,1,1]])
    def test_all_abstain(self):
        r=summarize([0,1],[.1,.9],[np.nan,np.nan],['a','b'],bootstrap=20)
        self.assertIsNone(r['accepted_int8_metrics']);self.assertEqual(r['coverage'],0)
    def test_invalid_probability(self):
        with self.assertRaises(ValueError):summarize([0],[.1],[np.inf],['a'])
    def test_selection_obeys_coverage_not_test(self):
        def item(coverage,error=.01):
            return {'model_bytes':5000,'calibration_count':256,'validation':{
                'coverage':coverage,'accepted_int8_metrics':{'f1':.8},'accepted_float_metrics':{'f1':.8},
                'max_probability_error_accepted':error,'p99_probability_error_accepted':.01,
                'threshold_agreement_accepted':1.}}
        candidates={'low_coverage':item(.9),'eligible':item(.99),'bad_parity':item(1.,.5)}
        self.assertEqual(select_candidate(candidates),'eligible')
    def test_none_selected_if_all_fail(self):
        self.assertIsNone(select_candidate({}))


class GroupedAblation(unittest.TestCase):
    def test_documented_feature_layout_required(self):
        from swallowguard.evaluate.grouped_ablation import evaluate
        with self.assertRaises(ValueError):evaluate(np.ones((12,14)),np.tile([0,1],6),np.repeat(['a','b','c'],4))
    def test_every_training_window_gets_one_grouped_oof_prediction(self):
        from swallowguard.evaluate.grouped_ablation import evaluate
        x=np.random.default_rng(2026).normal(size=(48,15))
        y=np.tile([0,1],24);s=np.repeat(['a','b','c','d','e','f'],8)
        result=evaluate(x,y,s,folds=3,bootstrap=20)
        self.assertEqual(len(result),6)
        for value in result.values():
            self.assertEqual(sum(f['test_windows'] for f in value['folds']),48)
            for fold in value['folds']:
                self.assertEqual(fold['training_participants']+fold['test_participants'],6)


if __name__=='__main__':unittest.main()
