# Milestone 04: electrical Rev-A acquisition contract

25 November 2026. RESEARCH MODE. Draft hardware reference reconciled with software; no patient connection, physical UART, sensor acquisition, STM32 build or target inference claimed.

## Source and scope

Read user's 16-page Electrical Rev A.0/Beta-03 PDF (SHA256 45a2e94a87d0b4b05f635d5b07ea7f46ae580a88c63afa567244bce0a3f81d43), including architecture/optical/link/GPIO figures. It proposes local STM32G0B1 + ADS131M02 acquisition, a full-duplex differential link and ESP32-S3 inference. It explicitly is not a released schematic. configs/electrical_reva.json transcribes proposals and keeps live/human/fabrication gates false. Vendor evidence and unresolved interfaces are in docs/REVA_VENDOR_REVIEW.md.

Main issue: current M0-R3 input is sound + upper/lower EMG (three channels, 2kHz). Rev-A raw input is PVDF + one EMG (two channels, 8kHz). Domain and preprocessing also differ. New Python/C++ contract checks block accidental reuse. No zero-filled/duplicated channel, inferred PVDF equivalence or clinical interpretation is introduced. The selected R3 model and locked M1 architecture are unchanged.

## Implemented deliverables

- Versioned little-endian data frames with bounded length, application CRC-32, signed24 ADC packing, explicit source origin, per-stream sequence and 64-bit raw timestamps.
- Fixed-capacity C++ streaming parser and Python reference; malformed lengths, corrupted bytes, fragmentation, resynchronization, explicit partial expiry and latched invalidity.
- Boot/origin/clock/rate/sequence guards, freshness check and model-input mismatch blocker. CRC recovery never automatically revalidates a segment.
- Sixteen targeted Python tests, including 30 deterministic cross-language randomized ADC frames and canonical CRC/extreme signed values; portable C++ sanitizer tests.
- A deterministic synthetic memory experiment, proposed link/RAM arithmetic, hardware work directories and disconnected bench/release traceability.
- ESP-IDF startup compiles a synthetic memory self-check; no UART/GPIO/sensor is configured. Existing simulator HAL remains a distinct post-DSP fixture.

## Calculated budget

40 paired ADC samples per5ms produce274-byte frames; optical status/motion frames40bytes at200Hz; IMU frames46bytes at200Hz. Total72,000bytes/s, 36% of a2-Mbaud8N1 ceiling, before sync/control/fault traffic. The source's51,200bytes/s estimate was raw-only. Maximum parser frame274bytes, 100ms serialized backlog7,200bytes before metadata, packed two-second dual ADC data96,000bytes. These are arithmetic budgets, not SRAM/latency/throughput measurements. No <100ms physical processing claim.

## Execution and verification status

Before interruption, sixteen targeted Python checks and portable C++ tests passed locally. The subsequent full-suite local result was not recovered and is not claimed. The execution environment later became unavailable. Source was reconstructed from the recorded changes and published via the connected GitHub interface; final source must be judged by the draft PR's actual CI results.

The CI workflow runs the complete core suite, portable C++ sanitizer checks and a60-s simulated-time memory transport experiment, retaining its aggregate JSON artifact. It also compiles the new headers into the ESP32-S3 simulator with the retained IDF/TFLM/ESP-NN dependency lock. Until the new run completes, its outcome remains pending. Synthetic frame/sample counts are not physical device measurements.

## Reproduce

python -m unittest discover -s tests -v
bash scripts/check_host.sh
python -m swallowguard.transport.simulate_reva build/reva_link_results.json --seconds 60

Use the repository's base dependency environment. Optional QAT tests need the separately pinned legacy-Keras environment. No dataset download is needed for any new test. For exact firmware dependencies, copy reports/firmware_dependencies_R3.lock to firmware/dependencies.lock, then build with IDF5.3.2 for esp32s3.

## Remaining gates / next experiment

1. Confirm exact STM32 suffix, power/AFE schematics, PixArt authorized init/logic/optics reference, connector/termination, ADC clock/filter and configuration metadata. No guessed registers or PCB fabrication outputs.
2. Verify AFE range/common-mode against ADS131M02 +/-1.2V/gain nominal span. MyoWare RAW bias is nearVIN/2; supply rails do not establish ADC full scale.
3. Implement actual HAL/drivers only against reviewed pin/config maps. Validate signal-generator/phantom capture, raw timing/CRC, missing DRDY and cable/load faults.
4. Clock synchronization/control packets, calibration metadata exchange, streaming decimation, physical quality gating, reliable SD logging and display drivers are not implemented here.
5. Obtain synchronized actual prototype data and independent validation before sensor-fed M1. M2 remains disabled; safety/ethics/clinical gates are unchanged.

Source PDF is not copied into GitHub. No patient rows, public waveform archives, trained binaries, secrets or fabricated schematic/build/performance results are added. No new large downloads or paid training.
