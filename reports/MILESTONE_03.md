# Milestone 03: bounded QAT passes the M0 numerical gate

25 November 2026. RESEARCH MODE only. Actual CPU experiments on the previously authorized D4 v2 processed clips; no new dataset download or paid compute.

## Decision

The **waveform_QAT** CNN passes the frozen engineering numerical criteria on 602 validation windows from six participants. It is eligible for disconnected bench integration, **not deployment-ready or clinically validated**. The M01 random-forest reference and locked M1 architecture remain unchanged. All four trials, including a failed PTQ control, are retained in `M0_R3_RESULTS.json`.

The study followed `docs/protocols/M0_R3_BOUNDED_QAT.json`, saved before training. Training/calibration used only the original 26 training participants (2,722 windows); model/checkpoint selection used the original six validation participants (602 windows). Participant-disjoint splitting is unchanged. Development has reused validation, so a new confirmation set is still required.

## Actual validation results

| Candidate | Accepted / 602 | Event F1 on accepted | Max absolute error vs float shadow | Threshold agreement | Model bytes | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Features PTQ | 598 | 0.92374 | 0.02611 | 100% | 2,496 | Pass |
| Features QAT | 602 | 0.92374 | 0.02758 | 100% | 2,408 | Pass |
| Waveform PTQ | 97 | 0.97436 | 0.03599 | 98.969% | 5,616 | **Fail: 16.11% coverage and agreement** |
| Waveform QAT | 602 | **0.93906** | **0.03995** | **99.668%** | **5,800** | **Selected** |

Acceptance requires coverage ≥95%, max error ≤0.05, threshold agreement ≥99%, accepted-subset F1 loss vs float ≤0.01, size <100,000 bytes and validation INT8 event F1 ≥0.90. These conditions do not certify input physiology, continuous-event performance or clinical risk. No numerical threshold was relaxed.

Selected validation precision/recall and full confusion matrices are in the JSON. Participant-cluster F1 95% percentile interval: 0.91576–0.96329 (1,000 resamples; only six validation participants; development reuse). The primary parity reference is an unquantized float shadow with the same learned kernels/biases. QAT fake-quant simulation vs INT8 max error is separately 0.02734, not the primary acceptance reference.

## Exposed-test regression after selection

Only the selected candidate was evaluated after writing `selection_before_regression.json`. The original M01 test was already inspected during earlier work; these 726 windows from six participants are **regression evidence, not a fresh holdout**.

Coverage 726/726; INT8 event F1 0.91951; precision 0.88161; recall 0.96083. Float-shadow F1 0.92053. Participant-cluster F1 95% interval 0.86571–0.96063. Maximum probability error 0.03552; threshold agreement 99.862%. Confusion matrix (true rows / predicted columns):

| True class | Non-swallow | Swallow |
| --- | ---: | ---: |
| Cough/throat-clear | 236 | 56 |
| Swallow task clip | 17 | 417 |

There are 73 errors, including 56 false-positive task clips. Error counts are not per-hour false alarms; clips are event-centred. No independent superiority over the M01 random forest is established. Healthy task recognition cannot establish aspiration or dysphagia detection.

## Artifact and software evidence

Selected CNN: 1,073 parameters, 5,800 bytes, SHA256 `ed486cdfc5a06578a444615a1bf7c0b3f2b745a424d149a21d5db2c3bdd1eeda`. Audited INT8 input `[1,4000,3]`, INT8 output `[1,1]`, no float tensors. Operators: CONV_2D, FULLY_CONNECTED, LOGISTIC, MEAN, RESHAPE. Input scale 0.007843137718737125 / zero point 0; output scale 0.00390625 / zero point -128.

Executed isolated environment: TensorFlow 2.18.1, tf-keras 2.18.0, TFMOT 0.8.0, NumPy 1.26.4, CPU only. Full dependency lock: `requirements-qat-executed.txt`. The original NumPy 2 environment was retained separately. Initial compatibility smoke tests found and corrected legacy-Keras seed handling and wrapper weight-copying before this successful study. Custom QAT remains experimental.

Local full suite: **79 Python tests passed**, including actual synthetic INT8 conversion and unquantized shadow-copy checks. Portable C++ sanitizer checks passed. Log: `execution_logs/milestone03_tests.log`. GitHub CI target compilation and exact dependency/ESP-NN evidence are recorded on the draft PR; no local ESP-IDF build is claimed.

The new `sg_tflm` component links a five-operator runner with structural model verification, explicit numerical/artifact-identity prerequisites, INT8 checks, quality/range gates and measured-invocation hooks. The identity boolean is a caller obligation, not a cryptographic implementation. Default firmware loads no model or tensor arena and uses simulated sensors. A compile check is not a device invocation.

## Reproduce without putting data in GitHub

```bash
python -m venv .venv-qat
.venv-qat/bin/pip install -r requirements-qat.txt
TF_USE_LEGACY_KERAS=1 PYTHONPATH=src .venv-qat/bin/python -m swallowguard.train.bounded_qat \
  /secure/D4/features_clean.npz /secure/D4/waveforms_clean.npz \
  /secure/D4/cnn_clean/evaluation.json docs/protocols/M0_R3_BOUNDED_QAT.json /secure/D4/r3
TF_USE_LEGACY_KERAS=1 PYTHONPATH=src .venv-qat/bin/python -m unittest discover -s tests -v
bash scripts/check_host.sh
```

Use the executed dependency lock when exact transitive versions are required. The optional manual QAT CI uses only synthetic fixtures. Actual trained artifacts are delivered privately, outside GitHub; no waveform or participant rows are included.

## Remaining gates

- Target inference, synthetic golden-vector parity, arena, heap/stacks, p50/p95/worst latency and power remain unmeasured. <100 ms is still a target.
- Window normalization discards absolute amplitude and is not artifact rejection. Physical signal-quality, clipping and synchronization need phantom measurements.
- D4 uses sound and two EMG channels. Optical tracking, respiratory sensing, BMI270 and PVDF transfer remain unvalidated on actual hardware.
- New external/locked-participant confirmation, source specification reconciliation and code-license decision remain open. M1/M2, safety review and human-subject prerequisites are unchanged.

Sources and critical appraisal: `docs/AI_RESEARCH_R3.md`. Dataset attribution: Kamavuako, Chen and Ismail, D4 version 2, DOI https://doi.org/10.18742/33952399, CC BY 4.0. Filtering, resampling, deduplication, normalization and models are SWALLOWGUARD derived research work; no source-author endorsement.
