# [Codex Task] Stage 2 Arc Ensemble — 전략별 분리 피드백 추가

## 문제
Stage 3 (Blueprint)과 Stage 4 (원고)는 REJECT 시 **REJECT된 전략에만 추가 피드백**을 주는 `strategy_specific_feedback` + `rejected_strategy` 구조가 있다.
Stage 2 (Arc)는 이 구조가 **누락**되어, 3개 전략 모두에 동일한 통합 피드백만 전달한다.

### 현재 상태 비교

| 구간 | 파일 | 분리 피드백 |
|------|------|-----------|
| Stage 3 Blueprint | `modules/domain/agents/blueprint_ensemble.py` L118-119 | ✅ `strategy_specific_feedback`, `rejected_strategy` |
| Stage 4 원고 | `modules/domain/agents/chief_writer.py` L125 | ✅ `strategy_specific_feedback`, `rejected_strategy` |
| **Stage 2 Arc** | `modules/domain/agents/arc_ensemble.py` L86 | ❌ `feedback`만 존재 |

---

## 수정 대상 파일

### 1. `modules/domain/agents/arc_ensemble.py`

#### A. `generate_ensemble()` 시그니처 수정 (L77~)

**현재:**
```python
def generate_ensemble(
    self,
    arc_no: int,
    ep_start: int,
    vol_strategy: str,
    curr_block: dict,
    prev_arc_context: str,
    constraint_block: str,
    assets: dict = None,
    feedback: str = "",
    protagonist_name: str = "주인공",
    # ... 나머지 파라미터
) -> tuple[dict | None, list[dict]]:
```

**변경:**
```python
def generate_ensemble(
    self,
    arc_no: int,
    ep_start: int,
    vol_strategy: str,
    curr_block: dict,
    prev_arc_context: str,
    constraint_block: str,
    assets: dict = None,
    feedback: str = "",
    strategy_specific_feedback: str = "",  # [신규] 특정 전략 전용 추가 피드백
    rejected_strategy: str = "",           # [신규] REJECT된 전략 이름
    protagonist_name: str = "주인공",
    # ... 나머지 파라미터 동일
) -> tuple[dict | None, list[dict]]:
```

#### B. `generate_ensemble()` 내부 — worker submit 분기 추가

**참조 패턴**: `blueprint_ensemble.py` L190-195

현재 `arc_ensemble.py`의 ThreadPoolExecutor 루프 (L148쯤):
```python
for strategy in self.strategies:
    future = executor.submit(
        self._generate_single,
        # ... 기존 파라미터
        feedback=feedback,
        strategy=strategy,
        # ...
    )
```

**변경:**
```python
for strategy in self.strategies:
    _strategy_feedback = (
        strategy_specific_feedback
        if (strategy.get("name") == rejected_strategy and strategy_specific_feedback)
        else ""
    )
    future = executor.submit(
        self._generate_single,
        # ... 기존 파라미터
        feedback=feedback,
        strategy_feedback=_strategy_feedback,  # [신규]
        strategy=strategy,
        # ...
    )
```

#### C. `_generate_single()` 시그니처 및 피드백 병합 (L287~)

**참조 패턴**: `blueprint_ensemble.py` L316-334

현재:
```python
def _generate_single(
    self,
    # ... 기존 파라미터
    feedback: str,
    strategy: dict,
    # ...
) -> dict | None:
```

**변경:**
```python
def _generate_single(
    self,
    # ... 기존 파라미터
    feedback: str,
    strategy_feedback: str = "",  # [신규]
    strategy: dict,
    # ...
) -> dict | None:
    try:
        # 기존 코드 앞에 피드백 병합 로직 추가
        _merged_feedback = feedback or ""
        if strategy_feedback:
            _merged_feedback = (
                f"{_merged_feedback}\n\n[전략별 보정 피드백]\n{strategy_feedback}"
                if _merged_feedback
                else f"[전략별 보정 피드백]\n{strategy_feedback}"
            )
        # 이후 프롬프트 구성 시 feedback 대신 _merged_feedback 사용
```

