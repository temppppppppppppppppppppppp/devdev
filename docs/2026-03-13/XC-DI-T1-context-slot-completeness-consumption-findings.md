# XC-DI-T1: Context Slot 완전성 vs 실제 소비

> Track: XC-DI (Protocol & 계약 준수)
> 대상: stage4_context.py (37 slots), stage2_context.py (47 slots), stage3_context.py (23 slots)
> 감사일: 2026-03-13
> 방법론: 3-Pass (수집 → 교차 검증 → 오탐 제거)

---

## 1. Stage4Context 슬롯 소비 분석 (37 slots)

### 필수 5종

| 슬롯 | 소비처 | 상태 |
|-------|--------|------|
| `ui` | stage4_orchestrator, stage4_interview_round, stage4_post_processor, stage4_context_builder 전역 | ACTIVE |
| `current_project` | 전역 (DB, Bible, paths, arcs 접근) | ACTIVE |
| `agents` | director, writer, manager, state_extractor, three_phase_bp 등 | ACTIVE |
| `sys` | api_client, hud, guard 접근 | ACTIVE |
| `state_tracker` | interview_round (NPC/아이템/시간 검증), post_processor (NPC overexposure) | ACTIVE |

### 확장 14종

| 슬롯 | 소비처 | 상태 |
|-------|--------|------|
| `memory` | post_processor:748 (memorize_v20_episode), context_builder:2321/2398 (벡터 검색), post_processor:1421 (sync) | ACTIVE |
| `context_advisor` | context_builder:2323 (SemanticQueryBroker 연동) | ACTIVE |
| `world_state` | orchestrator:375-377, context_builder:1873/2116-2135, post_processor:1147-1176 | ACTIVE |
| `fact_ledger` | context_builder:2165-2172/2188, post_processor:1151-1204 | ACTIVE |
| `character_voice` | orchestrator:1545-1554, post_processor:461-467 | ACTIVE |
| `perf_timer` | interview_round:1376/1415/1516/1780, context_builder:2345/2354, post_processor:605-606 | ACTIVE |
| `foreshadow_tracker` | post_processor:471-478, context_builder:2418-2419 | ACTIVE |
| `failure_learner` | interview_round:3264 (기록), interview_round:3641 (CW 컨텍스트 주입) | ACTIVE |
| `diversity_engine` | orchestrator:770-772 (writer injection) | ACTIVE |
| `semantic_plot_guard` | context_builder:2425-2432 | ACTIVE |
| `selected_genre` | orchestrator:1411, post_processor:418-419 | ACTIVE |
| `quality_dashboard` | interview_round:1454, post_processor:1289-1321 | ACTIVE |
| `pacing_analyzer` | orchestrator:740, post_processor:1266 | ACTIVE |
| `pass_rate_monitor` | interview_round:4571 | ACTIVE |
| `emotion_tracker` | post_processor:483-490 | ACTIVE |

### 조건부 모듈 (conditional_modules dict, 8종)

| 키 | 소비처 | 상태 |
|----|--------|------|
| `pre_director_checklist` | interview_round:2417 (get_module) | ACTIVE |
| `confidence_calibrator` | interview_round:2438 (get_module) | ACTIVE |
| `prompt_weighter` | interview_round:1387 (get_module) | ACTIVE |
| `cross_verifier` | interview_round:2455 (get_module) | ACTIVE |
| `chain_of_verification` | orchestrator:953 (get_module) | ACTIVE |
| `adversarial_self_play` | interview_round:3491 (get_module) | ACTIVE |
| `tree_of_thoughts` | interview_round:3140 (get_module) | ACTIVE |
| `multi_agent_deliberation` | interview_round:3154 (get_module) | ACTIVE |

### 콜백 12종

| 슬롯 | 소비처 | None 가드 | 상태 |
|-------|--------|-----------|------|
| `get_int_input` | orchestrator:1277/1479/1535 | :1277 callable guard, :1479 **가드 없음**, :1535 **가드 없음** | **RISK** |
| `build_item_acquisition_timeline` | context_builder:1864 | **가드 없음** (try-except 내부) | ACTIVE |
| `load_narrative_summaries` | context_builder:2448 | try-except 내부 | ACTIVE |
| `get_protagonist_name` | context_builder:81, post_processor:1333 | :81 try-except, :1333 truthiness 가드 | ACTIVE |
| `extract_npc_profiles` | interview_round:3537-3538 | callable 가드 | ACTIVE |
| `generate_narrative_summary` | post_processor:448 | try-except 내부 | ACTIVE |
| `generate_writer_guidance_v60_8` | context_builder:2514-2519 | inspect+callable 가드 | ACTIVE |
| `enrich_director_result` | interview_round:844-849 | inspect+callable 가드 | ACTIVE |
| `audit_event` | post_processor, interview_round | callable(getattr) 가드 | ACTIVE |
| `write_audit_summary` | (Stage4에서 직접 호출 없음 — Stage2/3에서만) | N/A | **DORMANT** |
| `flush_audit_buffer` | orchestrator:1608/1618, post_processor:601 | callable 가드 | ACTIVE |
| `safe_commit` | orchestrator:1610/1620 | callable 가드 | ACTIVE |

