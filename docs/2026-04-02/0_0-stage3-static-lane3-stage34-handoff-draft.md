# 0_0 Stage3 → Stage4 Handoff / Consumer Contract Lane (Terminal 3)

Date: 2026-04-02
Status: draft-bounded-partial-evidence
Document Type: bounded static survey lane draft
Master Order: `docs/2026-04-02/0_0-stage3-static-global-parallel-master-order.md`
Baseline Commit: `c5c5180bd3493bced341e21f29abb754a163de56`
Track: system
Mode: read-only static analysis only

---

## 1. Coverage

### Code surfaces inspected

| Surface | Path | Lines inspected |
|---------|------|-----------------|
| Stage4 Context Builder | `modules/core/stage4_context_builder.py` | L1-2475+ (TypedDicts, build_mandatory_context, entity extraction, seed assembly, prompt injections) |
| Stage4 Interview Round | `modules/core/stage4_interview_round.py` | L237 `_RoundContext.blueprint`, L986-1059 `_normalize_writer_blueprint`, L1061-1085 `_resolve_director_work_focus` |
| Stage4 Orchestrator | `modules/core/stage4_orchestrator.py` | L719-868 `_preflight_validate_blueprint`, L1061-1088 `_prepare_current_episode_inputs` |
| Stage4 Director Runtime | `modules/core/stage4_director_runtime.py` | L1183-1200 `_stage3_meta` consumption |
| Stage4 Outcome Runtime | `modules/core/stage4_outcome_runtime.py` | L882-904 `_stage3_meta` → retry escalation logic |
| Blueprint Constraint Compiler | `modules/domain/agents/blueprint_constraint_compiler.py` | L1-277 full (compile, compile_to_prompt) |
| Blueprint Ensemble | `modules/domain/agents/blueprint_ensemble.py` | L265-1060 (arc_focus resolution, _format_constraints 4-tier banding, prev_info) |
| Chief Writer Context Builder | `modules/domain/agents/chief_writer_context.py` | L1-617 full (build_common_context, immutable_fact_section, writer_core_sections) |
| Chief Writer Context Packets | `modules/domain/agents/chief_writer_context_packets.py` | L93 `_inventory_gaps` consumption |
| Stage3 Orchestrator | `modules/core/stage3_orchestrator.py` | L1680-2098 success path (annotate, persist, runtime payload) |
| Stage4 Types | `modules/core/stage4_types.py` | L16-60 `_RoundContext`, L63-91 `_InterviewRoundResult`, `WritingDirective` |
| Ensemble Prompt | `config/prompts/ensemble.yaml` | L270-449 (BLUEPRINT_GENERATION_PROMPT, output schema) |

### Handoff path traced

```
Stage3Orchestrator._handle_success()
  → _annotate_stage3_success_blueprint()      # stamps _stage3_meta, _inventory_gaps, _continuity_pins
  → ctx.current_project.save_episode_blueprint(ep, blueprint)   # DB persistence

Stage4Orchestrator._prepare_current_episode_inputs()
  → ctx.current_project.get_blueprint(next_ep)                  # DB read — sole handoff point
  → _preflight_validate_blueprint(blueprint, arc_data, ep_num)  # optional LLM pre-check + continuity_pins re-run
  → patched_blueprint or original blueprint → _EpisodeLoopInputs.blueprint

  → _RoundContext.blueprint (slots=True dataclass, propagated to all interview rounds)
    → Stage4ContextBuilder.build_mandatory_context(..., blueprint=...)
    → Stage4InterviewRound._normalize_writer_blueprint(blueprint)
    → ChiefWriterContextBuilder.build_common_context(blueprint=...)
```

---

## 2. Findings

### F-1. Handoff medium: DB-serialized dict — clean compiler output

The Stage3→Stage4 boundary is a **single DB persistence point**: `save_episode_blueprint()` / `get_blueprint()`. There is no in-memory object reference leakage, no shared mutable state, and no RPC-style protocol. The blueprint is a plain `dict` serialized to JSON in the project DB.

**Verdict**: This is a clean handoff boundary. The dict itself acts as the contract.

### F-2. Blueprint dict is the only handoff artifact — no separate constraint_prompt handoff

`BlueprintConstraintCompiler.compile()` produces a structured `constraint_block` dict that feeds into `blueprint_ensemble.generate_ensemble()` as a **Stage3-internal** input. The `constraint_block` is consumed within Stage3 to guide LLM blueprint generation. The `compile_to_prompt()` output is **never passed directly to Stage4**.

Instead, Stage4 reads the **result** of the LLM generation (the blueprint dict) — not the constraint input. The constraint_block's contents (must_focus, stop_line, continuity, inherited_state, fact_lock, capital_continuity) survive only insofar as they influenced the LLM-generated blueprint text.

**Implication**: There is a **one-way translation loss**. Stage2 arc truths reach Stage4 only if the Stage3 LLM faithfully compiled them into the blueprint's scene_breakdown, integrated_scenario, start_location, end_location, time_flow, protagonist_state, ending_state, etc. The constraint_block's structured authority banding (IMMUTABLE > HARD > CONTINUITY > ADVISORY) is enforced at Stage3 prompt level, not at Stage4 consumption level.

