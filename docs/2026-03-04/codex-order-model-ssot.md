# Codex Order: 모델 SSOT — models.yaml 단일 참조 통일

> **목적**: 모델명 변경 시 `config/models.yaml` 한 곳만 수정하면 전체 반영.
> **현황**: `constants.py`(16곳) + `config_manager.py`(5곳) + `state_locked_arc_generator.py`(2곳) + `narrative_structure_analyzer.py`/`self_reflection.py`/`tree_of_thoughts.py`(각 1곳) 분산.
> **금지**: 명세에 없는 파일 수정. 모델 값 자체를 변경하는 것 (구조 변경만, 값 보존).

---

## 0) 강제 제약

- 각 Phase 완료 후 `python -m py_compile` 문법 검사 필수.
- 모델 값 자체를 변경하지 말 것 (현재 `gemini-2.5-pro`/`gemini-2.5-flash` 배정 유지).
- 출력 보고서: `C:/Users/wjjo/Desktop/글도비/docs/2026-03-04/model-ssot-implementation-result.md`

---

## Phase 1: `config/models.yaml` — `role_constants` 섹션 추가

파일 말미에 추가:

```yaml
# ── [SSOT] 추상 역할 상수 — constants.py AIModels에서 참조 ──────────────────
role_constants:
  pro_main: "gemini-2.5-pro"      # 고사양: writer/architect/analyst/director 전용
  flash_main: "gemini-2.5-flash"  # 경량: module/analysis/summary 전용
  emergency: "gemini-2.5-pro"     # 긴급/429 폴백
```

---

## Phase 2: `modules/core/constants.py` — AIModels SSOT 전환

### 2-A: 파일 상단 import 직후, AIModels 클래스 직전에 헬퍼 함수 추가

```python
def _load_model_from_yaml(section: str, key: str, fallback: str) -> str:
    """[SSOT] config/models.yaml에서 모델명 로드. 파일 없으면 fallback 반환."""
    try:
        from pathlib import Path
        import yaml  # PyYAML (requirements에 이미 존재)

        _yaml_path = Path(__file__).parent.parent.parent / "config" / "models.yaml"
        if _yaml_path.exists():
            _data = yaml.safe_load(_yaml_path.read_text(encoding="utf-8"))
            _val = (_data or {}).get(section, {}).get(key)
            if _val and isinstance(_val, str):
                return _val
    except Exception:
        pass
    return fallback
```

### 2-B: AIModels 클래스 본문 전체 교체

**현재:**
```python
class AIModels:
    """AI 모델 이름 상수"""

    # [V60.65] 기본 3-pro, 할당량 초과 시 2.5-pro 폴백

    # [V65] 경량/보조 모델 (SSOT — main_a.py, stage2_orchestrator.py 등에서 참조)
    V50_MODULE_MODEL = "gemini-2.5-flash"  # V50 품질 모듈 전용 (SelfReflector, CrossVerifier 등)
    FLASH_ANALYSIS_MODEL = "gemini-2.5-flash"  # 경량 분석/추출용 (Preflight, StateExtractor 등)
    SUMMARY_MODEL = "gemini-2.5-flash"  # 요약/저비용 LLM 호출용

    # 점진적 모델 업그레이드 체계 - Architect
    TIER_1_ARCHITECT = "gemini-2.5-pro"  # 1차 시도: 3 Pro
    TIER_2_ARCHITECT = "gemini-2.5-pro"  # 2차 시도: 3 Pro
    TIER_3_ARCHITECT = "gemini-2.5-pro"  # 3차+ 시도: 3 Pro

    # 점진적 모델 업그레이드 체계 - Writer
    TIER_1_WRITER = "gemini-2.5-pro"  # 1차 시도: 3 Pro
    TIER_2_WRITER = "gemini-2.5-pro"  # 2차 시도: 3 Pro
    TIER_3_WRITER = "gemini-2.5-pro"  # 3차 시도 이후: 3 Pro

    EMERGENCY_FALLBACK = "gemini-2.5-pro"  # [V60.65] 긴급/할당량 초과 시 2.5 Pro
    QUOTA_FALLBACK = "gemini-2.5-pro"  # [V60.65] 429 에러 시 폴백 모델
    DEFAULT_WRITER = "gemini-2.5-pro"
    DEFAULT_ARCHITECT = "gemini-2.5-pro"
    DEFAULT_ANALYST = "gemini-2.5-pro"
    DEFAULT_REVIEWER = "gemini-2.5-pro"

    # [V40 Fix] Stage 4 전용 고정 모델
    STAGE4_FIXED_WRITER_MODEL = "gemini-2.5-pro"

    # Stage 2 전용 모델 상수
    STAGE2_MAIN_MODEL = "gemini-2.5-pro"  # Stage 2 주요 생성 모델
    STAGE2_EXTRACTION_MODEL = "gemini-2.5-pro"  # Stage 2 추출 모델
    STAGE2_VALIDATION_MODEL = "gemini-2.5-pro"  # Stage 2 검증 모델
```

