# TF-14 Findings 상태 무결성 감사

> Baseline: 2,549 passed, 0 violations (commit `91a87ab`)

---

## 현재 위치

```
Last Completed Round: Round E
Next Round: None
Status: Completed
```

---

## 진행 테이블

| Round | 내용 | 상태 | HIGH | MED | LOW | INFO |
|-------|------|------|------|-----|-----|------|
| A | DB 트랜잭션 원자성 | Completed | 0 | 2 | 0 | 1 |
| B | 롤백 원자성 (auto_backtrack) | Completed | 0 | 2 | 1 | 1 |
| C | NPC 이력 무결성 | Completed | 0 | 2 | 1 | 1 |
| D | world_state / fact_ledger 무결성 | Completed | 0 | 1 | 0 | 1 |
| E | 에피소드 상태 정합 | Completed | 0 | 2 | 1 | 1 |

---

## 발견 사항

### Round A
1. [MED] `commit_full_episode_data`가 Bible/Seeds를 DB 트랜잭션보다 먼저 저장해, 이후 DB Factory 실패 시 부분 커밋 상태가 발생할 수 있다.
   - Evidence: `modules/core/project_manager.py:549`
     - `self.save_v20_anchor("bible", self.master_bible)`
     - `self.sync_and_cleanup_seeds()`
   - Evidence: `modules/core/project_manager.py:559`
     - `db_success = self.db.commit_episode_factory(...)`
   - Evidence: `modules/core/project_manager.py:573`
     - `raise RuntimeError("SQLite Episode Factory 저장 실패")`
   - Why it matters: 에피소드 본문/상태 저장이 실패해도 배경 앵커 데이터가 최신으로 남아 에피소드 단위 원자성이 깨질 수 있다.

2. [MED] 메인 DB 저장과 벡터 저장(`memorize_v20_episode`)이 단일 트랜잭션이 아니며, 벡터 실패 시에도 성공 경로로 반환한다.
   - Evidence: `modules/core/project_manager.py:559`
     - `db_success = self.db.commit_episode_factory(...)`
   - Evidence: `modules/core/project_manager.py:593`
     - `vector_success = memory.memorize_v20_episode(...)`
   - Evidence: `modules/core/project_manager.py:616`
     - `return True  # DB는 성공했으므로 진행`
   - Evidence: `modules/core/vec_memory.py:453`
     - `self._conn.commit()`
   - Why it matters: DB는 성공, 벡터는 실패인 부분 성공을 허용해 검색/회상 경로가 지연 불일치 상태가 될 수 있다.

3. [INFO] 체크리스트의 `safe_commit`/`safe_commit_async` 명칭은 현재 코드에 없고, 실경로는 `commit_full_episode_data` + `commit_episode_factory`로 구성되어 있다.
   - Evidence: `modules/core/project_manager.py:466`
     - `def commit_full_episode_data(...):`
   - Evidence: `modules/core/db_manager.py:1349`
     - `def commit_episode_factory(...):`
   - Why it matters: 감사 체크리스트 명칭과 구현 명칭 사이에 차이가 있어, 추후 점검 문서 업데이트가 필요하다.

### Round B
1. [MED] `reset_project` 경로는 DB 리셋과 draft 파일 삭제 위주이며 벡터 롤백 호출이 직접 포함되지 않는다.
   - Evidence: `modules/core/project_manager.py:705`
     - `def reset_project(self, target_ep) -> None:`
   - Evidence: `modules/core/project_manager.py:707`
     - `self.db.reset_after(target_ep)`
   - Evidence: `modules/core/project_manager.py:712`
     - `for f in self.paths.drafts.glob("*.txt"):`
   - Evidence: `modules/core/vec_memory.py:1202`
     - `def delete_episodes_from(self, target_ep: int) -> int:`
   - Why it matters: 롤백 스텝이 DB/파일 위주로 보이며 벡터 삭제는 별도 경로 의존이라 운영 호출 순서에 따라 누락 위험이 있다.

