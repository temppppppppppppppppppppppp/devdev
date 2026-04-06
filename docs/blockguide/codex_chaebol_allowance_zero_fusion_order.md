# Codex: `chaebol_allowance_zero` 실패본 vs 재시도본 Fusion 오더

> 인코딩: **UTF-8 only**
> 작성일: 2026-03-11
> 목적: Codex/Opus 비교 문서와 상호 코멘트 결과를 한 장의 최종 합의 문서로 통합하기 위한 실행 오더
> 범위: 비교와 판정만 수행한다. JSON 재생성, 하네스 본문 패치, BI 재빌드는 이번 오더 범위 밖이다.

---

## 0. 정본 잠금

먼저 아래 경로를 정본으로 잠근다.

| 역할 | 정본 경로 | 비고 |
| ---- | --------- | ---- |
| 실패 TR | `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json` | 실패 현행 복사본 |
| 개선 TR | `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json` | 현재 골든 TR |
| 실패 BI | `bible/02_bi_chaebol_allowance_zero.json` | 실패 BI |
| 개선 BI | `bible/02_bi_chaebol_allowance_zero.json` | 재시도 BI |
| 기획 SSOT | `docs/2026-03-10/opus_재벌3세인데용돈이0원.md` | 공통 기획 축 |
| Phase 0 | `treatments/chaebol_allowance_zero_phase0_design.json` | 공통 설계 축 |
| 비교 기준 오더(D2) | `docs/blockguide/codex_chaebol_allowance_zero_failed_vs_retry_comparison_order.md` | 현재 기준 문서 |
| 상호 코멘트 결과 | `docs/blockguide/codex_chaebol_allowance_zero_mutual_comment_result.md` | BLOCKER/MAJOR 우선 해소 |

정리:

- `docs/2026-03-11/codex_chaebol_allowance_zero_failed_vs_retry_comparison_order.md`는 보관본으로만 취급한다.
- 현재 비교 기준의 정본은 `docs/blockguide/` 아래 D2다.

---

## 1. 입력 문서 우선순위

최종 통합 시 입력 우선순위는 아래와 같다.

1. 원본 JSON 직접 재검증 결과
2. `docs/blockguide/codex_chaebol_allowance_zero_mutual_comment_result.md`
3. `docs/2026-03-11/codex_chaebol_allowance_zero_failed_vs_retry_comparison.md`
4. `docs/2026-03-11/opus_chaebol_allowance_zero_failed_vs_retry_comparison.md`가 있으면 추가 반영
5. D2 오더 문서

규칙:

- 문서 간 충돌이 나면 **원본 JSON**이 최우선이다.
- 상호 코멘트의 `BLOCKER`와 `MAJOR`는 fusion 전에 반드시 반영 또는 기각 판정을 적는다.
- `R31` 규칙 자체가 과잉인지 여부는 비교 결론과 분리해서 다룬다.

---

## 2. Fusion 목표

최종 통합 문서는 아래 3가지를 동시에 달성해야 한다.

1. `실패본 대비 재시도본이 실제로 더 좋은 TR/BI인가`에 대한 결론 확정
2. 기존 비교 문서가 잘못 참조한 파일, 구버전 수치, 아크 오기재를 모두 정정
3. `R31 true-fail` 문제를 비교 결론과 분리해, 하네스 규칙 재조정 이슈로 따로 고정

핵심 원칙:

- `비교 승패`와 `하네스 규칙 보정`을 섞지 않는다.
- 재시도본이 실패본보다 낫다는 결론과, 현재 `R31`이 과잉 검출이라는 결론은 동시에 참일 수 있다.

---

## 3. 선해결 필수 항목

아래 항목은 fusion 문서 작성 전에 선해결 상태로 적는다.

### 3.1 BLOCKER

- `CR-01`: 현재 골든 TR은 `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json`이다.
  `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json`은 실패 TR 현행 복사본이다.

### 3.2 MAJOR

- `CR-02`: 실패 TR 아크 6 opponent는 `윤석진 5 / 백도현 5` 2명이다.
- `CR-03`: 현재 골든 TR 실측은 `opponent_unique 31`, `max_share 24.3%`, `avg_bundle_chars 5필드 972.93` 기준으로 본다.
- `CR-04`: 현재 골든 TR은 현행 `R31`에서 `tail-20 최다 57블록`으로 걸린다.

