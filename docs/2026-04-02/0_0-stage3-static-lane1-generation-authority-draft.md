# 0_0 Stage3 Static Lane 1 — Generation Authority / Prompt Hierarchy

Date: 2026-04-02
Status: draft-bounded-partial-evidence
Document Type: survey lane draft
Lane: Terminal 1 (Opus)
Master Order: `docs/2026-04-02/0_0-stage3-static-global-parallel-master-order.md`
Baseline Commit: `c5c5180bd3493bced341e21f29abb754a163de56`

## 1. Coverage

Surfaces inspected:

| Surface | Path | Lines Read |
|---------|------|-----------|
| BlueprintEnsembleGenerator | `modules/domain/agents/blueprint_ensemble.py` | full (L1–L1400+) |
| ensemble.yaml prompts | `config/prompts/ensemble.yaml` | full (ENSEMBLE_ARC_PROMPT + BLUEPRINT_GENERATION_PROMPT) |
| BlueprintConstraintCompiler | `modules/domain/agents/blueprint_constraint_compiler.py` | L1–L180 (compile + compile_to_prompt) |
| Stage3Orchestrator | `modules/core/stage3_orchestrator.py` | L1–80, L549–662, L1334–1558, L1661–1722 |
| ThreePhaseBlueprintRuntime | `modules/domain/agents/three_phase_blueprint_runtime.py` | L1–220 |

Not in scope (covered by other terminals):
- `unified_blueprint_validator.py` (Terminal 2)
- `stage4_context_builder.py` (Terminal 3)
- Artifact vertical slices (Terminal 4)

## 2. Findings

### F-1. Stage3 Has an Explicit, Three-Layer Context Priority Contract

The `BLUEPRINT_GENERATION_PROMPT` (ensemble.yaml L300–303) declares:

```
### [Context Priority Contract]
1. `Constraint Stack` outranks arc-mission prose.
2. `Arc Mission` outranks previous-truth archive.
3. `Previous Truth And Archive` outranks HUD convenience state.
```

This is the sole declared prompt-hierarchy for per-episode blueprint generation. It is explicit, and it survives into the actual LLM call without runtime override.

### F-2. Constraint Stack Is Itself Banded Into Four Tiers

`_format_constraints()` (blueprint_ensemble.py L898–1091) builds the constraint stack with explicit banding:

```
IMMUTABLE > HARD CONSTRAINT > EXPECTED CONTINUITY > ADVISORY
```

- **IMMUTABLE**: `fact_lock_packet` (settled prior canon), `capital_continuity_packet` (investment-genre continuity)
- **HARD CONSTRAINT**: `must_focus` (arc title, key events, episode content), `stop_line` (future episode boundary), `arc_constraint_summary` (Stage2 arc constraint)
- **EXPECTED CONTINUITY**: `continuity` (location, time, ongoing conflicts, active characters), `inherited_state` (equipment, injuries, mood, energy)
- **ADVISORY**: `state_changes_summary` (NPC deaths, skills, resolved plots), `semantic_carryover` (relationship rationale, foreshadow anchors)

This is compiler-like. The banding is structural and explicit. The prompt header tells the LLM: "충돌 시 상위 등급이 하위 등급을 무조건 우선합니다."

### F-3. What Stage3 Actually Ranks First

By combining F-1 and F-2, the effective priority during blueprint generation is:

1. **Protagonist identity lock** (hard-coded box at prompt top: `주인공 이름: {protagonist_name}`, `사용 금지` guard)
2. **Genre register guardrails** (anti-HUD, anti-recap, anti-cross-genre, scene authority contract — positioned before content sections)
3. **IMMUTABLE constraints** (fact-lock, capital-lock — cannot be overridden)
4. **HARD constraints** (must_focus episode content, stop_line future boundary, arc_constraint_summary)
5. **Arc Mission / arc_focus** (tactical_doc extract for this episode — subordinate to constraint stack per the priority contract)
6. **Strategy directive** (action/emotion/dialogue focused — injected after arc_focus)
7. **EXPECTED CONTINUITY** (location, time, character state from prior episode)
8. **Previous Truth And Archive** (prev_info_expanded: Tier 1 direct prev + Tier 2 structured bp carryover + Tier 3 manuscript ending truth)
9. **ADVISORY** (state_changes_summary, semantic_carryover)
10. **HUD Convenience State** (lowest priority per contract)

### F-4. Stage2 Truth Survival vs. Reinterpretation

The following Stage2 truths survive into Stage3 unchanged (compiler pass-through):

| Stage2 Truth | Stage3 Destination | Transformation |
|-------------|-------------------|----------------|
| `tactical_doc` (per-episode section) | `arc_focus` field in prompt | **Extracted verbatim** via `extract_episode_tactical()`, truncated at 15K chars |
| `constraint_summary` | `arc_constraint_summary` in HARD band | **Passed verbatim** |
| `state_changes` | `state_changes_summary` in ADVISORY band | **Summarized** by `_summarize_state_changes()` |
| `semantic_carryover` | ADVISORY band | **Normalized** but content preserved |
| `ep_start`, `ep_count`, `arc_no` | Constraint header | **Passed verbatim** |
| `episode_details` | Prepended to `arc_focus` | **Formatted** as "추가 사건" block |

The following undergo **prose reinterpretation**:

