# Run-Control Authority Locks Execution SSOT

Date: 2026-04-26
Status: closed
Canonical Path: `docs/2026-04-26/run-control-authority-locks-execution-ssot.md`
Temp Mirror Path: `docs/temp/run-control-authority-locks-execution-ssot.md`
Commit State:
- Baseline Commit: `6e6c85a9`
- Baseline Dirty Summary: `clean`
- Resume Commit: `6e6c85a9`
- Resume Drift Summary: `implementation applied and verified on 2026-04-26; temp mirror removed after closure`
Source Survey Docs: live workspace parallel deep-dive synthesis on 2026-04-26; no standalone survey doc saved
Evidence Artifacts: direct live-code evidence in `modules/api/bridge_server.py`, `modules/api/process_runner.py`, `modules/api/risk_approval.py`, `main_a.py`, and targeted tests
Side-Effect Coverage: covered

## 0. Execution Metadata Block

```yaml
execution_meta:
  schema_version: execution-meta-block-v1
  topic: run-control-authority-locks
  status: completed
  queue_role: historical_backing
  roadmap_rank: 1
  depends_on: []
  tranches:
    - id: public-run-input-lock
      title: Block public stdin_lines authority bypass
    - id: risk-approval-binding-lock
      title: Bind and consume risk approvals
    - id: regression-proof
      title: Add targeted authority regression tests
  verification_commands:
    - python -m pytest tests/test_risk_approval.py tests/test_bridge_server_http_contract.py tests/test_bridge_server_desktop_risk_gate.py tests/test_control_plane_approval_provenance_ssot.py
    - python scripts/check_utf8_hygiene.py modules/api/risk_approval.py modules/api/bridge_server.py modules/api/run_validator.py tests/test_risk_approval.py tests/test_bridge_server_http_contract.py docs/2026-04-26/run-control-authority-locks-execution-ssot.md docs/temp/run-control-authority-locks-execution-ssot.md
    - python scripts/ops_validator.py --strict
```

## 1. Intent

Lock the public run-control path so a client cannot ask for a safe key while secretly driving a destructive CLI path through raw stdin, and so risk-key approvals cannot be reused or applied to a different key than the one approved.

This executes now because the deep-dive found a P0 authority bypass in the `/run` surface:

- `/run` validates only `key` and `sub_key` before passing raw `inputs` to `ProcessRunner.start`.
- `ProcessRunner._build_stdin_sequence` treats `inputs.stdin_lines` as a complete stdin override.
- `main_a.py` exposes destructive or high-risk menu keys `44`, `77`, `88`, and `99`.

## 2. Baseline Facts

- Public authority path: desktop renderer or HTTP client -> `bridge_server /run` -> `ProcessRunner` -> `main_a.py`.
- Risk keys are centralized in `modules/api/control_plane_contract.py` and mirrored through `modules/api/run_validator.py`.
- `modules/api/risk_approval.py` stores `ApprovalRecord.key`, but the current validation path does not compare it with the requested key.
- `RiskApprovalGate.validate` records successful approval use, but the current gate does not consume approval IDs after success.
- Direct `ProcessRunner._build_stdin_sequence` tests use `stdin_lines` as an internal test harness seam, so the safe fix is to block it at the public `/run` boundary rather than remove the internal seam blindly.

## 3. Scope

Included:
- Public `/run` request validation for `inputs`.
- `RiskApprovalGate` key binding, status handling, and single-use consumption.
- Audit-log payloads needed to prove requested key vs approval-record key.
- Targeted tests for the authority bypass and approval misuse.

Excluded:
- Stop/start lifecycle truth fixes.
- Desktop stop timeout behavior.
- Stage4 session freshness and artifact hash verification.
- CI workflow expansion beyond targeted local verification in this tranche.
- New approval provisioning or persistent approval-store UI.

## 4. Pass 1. Inventory Summary

- `modules/api/bridge_server.py` lines around `/run`: extracts `inputs` and passes it to `runner.start`.
- `modules/api/process_runner.py` lines around `_build_stdin_sequence`: honors `inputs.stdin_lines` as a full stdin override.
- `modules/api/risk_approval.py` lines around `RiskApprovalGate.validate`: validates presence, lookup, expiry, and dual control, but not key match or reuse.
- `tests/test_risk_approval.py`: covers missing, unknown, expired, dual-control, success, and audit logging, but not key mismatch or reuse.
- `tests/test_bridge_server_http_contract.py`: covers invalid key, missing sub-key, active-run rejection, and valid request, but not public raw-stdin rejection.

