# TF-S4DD-T2: Stage 4 Logic & Flow Correctness Audit

**Date**: 2026-03-13
**Scope**: `stage4_orchestrator.py`, `stage4_interview_round.py`, `config/settings/validation.yaml`
**Auditor**: Claude Opus 4.6 (read-only)

---

## 2.1 Interview Loop Invariants

### Finding 2.1-1: Loop guard mechanism is sound

- **Severity**: INFO
- **File**: `modules/core/stage4_orchestrator.py:639-663`
- **Description**: The outer episode production loop uses a `loop_guard` counter incremented on every iteration, compared against `max_loops`. The formula is:
  ```python
  max_loops = max(1, min((target_ep or total_planned_ep) - latest_ep + 5, 100))
  ```
  This clamps between 1 and 100, with a +5 safety margin. The `max(1, ...)` prevents zero/negative loops. The hard cap of 100 prevents runaway execution.
- **Evidence**: Lines 639-663 show `loop_guard` starts at 0, increments before body, and breaks when `> max_loops`.

### Finding 2.1-2: target_ep=None is handled correctly

- **Severity**: INFO
- **File**: `modules/core/stage4_orchestrator.py:641, 646, 668`
- **Description**: When `target_ep` is None:
  - Line 641: `not target_ep and total_planned_ep <= 0` guards against no blueprints (None is falsy, so this fires correctly).
  - Line 646: `(target_ep or total_planned_ep)` falls back to `total_planned_ep` for max_loops calculation.
  - Line 668: `if target_ep and next_ep > target_ep` is skipped (None is falsy), so the loop continues until no more blueprints are found (line 674 breaks on missing blueprint).
- **Evidence**: The None path relies on blueprint availability as the natural termination condition, which is correct.

### Finding 2.1-3: target_ep=None with limit_mode=False keeps target_ep=None throughout

- **Severity**: INFO
- **File**: `modules/core/stage4_orchestrator.py:1486`
- **Description**: In `_prepare_stage4_session`, when `target_ep` is not provided and `limit_mode` is False, the code explicitly sets `target_ep = None` (line 1486). This flows into `_SessionConfig.target_ep` and then into `_run_interview_loop`. The loop then produces episodes until blueprints run out, bounded by the 100-iteration hard cap. This is the intended "produce everything" mode.

---

## 2.2 Retry/Escalation

### Finding 2.2-1: director_max_attempts default mismatch with YAML (cosmetic only)

- **Severity**: MINOR
- **File**: `modules/core/stage4_orchestrator.py:933` vs `config/settings/validation.yaml:94`
- **Description**: The code reads `_threshold("retry.director_max_attempts", 5)` with a fallback default of **5**, but `validation.yaml` defines `director_max_attempts: 10`. Since `_threshold()` reads the YAML first and only uses the Python default if the key is missing, the effective runtime value is **10** (correct). However, the Python fallback of 5 is misleading -- if the YAML key were ever removed, the system would silently halve its retry budget.
- **Evidence**: Line 933: `_threshold("retry.director_max_attempts", 5)` vs YAML line 94: `director_max_attempts: 10`.

### Finding 2.2-2: All attempts exhausted -- dual-path handling

- **Severity**: INFO
- **File**: `modules/core/stage4_orchestrator.py:1263-1298`
- **Description**: When all rounds are exhausted without PASS:
  1. If `_blueprint_regenerated` is True, an advisory suggests re-running Stage 2 (line 1266-1267).
  2. If `previous_attempt` contains a `best_manuscript`, the user is prompted: "1=use best result, 2=skip" (lines 1271-1283). Default is 2 (skip).
  3. If no best manuscript exists, the system logs "human review needed" and returns `should_return=True` (lines 1291-1298).

  The `should_return=True` propagates to `_run_interview_loop` line 865-868, which runs `run_post_episode_tasks()` and returns True, ending the entire Stage 4 session.
- **Evidence**: Lines 1263-1305 cover all exhaustion paths.

