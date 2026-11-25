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
| AFE/power component implementation | Candidate parts transcribed; follow-up manufacturer references below; exact suffixes/complete circuit/regulators still unresolved | Do not describe AFE or power design as approved. Measure PVDF capacitance/response, derive gain/stability/anti-aliasing and calculate worst-case current, cable drop, sequencing/back-power and protection before choosing values/MPNs. |

## Blocking findings

1. **Model-to-hardware mismatch:** D4-R3 is three channels (sound + upper/lower EMG); Rev-A has two ADC channels (PVDF + one EMG). Resampling does not create the missing muscle measurement or prove transducer transfer. Keep current sensor-fed inference blocked. Retain the independent synthetic model bench.
2. **AFE headroom:** at gain1 the ADC differential span is nominally +/-1.2 V, not the power rail. At gain32 it is nominally +/-37.5 mV (calculated). Check amplifier outputs and ADC common mode at all rails/faults. Preserve ADC counts and calibration metadata; no component-value or effective-resolution result is claimed.
3. **Transport budget:** the executable proposed profile is 72,000 bytes/s including application framing (36% of 2-Mbaud 8N1), compared with the draft's 51,200 raw bytes/s. Both omit some implementation traffic; neither is measured throughput.
4. **Acoustic bandwidth:** Rev-A proposes 8-kSPS PVDF acquisition, whereas D4 M0 is resampled to2kHz. Preserve high-rate raw data; any conversion to an M0 representation needs verified antialiasing, group-delay accounting and new domain evidence. No streaming decimator is implemented here.
5. **Proposed vs released hardware:** pin table, MCU suffix, display controller, AFE component values, regulator MPNs, clock tree and calibration remain unresolved. The user-provided draft guides software interfaces; it does not provide an ERC/DRC-approved circuit.

The AI evidence review remains docs/AI_RESEARCH_R3.md. No new journal performance claim is transferred to hardware. Engineering electrical facts use manufacturer references; current medical safety/clinical validation is not asserted.

## Next disconnected bench acceptance

Use the uploaded T01-T14 table as traceability, not pass results. In order: exact BOM/schematic/rail review; current-limited unconnected power bring-up; digital evaluation-board capture; signal-generator/phantom AFE sweep; measured ADC DRDY/clock/group delay; cable fault and sustained-load tests; logging under concurrent UI/inference; then independent safety review. Human-connected work remains forbidden. Close numerical acceptance criteria with the responsible electrical engineer before collecting real bench evidence.

## Follow-up component and filter findings

- PixArt v0.8 p9 absolute-maximum table lists I/O upper voltage as VDDIO, not VDDIO+0.3V. With the draft's3.0-V I/O rail, directly applying a3.3-V host output is outside that listed limit. Resolve the rail/translation/sequence design before connecting SPI/reset/IRQ; no automatic power-rail change is made. Core VDD remains a separate1.8-2.1V domain. The manufacturer's table was visually checked.
- TI Table8-2 supports8kSPS with HR mode,8.192-MHz master clock and OSR512. Under the regular steady-state sinc3 model, calculated gain at3kHz is0.4823 (-6.334dB), and digital-filter group delay is187.134us. This excludes analog filters, mechanics, extra phase calibration/global chop and reset fast-settling. It is NOT a measured response or the complete system delay. Do not select a new sample rate or equalizer automatically; define fidelity requirements and characterize the actual chain. Formula and assumptions are in reports/REVA_ADC_RESPONSE_ANALYTICAL.json.
- TI OPAx320 SBOS513F RevF (Dec2016), https://www.ti.com/lit/ds/symlink/opa320.pdf : single/dual low-bias RRIO candidates operating at1.8-5.5V. Exact suffix, charge-amplifier stability, input protection, bias and ADC drive still require a complete circuit.
- TI BQ2407x SLUS810N RevN, https://www.ti.com/lit/ds/symlink/bq24074.pdf : BQ24074 is a linear PowerPath charger supporting up to1.5A, not a boost regulator or a patient-isolation design. Do not assume SYSOFF functionality listed for other family variants. Set input/charge limits and evaluate dissipation, pack/NTC protection and interlock separately.
- TE manufacturer description https://www.te.com/en/product-CAT-PFS0006.html and linked LDT with Crimps datasheet RevA5 (June2025) were inspected. Its fixture examples include a resonance near180Hz without added mass and about7V open-circuit equivalent at2mm deflection; these are not our measurements. Its480pF typical electrical-loading example gives an ideal high-pass corner near332Hz at1Mohm. Exact delivered part/capacitance and in-assembly response remain unmeasured. AFE protection, impedance and saturation recovery cannot be selected from an assumed flat microphone response. Illustrative calculations, not component selections, are in reports/REVA_PVDF_LOADING_ANALYTICAL.json.

For the digital-filter calculation, with R=512, fMOD=4.096MHz and fDATA=8kHz:
H(f)=[sin(pi*f/fDATA)/(R*sin(pi*f/fMOD))]^3;
group delay=3*(R-1)/(2*fMOD).
These are conditional discrete-filter arithmetic, not a new physiological or clinical claim.