## 5. Pass 2. Semantic Classification

- P0 authority bypass: public `inputs.stdin_lines` lets a caller replace the validated menu key with a different stdin program.
- P1 approval binding gap: an approval for one risk key can validate a different risk key unless the record key is checked.
- P1 approval replay gap: a successful approval can be submitted again unless the gate consumes it.
- Internal harness seam: direct `ProcessRunner` tests still need a way to run child processes without interactive stdin, so public boundary validation must not remove the internal test seam.

## 6. Side-Effect Map

- file writes / artifacts: no runtime artifact writes are expected from the fix; this SSOT canonical and temp mirror are written.
- DB / schema / transaction boundaries: not applicable.
- JSONL / log / audit sinks: `logs/risk-approval-log.jsonl` audit rows should include enough record-key context to diagnose mismatch or replay.
- console / UI / operator output: `/run` error payloads must stay in backend code namespace, not desktop transport error namespace.
- rollback / recovery / retry: approval consumption is fail-safe; if approval validates but later subprocess start fails, the consumed approval should not be silently reused.
- cache / global state: in-memory `RiskApprovalGate` gains used-approval tracking only inside the gate instance.
- bootstrap fallback / config-env mutation: not applicable.

## 7. Realization Architecture

1. Add public-run input validation before risk approval and before `runner.start`.
2. Treat top-level `inputs.stdin_lines` as forbidden on public `/run`.
3. Reject non-object `inputs` payloads so string/list payloads cannot drift into `ProcessRunner`.
4. Keep `ProcessRunner._build_stdin_sequence` internal override behavior for tests and direct runner harnesses.
5. In `RiskApprovalGate.validate`, enforce:
   - approval record exists
   - record status is `approved`
   - approval record key exactly matches requested key
   - approval was not already consumed
   - expiry and dual control still pass
6. Consume approval ID after successful validation and audit the result.

## 8. Execution Tranches

1. Public input lock:
   - add a validator for `/run` `inputs`
   - reject `stdin_lines`
   - add HTTP contract regression
2. Approval binding lock:
   - add key mismatch rejection
   - add single-use rejection
   - add audit context fields
3. Regression proof:
   - run focused risk/bridge tests
   - run UTF-8 hygiene for touched text/code/docs
   - run temp queue validator

## 9. Acceptance Criteria

- A public `/run` request with `{"key": "1", "inputs": {"stdin_lines": ["1", "77"]}}` is rejected before `runner.start`.
- A public `/run` request whose `inputs` is not an object is rejected before `runner.start`.
- An approval record for key `44` cannot validate request key `77`.
- A successful approval cannot be reused for a second run request.
- Existing valid risk-key requests with a matching fresh approval still pass.
- Existing direct `ProcessRunner` unit tests that rely on `stdin_lines` as an internal seam still pass.
- Risk approval audit rows retain requested key and include record-key context when a record exists.

## 10. Verification Plan

- `python -m pytest tests/test_risk_approval.py tests/test_bridge_server_http_contract.py tests/test_bridge_server_desktop_risk_gate.py tests/test_control_plane_approval_provenance_ssot.py`
- `python -m pytest tests/test_process_runner.py`
- `python scripts/check_utf8_hygiene.py modules/api/risk_approval.py modules/api/bridge_server.py modules/api/run_validator.py tests/test_risk_approval.py tests/test_bridge_server_http_contract.py docs/2026-04-26/run-control-authority-locks-execution-ssot.md docs/temp/run-control-authority-locks-execution-ssot.md`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- Do not let Python decide narrative pass/reject outcomes; this work is only control-plane authorization and request-shape enforcement.
- Do not remove LLM Director authority or alter stage verdict semantics.
- Do not remove `ProcessRunner` internal stdin override unless tests and harnesses are redesigned.
- Do not create a permissive allowlist that lets public callers provide raw stdin under a different field name.
- Do not add a persistent approval backend in this tranche.
- Do not broaden into stop lifecycle or session-memory fixes inside this execution item.

## 12. Temp Queue Notes

- temp status: completed
- cleanup condition: satisfied; `docs/temp/run-control-authority-locks-execution-ssot.md` removed after implementation, verification, and closure update.
- roadmap dependency: none; single active temp execution mirror is allowed without aggregate roadmap.

## 13. Adversarial Document Audit

