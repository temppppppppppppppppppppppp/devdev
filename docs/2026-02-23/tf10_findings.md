# TF-10 Findings — 데이터 흐름 무결성 감사

> 베이스라인: 2,549 passed, 0 violations (commit `91a87ab`)

---

## 현재 위치

```
Last Completed Round: Round F
Next Round: 완료
Status: 완료
```

---

## 진행 테이블

| Round | 내용 | 상태 | HIGH | MED | LOW | INFO |
|-------|------|------|------|-----|-----|------|
| A | Stage 0 → Stage 2 (arc_data) | ✅ | 0 | 0 | 0 | 2 |
| B | Stage 2 내부 (arc 정제 체인) | ✅ | 0 | 1 | 0 | 1 |
| C | Stage 2 → Stage 3 (blueprint) | ✅ | 0 | 0 | 1 | 1 |
| D | Stage 3 → Stage 4 (원고 컨텍스트) | ✅ | 0 | 1 | 2 | 2 |
| E | NPC 데이터 흐름 | ✅ | 0 | 1 | 0 | 2 |
| F | 검증 체인 데이터 흐름 | ✅ | 0 | 1 | 1 | 2 |

---

## 발견 사항

### Round A
- 체크리스트 판정
  - PASS: Stage0 reverse 경로의 `save_anchor("arcs")` 저장 필드 확인 완료.
  - PASS: Stage2의 `load_anchor("arcs")` 수신 지점 및 소비 필드 확인 완료.
  - WARN: reverse 경로 Bible에는 `plot_roadmap`이 없어 Stage2 `arcs_source`는 빈 배열로 동작.
  - WARN: story/reverse 경로의 Arc 산출 방식이 비대칭(Story는 Stage0에서 arcs anchor 미저장, Reverse는 저장).
- 발견
  - `modules/core/stage0/reverse_expander.py:927`  
    `stub = {"_stub": True, ... "arc_no": arc_no, "volume_no": ..., "ep_start": ep_start, "ep_end": ep_end, "tactical_doc": ..., "key_events": ..., "joint_docs": {}, "state_changes": {}}`  
    - 등급: INFO  
    - 설명: reverse 경로 Arc stub 필수 필드(arc_no/ep_start/ep_end/state_changes 등)는 Stage2 재로딩 전제로 일관됨.
  - `modules/core/stage2_orchestrator.py:121`  
    `arcs_source = bible_root.get("plot_roadmap", [])`  
    `all_refined_arcs = self.ctx.current_project.db.load_anchor("arcs") or []` (`modules/core/stage2_orchestrator.py:140`)  
    - 등급: INFO  
    - 설명: Stage2 입력원이 이원화되어(blueprint 기반 `plot_roadmap` vs DB `arcs`) story/reverse 경로의 스키마 동일성은 구조적으로 성립하지 않음.

### Round B
- 체크리스트 판정
  - PASS: `preflight → validation → finalizer`에서 `refined_arc` 필드 추가/보강 흐름 추적 완료.
  - WARN: 체인 전반이 in-place mutation 중심이라(`dict`/`list` 공유) 단계 간 부수효과 관리가 필요.
  - WARN: `analyst.enrich_raw_block_async()` 반환 스키마와 finalizer 기대 스키마가 엄밀히 일치하지 않음.
- 발견
  - `modules/domain/agents/analyst.py:1163`  
    `if "block_id" not in enriched_result: ...`  
    `if "title" not in enriched_result: ...`  
    - 등급: MEDIUM  
    - 설명: enrich 결과에서 실질 보장 필드가 `block_id/title` 수준이며, finalizer가 기대하는 `joint_docs/status_shadow` 계약이 명시되지 않아 후속 단계가 기본값 주입으로 품질 저하를 흡수함.
  - `modules/core/stage2_finalizer.py:204`  
    `refined_arc["joint_docs"] = enriched_block.get("joint_docs", {})`  
    `refined_arc["status_shadow"] = enriched_block.get("status_shadow", {})`  
    - 등급: INFO  
    - 설명: 상류 스키마 미보장 상태를 finalizer가 placeholder로 복구하는 설계(방어적 처리)로 데이터 흐름은 유지되나, 정보 손실 가능성이 남음.

