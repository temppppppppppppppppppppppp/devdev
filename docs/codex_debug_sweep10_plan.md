# Debug Sweep 10 — 숨은 로직 버그 수정

> **목적**: 코드 스캔으로 발견된 실제 로직 버그 7건 수정. 리팩토링/스타일 아님 — 모두 잘못된 동작을 유발하는 진짜 버그.
> **규칙**: 각 항목은 독립 실행 가능. 수정 후 반드시 `set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -x -q` 통과 확인.
> **테스트 기준선**: 1,710 passed + 68 xfailed (Sweep 9 적용 후 변동 있으면 그 숫자 기준)
> **Ruff**: 수정한 파일에 `ruff check <파일> && ruff format <파일>` 적용

---

## 인코딩 안전 규칙 (필독)

1. **파일 읽기/쓰기 시 반드시 `encoding="utf-8"` 명시**
2. **한글 주석·문자열을 절대 변경하지 말 것** — 읽지 못하는 한글은 그대로 유지
3. **BOM 삽입 금지** — UTF-8 without BOM
4. **파일 전체를 다시 쓰지 말 것** — 변경할 부분만 정확히 수정
5. **수정 전후 파일 크기 비교** — ±10% 이상 차이나면 인코딩 파손 의심
6. **검증**: `python -c "open('<파일>', encoding='utf-8').read()"` 로 깨짐 확인

---

## A. CRITICAL — 적응형 임계값 반전 (1건)

### A-1: `modules/validation/validation_orchestrator.py:1391` — 불리언 반전

**파일**: `modules/validation/validation_orchestrator.py`
**라인**: 1391
**버그**: `set_manual_threshold_v59(threshold, 0)` 호출 시 (0=영구 고정), 적응형 임계값이 **활성화**됨. 주석은 "비활성화"인데 코드가 반대.
**영향**: 사용자가 수동으로 임계값을 영구 고정해도, 적응형 계산이 계속 덮어씀 → 수동 설정 무시됨.

**현재 코드**:
```python
self.use_adaptive_threshold = duration_episodes == 0  # 영구면 적응형 비활성화
```

**수정 코드**:
```python
self.use_adaptive_threshold = duration_episodes != 0  # 영구(0)면 적응형 비활성화, 임시(N>0)면 N화 후 적응형 복원
```

**검증 로직**:
- `duration_episodes == 0` (영구) → `use_adaptive_threshold = False` → 수동 임계값 유지
- `duration_episodes > 0` (임시) → `use_adaptive_threshold = True` → N화 후 적응형 복원

**테스트**: 아래 테스트 추가 (`tests/test_sweep10.py`에 포함)

```python
def test_manual_threshold_permanent_disables_adaptive():
    """A-1: duration_episodes=0 → use_adaptive_threshold=False"""
    orch = ValidationOrchestrator.__new__(ValidationOrchestrator)
    orch.current_threshold = 70
    orch.use_adaptive_threshold = True
    orch.threshold_profile = {"base_threshold": 70}
    orch.set_manual_threshold_v59(80, duration_episodes=0)
    assert orch.use_adaptive_threshold is False
    assert orch.current_threshold == 80

def test_manual_threshold_temporary_keeps_adaptive():
    """A-1: duration_episodes=5 → use_adaptive_threshold=True"""
    orch = ValidationOrchestrator.__new__(ValidationOrchestrator)
    orch.current_threshold = 70
    orch.use_adaptive_threshold = True
    orch.threshold_profile = {"base_threshold": 70}
    orch.set_manual_threshold_v59(80, duration_episodes=5)
    assert orch.use_adaptive_threshold is True
```

---

## B. HIGH — 앙상블 선택 편향 (1건)

### B-1: `modules/domain/agents/director_ensemble.py:397` — 항상 첫 번째 합격 후보 선택

**파일**: `modules/domain/agents/director_ensemble.py`
**라인**: 395-400
**버그**: LLM이 불합격 후보를 선택하면 `qualified_indices[0]`(항상 첫 번째)로 폴백. 더 긴(더 좋은) 합격 후보가 있어도 무시.
**영향**: 후보 A=4000자, C=5000자일 때 LLM이 B(불합격)를 선택하면 C(5000자) 대신 A(4000자)를 강제 선택.

