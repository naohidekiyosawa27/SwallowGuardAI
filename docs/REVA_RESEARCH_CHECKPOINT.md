# Current research checkpoint

Date: 25 November 2026 (Asia/Jakarta). Base fa4826cf9506e404112479ea9a15b9abeca32b65, draft PR #3; work branch feat/reva-acquisition-contract. Main and earlier draft PRs are not merged by the agent.

The 16-page electrical Rev A.0 source was read locally before the execution environment became unavailable; SHA256 45a2e94a87d0b4b05f635d5b07ea7f46ae580a88c63afa567244bce0a3f81d43. User authorizes it as an engineering reference. It explicitly remains a draft, with proposed STM32G0B1, ADS131M02 and MAX3490. Final package suffix/pin mapping, AFE, schematic/ERC, PCB/DRC and bench safety remain pending. No final schematic or release is fabricated.

New work: portable Python/C++ binary codec, bounded streaming decoder, continuity/provenance guards, M0 input-contract blocker, proposed hardware manifest and synthetic link experiment. Sixteen targeted Python tests and portable C++ tests passed earlier locally before interruption. The final full local test process result could not be recovered; it is not claimed. Reconstructed/published source must be tested in CI. Runtime execution environment is currently unavailable; use GitHub Actions for actual source checks and target compilation.

Next: read draft PR checks, fix any observed failures, preserve actual synthetic aggregate report, validate target build including new headers, and update the milestone with exact commit/run IDs. Do not claim physical UART, STM32 build, ADC sampling, hardware inference or clinical validation. Default remains simulated and model unloaded. No large dataset download, paid training or patient connection is authorized.

If interrupted, resume from current branch head, inspect human changes before editing, read AGENTS.md and this checkpoint. Keep firmware/model architecture unchanged unless the owner explicitly approves a major change.

Usage-note: the user requested continuation after a possible quota reset. Quota exhaustion/reset is not observable here. No automatic quota-triggered continuation has been confirmed; no schedule should be claimed without an actual successful scheduling result.
