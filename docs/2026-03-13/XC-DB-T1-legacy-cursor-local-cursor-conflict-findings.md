# XC-DB-T1: Legacy cursor vs Local cursor 패턴 충돌

> Track: XC-DB | 타깃: T1 | 생성일: 2026-03-13

---

## 1. 배경

`db_manager.py` L54-57 독스트링:
```python
[INF-P1-1] Thread-safety note:
``self.cursor`` is retained for backward compatibility but should NOT be used
in new/modified code. Instead, create a **local cursor** via
``cur = self.conn.cursor()`` inside each method, always within ``with self._lock:``.
```

그러나 실제로 `self.cursor.execute()`가 ~185회 사용되고 있으며, 로컬 커서 패턴은 일부 메서드에만 적용됨.

---

## 2. Findings

### [XC-DB-001] P2 | db_manager.py 내부 공유 커서와 로컬 커서 혼용 — 재진입 시 커서 상태 간섭

| 필드 | 내용 |
|------|------|
| ID | XC-DB-001 |
| Severity | P2 (품질 저하) |
| 현상 요약 | `self.cursor` (공유)와 `cur = self.conn.cursor()` (로컬)가 혼재하며, 중첩 호출 시 공유 커서의 결과 세트가 덮어써질 수 있다 |
| 코드 근거 | `db_manager.py:1537-1540` `get_lore_list_by_category()`에서 `cur = self.cursor.execute(...)` → 공유 커서 반환값을 `cur`에 받지만 이것은 `self.cursor` 자체임. 같은 lock 내에서 `update_lore_item()`이 `self.cursor.execute()`를 호출하면 진행 중인 결과 세트가 소실됨. |
| 영향 경계 | `commit_episode_factory()` (L2030-2217)가 내부에서 `save_causal_links()` (self.cursor L2024), `update_karma()` (self.cursor L1981), `update_lore_item()` (self.cursor L1467) 등을 호출. RLock이 재진입 가능하므로 같은 쓰레드 내 중첩 진입 시 공유 커서 결과가 덮어써질 수 있음. |
| 테스트 근거 | `test_db_manager.py` 존재하나 중첩 호출 시나리오 테스트 미확인 |
| 기존 중복 여부 | **T1-07** (OPUS-TF-T1)과 동일 현상. 본 finding은 구체적 재진입 시나리오 분석을 추가 |
| 권장 후속 조치 | 점진적으로 `self.cursor` → `cur = self.conn.cursor()` + `try/finally: cur.close()` 전환. 공수: 2-3시간 (185곳 기계적 변환) |

**코드 증거 — 혼용 패턴 (로컬 커서 사용 메서드 vs 공유 커서 사용 메서드)**:
- 로컬 커서: `save_manuscript()` L1053, `get_manuscript()` L1071, `get_blueprint()` L1098, `save_episode_bible()` L1154, `execute_query()` L1032, `execute_update()` L1043
- 공유 커서: `save_anchor()` L1549, `load_anchor()` L1566, `sync_seeds()` L1443, `archive_seed()` L1457, `save_blueprint()` L1847, `save_state_log_with_summary()` L1873, `get_latest_state()` L1882, `reset_after()` L2289-2329 (~30곳)

**재진입 시나리오**:
```
commit_episode_factory() [RLock 획득]
  → save_manuscript() [RLock 재진입, 로컬 cur — 안전]
  → update_martial_tracker() [RLock 재진입, 로컬 cur — 안전]
  → save_causal_links() [RLock 미사용 직접 self.cursor — L2024]
    → self.cursor.executemany(...)  ← 공유 커서 사용
  → L2138 self.cursor.execute(...) ← seeds 업데이트, 같은 공유 커서
```
`save_causal_links()`는 `with self._lock:` 블록 안에 있지만, `commit_episode_factory()`가 이미 `self._lock.acquire()` (L2050)를 잡고 있어 RLock 재진입됨. `self.cursor`가 executemany의 결과 세트를 가진 상태에서 다음 execute가 덮어쓰므로, 데이터 손실은 아니나 커서 상태가 오염될 수 있음.

