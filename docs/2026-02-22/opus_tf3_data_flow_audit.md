# Opus TF3: 전체 파이프라인 데이터 흐름 무결성 감사 보고서

> 감사일: 2026-02-22
> 감사 범위: Stage 0 -> Stage 2 -> Stage 3 -> Stage 4 -> DB 저장
> 초점: Stage 간 경계에서의 누락/변형/불일치

---

## 1. Stage 0 -> Stage 2 경계

### 1.1 데이터 흐름 경로

Stage 0 산출물(Bible, Treatment, StyleGuide, PresetState)은 두 경로로 DB에 저장된다.

**경로 A: `stage01_helpers.py` `_s0_save_results()` (L452-494)**
```
bible -> project.save_v20_anchor("bible", bible)
preset_state -> project.save_v20_anchor("preset_state", json.loads(preset_state))
style_guide -> project.save_v20_anchor("style_guide", stage0_manager.style_guide.to_dict())
treatment -> JSON 파일로 저장 (treatment_generated.json)
```

**경로 B: `stage01_helpers.py` `phase_0_recovery()` (L30-181) - 기존 파일 방식**
```
force_sync_v25_dna(bible_file, treatment_file) -> 파일 로드 + Bible에 plot_roadmap 주입
bible["protagonist_config"] = {...}
project.save_v20_anchor("bible", bible)
```

### 1.2 Stage 2에서의 로드

`stage2_orchestrator.py` L107-121:
```python
self.ctx.current_project.master_bible = self.ctx.current_project.db.load_anchor("bible")
bible_data = self.ctx.current_project.master_bible
bible_root = bible_data.get("MasterBible", bible_data)
arcs_source = bible_root.get("plot_roadmap", [])
```

### 1.3 발견 사항

| ID | 심각도 | 항목 | 설명 |
|----|--------|------|------|
| S0-1 | **MEDIUM** | Treatment 파일 vs DB 불일치 | Treatment는 JSON 파일(`treatment_generated.json`)로만 저장되고, DB anchor로는 저장되지 않는다. 대신 `plot_roadmap`이 Bible 내부에 주입된다. Stage 2는 `bible_root.get("plot_roadmap", [])`로 읽는다. 이 구조는 의도적이지만, Treatment 파일과 Bible 내 plot_roadmap이 별도 시점에 수정되면 동기화가 깨질 수 있다. |
| S0-2 | **LOW** | PresetState 저장/로드 비대칭 | `_s0_save_results()`에서 preset_state를 `json.loads(preset_state)` (문자열->dict 변환)하여 저장한다. Stage 2에서는 `self.ctx.preset_registry`로 접근하는데, 이는 `from_app(app)`에서 `app.preset_registry`를 직접 참조한다. DB에서 preset_state를 리로드하는 경로는 `StageZeroManager.load_state()`뿐이며, 일반 실행에서는 DB -> preset_registry 자동 복원이 없다. `_load_from_db()`는 bible/volumes/arcs만 복원한다. **신규 세션에서 preset_registry가 None일 수 있다.** |
| S0-3 | **LOW** | StyleGuide 저장 포맷 다양성 | 역설계 경로(`_s0_handle_reverse_engineering`)에서는 `json.loads(style_guide.to_json())`으로, 레퍼런스 분석 경로(`_s0_handle_style_analysis`)에서도 동일한 방식을 사용하지만, 컨셉 생성 경로(`_s0_save_results`)에서는 `.to_dict()`를 사용한다. `to_json()`과 `to_dict()`가 동일한 결과를 보장하는지 확인 필요. |
| S0-4 | **INFO** | protagonist_config 전달 무결 | protagonist_config는 Bible 내 `MasterBible.protagonist_config`에 주입되며, Stage 2(L128), Stage 3(`_bp_protagonist_config` L316-319), Stage 4(L680-703)에서 모두 동일한 경로 `bible_root.get("protagonist_config", {})`로 읽는다. 일관적 구조. |

