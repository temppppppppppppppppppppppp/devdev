# Phase 4B Test Gate: 배치별 테스트 게이트 + 실행 명령

> 작성일: 2026-02-13
> SSOT: (1) 코드베이스 (커밋 `1b3de64`), (2) Phase 4B 문서군(`docs/phase4b_*.md`)
> 테스트 환경: Windows 11 + Python 3.12 + pytest

---

## 현재 테스트 인벤토리 (Phase 4A 완료 기준)

| 파일 | 테스트 수 | 유형 | 상태 |
|------|----------|------|------|
| `tests/test_protocols.py` | 24 | 단위 | ✅ PASS |
| `tests/test_protocols_services.py` | 13 | 단위 | ✅ PASS |
| `tests/test_db_adapter.py` | 22 | 단위 | ✅ PASS |
| `tests/test_genre_guards.py` | 24 | 단위 | ✅ PASS |
| `tests/test_prompt_loader.py` | 20 | 단위 | ✅ PASS |
| 기타 22개 파일 | ~780 | 혼합 | ✅ PASS |
| **합계** | **~883** | — | — |

---

## 글로벌 게이트 (모든 배치 공통)

### Gate G0: 사전 조건 (배치 시작 전)

```powershell
# G0-1: 기존 테스트 전체 PASS 확인
set PYTHONIOENCODING=utf-8 && pytest --tb=short -q
# 기대: 883 passed

# G0-2: py_compile 통과 (주요 파일)
python -m py_compile main_a.py
python -m py_compile modules/core/stage2_orchestrator.py
python -m py_compile modules/core/stage4_orchestrator.py

# G0-3: Git 작업 디렉토리 clean
git status --porcelain
# 기대: 빈 출력
```

**판정**: G0 실패 시 해당 배치 착수 금지.

### Gate GF: 사후 조건 (매 배치 커밋 후)

```powershell
# GF-1: 기존 테스트 회귀 없음
set PYTHONIOENCODING=utf-8 && pytest --tb=short -q
# 기대: 이전 배치 이상 passed (신규 포함)

# GF-2: 전체 py_compile
python -m py_compile main_a.py
# + 해당 배치 신규 모듈

# GF-3: import 스모크
python -c "from main_a import SovereignApp"
# 기대: 에러 없음
```

**판정**: GF 실패 시 해당 배치 `git revert` 후 원인 분석.

---

## Batch 4B-1 테스트 게이트: AuditService

### 신규 테스트: `tests/test_audit_service.py`

| # | 테스트 | 유형 | 게이트 |
|---|--------|------|--------|
| 1 | `test_audit_event_appends_to_buffer` | 단위 | **차단** |
| 2 | `test_audit_event_appends_to_runtime_audit` | 단위 | **차단** |
| 3 | `test_flush_writes_jsonl_file` | 단위 | **차단** |
| 4 | `test_flush_clears_buffer` | 단위 | **차단** |
| 5 | `test_write_summary_calls_flush_first` | 단위 | **차단** |
| 6 | `test_write_summary_creates_json_file` | 단위 | **차단** |
| 7 | `test_flush_no_project_skips` | 단위 | 허용 |
| 8 | `test_facade_stub_delegates_correctly` | 통합 | **차단** |

### 실행 명령

```powershell
# 4B-1 신규 테스트
set PYTHONIOENCODING=utf-8 && pytest tests/test_audit_service.py -v

# 4B-1 py_compile
python -m py_compile modules/core/services/audit_service.py

# 글로벌 회귀
set PYTHONIOENCODING=utf-8 && pytest --tb=short -q
```

### 게이트 판정

- **차단 테스트 7개 중 1개라도 FAIL** → 4B-1 커밋 금지
- **허용 테스트 FAIL** → WARNING 기록 후 진행 가능
- **기존 883개 회귀 1개라도** → 4B-1 커밋 금지

---

## Batch 4B-2 테스트 게이트: FeedbackEnricher + NarrativeSummary

### 신규 테스트: `tests/test_feedback_enricher.py`

