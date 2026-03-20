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
from modules.core.response_schemas import BLUEPRINT_SCHEMA
from modules.core.tactical_utils import extract_episode_tactical

from .base_agent import AgentErrorType, _SYSTEM_CFG, BaseAgent

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
- 장면 말미를 설명문으로 기계적으로 요약하지 마세요.
- 감정 반응을 상투적인 반응구 반복으로 처리하지 말고 행동·대사·구체 감각으로 드러내세요.
- 정보 전달만 수행하는 대사가 길게 이어지지 않게 하세요.
- 매 씬의 도입과 종결 리듬을 같게 반복하지 마세요.
- 독자가 "익숙한 AI 문장"이라고 느낄 만한 접속구·감탄구 남용을 피하세요.
"""


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
        candidates = []

        # Arc 포커스 추출
        arc_focus = constraint_block.get("must_focus", {}).get("content", "")
        if not arc_focus:
            # [TTE] 에피소드별 지능 추출
            arc_focus = extract_episode_tactical(
                arc_data.get("tactical_doc", ""),
                ep_num,
                episode_details=arc_data.get("episode_details"),
            )

        # [TF-46] episode_details enrichment을 절삭 전에 수행 (기존: 절삭 후 prepend → enrichment 유실)
        _ep_details = arc_data.get("episode_details") or []
        if isinstance(_ep_details, list):
            for _item in _ep_details:
                if isinstance(_item, dict) and _item.get("ep_num") == ep_num:
                    _details = _item.get("details") or []
                    if isinstance(_details, list) and _details:
                        _detail_text = "\n".join(f"  - {d}" for d in _details if isinstance(d, str))
                        arc_focus = f"[{ep_num}화 핵심 사건 (Arc 설계 원본)]\n{_detail_text}\n\n{arc_focus}"
                    break
        # [TF-46] enrichment 후 안전캡 (12K→15K, enrichment 포함 여유)
        arc_focus = smart_truncate(
            arc_focus,
            max_chars=15000,
            head_chars=max(0, min(int(15000 * 0.55), 15000 - 80)),
        )

        # [V61.3] 병렬 실행 전에 genre 미리 로드 (SQLite thread-safety 문제 방지)
        genre = GenreTypes.WUXIA
        try:
            if hasattr(self, "context") and hasattr(self.context, "db"):
                bible = self.context.db.load_anchor("bible")
                if bible:
                    genre = bible.get("_genre", GenreTypes.WUXIA)
        except Exception as e:
            logging.warning(f" [V61.3] genre 사전 로드 실패: {str(e)[:50]}")

        # [TF-41] P1-2: genre를 _format_constraints에 전달 (내공 필터링용)
        constraints_str = self._format_constraints(constraint_block, genre=genre)

        # [V67] 이전 화 정보 확장 (이전 Blueprint 전문 + 이전 원고 전문)
        prev_info = self._format_prev_info_expanded(prev_blueprint, prev_blueprints, prev_manuscripts_text)

        # [V60.95] 고밀도 HUD 컨텍스트 구축
        hud_context = self._build_hud_context(state_tracker, ep_num)
        _work_retrieval_contract = ""
        try:
            _guard = getattr(self.context, "guard", None)
            if _guard and hasattr(_guard, "get_retrieval_contract_prompt"):
                _work_retrieval_contract = str(_guard.get_retrieval_contract_prompt("blueprint") or "").strip()
        except Exception as _e:
            logging.debug("[BPEnsemble] work retrieval contract 로드 실패: %s", _e)

        # 병렬 생성
        logging.warning(f" [BPEnsemble] 3개 후보 병렬 생성 중... (주인공: {protagonist_name})")
        _active_strategies = self.strategies
        if single_strategy:
            _filtered = [s for s in self.strategies if s.get("name") == single_strategy]
            if _filtered:
                _active_strategies = _filtered

        # [Phase 3-Obs] 에이전트 레벨 ThreadPoolExecutor 계측
        # [Tier4-11] shared context cache for ensemble fan-out
        shared_context = f"{arc_focus or ''}\n\n{constraints_str or ''}\n\n{prev_info or ''}\n\n{hud_context or ''}"
        cache_info = self._get_or_create_context_cache(
            cache_type="blueprint_ensemble",
            content=shared_context,
            ttl_seconds=600,
            project_name=self._context_cache_project_namespace("ep", ep_num),
        )
        cache_name = cache_info.get("cache_name")
        self.last_error_type = None
        self.last_error_types = []
        worker_error_types: list[str] = []

        _tp_t0 = time.monotonic()

        # [V61.3] 전체 병렬 처리 블록을 try-except로 감싸서 급사 방지
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {}
                for strategy in _active_strategies:
                    # [S3-P1-3] 모든 전략에 generic 피드백 전달, 거절된 전략에는 추가 specific 피드백
                    if strategy.get("name") == rejected_strategy and strategy_specific_feedback:
                        _strategy_feedback = strategy_specific_feedback
                    elif strategy_specific_feedback:
                        _strategy_feedback = f"[이전 시도 문제 요약]\n{strategy_specific_feedback}"
                    else:
                        _strategy_feedback = ""
                    future = executor.submit(
                        self._generate_single,
                        ep_num=ep_num,
                        arc_focus=arc_focus,
                        constraints_str=constraints_str,
                        prev_info=prev_info,
                        strategy=strategy,
                        feedback=feedback,
                        strategy_feedback=_strategy_feedback,
                        protagonist_name=protagonist_name,  # [V61] 주인공 이름 전달
                        protagonist_config=protagonist_config,  # [V60.90] 주인공 설정 전달
                        hud_context=hud_context,  # [V60.95] 고밀도 HUD 주입
                        genre=genre,  # [V61.3] 미리 로드한 genre 전달 (thread-safety)
                        cache_name=cache_name,  # [Tier4-11]
                    )
                    futures[future] = strategy["name"]
                    self._operator_log(
                        f"🎲 [Blueprint] 전략 '{strategy['name']}' 생성 시작",
                        meta={"strategy": strategy["name"]},
                    )

                # [V61.3] 타임아웃 적용 - 야간 무인 운영 시 무한 대기 방지
                try:
                    for future in as_completed(futures, timeout=self.ENSEMBLE_TIMEOUT):
                        strategy_name = futures[future]
                        try:
                            # [V61.3] 개별 후보에도 타임아웃 적용
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
                                    f"✓ [Blueprint] '{strategy_name}' 생성 완료 ({time.monotonic() - _tp_t0:.0f}초)",
                                    meta={
                                        "strategy": strategy_name,
                                        "elapsed_seconds": round(time.monotonic() - _tp_t0, 1),
                                    },
                                )
                        except FutureTimeoutError:
                            logging.warning(f" [V61.3] {strategy_name} 타임아웃 ({self.SINGLE_CANDIDATE_TIMEOUT}초)")
                            worker_error_types.append(AgentErrorType.TIMEOUT)
                            self._operator_log(
                                f"✗ [Blueprint] '{strategy_name}' 타임아웃",
                                level="warning",
                                meta={"strategy": strategy_name, "timeout_seconds": self.SINGLE_CANDIDATE_TIMEOUT},
                            )
                        except Exception as e:
                            logging.warning(f" {strategy_name} 실패: {str(e)[:50]}")
                            worker_error_types.append(self._classify_error(e))
                            self._operator_log(
                                f"✗ [Blueprint] '{strategy_name}' 실패",
                                level="warning",
                                meta={"strategy": strategy_name},
                            )
                except FutureTimeoutError:
                    # 전체 앙상블 타임아웃 - 완료된 후보만 사용
                    logging.warning(
                        f" [V61.3] 블루프린트 앙상블 타임아웃 ({self.ENSEMBLE_TIMEOUT}초) - 완료된 {len(candidates)}개 후보 사용"
                    )
                except Exception as e:
                    # [V61.3] as_completed 자체 예외 처리
                    logging.warning(f" [V61.3] 앙상블 루프 예외: {str(e)[:80]}")
                finally:
                    # [Sweep34] 미완료 future 정리로 shutdown 대기 최소화
                    for f in futures:
                        f.cancel()
        except Exception as e:
            # [V61.3] ThreadPoolExecutor 전체 예외 처리 - 급사 방지
            # stderr로 출력 (Rich 스피너가 stdout 가림)
            import traceback

            logging.error(f" [V61.3] 병렬 처리 크래시 방지: {str(e)[:100]}")
            logging.error(traceback.format_exc())

        # [Phase 3-Obs] 병렬 구간 소요 시간 기록
        try:
            logging.info(f"[PerfTimer:BlueprintEnsemble] bp_ep{ep_num}_ensemble={time.monotonic() - _tp_t0:.2f}s")
        except Exception as _e:
            logging.debug("[BlueprintEnsemble] PerfTimer 기록 실패 (무시): %s", _e)

        self.last_error_types = list(worker_error_types)
        self.last_error_type = self._select_generate_error_type(worker_error_types)

        if not candidates:
            logging.warning("❌ [BPEnsemble] 모든 후보 생성 실패")
            return None, []

        # [V60.85] Python 최소 기준 필터링 - 씬 4개 이상만 통과
        # 철학: Python은 "당선 불가" 후보만 걸러냄, 선택은 Director가 함
        qualified_candidates = []
        disqualified = []

        for candidate in candidates:
            strategy_name = candidate.get("_strategy", "unknown")
            scenes = candidate.get("scene_breakdown", {})
            scene_count = len(scenes) if isinstance(scenes, (dict, list)) else 0
            integrated = candidate.get("integrated_scenario", "")
            integrated_len = len(integrated) if isinstance(integrated, str) else 0

            # 최소 기준: 씬 4개 이상, 시나리오 500자 이상
            if scene_count >= 4 and integrated_len >= 500:
                candidate["_qualified"] = True
                candidate["_scene_count"] = scene_count
                candidate["_length"] = integrated_len
                qualified_candidates.append(candidate)
                logging.info(f" {strategy_name}: 통과 (씬 {scene_count}개, {integrated_len}자)")
            else:
                disqualified.append((strategy_name, scene_count, integrated_len))
                logging.info(f" {strategy_name}: 탈락 (씬 {scene_count}개, {integrated_len}자)")

        if not qualified_candidates:
            logging.warning("❌ [BPEnsemble] 모든 후보 최소 기준 미달")
            return None, []  # [P0] 미검증 원본 대신 빈 리스트 반환

        # [V60.85] Director가 선택할 수 있도록 후보 목록 반환
        # Python은 선택하지 않음 - Director에게 전체 전달
        logging.info(f" [BPEnsemble] {len(qualified_candidates)}개 후보 → Director 선택 대기")
        self._operator_log(
            f"📋 [Blueprint] {len(qualified_candidates)}개 후보 통과 → Director 선택 대기",
            meta={"qualified_candidates": len(qualified_candidates)},
        )

        # 메타데이터 저장 (Director 비교용)
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
            # 임시 필드 정리
            candidate.pop("_strategy", None)
            candidate.pop("_qualified", None)
            candidate.pop("_scene_count", None)
            candidate.pop("_length", None)

        # [V60.85] 첫 번째 후보를 "대표"로 반환하되, 전체 후보 리스트도 함께 반환
        # Validator에서 Director가 전체 비교 후 최종 선택
        return qualified_candidates[0], qualified_candidates

    def _generate_single(
        self,
        ep_num: int,
        arc_focus: str,
        constraints_str: str,
        prev_info: str,
        strategy: dict,
        feedback: str = "",
        strategy_feedback: str = "",
        protagonist_name: str = "주인공",  # [V61] 주인공 이름
        protagonist_config: dict = None,  # [V60.90] 주인공 설정
        hud_context: str = "",  # [V60.95] 고밀도 HUD 컨텍스트
        genre: str = GenreTypes.WUXIA,  # [V61.3] 미리 로드한 genre (thread-safety)
        cache_name: str = "",  # [Tier4-11] shared context cache name
    ) -> dict | tuple[None, str] | None:
        """단일 Blueprint 생성"""
        # [V61.3] 전체 메서드를 try-except로 감싸서 worker thread 크래시 방지
        try:
            # [V60.80] 피드백 강화 주입 - Director 피드백은 반드시 반영
            extra_directive = ""
            _merged_feedback = feedback or ""
            if strategy_feedback:
                _merged_feedback = (
                    f"{_merged_feedback}\n\n[전략별 보정 피드백]\n{strategy_feedback}"
                    if _merged_feedback
                    else f"[전략별 보정 피드백]\n{strategy_feedback}"
                )
            if _merged_feedback:
                extra_directive = f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 [CRITICAL] Director REJECT 피드백 - 이전 시도 실패 원인
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{_merged_feedback}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 위 피드백을 반드시 반영하세요. 동일한 실수 반복 시 다시 REJECT됩니다.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

            # [V60.90] protagonist_config 기반 지시사항 생성 (genre 파라미터 전달)
            protagonist_instructions = self._build_protagonist_instructions(protagonist_config, genre=genre)

            # [V70] POV 제약 생성
            _pov = protagonist_config.get("pov", "") if isinstance(protagonist_config, dict) else ""
            _pov_constraint = ""
            if _pov == "1인칭":
                _pov_constraint = """### 🎯 [V70] 시점 제약: 1인칭
