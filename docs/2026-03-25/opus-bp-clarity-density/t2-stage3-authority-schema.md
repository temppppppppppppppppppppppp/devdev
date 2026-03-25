# T2. Stage 3 Authority + Schema Bands Survey

Date: 2026-03-25
Status: final (3-pass audited, confidence 95%+)
Lane: T2 (Stage 3 Authority + Schema Bands)
Master Order: `docs/2026-03-25/bp-clarity-density-structural-improvement-4terminal-master-order.md`
Baseline Commit: `f61a35c89b4c964afbfa902790560448d98b1bfb`

## 1. Scope

This lane investigates whether blueprint blur comes from Stage 3 mixing too many coequal authority surfaces.

Focus surfaces:
- `must_focus`, `arc_focus`, `scene_breakdown`, `integrated_scenario`
- `fact_lock_packet`, `capital_continuity_packet`
- Schema contracts in `response_schemas.py`
- Prompt assembly in `blueprint_ensemble.py` + `ensemble.yaml`
- Constraint compilation in `blueprint_constraint_compiler.py`
- Orchestration flow in `stage3_orchestrator.py`

## 2. Findings

### Finding 1: The system has a 4-tier authority hierarchy, but the prompt flattens it to 2 visual tiers

**Evidence**: The constraint compiler (`blueprint_constraint_compiler.py` L137-275) and constraint formatter (`blueprint_ensemble.py` L846-1016) assemble 10+ constraint vectors into a single `{constraints}` string.

The implicit authority hierarchy is:

| Tier | Surface | Authority Level | Visual Marker in Prompt |
|------|---------|-----------------|------------------------|
| 1 | FACT-LOCK | IMMUTABLE | yes (emoji + bold header) |
| 1 | CAPITAL-LOCK | IMMUTABLE | yes (emoji + bold header) |
| 2 | must_focus (key_events, content) | HARD CONSTRAINT | section headers only |
| 2 | stop_line | HARD CONSTRAINT + REJECT | asterisk warning |
| 3 | continuity, inherited_state | EXPECTED COMPLIANCE | section headers only |
| 3 | arc_constraint_summary, state_changes_summary | ADVISORY | section headers only |
| 3 | semantic_carryover, immutable_fact_carryover | ADVISORY | section headers only |
| 4 | reader_feedback | ADVISORY | explicitly marked `(참고용, advisory)` |

**Problem**: Tier 2 and Tier 3 surfaces share the same `### [제약 조건]` block in the prompt (`ensemble.yaml` L283-284). The LLM receives `must_focus` (HARD) and `semantic_carryover` (ADVISORY) in the same visual band. Only Tier 1 (FACT-LOCK / CAPITAL-LOCK) and Tier 4 (reader_feedback) have distinct visual authority markers.

**Confidence**: 95% — verified against live code and prompt template.

### Finding 2: `arc_focus` and `must_focus` are separate authority bands that overlap in practice

**Evidence** (`blueprint_ensemble.py` L215-238):
- `arc_focus` is resolved from `must_focus.content` OR `tactical_doc` extraction
- `arc_focus` occupies its own section: `### [Arc 전술서 - 이번 화 핵심]` (ensemble.yaml L280-281)
- `must_focus` is embedded inside `### [제약 조건]` block (ensemble.yaml L283-284)

The overlap path depends on `key_events` presence (`blueprint_ensemble.py` L863-864):
```python
if content and not key_events:  # L864
    lines.append("[이번 화 핵심 초점]")
```

Two cases:
- **key_events present** (normal path): `content` → `arc_focus` ONLY; `key_events` → `constraints_str`. No duplication. Authority is cleanly split.
- **key_events absent** (degraded path): `content` → BOTH `arc_focus` AND `constraints_str`. Duplication occurs — the same text appears in two prompt sections with different authority labeling.

The system correctly avoids duplication on the normal path. But on the degraded path (when Stage 2 fails to provide `key_events`), the LLM sees `must_focus.content` twice — once as tactical context (arc_focus), once as a constraint. This is a Stage 2 upstream quality dependency, not a Stage 3 design flaw.

**Confidence**: 95% — corrected after precise code verification of the `not key_events` guard at L864.

### Finding 3: `integrated_scenario` and `scene_breakdown` are OUTPUTS, not competing authority inputs

**Evidence**: Both are LLM-generated fields in the blueprint response, not input-side constraints.

