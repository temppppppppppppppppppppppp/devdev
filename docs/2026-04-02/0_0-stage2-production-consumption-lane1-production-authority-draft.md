Date: 2026-04-02
Status: draft-bounded-partial-evidence
Document Type: lane survey draft (lane 1 of 5)
Canonical Path: `docs/2026-04-02/0_0-stage2-production-consumption-lane1-production-authority-draft.md`
Track: system
Mode: read-only survey
Baseline Commit: `09a7b478c2a2c16d708cc041aaa6e194278e7f9b`

# Lane 1: Stage2 Production Authority

## 1. Coverage

Surfaces inspected:

- `modules/domain/agents/arc_ensemble.py` (1,400+ lines) — full read
- `config/prompts/ensemble.yaml` (ENSEMBLE_ARC_PROMPT, BLUEPRINT_GENERATION_PROMPT) — full read
- `modules/domain/agents/four_phase_arc_runtime.py:710-750` — constraint block assembly
- `projects/0_0/plans/arcs/arc_001.txt` — saved tactical artifact
- `projects/0_0/plans/arcs/arc_002.txt` — saved tactical artifact
- `projects/0_0/logs/artifacts/stage2/arc_001/attempt_01/final_arc__creative.json` — raw JSON schema shape
- `projects/0_0/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json` — raw JSON schema shape + structured field content
- `projects/0_1/plans/` — confirmed no `arcs/` directory exists; blueprints only
- `projects/0_1/logs/artifacts/stage2/` — confirmed empty
- Prior survey: `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-parallel-bounded-survey.md`
- Prior survey: `docs/2026-04-01/0_0-stage2-stage3-context-hierarchy-bounded-survey.md`
- Prior memo: `docs/2026-04-01/stage23-architecture-simplification-long-term-memo.md`

Not inspected (out of lane scope):

- Stage3 consumer code (lane 2)
- Stage4 consumer code (lane 3)
- Full artifact vertical slices (lane 4)

## 2. Findings

### F-1. Stage2 Output Field Authority Classification

| Field | Authority Level | Shape | Evidence |
|-------|----------------|-------|----------|
| `arc_no` | **hard truth** | int | identifier, deterministic |
| `ep_start`, `ep_end`, `ep_count` | **hard truth** | int | range, normalized by `_normalize_pacing_contract` |
| `volume_no`, `global_arc_no` | **hard truth** | int | position identifiers, injected by Python |
| `tactical_doc` | **mission** (core authority) | str, 2900-4300+ chars | per-episode narrative plan; carries the bulk of real meaning; **unstructured prose** |
| `state_constraints` | **hard truth** | dict (4 keys) | `arc_start_state`, `arc_end_state`, `items_acquired`, `items_consumed` |
| `joint_docs` | **hard truth** | dict (3 keys) | `final_location`, `physical_inventory`, `world_joint` |
| `state_changes` | **hard truth** | dict (7-16 sub-fields) | timeline, npc_deaths, skill_acquisitions, relationship_changes, etc. — **schema-variable** |
| `episode_details` | **mission** (thin) | list[dict] | per-ep key events; only ~1 sentence per episode |
| `beat_sequence` | **carryover** | list[str] | per-ep one-line summaries paralleling tactical_doc |
| `pacing_decision` | **advisory** | dict (3 keys) | pace_mode, ep_count_reasoning, density_focus |
| `status_shadow` | **advisory** | dict (3 keys) | expected_injuries, item_consumption, key_stat_change |
| `hybrid_composition` | **advisory** | dict (3 keys) | primary/secondary narrative patterns |
| `constraint_summary` | **carryover** | str | prohibition block for next arc; prohibition-focused, not authority-preserving |
| `semantic_carryover` | **advisory** (dead) | dict | designed as structured bridge; **empty in both arc_001 and arc_002** |
| `arc_drive` | **advisory** | dict (3 keys) | narrative_drive, short_term_objective, status |
| `_ensemble_meta` | **internal** | dict | scoring metadata; not passed to downstream |
| `_strategy` | **internal** | str | which generation strategy produced this candidate |

### F-2. Core Authority Lives in Prose, Not in Structured Fields

The **real Stage2 authority** is `tactical_doc`. This field contains 2,900-4,300+ characters of episode-by-episode narrative planning with:

- per-episode start/end states (location, equipment, injuries, mental state)
- concrete scene descriptions and character interactions
- tactical progression and plot beats

Evidence: compare `arc_001.txt` (~2,948 chars, 4 episodes) and `arc_002.txt` (~4,312 chars, 5 episodes). Both carry rich, detailed, episode-by-episode prose with explicit checkpoint states.

**Problem**: `tactical_doc` is unstructured prose. Downstream consumers (Stage3, Stage4) cannot machine-parse it and must re-interpret it through their own LLM calls. This is the structural root of the "reinterpretation drift" identified in prior surveys.

### F-3. Structured Fields Are Correct But Thin