| # | 테스트 | 유형 | 게이트 |
|---|--------|------|--------|
| 1 | `test_enrich_adds_action_items_on_reject` | 단위 | **차단** |
| 2 | `test_enrich_categorizes_logic_error` | 단위 | **차단** |
| 3 | `test_enrich_categorizes_quality_issue` | 단위 | **차단** |
| 4 | `test_analyze_score_breakdown_critical` | 단위 | **차단** |
| 5 | `test_analyze_score_breakdown_ok_returns_empty` | 단위 | **차단** |
| 6 | `test_dynamic_critical_keywords_base` | 단위 | 허용 |
| 7 | `test_dynamic_critical_keywords_with_failure_learner` | 단위 | 허용 |
| 8 | `test_analyze_rejection_pattern` | 단위 | **차단** |
| 9 | `test_normalize_rejection_reason` | 단위 | **차단** |
| 10 | `test_thin_stubs_delegate_correctly` | 통합 | **차단** |
| 11 | `test_facade_stub_signature_match` | 통합 | **차단** |

### 신규 테스트: `tests/test_narrative_summary.py`

| # | 테스트 | 유형 | 게이트 |
|---|--------|------|--------|
| 1 | `test_load_summaries_cache_hit` | 단위 | **차단** |
| 2 | `test_load_summaries_builds_pyramid` | 단위 | **차단** |
| 3 | `test_generate_calls_llm_and_saves` | 단위 (mock LLM) | **차단** |
| 4 | `test_generate_invalidates_cache` | 단위 | **차단** |
| 5 | `test_generate_uses_db_commit_not_conn` | 단위 | **차단** |

### 실행 명령

```powershell
# 4B-2 신규 테스트
set PYTHONIOENCODING=utf-8 && pytest tests/test_feedback_enricher.py tests/test_narrative_summary.py -v

# 4B-2 py_compile
python -m py_compile modules/core/feedback_enricher.py
python -m py_compile modules/core/narrative_summary.py

# 글로벌 회귀
set PYTHONIOENCODING=utf-8 && pytest --tb=short -q
```

### 게이트 판정

- **차단 테스트 14개 중 1개라도 FAIL** → 4B-2 커밋 금지
- `test_generate_uses_db_commit_not_conn`: DB 위반(`main_a.py:4278`) 수정 확인 — FAIL 시 즉시 수정 필수
- **기존 회귀** → 4B-2 커밋 금지

---

## Batch 4B-3 테스트 게이트: ValidationHelpers + DataManager

### 신규 테스트: `tests/test_validation_helpers.py`

| # | 테스트 | 유형 | 게이트 |
|---|--------|------|--------|
| 1 | `test_validate_arc_mapping_corrects_arc_no` | 단위 | **차단** |
| 2 | `test_validate_arc_mapping_corrects_ep_start` | 단위 | **차단** |
| 3 | `test_validate_arc_data_fields_repairs_none` | 단위 | **차단** |
| 4 | `test_validate_arc_data_fields_repairs_type` | 단위 | **차단** |
| 5 | `test_validate_arc_integrity_pass` | 단위 | **차단** |
| 6 | `test_validate_arc_integrity_fail_missing_keys` | 단위 | **차단** |
| 7 | `test_validate_blueprint_integrity_pass` | 단위 | **차단** |
| 8 | `test_validate_blueprint_integrity_fail` | 단위 | **차단** |
| 9 | `test_extract_pattern_keywords` | 단위 | 허용 |
| 10 | `test_load_genre_references` | 단위 | 허용 |

### 신규 테스트: `tests/test_data_manager.py`

| # | 테스트 | 유형 | 게이트 |
|---|--------|------|--------|
| 1 | `test_reset_stage_2_deletes_anchor` | 단위 (mock DB) | **차단** |
| 2 | `test_reset_stage_2_clears_arcs` | 단위 | **차단** |
| 3 | `test_rewind_stage_2_keeps_earlier_arcs` | 단위 | **차단** |
| 4 | `test_rollback_deletes_ep_tables` | 단위 (mock DB) | **차단** |
| 5 | `test_rollback_restores_hud` | 단위 (mock DB) | **차단** |
| 6 | `test_rollback_deletes_files` | 단위 (tmp_path) | **차단** |
| 7 | `test_wipe_deletes_production_tables` | 단위 (mock DB) | **차단** |
| 8 | `test_wipe_resets_seeds` | 단위 (mock DB) | **차단** |
| 9 | `test_rollback_uses_raw_execute_not_cursor` | 단위 | **차단** |

### 실행 명령

```powershell
# 4B-3 신규 테스트
set PYTHONIOENCODING=utf-8 && pytest tests/test_validation_helpers.py tests/test_data_manager.py -v

# 4B-3 py_compile
python -m py_compile modules/core/validation_helpers.py
python -m py_compile modules/core/data_manager.py

# 글로벌 회귀
set PYTHONIOENCODING=utf-8 && pytest --tb=short -q
```

### 게이트 판정

