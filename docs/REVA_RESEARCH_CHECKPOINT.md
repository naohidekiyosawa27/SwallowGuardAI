# Current research checkpoint

25 November2026, Asia/Jakarta. Milestone04 software verification completed. Private repository naohidekiyosawa27/SwallowGuardAI, branch feat/reva-acquisition-contract, draft PR#5 stacked on draft PR#3. Current branch head must be inspected before further edits; human approval remains required before merges or fabrication.

CI-tested implementation commit b7963c0877d9e01db618d3a61c7d3cdec84ad469. Run45563812898 passed Python/host and ESP32-S3 jobs:92 passed/3 optional skips; C++ sanitizer checks passed;60-s simulated-time link experiment decoded36,000frames. Target IDF/TFLM/ESP-NN5.3.2/1.3.1/1.5.0 compiled, model unloaded, no physical execution. Final reports retain aggregate results and exact provenance. Any evidence-only follow-up does not change firmware/training/test code; read its commit description for CI scope.

Reference: user's16-page Electrical RevA.0 PDF, SHA25645a2e94a87d0b4b05f635d5b07ea7f46ae580a88c63afa567244bce0a3f81d43. It remains a draft, not released schematic. Actual RevA model input is incompatible with D4 M0-R3; never fill/duplicate the missing modality. Locked M1 architecture and M2 clinical-disabled state are unchanged.

Next work requires exact STM32 package/pin/DMA assignment and reviewed schematic/AFE/power/clock/optics interfaces, followed by disconnected signal-generator/mechanical-phantom tests. Read docs/REVA_VENDOR_REVIEW.md, REVA_WIRE_CONTRACT.md and hardware/validation/reva_release_gates.json. New high-priority findings are PixArt3.0V I/O versus3.3V host compatibility; ADC full scale/common mode; conditional sinc3 droop; PVDF mounting/loading/transients. No resistor/gain/rail/sample-rate change was released automatically.

Current local execution environment is unavailable. Use the repository and actual CI evidence; do not claim filesystem recovery, local full tests, STM32 compilation, sensor sampling, physical UART, arena/latency/power, new independent data or clinical results without measurement. If the environment returns, inspect existing files and human changes before reconciliation. Do not overwrite newer work with the pre-interruption local tree.

The user requested continuation after a possible quota reset. Quota exhaustion/reset is not observable. No automatic quota-triggered resumption or schedule has been confirmed. This durable checkpoint supports continuation on a subsequent request.