프롬프트 로드 부분에서 `feedback` → `_merged_feedback` 교체:
```python
# 현재 (L376쯤):
feedback=self._escape_braces(feedback[:1500] if feedback else "(없음)"),

# 변경:
feedback=self._escape_braces(_merged_feedback[:1500] if _merged_feedback else "(없음)"),
```

---

### 2. `modules/domain/agents/four_phase_arc_generator.py`

#### A. 당선 전략 추적 변수 추가 (L198쯤, retry 루프 앞)

```python
# [Patch Mode] 내부 retry용 이전 REJECT 추적
_prev_rejected_arc = None
_prev_reject_feedback = ""
_prev_selected_strategy = ""  # [신규] REJECT된 당선 전략 이름
```

#### B. 당선 전략 저장 (L340쯤, Phase 2 완료 후)

```python
pipeline_result["phases"]["generate"] = {
    "status": "complete",
    "candidates_count": len(all_candidates),
    "selected_strategy": best_arc.get("_ensemble_meta", {}).get("best_strategy", "unknown"),
}
# [신규] 당선 전략 이름 기록 (REJECT 시 다음 retry에 전달)
_current_strategy = best_arc.get("_ensemble_meta", {}).get("strategy", "")
```

#### C. REJECT 시 전략 정보 저장 (L388쯤)

현재:
```python
if best_arc:
    _prev_rejected_arc = best_arc
    _prev_reject_feedback = feedback
```

**변경:**
```python
if best_arc:
    _prev_rejected_arc = best_arc
    _prev_reject_feedback = feedback
    _prev_selected_strategy = _current_strategy  # [신규]
```

#### D. `generate_ensemble()` 호출에 전략 피드백 전달 (L288쯤)

현재 (L288~302):
```python
best_arc, all_candidates = self.ensemble.generate_ensemble(
    arc_no=arc_no,
    ep_start=ep_start,
    vol_strategy=vol_strategy,
    curr_block=curr_block,
    prev_arc_context=prev_arc_context,
    constraint_block=full_constraint_block,
    assets=assets,
    feedback=feedback,
    protagonist_name=protagonist_name,
    protagonist_config=protagonist_config,
    entity_registry=entity_registry,
    ep_count=ep_count,
    retry=retry,
)
```

**변경:**
```python
best_arc, all_candidates = self.ensemble.generate_ensemble(
    arc_no=arc_no,
    ep_start=ep_start,
    vol_strategy=vol_strategy,
    curr_block=curr_block,
    prev_arc_context=prev_arc_context,
    constraint_block=full_constraint_block,
    assets=assets,
    feedback=feedback,
    strategy_specific_feedback=_prev_reject_feedback if retry > 0 else "",  # [신규]
    rejected_strategy=_prev_selected_strategy if retry > 0 else "",          # [신규]
    protagonist_name=protagonist_name,
    protagonist_config=protagonist_config,
    entity_registry=entity_registry,
    ep_count=ep_count,
    retry=retry,
)
```

---

## 수정 범위 요약

| 파일 | 변경 유형 | 예상 라인 수 |
|------|----------|------------|
| `arc_ensemble.py` | 시그니처 + 분기 + 병합 | +15줄 |
| `four_phase_arc_generator.py` | 변수 + 전략추적 + 호출 | +8줄 |
| **합계** | | **~23줄** |

## 검증 방법
1. 기존 테스트 통과 확인
2. `retry > 0` 시 `_merged_feedback`에 `[전략별 보정 피드백]` 섹션이 REJECT된 전략에만 포함되는지 로그 확인
3. Stage 3 `blueprint_ensemble.py` L190-194, L328-334와 동일 패턴인지 비교

## 주의사항
- `_generate_single()` 시그니처에서 `strategy_feedback`은 `strategy` 파라미터 **앞에** 위치해야 함 (기존 호출에서 `strategy`를 keyword arg로 전달하므로 순서 자유)
- `patch_arc_with_feedback()` (L519)의 ensemble 호출에도 `strategy_specific_feedback="", rejected_strategy=""`를 추가해야 하지만, 패치 모드에서는 전략 분리가 불필요하므로 기본값("")으로 충분
- `_ensemble_meta`에 `strategy` 키가 이미 저장되고 있는지 확인 필요 — 현재 `arc_ensemble.py`에는 `best_strategy`로 저장 중. 키 이름 맞추어야 함
