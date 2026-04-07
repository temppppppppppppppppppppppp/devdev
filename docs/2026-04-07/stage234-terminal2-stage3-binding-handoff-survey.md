# Stage234 Terminal 2 — Stage3 Binding / Blueprint Handoff Survey

Date: 2026-04-07
Status: final
Document Type: read-only terminal survey
Canonical Path: `docs/2026-04-07/stage234-terminal2-stage3-binding-handoff-survey.md`
Track: system
Mode: read-only survey; no code patching; no docs/temp mutation
Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: active temp roadmap/queue mirrors plus widespread narrative/output/docs deltas`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Confidence: `96%`

## 1. Coverage

### Read

- `AGENTS.md`
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/implementation/commit-state-minimal-contract.md`
- `docs/stage_map/interfaces.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`
- `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md`
- `modules/core/stage3_orchestrator.py` (full — lines 0–2170+)
- `modules/domain/agents/three_phase_blueprint_runtime.py` (lines 0–100)
- `modules/domain/agents/blueprint_constraint_compiler.py` (full — lines 0–640+)
- `modules/domain/agents/blueprint_ensemble.py` (lines 0–100)
- `modules/domain/agents/unified_blueprint_validator.py` (full — lines 0–1170+)
- `modules/domain/agents/chief_writer_context_packets.py` (lines 0–100)

### Intentionally excluded

- Stage4 consumer-side code (Terminal 3 scope)
- Stage2 producer-side code (Terminal 1 scope)
- Cross-stage matrix construction (Terminal 4 scope)
- `docs/temp/` mutation
- Code patching

## 2. Findings

Ordered by severity.

### F1. `_stage3_meta` handoff is advisory-only, not a binding Stage4 intake contract (boundary-local)

**Severity: HIGH**

Stage3 annotates blueprints with `_stage3_meta` at `stage3_orchestrator.py:2005`:

```python
blueprint["_stage3_meta"] = {
    "final_verdict": final_verdict,
    "quality_gate_failed": quality_gate_failed,
    "quality_risk": quality_risk,
    "revision_required": revision_required,
    "last_score": pipeline_result.get("last_score", 0),
}
```

Stage4 consumers read this only in two narrow advisory paths:
- `stage4_director_runtime.py:1183-1190` — injects a Director advisory string if `quality_risk` is true
- `stage4_outcome_runtime.py:939-958` — lowers inplace-repair threshold if `quality_risk` is true

**No Stage4 intake path uses `_stage3_meta.revision_required`, `_stage3_meta.final_verdict`, or `_stage3_meta.quality_gate_failed` for any structured decision.** These fields survive transport (they sit inside the persisted blueprint JSON) but are semantically dead by Stage4's actual consumer flow. The `revision_required` flag is especially important: Stage3 raises it when `PASS_WITH_FIX` or `PASS_WITH_WARNING` verdicts land, but Stage4 never reads it to tighten its own repair escalation.

**Owner:** `modules/core/stage3_orchestrator.py` (emitter), `modules/core/stage4_director_runtime.py` / `modules/core/stage4_outcome_runtime.py` (partial consumer)

---

### F2. Binding prevalidation scope is narrow; most Python prevalidation issues are advisory-only (stage-local)

**Severity: HIGH**

`unified_blueprint_validator.py:53-62` defines `_BINDING_PREVALIDATION_CATEGORIES`:

```python
_BINDING_PREVALIDATION_CATEGORIES = {
    "scene_completeness",
    "arc_timeline",
    "capital_unit",
    "opening_anchor",
    "mission_clarity",
    "timeline_specificity",
    "protagonist_state",
    "fact_lock_institution",
    "tactical_semantic_fidelity",
}
```

The binding contract (`_apply_binding_prevalidation_contract`, line 211) only escalates to `PASS_WITH_FIX` for issues in these 9 categories with `MAJOR` or `CRITICAL` severity. All other prevalidation findings — including `dead_npc`, `fact_lock_location`, `fact_lock_item`, `stop_line_violation`, `scenario_density`, `scene_specificity`, `scene_characters` — remain **advisory-only**. They are passed to Director as `python_warnings` but have no binding escalation path.

This means a blueprint can survive Stage3 validation with a factual location drift, an item-state contradiction, or a stop-line violation if the Director LLM does not independently catch and reject it. The Python prevalidation detected the issue but could not enforce it.

**Owner:** `modules/domain/agents/unified_blueprint_validator.py`

---

### F3. `constraint_summary` undergoes strength inversion at compile (stage-local → boundary-local)

**Severity: MEDIUM**

Stage2 produces `constraint_summary` as a machine-meaningful MUST NOT DO field at the Arc level. The constraint compiler at `blueprint_constraint_compiler.py:91-93` passes it through as `arc_constraint_summary`:

```python
arc_constraint_summary = arc_data.get("constraint_summary", "")
```