### 내부 슬롯

| 슬롯 | 소비처 | 상태 |
|-------|--------|------|
| `session_logger` | interview_round:1805 (getattr 안전 접근) | ACTIVE |
| `_stage4_context_budget_meta` | context_builder:1493/1505 (쓰기), orchestrator:797 (읽기) | ACTIVE |

---

## 2. Stage2Context 슬롯 소비 분석 (47 slots)

### 필수 5종: 전부 ACTIVE (생략)

### 확장 19종

| 슬롯 | 소비처 | 상태 |
|-------|--------|------|
| `selected_genre` | orchestrator:266/302, preflight 다수 | ACTIVE |
| `preset_registry` | orchestrator:291 (StateTracker 생성) | ACTIVE |
| `perf_timer` | (Stage2에서 직접 참조 미확인) | **확인 필요** |
| `semantic_plot_guard` | preflight:740 | ACTIVE |
| `failure_learner` | orchestrator:591 참조 없음, preflight 내 미확인 | **확인 필요** |
| `memory` | (Stage2에서 직접 참조 미확인) | **확인 필요** |
| `context_advisor` | preflight:1147 | ACTIVE |
| `stage2_optimizer` | preflight:867-869, finalizer:1509/1712, validation_pipeline:368/825/941 | ACTIVE |
| `arc_draft_validator` | validation_pipeline:230-233/556-559 | ACTIVE |
| `arc_corrector` | validation_pipeline:601-612 | ACTIVE |
| `constraint_compiler` | preflight:697-728/1043-1068 | ACTIVE |
| `stage_rejection_history` | orchestrator:591 | ACTIVE |
| `pass_rate_monitor` | (Stage2 내 미확인) | **확인 필요** |
| `quality_dashboard` | (Stage2 내 미확인) | **확인 필요** |
| `quality_amplifier` | preflight:888-889 | ACTIVE |
| `agent_intelligence` | preflight:894-895 | ACTIVE |
| `constitutional_checker` | preflight:905-906 | ACTIVE |
| `self_reflector` | validation_pipeline:258-269 | ACTIVE |
| `use_arc_corrector` | validation_pipeline:601 (불리언 플래그) | ACTIVE |
| `adversarial_self_play` | preflight:1330/1354/1374-1382 | ACTIVE |

### 콜백 21종 + 메타 3종

| 슬롯 | 소비처 | None 가드 | 상태 |
|-------|--------|-----------|------|
| `audit_event` | orchestrator, preflight, finalizer, validation_pipeline (다수) | callable(getattr) 가드 | ACTIVE |
| `cumulative_state_cache` | orchestrator:366 (초기화) | 직접 할당 | ACTIVE |
| `cumulative_state_cache_key` | orchestrator:367 (초기화) | 직접 할당 | ACTIVE |
| `write_audit_summary` | orchestrator:995 | callable 가드 | ACTIVE |
| `validate_arc_data_fields` | preflight:1063 참조 | callable 가드 | ACTIVE |
| `validate_arc_mapping` | orchestrator:185-191 | callable 가드 + fallback | ACTIVE |
| `validate_arc_integrity` | finalizer:1027 | callable 가드 | ACTIVE |
| `state_tracker_loaded_arcs` | orchestrator:284/304 | or 0 폴백 | ACTIVE |
| `safe_commit_async` | finalizer:1091-1094 | callable 가드 | ACTIVE |
| `get_max_episode_from_manuscripts` | orchestrator:322 | 직접 호출 (Stage2에서 .ctx로) | ACTIVE |
| `get_int_input` | orchestrator:349 | callable 가드 | ACTIVE |
| `generate_structured_arc_feedback` | preflight/validation 내 retry 콜백 | callable 가드 (retry_feedback 체계) | ACTIVE |
| `generate_reverse_feedback_stage3_to_2` | retry 콜백 | callable 가드 | ACTIVE |
| `generate_reverse_feedback_stage4_to_2` | retry 콜백 | callable 가드 | ACTIVE |
| `fix_entity_registry_protagonist` | preflight:1061-1063 | callable(getattr) 가드 | ACTIVE |
| `calculate_arc_from_episode` | orchestrator:182 | getattr 가드 | ACTIVE |
| `build_strong_kind_feedback` | retry 콜백 | callable 가드 | ACTIVE |
| `build_minimal_arc_context` | retry 콜백 | callable 가드 | ACTIVE |
| `build_focused_context` | retry 콜백 | callable 가드 | ACTIVE |
| `analyze_rejection_pattern_v60` | retry 콜백 | callable 가드 | ACTIVE |
| `get_adaptive_feedback_intensity` | retry 콜백 | callable 가드 | ACTIVE |
| `generate_arc_context_v60` | orchestrator:381 | 직접 호출 | ACTIVE |
| `sync_cache_key_to_app` | preflight:715-716/1056-1057 | truthiness 가드 | ACTIVE |
| `retry_feedback_contract` | **소비처 없음** | N/A | **ORPHAN** |
| `retry_feedback_missing_callbacks` | **소비처 없음** | N/A | **ORPHAN** |
| `session_logger` | (Stage2 내 미확인) | N/A | **확인 필요** |

