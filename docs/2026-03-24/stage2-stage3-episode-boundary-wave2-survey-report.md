Date: 2026-03-24
Status: final
Document Type: survey report (Wave 2 follow-up)
Canonical Path: `docs/2026-03-24/stage2-stage3-episode-boundary-wave2-survey-report.md`
Temp Mirror Path: none (survey report, not execution SSOT)
Prerequisite: Wave 1 closed (`docs/2026-03-24/stage2-stage3-episode-boundary-wave1-execution-ssot.md`)
Source Survey Docs:
- `docs/2026-03-24/stage2-stage3-episode-boundary-expanded-survey-report.md`
- `docs/2026-03-24/stage2-stage3-episode-boundary-wave1-execution-ssot.md`
Evidence Artifacts:
- `projects/00_001/logs/artifacts/stage2/arc_001/attempt_01/final_arc__balanced.json`
- `projects/00_001/plans/blueprints/blueprint_0001.txt`
- `projects/00_001/logs/episode_production.jsonl`
- live code: `modules/core/stage2_validation_pipeline.py`, `modules/domain/agents/arc_draft_validator.py`, `modules/domain/agents/four_phase_arc_generator.py`
Commit State:
- Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Baseline Dirty Summary: `dirty workspace; Wave 1 patches landed in bcc + s3o + boundary tests; Wave 1 SSOT closure-audited`

---

# Stage 2-Stage 3 Episode Boundary Wave 2 Survey Report

## 1. Executive Summary

Wave 1 closed the primary failure chain (future-state leakage via `state_changes`, treatment block event fields, and stop line undercoverage). This survey investigates the four deferred topics to determine whether a bounded Wave 2 is warranted now or should wait for fresh live-run evidence.

**Root cause ordering after Wave 1 (post-fix):**

1. **`episode_details` sparseness** — secondary amplifier, now the loudest remaining gap; zero validation exists
2. **Allocation balance across episodes** — partially guarded (5:1 ratio advisory in `arc_draft_validator`); not the dominant risk
3. **LLM final `ep_count` judgment** — Python suggests, LLM decides; the heuristic is reasonable and was not the cause in `00_001`
4. **Manuscript length/density** — still a downstream consequence, not an independent cause

**Bounded conclusion: `no Wave 2 execution yet — defer pending fresh live-run evidence`**

Confidence: **92%** — below the 95% threshold for an execution SSOT. The ranking is solid, but the practical severity of `episode_details` sparseness post-Wave-1 is unverified without a fresh live run.

---

## 2. Investigation Questions Answered

### Q1. After Wave 1, what is now the dominant remaining failure risk?

**Answer: `episode_details` sparseness, but at uncertain severity.**

With Wave 1 in place:
- Future `state_changes` are filtered out of blueprint constraints
- Treatment block event fields (`event_villain`, `solution`, `reward`, `power_shift`) are quarantined
- Stop line now covers ALL future episodes with a blanket prohibition

The LLM's primary positive authority for "what to write in ep N" is now:
- `must_focus` (extracted from tactical_doc by episode)
- `episode_details[ep_num]` (from Stage 2 arc)
- `stop_line` (negative boundary, all future content)
- continuity pins + prior manuscript context

If `episode_details` is sparse (e.g., 2 items as in `00_001`), the LLM has limited positive guidance. However, in `00_001`, EP1 and EP2 both passed on the first attempt (PASS R0, score 96) despite having only 2 detail items each. The failures (EP3-7 rejections, 7/17 attempts) were all caused by Wave 1 leakage, not by density.

**Verdict: secondary amplifier, not yet proven as a primary failure cause post-Wave-1.**

### Q2. Can Stage 2 currently emit episodes that are structurally too thin?

**Answer: YES. There is zero validation on `episode_details`.**

Verified by grep: `episode_details` appears in neither `stage2_validation_pipeline.py` nor `arc_draft_validator.py`.

What IS validated today:
- `beat_sequence` count >= `ep_count` (flow guard)
- Per-beat word count: min 6 avg, min 4 per beat (flow guard)
- Tactical doc per-episode length: min 300 chars (arc_draft_validator)
- Tactical doc allocation balance: 5:1 max ratio advisory (arc_draft_validator)
- Tactical doc total length: min `ep_count * 450` chars (arc_draft_validator)

