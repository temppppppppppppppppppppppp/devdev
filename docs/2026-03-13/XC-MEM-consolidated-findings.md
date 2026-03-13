# XC-MEM 통합 Finding 목록 (PASS 1-2)

> 날짜: 2026-03-13
> Track: XC-MEM (메모리 안전 & 상태 정합성)
> 상태: PASS 2 완료 — 교차검증 및 중복 제거 적용

---

## 요약 통계

| 심각도 | 건수 |
|--------|------|
| P0 (Critical) | 0 |
| P1 (High) | 0 |
| P2 (Medium) | 4 |
| P3 (Low) | 6 |
| **합계** | **10** |

---

## PASS 1 후보 → PASS 2 판정

| ID | PASS 1 신뢰도 | PASS 2 판정 | 사유 |
|----|---------------|-------------|------|
| XC-MEM-T1-001 | LOW | retained (P3) | TruthGate 내부 전량 검사로 읽기 전용 확인. 방어적 개선 관점에서만 유의미 |
| XC-MEM-T1-002 | MED | retained (P3) | fact_ledger 미사용 확인. dead parameter |
| XC-MEM-T1-003 | HIGH | retained (P2) | 8개 advisory 병렬 쓰기 패턴 확인. CPython GIL 하 안전하나 구현 의존적 |
| XC-MEM-T2-001 | HIGH | retained (P2) | content_hash 기반 자연 방어가 있으나, 동일 에피소드 재실행 시 stale HIT 가능 |
| XC-MEM-T2-002 | MED | retained (P3) | arc_ensemble/blueprint_ensemble 무효화 누락. 영향 제한적 |
| XC-MEM-T2-003 | LOW | retained (P3) | TTL 만료만으로 충분하나 방어적 개선 가능 |
| XC-MEM-T3-001 | HIGH | retained (P2) | world_state/fact_ledger 독립 실패 시 분기 가능. 앱 재시작으로 복구 가능 |
| XC-MEM-T3-002 | HIGH | retained (P2) | _assert_rollback_invariants()가 ws/fl 미검증. MRL-T4와 관련되나 구체화는 신규 |
| XC-MEM-T3-003 | MED | retained (P3) | 에러 핸들링 비대칭. 리플레이 실패 시 영향 있으나 확률 낮음 |
| XC-MEM-T4-001 | HIGH | retained (P2) | lookahead 부재로 유사 이름 false positive. 실질적 영향 있음 |
| XC-MEM-T4-002 | LOW | retained (P3) | 단음절 필터 합리적. 실질 영향 극소 |
| XC-MEM-T4-003 | LOW | retained (P3) | 대사 마커 한정. 실질 영향 낮음 |
| XC-MEM-T4-004 | LOW | **제거** | 행동 동사 한정은 의도적 설계. 주어 패턴이 대부분 커버 |

---

## 전체 Finding 목록 (PASS 2 기준 10건)

### [XC-MEM-T1-001] P3 | TruthGate state_updates 방어적 복사 부재 (설계상 안전)

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T1-001 |
| Severity | P3 |
| 현상 요약 | TruthGate.validate()가 state_updates를 참조로 수신하나, 내부 7개 검사 모두 읽기 전용이므로 실제 변이 위험 없음 |
| 코드 근거 | `truth_gate.py:48` |
| 영향 경계 | Stage 4 advisory 체인 |
| 테스트 근거 | 입력 dict 변이 여부 검증 테스트 없으나 변이 경로 없음 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 향후 쓰기 로직 추가 시 deepcopy 적용 (0.5h) |

### [XC-MEM-T1-002] P3 | fact_ledger 인스턴스 미사용 (dead parameter)

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T1-002 |
| Severity | P3 |
| 현상 요약 | TruthGate 생성자의 fact_ledger 파라미터가 내부에서 참조되지 않음 |
| 코드 근거 | `truth_gate.py:21` |
| 영향 경계 | 없음 (dead code) |
| 테스트 근거 | 무관 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 향후 사용 계획 없으면 제거 (0.5h) |

### [XC-MEM-T1-003] P2 | validation_results 공유 list에 대한 병렬 쓰기

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T1-003 |
| Severity | P2 |
| 현상 요약 | 8개 advisory가 동일 validation_results 리스트에 병렬로 .setdefault() 호출. CPython GIL 의존적 |
| 코드 근거 | `stage4_interview_round.py:3808-3815`, L3858-3859 |
| 영향 경계 | Stage 4 advisory 체인. PyPy/free-threaded Python에서 위험 |
| 테스트 근거 | 병렬 쓰기 safety 테스트 없음 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 각 advisory가 독립 결과 반환 후 main thread에서 merge (2h) |

