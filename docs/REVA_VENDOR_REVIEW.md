# Electrical Rev-A evidence review

25 November 2026. Source is the user's 16-page Rev A.0 draft, SHA256 45a2e94a87d0b4b05f635d5b07ea7f46ae580a88c63afa567244bce0a3f81d43. Text and architecture/optical/link/GPIO figures were inspected before workspace interruption. No full proprietary datasheet or uploaded PDF is redistributed in this repository.

## Verified source pointers and engineering consequences

| Device | Primary technical source inspected | Consequence / remaining gate |
| --- | --- | --- |
| ADS131M02 | TI SBAS853A Rev A, April 2021; product/data-format sections, https://www.ti.com/lit/ds/symlink/ads131m02.pdf | Simultaneous 24-bit channels; full-scale differential +/-1.2 V/gain. Raw 0..3.3 V is not an ADC full-scale assumption. Check common-mode, gain, reference, anti-aliasing and SPI CRC independently. No board calibration is established. |
| MyoWare 2.0 | Manufacturer specs, https://myoware.com/Products/Technical-Specifications/ and supplier ecosystem guide https://learn.sparkfun.com/tutorials/getting-started-with-the-myoware-20-muscle-sensor-ecosystem/all | RAW is biased near VIN/2; manufacturer lists RAW gain200 and nominal 20.8/498.4-Hz filtering. ENV is not RAW. At 3.3 V, midrail is about 1.65 V; buffering/attenuation/common-mode need schematic analysis, not a direct ADC connection. No electrode connection is enabled. |
| MAX3490 | Analog Devices 19-0333 Rev2, May2024, https://www.analog.com/media/en/technical-documentation/data-sheets/max3483-max3491.pdf | 3.3-V full-duplex 10-Mbps part supports considering 2-Mbaud UART. MAX3488 is a 250-kbps full-duplex variant, not a drop-in speed equivalent. Receiver open-circuit failsafe does not establish every cable fault or patient isolation. Termination/EMC tests remain open. |
| ESP32-S3-WROOM-1 N16R8 | Manufacturer module datasheet v1.8, https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf | IO35/36/37 unavailable on Octal-PSRAM variants. Proposed GPIOs are transcribed separately, never activated. USB, strapping, debug/JTAG, module-pad numbers and boot states still require schematic review. |
| STM32G0B1 | ST DS13560 Rev6, Feb2026, https://www.st.com/resource/en/datasheet/stm32g0b1rb.pdf | Family supports up to64MHz and 144KB SRAM; exact package/peripheral/DMA assignment remains TBD. No STM32 target build or exact suffix is claimed. A family resource listing does not establish board timing. |
| BMI270 | Bosch BST-BMI270-DS000-08 rev1.6, March2026, https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi270-ds000.pdf | Manufacturer source located/opened. Pin/rail/init configuration, firmware API revision and axis calibration must be verified before live acquisition. No register sequence is invented. |
| SDP31 | Manufacturer product page, https://sensirion.com/products/catalog/SDP31 | +/-500 Pa differential-pressure part. Exact digital-datasheet command/CRC/scale handling not implemented in this milestone. Pressure remains pressure, not calibrated airflow. Pneumatic delay/condensation tests remain open. |
| PixArt PAA5163E1-QV22 | Manufacturer-authored document hosted by CODICO, v0.8, 21Jun2024, https://www.codico.com/en/mpattachment/file/download/id/1398/ | Distributor-hosted reference, not an independent clinical source. Exact init map, logic-level paths, optics, containment and footprint remain release gates. No copyrighted document redistribution or guessed register writes. |
| LDT0-028K / OPA320 / OPA2320 / BQ24074 / regulators | Candidates transcribed from uploaded draft; exact applicable datasheet/suffix and complete circuit not verified here | Do not describe AFE or power design as approved. Measure PVDF capacitance/response, derive gain/stability/anti-aliasing and calculate worst-case current, cable drop, sequencing/back-power and protection before choosing values/MPNs. |

## Blocking findings

1. **Model-to-hardware mismatch:** D4-R3 is three channels (sound + upper/lower EMG); Rev-A has two ADC channels (PVDF + one EMG). Resampling does not create the missing muscle measurement or prove transducer transfer. Keep current sensor-fed inference blocked. Retain the independent synthetic model bench.
2. **AFE headroom:** at gain1 the ADC differential span is nominally +/-1.2 V, not the power rail. At gain32 it is nominally +/-37.5 mV (calculated). Check amplifier outputs and ADC common mode at all rails/faults. Preserve ADC counts and calibration metadata; no component-value or effective-resolution result is claimed.
3. **Transport budget:** the executable proposed profile is 72,000 bytes/s including application framing (36% of 2-Mbaud 8N1), compared with the draft's 51,200 raw bytes/s. Both omit some implementation traffic; neither is measured throughput.
4. **Acoustic bandwidth:** Rev-A proposes 8-kSPS PVDF acquisition, whereas D4 M0 is resampled to2kHz. Preserve high-rate raw data; any conversion to an M0 representation needs verified antialiasing, group-delay accounting and new domain evidence. No streaming decimator is implemented here.
5. **Proposed vs released hardware:** pin table, MCU suffix, display controller, AFE component values, regulator MPNs, clock tree and calibration remain unresolved. The user-provided draft guides software interfaces; it does not provide an ERC/DRC-approved circuit.

The AI evidence review remains docs/AI_RESEARCH_R3.md. No new journal performance claim is transferred to hardware. Engineering electrical facts use manufacturer references; current medical safety/clinical validation is not asserted.

## Next disconnected bench acceptance

Use the uploaded T01-T14 table as traceability, not pass results. In order: exact BOM/schematic/rail review; current-limited unconnected power bring-up; digital evaluation-board capture; signal-generator/phantom AFE sweep; measured ADC DRDY/clock/group delay; cable fault and sustained-load tests; logging under concurrent UI/inference; then independent safety review. Human-connected work remains forbidden. Close numerical acceptance criteria with the responsible electrical engineer before collecting real bench evidence.