What is NOT validated:
- `episode_details` field existence
- `episode_details` per-episode detail count
- `episode_details` vs tactical_doc consistency
- Per-episode detail specificity or richness

An arc with `episode_details: [{"ep_num": 1, "details": ["도입"]}]` (1 item, 2 chars) would pass all current checks.

### Q3. What is the minimum bounded Python guardrail that improves allocation safety?

**Answer: an advisory warning when `episode_details` is too sparse.**

The minimum effective intervention:
- In `arc_draft_validator.py`, add a check: if any episode has < 3 detail items in `episode_details`, emit an advisory warning
- This is NOT a REJECT — it follows the AGENTS.md principle ("Python은 수집만, 판단은 LLM이")
- The advisory gets passed to the ConsensusValidator / Director, who can decide whether to regenerate
- Implementation: ~20 lines in `arc_draft_validator.py`, one new test

Why NOT a REJECT:
- 2 items/episode produced clean first-pass results in `00_001` EP1/EP2
- Different genres may have naturally sparser or denser episode details
- The LLM can elaborate from sparse details; the question is whether it does so well enough

### Q4. Should Wave 2 be allocation-balance first, density/specification first, paired small wave, or defer?

**Answer: `no Wave 2 execution yet — defer pending fresh live-run evidence`**

Rationale:
1. Wave 1 addressed the dominant failure chain. EP3-7 rejections in `00_001` were all continuity-firewall failures traced to EP1 scope overconsumption — a problem now fixed.
2. Without a fresh live run, the practical impact of `episode_details` sparseness post-Wave-1 is speculative. EP1/EP2 passed first-try despite 2 items each.
3. The 현상황요약 priority ("작가 측의 1차 합격 확률 + 수렴률") is best served by validating Wave 1 in a fresh run first.
4. If the fresh run reveals density-related failures (e.g., vague blueprints, empty scenes, under-filled manuscripts), then a targeted `episode_details` advisory would be the right Wave 2 scope.
5. Proactive implementation without evidence would violate the survey-first principle.

---

## 3. Code-Level Evidence

### 3.1 `ep_count` Ownership

| Component | Role | File:Line |
|---|---|---|
| `_determine_ep_count()` | Python heuristic: block content length → ep_count suggestion | `four_phase_arc_generator.py:453-524` |
| `_build_pacing_signal_payload()` | Collects density signals, labels them "LLM decides final ep_count" | `four_phase_arc_generator.py:526-578` |
| `_build_pacing_signal_guide()` | Formats pacing prompt: "Python collected, LLM decides final ep_count" | `arc_ensemble.py:779-826` |
| `_normalize_pacing_contract()` | Post-generation: reads LLM's chosen `ep_count`, coerces within bounds (2-6) | `arc_ensemble.py:828-860` |

**Conclusion:** Python suggests `ep_count` via content-length heuristic. The LLM can accept or override within [2, 6]. For `00_001`, Python suggested 4 and LLM chose 4 — they agreed. The heuristic produced a reasonable count for the content. This is not a primary failure vector.

### 3.2 `episode_details` Validation Gap

| Validator | Checks `episode_details`? | What it checks instead |
|---|---|---|
| `ArcDraftValidator.validate()` | **NO** | tactical_doc length, beat density, dead NPC, duplicates, location/injury continuity |
| `Stage2ValidationPipeline._stage2_flow_guard()` | **NO** | beat count >= ep_count, per-beat word count, narrative diversity |
| `Stage2ValidationPipeline.run_validation()` | **NO** | DraftValidator → SelfReflector → Consensus → FlowGuard → DuplicateGuard → ArcCorrector → ContinuityInspector |
| `ConstraintCompiler` | **NO** | item/grant tracking, state continuity |

**Zero production code validates `episode_details` at any stage of the pipeline.**

### 3.3 Existing Allocation Guards

