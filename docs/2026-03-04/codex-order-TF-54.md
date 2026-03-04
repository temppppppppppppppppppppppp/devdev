# Codex Order: TF-54 구현 (WritingDirective 시스템)

> **목적**: 에피소드별 동적 집필 지시 시스템 구현 — 표현 반복·엔딩 고착·감정 빈곤 근절.
> **구현 범위**: TF-54a(PatternTracker) → 54b(DirectiveGenerator) → 54c(CW 주입) → 54d(Director 정합성) → 54e(self-critique)
> **금지**: 명세에 없는 파일 생성, 명세에 없는 파일 수정, 테스트 파일 이외의 신규 메서드 추가.

---

## 0) 강제 제약

- 각 Phase 완료 후 `python -m py_compile`로 문법 검사 필수.
- 신규 파일은 명세 경로에만 생성.
- 수정 파일은 지정된 위치만 변경 (인접 코드 보존).
- 출력 보고서: `C:/Users/wjjo/Desktop/글도비/docs/2026-03-04/TF-54-implementation-result.md`

---

## Phase 1: TF-54a — PatternTracker + WritingDirective 타입

### 1-A: `WritingDirective` dataclass → `modules/core/stage4_types.py` 말미에 추가

```python
@dataclasses.dataclass
class WritingDirective:
    """에피소드별 동적 집필 지시. PatternTracker + LLM이 생성."""
    ending_style: str = ""
    metaphor_avoid: list[str] = dataclasses.field(default_factory=list)
    metaphor_suggest: list[str] = dataclasses.field(default_factory=list)
    emotion_required: str = ""
    npc_directives: dict[str, str] = dataclasses.field(default_factory=dict)
    intensity_note: str = ""
    expression_ban: list[str] = dataclasses.field(default_factory=list)

    def is_empty(self) -> bool:
        return not any([self.ending_style, self.metaphor_avoid, self.expression_ban])
```

`dataclasses`는 파일 상단에 이미 import됨. 없으면 추가.

---

### 1-B: `config/settings/validation.yaml` 말미에 추가

```yaml
pattern_tracker:
  lookback_episodes: 5          # 직전 몇 화 원고를 분석할지
  min_expression_freq: 2        # expression_ban 포함 최소 빈도
  enable: true                  # false 시 PatternTracker 전체 스킵
```

---

### 1-C: 신규 파일 생성 — `modules/core/pattern_tracker.py`

