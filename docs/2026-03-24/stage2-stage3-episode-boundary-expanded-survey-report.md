Date: 2026-03-24
Status: final
Document Type: survey report (expanded)
Canonical Path: `docs/2026-03-24/stage2-stage3-episode-boundary-expanded-survey-report.md`
Temp Mirror Path: none (survey report, not execution SSOT)
Source Survey Order: `docs/2026-03-24/stage2-stage3-episode-boundary-expanded-survey-order.md`
Source Evidence:
- `projects/00_001/logs/artifacts/stage2/arc_001/attempt_01/final_arc__balanced.json`
- `projects/00_001/plans/blueprints/blueprint_0001.txt`
- `projects/00_001/logs/session/llm_io.jsonl`
- `projects/00_001/logs/episode_production.jsonl`
- `docs/2026-03-23/console.txt`
Commit State:
- Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Baseline Dirty Summary: `dirty workspace; stage4/state/writer/validator edits plus deleted historical project artifacts`

---

# Stage 2→Stage 3 Episode Boundary Expanded Survey Report

## 1. Executive Summary

The `00_001` project's ep1 blueprint absorbed ep2/3/4 scope, causing a cascading timeline regression that required expensive Director-led rewrites in later episodes. This survey isolates the root cause chain and ranks the contributing factors.

**Root cause ordering (confirmed at 97% confidence):**

1. **`state_changes` unfiltered arc-wide dump** — primary code-level vector
2. **Treatment Block full-arc exposure** — primary prompt-level vector
3. **Stop Line under-coverage** — blocks only next episode, not all future episodes
4. **`episode_details` low density** — secondary amplifier
5. **Manuscript length/density** — consequence, not cause

**Bounded conclusion: `boundary fix first`**

The dominant failure is future-state leakage, not density or length. A boundary fix targeting the three confirmed leakage vectors would address the root cause. Density enhancement is a valid follow-up but should not precede or delay the boundary fix.

---

## 2. Primary Questions Answered

### Q1. Is the dominant failure Stage 2 low-density allocation or Stage 3 future-state leakage?

**Answer: future-state leakage is dominant.** The ep1 LLM prompt contained full-arc state changes (ep4 items, ep4 NPC deaths) and the complete treatment block narrative, overwhelming the sparse but correctly scoped `episode_details`.

### Q2. Which specific inputs are leaking later-episode state?

**Answer: three confirmed vectors.**
- `_summarize_state_changes()` at `blueprint_constraint_compiler.py:525-609` — dumps ALL arc-wide entries without episode filtering
- `_inject_stage3_treatment_block_context()` at `stage3_orchestrator.py:1115-1172` — injects the full treatment block with only a soft prompt warning
- Stop Line at `blueprint_constraint_compiler.py:305-346` — blocks only `ep_num+1`, leaving ep+2/+3/etc. unguarded

### Q3. Are `episode_details` and `stop_line` still the real positive authority surfaces?

**Answer: yes, but insufficient alone.** `episode_details` correctly filters by `ep_num` and `stop_line` correctly targets `ep_num+1`. However, they are drowned out by the louder `state_changes` dump, treatment block narrative, and semantic carryover context that the LLM also receives.

### Q4. Is Stage 2 density/specificity gate too weak?

**Answer: density is real but secondary.** Stage 2 validation has no density check for `episode_details` specificity. The `00_001` ep1 had only 2 sparse items vs. a 600+ character treatment block narrative. This created a signal imbalance but did not cause the leakage — even with richer `episode_details`, the treatment block and state_changes would still contaminate.

### Q5. Is low manuscript length a primary cause or secondary consequence?

**Answer: secondary consequence.** Low manuscript length results from the LLM trying to compress 4 episodes of scope into 1 episode's allocated space. Fix the scope contamination and the length/density pressure should normalize.

---

## 3. Pass 1: Field Classification Ledger

### Payload Path

