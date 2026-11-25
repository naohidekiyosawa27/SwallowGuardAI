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

The current source at commit b7963c0877d9e01db618d3a61c7d3cdec84ad469 passed both jobs in [GitHub Actions run45563812898](https://github.com/naohidekiyosawa27/SwallowGuardAI/actions/runs/45563812898):

- 95 Python tests run: **92 passed, 3 optional dependency skips** (TensorFlow/model-optimization dependencies are not installed in this core job). Portable C++ checks passed with undefined-behavior sanitizer. Sixteen new targeted tests include cross-language encoding/decoding.
- **60 seconds of simulated time**, deterministic in-memory experiment: 36,000 frames; 480,000 ADC pairs (960,000 scalar ADC samples), 12,000 optical and12,000 IMU sample sets;4,320,000 wire-format bytes. Corruption injection/resynchronization retained the validity block. See REVA_SYNTHETIC_LINK_RESULTS.json. Observed parser occupancy272bytes is sampled after feed chunks, not a measured peak memory/stack/RSS claim; declared frame capacity274bytes.
- **ESP32-S3 simulator target compiled successfully** under IDF5.3.2, TFLM1.3.1 and ESP-NN1.5.0 using the retained dependency lock. ESP-NN compile flag verified. Image size275,024bytes, with no model loaded. Vendor deprecation/shadowing warnings remain.
- No UART, sensor, STM32 or physical inference operation was executed. Target latency and arena remain null. A firmware image size is not model size or runtime RAM.
- Earlier sixteen targeted local tests and C++ tests passed before interruption. The final full local process result was not recovered; the local environment later became unavailable. The actual published source is verified by CI, not an invented local run.

Synthetic artifact14998109972 ZIP SHA25615a5f16f7e293e50b56b1cd253256da8358f5f41bcd4e3767662492b5bd5118a. Target build artifact15000062058 ZIP SHA256e6fbd27b992422c80fcece9780f10c02e75298b4f2e88f715ebf8dd8a8861171. Build evidence and log excerpts are retained in reports/.

## Additional electrical findings

PixArt v0.8 specifies I/O absolute maximum at VDDIO. The draft's3.0-V I/O proposal must be reconciled with a3.3-V host before wiring. ADS131M028kSPS alone does not prove a flat3-kHz passband: for the explicit HR/8.192MHz/OSR512 steady-state sinc3 assumptions, analytical gain at3kHz is about-6.334dB and filter delay187.134us. Analog/mechanical/other delays are excluded. TE LDT RevA5 fixture examples show mounting/loading sensitivity and potentially high open-circuit transients. Exact prototype response/protection is unmeasured.

Conditional calculations are in REVA_ADC_RESPONSE_ANALYTICAL.json and REVA_PVDF_LOADING_ANALYTICAL.json. They are not bench results, component selections or an approved change to the8kSPS profile. Manufacturer sources and remaining release gates are in docs/REVA_VENDOR_REVIEW.md and hardware/validation/reva_release_gates.json.

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