Pass 1 - structure and scope:
- Attack: the document might be too broad and accidentally absorb stop lifecycle, CI, or session-memory work.
- Result: scope explicitly excludes those lanes and confines realization to `/run` input authority plus approval binding/replay.

Pass 2 - evidence and consistency:
- Attack: the P0 could be fixed in the wrong layer by removing `stdin_lines` from `ProcessRunner`, breaking internal tests rather than securing public API.
- Result: document pins the public `/run` boundary as the enforcement point and preserves the internal runner seam.

Pass 3 - execution and readability:
- Attack: acceptance criteria could be descriptive but not executable.
- Result: criteria now name the exact bypass payload, key-mismatch case, replay case, expected non-start behavior, and verification commands.

Confidence Gate:
- Estimated confidence: 96%.
- Remaining uncertainty: production approval provisioning remains intentionally out of scope and must be handled in a separate UI/provisioning execution item.
- Save decision: final save and temp mirror are allowed.

## 14. Pre-Implementation Re-Audit

Current-state re-audit completed against baseline commit `6e6c85a9` before code modification.

- Structure: still an execution SSOT, not a survey-only note.
- Evidence: live code still contains public `inputs` passthrough, internal `stdin_lines` override, and unbound/unconsumed approval validation.
- Execution readiness: implementation can begin immediately after temp mirror validation.
- Confidence: 96%.

## 15. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: not required for a single active execution mirror
- execution-start rule: satisfied by section 14 current-state re-audit

## 16. Closure Note

Closure status: closed.

Verified behavior:
- Public `/run` rejects `inputs.stdin_lines` before `runner.start`.
- Public `/run` rejects non-object `inputs` before `runner.start`.
- Risk approval validation rejects key mismatch.
- Risk approval validation rejects approval replay after successful use.
- Existing matching fresh risk approval requests still pass.
- Direct `ProcessRunner` internal `stdin_lines` tests still pass.

Verification evidence:
- `python -m pytest tests/test_risk_approval.py tests/test_bridge_server_http_contract.py tests/test_bridge_server_desktop_risk_gate.py tests/test_control_plane_approval_provenance_ssot.py`: 33 passed.
- `python -m pytest tests/test_process_runner.py`: 38 passed.
- `python -m pytest tests/test_risk_approval.py tests/test_bridge_server_http_contract.py tests/test_bridge_server_desktop_risk_gate.py tests/test_control_plane_approval_provenance_ssot.py tests/test_process_runner.py`: 71 passed.
- `python -m ruff check modules/api/risk_approval.py modules/api/bridge_server.py modules/api/run_validator.py tests/test_risk_approval.py tests/test_bridge_server_http_contract.py`: passed.
- `python -m py_compile modules/api/risk_approval.py modules/api/bridge_server.py modules/api/run_validator.py`: passed.
- `python scripts/check_utf8_hygiene.py modules/api/risk_approval.py modules/api/bridge_server.py modules/api/run_validator.py tests/test_risk_approval.py tests/test_bridge_server_http_contract.py docs/2026-04-26/run-control-authority-locks-execution-ssot.md docs/temp/run-control-authority-locks-execution-ssot.md`: passed before temp mirror cleanup.
- `python scripts/ops_validator.py --strict`: passed with one active mirror before cleanup.
- `python scripts/ops_validator.py --strict`: passed after cleanup with no active execution SSOT mirrors.
- `git diff --check`: passed.

Complexity recount:
- `modules/api/run_validator.py`: max function 40 LOC, 120+ functions 0, 180+ functions 0.
- `modules/api/risk_approval.py`: max function 92 LOC after helper extraction, 120+ functions 0, 180+ functions 0.
- `modules/api/bridge_server.py`: touched `run_endpoint` is 119 LOC; existing unrelated 120+ helpers remain, but this patch does not introduce a new 120+ or 180+ touched function.

Residual risks:
- Approval provisioning remains in-memory and operationally incomplete; this was intentionally excluded and should be handled by a separate approval-provisioning execution item.
- Stop/start lifecycle truth, CI expansion, Stage4 hydration freshness, and artifact hash proof remain separate queued candidates from the deep-dive list.

Closure document adversarial audit:
- Pass 1 structure: closure note names status, verification, temp cleanup, and residual risks.
- Pass 2 evidence: closure claims are bounded to the tests and hygiene commands actually run in this turn.
- Pass 3 execution: no active follow-up remains inside this SSOT; deferred issues are explicitly outside scope.
- Estimated confidence: 96%.