### F-3. Stage4 reads a narrow set of blueprint keys

Stage4 consumers read these blueprint keys:

| Consumer | Keys read |
|----------|-----------|
| ChiefWriterContext | `scene_breakdown`, `integrated_scenario_advisory`, `integrated_scenario`, `ending_hook`, `start_location`, `time_flow` |
| Stage4InterviewRound `_normalize_writer_blueprint` | `scene_breakdown`, `integrated_scenario_advisory`, `integrated_scenario` (sanitized for UI contamination) |
| Stage4ContextBuilder `_extract_blueprint_entities` | `integrated_scenario`, `scene_breakdown`, `core_tension`, `expected_ending`, `pacing_notes`, `target_beat`, `relationship_changes`, `time_flow`, `protagonist_state`, `synopsis`, `scenes`, `ending_hook`, `key_events`, `npc_appearances`, `emotional_arc`, `required_items` |
| Stage4ContextBuilder `_suggest_ambient_npcs` | `scene_breakdown` → per-scene `location` |
| Stage4ContextBuilder `_collect_npc_roster` | `scene_breakdown` → per-scene `npcs`, `characters`, `participants`; top-level `npc_roster`, `key_npcs`, `characters` |
| Director Runtime | `_stage3_meta` (quality_risk, final_verdict, last_score, revision_required) |
| Outcome Runtime | `_stage3_meta` → quality_risk → retry escalation threshold |
| CW Context Packets | `_inventory_gaps` → future_guard_section |
| Stage4Orchestrator preflight | `scene_breakdown`, `ending_hook`, `ending_state`, `start_location`, `time_flow`, `core_tension`, `protagonist_state` |

**Key observation**: Most Stage4 consumers read `scene_breakdown` and `integrated_scenario` as prose authority. The structured metadata keys (`start_location`, `end_location`, `time_flow`, `protagonist_state`, `ending_state`) are read but primarily for supporting context (NPC roster, entity extraction, ambient hints), not as binding contract fields.

### F-4. _stage3_meta annotation: advisory-only handoff

Stage3 stamps `blueprint["_stage3_meta"]` with quality flags:
```python
{
    "final_verdict": str,          # "PASS" / "PASS_WITH_FIX" / "PASS_WITH_WARNING"
    "quality_gate_failed": bool,
    "quality_risk": bool,
    "revision_required": bool,
    "last_score": int,
}
```

Stage4 uses this in two places:
1. **Director Runtime** (L1183-1200): Injects advisory text into the Director's decision prompt when `quality_risk` or `revision_required` is set.
2. **Outcome Runtime** (L882-904): Uses `quality_risk` to lower the inplace-retry-before-blueprint-regeneration threshold.

Neither consumer treats `_stage3_meta` as blocking. It is **advisory escalation metadata**, not a gate.

### F-5. _continuity_pins and _inventory_gaps: post-annotation passthrough

Stage3 stamps:
- `blueprint["_continuity_pins"]` — list of location/time correction changes applied post-LLM-generation
- `blueprint["_inventory_gaps"]` — list of items used in the blueprint but not yet acquired

Stage4 re-runs `apply_continuity_pins()` in `_preflight_validate_blueprint()` (Stage4Orchestrator L835-845), potentially producing a `patched_blueprint`. This means Stage4 does **not blindly trust** Stage3's pin results — it independently re-validates.

`_inventory_gaps` is consumed by `ChiefWriterContextPackets` (L93) to build a "future guard" warning section in the writer prompt.

### F-6. integrated_scenario sanitization at Stage4 boundary

`Stage4InterviewRound._normalize_writer_blueprint()` performs deep-copy + sanitization:
- Strips UI contamination patterns (HUD/status window/system message patterns) from `scene_breakdown`, `integrated_scenario_advisory`, and `integrated_scenario`.
- Merges `integrated_scenario` into `integrated_scenario_advisory` and clears the original.
- This **narrows the writer-facing blueprint authority** — an explicit information-reduction step.

The `ChiefWriterContextBuilder._extract_blueprint_sections()` further demotes `integrated_scenario_advisory` to "Advisory" priority in the prompt:
> "이 블록은 흐름 참고용이다. Opening Anchor / Immutable Facts / writer hard canon / prev digest / structured scene contract와 충돌하면 아래 prose는 버려라."

### F-7. Stage4 reconstructs much of its own truth independently

Stage4ContextBuilder does not simply consume Stage3 blueprint as-is. It independently:
1. Loads `arc_data` from the project's arc list (same source Stage3 used).
2. Runs its own `extract_episode_tactical()` from the same arc tactical_doc.
3. Builds its own mandatory_context from world_state, fact_ledger, chain_link.
4. Computes its own NPC roster, entity extraction, ambient NPC hints.
5. Loads its own HUD report, inventory, martial_arts from StateTracker.
6. Builds its own immutable_fact_section from blueprint + world_state + chain_link.

