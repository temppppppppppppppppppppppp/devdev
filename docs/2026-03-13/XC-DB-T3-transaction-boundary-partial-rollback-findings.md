# XC-DB-T3: 트랜잭션 경계 & 부분 롤백 캐스케이드

> Track: XC-DB | 타깃: T3 | 생성일: 2026-03-13

---

## 1. 배경

`project_service.py`의 5개 파괴적 핸들러와 `db_manager.py`의 `commit_episode_factory()`가 다수의 DB 작업을 하나의 트랜잭션으로 묶어야 하나, 트랜잭션 경계 설정이 암시적이고 보상 트랜잭션이 없다.

트랜잭션 패턴:
1. `reset_after(commit=False)` — 내부에서 `BEGIN` + 다수 DELETE
2. 외부에서 추가 DELETE/UPDATE 실행 (ProjectService)
3. `_safe_commit()` — 최종 커밋

---

## 2. Findings

### [XC-DB-009] P1 | ProjectService reset_stage_2: lock 외부 DELETE 5+회 — 부분 실패 시 불완전 상태

| 필드 | 내용 |
|------|------|
| ID | XC-DB-009 |
| Severity | P1 (무성 실패) |
| 현상 요약 | `reset_stage_2()`가 `reset_after(commit=False)` 후 lock 외부에서 추가 DELETE를 실행하며, 중간 실패 시 일부 데이터만 삭제된 불완전 상태가 커밋될 수 있다 |
| 코드 근거 | `project_service.py:184-192` |
| 영향 경계 | Stage 2 리셋 시 arc_dependencies, stage_attempts, director_selections, anchors 테이블이 부분적으로만 정리될 수 있음 |
| 테스트 근거 | `test_project_service.py` — mock DB로 happy path만 검증 |
| 기존 중복 여부 | T1-09 관련이나 트랜잭션 경계 분석은 **신규** |
| 권장 후속 조치 | 모든 DELETE를 `reset_after()` 내부로 이동하거나, 전체를 `db.transaction()` 컨텍스트 매니저로 감싸기. 공수: 1시간 |

**상세 흐름**:
```python
def reset_stage_2(self):
    project.db.reset_after(1, commit=False)       # ← _lock 내부, BEGIN + 15+ DELETE
    # ↓ 이하 _lock 외부, 같은 트랜잭션 내이나 lock 미보호
    self._clear_stage2_metadata(project)           # 3개 DELETE (L132-136)
    self._clear_stage2_summary_anchors(project)    # 4개 DELETE (L101-114)
    self._clear_narrative_summary_anchors(project) # 1개 DELETE (L118)
    project.db.cursor.execute("DELETE ... 'arcs'") # 1개 DELETE (L189)
    self._safe_commit()                            # 커밋
```

**문제 시나리오**: `_clear_stage2_metadata()` L132 `DELETE FROM arc_dependencies` 성공 후, L133 `DELETE FROM stage_attempts WHERE stage = 2` 실패 시:
- arc_dependencies는 삭제됨
- stage_attempts는 남아있음
- 이후 `_safe_commit()` 호출 시 이 불완전 상태가 커밋됨? → **아니오**, `_safe_commit()` 내부에서 `conn.commit()`이 호출되면 모든 변경이 커밋되고, 실패 시 `except` 블록 (L211-213)에서 `_rollback_open_transaction()` 호출.

**재분석**: SQLite의 트랜잭션은 `BEGIN` ~ `COMMIT` 사이의 모든 변경을 원자적으로 처리. `reset_after(commit=False)`가 `BEGIN` 시작, 이후 모든 DELETE는 같은 트랜잭션 내. 중간에 예외 발생 시 `except` 블록에서 rollback.

**실질 위험**: 트랜잭션 원자성은 유지됨. 다만 **lock 외부에서 공유 커서 사용**이 문제. 다른 쓰레드가 이 사이에 `self.cursor`를 사용하면 트랜잭션이 오염될 수 있으나, `input()` 게이트로 실제 동시 실행 불가.