---

## 2. Stage 2 -> Stage 3 경계

### 2.1 데이터 흐름 경로

Stage 2 산출물은 **Arc 데이터**(리스트 of dict)로 DB anchor "arcs"에 저장된다.

**저장**: `stage2_finalizer.py` L312:
```python
self.ctx.current_project.save_v20_anchor("arcs", all_refined_arcs)
```

**Pydantic 검증 게이트**: `stage2_finalizer.py` L307:
```python
refined_arc = validate_arc(refined_arc)  # [Step2] Pydantic ingress+egress
```

**로드**: Stage 3는 `self.ctx.current_project.arcs`를 참조 (`project_manager.py` L144):
```python
self.arcs = anchors.get("arcs") if isinstance(anchors.get("arcs"), list) else []
```

### 2.2 Arc -> Stage 3 핵심 필드 추적

Stage 3의 `_process_single_episode()` (L280):
```python
arc_idx, arc_data = ctx.get_arc_context_for_episode(working_ep)
```

필요 필드와 실제 사용:

| 필드 | ArcData Pydantic 모델 | Stage 3 사용 여부 | 보장 여부 |
|------|----------------------|------------------|----------|
| `arc_no` | **필수** (int) | O (L297) | Pydantic 검증으로 보장 |
| `ep_start` | **필수** (int) | O (L285-290) 명시적 None 체크 | Pydantic 검증으로 보장 |
| `ep_end` | **필수** (int) | O (L96, 간접) | Pydantic 검증으로 보장 |
| `tactical_doc` | 기본값 `""` | O (Stage 4에서 주 사용) | 빈 문자열 가능 (비차단) |
| `state_constraints` | 기본값 `{}` | O (간접, entity_registry) | 빈 dict 가능 (비차단) |
| `foreshadowings` | `state_constraints.foreshadowings` | O (간접) | StateConstraints에서 기본 `[]` |

### 2.3 발견 사항

| ID | 심각도 | 항목 | 설명 |
|----|--------|------|------|
| S2-1 | **LOW** | Pydantic 검증 graceful degradation | `validate_arc()`(arc.py L206-216)는 검증 실패 시 원본 dict를 그대로 반환한다. 이는 의도적 설계이지만, 필수 필드(`arc_no`, `ep_start`, `ep_end`)가 누락된 불량 Arc가 DB에 저장될 수 있음을 의미한다. Stage 3의 `ep_start_val is None` 체크(L286)가 이를 방어한다. |
| S2-2 | **INFO** | Arc 데이터 직렬화 무손실 | Arc는 `json.dumps(data_dict)`로 저장되고 `json.loads(row["data"])`로 로드된다. `project_manager.py`의 `save_v20_anchor("arcs", ...)`은 `db.save_anchor()`를 호출하며, 이는 `json.dumps(data, ensure_ascii=False)`를 사용한다. Pydantic 모델의 `extra="allow"` 설정으로 LLM이 추가한 커스텀 키도 보존된다. 직렬화 손실 없음. |
| S2-3 | **INFO** | validate_arc_data_fields 방어 | Stage 3 L293-295에서 `ctx.validate_arc_data_fields(arc_data, arc_idx)`로 추가 검증. 이 콜백이 None이면 arc_data를 그대로 사용 (L294 조건문). |

---

## 3. Stage 3 -> Stage 4 경계

### 3.1 데이터 흐름 경로

Stage 3 산출물은 **Blueprint**(dict)로 DB blueprints 테이블에 저장된다.

**저장**: `stage3_orchestrator.py` L572:
```python
ctx.current_project.save_episode_blueprint(working_ep, blueprint)
```
-> `project_manager.py` L273-277:
```python
def save_episode_blueprint(self, ep_num, data):
    self.db.save_blueprint(ep_num, data)
```
-> `db_manager.py` L1087-1093:
```python
serialized = json.dumps(data_dict, ensure_ascii=False)
self.cursor.execute("INSERT OR REPLACE INTO blueprints (ep_num, data) VALUES (?, ?)", ...)
```