| Guard | File:Line | What it catches | Severity |
|---|---|---|---|
| Beat count >= ep_count | `stage2_validation_pipeline.py:1250` | Narrative collapse risk | REJECT |
| Per-beat word count | `stage2_validation_pipeline.py:1287-1325` | Sparse beat descriptions | REJECT |
| Tactical doc allocation balance (5:1) | `arc_draft_validator.py:432-465` | Extreme imbalance | Advisory (5pt penalty) |
| Tactical doc per-episode min length (300c) | `arc_draft_validator.py:432-465` | Short episodes | Advisory (3pt per) |
| Tactical doc total min length (ep_count×450) | `arc_draft_validator.py:406-430` | Overall thin arc | Advisory |

These guards cover `beat_sequence` and `tactical_doc`. None covers `episode_details`.

---

## 4. `00_001` Evidence Reassessment

### 4.1 Episode Details Density

From `final_arc__balanced.json`:

| Episode | Detail Items | Detail Content |
|---|---|---|
| EP 1 | 2 | "2024년 고독사 후 2006년 본가 침실에서 깨어남"; "18년 치 거시경제 데이터 복기 및 두통 극복" |
| EP 2 | 2 | "아버지 한정호의 서재로 호출됨"; "형들의 무관심 속에서 그룹 지원 거절하고 독자적 투자사 설립 선언" |
| EP 3 | 2 | "은행 PB 박성호를 만나 신탁 펀드 및 스폰서십 해지 강행"; "자산 20억 원 현금화 완료" |
| EP 4 | 2 | "여의도 낡은 오피스텔 계약 및 SW인베스트먼트 설립 완료"; "저녁 뉴스에서 이란 핵 문제 보도를 보며 WTI 투자 준비" |

- Uniform 2 items/episode — not imbalanced, just sparse
- Each item is a concrete narrative beat, not generic filler
- The content is specific enough to drive a single scene each

### 4.2 Production Pass/Fail Pattern

| Episode | Attempts | Result | Failure Cause |
|---|---|---|---|
| EP 1 | 1 | PASS (s96) | — |
| EP 2 | 1 | PASS (s96) | — |
| EP 3 | 3 | PASS (R2) | Blueprint re-did EP1's 20B liquidation (Wave 1 leakage) |
| EP 4 | 3 | PASS (R2) | Price point continuity error (cascade from EP1 overconsumption) |
| EP 5 | 2 | PASS (R1) | Blueprint misaligned vs EP4 state (cascade) |
| EP 6 | 3 | PASS (R2) | Item persistence confusion across boundary (cascade) |
| EP 7 | 2 | PASS (R1) | Candidate misalignment (cascade) |

**Total: 17 attempts for 7 episodes. 7 rejections — all traceable to Wave 1 leakage cascade, not to density.**

### 4.3 Post-Wave-1 Counterfactual

With Wave 1 fixes applied:
- EP1 blueprint would NOT see EP4 `state_changes` (법인 인감도장, 20억 OTP) — filtered by `_within_ep()`
- EP1 blueprint would NOT see treatment block `event_villain`/`solution` — quarantined
- EP1 stop line would enumerate EP2, EP3, EP4 content as forbidden — blanket prohibition

Expected effect: EP1 would stay within its 2-item scope. EP3-7 cascade would not occur. The 7 rejections would likely not happen.

But: would EP1's 2-item `episode_details` produce a *quality* blueprint? The evidence says yes (EP1 passed R0 at score 96). But that was with the full arc context leaking in — the LLM had *too much* material, not too little. In a post-Wave-1 world, the LLM would have *less* material. This is the open question.

---

## 5. Remaining Cause Ranking

| Rank | Cause | Classification | Actionable Now? | Confidence |
|---|---|---|---|---|
| 1 | `episode_details` sparseness (0 validation) | secondary amplifier | **maybe** — depends on fresh run | 88% |
| 2 | Allocation balance across episodes | partially guarded | no — existing 5:1 advisory is adequate | 92% |
| 3 | LLM final `ep_count` judgment | functioning as designed | no — heuristic is reasonable | 95% |
| 4 | Manuscript length/density | still a consequence | no — resolves when upstream fixes land | 95% |

### `final ep_count judgment left to the LLM`

**Classification: not actionable yet.**

The current split is:
- Python determines `ep_count_suggestion` via content-length heuristic (lines 453-524)
- LLM can override within [2, 6] bounds
- LLM prompt explicitly says "Python collected, LLM decides final ep_count"
- Post-generation, Python coerces within pace_mode bounds