2. [MED] `DBManager.reset_after`는 롤백 대상에서 `episode_meta`/`episode_fts`/`vec_episodes`를 직접 다루지 않는다.
   - Evidence: `modules/core/db_manager.py:1586`
     - `tables = ["blueprints", "state_logs", "causal_graph", "manuscripts", "martial_tracker"]`
   - Evidence: `modules/core/db_manager.py:1589`
     - `DELETE FROM episode_bibles ...`
   - Evidence: `modules/core/db_manager.py:1590`
     - `DELETE FROM sync_status ...`
   - Evidence: `modules/core/vec_memory.py:1214`
     - `cur.execute("DELETE FROM episode_meta WHERE ep_num >= ?", (target_ep,))`
   - Why it matters: sync 플래그만 초기화되고 실제 벡터/메타가 남으면 롤백 직후 정합성 판단 및 후속 동기화가 혼란스러울 수 있다.

3. [LOW] `reset_after`는 다중 DELETE 중간 실패 시 명시적 보상 로직이 없다.
   - Evidence: `modules/core/db_manager.py:1583`
     - `def reset_after(self, target_ep) -> None:`
   - Evidence: `modules/core/db_manager.py:1587`
     - `for tbl in tables: self.cursor.execute(...)`
   - Evidence: `modules/core/db_manager.py:1604`
     - `self.conn.commit()`
   - Why it matters: 중간 예외 시 일부 테이블만 정리된 상태로 남을 수 있다.

4. [INFO] 체크리스트의 `auto_backtrack_v35`/`rollback_episode` 명칭과 실제 코드 경로는 다르다.
   - Evidence: `modules/core/project_manager.py:705`
     - `def reset_project(self, target_ep) -> None:`
   - Evidence: `modules/core/db_manager.py:1583`
     - `def reset_after(self, target_ep) -> None:`
   - Evidence: `modules/core/vec_memory.py:1202`
     - `def delete_episodes_from(self, target_ep: int) -> int:`
   - Why it matters: 문서와 코드 경로를 맞춰야 운영 점검 시 오해를 줄일 수 있다.

### Round C
1. [MED] `npc_history` append-only 기록은 일부 경로에만 적용되고, 관계/부상/이동/부활 등 여러 업데이트는 기록 테이블에 누락된다.
   - Evidence: `modules/domain/agents/state_tracker_npc.py:94`
     - `def _record_change(...):`
   - Evidence: `modules/domain/agents/state_tracker_npc.py:108`
     - `db.insert_npc_change(...)`
   - Evidence: `modules/domain/agents/state_tracker_npc.py:770`
     - `self.tracker.npc_registry[npc]["relation_to_protag"] = to_rel`
   - Evidence: `modules/domain/agents/state_tracker_npc.py:819`
     - `self.tracker.npc_registry[npc_name]["injury"] = state`
   - Evidence: `modules/domain/agents/state_tracker_npc.py:867`
     - `self.tracker.npc_registry[npc_name]["location"] = to_loc`
   - Evidence: `modules/domain/agents/state_tracker_npc.py:1210`
     - `npc["status"] = "alive"`
   - Why it matters: 변경 이력 조회가 일부 필드만 수집되어 롤백 근거가 불완전해진다.

2. [MED] 사망 NPC 상태 변경 차단이 등록 경로에서 강제되지 않아 dead NPC의 무장/레벨/부상/위치 갱신이 가능하다.
   - Evidence: `modules/domain/agents/state_tracker_npc.py:169`
     - `if npc_name not in self.tracker.npc_registry: ...`
   - Evidence: `modules/domain/agents/state_tracker_npc.py:180`
     - `npc["weapon"] = weapon`
   - Evidence: `modules/domain/agents/state_tracker_npc.py:185`
     - `npc["level"] = level`
   - Evidence: `modules/domain/agents/state_tracker_npc.py:819`
     - `self.tracker.npc_registry[npc_name]["injury"] = state`
   - Evidence: `modules/domain/agents/state_tracker_npc.py:867`
     - `self.tracker.npc_registry[npc_name]["location"] = to_loc`
   - Why it matters: 생사 상태와 속성 변경이 충돌하면 상태 레지스트리 자체 무결성이 손상된다.

