# SWALLOWGUARD AI Beta-03 — executed milestone

Historical initial pilot report. Subsequent simulator build passed in GitHub CI; see [Milestone 02](MILESTONE_02.md) for current numerical validation results and remaining gates.

25 November 2026. **RESEARCH MODE only.** This package contains working source, real public-data M0 pilot results and explicitly gated firmware/TinyML candidates. No clinical claim or successful target build is made.

## What actually ran

- Read the complete supplied 10-page Beta-03 PDF. The two specifically named Work/GitHub specification files remain unavailable; reconciliation is open.
- GitHub repository is now selected: `naohidekiyosawa27/SwallowGuardAI`. Visibility is verified private and the authenticated user has admin/push access. Default branch `main` initially contains only the title README at `fae6c3044da8da722af323eb4e6b3227d5775557`. This source is prepared for feature-branch/draft-PR handoff; actual commit and CI evidence is recorded on GitHub. No default-branch merge is authorized.
- Verified primary repository metadata for all four datasets. D1 CC BY 4.0; D2 CC0; D3 King's Internal Access Only with embargo/no exposed files; D4 v2 CC BY 4.0. D3 is excluded.
- Following explicit user approval, downloaded only D4's 1,506,737,987-byte processed-clips archive. Publisher MD5 matched `cae6eb3013bcd7e3d1afe0278c6143fd`. Full-length archives and D1/D2 signal archives were not downloaded.
- Inspected all 4,053 real MAT files: 40,001×3 finite signal arrays and matching embedded 20-kHz/participant/session/activity metadata. Found three identical repeated waveforms within participants and none across participants; retained 4,050 after exact deduplication. No flatline channel at the diagnostic std≤1e-12 threshold. Full-scale clipping and raw QC were not established.
- Prepared deterministic features and three synchronous 2-kHz CNN channels (sound + upper/lower EMG). The inclusive 2-s endpoint was explicitly cropped from 4,001 resampled points to 4,000. No optical/pressure data was invented.
- Ran conventional M0 baselines and a lightweight CNN. Trained model artifacts and execution dependency lock are included. No paid compute was used.
- Ran **49 Python tests, all passing**, including the 4,137-parameter M1 architecture check. Portable C++ tests passed under g++ with undefined-behavior sanitizer. Optional synthetic INT8 export/operator/parity check also passed. See execution logs for exact output.

## Actual M0 results

| Partition | Participants | Clips | Swallow | Cough/throat-clear |
| --- | ---: | ---: | ---: | ---: |
| Training | 26 | 2722 | 1690 | 1032 |
| Validation | 6 | 602 | 358 | 244 |
| Test | 6 | 726 | 434 | 292 |

Participants, including repeat visits, are disjoint. Seed 2026. Training-only normalization and calibration. Random forest was selected by validation F1, not test results.

| Candidate | Validation F1 | Test F1 | Role |
| --- | ---: | ---: | --- |
| Logistic regression | 0.9003 | Not used for selection | Conventional comparison |
| Random forest | 0.9176 | 0.9085 | Selected M0 reference |
| CNN float, 1,073 parameters | 0.8667 | 0.9047 | TinyML candidate, not selected over reference |
| CNN INT8 | Not used to select reference | 0.9030 | Exported, deployment blocked |

Reference test precision 0.9023, recall 0.9147, F1 0.9085. Participant-cluster F1 95% percentile interval **0.8514–0.9510**, 1,000 resamples, six test participants. This small internal study does not establish external performance or statistical superiority.

Reference confusion matrix (rows true / columns predicted):

| True class | Predicted non-swallow | Predicted swallow |
| --- | ---: | ---: |
| Cough/throat-clear | 249 | 43 |
| Swallow task clip | 37 | 397 |

Reference failure counts by activity: {"Cough": 27, "Fluid": 36, "Solid": 1, "ThroatClearing": 16}. Class-specific failure counts and full aggregate metrics are in `reports/M0_D4_RESULTS.json`. Results describe event-centred healthy task clips. They do not measure dysphagia, aspiration, daily-life false alarms or continuous onset/offset accuracy. Publisher PASS selection and microphone-to-PVDF shift remain material limitations.

## Quantization finding — blocking deployment

