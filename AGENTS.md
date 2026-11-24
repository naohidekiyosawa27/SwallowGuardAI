# Engineering operating instructions

1. Read README, reports/MILESTONE_01.md and docs/SPECIFICATION_TRACEABILITY.md first. User instructions take precedence.
2. Preserve RESEARCH MODE. M0 = event classification, M1 = synchronized prototype event classification, M2 = clinical risk and disabled. Never turn event probabilities into risk scores.
3. Use feature branches and descriptive commits. Open draft PRs for review. Never merge or enable auto-merge without explicit human approval. Inspect existing remote content and permissions before any push.
4. Never upload patient records, waveform datasets, restricted data, secrets or private participant mappings. Only synthetic fixtures, public source metadata and aggregate audit results belong here.
5. Verify rights, version, checksum, participant IDs, annotation meaning and signal schema before training. Ask before large downloads and paid compute. Record each approval's exact scope.
6. Split by participant before derived windows or fitted preprocessing. Keep all visits together. Fit normalization, hyperparameters and INT8 calibration using train/validation as specified; never calibrate on held-out subjects. Bootstrap participants, not windows.
7. Never pair unrelated recordings into artificial multimodal examples. Missing optical or respiratory modalities remain absent. No fabricated negative or clinical labels. Ambiguous windows are excluded explicitly.
8. Reject clipping, missing data, detached sensors, invalid tracking or timing. No physiological-looking imputation. Bench thresholds and actual transport faults must be documented.
9. No fabricated sensor registers, firmware builds, model exports, measurements, experimental performance or GitHub identifiers. Mark synthetic/replay/bench provenance on every artifact. State skipped tests and missing prerequisites.
10. Run `bash scripts/verify.sh` for relevant core changes. Use optional TensorFlow and ESP-IDF jobs only when dependencies exist; never report host compilation as a target firmware build. Verify each actual INT8 model's tensors, operators, golden vectors, memory and latency.
11. No human-connected prototype tests before independent electrical/optical/mechanical safety review, approved protocol and ethics clearance as applicable. Biofeedback requires clinician-directed research design; no automatic therapy commands.
12. Cite primary repository records and vendor documentation for software/hardware facts. Use recent peer-reviewed sources for new biomedical claims; record evidence gaps instead of inventing references.
