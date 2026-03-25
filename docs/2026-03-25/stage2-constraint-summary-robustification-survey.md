# Stage 2 `constraint_summary` Robustification — Compact Survey

Date: 2026-03-25
Status: final (3-pass audited)
Document Type: survey (compact, survey-only)
Canonical Path: `docs/2026-03-25/stage2-constraint-summary-robustification-survey.md`
Commit State:
- Baseline Commit: `f61a35c89b4c964afbfa902790560448d98b1bfb`
- Baseline Dirty Summary: `dirty: Wave1+self-audit landed (uncommitted), canary_0325 artifacts, prior survey/SSOT docs`

## 1. Governing Question

Is `constraint_summary` currently too thin or fragile to carry meaningful Stage 2 → Stage 3 guidance, and what is the smallest bounded improvement with the best ROI?

## 2. Evidence Surfaces Examined

### Code (directly read)

| File | Line(s) | Role |
|------|---------|------|
| `modules/core/stage2_finalizer.py` | L1045-1058 | **Production**: keyword filter on ConstraintDB block |
| `modules/core/constraint_db.py` | L438-522 | **Source**: `generate_constraint_block()` — item/inventory/grants/state block |
| `modules/domain/agents/blueprint_constraint_compiler.py` | L90-93, L127, L250-254 | **Pass-through**: arc_data → constraint_block dict → prompt text |
| `modules/domain/agents/blueprint_ensemble.py` | L960-970 | **Consumption**: placed in Band 4 ADVISORY (lowest priority) |
| `modules/domain/agents/blueprint_ensemble.py` | L846-1050 | **Authority banding**: 4-tier format with explicit priority headers |
| `modules/core/stage2_validation_pipeline.py` | (all) | **0 references** to constraint_summary |
| `modules/core/stage3_orchestrator.py` | L260, L378, L388 | **Secondary consumption**: focus text + SemanticQueryBroker |
| `modules/core/stage4_context_builder.py` | L692, L800-802, L811, L1617-1619 | **Stage 4 consumption**: multi-point |
| `modules/models/arc.py` | L209 | **Schema**: `constraint_summary: str = ""` (Pydantic, optional) |

### Artifacts (directly read)

| Artifact | constraint_summary state |
|----------|-------------------------|
| Arc 1 (0324_00_, conservative) | **empty** (0 chars) |
| Arc 2 (0324_00_, balanced) | **present** (601 chars) — item prohibition lines only |
| Canary arcs[0] (Arc 1) | **empty** (0 chars) |
| Canary arcs[1] (Arc 2) | **present** (624 chars) — item prohibition lines only |
| Blueprint artifacts (EP1-EP4) | **not persisted** — prompt-time injection only |

## 3. Findings

### F-1. `constraint_summary` is produced by a 3-keyword line filter on ConstraintDB output

`stage2_finalizer.py:1055-1058`:
```python
if constraint_block:
    constraint_lines = constraint_block.strip().split("\n")
    must_not = [line.strip() for line in constraint_lines
                if "금지" in line or "MUST NOT" in line or "절대" in line]
    refined_arc["constraint_summary"] = "\n".join(must_not[:10]) if must_not else ""
```

The `constraint_block` parameter is a string from `ConstraintDB.generate_constraint_block()` (`constraint_db.py:438-522`), which produces an ASCII-box block containing:
1. Forbidden items (already acquired — reacquisition prevention)
2. Current inventory
3. Previously granted rights/passes
4. Prior arc end state (location, injuries, internal energy)

The keyword filter (`"금지"`, `"MUST NOT"`, `"절대"`) only reliably captures lines from sections 1 (forbidden items) and the header. Sections 2-4 (inventory, grants, state) do not contain these keywords and are systematically dropped.

**Conclusion**: `constraint_summary` is an item-prohibition keyword extract, not an arc constraint summary. The field name is misleading.

### F-2. Arc 1 is always blank — by design, not by bug

`constraint_db.py:448-450`:
```python
if for_arc <= 1 or not self.arc_states:
    return ""
```

For Arc 1, `generate_constraint_block()` returns `""` because there is no prior arc to constrain against. The `constraint_summary` keyword filter receives an empty string and produces `""`. The runtime warning at `blueprint_constraint_compiler.py:93` ("Arc 1에 constraint_summary 필드 없음") fires every time on all Arc 1 episodes and is structurally unavoidable.

