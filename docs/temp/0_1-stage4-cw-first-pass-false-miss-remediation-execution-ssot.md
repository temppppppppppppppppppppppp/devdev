# 0_1 Stage4 CW First-Pass False-Miss Remediation Execution SSOT

Date: 2026-03-31
Status: execution-ready
Document Type: execution SSOT
Canonical Path: `docs/2026-03-31/0_1-stage4-cw-first-pass-false-miss-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_1-stage4-cw-first-pass-false-miss-remediation-execution-ssot.md`
Baseline Commit: `229b85c655c32366818c2278462b51f3ad490913`
Baseline Dirty Summary: `dirty: active stage4 runtime/tests/log-db drift, active temp queue, multiple 2026-03-30 docs untracked`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-31/0_1-stage4-cw-first-pass-miss-parallel-bounded-survey.md`
- `docs/2026-03-30/0_1-stage4-cw-first-pass-miss-lane1-prompt-topology-draft.md`
- `docs/2026-03-30/0_1-stage4-cw-first-pass-miss-lane2-carryover-cognition-draft.md`
- `docs/2026-03-30/0_1-stage4-cw-first-pass-miss-lane3-model-tier-budget-draft.md`
- `docs/2026-03-30/0_1-stage4-cw-first-pass-miss-lane4-runtime-vs-gate-draft.md`
Evidence Artifacts:
- `docs/2026-03-31/0_1-stage4-cw-first-pass-miss-parallel-evidence.json`
- `projects/0_1/project_data.db`
- `projects/0_1/logs/session/decisions.jsonl`
- `projects/0_1/logs/episode_production.jsonl`
- `projects/0_1/logs/session/llm_io.jsonl`
Side-Effect Coverage: covered

## 1. Intent

Realize the smallest safe Stage 4 wave that follows the new survey conclusion:

- the system is over-diagnosing `CW first-pass weakness`
- the real primary issue is `Director PASS -> downstream gate override`
- prompt hierarchy and carryover framing are secondary contributors

This execution wave therefore does **not** try to redesign model policy or relax strong-advisory safety gates broadly.

It does three bounded things:

1. make the verdict layers explicit in persistence and operator evidence
2. strengthen first-pass authority framing so the prompt is less likely to underserve prior truth
3. make `carryover_ceiling` less investment-specific when structured prior-state hints are otherwise sparse

## 2. Baseline Facts

- audited survey conclusion: `downstream-first`, not `model-first`
- EP1-EP10 first-pass manuscripts were all `Director PASS`
- first-pass score range is `90-100`
- later passing attempts are often lower-scoring than the first pass
- first-pass misses cluster into downstream families:
  - `strong_advisory_escalation_non_local_fix`
  - `pass_with_fix_contract_missing_patch_targets`
  - `post_select_conflict`
- prompt hierarchy is mixed:
  - early IFC/chain-link anchors exist
  - but the explicit authority ladder arrives late
  - `V67` full prior-manuscript truth is not explicitly ranked in that ladder
- `carryover_ceiling` relies too heavily on investment-shaped cues

## 3. Scope

Included:

- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/chief_writer_prompts.py`
- `modules/domain/agents/chief_writer_context_packets.py`
- bounded Stage 4 / ChiefWriter tests
- canonical execution SSOT, temp mirror, roadmap refresh, queue-state refresh

Excluded:

- model/provider/fallback redesign
- strong-advisory policy redesign
- NpcDrift truth-source redesign beyond already-landed work
- Stage 3 lanes
- provider observability lane
- broad retry-lane routing redesign
- DB schema changes

## 4. Pass 1. Inventory Summary

Primary owners:

- `stage4_interview_round.py`
  - gate semantics payload
  - episode-production / DB / pass-rate attempt payloads
- `chief_writer_prompts.py`
  - first-pass authority framing
- `chief_writer_context_packets.py`
  - `carryover_ceiling` section generation

Primary sinks affected:

- `episode_production.jsonl`
- Stage 4 attempt DB payloads
- any operator/debug surfaces that consume `gate_semantics`
- CW first-pass prompt text

## 5. Pass 2. Semantic Classification

### Class A. Verdict-layer observability correction

Problem:

- current sinks foreground `final_verdict` and `gate_basis`
- they do not clearly surface whether `Director` already passed the manuscript
- operators therefore misread downstream overrides as `CW first-pass weakness`

Execution choice:

- add explicit `verdict_layers` metadata to gate-semantics payloads
- propagate a query-friendly subset into persisted attempt payloads

Minimum contract:

- `director_quality_passed`
- `downstream_override_applied`
- `primary_failure_layer`

### Class B. Prompt authority salience hardening

Problem:

- the explicit authority ladder is introduced too late
- `chain_link` and full `V67` prior-manuscript truth are not ranked explicitly

Execution choice:

- inject an earlier compact authority preface near the top of the CW prompt
- keep existing STEP 0.5, but strengthen its wording
- explicitly name:
  - `Opening Anchor`
  - `Immutable Facts`
  - `chain_link`
  - `prior manuscript full-text`
  - `prev digest`
  - `carryover ceiling`

### Class C. Carryover ceiling generic fallback

Problem:

- `carryover_ceiling` has investment-shaped evidence extraction
- non-investment episodes can lose one of the few structured prior-state reminder blocks

Execution choice:

- keep existing specific extraction
- add a bounded generic fallback from `prev_digest` when specific evidence is sparse
- do not attempt a large genre-router rewrite inside this wave

## 6. Side-Effect Map

- file writes:
  - `modules/core/stage4_interview_round.py`
  - `modules/domain/agents/chief_writer_prompts.py`
  - `modules/domain/agents/chief_writer_context_packets.py`
  - touched tests
  - canonical SSOT + temp mirror + roadmap + queue-state

- DB / persistence:
  - payload shape changes only
  - no schema change

- JSONL / audit sinks:
  - `episode_production.jsonl` gains clearer layer semantics
  - downstream override becomes easier to query

- operator output:
  - no new sink family
  - richer semantics in existing payloads only

- rollback / retry:
  - no retry-routing policy change intended in this wave

- config / env:
  - not applicable

## 7. Realization Architecture

### 7.1 Verdict Layers Payload

Add one bounded helper in `Stage4InterviewRound` that derives a stable verdict-layer payload from normalized director gate semantics.

Required fields:

- `director_quality_passed: bool`
- `downstream_override_applied: bool`
- `primary_failure_layer: "none" | "director_quality" | "downstream_gate"`

Propagation targets:

- `_build_gate_semantics_payload()`
- `_append_episode_log()` / `episode_production`
- `_build_stage4_pass_rate_attempt_payload()`
- `_build_stage4_db_attempt_payload()`

Guardrail:

- this is an observability/diagnosis correction only
- do not change the verdict itself in this tranche

### 7.2 Prompt Authority Preface

In `build_chief_writer_main_prompt()`:

- add a compact top-of-prompt authority preface immediately after the existing V67 contradiction warning
- keep the current STEP 0.5 block for backward compatibility
- make it explicit that feedback, constraints, and advisory prose must not override already-established prior truth

Guardrail:

- additive/ordering-safe
- no large prompt rewrite

### 7.3 Carryover Ceiling Fallback

In `ChiefWriterContextPackets._build_stage4_carryover_ceiling_section()`:

- preserve existing specific evidence extraction
- if the specific sub-blocks are sparse, use non-empty `prev_digest` lines as a generic fallback reminder block

Guardrail:

- bounded fallback only
- do not delete current investment cues
- do not add heavy genre branching

## 8. Execution Tranches

1. Tranche 1: verdict-layer observability correction
2. Tranche 2: first-pass authority preface and hierarchy reinforcement
3. Tranche 3: carryover ceiling generic fallback
4. Tranche 4: targeted verification and post-patch re-audit

## 9. Acceptance Criteria

- `gate_semantics` explicitly distinguishes Director-quality pass from downstream override
- Stage 4 attempt payloads expose a query-friendly downstream-override classification
- the CW prompt contains an early authority-preface naming full prior-manuscript truth and `chain_link`
- existing STEP 0.5 semantics remain intact
- `carryover_ceiling` emits a useful fallback reminder block when genre-specific hits are sparse but `prev_digest` is present
- no strong-advisory policy redesign or schema mutation leaks into this wave

## 10. Verification Plan

- targeted pytest shards:
  - `tests/test_stage4_interview_round.py`
  - `tests/test_stage4_lane2_binding_contract.py`
  - `tests/test_chief_writer_context.py`
- `python -m py_compile` on touched production/tests
- `ruff check` on touched production/tests
- `python scripts/check_utf8_hygiene.py` on touched docs/code/tests
- `python scripts/ops_validator.py --strict`
- `python scripts/sync_temp_queue_state.py`

## 11. Guardrails

- do not relax strong-advisory gates in this wave
- do not claim CW quality improved unless a later live rerun proves it
- do not widen into provider/model work
- do not convert this into a broad prompt redesign
- preserve Director sovereignty and current final-verdict behavior

## 12. Temp Queue Notes

- this item enters the active temp queue in the same turn
- it should be placed above older deferred Stage 4 observability work because it is the live user-requested lane
- roadmap refresh is required because `docs/temp/` already contains multiple execution items

## 13. 3-Pass Audit Record

Pass 1, structure and scope:

- execution SSOT type matches the requested next step
- included and excluded scope are bounded
- side-effect and verification sections are explicit

Pass 2, evidence and consistency:

- tranche order follows the audited survey:
  - diagnosis split first
  - prompt salience second
  - carryover fallback third
- no model-tier or advisory-policy overreach is introduced

Pass 3, execution and readability:

- the document is implementation-shaped
- acceptance criteria are concrete
- queue admission and validation hooks are explicit

Confidence: 96%
