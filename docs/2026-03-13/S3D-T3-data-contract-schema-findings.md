# S3D-T3: Stage 3 Data Contract & Schema Validation Audit (1-pass)

**Auditor**: Claude Opus 4.6
**Date**: 2026-03-13
**Scope**: Stage2 -> Stage3 -> Stage4 data contracts, Blueprint schema validation
**Mode**: Read-only audit

---

## Files Reviewed

| File | Lines | Role |
|------|-------|------|
| `modules/domain/agents/blueprint_constraint_compiler.py` | 461 | Arc -> constraint_block 컴파일 |
| `modules/domain/agents/blueprint_ensemble.py` | 941 | 3-strategy ensemble Blueprint 생성 |
| `modules/domain/agents/three_phase_blueprint_generator.py` | 790 | 3-phase 파이프라인 (Constraint -> Generate -> Validate) |
| `modules/core/stage3_orchestrator.py` | ~1900 | Stage 3 메인 루프, entity registry, prev_blueprints 관리 |
| `modules/core/stage4_context_builder.py` | ~600+ | Stage4 컨텍스트 빌더 (Blueprint 소비측) |
| `modules/models/blueprint.py` | 76 | Blueprint Pydantic v2 모델 |
| `modules/core/continuity_pin_guard.py` | 150 | 연속성 핀 가드 |
| `modules/core/services/state_service.py` | L241-287 | validate_arc_data_fields 구현 |

---

## Checklist Results

### 1. Arc required field consumption — ConstraintCompiler reference keys vs Stage2 output existence

**Status**: OK

**Evidence**:
- `blueprint_constraint_compiler.py:56-58` — `ep_start`, `ep_count`, `arc_no` 모두 `.get()` + 기본값 사용
- `blueprint_constraint_compiler.py:184-186` — `tactical_doc`, `episode_details` 모두 `.get()` + 폴백
- `blueprint_constraint_compiler.py:319-353` — `joint_docs`, `status_shadow`, `state_constraints` 모두 `.get()` + 방어
- `state_service.py:248-260` — `validate_arc_data_fields`에서 `tactical_doc`, `beat_sequence`, `joint_docs`, `status_shadow`, `arc_drive`, `hybrid_composition`, `ep_count`, `ep_end` 기본값 주입 확인

ConstraintCompiler가 참조하는 모든 Arc 키에 대해 `.get()` 방어가 적용되어 있으며, `validate_arc_data_fields`에서 사전 복구도 이루어진다.

---

### 2. ep_start None defense (L738-743) — validate_arc_data_fields correction failure path

**Status**: OK

**Evidence**:
- `stage3_orchestrator.py:738-743`:
  ```python
  ep_start_val = arc_data.get("ep_start")
  if ep_start_val is None or not isinstance(ep_start_val, int):
      ctx.ui.log(f"⚠️ [Stop] Arc ep_start 누락: arc_idx={arc_idx}")
      ...
      return {..., "break": True}
  ```
- `stage3_orchestrator.py:746-752`: `validate_arc_data_fields` 호출은 ep_start 검증 **이후** 수행됨

`ep_start`가 None이거나 int가 아닐 경우 즉시 break 반환하여 루프 중단. `validate_arc_data_fields`의 required_defaults에 `ep_start`는 포함되지 않지만(L248-260), Stage3Orchestrator가 직접 방어하므로 문제없다.

**참고**: `validate_arc_data_fields`가 `ep_start` 자체를 복구하지 않는 것은 의도적 설계로 보인다 (ep_start는 Arc 생성 시 필수 할당, 누락은 심각한 데이터 오류).

---

### 3. protagonist_items vs items_acquired — priority-fallback pattern correctness

**Status**: OK

**Evidence**:
- `stage3_orchestrator.py:1761-1762` (`_detect_inventory_gaps`):
  ```python
  for item in (_sc.get("protagonist_items") or _sc.get("items_acquired") or []):
  ```
- `stage4_context_builder.py:243`: `items_acquired` 단독 참조 (state_changes.items_acquired)
- `modules/models/arc.py:106,114`: Pydantic Arc 모델에서 `protagonist_items: list[str] = Field(default_factory=list)` + `items_acquired: list | None = None`

Stage 3 내에서는 `protagonist_items` 우선 폴백이 1곳(`_detect_inventory_gaps`)에서 정확히 적용. Stage4ContextBuilder의 `_collect_arc_state_entities`(L243)에서는 `state_changes.items_acquired`를 참조하는데, 이는 `state_constraints`가 아닌 `state_changes` 하위 키이므로 별개의 경로이며 문제 없다.

---

### 4. Blueprint Pydantic `extra="allow"` — custom key passthrough confirmation

**Status**: OK

**Evidence**:
- `modules/models/blueprint.py:35`: `model_config = ConfigDict(extra="allow")`
- `modules/models/blueprint.py:21`: `BlueprintRelationshipChange`도 `extra="allow"`
- `three_phase_blueprint_generator.py:601`: `best_blueprint = validate_blueprint(best_blueprint)` — Pydantic ingress+egress
- `modules/models/blueprint.py:65-75`: `validate_blueprint()` — 검증 실패 시 원본 dict 그대로 반환 (graceful degradation)

