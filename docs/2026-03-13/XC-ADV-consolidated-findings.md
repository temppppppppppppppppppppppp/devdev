# XC-ADV: 병렬 Advisory 체인 안전성 — 통합 Findings

> 감사 일자: 2026-03-13
> 감사 범위: Advisory Chain 병렬 실행 아키텍처 전반 (9개 파일, ~2,300줄)
> 방법론: 3-Pass (수집 → 교차검증 → 위양성 제거)

---

## Executive Summary

| 등급 | 건수 | 내용 |
|------|------|------|
| P0 | 0 | - |
| P1 | 1 | 글로벌 timeout 후 executor blocking |
| P2 | 7 | 공유 상태 변이, 예외 처리, 억제 로직, truncation |
| P3 | 8 | 정보성/개선 권장 |
| 제거 | 1 | 위양성 |
| **합계** | **17** (유효 16건) | |

---

## P1 Findings (1건)

### [XC-ADV-006] P1 | 글로벌 300s timeout 후 미수거 future 처리 부재

| 필드 | 내용 |
|------|------|
| ID | XC-ADV-006 |
| Severity | P1 |
| 현상 요약 | `as_completed(timeout=300)` 만료 시 미완료 future가 cancel 되지 않고 executor.shutdown(wait=True)가 무기한 대기 |
| 코드 근거 | `stage4_interview_round.py:3817-3832` |
| 영향 경계 | Stage 4 — 파이프라인 전체 blocking 가능 |
| 테스트 근거 | 기존 테스트 커버리지 0% (D-T3, T3-004 확인) |
| 기존 중복 여부 | T2-038 (ThreadPoolExecutor 타임아웃 후 메모리 점유)과 관련 |
| 권장 후속 조치 | Python 3.9+ `cancel_futures=True` 사용 또는 명시적 future.cancel() 추가. 공수 0.5h |

---

## P2 Findings (7건)

### [XC-ADV-001] P2 | validation_results 병렬 setdefault 변이
- TruthGate와 NpcDrift가 동일 validation_results[_ci] dict에 병렬 setdefault() 호출
- CPython GIL 하에서 안전하나, 비CPython 미지원 + 비대칭 설계
- `stage4_interview_round.py:3858-3859`, `3899-3900`

### [XC-ADV-004] P2 | TruthGate 내부 world_state 메서드 호출 시 부작용 가능성
- world_state getter 메서드의 순수성 미확인
- `truth_gate.py:100-108, 180-186, 211-218, 265-271, 331-335`

### [XC-ADV-005] P2 | _truth_gate_llm_ask 콜백 공유
- 6개 LLM advisory가 동일 콜백을 동시 호출. Context Caching 관여 시 경쟁 가능
- `stage4_interview_round.py:3844, 3883, 3935, 3959, 4038, 4089, 4137`

### [XC-ADV-007] P2 | as_completed TimeoutError 미포착
- TimeoutError가 for 루프 밖으로 전파, 부분 결과 유실
- `stage4_interview_round.py:3818`

### [XC-ADV-009] P2 | 예외 삼킴 — logging.debug 레벨
- future.result() 실패가 DEBUG로만 기록. 기본 INFO 설정에서 비가시
- `stage4_interview_round.py:3826`

### [XC-ADV-011] P2 | 동일 티어 간 충돌 억제 부재
- 티어 2 advisory 간 동일 NPC 중복 경고 미억제
- `stage4_interview_round.py:1091`

### [XC-ADV-018] P2 | TruthGate 경고 10건 상한 truncation
- 최대 21건 CRITICAL 경고 중 10건만 Director에 전달
- `stage4_interview_round.py:3866`

---

## P3 Findings (8건)

