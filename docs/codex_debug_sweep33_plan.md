# Debug Sweep 33 — scene_breakdown string 패턴 전면 수정

## Context

Sweep 32 완료 (2,059 passed, 68 xfailed). 5개 탐색 에이전트가 **scene_breakdown이 dict가 아닌 string으로 올 때** 발생하는 시스템적 버그 패턴을 발견. LLM이 `scene_breakdown`을 `{"scene_1": {...}, "scene_2": {...}}` 대신 `"씬1: 설명\n씬2: 설명"` 같은 문자열로 반환하면 `.items()` → AttributeError 크래시, `len()` → 글자수 반환(씬 수가 아닌) → 검증 게이트 우회.

**이미 가드가 있는 파일**: `diversity_sampler.py:276`, `continuity_manuscript.py:429,834` (Sweep 32에서 수정됨)
**가드가 없는 파일**: 8개 모듈 12곳

---

## A-1 (HIGH): `director_ensemble.py:203` — len() 검증 게이트 우회

**파일**: `modules/domain/agents/director_ensemble.py:203`

**문제**:
```python
scene_count = len(blueprint.get("scene_breakdown", {}))
if scene_count < 4:
    return {"decision": "REJECT", ...}
```
- scene_breakdown이 string이면 `len()`이 글자수를 반환 → `len("씬1: ...씬2: ...") == 40` → `< 4` 불통과 → 불량 Blueprint가 REJECT 안 됨

**수정**: L203 위에 isinstance 가드 추가:
```python
_sb = blueprint.get("scene_breakdown", {})
scene_count = len(_sb) if isinstance(_sb, dict) else 0
```

---

## A-2 (HIGH): `cross_agent_verifier.py:207-213,247` — .items() 크래시 + len() 오류

**파일**: `modules/core/cross_agent_verifier.py`

**문제**:
```python
# L207
scene_breakdown = blueprint.get("scene_breakdown", {})
if scene_breakdown:                          # string도 truthy
    scene_count = len(scene_breakdown)       # L210: 글자수
    for scene_id, scene_data in scene_breakdown.items():  # L213: AttributeError!
# L247
max_expected_length = len(scene_breakdown) * 1500 * 1.5  # 글자수 × 1500 → 거대 숫자
```

**수정**: L207 다음에 isinstance 가드:
```python
scene_breakdown = blueprint.get("scene_breakdown", {})
if not isinstance(scene_breakdown, dict):
    scene_breakdown = {}
```

---

## A-3 (HIGH): `prompt_builder.py:127-139` — .keys() 크래시

**파일**: `modules/core/prompt_builder.py`

**문제**:
```python
# L127
scene_breakdown = blueprint.get("scene_breakdown", {})
if not scene_breakdown:
    return ""
# L131: len(scene_breakdown)  → 글자수
# L139: list(scene_breakdown.keys())  → string.keys() → AttributeError!
```

**수정**: L128을 수정:
```python
if not scene_breakdown or not isinstance(scene_breakdown, dict):
    return ""
```

---

## A-4 (HIGH): `constitutional_checker.py:331-334` — .items() 크래시

**파일**: `modules/core/constitutional_checker.py`

**문제**:
```python
# L331
scene_breakdown = blueprint.get("scene_breakdown", {})
if scene_breakdown:
    # L334
    for i, (scene_id, scene_data) in enumerate(list(scene_breakdown.items())[:6], 1):
```
- string이면 `.items()` → AttributeError

**수정**: L332를 수정:
```python
if scene_breakdown and isinstance(scene_breakdown, dict):
```

---

## A-5 (HIGH): `writer_template.py:130-138` — .items() 크래시

**파일**: `modules/core/writer_template.py`

**문제**:
```python
# L130
scene_breakdown = blueprint.get("scene_breakdown", {})
# L138
for i, (scene_id, scene_data) in enumerate(scene_breakdown.items()):
```
- 가드 없이 바로 `.items()` 호출

**수정**: L130 다음에 isinstance 가드:
```python
scene_breakdown = blueprint.get("scene_breakdown", {})
if not isinstance(scene_breakdown, dict):
    scene_breakdown = {}
```