```python
"""[TF-54a] PatternTracker — 직전 N화 원고에서 반복 패턴 집계 (LLM 0회)."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# ── 추적 대상 표현 (장르 무관 공통 + 투자물 특화) ──────────────────────────
TRACKED_EXPRESSIONS: list[str] = [
    "사무실의 공기",
    "동공이 흔들",
    "입꼬리를 비틀",
    "폐부 깊숙이",
    r"단순한 .{1,15}(아니다|아니었다)",
    "거의 비명에 가까운",
    "강철 같은",
    "얼음처럼 차가운",
    "모든 것은 시나리오대로",
    "눈에 불꽃이 타올",
    "얼굴이 하얗게 질",
    r"사냥감|맹수|포식자",
    r"제국의 (왕|지휘석|기둥|영토)",
    "나는 알고 있었다",
    "그때였다",
    "텅 빈 사무실",
]

# ── 은유 카테고리 ────────────────────────────────────────────────────────────
METAPHOR_CATEGORIES: dict[str, list[str]] = {
    "군사": ["전쟁", "총알", "참호", "사령관", "전함", "함교", "무기", "탄창"],
    "사냥": ["사냥감", "맹수", "포식자", "먹잇감", "조준경", "미끼"],
    "제국": ["제국", "왕", "왕국", "기사", "신하", "왕좌"],
    "자연": ["바람", "파도", "폭풍", "태양", "달빛", "강물"],
    "음식": ["요리", "맛", "조리", "재료", "양념"],
    "건축": ["기둥", "주춧돌", "벽돌", "설계", "건물"],
    "게임": ["바둑", "장기", "체스", "카드", "판"],
}

# ── 엔딩 분류 키워드 ─────────────────────────────────────────────────────────
ENDING_CLASSIFIERS: dict[str, list[str]] = {
    "선언문": ["시작이었다", "서막이 올랐다", "전쟁이 시작", "사냥이 시작"],
    "수사의문문": ["것인가?", "것일까?", "될 것인가?"],
    "차가운미소": ["미소가 걸렸다", "미소를 지었다", "입꼬리를"],
    "조용한여운": [],  # 위 키워드에 해당하지 않으면 조용한여운으로 분류
}


@dataclass
class PatternReport:
    """PatternTracker가 집계한 직전 N화 패턴 요약."""
    expression_freq: dict[str, int] = field(default_factory=dict)
    ending_patterns: list[str] = field(default_factory=list)
    npc_reaction_patterns: dict[str, list[str]] = field(default_factory=dict)
    metaphor_categories: dict[str, int] = field(default_factory=dict)
    emotion_diversity: float = 0.0
    protagonist_emotions: list[str] = field(default_factory=list)

    def to_summary_text(self, min_freq: int = 2) -> str:
        """LLM 주입용 요약 텍스트 생성 (~500자)."""
        lines: list[str] = []

        freq_items = [(expr, cnt) for expr, cnt in self.expression_freq.items() if cnt >= min_freq]
        if freq_items:
            freq_items.sort(key=lambda x: -x[1])
            lines.append("【반복 표현】 " + ", ".join(f"'{e}'({c}회)" for e, c in freq_items[:6]))

        if self.ending_patterns:
            counter: dict[str, int] = {}
            for p in self.ending_patterns:
                counter[p] = counter.get(p, 0) + 1
            lines.append("【엔딩 패턴】 " + ", ".join(f"{k}:{v}회" for k, v in counter.items()))

        heavy = [(cat, cnt) for cat, cnt in self.metaphor_categories.items() if cnt >= 3]
        unused = [cat for cat, cnt in self.metaphor_categories.items() if cnt == 0]
        if heavy:
            lines.append("【과사용 은유】 " + ", ".join(f"{c}({n}회)" for c, n in heavy))
        if unused:
            lines.append("【미사용 은유】 " + ", ".join(unused[:3]))

        if self.emotion_diversity < 0.4 and self.protagonist_emotions:
            top = max(set(self.protagonist_emotions), key=self.protagonist_emotions.count)
            lines.append(f"【감정 빈곤】 주인공 감정이 '{top}'에 편중 (다양성={self.emotion_diversity:.2f})")

        for npc, reactions in list(self.npc_reaction_patterns.items())[:2]:
            if len(reactions) >= 3:
                lines.append(f"【NPC 반응 고정】 {npc}: {' → '.join(reactions[-3:])}")

        return "\n".join(lines)[:500]


class PatternTracker:
    """직전 N화 원고에서 반복 패턴을 Python으로 집계 (LLM 0회)."""

    def build_report(self, db, ep_num: int, lookback: int = 5) -> PatternReport:
        """DB에서 직전 lookback화 원고를 로드해 PatternReport 반환."""
        manuscripts: list[str] = self._load_manuscripts(db, ep_num, lookback)
        if not manuscripts:
            return PatternReport()

        report = PatternReport()
        report.expression_freq = self._count_expressions(manuscripts)
        report.ending_patterns = self._classify_endings(manuscripts)
        report.metaphor_categories = self._count_metaphors(manuscripts)

        combined = "\n".join(manuscripts)
        report.protagonist_emotions = self._extract_emotions(combined)
        unique = len(set(report.protagonist_emotions))
        total = len(report.protagonist_emotions)
        report.emotion_diversity = (unique / total) if total else 0.0

        return report

    # ── private helpers ──────────────────────────────────────────────────────

    def _load_manuscripts(self, db, ep_num: int, lookback: int) -> list[str]:
        if db is None:
            return []
        manuscripts: list[str] = []
        for ep in range(max(1, ep_num - lookback), ep_num):
            try:
                row = db.get_manuscript(ep)
                if row and isinstance(row.get("content"), str):
                    manuscripts.append(row["content"])
            except Exception as e:
                logger.debug("[PatternTracker] ep%d 로드 실패 (비치명): %s", ep, str(e)[:60])
        return manuscripts

    def _count_expressions(self, manuscripts: list[str]) -> dict[str, int]:
        combined = "\n".join(manuscripts)
        freq: dict[str, int] = {}
        for pattern in TRACKED_EXPRESSIONS:
            try:
                count = len(re.findall(pattern, combined))
                if count > 0:
                    freq[pattern] = count
            except re.error:
                pass
        return freq

    def _classify_endings(self, manuscripts: list[str]) -> list[str]:
        patterns: list[str] = []
        for ms in manuscripts:
            tail = ms[-200:] if len(ms) > 200 else ms
            classified = "조용한여운"
            for label, keywords in ENDING_CLASSIFIERS.items():
                if label == "조용한여운":
                    continue
                if any(kw in tail for kw in keywords):
                    classified = label
                    break
            patterns.append(classified)
        return patterns

    def _count_metaphors(self, manuscripts: list[str]) -> dict[str, int]:
        combined = "\n".join(manuscripts)
        return {cat: sum(combined.count(kw) for kw in keywords)
                for cat, keywords in METAPHOR_CATEGORIES.items()}

    def _extract_emotions(self, text: str) -> list[str]:
        """간단한 감정 키워드 추출 (regex 기반)."""
        emotion_patterns = [
            "차가운 만족", "차가운 분노", "씁쓸", "안도", "두려움",
            "기쁨", "슬픔", "허탈", "흥분", "죄책감",
        ]
        found: list[str] = []
        for emo in emotion_patterns:
            count = text.count(emo)
            found.extend([emo] * count)
        return found
```

