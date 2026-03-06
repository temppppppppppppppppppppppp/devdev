"""[B-1-7] Stage2 finalizer extracted from Stage2Orchestrator."""

import json
import logging
import re
import time

from modules.core.metrics_collector import get_metrics_collector
from modules.models.arc import validate_arc


def _to_num_with_korean_units(raw: object) -> float | None:
    """'23억', '1.2조', '+3만' 형식 텍스트 → float 변환."""
    if isinstance(raw, (int, float)):
        return float(raw)
    if not isinstance(raw, str):
        return None

    text = re.sub(r"\([^)]*\)", "", raw).strip()
    text = text.replace(",", "")
    if not text:
        return None

    sign = 1.0
    if text[0] in "+-":
        if text[0] == "-":
            sign = -1.0
        text = text[1:].strip()

    unit_map = (
        ("조", 1e12),
        ("억", 1e8),
        ("만", 1e4),
    )
    total = 0.0
    matched_unit = False

    for unit, mult in unit_map:
        value_pattern = rf"([0-9]+(?:\.[0-9]+)?)\s*{re.escape(unit)}"
        for value in re.findall(value_pattern, text):
            try:
                total += float(value) * mult
                matched_unit = True
            except ValueError:
                return None
        text = re.sub(value_pattern, "", text)

    if matched_unit:
        tail = re.search(r"([0-9]+(?:\.[0-9]+)?)", text)
        if tail:
            try:
                total += float(tail.group(1))
            except ValueError:
                return None
        return sign * total

    plain = re.search(r"([0-9]+(?:\.[0-9]+)?)", text)
    if not plain:
        return None
    try:
        return sign * float(plain.group(1))
    except ValueError:
        return None


def _relative_error(stated: float, actual: float) -> float:
    if actual == 0:
        return 0.0 if stated == 0 else float("inf")
    return abs(stated - actual) / abs(actual)


def _format_eok(value: float) -> str:
    return f"{value / 1e8:.1f}" + "억"


def _check_tactical_arithmetic(tactical_doc: str) -> list[str]:
    """
    [NS-1-P] Verify arithmetic claims in tactical_doc with pure Python checks.
    Returns warning strings when mismatch is over 5%.
    """
    if not tactical_doc:
        return []

    tolerance = 0.05
    issues: list[str] = []

    num_with_unit = r"[\d,]+(?:\.[\d]+)?(?:조|억|만)?"
    mul_op = r"(?:[xX×*]|곱)"
    eq_op = r"(?:=|는|은|:)"
    bae = "배"

    mult_pattern = re.compile(
        rf"(?P<a>{num_with_unit})\s*{mul_op}\s*"
        rf"(?P<n>[\d,]+(?:\.[\d]+)?)\s*{bae}?\s*{eq_op}\s*"
        rf"(?P<c>{num_with_unit})"
    )
    pct_pattern = re.compile(
        rf"(?P<a>{num_with_unit})\s*{mul_op}\s*"
        rf"(?P<p>[\d,]+(?:\.[\d]+)?)%\s*{eq_op}\s*"
        rf"(?P<c>{num_with_unit})"
    )

    for match in mult_pattern.finditer(tactical_doc):
        a = _to_num_with_korean_units(match.group("a"))
        n = _to_num_with_korean_units(match.group("n"))
        stated = _to_num_with_korean_units(match.group("c"))
        if None in (a, n, stated):
            continue
        actual = a * n
        if _relative_error(stated, actual) > tolerance:
            issues.append(
                f"Arithmetic mismatch: {match.group(0).strip()} "
                f"(stated={match.group('c')}, actual={_format_eok(actual)})"
            )

    for match in pct_pattern.finditer(tactical_doc):
        a = _to_num_with_korean_units(match.group("a"))
        pct = _to_num_with_korean_units(match.group("p"))
        stated = _to_num_with_korean_units(match.group("c"))
        if None in (a, pct, stated):
            continue
        actual = a * (pct / 100.0)
        if _relative_error(stated, actual) > tolerance:
            issues.append(
                f"Arithmetic mismatch: {match.group(0).strip()} "
                f"(stated={match.group('c')}, actual={_format_eok(actual)})"
            )

    return issues


def _check_cross_arc_asset_continuity(tactical_doc: str, prev_arcs: list) -> list[str]:
    """[TF-57-C] 직전 Arc 자산 수치 → 현재 Arc 첫 에피소드 자산 연속성 advisory.

    직전 Arc arc_end_state 또는 tactical_doc 종료 상태에서 총자산 수치를 추출하고
    현재 tactical_doc에서 언급된 첫 자산 수치와 ±20% 이상 차이 시 advisory 반환.
    advisory-only — REJECT 강제 없음.
    """
    if not tactical_doc or not prev_arcs:
        return []

    import re as _re57c

    _asset_re = _re57c.compile(r"총자산\s*약?\s*(\d[\d.,]*)\s*억")

    # 직전 Arc 자산 추출 (arc_end_state 우선, tactical_doc 폴백)
    prev_arc = prev_arcs[-1]
    prev_asset: float | None = None

    _prev_end = prev_arc.get("state_constraints", {}).get("arc_end_state", {})
    for _key in ("total_assets", "asset", "assets"):
        _val = _prev_end.get(_key)
        if isinstance(_val, int | float) and _val > 0:
            prev_asset = float(_val)
            break

    if prev_asset is None:
        _prev_td = prev_arc.get("tactical_doc", "")
        _prev_matches = _asset_re.findall(_prev_td)  # 마지막 언급 = [-1]
        if _prev_matches:
            try:
                prev_asset = float(_prev_matches[-1].replace(",", "")) * 1e8
            except ValueError:
                pass

    if prev_asset is None or prev_asset <= 0:
        return []

    # 현재 Arc 첫 자산 언급 추출
    _curr_m = _asset_re.search(tactical_doc[:2000])  # 첫 2000자
    if not _curr_m:
        return []

    try:
        curr_asset = float(_curr_m.group(1).replace(",", "")) * 1e8
    except ValueError:
        return []

    if curr_asset <= 0:
        return []

    delta_pct = abs(curr_asset - prev_asset) / prev_asset
    if delta_pct > 0.20:
        return [
            f"[TF-57-C 자산 연속성 advisory] 직전 Arc 종료 자산 {prev_asset/1e8:.1f}억 대비 "
            f"현재 Arc 첫 언급 자산 {curr_asset/1e8:.1f}억 — {delta_pct*100:.0f}% 차이 (허용 20% 초과). "
            "직전 Arc 계산과 정합하는지 확인하세요."
        ]
    return []


def _check_block_worldstate_alignment(
    enriched_block: dict,
    refined_arc: dict,
    arc_no: int,
    threshold_pct: float = 0.30,
) -> list[str]:
    """
    [NS-2] Compare treatment block goal numbers with arc_end_state values.
    Advisory-only warning (no forced reject).
    """
    warnings: list[str] = []

    if not isinstance(enriched_block, dict) or not isinstance(refined_arc, dict):
        return warnings

    genre_ext = enriched_block.get("genre_ext")
    if not isinstance(genre_ext, dict):
        return warnings

    state_constraints = refined_arc.get("state_constraints")
    if not isinstance(state_constraints, dict):
        return warnings

    arc_end_state = state_constraints.get("arc_end_state")
    if not isinstance(arc_end_state, dict):
        return warnings

    target_capital = _to_num_with_korean_units(genre_ext.get("capital_after"))
    if target_capital in (None, 0):
        return warnings

    actual_capital = None
    actual_key = None
    for key in ("total_assets", "assets", "capital", "total_capital"):
        value = _to_num_with_korean_units(arc_end_state.get(key))
        if value is not None:
            actual_capital = value
            actual_key = key
            break

    if actual_capital is None:
        return warnings

    divergence = abs(target_capital - actual_capital) / abs(target_capital)
    if divergence > threshold_pct:
        warnings.append(
            f"[NS-2] Arc {arc_no} capital divergence: "
            f"target={genre_ext.get('capital_after')} vs arc_end_state.{actual_key}={_format_eok(actual_capital)} "
            f"(delta={divergence * 100:.0f}%)"
        )

    return warnings