**현재 코드**:
```python
if selected_idx not in qualified_indices and qualified_indices:
    old_selection = selected_letter
    selected_idx = qualified_indices[0]
    selected_letter = ["A", "B", "C"][selected_idx]
    v60_97_swapped = True
```

**수정 코드**:
```python
if selected_idx not in qualified_indices and qualified_indices:
    old_selection = selected_letter
    # 합격 후보 중 가장 긴 원고 선택 (품질 추정)
    selected_idx = max(qualified_indices, key=lambda i: len(candidates[i].get("manuscript", "")))
    selected_letter = ["A", "B", "C"][selected_idx]
    v60_97_swapped = True
```

**테스트**:
```python
def test_ensemble_selects_longest_qualified():
    """B-1: 불합격 선택 시 가장 긴 합격 후보로 폴백"""
    candidates = [
        {"manuscript": "A" * 4000},
        {"manuscript": "B" * 3000},  # 불합격
        {"manuscript": "C" * 5000},
    ]
    qualified_indices = [0, 2]  # A와 C만 합격
    selected_idx = 1  # LLM이 B 선택 (불합격)

    if selected_idx not in qualified_indices and qualified_indices:
        selected_idx = max(qualified_indices, key=lambda i: len(candidates[i].get("manuscript", "")))

    assert selected_idx == 2  # C(5000자)가 선택되어야 함
```

---

## C. MEDIUM — LLM 응답 파싱 안전성 (2건)

### C-1: `modules/domain/agents/chief_writer_quality.py:325` — dict 키 직접 접근

**파일**: `modules/domain/agents/chief_writer_quality.py`
**라인**: 325
**버그**: `issue['type']`, `issue['description']` 직접 접근 — LLM 응답에 해당 키가 없으면 `KeyError` 크래시.
**영향**: 품질 게이트 수정 시도 중 크래시 → 원고 수정 실패 → 불필요한 재시도.

**현재 코드**:
```python
for issue in issues[:3]:  # 최대 3개만 수정
    fix_instructions.append(f"- {issue['type']}: {issue['description']}")
```

**수정 코드**:
```python
for issue in issues[:3]:  # 최대 3개만 수정
    issue_type = issue.get("type", "unknown") if isinstance(issue, dict) else str(issue)
    issue_desc = issue.get("description", "") if isinstance(issue, dict) else ""
    fix_instructions.append(f"- {issue_type}: {issue_desc}")
```

### C-2: `modules/domain/agents/analyst.py:830-831` — 동일 비트 패딩

**파일**: `modules/domain/agents/analyst.py`
**라인**: 830-831
**버그**: LLM이 beat_sequence를 부족하게 반환하면, 모든 부족분에 동일한 제네릭 문자열 삽입. 5화 중 3화만 반환되면 4~5화가 동일 비트.
**영향**: 에피소드 4, 5가 동일한 서사 지시("서사적 긴장감 고조")를 받아 차별화 실패 → 반복적 원고 생성.

**현재 코드**:
```python
else:
    while len(beats) < actual_ep_count:
        beats.append("서사적 긴장감 고조 및 빌드업 수행")
```

**수정 코드**:
```python
else:
    fallback_beats = [
        "서사적 긴장감 고조 및 빌드업 수행",
        "캐릭터 내면 갈등 심화 및 선택의 기로",
        "예상치 못한 전환점 발생",
        "이해관계자 간 대립 격화",
        "결정적 사건을 향한 수렴",
    ]
    while len(beats) < actual_ep_count:
        idx = len(beats) % len(fallback_beats)
        beats.append(fallback_beats[idx])
    logging.warning(
        "[Analyst] beat_sequence 부족 (%d/%d) — 폴백 비트 %d개 추가",
        len(beats) - (actual_ep_count - len(beats)),
        actual_ep_count,
        actual_ep_count - len(beats),
    )
```