---

### Phase 1 검증

```bash
python -m py_compile modules/core/stage4_types.py
python -m py_compile modules/core/pattern_tracker.py
```

---

## Phase 2: TF-54b — WritingDirectiveGenerator + YAML 프롬프트

### 2-A: 신규 파일 — `config/prompts/writing_directive.yaml`

```yaml
system: |
  당신은 웹소설 집필 감독입니다. 직전 {N}화 패턴 분석과 이번 화 블루프린트를 참고하여
  이번 화의 집필 지시(WritingDirective)를 JSON으로 생성하세요.

  [직전 {N}화 패턴 분석]
  {pattern_summary}

  [이번 화 블루프린트 요약]
  {blueprint_summary}

  목표: 직전 화들과 겹치지 않는 신선한 표현·구조·감정 유도.
  반드시 JSON만 출력하세요. 설명 텍스트 없이 JSON 객체만.

  {
    "ending_style": "이번 화 마무리 방식 — 선언문/수사의문문/조용한여운/일상적마무리 중 1개 + 사유 1문장",
    "metaphor_avoid": ["과사용 은유 키워드 최대 4개"],
    "metaphor_suggest": ["대안 은유 영역 최대 3개"],
    "emotion_required": "주인공에게 요구하는 감정 1가지 (최근 부족한 감정)",
    "npc_directives": {"NPC명": "이번 화 행동 지시 1문장"},
    "intensity_note": "이번 화 전반 강도 가이드 1문장",
    "expression_ban": ["이번 화 금지 표현 — 최근 2회+ 등장한 것만, 최대 5개"]
  }
```

---

### 2-B: 신규 파일 — `modules/core/writing_directive_generator.py`

