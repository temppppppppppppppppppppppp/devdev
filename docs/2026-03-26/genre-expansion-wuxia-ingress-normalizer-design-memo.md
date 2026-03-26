# 무협 장르 확장 Ingress Normalizer 설계 메모

Date: 2026-03-26
Status: final
Type: bounded system-track design memo

## 목적

- 무협 장르 확장 문제를 어떤 사고 틀로 다뤄야 하는지 고정한다.
- 현재 문제의 본체가 하네스 문제인지, 계약 문제인지, 구현 순서 문제인지 분리한다.
- 바로 패치로 들어가기 전에, 이후 execution SSOT가 따라야 할 방향과 단계 순서를 고정한다.

## 범위

- `BI/TR -> main_a.py -> Stage 2` 런타임 ingress 계약
- 내부 runtime consumer contract의 최소 표준
- 무협 장르 확장을 위한 단계별 수정 순서

## 범위 밖

- 코드 수정
- Stage 3/4 품질 튜닝
- 무협 전투씬 readiness 자체의 재조사
- 장르별 raw schema를 Stage 2/3/4가 직접 다중지원하도록 넓히는 설계

## Commit State

- Baseline Commit: `a8034b1efdbe01a49effabf92cc9f736ebbca991`
- Baseline Dirty Summary: `clean`
- Temp Queue State: `empty` (`docs/temp/queue-state.json`, `active_item_count: 0`)

## 근거 문서

- `docs/2026-03-26/genre-expansion-wuxia-consumer-contract-context.md`

보조 spot-check:

- `modules/core/response_schemas.py:827-828`
- `modules/core/stage0_handoff.py:20-24`
- `modules/core/stage0_handoff.py:85-163`
- `modules/core/project_manager.py:842-845`
- `modules/core/stage01_helpers.py:224-229`
- `modules/core/stage01_helpers.py:307-313`

## 핵심 진단

현재 무협 장르 확장 문제의 본체는 다음과 같다.

`무협이 Stage 3/4에서 본질적으로 안 되는 것이 아니라, raw BI/TR가 현재 runtime ingress consumer contract에 맞지 않는다.`

즉 문제의 성격은 다음 순서로 읽는 것이 맞다.

1. 하네스가 일부 mismatch를 드러낸다
2. 그러나 본체는 하네스가 아니라 ingress contract mismatch다
3. downstream을 장르별 raw schema 다중지원으로 넓히는 것은 우아하지 않다

## 질문 1. 이게 하네스 문제인가

`부분적으로만 예`, `본질적으로는 계약 문제`다.

이유:

- `validate_treatment_structure()`는 treatment가 list가 아니면 바로 reject한다. `modules/core/response_schemas.py:827-828`
- `build_plot_roadmap_from_treatment()`는 dict일 때 `treatments`만 풀고 `blocks`는 풀지 않는다. `modules/core/stage0_handoff.py:20-24`
- `force_sync_v25_dna()`는 treatment_data를 list처럼 직접 순회한다. `modules/core/project_manager.py:842-845`

즉 하네스와 ingress helper가 현재 internal contract를 엄격히 가정하고 있고, raw wuxia pair는 그 계약에 그대로는 들어오지 못한다.

따라서 정확한 표현은:

- `하네스가 문제를 만든다`보다
- `하네스가 좁은 runtime contract를 드러낸다`

## 질문 2. 시스템적으로 어떻게 우아하게 고칠 것인가

가장 우아한 해법은 다음 한 줄로 정리된다.

`raw family-native BI/TR는 source truth로 유지하고, ingress normalizer 하나로 내부 runtime contract로 변환한다.`

### 권장 구조

1. Source truth
- raw `BI`
- raw `TR`

2. Adapter layer
- 단일 `ingress normalizer`

3. Canonical runtime contract
- ingress-normalized treatment block list
- Stage 2-ready `plot_roadmap`
- minimally compatible `protagonist_config`

4. Downstream
- Stage 2/3/4는 기존 consumer contract를 유지

### 피해야 할 방향

- Stage 2가 투자물 schema, 무협 schema, 기업물 schema를 직접 다 이해하게 만드는 것
- Stage 3/4 prompt가 raw family schema를 직접 여러 개 소비하게 만드는 것
- 하위 단계에서 장르별 예외를 누적하는 것

이 방향은 blast radius가 너무 크고, `golden canaria` 같은 기존 control을 오염시킬 가능성이 높다.

## 질문 3. 어떤 단계로 수정할 것인가

수정 순서는 아래처럼 고정하는 것이 맞다.

### 단계 1. Consumer contract 명문화

