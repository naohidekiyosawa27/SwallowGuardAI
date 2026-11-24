# GitHub engineering handoff

Repository: https://github.com/naohidekiyosawa27/SwallowGuardAI

Repository ID: 1470607768. Visibility was verified as private after the owner changed it. The authenticated user naohidekiyosawa27 has admin/push/pull access. Default branch: main. The inspected initial main commit is fae6c3044da8da722af323eb4e6b3227d5775557, containing only the original title README. No existing engineering files or AGENTS instructions were present remotely.

The engineering foundation is prepared for feature branch feat/beta03-foundation-data-audit. Documentation/data audit and implementation/tests are separate descriptive commits. Actual commit IDs, draft PR and CI checks are recorded by GitHub and reported to the owner after the operations complete. No default-branch merge or auto-merge is authorized.

## Review scope

- Source code, synthetic fixtures, public dataset metadata and aggregate pilot results only.
- No waveform archives, per-participant rows, credentials, trained binary weights or serialized models are uploaded.
- RESEARCH MODE remains enabled; M2 and clinical outputs are disabled.
- Local evidence: 49 Python tests and portable C++ tests passed. Target firmware/CI results must be taken from the actual GitHub run; local host compilation is not an ESP-IDF build.
- CNN INT8 candidate has a measured parity outlier and is not accepted for deployment. Random forest remains the validation-selected conventional M0 reference.
- The two specifically named Work/GitHub specification files remain missing; the supplied Beta-03 PDF is the specification used.

## Next review

Review the draft PR and automated checks, reconcile missing specifications, resolve INT8 range/outlier behavior on independent validation data, and perform actual hardware/phantom metrology. Human approval remains required before merging or clinical work.
