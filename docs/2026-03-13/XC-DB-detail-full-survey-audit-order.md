# XC-DB: DB 트랜잭션 일관성 & 커서 안전 — 조사 계획

> Track: XC-DB | 생성일: 2026-03-13 | 감사 유형: 문서 전용 코드 감사

---

## 1. 감사 범위

### 핵심 파일
| 파일 | 역할 | 라인 수 |
|------|------|---------|
| `modules/core/db_manager.py` | SQLite DB 매니저 (WAL, RLock, 30+ 테이블) | ~3,500 |
| `modules/core/services/project_service.py` | 파괴적 프로젝트 작업 (롤백/리와인드/와이프) | ~430 |
| `modules/core/stage4_post_processor.py` | Stage4 PASS 후처리 (DB 다중 쓰기) | ~1,200 |
| `modules/core/stage2_finalizer.py` | Stage2 Director 심사 + PASS 후처리 | ~1,200 |

### 보조 파일 (직접 커서 접근 확인)
- `modules/core/vec_memory.py` — 별도 `check_same_thread=False` 커넥션
- `modules/core/stage4_interview_round.py` — `ThreadPoolExecutor(max_workers=8)` Advisory 병렬
- `smoke_sc.py` — `project.db.cursor.execute()` 직접 접근

---

## 2. 타깃 분석 항목

### XC-DB-T1: Legacy cursor vs Local cursor 패턴 충돌
- **초점**: `db_manager.py` L63 `self.cursor` (공유) vs L54-57 독스트링 지침 (로컬 커서 권장)
- **검증**: `self.cursor.execute` ~185회 사용 중 lock 없는 경로 존재 여부
- **검증**: `project_service.py` 15곳 `project.db.cursor.execute()` — lock 바이패스 여부
- **검증**: Advisory 8쓰레드에서 DB 접근 시 커서 경합

### XC-DB-T2: JSON 컬럼 corruption 복원력
- **초점**: `_safe_json_loads()` L79-84 — 적용 범위 vs 미적용 경로
- **검증**: JSON 쓰기 경로에서 `json.dumps()` 실패 시 동작
- **검증**: `load_anchor()`, `get_manuscript()` 등 읽기에서 NULL/손상 JSON 처리

### XC-DB-T3: 트랜잭션 경계 & 부분 롤백 캐스케이드
- **초점**: `project_service.py` 5개 핸들러의 트랜잭션 경계
- **검증**: `reset_stage_2` — `reset_after(commit=False)` + 5개 DELETE + `_safe_commit()`
- **검증**: 중간 실패 시 보상 트랜잭션 부재
- **검증**: `commit_episode_factory()` 원자성 보장 범위

### XC-DB-T4: WAL + check_same_thread=False 상호작용
- **초점**: L125 `check_same_thread=False`, L158 `PRAGMA journal_mode=WAL`
- **검증**: Advisory 8쓰레드 + 메인 쓰레드 동시 DB 접근
- **검증**: WAL 체크포인트 자동/수동 정책
- **검증**: `VACUUM` (L2344) 실행 시 WAL 모드 간섭

---

## 3. 방법론: 3-Pass

| Pass | 목표 | 기준 |
|------|------|------|
| PASS 1 | 전수 후보 수집 | HIGH/MED/LOW confidence 태깅 |
| PASS 2 | 코드 근거 교차 검증 | 런타임 도달 가능성, 기존 262+ finding 중복 확인 |
| PASS 3 | 오탐 제거, 최종 심각도 | P0-P3 확정, 공수 추정 |

## 4. 기존 finding 교차 참조 대상

| ID | 제목 | 관련 |
|----|------|------|
| T1-07 | db_manager.py 15개+ 메서드 공유 cursor | T1 직접 겹침 |
| T1-09 | ProjectService raw cursor 접근 15곳 | T1 직접 겹침 |
| T1-06 | execute_update() commit 누락 | T3 관련 |
| checklist-3pass L73 | DB RLock + WAL OK | T4 관련 |

---

## 5. 산출물

1. `XC-DB-T1-legacy-cursor-local-cursor-conflict-findings.md`
2. `XC-DB-T2-json-column-corruption-resilience-findings.md`
3. `XC-DB-T3-transaction-boundary-partial-rollback-findings.md`
4. `XC-DB-T4-wal-check-same-thread-interaction-findings.md`
5. `XC-DB-consolidated-findings.md`
6. `XC-DB-consolidated-findings-3pass-reaudit.md`