**Evidence**: Both 0324_00_ and canary_0325 show Arc 1 constraint_summary = empty, Arc 2 = present. This matches the code path exactly.

### F-3. Arc 2+ content is narrow and redundant with higher-authority bands

Arc 2 constraint_summary content (both projects):
- Header decoration lines (`█ [V60.28] 절대 금지 - 위반 시 즉시 REJECT █`)
- Emoji-heavy forbidden item entries (`❌ 'SW인베스트먼트 법인 인감' - Arc 1에서 이미 획득함 → 다시 획득 금지!`)
- Self-check checkbox lines (`□ items_acquired에 금지 목록 아이템 없는가?`)

This information is **already covered** by higher-authority mechanisms in the Wave 1 banded prompt:
- **Band 1 IMMUTABLE**: FACT-LOCK packet covers confirmed canonical facts including possessions
- **Band 1 IMMUTABLE**: CAPITAL-LOCK packet covers financial state continuity (investment genre)
- **Band 2 HARD CONSTRAINT**: STOP_LINE prevents future-event consumption
- **Band 3 EXPECTED CONTINUITY**: inherited_state carries equipment, injuries, energy

The constraint_summary items (forbidden acquisitions) are a strict subset of what FACT-LOCK and inherited_state already carry at higher authority.

### F-4. Authority placement is inconsistent across two formatting paths

| Path | Label | Authority |
|------|-------|-----------|
| `compile_to_prompt()` (compiler L250-254) | "🚫 ARC 제약 (MUST NOT DO)" | High (implies mandatory) |
| `_format_constraints()` (ensemble L960-970) | "[Arc 제약 요약]" under ADVISORY band | **Band 4 (lowest)** |

The Wave 1 authority-banded path (`_format_constraints`) is the live path for blueprint generation. The older `compile_to_prompt` path is used for the non-banded prompt variant. In the banded prompt, constraint_summary content reaches the LLM as the lowest-priority advisory.

### F-5. Stage 2 validation pipeline has zero constraint_summary awareness

`stage2_validation_pipeline.py` contains 0 references to `constraint_summary`. There is no validation that:
- constraint_summary was produced at all
- constraint_summary is non-empty when ConstraintDB had forbidden items
- constraint_summary content is semantically correct

This is consistent with the field's secondary status — it was never intended as a validated contract field.

### F-6. The field serves a real but narrow function

Despite its thinness, `constraint_summary` does carry one piece of unique signal: **explicit forbidden-item names with acquisition history**. The FACT-LOCK packet carries settled facts, but does not always enumerate "which items must NOT be re-acquired" with the same explicitness. For investment-genre works where item/asset tracking is critical, this narrow signal has non-zero value.

However, this value is declining as FACT-LOCK and CAPITAL-LOCK mature. Both canary arcs show that the higher-authority packets already carry the same operational constraint.

## 4. Investigation Question Answers

### Q1. How is `constraint_summary` produced today, exactly?

Keyword filter on `ConstraintDB.generate_constraint_block()` output. 3 keywords (`금지`, `MUST NOT`, `절대`), at most 10 matching lines. Source is item/inventory tracking only. Production happens in `stage2_finalizer.py:1055-1058` during arc preparation, not during validation.

### Q2. Is it effectively just "금지문 요약", and does that make it too thin?

**Yes**, it is literally a forbidden-item-line extract. The thinness is real but **not currently harmful** because:
- Higher-authority bands (FACT-LOCK, CAPITAL-LOCK, inherited_state) carry the same operational constraint with more structure
- The field sits in Band 4 ADVISORY, so even if it were richer, it would not override Band 1-3 content

### Q3. Where does Stage 3 consume it, and with what relative authority?

| Consumer | Authority | Notes |
|----------|-----------|-------|
| `blueprint_ensemble.py:_format_constraints` | Band 4 ADVISORY | Primary blueprint gen path |
| `blueprint_constraint_compiler.py:compile_to_prompt` | "MUST NOT DO" label | Non-banded path (secondary) |
| `stage3_orchestrator.py` L260, L378, L388 | Focus text input | SemanticQueryBroker signal |
| `stage4_context_builder.py` L692, L800, L1617 | Tier-0 + focus text | Multi-point Stage 4 consumption |