**로드**: Stage 4 L326:
```python
blueprint = self.ctx.current_project.get_blueprint(next_ep)
```
-> `project_manager.py`:
```python
def get_blueprint(self, ep_num):
    return self.db.get_blueprint(ep_num)
```
-> `db_manager.py` L626-641: `json.loads(row["data"])`

### 3.2 Blueprint 필수 필드 추적

Stage 4의 `chief_writer_context.py` L96-103에서 핵심 사용:
```python
scenes = blueprint.get("scene_breakdown", {})
if scenes:
    scene_breakdown = json.dumps(scenes, ensure_ascii=False, indent=2)
integrated = blueprint.get("integrated_scenario", "")
```

| 필드 | Blueprint Pydantic 모델 | Stage 4 사용 | 보장 여부 |
|------|------------------------|-------------|----------|
| `scene_breakdown` | 기본값 `{}` (dict) | **핵심** (CW 프롬프트) | `.get({})` 폴백으로 빈 dict 안전 |
| `integrated_scenario` | 기본값 `""` (str) | **핵심** (CW 프롬프트) | `.get("")` 폴백으로 빈 문자열 안전 |
| `pacing_notes` | 기본값 `""` | 선택적 | 안전 |
| `target_beat` | 기본값 `""` | 선택적 | 안전 |
| `relationship_changes` | 기본값 `[]` | 선택적 | 안전 |
| `episode_number` | 기본값 `0` | 간접 | 저장 시 ep_num으로 DB PK 사용 |
| `_stage3_meta` | 동적 추가 (L549-556) | Stage 4에서 quality_risk 참조 | 없으면 무시 |
| `quality_gate_failed` | 동적 추가 (L555) | Stage 4에서 참조 | 없으면 `.get()` 안전 |

### 3.3 발견 사항

| ID | 심각도 | 항목 | 설명 |
|----|--------|------|------|
| S3-1 | **MEDIUM** | Blueprint Pydantic 검증도 graceful degradation | `validate_blueprint()`(blueprint.py L65-75)는 실패 시 원본 dict 반환. `blueprint_ensemble.py` L396에서 `scene_breakdown`과 `integrated_scenario` 존재를 체크하지만, 이 체크를 통과한 후 Pydantic 검증이 실패해도 원본이 그대로 저장된다. Stage 4에서 `.get()` 폴백으로 방어되므로 크래시는 없지만, **scene_breakdown이나 integrated_scenario가 빈 상태로 Stage 4에 도달하면 빈 프롬프트가 CW에 전달된다.** |
| S3-2 | **LOW** | Blueprint JSON 직렬화 왕복 무손실 | `json.dumps()` -> DB TEXT -> `json.loads()`로 완전한 왕복. Blueprint의 모든 키가 보존된다. `_stage3_meta` 같은 동적 추가 키도 DB에 함께 저장된다. |
| S3-3 | **INFO** | Blueprint NULL data 방어 | `db_manager.py` L637에서 `json.loads(row["data"])`에 `TypeError` 방어가 있어, DB에 NULL이 저장되어도 크래시하지 않고 None을 반환한다. |

---

## 4. Stage 4 -> DB 원자적 저장

### 4.1 데이터 흐름 경로

Stage 4 PASS 결과의 DB 저장은 `stage4_post_processor.py` `process_pass_result()`에서 수행된다.

### 4.2 저장 순서와 원자성 분석

