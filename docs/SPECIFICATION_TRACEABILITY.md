# Specification traceability and decisions

Primary file actually supplied: `SWALLOWGUARD_AI_Technical_Design_Brief(1).pdf`, 10 pages, Beta-03 dated 25 November 2026. It was read locally in full. The requested Work/GitHub PDF and Markdown were searched by exact names and a simplified title query but were not found. Their content is not assumed. The supplied PDF still refers to an earlier Antigravity handoff; this workspace follows the user's newer Work/GitHub instruction.

| Requirement | Implementation/evidence | Status |
| --- | --- | --- |
| Research-only M0/M1; M2 disabled | contracts.py, C++ ResearchDecision, tests | Implemented in current interfaces |
| Dataset rights and access | registry.json and D1-D4 metadata | Verified metadata; file-level status in report |
| Participant split | train/splits.py; train-only scaler; tests | Implemented |
| Five modalities | hardware.json, SimulatedHAL | Virtual acquisition; real drivers blocked |
| DSP and quality | preprocess/ | Candidate software; calibration pending |
| Intermediate fusion | models.py m1_candidate | Candidate only; paired device data missing |
| INT8 inference | export/int8.py, optional tflm_candidate.hpp | Execution status in report; no target measurements |
| ESP32-S3 acquisition | firmware/main/app_main.cpp | Simulator; ESP-IDF build status in report |
| TFT, SD, biofeedback | documented interfaces | Hardware integration pending |
| Laboratory phantom evaluation | SAFETY_AND_PHANTOM.md | Protocol, no measurements |
| Feature branches and draft PR | GITHUB_HANDOFF.md | Private repository and permissions verified; feature-branch handoff |

Locked architecture is retained. D4 v2 is an M0 data candidate, never a surrogate for the five-sensor prototype. D3 was downgraded from an apparently open shortlist item to restricted/internal access after reading its API rights. The user explicitly approved the 1,506,737,987-byte D4 processed-clips download during this session. This does not approve other large datasets, paid compute, merges or clinical work.

Milestone 02 preserves the locked M1 architecture. Additional Dense/sigmoid exports are conventional M0 numerical comparators only; none passed the preregistered engineering tolerances, and none changes the deployed/reference model. Both predeclared and follow-up protocols and all negative trials are retained.
