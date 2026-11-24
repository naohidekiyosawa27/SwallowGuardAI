import csv
import json
from pathlib import Path
import tempfile
import unittest
import importlib.util
import numpy as np
from scipy.io import savemat
from swallowguard.contracts import Recording,Source,require_paired,research_output
from swallowguard.preprocess.signals import (bandpass,resample,emg_envelope,optical_features,
                                          TrainStandardizer,window_features)
from swallowguard.preprocess.timing import fit_clock,align_timestamps,frame_to_sample
from swallowguard.preprocess.quality import assess,QualityLimits
from swallowguard.preprocess.segmentation import labeled_windows
from swallowguard.train.splits import subject_split,assert_disjoint
from swallowguard.evaluate.metrics import binary_metrics,cluster_f1_ci
from swallowguard.export.int8 import quantize_input,checked_quantize_input
from swallowguard.adapters.d2 import load_csv
from swallowguard.adapters.d4 import load_clip

ROOT=Path(__file__).resolve().parents[1]


class Contracts(unittest.TestCase):
    def recording(self,subject='S1'):
        return Recording('fixture',subject,'session','recording',Source.SYNTHETIC,
                         200,np.arange(10)*5000,np.arange(10).reshape(-1,1),('x',))
    def test_recording_valid(self):self.recording().validate()
    def test_unpaired_rejected(self):
        with self.assertRaises(ValueError):require_paired([self.recording(),self.recording('S2')])
    def test_paired_allowed(self):require_paired([self.recording(),self.recording()])
    def test_no_m2(self):
        with self.assertRaises(ValueError):research_output(valid=True,model_stage='M2')
    def test_invalid_hides_probability(self):
        d=research_output(valid=False,event_probability=.9)
        self.assertIsNone(d['event_probability']);self.assertIsNone(d['clinical_risk'])
        self.assertFalse(d['swallowing_safety_clearance'])
    def test_probability_validation(self):
        with self.assertRaises(ValueError):research_output(valid=True,event_probability=float('nan'))


class DSP(unittest.TestCase):
    def setUp(self):
        self.t=np.arange(2000)/2000
        self.x=np.sin(2*np.pi*100*self.t)[:,None]
    def test_antialias_attenuation(self):
        x=np.sin(2*np.pi*800*self.t)[:,None]
        y=resample(x,2000,200)
        self.assertEqual(y.shape,(200,1));self.assertLess(np.sqrt(np.mean(y[20:-20]**2)),.02)
    def test_filter_rejects_nyquist(self):
        with self.assertRaises(ValueError):bandpass(self.x,2000,20,1000)
    def test_filter_attenuates_low_frequency(self):
        x=np.sin(2*np.pi*2*self.t)[:,None]
        self.assertLess(np.std(bandpass(x,2000,20,450)[500:]),.01)
    def test_envelope_shape(self):self.assertEqual(emg_envelope(self.x).shape,(200,1))
    def test_optical_calibration(self):
        y=optical_features(np.ones((10,2)),200,10)
        np.testing.assert_allclose(y[-1,:2],[.09,.09]);np.testing.assert_allclose(y[:,2:],2.)
    def test_missing_rejected(self):
        with self.assertRaises(ValueError):resample(np.array([[0.],[np.nan]]),100,50)
    def test_normalizer_train_only(self):
        with self.assertRaises(ValueError):TrainStandardizer().fit(self.x,partition='test')
    def test_normalizer_no_refit_on_test(self):
        n=TrainStandardizer().fit(np.array([[0.],[2.]]),partition='train')
        np.testing.assert_allclose(n.transform(np.array([[10.],[12.]])),[[9],[11]])
    def test_features(self):self.assertEqual(window_features(self.x).shape,(5,))
    def test_ambiguous_windows_skipped(self):
        x=np.ones((30,1));labels=np.array([2]*10+[1]*10+[0]*10)
        windows=list(labeled_windows(x,labels,length=10,hop=10))
        self.assertEqual([(w[0],w[2]) for w in windows],[(0,1),(20,0)])


class Timing(unittest.TestCase):
    def test_affine_clock(self):
        s=np.arange(6)*1e6;r=s*1.0001+2000
        c=fit_clock(s,r)
        self.assertAlmostEqual(c['skew_ppm'],100,places=5)
        np.testing.assert_allclose(align_timestamps(s,c),r,atol=1e-8)
    def test_delay_compensation(self):
        np.testing.assert_equal(align_timestamps([1,2],{'slope':1.,'offset_us':10},measured_filter_delay_us=3),[8,9])
    def test_duplicate_trigger_rejected(self):
        with self.assertRaises(ValueError):fit_clock([0,0,2],[0,1,2])
    def test_frame_mapping_origin(self):
        self.assertEqual(frame_to_sample(61,frame_origin=1),4000)
        self.assertEqual(frame_to_sample(60,frame_origin=0),4000)
    def test_origin_required(self):
        with self.assertRaises(TypeError):frame_to_sample(60)