### Finding 2.2-3: Escalation chain (V75-D -> V75-B) is well-structured

- **Severity**: INFO
- **File**: `modules/core/stage4_orchestrator.py:1150-1261`
- **Description**: The escalation follows a strict sequence:
  1. **V75-D InPlace** (lines 1150-1219): Triggered on `_logic_error_streak >= threshold` (2 normally, 1 if quality_risk). One-shot (`_inplace_attempted` flag). On success, resets streak and feedback.
  2. **V75-B Full Regen** (lines 1221-1261): Triggered only after inplace was attempted (`_inplace_attempted and not _blueprint_regenerated`). One-shot (`_blueprint_regenerated` flag). On failure, still sets `_blueprint_regenerated = True` to prevent re-entry.

  Both flags prevent infinite escalation loops.

---

## 2.3 Verdict Routing Completeness

### Finding 2.3-1: PASS path -- CoVe post-verification can downgrade

- **Severity**: INFO
- **File**: `modules/core/stage4_orchestrator.py:947-1042`
- **Description**: When `_round_result.verdict in ("PASS", "PASS_WITH_FIX")`, the orchestrator runs Chain-of-Verification (CoVe). CoVe can downgrade to REJECT via three paths:
  1. `quick_verify` fails AND `verify` returns `should_regenerate=True` (line 976) -> REJECT, `continue` to next round.
  2. CoVe LLM runtime exception (line 998-1019) -> fail-closed REJECT.
  3. CoVe Quick runtime exception (line 1020-1040) -> fail-closed REJECT.

  On PASS with no CoVe issues, execution breaks out of the loop (line 1042).

### Finding 2.3-2: PASS_WITH_FIX -> 3-tier routing implemented correctly

- **Severity**: INFO
- **File**: `modules/core/stage4_interview_round.py:2628-2878`
- **Description**: `_execute_pass_with_fix_loop` handles the fix cycle:
  1. **fix_scope routing** (lines 2668-2675): If Director returns `fix_scope` of "partial" or "full", the loop breaks immediately, downgrading to REJECT for the retry path to handle with patch/rewrite. Only "inplace" (or fallback to inplace based on score) proceeds with in-loop patching.
  2. **InPlace patching** (lines 2683-2721): Up to 3 iterations (`_MAX_FIX = 3`). Each iteration: `chief_writer.inplace_patch()` -> min_length guard -> preservation ratio guard -> change ratio advisory -> Director re-audit.
  3. **Re-audit outcomes** (lines 2799-2833):
     - PASS: Accept patched manuscript, break with `_fix_ok = True`.
     - PASS_WITH_FIX: Continue loop (update `_current_ms` and feedback).
     - REJECT: Break loop.
  4. **Post-loop** (lines 2835-2877): If `_fix_ok`, verdict = PASS. Otherwise, verdict = REJECT with PF-3 logic: if last re-audit was PASS_WITH_FIX (not REJECT), adopt the patched manuscript.

### Finding 2.3-3: QualityGate bypass for PASS_WITH_FIX confirmed

- **Severity**: INFO
- **File**: `modules/core/stage4_interview_round.py:2909-2916`
- **Description**: The QualityGate check at line 2910 reads:
  ```python
  if verdict == "PASS" and score < _quality_gate_score:
  ```
  This explicitly checks only `"PASS"`, not `"PASS_WITH_FIX"`. Therefore PASS_WITH_FIX bypasses QualityGate as documented in CLAUDE.md. This is intentional -- Director sovereignty means if the Director says "pass with fix", the quality gate doesn't second-guess it.

### Finding 2.3-4: REJECT path flows to retry logic

- **Severity**: INFO
- **File**: `modules/core/stage4_interview_round.py:2880-3061` and `stage4_orchestrator.py:1043-1045`
- **Description**: When `_process_verdict` returns None (first element of tuple), the orchestrator loop at line 1043-1044 picks up `director_feedback` and `previous_attempt` for the next round. The REJECT handling includes score history tracking (plateau detection), reject_bucket streak tracking, and the V75-D/V75-B escalation chain.

