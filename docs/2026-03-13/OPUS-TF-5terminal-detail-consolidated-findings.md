# OPUS TF 2차 디테일 감사 통합 보고서

> **작성일**: 2026-03-13
> **범위**: 디테일 감사 T1~T5 전량 취합 (`D-T1`, `D-T2`, `D-T3`, `D-T4`, `D-T5`)
> **방법**: 터미널별 3PASS 결과 취합 + 마스터 교차 검증 + ledger 정리

---

## 총괄 통계

| Severity | T1 | T2 | T3 | T4 | T5 | **확정** |
|----------|----|----|----|----|----|--------:|
| **P0** | 0 | 0 | 0 | 0 | 0 | **0** |
| **P1** | 0 | 0 | 0 | 0 | 2 | **2** |
| **P2** | 2 | 3 | 2 | 2 | 11 | **20** |
| **P3** | 2 | 3 | 3 | 3 | 9 | **20** |
| **합계** | 4 | 6 | 5 | 5 | 22 | **42** |

## 터미널별 상태

| 터미널 | 상태 | 문서 | 최종 건수 |
|--------|------|------|----------|
| T1 | 완료 | `D-T1-detail-infra-audit.md` | 4 |
| T2 | 완료 | `D-T2-detail-agents-models-audit.md` | 6 |
| T3 | 완료 | `D-T3-detail-tests-audit.md` | 5 |
| T4 | 완료 | `D-T4-config-contract-ssot-audit-report.md` | 5 |
| T5 | 완료 | `OPUS-TF-5terminal-detail-T5-findings.md` | 22 |

---

## 상위 위험군

### P1 (즉시 추적 필요)

| ID | 터미널 | 주제 |
|----|--------|------|
| D-T5-001 | T5 | 실제 진입점이 아닌 `main.js` 복제본 2개 잔존 |
| D-T5-002 | T5 | 렌더러가 `generativelanguage.googleapis.com`에 직접 fetch하여 API 키 노출 경로 형성 |

### P2 (구조/계약/정합성)

| ID | 터미널 | 주제 |
|----|--------|------|
| D-T1-002 | T1 | Stage 0 외부 시점 삽입 정책 메뉴 mojibake |
| D-T1-004 | T1 | `reflexion_manager`가 `DBManager` commit API 우회 |
| D-T2-01 | T2 | `Critic` dead agent |
| D-T2-02 | T2 | `ArcCritic` dead agent |
| D-T2-03 | T2 | `RelationshipChange.model_config` 이중 선언 |
| D-T3-01 | T3 | Stage3 -> Stage4 핸드오프 계약 테스트 부재 |
| D-T3-02 | T3 | Advisory 병렬 경로 테스트가 `MagicMock`으로 우회 |
| D-T4-01 | T4 | `api-contract-v1.yaml` 엔드포인트 4건 누락 |
| D-T4-02 | T4 | `전처리_ssot/contracts/` 8개 계약 파일이 코드 미연동 |
| D-T5-003 | T5 | CSP `script-src 'unsafe-inline'` 허용 |
| D-T5-004 | T5 | `material:delete-file` main process 확인 다이얼로그 부재 |
| D-T5-006 | T5 | `stopBackend()` race |
| D-T5-007 | T5 | `startupTimer` clearTimeout 누락 |
| D-T5-008 | T5 | `smoke_sc.py` 복구가 atexit 의존 |
| D-T5-009 | T5 | `RESET.py` 동적 테이블명 + FinanceHUD 미반영 |
| D-T5-010 | T5 | `tf_c1_patch.py` 1회성 패치 잔류 |
| D-T5-011 | T5 | `phase0_design.json` 스키마 불일치 |
| D-T5-012 | T5 | `StoryExpander.save_all()` / `load_state()` 포맷 불일치 |
| D-T5-013 | T5 | 최소 로그 스키마 검증 갭 |
| D-T5-015 | T5 | `run_stage4_smoke.py` manuscripts 무조건 DELETE |

---

## 교차 검증 요약

### 1. hard duplicate 제거 대상은 확인되지 않았다

- 이번 디테일 세트에서는 같은 ID를 다른 터미널이 중복 보고한 사례를 확정하지 못했다.
- `D-T4-01`의 API 계약 누락과 `D-T5-001/002`의 Desktop 문제는 모두 표면이 다르다.
- `D-T1-002`의 mojibake는 1차 T2와 theme이 겹치지만, 디테일 세트 내부 중복으로는 보지 않았다.

### 2. dead/stale surface가 여러 터미널에서 반복 확인된다

- T1: `error_helper.py`
- T2: `Critic`, `ArcCritic`, 미사용 validator 2건
- T4: Spec-only contract 8건, 미참조 config 3건
- T5: 1회성/임시 파일, 중복 `main.js`, temp 파일

### 3. 테스트와 런타임 계약 사이의 갭이 독립 클러스터를 이룬다

- T3는 Stage3->Stage4 handoff와 advisory 병렬 경로 테스트 부재를 적출했다.
- T4는 API contract와 계약 JSON의 형해화를 적출했다.
- T5는 Desktop 진입점과 렌더러/메인 프로세스 경계를 적출했다.

---

## ledger 보정

- `D-T1` 복원 과정에서 원래 구두 요약의 "`reflexion_memory` CREATE 부재"는 오탐으로 제거했다.
- `D-T5` 문서 본문 헤더에는 `P2 — MODERATE (10건)`으로 적혀 있으나, 실제 ID 수와 상단 집계표 기준 값은 `11건`이다. 이 통합표는 `11건`을 최종 ledger로 사용한다.
- `T3` 오더의 "`xfail 68개`"는 현재 tree와 불일치하며, 현재 마커 잔존 수는 `0건`이다.

## 결론

- 2차 디테일 감사는 이제 **T1~T5 전부 문서화 완료** 상태다.
- 최우선 추적 항목은 Desktop 진입점 중복과 렌더러 API 키 노출 경로다.
- 중기적으로는 dead surface 정리와 테스트/계약 SSOT 정리가 함께 필요하다.

