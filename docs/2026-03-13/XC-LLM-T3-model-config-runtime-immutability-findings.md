# XC-LLM-T3: 모델 설정 런타임 불변성 — Findings

> 작성일: 2026-03-13
> 감사 범위: `constants.py`, `base_agent.py`, `llm_router.py`, `config/models.yaml`

---

## 실행 요약

모델 설정은 3개의 독립적 경로에서 `config/models.yaml`을 읽는다:

1. **`constants.py` AIModels**: import-time에 `_load_model_from_yaml()`로 읽어 클래스 변수에 고정. 프로세스 수명 동안 불변.
2. **`base_agent.py` `_load_model_config()`**: 에이전트 인스턴스 생성마다 YAML 파일을 다시 읽음.
3. **`llm_router.py` `_load_provider_configs()`**: Router 인스턴스 생성 시 1회 읽음. 싱글톤이므로 프로세스 수명 동안 1회.

이로 인해 **런타임 YAML 변경 시 경로별 불일치** 가능성이 존재한다.

---

## PASS 1: 후보 수집

### [XC-LLM-010] P3 | AIModels import-time 캐싱으로 YAML 변경 미반영

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-010 |
| Severity | P3 (코드 스멜) |
| 현상 요약 | `constants.py` AIModels 클래스의 모든 상수가 import-time에 `_load_model_from_yaml()`으로 고정되어, 프로세스 실행 중 `models.yaml` 변경 시 반영 불가. |
| 코드 근거 | `modules/core/constants.py:266-298` — 15개 모델 상수가 모두 `_load_model_from_yaml(section, key, fallback)` 호출 |
| 영향 경계 | 모든 스테이지 (AIModels 상수가 모델 선택에 사용) |
| 테스트 근거 | import-time 캐싱 동작 테스트 부재 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 의도된 설계. CLAUDE.md에 "[SSOT] config/models.yaml 단일 참조. constants.py _load_model_from_yaml() import-time 로드"로 명시. 런타임 변경은 **지원하지 않는 기능**이므로 P3 유지. |

```python
# constants.py:266-298
class AIModels:
    V50_MODULE_MODEL = _load_model_from_yaml("role_constants", "flash_main", "gemini-2.5-flash")
    FLASH_ANALYSIS_MODEL = _load_model_from_yaml("role_constants", "flash_main", "gemini-2.5-flash")
    # ... 15개 상수 모두 import-time 고정
```

**신뢰도**: HIGH. **영향도**: LOW (의도된 설계).

---

### [XC-LLM-011] P3 | base_agent.py _load_model_config() 매 호출 YAML I/O

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-011 |
| Severity | P3 (코드 스멜) |
| 현상 요약 | `_load_model_config()`이 에이전트 인스턴스 생성마다 `models.yaml`을 파일 시스템에서 읽는다. 캐싱 없음. |
| 코드 근거 | `modules/domain/agents/base_agent.py:85-96` (`_load_model_config()`), 호출자: `_get_agent_default_model()` (L104), `_get_sub_component_models()` (L115), `_get_model_fallback_chain()` (L126) |
| 영향 경계 | 에이전트 초기화 성능 (Stage4에서 ~10개 에이전트 생성 시 ~10회 YAML 읽기) |
| 테스트 근거 | 캐싱 테스트 부재 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 모듈-레벨 캐시 추가 (`_MODEL_CONFIG_CACHE = None` + lazy load). 공수: 0.5h. 현재 성능 영향 미미 (YAML 파일 65줄, 디스크 캐시 적중). |

```python
# base_agent.py:85-96 — 캐싱 없이 매번 파일 I/O
def _load_model_config() -> dict:
    config_path = _resolve_models_config_path()
    try:
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                if isinstance(data, dict):
                    return data
    except (OSError, yaml.YAMLError):
        ...
    return {}
```

**참고**: `_get_agent_default_model(agent_key)` → `_load_model_config()` 체인이 `BaseAgent.__init__` (L290-291)에서 호출된다:
```python
# base_agent.py:290-291
agent_key = _to_snake_case(self.__class__.__name__)
resolved_model = _get_agent_default_model(agent_key)  # ← _load_model_config() 호출
```

에이전트가 생성될 때마다 YAML을 다시 읽는다. Stage4에서 에이전트 10개 이상 생성 시 10+회 반복되나, 65줄 YAML 파일의 I/O 비용은 무시할 수 있는 수준.

**신뢰도**: HIGH. **영향도**: LOW (성능 미미).

---

### [XC-LLM-012] P3 | AIModels(import-time)와 _load_model_config()(런타임) 간 잠재적 불일치

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-012 |
| Severity | P3 (코드 스멜) |
| 현상 요약 | `AIModels.STAGE4_FIXED_WRITER_MODEL`은 import-time에 고정되고, `BaseAgent.__init__`의 `_get_agent_default_model()`은 런타임에 YAML을 다시 읽는다. 프로세스 실행 중 YAML이 변경되면 두 경로의 모델명이 불일치할 수 있다. |
| 코드 근거 | `constants.py:295` (import-time) vs `base_agent.py:290-292` (런타임) |
| 영향 경계 | 이론적으로 모든 스테이지, 실질적으로는 발생하지 않음 |
| 테스트 근거 | 일관성 검증 테스트 부재 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 두 경로를 하나로 통일. 방안 1: `_load_model_config()`에 모듈-레벨 캐시 추가하여 import-time 1회만 로드. 방안 2: AIModels를 폐지하고 `_get_agent_default_model()`만 사용. 공수: 2h. |

