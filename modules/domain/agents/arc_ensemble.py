"""
[V60.11] Arc Ensemble Generator
병렬로 다수 Arc 후보를 생성하고 최적 후보를 선택

Strategy:
1. 3개의 서로 다른 전략으로 Arc 후보 생성 (병렬)
2. 각 후보를 빠르게 검증 (Python 기반)
3. 점수가 가장 높은 후보 선택
4. 모든 후보가 실패하면 피드백 통합하여 재생성

Cost: ~3x single generation (but higher pass rate)
"""

import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import TimeoutError as FutureTimeoutError

from modules.core.constants import GenreTypes, Stage2Limits
from modules.core.genre_schema_builder import build_state_constraints_schema, build_status_shadow_schema
from modules.core.prompt_loader import PromptLoader
from modules.core.response_schemas import ARC_DESIGN_SCHEMA  # [TF11] response_schema 확대

from .base_agent import _SYSTEM_CFG, BaseAgent

# [V60.95] 원시인 모드 금지어 Guard (JSON 기반)
try:
    from modules.core.primitive_guard import get_primitive_constraint_section

    PRIMITIVE_GUARD_AVAILABLE = True
except ImportError:
    PRIMITIVE_GUARD_AVAILABLE = False


# ── [장르별 에너지 시스템 블록] ──────────────────────────────────────
_WUXIA_ENERGY_BLOCK = """\
  ### [V62.2] 🩹 주인공 자연 회복 원칙 (무협 전용)
  - 주인공은 소설 주인공이다. 힐링팩터가 있다. 절대 약해지지 않는다.
  - 아크 시작: 부상="없음", 내공=이전 Arc 종료값 (최소 90%). 자연 회복 적용.
  - 화별 내공 규칙:
    · 한 화 안에서 긴장/전투로 소모 가능 (최저 60%까지만)
    · 다음 화 시작 시 반드시 90% 이상으로 회복
    · 내공이 화를 거듭하며 떨어지기만 하는 것은 절대 금지
    · 주인공은 점점 강해진다. 내공은 우상향이 기본이다.
  - 부상: Arc 내 일시적 피로/타박 허용, 다음 화면 회복됨. 만성화 금지.
  - arc_end_state: injuries="없음", internal_energy=최소 90 (이전 Arc 종료값 기반)
  - status_shadow: expected_injuries="없음", internal_energy_loss="자연 회복 적용"

  ### [V60.40] 화간 상태 체크포인트 필수
  각 화는 반드시 시작 상태와 종료 상태를 명시하라:
  - 시작 상태: 위치, 내공%, 부상, 소지품 (이전 화 종료 상태 기반 + 자연 회복 적용)
  - 종료 상태: 위치, 내공%, 부상, 획득/소모 아이템
  - ⚠️ 내공이 화를 넘기며 계속 떨어지는 패턴은 REJECT 사유임"""


def _build_non_wuxia_energy_block(genre: str, critical_keys: list[str] | None = None) -> str:
    """비무협 장르용 에너지 시스템 블록 동적 생성."""
    _ck = critical_keys or []
    _sc_field = build_state_constraints_schema(genre, _ck)
    # 장르 핵심 수치 라벨 추출 (예: "capital"→"자본금")
    _key_label = _sc_field.split(":")[0].strip().strip('"') if ":" in _sc_field else "핵심 수치"
    _desc = _sc_field.split(":", 1)[1].strip().strip('"') if ":" in _sc_field else "현재 상태"
    return f"""\
  ### [V62.2] 🩹 주인공 자연 회복 원칙
  - 주인공은 소설 주인공이다. 절대 약해지지 않는다.
  - 아크 시작: 부상="없음". 예외 없음.
  - ⚠️ 이 장르는 내공/기력 시스템이 없음. "내공" 표현 절대 금지.

  ### [V60.40] 화간 상태 체크포인트 필수
  각 화는 반드시 시작 상태와 종료 상태를 명시하라:
  - 시작 상태: 위치, {_key_label}({_desc}), 부상, 소지품
  - 종료 상태: 위치, {_key_label}({_desc}), 부상, 획득/소모 아이템
  - ⚠️ "내공", "기력", "내력" 등 무협 용어 사용 시 REJECT"""


# 다양한 생성 전략
GENERATION_STRATEGIES = [
    {
        "name": "conservative",
        "temperature": 0.3,
        "focus": "안정성과 연속성 우선. 이전 Arc 상태를 정확히 계승하고, 새로운 요소는 최소화.",
        "style": "기존 설정 활용 중심",
    },
    {
        "name": "balanced",
        "temperature": 0.5,
        "focus": "연속성과 새로움의 균형. 이전 상태를 계승하면서 적절한 새 갈등 도입.",
        "style": "균형 잡힌 전개",
    },
    {
        "name": "creative",
        "temperature": 0.7,
        "focus": "서사적 흥미 우선. 연속성을 유지하면서 예상치 못한 전개 시도.",
        "style": "창의적 전개",
    },
]


