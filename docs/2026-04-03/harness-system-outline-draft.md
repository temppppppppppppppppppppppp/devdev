# 하네스 체계도 구상 메모 v0.1

Date: 2026-04-03
Status: draft note
Scope: harness structure concept only
Execution Rule: 저장용 메모이며 아직 active SSOT나 실행 규칙으로 승격하지 않는다.

## 1. Purpose

글도비 작업 흐름을 하네스 단위로 더 단순하게 보기 위해,
상위 체계를 크게 두 갈래로 나누는 구상을 메모로 남긴다.

이 문서는 즉시 적용 문서가 아니라,
향후 구조 정리 시 기준 후보로 검토하기 위한 초안이다.

## 2. Proposed Top-Level Split

현재 공식으로 박아 둘 상위 흐름 문장은 아래다.

`리서치 -> 기획안 -> Stage 0 preprocess -> Phase 0 design -> TR 생성 -> BI 생성 -> 글도비 파이프라인`

### A. 재료 사이드 오더

재료를 모으고 정제하고 생산 준비를 하는 쪽을 묶는다.

예상 하위 흐름:

1. 리서치
2. 기획안
3. Stage 0 preprocess
4. Phase 0 design
5. TR 생성
6. BI 생성

의도:

- reference / few-shot / 실물 자료
- 작품 아이디어와 pitch 정리
- Stage 0 준비물 정리와 생산 진입 게이트
- `Phase 0 design` 작성
- `TR` 생성
- `BI` 생성

즉, 작품 생산 재료와 서사 산출물 준비 쪽을 한 묶음으로 보는 구조다.

### B. 시스템 오더

글도비 런타임과 실제 앱/파이프라인을 다루는 쪽을 묶는다.

예상 하위 흐름:

1. 글도비 파이프라인

의도:

- 코드베이스
- 런타임
- DB
- desktop/app 연결
- 테스트 및 회귀
- 시스템 제어 흐름

즉, 작품 재료 생산이 아니라 글도비 시스템 자체를 다루는 구조다.

## 3. Working Interpretation

이 구상은 현재의 복잡한 구조를 아래처럼 단순화해서 보자는 뜻이다.

- `재료 사이드 오더`
  - 리서치
  - 기획안
  - Stage 0 preprocess
  - Phase 0 design
  - TR 생성
  - BI 생성
- `시스템 오더`
  - 글도비 파이프라인

핵심은 폴더를 먼저 옮기는 것이 아니라,
하네스의 진입 분기 자체를 이 수준에서 먼저 단순화하는 것이다.

## 4. Current Constraint

- IDE 2가 `Phase 0` 관련 작업을 처리 중이므로 지금은 실행 금지
- 현재 메모는 naming / routing / harness top split 후보만 저장
- 기존 `AGENTS.md`의 system-track / narrative-pipeline 구분을 즉시 대체하지 않음

## 5. Future Use

나중에 이 메모를 실제 구조 정리에 사용할 경우에는 아래 순서로 검토한다.

1. 현재 narrative 관련 경로를 `재료 사이드 오더`로 재분류 가능한지 확인
2. 현재 system-track 경로를 `시스템 오더`로 일관되게 묶을 수 있는지 확인
3. 라우터와 하네스 read order를 이 2축 기준으로 다시 설계
4. 그 다음에만 문서/폴더 cutover 여부 판단

## 6. Conclusion

현재 저장하려는 핵심 문장은 아래다.

글도비 하네스 체계는 장기적으로 아래 상위 체인을 기준으로 정리한다.

`리서치 -> 기획안 -> Stage 0 preprocess -> Phase 0 design -> TR 생성 -> BI 생성 -> 글도비 파이프라인`

이를 하네스 체계로 나누면

- `재료 사이드 오더`
  - 리서치
  - 기획안
  - Stage 0 preprocess
  - Phase 0 design
  - TR 생성
  - BI 생성
- `시스템 오더`
  - 글도비 파이프라인

이런 식으로 상위 분기하겠다는 방향으로 정리한다.

## 7. 3-Pass Audit Note

Pass 1. Structure and scope
- 실행 문서가 아니라 체계 구상 메모로 범위 고정
- 상위 2분기와 예시 하위 흐름만 기록

Pass 2. Evidence and consistency
- 현재 workspace가 narrative/material 축과 system/pipeline 축으로 실제 분리되어 있다는 기존 조사 결과와 정합
- 즉시 적용이 아니라 future structure candidate임을 명시

Pass 3. Execution and readability
- 간단한 상위 구조 문장으로 읽히게 정리
- 현재는 저장만 하고 실행하지 않는다는 제한을 명시

Estimated Confidence: 96%
