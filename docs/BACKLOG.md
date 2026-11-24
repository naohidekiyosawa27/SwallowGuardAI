# Engineering backlog

| ID | Priority | Dependency | Deliverable / acceptance |
| --- | --- | --- | --- |
| R01 | P0 | User repository URL and integration access | Inspect actual branch/tree/permissions; feature branch and draft PR; no default merge |
| R02 | P0 | Missing Work/GitHub specifications | Reconcile supplied PDF against exact PDF/MD when available |
| D01 | P0 | None | Verified D1-D4 rights/versions/file sizes: implemented; keep D3 blocked |
| D02 | P0 | Approved D4 processed archive | Checksum + real MAT inspection + subject/label/quality audit; report actual results |
| D03 | P1 | Separate approval | D1/D2 archives, actual participant maps, schema, annotation origin and rates |
| M01 | P0 | D02 | Grouped conventional M0 baselines, validation selection, held-out confusion/cluster CI and failure analysis |
| M02 | P1 | M01 | Same-subject CNN comparison; train-only normalization; no test-based model selection |
| M03 | P1 | M02 | Actual full INT8 export, tensor/operator audit, held-out parity and golden vectors |
| F01 | P0 | ESP-IDF/toolchain | Target simulator build and CI result; host tests alone are insufficient |
| H01 | P0 | Exact datasheets/schematic | Pin, power, ADC and optical safety review; no guessed registers |
| H02 | P0 | H01 and instruments | Mechanical/optical phantom metrology and common-trigger synchronization |
| F02 | P1 | H02 | Hardware HAL/DMA, measured ring-buffer sizing, watchdog and dropout tests |
| F03 | P1 | M03/F02 | TFLM/ESP-NN exact-model target integration; latency p50/p95, arena/heap/stacks/power |
| F04 | P1 | Hardware pinout | TFT research UI + reliable microSD logging and fault tests |
| M04 | P2 | Synchronized real prototype dataset | M1 four-branch fusion, timing features and optical ablation |
| S01 | P0 | Independent specialists | Electrical/optical/mechanical/battery safety review before human connection |
| C01 | Future | Clinical partner + safety/ethics/protocol | M2 endpoint/reference design; implementation remains disabled |

No planned task is a measured result. Major deviations from the locked architecture require owner review. The simulator and source scaffolding can be reviewed before hardware or human-subject studies exist.

## Executed status

D02 and M01 completed for authorized D4 v2 processed clips; M02 completed as an exploratory CNN comparison. M03 export/operator audit completed, but quantization acceptance is blocked by an outlier. Repository selection and private visibility for R01 are resolved; feature-branch/draft-PR publication is the active handoff. R02, F01 and all actual hardware/safety/clinical gates remain open. No external validation or target inference is claimed.

## Milestone 02 evidence and open gates

Completed: fixed-CNN calibration comparison, FP32/reference-kernel controls, internal activation intervention, input-range accounting, six conventional grouped-CV ablations, three linear INT8 comparators, and cross-language numerical guard tests. All six quantized candidates failed frozen numerical validation criteria and remain blocked; thresholds were not relaxed.

Next: predeclare a bounded/QAT or validated-normalization study using training/validation data; retain failed trials; obtain independent confirmation data; implement only accepted model integration with actual TFLM/ESP-NN target benchmarks. Physical sensor acquisition, phantom metrology, safety review and M1/M2 evidence gates remain open. The initial simulator target build has passed; hardware operation has not been measured.

## Milestone 03 update

M03 numerical acceptance now passes for the bounded waveform QAT candidate (5,800 bytes; validation coverage 100%, F1 0.93906, max error 0.03995, agreement 99.668%). All four R3 trials are retained; waveform PTQ fails. The M01 reference and M1 architecture are unchanged. See `reports/MILESTONE_03.md`.

F03 now has a guarded TFLM/ESP-NN component and CI compilation check. Default firmware loads no model. Physical invocation, golden-vector parity, memory, latency and power measurements remain open. Obtain new independent confirmation data before making generalization claims. All earlier M02 failures remain valid historical results.
