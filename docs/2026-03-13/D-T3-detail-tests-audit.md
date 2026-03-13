# [D-T3] 미열거 테스트 전수 감사 보고서

> **터미널**: Terminal 3
> **작성일**: 2026-03-13
> **범위**: `tests/` 하위 미열거 테스트 전반, `tests/e2e`, `tests/integration`, `tests/chaos`, `tests/property`, `stage3/stage4` 관련 테스트 경계
> **방법**: 자체 3PASS 감리 (전 파일 구조 스캔 → 후보 재검증 → 최종 확정) + 정적 grep + 표적 파일 읽기

---

## 확정 발견사항

### [D-T3-01] P2 | Blueprint -> Stage4 핸드오프 계약을 묶는 교차 단계 테스트가 없다

**근거 파일**
- `tests/test_stage3_orchestrator.py`
- `tests/test_stage4_context_builder.py`
- `tests/test_stage4_orchestrator.py`

**증거**
- `tests/` 전역 grep에서 `handoff`, `cross-stage`, `blueprint.*stage4` 성격의 직접 계약 테스트가 확인되지 않았다.
- `test_stage3_orchestrator.py`는 Stage 3 출력으로 `{"integrated_scenario": "...", "scene_breakdown": {...}}` 수준의 stub blueprint를 주로 검증한다.
- `test_stage4_context_builder.py`와 `test_stage4_orchestrator.py`는 `blueprint={}` 또는 부분 payload로 Stage 4 내부 유틸을 검증하는 케이스가 다수다.

**영향**
- Stage 3이 저장한 blueprint 스키마와 Stage 4가 실제 소비하는 필드 셋 사이의 계약 파손을 조기 검출하지 못한다.

**수정안**
- Stage 3 저장 payload를 그대로 Stage 4 입력으로 넘기는 계약 테스트 1세트 추가.

---

### [D-T3-02] P2 | Advisory 병렬 경로는 핵심 테스트에서 `MagicMock`으로 우회된다

**근거 파일**
- `tests/test_stage4_interview_round.py:288`
- `modules/core/stage4_interview_round.py:3704-3726`

**증거**
- 테스트는 `_run_advisory_chain` 자체를 `MagicMock(return_value=[...])`로 대체한다.
- 실제 프로덕션은 `ThreadPoolExecutor(max_workers=8)`, `as_completed`, `future.result(timeout=60)` 경로를 사용한다.

**영향**
- advisory timeout, 부분 실패, future 수거 순서, 병렬 dict 병합 같은 위험 표면이 단위 테스트에서 직접 검증되지 않는다.

**수정안**
- `_run_advisory_chain` 실함수를 대상으로
  - 전원 성공
  - 일부 timeout
  - 일부 advisory 예외
  3경로를 분리 검증.

---

### [D-T3-03] P3 | E2E smoke 테스트 상당수가 체크인된 프로젝트 자산에 의존해 휴대성이 낮다

**근거 파일**
- `tests/e2e/test_l3_stage2_realproject.py`
- `tests/e2e/test_l3_stage3_smoke.py`
- `tests/e2e/test_l3_stage4_smoke.py`
- `tests/e2e/test_l3_golden_route.py`

**증거**
- `REAL_PROJECT_DB` 부재 시 `pytest.skip(...)` 처리.
- `treatments/*_tr_block_ALL.json` 또는 매칭 `bible/*_bi.json` 부재 시 `pytest.skip(...)` 처리.

**영향**
- 저장소 외부 환경이나 최소 CI 워커에서는 E2E 신호가 쉽게 사라진다.
- 테스트가 "실패"가 아니라 "skip"로 빠지기 때문에 결손을 눈치채기 어렵다.

**수정안**
- 경량 fixture용 seed artifact를 별도 테스트 자산으로 고정하거나, skip 사유를 CI 요약에 강제 표기.

---

### [D-T3-04] P3 | `integration/test_pipeline_smoke.py`의 VecMemory 경로는 환경 의존 skip이 많다

**근거 파일**
- `tests/integration/test_pipeline_smoke.py:132`
- `tests/integration/test_pipeline_smoke.py:166-170`

**증거**
- `sqlite-vec unavailable in this environment`
- `VecMemory not operational`
- `VecMemory 초기화 실패`

세 경로 모두 `pytest.skip(...)`로 처리된다.

**영향**
- 메모리/검색 관련 핵심 smoke가 환경에 따라 완전히 비활성화될 수 있다.
- 통합 테스트 통과 수치만 봐서는 retrieval 계층이 실제로 검증됐는지 알기 어렵다.

**수정안**
- skip 대신 최소한 xpass/xfail 또는 별도 summary ledger로 남겨 환경 의존성을 추적.

---

### [D-T3-05] P3 | xfail 인벤토리 기준선이 현재 트리와 맞지 않는다

**근거**
- 오더는 "`xfail 68개` 재검증"을 요구한다.
- 현재 `tests/*.py` 전체에서 `pytest.mark.xfail` / `xfail` 마커 grep 결과는 `0건`이다.
- `CLAUDE.md`의 테스트 기준선은 `3,847 collected`이지만 xfail 현황 ledger는 별도로 없다.

**영향**
- 과거에 xfail로 남겨둔 기대 실패가 실제로 수정됐는지, 단지 마커만 제거됐는지 현재 트리만으로는 복구할 수 없다.
- 테스트 부채 추적성이 끊긴다.

**수정안**
- xfail이 0건으로 줄어든 이유를 changelog 또는 audit ledger로 남길 필요가 있다.

---

## xfail 68개 재점검 메모

- **현재 tree 기준 xfail 마커 잔존 수**: `0`
- **판정**: "68개 중 68개가 현재도 xfail로 남아 있다"는 상태는 아니다.
- **주의**: 이것이 곧 "68개 전부 수정 완료"를 의미하지는 않는다. 마커 제거, 파일 이동, 테스트 삭제 중 무엇인지는 현재 소스만으로 단정 불가.

## 오탐 제거 로그

| ID | PASS1 후보 | PASS2 결과 | 사유 |
|----|------------|------------|------|
| FP-1 | assert 없는 테스트 파일 다수 | 제거 | `conftest.py`, fixture 모듈, import smoke 파일이 섞여 있던 파일 단위 오탐 |
| FP-2 | `MagicMock` 사용 테스트 전반 = 무효 테스트 | 제거 | 다수 케이스는 계약값/호출 인자/상태 변이를 충분히 검증 |
| FP-3 | `xfail 68개` 자체가 현재 결함 | 제거 | 현재는 마커 부재가 사실이며, 결함은 코드보다 ledger 단절 |
| FP-4 | `stage4_smoke` 전량 무가치 | 제거 | 파일 출력/DB 쓰기/루프 종료 조건 자체는 유효하게 검증 |
| FP-5 | `integration/test_pipeline_smoke.py` 전량 무효 | 제거 | DB/VecMemory 공통 경로는 환경이 맞을 때 실제 smoke 가치가 있음 |
| FP-6 | orphan test 대량 존재 | 제거 | 표본 추적에서 즉시 고아 파일은 확인되지 않음 |

**PASS1**: 11건 후보
**PASS2**: 6건 오탐 제거
**PASS3**: **5건 확정**

- P0: 0건
- P1: 0건
- P2: 2건 (`D-T3-01`, `D-T3-02`)
- P3: 3건 (`D-T3-03`, `D-T3-04`, `D-T3-05`)