**실제 위험도**: SQLite의 `executemany()` 후 `fetchone()`/`fetchall()`을 하지 않으므로 결과 세트 간섭은 DML(INSERT/UPDATE/DELETE) 계열에서는 실질적 영향 없음. **SELECT 혼용 시에만 문제**. 현재 `commit_episode_factory()`에서 SELECT 호출은 없어 **실제 운영 위험은 LOW**.

---

### [XC-DB-002] P2 | ProjectService 15곳 raw cursor 접근 — RLock 바이패스

| 필드 | 내용 |
|------|------|
| ID | XC-DB-002 |
| Severity | P2 (품질 저하) |
| 현상 요약 | `project_service.py`에서 `project.db.cursor.execute()` 15곳 직접 호출로 DBManager의 `_lock` 보호를 우회한다 |
| 코드 근거 | `project_service.py:101-154` — `_clear_stage2_summary_anchors()`, `_clear_stage2_metadata()`, `_clear_narrative_summary_anchors()` 등에서 `project.db.cursor.execute("DELETE FROM ...")`를 직접 호출. `with self._lock:` 없이 실행됨. |
| 영향 경계 | Stage 2 리셋/리와인드/에피소드 롤백 시 호출. 이 경로는 메인 쓰레드에서만 호출되므로 (사용자 input() 게이트), Advisory 병렬 쓰레드와의 실제 경합 가능성은 극히 낮음. |
| 테스트 근거 | `test_project_service.py` 존재, mock DB 사용 |
| 기존 중복 여부 | **T1-09** (OPUS-TF-T1)과 동일 현상 |
| 권장 후속 조치 | `execute_update()`/`execute_query()` 또는 전용 메서드로 교체. 공수: 1시간 |

**15곳 전체 목록**:
```
L101: project.db.cursor.execute("DELETE FROM anchors WHERE key = 'volumes'")
L102: project.db.cursor.execute("DELETE FROM anchors WHERE key = 'series_summary'")
L103: project.db.cursor.execute("DELETE FROM anchors WHERE key LIKE 'volume_summary_%'")
L105: project.db.cursor.execute("DELETE FROM anchors WHERE key LIKE 'arc_summary_%'")
L107: project.db.cursor.execute("DELETE ... GLOB 'arc_summary_[0-9]*' ...")
L118: project.db.cursor.execute("DELETE FROM anchors WHERE key LIKE 'narrative_summary_ep_%'")
L121: project.db.cursor.execute("DELETE ... GLOB 'narrative_summary_ep_[0-9]*' ...")
L132: project.db.cursor.execute("DELETE FROM arc_dependencies")
L133: project.db.cursor.execute("DELETE FROM stage_attempts WHERE stage = 2")
L134: project.db.cursor.execute("DELETE FROM director_selections ...")
L139: project.db.cursor.execute("DELETE FROM arc_dependencies WHERE from_arc_no >= ? ...")
L143: project.db.cursor.execute("DELETE FROM stage_attempts WHERE stage = 2 AND arc_num >= ?")
L147: project.db.cursor.execute("DELETE FROM director_selections ... ep_num >= ? ...")
L189: project.db.cursor.execute("DELETE FROM anchors WHERE key = 'arcs'")
L315: project.db.cursor.execute("SELECT data FROM state_logs WHERE ep_num = ?", ...)
```

**위험 분석**: `reset_stage_2()`는 `project.db.reset_after(1, commit=False)` 호출 후 위 DELETE들을 실행. `reset_after()` 내부에서 `self._lock` 획득 후 `self.cursor.execute("BEGIN")` 시작. 이후 `_clear_stage2_*()` 호출 시 lock 없이 같은 `self.cursor`를 사용. **같은 트랜잭션 내이므로 원자성은 유지되나**, lock 외부에서 공유 커서 접근은 독스트링 위반이며, 다른 쓰레드가 동시에 같은 커서에 접근하면 문제 발생.

**실제 위험도**: `input()` 게이트가 있어 사용자가 직접 확인해야만 실행되므로, Advisory 병렬 쓰레드와 동시 실행될 가능성은 **매우 낮음**. 코드 스멜 수준.

---

### [XC-DB-003] P3 | get_lore_list_by_category() — 공유 커서 반환값을 변수에 저장하나 실체는 self.cursor