```python
"""[TF-54b] WritingDirectiveGenerator — 패턴 리포트 + Blueprint → 집필 지시 LLM 1회."""
from __future__ import annotations

import json
import logging
from typing import Callable

from modules.core.pattern_tracker import PatternReport
from modules.core.stage4_types import WritingDirective

logger = logging.getLogger(__name__)

_YAML_KEY = "writing_directive"


class WritingDirectiveGenerator:
    """PatternReport + Blueprint를 받아 WritingDirective를 LLM 1회로 생성."""

    def __init__(self, prompt_loader=None):
        self._prompt_loader = prompt_loader

    def generate(
        self,
        pattern_report: PatternReport,
        blueprint: dict,
        genre: str,
        ep_num: int,
        llm_callback: Callable[[str], str],
        lookback: int = 5,
    ) -> WritingDirective:
        """LLM 1회 호출로 WritingDirective 생성. 실패 시 빈 WritingDirective 반환."""
        try:
            prompt = self._build_prompt(pattern_report, blueprint, genre, ep_num, lookback)
            raw = llm_callback(prompt)
            return self._parse_response(raw)
        except Exception as e:
            logger.warning("[TF-54b] WritingDirectiveGenerator 실패 (비치명): %s", str(e)[:120])
            return WritingDirective()

    def _build_prompt(
        self,
        report: PatternReport,
        blueprint: dict,
        genre: str,
        ep_num: int,
        lookback: int,
    ) -> str:
        pattern_summary = report.to_summary_text() or "직전 화 패턴 없음 (초기 에피소드)"
        blueprint_summary = self._summarize_blueprint(blueprint)

        # PromptLoader 사용 가능하면 YAML 프롬프트 로드
        if self._prompt_loader:
            try:
                tmpl = self._prompt_loader.get(_YAML_KEY, "system", "")
                prompt = tmpl.format(
                    N=lookback,
                    pattern_summary=pattern_summary,
                    blueprint_summary=blueprint_summary,
                )
                return prompt
            except Exception:
                pass

        # 폴백: 인라인 프롬프트
        return (
            f"직전 {lookback}화 패턴:\n{pattern_summary}\n\n"
            f"블루프린트 요약:\n{blueprint_summary}\n\n"
            "위를 참고해 이번 화 집필 지시를 JSON으로만 출력하세요:\n"
            '{"ending_style":"","metaphor_avoid":[],"metaphor_suggest":[],'
            '"emotion_required":"","npc_directives":{},"intensity_note":"","expression_ban":[]}'
        )

    def _summarize_blueprint(self, blueprint: dict) -> str:
        if not isinstance(blueprint, dict):
            return ""
        parts: list[str] = []
        scenario = str(blueprint.get("integrated_scenario", "") or "").strip()
        if scenario:
            parts.append(scenario[:300])
        scene_breakdown = blueprint.get("scene_breakdown", [])
        if isinstance(scene_breakdown, list):
            for i, scene in enumerate(scene_breakdown[:3], 1):
                if isinstance(scene, dict):
                    goal = str(scene.get("goal", "") or scene.get("objective", "")).strip()
                    if goal:
                        parts.append(f"씬{i}: {goal[:80]}")
        return "\n".join(parts)[:400]

    def _parse_response(self, raw: str) -> WritingDirective:
        if not raw or not raw.strip():
            return WritingDirective()
        text = raw.strip()
        # JSON 블록 추출
        if "```" in text:
            start = text.find("```")
            end = text.rfind("```")
            if start != end:
                text = text[start + 3:end].strip()
                if text.startswith("json"):
                    text = text[4:].strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # 중괄호 범위 추출 시도
            s = text.find("{")
            e = text.rfind("}")
            if s != -1 and e > s:
                try:
                    data = json.loads(text[s:e + 1])
                except json.JSONDecodeError:
                    return WritingDirective()
            else:
                return WritingDirective()

        if not isinstance(data, dict):
            return WritingDirective()

        def _list(key: str) -> list[str]:
            v = data.get(key, [])
            return [str(x) for x in v] if isinstance(v, list) else []

        def _dict(key: str) -> dict[str, str]:
            v = data.get(key, {})
            return {str(k): str(val) for k, val in v.items()} if isinstance(v, dict) else {}

        return WritingDirective(
            ending_style=str(data.get("ending_style", "") or ""),
            metaphor_avoid=_list("metaphor_avoid"),
            metaphor_suggest=_list("metaphor_suggest"),
            emotion_required=str(data.get("emotion_required", "") or ""),
            npc_directives=_dict("npc_directives"),
            intensity_note=str(data.get("intensity_note", "") or ""),
            expression_ban=_list("expression_ban"),
        )