- `scene_breakdown`: minimum 4 scenes for qualification (`blueprint_ensemble.py` L442), minimum 3 scenes for schema validation (`unified_blueprint_validator.py` L705-714)
- `integrated_scenario`: minimum 500 chars for qualification (`blueprint_ensemble.py` L442), minimum 800 chars for validation (`unified_blueprint_validator.py` L694-703)
- Both are validated independently; neither overrides the other in code logic

**However**, the schema allows a structural weakness: scene entries accept `anyOf: [OBJECT | STRING]` (`response_schemas.py` L557). A scene can degrade to a flat string instead of a structured object with goal/summary/characters/key_events/location/tension_level. When this happens, the scene_breakdown structurally collapses toward integrated_scenario quality — both become unstructured prose.

In practice, canary artifacts show well-structured scenes (verified: `canary_0325` ep5 has 5 scenes, each with type/title/goal/summary/characters/key_events/location/tension_level). The string fallback exists for compatibility but does not appear to be the dominant failure mode.

**Confidence**: 95% — verified against schema code and live artifacts.

### Finding 4: 6+ advisory blocks are prepended to semantic context with no attention budget

**Evidence** (`stage3_orchestrator.py` L1237-1267):

Prepended to semantic_ctx in this order:
1. `[WorldState 핵심 요약]` — max 1,800 chars
2. `[StyleGuide 문체/anti-AI 참고]` — variable
3. `[팩트 원장 핵심 수치]` — variable
4. `[DB-4 장기 미회수 복선]` — with "오탐 가능, 참고용" caveat
5. `[작품 추적 슬롯 요약]` — tracking_slots, mandatory_scene_engines
6. Smart retrieval semantic chunks — variable

These are injected as semantic context (system/user messages) BEFORE the main blueprint prompt. They lack explicit priority ordering or attention weighting. The main prompt (`ensemble.yaml`) does not reference them by name or tell the LLM how to trade off between advisory context and hard constraints.

**Confidence**: 90% — confirmed by code; the actual attention impact depends on model behavior, which cannot be measured statically.

### Finding 5: Treatment block injection deliberately filters per-episode specificity

**Evidence** (`stage3_orchestrator.py` L1151-1157):
```
"⚠️ 현재 화는 {ep}화입니다.
아래는 아크 전체의 제목·감정선·복선만 제공합니다.
구체적 사건(빌런 등장, 해결책, 보상, 전력 변화)은 제거되었습니다.
현재 화의 구체적 내용은 arc_focus와 MUST_FOCUS를 기준으로 작성하세요."
```

This is a correct authority separation: treatment-level arc overview is filtered to arc-scope, and the prompt explicitly directs the LLM to use `arc_focus` and `MUST_FOCUS` for per-episode specificity. This is a good example of authority banding in practice.

**Confidence**: 95%.

### Finding 6: The constraint_str assembly order does NOT match importance order

**Evidence** (`blueprint_ensemble.py` L846-1016):

Assembly sequence in `_format_constraints()`:
1. must_focus (HARD)
2. stop_line (HARD)
3. continuity (ADVISORY)
4. inherited_state (ADVISORY)
5. arc_constraint_summary (ADVISORY)
6. state_changes_summary (ADVISORY)
7. semantic_carryover (ADVISORY)
8. **fact_lock_packet → INSERTED AT POSITION 0** (IMMUTABLE)
9. capital_continuity_packet (IMMUTABLE)

The `lines.insert(0, ...)` at L998 moves FACT-LOCK to the top AFTER all other items are assembled. This is the correct final ordering (immutable first). However, capital_continuity_packet is merely appended at the end (L1008-1014), placing it BELOW advisory items in the final text.

If the LLM treats prompt position as authority weight, CAPITAL-LOCK may receive less attention than advisory continuity or state_changes content simply because it appears last.

**Confidence**: 85% — code-confirmed positioning; actual LLM attention behavior is inferential.

### Finding 7: quality_risk is a boolean flag, not a severity spectrum

**Evidence** (`unified_blueprint_validator.py` L119-151):

`quality_risk = bool(entries)` — True if ANY python_warning exists, False otherwise. There is no graduated quality_risk signal. A single MINOR issue and five CRITICAL issues produce the same `quality_risk = True`.

Additionally, `python_warnings` is capped at 4 entries (L148), and messages are truncated to 160 chars (L143). This compression loses diagnostic precision.

**Confidence**: 95%.

### Finding 8: Validation checks structure but not authority coherence

