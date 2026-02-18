# Debug Sweep 35 — 롤백 캐시 미무효화 + 네트워크 재시도 한계 + 재귀 깊이

## Context

Sweep 34 완료 (2,074 passed, 68 xfailed). 5개 탐색 에이전트 중 4개 완료 — 롤백 후 캐시 불일치(2건), 네트워크 재시도 설계 결함(1건), 재귀 깊이 무제한(1건) 발견. 인코딩 처리는 완벽(0건).

---

## A-1 (MEDIUM): `_rollback_episode` — Director 원고 캐시 미무효화

**파일**: `main_a.py:2663-2679`

**문제**: `_rollback_episode()`이 4개 캐시를 무효화하지만 Director의 Gemini API 원고 캐시를 빠뜨림:

```python
def _rollback_episode(self):
    self._project_service.rollback_episode()
    self._prompt_builder._item_timeline_cache = {}       # ✓
    self._cumulative_state_cache = None                   # ✓
    self._cumulative_state_cache_key = 0                  # ✓
    self._narrative_summaries_cache = None                # ✓
    # writer cache                                        # ✓
    # ← Director manuscript_cache_name 누락!
    # ← Director _cached_manuscript_count 누락!
    # ← Director _continuity._cached_manuscript_ep 누락!
```

`director_caching.py:123`에서 `_cached_manuscript_count == len(manuscripts_compiled)` 카운트 비교만 수행 → 롤백 후 에피소드 수 동일하면 **변경된 내용의 구 캐시** 재사용 → Director가 옛 원고 기반으로 모순 검사 수행

**수정**: L2679 뒤에 Director 캐시 무효화 추가:
```python
        # [Sweep35] Director 원고 캐시 무효화
        try:
            _director = self.agents.get("director") if isinstance(self.agents, dict) else None
            if _director and hasattr(_director, "_caching"):
                _director._caching.manuscript_cache_name = None
                _director._caching._cached_manuscript_count = 0
            if _director and hasattr(_director, "_continuity"):
                _director._continuity._cached_manuscript_ep = None
                _director._continuity._cached_blueprint_ep = None
        except Exception as _dc_err:
            logging.warning(f"[Sweep35] Director cache invalidation failed (non-blocking): {_dc_err}")
```

---

## A-2 (MEDIUM): `rewind_stage_2` — 캐시 무효화 전무

**파일**: `main_a.py:2660-2661` + `modules/core/services/project_service.py:55-83`

**문제**: `_rewind_stage_2()`는 아크 삭제만 하고 캐시를 전혀 무효화하지 않음:

```python
def _rewind_stage_2(self):
    self._project_service.rewind_stage_2()  # 아크 삭제
    # ← 캐시 무효화 0건!
```

`_rollback_episode()`는 5개 캐시를 무효화하는 것과 대조적. 특히 `StateExtractor._state_cache`가 삭제된 아크 번호의 구 데이터를 보유 → 같은 번호로 새 아크 생성 시 구 상태 반환.

**수정**: `main_a.py` L2661 뒤에 캐시 무효화 추가:
```python
    def _rewind_stage_2(self):
        self._project_service.rewind_stage_2()
        # [Sweep35] Stage 2 되감기 후 캐시 무효화
        self._cumulative_state_cache = None
        self._cumulative_state_cache_key = 0
        self._prompt_builder._item_timeline_cache = {}
        self._narrative_summaries_cache = None
        try:
            _se = self.agents.get("state_extractor") if isinstance(self.agents, dict) else None
            if _se and hasattr(_se, "invalidate_cache"):
                _se.invalidate_cache()  # 전체 클리어
        except Exception as _se_err:
            logging.warning(f"[Sweep35] StateExtractor cache clear failed (non-blocking): {_se_err}")
```

---

## A-3 (MEDIUM): `base_agent.py` — MAX_NETWORK_RETRIES=22 도달 불가

**파일**: `modules/domain/agents/base_agent.py:329-391`

**문제**: 네트워크 재시도 로직이 `for attempt in range(MAX_CONTINUATIONS=5)` 안에서 `continue`로 구현 → 각 재시도가 외부 루프 반복 소비:

```python
MAX_CONTINUATIONS = 5           # 외부 루프 5회
MAX_NETWORK_RETRIES = 22        # 네트워크 재시도 22회 (의도)

for attempt in range(MAX_CONTINUATIONS):    # 실제 최대 5회
    try:
        response = self.client.models.generate_content(...)
    except Exception as api_error:
        if self._is_network_error(api_error) and network_retry_count < self.MAX_NETWORK_RETRIES:
            network_retry_count += 1
            continue  # ← range(5) 반복 소비!
```

