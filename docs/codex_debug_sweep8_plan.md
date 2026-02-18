# Debug Sweep 8차 — 상수 통합 + 미사용 코드 정리

> **목적**: 하드코딩 매직넘버 → 중앙 상수 참조 통합, 미사용 import 제거, async 안전성
> **규칙**: 각 항목은 독립 실행 가능 (의존성 없음, 단 B는 B-0 먼저). 수정 후 반드시 `set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q` 통과 확인.
> **테스트 기준선**: 1,730 passed + 68 xfailed (Sweep 7 적용 후 변동 가능 — 실행 전 확인)
> **Ruff**: 수정한 파일에 `ruff check <파일> && ruff format <파일>` 적용
> **커밋하지 말 것** — 수정만 하고 검증만 수행

### ⚠️ CRITICAL: Encoding Safety Rules

**All source files are UTF-8 encoded with Korean comments and string literals.**

1. **NEVER re-write entire files.** Only modify the specific lines described in each item.
2. When reading files, always use `encoding='utf-8'`.
3. When writing files, always use `encoding='utf-8'` and write back only the changed content.
4. **Do NOT use `open()` without explicit `encoding='utf-8'`** — the default system encoding may corrupt Korean characters.
5. Prefer targeted line-level edits over full-file rewrites.
6. After each file modification, verify Korean text is intact.

---

## A. ManuscriptLimits 상수 참조 통합 (21건, 13파일)

> `modules/core/constants.py`에 이미 정의된 `ManuscriptLimits` (MIN=4000, WARNING=4500, TARGET=5000, MAX=15000)를 하드코딩 대신 import하여 사용.

**각 파일에 공통 작업**:
```python
# 파일 상단 import 영역에 추가:
from modules.core.constants import ManuscriptLimits
```

### A-1: `main_a.py:356,362,365,619`

**L356**: `if content_length < 4000:` → `if content_length < ManuscriptLimits.MIN_LENGTH:`
**L362**: `f"최소 {4000 - content_length}자 추가 필요..."` → `f"최소 {ManuscriptLimits.MIN_LENGTH - content_length}자 추가 필요..."`
**L365**: `elif content_length < 4500:` → `elif content_length < ManuscriptLimits.WARNING_LENGTH:`
**L619**: `target_len: int = 5000,` → `target_len: int = ManuscriptLimits.TARGET_LENGTH,`

---

### A-2: `modules/core/confidence_calibration.py:148,150,153`

**L148**: `if 5000 <= length <= 12000:` → `if ManuscriptLimits.TARGET_LENGTH <= length <= 12000:`
**L150**: `elif 4000 <= length < 5000 or 12000 < length <= 15000:` → `elif ManuscriptLimits.MIN_LENGTH <= length < ManuscriptLimits.TARGET_LENGTH or 12000 < length <= ManuscriptLimits.MAX_LENGTH:`
**L153**: `elif 3000 <= length < 4000:` → `elif 3000 <= length < ManuscriptLimits.MIN_LENGTH:`

---

### A-3: `modules/core/quality_dashboard.py:588,591,593,596`

**L588**: `if length < 4000:` → `if length < ManuscriptLimits.MIN_LENGTH:`
**L591**: `"impact": f"{length}자 (최소 4000자)"` → `"impact": f"{length}자 (최소 {ManuscriptLimits.MIN_LENGTH}자)"`
**L593**: `elif length < 4500:` → `elif length < ManuscriptLimits.WARNING_LENGTH:`
**L596**: `elif 4500 <= length <= 8000:` → `elif ManuscriptLimits.WARNING_LENGTH <= length <= 8000:`

---

### A-4: `modules/domain/agents/director.py:141,198`

**L141**: `target_len=4500,` → `target_len=ManuscriptLimits.WARNING_LENGTH,`
**L198**: `def _audit_with_v0128(..., target_len=4500):` → `target_len=ManuscriptLimits.WARNING_LENGTH`

---