```
[Block 1] 원고 + HUD (L117-153) -- 자체 트랜잭션
  save_manuscript(ep_num, title, content)
  update_martial_tracker(ep_num, state_updates)
  conn.commit()
  -- 실패 시: conn.rollback() -> return False (집필 중단)

[Block 2] 벡터 메모리 (L216-258) -- 비차단, 독립
  memory.memorize_v20_episode(...)
  -- 실패 시: 로깅만, 계속 진행

[Block 3] Manager LLM 정산 (L162-448) -- 비차단, 독립
  bible_delta 구성 -> save_episode_bible(next_ep, bible_delta)
  state_log 저장 -> save_state_log_with_summary(next_ep, state_log_data, summary)
  -- 실패 시: 에피소드 진행 유지

[Block 4] 에피소드 연결고리 (L453-467) -- 비차단, 독립
  save_anchor(f"chain_link_{next_ep}", _chain_link)
  -- 실패 시: 로깅만

[Block 5] WorldState + FactLedger (L469-513) -- 원자적 트랜잭션
  with db.transaction():
      world_state.update_from_state_changes(next_ep, state_changes)
      world_state.save()  # save_anchor("world_state", ...)
      fact_ledger.update_from_state_changes(next_ep, state_changes)
      fact_ledger.update_from_bible_delta(next_ep, bible_delta)
      fact_ledger.save()  # save_anchor("fact_ledger", ...)
  -- 실패 시: 트랜잭션 롤백, 비차단

[Block 6] 만족도 태그 + 호흡 분석 (L515-555) -- 비차단
  save_satisfaction_tag(next_ep, tag)
  save_pacing_record(next_ep, pacing_data)
```

### 4.3 발견 사항

| ID | 심각도 | 항목 | 설명 |
|----|--------|------|------|
| S4-1 | **HIGH** | Block 1과 Block 3 간 원자성 미보장 | 원고(Block 1)는 `conn.commit()`으로 즉시 커밋되지만, `bible_delta`(Block 3)는 별도로 저장된다. Block 1 성공 + Block 3 실패 시 **원고는 저장되었으나 episode_bible(설정 변화 기록)은 누락**되는 부분 실패 상태가 발생한다. 이는 의도적 설계(원고가 최우선)이지만, 이후 `get_cumulative_bible()`이 해당 화의 설정 변화를 놓치게 된다. |
| S4-2 | **MEDIUM** | bible_delta 구성 실패 시 전체 Block 3 스킵 | L447의 `except Exception`에서 Block 3 전체가 `try-except`로 감싸져 있어, Manager LLM 호출 실패 시 **bible_delta, state_log, knowledge_map** 모두 저장되지 않는다. 원고만 남는 "고아 에피소드"가 발생할 수 있다. |
| S4-3 | **MEDIUM** | WorldState/FactLedger 원자성 조건부 | Block 5의 `db.transaction()`은 `_meta_db`가 None이면 `_nullcontext()`를 사용한다(L474). 이 경우 WorldState.save()와 FactLedger.save()가 각각 독립적으로 commit하므로, WorldState 성공 + FactLedger 실패 시 불일치가 발생할 수 있다. 다만, `_meta_db`가 None인 경우는 `current_project.db`가 없는 비정상 상태에서만 발생하므로 실무적 위험은 낮다. |
| S4-4 | **LOW** | bible_delta 사전 초기화 | L163에서 `bible_delta = None`으로 초기화되어 있어, Block 3가 예외로 스킵되면 Block 5의 `fact_ledger.update_from_bible_delta(next_ep, bible_delta)`가 `bible_delta=None`으로 호출된다. L502에서 `if bible_delta:` 가드가 있어 크래시는 방지되지만, FactLedger에 bible_delta 정보가 유실된다. |
| S4-5 | **INFO** | NPC 이력 저장 경로 | `npc_history` 테이블에 직접 쓰는 코드는 `db_manager.py` L1656-1664의 `record_npc_change()`이다. Stage 4 post-processor에서는 직접 호출하지 않는다. NPC 이력은 **HUD 업데이트 시** Director의 `on_approve_workflow()` 내부에서 간접적으로 기록되거나, Stage 2의 StateTracker에서 기록된다. |

---

## 5. DI Context 슬롯 None 분석

### 5.1 Stage2Context (44슬롯)

**필수 5종**: `ui`, `current_project`, `agents`, `sys`, `state_tracker`

