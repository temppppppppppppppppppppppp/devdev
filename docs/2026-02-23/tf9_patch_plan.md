# TF-9 패치 플랜 (Codex 실행용)

> **작성일**: 2026-02-23
> **실행자**: Codex (자율 에이전트)
> **베이스라인**: 2,542 passed, 0 violations (commit `2fcffff`)
> **성격**: 감사 없음 — TF-8 감리 후 발견된 버그 수정 + MEDIUM 백로그 패치

---

## ★★★ CODEX 최우선 오더 (이 섹션부터 읽어라)

1. **이 문서 전체를 읽어라**
2. **tf9_findings.md 확인** — 완료 단계 확인 후 거기서부터 재개
3. **각 Step은 반드시 Read 도구로 해당 파일을 직접 읽은 후 수정한다**
4. **각 Step 완료 즉시 tf9_findings.md "현재 위치" 섹션을 업데이트한다**

### 컨텍스트 컴팩트 복구

1. `docs/2026-02-23/tf9_patch_plan.md` 재독
2. `docs/2026-02-23/tf9_findings.md` 재독 → "현재 위치" 확인
3. 다음 미완료 Step부터 즉시 재개
4. **절대 Step 1부터 다시 시작하지 않는다**

---

## 배경

TF-8 2차 감리(`2fcffff`)에서 발견된 신규 HIGH 이슈 1건 + MEDIUM 백로그 4건을 처리한다.

| ID | 등급 | 내용 |
|----|------|------|
| TF8R-1 | HIGH | `stage4_context_builder` arc_no 전달이 죽은 코드 (항상 None) |
| TF8-F-2 | MEDIUM | invalid retrieval_mode silent 폴백 (경고 없음) |
| TF8-I-2 | MEDIUM | retrieval_mode 라우팅 단위 테스트 부재 |
| TF8-I-3 | MEDIUM | D2 로그 caplog 포맷 검증 테스트 부재 |

> E-2(dense 로그 hits/selected 보강)는 `_knn_search` 내부 리팩터 필요 — 이번 TF에서 보류.

---

## 진행 테이블

| Step | 내용 | 대상 파일 | 상태 |
|------|------|-----------|------|
| Step 1 | arc_no 전달 수정 (TF8R-1) | `stage4_context_builder.py` | ⬜ |
| Step 2 | invalid mode 경고 로그 (TF8-F-2) | `stage2_preflight.py`, `stage4_context_builder.py` | ⬜ |
| Step 3 | retrieval_mode 라우팅 테스트 (TF8-I-2) | `tests/test_retrieval_mode_routing.py` (신규) | ⬜ |
| Step 4 | D2 로그 caplog 테스트 (TF8-I-3) | `tests/test_vec_memory.py` | ⬜ |
| Step 5 | 최종 검증 + 커밋 | pytest, ruff | ⬜ |

---

## Step 1: arc_no 전달 수정 (TF8R-1) — HIGH

### 문제 요약

`_execute_retrieval_plan(plan)` 내부에서 `getattr(plan, "arc_no", None)`을 사용하지만
`RetrievalPlan` 필드는 `[stage, episode_num, slots, total_budget_chars, used_llm]`이므로
`current_arc_no`는 항상 `None`. arc bonus가 stage4 hybrid/dense에서 전혀 작동하지 않는다.

### 읽어야 할 파일

| 파일 | 구간 | 이유 |
|------|------|------|
| `modules/core/stage4_context_builder.py` | L140–L200 | `_execute_retrieval_plan` 시그니처·본문 |
| `modules/core/stage4_context_builder.py` | L710–L750 | 호출부 + `arc_data` 가용성 확인 |

### 수정 내용

**변경 1: `_execute_retrieval_plan` 시그니처 + 본문 (L140, L149)**

현재:
```python
def _execute_retrieval_plan(self, plan: "RetrievalPlan") -> list[str]:
    ...
    current_arc_no = getattr(plan, "arc_no", None)
```

수정 후:
```python
def _execute_retrieval_plan(self, plan: "RetrievalPlan", arc_no: int | None = None) -> list[str]:
    ...
    current_arc_no = arc_no
```

**변경 2: 호출부 (L739–L741 부근)**

현재:
```python
for _retrieved in self._execute_retrieval_plan(_retrieval_plan):
```

수정 후 (호출 직전에 arc_no 추출 후 전달):
```python
_arc_no_s4 = arc_data.get("arc_no", None) if arc_data else None
for _retrieved in self._execute_retrieval_plan(_retrieval_plan, arc_no=_arc_no_s4):
```

### 검증

```bash
pytest tests/ -q --tb=short 2>&1 | tail -5
ruff check modules/core/stage4_context_builder.py
```

