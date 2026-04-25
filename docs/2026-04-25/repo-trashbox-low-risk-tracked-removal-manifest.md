# Repo Trashbox Low-Risk Tracked Removal Manifest

Date: 2026-04-25
Status: final - manifest complete; no tracked removal performed
Canonical Path: `docs/2026-04-25/repo-trashbox-low-risk-tracked-removal-manifest.md`
Governing SSOT: `docs/2026-04-24/repo-trashbox-cleanup-execution-ssot.md`
Baseline Commit: `bcbe0955a53b57d0e44953ace2db54ffadffc651`
Baseline Dirty Summary: `clean branch feat/repo-trashbox-low-risk-removal-manifest opened from main after PR #19 packaging scope merge`

## 1. Question

Can the lowest-risk tracked repo residue be made reviewable for a future deletion PR without touching production runtime, formal tests, active queue mirrors, or canary cleanup scope?

## 2. Verdict

Yes. The tracked removal set below is low-risk enough for a dedicated follow-up PR, provided that the PR uses `git rm` for exactly the listed paths and does not bundle broader repo cleanup.

This document does not authorize or perform removal. It only freezes the removal candidate set and validation contract.

## 3. Removal Set

| Candidate | Tracked files | Bytes | Reference finding | Future action |
| --- | ---: | ---: | --- | --- |
| `MagicMock/` | 2 | 792 | Docs/config/test-contract references only; no runtime dependency on root `MagicMock/` path found | tracked-remove |
| `tmp_stage2_digest_debug/` | 6 | 386870 | Docs/config references only; packaging and ignore scope already cover future residue | tracked-remove |
| `rlhf_data/test_project/` | 6 | 2680 | Generated test-project feedback data; no production runtime reference found | tracked-remove |
| `datasets/test_project/` | 3 | 42042 | Historical survey/docs reference only; generated approved test-project artifacts | tracked-remove |
| `crash_dump.log` | 1 | 2267 | `main_a.py` may recreate root crash log dynamically; tracked seed file is not required | tracked-remove |
| `error.log` | 1 | 746 | Runtime fallback is `logs/error.log`, not tracked root `error.log` | tracked-remove |
| `test_results.xml` | 1 | 191256 | Packaging excludes this result file; no runtime dependency found | tracked-remove |
| `tmp_project_00.db` | 1 | 876544 | Local temporary DB residue; no runtime dependency found | tracked-remove |

Total: 21 tracked files, 1503197 bytes.

## 4. Exact Tracked Paths

```text
MagicMock/mock.current_project.paths.root/1384832399024/logs/soft_failures.jsonl
MagicMock/mock.current_project.paths.root/2930521814512/logs/soft_failures.jsonl
tmp_stage2_digest_debug/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json
tmp_stage2_digest_debug/logs/pass_rate_monitor.json
tmp_stage2_digest_debug/logs/runtime_audit.jsonl
tmp_stage2_digest_debug/logs/runtime_audit_summary.json
tmp_stage2_digest_debug/logs/session/decisions.jsonl
tmp_stage2_digest_debug/project_data.db
rlhf_data/test_project/feedback_ep_001.json
rlhf_data/test_project/feedback_ep_002.json
rlhf_data/test_project/rlhf_data_20260128_223108.jsonl
rlhf_data/test_project/rlhf_data_20260128_223122.jsonl
rlhf_data/test_project/rlhf_data_20260128_224804.jsonl
rlhf_data/test_project/rlhf_data_20260128_230826.jsonl
datasets/test_project/approved/ep_001_approved.json
datasets/test_project/approved/ep_001_approved_20260128_224804.json
datasets/test_project/approved/ep_001_approved_20260128_230826_766_afa66f20.json
crash_dump.log
error.log
test_results.xml
tmp_project_00.db
```

## 5. Guardrails For The Future Removal PR

- Use `git rm -- <paths>` for the exact tracked paths listed above.
- Do not use filesystem-only deletion for tracked files.
- Do not touch `test_mode/`, `lite_mode/`, `spikes/`, `projects/_canary/`, `tests/`, or `docs/temp/`.
- Do not change `main_a.py` crash-dump behavior in the removal PR.
- Do not change the `logs/error.log` runtime fallback.
- Do not create or commit a trashbox holding directory.
- If the user asks for a local archival copy, verify the absolute destination first and keep that copy outside the committed PR.

## 6. Validation Contract

Future removal PR validation should include:

- `git status --short`
- scoped `rg` reference scans for the removed roots and root files
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`
- `python scripts/check_utf8_hygiene.py docs/2026-04-25/repo-trashbox-low-risk-tracked-removal-manifest.md docs/2026-04-24/repo-trashbox-cleanup-execution-ssot.md docs/2026-04-24/active-temp-execution-roadmap.md docs/temp/repo-trashbox-cleanup-execution-ssot.md docs/temp/execution-roadmap.md docs/temp/queue-state.json`
- `python -m pytest tests/test_surface_containment_contract.py tests/test_runtime_authority_contract.py -q`

## 7. Pass 1 - Inventory Check

The candidate set was limited to small, already-identified residue surfaces. Large maintenance-mode trees such as `test_mode/`, `lite_mode/`, and `spikes/` remain outside this manifest.

Pass 1 result: pass.

## 8. Pass 2 - Reference Check

Scoped reference scans found docs/config/test-contract references for the candidate roots and result files. Runtime-sensitive findings are bounded to dynamic recreation behavior for `crash_dump.log` and the separate `logs/error.log` fallback, neither of which requires the tracked root artifact files to stay in Git.

Pass 2 result: pass.

## 9. Pass 3 - Side-Effect Check

The follow-up removal shape is reviewable because it removes only tracked residue, does not rewrite history, does not change runtime code, and remains reversible by reverting the removal PR.

Pass 3 result: pass.

Confidence: 96/100
