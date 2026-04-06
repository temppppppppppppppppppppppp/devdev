# WorkGuard Generation Operating Rule

- Date: 2026-04-06
- Scope: narrative/material operating rule
- Status: active draft for team use
- Decision type: no-code operating policy

## 1. Decision

재료 사이드가 `work_guard`까지 책임지는 방향은 맞다.

하지만 운영 방식은 `TR/BI 페어 + work_guard를 마지막에 3개 동시 생성`이 아니다.

권장 운영은 아래다.

1. 같은 upstream truth에서 `TR`, `BI`, `work_guard`가 모두 파생된다
2. 그중 `work_guard`는 `TR/BI`와 동급 최종 산출물이 아니라 `runtime rule artifact`다
3. 따라서 `work_guard`는 `TR`보다 먼저 초안이 잡히고, `TR` 전에 freeze되는 것이 원칙이다

한 줄로 압축하면:

- `3개 동시 생성`보다 `1개 원천 -> 3개 파생`
- 그리고 `work_guard`는 그중 가장 먼저 굳는 runtime 규약이다

## 2. Why

현재 워크스페이스에서 `work_guard.yaml`은 실제 런타임 가드로 소비된다.

Evidence:

- [main_a.py](../../main_a.py#L1344)
- [work_guard.py](../../modules/core/genre_guards/work_guard.py#L610)

반면 `BI` 빌더는 기본적으로 `phase0 + draft -> BI` 계약으로 묶여 있다.

Evidence:

- [build_narrative_bi.py](../../scripts/build_narrative_bi.py#L17)
- [build_bi_from_phase0_and_tr.py](../../scripts/build_bi_from_phase0_and_tr.py#L17)
- [blockguide.py](../../modules/narrative_router/families/blockguide.py#L54)
- [wuxguide.py](../../modules/narrative_router/families/wuxguide.py#L34)

즉 구조적으로:

- `TR/BI`는 서사 산출물
- `work_guard`는 downstream 생성기가 참고할 작품 규약

레이어가 다르기 때문에, 같은 타이밍에 “최종물 3종 세트”처럼 다루는 건 부정확하다.

## 3. Current System Reality

### 현재 Stage 0/Stage0 계층에서의 위치

Stage 0 문서는 이미 `work_guard`를 선택적 출력으로 취급한다.

Evidence:

- [stage0.md](../../docs/stage_map/stage0.md#L33)
- [stage0.md](../../docs/stage_map/stage0.md#L64)
- [stage0.md](../../docs/stage_map/stage0.md#L86)
- [stage0/__init__.py](../../modules/core/stage0/__init__.py#L153)
- [stage0/__init__.py](../../modules/core/stage0/__init__.py#L182)

즉 시스템적으로도 `work_guard`는 원래 TR/BI 뒤에 덧붙는 부속물이 아니라, 앞단에서 준비할 수 있는 작품 규약 자산에 가깝다.

### 현재 narrative-router 계약에서의 위치

Planning readiness는 아직 preprocess 4-pack만 본다.

Evidence:

- [treatment-planning-harness.md](../../docs/blockguide/treatment-planning-harness.md#L19)
- [blockguide.py](../../modules/narrative_router/families/blockguide.py#L43)
- [wuxguide.py](../../modules/narrative_router/families/wuxguide.py#L23)

즉 현재 시스템은 `work_guard`를 아직 필수 readiness artifact로 강제하지 않는다.

이 말은 곧:

- 지금 당장 `TR/BI/work_guard 3종 동시 생성`을 시스템 계약처럼 취급하면 과장이다
- 먼저 운영 규칙으로 freeze timing을 정하고, 나중에 필요하면 계약 승격을 검토하는 게 맞다

## 4. Recommended Operating Sequence

권장 순서는 아래다.

1. `material_ssot`에서 철학/기획 truth를 잠근다
2. preprocess 4-pack을 잠근다
3. `phase0_design`을 잠근다
4. 그 truth를 바탕으로 `work_guard draft`를 만든다
5. `work_guard draft`를 manual audit 후 freeze한다
6. freeze된 `work_guard`를 기준으로 `TR`을 생성한다
7. freeze된 `work_guard + phase0 + TR`을 기준으로 `BI`를 생성한다

즉:

- `Phase0 -> work_guard freeze -> TR -> BI`

이 순서가 가장 자연스럽다.

## 5. Why Not Simultaneous Triple Generation

`TR/BI/work_guard 동시 생성`이 별로인 이유는 네 가지다.

### 5.1 `work_guard`는 생성기 입력에 더 가깝다

`TR`과 `BI`는 결과물이고, `work_guard`는 생성기의 작품 정체성 가드다.

같은 레이어처럼 다루면 역할이 흐려진다.

### 5.2 `work_guard`가 늦게 생기면 ROI가 떨어진다

우리가 조사한 가장 큰 distortion seam은 `Stage2 -> Stage3`다.

즉 `work_guard`는 늦게 붙일수록 효과가 줄어든다.

### 5.3 `BI`는 `work_guard`를 직접 계약 입력으로 받지 않는다

현재 builder CLI는 `phase0`, `draft`, `output`만 직접 입력으로 받는다.

Evidence:

- [build_narrative_bi.py](../../scripts/build_narrative_bi.py#L17)

그래서 지금 “3개 동시 생성”을 말해도 실질적으로는 저장 타이밍만 묶는 것이지, 계약 소비는 묶이지 않는다.

### 5.4 운영상 audit 기준이 달라진다

- `TR`은 블록 품질/연속성 audit 대상
- `BI`는 canonical view / HUD / bible contract audit 대상
- `work_guard`는 작품 정체성 drift 방지용 audit 대상

한 묶음으로 저장하면, 실패 원인이 섞여서 관리가 나빠진다.

## 6. Best Practical Model

가장 좋은 모델은 `동시 생성`이 아니라 `동시 파생`이다.

뜻은 이렇다.

- 같은 상위 truth에서 3개가 나온다
- 하지만 저장/승인/freeze 타이밍은 분리한다

권장 구분:

- `work_guard`
  - 작품 정체성 규약
  - earliest freeze
- `TR`
  - 서사 전개 설계
  - middle artifact
- `BI`
  - 세계/주인공/장기지표 canonicalization
  - later artifact

## 7. Team Rule

앞으로 팀 운영 규칙은 이렇게 잡는다.

### Rule 1

재료 사이드는 `TR/BI`만이 아니라 `work_guard`의 내용 책임도 가진다.

### Rule 2

`work_guard`는 `TR/BI`와 같은 “최종 산출물 3종 세트”가 아니다.

### Rule 3

`work_guard`는 가능하면 `Phase0` 직후, `TR` 전에 초안 작성과 freeze를 끝낸다.

### Rule 4

`TR`과 `BI`는 freeze된 `work_guard`를 역참조하는 구조로 본다.

### Rule 5

작품별로 truth가 크게 바뀌면 `TR/BI`를 고치기 전에 `work_guard`부터 다시 잠근다.

## 8. Optional Future Upgrade

나중에 시스템 계약으로 승격하고 싶다면, 그때는 아래 둘 중 하나를 고르면 된다.

### Option A

preprocess/Phase0 readiness에 `work_guard`를 필수 파일로 추가한다

장점:

- `TR` 진입 전에 작품 규약이 강제로 잠긴다

단점:

- narrative-router / validator / contract 수정이 필요하다

### Option B

material-side generator가 `Phase0 truth -> work_guard draft`를 자동 생성하게 한다

장점:

- operator 비용이 줄어든다

단점:

- 생성 자동화가 들어가면 품질 감사 규칙도 같이 필요하다

둘 다 미래 구현 옵션이지, 오늘 바로 동시 생성 규칙으로 밀어붙일 이유는 아니다.

## 9. Practical Recommendation

오늘 기준 추천은 이거다.

1. 재료 사이드는 `work_guard`까지 책임진다
2. 하지만 운영 문법은 `TR/BI pair + runtime guard`
3. `work_guard`는 `Phase0` 직후 따로 생성/감리/freeze
4. 그 다음 `TR`
5. 그 다음 `BI`

즉 실무 문장으로는:

- `앞으로는 TR/BI pair만 만든다가 아니라, work_guard draft까지 같이 설계한다`
- `다만 저장 순서는 work_guard -> TR -> BI로 본다`

## 10. 3-Pass Audit

- Pass 1: 현재 코드에서 `work_guard`가 실제로 어느 레이어에서 소비되는지 다시 확인함
- Pass 2: 현재 router/planning 계약이 아직 `work_guard`를 필수 readiness로 보지 않는 점을 반영함
- Pass 3: “동시 생성”과 “동시 파생”을 분리해 운영 문장이 오해 없도록 다듬음
- Confidence: 0.98
