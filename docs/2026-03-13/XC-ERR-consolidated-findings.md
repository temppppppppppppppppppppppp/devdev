# XC-ERR: 에러 전파 & 실패 모드 충실도 — 통합 Findings

> 생성일: 2026-03-13
> 트랙: XC-ERR (Error Propagation & Failure Mode Fidelity)
> 총 Findings: 23건 (P1: 2, P2: 7, P3: 14)

---

## 심각도 분포

| 심각도 | 건수 | 서브태스크 |
|--------|------|-----------|
| P0 | 0 | - |
| P1 | 2 | T2(1), T3(1) |
| P2 | 7 | T1(4), T2(2), T3(1) |
| P3 | 14 | T1(7), T2(1), T3(6) |

---

## P1 Findings (수정 권장)

### [XC-ERR-012] P1 | Stage 2 validation 에러 디테일이 Stage 4에 전달되지 않음
- **소스**: T2
- **파일**: `stage4_context_builder.py` 전체 — `stage_attempts` 테이블 참조 0건
- **영향**: Stage 4가 Stage 2의 구조적 문제(자동 교정 이력, 중복 의심)를 모르고 집필
- **비고**: 디렉터 주권주의와의 긴장 — 의도적 설계일 가능성

### [XC-ERR-016] P1 | _safe_commit() 실패 시 미커밋 트랜잭션이 유령으로 남음
- **소스**: T3
- **파일**: `project_service.py:190-192` (reset_stage_2)
- **영향**: DB 미커밋 DELETE가 다음 작업에 영향
- **수정**: `_safe_commit()` False 반환 시 `_rollback_open_transaction()` 호출 추가

---

## P2 Findings (개선 권장)

| ID | 제목 | 파일:라인 |
|----|------|----------|
| XC-ERR-001 | Stage3 telemetry setattr silent pass | `stage3_orchestrator.py:467-473` |
| XC-ERR-002 | Stage4 동일 telemetry silent pass | `stage4_orchestrator.py:262-268` |
| XC-ERR-005 | DB 마이그레이션 rollback 내 pass | `db_manager.py:231-234` |
| XC-ERR-006 | DB merge 마이그레이션 rollback+DETACH 삼킴 | `db_manager.py:938-941` |
| XC-ERR-013 | Stage 2→3 에러 컨텍스트 압축 | `stage3_orchestrator.py:729-736` |
| XC-ERR-014 | stage_attempts 에러 분류 granularity 부족 | `db_manager.py:557-588` |
| XC-ERR-017~020 | 롤백 보상 갭 4건 | `project_service.py` 다수 |

---

## P3 Findings (인지/모니터링)

| ID | 제목 | 비고 |
|----|------|------|
| XC-ERR-003 | world_state.get_summary silent return | 비차단 |
| XC-ERR-004 | 두 번째 get_summary 폴백도 silent | sister |
| XC-ERR-007 | save_episode_data rollback 후 pass | 의도적 [R7-P1-2] |
| XC-ERR-008 | prompt_version silent return None | logging.debug 존재 |
| XC-ERR-009 | 5개+ advisory 빌더 silent return "" | 의도적 비차단 |
| XC-ERR-010 | protagonist 3단계 폴백 체인 | 견고한 설계 |
| XC-ERR-011 | notifier import except Exception | except 범위 좁히기만 |
| XC-ERR-015 | FailureAnalyzer 이중 리포팅 | 비차단 |
| XC-ERR-020 | 파일시스템/DB 비원자성 | 수용 가능 트레이드오프 |
| XC-ERR-021 | VectorDB 삭제 실패 삼킴 | soft_failure 미리포팅 |
| XC-ERR-022 | rollback invariants 경고만 | 자동 복구 없음 |
| XC-ERR-023 | reset_after 양호 패턴 | 정보성 |

---

## 핵심 패턴 요약

### 1. 코드베이스의 에러 처리 전략 (양호)
- **bare except 0건**: 전량 제거 완료
- **soft_failure 인프라**: 구조화된 리포팅 시스템 (`soft_failure.py`) 가동 중
- **비차단 설계**: advisory/context 실패가 메인 파이프라인을 차단하지 않음 (대원칙 1 준수)
- **DB 트랜잭션**: `db_manager.py`의 `transaction()` 컨텍스트 매니저가 적절한 에러 타입별 롤백 제공

### 2. 개선 필요 영역
- **_safe_commit() False 경로**: 예외 없이 실패하는 경우 미커밋 트랜잭션이 남음 (P1)
- **크로스 스테이지 에러 전파**: 의도적 부재이나 인지 필요 (P1)
- **telemetry setattr pass**: 최소 logging.debug 추가 필요 (P2)
- **EmotionTracker/StateDeltaTracker rollback**: sister 트래커와 비대칭 보호 (P2)

### 3. 수정 불필요 영역
- advisory 빌더의 `logging.debug + return ""` 패턴 (96건): 의도적 비차단
- `failure_analyzer.py`의 28건: 분석 유틸리티의 방어적 처리
- `db_manager.py` save_episode_data의 이중 rollback pass: `[R7-P1-2]` 의도적 방어

---

## 기존 감사 교차 참조

| 기존 Track | 중첩 Finding | 관계 |
|-----------|-------------|------|
| MRL-T4 | XC-ERR-016~019 | 롤백 계약 — 부분 중첩, XC-ERR은 에러 전파 관점에서 분석 |
| MCP-T4 | XC-ERR-020 | 파괴적 작업 복구 — 파일시스템 비원자성 |
| ROP-T2 | XC-ERR-021 | soft_failure 감사 — VectorDB 경로 미리포팅 |
| MCS-T3 | XC-ERR-012 | Stage4→Stage2 의미론 — 에러 컨텍스트 전파 관점 추가 |
| MCS-T2 | XC-ERR-013 | Stage3→Stage2 의미론 — 에러 컨텍스트 관점 추가 |

---

## 예상 수정 공수

| 우선순위 | Finding | 공수 |
|----------|---------|------|
| 즉시 | XC-ERR-016 (_safe_commit 후 rollback) | 1h |
| 즉시 | XC-ERR-019 (EmotionTracker try-except) | 1h |
| 단기 | XC-ERR-001/002 (telemetry logging) | 1h |
| 단기 | XC-ERR-017/018 (sister commit 패턴) | 1h |
| 중기 | XC-ERR-011 (except 범위 좁히기) | 0.5h |
| 검토 | XC-ERR-012 (크로스스테이지 에러 전파) | 4h (설계 검토) |
| **합계** | | **~8.5h** |
