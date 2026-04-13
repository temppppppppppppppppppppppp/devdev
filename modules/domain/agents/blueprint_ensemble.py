"""
utf8-hygiene: allow-file -- legacy Korean prompt text in this generator predates the structured carryover patch.
[V60.80] Blueprint Ensemble Generator
병렬로 3개 Blueprint 후보 생성 후 최적 선택

전략:
- Strategy A: 액션 중심 (긴장도 높음, 전투/추격/대결)
- Strategy B: 감정 중심 (캐릭터 심리, 갈등/화해/성장)
- Strategy C: 대화 중심 (관계 발전, 정보 교환, 음모)

내부적으로 Two-Phase 방식 적용:
1. 구조 생성 (scene_breakdown)
2. 상세화 (integrated_scenario)
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import TimeoutError as FutureTimeoutError

from modules.core.constants import AIModels, GenreTypes, smart_truncate
from modules.core.hud_utils import build_hud_context as _build_hud_context_shared
from modules.core.project_support import normalize_external_pov_insert_policy
from modules.core.prompt_loader import PromptLoader
from modules.core.response_schemas import (
    BLUEPRINT_ENSEMBLE_MIN_INTEGRATED_SCENARIO_CHARS,
    BLUEPRINT_OPENING_TRANSITION_TYPES,
    BLUEPRINT_SCHEMA,
)
from modules.core.scene_obligation_heuristics import has_actionable_obligation_text, has_meaningful_state_value
from modules.core.stage_cross_stage_contract import (
    apply_opening_transition_contract,
    read_declared_opening_transition_type,
)
from modules.core.tactical_utils import extract_episode_tactical

from .base_agent import _SYSTEM_CFG, AgentErrorType, BaseAgent
from .scene_cardinality_contract import evaluate_stage3_scene_cardinality

# [V60.95] 원시인 모드 금지어 Guard (JSON 기반)
try:
    from modules.core.primitive_guard import get_primitive_constraint_section

    PRIMITIVE_GUARD_AVAILABLE = True
except ImportError:
    PRIMITIVE_GUARD_AVAILABLE = False


# Blueprint 생성 전략
BLUEPRINT_STRATEGIES = [
    {
        "name": "action_focused",
        "display": "액션 중심",
        "directive": """
[전략: 액션 중심]
- 긴장도를 높게 유지하세요 (7-9/10)
- 전투, 추격, 대결 씬을 중심으로 구성하세요
- 빠른 템포와 역동적인 전개를 강조하세요
- 감정 묘사는 최소화하고 행동으로 보여주세요
- [QI-1-A6] ending_hook은 물리적 위기/액션 클리프행어로 끝낼 것
""",
        "tension_range": (7, 9),
    },
    {
        "name": "emotion_focused",
        "display": "감정 중심",
        "directive": """
[전략: 감정 중심]
- 캐릭터의 내면 심리를 깊이 있게 다루세요
- 갈등, 화해, 성장의 순간을 부각하세요
- 대화 속 감정의 미묘한 변화를 묘사하세요
- 긴장도는 중간 수준으로 유지하세요 (4-6/10)
- [QI-1-A6] ending_hook은 감정적 반전/내면 갈등 여운으로 끝낼 것
""",
        "tension_range": (4, 6),
    },
    {
        "name": "dialogue_focused",
        "display": "대화 중심",
        "directive": """
[전략: 대화 중심]
- 캐릭터 간 대화를 통해 이야기를 전개하세요
- 정보 교환, 음모, 협상 씬을 중심으로 구성하세요
- 대사를 통해 캐릭터 성격과 관계를 드러내세요
- 서브텍스트(말 속에 숨겨진 의미)를 활용하세요
- [QI-1-A6] ending_hook은 대사 중단/대화 반전으로 끝낼 것
""",
        "tension_range": (3, 7),
    },
]

AI_TELL_BLUEPRINT_GUARDRAIL = """
[AI 티 회피 지침]
- Blueprint는 downstream scene authority이지 브리핑 문서나 회차 요약문이 아닙니다.
- integrated_scenario에 독자 대상 설명문, recap, 메타 해설을 끼워 넣지 마세요.
- 상태창/HUD/시스템 메시지/홀로그램 같은 게임식 UI를 정본 근거 없이 새로 발명하지 마세요.
- 장면 말미를 설명문으로 기계적으로 요약하지 마세요.
- 감정 반응을 상투적인 반응구 반복으로 처리하지 말고 행동·대사·구체 감각으로 드러내세요.
- 정보 전달만 수행하는 대사가 길게 이어지지 않게 하세요.
- 매 씬의 도입과 종결 리듬을 같게 반복하지 마세요.
- 독자가 "익숙한 AI 문장"이라고 느낄 만한 접속구·감탄구 남용을 피하세요.
"""

_BLUEPRINT_SYSTEM_UI_MARKERS = tuple(
    marker.casefold()
    for marker in (
        "HUD",
        "상태창",
        "상태 창",
        "status window",
        "홀로그램 창",
        "홀로그램",
        "hologram window",
        "퀘스트 창",
        "퀘스트",
        "quest window",
        "알림창",
        "notification window",
        "시스템 메시지",
        "system message",
        "스탯창",
        "스테이터스 창",
        "[👤",
        "[💰",
        "[🎯",
        "[HP",
        "[MP",
        "[LV",
        "[SYSTEM",
    )
)

_BLUEPRINT_META_RECAP_MARKERS = tuple(
    marker.casefold()
    for marker in (
        "직전 화",
        "이전 화",
        "이번 화",
        "이번 에피소드",
    )
)

_TACTICAL_INTRUSION_ENTRY_MARKERS = (
    "취객",
    "난입",
    "들이닥",
    "무단침입",
    "괴한",
    "습격",
    "침입자",
    "철문",
    "그림자",
    "심부름센터",
    "직원",
)

_TACTICAL_INTRUSION_CONFLICT_MARKERS = (
    "멱살",
    "결박",
    "제압",
    "처리",
    "대응",
    "차단",
    "쫓아낸",
    "도망치",
    "위협",
    "협박",
    "박살",
    "쇠파이프",
    "쇠지렛대",
    "군화",
)


# [V60.98] 씬 프리셋 정의 - 장면/화자 전환 연출
SCENE_PRESETS = {
    "opening_hook": "화 시작, 독자 유입용. 시각 중심, 임팩트 있는 오프닝.",
    "daily_routine": "일상 묘사, 세계관 노출. 여유로운 호흡.",
    "tension_build": "긴장감 축적. 불안한 분위기, 짧은 문장.",
    "action_peak": "전투/액션 클라이맥스. 빠른 호흡, 시각 중심, 대사 최소.",
    "emotional_reveal": "감정 폭발, 내면 묘사. 느린 호흡, 대사/독백 중심.",
    "dialogue_duel": "설전/협상/대립. 대사 중심, 긴장감 있는 대화.",
    "villain_scheme": "★악역 시점 전환★ 음모/계략 노출. 독자에게 위협 암시.",
    "side_glimpse": "★조연 시점 전환★ 주인공 부재 상황, '저 사람 대단해!' 반응.",
    "flashback": "과거 회상. 몽환적 전환, 과거 시제.",
    "omniscient_hint": "★전지적 시점★ 복선/떡밥 암시. '그는 아직 몰랐다...'",
    "cliffhanger": "화 끝 훅. 급박한 전개, 긴장 최고조에서 끊기.",
    "resolution": "갈등 해소, 정리. 여운 있는 마무리.",
}


def build_external_pov_policy_constraint(primary_pov: str, external_pov_insert_policy: str, *, genre: str = "") -> str:
    pov = str(primary_pov or "").strip()
    policy = normalize_external_pov_insert_policy(external_pov_insert_policy, primary_pov=pov, genre=genre)

    if pov == "1인칭":
        if policy == "금지":
            return """### [V-POV] 외부 시점 삽입 정책: 금지
- 주인공 부재 장면 금지
- villain_scheme, side_glimpse, omniscient_hint 프리셋 사용 금지
- 모든 씬은 주인공이 직접 관찰/행동 가능한 범위 안에서만 설계"""
        if policy == "제한적 허용":
            return """### [V-POV] 외부 시점 삽입 정책: 제한적 허용
- 기본은 1인칭 유지
- side_glimpse만 씬 전환(***) 뒤 1회성 짧은 반응 컷으로 허용
- villain_scheme, omniscient_hint는 사용 금지
- 외부 시점 컷이 본편 POV를 대체하지 않게 설계"""
        return """### [V-POV] 외부 시점 삽입 정책: 적극 허용
- 기본은 1인칭 유지하되, 씬 전환(***) 뒤 외부 시점 컷을 전략적으로 허용
- side_glimpse, villain_scheme, omniscient_hint를 짧은 삽입 컷으로만 사용
- 동일 씬 내부 시점 혼합은 금지"""

    if pov == "3인칭":
        if policy == "금지":
            return """### [V-POV] 외부 시점 삽입 정책: 금지
- 주인공 중심 3인칭만 유지
- villain_scheme, side_glimpse, omniscient_hint 프리셋 사용 금지"""
        if policy == "제한적 허용":
            return """### [V-POV] 외부 시점 삽입 정책: 제한적 허용
- villain_scheme, side_glimpse는 씬 전환(***) 뒤 짧게만 사용 (1-2문단)
- omniscient_hint는 화당 1회 이내로 제한
- 외부 시점은 반응/위협 암시/정보 경제에만 사용"""
        return """### [V-POV] 외부 시점 삽입 정책: 적극 허용