### Finding 2.3-5: EMPTY verdict path

- **Severity**: INFO
- **File**: `modules/core/stage4_interview_round.py:1419-1470`
- **Description**: When all candidates are empty after filtering (`candidates = [c for c in candidates if c.get("manuscript", "").strip()]`), the method returns `_InterviewRoundResult(verdict="EMPTY", ...)`. Back in the orchestrator at line 947, `"EMPTY"` is NOT in `("PASS", "PASS_WITH_FIX")`, so it falls to the REJECT path (line 1043-1044). The `previous_attempt` is populated with `score=0` and the feedback includes "[시스템] 모든 후보 생성 실패. 재시도 필요."

---

## 2.4 Patch Mode 3-tier

### Finding 2.4-1: InPlace/Partial/Full routing logic

- **Severity**: INFO
- **File**: `modules/core/stage4_interview_round.py:3354-3488`
- **Description**: The `_generate_candidates` method implements 3-tier routing on REJECT retry:
  1. **InPlace** (lines 3381-3443): `fix_scope == "inplace"` OR (no fix_scope AND `prev_score >= PatchModeThresholds.INPLACE(60)`). Calls `chief_writer.inplace_patch()`. If result is empty or fails guards, falls through to patch.
  2. **Patch** (lines 3446-3473): `fix_scope in ("inplace", "partial")` (inplace failure cascades here) OR (no fix_scope AND `prev_score >= REWRITE(50)`). Calls `chief_writer.patch_with_feedback()`. If result is empty, falls through to rewrite.
  3. **Rewrite** (lines 3476-3488): Final fallback. Calls `chief_writer.regenerate_with_feedback()`.

### Finding 2.4-2: InPlace guards are applied consistently in both paths

- **Severity**: INFO
- **File**: `modules/core/stage4_interview_round.py:3426-3441` (REJECT retry) and `2708-2721` (PASS_WITH_FIX loop)
- **Description**: Both the REJECT retry path and the PASS_WITH_FIX fix loop apply:
  - `min_patched_length` guard (default 2000 chars) -- YAML `patch_mode.min_patched_length: 2000` matches.
  - `inplace_min_preserve_ratio` guard (default 0.70) -- YAML `patch_mode.inplace_min_preserve_ratio: 0.70` matches.
  - `inplace_max_change_ratio` advisory (default 0.30) -- YAML `patch_mode.inplace_max_change_ratio: 0.30` matches. Note: this is advisory-only (Director sovereignty), not blocking.

### Finding 2.4-3: 30KB guard is NOT in manuscript InPlace -- it is in Arc/Blueprint InPlace only

- **Severity**: INFO
- **File**: CLAUDE.md mentions "30KB -> return None (full fallback)". This applies to `four_phase_arc_generator.py` and `three_phase_blueprint_generator.py` InPlace, NOT to manuscript InPlace in `chief_writer.py`.
- **Description**: The manuscript InPlace in `chief_writer.inplace_patch()` operates on plain text, not JSON structures. The 30KB JSON truncation guard is only relevant for structured Arc/Blueprint JSON. This is correct behavior as documented in `T3-stage3-4-pipeline-audit-report.md` finding T3-020.

---

## 2.5 Score Threshold Consistency

### Threshold Cross-reference Table