| 필드 | 내용 |
|------|------|
| ID | XC-DB-003 |
| Severity | P3 (코드 스멜) |
| 현상 요약 | `cur = self.cursor.execute(...)` 패턴이 로컬 커서처럼 보이나, 실제로 `self.cursor` 자체를 반환하여 혼동을 유발한다 |
| 코드 근거 | `db_manager.py:1537-1540` — `cur = self.cursor.execute("SELECT * FROM encyclopedia")` 후 `cur.fetchall()`. 여기서 `cur`는 `self.cursor`의 alias. |
| 영향 경계 | 코드 가독성/유지보수성 저하. `self.cursor.execute()`의 반환값은 cursor 자체이므로, `cur.close()` 호출 시 `self.cursor`가 닫히는 위험. 현재 `cur.close()` 호출 없으므로 실질적 문제 없음. |
| 테스트 근거 | N/A |
| 기존 중복 여부 | T1-07 하위 사례 |
| 권장 후속 조치 | `cur = self.conn.cursor()` + `try/finally: cur.close()` 패턴으로 전환. 공수: 10분 |

동일 패턴 다수:
- L1566 `load_anchor()`: `cur = self.cursor.execute(...)`
- L1579 `load_all_anchors()`: `cur = self.cursor.execute(...)`
- L1854 `get_previous_blueprint()`: `cur = self.cursor.execute(...)`
- L1882 `get_latest_state()`: `cur = self.cursor.execute(...)`
- L2264 `get_latest_episode_number()`: `cur = self.cursor.execute(...)`

---

### [XC-DB-004] P3 | Advisory 8쓰레드 DB 접근 — 공유 커서 사용 가능 경로

| 필드 | 내용 |
|------|------|
| ID | XC-DB-004 |
| Severity | P3 (코드 스멜) |
| 현상 요약 | Advisory 병렬 8쓰레드에서 DB를 읽는 경로가 존재하며, 일부 DBManager 메서드가 공유 커서를 사용한다 |
| 코드 근거 | `stage4_interview_round.py:3807` `ThreadPoolExecutor(max_workers=8)`. advisory 메서드들이 `self.ctx.world_state`, `self.ctx.fact_ledger` 등을 참조하며, 이들이 내부적으로 `db.get_*()` 호출 가능. 예: `_advisory_numeric_drift()` → `fact_ledger` → DB read. |
| 영향 경계 | `get_recent_causal_links()` (L1924) 등은 `with self._lock:` + `self.cursor.execute()` 패턴. 8쓰레드가 동시에 이 메서드를 호출하면 RLock이 순차화하지만, 공유 커서의 결과 세트가 쓰레드 간 교차 오염될 수 있다. |
| 테스트 근거 | Advisory 병렬 실행 테스트 미확인 |
| 기존 중복 여부 | 신규 (T1-07 확장) |
| 권장 후속 조치 | Advisory가 호출하는 DB 읽기 메서드를 로컬 커서 패턴으로 전환 우선. 공수: 1시간 |

**상세 분석**: RLock은 같은 쓰레드의 재진입을 허용하지만, **다른 쓰레드 간에는 배타적**. 따라서 8개 Advisory 쓰레드가 동시에 `with self._lock:` + `self.cursor.execute()` 호출 시, lock이 순차화하므로 **쓰레드 간 공유 커서 간섭은 발생하지 않는다**. Lock 획득 → execute → fetchall → Lock 해제 순서가 원자적.

**결론**: RLock 보호로 실제 데이터 오염은 발생하지 않음. 그러나 로컬 커서 사용 시 Lock 점유 시간이 줄어들어 병렬 처리량이 개선될 수 있음. **성능 개선 기회**.

---

## 3. 요약

| ID | Severity | 현상 | 실제 위험 |
|----|----------|------|-----------|
| XC-DB-001 | P2 | 공유/로컬 커서 혼용 재진입 | LOW (DML only) |
| XC-DB-002 | P2 | ProjectService RLock 바이패스 | LOW (input 게이트) |
| XC-DB-003 | P3 | cursor alias 혼동 패턴 | 코드 스멜 |
| XC-DB-004 | P3 | Advisory 쓰레드 공유 커서 | Lock 보호로 안전, 성능 기회 |
