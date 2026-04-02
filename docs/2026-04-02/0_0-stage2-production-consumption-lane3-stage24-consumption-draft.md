# 0_0 Stage2 Production-Consumption Lane 3: Stage2 → Stage4/Validator/Compiler Consumption Draft

Date: 2026-04-02
Status: draft-bounded-partial-evidence
Document Type: survey lane draft
Master Order: `docs/2026-04-02/0_0-stage2-production-consumption-global-parallel-master-order.md`
Terminal: 3 (Opus)
Role: Stage2 → Stage4 / validator / compiler consumption lane
Baseline Commit: `09a7b478c2a2c16d708cc041aaa6e194278e7f9b`

## 1. Coverage

### Code surfaces inspected

| Surface | Path | Lines inspected |
|---|---|---|
| BlueprintConstraintCompiler | `modules/domain/agents/blueprint_constraint_compiler.py` | Full (L1-670) |
| Stage4ContextBuilder | `modules/core/stage4_context_builder.py` | L1-400, L470-850, L1530-2270 |
| ChiefWriterContextBuilder | `modules/domain/agents/chief_writer_context.py` | Full (L1-617) |
| UnifiedBlueprintValidator | `modules/domain/agents/unified_blueprint_validator.py` | L95-200, L290-550, L690-770, L860-1060, L1655-1775 |

### Prior survey context consumed

| Doc | Key takeaway |
|---|---|
| 03-31 readiness survey | Stage2 content-sufficient but schema-fragile; Stage3 is the primary blocker |
| 04-01 context hierarchy survey | Stage2 partially hierarchical / operationally flattened; Stage3 hierarchical by design but mixed by payload |
| 04-01 simplification memo | Long-term goal is authority handoff reduction, Stage3 compression candidate |

### Scope

This lane traces how Stage2 output fields are consumed by downstream consumers: the constraint compiler, the Stage4 context builder, the blueprint validator, and the CW context builder. It separates:

- which Stage2 fields arrive as hard constraints
- which arrive as advisory/reference
- where authority is demoted, renamed, or duplicated

## 2. Findings

### F-1. `constraint_summary` authority inversion between Stage3 generator and Stage4

**Stage4** (`stage4_context_builder.py:1646-1648`) injects `arc_data["constraint_summary"]` into the Tier-0 mandatory context block as:

```
[Arc 제약 - MUST NOT DO]
{constraint_summary}
```

This is the highest priority band in Stage4. The constraint is treated as a hard prohibition.

However, the prior readiness survey (03-31 Lane 1) established that `BlueprintEnsemble` (the Stage3 generator) places the same `constraint_summary` in the `ADVISORY` band — not in the `IMMUTABLE` or `HARD CONSTRAINT` bands.

**This is an authority-strength inversion.** The downstream consumer (Stage4) treats the field more strictly than the upstream generator (Stage3) that was supposed to have already obeyed it. If Stage3 didn't bind to it, Stage4's hard constraint is a downstream remediation attempt, not an authority-preserving handoff.

### F-2. `tactical_doc` is consumed as raw prose everywhere, never structurally parsed by Stage4

`stage4_context_builder.py:2124-2127` reads `arc_data["tactical_doc"]` into `arc_tactical` (a plain string), used for:

1. **Focus text composition** (`_compose_work_focus_text`, L687-688) — appended first, as raw text
2. **Work identity slot summary** (`_build_work_identity_slot_summary`) — via semantic query broker
3. **Retrieval context queries** (`_collect_stage4_retrieval_context`, L1840-1850) — fed to retrieval as-is
4. **CW prompt** (`chief_writer_context.py:262`) — passed as `arc_doc` parameter, escape-braced only

No Stage4 consumer parses `tactical_doc` into structured fields. Stage4 trusts the raw prose as a reference document, not as a structural contract. This is consistent with the 04-01 finding that Stage2's meaningful truth is mostly in `tactical_doc` prose rather than in structured fields.

### F-3. `state_changes` are consumed for entity discovery, not as behavioral constraints

`stage4_context_builder.py` reads `arc_data["state_changes"]` through two static methods:

- `_collect_npc_roster()` (L276-341): extracts NPC names from 8 sub-fields (`npc_deaths`, `relationship_changes`, `npc_injuries`, `npc_movements`, `npc_attribute_changes`, `npc_personality_changes`, `companion_changes`, `npc_introductions`)
- `_collect_arc_state_entities()` (L344-396): extracts NPCs, items, plots, locations

These are used for:
- Entity extraction for continuity packet
- NPC boundary block (knowledge/identity guidance)
- Retrieval focus queries

**But `state_changes` are NOT consumed as hard behavioral constraints by Stage4.** They are entity discovery aids. The actual behavioral authority flows through `blueprint` fields (Stage3 output) and `constraint_block` (compiler output), not through raw `state_changes`.