class ArcEnsembleGenerator(BaseAgent):
    """
    [V60.11] Arc Ensemble Generator

    병렬로 3개 Arc 후보 생성 후 최적 선택
    """

    # [V61.3→TF-26] 앙상블 타임아웃 — system.yaml ensemble_timeouts.arc 참조
    _TIMEOUTS = _SYSTEM_CFG.get("ensemble_timeouts", {}).get("arc", {})
    ENSEMBLE_TIMEOUT = _TIMEOUTS.get("ensemble", 300)
    SINGLE_CANDIDATE_TIMEOUT = _TIMEOUTS.get("single", 240)

    def __init__(
        self, context, client, model_tier: str = "gemini-2.5-pro"
    ):  # [SSOT-P2] 호출부(main_a.py:L1513)가 model_tier 인자를 명시 전달
        # [V62.4] gemini-2.5-pro로 변경 - 3-pro 쿼터 소진 문제 방지
        super().__init__(context, client, model_tier)
        # [V60.37] 스마트 폴백 (BaseAgent에서 자동 설정: gemini-3 → gemini-2.5-pro)
        self._prompt_loader = PromptLoader()
        self.strategies = GENERATION_STRATEGIES
        self.max_workers = 3

    def generate_ensemble(
        self,
        arc_no: int,
        ep_start: int,
        vol_strategy: str,
        curr_block: dict,
        prev_arc_context: str,
        constraint_block: str,
        prev_equipment: list[str] | None = None,
        forbidden_items: list[str] | None = None,
        assets: dict = None,
        feedback: str = "",
        strategy_specific_feedback: str = "",  # [EnsembleFB] 특정 전략 전용 추가 피드백
        rejected_strategy: str = "",  # [EnsembleFB] REJECT된 전략 이름
        protagonist_name: str = "주인공",  # [V60.18] 주인공 이름 (필수!)
        protagonist_config: dict = None,  # [V60.88] 주인공 설정 (world_origin, incarnation_type)
        entity_registry: dict = None,  # [V60.92] Entity Registry (NPC 명칭 일관성)
        ep_count: int = None,  # [V61.1] 가변 페이싱 - 상위에서 결정된 ep_count
        retry: int = 0,  # [V61.5] 재시도 횟수 (>0이면 thinking "medium"으로 다운그레이드)
        single_strategy: str = "",  # [TF-36] partial 시 1개 전략만
    ) -> tuple[dict | None, list[dict]]:
        """
        앙상블 Arc 생성

        Args:
            arc_no: Arc 번호
            ep_start: 시작 화수
            vol_strategy: Volume 전략
            curr_block: 현재 블록 DNA
            prev_arc_context: 이전 Arc 맥락
            constraint_block: 제약 조건 블록
            prev_equipment: 직전 Arc 종료 소지품(구조적 주입, 선택)
            forbidden_items: 금지 아이템 목록(구조적 주입, 선택)
            assets: AssetLibrary
            feedback: 이전 피드백
            protagonist_name: [V60.18] 주인공 이름 (환각 방지)
            protagonist_config: [V60.88] 주인공 설정 (world_origin, incarnation_type)
            entity_registry: [V60.92] Entity Registry (NPC 명칭 일관성)
            ep_count: [V61.1] 가변 페이싱 - 상위에서 결정된 화수 (None이면 기본값 5)

        Returns:
            (best_arc, all_candidates) - 최적 Arc와 모든 후보 리스트
        """
        # [V61.1] 가변 페이싱: 상위에서 결정된 ep_count 우선, 없으면 기본값 5
        if ep_count is None:
            ep_count = curr_block.get("ep_count", 5) if isinstance(curr_block, dict) else 5
        ep_end = ep_start + ep_count - 1
        candidates = []

        # [V61.3] 병렬 실행 전에 genre 미리 로드 (SQLite thread-safety 문제 방지)
        genre = GenreTypes.WUXIA
        try:
            if hasattr(self, "context") and hasattr(self.context, "db"):
                bible = self.context.db.load_anchor("bible")
                if bible:
                    genre = bible.get("_genre", GenreTypes.WUXIA)
        except Exception as e:
            logging.warning(f" [V61.3] genre 사전 로드 실패: {str(e)[:50]}")

        # [Phase 3-Obs] 에이전트 레벨 ThreadPoolExecutor 계측
        # [Tier4-11] shared context cache for ensemble fan-out
        shared_context = f"{prev_arc_context or ''}\n\n{constraint_block or ''}"
        cache_info = self._get_or_create_context_cache(
            cache_type="arc_ensemble",
            content=shared_context,
            ttl_seconds=600,
            project_name=f"arc{arc_no}",
        )
        cache_name = cache_info.get("cache_name")

        _tp_t0 = time.monotonic()

        # [TF-36] single_strategy 필터링 (partial 시 1개 전략만)
        _active_strategies = self.strategies
        if single_strategy:
            _filtered = [s for s in self.strategies if s.get("name") == single_strategy]
            if _filtered:
                _active_strategies = _filtered

        # [V61.3] 전체 병렬 처리 블록을 try-except로 감싸서 급사 방지
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {}
                for strategy in _active_strategies:
                    # [EnsembleFB] REJECT된 전략에만 전용 피드백 주입
                    _strategy_fb = (
                        strategy_specific_feedback
                        if (strategy["name"] == rejected_strategy and strategy_specific_feedback)
                        else ""
                    )
                    future = executor.submit(
                        self._generate_single,
                        arc_no=arc_no,
                        ep_start=ep_start,
                        ep_end=ep_end,
                        vol_strategy=vol_strategy,
                        curr_block=curr_block,
                        prev_arc_context=prev_arc_context,
                        constraint_block=constraint_block,
                        assets=assets,
                        feedback=feedback,
                        strategy_feedback=_strategy_fb,
                        strategy=strategy,
                        protagonist_name=protagonist_name,  # [V60.18]
                        protagonist_config=protagonist_config,  # [V60.88]
                        entity_registry=entity_registry,  # [V60.92]
                        genre=genre,  # [V61.3] 미리 로드한 genre 전달 (thread-safety)
                        retry=retry,  # [V61.5] 재시도 횟수 전달
                        cache_name=cache_name,  # [Tier4-11]
                    )
                    futures[future] = strategy["name"]

                _strat_names = ", ".join(futures.values())
                print(f"      🎲 [Arc] {len(futures)}개 전략 병렬 생성 중 ({_strat_names})...")
                # [V61.3] 타임아웃 적용 - 야간 무인 운영 시 무한 대기 방지
                try:
                    for future in as_completed(futures, timeout=self.ENSEMBLE_TIMEOUT):
                        strategy_name = futures[future]
                        try:
                            # [V61.3] 개별 후보에도 타임아웃 적용
                            result = future.result(timeout=self.SINGLE_CANDIDATE_TIMEOUT)
                            if result:
                                result["_strategy"] = strategy_name
                                candidates.append(result)
                                print(f"      ✓ [Arc] '{strategy_name}' 생성 완료 ({time.monotonic() - _tp_t0:.0f}초)")
                        except FutureTimeoutError:
                            logging.warning(f" [V61.3] {strategy_name} 전략 타임아웃 ({self.SINGLE_CANDIDATE_TIMEOUT}초)"
                            )
                            print(f"      ✗ [Arc] '{strategy_name}' 타임아웃")
                        except Exception as e:
                            logging.warning(f" [Ensemble] {strategy_name} 전략 실패: {str(e)[:50]}")
                            print(f"      ✗ [Arc] '{strategy_name}' 실패")
                except FutureTimeoutError:
                    # 전체 앙상블 타임아웃 - 완료된 후보만 사용
                    logging.warning(f" [V61.3] 앙상블 전체 타임아웃 ({self.ENSEMBLE_TIMEOUT}초) - 완료된 {len(candidates)}개 후보 사용"
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

            logging.error(f" [V61.3] Arc 병렬 처리 크래시 방지: {str(e)[:100]}")
            logging.error(traceback.format_exc())

        # [Phase 3-Obs] 병렬 구간 소요 시간 기록
        try:
            logging.warning(f"[PerfTimer:ArcEnsemble] arc_{arc_no}_ensemble={time.monotonic() - _tp_t0:.2f}s")
        except Exception as _e:
            logging.debug("[ArcEnsemble] PerfTimer 기록 실패 (무시): %s", _e)

        if not candidates:
            return None, []

        # [V60.73] tactical_doc 최소 길이 필터 (가변 페이싱: 화당 500자)
        min_tactical_length = ep_count * Stage2Limits.MIN_CHARS_PER_EPISODE  # 3화=1500자, 5화=2500자, 7화=3500자
        valid_candidates = []
        for candidate in candidates:
            # [V60.74] tactical_doc 타입 안전 변환 (dict/list 처리)
            tactical = candidate.get("tactical_doc", "")
            tactical = self._safe_tactical_str(tactical)
            candidate["tactical_doc"] = tactical  # 변환된 값으로 업데이트
            tactical_len = len(tactical)
            if tactical_len >= min_tactical_length:
                valid_candidates.append(candidate)
            else:
                logging.info(f" [Ensemble] {candidate.get('_strategy', '?')} 제외: tactical_doc {tactical_len}자 < {min_tactical_length}자 (ep_count={ep_count})"
                )
                print(
                    f"      ✗ [Arc] '{candidate.get('_strategy', '?')}' 분량 미달 ({tactical_len}자 < {min_tactical_length}자)"
                )

        # [V60.74] 유효한 후보가 없으면 최장 후보 선택 + 경고 레벨 판단
        if not valid_candidates:

            def safe_tactical_len(x):
                t = x.get("tactical_doc", "")
                return len(t) if isinstance(t, str) else len(str(t)) if t else 0

            candidates.sort(key=safe_tactical_len, reverse=True)
            longest = candidates[0]
            longest_len = safe_tactical_len(longest)
            min_required = ep_count * Stage2Limits.MIN_CHARS_PER_EPISODE

            # 권장값의 60% 미만이면 경고 레벨 높임
            if longest_len < min_required * 0.6:
                logging.warning(f" [Ensemble] 모든 후보 심각한 분량 부족: {longest_len}자 < {int(min_required * 0.6)}자 (권장의 60%)"
                )
                logging.warning("→ Critic/Consensus에서 REJECT 가능성 높음")
            else:
                logging.warning(f" [Ensemble] 모든 후보 분량 미달, 최대 분량 후보 선택: {longest_len}자")

            valid_candidates = candidates[:1]

        # 후보 평가 및 선택
        scored_candidates = []
        for candidate in valid_candidates:
            score, issues = self._evaluate_candidate(
                candidate,
                prev_arc_context,
                constraint_block,
                prev_equipment=prev_equipment,
                forbidden_items=forbidden_items,
            )
            candidate["_score"] = score
            candidate["_issues"] = issues
            scored_candidates.append(candidate)

        # 점수순 정렬
        scored_candidates.sort(key=lambda x: x.get("_score", 0), reverse=True)

        best = scored_candidates[0]
        # [V60.37] 타입 안전성
        best_tactical = best.get("tactical_doc", "")
        tactical_len = (
            len(best_tactical) if isinstance(best_tactical, str) else len(str(best_tactical)) if best_tactical else 0
        )

        # [V61.3] 후보별 점수 비교 출력
        logging.warning(" [Ensemble] 후보 비교:")
        _filtered_count = len(candidates) - len(scored_candidates)
        _filter_note = f" (분량미달 {_filtered_count}개 제외)" if _filtered_count > 0 else ""
        print(f"      📋 [Arc] {len(scored_candidates)}/{len(candidates)}개 후보 비교{_filter_note}")
        for c in scored_candidates:
            strategy = c.get("_strategy", "?")
            score = c.get("_score", 0)
            issues = c.get("_issues", [])
            issue_summary = f" - {issues[0][:40]}..." if issues else ""
            marker = "→" if c is best else " "
            logging.info(f"{marker} {strategy}: {score}점{issue_summary}")
            _pick = "→" if c is best else " "
            print(f"        {_pick} {strategy}: {score}점{issue_summary}")
        logging.info(f"→ {best.get('_strategy')} 선택 (tactical: {tactical_len}자)")
        print(f"      🏆 [Arc] '{best.get('_strategy')}' 선택 ({tactical_len}자)")

        # [V60.74] 메타데이터 보존 (디버깅용) - _ensemble_meta에 저장
        ensemble_meta = {
            "best_strategy": best.get("_strategy", "unknown"),
            "best_score": best.get("_score", 0),
            "all_scores": [(c.get("_strategy", "?"), c.get("_score", 0)) for c in scored_candidates],
            "total_candidates": len(scored_candidates),
        }
        best["_ensemble_meta"] = ensemble_meta

        # 메타데이터 제거 후 반환 (단, _ensemble_meta·_strategy는 유지)
        for c in scored_candidates:
            # _strategy는 Director 비교용으로 보존 [TF-47]
            c.pop("_score", None)
            c.pop("_issues", None)

        return best, scored_candidates

    def _generate_single(
        self,
        arc_no: int,
        ep_start: int,
        ep_end: int,
        vol_strategy: str,
        curr_block: dict,
        prev_arc_context: str,
        constraint_block: str,
        assets: dict,
        feedback: str,
        strategy_feedback: str = "",  # [EnsembleFB] 전략별 보정 피드백
        strategy: dict = None,
        protagonist_name: str = "주인공",  # [V60.18]
        protagonist_config: dict = None,  # [V60.88]
        entity_registry: dict = None,  # [V60.92]
        genre: str = GenreTypes.WUXIA,  # [V61.3] 미리 로드한 genre (thread-safety)
        retry: int = 0,  # [V61.5] 재시도 횟수
        cache_name: str = "",  # [Tier4-11] shared context cache name
    ) -> dict | None:
        """단일 전략으로 Arc 생성"""
        try:
            # [EnsembleFB] 전략별 보정 피드백 병합
            _merged_feedback = feedback or ""
            if strategy_feedback:
                _merged_feedback = (
                    f"{_merged_feedback}\n\n[전략별 보정 피드백]\n{strategy_feedback}"
                    if _merged_feedback
                    else f"[전략별 보정 피드백]\n{strategy_feedback}"
                )

            # [V60.13] 최우선 금지 요약 생성 - 프롬프트 최상단에 배치
            prohibition_summary = self._generate_prohibition_summary(prev_arc_context, constraint_block)

            # [V60.88] 주인공 설정 기반 지침 생성
            protagonist_instructions = ""
            if protagonist_config:
                world_origin = protagonist_config.get("world_origin", "원시인")
                incarnation_type = protagonist_config.get("incarnation_type", "회귀자")
                lines = [f"- 세계 출신: {world_origin}", f"- 환생 유형: {incarnation_type}"]

                # [V61.3] genre는 이제 파라미터로 전달받음 (DB 접근 제거 - thread-safety)

                # [V60.96] 원시인 모드: 장르별 JSON 기반 PrimitiveGuard 사용
                if world_origin == "원시인":
                    if PRIMITIVE_GUARD_AVAILABLE:
                        lines.append(get_primitive_constraint_section(protagonist_config, genre=genre, length="medium"))
                    else:
                        lines.append("⚠️ [원시인 모드] 현대 용어 절대 금지!")
                else:
                    lines.append("📝 주인공은 현대 사회를 알고 있음")

                if incarnation_type == "회귀자":
                    lines.append("🔄 미래를 알고 있음 (합리적 이유 없이는 내면 독백으로 처리)")
                elif incarnation_type == "빙의자":
                    lines.append("👤 원래 인물의 기억/관계를 의식")
                elif incarnation_type == "환생자":
                    lines.append("👶 전생의 기억이 있음")
                protagonist_instructions = "\n[🌍 주인공 설정]\n" + "\n".join(lines)

            # [V60.92] Entity Registry 섹션 생성
            entity_registry_section = self._format_entity_registry(entity_registry) if entity_registry else ""

            # [V62.2] genre_ext 가이드 생성 - 장르별 핵심 필드를 AI에게 명시
            genre_ext_guide = ""
            if isinstance(curr_block, dict):
                ge = curr_block.get("genre_ext") or (curr_block.get("raw_data") or {}).get("genre_ext")
                if ge and isinstance(ge, dict):
                    lines = [
                        "### [장르 특화 정보 - genre_ext]",
                        "이 블록의 장르 고유 데이터입니다. Arc 설계 시 반드시 반영하세요:",
                    ]
                    for k, v in ge.items():
                        lines.append(f"- **{k}**: {v}")
                    genre_ext_guide = "\n".join(lines)

            # [TF-9] 확장 블록 메타데이터 가이드 - 범용 직렬화 (장르 불문 자동 처리)
            # genre_ext/regression_ext/content/block_id/title/raw_data 외 나머지 필드 전체를 섹션화
            _BLOCK_STANDARD_FIELDS = {"block_id", "title", "content", "genre_ext", "regression_ext", "raw_data"}
            extended_block_guide = ""
            if isinstance(curr_block, dict):
                _ext_parts = []
                for _key, _val in curr_block.items():
                    if _key in _BLOCK_STANDARD_FIELDS or not _val:
                        continue
                    # 값 직렬화
                    if isinstance(_val, list):
                        _serialized = ", ".join(str(i) for i in _val) if _val else ""
                    elif isinstance(_val, dict):
                        _serialized = json.dumps(_val, ensure_ascii=False)
                    else:
                        _serialized = str(_val)
                    if _serialized:
                        _ext_parts.append(f"- **{_key}**: {_serialized}")
                if _ext_parts:
                    extended_block_guide = (
                        "### [블록 확장 메타데이터 - 반드시 Arc에 반영]\n"
                        "아래는 treatment 설계 시 포함된 핵심 연출 데이터입니다. "
                        "모든 항목을 Arc tactical_doc에 반영하세요.\n"
                        "특히 foreshadow는 tactical_doc 씬에 직접 심고, "
                        "callback은 이전 복선이 회수되는 씬을 명시하고, "
                        "emotional_beat/tension_level은 화별 감정 밀도 설계에 반영하세요:\n" + "\n".join(_ext_parts)
                    )

            _use_cached_context = bool(cache_name)
            _cached_context_stub = "[context cached: refer to cached_content]"

            # [TF-45] 장르별 스키마 필드 주입
            _ck = []
            try:
                if (
                    hasattr(self, "context")
                    and hasattr(self.context, "sys")
                    and hasattr(self.context.sys, "hud")
                    and self.context.sys.hud
                ):
                    _ck = self.context.sys.hud.get_critical_keys()
            except Exception as e:
                logging.debug("[TF-26] critical_keys lookup failed: %s", str(e)[:100])
            _sc_genre_field = self._escape_braces(build_state_constraints_schema(genre, _ck))
            _ss_schema = self._escape_braces(build_status_shadow_schema(genre, _ck))

            prompt = self._prompt_loader.load(
                "ensemble",
                "ENSEMBLE_ARC_PROMPT",
                strategy_name=strategy["name"].upper(),
                strategy_focus=strategy["focus"],
                strategy_style=strategy["style"],
                prohibition_summary=self._escape_braces(prohibition_summary),  # [V70]
                protagonist_name=self._escape_braces(protagonist_name),  # [V70]
                protagonist_instructions=self._escape_braces(protagonist_instructions),  # [V70]
                constraint_block=self._escape_braces(
                    _cached_context_stub if _use_cached_context else (constraint_block or "(없음)")
                ),
                prev_arc_context=self._escape_braces(
                    _cached_context_stub if _use_cached_context else (prev_arc_context or "시작점")
                ),
                curr_block=self._escape_braces(json.dumps(curr_block, ensure_ascii=False) if curr_block else "{}"),
                genre_ext_guide=self._escape_braces(genre_ext_guide),
                extended_block_guide=self._escape_braces(extended_block_guide),  # [TF-9]
                vol_strategy=self._escape_braces(vol_strategy[:6000] if vol_strategy else "(없음)"),
                assets=self._escape_braces(json.dumps(assets, ensure_ascii=False)[:6000] if assets else "{}"),
                feedback=self._escape_braces(_merged_feedback[:9000] if _merged_feedback else "(없음)"),
                entity_registry_section=self._escape_braces(entity_registry_section),  # [V60.92]
                energy_system_block=self._escape_braces(self._get_energy_system_block(genre, _ck)),
                state_constraints_genre_field=_sc_genre_field,
                status_shadow_schema=_ss_schema,
                arc_no=arc_no,
                ep_start=ep_start,
                ep_end=ep_end,
            )
            full_prompt_fallback = prompt
            if _use_cached_context:
                full_prompt_fallback = self._prompt_loader.load(
                    "ensemble",
                    "ENSEMBLE_ARC_PROMPT",
                    strategy_name=strategy["name"].upper(),
                    strategy_focus=strategy["focus"],
                    strategy_style=strategy["style"],
                    prohibition_summary=self._escape_braces(prohibition_summary),  # [V70]
                    protagonist_name=self._escape_braces(protagonist_name),  # [V70]
                    protagonist_instructions=self._escape_braces(protagonist_instructions),  # [V70]
                    constraint_block=self._escape_braces(constraint_block or "(없음)"),
                    prev_arc_context=self._escape_braces(prev_arc_context or "시작점"),
                    curr_block=self._escape_braces(json.dumps(curr_block, ensure_ascii=False) if curr_block else "{}"),
                    genre_ext_guide=self._escape_braces(genre_ext_guide),
                    extended_block_guide=self._escape_braces(extended_block_guide),  # [TF-9]
                    vol_strategy=self._escape_braces(
                        vol_strategy[:4000] if vol_strategy else "(없음)"
                    ),  # [TF-46] 2K→4K
                    assets=self._escape_braces(
                        json.dumps(assets, ensure_ascii=False)[:4000] if assets else "{}"
                    ),  # [TF-46] 2K→4K
                    feedback=self._escape_braces(_merged_feedback[:9000] if _merged_feedback else "(없음)"),
                    entity_registry_section=self._escape_braces(entity_registry_section),  # [V60.92]
                    energy_system_block=self._escape_braces(self._get_energy_system_block(genre, _ck)),
                    state_constraints_genre_field=_sc_genre_field,
                    status_shadow_schema=_ss_schema,
                    arc_no=arc_no,
                    ep_start=ep_start,
                    ep_end=ep_end,
                )
                if not full_prompt_fallback:
                    full_prompt_fallback = prompt
            if not prompt:
                logging.warning("[ArcEnsemble] ENSEMBLE_ARC_PROMPT not found in prompt loader")
                return None

            # [V60.27] Thinking Level 적용 - Arc 생성 품질 향상
            # [V61.5] 재시도 시 "medium"으로 다운그레이드 (피드백이 사고를 보조)
            thinking = "high" if retry == 0 else "medium"
            result = self._ask_with_cached_context(
                cache_name=cache_name,
                prompt=prompt,
                temperature=strategy["temperature"],
                thinking_level=thinking,
                full_prompt_fallback=full_prompt_fallback,
                response_schema=ARC_DESIGN_SCHEMA,  # [TF11] API 레벨 스키마 강제
            )

            if isinstance(result, str):
                result = self._extract_json_robust(result)
            # [V70] list/파싱에러 방어
            if not isinstance(result, dict) or result.get("parsing_error"):
                return None

            # 필수 필드 보장
            result = self._ensure_required_fields(result, arc_no, ep_start, ep_end)

            return result

        except Exception as e:
            # [V61.3] stderr로 출력 (Rich 스피너가 stdout 가림)
            import traceback

            logging.error(f" [V61.3] ArcEnsemble _generate_single 크래시: {str(e)[:80]}")
            logging.error(traceback.format_exc())
            return None

    def _evaluate_candidate(
        self,
        candidate: dict,
        prev_arc_context: str,
        constraint_block: str,
        prev_equipment: list[str] | None = None,
        forbidden_items: list[str] | None = None,
    ) -> tuple[int, list[str]]:
        """
        후보 평가 (100점 만점)

        평가 기준:
        - 필수 필드 완성도 (20점)
        - 제약 조건 준수 (30점)
        - 연속성 (25점)
        - tactical_doc 품질 (25점)
        """
        score = 100
        issues = []

        # 1. 필수 필드 완성도 (20점)
        # [V61] state_changes 추가
        required_fields = ["arc_no", "ep_count", "tactical_doc", "joint_docs", "state_constraints", "state_changes"]
        for field in required_fields:
            if field not in candidate or not candidate[field]:
                score -= 4
                issues.append(f"필수 필드 누락: {field}")

        # 2. 제약 조건 준수 (30점)
        if constraint_block or forbidden_items or candidate.get("_forbidden_items"):
            # 획득 금지 아이템 검사
            items_acquired = candidate.get("state_constraints", {}).get("items_acquired", [])
            tactical = candidate.get("tactical_doc", "")
            # [V60.37] 타입 안전성
            if not isinstance(tactical, str):
                tactical = str(tactical) if tactical else ""

            # Tier 1: 구조적 금지 아이템 (호출자 주입) 우선
            _forbidden_structured = forbidden_items
            if _forbidden_structured is None:
                _forbidden_structured = candidate.get("_forbidden_items", [])

            if _forbidden_structured:
                forbidden_items = [str(item).strip() for item in _forbidden_structured if str(item).strip()]
            else:
                # Tier 3: 문자열 regex 폴백
                forbidden_items = re.findall(r"❌\s*([가-힣\w]+)", constraint_block)
            # [V70] items_acquired를 str 리스트로 변환 (substring 오탐 방지)
            _acq_strs = [str(i).strip() for i in items_acquired] if isinstance(items_acquired, list) else []

            # [BUG-A] 기존 소지품 화이트리스트 — 이미 보유 중인 아이템은 금지 체크 스킵
            _existing_equip: set[str] = set()
            _start_eq = candidate.get("state_constraints", {}).get("arc_start_state", {}).get("equipment", [])
            if isinstance(_start_eq, list):
                _existing_equip.update(str(e).strip() for e in _start_eq if str(e).strip())
            _prev_eq = prev_equipment
            if _prev_eq is None:
                _prev_eq = candidate.get("_prev_equipment", [])
            if isinstance(_prev_eq, list):
                _existing_equip.update(str(e).strip() for e in _prev_eq if str(e).strip())

            for item in forbidden_items:
                if item in _existing_equip:
                    continue  # 이미 보유 중인 아이템은 스킵
                if item in _acq_strs or ("획득" in tactical and item in tactical):
                    score -= 15
                    issues.append(f"금지 아이템 획득 시도: {item}")

        # 3. 연속성 (25점)
        if (prev_arc_context and prev_arc_context != "서사 시작점") or prev_equipment or candidate.get("_prev_equipment"):
            # 시작 위치 검사
            start_state = candidate.get("state_constraints", {}).get("arc_start_state", {})
            if isinstance(prev_arc_context, str) and "위치" in prev_arc_context:
                prev_loc_match = re.search(r"위치[:\]]\s*([가-힣\w\s]+)", prev_arc_context)
                if prev_loc_match:
                    prev_loc = prev_loc_match.group(1).strip()[:20]
                    curr_loc = start_state.get("location", "")
                    if prev_loc and curr_loc and prev_loc not in curr_loc and curr_loc not in prev_loc:
                        score -= 10
                        issues.append(f"시작 위치 불일치: 이전={prev_loc}, 현재={curr_loc}")

            # 소지품 계승 검사
            curr_equip = start_state.get("equipment", [])
            prev_equipment_items: list[str] = []

            # Tier 1: 구조적 이전 Arc 소지품 (호출자 주입) 우선
            _prev_structured = prev_equipment
            if _prev_structured is None:
                _prev_structured = candidate.get("_prev_equipment", [])
            if _prev_structured:
                prev_equipment_items = [str(item).strip() for item in _prev_structured if str(item).strip()]

            # Tier 3: 문자열 컨텍스트 폴백
            if not prev_equipment_items and isinstance(prev_arc_context, str) and "소지품" in prev_arc_context:
                prev_inv_match = re.search(r"소지품[:\]]\s*([^\n]+)", prev_arc_context)
                if prev_inv_match:
                    prev_equipment_items = [x.strip() for x in prev_inv_match.group(1).split(",") if x.strip()]

            if prev_equipment_items and curr_equip:
                for item in prev_equipment_items[:5]:
                    if not any(item in str(ce) or str(ce) in item for ce in curr_equip):
                        score -= 5
                        issues.append(f"소지품 미계승: {item}")

        # 4. tactical_doc 품질 (25점) - [V60.73] 가변 페이싱 기준 (화당 500자)
        tactical = candidate.get("tactical_doc", "")
        # [V60.37] 타입 안전성
        if not isinstance(tactical, str):
            tactical = str(tactical) if tactical else ""
        ep_count = candidate.get("ep_count", 5)
        # [Sweep44] LLM이 문자열 반환 시 int 변환 (TypeError 방지)
        if not isinstance(ep_count, int):
            try:
                ep_count = int(ep_count)
            except (ValueError, TypeError):
                ep_count = 5
        min_length = ep_count * Stage2Limits.MIN_CHARS_PER_EPISODE  # 3화=1500자, 5화=2500자, 7화=3500자
        recommended_length = ep_count * 600  # 권장: 화당 600자
        if len(tactical) < min_length:
            score -= 40  # 최소 기준 미달은 사실상 실격
            issues.append(
                f"[CRITICAL] tactical_doc 분량 심각 부족: {len(tactical)}자 (최소 {min_length}자, ep_count={ep_count})"
            )
        elif len(tactical) < recommended_length:
            score -= 10
            issues.append(f"tactical_doc 분량 미흡: {len(tactical)}자 (권장 {recommended_length}자)")
        elif len(tactical) < ep_count * 700:
            score -= 5
            issues.append(f"tactical_doc 분량 보통: {len(tactical)}자")

        # 화수별 구분 검사 (ep_count는 상단에서 이미 int 변환됨)
        ep_mentions = len(re.findall(r"제\s*\d+\s*화", tactical))
        if ep_mentions < ep_count:
            score -= 5
            issues.append(f"화수 구분 부족: {ep_mentions}/{ep_count}")

        return max(0, score), issues

    def _ensure_required_fields(self, result: dict, arc_no: int, ep_start: int, ep_end: int) -> dict:
        """필수 필드 보장"""
        if "arc_no" not in result:
            result["arc_no"] = arc_no
        if "ep_start" not in result:
            result["ep_start"] = ep_start
        if "ep_end" not in result:
            result["ep_end"] = ep_end
        if "ep_count" not in result:
            result["ep_count"] = ep_end - ep_start + 1

        # [Sweep47] 타입도 검증 — LLM이 list/string 반환 시 AttributeError 방지
        if "state_constraints" not in result or not isinstance(result["state_constraints"], dict):
            result["state_constraints"] = {
                "arc_start_state": {"location": "이전 Arc 종료 위치", "equipment": []},
                "arc_end_state": {"location": "알 수 없음", "equipment": []},
                "items_acquired": [],
                "items_consumed": [],
            }

        if "joint_docs" not in result:
            result["joint_docs"] = {"final_location": "알 수 없음", "physical_inventory": [], "world_joint": ""}

        if "status_shadow" not in result:
            result["status_shadow"] = {
                "key_stat_change": "변동 없음",
                "expected_injuries": "없음",
                "item_consumption": [],
            }
        # backward-compat: 기존 소비자가 internal_energy_loss를 읽으므로 key_stat_change에서 복사
        _ss = result["status_shadow"]
        if "key_stat_change" in _ss and "internal_energy_loss" not in _ss:
            _ss["internal_energy_loss"] = _ss["key_stat_change"]

        # [V61] state_changes 필드 보장
        if "state_changes" not in result:
            result["state_changes"] = {
                "timeline": {"start": {}, "end": {}},
                "npc_deaths": [],
                "skill_acquisitions": [],
                "relationship_changes": [],
                "major_items": [],
                "resolved_plots": [],
            }
        else:
            # 하위 필드 보장
            sc = result["state_changes"]
            if "timeline" not in sc:
                sc["timeline"] = {"start": {}, "end": {}}
            elif not isinstance(sc["timeline"], dict):
                sc["timeline"] = {"start": {}, "end": {}}
            else:
                if "start" not in sc["timeline"]:
                    sc["timeline"]["start"] = {}
                if "end" not in sc["timeline"]:
                    sc["timeline"]["end"] = {}
            if "npc_deaths" not in sc:
                sc["npc_deaths"] = []
            if "skill_acquisitions" not in sc:
                sc["skill_acquisitions"] = []
            if "relationship_changes" not in sc:
                sc["relationship_changes"] = []
            if "major_items" not in sc:
                sc["major_items"] = []
            if "resolved_plots" not in sc:
                sc["resolved_plots"] = []

        return result

    def _safe_tactical_str(self, tactical) -> str:
        """
        [V60.74] tactical_doc을 안전하게 문자열로 변환

        Args:
            tactical: str, dict, list, None 등 다양한 타입

        Returns:
            str: 변환된 문자열
        """
        if isinstance(tactical, str):
            return tactical
        if tactical is None:
            return ""
        if isinstance(tactical, dict):
            # dict라면 값들을 조인 (content, text 등 우선 시도)
            if "content" in tactical:
                return str(tactical["content"])
            if "text" in tactical:
                return str(tactical["text"])
            # 그 외에는 모든 값 조인
            return "\n".join(str(v) for v in tactical.values() if v)
        if isinstance(tactical, list):
            return "\n".join(str(item) for item in tactical if item)
        # 기타 타입
        return str(tactical)

    def _generate_prohibition_summary(self, prev_arc_context: str, constraint_block: str) -> str:
        """
        [V60.13] 최우선 금지 사항 요약 생성

        프롬프트 최상단에 배치하여 LLM이 절대 무시할 수 없도록 함
        """
        lines = []

        # 1. 시작 상태 추출 (prev_arc_context에서)
        if prev_arc_context:
            # 내공 추출
            energy_match = re.search(r"내공[:\s]*(\d+)%", prev_arc_context)
            if energy_match:
                lines.append(f"✅ 시작 내공: {energy_match.group(1)}% (이 수치로 시작해야 함!)")

            # 부상 추출
            injury_patterns = ["완치", "없음", "중상", "경상", "부상"]
            for pattern in injury_patterns:
                if pattern in prev_arc_context:
                    if pattern in ["완치", "없음"]:
                        lines.append("✅ 시작 부상: 없음 (건강한 상태로 시작!)")
                    else:
                        lines.append(f"✅ 시작 부상: {pattern} (이 상태로 시작!)")
                    break

        # 2. 금지 아이템 추출 (constraint_block에서)
        if constraint_block:
            # ❌ 패턴 추출
            forbidden = re.findall(r"❌\s*([^\n❌]+)", constraint_block)
            if forbidden:
                lines.append("")
                lines.append("🚫 절대 다시 획득/수여 금지 (잔고·수량이 달라도 동일 아이템으로 간주):")
                for item in forbidden[:10]:
                    # 박스 문자, 패딩, Arc 출처 주석 제거 → 핵심 아이템명만 추출
                    clean_item = re.sub(r"\s*\(Arc\s*\d+.*?\)", "", item)
                    clean_item = re.sub(r"[│┤├─+|]", "", clean_item).strip()
                    clean_item = clean_item[:60]
                    if clean_item:
                        lines.append(f"   ❌ {clean_item}")
                lines.append("   ⚠️ items_acquired에 위 아이템명이 포함되면 즉시 REJECT됩니다.")

        # 3. 기본 경고
        if not lines:
            lines.append("(금지 사항 없음 - 첫 Arc)")

        return "\n".join(lines)

    # [V61.5] _escape_braces 오버라이드 제거 → BaseAgent의 이중 이스케이프 방지 로직 사용

    @staticmethod
    def _get_energy_system_block(genre: str, critical_keys: list[str] | None = None) -> str:
        """장르별 에너지(내공) 시스템 규칙 블록. 무협만 내공 규칙 포함."""
        if genre in ("wuxia", "무협"):
            return _WUXIA_ENERGY_BLOCK
        return _build_non_wuxia_energy_block(genre, critical_keys)

    def _format_entity_registry(self, entity_registry: dict) -> str:
        """
        [V60.92] Entity Registry를 프롬프트용 문자열로 변환
        NPC 명칭 일관성을 위해 등록된 이름만 사용하도록 안내
        """
        if not entity_registry:
            return ""

        lines = [
            "### [V60.92] 🏷️ Entity Registry - 명칭 일관성 필수!",
            "╔══════════════════════════════════════════════════════════════════╗",
            "║ ⚠️ 아래 등록된 이름만 사용하세요! 다른 명칭/별명 사용 금지!      ║",
            "╚══════════════════════════════════════════════════════════════════╝",
        ]

        categories = [
            ("characters", "👤 캐릭터"),
            ("organizations", "🏛️ 조직/문파"),
            ("locations", "📍 장소"),
            ("objects", "🗡️ 아이템/물건"),
            ("concepts", "📜 개념/기술"),
        ]

        has_content = False
        for key, label in categories:
            items = entity_registry.get(key, [])
            if items:
                has_content = True
                lines.append(f"\n{label}:")
                for item in items[:20]:  # 최대 20개
                    if isinstance(item, dict):
                        name = item.get("name", item.get("이름", str(item)))
                        alias = item.get("alias", item.get("별칭", ""))
                        if alias:
                            lines.append(f"  • {name} (={alias})")
                        else:
                            lines.append(f"  • {name}")
                    else:
                        lines.append(f"  • {item}")

        if not has_content:
            return ""

        lines.append("\n→ 위 목록에 없는 새 NPC/조직 등장 시 반드시 명확한 이름 부여!")
        return "\n".join(lines)


def create_ensemble_generator(
    context, client, model_tier: str = "gemini-2.5-pro"
):  # [SSOT-P2] 호출부(main_a.py:L1513)가 model_tier 인자를 명시 전달
    """[V62.4] ArcEnsembleGenerator 생성 헬퍼 - gemini-2.5-pro 사용"""
    return ArcEnsembleGenerator(context, client, model_tier)