`state_constraints` has only 4 top-level keys:
- `arc_start_state`: location, equipment, injuries (+ genre field)
- `arc_end_state`: location, equipment, injuries (+ genre field)
- `items_acquired`: list
- `items_consumed`: list

This covers physical state transitions but does **not** cover:
- narrative authority (what should happen in each episode)
- scene authority (locations, characters, interactions per episode)
- relationship/conflict state transitions per episode
- stop-line contract (what the arc must NOT touch)

These are all embedded in `tactical_doc` prose.

### F-4. `semantic_carryover` is Dead

Both inspected arcs (`arc_001/final_arc__creative.json` and `arc_002/final_arc__balanced.json`) have `semantic_carryover: {}` (empty dict). This field was designed to carry structured semantic meaning forward but is not populated by the LLM.

### F-5. `episode_details` is Too Thin for Authority Transfer

`episode_details` provides only 1 detail string per episode. Example from arc_002:

```json
{"details": ["한시우가 박성호 PB의 만류를 무시하고 15억 원 규모의 WTI 6월물 3배 레버리지 매수를 지시함"], "ep_num": 5}
```

This is a 1-sentence summary. It cannot serve as a binding contract for Stage3 blueprint generation. The full episode authority remains in `tactical_doc` prose.

### F-6. Schema Instability Across Arcs

`state_changes` has 7 keys in arc_001 but 8 in arc_002 (added `npc_martial_state_changes`). The prompt template requests 16+ sub-fields (see ensemble.yaml L157-228), but LLM output shape varies. The `_ensure_required_fields` method provides fallbacks for critical top-level fields but does not normalize `state_changes` sub-field presence.

### F-7. Prompt Hierarchy Is Declared But Not Machine-Enforced

The prompt template declares a priority contract:
```
[Context Priority Contract]
1. prohibition_summary and constraint_block are absolute.
2. Current Block DNA and Current Block Event Guard define what this block may do.
3. Previous Arc Context is carryover reference and must not override 1-2.
```

This hierarchy is a text instruction to the LLM. Python code does not validate that the LLM response respects this priority. Validation (`_evaluate_candidate`) checks field presence, constraint compliance, continuity, and tactical length — but does not check whether the response respected context priority semantics.

### F-8. Constraint Block Assembly is Hierarchy-Intent but Operationally Flat

The `full_constraint_block` (built at `four_phase_arc_runtime.py:729-739`) concatenates:
1. genre energy warning
2. PREFLIGHT analysis
3. HARD CONSTRAINTS (compiled)
4. NEGATIVE EXAMPLES
5. SELF-CHECK

Each section has a header (`### [PREFLIGHT 분석]`, `### [HARD CONSTRAINTS — 절대 금지]`, etc.), but the result is a single flat string. No structural separator tells the LLM which constraints are binding vs informational.

### F-9. `constraint_summary` is Prohibition-Focused

The `constraint_summary` field saved with the arc artifact (599 chars in arc_002) is primarily a list of prohibited item re-acquisitions and negative constraints. It does **not** summarize what the arc positively authorizes. This means the forward-carried constraint contract is "what NOT to do" focused, not "what this arc established as truth" focused.

## 3. Non-Issues

### NI-1. Tactical Content Quality is Not the Problem

The actual `tactical_doc` prose is rich, detailed, and well-structured as natural language. Each episode has explicit `[시작 상태]`/`[종료 상태]` checkpoints with location, equipment, injuries, and mental state. The problem is not content quality; it is content packaging (prose vs structured contract).

### NI-2. Python Scoring/Evaluation is Sound

`_evaluate_candidate()` uses a 100-point rubric across 4 dimensions:
- Required field completeness (20 points)
- Constraint compliance (30 points)
- Continuity (25 points)
- Tactical doc quality (25 points)

This is well-designed and catches structural defects.

### NI-3. Ensemble Strategy Diversity is Functional

3 strategies (conservative/balanced/creative) with temperature variation (0.3/0.5/0.7), parallel generation, scoring, and Director selection work correctly. The `_build_strategy_execution_plan` method adjusts temperatures based on recent win rates.

### NI-4. Pacing Signal Flow is Clean

Python collects pacing signals (content length, sentence count, tension level, item hints, resource presence) and passes them as advisory signals. The LLM decides final `ep_count`. Python then normalizes via `_normalize_pacing_contract`. Clean producer-consumer contract.

### NI-5. Constraint Generation Pipeline is Comprehensive

The 4-phase constraint assembly (preflight analysis → compiled constraints → negative examples → self-check) covers the necessary safety envelope.

## 4. Stage2 Authority Packet Table

