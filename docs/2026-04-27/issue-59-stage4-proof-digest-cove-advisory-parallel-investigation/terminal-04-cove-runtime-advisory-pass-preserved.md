# Issue #59 Terminal 04 - CoVe Runtime Advisory PASS Preserved

Status: final after 3-pass adversarial audit  
Scope: CoVe runtime exception path and Director PASS preservation

## Finding Summary

The Stage4 CoVe runtime exception path is intentionally advisory-only. When CoVe quick verification or LLM verification raises at runtime, Stage4 logs the advisory and preserves the Director PASS.

This is distinct from semantic CoVe fail-closed retry, which only fires when CoVe returns a valid verification result with `should_regenerate=True`.

## Evidence

- `modules/core/stage4_outcome_runtime.py`:
  - `handle_pass_round_result` runs CoVe after a PASS round.
  - `run_cove_pass_verification` catches quick verification exceptions and calls `handle_cove_runtime_failure`.
  - `run_cove_llm_verification` catches LLM verification exceptions and calls `handle_cove_runtime_failure`.
  - `handle_cove_runtime_failure` emits an advisory message and preserves Director PASS.
  - `_log_cove_runtime_advisory` writes `STAGE4_COVE_RUNTIME_ADVISORY` with `director_pass_preserved=true`.
- Live project evidence:
  - `projects/01_골든카나리아/logs/episode_production.jsonl` has five `STAGE4_COVE_RUNTIME_ADVISORY` rows.
  - `projects/01_골든카나리아/logs/runtime_audit.jsonl` has five matching `stage4_cove_runtime_advisory` audit rows.
  - `projects/01_골든카나리아/logs/session/ui_events.jsonl` shows five visible UI messages saying CoVe LLM runtime failure and Director PASS preserved.
- Existing tests cover:
  - LLM parse/runtime errors preserve final manuscript.
  - quick verification runtime errors preserve final manuscript.
  - runtime advisory payload preserves full detail.
  - UI/audit advisory emission.

## Risk / Gap

Operator surfaces can still misread CoVe runtime advisory as a content rejection if they do not preserve the semantic label:

- `cove_runtime_failure`: verifier failed to run or parse; Director PASS preserved.
- `cove_fail_closed`: verifier semantically detected a critical issue and requested regeneration.

## Suggested Contract Or Test

Add an explicit invariant to Stage4 summaries and benchmark packets:

- `cove_runtime_advisory_count`
- `cove_runtime_advisory_pass_preserved_count`
- `cove_fail_closed_retry_count`
- `cove_runtime_advisory_is_terminal=false`

Test expectation: if CoVe raises `ChainOfVerificationParseError`, Stage4 keeps `accepted=True` or preserves the final manuscript path, emits advisory logs, and does not increment semantic reject counters.

## Implementation Owner Surface

- `modules/core/stage4_outcome_runtime.py`
- `modules/core/chain_of_verification.py`
- `modules/core/services/audit_service.py`
- Benchmark archiving/reporting scripts

## Open Questions

- Should repeated CoVe runtime advisory events trigger a separate operational warning threshold after N preserved PASS events?
- Should the dashboard display CoVe runtime advisory counts next to proof digest warn?

## 3-Pass Save Audit

- Pass 1: Source and tests were checked against live advisory logs.
- Pass 2: Runtime exception advisory was separated from semantic CoVe fail-closed retry.
- Pass 3: No recommendation changes Director authority or makes Python the final quality judge.

