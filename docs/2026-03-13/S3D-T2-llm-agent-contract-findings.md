# S3D-T2: Stage 3 LLM Call Paths & Agent Contracts — 1pass Audit

**Date**: 2026-03-13
**Scope**: Stage 3 Blueprint pipeline (ThreePhaseBlueprintGenerator, BlueprintEnsembleGenerator, UnifiedBlueprintValidator, ContinuityBlueprintValidator, DirectorEnsembleSelector)
**Method**: Read-only code audit, 10-item checklist

---

## Checklist Results

### 1. LLM Call Inventory — Minimum/Maximum Calls per Single Attempt

**Status: OK**

| Path | Calls | Evidence |
|------|-------|----------|
| **Minimum (happy path, 1 attempt)** | 2 | Ensemble 3-parallel LLM calls (ThreadPoolExecutor) + Director compare 1 call |
| **Maximum (worst case, max_retries=9)** | ~40+ | 10 attempts x (3 ensemble + 1 director_compare) + continuity checks + PASS_WITH_FIX patch loops (max 3 per pass) + ASP calls |

Breakdown per attempt:
- Phase 1 (Constraint): 0 LLM calls (pure Python, `BlueprintConstraintCompiler.compile()`)
- Phase 2 (Generate): 3 LLM calls (parallel ensemble) or 1 (inplace patch) or 1 (partial)
  - `blueprint_ensemble.py:559` — `self._ask_with_cached_context()` per strategy
  - InPlace: `three_phase_blueprint_generator.py:737` — `self.ensemble.ask()`
- Phase 3 (Validate): 1-2 LLM calls
  - Multi-candidate: `director_ensemble.py:338` — `self._d.ask()` (compare_and_select_blueprint)
  - Single candidate: `unified_blueprint_validator.py:257` — `director.audit_manuscript()`
  - Continuity check (optional): `three_phase_blueprint_generator.py:363` — `director.check_blueprint_continuity_with_cache()`
- ASP (retry >= 2): 1 additional call via `adversarial_self_play.generate_with_adversary()`
- PASS_WITH_FIX loop: up to 3 iterations x (1 inplace patch + 1 director re-audit) = 6 calls

**Evidence**:
- `three_phase_blueprint_generator.py:64` — `max_retries: int = 9`
- `three_phase_blueprint_generator.py:176` — `for retry in range(max_retries + 1)`
- `blueprint_ensemble.py:300` — `ThreadPoolExecutor(max_workers=self.max_workers)` where `max_workers=3` (L190)

---

### 2. Model Selection Path — Consistency with models.yaml

**Status: OK**

| Component | models.yaml Key | Configured Model | Code Default Fallback | Match |
|-----------|----------------|------------------|-----------------------|-------|
| ThreePhaseBlueprintGenerator | `agents.three_phase_blueprint_generator` | gemini-2.5-pro | — | Yes |
| Ensemble sub-component | `sub_components.three_phase_blueprint_generator.ensemble` | gemini-2.5-pro | `AIModels.DEFAULT_ARCHITECT` | Yes |
| Validator sub-component | `sub_components.three_phase_blueprint_generator.validator` | gemini-2.5-flash | `AIModels.FLASH_ANALYSIS_MODEL` | Yes |
| UnifiedBlueprintValidator | `agents.unified_blueprint_validator` | gemini-2.5-flash | `AIModels.FLASH_ANALYSIS_MODEL` | Yes |
| Director (compare) | `agents.director` | gemini-2.5-pro | — | Yes |

**Evidence**:
- `three_phase_blueprint_generator.py:45-47` — `_get_sub_component_models("three_phase_blueprint_generator")`
- `base_agent.py:104-112` — `_get_agent_default_model()` reads from `config.get("agents", {})`
- `base_agent.py:115-123` — `_get_sub_component_models()` reads from `config.get("sub_components", {})`
- `models.yaml:30,42,56-58` — agent and sub_component entries

---

