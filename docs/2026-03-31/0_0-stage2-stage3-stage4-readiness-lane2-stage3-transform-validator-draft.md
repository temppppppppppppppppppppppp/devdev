# Lane 2: Stage 3 Transformation / Validator / Contract Survey

Date: 2026-03-31
Status: draft-bounded-partial-evidence
Lane: 2 of 5 (Opus Terminal 2)
Master Order: `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-parallel-master-order.md`
Baseline Commit: `fd1707372bd7eb8ad23a5d4506ef556e3f72cc51`

---

## 1. Coverage

### Code Surfaces Inspected

| File | Lines | Role |
|---|---|---|
| `modules/core/stage3_orchestrator.py` | ~1,500 | Batch orchestration, semantic_context build, retry control |
| `modules/core/stage3_context.py` | 129 | DI context: 2 required + 10 props + 10 callbacks |
| `modules/domain/agents/three_phase_blueprint_generator.py` | ~150 | Thin facade delegating to runtime |
| `modules/domain/agents/three_phase_blueprint_runtime.py` | ~1,700 | Core 3-phase pipeline: constraint -> generate -> validate |
| `modules/domain/agents/blueprint_constraint_compiler.py` | ~900 | Arc -> constraint_block extraction |
| `modules/domain/agents/blueprint_ensemble.py` | ~1,100 | 3-strategy ensemble generation (action/emotion/dialogue) |
| `modules/domain/agents/unified_blueprint_validator.py` | ~1,600 | Python pre-validation (12 categories) + Director mediation |
| `modules/models/blueprint.py` | schema | Blueprint field schema + validate_blueprint() |

### Artifact Surfaces Inspected

| Artifact | Evidence Type |
|---|---|
| `projects/0_0/logs/artifacts/stage3/ep_0001/attempt_01/final_blueprint__action_focused.json` | Real artifact |
| `projects/0_0/logs/artifacts/stage3/ep_0002/attempt_01/final_blueprint__emotion_focused.json` | Real artifact |
| `projects/0_0/logs/artifacts/stage3/ep_0005/attempt_06/final_blueprint__action_focused.json` | Real artifact |
| `projects/0_0/logs/artifacts/stage3/ep_0006/attempt_09/final_blueprint__dialogue_focused.json` | Real artifact |
| `projects/0_0/logs/artifacts/stage3/ep_0008/attempt_01/final_blueprint__dialogue_focused.json` | Real artifact |
| `projects/0_0/plans/blueprints/blueprint_0001.txt` | DB-stored form |
| `projects/0_0/plans/blueprints/blueprint_0002.txt` | DB-stored form |
| `projects/0_0/plans/blueprints/blueprint_0005.txt` | DB-stored form |
| `projects/0_0/plans/blueprints/blueprint_0006.txt` | DB-stored form |
| `projects/0_0/plans/blueprints/blueprint_0008.txt` | DB-stored form |

---

## 2. Findings

### F-1. constraint_summary Authority Demotion (GENERATION-SIDE)

**Severity**: CRITICAL
**Category**: Stage 2 -> Stage 3 authority dilution

Stage 2's `constraint_summary` -- the explicit MUST-NOT-DO prohibition list -- is classified as **ADVISORY band** in the 4-tier authority system (`blueprint_ensemble.py` `_format_constraints()`). The banding hierarchy is:

| Band | Authority Level | Stage 2 Source |
|---|---|---|
| IMMUTABLE | Cannot be overridden | fact_lock_packet, capital_continuity_packet |
| HARD CONSTRAINT | Must obey | must_focus (episode content), stop_line |
| EXPECTED CONTINUITY | Should maintain | location, time, ongoing conflicts, inherited_state |
| ADVISORY | Reference only | **constraint_summary**, state_changes_summary, semantic_carryover |

The LLM is told ADVISORY items are "reference, not mandatory." This means Stage 2's prohibition list competes with supplementary context rather than binding the generator. A blueprint can violate constraint_summary and still pass validation, because no pre-validation or Director check specifically audits constraint_summary compliance.