| File | Line | Key | Code Default | YAML Value | Match? |
|------|------|-----|-------------|------------|--------|
| stage4_orchestrator.py | 47 | `npc_exposure.max_mentions_per_episode` | 15 | 15 | YES |
| stage4_orchestrator.py | 109 | `cross_episode_repetition.overlap_warning` | 3 | 3 | YES |
| stage4_orchestrator.py | 111 | `cross_episode_repetition.overlap_regression` | 6 | 6 | YES |
| stage4_orchestrator.py | 358 | `blueprint_preflight.enabled` | True | true | YES |
| stage4_orchestrator.py | 359 | `blueprint_preflight.min_episode` | 2 | 2 | YES |
| stage4_orchestrator.py | 794 | `context.mandatory_context_max` | 80000 | 400000 | **MISMATCH** |
| **stage4_orchestrator.py** | **933** | **`retry.director_max_attempts`** | **5** | **10** | **MISMATCH** |
| stage4_interview_round.py | 116 | `patch_mode.inplace_min_samples` | 5 | 5 | YES |
| stage4_interview_round.py | 1141 | `pattern_tracker.enable` | True | true | YES |
| stage4_interview_round.py | 1143 | `pattern_tracker.lookback_episodes` | 5 | 5 | YES |
| stage4_interview_round.py | 2269 | `smart_retrieval.enabled` | False | true | **MISMATCH** |
| stage4_interview_round.py | 2270 | `smart_retrieval.director_enabled` | False | true | **MISMATCH** |
| stage4_interview_round.py | 2310 | `context.vector_max_results_s4` | 20 | 50 | **MISMATCH** |
| stage4_interview_round.py | 2311 | `smart_retrieval.slot_max_chars_default` | 1500 | 3000 | **MISMATCH** |
| stage4_interview_round.py | 2312 | `smart_retrieval.max_npcs_per_slot` | 5 | 5 | YES |
| stage4_interview_round.py | 2371 | `smart_retrieval.director_total_budget` | 20000 | 300000 | **MISMATCH** |
| stage4_interview_round.py | 2670 | `patch_mode.inplace_below` | 60 | 60 | YES |
| stage4_interview_round.py | 2708 | `patch_mode.min_patched_length` | 2000 | 2000 | YES |
| stage4_interview_round.py | 2714 | `patch_mode.inplace_min_preserve_ratio` | 0.70 | 0.70 | YES |
| stage4_interview_round.py | 2737 | `patch_mode.inplace_max_change_ratio` | 0.30 | 0.30 | YES |
| stage4_interview_round.py | 2909 | `scoring.quality_gate_score` | 90 | 90 | YES |
| stage4_interview_round.py | 3371 | `feature_flags.enable_patch_mode` | True | true | YES |
| stage4_interview_round.py | 3428 | `patch_mode.min_patched_length` | 2000 | 2000 | YES |
| stage4_interview_round.py | 3429 | `patch_mode.inplace_min_preserve_ratio` | 0.70 | 0.70 | YES |

### Finding 2.5-1: Seven code defaults differ from YAML values

- **Severity**: MINOR
- **File**: Multiple (see table above)
- **Description**: Seven `_threshold()` calls have Python fallback defaults that differ from the actual YAML values. Since `_threshold()` reads YAML first and only uses the Python default when the key is missing, these mismatches are **cosmetic at runtime** -- the YAML values are the effective values. However, they create a maintenance risk: if any of these YAML keys were removed or renamed, the system would silently degrade to the stale Python defaults.

  The most notable mismatches:
  - `retry.director_max_attempts`: code=5, YAML=10 (halved retry budget on YAML loss)
  - `context.mandatory_context_max`: code=80000, YAML=400000 (5x context reduction on YAML loss)
  - `smart_retrieval.director_total_budget`: code=20000, YAML=300000 (15x budget reduction on YAML loss)
  - `smart_retrieval.enabled/director_enabled`: code=False, YAML=true (feature disabled on YAML loss)

---

## 2.6 Empty Manuscript Path

### Finding 2.6-1: Three empty candidates are handled correctly