This split is reasonable:
- The heuristic correctly determined 4 episodes for `00_001`'s content
- The LLM agreed with 4
- The problem was not the count but the scope contamination
- Moving `ep_count` entirely to Python would steal a creative decision without evidence that the LLM is making bad choices

**Verdict: the `ep_count` split is functioning as designed and is not a primary or secondary failure vector.**

---

## 6. Recommendation

### Primary: `no Wave 2 execution yet`

**Run a fresh live run with Wave 1 fixes first.** Then assess:

1. **EP1 first-pass acceptance**: Does it still pass R0 with proper boundary isolation?
2. **EP3-7 cascade elimination**: Are the continuity-firewall rejections gone?
3. **Blueprint quality from sparse details**: Does the LLM produce adequate blueprints from 2-item `episode_details`?
4. **Manuscript density**: Is the manuscript length/quality acceptable when the LLM has only bounded current-episode context?

### If the fresh run reveals density-related failures:

Promote to Wave 2 with scope:

**`episode_details` minimum specificity advisory** — `arc_draft_validator.py`
- Add an advisory check: if any episode has < 3 detail items in `episode_details`, emit a warning
- Advisory only (not REJECT) — follows "Python은 수집만" principle
- The warning gets passed to ConsensusValidator / Director for judgment
- Estimated implementation: ~20 lines in `arc_draft_validator.py`, one test file

### If the fresh run passes cleanly:

No Wave 2 needed. The density issue was a secondary amplifier that resolved when the primary cause was fixed.

### Explicitly deferred regardless of fresh run:

- `ep_count` judgment redesign — not supported by evidence
- Manuscript length retune — still a consequence
- Stage 4 retry routing — out of scope
- Broad prompt architecture rewrite — out of scope

---

## 7. Confidence and Decision Gate

- **Confidence: 92%**
- **Basis:**
  - The remaining-cause ranking is well-supported by code audit and `00_001` evidence
  - Wave 1's effect on the cascade is clear (all 7 rejections trace to leakage)
  - The `ep_count` question is conclusively answered (Python suggests, LLM decides, split is reasonable)
  - The 8% uncertainty comes from: no fresh live-run evidence to confirm that density sparseness does/doesn't cause post-Wave-1 failures
- **Decision: do NOT create an execution SSOT**
  - Confidence is below 95%
  - The remaining gap is empirical (fresh run needed), not analytical
  - Premature implementation would be speculative

---

## 8. Generalization Beyond `00_001`

The `episode_details` sparseness pattern likely generalizes:
- The field is LLM-generated with no downstream validation
- Different treatment blocks produce different detail densities
- Investment genre may have naturally sparser details than wuxia (fewer physical events, more procedural steps)
- But: wuxia arcs with rich beat_sequences may compensate via `must_focus` extraction from tactical_doc

The Wave 1 leakage pattern definitely generalizes:
- It was structural code-level (`_summarize_state_changes` had no filter, treatment block was unguarded, stop line covered only next-ep)
- Any multi-episode arc would exhibit the same contamination

**Wave 1 fixes are universally applicable. Wave 2 density fixes may be genre- or content-dependent.**

---

## 9. 3-Pass Audit Record

- Pass 1
  - confirmed this document is a survey report, not an execution SSOT
  - confirmed scope covers all four deferred topics from the Wave 1 SSOT
  - confirmed Wave 1 patches are verified live in workspace

- Pass 2
  - confirmed code evidence: zero `episode_details` validation in the entire Stage 2 pipeline
  - confirmed `ep_count` ownership: Python suggests (heuristic), LLM decides (prompt), Python coerces (bounds)
  - confirmed `00_001` production pattern: 2 items/ep, EP1/EP2 passed R0, EP3-7 failed from leakage cascade
  - confirmed no overclaiming: the density issue is marked "uncertain severity" not "confirmed problem"

- Pass 3
  - confirmed recommendation is actionable: "run fresh live run, then decide"
  - confirmed the stop rule is satisfied: confidence < 95% → no execution SSOT
  - confirmed the `ep_count` question is explicitly and conclusively answered
  - confirmed Wave 1 topics are not reopened

## 10. Confidence

- Confidence: 92%
- Below 95% threshold — no execution SSOT produced
- Follow-up trigger: fresh live-run results showing density-specific failures
