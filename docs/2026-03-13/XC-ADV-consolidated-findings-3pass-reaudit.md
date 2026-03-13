# XC-ADV: 병렬 Advisory 체인 안전성 — 3-Pass 최종 감사 결과

> 감사 일자: 2026-03-13
> 감사 범위: Advisory Chain 병렬 실행 아키텍처 전반
> 최종 3-Pass 완료

---

## 1. 3-Pass 실행 이력

### PASS 1: 전수 수집
- 수집 범위: 9개 파일, 4개 타겟, ~2,300줄 코드
- 수집 결과: 21건 후보 (T1: 5, T2: 5, T3: 5, T4: 6)

### PASS 2: 교차 검증
- 런타임 도달 가능성 확인: 전체 21건 도달 가능 확인
- 기존 findings 교차: T3-004, T2-038, OPUS-TF-T1, D-T3 4건과 부분 중복
- GIL 보호 범위 재검토: CPython setdefault() atomic 확인

### PASS 3: 위양성 제거 + 최종 등급
- 제거: 1건 (XC-ADV-020: 포맷팅 줄바꿈 변형 — 실질 위험 없음)
- 하향 조정: 3건 (XC-ADV-016: P2→P3, XC-ADV-017: P2→P3, XC-ADV-021: P2→P3)
- 최종 유효: **16건**

---

## 2. 최종 Finding Registry

| ID | Severity | 타겟 | 제목 | 상태 |
|----|---------|------|------|------|
| XC-ADV-001 | P2 | T1 | validation_results 병렬 setdefault 변이 | open |
| XC-ADV-002 | P3 | T1 | candidates dict 읽기 전용 — 현재 안전 | info |
| XC-ADV-003 | P3 | T1 | self.ctx 공유 참조 — getter만 호출 | info |
| XC-ADV-004 | P2 | T1 | world_state getter 부작용 가능성 | open |
| XC-ADV-005 | P2 | T1 | _truth_gate_llm_ask 콜백 공유 thread-safety | open |
| **XC-ADV-006** | **P1** | **T2** | **글로벌 timeout 후 executor blocking** | **open** |
| XC-ADV-007 | P2 | T2 | as_completed TimeoutError 미포착 | open |
| XC-ADV-008 | P3 | T2 | 이중 timeout 의미론적 모호성 | info |
| XC-ADV-009 | P2 | T2 | 예외 삼킴 — logging.debug 레벨 | open |
| XC-ADV-010 | P3 | T2 | 광범위 except 절 — 의도적 설계 | info |
| XC-ADV-011 | P2 | T3 | 동일 티어 간 충돌 억제 부재 | open |
| XC-ADV-012 | P3 | T3 | broad 키워드 매칭 오탐 가능성 | info |
| XC-ADV-013 | P3 | T3 | NumericConsistency 미분류 | open |
| XC-ADV-014 | P2 | T3 | 억제 사실 미전달 | open |
| XC-ADV-016 | P3 | T4 | 라운드 리셋 확인 — 누수 없음 | closed |
| XC-ADV-018 | P2 | T4 | TruthGate 경고 10건 상한 truncation | open |
| XC-ADV-019 | P3 | T4 | advisory_summary 단순 플래그 방식 | info |

---

## 3. 위험 매트릭스

```
           영향 범위
           단일 advisory  |  Advisory 체인 전체  |  파이프라인 전체
  ─────────────────────────────────────────────────────────
  빈도    드물게          │  XC-ADV-008         │  XC-ADV-006 (P1)
  (낮음)                  │                     │  XC-ADV-007
  ─────────────────────────────────────────────────────────
  빈도    에피소드마다    │  XC-ADV-009,010     │  XC-ADV-001
  (중간)                  │  XC-ADV-012,013     │  XC-ADV-005
  ─────────────────────────────────────────────────────────
  빈도    항상            │  XC-ADV-011         │  XC-ADV-018
  (높음)                  │  XC-ADV-014,019     │
```

---

## 4. 핵심 결론

### 4.1 Advisory 체인의 thread-safety 상태

**현재 CPython 런타임에서 안전하다.** 그 이유:

