Date: 2026-03-24
Status: final
Document Type: survey report (T7 lane)
Lane: Blueprint Synthesis / Integrated Scenario
Canonical Path: `docs/2026-03-24/opus-residual/t7-blueprint-synthesis-integrated-scenario.md`
Evidence Ledger: `docs/2026-03-24/opus-residual/t7-blueprint-synthesis-integrated-scenario-evidence.md`
Source Survey Docs:
- `docs/2026-03-24/stage2-stage3-residual-leakage-resurvey-10terminal-master-order.md`
- `docs/2026-03-24/stage2-stage3-episode-boundary-expanded-survey-report.md`
- `docs/2026-03-24/stage2-stage3-episode-boundary-wave1-execution-ssot.md`
- `docs/2026-03-24/stage2-stage3-episode-boundary-wave2-survey-report.md`
Commit State:
- Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Baseline Dirty Summary: `dirty workspace; Wave 1 closed, Wave 2 survey finalized, fresh live-run evidence updated`

---

# T7: Blueprint Synthesis / Integrated Scenario

## 1. Executive Summary

The blueprint ensemble and three-phase blueprint runtime do NOT independently re-inflate arc-global narrative material. They are transparent passthroughs that faithfully format and relay upstream inputs. The `integrated_scenario` field is an LLM output, not an input — the blueprint synthesis layer does not generate or manipulate arc-global content.

However, the synthesis layer is the **final formatting stage** through which one confirmed residual leakage vector passes: `semantic_carryover`. This field is arc-global, not episode-filtered, and contains concrete arc-end-state descriptions (20B capital, corporate establishment, family escape) that reach the LLM prompt as `[Arc Semantic Carryover]` via `_format_constraints()`. When combined with sparse `must_focus` (2 items for ep1), this creates the signal imbalance that allows the LLM to absorb future-episode content into the current blueprint.

**Classification: secondary amplifier / passthrough for upstream residual leakage**

The synthesis layer does not originate the problem but does not block it either.

---

## 2. Included Coverage / Exclusions

### Included
- `modules/domain/agents/blueprint_ensemble.py` — full prompt assembly path, `_generate_single()`, `_build_blueprint_prompt_bundle()`, `_resolve_blueprint_arc_focus()`, `_format_constraints()`, `_format_prev_info_expanded()`
- `modules/domain/agents/three_phase_blueprint_runtime.py` — retry loop, constraint resolution, generation dispatch
- `config/prompts/ensemble.yaml` — BLUEPRINT_GENERATION_PROMPT template
- `modules/core/tactical_utils.py` — `extract_episode_tactical()` fallback behavior
- Blueprint artifact structure from `projects/00_001/logs/artifacts/stage3/ep_0001/attempt_09/`
- Arc payload from `projects/00_001/logs/artifacts/stage2/arc_001/attempt_01/final_arc__balanced.json`

### Excluded
- Stage 2 arc generation (T2/T3 lanes)
- Constraint compiler internals (T5 lane)
- Stage 3 prompt injection (T6 lane)
- Stage 4 contradiction detection (T8 lane)
- LLM I/O trace analysis (T9 lane)

---

## 3. Key Evidence

### E1. Prompt Assembly Is Text-Only

`_generate_single()` at `blueprint_ensemble.py:558-572` receives only pre-formatted strings: `arc_focus`, `constraints_str`, `prev_info`, `feedback`, `hud_context`, plus strategy/protagonist/genre parameters. The `arc_data` dict is NOT accessible inside the prompt generation path. The LLM cannot directly access raw arc payload fields.

### E2. `semantic_carryover` Passes Through Unfiltered

The constraint compiler normalizes but does NOT episode-filter `semantic_carryover` (`blueprint_constraint_compiler.py:97, 654-699`). The blueprint ensemble's `_format_constraints()` (`blueprint_ensemble.py:963-986`) formats it as `[Arc Semantic Carryover]` and injects it into the LLM prompt.

For 00_001, this section contains:
- `continuity_checkpoints`: "20억 자본금 확보 완료", "법인 설립 완료" (ep3/ep4 end state)
- `growth_justification`: "초기 투자 자본 20억 원 확보" (ep3 milestone)
- `foreshadow_anchors`: "유가 상승세, 이란 핵 문제 재점화 보도" (ep4 event)

### E3. ep1 Blueprint Absorbed semantic_carryover Content