### tf9_findings.md 업데이트

완료 후 "현재 위치"를 `Step 1 완료 / Next: Step 2`로 갱신.

---

## Step 2: invalid retrieval_mode 경고 로그 (TF8-F-2) — MEDIUM

### 문제 요약

`retrieval_mode`가 `"dense"/"hybrid"/"sparse"` 이외의 값이면 else 분기(dense)로 silent 폴백.
운영자가 오설정을 인지하기 어렵다.

### 읽어야 할 파일

| 파일 | 구간 | 이유 |
|------|------|------|
| `modules/core/stage2_preflight.py` | L134–L166 | retrieval_mode 분기 전체 |
| `modules/core/stage4_context_builder.py` | L167–L196 | retrieval_mode 분기 전체 |

### 수정 내용

**`stage2_preflight.py` — else 분기 진입부 (L158 부근)**

현재:
```python
    else:
        result = memory.retrieve_multi_query_context(
```

수정 후:
```python
    else:
        if _retrieval_mode not in ("dense", "hybrid", "sparse"):
            logging.warning(
                "[Retrieval] 알 수 없는 retrieval_mode '%s', dense로 폴백",
                _retrieval_mode,
            )
        result = memory.retrieve_multi_query_context(
```

**`stage4_context_builder.py` — else 분기 진입부 (L186 부근)**

현재:
```python
                    else:
                        result = memory.retrieve_multi_query_context(
```

수정 후:
```python
                    else:
                        if _retrieval_mode not in ("dense", "hybrid", "sparse"):
                            logging.warning(
                                "[Retrieval] 알 수 없는 retrieval_mode '%s', dense로 폴백",
                                _retrieval_mode,
                            )
                        result = memory.retrieve_multi_query_context(
```

### 주의

- `stage2_preflight.py`의 else는 `vec_slot_count <= 1` 분기 이후이므로 mode="dense"도 진입 가능.
  경고 조건 `not in ("dense", "hybrid", "sparse")`가 반드시 있어야 false alarm 없음.

### 검증

```bash
ruff check modules/core/stage2_preflight.py modules/core/stage4_context_builder.py
pytest tests/ -q --tb=short 2>&1 | tail -5
```

### tf9_findings.md 업데이트

완료 후 "현재 위치"를 `Step 2 완료 / Next: Step 3`로 갱신.

---

## Step 3: retrieval_mode 라우팅 단위 테스트 (TF8-I-2) — MEDIUM

### 목적

`_execute_retrieval_plan` 분기 + Step 1 arc_no 수정 정합성을 고정하는 테스트.
hybrid/sparse/dense/invalid 4개 경로 검증.

### 파일 경로

`tests/test_retrieval_mode_routing.py` (신규 파일)

### 테스트 구조

아래 4개 테스트를 작성한다. `unittest.mock.patch`로 `_threshold` 모킹.

