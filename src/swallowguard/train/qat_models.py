"""Research-only bounded M0 models and explicit fixed-range QAT configuration.

Use the isolated requirements-qat environment and TF_USE_LEGACY_KERAS=1.
Custom quantizers are experimental; only an actually audited flatbuffer may
proceed to numerical validation. M1 remains unchanged.
"""
import tensorflow as tf
import tf_keras as keras
import tensorflow_model_optimization as tfmot


class FixedRange(tfmot.quantization.keras.quantizers.Quantizer):
    def __init__(self,minimum,maximum):self.minimum=float(minimum);self.maximum=float(maximum)
    def build(self,tensor_shape,name,layer):return {}
    def __call__(self,inputs,training,weights,**kwargs):
        return tf.quantization.fake_quant_with_min_max_vars(inputs,self.minimum,self.maximum,num_bits=8,narrow_range=False)
    def get_config(self):return {'minimum':self.minimum,'maximum':self.maximum}
    def __eq__(self,other):return isinstance(other,FixedRange) and self.get_config()==other.get_config()


class BoundedQuantizeConfig(tfmot.quantization.keras.QuantizeConfig):
    def __init__(self,minimum=0.,maximum=6.,weighted=False,per_axis=False):
        self.minimum=float(minimum);self.maximum=float(maximum);self.weighted=bool(weighted);self.per_axis=bool(per_axis)
    def get_weights_and_quantizers(self,layer):
        if not self.weighted:return []
        q=tfmot.quantization.keras.quantizers.LastValueQuantizer(num_bits=8,per_axis=self.per_axis,symmetric=True,narrow_range=True)
        return [(layer.kernel,q)]
    def get_activations_and_quantizers(self,layer):return []
    def set_quantize_weights(self,layer,quantize_weights):
        if self.weighted:layer.kernel=quantize_weights[0]
    def set_quantize_activations(self,layer,quantize_activations):pass
    def get_output_quantizers(self,layer):return [FixedRange(self.minimum,self.maximum)]
    def get_config(self):return {'minimum':self.minimum,'maximum':self.maximum,'weighted':self.weighted,'per_axis':self.per_axis}


CUSTOM_OBJECTS={'FixedRange':FixedRange,'BoundedQuantizeConfig':BoundedQuantizeConfig}


def bounded_m0(kind,channels=3,samples=4000):
    if kind=='features':
        inp=keras.Input((15,),name='features');x=inp
    elif kind=='waveform':
        inp=keras.Input((samples,channels),name='signal')
        x=keras.layers.Reshape((samples,1,channels),name='expand')(inp)
        x=keras.layers.Conv2D(8,(5,1),strides=(2,1),activation='relu6',kernel_initializer=keras.initializers.GlorotUniform(seed=2026),name='conv_a')(x)
        x=keras.layers.Conv2D(16,(5,1),strides=(2,1),activation='relu6',kernel_initializer=keras.initializers.GlorotUniform(seed=2027),name='conv_b')(x)
        x=keras.layers.GlobalAveragePooling2D(name='pool')(x)
    else:raise ValueError('Unknown bounded M0 representation')
    x=keras.layers.Dense(16,activation='relu6',kernel_initializer=keras.initializers.GlorotUniform(seed=2028),name='latent')(x)
    x=keras.layers.Dense(1,activation='linear',kernel_initializer=keras.initializers.GlorotUniform(seed=2029),name='logits')(x)
    out=keras.layers.Activation('sigmoid',name='event_probability')(x)
    return keras.Model(inp,out,name='M0_bounded_'+kind)


def quantization_aware(base):
    def annotate(layer):
        if isinstance(layer,keras.layers.InputLayer):return layer
        weighted=isinstance(layer,(keras.layers.Conv2D,keras.layers.Dense))
        if layer.name=='logits':lo,hi=-8.,8.
        elif layer.name=='event_probability':lo,hi=0.,255/256
        elif isinstance(layer,keras.layers.Reshape):lo,hi=-1.,1.
        else:lo,hi=0.,6.
        config=BoundedQuantizeConfig(lo,hi,weighted,per_axis=isinstance(layer,keras.layers.Conv2D))
        return tfmot.quantization.keras.quantize_annotate_layer(layer,config)
    annotated=keras.models.clone_model(base,clone_function=annotate)
    annotated.set_weights(base.get_weights())
    with tfmot.quantization.keras.quantize_scope(CUSTOM_OBJECTS):
        result=tfmot.quantization.keras.quantize_apply(annotated)
    # Fix the declared model input domain with 10% preprocessing headroom.
    # No synthetic or held-out representative waveform is introduced.
    for layer in result.layers:
        if type(layer).__name__=='QuantizeLayer':layer.quantizer=FixedRange(-1.,1.)
    return result


def float_shadow(qat,kind,channels=3,samples=4000):
    result=bounded_m0(kind,channels,samples)
    for layer in result.layers:
        if isinstance(layer,(keras.layers.Conv2D,keras.layers.Dense)):
            wrapper=qat.get_layer('quant_'+layer.name)
            kernels=[v for v in wrapper.trainable_weights if v.shape==layer.kernel.shape]
            biases=[v for v in wrapper.trainable_weights if v.shape==layer.bias.shape]
            if len(kernels)!=1 or len(biases)!=1:raise ValueError('Ambiguous QAT shadow weights')
            layer.set_weights([kernels[0].numpy(),biases[0].numpy()])
    return result
