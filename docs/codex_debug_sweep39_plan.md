# Debug Sweep 39 — 얕은 복사 + 산술 잔여

## Context

Sweep 38 완료 (코덱스 실행 중). 5개 에이전트로 로직 역전, 얕은 복사, 불완전 에러 복구, 산술 경계, API 계약 불일치 탐색.
37회 스윕 후 발견 밀도 급감 — 수동 검증 후 **확인 4건** + 대량 오탐 기록.

---

## A-1 (MEDIUM): `preset_registry.py` — mutable default 직접 반환

**파일**: `modules/core/stage0/preset_registry.py:504, 506`

**문제**: `get_field_value()` 폴백 경로에서 `field_def.default`를 deepcopy 없이 반환:

```python
def get_field_value(self, field_name: str, raw_value: Any) -> Any:
    field_def = ...
    try:
        # ... 타입별 변환 ...
        elif field_def.type == "enum":
            if value in field_def.enum_values:
                return value
            return field_def.default  # L504 — 공유 객체 직접 반환
    except (ValueError, TypeError, KeyError, AttributeError):
        return field_def.default      # L506 — 공유 객체 직접 반환
```

- L504: enum 타입은 default가 string이므로 안전하지만, 코드 일관성 부족
- L506: dict/list 타입 필드에서 예외 발생 시 `{}` 또는 `[]` 공유 객체 직접 반환
  - COMMON_PRESET `"relationships"` default `{}`, `"secrets"` default `[]` 등이 해당
  - 호출자가 반환값을 변이하면 클래스 레벨 default가 오염됨
- 주요 경로(L563, L588)는 이미 `copy.deepcopy(field_def.default)` 사용 중 — 이 2곳만 누락

**수정**:
```python
        elif field_def.type == "enum":
            if value in field_def.enum_values:
                return value
            return copy.deepcopy(field_def.default)  # L504
    except (ValueError, TypeError, KeyError, AttributeError):
        return copy.deepcopy(field_def.default)      # L506
```

`import copy`는 파일 상단 L7에 이미 존재.

---

## A-2 (MEDIUM): `state_tracker.py` — `to_dict()` 얕은 병합

**파일**: `modules/domain/agents/state_tracker.py:67`

**문제**: `EpisodeState.to_dict()`에서 `extra_fields`를 shallow update로 병합:

```python
def to_dict(self) -> dict:
    base = {
        "ep_num": self.ep_num,
        "location": self.location,
        "weapons": self.weapons.copy(),
        "items": self.items.copy(),
        "injuries": self.injuries,
        "internal_energy": self.internal_energy,
        "relationships": self.relationships.copy(),
    }
    base.update(self.extra_fields)  # ← 얕은 병합: nested dict/list 공유
    return base
```

- `extra_fields`에 중첩 dict (예: `"stats": {"strength": 10}`)가 있으면 반환된 dict와 `self.extra_fields`가 내부 참조를 공유
- 호출자(`analyst.py:681`, `hud_utils.py:55`)가 변이 시 원본 `EpisodeState` 내부 상태 오염

**수정**:
```python
    base.update(copy.deepcopy(self.extra_fields))
    return base
```

파일 상단에 `import copy` 추가 필요. `from __future__ import annotations` 아래에 배치.

---

## B-1 (LOW): `feedback_system.py` — int() 절삭 나머지 손실

**파일**: `modules/core/feedback_system.py:95-97`

**문제**: `int()` 절삭으로 합산이 `shortage`보다 작아짐:

```python
dialogue_add = int(shortage * 0.35)
desc_add = int(shortage * 0.40)
action_add = int(shortage * 0.25)
```

- `shortage=1001`: `350 + 400 + 250 = 1000` (1자 손실)
- `shortage=999`: `349 + 399 + 249 = 997` (2자 손실)
- LLM에 제공되는 분량 가이드라인이 실제보다 적음

**수정**: 나머지를 가장 큰 항목에 할당:
```python
dialogue_add = int(shortage * 0.35)
desc_add = int(shortage * 0.40)
action_add = shortage - dialogue_add - desc_add  # 나머지 전부 할당
```

---

## B-2 (LOW): `semantic_plot_guard.py` — 무한 재시도 (문서와 불일치)

**파일**: `modules/core/semantic_plot_guard.py:76-87`

**문제**: 초기화 실패 시 `_init_done = True` 설정으로 매 `_embed_text()` 호출마다 재시도 발생:

```python
def _try_init_client(self) -> None:
    if self._client or not _GENAI_AVAILABLE or not self._api_key:
        return
    try:
        self._client = genai.Client(api_key=self._api_key)
        self._init_done = True        # 성공: True
    except Exception as e:
        self._client = None
        self._init_done = True         # L80: 실패에도 True → 매번 재시도 허용

def _embed_text(self, text: str) -> list | None:
    if not self._client and self._init_done:  # L85: True면 재시도
        self._init_done = False                # L86: False로 리셋
        self._try_init_client()                # L87: 재시도 → 실패 시 다시 True
```

- 영구 실패(잘못된 API 키)인 경우 매 embed 호출마다 불필요한 네트워크 요청
- 주석 "재시도 1회 허용"과 실제 동작(무한 재시도) 불일치

