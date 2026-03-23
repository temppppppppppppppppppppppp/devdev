"""
[V60.75] Three Phase Arc Generator (구 Four Phase)
3단계 Arc 생성 파이프라인 - 단순화 + 효율화

철학: "충분한 분량의, 상호 개연성 및 일관성 있는 Arc"

파이프라인:
1. Constraint: 제약 수집 (Preflight + Compiler + NegativeExamples)
2. Generate: Ensemble 생성 (3개 후보 → 최적 선택)
3. Validate: 통합 검증 (Python + LLM)

[V60.75 리팩토링]
- 기존: Preflight → Ensemble → Phase2.5 → Critic → Consensus (5단계, 8 LLM호출)
- 변경: Constraint → Generate → Validate (3단계, 4 LLM호출)
- 효과: 비용 50% 절감, 책임 명확화
"""

import json
import logging
import re
from collections.abc import Callable

from modules.core.constants import AIModels, ContextLimits, Stage2Limits, smart_truncate
from modules.core.fact_ledger import summarize_fact_ledger_numbers_block
from modules.core.failure_analyzer import FailureAnalyzer
from modules.validation.threshold_helper import _threshold

from .arc_ensemble import ArcEnsembleGenerator
from .base_agent import BaseAgent, _get_sub_component_models
from .constraint_compiler import ConstraintCompiler
from .negative_example_injector import NegativeExampleInjector
from .preflight_checker import PreflightChecker
from .unified_arc_validator import UnifiedArcValidator
from .four_phase_arc_runtime import FourPhaseArcRuntime

_NS3B_DIVERGENCE_THRESHOLD: float = _threshold("arc.ns3b_divergence_threshold", 0.30)
_DB_ADVISORY_NOTICE = "(Python 자동 감지 — 오탐 가능, 참고용)"

# 장르 Guard 이름 → NegativeExampleInjector 장르 키 매핑
_NEI_GENRE_DETECT_MAP: dict[str, str] = {
    "wuxia": "wuxia",
    "무협": "wuxia",
    "hunter": "hunter",
    "헌터": "hunter",
    "investment": "investment",
    "투자": "investment",
    "fantasy": "fantasy",
    "판타지": "fantasy",
    "cooking": "cooking",
    "요리": "cooking",
    "alt_history": "alt_history",
    "대체역사": "alt_history",
    "actor": "actor",
    "배우": "actor",
    "sports": "sports",
    "스포츠": "sports",
    "medical": "medical",
    "의학": "medical",
    "composer": "composer",
    "작곡": "composer",
}


def _build_extended_timeline_advisory(db) -> list[str]:
    """장기 timeline_entries를 Arc 생성용 컨텍스트 라인으로 변환한다."""
    getter = getattr(db, "get_timeline_range", None)
    if not callable(getter):
        return []

    try:
        timeline = getter(start_ep=1, end_ep=9999, limit=30)
        if not isinstance(timeline, list) or len(timeline) < 5:
            return []

        timeline_lines = [f"[DB-9 확장 타임라인 (최근 15화)] {_DB_ADVISORY_NOTICE}"]
        for entry in timeline[-15:]:
            if not isinstance(entry, dict):
                continue
            ep_no = entry.get("ep_no", "?")
            story_date = str(entry.get("story_date", "") or "").strip()
            elapsed_days = entry.get("elapsed_days", "")
            time_note = str(entry.get("time_note", "") or "")[:40]
            parts = [f"ep{ep_no}"]
            if story_date:
                parts.append(story_date)
            if elapsed_days not in (None, ""):
                parts.append(f"+{elapsed_days}일")
            if time_note:
                parts.append(time_note)
            timeline_lines.append("  " + " | ".join(parts))
        return timeline_lines if len(timeline_lines) > 1 else []
    except Exception as tl_err:
        logging.debug("[DB-9] timeline advisory 실패 (비치명): %s", tl_err)
        return []


def _check_arc_vs_block_targets(
    arc: dict,
    curr_block: dict | None,
    arc_no: int,
    threshold: float = _NS3B_DIVERGENCE_THRESHOLD,
) -> str:
    """
    [NS-3-B] arc_end_state 수치 vs curr_block.genre_ext 목표 비교.
    Python-only advisory. 괴리율이 임계치를 넘으면 경고 문자열을 반환.
    """
    if not isinstance(curr_block, dict) or not isinstance(arc, dict):
        return ""

    genre_ext = curr_block.get("genre_ext")
    if not isinstance(genre_ext, dict):
        return ""

    state_constraints = arc.get("state_constraints", {})
    if not isinstance(state_constraints, dict):
        return ""
    arc_end = state_constraints.get("arc_end_state", {})
    if not isinstance(arc_end, dict):
        return ""

    def parse_num(raw) -> float | None:
        if isinstance(raw, (int, float)):
            return float(raw)
        if not isinstance(raw, str):
            return None
        s = re.sub(r"\([^)]*\)", "", raw).strip()
        if not s:
            return None
        sign = 1.0
        if s[0] in "+-":
            if s[0] == "-":
                sign = -1.0
            s = s[1:].strip()
        s = s.replace(",", "")

        total = 0.0
        matched = False
        for unit, mult in (("조", 1e12), ("억", 1e8), ("만", 1e4)):
            m = re.search(rf"([\d]+(?:\.[\d]+)?)\s*{unit}", s)
            if m:
                matched = True
                try:
                    total += float(m.group(1)) * mult
                except ValueError:
                    return None
                s = re.sub(rf"[\d]+(?:\.[\d]+)?\s*{unit}", "", s)
        if matched:
            tail = re.search(r"([\d]+(?:\.[\d]+)?)", s)
            if tail:
                try:
                    total += float(tail.group(1))
                except ValueError:
                    return None
            return sign * total

        plain = re.search(r"([\d]+(?:\.[\d]+)?)", s)
        if not plain:
            return None
        try:
            return sign * float(plain.group(1))
        except ValueError:
            return None

    target = parse_num(genre_ext.get("capital_after", ""))
    if not target:
        return ""

    actual = None
    actual_key = None
    for key in ("capital", "total_assets", "assets", "total_capital"):
        value = parse_num(arc_end.get(key, ""))
        if value is not None:
            actual = value
            actual_key = key
            break

    if actual is None:
        return ""

    divergence = abs(target - actual) / abs(target) if target else 0.0
    if divergence > threshold:
        return (
            f"[NS-3-B] Arc {arc_no} arc_end_state.{actual_key}={actual / 1e8:.1f}억 vs "
            f"treatment target capital_after={genre_ext.get('capital_after')} "
            f"(divergence {divergence * 100:.0f}%). "
            "Please realign tactical_doc numbers with block target."
        )
    return ""


def _format_investment_advisory(results: list[dict]) -> str:
    """F-1/F-2 결과를 Director advisory 문자열로 포맷."""
    if not results:
        return ""

    lines = ["[MAJOR · InvestmentMathVerifier] 투자 수치 검산 결과:"]
    minor_lines: list[str] = []
    minor_count = 0

    for r in results:
        severity = str(r.get("severity", "MINOR")).upper()
        text = str(r.get("text") or r.get("issue") or "").strip()
        if not text:
            continue

        idx = r.get("candidate_idx")
        prefix = f"(후보 {int(idx) + 1}) " if isinstance(idx, int | float) else ""
        line = f"  [{severity}] {prefix}{text}"

        if severity == "MINOR":
            minor_count += 1
            minor_lines.append(line)
            continue
        lines.append(line)

    # 노이즈 억제를 위해 MINOR는 3건 이상일 때만 표시
    if minor_count >= 3:
        lines.extend(minor_lines)

    return "\n".join(lines)


def _merge_candidate_quality_flag(
    flag: dict,
    *,
    force_reject: bool = False,
    force_pass_with_fix: bool = False,
    score_cap: int | None = None,
    reason: str = "",
    feedback: str = "",
) -> dict:
    if force_reject:
        flag["force_reject"] = True
    if force_pass_with_fix:
        flag["force_pass_with_fix"] = True
    if isinstance(score_cap, int):
        current = flag.get("score_cap")
        flag["score_cap"] = min(int(current), score_cap) if isinstance(current, int) else score_cap
    if reason:
        reasons = flag.setdefault("reasons", [])
        if reason not in reasons:
            reasons.append(reason[:160])
    if feedback:
        snippets = flag.setdefault("_feedback_snippets", [])
        if feedback not in snippets:
            snippets.append(feedback[:240])
            flag["feedback"] = "\n".join(snippets[:3])
    return flag