### Q4. What is the best bounded next wave?

| Option | ROI | Blast Radius | Verdict |
|--------|-----|--------------|---------|
| **A. Keyword robustification** (add more keywords to the filter) | Low | Low | Would capture more lines from the same narrow source — does not address structural thinness |
| **B. Richer summary extraction** (expand source beyond ConstraintDB) | Medium | Medium-High | Requires new extraction logic, potentially from state_constraints, arc summary, or LLM. Risks duplicating semantic_carryover + state_changes_summary |
| **C. Validator/backfill** (add validation that constraint_summary is non-empty) | Low | Low | Would force a fill for Arc 1, but Arc 1 has nothing to constrain against — the emptiness is correct |
| **D. No wave yet** | N/A | None | The field is thin but not harmful, and real constraint delivery is handled by higher-authority bands |

**Recommendation: D (no wave yet).**

### Q5. Would improving `constraint_summary` materially help blueprint clarity?

**No.** The information `constraint_summary` COULD carry (broader strategic constraints) already flows through:
- `semantic_carryover` (relationship rationale, foreshadow anchors)
- `state_changes_summary` (NPC deaths, skill acquisitions, resolved plots)
- `must_focus` (per-episode key events and content)
- `stop_line` (future-episode prohibition)
- `fact_lock_packet` (confirmed canonical facts)
- `capital_continuity_packet` (financial state)

Enriching `constraint_summary` to cover these areas would duplicate existing Band 1-3 content. The marginal clarity gain would be negative (token bloat) or zero.

## 5. Candidate Fixes Ranked by ROI and Blast Radius

| Rank | Fix | ROI | Blast | Status |
|------|-----|-----|-------|--------|
| 1 | **Silence the Arc 1 warning log** — `blueprint_constraint_compiler.py:93` fires on every Arc 1 episode and is structurally unavoidable. Change from `logging.info` to `logging.debug`. | High (noise reduction) | Minimal (1 line) | Candidate for hygiene commit |
| 2 | **Rename field for clarity** — `constraint_summary` → `item_prohibition_summary` or add docstring. Documentation-only. | Low (no runtime effect) | Low | Not worth a wave |
| 3 | **Remove Band 4 duplication** — if FACT-LOCK already covers item prohibitions, constraint_summary in Band 4 is pure redundancy. Could suppress it when FACT-LOCK is present. | Medium (token savings) | Low | Candidate for future banding cleanup wave |
| 4 | **Enrich source** — extract broader arc constraints. | Low-Medium | Medium-High | **Not recommended** — would duplicate 5+ existing channels |

## 6. Confidence Assessment

**Estimated confidence: 96%.**

Evidence is anchored in code reads (8 files), artifact reads (4 arc artifacts, 4 blueprint artifacts), and DB queries (2 projects). The only uncertainty is whether future genre expansions might create scenarios where `constraint_summary` carries unique value not covered by FACT-LOCK — but this is speculative and does not affect the current recommendation.

## 7. 3-Pass Audit Log

### Pass 1: Structure and Scope
- Document type matches request (compact survey, no execution SSOT)
- Scope is explicit: constraint_summary production, delivery, consumption only
- Excluded surfaces are clear (no episode_details, no Stage 3 self-audit, no Stage 4 redesign)
- Section order follows investigation questions

### Pass 2: Evidence and Consistency
- File paths verified against direct reads
- Line numbers verified against grep output
- Arc 1 blank / Arc 2 present pattern confirmed in both 0324_00_ and canary_0325
- Authority band placement confirmed in both formatting paths
- No contradiction between findings and code

### Pass 3: Execution and Readability
- Survey is actionable: clear "no wave yet" recommendation with ranked alternatives
- No overreach beyond surveyed evidence
- Guardrails explicit: does not reopen episode_details floor, Stage 3 self-audit, or Stage 4

---

**Dominant constraint_summary gap: misleading name + item-prohibition-only content (but not harmful — covered by higher-authority bands)**

**Best bounded next wave: none (log-level hygiene fix is the only worthwhile micro-change)**

**Should Codex open an execution SSOT now: no**