| ID | 제목 | 코드 위치 |
|----|------|----------|
| XC-ADV-002 | candidates dict 읽기 전용 — 현재 안전 | `stage4_interview_round.py:3808-3815` |
| XC-ADV-003 | self.ctx 공유 참조 — getter만 호출 | 다수 |
| XC-ADV-008 | 이중 timeout 의미론적 모호성 — dead timeout | `stage4_interview_round.py:3818-3821` |
| XC-ADV-010 | 광범위 except 절 — 의도적 비치명 설계 | `stage4_interview_round.py:3870 외 6곳` |
| XC-ADV-012 | broad 키워드 매칭 오탐 가능성 — 실현 확률 낮음 | `stage4_interview_round.py:1023-1064` |
| XC-ADV-013 | NumericConsistency 미분류 — 기본 티어 1 | `stage4_interview_round.py:1004-1021` |
| XC-ADV-016 | _last_advisory_summary 라운드 리셋 확인 — 누수 없음 | `stage4_interview_round.py:1290-1291` |
| XC-ADV-019 | advisory_summary 단순 플래그 방식 — 건수 미저장 | `stage4_interview_round.py:1566-1583` |

---

## 추가 P3 (억제/주입 관련)

| ID | 제목 | 비고 |
|----|------|------|
| XC-ADV-014 | 억제 사실 미전달 — Director 정보 완전성 | P2 → 확정 P2 (T3에 기록) |
| XC-ADV-015 | 단방향 억제 설계 확인 | 정보성 |
| XC-ADV-017 | "이상 없음" 축약 — 설계 의도적 | P3 |
| XC-ADV-021 | advisory 최상단 배치 — 의도적 설계 | P3 |

---

## 타겟별 요약

### T1: 병렬 공유 상태 변이 (5건)
- **P2 2건**: validation_results setdefault, llm_ask 콜백 공유
- **P3 3건**: candidates 읽기 전용, ctx 공유 참조 안전, world_state getter 순수성
- **결론**: CPython GIL 하에서 현재 안전. 방어적 개선 권장.

### T2: Timeout & 예외 삼킴 (5건)
- **P1 1건**: 글로벌 timeout 후 executor blocking
- **P2 2건**: TimeoutError 미포착, logging.debug 레벨
- **P3 2건**: 이중 timeout 모호성, 광범위 except
- **결론**: XC-ADV-006이 유일한 P1. timeout 후 future 정리 로직 추가 필요.

### T3: 억제 양방향성 (5건)
- **P2 2건**: 동일 티어 미억제, 억제 사실 미전달
- **P3 3건**: broad 매칭 오탐, NumericConsistency 미분류, 단방향 설계 확인
- **결론**: 억제 로직은 합리적. 동일 티어 중복과 미전달이 개선 대상.

### T4: MC 주입 충실도 (5건)
- **P2 1건**: TruthGate 10건 상한
- **P3 4건**: 라운드 누수 없음, 축약 설계, 플래그 방식, 최상단 배치
- **결론**: 주입 경로 전반적으로 충실. TruthGate truncation이 유일한 실질 위험.

---

## 기존 Findings 교차 참조 결과

| 기존 ID | 본 감사 관련 | 중복 여부 |
|----------|------------|---------|
| T3-004 | XC-ADV-006, 007 | **부분 중복** — T3-004는 테스트 부재만 언급, 본 감사는 구체적 blocking 경로 신규 발견 |
| T2-038 | XC-ADV-006 | **부분 중복** — T2-038은 메모리 관점, 본 감사는 blocking 관점 |
| OPUS-TF-T1 L273 | XC-ADV-002 | **관련** — 중복 계산 관련이나 mutation이 아닌 성능 이슈 |
| D-T3 | XC-ADV-006, 007, 009, 010 | **부분 중복** — D-T3은 테스트 갭 관점 |

---

## 공수 추정 요약

| 우선순위 | 작업 | 공수 |
|---------|------|------|
| P1 | XC-ADV-006: cancel_futures 적용 | 0.5h |
| P2 | XC-ADV-007: TimeoutError 포착 | 0.3h |
| P2 | XC-ADV-009: logging.warning 상향 | 0.1h |
| P2 | XC-ADV-018: truncation 잔여 건수 표시 | 0.2h |
| P2 | XC-ADV-001: thread-local 수집 패턴 | 0.5h |
| P2 | XC-ADV-011: 동일 티어 중복 처리 | 1.0h |
| P2 | XC-ADV-014: 억제 사실 요약 라인 | 0.3h |
| P2 | XC-ADV-005: llm_ask thread-safety 조사 | 1.0h |
| **합계** | | **3.9h** |