```

---

### Phase 2 검증

```bash
python -m py_compile modules/core/writing_directive_generator.py
```

---

## Phase 3: TF-54c — CW 컨텍스트 주입

### 3-A: `modules/domain/agents/chief_writer_context.py` — `build_common_context()` 파라미터 + 섹션 추가

`build_common_context()` 시그니처 말미에 파라미터 추가:

```python
# 현재 시그니처 마지막 줄 (upcoming_arc_items 파라미터) 다음에 추가
writing_directive=None,  # WritingDirective | None  [TF-54c]
```

`build_common_context()` 바디 내에서 context 문자열을 조합하는 부분 말미에 다음 섹션 주입:

```python
# [TF-54c] WritingDirective 섹션 주입
if writing_directive and not writing_directive.is_empty():
    _wd_lines = ["### 이번 화 집필 지시 (WritingDirective)",
                 "**반드시 준수하세요. Director가 이 지시의 준수 여부를 평가합니다.**", ""]
    if writing_directive.ending_style:
        _wd_lines.append(f"- 마무리 방식: {writing_directive.ending_style}")
    if writing_directive.expression_ban:
        _wd_lines.append(f"- 금지 표현: {', '.join(writing_directive.expression_ban)}")
    if writing_directive.metaphor_avoid:
        _wd_lines.append(f"- 피할 은유: {', '.join(writing_directive.metaphor_avoid)}")
    if writing_directive.metaphor_suggest:
        _wd_lines.append(f"- 추천 은유: {', '.join(writing_directive.metaphor_suggest)}")
    if writing_directive.emotion_required:
        _wd_lines.append(f"- 감정 요구: {writing_directive.emotion_required}")
    if writing_directive.npc_directives:
        npc_str = ", ".join(f"{k}: {v}" for k, v in writing_directive.npc_directives.items())
        _wd_lines.append(f"- NPC 지시: {npc_str}")
    if writing_directive.intensity_note:
        _wd_lines.append(f"- 강도 가이드: {writing_directive.intensity_note}")
    # context 변수에 append (파일 내 context 조합 방식에 맞게 삽입)
```

**주의**: `build_common_context()`의 반환 방식(리스트 join, f-string 등)에 맞게 삽입 위치를 조정할 것. 함수 내부에서 context를 어떻게 조합하는지 먼저 확인 후 적절한 위치에 삽입.

---

### 3-B: `config/prompts/chief_writer.yaml` — COMMON_RULES 9~11번 추가

COMMON_RULES 섹션 말미에 추가:

```yaml
9. [TF-54] 은유 다양성: WritingDirective의 metaphor_avoid에 있는 은유 영역을 이번 화에서 피하라.
   metaphor_suggest의 영역을 적극 활용하라.
10. [TF-54] 강도 조절: 일상 행동(계약, 이동, 식사)은 담담하게 서술하라.
    모든 장면을 극적으로 묘사하면 진짜 클라이맥스의 임팩트가 죽는다.
11. [TF-54] NPC 음성 분화: 각 NPC는 고유한 말투·어휘·문장 길이를 가져야 한다.
    WritingDirective의 npc_directives를 따라 이번 화에서의 행동을 차별화하라.
```

---

## Phase 4: TF-54d — Director 정합성 + TF-35c 부분 해제

### 4-A: `config/prompts/director.yaml` — TF-35c 규칙 수정

파일에서 "절대 포함하지 말 것" 또는 "스타일 개선" 금지 관련 기존 TF-35c 텍스트를 찾아 다음으로 교체:

```yaml
# 기존 (예시):
# 절대 포함하지 말 것: 분량 확장, 대화 비율 조정, 문체 개선, 묘사 추가 등 양적/스타일 지시.

# 변경:
절대 포함하지 말 것: 분량 확장, 대화 비율 조정, 묘사 추가 등 양적 지시.
단, WritingDirective 위반 사항은 feedback에 포함할 것:
- 금지 표현 사용 (expression_ban에 있는 표현이 원고에 등장)
- ending_style 미준수 (지시한 마무리 방식과 다른 방식으로 종결)
- 감정 요구 미충족 (emotion_required로 지시한 감정이 원고에 없음)
이것은 스타일 '개선' 요구가 아니라 사전 합의된 '계약' 위반 지적이다.
또한 quality_engagement 평가 시 WritingDirective 준수 여부를 고려하라.
```

**주의**: 파일에서 TF-35c 관련 실제 텍스트를 먼저 확인 후 해당 부분만 수정.

---

### 4-B: `modules/domain/agents/director_ensemble.py` — mandatory_context에 directive 추가

`_director_mc_parts`를 구성하는 부분을 찾아 다음을 추가:

```python
# [TF-54d] WritingDirective를 Director mandatory_context에 주입
# stage4_interview_round에서 _director_mc_parts에 directive 텍스트를 prepend하는 방식으로 처리
# (stage4_interview_round에서 주입하므로 director_ensemble.py 수정 불필요할 수 있음 — 확인 후 결정)
```

**주의**: `_director_mc_parts`가 `stage4_interview_round.py`에서 구성되는지, `director_ensemble.py`에서 구성되는지 먼저 확인할 것. 실제 구성 위치에서만 수정.

---

## Phase 5: TF-54c+d 통합 배선 — `modules/core/stage4_interview_round.py`

`run()` 메서드에서 Blueprint 로드 직후 다음 코드를 추가:

```python
# [TF-54a+b] PatternTracker + WritingDirectiveGenerator 호출
from modules.core.pattern_tracker import PatternTracker
from modules.core.writing_directive_generator import WritingDirectiveGenerator
from modules.core.stage4_types import WritingDirective