### A-5: `modules/domain/agents/director_auditor.py:171,177,324`

**L171**: `def _audit_with_v0128(..., target_len=4500):` → `target_len=ManuscriptLimits.WARNING_LENGTH`
**L177**: `mode = "BLUEPRINT" if target_len <= 4000 else "MANUSCRIPT"` → `target_len <= ManuscriptLimits.MIN_LENGTH`
**L324**: `target_len=4500,` → `target_len=ManuscriptLimits.WARNING_LENGTH,`

---

### A-6: `modules/core/prompt_builder.py:120,448`

**L120**: `def generate_high_impact_zone_guide(..., target_len: int = 5000) -> str:` → `target_len: int = ManuscriptLimits.TARGET_LENGTH`
**L448**: `target_len: int = 5000,` → `target_len: int = ManuscriptLimits.TARGET_LENGTH,`

---

### A-7: `modules/core/ab_testing.py:72`

**L72**: `target_len=5000,` → `target_len=ManuscriptLimits.TARGET_LENGTH,`

---

### A-8: `modules/core/config_manager.py:42`

**L42**: `"target_manuscript_length": 5000,` → `"target_manuscript_length": ManuscriptLimits.TARGET_LENGTH,`

---

### A-9: `modules/core/writer_template.py:176`

**L176**: `total_min_chars=max(4000, total_min),` → `total_min_chars=max(ManuscriptLimits.MIN_LENGTH, total_min),`

---

### A-10: `modules/core/feedback_system.py:723,730,737`

**L723**: `"guidance": "5000자 이상, 균형 잡힌 씬 분배를 목표로."` → `"guidance": f"{ManuscriptLimits.TARGET_LENGTH}자 이상, 균형 잡힌 씬 분배를 목표로."`
**L730**: `"guidance": "4500자 이상, 핵심 씬 반영에 집중."` → `"guidance": f"{ManuscriptLimits.WARNING_LENGTH}자 이상, 핵심 씬 반영에 집중."`
**L737**: `"guidance": "4000자 최소 기준, Blueprint 핵심만 반영."` → `"guidance": f"{ManuscriptLimits.MIN_LENGTH}자 최소 기준, Blueprint 핵심만 반영."`

---

### A-11: `modules/core/error_helper.py:123`

**L123**: `solution="원고가 4000자 이상이 되도록 내용을 보강하세요"` → `solution=f"원고가 {ManuscriptLimits.MIN_LENGTH}자 이상이 되도록 내용을 보강하세요"`

---

### A-12: `modules/core/constitutional_checker.py:168`

**L168**: `question="원고가 4000자 미만인가?"` → `question=f"원고가 {ManuscriptLimits.MIN_LENGTH}자 미만인가?"`

---

### A-13: `modules/domain/agents/critic.py:72`

**L72**: `"recommendations": ["최소 4000자 이상의 원고 필요"]` → `"recommendations": [f"최소 {ManuscriptLimits.MIN_LENGTH}자 이상의 원고 필요"]`

---

## B. ContextLimits 200K 상수 통합 (9건, 8파일)

> Sweep 7 G-2에서 `ContextLimits.MAX_CONTEXT_CHARS = 200_000`이 `constants.py`에 추가된 상태 전제.
> 만약 추가되지 않았다면 B-0을 먼저 수행.

### B-0: `modules/core/constants.py` — ContextLimits 클래스 추가 (Sweep 7에서 미완료 시)

**확인**: `constants.py`에 `class ContextLimits`가 있는지 검사. 없으면 파일 끝에 추가:

```python
class ContextLimits:
    """컨텍스트 크기 제한 상수"""
    MAX_CONTEXT_CHARS = 200_000  # Gemini API 컨텍스트 절삭 임계값
```

---

**각 파일에 공통 작업**:
```python
from modules.core.constants import ContextLimits
```

### B-1: `modules/core/stage2_finalizer.py:97-98`