**변경 후:**
```python
class AIModels:
    """AI 모델 이름 상수 — [SSOT] config/models.yaml role_constants/agents 참조."""

    # ── 경량/보조 모델 ────────────────────────────────────────────────────────
    V50_MODULE_MODEL = _load_model_from_yaml("role_constants", "flash_main", "gemini-2.5-flash")
    FLASH_ANALYSIS_MODEL = _load_model_from_yaml("role_constants", "flash_main", "gemini-2.5-flash")
    SUMMARY_MODEL = _load_model_from_yaml("role_constants", "flash_main", "gemini-2.5-flash")

    # ── Architect 티어 ────────────────────────────────────────────────────────
    TIER_1_ARCHITECT = _load_model_from_yaml("role_constants", "pro_main", "gemini-2.5-pro")
    TIER_2_ARCHITECT = _load_model_from_yaml("role_constants", "pro_main", "gemini-2.5-pro")
    TIER_3_ARCHITECT = _load_model_from_yaml("role_constants", "pro_main", "gemini-2.5-pro")

    # ── Writer 티어 ──────────────────────────────────────────────────────────
    TIER_1_WRITER = _load_model_from_yaml("role_constants", "pro_main", "gemini-2.5-pro")
    TIER_2_WRITER = _load_model_from_yaml("role_constants", "pro_main", "gemini-2.5-pro")
    TIER_3_WRITER = _load_model_from_yaml("role_constants", "pro_main", "gemini-2.5-pro")

    # ── 폴백 ─────────────────────────────────────────────────────────────────
    EMERGENCY_FALLBACK = _load_model_from_yaml("role_constants", "emergency", "gemini-2.5-pro")
    QUOTA_FALLBACK = _load_model_from_yaml("role_constants", "emergency", "gemini-2.5-pro")

    # ── 기본값 ────────────────────────────────────────────────────────────────
    DEFAULT_WRITER = _load_model_from_yaml("role_constants", "pro_main", "gemini-2.5-pro")
    DEFAULT_ARCHITECT = _load_model_from_yaml("role_constants", "pro_main", "gemini-2.5-pro")
    DEFAULT_ANALYST = _load_model_from_yaml("role_constants", "pro_main", "gemini-2.5-pro")
    DEFAULT_REVIEWER = _load_model_from_yaml("role_constants", "pro_main", "gemini-2.5-pro")

    # ── Stage 전용 ───────────────────────────────────────────────────────────
    STAGE4_FIXED_WRITER_MODEL = _load_model_from_yaml("agents", "chief_writer", "gemini-2.5-pro")
    STAGE2_MAIN_MODEL = _load_model_from_yaml("agents", "four_phase_arc_generator", "gemini-2.5-pro")
    STAGE2_EXTRACTION_MODEL = _load_model_from_yaml("agents", "state_locked_arc_generator", "gemini-2.5-pro")
    STAGE2_VALIDATION_MODEL = _load_model_from_yaml("role_constants", "pro_main", "gemini-2.5-pro")
```

### Phase 2 검증

```bash
python -m py_compile modules/core/constants.py
python -c "from modules.core.constants import AIModels; print(AIModels.STAGE4_FIXED_WRITER_MODEL, AIModels.FLASH_ANALYSIS_MODEL)"
# 출력 예: gemini-2.5-pro gemini-2.5-flash
```

---

## Phase 3: `modules/core/config_manager.py` — settings["models"] 동적 로드

### 3-A: `__init__()` 상단에 헬퍼 메서드 호출 추가

`self.settings = {...}` 블록을 찾아, `"models"` 딕셔너리를 동적 로드로 교체.

