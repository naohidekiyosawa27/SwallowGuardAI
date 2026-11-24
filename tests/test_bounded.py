import importlib.util
import unittest
import numpy as np
from swallowguard.preprocess.bounded import normalized_windows,BoundedFeatures


class BoundedRepresentations(unittest.TestCase):
    def setUp(self):self.x=np.random.default_rng(2026).normal(size=(8,100,3))
    def test_window_bound_without_mutating_raw(self):
        original=self.x.copy();result=normalized_windows(self.x)
        np.testing.assert_array_equal(self.x,original)
        self.assertTrue(np.isfinite(result).all());self.assertLessEqual(float(np.max(np.abs(result))),.900001)
    def test_window_gain_and_offset_invariance(self):
        np.testing.assert_allclose(normalized_windows(self.x),normalized_windows(self.x*50+100),atol=1e-6)
    def test_per_window_no_cross_recording_fit(self):
        one=normalized_windows(self.x[:1]);all_windows=normalized_windows(self.x)
        np.testing.assert_array_equal(one[0],all_windows[0])
    def test_flatline_rejected(self):
        with self.assertRaises(ValueError):normalized_windows(np.ones((1,100,3)))
    def test_nonfinite_rejected(self):
        self.x[0,0,0]=np.nan
        with self.assertRaises(ValueError):normalized_windows(self.x)
    def test_invalid_headroom(self):
        for value in [0.,1.,np.nan]:
            with self.subTest(value=value),self.assertRaises(ValueError):normalized_windows(self.x,headroom=value)
    def test_invalid_flatline_threshold(self):
        with self.assertRaises(ValueError):normalized_windows(self.x,minimum_peak=-1)
    def test_feature_training_partition_required(self):
        with self.assertRaises(ValueError):BoundedFeatures().fit(self.x[:,0,:],partition='test')
    def test_feature_bound_and_monotonicity(self):
        transform=BoundedFeatures().fit(np.array([[-1.],[1.]]),partition='train')
        values=transform.transform(np.array([[-10000.],[-1.],[0.],[1.],[10000.]]))
        self.assertTrue(np.all(np.diff(values.ravel())>0));self.assertLess(np.max(np.abs(values)),.9)
    def test_feature_manifest_reconstructs_transform(self):
        transform=BoundedFeatures().fit(self.x[:,0,:],partition='train');d=transform.manifest()
        z=(self.x[:,1,:]-np.asarray(d['mean']))/np.asarray(d['scale'])
        np.testing.assert_allclose(transform.transform(self.x[:,1,:]),d['headroom']*z/(1+np.abs(z)),atol=1e-7)


HAS_QAT=bool(importlib.util.find_spec('tensorflow_model_optimization') and importlib.util.find_spec('tf_keras'))


@unittest.skipUnless(HAS_QAT,'Isolated legacy-Keras QAT environment not installed')
class QATExport(unittest.TestCase):
    def test_shadow_copies_unquantized_trained_weights(self):
        import tensorflow as tf
        from swallowguard.train.qat_models import bounded_m0,quantization_aware,float_shadow
        tf.random.set_seed(2026)
        base=bounded_m0('features');aware=quantization_aware(base)
        x=np.random.default_rng(2026).uniform(-.9,.9,(8,15)).astype(np.float32)
        aware.compile(optimizer='adam',loss='binary_crossentropy');aware.train_on_batch(x,np.tile([0,1],4))
        shadow=float_shadow(aware,'features')
        wrapper=aware.get_layer('quant_latent')
        expected=next(v for v in wrapper.trainable_weights if tuple(v.shape)==(15,16)).numpy()
        np.testing.assert_array_equal(shadow.get_layer('latent').kernel.numpy(),expected)
    def test_actual_full_int8_export_has_input_headroom(self):
        import tensorflow as tf
        from swallowguard.train.qat_models import bounded_m0,quantization_aware,float_shadow
        from swallowguard.export.int8 import convert,audit
        from swallowguard.evaluate.selective import infer_accepted
        tf.random.set_seed(2026)
        x=np.random.default_rng(2026).uniform(-.9,.9,(8,15)).astype(np.float32)
        model=quantization_aware(bounded_m0('features'))
        b=convert(model,[x],partition='train',representative_indices=np.arange(len(x)))
        report=audit(b);self.assertEqual(report['operators'],['FULLY_CONNECTED','LOGISTIC'])
        actual=infer_accepted(b,x);self.assertTrue(np.isfinite(actual).all())
        shadow=float_shadow(model,'features')(x,training=False).numpy().ravel()
        self.assertLess(float(np.max(np.abs(shadow-actual))),.05)


if __name__=='__main__':unittest.main()