_writing_directive: WritingDirective = WritingDirective()
try:
    _pt_enabled = _threshold("pattern_tracker.enable", True)
    if _pt_enabled:
        _pt = PatternTracker()
        _lookback = int(_threshold("pattern_tracker.lookback_episodes", 5))
        _pt_report = _pt.build_report(db=self.ctx.db, ep_num=next_ep, lookback=_lookback)
        if _pt_report:
            _wdg = WritingDirectiveGenerator(prompt_loader=self.ctx.prompt_loader)
            _writing_directive = _wdg.generate(
                pattern_report=_pt_report,
                blueprint=blueprint,
                genre=genre,
                ep_num=next_ep,
                llm_callback=self._truth_gate_llm_ask,  # Flash LLM 재사용
                lookback=_lookback,
            )
            if not _writing_directive.is_empty():
                logging.info("[TF-54] WritingDirective 생성 완료: ending=%s, ban=%d개",
                             _writing_directive.ending_style[:30], len(_writing_directive.expression_ban))
except Exception as _wd_e:
    logging.warning("[TF-54] WritingDirective 생성 실패 (비치명): %s", str(_wd_e)[:100])
    _writing_directive = WritingDirective()
```

이후 CW 컨텍스트 빌드 호출 시 `writing_directive=_writing_directive` 전달.
Director `_director_mc_parts` 구성 시 directive 텍스트 prepend:

```python
# [TF-54d] Director에도 동일한 directive 주입
if not _writing_directive.is_empty():
    _wd_text = f"[WritingDirective]\n{_writing_directive.ending_style}\n금지: {', '.join(_writing_directive.expression_ban)}"
    _director_mc_parts.insert(0, _wd_text)  # 또는 append — 기존 구조에 맞게
```

**주의**: `_truth_gate_llm_ask`가 실제로 Flash 모델을 사용하는지 확인. 아니면 Flash LLM 콜백을 별도로 확인할 것.

---

## Phase 6: TF-54e — CW Self-Critique 확장

### `modules/domain/agents/chief_writer_quality.py` — `_self_critique()` 체크 2건 추가

기존 `_self_critique()` 메서드에서 체크 리스트에 다음 2건 추가:

```python
# [TF-54e] 6번째 체크: WritingDirective 준수
def _check_writing_directive(self, manuscript: str, directive) -> list[str]:
    """금지 표현 사용, ending_style 미준수 감지."""
    if directive is None or directive.is_empty():
        return []
    issues: list[str] = []
    for expr in directive.expression_ban:
        if expr and expr in manuscript:
            issues.append(f"금지 표현 '{expr}' 사용됨")
    # 엔딩 스타일 체크 (마지막 200자 기준)
    tail = manuscript[-200:] if len(manuscript) > 200 else manuscript
    if "조용한여운" in directive.ending_style and any(
        kw in tail for kw in ["시작이었다", "서막이 올랐다", "전쟁이 시작"]
    ):
        issues.append("ending_style '조용한여운' 지시인데 선언문으로 종결")
    return issues

# [TF-54e] 7번째 체크: 표현 신선도
def _check_expression_freshness(self, manuscript: str, expression_freq: dict) -> list[str]:
    """PatternReport의 고빈도 표현이 이번 원고에도 등장하는지 감지."""
    issues: list[str] = []
    for expr, freq in expression_freq.items():
        if freq >= 3 and expr in manuscript:
            issues.append(f"반복 표현 '{expr[:20]}' 이번 화에도 사용 (직전 {freq}회)")
    return issues