`from_app()` (L203-253)에서 `getattr(app, ..., None)` 패턴을 사용한다.

| 슬롯 | None 가능성 | 하류 영향 |
|------|------------|----------|
| `state_tracker` | **높음** (Stage 0/1 직후 첫 실행 시) | L148-151에서 `self.ctx.state_tracker is None` 체크로 재초기화. 안전. |
| `semantic_plot_guard` | 중간 (V50 모듈 미설치 시) | 사용처에서 `if self.ctx.semantic_plot_guard:` 가드. 안전. |
| `failure_learner` | 중간 | 동일 패턴. 안전. |
| `stage2_optimizer` | 중간 | 동일 패턴. 안전. |
| `arc_draft_validator` | 중간 | 동일 패턴. 안전. |
| `stage_rejection_history` | **높음** (초기 None) | L409에서 `if self.ctx.stage_rejection_history:` 가드. 안전. |

**콜백 21종**: 모두 `getattr(app, "_method_name", None)` 패턴.

| 콜백 | None 시 위험 | 방어 |
|------|-------------|------|
| `audit_event` | 감사 기록 누락 | L259 `self.ctx.audit_event(...)` 직접 호출 -- **None이면 TypeError**. 그러나 이 시점에서 app에 항상 존재하므로 실무상 안전. |
| `safe_commit_async` | DB 커밋 실패 | L314에서 호출하므로 None이면 예외 발생. `from_app()`에서 항상 바인딩되므로 실무상 안전. |

### 5.2 Stage3Context (19슬롯)

**필수 2종**: `ui`, `current_project`

| 슬롯 | None 가능성 | 하류 영향 |
|------|------------|----------|
| `agents` | 매우 낮음 | L350 등에서 직접 접근. None이면 TypeError. `from_app()`에서 항상 바인딩. |
| `state_tracker` | **높음** | L89에서 `ctx.state_tracker = getattr(self.app, "state_tracker", None)`으로 lazy init 후 동기화. `_init_state_tracker_if_needed()`가 실패하면 None 유지. `_get_entity_registry()` L350에서 None 체크 없이 사용하지 않음 -- 실제로는 `ctx.agents` 존재 체크로 간접 방어. |
| `validate_arc_data_fields` | 중간 | L293에서 직접 `ctx.validate_arc_data_fields(arc_data, arc_idx)` 호출. **None이면 TypeError.** 그러나 `from_app()`에서 바인딩. |
| `safe_commit` | **주의** | L574에서 `callable(ctx.safe_commit)` 체크(S3-N-P1-3 패치). 안전. |
| `audit_event` | **주의** | L271에서 `callable(ctx.audit_event)` 체크. 안전. |
| `validate_blueprint_integrity` | 중간 | L560에서 `callable(ctx.validate_blueprint_integrity)` 체크. 안전. |

### 5.3 Stage4Context (24슬롯)

**필수 5종**: `ui`, `current_project`, `agents`, `sys`, `state_tracker`

| 슬롯 | None 가능성 | 하류 영향 |
|------|------------|----------|
| `memory` | 중간 (VecMemory 미설치) | L246 `if self.ctx.memory and self.ctx.memory.is_operational():`. 안전. |
| `world_state` | **높음** (V68 lazy init 실패 시) | L477 `if self.ctx.world_state:`. 안전. |
| `fact_ledger` | **높음** (V68 lazy init 실패 시) | L498 `if self.ctx.fact_ledger:`. 안전. |
| `diversity_engine` | 중간 | L415 `if self.ctx.diversity_engine:`. 안전. |
| `pacing_analyzer` | 중간 | L534 조건부 사용. 안전. |
| `conditional_modules` | 기본값 `{}` | `get_module()` 메서드로 안전 접근. |

### 5.4 발견 사항

