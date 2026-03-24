Date: 2026-03-24
Status: final
Document Type: lane survey report (T4 of 10)
Canonical Path: `docs/2026-03-24/opus-residual/t4-current-episode-extraction.md`
Temp Mirror Path: none (lane survey report, not execution SSOT)
Master Order: `docs/2026-03-24/stage2-stage3-residual-leakage-resurvey-10terminal-master-order.md`
Source Evidence:
- `modules/core/tactical_utils.py` (production code)
- `modules/domain/agents/blueprint_constraint_compiler.py:230-268` (`_extract_episode_focus`)
- `modules/domain/agents/blueprint_ensemble.py:215-238` (`_resolve_blueprint_arc_focus`)
- `modules/core/stage3_orchestrator.py:1950-1954` (continuity-pin extraction)
- `modules/domain/agents/three_phase_blueprint_generator.py:184-194` (patch-mode extraction)
- `modules/core/prompt_builder.py:691` (Stage 4 context extraction)
- `modules/domain/agents/director_ensemble.py:1529-1533` (Director verdict extraction)
- `modules/core/stage4_context_builder.py:1788-1793` (Stage 4 context builder extraction)
- `modules/core/stage4_orchestrator.py:746-750` (Stage 4 orchestrator extraction)
- `modules/domain/agents/continuity_arc.py:583,990-1001` (ContinuityArc extraction)
- `modules/domain/agents/continuity_inspector.py:392` (ContinuityInspector extraction)
- `modules/core/tree_of_thoughts.py:389-392` (ToT extraction)
- `projects/00_001/logs/artifacts/stage2/arc_001/attempt_01/final_arc__balanced.json` (live arc data)
- `projects/00_001/logs/artifacts/stage3/ep_0001/attempt_09/final_blueprint__emotion_focused.json` (live ep1 blueprint)
Commit State:
- Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Baseline Dirty Summary: `dirty workspace; Wave 1 closed, Wave 2 survey finalized, fresh live-run evidence updated`

---

# T4: Current-Episode Extraction — Lane Survey Report

## 1. Executive Summary

The current-episode extraction layer (`tactical_utils.py` + `_extract_episode_focus`) is **not the residual culprit**. It correctly isolates current-episode content for `must_focus` and the primary `arc_focus` derivation path. The extraction does not leak future-episode material into early-episode blueprint inputs.

**Classification: `noise / not the culprit`**