```python
"""retrieval_mode 라우팅 단위 테스트 (TF8-I-2, TF8R-1 arc_no 수정 검증 포함)."""
import types
import unittest.mock as mock

import pytest

from modules.core.stage4_context_builder import Stage4ContextBuilder


def _make_ctx():
    """최소 Stage4Context 목 객체."""
    ctx = mock.MagicMock()
    ctx.ui.log = mock.MagicMock()
    return ctx


def _make_plan(episode_num=5):
    """최소 RetrievalPlan 목 객체."""
    slot = mock.MagicMock()
    slot.priority = 2
    slot.source = "vec_memory"
    slot.category = "general"
    slot.query = "테스트 쿼리"
    plan = mock.MagicMock()
    plan.episode_num = episode_num
    plan.slots = [slot]
    return plan


def _make_memory():
    """최소 VecMemory 목 객체."""
    mem = mock.MagicMock()
    mem.retrieve_hybrid_context.return_value = "hybrid result"
    mem.retrieve_multi_query_context.return_value = "dense result"
    mem._fts_search.return_value = [{"ep_num": 1, "summary": "sparse summary"}]
    return mem


class TestRetrievalModeRouting:
    def test_hybrid_mode_calls_retrieve_hybrid_context(self):
        """retrieval_mode=hybrid이면 retrieve_hybrid_context가 호출된다."""
        ctx = _make_ctx()
        builder = Stage4ContextBuilder.__new__(Stage4ContextBuilder)
        builder.ctx = ctx
        ctx.memory = _make_memory()

        plan = _make_plan()
        with mock.patch(
            "modules.core.stage4_context_builder._threshold",
            side_effect=lambda k, d=None: "hybrid" if "retrieval_mode" in k else d,
        ):
            list(builder._execute_retrieval_plan(plan))

        ctx.memory.retrieve_hybrid_context.assert_called_once()
        ctx.memory.retrieve_multi_query_context.assert_not_called()

    def test_sparse_mode_calls_fts_search(self):
        """retrieval_mode=sparse이면 _fts_search가 호출된다."""
        ctx = _make_ctx()
        builder = Stage4ContextBuilder.__new__(Stage4ContextBuilder)
        builder.ctx = ctx
        ctx.memory = _make_memory()

        plan = _make_plan()
        with mock.patch(
            "modules.core.stage4_context_builder._threshold",
            side_effect=lambda k, d=None: "sparse" if "retrieval_mode" in k else d,
        ):
            list(builder._execute_retrieval_plan(plan))

        ctx.memory._fts_search.assert_called_once()
        ctx.memory.retrieve_hybrid_context.assert_not_called()

    def test_invalid_mode_falls_back_to_dense(self):
        """retrieval_mode=invalid이면 retrieve_multi_query_context(dense)로 폴백된다."""
        ctx = _make_ctx()
        builder = Stage4ContextBuilder.__new__(Stage4ContextBuilder)
        builder.ctx = ctx
        ctx.memory = _make_memory()

        plan = _make_plan()
        with mock.patch(
            "modules.core.stage4_context_builder._threshold",
            side_effect=lambda k, d=None: "unknown_mode" if "retrieval_mode" in k else d,
        ):
            list(builder._execute_retrieval_plan(plan))

        ctx.memory.retrieve_multi_query_context.assert_called_once()
        ctx.memory.retrieve_hybrid_context.assert_not_called()

    def test_arc_no_propagated_to_hybrid(self):
        """arc_no 파라미터가 retrieve_hybrid_context에 전달된다 (TF8R-1 수정 검증)."""
        ctx = _make_ctx()
        builder = Stage4ContextBuilder.__new__(Stage4ContextBuilder)
        builder.ctx = ctx
        ctx.memory = _make_memory()

        plan = _make_plan()
        with mock.patch(
            "modules.core.stage4_context_builder._threshold",
            side_effect=lambda k, d=None: "hybrid" if "retrieval_mode" in k else (10 if k in ("smart_retrieval.dense_k", "smart_retrieval.sparse_k") else (60 if "rrf_k" in k else d)),
        ):
            list(builder._execute_retrieval_plan(plan, arc_no=3))

        call_kwargs = ctx.memory.retrieve_hybrid_context.call_args
        assert call_kwargs.kwargs.get("current_arc_no") == 3 or (
            call_kwargs.args and 3 in call_kwargs.args
        ), f"current_arc_no=3이 전달되지 않음: {call_kwargs}"

    def test_arc_no_propagated_to_dense(self):
        """arc_no 파라미터가 retrieve_multi_query_context에 전달된다 (TF8R-1 수정 검증)."""
        ctx = _make_ctx()
        builder = Stage4ContextBuilder.__new__(Stage4ContextBuilder)
        builder.ctx = ctx
        ctx.memory = _make_memory()

        plan = _make_plan()
        with mock.patch(
            "modules.core.stage4_context_builder._threshold",
            side_effect=lambda k, d=None: "dense" if "retrieval_mode" in k else d,
        ):
            list(builder._execute_retrieval_plan(plan, arc_no=5))

        call_kwargs = ctx.memory.retrieve_multi_query_context.call_args
        assert call_kwargs.kwargs.get("current_arc_no") == 5 or (
            call_kwargs.args and 5 in call_kwargs.args
        ), f"current_arc_no=5이 전달되지 않음: {call_kwargs}"
```

### 주의

- `_threshold` mock: `side_effect`에서 `"retrieval_mode"` 키 여부로 값 반환 분기.
  기타 키는 `d` (기본값) 반환.
- Stage4ContextBuilder를 `__new__`로 생성해 DI 없이 최소 테스트.
- 실제 파일 Read 후 import 경로 + 클래스명 확인 필수.

### 검증

```bash
pytest tests/test_retrieval_mode_routing.py -v --tb=short
ruff check tests/test_retrieval_mode_routing.py
```

### tf9_findings.md 업데이트

완료 후 "현재 위치"를 `Step 3 완료 / Next: Step 4`로 갱신.

---

## Step 4: D2 로그 caplog 포맷 테스트 (TF8-I-3) — MEDIUM

### 목적

D2 observability 로그의 파싱 가능 포맷(`[VecMem] path=...`)이 회귀하지 않도록 고정.

### 읽어야 할 파일

| 파일 | 구간 | 이유 |
|------|------|------|
| `modules/core/vec_memory.py` | L437–L464 | dense/fallback 경로 로그 위치 확인 |
| `tests/test_vec_memory.py` | 마지막 50줄 | 추가 위치 확인 |

