# 0_0 Stage3 Static Global Bounded Survey

- date: 2026-04-02
- scope: Stage3 generation authority, validator/binding, Stage3->Stage4 handoff, artifact drift taxonomy
- status: final
- confidence: 96%
- lineage:
  - `docs/2026-04-02/0_0-stage3-static-lane1-generation-authority-draft.md`
  - `docs/2026-04-02/0_0-stage3-static-lane2-validator-binding-draft.md`
  - `docs/2026-04-02/0_0-stage3-static-lane3-stage34-handoff-draft.md`
  - `docs/2026-04-02/0_0-stage3-static-lane4-artifact-drift-vertical-slice-draft.md`

## Answer First

`Stage3`는 `설계상 compiler-like`, `운영상 mixed`, `artifact truth 기준으로는 아직 first-drift layer`다.

더 정확히 말하면:

- generation hierarchy 자체는 생각보다 잘 설계돼 있다
- 하지만 validator/binding이 advisory-heavy라 enforcement가 약하다
- handoff는 architecturally clean하지만 semantic contract는 lossy하다
- 그래서 최종 artifact에서는 여전히 `Stage3`가 첫 실질 drift를 만든다

현재 판정은 다음과 같다.

- Stage3 generation verdict: `mixed (compiler-like design, reinterpretive core)`
- Stage3 validator/binding verdict: `advisory-heavy`
- Stage3 -> Stage4 handoff verdict: `handoff-clean but semantically lossy`
- artifact verdict: `first-drift-at-stage3`
- long-term direction: `tighten Stage3 contracts first`, 그 다음 `compiler/substep compression` 검토

## Hard Conclusions

1. Stage3 prompt hierarchy 자체는 무질서하지 않다.
   - `Constraint Stack > Arc Mission > Previous Truth And Archive > HUD` 우선순위가 명시돼 있다.
   - 내부 constraint stack도 `IMMUTABLE > HARD CONSTRAINT > EXPECTED CONTINUITY > ADVISORY`로 banding되어 있다.
   - 즉 Stage3의 설계 의도는 compiler-like에 가깝다.

2. Stage3의 실질 약점은 hierarchy 부재가 아니라 enforcement weakness다.
   - Python prevalidation은 넓게 존재하지만, 사실상 Director advisory로만 흐른다.
   - binding prevalidation은 `PASS -> PASS_WITH_FIX`까지만 올릴 수 있고 독립 REJECT를 만들지 못한다.
   - 가장 위험한 drift 중 일부는 binding scope 밖에 있다.

3. 첫 material drift는 여전히 Stage3 artifact에서 발생한다.
   - `0_0 ep5`, `0_0 ep6`에서 off-arc invention, invented character cascade, institution drift, timeline compression이 Stage3 blueprint에서 처음 보인다.
   - 이는 현재 조사에서 가장 강한 artifact truth다.

4. Stage3 -> Stage4 handoff는 clean하지만 lossy하다.
   - handoff 자체는 DB-serialized blueprint dict 하나로 clean하다.
   - 하지만 Stage2/Stage3 structured constraint truth가 Stage4까지 machine-readable contract로 가지 않고, Stage3 LLM이 만든 blueprint prose/JSON으로만 넘어간다.
   - Stage4는 Stage3 constraint hierarchy를 직접 볼 수 없다.

5. 현재 Stage3는 compiler가 아니다.
   - compiler-like 요소는 분명하지만, 핵심 scene design은 여전히 tactical_doc와 constraints를 narrative scene으로 재해석하는 LLM translation layer다.
   - 실 artifact 기준으로는 `mixed`보다 한 단계 더 나쁜 `reinterpretation-heavy` 신호도 남아 있다.

## Medium-Confidence Conclusions

1. Stage3의 가장 큰 실패 축은 `prompt hierarchy flattening` 하나로 설명되지 않는다.
   - hierarchy는 존재한다.
   - 더 큰 문제는 validator가 hard block이 아니고, Stage4 handoff가 semantic fidelity를 직접 검증할 수 없다는 점이다.

2. canary 개선 신호는 Stage3 구조가 완전히 틀리지 않았다는 증거다.
   - semantic-fidelity wave 이후 off-arc invention과 invented-character cascade는 크게 줄었다.
   - 특히 ep5/ep6 retry count 개선은 의미 있다.
   - 다만 timeline과 institution identity drift는 아직 잔존한다.

3. Stage3 cold-start weakness가 있다.
   - main artifact 기준 최악의 drift는 arc 초입인 ep5/ep6에 집중된다.
   - ep7~9는 상대적으로 안정적이다.

4. Stage3를 바로 없애기보다 contract를 강화해야 한다.
   - 현 상태에서 Stage3를 그냥 접으면 unresolved translation debt가 다른 stage로 이동할 가능성이 크다.
   - 먼저 contract normalization과 enforcement strengthening이 필요하다.

## Open Questions

1. `arc_compliance`, `fact_lock_location`, `fact_lock_provenance`, `capital_state` 같은 high-severity category를 binding scope에 올릴지 여부
2. Stage3의 timeline binding을 prose가 아니라 machine-enforced packet으로 더 끌어올릴 수 있는지 여부
3. institution/entity lock을 Stage3 generation 단계에서 더 강하게 거는 방식이 가능한지 여부
4. context caching이 실제로 priority banding 인지를 약화시키는지 여부