**Impact**: Stage 2 authority is materially weakened at the point of highest leverage -- the prohibition list that should prevent narrative drift.

---

### F-2. Tactical Doc Regex Fragility (GENERATION-SIDE)

**Severity**: IMPORTANT
**Category**: Stage 2 -> Stage 3 extraction fragility

The constraint_compiler extracts per-episode content from `tactical_doc` using `_EPISODE_HEADER_PATTERNS` regex matching (`tactical_utils.py`). If the tactical_doc uses a non-standard header format:

1. `must_focus.content` falls back to `beat_sequence[arc_position - 1]`
2. If beat_sequence is also empty, it becomes the string "current episode tactical info unavailable"
3. `stop_line` (next episode boundaries) also fails -- the LLM receives NO explicit stop boundary

This is a silent failure: no warning is logged, no pre-validation check catches it. The blueprint generator proceeds with an empty directive and an open boundary.

**Evidence**: In `0_0`, all inspected artifacts have populated must_focus, indicating the regex matched for these episodes. But this is a structural fragility that could silently fail on any non-standard arc format.

---

### F-3. Strategy Directive vs Arc Intent Conflict (GENERATION-SIDE)

**Severity**: IMPORTANT
**Category**: Transformation weakness

Each ensemble strategy (action_focused, emotion_focused, dialogue_focused) injects tone/tension directives (e.g., "tension 7-9/10"). These are concatenated alongside arc constraints in `{strategy_directive}`. No reconciliation mechanism exists when a strategy demands high tension but the arc intends a calm transition episode.

**Artifact evidence**: ep_0001 (action_focused) and ep_0002 (emotion_focused) both produced STRONG results on first attempt, suggesting strategy alignment was good for these episodes. But ep_0006 required 9 attempts (dialogue_focused), which may indicate strategy-arc conflict for that episode type.

---

### F-4. Retry Loop Authority Drift (GENERATION-SIDE)

**Severity**: IMPORTANT
**Category**: Progressive authority degradation

The retry loop (`three_phase_blueprint_runtime.py`) accumulates Director rejection feedback across retries. By retry 3+:

1. **Prompt inflation**: Feedback text grows linearly, diluting original arc instructions
2. **ASP candidate replacement** (retry >= 2): Adversarial Self-Play rewrites `all_candidates[0]` using director_feedback context, not original arc constraints
3. **In-place patch mode**: High-scoring rejected blueprints are patched against Director feedback only, not re-generated from arc authority
4. **Director leniency instruction**: "If retry count >= 2, apply lenient judgment" (director.yaml L952). Scene minimum drops 4 -> 3.

**Artifact evidence**: ep_0005 (attempt_06) ended with only 1 candidate (vs normal 3), 2 prevalidation warnings including CRITICAL fact_lock violation. ep_0006 (attempt_09) shows schema drift (missing `type` field), temporal regression (2/28 -> 2/1). Both carry residual issues the pipeline flagged but could not fix.

---

### F-5. Validator Cannot REJECT Before Director (VALIDATOR-SIDE)

**Severity**: IMPORTANT
**Category**: Validator structural limitation

The unified_blueprint_validator's Python pre-validation is explicitly **advisory-only** ("REJECT authority none" per docstring). The maximum intervention is:

| Mechanism | Effect |
|---|---|
| Advisory issues | Collected, passed to Director as FYI |
| Binding pre-validation (3 categories) | Can upgrade Director PASS -> PASS_WITH_FIX |
| Continuity pre-check | Can REJECT only on CRITICAL continuity issues (in practice: never, because location is MAJOR) |
| Quality gate | Can force-REJECT a Director PASS if score < 90 |

This means structurally inadequate blueprints (no opening anchor, no timeline, vague participants, no mission clarity) can only be caught by the Director's subjective LLM judgment, which uses a **manuscript-oriented rubric** (prose quality, dialogue naturalness) rather than a blueprint-specific rubric.

---

### F-6. Director Uses Manuscript Rubric for Blueprints (VALIDATOR-SIDE)

**Severity**: IMPORTANT
**Category**: Rubric mismatch