| ID | 심각도 | 항목 | 설명 |
|----|--------|------|------|
| DI-1 | **LOW** | Stage2Context.audit_event 직접 호출 | `stage2_orchestrator.py` L258에서 `self.ctx.audit_event(...)`를 직접 호출한다. `from_app()`에서 `getattr(app, "_audit_event", None)`으로 바인딩하므로, `app._audit_event`가 존재하지 않으면 None이 되어 `TypeError: 'NoneType' object is not callable` 발생. 현재 `SovereignApp`에는 항상 `_audit_event`가 존재하므로 실무적 위험은 없으나, 테스트에서 mock 없이 Stage2Context를 생성하면 크래시할 수 있다. |
| DI-2 | **INFO** | Stage3Context의 validate_arc_data_fields | `callable()` 체크 없이 직접 호출(L293). `from_app()`에서 항상 바인딩되므로 안전하지만, 독립 테스트 시 주의 필요. |
| DI-3 | **INFO** | 전반적 None 방어 우수 | Stage 3/4의 대부분의 선택적 슬롯에서 `callable()` 또는 `if x:` 체크가 적용되어 있다. S3-N-P1-3 패치로 Stage 3의 콜백 None 방어가 체계적으로 적용됨. |

---

## 6. DB 스키마 vs 코드 일치성

### 6.1 DDL 테이블 목록 (db_manager.py `_boot_db()`)

| # | 테이블명 | PK | 사용 여부 | 비고 |
|---|---------|-----|----------|------|
| 1 | `sync_status` | ep_num | O | 벡터 동기화 상태 |
| 2 | `surgery_logs` | id (AUTO) | O | 수술 기록 |
| 3 | `anchors` | key (TEXT) | **핵심** | Bible, arcs, volumes, style_guide 등 모든 앵커 |
| 4 | `blueprints` | ep_num | **핵심** | Stage 3 산출물 |
| 5 | `state_logs` | ep_num | O | 에피소드 상태 로그 + summary |
| 6 | `causal_graph` | id (AUTO) | O | 인과관계 링크 |
| 7 | `karma_status` | npc_name | O | NPC 카르마 |
| 8 | `manuscripts` | ep_num | **핵심** | Stage 4 원고 |
| 9 | `reflexion_memory` | pattern_type | O | 과거 실패 패턴 |
| 10 | `martial_tracker` | ep_num | O | HUD 15대 지표 |
| 11 | `seeds` | seed_id | O | 복선 관리 |
| 12 | `encyclopedia` | id (AUTO), UNIQUE(item) | O | 로어 백과 |
| 13 | `episode_bibles` | ep_num | O | 화별 설정 변화 |
| 14 | `npc_history` | id (AUTO) | O | NPC 변경 이력 |
| 15 | `episode_sentence_hashes` | (episode_number, sentence_hash) | O | 크로스 에피소드 반복 |
| 16 | `episode_satisfaction_tags` | ep_num | O | 만족도 태그 |
| 17 | `director_selections` | id (AUTO) | O | Director 선택 기록 |
| 18 | `cost_log` | id (AUTO) | O | 비용 추적 |
| 19 | `vec_episodes` | (VIRTUAL) | O (조건부) | sqlite-vec 미설치 시 스킵 |
| 20 | `episode_meta` | ep_num | O | 벡터 메모리 메타 |
| 21 | `episode_pacing` | ep_num | O | 호흡 분석 |

### 6.2 발견 사항

