# XC-MEM Track: 메모리 안전 & 상태 정합성 — 전면 전량 조사 계획

> 날짜: 2026-03-13
> Track: XC-MEM (Cross-cutting Memory Safety & State Integrity)
> 방법론: 3-Pass (수집 -> 교차검증 -> 오탐 제거)

---

## 1. 목적

`truth_gate.py`, `base_agent.py`, `project_service.py`, `stage4_interview_round.py`,
`world_state.py`, `fact_ledger.py` 등 메모리 상태를 다루는 핵심 모듈을 대상으로:

1. **참조 전달(reference passing)에 의한 상태 오염** 가능성
2. **Context Caching 무효화 누락**으로 인한 stale 데이터 잔류
3. **롤백 시 상태 스냅샷 분기**(world_state/fact_ledger 비동기 실패)
4. **사망 NPC regex 엣지 케이스**에 의한 false positive/negative

를 전면 조사한다.

---

## 2. 대상 파일

| 파일 | 줄 수 | 역할 |
|------|-------|------|
| `modules/core/truth_gate.py` | 439 | 메모리 오염 방지 7개 검사 |
| `modules/core/world_state.py` | ~1200 | 세계 상태 문서 관리 |
| `modules/core/fact_ledger.py` | ~730 | 누적 팩트 원장 |
| `modules/domain/agents/base_agent.py` | ~2000 | AI 에이전트 베이스 (Context Caching 포함) |
| `modules/core/services/project_service.py` | 430 | 롤백/리셋/와이프 서비스 |
| `modules/core/stage4_interview_round.py` | ~4100 | Stage4 인터뷰 라운드 (advisory 체인) |
| `main_a.py` | ~9000 | 진입점 (롤백 후 캐시 무효화) |

---

## 3. 타겟 분석 항목

### XC-MEM-T1: TruthGate 방어적 복사 갭
- **초점**: `truth_gate.py:24-48` — `validate()` 메서드의 `state_updates` 파라미터
- **검사 항목**:
  - `state_updates`가 참조로 전달되어 TruthGate 내부에서 caller 상태를 변이시킬 수 있는가
  - `stage4_interview_round.py:3836-3872`에서 TruthGate에 전달하기 전 defensive copy 여부
  - `world_state`, `fact_ledger` 인스턴스가 TruthGate 내부에서 write 접근 가능한가

### XC-MEM-T2: Context Caching 무효화 크로스 스테이지
- **초점**: `base_agent.py:1765` — 클래스 변수 `_context_caches`
- **검사 항목**:
  - 롤백 시 `BaseAgent._context_caches`가 무효화되는가
  - 개별 에이전트 `invalidate_caches()` vs 클래스 레벨 `_context_caches.clear()` 차이
  - TTL 만료만으로 충분한지 (30분 default)
  - API key rotation 시에만 `.clear()` 호출되는 패턴

### XC-MEM-T3: 롤백 중 상태 스냅샷 분기
- **초점**: `project_service.py:63-98` — `_restore_runtime_state()`
- **검사 항목**:
  - `world_state.rollback_to()` 성공 + `fact_ledger.rollback_to()` 실패 시 상태 분기
  - 개별 `try/except`로 인한 부분 실패 허용 패턴
  - `episode_bibles` 리플레이 중 동일 DB 커넥션 공유로 인한 교차 오염
  - `_assert_rollback_invariants()` 커버리지 한계

### XC-MEM-T4: 사망 NPC Regex 엣지 케이스
- **초점**: `truth_gate.py:116-152` — `_check_deceased_resurrection()`
- **검사 항목**:
  - `(?<![가-힣])` lookbehind의 한글 2바이트 NPC 이름 처리
  - 부분 문자열 매칭 (예: "김" vs "김철수")
  - `len(name) < 2` 필터의 단음절 NPC 이름 무시
  - 회상 키워드 근접도 검사 없음 (같은 줄 어디든 있으면 허용)

---

## 4. 3-Pass 방법론

### PASS 1: 후보 수집
- 대상 파일 전량 읽기
- HIGH/MED/LOW 신뢰도로 후보 finding 수집
- 코드 스니펫 + 줄 번호 기록

### PASS 2: 교차 검증
- 런타임 도달 가능성 확인
- 기존 262+ finding과 중복 여부 교차 참조
- 테스트 커버리지 확인

### PASS 3: 최종 판정
- 오탐 제거
- P0-P3 심각도 할당
- 8필드 표준 포맷으로 최종 finding 작성

---

## 5. 산출물

| 파일명 | 내용 |
|--------|------|
| `XC-MEM-T1-truthgate-defensive-copy-gap-findings.md` | T1 상세 분석 |
| `XC-MEM-T2-context-caching-invalidation-cross-stage-findings.md` | T2 상세 분석 |
| `XC-MEM-T3-rollback-state-snapshot-divergence-findings.md` | T3 상세 분석 |
| `XC-MEM-T4-deceased-npc-regex-edge-case-findings.md` | T4 상세 분석 |
| `XC-MEM-consolidated-findings.md` | 통합 finding (PASS 1-2) |
| `XC-MEM-consolidated-findings-3pass-reaudit.md` | 3pass 최종 판정 |
