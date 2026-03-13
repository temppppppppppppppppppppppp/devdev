# XC-MEM 3-Pass 최종 판정 (Reaudit)

> 날짜: 2026-03-13
> Track: XC-MEM (메모리 안전 & 상태 정합성)
> 상태: PASS 3 완료 — 오탐 제거 및 최종 심각도 할당

---

## 1. PASS 3 판정 요약

| ID | PASS 2 | PASS 3 | 변경 사유 |
|----|--------|--------|----------|
| XC-MEM-T1-001 | P3 | **제거** | 현재 코드에서 변이 경로가 존재하지 않음. 미래 가능성만으로는 finding 아님 |
| XC-MEM-T1-002 | P3 | P3 유지 | dead parameter 확인. 향후 사용 계획 확인 필요 |
| XC-MEM-T1-003 | P2 | P2 유지 | CPython GIL 의존적 동작. free-threaded Python 3.13+ 대비 필요 |
| XC-MEM-T2-001 | P2 | P2 유지 | content_hash 자연 방어가 있으나 edge case 존재. 수정 공수 극소(0.5h) |
| XC-MEM-T2-002 | P3 | **제거** | arc_ensemble/blueprint_ensemble이 BaseAgent Level 2 인메모리 캐시를 별도로 유지하지 않으므로 무효화 불필요. _context_caches.clear()가 전체를 커버 |
| XC-MEM-T2-003 | P3 | **제거** | XC-MEM-T2-001 수정(`.clear()` 추가)이 이 문제를 자동 해결 |
| XC-MEM-T3-001 | P2 | P2 유지 | 부분 실패 허용은 실질적 위험. 앱 재시작 복구 가능하나 사용자 경험 영향 |
| XC-MEM-T3-002 | P2 | P2 유지 | invariant 검증 범위 확장 필요 확인 |
| XC-MEM-T3-003 | P3 | P3 유지 | 에러 핸들링 비대칭 확인. 영향 확률 낮으나 존재 |
| XC-MEM-T4-001 | P2 | P2 유지 | lookahead 부재로 false positive 확인. 실제 프로덕션 시나리오에서 발생 가능 |

---

## 2. 최종 Finding 목록 (7건)

### 2.1 P2 Finding (4건)

#### [XC-MEM-T1-003] P2 | validation_results 공유 list에 대한 병렬 쓰기

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T1-003 |
| Severity | P2 |
| 현상 요약 | 8개 advisory가 ThreadPoolExecutor로 병렬 실행되면서 동일 `validation_results` 리스트의 같은 인덱스 dict에 `.setdefault()` 호출. CPython GIL 하에서 실질적 문제 없으나 구현 의존적 |
| 코드 근거 | `stage4_interview_round.py:3808-3815` — 8개 future에 `candidates`, `validation_results` 공유 전달. L3858-3859 `validation_results[_ci].setdefault("truth_gate_warnings", ...)` |
| 영향 경계 | Stage 4 advisory 체인. Python 3.13 free-threaded 모드 도입 시 data race 가능 |
| 테스트 근거 | 병렬 쓰기 safety 검증 테스트 없음 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 각 advisory가 독립 결과를 반환하고 main thread에서 merge하는 패턴 적용 (2h) |

#### [XC-MEM-T2-001] P2 | 롤백/리셋/와이프 시 BaseAgent._context_caches 미무효화

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T2-001 |
| Severity | P2 |
| 현상 요약 | 4개 파괴적 연산(rollback_episode, reset_stage_2, rewind_stage_2, wipe_production_data) 성공 후 `BaseAgent._context_caches`가 클리어되지 않음. API key rotation 시에만 `.clear()` 호출 |
| 코드 근거 | `main_a.py:3288-3314` — `_rollback_episode()` 성공 후 Level 2(에이전트 개별) 캐시만 무효화. `BaseAgent._context_caches.clear()` 미호출. 동일 누락: L3226, L3256, L3328 |
| 영향 경계 | 롤백 후 30분(TTL) 이내 동일 content_hash 재진입 시 stale Gemini 캐시 HIT 가능. content_hash 기반 키 설계가 자연 방어막이나 edge case 존재 |
| 테스트 근거 | `tests/test_main_a_rollback.py`는 Level 2 캐시 무효화만 검증 |
| 기존 중복 여부 | MRL-T2 관련이나 Gemini API Context Cache 레벨 구체화는 신규 |
| 권장 후속 조치 | 4개 파괴적 연산 성공 후 `BaseAgent._context_caches.clear()` 1줄 추가 (0.5h) |

#### [XC-MEM-T3-001] P2 | world_state/fact_ledger 독립 롤백 시 부분 실패 허용

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T3-001 |
| Severity | P2 |
| 현상 요약 | `_restore_runtime_state()`에서 world_state와 fact_ledger의 `rollback_to()`가 독립 `try/except`로 실행. 한쪽만 실패 시 인메모리 상태 분기 → 다음 에피소드 생산 시 모순 데이터가 advisory에 전달 |
| 코드 근거 | `project_service.py:70-82` — `world_state.rollback_to(target_ep)` L73, `fact_ledger.rollback_to(target_ep)` L80 각각 독립 `try/except`. 실패 시 UI 로그만 출력 |
| 영향 경계 | Stage 4 advisory 체인 (TruthGate는 world_state, NumericDrift는 fact_ledger 참조). 앱 재시작으로 DB에서 재로드하면 복구 |
| 테스트 근거 | 부분 실패 시나리오 테스트 없음. `_assert_rollback_invariants()` (L374-396)은 emotion/state_delta만 검증 |
| 기존 중복 여부 | MRL-T4-001 관련. world_state/fact_ledger 분기 구체화는 신규 |
| 권장 후속 조치 | 한쪽 실패 시 양쪽 모두 INIT_STATE로 재초기화 (1h). 또는 `_assert_rollback_invariants()`에 ws/fl `last_updated_ep < target_ep` 검증 추가 (1h) |

