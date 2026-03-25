# T4. Bounded Structural Improvement Option Ledger

Date: 2026-03-25
Lane: T4 (Terminal 4)
Status: survey-only
Master Order: `docs/2026-03-25/bp-clarity-density-structural-improvement-4terminal-master-order.md`
Save Path: `docs/2026-03-25/opus-bp-clarity-density/t4-bounded-improvement-option-ledger.md`
Baseline Commit: `f61a35c89b4c964afbfa902790560448d98b1bfb`

## 1. Survey Scope

This ledger synthesizes findings from the T1-T3 evidence surfaces to produce bounded, operational improvement candidates for blueprint clarity and density. It does NOT choose the final wave — that decision belongs to the merge owner.

Evidence surfaces inspected:
- `blueprint_ensemble.py` — prompt assembly, authority layering, 10 constraint surfaces
- `blueprint_constraint_compiler.py` — constraint compilation, compile_to_prompt formatting
- `unified_blueprint_validator.py` — Python prevalidation checks, quality_risk signal
- `three_phase_blueprint_runtime.py` — retry state, Director feedback injection
- `director_prompts.py` — DIRECTOR_AUDIT_PROMPT_V30 scoring rubric
- `response_schemas.py` — BLUEPRINT_SCHEMA, DIRECTOR_AUDIT_SCHEMA
- `four_phase_arc_generator.py` — Stage 2 arc output structure
- `arc_ensemble.py` — Stage 2 ensemble evaluation, required fields
- `stage3_orchestrator.py` — semantic_context assembly, tactical extraction
- `tactical_utils.py` — extract_episode_tactical regex extraction

## 2. Root-Cause Diagnosis Summary

Blueprint clarity/density is currently limited by **four concurrent factors**, not one dominant bottleneck:

| Factor | Severity | Layer |
|--------|----------|-------|
| Stage 2 `episode_details` is optional and rarely populated; tactical_doc is unstructured prose requiring Stage 3 re-parse | Moderate | Upstream |
| 10 authority surfaces in blueprint prompt lack explicit priority ordering; LLM must infer which surfaces override | Moderate | Authority |
| Python prevalidation cannot detect vague/thin content — only structural/factual checks | High | Validation |
| No prompt-level self-audit; no scene-level Director feedback in retry loop | High | Self-Audit |

The interaction pattern is: **upstream sparsity produces thin constraint input → authority mixing obscures which constraints to prioritize → prevalidation cannot see the resulting blur → Director feedback is too coarse to guide targeted density improvement on retry**.

## 3. Option Ledger

### Option A: Prompt-Level Self-Audit Instruction

**Category**: self-audit opportunity
**Structural or cosmetic**: secondary amplifier
**Blast radius**: prompt-only, zero code change
**Estimated cost**: low (prompt template edit)

**Description**:
Add a self-check instruction block at the end of the ensemble generation prompt, instructing the LLM to verify each scene meets minimum density criteria before submitting.

**Mechanism**:
```
[자기 점검] 제출 전 아래를 확인하세요:
- 각 씬에 구체적 행동(전투 동작, 대화 발화, 이동 경로)이 1개 이상 있는가?
- 각 씬에 NPC 이름이 최소 1회 명시되었는가?
- integrated_scenario에 감각 묘사(시각/청각/촉각)가 3회 이상 있는가?
- ending_hook이 다음 화 유인력을 가진 구체적 상황인가?
```

**Why secondary**:
- Self-audit cannot fix thin upstream input — if tactical_doc lacks per-episode specificity, the LLM cannot invent details
- Self-audit helps most when the LLM already has sufficient material but under-deploys it
- Industry evidence: self-check prompts improve output quality ~5-15% for capable models, but do not fix information-starved generation

**Pairs with**: Option C (density floor in prevalidation), Option E (scene-level Director feedback)
**Should NOT pair with**: Option D (upstream specificity floor) in the same wave — too many moving parts for clean canary

---

### Option B: Explicit Authority Priority Ordering in Prompt

**Category**: authority re-banding
**Structural or cosmetic**: structural (root-cause)
**Blast radius**: prompt assembly in `blueprint_ensemble.py` `_format_constraints` + `compile_to_prompt`
**Estimated cost**: moderate (prompt restructuring, no schema change)