**Evidence** (`unified_blueprint_validator.py`):

Current validation detects:
- Missing required fields (scene_breakdown, integrated_scenario) — L681-692
- Minimum char/scene thresholds — L694-714
- Shallow scenes (no goal/summary) — L719-745
- Stop-line violations — L785-803
- Continuity breaks (location) — L805-831
- Fact-lock drift (location, item, institution) — L902-1056
- Capital drift — L1058-1137
- Temporal deictic drift — L1140-1199

NOT detected:
- Whether scene_breakdown goals/events are concrete vs vague
- Whether integrated_scenario merely restates scene_breakdown without adding value
- Whether must_focus key_events actually appear in scenes
- Whether advisory content (semantic_carryover, reader_feedback) improperly influenced hard constraints
- Relative density/specificity between scenes (some scenes thin, others verbose)

**Confidence**: 95% — negative evidence confirmed by full file read.

## 3. Core Question Answers

### Q1: Which surfaces are treated as authoritative vs advisory in practice?

**Authoritative (hard, blocking)**:
- FACT-LOCK, CAPITAL-LOCK: emoji-marked, explicit "변경 금지"
- stop_line: explicit REJECT warning
- must_focus.key_events: section-headed but no explicit override label
- episode_number, scene_breakdown, integrated_scenario: schema-required

**Advisory (soft, reference-only)**:
- reader_feedback: explicitly marked "(참고용, advisory)"
- All 6 prepended semantic advisories: implicitly advisory by position
- semantic_carryover: implicitly advisory

**Mixed/ambiguous**:
- must_focus.content: cleanly separated when key_events present; duplicated into both arc_focus and constraints when key_events absent (degraded path)
- continuity/inherited_state: expected compliance but no REJECT or marking
- arc_constraint_summary / state_changes_summary: pass-through from Stage 2, no authority level declared

### Q2: Does `integrated_scenario` overtake structured scene authority?

**No**, in code logic. Both are independently generated and validated outputs. The schema allows scene string fallback but live artifacts show structured scenes are the norm.

The real risk is not integrated_scenario "overtaking" scene_breakdown, but scene_breakdown entries being thin or vague even when they pass structural validation. Current validation checks scene count and depth (goal/summary present) but not scene specificity (are goals concrete enough to guide a manuscript?).

### Q3: Is the current blueprint schema itself too loose?

**Partially**. The schema correctly requires scene_breakdown and integrated_scenario, and scene entries have a rich typed structure. The looseness exists in:

1. **String fallback for scenes**: `anyOf: [OBJECT | STRING]` allows scenes to degrade to flat text
2. **No minimum quality for scene fields**: having an empty `content: ""` passes schema validation (observed in canary artifacts)
3. **No required count for key_events**: a scene with 0 key_events passes
4. **No cross-field coherence**: scene goals don't need to map to must_focus key_events

## 4. Summary

### What this lane found:

1. The authority hierarchy exists implicitly (4 tiers) but is communicated to the LLM as effectively 2 visual tiers (emoji-marked immutables vs everything else undifferentiated)
2. `must_focus.content` duplication across `arc_focus` and `constraints` sections only occurs on the degraded path (when Stage 2 fails to provide `key_events`); normal path is cleanly separated
3. `integrated_scenario` vs `scene_breakdown` is a non-issue in code — they are complementary outputs
4. The real clarity/density bottleneck in this lane is the **flattened authority presentation** in the prompt: Tier 2 hard constraints look the same as Tier 3 advisory guidance
5. Validation enforces structure but not specificity — scenes can be structurally valid yet narratively vague

### What this lane did NOT find:

- Evidence that the schema itself is the dominant limiter (it is adequate but could be tighter)
- Evidence that integrated_scenario overtakes scene_breakdown
- Evidence that advisory blocks actively harm blueprint quality (they are neutral to positive)

## 5. Mandatory Final Lines

- Dominant limiter in this lane: **authority mixing** — Tier 2 hard constraints and Tier 3 advisory guidance share the same visual band in the prompt, making them indistinguishable to the LLM
- Best bounded improvement candidate in this lane: **explicit authority banding in the prompt constraint block** — visually separate HARD CONSTRAINT and ADVISORY sections within `### [제약 조건]`, and deduplicate must_focus.content from arc_focus
- Should this lane alone trigger a new SSOT: **no** — this is one limiter among multiple; cross-lane synthesis needed