#### [XC-MEM-T4-001] P2 | 유사 이름 NPC의 false positive (lookahead 부재)

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T4-001 |
| Severity | P2 |
| 현상 요약 | 사망 NPC "무영"이 있을 때 생존 NPC "무영검이 공격했다" 원고에서 `(?<![가-힣])무영.*공격` 패턴이 매칭되어 false positive 경고 발생. `(?![가-힣])` lookahead가 없음 |
| 코드 근거 | `truth_gate.py:127-135` — `_lb = r"(?<![가-힣])"` lookbehind만 적용. 이름 뒤 한글 추가 문자 검사 없음 |
| 영향 경계 | TruthGate CRITICAL 경고 → Director REJECT 유도. advisory 모드이므로 blocking은 아니나, Director가 REJECT 판정 시 불필요한 재작성 루프 발생 |
| 테스트 근거 | `tests/test_truth_gate.py` — 유사 이름 NPC 간 간섭 테스트 없음 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | action_patterns의 `{_esc}` 뒤에 `(?![가-힣])` 추가 (1h). 예: `rf"{_lb}{_esc}(?![가-힣])[이가은는]\s"` |

### 2.2 P3 Finding (3건)

#### [XC-MEM-T1-002] P3 | TruthGate fact_ledger dead parameter

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T1-002 |
| Severity | P3 |
| 현상 요약 | `TruthGate.__init__`의 `fact_ledger` 파라미터가 `self._fact_ledger`에 할당되나 7개 검사 메서드 어디에서도 참조되지 않음 |
| 코드 근거 | `truth_gate.py:21` |
| 영향 경계 | 코드 정리 관점. 메모리 안전 영향 없음 |
| 테스트 근거 | 무관 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 향후 사용 계획 확인 후 판단 (0.5h) |

#### [XC-MEM-T3-002] P3 | _assert_rollback_invariants() world_state/fact_ledger 미검증

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T3-002 |
| Severity | P3 |
| 현상 요약 | 롤백 후 invariant 검증이 emotion_tracker와 state_delta_tracker만 대상. world_state와 fact_ledger의 `last_updated_ep`가 target_ep 이상인지 검증하지 않음 |
| 코드 근거 | `project_service.py:374-396` |
| 영향 경계 | 사용자 인식/실제 상태 불일치 조기 감지 불가 |
| 테스트 근거 | invariant 검증 자체 테스트 없음 |
| 기존 중복 여부 | MRL-T4 관련 |
| 권장 후속 조치 | ws/fl last_updated_ep 검증 추가 (1h) |

#### [XC-MEM-T3-003] P3 | WorldState vs FactLedger 리플레이 에러 핸들링 비대칭

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T3-003 |
| Severity | P3 |
| 현상 요약 | WorldState.update_from_state_changes()는 8개 섹션별 독립 try/except, FactLedger는 단일 흐름. 리플레이 중 중간 항목 실패 시 데이터 범위 차이 |
| 코드 근거 | `world_state.py:158-500+` (섹션별 try/except) vs `fact_ledger.py:129-400+` |
| 영향 경계 | 롤백 리플레이 정합성. 발생 확률 낮음 |
| 테스트 근거 | 부분 실패 시나리오 테스트 없음 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | FactLedger에 섹션별 try/except 추가 (2h) |

---

## 3. 제거된 후보 (3건)

| ID | 제거 사유 |
|----|----------|
| XC-MEM-T1-001 | 미래 가능성만으로는 finding 아님. 현재 변이 경로 0 |
| XC-MEM-T2-002 | arc_ensemble/blueprint_ensemble이 Level 2 캐시를 별도 유지하지 않음. T2-001 수정으로 커버 |
| XC-MEM-T2-003 | T2-001 수정(`.clear()` 추가)이 이 문제를 자동 해결 |

---

## 4. 권장 조치 우선순위

| 순위 | Finding | 공수 | 효과 |
|------|---------|------|------|
| 1 | XC-MEM-T2-001 | 0.5h | Gemini API 캐시 stale 방지 (4곳에 1줄 추가) |
| 2 | XC-MEM-T4-001 | 1h | 사망 NPC false positive 제거 (lookahead 추가) |
| 3 | XC-MEM-T3-001 | 1h | 롤백 부분 실패 시 안전망 |
| 4 | XC-MEM-T3-002 | 1h | invariant 검증 범위 확장 |
| 5 | XC-MEM-T1-003 | 2h | 병렬 쓰기 안전성 (Python 3.13+ 대비) |
| 6 | XC-MEM-T3-003 | 2h | 리플레이 에러 복원력 |
| 7 | XC-MEM-T1-002 | 0.5h | dead parameter 정리 |

**총 예상 공수: 8h**

---

## 5. 결론

XC-MEM Track에서 **P0/P1 심각도 finding은 0건**이다. 4건의 P2와 3건의 P3가 확인되었으며, 모두 "즉시 데이터 손실" 수준이 아닌 "방어적 개선" 또는 "edge case 대비" 성격이다.

가장 영향력 있는 finding은:
- **XC-MEM-T2-001**: 수정 공수 0.5h로 가장 투자 효율이 높음
- **XC-MEM-T4-001**: 실제 프로덕션에서 유사 이름 NPC가 등장할 때 불필요한 REJECT 유발 가능

현재 시스템의 메모리 안전 설계는 전반적으로 양호하며, TruthGate의 읽기 전용 패턴, content_hash 기반 캐시 키, 앱 재시작 자동 복구 등이 자연적 방어 메커니즘으로 작동하고 있다.
