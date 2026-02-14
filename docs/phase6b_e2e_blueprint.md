# Phase 6-B: E2E 테스트 청사진

> **작성일**: 2026-02-14
> **전제**: Phase 3-5A(NPC 이력), 5-B(Settings 외부화) 완료
> **목표**: Stage 0→2→4 파이프라인을 mock LLM으로 1~2화 안정 통과시키는 자동화 E2E 테스트

---

## 1. 현황 분석

### 기존 테스트 현황

| 구분 | 파일 | 내용 |
|------|------|------|
| 단위 | `test_stage4_orchestrator.py` | 패치 모드 분기 로직만 (실 파이프라인 미실행) |
| 단위 | `test_stage2_pipeline.py` | Analyst/Stage2 유틸 함수 |
| 단위 | `test_npc_history.py` | NPC 이력 DB CRUD + 기록 API (29건) |
| 단위 | `test_config_manager.py` | ConfigManager + _threshold() (25건) |
| 통합 | `test_integration.py` | Bible 로드/DB 동기화 수준 |
| 수동 | `tests/stage4_v2_test/test_episode_1.py` | 실 API 호출 (CI 불가) |

**부재**: Stage 2→4 파이프라인을 mock LLM으로 end-to-end 실행하는 테스트 = **0건**

### 왜 필요한가

1. Phase 3-5A/5-B에서 validator, npc_history, threshold_helper 변경 → 회귀 확인 수단 필요
2. NPC 연속성 24개 시나리오 중 자동 검증은 사망NPC 1개뿐
3. Phase 4(구조 개선) 진행 시 안전망

---

## 2. 전략: 3-Layer 테스트

| Layer | 범위 | Mock | DB | 속도 | 이번 범위 |
|-------|------|------|-----|------|-----------|
| **L1: Smoke** | 오케스트레이터 초기화 + 검증 파이프라인 해피패스 | LLM 전체 | tmp_path 파일 SQLite | <5초 | **포함** |
| **L2: Scenario** | NPC 연속성, 재시도/복구, 패치 모드 | LLM mock | tmp_path 파일 SQLite | <15초 | **포함** |
| **L3: Live** | 실제 API 호출 (선택적, CI 제외) | 없음 | 파일 SQLite | 분 단위 | 백로그 |

---

## 3. 파일 구조

```
tests/e2e/
├── __init__.py                      # 패키지 마커
├── conftest.py                      # E2E 전용 fixtures (~200줄)
├── test_smoke_pipeline.py           # L1: 기본 통과 (~200줄)
├── test_npc_continuity_e2e.py       # L2: NPC 시나리오 (~250줄)
└── test_retry_recovery_e2e.py       # L2: 재시도/복구 (~200줄)
```

**수정 금지**: 프로덕션 코드 전체. 테스트 인프라만 추가.

---

## 4. Fixtures 설계 — `conftest.py`

### 4-1. 실제 DBManager (tmp_path 파일 DB)

```python
@pytest.fixture
def e2e_db(tmp_path):
    db = DBManager(tmp_path / "e2e.db")
    yield db
    db.close()
```

### 4-2. 샘플 데이터 (고정)

```python
@pytest.fixture
def e2e_bible():
    return {
        "MasterBible": {
            "ProjectData": {"CoreIdentity": {"desire": "천하제일"}},
            "AssetLibrary": {
                "KeyNPCs": [
                    {"name": "노사부", "role": "mentor", "status": "alive"},
                    {"name": "흑풍", "role": "villain", "status": "alive"},
                ],
                "Key_Items": [{"name": "청풍검", "status": "소지"}],
            },
            "protagonist_config": {
                "name": "이청풍",
                "world_origin": "현대인",
                "incarnation_type": "회귀자",
            },
        }
    }

@pytest.fixture
def e2e_arc():
    return {
        "arc_no": 1, "ep_start": 1, "ep_end": 10, "ep_count": 10,
        "tactical_doc": "이청풍이 청풍산장에서 수련을 시작하고...",
        "state_changes": {"npc_deaths": [], "relationship_changes": []},
        "constraint_summary": "사망 NPC 없음",
    }

@pytest.fixture
def e2e_blueprint():
    return {
        "ep_number": 1, "title": "운명의 시작",
        "scene_breakdown": [
            {"scene_num": 1, "location": "청풍산장", "characters": ["이청풍", "노사부"]},
            {"scene_num": 2, "location": "연무장", "characters": ["이청풍"]},
            {"scene_num": 3, "location": "뒤산", "characters": ["이청풍", "흑풍"]},
        ],
        "integrated_scenario": "이청풍이 노사부에게 검을 배우고, 흑풍과 조우한다.",
    }
```