The SAME `DIRECTOR_AUDIT_PROMPT_V30` prompt template is used for both manuscript AND blueprint evaluation. The mode flag ("BLUEPRINT" when target_len <= 4000 chars) adjusts some thresholds, but the 5-category rubric remains:

| Category | Weight | Blueprint Relevance |
|---|---|---|
| setting_consistency | 20 | HIGH -- applicable |
| scene_composition | 20 | HIGH -- applicable |
| narrative_flow | 20 | MEDIUM -- different criteria at blueprint level |
| reader_engagement | 20 | LOW -- premature at blueprint stage |
| prose_quality | 20 | LOW -- blueprints are structural, not prose |

40% of the Director's score evaluates dimensions (reader_engagement, prose_quality) that are irrelevant or premature at blueprint stage. This inflates scores for prose-polished but structurally weak blueprints.

---

### F-7. Six Validator Blind Spots (VALIDATOR-SIDE)

**Severity**: IMPORTANT
**Category**: Missing validation coverage

| Dimension | Python Pre-check | Director Rubric | Net Coverage |
|---|---|---|---|
| Opening anchor quality | NONE | Not in rubric | **BLIND** |
| Episode mission clarity | NONE | Not in rubric (closest: narrative_flow) | **BLIND** |
| Timeline specificity in time_flow | NONE | Not in rubric | **BLIND** |
| Scene participant correctness vs arc cast | Only checks empty list | Not specifically rubric'd | **WEAK** |
| protagonist_state consistency | NONE | Not in rubric | **BLIND** |
| Ending hook pickup-ability | NONE | Not in rubric (closest: reader_engagement) | **WEAK** |

These are the dimensions most likely to cause Stage 4 churn: a blueprint can pass validation with no opening anchor, no mission clarity, no timeline, and vague participants.

---

### F-8. Emergency Fallback Accepts Failed Blueprints (VALIDATOR-SIDE)

**Severity**: IMPORTANT
**Category**: Escape hatch quality leak

After exhausting all retries (up to 9), if the best score >= `PatchModeThresholds.REWRITE`, the system accepts the blueprint as `PASS_WITH_WARNING` with `quality_gate_failed=True`. This is by design -- the system cannot block forever. But it means:

1. ep_0005's CRITICAL fact_lock violation survived to production
2. ep_0006's temporal regression and schema drift survived to production
3. Stage 4 receives these blueprints without any signal that they were emergency-accepted (unless it reads `_ensemble_meta.quality_risk`)

---

### F-9. Schema Drift Across Episodes (GENERATION-SIDE)

**Severity**: MINOR
**Category**: Blueprint format inconsistency

| Field | ep_0001/0002 | ep_0005 | ep_0006 | ep_0008 |
|---|---|---|---|---|
| scene `type` | snake_case (opening_hook, etc.) | TitleCase (Action, Tension, etc.) | **MISSING** | snake_case |
| scene `content` | empty | **populated** | empty | partial |
| scene `description` | absent | present | absent | present |
| `location` (top-level) | empty | empty | empty | empty |

This inconsistency means Stage 4 cannot rely on a stable schema contract across episodes. The `type` field absence in ep_0006 is particularly notable -- Stage 4 scene-routing logic may depend on this field.

---

### F-10. semantic_context Token Volume Imbalance (GENERATION-SIDE)

**Severity**: MINOR
**Category**: Context competition

The `semantic_context` aggregates 8 advisory sources (treatment block, timeline advisory, WorldState, StyleGuide, FactLedger, stale seeds, work focus, smart retrieval). At scale (30+ prior episodes), this context can grow very large relative to the compact `must_focus` episode directive. The system mitigates with `smart_truncate` and budget caps, but the ratio is not contractually guaranteed.

In early episodes (0_0 ep_0001-0008), this is unlikely to be an issue because the semantic context is still small. But it is a structural scalability risk.

---

## 3. Non-Issues

### NI-1. integrated_scenario Quality is Universally Strong

All 5 inspected blueprints produce concrete, dialogue-rich, financially specific writing briefs in `integrated_scenario`. This is the primary payload Stage 4 consumes, and it is consistently the strongest field. Lengths: 1,200-2,200 chars, trending upward across episodes.