- **차단 테스트 17개 중 1개라도 FAIL** → 4B-3 커밋 금지
- `test_rollback_uses_raw_execute_not_cursor`: DB 위반 수정 확인 — FAIL 시 `raw_execute` 화이트리스트 확인
- **기존 회귀** → 4B-3 커밋 금지

---

## Batch 4B-4 테스트 게이트: Stage0/Stage3 Orchestrator

### 신규 테스트: `tests/test_stage3_orchestrator.py`

| # | 테스트 | 유형 | 게이트 |
|---|--------|------|--------|
| 1 | `test_lazy_init_state_tracker` | 단위 (mock app) | **차단** |
| 2 | `test_lazy_init_world_state` | 단위 (mock app) | **차단** |
| 3 | `test_lazy_init_fact_ledger` | 단위 (mock app) | **차단** |
| 4 | `test_skip_existing_blueprint` | 단위 (mock app) | **차단** |
| 5 | `test_continuity_block_no_prev` | 단위 (mock app) | **차단** |
| 6 | `test_consecutive_failure_abort` | 단위 (mock app) | **차단** |

### 신규 테스트: `tests/test_stage0_orchestrator.py`

| # | 테스트 | 유형 | 게이트 |
|---|--------|------|--------|
| 1 | `test_stage0_module_imports` | 스모크 | **차단** |
| 2 | `test_get_protagonist_name_from_bible` | 단위 | **차단** |
| 3 | `test_fix_entity_registry_protagonist` | 단위 | **차단** |
| 4 | `test_validate_volume_boundaries` | 단위 | 허용 |

### 실행 명령

```powershell
# 4B-4 신규 테스트
set PYTHONIOENCODING=utf-8 && pytest tests/test_stage3_orchestrator.py tests/test_stage0_orchestrator.py -v

# 4B-4 py_compile
python -m py_compile modules/core/stage0_orchestrator.py
python -m py_compile modules/core/stage3_orchestrator.py

# 글로벌 회귀
set PYTHONIOENCODING=utf-8 && pytest --tb=short -q

# [수동] Stage 3 스모크 테스트 (선택적 — LLM 비용 발생)
# 더미 프로젝트에서 1화 Blueprint 생성 실행
```

### 게이트 판정

- **차단 테스트 9개 중 1개라도 FAIL** → 4B-4 커밋 금지
- **특히 lazy init 3개 테스트**: V68 핵심 시스템이므로 반드시 PASS
- **기존 회귀** → 4B-4 커밋 금지

---

## Batch 4B-5 테스트 게이트: AppBootstrap + StageDispatcher

### 신규 테스트: `tests/test_app_bootstrap.py`

| # | 테스트 | 유형 | 게이트 |
|---|--------|------|--------|
| 1 | `test_attach_agents_creates_all_required` | 단위 (mock sys) | **차단** |
| 2 | `test_attach_agents_sets_state_tracker` | 단위 | **차단** |
| 3 | `test_attach_agents_sets_feedback_system` | 단위 | **차단** |
| 4 | `test_ignite_cache_system` | 단위 (mock API) | 허용 |
| 5 | `test_is_cache_alive_true` | 단위 (mock API) | 허용 |
| 6 | `test_is_cache_alive_false` | 단위 | 허용 |

### 신규 테스트: `tests/test_stage_dispatcher.py`

| # | 테스트 | 유형 | 게이트 |
|---|--------|------|--------|
| 1 | `test_dispatcher_module_imports` | 스모크 | **차단** |
| 2 | `test_get_arc_context_for_episode` | 단위 | **차단** |
| 3 | `test_calculate_arc_from_episode` | 단위 | **차단** |
| 4 | `test_get_max_episode_from_manuscripts` | 단위 | **차단** |

### 신규 테스트: `tests/test_import_smoke.py`

| # | 테스트 | 유형 | 게이트 |
|---|--------|------|--------|
| 1 | `test_sovereign_app_import` | 스모크 | **차단** |

### 실행 명령

```powershell
# 4B-5 신규 테스트
set PYTHONIOENCODING=utf-8 && pytest tests/test_app_bootstrap.py tests/test_stage_dispatcher.py tests/test_import_smoke.py -v

# 4B-5 py_compile (전체)
python -m py_compile main_a.py
python -m py_compile modules/core/app_bootstrap.py
python -m py_compile modules/core/stage_dispatcher.py
python -m py_compile modules/core/services/audit_service.py
python -m py_compile modules/core/feedback_enricher.py
python -m py_compile modules/core/narrative_summary.py
python -m py_compile modules/core/validation_helpers.py
python -m py_compile modules/core/data_manager.py
python -m py_compile modules/core/stage0_orchestrator.py
python -m py_compile modules/core/stage3_orchestrator.py

# 글로벌 회귀 (최종)
set PYTHONIOENCODING=utf-8 && pytest --tb=short -q

# [수동 필수] E2E 스모크 테스트
# Stage 0 → Stage 2 → Stage 4 파이프라인 1회 실행 (최소 3화)
```