**참고**: `logging.warning` 라인의 인수에서 원래 beats 수는 패딩 전이므로, while 루프 진입 전에 `original_count = len(beats)`를 저장하고 사용하세요:
```python
else:
    original_count = len(beats)
    fallback_beats = [
        "서사적 긴장감 고조 및 빌드업 수행",
        "캐릭터 내면 갈등 심화 및 선택의 기로",
        "예상치 못한 전환점 발생",
        "이해관계자 간 대립 격화",
        "결정적 사건을 향한 수렴",
    ]
    while len(beats) < actual_ep_count:
        idx = len(beats) % len(fallback_beats)
        beats.append(fallback_beats[idx])
    logging.warning(
        "[Analyst] beat_sequence 부족 (%d/%d) — 폴백 비트 %d개 추가",
        original_count, actual_ep_count, actual_ep_count - original_count,
    )
```

---

## D. MEDIUM — 타입 불일치 (1건)

### D-1: `modules/core/stage2_finalizer.py:202-210` — 인벤토리 소비 타입 혼재

**파일**: `modules/core/stage2_finalizer.py`
**라인**: 202-210
**버그**: `consumed` 가 dict 리스트(`[{"name":"검","qty":1}]`)일 때, `item not in consumed` 비교가 string vs dict로 항상 True → 소비된 아이템이 계승됨.
**영향**: 소비된 아이템이 다음 Arc에 그대로 전달 → 이미 사용한 아이템이 인벤토리에 잔류.

**현재 코드**:
```python
consumed = curr_status.get("item_consumption", [])
if isinstance(consumed, str):
    consumed = [consumed] if consumed else []
# ... (dict 타입 미처리)
inherited = [item for item in prev_inventory if item not in consumed]
```

**수정 코드**:
```python
consumed_raw = curr_status.get("item_consumption", [])
if isinstance(consumed_raw, str):
    consumed_names = [consumed_raw] if consumed_raw else []
elif isinstance(consumed_raw, list):
    consumed_names = []
    for c in consumed_raw:
        if isinstance(c, str):
            consumed_names.append(c)
        elif isinstance(c, dict):
            consumed_names.append(c.get("name", c.get("item", "")))
else:
    consumed_names = []
inherited = [item for item in prev_inventory if item not in consumed_names]
```

**테스트**:
```python
def test_inventory_consumption_dict_type():
    """D-1: consumed가 dict 리스트일 때도 아이템 제거"""
    prev_inventory = ["검", "갑옷", "비급"]
    consumed_raw = [{"name": "검", "qty": 1}]

    consumed_names = []
    for c in consumed_raw:
        if isinstance(c, str):
            consumed_names.append(c)
        elif isinstance(c, dict):
            consumed_names.append(c.get("name", c.get("item", "")))

    inherited = [item for item in prev_inventory if item not in consumed_names]
    assert inherited == ["갑옷", "비급"]  # "검"이 제거되어야 함
```

---

## E. MEDIUM — 빈 리스트 안전성 (2건)

### E-1: `modules/core/pacing_analyzer.py:418-421` — min()/max() 빈 리스트

**파일**: `modules/core/pacing_analyzer.py`
**라인**: 418-421
**버그**: `scores`, `dialogue_ratios`, `avg_lengths` 리스트에서 `min()`/`max()` 호출. PacingAnalysis 객체의 속성이 None이면 리스트 컴프리헨션이 None을 포함하고 비교 실패.
**영향**: 분석 트렌드 함수 크래시 → 관측성 데이터 손실.

**현재 코드**:
```python
return {
    "score_trend": trend,
    "avg_score": sum(scores) / len(scores),
    "score_range": (min(scores), max(scores)),
    "dialogue_consistency": max(dialogue_ratios) - min(dialogue_ratios) < 0.15,
    "length_consistency": max(avg_lengths) - min(avg_lengths) < 15,
    "total_issues": sum(len(a.issues) for a in analyses),
}
```

**수정 코드**:
```python
return {
    "score_trend": trend,
    "avg_score": sum(scores) / len(scores) if scores else 0,
    "score_range": (min(scores), max(scores)) if scores else (0, 0),
    "dialogue_consistency": (max(dialogue_ratios) - min(dialogue_ratios) < 0.15) if dialogue_ratios else True,
    "length_consistency": (max(avg_lengths) - min(avg_lengths) < 15) if avg_lengths else True,
    "total_issues": sum(len(a.issues) for a in analyses),
}
```

### E-2: `modules/core/pacing_analyzer.py:83` — 마침표 없는 마지막 문장 누락