**수정**: 실패 시 `_init_done` 유지하되 재시도 카운터 도입:
```python
def __init__(self, api_key=None):
    # ... 기존 코드 ...
    self._retry_count = 0
    self._max_retries = 1

def _try_init_client(self) -> None:
    if self._client or not _GENAI_AVAILABLE or not self._api_key:
        return
    try:
        self._client = genai.Client(api_key=self._api_key)
        self._init_done = True
    except Exception as e:
        logging.warning(f"⚠️ [V63] SemanticPlotGuard 초기화 실패: {str(e)[:80]}")
        self._client = None
        self._retry_count += 1

def _embed_text(self, text: str) -> list | None:
    if not self._client and self._retry_count <= self._max_retries:
        self._try_init_client()
    # ... 나머지 동일
```

---

## 수정 파일 총괄

| # | 파일 | 변경 |
|---|------|------|
| A-1 | `modules/core/stage0/preset_registry.py` | L504, L506: `copy.deepcopy()` 래핑 |
| A-2 | `modules/domain/agents/state_tracker.py` | L67: `copy.deepcopy(self.extra_fields)` + import 추가 |
| B-1 | `modules/core/feedback_system.py` | L97: 나머지 역산 할당 |
| B-2 | `modules/core/semantic_plot_guard.py` | 재시도 카운터 도입 (3줄 변경) |

**총 4파일, ~15줄**

---

## 오탐 제거 기록

| 보고 | 실제 | 이유 |
|------|------|------|
| world_state.py `get_state_dict()` shallow copy | ✗ Sweep30에서 이미 검토 | 테스트 코드만 호출. 프로덕션 호출자 없음. nested 변이 없음 |
| db_manager.py `get_cumulative_bible()` 캐시 오염 | ✗ 오탐 | L526 `deepcopy()`로 캐시 보호됨. 예외 시 L586 미도달 → 캐시 무관 |
| preset_registry.py 클래스 레벨 mutable default | ✗ 대부분 보호됨 | L563, L588에서 `deepcopy()` 사용. L504/506만 누락 (A-1에 포함) |
| stage4_post_processor.py 부분 상태 갱신 | ✗ 설계 의도 | "비차단" 정책 — 부분 갱신이 전체 크래시보다 나음 |
| world_state.py 부분 dict 변이 | ✗ 설계 의도 | 동일 "비차단" 정책. 로깅 후 계속 진행 |
| audit_event 콜백 None 가드 미비 | ✗ 오탐 | `main_a.py:2333`에 항상 정의됨. `getattr(app, "_audit_event", None)` 항상 찾음 |
| save_manuscript 키워드 인수 스타일 | ✗ 스타일 차이 | Python은 positional=keyword 동일 처리. 기능적 차이 없음 |
| Python str slicing 한글 깨짐 (재확인) | ✗ 오탐 | Python 3 str은 Unicode. 바이트 분할 아님 |
| 에피소드/Arc 산술 오류 | ✗ 전량 정상 | `(ep-1)//5+1` 패턴 전체 검증 통과 |
| 로직 역전 (전량) | ✗ 1건 외 전량 정상 | 임계값 비교, if/else, and/or 모두 정상 |

---

## 검증

```bash
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q -x -p no:capture
```

---

## 소감

37회 스윕 이후 발견 밀도가 급격히 감소. CRITICAL 0건, MEDIUM 2건, LOW 2건.
코드베이스의 방어적 프로그래밍 수준이 높아져 추가 스윕의 ROI가 낮은 단계에 도달.

---

## Execution Update (2026-02-18)

Status: completed for Sweep 39 scope.

Applied items:
- A-1 `modules/core/stage0/preset_registry.py`: default return paths in `_enforce_type()` now use `copy.deepcopy(field_def.default)` for enum fallback and exception fallback.
- A-2 `modules/domain/agents/state_tracker.py`: `EpisodeState.to_dict()` now merges dynamic fields via `copy.deepcopy(self.extra_fields)` to avoid nested-reference aliasing.
- B-1 `modules/core/feedback_system.py`: shortage allocation now preserves total by assigning remainder to action bucket (`action_add = shortage - dialogue_add - desc_add`).
- B-2 `modules/core/semantic_plot_guard.py`: retry counter guard introduced (`_retry_count`, `_max_retries`) and init retry path changed to finite retries (no per-call infinite re-init loop).

Added tests:
- `tests/test_sweep39.py` (5 tests):
  - preset registry deepcopy fallback source guard
  - EpisodeState deep-copy behavior for nested extra fields
  - feedback shortage allocation sum consistency
  - semantic plot guard retry source guard
  - semantic plot guard finite retry runtime behavior

Verification run:
- `python -m py_compile modules/core/stage0/preset_registry.py modules/domain/agents/state_tracker.py modules/core/feedback_system.py modules/core/semantic_plot_guard.py tests/test_sweep39.py` -> pass
- `python -m pytest tests/test_sweep39.py -q -x -p no:capture` -> `5 passed`
- `python -m pytest tests/ -q -k "sweep39 or preset_registry or state_tracker or feedback_system or semantic_plot_guard" -x -p no:capture` -> `130 passed, 2025 deselected, 1 warning`
- `python -m pytest tests/ -q -x -p no:capture` -> `2098 passed, 68 xfailed, 1 warning`

Notes:
- Full-suite output still includes the existing mocked ImportError traceback print from test flow, but pytest exit code is 0 and suite status is green.
