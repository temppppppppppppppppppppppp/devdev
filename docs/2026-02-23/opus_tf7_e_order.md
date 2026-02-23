# TF-7-E: World State / Fact Ledger / State Delta 삼중 일관성 — 감사 실행 오더

> **Opus TF-7-E** | 2026-02-23
> **담당**: Opus 에이전트 E
> **출력**: `docs/2026-02-23/opus_tf7_e_audit.md`
> **수칙**: 수정 금지 / 수동 코드 조사만 / UTF-8 주의 / 근거 필수

---

## 배경
에피소드 롤백(D-2 완료)에서 `npc_history`, `WorldState`, `FactLedger` 롤백이 구현됐다고 표기. 그러나 3개 저장소(`world_state.py`, `fact_ledger.py`, `state_delta_tracker.py`)가 동일 트랜잭션 내에서 원자적으로 롤백되는지 미검증. TF-6 A에서 `project_service.py` 롤백 원자성 수정됨 — 그 파급 확인.

---

## 실행 순서

### Step 1: WorldState 롤백 메커니즘
**파일**: `modules/core/world_state.py` (474줄)
- Read 도구로 전체 파일 읽기
- `rollback_to(ep_num)` 또는 `reset_to(ep_num)` 메서드 존재 여부
- 없으면: WorldState가 에피소드 번호별 스냅샷 없이 단일 상태만 유지하는 구조인지 확인
- DB 저장 방식: JSON 직렬화 → `TEXT` 컬럼 vs 별도 스냅샷 테이블
- `ensure_ascii=False` 직렬화 여부 (한글 세계관 설정)

### Step 2: FactLedger 롤백 메커니즘
**파일**: `modules/core/fact_ledger.py` (601줄)
- Read 도구로 전체 파일 읽기
- append-only 이력 확인: `INSERT` only, `UPDATE/DELETE` 없는지
- 롤백 시 처리: `ep_num` 이후 항목 `DELETE` vs `WHERE ep_num <= target` 조회
- `deceased=True` 팩트의 `ep_num` 기록 여부 — 롤백 후 미래 사망 팩트 차단 가능한지
- JSON 역직렬화 시 `True`/`False` vs `"True"`/`"False"` 문자열 혼용 위험

### Step 3: StateDeltaTracker 크기 제한
**파일**: `modules/core/state_delta_tracker.py` (419줄)
- Read 도구로 전체 파일 읽기
- delta 항목 누적 자료구조: `list`, `deque`, `dict` 중 어느 것인가
- 최대 크기 제한 여부 (TF-6 TF-B 계열과 동일 패턴 탐색)
- `state_tracker.py`의 메인 상태와 delta가 분기(diverge)될 수 있는 경로
- 롤백 시 delta가 초기화되는지 확인

### Step 4: StateTracker 스냅샷 경로 집중 감사
**파일**: `modules/domain/agents/state_tracker.py`
- 파일 전체를 읽지 않고, 다음 키워드 영역만 집중:
  - `rollback`, `snapshot`, `reset`, `_undo` 관련 메서드
  - `world_state`, `fact_ledger`, `state_delta_tracker`와의 상호작용 경로
- 롤백 시 `world_state.rollback()`, `fact_ledger.rollback()`, `state_delta_tracker.reset()` 모두 호출하는지
- 호출 순서와 예외 발생 시 부분 롤백 위험

### Step 5: ConstraintDB 에피소드 태깅
**파일**: `modules/core/constraint_db.py` (585줄)
- Read 도구로 전체 파일 읽기
- 제약 조건 추가 시 `ep_num` 또는 `episode` 필드 기록 여부
- 롤백 시 미래 제약 조건 필터링: `WHERE ep_num <= target` 조건 존재 여부
- 제약 조건 DB가 독립 트랜잭션으로 커밋되는지 확인

### Step 6: ReferenceAnchor 에피소드 태깅
**파일**: `modules/core/reference_anchor.py` (351줄)
- Read 도구로 전체 파일 읽기
- 앵커 항목의 에피소드 태깅 여부
- 롤백 후 미래 앵커 참조 차단: `ep_num > target` 앵커 필터링 로직

### Step 7: 원자성 교차 확인
- `modules/core/services/project_service.py`의 `rollback_episode()` 메서드
  - TF-6 A 패치 후 WorldState/FactLedger/StateDelta가 모두 동일 `_safe_commit()` 안에 포함되는지
  - 개별 커밋 경로가 남아 있는지

---

## 이슈 판정 기준
- CRITICAL: 롤백 후 WorldState/FactLedger가 복구되지 않아 사망NPC가 재등장하는 경로
- HIGH: 3개 저장소 중 일부만 롤백되어 데이터 불일치
- MEDIUM: 크기 제한 없는 누적, 에피소드 태깅 누락

---

## 출력 파일 구조
```
# TF-7-E 감사 보고서 — World State / Fact Ledger / State Delta

## 감사 파일 목록
## 발견 이슈 (총 N건)
### [TF-7-E-1] ...
## [FP] 오탐 목록
## TF-6-A 패치 파급 확인
## 요약 테이블
```