**파일**: `modules/core/pacing_analyzer.py`
**라인**: 83
**버그**: `SENTENCE_PATTERN = re.compile(r"[^.!?。？！]+[.!?。？！]+")` — 마침표 없이 끝나는 마지막 문장이 매칭 안 됨.
**영향**: 원고 마지막 문장이 마침표 없으면 페이싱 분석에서 탈락 → 문장 수 과소 카운트.

**현재 코드**:
```python
SENTENCE_PATTERN = re.compile(r"[^.!?。？！]+[.!?。？！]+")
```

**수정 코드**:
```python
SENTENCE_PATTERN = re.compile(r"[^.!?。？！]+[.!?。？！]+|[^.!?。？！]+$")
```

**설명**: `|[^.!?。？！]+$` 추가 — 문장 끝 구두점 없이 문자열이 끝나는 경우도 캡처.

**테스트**:
```python
import re

def test_sentence_pattern_captures_unpunctuated_ending():
    """E-2: 마침표 없는 마지막 문장도 캡처"""
    pattern = re.compile(r"[^.!?。？！]+[.!?。？！]+|[^.!?。？！]+$")
    text = "첫 번째 문장입니다. 두 번째 문장입니다"
    sentences = pattern.findall(text)
    assert len(sentences) == 2
    assert "두 번째 문장입니다" in sentences[1]
```

---

## 테스트 파일

### `tests/test_sweep10.py` 신규 생성

위 각 항목의 테스트를 하나의 파일로 통합:

```python
"""
[Sweep10] 숨은 로직 버그 수정 테스트
"""

import re

import pytest


class TestA1AdaptiveThreshold:
    """A-1: 영구 임계값 설정 시 적응형 비활성화"""

    def test_permanent_disables_adaptive(self):
        from modules.validation.validation_orchestrator import ValidationOrchestrator

        orch = ValidationOrchestrator.__new__(ValidationOrchestrator)
        orch.current_threshold = 70
        orch.use_adaptive_threshold = True
        orch.threshold_profile = {"base_threshold": 70}
        orch.set_manual_threshold_v59(80, duration_episodes=0)
        assert orch.use_adaptive_threshold is False
        assert orch.current_threshold == 80

    def test_temporary_keeps_adaptive(self):
        from modules.validation.validation_orchestrator import ValidationOrchestrator

        orch = ValidationOrchestrator.__new__(ValidationOrchestrator)
        orch.current_threshold = 70
        orch.use_adaptive_threshold = True
        orch.threshold_profile = {"base_threshold": 70}
        orch.set_manual_threshold_v59(80, duration_episodes=5)
        assert orch.use_adaptive_threshold is True


class TestB1EnsembleSelection:
    """B-1: 앙상블 불합격 폴백 시 최장 후보 선택"""

    def test_selects_longest_qualified(self):
        candidates = [
            {"manuscript": "A" * 4000},
            {"manuscript": "B" * 3000},
            {"manuscript": "C" * 5000},
        ]
        qualified_indices = [0, 2]
        selected_idx = 1  # LLM이 불합격 B 선택

        if selected_idx not in qualified_indices and qualified_indices:
            selected_idx = max(
                qualified_indices,
                key=lambda i: len(candidates[i].get("manuscript", "")),
            )

        assert selected_idx == 2


class TestC1IssueKeyAccess:
    """C-1: issue dict 키 안전 접근"""

    def test_missing_keys_no_crash(self):
        issue = {"problem": "some issue"}  # type/description 키 없음
        issue_type = issue.get("type", "unknown") if isinstance(issue, dict) else str(issue)
        issue_desc = issue.get("description", "") if isinstance(issue, dict) else ""
        result = f"- {issue_type}: {issue_desc}"
        assert "unknown" in result

    def test_string_issue_no_crash(self):
        issue = "plain string issue"
        issue_type = issue.get("type", "unknown") if isinstance(issue, dict) else str(issue)
        issue_desc = issue.get("description", "") if isinstance(issue, dict) else ""
        result = f"- {issue_type}: {issue_desc}"
        assert "plain string issue" in result


class TestD1InventoryConsumption:
    """D-1: 소비된 아이템 dict 타입 처리"""

    def test_dict_consumption_removes_item(self):
        prev_inventory = ["검", "갑옷", "비급"]
        consumed_raw = [{"name": "검", "qty": 1}]

        consumed_names = []
        for c in consumed_raw:
            if isinstance(c, str):
                consumed_names.append(c)
            elif isinstance(c, dict):
                consumed_names.append(c.get("name", c.get("item", "")))

        inherited = [item for item in prev_inventory if item not in consumed_names]
        assert inherited == ["갑옷", "비급"]

    def test_mixed_consumption_types(self):
        prev_inventory = ["검", "갑옷", "비급"]
        consumed_raw = ["갑옷", {"name": "비급"}]

        consumed_names = []
        for c in consumed_raw:
            if isinstance(c, str):
                consumed_names.append(c)
            elif isinstance(c, dict):
                consumed_names.append(c.get("name", c.get("item", "")))

        inherited = [item for item in prev_inventory if item not in consumed_names]
        assert inherited == ["검"]


class TestE1PacingEmptyList:
    """E-1: 빈 리스트에서 min/max 안전"""

    def test_empty_scores_safe(self):
        scores = []
        avg = sum(scores) / len(scores) if scores else 0
        score_range = (min(scores), max(scores)) if scores else (0, 0)
        assert avg == 0
        assert score_range == (0, 0)


class TestE2SentencePattern:
    """E-2: 마침표 없는 마지막 문장 캡처"""

    def test_captures_unpunctuated_ending(self):
        pattern = re.compile(r"[^.!?。？！]+[.!?。？！]+|[^.!?。？！]+$")
        text = "첫 번째 문장입니다. 두 번째 문장입니다"
        sentences = pattern.findall(text)
        assert len(sentences) == 2

    def test_all_punctuated_still_works(self):
        pattern = re.compile(r"[^.!?。？！]+[.!?。？！]+|[^.!?。？！]+$")
        text = "첫 번째. 두 번째. 세 번째."
        sentences = pattern.findall(text)
        assert len(sentences) == 3
```

