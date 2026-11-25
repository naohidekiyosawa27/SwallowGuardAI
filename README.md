# SWALLOWGUARD AI Beta-03

**RESEARCH MODE — event recognition and mechanical-phantom research only.**
No clinical diagnosis, aspiration detection, swallowing-safety clearance, diet recommendation or autonomous treatment is available. M0/M1 outputs describe events, never patient risk.

Electrical follow-up: [Milestone 04](reports/MILESTONE_04.md) adds a proposed Rev-A acquisition/link contract and blocks the incompatible two-channel hardware input from the D4 three-channel model. Hardware execution remains pending. See [vendor/interface review](docs/REVA_VENDOR_REVIEW.md) and [wire ICD](docs/REVA_WIRE_CONTRACT.md).

The M0 research milestone passes the M0 numerical gate with a 5,800-byte full-INT8 bounded-QAT CNN. Validation F1 0.9391 is internal development evidence; independent confirmation and physical inference remain pending. See [Milestone 03](reports/MILESTONE_03.md), [recent AI evidence](docs/AI_RESEARCH_R3.md), [Milestone 02 saturation controls](reports/MILESTONE_02.md), [the initial pilot](reports/MILESTONE_01.md), [dataset inventory](docs/DATASETS.md), [architecture](docs/ARCHITECTURE.md), [backlog](docs/BACKLOG.md) and [safety gates](docs/SAFETY_AND_PHANTOM.md).

## Quick start

Python 3.11 or 3.12 and a C++17 compiler are required. No dataset download occurs during installation or tests.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
bash scripts/verify.sh
```

Run M0 baselines on an authorized local canonical feature table:

```bash
python -m swallowguard.train.baseline /secure/data/features.npz /secure/results/baseline.json
```

For a locally downloaded and checksum-verified D4 v2 archive:

```bash
python -m swallowguard.adapters.prepare_d4 /secure/extracted /secure/processed_clip_manifest.csv /secure/data/d4_features.npz
python -m swallowguard.train.baseline /secure/data/d4_features.npz /secure/results/d4_baseline.json
```

The feature-table workflow compares logistic regression and random forest using validation subjects and evaluates the selected candidate on held-out participants. Normalization is fitted inside the training pipeline. It reports window-level event metrics and subject-cluster confidence intervals. It does not measure continuous swallow detection, aspiration, or dysphagia.

Optional TensorFlow tools:

```bash
pip install -e '.[tinyml]'
python scripts/check_tinyml.py
python -m swallowguard.train.cnn /secure/data/waveform_windows.npz /secure/results/m0_cnn --epochs 20
```

The synthetic TinyML check verifies interfaces only. Never cite it as experimental performance. See [model protocol](docs/ML_PROTOCOL.md) for the input contract and remaining export gates.

## Repository map

| Path | Contents |
| --- | --- |
| `configs/` | Unverified sensor targets, DSP candidates and model shapes |
| `datasets/registry.json` | Machine-readable rights/access and verification status |
| `datasets/cards/` | Source-specific data cards and label limitations |
| `datasets/evidence/` | Public metadata evidence and aggregate manifest audit |
| `src/swallowguard/adapters/` | Strict D2/D4 loaders and guarded HRCA array contract |
| `src/swallowguard/preprocess/` | Filtering, resampling, alignment, segmentation, quality |
| `src/swallowguard/train/` | Subject splits, M0 baselines/CNN, gated M1 candidate |
| `src/swallowguard/evaluate/` | Confusion matrices and participant-cluster bootstrap |
| `src/swallowguard/export/` | INT8 conversion, tensor/operator audit, float parity |
| `firmware/` | ESP-IDF simulated acquisition and host-testable C++ core |
| `tests/` | Synthetic fixtures and behavioral/integration checks |
| `.github/workflows/` | Python/host/ESP-IDF CI and optional TinyML check |
| `models/cards/` | Model scope, numerical acceptance and remaining validation gates |
| `reports/` | Actual execution evidence and benchmark status |

No patient records, waveforms, credentials or restricted archives belong in GitHub. Downloaded research files and intermediate artifacts are excluded by `.gitignore`. Code licensing remains an owner decision; dataset licenses do not license this code automatically.