The extraction layer is one of the positive authority surfaces that Wave 1 correctly preserved. The ep1 overconsumption in `00_001` is not caused by a failure in episode-tactical extraction; it is caused by louder, arc-global inputs that bypass this extraction entirely (treatment block, state_changes, semantic_carryover — other lanes' territory).

One latent design concern is flagged: 7 of 12 production callers use `fallback_full=True` (the default), which would return the full arc-wide `tactical_doc` if both `episode_details` and regex extraction fail simultaneously. This did not trigger in `00_001` but represents a dormant leakage surface for future arcs with poorly structured tactical docs.

---

## 2. Included Coverage / Exclusions

### Included

- `modules/core/tactical_utils.py`: shared extraction utility (`extract_episode_tactical`, `_EPISODE_HEADER_PATTERNS`)
- `modules/domain/agents/blueprint_constraint_compiler.py:230-268`: `_extract_episode_focus` (produces `must_focus`)
- `modules/domain/agents/blueprint_ensemble.py:215-238`: `_resolve_blueprint_arc_focus` (assembles `arc_focus` for blueprint LLM prompt)
- All 12 production callers of `extract_episode_tactical` across the pipeline
- `00_001` arc `episode_details` field and `tactical_doc` field structure
- `00_001` ep1 blueprint `integrated_scenario` and `ending_state` as downstream evidence

### Exclusions

- Treatment block injection (T6 scope)
- `_summarize_state_changes` Wave 1 filter effectiveness (T5/T2 scope)
- `semantic_carryover` and `foreshadow_anchors` (T2/T5 scope)
- Blueprint synthesis / `integrated_scenario` generation logic (T7 scope)
- Stage 4 contradiction detection (T8 scope)
- Stage 2 density/allocation validation gaps (T3 scope)

---

## 3. Key Evidence

### E1. `extract_episode_tactical()` filters correctly by `ep_num`

**File: `modules/core/tactical_utils.py:31-73`**

The function has a 3-tier priority:

| Priority | Source | Filter Mechanism | Result for ep1 in 00_001 |
|----------|--------|-----------------|--------------------------|
| 1 | `episode_details` | `item.get("ep_num") == ep_num` (exact match) | Returns 2 items: "2024년 고독사 후..." and "18년 치 거시경제 데이터..." |
| 2 | Regex on `tactical_doc` | Pattern anchors on `제 {ep} 화` header, captures until next header | Would return ep1 section (회귀 + 편두통 극복) |
| 3 | Fallback | If `fallback_full=True`, returns full `tactical_doc` | Would return all 4 episodes |

For `00_001`, Priority 1 succeeds because `episode_details` has all 4 episodes with `ep_num` fields. The extraction returns only ep1's 2 detail items.

### E2. `_extract_episode_focus()` uses `fallback_full=False`

**File: `modules/domain/agents/blueprint_constraint_compiler.py:232-236`**

```python
content = extract_episode_tactical(
    arc_data.get("tactical_doc", ""),
    ep_num,
    episode_details=arc_data.get("episode_details"),
    fallback_full=False,  # <-- SAFE: no full-doc fallback
)
```

This is the primary extraction path for `must_focus`. With `fallback_full=False`, if both `episode_details` and regex fail, it returns an empty string rather than the full `tactical_doc`. This prevents arc-wide leakage.

### E3. `must_focus` output for ep1 is correctly scoped

Given `00_001` data, `must_focus.content` for ep1 would be:
```
- 2024년 고독사 후 2006년 본가 침실에서 눈을 뜸
- 18년 치 거시경제 데이터 복기 및 두통 극복
```

This matches the arc's `episode_details[0]` exactly. No ep2/ep3/ep4 content is present.

### E4. `_resolve_blueprint_arc_focus()` enriches correctly but has a fallback gap

**File: `modules/domain/agents/blueprint_ensemble.py:215-238`**

This function:
1. Gets `must_focus.content` from the constraint_block (ep-scoped) — **primary path**
2. If empty, falls back to `extract_episode_tactical(...)` with **default `fallback_full=True`** — fallback path
3. Prepends `episode_details[ep_num]` items as supplementary context — correctly filtered by `ep_num`

For `00_001` ep1, step 1 succeeds (must_focus.content is populated). The fallback in step 2 is never triggered. Step 3 correctly adds only ep1 details.

### E5. Full caller inventory with `fallback_full` status

| # | Caller | File:Line | `fallback_full` | Truncation | Stage | Classification |
|---|--------|-----------|-----------------|------------|-------|----------------|
| 1 | `_extract_episode_focus` | bcc:232 | **False** | 500c (prompt) | S3 constraint | **SAFE** |
| 2 | `_resolve_blueprint_arc_focus` | bp_ens:218 | True (default) | 15000c | S3 blueprint gen | Fallback-only |
| 3 | `apply_continuity_pins` | s3o:1950 | True (default) | none | S3 post-process | Fallback-only |
| 4 | Patch-mode extraction | tpbg:186 | True (default) | :3000 | S3 patch mode | Truncated |
| 5 | Stage 4 context summary | pb:691 | True (default) | :1800 | S4 context | Truncated |
| 6 | Director verdict | de:1529 | True (default) | :6000 | S4 Director | Truncated |
| 7 | ContinuityInspector | ci:392 | **False** | none | Validation | **SAFE** |
| 8 | ContinuityArc | ca:583 | **False** | none | ContinuityArc | **SAFE** |
| 9 | ContinuityArc first/last | ca:990-1001 | **False** | none | ContinuityArc | **SAFE** |
| 10 | Tree of Thoughts | tot:389 | True (default) | context-dependent | S3 ToT | Fallback-only |
| 11 | Stage 4 context builder | s4cb:1788 | **False** | none | S4 context | **SAFE** |
| 12 | Stage 4 orchestrator | s4o:746 | True (default) | :3000 | S4 prompt | Truncated |

- **5 of 12 callers use `fallback_full=False`**: These are definitively safe.
- **7 of 12 callers use `fallback_full=True`** (default): These would receive the full arc-wide `tactical_doc` if extraction fails. However, in all 7 cases, either (a) the `episode_details` path succeeds first, (b) the regex path succeeds first, or (c) the result is truncated to a bounded prefix.

### E6. `00_001` tactical_doc has clear episode headers

The `tactical_doc` in `final_arc__balanced.json:363` is well-structured with `제 N화:` headers and `[시작 상태]`/`[종료 상태]` markers. All 6 regex patterns in `_EPISODE_HEADER_PATTERNS` would match these headers correctly. The regex fallback would also correctly extract only ep1's section.

### E7. ep1 blueprint overconsumption is NOT caused by the extraction layer

The ep1 blueprint (attempt_09) ending_state says "자본금 20억 확보 및 법인 설립을 완료하고 첫 투자를 목전에 둔 상태" — this is ep4's final state compressed into ep1.

But `must_focus` for ep1 only says "2024년 고독사 후... / 18년 치 거시경제 데이터 복기". The overconsumption comes from other channels that the extraction layer does not control:
- `state_changes` (pre-Wave-1: unfiltered arc-wide items)
- Treatment block (full arc narrative)
- `semantic_carryover` (arc-wide foreshadow anchors, continuity checkpoints)

---

## 4. Findings Ranked

| # | Finding | Classification | Confidence |
|---|---------|---------------|------------|
| F1 | `extract_episode_tactical()` correctly filters by `ep_num` via episode_details and regex | `noise / not the culprit` | 98% |
| F2 | `_extract_episode_focus()` uses `fallback_full=False`, preventing full-doc leakage | `noise / not the culprit` | 98% |
| F3 | `must_focus` output for ep1 is correctly scoped to ep1's 2 detail items | `noise / not the culprit` | 97% |
| F4 | 7/12 callers use `fallback_full=True` default — latent leakage surface if extraction fails | `follow-up only` | 93% |
| F5 | `_resolve_blueprint_arc_focus()` enrichment prepends `episode_details[ep_num]` correctly | `noise / not the culprit` | 97% |
| F6 | ep1 overconsumption is caused by inputs bypassing extraction, not by extraction itself | `noise / not the culprit` (confirms other lanes) | 96% |

---

## 5. Cleared Non-Culprits

| Surface | Why Cleared | Evidence |
|---------|-------------|----------|
| `extract_episode_tactical()` | Correctly filters by `ep_num` in both episode_details and regex paths | Code audit of tactical_utils.py:31-73; 00_001 data match |
| `_extract_episode_focus()` | Uses `fallback_full=False`; produces only current-ep content | bcc:232-236 |
| `must_focus` field | Contains only ep1's 2 detail items for 00_001 ep1 | Derivation trace from episode_details[0] through extraction |
| `_resolve_blueprint_arc_focus()` | Primary path uses constraint_block.must_focus.content (ep-scoped); enrichment filters by ep_num | bp_ens:215-238 |
| `_EPISODE_HEADER_PATTERNS` | 6 regex patterns correctly anchor on `제 {ep} 화` headers | Pattern inspection + 00_001 tactical_doc structure |
| `episode_details` ep_num filter | `item.get("ep_num") == ep_num` is an exact integer match | tactical_utils.py:52 |

---

## 6. Residual Culprit Candidate

**This lane does not contain a residual culprit.**

The extraction layer is a positive authority surface that correctly isolates current-episode content. The ep1 overconsumption is caused by louder inputs that bypass this extraction entirely and enter the blueprint prompt through separate channels. The extraction layer's correctly scoped `must_focus` is simply overwhelmed by the volume of arc-global material coming through `state_changes`, treatment block, and `semantic_carryover`.

### Latent Design Concern (follow-up only)

7 of 12 callers use `fallback_full=True` (the default parameter value). If a future arc has:
- A `tactical_doc` without recognizable episode headers (no `제 N화`, no `Beat N:`, etc.)
- AND empty or malformed `episode_details`

Then these callers would receive the full arc-wide `tactical_doc` as if it were current-episode content. This did not trigger in `00_001` (where both paths succeed) but is a dormant leakage surface.

**Recommended follow-up**: Change the default of `fallback_full` from `True` to `False` in `extract_episode_tactical()` function signature, or add explicit `fallback_full=False` to the 7 callers that currently rely on the default. This is a defensive hardening measure, not a fix for the current failure family.

---

## 7. Next-Scope Recommendation

**No action needed for this lane in the current wave.**

The extraction layer is clean. The residual culprit lies in other lanes (likely T2/T5/T6/T7 territory — wherever arc-global material enters the blueprint prompt without passing through this extraction filter).

**Optional defensive hardening** (Wave 3 or later):
- Flip `fallback_full` default to `False` in `tactical_utils.py:36`
- This would affect 7 callers; each should be checked for downstream impact
- Estimated scope: ~30 minutes, low risk, bounded to the extraction utility

---

## 8. Confidence And Limits

- **Confidence: 96%**
- **Basis:**
  - Code audit covers the complete extraction function, all 12 production callers, and the downstream derivation of `must_focus` and `arc_focus`
  - Fresh live-run evidence confirms that `episode_details` and `tactical_doc` structures support successful extraction
  - The ep1 blueprint's overconsumption content does not trace back to the extraction layer's output
- **Limits:**
  - Did not trace the full LLM prompt assembly end-to-end (T6/T7 scope)
  - Did not inspect `llm_io.jsonl` to verify what `must_focus` text actually reached the model (T9 scope)
  - The `fallback_full=True` default concern is inferred from code structure, not from a live failure case
- **Uncertainty source:** 4% uncertainty from inability to confirm via live LLM I/O traces that `must_focus` was not silently overridden or discarded by a downstream prompt assembly step

### Mandatory Conclusions

- **Can this seam alone explain ep1 overconsumption: NO**
- **Can this seam explain ep3/ep4 continuity-firewall replay: NO**
- **Can this seam be fixed in a bounded next wave: N/A** (not broken; optional defensive hardening is ~30 min)

---

## 9. 3-Pass Audit Record

- Pass 1
  - confirmed this document is a lane survey report, not an execution SSOT
  - confirmed scope matches T4 lane definition from the master order
  - confirmed all 12 production callers are inventoried with `fallback_full` status
  - confirmed report sections match the required output contract
- Pass 2
  - confirmed evidence anchors are concrete (file:line for code, field names for data)
  - confirmed `must_focus` derivation trace is consistent with live 00_001 data
  - confirmed the `fallback_full=True` concern is correctly scoped as `follow-up only`
  - confirmed no overclaiming: lane does not attempt to explain the overconsumption
- Pass 3
  - confirmed mandatory conclusions are explicitly stated
  - confirmed the recommendation is bounded (no action needed; optional hardening flagged)
  - confirmed cleared non-culprits are listed with specific evidence
  - confirmed the report does not create execution SSOTs or roadmaps
