# XC-ERR: 3-Pass 재감사 결과

> 생성일: 2026-03-13
> 트랙: XC-ERR (Error Propagation & Failure Mode Fidelity)
> 재감사 대상: 23건 전량

---

## Pass 1 → Pass 2 변경사항

| Finding | Pass 1 | Pass 2 | 변경 사유 |
|---------|--------|--------|----------|
| XC-ERR-005 | P1 | P2 | DB 마이그레이션은 초기 1회성 실행 — 런타임 영향 낮음 |
| XC-ERR-006 | P1 | P2 | 동일 사유 |
| XC-ERR-016 | P0 | P1 | 인메모리 변경(arcs=[])은 커밋 후 실행 확인 — 미커밋 트랜잭션 유령만 문제 |
| XC-ERR-020 | P2 | P2 유지 | 비원자성이나 안전한 방향(고아 파일) |

---

## Pass 2 → Pass 3 변경사항

| Finding | Pass 2 | Pass 3 | 변경 사유 |
|---------|--------|--------|----------|
| 전체 | - | - | Pass 2 → Pass 3 추가 변경 없음 |

---

## 위양성 제거 결과

### 제거된 후보 (Pass 1에서 수집되었으나 위양성으로 판정)

1. **`failure_analyzer.py` 28건의 except Exception**: 분석 유틸리티는 부실 데이터 대응이 핵심 기능. 모두 `_report_soft_failure()` 또는 `logging.debug` 포함. → 정상

2. **`stage4_post_processor.py` 47건 중 대부분**: `_report_soft_failure()` 호출하는 패턴이 대부분. 구조화된 리포팅이므로 "삼킴"이 아님. → 정상

3. **`stage4_interview_round.py` 71건 중 대부분**: advisory 체인(TruthGate, NpcDrift 등)의 개별 실패를 비차단 처리. ThreadPoolExecutor 내부에서 개별 advisory 실패가 전체를 막지 않는 설계. → 정상 (대원칙 1 준수)

4. **`vec_memory.py` 33건**: sqlite-vec 미설치 환경 대응 + 개별 임베딩 실패 비차단. → 정상

5. **`base_agent.py` 27건**: LLM 호출 재시도 로직 내 에러 핸들링 + 캐시 실패 비차단. → 정상

---

## 최종 Finding 등급 확정

### P1 (2건) — 수정 권장
| ID | 제목 | 확신도 |
|----|------|--------|
| XC-ERR-012 | Stage 2 validation 에러가 Stage 4에 미전달 | HIGH — 코드 근거 명확, 단 설계 의도 검토 필요 |
| XC-ERR-016 | _safe_commit() False 시 미롤백 | HIGH — 코드 경로 확인 완료 |

### P2 (7건) — 개선 권장
| ID | 제목 | 확신도 |
|----|------|--------|
| XC-ERR-001 | Stage3 telemetry silent pass | HIGH |
| XC-ERR-002 | Stage4 telemetry silent pass | HIGH |
| XC-ERR-005 | DB 마이그레이션 rollback 삼킴 | MED — 초기 1회성 |
| XC-ERR-006 | DB merge rollback+DETACH 삼킴 | MED — 초기 1회성 |
| XC-ERR-013 | Stage 2→3 에러 컨텍스트 압축 | MED — 설계 트레이드오프 |
| XC-ERR-014 | stage_attempts 분류 granularity | MED |
| XC-ERR-017 | rewind commit 실패 미롤백 | HIGH — XC-ERR-016 sister |
| XC-ERR-018 | rollback commit 실패 미롤백 | HIGH — XC-ERR-016 sister |
| XC-ERR-019 | EmotionTracker/StateDelta 미보호 | HIGH — sister 트래커 비대칭 |
| XC-ERR-020 | 파일/DB 비원자성 | LOW — 수용 가능 |

### P3 (14건) — 인지/모니터링
모두 확신도 HIGH — 코드 근거 확인 완료, 현행 유지 가능.

---

## 기존 262+ Finding 교차 참조 결과

### 중복으로 제외된 항목: 0건
- MRL-T4, MCP-T4, ROP-T2, MCS-T2/T3와 부분 중첩이 있으나, **에러 전파 관점**은 모두 신규 분석
- 기존 트랙은 "롤백 계약", "파괴적 작업 복구", "soft_failure 감사", "의미론 보존" 관점
- XC-ERR은 "에러 정보의 전파 충실도"와 "실패 시 보상 완전성" 관점으로 차별화

### 보완 관계
| XC-ERR Finding | 기존 Track | 관계 |
|----------------|-----------|------|
| XC-ERR-016~018 | MRL-T4 | 롤백 계약의 에러 전파 관점 보완 |
| XC-ERR-019 | MRL-T4 | 비대칭 보호 발견 (MRL-T4 미커버) |
| XC-ERR-012 | MCS-T3 | 에러 컨텍스트 전파 관점 추가 (MCS-T3은 성공 데이터 의미론) |
| XC-ERR-021 | ROP-T2 | VectorDB soft_failure 미리포팅 (ROP-T2 커버리지 외) |

---

## 결론

XC-ERR 트랙 감사 결과, 코드베이스의 에러 처리는 **전반적으로 양호**하다:
- bare except 0건
- soft_failure 인프라 가동 중
- 대부분의 비차단 경로에 최소 logging.debug 존재
- DB 트랜잭션 관리가 견고 (transaction 컨텍스트 매니저)

주요 개선점은 2개:
1. **_safe_commit() False 경로의 미커밋 트랜잭션 유령** (P1, 즉시 수정 가능 1h)
2. **EmotionTracker/StateDeltaTracker rollback try-except 누락** (P2, 즉시 수정 가능 1h)

크로스 스테이지 에러 전파 부재(XC-ERR-012)는 설계 의도와의 긴장이 있으므로 **설계 검토 후 결정** 권장.