**Description**:
Add an explicit priority ordering preamble to the constraint block, with conflict resolution rules. Currently the LLM sees 10 coequal authority surfaces with varied label strengths (some use "변경금지", others are purely descriptive). Positional authority (FACT-LOCK prepended) is the only implicit signal.

**Current state**:
- Tier 1 (FACT-LOCK, CAPITAL-LOCK): strong imperative language, positional advantage
- Tier 2 (MUST_FOCUS, STOP_LINE): strong imperative, but no explicit override relationship
- Tier 3 (CONTINUITY, INHERITED_STATE): **weak descriptive labels**, no imperative
- Tier 4 (ARC_CONSTRAINT_SUMMARY, STATE_CHANGES_SUMMARY, SEMANTIC_CARRYOVER): informational/advisory

**Proposed change**:
Insert at the start of constraint block:
```
[제약 우선순위]
1. FACT-LOCK: 확정 사실. 다른 모든 제약보다 우선. 충돌 시 FACT-LOCK이 이긴다.
2. STOP_LINE: 위반 시 즉시 REJECT. MUST_FOCUS와 충돌 시 STOP_LINE이 이긴다.
3. MUST_FOCUS: 이번 화 핵심. 반드시 포함하되 FACT-LOCK/STOP_LINE을 침범하지 않는다.
4. CONTINUITY: 이전 화 연속성. 무시하면 독자 이탈. 위 3개와 충돌 시 위 항목 우선.
5. 나머지 (INHERITED_STATE, ARC_CONSTRAINT, STATE_CHANGES, SEMANTIC_CARRYOVER): 참고용.
```

**Why structural**:
- Eliminates the LLM's guessing about which surface overrides which
- Directly addresses the authority-mixing root cause
- Measurable: canary can track FACT-LOCK/STOP_LINE violation rates before vs. after

**Pairs with**: Option A (self-audit), Option C (density prevalidation)
**Should NOT pair with**: Option D (upstream) in the same wave

---

### Option C: Python Prevalidation Density Signal

**Category**: validation blind spot
**Structural or cosmetic**: structural (root-cause)
**Blast radius**: `unified_blueprint_validator.py` prevalidate method only
**Estimated cost**: moderate (new Python checks, no LLM cost)

**Description**:
Add Python-level density checks that can catch thin/vague blueprints before Director invocation.

**Current blind spots** (prevalidator cannot detect):
1. Vague prose within structure (sentences lack specificity)
2. Repetitive/padded content that hits char count but lacks substance
3. Shallow scene goals ("무언가 일이 발생한다")
4. Thin relationship_changes without justification
5. Integrated scenario shorter per-scene than minimum density floor

**Proposed checks** (all advisory-only, Python 수집 → Director 판단):

| Check | Severity | Mechanism |
|-------|----------|-----------|
| Per-scene minimum length | MINOR | `len(scene_summary) < 80` → advisory warning |
| Scene goal presence and minimum length | MINOR | `len(goal) < 20` → advisory warning |
| Integrated scenario density floor | MAJOR | `len(integrated) / scene_count < 300` → per-scene avg too thin |
| Concrete noun density proxy | MINOR | Count named entities (한글 고유명사 패턴) in integrated; < 3 per scene → advisory |
| `quality_risk` grading (not binary) | N/A | Replace `bool(issues)` with 3-level: `none` / `minor` / `major` |

**Why structural**:
- Current prevalidation is blind to density — the single largest gap in the quality gate pipeline
- Python checks are free (no LLM cost) and run before Director, reducing wasted Director calls on obviously thin blueprints
- Graded quality_risk enables downstream differentiation (e.g., `major` quality_risk could influence retry strategy selection)

**Design constraint**: All new checks must remain advisory-only per 대원칙 #1 ("Python은 수집만, 판단은 LLM이"). These checks generate warnings for Director, not blocks.

**Pairs with**: Option A (self-audit), Option B (authority re-banding)
**Should NOT pair with**: Option F (schema tightening) in the same wave — verify density signal value first

---

### Option D: Upstream Specificity Floor (Stage 2)

**Category**: upstream specificity
**Structural or cosmetic**: structural (root-cause)
**Blast radius**: Stage 2 `ARC_DESIGN_SCHEMA`, `arc_ensemble.py` scoring, `four_phase_arc_generator.py` prompt
**Estimated cost**: high (Stage 2 schema + prompt + ensemble evaluation change)