먼저 고정할 것은 implementation이 아니라 contract다.

명시해야 할 내부 표준:

- treatment 입력은 최종적으로 `list[block]`여야 한다
- 각 block은 최소 `block_no`를 가져야 한다
- Stage 2는 `plot_roadmap`만 본다
- `protagonist_config`는 좁은 runtime subset을 보장해야 한다

이 단계의 목표는:

- downstream이 무엇을 기대하는지 문서로 못 박는 것
- 무협 확장을 downstream 다중지원 문제로 착각하지 않게 하는 것

### 단계 2. Ingress normalizer 도입

다음 단계에서만 코드 변경을 연다.

정규화 책임:

- `list`
- `dict.blocks`
- `dict.treatments`

를 모두 받아 하나의 treatment block list로 정규화한다.

동시에:

- `block -> block_no` 매핑
- TR 기반 `plot_roadmap` 재구성
- blank-safe universal subset 보장

을 수행한다.

핵심 원칙:

- 정규화는 ingress에서 한 번만
- Stage 2/3/4는 raw family schema를 직접 보지 않음

### 단계 3. protagonist_config overwrite 제거

현재는 `_save_phase0_protagonist_config()`가 기존 config를 overwrite한다. `modules/core/stage01_helpers.py:307-313`

무협 확장에서는 이 overwrite가 가족 고유 설정을 지우는 부작용을 만들 수 있다.

따라서 이후 execution SSOT에서는:

- overwrite가 아니라 merge
- runtime required subset은 보장
- family-native 필드는 보존

을 원칙으로 둬야 한다.

### 단계 4. Stage 2 readiness는 정규화 결과만 기준으로 유지

`check_plot_roadmap_ready()` 자체를 장르별 raw 필드 다중지원으로 넓히는 것은 2차 선택지다.

1차 목표는:

- Stage 2 consumer가 이해하는 payload를 ingress에서 최대한 canonical shape로 승격시키는 것

즉 우선순위는:

- Stage 2 완화
- 보다 ingress 정규화

다.

### 단계 5. Canary split 고정

패치 이후 검증 축은 두 개로 나누는 것이 맞다.

- `golden canaria`
  - canonical runtime contract canary
- `wuxia_heavenly_physician`
  - ingress-adapter canary

이렇게 해야:

- 기존 baseline 오염 여부
- 무협 ingress adapter 성공 여부

를 분리해서 볼 수 있다.

### 단계 6. 그 다음에만 payload 확장 여부 판단

만약 ingress normalizer 이후에도 무협이 Stage 2 readiness에서 막히면, 그때 좁게 재판정한다.

그때 검토할 후보:

- `martial_ext`
- `realm_before`
- `realm_after`
- `martial_event`

하지만 이것은 ingress normalizer 이후의 2차 단계이며, 초기 wave 범위에 넣지 않는 것이 맞다.

## 실행 원칙

이 설계 메모 이후의 실행 원칙은 다음과 같다.

1. 문서 먼저
- 이 메모를 기준으로 implementation 범위를 고정한다

2. 그 다음 execution SSOT
- ingress normalizer bounded wave만 연다

3. 구현 범위 제한
- ingress / Stage 0 handoff / Stage 2 readiness alignment까지만

4. control 보호
- `golden canaria` 경로를 깨지 않는 것이 1급 acceptance criteria다

## 바로 다음 문서

이 메모 다음에는 추가 survey보다 `execution SSOT`가 맞다.

예상 tranche는 다음처럼 자르는 것이 적절하다.

1. TR shape normalization
2. `plot_roadmap` rebuild normalization
3. `protagonist_config` merge-safe save
4. Stage 2 readiness alignment
5. bounded regression tests

## 단일 요약

무협 장르 확장의 첫 문제는 Stage 3/4 품질이 아니라 `raw BI/TR를 현재 runtime internal contract로 어떻게 안전하게 승격시키느냐`다.

따라서 가장 우아한 방향은:

`raw BI/TR는 그대로 두고, ingress normalizer 하나로 내부 표준 계약으로 변환한 뒤, downstream은 그대로 유지한다`

이다.

---

## 3-Pass Audit Notes

- Pass 1: 문제를 하네스 문제, 계약 문제, 수정 순서 문제로 분리해 구조를 고정했다
- Pass 2: consumer-contract memo와 실제 ingress 코드 spot-check를 대조해 주장 범위를 제한했다
- Pass 3: survey 재반복이 아니라 바로 execution SSOT로 이어질 수 있게 단계 순서를 명시했다
- Confidence: 0.97