---

## A-6 (MEDIUM): `confidence_calibration.py:339-341` — len() 점수 왜곡

**파일**: `modules/core/confidence_calibration.py`

**문제**:
```python
# L339
scene_breakdown = bp.get("scene_breakdown", {})
scene_count = len(scene_breakdown)  # string → 글자수 → 점수 과대 평가
```
- `len("씬1:...") == 25` → `4 <= 25 <= 7` 불통과 → `25 > 8` → score=10+concerns
- 실제 씬 0개인데 구조 점수 10점 받음

**수정**: L339 다음에 isinstance 가드:
```python
scene_breakdown = bp.get("scene_breakdown", {})
if not isinstance(scene_breakdown, dict):
    scene_breakdown = {}
scene_count = len(scene_breakdown)
```

---

## A-7 (MEDIUM): `pre_director_checklist.py:302-305,365,508-509` — 전달 + len() 오류

**파일**: `modules/core/pre_director_checklist.py`

**문제** (3곳):
```python
# L302-305: string을 _measure_scene_reflection에 전달 → .items() 크래시
scene_breakdown = blueprint.get("scene_breakdown", {})
if scene_breakdown:
    scene_metrics = self.manuscript_checker._measure_scene_reflection(manuscript, scene_breakdown)

# L365: len(string) → 글자수 → expected_max 거대
scene_count = len(blueprint.get("scene_breakdown", {}))

# L508-509: len(string) → 글자수 → scene_count < 3 우회
scene_breakdown = bp.get("scene_breakdown", {})
scene_count = len(scene_breakdown)
```

**수정**:
- L302: `if scene_breakdown and isinstance(scene_breakdown, dict):`
- L365: `_sb = blueprint.get("scene_breakdown", {}); scene_count = len(_sb) if isinstance(_sb, dict) else 0`
- L508: 다음 줄에 `if not isinstance(scene_breakdown, dict): scene_breakdown = {}`

---

## A-8 (MEDIUM): `pre_director_manuscript_checker.py:127,221` — .items()/.keys() 크래시 (방어 보강)

**파일**: `modules/core/pre_director_manuscript_checker.py`

**문제**: 호출자(A-7)에서 가드 추가되지만, 메서드 자체도 방어해야 함:
```python
# L127: _measure_scene_reflection(self, manuscript, scene_breakdown: dict) — 타입 힌트만
# L143: for scene_key, scene_data in scene_breakdown.items():

# L221: _check_scene_density_balance(self, manuscript, scene_breakdown: dict) — 타입 힌트만
# L230: if not scene_breakdown or len(scene_breakdown) < 3:
# L245: scene_keys = list(scene_breakdown.keys())
```

**수정**: 각 메서드 초입에 isinstance 가드 추가:
- L136 (`if not scene_breakdown:`) → `if not scene_breakdown or not isinstance(scene_breakdown, dict):`
- L230 (`if not scene_breakdown or len(scene_breakdown) < 3:`) → `if not isinstance(scene_breakdown, dict) or not scene_breakdown or len(scene_breakdown) < 3:`

---

## B-1 (MEDIUM): `diversity_sampler.py:285` — structure score 오버플로 (최대 130)

**파일**: `modules/core/diversity_sampler.py:285`

**문제**:
```python
scores["structure"] = 80 + (0.5 - abs(cv - 0.35)) * 100
```
- cv=0.35일 때: `80 + 0.5 * 100 = 130` → 0-100 스케일 초과
- 가중 평균에서 structure가 30% → 전체 점수도 왜곡

**수정**:
```python
scores["structure"] = min(100, 80 + (0.5 - abs(cv - 0.35)) * 100)
```

---

## B-2 (LOW): `semantic_plot_guard.py:167,276` — tactical_doc 타입 가드 누락

**파일**: `modules/core/semantic_plot_guard.py`