The blueprint provides **scene structure** (what happens) and **episode-specific metadata** (start/end location, time flow). Everything else is independently sourced.

---

## 3. Non-Issues

### NI-1. No shared mutable state between Stage3 and Stage4
The handoff is DB-mediated. No object aliasing risk.

### NI-2. No constraint_block leakage
`BlueprintConstraintCompiler` output stays within Stage3. Stage4 never sees the raw constraint_block dict. This is correct design — Stage4 should consume the *result* of constraint-guided generation, not the constraints themselves.

### NI-3. Stage4 preflight re-validates continuity pins
Stage4 does not blindly trust Stage3's `_continuity_pins`. It runs its own `apply_continuity_pins()` pass, which is a healthy trust-but-verify pattern.

### NI-4. _stage3_meta is correctly advisory
The quality metadata flows as advisory, not as a blocking gate. This matches the Director sovereignty principle (대원칙 3: Director 주권주의).

---

## 4. Verdict

**handoff-clean** — with one significant structural observation.

### Structural observation: the handoff is clean but lossy by design

The Stage3→Stage4 handoff is architecturally clean:
- Single DB persistence boundary
- No shared mutable state
- No protocol coupling
- Stage4 independently reconstructs most of its context
- Advisory metadata flows correctly as non-blocking

However, the handoff is **lossy by design**:
- Stage2 structured truth (constraint_block fields like must_focus, stop_line, inherited_state, fact_lock) reaches Stage4 **only through LLM prose intermediation** at Stage3.
- If the Stage3 LLM fails to faithfully encode a stop_line or fact_lock into the blueprint's scene_breakdown/integrated_scenario, that truth is lost to Stage4.
- Stage4 has no mechanism to independently verify whether the blueprint correctly reflects the constraint_block. The preflight check validates continuity (location/time), but does not validate arc-mission fidelity or stop_line compliance.
- The 4-tier authority banding (IMMUTABLE > HARD > CONTINUITY > ADVISORY) from `_format_constraints()` exists only in the Stage3 LLM prompt — Stage4 has no visibility into this hierarchy.

This means:
- **Stage3 is not a pure compiler** — it translates structured constraints into prose/JSON through LLM generation, which is inherently lossy.
- **Stage4 cannot detect Stage3 compilation failures** — if Stage3 produces a plausible-looking blueprint that silently drops a stop_line violation or fact_lock anchor, Stage4 will faithfully amplify that omission into the final manuscript.
- **The handoff quality depends entirely on Stage3 LLM fidelity** — the architectural boundary is clean, but the semantic contract is trust-based.

### Answers to master order questions (Terminal 3 scope)

**Q: What Stage3 truths survive into Stage4 as strong handoff truth?**
- `scene_breakdown` (scene structure, NPCs, locations, tension levels) — strong
- `integrated_scenario` / `integrated_scenario_advisory` — medium (demoted to advisory by CW context builder)
- `start_location`, `end_location`, `time_flow` — strong for continuity validation
- `protagonist_state`, `ending_state` — strong for state tracking
- `ending_hook` — strong (directly injected to CW prompt as section)
- `_stage3_meta` — advisory only (affects Director advisory text and retry threshold)
- `_inventory_gaps` — advisory only (future guard warning in CW prompt)
- `_continuity_pins` — re-validated independently by Stage4

**Q: What gets renamed, weakened, or flattened before Stage4 sees it?**
- `integrated_scenario` → merged into `integrated_scenario_advisory` → explicitly demoted to lowest-priority advisory in CW prompt
- UI contamination patterns stripped from all blueprint text by `_normalize_writer_blueprint()`
- Stage3's constraint_block 4-tier authority hierarchy is **completely invisible** to Stage4
- Stage3's structured FACT-LOCK, CAPITAL-LOCK, STOP_LINE enforcement is present only as prompt text in the blueprint's prose output — not as machine-readable metadata Stage4 can check

**Q: Does Stage3 handoff look like a compiler output or another prose brief?**
The blueprint dict is **structurally** a compiler output (typed JSON with explicit fields for scene_breakdown, locations, states). But the **semantic content** of those fields is LLM-generated prose, not mechanically derived from input constraints. The blueprint is best described as a **"structured prose brief"** — it has the shape of a compiler output but the fidelity characteristics of a translation.

---

## 5. Stop

read-only lane complete; no files mutated

---

## 3-Pass Audit Record

Pass 1, structure and scope:
- Confirmed terminal 3 lane scope: Stage3→Stage4 handoff / consumer contract
- All three required surfaces inspected (stage4_context_builder, chief_writer_context, blueprint_constraint_compiler) plus additional consumers
- Coverage table, findings, non-issues, verdict structure present

Pass 2, evidence and consistency:
- All code path references verified against live codebase at baseline commit
- Line numbers and method names cross-checked
- No overclaiming beyond static inspection scope
- Blueprint key consumption table derived from actual `.get()` calls in code

Pass 3, execution and readability:
- Findings are concrete and actionable
- Verdict directly addresses master order questions
- No code edits or DB writes performed
- Draft path matches master order specification

Confidence: 96%