### Round C
- 체크리스트 판정
  - PASS: Stage3가 읽는 Arc 핵심 필드(`arc_no/ep_start/ep_end`)와 Stage2 저장 스키마가 정합.
  - PASS: `world_state`/`fact_ledger` 초기화 시점 확인 (`WorldStateManager`: L220, `FactLedger`: L237).
  - WARN: Blueprint 필수 필드 검증이 최소 필드 중심이라, 일부 필드는 기본값으로 조용히 보정됨.
- 발견
  - `modules/domain/agents/blueprint_ensemble.py:441`  
    `if "scene_breakdown" not in result or "integrated_scenario" not in result: return None`  
    - 등급: LOW  
    - 설명: 후보 유효성 게이트가 최소 2필드 위주라 `episode_number` 등 스키마 핵심 필드 누락이 조기 차단되지 않고 후단 기본값 보정에 의존.
  - `modules/core/stage3_orchestrator.py:220`  
    `app.world_state = WorldStateManager(app.current_project.db)`  
    `app.fact_ledger = FactLedger(app.current_project.db)` (`modules/core/stage3_orchestrator.py:237`)  
    - 등급: INFO  
    - 설명: Stage3 시작 시 world_state/fact_ledger lazy init이 명시되어 Stage4로의 상태 전달 경로는 확보됨.

### Round D
- 체크리스트 판정
  - WARN: Stage4는 `blueprint`를 DB JSON raw 형태로 수신해 사용하며, 모델 검증 실패 시 원본 유지 경로가 있어 스키마 불일치가 후단으로 전파될 수 있음.
  - PASS: world_state 요약은 `get_summary(max_chars=5000)`로 추출되어 RoundContext→ChiefWriterContext로 직렬화 주입됨.
  - WARN: fact_ledger 요약은 Writer `mandatory_context`에는 주입되지만, Blocking/Continuity 검증용 `_cv_context`에는 동등한 payload가 명시 주입되지 않음.
  - PASS: `arc_data → stage4_context_builder → retrieval(current_arc_no)` 경로로 `arc_no` 전달이 유지됨(TF-9 수정 경로 정상).
- 발견
  - `modules/models/blueprint.py:65`  
    `def validate_blueprint(raw: dict) -> dict:`  
    `... except Exception as e: ... return raw`  
    - 등급: MEDIUM  
    - 설명: Blueprint 검증 실패 시 fail-open으로 원본 dict를 그대로 통과시켜, Stage4 소비 시점까지 스키마 오염이 전파될 수 있음.
  - `modules/core/stage4_context_builder.py:659`  
    `_fl_summary = self.ctx.fact_ledger.to_summary(max_chars=15000)`  
    `_mc_parts.insert(0, _fl_summary)`  
    (`modules/core/stage4_interview_round.py:275`의 `_cv_context`에는 `fact_ledger` 키 없음)  
    - 등급: LOW  
    - 설명: fact_ledger 제약이 Writer 컨텍스트 중심으로만 주입되어, Blocking/Continuity 단계의 구조화 검증 신호는 약함.
  - `modules/validation/blocking_validator_scene_checks.py:52`  
    `if not scene_breakdown or not isinstance(scene_breakdown, dict):`  
    `    return {"check": "required_scenes", "passed": True}`  
    (`modules/validation/blocking_validator_scene_checks.py:120`, `modules/validation/blocking_validator_scene_checks.py:176`도 동일한 스킵 패턴)  
    - 등급: LOW  
    - 설명: Blueprint 씬 메타가 누락되면 핵심 씬/완성도/범위 검사 일부가 통과 처리되어 차단 강도가 낮아질 수 있음.
  - `modules/core/stage4_context_builder.py:536`  
    `_world_state_summary = self.ctx.world_state.get_summary(max_chars=5000)`  
    `return {..., "world_state_summary": _world_state_summary}`  
    (`modules/domain/agents/chief_writer_context.py:209`에서 프롬프트 섹션으로 주입)  
    - 등급: INFO  
    - 설명: world_state 요약은 Stage4 입력에서 Writer 프롬프트까지 문자열 직렬화 경로가 유지됨.
  - `modules/core/stage4_context_builder.py:746`  
    `_arc_no_s4 = arc_data.get("arc_no", None)`  
    `for _retrieved in self._execute_retrieval_plan(_retrieval_plan, arc_no=_arc_no_s4):`  
    (`modules/core/stage4_context_builder.py:198`에서 `current_arc_no=current_arc_no` 사용)  
    - 등급: INFO  
    - 설명: arc_no가 Stage4 retrieval plan 실행부까지 전달되어 아크 범위 검색 필터가 동작함.

