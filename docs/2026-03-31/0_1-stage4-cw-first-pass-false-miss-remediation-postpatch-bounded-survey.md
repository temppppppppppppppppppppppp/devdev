# 0_1 Stage4 CW First-Pass False-Miss Remediation Postpatch Bounded Survey

Date: 2026-03-31
Status: final (3-pass audited, static validation closed)
Document Type: postpatch bounded survey
Canonical Path: `docs/2026-03-31/0_1-stage4-cw-first-pass-false-miss-remediation-postpatch-bounded-survey.md`
Temp Mirror Path: `(none - survey only)`
Baseline Commit: `229b85c655c32366818c2278462b51f3ad490913`
Baseline Dirty Summary: `dirty: active stage4 runtime/tests/log-db drift, temp queue active, multiple prior docs/log artifacts still dirty`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Source Survey:
- `docs/2026-03-31/0_1-stage4-cw-first-pass-miss-parallel-bounded-survey.md`
Source Execution SSOT:
- `docs/2026-03-31/0_1-stage4-cw-first-pass-false-miss-remediation-execution-ssot.md`
Evidence Artifact:
- `docs/2026-03-31/0_1-stage4-cw-first-pass-false-miss-remediation-postpatch-evidence.json`

## Answer First

This wave landed the bounded remediation that the synthesis survey called for.

What is now true in static code:

1. Stage 4 persistence can now distinguish `Director PASS` from `downstream gate override`.
2. Chief Writer first-pass prompts now expose the authority ladder earlier and explicitly name `chain_link` plus prior-manuscript full text.
3. `carryover_ceiling` no longer depends only on narrow investment-shaped cues when prior-state hints are sparse.
4. The bounded regression set passed: compile, `ruff`, UTF-8 hygiene, targeted pytest shards, queue-state sync, and `ops_validator --strict`.

What is not yet true:

- there is still no fresh live rerun proving improved runtime behavior on new Stage 4 attempts
- this wave did not redesign strong-advisory policy, provider/model policy, or broad retry routing

Smallest correct status:

- `implemented and statically validated`
- `not yet runtime-closed`

## Hard Conclusions

### 1. Verdict-layer diagnosis is now first-class persistence, not an inferred afterthought

`modules/core/stage4_interview_round.py` now computes a `verdict_layers` structure and pushes query-friendly aliases into the main sinks.

Anchors:

- `modules/core/stage4_interview_round.py:2168-2214`
- `modules/core/stage4_interview_round.py:6002-6008`
- `modules/core/stage4_interview_round.py:6111-6141`
- `modules/core/stage4_interview_round.py:6185-6222`

Persisted fields now include:

- `director_quality_passed`
- `downstream_override_applied`
- `primary_failure_layer`

This directly addresses the survey's primary diagnosis gap: operators no longer need to reconstruct `Director PASS -> downstream REJECT` purely from indirect fields.

### 2. First-pass authority framing is materially stronger than baseline

`modules/domain/agents/chief_writer_prompts.py` now inserts an explicit early authority preface that names:

- `Opening Anchor`
- `Immutable Facts`
- `chain_link`
- `prior manuscript full-text`
- `prev digest`
- `carryover ceiling`

Anchors:

- `modules/domain/agents/chief_writer_prompts.py:106-107`
- `modules/domain/agents/chief_writer_prompts.py:138`

This does not prove first-pass output quality will improve in live runs, but it does close the static prompt-topology weakness identified in the survey.

### 3. Carryover fallback is broader and less dependent on narrow domain-specific detectors

`modules/domain/agents/chief_writer_context_packets.py` now injects bounded generic reminders from `prev_digest` when specific carryover evidence is sparse.

Anchors:

- `modules/domain/agents/chief_writer_context_packets.py:258-263`
- `modules/domain/agents/chief_writer_context_packets.py:279`

This closes the survey's secondary complaint that first-pass carryover reinforcement could become too thin outside investment-shaped cues.

### 4. The bounded regression set is clean

Validation results:

- `python -m py_compile ...` -> pass
- `ruff check ...` -> pass after one trivial forward-annotation cleanup
- `python scripts/check_utf8_hygiene.py ...` -> pass
- `pytest tests/test_stage4_cw_false_miss_remediation.py tests/test_chief_writer_context.py -k "early_authority_preface or opening_anchor or integrated_scenario or carryover_ceiling"` -> `7 passed`
- `pytest tests/test_stage4_interview_round.py -k "build_stage4_pass_rate_attempt_payload_extracts_gate_semantics or build_stage4_db_attempt_payload_uses_fallback_advisory_and_model or append_episode_log_includes_gate_semantics or save_director_selection_persists_gate_semantics_payload"` -> `4 passed`
- `pytest tests/test_stage4_lane2_binding_contract.py` -> `25 passed`
- `pytest tests/test_stage4_advisory_escalation_seam.py` -> `19 passed`
- `python scripts/sync_temp_queue_state.py` -> wrote `docs/temp/queue-state.json`, `ITEMS: 8`
- `python scripts/ops_validator.py --strict` -> `errors=0 warnings=0`

## Medium-Confidence Conclusions

### 1. Operator diagnosis should now be materially less misleading

The new top-level fields in DB/attempt payloads and `episode_production` rows should make false-miss analysis much faster and less error-prone.

This is high-confidence at the code-contract level, but still medium-confidence at runtime because no fresh merged live evidence was collected in this wave.

### 2. First-pass prompt salience is better, but outcome lift is still unproven

The prompt now states the authority ladder earlier, and the carryover ceiling gains a generic fallback path. That is the correct direction relative to the survey.

But the effect size on real manuscripts remains unproven until a fresh Stage 4 run is audited.

## Open Questions

1. Does a fresh live Stage 4 rerun show fewer `Director PASS -> downstream REJECT` misreads in practice?
2. Are downstream consumers already querying the new top-level verdict-layer fields, or do they still rely on legacy `final_verdict`-only views?
3. Should strong-advisory policy be redesigned in a later wave, or is improved observability enough for now?
4. Does the early authority preface need to move even higher in the final rendered prompt, or is the current placement sufficient?

## Scope Actually Realized

Implemented:

- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/chief_writer_prompts.py`
- `modules/domain/agents/chief_writer_context_packets.py`
- `tests/test_stage4_cw_false_miss_remediation.py`

Explicitly not implemented in this wave:

- model/provider/fallback redesign
- strong-advisory policy redesign
- retry-routing redesign
- live rerun / live-merge closure

## Pass Ledger

### Pass 1

- confirmed the survey's three intended seams were the only ones touched
- confirmed no DB schema change was required

### Pass 2

- re-read code anchors and aligned them against the execution SSOT intent
- checked that the new test file covers each newly introduced seam

### Pass 3

- verified UTF-8 hygiene on touched docs/code/tests
- verified temp mirror integrity and queue integrity via `ops_validator --strict`
- withheld any `resolved` claim because no fresh runtime rerun evidence exists

## Confidence

Confidence: `96%` for the static claim that this bounded execution wave landed correctly and validated cleanly.

Confidence is intentionally below runtime closure because no fresh live rerun or merged post-run evidence was collected in this turn.