```

`_self_critique()` 메서드에서 이 두 메서드를 호출하고 결과를 issues 리스트에 통합.
`directive`와 `expression_freq` 파라미터를 `_self_critique()`에 추가 (`directive=None, expression_freq=None` 기본값).

---

## 테스트 파일 생성

### `tests/test_pattern_tracker.py` (신규)

```python
"""[TF-54a] PatternTracker 단위 테스트."""
import pytest
from modules.core.pattern_tracker import PatternTracker, PatternReport, TRACKED_EXPRESSIONS


def test_count_expressions_basic():
    tracker = PatternTracker()
    manuscripts = ["사무실의 공기가 얼어붙었다. 동공이 흔들렸다."]
    freq = tracker._count_expressions(manuscripts)
    assert freq.get("사무실의 공기", 0) >= 1
    assert freq.get("동공이 흔들", 0) >= 1


def test_classify_endings_선언문():
    tracker = PatternTracker()
    ms = ["이것이 진짜 시작이었다."]
    patterns = tracker._classify_endings([ms[0]])
    assert patterns[0] == "선언문"


def test_classify_endings_조용한여운():
    tracker = PatternTracker()
    ms = ["그는 조용히 창밖을 바라보았다."]
    patterns = tracker._classify_endings([ms[0]])
    assert patterns[0] == "조용한여운"


def test_count_metaphors():
    tracker = PatternTracker()
    manuscripts = ["전쟁이 시작되었다. 총알처럼 빠르게. 맹수처럼 달려들었다."]
    cats = tracker._count_metaphors(manuscripts)
    assert cats["군사"] >= 1
    assert cats["사냥"] >= 1


def test_emotion_diversity_low():
    tracker = PatternTracker()
    text = "차가운 만족. 차가운 만족. 차가운 만족."
    emotions = tracker._extract_emotions(text)
    unique = len(set(emotions))
    total = len(emotions)
    diversity = unique / total if total else 0
    assert diversity <= 0.5


def test_to_summary_text_not_empty():
    report = PatternReport(
        expression_freq={"사무실의 공기": 5, "동공이 흔들": 3},
        ending_patterns=["선언문", "선언문", "선언문"],
        metaphor_categories={"군사": 10, "사냥": 5, "음식": 0},
        emotion_diversity=0.2,
        protagonist_emotions=["차가운 만족"] * 5,
    )
    text = report.to_summary_text()
    assert len(text) > 10
    assert "반복 표현" in text or "엔딩" in text


def test_build_report_no_db():
    tracker = PatternTracker()
    report = tracker.build_report(db=None, ep_num=5)
    assert isinstance(report, PatternReport)


def test_build_report_db_returns_none(monkeypatch):
    class FakeDB:
        def get_manuscript(self, ep):
            return None
    tracker = PatternTracker()
    report = tracker.build_report(db=FakeDB(), ep_num=5, lookback=3)
    assert isinstance(report, PatternReport)
    assert report.expression_freq == {}
```

### `tests/test_writing_directive.py` (신규)

```python
"""[TF-54b,e] WritingDirectiveGenerator + WritingDirective 단위 테스트."""
import pytest
from modules.core.stage4_types import WritingDirective
from modules.core.writing_directive_generator import WritingDirectiveGenerator


def test_writing_directive_is_empty():
    wd = WritingDirective()
    assert wd.is_empty()


def test_writing_directive_not_empty():
    wd = WritingDirective(ending_style="조용한여운")
    assert not wd.is_empty()


def test_parse_valid_json():
    gen = WritingDirectiveGenerator()
    raw = '{"ending_style":"조용한여운","metaphor_avoid":["군사"],"metaphor_suggest":["음식"],"emotion_required":"안도","npc_directives":{},"intensity_note":"담담하게","expression_ban":["사무실의 공기"]}'
    wd = gen._parse_response(raw)
    assert wd.ending_style == "조용한여운"
    assert "군사" in wd.metaphor_avoid
    assert "사무실의 공기" in wd.expression_ban


def test_parse_json_with_markdown():
    gen = WritingDirectiveGenerator()
    raw = '```json\n{"ending_style":"선언문","metaphor_avoid":[],"metaphor_suggest":[],"emotion_required":"","npc_directives":{},"intensity_note":"","expression_ban":[]}\n```'
    wd = gen._parse_response(raw)
    assert wd.ending_style == "선언문"


