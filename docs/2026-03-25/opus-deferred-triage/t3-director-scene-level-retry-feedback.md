# T3. Scene-Level Director Retry Feedback — Deferred Triage

Date: 2026-03-25
Status: final
Document Type: deferred triage lane report
Canonical Path: `docs/2026-03-25/opus-deferred-triage/t3-director-scene-level-retry-feedback.md`
Triage Master Order: `docs/2026-03-25/deferred-followups-yesno-triage-7terminal-master-order.md`

## 1. Triage Question

Should a bounded Director retry-feedback wave open now, or is this still a later-after-canary candidate?

## 2. Current State — Director Feedback Architecture

### 2.1 Stage 3 Blueprint Retry Loop

**Retry state**: `three_phase_blueprint_runtime.py:22-31` — `_ThreePhaseRetryState` dataclass holds:
- `prev_reject_feedback` (Director verdict_reason/feedback — overall text)
- `prev_reject_strategy` (which strategy was rejected)
- `prev_fix_scope` ("inplace" / "partial" / "full")
- `prev_score_breakdown` (category scores dict — not scene-indexed)
- `prev_validation_warnings` (Python prevalidation issues list)

**Feedback injection**: `three_phase_blueprint_runtime.py:1420-1423` — merges strategy feedback + initial feedback into `attempt_feedback`, passed to phase2 generation.

**Feedback builder**: `three_phase_blueprint_runtime.py:228-240` — `_build_retry_strategy_feedback()` assembles from prev_reject_strategy, prev_reject_feedback, prev_fix_scope, prev_validation_warnings, prev_score_breakdown. All fields are **overall-level**, none are scene-indexed.

**Strategy feedback wrapper**: `blueprint_ensemble.py:299-308` — `_build_blueprint_strategy_feedback()` returns strategy-specific or generic `[이전 시도 문제 요약]`. No scene granularity.

### 2.2 Stage 4 Manuscript Retry Loop

**Fix feedback extraction**: `stage4_interview_round.py:5204-5267` — `_extract_fix_feedback()` extracts:
- `fix_pack`: target_kind, patch_targets, must_fix, do_not_regress, success_condition, evidence_summary
- `action_items`: Core fix instructions
- `fix_scope_reasoning`: Why this scope
- Issues, open_review

**Feedback injection**: `stage4_interview_round.py:2184-2186` — Director feedback injected as `director_feedback` kwarg into writer generation.

**Regeneration feedback**: `chief_writer.py:1078-1089` — wraps as `[이전 REJECT (시도 {N})에서 지적된 사항]` block. Overall level, no scene index.

**Retry history**: `chief_writer.py:2072-2104` — bucket/category/contradiction-level feedback. Not scene-level.

### 2.3 Director Output Structure

**Director prompts**: `director_prompts.py:137-166` — output schema includes:
- `verdict`, `score`, `selection_reason`, `verdict_reason`
- `feedback` (overall), `action_items` (list, overall), `fix_scope`, `fix_scope_reasoning`
- `contradictions` (list with type/description/violation — not scene-mapped)

**Blueprint validator**: `unified_blueprint_validator.py:336-353` — validation issues have `category`, `issue`, `severity` but no `scene_index` field.

### 2.4 Key Negative Finding: No Scene-Level Feedback Exists

| Surface | Scene-Level Granularity |
|---------|------------------------|
| Director verdict_reason | NO — overall text |
| Director action_items | NO — overall list |
| Director fix_scope | NO — "full"/"partial"/"inplace" overall |
| Director contradictions | NO — description text, not scene-mapped |
| Blueprint validator issues | NO — category/severity, no scene index |
| Score breakdown | NO — category scores, not scene scores |
| Retry state injection | NO — prev_reject_feedback is overall text |
| Stage 4 fix_pack | PARTIAL — patch_targets mention areas but not scene indices |

Blueprint `scene_breakdown` data **exists** in the generated artifact (per-scene goal, summary, characters, etc.), but Director and validator never decompose feedback at scene granularity.