### 4-3. Mock LLM 응답

```python
MOCK_MANUSCRIPT = "이청풍은 새벽녘에 눈을 떴다. " * 300  # ~5100자 (>MIN 4000)

MOCK_ENSEMBLE = [
    {"text": MOCK_MANUSCRIPT, "strategy_name": "balanced", "title": "운명의 시작"},
    {"text": MOCK_MANUSCRIPT, "strategy_name": "narrative", "title": "운명의 시작"},
    {"text": MOCK_MANUSCRIPT, "strategy_name": "tension", "title": "운명의 시작"},
]

MOCK_DIRECTOR_PASS = {"selected": "A", "verdict": "PASS", "score": 85, "reason": "좋은 원고", "feedback": ""}
MOCK_DIRECTOR_REJECT = {"selected": "A", "verdict": "REJECT", "score": 45, "reason": "부족", "feedback": "개선 필요"}
```

### 4-4. Stage4Context 수동 조립

```python
@pytest.fixture
def e2e_stage4_ctx(e2e_db, e2e_bible, mock_llm_client):
    """필수 5종 실제, 나머지 MagicMock"""
    from modules.core.stage4_context import Stage4Context
    # ui, current_project, agents, sys, state_tracker
    # + 확장 10종 (MagicMock)
    # + 콜백 7종 (lambda no-op)
    return ctx
```

### 4-5. Mock 대상 목록

| 대상 | 메서드 | Mock 반환 |
|------|--------|-----------|
| ChiefWriter | `generate_ensemble()` | 3개 후보 (~5100자, >MIN 4000) |
| ChiefWriter | `regenerate_with_feedback()` | 3개 재작성 후보 |
| ChiefWriter | `patch_with_feedback()` | 3개 패치 후보 |
| Director | `select_and_judge_ensemble()` | verdict dict |
| Stage4Orch | `_extract_chain_link()` | chain_link dict |
| BaseAgent | `ask()` | 호출별 고정 JSON (monkeypatch) |

---

## 5. 테스트 명세

### L1: Smoke — `test_smoke_pipeline.py` (8건)

| # | 테스트 | 검증 |
|---|--------|------|
| 1 | `test_stage4_context_creation` | Stage4Context DI 22개 슬롯 조립 성공 |
| 2 | `test_db_schema_complete` | DBManager 테이블 10+ 생성 확인 |
| 3 | `test_bible_db_roundtrip` | Bible 저장 → 로드 일치 |
| 4 | `test_blueprint_db_roundtrip` | Blueprint 저장 → 로드 일치 |
| 5 | `test_validation_happy_path` | 정상 원고(~5100자) → 6-tier PASS |
| 6 | `test_blocking_min_length_reject` | 4000자 미만 → BLOCKING REJECT |
| 7 | `test_world_state_init_save_load` | WorldStateManager 초기화 → DB → 로드 |
| 8 | `test_fact_ledger_init_save_load` | FactLedger 초기화 → DB → 로드 |

### L2: NPC 시나리오 — `test_npc_continuity_e2e.py` (7건)

참고자료 3-C 시나리오 기반:

| # | 테스트 | 시나리오 | 검증 |
|---|--------|---------|------|
| 1 | `test_dead_npc_action_rejected` | ② 사망NPC 행동 | blocking REJECT |
| 2 | `test_dead_npc_recall_allowed` | ② 사망NPC 회상 | blocking PASS |
| 3 | `test_npc_history_records_death` | DB 이력 | npc_history 1건 삽입 |
| 4 | `test_npc_history_records_weapon_change` | DB 이력 | weapon diff 기록 |
| 5 | `test_personality_sudden_change_warning` | ③ 성격급변 | continuity warning |
| 6 | `test_npc_history_in_validation_context` | 통합 | validation_context에 npc_history 존재 |
| 7 | `test_threshold_override_via_yaml` | 5-B 통합 | YAML 값 → validator 반영 |

### L2: 재시도/복구 — `test_retry_recovery_e2e.py` (7건)

| # | 테스트 | 시나리오 | 검증 |
|---|--------|---------|------|
| 1 | `test_round0_pass_saves_manuscript` | 1라운드 합격 | DB manuscripts 저장 |
| 2 | `test_round0_reject_triggers_round1` | 불합격 | regenerate_with_feedback 호출 |
| 3 | `test_patch_mode_entry_score_60` | score=60, round=1 | patch_with_feedback 호출 |
| 4 | `test_patch_mode_boundary_50` | score=50 경계값 | patch_with_feedback 호출 |
| 5 | `test_low_score_full_rewrite` | score=30 | regenerate (패치 아님) |
| 6 | `test_all_rounds_fail_frozen_human` | 3라운드 전패 | legacy Writer 호출 |
| 7 | `test_chain_link_saved_after_pass` | 합격 후 | DB anchor chain_link_1 존재 |

---

## 6. 검증 게이트

```bash
# Gate 1: py_compile
python -m py_compile tests/e2e/conftest.py
python -m py_compile tests/e2e/test_smoke_pipeline.py
python -m py_compile tests/e2e/test_npc_continuity_e2e.py
python -m py_compile tests/e2e/test_retry_recovery_e2e.py

# Gate 2: SovereignApp import
python -c "from main_a import SovereignApp; print('OK')"

# Gate 3: E2E 테스트
# cmd:
set PYTHONIOENCODING=utf-8
# PowerShell:
# $env:PYTHONIOENCODING='utf-8'
pytest tests/e2e/ -v

# Gate 4: 기존 테스트 회귀
pytest tests/test_npc_history.py tests/test_config_manager.py tests/test_stage4_orchestrator.py -v

# Gate 5: pre-commit
pre-commit run --files tests/e2e/conftest.py tests/e2e/test_smoke_pipeline.py tests/e2e/test_npc_continuity_e2e.py tests/e2e/test_retry_recovery_e2e.py
```

---

## 7. 리스크 및 완화

| 리스크 | 완화 |
|--------|------|
| Stage4Context 조립 복잡 (22 슬롯) | 필수 5종만 실제, 나머지 MagicMock |
| async 메서드 테스트 | `pytest-asyncio` 사용 |
| Mock 응답 ≠ 실 파이프라인 | `_extract_json_robust()` 통과하는 JSON |
| PromptLoader 싱글톤 캐시 | 실 YAML 사용, 리셋 불필요 |
| 프로덕션 코드 변경 유혹 | 수정 금지 정책 (테스트만 추가) |

---

## 8. 산출물 요약

- **tests/e2e/**: 4개 파일, ~850줄, 22개 테스트
- **L1 Smoke 8건**: DB 라운드트립, 검증 해피패스, V68 시스템 초기화
- **L2 NPC 7건**: 사망NPC 차단/회상, 이력 기록, 성격급변, validation_context 통합
- **L2 Recovery 7건**: 3라운드 재시도, 패치 분기(경계값 포함), chain_link 후처리
- **프로덕션 코드 변경 0건**
- **DoD**: 22/22 PASS, 기존 테스트 회귀 없음, pre-commit 통과