LLM이 생성하는 `ending_hook`, `cliffhanger`, `ongoing_conflicts`, `_ensemble_meta`, `_stage3_meta`, `_continuity_pins`, `_inventory_gaps` 등 미정의 키가 `extra="allow"`로 안전하게 통과된다.

---

### 5. Blueprint required fields — PreValidator vs Ensemble filter vs Pydantic defaults conflict

**Status**: OK

**Evidence**:
- **Ensemble filter** (`blueprint_ensemble.py:573-574`): `scene_breakdown` + `integrated_scenario` 존재 필수
- **Ensemble 최소 기준** (`blueprint_ensemble.py:390`): `scene_count >= 4` and `integrated_len >= 500`
- **Pydantic defaults** (`blueprint.py:38-51`): `scene_breakdown: dict = Field(default_factory=dict)`, `integrated_scenario: str = ""`
- **model_validator** (`blueprint.py:53-62`): `ep_num` <-> `episode_number` 상호 동기화

Ensemble은 `scene_breakdown`과 `integrated_scenario` 존재를 직접 검증하므로 Pydantic 기본값(빈 dict/빈 문자열)이 빈 채로 통과하는 상황이 발생하지 않는다. Ensemble 필터 → Validator → Pydantic 순서가 올바르게 적용.

---

### 6. stop_line extraction — 3-level fallback chain gaps

**Status**: OK

**Evidence** (`blueprint_constraint_compiler.py:218-259`):
1. **Level 1** (L232-239): `episode_details` 에서 `next_ep` 항목 매칭 → `details` 리스트 join
2. **Level 2** (L242-249): `_EPISODE_HEADER_PATTERNS` 다중 정규식으로 `tactical_doc`에서 추출
3. **Level 3** (L252-257): `beat_sequence[arc_position]` 폴백 (TypeSafety dict->str 래핑 포함)
4. **Arc finale** (L221-222): `arc_position >= ep_count` 시 `content: None, is_arc_finale: True` 반환

3단 폴백 체인이 빈틈 없이 구성되어 있다. 각 레벨은 이전 레벨이 `content`를 채우지 못한 경우에만 진입하며, 최종적으로 content가 없으면 `None`을 반환하고, 소비측(`blueprint_ensemble.py:702-706`, `unified_blueprint_validator.py:392-393`)에서 `.get("content")`로 None 안전 처리.

---

### 7. ContinuityPinGuard — previous manuscript reference vs previous Blueprint reference appropriateness

**Status**: FINDING

**Severity**: P3 (Low, advisory-only)

**Evidence**:
- `stage3_orchestrator.py:1450-1464`: `previous_published_text`를 직전 화 **원고(manuscript)**에서 로드
- `stage3_orchestrator.py:1466-1473`: `arc_tactical_text`를 현재 화의 Arc tactical에서 추출
- `continuity_pin_guard.py:108`: `source_text = _coerce_text(previous_published_text) or _coerce_text(arc_tactical_text)`
- `continuity_pin_guard.py:113-131`: quoted token 대조 — source에 1개, blueprint에 불일치 → 자동 교정

**설명**: ContinuityPinGuard는 직전 원고(`previous_published_text`)를 1차 소스로, Arc tactical을 2차 소스로 사용한다. 이는 올바른 설계이다 (원고가 최종 출판물이므로 ground truth). 다만, **첫 화** 또는 **원고 미존재 상황**에서는 `previous_published_text`가 빈 문자열이 되어 Arc tactical만 참조하게 된다. 이 경우 Arc tactical에도 quoted token이 없으면 핀 가드가 사실상 비활성화된다.

**영향**: 연속성 핀 교정이 소스 부재로 인해 비활성화되는 edge case가 존재하지만, 이는 직전 원고가 없는 초기 화에서만 발생하며 실질적 위험은 낮다.

---

### 8. prev_blueprints management — initial load/append/cap consistency

**Status**: OK

**Evidence**:
- **초기 로드** (`stage3_orchestrator.py:573-577`): `range(max(1, working_ep - 30), working_ep)` — 최근 30개 로드
- **기존 BP 스킵 시 추가** (`stage3_orchestrator.py:709-711`): `prev_blueprints.append(_existing_bp)` + cap `prev_blueprints[:] = prev_blueprints[-30:]`
- **성공 시 추가** (`stage3_orchestrator.py:1521-1523`): `prev_blueprints.append(blueprint)` + cap `prev_blueprints[:] = prev_blueprints[-30:]`
- **소비** (`stage3_orchestrator.py:1249`): `prev_blueprints[-30:]` 전달 (ThreePhaseGenerator → Ensemble)
- **소비** (`stage3_orchestrator.py:993,998,1169`): `prev_blueprints[-5:]` 전달 (Smart Context Retrieval)