### Round E
- 체크리스트 판정
  - PASS: NPC 등록 → 상태 변경 → DB 이력 기록 → Stage4 검증 컨텍스트 참조 체인 확인.
  - WARN: 일반 변경 경로는 append-only를 준수하나, `merge_npc_registry` 병합 경로는 이력 append를 남기지 않아 감사 추적 공백이 발생할 수 있음.
  - PASS: deceased NPC의 Blueprint/원고 재등장은 별도 차단 검사 경로가 존재함.
- 발견
  - `modules/core/db_manager.py:389`  
    `CREATE TABLE IF NOT EXISTS npc_history (... id INTEGER PRIMARY KEY AUTOINCREMENT, ...)`  
    `CREATE INDEX IF NOT EXISTS idx_npc_history_name ...`  
    - 등급: INFO  
    - 설명: NPC 이력은 append-only 테이블(+인덱스)로 분리 저장되어 변경 추적 기반은 갖춰져 있음.
  - `modules/domain/agents/state_tracker_npc.py:530`  
    `def merge_npc_registry(self, other: "StateTracker"):`  
    `... existing.update(filtered)`  
    - 등급: MEDIUM  
    - 설명: 병합 경로는 `_record_change()`를 호출하지 않아 DB `npc_history`에 변화 근거가 남지 않을 수 있음.
  - `modules/domain/agents/state_tracker_npc.py:1232`  
    `def check_dead_npc_in_blueprint(...):`  
    (`modules/domain/agents/state_tracker_npc.py:1331` `check_dead_npc_in_manuscript`)  
    - 등급: INFO  
    - 설명: 사망 NPC 재등장 차단이 Blueprint/원고 양쪽에서 별도 검사로 구현되어 있음.

### Round F
- 체크리스트 판정
  - PASS: 검증 입력 출처는 후보 원고(`candidates`), `blueprint`, `validation_context`(HUD/NPC/시간선 등)로 분리 공급됨.
  - PASS: Stage4 경로에서 Python 검증 결과(`validation_results`)와 경고가 Director 선택 프롬프트에 전달됨.
  - WARN: CRITICAL/MAJOR/MINOR 분류는 프롬프트 스키마에 존재하나, selector 코드의 고정 룰보다는 LLM 산출 `verdict/score`에 간접 반영되는 구조임.
- 발견
  - `modules/validation/continuity_validator.py:113`  
    `if not prev_hud: ... return {"passed": True, "degraded": True, ...}`  
    - 등급: MEDIUM  
    - 설명: prev_hud 누락 시 연속성 검증이 DEGRADED PASS로 종료되어, 입력 누락 상황에서 위반 미검출 가능성이 커짐.
  - `modules/validation/pre_llm_validator.py:127`  
    `# [V60.56] ... 항상 passed=True`  
    `return {"passed": True, ...}`  
    (`modules/validation/validation_orchestrator.py:523`에서 감점 최대 -1 반영)  
    - 등급: LOW  
    - 설명: pre-LLM은 advisory 전용이며 최종 차단력은 제한적이어서, 강한 이상 신호도 본검증 단계 의존도가 큼.
  - `modules/core/stage4_interview_round.py:675`  
    `_director_mc_parts.append("[V66.3] Python 사전 검증 결과 ...")`  
    `director_result = self.ctx.agents["director"].select_and_judge_ensemble(... validation_results=validation_results ...)`  
    - 등급: INFO  
    - 설명: 후보별 검증 경고가 Director 의사결정 입력으로 결합되는 전달 경로가 명확함.
  - `modules/domain/agents/director_prompts.py:129`  
    `"severity": "CRITICAL|MAJOR|MINOR"`  
    (`modules/domain/agents/director_ensemble.py:412` 이후는 `selected/verdict/score` 기반 분기)  
    - 등급: INFO  
    - 설명: 심각도 분류는 프롬프트 지시로 수집되지만, 코드 레벨의 결정 함수는 점수/판정 중심으로 동작함.

---

## 집계

| 등급 | 건수 |
|------|------|
| HIGH | 0 |
| MEDIUM | 4 |
| LOW | 4 |
| INFO | 10 |
| **합계** | **18** |
