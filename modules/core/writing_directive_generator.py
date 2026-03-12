"""[TF-54b] WritingDirectiveGenerator — PatternReport + Blueprint -> WritingDirective."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable

try:
    from modules.core.prompt_loader import PromptLoader
except ImportError:  # pragma: no cover - optional dependency in tests
    PromptLoader = None

from modules.core.pattern_tracker import PatternReport
from modules.core.stage4_types import WritingDirective

logger = logging.getLogger(__name__)

_PROMPT_DOMAIN = "writing_directive"
_PROMPT_KEY = "WRITING_DIRECTIVE_SYSTEM"


class WritingDirectiveGenerator:
    """PatternReport + Blueprint를 받아 WritingDirective를 LLM 1회로 생성."""

    def __init__(self, prompt_loader=None):
        if prompt_loader is not None:
            self._prompt_loader = prompt_loader
        elif PromptLoader:
            self._prompt_loader = PromptLoader()
        else:
            self._prompt_loader = None

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
            result = self._parse_response(raw)
            # [QI-1-A4] PatternReport 엔딩 문구를 ending_avoid_phrases에 병합
            if pattern_report and getattr(pattern_report, "recent_ending_texts", None):
                _existing = set(result.ending_avoid_phrases)
                for text in pattern_report.recent_ending_texts[-3:]:
                    if text and text not in _existing:
                        result.ending_avoid_phrases.append(text)
            return result
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
        pattern_summary = report.to_summary_text(min_freq=2) if report else ""
        pattern_summary = pattern_summary or "직전 화 패턴 없음 (초기 에피소드)"
        # [QI-1-A4] 직전 엔딩 문구 회피 목록
        _ending_texts = getattr(report, "recent_ending_texts", []) if report else []
        if _ending_texts:
            _avoid_section = "\n【회피할 엔딩 문구】 아래 문구는 이미 사용했으므로 유사한 엔딩을 피하세요:\n"
            _avoid_section += "\n".join(f"  - \"{t}\"" for t in _ending_texts[-3:])
            pattern_summary += "\n" + _avoid_section
        blueprint_summary = self._summarize_blueprint(blueprint)

        if self._prompt_loader:
            try:
                prompt = None
                if hasattr(self._prompt_loader, "load"):
                    prompt = self._prompt_loader.load(
                        _PROMPT_DOMAIN,
                        _PROMPT_KEY,
                        N=lookback,
                        pattern_summary=pattern_summary,
                        blueprint_summary=blueprint_summary,
                        genre=genre,
                        ep_num=ep_num,
                    )
                elif hasattr(self._prompt_loader, "get"):
                    tmpl = self._prompt_loader.get(_PROMPT_KEY, "")
                    if isinstance(tmpl, str) and tmpl:
                        prompt = tmpl.format(
                            N=lookback,
                            pattern_summary=pattern_summary,
                            blueprint_summary=blueprint_summary,
                            genre=genre,
                            ep_num=ep_num,
                        )
                if isinstance(prompt, str) and prompt.strip():
                    return prompt
            except Exception as e:
                logger.debug("[TF-54b] prompt_loader 로드 실패: %s", str(e)[:100])

        return (
            f"[Genre] {genre}\n"
            f"[Episode] {ep_num}\n"
            f"[직전 {lookback}화 패턴]\n{pattern_summary}\n\n"
            f"[이번 화 블루프린트 요약]\n{blueprint_summary}\n\n"
            "위를 참고해 이번 화 집필 지시를 JSON으로만 출력하세요:\n"
            '{"ending_style":"","metaphor_avoid":[],"metaphor_suggest":[],"emotion_required":"",'
            '"npc_directives":{},"intensity_note":"","expression_ban":[]}'
        )

    def _summarize_blueprint(self, blueprint: dict) -> str:
        if not isinstance(blueprint, dict):
            return ""
        parts: list[str] = []

        scenario = str(blueprint.get("integrated_scenario", "") or "").strip()
        if scenario:
            parts.append(scenario[:300])

        scene_breakdown = blueprint.get("scene_breakdown", [])
        if isinstance(scene_breakdown, dict):
            scene_iter = list(scene_breakdown.values())[:3]
        elif isinstance(scene_breakdown, list):
            scene_iter = scene_breakdown[:3]
        else:
            scene_iter = []
        for i, scene in enumerate(scene_iter, 1):
            if isinstance(scene, dict):
                goal = str(scene.get("goal", "") or scene.get("objective", "")).strip()
                if goal:
                    parts.append(f"씬{i}: {goal[:80]}")
            elif isinstance(scene, str) and scene.strip():
                parts.append(f"씬{i}: {scene[:80]}")

        ending_hook = str(blueprint.get("ending_hook", "") or "").strip()
        if ending_hook:
            parts.append(f"엔딩 훅: {ending_hook[:100]}")

        return "\n".join(parts)[:500]

    def _parse_response(self, raw: str) -> WritingDirective:
        if not raw or not raw.strip():
            return WritingDirective()

        text = raw.strip()
        if "```" in text:
            start = text.find("```")
            end = text.rfind("```")
            if start != end:
                text = text[start + 3 : end].strip()
                if text.startswith("json"):
                    text = text[4:].strip()

        data = None
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            s = text.find("{")
            e = text.rfind("}")
            if s != -1 and e > s:
                try:
                    data = json.loads(text[s : e + 1])
                except json.JSONDecodeError:
                    return WritingDirective()
            else:
                return WritingDirective()

        if not isinstance(data, dict):
            return WritingDirective()

        def _pick(*keys: str):
            for key in keys:
                if key in data:
                    return data.get(key)
            return None

        def _as_list(*keys: str) -> list[str]:
            value = _pick(*keys)
            if isinstance(value, list):
                return [str(v) for v in value if str(v).strip()]
            if isinstance(value, str) and value.strip():
                return [v.strip() for v in value.split(",") if v.strip()]
            return []

        def _as_dict(*keys: str) -> dict[str, str]:
            value = _pick(*keys)
            if isinstance(value, dict):
                return {str(k): str(v) for k, v in value.items() if str(k).strip() and str(v).strip()}
            return {}

        def _as_str(*keys: str) -> str:
            value = _pick(*keys)
            if value is None:
                return ""
            return str(value).strip()

        return WritingDirective(
            ending_style=_as_str("ending_style", "endingStyle", "ending", "ending_type"),
            ending_avoid_phrases=_as_list("ending_avoid_phrases", "endingAvoidPhrases", "avoid_endings"),
            metaphor_avoid=_as_list("metaphor_avoid", "metaphorAvoid", "avoid_metaphor", "avoid_metaphors"),
            metaphor_suggest=_as_list("metaphor_suggest", "metaphorSuggest", "suggest_metaphor", "suggest_metaphors"),
            emotion_required=_as_str("emotion_required", "emotionRequired", "required_emotion", "emotion"),
            npc_directives=_as_dict("npc_directives", "npcDirectives", "npc_actions"),
            intensity_note=_as_str("intensity_note", "intensityNote", "intensity"),
            expression_ban=_as_list("expression_ban", "expressionBan", "banned_expressions", "ban_expressions"),
        )