3. [LOW] `bind_db()` 미호출 시 NPC 변경 기록이 조용히 누락되고, 기본 생성 경로(`create_tracker_from_arcs`)는 DB 바인딩을 강제하지 않는다.
   - Evidence: `modules/domain/agents/state_tracker.py:1029`
     - `def bind_db(self, db_manager) -> None:`
   - Evidence: `modules/domain/agents/state_tracker_npc.py:106`
     - `db = getattr(self.tracker, "_db", None)`
   - Evidence: `modules/domain/agents/state_tracker_npc.py:107`
     - `if db and hasattr(db, "insert_npc_change"):`
   - Evidence: `modules/domain/agents/state_tracker.py:1511`
     - `master_tracker = StateTracker()`
   - Why it matters: 기능은 동작해도 감사 추적 로그가 비어버릴 수 있다.

4. [INFO] `npc_history` 저장 자체는 append-only로 구현되어 기존 이력 훼손 위험은 낮다.
   - Evidence: `modules/core/db_manager.py:1826`
     - `"""... append-only 삽입"""`
   - Evidence: `modules/core/db_manager.py:1830`
     - `INSERT INTO npc_history (...) VALUES (...)`
   - Why it matters: 기록 경로만 보완되면 변경 불변성은 확보된다.

### Round D
1. [MED] `ContinuityValidator`는 `world_state`/`fact_ledger`를 직접 참조하지 않고 `validation_context` 주입값(`prev_hud`, `npc_personalities`, `npc_history`, `time_warnings`)에 의존한다.
   - Evidence: `modules/validation/continuity_validator.py:72`
     - `def validate(..., validation_context: dict, prev_hud: dict | None = None)`
   - Evidence: `modules/validation/continuity_validator.py:107`
     - `prev_hud = validation_context.get("prev_hud") or validation_context.get("martial_hud")`
   - Evidence: `modules/validation/continuity_validator.py:750`
     - `'npc_personalities': ..., 'npc_history': ...`
   - Evidence: `modules/validation/continuity_validator.py:917`
     - `'time_warnings': [...]`
   - Why it matters: FactLedger/WorldState가 있어도 검증기가 직접 반영하지 않아 상위 조립부의 context 구성 품질에 결과가 좌우된다.

2. [INFO] Stage3 초기화 실패 시 `world_state`/`fact_ledger`를 `None`으로 두고 Stage4가 null-guard로 진행하도록 되어 런타임 중단은 회피된다.
   - Evidence: `modules/core/stage3_orchestrator.py:227`
     - `app.world_state = None`
   - Evidence: `modules/core/stage3_orchestrator.py:248`
     - `app.fact_ledger = None`
   - Evidence: `modules/core/stage3_orchestrator.py:90`
     - `ctx.world_state = getattr(self.app, "world_state", None)`
   - Evidence: `modules/core/stage4_context.py:76`
     - `world_state=None, fact_ledger=None`
   - Evidence: `modules/core/stage4_context_builder.py:625`
     - `if self.ctx.world_state:`
   - Evidence: `modules/core/stage4_context_builder.py:657`
     - `if self.ctx.fact_ledger:`
   - Why it matters: Stage3 유틸리티 실패가 Stage4 전체 중단으로 직결되지 않고, null-safe 경로로 운영 지속이 가능하다.