The actual CNN INT8 flatbuffer is **5,736 bytes** (size target <100,000 bytes met for this candidate). SHA256 `2af08c92a2fe1153fe4f599c08ebd0fe2b9a2e2450fd1c26397b8e75b8e266f4`. INT8 I/O and no floating tensors; audited operators: CONV_2D, FULLY_CONNECTED, LOGISTIC, MEAN, RESHAPE. Fixed-batch/resource freezing resolved initial SHAPE/PACK/STRIDED_SLICE and READ_VARIABLE conversion failures. The executed pinned path is documented in source.

Float/INT8 threshold agreement is 99.17%; p99 absolute probability error 0.0153. However, one held-out clip has maximum error **0.9453**, with float probability 1.0000 and INT8 probability 0.0547. Approximately 5.39% of that clip's normalized input lies outside the INT8 representable range. The association with saturation is measured; its full causal explanation is not established.

`checked_quantize_input` now rejects out-of-range input at a proposed runtime boundary. That safeguard has unit tests, but its abstention rate and effect on independent data have not been validated. The reported metrics are ungated pilot metrics and have not been inflated by removing the failed test clip. The shared held-out split was inspected during pipeline corrections, so these are exploratory results; a new locked evaluation is required for confirmation.

**The CNN is not an accepted deployment model.** TFLM/ESP-NN integration, ESP-IDF target build, memory arena, heap/stacks, power and p50/p95 latency remain unmeasured. No <100-ms latency claim is made.

## Delivered engineering work

Repository architecture, AGENTS instructions, strict data contracts/adapters, dataset registry/cards/evidence, filtering/resampling/alignment/quality/segmentation, train-only scaling, subject splits, two conventional baselines, M0 CNN, untrained M1 intermediate-fusion architecture, INT8 conversion/audit/parity tools, synthetic golden vector, C++ model array, simulated sensor HAL, bounded buffering/queues, ESP-IDF task skeleton, CI definitions, model cards, phantom/safety plan and engineering backlog.

The default firmware is simulated-only. Local display is serial status, logging is a queue-drain counter, and actual TFT/microSD/live sensor integration is pending. No fabricated registers or dummy clinical model are supplied. M2 and clinical outputs remain disabled.

## Reproduce

Use `reports/requirements-executed.txt` in an isolated Python 3.12 environment for the executed dependencies. Then `pip install -e . --no-deps` and `bash scripts/verify.sh`. The simpler `pip install -e '.[tinyml]'` reproduces top-level pins but may resolve different transitive package versions. Compiler and runtime versions are in `reports/execution_environment.json`.

Data access and paths remain local. Download/recheck the exact approved D4 v2 archive, inspect/extract safely, and use the publisher's clip manifest. Commands:

```bash
python -m swallowguard.adapters.audit_d4 /secure/extracted /secure/processed_clip_manifest.csv /secure/results/audit.json
python -m swallowguard.adapters.prepare_d4 /secure/extracted /secure/processed_clip_manifest.csv /secure/data/features.npz --waveforms /secure/data/waveforms.npz
python -m swallowguard.train.baseline /secure/data/features.npz /secure/results/baseline.json --model-output /secure/results/reference.joblib
python -m swallowguard.train.cnn /secure/data/waveforms.npz /secure/results/cnn --epochs 8
python scripts/export_model_c.py /secure/results/cnn/m0.int8.tflite /secure/results/c_export
```

Only load joblib model files from a trusted source; never execute arbitrary serialized models. The artifact manifest gives hashes for this package's actual trained weights. Raw waveforms and per-participant manifests are intentionally absent from the deliverable.

## Remaining gates

1. Review the feature-branch draft PR and its actual automated checks in the verified private repository. No default-branch merge is authorized.
2. Reconcile the two missing Work/GitHub briefs and owner choices for source-code licensing.
3. Address quantization outlier/input quality using training/validation protocols, then confirm on a new locked held-out or external dataset. Random forest remains the selected conventional event reference; its success does not select the CNN automatically.
4. Install/verify ESP-IDF and run the configured target build; review real hardware documentation/pinout and perform phantom metrology/safety checks before actual sensor acquisition. Target measurements cannot be inferred from host tests.
5. M1 requires real synchronized prototype recordings; M2 requires clinician adjudication and safety/ethics authorization. No human-connected test, clinical risk output or autonomous therapy was performed.

Dataset attribution: Kamavuako, Chen and Ismail, *A Multimodal Healthy Swallowing Dataset of Synchronous Swallowing Sounds and Surface Electromyography for Reproducible Research*, version 2, DOI https://doi.org/10.18742/33952399, CC BY 4.0. SWALLOWGUARD filtering, resampling, deduplication and models are derived research work; no source-author endorsement is implied.