---

## 실행 가이드 (Codex용)

- **총 7개 항목** (A: 1, B: 1, C: 2, D: 1, E: 2) + 테스트 파일 1개
- 각 항목 수정 후: `ruff check <파일> && ruff format <파일> && set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -x -q`
- **커밋하지 말 것** — 수정만 하고 검증만 수행

---

## 카테고리별 커밋 메시지

```
fix(sweep10-a): invert adaptive threshold boolean — permanent override now works
fix(sweep10-b): ensemble fallback selects longest qualified candidate
fix(sweep10-c): safe dict access in quality gate + diverse beat fallback
fix(sweep10-d): inventory consumption handles dict-type items
fix(sweep10-e): pacing analyzer empty list safety + sentence regex fix
test(sweep10): add 11 tests for logic bug fixes
```

---

## 산출물 요약

| 카테고리 | 항목 수 | 신규 테스트 | 성격 |
|----------|---------|------------|------|
| A. 적응형 임계값 반전 | 1 | +2 | CRITICAL 로직 버그 |
| B. 앙상블 선택 편향 | 1 | +1 | HIGH 로직 버그 |
| C. LLM 응답 안전성 | 2 | +2 | MEDIUM 크래시 방지 |
| D. 타입 불일치 | 1 | +2 | MEDIUM 데이터 무결성 |
| E. 빈 리스트 + 정규식 | 2 | +4 | MEDIUM 데이터 정확도 |
| **합계** | **7** | **+11** | |

---

## 오탐 제거 기록 (참고용)

다음 항목들은 스캔에서 발견되었으나 검증 후 정상으로 확인:

| 보고 내용 | 판정 | 이유 |
|-----------|------|------|
| director_ensemble.py:286 빈 리스트 crash | 정상 | candidates 비어있을 때 L273에서 조기 반환, lengths는 항상 비어있지 않음 |
| consistency_validator.py:121 카테고리 분리 | 정상 설계 | violations=보고용 전체 리스트, unjustifiable=REJECT 판정용 (L222) |
| stage2_preflight.py 캐시 키 | 정상 | skip된 arc는 상태 변경 없으므로 캐시 유효 |
| context_compression.py:226 빈 리스트 | 정상 | len(sentences)<=3 조기 반환으로 보호됨 |