Then `compile_to_prompt` at line 252 renders it as a `### 🚫 ARC 제약 (MUST NOT DO)` prose section in the prompt. By the time this reaches Stage4, it is already flattened: Stage4's `stage4_context_builder.py:812-814` reads `constraint_summary` from the arc and re-renders it as `- 현재 갈등축:` — a weaker advisory reframe that drops the MUST NOT DO enforcement semantic.

The constraint survives transport cleanly (the raw string persists in `arc_data`), but each stage re-interprets and re-renders it independently, with progressive strength dilution from hard prohibition → prompt section → advisory context line.

**Owner:** `modules/domain/agents/blueprint_constraint_compiler.py` (Stage3 transport), `modules/core/stage4_context_builder.py` (Stage4 re-render)

---

### F4. `state_changes_summary` is a one-way summary with no reverse verification (stage-local)

**Severity: MEDIUM**

The constraint compiler at `blueprint_constraint_compiler.py:96` calls `_summarize_state_changes(arc_data.get("state_changes", {}), ep_num)` to build a prose summary of cumulative state changes up to the current episode. This summary is injected into the constraint block as `state_changes_summary` and rendered as `### 📊 상태 변화 (현재 화까지 확정된 이벤트)`.

However, the summary is a lossy compression of the structured `state_changes` dict. The original dict contains typed entries (`npc_movements`, `items_acquired`, `resolved_plots`, `active_plots`, `major_items`) that are directly usable as structured constraints. The summarized prose version cannot be machine-verified against the generated blueprint — it exists only as LLM advisory context.

Stage4's `stage4_context_builder.py:291-400` reads the same raw `state_changes` dict directly from `arc_data` for NPC candidate collection and entity extraction, bypassing the Stage3 summary entirely. This parallel consumption path means the summary is effectively a Stage3-local artifact that neither Stage3 nor Stage4 verifies downstream.

**Owner:** `modules/domain/agents/blueprint_constraint_compiler.py`

---

### F5. `semantic_carryover` is transported but low-signal (stage-local)

**Severity: LOW**

`blueprint_constraint_compiler.py:97` extracts `semantic_carryover` from `arc_data` and normalizes it. The `compile_to_prompt` method renders it as `### ARC semantic carryover` at the top of the constraint block. However, as documented in the Stage2 SSOT baseline facts: "`semantic_carryover` behaves like a dead or low-signal field in current practice."

Stage3 faithfully transports it, but neither Stage3 validation nor Stage4 intake treats it as a meaningful constraint. It occupies prompt space without contributing measurable binding value.

**Owner:** `modules/domain/agents/blueprint_constraint_compiler.py`

---

### F6. `beat_sequence` is a tertiary fallback with no forward contract (stage-local)

**Severity: LOW**

`blueprint_constraint_compiler.py:287-296` uses `beat_sequence` as a fallback when `tactical_doc` and `episode_details` extraction fails:

```python
if not content:
    beats = arc_data.get("beat_sequence", [])
    if arc_position - 1 < len(beats):
        content = beats[arc_position - 1]
```

Similarly for stop-line extraction at line 396-399. `beat_sequence` is also used in `_extract_stop_line` as a last resort. However, `beat_sequence` items can be dicts or strings (line 293-296 handles both), and the field itself is effectively dropped at the Stage2→Stage3 boundary as documented in the cross-stage SSOT. It serves only as an emergency fallback, not a contracted handoff surface.

**Owner:** `modules/domain/agents/blueprint_constraint_compiler.py`

---

### F7. Blueprint persistence omits pipeline-level observability metadata (boundary-local)

**Severity: MEDIUM**

`stage3_orchestrator.py:2085` persists the blueprint via `save_episode_blueprint(working_ep, blueprint)`. The persisted dict includes `_stage3_meta` (5 fields) and optionally `_inventory_gaps` and `_continuity_pins`.

However, the richer pipeline-level observability — `semantic_ctx_chars`, `semantic_ctx_sources`, `coverage_warnings`, `advisor_path_used`, `provenance_ledger`, `budget_ledger` — is computed by `_build_stage3_observability_flags` (line 69-87) and written only to `stage_attempts` DB table and JSONL logs, not to the blueprint itself. Stage4 therefore has no access to these signals when reading the blueprint dict.

This is relevant because `coverage_warnings` could inform Stage4 whether the blueprint was generated under partial context (e.g., missing semantic retrieval coverage). Stage4 currently treats all blueprints as equally well-informed, regardless of their context coverage at generation time.

**Owner:** `modules/core/stage3_orchestrator.py` (emitter), `modules/core/stage4_context_builder.py` (implicit non-consumer)

## 3. Authority / Loss Map