- 의도: 22회 재시도 × 10~30초 백오프 = 약 5~10분 장애 대응
- 실제: 5회 재시도 × 10~30초 = 약 75~150초만 대응
- **결과**: 야간 무인 운영 시 3분 이상 네트워크 장애에서 불필요한 작업 중단

**수정**: 네트워크 재시도를 내부 while 루프로 분리:
```python
for attempt in range(MAX_CONTINUATIONS):
    try:
        # 네트워크 재시도 내부 루프
        while True:
            try:
                time.sleep(self.API_DELAY)
                response = self.client.models.generate_content(
                    model=current_model, contents=current_prompt, config=config
                )
                rate_limit_retry_count = 0
                network_retry_count = 0
                break  # 성공 → 내부 루프 탈출
            except Exception as api_error:
                if self._is_network_error(api_error) and network_retry_count < self.MAX_NETWORK_RETRIES:
                    network_retry_count += 1
                    wait_time = min(
                        self.NETWORK_RETRY_DELAY_BASE + (network_retry_count - 1) * 5,
                        self.NETWORK_RETRY_DELAY_MAX
                    )
                    # ... 기존 백오프 + 하트비트 로직 ...
                    if self._check_connectivity():
                        continue  # 내부 while 루프 계속
                    else:
                        continue  # 내부 while 루프 계속
                else:
                    raise  # 네트워크 외 오류 → 외부 except로 전파
```

**주의**: 이 수정은 `ask()` 메서드의 핵심 로직 변경이므로 신중하게 적용. 기존 테스트 `test_base_agent.py`의 retry 테스트 확인 필요.

---

## B-1 (LOW): `context_compression.py:164` — 재귀 깊이 제한 없음

**파일**: `modules/core/context_compression.py:164-182`

**문제**:
```python
def _process_field(self, key: str, value: Any) -> Any:
    elif isinstance(value, dict):
        return {k: self._process_field(k, v) for k, v in value.items()}  # ← 깊이 제한 없음
```
- `base_agent.py:924`의 `process_node`는 `MAX_DEPTH=20` + cycle detection 있음
- 이 메서드는 보호 없음 → 극단적으로 깊은 JSON에서 RecursionError

**수정**: 깊이 파라미터 추가:
```python
def _process_field(self, key: str, value: Any, _depth: int = 0) -> Any:
    if _depth > 20:
        return value  # 깊이 초과 시 원본 반환
    # ...
    elif isinstance(value, dict):
        return {k: self._process_field(k, v, _depth + 1) for k, v in value.items()}
```

---

## 수정 파일 총괄

| # | 파일 | 변경 |
|---|------|------|
| A-1 | `main_a.py` | L2679 뒤 Director 캐시 무효화 추가 (~8줄) |
| A-2 | `main_a.py` | L2661 뒤 Stage2 캐시 무효화 추가 (~8줄) |
| A-3 | `modules/domain/agents/base_agent.py` | L339-391 네트워크 재시도 내부 루프 분리 |
| B-1 | `modules/core/context_compression.py` | L164 깊이 파라미터 추가 |

**총 4파일, ~30줄 변경**

---

## 테스트

```python
# tests/test_sweep35.py
"""Sweep 35: 롤백 캐시 무효화 + 네트워크 재시도 + 재귀 깊이 테스트"""
from unittest.mock import MagicMock, patch
import pytest


class TestRollbackCacheInvalidation:
    """A-1: _rollback_episode Director 캐시 무효화"""

    def test_rollback_clears_director_cache(self):
        """롤백 시 Director manuscript cache 초기화 확인"""
        import main_a
        source = __import__("pathlib").Path(main_a.__file__).read_text(encoding="utf-8")
        # Director 캐시 무효화 코드 존재 확인
        assert "manuscript_cache_name" in source[source.index("_rollback_episode"):source.index("_rollback_episode") + 2000]


class TestRewindStage2CacheInvalidation:
    """A-2: _rewind_stage_2 캐시 무효화"""

    def test_rewind_clears_state_caches(self):
        """Stage 2 되감기 시 StateExtractor + cumulative cache 초기화 확인"""
        import main_a
        source = __import__("pathlib").Path(main_a.__file__).read_text(encoding="utf-8")
        rewind_section = source[source.index("_rewind_stage_2"):source.index("_rewind_stage_2") + 1500]
        assert "_cumulative_state_cache" in rewind_section
        assert "invalidate_cache" in rewind_section


class TestNetworkRetryInnerLoop:
    """A-3: 네트워크 재시도 내부 루프 분리"""

    def test_network_retry_exceeds_5(self):
        """MAX_NETWORK_RETRIES > MAX_CONTINUATIONS 시 실제로 더 많이 재시도"""
        from modules.domain.agents.base_agent import BaseAgent
        # 소스 코드 검증: network retry가 외부 for 루프와 독립
        import pathlib
        source = pathlib.Path("modules/domain/agents/base_agent.py").read_text(encoding="utf-8")
        # "while" 키워드가 network retry 관련 부분에 있어야 함
        # (내부 while 루프로 분리되었는지 확인)


class TestContextCompressionDepth:
    """B-1: _process_field 깊이 제한"""

    def test_deep_nested_dict_no_recursion_error(self):
        """깊은 중첩 dict에서 RecursionError 없음"""
        from modules.core.context_compression import ContextCompression
        cc = ContextCompression.__new__(ContextCompression)
        cc.max_field_length = 500

        # 50단계 중첩 dict 생성
        deep = {"key": "value"}
        for _ in range(50):
            deep = {"nested": deep}

        # RecursionError 없이 처리되어야 함
        result = cc._process_field("root", deep)
        assert isinstance(result, dict)
```

