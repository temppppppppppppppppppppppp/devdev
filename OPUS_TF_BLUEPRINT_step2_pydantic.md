# Step 2. Pydantic 모델 도입 — Opus TF 청사진

> **전제**: Step 1 완료 (장르 가드 YAML 외부화, ruff 정리)
> **위험도**: RISKY — 핵심 데이터 흐름 전체에 영향
> **예상 규모**: ~800줄 신규 + ~200줄 수정

---

## 1. 현재 상태 (문제)

프로젝트 전체가 **bare dict** 기반. 키 오타 → 런타임 에러, IDE 자동완성 불가.

```python
# 실제 코드 (stage4_orchestrator.py L387)
arc_data = next(a for a in self.app.current_project.arcs
    if a.get("ep_start", 0) <= next_ep <= a.get("ep_end", 0))

# 키 오타해도 None 반환 → 묵시적 실패
blueprint.get("scene_breakdwon", {})  # typo → 빈 dict, 에러 없음
```

- **Pydantic**: 미사용 (0건)
- **TypedDict**: 미사용 (0건)
- **@dataclass**: **40개 파일**에서 61건 사용 (`state_tracker`, `pacing_analyzer`, `pass_rate_monitor`, `power_scaling`, `quality_amplifier`, `seed_tracker`, `semantic_cache`, `project_manager`, `relationship_tracker` 등)

---

## 2. 대상 데이터 구조 (4종)

### 2-A. Arc 데이터

| 키 | 타입 | 비고 |
|---|---|---|
| `arc_no` | int | 필수 |
| `global_arc_no` | int | `arc_no` 별칭 (project_manager에서 사용) |
| `volume_no` | int | 볼륨 번호 |
| `ep_start` | int | 필수 |
| `ep_end` | int | 필수 |
| `ep_count` | int | 기본 5 |
| `tactical_doc` | str \| dict | 전술 문서 본체 |
| `beat_sequence` | list[dict] \| str | 비트 시퀀스 |
| `seed_injection` / `seeds` | list[dict] | 복선 정보 |
| `state_constraints` | dict | 하위 키 상세 아래 참조 |
| `joint_docs` | dict | |
| `status_shadow` | dict | `expected_injuries`, `internal_energy_loss` |
| `constraint_summary` | str | |
| `state_changes` | dict | |
| `hybrid_composition` | dict | `primary` 키 존재 (Arc 패턴 추적용) |
| `_ensemble_meta` | dict | FourPhase 반환 메타 (`best_strategy` 등) |

**`state_constraints` 하위 키** — Canonical Key Map:

| Canonical (Pydantic 필드명) | Schema 이름 (`response_schemas.py`) | 런타임 접근 (`constraint_compiler.py`) | 비고 |
|---|---|---|---|
| `arc_start_state` | `arc_start_state` | (직접 접근 없음) | `ARC_STATE_SCHEMA` 일치 |
| `arc_end_state` | `arc_end_state` | (직접 접근 없음) | 동일 |
| `protagonist_items` | `protagonist_items` | (직접 접근 없음) | |
| `distributed_items` | `distributed_items` | (직접 접근 없음) | ⚠️ 문서에 누락되어 있었음 |
| `items_consumed` | `items_consumed` (L249) | (직접 접근 없음) | ~~문서 오기: `consumed_items`~~ |
| `items_acquired` | (Schema 미정의) | L95 `.get("items_acquired")` | 런타임 전용 — adapter 필요 |
| `grants_received` | (Schema 미정의) | L140 `.get("grants_received")` | 런타임 전용 — adapter 필요 |
| `relationship_changes` | `relationship_changes` | (직접 접근 없음) | |
| `power_changes` | `power_changes` (L270) | (직접 접근 없음) | ~~문서 오기: `power_scaling`~~ |
| `foreshadowings` | `foreshadowings` | (직접 접근 없음) | |
| `continuity_checkpoints` | `continuity_checkpoints` | (직접 접근 없음) | |

