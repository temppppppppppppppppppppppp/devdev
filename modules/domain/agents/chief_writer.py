"""
[V60.80] Chief Writer - Stage 4 앙상블 원고 생성 엔진

Stage 4 "Director 주권주의" 아키텍처의 핵심 생성 에이전트.
3개 후보를 병렬 생성하여 Director에게 제출.

핵심 철학: "Blueprint를 토대로 양질의 원고를 연속성 있게 생산한다"

[V60.81] Writer 핵심 기능 통합:
- Self-Critique (다중 라운드 자체 검토)
- Leakage 방지 (출력 정제)
- NPC 빈도/장비 추적
- HUD 변화 추세 모니터링
- DNA 모드 (1화 특수 처리)
- Rubric 기반 품질 평가
"""

import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import TimeoutError as FutureTimeoutError

from modules.core.constants import smart_truncate
from modules.core.genre_schema_builder import build_state_updates_schema
from modules.models.manuscript import validate_manuscript_candidate

from .base_agent import _SYSTEM_CFG, BaseAgent
from .chief_writer_context import ChiefWriterContextBuilder, normalize_chief_writer_genre_code
from .chief_writer_prompts import (
    get_prompt_template_output,
)
from .chief_writer_quality import ChiefWriterQualityGate

# [TF-45] 한국어 장르명 → 코드 변환 (chief_writer_context.py와 동일)
_CW_GENRE_CODE_MAP = {
    "무협": "wuxia",
    "판타지": "fantasy",
    "헌터물": "hunter",
    "투자물": "investment",
    "스포츠": "sports",
    "의학": "medical",
    "배우물": "actor",
    "요리": "cooking",
    "작곡가": "composer",
    "대체역사": "alt_history",
}