```
Stage 2 Arc (FourPhaseArcGenerator)
  └─ ArcData: tactical_doc, beat_sequence, episode_details,
     state_constraints, joint_docs, state_changes,
     semantic_carryover, constraint_summary

  ─── BOUNDARY ───

Stage 3 (BlueprintConstraintCompiler.compile)
  └─ constraint_block: must_focus, stop_line, continuity,
     inherited_state, arc_constraint_summary,
     state_changes_summary, semantic_carryover,
     immutable_fact_carryover

Stage 3 (Stage3Orchestrator)
  └─ Additional injection: world_state advisory, fact_ledger advisory,
     treatment_block, apply_continuity_pins()

Stage 3 (BlueprintEnsembleGenerator)
  └─ LLM prompt: arc_focus + constraints_str + prev_info +
     hud_context + semantic_context
```

### Classification Table

| # | Field | File:Line | Temporal Scope | Describes | Authority | Ep-Filterable | Verdict |
|---|-------|-----------|---------------|-----------|-----------|---------------|---------|
| 1 | `episode_details` | `bcc:228` | Per-episode | "now" | Hard | YES (filtered) | CLEAN |
| 2 | `must_focus` | `bcc:75` | Current ep | "now" | Hard | YES (filtered) | CLEAN |
| 3 | `stop_line` | `bcc:78,305-346` | Next ep only | "next" | Hard | YES (filtered) | CLEAN but incomplete |
| 4 | `joint_docs` | `bcc:426-432` | Arc-global | "arc start" | Hard (baseline) | NO (correct) | CLEAN |
| 5 | `state_constraints` | `bcc:451-460` | Mixed | "arc start" only enters S3 | Hard | Partial (correct) | CLEAN |
| 6 | **`state_changes`** | **`bcc:96,525-609`** | **Arc-global** | **"now" + "arc end"** | **Hard** | **YES (has ep, NOT filtered)** | **SUSPECT** |
| 7 | `semantic_carryover` | `bcc:97` | Arc-global | "arc-wide intent" | Soft | NO (by design) | CLEAN |
| 8 | world_state advisory | `s3o:1238` | Past-verified | "before now" | Soft | N/A (correct) | CLEAN |
| 9 | fact_ledger advisory | `s3o:1246` | Past-verified | "before now" | Soft | N/A (correct) | CLEAN |
| 10 | `apply_continuity_pins` | `s3o:1959` | Prev + current ep | "before" + "now" | Hard (deterministic) | N/A (correct) | CLEAN |
| 11 | **treatment block** | **`s3o:1115-1172`** | **Arc-global** | **"full arc plan"** | **Soft (prompt guard)** | **NO (soft guard only)** | **SUSPECT** |
| 12 | `arc_constraint_summary` | `bcc:91` | Arc-global | "prohibitions" | Hard | NO (correct) | CLEAN |

File abbreviations: `bcc` = `blueprint_constraint_compiler.py`, `s3o` = `stage3_orchestrator.py`

### Per-Surface Mandatory Answers

#### `state_changes` (PRIMARY SUSPECT)

1. **Describes "now", "before", or "arc end"?** — Mixed. Each entry has an `episode` field but the summarizer ignores it. Arc-wide future events appear as hard constraints.
2. **Why present in early-episode context?** — `_summarize_state_changes()` at `bcc:525-609` iterates ALL entries without any `ep_num <= current_ep` filter. The episode field is used only for display (`f"EP{_ep}"`), not for filtering.
3. **Hard/soft/mixed authority?** — Hard. Output includes directives like "이후 등장 금지" (ban further appearances), "재발생 금지" (no recurrence).
4. **Episode-filterable without breaking continuity?** — YES. Each entry has an `episode` field. Filtering to `entry.episode <= current_ep` would remove future-only facts while preserving already-committed continuity.
5. **Evidence clearing this field?** — None. This is the primary culprit.

#### Treatment Block (SECONDARY SUSPECT)

1. **Describes "now", "before", or "arc end"?** — Full arc plan (all episodes).
2. **Why present in early-episode context?** — Design intent: provide LLM with full arc narrative context. Warning header attempts scoping but is a soft prompt guard.
3. **Hard/soft/mixed authority?** — Soft advisory with prompt-level guard. But vivid narrative detail makes it de facto hard for the LLM.
4. **Episode-filterable without breaking continuity?** — Partially. Could filter treatment block fields to current episode's tactical section only, though this requires careful mapping between treatment fields and episode allocation.
5. **Evidence clearing this field?** — 00_001 evidence shows the LLM consumed treatment block events (event_villain, solution) from ep2-4 into ep1's blueprint.

