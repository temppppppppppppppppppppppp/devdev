# 4개 프로젝트 1Arc 런 병합 수정 오더 3PASS 감리

> 작성일: 2026-03-13  
> 대상 SSOT: `docs/2026-03-13/four-project-1arc-merged-remediation-execution-ssot.md`

## Executive Summary

- 판정: `execution-ready`
- 최종 확신도: `95%`
- 핵심 결론:
  - 4P 조사 결과를 그대로 구현 대상으로 삼으면 범위가 과도하다.
  - 최근 closure 문서까지 반영하면 실제 남는 범위는 `proof-heavy`이며, code-hardening open item은 사실상 `03형 Stage 2 integrity debt` 1축뿐이다.
  - 따라서 SSOT가 historical debt와 open debt를 분리한 현재 구조가 맞다.

## Pass 1: 근거 병합 검증

다음 항목이 Opus 문서와 직접 근거에서 동시에 확인된다.

- `00/01/03`의 POV artifact drift
- `0w`의 Stage 4 continuity conflict 후 recovery
- `03`의 `data_missing`, `integrity_fail`
- 네 프로젝트 공통 TF-47 historical retry 흔적

다음 항목은 Opus 문서와 직접 근거를 다시 대조한 결과 실행 대상으로 남길 필요가 없다고 판정했다.

- artifact missing
- sink alignment drift
- mojibake
- PASS_WITH_FIX provenance 유실

이 분리는 타당하다. 직접 파일과 DB 근거가 있기 때문이다.

## Pass 2: 최신 코드 상태와의 충돌 검증

SSOT는 과거 런 evidence만 보지 않고, 아래 최신 closure 문서와도 충돌 검사를 수행했다.

- `viewpoint-primary-pov-external-insert-remediation-postfix-3pass-closure.md`
- `stage4-director-cw-log-informed-remediation-postfix-5pass-closure.md`
- `logging-hardening-moderate-followup-postfix-3pass-closure.md`

검증 결과:

- POV taxonomy 분리 부족을 새 코드 수정 범위로 다시 올리면 중복이다.
- Stage 4 provenance/logging 부족을 새 코드 수정 범위로 다시 올리면 중복이다.
- TF-47 자체 재수정도 현재 코드 상태와는 충돌한다. historical evidence일 뿐이다.

따라서 SSOT가 `proof-only`와 `code-hardening`을 구분한 현재 구조는 합리적이다.

## Pass 3: 범위 과대화 / 과소화 감리

### 과대화 여부

과대화 위험:

- historical TF-47을 다시 구현 대상으로 올리는 경우
- 이미 닫힌 POV/logging 축을 재개방하는 경우

SSOT는 이를 피하고 있다. 따라서 과대화는 통제됐다.

### 과소화 여부

과소화 위험:

- `03`의 Stage 2 integrity debt를 proof-only로 내려버리는 경우
- `0w`의 continuity conflict를 단순 관찰로만 끝내는 경우

SSOT는 이를 피하고 있다.

- `03`은 명시적 code-harden target으로 남겼고
- `0w`는 fresh runtime proof 대상으로 유지했다.

따라서 과소화도 통제됐다.

## 잔여 불확실성

- `03`형 debt가 현재 코드에서도 재현될지 여부는 fresh rerun 전까지는 100% 단정할 수 없다.
- `state_tracker 없음`이 benign early-arc skip인지 wiring gap인지도 fresh evidence가 더 필요하다.

하지만 이 불확실성은 SSOT의 구조적 문제라기보다, 실행 후 검증에서 닫혀야 할 항목이다.

## Confidence Ledger

- `70`: Opus 문서 + 직접 로그/DB 근거 병합 완료
- `+10`: retained/non-retained 분리 근거 확보
- `+5`: 최신 closure 문서와 충돌 여부 검증
- `+5`: proof-only vs code-hardening 범위 분리
- `+5`: 실행 순서의 ROI 정렬 확인
- `-5`: `03` 재현성과 `state_tracker` benign skip 여부는 runtime proof 전까지 잔여

최종 확신도: `95%`

## 최종 판정

- SSOT는 현재 상태로 `execution-ready`다.
- 범위를 더 넓히면 중복 수정 위험이 커지고, 더 좁히면 `03`형 debt를 놓친다.
- 따라서 이번 오더 문서는 `지금 시점 기준 가장 방어 가능한 실행 범위`로 본다.