### NI-2. Capital/State Facts Preservation is Strong

Financial data (amounts, leverages, prices, penalties) is consistently concrete across all 5 artifacts. The constraint_compiler's `capital_continuity_packet` and `fact_lock_packet` (IMMUTABLE band) effectively preserve numerical authority from Stage 2 to Stage 3.

### NI-3. Opening Anchor is De Facto Strong Despite No Validation

Despite no validator check for opening anchor quality, all 5 blueprints have strong opening setups: vivid physical scenes, direct continuity from prior episode endings, specific sensory details. This appears to be an emergent property of the ensemble prompt quality, not a validated contract.

### NI-4. Ending Hook Quality is Generally Good

4 of 5 blueprints have specific, pickup-able ending hooks (physical action, mystery call, cliffhanger dialogue). Only ep_0006 is merely adequate (mission briefing style).

### NI-5. 4-Tier Authority Banding is Sound in Principle

The IMMUTABLE > HARD CONSTRAINT > EXPECTED CONTINUITY > ADVISORY hierarchy is well-designed. The issue is that `constraint_summary` is miscategorized, not that the system itself is broken.

### NI-6. Constraint Block is Comprehensive

The constraint_compiler produces 12 structured fields covering episode focus, stop-line, continuity, inherited state, state changes, fact locks, and capital continuity. The extraction logic is thorough when the source data matches expected formats.

---

## 4. Stage 3 Transform Table

### Authority Preservation Matrix

| Stage 2 Field | Stage 3 Destination | Authority Band | Preservation |
|---|---|---|---|
| tactical_doc (per-ep section) | constraint_block.must_focus | HARD | STRONG -- if regex matches |
| tactical_doc (next-ep section) | constraint_block.stop_line | HARD | STRONG -- if regex matches |
| state_changes | constraint_block.state_changes_summary | ADVISORY | ADEQUATE -- present but non-binding |
| constraint_summary | constraint_block.arc_constraint_summary | **ADVISORY** | **WEAK -- should be HARD** |
| joint_docs | constraint_block.inherited_state | EXPECTED CONTINUITY | ADEQUATE |
| status_shadow | constraint_block.inherited_state | EXPECTED CONTINUITY | ADEQUATE |
| state_constraints | constraint_block.inherited_state | EXPECTED CONTINUITY | ADEQUATE |
| semantic_carryover | constraint_block.semantic_carryover | ADVISORY | ADEQUATE |
| summary | work_focus_text only | ADVISORY (off-band) | WEAK -- not in constraint block |
| block_theme | work_focus_text only | ADVISORY (off-band) | WEAK -- not in constraint block |
| plot_suspension | work_focus_text only | ADVISORY (off-band) | WEAK -- not in constraint block |
| arc_tactical | work_focus_text only | ADVISORY (off-band) | WEAK -- not in constraint block |
| fact_lock_packet (from prior bp) | constraint_block.fact_lock_packet | IMMUTABLE | STRONG |
| capital_continuity_packet | constraint_block.capital_continuity_packet | IMMUTABLE | STRONG |

---

## 5. Validator Blind-Spot Table

| Dimension | Python Pre-check | Binding? | Director Rubric | Can Block REJECT? | Net |
|---|---|---|---|---|---|
| Structure (fields, lengths) | 4 checks | No | scene_composition (20pts) | Via quality_gate only | ADEQUATE |
| Stop-line violation | Token overlap check | No | Not specific | No | ADEQUATE |
| Dead NPC | check_dead_npc_in_blueprint | No | REJECT recommendation | Via Director | ADEQUATE |
| Fact-lock drift | 4 sub-checks (location, item, hook, institution) | No | Not specific | No | ADEQUATE |
| Capital state drift | 2 sub-checks (contradiction, phantom) | No | Not specific | No | ADEQUATE |
| Capital unit alignment | Currency mismatch | **Yes** | Not specific | PASS->PASS_WITH_FIX | ADEQUATE |
| Scene completeness | Empty characters/goals | **Yes** | Not specific | PASS->PASS_WITH_FIX | ADEQUATE |
| Arc timeline alignment | ending_state vs arc | **Yes** | Not specific | PASS->PASS_WITH_FIX | ADEQUATE |
| **Opening anchor** | **NONE** | No | **NONE** | No | **BLIND** |
| **Mission/objective clarity** | **NONE** | No | **NONE** | No | **BLIND** |
| **Timeline specificity (time_flow)** | **NONE** | No | **NONE** | No | **BLIND** |
| **protagonist_state consistency** | **NONE** | No | **NONE** | No | **BLIND** |
| **Scene participant vs arc cast** | Empty-only check | No | **NONE** | No | **WEAK** |
| **Ending hook pickup-ability** | **NONE** | No | reader_engagement (indirect) | No | **WEAK** |

