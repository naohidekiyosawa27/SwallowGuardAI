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