**현재 패턴**:
```python
if len(arc_history_text) > 200000:
    arc_history_text = arc_history_text[:200000] + "\n... (컨텍스트 절삭)"
```
**수정**:
```python
if len(arc_history_text) > ContextLimits.MAX_CONTEXT_CHARS:
    arc_history_text = arc_history_text[:ContextLimits.MAX_CONTEXT_CHARS] + "\n... (컨텍스트 절삭)"
```

---

### B-2: `modules/core/stage3_orchestrator.py:413-414`

동일 패턴. `200000` → `ContextLimits.MAX_CONTEXT_CHARS` 로 교체.

---

### B-3: `modules/domain/agents/blueprint_ensemble.py:672-673`

동일 패턴. `200000` → `ContextLimits.MAX_CONTEXT_CHARS` 로 교체.

---

### B-4: `modules/domain/agents/chief_writer_context.py:297`

**현재**: `[:200000]` (bare slice)
**수정**: `[:ContextLimits.MAX_CONTEXT_CHARS]`

---

### B-5: `modules/domain/agents/preflight_checker.py:249-250`

동일 패턴. `200000` → `ContextLimits.MAX_CONTEXT_CHARS` 로 교체.

---

### B-6: `modules/domain/agents/director_ensemble.py:326-327`

동일 패턴. `200000` → `ContextLimits.MAX_CONTEXT_CHARS` 로 교체.

---

### B-7: `modules/domain/agents/director_continuity.py:382-383,720`

**L382-383**: 동일 패턴. `200000` → `ContextLimits.MAX_CONTEXT_CHARS`.
**L720**: `[:200000]` (bare slice) → `[:ContextLimits.MAX_CONTEXT_CHARS]`

---

### B-8: `modules/domain/agents/four_phase_arc_generator.py:402-403`

동일 패턴. `200000` → `ContextLimits.MAX_CONTEXT_CHARS` 로 교체.

---

## C. 미사용 import 정리 (15건, 10파일)

> `ruff check --fix`로 자동 수정 가능한 항목도 있으나, 수동 검증 권장.

### C-1: `modules/domain/agents/base_agent.py:16`

**삭제**: `from modules.core.escape_utils import EscapeUtils`

### C-2: `modules/domain/agents/director_auditor.py:24`

**삭제**: `from modules.core.primitive_guard import validate_primitive_compliance`

### C-3: `main_a.py:49`

**삭제 또는 축소**: `from modules.core.spinners import FancySpinner, StageSpinner, rich_console`
- 파일 내에서 실제 사용되는 것만 남기기. 사용 여부 `grep` 확인 후 결정.

### C-4: `main_a.py:87`

**확인 후 삭제**: `from modules.core.stage0 import StageZeroManager`
- 사용 여부 확인: `StageZeroManager`가 파일 내에서 참조되는지 검사.

### C-5: `main_a.py:111`

**확인 후 삭제**: `from modules.core.cross_agent_verifier import ComplianceLevel`

### C-6: `main_a.py:125`

**확인 후 삭제**: `from modules.core.self_reflection import ReflectionTarget`

### C-7: `modules/core/progress_manager.py:8-9`

**삭제**: `import time` + `from dataclasses import field`

### C-8: `modules/core/stage0/__init__.py:32,35`

**삭제**: `import os` + `from typing import Dict, List, Optional, Tuple`

### C-9: `modules/core/stage0/reverse_expander.py:14,21`

**삭제**: `from typing import Dict, List, Optional, Tuple` + `from spinner import PhaseIndicator, print_error`
- 주의: `spinner` import가 실제로 사용되는지 확인.

### C-10: `modules/core/stage0/spinner.py:12,17`

**삭제**: `from typing import Optional` + `from rich.color import Color`

### C-11: `modules/core/stage0/story_expander.py:12,18`

**삭제**: `from typing import Optional` + `from spinner import ProgressBar, print_error`
- 주의: `spinner` import가 실제로 사용되는지 확인.

**검증**: 각 파일에서 삭제 후 `python -m py_compile <파일>` 통과 확인. import 에러 발생 시 삭제 취소.