- 3인칭 본류를 유지하되 외부 시점 컷을 scene-level로 허용
- villain_scheme, side_glimpse, omniscient_hint를 아크 흐름에 맞춰 사용
- 같은 장면 안에서 시점을 뒤섞지 말고 씬 경계(***)를 명확히 둘 것"""

    if pov == "전지적":
        if policy == "금지":
            return """### [V-POV] 외부 시점 삽입 정책: 금지
- 전지적 서술은 허용하되 별도 외부 POV 프리셋은 사용 금지
- 시점 전환 효과를 남용하지 말고 핵심 서술자 관점을 유지"""
        if policy == "제한적 허용":
            return """### [V-POV] 외부 시점 삽입 정책: 제한적 허용
- 전지적 서술을 본류로 유지
- side_glimpse, villain_scheme, omniscient_hint는 장면 효과용으로만 절제 사용"""
        return """### [V-POV] 외부 시점 삽입 정책: 적극 허용
- 전지적 서술을 기반으로 scene-level 외부 POV 컷을 자유롭게 설계 가능
- 단, 과도한 빈도와 중복 설명은 금지"""

    if pov == "혼합":
        if policy == "금지":
            return """### [V-POV] 혼합 시점 + 외부 시점 금지
- 혼합은 허용하되 외부 반응 컷/악역 컷/전지적 힌트 프리셋은 사용 금지
- 선택된 시점 전환 외 추가 삽입 컷을 넣지 말 것"""
        if policy == "제한적 허용":
            return """### [V-POV] 혼합 시점 + 제한적 외부 시점
- scene-level switching은 허용
- 외부 삽입 컷은 reaction/foreshadowing 용도로만 제한 사용
- 같은 씬 내부 시점 혼합은 금지"""
        return """### [V-POV] 혼합 시점 + 적극적 외부 시점
