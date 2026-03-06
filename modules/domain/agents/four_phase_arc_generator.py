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

from modules.core.constants import ContextLimits, Stage2Limits
from modules.validation.threshold_helper import _threshold

from .arc_ensemble import ArcEnsembleGenerator
from .base_agent import BaseAgent, _get_sub_component_models
from .constraint_compiler import ConstraintCompiler
from .negative_example_injector import NegativeExampleInjector
from .preflight_checker import PreflightChecker
from .unified_arc_validator import UnifiedArcValidator

_NS3B_DIVERGENCE_THRESHOLD: float = _threshold("arc.ns3b_divergence_threshold", 0.30)

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
    for key in ("total_assets", "assets", "capital", "total_capital"):
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


def _ns4_extract_time_markers(arc_data: dict) -> list:
    """[NS-4-S2] Arc tactical_doc/beat_sequence에서 날짜·상대시간 마커 추출 (regex, LLM 0회)."""
    import re as _re
    _text = (arc_data.get("tactical_doc") or "") + "\n" + (arc_data.get("beat_sequence") or "")
    _patterns = [
        r"\d{4}년\s*\d{1,2}월(?:\s*\d{1,2}일)?",
        r"\d{1,2}월\s*\d{1,2}일",
        r"\d{1,2}월(?:\s*(?:말|초|중순|하순|상순))?",
        r"\d+(?:일|주|달|개월|년)\s*(?:후|전)",
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


class FourPhaseArcGenerator(BaseAgent):
    """
    [V60.75] Three Phase Arc Generator

    3단계 파이프라인: 제약수집 → 생성 → 검증
    (클래스명은 호환성을 위해 유지)
    """

    def __init__(self, context, client, model_tier: str = None):
        super().__init__(context, client, model_tier)
        # DI 후보: context.master_bible (getattr fallback 2회: L177, L545 — protagonist_config 추출)
        # DI 후보: context.guard (hasattr 패턴 — 장르 감지용, L63)

        # 서브 모듈
        sub_models = _get_sub_component_models("four_phase_arc_generator")
        self.preflight = PreflightChecker(context, client, sub_models.get("preflight", "gemini-2.5-flash"))
        self.ensemble = ArcEnsembleGenerator(context, client, sub_models.get("ensemble", "gemini-2.5-pro"))
        self.validator = UnifiedArcValidator(context, client, sub_models.get("validator", "gemini-2.5-flash"))
        self.compiler = ConstraintCompiler()
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
        self.negative_injector = NegativeExampleInjector(_detected_genre)

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
            (ep_count, reasoning) - 3~7 범위의 화수와 결정 이유
        """
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
        if content_len < 500:
            ep_count = Stage2Limits.MIN_EP_COUNT  # 3화
            reasoning = f"블록 정보량 부족 ({content_len}자 < 500자) → 최소 화수"
        elif content_len > 1500:
            ep_count = Stage2Limits.MAX_EP_COUNT  # 7화
            reasoning = f"블록 정보량 풍부 ({content_len}자 > 1500자) → 최대 화수"
        else:
            # 500~1500자 구간: 문장 수 비례로 4~6화 결정
            import re

            sentence_count = len(re.split(r"[.。!?!\?\n]+", block_content))
            if sentence_count <= 8:
                ep_count = 4
                reasoning = f"보통 정보량 ({content_len}자, {sentence_count}문장) → 4화"
            elif sentence_count >= 15:
                ep_count = 6
                reasoning = f"높은 정보량 ({content_len}자, {sentence_count}문장) → 6화"
            else:
                ep_count = Stage2Limits.DEFAULT_EP_COUNT  # 5화
                reasoning = f"표준 정보량 ({content_len}자, {sentence_count}문장) → 기본 5화"

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
        ep_count = max(Stage2Limits.MIN_EP_COUNT, min(Stage2Limits.MAX_EP_COUNT, ep_count))

        return ep_count, reasoning

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
        entity_registry: dict = None,  # [V60.92] Entity Registry (NPC 명칭 일관성)
        state_tracker=None,  # [V60.94] StateTracker (죽은 NPC 검증용)
        vector_context: str = "",  # [V63.3] 벡터 검색 결과
        adversarial_self_play=None,
        director=None,  # [TF-47] Arc 후보 Director 비교 선택
    ) -> tuple[dict | None, dict]:
        """
        3단계 Arc 생성

        Args:
            arc_no: Arc 번호
            ep_start: 시작 화수
            vol_strategy: Volume 전략
            curr_block: 현재 블록 DNA
            prev_arcs: 이전 Arc 리스트
            assets: AssetLibrary
            max_internal_retries: 내부 재시도 횟수
            protagonist_name: 주인공 이름
            director_feedback: [V60.77] Director REJECT 피드백 (재시도 시 반영)
            entity_registry: [V60.92] Entity Registry (NPC 명칭 일관성)
            state_tracker: [V60.94] StateTracker (죽은 NPC 검증용)
            vector_context: [V63.3] 벡터 검색 결과 (과거 유사 맥락)
            director: [TF-47] Director 인스턴스 (Arc 후보 비교 선택용, None이면 기존 Validator 경로)

        Returns:
            (generated_arc, pipeline_result)
        """
        self.stats["total_attempts"] += 1

        # [V60.88] protagonist_config 추출 (context에서 직접 로드)
        protagonist_config = {}
        try:
            master_bible = getattr(self.context, "master_bible", {})
            if master_bible:
                bible_root = master_bible.get("MasterBible", master_bible)
                protagonist_config = bible_root.get("protagonist_config", {})
        except Exception as e:
            logging.debug("[TF-26] master_bible access failed (generate): %s", str(e)[:100])

        # [V61.1] LLM 기반 가변 페이싱 - ep_count 동적 결정
        ep_count, pacing_reason = self._determine_ep_count(curr_block, arc_no, prev_arcs)
        logging.info(f" [V61.1] 가변 페이싱: {ep_count}화 결정 - {pacing_reason}")

        pipeline_result = {
            "arc_no": arc_no,
            "phases": {},
            "final_verdict": None,
            "retries": 0,
            "patch_used": False,
            "patch_fallback": False,
        }

        # [V62.5] 이전 Arc 아이템/수여물 사전 수집 (UnifiedArcValidator 중복 스캔 방지)
        _pre_items = set()
        _pre_grants = set()
        for _prev in prev_arcs:
            _acq = _prev.get("state_constraints", {}).get("items_acquired", [])
            if isinstance(_acq, list):
                _pre_items.update(
                    (i.get("name", i.get("item", "")) if isinstance(i, dict) else str(i)).strip() for i in _acq if i
                )
            _grt = _prev.get("state_constraints", {}).get("grants_received", [])
            if isinstance(_grt, list):
                _pre_grants.update(
                    (g.get("name", g.get("item", "")) if isinstance(g, dict) else str(g)).strip() for g in _grt if g
                )

        # Preflight 캐싱
        cached_constraint_block = None
        cached_preflight = None
        # [V60.77] Director 피드백이 있으면 우선 반영
        feedback = ""
        _base_director_feedback = ""
        if director_feedback:
            _base_director_feedback = f"[🎬 Director 피드백 - 반드시 반영할 것]\n{director_feedback}\n"
            feedback = _base_director_feedback
            logging.info(f" [V60.77] Director 피드백 주입됨 ({len(director_feedback)}자)")

        # [Patch Mode] 내부 retry용 이전 REJECT 추적
        _prev_rejected_arc = None
        _prev_reject_feedback = ""
        _prev_selected_strategy = ""  # [EnsembleFB] REJECT된 당선 전략 이름
        _spare_candidates: list[dict] = []  # [SpareCandidate] 앙상블 차순위 재활용 풀

        for retry in range(max_internal_retries + 1):
            pipeline_result["retries"] = retry

            # ═══════════════════════════════════════════════════════════════
            # PHASE 1: CONSTRAINT - 제약 수집
            # ═══════════════════════════════════════════════════════════════
            if cached_constraint_block and retry > 0:
                logging.info(" [Phase 1] 제약 캐시 사용")
                full_constraint_block = cached_constraint_block
                preflight_result = cached_preflight
            else:
                logging.info(f" [Phase 1] 제약 수집 중... (이전 Arc {len(prev_arcs)}개)")

                preflight_result = self.preflight.analyze(prev_arcs)
                preflight_injection = self.preflight.generate_analyst_injection(preflight_result, genre=self._genre)
                compiled_constraints = self.compiler.compile(prev_arcs)
                negative_examples = self.negative_injector.generate_injection()
                self_check = self.negative_injector.generate_self_check_prompt()

                # [TF-39] P1-4: 제약 블록 섹션 구조화
                # [TF-60] 비무협 장르: 정신력/내공/마나 수치 금지
                _genre_energy_warning = (
                    f"⚠️ 이 작품은 {self._genre} 장르입니다. tactical_doc의 [시작 상태]/[종료 상태]에\n"
                    '"내공", "정신력", "마나" 등의 수치화된 능력치를 사용하지 마세요.\n'
                    "심리 상태는 서술형으로 표현하세요. (예: \"극도의 긴장 상태\", \"자신감 회복\")"
                ) if self._genre not in ("wuxia",) else ""
                full_constraint_block = "\n\n".join(
                    part
                    for part in [
                        _genre_energy_warning,
                        f"### [PREFLIGHT 분석]\n{preflight_injection}" if preflight_injection else "",
                        f"### [HARD CONSTRAINTS — 절대 금지]\n{compiled_constraints}" if compiled_constraints else "",
                        f"### [NEGATIVE EXAMPLES]\n{negative_examples}" if negative_examples else "",
                        f"### [SELF-CHECK]\n{self_check}" if self_check else "",
                    ]
                    if part.strip()
                )

                cached_preflight = preflight_result
                cached_constraint_block = full_constraint_block

            pipeline_result["phases"]["constraint"] = {
                "status": "complete" if retry == 0 else "cached",
                "constraint_block_length": len(full_constraint_block),
            }
            self.stats["phase1_complete"] += 1

            # ═══════════════════════════════════════════════════════════════
            # PHASE 2: GENERATE - Ensemble 생성
            # ═══════════════════════════════════════════════════════════════
            logging.info(" [Phase 2] Ensemble 생성 중 (3개 후보)...")

            prev_arc_context = self._generate_prev_context(prev_arcs, preflight_result)
            # [V63.3] 벡터 메모리 컨텍스트 주입
            if vector_context:
                prev_arc_context = f"{prev_arc_context}\n\n[과거 유사 맥락 (벡터 검색)]\n{vector_context}"

            # [Patch Mode] 내부 retry: 이전 REJECT arc가 있으면 패치 시도
            best_arc = None
            all_candidates = []
            if _prev_rejected_arc and retry >= 1:
                pipeline_result["patch_used"] = True
                logging.info(f"[Patch Mode] FourPhase 내부 패치 시도 (retry={retry})")
                try:
                    best_arc, _patch_result = self.patch_arc_with_feedback(
                        original_arc=_prev_rejected_arc,
                        director_feedback=_prev_reject_feedback,
                        attempt_number=retry + 1,
                        arc_no=arc_no,
                        ep_start=ep_start,
                        vol_strategy=vol_strategy,
                        curr_block=curr_block,
                        prev_arcs=prev_arcs,
                        assets=assets,
                        protagonist_name=protagonist_name,
                        entity_registry=entity_registry,
                        state_tracker=state_tracker,
                        vector_context=vector_context,
                        adversarial_self_play=adversarial_self_play,
                    )
                    if best_arc and _patch_result.get("final_verdict") == "PASS":
                        # 패치 + 검증 모두 성공 → Phase 3 스킵하고 바로 반환
                        pipeline_result["phases"]["generate"] = {
                            "status": "patch_pass",
                            "candidates_count": 1,
                            "selected_strategy": "patch",
                        }
                        pipeline_result["final_verdict"] = "PASS"
                        pipeline_result["retries"] = retry
                        self.stats["phase3_pass"] += 1
                        logging.info(f"✅ [Patch Mode] FourPhase 내부 패치 성공 (retry={retry})")
                        return best_arc, pipeline_result
                    # 패치 검증 실패 → 폴백
                    if not best_arc:
                        pipeline_result["patch_fallback"] = True
                        logging.info("[Patch Mode] FourPhase 내부 패치 실패 → 전면 재생성 폴백")
                except Exception as _patch_err:
                    logging.warning(f"[Patch Mode] FourPhase 내부 패치 오류: {str(_patch_err)[:80]}")
                    pipeline_result["patch_fallback"] = True
                    best_arc = None

            if not best_arc:
                # [SpareCandidate] 차순위 후보가 남아있으면 재생성 없이 재활용
                if _spare_candidates:
                    best_arc = _spare_candidates.pop(0)
                    all_candidates = [best_arc]
                    logging.info(f" [SpareCandidate] 차순위 재활용 (남은 후보: {len(_spare_candidates)}개)")
                else:
                    best_arc, all_candidates = self.ensemble.generate_ensemble(
                        arc_no=arc_no,
                        ep_start=ep_start,
                        vol_strategy=vol_strategy,
                        curr_block=curr_block,
                        prev_arc_context=prev_arc_context,
                        constraint_block=full_constraint_block,
                        assets=assets,
                        feedback=feedback,
                        strategy_specific_feedback=_prev_reject_feedback if retry > 0 else "",  # [EnsembleFB]
                        rejected_strategy=_prev_selected_strategy if retry > 0 else "",  # [EnsembleFB]
                        protagonist_name=protagonist_name,
                        protagonist_config=protagonist_config,  # [V60.88]
                        entity_registry=entity_registry,  # [V60.92] Entity Registry
                        ep_count=ep_count,  # [V61.1] 가변 페이싱
                        retry=retry,  # [V61.5] 재시도 시 thinking 다운그레이드
                    )
                    # [SpareCandidate] 차순위 후보 보존 (best_arc 제외한 나머지)
                    if all_candidates and len(all_candidates) > 1:
                        for _c in all_candidates:
                            if _c is not best_arc and _c not in _spare_candidates:
                                _spare_candidates.append(_c)
                        if _spare_candidates:
                            logging.info(f" [SpareCandidate] 차순위 {len(_spare_candidates)}개 보존")

            if best_arc:
                logging.info(f"✅ [Phase 2] Ensemble 완료 — 선택 전략: {best_arc.get('strategy', '?')}")

            if not best_arc:
                logging.warning("❌ [Phase 2] Ensemble 생성 실패")
                pipeline_result["phases"]["generate"] = {"status": "failed"}
                # [Sweep55] Director 원래 피드백 보존 (Sweep53 패턴과 동일)
                _gen_fail_msg = "Ensemble 생성 실패. 다시 시도하세요."
                feedback = f"{_base_director_feedback}\n{_gen_fail_msg}" if _base_director_feedback else _gen_fail_msg
                continue

            if retry >= 2 and adversarial_self_play and best_arc:
                try:
                    _asp_ctx = {
                        "arc_no": arc_no,
                        "ep_start": ep_start,
                        "director_feedback": feedback,
                    }
                    _asp_input = json.dumps(best_arc, ensure_ascii=False)
                    _asp_result = adversarial_self_play.generate_with_adversary(
                        initial_content=_asp_input,
                        content_type="arc",
                        context=_asp_ctx,
                    )
                    _asp_output = getattr(_asp_result, "final_output", "") if _asp_result else ""
                    if _asp_output:
                        _asp_arc = self._extract_json_robust(_asp_output)
                        if not isinstance(_asp_arc, dict) or not _asp_arc:
                            try:
                                _asp_arc = json.loads(_asp_output)
                            except (json.JSONDecodeError, ValueError):
                                _asp_arc = {}
                        if isinstance(_asp_arc, dict) and _asp_arc.get("tactical_doc"):
                            # [TF10-P2] episode_details 복원 — ASP 교체 시 소실 방지
                            _orig_details = best_arc.get("episode_details")
                            best_arc = _asp_arc
                            if _orig_details and not best_arc.get("episode_details"):
                                best_arc["episode_details"] = _orig_details
                            pipeline_result["asp_used"] = True
                            logging.info(f"✅ [ASP] Stage2 Arc 교정 적용 (retry={retry})")
                except Exception as e:
                    logging.warning(f"[SilentPass:Stage2:ASP] {e!s:.120}")

            # [EnsembleFB] 당선 전략 이름 기록 (REJECT 시 다음 retry에 전달)
            _current_strategy = best_arc.get("_ensemble_meta", {}).get("best_strategy", "unknown")
            pipeline_result["phases"]["generate"] = {
                "status": "complete",
                "candidates_count": len(all_candidates),
                "selected_strategy": _current_strategy,
            }
            self.stats["phase2_complete"] += 1

            # ═══════════════════════════════════════════════════════════════
            # PHASE 2.5: AUTO-SANITIZE - 부상 에스컬레이션 자동 세정
            # ═══════════════════════════════════════════════════════════════
            best_arc = self._check_arc_end_state(best_arc)

            # [TF-22-01] arc_start_state.location 강제 주입 — Arc 경계 공간 연속성
            if prev_arcs:
                _last_end = prev_arcs[-1].get("state_constraints", {}).get("arc_end_state", {})
                _plan_loc = _last_end.get("location") if isinstance(_last_end, dict) else None
                _exec_state = self._load_execution_state(prev_arcs[-1])
                _forced_loc = (_exec_state.get("protagonist_location") if _exec_state else None) or _plan_loc
                if _forced_loc:
                    _sc = best_arc.setdefault("state_constraints", {})
                    _as = _sc.setdefault("arc_start_state", {})
                    if not _as.get("location"):
                        _as["location"] = _forced_loc

            # [NS-3-B] Phase 2.55: Treatment block numeric target alignment (advisory, Python-only)
            _ns3b_warning = _check_arc_vs_block_targets(best_arc, curr_block, arc_no)
            if _ns3b_warning:
                logging.warning("[NS-3-B] %s", _ns3b_warning)
                _ns3b_header = f"[NS-3-B 수치 목표 괴리 경고]\n{_ns3b_warning}"
                feedback = f"{_ns3b_header}\n\n{feedback}" if feedback else _ns3b_header

            # ═══════════════════════════════════════════════════════════════
            # PHASE 2.6: DIRECTOR SELECTION — 후보 비교 선택 [TF-47]
            # ═══════════════════════════════════════════════════════════════
            if director and len(all_candidates) >= 2:
                _valid_for_director = [c for c in all_candidates if c.get("tactical_doc")]
                if len(_valid_for_director) >= 2:
                    logging.info(f" [TF-47] Director Arc 비교 선택 ({len(_valid_for_director)}개 후보)")
                    try:
                        _dir_result = director.compare_and_select_arc(
                            candidates=_valid_for_director,
                            arc_no=arc_no,
                            curr_block=curr_block,
                            prev_arc_context=prev_arc_context,
                            constraint_block=full_constraint_block,
                        )
                        _dir_decision = _dir_result.get("decision", "REJECT")
                        _dir_arc = _dir_result.get("selected_arc")

                        if _dir_decision == "PASS" and _dir_arc:
                            best_arc = _dir_arc
                            pipeline_result["phases"]["director_selection"] = {
                                "status": "pass",
                                "score": _dir_result.get("score", 0),
                                "selected_strategy": _dir_arc.get("_strategy", "?"),
                            }
                            pipeline_result["final_verdict"] = "PASS"
                            self.stats["phase3_pass"] += 1
                            logging.info(f"✅ [TF-47] Director PASS — Arc {arc_no}")
                            return best_arc, pipeline_result

                        elif _dir_decision == "PASS_WITH_FIX" and _dir_arc:
                            best_arc = _dir_arc
                            pipeline_result["phases"]["director_selection"] = {
                                "status": "pass_with_fix",
                                "score": _dir_result.get("score", 0),
                                "feedback": _dir_result.get("feedback", ""),
                                "fix_scope": _dir_result.get("fix_scope", "inplace"),
                            }
                            pipeline_result["final_verdict"] = "PASS"
                            self.stats["phase3_pass"] += 1
                            logging.info(f"✅ [TF-47] Director PASS_WITH_FIX — Arc {arc_no}")
                            return best_arc, pipeline_result

                        else:
                            # Director REJECT → 피드백으로 retry
                            best_arc = _dir_arc or best_arc
                            _dir_feedback = _dir_result.get("feedback", "Director REJECT")
                            feedback = (
                                f"{_base_director_feedback}\n[Director 비교 피드백]\n{_dir_feedback}"
                                if _base_director_feedback
                                else _dir_feedback
                            )
                            pipeline_result["phases"]["director_selection"] = {
                                "status": "reject",
                                "score": _dir_result.get("score", 0),
                            }
                            logging.warning(f"❌ [TF-47] Director REJECT — Arc {arc_no}, retry")

                            _prev_rejected_arc = best_arc
                            _prev_reject_feedback = feedback
                            _prev_selected_strategy = _dir_arc.get("_strategy", "unknown") if _dir_arc else "unknown"
                            _spare_candidates.clear()
                            continue  # retry loop

                    except Exception as e:
                        logging.warning(f"[TF-47] Director 비교 실패, Validator 폴백: {str(e)[:100]}")

            # ═══════════════════════════════════════════════════════════════
            # PHASE 3: VALIDATE - 통합 검증 (Director 미사용 또는 단일 후보 시)
            # ═══════════════════════════════════════════════════════════════
            logging.info(" [Phase 3] 통합 검증 중...")

            verdict, validation_result = self.validator.validate(
                arc=best_arc,
                prev_arcs=prev_arcs,
                constraints=full_constraint_block,
                state_tracker=state_tracker,  # [V60.94] 죽은 NPC 검증용
                pre_collected_items=_pre_items,  # [V62.5] 중복 스캔 방지
                pre_collected_grants=_pre_grants,  # [V62.5] 중복 스캔 방지
                genre=self._genre,
            )

            pipeline_result["phases"]["validate"] = {
                "status": "complete",
                "verdict": verdict,
                "issues_count": len(validation_result.get("issues", [])),
                "confidence": validation_result.get("confidence", 0),
            }

            if verdict == "PASS":
                self.stats["phase3_pass"] += 1
                pipeline_result["final_verdict"] = "PASS"
                logging.info(f"✅ [Phase 3] PASS - Arc {arc_no} 생성 완료")
                _conf = validation_result.get("confidence", 0)
                _all_issues = validation_result.get("issues", [])
                _n_issues = len(_all_issues)
                _summary = validation_result.get("summary", "")
                _major_issues = [i for i in _all_issues if i.get("severity") == "MAJOR"]
                logging.debug("[Stage2 Validator] Arc %d PASS (confidence=%.2f, issues=%d) summary=%s",
                    arc_no,
                    _conf,
                    _n_issues,
                    str(_summary)[:300],
                )
                for _mi in _major_issues[:3]:
                    logging.debug(" MAJOR 경고: %s", _mi.get("issue", "?")[:120])
                return best_arc, pipeline_result
            else:
                self.stats["phase3_reject"] += 1
                # [Sweep53] Director 원래 피드백 보존 + 검증 피드백 결합
                _validator_feedback = validation_result.get("feedback", "검증 실패")
                feedback = (
                    f"{_base_director_feedback}\n[검증 피드백]\n{_validator_feedback}"
                    if _base_director_feedback
                    else _validator_feedback
                )

                # [Patch Mode] REJECT된 arc 보존 (다음 retry에서 패치 시도용)
                if best_arc:
                    _prev_rejected_arc = best_arc
                    _prev_reject_feedback = feedback
                    _prev_selected_strategy = _current_strategy  # [EnsembleFB]
                    # [SpareCandidate] score가 너무 낮으면 동일 배치 차순위도 품질 부족 → 버림
                    # confidence는 0.0~1.0 float (UnifiedArcValidator 반환)
                    _reject_confidence = validation_result.get("confidence", 0)
                    if _reject_confidence < 0.5:
                        _spare_candidates.clear()
                        logging.info(f"[SpareCandidate] confidence={_reject_confidence:.2f} < 0.5 → 차순위 전량 폐기")

                # REJECT 기록
                issues = validation_result.get("issues", [])
                logging.debug("[Stage2 Validator] Arc %d REJECT (%d/%d) confidence=%.2f",
                    arc_no,
                    retry + 1,
                    max_internal_retries + 1,
                    validation_result.get("confidence", 0),
                )
                for issue in issues[:5]:
                    logging.debug(" [%s][%s] %s",
                        issue.get("severity", "?"),
                        issue.get("category", "?"),
                        issue.get("issue", "?")[:120],
                    )
                logging.debug(" 피드백: %s", str(_validator_feedback)[:200])
                if issues:
                    first_issue = issues[0]
                    self.negative_injector.record_rejection(
                        best_arc, first_issue.get("issue", "알 수 없음"), first_issue.get("category", "unknown")
                    )

                    # 이슈 출력
                    logging.warning(" [Phase 3] REJECT - 주요 이슈:")
                    for issue in issues[:3]:
                        sev = issue.get("severity", "?")
                        cat = issue.get("category", "?")
                        text = issue.get("issue", "?")
                        logging.info(f"[{sev}][{cat}] {text}")

                logging.warning(f"❌ [Phase 3] REJECT - 재시도 {retry + 1}/{max_internal_retries + 1}")

        # 모든 재시도 실패
        pipeline_result["final_verdict"] = "FAILED"
        logging.warning(f"❌ [ThreePhase] Arc {arc_no} 모든 재시도 실패 ({max_internal_retries + 1}회)")
        if feedback:
            logging.info(f"마지막 피드백: {feedback[:200]}...")
        return None, pipeline_result

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
            logging.warning("[TRUNCATION] _inplace_patch_arc: Arc JSON %d자 → 30000자 (%.1f%% 손실)",
                len(_full_json),
                (1 - 30000 / len(_full_json)) * 100,
            )
        original_json = _full_json[:30000]

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
            # 원본 필드 병합 (부분 응답 보상)
            for key, val in original_arc.items():
                if key not in result:
                    result[key] = val
            # arc_end_state 검증
            _sc = result.get("state_constraints", {})
            if not isinstance(_sc, dict) or not _sc.get("arc_end_state"):
                logging.warning("[TF-23] InPlace: arc_end_state 누락 → 실패")
                return None
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

        # 1) YAML 프롬프트 로드
        try:
            from modules.core.prompt_loader import PromptLoader

            _patch_template = PromptLoader().load("arc_generator", "ARC_PATCH_MODE_PROMPT")
        except Exception as e:
            logging.warning(f"[SilentPass:ArcGen] ARC_PATCH_MODE_PROMPT 로드 실패: {e!s:.100}")
            _patch_template = None

        # 2) 원본 Arc 직렬화
        _full_json = json.dumps(original_arc, ensure_ascii=False, indent=2)
        if len(_full_json) > 30000:
            logging.warning("[TRUNCATION] patch_arc_with_feedback: Arc JSON %d자 → 30000자 (%.1f%% 손실)",
                len(_full_json),
                (1 - 30000 / len(_full_json)) * 100,
            )
        _original_text = _full_json[:30000]

        # 3) 패치 프롬프트 포맷
        if _patch_template:
            # [Sweep55] .format()에 json.dumps의 {}가 있으면 KeyError/ValueError 크래시 방지
            # WARNING: _esc()는 str.format() 호출 전에 반드시 적용해야 합니다.
            # JSON 문자열 내 {/}가 format placeholder로 해석되어 KeyError 발생 방지.
            def _esc(s):
                """Escape braces for str.format() — {→{{ }→}}"""
                return s.replace("{", "{{").replace("}", "}}")

            _patch_section = _patch_template.format(
                feedback_text=_esc(director_feedback),
                original_arc=_esc(_original_text),
            )
        else:
            _patch_section = (
                f"[패치 모드: Arc 원본 보존 + 지적사항만 수정]\n\n"
                f"## Director 피드백\n{director_feedback}\n\n"
                f"## 원본 Arc\n{_original_text}\n\n"
                f"전면 재설계하지 마세요. 지적된 부분만 고치세요."
            )

        enhanced_feedback = (
            f"[🔧 {attempt_number}차 수정 - 패치 모드: Arc 원본 보존 + 지적사항만 수정]\n\n"
            f"{_patch_section}\n\n"
            f"⚠️ 원본 Arc의 전체 구조, 에피소드 배분, 서사 흐름을 보존하면서 피드백 지적사항만 수정하세요.\n"
            f"⚠️ 수정하지 않는 부분은 원본을 그대로 유지하세요."
        )

        # 4) Phase 1: Constraint (generate()와 동일)
        preflight_result = self.preflight.analyze(prev_arcs)
        preflight_injection = self.preflight.generate_analyst_injection(preflight_result, genre=self._genre)
        compiled_constraints = self.compiler.compile(prev_arcs)
        negative_examples = self.negative_injector.generate_injection()
        self_check = self.negative_injector.generate_self_check_prompt()
        # [TF-39] P1-4: 제약 블록 섹션 구조화
        # [TF-60] 비무협 장르: 정신력/내공/마나 수치 금지
        _genre_energy_warning_p = (
            f"⚠️ 이 작품은 {self._genre} 장르입니다. tactical_doc의 [시작 상태]/[종료 상태]에\n"
            '"내공", "정신력", "마나" 등의 수치화된 능력치를 사용하지 마세요.\n'
            "심리 상태는 서술형으로 표현하세요. (예: \"극도의 긴장 상태\", \"자신감 회복\")"
        ) if self._genre not in ("wuxia",) else ""
        full_constraint_block = "\n\n".join(
            part
            for part in [
                _genre_energy_warning_p,
                f"### [PREFLIGHT 분석]\n{preflight_injection}" if preflight_injection else "",
                f"### [HARD CONSTRAINTS — 절대 금지]\n{compiled_constraints}" if compiled_constraints else "",
                f"### [NEGATIVE EXAMPLES]\n{negative_examples}" if negative_examples else "",
                f"### [SELF-CHECK]\n{self_check}" if self_check else "",
            ]
            if part.strip()
        )

        # 5) Phase 2: Ensemble 생성 (패치 피드백 주입)
        ep_count, _ = self._determine_ep_count(curr_block, arc_no, prev_arcs)
        protagonist_config = {}
        try:
            master_bible = getattr(self.context, "master_bible", {})
            if master_bible:
                bible_root = master_bible.get("MasterBible", master_bible)
                protagonist_config = bible_root.get("protagonist_config", {})
        except Exception as e:
            logging.debug("[TF-26] master_bible access failed (patch): %s", str(e)[:100])

        prev_arc_context = self._generate_prev_context(prev_arcs, preflight_result)
        if vector_context:
            prev_arc_context = f"{prev_arc_context}\n\n[과거 유사 맥락 (벡터 검색)]\n{vector_context}"

        try:
            best_arc, all_candidates = self.ensemble.generate_ensemble(
                arc_no=arc_no,
                ep_start=ep_start,
                vol_strategy=vol_strategy,
                curr_block=curr_block,
                prev_arc_context=prev_arc_context,
                constraint_block=full_constraint_block,
                assets=assets,
                feedback=enhanced_feedback,
                protagonist_name=protagonist_name,
                protagonist_config=protagonist_config,
                entity_registry=entity_registry,
                ep_count=ep_count,
                retry=0,
                single_strategy=rejected_strategy,  # [TF-36] partial 시 1개 전략만
            )
        except Exception as e:
            logging.warning(f"[Patch Mode] Arc ensemble 생성 실패: {e!s:.200}")
            pipeline_result["final_verdict"] = "FAILED"
            return None, pipeline_result

        if not best_arc:
            logging.warning("[Patch Mode] Arc ensemble 후보 없음 → 폴백 필요")
            pipeline_result["final_verdict"] = "FAILED"
            return None, pipeline_result

        # 6) Phase 2.5: Auto-sanitize
        best_arc = self._check_arc_end_state(best_arc)

        # [TF-22-01] arc_start_state.location 강제 주입 (Patch Mode 경로)
        if prev_arcs:
            _last_end_p = prev_arcs[-1].get("state_constraints", {}).get("arc_end_state", {})
            _plan_loc_p = _last_end_p.get("location") if isinstance(_last_end_p, dict) else None
            _exec_state_p = self._load_execution_state(prev_arcs[-1])
            _forced_loc_p = (_exec_state_p.get("protagonist_location") if _exec_state_p else None) or _plan_loc_p
            if _forced_loc_p:
                _sc_p = best_arc.setdefault("state_constraints", {})
                _as_p = _sc_p.setdefault("arc_start_state", {})
                if not _as_p.get("location"):
                    _as_p["location"] = _forced_loc_p

        # 7) Phase 3: Validate
        _pre_items = set()
        _pre_grants = set()
        for _prev in prev_arcs:
            _acq = _prev.get("state_constraints", {}).get("items_acquired", [])
            if isinstance(_acq, list):
                _pre_items.update(
                    (i.get("name", i.get("item", "")) if isinstance(i, dict) else str(i)).strip() for i in _acq if i
                )
            _grt = _prev.get("state_constraints", {}).get("grants_received", [])
            if isinstance(_grt, list):
                _pre_grants.update(
                    (g.get("name", g.get("item", "")) if isinstance(g, dict) else str(g)).strip() for g in _grt if g
                )

        verdict, validation_result = self.validator.validate(
            arc=best_arc,
            prev_arcs=prev_arcs,
            constraints=full_constraint_block,
            state_tracker=state_tracker,
            pre_collected_items=_pre_items,
            pre_collected_grants=_pre_grants,
            genre=self._genre,
        )

        pipeline_result["phases"]["validate"] = {
            "status": "complete",
            "verdict": verdict,
            "issues_count": len(validation_result.get("issues", [])),
        }

        if verdict == "PASS":
            # [OpusTF] ASP 교정 — generate() L338-349 패턴 재사용
            if adversarial_self_play and best_arc:
                try:
                    _asp_ctx = {
                        "arc_no": arc_no,
                        "ep_start": ep_start,
                        "director_feedback": director_feedback,
                    }
                    _asp_input = json.dumps(best_arc, ensure_ascii=False)
                    _asp_result = adversarial_self_play.generate_with_adversary(
                        initial_content=_asp_input,
                        content_type="arc",
                        context=_asp_ctx,
                    )
                    _asp_output = getattr(_asp_result, "final_output", "") if _asp_result else ""
                    if _asp_output:
                        _asp_arc = self._extract_json_robust(_asp_output)
                        if not isinstance(_asp_arc, dict) or not _asp_arc:
                            try:
                                _asp_arc = json.loads(_asp_output)
                            except (json.JSONDecodeError, ValueError):
                                _asp_arc = {}
                        if isinstance(_asp_arc, dict) and _asp_arc.get("tactical_doc"):
                            # [TF10-P2] episode_details 복원 — Patch Mode ASP 교체 시 소실 방지
                            _orig_details = best_arc.get("episode_details")
                            best_arc = _asp_arc
                            if _orig_details and not best_arc.get("episode_details"):
                                best_arc["episode_details"] = _orig_details
                            pipeline_result["asp_used"] = True
                            logging.info(f"✅ [Patch+ASP] Arc {arc_no} ASP 교정 적용")
                except Exception as e:
                    logging.warning(f"[SilentPass:PatchMode:ASP] {e!s:.120}")

            pipeline_result["final_verdict"] = "PASS"
            logging.info(f"✅ [Patch Mode] Arc {arc_no} 패치 성공")
            return best_arc, pipeline_result

        logging.warning(f" [Patch Mode] Arc {arc_no} 패치 검증 실패 → 폴백 필요")
        pipeline_result["final_verdict"] = "FAILED"
        return None, pipeline_result

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
                _active = _ws.get("active_items", {})
                if isinstance(_active, dict) and _active:
                    result["active_items"] = {k: v for k, v in list(_active.items())[:30]}

            # 2) FactLedger — 핵심 수치 (인물, 아이템, 자산)
            _fl = _db.load_anchor("fact_ledger")
            if _fl and isinstance(_fl, dict):
                _facts = _fl.get("facts", {})
                if isinstance(_facts, dict):
                    _key_facts = {}
                    for _fk, _fv in list(_facts.items())[:30]:
                        if isinstance(_fv, dict):
                            _key_facts[_fk] = {
                                "value": _fv.get("value"),
                                "last_ep": _fv.get("last_ep"),
                            }
                    if _key_facts:
                        result["fact_ledger"] = _key_facts

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

    def _generate_prev_context(self, prev_arcs: list[dict], preflight_result: dict) -> str:
        """[V67] 이전 Arc 컨텍스트 생성 - 전문 확장 (Gemini 대용량 컨텍스트 활용)"""
        if not prev_arcs:
            return "서사 시작점 (첫 Arc)"

        lines = []
        last_arc = prev_arcs[-1]
        last_arc_no = last_arc.get("arc_no", "?")

        state = last_arc.get("state_constraints", {})
        arc_end = state.get("arc_end_state", {})
        joint = last_arc.get("joint_docs", {})
        shadow = last_arc.get("status_shadow", {})

        # 상태 추출 (arc_end_state 우선) + [V62.2] 아크 간 자연 회복
        raw_energy = arc_end.get("internal_energy")
        if raw_energy is None:
            loss_str = shadow.get("internal_energy_loss", "0%")
            try:
                import re

                _m = re.search(r"(\d+)", str(loss_str))  # [V70] None 방어
                loss = int(_m.group(1)) if _m else 0
                raw_energy = max(0, 100 - loss)
            except Exception:
                raw_energy = Stage2Limits.INTERNAL_ENERGY_FALLBACK

        # [TF-39] P0-2: 내공 자연 회복 — 최소 90% (100% 강제 리셋 → 자연 회복)
        # [TF-41] P0-1: 비무협 장르는 내공 라인 자체를 출력하지 않음
        if self._genre == "wuxia":
            final_energy = max(90, int(raw_energy) if isinstance(raw_energy, (int, float)) else 100)
            if isinstance(raw_energy, (int, float)) and raw_energy < final_energy:
                logging.info(f" [V62.2] 내공 자연 회복: {int(raw_energy)}% → {final_energy}% (아크 간 휴식)")
        else:
            final_energy = None

        raw_injuries = arc_end.get("injuries") or "없음"
        final_injuries = self._sanitize_injuries(raw_injuries)
        final_location = arc_end.get("location") or joint.get("final_location", "알 수 없음")
        final_location = _trim_location(final_location)  # [TF-60] 과잉 복사 방지
        final_equipment = arc_end.get("equipment")
        if final_equipment is None:
            final_equipment = joint.get("physical_inventory", [])
        if isinstance(final_equipment, str):
            final_equipment = [i.strip() for i in final_equipment.split(",") if i.strip()]

        # 필수 계승 블록
        lines.append("=" * 50)
        lines.append(f"🔴 [Arc {last_arc_no} 종료 상태 → 다음 Arc 필수 시작 조건]")
        lines.append("=" * 50)
        if final_energy is not None:
            lines.append(f"✅ 내공: {final_energy}%")
        lines.append(f"✅ 부상: {final_injuries}")
        lines.append(f"✅ 위치: {final_location}")
        lines.append(f"✅ 소지품: {final_equipment}")
        # [TF-59] 재무 상태 계승
        _capital = arc_end.get("capital")
        _total_assets = arc_end.get("total_assets")
        _portfolio = arc_end.get("portfolio_position")
        if _capital or _total_assets or _portfolio:
            lines.append(f"✅ 자본금: {_capital or '미기재'}")
            lines.append(f"✅ 총자산: {_total_assets or '미기재'}")
            lines.append(f"✅ 포지션: {_portfolio or '미기재'}")
        lines.append("=" * 50)
        lines.append("")

        # [TF-48] 실제 에피소드 실행 결과 주입 — Arc 계획과 실행 간 차이 보정
        _exec = self._load_execution_state(last_arc)
        if _exec:
            lines.append("=" * 50)
            lines.append("⚠️ [TF-48] 실제 에피소드 실행 결과 (Arc 계획보다 우선)")
            lines.append("다음 Arc 설계 시 아래 실행 결과를 반드시 참조하라.")
            lines.append("=" * 50)
            # 주인공 자산
            _assets = _exec.get("protagonist_assets", {})
            if _assets:
                for _ak, _av in _assets.items():
                    lines.append(f"  💰 {_ak}: {_av}")
            _status = _exec.get("protagonist_status", {})
            if _status:
                for _sk, _sv in _status.items():
                    lines.append(f"  📊 {_sk}: {_sv}")
            _loc = _exec.get("protagonist_location")
            if _loc:
                lines.append(f"  📍 실제 위치: {_loc}")
            # 최신 에피소드 재무 상태
            _les = _exec.get("last_episode_state", {})
            if _les:
                _cap = _les.get("capital")
                _total = _les.get("total_assets")
                _ep = _les.get("ep_num")
                if _cap is not None or _total is not None:
                    lines.append(f"  📋 제{_ep}화 종료 기준: 자본금={_cap}, 총자산={_total}")
                _new_items = _les.get("new_items", [])
                if _new_items:
                    lines.append(f"  🆕 제{_ep}화 신규 아이템: {_new_items}")
            # FactLedger 핵심 수치
            _fl = _exec.get("fact_ledger", {})
            if _fl:
                _fl_lines = []
                for _fk, _fv in list(_fl.items())[:15]:
                    _fl_lines.append(f"{_fk}={_fv.get('value')} (ep{_fv.get('last_ep')})")
                if _fl_lines:
                    lines.append(f"  📖 팩트원장: {'; '.join(_fl_lines)}")
            # 활성 아이템
            _ai = _exec.get("active_items", {})
            if _ai:
                _ai_names = list(_ai.keys())[:20]
                lines.append(f"  🎒 활성 아이템: {', '.join(_ai_names)}")
            lines.append("=" * 50)
            lines.append("")

        # 보조 정보
        world = preflight_result.get("world_state", {})
        conflicts = world.get("ongoing_conflicts", [])
        if conflicts:
            lines.append(f"진행 중인 갈등: {', '.join(str(c) for c in conflicts[:3])}")

        # [V62.7] 완결된 갈등 (재생성 금지)
        resolved = world.get("resolved_conflicts", [])
        if resolved:
            lines.append(f"완결된 갈등 (재생성 금지): {', '.join(str(r) for r in resolved[:5])}")

        relationships = preflight_result.get("relationship_map", {})
        if relationships:
            rel_summary = ", ".join([f"{k}: {v.get('current_state', '?')}" for k, v in list(relationships.items())[:5]])
            lines.append(f"주요 관계: {rel_summary}")

        # [TF-39] P0-3: state_changes 핵심 필드 주입
        _sc = last_arc.get("state_changes", {})
        if isinstance(_sc, dict):
            _deaths = _sc.get("npc_deaths", [])
            if _deaths:
                _names = [d.get("name", d.get("npc", str(d))) if isinstance(d, dict) else str(d) for d in _deaths[:10]]
                lines.append(f"\n🚫 사망 NPC (부활 금지): {', '.join(_names)}")

            _skills = _sc.get("skill_acquisitions", [])
            if _skills:
                _names = [
                    s.get("name", s.get("skill", str(s))) if isinstance(s, dict) else str(s) for s in _skills[:10]
                ]
                lines.append(f"⚔️ 습득 기술: {', '.join(_names)}")

            _resolved = _sc.get("resolved_plots", [])
            if _resolved:
                _names = [
                    r.get("plot", r.get("description", str(r))) if isinstance(r, dict) else str(r)
                    for r in _resolved[:10]
                ]
                lines.append(f"🚫 완결된 플롯 (재생성 금지): {', '.join(_names)}")

            _perm = _sc.get("permanent_injuries", [])
            if _perm:
                _descs = [
                    str(p)[:50] if not isinstance(p, dict) else p.get("description", str(p))[:50] for p in _perm[:5]
                ]
                lines.append(f"🩹 영구 부상: {', '.join(_descs)}")

            _comp = _sc.get("companion_changes", [])
            if _comp:
                _descs = [str(c)[:50] if not isinstance(c, dict) else c.get("name", str(c))[:30] for c in _comp[:5]]
                lines.append(f"👥 동행자 변경: {', '.join(_descs)}")

        # ── [V67] 이전 Arc tactical_doc 전문 확장 (최대 30개) ──
        _prev_start = max(0, len(prev_arcs) - 30)
        _arc_history_lines = []
        for _pa in prev_arcs[_prev_start:]:
            _pa_no = _pa.get("arc_no", "?")
            _pa_ep_s = _pa.get("ep_start", "?")
            _pa_ep_e = _pa.get("ep_end", "?")
            _pa_td = _pa.get("tactical_doc", "")
            if isinstance(_pa_td, dict):
                import json

                _pa_td = json.dumps(_pa_td, ensure_ascii=False)
            if _pa_td:
                _arc_history_lines.append(f"━━━ Arc {_pa_no} (제{_pa_ep_s}화~제{_pa_ep_e}화) ━━━\n{_pa_td}")
        if _arc_history_lines:
            _full_history = "\n\n".join(_arc_history_lines)
            # 200K자 상한
            if len(_full_history) > ContextLimits.MAX_CONTEXT_CHARS:
                _full_history = _full_history[: ContextLimits.MAX_CONTEXT_CHARS] + "\n... (200K자 절삭)"
            lines.append("")
            lines.append(f"[V67] ═══ 이전 Arc 전술서 전문 ({len(_arc_history_lines)}개) ═══")
            lines.append(_full_history)
            logging.info(f" [V67] FourPhase prev_context 확장: {len(_arc_history_lines)}개 Arc 전술서 ({len(_full_history):,}자)"
            )

        # [NS-4-S2] 이전 Arc 시간 마커 — 크로스 Arc 시간 연속성 (LLM 0회)
        try:
            _ns4_markers = _ns4_extract_time_markers(last_arc)
            if _ns4_markers:
                lines.append("")
                lines.append(
                    f"⏱️ [NS-4] 이전 Arc {last_arc_no} 시간 마커: {', '.join(_ns4_markers)}\n"
                    "※ 이번 Arc tactical_doc에 '이전 Arc 종료로부터 X달/주 후 시작'을 명시하세요."
                )
        except Exception as _ns4_s2_err:
            logging.debug("[NS-4-S2] 시간 마커 주입 실패 (비차단): %s", _ns4_s2_err)

        return "\n".join(lines)

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


def create_four_phase_generator(context, client, model_tier: str = "gemini-2.5-pro"):
    """FourPhaseArcGenerator 생성 헬퍼 (호환성 유지)"""
    return FourPhaseArcGenerator(context, client, model_tier)
