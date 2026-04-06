# Terminal 3: Continuity Pins, Inventory Gaps, and Carryover Planning Residue

Date: 2026-04-06
Status: final
Mode: read-only bounded survey
Scope: latest Stage3 run, `projects/00_골든`

---

## Findings First

### Verdict: All flagged items are conservative advisory warnings, not true continuity leaks. No Stage3 blocker.

| Warning Family | Episodes | Type | True Leak? | Blocks S4? |
|---|---|---|---|---|
| TF-49 `몸뿐` | ep2, ep3, ep4 | **semantic false positive** | No | No |
| TF-49 `법인 통장/사업자등록증` | ep5, ep6 | **correctly identified planning-time gap** | No (blueprint describes acquisition) | No |
| PinGuard unresolved | ep3, ep5 | **data-absent false trigger** | No | No |

---

## Q1: Why does TF-49 inventory gaps persist after repeated PASS outcomes?

### Root Cause

`_detect_inventory_gaps` (`stage3_orchestrator.py:2469-2533`) compares `protagonist_state.equipment` against `WorldState.get_owned_items()` (`world_state.py:1319`). During this fresh Stage 3 run, WorldState was newly initialized (tttt.txt: `🌍 [V68] WorldStateManager 초기화 (신규)`) and contains zero `active_items`. The fallback `constraint_db.get_current_inventory()` is also empty for a virgin project.

### Mechanism

```
owned = world_state.get_owned_items()   → empty set (fresh run)
referenced = blueprint.protagonist_state.equipment  → ["몸뿐"] or ["SW인베스트먼트 법인 통장", ...]
gap = referenced - owned                → everything referenced is flagged
```

### Item-by-item analysis

**"몸뿐" (ep2-ep4)**: Literal meaning is "only the body" — a semantic sentinel for "protagonist has no equipment." The detector at `stage3_orchestrator.py:2499-2505` reads `protagonist_state.equipment` literally without sentinel filtering. Since "몸뿐" is never an actual item in `active_items`, it is always flagged. This is a **pure false positive** that will recur in every fresh-run blueprint using this sentinel.

Evidence:
- ep1 artifact: `protagonist_state.equipment = ["몸뿐"]` (not flagged — `working_ep > 1` guard at line 2011 skips ep1)
- ep2 artifact: `protagonist_state.equipment = ["몸뿐"]` → gap 1
- ep3 artifact: `protagonist_state.equipment = ["몸뿐"]` → gap 1
- ep4 artifact: `protagonist_state.equipment = ["몸뿐"]` → gap 1

**"SW인베스트먼트 법인 통장, SW인베스트먼트 사업자등록증" (ep5-ep6)**: Legitimate inventory items. The ep5 blueprint describes the protagonist establishing a company and receiving these documents; the ep6 blueprint shows the protagonist carrying them to a securities firm. The gap is correctly detected — the items are referenced before the WorldState records ownership — but the blueprint itself already plans the acquisition path.

Evidence:
- ep5 artifact: `protagonist_state.equipment = ["SW인베스트먼트 법인 통장", "SW인베스트먼트 사업자등록증"]` → gap 2
- ep6 artifact: same equipment, same gap count → gap 2 (unchanged because WorldState never updates during Stage 3)
- The gap count grew from 1 to 2 at ep5 because real items replaced the sentinel

### Why PASS despite gaps

TF-49 gaps are **advisory-only**. They:
- Do NOT modify the Director score (all scores in `decisions.jsonl` show no penalty)
- Do NOT trigger REJECT
- Are embedded in the blueprint via `blueprint["_inventory_gaps"]` for downstream consumption
- `chief_writer_context_packets.py:201-216` surfaces the gap to ChiefWriter with guidance: *"Add a natural acquisition beat before the item is used. Using it without setup is reject-worthy."*

This is working as designed: Stage 3 flags the gap, Stage 4 ChiefWriter resolves it narratively.

---

## Q2: Why are PinGuard warnings unresolved in ep3 and ep5?

