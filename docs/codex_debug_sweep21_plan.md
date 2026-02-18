# Debug Sweep 21 — 캐시 미저장 + 에러 핸들러 크래시 + 로깅 레벨

## Context

Sweep 20(6건) 완료 후, 5-에이전트 병렬 탐색으로 미탐색 핵심 모듈 전면 스윕:
prompt_builder, director_continuity/director_prompts/director, advisory 모듈 4종, stage0 모듈 5종, manager/analyst/preset_registry.
수동 코드 검증으로 **확인된 실제 버그 5건** 정리.

---

## A-1 (HIGH): `director_continuity.py:700` _manuscript_cache_name 미저장 → 캐시 재사용 전면 무력화

**파일**: `modules/domain/agents/director_continuity.py:698-706`

**문제**:
```python
# L698-700 — 캐시 생성
cache_result = self._d._get_or_create_context_cache(
    cache_type="manuscript", content=context_text, ttl_seconds=1800, project_name=project_name
)
self._cached_manuscript_ep = ep_num                    # ✅ 저장
self._cached_context_text_manuscript = context_text    # ✅ 저장
# ❌ self._manuscript_cache_name 미저장!

# L704-706 — 캐시 재사용 시도
else:
    context_text = getattr(self, "_cached_context_text_manuscript", "")
    cache_result = {"cached": True, "cache_name": getattr(self, "_manuscript_cache_name", None)}
    # ↑ _manuscript_cache_name이 설정된 적 없으므로 항상 None
```
- `_get_or_create_context_cache()`가 반환하는 `cache_name`을 인스턴스에 저장하지 않음
- 캐시 재사용 경로(L706)에서 `getattr(self, "_manuscript_cache_name", None)` → 항상 None
- 결과: L716 `cache_result.get("cache_name")` 항상 None → 캐시 미활용, 매번 전체 컨텍스트 전송
- LLM Context Caching 비용 절감 효과 완전 소실

**수정** — L702 뒤에 추가:
```python
self._cached_manuscript_ep = ep_num
self._cached_context_text_manuscript = context_text
self._manuscript_cache_name = cache_result.get("cache_name")  # ← 추가
```

**테스트**: `_get_or_create_context_cache` mock이 `{"cache_name": "test_cache"}` 반환 시, 두 번째 호출에서 `cache_result["cache_name"]`이 `"test_cache"`인지 검증

---

## A-2 (MEDIUM): `prompt_builder.py:541-545` 에러 핸들러에서 self._app 미검증 → 이중 크래시

**파일**: `modules/core/prompt_builder.py:541-545`

**문제**:
```python
# __init__: def __init__(self, app=None)  ← app이 None일 수 있음

except Exception as se_err:
    self._app._audit_event(         # ← self._app=None → AttributeError
        "v60_10_state_extractor_error", ...
    )
    self._app.ui.log(...)           # ← 동일 크래시
```
- `PromptBuilder(app=None)` 가능 (L36: `app=None` 기본값)
- try 블록의 원본 에러가 발생하면 except 핸들러에서 이중 크래시
- 원본 에러 메시지 소실 + 디버깅 불가

**수정**:
```python
except Exception as se_err:
    if self._app:
        self._app._audit_event(
            "v60_10_state_extractor_error", "StateExtractor failed, using fallback", {"error": str(se_err)[:100]}
        )
        self._app.ui.log(f"      ⚠️ [V60.10] StateExtractor 실패, Python 폴백 사용: {str(se_err)[:50]}")
    else:
        logging.warning(f"[V60.10] StateExtractor 실패 (app=None), 폴백 사용: {se_err}")
```

**테스트**: `PromptBuilder(app=None)`에서 `generate_arc_context_v60()` 호출 시 예외 발생해도 크래시 없이 폴백 반환 검증

---

## A-3 (MEDIUM): `prompt_builder.py:824-825` 동일 패턴 — 에러 핸들러 이중 크래시

**파일**: `modules/core/prompt_builder.py:824-825`

**문제**:
```python
except Exception as e:
    self._app.ui.log(f"⚠️ 아이템 타임라인 생성 실패 (비차단): {e}")  # ← self._app=None 시 크래시
    return ""
```
- A-2와 동일 패턴: `self._app`가 None이면 에러 핸들러 자체가 크래시