| Authoritative Surface | Actual Consumer Surface | Loss / Compression Point |
|---|---|---|
| `_stage3_meta` (5 fields: `final_verdict`, `quality_gate_failed`, `quality_risk`, `revision_required`, `last_score`) | Stage4 reads only `quality_risk` in 2 advisory paths | `revision_required`, `final_verdict`, `quality_gate_failed` are dead fields downstream |
| `_BINDING_PREVALIDATION_CATEGORIES` (9 categories) | Only MAJOR/CRITICAL in those 9 categories trigger `PASS_WITH_FIX` | All other Python prevalidation findings (dead NPC, fact-lock, stop-line, density) are advisory-only |
| `constraint_summary` → `arc_constraint_summary` → MUST NOT DO prompt section | Stage4 re-reads raw `constraint_summary` from `arc_data` and renders as `현재 갈등축:` | Strength inversion: hard prohibition → advisory context line |
| `state_changes` dict → `state_changes_summary` prose | Stage4 reads raw `state_changes` dict directly, ignores Stage3 summary | Stage3 summary is orphaned; no consumer |
| `semantic_carryover` field | Rendered as prompt section; no downstream machine consumer | Dead or near-dead signal field |
| `beat_sequence` fallback | Emergency-only fallback inside compiler | No forward contract; dropped at Stage3 boundary |
| Pipeline observability flags (semantic_ctx_chars, coverage_warnings, etc.) | Written to stage_attempts and JSONL; not in blueprint dict | Stage4 has no visibility into blueprint generation context quality |

## 4. Non-Issues

### N1. Blueprint transport is clean

The blueprint dict itself is persisted to DB via `save_episode_blueprint` and retrieved by Stage4 via `get_blueprint`. The DB→JSON→dict round-trip is reliable. The `interfaces.md` contract is honored: Stage4 receives the full blueprint dict. There is no transport-level data loss.

### N2. Fact-lock and capital-continuity packets are well-structured

`blueprint_constraint_compiler.py` builds `fact_lock_packet` (line 552-637+) and `capital_continuity_packet` (line 112-117) with structured `anchors` and `fields`. These are rendered into the prompt with clear emoji-marked sections and explicit REJECT language. The problem is not packet quality but binding scope — the validator cannot enforce them.

### N3. Continuity pins are applied post-validation

`apply_continuity_pins` (line 2043-2054) is applied after validation succeeds. This is architecturally correct — pins fix continuity drift without reopening the validation loop. Unresolved pins are logged and audited.

### N4. Stage3 lazy-init of StateTracker/WorldState/FactLedger is correct

The `_init_*_if_needed` methods (lines 709-769) are idempotent and correctly documented as the authoritative lazy-init source on the Stage2→3→4 path. Stage4 gateway re-runs them as fallback only for Stage-3-skip flows.

## 5. Owner Verdict

The narrowest plausible owner set for a future Stage3 binding harness wave:

1. **`modules/domain/agents/unified_blueprint_validator.py`** — owns the binding prevalidation scope, the advisory/binding boundary, and the `_BINDING_PREVALIDATION_CATEGORIES` set. Widening binding scope here directly closes the enforcement gap in F2.

2. **`modules/core/stage3_orchestrator.py`** — owns `_stage3_meta` emission (F1) and pipeline observability persistence decisions (F7). Adding `coverage_warnings` or `revision_required` to the persisted blueprint dict would require changes here.

3. **`modules/domain/agents/blueprint_constraint_compiler.py`** — owns `constraint_summary` strength rendering (F3), `state_changes_summary` lossy compression (F4), and low-signal field transport (F5, F6). If the long-term direction is stronger structured constraint handoff, the compiler is the owner.

For the most bounded next action, `unified_blueprint_validator.py` alone would close the highest-severity gap (F2) by widening `_BINDING_PREVALIDATION_CATEGORIES` to include `fact_lock_location`, `fact_lock_item`, `dead_npc`, and `stop_line_violation`.

## 6. Promotion Signal

`covered-by-existing-queue`

Rationale:

- F1 (`_stage3_meta` advisory-only handoff) maps to the existing parked `0_0-stage3-contract-tightening-remediation` lane's Tranche 3 (semantic handoff preservation) plus the existing `0_0-stage234-cross-stage-contract-normalization-remediation` lane's owner-matrix work.
- F2 (binding scope gap) is the primary focus of the existing `0_0-stage3-contract-tightening-remediation` lane's Tranche 1 (binding scope tightening).
- F3 (constraint_summary strength inversion) spans Stage3 and Stage4 and is covered by the existing cross-stage normalization lane.
- F4–F6 are lower severity and internal to Stage3; they can be addressed when the Stage3 tightening lane is activated.
- F7 (pipeline observability gap) is bounded and can be folded into the Stage3 tightening lane without a new execution SSOT.

No finding identified a debt category with bounded execution potential that is completely uncovered by the existing queue.

## 7. Stop

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-07 output