**결론**: Severity P1 → **P2 하향**. 트랜잭션 원자성 자체는 보장되나, lock 외부 커서 접근은 설계 위반.

---

### [XC-DB-010] P2 | rollback_episode: 5단계 작업 체인에서 VectorDB/파일 삭제는 커밋 후 — 보상 불가

| 필드 | 내용 |
|------|------|
| ID | XC-DB-010 |
| Severity | P2 (품질 저하) |
| 현상 요약 | `rollback_episode()`이 DB 커밋 성공 후 VectorDB 삭제, 파일 삭제, 런타임 상태 복원을 순차 실행하며, 이 중 하나가 실패해도 DB는 이미 롤백 상태 — 외부 저장소와 불일치 |
| 코드 근거 | `project_service.py:312-372` |
| 영향 경계 | 에피소드 롤백 후 VectorDB에 삭제된 에피소드의 임베딩이 잔류하거나, 파일 시스템에 orphan 원고 파일이 남을 수 있음 |
| 테스트 근거 | `test_project_service.py` — VectorDB 실패 시나리오 미검증 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | VectorDB/파일 삭제 실패 시 재시도 또는 "불일치 감지" 플래그 저장. 공수: 30분 |

**작업 순서**:
1. `project.db.reset_after(target_ep, commit=False)` — DB 삭제 (트랜잭션 내)
2. `_clear_narrative_summary_anchors()` — 추가 DELETE
3. seeds UPDATE
4. bible anchor 저장
5. `_safe_commit()` — **커밋** ← 여기서 DB 변경 확정
6. `_delete_draft_files_from_episode()` — 파일 삭제 ← 실패 시 orphan
7. `memory.delete_episodes_from()` — VectorDB 삭제 ← 실패 시 잔류
8. `_restore_runtime_state()` — 메모리 상태 복원

**위험**: 6-8번 중 하나가 실패하면 DB는 정리됐으나 외부 저장소는 불일치. 현재 코드에서 6번은 `OSError` catch, 7번은 `except Exception` catch로 **에러를 로깅하고 계속 진행** (비차단). 이는 **의도된 설계** — "DB가 SSOT이고 외부 저장소는 재생 가능"이라는 전제.

**실질 위험**: VectorDB 잔류 임베딩은 다음 에피소드 생성 시 중복 감지 등에 영향을 줄 수 있으나, 시스템이 DB 기준으로 동작하므로 **실질적 영향 LOW**.

---

### [XC-DB-011] P2 | reset_after() 내부 DELETE 순서 — episode_fts 삭제 실패 무시

| 필드 | 내용 |
|------|------|
| ID | XC-DB-011 |
| Severity | P2 (품질 저하) |
| 현상 요약 | `reset_after()` 내부에서 `episode_fts` DELETE 실패를 `pass`로 무시하며, FTS 인덱스와 실제 데이터 간 불일치가 발생할 수 있다 |
| 코드 근거 | `db_manager.py:2314-2317` |
| 영향 경계 | FTS 전문 검색 결과에 삭제된 에피소드가 포함될 수 있음 |
| 테스트 근거 | N/A |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | FTS 삭제 실패 시 경고 로깅 추가. `episode_meta` 삭제 전 FTS 삭제 시도는 현재 순서가 올바름 (FTS는 meta의 auxiliary). 공수: 5분 |

```python
# L2313-2317
try:
    self.cursor.execute("DELETE FROM episode_fts WHERE rowid >= ?", (target_ep,))
except Exception:
    pass  # FTS table may not exist
```

**분석**: FTS5 가상 테이블은 환경에 따라 없을 수 있어 `pass`가 합리적. 그러나 FTS가 존재하는데 삭제 실패(예: DB locked)인 경우도 무시됨. `pass` 대신 `logging.debug()`로 변경 권장.

---