### 추가할 테스트 (`tests/test_vec_memory.py` 기존 클래스에 추가)

기존 `TestHybridRetrieval` 또는 새 `TestD2Logging` 클래스에 아래 테스트를 추가:

```python
def test_d2_fallback_log_format(self, caplog):
    """임베딩 실패 시 [VecMem] path=fallback 포맷으로 로그가 찍힌다."""
    import logging
    vm, _ = self._make_vm()
    vm._embed_text = lambda _: None  # 임베딩 실패 강제

    with caplog.at_level(logging.DEBUG, logger="root"):
        result = vm.retrieve_high_res_context("테스트 쿼리", current_ep=5)

    d2_logs = [r.message for r in caplog.records if "[VecMem]" in r.message]
    assert any("path=fallback" in msg for msg in d2_logs), (
        f"path=fallback 로그 없음: {d2_logs}"
    )
    assert any("ep<5" in msg for msg in d2_logs), (
        f"ep<5 없음: {d2_logs}"
    )

def test_d2_dense_log_format(self, caplog):
    """임베딩 성공 + KNN 결과 있을 때 [VecMem] path=dense 로그가 찍힌다."""
    import logging
    vm, _ = self._make_vm()
    vm._embed_text = lambda _: [0.0] * EMBED_DIM  # 임베딩 성공 강제
    vm._knn_search = lambda *a, **k: "mock result"  # KNN 결과 강제

    with caplog.at_level(logging.DEBUG, logger="root"):
        result = vm.retrieve_high_res_context("테스트 쿼리", current_ep=5)

    d2_logs = [r.message for r in caplog.records if "[VecMem]" in r.message]
    assert any("path=dense" in msg for msg in d2_logs), (
        f"path=dense 로그 없음: {d2_logs}"
    )
    assert any("ep<5" in msg for msg in d2_logs), (
        f"ep<5 없음: {d2_logs}"
    )
```

### 주의

- `EMBED_DIM` 상수를 `from modules.core.vec_memory import EMBED_DIM`으로 import하거나 `3072`로 직접 사용.
- `_make_vm` 헬퍼가 반환하는 `vm` 객체에 `_embed_text`를 직접 교체 가능한지 확인 후 진행.
- `caplog`은 pytest fixture이므로 `self, caplog` 시그니처로 사용.
- 기존 클래스에 `caplog` 파라미터가 없으면 새 클래스 `TestD2Logging`으로 분리.

### 검증

```bash
pytest tests/test_vec_memory.py -k "test_d2" -v --tb=short
```

### tf9_findings.md 업데이트

완료 후 "현재 위치"를 `Step 4 완료 / Next: Step 5`로 갱신.

---

## Step 5: 최종 검증 + 커밋

### 검증

```bash
pytest tests/ -q --tb=short 2>&1 | tail -5
# 기대: 2545+ passed, 0 xfailed (신규 테스트 5개 이상 추가 예상)

ruff check modules/ main_a.py tests/
# 기대: All checks passed.
```

### 커밋 메시지

```
fix(tf9): arc_no retrieval 전달 수정 + MEDIUM 백로그 패치 (TF8R-1/F-2/I-2/I-3)

- Step 1: stage4_context_builder arc_no 죽은 코드 수정 (항상 None → arc_data에서 추출)
- Step 2: invalid retrieval_mode silent 폴백에 경고 로그 추가
- Step 3: retrieval_mode 라우팅 + arc_no 전달 단위 테스트 5개 추가
- Step 4: D2 로그 caplog 포맷 테스트 2개 추가
- 테스트 기준선: 2,5XX passed, 0 xfailed
```

### tf9_findings.md 최종 업데이트

```
Last Completed Round: Step 5 (TF-9 완료)
Status: 완료
최종 pytest: 2,5XX passed
최종 커밋: <해시>
```

---

## 부록: 핵심 코드 위치

| 항목 | 파일 | 줄 |
|------|------|----|
| `_execute_retrieval_plan` 시그니처 | `stage4_context_builder.py` | L140 |
| `current_arc_no = getattr(...)` 제거 대상 | `stage4_context_builder.py` | L149 |
| 호출부 (arc_no 주입 위치) | `stage4_context_builder.py` | L740 |
| stage2 else 분기 (경고 추가) | `stage2_preflight.py` | L158 |
| stage4 else 분기 (경고 추가) | `stage4_context_builder.py` | L186 |
| dense 로그 (fallback) | `vec_memory.py` | L447–L453 |
| dense 로그 (dense) | `vec_memory.py` | L457–L463 |
