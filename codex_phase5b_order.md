# Codex 오더: Phase 5-B Settings YAML + 모델 티어 중앙화

> **브랜치**: `devdev`
> **위험도**: SAFE (프롬프트/설정 전용, 로직 무변경)
> **전제**: 없음 (독립 작업)

---

## 현황 요약

| 항목 | 현재 상태 | 문제 |
|------|----------|------|
| **모델 티어** | 20+파일 `__init__`에 `gemini-*` 하드코딩 (70+건) | 모델 교체 시 전 파일 수정 필요 |
| **`settings.json`** | `config/settings.json` 존재, `main_a.py` L1433에서 로드 | 에이전트가 **안 읽고** 자기 기본값 사용 |
| **MODEL_FALLBACK_CHAIN** | `base_agent.py` L47~51에 하드코딩 | YAML로 이동 가능 |
| **장르 가드** | `genre_guards/*.py` 11개, FORBIDDEN_TERMS 등 하드코딩 | Phase 5-B 대상이나 이번 오더에서 제외 (별도 분리) |

---

## Task A: `config/models.yaml` 생성 + `BaseAgent`에서 읽기

### 목표
에이전트별 기본 모델 + 폴백 체인을 YAML로 뽑아내고, `BaseAgent.__init__`에서 읽게 한다.

### 생성할 파일

**`config/models.yaml`**:
```yaml
# 에이전트별 기본 모델 매핑
# 키 = 에이전트 클래스명(소문자_스네이크), 값 = 기본 모델
agents:
  chief_writer: "gemini-3-pro-preview"
  blueprint_ensemble: "gemini-3-pro-preview"
  three_phase_blueprint_generator: "gemini-3-pro-preview"
  state_locked_arc_generator: "gemini-3-pro-preview"
  block_enricher: "gemini-3-flash-preview"
  preflight_checker: "gemini-3-flash-preview"
  state_extractor: "gemini-3-flash-preview"
  four_phase_arc_generator: "gemini-2.5-pro"
  continuity_inspector: "gemini-2.5-pro"
  director: "gemini-2.5-pro"
  arc_corrector: "gemini-2.5-flash"
  consensus_validator: "gemini-2.5-flash"
  unified_arc_validator: "gemini-2.5-flash"
  unified_blueprint_validator: "gemini-2.5-flash"
  critic: "gemini-2.0-flash"
  weaver: "gemini-1.5-pro"
  writer: "gemini-1.5-pro"  # 레거시

# 폴백 체인 (Model A 실패 시 → Model B)
fallback_chain:
  "gemini-3-pro-preview": "gemini-2.5-pro"
  "gemini-3-flash-preview": "gemini-2.5-flash"
  "gemini-2.0-flash": "gemini-2.5-flash"

# 서브 컴포넌트 모델 (four_phase_arc_generator 내부 등)
sub_components:
  four_phase_arc_generator:
    preflight: "gemini-3-flash-preview"
    ensemble: "gemini-2.5-pro"
    validator: "gemini-2.5-flash"
  three_phase_blueprint_generator:
    ensemble: "gemini-3-pro-preview"
    validator: "gemini-2.5-flash"
```

### 수정할 파일

#### `modules/domain/agents/base_agent.py`

1. **`__init__` 메서드** (L129 부근):
   - `model_tier` 파라미터 기본값을 `None`으로 변경
   - `model_tier`가 `None`일 때 → `config/models.yaml`에서 클래스명 기반 조회
   - `model_tier`가 명시적일 때 → 기존대로 사용 (호환성 유지)
   - 조회 실패 시 → 기존 기본값 `"gemini-2.5-flash"` 폴백

2. **`MODEL_FALLBACK_CHAIN`** (L47~51):
   - YAML의 `fallback_chain`에서 로드
   - YAML 로드 실패 시 기존 딕셔너리 유지 (fail-safe)

3. **로더 함수 추가** (클래스 변수/모듈 레벨):
```python
import yaml

def _load_model_config() -> dict:
    """config/models.yaml 로드. 실패 시 빈 dict 반환."""
    try:
        config_path = Path(__file__).parent.parent.parent / "config" / "models.yaml"
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    except Exception:
        logging.warning("⚠️ models.yaml 로드 실패, 하드코딩 폴백 사용")
    return {}
```

### ⚠️ 안전 규칙
- **기존 동작 100% 호환**: `model_tier`를 명시적으로 넘기는 호출은 전혀 변경 없음
- YAML 로드 실패 → 기존 하드코딩 폴백 (절대 크래시 안 함)
- 이 Task에서는 각 에이전트 `__init__`의 기본값을 **변경하지 않음** (Task B에서 처리)