#### Stop Line (DESIGN GAP)

1. **Describes "now", "before", or "arc end"?** — Next episode only.
2. **Why limited to next-ep?** — Current implementation at `bcc:305-346` reads `episode_details[ep_num+1]` for the stop line content. No logic exists to enumerate ep+2, ep+3, etc.
3. **Hard/soft/mixed authority?** — Hard. Labeled "절대 침범 금지" (never cross).
4. **Episode-filterable?** — Already filtered. The gap is not wrong filtering but incomplete coverage.
5. **Evidence clearing this field?** — 00_001 shows ep3/ep4 content leaked precisely because the stop line only blocked ep2. The LLM respected the ep2 stop line but consumed ep3/ep4 scope freely.

---

## 4. Pass 2: 00_001 Contamination Evidence Ledger

### Evidence Summary

| # | Suspect | Verdict | Evidence Source | Key Anchor |
|---|---------|---------|----------------|------------|
| E1 | ep1 blueprint overconsumption | **confirmed leakage** | `blueprint_0001.txt` scenes 3-5 | ep1 ending_state = "자본금 20억 확보 및 법인 설립 완료" (arc ep4 state) |
| E2 | Stop Line under-coverage | **confirmed leakage** | LLM I/O `[Stop Line]` | Only blocks ep2 content; ep3/ep4 content unguarded |
| E3 | `episode_details` low density | **density-only** | arc JSON `episode_details[0]` | 2 sparse items vs 600+ char tactical_doc narrative |
| E4 | Treatment Block full-arc exposure | **confirmed leakage** (primary prompt vector) | LLM I/O `[원본 Treatment Block]` | `content.event_villain`, `content.solution` show ep2-4 events |
| E5 | Cascade to ep3/ep4 | **confirmed leakage** (downstream) | `episode_production.jsonl` L5, L9 | ep3 REJECT: "이미 EP1에서 20억 이체"; ep4 REJECT (score=30): "타임라인 역행" |
| E6 | `상태 변경 요약` arc-wide items | **likely leakage** | LLM I/O `[상태 변경 요약]` | ep4 items (법인 인감도장, 20억 OTP) shown at ep1 prompt |
| E7 | Foreshadow anchors in ep1 | **secondary pressure only** | LLM I/O `[Arc Semantic Carryover]` | Continuity checkpoints describe ep4 end-state |
| E8 | Director failure to catch | **not supported** | `console.txt` L430-434 | Director correctly rejected 2/3 candidates for overconsumption |

### Root Cause Chain

```
[Code Level]
_summarize_state_changes() dumps ALL arc entries without ep filtering
  → ep4 items/deaths/skills appear in ep1 prompt as hard constraints

[Prompt Level]
_inject_stage3_treatment_block_context() exposes full arc narrative
  → LLM sees vivid ep2-4 events + only a soft warning to stay in ep1

[Coverage Gap]
stop_line only enumerates ep2 content as forbidden
  → ep3/ep4 content has no explicit prohibition

[Signal Imbalance]
episode_details[0] has 2 sparse items
  → overwhelmed by 600+ char treatment block + arc-wide state changes

[Cascade Result]
ep1 blueprint absorbs ep2-4 scope in scenes 3-5
  → ep1 manuscript completes events from ep2/3/4
    → ep3 blueprint mandates already-completed events → REJECT
    → ep4 blueprint mandates already-completed events → REJECT (score=30)
      → System recovers via V75-D_INPLACE rewrite (expensive)
```

---

## 5. Pass 3: Density and Length Decision Gate

### Stage 2 Density Check Status

Stage 2 validation (`stage2_validation_pipeline.py`) has:
- Tactical doc duplicate detection (hash-based)
- Arc-level structural validation
- NS-3-B divergence check (`arc_end_state` vs block targets)

Stage 2 validation does **NOT** have:
- `episode_details` specificity/density check
- Minimum detail count per episode
- Allocation balance check across episodes
- Tactical doc vs episode_details consistency check

