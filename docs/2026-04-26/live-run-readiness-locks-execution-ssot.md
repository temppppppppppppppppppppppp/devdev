# Live Run Readiness Locks Execution SSOT

Date: 2026-04-26
Status: closed
Canonical Path: `docs/2026-04-26/live-run-readiness-locks-execution-ssot.md`
Temp Mirror Path: removed at closure
Commit State:
- Baseline Commit: `05964ee2702ac7d128805ca49e9b1f45cc0f2d4e`
- Baseline Dirty Summary: `clean`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- inline parallel P0-P3 live-run readiness deep dive on 2026-04-25 and 2026-04-26
Evidence Artifacts:
- live code evidence from `modules/api/process_runner.py`
- live code evidence from `modules/api/bridge_server.py`
- live code evidence from `scripts/run_stage2_canary.py`
- live code evidence from `scripts/run_stage3_canary.py`
- live code evidence from `scripts/run_stage4_canary.py`
- live code evidence from `scripts/run_stage34_canary.py`
- live code evidence from `scripts/run_stage34_ep_demo_canary.py`
- live code evidence from `scripts/run_stage4_direct_supervised_guarded.py`
- live code evidence from `scripts/canary_semantic_exit.py`
Side-Effect Coverage: covered

## 1. Intent

Before any fresh live run, close the blocking runtime-readiness gaps that can make the operator believe a run is safe or complete while the process is hung, stopped unclearly, or semantically failed.

This document authorizes a bounded implementation wave only for:
- concurrent stderr draining and better stop diagnostics in the bridge `ProcessRunner`
- prompt broker cleanup on stop
- canary/direct script semantic exit codes that fail when hard gates or guarded summaries fail

## 2. Baseline Facts

- `ProcessRunner` starts child processes with both stdout and stderr piped.
- Runtime stdout is drained live, but stderr is currently read after stdout EOF, which can deadlock if stderr fills its pipe.
- `/stop` clears runner state and emits an empty `run_stopped` event, while prompt broker cleanup currently happens only on normal exit.
- `run_stage*canary.py` scripts can return process exit code `0` even when their JSON payload reports hard gate failure or partial evidence.
- The prior P0 Stage 4 rejected `last_best` adoption issue is already closed in `05964ee2` and is not in scope here.

## 3. Scope

Included:
- `modules/api/process_runner.py`
- `modules/api/bridge_server.py`
- `scripts/run_stage2_canary.py`
- `scripts/run_stage3_canary.py`
- `scripts/run_stage4_canary.py`
- `scripts/run_stage34_canary.py`
- `scripts/run_stage34_ep_demo_canary.py`
- `scripts/run_stage4_direct_supervised_guarded.py`
- directly related tests

Excluded:
- artifact byte-truth and content-addressed artifact snapshot naming
- runtime audit freshness/session-cache lineage hardening
- Director-positive verdict re-adjudication policy
- broad desktop shutdown process-tree behavior
- full fresh live run execution

## 4. Pass 1. Inventory Summary

- Process runner hotspot: `stderr=asyncio.subprocess.PIPE` plus deferred `proc.stderr.read()` in the stdout read-loop finalizers.
- Stop hotspot: direct child terminate/kill only, no stop payload diagnostics, no prompt broker cleanup on `/stop`.
- Canary hotspot: `main()` paths return `0` after `run_canary()` regardless of payload hard-gate status.
- Guarded direct hotspot: summary payload can mark operational failure while process returns `0`.

## 5. Pass 2. Semantic Classification

- Class A, process safety: stderr must be drained concurrently with stdout so subprocess liveness cannot block on an unread pipe.
- Class B, operator truth: stop events must preserve compact diagnostics and clear broker prompts for the stopped run.
- Class C, semantic success: automation must not treat a canary or guarded direct run as successful when the payload says hard gates failed, proof status is partial, or summary success is false.

## 6. Side-Effect Map

- file writes / artifacts: canary summary JSON files and guarded direct summary JSON files are unchanged except for process exit behavior.
- DB / schema / transaction boundaries: not applicable; no schema or DB writes are added.
- JSONL / log / audit sinks: no new durable JSONL sink is required.
- console / UI / operator output: stderr tails and stop payload diagnostics become operator-visible through event payloads.
- rollback / recovery / retry: stop cleanup should avoid orphan prompt state; process kill semantics remain bounded to current runner child.
- cache / global state: prompt broker pending state for the stopped run is cleared.
- bootstrap fallback / config-env mutation: not applicable.

## 7. Realization Architecture

- Add a dedicated stderr drain task to `ProcessRunner` and start it alongside the stdout read-loop.
- Remove deferred whole-stderr reads from stdout finalizers to prevent a deadlock wait point.
- Preserve stderr tails in exit/stop diagnostics and avoid clearing them before `/stop` can emit its payload.
- Have `/stop` call `broker.cleanup_run(run_id)` for the stopped run.
- Add semantic exit helpers to canary/direct scripts so `main()` returns non-zero on failed hard gates, partial proof, archive errors, or guarded summary failure.

## 8. Execution Tranches

1. Patch `ProcessRunner` concurrent stderr draining and stop diagnostics.
2. Patch `/stop` prompt broker cleanup and stop event payload.
3. Patch canary/direct semantic exit codes.
4. Add focused regression tests.
5. Run targeted validation, close this execution item, and remove the temp mirror.