**수정**:
```python
except Exception as e:
    if self._app:
        self._app.ui.log(f"⚠️ 아이템 타임라인 생성 실패 (비차단): {e}")
    else:
        logging.warning(f"아이템 타임라인 생성 실패: {e}")
    return ""
```

**테스트**: A-2 테스트에 통합 가능

---

## B-1 (MEDIUM): `director_continuity.py:127` 불일치 검출 로깅 INFO → WARNING

**파일**: `modules/domain/agents/director_continuity.py:127`

**문제**:
```python
if mismatches:
    decision = result.get("decision", "WARNING")
    logging.info(f"⚠️ [V61] Entity 일관성 검증: {decision} ({len(mismatches)}개 불일치)")  # ← INFO
```
- Entity 불일치가 감지된 상황 (⚠️ 이모지까지 사용)인데 `logging.info` 사용
- 같은 파일 L136의 에러 핸들러는 올바르게 `logging.warning` 사용
- 운영 모니터링에서 불일치 경고가 INFO 레벨에 묻힘

**수정**:
```python
logging.warning(f"⚠️ [V61] Entity 일관성 검증: {decision} ({len(mismatches)}개 불일치)")
```

**테스트**: mismatches 존재 시 WARNING 레벨 로그 출력 검증

---

## B-2 (LOW): `stage4_post_processor.py:444` get_protagonist_name() None 반환 → 변수에 None 전파

**파일**: `modules/core/stage4_post_processor.py:444`

**문제**:
```python
_prot_name = self.ctx.get_protagonist_name() if self.ctx.get_protagonist_name else ""
```
- 조건문은 콜백 **존재 여부**만 확인 (함수 객체의 truthiness)
- 콜백이 존재하지만 None을 반환하면 `_prot_name = None`
- 이후 `if _prot_name and _prot_name in ...` 사용 → None은 falsy이므로 크래시 없지만 의도와 불일치

**수정**:
```python
_prot_name = (self.ctx.get_protagonist_name() or "") if self.ctx.get_protagonist_name else ""
```

**테스트**: `get_protagonist_name`이 None 반환 시 `_prot_name`이 `""` 인지 검증

---

## 수정 파일 총괄

| # | 파일 | 변경량 |
|---|------|--------|
| A-1 | `modules/domain/agents/director_continuity.py` | 1줄 추가 (cache_name 저장) |
| A-2 | `modules/core/prompt_builder.py` | 5줄 수정 (if self._app guard) |
| A-3 | `modules/core/prompt_builder.py` | 3줄 수정 (if self._app guard) |
| B-1 | `modules/domain/agents/director_continuity.py` | 1줄 수정 (info→warning) |
| B-2 | `modules/core/stage4_post_processor.py` | 1줄 수정 (or "" 추가) |

**총 ~11줄 변경**

---

## 오탐 제거 기록