초기 로드, 스킵 추가, 성공 추가 모두 30개 cap이 일관되게 적용. in-place slice assignment `prev_blueprints[:] = prev_blueprints[-30:]`로 원래 리스트 참조를 유지하므로 외부 참조 불일치도 없다.

---

### 9. Entity Registry -> Stage4 delivery path — duplication/omission

**Status**: FINDING

**Severity**: P2 (Medium)

**Evidence**:
- **Stage 3 경로** (`stage3_orchestrator.py:757,811-848`):
  - `_get_entity_registry()` → `state_extractor.extract_cumulative_state(all_arcs[:arc_idx+1])` → `entity_registry` dict
  - Arc 단위 캐시 (`_entity_cache_arc_idx`)
  - `fix_entity_registry_protagonist()` 후처리
  - `ThreePhaseBlueprintGenerator.generate()` 에 `entity_registry` 전달 (L994, 1253)
  - 하지만 **Blueprint 자체에 entity_registry를 저장하지 않음**

- **Stage 4 경로** (`stage4_orchestrator.py:1352-1358`):
  - `state_extractor.extract_cumulative_state(ep_num - 1)` → 완전히 **재추출**
  - Stage 3에서 추출한 결과를 재사용하지 않음

- **Stage 4 Context Builder** (`stage4_context_builder.py`):
  - `entity_registry` 그립 검색 결과: 0건 — Stage4ContextBuilder는 entity_registry를 직접 참조하지 않음
  - 대신 `_collect_npc_roster()`, `_collect_arc_state_entities()`로 Arc data에서 직접 엔티티 수집

**설명**: Entity Registry가 Stage 3과 Stage 4에서 독립적으로 재추출된다. Stage 3에서는 `extract_cumulative_state(all_arcs[:arc_idx+1])`로 **Arc 리스트** 기반, Stage 4에서는 `extract_cumulative_state(ep_num - 1)`로 **에피소드 번호** 기반으로 호출하여 입력이 다르다. 이는 중복 LLM 호출(state_extractor 내부)을 발생시키며, 두 스테이지 간 entity_registry 불일치 가능성이 있다.

**영향**: LLM 비용 중복 (Stage 3 + Stage 4 양측에서 state_extractor 호출). Entity Registry 일관성은 state_extractor의 결정론성에 의존하나, LLM 기반이므로 호출마다 미세 차이 발생 가능.

---

### 10. state_changes_summary -> Blueprint reflection path

**Status**: OK

**Evidence**:
- **생성** (`blueprint_constraint_compiler.py:81`): `state_changes_summary = self._summarize_state_changes(arc_data.get("state_changes", {}))`
- **constraint_block 포함** (`blueprint_constraint_compiler.py:93`): `"state_changes_summary": state_changes_summary`
- **프롬프트 주입 경로 1** (`blueprint_constraint_compiler.py:170-175`): `compile_to_prompt()` 내 `sc_summary` 섹션
- **프롬프트 주입 경로 2** (`blueprint_ensemble.py:769-800`): `_format_constraints()` 내 `state_changes_summary` 소비
  - str 타입: 800자 cap (L773)
  - dict 타입: `npc_deaths`, `skill_acquisitions`, `resolved_plots`, `permanent_injuries` 구조화 처리 (L775-799)
- **summarize 범위** (`blueprint_constraint_compiler.py:371-455`): `npc_deaths`, `skill_acquisitions`, `relationship_changes`, `major_items`, `npc_injuries`, `npc_movements`, `resolved_plots` — 7개 카테고리 전량 처리

`_summarize_state_changes`는 str을 반환하므로, `_format_constraints`의 dict 분기(L774-799)는 도달하지 않는다. 이는 버그가 아니라 방어적 처리이다 (향후 constraint_block을 dict로 변경 시 자동 대응).

---

## Summary

| # | Checklist Item | Status | Severity |
|---|---------------|--------|----------|
| 1 | Arc required field consumption | OK | — |
| 2 | ep_start None defense | OK | — |
| 3 | protagonist_items vs items_acquired | OK | — |
| 4 | Blueprint Pydantic extra="allow" | OK | — |
| 5 | Blueprint required fields conflict | OK | — |
| 6 | stop_line 3-level fallback | OK | — |
| 7 | ContinuityPinGuard source reference | FINDING | P3 |
| 8 | prev_blueprints management | OK | — |
| 9 | Entity Registry -> Stage4 delivery | FINDING | P2 |
| 10 | state_changes_summary reflection | OK | — |

**P0**: 0건
**P1**: 0건
**P2**: 1건 (Entity Registry 중복 추출 + 잠재적 불일치)
**P3**: 1건 (ContinuityPinGuard 소스 부재 edge case)

---

## Recommendations (코드 변경 없음 — 기록만)

1. **P2 #9**: Entity Registry를 Blueprint dict에 `_entity_registry` 키로 저장 후 Stage 4에서 재사용하거나, state_extractor 결과를 DB에 캐시하여 중복 호출 제거 고려.
2. **P3 #7**: 첫 화 ContinuityPinGuard 비활성화는 현재 설계 의도에 부합. 별도 조치 불필요.