**현재:**
```python
self.settings = {
    "models": {
        "analyst": "gemini-2.5-pro",  # [V60.24] Gemini 3
        # [V65] architect 삭제 (레거시 에이전트 제거)
        "writer": "gemini-2.5-pro",  # 7,000자 고해상도 집필
        "director": "gemini-2.5-pro",  # [V60.24] Gemini 3
        "manager": "gemini-2.5-pro",  # [V60.24] Gemini 3
        "editor": "gemini-2.5-pro",  # [V60.24] Gemini 3
    },
    "limits": {
        ...
    },
}
```

**변경 후:**
```python
# [SSOT] models.yaml agents 섹션에서 동적 로드
_models_from_yaml = self._load_agents_from_yaml()

self.settings = {
    "models": _models_from_yaml if _models_from_yaml else {
        "analyst": "gemini-2.5-pro",
        "writer": "gemini-2.5-pro",
        "director": "gemini-2.5-pro",
        "manager": "gemini-2.5-pro",
        "editor": "gemini-2.5-pro",
    },
    "limits": {
        ...  # 기존 limits 블록 그대로 유지
    },
}
```

### 3-B: `ConfigManager` 클래스에 private 헬퍼 메서드 추가

`get_model_for_agent()` 메서드 바로 앞에 삽입:

```python
def _load_agents_from_yaml(self) -> dict | None:
    """[SSOT] config/models.yaml agents 섹션을 로드해 dict 반환. 실패 시 None."""
    try:
        from pathlib import Path
        import yaml

        _yaml_path = Path(__file__).parent.parent.parent / "config" / "models.yaml"
        if _yaml_path.exists():
            _data = yaml.safe_load(_yaml_path.read_text(encoding="utf-8"))
            _agents = (_data or {}).get("agents")
            if isinstance(_agents, dict) and _agents:
                return dict(_agents)
    except Exception:
        pass
    return None
```

### Phase 3 검증

```bash
python -m py_compile modules/core/config_manager.py
python -c "
from modules.core.config_manager import ConfigManager
cm = ConfigManager()
print('analyst:', cm.get_model_for_agent('analyst'))
print('chief_writer:', cm.get_model_for_agent('chief_writer'))
print('writer:', cm.get_model_for_agent('writer'))
"
# analyst: gemini-2.5-pro
# chief_writer: gemini-2.5-pro
# writer: gemini-2.5-flash
```

---

## Phase 4: `state_locked_arc_generator.py` — 하드코딩 문자열 → AIModels

`__init__` 내 L173~174 교체:

**현재:**
```python
self.extraction_model = "gemini-2.5-pro"  # 추출도 Gemini 3
self.draft_model = "gemini-2.5-pro"  # [V60.17] Speculative: 초안용 모델
```

**변경 후:**
```python
from modules.core.constants import AIModels  # 파일 상단 import에 이미 있으면 생략

self.extraction_model = AIModels.STAGE2_EXTRACTION_MODEL  # [SSOT]
self.draft_model = AIModels.STAGE2_MAIN_MODEL              # [SSOT]
```

**주의**: `from modules.core.constants import AIModels`가 파일 상단에 이미 있는지 확인. 없으면 상단에 추가.

---

## Phase 5: `narrative_structure_analyzer.py` / `self_reflection.py` / `tree_of_thoughts.py` — AIModels 교체

각 파일에서 `model: str = "gemini-2.5-pro"` 기본값을 AIModels로 교체.

### 5-A: `modules/core/narrative_structure_analyzer.py`

```python
# 현재 (L68):
def __init__(self, client, model: str = "gemini-2.5-pro"):

# 변경:
def __init__(self, client, model: str = AIModels.DEFAULT_ARCHITECT):
```

```python
# 현재 (L303):
def create_narrative_analyzer(client, model: str = "gemini-2.5-pro"):

# 변경:
def create_narrative_analyzer(client, model: str = AIModels.DEFAULT_ARCHITECT):
```

`from modules.core.constants import AIModels` import 필요 시 추가.

### 5-B: `modules/core/self_reflection.py`

```python
# 현재 (L155):
def __init__(self, api_client, model: str = "gemini-2.5-pro"):

# 변경:
def __init__(self, api_client, model: str = AIModels.DEFAULT_ARCHITECT):
```

`from modules.core.constants import AIModels` import 필요 시 추가.

### 5-C: `modules/core/tree_of_thoughts.py`

```python
# 현재 (L151):
def __init__(self, api_client, model: str = "gemini-2.5-pro"):

# 변경:
def __init__(self, api_client, model: str = AIModels.DEFAULT_ARCHITECT):
```

`from modules.core.constants import AIModels` import 필요 시 추가.

