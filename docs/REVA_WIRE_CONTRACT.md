# Rev-A proposed head-to-controller ICD v1

Status: executable software proposal, not an approved schematic, STM32 firmware or physical UART driver. RESEARCH MODE. No patient connection. Origin must remain synthetic for the provided experiment. No record from another participant may fill a missing modality.

## Frame layout

All numeric fields and payload scalars are little-endian. Byte order differs from some sensor SPI/I2C words; the acquisition driver must explicitly translate. No packed C struct casts or alignment assumptions.

| Offset | Bytes | Field |
| --- | ---: | --- |
| 0 | 2 | Magic ASCII SG |
| 2 | 1 | Schema version 1 |
| 3 | 1 | Kind: 1 ADC pair, 2 optical, 3 IMU |
| 4 | 2 | Origin bits 0..1; quality fault bits 2..5 |
| 6 | 4 | Boot/session identifier |
| 10 | 4 | Per-kind sequence, modulo 2^32 |
| 14 | 8 | First sample head timestamp, microseconds |
| 22 | 4 | Sample interval, microseconds |
| 26 | 2 | Number of simultaneous sample sets |
| 28 | 2 | Payload bytes |
| 30 | variable | Payload |
| end-4 | 4 | Application CRC-32/ISO-HDLC, little-endian |

Application CRC uses reflected polynomial 0xEDB88320, initial/final XOR 0xFFFFFFFF; CRC("123456789")=0xCBF43926. It covers header and payload. It is NOT the ADS131M02 SPI CRC, a cryptographic MAC, authentication, or an electrical isolation mechanism. Sensor CRC must be checked independently before packing.

Origin: 0 synthetic, 1 research replay, 2 live disconnected bench; 3 invalid. Fault bits: bit2 acquisition invalid; bit3 sensor-CRC fault; bit4 saturation; bit5 timing fault. Bits6..15 are reserved and rejected. Provenance metadata is not proof of authenticity. All fault bits block segment validity. Optical status is a separate opaque unsigned16 field pending verified vendor semantics.

| Kind | Payload per sample set | Interval | Allowed sets/frame |
| --- | --- | ---: | ---: |
| ADC pair | PVDF signed24 + sEMG signed24 | 125 us | 1..40 |
| Optical | signed16 dx, signed16 dy, unsigned16 raw status | 5000 us | 1 |
| IMU | signed16 ax, ay, az, gx, gy, gz | 5000 us | 1 |

The proposed optical widths require confirmation against the exact vendor register format. Signatures/counts do not establish calibrated units. ADC output codes are not assumed volts, pressure is not assumed flow, and no raw status bit meaning is invented.

Maximum payload 240 bytes and maximum frame 274 bytes. Python/C++ implementations reject oversized lengths, invalid types/rates/counts/flags, timestamp interval overflow, CRC failures and trailing bytes. C++ parser storage is fixed-size. Garbage and corrupted frames can be resynchronized, but validity remains latched false. Error counters count rejected bytes/header attempts, not a measured physical packet-loss rate. Truncation needs a caller-managed timeout invoking expire_partial(); no physical timer driver is implemented.

## Session and clock contract

The receiver explicitly selects a new boot ID and origin at segment creation. Do not automatically accept a boot-ID change: close/flush the old segment, record a reset and explicitly begin a new one. A boot ID must not be reused while old packets may remain; no persistent/random boot-ID implementation is provided. Sequence starts at any observed first value per kind and must then be contiguous modulo 2^32. First timestamp after the first packet must equal the previous end-exclusive time. Duplicate, lost, reordered, reset-origin or temporal-discontinuity records invalidate the segment.

Timestamps are first sample DRDY observations in the head's own clock, not arrival time or physiological onset. The local MCU must extend any finite timer counter to the specified 64-bit representation. Period 125 us is a nominal contract and does not prove oscillator accuracy. Timing drift, ADC digital-filter delay and pneumatic delay need recorded calibration. fit_clock() exists for paired common triggers, but physical synchronization, sync-command messages, delay compensation and timebase negotiation are NOT implemented by this data-only codec.

healthy() requires all three head streams and compares freshness against each last sample on the SAME head clock. Default 20 ms staleness is a proposed software bench threshold, not an accepted physiological/safety tolerance. Parser faults must be passed into SegmentGuard; recovery alone cannot clear them. No interpolation over dropped samples or silent re-stamping is permitted.

## Calculated budget, not a physical measurement

Proposed operating profile: one 40-pair ADC block every 5 ms, one optical frame and one IMU frame every 5 ms.

| Stream | Frame bytes | Frames/s | Bytes/s |
| --- | ---: | ---: | ---: |
| ADC pair | 274 | 200 | 54,800 |
| Optical, including raw status | 40 | 200 | 8,000 |
| IMU | 46 | 200 | 9,200 |
| Total | | | 72,000 |

2 Mbaud 8N1 has a 200,000-byte/s line ceiling; this profile consumes 36%, before sync/control traffic, retransmissions and fault logs. Unlike the brief's 25.6% raw-only estimate, this includes the chosen framing and optical status width. Neither number proves sustained operation. ADC batching adds up to a 5-ms assembly interval and serialization of a 274-byte frame takes 1.37 ms at the proposed baud. Scheduling, queue contention and cable integrity remain unmeasured.

100 ms of serialized stream bytes requires 7,200 bytes before queue metadata/margins. Two seconds of packed dual-channel 8-kSPS ADC values requires 96,000 bytes before timestamps/metadata. Do not size a queue by scalar Sample objects without accounting for their actual sizeof(), buffering copies and acquisition/SD concurrency. No tensor-arena or physical SRAM measurement is inferred from these arithmetic budgets.

## Reproduce and boundaries

python -m swallowguard.transport.simulate_reva /secure/results/reva_link.json --seconds 60

This is a deterministic in-memory workload and corruption injection, not a real-time UART benchmark. Host tests exercise the same portable decoder. Firmware startup compiles a synthetic in-memory self-check only; no UART/pin/register is initialized. The old simulated HAL still represents its prior post-DSP rates; it is not an ADS131M02 8-kSPS driver.

The D4 M0-R3 input is throat sound + upper/lower EMG at 2 kHz, 4000 points. Rev-A is PVDF + one EMG at 8 kHz raw. model_input_contract.hpp and transport/model_contract.py reject mismatched channels, rate, window, domain or preprocessing. Exact metadata matches are necessary only; model acceptance and independent quality gates are still required. No duplicated/zero-filled EMG, microphone-to-PVDF equivalence or prototype performance is asserted. A disconnected synthetic model benchmark remains possible through the separate R3 bench protocol.

Parser and guard objects are single-owner components; do not share a mutable instance across RTOS tasks without external synchronization. A transport-ready segment remains distinct from physically valid calibrated data. A stale/partial receive timeout also requires a real caller-managed reference clock; that hardware integration is pending.