| ID | 심각도 | 항목 | 설명 |
|----|--------|------|------|
| DB-1 | **INFO** | episode_bibles 마이그레이션 안전 | `causal_links`, `karma_matrix`, `knowledge_map` 3개 컬럼은 ALTER TABLE로 추가되며, L316에서 "duplicate column"/"already exists" 외 에러만 재발생. 안전한 마이그레이션. |
| DB-2 | **INFO** | reset_after() 포괄적 정리 | `reset_after()` (L1430-1452)에서 21개 테이블 중 `reflexion_memory`, `encyclopedia`, `cost_log`, `episode_meta`, `vec_episodes`를 제외하고 롤백한다. `reflexion_memory`는 시간 독립적 학습 데이터이므로 유지가 적절. `encyclopedia`는 주석에 "별도 정책 필요"로 명시. `episode_meta`와 `vec_episodes`는 벡터 데이터로, 롤백 시 정리되지 않아 **검색 결과에 삭제된 에피소드 정보가 남을 수 있다.** |
| DB-3 | **LOW** | episode_meta/vec_episodes 롤백 누락 | `reset_after()`에서 `episode_meta`와 `vec_episodes`를 정리하지 않는다. 에피소드 롤백 후 벡터 검색 시 삭제된 에피소드의 요약/임베딩이 반환될 수 있다. `vec_episodes`는 가상 테이블이므로 일반 DELETE가 안 될 수 있고, `episode_meta`는 일반 테이블이므로 정리 가능. |
| DB-4 | **INFO** | delete_episode_bibles_after 분리 호출 | L892-902에서 `self.cursor` (레거시)를 직접 사용. 대부분의 다른 메서드는 로컬 커서를 사용하는데, 이 메서드만 레거시 패턴. 기능에는 문제 없으나 스레드 안전성 면에서 비일관적. |
| DB-5 | **INFO** | `commit_episode_factory` vs Stage 4 분리 저장 | `commit_episode_factory()`는 원자적 트랜잭션으로 7개 하위 테이블을 한 번에 저장하는 메서드이지만, **Stage 4 post-processor에서는 사용하지 않는다.** Stage 4는 Block 1~6을 개별적으로 저장한다. `commit_episode_factory()`는 레거시 호환용으로 보인다. 이 불일치는 의도적이지만, Stage 4가 `commit_episode_factory()`를 사용하면 원자성이 더 강해질 수 있다. |

---

## 7. 종합 위험 평가

### 7.1 심각도별 분류

| 심각도 | 건수 | 항목 |
|--------|------|------|
| **HIGH** | 1 | S4-1 (원고와 bible_delta 간 원자성 미보장) |
| **MEDIUM** | 3 | S0-1 (Treatment 파일/DB 이중 관리), S3-1 (Blueprint 빈 필드 전달), S4-2 (Block 3 전체 스킵), S4-3 (WorldState/FactLedger 조건부 원자성) |
| **LOW** | 5 | S0-2 (preset_registry 미복원), S0-3 (StyleGuide 포맷 다양성), S2-1 (Pydantic graceful degradation), S4-4 (bible_delta None), DB-3 (episode_meta 롤백 누락) |
| **INFO** | 10 | 나머지 |

### 7.2 가장 중요한 데이터 흐름 위험 3건

**1. [S4-1] 원고와 메타데이터 간 원자성 미보장**
- **위치**: `stage4_post_processor.py` Block 1 vs Block 3
- **시나리오**: Manager LLM 호출 실패(타임아웃, API 에러) 시 원고는 DB에 있지만 episode_bible이 없는 "고아 에피소드" 발생
- **영향**: `get_cumulative_bible()`이 해당 화의 아이템 획득/NPC 사망/관계 변화를 놓침 -> 이후 화의 연속성 컨텍스트 불완전
- **현재 방어**: 의도적 설계 (원고 최우선 원칙). 재실행 시 Manager가 누락분을 재정산하지는 않음
- **권고**: 고아 에피소드 감지 쿼리(`manuscripts LEFT JOIN episode_bibles WHERE episode_bibles.ep_num IS NULL`) 추가 고려

**2. [S4-2] Manager LLM 실패 시 전체 Block 3 유실**
- **위치**: `stage4_post_processor.py` L447 `except Exception`
- **시나리오**: ThreadPoolExecutor에서 Manager LLM 호출이 예외 발생 시 bible_delta, state_log, causal_links 모두 유실
- **영향**: S4-1과 동일하지만, state_log(상태 로그)까지 유실되어 `get_latest_state()` 결과에 gap 발생
- **현재 방어**: 비차단 설계로 에피소드 진행은 유지. 벡터 메모리(Block 2)는 별도로 저장되므로 시맨틱 검색은 유지
- **권고**: Manager 실패 시 최소한의 bible_delta (빈 상태라도)를 저장하여 gap 방지