> [!CAUTION]
> **3계층 불일치 존재**: Schema(`items_consumed`) ↔ 문서(~~`consumed_items`~~) ↔ 런타임(`items_acquired`/`grants_received`).
> Pydantic 모델에서는 **Schema 키를 canonical로 채택**하되, 런타임 전용 키는 `extra="allow"`로 수용.
> `constraint_compiler.py`가 접근하는 `items_acquired`/`grants_received`는 Schema에 없으므로,
> Arc 생성 파이프라인이 이 키를 주입하는 것. Pydantic 모델에서 Optional 필드로 정의한다.

**생산**: `stage2_orchestrator.py`
**저장**: `project_manager.save_v20_anchor('arcs', data)` → DB `json.dumps()` + txt 파일
**메모리**: `project_manager.arcs` (`list[dict]`)
**소비**: **43개 파일** (상세 목록 §7)

### 2-B. Blueprint 데이터

| 키 | 타입 | 비고 |
|---|---|---|
| `scene_breakdown` | dict | 씬별 상세 |
| `integrated_scenario` | str | 통합 시나리오 |
| `protagonist_state` | dict | |
| `relationship_changes` | list[dict] | |
| `time_flow` | str | |
| `start_location` / `location` | str | 별칭 관계 |
| `core_tension` | str | 핵심 갈등 |
| `expected_ending` | str | 예상 결말 |

**생산**: `three_phase_blueprint_generator.py` (Stage 3 전용 오케스트레이터 **없음**)
**저장**: `db_manager.save_blueprint(ep, data)` → `json.dumps()` + txt 파일
**소비**: **28개+ 파일** (상세 목록 §7)

### 2-C. 원고 후보 (Manuscript Candidate)

`chief_writer.generate_ensemble()` 반환값 (각 후보 dict):

| 키 | 타입 | 비고 |
|---|---|---|
| `strategy` | str | `"balanced"` / `"narrative"` / `"tension"` / `"error_fallback"` |
| `manuscript` | str | 원고 본문 |
| `title` | str | 에피소드 제목 |
| `strategy_name` | str | Stage4에서 사용하는 별칭 |

**Self-Critique 결과** dict:

| 키 | 타입 | 비고 |
|---|---|---|
| `has_issues` | bool | |
| `issues` | list[str] | |
| `severity` | str | |

**원고 캐시** (`_manuscript_cache`):

| 키 | 타입 | 비고 |
|---|---|---|
| `content` | str | 원고 본문 |
| `hud_snapshot` | dict | HUD 스냅샷 |

**생산**: `chief_writer.py` / `writer.py` (폴백)
**소비**: `stage4_orchestrator.py` (`candidates[i].get("manuscript")`), `project_manager.commit_full_episode_data()`

### 2-D. NPC 레지스트리 및 상태

#### NPC 엔트리 (bare dict)

| 키 | 타입 | 비고 |
|---|---|---|
| `name` | str | 필수 |
| `status` | str | `"alive"` / `"dead"` |
| `weapon` | str | |
| `level` | str | |
| `death_arc` | int \| None | 사망한 Arc |
| `last_arc` | int | 마지막 등장 Arc |
| *동적 필드* | Any | `PresetRegistry` 기반 확장 |

**생산**: `state_tracker.create_npc_entry()` (kwargs 병합)

#### EpisodeState (@dataclass — 유지)

| 필드 | 타입 | 기본값 |
|------|------|--------|
| `ep_num` | int | 필수 |
| `location` | str | `""` |
| `weapons` | List[str] | `[]` |
| `items` | List[str] | `[]` |
| `injuries` | str | `"정상"` |
| `internal_energy` | int | `100` |
| `relationships` | Dict[str, str] | `{}` |
| `extra_fields` | Dict[str, Any] | `{}` (동적 확장) |

> [!NOTE]
> `EpisodeState`는 이미 `@dataclass`로 잘 구현되어 있으며 `to_dict()`, `get()`, `set()` 메서드가 있음.
> **1단계에서 Pydantic 전환 대상 아님.** NPC 엔트리(bare dict)만 모델화.

### Phase A: 모델 정의 (신규 파일)

```
modules/models/
├── __init__.py
├── arc.py          # ArcData, StateConstraints, JointDocs, StatusShadow
├── blueprint.py    # Blueprint, SceneBreakdown, ProtagonistState
├── manuscript.py   # ManuscriptCandidate, ManuscriptResult
└── npc.py          # NPCEntry, NPCRelationship (state_tracker EpisodeState 유지)
```

