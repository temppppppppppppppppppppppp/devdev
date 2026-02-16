# Codex Order: B-1-4 — ChiefWriter Context Builder 추출

> OPUS TF 감리 지시서
> 기준 커밋: `7242d4a` (B-1-3 완료)
> 대상 파일: `modules/domain/agents/chief_writer.py` (2,255줄)

---

## 1. 목표

`chief_writer.py`에서 **컨텍스트 빌딩 + 분석 메서드 19개** (~1,020줄)를
`modules/domain/agents/chief_writer_context.py`로 추출한다.

V64 위임 패턴: `ChiefWriter → ChiefWriterContextBuilder(host)` lazy init.

---

## 2. 추출 대상 메서드 (19개)

### 2-A. 메인 컨텍스트 빌더 (1개, ~289줄)

| # | 메서드 | 라인 | 역할 |
|---|--------|------|------|
| 1 | `_build_common_context` | L486-774 | **GOD METHOD** — 전체 프롬프트 조립, 16+ 서브메서드 호출 |

### 2-B. 원고 분석/다이제스트 (5개, ~333줄)

| # | 메서드 | 라인 | 역할 |
|---|--------|------|------|
| 2 | `_generate_episode_digest` | L778-933 | 이전 에피소드 regex 상태 다이제스트 (NO LLM) |
| 3 | `_detect_deaths_from_manuscript` | L934-957 | 사망 NPC 감지 (regex) |
| 4 | `_detect_past_events_from_manuscript` | L959-996 | 과거 사건 감지 (regex) |
| 5 | `_build_past_guard_section` | L998-1038 | 과거 침범 방지 가드 |
| 6 | `_build_future_guard_section` | L1040-1114 | 미래 침범 방지 가드 |

### 2-C. HUD/상태 분석 (4개, ~133줄)

| # | 메서드 | 라인 | 역할 |
|---|--------|------|------|
| 7 | `_get_hud_trend_safe` | L1899-1901 | HUD 추세 위임 (3줄) |
| 8 | `_extract_numeric_value` | L1903-1913 | 숫자 추출 유틸 |
| 9 | `_build_hud_context` | L1915-1917 | HUD 컨텍스트 위임 (3줄) |
| 10 | `_check_hud_anomalies` | L1919-2034 | HUD 급변 감지 (내공/경지/부상) |

### 2-D. NPC/데이터 추출 (4개, ~108줄)

| # | 메서드 | 라인 | 역할 |
|---|--------|------|------|
| 11 | `_get_npc_equipment_summary` | L2036-2063 | NPC 장비 현황 추출 |
| 12 | `_get_npc_frequency` | L1799-1832 | NPC 등장 빈도 추적 |
| 13 | `_get_npc_frequency_warning` | L1834-1860 | NPC 빈도 경고 메시지 생성 |
| 14 | `_get_dna_instruction` | L2069-2087 | DNA 모드 지시문 (1화 특수) |

### 2-E. 강제 맥락 주입 (5개, ~174줄)

| # | 메서드 | 라인 | 역할 |
|---|--------|------|------|
| 15 | `_build_anti_trope_instructions` | L2093-2100 | 반클리셰 지시 |
| 16 | `_build_mandatory_context` | L2102-2141 | 강제 맥락 주입 (HUD급변+최근사건+NPC상태) |
| 17 | `_extract_recent_events` | L2143-2172 | 최근 N화 핵심 사건 추출 |
| 18 | `_extract_npc_last_states` | L2174-2200 | NPC 마지막 관계 상태 |
| 19 | `_build_justification_guidance` | L2202-2250 | 정당화 패턴 가이드 |

---

## 3. Facade에 남는 메서드

### 3-A. 공개 진입점 (3개)

| 메서드 | 라인 | 변경 |
|--------|------|------|
| `generate_ensemble` | L117-357 | L185: `self._build_common_context(...)` → `self._context_builder.build_common_context(...)` |
| `regenerate_with_feedback` | L1116-1228 | 변경 없음 (generate_ensemble 호출) |
| `patch_with_feedback` | L1234-1341 | 변경 없음 (generate_ensemble 호출) |