class ChiefWriter(BaseAgent):
    """
    [V60.80] Chief Writer - 앙상블 원고 생성 엔진

    특징:
    - 3개 후보 병렬 생성 (균형/서사/긴장감)
    - CoT (Chain of Thought) 기반 전략적 집필
    - Director 피드백 반영 재생성
    """

    # [V61.3→TF-26] 앙상블 타임아웃 — system.yaml ensemble_timeouts.chief_writer 참조
    _TIMEOUTS = _SYSTEM_CFG.get("ensemble_timeouts", {}).get("chief_writer", {})
    ENSEMBLE_TIMEOUT = _TIMEOUTS.get("ensemble", 600)
    SINGLE_CANDIDATE_TIMEOUT = _TIMEOUTS.get("single", 540)

    # 앙상블 전략 정의
    ENSEMBLE_STRATEGIES = {
        "balanced": {
            "name": "균형 전략",
            "temperature": 0.7,
            "emphasis": "Blueprint 충실 재현",
            "instruction": """
[전략 A: 균형]
- Blueprint의 모든 씬을 균등한 비중으로 반영
- 서사와 액션의 조화로운 배분
- 안정적인 품질 우선
- ⚠️ 반드시 5,000자 이상 작성. 각 씬에 충분한 묘사와 대화를 배분할 것
""",
        },
        "narrative": {
            "name": "서사 강조",
            "temperature": 0.8,
            "emphasis": "심리 묘사 + 관계 발전",
            "instruction": """
[전략 B: 서사 강조]
- 캐릭터 내면 묘사 강화
- 관계 발전과 감정선에 집중
- 대화와 심리 갈등 확대
- ⚠️ 반드시 5,000자 이상 작성. 심리 묘사와 대화를 충분히 확장할 것
""",
        },
        "tension": {
            "name": "긴장감 + 반전 강조",
            "temperature": 0.9,
            "emphasis": "반전 + 클리프행어 + 예측 불가능 전개",
            "instruction": """
[전략 C: 몰입감 극대화]
- 독자 예측을 벗어나는 전개 1개 이상 포함
- 서스펜스와 긴장감 극대화. 정보를 독자에게 천천히 공개하라
- 강렬한 클리프행어 (단순 전투 외: 정보 폭탄, 배신, 반전)
- 캐릭터 간 긴장감 있는 대화 (침묵, 눈빛, 서브텍스트)
- ⚠️ 반드시 5,000자 이상 작성. 긴장 고조와 반전을 충분히 전개할 것
""",
        },
    }

    # [V64.P4] 프롬프트 외부화
    PROMPT_TEMPLATE_OUTPUT = get_prompt_template_output()

    def __init__(self, context, client, model_tier=None) -> None:
        super().__init__(context, client, model_tier)
        self._agent_name = "ChiefWriter"
        # [V60.82] 배치 캐시 - DB 쿼리 최적화
        self._manuscript_cache = {}  # {ep_num: content}
        self._cache_ep_num = -1  # 캐시 유효성 기준
        self._context_builder = None  # [B-1-4] lazy init
        self._quality_gate = None  # [B-1-5] lazy init
        # [V65] _emotion_skeleton_cache / _emotion_skeleton_blueprint_hash 삭제 (Emotion Skeleton Dead Code 제거)

    def _load_strategy_bias(self, strategy_names: list[str], *, lookback: int = 20) -> dict[str, float]:
        """최근 PASS 선택 비중을 전략별로 로드한다."""
        db_candidates = []
        for db in (
            self._resolve_logging_db(),
            getattr(self.context, "db", None),
        ):
            if db is None or not hasattr(db, "get_strategy_win_rates"):
                continue
            if any(existing is db for existing in db_candidates):
                continue
            db_candidates.append(db)

        for db in db_candidates:
            try:
                stats = db.get_strategy_win_rates(
                    lookback=lookback,
                    allowed_strategies=tuple(strategy_names),
                )
            except Exception as bias_err:
                logging.debug("[QR-3] ChiefWriter 전략 비중 조회 실패 (비치명): %s", bias_err)
                continue

            if not isinstance(stats, dict) or int(stats.get("total", 0) or 0) <= 0:
                continue
            return {name: float(stats.get(name, 0.0) or 0.0) for name in strategy_names}
        return {}

    def _build_strategy_execution_plan(self, strategy_names: list[str]) -> tuple[list[str], dict[str, float], dict[str, float]]:
        """전략 실행 순서와 temperature 보정값을 계산한다."""
        shares = self._load_strategy_bias(strategy_names)
        if not shares or all(shares.get(name, 0.0) <= 0 for name in strategy_names):
            return strategy_names, {}, shares

        ordered = sorted(strategy_names, key=lambda name: shares.get(name, 0.0), reverse=True)
        adjusted_temperatures: dict[str, float] = {}
        for name in strategy_names:
            base = float(self.ENSEMBLE_STRATEGIES[name]["temperature"])
            share = shares.get(name, 0.0)
            adjusted = base
            if share >= 0.5:
                adjusted = max(0.1, round(base - 0.05, 2))
            elif share <= 0.15:
                adjusted = min(1.0, round(base + 0.1, 2))
            elif share <= 0.3:
                adjusted = min(1.0, round(base + 0.05, 2))
            adjusted_temperatures[name] = adjusted

        logging.info(
            "[QR-3] ChiefWriter 전략 비중 적용: %s",
            ", ".join(f"{name}={int(shares.get(name, 0.0) * 100)}%" for name in ordered),
        )
        return ordered, adjusted_temperatures, shares

    def _select_ensemble_strategies(
        self,
        *,
        strategy_budget: str = "full",
        preferred_strategy: str = "",
        single_strategy: str = "",
    ) -> tuple[list[str], dict[str, float]]:
        """Resolve strategy set for the current ensemble budget."""
        strategies = ["balanced", "narrative", "tension"]

        if single_strategy:
            target = [name for name in strategies if name == single_strategy]
            return (target or ["balanced"]), {}

        if strategy_budget == "reduced":
            ordered: list[str] = []
            preferred = preferred_strategy if preferred_strategy in strategies else ""
            for name in (preferred, "balanced", "tension", "narrative"):
                if name and name not in ordered:
                    ordered.append(name)
                if len(ordered) >= 2:
                    break
            return ordered[:2], {}

        ordered, adjusted_temperatures, _ = self._build_strategy_execution_plan(strategies)
        return ordered, adjusted_temperatures

    @staticmethod
    def _build_char_ngrams(text: str, n: int = 3) -> set[str]:
        normalized = re.sub(r"\s+", " ", str(text or "")).strip()
        if not normalized:
            return set()
        if len(normalized) < n:
            return {normalized}
        return {normalized[i : i + n] for i in range(len(normalized) - n + 1)}

    def _annotate_candidate_diversity(self, candidates: list[dict], *, threshold: float = 0.7) -> dict:
        """후보 간 3-gram Jaccard 유사도를 계산해 metadata에 기록한다."""
        indexed_texts: list[tuple[int, str]] = []
        for idx, candidate in enumerate(candidates):
            if not isinstance(candidate, dict):
                continue
            manuscript = str(candidate.get("manuscript", "") or "").strip()
            if manuscript:
                indexed_texts.append((idx, manuscript))

        if len(indexed_texts) < 2:
            return {}

        labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        pairwise = []
        high_similarity_pairs = []
        max_similarity = 0.0
        for left_pos in range(len(indexed_texts)):
            left_idx, left_text = indexed_texts[left_pos]
            left_grams = self._build_char_ngrams(left_text)
            if not left_grams:
                continue
            for right_pos in range(left_pos + 1, len(indexed_texts)):
                right_idx, right_text = indexed_texts[right_pos]
                right_grams = self._build_char_ngrams(right_text)
                if not right_grams:
                    continue
                union = left_grams | right_grams
                similarity = (len(left_grams & right_grams) / len(union)) if union else 0.0
                similarity = round(similarity, 2)
                pair_label = f"{labels[left_idx]}-{labels[right_idx]}"
                pairwise.append({"pair": pair_label, "similarity": similarity})
                max_similarity = max(max_similarity, similarity)
                if similarity >= threshold:
                    high_similarity_pairs.append((pair_label, similarity))

        warning = ""
        if high_similarity_pairs:
            pairs_text = ", ".join(f"{pair} {int(score * 100)}%" for pair, score in high_similarity_pairs[:3])
            warning = f"[후보 다양성 경고] 후보 유사도 높음: {pairs_text}"

        summary = {
            "pairwise": pairwise,
            "max_similarity": round(max_similarity, 2),
            "high_similarity_pairs": [
                {"pair": pair, "similarity": similarity} for pair, similarity in high_similarity_pairs
            ],
            "warning": warning,
        }
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            metadata = candidate.setdefault("metadata", {})
            if isinstance(metadata, dict):
                metadata["diversity"] = summary
        return summary

    def _get_critical_keys_for_genre(self) -> list[str]:
        """[TF-45] 현재 프로젝트 HUD에서 critical_keys 추출."""
        try:
            ctx = getattr(self, "_context", None) or getattr(self, "context", None)
            if ctx and hasattr(ctx, "sys") and hasattr(ctx.sys, "hud") and ctx.sys.hud:
                return ctx.sys.hud.get_critical_keys()
        except Exception:
            pass
        return []

    @property
    def context_builder(self) -> "ChiefWriterContextBuilder":
        if self._context_builder is None:
            self._context_builder = ChiefWriterContextBuilder(self)
        return self._context_builder

    @property
    def quality_gate(self) -> "ChiefWriterQualityGate":
        if self._quality_gate is None:
            self._quality_gate = ChiefWriterQualityGate(self)
        return self._quality_gate

    def generate_ensemble(
        self,
        ep_num: int,
        blueprint: dict,
        prev_manuscript: str,
        hud_report: str,
        arc_doc: str,
        master_bible: dict,
        style_guide: str = "",
        reference_excerpt: str = "",
        director_feedback: str = "",
        strategy_specific_feedback: str = "",
        rejected_strategy: str = "",
        single_strategy: str = "",
        failure_constraints: str = "",
        # [V60.80 FIX] 미래 침범 방지용 추가 파라미터
        current_inventory: list[str] = None,
        current_martial_arts: list[str] = None,
        dead_npcs: list[str] = None,
        item_acquisition_timeline: str = "",
        # [V60.80+] 기존 Writer 핵심 기능 통합
        reference_anchor_prompt: str = "",
        mandatory_context: str = "",
        anti_trope_prompt: str = "",
        justification_prompt: str = "",
        reflexion_prompt: str = "",
        genre_name: str = "무협",
        # [V60.81] 추가 파라미터
        npc_equipment_summary: str = "",
        intro_dna: str = "",  # [QI-1-C3] CYNICAL 하드코딩 제거
        # [V60.85] 장르 Guard Purism Prompt
        purism_prompt: str = "",
        # [V60.95] 고밀도 HUD 전달
        state_tracker=None,
        # [V67] 이전 원고 전문 — 모순 방지용 컨텍스트
        prev_manuscripts_text: str = "",
        # [V68] 세계 상태 요약 — 장기연재 모순 방지
        world_state_summary: str = "",
        # [V68] 에피소드 연결고리 — 직전 화에서 이어받아야 할 것
        chain_link_section: str = "",
        # [emotional_beat] 감정 정점
        emotional_beat_section: str = "",
        # [B-4] 주인공 동기/약속
        motivations: list = None,
        promises: list = None,
        # [TF-49b] Arc 계획 아이템 사전 정당화
        upcoming_arc_items: list[str] = None,
        strategy_budget: str = "full",
        preferred_strategy: str = "",
    ) -> list[dict]:
        """
        3개 후보 원고 병렬 생성

        Args:
            ep_num: 에피소드 번호
            blueprint: Blueprint 데이터
            prev_manuscript: 직전 화 원고
            hud_report: 현재 HUD 상태
            arc_doc: Arc 전술 문서
            master_bible: 마스터 바이블
            style_guide: 플랫폼 스타일 가이드
            director_feedback: Director 피드백 (재시도 시)
            failure_constraints: 실패 학습 제약 (이전 REJECT 패턴)
            purism_prompt: 장르 Guard의 순혈주의 지침 (V60.85)
            prev_manuscripts_text: [V67] 이전 30화 원고 전문 (모순 방지용)
            world_state_summary: [V68] 세계 상태 요약 (장기연재 모순 방지)
            chain_link_section: [V68] 직전 화 연결고리 (다음 화에서 이어받을 것)

        Returns:
            List[Dict]: 3개 후보 원고 [{
                "strategy": str,
                "manuscript": str,
                "title": str,
                "state_updates": dict,
                "metadata": dict
            }]
        """
        # [V60.82] DB 배치 프리페치 - 중복 쿼리 제거
        self._prefetch_manuscripts(ep_num, window=10)

        # 공통 컨텍스트 구성
        common_context = self.context_builder.build_common_context(
            ep_num=ep_num,
            blueprint=blueprint,
            prev_manuscript=prev_manuscript,
            hud_report=hud_report,
            arc_doc=arc_doc,
            master_bible=master_bible,
            style_guide=style_guide,
            reference_excerpt=reference_excerpt,
            director_feedback=director_feedback,
            failure_constraints=failure_constraints,
            # 미래 침범 방지
            current_inventory=current_inventory or [],
            current_martial_arts=current_martial_arts or [],
            dead_npcs=dead_npcs or [],
            item_acquisition_timeline=item_acquisition_timeline,
            # 기존 Writer 핵심 기능
            reference_anchor_prompt=reference_anchor_prompt,
            mandatory_context=mandatory_context,
            anti_trope_prompt=anti_trope_prompt,
            justification_prompt=justification_prompt,
            reflexion_prompt=reflexion_prompt,
            genre_name=genre_name,
            # [V60.81] 추가 파라미터
            npc_equipment_summary=npc_equipment_summary,
            intro_dna=intro_dna,
            # [V60.85] 장르 Guard Purism Prompt
            purism_prompt=purism_prompt,
            # [V60.95] 고밀도 HUD 전달
            state_tracker=state_tracker,
            # [V67] 이전 원고 전문
            prev_manuscripts_text=prev_manuscripts_text,
            # [V68] 세계 상태 요약
            world_state_summary=world_state_summary,
            # [V68] 에피소드 연결고리
            chain_link_section=chain_link_section,
            emotional_beat_section=emotional_beat_section,
            # [TF-49b] Arc 계획 아이템 사전 정당화
            upcoming_arc_items=upcoming_arc_items,
        )

        # [V61.7] 컨텍스트 캐싱 시도 (토큰 비용 50-67% 절감)
        cache_name = None
        try:
            cache_info = self._get_or_create_context_cache(
                cache_type="manuscript",
                content=common_context,
                ttl_seconds=600,  # 10분 (같은 에피소드 재시도 대비)
                project_name=self._context_cache_project_namespace("ep", ep_num),
            )
            cache_name = cache_info.get("cache_name")
            if cache_name:
                logging.info(f" [V61.7] 컨텍스트 캐시 활성 (ep{ep_num}, {len(common_context)}자)")
        except Exception as e:  # [V64.P4] OPTIONAL: context caching
            logging.debug(f"[SILENT] context caching: {e}")
            pass  # 캐싱 실패해도 기존 방식으로 진행

        # 병렬 생성
        candidates = []
        strategies, _strategy_temperatures = self._select_ensemble_strategies(
            strategy_budget=strategy_budget,
            preferred_strategy=preferred_strategy,
            single_strategy=single_strategy,
        )

        # [Phase 3-Obs] 에이전트 레벨 ThreadPoolExecutor 계측
        _tp_t0 = time.monotonic()

        # [V61.3] 전체 병렬 처리 블록을 try-except로 감싸서 급사 방지
        try:
            with ThreadPoolExecutor(max_workers=max(1, min(3, len(strategies)))) as executor:
                futures = {}
                for strategy in strategies:
                    _feedback = (
                        strategy_specific_feedback
                        if (strategy == rejected_strategy and strategy_specific_feedback)
                        else ""
                    )
                    future = executor.submit(
                        self._generate_single_candidate,
                        ep_num=ep_num,
                        strategy=strategy,
                        blueprint=blueprint,
                        common_context=common_context,
                        hud_report=hud_report,
                        master_bible=master_bible,
                        genre_name=genre_name,
                        cache_name=cache_name,
                        strategy_feedback=_feedback,
                        motivations=motivations,
                        promises=promises,
                        strategy_temperature=_strategy_temperatures.get(strategy),
                    )
                    futures[future] = strategy

                _strat_names = ", ".join(futures.values())
                self._operator_log(
                    f"🎲 [Writer] {len(futures)}개 전략 병렬 생성 중 ({_strat_names})...",
                    meta={"candidate_count": len(futures), "strategies": list(futures.values())},
                )
                # [V61.3] 타임아웃 적용 - 야간 무인 운영 시 무한 대기 방지
                # [Sweep300-R41] 알려진 제한: as_completed(timeout=T)는 soft bound.
                # Python ThreadPoolExecutor는 실행 중인 스레드를 강제 중단할 수 없으므로,
                # LLM API 호출이 T초를 초과하면 실제 대기 시간 > T가 될 수 있다.
                # cancel()은 PENDING(미시작) future에만 유효하며, RUNNING future에는 무효.
                try:
                    for future in as_completed(futures, timeout=self.ENSEMBLE_TIMEOUT):
                        strategy = futures[future]
                        try:
                            # [V61.3] 개별 후보에도 타임아웃 적용
                            result = future.result(timeout=self.SINGLE_CANDIDATE_TIMEOUT)
                            if result:
                                candidates.append(result)
                                logging.info(f"✅ [ChiefWriter] 후보 {strategy} 생성 완료 ({len(result.get('manuscript', ''))}자)"
                                )
                                self._operator_log(
                                    f"✓ [Writer] '{strategy}' 완료 ({len(result.get('manuscript', ''))}자, {time.monotonic() - _tp_t0:.0f}초)",
                                    meta={
                                        "strategy": strategy,
                                        "manuscript_chars": len(result.get("manuscript", "")),
                                        "elapsed_seconds": round(time.monotonic() - _tp_t0, 1),
                                    },
                                )
                        except FutureTimeoutError:
                            logging.warning(f" [V61.3] 후보 {strategy} 타임아웃 ({self.SINGLE_CANDIDATE_TIMEOUT}초)")
                            self._operator_log(
                                f"✗ [Writer] '{strategy}' 타임아웃",
                                level="warning",
                                meta={"strategy": strategy, "timeout_seconds": self.SINGLE_CANDIDATE_TIMEOUT},
                            )
                            candidates.append(
                                {
                                    "strategy": strategy,
                                    "manuscript": "",
                                    "title": "",
                                    "state_updates": {},
                                    "metadata": {"error": "타임아웃"},
                                    "error": True,
                                }
                            )
                        except Exception as e:
                            logging.warning(f" [ChiefWriter] 후보 {strategy} 생성 실패: {str(e)[:50]}")
                            self._operator_log(
                                f"✗ [Writer] '{strategy}' 실패",
                                level="warning",
                                meta={"strategy": strategy},
                            )
                            # 실패한 전략은 빈 결과로 대체
                            candidates.append(
                                {
                                    "strategy": strategy,
                                    "manuscript": "",
                                    "title": "",
                                    "state_updates": {},
                                    "metadata": {"error": str(e)},
                                    "error": True,
                                }
                            )
                except FutureTimeoutError:
                    # 전체 앙상블 타임아웃 - 완료된 후보만 사용
                    logging.warning(f" [V61.3] 원고 앙상블 타임아웃 ({self.ENSEMBLE_TIMEOUT}초) - 완료된 {len(candidates)}개 후보 사용"
                    )
                except Exception as e:
                    # [V61.3] as_completed 자체 예외 처리
                    logging.warning(f" [V61.3] 원고 앙상블 루프 예외: {str(e)[:80]}")
                finally:
                    # [Sweep3-G2] 미완료 future 정리 — 백그라운드 실행 방지
                    for f in futures:
                        f.cancel()
        except Exception as e:
            # [V61.3] ThreadPoolExecutor 전체 예외 처리 - 급사 방지
            # stderr로 출력 (Rich 스피너가 stdout 가림)
            import traceback

            logging.error(f" [V61.3] 원고 병렬 처리 크래시 방지: {str(e)[:100]}")
            logging.error(traceback.format_exc())

        # [Phase 3-Obs] 병렬 구간 소요 시간 기록
        try:
            logging.warning(f"[PerfTimer:ChiefWriter] cw_ep{ep_num}_ensemble={time.monotonic() - _tp_t0:.2f}s")
        except Exception as _e:
            logging.debug("[CW] PerfTimer 기록 실패: %s", _e)

        # 최소 1개 후보 보장
        valid_candidates = [c for c in candidates if not c.get("error")]
        if not valid_candidates:
            logging.warning(" [ChiefWriter] 모든 후보 생성 실패 - 단일 재시도")
            self._operator_log("⚠️ [Writer] 전원 실패 → 단일 폴백 시도", level="warning")
            _fallback_strategy = strategies[0] if strategies else "balanced"
            fallback = self._generate_single_candidate(
                ep_num=ep_num,
                strategy=_fallback_strategy,
                blueprint=blueprint,
                common_context=common_context,
                hud_report=hud_report,
                master_bible=master_bible,
                genre_name=genre_name,
                cache_name=cache_name,
                motivations=motivations,
                promises=promises,
                strategy_temperature=_strategy_temperatures.get(_fallback_strategy),
                strategy_feedback=(
                    strategy_specific_feedback
                    if (_fallback_strategy == rejected_strategy and strategy_specific_feedback)
                    else ""
                ),
            )
            if fallback and not fallback.get("error"):
                candidates = [fallback]
            else:
                # [Sweep45] 에러 후보만 남은 상태 → 비우고 C-4 폴백으로 전환
                candidates = []

        # [V66.3] C-4: 모든 후보 생성 실패 시 에러 dict 반환 (빈 배열 방지 → downstream IndexError 크래시 방어)
        if not candidates:
            logging.error("[ChiefWriter] generate_ensemble: 앙상블 + 단일 폴백 모두 실패 — 에러 후보 반환")
            candidates = [
                {
                    "strategy": "error_fallback",
                    "strategy_name": "에러 폴백",
                    "manuscript": "",
                    "title": f"제{ep_num}화 (생성 실패)",
                    "state_updates": {},
                    "metadata": {"error": "모든 후보 생성 실패"},
                    "error": True,
                    "error_message": "모든 후보 생성 실패",
                }
            ]

        # [Step2] Pydantic ingress+egress — 각 후보 검증
        candidates = [validate_manuscript_candidate(c) for c in candidates]
        self._annotate_candidate_diversity(candidates)
        return candidates

    def _generate_single_candidate(
        self,
        ep_num: int,
        strategy: str,
        blueprint: dict,
        common_context: str,
        hud_report: str = "",
        master_bible: dict = None,
        genre_name: str = "무협",
        cache_name: str = None,
        strategy_feedback: str = "",
        motivations: list = None,
        promises: list = None,
        strategy_temperature: float | None = None,
    ) -> dict | None:
        """
        [V60.81] 단일 후보 생성 + Self-Critique + Leakage 방지
        [V61.7] 컨텍스트 캐싱 지원 - 토큰 비용 50-67% 절감

        Args:
            ep_num: 에피소드 번호
            strategy: 전략 이름 (balanced/narrative/tension)
            common_context: 공통 컨텍스트
            hud_report: HUD 상태 (Self-Critique용)
            master_bible: 마스터 바이블 (NPC 정보 추출용)
            genre_name: 장르명
            cache_name: [V61.7] 캐시 이름 (있으면 캐시 사용, 없으면 기존 방식)
        """
        # [V61.3] 전체 메서드를 try-except로 감싸서 worker thread 크래시 방지
        try:
            strategy_config = self.ENSEMBLE_STRATEGIES.get(strategy, self.ENSEMBLE_STRATEGIES["balanced"])
            _temperature = (
                float(strategy_temperature)
                if isinstance(strategy_temperature, (int, float))
                else float(strategy_config["temperature"])
            )
            _strategy_feedback_block = (
                f"\n[Strategy-Specific Feedback]\n{strategy_feedback}\n" if strategy_feedback else ""
            )

            # [TF-45] 장르별 state_updates 스키마 주입
            _genre_code = normalize_chief_writer_genre_code(genre_name)
            _critical_keys = self._get_critical_keys_for_genre()
            _su_schema = build_state_updates_schema(_genre_code, _critical_keys)
            _output_block = self.PROMPT_TEMPLATE_OUTPUT.format(
                strategy=strategy,
                state_updates_schema=_su_schema,
            )

            # [V61.7] 캐시 사용 분기
            if cache_name:
                # 캐시 활성: common_context는 캐시에 있으므로 전략 부분만 전송
                strategy_prompt = f"""{strategy_config["instruction"]}
{_strategy_feedback_block}
{_output_block}"""

                # 폴백용 전체 프롬프트 (캐시 실패 시)
                full_prompt = f"""{common_context}
{_strategy_feedback_block}
{strategy_config["instruction"]}

{_output_block}"""

                response = self._ask_with_cached_context(
                    cache_name=cache_name,
                    prompt=strategy_prompt,
                    temperature=_temperature,
                    thinking_level="medium",
                    full_prompt_fallback=full_prompt,
                )
            else:
                # [V60.82] 기존 방식: 전체 프롬프트
                full_prompt = f"""{common_context}
{_strategy_feedback_block}
{strategy_config["instruction"]}

{_output_block}"""

                response = self.ask(
                    prompt=full_prompt,
                    temperature=_temperature,
                    thinking_level="medium",  # [V61.6] 원고 생성 추론 강화
                )

            # [V60.81] Leakage 방지 적용
            response = self.quality_gate.sanitize_leakage(response)

            data = self._extract_json_robust(response)

            if not isinstance(data, dict) or not data or data.get("parsing_error"):
                return None

            # 원고 추출 (타입 안전성 보장)
            manuscript_content = data.get("content", "")
            if not isinstance(manuscript_content, str):
                # content가 리스트/딕셔너리인 경우 문자열로 변환 시도
                if isinstance(manuscript_content, list):
                    manuscript_content = "\n".join(str(item) for item in manuscript_content)
                elif isinstance(manuscript_content, dict):
                    manuscript_content = (
                        manuscript_content.get("text", "")
                        or manuscript_content.get("content", "")
                        or json.dumps(manuscript_content, ensure_ascii=False)
                    )
                else:
                    manuscript_content = str(manuscript_content) if manuscript_content else ""
            manuscript_json = json.dumps(data, ensure_ascii=False)

            # [V60.81] Self-Critique 적용 (NPC 정보 필요)
            npcs = []
            if master_bible:
                bible_root = master_bible.get("MasterBible", master_bible) if isinstance(master_bible, dict) else {}
                assets = bible_root.get("AssetLibrary", {})
                npcs = assets.get("KeyNPCs", []) or assets.get("Key_NPCs", [])

            critiqued_manuscript = self.quality_gate.apply_self_critique(
                manuscript=manuscript_json,
                hud_report=hud_report,
                npcs=npcs,
                genre_name=genre_name,
                ep_num=ep_num,
                motivations=motivations,
                promises=promises,  # [B-4]
                blueprint=blueprint,
            )

            # Self-Critique 결과에서 content 재추출
            try:
                critiqued_data = json.loads(critiqued_manuscript)
                _crit_content = critiqued_data.get("content")
                # [TypeSafety] content가 dict/list일 수 있음 → 문자열 변환
                if isinstance(_crit_content, list):
                    _crit_content = "\n".join(str(item) for item in _crit_content)
                elif isinstance(_crit_content, dict):
                    _crit_content = (
                        _crit_content.get("text", "")
                        or _crit_content.get("content", "")
                        or json.dumps(_crit_content, ensure_ascii=False)
                    )
                final_content = _crit_content or manuscript_content
                final_title = critiqued_data.get("title", data.get("title", f"제{ep_num}화"))
                final_state = critiqued_data.get("state_updates", data.get("state_updates", {}))
            except (json.JSONDecodeError, ValueError, TypeError):  # [V64.P4] IMPORTANT: critique parse, safe default
                final_content = manuscript_content
                final_title = data.get("title", f"제{ep_num}화")
                final_state = data.get("state_updates", {})

            # patch_state_updates JSON이 원고 끝에 누출된 경우 제거
            final_content = re.sub(
                r'\s*\{"patch_state_updates"\s*:.*?\}\s*$', "", final_content, flags=re.DOTALL
            ).rstrip()

            return {
                "strategy": strategy,
                "strategy_name": strategy_config["name"],
                "manuscript": final_content,
                "title": final_title,
                "state_updates": final_state,
                "key_scenes_covered": data.get("key_scenes_covered", []),
                "metadata": {
                    "temperature": _temperature,
                    "emphasis": strategy_config["emphasis"],
                    "length": len(final_content),
                    "self_critique_applied": True,
                },
            }

        except Exception as e:
            # [V61.3] stderr로 출력 (Rich 스피너가 stdout 가림)
            import traceback

            logging.error(f" [V61.3] ChiefWriter _generate_single_candidate 크래시: {str(e)[:80]}")
            logging.error(traceback.format_exc())
            return None

    def _build_common_context(self, *args, **kwargs):
        return self.context_builder.build_common_context(*args, **kwargs)

    # ── [V62.6] 에피소드 상태 다이제스트 ──────────────────────────

    def _generate_episode_digest(self, *args, **kwargs):
        return self.context_builder._generate_episode_digest(*args, **kwargs)

    def _detect_deaths_from_manuscript(self, *args, **kwargs):
        return self.context_builder._detect_deaths_from_manuscript(*args, **kwargs)

    def _detect_past_events_from_manuscript(self, *args, **kwargs):
        return self.context_builder._detect_past_events_from_manuscript(*args, **kwargs)

    def _build_past_guard_section(self, *args, **kwargs):
        return self.context_builder._build_past_guard_section(*args, **kwargs)

    def _build_future_guard_section(self, *args, **kwargs):
        return self.context_builder._build_future_guard_section(*args, **kwargs)

    def regenerate_with_feedback(
        self,
        ep_num: int,
        blueprint: dict,
        prev_manuscript: str,
        hud_report: str,
        arc_doc: str,
        master_bible: dict,
        style_guide: str,
        director_feedback: str,
        previous_attempt: dict,
        attempt_number: int,
        reference_excerpt: str = "",
        # [V60.80 FIX] 미래 침범 방지용 추가 파라미터
        current_inventory: list[str] = None,
        current_martial_arts: list[str] = None,
        dead_npcs: list[str] = None,
        item_acquisition_timeline: str = "",
        # [V60.80+] 기존 Writer 핵심 기능
        reference_anchor_prompt: str = "",
        mandatory_context: str = "",
        anti_trope_prompt: str = "",
        justification_prompt: str = "",
        reflexion_prompt: str = "",
        genre_name: str = "무협",
        # [V60.81] 추가 파라미터
        npc_equipment_summary: str = "",
        intro_dna: str = "",  # [QI-1-C3] CYNICAL 하드코딩 제거
        # [V60.85] 장르 Guard Purism Prompt
        purism_prompt: str = "",
        # [V60.95] 고밀도 HUD 전달
        state_tracker=None,
        # [V67] 이전 원고 전문 — 모순 방지용 컨텍스트
        prev_manuscripts_text: str = "",
        # [V68] 세계 상태 요약 — 장기연재 모순 방지
        world_state_summary: str = "",
        # [V68] 에피소드 연결고리 — 직전 화에서 이어받아야 할 것
        chain_link_section: str = "",
        # [emotional_beat] 감정 정점
        emotional_beat_section: str = "",
        # [B-4] 주인공 동기/약속
        motivations: list = None,
        promises: list = None,
        # [TF-49b] Arc 계획 아이템 사전 정당화
        upcoming_arc_items: list[str] = None,
        strategy_budget: str = "full",
        preferred_strategy: str = "",
    ) -> list[dict]:
        """
        Director 피드백 반영 재생성

        Args:
            ... (기존 파라미터)
            director_feedback: Director의 구체적 피드백
            previous_attempt: 이전 시도 결과
            attempt_number: 현재 시도 번호 (2 또는 3)
            current_inventory: 현재 소지품 목록
            current_martial_arts: 현재 무공 목록
            dead_npcs: 죽은 NPC 목록
            item_acquisition_timeline: 아이템 획득 타임라인
            purism_prompt: 장르 Guard의 순혈주의 지침 (V60.85)
            prev_manuscripts_text: [V67] 이전 30화 원고 전문 (모순 방지용)
            world_state_summary: [V68] 세계 상태 요약 (장기연재 모순 방지)
            chain_link_section: [V68] 직전 화 연결고리 (다음 화에서 이어받을 것)

        Returns:
            List[Dict]: 새로운 3개 후보
        """
        _history_feedback = self._build_retry_history_feedback(previous_attempt)

        # 피드백 강화
        enhanced_feedback = f"""
[🚨 {attempt_number}차 재시도 - Director 피드백 필수 반영]

{director_feedback}

[이전 시도 분석]
- 선택된 전략: {previous_attempt.get("strategy", "unknown")}
- 문제점: {previous_attempt.get("rejection_reason", "unknown")}

⚠️ 위 피드백을 100% 반영하지 않으면 다시 REJECT됩니다.
"""

        _sb = previous_attempt.get("score_breakdown", {})
        if isinstance(_sb, dict) and _sb:
            _sb_lines = [f"  - {k}: {v}" for k, v in _sb.items() if isinstance(v, int | float)]
            if _sb_lines:
                enhanced_feedback += "\n[세부 채점]\n" + "\n".join(_sb_lines)

        _vw = previous_attempt.get("validation_warnings", [])
        if isinstance(_vw, list) and _vw:
            enhanced_feedback += "\n[Python 검증 경고]\n" + "\n".join(f"- {w}" for w in _vw[:10])

        _fsr = previous_attempt.get("fix_scope_reasoning", "")
        if _fsr:
            enhanced_feedback += f"\n[수정 범위 근거]\n{_fsr}"

        # [A-2] Director 서사 관찰 명시 전달
        _open_review = previous_attempt.get("open_review", "")
        if _open_review and _open_review not in ("특이사항 없음", "없음", ""):
            enhanced_feedback += f"\n\n[Director 서사 관찰 — 반드시 개선할 것]\n{_open_review}"
        if _history_feedback:
            enhanced_feedback += f"\n\n{_history_feedback}"

        # 실패 학습 제약 구성
        failure_constraints = ""
        if previous_attempt.get("action_items"):
            items = previous_attempt.get("action_items", [])
            failure_constraints = "이전 REJECT 사유:\n" + "\n".join([f"- {item}" for item in items])
        _rejected_strategy = str(previous_attempt.get("selected_strategy_key", "") or "")
        _strategy_feedback = previous_attempt.get("selection_reason", "")
        if isinstance(_strategy_feedback, dict):
            _strategy_feedback = json.dumps(_strategy_feedback, ensure_ascii=False)
        if not isinstance(_strategy_feedback, str):
            _strategy_feedback = str(_strategy_feedback or "")

        return self.generate_ensemble(
            ep_num=ep_num,
            blueprint=blueprint,
            prev_manuscript=prev_manuscript,
            hud_report=hud_report,
            arc_doc=arc_doc,
            master_bible=master_bible,
            style_guide=style_guide,
            reference_excerpt=reference_excerpt,
            director_feedback=enhanced_feedback,
            strategy_specific_feedback=_strategy_feedback,
            rejected_strategy=_rejected_strategy,
            failure_constraints=failure_constraints,
            # 미래 침범 방지 데이터 전달
            current_inventory=current_inventory,
            current_martial_arts=current_martial_arts,
            dead_npcs=dead_npcs,
            item_acquisition_timeline=item_acquisition_timeline,
            # 기존 Writer 핵심 기능
            reference_anchor_prompt=reference_anchor_prompt,
            mandatory_context=mandatory_context,
            anti_trope_prompt=anti_trope_prompt,
            justification_prompt=justification_prompt,
            reflexion_prompt=reflexion_prompt,
            genre_name=genre_name,
            # [V60.81] 추가 파라미터
            npc_equipment_summary=npc_equipment_summary,
            intro_dna=intro_dna,
            # [V60.85] 장르 Guard Purism Prompt
            purism_prompt=purism_prompt,
            # [V60.95] 고밀도 HUD 전달
            state_tracker=state_tracker,
            # [V67] 이전 원고 전문
            prev_manuscripts_text=prev_manuscripts_text,
            # [V68] 세계 상태 요약
            world_state_summary=world_state_summary,
            # [V68] 에피소드 연결고리
            chain_link_section=chain_link_section,
            emotional_beat_section=emotional_beat_section,
            motivations=motivations,  # [B-4]
            promises=promises,  # [B-4]
            upcoming_arc_items=upcoming_arc_items,  # [TF-49b]
            strategy_budget=strategy_budget,
            preferred_strategy=preferred_strategy,
        )

    # =========================================================================
    # [TF-23] InPlace — LLM 1회 호출로 원고 국소 수정
    # =========================================================================

    _STRUCTURAL_PATCH_LOCAL_HINTS = {
        "opening": ("도입", "초반", "오프닝", "첫 장면", "시작"),
        "ending": ("엔딩", "결말", "마지막", "마무리", "후반", "후반부", "클라이맥스", "ending", "final"),
        "dialogue": ("대화", "대사", "말투", "dialogue"),
        "confrontation": ("전투", "대결", "결전", "충돌", "액션", "confrontation"),
        "revelation": ("반전", "정체", "드러", "밝혀", "revelation"),
    }
    _STRUCTURAL_PATCH_GLOBAL_HINTS = (
        "전반",
        "전체",
        "전체적",
        "전면",
        "전체적으로",
        "구조",
        "플롯",
        "문체",
        "톤",
        "호흡",
        "페이싱",
        "리듬",
        "pacing",
        "tone",
        "style",
    )

    def _set_last_inplace_patch_trace(
        self,
        *,
        patch_strategy: str = "",
        patch_targets: list[str] | None = None,
        fallback_reason: str = "",
        focus: str = "",
        structural_attempted: bool = False,
    ) -> dict:
        trace = {
            "patch_strategy": str(patch_strategy or ""),
            "patch_targets": list(patch_targets or []),
            "fallback_reason": str(fallback_reason or ""),
            "focus": str(focus or ""),
            "structural_attempted": bool(structural_attempted),
        }
        self._last_inplace_patch_trace = trace
        return trace

    @staticmethod
    def _normalize_fix_pack(fix_pack: dict | None) -> dict:
        payload = fix_pack if isinstance(fix_pack, dict) else {}

        def _normalize_list(raw: object, *, limit: int, item_limit: int) -> list[str]:
            if isinstance(raw, str):
                items = [raw]
            elif isinstance(raw, list):
                items = raw
            else:
                return []
            cleaned: list[str] = []
            seen: set[str] = set()
            for item in items:
                text = " ".join(str(item or "").split()).strip()
                if not text:
                    continue
                text = text[:item_limit]
                if text in seen:
                    continue
                seen.add(text)
                cleaned.append(text)
                if len(cleaned) >= limit:
                    break
            return cleaned

        patch_targets = _normalize_list(payload.get("patch_targets"), limit=6, item_limit=80)
        must_fix = _normalize_list(payload.get("must_fix"), limit=6, item_limit=180)
        do_not_regress = _normalize_list(payload.get("do_not_regress"), limit=6, item_limit=180)
        success_condition = " ".join(str(payload.get("success_condition", "") or "").split()).strip()[:220]
        target_kind = " ".join(str(payload.get("target_kind", "") or "").split()).strip()[:80]
        evidence_summary = " ".join(str(payload.get("evidence_summary", "") or "").split()).strip()[:220]

        normalized = {
            "patch_targets": patch_targets,
            "must_fix": must_fix,
            "do_not_regress": do_not_regress,
            "success_condition": success_condition,
            "target_kind": target_kind,
        }
        if evidence_summary:
            normalized["evidence_summary"] = evidence_summary

        has_payload = any(
            normalized.get(key)
            for key in ("patch_targets", "must_fix", "do_not_regress", "success_condition", "target_kind", "evidence_summary")
        )
        return normalized if has_payload else {}

    def _build_fix_pack_guidance(self, fix_pack: dict | None) -> str:
        normalized = self._normalize_fix_pack(fix_pack)
        if not normalized:
            return ""

        lines = ["[Fix Pack Local Repair Contract]"]
        if normalized.get("target_kind"):
            lines.append(f"- target_kind: {normalized['target_kind']}")
        patch_targets = normalized.get("patch_targets") or []
        if patch_targets:
            lines.append("- patch_targets: " + ", ".join(patch_targets[:6]))
        must_fix = normalized.get("must_fix") or []
        if must_fix:
            lines.append("- must_fix:")
            lines.extend(f"  - {item}" for item in must_fix[:5])
        do_not_regress = normalized.get("do_not_regress") or []
        if do_not_regress:
            lines.append("- do_not_regress:")
            lines.extend(f"  - {item}" for item in do_not_regress[:5])
        success_condition = str(normalized.get("success_condition", "") or "").strip()
        if success_condition:
            lines.append(f"- success_condition: {success_condition}")
        evidence_summary = str(normalized.get("evidence_summary", "") or "").strip()
        if evidence_summary:
            lines.append(f"- evidence_summary: {evidence_summary}")
        lines.append("- Keep the selected manuscript intact outside the listed anchors.")
        return "\n".join(lines)

    def _classify_structural_patch_focus(self, director_feedback: str) -> str:
        feedback = str(director_feedback or "")
        if not feedback:
            return ""
        for focus, keywords in self._STRUCTURAL_PATCH_LOCAL_HINTS.items():
            if any(keyword in feedback for keyword in keywords):
                return focus
        if any(keyword in feedback for keyword in self._STRUCTURAL_PATCH_GLOBAL_HINTS):
            return "global"
        return ""

    def _split_manuscript_into_structural_blocks(
        self,
        original_manuscript: str,
        *,
        expected_blocks: int,
    ) -> tuple[list[str], str]:
        from modules.core.stage4_context_builder import Stage4ContextBuilder

        manuscript = str(original_manuscript or "").strip()
        if not manuscript:
            return [], "\n\n"

        explicit_blocks = Stage4ContextBuilder._split_scenes(manuscript)
        has_explicit_boundary = bool(re.search(r"\n(?:#{1,3}\s+\S+|---+|\*\*\*+|\n{3,})", manuscript))
        if has_explicit_boundary and len(explicit_blocks) >= 2:
            if not expected_blocks or abs(len(explicit_blocks) - expected_blocks) <= 1:
                separator = "\n\n---\n\n" if ("---" in manuscript or "***" in manuscript) else "\n\n\n"
                return explicit_blocks, separator

        paragraphs = [paragraph.strip() for paragraph in re.split(r"\n{2,}", manuscript) if paragraph.strip()]
        if len(paragraphs) < 2:
            return [], "\n\n"

        target_blocks = expected_blocks if expected_blocks >= 2 else min(max(len(paragraphs) // 3, 2), 6)
        target_blocks = max(2, min(target_blocks, len(paragraphs)))
        base_size, extra = divmod(len(paragraphs), target_blocks)
        blocks: list[str] = []
        cursor = 0
        for block_idx in range(target_blocks):
            chunk_size = base_size + (1 if block_idx < extra else 0)
            chunk = paragraphs[cursor : cursor + chunk_size]
            cursor += chunk_size
            if chunk:
                blocks.append("\n\n".join(chunk))
        return blocks, "\n\n"

    def _select_structural_patch_targets(self, *, focus: str, slots: list, block_count: int) -> list[int]:
        if not slots or block_count <= 1:
            return []

        usable_count = min(len(slots), block_count)
        last_idx = usable_count - 1
        middle_idx = min(max(1, usable_count // 2), last_idx)

        if focus == "opening":
            return [0]
        if focus == "ending":
            return sorted({max(0, last_idx - 1), last_idx}) if usable_count >= 4 else [last_idx]
        if focus == "dialogue":
            return [middle_idx]
        if focus == "confrontation":
            for idx, slot in enumerate(slots[:usable_count]):
                if getattr(getattr(slot, "scene_type", None), "value", "") == "confrontation":
                    return [idx]
            return [middle_idx]
        if focus == "revelation":
            for idx, slot in enumerate(slots[:usable_count]):
                if getattr(getattr(slot, "scene_type", None), "value", "") in {"revelation", "resolution"}:
                    return [idx]
            return [max(0, last_idx - 1)]
        return []

    def _build_structural_patch_plan(
        self,
        *,
        original_manuscript: str,
        director_feedback: str,
        blueprint: dict | None,
        genre_name: str = "",
    ) -> dict:
        from modules.core.writer_template import create_writer_template

        if not isinstance(blueprint, dict):
            return {}

        scene_breakdown = blueprint.get("scene_breakdown", {})
        if not isinstance(scene_breakdown, dict) or len(scene_breakdown) < 2:
            return {}

        focus = self._classify_structural_patch_focus(director_feedback)
        if not focus or focus == "global":
            return {}

        blocks, separator = self._split_manuscript_into_structural_blocks(
            original_manuscript,
            expected_blocks=len(scene_breakdown),
        )
        if len(blocks) < 2:
            return {}

        genre_code = normalize_chief_writer_genre_code(genre_name)
        template = create_writer_template(genre=genre_code).generate_template(blueprint=blueprint)
        if not getattr(template, "slots", None):
            return {}

        slots = list(template.slots)[: len(blocks)]
        target_indexes = self._select_structural_patch_targets(
            focus=focus,
            slots=slots,
            block_count=len(blocks),
        )
        if not target_indexes:
            return {}

        target_scene_ids: list[str] = []
        target_payload_lines: list[str] = []
        boundary_lines: list[str] = []
        scene_plan_lines: list[str] = []
        target_index_map: dict[str, int] = {}

        for idx, slot in enumerate(slots):
            scene_plan_lines.append(
                f"- {slot.scene_id} | {slot.scene_type.value} | {str(slot.description or '')[:120]}"
            )

            if idx not in target_indexes:
                continue

            scene_id = slot.scene_id
            target_scene_ids.append(scene_id)
            target_index_map[scene_id] = idx
            target_payload_lines.append(
                "\n".join(
                    [
                        f"[{scene_id}]",
                        f"type={slot.scene_type.value}",
                        f"description={str(slot.description or '')[:160]}",
                        "required=" + ", ".join(str(item) for item in list(slot.required_elements or [])[:4]),
                        blocks[idx],
                    ]
                )
            )
            prev_excerpt = blocks[idx - 1][-220:] if idx > 0 else ""
            next_excerpt = blocks[idx + 1][:220] if idx + 1 < len(blocks) else ""
            boundary_lines.append(
                "\n".join(
                    [
                        f"[{scene_id} boundary]",
                        f"prev={prev_excerpt}" if prev_excerpt else "prev=",
                        f"next={next_excerpt}" if next_excerpt else "next=",
                    ]
                )
            )

        if not target_scene_ids:
            return {}

        return {
            "focus": focus,
            "blocks": blocks,
            "separator": separator,
            "target_scene_ids": target_scene_ids,
            "target_index_map": target_index_map,
            "scene_plan": "\n".join(scene_plan_lines),
            "boundary_context": "\n\n".join(boundary_lines),
            "target_scene_payload": "\n\n".join(target_payload_lines),
        }

    def _load_structural_patch_payload(self, response: str) -> dict:
        stripped = str(response or "").strip()
        if not stripped:
            return {}
        if stripped.startswith("```"):
            stripped = re.sub(r"^```(?:json)?\s*|\s*```$", "", stripped, flags=re.IGNORECASE | re.DOTALL).strip()
        try:
            parsed = json.loads(stripped)
        except (json.JSONDecodeError, TypeError, ValueError):
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _attempt_structural_inplace_patch(
        self,
        *,
        original_manuscript: str,
        director_feedback: str,
        attempt_number: int,
        style_guide: str = "",
        blueprint: dict | None = None,
        genre_name: str = "",
    ) -> list[dict] | None:
        from modules.core.prompt_loader import PromptLoader

        plan = self._build_structural_patch_plan(
            original_manuscript=original_manuscript,
            director_feedback=director_feedback,
            blueprint=blueprint,
            genre_name=genre_name,
        )
        if not plan:
            return None

        self._set_last_inplace_patch_trace(
            patch_strategy="inplace_patch_structural",
            patch_targets=list(plan["target_scene_ids"]),
            focus=str(plan["focus"] or ""),
            structural_attempted=True,
        )

        def _esc(text: str) -> str:
            return str(text or "").replace("{", "{{").replace("}", "}}")

        try:
            template = PromptLoader().load("chief_writer", "PATCH_MODE_STRUCTURAL_PROMPT")
        except Exception as exc:
            logging.warning("[PWF-STRUCT] PATCH_MODE_STRUCTURAL_PROMPT 로드 실패: %s", exc)
            template = None

        if template:
            prompt = template.format(
                focus_label=_esc(plan["focus"]),
                style_guide=_esc(style_guide or ""),
                feedback_text=_esc(director_feedback),
                scene_plan=_esc(plan["scene_plan"]),
                target_scene_ids=", ".join(plan["target_scene_ids"]),
                boundary_context=_esc(plan["boundary_context"]),
                target_scene_payload=_esc(plan["target_scene_payload"]),
            )
        else:
            prompt = (
                "[Structural InPlace Patch]\n\n"
                f"focus={plan['focus']}\n"
                f"target_scene_ids={', '.join(plan['target_scene_ids'])}\n\n"
                f"[StyleGuide]\n{style_guide}\n\n"
                f"[DirectorFeedback]\n{director_feedback}\n\n"
                f"[ScenePlan]\n{plan['scene_plan']}\n\n"
                f"[BoundaryContext]\n{plan['boundary_context']}\n\n"
                f"[TargetScenes]\n{plan['target_scene_payload']}\n\n"
                'Return JSON only: {"patched_blocks":{"scene_id":"patched text"}, "patch_state_updates": {...}}'
            )

        logging.info(
            "[PWF-STRUCT] scene-aware inplace patch attempt=%d focus=%s targets=%s",
            attempt_number,
            plan["focus"],
            plan["target_scene_ids"],
        )
        try:
            response = self.ask(prompt, temperature=0.2, thinking_level="medium")
        except Exception as exc:
            logging.warning("[PWF-STRUCT] scene-aware inplace 호출 실패: %s", exc)
            return None

        payload = self._load_structural_patch_payload(response)
        patched_blocks = payload.get("patched_blocks", {}) if isinstance(payload, dict) else {}
        if not isinstance(patched_blocks, dict):
            logging.info("[PWF-STRUCT] patched_blocks 누락 → whole-text fallback")
            self._set_last_inplace_patch_trace(
                patch_strategy="inplace_patch_structural",
                patch_targets=list(plan["target_scene_ids"]),
                fallback_reason="missing_patched_blocks",
                focus=str(plan["focus"] or ""),
                structural_attempted=True,
            )
            return None

        merged_blocks = list(plan["blocks"])
        patched_any = False
        for scene_id in plan["target_scene_ids"]:
            patch_text = str(patched_blocks.get(scene_id, "") or "").strip()
            if len(patch_text) < 80:
                continue
            block_idx = plan["target_index_map"].get(scene_id)
            if block_idx is None or block_idx >= len(merged_blocks):
                continue
            merged_blocks[block_idx] = patch_text
            patched_any = True

        if not patched_any:
            logging.info("[PWF-STRUCT] usable patched block 없음 → whole-text fallback")
            self._set_last_inplace_patch_trace(
                patch_strategy="inplace_patch_structural",
                patch_targets=list(plan["target_scene_ids"]),
                fallback_reason="no_usable_patched_blocks",
                focus=str(plan["focus"] or ""),
                structural_attempted=True,
            )
            return None

        merged_manuscript = str(plan["separator"] or "\n\n").join(merged_blocks).strip()
        if len(merged_manuscript) < 2000:
            logging.warning("[PWF-STRUCT] merged structural patch too short: %d", len(merged_manuscript))
            self._set_last_inplace_patch_trace(
                patch_strategy="inplace_patch_structural",
                patch_targets=list(plan["target_scene_ids"]),
                fallback_reason="patched_output_too_short",
                focus=str(plan["focus"] or ""),
                structural_attempted=True,
            )
            return None

        state_updates = payload.get("patch_state_updates", {})
        if not isinstance(state_updates, dict):
            state_updates = {}

        self._set_last_inplace_patch_trace(
            patch_strategy="inplace_patch_structural",
            patch_targets=list(plan["target_scene_ids"]),
            focus=str(plan["focus"] or ""),
            structural_attempted=True,
        )

        return [
            {
                "manuscript": merged_manuscript,
                "strategy": "inplace_patch_structural",
                "state_updates": state_updates,
                "patch_targets": list(plan["target_scene_ids"]),
            }
        ]

    def inplace_patch(
        self,
        *,
        original_manuscript: str,
        director_feedback: str,
        attempt_number: int,
        style_guide: str = "",  # [TF-37] 스타일 클로닝 갭 수정
        fix_pack: dict | None = None,
    ) -> list[dict]:
        """[TF-23] LLM 1회 호출로 원고 in-place 수정. 실패 시 빈 리스트 → patch/rewrite 폴백."""
        from modules.core.constants import smart_truncate
        from modules.core.prompt_loader import PromptLoader

        normalized_fix_pack = self._normalize_fix_pack(fix_pack)
        fix_pack_guidance = self._build_fix_pack_guidance(normalized_fix_pack)
        blueprint = getattr(self, "_inplace_patch_blueprint", None)
        genre_name = str(getattr(self, "_inplace_patch_genre_name", "") or "")
        focus = self._classify_structural_patch_focus(director_feedback)
        scene_breakdown = blueprint.get("scene_breakdown", {}) if isinstance(blueprint, dict) else {}
        structural_attempted = False
        fallback_reason = ""

        if normalized_fix_pack.get("patch_targets"):
            self._set_last_inplace_patch_trace(
                patch_strategy="inplace_patch",
                patch_targets=list(normalized_fix_pack.get("patch_targets") or []),
                fallback_reason="",
                focus="",
                structural_attempted=False,
            )
        elif not isinstance(blueprint, dict):
            fallback_reason = "missing_blueprint"
        elif not isinstance(scene_breakdown, dict) or len(scene_breakdown) < 2:
            fallback_reason = "missing_scene_breakdown"
        elif not focus:
            fallback_reason = "unclassified_feedback"
        elif focus == "global":
            fallback_reason = "global_issue"
        else:
            structural_attempted = True
            _structural_result = self._attempt_structural_inplace_patch(
                original_manuscript=original_manuscript,
                director_feedback=director_feedback,
                attempt_number=attempt_number,
                style_guide=style_guide,
                blueprint=blueprint,
                genre_name=genre_name,
            )
            if _structural_result:
                return _structural_result

            _existing_trace = dict(getattr(self, "_last_inplace_patch_trace", {}) or {})
            fallback_reason = str(_existing_trace.get("fallback_reason") or "structural_patch_unusable")
            focus = str(_existing_trace.get("focus") or focus)
            self._set_last_inplace_patch_trace(
                patch_strategy="inplace_patch",
                patch_targets=list(_existing_trace.get("patch_targets") or []),
                fallback_reason=fallback_reason,
                focus=focus,
                structural_attempted=True,
            )

        if not structural_attempted:
            self._set_last_inplace_patch_trace(
                patch_strategy="inplace_patch",
                patch_targets=[],
                fallback_reason=fallback_reason,
                focus=focus,
                structural_attempted=False,
            )

        try:
            _patch_template = PromptLoader().load("chief_writer", "PATCH_MODE_PROMPT")
        except Exception as e:
            logging.warning(f"[TF-23] PATCH_MODE_PROMPT 로드 실패: {e!s:.100}")
            _patch_template = None

        def _esc(s):
            return s.replace("{", "{{").replace("}", "}}")

        _style_text = _esc(style_guide) if style_guide else "기본 웹소설 문체"  # [TF-37]
        _feedback_text = director_feedback
        if fix_pack_guidance:
            _feedback_text = f"{director_feedback}\n\n{fix_pack_guidance}".strip()

        # [F-4] 트렁케이션 경고
        _orig_len = len(original_manuscript or "")
        if _orig_len > 150000:
            logging.warning("[TRUNCATION] chief_writer.inplace_patch: 원고 %d자 → 150000자 (%.1f%% 손실)",
                _orig_len,
                (1 - 150000 / _orig_len) * 100,
            )

        # [TF-IPG] 원본 글자수 명시 — LLM에게 구체적 목표치 제공
        _min_char_target = int(_orig_len * 0.9)  # ±10% 하한

        if _patch_template:
            prompt = _patch_template.format(
                feedback_text=_esc(_feedback_text),
                original_manuscript=_esc(smart_truncate(original_manuscript, max_chars=150000, head_chars=20000)),
                style_guide=_style_text,  # [TF-37]
                original_char_count=_orig_len,
                min_char_target=_min_char_target,
            )
        else:
            prompt = (
                "[원고 원본 보존 + 지적사항만 수정]\n\n"
                + (f"## 문체 가이드\n{style_guide}\n\n" if style_guide else "")
                + f"## Director 피드백\n{_feedback_text}\n\n"
                f"## 원본 원고\n{smart_truncate(original_manuscript, max_chars=150000, head_chars=20000)}\n\n"
                f"전면 재작성하지 마세요. 지적된 부분만 고치세요."
            )

        try:
            response = self.ask(prompt, temperature=0.3, thinking_level="medium")
            if not response or len(response) < 2000:
                logging.warning(f"[TF-23] InPlace 응답 길이 부족: {len(response or '')}자 < 2000자")
                return []
            # [TF-47] patch_state_updates + manuscript 추출
            # ask()가 response_mime_type="application/json"을 강제하므로
            # LLM이 {"content":"원고...", "patch_state_updates":{...}} 형태로 반환할 수 있음
            _state_updates = {}
            _manuscript = ""

            # 1단계: 전체 JSON 파싱 시도 (ask()가 JSON 강제하는 경우)
            _stripped = response.strip()
            if _stripped.startswith("{") and _stripped.endswith("}"):
                try:
                    _parsed = json.loads(_stripped)
                    if isinstance(_parsed, dict):
                        _state_updates = _parsed.get("patch_state_updates", {})
                        if not isinstance(_state_updates, dict):
                            _state_updates = {}
                        # 원고 텍스트 추출 (여러 키 이름 시도)
                        _manuscript = (
                            _parsed.get("corrected_manuscript")
                            or _parsed.get("patched_text")
                            or _parsed.get("revised_manuscript")
                            or _parsed.get("content")
                            or _parsed.get("text")
                            or _parsed.get("manuscript")
                            or _parsed.get("patched_manuscript")
                            or ""
                        )
                except (json.JSONDecodeError, ValueError):
                    pass  # JSON 파싱 실패 → 2단계로

            # 2단계: JSON 파싱 실패 또는 원고가 빈 경우 → 기존 마커 방식 폴백
            if not _manuscript:
                _su_marker = '"patch_state_updates"'
                _su_idx = response.rfind(_su_marker)
                if _su_idx >= 0:
                    # patch_state_updates 직전의 { 를 찾되, position 0이면 스킵 (전체 JSON wrapper)
                    _outer_start = response.rfind("{", 0, _su_idx)
                    if _outer_start > 0:
                        _tail = response[_outer_start:]
                        try:
                            _outer = json.loads(_tail)
                            _state_updates = _outer.get("patch_state_updates", {})
                            if not isinstance(_state_updates, dict):
                                _state_updates = {}
                            response = response[:_outer_start].rstrip()
                        except (json.JSONDecodeError, ValueError):
                            _su_match = re.search(r'\{"patch_state_updates"\s*:\s*(\{.*?\})\}', response, re.DOTALL)
                            if _su_match:
                                try:
                                    _state_updates = json.loads(_su_match.group(1))
                                except (json.JSONDecodeError, ValueError):
                                    pass
                                response = response[: _su_match.start()].rstrip()
                # [TF-36] LLM이 JSON으로 감싼 경우 텍스트 추출
                _manuscript = self._unwrap_manuscript_text(response)

            # [TF-IPG] [원고_끝] 마커 검증 — 마커가 있으면 제거, 없으면 잘림 경고
            _end_marker = "[원고_끝]"
            _marker_idx = _manuscript.rfind(_end_marker)
            if _marker_idx >= 0:
                _manuscript = _manuscript[:_marker_idx].rstrip()
            else:
                logging.warning("[TF-IPG] [원고_끝] 마커 없음 — 출력이 잘렸을 수 있음 (%d자)", len(_manuscript))

            # [TF-IPG GAP-1] 추출된 manuscript 자체의 길이 체크 (raw 응답이 아닌 추출본 기준)
            if not _manuscript or len(_manuscript) < 2000:
                logging.warning(
                    "[TF-IPG] 추출된 manuscript 길이 부족: %d자 < 2000자 (raw 응답 %d자)",
                    len(_manuscript or ""), len(response or ""),
                )
                return []
            _existing_trace = dict(getattr(self, "_last_inplace_patch_trace", {}) or {})
            _trace_focus = "" if normalized_fix_pack.get("patch_targets") else str(_existing_trace.get("focus") or focus)
            self._set_last_inplace_patch_trace(
                patch_strategy="inplace_patch",
                patch_targets=list(_existing_trace.get("patch_targets") or normalized_fix_pack.get("patch_targets") or []),
                fallback_reason=str(_existing_trace.get("fallback_reason") or fallback_reason),
                focus=_trace_focus,
                structural_attempted=bool(_existing_trace.get("structural_attempted") or structural_attempted),
            )
            logging.info(f"✅ [TF-23] 원고 in-place 수정 완료 ({len(_manuscript)}자)")
            result = {
                "manuscript": _manuscript,
                "strategy": "inplace_patch",
                "state_updates": _state_updates,
            }
            patch_targets = list(_existing_trace.get("patch_targets") or normalized_fix_pack.get("patch_targets") or [])
            if patch_targets:
                result["patch_targets"] = patch_targets
            return [result]
        except Exception as e:
            logging.warning(f"[TF-23] 원고 in-place 패치 실패: {e!s:.200}")
            return []

    def _unwrap_manuscript_text(self, text: str) -> str:
        """[TF-36] LLM 응답이 JSON 배열/객체로 감싸진 경우 순수 텍스트 추출."""
        if not text:
            return text
        stripped = text.strip()
        # JSON 배열 ["text"] 또는 객체 {"content": "text"} 감지
        if (stripped.startswith("[") and stripped.endswith("]")) or (
            stripped.startswith("{") and stripped.endswith("}")
        ):
            try:
                parsed = json.loads(stripped)
                if isinstance(parsed, list):
                    # ["text1", "text2"] → join
                    return "\n\n".join(str(item) for item in parsed)
                elif isinstance(parsed, dict):
                    return (
                        parsed.get("corrected_manuscript")
                        or parsed.get("patched_text")
                        or parsed.get("revised_manuscript")
                        or parsed.get("content")
                        or parsed.get("text")
                        or parsed.get("manuscript")
                        or parsed.get("patched_manuscript")
                        or text
                    )
            except (json.JSONDecodeError, ValueError):
                pass
        return text

    # =========================================================================
    # [Phase 3-5B] 패치 모드 — 원본 보존 + 피드백 지적사항만 수정
    # =========================================================================

    def patch_with_feedback(
        self,
        ep_num: int,
        blueprint: dict,
        prev_manuscript: str,
        hud_report: str,
        arc_doc: str,
        master_bible: dict,
        style_guide: str,
        original_manuscript: str,
        director_feedback: str,
        previous_attempt: dict,
        attempt_number: int,
        reference_excerpt: str = "",
        # 이하 generate_ensemble과 동일
        current_inventory: list[str] = None,
        current_martial_arts: list[str] = None,
        dead_npcs: list[str] = None,
        item_acquisition_timeline: str = "",
        reference_anchor_prompt: str = "",
        mandatory_context: str = "",
        anti_trope_prompt: str = "",
        justification_prompt: str = "",
        reflexion_prompt: str = "",
        genre_name: str = "무협",
        npc_equipment_summary: str = "",
        intro_dna: str = "",  # [QI-1-C3] CYNICAL 하드코딩 제거
        purism_prompt: str = "",
        state_tracker=None,
        prev_manuscripts_text: str = "",
        world_state_summary: str = "",
        chain_link_section: str = "",
        emotional_beat_section: str = "",
        # [B-4] 주인공 동기/약속
        motivations: list = None,
        promises: list = None,
        # [TF-49b] Arc 계획 아이템 사전 정당화
        upcoming_arc_items: list[str] = None,
    ) -> list[dict]:
        """[Phase 3-5B] 원본 원고를 보존하며 피드백 지적사항만 수정.

        패치 전용 프롬프트(PATCH_MODE_PROMPT)를 로드하여 원본 원고 + Director
        피드백을 director_feedback 섹션으로 포맷한 뒤, generate_ensemble()을
        호출한다.

        현재 runtime 의미는 broad 3-strategy ensemble이 아니라, 보통
        `single_strategy=<previous selected strategy>`를 준 bounded regenerate
        경로다. 즉 REJECT retry의 patch lane은 "선택된 전략 1개 대상 원문참조
        재생성"에 가깝다.

        실패 시 빈 리스트 반환 → 호출측에서 full rewrite 폴백.
        """
        try:
            from modules.core.prompt_loader import PromptLoader

            _patch_template = PromptLoader().load("chief_writer", "PATCH_MODE_PROMPT")
        except Exception as e:
            logging.warning(f"[SilentPass:ChiefWriter] PATCH_MODE_PROMPT 로드 실패: {e!s:.100}")
            _patch_template = None

        # 패치 프롬프트 포맷
        # [F-4] 트렁케이션 경고
        _orig_len = len(original_manuscript or "")
        if _orig_len > 150000:
            logging.warning("[TRUNCATION] chief_writer._patch_for_fix_loop: 원고 %d자 → 150000자 (%.1f%% 손실)",
                _orig_len,
                (1 - 150000 / _orig_len) * 100,
            )

        if _patch_template:
            # [Sweep55] .format()에 {}가 있으면 KeyError/ValueError 크래시 방지
            def _esc(s):
                return s.replace("{", "{{").replace("}", "}}")

            _min_char_target = int(_orig_len * 0.9)
            _patch_section = _patch_template.format(
                feedback_text=_esc(director_feedback),
                original_manuscript=_esc(smart_truncate(original_manuscript, max_chars=150000, head_chars=20000)),
                style_guide=_esc(style_guide or ""),
                original_char_count=_orig_len,
                min_char_target=_min_char_target,
            )
        else:
            # YAML 로드 실패 시 인라인 폴백
            _patch_section = (
                f"[패치 모드: 원본 보존 + 지적사항만 수정]\n\n"
                f"## Director 피드백\n{director_feedback}\n\n"
                f"## 원본 원고\n{smart_truncate(original_manuscript, max_chars=150000, head_chars=20000)}\n\n"
                f"전면 재작성하지 마세요. 지적된 부분만 고치세요."
            )

        enhanced_feedback = f"""
[🔧 {attempt_number}차 수정 - 패치 모드: 원본 보존 + 지적사항만 수정]

{_patch_section}

⚠️ 원본 원고의 전체 구조, 문체, 장점을 보존하면서 피드백 지적사항만 수정하세요.
⚠️ 수정하지 않는 부분은 원문을 그대로 유지하세요.
"""
        _history_feedback = self._build_retry_history_feedback(previous_attempt)
        if _history_feedback:
            enhanced_feedback += f"\n{_history_feedback}"
        _fix_pack_guidance = self._build_fix_pack_guidance(previous_attempt.get("fix_pack"))
        if _fix_pack_guidance:
            enhanced_feedback += f"\n\n{_fix_pack_guidance}"

        failure_constraints = ""
        if previous_attempt.get("action_items"):
            items = previous_attempt.get("action_items", [])
            failure_constraints = "이전 REJECT 사유:\n" + "\n".join([f"- {item}" for item in items])
        _fsr = previous_attempt.get("fix_scope_reasoning", "")
        if _fsr:
            failure_constraints += f"\n[수정 범위 근거]\n{_fsr}"
        _rejected_strategy = str(previous_attempt.get("selected_strategy_key", "") or "")
        _strategy_feedback = previous_attempt.get("selection_reason", "")
        if isinstance(_strategy_feedback, dict):
            _strategy_feedback = json.dumps(_strategy_feedback, ensure_ascii=False)
        if not isinstance(_strategy_feedback, str):
            _strategy_feedback = str(_strategy_feedback or "")

        try:
            return self.generate_ensemble(
                ep_num=ep_num,
                blueprint=blueprint,
                prev_manuscript=prev_manuscript,
                hud_report=hud_report,
                arc_doc=arc_doc,
                master_bible=master_bible,
                style_guide=style_guide,
                reference_excerpt=reference_excerpt,
                director_feedback=enhanced_feedback,
                strategy_specific_feedback=_strategy_feedback,
                rejected_strategy=_rejected_strategy,
                single_strategy=_rejected_strategy,
                failure_constraints=failure_constraints,
                current_inventory=current_inventory,
                current_martial_arts=current_martial_arts,
                dead_npcs=dead_npcs,
                item_acquisition_timeline=item_acquisition_timeline,
                reference_anchor_prompt=reference_anchor_prompt,
                mandatory_context=mandatory_context,
                anti_trope_prompt=anti_trope_prompt,
                justification_prompt=justification_prompt,
                reflexion_prompt=reflexion_prompt,
                genre_name=genre_name,
                npc_equipment_summary=npc_equipment_summary,
                intro_dna=intro_dna,
                purism_prompt=purism_prompt,
                state_tracker=state_tracker,
                prev_manuscripts_text=prev_manuscripts_text,
                world_state_summary=world_state_summary,
                chain_link_section=chain_link_section,
                emotional_beat_section=emotional_beat_section,
                motivations=motivations,
                promises=promises,
                upcoming_arc_items=upcoming_arc_items,  # [TF-49b]
            )
        except Exception as e:
            logging.warning(f"[Phase 3-5B] patch_with_feedback 실패, 빈 리스트 반환: {e}")
            return []

    @staticmethod
    def _build_retry_history_feedback(previous_attempt: dict | None) -> str:
        """누적된 REJECT 히스토리를 CW 재시도 프롬프트용 요약으로 변환."""
        if not isinstance(previous_attempt, dict):
            return ""

        history = previous_attempt.get("prior_attempts") or previous_attempt.get("history") or []
        if not isinstance(history, list) or not history:
            return ""

        recent = [item for item in history[-3:] if isinstance(item, dict)]
        if not recent:
            return ""

        lines = ["[누적 실패 히스토리 — 반복 금지]"]
        bucket_counts: dict[str, int] = {}
        category_counts: dict[str, int] = {}
        contradiction_hits: dict[str, int] = {}
        for idx, item in enumerate(recent, start=1):
            bucket = str(item.get("reject_bucket", "") or "").strip()
            category = str(item.get("error_category", "") or "").strip()
            reason = str(item.get("rejection_reason", "") or "").strip()
            score = item.get("score", "")
            action_items = [str(action).strip() for action in (item.get("action_items") or []) if str(action).strip()]
            contradictions = [
                str(name).strip() for name in (item.get("contradiction_types") or []) if str(name).strip()
            ]

            if bucket:
                bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
            if category:
                category_counts[category] = category_counts.get(category, 0) + 1
            for contradiction in contradictions:
                contradiction_hits[contradiction] = contradiction_hits.get(contradiction, 0) + 1

            summary_parts = []
            if bucket:
                summary_parts.append(bucket)
            if category:
                summary_parts.append(category)
            if action_items:
                summary_parts.append(f"action={' / '.join(action_items[:2])}")
            elif reason:
                summary_parts.append(reason[:120])
            contradiction_details = item.get("contradiction_details") or []
            detail_lines: list[str] = []
            for detail in contradiction_details[:2] if isinstance(contradiction_details, list) else []:
                if isinstance(detail, dict):
                    kind = str(detail.get("type", "") or "모순").strip()
                    body = (
                        str(detail.get("current_violation", "") or "").strip()
                        or str(detail.get("description", "") or "").strip()
                    )
                    text = f"{kind}: {body[:60]}".strip()
                else:
                    text = str(detail or "").strip()[:60]
                if text:
                    detail_lines.append(text)
            if detail_lines:
                summary_parts.append(f"detail={' / '.join(detail_lines)}")
            if score not in ("", None):
                summary_parts.append(f"score={score}")
            lines.append(f"- 시도 {idx}: " + " | ".join(summary_parts[:4]))

        repeated = []
        repeated.extend([name for name, count in bucket_counts.items() if count >= 2])
        repeated.extend([name for name, count in category_counts.items() if count >= 2])
        repeated.extend([name for name, count in contradiction_hits.items() if count >= 2])
        if repeated:
            lines.append("공통 실패 패턴: " + ", ".join(dict.fromkeys(repeated)))
        lines.append("위 패턴을 다시 반복하지 말고, 이번 시도에서는 근본 원인부터 제거하세요.")
        return "\n".join(lines)

    # =========================================================================
    # [V60.81] Writer 핵심 기능 통합 - Self-Critique & Quality Assurance
    # =========================================================================

    def _sanitize_leakage(self, *args, **kwargs):
        return self.quality_gate.sanitize_leakage(*args, **kwargs)

    def _apply_self_critique(self, *args, **kwargs):
        return self.quality_gate.apply_self_critique(*args, **kwargs)

    def _self_critique(self, *args, **kwargs):
        return self.quality_gate._self_critique(*args, **kwargs)

    def _check_hud_consistency(self, *args, **kwargs):
        return self.quality_gate._check_hud_consistency(*args, **kwargs)

    def _check_cliche_overuse(self, *args, **kwargs):
        return self.quality_gate._check_cliche_overuse(*args, **kwargs)

    def _check_justification_gaps(self, *args, **kwargs):
        return self.quality_gate._check_justification_gaps(*args, **kwargs)

    def _check_npc_relationship(self, *args, **kwargs):
        return self.quality_gate._check_npc_relationship(*args, **kwargs)

    def _fix_manuscript_issues(self, *args, **kwargs):
        return self.quality_gate._fix_manuscript_issues(*args, **kwargs)

    def _evaluate_with_rubric(self, *args, **kwargs):
        return self.quality_gate._evaluate_with_rubric(*args, **kwargs)

    # =========================================================================
    # [V60.82] DB 배치 캐시 - 중복 쿼리 제거
    # =========================================================================

    def _prefetch_manuscripts(self, ep_num: int, window: int = 10) -> None:
        """
        [V60.82] 최근 N화 원고를 한 번에 로드하여 캐시

        이후 _get_npc_frequency, _count_recent_cliches, _check_hud_anomalies에서
        DB 직접 조회 대신 캐시 사용
        """
        # 이미 같은 에피소드에 대해 캐시됨
        if self._cache_ep_num == ep_num and self._manuscript_cache:
            return

        self._manuscript_cache = {}
        self._cache_ep_num = ep_num

        try:
            for i in range(max(1, ep_num - window), ep_num):
                try:
                    past_ms = self.context.db.get_manuscript(i)
                    if past_ms:
                        content = past_ms.get("content", "") if isinstance(past_ms, dict) else str(past_ms)
                        # [LM-Tier TF-E] manuscripts 테이블에 hud_snapshot 컬럼 활성화 — JSON dict 반환
                        hud_snapshot = past_ms.get("hud_snapshot", {}) if isinstance(past_ms, dict) else {}
                        self._manuscript_cache[i] = {"content": content, "hud_snapshot": hud_snapshot}
                except (KeyError, TypeError, AttributeError):  # [V64.P4] individual ms load failure
                    continue
        except Exception as e:  # [V64.P4] IMPORTANT: manuscript cache build failure affects continuity checks
            logging.warning(f" [V64.P4] 원고 캐시 구축 실패: {str(e)[:60]}")

    def invalidate_manuscript_cache(self):
        """원고 캐시 무효화 (에피소드 롤백 시 호출)."""
        self._manuscript_cache = {}
        self._cache_ep_num = -1
        self._last_inplace_patch_trace = {}

    def _get_cached_manuscript(self, ep_num: int) -> dict:
        """[V60.82] 캐시에서 원고 조회"""
        return self._manuscript_cache.get(ep_num, {"content": "", "hud_snapshot": {}})

    # =========================================================================
    # [V60.81] NPC/HUD 추적 기능
    # =========================================================================

    def _get_npc_frequency(self, *args, **kwargs):
        return self.context_builder._get_npc_frequency(*args, **kwargs)

    def _get_npc_frequency_warning(self, *args, **kwargs):
        return self.context_builder._get_npc_frequency_warning(*args, **kwargs)

    def _count_recent_cliches(self, *args, **kwargs):
        return self.quality_gate._count_recent_cliches(*args, **kwargs)

    def _get_hud_trend_safe(self, *args, **kwargs):
        return self.context_builder._get_hud_trend_safe(*args, **kwargs)

    def _extract_numeric_value(self, *args, **kwargs):
        return self.context_builder._extract_numeric_value(*args, **kwargs)

    def _build_hud_context(self, *args, **kwargs):
        return self.context_builder._build_hud_context(*args, **kwargs)

    def _check_hud_anomalies(self, *args, **kwargs):
        return self.context_builder._check_hud_anomalies(*args, **kwargs)

    def _get_npc_equipment_summary(self, *args, **kwargs):
        return self.context_builder._get_npc_equipment_summary(*args, **kwargs)

    # =========================================================================
    # [V60.81] DNA 모드 & 1화 특수 처리
    # =========================================================================

    def _get_dna_instruction(self, *args, **kwargs):
        return self.context_builder._get_dna_instruction(*args, **kwargs)

    # =========================================================================
    # [V60.81] Context Building (Writer 통합) - 독립 실행용
    # =========================================================================

    def _build_anti_trope_instructions(self, *args, **kwargs):
        return self.context_builder._build_anti_trope_instructions(*args, **kwargs)

    def _build_mandatory_context(self, *args, **kwargs):
        return self.context_builder._build_mandatory_context(*args, **kwargs)

    def _extract_recent_events(self, *args, **kwargs):
        return self.context_builder._extract_recent_events(*args, **kwargs)

    def _extract_npc_last_states(self, *args, **kwargs):
        return self.context_builder._extract_npc_last_states(*args, **kwargs)

    def _build_justification_guidance(self, *args, **kwargs):
        return self.context_builder._build_justification_guidance(*args, **kwargs)

    # [V65] Dead Code 삭제: _self_refine (-85줄), EMOTION_STATES/GENRE_EMOTION_PATTERNS/
    # generate_emotion_skeleton/_analyze_scene_types/build_emotion_prompt_injection/
    # auto_map_emotions_to_manuscript/get_emotion_skeleton_lazy (-320줄),
    # quick_self_check/self_review_and_refine (-197줄)