> [!IMPORTANT]
> **Pydantic v2** 사용. `model_validate()` / `model_dump()` API.
> 기존 코드가 `dict.get()` 패턴에 의존하므로 **점진적 마이그레이션** 필수.

> [!TIP]
> `response_schemas.py` (574줄)에 이미 Gemini API용 `types.Schema`로 Arc/Director/Character 스키마가 정의되어 있음.
> Pydantic 모델 설계 시 **이 스키마를 참조**하여 키/타입 일치시킬 것.
> - `ARC_STATE_SCHEMA`: `location`, `equipment`, `injuries`, `internal_energy`
> - `ARC_STATE_CONSTRAINTS_SCHEMA`: `arc_start_state`, `arc_end_state`, `protagonist_items`, **`items_consumed`**, **`distributed_items`**, `relationship_changes`, **`power_changes`**, `foreshadowings`, `continuity_checkpoints`

### Phase B: 점진적 전환 전략

```python
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

# 방법: "입구에서 검증, 내부는 모델, 출구에서 dict"
# → 기존 코드 최소 변경

class ArcData(BaseModel):
    model_config = ConfigDict(extra="allow")  # v2: 미지 키 허용 (하위 호환)

    arc_no: int
    ep_start: int
    ep_end: int
    ep_count: int = 5
    tactical_doc: str = ""
    state_constraints: dict = Field(default_factory=dict)  # v2: mutable default
    joint_docs: dict = Field(default_factory=dict)
    status_shadow: dict = Field(default_factory=dict)
    constraint_summary: str = ""
    state_changes: dict = Field(default_factory=dict)
    # 런타임 전용 키 (Schema 미정의이나 constraint_compiler가 사용)
    items_acquired: Optional[list[str]] = None
    grants_received: Optional[list[str]] = None
```

**전환 순서**:
1. `ArcData` 모델 정의 → `stage2_orchestrator.py`의 Arc 생성 직후 `ArcData.model_validate(raw_dict)` 삽입
2. `Blueprint` 모델 정의 → Stage 3 Blueprint 로드 직후 검증
3. `ManuscriptCandidate` → `chief_writer.py` 반환값 구조화
4. NPC 엔트리 → `state_tracker.py` (기존 `@dataclass` → Pydantic 전환 or 유지)

### Phase C: writer.py 레거시 유틸 이전

`stage4_orchestrator.py`에서 `writer_agent`를 통해 호출하는 유틸 3개:

| 메서드 | 위치 | 호출 주체 | 이전 대상 |
|--------|------|-----------|-----------|
| `_build_mandatory_context(ep)` | `writer.py` L257-285 | `stage4_orchestrator.py` L501 | `prompt_builder.py` or `chief_writer.py` |
| `_build_anti_trope_instructions(genre)` | `writer.py` L287-295 | `stage4_orchestrator.py` L762 | `prompt_builder.py` |
| `_build_justification_guidance(hud, genre)` | `writer.py` L297-329 | `stage4_orchestrator.py` L767 | `prompt_builder.py` |

> [!WARNING]
> `writer.py`는 냉동인간(폴백) 전용이므로, 유틸 이전 후에도 `writer.py` 자체는 삭제하지 않는다.
> `write_v20_manuscript()` 본체는 stage4에서 여전히 사용 중.

---

## 4. 위험 요소 및 대응

| 위험 | 심각도 | 대응 |
|------|--------|------|
| Arc dict에 예측 불가 키 존재 | HIGH | `extra = "allow"` + 로그 경고 |
| LLM 응답이 dict 스키마 위반 | HIGH | `model_validate()`에서 `ValidationError` → 폴백 dict 유지 |
| **DB 직렬화**: `json.dumps(data_dict)` 기대 | HIGH | `model_dump()` 결과는 dict이므로 호환. 단 DB 로드 시 `model_validate(json.loads(row))` 필요 |
| **@dataclass 19파일 52건+와 공존** | MEDIUM | Pydantic은 `modules/models/`에만. 기존 @dataclass는 건드리지 않음 |
| 기존 `.get()` 호출부 전체 수정 필요 | MEDIUM | 1단계에서는 모델 삽입만, `.get()` 제거는 2단계 |
| `state_tracker.py` @dataclass → Pydantic 충돌 | MEDIUM | 1단계에서는 NPC 모델만, EpisodeState는 유지 |
| 순환 import | LOW | `modules/models/`를 독립 패키지로 유지 |
| **`project_manager.arcs`가 `list[dict]` 메모리** | MEDIUM | Pydantic 모델은 검증용. `arcs` 리스트 자체 교체는 2단계 |