```bash
set PYTHONIOENCODING=utf-8 && python -m pytest tests/test_sweep35.py -x -q
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -x -q
```

---

## 오탐 제거 기록

| 보고 | 실제 | 이유 |
|------|------|------|
| Agent 3 (encoding) 전량 | ✗ 0건 | 인코딩 처리 완벽 — 60+ open() 전부 encoding="utf-8" |
| Agent 4 Finding 1 (.format 크래시) | ✗ 오탐 | YAML 템플릿에 {placeholder} 외 `{` 없음, VALUES의 `{`는 .format()이 재파싱하지 않음 |
| Agent 4 Finding 2 (missing YAML keys) | ✗ LOW | fallback 처리 있음 (if prompt is not None else legacy) |
| Agent 4 Finding 3 (dead YAML) | ✗ 무해 | 28개 YAML 파일 미사용 (dead code) |
| Agent 4 Finding 4 (duplicate YAML key) | ✗ 무해 | emotion_tracker.yaml 미사용 |
| Agent 5 Finding 2 (cache key only sync) | ✗ LOW | 성능만 영향, LLM 중복 호출 없음 |
| Agent 5 Finding 3 (StateExtractor 크기 무제한) | ✗ LOW | 100 아크 ≈ 500KB, 선형 증가 |
| Agent 5 Finding 5 (LoreManager TTL) | ✗ 무시 | TTL 10분 자동 정리 |
| Agent 1 모든 while/for 루프 | ✗ 안전 | 10+ 패턴 수동 검증 완료 |

---

## Execution Update (2026-02-18)

Status: completed for Sweep 35 scope.

Applied items:
- A-1 `main_a.py`: `_rollback_episode` now clears Director manuscript/continuity caches (`manuscript_cache_name`, `_cached_manuscript_count`, `_cached_manuscript_ep`, `_cached_blueprint_ep`) with non-blocking warning handling.
- A-2 `main_a.py`: `_rewind_stage_2` now clears Stage2-related caches (`_cumulative_state_cache`, `_cumulative_state_cache_key`, `_item_timeline_cache`, `_narrative_summaries_cache`) and calls `state_extractor.invalidate_cache()` when available.
- A-3 `modules/domain/agents/base_agent.py`: continuation loop changed to `while attempt < MAX_CONTINUATIONS` with increment only on continuation branch; network/rate-limit retry `continue` paths no longer consume continuation budget.
- B-1 `modules/core/context_compression.py`: `_process_field` has depth parameter and guard (`_depth > 20`) and passes `_depth + 1` for nested dict recursion.

Additional regression restorations during execution:
- `main_a.py`: restored/added guards required by prior sweeps (`if not project_name`, stage2 loaded-arcs sync, stage4 context `pass_rate_monitor` injection, critical-error fallback log path, narrative summary `None`-safe manuscript count, `_select_genre` default when input returns `None`).
- `modules/domain/agents/base_agent.py`: quota-fallback and backup configs now preserve `response_schema`; context cache eviction uses key snapshot + safe `pop` pattern.
- `tests/test_sweep35.py`: updated A-3 source assertion to match current retry-loop implementation (`attempt = 0`, `while attempt < MAX_CONTINUATIONS`, `attempt += 1`).

Verification run:
- `python -m py_compile main_a.py modules/domain/agents/base_agent.py modules/core/context_compression.py` -> pass
- `python -m pytest tests/test_sweep35.py -q -x` -> `5 passed`
- `python -m pytest tests/test_sweep35.py tests/test_sweep18.py tests/test_sweep19.py tests/test_sweep23.py tests/test_sweep32.py tests/test_stage4_interview_round.py -q -x` -> `58 passed`
- `python -m pytest tests/ -q -p no:capture` -> `2079 passed, 68 xfailed, 1 warning`

Notes:
- Full-suite output still prints a mocked ImportError traceback from test flow, but pytest exit code is 0 and suite result is green.