### 3. Context Caching — cache_type Registration, TTL 600s Appropriateness

**Status: OK**

- **cache_type**: `"blueprint_ensemble"` registered at `blueprint_ensemble.py:289`
- **TTL**: 600 seconds (10 minutes) at `blueprint_ensemble.py:291`
- **Appropriateness**: 600s is adequate. Blueprint ensemble retries happen within the same generate() call which typically completes within 10 minutes. The cache key includes `ep_num` via `_context_cache_project_namespace("ep", ep_num)`, so cross-episode contamination is prevented.
- **Cache scope**: Shared context = `arc_focus + constraints_str + prev_info + hud_context` — correctly scoped to the fan-out, with only strategy-specific prompt varying per candidate.

**Evidence**:
- `blueprint_ensemble.py:288-293` — cache creation
- `base_agent.py:1770-1862` — `_get_or_create_context_cache()` implementation with TTL check, lock, and eviction

---

### 4. ThreadPoolExecutor(3) — Timeout Configuration Path, Default Values

**Status: OK**

| Parameter | Source | Default | Value |
|-----------|--------|---------|-------|
| `ENSEMBLE_TIMEOUT` | `system.yaml ensemble_timeouts.blueprint.ensemble` | 300s | 300s |
| `SINGLE_CANDIDATE_TIMEOUT` | `system.yaml ensemble_timeouts.blueprint.single` | 240s | 240s |
| `max_workers` | Hardcoded | 3 | 3 |

**Evidence**:
- `blueprint_ensemble.py:182-184` — `_TIMEOUTS = _SYSTEM_CFG.get("ensemble_timeouts", {}).get("blueprint", {})`
- `system.yaml:44` — `blueprint: {ensemble: 300, single: 240}`
- `blueprint_ensemble.py:330` — `as_completed(futures, timeout=self.ENSEMBLE_TIMEOUT)`
- `blueprint_ensemble.py:334` — `future.result(timeout=self.SINGLE_CANDIDATE_TIMEOUT)`
- `blueprint_ensemble.py:190` — `self.max_workers = 3`

---

### 5. JSON Parsing Robustness — Director Response non-JSON Fallback

**Status: OK**

Two fallback paths exist when Director JSON parsing fails:

1. **Multi-candidate path** (`director_ensemble.py:341-345`): If `_extract_json_robust()` returns non-dict, falls back to `_fallback_first_candidate()` which calls `_evaluate_single_blueprint()`. That method returns REJECT with score=55 (L472-478), preserving Director sovereignty.

2. **Single-candidate path** (`unified_blueprint_validator.py:319-329`): Exception handler returns REJECT with phase="director_error" and descriptive feedback.

3. **ContinuityBlueprintValidator** (`continuity_blueprint.py:237-246`): If JSON parsing fails, returns PASS with `parsing_error=True` and warning — this is a soft-fail since continuity is advisory.

**Evidence**:
- `director_ensemble.py:341-345` — non-dict fallback
- `director_ensemble.py:419-423` — exception fallback
- `unified_blueprint_validator.py:319-329` — exception REJECT
- `continuity_blueprint.py:237-246` — parsing failure soft-pass

**Minor note**: The `_fallback_first_candidate` path (L480-491) always returns REJECT (via `_evaluate_single_blueprint` L472-478 which logs "[대원칙3] Director LLM 미호출 — fail closed"). This is correct fail-closed behavior.

---

### 6. InPlace Patch — 30KB Protection, rfind Position 0 Protection

**Status: OK (30KB) / NOT-APPLICABLE (rfind)**

- **30KB protection**: Present at `three_phase_blueprint_generator.py:689-691`. If Blueprint JSON exceeds 30,000 characters, returns `None` immediately, triggering full-rewrite fallback.
- **rfind position 0 protection**: This is a Stage 4 (chief_writer.py) concern, not Stage 3. Blueprint InPlace uses `_extract_json_robust()` for JSON parsing (L740), not rfind-based text splitting. No rfind usage exists in the Stage 3 InPlace path.
- **1-depth deep merge**: Present at `three_phase_blueprint_generator.py:747-753` — preserves original fields not in patched result, with sub-key level merge for dict values.
- **Scene key restoration**: `three_phase_blueprint_generator.py:754-759` — lost scene keys from `scene_breakdown` are restored from original.