### [XC-MEM-T2-001] P2 | 롤백/리셋/와이프 시 BaseAgent._context_caches 미무효화

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T2-001 |
| Severity | P2 |
| 현상 요약 | 4개 파괴적 연산 후 Gemini API Context Cache가 무효화되지 않음 |
| 코드 근거 | `main_a.py:3288-3314` (및 L3226, L3256, L3328) |
| 영향 경계 | 5개 Context Caching 에이전트. content_hash 기반 자연 방어 있으나 완벽하지 않음 |
| 테스트 근거 | `BaseAgent._context_caches` 상태 검증 없음 |
| 기존 중복 여부 | MRL-T2와 관련되나 Gemini API 레벨 구체화는 신규 |
| 권장 후속 조치 | `BaseAgent._context_caches.clear()` 1줄 추가 (0.5h) |

### [XC-MEM-T2-002] P3 | arc_ensemble/blueprint_ensemble 캐시 무효화 미호출

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T2-002 |
| Severity | P3 |
| 현상 요약 | 롤백 시 writer/director만 무효화. arc_ensemble/blueprint_ensemble 미대상 |
| 코드 근거 | `main_a.py:3226-3246` |
| 영향 경계 | Stage 2 리셋 후 재실행 시 |
| 테스트 근거 | 무효화 테스트 없음 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 무효화 대상 확인 후 추가 (1h) |

### [XC-MEM-T2-003] P3 | _context_caches 명시적 무효화 API 부재

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T2-003 |
| Severity | P3 |
| 현상 요약 | TTL 만료와 LRU 퇴출만으로 자동 정리. 명시적 무효화 메서드 없음 |
| 코드 근거 | `base_agent.py:1804-1846` |
| 영향 경계 | Gemini API 서버 캐시 자원 |
| 테스트 근거 | 없음 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | `invalidate_all_context_caches()` 클래스 메서드 추가 (1h) |

### [XC-MEM-T3-001] P2 | world_state/fact_ledger 독립 롤백 시 부분 실패 허용

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T3-001 |
| Severity | P2 |
| 현상 요약 | 한쪽 rollback_to() 실패 시 인메모리 상태 분기. 다음 생산에 모순 데이터 전달 가능 |
| 코드 근거 | `project_service.py:70-82` |
| 영향 경계 | Stage 4 advisory (TruthGate, NumericDrift). 앱 재시작 시 복구 |
| 테스트 근거 | 부분 실패 시나리오 테스트 없음 |
| 기존 중복 여부 | MRL-T4-001 관련. world_state/fact_ledger 분기 구체화는 신규 |
| 권장 후속 조치 | 한쪽 실패 시 양쪽 재초기화 (1h) |

### [XC-MEM-T3-002] P2 | _restore_runtime_state() 실패가 성공으로 보고

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T3-002 |
| Severity | P2 |
| 현상 요약 | 인메모리 복원 실패가 silent. _assert_rollback_invariants()가 ws/fl 미검증 |
| 코드 근거 | `project_service.py:70-98`, L374-396 |
| 영향 경계 | 사용자 인식/실제 상태 불일치 |
| 테스트 근거 | invariant 검증 테스트 없음 |
| 기존 중복 여부 | MRL-T4-001 관련. 구체화 신규 |
| 권장 후속 조치 | invariant에 ws/fl last_updated_ep 검증 추가 (1h) |

### [XC-MEM-T3-003] P3 | episode_bibles 리플레이 에러 핸들링 비대칭

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T3-003 |
| Severity | P3 |
| 현상 요약 | WorldState는 섹션별 try/except, FactLedger는 단일 흐름. 리플레이 실패 시 데이터 범위 차이 |
| 코드 근거 | `world_state.py:158-500+` vs `fact_ledger.py:129-400+` |
| 영향 경계 | 롤백 리플레이 정합성 |
| 테스트 근거 | 부분 실패 테스트 없음 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | FactLedger에 섹션별 try/except 추가 (2h) |

### [XC-MEM-T4-001] P2 | 유사 이름 NPC의 false positive (lookahead 부재)

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T4-001 |
| Severity | P2 |
| 현상 요약 | 사망 NPC 이름이 생존 NPC 이름의 접두사인 경우 false positive |
| 코드 근거 | `truth_gate.py:128-135` — lookahead `(?![가-힣])` 부재 |
| 영향 경계 | TruthGate → Director REJECT 유도 |
| 테스트 근거 | 유사 이름 간섭 테스트 없음 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | lookahead 추가 (1h) |

---

## 기존 Finding과의 관계

| XC-MEM Finding | 관련 기존 Finding | 관계 |
|----------------|-------------------|------|
| XC-MEM-T2-001 | MRL-T2 (cache lifecycle) | 구체화 (Gemini API 레벨 특정) |
| XC-MEM-T3-001 | MRL-T4-001 (commit-rollback recovery) | 구체화 (ws/fl 분기 시나리오 특정) |
| XC-MEM-T3-002 | MRL-T4-001 | 구체화 (invariant 검증 범위 특정) |
| 나머지 7건 | 해당 없음 | 완전 신규 |
