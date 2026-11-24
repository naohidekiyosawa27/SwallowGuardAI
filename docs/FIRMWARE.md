# Firmware implementation and bench bring-up

Current active target is simulated acquisition only. No sensor register writes, pin assignments, clinical outputs or human-connected operation are implemented.

```bash
. /path/to/esp-idf/export.sh
cd firmware
idf.py set-target esp32s3
idf.py build
```

The GitHub workflow proposes Espressif IDF v5.3.2 for the simulator. Its actual CI result must be checked after the repository is connected. `sdkconfig.defaults` proposes 16-MB flash and octal PSRAM for N16R8; verify the exact board/module and schematic before flashing. Host g++ tests are independent of ESP-IDF and prove only the exercised portable logic.

`app_main.cpp` implements acquisition/processing/logging tasks, bounded queues, latched overflow/timeout invalidity and serial research status. SimulatedHAL timestamps are virtual; ESP scheduling is not an ADC or clock-synchronization benchmark. `research_core.hpp` offers a single-thread ring with explicit overflow and a quality gate. The optional `tflm_candidate.hpp` is an integration contract outside the default build; its compile and runtime behavior are unverified until linked with the selected component and a verified model.

## Pending boundaries

| Boundary | Required input / exit evidence |
| --- | --- |
| PAA5163E1 SPI driver | Authorized exact datasheet/init map; power/I/O/VCSEL review; tracking and standoff characterization |
| ADC acquisition | AFE transfer function, full scale, analog antialias and source impedance; measured DMA timing |
| SDP31 | Official command set, CRC/unit conversion and pneumatic calibration; no pressure-as-flow assumption |
| BMI270 | Official initialization/configuration, axis map, timestamping and bench motion thresholds |
| DSP | Streaming state/delay equivalence with Python, fixed-point bounds and golden vectors |
| TFLM + ESP-NN | Component pin and lockfile; exact INT8 operator/tensor audit; target build and replay |
| TFT | Controller, pinout, RESEARCH MODE/event/quality screens; no risk UI |
| microSD | SPI/SDMMC wiring, immutable raw schema, bounded writes, error handling; no silent loss |
| Research biofeedback | Clinician-directed display contract, separate from autonomous treatment |

Espressif component `espressif/esp-tflite-micro` 1.3.1 was located in the official registry and documents ESP-NN integration. It is a candidate verified-to-exist version, not a tested dependency of this simulator. Add/pin it only with a reviewed model integration branch and retain the resolved dependency lock. No generated placeholder model is embedded merely to claim inference works.

Long sensor cabling, electrical isolation, optical containment, watchdog scheduling and log-pressure behavior remain bench review items. All embedded thresholds are assumptions until measured.

## Verified base build and new numerical guard

The base simulator at a511265d7a82f81140a81c79cc906b741dc06514 built successfully for ESP32-S3 in IDF v5.3.2: https://github.com/naohidekiyosawa27/SwallowGuardAI/actions/runs/45459733898 . This resolves the earlier simulator compilation blocker only.

Milestone 02 adds quantization_guard.hpp to the simulator compilation and host tests. It rejects invalid scale/zero point, nonfinite/out-of-range input and missing independent model acceptance. Python/C++ decisions are checked on 75 synthetic float32 boundary/random cases. Passing this input guard does not guarantee internal activation parity. All current numerical candidates failed validation; no actual model is enabled. Target checks for the new branch are reported by its PR CI.

## R3 TFLM/ESP-NN compile integration

`components/sg_tflm` pins `espressif/esp-tflite-micro` 1.3.1 and declares a public managed-component dependency. CI records the resolved ESP-NN version, dependency lock and compile flag. Actual dependency resolution and compilation must pass before describing the integration as built. `ResearchTFLMRunner` provides five operators and guarded initialization/invocation; caller-owned model bytes and a 16-byte-aligned arena must outlive it. Artifact SHA verification, physical quality and prequantization range checks are mandatory caller prerequisites, not inferred from a bool supplied by an untrusted source.

Default firmware constructs only an unloaded runner. No model or arena is linked, no TFLM invocation runs and simulated acquisition remains active. Trained model bytes stay outside GitHub. On a disconnected bench, first verify the private artifact SHA, then replay synthetic golden vectors, report output-unit tolerance, allocate/bound arena, and record p50/p95/worst Invoke time plus preprocessing/end-to-end latency, heap/stacks and power. Only measured target results can satisfy deployment resource gates. Live sensor drivers and human-connected tests remain blocked.

Actual R3 CI run 45470279058 succeeded on implementation commit e45daf1f1f8020bbc42d44dd4648a179accfa3d8. Resolved IDF/TFLM/ESP-NN versions were 5.3.2/1.3.1/1.5.0; ESP-NN flag found. To reproduce the exact resolved graph, copy `reports/firmware_dependencies_R3.lock` to `firmware/dependencies.lock` before `idf.py set-target esp32s3` and `idf.py build`. The image is 272,640 bytes with no model loaded. Vendor deprecation warnings remain; no target execution or runtime resource claim follows from this compile result.