---

## 5. 검증 계획

> [!IMPORTANT]
> `tests/test_pydantic_models.py`는 **현재 존재하지 않음**. Step 2 구현 시 생성 필요.
> 기존 테스트 28개 파일은 `tests/` 디렉토리에 있음 (`test_base_agent.py`, `test_chief_writer.py` 등).

### 5-1. 신규 테스트 파일 생성 (`tests/test_pydantic_models.py`)

```python
# tests/test_pydantic_models.py — Step 2 구현 시 생성
import pytest
from modules.models.arc import ArcData, StateConstraints
from modules.models.blueprint import Blueprint
from modules.models.manuscript import ManuscriptCandidate

def test_arc_model_validate_minimal():
    raw = {"arc_no": 1, "ep_start": 1, "ep_end": 5}
    arc = ArcData.model_validate(raw)
    assert arc.arc_no == 1

def test_arc_model_extra_keys_allowed():
    raw = {"arc_no": 1, "ep_start": 1, "ep_end": 5, "unknown_key": "hello"}
    arc = ArcData.model_validate(raw)
    assert arc.model_dump()["unknown_key"] == "hello"

def test_arc_model_dump_dict_compatible():
    raw = {"arc_no": 1, "ep_start": 1, "ep_end": 5, "tactical_doc": "test"}
    arc = ArcData.model_validate(raw)
    d = arc.model_dump()
    assert isinstance(d, dict)
    assert d["arc_no"] == 1

def test_state_constraints_canonical_keys():
    raw = {"arc_start_state": {}, "arc_end_state": {}, "items_consumed": ["gold"], "power_changes": {}}
    sc = StateConstraints.model_validate(raw)
    assert sc.items_consumed == ["gold"]
```

### 5-2. 검증 명령

```bash
# 1. 신규 모델 테스트
python -m pytest tests/test_pydantic_models.py -v

# 2. 기존 28개 테스트 회귀 (regression)
python -m pytest tests/ -v --tb=short

# 3. 인라인 스모크 테스트
python -c "
from modules.models.arc import ArcData
sample = {'arc_no': 1, 'ep_start': 1, 'ep_end': 5, 'ep_count': 5, 'tactical_doc': 'test'}
arc = ArcData.model_validate(sample)
print(f'OK: {arc.arc_no}, ep {arc.ep_start}-{arc.ep_end}')
assert isinstance(arc.model_dump(), dict)
"

# 4. ruff 통과
python -m ruff check modules/models/ --fix

# 5. compileall
python -m compileall modules/models/ -q
```

---

## 6. 선행 조건

- [x] Step 1 완료 (장르 가드 YAML 외부화)
- [ ] `pydantic` 설치: `pip install pydantic>=2.0`
- [ ] `requirements.txt`에 `pydantic>=2.0` 추가 (현재 **미포함**)
- [ ] `modules/models/` 디렉토리 생성

> [!NOTE]
> `pyproject.toml`에는 `dependencies` 섹션이 없음 (런타임 의존성 미선언). `requirements.txt`만 관리.

---

## 7. 영향 범위 — 스테이지별 전수조사 결과

> [!CAUTION]
> `arc_no` 하나만 grep해도 **43개 파일**에서 소비. 모델 변경 시 파급 범위가 매우 넓음.
> **점진적 전환(`extra="allow"` + `model_dump()` 호환)**이 필수인 이유.

### Stage 0 (세계 설정)
| 파일 | Arc dict 소비 | Blueprint 소비 |
|------|:---:|:---:|
| `stage0/reverse_expander.py` | ✅ | |

