# Issue #59 Terminal 05 - CoVe Fail-Closed Retry Policy

Status: final after 3-pass adversarial audit  
Scope: semantic CoVe critical failure, retry disposition, and tests

## Finding Summary

Stage4 CoVe has two separate paths:

- Runtime advisory path: verifier exception or parse failure, Director PASS preserved.
- Semantic fail-closed path: verifier returns a critical result with `should_regenerate=True`, Stage4 requests retry and records `cove_fail_closed=True`.

The semantic path is already represented in source and tests.

## Evidence

- `modules/core/chain_of_verification.py` sets `should_regenerate` when overall severity is `CRITICAL`.
- `modules/core/stage4_outcome_runtime.py`:
  - `_handle_cove_llm_verification_result` delegates to retry disposition only if `_build_cove_retry_kwargs` returns data.
  - `_build_cove_retry_kwargs` returns retry data only when `cove_result.should_regenerate` is true.
  - `_build_cove_retry_disposition` records `retry_pathology_source="cove_fail_closed"`, `cove_fail_closed=True`, `cove_runtime_failure=False`, and `provisional_pass_downgrade=True`.
- Existing tests cover:
  - Stage4 still retries when CoVe requests regeneration.
  - direct `handle_pass_round_result` retry behavior on CoVe regeneration.
  - nonblocking CoVe issues log summaries without retry.
  - runtime exceptions do not set `cove_fail_closed`.

## Risk / Gap

The code-level split is good, but downstream reports can still collapse both paths as "CoVe problem." That would poison benchmark reject-rate comparisons, because runtime advisory should not be counted as semantic rejection.

There is also a local test hygiene issue: one Stage4 orchestrator test contains assertions after a `return`, making those later assertions unreachable. That does not invalidate the covered behavior, but it weakens regression confidence.

## Suggested Contract Or Test

Add a regression table for four cases:

- quick verify raises: PASS preserved, `cove_runtime_failure=True`, no semantic retry.
- LLM verify raises/parse fails: PASS preserved, `cove_runtime_failure=True`, no semantic retry.
- LLM verify returns noncritical issue: PASS preserved, nonblocking warning.
- LLM verify returns critical issue: retry disposition, `cove_fail_closed=True`, PASS downgraded for retry.

Fix the unreachable assertions in the existing Stage4 orchestrator test and assert the second-round quick path where intended.

## Implementation Owner Surface

- `tests/test_stage4_orchestrator.py`
- `modules/core/stage4_outcome_runtime.py`
- `modules/core/chain_of_verification.py`

## Open Questions

- Should benchmark comparison expose semantic CoVe fail-closed as a separate rejection subtype?
- Should noncritical CoVe issues be archived as advisory counts for later quality review?

## 3-Pass Save Audit

- Pass 1: Runtime exception and semantic critical paths were traced separately.
- Pass 2: Existing test coverage was checked for false confidence.
- Pass 3: Suggested tests stay within existing runtime contract and do not change authority policy.