### Root Cause

`apply_continuity_pins` (`continuity_pin_guard.py:133-207`) is designed for Stage 3/4 handoff verification using `previous_published_text` (Stage 4 manuscripts). During a fresh Stage 3 run, **no manuscripts exist**.

### Mechanism

```python
prev_row = db.get_manuscript(working_ep - 1)   → None (no Stage 4 ever ran)
prev_published_text = ""                        → empty
source_text = "" or arc_tactical_text           → falls back to arc tactical text only
```

The function then extracts quoted tokens from `source_text` and `blueprint_text`:

```python
source_quoted = _extract_quoted_tokens(source_text)      # from arc tactical
blueprint_quoted = _extract_quoted_tokens(blueprint_text) # from blueprint
```

The `unresolved` path at line 166-173 fires when:
1. Exactly 1 quoted token exists in the arc tactical text
2. That token does NOT appear in the blueprint's quoted tokens
3. Multiple mismatched tokens exist in the blueprint

### Why only ep3 and ep5?

The triggering condition is narrowly constrained (`len(source_quoted) == 1`). For ep1, ep2, ep4, ep6, the arc tactical excerpts either have zero or multiple quoted tokens, which skip the unresolved branch entirely. Only ep3 and ep5's specific arc tactical sections produce exactly one source token that mismatches the blueprint.

### Downstream impact

PinGuard WARN:
- Is advisory-only (`ui.log` + `audit_event`, no score change)
- Does NOT modify the blueprint's PASS verdict
- Embeds findings in `blueprint["_continuity_pin_unresolved"]` for operator awareness
- `decisions.jsonl` shows no penalty on ep3 (score 95) or ep5 (score 84) from PinGuard

---

## Q3: Are the flagged items true continuity leaks or conservative carryover checks?

**Conservative carryover checks in all cases.**

### Evidence summary

| Item | Diagnosis | Rationale |
|---|---|---|
| "몸뿐" inventory gap | False positive | Sentinel meaning "no items" treated as literal item name. Never exists in `active_items` by definition. |
| "법인 통장/사업자등록증" gap | Correct advisory | Blueprint describes acquisition path. Gap alerts ChiefWriter to add natural acquisition beats in Stage 4. |
| PinGuard ep3/ep5 unresolved | Data-absent false trigger | Pin system designed for manuscript handoff; no manuscripts exist during fresh Stage 3. Arc tactical fallback is weaker signal. |

### Will they worsen in later episodes?

**TF-49 "몸뿐"**: Will disappear once the protagonist acquires real items (ep5+). Already resolved naturally in the current run — ep5 replaces "몸뿐" with real equipment.

**TF-49 real item gaps**: Will likely grow as the story introduces more equipment (weapons, documents, access keys). However, each gap is advisory and correctly handled downstream. The count going from 1→2 between ep4 and ep5 is a natural consequence of plot progression, not a system regression.

**PinGuard unresolved**: Will persist at a similar low frequency (~2 of 6 episodes). Once Stage 4 produces manuscripts, the primary `previous_published_text` source becomes available, and the pin system will operate at its designed accuracy level. The current false triggers are a **fresh-run-only artifact**.

---

## Q4: Is the likely owner in context building, pin application, or the blueprint plan itself?

### Narrowest owner file set

| Priority | Owner File | Responsibility | What it emits |
|---|---|---|---|
| **Primary** | `modules/core/stage3_orchestrator.py` | Calls both `_detect_inventory_gaps` and `apply_continuity_pins`; decides when to annotate, log, and persist | All TF-49 and PinGuard warnings |
| **Secondary** | `modules/core/continuity_pin_guard.py` | Pin detection logic; quoted-token matching and time-surface comparison | PinGuard `unresolved` entries |
| **Downstream** | `modules/domain/agents/chief_writer_context_packets.py` | Surfaces `_inventory_gaps` to ChiefWriter prompt; not a source of warnings | TF-49 advisory section in writer prompt |

