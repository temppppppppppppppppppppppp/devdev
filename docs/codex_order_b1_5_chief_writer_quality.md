# Codex Order: B-1-5 — ChiefWriter Quality Gate 추출

> OPUS TF 감리 지시서
> 기준 커밋: `1e8db62` (B-1-4 완료)
> 대상 파일: `modules/domain/agents/chief_writer.py` (1,267줄)

---

## 1. 목표

`chief_writer.py`에서 **Self-Critique + 품질 검증 파이프라인 10개 메서드** (~439줄)를
`modules/domain/agents/chief_writer_quality.py`로 추출한다.

V64 위임 패턴: `ChiefWriter → ChiefWriterQualityGate(host)` lazy init.

---

## 2. 추출 대상 메서드 (10개)

### 2-A. 출력 정제 (1개, ~46줄)

| # | 메서드 | 라인 | 역할 |
|---|--------|------|------|
| 1 | `_sanitize_leakage` | L728-773 | 미래 씬 누수 방지, 금지키 제거, 영문 괄호 병기 제거 |

### 2-B. Self-Critique 오케스트레이터 (2개, ~102줄)

| # | 메서드 | 라인 | 역할 |
|---|--------|------|------|
| 2 | `_apply_self_critique` | L775-828 | 다중 라운드 Self-Critique 루프 (최대 3회) |
| 3 | `_self_critique` | L830-877 | 단일 라운드 — 4개 체커 호출 |

### 2-C. 개별 체커 (4개, ~137줄)

| # | 메서드 | 라인 | 역할 |
|---|--------|------|------|
| 4 | `_check_hud_consistency` | L879-903 | HUD 모순 감지 (regex) |
| 5 | `_check_cliche_overuse` | L905-950 | 클리셰 과용 감지 (regex + DB) |
| 6 | `_check_justification_gaps` | L952-982 | 정당화 누락 감지 (regex) |
| 7 | `_check_npc_relationship` | L984-1018 | NPC 관계 일관성 감지 (regex + dict) |

### 2-D. 수정 + 평가 (2개, ~118줄)

| # | 메서드 | 라인 | 역할 |
|---|--------|------|------|
| 8 | `_fix_manuscript_issues` | L1020-1053 | LLM 호출로 문제 수정 (유일한 LLM 사용) |
| 9 | `_evaluate_with_rubric` | L1055-1138 | Rubric 기반 품질 점수 (1.0~4.0, NO LLM) |

### 2-E. 클리셰 카운트 (1개, ~36줄)

| # | 메서드 | 라인 | 역할 |
|---|--------|------|------|
| 10 | `_count_recent_cliches` | L1186-1221 | 최근 N화 클리셰 빈도 (캐시 사용) |

---

## 3. Facade에 남는 메서드

### 3-A. 공개 진입점 (3개, 변경 없음)

| 메서드 | 비고 |
|--------|------|
| `generate_ensemble` | 변경 없음 |
| `regenerate_with_feedback` | 변경 없음 |
| `patch_with_feedback` | 변경 없음 |

### 3-B. 생성 파이프라인 (1개, 호출부 2곳 변경)

| 메서드 | 변경 |
|--------|------|
| `_generate_single_candidate` | L413: `self._sanitize_leakage(...)` → `self.quality_gate.sanitize_leakage(...)` |
| | L437: `self._apply_self_critique(...)` → `self.quality_gate.apply_self_critique(...)` |

### 3-C. 캐시 (2개, 변경 없음)

| 메서드 | 비고 |
|--------|------|
| `_prefetch_manuscripts` | facade에 유지 (instance state) |
| `_get_cached_manuscript` | facade에 유지 (quality gate에서 host 참조) |

### 3-D. B-1-4 thin wrappers (17개, 변경 없음)

context_builder 위임 래퍼들 — 그대로 유지.

---

## 4. 신규 파일 구조

```python
# modules/domain/agents/chief_writer_quality.py
"""
[B-1-5] ChiefWriter Quality Gate — Self-Critique + 품질 검증 파이프라인
V64 위임 패턴: ChiefWriter facade에서 lazy init으로 사용
"""

import json
import logging
import re

from .chief_writer_prompts import get_fix_issues_prompt


class ChiefWriterQualityGate:
    """
    ChiefWriter의 Self-Critique + 품질 검증 담당 서브모듈.

    host(ChiefWriter) 참조를 통해:
    - self.host.ask()              — BaseAgent LLM 호출
    - self.host._escape_braces()   — BaseAgent 문자열 유틸
    - self.host._get_cached_manuscript()  — 원고 캐시 조회
    """

    def __init__(self, host: "ChiefWriter"):
        self.host = host

    # ── 공개 메서드 ──
    def sanitize_leakage(self, text: str) -> str:
        """기존 _sanitize_leakage 이전"""
        ...

    def apply_self_critique(
        self, manuscript: str, hud_report: str, npcs: list,
        genre_name: str, ep_num: int = None,
    ) -> str:
        """기존 _apply_self_critique 이전"""
        ...

    # ── 이하 8개 비공개 메서드 (기존 코드 그대로 이전) ──
```

---