**Evidence**:
- `three_phase_blueprint_generator.py:689-691` — 30KB guard
- `three_phase_blueprint_generator.py:740` — `self.ensemble._extract_json_robust(response)` (no rfind)
- `three_phase_blueprint_generator.py:747-759` — deep merge + scene restoration

---

### 7. ASP Integration — retry >= 2 Activation Condition Sufficiency

**Status: FINDING — P3**

**Description**: ASP activation threshold is `retry >= 2` (0-indexed), meaning it activates on the **3rd attempt** (retry=2). With default `max_retries=9`, ASP can participate in attempts 3-10 (8 out of 10 attempts). The condition also requires `adversarial_self_play` to be non-None and `best_blueprint` to exist.

**Concern**: The condition is sufficient but the threshold is low relative to Stage 4's documented "retry >= 2" convention. Since ASP adds an extra LLM call and only contributes an additional candidate (not a replacement), this is acceptable. The ASP result is appended to `all_candidates` (L332) and goes through the normal Director comparison, so quality is not compromised.

**Evidence**:
- `three_phase_blueprint_generator.py:297` — `if retry >= 2 and adversarial_self_play and best_blueprint:`
- `three_phase_blueprint_generator.py:332` — `all_candidates.append(_asp_bp)` (additive, not replacement)

**Verdict**: Functionally correct. P3 because the activation threshold could be documented more clearly but has no quality impact.

---

### 8. Director Comparison Prompt — Weight Sum 100%, Immediate REJECT Conditions

**Status: OK**

**Weight sum**: 40% + 35% + 15% + 10% = **100%** (correct)

| Criterion | Weight | Source |
|-----------|--------|--------|
| Consistency/no-contradictions | 40% | L315 |
| Arc compliance | 35% | L316 |
| Continuity | 15% | L317 |
| Next-episode hook | 10% | L318 |

**Immediate REJECT conditions** (L293-298):
1. Contradiction >= 1 found in consistency check
2. Arc tactical core events not reflected at all
3. Spatial/temporal contradiction with previous episode end state
4. Integrated scenario < 1000 chars
5. Ending hook missing or empty

**Additional hard gate** (L305-307): Absolute score < 80 = REJECT regardless of relative ranking.

**Evidence**:
- `director_ensemble.py:314-318` — weight definitions
- `director_ensemble.py:293-298` — immediate REJECT conditions
- `director_ensemble.py:307` — "절대 점수 80점 미만이면 REJECT"

---

### 9. director=None REJECT — 대원칙 3 (Director Sovereignty) Formal Compliance

**Status: OK**

Director sovereignty is enforced at two levels:

1. **UnifiedBlueprintValidator.validate()** (`unified_blueprint_validator.py:186-196`): If `director is None`, returns `("REJECT", {...})` with phase="no_director" and explicit message "Director 에이전트 미주입 — 디렉터 주권주의에 의해 REJECT". Score=0.

2. **DirectorEnsembleSelector._evaluate_single_blueprint()** (`director_ensemble.py:471-478`): Even for single candidates, returns REJECT with score=55 and message "Director LLM 미호출 상태의 단일 후보 자동 PASS 금지". This prevents bypassing Director via the single-candidate path.

3. **Emergency fallback** (`three_phase_blueprint_generator.py:653`): The end-of-retries fallback requires `director` to be truthy: `if best_blueprint and director and _last_score >= PatchModeThresholds.REWRITE`. Without Director, no emergency PASS_WITH_WARNING is issued.