The ep1 blueprint (attempt 09) `integrated_scenario` and `ending_state` contain all items from the `semantic_carryover.continuity_checkpoints`:
- "20억 확보" → scenes 3-4
- "법인 설립 완료" → scene 4
- "이란 핵 문제" → scene 5
- `ending_state.protagonist_status`: "자본금 20억 확보 및 법인 설립을 완료"

Direct content match between `semantic_carryover` and overconsummed blueprint output.

### E4. Wave 1 Fixes Are Verified in Synthesis Layer

Treatment block: now filtered to `title/emotional_beat/foreshadow/content.context` only (`stage3_orchestrator.py:1127-1140`). Verified.

State changes: filtered upstream by constraint compiler's `_summarize_state_changes()` Wave 1 patch. Not re-inflated by synthesis layer. Verified.

Stop line: expanded to cover all future episodes upstream. Passed through correctly by `_format_constraints()`. Verified.

### E5. Latent Fallback Risk in `_resolve_blueprint_arc_focus()`

`blueprint_ensemble.py:215-238` calls `extract_episode_tactical()` with default `fallback_full=True` as a fallback when `must_focus.content` is empty. If both `must_focus.content` AND regex extraction fail, the entire multi-episode `tactical_doc` would be returned as `arc_focus`. Mitigated by `must_focus.content` being almost always populated by the constraint compiler. Not observed in 00_001 evidence but is a latent code-level risk.

---

## 4. Findings Ranked

| Rank | Finding | Classification | Anchor |
|------|---------|---------------|--------|
| F1 | `semantic_carryover` passes through synthesis layer unfiltered, containing arc-end-state material that matches ep1 overconsumption | **likely residual leakage (passthrough)** | `blueprint_ensemble.py:963-986`, `final_arc__balanced.json:155-183` |
| F2 | Latent `fallback_full=True` in `_resolve_blueprint_arc_focus()` could expose full `tactical_doc` if `must_focus.content` is empty | **follow-up only** | `blueprint_ensemble.py:218` vs `blueprint_constraint_compiler.py:236` |
| F3 | `_format_prev_info_expanded()` propagates overconsummed blueprints to later episodes | **secondary amplifier (cascade propagation)** | `blueprint_ensemble.py:1054-1101` |
| F4 | Treatment block injection is correctly filtered by Wave 1 | **noise / not the culprit** | `stage3_orchestrator.py:1127-1140` |
| F5 | `_build_hud_context()`, `_build_reader_feedback_context()` are episode-scoped | **noise / not the culprit** | `blueprint_ensemble.py:990-992, 778-840` |
| F6 | `_generate_single()` and `_build_blueprint_prompt_bundle()` have no direct arc_data access | **noise / not the culprit** | `blueprint_ensemble.py:558-572, 637-652` |

---

## 5. Cleared Non-Culprits

- **Blueprint ensemble prompt template** (`ensemble.yaml` BLUEPRINT_GENERATION_PROMPT): Template slots are filled by pre-formatted text. The template itself does not add arc-global content. Cleared.
- **`_format_prev_info_expanded()`**: For ep1, returns "(첫 에피소드 - 이전 화 없음)". For later episodes, includes previous blueprint `integrated_scenario` which is legitimate past-state continuity data. Cleared as independent cause (cascade propagation only).
- **`_build_hud_context()`**: Delegates to `modules.core.hud_utils.build_hud_context()` with episode-scoped variant. Cleared.
- **`_build_reader_feedback_context()`**: Reads from DB with `before_ep=ep_num` lookback. Cleared.
- **`three_phase_blueprint_runtime.py` retry loop**: Manages retry/patch/validation flow. Does not inject new content. Passes `arc_data` and `constraint_block` to ensemble but does not inflate them. Cleared.
- **`inherited_state`**: For ep1, reads `arc_start_state.equipment` (correctly ["예금통장", "신탁 펀드 증서", "승마 스폰서십 계약서"]), not arc-end-state equipment. Cleared.

---

## 6. Residual Culprit Candidate

**`semantic_carryover` — arc-global unfiltered field passing through the blueprint synthesis layer**