### Stage 2 (Arc 설계) — **Arc dict 생산 + 소비**
| 파일 | Arc dict 소비 | Blueprint 소비 |
|------|:---:|:---:|
| `stage2_orchestrator.py` (2117줄) | ✅ 생산 | |
| `stage2_optimizer.py` | ✅ | |
| `analyst.py` | ✅ | |
| `four_phase_arc_generator.py` | ✅ | |
| `arc_draft_validator.py` | ✅ | |
| `arc_critic.py` | ✅ | |
| `arc_corrector.py` | ✅ | |
| `arc_ensemble.py` | ✅ | |
| `unified_arc_validator.py` | ✅ | |
| `constraint_compiler.py` | ✅ | |
| `state_extractor.py` | ✅ | ✅ |
| `preflight_checker.py` | ✅ | ✅ |
| `negative_example_injector.py` | ✅ | |
| `continuity_arc.py` | ✅ | |
| `continuity_tracker.py` | ✅ | ✅ |
| `arc_summary_utils.py` | ✅ | |

### Stage 3 (Blueprint 설계) — **Blueprint dict 생산 + 소비**
| 파일 | Arc dict 소비 | Blueprint 소비 |
|------|:---:|:---:|
| `three_phase_blueprint_generator.py` | ✅ | ✅ 생산 |
| `blueprint_constraint_compiler.py` | ✅ | ✅ |
| `blueprint_ensemble.py` | | ✅ |
| `unified_blueprint_validator.py` | ✅ | ✅ |
| `continuity_blueprint.py` | | ✅ |

### Stage 4 (원고 집필) — **주요 소비처**
| 파일 | Arc dict 소비 | Blueprint 소비 |
|------|:---:|:---:|
| `stage4_orchestrator.py` (1596줄) | ✅ | ✅ |
| `chief_writer.py` (1832줄) | | ✅ |
| `writer.py` (450줄, 레거시) | | ✅ |
| `director_auditor.py` | ✅ | ✅ |
| `director_ensemble.py` | ✅ | ✅ |
| `director_continuity.py` | | ✅ |
| `manuscript_validator.py` | | ✅ |
| `continuity_manuscript.py` | | ✅ |

### Cross-Stage (공통 인프라)
| 파일 | Arc dict 소비 | Blueprint 소비 |
|------|:---:|:---:|
| `prompt_builder.py` (772줄) | ✅ | ✅ |
| `project_manager.py` | ✅ | ✅ |
| `state_tracker.py` (1085줄) | ✅ | ✅ |
| `state_tracker_npc.py` | ✅ | ✅ |
| `state_tracker_financial.py` | ✅ | |
| `state_tracker_plots.py` | ✅ | |
| `feedback_system.py` | ✅ | ✅ |
| `constitutional_checker.py` | ✅ | ✅ |
| `constraint_db.py` | ✅ | |
| `blueprint_memory.py` | ✅ | ✅ |
| `semantic_item_registry.py` | ✅ | |
| `agent_intelligence.py` | ✅ | |
| `context_compression.py` | | ✅ |
| `cross_agent_verifier.py` | ✅ | ✅ |
| `tree_of_thoughts.py` | ✅ | ✅ |
| `diversity_sampler.py` | | ✅ |
| `expert_mixture.py` | | ✅ |
| `quality_amplifier.py` | | ✅ |
| `confidence_calibration.py` | | ✅ |
| `adversarial_self_play.py` | | ✅ |
| `pattern_tracker.py` | | ✅ |
| `pre_director_checklist.py` | | ✅ |
| `writer_template.py` | | ✅ |
| `world_state.py` | | ✅ |
| `fact_ledger.py` | | ✅ |
| `db_manager.py` | | ✅ |
| `blocking_validator.py` | | ✅ |

### 합계
| 데이터 | 소비 파일 수 |
|--------|:-----------:|
| **Arc dict** | **43** |
| **Blueprint dict** | **28+** |
| **총 고유 파일** | **~50** |

> [!IMPORTANT]
> Phase B의 점진적 전환이 핵심 — 모델을 정의해도 기존 `.get()` 호출부는 **1단계에서 건드리지 않는다**.
> 입구(`model_validate`)와 출구(`model_dump()`)만 삽입하여 기존 코드와 100% 호환 유지.