---

## 6. Per-Episode Readiness (Artifact Truth)

| Dimension | ep_0001 | ep_0002 | ep_0005 | ep_0006 | ep_0008 |
|---|---|---|---|---|---|
| Scene Participants | STRONG | STRONG | ADEQUATE | ADEQUATE | STRONG |
| Timeline/Time | STRONG | STRONG | **WEAK** | **WEAK** | ADEQUATE |
| Capital/State Facts | STRONG | STRONG | STRONG | STRONG | STRONG |
| Opening Anchor | STRONG | STRONG | STRONG | STRONG | STRONG |
| Mission Clarity | STRONG | STRONG | ADEQUATE | ADEQUATE | STRONG |
| Scene Breakdown | STRONG | STRONG | STRONG | **ADEQUATE** | STRONG |
| integrated_scenario | STRONG | STRONG | STRONG | STRONG | STRONG |
| Ending Hook | STRONG | STRONG | STRONG | ADEQUATE | STRONG |
| Attempt Count | 1 | 1 | **6** | **9** | 1 |
| quality_risk | true | true | true | true | **false** |
| Prevalidation Warnings | 1 (MINOR) | 1 (MINOR) | **2 (CRITICAL+MAJOR)** | 1 (MINOR) | **0** |
| **Overall** | **STRONG** | **STRONG** | **ADEQUATE** | **ADEQUATE-** | **STRONG** |

---

## 7. Verdict

### stage3-fragile

Stage 3 is **structurally fragile** for Stage 4 progression. It is not blocking -- the pipeline works and produces usable blueprints -- but it has material weaknesses that create avoidable Stage 4 churn.

**Rationale**:

1. **Generation side**: Stage 2's constraint_summary is demoted to ADVISORY band, diluting the prohibition authority that should prevent narrative drift. Retry loops progressively drift from arc intent. 4 Stage 2 fields (summary, block_theme, plot_suspension, arc_tactical) reach the LLM only as weak advisory text, not as structured constraints.

2. **Validator side**: 4 dimensions critical for Stage 4 consumption (opening anchor, mission clarity, timeline specificity, protagonist_state) have ZERO coverage in both Python pre-validation and Director rubric. The Director uses a manuscript rubric where 40% of the score evaluates prose quality -- irrelevant at blueprint stage.

3. **Artifact truth**: First-attempt episodes (0001, 0002, 0008) are STRONG. High-retry episodes (0005 at attempt_06, 0006 at attempt_09) carry residual CRITICAL/MAJOR issues that the pipeline flagged but could not fix. The emergency fallback escape hatch accepts these degraded blueprints.

4. **Distinction**: The fragility is approximately 60% generation-side (authority banding, retry drift, Stage 2 field loss) and 40% validator-side (blind spots, rubric mismatch, no pre-Director REJECT power).

**What "fragile" means concretely**: Episodes where Stage 2 arc authority is strong and strategy alignment is natural pass on first attempt with STRONG blueprints. Episodes where arc authority is ambiguous or strategy-misaligned enter the retry loop, where each retry degrades authority further, ultimately producing ADEQUATE blueprints with known defects. Stage 4 inherits these defects as intake-level risk.

---

## 8. Stop

read-only lane complete; no files mutated