### [XC-DB-012] P2 | commit_episode_factory: 8단계 중 seeds 업데이트가 공유 커서로 비일관

| 필드 | 내용 |
|------|------|
| ID | XC-DB-012 |
| Severity | P2 (품질 저하) |
| 현상 요약 | `commit_episode_factory()` L2138에서 seeds 아카이빙이 `self.cursor.execute()`로 직접 실행되며, 7단계까지 로컬 커서를 사용하는 메서드와 혼재 |
| 코드 근거 | `db_manager.py:2138-2140` — `self.cursor.execute("UPDATE seeds SET status = 'archived' ...")` |
| 영향 경계 | `commit_episode_factory()` 전체가 `self._lock.acquire()` (L2050)로 보호되므로 다른 쓰레드 접근은 차단됨. 같은 쓰레드 내 재진입도 없음 (최상위 호출). |
| 테스트 근거 | `test_db_manager.py` |
| 기존 중복 여부 | T1-07 하위 사례 |
| 권장 후속 조치 | `archive_seed()` 메서드 호출로 대체. 공수: 5분 |

---

### [XC-DB-013] P3 | execute_update() commit 누락 — 호출자 의존

| 필드 | 내용 |
|------|------|
| ID | XC-DB-013 |
| Severity | P3 (코드 스멜) |
| 현상 요약 | `execute_update()` L1039-1047이 커밋을 수행하지 않아 호출자가 수동 커밋해야 한다 |
| 코드 근거 | `db_manager.py:1039-1047` — `if not nested: self.commit()` 패턴 부재. 호출처 `reflexion_manager.py`에서 `self.context.db.conn.commit()` 수동 호출. |
| 영향 경계 | reflexion_memory 저장 시 커밋 누락 가능성 |
| 테스트 근거 | N/A |
| 기존 중복 여부 | **T1-06** (OPUS-TF-T1)과 동일 |
| 권장 후속 조치 | `if not nested: self.commit()` 추가 또는 독스트링 명시. 공수: 5분 |

---

### [XC-DB-014] P3 | transaction() 컨텍스트 매니저와 commit_episode_factory() 이중 패턴

| 필드 | 내용 |
|------|------|
| ID | XC-DB-014 |
| Severity | P3 (코드 스멜) |
| 현상 요약 | `transaction()` (L2219-2259) 컨텍스트 매니저와 `commit_episode_factory()` (L2030-2217)가 각각 독자적 트랜잭션 관리를 구현하여 코드 중복 |
| 코드 근거 | `transaction()`: `self._lock.acquire()` → `BEGIN` → yield → `commit`. `commit_episode_factory()`: `self._lock.acquire()` → `self.begin()` → 작업 → `self.commit()`. 동일한 패턴의 별도 구현. |
| 영향 경계 | 유지보수 부담. `transaction()` 사용처는 테스트 코드 중심, 운영 코드는 `commit_episode_factory()` 사용. |
| 테스트 근거 | N/A |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | `commit_episode_factory()` 내부를 `with self.transaction():` 사용으로 리팩토링 가능하나, 안정성 우선으로 현행 유지도 합리적. 최저 우선순위. |

---

## 3. 요약

| ID | Severity | 현상 | 실제 위험 |
|----|----------|------|-----------|
| XC-DB-009 | P2 (P1→하향) | reset_stage_2 lock 외부 DELETE | LOW (트랜잭션 원자성 유지) |
| XC-DB-010 | P2 | rollback 후 외부 저장소 불일치 | LOW (의도된 비차단 설계) |
| XC-DB-011 | P2 | FTS 삭제 실패 무시 | LOW (환경 호환성) |
| XC-DB-012 | P2 | commit_episode_factory 공유 커서 | LOW (lock 보호) |
| XC-DB-013 | P3 | execute_update commit 누락 | T1-06 중복 |
| XC-DB-014 | P3 | 이중 트랜잭션 패턴 | 코드 스멜 |
