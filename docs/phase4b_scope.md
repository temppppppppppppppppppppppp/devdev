# Phase 4B Scope: 배치 계획 + 포함/제외 메서드 + 롤백 단위

> 작성일: 2026-02-13
> SSOT: (1) 코드베이스 (커밋 `1b3de64`), (2) Phase 4B 문서군(`docs/phase4b_*.md`)
> 원칙: 동작 보존 + Facade 위임 기반 점진 추출

---

## 충돌 보고서

| # | 문서 (기존 설계 기준) | 코드 (SSOT) | 판정 |
|---|--------------------------|------------|------|
| C1 | "DB 위반 6건" (A-4 섹션) | **34건** / 7파일 (`main_a.py`:19, `project_manager.py`:5, `reverse_expander.py`:6, `reflexion_manager.py`:2, `stage4_orchestrator.py`:1, `lore_manager.py`:1, `blueprint_memory.py`:1) | 코드 우선 — 34건이 정확 |
| C2 | "7종 re-export" (C 섹션 #3) | **6종** (5 service + 1 DB) | 코드 우선 — 에이전트 어댑터 4B 이월로 6종 |
| C3 | "Phase 4B 추출 ~3,200줄" (C 섹션) | 실측 **~3,490줄** (아래 배치별 상세 참조) | 코드 우선 |

---

## 배치 전략 총괄

```
4B-1 (AuditService)       ────→ 4B-2 (Feedback+Narrative) ────→ 4B-3 (Validation+DataMgr)
     53줄, LOW                    610줄, LOW-MED                    579줄, MED
                                                                        │
4B-4 (Stage0+Stage3 Orch)  ←─────────────────────────────────────────────┘
     1,285줄, MED-HIGH
                │
4B-5 (Bootstrap+Dispatcher) ←────┘
     1,101줄, HIGH
```

**의존 관계**: 4B-1 → 4B-2 (feedback이 _audit_event 호출) → 4B-3 (validation이 _audit_event 호출) → 4B-4 (Stage가 모든 서비스 사용) → 4B-5 (Bootstrap이 전체 조립)

---

## Batch 4B-1: AuditService 추출

| 항목 | 내용 |
|------|------|
| **추출 모듈** | `modules/core/services/audit_service.py` |
| **크기** | ~53줄 (원본) + ~30줄 (클래스 뼈대) = ~83줄 |
| **리스크** | **LOW** |
| **롤백 단위** | 단일 커밋 revert |

### 포함 메서드

| 메서드 | 원본 위치 | 크기 | 의존성 |
|--------|----------|------|--------|
| `_audit_event` | `main_a.py:2992-3005` | 14줄 | `self.runtime_audit`, `self._audit_buffer` (list append) |
| `_flush_audit_buffer` | `main_a.py:3007-3023` | 17줄 | `self._audit_buffer`, `self.current_project.paths.root` (파일 I/O) |
| `_write_audit_summary` | `main_a.py:3025-3044` | 20줄 | `self.runtime_audit`, `self.current_project.paths.root` (파일 I/O), 내부에서 `_flush_audit_buffer` 호출 |

### 제외 메서드

없음 — 감사 서비스는 이 3개 메서드로 완결.

### Facade 스텁 (main_a.py 잔류)

```python
def _audit_event(self, *a, **kw): return self._audit.audit_event(*a, **kw)
def _flush_audit_buffer(self): return self._audit.flush_audit_buffer()
def _write_audit_summary(self, tag="snapshot"): return self._audit.write_audit_summary(tag)
```

### 생성자 주입 파라미터

```python
class AuditService:
    def __init__(self, runtime_audit: list, project_paths_fn, ui_log_fn):
        # runtime_audit: self.runtime_audit 참조 공유
        # project_paths_fn: lambda -> self.current_project.paths (lazy 접근)
        # ui_log_fn: self.ui.log
```

### 완료 판정

- [ ] `python -m py_compile modules/core/services/audit_service.py`
- [ ] `pytest tests/test_audit_service.py` — 6개 이상
- [ ] `main_a.py`에서 `self._audit.audit_event` 호출 경로 동작 확인

### 중단 조건

- `_flush_audit_buffer`의 파일 I/O 경로(`self.current_project.paths.root / "logs"`)가 추출 후 접근 불가 → 즉시 중단, Facade 스텁 원복

---

## Batch 4B-2: FeedbackEnricher + NarrativeSummary 추출

| 항목 | 내용 |
|------|------|
| **추출 모듈** | `modules/core/feedback_enricher.py`, `modules/core/narrative_summary.py` |
| **크기** | FE ~434줄 + NS ~176줄 = ~610줄 |
| **리스크** | **LOW-MEDIUM** |
| **롤백 단위** | 단일 커밋 revert (두 모듈 동시) |

### FeedbackEnricher 포함 메서드 (18개)

| 메서드 | 원본 위치 | 크기 | 유형 |
|--------|----------|------|------|
| `_enrich_director_result` | `main_a.py:281-418` | 138줄 | **실질 로직** |
| `_analyze_score_breakdown` | `main_a.py:424-510` | 87줄 | **실질 로직** |
| `_get_dynamic_critical_keywords` | `main_a.py:533-571` | 39줄 | **실질 로직** |
| `_analyze_rejection_pattern_v60` | `main_a.py:614-674` | 61줄 | **실질 로직** |
| `_normalize_rejection_reason` | `main_a.py:676-699` | 24줄 | **실질 로직** |
| `_get_rejection_fix_guide` | `main_a.py:701-714` | 14줄 | **실질 로직** |
| `_quantify_reject_feedback` | `main_a.py:420-422` | 3줄 | Thin → `_feedback_system` |
| `_simplify_prompt_for_retry` | `main_a.py:513-515` | 3줄 | Thin → `_feedback_system` |
| `_build_strong_kind_feedback` | `main_a.py:517-519` | 3줄 | Thin → `_feedback_system` |
| `_build_focused_context` | `main_a.py:521-523` | 3줄 | Thin → `_feedback_system` |
| `_build_minimal_arc_context` | `main_a.py:525-527` | 3줄 | Thin → `_feedback_system` |
| `_generate_arc_position_guide` | `main_a.py:529-531` | 3줄 | Thin → `_prompt_builder` |
| `_generate_writer_guidance_v60_8` | `main_a.py:577-588` | 12줄 | Thin → `_prompt_builder` |
| `_generate_structured_arc_feedback` | `main_a.py:590-594` | 5줄 | Thin → `_feedback_system` |
| `_generate_reverse_feedback_stage4_to_3` | `main_a.py:596-600` | 5줄 | Thin → `_feedback_system` |
| `_generate_reverse_feedback_stage3_to_2` | `main_a.py:602-604` | 3줄 | Thin → `_feedback_system` |
| `_generate_arc_context_v60` | `main_a.py:606-608` | 3줄 | Thin → `_prompt_builder` |
| `_get_adaptive_feedback_intensity` | `main_a.py:610-612` | 3줄 | Thin → `_feedback_system` |

### FeedbackEnricher 제외 메서드

| 메서드 | 원본 위치 | 제외 사유 |
|--------|----------|----------|
| `_classify_rejection_feedback` | `main_a.py:2988-2990` | 이미 `_feedback_system` 위임. 영역 7(Validation Helpers)에 분류되어 4B-3으로 이동 |

### NarrativeSummary 포함 메서드 (2개)

| 메서드 | 원본 위치 | 크기 | 의존성 |
|--------|----------|------|--------|
| `_generate_narrative_summary` | `main_a.py:4166-4287` | 122줄 | `self.current_project.db` (get_recent_manuscripts, save_anchor), `self.sys.api_client` (LLM 호출), `self.ui`, DB 위반: `main_a.py:4278` (`db.conn.commit()`) |
| `_load_narrative_summaries` | `main_a.py:4289-4341` | 53줄 | `self.current_project.db` (load_anchor), `self.current_project.load_v20_anchor`, `self._narrative_summaries_cache` |

### NarrativeSummary 제외 메서드

없음 — 서사 요약은 이 2개 메서드로 완결.

### DB 위반 처리 계획

| 위반 | 위치 | 대응 |
|------|------|------|
| `self.current_project.db.conn.commit()` | `main_a.py:4278` | `DBAdapter.commit()` 또는 `db.commit()` 호출로 교체 |

### 완료 판정

- [ ] `python -m py_compile modules/core/feedback_enricher.py`
- [ ] `python -m py_compile modules/core/narrative_summary.py`
- [ ] `pytest tests/test_feedback_enricher.py` — 10개 이상
- [ ] `pytest tests/test_narrative_summary.py` — 4개 이상
- [ ] `stage4_orchestrator.py`에서 `self.app._enrich_director_result()` 호출 성공

### 중단 조건

- `_enrich_director_result` 서명 변경으로 `stage4_orchestrator.py` 호출 경로 깨짐 → Facade 스텁 서명 100% 보존 확인 후 재시도

---

## Batch 4B-3: ValidationHelpers + DataManager 추출

| 항목 | 내용 |
|------|------|
| **추출 모듈** | `modules/core/validation_helpers.py`, `modules/core/data_manager.py` |
| **크기** | VH ~332줄 + DM ~247줄 = ~579줄 |
| **리스크** | **MEDIUM** |
| **롤백 단위** | 단일 커밋 revert (두 모듈 동시) |

### ValidationHelpers 포함 메서드 (13개)

| 메서드 | 원본 위치 | 크기 | 의존성 |
|--------|----------|------|--------|
| `_validate_arc_mapping` | `main_a.py:2806-2846` | 41줄 | `self.ui`, `self._audit_event`, `self._extract_block_index` |
| `_extract_pattern_keywords` | `main_a.py:2848-2865` | 18줄 | 순수 함수 (re 모듈만) |
| `_pattern_presence_check` | `main_a.py:2867-2874` | 8줄 | `self._extract_pattern_keywords` |
| `_build_validation_context` | `main_a.py:2880-2884` | 5줄 | Thin → `_prompt_builder` |
| `_extract_npc_profiles` | `main_a.py:2890-2892` | 3줄 | Thin → `_prompt_builder` |
| `_get_character_traits` | `main_a.py:2894-2896` | 3줄 | Thin → `_prompt_builder` |
| `_load_character_archetypes` | `main_a.py:2898-2907` | 10줄 | 파일 I/O (JSON 로드) |
| `_get_archetype_reference_for_npcs` | `main_a.py:2909-2986` | 78줄 | `self._load_character_archetypes` |
| `_classify_rejection_feedback` | `main_a.py:2988-2990` | 3줄 | Thin → `_feedback_system` |
| `_validate_arc_data_fields` | `main_a.py:3095-3149` | 55줄 | `self.ui`, `self._audit_event` |
| `_load_genre_references` | `main_a.py:3151-3197` | 47줄 | `self.selected_genre`, `self.ui`, `self._audit_event`, 파일 I/O |
| `_validate_arc_integrity` | `main_a.py:3199-3227` | 29줄 | `self.ui`, `self._audit_event` |
| `_validate_blueprint_integrity` | `main_a.py:3229-3253` | 25줄 | `self.ui`, `self._audit_event` |

### ValidationHelpers 제외 메서드

| 메서드 | 원본 위치 | 제외 사유 |
|--------|----------|----------|
| `_get_arc_context_for_episode` | `main_a.py:3046-3093` | Stage 위임 로직과 밀결합 — Stage 디스패치 모듈(4B-5)로 이동 |
| `_show_volume_table` | `main_a.py:3255-3278` | UI 전용 — StageDispatcher(4B-5)로 이동 |
| `_extract_block_index` | (별도 위치) | `_validate_arc_mapping`이 호출하나, 단일 유틸리티라 ValidationHelpers에 포함 |

### DataManager 포함 메서드 (4개)

| 메서드 | 원본 위치 | 크기 | DB 위반 | 의존성 |
|--------|----------|------|---------|--------|
| `_reset_stage_2` | `main_a.py:3907-3919` | 13줄 | **1건** (`:3912` `cursor.execute`) | `self.current_project.db`, `self._safe_commit` |
| `_rewind_stage_2` | `main_a.py:3921-3955` | 35줄 | 0건 (safe API 사용) | `self.current_project`, `self.ui` |
| `_rollback_episode` | `main_a.py:3957-4099` | 143줄 | **15건** (`:3996-4059`) | `self.current_project.db` (직접 SQL 6+ 테이블), `self.memory` (VectorDB), 파일 I/O, `self._safe_commit` |
| `_wipe_production_data` | `main_a.py:4101-4156` | 56줄 | **4건** (`:4135,4138,4139`) | `self.current_project.db` (직접 SQL), `self.memory` (VectorDB), 파일 I/O |

### DataManager DB 위반 처리 계획

| 위반 위치 | 현재 코드 | 대응 |
|----------|----------|------|
| `main_a.py:3912` | `self.current_project.db.cursor.execute("DELETE FROM ...")` | `DBAdapter.raw_execute()` 사용 |
| `main_a.py:3996-3997` | `self.current_project.db.cursor.execute/fetchone` | `DBAdapter.raw_execute()` → dict 반환 |
| `main_a.py:4004-4005` | `db.cursor.execute("SELECT/UPDATE")` | `DBAdapter.raw_execute()` |
| `main_a.py:4021` | `db.cursor.execute("UPDATE anchors ...")` | `DBAdapter.raw_execute()` |
| `main_a.py:4040` | `db.cursor.execute(f"DELETE FROM {t} ...")` | `DBAdapter.raw_execute()` (화이트리스트 검증 이미 존재) |
| `main_a.py:4044-4046` | `db.cursor.execute("DELETE/UPDATE")` | `DBAdapter.raw_execute()` |
| `main_a.py:4059` | `db.cursor.execute("DELETE FROM sqlite_sequence ...")` | `DBAdapter.raw_execute()` |
| `main_a.py:4135` | `db.cursor.execute(f"DELETE FROM {t}")` | `DBAdapter.raw_execute()` |
| `main_a.py:4138` | `db.cursor.execute("UPDATE seeds ...")` | `DBAdapter.raw_execute()` |
| `main_a.py:4139` | `db.conn.commit()` | `db.commit()` |

### 완료 판정

- [ ] `python -m py_compile modules/core/validation_helpers.py`
- [ ] `python -m py_compile modules/core/data_manager.py`
- [ ] `pytest tests/test_validation_helpers.py` — 8개 이상
- [ ] `pytest tests/test_data_manager.py` — 8개 이상
- [ ] `_rollback_episode` 수동 테스트: 더미 프로젝트에서 롤백 1회 실행

### 중단 조건

- `_rollback_episode`의 직접 SQL(DELETE FROM 6+ 테이블)이 `DBAdapter.raw_execute()` 화이트리스트(`DELETE FROM` 허용 — `db_adapter.py:60`)에 걸리는 경우 → `raw_execute` 화이트리스트 확장 후 재시도
- HUD 롤백 로직(`main_a.py:3994-4027`)이 `self.selected_genre`, `self.current_project.master_bible`에 의존 — 추출 시 이 참조 경로가 깨지면 즉시 중단

---

## Batch 4B-4: Stage0Orchestrator + Stage3Orchestrator 추출

| 항목 | 내용 |
|------|------|
| **추출 모듈** | `modules/core/stage0_orchestrator.py`, `modules/core/stage3_orchestrator.py` |
| **크기** | S0 ~885줄 + S3 ~400줄 = ~1,285줄 |
| **리스크** | **MEDIUM-HIGH** |
| **롤백 단위** | 독립 커밋 2개 (S0, S3 분리 가능) |

### Stage3Orchestrator 포함 메서드 (1개, 400줄)

| 메서드 | 원본 위치 | 크기 | 핵심 의존성 |
|--------|----------|------|------------|
| `_stage_3_batch_blueprinting` | `main_a.py:3280-3679` | 400줄 | `self.state_tracker`, `self.world_state`, `self.fact_ledger`, `self.agents["three_phase_bp"]`, `self.agents["director"]`, `self.agents["state_extractor"]`, `self.current_project`, `self.selected_genre`, `self.ui`, `self._safe_commit`, `self._audit_event`, `self._get_arc_context_for_episode`, `self._validate_arc_data_fields`, `self._validate_blueprint_integrity`, `self._get_protagonist_name`, `self._fix_entity_registry_protagonist`, `self._get_max_episode_from_manuscripts`, `self._get_int_input`, `self._write_audit_summary` |

**V68 lazy init 결합** (`main_a.py:3296-3349`):
- StateTracker: `:3299-3312` (미초기화 시 아크 전체 스캔)
- WorldStateManager: `:3317-3329` (DB 로드)
- FactLedger: `:3334-3349` (DB 로드)

→ 추출 시 lazy init 로직을 Stage3Orchestrator 내부로 그대로 이전. `self.app`으로부터 `state_tracker`, `world_state`, `fact_ledger` 참조 유지.

### Stage0Orchestrator 포함 메서드 (10개, ~885줄)

| 메서드 | 원본 위치 | 크기 |
|--------|----------|------|
| `_ui_select_bible` | `main_a.py:1111-1133` | 23줄 |
| `_ui_select_treatment` | `main_a.py:1135-1180` | 46줄 |
| `_enrich_treatment_blocks` | `main_a.py:1182-1324` | 143줄 |
| `_phase_0_recovery` | `main_a.py:2022-2168` | 147줄 |
| `_stage_0_extended` | `main_a.py:2169-2373` | 205줄 |
| `_extend_blocks` | `main_a.py:2375-2421` | 47줄 |
| `_stage_1_volumes` | `main_a.py:2459-2641` | 183줄 |
| `_validate_volume_boundaries` | `main_a.py:2709-2740` | 32줄 |
| `_get_protagonist_name` | `main_a.py:1755-1783` | 29줄 |
| `_fix_entity_registry_protagonist` | `main_a.py:1785-1814` | 30줄 |

### 제외 메서드 (4B-5로 이동)

| 메서드 | 사유 |
|--------|------|
| `_get_max_episode_from_manuscripts` (`main_a.py:2642-2662`) | Stage 디스패치 유틸 — 4B-5 |
| `_calculate_arc_from_episode` (`main_a.py:2664-2669`) | Stage 디스패치 유틸 — 4B-5 |

### 완료 판정

- [ ] `python -m py_compile modules/core/stage0_orchestrator.py`
- [ ] `python -m py_compile modules/core/stage3_orchestrator.py`
- [ ] `python -c "from main_a import SovereignApp"` — import 성공
- [ ] Stage 3 수동 스모크 테스트: 1화 Blueprint 생성 1회

### 중단 조건

- Stage 3의 V68 lazy init 로직(`main_a.py:3296-3349`)이 추출 후 `self.state_tracker`/`self.world_state`/`self.fact_ledger` 접근 불가 → Facade 경로(`self.app.state_tracker`) 보존 확인 후 재시도
- `self.agents["three_phase_bp"].generate()` 호출(`main_a.py:3557-3572`)의 12개 파라미터 중 하나라도 누락 → 즉시 중단

---

## Batch 4B-5: AppBootstrap + StageDispatcher 추출

| 항목 | 내용 |
|------|------|
| **추출 모듈** | `modules/core/app_bootstrap.py`, `modules/core/stage_dispatcher.py` |
| **크기** | AB ~675줄 + SD ~426줄 = ~1,101줄 |
| **리스크** | **HIGH** |
| **롤백 단위** | 독립 커밋 2개 (AB, SD 분리 가능) |

### AppBootstrap 포함 메서드 (8개)

| 메서드 | 원본 위치 | 크기 |
|--------|----------|------|
| `boot` | `main_a.py:798-886` | 89줄 |
| `_load_models_yaml` | `main_a.py:888-904` | 17줄 |
| `_get_agent_model_map` | `main_a.py:906-914` | 9줄 |
| `_ignite_quad_cache_system` | `main_a.py:916-1060` | 145줄 |
| `_is_cache_alive` | `main_a.py:1062-1069` | 8줄 |
| `_check_vector_db_lock` | `main_a.py:1071-1109` | 39줄 |
| `_attach_agents` | `main_a.py:1326-1738` | 413줄 |
| `_emergency_shutdown` | `main_a.py:716-744` | 29줄 |

### StageDispatcher 포함 메서드 (7개)

| 메서드 | 원본 위치 | 크기 |
|--------|----------|------|
| `_run_main_process` | `main_a.py:1816-1922` | 107줄 |
| `_shutdown_app` | `main_a.py:1927-2020` | 94줄 |
| `_select_genre` | `main_a.py:3680-3887` | 208줄 |
| `_select_project` | `main_a.py:3888-3905` | 18줄 |
| `_get_arc_context_for_episode` | `main_a.py:3046-3093` | 48줄 |
| `_get_max_episode_from_manuscripts` | `main_a.py:2642-2662` | 21줄 |
| `_calculate_arc_from_episode` | `main_a.py:2664-2669` | 6줄 |

### 제외 메서드 (main_a.py에 잔류)

| 메서드 | 사유 |
|--------|------|
| `__init__` (`main_a.py:162-239`) | DI Container 역할 — SovereignApp 핵심. 4C에서 서비스 주입 전환 시 수정 |
| `_safe_commit` (`main_a.py:240-262`) | DB 트랜잭션 안전 래퍼 — 다수 모듈에서 `self.app._safe_commit()` 호출, 4C까지 잔류 |
| `_safe_commit_async` (`main_a.py:264-279`) | 동일 사유 |

### 완료 판정

- [ ] `python -m py_compile modules/core/app_bootstrap.py`
- [ ] `python -m py_compile modules/core/stage_dispatcher.py`
- [ ] `python -c "from main_a import SovereignApp; app = SovereignApp()"` — __init__ 성공
- [ ] 전체 pytest PASS
- [ ] Stage 0→2→4 파이프라인 수동 스모크 테스트 1회 (3화 이상)

### 중단 조건

- `_attach_agents`(`main_a.py:1326-1738`, 413줄)의 31개 V50 모듈 초기화에서 `self.xxx = ...` 직접 속성 할당이 추출 모듈에서 `self.app.xxx = ...`로 전환 시 AttributeError → `AppBootstrap.__init__(self, app)` 패턴으로 `app` 참조 전달 확인 후 재시도
- `boot()` 실행 시 전체 시스템 기동 실패 → **Phase 4B 전체 중단**, `git revert` 실행

---

## 전체 배치 요약

| 배치 | 모듈 | 메서드 수 | 줄수 | 리스크 | DB 위반 처리 |
|------|------|----------|------|--------|------------|
| 4B-1 | audit_service.py | 3 | ~83 | LOW | 0건 |
| 4B-2 | feedback_enricher.py + narrative_summary.py | 20 | ~610 | LOW-MED | 1건 (`main_a.py:4278`) |
| 4B-3 | validation_helpers.py + data_manager.py | 17 | ~579 | MED | 20건 (data_manager에 집중) |
| 4B-4 | stage0_orchestrator.py + stage3_orchestrator.py | 11 | ~1,285 | MED-HIGH | 0건 |
| 4B-5 | app_bootstrap.py + stage_dispatcher.py | 15 | ~1,101 | HIGH | 0건 (shutdown 1건 가능) |
| **합계** | **9개 신규 모듈** | **66** | **~3,658** | — | **21건** |

### 글로벌 중단 조건

1. **어느 배치든 `python -c "from main_a import SovereignApp"` 실패** → 해당 배치 revert
2. **기존 테스트 회귀 5개 이상** → 해당 배치 revert
3. **Stage 0→2→4 파이프라인 스모크 테스트 실패** → Phase 4B 전체 재검토
4. **순환 import 감지** → 해당 모듈의 import를 lazy import(함수 내 import)로 전환, 2회 이상 반복 시 중단