### 3.3 Strengthen

- `ST-01`: tail 정밀도는 `tail-15`와 `tail-20`을 구분해 적는다.
- `ST-02`: `business_sector` 탐색 경로는 `genre_ext.business_sector`까지 포함해 문서에 적는다.
- `ST-04`: 중간 `validate_v3`는 70블록 전체 기준과 아크 기준을 분리해서 적는다.
- `ST-05`: 아크 2도 안전 배치 권장 구간으로 넣는다.

---

## 4. 최종 Fusion 문서 출력 계약

최종 문서는 아래 경로로 작성한다.

- `docs/2026-03-11/codex_chaebol_allowance_zero_failed_vs_retry_fusion.md`

섹션 순서는 고정한다.

1. `Findings`
2. `Shared Ground`
3. `Resolved Corrections`
4. `Remaining Open Issues`
5. `Fusion Verdict`
6. `Next Actions`

### 4.1 Findings

- 심각도 순으로 쓴다.
- 첫 줄에서 `재시도본이 실패본보다 낫다 / 아니다`를 명확히 적는다.
- `BI 5-pass PASS`가 source TR 품질을 보증하지 않는다는 점을 함께 적는다.

### 4.2 Shared Ground

반드시 아래를 공통분모로 적는다.

- 실패본 5대 결함의 성격
- 재시도본의 개선 방향
- `sector missing`이 field-drift 성격이라는 점
- BI 차이는 구조 자체보다 source TR 품질 차이라는 점

### 4.3 Resolved Corrections

반드시 아래를 표로 고정한다.

- 골든 TR 정본 경로
- 실패 TR 정본 경로
- 아크 6 opponent 수정
- 현재 골든 수치 갱신
- `R31` true-fail 상태

### 4.4 Remaining Open Issues

최소 아래 3개를 남긴다.

- `R31` rule recalibration
- `business_sector` 중첩 경로를 validate 문서/코드에 어떻게 반영할지
- `docs/2026-03-11`와 `docs/blockguide`의 중복 오더 정리

### 4.5 Fusion Verdict

판정은 아래 셋 중 하나만 쓴다.

- `대체 가능`
- `부분 개선`
- `대체 불가`

현재 기본값:

- 비교 결론만 보면 `대체 가능`
- 단, `R31` 하네스는 별도 보정 필요

### 4.6 Next Actions

다음 행동은 2갈래로만 닫는다.

1. 비교 결과를 확정하고 종료
2. `R31` 문서 기준으로 하네스 규칙 재조정 단계로 이동

---

## 5. 충돌 해결 규칙

문서 간 의견 충돌은 아래 순서로 푼다.

1. 숫자/경로 충돌: 원본 JSON 직접 계산으로 해결
2. 용어 충돌: D1/TF-BH1 정의 우선
3. 비교 결론 vs 규칙 결론 충돌:
   - 비교 결론은 산출물 우열
   - 규칙 결론은 하네스 적정성
   - 둘은 분리 기재

명시 금지:

- `R31`이 과잉이라고 해서 재시도본 개선 사실까지 뒤집기
- 반대로 재시도본이 더 좋다고 해서 `R31` 문제를 덮기

---

## 6. Fusion 전용 체크리스트

- [ ] 실패 TR / 개선 TR 정본 경로가 고정됐는가
- [ ] `CR-01~04`가 전부 해소되었는가
- [ ] `avg_bundle_chars`가 4필드/5필드 중 어느 정의인지 문서에 적었는가
- [ ] `BI PASS`와 `source TR 품질`을 분리해서 적었는가
- [ ] `R31` true-fail 이슈를 별도 오픈 이슈로 분리했는가
- [ ] UTF-8 오염(`???`, `�`)이 없는가

---

## 7. 최종 판정 기본선

이 fusion의 기본 결론은 아래처럼 잠근다.

- 비교 결론: **재시도본은 실패본을 대체 가능**
- 문서 결론: **기존 비교 오더는 정정 완료 후 사용 가능**
- 하네스 결론: **`R31`은 별도 재조정 문서 기준으로 다시 설계 필요**

이 셋을 한 문장으로 섞지 말고, 문단을 분리해 적는다.