⚠️ 이 작품은 1인칭 시점입니다. Blueprint 설계 시:
- villain_scheme, omniscient_hint 프리셋 사용 금지 (주인공 부재 장면 불가)
- 모든 씬에 주인공이 반드시 등장해야 함
- 주인공이 모르는 정보는 씬에 직접 노출 금지 → 나중에 전해 듣거나 발견하는 구조로 설계"""
            elif _pov == "3인칭":
                _pov_constraint = """### 📖 [V70] 시점: 3인칭 제한적
- villain_scheme, side_glimpse는 씬 전환(***) 후 짧게만 사용 (1-2문단)
- omniscient_hint는 화당 1회 이내로 제한"""

            # [TF-I23/I24] 독자 피드백 컨텍스트 (advisory-only)
            _external_pov_insert_policy = (
                protagonist_config.get("external_pov_insert_policy", "") if isinstance(protagonist_config, dict) else ""
            )
            _pov_constraint = build_external_pov_policy_constraint(
                _pov,
                _external_pov_insert_policy,
                genre=genre,
            )
            _reader_fb = self._build_reader_feedback_context(ep_num)
            _work_retrieval_contract = ""
            try:
                _guard = getattr(self.context, "guard", None)
                if _guard and hasattr(_guard, "get_retrieval_contract_prompt"):
                    _work_retrieval_contract = str(_guard.get_retrieval_contract_prompt("blueprint") or "").strip()
            except Exception as _e:
                logging.debug("[BPEnsemble] work retrieval contract 로드 실패: %s", _e)
            _use_cached_context = bool(cache_name)
            _cached_context_stub = "[context cached: refer to cached_content]"
            prompt = self._prompt_loader.load(
                "ensemble",
                "BLUEPRINT_GENERATION_PROMPT",
                strategy_display=strategy["display"],
                ep_num=ep_num,
                protagonist_name=self._escape_braces(protagonist_name),  # [V70] 주인공 이름 주입
                protagonist_instructions=self._escape_braces(protagonist_instructions),  # [V70] 주인공 설정 지시
                arc_focus=self._escape_braces(_cached_context_stub if _use_cached_context else arc_focus),
                constraints=self._escape_braces(_cached_context_stub if _use_cached_context else constraints_str),
                strategy_directive=self._escape_braces(
                    strategy["directive"]
                    + AI_TELL_BLUEPRINT_GUARDRAIL
                    + extra_directive
                    + (f"\n\n{_work_retrieval_contract}" if _work_retrieval_contract else "")
                ),  # [V70] Director feedback 내 {} 방어
                prev_info=self._escape_braces(_cached_context_stub if _use_cached_context else prev_info),
                hud_context=(
                    self._escape_braces(_cached_context_stub if _use_cached_context else hud_context)
                    if hud_context
                    else "(상태 정보 없음)"
                ),  # [V60.95]
                pov_constraint=self._escape_braces(_pov_constraint),  # [V70] [TF-S3-10]
                reader_feedback=self._escape_braces(_reader_fb) if _reader_fb else "",  # [TF-I23/I24]
            )
            full_prompt_fallback = prompt
            if _use_cached_context:
                full_prompt_fallback = self._prompt_loader.load(
                    "ensemble",
                    "BLUEPRINT_GENERATION_PROMPT",
                    strategy_display=strategy["display"],
                    ep_num=ep_num,
                    protagonist_name=self._escape_braces(protagonist_name),  # [V70] 주인공 이름 주입
                    protagonist_instructions=self._escape_braces(protagonist_instructions),  # [V70] 주인공 설정 지시
                    arc_focus=self._escape_braces(arc_focus),
                    constraints=self._escape_braces(constraints_str),
                    strategy_directive=self._escape_braces(
                        strategy["directive"]
                        + AI_TELL_BLUEPRINT_GUARDRAIL
                        + extra_directive
                        + (f"\n\n{_work_retrieval_contract}" if _work_retrieval_contract else "")
                    ),  # [V70] Director feedback 내 {} 방어
                    prev_info=self._escape_braces(prev_info),
                    hud_context=self._escape_braces(hud_context) if hud_context else "(상태 정보 없음)",  # [V60.95]
                    pov_constraint=self._escape_braces(_pov_constraint),  # [V70] [TF-S3-10]
                    reader_feedback=self._escape_braces(_reader_fb) if _reader_fb else "",  # [TF-I23/I24]
                )
                if not full_prompt_fallback:
                    full_prompt_fallback = prompt
            if not prompt:
                logging.warning("[BPEnsemble] BLUEPRINT_GENERATION_PROMPT not found in prompt loader")
                return None, AgentErrorType.UNKNOWN

            _strategy_name = strategy.get("name", "unknown")
            self._operator_log(
                f"⏳ [Blueprint] '{_strategy_name}' LLM 호출 중...",
                meta={"strategy": _strategy_name},
            )
            response = self._ask_with_cached_context(
                cache_name=cache_name,
                prompt=prompt,
                temperature=0.7,
                thinking_level="medium",
                full_prompt_fallback=full_prompt_fallback,
                response_schema=BLUEPRINT_SCHEMA,
            )
            self._operator_log(
                f"📝 [Blueprint] '{_strategy_name}' 응답 수신 ({len(response):,}자)",
                meta={"strategy": _strategy_name, "response_chars": len(response)},
            )
            result = self._extract_json_robust(response)

            if not isinstance(result, dict):
                return None, AgentErrorType.SCHEMA_INCOMPATIBLE

            # 필수 필드 확인
            if "scene_breakdown" not in result or "integrated_scenario" not in result:
                return None, AgentErrorType.SCHEMA_INCOMPATIBLE

            return result

        except Exception as e:
            # [V61.3] stderr로 출력 (Rich 스피너가 stdout 가림)
            import traceback

            logging.error(f" [V61.3] BPEnsemble _generate_single 크래시: {str(e)[:80]}")
            logging.error(traceback.format_exc())
            return None, self._classify_error(e)

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
        """Format compact blueprint constraints for the generation prompt."""
        lines: list[str] = []

        must_focus = constraint_block.get("must_focus", {})
        if isinstance(must_focus, dict):
            arc_title = str(must_focus.get("arc_title", "") or "").strip()
            if arc_title:
                lines.append("[이번 화 제목]")
                lines.append(f"  {_fit_compact_context(arc_title, 120)}")
            key_events = must_focus.get("key_events") or []
            if isinstance(key_events, list) and key_events:
                lines.append("[이번 화 필수 이벤트]")
                for event in key_events[:5]:
                    text = str(event or "").strip()
                    if text:
                        lines.append(f"  - {_fit_compact_context(text, 120)}")
            content = str(must_focus.get("content", "") or "").strip()
            if content and not key_events:
                lines.append("[이번 화 핵심 초점]")
                lines.append(f"  {_fit_compact_context(content, 500)}")

        stop_line = constraint_block.get("stop_line", {})
        if isinstance(stop_line, dict) and stop_line.get("content"):
            lines.append("\n[Stop Line]")
            lines.append(f"  다음 화 내용 금지: {_fit_compact_context(stop_line['content'], 150)}")

        continuity = constraint_block.get("continuity", {})
        if isinstance(continuity, dict):
            continuity_lines: list[str] = []
            if continuity.get("location"):
                continuity_lines.append(f"  이전 종료 위치: {_fit_compact_context(continuity['location'], 120)}")
            if continuity.get("time_context"):
                continuity_lines.append(f"  시간 맥락: {_fit_compact_context(continuity['time_context'], 100)}")
            conflicts = continuity.get("ongoing_conflicts") or []
            if isinstance(conflicts, list):
                for item in conflicts[:5]:
                    text = str(item or "").strip()
                    if text:
                        continuity_lines.append(f"  - 진행 중 갈등: {_fit_compact_context(text, 80)}")
            elif conflicts:
                continuity_lines.append(f"  - 진행 중 갈등: {_fit_compact_context(conflicts, 200)}")
            active = continuity.get("active_characters") or []
            if isinstance(active, list) and active:
                names = [_fit_compact_context(str(item or "").strip(), 20) for item in active[:10] if str(item or "").strip()]
                if names:
                    continuity_lines.append(f"  등장 캐릭터: {', '.join(names)}")
            elif active:
                continuity_lines.append(f"  등장 캐릭터: {_fit_compact_context(active, 200)}")
            if continuity_lines:
                lines.append("\n[연속성]")
                lines.extend(continuity_lines)

        inherited = constraint_block.get("inherited_state", {})
        if isinstance(inherited, dict):
            inherited_lines: list[str] = []
            equip = inherited.get("equipment")
            if equip:
                if isinstance(equip, list):
                    equip = ", ".join(str(x) if not isinstance(x, dict) else str(x.get("name", x)) for x in equip[:5])
                inherited_lines.append(f"  장비: {_fit_compact_context(equip, 200)}")
            injuries = inherited.get("injuries")
            if injuries:
                if isinstance(injuries, list):
                    inherited_lines.append(
                        f"  부상: {', '.join(_fit_compact_context(i, 40) for i in injuries[:5])}"
                    )
                else:
                    inherited_lines.append(f"  부상: {_fit_compact_context(injuries, 200)}")
            if genre == "wuxia" and inherited.get("internal_energy") is not None:
                inherited_lines.append(f"  내공/에너지: {_fit_compact_context(inherited['internal_energy'], 80)}")
            if inherited.get("mood"):
                inherited_lines.append(f"  심리 상태: {_fit_compact_context(inherited['mood'], 100)}")
            if inherited_lines:
                lines.append("\n[계승 상태]")
                lines.extend(inherited_lines)

        arc_summary = constraint_block.get("arc_constraint_summary")
        if arc_summary:
            lines.append("\n[Arc 제약 요약]")
            if isinstance(arc_summary, str):
                lines.append(f"  {_fit_compact_context(arc_summary, 500)}")
            elif isinstance(arc_summary, dict):
                for key, value in list(arc_summary.items())[:10]:
                    lines.append(f"  {key}: {_fit_compact_context(value, 100)}")

        sc_summary = constraint_block.get("state_changes_summary")
        if sc_summary:
            lines.append("\n[상태 변경 요약]")
            if isinstance(sc_summary, str):
                lines.append(f"  {_fit_compact_context(sc_summary, 800)}")
            elif isinstance(sc_summary, dict):
                deaths = sc_summary.get("npc_deaths", [])
                if deaths:
                    names = [
                        d.get("name", d.get("npc", str(d))) if isinstance(d, dict) else str(d) for d in deaths[:10]
                    ]
                    lines.append(f"  사망 NPC: {', '.join(names)}")
                skills = sc_summary.get("skill_acquisitions", [])
                if skills:
                    names = [
                        s.get("name", s.get("skill", str(s))) if isinstance(s, dict) else str(s) for s in skills[:10]
                    ]
                    lines.append(f"  획득 기술: {', '.join(names)}")
                resolved = sc_summary.get("resolved_plots", [])
                if resolved:
                    names = [
                        r.get("plot", r.get("description", str(r))) if isinstance(r, dict) else str(r)
                        for r in resolved[:10]
                    ]
                    lines.append(f"  해결 플롯: {', '.join(names)}")
                permanent = sc_summary.get("permanent_injuries", [])
                if permanent:
                    descs = [
                        _fit_compact_context(p, 50)
                        if not isinstance(p, dict)
                        else _fit_compact_context(p.get("description", str(p)), 50)
                        for p in permanent[:5]
                    ]
                    lines.append(f"  영구 부상: {', '.join(descs)}")

        semantic_carryover = constraint_block.get("semantic_carryover")
        if isinstance(semantic_carryover, dict) and semantic_carryover:
            lines.append("\n[Arc Semantic Carryover]")
            for entry in semantic_carryover.get("relationship_rationale", []) or []:
                if not isinstance(entry, dict):
                    continue
                npc = str(entry.get("npc", "") or "").strip() or "?"
                cue = str(entry.get("trigger", "") or entry.get("justification", "") or "").strip()
                if cue:
                    lines.append(f"  relationship {npc}: {_fit_compact_context(cue, 120)}")
            growth = str(semantic_carryover.get("growth_justification", "") or "").strip()
            if growth:
                lines.append(f"  growth_justification: {_fit_compact_context(growth, 140)}")
            for anchor in (semantic_carryover.get("foreshadow_anchors", []) or [])[:3]:
                text = str(anchor or "").strip()
                if text:
                    lines.append(f"  foreshadow: {_fit_compact_context(text, 120)}")
            checkpoints = [
                _fit_compact_context(str(item or "").strip(), 80)
                for item in (semantic_carryover.get("continuity_checkpoints", []) or [])[:3]
            ]
            checkpoints = [item for item in checkpoints if item]
            if checkpoints:
                lines.append(f"  continuity: {'; '.join(checkpoints)}")

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

    def _format_prev_info_expanded(
        self, prev_blueprint: dict | None, prev_blueprints: list[dict] | None = None, prev_manuscripts_text: str = ""
    ) -> str:
        """[V67] 이전 Blueprint/원고 확장 정보 포맷팅 (Gemini 대용량 컨텍스트 활용)"""
        sections = []

        # ── 직전 Blueprint 상세 (필수 계승) ──
        direct_prev = self._format_prev_info(prev_blueprint)
        sections.append(direct_prev)

        # ── [V67] 이전 Blueprint 전문 (최대 30개) ──
        if prev_blueprints and len(prev_blueprints) > 0:
            bp_lines = []
            bp_lines.append(f"\n[V67] ═══ 이전 Blueprint 전문 ({len(prev_blueprints)}개) ═══")
            bp_lines.append("이전 에피소드의 설계도입니다. 모순되는 내용을 절대 생성하지 마세요.")
            for bp in prev_blueprints:
                bp_ep = bp.get("ep_num", "?")
                bp_title = bp.get("title", "")
                bp_scenario = bp.get("integrated_scenario", "")
                bp_end_loc = bp.get("end_location", "")
                bp_hook = bp.get("ending_hook", "")
                bp_lines.append(f"\n━━━ 제{bp_ep}화 '{bp_title}' ━━━")
                if bp_scenario:
                    bp_lines.append(f"[시나리오] {bp_scenario}")
                if bp_end_loc:
                    bp_lines.append(f"[종료위치] {bp_end_loc}")
                if bp_hook:
                    bp_lines.append(f"[엔딩훅] {bp_hook}")
                # 씬 구성 요약
                scenes = bp.get("scene_breakdown", {})
                # [V70] list 타입 대응 (LLM이 list로 반환하는 경우)
                if isinstance(scenes, list):
                    scenes = {f"scene_{i + 1}": s for i, s in enumerate(scenes) if isinstance(s, dict)}
                if isinstance(scenes, dict):
                    for sk, sv in scenes.items():
                        if isinstance(sv, dict):
                            s_title = sv.get("title", "")
                            s_chars = sv.get("characters", [])
                            s_events = sv.get("key_events", [])
                            # [V70] 타입 방어 (str → list 변환)
                            if isinstance(s_chars, str):
                                s_chars = [s_chars]
                            if isinstance(s_events, str):
                                s_events = [s_events]
                            chars_str = (
                                _fit_compact_context(
                                    ", ".join(str(item or "").strip() for item in s_chars if str(item or "").strip()),
                                    120,
                                )
                                if s_chars
                                else ""
                            )
                            events_str = (
                                _fit_compact_context(
                                    "; ".join(str(item or "").strip() for item in s_events if str(item or "").strip()),
                                    180,
                                )
                                if s_events
                                else ""
                            )
                            bp_lines.append(
                                f"  [{sk}] {_fit_compact_context(s_title, 80)} | 등장: {chars_str} | 이벤트: {events_str}"
                            )

            bp_full = "\n".join(bp_lines)
            # 400K자 상한 (Gemini 1.05M 토큰 입력 여유)
            if len(bp_full) > 400000:
                bp_full = smart_truncate(
                    bp_full,
                    max_chars=400000,
                    head_chars=max(0, min(int(400000 * 0.55), 400000 - 80)),
                )
            sections.append(bp_full)

        # ── [V67] 이전 원고 전문 ──
        if prev_manuscripts_text:
            ms_section = (
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