def _build_candidate_quality_flags(
    candidates: list[dict],
    ns3b_notes: list[tuple[int, str]],
    investment_advisories: list[dict],
) -> list[dict]:
    flags = [
        {
            "force_reject": False,
            "force_pass_with_fix": False,
            "score_cap": None,
            "reasons": [],
            "feedback": "",
        }
        for _ in candidates
    ]

    for idx, note in ns3b_notes:
        if 0 <= idx < len(flags):
            _merge_candidate_quality_flag(
                flags[idx],
                force_pass_with_fix=True,
                score_cap=89,
                reason=f"ns3b:{note}",
                feedback=f"NS-3-B mismatch requires at least PASS_WITH_FIX.\n{note}",
            )

    for advisory in investment_advisories:
        if not isinstance(advisory, dict):
            continue
        idx = advisory.get("candidate_idx")
        if not isinstance(idx, int) or not (0 <= idx < len(flags)):
            continue
        severity = str(advisory.get("severity", "MINOR")).upper()
        text = str(advisory.get("text") or advisory.get("issue") or "").strip()
        if severity == "CRITICAL":
            _merge_candidate_quality_flag(
                flags[idx],
                force_reject=True,
                score_cap=69,
                reason=f"investment-critical:{text or 'critical_advisory'}",
                feedback=f"Critical investment advisory blocks automatic PASS.\n{text}".strip(),
            )
        elif severity == "MAJOR":
            _merge_candidate_quality_flag(
                flags[idx],
                force_pass_with_fix=True,
                score_cap=89,
                reason=f"investment-major:{text or 'major_advisory'}",
                feedback=f"Major investment advisory requires at least PASS_WITH_FIX.\n{text}".strip(),
            )

    for flag in flags:
        flag.pop("_feedback_snippets", None)
    return flags


def _ns4_extract_time_markers(arc_data: dict) -> list:
    """[NS-4-S2] Arc tactical_doc/beat_sequence에서 날짜·상대시간 마커 추출 (regex, LLM 0회)."""
    import re as _re

    tactical_doc = arc_data.get("tactical_doc") or ""
    beat_seq = arc_data.get("beat_sequence") or ""
    if isinstance(beat_seq, list):
        beat_seq = " ".join(str(b) for b in beat_seq)

    _text = str(tactical_doc) + "\n" + str(beat_seq)
    _patterns = [
        r"\d{4}년\s*\d{1,2}월(?:\s*\d{1,2}일)?",  # utf8-hygiene: allow-line regex quantifier
        r"\d{1,2}월\s*\d{1,2}일",
        r"\d{1,2}월(?:\s*(?:말|초|중순|하순|상순))?",  # utf8-hygiene: allow-line regex quantifier
        r"\d+(?:일|주|달|개월|년)\s*(?:후|전)",  # utf8-hygiene: allow-line regex quantifier
    ]
    _found = []
    for _p in _patterns:
        _found.extend(_re.findall(_p, _text))
    return list(dict.fromkeys(_found))[:5]


def _trim_location(loc: str, max_len: int = 80) -> str:
    """[TF-60] 위치 문자열이 과도하게 긴 경우 핵심어만 추출."""
    if not loc or len(loc) <= max_len:
        return loc
    # 첫 문장(마침표 기준) 추출 시도
    dot_pos = loc.find(".")
    if 10 < dot_pos <= max_len:
        return loc[:dot_pos].strip()
    # 마침표 없으면 첫 max_len자
    return loc[:max_len].rstrip() + "…"


def _normalize_item_name(value) -> str:
    """아이템 값을 문자열 이름으로 정규화."""
    if isinstance(value, dict):
        for key in ("item", "name", "value"):
            item = value.get(key)
            if item:
                return str(item).strip()
        return ""
    return str(value).strip() if value else ""


def _extract_forbidden_item_names(preflight_result: dict) -> list[str]:
    """preflight.absolute_prohibitions.items_cannot_acquire -> 아이템명 리스트."""
    if not isinstance(preflight_result, dict):
        return []
    prohibitions = preflight_result.get("absolute_prohibitions", {})
    if not isinstance(prohibitions, dict):
        return []
    raw_items = prohibitions.get("items_cannot_acquire", [])
    if not isinstance(raw_items, list):
        return []
    names = []
    seen = set()
    for raw in raw_items:
        name = _normalize_item_name(raw)
        if name and name not in seen:
            seen.add(name)
            names.append(name)
    return names


def _extract_prev_arc_end_equipment(prev_arcs: list[dict]) -> list[str]:
    """직전 Arc arc_end_state.equipment를 문자열 리스트로 정규화."""
    if not prev_arcs:
        return []
    last_arc = prev_arcs[-1] if isinstance(prev_arcs[-1], dict) else {}
    state_constraints = last_arc.get("state_constraints", {})
    if not isinstance(state_constraints, dict):
        return []
    arc_end = state_constraints.get("arc_end_state", {})
    if not isinstance(arc_end, dict):
        return []
    equipment = arc_end.get("equipment", [])

    names = []
    seen = set()
    if isinstance(equipment, str):
        parts = [x.strip() for x in equipment.split(",")]
    elif isinstance(equipment, list):
        parts = equipment
    else:
        parts = []

    for raw in parts:
        name = _normalize_item_name(raw)
        if name and name not in seen:
            seen.add(name)
            names.append(name)
    return names