```
┌──────────────────────────┬──────────────────┬───────────────────────────────────────────────┐
│ Field                    │ Authority Band   │ Downstream Binding Strength                   │
├──────────────────────────┼──────────────────┼───────────────────────────────────────────────┤
│ arc_no, ep_start/end     │ HARD TRUTH       │ Deterministic, machine-enforced               │
│ state_constraints        │ HARD TRUTH       │ Schema-stable, thin (4 keys)                  │
│ joint_docs               │ HARD TRUTH       │ Schema-stable, thin (3 keys)                  │
│ state_changes            │ HARD TRUTH       │ Schema-variable (7-16 sub-fields)             │
│ tactical_doc             │ MISSION          │ Core authority, but unstructured prose         │
│ episode_details          │ MISSION (thin)   │ 1 sentence/ep — insufficient for binding      │
│ beat_sequence            │ CARRYOVER        │ Parallel summaries, not additive              │
│ constraint_summary       │ CARRYOVER        │ Prohibition-focused, not authority-preserving  │
│ pacing_decision          │ ADVISORY         │ Informational only                            │
│ status_shadow            │ ADVISORY         │ Informational only                            │
│ hybrid_composition       │ ADVISORY         │ Informational only                            │
│ semantic_carryover       │ ADVISORY (dead)  │ Empty in practice                             │
│ arc_drive                │ ADVISORY         │ Informational only                            │
└──────────────────────────┴──────────────────┴───────────────────────────────────────────────┘
```

## 5. Stage2 Term Inventory Table

| Stage2 Term | Code Surface | Live in Artifact? | Downstream Consumer Term (if different) |
|-------------|-------------|-------------------|----------------------------------------|
| `tactical_doc` | arc_ensemble.py L106, ensemble.yaml L106 | Yes (str, 2900-4300+ chars) | Stage3: extracted via LLM as `arc_focus` |
| `state_constraints` | arc_ensemble.py L1276, ensemble.yaml L114-149 | Yes (dict, 4 keys) | Stage3: consumed as `inherited_state` by compiler |
| `joint_docs` | arc_ensemble.py L1414, ensemble.yaml L147-150 | Yes (dict, 3 keys) | Stage3: consumed for location/inventory |
| `state_changes` | ensemble.yaml L153-228 | Yes (dict, 7-16 keys) | Stage3 compiler: `state_changes_summary` |
| `episode_details` | ensemble.yaml L225-236 | Yes (list, 1 sent/ep) | Stage3: used for episode-level targeting |
| `constraint_summary` | arc_ensemble.py L599+ | Yes (str, 0-599 chars) | Stage3 compiler: `arc_constraint_summary` |
| `status_shadow` | arc_ensemble.py L1417-1423 | Yes (dict, 3 keys) | Minimal downstream use |
| `semantic_carryover` | ensemble.yaml implied | Empty in practice | Dead channel |
| `beat_sequence` | ensemble.yaml L107 | Yes (list) | Minimal downstream use |
| `pacing_decision` | arc_ensemble.py L895-926 | Yes (dict, 3 keys) | Not consumed downstream as authority |
| `arc_drive` | artifact only | Yes (dict, 3 keys) | Shape-variable per arc |
| `hybrid_composition` | ensemble.yaml L108-111 | Yes (dict, 3 keys) | Not consumed downstream as authority |
| `constraint_block` | four_phase_arc_runtime.py L729-739 | Not saved in artifact | Stage2-internal; rebuilt per generation |
| `prev_arc_context` | four_phase_arc_generator.py L1225-1604 | Not saved in artifact | Stage2-internal; carries history context |

## 6. Verdict

**`stage2-schema-fragile`**

Stage2 is content-sufficient but schema-fragile.

Evidence summary:

1. **Content richness**: `tactical_doc` provides detailed episode-by-episode narrative plans with explicit state checkpoints. The quality of prose output is high.
2. **Schema fragility**: The boundary between structured hard truth (`state_constraints`, `joint_docs`) and unstructured mission authority (`tactical_doc`) is the core weakness. Most of the real authority lives in prose that must be re-interpreted by downstream consumers.
3. **Thin structured contract**: `episode_details` (~1 sentence/ep) and `constraint_summary` (prohibition-focused) are too thin to serve as binding downstream contracts.
4. **Dead fields**: `semantic_carryover` is consistently empty despite being designed as a structured bridge.
5. **Schema instability**: `state_changes` sub-field count varies between arcs. `arc_drive` key structure varies.
6. **Priority hierarchy declared but not enforced**: The prompt `[Context Priority Contract]` is a text instruction, not a machine-validated gate.

The core structural issue is not that Stage2 produces bad content — it produces good content. The issue is that Stage2's core authority is trapped in prose (`tactical_doc`), and its structured fields are either too thin (`episode_details`, `constraint_summary`), too variable (`state_changes`), or dead (`semantic_carryover`) to serve as a reliable authority handoff contract.

This is consistent with the prior 2026-03-31 survey verdict ("Stage 2 is content-rich but shape-unstable") and the 2026-04-01 hierarchy survey finding ("Stage2 partially hierarchical, operationally flattened").

## 7. Stop

read-only lane complete; no files mutated
