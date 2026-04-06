# WorkGuard Global Contract Promotion Decision

- Date: 2026-04-06
- Status: approved operating decision
- Scope: global governance wording only
- Code impact: none

## 1. Decision

`work_guard`를 전역 계약으로 승격할 수 있다.

단, 승격 방식은 아래여야 한다.

- `work_guard`를 `runtime optional, material-side standard`로 정의한다
- 전역 문구로는 `global material-side standard companion artifact`로 부른다
- 즉 파이프라인 코드와 stage detection은 그대로 둔다
- 대신 재료 사이드 표준 산출물로는 `Phase 0` 뒤, `TR` 전에 `work_guard draft/freeze`를 정식 운영 문법으로 올린다

한 줄로 압축하면:

- `optional consumer`
- `standard producer`

## 2. Why This Is The Right Split

현재 시스템 현실은 둘로 갈라져 있다.

### 2.1 Runtime side

- 런타임은 `{project}/config/work_guard.yaml`이 있으면 사용하고, 없으면 baseline으로 진행한다

Evidence:

- [main_a.py](../../main_a.py#L1344)
- [work_guards/README.md](../../work_guards/README.md#L7)

### 2.2 Material-side side

- `work_guard`는 이미 `20_pitch` 철학을 downstream rule로 번역하는 canonical bridge를 가지고 있다
- `WG-V1 / WG-V2 / WG-V3` operator pack도 준비됐다

Evidence:

- [work-guard-translation-map.md](../../material_ssot/20_pitch/work-guard-translation-map.md)
- [work-guard-validator-checklist-spec.md](./work-guard-validator-checklist-spec.md)
- [wg-v2-freeze-checklist.md](./wg-v2-freeze-checklist.md)
- [wg-v3-drift-audit-card.md](./wg-v3-drift-audit-card.md)

즉 consumer는 optional인데, producer는 이미 표준화할 준비가 됐다.

## 3. What Should Become Global Contract

전역 계약으로 올릴 문장은 아래가 맞다.

### 3.1 Root stage chain

루트 파이프라인 표기는 유지한다.

- `리서치 -> 기획안 -> Stage 0 preprocess -> Phase 0 design -> TR 생성 -> BI 생성 -> 글도비 파이프라인`

이건 stage-axis 체인이다.

### 3.2 New companion contract

별도 companion contract를 추가한다.

- `work_guard`는 material-side의 정식 companion artifact다
- 표준 재료 사이드 흐름에서는 `Phase 0 design` 뒤, `TR` 전 `work_guard draft/freeze`를 수행한다
- 권장 운영 순서는 `Phase 0 design -> WG-V1 -> WG-V2 PASS -> work_guard freeze -> TR -> WG-V3 -> BI`

### 3.3 Optionality clause

반드시 함께 적어야 하는 문장:

- 현재 stage detection은 `work_guard` 존재 여부로 바뀌지 않는다
- 현재 runtime/pipeline은 `work_guard`가 없어도 baseline으로 진행 가능하다
- 즉 이 승격은 `생산 표준 승격`이지 `런타임 강제화`가 아니다

## 4. Why Not Make It A Hard Stage Today

지금 당장 `work_guard`를 hard stage로 올리면 아래가 필요하다.

- router 수정
- validator 수정
- stage detection 수정
- readiness contract 수정

현재 사용자 의도는 여기가 아니다.

사용자 의도는:

- 재료 사이드에서 정식으로 만든다
- 하지만 파이프라인 코드는 건드리지 않는다

그래서 hard-stage 승격이 아니라 `global companion contract` 승격이 맞다.

## 5. Recommended AGENTS Wording

AGENTS에는 아래 의미가 들어가면 충분하다.

1. 루트 `Pipeline Order`는 유지
2. 별도 `WorkGuard companion contract`를 추가
3. narrative execution rules에 pre-`TR` freeze 원칙을 짧게 명시
4. stage detection / runtime optionality는 unchanged라고 못박기

## 6. Operational Consequence

이 결정을 적용하면 아래가 가능해진다.

- 재료 사이드에서는 `work_guard`를 안 만들면 계약 미달로 본다
- 하지만 legacy 프로젝트나 baseline runtime은 즉시 깨지지 않는다
- `TR -> work_guard -> BI` 같은 뒤늦은 부속물 취급도 막을 수 있다
- 이후 원하면 별도 wave에서 hard-stage 승격을 검토할 수 있다

## 7. Final Recommendation

오늘 기준 최종 추천은 이거다.

- `work_guard`를 전역 `material-side standard companion artifact`로 승격한다
- AGENTS에 그 문장을 올린다
- stage detection과 pipeline code는 그대로 둔다
- hard-stage 승격은 미래 옵션으로 남긴다