def test_parse_empty_returns_empty():
    gen = WritingDirectiveGenerator()
    wd = gen._parse_response("")
    assert wd.is_empty()


def test_parse_invalid_json_returns_empty():
    gen = WritingDirectiveGenerator()
    wd = gen._parse_response("이것은 JSON이 아닙니다")
    assert wd.is_empty()


def test_generate_llm_failure_returns_empty():
    def failing_llm(prompt):
        raise RuntimeError("LLM 호출 실패")
    from modules.core.pattern_tracker import PatternReport
    gen = WritingDirectiveGenerator()
    report = PatternReport()
    wd = gen.generate(report, {}, "투자", 5, failing_llm)
    assert wd.is_empty()


def test_generate_success():
    def mock_llm(prompt):
        return '{"ending_style":"조용한여운","metaphor_avoid":["군사"],"metaphor_suggest":["음식"],"emotion_required":"안도","npc_directives":{"박성호":"유능한 모습"},"intensity_note":"담담하게","expression_ban":["동공이 흔들"]}'
    from modules.core.pattern_tracker import PatternReport
    gen = WritingDirectiveGenerator()
    report = PatternReport()
    wd = gen.generate(report, {}, "투자", 5, mock_llm)
    assert not wd.is_empty()
    assert wd.ending_style == "조용한여운"
```

---

## 최종 검증

```bash
python -m py_compile modules/core/pattern_tracker.py
python -m py_compile modules/core/writing_directive_generator.py
python -m py_compile modules/core/stage4_types.py
python -m py_compile modules/domain/agents/chief_writer_context.py
python -m py_compile modules/domain/agents/chief_writer_quality.py
python -m py_compile modules/core/stage4_interview_round.py
ruff check modules/core/pattern_tracker.py modules/core/writing_directive_generator.py
pytest tests/test_pattern_tracker.py tests/test_writing_directive.py -v
pytest tests/ -q
```

---

## 보고서 형식 (고정)

출력 파일: `C:/Users/wjjo/Desktop/글도비/docs/2026-03-04/TF-54-implementation-result.md`

```markdown
# TF-54 구현 결과

> 구현일: 2026-03-04

## 수정/생성 내역

| Phase | 파일 | 작업 | 완료 여부 |
|-------|------|------|---------|
| 1-A | stage4_types.py | WritingDirective dataclass 추가 | ✅/❌ |
| 1-B | validation.yaml | pattern_tracker 설정 추가 | ✅/❌ |
| 1-C | pattern_tracker.py | 신규 생성 | ✅/❌ |
| 2-A | writing_directive.yaml | 신규 생성 | ✅/❌ |
| 2-B | writing_directive_generator.py | 신규 생성 | ✅/❌ |
| 3-A | chief_writer_context.py | writing_directive 파라미터 + 섹션 | ✅/❌ |
| 3-B | chief_writer.yaml | COMMON_RULES 9~11 추가 | ✅/❌ |
| 4-A | director.yaml | TF-35c 부분 해제 | ✅/❌ |
| 4-B | director_ensemble.py | directive 주입 위치 확인 | ✅/❌ |
| 5 | stage4_interview_round.py | PatternTracker + Generator 배선 | ✅/❌ |
| 6 | chief_writer_quality.py | self-critique 2건 추가 | ✅/❌ |
| 테스트 | test_pattern_tracker.py | 신규 생성 | ✅/❌ |
| 테스트 | test_writing_directive.py | 신규 생성 | ✅/❌ |

## 주요 결정 사항

(Phase 4-B director_ensemble.py 수정 여부, _truth_gate_llm_ask 확인 결과 등)

## 검증 결과

- py_compile: 통과/실패
- ruff: 위반 N건
- test_pattern_tracker: N passed
- test_writing_directive: N passed
- 전체 테스트: N passed, N failed

## 체크리스트

- [ ] 명세에 없는 파일 수정 없음
- [ ] WritingDirective.is_empty() 정상 동작
- [ ] PatternTracker LLM 0회 확인
- [ ] WritingDirectiveGenerator LLM 1회 확인
- [ ] stage4_interview_round 배선 완료
- [ ] 전체 테스트 회귀 없음
```
