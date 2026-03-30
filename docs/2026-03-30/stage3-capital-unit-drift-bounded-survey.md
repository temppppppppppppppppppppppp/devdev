# Stage 3 Capital Unit Drift Bounded Survey

Date: 2026-03-30
Status: final
Confidence: 96%
Scope: Stage 3 investment-genre blueprint financial/currency unit drift
Project: `0_1`
Canonical Focus: prevent recurrence of the EP17 financial-unit defect family

## 1. Why This Survey Exists

`EP17` and `EP20` live artifacts in the current workspace are already manually repaired.
This survey is therefore not about proving a still-broken live artifact.

It is about two narrower questions:

1. Did a real Stage 3 family exist where investment-capital amounts drifted into the wrong unit system?
2. If yes, where is the lowest-risk code seam that can prevent the family from passing again?

## 2. Authority And Evidence

### Live workspace truth

- `projects/0_1/plans/blueprints/blueprint_0017.txt`
  - currently uses `5억 원` additional margin phrasing
- `projects/0_1/logs/artifacts/stage3/ep_0017/attempt_03/final_blueprint__emotion_focused.json`
  - currently uses `WTI 익절로 확보한 가용 현금 중 5억 원`
- `projects/0_1/plans/blueprints/blueprint_0020.txt`
  - currently uses `한 달이 지난 2006년 9월 초`
- `projects/0_1/logs/artifacts/stage3/ep_0020/attempt_01/final_blueprint__action_focused.json`
  - currently uses `2006년 9월 초 오전`

### Historical defect evidence

- `docs/2026-03-30/0_1-stage3-blueprint-ep16-20-integrity-bounded-survey.md`
  - records the pre-repair EP17 claim as:
    - `"3,500만 달러" 금융 단위 오류`
  - records the pre-repair EP20 claim as:
    - `timeline "8월 9일" vs Arc 5 "9월"`

### Code-path evidence

- `modules/domain/agents/blueprint_constraint_compiler.py`
  - builds `capital_continuity_packet`
  - surfaces it into prompt text via `[CAPITAL-LOCK]`
- `modules/domain/agents/unified_blueprint_validator.py`
  - has capital continuity drift checks
  - but those checks focus on already-deployed capital reappearing as available
  - no explicit invariant exists for KRW-authoritative arc state drifting into USD-denominated deployment amounts

## 3. Observed Facts

### 3.1 The generator already receives capital continuity hints

`blueprint_constraint_compiler.py` facts:

- line 112 builds `capital_continuity_packet`
- line 133 stores it in `constraint_block`
- lines 179-188 emit a `[CAPITAL-LOCK]` section into the Stage 3 prompt

Operational meaning:

- the LLM is not blind to prior capital state
- this family is not caused by missing prompt exposure alone

### 3.2 The current validator capital checks are aimed at a different family

`unified_blueprint_validator.py` facts:

- line 973 calls `_collect_capital_state_drift_issues()`
- line 1176 reads `constraint_block["capital_continuity_packet"]`
- lines 1186-1204 detect contradiction patterns such as:
  - still available capital after already committed deployment
  - freshly deploy / full deploy contradictions
- lines 1206-1246 detect `phantom_capital`
  - deployed amount reappearing as available/held capital

Operational meaning:

- existing capital validation is continuity-oriented
- it does not explicitly compare capital unit regime
- it does not reject a case where authoritative packet is KRW-dominant but blueprint injects USD-denominated deployment amounts

### 3.3 The current binding contract does not cover capital unit drift

`unified_blueprint_validator.py` facts:

- line 52 binds only:
  - `scene_completeness`
  - `arc_timeline`
- lines 155-198 coerce plain `PASS` to `PASS_WITH_FIX` only for those categories

Operational meaning:

- even if a money-unit mismatch were emitted as a generic warning today, it would stay advisory unless Director independently downgraded the verdict

## 4. Root Cause Chain

1. Stage 3 already receives prior capital state via `capital_continuity_packet`.
2. Existing Python prevalidation looks for `capital_state` / `phantom_capital`, which are about continuity and redeployment state.
3. No validator invariant checks whether capital deployment amounts in the blueprint stay in the same authoritative unit regime as the prior arc/state packet.
4. No binding verdict contract exists for a capital-unit mismatch family.
5. Result: a KRW-authoritative investment arc can still pass after the generator invents a USD-denominated deployment amount, as long as narrative quality stays acceptable.

## 5. Defect Family Definition

This survey narrows the target family to:

`capital_unit_drift`

Definition:

- investment-genre Stage 3 blueprint
- authoritative capital packet is clearly KRW-dominant
- blueprint introduces a USD-denominated amount in capital/deployment context
- example contexts:
  - `추가 증거금`
  - `투입`
  - `가용 현금`
  - `총자산`
  - `유동성`
  - `예치`
- non-target examples:
  - commodity price quotes like `700달러`
  - macro references to `달러 유동성`
  - generic historical market price narration

## 6. Lowest-Risk Seam

Lowest-risk seam remains a single production file:

- `modules/domain/agents/unified_blueprint_validator.py`

Why:

- the prompt already contains capital-lock context
- the missing contract is validation, not data plumbing
- the current Stage 3 binding pattern already exists and can be extended narrowly
- no DB or runtime orchestration change is required

Recommended implementation shape:

1. add a new collector for capital-unit mismatch in the validator
2. classify it as a new category such as `capital_unit`
3. add `capital_unit` to the existing binding set
4. coerce plain `PASS` to `PASS_WITH_FIX` for `MAJOR/CRITICAL` capital-unit findings

## 7. Deferred Families

These remain outside this tranche:

- `scene content` empty-string pattern in EP18/19
- relationship `from_state` regression in EP19

Reason:

- different semantic families
- higher ambiguity
- not needed to close the capital-unit recurrence hole

## 8. Closure Target

This tranche is complete only if:

1. KRW-dominant capital packet + USD deployment amount produces a `MAJOR` issue
2. that issue is categorized into a binding family
3. single-candidate `PASS` becomes `PASS_WITH_FIX`
4. compare-path `PASS` becomes `PASS_WITH_FIX`
5. commodity price mentions such as `700달러` do not false-positive

## 9. 3-Pass Audit

### Pass 1 - Fact verification

- confirmed `capital_continuity_packet` build/store/prompt emission paths
- confirmed validator capital drift path and current binding set
- confirmed current EP17/EP20 live artifacts are already repaired
- confirmed historical defect claim persists in the canonical EP16-20 survey doc

### Pass 2 - Logic completeness

- verified that prompt exposure exists, so generator-only blame is insufficient
- verified the live blind spot is specifically unit-regime mismatch, not generic capital continuity
- verified the existing binding contract can absorb one more narrow category without architecture change

### Pass 3 - Side effects / omissions

- narrowed this tranche away from `scene content` and relationship semantics
- kept scope to validator-only hardening plus binding extension
- avoided a broad `quality_risk => reject` policy change

Final judgment:

- survey sufficient for execution
- no broader survey is required before implementation