---

## D. Sync I/O in async def (1건)

### D-1: `modules/core/stage2_orchestrator.py:696`

**현상**: `async def` 내부에서 `open()` + `f.write()` 블로킹 호출 → 이벤트 루프 차단.

**현재 코드 (L696 부근)**:
```python
with open(failure_report_path, "w", encoding="utf-8") as f:
    f.write(report_content)
```

**수정**:
```python
import asyncio
...
await asyncio.to_thread(
    lambda: open(failure_report_path, "w", encoding="utf-8").write(report_content)
)
```

또는 더 안전한 패턴:
```python
def _write_report(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

await asyncio.to_thread(_write_report, failure_report_path, report_content)
```

- `import asyncio`가 파일 상단에 이미 있는지 확인.

---

## E. "projects" 경로 상수화 (10건, 2파일)

### E-0: 상수 확인

`modules/core/config_manager.py:20`에 이미 `self.projects_dir = self.root / "projects"`가 있음.
`main_a.py`에서는 `self.config_manager`를 통해 접근 가능한지 확인.

접근 불가 시, `main_a.py` 클래스 레벨에 상수 추가:
```python
_PROJECTS_DIR = "projects"
```

### E-1~E-8: `main_a.py` 8개 위치

| 줄 | 현재 | 수정 |
|----|------|------|
| 844 | `Path("projects") / project_name` | `Path(self._PROJECTS_DIR) / project_name` 또는 `self.config_manager.projects_dir / project_name` |
| 1512 | `os.path.join("projects", ...)` | 동일 상수 참조로 교체 |
| 1520 | `os.path.join("projects", ...)` | 동일 |
| 1527 | `os.path.join("projects", ...)` | 동일 |
| 1581 | `os.path.join("projects", ...)` | 동일 |
| 1952 | `os.path.join("projects", ...)` | 동일 |
| 1964 | `os.path.join("projects", ...)` | 동일 |
| 1975 | `os.path.join("projects", ...)` | 동일 |

### E-9: `modules/core/stage4_post_processor.py:127`

`os.path.join("projects", self.ctx.current_project.name, "logs")` → 동일 상수 참조로 교체.

**주의**: `os.path.join` → `Path` 통일도 바람직하나, 이 Sweep에서는 상수화만 수행. pathlib 통일은 별도 Sweep.

---

## 실행 가이드 (Codex용)

- **총 항목 수**: A(21) + B(9) + C(15) + D(1) + E(10) = **56건**
- A/B/C/D/E 카테고리 간 독립 — 병렬 실행 가능
- B 카테고리 내에서는 B-0을 먼저 실행 후 B-1~B-8
- C 카테고리: 삭제 전 반드시 `py_compile` 확인
- 기대 결과: `1,730+ passed, 68 xfailed`
- **커밋하지 말 것**

---

## 카테고리별 커밋 메시지

```
refactor(sweep8-a): consolidate ManuscriptLimits references — 21 hardcoded values across 13 files
refactor(sweep8-b): consolidate ContextLimits.MAX_CONTEXT_CHARS — 9 hardcoded 200K values across 8 files
chore(sweep8-c): remove 15 unused imports across 10 files
fix(sweep8-d): wrap sync file I/O in asyncio.to_thread inside async def
refactor(sweep8-e): centralize hardcoded "projects" path string in 10 locations
```

---

## 산출물 요약

| 카테고리 | 항목 수 | 파일 수 | 성격 |
|----------|---------|---------|------|
| A. ManuscriptLimits 통합 | 21 | 13 | 유지보수성 |
| B. ContextLimits 200K 통합 | 9 | 8 | 유지보수성 |
| C. 미사용 import 정리 | 15 | 10 | 코드 위생 |
| D. Sync I/O in async | 1 | 1 | 런타임 안전성 |
| E. "projects" 경로 상수화 | 10 | 2 | 유지보수성 |
| **합계** | **56** | **~25** | |