### 3-B. 생성 파이프라인 (1개)

| 메서드 | 라인 | 변경 |
|--------|------|------|
| `_generate_single_candidate` | L359-484 | 변경 없음 |

### 3-C. Self-Critique 파이프라인 (9개, B-1-5 대상)

| 메서드 | 라인 |
|--------|------|
| `_sanitize_leakage` | L1347-1392 |
| `_apply_self_critique` | L1394-1447 |
| `_self_critique` | L1449-1497 |
| `_check_hud_consistency` | L1498-1523 |
| `_check_cliche_overuse` | L1524-1570 |
| `_check_justification_gaps` | L1571-1602 |
| `_check_npc_relationship` | L1603-1637 |
| `_fix_manuscript_issues` | L1639-1672 |
| `_evaluate_with_rubric` | L1674-1757 |

### 3-D. 캐시/유틸 (3개)

| 메서드 | 라인 | 비고 |
|--------|------|------|
| `_prefetch_manuscripts` | L1763-1789 | 캐시 빌드 (instance state) |
| `_get_cached_manuscript` | L1791-1793 | 캐시 조회 |
| `_count_recent_cliches` | L1862-1897 | 클리셰 빈도 (quality pipeline에서 사용) |

---

## 4. 신규 파일 구조

```python
# modules/domain/agents/chief_writer_context.py
"""
[B-1-4] ChiefWriter Context Builder — 원고 생성 컨텍스트 조립
V64 위임 패턴: ChiefWriter facade에서 lazy init으로 사용
"""

import json
import logging
import re

from modules.core.hud_utils import build_hud_context as _build_hud_context_shared
from modules.core.hud_utils import get_hud_trend_safe as _get_hud_trend_safe_shared

try:
    from modules.core.primitive_guard import get_primitive_constraint_section
    PRIMITIVE_GUARD_AVAILABLE = True
except ImportError:
    PRIMITIVE_GUARD_AVAILABLE = False

from .chief_writer_prompts import (
    build_chief_writer_main_prompt,
    get_anti_trope_instructions,
    get_common_rules_section,
    get_modern_origin_section,
    get_primitive_constraint_fallback,
    get_writing_guidelines_section,
)


class ChiefWriterContextBuilder:
    """
    ChiefWriter의 컨텍스트 빌딩 + 분석 담당 서브모듈.

    host(ChiefWriter) 참조를 통해:
    - self.host._escape_braces()   — BaseAgent 문자열 유틸
    - self.host._get_cached_manuscript()  — 원고 캐시 조회
    - self.host.context  — 프로젝트 컨텍스트 (DB, bible)
    """

    def __init__(self, host: "ChiefWriter"):
        self.host = host

    @property
    def context(self):
        """host의 프로젝트 컨텍스트 위임"""
        return self.host.context

    # ── 공개 메서드 ──
    def build_common_context(self, ...) -> str:
        """기존 _build_common_context 이전 — 시그니처 동일"""
        ...

    # ── 이하 19개 비공개 메서드 (기존 코드 그대로 이전) ──
```

---

## 5. Facade 변경 (`chief_writer.py`)

### 5-A. import 추가

```python
# chief_writer.py 상단 (기존 import 블록 뒤)
from .chief_writer_context import ChiefWriterContextBuilder
```

### 5-B. import 제거 (context builder로 이전)

```python
# 다음 import들은 chief_writer.py에서 삭제 (context builder로 이전됨):
# from modules.core.hud_utils import build_hud_context as _build_hud_context_shared
# from modules.core.hud_utils import get_hud_trend_safe as _get_hud_trend_safe_shared
# primitive_guard try/except 블록 전체
# from .chief_writer_prompts 에서: build_chief_writer_main_prompt, get_anti_trope_instructions,
#     get_common_rules_section, get_modern_origin_section,
#     get_primitive_constraint_fallback, get_writing_guidelines_section
```