## Generation Truth

Stage3 generation은 명시적 hierarchy를 가진다.

- top priority:
  - protagonist lock
  - genre / anti-HUD / anti-recap guard
  - immutable constraints
- then:
  - hard constraints (`must_focus`, `stop_line`, `arc_constraint_summary`)
  - arc mission / `arc_focus`
  - strategy directive
  - expected continuity
  - previous truth / archive
  - advisory / hud

판정:

- hierarchy design: 강함
- mission truth survival: 부분 성공
- reinterpretive pressure: 여전히 높음

핵심 문제:

- `tactical_doc`는 일부 verbatim extraction이 되지만
- 결국 Stage3는 그것을 `scene_breakdown + integrated_scenario`로 다시 창작/번역한다
- `beat_sequence`, `hybrid_composition`, 일부 Stage2 truth는 직접적 pass-through가 아니라 재결정 대상이 된다

## Validator Truth

validator와 binding은 coverage는 넓지만 authority는 약하다.

- 14개 collector가 다양한 seam을 잡는다
- 그러나 대부분은 Director에 advisory 형태로 전달된다
- binding category도 독립적인 hard reject가 아니라 `PASS_WITH_FIX` promotion 위주다
- binding scope에 없는 high-severity seam이 남아 있다

판정:

- detection breadth: 넓음
- enforcement strength: 약함
- dominant issue: `binding scope gap + advisory-only resolution`

## Handoff Truth

Stage3 -> Stage4 handoff는 clean하지만 semantic guarantee는 약하다.

- clean:
  - DB persistence boundary
  - no shared mutable state
  - no protocol coupling
- weak:
  - Stage4는 Stage3 constraint hierarchy를 직접 받지 않음
  - Stage4는 blueprint dict의 prose/scene structure를 신뢰하고 증폭한다
  - 따라서 Stage3 compilation failure가 plausible blueprint로 남으면 Stage4가 그 omission을 이어받는다

판정:

- transport cleanliness: 좋음
- semantic fidelity guarantee: 약함

## Artifact Truth

대표 slice 기준 주요 drift taxonomy는 이렇다.

### Slice A: 0_0 ep5

- Stage2 truth: 금융 PB 상대로 leverage 결단, cerebral pressure
- Stage3 drift:
  - 불량배/물리 위협 invention
  - institution drift
  - timeline jump

### Slice B: 0_0 ep6

- Stage2 truth: 내적 고민, 리스크 fixation
- Stage3 drift:
  - invented crime subplot continuation
  - invented characters
  - timeline and identity instability

### Slice C: 0_0 ep7-9

- main artifacts에서는 이미 오염 cascade 흔적이 이어진다
- canary artifacts에서는 많이 깨끗해졌지만 timeline / institution drift는 잔존한다

판정:

- dominant historical drift:
  1. off-arc invention
  2. invented character cascade
  3. institution identity instability
  4. timeline compression / reversal
  5. numeric/price drift

## Contract Drift

가장 큰 Stage3 contract drift는 아래 4개다.

1. `constraint hierarchy exists but does not survive as enforceable contract`
   - 설계는 강하지만 post-generation enforcement와 Stage4 handoff가 약하다.

2. `binding scope gap`
   - high-severity seam 일부가 binding 밖에 있어 advisory-only로 남는다.

3. `structured constraint -> prose blueprint translation loss`
   - Stage3는 compiler처럼 보이지만 실제론 structured truth를 prose blueprint로 번역한다.

4. `handoff-clean but semantic-lossy`
   - Stage4는 blueprint dict를 깨끗하게 받지만, 원래 Stage2/Stage3 hard hierarchy는 잃은 채 받는다.

## Long-Term Structure Direction

현재 evidence는 `Stage3 keep as-is`를 지지하지 않는다.

우선순위는 이렇다.

1. `tighten Stage3 contracts`
   - binding scope 강화
   - timeline/entity/institution fidelity 강화
   - Stage4로 넘기는 semantic contract subtype 보강

2. `reduce reinterpretive freedom where it causes repeat drift`
   - 특히 arc cold-start 구간에서 off-arc invention을 더 세게 막아야 한다

3. `then evaluate Stage3 compiler/substep compression`
   - 지금도 설계는 compiler 쪽에 가깝다
   - 다만 enforcement와 semantic guarantee가 충분히 올라온 뒤에야 외부 stage 축소를 판단할 수 있다

## Next Action

다음 액션은 `Stage3 contract-enforcement static follow-up` 또는 그에 준하는 bounded execution SSOT다.

가장 우선되는 seam:

- binding scope gap
- timeline/entity lock strengthening
- Stage3 -> Stage4 semantic contract preservation

## 3-Pass Audit

- pass1: 4개 lane verdict를 generation / validator / handoff / artifact 축으로 정렬
- pass2: hierarchy 강점과 artifact drift 약점을 동시에 유지해 과소/과대평가를 제거
- pass3: long-term direction을 `Stage3 즉시 삭제`가 아니라 evidence-bounded contract tightening으로 제한

최종 confidence는 96%다.
