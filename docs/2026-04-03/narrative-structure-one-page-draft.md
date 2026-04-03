# 리서치 · 기획안 · BI/TR 생성 구조 정리안 v0.1

Date: 2026-04-03
Status: draft note
Scope: narrative research / pitch / Stage 0 / Phase 0 / TR / BI structure only
Execution Rule: IDE 2가 `Phase 0` 관련 작업을 처리 중이므로 본 문서는 실행 지시가 아니라 구조 정리용 저장 메모로만 사용한다.

## 1. Purpose

현재 글도비의 서사 생산 경로는 `리서치`, `기획안`, `Stage 0/Phase 0`, `TR`, `BI`가 여러 폴더와 하네스로 분산되어 있어 진입 판단과 권위 경로가 직관적이지 않다.

이번 정리의 목적은 파일 이동이나 즉시 실행이 아니라, 아래 세 가지를 먼저 고정하는 데 있다.

- 현재 authoritative path가 어디인지
- 어떤 폴더가 mirror / scaffold / queue인지
- 나중에 어떤 순서로 정리해야 안전한지

## 2. Current Authority Snapshot

현재 확인된 기준상 가장 안전한 해석은 아래와 같다.

- `전처리_ssot` = Stage 0 운영 허브
- `docs/narrative-router` = family 진입 라우터
- `docs/실물기반 사각지대 테스트/few-shot-bank` = reference/few-shot authoritative source
- `treatments/`, `bible/` = live 산출물
- `narrative_ssot` = pilot용 scaffold, 아직 canonical 아님
- `docs/temp` = 실행 큐, 구조 SSOT가 아니라 운영 queue mirror

## 3. Main Problem

문제의 본질은 폴더 수보다도 `authority`, `mirror`, `scaffold`, `queue`가 동시에 살아 있어 경계가 흐려졌다는 점이다.

대표 중복 축은 아래와 같다.

- 기획안: `전처리_ssot/기획안` vs `전처리_ssot/docs/10_pitches`
- reference bank: `docs/실물기반 사각지대 테스트/few-shot-bank` vs `narrative_ssot/10_reference_bank`
- 하네스: `docs/narrative-router + family harness` vs `narrative_ssot/30_harness`
- 산출물 경로: live output은 `treatments/`, `bible/`인데 scaffold에도 동일 의미 경로가 준비돼 있음

## 4. Working Interpretation

현 시점 임시 해석은 아래로 둔다.

- 리서치 원본: `docs/실물기반 사각지대 테스트`
- 기획안 허브: `전처리_ssot/docs/10_pitches`
- legacy 기획안 묶음: `전처리_ssot/기획안`
- Stage 0 운영 허브: `전처리_ssot`
- family 라우팅 진입: `docs/narrative-router`
- live preprocess: `treatments/preprocess/{work_id}`
- live Phase 0/TR: `treatments`
- live BI: `bible`
- scaffold 후보: `narrative_ssot`
- 실행 대기열: `docs/temp`

## 5. Immediate Rules

- IDE 2의 `Phase 0` 작업이 끝나기 전까지 `Phase 0` 관련 경로는 수정하지 않는다.
- `treatments/`, `bible/`, `treatments/preprocess/{work_id}`는 즉시 이동하지 않는다.
- 먼저 각 경로에 `canonical / mirror / scaffold / queue / archive` 라벨을 붙인다.
- 실제 파일 이동보다 `read order`와 `authority boundary`를 먼저 고정한다.
- `narrative_ssot`는 cutover 전까지 scaffold로만 취급한다.

## 6. Target Direction

정리 방향은 한 폴더로 몰아넣는 것이 아니라 역할 분리를 명확히 하는 것이다.

- `research/reference`
- `pitch/intake`
- `preprocess/stage0`
- `phase0/tr/bi live outputs`
- `router/harness`
- `scaffold/migration`

즉, 최종적으로는 `자료`, `기획`, `전처리`, `생산`, `진입 하네스`, `이관 실험`이 분리되어 보여야 한다.

## 7. Next Safe Sequence

실제 정리는 아래 순서로만 착수한다.

1. IDE 2의 `Phase 0` 작업 종료 확인
2. 현재 active `work_id`와 live output 경로 재확인
3. 기획안 / reference / 하네스 중복 경로를 표로 분류
4. 단일 read-order 문서 초안 작성
5. 이후에만 mirror 정리 또는 cutover 검토

## 8. Conclusion

지금 당장 필요한 것은 폴더 이동이 아니라, `현재 권위 경로`, `mirror`, `실험 구조`를 한 장으로 고정하는 일이다.

따라서 현 단계의 방침은 아래로 둔다.

- `Phase 0` 축은 동결
- legacy authority는 유지
- `narrative_ssot`는 실험 scaffold로만 운용
- 구조 정리는 문서 / 라벨 / read order부터 시작
- 실제 cutover는 나중에 별도 판단

## 9. 3-Pass Audit Note

Pass 1. Structure and scope
- 1페이지 구조 정리 메모 형식으로 한정
- 실행 문서가 아니라 저장용 운영 노트로 범위 고정

Pass 2. Evidence and consistency
- `전처리_ssot`, `docs/narrative-router`, `docs/실물기반 사각지대 테스트`, `narrative_ssot`, `treatments`, `bible`, `docs/temp`를 직접 확인한 뒤 경로 반영
- `narrative_ssot`의 draft/scaffold 성격과 reference mirror 상태 반영

Pass 3. Execution and readability
- 즉시 실행 금지와 착수 조건을 명시
- 다음 행동을 `문서 정리 -> 분류표 -> read order 정리` 순서로 제한

Estimated Confidence: 96%