### F-4. `constraint_summary` appears under 3 different names/contexts in Stage4

| Location | Name/Label | Band |
|---|---|---|
| `_build_tier0_mandatory_sections` L1646 | `[Arc 제약 - MUST NOT DO]` | Tier-0 mandatory |
| `_build_work_identity_slot_summary` L800-802 | `현재 갈등축` | Work tracking slot summary |
| `SemanticQueryBroker` input L811 | (unlabeled focus text component) | Retrieval query input |

The same Stage2 concept (`constraint_summary`) arrives in Stage4 under three different names with three different purposes:
1. A hard prohibition
2. A conflict axis descriptor
3. A retrieval query seed

This is not catastrophic duplication — each usage serves a distinct purpose. But it means the term `constraint_summary` has drifted into three semantic frames within a single consumer stage.

### F-5. ChiefWriterContextBuilder is properly authority-isolated from Stage2

`chief_writer_context.py` never receives raw `arc_data`. All Stage2 truth arrives through intermediary parameters:

- `arc_doc` (string) — the formatted tactical document
- `blueprint` (dict) — the Stage3 output (already compiled)
- Various Stage4-assembled sections (world_state_summary, chain_link_section, etc.)

This is architecturally sound. CW is a terminal consumer that writes prose, not a Stage2 interpreter. The isolation prevents CW from independently re-parsing Stage2 authority.

### F-6. `semantic_carryover` has an explicit coverage warning confirming it may not survive to Stage4

`stage4_context_builder.py:840-843` defines:

```python
mapping["missing_semantic_carryover"] = (
    "Stage 2 semantic carryover was planned but did not survive into Stage 4 mandatory_context. "
    "Directly restate the relation rationale and continuity anchors."
)
```

This is a built-in coverage warning code that fires when `semantic_carryover` planned by Stage2 is absent from Stage4 mandatory context. The existence of this warning confirms the codebase is aware that Stage2 semantic carryover can be lost in transit — it is not reliably preserved.

### F-7. Validator checks are narrow; key Stage2 authority concepts have no binding validation

`UnifiedBlueprintValidator._python_pre_validate()` runs these checks:

| Check | Stage2 field consumed | Binding? |
|---|---|---|
| Structure (scene count, length) | none | no Stage2 involvement |
| Fidelity (NPC mention) | `state_constraints.relationship_changes` | MINOR severity only |
| Arc compliance (stop-line) | via `constraint_block.stop_line` | CRITICAL |
| Continuity (location) | via `prev_blueprint` | MAJOR |
| Fact-lock drift | via `constraint_block.fact_lock_packet` | via Director |
| Capital state drift | via `constraint_block.capital_continuity_packet` | via Director |
| Timeline alignment | `state_changes.timeline` | MAJOR |
| Tactical semantic fidelity | `tactical_doc` + `episode_details` | CRITICAL |

**Not checked by the validator:**

| Stage2 concept | Consumption status |
|---|---|
| `constraint_summary` prohibitions | Stage4 injects as hard text but validator never checks blueprint compliance |
| `episode_details` coverage | Compiler extracts for stop-line/focus, but validator doesn't verify all items are reflected |
| `semantic_carryover` | Compiler normalizes and passes through, but validator doesn't check if it survives into blueprint |
| `must_focus` content fidelity | Compiler builds from `tactical_doc`, but validator doesn't verify blueprint actually focuses on it |

These are the strongest Stage2 authority concepts, yet they have no binding prevalidation gate.

### F-8. BlueprintConstraintCompiler is the strongest Stage2 consumer, but its output is partially unused

The compiler (`blueprint_constraint_compiler.py:44-136`) produces a well-structured `constraint_block` with 11 named fields:

```python
constraint_block = {
    "ep_num", "arc_no", "arc_position",
    "must_focus", "stop_line", "continuity", "inherited_state",
    "arc_constraint_summary",  # [V63]
    "state_changes_summary",   # [V63.2]
    "semantic_carryover",
    "immutable_fact_carryover", # [IFC]
    "fact_lock_packet",         # [S3-FL]
    "capital_continuity_packet" # [S3-CC]
}
```

This is high-quality structured extraction from Stage2. However:

- `compile_to_prompt()` (the pretty-printer) is **not called in production** (confirmed by 04-01 survey: "repo 내 호출이 없다"). The actual consumer is `BlueprintEnsemble._format_constraints()`.
- The validator only uses a subset: `stop_line`, `must_focus.content`, `fact_lock_packet`, `capital_continuity_packet`.
- `semantic_carryover`, `inherited_state`, and `state_changes_summary` are passed through to the generator but have no validation binding.

## 3. Non-Issues

### N-1. Stage4 is not re-parsing Stage2 authority