**문제**:
```python
# L167: tactical_doc.split("\n")  — dict이면 AttributeError
# L276: tactical_doc[:3000]       — dict이면 TypeError
```
- 호출자(`stage2_finalizer.py:254`)는 `refined_arc.get("tactical_doc", "")`로 전달
- 보통 string이지만, LLM이 dict로 반환 가능
- 호출부 try/except 안이라 크래시는 안 나지만, 기능 무력화

**수정**: `check_new_arc` 메서드 초입 (L152 근처):
```python
if tactical_doc and not isinstance(tactical_doc, str):
    tactical_doc = str(tactical_doc)
```

---

## B-3 (LOW): `director_auditor.py:642` — dead kwarg `current_len`

**파일**: `modules/domain/agents/director_auditor.py:642`

**문제**:
```python
self.prompt_loader.load_and_format(
    "director",
    "DIRECTOR_AUDIT_PROMPT_V30",
    ...
    current_len=current_len,  # ← YAML 템플릿에 {current_len} 없음 → 무시됨
    ...
)
```
- `config/prompts/director.yaml`의 `DIRECTOR_AUDIT_PROMPT_V30`에 `{current_len}` 플레이스홀더 없음
- 무해하지만 코드 읽기에 혼란

**수정**: L642 삭제 (`current_len=current_len,` 행 제거)

---

## 수정 파일 총괄

| # | 파일 | 변경 |
|---|------|------|
| A-1 | `modules/domain/agents/director_ensemble.py` | L203 isinstance 가드 |
| A-2 | `modules/core/cross_agent_verifier.py` | L207 isinstance 가드 |
| A-3 | `modules/core/prompt_builder.py` | L128 isinstance 조건 추가 |
| A-4 | `modules/core/constitutional_checker.py` | L332 isinstance 조건 추가 |
| A-5 | `modules/core/writer_template.py` | L130 isinstance 가드 |
| A-6 | `modules/core/confidence_calibration.py` | L339 isinstance 가드 |
| A-7 | `modules/core/pre_director_checklist.py` | L302,L365,L508 isinstance 가드 (3곳) |
| A-8 | `modules/core/pre_director_manuscript_checker.py` | L136,L230 isinstance 조건 보강 |
| B-1 | `modules/core/diversity_sampler.py` | L285 `min(100, ...)` 클램프 |
| B-2 | `modules/core/semantic_plot_guard.py` | L152 tactical_doc str 변환 |
| B-3 | `modules/domain/agents/director_auditor.py` | L642 dead kwarg 삭제 |

**총 11파일, ~20줄 변경**

---

## 테스트

기존 테스트로 회귀 확인 + scene_breakdown string 시나리오 테스트 추가:

```python
# tests/test_sweep33.py
"""Sweep 33: scene_breakdown string 패턴 방어 테스트"""
import pytest


class TestSceneBreakdownStringGuard:
    """scene_breakdown이 string일 때 크래시하지 않는지 검증"""

    def test_director_ensemble_string_scene_breakdown(self):
        """director_ensemble: string scene_breakdown → scene_count=0"""
        from modules.domain.agents.director_ensemble import DirectorEnsemble
        from unittest.mock import MagicMock

        de = DirectorEnsemble.__new__(DirectorEnsemble)
        de._d = MagicMock()
        bp = {
            "scene_breakdown": "씬1: 전투\n씬2: 대화",
            "integrated_scenario": "x" * 1000,
        }
        # string scene_breakdown → scene_count should be 0 → REJECT
        result = de._validate_blueprint_basic(bp)
        assert result["decision"] == "REJECT"

    def test_cross_agent_verifier_string_scene_breakdown(self):
        """cross_agent_verifier: string scene_breakdown → no crash"""
        from modules.core.cross_agent_verifier import CrossAgentVerifier
        from unittest.mock import MagicMock

        cav = CrossAgentVerifier.__new__(CrossAgentVerifier)
        bp = {
            "scene_breakdown": "씬1: 전투\n씬2: 대화",
            "ending_hook": "다음 화에서...",
        }
        # Should not crash
        violations = cav._check_manuscript_blueprint_consistency("원고 " * 500, bp)
        assert isinstance(violations, list)

    def test_prompt_builder_string_scene_breakdown(self):
        """prompt_builder: string scene_breakdown → returns empty string"""
        from modules.core.prompt_builder import PromptBuilder
        from unittest.mock import MagicMock

        pb = PromptBuilder.__new__(PromptBuilder)
        bp = {"scene_breakdown": "씬1: 전투\n씬2: 대화"}
        result = pb.generate_high_impact_zone_guide(bp)
        assert result == ""

    def test_constitutional_checker_string_scene_breakdown(self):
        """constitutional_checker: string scene_breakdown → no crash"""
        from modules.core.constitutional_checker import ConstitutionalChecker
        from unittest.mock import MagicMock

        cc = ConstitutionalChecker.__new__(ConstitutionalChecker)
        cc.MANUSCRIPT_CONSTITUTION = []
        bp = {"scene_breakdown": "씬1: 전투"}
        # _build_constitution_context should not crash
        lines = []
        # The method adds to lines list from blueprint
        # Just verify no AttributeError on .items()

    def test_writer_template_string_scene_breakdown(self):
        """writer_template: string scene_breakdown → empty slots"""
        from modules.core.writer_template import WriterTemplate
        from unittest.mock import MagicMock

        wt = WriterTemplate.__new__(WriterTemplate)
        wt.SCENE_LENGTH = {}
        bp = {"scene_breakdown": "씬1: 전투", "ep_num": 1}
        # from_blueprint with string scene_breakdown should produce 0 slots
        template = wt.from_blueprint(bp)
        assert len(template.slots) == 0

    def test_confidence_calibration_string_scene_breakdown(self):
        """confidence_calibration: string scene_breakdown → scene_count=0"""
        from modules.core.confidence_calibration import ConfidenceCalibration
        from unittest.mock import MagicMock

        cc = ConfidenceCalibration.__new__(ConfidenceCalibration)
        bp = {
            "scene_breakdown": "씬1: 전투",
            "ep_num": 1,
            "integrated_scenario": "시나리오" * 200,
        }
        # Should not crash, scene_count should be 0
        result = cc._evaluate_blueprint_confidence(bp)
        assert result["factors"]["scene_count"] == 0

    def test_pre_director_checklist_string_scene_breakdown(self):
        """pre_director_checklist: string scene_breakdown → no crash"""
        from modules.core.pre_director_checklist import PreDirectorChecklist
        from unittest.mock import MagicMock

        pdc = PreDirectorChecklist.__new__(PreDirectorChecklist)
        pdc.manuscript_checker = MagicMock()
        context = {
            "blueprint": {"scene_breakdown": "씬1: 전투"},
            "manuscript": "원고" * 500,
        }
        # Should not crash on _measure_scene_reflection call

    def test_diversity_sampler_score_clamp(self):
        """diversity_sampler: structure score <= 100"""
        from modules.core.diversity_sampler import DiversitySampler
        from unittest.mock import MagicMock

        ds = DiversitySampler.__new__(DiversitySampler)
        ds._prev_types = []
        bp = {
            "scene_breakdown": {
                "s1": {"type": "전투", "description": "a" * 100},
                "s2": {"type": "대화", "description": "b" * 100},
                "s3": {"type": "내면", "description": "c" * 100},
                "s4": {"type": "이동", "description": "d" * 100},
            }
        }
        result = ds.evaluate_diversity(bp)
        assert result["structure"] <= 100

    def test_semantic_plot_guard_dict_tactical_doc(self):
        """semantic_plot_guard: dict tactical_doc → str 변환, no crash"""
        from modules.core.semantic_plot_guard import SemanticPlotGuard
        from unittest.mock import MagicMock

        spg = SemanticPlotGuard.__new__(SemanticPlotGuard)
        spg._client = None
        spg._resolved_embeddings = []
        spg._resolved_keywords = [{"name": "test", "keywords": {"전투", "무공"}}]
        # dict tactical_doc should not crash
        result = spg.check_new_arc(tactical_doc={"content": "전투 장면"})
        assert isinstance(result, list)
```

```bash
set PYTHONIOENCODING=utf-8 && python -m pytest tests/test_sweep33.py -x -q
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -x -q
```

---