1. **대부분 읽기 전용**: 8개 advisory 중 6개는 공유 객체를 읽기만 한다.
2. **유일한 쓰기 2건**: TruthGate/NpcDrift의 `validation_results[_ci].setdefault()` — 서로 다른 key를 사용하므로 CPython GIL 하에서 경쟁 없음.
3. **LLM 콜백**: `_truth_gate_llm_ask`가 stateless wrapper라면 안전. Context Caching 경로만 확인 필요.

### 4.2 Timeout 아키텍처

**as_completed(300s) + future.result(60s) 이중 구조는 기능적이나, 엣지 케이스 처리 미흡:**

1. **P1**: 글로벌 timeout 후 executor가 미완료 future를 대기하며 blocking.
2. **P2**: TimeoutError가 상위로 전파되어 부분 결과 유실.
3. `future.result(timeout=60)`은 dead timeout (as_completed가 이미 완료된 future만 yield).

### 4.3 억제 로직

**티어 기반 단방향 억제는 올바른 설계:**

1. TruthGate(CRITICAL) → NpcDrift/RelDrift(MAJOR) 억제: 정확.
2. 동일 티어 간 미억제: Director에게 다중 관점 제공으로 해석 가능.
3. NumericConsistency 미분류: 간단한 수정으로 해결 가능.

### 4.4 MC 주입 충실도

**전반적으로 충실:**

1. 라운드 간 누수 없음 (L1290-1291 리셋 확인).
2. 포맷팅이 태그 정리 + 우선순위 재부착으로 가독성 향상.
3. TruthGate 10건 상한이 유일한 실질적 정보 손실 경로.

---

## 5. 권장 조치 우선순위

### 즉시 (P1, 0.5h)
- [ ] XC-ADV-006: `_run_advisory_chain()` 리팩터링 — `as_completed` 루프를 try/except TimeoutError로 감싸고, 미완료 future에 `cancel()` 호출. Python 3.9+에서는 executor context manager에 `cancel_futures=True` 전달 (현재 `with` 블록 내에서는 직접 불가하므로, 루프 후 명시적 cancel 필요)

### 단기 (P2, 2.4h)
- [ ] XC-ADV-007: TimeoutError 포착 + 부분 결과 보존 (0.3h)
- [ ] XC-ADV-009: logging.debug → logging.warning 상향 (0.1h)
- [ ] XC-ADV-018: truncation 잔여 건수 요약 라인 (0.2h)
- [ ] XC-ADV-001: thread-local 수집 후 메인 스레드 merge (0.5h)
- [ ] XC-ADV-014: 억제 요약 라인 추가 (0.3h)
- [ ] XC-ADV-005: llm_ask thread-safety 조사 (1.0h)

### 중기 (P3, 1.4h)
- [ ] XC-ADV-013: NumericConsistency 분류 조건 추가 (0.1h)
- [ ] XC-ADV-011: 동일 티어 중복 처리 설계 결정 (1.0h)
- [ ] XC-ADV-019: advisory_summary 건수 저장 (0.3h)

---

## 6. 기존 Findings 통합 매핑

| 본 감사 ID | 기존 ID | 관계 |
|-----------|---------|------|
| XC-ADV-006 | T2-038 | 보완 (blocking 경로 신규 발견) |
| XC-ADV-006, 007 | T3-004 | 보완 (구체적 실패 시나리오 신규 발견) |
| XC-ADV-002 | OPUS-TF-T1 L273 | 관련 (성능 vs safety 관점 차이) |
| XC-ADV-006-010 | D-T3 | 보완 (테스트 갭의 구체적 위험 식별) |

---

## 7. 감사 품질 메타데이터

| 항목 | 값 |
|------|-----|
| 분석 파일 수 | 9 |
| 분석 코드 줄수 | ~2,300 |
| PASS 1 후보 | 21 |
| PASS 2 교차검증 | 21/21 도달 가능 |
| PASS 3 위양성 제거 | 1건 |
| 최종 유효 findings | 16건 |
| P0/P1/P2/P3 분포 | 0/1/7/8 |
| 기존 중복 확인 | 4건 부분 중복 (신규 관점 추가) |
| 총 권장 공수 | 4.3h |