class Stage2Finalizer:
    """Director audit + PASS/REJECT post-processing for Stage 2."""

    def __init__(self, host) -> None:
        self.host = host

    @property
    def ctx(self):
        return self.host.ctx

    async def run_finalize(
        self,
        *,
        refined_arc: dict,
        enriched_block: dict,
        arc_drive: dict,
        all_refined_arcs: list,
        global_arc_no: int,
        current_ep_start: int,
        current_feedback: str,
        protagonist_name: str,
        suspected_duplicates: list,
        entity_registry_for_director,
        constraint_block: str,
        draft_validator_passed: bool,
        consensus_passed: bool,
        attempt: int,
        generation_method: str,
        st_snapshot,
        director_feedback_for_fourphase: str,
        last_refined_context: str,
        bible_root: dict,
        genre: str,
        constraint_db,
        is_patch: bool = False,
        prev_score: float = 0.0,
        patch_fallback: bool = False,
    ) -> dict:
        """[4-R3-e] Director audit and post-audit finalize.

        Handles SemanticPlotGuard, Director context/audit,
        PASS finalization (DB save, metrics, volume summary),
        and REJECT handling (rollback, feedback).

        Returns dict with action='break'|'retry'|'next'.
        """
        from modules.core.constants import ContextLimits, RecoveryLimits

        # [V66] SemanticPlotGuard 중복 검사
        if self.ctx.semantic_plot_guard:
            try:
                tactical_text = refined_arc.get("tactical_doc", "")
                if isinstance(tactical_text, dict):
                    tactical_text = str(tactical_text)
                spg_warnings = self.ctx.semantic_plot_guard.check_new_arc(tactical_doc=tactical_text)
                if spg_warnings:
                    spg_text = self.ctx.semantic_plot_guard.format_warnings(spg_warnings)
                    logging.warning(f"⚠️ [V66] {spg_text}")
                    # Director 피드백에 추가
                    if current_feedback:
                        current_feedback = f"{current_feedback}\n{spg_text}"
                    else:
                        current_feedback = spg_text
            except (AttributeError, TypeError, RuntimeError) as e:
                logging.warning(f"⚠️ [V64.P4-fix] 플롯 중복 감지 실패: {e}")

        # [V65] PerfTimer: Director 대면 측정
        _director_duration_ms = None
        _director_t0 = time.monotonic()
        try:
            self.ctx.perf_timer.start(f"s2_arc_{global_arc_no}_director")
        except (AttributeError, TypeError) as e:
            logging.debug(f"[PerfTimer] start s2 director: {e}")

        # [V67] Director 컨텍스트 확장: 이전 30개 Arc tactical_doc 전문 전달
        _expanded_prev_context = last_refined_context
        if all_refined_arcs:
            _prev_arc_docs = []
            _prev_start = max(0, len(all_refined_arcs) - 30)
            for _pa_idx in range(_prev_start, len(all_refined_arcs)):
                _pa = all_refined_arcs[_pa_idx]
                _pa_no = _pa.get("arc_no", _pa_idx + 1)
                _pa_td = _pa.get("tactical_doc", "")
                if isinstance(_pa_td, dict):
                    _pa_td = json.dumps(_pa_td, ensure_ascii=False)
                if _pa_td:
                    _pa_ep_s = _pa.get("ep_start", "?")
                    _pa_ep_e = _pa.get("ep_end", "?")
                    _prev_arc_docs.append(f"━━━ Arc {_pa_no} (제{_pa_ep_s}화~제{_pa_ep_e}화) ━━━\n{_pa_td}")
            if _prev_arc_docs:
                _full_arc_history = "\n\n".join(_prev_arc_docs)
                # 1M자 상한 (ContextLimits.MAX_CONTEXT_CHARS)
                if len(_full_arc_history) > ContextLimits.MAX_CONTEXT_CHARS:
                    _full_arc_history = _full_arc_history[: ContextLimits.MAX_CONTEXT_CHARS] + "\n... (1M자 절삭)"
                _expanded_prev_context = (
                    f"[V67] ═══ 이전 Arc 전술서 전문 ({len(_prev_arc_docs)}개) ═══\n"
                    f"{_full_arc_history}\n\n"
                    f"═══ 상태 요약 ═══\n{last_refined_context}"
                )
                logging.info(
                    f"📚 [V67] Director 컨텍스트 확장: {len(_prev_arc_docs)}개 Arc ({len(_expanded_prev_context)}자)"
                )

        # [V67.1] story_context 조립
        _story_context = ""
        try:
            _prot_config = bible_root.get("protagonist_config", {})
            _sc_parts = [f"- 장르: {genre}"]
            if _prot_config:
                _sc_parts.append(f"- 주인공: {_prot_config.get('name', protagonist_name or '미상')}")
                _incarnation = _prot_config.get("incarnation_type", "미상")
                _sc_parts.append(f"- 환생 유형: {_incarnation}")
                if _incarnation == "회귀자":
                    _sc_parts.append("→ 회귀자: 미래를 알고 역사를 변경하려 함. 이것은 모순이 아님.")
                elif _incarnation == "빙의자":
                    _sc_parts.append("→ 빙의자: 원래 인물과 다른 인격.")
                elif _incarnation == "환생자":
                    _sc_parts.append("→ 환생자: 전생 기억 보유.")
            _story_context = "\n".join(_sc_parts)
        except (KeyError, TypeError, AttributeError) as e:
            logging.warning(f"[SilentPass:Stage2Finalizer] 스토리 컨텍스트 생성 실패: {e!s:.100}")
            _story_context = ""

        # [TF-25-09] ArcAutoCorrector 수정 내역을 Director advisory로 주입
        if constraint_block and "[Python 자동 수정" in constraint_block:
            _corr_start = constraint_block.find("[Python 자동 수정")
            _corr_end = constraint_block.find("\n\n[Python Pre-Director advisory", _corr_start)
            _corr_advisory = (
                constraint_block[_corr_start:_corr_end] if _corr_end > 0 else constraint_block[_corr_start:]
            )
            _story_context += f"\n\n⚠️ {_corr_advisory}"

        # [TF-25-08] Python Pre-Director advisory를 Director 컨텍스트에 주입
        if constraint_block and "[Python Pre-Director advisory" in constraint_block:
            _adv_start = constraint_block.find("[Python Pre-Director advisory")
            _adv_text = constraint_block[_adv_start:]
            _story_context += f"\n\n⚠️ {_adv_text}"

        # [TF-57-C] 크로스-Arc 자산 연속성 advisory
        _tactical_doc = refined_arc.get("tactical_doc", "") if isinstance(refined_arc, dict) else ""
        _cross_arc_issues = _check_cross_arc_asset_continuity(_tactical_doc, all_refined_arcs)
        if _cross_arc_issues:
            _story_context += "\n\n" + "\n".join(_cross_arc_issues)
            logging.info("[TF-57-C] 크로스-Arc 자산 연속성 advisory 주입: %d건", len(_cross_arc_issues))

        self.ctx.ui.log("      🤔 [TF-38] Director 전략적 무결성 검수 중...")
        print("      🤔 [Director] 전략적 무결성 검수 중 (LLM 호출, 1~3분 소요)...")
        # [G7] Director 심사 호출 크래시 방어
        try:
            audit = self.ctx.agents["director"].audit_strategic_plan(
                refined_arc,
                _expanded_prev_context,
                curr_block=enriched_block,
                protagonist_name=protagonist_name,
                suspected_duplicates=suspected_duplicates,
                entity_registry=entity_registry_for_director,
                story_context=_story_context,  # [V67.1]
            )
        except (RuntimeError, OSError, ValueError) as _dir_err:
            logging.warning(f"[G7] Director 심사 호출 실패: {_dir_err!s:.100}")
            self.ctx.ui.log("      ⚠️ [Director] 심사 호출 실패 — 폴백 REJECT")
            audit = {
                "decision": "REJECT",
                "score": 50,
                "reason": "Director 호출 실패 — 폴백 REJECT",
                "self_consistency": {},
            }
        try:
            _elapsed = self.ctx.perf_timer.stop(f"s2_arc_{global_arc_no}_director")
            if _elapsed and _elapsed > 0:
                _director_duration_ms = max(0, int(_elapsed * 1000))
        except (AttributeError, TypeError) as e:
            logging.debug(f"[PerfTimer] stop s2 director: {e}")
        if _director_duration_ms is None:
            _director_duration_ms = max(0, int((time.monotonic() - _director_t0) * 1000))

        # Director 심사 결과 사용자 출력
        _d_decision = audit.get("decision", "?")
        _d_score = audit.get("score", "?")
        _d_reason = audit.get("reason", "")
        _d_status = "✅" if _d_decision in ("PASS", "PASS_WITH_FIX") else "❌"
        print(f"      {_d_status} [Director] {_d_decision} (score={_d_score})")
        self.ctx.ui.log(f"\n      🎬 [Director] {_d_decision} (score={_d_score})")
        if _d_reason:
            for _i in range(0, len(str(_d_reason)), 80):
                self.ctx.ui.log(f"         {str(_d_reason)[_i : _i + 80]}")
        _d_contradictions = audit.get("contradictions", [])
        if _d_contradictions and not isinstance(_d_contradictions, list):
            _d_contradictions = [_d_contradictions] if _d_contradictions else []
        if _d_contradictions:
            self.ctx.ui.log(f"         📌 모순 {len(_d_contradictions)}건:")
            for _c in _d_contradictions[:5]:
                self.ctx.ui.log(f"            ▸ {str(_c)[:120]}")
        if _d_decision == "REJECT" and audit.get("re_slice_instruction"):
            self.ctx.ui.log(f"         🔧 수정지시: {str(audit['re_slice_instruction'])[:150]}")
        # [TF-28c] Director thinking 표시 (절삭 없음)
        _d_thinking = audit.get("_director_thinking", "")
        if _d_thinking:
            self.ctx.ui.log("      💭 [Director Thinking]")
            self.ctx.ui.log(_d_thinking)

        # ═══════════════════════════════════════════════════════════════
        # [TF-25-07] V60.43 API 할당량 오류 감지 — 경고만 (대원칙 1+3 준수)
        # Python은 판정을 변경하지 않음. Director REJECT 유지 → 오케스트레이터 재시도 루프가 처리.
        # ═══════════════════════════════════════════════════════════════
        if audit.get("decision") == "REJECT" and draft_validator_passed and consensus_passed:
            self_consistency = audit.get("self_consistency", {})
            scores = self_consistency.get("scores", [])
            all_default_50 = len(scores) >= 2 and all(s == 50 for s in scores)
            zero_count = sum(1 for s in scores if s == 0)
            many_zeros = len(scores) >= 2 and zero_count >= len(scores) // 2
            is_quota_failure = all_default_50 or many_zeros

            if is_quota_failure:
                logging.warning(
                    "[TF-25-07] V60.43 API 쿼터 실패 패턴 감지 — Director REJECT 유지 (score=0이 %d/%d개)",
                    zero_count,
                    len(scores),
                )
                audit["v60_43_api_warning"] = True

        from modules.validation.threshold_helper import _threshold

        _quality_gate_score = _threshold("scoring.quality_gate_score", 90)
        _score_raw = audit.get("score", 0)
        try:
            _score = int(_score_raw)
        except (ValueError, TypeError):
            _score = 0

        _td = refined_arc.get("tactical_doc", "")
        _td_len = len(str(_td)) if isinstance(_td, dict) else len(_td or "")

        # [LOG-1] 판정 경로 세션 로깅
        _sl = getattr(self.ctx, "session_logger", None)
        if _sl:
            try:
                _sl.log_decision(
                    stage="stage2",
                    ep_num=global_arc_no,
                    round_num=attempt,
                    decision_type="arc",
                    result=audit.get("decision", "UNKNOWN"),
                    score=_score,
                    generation_method=generation_method,
                    reason=str(audit.get("reason", ""))[:500],
                )
            except (AttributeError, TypeError) as _e:
                logging.debug("[SilentPass:S2:SessionLog] %s", _e)

        # [TF-32-VERIFY] PASS_WITH_FIX → patch + Director 재심사 반복 (최대 3회)
        _d_decision = audit.get("decision", "")
        if _d_decision == "PASS_WITH_FIX":
            # [TF-46] PASS_WITH_FIX는 Director 주권 존중 — QualityGate 미적용, 바로 patch loop 진입
            _MAX_FIX = 3
            _four_phase = self.ctx.agents.get("four_phase")
            _current_arc = dict(refined_arc)
            _current_audit = audit
            _fix_ok = False
            _applied_patches: list[str] = []

            for _fix_i in range(_MAX_FIX):
                # [TF-33][PF-1] Director fix_scope 기반 수정 전략 라우팅 — 누락 시 점수 기반 폴백
                _fix_scope = _current_audit.get("fix_scope", "")
                if not _fix_scope:
                    _inplace_thresh = int(_threshold("patch_mode.inplace_below", 60))
                    _fix_scope = "inplace" if _score >= _inplace_thresh else "full"
                    logging.warning("[PF-1] fix_scope 누락 → score=%d fallback: %s", _score, _fix_scope)
                if _fix_scope in ("partial", "full"):
                    self.ctx.ui.log(f"      🔀 [TF-33] fix_scope={_fix_scope!r} → inplace 불가, retry 경로 위임")
                    break  # → REJECT → retry 경로에서 patch/rewrite 처리

                _fix_instr = _current_audit.get("re_slice_instruction", "")
                self.ctx.ui.log(
                    f"      🔧 [TF-32-V] PASS_WITH_FIX patch #{_fix_i + 1}/{_MAX_FIX} (fix: {str(_fix_instr)[:80]})"
                )

                if not (_four_phase and hasattr(_four_phase, "_inplace_patch_arc")):
                    logging.warning("[TF-32-V] four_phase 에이전트 미등록 → REJECT")
                    break

                try:
                    _patched = _four_phase._inplace_patch_arc(
                        original_arc=_current_arc,
                        director_feedback=_fix_instr,
                        arc_no=global_arc_no,
                    )
                except (RuntimeError, ValueError, OSError):
                    logging.exception("[TF-32-V] inplace_patch_arc 예외")
                    break
                if not _patched:
                    logging.warning("[TF-32-V] patch 실패 → REJECT")
                    break

                # [NS-1-P] Detect arithmetic mismatch in inplace tactical_doc patch.
                _arith_patch_ctx = ""
                _tactical_patched = _patched.get("tactical_doc", "") if isinstance(_patched, dict) else ""
                if _tactical_patched:
                    _arith_issues = _check_tactical_arithmetic(str(_tactical_patched))
                    if _arith_issues:
                        _arith_warn = "\n".join(f"  - {item}" for item in _arith_issues)
                        logging.warning("[NS-1-P] arithmetic warning detected in inplace patch:\n%s", _arith_warn)
                        _arith_patch_ctx = (
                            "\n\n[NS-1-P arithmetic warning in inplace patch]\n"
                            f"{_arith_warn}\n"
                            "Please verify the patched tactical_doc arithmetic before approving."
                        )

                # [F-2] InPlace Arc 변경 비율 로깅
                try:
                    from modules.core.constants import calc_patch_change_ratio

                    _orig_j = json.dumps(_current_arc, ensure_ascii=False)
                    _patch_j = json.dumps(_patched, ensure_ascii=False)
                    _change_ratio = calc_patch_change_ratio(_orig_j, _patch_j)
                    _max_ratio = float(_threshold("patch_mode.inplace_max_change_ratio", 0.30))
                    if _change_ratio > _max_ratio:
                        logging.warning(
                            "[F-2] InPlace Arc 변경 비율 %.1f%% > %.0f%% (S2)",
                            _change_ratio * 100,
                            _max_ratio * 100,
                        )
                except Exception as _e:
                    logging.debug("[S2-Finalizer] change_ratio 계산 실패: %s", _e)

                # [PWF-S2] 패치 이력 적적 — Director 재심사 컨텍스트에 주입
                if _fix_instr:
                    _applied_patches.append(str(_fix_instr)[:200])

                # Director 재심사 (동일 메서드)
                self.ctx.ui.log(f"      🔄 [TF-38] Director 재심사 #{_fix_i + 1} 호출 중...")
                # [PWF-S2] 재심사에 이미 적용된 패치를 story_context에 주입
                # → curr_block 문서로 인한 동일 오류 재감지 가능성 최소화
                _patch_ctx = _arith_patch_ctx
                if _applied_patches:
                    _patch_lines = "\n".join(f"- {p}" for p in _applied_patches)
                    _patch_ctx += (
                        "\n\n[PASS_WITH_FIX 재심사 — 이미 적용된 패치]\n"
                        f"{_patch_lines}\n"
                        "위 항목은 tactical_doc에 이미 반영되었습니다. "
                        "curr_block 문서에서 동일 오류가 보여도 tactical_doc에서 수정되었으면 승인하세요."
                    )
                try:
                    _re_audit = self.ctx.agents["director"].audit_strategic_plan(
                        _patched,
                        _expanded_prev_context,
                        curr_block=enriched_block,
                        protagonist_name=protagonist_name,
                        suspected_duplicates=suspected_duplicates,
                        entity_registry=entity_registry_for_director,
                        story_context=(_story_context or "") + _patch_ctx,
                    )
                except (RuntimeError, ValueError, OSError):
                    logging.exception("[TF-32-V] 재심사 예외")
                    break

                _re_d = _re_audit.get("decision", "REJECT")
                _re_s = _re_audit.get("score", 0)
                try:
                    _re_s = int(_re_s)
                except (ValueError, TypeError):
                    _re_s = 0
                self.ctx.ui.log(f"      🎬 [TF-32-V] 재심사 #{_fix_i + 1}: {_re_d} (score={_re_s})")

                if _re_d == "PASS":
                    if _re_s < _quality_gate_score:
                        self.ctx.ui.log(
                            f"      ⚠️ [TF-35] 재심사 PASS이나 score={_re_s} < {_quality_gate_score} → patch 종료"
                        )
                        break
                    _current_arc = _patched
                    _fix_ok = True
                    break
                elif _re_d == "PASS_WITH_FIX":
                    _current_arc = _patched
                    _current_audit = _re_audit  # 다음 반복
                else:  # REJECT
                    break

            if _fix_ok:
                refined_arc.clear()
                refined_arc.update(_current_arc)
                _d_decision = "PASS"
                _score = _re_s  # [TF-46] 재심사 점수로 갱신 (stale score → QualityGate 오작동 방지)
                self.ctx.ui.log("      ✅ [TF-32-V] Arc 수정 완료 → PASS 확정")
            else:
                _d_decision = "REJECT"
                audit["decision"] = "REJECT"
                # [PF-3] PASS_WITH_FIX 소진 시에만 패치본 채택 — 디렉터 주권주의
                _last_decision = _current_audit.get("decision", "")
                if _last_decision == "PASS_WITH_FIX" and _current_arc != dict(refined_arc):
                    refined_arc.clear()
                    refined_arc.update(_current_arc)
                    _pf3_score = _current_audit.get("score", _score)
                    try:
                        _pf3_score = int(_pf3_score)
                    except (ValueError, TypeError):
                        _pf3_score = _score
                    audit["score"] = _pf3_score
                    self.ctx.ui.log(f"      📈 [PF-3] PASS_WITH_FIX 소진 → 패치본 채택 (score={_pf3_score})")
                # [TF-33] Director fix_scope + reasoning 보존 → retry 경로에서 patch/rewrite 라우팅
                _last_fix_scope = _current_audit.get("fix_scope", "")
                if _last_fix_scope:
                    audit["fix_scope"] = _last_fix_scope
                _last_fsr = _current_audit.get("fix_scope_reasoning", "")
                if _last_fsr:
                    audit["fix_scope_reasoning"] = _last_fsr
                audit["reason"] = (audit.get("reason", "") or "") + (
                    f"\n[TF-32-V] PASS_WITH_FIX 수정 {_MAX_FIX}회 내 미해결 → REJECT"
                )
                audit["re_slice_instruction"] = audit.get("re_slice_instruction") or "지적사항 미해결 — 재설계 필요"
                self.ctx.ui.log("      ❌ [TF-32-V] 수정 실패 → REJECT 전환")

        if _d_decision in ("PASS", "PASS_WITH_FIX"):  # [TF-R4-S2-01] [TF-32-S2] PASS/PASS_WITH_FIX 수용
            if _d_decision == "PASS" and _td_len >= 1500 and _score < _quality_gate_score:  # [TF-46] PASS만 gate 적용
                self.ctx.ui.log(
                    f"      ⚠️ [QualityGate] PASS 판정이나 score={_score} < {_quality_gate_score} → REJECT 전환"
                )
                audit["decision"] = "REJECT"
                audit["reason"] = (audit.get("reason") or "") + (
                    f"\n[Quality Gate] score {_score}점으로 {_quality_gate_score}점 미달."
                )
                audit["re_slice_instruction"] = audit.get("re_slice_instruction") or "품질 개선 후 재제출"
                # [TF-30-4] QualityGate REJECT 사유를 FourPhase 재시도에 전달
                director_feedback_for_fourphase = (
                    f"[QualityGate REJECT] score {_score}점 < {_quality_gate_score}점.\n"
                    f"{audit.get('reason', '')}\n"
                    f"[수정 지시] {audit.get('re_slice_instruction', '품질 개선 후 재제출')}"
                )
                # [P1-B1] StateTracker 롤백 — FourPhase PASS 후 팬텀 데이터 방지
                if st_snapshot and generation_method.startswith("four_phase"):
                    _st = self.ctx.state_tracker
                    if _st:
                        for _k, _v in st_snapshot.items():
                            if hasattr(_st, _k):
                                setattr(_st, _k, _v)
                # [E5a-P1-1] QualityGate REJECT — reject metrics 기록
                self._record_s2_reject_metrics(
                    global_arc_no=global_arc_no,
                    attempt=attempt,
                    generation_method=generation_method,
                    audit=audit,
                    is_patch=is_patch,
                    prev_score=prev_score,
                    patch_fallback=patch_fallback,
                )
                return {
                    "action": "retry",
                    "current_feedback": audit["reason"],
                    "score": _score,
                    "rejected_arc": refined_arc,
                    "score_breakdown": {},
                    "director_feedback_for_fourphase": director_feedback_for_fourphase,
                    "fix_scope": audit.get("fix_scope", ""),  # [TF-23] Director 판단 수정 범위
                }

            ### [0124 핵심 3] 욕망 데이터 및 HUD 그림자 물리적 박제
            refined_arc["arc_drive"] = arc_drive if arc_drive else {}
            refined_arc["joint_docs"] = enriched_block.get("joint_docs", {})
            refined_arc["status_shadow"] = enriched_block.get("status_shadow", {})

            critical_missing = []
            if not refined_arc.get("hybrid_composition"):
                self.ctx.ui.log(f"⚠️ [Arc {global_arc_no}] 패턴 구성(hybrid_composition) 누락 - 기본값 주입")
                if callable(getattr(self.ctx, "audit_event", None)):
                    self.ctx.audit_event("data_missing", "hybrid_composition missing", {"arc_no": global_arc_no})
                refined_arc["hybrid_composition"] = {
                    "primary": "standard_progression",
                    "secondary": [],
                    "mixing_logic": "기본 전개",
                }
                critical_missing.append("hybrid_composition")

            if not refined_arc.get("joint_docs"):
                self.ctx.ui.log(f"⚠️ [Arc {global_arc_no}] joint_docs 누락 - 기본값 주입")
                if callable(getattr(self.ctx, "audit_event", None)):
                    self.ctx.audit_event("data_missing", "joint_docs missing", {"arc_no": global_arc_no})
                refined_arc["joint_docs"] = {
                    "final_location": "위치 미정",
                    "physical_inventory": ["물품 미정"],
                    "world_joint": "변화 없음",
                }
                critical_missing.append("joint_docs")

            # [V49.6 NEW] physical_inventory 계승
            curr_joint = refined_arc.get("joint_docs", {})
            curr_inventory = curr_joint.get("physical_inventory", [])
            # [B3-P1-2] physical_inventory 타입 정규화 (str|dict → list)
            if isinstance(curr_inventory, str):
                curr_inventory = [curr_inventory] if curr_inventory and curr_inventory != "[]" else []
            elif isinstance(curr_inventory, dict):
                curr_inventory = [curr_inventory] if curr_inventory else []
            if not curr_inventory:
                if all_refined_arcs:
                    prev_joint = all_refined_arcs[-1].get("joint_docs", {})
                    prev_inventory = prev_joint.get("physical_inventory", [])
                    # [TF-R3-S2-02] 문자열 직렬화된 인벤토리 → 리스트 변환
                    if isinstance(prev_inventory, str):
                        try:
                            import json as _json

                            prev_inventory = _json.loads(prev_inventory)
                        except (ValueError, TypeError):
                            prev_inventory = []
                    # [B3-P1-2] prev_inventory도 dict일 수 있음 → list 정규화
                    if isinstance(prev_inventory, dict):
                        prev_inventory = [prev_inventory] if prev_inventory else []
                    if prev_inventory and prev_inventory != [] and prev_inventory != "[]":
                        curr_status = refined_arc.get("status_shadow", {})
                        consumed_raw = curr_status.get("item_consumption", [])
                        if isinstance(consumed_raw, str):
                            consumed_names = [consumed_raw] if consumed_raw else []
                        elif isinstance(consumed_raw, list):
                            consumed_names = []
                            for consumed_item in consumed_raw:
                                if isinstance(consumed_item, str):
                                    consumed_names.append(consumed_item)
                                elif isinstance(consumed_item, dict):
                                    consumed_names.append(consumed_item.get("name", consumed_item.get("item", "")))
                        else:
                            consumed_names = []
                        state_constraints = refined_arc.get("state_constraints", {})
                        acquired = state_constraints.get("items_acquired", [])
                        if isinstance(acquired, str):
                            acquired = [acquired] if acquired else []
                        elif not isinstance(acquired, list):
                            # [TF-R3-S2-03] dict 등 비-리스트 타입 방어
                            acquired = [acquired] if acquired else []
                        if isinstance(prev_inventory, list):
                            # [Sweep45] dict 아이템도 consumed 비교 가능하도록 이름 추출
                            def _item_name(it):
                                if isinstance(it, dict):
                                    return it.get("name", it.get("item", ""))
                                return str(it)

                            inherited = [item for item in prev_inventory if _item_name(item) not in consumed_names]
                            inherited.extend(acquired)
                            refined_arc["joint_docs"]["physical_inventory"] = inherited
                            self.ctx.ui.log(
                                f"      🔄 [V49.6] physical_inventory 이전 Arc에서 계승: {inherited[:3]}{'...' if len(inherited) > 3 else ''}"
                            )

            if not refined_arc.get("status_shadow"):
                self.ctx.ui.log(f"⚠️ [Arc {global_arc_no}] status_shadow 누락 - 기본값 주입")
                if callable(getattr(self.ctx, "audit_event", None)):
                    self.ctx.audit_event("data_missing", "status_shadow missing", {"arc_no": global_arc_no})
                refined_arc["status_shadow"] = {
                    "internal_energy_loss": "0%",
                    "expected_injuries": "없음",
                    "item_consumption": [],
                }
                critical_missing.append("status_shadow")

            if len(critical_missing) >= RecoveryLimits.CRITICAL_MISSING_THRESHOLD:
                self.ctx.ui.log(f"🚨 [Arc {global_arc_no}] 핵심 데이터 과다 누락({len(critical_missing)}개)")
                current_feedback = f"필수 키 누락: {', '.join(critical_missing)}. 완전한 JSON 구조로 재설계하라."
                refined_arc = None
                # [P1-B1] StateTracker 롤백
                if st_snapshot and generation_method.startswith("four_phase") and self.ctx.state_tracker:
                    for _k, _v in st_snapshot.items():
                        if hasattr(self.ctx.state_tracker, _k):
                            setattr(self.ctx.state_tracker, _k, _v)
                return {"action": "retry", "current_feedback": current_feedback}

            if callable(getattr(self.ctx, "validate_arc_integrity", None)) and not self.ctx.validate_arc_integrity(
                refined_arc
            ):
                current_feedback = "필수 키가 누락된 전술 설계입니다. 형식을 완전한 JSON으로 다시 출력하십시오."
                refined_arc = None
                # [P1-B1] StateTracker 롤백
                if st_snapshot and generation_method.startswith("four_phase") and self.ctx.state_tracker:
                    for _k, _v in st_snapshot.items():
                        if hasattr(self.ctx.state_tracker, _k):
                            setattr(self.ctx.state_tracker, _k, _v)
                return {"action": "retry", "current_feedback": current_feedback}

            # [TF-S2-03] 중복 check_new_arc() 제거 — L58-74의 첫 번째 호출이 이미 처리

            # [V63] constraint_summary 저장
            if constraint_block:
                _constraint_lines = constraint_block.strip().split("\n")
                _must_not = [ln.strip() for ln in _constraint_lines if "금지" in ln or "MUST NOT" in ln or "절대" in ln]
                refined_arc["constraint_summary"] = "\n".join(_must_not[:10]) if _must_not else ""

            # [Equipment Sync] arc_start_state.equipment ← 이전 Arc 종료 소지품 강제 동기화
            if all_refined_arcs:
                _prev = all_refined_arcs[-1]
                _prev_end = _prev.get("state_constraints", {}).get("arc_end_state", {})
                _correct_equip = _prev_end.get("equipment")
                if _correct_equip is None:
                    _correct_equip = _prev.get("joint_docs", {}).get("physical_inventory", [])
                # 타입 정규화
                if isinstance(_correct_equip, str):
                    _correct_equip = [_correct_equip] if _correct_equip and _correct_equip != "[]" else []
                elif isinstance(_correct_equip, dict):
                    _correct_equip = [_correct_equip] if _correct_equip else []
                elif not isinstance(_correct_equip, list):
                    _correct_equip = []

                _curr_sc = refined_arc.get("state_constraints", {})
                _curr_start = _curr_sc.get("arc_start_state", {})
                _old_equip = _curr_start.get("equipment", [])
                if _old_equip != _correct_equip:
                    _curr_start["equipment"] = _correct_equip
                    _curr_sc["arc_start_state"] = _curr_start
                    refined_arc["state_constraints"] = _curr_sc
                    self.ctx.ui.log(
                        f"      🔧 [Equipment Sync] Arc {global_arc_no} 시작 소지품 → "
                        f"이전 Arc 종료 소지품으로 동기화 ({len(_correct_equip)}개 아이템)"
                    )

            # [P0-B3-1] arc_no 보장 — validate_arc 전 주입
            if isinstance(refined_arc, dict) and "arc_no" not in refined_arc:
                refined_arc["arc_no"] = global_arc_no
            refined_arc = validate_arc(refined_arc)  # [Step2] Pydantic ingress+egress

            # [NS-2] Advisory-only check: treatment block target vs arc_end_state alignment.
            _ns2_warnings = _check_block_worldstate_alignment(enriched_block, refined_arc, global_arc_no)
            if _ns2_warnings:
                for _warn in _ns2_warnings:
                    logging.warning(_warn)

            all_refined_arcs.append(refined_arc)

            ### [0124 핵심 4] DB 원자적 커밋
            try:
                self.ctx.current_project.save_v20_anchor("arcs", all_refined_arcs)
                # [Codex-fix] safe_commit_async는 실패 시 예외 대신 False 반환
                if callable(getattr(self.ctx, "safe_commit_async", None)):
                    _commit_ok = await self.ctx.safe_commit_async()
                    if not _commit_ok:
                        raise RuntimeError("safe_commit_async returned False")
            except (OSError, RuntimeError) as commit_err:
                # [TF-C09] DB 트랜잭션 롤백 — 반쪽 커밋 방지
                try:
                    _conn = self.ctx.current_project.db.conn
                    if _conn.in_transaction:
                        _conn.rollback()
                        logging.info("🔄 [TF-C09] DB rollback 완료 (Arc %d)", global_arc_no)
                except Exception as _rb:
                    logging.warning("⚠️ [TF-C09] DB rollback 실패: %s", _rb)
                self.ctx.ui.log(f"🚨 [DB] Arc {global_arc_no} 저장 실패: {commit_err}")
                if callable(getattr(self.ctx, "audit_event", None)):
                    self.ctx.audit_event(
                        "db_commit_error",
                        "arc save failed in async",
                        {"arc_no": global_arc_no, "error": str(commit_err)},
                    )
                all_refined_arcs.pop()
                # [Sweep52] DB 실패 시 StateTracker 롤백 (st_snapshot 보존)
                if st_snapshot:
                    try:
                        _st = self.ctx.state_tracker
                        for _k, _v in st_snapshot.items():
                            if hasattr(_st, _k):  # [감리] 다른 롤백 경로와 일관된 hasattr 가드
                                setattr(_st, _k, _v)
                        logging.info("🔄 [V70] DB 실패 StateTracker 롤백 완료")
                    except Exception as _rb_err:
                        logging.warning(f"⚠️ [V70] DB 실패 StateTracker 롤백 실패: {_rb_err}")
                return {"action": "retry", "current_feedback": current_feedback}

            st_snapshot = None  # [V70] DB 커밋 성공 후 스냅샷 해제
            self.ctx.cumulative_state_cache = None
            self.ctx.cumulative_state_cache_key = None  # [S-08] 센티넬 (0은 유효한 키일 수 있음)

            # [Graph-Layer] Arc 인과 의존성 자동 기록 (순차 의존: 전화 Arc → 현재 Arc)
            _arc_no = global_arc_no
            if _arc_no > 1 and getattr(self.ctx, "current_project", None):
                try:
                    _desc = refined_arc.get("theme", "") or refined_arc.get("title", "")
                    self.ctx.current_project.db.upsert_arc_dependency(
                        from_arc=_arc_no - 1,
                        to_arc=_arc_no,
                        dep_type="causes",
                        description=str(_desc)[:200],
                    )
                    # 명시적 prerequisite_arcs 필드 처리
                    for _prereq in refined_arc.get("prerequisite_arcs") or []:
                        if isinstance(_prereq, int) and _prereq != _arc_no:
                            self.ctx.current_project.db.upsert_arc_dependency(_prereq, _arc_no, "requires", "")
                except (AttributeError, TypeError) as _ade:
                    logging.debug("[Stage2] arc_dependency 저장 실패 (비치명): %s", _ade)

            # [B4-P1-1] constraint_db는 DB 커밋 이후 업데이트 — 실패해도 다음 루프에서 복구 가능
            try:
                constraint_db.update_arc_state(refined_arc)
                self.ctx.ui.log(
                    f"      🔒 [V49.4] ConstraintDB 업데이트 완료 (총 {len(constraint_db.arc_states)}개 Arc)"
                )
            except (AttributeError, TypeError, RuntimeError) as _cdb_err:
                logging.warning("[B4-P1-1] constraint_db.update_arc_state 실패 (비치명적): %s", _cdb_err)

            if callable(getattr(self.ctx, "generate_arc_context_v60", None)):
                last_refined_context = self.ctx.generate_arc_context_v60(all_refined_arcs, global_arc_no + 1)
            current_ep_start = refined_arc["ep_end"] + 1

            # [4-R3-f] PASS 메트릭 기록
            self._record_s2_pass_metrics(
                global_arc_no=global_arc_no,
                attempt=attempt,
                generation_method=generation_method,
                audit=audit,
                duration_ms=_director_duration_ms,
                is_patch=is_patch,
                prev_score=prev_score,
                patch_fallback=patch_fallback,
            )

            # [Phase 6] Arc 단위 비용 스냅샷 저장 (비차단)
            try:
                collector = get_metrics_collector()
                if collector and self.ctx.current_project and hasattr(self.ctx.current_project, "db"):
                    scope = collector.snapshot_and_reset_scope()
                    if (
                        scope.get("total_calls", 0) > 0
                        or scope.get("total_tokens", 0) > 0
                        or scope.get("total_cost_usd", 0.0) > 0
                    ):
                        self.ctx.current_project.db.save_cost_record(
                            session_id=collector.session_id,
                            scope_type="arc",
                            scope_id=global_arc_no,
                            total_calls=scope.get("total_calls", 0),
                            total_tokens=scope.get("total_tokens", 0),
                            total_cost_usd=scope.get("total_cost_usd", 0.0),
                            model_breakdown=scope.get("model_breakdown", "{}"),
                        )
            except (OSError, RuntimeError, TypeError) as cost_err:
                logging.warning("[Phase 6] Arc 비용 기록 실패 (비차단): %s", cost_err)

            # [V68] 계층적 요약 피라미드 — 볼륨 요약 (10 Arc마다)
            if global_arc_no > 0 and global_arc_no % 10 == 0:
                try:
                    _vol_no = global_arc_no // 10
                    _arc_summaries_for_vol = []
                    for _ai in range(global_arc_no - 9, global_arc_no + 1):
                        _as = self.ctx.current_project.load_v20_anchor(f"arc_summary_{_ai}")
                        if _as:
                            # arc_summary는 dict 또는 str일 수 있음
                            if isinstance(_as, dict):
                                _as_text = _as.get("summary", "") or _as.get("text", "")
                                if not _as_text:
                                    # [V70] arc_summary dict를 읽기 좋은 텍스트로 변환
                                    _parts = []
                                    if _as.get("npc_status") and isinstance(_as["npc_status"], dict):
                                        _parts.append(
                                            "NPC: "
                                            + ", ".join(
                                                f"{n}({v.get('status', '')})" for n, v in _as["npc_status"].items()
                                            )
                                        )
                                    if _as.get("world_changes"):
                                        _parts.append(
                                            "세계변화: " + "; ".join(str(w) for w in _as["world_changes"][:5])
                                        )
                                    if _as.get("resolved_plots"):
                                        _parts.append(
                                            "해결플롯: " + "; ".join(str(p) for p in _as["resolved_plots"][:5])
                                        )
                                    if _as.get("active_plots"):
                                        _parts.append("진행플롯: " + "; ".join(str(p) for p in _as["active_plots"][:5]))
                                    if _as.get("destroyed_entities"):
                                        _parts.append(
                                            "파괴: " + "; ".join(str(d) for d in _as["destroyed_entities"][:3])
                                        )
                                    _as_text = " | ".join(_parts) if _parts else str(_as)
                            else:
                                _as_text = str(_as)
                            if _as_text:
                                _arc_summaries_for_vol.append(f"Arc {_ai}: {_as_text}")

                    if _arc_summaries_for_vol:
                        _vol_prompt = (
                            "아래 10개 아크 요약을 하나의 볼륨 요약으로 합쳐주세요.\n"
                            "핵심 사건, 주요 인물 변화, 세계 상태 변화에 집중하세요.\n"
                            "1000자 이내로 작성하세요.\n\n"
                            + "\n".join(_arc_summaries_for_vol)
                            + f"\n\n볼륨 {_vol_no} 요약:"
                        )
                        _vol_result = self.ctx.agents["director"].ask(_vol_prompt, temperature=0.2)
                        if _vol_result and isinstance(_vol_result, str) and len(_vol_result) > 20:
                            self.ctx.current_project.save_v20_anchor(f"volume_summary_{_vol_no}", _vol_result)
                            logging.info(f"📖 [V68] 볼륨 {_vol_no} 요약 저장 완료 ({len(_vol_result)}자)")

                            # [V68] 시리즈 요약 갱신 — 기존 + 새 볼륨 통합
                            try:
                                _existing_series = self.ctx.current_project.load_v20_anchor("series_summary") or ""
                                if isinstance(_existing_series, dict):
                                    _existing_series = _existing_series.get("summary", "") or str(_existing_series)
                                _series_prompt = (
                                    "아래는 기존 시리즈 요약과 새 볼륨 요약입니다.\n"
                                    "이를 통합하여 전체 시리즈 요약을 1000자 이내로 갱신하세요.\n"
                                    "핵심 사건, 주요 인물 변화, 세계 상태 변화에 집중하세요.\n\n"
                                    f"기존 시리즈 요약:\n{_existing_series or '(아직 없음)'}\n\n"
                                    f"새 볼륨 {_vol_no} 요약:\n{_vol_result}\n\n"
                                    "갱신된 시리즈 요약:"
                                )
                                _series_result = self.ctx.agents["director"].ask(_series_prompt, temperature=0.2)
                                if _series_result and isinstance(_series_result, str) and len(_series_result) > 20:
                                    self.ctx.current_project.save_v20_anchor("series_summary", _series_result)
                                    logging.info(f"📚 [V68] 시리즈 요약 갱신 완료 ({len(_series_result)}자)")
                            except Exception as _se:
                                logging.warning(f"⚠️ [V68] 시리즈 요약 갱신 실패 (비차단): {_se}")
                        else:
                            logging.warning("⚠️ [V68] 볼륨 요약 LLM 응답 불충분 — 건너뜀")
                except Exception as _ve:
                    logging.warning(f"⚠️ [V68] 볼륨 요약 생성 실패 (비차단): {_ve}")

            return {
                "action": "break",
                "last_refined_context": last_refined_context,
                "current_ep_start": current_ep_start,
                "current_feedback": current_feedback,
                "director_feedback_for_fourphase": director_feedback_for_fourphase,
                "st_snapshot": st_snapshot,
            }
        else:
            # [V60.77] Director REJECT (PASS_WITH_FIX는 위에서 PASS 경로로 처리됨)
            _rejected_arc = refined_arc  # [Patch Mode] REJECT된 Arc 보존 (패치 모드 판단용)
            base_feedback = audit.get("re_slice_instruction") or "밀도 보강 필요"
            reject_reason = audit.get("reason") or "사유 미상"
            _score_breakdown = {}
            _self_consistency = audit.get("self_consistency", {})
            if isinstance(_self_consistency, dict):
                for _k in ("votes", "pass_votes", "median_score"):
                    _v = _self_consistency.get(_k)
                    if isinstance(_v, int | float):
                        _score_breakdown[_k] = _v

            if callable(getattr(self.ctx, "get_adaptive_feedback_intensity", None)):
                adaptive_intensity = self.ctx.get_adaptive_feedback_intensity(attempt, stage=2)
                intensity_guide = f"\n\n[V60.9 재시도 가이드 ({attempt + 1}회차)]\n{adaptive_intensity['guidance']}"
            else:
                intensity_guide = ""

            self.ctx.ui.log(f"      🎬 [Director REJECT] {reject_reason[:100]}")
            self.ctx.ui.log(f"      📋 피드백: {base_feedback[:100]}")

            # [V70] StateTracker 롤백: FourPhase PASS → Director REJECT 시 팬텀 데이터 제거
            if st_snapshot and generation_method.startswith("four_phase"):  # [TF-R2-S2-11] ASP 포함
                try:
                    _st = self.ctx.state_tracker
                    for _k, _v in st_snapshot.items():
                        if hasattr(_st, _k):  # [감리] 다른 롤백 경로와 일관된 hasattr 가드
                            setattr(_st, _k, _v)
                    logging.info("🔄 [V70] StateTracker 롤백 완료 (Director REJECT)")
                except Exception as _rb_err:
                    logging.warning(f"⚠️ [V70] StateTracker 롤백 실패 (비차단): {_rb_err}")
                st_snapshot = None

            director_feedback_for_fourphase = f"""[Director REJECT 사유]
{reject_reason}

[수정 지시]
{base_feedback}

[재시도 가이드]
{intensity_guide}
"""
            refined_arc = None
            self.ctx.ui.log(f"      🔄 [V60.77] Director 피드백 → FourPhase 대면 {min(attempt + 2, 5)}/5")

            # [4-R3-f] REJECT 메트릭 기록
            self._record_s2_reject_metrics(
                global_arc_no=global_arc_no,
                attempt=attempt,
                generation_method=generation_method,
                audit=audit,
                duration_ms=_director_duration_ms,
                is_patch=is_patch,
                prev_score=prev_score,
                patch_fallback=patch_fallback,
            )

        return {
            "action": "retry",
            "last_refined_context": last_refined_context,
            "current_ep_start": current_ep_start,
            "current_feedback": current_feedback,
            "director_feedback_for_fourphase": director_feedback_for_fourphase,
            "st_snapshot": st_snapshot,
            "score": audit.get("score", 0),  # [Patch Mode] Director 점수
            "rejected_arc": _rejected_arc,  # [Patch Mode] REJECT된 Arc (패치 입력용)
            "score_breakdown": _score_breakdown,
            "selection_reason": reject_reason,
            "validation_warnings": [reject_reason, base_feedback],
            "fix_scope": audit.get("fix_scope", ""),  # [TF-33] Director 판단 수정 범위
            "fix_scope_reasoning": audit.get("fix_scope_reasoning", ""),  # [TF-33]
        }

    def _record_s2_pass_metrics(
        self,
        *,
        global_arc_no: int,
        attempt: int,
        generation_method: str,
        audit: dict,
        duration_ms: int | None = None,
        is_patch: bool = False,
        prev_score: float = 0.0,
        patch_fallback: bool = False,
    ) -> None:
        """[4-R3-f] Record Stage 2 PASS metrics (PassRateMonitor, Dashboard, Optimizer, PerfTimer)."""
        from modules.core.spinners import V50_MODULES_AVAILABLE

        if V50_MODULES_AVAILABLE and self.ctx.pass_rate_monitor:
            try:
                self.ctx.pass_rate_monitor.record_attempt(
                    stage=2,
                    episode=global_arc_no,
                    arc=global_arc_no,
                    attempt_num=attempt + 1,
                    success=True,
                    generation_method=generation_method,
                    is_patch=is_patch,
                    prev_score=prev_score,
                    patch_fallback=patch_fallback,
                )
            except Exception as e:  # [V64.P4] OPTIONAL: metrics
                logging.debug(f"[SILENT] metrics (success): {e}")

        try:
            _db = getattr(getattr(self.ctx, "current_project", None), "db", None)
            if _db and hasattr(_db, "save_stage_attempt"):
                _score = audit.get("score", 0)
                if not isinstance(_score, int):
                    try:
                        _score = int(_score)
                    except (ValueError, TypeError):
                        _score = 0
                _director = getattr(getattr(self.ctx, "agents", {}), "get", lambda *_: None)("director")
                _model = getattr(_director, "primary_model", None) if _director else None
                _failure_category = self._extract_failure_category(audit)
                _advisory_flags = self._extract_advisory_flags(audit)
                _db.save_stage_attempt(
                    stage=2,
                    verdict=str(audit.get("decision", "PASS")),
                    attempt_num=attempt + 1,
                    ep_num=global_arc_no,
                    arc_num=global_arc_no,
                    score=_score,
                    failure_category=_failure_category,
                    fix_scope=str(audit.get("fix_scope", "") or ""),
                    model=str(_model) if _model else None,
                    duration_ms=duration_ms,
                    advisory_flags=_advisory_flags,
                )
        except Exception as _sa_err:
            logging.debug("[stage_attempts] Stage2 PASS 기록 실패 (비차단): %s", _sa_err)

        if V50_MODULES_AVAILABLE and self.ctx.quality_dashboard:
            try:
                self.ctx.quality_dashboard.record_validation(
                    ep_num=global_arc_no,
                    result={
                        "decision": "PASS",
                        "score": audit.get("score", 80),
                        "violations": [],
                        "warnings": [],
                    },
                    stage=2,
                )
            except Exception as e:  # [V64.P4] OPTIONAL: dashboard metrics
                logging.debug(f"[SILENT] dashboard metrics (PASS): {e}")

        if self.ctx.stage2_optimizer:
            try:
                self.ctx.stage2_optimizer.failure_memory.clear_arc_failures(global_arc_no)
                self.ctx.ui.log(f"      ✨ [V60.25] Arc {global_arc_no} 최종 성공 - 실패 메모리 클리어")
            except Exception as e:  # [V64.P4] OPTIONAL: optimizer memory clear
                logging.debug(f"[SILENT] optimizer memory clear: {e}")

        try:
            self.ctx.perf_timer.log_summary()
            self.ctx.perf_timer.reset()
        except Exception as e:
            logging.debug(f"[PerfTimer] s2 summary/reset: {e}")

    def _record_s2_reject_metrics(
        self,
        *,
        global_arc_no: int,
        attempt: int,
        generation_method: str,
        audit: dict,
        duration_ms: int | None = None,
        is_patch: bool = False,
        prev_score: float = 0.0,
        patch_fallback: bool = False,
    ) -> None:
        """[4-R3-f] Record Stage 2 REJECT metrics (PassRateMonitor, Dashboard, History, Optimizer)."""
        from modules.core.spinners import V50_MODULES_AVAILABLE

        if V50_MODULES_AVAILABLE and self.ctx.pass_rate_monitor:
            try:
                self.ctx.pass_rate_monitor.record_attempt(
                    stage=2,
                    episode=global_arc_no,
                    arc=global_arc_no,
                    attempt_num=attempt + 1,
                    success=False,
                    reject_reason=str(audit.get("reason", ""))[:100],
                    generation_method=generation_method,
                    is_patch=is_patch,
                    prev_score=prev_score,
                    patch_fallback=patch_fallback,
                )
            except Exception as e:  # [V64.P4] OPTIONAL: metrics
                logging.debug(f"[SILENT] metrics (reject): {e}")

        try:
            _db = getattr(getattr(self.ctx, "current_project", None), "db", None)
            if _db and hasattr(_db, "save_stage_attempt"):
                _score = audit.get("score", 0)
                if not isinstance(_score, int):
                    try:
                        _score = int(_score)
                    except (ValueError, TypeError):
                        _score = 0
                _director = getattr(getattr(self.ctx, "agents", {}), "get", lambda *_: None)("director")
                _model = getattr(_director, "primary_model", None) if _director else None
                _failure_category = self._extract_failure_category(audit)
                _advisory_flags = self._extract_advisory_flags(audit)
                _db.save_stage_attempt(
                    stage=2,
                    verdict=str(audit.get("decision", "REJECT")),
                    attempt_num=attempt + 1,
                    ep_num=global_arc_no,
                    arc_num=global_arc_no,
                    score=_score,
                    failure_category=_failure_category,
                    reject_reason=str(audit.get("reason", ""))[:500],
                    fix_scope=str(audit.get("fix_scope", "") or ""),
                    model=str(_model) if _model else None,
                    duration_ms=duration_ms,
                    advisory_flags=_advisory_flags,
                )
        except Exception as _sa_err:
            logging.debug("[stage_attempts] Stage2 REJECT 기록 실패 (비차단): %s", _sa_err)

        try:
            _score = audit.get("score", 0)
            if not isinstance(_score, int):
                try:
                    _score = int(_score)
                except (ValueError, TypeError):
                    _score = 0
            self.ctx.current_project.db.save_cost_record(
                session_id=f"arc_{global_arc_no}",
                scope_type="arc",
                scope_id=int(global_arc_no),
                total_calls=0,
                total_tokens=0,
                total_cost_usd=0.0,
                model_breakdown={
                    "event": "stage2_reject",
                    "score": _score,
                    "attempt": attempt + 1,
                    "generation_method": generation_method,
                    "is_patch": is_patch,
                    "patch_fallback": patch_fallback,
                },
            )
        except (OSError, RuntimeError, TypeError) as e:
            logging.warning(f"[SilentPass:Stage2RejectMetric] {e!s:.120}")

        if V50_MODULES_AVAILABLE and self.ctx.quality_dashboard:
            try:
                self.ctx.quality_dashboard.record_validation(
                    ep_num=global_arc_no,
                    result={
                        "decision": "REJECT",
                        "score": audit.get("score", 0),
                        "violations": [
                            {
                                "type": "director_reject",
                                "description": str(audit.get("reason", ""))[:200],
                            }
                        ],
                        "warnings": [],
                    },
                    stage=2,
                )
            except Exception as e:  # [V64.P4] OPTIONAL: dashboard metrics
                logging.debug(f"[SILENT] dashboard metrics (REJECT): {e}")

        if self.ctx.stage_rejection_history is not None:  # [Sweep4] None 가드
            self.ctx.stage_rejection_history.append(
                {
                    "stage": 2,
                    "arc_no": global_arc_no,
                    "reason": str(audit.get("reason", ""))[:200],
                    "attempt": attempt + 1,
                }
            )

        if self.ctx.stage2_optimizer:
            try:
                self.ctx.stage2_optimizer.failure_memory.record_failure(
                    arc_no=global_arc_no,
                    failure_type="director_reject",
                    details=str(audit.get("reason", ""))[:200],
                )
            except Exception as e:  # [V64.P4] OPTIONAL: optimizer failure recording
                logging.debug(f"[SILENT] optimizer failure recording: {e}")

    @staticmethod
    def _extract_failure_category(audit: dict) -> str | None:
        """Best-effort category extraction without fabricating missing fields."""
        if not isinstance(audit, dict):
            return None
        for key in ("error_category", "failure_category", "reject_category"):
            value = audit.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()[:80]
        contradiction_types = audit.get("contradiction_types")
        if isinstance(contradiction_types, list):
            for item in contradiction_types:
                if isinstance(item, str) and item.strip():
                    return item.strip()[:80]
        return None

    @staticmethod
    def _extract_advisory_flags(audit: dict) -> dict | None:
        """Collect advisory-like metadata already available in Director audit output."""
        if not isinstance(audit, dict):
            return None

        flags: dict = {}
        if audit.get("v60_43_api_warning"):
            flags["v60_43_api_warning"] = 1

        contradictions = audit.get("contradictions")
        if isinstance(contradictions, list):
            flags["contradictions_count"] = len(contradictions)

        contradiction_types = audit.get("contradiction_types")
        if isinstance(contradiction_types, list):
            compact_types = [str(t)[:40] for t in contradiction_types[:5] if str(t).strip()]
            if compact_types:
                flags["contradiction_types"] = compact_types

        self_consistency = audit.get("self_consistency")
        if isinstance(self_consistency, dict):
            votes = self_consistency.get("votes")
            pass_votes = self_consistency.get("pass_votes")
            if isinstance(votes, int):
                flags["votes"] = votes
            if isinstance(pass_votes, int):
                flags["pass_votes"] = pass_votes

        return flags or None