### If a fix wave were needed (hypothetical)

**Single-file fix for "몸뿐" false positive**:
- `stage3_orchestrator.py:_detect_inventory_gaps` — add sentinel exclusion (e.g., skip items matching `["몸뿐", "없음", "해당없음"]`) at line 2503-2504
- Scope: ~5 lines

**Single-file fix for PinGuard fresh-run noise**:
- `stage3_orchestrator.py:_annotate_stage3_success_blueprint` — skip PinGuard call when `prev_published_text` is empty (line 2041), or
- `continuity_pin_guard.py:apply_continuity_pins` — return early when `previous_published_text` is empty and no strong arc tactical signal exists
- Scope: ~3 lines

Both fixes are bounded and non-breaking. Neither is a Stage3 blocker for S4 progression.

---

## Authoritative Evidence Trail

| Source | File | Evidence |
|---|---|---|
| decisions.jsonl | `projects/00_골든/logs/session/decisions.jsonl` | All 6 ep PASS, scores 84-95, no penalty from TF-49 or PinGuard |
| ui_events.jsonl seq 160-204 | `projects/00_골든/logs/session/ui_events.jsonl` | TF-49 lines at seq 160,170,181,192,204; PinGuard lines at seq 171,193 |
| ep3 artifact | `logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__emotion_focused.json` | equipment=["몸뿐"], python_warnings has fidelity MINOR + scenario_density MINOR |
| ep5 artifact | `logs/artifacts/stage3/ep_0005/attempt_02/final_blueprint__action_focused.json` | equipment=["SW인베스트먼트 법인 통장","SW인베스트먼트 사업자등록증"], prevalidation_issue_count=6 |
| ep6 artifact | `logs/artifacts/stage3/ep_0006/attempt_02/final_blueprint__action_focused.json` | same equipment as ep5, fidelity MINOR (1 NPC 미언급) |
| TF-49 detector | `modules/core/stage3_orchestrator.py:2469-2533` | `protagonist_state.equipment` compared against `world_state.get_owned_items()` |
| PinGuard | `modules/core/continuity_pin_guard.py:133-207` | Quoted-token matching, time-surface matching, opening-action-continuity |
| WorldState | `modules/core/world_state.py:1319-1322` | `get_owned_items()` reads `self._state["active_items"]`, status=="보유" |
| ChiefWriter context | `modules/domain/agents/chief_writer_context_packets.py:200-216` | TF-49 gap advisory injected into writer prompt |
| Enrichment call | `modules/core/stage3_orchestrator.py:1989-2060` | `_annotate_stage3_success_blueprint`: TF-49 at L2011, PinGuard at L2041 |
| Persist call | `modules/core/stage3_orchestrator.py:2083` | `save_episode_blueprint(working_ep, blueprint)` — enriched blueprint with `_inventory_gaps` and `_continuity_pin_unresolved` fields |
| tttt.txt | `tttt.txt` | `WorldStateManager 초기화 (신규)`, `팩트 원장 초기화 (신규)` confirms fresh state |

---

## Summary

1. **TF-49 inventory gaps persist because WorldState is empty during fresh Stage 3 runs.** The "몸뿐" gap is a semantic false positive; the "법인 통장/사업자등록증" gap is a correct but advisory-only planning awareness signal.

2. **PinGuard unresolved pins fire because the system depends on Stage 4 manuscripts that don't yet exist.** The arc-tactical-only fallback is a weaker signal that triggers false positives in 2 of 6 episodes.

3. **All flagged items are conservative carryover checks, not true continuity leaks.** None affect PASS/REJECT verdicts, scores, or downstream Stage 4 readiness.

4. **The narrowest owner is `stage3_orchestrator.py`.** If fixes were needed, a ~5-line sentinel exclusion for "몸뿐" and a ~3-line early-return for PinGuard-without-manuscripts would eliminate all current noise. Neither fix is a prerequisite for S4 progression.

---

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-06 output