## 오탐 제거 기록

| 보고 | 실제 | 이유 |
|------|------|------|
| Agent 1 (closure/lambda) 전량 | ✗ 오탐 | 12개 패턴 전수 검사 — 모두 안전 |
| Agent 3 (circular refs) Director↔sub-modules | ✗ 설계 패턴 | V64 위임 패턴 — 의도된 구조 |
| Agent 3 (test cache leak) `_CONSTITUTION_CACHE` | ✗ 오탐 | 테스트 격리 이슈, 프로덕션 무관 |
| `continuity_manuscript.py:429,834` scene_breakdown | ✗ 이미 수정 | Sweep 32에서 isinstance 가드 추가됨 |
| `stage2_finalizer.py:343` npc_status.items() | ✗ 이미 수정 | L343에 `isinstance(..., dict)` 가드 존재 |
| `stage2_finalizer.py:254` tactical_doc dict | ✗ 부분 오탐 | L253 try/except 내부, `.split()` 아님 — 실제 `.split()`은 `semantic_plot_guard.py:167` (B-2로 이동) |

---

## Execution Update (2026-02-18)

Status: completed for Sweep 33 scope.

Applied items:
- A-1 `modules/domain/agents/director_ensemble.py`: `scene_breakdown` scene count now uses dict-only guard (`isinstance(..., dict)`), so string payload no longer bypasses REJECT gate.
- A-2 `modules/core/cross_agent_verifier.py`: added dict normalization for `scene_breakdown` in architect/writer precheck paths; avoids `.items()` crash and wrong `len(string)` scaling.
- A-3 `modules/core/prompt_builder.py`: `generate_high_impact_zone_guide` now returns empty guide unless `scene_breakdown` is dict.
- A-4 `modules/core/constitutional_checker.py`: context scene loop now runs only when `scene_breakdown` is dict.
- A-5 `modules/core/writer_template.py`: non-dict `scene_breakdown` normalized to `{}` before slot generation.
- A-6 `modules/core/confidence_calibration.py`: non-dict `scene_breakdown` normalized before `scene_count` calculation.
- A-7 `modules/core/pre_director_checklist.py`: three paths guarded (reflection handoff, expected length calc, scene-count checks) against string scene payloads.
- A-8 `modules/core/pre_director_manuscript_checker.py`: both scene reflection/density methods now early-return unless `scene_breakdown` is dict.
- B-1 `modules/core/diversity_sampler.py`: structure score clamped with `min(100, ...)` to enforce 0-100 range.
- B-2 `modules/core/semantic_plot_guard.py`: non-string `tactical_doc` is string-coerced at method entry.
- B-3 `modules/domain/agents/director_auditor.py`: removed dead `current_len` prompt kwarg not referenced by template.

Additional hardening done during verification:
- `modules/core/prompt_builder.py`: app-none safety guards added for `extract_npc_profiles`, `get_character_traits`, `generate_arc_context_v60`, and `build_item_acquisition_timeline`.
- `modules/core/cross_agent_verifier.py`: restored float coercion for `compliance_score` and made `_parse_result` robust for list payloads.
- `modules/domain/agents/director_ensemble.py`: aligned progress log level calls to expected `logging.info` in normal flow.

Added tests:
- `tests/test_sweep33.py` (7 tests): scene_breakdown string guards, tactical_doc type normalization, structure clamp, and source-level regression assertions.

Verification run:
- `python -m pytest tests/test_sweep33.py -q -x` -> `7 passed`
- `python -m pytest tests/test_prompt_builder.py tests/test_sweep33.py -q -x` -> `50 passed`
- `python -m pytest tests/test_director_modules.py tests/test_prompt_builder.py tests/test_stage2_pipeline.py tests/test_stage2_validation_pipeline.py tests/test_stage4_interview_round.py tests/test_continuity_modules.py -q -x` -> `285 passed`
- `python -m pytest tests/ -q -p no:capture` -> `2066 passed, 68 xfailed, 1 warning`

Notes:
- Test output still includes existing interactive/log prints and a post-run mocked ImportError traceback print, but pytest exit code is 0.
