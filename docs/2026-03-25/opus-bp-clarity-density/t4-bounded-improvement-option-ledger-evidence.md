# T4 Evidence — Bounded Improvement Option Ledger

Date: 2026-03-25
Lane: T4 (Terminal 4)
Parent: `docs/2026-03-25/opus-bp-clarity-density/t4-bounded-improvement-option-ledger.md`

## Evidence Sources

### E1. Authority Surface Inventory (blueprint_ensemble.py)

10 authority surfaces identified in `_format_constraints()` (L846-1016):

| # | Surface | Tier | Insertion | Imperative Language | Truncation |
|---|---------|------|-----------|---------------------|------------|
| 1 | FACT-LOCK | 1 | Prepended (L998 `lines.insert(0, ...)`) | "변경 금지" | Regex-guided |
| 2 | CAPITAL-LOCK | 1 | Appended (L1011) | "변경 금지" | Genre-gated |
| 3 | MUST_FOCUS | 2 | 2nd position | "반드시 포함" | Content: 500ch |
| 4 | STOP_LINE | 2 | 3rd position | "즉시 REJECT" | Future: 300ch |
| 5 | CONTINUITY | 3 | 4th position | **None** (descriptive) | Time: 100ch |
| 6 | INHERITED_STATE | 3 | 5th position | **None** (descriptive) | Equipment: 10 |
| 7 | ARC_CONSTRAINT_SUMMARY | 4 | 6th position | None | 500ch or 10 kv |
| 8 | STATE_CHANGES_SUMMARY | 4 | 7th position | None (emoji info) | 800ch |
| 9 | SEMANTIC_CARRYOVER | 4 | 8th position | "참고용" (advisory) | 120ch/entry |
| 10 | IMMUTABLE_FACT_CARRYOVER | 5 | Block-level | "불변 조건" | Max 5/category |

Key gap: No explicit priority ordering instruction. No conflict resolution rules. LLM infers priority from position + label strength.

### E2. Prevalidation Blind Spots (unified_blueprint_validator.py)

Existing checks (all Python, no LLM cost):
- Structure: required fields, min char count (800), scene count >= 3, scene goal/summary presence
- Fidelity: Arc NPC mentions in integrated scenario
- Arc compliance: stop-line violation (token overlap)
- Continuity: location transition check
- Fact-lock drift: location, provenance sentiment, institution/venue authority
- Capital state drift: contradiction patterns, phantom capital
- Temporal deictic: absolute past references, future-memory patterns
- Dead NPC: advisory-only via state_tracker

**Cannot detect**:
- Vague prose within valid structure
- Repetitive/padded content that meets char threshold
- Shallow scene goals (e.g., "목표: 이야기를 진행한다")
- Thin relationship_changes without justification
- Authority drift in voice/tone (not locked facts)
- Tactical doc fidelity (blueprint ignoring arc beats)

quality_risk: binary `True/False`, not graded. Does NOT trigger retry.

### E3. Upstream Specificity (Stage 2 → Stage 3 handoff)

- `episode_details`: **optional** (not in ARC_DESIGN_SCHEMA required fields)
- `tactical_doc`: **required**, minimum `ep_count * 500` chars (arc_ensemble L1304)
- Stage 3 extraction: `extract_episode_tactical()` in `tactical_utils.py` L31-73
  - Priority: episode_details > regex header patterns > full tactical_doc fallback
  - Regex patterns: `[제 N화]`, `## 제N화`, `제N화:`, `Beat N:`
  - Fallback to full text = complete loss of per-episode specificity
- Arc ensemble evaluation: only checks `ep_mentions < ep_count` (presence, not depth)

### E4. Director Audit and Retry (director_prompts.py + three_phase_blueprint_runtime.py)

DIRECTOR_AUDIT_PROMPT_V30 scores 5 categories (20 pts each):
1. Scene Composition — counts scenes and density evenness
2. Narrative Flow — forward momentum, repetition detection
3. Prose Quality — fluency, sensory richness, AI-text traces
4. Reader Engagement — cliffhanger, unpredictability
5. Setting Consistency — factual adherence

**No dedicated clarity/density dimension**. These are embedded in Scene Composition and Prose Quality.

Retry feedback injection (`_build_retry_strategy_feedback()` L228-245):
- Captures: prev_reject_feedback, score_breakdown, fix_scope, validation_warnings
- Injects as aggregate string — **no scene-level granularity**
- Ensemble Generator sees "밀도 높이기" without knowing which scene is thin

quality_risk: recorded in pipeline_result but **advisory-only** — verdict and score control retry decision.

### E5. Schema Permissiveness (response_schemas.py)

BLUEPRINT_SCHEMA (L614-647):
- Required: `["episode_number", "scene_breakdown", "integrated_scenario"]`
- Optional: title, pacing_notes, target_beat, relationship_changes, time_flow, start_location, end_location, core_tension, expected_ending, ending_hook, protagonist_state, ending_state
- No `minLength` on any field in schema
- Scene objects allow bare strings (backward compat)
- `relationship_changes[*].justification` optional

### E6. Self-Audit Absence

Searched blueprint_ensemble.py, three_phase_blueprint_runtime.py, director_prompts.py:
- No "self-check", "self-audit", "자기 점검", "제출 전 확인" pattern found in generation prompts
- All quality reflection is post-hoc via Director
- AI_TELL_BLUEPRINT_GUARDRAIL (L82-89) addresses style avoidance but not density/clarity self-check

## Evidence Confidence

| Claim | Confidence | Basis |
|-------|------------|-------|
| 10 authority surfaces exist without explicit priority ordering | 95% | Direct code read |
| Prevalidation cannot detect vague/thin content | 95% | Exhaustive check inventory |
| episode_details is optional and rarely populated | 90% | Schema + ensemble eval code |
| Director feedback is aggregate (not scene-level) | 95% | Schema + retry state code |
| No prompt-level self-audit instruction exists | 90% | Prompt template search |
| B+C+A is the best bounded Stage 3 wave | 80% | Synthesis, not empirical |