### Phase 5 검증

```bash
python -m py_compile modules/core/narrative_structure_analyzer.py
python -m py_compile modules/core/self_reflection.py
python -m py_compile modules/core/tree_of_thoughts.py
python -m py_compile modules/domain/agents/state_locked_arc_generator.py
```

---

## 최종 검증

```bash
# 1. 전체 py_compile
python -m py_compile modules/core/constants.py modules/core/config_manager.py modules/domain/agents/state_locked_arc_generator.py modules/core/narrative_structure_analyzer.py modules/core/self_reflection.py modules/core/tree_of_thoughts.py

# 2. SSOT 실제 값 확인
python -c "
from modules.core.constants import AIModels
print('STAGE4_FIXED_WRITER_MODEL:', AIModels.STAGE4_FIXED_WRITER_MODEL)
print('FLASH_ANALYSIS_MODEL:', AIModels.FLASH_ANALYSIS_MODEL)
print('STAGE2_EXTRACTION_MODEL:', AIModels.STAGE2_EXTRACTION_MODEL)
assert AIModels.STAGE4_FIXED_WRITER_MODEL == 'gemini-2.5-pro'
assert AIModels.FLASH_ANALYSIS_MODEL == 'gemini-2.5-flash'
print('AIModels SSOT 검증 통과')
"

# 3. ConfigManager 로드 확인
python -c "
from modules.core.config_manager import ConfigManager
cm = ConfigManager()
assert cm.get_model_for_agent('analyst') == 'gemini-2.5-pro'
assert cm.get_model_for_agent('chief_writer') == 'gemini-2.5-pro'
print('ConfigManager SSOT 검증 통과')
"

# 4. ruff
ruff check modules/core/constants.py modules/core/config_manager.py modules/domain/agents/state_locked_arc_generator.py modules/core/narrative_structure_analyzer.py modules/core/self_reflection.py modules/core/tree_of_thoughts.py

# 5. 전체 테스트
pytest tests/ -q
```

**주의사항 (test_config_manager.py)**:
`test_existing_api_model_lookup`이 `monkeypatch.chdir(tmp_path)`를 사용하지만,
`_load_agents_from_yaml()`은 `Path(__file__).parent` 기반 절대경로로 models.yaml을 찾으므로
**tmp_path chdir의 영향을 받지 않는다.** 따라서 `get_model_for_agent("writer")` 반환값이
기존 `"gemini-2.5-pro"` → `"gemini-2.5-flash"` (models.yaml 값)로 바뀔 수 있음.

**테스트 수정 대상 (1건)**:
```python
# tests/test_config_manager.py L152
# 현재:
assert cm.get_model_for_agent("writer") == "gemini-2.5-pro"
# 변경:
assert cm.get_model_for_agent("writer") == "gemini-2.5-flash"  # models.yaml 값
```

---

## 보고서 형식 (고정)

출력 파일: `C:/Users/wjjo/Desktop/글도비/docs/2026-03-04/model-ssot-implementation-result.md`

```markdown
# 모델 SSOT 구현 결과

> 구현일: 2026-03-04

## 수정 내역

| Phase | 파일 | 작업 | 완료 여부 |
|-------|------|------|---------|
| 1 | models.yaml | role_constants 섹션 추가 | ✅/❌ |
| 2 | constants.py | AIModels → yaml 동적 로드 | ✅/❌ |
| 3 | config_manager.py | settings["models"] → yaml 로드 | ✅/❌ |
| 4 | state_locked_arc_generator.py | 하드코딩 → AIModels | ✅/❌ |
| 5-A | narrative_structure_analyzer.py | 기본값 → AIModels | ✅/❌ |
| 5-B | self_reflection.py | 기본값 → AIModels | ✅/❌ |
| 5-C | tree_of_thoughts.py | 기본값 → AIModels | ✅/❌ |
| 테스트 | test_config_manager.py | writer 기댓값 수정 | ✅/❌ |

## 검증 결과

- py_compile: 통과/실패
- SSOT 값 확인: 통과/실패
- ruff: 위반 N건
- 전체 테스트: N passed, N failed

## 체크리스트

- [ ] models.yaml role_constants 3개 키 추가 완료
- [ ] AIModels 16개 attr 모두 yaml 참조
- [ ] ConfigManager yaml 로드 fallback 정상
- [ ] 모델 값 자체 변경 없음 (pro/flash 배정 동일)
- [ ] 전체 테스트 회귀 없음
```