---

## Task B: 에이전트 `__init__` 기본값 → `None` 전환

### 목표
20+개 에이전트의 `model_tier=` 기본값을 `None`으로 바꿔서 `BaseAgent`에서 YAML 조회하게 한다.

### 대상 파일 (변경 패턴 동일)

변경 전:
```python
def __init__(self, context, client, model_tier: str = "gemini-2.5-flash"):
```

변경 후:
```python
def __init__(self, context, client, model_tier: str = None):
```

대상 목록:
| 파일 | 현재 기본값 |
|------|-----------|
| `arc_corrector.py` L89 | `gemini-2.5-flash` |
| `block_enricher.py` L203 | `gemini-3-flash-preview` |
| `blueprint_ensemble.py` L103 | `gemini-3-pro-preview` |
| `chief_writer.py` L107 | `gemini-3-pro-preview` |
| `consensus_validator.py` L155 | `gemini-2.5-flash` |
| `continuity_inspector.py` L65 | `gemini-2.5-pro` |
| `critic.py` L33 | `gemini-2.0-flash` |
| `four_phase_arc_generator.py` L40 | `gemini-2.5-pro` |
| `preflight_checker.py` L120 | `gemini-3-flash-preview` |
| `state_extractor.py` L148 | `gemini-3-flash-preview` |
| `state_locked_arc_generator.py` L169 | `gemini-3-pro-preview` |
| `three_phase_blueprint_generator.py` L37 | `gemini-3-pro-preview` |
| `unified_arc_validator.py` L105 | `gemini-2.5-flash` |
| `unified_blueprint_validator.py` L41 | `gemini-2.5-flash` |
| `weaver.py` L15 | `gemini-1.5-pro` |

### ⚠️ 제외 (건드리지 마)
- `writer.py` — 레거시, Phase 2에서 삭제 예정
- `create_*()` 팩토리 함수들 — 호출부가 명시적 모델 전달하므로 변경 불필요
- `four_phase_arc_generator.py` 내부 서브 컴포넌트 (`self.preflight`, `self.ensemble`, `self.validator`) — `sub_components` YAML에서 읽도록 별도 처리

### 안전 규칙
- `create_*()` 팩토리 함수의 기본값은 **유지** (명시적 호출부이므로)
- 서브 컴포넌트 모델은 `__init__`에서 `models.yaml`의 `sub_components` 섹션 참조

---

## Task C: `settings.json` → `models.yaml` 통합

### 목표
기존 `config/settings.json`의 `models` 섹션과 `models.yaml`이 중복이므로 정리.

### 작업
1. `settings.json`에서 `models` 키 제거 (이제 `models.yaml`이 담당)
2. `main_a.py` L1433 부근 — `settings.json`에서 모델 읽던 코드 → `models.yaml` 사용하도록 변경
3. `settings.json`에는 `costs`, `validation` 설정만 남김

---

## 검증 계획

### 자동 검증
```bash
# 1. 구문 검증
python -m compileall modules/ -q

# 2. YAML 파싱 검증
python -c "import yaml; yaml.safe_load(open('config/models.yaml', encoding='utf-8')); print('OK')"

# 3. 기존 테스트 통과
pytest tests/ -x -q --tb=short

# 4. BaseAgent 모델 로드 확인
python -c "
from modules.domain.agents.base_agent import BaseAgent, _load_model_config
cfg = _load_model_config()
print(f'agents: {len(cfg.get(\"agents\", {}))} 개')
print(f'fallback: {cfg.get(\"fallback_chain\", {})}')
assert len(cfg.get('agents', {})) >= 15, 'agents 매핑 누락'
print('✅ models.yaml 로드 성공')
"
```

### 중요 확인 사항
- `pytest tests/test_base_agent.py` — BaseAgent 관련 테스트 통과
- `pytest tests/test_genre_guard.py` — 가드 테스트 통과 (이번에 안 건드리지만 확인)
- 기존 `model_tier`를 명시적으로 넘기는 호출부가 정상 작동하는지 확인

---

## 실행 순서

```
Task A → Task B → Task C (순서 엄수)
```

- Task A만 완료해도 기존 동작은 100% 유지됨 (YAML 안 읽혀도 폴백)
- Task B는 Task A의 `_load_model_config()` 의존
- Task C는 Task A+B 검증 후 정리 작업