**Description**:
Make `episode_details` a required field with structured per-episode content, and add per-episode beat-to-scene mapping to reduce Stage 3's need to re-parse tactical_doc.

**Current state**:
- `episode_details` is **optional** in ARC_DESIGN_SCHEMA (not in required list)
- `tactical_doc` is **required** but unstructured prose (500+ chars per episode)
- Stage 3 relies on regex extraction (`_EPISODE_HEADER_PATTERNS`) to parse tactical_doc — lossy
- Arc ensemble evaluation only checks `ep_mentions < ep_count` (presence, not depth)

**Proposed change**:
1. Add `episode_details` to ARC_DESIGN_SCHEMA required fields
2. Define minimum per-episode structure: `{ep_num, key_events: [str], scene_goals: [str], expected_tension: int}`
3. Add arc_ensemble scoring penalty for sparse episode_details (parallel to existing tactical_doc length penalty)

**Why structural**:
- Directly addresses the upstream sparsity root cause
- Eliminates Stage 3's redundant NLP work on tactical_doc
- Makes Stage 2 → Stage 3 handoff deterministic instead of regex-dependent

**Why high cost**:
- Changes Stage 2 LLM output format — requires prompt + schema + evaluation changes
- May increase Stage 2 token cost (LLM must produce more structured output)
- Requires Stage 2 regression testing
- Risk: if LLM cannot consistently populate structured episode_details, the required field becomes a retry tax

**Should be a separate wave**: This is a Stage 2 change that should be canary-tested independently from Stage 3 improvements.

**Pairs with**: Nothing in the same wave — test alone for clean canary signal.

---

### Option E: Scene-Level Director Feedback in Retry

**Category**: self-audit opportunity (Director-side)
**Structural or cosmetic**: structural (amplifier on root-cause)
**Blast radius**: `director_prompts.py` DIRECTOR_AUDIT_PROMPT_V30 + `DIRECTOR_AUDIT_SCHEMA` + retry feedback injection
**Estimated cost**: moderate-high (Director prompt + schema + retry state restructuring)

**Description**:
Extend the Director audit to output per-scene diagnostics, and feed scene-level feedback into the retry loop so the Ensemble Generator knows which specific scenes need density improvement.

**Current state**:
- Director scores `scene_composition` (0-20 pts) but outputs a single aggregate feedback string
- Retry state captures `prev_reject_feedback` as one string — no scene-level granularity
- Ensemble Generator on retry receives "장면의 밀도를 높이세요" without knowing which scene is thin
- `DIRECTOR_AUDIT_SCHEMA` has no `scene_by_scene_feedback` field

**Proposed change**:
1. Add `scene_diagnostics` array to `DIRECTOR_AUDIT_SCHEMA`:
   ```
   scene_diagnostics: [{scene_id: str, density_ok: bool, clarity_issue: str}]
   ```
2. Inject per-scene diagnostics into retry feedback bundle
3. Ensemble Generator prompt on retry includes: "Scene 3 밀도 부족: {clarity_issue}"

**Why structural**:
- Directly addresses the coarse-feedback gap that prevents targeted density improvement on retry
- The current retry loop already collects and re-injects feedback — this tightens its granularity
- Scene-level feedback is actionable; aggregate feedback is not

**Why moderate-high cost**:
- Director prompt change requires careful testing (larger output = higher Director token cost)
- Schema change requires backward compatibility
- Retry state restructuring is non-trivial

**Pairs with**: Option A (self-audit), Option C (density prevalidation)
**Should be tested after**: Option B and C are validated

---

### Option F: Schema Tightening for Density Enforcement

**Category**: schema tightening
**Structural or cosmetic**: cosmetic (enforcement layer, not root-cause)
**Blast radius**: `response_schemas.py` BLUEPRINT_SCHEMA
**Estimated cost**: low-moderate

**Description**:
Add `minLength` constraints on key BLUEPRINT_SCHEMA fields and make scene structure fields required.

**Current state**:
- `integrated_scenario` has no `minLength` in schema (only in Python prevalidator)
- Scene breakdown allows bare strings (backward compatibility)
- `relationship_changes[*].justification` is optional
- All optional fields have no content constraints

**Proposed change**:
1. Add `minLength: 2000` on `integrated_scenario`
2. Require scene objects to have `goal` and `summary` (not bare strings)
3. Make `relationship_changes[*].justification` required when `relationship_changes` is present