**이론적 시나리오**:
1. 프로세스 시작: `AIModels.STAGE4_FIXED_WRITER_MODEL = "gemini-2.5-pro"` (import-time 고정)
2. 사용자가 `config/models.yaml`의 `agents.chief_writer`를 `"gemini-2.5-flash"`로 변경
3. Stage4에서 `ChiefWriter.__init__` → `_get_agent_default_model("chief_writer")` → `"gemini-2.5-flash"` (런타임 읽기)
4. 다른 코드에서 `AIModels.STAGE4_FIXED_WRITER_MODEL` → `"gemini-2.5-pro"` (import-time 값)
5. 동일 에이전트에 대해 두 가지 모델명이 공존

**실질 영향**: 운영 중 YAML 변경은 예상되지 않는 사용 패턴. 프로세스 재시작으로 해결 가능. P3 유지.

**신뢰도**: MED. **영향도**: LOW.

---

### [XC-LLM-013] P3 | _SHARED_ROUTER force_reload 사용 시 진행 중인 요청과의 경합

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-013 |
| Severity | P3 (코드 스멜) |
| 현상 요약 | `get_shared_llm_router(force_reload=True)` 호출 시 기존 router가 대체되지만, 이미 기존 router를 참조하고 있는 BaseAgent 인스턴스는 구 router를 계속 사용한다. |
| 코드 근거 | `llm_router.py:134-138`, `base_agent.py:287` (`self._llm_router = get_shared_llm_router()`) |
| 영향 경계 | `force_reload=True` 호출 경로 (현재 코드에서 호출자 없음) |
| 테스트 근거 | force_reload 테스트 부재 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | `force_reload=True` 호출자가 없으므로 현재 무해. 향후 사용 시 BaseAgent가 router를 인스턴스 변수로 캐시하는 점 주의. 공수: 0h (현재). |

```python
# base_agent.py:287 — 인스턴스 변수로 캐시
self._llm_router = get_shared_llm_router()  # ← 생성 시점의 router 고정

# force_reload 후에도 이미 생성된 에이전트는 구 router 참조
```

**신뢰도**: HIGH. **영향도**: NONE (호출자 없음).

---

### [XC-LLM-014] P3 | _load_model_from_yaml 실패 시 silent fallback (로깅 없음)

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-014 |
| Severity | P3 (코드 스멜) |
| 현상 요약 | `_load_model_from_yaml()`이 `except Exception: pass`로 모든 예외를 무시하고 fallback을 반환한다. YAML 파싱 오류, 파일 권한 문제 등이 silent하게 처리됨. |
| 코드 근거 | `modules/core/constants.py:22-23` |
| 영향 경계 | 모델 설정 디버깅 |
| 테스트 근거 | YAML 로드 실패 시 fallback 반환 테스트 부재 |
| 기존 중복 여부 | T1-18 (llm_router.py YAML silent pass)와 동일 패턴이나 다른 파일 |
| 권장 후속 조치 | `logging.debug()` 추가. 공수: 0.25h. |

```python
# constants.py:22-23
except Exception:
    pass  # ← 모든 예외 무시, 로깅 없음
```

**신뢰도**: HIGH. **영향도**: LOW.

---

## PASS 2: 교차 검증

| ID | PASS 1 판정 | 런타임 도달? | 기존 중복? | PASS 2 판정 |
|----|-------------|------------|----------|------------|
| XC-LLM-010 | P3 | 예 (import-time) | 신규 | P3 유지 (의도된 설계) |
| XC-LLM-011 | P3 | 예 (에이전트 생성마다) | 신규 | P3 유지 |
| XC-LLM-012 | P3 | 이론적 (YAML 런타임 변경 시) | 신규 | P3 유지 |
| XC-LLM-013 | P3 | 아니오 (호출자 없음) | 신규 | P3 유지 |
| XC-LLM-014 | P3 | 예 (YAML 오류 시) | T1-18 유사 패턴 | P3 유지 |

---

## PASS 3: 최종 확정

모든 finding이 P3 등급. 모델 설정 시스템은 **의도된 단순성**으로 설계되어 있으며, 런타임 변경을 지원하지 않는 것은 합리적 결정이다.

### 확정: XC-LLM-010 (P3)
- import-time 캐싱은 의도적. 런타임 재로드가 필요한 운영 시나리오 없음.

### 확정: XC-LLM-011 (P3)
- 매 호출 YAML I/O는 비효율적이나 성능 영향 무시할 수준.

### 확정: XC-LLM-012 (P3)
- 이론적 불일치. 운영 중 YAML 변경은 예상 외 시나리오.

### 확정: XC-LLM-013 (P3)
- force_reload 호출자 없어 미도달.

### 확정: XC-LLM-014 (P3)
- silent pass 패턴. 디버깅 편의 개선.

---

## T3 최종 결론

| 등급 | 건수 | 비고 |
|------|------|------|
| P0 | 0 | - |
| P1 | 0 | - |
| P2 | 0 | - |
| P3 | 5 | XC-LLM-010~014 (모두 설계적 기술 부채, 현재 무해) |

**핵심 판단**: 모델 설정 시스템은 "import-time 1회 로드 + 프로세스 재시작으로 갱신"이라는 단순한 계약을 따른다. 이 계약은 현재 운영 패턴 (CLI 기반, 프로젝트당 1회 실행)에 적합하다. `base_agent.py`의 매 호출 YAML I/O는 모듈-레벨 캐시로 개선할 수 있으나 우선순위 낮음.