## 9. Acceptance Criteria

- A subprocess that writes stderr without closing stdout cannot block the runner because stderr is drained concurrently.
- `run_failed` payloads still include stderr tail diagnostics.
- `/stop` emits a compact diagnostic payload and clears prompt broker state for the stopped run.
- Stage 2/3/4/34 canary scripts return non-zero when their semantic proof status is fail/partial/error.
- Guarded Stage 4 direct runner returns non-zero when its summary marks failure.
- Touched production functions do not newly enter the 120+/180+ complexity guard bands.

## 10. Verification Plan

- `python -m pytest tests/test_process_runner.py -q`
- `python -m pytest tests/test_bridge_server_http_contract.py -q`
- `python -m pytest tests/test_canary_semantic_exit.py -q`
- `python -m pytest tests/test_run_stage2_canary.py tests/test_run_stage3_canary.py tests/test_run_stage4_canary.py tests/test_run_stage34_canary.py tests/test_run_stage34_ep_demo_canary.py -q`
- `python -m pytest tests/test_run_stage4_direct_supervised_guarded.py -q`
- `python -m ruff check <touched files>`
- `python scripts/check_utf8_hygiene.py <touched files>`
- `git diff --check`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- Do not run a fresh live run inside this execution wave.
- Do not change Director pass/reject policy in this wave.
- Do not introduce process-tree-wide kill behavior beyond the currently launched runner child without a separate execution doc.
- Do not make canary analysis-only commands fail just because they report an existing partial result unless their command purpose is a fresh run.

## 12. Temp Queue Notes

- temp status: closed and removed
- cleanup condition: satisfied after implementation validation and canonical closure update
- roadmap dependency: none; this is the only active execution item

## 13. Document 3-Pass Audit

- Pass 1, structure and scope: PASS. The document is an execution SSOT with explicit included/excluded surfaces, acceptance criteria, and verification commands.
- Pass 2, evidence and consistency: PASS. Claims are bounded to inspected live code and current `05964ee2` baseline state.
- Pass 3, execution and readability: PASS. Tranches are sequenced, side effects are covered, and excluded P1/P2 follow-up lanes are not silently absorbed.
- Confidence: 96%. The runner and canary findings are independently supported by live code reads and parallel deep-dive evidence; broader artifact/session issues are intentionally deferred.

## 14. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule: this document was audited against `05964ee2702ac7d128805ca49e9b1f45cc0f2d4e` and is current for this branch.

## 15. Closure Evidence

Implementation Summary:
- `ProcessRunner` now drains stderr concurrently, returns stop diagnostics, and suppresses duplicate normal-exit callbacks during explicit stop.
- `/stop` now cleans the prompt broker for the stopped `run_id` and broadcasts the stop diagnostic payload.
- Canary/direct script `run` and `full` commands now return non-zero when the already-authored proof payload fails; `prepare`, `analyze`, and branch inventory remain advisory exit-zero paths.

Validation Results:
- `python -m pytest tests/test_canary_semantic_exit.py tests/test_run_stage2_canary.py tests/test_run_stage3_canary.py tests/test_run_stage4_canary.py tests/test_run_stage34_canary.py tests/test_run_stage34_ep_demo_canary.py tests/test_run_stage4_direct_supervised_guarded.py -q` -> PASS, 51 passed.
- `python -m pytest tests/test_process_runner.py tests/test_bridge_server_http_contract.py -q` -> PASS, 47 passed.
- `python -m py_compile modules\api\process_runner.py modules\api\bridge_server.py scripts\canary_semantic_exit.py scripts\run_stage2_canary.py scripts\run_stage3_canary.py scripts\run_stage4_canary.py scripts\run_stage34_canary.py scripts\run_stage34_ep_demo_canary.py scripts\run_stage4_direct_supervised_guarded.py` -> PASS.
- `python -m ruff check <touched code/test files>` -> PASS.
- `python scripts\check_utf8_hygiene.py <touched code/test/doc files>` -> PASS.
- `git diff --check` -> PASS.
- `python scripts\ops_validator.py --strict` -> PASS before temp mirror removal.

Complexity Recount:
- `modules/api/process_runner.py`: `stop` 48 LOC, `_cancel_task` 8 LOC, `_read_stderr_loop` 27 LOC, `_await_stderr_drain` 11 LOC, `_read_loop` 61 LOC, `_read_loop_mode_b` 110 LOC.
- `modules/api/bridge_server.py`: `stop_endpoint` 17 LOC.
- `scripts/canary_semantic_exit.py`: touched helpers 2 to 16 LOC.
- Canary/direct `main()` functions: 14 to 34 LOC.
- No touched production function newly entered the 120+/180+ guard bands.

Closure 3-Pass Audit:
- Pass 1, scope completion: PASS. All included tranches have code changes and focused tests.
- Pass 2, evidence consistency: PASS. Validation evidence covers runner liveness, stop cleanup, semantic exit behavior, UTF-8 hygiene, and ops queue integrity.
- Pass 3, closure readiness: PASS. Deferred artifact/session/director policy lanes remain excluded rather than silently absorbed.
- Confidence: 96%. This wave is closed for live-run readiness locks; remaining deep-dive items require separate execution documents.
