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

## Stacked research continuation

Milestone 02 is prepared on feat/m0-quantization-abstention. The owner merged PR #1 during this research session; observed main is d666940924bd3e2e568c35170f2739d1f07c0453, with the same foundation tree 606542ed5e549c61ac96763e0dae967ae7221077. The research branch is based on that main commit and its draft PR targets main. No research PR merge is authorized or automated. New source contains only aggregate results and synthetic fixtures, not raw waveforms or model binaries.

## Milestone 03 review

Draft PR #3: https://github.com/naohidekiyosawa27/SwallowGuardAI/pull/3, branch `feat/m0-bounded-qat`, stacked on the still-open draft PR #2. Initial implementation commit `e45daf1f1f8020bbc42d44dd4648a179accfa3d8`. Its 122 remote source blobs matched local hashes. Python/host CI run `45470279058` passed with 76 tests passed and 3 optional tests skipped; local isolated QAT suite passed all 79. Target CI also passed: IDF 5.3.2, TFLM 1.3.1, ESP-NN 1.5.0 and ESP-NN compile flag found. Retained dependency lock and JSON evidence are in reports/. This confirms compilation only; physical invocation remains unmeasured. No default-branch merge is authorized.

Selected trained model and synthetic replay package are delivered privately outside GitHub. Public metadata, source code and aggregate results only are present in the repository. `reports/MILESTONE_03.md` separates numerical acceptance from independent/hardware/clinical validation.
