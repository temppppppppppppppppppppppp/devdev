# 0_0 Stage2 Production-Consumption Global Bounded Survey

- date: 2026-04-02
- scope: Stage2 production authority + downstream consumption contract global bounded survey
- status: final
- confidence: 96%
- lineage:
  - `docs/2026-04-02/0_0-stage2-production-consumption-lane1-production-authority-draft.md`
  - `docs/2026-04-02/0_0-stage2-production-consumption-lane2-stage23-transform-drift-draft.md`
  - `docs/2026-04-02/0_0-stage2-production-consumption-lane3-stage24-consumption-draft.md`
  - `docs/2026-04-02/0_0-stage2-production-consumption-lane4-artifact-vertical-slice-draft.md`

## Answer First

Stage2는 `내용 부족`이 아니라 `authority packaging`이 약한 상태다. 핵심 truth와 mission은 충분히 생산하지만, 가장 중요한 권위가 구조화 필드보다 `tactical_doc` prose에 갇혀 있다. 그 결과 Stage3는 Stage2를 compiler처럼 단순 전달하지 못하고 재해석층이 되며, Stage4와 validator는 같은 Stage2 truth를 서로 다른 이름과 다른 강도로 소비한다.

따라서 현재 판정은 다음과 같다.

- Stage2 production verdict: `content-sufficient but schema-fragile`
- Stage2 consumption verdict: `consumer-diluted`
- first material drift point: `Stage3`
- long-term direction: `contract normalization first`, 그 다음 `Stage3 external stage -> compiler/substep candidate` 검토

## Hard Conclusions

1. Stage2는 핵심 narrative authority를 실제로 생산한다.
   - 특히 `tactical_doc`가 episode mission, tactical intent, scene drive의 실질 권위다.
   - `arc_no`, `ep_start`, `ep_end`, `state_constraints`, `joint_docs`, `state_changes`도 hard truth 축으로 기능한다.

2. Stage2의 가장 큰 문제는 생산 실패가 아니라 packaging failure다.
   - 구조화 필드인 `episode_details`, `constraint_summary`, `semantic_carryover`는 얇거나 비어 있거나 일관성이 약하다.
   - 가장 중요한 권위가 prose tactical doc 안에 남아 downstream에서 다시 해석된다.

3. 첫 실질 narrative drift는 Stage3에서 발생한다.
   - 대표적으로 `0_0 ep5`, `0_0 ep6`에서 Stage2에는 없는 물리 난입/활극/기관명 drift가 Stage3 blueprint에서 처음 등장한다.
   - 이 신호는 현재 조사에서 가장 강한 artifact truth다.

4. Stage2 truth는 downstream에서 소비되지만 authority strength가 일치하지 않는다.
   - 같은 `constraint_summary` 계열 truth가 Stage3 generation에선 advisory처럼 취급되고, Stage4에선 Tier-0 prohibition으로 강화된다.
   - 즉 동일 truth가 stage별로 hard/advisory strength inversion을 겪는다.

5. 현재 구조에서 Stage3는 독립 창작 단계라기보다 `re-interpretive translation layer` 비중이 크다.
   - compiler-like output band는 존재하지만, 핵심 content authority는 여전히 prose tactical_doc 재해석에 기대고 있다.
   - 장기적으로 Stage3는 외부 stage보다 compiler/substep 후보로 보는 근거가 충분하다.

## Medium-Confidence Conclusions

1. Stage2 자체는 immediate blocker가 아니다.
   - Stage2 content는 대표 slice 기준 충분히 specific하다.
   - 다만 schema/contract weakness가 누적 비용을 만든다.

2. Stage4 단독 문제로 보였던 일부 seam도 upstream contract drift의 결과일 가능성이 크다.
   - Stage4는 종종 Stage2 authority를 강하게 읽으려 하지만, 그 authority가 이미 Stage3에서 advisory/prose 형태로 약화된 뒤 들어온다.

3. `semantic_carryover`와 일부 structured carryover field는 dead-field 또는 low-signal field일 가능성이 높다.
   - 존재는 하지만 운영상 강한 truth owner로 기능하지 않는다.

4. `state_changes`는 hard truth owner가 아니라 discovery/roster 쪽 소비가 더 강하다.
   - 특히 downstream에서 entity discovery는 하지만 behavior/mission binding은 약하다.

## Open Questions

1. `episode_details`를 authority field로 키울지, 아니면 tactical_doc를 machine-readable packet으로 더 강하게 분해할지 어느 쪽이 cost-effective한가.
2. `beat_sequence`, `hybrid_composition` 같이 현재 드랍되는 Stage2 field를 살릴 가치가 있는가, 아니면 제거해야 하는가.
3. `semantic_carryover`는 복구할 field인가, 아니면 dead contract로 정리할 field인가.
4. Stage3를 외부 stage로 유지할 최소 고유 책임이 정확히 무엇인가.

## Production Truth

Stage2 production은 약하지 않다. 약한 것은 packaging이다.