---

## 3. Stage3Context 슬롯 소비 분석 (23 slots)

### 필수 2종 + 속성 10종

| 슬롯 | 소비처 | 상태 |
|-------|--------|------|
| `ui` | orchestrator 전역 (ctx.ui.log) | ACTIVE |
| `current_project` | orchestrator (DB, Blueprint, Bible 접근) | ACTIVE |
| `agents` | orchestrator:443 (telemetry), orchestrator:1256 | ACTIVE |
| `sys` | orchestrator 내 state_tracker 초기화 시 (app.sys.api_client) | ACTIVE (간접) |
| `state_tracker` | orchestrator:511/515-516/1256 | ACTIVE |
| `memory` | orchestrator:969 | ACTIVE |
| `context_advisor` | orchestrator:970 | ACTIVE |
| `world_state` | orchestrator:331/512/515/1148/1745-1747 | ACTIVE |
| `fact_ledger` | orchestrator:332/513/1156 | ACTIVE |
| `adversarial_self_play` | orchestrator:1260 | ACTIVE |
| `preset_registry` | orchestrator (app.preset_registry 참조, ctx 경유 미확인) | **간접만** |
| `selected_genre` | orchestrator:972-973 | ACTIVE |
| `pass_rate_monitor` | orchestrator:1357-1359/1870-1872 | ACTIVE |

### 콜백 10종

| 슬롯 | 소비처 | None 가드 | 상태 |
|-------|--------|-----------|------|
| `get_protagonist_name` | orchestrator:868-870 | callable(getattr) 가드 | ACTIVE |
| `audit_event` | orchestrator:721-722/741-742/1275-1276/1488-1489/1497-1498/1511-1512/1527-1528/1944-1945 | callable 가드 | ACTIVE |
| `write_audit_summary` | orchestrator:602-603 | callable 가드 | ACTIVE |
| `get_arc_context_for_episode` | orchestrator:730-731 | callable 가드 | ACTIVE |
| `get_max_episode_from_manuscripts` | orchestrator:533 | callable 가드 | ACTIVE |
| `get_int_input` | orchestrator:554-560 | callable 가드 | ACTIVE |
| `safe_commit` | orchestrator:1509 | callable 가드 | ACTIVE |
| `validate_arc_data_fields` | orchestrator:747-748 | callable(getattr) 가드 | ACTIVE |
| `validate_blueprint_integrity` | orchestrator:1495 | callable 가드 | ACTIVE |
| `fix_entity_registry_protagonist` | orchestrator:827-828 | callable(getattr) 가드 | ACTIVE |
| `session_logger` | orchestrator:1309/1815 | getattr 가드 | ACTIVE |

---

## 4. Findings

### [XC-DI-001] P3 | Stage4 `get_int_input` 콜백 2곳 None 가드 미적용

| 필드 | 내용 |
|------|------|
| ID | XC-DI-001 |
| Severity | P3 |
| 현상 요약 | `stage4_orchestrator.py:1479`와 `:1535`에서 `get_int_input` 콜백을 None 가드 없이 직접 호출 |
| 코드 근거 | `stage4_orchestrator.py:1479` `target_ep = self.ctx.get_int_input(...)` — callable 검사 없음. 동일 파일 :1535도 동일 패턴 |
| 영향 경계 | Stage 4 진입 시 `get_int_input=None`이면 `TypeError: 'NoneType' is not callable` |
| 테스트 근거 | `from_app()` 경로에서는 `_safe_getattr`로 바인딩되어 실질적으로 None이 아님. 테스트 mock 경로에서만 위험 |
| 기존 중복 여부 | 없음 |
| 권장 후속 조치 | :1276처럼 `callable(getattr(self.ctx, "get_int_input", None))` 가드 추가. 공수 5분 |

### [XC-DI-002] P3 | Stage4 `write_audit_summary` 콜백 슬롯 Stage4 내 소비처 없음 (Dormant)