---

## 8. 기존 스키마 참조 자료

### `response_schemas.py` (574줄) — Gemini API용

Pydantic 모델 설계 시 키/타입을 일치시켜야 하는 기존 스키마:

| 스키마 | 역할 | 핵심 키 |
|--------|------|--------|
| `ARC_STATE_SCHEMA` | Arc 상태 | `location`, `equipment`, `injuries`, `internal_energy` |
| `ARC_STATE_CONSTRAINTS_SCHEMA` | Arc 제약 | `arc_start_state`, `arc_end_state`, `protagonist_items`, **`items_consumed`**, **`distributed_items`**, `relationship_changes`, **`power_changes`**, `foreshadowings` |
| `DIRECTOR_AUDIT_SCHEMA` | Director 심사 | `decision`, `score`, `loop_detected`, `reason` |
| `CHARACTER_LOGIC_SCHEMA` | 캐릭터 검증 | `decision`, `score`, `violations`, `severity` |
| `SCORING_RESULT_SCHEMA` | 채점 | `tier`, `passed`, `total_score`, `breakdown` |

> [!WARNING]
> 이 스키마들은 Gemini `types.Schema` 객체이므로 Pydantic과 직접 호환되지 않음.
> Pydantic 모델 정의 시 키 이름과 타입을 **수동으로 매핑**해야 함.

### `main_a.py` 접근 패턴 (God Object)

| 패턴 | 횟수 | 대상 |
|------|:----:|------|
| `self.current_project.arcs` | 11 | Arc list[dict] 직접 접근 |
| `self.current_project.arcs[i].get(...)` | 0 | (해당 리터럴 패턴 없음) |
| `self.current_project.get_blueprint(ep)` | 4 | Blueprint 로드 |
| `self.current_project.save_v20_anchor("arcs", ...)` | 1 | Arc 저장 |
| `self.current_project.save_episode_blueprint(ep, bp)` | 1 | Blueprint 저장 |
| `self.current_project.save_v20_anchor("style_guide", ...)` | 3 | StyleGuide 저장 |

> [!NOTE]
> `main_a.py`는 God Object (`SovereignApp`)이므로 Step 7에서 분해 예정.
> Step 2에서는 `main_a.py`를 수정하지 않음. `model_dump()` 호환으로 간접 적용.

---

## 9. Pydantic 대상 외 구조체 (존재 인지만 하고 전환 안 함)

| 구조체 | 파일 | 유형 | 이유 |
|--------|------|------|------|
| `StyleGuide` | `stage0/style_extractor.py` | @dataclass (22필드) | 이미 `to_dict()`/`from_dict()` 보유. DB 앵커로 저장/로드 완비. |
| `EpisodeState` | `state_tracker.py` | @dataclass (8필드) | `to_dict()`/`get()`/`set()` 메서드 완비. 동적 확장(`extra_fields`). |
| `StateTransition` | `state_tracker.py` | @dataclass | 단순 데이터 홀더. |
| `ProjectPaths` | `project_manager.py` | @dataclass (5필드) | 경로 전용, 단순. |
| 15개+ 기타 @dataclass | 각종 모듈 | @dataclass | 각각 독립적 내부 사용. 외부 데이터 유량 없음. |

---

## 10. 주의사항

### 성능
- `model_validate()`는 필드 수에 비례하여 오버헤드 남 (`~10µs/검증`)
- Arc 설계 경로는 문제 없음 (회당 1회)
- **Stage 4 문필 경로는 주의**: 재시도 루프 내부에서 매회 검증하면 누적 오버헤드

### `_auto_sanitize_injuries()` 위치
- `FourPhaseArcGenerator._auto_sanitize_injuries()`는 Arc dict를 **직접 수정** (in-place mutation)
- `model_validate` 삽입 시 이 메서드 **이후에** 배치해야 함 (sanitize 후 유효성 검증)

### Arc dict의 `_ensemble_meta` 키
- 이 키는 FourPhase 내부 메타데이터로, DB에 저장되어도 무해
- Pydantic 모델에서 `extra = "allow"`로 자동 허용되므로 별도 필드 정의 불필요