- hard truth:
  - `arc_no`, `ep_start`, `ep_end`, `ep_count`, `volume_no`, `global_arc_no`
  - `state_constraints`
  - `joint_docs`
  - `state_changes`
- mission truth:
  - `tactical_doc`가 실질 canonical mission authority
  - `episode_details`는 존재하지만 얇다
- carryover truth:
  - `constraint_summary`
  - `beat_sequence`
- advisory/history:
  - `pacing_decision`
  - `status_shadow`
  - `hybrid_composition`
  - `arc_drive`

판정:

- content authority: 충분
- structured authority bridge: 약함
- dead/low-signal field: 존재
- prompt hierarchy: 선언적이지 machine-enforced가 아님

## Consumption Truth

Stage2 truth는 downstream에서 사라지지 않는다. 대신 이름과 강도가 바뀐다.

### Stage2 -> Stage3

- `tactical_doc`는 여전히 핵심이지만 prose `arc_focus`로 재서술된다.
- `BlueprintConstraintCompiler`는 분명한 constraint band를 만든다.
- 그러나 content mission은 여전히 LLM 재해석에 기대고 있다.
- `beat_sequence`, `hybrid_composition`는 사실상 boundary에서 드랍된다.
- `state_changes`는 compression/demotion을 겪는다.

### Stage2 -> Stage4 / Validator / Compiler

- Stage4는 `constraint_summary`를 더 강하게 읽는다.
- Stage4는 `tactical_doc`를 raw prose authority로 본다.
- validator는 일부 중요한 Stage2 concept에 대해 binding coverage가 충분하지 않다.
- `ChiefWriterContextBuilder`는 raw Stage2를 직접 읽지 않는다는 점에서 오히려 clean하다.

판정:

- Stage2 truth survival: 부분 성공
- authority preservation: 불완전
- consumer consistency: 약함

## Artifact Truth

대표 slice 기준으로 보면 first drift는 Stage3다.

### Slice A: 0_0 ep5

- Stage2 beat: 금융 PB 통화, WTI leverage decision, cerebral pressure
- Stage3 blueprint: 불량배/난입/물리 위협, 기관명 drift, 숫자/timeline drift
- 해석:
  - Stage2가 비어 있어서가 아니라 Stage3가 off-arc invention을 한 것

### Slice B: 0_0 ep6

- Stage2 beat: 내적 고민, 리스크 fixation 중심
- Stage3 blueprint: 기존 활극 subplot 연장, NPC 발명, detail invention
- 해석:
  - Stage3는 compiler가 아니라 narrative reinterpretation layer로 동작

### Slice C: 0_1 ep9 / ep13 / ep15

- upstream full chain은 부족하지만 Stage4-only quality contrast로는 유효
- 다만 이번 survey의 first-drift 판정 근거로는 0_0 ep5/6이 훨씬 강하다

## Contract Drift

가장 큰 drift는 아래 3개다.

1. `tactical_doc` authority trapped in prose
   - 가장 중요한 mission truth가 structured packet으로 승격되지 못해 downstream reinterpretation cost를 만든다.

2. `constraint_summary` strength inversion
   - Stage3 generation에선 advisory 성격이 강하고, Stage4에선 hard prohibition처럼 읽힌다.

3. dropped Stage2 fields
   - `beat_sequence`, `hybrid_composition`, 일부 carryover field가 경계에서 사실상 사라진다.

추가 drift:

- `state_changes` advisory demotion
- `episode_details` prose demotion
- dead `compile_to_prompt()` / formatter split
- `semantic_carryover` low-signal / dead-field화

## Long-Term Structure Direction

현재 구조를 `keep as-is`로 두는 건 권장되지 않는다.

우선순위는 이렇다.

1. `contract normalization`
   - `hard truth / mission / carryover / advisory` 4층 vocabulary를 공통화
   - Stage2 authority를 구조화 packet으로 더 강하게 승격
   - downstream consumer strength inversion 제거

2. `Stage3 role reduction`
   - Stage3의 고유 책임만 남기고 재해석층 역할을 줄인다
   - 최종적으로는 external stage라기보다 compiler/substep 후보로 검토 가능

3. `dead-field cleanup`
   - 살아 있지 않은 contract field는 복구할지 제거할지 결정

## Next Action

다음 액션은 `Stage2 contract normalization bounded wave`가 맞다.

구체적으로는:

- Stage2 canonical packet 재설계
- `tactical_doc` mission authority의 structured extraction 강화
- `constraint_summary` hard/advisory strength 통일
- `beat_sequence / hybrid_composition / semantic_carryover`의 keep-or-drop 판정

## 3-Pass Audit

- pass1: 4개 lane draft의 verdict와 scope를 하나의 answer-first 판정으로 정규화
- pass2: production truth / consumption truth / artifact truth / contract drift 4축 정렬 확인
- pass3: long-term direction과 next action이 evidence 범위를 넘지 않는지 제한 검토

최종 confidence는 96%다.