class FourPhaseArcGenerator(BaseAgent):
    """
    [V60.75] Three Phase Arc Generator

    3단계 파이프라인: 제약수집 → 생성 → 검증
    (클래스명은 호환성을 위해 유지)
    """

    def __init__(
        self,
        context,
        client,
        model_tier: str = None,
        flash_ask: Callable[[str], str] | None = None,
    ):
        super().__init__(context, client, model_tier)
        # DI 후보: context.master_bible (getattr fallback 2회: L177, L545 — protagonist_config 추출)
        # DI 후보: context.guard (hasattr 패턴 — 장르 감지용, L63)

        # 서브 모듈
        sub_models = _get_sub_component_models("four_phase_arc_generator")
        self.preflight = PreflightChecker(context, client, sub_models.get("preflight", "gemini-2.5-flash"))
        self.ensemble = ArcEnsembleGenerator(context, client, sub_models.get("ensemble", AIModels.DEFAULT_ARCHITECT))
        self.validator = UnifiedArcValidator(context, client, sub_models.get("validator", "gemini-2.5-flash"))
        self.compiler = None
        # [S2#1] 장르 Guard에서 장르 감지 → NegativeExampleInjector에 전달
        _detected_genre = "wuxia"
        try:
            if hasattr(context, "guard") and context.guard:
                _guard_name = context.guard.get_genre_name().lower()
                for _key, _genre in _NEI_GENRE_DETECT_MAP.items():
                    if _key in _guard_name:
                        _detected_genre = _genre
                        break
        except Exception as _e:
            logging.warning("[FourPhase] 장르 감지 실패, wuxia 기본값 사용: %s", _e)
        self._genre = _detected_genre
        self.compiler = ConstraintCompiler(genre=self._genre)
        self.negative_injector = NegativeExampleInjector(_detected_genre)
        self._flash_ask = flash_ask
        self.runtime = FourPhaseArcRuntime(self)

        # 통계
        self.stats = {
            "total_attempts": 0,
            "phase1_complete": 0,
            "phase2_complete": 0,
            "phase3_pass": 0,
            "phase3_reject": 0,
        }

    def _determine_ep_count(self, curr_block: dict, arc_no: int, prev_arcs: list[dict]) -> tuple[int, str]:
        """
        [V66.1] Python 휴리스틱 기반 가변 페이싱 - ep_count 동적 결정 (정보량 기반)

        LLM 호출 없이 블록 텍스트 길이/문장 수로 적정 화수를 판단.
        기존 LLM 호출 대비 5-10s 절감.

        Args:
            curr_block: 현재 블록 DNA
            arc_no: Arc 번호
            prev_arcs: 이전 Arc 리스트

        Returns:
            (ep_count, reasoning) - 3~6 범위의 화수와 결정 이유
        """
        min_ep_count = 2
        max_ep_count = Stage2Limits.MAX_EP_COUNT

        # 블록 내용 추출
        block_content = ""
        if isinstance(curr_block, dict):
            for key in ["context", "event_villain", "solution", "reward", "content"]:
                val = curr_block.get(key, "")
                if isinstance(val, str):
                    block_content += val + " "
                elif isinstance(val, dict):
                    block_content += json.dumps(val, ensure_ascii=False) + " "

        content_len = len(block_content.strip())

        # [V66.1] Python 휴리스틱: 텍스트 길이 + 문장 수 기반 판단
        if content_len < 350:
            ep_count = 2
            reasoning = f"블록 정보량 매우 부족 ({content_len}자 < 350자) → 2화 압축"
        elif content_len < 500:
            ep_count = 3
            reasoning = f"블록 정보량 부족 ({content_len}자 < 500자) → 3화 압축"
        elif content_len > 1500:
            ep_count = max_ep_count  # 6화
            reasoning = f"블록 정보량 풍부 ({content_len}자 > 1500자) → 최대 화수"
        else:
            # [PC-1-B] 500~1500자 구간: 문장 수 비례로 2~5화 결정
            import re

            sentence_count = len(re.split(r"[.。!?!\?\n]+", block_content))  # utf8-hygiene: allow-line regex quantifier
            if sentence_count <= 5:
                ep_count = 2
                reasoning = f"낮은 정보량 ({content_len}자, {sentence_count}문장) → 2화"
            elif sentence_count <= 8:
                ep_count = 3
                reasoning = f"보통 정보량 ({content_len}자, {sentence_count}문장) → 3화"
            elif sentence_count >= 15:
                ep_count = 5  # [PC-1-B] 6→5
                reasoning = f"높은 정보량 ({content_len}자, {sentence_count}문장) → 5화"
            else:
                ep_count = Stage2Limits.DEFAULT_EP_COUNT  # 4화
                reasoning = f"표준 정보량 ({content_len}자, {sentence_count}문장) → 기본 {Stage2Limits.DEFAULT_EP_COUNT}화"

        # [TF-9] tension_level 보정 — treatment 설계 의도 반영
        tension_level = curr_block.get("tension_level") if isinstance(curr_block, dict) else None
        if isinstance(tension_level, (int, float)):
            if tension_level >= 8:
                ep_count += 1
                reasoning += f" / tension={tension_level} → +1화"
            elif tension_level <= 3:
                ep_count -= 1
                reasoning += f" / tension={tension_level} → -1화"

        # 범위 강제 (안전장치)
        ep_count = max(min_ep_count, min(max_ep_count, ep_count))

        return ep_count, reasoning

    def _build_pacing_signal_payload(
        self,
        curr_block: dict,
        ep_count_suggestion: int,
        pacing_reason: str,
    ) -> dict:
        """Collect density signals while leaving the final ep_count judgment to the LLM."""
        block_content = ""
        item_hint_count = 0
        reward_present = False
        solution_present = False

        if isinstance(curr_block, dict):
            for key in ["context", "event_villain", "solution", "reward", "content"]:
                val = curr_block.get(key, "")
                if key == "reward":
                    reward_present = bool(val)
                if key == "solution":
                    solution_present = bool(val)
                if isinstance(val, str):
                    block_content += val + " "
                    if key in {"event_villain", "solution", "reward"}:
                        item_hint_count += len(re.findall(r"[가-힣A-Za-z0-9_]+", val))
                elif isinstance(val, dict):
                    serialized = json.dumps(val, ensure_ascii=False)
                    block_content += serialized + " "
                    if key in {"event_villain", "solution", "reward"}:
                        item_hint_count += len(re.findall(r"[가-힣A-Za-z0-9_]+", serialized))

        content_len = len(block_content.strip())
        sentence_count = len(re.split(r"[.。?!\n]+", block_content)) if block_content.strip() else 0  # utf8-hygiene: allow-line regex quantifier
        tension_level = curr_block.get("tension_level") if isinstance(curr_block, dict) else None
        low_resource_block = bool(item_hint_count <= 8 and not reward_present and not solution_present)

        if ep_count_suggestion <= 3:
            suggested_pace_mode = "compressed"
        elif ep_count_suggestion >= 6:
            suggested_pace_mode = "expanded"
        else:
            suggested_pace_mode = "standard"

        return {
            "content_len": content_len,
            "sentence_count": sentence_count,
            "tension_level": tension_level,
            "item_hint_count": item_hint_count,
            "reward_present": reward_present,
            "solution_present": solution_present,
            "low_resource_block": low_resource_block,
            "ep_count_suggestion": ep_count_suggestion,
            "suggested_pace_mode": suggested_pace_mode,
            "pacing_reason": pacing_reason,
        }

    def generate(
        self,
        arc_no: int,
        ep_start: int,
        vol_strategy: str,
        curr_block: dict,
        prev_arcs: list[dict],
        assets: dict = None,
        max_internal_retries: int = 9,
        protagonist_name: str = "주인공",
        director_feedback: str = "",
        entity_registry: dict = None,
        state_tracker=None,
        vector_context: str = "",
        adversarial_self_play=None,
        director=None,
    ) -> tuple[dict | None, dict]:
        """Thin owner shell over the bounded four-phase runtime."""
        return self.runtime.generate(
            arc_no=arc_no,
            ep_start=ep_start,
            vol_strategy=vol_strategy,
            curr_block=curr_block,
            prev_arcs=prev_arcs,
            assets=assets,
            max_internal_retries=max_internal_retries,
            protagonist_name=protagonist_name,
            director_feedback=director_feedback,
            entity_registry=entity_registry,
            state_tracker=state_tracker,
            vector_context=vector_context,
            adversarial_self_play=adversarial_self_play,
            director=director,
        )

    # =========================================================================
    # [TF-23] InPlace — LLM 1회 호출로 Arc 국소 수정
    # =========================================================================

    def _inplace_patch_arc(
        self,
        *,
        original_arc: dict,
        director_feedback: str,
        arc_no: int,
    ) -> dict | None:
        """[TF-23] LLM 1회 호출로 Arc in-place 수정. 실패 시 None → patch/rewrite 폴백."""
        from modules.core.prompt_loader import PromptLoader
        from modules.core.response_schemas import ARC_DESIGN_SCHEMA

        _full_json = json.dumps(original_arc, ensure_ascii=False, indent=2)
        if len(_full_json) > 30000:
            logging.warning("[TRUNCATION] _inplace_patch_arc: Arc JSON %d자 > 30KB 상한 → InPlace 불가", len(_full_json))
            return None  # 절단 시 깨진 JSON → full rewrite 폴백
        original_json = _full_json

        try:
            _patch_template = PromptLoader().load("arc_generator", "ARC_PATCH_MODE_PROMPT")
        except Exception as e:
            logging.warning(f"[TF-23] ARC_PATCH_MODE_PROMPT 로드 실패: {e!s:.100}")
            _patch_template = None

        def _esc(s):
            return s.replace("{", "{{").replace("}", "}}")

        if _patch_template:
            prompt = _patch_template.format(
                feedback_text=_esc(director_feedback),
                original_arc=_esc(original_json),
            )
        else:
            prompt = (
                f"[Arc 원본 보존 + 지적사항만 수정]\n\n"
                f"## Director 피드백\n{director_feedback}\n\n"
                f"## 원본 Arc\n{original_json}\n\n"
                f"전면 재설계하지 마세요. 지적된 부분만 고치세요."
            )

        try:
            response = self.ensemble.ask(
                prompt, temperature=0.3, response_schema=ARC_DESIGN_SCHEMA, thinking_level="medium"
            )
            result = self.ensemble._extract_json_robust(response)
            if not isinstance(result, dict):
                return None
            # 원본 필드 병합 (부분 응답 보상) — 1-depth deep merge
            for key, val in original_arc.items():
                if key not in result:
                    result[key] = val
                elif isinstance(val, dict) and isinstance(result[key], dict):
                    for sub_key, sub_val in val.items():
                        if sub_key not in result[key]:
                            result[key][sub_key] = sub_val
            # arc_end_state 검증
            _sc = result.get("state_constraints", {})
            if not isinstance(_sc, dict) or not _sc.get("arc_end_state"):
                logging.warning("[TF-23] InPlace: arc_end_state 누락 → 실패")
                return None
            from modules.models.arc import validate_arc
            result = validate_arc(result)
            logging.info(f"✅ [TF-23] Arc {arc_no} in-place 수정 완료")
            return result
        except Exception as e:
            logging.warning(f"[TF-23] Arc in-place 패치 실패: {e!s:.200}")
            return None

    # =========================================================================
    # [Patch Mode] Arc 원본 보존 + Director 피드백 지적사항만 수정
    # =========================================================================

    def patch_arc_with_feedback(
        self,
        *,
        original_arc: dict,
        director_feedback: str,
        attempt_number: int,
        # generate()와 동일 파라미터
        arc_no: int,
        ep_start: int,
        vol_strategy: str,
        curr_block: dict,
        prev_arcs: list[dict],
        assets: dict = None,
        protagonist_name: str = "주인공",
        entity_registry: dict = None,
        state_tracker=None,
        vector_context: str = "",
        adversarial_self_play=None,
        rejected_strategy: str = "",  # [TF-36] partial 시 1개 전략만
    ) -> tuple[dict | None, dict]:
        """[Patch Mode] 원본 Arc를 보존하며 Director 피드백 지적사항만 수정.

        패치 전용 프롬프트(ARC_PATCH_MODE_PROMPT)를 로드하여 원본 Arc + Director
        피드백을 enhanced_feedback으로 조립한 뒤, generate()의 Phase 2 ensemble을
        호출하여 후보를 생성한다.

        실패 시 (None, pipeline_result) 반환 → 호출측에서 full regenerate 폴백.
        """
        pipeline_result = {
            "arc_no": arc_no,
            "phases": {},
            "final_verdict": None,
            "retries": 0,
            "patch_mode": True,
            "patch_used": True,
            "patch_fallback": False,
        }

        enhanced_feedback = self._build_patch_mode_feedback(
            original_arc=original_arc,
            director_feedback=director_feedback,
            attempt_number=attempt_number,
        )
        preflight_result, full_constraint_block = self._build_patch_mode_constraint_block(prev_arcs)
        best_arc = self._run_patch_mode_ensemble_generation(
            arc_no=arc_no,
            ep_start=ep_start,
            vol_strategy=vol_strategy,
            curr_block=curr_block,
            prev_arcs=prev_arcs,
            assets=assets,
            protagonist_name=protagonist_name,
            entity_registry=entity_registry,
            vector_context=vector_context,
            rejected_strategy=rejected_strategy,
            preflight_result=preflight_result,
            full_constraint_block=full_constraint_block,
            enhanced_feedback=enhanced_feedback,
        )
        if best_arc is None:
            pipeline_result["final_verdict"] = "FAILED"
            return None, pipeline_result

        verdict, validation_result = self._validate_patch_mode_candidate(
            best_arc=best_arc,
            prev_arcs=prev_arcs,
            full_constraint_block=full_constraint_block,
            state_tracker=state_tracker,
        )

        pipeline_result["phases"]["validate"] = {
            "status": "complete",
            "verdict": verdict,
            "issues_count": len(validation_result.get("issues", [])),
        }

        if verdict == "PASS":
            best_arc, asp_used = self._apply_patch_mode_asp_correction(
                best_arc=best_arc,
                arc_no=arc_no,
                ep_start=ep_start,
                director_feedback=director_feedback,
                adversarial_self_play=adversarial_self_play,
            )
            if asp_used:
                pipeline_result["asp_used"] = True

            pipeline_result["final_verdict"] = "PASS"
            logging.info(f"✅ [Patch Mode] Arc {arc_no} 패치 성공")
            return best_arc, pipeline_result

        logging.warning(f" [Patch Mode] Arc {arc_no} 패치 검증 실패 → 폴백 필요")
        pipeline_result["final_verdict"] = "FAILED"
        return None, pipeline_result

    def _build_patch_mode_feedback(self, *, original_arc: dict, director_feedback: str, attempt_number: int) -> str:
        """Patch-mode prompt를 구성하고 원본 Arc tail context를 보존한다."""
        try:
            from modules.core.prompt_loader import PromptLoader

            patch_template = PromptLoader().load("arc_generator", "ARC_PATCH_MODE_PROMPT")
        except Exception as e:
            logging.warning(f"[SilentPass:ArcGen] ARC_PATCH_MODE_PROMPT 로드 실패: {e!s:.100}")
            patch_template = None

        full_json = json.dumps(original_arc, ensure_ascii=False, indent=2)
        if len(full_json) > 30000:
            logging.warning(
                "[TRUNCATION] patch_arc_with_feedback: Arc JSON %d자 → 30000자 (%.1f%% 손실)",
                len(full_json),
                (1 - 30000 / len(full_json)) * 100,
            )
        original_text = smart_truncate(full_json, max_chars=30000, head_chars=16500)

        if patch_template:
            def _esc(value: str) -> str:
                return value.replace("{", "{{").replace("}", "}}")

            patch_section = patch_template.format(
                feedback_text=_esc(director_feedback),
                original_arc=_esc(original_text),
            )
        else:
            patch_section = (
                f"[패치 모드: Arc 원본 보존 + 지적사항만 수정]\n\n"
                f"## Director 피드백\n{director_feedback}\n\n"
                f"## 원본 Arc\n{original_text}\n\n"
                f"전면 재설계하지 마세요. 지적된 부분만 고치세요."
            )

        return (
            f"[🔧 {attempt_number}차 수정 - 패치 모드: Arc 원본 보존 + 지적사항만 수정]\n\n"
            f"{patch_section}\n\n"
            f"⚠️ 원본 Arc의 전체 구조, 에피소드 배분, 서사 흐름을 보존하면서 피드백 지적사항만 수정하세요.\n"
            f"⚠️ 수정하지 않는 부분은 원본을 그대로 유지하세요."
        )

    def _build_patch_mode_constraint_block(self, prev_arcs: list[dict]) -> tuple[dict, str]:
        """Patch-mode에서도 generate()와 동일한 constraint envelope를 사용한다."""
        preflight_result = self.preflight.analyze(prev_arcs)
        preflight_injection = self.preflight.generate_analyst_injection(preflight_result, genre=self._genre)
        compiled_constraints = self.compiler.compile(prev_arcs)
        negative_examples = self.negative_injector.generate_injection()
        self_check = self.negative_injector.generate_self_check_prompt()
        genre_energy_warning = (
            f"⚠️ 이 작품은 {self._genre} 장르입니다. tactical_doc의 [시작 상태]/[종료 상태]에\n"
            '"내공", "정신력", "마나" 등의 수치화된 능력치를 사용하지 마세요.\n'
            "심리 상태는 서술형으로 표현하세요. (예: \"극도의 긴장 상태\", \"자신감 회복\")"
        ) if self._genre not in ("wuxia",) else ""
        full_constraint_block = "\n\n".join(
            part
            for part in [
                genre_energy_warning,
                f"### [PREFLIGHT 분석]\n{preflight_injection}" if preflight_injection else "",
                f"### [HARD CONSTRAINTS — 절대 금지]\n{compiled_constraints}" if compiled_constraints else "",
                f"### [NEGATIVE EXAMPLES]\n{negative_examples}" if negative_examples else "",
                f"### [SELF-CHECK]\n{self_check}" if self_check else "",
            ]
            if part.strip()
        )
        return preflight_result, full_constraint_block

    def _run_patch_mode_ensemble_generation(
        self,
        *,
        arc_no: int,
        ep_start: int,
        vol_strategy: str,
        curr_block: dict,
        prev_arcs: list[dict],
        assets: dict | None,
        protagonist_name: str,
        entity_registry: dict | None,
        vector_context: str,
        rejected_strategy: str,
        preflight_result: dict,
        full_constraint_block: str,
        enhanced_feedback: str,
    ) -> dict | None:
        """Patch-mode ensemble 후보를 생성하고 후속 검증 전 상태를 보정한다."""
        ep_count_suggestion, pacing_reason = self._determine_ep_count(curr_block, arc_no, prev_arcs)
        pacing_signals = self._build_pacing_signal_payload(curr_block, ep_count_suggestion, pacing_reason)
        protagonist_config = {}
        try:
            master_bible = getattr(self.context, "master_bible", {})
            if master_bible:
                bible_root = master_bible.get("MasterBible", master_bible)
                protagonist_config = bible_root.get("protagonist_config", {})
        except Exception as e:
            logging.debug("[TF-26] master_bible access failed (patch): %s", str(e)[:100])

        prev_arc_context = self._generate_prev_context(prev_arcs, preflight_result)
        prev_equipment = _extract_prev_arc_end_equipment(prev_arcs)
        forbidden_items = _extract_forbidden_item_names(preflight_result)
        if vector_context:
            prev_arc_context = f"{prev_arc_context}\n\n[과거 유사 맥락 (벡터 검색)]\n{vector_context}"

        try:
            _, all_candidates = self.ensemble.generate_ensemble(
                arc_no=arc_no,
                ep_start=ep_start,
                vol_strategy=vol_strategy,
                curr_block=curr_block,
                prev_arc_context=prev_arc_context,
                constraint_block=full_constraint_block,
                prev_equipment=prev_equipment,
                forbidden_items=forbidden_items,
                assets=assets,
                feedback=enhanced_feedback,
                protagonist_name=protagonist_name,
                protagonist_config=protagonist_config,
                entity_registry=entity_registry,
                ep_count_suggestion=ep_count_suggestion,
                pacing_signals=pacing_signals,
                retry=0,
                single_strategy=rejected_strategy,
            )
        except Exception as e:
            logging.warning(f"[Patch Mode] Arc ensemble 생성 실패: {e!s:.200}")
            return None

        if not all_candidates:
            logging.warning("[Patch Mode] Arc ensemble 후보 없음 → 폴백 필요")
            return None

        best_arc = self._check_arc_end_state(all_candidates[0])
        if prev_arcs:
            last_end = prev_arcs[-1].get("state_constraints", {}).get("arc_end_state", {})
            plan_loc = last_end.get("location") if isinstance(last_end, dict) else None
            exec_state = self._load_execution_state(prev_arcs[-1])
            forced_loc = (exec_state.get("protagonist_location") if exec_state else None) or plan_loc
            if forced_loc:
                patched_constraints = best_arc.setdefault("state_constraints", {})
                arc_start_state = patched_constraints.setdefault("arc_start_state", {})
                if not arc_start_state.get("location"):
                    arc_start_state["location"] = forced_loc
        return best_arc

    def _validate_patch_mode_candidate(
        self,
        *,
        best_arc: dict,
        prev_arcs: list[dict],
        full_constraint_block: str,
        state_tracker,
    ) -> tuple[str, dict]:
        """Patch-mode 후보를 본 검증기에 태우기 전에 선행 상태를 평탄화한다."""
        pre_items = set()
        pre_grants = set()
        for prev_arc in prev_arcs:
            prev_constraints = prev_arc.get("state_constraints", {})
            acquired = prev_constraints.get("protagonist_items") or prev_constraints.get("items_acquired", [])
            if isinstance(acquired, list):
                pre_items.update(
                    (item.get("name", item.get("item", "")) if isinstance(item, dict) else str(item)).strip()
                    for item in acquired
                    if item
                )
            grants = prev_constraints.get("grants_received", [])
            if isinstance(grants, list):
                pre_grants.update(
                    (grant.get("name", grant.get("item", "")) if isinstance(grant, dict) else str(grant)).strip()
                    for grant in grants
                    if grant
                )

        return self.validator.validate(
            arc=best_arc,
            prev_arcs=prev_arcs,
            constraints=full_constraint_block,
            state_tracker=state_tracker,
            pre_collected_items=pre_items,
            pre_collected_grants=pre_grants,
            genre=self._genre,
        )

    def _apply_patch_mode_asp_correction(
        self,
        *,
        best_arc: dict,
        arc_no: int,
        ep_start: int,
        director_feedback: str,
        adversarial_self_play,
    ) -> tuple[dict, bool]:
        """Patch-mode PASS 결과에 한해 ASP 보정을 적용한다."""
        if not adversarial_self_play or not best_arc:
            return best_arc, False

        try:
            asp_context = {
                "arc_no": arc_no,
                "ep_start": ep_start,
                "director_feedback": director_feedback,
            }
            asp_input = json.dumps(best_arc, ensure_ascii=False)
            asp_result = adversarial_self_play.generate_with_adversary(
                initial_content=asp_input,
                content_type="arc",
                context=asp_context,
            )
            asp_output = getattr(asp_result, "final_output", "") if asp_result else ""
            if asp_output:
                asp_arc = self._extract_json_robust(asp_output)
                if not isinstance(asp_arc, dict) or not asp_arc:
                    try:
                        asp_arc = json.loads(asp_output)
                    except (json.JSONDecodeError, ValueError):
                        asp_arc = {}
                if isinstance(asp_arc, dict) and asp_arc.get("tactical_doc"):
                    original_details = best_arc.get("episode_details")
                    best_arc = asp_arc
                    if original_details and not best_arc.get("episode_details"):
                        best_arc["episode_details"] = original_details
                    logging.info(f"✅ [Patch+ASP] Arc {arc_no} ASP 교정 적용")
                    return best_arc, True
        except Exception as e:
            logging.warning(f"[SilentPass:PatchMode:ASP] {e!s:.120}")

        return best_arc, False

    def _load_execution_state(self, last_arc: dict) -> dict:
        """[TF-48] 실제 에피소드 실행 결과 로드 — Arc 계획 상태와 실행 상태 간 차이 보정.

        WorldState + FactLedger + episode_bibles에서 실제 데이터를 가져와
        Arc 생성 시 정확한 상태를 전달한다.
        """
        result = {}
        try:
            _db = getattr(getattr(self.context, "current_project", None), "db", None)
            if not _db:
                return result

            # 1) WorldState — 주인공 자산, 활성 아이템, 위치
            _ws = _db.load_anchor("world_state")
            if _ws and isinstance(_ws, dict):
                _protag = _ws.get("protagonist", {})
                if isinstance(_protag, dict):
                    result["protagonist_assets"] = _protag.get("assets", {})
                    result["protagonist_location"] = _protag.get("location", "")
                    result["protagonist_status"] = _protag.get("status", {})
                _motivations = [
                    _mot
                    for _mot in (_ws.get("motivations") or [])
                    if isinstance(_mot, dict) and _mot.get("status") == "active" and _mot.get("text")
                ]
                if _motivations:
                    result["motivations"] = _motivations[:5]
                _promises = [
                    _promise
                    for _promise in (_ws.get("promises") or [])
                    if isinstance(_promise, dict)
                    and _promise.get("text")
                    and _promise.get("status") in ("pending", None, "")
                ]
                if _promises:
                    result["promises"] = _promises[:5]
                _elapsed = _ws.get("cumulative_elapsed", {})
                if isinstance(_elapsed, dict) and _elapsed.get("total_days"):
                    result["cumulative_elapsed"] = {"total_days": _elapsed.get("total_days", 0)}
                _active = _ws.get("active_items", {})
                if isinstance(_active, dict) and _active:
                    result["active_items"] = {k: v for k, v in list(_active.items())[:30]}

            # 2) FactLedger — 핵심 수치 (인물, 아이템, 자산)
            _fl = _db.load_anchor("fact_ledger")
            if _fl and isinstance(_fl, dict):
                _facts = _fl.get("numbers", {})
                if isinstance(_facts, dict):
                    _key_facts = {}
                    for _fk, _fv in list(_facts.items())[:30]:
                        if isinstance(_fv, dict):
                            _key_facts[_fk] = {
                                "value": _fv.get("value"),
                                "unit": _fv.get("unit"),
                                "established_value": _fv.get("established_value"),
                                "established_ep": _fv.get("established_ep"),
                                "last_ep": _fv.get("last_ep"),
                            }
                    if _key_facts:
                        result["fact_ledger"] = _key_facts
                _fl_summary = summarize_fact_ledger_numbers_block(
                    _fl,
                    header="[팩트 원장 핵심 수치]",
                    max_items=15,
                )
                if _fl_summary:
                    result["fact_ledger_summary"] = _fl_summary

            # 3) 최신 episode_bible — 마지막 화의 상태 변화
            _ep_end = last_arc.get("ep_end", 0)
            if _ep_end > 0:
                _eb = _db.get_episode_bible(_ep_end)
                if _eb and isinstance(_eb, dict):
                    result["last_episode_state"] = {
                        "ep_num": _eb.get("ep_num"),
                        "capital": _eb.get("capital"),
                        "total_assets": _eb.get("total_assets"),
                        "new_items": _eb.get("new_items", []),
                        "location": _eb.get("location", ""),
                    }
        except Exception as _ex:
            logging.debug("[TF-48] execution_state 로드 실패 (비치명): %s", str(_ex)[:100])
        return result

    def _collect_forgotten_npcs(self, *, before_ep: int, window: int = 10, limit: int = 5) -> list[dict]:
        """최근 N화 동안 등장하지 않은 주요 NPC를 수집한다."""
        _ctx = getattr(self, "context", None)
        _db = getattr(getattr(_ctx, "current_project", None), "db", None)
        if not _db or not hasattr(_db, "get_npc_recent_episodes"):
            return []
        if before_ep <= 1:
            return []

        _ws_anchor = {}
        try:
            if hasattr(_db, "load_anchor"):
                _ws_anchor = _db.load_anchor("world_state") or {}
        except Exception:
            _ws_anchor = {}

        _alive = _ws_anchor.get("alive_npcs", {}) if isinstance(_ws_anchor, dict) else {}
        _mb = getattr(_ctx, "master_bible", None) or {}
        _mb_root = _mb.get("MasterBible", _mb) if isinstance(_mb, dict) else {}
        _assets = _mb_root.get("AssetLibrary", {}) if isinstance(_mb_root, dict) else {}
        _key_npcs = _assets.get("KeyNPCs", []) or _assets.get("Key_NPCs", [])
        _protag_name = str((_mb_root.get("protagonist_config", {}) or {}).get("name", "") or "").strip()

        _candidate_names: list[str] = []
        for _name in _alive.keys():
            _text = str(_name or "").strip()
            if _text and _text not in _candidate_names:
                _candidate_names.append(_text)
        for _npc in _key_npcs:
            if isinstance(_npc, dict):
                _text = str(_npc.get("name", "") or "").strip()
                if _text and _text not in _candidate_names:
                    _candidate_names.append(_text)

        _forgotten: list[dict] = []
        _cutoff = max(1, before_ep - window)
        for _name in _candidate_names:
            if not _name or _name == _protag_name:
                continue
            _info = _alive.get(_name, {}) if isinstance(_alive, dict) else {}
            _first_seen = int(_info.get("first_seen_ep", 0) or 0) if isinstance(_info, dict) else 0
            if _first_seen and _first_seen >= _cutoff:
                continue
            _recent_eps = _db.get_npc_recent_episodes(_name, before_ep=before_ep, limit=1) or []
            _last_seen = int(_recent_eps[0]) if _recent_eps else _first_seen
            if _last_seen >= _cutoff:
                continue
            _role = ""
            if isinstance(_info, dict):
                _role = str(_info.get("role", "") or _info.get("role_at_intro", "") or "").strip()
            if not _role:
                for _npc in _key_npcs:
                    if isinstance(_npc, dict) and str(_npc.get("name", "") or "").strip() == _name:
                        _role = str(_npc.get("role", "") or "").strip()
                        break
            _forgotten.append(
                {
                    "name": _name,
                    "role": _role,
                    "last_seen_ep": _last_seen,
                    "first_seen_ep": _first_seen,
                }
            )

        _forgotten.sort(key=lambda item: (item.get("last_seen_ep", 0), item.get("first_seen_ep", 0), item.get("name", "")))
        return _forgotten[:limit]

    def _build_forgotten_npc_advisory(self, *, before_ep: int, window: int = 10) -> tuple[str, set[str]]:
        """Arc 설계 단계에 전달할 방치 NPC advisory."""
        _forgotten = self._collect_forgotten_npcs(before_ep=before_ep, window=window)
        if not _forgotten:
            return "", set()

        _lines = [f"[방치 NPC 주의] 최근 {window}화 이상 미등장한 주요 NPC"]
        _names: set[str] = set()
        for _entry in _forgotten:
            _name = str(_entry.get("name", "") or "").strip()
            if not _name:
                continue
            _names.add(_name)
            _last_seen = _entry.get("last_seen_ep")
            _role = str(_entry.get("role", "") or "").strip()
            _role_suffix = f", 역할={_role}" if _role else ""
            _last_seen_label = f"ep{_last_seen}" if _last_seen else "기록 없음"
            _lines.append(f"- {_name} (마지막 등장 {_last_seen_label}{_role_suffix})")
        _lines.append("이번 Arc 설계에서 관계 유지·복선 회수·재등장 필요성을 점검하라.")
        return "\n".join(_lines), _names

    def _build_dormant_promise_advisory(self, forgotten_npcs: set[str]) -> str:
        """방치 NPC와 연결된 미이행 약속/서약 advisory."""
        if not forgotten_npcs:
            return ""

        _db = getattr(getattr(self.context, "current_project", None), "db", None)
        if not _db or not hasattr(_db, "load_anchor"):
            return ""
        try:
            _ws = _db.load_anchor("world_state") or {}
        except Exception:
            return ""

        _promises = _ws.get("promises", []) if isinstance(_ws, dict) else []
        _lines = ["[방치 맹세 경고] 미이행 약속 중 당사자가 장기간 미등장"]
        _count = 0
        for _promise in _promises or []:
            if not isinstance(_promise, dict):
                continue
            if str(_promise.get("status", "pending") or "pending").strip() not in ("pending", ""):
                continue
            _promiser = str(_promise.get("promiser", "") or "").strip()
            _promisee = str(_promise.get("promisee", "") or "").strip()
            if _promiser not in forgotten_npcs and _promisee not in forgotten_npcs:
                continue
            _text = str(_promise.get("text", "") or "").strip()
            if not _text:
                continue
            _since_ep = _promise.get("since_ep")
            _parties = "→".join(x for x in (_promiser, _promisee) if x)
            _label = f"{_parties}: {_text}" if _parties else _text
            if _since_ep:
                _label += f" (ep{_since_ep}~)"
            _lines.append(f"- {_label}")
            _count += 1
            if _count >= 5:
                break
        if _count == 0:
            return ""
        _lines.append("이번 Arc에서 해당 약속의 진행·지연 사유·회수 계획을 명시하라.")
        return "\n".join(_lines)

    def _generate_prev_context(self, prev_arcs: list[dict], preflight_result: dict) -> str:
        """[V67] 이전 Arc 컨텍스트 생성 - 전문 확장 (Gemini 대용량 컨텍스트 활용)"""
        if not prev_arcs:
            return "서사 시작점 (첫 Arc)"

        last_arc = prev_arcs[-1]
        last_arc_no = last_arc.get("arc_no", "?")
        lines = []
        lines.extend(self._build_prev_context_carryover_lines(last_arc, last_arc_no))
        lines.extend(self._build_prev_context_execution_lines(last_arc))
        lines.extend(self._build_prev_context_quality_lines(last_arc, last_arc_no))
        lines.extend(self._build_prev_context_advisory_lines(prev_arcs, last_arc, last_arc_no, preflight_result))
        return "\n".join(lines)

    def _build_prev_context_carryover_lines(self, last_arc: dict, last_arc_no) -> list[str]:
        """직전 Arc 종료 상태를 다음 Arc 강제 시작 조건으로 평탄화한다."""
        lines = []
        state = last_arc.get("state_constraints", {})
        arc_end = state.get("arc_end_state", {})
        joint = last_arc.get("joint_docs", {})
        shadow = last_arc.get("status_shadow", {})

        raw_energy = arc_end.get("internal_energy")
        if raw_energy is None:
            loss_str = shadow.get("internal_energy_loss", "0%")
            try:
                match = re.search(r"(\d+)", str(loss_str))
                loss = int(match.group(1)) if match else 0
                raw_energy = max(0, 100 - loss)
            except Exception:
                raw_energy = Stage2Limits.INTERNAL_ENERGY_FALLBACK

        if self._genre == "wuxia":
            final_energy = max(90, int(raw_energy) if isinstance(raw_energy, (int, float)) else 100)
            if isinstance(raw_energy, (int, float)) and raw_energy < final_energy:
                logging.info(f" [V62.2] 내공 자연 회복: {int(raw_energy)}% → {final_energy}% (아크 간 휴식)")
        else:
            final_energy = None

        final_injuries = self._sanitize_injuries(arc_end.get("injuries") or "없음")
        final_location = arc_end.get("location") or joint.get("final_location", "알 수 없음")
        final_location = _trim_location(final_location)
        final_equipment = arc_end.get("equipment")
        if final_equipment is None:
            final_equipment = joint.get("physical_inventory", [])
        if isinstance(final_equipment, str):
            final_equipment = [item.strip() for item in final_equipment.split(",") if item.strip()]

        lines.append("=" * 50)
        lines.append(f"🔴 [Arc {last_arc_no} 종료 상태 → 다음 Arc 필수 시작 조건]")
        lines.append("=" * 50)
        if final_energy is not None:
            lines.append(f"✅ 내공: {final_energy}%")
        lines.append(f"✅ 부상: {final_injuries}")
        lines.append(f"✅ 위치: {final_location}")
        lines.append(f"✅ 소지품: {final_equipment}")
        capital = arc_end.get("capital")
        total_assets = arc_end.get("total_assets")
        portfolio = arc_end.get("portfolio_position")
        if capital or total_assets or portfolio:
            lines.append(f"✅ 자본금: {capital or '미기재'}")
            lines.append(f"✅ 총자산: {total_assets or '미기재'}")
            lines.append(f"✅ 포지션: {portfolio or '미기재'}")
        lines.append("=" * 50)
        lines.append("")
        return lines

    def _build_prev_context_execution_lines(self, last_arc: dict) -> list[str]:
        """DB 실행 상태를 Arc 계획보다 높은 우선순위의 carryover block으로 붙인다."""
        lines = []
        execution_state = self._load_execution_state(last_arc)
        if not execution_state:
            return lines

        lines.append("=" * 50)
        lines.append("⚠️ [TF-48] 실제 에피소드 실행 결과 (Arc 계획보다 우선)")
        lines.append("다음 Arc 설계 시 아래 실행 결과를 반드시 참조하라.")
        lines.append("=" * 50)
        assets = execution_state.get("protagonist_assets", {})
        if assets:
            for asset_key, asset_value in assets.items():
                lines.append(f"  💰 {asset_key}: {asset_value}")
        status = execution_state.get("protagonist_status", {})
        if status:
            for status_key, status_value in status.items():
                lines.append(f"  📊 {status_key}: {status_value}")
        protagonist_location = execution_state.get("protagonist_location")
        if protagonist_location:
            lines.append(f"  📍 실제 위치: {protagonist_location}")
        elapsed = execution_state.get("cumulative_elapsed", {})
        if isinstance(elapsed, dict) and elapsed.get("total_days"):
            lines.append(f"  ⏱️ 누적 경과: 총 {elapsed.get('total_days')}일")

        motivations = execution_state.get("motivations", [])
        if motivations:
            motivation_lines = []
            for motivation in motivations[:5]:
                text = str(motivation.get("text", "") or "").strip()
                if not text:
                    continue
                since_ep = motivation.get("since_ep")
                motivation_lines.append(f"{text} (ep{since_ep}~)" if since_ep else text)
            if motivation_lines:
                lines.append(f"  🎯 핵심 동기: {'; '.join(motivation_lines)}")

        promises = execution_state.get("promises", [])
        if promises:
            promise_lines = []
            for promise in promises[:5]:
                text = str(promise.get("text", "") or "").strip()
                if not text:
                    continue
                promiser = str(promise.get("promiser", "") or "").strip()
                promisee = str(promise.get("promisee", "") or "").strip()
                parties = "→".join(item for item in [promiser, promisee] if item)
                since_ep = promise.get("since_ep")
                label = f"{parties}: {text}" if parties else text
                if since_ep:
                    label += f" (ep{since_ep}~)"
                promise_lines.append(label)
            if promise_lines:
                lines.append(f"  🤝 미이행 약속: {'; '.join(promise_lines)}")

        last_episode_state = execution_state.get("last_episode_state", {})
        if last_episode_state:
            capital = last_episode_state.get("capital")
            total_assets = last_episode_state.get("total_assets")
            ep_no = last_episode_state.get("ep_num")
            if capital is not None or total_assets is not None:
                lines.append(f"  📋 제{ep_no}화 종료 기준: 자본금={capital}, 총자산={total_assets}")
            new_items = last_episode_state.get("new_items", [])
            if new_items:
                lines.append(f"  🆕 제{ep_no}화 신규 아이템: {new_items}")

        fact_ledger_summary = str(execution_state.get("fact_ledger_summary", "") or "").strip()
        if fact_ledger_summary:
            fact_lines = fact_ledger_summary.splitlines()
            lines.append(f"  📖 {fact_lines[0]}")
            for fact_line in fact_lines[1:]:
                lines.append(f"     {fact_line}")
        else:
            fact_ledger = execution_state.get("fact_ledger", {})
            if fact_ledger:
                fact_lines = []
                for fact_key, fact_value in list(fact_ledger.items())[:15]:
                    unit = str(fact_value.get("unit", "") or "").strip()
                    unit_suffix = f" {unit}" if unit else ""
                    established_value = fact_value.get("established_value")
                    established_ep = fact_value.get("established_ep", "?")
                    current_value = fact_value.get("value")
                    last_ep = fact_value.get("last_ep")
                    if established_value not in ("", None) and str(established_value) != str(current_value):
                        fact_lines.append(
                            f"{fact_key}={established_value}{unit_suffix}(ep{established_ep})->"
                            f"{current_value}{unit_suffix}(ep{last_ep})"
                        )
                    else:
                        fact_lines.append(f"{fact_key}={current_value}{unit_suffix} (ep{last_ep})")
                if fact_lines:
                    lines.append(f"  📖 팩트원장: {'; '.join(fact_lines)}")

        active_items = execution_state.get("active_items", {})
        if active_items:
            active_item_names = list(active_items.keys())[:20]
            lines.append(f"  🎒 활성 아이템: {', '.join(active_item_names)}")
        lines.append("=" * 50)
        lines.append("")
        return lines

    def _build_prev_context_quality_lines(self, last_arc: dict, last_arc_no) -> list[str]:
        """FailureAnalyzer/최근 reject/품질 추세를 다음 Arc prompt advisory로 압축한다."""
        lines = []
        before_ep = int(last_arc.get("ep_end", 0) or 0) + 1
        forgotten_advisory, forgotten_names = self._build_forgotten_npc_advisory(before_ep=before_ep, window=10)
        if forgotten_advisory:
            lines.append(forgotten_advisory)
            lines.append("")

        promise_advisory = self._build_dormant_promise_advisory(forgotten_names)
        if promise_advisory:
            lines.append(promise_advisory)
            lines.append("")

        context = getattr(self, "context", None)
        db = getattr(getattr(context, "current_project", None), "db", None)
        if not db:
            return lines

        try:
            arc_rejects = db.get_stage_attempts_for_arc(
                int(last_arc_no) if str(last_arc_no).isdigit() else 0,
                stages=(3, 4),
                verdict="REJECT",
                limit=20,
            )
            if arc_rejects:
                category_counts: dict[str, int] = {}
                reason_samples: list[str] = []
                for row in arc_rejects:
                    category = str(row.get("failure_category", "") or "uncategorized").strip()
                    category_counts[category] = category_counts.get(category, 0) + 1
                    reason = str(row.get("reject_reason", "") or "").strip()
                    if reason and reason not in reason_samples:
                        reason_samples.append(reason[:90])
                top_categories = sorted(category_counts.items(), key=lambda item: item[1], reverse=True)[:3]
                lines.append("[직전 Arc Stage3/4 주요 실패]")
                if top_categories:
                    lines.append("실패 카테고리: " + ", ".join(f"{name}({count})" for name, count in top_categories))
                if reason_samples:
                    lines.append("대표 reject 사유:")
                    for reason in reason_samples[:3]:
                        lines.append(f"- {reason}")
                lines.append("")
        except Exception as reject_err:
            logging.debug("[QI-FL-2] stage_attempts Arc 소비 실패 (비치명): %s", reject_err)

        try:
            analyzer = FailureAnalyzer(db)
            failure_summary = analyzer.summary()
            stage4_stats = (failure_summary.get("stage_pass_rates") or {}).get("stage_4", {})
            top_agents = failure_summary.get("top_failed_agents") or []
            top_failures = failure_summary.get("top_failure_categories") or []
            quality_distribution = failure_summary.get("quality_distribution") or {}
            if stage4_stats or top_agents or top_failures or quality_distribution:
                lines.append("[이전 Arc 실패 분석]")
                if stage4_stats:
                    lines.append(
                        f"Stage4 pass_rate={stage4_stats.get('pass_rate_pct', 0)}% "
                        f"(시도 {stage4_stats.get('total_attempts', 0)}회)"
                    )
                if top_failures:
                    lines.append(
                        "주요 실패 원인: "
                        + ", ".join(
                            f"{item.get('category', '?')}({item.get('count', 0)})" for item in top_failures[:3]
                        )
                    )
                if top_agents:
                    agent = top_agents[0]
                    lines.append(
                        f"실패 빈도 상위 에이전트: {agent.get('agent', '?')} "
                        f"({int(agent.get('fail_rate_pct', 0))}% 실패)"
                    )
                if quality_distribution:
                    lines.append(
                        f"최근 품질 분포: 평균 {quality_distribution.get('avg_score', 0)}점, "
                        f"고득점 {quality_distribution.get('high_score_count', 0)}건"
                    )
                lines.append("")

            success_patterns = failure_summary.get("top_success_patterns") or analyzer.top_success_patterns(top_n=2)
            if success_patterns:
                lines.append("[직전 Arc 고득점 패턴]")
                for pattern in success_patterns[:2]:
                    lines.append(f"- {pattern.get('description', '')}")
                lines.append("")
        except Exception as fa_err:
            logging.debug("[QI-FL-3/4] FailureAnalyzer 소비 실패 (비치명): %s", fa_err)

        try:
            score_rows = db.get_recent_episode_scores(before_ep=before_ep, lookback=5)
            scores = []
            for row in score_rows:
                try:
                    scores.append(int(row.get("score", 0) or 0))
                except (TypeError, ValueError):
                    continue
            if len(scores) >= 3:
                trend_lines = []
                if all(scores[index] > scores[index + 1] for index in range(len(scores) - 1)):
                    trend_lines.append(f"최근 {len(scores)}화 연속 하락 ({scores[0]}→{scores[-1]})")
                avg_score = round(sum(scores) / len(scores), 1)
                if avg_score < 80:
                    trend_lines.append(f"최근 평균 {avg_score}점으로 저하")
                if trend_lines:
                    lines.append("[품질 추세 경고]")
                    lines.extend(f"- {line}" for line in trend_lines)
                    lines.append("")
        except Exception as trend_err:
            logging.debug("[QI-FL-5] 품질 추세 Arc 전달 실패 (비치명): %s", trend_err)

        return lines

    def _build_prev_context_advisory_lines(
        self,
        prev_arcs: list[dict],
        last_arc: dict,
        last_arc_no,
        preflight_result: dict,
    ) -> list[str]:
        """world/preflight/state_changes/tactical-doc history/time advisory를 후반부에 붙인다."""
        lines = []
        world = preflight_result.get("world_state", {})
        conflicts = world.get("ongoing_conflicts", [])
        if conflicts:
            lines.append(f"진행 중인 갈등: {', '.join(str(conflict) for conflict in conflicts[:3])}")

        resolved_conflicts = world.get("resolved_conflicts", [])
        if resolved_conflicts:
            lines.append(f"완결된 갈등 (재생성 금지): {', '.join(str(item) for item in resolved_conflicts[:5])}")

        relationships = preflight_result.get("relationship_map", {})
        if relationships:
            relationship_summary = ", ".join(
                f"{name}: {value.get('current_state', '?')}" for name, value in list(relationships.items())[:5]
            )
            lines.append(f"주요 관계: {relationship_summary}")

        state_changes = last_arc.get("state_changes", {})
        if isinstance(state_changes, dict):
            deaths = state_changes.get("npc_deaths", [])
            if deaths:
                names = [
                    item.get("name", item.get("npc", str(item))) if isinstance(item, dict) else str(item)
                    for item in deaths[:10]
                ]
                lines.append(f"\n🚫 사망 NPC (부활 금지): {', '.join(names)}")

            skills = state_changes.get("skill_acquisitions", [])
            if skills:
                names = [
                    item.get("name", item.get("skill", str(item))) if isinstance(item, dict) else str(item)
                    for item in skills[:10]
                ]
                lines.append(f"⚔️ 습득 기술: {', '.join(names)}")

            resolved_plots = state_changes.get("resolved_plots", [])
            if resolved_plots:
                names = [
                    item.get("plot", item.get("description", str(item))) if isinstance(item, dict) else str(item)
                    for item in resolved_plots[:10]
                ]
                lines.append(f"🚫 완결된 플롯 (재생성 금지): {', '.join(names)}")

            permanent_injuries = state_changes.get("permanent_injuries", [])
            if permanent_injuries:
                descriptions = [
                    str(item)[:50] if not isinstance(item, dict) else item.get("description", str(item))[:50]
                    for item in permanent_injuries[:5]
                ]
                lines.append(f"🩹 영구 부상: {', '.join(descriptions)}")

            companion_changes = state_changes.get("companion_changes", [])
            if companion_changes:
                descriptions = [
                    str(item)[:50] if not isinstance(item, dict) else item.get("name", str(item))[:30]
                    for item in companion_changes[:5]
                ]
                lines.append(f"👥 동행자 변경: {', '.join(descriptions)}")

        prev_start = max(0, len(prev_arcs) - 30)
        arc_history_lines = []
        for prev_arc in prev_arcs[prev_start:]:
            prev_arc_no = prev_arc.get("arc_no", "?")
            prev_ep_start = prev_arc.get("ep_start", "?")
            prev_ep_end = prev_arc.get("ep_end", "?")
            tactical_doc = prev_arc.get("tactical_doc", "")
            if isinstance(tactical_doc, dict):
                tactical_doc = json.dumps(tactical_doc, ensure_ascii=False)
            if tactical_doc:
                arc_history_lines.append(f"━━━ Arc {prev_arc_no} (제{prev_ep_start}화~제{prev_ep_end}화) ━━━\n{tactical_doc}")
        if arc_history_lines:
            full_history = "\n\n".join(arc_history_lines)
            if len(full_history) > ContextLimits.MAX_CONTEXT_CHARS:
                full_history = full_history[: ContextLimits.MAX_CONTEXT_CHARS] + "\n... (200K자 절삭)"
            lines.append("")
            lines.append(f"[V67] ═══ 이전 Arc 전술서 전문 ({len(arc_history_lines)}개) ═══")
            lines.append(full_history)
            logging.info(
                f" [V67] FourPhase prev_context 확장: {len(arc_history_lines)}개 Arc 전술서 ({len(full_history):,}자)"
            )

        try:
            ns4_markers = _ns4_extract_time_markers(last_arc)
            if ns4_markers:
                lines.append("")
                lines.append(
                    f"⏱️ [NS-4] 이전 Arc {last_arc_no} 시간 마커: {', '.join(ns4_markers)}\n"
                    "※ 이번 Arc tactical_doc에 '이전 Arc 종료로부터 X달/주 후 시작'을 명시하세요."
                )
        except Exception as ns4_err:
            logging.debug("[NS-4-S2] 시간 마커 주입 실패 (비차단): %s", ns4_err)

        project = getattr(getattr(self, "context", None), "current_project", None)
        db = getattr(project, "db", None) if project else None
        timeline_lines = _build_extended_timeline_advisory(db)
        if timeline_lines:
            lines.append("")
            lines.extend(timeline_lines)
        return lines

    # ──────────────────────────────────────────────
    # [V62.2] Injury Escalation Guard
    # 부상 자기강화 루프 차단: 만성질환/에스컬레이션 필터
    # ──────────────────────────────────────────────
    CHRONIC_INJURY_KEYWORDS = [
        "성대 결절",
        "성대결절",
        "실명",
        "마비",
        "불구",
        "절단",
        "암",
        "종양",
        "만성",
        "대화 불가",
        "말 못함",
        "목소리 상실",
        "청력 상실",
        "시력 상실",
        "반신불수",
        "전신 탈진",
        "코피",
    ]

    def _sanitize_injuries(self, raw: str) -> str:
        """[V62.2] 이전 Arc → 다음 Arc 전파 시 부상은 항상 '없음'.
        소설 세계관: 아크 간 시간 경과로 자연 치유 가정 (힐링팩터).
        """
        if not raw or raw.strip() in ("없음", "정상", ""):
            return "없음"
        logging.info(f" [V62.2] 자연 치유: '{raw[:50]}' → '없음' (아크 간 회복)")
        return "없음"

    def _check_arc_end_state(self, arc: dict) -> dict:
        """[I-12] 아크 종료 상태 점검 (advisory only — 대원칙 #1 준수).

        자동 덮어쓰기 대신 WARNING 로깅으로 LLM에 판단을 위임합니다.
        부상 회복 여부, 내공 복원 여부는 LLM이 아크 생성 시 결정합니다.
        """
        warnings = []

        sc = arc.get("state_constraints", {})
        end_state = sc.get("arc_end_state", {})
        if isinstance(end_state, dict):
            inj = str(end_state.get("injuries", "없음"))
            if inj not in ("없음", "정상", ""):
                warnings.append(f"부상 미회복: '{inj}' (아크 간 자연 치유 고려)")
            # [ARC-NOISE-1] 내공(internal_energy)은 무협/헌터/판타지 장르만 해당
            _energy_genres = {"wuxia", "hunter", "fantasy"}
            energy = end_state.get("internal_energy")
            if isinstance(energy, (int, float)) and energy < 100 and self._genre in _energy_genres:
                warnings.append(f"내공 미복원: {energy}% (아크 간 회복 고려)")

        ss = arc.get("status_shadow", {})
        if isinstance(ss, dict):
            ei = str(ss.get("expected_injuries", "없음"))
            if ei not in ("없음", "정상", ""):
                # [NR-1] 정신적 피로는 자연 회복 가능 — advisory 레벨 낮춤
                _mental_keywords = ("정신", "마모", "스트레스", "피로", "mental", "fatigue", "burnout")
                _is_mental = any(k in ei.lower() for k in _mental_keywords)
                if _is_mental:
                    warnings.append(f"status_shadow 정신적 피로 잔류: '{ei}' (일상 휴식으로 자연 회복 가능)")
                else:
                    warnings.append(f"status_shadow 부상 잔류: '{ei}'")

        if warnings:
            logging.warning(f"[I-12] 아크 종료 상태 점검: {warnings}")

        return arc

    def get_stats(self) -> dict:
        """통계 반환"""
        total = self.stats["total_attempts"]
        if total == 0:
            return self.stats

        return {**self.stats, "pass_rate": f"{(self.stats['phase3_pass'] / total * 100):.1f}%" if total > 0 else "N/A"}

    def print_stats(self) -> None:
        """통계 출력"""
        stats = self.get_stats()
        logging.info("\n[ThreePhaseArcGenerator 통계]")
        logging.info(f"총 시도: {stats['total_attempts']}")
        logging.info(f"Phase 1 완료: {stats['phase1_complete']}")
        logging.info(f"Phase 2 완료: {stats['phase2_complete']}")
        logging.info(f"Phase 3 PASS: {stats['phase3_pass']}")
        logging.warning(f"Phase 3 REJECT: {stats['phase3_reject']}")
        logging.info(f"최종 통과율: {stats.get('pass_rate', 'N/A')}")


def create_four_phase_generator(
    context,
    client,
    model_tier: str = AIModels.DEFAULT_ARCHITECT,
    flash_ask: Callable[[str], str] | None = None,
):
    """FourPhaseArcGenerator 생성 헬퍼 (호환성 유지)"""
    return FourPhaseArcGenerator(context, client, model_tier, flash_ask=flash_ask)