Stage4 does not attempt to independently re-derive structured authority from `tactical_doc` prose. It reads `constraint_summary`, `state_changes`, and `arc_no/ep_start/ep_count` as structured fields, and passes `tactical_doc` as a reference document. This is the correct consumption pattern.

### N-2. CW is properly isolated

CW receives pre-assembled context, not raw Stage2 data. This prevents the terminal writer from independently reinterpreting Stage2 contracts.

### N-3. The compiler's structured extraction is sound

`BlueprintConstraintCompiler.compile()` reads the right fields from `arc_data` and produces a well-shaped output. The extraction logic itself is correct. The problem is downstream (incomplete consumption and absent validation), not in the compiler.

### N-4. Validator correctly blocks physical-intrusion invention

The `_collect_tactical_semantic_fidelity_issues()` check (L1701-1765) is a well-designed guard against the specific EP5 fabrication pattern. It reads `tactical_doc`/`episode_details` and checks for unauthorized intrusion markers in the blueprint. This is the strongest binding validation of Stage2 authority.

## 4. Verdict

**`consumer-diluted`**

Stage2 truths are consumed by the downstream pipeline, but authority is systematically diluted at three levels:

1. **Authority-strength inversion**: Stage4 treats `constraint_summary` as hard constraint, but Stage3 generator treats it as advisory. The generator is the one that should bind hardest, since it produces the blueprint. The downstream remediation in Stage4 is backward.

2. **Term drift within Stage4**: `constraint_summary` appears under 3 names/purposes in one stage. Not harmful yet, but it fragments the concept.

3. **Validation gap**: The validator checks stop-line, timeline, and intrusion markers well. But it does NOT validate that `constraint_summary` prohibitions, `must_focus` content, or `semantic_carryover` concepts are actually obeyed by the blueprint. These are the primary Stage2 authority concepts.

The strongest consumer is the BlueprintConstraintCompiler, which produces clean structured output. But the chain weakens after that: the generator binds loosely, the validator checks narrowly, and Stage4 injects remediation text that would have been more effective as an upstream gate.

The weakest link is not Stage4 consumption itself (which is architecturally sound), but the fact that Stage2's strongest concepts pass through Stage3 generation with advisory binding and arrive at Stage4 as raw text patches rather than structurally enforced constraints.

## Stage2 Consumer Matrix

| Consumer | Stage2 fields consumed | Authority treatment |
|---|---|---|
| BlueprintConstraintCompiler | `tactical_doc`, `episode_details`, `beat_sequence`, `constraint_summary`, `state_changes`, `semantic_carryover`, `joint_docs`, `status_shadow`, `state_constraints`, `ep_start`, `ep_count`, `arc_no` | Structured extraction → named fields |
| UnifiedBlueprintValidator | `arc_no`, `tactical_doc`, `ep_start`, `ep_count`, `state_constraints.relationship_changes`, `state_changes.timeline`, `episode_details` | Narrow binding checks; wide gaps |
| Stage4ContextBuilder | `tactical_doc` (as raw string), `constraint_summary`, `state_changes` (entity roster), `ep_start`, `ep_count`, `arc_no`, `goal`, `core_conflict`, `hook` | Mixed: constraint_summary as hard; rest as reference |
| ChiefWriterContextBuilder | None directly; receives `arc_doc` string and assembled context | Properly isolated |

## Authority-Strength Comparison Table

| Stage2 concept | Compiler output | Stage3 generator binding | Validator binding | Stage4 injection |
|---|---|---|---|---|
| `constraint_summary` | `arc_constraint_summary` field | **ADVISORY** band | **None** | **Tier-0 MUST NOT DO** |
| `tactical_doc` → episode focus | `must_focus.content` | Generation seed | Semantic fidelity check (intrusion only) | Focus text, retrieval query |
| `episode_details` | `stop_line`, `must_focus` | Not directly checked | Stop-line overlap check | Not consumed directly |
| `state_changes` (NPC/items) | `state_changes_summary` | Generation context | Relationship NPC mention (MINOR) | Entity roster, NPC boundary |
| `semantic_carryover` | Normalized passthrough | Generation context | **None** | Missing-carryover warning |
| `state_constraints` | `inherited_state` | Generation context | Timeline alignment (MAJOR) | Not consumed directly |
| `fact_lock_packet` | Extracted from prev canon | Top of constraint prompt | Director-deferred | Immutable fact section |
| `capital_continuity_packet` | Extracted for investment genre | Prompt injection | Director-deferred | Not consumed directly |

Key pattern: **authority climbs downstream** for `constraint_summary` (advisory in Stage3 → hard in Stage4) — which is structurally inverted. The generator that should bind hardest binds loosest.

## Stop

read-only lane complete; no files mutated