### Round E
1. [MED] Stage4 PASS 후 manuscript/DB commit이 먼저 확정되고, 이후 `character_voice`/`foreshadow`/`episode_bible`/`world_state`/`fact_ledger` 실패는 비치명 처리되어 부분 갱신이 발생할 수 있다.
   - Evidence: `modules/core/stage4_post_processor.py:119`
     - `save_manuscript(...)`
   - Evidence: `modules/core/stage4_post_processor.py:125`
     - `self.ctx.current_project.db.conn.commit()`
   - Evidence: `modules/core/stage4_post_processor.py:275`
     - `self.ctx.character_voice.analyze_manuscript(...)`
   - Evidence: `modules/core/stage4_post_processor.py:282`
     - `self.ctx.foreshadow_tracker.auto_detect_from_manuscript(...)`
   - Evidence: `modules/core/stage4_post_processor.py:430`
     - `save_episode_bible(...)` (실패 비치명)
   - Evidence: `modules/core/stage4_post_processor.py:537`
     - `except Exception as _meta_err: ...`
   - Evidence: `modules/core/stage4_post_processor.py:728`
     - `return True`
   - Why it matters: N화의 PASS가 이미 본문 DB에 확정된 뒤 부가 상태 업데이트 실패가 발생하면 N+1 시작 시점 정합성이 흔들릴 수 있다.

2. [MED] 롤백 경로 `reset_after`가 `character_voice`/`foreshadow` 테이블을 정리하지 않아 롤백 후 미래 에피소드 흔적이 남을 수 있다.
   - Evidence: `modules/core/db_manager.py:1586`
     - `tables = ["blueprints", "state_logs", "causal_graph", "manuscripts", "martial_tracker"]`
   - Evidence: `modules/core/character_voice.py:448`
     - `INSERT OR REPLACE INTO character_voice(...)`
   - Evidence: `modules/core/foreshadow_tracker.py:428`
     - `DELETE FROM foreshadow`
   - Evidence: `modules/core/stage4_post_processor.py:278`
     - `self.ctx.character_voice.save_to_db(...)`
   - Evidence: `modules/core/stage4_post_processor.py:286`
     - `self.ctx.foreshadow_tracker.save_to_db(...)`
   - Why it matters: main 데이터만 롤백되고 보조 추적기가 남으면 N+1 프롬프트에 미래 정보가 유입될 수 있다.

3. [LOW] `character_voice`/`foreshadow` 모듈에는 `target_ep` 기반 rollback API가 없고, 복구는 DB 정리 + 재로딩 절차에 의존한다.
   - Evidence: `modules/core/character_voice.py:420`
     - `def save_to_db(self, db) -> None:`
   - Evidence: `modules/core/character_voice.py:503`
     - `def load_from_db(self, db) -> int:`
   - Evidence: `modules/core/character_voice.py:569`
     - `def clear(self) -> None:`
   - Evidence: `modules/core/foreshadow_tracker.py:419`
     - `def save_to_db(self, db) -> None:`
   - Evidence: `modules/core/foreshadow_tracker.py:527`
     - `def load_from_db(self, db) -> int:`
   - Evidence: `modules/core/foreshadow_tracker.py:678`
     - `def clear(self) -> None:`
   - Why it matters: rollback 품질은 외부 오케스트레이션 정확도에 크게 의존한다.

4. [INFO] `character_voice`는 `last_seen_episode`를 갱신하고 Writer 주입 시 최신 에피소드 순으로 정렬해 기본 에피소드 순서를 유지한다.
   - Evidence: `modules/core/character_voice.py:249`
     - `profile.last_seen_episode = ep_num`
   - Evidence: `modules/core/character_voice.py:366`
     - `sorted(..., key=lambda x: self.profiles[x].last_seen_episode, reverse=True)`
   - Why it matters: 정상 선형 생성 흐름에서는 최신 화자 톤이 우선 반영된다.

---

## 집계

| 등급 | 건수 |
|------|------|
| HIGH | 0 |
| MEDIUM | 9 |
| LOW | 3 |
| INFO | 5 |
| **합계** | **17** |