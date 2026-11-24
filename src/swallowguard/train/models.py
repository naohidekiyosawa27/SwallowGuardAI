"""Candidate architectures, NOT trained models. Import TensorFlow lazily."""
M1_SHAPES = {"optical": (800,4), "pvdf": (8000,1), "emg": (800,1), "resp": (400,1)}


def branch(tf, input_tensor, *, channels, pvdf=False, name="signal"):
    # Explicit Conv2D with width 1 implements temporal 1D convolution for TFLM.
    x = tf.keras.layers.Reshape((int(input_tensor.shape[1]),1,channels),name=f"{name}_expand")(input_tensor)
    x = tf.keras.layers.Conv2D(8,(7 if pvdf else 5,1),strides=(4 if pvdf else 2,1),
                              activation="relu",padding="valid",name=f"{name}_conv_a")(x)
    x = tf.keras.layers.Conv2D(16,(5,1),strides=(2,1),activation="relu",name=f"{name}_conv_b")(x)
    return tf.keras.layers.GlobalAveragePooling2D(name=f"{name}_pool")(x)


def m0_model(samples=800, channels=1):
    import tensorflow as tf
    inp = tf.keras.Input((samples,channels),name="signal")
    x = branch(tf,inp,channels=channels)
    x = tf.keras.layers.Dense(16,activation="relu")(x)
    out = tf.keras.layers.Dense(1,activation="sigmoid",name="event_probability")(x)
    return tf.keras.Model(inp,out,name="M0_research_event")


def m1_candidate():
    import tensorflow as tf
    inputs, latents = [], []
    for name,shape in M1_SHAPES.items():
        inp = tf.keras.Input(shape,name=name);inputs.append(inp)
        latents.append(branch(tf,inp,channels=shape[1],pvdf=name=="pvdf",name=name))
    timing = tf.keras.Input((8,),name="timing_features");inputs.append(timing)
    x = tf.keras.layers.Concatenate()(latents+[timing])
    x = tf.keras.layers.Dense(16,activation="relu")(x)
    out = tf.keras.layers.Dense(1,activation="sigmoid",name="event_probability")(x)
    model = tf.keras.Model(inputs,out,name="M1_untrained_candidate")
    if model.count_params() != 4137:
        raise ValueError("Architecture differs from Beta-03 specification")
    return model