- **Severity**: INFO
- **File**: `modules/core/stage4_interview_round.py:1419-1470`
- **Description**: Trace of what happens when CW produces 3 empty candidates:
  1. Line 1420: `candidates = [c for c in candidates if c.get("manuscript", "").strip()]` filters all three out, resulting in `candidates = []`.
  2. Line 1423: `if not candidates:` branch fires.
  3. Lines 1424-1428: Logs error, appends "재시도 필요" to feedback.
  4. Lines 1429-1437: Builds `previous_attempt` with `score=0`, preserving `_tot_used`/`_mad_used` flags and attempt history.
  5. Lines 1438-1450: Records attempt as `verdict="ERROR"`, `reject_reason="empty_candidates"`.
  6. Lines 1451-1465: Records to QualityDashboard if available.
  7. Lines 1466-1470: Returns `_InterviewRoundResult(verdict="EMPTY", ...)`.
  8. Back in orchestrator (line 947): `"EMPTY"` is not in `("PASS", "PASS_WITH_FIX")`, so falls to REJECT path.
  9. The next round will attempt `regenerate_with_feedback()` (full rewrite) since `previous_attempt["score"] == 0` is below all patch thresholds.

### Finding 2.6-2: UI message references hardcoded round number

- **Severity**: MINOR
- **File**: `modules/core/stage4_interview_round.py:1426`
- **Description**: The log message reads:
  ```python
  f"{'최종 실패 처리' if round_num >= 4 else '다음 면담으로 진행'}"
  ```
  This hardcodes `4` as the "last round" threshold, but `_max_rounds` comes from `_threshold("retry.director_max_attempts", 5)` which at runtime is **10** (from YAML). So the message says "최종 실패 처리" (final failure) starting from round 5, but there are actually 5 more rounds remaining. This is a cosmetic UI inaccuracy only -- it does not affect control flow. The actual loop termination is governed by `_max_rounds` in the orchestrator.

---

## Summary

| # | Severity | Finding |
|---|----------|---------|
| 2.1-1 | INFO | Loop guard mechanism is sound (max 100, min 1) |
| 2.1-2 | INFO | target_ep=None handled correctly (natural blueprint exhaustion) |
| 2.1-3 | INFO | "Produce everything" mode works via target_ep=None pass-through |
| 2.2-1 | MINOR | `director_max_attempts` code default (5) != YAML (10) -- cosmetic but misleading fallback |
| 2.2-2 | INFO | All-attempts-exhausted has user prompt + human review fallback |
| 2.2-3 | INFO | V75-D/V75-B escalation chain is one-shot and well-guarded |
| 2.3-1 | INFO | PASS path: CoVe can downgrade, fail-closed on exceptions |
| 2.3-2 | INFO | PASS_WITH_FIX: 3-tier routing (inplace loop/partial break/full break) correct |
| 2.3-3 | INFO | QualityGate bypass for PASS_WITH_FIX confirmed (checks only `"PASS"`) |
| 2.3-4 | INFO | REJECT path flows correctly to retry with feedback preservation |
| 2.3-5 | INFO | EMPTY verdict treated as REJECT with score=0, triggers full rewrite |
| 2.4-1 | INFO | InPlace/Patch/Rewrite cascade with proper fallback chain |
| 2.4-2 | INFO | Guards (min_length, preserve_ratio, change_ratio) applied in both paths |
| 2.4-3 | INFO | 30KB guard is Arc/Blueprint-only, not manuscript -- correct |
| 2.5-1 | MINOR | 7 `_threshold()` defaults differ from YAML (cosmetic at runtime, maintenance risk) |
| 2.6-1 | INFO | 3 empty candidates: filtered -> EMPTY -> REJECT -> full rewrite next round |
| 2.6-2 | MINOR | Hardcoded `round_num >= 4` in UI message vs dynamic `_max_rounds=10` |

**CRITICAL findings: 0**
**MAJOR findings: 0**
**MINOR findings: 3**
**INFO findings: 14**

**Overall assessment**: Stage 4 logic and flow correctness is robust. The interview loop, verdict routing, patch mode tiers, and escalation chain are all well-structured with proper guards and fallbacks. The three MINOR findings are cosmetic/maintenance-risk issues that do not affect runtime behavior as long as the YAML configuration remains intact.
