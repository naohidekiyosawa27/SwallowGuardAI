# Recent AI evidence and the M0-R3 decision

Reviewed 25 November 2026. Primary sources are recorded in `LITERATURE_R3.json` and `LITERATURE_R3.bib`. These papers concern different tasks/devices; their performance is not evidence of swallowing or clinical accuracy.

| Primary journal source | Useful engineering principle | Decision and limitation |
| --- | --- | --- |
| King et al., *Scientific Reports* (2025), [MicroNAS](https://doi.org/10.1038/s41598-025-90764-z) | Evaluate time-series architecture against memory and latency constraints | Preserve the small CNN; measure actual target resources next. No architecture search was run. Publisher metadata and institutional PDF were inspected; a local PDF retry failed with HTTP 503. |
| Leogrande et al., *Sensors* (2026), [quantization-aware architecture selection](https://doi.org/10.3390/s26092674) | Quantization robustness belongs in model selection | Compare actual INT8 exports, not float F1 alone. The paper's acknowledged random-window evaluation is not adopted: SWALLOWGUARD retains participant-disjoint splits. PPG blood-pressure results do not transfer to M0. |
| Alanazi et al., *Electronics* (2026), [cross-layer TinyML optimization](https://doi.org/10.3390/electronics15132918) | Assess model, memory and hardware together | Keep full INT8 and audit deployment resources. No mixed precision, DVFS, distillation or reproduction of that system is claimed. Z-score normalization does not mathematically bound unseen values. |

The [official TensorFlow QAT guide](https://www.tensorflow.org/model_optimization/guide/quantization/training_comprehensive_guide) supplies the implementation pattern, not journal evidence. Its custom quantization configuration is experimental; passing a Python simulation does not prove device compatibility.

## Implemented hypothesis

M02 measured internal activation saturation in the previous export. R3 therefore tests **bounded numerical representations plus bounded activations plus QAT**, while retaining PTQ controls. This specific combination is our engineering adaptation, not a published swallowing method or a claim of novelty.

For synchronous sound and two EMG channels, independently per window/channel:

`u = 0.9 * (x - mean(x)) / max(abs(x - mean(x)))`.

Finite, non-flat windows are required. No waveform is clipped or imputed. The transformation removes offset and absolute amplitude, so amplitude-dependent physiology cannot be inferred. Flatline, clipping, detachment and timing checks must precede this representation on a future physical device. Passing the bound is not physical signal-quality certification.

The feature comparator fits a standardizer on training participants, then applies `0.9*z/(1+abs(z))`. Conv/Dense activations use ReLU6. QAT uses fixed input/activation/output ranges and 8-bit weights; deployment is an audited full-INT8 flatbuffer. Compare the integer model against a float shadow containing the same learned **unquantized** weights. Report fake-quant simulation agreement separately to avoid a circular parity test.

## Frozen decision rule and outcome

The four-candidate protocol was saved before training in `protocols/M0_R3_BOUNDED_QAT.json`. Numerical limits were retained: coverage ≥95%, maximum probability error ≤0.05, threshold agreement ≥99%, F1 loss ≤0.01, model <100,000 bytes. A validation event-F1 floor of 0.90 was added; no numerical tolerance was relaxed. Select eligible candidates only by validation results.

Three candidates passed. Waveform PTQ failed because its input range covered only 97/602 validation windows and agreement was below 99%; its high accepted-subset F1 must not hide the 505 abstentions. Waveform QAT was selected. See `reports/MILESTONE_03.md` for all results and the unchanged clinical/hardware gates.

## Next evidence, in order

1. Compile the guarded TFLM/ESP-NN runner and retain dependency/build evidence.
2. Replay synthetic golden vectors on a disconnected ESP32-S3 bench. Verify artifact identity, parity, arena, heap/stacks and latency distribution; measure rather than infer <100 ms.
3. Validate physical DSP and synchronization on mechanical phantoms. Microphone data does not establish PVDF transfer, and public data has no optical/respiratory branch.
4. Obtain a new participant-disjoint confirmation set with verified rights and matching labels. Existing validation is development data; the old test is exposed regression data.
5. M1 needs synchronized prototype data. M2 remains disabled until clinically adjudicated data, safety/ethics authorization and reference assessments exist.

## Follow-up domain search after the R3 experiment

These sources were found after training and did not guide or change the frozen four-candidate study.

- Zhao et al., *Machine Intelligence Research* (2026), [LiteMamba-EMG](https://doi.org/10.1007/s11633-026-1663-8): publisher abstract describes channel-cooperative state-space modeling and self-supervised pretraining from hand sEMG. Full methods and latency hardware were not verified. Its reported 2.56 million parameters imply roughly 2.56 MB of dense INT8 weights before overhead, exceeding the 100 KB target. Treat pretraining/distillation as a future ablation hypothesis, not a deployable replacement or a proven gain for D4. No external weights or NinaPro archive were downloaded; M1 remains unchanged.
- Takai et al., *Advanced Biomedical Engineering* (2026), [PVDF decision-tree event detection](https://doi.org/10.14326/abe.15.215): publisher abstract and PDF measurement/preprocessing sections were inspected. The work separates isolated-task classification from continuous eating-event detection. Its PVDF system digitizes at 10 kHz and studies components up to 3 kHz. SWALLOWGUARD's D4 M0 representation at 2 kHz cannot represent that upper band; do not copy its filters or infer microphone-to-PVDF equivalence. This supports a separate phantom transfer-function/bandwidth study and continuous annotation protocol. Participant split was not verified, so its metrics are not an independent cross-subject benchmark for SWALLOWGUARD. No human test is authorized by this review.