class Quality(unittest.TestCase):
    def setUp(self):
        self.t=np.arange(100)*5000.;self.x=np.sin(np.arange(100))[:,None];self.limits=QualityLimits(2.)
    def q(self,**kwargs):return assess(self.t,self.x,200,self.limits,**kwargs)
    def test_good(self):self.assertTrue(self.q()['valid'])
    def test_gap(self):
        self.t[50:]+=10000;self.assertIn('gap',self.q()['reasons'])
    def test_clipping(self):
        self.x[0]=2;self.assertIn('clipping',self.q()['reasons'])
    def test_flatline(self):
        self.x[:]=0;self.assertIn('flatline',self.q()['reasons'])
    def test_nan(self):
        self.x[0]=np.nan;self.assertFalse(self.q()['valid'])
    def test_duplicate(self):
        self.t[1]=0;self.assertFalse(self.q()['valid'])
    def test_detached(self):self.assertFalse(self.q(sensor_attached=False)['valid'])
    def test_motion(self):self.assertFalse(self.q(motion_ok=False)['valid'])
    def test_tracking_loss(self):self.assertFalse(self.q(tracking_ok=False)['valid'])
    def test_sequence_gap(self):
        s=np.arange(100);s[50:]+=1;self.assertFalse(self.q(sequence=s)['valid'])
    def test_rate_drift(self):
        self.t*=1.1;self.assertIn('rate_error',self.q()['reasons'])


class SplitsMetrics(unittest.TestCase):
    def test_disjoint_subjects_all_sessions(self):
        s=np.repeat([f's{i}' for i in range(20)],4)
        split=subject_split(s);assert_disjoint(split)
        self.assertEqual(set(sum(split.values(),[])),set(s))
    def test_reproducible(self):self.assertEqual(subject_split(list('abcdefghij')),subject_split(list('abcdefghij')))
    def test_leakage_rejected(self):
        with self.assertRaises(ValueError):assert_disjoint({'train':['a'],'validation':['b'],'test':['a']})
    def test_insufficient_subjects(self):
        with self.assertRaises(ValueError):subject_split(['a','b'])
    def test_confusion_orientation(self):
        self.assertEqual(binary_metrics([0,0,1,1],[0,1,1,1])['confusion_matrix_true_rows_pred_columns'],[[1,1],[0,2]])
    def test_cluster_ci(self):
        d=cluster_f1_ci([0,1,0,1],[0,1,0,1],['a','a','b','b'],iterations=20)
        self.assertEqual(d['low'],1);self.assertEqual(d['high'],1)
    def test_single_subject_ci_unavailable(self):
        self.assertIsNone(cluster_f1_ci([0,1],[0,1],['a','a'],iterations=20)['low'])


class Adapters(unittest.TestCase):
    def test_d2_documented_fixture(self):
        path=ROOT/'tests/fixtures/P1_S1/recording.csv'
        r,y=load_csv(path,source='synthetic',all_channels_sample_rate_hz=2000,channel_rate_verified=True)
        self.assertEqual(r.subject_id,'P1');self.assertEqual(r.values.shape,(20,5));self.assertEqual(set(y),{0,1,2,3,4})
    def test_d2_timebase_guard(self):
        with self.assertRaises(ValueError):load_csv('unused',source='synthetic',all_channels_sample_rate_hz=2000,channel_rate_verified=False)
    def test_d4_synthetic_mat(self):
        row={'participant_id':'HSD001','session_id':'HSD001_S1','clip_id':'fixture','activity':'Fluid',
             'sampling_frequency_hz':'20000','n_samples':'40001','n_columns':'3'}
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'synthetic.mat';savemat(p,{'data':np.ones((40001,3)),
                'sampling_frequency_hz':20000,'participant_id':'HSD001','session_id':'HSD001_S1','activity':'Fluid'})
            r,y=load_clip(p,row,source=Source.SYNTHETIC)
            self.assertEqual(len(r.values),40001);self.assertEqual(y,1)
    def test_registry_restriction(self):
        registry=json.loads((ROOT/'datasets/registry.json').read_text())
        d=next(x for x in registry['datasets'] if x['id']=='D3')
        self.assertFalse(d['training_allowed']);self.assertEqual(d['access'],'restricted_internal')


class Quantization(unittest.TestCase):
    def test_quantization_saturates(self):
        np.testing.assert_equal(quantize_input(np.array([-100.,0,100.]),.1,-3),[-128,-3,127])
    def test_invalid_scale(self):
        with self.assertRaises(ValueError):quantize_input(np.array([1.]),0,0)
    def test_runtime_quantization_range_rejected(self):
        with self.assertRaises(ValueError):checked_quantize_input(np.array([100.]),.1,0)
    def test_runtime_quantization_in_range(self):
        np.testing.assert_equal(checked_quantize_input(np.array([0.,1.]),.1,0),[0,10])
    @unittest.skipUnless(importlib.util.find_spec('tensorflow'),'TensorFlow not installed: architecture/export unverified')
    def test_model_parameter_count(self):
        from swallowguard.train.models import m1_candidate
        self.assertEqual(m1_candidate().count_params(),4137)


class BaselineIntegration(unittest.TestCase):
    def test_synthetic_grouped_training(self):
        from swallowguard.train.baseline import run
        rng=np.random.default_rng(9);subjects=np.repeat([f'fixture_{i}' for i in range(20)],6)
        y=np.tile([0,1,0,1,0,1],20);x=rng.normal(size=(120,5))+y[:,None]*.2
        report=run(x,y,subjects,source='synthetic',dataset_id='fixture_only')
        self.assertTrue(report['synthetic_only']);assert_disjoint(report['split'])
        self.assertEqual(report['stage'],'M0');self.assertIn(report['selected'],report['validation'])


if __name__=='__main__':unittest.main()