## 5. Facade 변경 (`chief_writer.py`)

### 5-A. import 추가

```python
# chief_writer.py 상단 import 블록
from .chief_writer_quality import ChiefWriterQualityGate
```

### 5-B. import 제거

```python
# get_fix_issues_prompt → quality gate로 이전
# 변경 전:
from .chief_writer_prompts import (
    get_fix_issues_prompt,
    get_prompt_template_output,
)

# 변경 후:
from .chief_writer_prompts import get_prompt_template_output
```

### 5-C. `__init__` 변경

```python
def __init__(self, context, client, model_tier=None) -> None:
    super().__init__(context, client, model_tier)
    self._agent_name = "ChiefWriter"
    self._manuscript_cache = {}
    self._cache_ep_num = -1
    self._context_builder = None
    self._quality_gate = None   # ← 추가
```

### 5-D. lazy property 추가

```python
@property
def quality_gate(self) -> "ChiefWriterQualityGate":
    if self._quality_gate is None:
        from .chief_writer_quality import ChiefWriterQualityGate
        self._quality_gate = ChiefWriterQualityGate(self)
    return self._quality_gate
```

### 5-E. 호출부 변경 (`_generate_single_candidate` 내부, 2곳)

```python
# BEFORE (L413):
response = self._sanitize_leakage(response)

# AFTER:
response = self.quality_gate.sanitize_leakage(response)

# BEFORE (L437-438):
critiqued_manuscript = self._apply_self_critique(
    manuscript=manuscript_json, hud_report=hud_report,
    npcs=npcs, genre_name=genre_name, ep_num=ep_num
)

# AFTER:
critiqued_manuscript = self.quality_gate.apply_self_critique(
    manuscript=manuscript_json, hud_report=hud_report,
    npcs=npcs, genre_name=genre_name, ep_num=ep_num
)
```

### 5-F. thin wrappers (기존 테스트 호환)

```python
# B-1-4 패턴과 동일 — 기존 테스트가 self._sanitize_leakage() 등을 호출할 수 있으므로
def _sanitize_leakage(self, *args, **kwargs):
    return self.quality_gate.sanitize_leakage(*args, **kwargs)

def _apply_self_critique(self, *args, **kwargs):
    return self.quality_gate.apply_self_critique(*args, **kwargs)

def _self_critique(self, *args, **kwargs):
    return self.quality_gate._self_critique(*args, **kwargs)

# ... 나머지 7개도 동일 패턴
```

---

## 6. 의존성 그래프 (cross-module)

```
ChiefWriter (facade)
  ├── context_builder: ChiefWriterContextBuilder(self)    [B-1-4]
  │
  ├── quality_gate: ChiefWriterQualityGate(self)          [B-1-5 ← 신규]
  │     ├── self.host.ask(prompt, temperature, thinking_level) ← BaseAgent LLM
  │     ├── self.host._escape_braces(text)                     ← BaseAgent util
  │     └── self.host._get_cached_manuscript(ep)               ← 캐시 (facade)
  │
  ├── _prefetch_manuscripts()     ← 캐시 빌드 (facade)
  └── _get_cached_manuscript()    ← 캐시 조회 (facade)
```

### Quality Gate 내부 호출 경로 (self 참조 변환)

| 기존 (`chief_writer.py`) | 변환 후 (`chief_writer_quality.py`) |
|--------------------------|-------------------------------------|
| `self.ask(prompt, ...)` | `self.host.ask(prompt, ...)` |
| `self._escape_braces(x)` | `self.host._escape_braces(x)` |
| `self._get_cached_manuscript(ep)` | `self.host._get_cached_manuscript(ep)` |
| `self._sanitize_leakage(text)` | `self.sanitize_leakage(text)` (같은 클래스 내, 언더스코어 제거) |
| `self._evaluate_with_rubric(m, g)` | `self._evaluate_with_rubric(m, g)` (같은 클래스 내) |
| `self._self_critique(...)` | `self._self_critique(...)` (같은 클래스 내) |
| `self._fix_manuscript_issues(...)` | `self._fix_manuscript_issues(...)` (같은 클래스 내) |
| `self._count_recent_cliches(...)` | `self._count_recent_cliches(...)` (같은 클래스 내) |

**핵심**: 10개 메서드가 모두 같은 클래스로 이동하므로, 메서드 간 `self.xxx()` 호출은 대부분 변경 불필요.
변경이 필요한 것은 **host 의존** 3개뿐:
1. `self.ask(...)` → `self.host.ask(...)`
2. `self._escape_braces(...)` → `self.host._escape_braces(...)`
3. `self._get_cached_manuscript(...)` → `self.host._get_cached_manuscript(...)`

**주의**: `_fix_manuscript_issues` 내부에서 `self._sanitize_leakage(fixed)` 호출 — 이것은 같은 클래스 내이므로 `self.sanitize_leakage(fixed)`로 변경 (public name).

---

## 7. 테스트 파일

`tests/test_chief_writer_quality.py` (신규, ~200줄)

최소 검증 항목:

| # | 테스트 | 검증 |
|---|--------|------|
| 1 | `test_quality_gate_init` | host 참조 |
| 2 | `test_sanitize_leakage_empty` | 빈 입력 → 빈 반환 |
| 3 | `test_sanitize_leakage_removes_banned_keys` | Beat 3, future_hint 등 제거 |
| 4 | `test_sanitize_leakage_removes_english_parentheses` | 영문 괄호 병기 제거 |
| 5 | `test_apply_self_critique_high_rubric_skip` | rubric >= 3.5 → 스킵 |
| 6 | `test_apply_self_critique_low_rubric_runs` | rubric < 3.5 → 체크 실행 |
| 7 | `test_self_critique_no_issues` | 이슈 없음 → has_issues=False |
| 8 | `test_check_hud_consistency` | HUD 모순 감지 |
| 9 | `test_check_cliche_overuse` | 무협 클리셰 감지 |
| 10 | `test_check_cliche_overuse_recent` | 최근 빈도 기반 감지 |
| 11 | `test_check_justification_gaps` | 정당화 누락 감지 |
| 12 | `test_check_npc_relationship` | NPC 관계 불일치 감지 |
| 13 | `test_fix_manuscript_issues_calls_llm` | host.ask() 호출 확인 |
| 14 | `test_fix_manuscript_issues_fallback` | LLM 실패 시 원본 반환 |
| 15 | `test_evaluate_with_rubric_short` | 100자 미만 → 1.0 |
| 16 | `test_evaluate_with_rubric_good` | 양질 원고 → 3.0+ |
| 17 | `test_count_recent_cliches` | 캐시 기반 빈도 카운트 |
| 18 | `test_count_recent_cliches_empty_cache` | 캐시 없음 → 빈 dict |

Mock 전략:
- `host` = MagicMock(spec=ChiefWriter)
- `host.ask` = MagicMock(return_value='{"content":"fixed"}')
- `host._escape_braces` = lambda x: str(x).replace("{", "{{").replace("}", "}}")
- `host._get_cached_manuscript` = lambda ep: {"content": "...", "hud_snapshot": {}}

---

## 8. 수정 금지

- `chief_writer_context.py` — 변경 없음
- `chief_writer_prompts.py` — 변경 없음
- `base_agent.py` — 변경 없음
- `stage4_orchestrator.py` — 변경 없음
- `stage4_interview_round.py` — 변경 없음

---

## 9. 검증 게이트

```bash
# Gate 1: 신규 파일 컴파일
python -m py_compile modules/domain/agents/chief_writer_quality.py
python -m py_compile tests/test_chief_writer_quality.py

# Gate 2: ChiefWriter import 불변
python -c "from modules.domain.agents.chief_writer import ChiefWriter; print('OK')"

# Gate 3: SovereignApp import 불변
python -c "from main_a import SovereignApp; print('OK')"

# Gate 4: 신규 테스트
set PYTHONIOENCODING=utf-8
pytest tests/test_chief_writer_quality.py -v

# Gate 5: 기존 회귀 (chief_writer + context_builder + stage4)
pytest tests/test_chief_writer.py tests/test_chief_writer_context.py tests/test_stage4_orchestrator.py tests/test_stage4_interview_round.py -v

# Gate 6: pre-commit
pre-commit run --files modules/domain/agents/chief_writer_quality.py modules/domain/agents/chief_writer.py tests/test_chief_writer_quality.py
```

---

## 10. 커밋 메시지

```
refactor(chief-writer): extract quality gate to sub-module (B-1-5)

- Move 10 self-critique/quality methods (~439 lines) to
  ChiefWriterQualityGate in chief_writer_quality.py
- V64 delegation: lazy init property, host reference pattern
- No change to ChiefWriter public API
- Add 18 unit tests for extracted methods
- chief_writer.py: 1,267 → ~850 lines (-33%)
```

---

## 11. 예상 결과

| 파일 | Before | After |
|------|--------|-------|
| `chief_writer.py` | 1,267줄 | ~850줄 (-33%) |
| `chief_writer_quality.py` | — | ~460줄 (신규) |
| `test_chief_writer_quality.py` | — | ~200줄 (신규) |

| 지표 | Before | After |
|------|--------|-------|
| ChiefWriter 서브모듈 | 1개 (context) | 2개 (context + quality) |
| host 의존 | — | 3종 (ask, escape_braces, get_cached_manuscript) |
| ChiefWriter 공개 API | 3 메서드 | 불변 |
| 기존 테스트 | 481 passed | 불변 |

---

## 12. B-1 모놀리스 분할 최종 진행표

| 단계 | 대상 | 서브모듈 | 줄 수 | 상태 |
|------|------|---------|------|------|
| B-1-1 | stage4 | PostProcessor | 543 | ✅ |
| B-1-2 | stage4 | ContextBuilder | 570 | ✅ |
| B-1-3 | stage4 | InterviewRound | 554 | ✅ |
| B-1-4 | chief_writer | ContextBuilder | 1,074 | ✅ |
| **B-1-5** | **chief_writer** | **QualityGate** | **~460** | **← 현재** |

B-1-5 완료 시: stage4 + chief_writer 모놀리스 분할 **전체 완료**.