**Evidence**:
- `unified_blueprint_validator.py:186-196` — explicit None check
- `director_ensemble.py:471-478` — fail-closed for single candidate
- `three_phase_blueprint_generator.py:653` — `director` truthiness required for emergency fallback

---

### 10. PASS_WITH_FIX Retry Loop — Max 3 Iterations, fix_scope Routing, Exhaustion to REJECT

**Status: FINDING — P2**

**Max iterations**: `_MAX_FIX = 3` at `three_phase_blueprint_generator.py:451`. Correct.

**fix_scope routing** (`three_phase_blueprint_generator.py:458-465`):
- If `fix_scope` is missing: falls back to score-based routing (`inplace` if score >= threshold, else `full`). Correct.
- If `fix_scope` is `"partial"` or `"full"`: breaks out of the fix loop immediately (L463-465), delegating to the outer generate retry loop. Correct.
- Only `fix_scope="inplace"` proceeds with the patch loop. Correct.

**Exhaustion behavior** (`three_phase_blueprint_generator.py:551-598`):
- If `_fix_ok` is False after 3 iterations: verdict is set to "REJECT" (L563), feedback is constructed, and `continue` sends execution back to the outer retry loop (L598). Correct.

**FINDING**: When the PASS_WITH_FIX loop exhausts and the last re-audit verdict was PASS_WITH_FIX or PASS_WITH_WARNING, the code adopts the patched blueprint (`_current_bp`) as `best_blueprint` (L554-555) before setting verdict to REJECT. This means the next retry loop iteration uses a partially-patched blueprint as `_previous_best` (L594-597), which may lead to an inplace patch on top of a patch. While this is likely intentional (progressive refinement), it creates a chain: original -> patch1 -> patch2 -> patch3 -> inplace_on_patch3. The quality degradation risk from multi-layered patches is real but mitigated by:
  - The InPlace change ratio guard (`_max_ratio`, L496)
  - Pydantic validation on each patch (`validate_blueprint()`, L760)
  - Director re-audit on each iteration

**Severity**: P2 — The multi-layer patch chain is a design risk, not a bug. The guards are present but the compounding effect on JSON structure integrity is not explicitly bounded.

**Evidence**:
- `three_phase_blueprint_generator.py:451` — `_MAX_FIX = 3`
- `three_phase_blueprint_generator.py:458-465` — fix_scope routing
- `three_phase_blueprint_generator.py:551-598` — exhaustion path
- `three_phase_blueprint_generator.py:554-555` — patched blueprint adoption before REJECT

---

## Summary

| # | Item | Status | Severity |
|---|------|--------|----------|
| 1 | LLM call inventory | OK | — |
| 2 | Model selection path | OK | — |
| 3 | Context Caching | OK | — |
| 4 | ThreadPoolExecutor(3) timeout | OK | — |
| 5 | JSON parsing robustness | OK | — |
| 6 | InPlace 30KB / rfind | OK / N/A | — |
| 7 | ASP integration | FINDING | P3 |
| 8 | Director comparison prompt weights | OK | — |
| 9 | director=None REJECT | OK | — |
| 10 | PASS_WITH_FIX retry loop | FINDING | P2 |

**P0**: 0, **P1**: 0, **P2**: 1, **P3**: 1

### Files Audited
- `modules/domain/agents/three_phase_blueprint_generator.py` (790 lines)
- `modules/domain/agents/blueprint_ensemble.py` (941 lines)
- `modules/domain/agents/unified_blueprint_validator.py` (466 lines)
- `modules/domain/agents/continuity_blueprint.py` (480 lines)
- `modules/domain/agents/director_ensemble.py` (Stage 3 sections, L185-492)
- `config/prompts/blueprint_generator.yaml`
- `config/prompts/ensemble.yaml` (L255-380, BLUEPRINT_GENERATION_PROMPT)
- `config/models.yaml`
- `config/system.yaml` (ensemble_timeouts)
- `modules/domain/agents/base_agent.py` (context cache, model resolution)
- `modules/core/constants.py` (PatchModeThresholds)