## 3. What Scene-Level Retry Feedback Would Require

To add scene-level Director retry feedback, the following surfaces would need changes:

**Minimum scope (Stage 3 only)**:
1. `director_prompts.py` or Director sub-modules — add scene-indexed fields to rejection output schema
2. `unified_blueprint_validator.py` — add scene index to issue entries
3. `three_phase_blueprint_runtime.py` — extract and inject per-scene feedback into retry state
4. `blueprint_ensemble.py` — format scene-level feedback for retry prompt

**Full scope (Stage 3 + Stage 4)**:
5. `stage4_interview_round.py` — extract scene feedback from Director
6. `chief_writer.py` — inject scene-level feedback into regeneration prompt
7. Director evaluation prompt — instruct Director to produce per-scene assessments

**Estimated blast radius**: MEDIUM-HIGH
- Touches Director prompt output schema (affects both Stage 3 and Stage 4 paths)
- Modifies retry state dataclass
- Changes what the generator LLM sees on retry
- Director prompt token budget increases

## 4. ROI Assessment

### 4.1 Arguments For Opening Now

- The feedback gap is real and structural — Director detects scene-level issues (via validator) but can only express them as overall text
- Retry efficiency could improve if the generator knows exactly which scene to fix
- The current retry loop sometimes makes global rewrites when only one scene was weak

### 4.2 Arguments For Waiting

- **No post-patch canary yet**: Wave 1 (authority re-banding + density prevalidation) and the self-audit wave both closed today but have NOT been verified by a fresh full canary. Opening a Director retry-feedback wave before seeing their effect would violate single-variable attribution.
- **Blast radius is non-trivial**: Unlike the prompt-only self-audit wave, this requires schema changes to Director output format, retry state management, and feedback injection — at least 4-7 files across multiple ownership surfaces.
- **Director prompt is high-authority surface**: Director is the sovereignty holder. Changes to Director's output schema affect all stages, not just Stage 3. The blast radius is wider than any wave opened so far in this session.
- **Unclear current magnitude**: Without canary evidence showing "retry is burning cycles because feedback lacks scene granularity," the improvement is predicted but unquantified.
- **Authority re-banding may reduce the need**: If the generator receives clearer authority bands and self-audits before submission (from the two just-closed waves), fewer retries may be needed overall — potentially reducing the ROI of scene-level feedback optimization.

### 4.3 Confidence Assessment

The gap is real (95%+ confidence that scene-level feedback does not exist). The question is timing, not existence.

Whether scene-level feedback is the **next** highest-ROI wave is below 95% confidence because:
- Wave 1 and self-audit effects are unverified
- The interaction between improved authority presentation + self-audit + retry feedback is untested
- No canary data exists to quantify retry waste from lack of scene granularity

## 5. Blast-Radius Note

- Director output schema change: affects Stage 3 AND Stage 4 downstream consumers
- Retry state dataclass change: `_ThreePhaseRetryState` + Stage 4 retry payloads
- Feedback formatting: blueprint_ensemble.py + chief_writer.py
- Director prompt token increase: ~200-400 tokens per evaluation call (scene-indexed output)
- Testing: Would require new test coverage for scene-level feedback extraction, injection, and round-trip
- Risk of over-specification: If Director is forced to itemize per-scene, it may over-reject on minor scene-level noise

## 6. Verdict

The scene-level Director retry feedback gap is real and well-characterized, but opening it now would:

1. Violate single-variable attribution before the two just-closed waves have canary evidence
2. Touch the high-authority Director output schema with MEDIUM-HIGH blast radius
3. Attempt to optimize a retry path whose current waste level is unquantified

The correct next step is: run a fresh canary with Wave 1 + self-audit active, observe retry patterns, then decide whether scene-level feedback is the dominant remaining lever.

---

Lane verdict: later after canary
Best bounded next wave from this lane: Stage 3 scene-level Director retry feedback (after post-Wave1+self-audit canary)
Should Codex open an execution SSOT from this lane now: no