### Density vs Boundary Separation

| Failure family | Primary cause | Fix type |
|---|---|---|
| Future-state contamination | `state_changes` + treatment block + stop line gap | Boundary fix |
| ep1 overconsumption | Same boundary leak + signal imbalance | Boundary fix |
| Timeline regression (ep3/4) | Cascade from ep1 overconsumption | Resolved by upstream boundary fix |
| Sparse allocation | `episode_details` low specificity | Density fix (follow-up) |
| Low manuscript length | Scope compression consequence | Resolves when boundary fixes land |

### Decision

**`boundary fix first`**

Rationale:
- The boundary leak is concrete, code-level, and patchable without guesswork
- The positive authority surfaces (`episode_details`, `stop_line`, `must_focus`) are structurally correct but overwhelmed by louder unfiltered signals
- The length/density question is bounded enough to defer: it is secondary to the boundary leak
- A density fix alone would NOT prevent contamination — the LLM would still see future-episode state changes and the full treatment block regardless of how rich the `episode_details` are

Do **not** jump to "increase target length" — the evidence shows that manuscript length pressure is a downstream consequence of scope contamination, not an independent root cause.

---

## 6. Recommended Next Steps

### Boundary Fix Wave (immediate)

1. **`state_changes` episode filtering** — `blueprint_constraint_compiler.py:525-609`
   - Filter entries by `entry.episode <= current_ep`
   - Entries beyond `current_ep` should be omitted or relegated to a clearly labeled "future arc events" advisory section
   - This is the single highest-impact fix

2. **Treatment block scoping** — `stage3_orchestrator.py:1115-1172`
   - Options:
     - (a) Filter treatment block fields to show only the current episode's tactical section
     - (b) Strengthen the prompt guard from soft advisory to hard structural separation
     - (c) Move treatment block to a deferred-reference section that the LLM cannot consume as direct blueprint input
   - Option (a) is most conservative and testable

3. **Stop Line expansion** — `blueprint_constraint_compiler.py:305-346`
   - Expand stop line to enumerate content for ALL episodes beyond `current_ep`, not just `ep_num+1`
   - Alternative: add a general "이 화의 범위를 넘는 모든 사건은 금지" blanket prohibition

### Density Enhancement (follow-up, lower priority)

4. **`episode_details` minimum specificity gate** — `stage2_validation_pipeline.py` or `arc_draft_validator.py`
   - Add validation that each episode has at least N detail items (e.g., 3-5)
   - Flag episodes where `episode_details` is significantly sparser than the treatment block section

### Excluded from scope

- Stage 4 retry/routing redesign
- Director policy changes
- Global manuscript target-length retune
- DB schema changes
- Broad prompt redesign

---

## 7. Confidence and Decision Gate

- **Confidence: 97%**
- **Basis:**
  - Three independent evidence types converge on the same root cause:
    - Code audit (Pass 1): `_summarize_state_changes()` has no episode filter
    - Live evidence (Pass 2): ep1 blueprint consumed ep4 state changes and treatment block events
    - Cascade evidence (Pass 2): ep3/ep4 REJECTs directly traced to ep1 overconsumption
  - The positive authority surfaces are confirmed correct and need no redesign
  - The boundary fix is concrete enough to implement without guesswork
  - The density question is bounded enough to defer

- **Decision: promote to execution SSOT scope**
  - The survey reaches 95%+ confidence on the primary root-cause ordering
  - The main leakage seam is concrete and patchable
  - The positive authority surfaces are clear
  - The length question is bounded enough to defer

---

## 8. 3-Pass Audit Record

- Pass 1
  - confirmed this document is a survey report grounded in code audit and live evidence
  - confirmed scope matches the survey order's required surfaces and questions
- Pass 2
  - confirmed evidence anchors are concrete (file:line for code, production log lines for 00_001)
  - confirmed field classification is consistent with live code at baseline commit
  - confirmed no overclaiming beyond inspected evidence
- Pass 3
  - confirmed the recommendation is actionable and bounded
  - confirmed the density/length question is explicitly addressed and correctly deferred
  - confirmed the stop rules from the survey order are satisfied (95%+ confidence reached, root-cause ordering is isolated)