| 필드 | 내용 |
|------|------|
| ID | XC-DI-002 |
| Severity | P3 |
| 현상 요약 | `Stage4Context`에 `write_audit_summary` 슬롯이 선언되어 있지만, Stage4 오케스트레이터/서브모듈에서 실제 소비되지 않음 |
| 코드 근거 | `stage4_context.py:82` 슬롯 선언. grep 결과 `stage4_orchestrator.py`, `stage4_interview_round.py`, `stage4_post_processor.py`, `stage4_context_builder.py` 어디에서도 `self.ctx.write_audit_summary` 호출 없음 |
| 영향 경계 | 기능 영향 없음. 슬롯 메모리 낭비만 존재 |
| 테스트 근거 | 테스트에서 미검증 (슬롯 자체가 미사용) |
| 기존 중복 여부 | 없음 |
| 권장 후속 조치 | 향후 cleanup 시 제거 검토. Stage2/3에서는 사용되므로 Protocol 통일 목적이면 유지 가능. 공수 무시 |

### [XC-DI-003] P3 | Stage2 `retry_feedback_contract`/`retry_feedback_missing_callbacks` 슬롯 소비처 없음 (Orphan)

| 필드 | 내용 |
|------|------|
| ID | XC-DI-003 |
| Severity | P3 |
| 현상 요약 | Stage2Context에 `retry_feedback_contract`와 `retry_feedback_missing_callbacks` 슬롯이 선언·할당되지만, Stage2 orchestrator/preflight/finalizer/validation_pipeline 어디에서도 읽히지 않음 |
| 코드 근거 | `stage2_context.py:188-189` 슬롯 선언, `:301-308` 기본값 할당, `:364-365` from_app에서 주입. 그러나 `stage2_orchestrator.py`, `stage2_preflight.py`, `stage2_finalizer.py`, `stage2_validation_pipeline.py` 전부 `retry_feedback_contract`/`retry_feedback_missing` 참조 0건 |
| 영향 경계 | 기능 영향 없음. Observability 목적으로 선언되었으나 실제 관측 코드 미구현 |
| 테스트 근거 | 테스트에서 미검증 |
| 기존 중복 여부 | 없음 |
| 권장 후속 조치 | (1) 관측 코드 추가하여 활성화하거나, (2) 슬롯 제거. `_build_retry_feedback_contract()` 로직은 콜백 해소에 유효하므로 계산 자체는 유지하되 결과 저장 슬롯만 제거 가능. 공수 10분 |

### [XC-DI-004] P3 | Stage3Context에 미사용 의심 슬롯: `preset_registry`

| 필드 | 내용 |
|------|------|
| ID | XC-DI-004 |
| Severity | P3 |
| 현상 요약 | `Stage3Context.preset_registry` 슬롯이 선언되어 있으나, `stage3_orchestrator.py` 내부에서 `ctx.preset_registry`를 직접 참조하는 곳이 없음 |
| 코드 근거 | `stage3_context.py:29` 슬롯 선언. `stage3_orchestrator.py`에서 `app.preset_registry`는 `_init_state_tracker_if_needed()`에서 `app` 직접 접근으로 사용 (`:637`). ctx 경유 접근 0건 |
| 영향 경계 | 기능 영향 없음. `app` 직접 접근이 ctx를 우회하고 있어 DI 패턴 일관성 위반 |
| 테스트 근거 | 미검증 |
| 기존 중복 여부 | 없음 |
| 권장 후속 조치 | `_init_state_tracker_if_needed()` 내부의 `app.preset_registry` → `ctx.preset_registry` 전환. 공수 5분 |

### [XC-DI-005] P2 | Stage3 `_init_*` 메서드가 ctx가 아닌 self.app 직접 접근 — DI 우회

| 필드 | 내용 |
|------|------|
| ID | XC-DI-005 |
| Severity | P2 |
| 현상 요약 | `stage3_orchestrator.py`의 `_init_state_tracker_if_needed()`, `_init_world_state_if_needed()`, `_init_fact_ledger_if_needed()` 3개 메서드가 `self.app`에 직접 속성을 할당하여 DI 컨텍스트를 우회 |
| 코드 근거 | `stage3_orchestrator.py:630-690` — `app.state_tracker = StateTracker(...)`, `app.world_state = WorldStateManager(...)`, `app.fact_ledger = FactLedger(...)`. 이후 `:511-513`에서 `ctx.state_tracker = getattr(self.app, "state_tracker", None)` 으로 ctx에 재주입 |
| 영향 경계 | `self.app`이 None이거나 테스트 stub이면 AttributeError. 또한 ctx와 app 간 상태 불일치 가능 |
| 테스트 근거 | e2e 테스트에서 `app` mock으로 커버되지만, 단위 테스트에서 ctx-only 주입 시 이 경로 미통과 |
| 기존 중복 여부 | 없음 |
| 권장 후속 조치 | `_init_*` 로직을 ctx 기반으로 전환하거나, `from_app()` 시점에 lazy init 포함. 공수 1시간 |
