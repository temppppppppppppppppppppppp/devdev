"""
Four-phase arc runtime orchestration split.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from modules.validation.threshold_helper import _threshold

if TYPE_CHECKING:
    from .four_phase_arc_generator import FourPhaseArcGenerator

_NS3B_DIVERGENCE_THRESHOLD: float = _threshold("arc.ns3b_divergence_threshold", 0.30)


@dataclass
class _FourPhaseRuntimeBootstrap:
    protagonist_config: dict
    ep_count_suggestion: int
    pacing_signals: dict
    pipeline_result: dict
    pre_items: set[str]
    pre_grants: set[str]
    feedback: str
    base_director_feedback: str
    prev_rejected_arc: dict | None = None
    prev_reject_feedback: str = ""
    prev_selected_strategy: str = ""
    spare_candidates: list[dict] = field(default_factory=list)


@dataclass
class _FourPhaseConstraintEnvelope:
    full_constraint_block: str
    preflight_result: dict
    cached_constraint_block: str | None
    cached_preflight: dict | None


@dataclass
class _FourPhaseGenerationEnvelope:
    best_arc: dict | None
    all_candidates: list[dict]
    prev_arc_context: str
    feedback: str
    prev_rejected_arc: dict | None
    prev_reject_feedback: str
    prev_selected_strategy: str
    spare_candidates: list[dict]
    should_continue: bool = False
    patch_succeeded: bool = False


@dataclass
class _FourPhaseCandidateEnvelope:
    all_candidates: list[dict]
    ns3b_director_advisory: str
    investment_director_advisory: str
    investment_advisory: list[dict]
    candidate_quality_flags: list[dict]


@dataclass
class _FourPhaseDirectorSelectionEnvelope:
    best_arc: dict | None
    feedback: str
    prev_rejected_arc: dict | None
    prev_reject_feedback: str
    prev_selected_strategy: str
    spare_candidates: list[dict]
    should_continue: bool = False
    should_return: bool = False


@dataclass
class _FourPhaseValidationEnvelope:
    best_arc: dict | None
    feedback: str
    prev_rejected_arc: dict | None
    prev_reject_feedback: str
    prev_selected_strategy: str
    spare_candidates: list[dict]
    should_continue: bool = False
    should_return: bool = False

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

class FourPhaseArcRuntime:
    """Owns the per-arc four-phase pipeline."""

    def __init__(self, owner: "FourPhaseArcGenerator") -> None:
        self.owner = owner

    def _bootstrap_generation_state(
        self,
        *,
        arc_no: int,
        curr_block: dict,
        prev_arcs: list[dict],
        director_feedback: str,
    ) -> _FourPhaseRuntimeBootstrap:
        owner = self.owner
        owner.stats["total_attempts"] += 1

        protagonist_config = {}
        try:
            master_bible = getattr(owner.context, "master_bible", {})
            if master_bible:
                bible_root = master_bible.get("MasterBible", master_bible)
                protagonist_config = bible_root.get("protagonist_config", {})
        except Exception as e:
            logging.debug("[TF-26] master_bible access failed (generate): %s", str(e)[:100])

        ep_count_suggestion, pacing_reason = owner._determine_ep_count(curr_block, arc_no, prev_arcs)
        pacing_signals = owner._build_pacing_signal_payload(curr_block, ep_count_suggestion, pacing_reason)
        logging.info(f" [V61.1] LLM pacing suggestion: {ep_count_suggestion}화 추천 - {pacing_reason}")

        pipeline_result = {
            "arc_no": arc_no,
            "phases": {},
            "final_verdict": None,
            "retries": 0,
            "patch_used": False,
            "patch_fallback": False,
        }

        pre_items = set()
        pre_grants = set()
        for prev_arc in prev_arcs:
            prev_constraints = prev_arc.get("state_constraints", {})
            acquired = prev_constraints.get("protagonist_items") or prev_constraints.get("items_acquired", [])
            if isinstance(acquired, list):
                pre_items.update(
                    (
                        item.get("name", item.get("item", ""))
                        if isinstance(item, dict)
                        else str(item)
                    ).strip()
                    for item in acquired
                    if item
                )
            grants = prev_constraints.get("grants_received", [])
            if isinstance(grants, list):
                pre_grants.update(
                    (
                        grant.get("name", grant.get("item", ""))
                        if isinstance(grant, dict)
                        else str(grant)
                    ).strip()
                    for grant in grants
                    if grant
                )

        base_director_feedback = ""
        feedback = ""
        if director_feedback:
            base_director_feedback = f"[이전 Director 피드백 - 반드시 반영할 것]\n{director_feedback}\n"
            feedback = base_director_feedback
            logging.info(f" [V60.77] Director 피드백 주입됨 ({len(director_feedback)}자)")

        return _FourPhaseRuntimeBootstrap(
            protagonist_config=protagonist_config,
            ep_count_suggestion=ep_count_suggestion,
            pacing_signals=pacing_signals,
            pipeline_result=pipeline_result,
            pre_items=pre_items,
            pre_grants=pre_grants,
            feedback=feedback,
            base_director_feedback=base_director_feedback,
        )

    def _resolve_constraint_phase(
        self,
        *,
        retry: int,
        prev_arcs: list[dict],
        cached_constraint_block: str | None,
        cached_preflight: dict | None,
        pipeline_result: dict,
    ) -> _FourPhaseConstraintEnvelope:
        owner = self.owner

        if cached_constraint_block and retry > 0:
            logging.info(" [Phase 1] 제약 캐시 사용")
            full_constraint_block = cached_constraint_block
            preflight_result = cached_preflight or {}
        else:
            logging.info(f" [Phase 1] 제약 수집 중... (이전 Arc {len(prev_arcs)}개)")

            preflight_result = owner.preflight.analyze(prev_arcs)
            preflight_injection = owner.preflight.generate_analyst_injection(preflight_result, genre=owner._genre)
            compiled_constraints = owner.compiler.compile(prev_arcs)
            negative_examples = owner.negative_injector.generate_injection()
            self_check = owner.negative_injector.generate_self_check_prompt()

            genre_energy_warning = (
                f"⚠️ 이 작품은 {owner._genre} 장르입니다. tactical_doc의 [시작 상태]/[종료 상태]에\n"
                '"내공", "정신력", "마나" 등의 수치화된 능력치를 사용하지 마세요.\n'
                "심리 상태는 서술형으로 표현하세요. (예: \"극도의 긴장 상태\", \"자신감 회복\")"
            ) if owner._genre not in ("wuxia",) else ""
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
            cached_preflight = preflight_result
            cached_constraint_block = full_constraint_block

        pipeline_result["phases"]["constraint"] = {
            "status": "complete" if retry == 0 else "cached",
            "constraint_block_length": len(full_constraint_block),
        }
        owner.stats["phase1_complete"] += 1
        return _FourPhaseConstraintEnvelope(
            full_constraint_block=full_constraint_block,
            preflight_result=preflight_result,
            cached_constraint_block=cached_constraint_block,
            cached_preflight=cached_preflight,
        )

    def _run_generation_phase(
        self,
        *,
        retry: int,
        arc_no: int,
        ep_start: int,
        vol_strategy: str,
        curr_block: dict,
        prev_arcs: list[dict],
        assets: dict | None,
        protagonist_name: str,
        entity_registry: dict | None,
        state_tracker,
        vector_context: str,
        adversarial_self_play,
        protagonist_config: dict,
        ep_count_suggestion: int,
        pacing_signals: dict,
        full_constraint_block: str,
        preflight_result: dict,
        feedback: str,
        base_director_feedback: str,
        prev_rejected_arc: dict | None,
        prev_reject_feedback: str,
        prev_selected_strategy: str,
        spare_candidates: list[dict],
        pipeline_result: dict,
    ) -> _FourPhaseGenerationEnvelope:
        owner = self.owner

        logging.info(" [Phase 2] Ensemble 생성 중 (3개 후보)...")

        prev_arc_context = owner._generate_prev_context(prev_arcs, preflight_result)
        prev_equipment = _extract_prev_arc_end_equipment(prev_arcs)
        forbidden_items = _extract_forbidden_item_names(preflight_result)
        if vector_context:
            prev_arc_context = f"{prev_arc_context}\n\n[과거 유사 맥락 (벡터 검색)]\n{vector_context}"

        best_arc = None
        all_candidates: list[dict] = []
        if prev_rejected_arc and retry >= 1:
            pipeline_result["patch_used"] = True
            logging.info(f"[Patch Mode] FourPhase 내부 패치 시도 (retry={retry})")
            try:
                best_arc, patch_result = owner.patch_arc_with_feedback(
                    original_arc=prev_rejected_arc,
                    director_feedback=prev_reject_feedback,
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
                if best_arc and patch_result.get("final_verdict") == "PASS":
                    pipeline_result["phases"]["generate"] = {
                        "status": "patch_pass",
                        "candidates_count": 1,
                        "selected_strategy": "patch",
                    }
                    pipeline_result["final_verdict"] = "PASS"
                    pipeline_result["retries"] = retry
                    owner.stats["phase3_pass"] += 1
                    logging.info(f"✅ [Patch Mode] FourPhase 내부 패치 성공 (retry={retry})")
                    return _FourPhaseGenerationEnvelope(
                        best_arc=best_arc,
                        all_candidates=[],
                        prev_arc_context=prev_arc_context,
                        feedback=feedback,
                        prev_rejected_arc=prev_rejected_arc,
                        prev_reject_feedback=prev_reject_feedback,
                        prev_selected_strategy=prev_selected_strategy,
                        spare_candidates=spare_candidates,
                        patch_succeeded=True,
                    )
                if not best_arc:
                    pipeline_result["patch_fallback"] = True
                    logging.info("[Patch Mode] FourPhase 내부 패치 실패 → 전면 재생성 폴백")
            except Exception as patch_err:
                logging.warning(f"[Patch Mode] FourPhase 내부 패치 오류: {str(patch_err)[:80]}")
                pipeline_result["patch_fallback"] = True
                best_arc = None

        if not best_arc:
            if spare_candidates:
                best_arc = spare_candidates.pop(0)
                all_candidates = [best_arc]
                logging.info(f" [SpareCandidate] 차순위 재활용 (남은 후보: {len(spare_candidates)}개)")
            else:
                best_arc, all_candidates = owner.ensemble.generate_ensemble(
                    arc_no=arc_no,
                    ep_start=ep_start,
                    vol_strategy=vol_strategy,
                    curr_block=curr_block,
                    prev_arc_context=prev_arc_context,
                    constraint_block=full_constraint_block,
                    prev_equipment=prev_equipment,
                    forbidden_items=forbidden_items,
                    assets=assets,
                    feedback=feedback,
                    strategy_specific_feedback=prev_reject_feedback if retry > 0 else "",
                    rejected_strategy=prev_selected_strategy if retry > 0 else "",
                    protagonist_name=protagonist_name,
                    protagonist_config=protagonist_config,
                    entity_registry=entity_registry,
                    ep_count_suggestion=ep_count_suggestion,
                    pacing_signals=pacing_signals,
                    retry=retry,
                )
                if best_arc is not None and all_candidates and len(all_candidates) > 1:
                    for candidate in all_candidates:
                        if candidate is not best_arc and candidate not in spare_candidates:
                            spare_candidates.append(candidate)
                    if spare_candidates:
                        logging.info(f" [SpareCandidate] 차순위 {len(spare_candidates)}개 보존")

        if all_candidates:
            logging.info(f"✅ [Phase 2] Ensemble 완료 — {len(all_candidates)}개 후보 → Director 선택 대기")

        if not all_candidates:
            logging.warning("❌ [Phase 2] Ensemble 생성 실패")
            pipeline_result["phases"]["generate"] = {"status": "failed"}
            generate_failure = "Ensemble 생성 실패. 다시 시도하세요."
            feedback = f"{base_director_feedback}\n{generate_failure}" if base_director_feedback else generate_failure
            return _FourPhaseGenerationEnvelope(
                best_arc=None,
                all_candidates=[],
                prev_arc_context=prev_arc_context,
                feedback=feedback,
                prev_rejected_arc=prev_rejected_arc,
                prev_reject_feedback=prev_reject_feedback,
                prev_selected_strategy=prev_selected_strategy,
                spare_candidates=spare_candidates,
                should_continue=True,
            )

        if retry >= 2 and adversarial_self_play and all_candidates:
            try:
                asp_context = {
                    "arc_no": arc_no,
                    "ep_start": ep_start,
                    "director_feedback": feedback,
                }
                asp_target = all_candidates[0]
                asp_input = json.dumps(asp_target, ensure_ascii=False)
                asp_result = adversarial_self_play.generate_with_adversary(
                    initial_content=asp_input,
                    content_type="arc",
                    context=asp_context,
                )
                asp_output = getattr(asp_result, "final_output", "") if asp_result else ""
                if asp_output:
                    asp_arc = owner._extract_json_robust(asp_output)
                    if not isinstance(asp_arc, dict) or not asp_arc:
                        try:
                            asp_arc = json.loads(asp_output)
                        except (json.JSONDecodeError, ValueError):
                            asp_arc = {}
                    if isinstance(asp_arc, dict) and asp_arc.get("tactical_doc"):
                        original_details = asp_target.get("episode_details")
                        if original_details and not asp_arc.get("episode_details"):
                            asp_arc["episode_details"] = original_details
                        all_candidates[0] = asp_arc
                        if best_arc is None or best_arc is asp_target:
                            best_arc = asp_arc
                        pipeline_result["asp_used"] = True
                        logging.info(f"✅ [ASP] Stage2 Arc 교정 적용 (retry={retry})")
            except Exception as e:
                logging.warning(f"[SilentPass:Stage2:ASP] {e!s:.120}")

        return _FourPhaseGenerationEnvelope(
            best_arc=best_arc,
            all_candidates=all_candidates,
            prev_arc_context=prev_arc_context,
            feedback=feedback,
            prev_rejected_arc=prev_rejected_arc,
            prev_reject_feedback=prev_reject_feedback,
            prev_selected_strategy=prev_selected_strategy,
            spare_candidates=spare_candidates,
        )

    def _prepare_candidates_for_selection(
        self,
        *,
        arc_no: int,
        curr_block: dict,
        prev_arcs: list[dict],
        all_candidates: list[dict],
    ) -> _FourPhaseCandidateEnvelope:
        owner = self.owner

        # [TF-22-01] arc_start_state.location 강제 주입 — Arc 경계 공간 연속성
        if prev_arcs and all_candidates:
            last_end = prev_arcs[-1].get("state_constraints", {}).get("arc_end_state", {})
            plan_loc = last_end.get("location") if isinstance(last_end, dict) else None
            exec_state = owner._load_execution_state(prev_arcs[-1])
            forced_loc = (exec_state.get("protagonist_location") if exec_state else None) or plan_loc
            if forced_loc:
                for candidate in all_candidates:
                    state_constraints = candidate.setdefault("state_constraints", {})
                    arc_start_state = state_constraints.setdefault("arc_start_state", {})
                    if not arc_start_state.get("location"):
                        arc_start_state["location"] = forced_loc

        ns3b_director_advisory = ""
        investment_director_advisory = ""
        investment_advisory: list[dict] = []
        candidate_quality_flags: list[dict] = []
        ns3b_note_items: list[tuple[int, str]] = []
        ns3b_notes: list[str] = []

        if all_candidates:
            for idx, candidate in enumerate(all_candidates, start=1):
                if not isinstance(candidate, dict):
                    continue
                candidate = owner._check_arc_end_state(candidate)
                all_candidates[idx - 1] = candidate
                warning = _check_arc_vs_block_targets(candidate, curr_block, arc_no)
                if warning:
                    strategy = candidate.get("_strategy", f"candidate-{idx}")
                    ns3b_note_items.append((idx - 1, warning))
                    ns3b_notes.append(f"- 후보 {idx} ({strategy}): {warning}")
            if ns3b_notes:
                ns3b_director_advisory = "[NS-3-B 수치 목표 괴리 경고]\n" + "\n".join(ns3b_notes)
                logging.warning("[NS-3-B] Director advisory generated (%d건)", len(ns3b_notes))

        if owner._genre == "investment" and all_candidates:
            try:
                from modules.core.investment_arithmetic_checker import InvestmentArithmeticChecker

                checker = InvestmentArithmeticChecker.from_yaml()
                prev_end = {}
                if prev_arcs:
                    prev_end = prev_arcs[-1].get("state_constraints", {}).get("arc_end_state", {})

                flash_enabled = bool(_threshold("investment_math.flash_enabled", True))
                flash_ask = owner._flash_ask if flash_enabled else None
                verifier = None
                if flash_ask is not None:
                    from modules.core.investment_math_verifier import InvestmentMathVerifier

                    verifier = InvestmentMathVerifier(llm_ask=flash_ask)

                for idx, candidate in enumerate(all_candidates):
                    if not isinstance(candidate, dict):
                        continue
                    tactical_doc = str(candidate.get("tactical_doc", ""))
                    f1_results = checker.check(candidate, arc_no, prev_arc_end_state=prev_end)
                    if verifier is not None and f1_results:
                        f2_results = verifier.verify(tactical_doc, f1_results, arc_no, genre=owner._genre)
                        f1_results.extend(f2_results)
                    for result in f1_results:
                        if isinstance(result, dict):
                            result["candidate_idx"] = idx
                            investment_advisory.append(result)

                if investment_advisory:
                    investment_director_advisory = _format_investment_advisory(investment_advisory)
                    logging.warning("[F] Investment advisory generated (%d건)", len(investment_advisory))
            except Exception as e:
                logging.warning("[F] Investment advisory generation failed: %s", str(e)[:120])

        if all_candidates:
            candidate_quality_flags = _build_candidate_quality_flags(
                all_candidates,
                ns3b_note_items,
                investment_advisory,
            )

        return _FourPhaseCandidateEnvelope(
            all_candidates=all_candidates,
            ns3b_director_advisory=ns3b_director_advisory,
            investment_director_advisory=investment_director_advisory,
            investment_advisory=investment_advisory,
            candidate_quality_flags=candidate_quality_flags,
        )

    def _run_director_selection_phase(
        self,
        *,
        director,
        arc_no: int,
        curr_block: dict,
        prev_arc_context: str,
        full_constraint_block: str,
        all_candidates: list[dict],
        candidate_quality_flags: list[dict],
        ns3b_director_advisory: str,
        investment_director_advisory: str,
        investment_advisory: list[dict],
        base_director_feedback: str,
        feedback: str,
        prev_rejected_arc: dict | None,
        prev_reject_feedback: str,
        prev_selected_strategy: str,
        spare_candidates: list[dict],
        pipeline_result: dict,
    ) -> _FourPhaseDirectorSelectionEnvelope:
        owner = self.owner

        if not director or not all_candidates:
            return _FourPhaseDirectorSelectionEnvelope(
                best_arc=None,
                feedback=feedback,
                prev_rejected_arc=prev_rejected_arc,
                prev_reject_feedback=prev_reject_feedback,
                prev_selected_strategy=prev_selected_strategy,
                spare_candidates=spare_candidates,
            )

        paired_for_director = [
            (candidate, candidate_quality_flags[idx] if idx < len(candidate_quality_flags) else {})
            for idx, candidate in enumerate(all_candidates)
            if candidate.get("tactical_doc")
        ]
        non_reject_pairs = [pair for pair in paired_for_director if not pair[1].get("force_reject")]
        if non_reject_pairs:
            paired_for_director = non_reject_pairs
        valid_for_director = [pair[0] for pair in paired_for_director]
        valid_quality_flags = [pair[1] for pair in paired_for_director]
        if not valid_for_director:
            return _FourPhaseDirectorSelectionEnvelope(
                best_arc=None,
                feedback=feedback,
                prev_rejected_arc=prev_rejected_arc,
                prev_reject_feedback=prev_reject_feedback,
                prev_selected_strategy=prev_selected_strategy,
                spare_candidates=spare_candidates,
            )

        logging.info(f" [TF-47] Director Arc 비교 선택 ({len(valid_for_director)}개 후보)")
        try:
            director_advisory = ns3b_director_advisory
            if investment_director_advisory:
                director_advisory = (
                    f"{director_advisory}\n\n{investment_director_advisory}"
                    if director_advisory
                    else investment_director_advisory
                )
            director_result = director.compare_and_select_arc(
                candidates=valid_for_director,
                arc_no=arc_no,
                curr_block=curr_block,
                prev_arc_context=prev_arc_context,
                constraint_block=full_constraint_block,
                advisory=director_advisory,
                candidate_quality_flags=valid_quality_flags,
            )
            director_decision = director_result.get("decision", "REJECT")
            director_arc = director_result.get("selected_arc")

            if director_decision == "PASS" and director_arc:
                best_arc = director_arc
                current_strategy = (
                    best_arc.get("_ensemble_meta", {}).get("best_strategy")
                    or best_arc.get("_strategy", "unknown")
                )
                pipeline_result["phases"]["generate"] = {
                    "status": "complete",
                    "candidates_count": len(all_candidates),
                    "selected_strategy": current_strategy,
                }
                pipeline_result["phases"]["director_selection"] = {
                    "status": "pass",
                    "score": director_result.get("score", 0),
                    "selected_strategy": director_arc.get("_strategy", "?"),
                    "ns3b_advisory": bool(ns3b_director_advisory),
                    "investment_advisory": bool(investment_advisory),
                }
                owner.stats["phase2_complete"] += 1
                pipeline_result["final_verdict"] = "PASS"
                owner.stats["phase3_pass"] += 1
                logging.info(f"✅ [TF-47] Director PASS — Arc {arc_no}")
                return _FourPhaseDirectorSelectionEnvelope(
                    best_arc=best_arc,
                    feedback=feedback,
                    prev_rejected_arc=prev_rejected_arc,
                    prev_reject_feedback=prev_reject_feedback,
                    prev_selected_strategy=prev_selected_strategy,
                    spare_candidates=spare_candidates,
                    should_return=True,
                )

            if director_decision == "PASS_WITH_FIX" and director_arc:
                best_arc = director_arc
                current_strategy = (
                    best_arc.get("_ensemble_meta", {}).get("best_strategy")
                    or best_arc.get("_strategy", "unknown")
                )
                pipeline_result["phases"]["generate"] = {
                    "status": "complete",
                    "candidates_count": len(all_candidates),
                    "selected_strategy": current_strategy,
                }
                pipeline_result["phases"]["director_selection"] = {
                    "status": "pass_with_fix",
                    "score": director_result.get("score", 0),
                    "feedback": director_result.get("feedback", ""),
                    "fix_scope": director_result.get("fix_scope", "inplace"),
                    "ns3b_advisory": bool(ns3b_director_advisory),
                    "investment_advisory": bool(investment_advisory),
                }
                owner.stats["phase2_complete"] += 1
                pipeline_result["final_verdict"] = "PASS"
                owner.stats["phase3_pass"] += 1
                logging.info(f"✅ [TF-47] Director PASS_WITH_FIX — Arc {arc_no}")
                return _FourPhaseDirectorSelectionEnvelope(
                    best_arc=best_arc,
                    feedback=feedback,
                    prev_rejected_arc=prev_rejected_arc,
                    prev_reject_feedback=prev_reject_feedback,
                    prev_selected_strategy=prev_selected_strategy,
                    spare_candidates=spare_candidates,
                    should_return=True,
                )

            best_arc = director_arc or valid_for_director[0]
            director_feedback = director_result.get("feedback", "Director REJECT")
            feedback = (
                f"{base_director_feedback}\n[Director 비교 피드백]\n{director_feedback}"
                if base_director_feedback
                else director_feedback
            )
            pipeline_result["phases"]["director_selection"] = {
                "status": "reject",
                "score": director_result.get("score", 0),
            }
            logging.warning(f"❌ [TF-47] Director REJECT — Arc {arc_no}, retry")
            prev_rejected_arc = best_arc
            prev_reject_feedback = feedback
            prev_selected_strategy = best_arc.get("_strategy", "unknown")
            spare_candidates = [candidate for candidate in valid_for_director if candidate is not prev_rejected_arc]
            return _FourPhaseDirectorSelectionEnvelope(
                best_arc=best_arc,
                feedback=feedback,
                prev_rejected_arc=prev_rejected_arc,
                prev_reject_feedback=prev_reject_feedback,
                prev_selected_strategy=prev_selected_strategy,
                spare_candidates=spare_candidates,
                should_continue=True,
            )
        except Exception as e:
            logging.warning(f"[TF-47] Director 비교 실패, fail-closed retry: {str(e)[:100]}")
            director_feedback = f"Director compare failed: {str(e)[:100]}"
            feedback = (
                f"{base_director_feedback}\n[Director compare failure]\n{director_feedback}"
                if base_director_feedback
                else director_feedback
            )
            pipeline_result["phases"]["director_selection"] = {
                "status": "error",
                "score": 0,
                "error": str(e)[:120],
            }
            return _FourPhaseDirectorSelectionEnvelope(
                best_arc=None,
                feedback=feedback,
                prev_rejected_arc=prev_rejected_arc,
                prev_reject_feedback=prev_reject_feedback,
                prev_selected_strategy=prev_selected_strategy,
                spare_candidates=spare_candidates,
                should_continue=True,
            )

    def _run_phase3_validation(
        self,
        *,
        arc_no: int,
        retry: int,
        max_internal_retries: int,
        curr_block: dict,
        best_arc: dict,
        all_candidates: list[dict],
        full_constraint_block: str,
        prev_arcs: list[dict],
        state_tracker,
        pre_items: set[str],
        pre_grants: set[str],
        feedback: str,
        base_director_feedback: str,
        investment_advisory: list[dict],
        prev_rejected_arc: dict | None,
        prev_reject_feedback: str,
        prev_selected_strategy: str,
        spare_candidates: list[dict],
        pipeline_result: dict,
    ) -> _FourPhaseValidationEnvelope:
        owner = self.owner

        best_arc = owner._check_arc_end_state(best_arc)
        ns3b_warning = _check_arc_vs_block_targets(best_arc, curr_block, arc_no)
        if ns3b_warning:
            logging.warning("[NS-3-B] %s", ns3b_warning)
            ns3b_header = f"[NS-3-B 수치 목표 괴리 경고]\n{ns3b_warning}"
            feedback = f"{ns3b_header}\n\n{feedback}" if feedback else ns3b_header

        if investment_advisory:
            investment_header = _format_investment_advisory(investment_advisory)
            feedback = f"{investment_header}\n\n{feedback}" if feedback else investment_header

        current_strategy = (
            best_arc.get("_ensemble_meta", {}).get("best_strategy")
            or best_arc.get("_strategy", "unknown")
        )
        pipeline_result["phases"]["generate"] = {
            "status": "complete",
            "candidates_count": len(all_candidates),
            "selected_strategy": current_strategy,
        }
        owner.stats["phase2_complete"] += 1

        logging.info(" [Phase 3] 통합 검증 중...")
        verdict, validation_result = owner.validator.validate(
            arc=best_arc,
            prev_arcs=prev_arcs,
            constraints=full_constraint_block,
            state_tracker=state_tracker,
            pre_collected_items=pre_items,
            pre_collected_grants=pre_grants,
            genre=owner._genre,
        )
        pipeline_result["phases"]["validate"] = {
            "status": "complete",
            "verdict": verdict,
            "issues_count": len(validation_result.get("issues", [])),
            "confidence": validation_result.get("confidence", 0),
        }

        if verdict == "PASS":
            owner.stats["phase3_pass"] += 1
            pipeline_result["final_verdict"] = "PASS"
            logging.info(f"✅ [Phase 3] PASS - Arc {arc_no} 생성 완료")
            confidence = validation_result.get("confidence", 0)
            all_issues = validation_result.get("issues", [])
            issue_count = len(all_issues)
            summary = validation_result.get("summary", "")
            major_issues = [issue for issue in all_issues if issue.get("severity") == "MAJOR"]
            logging.debug(
                "[Stage2 Validator] Arc %d PASS (confidence=%.2f, issues=%d) summary=%s",
                arc_no,
                confidence,
                issue_count,
                str(summary)[:300],
            )
            for major_issue in major_issues[:3]:
                logging.debug(" MAJOR 경고: %s", major_issue.get("issue", "?")[:120])
            return _FourPhaseValidationEnvelope(
                best_arc=best_arc,
                feedback=feedback,
                prev_rejected_arc=prev_rejected_arc,
                prev_reject_feedback=prev_reject_feedback,
                prev_selected_strategy=prev_selected_strategy,
                spare_candidates=spare_candidates,
                should_return=True,
            )

        owner.stats["phase3_reject"] += 1
        validator_feedback = validation_result.get("feedback", "검증 실패")
        feedback = (
            f"{base_director_feedback}\n[검증 피드백]\n{validator_feedback}"
            if base_director_feedback
            else validator_feedback
        )

        if best_arc:
            prev_rejected_arc = best_arc
            prev_reject_feedback = feedback
            prev_selected_strategy = current_strategy
            reject_confidence = validation_result.get("confidence", 0)
            if reject_confidence < 0.5:
                spare_candidates.clear()
                logging.info(f"[SpareCandidate] confidence={reject_confidence:.2f} < 0.5 → 차순위 전량 폐기")

        issues = validation_result.get("issues", [])
        logging.debug(
            "[Stage2 Validator] Arc %d REJECT (%d/%d) confidence=%.2f",
            arc_no,
            retry + 1,
            max_internal_retries + 1,
            validation_result.get("confidence", 0),
        )
        for issue in issues[:5]:
            logging.debug(
                " [%s][%s] %s",
                issue.get("severity", "?"),
                issue.get("category", "?"),
                issue.get("issue", "?")[:120],
            )
        logging.debug(" 피드백: %s", str(validator_feedback)[:200])
        if issues:
            first_issue = issues[0]
            owner.negative_injector.record_rejection(
                best_arc,
                first_issue.get("issue", "알 수 없음"),
                first_issue.get("category", "unknown"),
            )
            logging.warning(" [Phase 3] REJECT - 주요 이슈:")
            for issue in issues[:3]:
                severity = issue.get("severity", "?")
                category = issue.get("category", "?")
                text = issue.get("issue", "?")
                logging.info(f"[{severity}][{category}] {text}")

        logging.warning(f"❌ [Phase 3] REJECT - 재시도 {retry + 1}/{max_internal_retries + 1}")
        return _FourPhaseValidationEnvelope(
            best_arc=best_arc,
            feedback=feedback,
            prev_rejected_arc=prev_rejected_arc,
            prev_reject_feedback=prev_reject_feedback,
            prev_selected_strategy=prev_selected_strategy,
            spare_candidates=spare_candidates,
            should_continue=True,
        )

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
        owner = self.owner

        bootstrap = self._bootstrap_generation_state(
            arc_no=arc_no,
            curr_block=curr_block,
            prev_arcs=prev_arcs,
            director_feedback=director_feedback,
        )
        protagonist_config = bootstrap.protagonist_config
        ep_count_suggestion = bootstrap.ep_count_suggestion
        pacing_signals = bootstrap.pacing_signals
        pipeline_result = bootstrap.pipeline_result

        pre_items = bootstrap.pre_items
        pre_grants = bootstrap.pre_grants
        feedback = bootstrap.feedback
        base_director_feedback = bootstrap.base_director_feedback
        prev_rejected_arc = bootstrap.prev_rejected_arc
        prev_reject_feedback = bootstrap.prev_reject_feedback
        prev_selected_strategy = bootstrap.prev_selected_strategy
        spare_candidates = bootstrap.spare_candidates
        cached_constraint_block = None
        cached_preflight = None

        for retry in range(max_internal_retries + 1):
            pipeline_result["retries"] = retry

            # ═══════════════════════════════════════════════════════════════
            # PHASE 1: CONSTRAINT - 제약 수집
            # ═══════════════════════════════════════════════════════════════
            constraint_phase = self._resolve_constraint_phase(
                retry=retry,
                prev_arcs=prev_arcs,
                cached_constraint_block=cached_constraint_block,
                cached_preflight=cached_preflight,
                pipeline_result=pipeline_result,
            )
            full_constraint_block = constraint_phase.full_constraint_block
            preflight_result = constraint_phase.preflight_result
            cached_constraint_block = constraint_phase.cached_constraint_block
            cached_preflight = constraint_phase.cached_preflight

            # ═══════════════════════════════════════════════════════════════
            # PHASE 2: GENERATE - Ensemble 생성
            # ═══════════════════════════════════════════════════════════════
            generation_phase = self._run_generation_phase(
                retry=retry,
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
                protagonist_config=protagonist_config,
                ep_count_suggestion=ep_count_suggestion,
                pacing_signals=pacing_signals,
                full_constraint_block=full_constraint_block,
                preflight_result=preflight_result,
                feedback=feedback,
                base_director_feedback=base_director_feedback,
                prev_rejected_arc=prev_rejected_arc,
                prev_reject_feedback=prev_reject_feedback,
                prev_selected_strategy=prev_selected_strategy,
                spare_candidates=spare_candidates,
                pipeline_result=pipeline_result,
            )
            best_arc = generation_phase.best_arc
            all_candidates = generation_phase.all_candidates
            prev_arc_context = generation_phase.prev_arc_context
            feedback = generation_phase.feedback
            prev_rejected_arc = generation_phase.prev_rejected_arc
            prev_reject_feedback = generation_phase.prev_reject_feedback
            prev_selected_strategy = generation_phase.prev_selected_strategy
            spare_candidates = generation_phase.spare_candidates

            if generation_phase.patch_succeeded:
                return best_arc, pipeline_result
            if generation_phase.should_continue:
                continue

            candidate_phase = self._prepare_candidates_for_selection(
                arc_no=arc_no,
                curr_block=curr_block,
                prev_arcs=prev_arcs,
                all_candidates=all_candidates,
            )
            all_candidates = candidate_phase.all_candidates
            investment_advisory = candidate_phase.investment_advisory

            director_phase = self._run_director_selection_phase(
                director=director,
                arc_no=arc_no,
                curr_block=curr_block,
                prev_arc_context=prev_arc_context,
                full_constraint_block=full_constraint_block,
                all_candidates=all_candidates,
                candidate_quality_flags=candidate_phase.candidate_quality_flags,
                ns3b_director_advisory=candidate_phase.ns3b_director_advisory,
                investment_director_advisory=candidate_phase.investment_director_advisory,
                investment_advisory=investment_advisory,
                base_director_feedback=base_director_feedback,
                feedback=feedback,
                prev_rejected_arc=prev_rejected_arc,
                prev_reject_feedback=prev_reject_feedback,
                prev_selected_strategy=prev_selected_strategy,
                spare_candidates=spare_candidates,
                pipeline_result=pipeline_result,
            )
            best_arc = director_phase.best_arc
            feedback = director_phase.feedback
            prev_rejected_arc = director_phase.prev_rejected_arc
            prev_reject_feedback = director_phase.prev_reject_feedback
            prev_selected_strategy = director_phase.prev_selected_strategy
            spare_candidates = director_phase.spare_candidates
            if director_phase.should_return:
                return best_arc, pipeline_result
            if director_phase.should_continue:
                continue

            # Director 미사용/실패 시 1순위 후보 폴백
            if best_arc is None and all_candidates:
                best_arc = all_candidates[0]

            validation_phase = self._run_phase3_validation(
                arc_no=arc_no,
                retry=retry,
                max_internal_retries=max_internal_retries,
                curr_block=curr_block,
                best_arc=best_arc,
                all_candidates=all_candidates,
                full_constraint_block=full_constraint_block,
                prev_arcs=prev_arcs,
                state_tracker=state_tracker,
                pre_items=pre_items,
                pre_grants=pre_grants,
                feedback=feedback,
                base_director_feedback=base_director_feedback,
                investment_advisory=investment_advisory,
                prev_rejected_arc=prev_rejected_arc,
                prev_reject_feedback=prev_reject_feedback,
                prev_selected_strategy=prev_selected_strategy,
                spare_candidates=spare_candidates,
                pipeline_result=pipeline_result,
            )
            best_arc = validation_phase.best_arc
            feedback = validation_phase.feedback
            prev_rejected_arc = validation_phase.prev_rejected_arc
            prev_reject_feedback = validation_phase.prev_reject_feedback
            prev_selected_strategy = validation_phase.prev_selected_strategy
            spare_candidates = validation_phase.spare_candidates
            if validation_phase.should_return:
                return best_arc, pipeline_result
            if validation_phase.should_continue:
                continue

        # 모든 재시도 실패
        pipeline_result["final_verdict"] = "FAILED"
        logging.warning(f"❌ [ThreePhase] Arc {arc_no} 모든 재시도 실패 ({max_internal_retries + 1}회)")
        if feedback:
            logging.info(f"마지막 피드백: {feedback[:200]}...")
        return None, pipeline_result

