# Research safety and mechanical-phantom plan

Current scope: mechanical phantom, simulator, authorized public-data replay and non-human bench metrology. This document is an engineering plan, not a medical-device conformity assessment or clinical permission. No human testing is authorized by the current workspace.

## Gates

| Gate | Required evidence | Current disposition |
| --- | --- | --- |
| G0 dataset | Rights, checksums, real schema, IDs, labels and subject split | Dataset-specific status in inventory/report |
| G1 optical bench | Reference displacement encoder, calibrated travel, standoff/reflectance sweeps, hysteresis, speed/dropout | Not measured |
| G2 acquisition | Common trigger, actual rates/jitter, skew, filtering delay, clipping and cable integrity | Simulation tests only |
| G3 TinyML | Exact INT8 parity/operators/golden vectors, target memory and p50/p95 latency | Target unmeasured |
| G4 safety | Independent optical/electrical/mechanical/battery/material/infection-control review | Not performed |
| G5 human research | Clinical partner, approved protocol, ethics and consent/data controls, specified references | Not approved |

## Phantom experiments

1. Use a displacement stage/encoder and compliant mechanical target. Sweep motion amplitude/speed and the PDF's provisional standoff/travel assumptions; record reference trace and optical counts with common trigger. Assess bias, repeatability, hysteresis, tracking dropout and contact loading.
2. Apply calibrated vibration with a reference accelerometer and impedance/AFE measurement. Sweep amplitude/frequency, ADC saturation, noise and mounting conditions. Establish PVDF passband from measurements instead of assuming throat sounds and PVDF are interchangeable.
3. Inject an isolated electrical simulator into the EMG acquisition chain. No electrodes are attached to a person. Verify AFE gain, bandwidth, clipping, noise and saturation recovery.
4. Apply controlled pneumatic waveforms with a reference pressure standard. Evaluate leaks, offsets and response; derive flow only if an actual validated pressure-flow interface is present.
5. Move the phantom with controlled inertial disturbances and cable perturbations. Exercise sensor disconnects, dropped samples, drift and SD stalls; confirm invalid measurement without substituted signals or clinical output.
6. Record all instrument IDs/calibration dates, fixtures, settings, firmware/model hashes and repetitions. Predefine acceptance limits after instrument uncertainty analysis and before comparative tests. Report failures and excluded segments explicitly.

## Risk controls

External motion is not internal laryngeal motion. Microphone-to-PVDF and laboratory-to-primary-care shifts require new evidence. Enclose optical emissions; no laser class/eye-safety claim is made. Review neck contact force/fit and emergency removal. Hobby EMG hardware, USB connections and batteries need independent electrical safety review before any human connection. Public-data replay cannot establish rehabilitation efficacy or disease detection.

Potential standards applicability must be determined by qualified medical-device specialists for the final intended use; this workspace does not assert certification or regulatory clearance. Human clinicians retain clinical decisions; repository review retains merges and architectural changes.