**3. [DB-3] 에피소드 롤백 시 벡터 데이터 잔류**
- **위치**: `db_manager.py` `reset_after()` L1430-1452
- **시나리오**: 에피소드 10에서 롤백 시 manuscripts/blueprints/state_logs는 삭제되지만 episode_meta/vec_episodes에 삭제된 에피소드 데이터가 남음
- **영향**: Smart Context Retrieval이 삭제된 에피소드를 참조하여 모순 발생 가능
- **현재 방어**: 없음 (벡터 데이터는 시간이 지나면 자연적으로 검색 우선순위가 낮아짐)
- **권고**: `reset_after()`에 `DELETE FROM episode_meta WHERE ep_num >= ?` 추가

---

## 8. 전체 데이터 흐름 다이어그램

```
Stage 0                    Stage 2                     Stage 3                    Stage 4
========                   ========                    ========                   ========
Bible ──────────────────> DB anchor "bible"
Treatment ──> JSON file ─> plot_roadmap in Bible
StyleGuide ─────────────> DB anchor "style_guide"
PresetState ────────────> DB anchor "preset_state"
                          |
                          v
                     Arc 설계 루프
                     (Analyst -> FourPhase -> Director)
                          |
                     validate_arc()  [Pydantic]
                          |
                          v
                     DB anchor "arcs"  ────────────> ctx.current_project.arcs
                                                          |
                                                     Blueprint 생성 루프
                                                     (Constraint -> Ensemble -> Validate)
                                                          |
                                                     validate_blueprint()  [Pydantic]
                                                          |
                                                          v
                                                     DB blueprints 테이블  ───────────> blueprint 로드
                                                                                            |
                                                                                     원고 집필 루프
                                                                                     (CW -> Director 면담)
                                                                                            |
                                                                                            v
                                                                                    [Block 1] manuscripts  (원자적)
                                                                                    [Block 1] martial_tracker
                                                                                    [Block 2] vec_episodes  (비차단)
                                                                                    [Block 3] episode_bibles  (비차단)
                                                                                    [Block 3] state_logs
                                                                                    [Block 4] chain_link anchor  (비차단)
                                                                                    [Block 5] world_state anchor  (원자적*)
                                                                                    [Block 5] fact_ledger anchor
                                                                                    [Block 6] satisfaction_tags  (비차단)
                                                                                    [Block 6] episode_pacing
```

*Block 5의 원자성은 `db.transaction()` 사용 여부에 따라 조건부

---

## 9. 결론

전체 파이프라인의 데이터 흐름은 **대체로 건전**하다. 각 Stage 간 경계에서 다음과 같은 방어 메커니즘이 작동한다:

1. **Pydantic 검증 게이트**: Arc(Stage 2 출구)와 Blueprint(Stage 3 출구)에 적용. graceful degradation으로 검증 실패 시에도 크래시 없이 진행.
2. **`.get()` 폴백**: 모든 하류 Stage에서 필수 필드에 `.get(key, default)` 패턴 사용. None/빈값 방어.
3. **DI Context callable() 체크**: Stage 3의 콜백 슬롯에 S3-N-P1-3 패치로 체계적 None 방어.
4. **JSON 직렬화 왕복 무손실**: `json.dumps(ensure_ascii=False)` -> DB TEXT -> `json.loads()` 경로에서 데이터 손실 없음.

**주요 개선 기회**:
- Stage 4의 원고-메타데이터 간 원자성 강화 (현재 의도적 분리이지만 고아 에피소드 감지 필요)
- 에피소드 롤백 시 벡터 데이터(episode_meta) 정리 추가
- preset_registry의 DB -> 메모리 자동 복원 경로 추가