**Why cosmetic**:
- Schema enforcement catches malformed output but doesn't help the LLM generate better content
- A `minLength: 2000` schema constraint on `integrated_scenario` is already enforced by the Python prevalidator (`BLUEPRINT_MIN_CHARS = 800`)
- Schema tightening creates retry cost for marginal LLM failures without improving the prompt or feedback quality

**Pairs with**: Option C (density prevalidation adds the diagnostic the schema lacks)
**Should NOT lead**: Schema tightening without diagnostic feedback creates rejection without guidance

## 4. Option Comparison Matrix

| Option | Root-Cause? | Cost | Canary-Testable? | ROI | Recommended Wave |
|--------|-------------|------|-------------------|-----|------------------|
| **A. Self-Audit Prompt** | No (secondary) | Low | Yes | Medium | Wave 1 (quick win) |
| **B. Authority Re-Banding** | Yes (authority) | Moderate | Yes | High | Wave 1 |
| **C. Density Prevalidation** | Yes (validation) | Moderate | Yes | High | Wave 1 |
| **D. Upstream Specificity** | Yes (upstream) | High | Yes (separate) | High but risky | Wave 2 (separate) |
| **E. Scene-Level Feedback** | Yes (feedback) | Moderate-High | Yes | High | Wave 2 |
| **F. Schema Tightening** | No (cosmetic) | Low-Moderate | Yes | Low | Defer |

## 5. Recommended Wave 1 Bundle

If the merge owner wants **one small next wave** for blueprint clarity/density:

**Bundle: B + C + A** (Authority Re-Banding + Density Prevalidation + Self-Audit Prompt)

Rationale:
1. **B (authority re-banding)** fixes the root cause of authority mixing — the LLM gets explicit priority ordering and conflict resolution
2. **C (density prevalidation)** fills the largest validation blind spot — the quality gate can now see thin blueprints before Director invocation
3. **A (self-audit prompt)** is a low-cost amplifier that reinforces B and C at the generation step

This bundle:
- Stays within Stage 3 (no Stage 2 dependency)
- Requires no schema changes (clean rollback surface)
- Is canary-testable as a single unit (all three changes affect the same pipeline)
- Has bounded blast radius (prompt assembly + prevalidation + prompt template)

**What to defer**:
- D (upstream specificity) should be a separate Stage 2 wave
- E (scene-level feedback) should come after B+C validates the density signal
- F (schema tightening) is cosmetic and should not lead

## 6. Options That Pair Naturally vs. Must Stay Separated

**Natural pairs**:
- A + B + C: all Stage 3, all reinforce clarity/density from different angles
- D alone: Stage 2 change must be isolated for clean canary interpretation
- E after B+C: scene-level feedback is more valuable once the pipeline can already detect density issues

**Must stay separated**:
- D vs. (A+B+C): Stage 2 and Stage 3 changes have independent failure modes
- F vs. C: schema tightening without diagnostic feedback creates blind rejection
- E vs. D: both increase token cost; concurrent deployment obscures cost attribution

## 7. Confidence and Limits

- **Confidence in root-cause diagnosis**: 85%. The four concurrent factors are well-evidenced from code, but live canary data would strengthen the claim that authority mixing (not just upstream sparsity) is a material limiter.
- **Confidence in Option B+C+A as best bounded next wave**: 80%. The bundle addresses 3 of 4 root causes within Stage 3. The remaining uncertainty is whether authority re-banding alone materially reduces blueprint blur, or whether upstream specificity (Option D) is the true bottleneck.
- **Limit**: This ledger does not assess LLM behavioral response to prompt changes. Prompt-level interventions (A, B) require empirical validation via canary; their effectiveness is model-dependent.
- **Limit**: Density prevalidation (C) is bounded by what Python can detect without NLP. The proposed concrete-noun-density proxy is a heuristic, not a ground-truth measure.

---

Dominant limiter in this lane: `mixed` (authority mixing + validation blind spot are co-dominant; upstream specificity and self-audit are secondary amplifiers)
Best bounded improvement candidate in this lane: `B+C+A bundle (authority re-banding + density prevalidation + self-audit prompt)`
Should this lane alone trigger a new SSOT: `no` (merge owner should synthesize all 4 lanes first)