### 게이트 판정

- **차단 테스트 8개 중 1개라도 FAIL** → 4B-5 커밋 금지
- **`test_sovereign_app_import` FAIL** → Phase 4B 전체 재검토
- **기존 회귀 5개 이상** → Phase 4B 전체 rollback 검토
- **E2E 스모크 테스트 실패** → Phase 4B 전체 rollback

---

## 최종 완료 게이트 (Phase 4B 전체)

### Gate FINAL: Phase 4B 완료 판정

```powershell
# F-1: 전체 py_compile (11개 파일)
python -m py_compile main_a.py
python -m py_compile modules/core/services/audit_service.py
python -m py_compile modules/core/feedback_enricher.py
python -m py_compile modules/core/narrative_summary.py
python -m py_compile modules/core/validation_helpers.py
python -m py_compile modules/core/data_manager.py
python -m py_compile modules/core/stage0_orchestrator.py
python -m py_compile modules/core/stage3_orchestrator.py
python -m py_compile modules/core/app_bootstrap.py
python -m py_compile modules/core/stage_dispatcher.py

# F-2: 전체 pytest PASS
set PYTHONIOENCODING=utf-8 && pytest --tb=short -q
# 기대: 883 + ~60 신규 = ~943 passed

# F-3: import 스모크
python -c "from main_a import SovereignApp"

# F-4: main_a.py 줄수 확인
python -c "print(len(open('main_a.py').readlines()))"
# 기대: ~1,200줄 이하 (현재 4,402줄에서 ~73% 감소)

# F-5: self.app 참조 카운트 무변경 확인
python -c "import re; t=open('modules/core/stage2_orchestrator.py').read(); print('stage2:', len(re.findall(r'self\.app\.', t)))"
python -c "import re; t=open('modules/core/stage4_orchestrator.py').read(); print('stage4:', len(re.findall(r'self\.app\.', t)))"
# 기대: stage2: 335, stage4: 300 (4B에서는 변경 없음)

# F-6: DB 위반 잔존 확인
python -c "import re; t=open('main_a.py').read(); print('main_a db violations:', len(re.findall(r'\.db\.(?:conn|cursor)\.', t)))"
# 기대: 0건 이하 (추출 모듈로 이동됨, 잔류는 _safe_commit만)
```

### Phase 4B 완료 체크리스트

| # | 항목 | 상태 |
|---|------|------|
| 1 | 전체 py_compile 11개 파일 PASS | [ ] |
| 2 | 전체 pytest ~943개 PASS | [ ] |
| 3 | `from main_a import SovereignApp` 성공 | [ ] |
| 4 | main_a.py ~1,200줄 이하 | [ ] |
| 5 | stage2/stage4 `self.app` 카운트 무변경 | [ ] |
| 6 | E2E 스모크: Stage 0→2→4 3화 이상 생산 | [ ] |
| 7 | 신규 9개 모듈 모두 독립 단위 테스트 존재 | [ ] |

---

## 테스트 추가 요약

| 배치 | 테스트 파일 | 차단 | 허용 | 합계 |
|------|-----------|------|------|------|
| 4B-1 | test_audit_service.py | 7 | 1 | 8 |
| 4B-2 | test_feedback_enricher.py | 9 | 2 | 11 |
| 4B-2 | test_narrative_summary.py | 5 | 0 | 5 |
| 4B-3 | test_validation_helpers.py | 8 | 2 | 10 |
| 4B-3 | test_data_manager.py | 9 | 0 | 9 |
| 4B-4 | test_stage3_orchestrator.py | 6 | 0 | 6 |
| 4B-4 | test_stage0_orchestrator.py | 3 | 1 | 4 |
| 4B-5 | test_app_bootstrap.py | 3 | 3 | 6 |
| 4B-5 | test_stage_dispatcher.py | 4 | 0 | 4 |
| 4B-5 | test_import_smoke.py | 1 | 0 | 1 |
| **합계** | **10개 파일** | **55** | **9** | **64** |

Phase 4B 완료 후 총 테스트: ~883 (기존) + ~64 (신규) = **~947개**