- 혼합 시점 작품으로 설계하되 scene 경계를 명확히 둘 것
- side_glimpse, villain_scheme, omniscient_hint를 전략적으로 사용할 수 있음
- 동일 씬 내부 시점 혼합과 불필요한 churn은 금지"""

    return ""


def _fit_compact_context(value: object, max_chars: int, *, head_ratio: float = 0.55) -> str:
    raw = str(value or "")
    if len(raw) <= max_chars:
        return raw
    head_chars = max(0, min(int(max_chars * head_ratio), max_chars - 80))
    return smart_truncate(raw, max_chars=max_chars, head_chars=head_chars)


def _append_constraint_section(lines: list[str], header: str, band_lines: list[str]) -> None:
    if not band_lines:
        return
    lines.append(header)
    lines.extend(band_lines)
    lines.append("")


class BlueprintEnsembleGenerator(BaseAgent):
    """
    [V60.80] Blueprint Ensemble Generator

    병렬로 3개 Blueprint 후보 생성 후 최적 선택
    """

    # [V61.3→TF-26] 앙상블 타임아웃 — system.yaml ensemble_timeouts.blueprint 참조
    _TIMEOUTS = _SYSTEM_CFG.get("ensemble_timeouts", {}).get("blueprint", {})
    ENSEMBLE_TIMEOUT = _TIMEOUTS.get("ensemble", 300)
    SINGLE_CANDIDATE_TIMEOUT = _TIMEOUTS.get("single", 240)

    def __init__(self, context, client, model_tier: str = None):
        super().__init__(context, client, model_tier)
        self._prompt_loader = PromptLoader()
        self.strategies = BLUEPRINT_STRATEGIES
        self.max_workers = 3
        self.last_error_types: list[str] = []

    @staticmethod
    def _select_generate_error_type(error_types: list[str]) -> str | None:
        """Collapse worker failures into one fast-fail hint for the caller."""
        if not error_types:
            return None
        if AgentErrorType.SCHEMA_INCOMPATIBLE in error_types:
            return AgentErrorType.SCHEMA_INCOMPATIBLE
        non_unknown = [error_type for error_type in error_types if error_type and error_type != AgentErrorType.UNKNOWN]
        if non_unknown:
            return non_unknown[0]
        return error_types[0]

    def _resolve_blueprint_arc_focus(self, ep_num: int, arc_data: dict, constraint_block: dict) -> str:
        arc_focus = constraint_block.get("must_focus", {}).get("content", "")
        if not arc_focus:
            # Stage3 producer-input 전용: tactical_doc shadowing 방지를 위해 prefer_full_doc 모드 사용.
            # episode_details bullet TL;DR과 per-episode tactical_doc slice를 함께 결합한다.
            # 다른 12개 호출자(Stage4/Director/continuity/ToT/prompt_builder 등)는 default(False)를 유지.
            arc_focus = extract_episode_tactical(
                arc_data.get("tactical_doc", ""),
                ep_num,
                episode_details=arc_data.get("episode_details"),
                prefer_full_doc=True,
            )

        episode_details = arc_data.get("episode_details") or []
        if isinstance(episode_details, list):
            for item in episode_details:
                if isinstance(item, dict) and item.get("ep_num") == ep_num:
                    details = item.get("details") or []
                    if isinstance(details, list) and details:
                        detail_text = "\n".join(f"  - {detail}" for detail in details if isinstance(detail, str))
                        arc_focus = f"[{ep_num}화 추가 사건 (Arc 단계 보강)]\n{detail_text}\n\n{arc_focus}"
                    break

        return smart_truncate(
            arc_focus,
            max_chars=15000,
            head_chars=max(0, min(int(15000 * 0.55), 15000 - 80)),
        )

    def _resolve_blueprint_ensemble_genre(self) -> str:
        genre = GenreTypes.WUXIA
        try:
            if hasattr(self, "context") and hasattr(self.context, "db"):
                bible = self.context.db.load_anchor("bible")
                if bible:
                    genre = bible.get("_genre", GenreTypes.WUXIA)
        except Exception as exc:
            logging.warning(f" [V61.3] genre 사전 로드 실패: {str(exc)[:50]}")
        return genre

    def _prepare_blueprint_ensemble_context(
        self,
        *,
        ep_num: int,
        arc_data: dict,
        constraint_block: dict,
        prev_blueprint: dict | None,
        prev_blueprints: list[dict] | None,
        prev_manuscripts_text: str,
        state_tracker,
    ) -> dict:
        arc_focus = self._resolve_blueprint_arc_focus(ep_num, arc_data, constraint_block)
        genre = self._resolve_blueprint_ensemble_genre()
        constraints_str = self._format_constraints(constraint_block, genre=genre)
        must_focus = constraint_block.get("must_focus", {}) if isinstance(constraint_block, dict) else {}
        tactical_excerpt = str(must_focus.get("content", "") or "").strip() if isinstance(must_focus, dict) else ""
        if not tactical_excerpt:
            tactical_excerpt = str(arc_focus or "").strip()
        prev_info = self._format_prev_info_expanded(prev_blueprint, prev_blueprints, prev_manuscripts_text)
        hud_context = self._build_hud_context(state_tracker, ep_num)

        try:
            guard = getattr(self.context, "guard", None)
            if guard and hasattr(guard, "get_retrieval_contract_prompt"):
                guard.get_retrieval_contract_prompt("blueprint")
        except Exception as exc:
            logging.debug("[BPEnsemble] work retrieval contract 로드 실패: %s", exc)

        shared_context = f"{constraints_str or ''}\n\n{arc_focus or ''}\n\n{prev_info or ''}\n\n{hud_context or ''}"
        cache_info = self._get_or_create_context_cache(
            cache_type="blueprint_ensemble",
            content=shared_context,
            ttl_seconds=600,
            project_name=self._context_cache_project_namespace("ep", ep_num),
        )
        return {
            "arc_focus": arc_focus,
            "genre": genre,
            "constraints_str": constraints_str,
            "tactical_excerpt": tactical_excerpt,
            "prev_info": prev_info,
            "hud_context": hud_context,
            "cache_name": cache_info.get("cache_name"),
        }

    def _select_blueprint_ensemble_strategies(self, single_strategy: str) -> list[dict]:
        if not single_strategy:
            return self.strategies

        filtered = [strategy for strategy in self.strategies if strategy.get("name") == single_strategy]
        return filtered or self.strategies

    @staticmethod
    def _build_blueprint_strategy_feedback(
        strategy_name: str,
        rejected_strategy: str,
        strategy_specific_feedback: str,
    ) -> str:
        if strategy_name == rejected_strategy and strategy_specific_feedback:
            return strategy_specific_feedback
        if strategy_specific_feedback:
            return f"[이전 시도 문제 요약]\n{strategy_specific_feedback}"
        return ""

    def _run_blueprint_ensemble_workers(
        self,
        *,
        ep_num: int,
        active_strategies: list[dict],
        arc_focus: str,
        constraints_str: str,
        tactical_excerpt: str,
        prev_info: str,
        feedback: str,
        strategy_specific_feedback: str,
        rejected_strategy: str,
        protagonist_name: str,
        protagonist_config: dict | None,
        hud_context: str,
        genre: str,
        cache_name: str,
        prev_blueprint: dict | None,
    ) -> tuple[list[dict], list[str]]:
        candidates: list[dict] = []
        worker_error_types: list[str] = []
        timer_started_at = time.monotonic()

        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {}
                for strategy in active_strategies:
                    strategy_name = strategy["name"]
                    future = executor.submit(
                        self._generate_single,
                        ep_num=ep_num,
                        arc_focus=arc_focus,
                        constraints_str=constraints_str,
                        tactical_excerpt=tactical_excerpt,
                        prev_info=prev_info,
                        strategy=strategy,
                        feedback=feedback,
                        strategy_feedback=self._build_blueprint_strategy_feedback(
                            strategy_name,
                            rejected_strategy,
                            strategy_specific_feedback,
                        ),
                        protagonist_name=protagonist_name,
                        protagonist_config=protagonist_config,
                        hud_context=hud_context,
                        genre=genre,
                        cache_name=cache_name,
                        prev_blueprint=prev_blueprint,
                    )
                    futures[future] = strategy_name
                    self._operator_log(
                        f"🔡 [Blueprint] 전략 '{strategy_name}' 생성 시작",
                        meta={"strategy": strategy_name},
                    )

                try:
                    for future in as_completed(futures, timeout=self.ENSEMBLE_TIMEOUT):
                        strategy_name = futures[future]
                        try:
                            future_output = future.result(timeout=self.SINGLE_CANDIDATE_TIMEOUT)
                            worker_error_type = None
                            result = future_output
                            if (
                                isinstance(future_output, tuple)
                                and len(future_output) == 2
                                and future_output[0] is None
                                and isinstance(future_output[1], str)
                            ):
                                result = future_output[0]
                                worker_error_type = future_output[1]
                            if worker_error_type:
                                worker_error_types.append(worker_error_type)
                            if result and isinstance(result, dict):
                                result["_strategy"] = strategy_name
                                candidates.append(result)
                                logging.info(f" {strategy_name} 생성 완료")
                                self._operator_log(
                                    f"✅ [Blueprint] '{strategy_name}' 생성 완료 ({time.monotonic() - timer_started_at:.0f}초)",
                                    meta={
                                        "strategy": strategy_name,
                                        "elapsed_seconds": round(time.monotonic() - timer_started_at, 1),
                                    },
                                )
                        except FutureTimeoutError:
                            logging.warning(
                                f" [V61.3] {strategy_name} 개별 타임아웃 ({self.SINGLE_CANDIDATE_TIMEOUT}초)"
                            )
                            worker_error_types.append(AgentErrorType.TIMEOUT)
                            self._operator_log(
                                f"⚠️ [Blueprint] '{strategy_name}' 개별 타임아웃",
                                level="warning",
                                meta={"strategy": strategy_name, "timeout_seconds": self.SINGLE_CANDIDATE_TIMEOUT},
                            )
                        except Exception as exc:
                            logging.warning(f" {strategy_name} 실패: {str(exc)[:50]}")
                            worker_error_types.append(self._classify_error(exc))
                            self._operator_log(
                                f"⚠️ [Blueprint] '{strategy_name}' 실패",
                                level="warning",
                                meta={"strategy": strategy_name},
                            )
                except FutureTimeoutError:
                    logging.warning(
                        f" [V61.3] 블루프린트 전체 타임아웃 ({self.ENSEMBLE_TIMEOUT}초) - 완료된 {len(candidates)}개 후보 사용"
                    )
                except Exception as exc:
                    logging.warning(f" [V61.3] 병렬 루프 예외: {str(exc)[:80]}")
                finally:
                    for f in futures:
                        f.cancel()
        except Exception as exc:
            import traceback

            logging.error(f" [V61.3] 병렬 처리 불능 방어: {str(exc)[:100]}")
            logging.error(traceback.format_exc())

        try:
            logging.info(
                f"[PerfTimer:BlueprintEnsemble] bp_ep{ep_num}_ensemble={time.monotonic() - timer_started_at:.2f}s"
            )
        except Exception as exc:
            logging.debug("[BlueprintEnsemble] PerfTimer 기록 실패 (무시): %s", exc)

        return candidates, worker_error_types

    def _qualify_blueprint_candidates(self, candidates: list[dict]) -> tuple[list[dict], list[tuple[str, int, int]]]:
        qualified_candidates: list[dict] = []
        disqualified: list[tuple[str, int, int]] = []

        for candidate in candidates:
            strategy_name = candidate.get("_strategy", "unknown")
            scenes = candidate.get("scene_breakdown", {})
            integrated = candidate.get("integrated_scenario", "")
            integrated_len = len(integrated) if isinstance(integrated, str) else 0
            scene_gate_passed, scene_count, _, _ = evaluate_stage3_scene_cardinality(scenes, integrated)
            contract_reason = self._blueprint_contract_admission_reason(candidate)

            if (
                scene_gate_passed
                and integrated_len >= BLUEPRINT_ENSEMBLE_MIN_INTEGRATED_SCENARIO_CHARS
                and not contract_reason
            ):
                candidate["_qualified"] = True
                candidate["_scene_count"] = scene_count
                candidate["_length"] = integrated_len
                qualified_candidates.append(candidate)
                logging.info(f" {strategy_name}: 통과 (씬 {scene_count}개, {integrated_len}자)")
            else:
                disqualified.append((strategy_name, scene_count, integrated_len))
                reason_suffix = f", 사유={contract_reason}" if contract_reason else ""
                logging.info(f" {strategy_name}: 탈락 (씬 {scene_count}개, {integrated_len}자{reason_suffix})")

        return qualified_candidates, disqualified

    def _finalize_blueprint_candidates(
        self,
        qualified_candidates: list[dict],
        disqualified: list[tuple[str, int, int]],
    ) -> tuple[dict, list[dict]]:
        self._operator_log(
            f"🧥 [Blueprint] {len(qualified_candidates)}개 후보 통과 -> Director 선택 대기",
            meta={"qualified_candidates": len(qualified_candidates)},
        )

        for idx, candidate in enumerate(qualified_candidates):
            strategy_name = candidate.get("_strategy", "unknown")
            candidate["_ensemble_meta"] = {
                "candidate_index": idx,
                "strategy": strategy_name,
                "scene_count": candidate.get("_scene_count", 0),
                "length": candidate.get("_length", 0),
                "total_candidates": len(qualified_candidates),
                "disqualified": disqualified,
            }
            candidate.pop("_strategy", None)
            candidate.pop("_qualified", None)
            candidate.pop("_scene_count", None)
            candidate.pop("_length", None)

        return qualified_candidates[0], qualified_candidates

    def generate_ensemble(
        self,
        ep_num: int,
        arc_data: dict,
        constraint_block: dict,
        prev_blueprint: dict | None = None,
        feedback: str = "",
        strategy_specific_feedback: str = "",
        rejected_strategy: str = "",
        single_strategy: str = "",
        protagonist_name: str = "주인공",  # [V61] 주인공 이름 (필수!)
        protagonist_config: dict = None,  # [V60.90] 주인공 설정 (world_origin, incarnation_type)
        state_tracker=None,  # [V60.95] StateTracker (고밀도 HUD 전달)
        prev_blueprints: list[dict] | None = None,  # [V67] 이전 Blueprint 리스트
        prev_manuscripts_text: str = "",  # [V67] 이전 원고 전문 (모순 방지)
    ) -> tuple[dict | None, list[dict]]:
        """
        앙상블 Blueprint 생성

        Args:
            ep_num: 에피소드 번호
            arc_data: Arc 데이터
            constraint_block: 제약 조건 블록
            prev_blueprint: 직전 Blueprint
            feedback: 이전 REJECT 피드백
            protagonist_name: [V61] 주인공 이름 (환각 방지)
            protagonist_config: [V60.90] 주인공 설정 {world_origin, incarnation_type}
            state_tracker: [V60.95] StateTracker (고밀도 HUD - 17+ 필드, NPC 레지스트리)
            prev_blueprints: [V67] 이전 Blueprint 리스트 (전문 전달)
            prev_manuscripts_text: [V67] 이전 원고 전문 (모순 방지)

        Returns:
            (best_blueprint, all_candidates) - 최적 Blueprint와 모든 후보 리스트
        """
        context_bundle = self._prepare_blueprint_ensemble_context(
            ep_num=ep_num,
            arc_data=arc_data,
            constraint_block=constraint_block,
            prev_blueprint=prev_blueprint,
            prev_blueprints=prev_blueprints,
            prev_manuscripts_text=prev_manuscripts_text,
            state_tracker=state_tracker,
        )
        # Source guard note: genre resolution still defaults through GenreTypes.WUXIA in the prep helper.

        logging.warning(f" [BPEnsemble] 3개 후보 병렬 생성 중... (주인공: {protagonist_name})")
        active_strategies = self._select_blueprint_ensemble_strategies(single_strategy)
        self.last_error_type = None
        self.last_error_types = []

        candidates, worker_error_types = self._run_blueprint_ensemble_workers(
            ep_num=ep_num,
            active_strategies=active_strategies,
            arc_focus=context_bundle["arc_focus"],
            constraints_str=context_bundle["constraints_str"],
            tactical_excerpt=context_bundle["tactical_excerpt"],
            prev_info=context_bundle["prev_info"],
            feedback=feedback,
            strategy_specific_feedback=strategy_specific_feedback,
            rejected_strategy=rejected_strategy,
            protagonist_name=protagonist_name,
            protagonist_config=protagonist_config,
            hud_context=context_bundle["hud_context"],
            genre=context_bundle["genre"],
            cache_name=context_bundle["cache_name"],
            prev_blueprint=prev_blueprint,
        )

        self.last_error_types = list(worker_error_types)
        self.last_error_type = self._select_generate_error_type(worker_error_types)

        if not candidates:
            logging.warning("❌ [BPEnsemble] 모든 후보 생성 실패")
            return None, []

        qualified_candidates, disqualified = self._qualify_blueprint_candidates(candidates)
        if not qualified_candidates:
            logging.warning("❌ [BPEnsemble] 모든 후보 최소 기준 미달")
            return None, []

        logging.info(f" [BPEnsemble] {len(qualified_candidates)}개 후보 → Director 선택 대기")
        return self._finalize_blueprint_candidates(qualified_candidates, disqualified)

    def _generate_single(
        self,
        ep_num: int,
        arc_focus: str,
        constraints_str: str,
        tactical_excerpt: str,
        prev_info: str,
        strategy: dict,
        feedback: str = "",
        strategy_feedback: str = "",
        protagonist_name: str = "protagonist",
        protagonist_config: dict = None,
        hud_context: str = "",
        genre: str = GenreTypes.WUXIA,
        cache_name: str = "",
        prev_blueprint: dict | None = None,
    ) -> dict | tuple[None, str] | None:
        """Generate a single blueprint candidate."""
        try:
            extra_directive = ""
            merged_feedback = feedback or ""
            if strategy_feedback:
                merged_feedback = (
                    f"{merged_feedback}\n\n[Strategy feedback]\n{strategy_feedback}"
                    if merged_feedback
                    else f"[Strategy feedback]\n{strategy_feedback}"
                )
            if merged_feedback:
                extra_directive = (
                    "\n\n"
                    "[CRITICAL] Director reject feedback\n"
                    f"{merged_feedback}\n"
                    "Apply the feedback directly. Repeating the same failure will be rejected again.\n"
                )

            protagonist_instructions = self._build_protagonist_instructions(protagonist_config, genre=genre)
            pov = protagonist_config.get("pov", "") if isinstance(protagonist_config, dict) else ""
            external_pov_insert_policy = (
                protagonist_config.get("external_pov_insert_policy", "") if isinstance(protagonist_config, dict) else ""
            )
            pov_constraint = build_external_pov_policy_constraint(
                pov,
                external_pov_insert_policy,
                genre=genre,
            )
            reader_feedback = self._build_reader_feedback_context(ep_num)
            prompt, full_prompt_fallback = self._build_blueprint_prompt_bundle(
                ep_num=ep_num,
                arc_focus=arc_focus,
                constraints_str=constraints_str,
                prev_info=prev_info,
                strategy=strategy,
                protagonist_name=protagonist_name,
                protagonist_instructions=protagonist_instructions,
                extra_directive=extra_directive,
                hud_context=hud_context,
                pov_constraint=pov_constraint,
                reader_feedback=reader_feedback,
                cache_name=cache_name,
            )
            if not prompt:
                return None, AgentErrorType.UNKNOWN

            strategy_name = strategy.get("name", "unknown")
            self._operator_log(
                f"[Blueprint] '{strategy_name}' LLM request",
                meta={"strategy": strategy_name},
            )
            return self._request_blueprint_generation(
                cache_name=cache_name,
                prompt=prompt,
                full_prompt_fallback=full_prompt_fallback,
                strategy_name=strategy_name,
                genre=genre,
                tactical_excerpt=tactical_excerpt,
                prev_blueprint=prev_blueprint,
            )
        except Exception as e:
            import traceback

            logging.error("[BPEnsemble] _generate_single failed: %s", str(e)[:80])
            logging.error(traceback.format_exc())
            return None, self._classify_error(e)

    def _build_blueprint_prompt_bundle(
        self,
        *,
        ep_num: int,
        arc_focus: str,
        constraints_str: str,
        prev_info: str,
        strategy: dict,
        protagonist_name: str,
        protagonist_instructions: str,
        extra_directive: str,
        hud_context: str,
        pov_constraint: str,
        reader_feedback: str,
        cache_name: str,
    ) -> tuple[str | None, str]:
        work_retrieval_contract = ""
        try:
            guard = getattr(self.context, "guard", None)
            if guard and hasattr(guard, "get_retrieval_contract_prompt"):
                work_retrieval_contract = str(guard.get_retrieval_contract_prompt("blueprint") or "").strip()
        except Exception as exc:
            logging.debug("[BPEnsemble] work retrieval contract load failed: %s", exc)

        use_cached_context = bool(cache_name)
        cached_context_stub = "[context cached: refer to cached_content]"
        strategy_directive = self._escape_braces(
            strategy["directive"]
            + AI_TELL_BLUEPRINT_GUARDRAIL
            + extra_directive
            + (f"\n\n{work_retrieval_contract}" if work_retrieval_contract else "")
        )
        prompt = self._prompt_loader.load(
            "ensemble",
            "BLUEPRINT_GENERATION_PROMPT",
            strategy_display=strategy["display"],
            ep_num=ep_num,
            protagonist_name=self._escape_braces(protagonist_name),
            protagonist_instructions=self._escape_braces(protagonist_instructions),
            arc_focus=self._escape_braces(cached_context_stub if use_cached_context else arc_focus),
            constraints=self._escape_braces(cached_context_stub if use_cached_context else constraints_str),
            strategy_directive=strategy_directive,
            prev_info=self._escape_braces(cached_context_stub if use_cached_context else prev_info),
            hud_context=(
                self._escape_braces(cached_context_stub if use_cached_context else hud_context)
                if hud_context
                else "(no HUD context)"
            ),
            pov_constraint=self._escape_braces(pov_constraint),
            reader_feedback=self._escape_braces(reader_feedback) if reader_feedback else "",
        )
        full_prompt_fallback = prompt
        if use_cached_context:
            full_prompt_fallback = self._prompt_loader.load(
                "ensemble",
                "BLUEPRINT_GENERATION_PROMPT",
                strategy_display=strategy["display"],
                ep_num=ep_num,
                protagonist_name=self._escape_braces(protagonist_name),
                protagonist_instructions=self._escape_braces(protagonist_instructions),
                arc_focus=self._escape_braces(arc_focus),
                constraints=self._escape_braces(constraints_str),
                strategy_directive=strategy_directive,
                prev_info=self._escape_braces(prev_info),
                hud_context=self._escape_braces(hud_context) if hud_context else "(no HUD context)",
                pov_constraint=self._escape_braces(pov_constraint),
                reader_feedback=self._escape_braces(reader_feedback) if reader_feedback else "",
            )
            if not full_prompt_fallback:
                full_prompt_fallback = prompt
        if not prompt:
            logging.warning("[BPEnsemble] BLUEPRINT_GENERATION_PROMPT not found in prompt loader")
        return prompt, full_prompt_fallback or ""

    def _request_blueprint_generation(
        self,
        *,
        cache_name: str,
        prompt: str,
        full_prompt_fallback: str,
        strategy_name: str,
        genre: str,
        tactical_excerpt: str = "",
        prev_blueprint: dict | None = None,
    ) -> dict | tuple[None, str]:
        response = self._ask_with_cached_context(
            cache_name=cache_name,
            prompt=prompt,
            temperature=0.7,
            thinking_level="medium",
            full_prompt_fallback=full_prompt_fallback,
            response_schema=BLUEPRINT_SCHEMA,
        )
        self._operator_log(
            f"[Blueprint] '{strategy_name}' response received ({len(response):,} chars)",
            meta={"strategy": strategy_name, "response_chars": len(response)},
        )
        result = self._extract_json_robust(response)
        if not isinstance(result, dict):
            return None, AgentErrorType.SCHEMA_INCOMPATIBLE
        if "scene_breakdown" not in result or "integrated_scenario" not in result:
            return None, AgentErrorType.SCHEMA_INCOMPATIBLE
        return self._sanitize_blueprint_candidate(
            result,
            strategy_name=strategy_name,
            genre=genre,
            tactical_excerpt=tactical_excerpt,
            prev_blueprint=prev_blueprint,
        )

    @staticmethod
    def _scene_has_meaningful_payload(scene: dict) -> bool:
        if not isinstance(scene, dict):
            return False

        for field_name in ("summary", "description", "goal", "content"):
            if has_actionable_obligation_text(scene.get(field_name, "")):
                return True

        raw_events = scene.get("key_events", [])
        if isinstance(raw_events, str):
            raw_events = [raw_events]
        if isinstance(raw_events, list):
            if any(has_actionable_obligation_text(event) for event in raw_events):
                return True

        return False

    @staticmethod
    def _scene_has_actionable_key_events(scene: dict) -> bool:
        if not isinstance(scene, dict):
            return False

        raw_events = scene.get("key_events", [])
        if isinstance(raw_events, str):
            raw_events = [raw_events]
        if not isinstance(raw_events, list):
            return False
        return any(has_actionable_obligation_text(event) for event in raw_events)

    @classmethod
    def _scene_is_contract_complete(cls, scene: dict) -> bool:
        if not isinstance(scene, dict):
            return False
        return cls._scene_has_meaningful_payload(scene) and cls._scene_has_actionable_key_events(scene)

    @staticmethod
    def _has_meaningful_protagonist_state(protagonist_state: object) -> bool:
        if not isinstance(protagonist_state, dict):
            return False

        for value in protagonist_state.values():
            if has_meaningful_state_value(value):
                return True

        return False

    def _blueprint_contract_admission_reason(self, candidate: dict) -> str:
        opening_transition = candidate.get("opening_transition")
        if not isinstance(opening_transition, dict):
            return "missing_opening_transition"

        opening_type = str(opening_transition.get("type", "") or "").strip()
        if opening_type not in BLUEPRINT_OPENING_TRANSITION_TYPES:
            return "invalid_opening_transition"

        if not self._has_meaningful_protagonist_state(candidate.get("protagonist_state")):
            return "missing_protagonist_state"

        scene_breakdown = candidate.get("scene_breakdown")
        if isinstance(scene_breakdown, list):
            scene_iter = scene_breakdown
        elif isinstance(scene_breakdown, dict):
            scene_iter = scene_breakdown.values()
        else:
            return "missing_scene_breakdown"

        incomplete_scene_count = sum(1 for scene in scene_iter if not self._scene_is_contract_complete(scene))
        if incomplete_scene_count:
            return f"scene_completeness:{incomplete_scene_count}"

        informative_scene_count = sum(1 for scene in scene_iter if self._scene_has_meaningful_payload(scene))
        if informative_scene_count < 2:
            return f"insufficient_scene_payload:{informative_scene_count}"

        return ""

    @staticmethod
    def _collect_candidate_tactical_surface(candidate: dict) -> str:
        parts: list[str] = []
        integrated = str(candidate.get("integrated_scenario", "") or "").strip()
        if integrated:
            parts.append(integrated)

        scenes = candidate.get("scene_breakdown", {})
        if isinstance(scenes, dict):
            scene_iter = scenes.values()
        elif isinstance(scenes, list):
            scene_iter = scenes
        else:
            scene_iter = []

        for scene in scene_iter:
            if not isinstance(scene, dict):
                continue
            for key in ("title", "summary", "goal", "description", "location"):
                value = str(scene.get(key, "") or "").strip()
                if value:
                    parts.append(value)
            raw_events = scene.get("key_events", [])
            if isinstance(raw_events, str):
                raw_events = [raw_events]
            if isinstance(raw_events, list):
                parts.extend(str(item or "").strip() for item in raw_events if str(item or "").strip())

        return "\n".join(parts)

    def _detect_unauthorized_tactical_intrusion(self, candidate: dict, *, tactical_excerpt: str) -> str:
        authority_text = str(tactical_excerpt or "").strip().lower()
        if not authority_text:
            return ""
        if any(marker in authority_text for marker in _TACTICAL_INTRUSION_ENTRY_MARKERS) and any(
            marker in authority_text for marker in _TACTICAL_INTRUSION_CONFLICT_MARKERS
        ):
            return ""

        candidate_text = self._collect_candidate_tactical_surface(candidate).lower()
        if not candidate_text:
            return ""

        entry_hits = [marker for marker in _TACTICAL_INTRUSION_ENTRY_MARKERS if marker in candidate_text]
        conflict_hits = [marker for marker in _TACTICAL_INTRUSION_CONFLICT_MARKERS if marker in candidate_text]
        if not entry_hits or not conflict_hits:
            return ""
        return f"entry={entry_hits[0]}; conflict={conflict_hits[0]}"

    @staticmethod
    def _normalize_opening_transition_contract(candidate: dict, *, prev_blueprint: dict | None) -> str:
        """opening_transition contract 정규화 + 출처 라벨 반환.

        Return values:
          - ``""``: LLM이 이미 유효한 type을 직접 선언했고 정규화 불필요
          - ``"declared"``: LLM이 alias 형태로 선언, canonical type으로 정규화 후 mutation
          - ``"inferred"``: LLM 미선언, prev_blueprint/scene/time_flow 단서로 추론 + mutation
          - ``"missing"``: LLM 미선언 AND 추론 단서 부재 → cheap admission fail-closed 신호

        ``"missing"``은 cheap admission이 차단해야 하는 신호이며, 호출자는 이 값에 대해
        후보를 폐기해야 한다. T4.H1 (cheap gate disarmed by upstream normalization)을 닫는다.
        """
        raw_contract = candidate.get("opening_transition")
        declared_type = read_declared_opening_transition_type(candidate)
        if declared_type:
            raw_type = str(raw_contract.get("type", "") or "").strip() if isinstance(raw_contract, dict) else ""
            if raw_type == declared_type and isinstance(raw_contract, dict):
                return ""
            normalized_contract = dict(raw_contract) if isinstance(raw_contract, dict) else {}
            normalized_contract["type"] = declared_type
            candidate["opening_transition"] = normalized_contract
            return "declared"

        raw_type = str(raw_contract.get("type", "") or "").strip() if isinstance(raw_contract, dict) else ""
        if raw_type in BLUEPRINT_OPENING_TRANSITION_TYPES:
            return ""

        inferred_contract = apply_opening_transition_contract(candidate, prev_blueprint=prev_blueprint)
        if inferred_contract:
            return "inferred"
        return "missing"

    def _build_protagonist_instructions(self, protagonist_config: dict, genre: str = "wuxia") -> str:
        """
        [V60.90] protagonist_config 기반 프롬프트 지시사항 생성

        Args:
            protagonist_config: {world_origin: '원시인'|'현대인', incarnation_type: '회귀자'|'빙의자'|'환생자'}
            genre: [V61.3] 미리 로드한 장르 (thread-safety 위해 파라미터로 전달)

        Returns:
            프롬프트에 삽입할 지시사항 문자열
        """
        if not protagonist_config:
            return "║ (주인공 설정 정보 없음)"

        lines = []
        world_origin = protagonist_config.get("world_origin", "원시인")
        incarnation_type = protagonist_config.get("incarnation_type", "회귀자")

        # [V61.3] genre는 이제 파라미터로 전달받음 (DB 접근 제거 - thread-safety)

        # [V60.96] world_origin 기반 지시 (장르별 JSON 기반 PrimitiveGuard)
        if world_origin == "원시인":
            if PRIMITIVE_GUARD_AVAILABLE:
                prim_section = get_primitive_constraint_section(protagonist_config, genre=genre, length="short")
                lines.append(f"║ {prim_section}")
            else:
                lines.append("║ ⚠️ [원시인 모드] 현대 용어 절대 금지!")
        else:
            lines.append("║ 📝 [현대인 모드] 주인공은 현대 사회를 알고 있음")

        # incarnation_type 기반 지시
        if incarnation_type == "회귀자":
            lines.append("║ 🔄 [회귀자] 미래를 알고 있음 (합리적 이유 없이는 내면 독백으로 처리)")
        elif incarnation_type == "빙의자":
            lines.append("║ 👤 [빙의자] 원래 인물의 기억/관계를 의식")
        elif incarnation_type == "환생자":
            lines.append("║ 👶 [환생자] 전생의 기억이 있음")

        return "\n".join(lines) if lines else "║ (주인공 설정 정보 없음)"

    def _build_reader_feedback_context(self, ep_num: int) -> str:
        """[TF-I23/I24] 독자 만족도 + 호흡 분석 추이 → advisory 컨텍스트 생성.

        Python은 데이터만 수집/포맷. Blueprint LLM이 활용 여부 판단.
        """
        parts = []
        try:
            db = getattr(self.context, "db", None)
            if not db:
                return ""

            # ── I-23: 만족도 추이 ──
            try:
                sat_tags = db.get_recent_satisfaction_tags(before_ep=ep_num, lookback=5)
            except Exception as _e:
                logging.debug("[BlueprintEnsemble] sat_tags 조회 실패: %s", _e)
                sat_tags = []
            if sat_tags:
                parts.append("[독자 만족도 추이 (최근 5화)]")
                consecutive_frustration = 0
                for tag in sat_tags:
                    score = tag.get("satisfaction_score", 5)
                    frust = "불만" if tag.get("frustration_flag") else ""
                    agency = tag.get("protagonist_agency", "자력")
                    extras = ", ".join(filter(None, [agency, frust]))
                    parts.append(
                        f"  제{tag.get('ep_num', 0)}화: {tag.get('primary_tag', '미분류')} ({score}/10, {extras})"
                    )
                    if tag.get("frustration_flag"):
                        consecutive_frustration += 1
                    else:
                        consecutive_frustration = 0
                if consecutive_frustration >= 2:
                    parts.append("  ⚠️ 연속 좌절감 — 주인공 능동적 활약 씬 필수")

            # ── I-24: 호흡 분석 추이 ──
            try:
                pacing_records = db.get_recent_pacing_records(before_ep=ep_num, lookback=5)
            except Exception as _e:
                logging.debug("[BlueprintEnsemble] pacing_records 조회 실패: %s", _e)
                pacing_records = []
            if pacing_records:
                parts.append("[호흡 분석 추이 (최근 5화)]")
                for rec in pacing_records:
                    _dr = rec.get("dialogue_ratio")
                    dial_pct = f"{_dr:.0%}" if _dr is not None else "0%"
                    parts.append(
                        f"  제{rec.get('ep_num', 0)}화: 점수 {rec.get('pacing_score', 0)}/100, "
                        f"대화 {dial_pct}, 장면전환 {rec.get('scene_break_count', 0)}회"
                    )
                # 최근 평균 호흡 경고
                avg_dial = sum(r.get("dialogue_ratio") or 0 for r in pacing_records) / len(pacing_records)
                avg_score = sum(r.get("pacing_score") or 50 for r in pacing_records) / len(pacing_records)
                if avg_dial < 0.15:
                    parts.append("  ⚠️ 대화 비율 저조 — 캐릭터 상호작용 씬 추가 고려")
                if avg_score < 40:
                    parts.append("  ⚠️ 호흡 점수 낮음 — 문장 길이 다양화 및 장면 전환 고려")

        except Exception as e:
            logging.warning("[TF-I23/I24] 독자 피드백 컨텍스트 생성 실패: %s", e)
            return ""

        return "\n".join(parts) if parts else ""

    def _format_constraints(self, constraint_block: dict, *, genre: str = "wuxia") -> str:
        """Format blueprint constraints with explicit 4-tier authority banding.

        Band hierarchy (conflict resolution order):
          IMMUTABLE > HARD CONSTRAINT > EXPECTED CONTINUITY > ADVISORY
        """
        # ── Band 1: IMMUTABLE (확정 사실, 변경 불가) ──
        immutable_lines: list[str] = []

        fact_lock = constraint_block.get("fact_lock_packet", {})
        if isinstance(fact_lock, dict) and fact_lock.get("anchors"):
            immutable_lines.append("[FACT-LOCK: 확정 사실 — 변경 금지]")
            for anchor in fact_lock["anchors"]:
                if isinstance(anchor, dict) and anchor.get("fact"):
                    cat = anchor.get("category", "")
                    prefix = f"[{cat}] " if cat else ""
                    immutable_lines.append(f"  - {prefix}{anchor['fact']}")

        capital_pkt = constraint_block.get("capital_continuity_packet", {})
        if isinstance(capital_pkt, dict) and capital_pkt.get("fields"):
            immutable_lines.append("[CAPITAL-LOCK: 자본 상태 연속성 — 변경 금지]")
            for field in capital_pkt["fields"]:
                if isinstance(field, dict) and field.get("label") and field.get("value"):
                    immutable_lines.append(f"  - {field['label']}: {field['value']}")

        # ── Band 2: HARD CONSTRAINT (필수 준수, 위반 시 REJECT) ──
        hard_lines: list[str] = []

        must_focus = constraint_block.get("must_focus", {})
        if isinstance(must_focus, dict):
            arc_title = str(must_focus.get("arc_title", "") or "").strip()
            if arc_title:
                hard_lines.append("[이번 화 제목]")
                hard_lines.append(f"  {_fit_compact_context(arc_title, 120)}")
            key_events = must_focus.get("key_events") or []
            if isinstance(key_events, list) and key_events:
                hard_lines.append("[이번 화 필수 이벤트]")
                for event in key_events[:5]:
                    text = str(event or "").strip()
                    if text:
                        hard_lines.append(f"  - {_fit_compact_context(text, 120)}")
            content = str(must_focus.get("content", "") or "").strip()
            if content and not key_events:
                hard_lines.append("[이번 화 핵심 초점]")
                hard_lines.append(f"  {_fit_compact_context(content, 500)}")

        stop_line = constraint_block.get("stop_line", {})
        if isinstance(stop_line, dict) and not stop_line.get("is_arc_finale"):
            if stop_line.get("content"):
                hard_lines.append("[Stop Line]")
                _next_ep = stop_line.get("next_ep", "?")
                hard_lines.append(
                    f"  [제{_next_ep}화] 다음 화 내용 금지: {_fit_compact_context(stop_line['content'], 150)}"
                )
                for _fe in stop_line.get("future_eps") or []:
                    if isinstance(_fe, dict) and _fe.get("content"):
                        hard_lines.append(
                            f"  [제{_fe.get('ep', '?')}화] 금지: {_fit_compact_context(_fe['content'], 150)}"
                        )
                _cur_ep = constraint_block.get("ep_num", "?")
                hard_lines.append(
                    f"  *** 제{_cur_ep}화 이후 모든 에피소드 사건/NPC/전개를 "
                    f"이번 화에서 소비하거나 언급하면 즉시 REJECT ***"
                )

        arc_summary = constraint_block.get("arc_constraint_summary")
        if arc_summary:
            hard_lines.append("[Arc 제약 - MUST NOT DRIFT]")
            if isinstance(arc_summary, str):
                hard_lines.append(f"  {_fit_compact_context(arc_summary, 500)}")
            elif isinstance(arc_summary, dict):
                for key, value in list(arc_summary.items())[:10]:
                    hard_lines.append(f"  {key}: {_fit_compact_context(value, 100)}")

        # ── Band 3: EXPECTED CONTINUITY (계승 필수, 불일치 시 경고) ──
        continuity_lines: list[str] = []

        continuity = constraint_block.get("continuity", {})
        if isinstance(continuity, dict):
            _cont_items: list[str] = []
            if continuity.get("location"):
                _cont_items.append(f"  이전 종료 위치: {_fit_compact_context(continuity['location'], 120)}")
            if continuity.get("time_context"):
                _cont_items.append(f"  시간 맥락: {_fit_compact_context(continuity['time_context'], 100)}")
            conflicts = continuity.get("ongoing_conflicts") or []
            if isinstance(conflicts, list):
                for item in conflicts[:5]:
                    text = str(item or "").strip()
                    if text:
                        _cont_items.append(f"  - 진행 중 갈등: {_fit_compact_context(text, 80)}")
            elif conflicts:
                _cont_items.append(f"  - 진행 중 갈등: {_fit_compact_context(conflicts, 200)}")
            active = continuity.get("active_characters") or []
            if isinstance(active, list) and active:
                names = [
                    _fit_compact_context(str(item or "").strip(), 20) for item in active[:10] if str(item or "").strip()
                ]
                if names:
                    _cont_items.append(f"  등장 캐릭터: {', '.join(names)}")
            elif active:
                _cont_items.append(f"  등장 캐릭터: {_fit_compact_context(active, 200)}")
            if _cont_items:
                continuity_lines.append("[연속성]")
                continuity_lines.extend(_cont_items)

        inherited = constraint_block.get("inherited_state", {})
        if isinstance(inherited, dict):
            inherited_items: list[str] = []
            equip = inherited.get("equipment")
            if equip:
                if isinstance(equip, list):
                    equip = ", ".join(str(x) if not isinstance(x, dict) else str(x.get("name", x)) for x in equip[:5])
                inherited_items.append(f"  장비: {_fit_compact_context(equip, 200)}")
            injuries = inherited.get("injuries")
            if injuries:
                if isinstance(injuries, list):
                    inherited_items.append(f"  부상: {', '.join(_fit_compact_context(i, 40) for i in injuries[:5])}")
                else:
                    inherited_items.append(f"  부상: {_fit_compact_context(injuries, 200)}")
            if genre == "wuxia" and inherited.get("internal_energy") is not None:
                inherited_items.append(f"  내공/에너지: {_fit_compact_context(inherited['internal_energy'], 80)}")
            if inherited.get("mood"):
                inherited_items.append(f"  심리 상태: {_fit_compact_context(inherited['mood'], 100)}")
            if inherited_items:
                continuity_lines.append("[계승 상태]")
                continuity_lines.extend(inherited_items)

        # ── Band 4: ADVISORY (참고용, 필수 아님) ──
        advisory_lines: list[str] = []

        sc_summary = constraint_block.get("state_changes_summary")
        if sc_summary:
            advisory_lines.append("[상태 변경 요약]")
            if isinstance(sc_summary, str):
                advisory_lines.append(f"  {_fit_compact_context(sc_summary, 800)}")
            elif isinstance(sc_summary, dict):
                deaths = sc_summary.get("npc_deaths", [])
                if deaths:
                    names = [
                        d.get("name", d.get("npc", str(d))) if isinstance(d, dict) else str(d) for d in deaths[:10]
                    ]
                    advisory_lines.append(f"  사망 NPC: {', '.join(names)}")
                skills = sc_summary.get("skill_acquisitions", [])
                if skills:
                    names = [
                        s.get("name", s.get("skill", str(s))) if isinstance(s, dict) else str(s) for s in skills[:10]
                    ]
                    advisory_lines.append(f"  획득 기술: {', '.join(names)}")
                resolved = sc_summary.get("resolved_plots", [])
                if resolved:
                    names = [
                        r.get("plot", r.get("description", str(r))) if isinstance(r, dict) else str(r)
                        for r in resolved[:10]
                    ]
                    advisory_lines.append(f"  해결 플롯: {', '.join(names)}")
                permanent = sc_summary.get("permanent_injuries", [])
                if permanent:
                    descs = [
                        _fit_compact_context(p, 50)
                        if not isinstance(p, dict)
                        else _fit_compact_context(p.get("description", str(p)), 50)
                        for p in permanent[:5]
                    ]
                    advisory_lines.append(f"  영구 부상: {', '.join(descs)}")

        semantic_carryover = constraint_block.get("semantic_carryover")
        if isinstance(semantic_carryover, dict) and semantic_carryover:
            advisory_lines.append("[Future Semantic Advisory — 이번 화 obligation 아님]")
            advisory_lines.append(
                "  아래 항목은 미래 화/관계 맥락 참고용이다. 이번 화에서 반드시 모두 소비할 필요는 없다."
            )
            for entry in semantic_carryover.get("relationship_rationale", []) or []:
                if not isinstance(entry, dict):
                    continue
                npc = str(entry.get("npc", "") or "").strip() or "?"
                cue = str(entry.get("trigger", "") or entry.get("justification", "") or "").strip()
                if cue:
                    advisory_lines.append(f"  relationship {npc}: {_fit_compact_context(cue, 120)}")
            # [W2] growth_justification: suppressed (arc-end achievement fuel)
            # [W2] continuity_checkpoints: suppressed (arc-end completion state)
            for anchor in (semantic_carryover.get("foreshadow_anchors", []) or [])[:3]:
                text = str(anchor or "").strip()
                if text:
                    advisory_lines.append(f"  [미래 복선 참고용] foreshadow: {_fit_compact_context(text, 120)}")

        lines = [
            "[\uc81c\uc57d \uc6b0\uc120\uc21c\uc704: IMMUTABLE > HARD CONSTRAINT > EXPECTED CONTINUITY > ADVISORY]",
            "\ucda9\ub3cc \uc2dc \uc0c1\uc704 \ub4f1\uae09\uc774 \ud558\uc704 \ub4f1\uae09\uc744 \ubb34\uc870\uac74 \uc6b0\uc120\ud569\ub2c8\ub2e4.",
            "",
        ]
        for header, band_lines in (
            (
                "\u2550\u2550\u2550 IMMUTABLE (\ud655\uc815 \uc0ac\uc2e4 \u2014 \uc808\ub300 \ubcc0\uacbd \uae08\uc9c0) \u2550\u2550\u2550",
                immutable_lines,
            ),
            (
                "\u2500\u2500\u2500 HARD CONSTRAINT (\ud544\uc218 \uc900\uc218 \u2014 \uc704\ubc18 \uc2dc REJECT) \u2500\u2500\u2500",
                hard_lines,
            ),
            (
                "\u2500\u2500\u2500 EXPECTED CONTINUITY (\uacc4\uc2b9 \uae30\ub300 \u2014 \ubd88\uc77c\uce58 \uc2dc \uacbd\uace0) \u2500\u2500\u2500",
                continuity_lines,
            ),
            (
                "\u00b7\u00b7\u00b7 ADVISORY (\ucc38\uace0\uc6a9 \u2014 \ud544\uc218 \uc544\ub2d8) \u00b7\u00b7\u00b7",
                advisory_lines,
            ),
        ):
            _append_constraint_section(lines, header, band_lines)
        if lines[-1] == "":
            lines.pop()

        return "\n".join(lines) if lines else "(constraints unavailable)"

    def _build_hud_context(self, state_tracker, ep_num: int) -> str:
        """[V64 P2-7] 위임 → modules.core.hud_utils.build_hud_context (blueprint variant)"""
        return _build_hud_context_shared(state_tracker, ep_num, variant="blueprint")

    def _format_prev_info(self, prev_blueprint: dict | None) -> str:
        """이전 Blueprint 정보 포맷팅 (레거시 - 단일 Blueprint)"""
        if not prev_blueprint:
            return "(첫 에피소드 - 이전 화 없음)"

        lines = []

        # [V61.5] 이전 에피소드 종료 상태 섹션 강화
        lines.append("━━━━━ [V61.5] 이전 에피소드 종료 상태 ━━━━━")
        lines.append("⚠️ 아래 상태에서 시작해야 합니다. 위치/시점 불연속 금지!")

        ending_hook = prev_blueprint.get("ending_hook", "")
        if ending_hook:
            lines.append(f"엔딩 훅: {ending_hook}")

        end_location = prev_blueprint.get("end_location", "")
        if end_location:
            lines.append(f"종료 위치: {end_location}")

        # [V61.5] 시간 흐름 정보 추가
        time_flow = prev_blueprint.get("time_flow", "")
        if time_flow:
            lines.append(f"시간 흐름: {time_flow}")

        # [V61.5] ending_state 필드 (있으면)
        ending_state = prev_blueprint.get("ending_state", {})
        if ending_state:
            if ending_state.get("location"):
                lines.append(f"종료 위치 (상세): {ending_state['location']}")
            if ending_state.get("timeline"):
                tl = ending_state["timeline"]
                if isinstance(tl, dict):
                    tl_str = ", ".join(f"{k}:{v}" for k, v in tl.items())
                else:
                    tl_str = str(tl)
                lines.append(f"종료 시점: {tl_str}")
            if ending_state.get("protagonist_status"):
                lines.append(f"주인공 상태: {ending_state['protagonist_status']}")

        protag_state = prev_blueprint.get("protagonist_state", {})
        if protag_state:
            mood = protag_state.get("mood", "")
            injuries = protag_state.get("injuries", "")
            equipment = protag_state.get("equipment", [])
            if mood:
                lines.append(f"감정 상태: {mood}")
            if injuries and injuries != "없음":
                lines.append(f"부상: {injuries}")
            if equipment:
                equip_str = (
                    ", ".join(str(x) if isinstance(x, dict) else x for x in equipment[:5])
                    if isinstance(equipment, list)
                    else str(equipment)
                )
                lines.append(f"소지품: {equip_str}")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        return "\n".join(lines) if len(lines) > 3 else "(이전 화 정보 없음)"

    @staticmethod
    def _genre_allows_explicit_system_ui(genre: str) -> bool:
        return genre in {GenreTypes.HUNTER, GenreTypes.FANTASY}

    def _detect_blueprint_text_contamination(self, text: object, *, allow_system_ui: bool) -> str | None:
        raw = str(text or "").strip()
        if not raw:
            return None

        lowered = raw.casefold()
        if any(marker in lowered for marker in _BLUEPRINT_META_RECAP_MARKERS):
            return "meta_recap_register"
        if not allow_system_ui and any(marker in lowered for marker in _BLUEPRINT_SYSTEM_UI_MARKERS):
            return "system_ui_register"
        return None

    def _sanitize_blueprint_candidate(
        self,
        candidate: dict,
        *,
        strategy_name: str,
        genre: str,
        tactical_excerpt: str = "",
        prev_blueprint: dict | None = None,
    ) -> dict | tuple[None, str]:
        allow_system_ui = self._genre_allows_explicit_system_ui(genre)
        integrated_reason = self._detect_blueprint_text_contamination(
            candidate.get("integrated_scenario", ""),
            allow_system_ui=allow_system_ui,
        )
        if integrated_reason:
            logging.warning(
                "[BPEnsemble] rejecting contaminated blueprint candidate (%s): %s",
                strategy_name,
                integrated_reason,
            )
            self._operator_log(
                f"⚠️ [Blueprint] '{strategy_name}' 오염 후보 폐기",
                level="warning",
                meta={"strategy": strategy_name, "reason": integrated_reason},
            )
            return None, AgentErrorType.SCHEMA_INCOMPATIBLE

        scene_breakdown = candidate.get("scene_breakdown")
        if isinstance(scene_breakdown, list):
            scene_iter = [(f"scene_{idx}", scene) for idx, scene in enumerate(scene_breakdown, start=1)]
        elif isinstance(scene_breakdown, dict):
            scene_iter = list(scene_breakdown.items())
        else:
            scene_iter = []

        sanitized_key_events = 0
        for scene_key, scene in scene_iter:
            if not isinstance(scene, dict):
                continue

            for field_name in ("summary", "description", "goal", "content"):
                reason = self._detect_blueprint_text_contamination(
                    scene.get(field_name, ""),
                    allow_system_ui=allow_system_ui,
                )
                if reason:
                    logging.warning(
                        "[BPEnsemble] rejecting contaminated scene field (%s/%s/%s): %s",
                        strategy_name,
                        scene_key,
                        field_name,
                        reason,
                    )
                    self._operator_log(
                        f"⚠️ [Blueprint] '{strategy_name}' 오염 씬 폐기",
                        level="warning",
                        meta={
                            "strategy": strategy_name,
                            "scene": scene_key,
                            "field": field_name,
                            "reason": reason,
                        },
                    )
                    return None, AgentErrorType.SCHEMA_INCOMPATIBLE

            raw_events = scene.get("key_events", [])
            if isinstance(raw_events, str):
                raw_events = [raw_events]
            if not isinstance(raw_events, list):
                continue

            filtered_events = []
            dropped_events = 0
            for event in raw_events:
                reason = self._detect_blueprint_text_contamination(event, allow_system_ui=allow_system_ui)
                if reason:
                    dropped_events += 1
                    continue
                filtered_events.append(event)

            if dropped_events and not filtered_events:
                logging.warning(
                    "[BPEnsemble] rejecting blueprint candidate (%s): scene %s lost all key_events to contamination",
                    strategy_name,
                    scene_key,
                )
                self._operator_log(
                    f"⚠️ [Blueprint] '{strategy_name}' key_events 오염 후보 폐기",
                    level="warning",
                    meta={"strategy": strategy_name, "scene": scene_key},
                )
                return None, AgentErrorType.SCHEMA_INCOMPATIBLE

            if dropped_events:
                scene["key_events"] = filtered_events
                sanitized_key_events += dropped_events

        if sanitized_key_events:
            logging.info(
                "[BPEnsemble] sanitized %d contaminated key_events from %s",
                sanitized_key_events,
                strategy_name,
            )
            self._operator_log(
                f"🧹 [Blueprint] '{strategy_name}' key_events 오염 정리",
                meta={"strategy": strategy_name, "removed_key_events": sanitized_key_events},
            )

        opening_transition_route = self._normalize_opening_transition_contract(
            candidate,
            prev_blueprint=prev_blueprint,
        )
        if opening_transition_route == "missing":
            # T4.H1: cheap gate disarmed 닫기 — LLM이 opening_transition을 선언하지 않았고
            # prev_blueprint/scene/time_flow에서도 추론할 단서가 없으면 즉시 폐기.
            # 이전에는 normalizer가 빈 string을 반환해 admission gate가 통과시켜 버렸다.
            logging.warning(
                "[BPEnsemble] rejecting candidate (%s): opening_transition pure omission with no inference anchor",
                strategy_name,
            )
            self._operator_log(
                f"⚠️ [Blueprint] '{strategy_name}' opening_transition 부재 + 추론 불가 후보 폐기",
                level="warning",
                meta={
                    "strategy": strategy_name,
                    "reason": "missing_opening_transition_pure_omission",
                },
            )
            return None, AgentErrorType.SCHEMA_INCOMPATIBLE
        if opening_transition_route in ("declared", "inferred"):
            logging.info(
                "[BPEnsemble] normalized opening_transition contract for %s via %s path",
                strategy_name,
                opening_transition_route,
            )
            self._operator_log(
                f"[Blueprint] '{strategy_name}' opening_transition contract normalized",
                meta={"strategy": strategy_name, "route": opening_transition_route},
            )

        tactical_intrusion_reason = self._detect_unauthorized_tactical_intrusion(
            candidate,
            tactical_excerpt=tactical_excerpt,
        )
        if tactical_intrusion_reason:
            logging.warning(
                "[BPEnsemble] rejecting unauthorized tactical intrusion candidate (%s): %s",
                strategy_name,
                tactical_intrusion_reason,
            )
            self._operator_log(
                f"⚠️ [Blueprint] '{strategy_name}' tactical authority 미달 후보 폐기",
                level="warning",
                meta={"strategy": strategy_name, "reason": tactical_intrusion_reason},
            )
            return None, AgentErrorType.SCHEMA_INCOMPATIBLE

        contract_reason = self._blueprint_contract_admission_reason(candidate)
        if contract_reason:
            logging.warning(
                "[BPEnsemble] rejecting under-structured blueprint candidate (%s): %s",
                strategy_name,
                contract_reason,
            )
            self._operator_log(
                f"⚠️ [Blueprint] '{strategy_name}' 구조 계약 미달 후보 폐기",
                level="warning",
                meta={"strategy": strategy_name, "reason": contract_reason},
            )
            return None, AgentErrorType.SCHEMA_INCOMPATIBLE

        return candidate

    def _format_prev_blueprint_carryover(self, bp: dict) -> str:
        bp_ep = bp.get("ep_num", "?")
        bp_title = bp.get("title", "")
        lines = [f"\n━━━ 제{bp_ep}화 '{bp_title}' ━━━"]

        carryover_fields = (
            ("시작위치", bp.get("start_location", "")),
            ("종료위치", bp.get("end_location", "")),
            ("시간흐름", bp.get("time_flow", "")),
            ("핵심긴장", bp.get("core_tension", "")),
            ("결말방향", bp.get("expected_ending", "")),
            ("엔딩훅", bp.get("ending_hook", "")),
        )
        for label, value in carryover_fields:
            if value:
                lines.append(f"[{label}] {_fit_compact_context(value, 160)}")

        protagonist_state = bp.get("protagonist_state", {})
        if isinstance(protagonist_state, dict):
            state_parts = []
            mood = protagonist_state.get("mood", "")
            injuries = protagonist_state.get("injuries", "")
            equipment = protagonist_state.get("equipment", [])
            if mood:
                state_parts.append(f"감정:{_fit_compact_context(mood, 60)}")
            if injuries and injuries != "없음":
                state_parts.append(f"부상:{_fit_compact_context(injuries, 60)}")
            if isinstance(equipment, list) and equipment:
                equipment_text = ", ".join(str(item or "").strip() for item in equipment[:5] if str(item or "").strip())
                if equipment_text:
                    state_parts.append(f"장비:{_fit_compact_context(equipment_text, 100)}")
            elif equipment:
                state_parts.append(f"장비:{_fit_compact_context(equipment, 100)}")
            if state_parts:
                lines.append(f"[주인공상태] {' | '.join(state_parts)}")

        scenes = bp.get("scene_breakdown", {})
        if isinstance(scenes, list):
            scenes = {f"scene_{i + 1}": scene for i, scene in enumerate(scenes) if isinstance(scene, dict)}
        if isinstance(scenes, dict):
            for scene_key, scene_value in scenes.items():
                if not isinstance(scene_value, dict):
                    continue
                scene_title = _fit_compact_context(scene_value.get("title", ""), 80)
                scene_location = _fit_compact_context(scene_value.get("location", ""), 60)
                scene_summary = scene_value.get("summary", "") or scene_value.get("description", "")
                scene_summary = _fit_compact_context(scene_summary, 120) if scene_summary else ""
                scene_chars = scene_value.get("characters", [])
                scene_events = scene_value.get("key_events", [])
                if isinstance(scene_chars, str):
                    scene_chars = [scene_chars]
                if isinstance(scene_events, str):
                    scene_events = [scene_events]
                chars_str = (
                    _fit_compact_context(
                        ", ".join(str(item or "").strip() for item in scene_chars if str(item or "").strip()),
                        120,
                    )
                    if scene_chars
                    else ""
                )
                events_str = (
                    _fit_compact_context(
                        "; ".join(str(item or "").strip() for item in scene_events if str(item or "").strip()),
                        180,
                    )
                    if scene_events
                    else ""
                )
                scene_parts = [f"[{scene_key}] {scene_title}"]
                if scene_location:
                    scene_parts.append(f"장소: {scene_location}")
                if chars_str:
                    scene_parts.append(f"등장: {chars_str}")
                if scene_summary:
                    scene_parts.append(f"요약: {scene_summary}")
                if events_str:
                    scene_parts.append(f"이벤트: {events_str}")
                lines.append(" | ".join(scene_parts))

        return "\n".join(lines)

    def _format_prev_info_expanded(
        self, prev_blueprint: dict | None, prev_blueprints: list[dict] | None = None, prev_manuscripts_text: str = ""
    ) -> str:
        """[V67] 이전 Blueprint/원고 확장 정보 포맷팅 (Gemini 대용량 컨텍스트 활용)"""
        sections = []

        # ── 직전 Blueprint 상세 (필수 계승) ──
        direct_prev = self._format_prev_info(prev_blueprint)
        sections.append("[Context Tier 1 - Direct Previous Episode Truth]")
        sections.append(direct_prev)

        # ── [V67] 이전 Blueprint 전문 (최대 30개) ──
        if prev_blueprints and len(prev_blueprints) > 0:
            bp_lines = ["[Context Tier 2 - Structured Previous Blueprint Carryover]"]
            bp_lines.append(f"\n[V67] ═══ 이전 Blueprint 전문 ({len(prev_blueprints)}개) ═══")
            bp_lines.append("이전 에피소드의 구조화된 계승 정보입니다. 모순되는 내용을 절대 생성하지 마세요.")
            for bp in prev_blueprints:
                bp_lines.append(self._format_prev_blueprint_carryover(bp))

            bp_full = "\n".join(bp_lines)
            # 400K자 상한 (Gemini 1.05M 토큰 입력 여유)
            if len(bp_full) > 400000:
                bp_full = smart_truncate(
                    bp_full,
                    max_chars=400000,
                    head_chars=max(0, min(int(400000 * 0.55), 400000 - 80)),
                )
            sections.append(bp_full)

        # ── [pre-rerun] 직전 원고 말미 → 시간 진실 소스 ──
        if prev_manuscripts_text:
            sections.append("[Context Tier 3 - Manuscript Ending Truth]")
            ending_excerpt = prev_manuscripts_text.strip()[-800:]
            sections.append(
                "\n[pre-rerun] ═══ 직전 원고 실제 종료 상황 (원고 기준 — Blueprint 메타데이터보다 우선) ═══\n"
                "⚠️ 아래 원고 말미가 실제 종료 시점/위치/상황의 진실 소스입니다.\n"
                "Blueprint의 time_flow나 ending_state.timeline과 다를 경우, 원고 내용을 따르세요.\n\n"
                f"{ending_excerpt}"
            )

        # ── [V67] 이전 원고 전문 ──
        if prev_manuscripts_text:
            ms_section = (
                "\n[Context Tier 4 - Archive Appendix / lower priority than Tier 1-3]\n"
                f"\n[V67] ═══ 이전 원고 전문 ═══\n"
                f"아래는 이전 에피소드의 최종 원고입니다. 이 내용과 모순되는 Blueprint를 절대 생성하지 마세요.\n"
                f"특히: 사망한 캐릭터 재등장, 이미 일어난 이벤트 반복, 위치/시간 불연속에 주의하세요.\n\n"
                f"{prev_manuscripts_text}"
            )
            # 400K자 상한 (Gemini 1.05M 토큰 입력 여유)
            if len(ms_section) > 400000:
                ms_section = smart_truncate(
                    ms_section,
                    max_chars=400000,
                    head_chars=max(0, min(int(400000 * 0.55), 400000 - 80)),
                )
            sections.append(ms_section)

        result = "\n\n".join(sections)
        return smart_truncate(result)


def create_blueprint_ensemble(context, client, model_tier: str = AIModels.DEFAULT_ARCHITECT):
    """BlueprintEnsembleGenerator 생성 헬퍼"""
    return BlueprintEnsembleGenerator(context, client, model_tier)
