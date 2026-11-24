# Next experiment: disconnected ESP32-S3 numerical bench

Status: **protocol only, not executed on hardware**. No person or sensor worn on a person. The firmware default remains simulated-only and unloaded. This protocol does not authorize changing to live sensor drivers or clinical use.

1. Record board/module, IDF and toolchain versions, exact TFLM/ESP-NN dependency lock, CPU clock, memory placement, sdkconfig, git commit and model SHA256. Confirm the selected artifact is exactly `ed486cdfc5a06578a444615a1bf7c0b3f2b745a424d149a21d5db2c3bdd1eeda` before asserting `artifact_identity_verified`. Never treat structural FlatBuffer verification as provenance verification.
2. Begin with the private package's synthetic INT8 golden vector. No participant waveform is needed. Allocate a 16-byte-aligned caller-owned arena; keep model/arena alive throughout invocation. Record allocation failures. Increase arena only within a declared board budget, documenting every attempt. Report `arena_used_bytes()` plus available/minimum heap and task stack high-water marks separately.
3. Use `ResearchTFLMRunner`, expected input elements 12,000, explicit numerical pass and actual identity verification. Feed already quantized synthetic values. The physical-quality boolean means synthetic bench contract validity here, never evidence of patient/sensor quality. Confirm bad/null inputs, incorrect counts and false gates produce `valid=false`. Log provenance `synthetic` on every record.
4. Compare target INT8 output with desktop golden output. Freeze acceptable difference at **≤1 output integer unit** for this bench check. Retain exact observed values and failures; a tolerance change requires a new protocol. One golden vector verifies an interface only, not dataset or clinical accuracy.
5. Run 20 warm-ups followed by 1,000 timed invocations of the same synthetic vector, reporting p50/p95/max Invoke time and repeatability. Measure preprocessing and complete window-to-result latency separately on additional synthetic windows. Record dropouts/watchdog/logging contention and distinguish cold-start allocation from steady-state inference.
6. The engineering latency target is p95 end-to-end processing **<100 ms after the 2-second window is available**. It does not mean a 100-ms physiological event-detection delay. Report the full observation/segmentation delay and hop size separately. Power needs an instrument and a separately recorded method; do not infer energy from MAC count.
7. Promote only to further mechanical-phantom experiments after reviewing measured failures and resource margins. A passing synthetic bench does not authorize live hardware/human connection, M1 data collection or M2 clinical output.

The actual selected graph requires 878,112 logical Conv/Dense MACs per window and 12,000 input bytes; these are shape calculations, not measurements. `reports/M0_R3_STATIC_BUDGET.json` deliberately leaves arena and latency null. Reproduce the calculation with:

```bash
PYTHONPATH=src .venv/bin/python scripts/static_model_budget.py \
  /secure/m0_r3.int8.tflite /secure/static_budget.json
```

Save bench records outside GitHub if they contain real measurements linked to participants. Synthetic benchmark logs and reviewed aggregate measurements can be added through a new feature-branch draft PR. No data, patient or clinical claim is implied by this protocol.
