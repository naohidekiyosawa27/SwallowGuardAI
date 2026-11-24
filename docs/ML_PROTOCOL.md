# Reproducible model protocol

## M0

M0 predicts physiological event categories only. Begin with D4's verified same-recording acoustic and EMG channels or another independently verified source. Avoid pooling datasets before a domain and identity review. D4 swallow classes map Fluid/Saliva/Solid to event=1 and Cough/ThroatClearing to event=0. This is event-clip classification; no healthy/diseased inference follows.

1. Freeze source version, file hashes, annotation mapping and participant manifest. Split participants deterministically with seed 2026; retain repeated visits in their participant partition. Small samples may need grouped CV; the default split is not evidence of adequate statistical power.
2. Apply deterministic per-recording preprocessing. Fit mean/scale only on training data. Persist split and scaler. D4's publisher-selected clips already exist before our split; account for their selection and do not assert raw QC was repeated.
3. Compare logistic regression and bounded random forest on fixed features. Select by validation F1, then evaluate once on held-out subjects. CNN is another candidate; choosing between CNN and baselines must also use validation data, not held-out results.
4. Report class-order confusion matrix, precision/recall/F1, class and participant counts, participant-cluster percentile CIs, and failure cases. Separate session-clip errors from continuous event errors. Event matching, onset/offset error and false events/min remain pending full-length annotations.
5. Train a lightweight Conv2D(width=1) temporal CNN candidate with the same subjects and endpoint. Optional early stopping uses validation only. No cross-subject normalization or INT8 calibration leakage.

Canonical feature NPZ fields: numeric `X` N×F, binary `y` N, string `subjects` N, scalar string `source`, scalar string `dataset_id`. Canonical CNN NPZ uses X N×T×C and the same metadata. Object/pickle arrays are forbidden. D4 tooling prepares feature tables and optional synchronized 4,000×3 acoustic/EMG waveform windows at 2 kHz. This M0 uses the publisher's two-second clips; the M1 four-second design assumption is unchanged. Exact duplicate waveforms are excluded deterministically; duplicate cross-subject or conflicting labels abort processing.

## M1 and M2

M1 is the PDF's four-branch intermediate-fusion candidate: 16 pooled features per branch + eight timing features, Dense(16), sigmoid event head. Expected 4,137 parameters are checked when TensorFlow is available. Timing-feature definitions and normalization still need paired actual prototype data. Optical addition must be compared with non-optical ablation on the same held-out participants. No public channel is relabelled as optical.

M2 remains disabled. It requires an independently reviewed safety/ethics protocol, clinician adjudication, specified reference assessment and endpoint-specific labels. M0/M1 probabilities cannot be exposed as clinical risk, and swallowing-safety clearance is never inferred here.

## INT8 gate

Use training subjects only for the representative set; enforce INT8 builtins and INT8 I/O. Audit operators and reject floating tensors. Integer shape/index/bias tensors may remain INT32/INT64; that is compatible with full integer quantization. The candidate resolver allows RESHAPE, CONV_2D, MEAN, FULLY_CONNECTED, LOGISTIC and CONCATENATION, but target support still needs exact-model verification.

Measure float versus dequantized INT8 probability error, threshold agreement and held-out metric degradation. `checked_quantize_input` rejects inputs outside the numerical INT8 range, while `quantize_input` deliberately permits saturation for diagnostic parity evaluation. Neither alone establishes physiological quality. Actual pilot outlier analysis is in reports/QUANTIZATION_FAILURE_ANALYSIS.json; deployment is blocked. Save synthetic golden vectors and tensor quantization metadata before target integration. Target size is <100,000 bytes and latency <100 ms; a small weight count does not prove either. Measure target p50/p95 latency, arena, heap/stack high-water marks, power and transport behavior. The 4-s window is separate from compute latency.

The pinned TensorFlow conversion path is retained for TFLM reproducibility. Current Google guidance marks conversion-time quantization deprecated in favor of LiteRT Quantizer; migration is a future compatibility decision and must be verified against ESP TFLM rather than silently replacing the locked deployment stack. Sources: [official quantization guidance](https://developers.google.com/edge/litert/conversion/tensorflow/quantization/post_training_quantization), [Espressif TFLM](https://github.com/espressif/esp-tflite-micro), [ESP-NN](https://github.com/espressif/esp-nn).

## Executed Milestone 02

See reports/MILESTONE_02.md and immutable protocols under docs/protocols/. The fixed-CNN study selects calibration only on training data and candidates only on validation. The prior test split is already exposed; its known outlier is a numerical diagnostic, not new confirmation. All three CNN calibration candidates and three linear feature comparators failed the declared numerical criteria. No new regression evaluation or deployment selection followed those failures.

The numerical input gate is necessary but insufficient: intermediate activations can saturate even for input-range-accepted validation clips. The export pipeline returns no eligible candidate when validation fails. C++ QuantizationRange and quantized_decision are portable contracts for future integration, not enabled TFLM inference. Grouped five-fold ablations use only the original 26 training participants and fit logistic normalization within each fold.

## M0-R3 bounded-QAT follow-up

`protocols/M0_R3_BOUNDED_QAT.json` freezes four candidates, original participant split and numerical limits before training. Full-INT8 waveform QAT passed; model card `models/cards/M0_R3.md` and `reports/MILESTONE_03.md` record all results. Float parity uses the same learned unquantized weights, not only fake-quant simulation. Bounded normalization removes absolute amplitude; it is not a physical quality gate. Existing validation is reused development data and the original test is exposed regression only. M1/M2 remain unchanged.
