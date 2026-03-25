# Stage 2 `episode_details` Specificity Floor — Compact Survey

Date: 2026-03-25
Status: final (3-pass audited)
Document Type: survey (compact, survey-only)
Canonical Path: `docs/2026-03-25/stage2-episode-details-specificity-floor-survey.md`
Commit State:
- Baseline Commit: `f61a35c89b4c964afbfa902790560448d98b1bfb`
- Baseline Dirty Summary: `dirty: Wave1 landed (uncommitted), canary artifacts, prior survey docs`
Prior Art:
- `docs/2026-03-25/opus-bp-clarity-density/t1-stage2-upstream-specificity.md`
- `docs/2026-03-25/bp-clarity-density-4terminal-merge-audit.md`

## 1. Governing Question

Can a Python-enforceable specificity floor on `episode_details` meaningfully improve Stage 3 blueprint inputs without taking creative allocation judgment away from the LLM?

## 2. Evidence Surfaces Examined

### Code (directly read)

| File | Relevance | `episode_details` references |
|------|-----------|------------------------------|
| `modules/models/arc.py` L214-216 | Pydantic field definition | `list[dict] = Field(default_factory=list)` — optional |
| `modules/core/response_schemas.py` L484-494 | Gemini JSON schema | `{ep_num: int, details: string[]}` — NOT in required array |
| `modules/domain/agents/four_phase_arc_generator.py` L1000-1003 | ASP fallback preservation | preserves original when ASP drops it |
| `modules/domain/agents/arc_draft_validator.py` | Draft validation | **0 references** — no quality check |
| `modules/core/stage2_validation_pipeline.py` | Stage 2 validation | **0 references** — no quality check |
| `modules/domain/agents/unified_arc_validator.py` L534-566 | Type check only | ADVISORY severity, checks list/dict/int types only |
| `modules/core/tactical_utils.py` L31-73 | 3-layer extraction | Priority: episode_details > regex > full tactical_doc |
| `modules/domain/agents/blueprint_ensemble.py` L215-238 | Stage 3 consumption | double injection (ep_details + tactical regex fallback) |
| `modules/domain/agents/blueprint_constraint_compiler.py` L282 | Pass-through | extraction forwarding only |
| `modules/core/stage3_orchestrator.py` L1950-1953 | Stage 3 call site | `extract_episode_tactical(... episode_details=...)` |
| `modules/core/stage2_finalizer.py` L1058 | constraint_summary | keyword-only extraction — separate concern |

### Artifacts (directly read)

| Artifact | Source |
|----------|--------|
| Arc 1 (ep1-5), investment genre | `projects/0324_00_/logs/artifacts/stage2/arc_001/...final_arc__conservative.json` |
| Arc 2 (ep6-10), investment genre | `projects/0324_00_/logs/artifacts/stage2/arc_002/...final_arc__balanced.json` |
| EP1, EP5, EP6 blueprints | `projects/0324_00_/logs/artifacts/stage3/ep_000{1,5,6}/...` |
| Canary 0325 arc data | `projects/canary_0325/project_data.db` → `anchors.arcs` (via t1 survey) |
| Canary EP5, EP7, EP8 blueprints | `projects/canary_0325/logs/artifacts/stage3/...` |

## 3. Findings

### F-1. `episode_details` has zero validation beyond type checking

- `stage2_validation_pipeline.py`: 0 references
- `arc_draft_validator.py`: 0 references
- `unified_arc_validator.py`: type-only check (list/dict/int), ADVISORY severity, non-blocking
- No check for: string length, bullet count per episode, episode range coverage, named-entity presence, or content quality

### F-2. `episode_details` is always a compressed subset of `tactical_doc`

Measured from live artifacts (investment genre, 0324_00_ + canary_0325):

| Metric | tactical_doc | episode_details |
|--------|--------------|-----------------|
| Per-episode avg length | ~870-925 chars | ~100-160 chars (2 bullets x 50-80 chars) |
| Specificity grade | Narrative-grade (named entities, amounts, locations, state brackets) | Compressed summary (subset of tactical) |
| Unique information | Yes (ground truth) | **No** (always derivative) |

No episode_details entry in any examined artifact contained information absent from tactical_doc.

### F-3. The 3-layer fallback makes thin episode_details non-blocking

`extract_episode_tactical()` in `tactical_utils.py`:
1. Priority 1: episode_details bullet → ~100-160 chars
2. Priority 2: regex extraction from tactical_doc → ~500-925 chars per episode
3. Priority 3: full tactical_doc fallback

When episode_details is thin or absent, the regex path extracts **richer** content from tactical_doc. A missing or sparse episode_details actually results in the Stage 3 generator receiving **more** context, not less.

### F-4. Live data shows upstream specificity is concrete, not generic

All examined episode_details across both projects contain:
- Real-world event anchors ("이란 핵 위기", "에콰도르 자원 국유화")
- Specific quantities ("20억 원", "3배 레버리지", "3.75억 원")
- Named NPCs ("박성호 PB", "한정호 회장", "한태준/한태민")
- Progression markers (knowledge → capital → infrastructure → execution)

No episode found with generic/placeholder-level details ("something happens", "emotional growth occurs").

### F-5. Clarity loss is a downstream (Stage 3) phenomenon, not upstream

Decisive comparison from t1 survey:

| Item | tactical_doc (Stage 2 input) | Blueprint (Stage 3 output) |
|------|------------------------------|---------------------------|
| EP7 target | "시선이 남미 대륙의 한 지점에 머물렀다. '에콰도르...'" | "다가올 시장의 파도를 직감한다" |
| EP7 brothers | "한태준은 어이가 없다는 듯 헛웃음... 한태민은 '깡통 차고...'" | "한태준과 한태민이 15억 투자를 비웃는다" |

The LLM selectively compresses specificity during blueprint generation despite having full tactical_doc available. This is not an upstream input problem.

### F-6. Double injection is harmless but wasteful

`blueprint_ensemble.py` L215-238 injects episode_details twice:
1. Via `extract_episode_tactical()` Priority 1 path
2. Via explicit `[{ep_num}화 추가 사건]` header prepend

~200-400 token redundancy within the 15K char budget. Non-harmful but inefficient.

## 4. Investigation Answers

### Q1. Where is `episode_details` shape defined or implied today?

- Schema: `response_schemas.py` L484-494 — `{ep_num: int, details: string[]}`
- Model: `arc.py` L214-216 — `list[dict] = Field(default_factory=list)`
- Prompt guidance: `ensemble.yaml` L219-229 — "장소-인물-사건 형식, 최소 1개 이상"
- Required status: **optional** in schema, Pydantic default `[]`

### Q2. What fields are too sparse to support strong Stage 3 blueprint generation?

**None critically.** `episode_details` is sparse by design (~50-80 chars/bullet), but `tactical_doc` (~870-925 chars/episode) is the actual specificity carrier. The 3-layer fallback ensures Stage 3 always gets the richer source.

The only identified Stage 2 → Stage 3 delivery gap is `constraint_summary` (keyword-only extraction can produce empty string for early arcs), but this is a constraint delivery issue, not a specificity floor issue.

### Q3. What minimum specificity floor could Python validate safely?

Technically feasible candidates (ordered by safety):

| Candidate Floor | Implementation | Safety | ROI |
|----------------|----------------|--------|-----|
| A. Min detail string length (>20 chars) | `len(detail) > 20` per bullet | Safe — no creative judgment | Very low — never triggered in live data |
| B. Min 1 item per episode in arc range | Check each ep_num in [ep_start, ep_end] | Safe — structural completeness | Low — fallback to tactical_doc compensates |
| C. Named-entity presence check | Regex for proper nouns or quoted strings | Medium — false positives in non-Korean text | Low — tactical_doc already carries them |
| D. Min per-episode char budget | Sum(details) > N chars per episode | Medium — genre-dependent threshold | Very low — suppresses valid compressed style |

All candidates are technically implementable but have **very low ROI** because:
- `episode_details` is never the sole input path (3-layer fallback)
- `tactical_doc` is the real specificity carrier and is already narrative-grade
- No live artifact exhibits the "thin upstream → thin blueprint" failure mode

### Q4. Should the next wave be floor, floor+validator, or no wave?

**No wave yet.**

Reasoning:
- The t1 survey, the merge audit, and this compact re-survey all converge: Stage 2 upstream specificity is not the dominant blueprint clarity limiter
- Wave 1 (Stage 3 authority re-banding + density prevalidation) just landed — its effect on blueprint clarity should be measured before introducing upstream changes
- A specificity floor would add validation overhead for a field that is compensated by fallback and has no observed failure mode in live runs
- The operating principle of single-culprit-first attribution would be violated by introducing upstream changes before measuring the Wave 1 downstream improvement

## 5. Candidate Guardrails Ranked by ROI and Blast Radius

| Rank | Candidate | ROI | Blast Radius | Recommendation |
|------|-----------|-----|--------------|----------------|
| 1 | `constraint_summary` keyword robustification | Medium | Low (Stage 2 finalizer only) | Best Stage 2 improvement, but is a constraint-delivery fix, not a specificity floor |
| 2 | Remove `episode_details` double injection | Low-Medium | Very low (blueprint_ensemble L224-232 only) | Saves ~200-400 tokens/episode, zero quality risk |
| 3 | Min 1 episode_details item per episode | Low | Low (validator + advisory) | Safe structural check, but fallback compensates |
| 4 | Min detail string length >20 chars | Very low | Very low | Never triggered in observed data |
| 5 | Named-entity presence in details | Very low | Medium (genre-dependent threshold) | False-positive risk across genres |

## 6. Confidence and Limits

Estimated confidence: 95%

Why this clears the gate:
- Three independent evidence layers converge (code static analysis + live artifact inspection + prior t1 survey)
- Both the 0324_00_ production run and canary_0325 show the same pattern: concrete upstream, selective downstream loss
- No examined artifact exhibits the "thin episode_details → thin blueprint" failure mode
- The 3-layer fallback architecture makes episode_details sparseness structurally non-blocking

Limits:
- Only investment genre examined in depth — other genres (wuxia, hunter, fantasy) may behave differently
- Single canary + single production run — not a large statistical sample
- LLM generation stability of episode_details across model versions untested

## 7. Mandatory Final Lines

- Dominant upstream specificity gap: `none observed` — episode_details is derivative of tactical_doc and compensated by 3-layer fallback; clarity loss is a Stage 3 phenomenon
- Best bounded next wave: `no wave yet` — measure Wave 1 (Stage 3 authority re-banding + density prevalidation) effect first; if blueprint clarity still lags, `constraint_summary keyword robustification` is the highest-ROI Stage 2 intervention, not an episode_details specificity floor
- Should Codex open an execution SSOT now: `no`