facade에 남길 import:
```python
from .chief_writer_prompts import (
    get_fix_issues_prompt,
    get_prompt_template_output,
)
```

### 5-C. `__init__` 변경

```python
def __init__(self, context, client, model_tier=None) -> None:
    super().__init__(context, client, model_tier)
    self._agent_name = "ChiefWriter"
    self._manuscript_cache = {}
    self._cache_ep_num = -1
    self._context_builder = None  # ← 추가 (lazy init)
```

### 5-D. lazy property 추가

```python
@property
def context_builder(self) -> "ChiefWriterContextBuilder":
    if self._context_builder is None:
        from .chief_writer_context import ChiefWriterContextBuilder
        self._context_builder = ChiefWriterContextBuilder(self)
    return self._context_builder
```

### 5-E. 호출부 변경 (1곳)

```python
# generate_ensemble() 내부, L185
# BEFORE:
common_context = self._build_common_context(
    ep_num=ep_num,
    ...
)

# AFTER:
common_context = self.context_builder.build_common_context(
    ep_num=ep_num,
    ...
)
```

---

## 6. 의존성 그래프 (cross-module)

```
ChiefWriter (facade)
  ├── context_builder: ChiefWriterContextBuilder(self)
  │     ├── self.host._escape_braces()      ← BaseAgent
  │     ├── self.host._get_cached_manuscript() ← 캐시 (facade)
  │     └── self.host.context               ← 프로젝트 컨텍스트
  │
  ├── _prefetch_manuscripts()  ← 캐시 빌드 (facade)
  ├── _get_cached_manuscript() ← 캐시 조회 (facade)
  ├── _count_recent_cliches()  ← 클리셰 카운트 (facade, quality용)
  │
  └── [B-1-5 예정] _sanitize_leakage, _apply_self_critique, ...
```

### Context Builder 내부 호출 경로 (self 참조 변환)

| 기존 (`chief_writer.py`) | 변환 후 (`chief_writer_context.py`) |
|--------------------------|-------------------------------------|
| `self._escape_braces(x)` | `self.host._escape_braces(x)` |
| `self._get_cached_manuscript(ep)` | `self.host._get_cached_manuscript(ep)` |
| `self.context.db.xxx()` | `self.context.db.xxx()` (property 위임) |
| `self.context.master_bible` | `self.context.master_bible` (property 위임) |
| `self._generate_episode_digest(...)` | `self._generate_episode_digest(...)` (같은 클래스 내) |
| `self._check_hud_anomalies(...)` | `self._check_hud_anomalies(...)` (같은 클래스 내) |
| `self._get_npc_frequency_warning(...)` | `self._get_npc_frequency_warning(...)` (같은 클래스 내) |

**핵심**: 19개 메서드가 모두 같은 클래스로 이동하므로, 메서드 간 `self.xxx()` 호출은 변경 불필요.
변경이 필요한 것은 **facade 의존** 2개뿐:
1. `self._escape_braces()` → `self.host._escape_braces()`
2. `self._get_cached_manuscript()` → `self.host._get_cached_manuscript()`

---

## 7. 테스트 파일

`tests/test_chief_writer_context.py` (신규, ~200줄)

최소 검증 항목:

| # | 테스트 | 검증 |
|---|--------|------|
| 1 | `test_context_builder_init` | host 참조, context property |
| 2 | `test_build_common_context_returns_string` | 반환 타입 str, 비어있지 않음 |
| 3 | `test_generate_episode_digest_empty` | 빈/짧은 원고 → 빈 문자열 |
| 4 | `test_generate_episode_digest_extracts_names` | regex NPC 이름 추출 |
| 5 | `test_detect_deaths_from_manuscript` | 사망 키워드 감지 |
| 6 | `test_detect_past_events` | 과거 사건 키워드 감지 |
| 7 | `test_build_past_guard_section` | 가드 섹션 포맷 |
| 8 | `test_build_future_guard_section` | 인벤토리/무공/사망NPC 가드 |
| 9 | `test_check_hud_anomalies_no_data` | 데이터 없음 → has_anomalies=False |
| 10 | `test_check_hud_anomalies_energy_spike` | 내공 급상승 감지 |
| 11 | `test_check_hud_anomalies_realm_jump` | 경지 급상승 감지 |
| 12 | `test_get_npc_frequency` | NPC 빈도 카운트 |
| 13 | `test_get_npc_frequency_warning` | 미등장/과등장 경고 |
| 14 | `test_build_mandatory_context` | 강제 맥락 포맷 |
| 15 | `test_extract_recent_events` | DB에서 이벤트 추출 |
| 16 | `test_build_justification_guidance_physical` | 신체 제약 감지 |
| 17 | `test_build_justification_guidance_none` | 제약 없음 → 빈 문자열 |
| 18 | `test_get_dna_instruction_ep1` | 1화 DNA 모드 |
| 19 | `test_get_dna_instruction_ep5` | 일반 연속 모드 |
| 20 | `test_build_anti_trope_instructions` | 장르별 반클리셰 |

Mock 전략:
- `host` = MagicMock(spec=ChiefWriter)
- `host._escape_braces` = lambda x: str(x).replace("{", "{{").replace("}", "}}")
- `host._get_cached_manuscript` = lambda ep: {"content": "...", "hud_snapshot": {}}
- `host.context.db` = MagicMock()
- `host.context.master_bible` = fixture bible dict

---

## 8. 수정 금지

- `chief_writer_prompts.py` — 변경 없음
- `base_agent.py` — 변경 없음
- `stage4_orchestrator.py` — 변경 없음
- `stage4_interview_round.py` — 변경 없음 (ChiefWriter 공개 API 불변)
- `hud_utils.py` — 변경 없음

---

## 9. 검증 게이트

```bash
# Gate 1: 신규 파일 컴파일
python -m py_compile modules/domain/agents/chief_writer_context.py
python -m py_compile tests/test_chief_writer_context.py

# Gate 2: ChiefWriter import 불변
python -c "from modules.domain.agents.chief_writer import ChiefWriter; print('OK')"

# Gate 3: SovereignApp import 불변
python -c "from main_a import SovereignApp; print('OK')"

# Gate 4: 신규 테스트
set PYTHONIOENCODING=utf-8
pytest tests/test_chief_writer_context.py -v

# Gate 5: 기존 회귀
pytest tests/test_stage4_orchestrator.py tests/test_stage4_interview_round.py tests/test_stage4_post_processor.py tests/test_stage4_context_builder.py -v

# Gate 6: pre-commit
pre-commit run --files modules/domain/agents/chief_writer_context.py modules/domain/agents/chief_writer.py tests/test_chief_writer_context.py
```

---

## 10. 커밋 메시지

```
refactor(chief-writer): extract context builder to sub-module (B-1-4)

- Move 19 context-building/analysis methods (~1,020 lines) to
  ChiefWriterContextBuilder in chief_writer_context.py
- V64 delegation: lazy init property, host reference pattern
- No change to ChiefWriter public API (generate_ensemble/
  regenerate_with_feedback/patch_with_feedback)
- Add 20 unit tests for extracted methods
- chief_writer.py: 2,255 → ~1,250 lines (-44%)
```

---

## 11. 예상 결과

| 파일 | Before | After |
|------|--------|-------|
| `chief_writer.py` | 2,255줄 | ~1,250줄 (-44%) |
| `chief_writer_context.py` | — | ~1,020줄 (신규) |
| `test_chief_writer_context.py` | — | ~200줄 (신규) |

| 지표 | Before | After |
|------|--------|-------|
| `self.app` in context builder | 0 | 0 |
| `self.host` 참조 | — | 2종 (escape_braces, get_cached_manuscript) |
| ChiefWriter 공개 API | 3 메서드 | 불변 |
| 기존 테스트 | 454 passed | 불변 |