| 보고 | 실제 | 이유 |
|------|------|------|
| `prompt_builder.py:554-565` 변수 섀도잉 | ✗ 오탐 | L565 `state_constraints → arc_end_state` 추출은 L555 이후, 변수 재정의지만 이전 값 미사용 |
| `writer_prompt_builders.py:69` 대소문자 불일치 | ✗ 오탐 | 한글 문자열은 대소문자 구분 없음 |
| `quality_dashboard.py:921` isinstance(int\|float) | ✗ 오탐 | Python 3.10+ PEP 604 유효 문법 |
| `information_diffusion.py:52` off-by-one | ✗ 오탐 | `get_latest_episode_number()`가 MAX+1 반환 → `range(1, latest_ep)` 정확 |
| `reverse_expander.py:441-442` 에피소드 인덱싱 | ✗ 설계 | `ep_num - 1` 인덱싱 + bounds check 존재. 역설계 시 에피소드 순차적 |
| `reverse_expander.py:789-795` 위치 기반 인덱싱 | ✗ 설계 | `enumerate(raw_drafts)` 기반, episode_bibles와 1:1 대응. bounds check 존재 |
| `manager.py:133` 반전된 폴백 로직 | ✗ 오탐 | `current_state.get("actual_truth", current_state)` = 하위 키 우선, 없으면 전체 dict. 의도된 설계 |
| `analyst.py:825-828` beat sequence off-by-one | ✗ 오탐 | `beats[:n-1] + [combined(beats[n-1:])]` = n개. 최종 개수 정확 |
| `analyst.py:343` valid 플래그 부상 무시 | ✗ 설계 | `valid`는 아이템 CRITICAL 이슈만 반영, 부상은 advisory (soft check) |
| `stage0/__init__.py:257` None vs StyleGuide 반환 | ✗ 설계 | 정상 경로(L242)도 None 반환, 모든 호출자 None 처리 |
| `preset_registry.py:644-650` activate_preset 반환값 무시 | ✗ 오탐 | activate_preset은 in-place 수정 (active_presets set), 반환값 무관 |
| `preset_registry.py:480-507` silent exception | ✗ 정책 준수 | V64.P4 OPTIONAL 정책: 타입 강제 실패 시 default 반환 |
| `preset_registry.py:525-532` falsy-zero 한글 숫자 | ✗ 오탐 | `current==0 → 1` 처리는 "억" (1억) 의미. "0억" 입력은 실전 불가 |
| `story_expander.py:161` title_suggestions 타입 | ✗ 오탐 | `or ["무제"]` + `[0]` = 빈 리스트/None 방어 완비. LLM JSON 파싱이 list 보장 |
| `analyst.py:906-918` dead code stub 호출 | ✗ 기존 | Sweep 16 B-3에서 이미 기록됨 |

---

## 검증

```bash
PYTHONIOENCODING=utf-8 python -m pytest tests/test_prompt_builder.py tests/test_director.py tests/test_stage4_post_processor.py -q -x
PYTHONIOENCODING=utf-8 python -m pytest tests/ -q -p no:capture
```

---

## Execution Status (2026-02-18)

- 완료: A-1 `modules/domain/agents/director_continuity.py`
  - manuscript cache 생성 시 `self._manuscript_cache_name = cache_result.get("cache_name")` 저장 추가
- 완료: A-2 `modules/core/prompt_builder.py`
  - `generate_arc_context_v60()` 예외 경로에서 `self._app` 존재 여부 가드 추가
- 완료: A-3 `modules/core/prompt_builder.py`
  - `build_item_acquisition_timeline()` 예외 경로에서 `self._app` 존재 여부 가드 추가
- 완료: B-1 `modules/domain/agents/director_continuity.py`
  - Entity mismatch 로그를 `info` -> `warning`으로 조정
- 완료: B-2 `modules/core/stage4_post_processor.py`
  - `_prot_name` 계산식에 `or ""` 추가하여 `None` 전파 차단

### Tests Added/Updated

- 수정: `tests/test_prompt_builder.py`
  - `app=None`에서 `generate_arc_context_v60()` 폴백 동작 검증
  - `app=None`에서 `build_item_acquisition_timeline()` 예외 없이 `""` 반환 검증
- 수정: `tests/test_director_modules.py`
  - manuscript continuity 캐시 재사용 시 `cache_name` 유지/재사용 경로 검증
  - Entity mismatch 로그가 warning 레벨로 기록되는지 검증
- 수정: `tests/test_stage4_post_processor.py`
  - `get_protagonist_name()`이 `None`을 반환해도 overexposure detector에 `""` 전달되는지 검증

### Pytest Results

1. 타겟 실행 (계획서 기준 변형)
   - 계획서 명령의 `tests/test_director.py`는 저장소에 없어 `tests/test_director_modules.py`로 대체 실행
   - `python -m pytest tests/test_prompt_builder.py tests/test_director_modules.py tests/test_stage4_post_processor.py -q -x`
   - 결과: `127 passed`
2. 전체 실행
   - `python -m pytest tests/ -q -p no:capture`
   - 결과: `2 failed, 1972 passed, 68 xfailed, 1 warning`
   - 실패 테스트:
     - `tests/test_stage2_pipeline.py::TestAnalystProtagonistConfig::test_world_origin_primitive`
     - `tests/test_stage2_pipeline.py::TestAnalystProtagonistConfig::test_incarnation_type_regression`