Mechanism:
1. Stage 2 generates `semantic_carryover` with arc-end-state descriptions (20B capital, corporate establishment, WTI investment)
2. Constraint compiler normalizes but does NOT episode-filter (`_normalize_semantic_carryover` at `blueprint_constraint_compiler.py:654-699`)
3. Blueprint ensemble formats as `[Arc Semantic Carryover]` in `_format_constraints()` (`blueprint_ensemble.py:963-986`)
4. LLM receives sparse `must_focus` (2 items for ep1) alongside rich `semantic_carryover` describing the full arc outcome
5. LLM absorbs `semantic_carryover` material into ep1 blueprint `integrated_scenario`, producing overconsumption

Important caveat: this finding is about a vector that **passes through** the synthesis layer. The **origin** is in the constraint compiler's lack of episode filtering on `semantic_carryover`, not in the blueprint ensemble itself. The fix belongs upstream in the constraint compiler or in `_normalize_semantic_carryover()`.

---

## 7. Next-Scope Recommendation

**Bounded fix: episode-filter `semantic_carryover` in `_normalize_semantic_carryover()` or add an episode-aware wrapper in `_format_constraints()`**

Option A (preferred, upstream): Add episode filtering to `_normalize_semantic_carryover()` or a new `_filter_semantic_carryover_by_episode()` in the constraint compiler. Filter `continuity_checkpoints` and `growth_justification` to only include milestones achievable by `current_ep`. Keep `foreshadow_anchors` and `relationship_rationale` as advisory only.

Option B (downstream, in synthesis layer): In `_format_constraints()`, relabel `semantic_carryover` as advisory-only with a strong structural guard, similar to the Wave 1 treatment block header. This would not remove the content but could reduce LLM uptake.

Option C (combined): Filter concrete milestones upstream + add advisory label downstream.

Secondary fix: Change `fallback_full=True` to `fallback_full=False` in `_resolve_blueprint_arc_focus()` at `blueprint_ensemble.py:218` to close the latent full-tactical-doc fallback risk.

Scope: ~30 lines in `blueprint_constraint_compiler.py` + optional ~5 lines in `blueprint_ensemble.py`. No broad refactor required.

---

## 8. Confidence and Limits

- **Confidence: 93%**
- **Basis:**
  - Code-level tracing is complete for the entire blueprint synthesis prompt assembly path
  - Direct content match between `semantic_carryover` fields and ep1 overconsumption output
  - Wave 1 fixes verified as correctly implemented in the synthesis layer
  - All non-culprit surfaces cleared with evidence
- **Limits:**
  - Did not trace the full LLM I/O for ep1 attempt 09 to confirm `semantic_carryover` text literally appears in the prompt (deferred to T9 lane)
  - Cannot quantify the relative weight of `semantic_carryover` vs `episode_details` sparseness as causes of overconsumption without a controlled experiment
  - The `_collect_stage3_smart_retrieval_bundle()` internal content (vector/DB retrieval) was not fully audited — could contain additional arc-global material via work_focus or slot summaries

---

## Mandatory Conclusions

- **Can this seam alone explain ep1 overconsumption: no** — `semantic_carryover` is a contributing factor (likely residual leakage passthrough) but operates in conjunction with sparse `episode_details` and potentially other upstream fields. The synthesis layer itself does not originate the leakage.
- **Can this seam explain ep3/ep4 continuity-firewall replay: partially** — only as downstream cascade propagation. If ep1 overconsumes due to `semantic_carryover` (plus sparse positive guidance), the overconsummed ep1 blueprint propagates via `_format_prev_info_expanded()` to later episodes. But the synthesis layer is not the independent cause of the ep3/ep4 replays.
- **Can this seam be fixed in a bounded next wave: yes** — episode-filtering `semantic_carryover` upstream (~30 lines) plus closing the `fallback_full` latent risk (~5 lines) is a bounded, testable fix.

---

## 3-Pass Audit Record

- Pass 1
  - confirmed this document is a survey report, not an execution SSOT
  - confirmed scope covers all T7 lane questions from the master order
  - confirmed included/excluded surfaces are explicit
- Pass 2
  - confirmed all findings are anchored to concrete file:line references
  - confirmed evidence ledger E1-E9 supports the findings
  - confirmed no overclaiming: synthesis layer is classified as passthrough, not originator
  - confirmed semantic_carryover content match is concrete (00_001 arc JSON vs ep1 blueprint JSON)
- Pass 3
  - confirmed next-scope recommendation is bounded and actionable
  - confirmed mandatory conclusions are explicit
  - confirmed Wave 1 fix verification is included
  - confirmed confidence basis and limits are stated