| Stage2 Truth | Reinterpretation Point | Nature |
|-------------|----------------------|--------|
| `tactical_doc` as a whole | `BLUEPRINT_GENERATION_PROMPT` asks LLM to "design scenes" | The LLM is asked to translate a tactical document into scene_breakdown + integrated_scenario — this is inherently reinterpretive |
| `beat_sequence` | Not directly passed to Stage3 | Beat sequence is Stage2's own arc-level pacing; Stage3 receives `tactical_doc` section and must independently decide scene pacing |
| `hybrid_composition` | Not directly passed to Stage3 | Strategy/pattern mix is re-decided by the blueprint strategy directive |
| `state_constraints` | Reconstructed from prior blueprints and arc data | Stage3 re-derives continuity from prev_blueprint rather than consuming Stage2's state_constraints directly |

### F-5. Previous-Info Expanded Is a Three-Tier Truth Context

`_format_prev_info_expanded()` (L1362–L1399) builds:

- **Tier 1: Direct Previous Episode Truth** — ending hook, end location, time flow, ending_state, protagonist_state
- **Tier 2: Structured Previous Blueprint Carryover** — up to 30 previous blueprints, structured per-scene carryover (400K char cap)
- **Tier 3: Manuscript Ending Truth** — raw manuscript ending (last 800 chars), explicitly declared as "Blueprint 메타데이터보다 우선"

This means Stage3 has a designed mechanism where manuscript prose truth outranks structured blueprint metadata — a deliberate anti-drift anchor.

### F-6. Semantic Bundle Is Injected as Feedback, Not Authority

In `_run_stage3_blueprint_generation_handoff()` (L1496–1513), the semantic_context is passed to the ThreePhase runtime as part of `initial_feedback_parts` alongside `external_feedback`. It is not injected into the constraint stack or arc_focus hierarchy. It operates as advisory enrichment, not structural authority.

### F-7. Strategy Directive Sits Between Arc Mission and Previous Truth

The `{strategy_directive}` slot in `BLUEPRINT_GENERATION_PROMPT` is positioned after `{arc_focus}` and before `{prev_info}`. This means:
- Strategy influences scene design but is subordinate to arc mission content
- Strategy is NOT subordinate to previous truth — it has authority to reshape how scenes are designed from the arc mission

The three strategies (action, emotion, dialogue) each provide:
- Tone/tension directives
- `AI_TELL_BLUEPRINT_GUARDRAIL` (anti-recap, anti-briefing)
- Any Director reject feedback from prior attempts
- Work retrieval contract from genre guard

### F-8. Context Caching Potentially Flattens Hierarchy

When context caching is active (`cache_name` is set), constraints_str, arc_focus, prev_info, and hud_context are replaced with `"[context cached: refer to cached_content]"` stubs in the main prompt. The cached shared_context (L325) is `constraints_str + arc_focus + prev_info + hud_context` concatenated in that order.

This means when cache is active, the LLM sees the constraint priority contract but the actual content arrives as a flat cached blob without the visual section headers that reinforce hierarchy. The `full_prompt_fallback` preserves the structured version for cache-miss scenarios.

**Potential risk**: The flattened cache content may weaken the LLM's ability to distinguish priority tiers, since the visual separators (`###` headers, band markers) may be outside the cached portion.

## 3. Non-Issues

### N-1. Protagonist Lock Is Solid
The protagonist name is locked at the prompt's very top in a visually emphasized box, with explicit "사용 금지" guards. This is robust.

### N-2. Stop-Line Boundary Is Correctly Hard
The stop_line includes future episodes and explicitly states "즉시 REJECT" for violations. It is in the HARD CONSTRAINT band, which is correct.

### N-3. Genre Register Guardrails Are Front-Loaded
Anti-HUD, anti-recap, anti-cross-genre contamination guards are placed before the content sections in the prompt. The `_sanitize_blueprint_candidate()` method (L1173–L1278) also enforces these post-generation via text contamination detection. This is a dual-layer defense.

### N-4. Dead NPC Precheck Exists
`_apply_stage3_dead_npc_precheck()` at the orchestrator level catches deceased character violations after blueprint generation. This is correct per the "사망 캐릭터" AGENTS.md rule.

## 4. Verdict

**mixed** — leaning compiler-like for structural/constraint pass-through, but with a clear reinterpretive core in the scene-design step.

Rationale:

- **Compiler-like aspects**: Stage3 has an explicit, enforced constraint hierarchy with 4-tier banding. Stage2 truths (tactical_doc sections, constraint_summary, state_changes) are passed through with minimal transformation. The fact-lock and capital-lock packets are genuinely immutable. The prompt priority contract is clearly stated and structurally reinforced.

- **Reinterpretive aspects**: The fundamental act of Stage3 — converting a tactical_doc section into scene_breakdown + integrated_scenario prose — is inherently reinterpretive. The LLM must translate tactical instructions into narrative scene design. `beat_sequence` and `hybrid_composition` from Stage2 are not directly forwarded, requiring Stage3 to independently re-decide pacing structure. The three-strategy ensemble approach introduces its own creative pressure that may diverge from Stage2 intent.

- **Net assessment**: Stage3's authority design is more compiler-like than expected. The constraint hierarchy is well-structured and the priority contract is explicit. The remaining reinterpretation is concentrated in the scene-design core (tactical → scenes), which is arguably unavoidable and desirable. The risk area is not prompt hierarchy flattening, but rather whether the LLM faithfully follows the priority contract when the cached context blob weakens visual separators.

## 5. Stop

read-only lane complete; no files mutated
