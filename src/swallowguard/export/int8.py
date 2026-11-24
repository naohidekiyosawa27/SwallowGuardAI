"""Training-only calibration, operator audit and held-out quantization parity."""
import hashlib
import numpy as np

ALLOWED_OPS = {"RESHAPE", "CONV_2D", "MEAN", "FULLY_CONNECTED", "LOGISTIC", "CONCATENATION"}


def quantize_input(x, scale, zero_point):
    if not np.isfinite(scale) or scale <= 0 or not np.isfinite(x).all():
        raise ValueError("Invalid INT8 calibration or input")
    return np.clip(np.rint(np.asarray(x)/scale+zero_point),-128,127).astype(np.int8)


def checked_quantize_input(x, scale, zero_point):
    """Fail-closed deployment boundary; plain quantize_input is diagnostic only.

    This guards numerical range, not physiological signal validity or clinical
    safety. Its effect on abstention must be measured on future independent data.
    """
    q=quantize_input(x,scale,zero_point)
    minimum,maximum=(-128-zero_point)*scale,(127-zero_point)*scale
    if np.any(np.asarray(x)<minimum) or np.any(np.asarray(x)>maximum):
        raise ValueError('invalid_measurement: input exceeds INT8 calibration range')
    return q


def convert(model, training_inputs, *, partition):
    import tensorflow as tf
    if partition != "train":
        raise ValueError("Representative set must come exclusively from training subjects")
    if len(training_inputs) != len(model.inputs) or not training_inputs or not len(training_inputs[0]):
        raise ValueError("Invalid representative input set")
    if any(len(x) != len(training_inputs[0]) or not np.isfinite(x).all() for x in training_inputs):
        raise ValueError("Missing/unpaired representative inputs")
    def representative():
        # Deterministic coverage across training recordings, rather than the
        # first participant/class-sorted block. Never use held-out samples.
        selected=np.random.default_rng(2026).permutation(len(training_inputs[0]))[:256]
        for i in selected:
            yield [np.asarray(x[i:i+1],dtype=np.float32) for x in training_inputs]
    # Embedded inference uses batch 1 with fixed temporal/channel dimensions.
    # Freeze this signature to avoid SHAPE/PACK/STRIDED_SLICE introduced by
    # Keras dynamic-batch reshape bookkeeping.
    specs=[tf.TensorSpec([1,*inp.shape[1:]],tf.float32,name=inp.name.split(':')[0]) for inp in model.inputs]
    @tf.function(input_signature=specs)
    def serving(*args):
        return model(list(args) if len(args)>1 else args[0],training=False)
    # Freeze resources as constants too: a concrete signature alone can retain
    # READ_VARIABLE with newer Keras, which is unsuitable for this TFLM model.
    from tensorflow.python.framework.convert_to_constants import convert_variables_to_constants_v2
    frozen=convert_variables_to_constants_v2(serving.get_concrete_function())
    converter = tf.lite.TFLiteConverter.from_concrete_functions([frozen])
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = representative
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8
    return converter.convert()


def audit(model_bytes):
    import tensorflow as tf
    interpreter = tf.lite.Interpreter(model_content=model_bytes)
    interpreter.allocate_tensors()
    for tensor in interpreter.get_input_details()+interpreter.get_output_details():
        if tensor['dtype'] != np.int8 or tensor['quantization'][0] <= 0:
            raise ValueError("Model must expose calibrated INT8 input/output")
    if any(np.issubdtype(t['dtype'],np.floating) for t in interpreter.get_tensor_details()):
        raise ValueError("Float fallback tensor found")
    # Private API is confined to this pinned TensorFlow inspection utility.
    ops = sorted({op['op_name'] for op in interpreter._get_ops_details()} - {"DELEGATE"})
    if set(ops)-ALLOWED_OPS:
        raise ValueError(f"Unsupported candidate operators: {set(ops)-ALLOWED_OPS}")
    def describe(t):
        return {"name":t['name'],"shape":t['shape'].tolist(),"dtype":str(np.dtype(t['dtype'])),
                "scale":float(t['quantization'][0]),"zero_point":int(t['quantization'][1])}
    return {"bytes":len(model_bytes),"below_100000_byte_target":len(model_bytes)<100000,
            "sha256":hashlib.sha256(model_bytes).hexdigest(),"operators":ops,
            "inputs":[describe(t) for t in interpreter.get_input_details()],
            "outputs":[describe(t) for t in interpreter.get_output_details()],
            "latency_ms":None,"tensor_arena_bytes":None,"device_verified":False}


def parity(model, model_bytes, heldout_inputs, *, labels=None, subjects=None):
    """M0 single-input parity; evaluate threshold at 0.5, chosen before test."""
    import tensorflow as tf
    i = tf.lite.Interpreter(model_content=model_bytes);i.allocate_tensors()
    ins, outs = i.get_input_details(), i.get_output_details()
    if len(ins) != 1 or len(outs) != 1 or not len(heldout_inputs):
        raise ValueError("Require nonempty single-input M0 heldout data")
    actual=[]
    for x in heldout_inputs:
        scale,z = ins[0]['quantization']
        i.set_tensor(ins[0]['index'],quantize_input(x[None],scale,z));i.invoke()
        scale,z=outs[0]['quantization']
        actual.append(float((i.get_tensor(outs[0]['index']).astype(float)-z).ravel()[0]*scale))
    expected = model(heldout_inputs,training=False).numpy().ravel()
    actual = np.asarray(actual)
    result={"samples":len(actual),"max_absolute_probability_error":float(np.max(np.abs(expected-actual))),
            "p99_absolute_probability_error":float(np.quantile(np.abs(expected-actual),.99)),
            "samples_probability_error_above_0_05":int(np.sum(np.abs(expected-actual)>.05)),
            "threshold_agreement":float(np.mean((expected>=0.5)==(actual>=0.5)))}
    if labels is not None:
        from swallowguard.evaluate.metrics import binary_metrics,cluster_f1_ci
        result['int8_window_metrics']=binary_metrics(labels,(actual>=0.5).astype(int))
        if subjects is not None:
            result['int8_subject_cluster_f1_ci']=cluster_f1_ci(labels,(actual>=0.5).astype(int),subjects)
    return result
