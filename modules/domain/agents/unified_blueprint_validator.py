"""
[V60.80] Unified Blueprint Validator
Stage 3 사전검사기 + Director 최종 판정

철학:
- "디렉터주권주의" - 최종 결정권은 Director에게 있다
- 사전검사는 Director 호출 전 자가점검 수준

구조:
1. Python 사전검사 (무료, 빠름) - 경고만, REJECT 권한 없음
   - 분량 체크 (integrated_scenario 길이)
   - 필수 필드 체크 (scene_breakdown, integrated_scenario)
   - 정지선 위반 체크 (다음 화 내용 침범)
   - 연속성 체크 (위치, 시간)
   - [V60.96] 죽은 NPC 등장 체크 (CRITICAL 경고 → Director에게 전달)
2. Director 최종 판정 (audit_manuscript)
   - Arc 준수, 서사 개연성, 캐릭터 논리 검증
   - Director의 verdict가 최종 결정
   - [V60.96] 죽은 NPC 경고 포함 시 REJECT 권고
"""

import json
import logging
import re

from modules.core.constants import AIModels, Stage2Limits

from .base_agent import _get_agent_default_model

# Blueprint 검증용 최소 분량
BLUEPRINT_MIN_CHARS = 800  # integrated_scenario 최소 길이
_STOP_LINE_TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣]{2,}")
_STOP_LINE_SPLIT_RE = re.compile(r"[\n;,.!?/]+")
_STOP_LINE_COMMON_TOKENS = {
    "다음",
    "다음화",
    "이번",
    "에피소드",
    "장면",
    "주인공",
    "블루프린트",
    "시나리오",
    "계획",
    "전개",
    "준비",
    "상황",
    "현재",
    "이후",
    "화",
}


def _safe_int(value, default=0):
    """LLM 반환값을 안전하게 int로 변환한다."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


class UnifiedBlueprintValidator:
    """
    [V60.80] 통합 Blueprint 검증기

    역할:
    1. Python 사전검사 (무료)
    2. Director 호출 중개 (최종 판정)
    """

    def __init__(self, context, client, model_tier: str = None):
        self.context = context
        self.client = client
        self.model_tier = (
            model_tier or _get_agent_default_model("unified_blueprint_validator") or AIModels.FLASH_ANALYSIS_MODEL
        )
        self.min_chars = BLUEPRINT_MIN_CHARS

    def _safe_causal_history(self) -> str:
        """get_causal_history_summary()를 안전하게 호출한다 (DB 오류 시 빈 문자열)."""
        if not hasattr(self.context, "get_causal_history_summary"):
            return ""
        try:
            return str(self.context.get_causal_history_summary())
        except Exception as e:
            logging.warning(f"[S3-P1-2] get_causal_history_summary DB 오류: {e!s:.100}")
            return ""

    def _apply_dead_npc_advisory(
        self,
        pre_result: dict,
        *,
        blueprint: dict | None,
        state_tracker,
        working_ep: int,
        arc_no: int,
    ) -> list[dict]:
        """Keep dead-NPC checks advisory-only and reusable across compare flows."""
        if not state_tracker or not isinstance(blueprint, dict):
            return []

        dead_npc_violations = state_tracker.check_dead_npc_in_blueprint(blueprint, working_ep, arc_no)
        if not dead_npc_violations:
            return []

        violation_names = [v["npc_name"] for v in dead_npc_violations]
        pre_result.setdefault("issues", []).append(
            {
                "severity": "CRITICAL",
                "category": "dead_npc",
                "issue": f"죽은 NPC 등장: {', '.join(violation_names)}",
                "evidence": dead_npc_violations[0]["reason"],
                "fix_hint": "죽은 NPC는 회상/언급만 허용",
            }
        )
        pre_result["has_critical"] = True
        return dead_npc_violations

    def _build_python_warning_entries(self, issues: list) -> tuple[list[dict], bool]:
        """Compact Python findings so Director sees bounded evidence, not raw dumps."""
        if not isinstance(issues, list):
            return [], False

        entries: list[dict] = []
        seen: set[tuple[str, str, str]] = set()
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            severity = str(issue.get("severity", "MINOR") or "MINOR").upper()
            category = str(issue.get("category", "issue") or "issue").strip()[:40]
            message = str(issue.get("issue") or issue.get("evidence") or "").strip()
            if not message:
                continue
            key = (severity, category, message[:160])
            if key in seen:
                continue
            seen.add(key)
            entry = {
                "source": "python_prevalidate",
                "severity": severity,
                "category": category,
                "message": message[:160],
            }
            focus = str(issue.get("fix_hint", "") or "").strip()
            if focus:
                entry["focus"] = focus[:120]
            entries.append(entry)
            if len(entries) >= 4:
                break

        return entries, bool(entries)

    @staticmethod
    def _extract_stop_line_clauses(text: str) -> list[str]:
        if not isinstance(text, str):
            return []
        clauses: list[str] = []
        seen: set[str] = set()
        for raw in _STOP_LINE_SPLIT_RE.split(text):
            clause = " ".join(str(raw).strip().split())
            if len(clause) < 8:
                continue
            lowered = clause.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            clauses.append(clause)
        return clauses

    @staticmethod
    def _extract_significant_stop_tokens(text: str) -> set[str]:
        if not isinstance(text, str):
            return set()
        tokens: set[str] = set()
        for token in _STOP_LINE_TOKEN_RE.findall(text.lower()):
            if token.isdigit():
                continue
            if token in _STOP_LINE_COMMON_TOKENS:
                continue
            tokens.add(token)
        return tokens

    def _detect_stop_line_violation(self, stop_content: str, integrated: str) -> dict | None:
        if not isinstance(stop_content, str) or not isinstance(integrated, str):
            return None

        integrated_norm = " ".join(integrated.lower().split())
        if not integrated_norm:
            return None
        integrated_tokens = self._extract_significant_stop_tokens(integrated_norm)

        for clause in self._extract_stop_line_clauses(stop_content):
            clause_norm = " ".join(clause.lower().split())
            if len(clause_norm) >= 12 and clause_norm in integrated_norm:
                return {"mode": "clause_substring", "evidence": clause[:120]}

            clause_tokens = self._extract_significant_stop_tokens(clause_norm)
            if len(clause_tokens) < 3:
                continue
            overlap = clause_tokens & integrated_tokens
            overlap_ratio = len(overlap) / max(len(clause_tokens), 1)
            if len(overlap) >= 3 and overlap_ratio >= 0.75:
                return {
                    "mode": "token_overlap",
                    "evidence": clause[:120],
                    "overlap_tokens": sorted(overlap)[:5],
                }

        return None

    def _prepare_compare_candidate(
        self,
        candidate: dict,
        *,
        candidate_index: int,
        arc_data: dict,
        constraint_block: dict,
        prev_blueprint: dict | None,
        state_tracker,
        working_ep: int,
        arc_idx: int,
    ) -> tuple[dict, dict]:
        """Attach bounded prevalidation evidence before Director compare selection."""
        if not isinstance(candidate, dict):
            return {"issues": [], "has_critical": False}, {
                "candidate_index": candidate_index,
                "quality_risk": False,
            }

        pre_result = self._python_pre_validate(
            candidate,
            constraint_block,
            prev_blueprint,
            state_tracker,
            arc_data=arc_data,
        )
        candidate_arc_no = arc_data.get("arc_no", 0) if isinstance(arc_data, dict) else arc_idx
        if candidate_arc_no <= 0:
            candidate_arc_no = arc_idx
        self._apply_dead_npc_advisory(
            pre_result,
            blueprint=candidate,
            state_tracker=state_tracker,
            working_ep=working_ep,
            arc_no=candidate_arc_no,
        )

        python_warnings, quality_risk = self._build_python_warning_entries(pre_result.get("issues", []))
        meta = candidate.get("_ensemble_meta", {})
        if not isinstance(meta, dict):
            meta = {}
        meta["python_warnings"] = python_warnings
        meta["quality_risk"] = quality_risk
        meta["prevalidation_issue_count"] = len(pre_result.get("issues", []))
        candidate["_ensemble_meta"] = meta

        advisory = {
            "candidate_index": candidate_index,
            "strategy": str(meta.get("strategy", "") or "")[:60],
            "issue_count": len(pre_result.get("issues", [])),
            "quality_risk": quality_risk,
        }
        if python_warnings:
            advisory["python_warnings"] = python_warnings
        return pre_result, advisory

    def _run_compare_validation(
        self,
        *,
        all_candidates: list[dict],
        arc_data: dict,
        constraint_block: dict,
        prev_blueprint: dict | None,
        director,
        entity_registry: dict | None,
        state_tracker,
        working_ep: int,
        arc_idx: int,
    ) -> tuple[str, dict]:
        logging.warning(f"[V60.85] Director compare mode with {len(all_candidates)} candidates")

        compare_pre_results: list[dict] = []
        candidate_advisories: list[dict] = []
        for idx, candidate in enumerate(all_candidates):
            pre_result, advisory = self._prepare_compare_candidate(
                candidate,
                candidate_index=idx,
                arc_data=arc_data,
                constraint_block=constraint_block,
                prev_blueprint=prev_blueprint,
                state_tracker=state_tracker,
                working_ep=working_ep,
                arc_idx=arc_idx,
            )
            compare_pre_results.append(pre_result)
            candidate_advisories.append(advisory)

        compare_result = director.compare_and_select_blueprint(
            candidates=all_candidates,
            arc_data=arc_data,
            ep_num=working_ep,
            prev_blueprint=prev_blueprint,
            entity_registry=entity_registry,
            state_tracker=state_tracker,
        )

        selected_idx = _safe_int(compare_result.get("selected_index", 0), 0)
        if selected_idx < 0 or selected_idx >= len(all_candidates):
            selected_idx = 0
        selected_bp = compare_result.get("selected_blueprint")
        if not isinstance(selected_bp, dict) and 0 <= selected_idx < len(all_candidates):
            selected_bp = all_candidates[selected_idx]

        contradictions = compare_result.get("contradictions", [])
        if not isinstance(contradictions, list):
            contradictions = []

        if 0 <= selected_idx < len(compare_pre_results):
            selected_pre_result = compare_pre_results[selected_idx]
        else:
            selected_pre_result = {"issues": [], "has_critical": False}
        selected_candidate_advisory = (
            candidate_advisories[selected_idx]
            if 0 <= selected_idx < len(candidate_advisories)
            else {"candidate_index": selected_idx, "quality_risk": False}
        )

        verdict = compare_result.get("decision", "REJECT")
        quality_risk = bool(
            compare_result.get("quality_risk", False) or selected_candidate_advisory.get("quality_risk", False)
        )
        revision_required = bool(
            compare_result.get("revision_required", False) or verdict in ("PASS_WITH_FIX", "PASS_WITH_WARNING")
        )
        selection_reason = str(compare_result.get("selection_reason") or compare_result.get("reason", "") or "")
        verdict_reason = str(compare_result.get("verdict_reason") or selection_reason or "")

        result = {
            "verdict": verdict,
            "phase": "director_compare+python_prevalidate",
            "issues": selected_pre_result.get("issues", []),
            "summary": selection_reason,
            "score": compare_result.get("score", 0),
            "feedback": compare_result.get("feedback", ""),
            "confidence": 0.9 if _safe_int(compare_result.get("score", 0), 0) >= 70 else 0.6,
            "selected_index": selected_idx,
            "selected_blueprint": selected_bp,
            "comparison_notes": compare_result.get("comparison_notes", ""),
            "contradictions": contradictions,
            "fix_scope": compare_result.get("fix_scope", ""),
            "fix_scope_reasoning": compare_result.get("fix_scope_reasoning", ""),
            "selection_reason": selection_reason,
            "verdict_reason": verdict_reason,
            "quality_risk": quality_risk,
            "revision_required": revision_required,
            "candidate_count": len(all_candidates),
            "candidate_advisories": candidate_advisories,
            "selected_candidate_advisory": selected_candidate_advisory,
        }

        status = "PASS" if verdict in ("PASS", "PASS_WITH_FIX", "PASS_WITH_WARNING") else "REJECT"
        logging.info(f"[{status}] Director selected candidate {selected_idx + 1} with score {compare_result.get('score', 0)}")
        return verdict, result

    def _run_python_prevalidation_phase(
        self,
        *,
        blueprint: dict,
        arc_data: dict,
        constraint_block: dict,
        prev_blueprint: dict | None,
        state_tracker,
        working_ep: int,
        arc_idx: int,
    ) -> dict:
        pre_result = self._python_pre_validate(
            blueprint,
            constraint_block,
            prev_blueprint,
            state_tracker,
            arc_data=arc_data,
        )

        arc_no = arc_data.get("arc_no", 0) if arc_data else arc_idx
        if arc_no <= 0:
            arc_no = arc_idx

        dead_npc_violations = self._apply_dead_npc_advisory(
            pre_result,
            blueprint=blueprint,
            state_tracker=state_tracker,
            working_ep=working_ep,
            arc_no=arc_no,
        )
        if dead_npc_violations:
            violation_names = [v["npc_name"] for v in dead_npc_violations]
            logging.warning(f"[V60.96] Dead NPC advisory forwarded to Director: {', '.join(violation_names)}")

        if pre_result["has_critical"]:
            logging.warning("[PreValidator] Critical Python findings deferred to Director")
            for issue in pre_result["issues"]:
                if issue.get("severity") == "CRITICAL":
                    logging.warning(f"- {issue.get('issue', '?')}")
        elif pre_result["issues"]:
            logging.warning(f"[PreValidator] Python findings forwarded: {len(pre_result['issues'])}")

        return pre_result

    def _build_no_director_validation_result(self, pre_result: dict) -> tuple[str, dict]:
        logging.error("[FailClosed] Director missing during blueprint validation")
        return "REJECT", {
            "verdict": "REJECT",
            "phase": "no_director",
            "issues": pre_result["issues"],
            "summary": "Director unavailable during blueprint validation",
            "feedback": "Blueprint validation requires a Director decision.",
            "score": 0,
        }

    def _build_blueprint_validation_context(self, *, state_tracker, prev_hud: dict | None) -> dict:
        validation_context = {"skip_continuity": True, "mode": "BLUEPRINT"}
        if state_tracker:
            encyclopedia_npcs = []
            for npc_name, npc_info in getattr(state_tracker, "npc_registry", {}).items():
                encyclopedia_npcs.append(
                    {
                        "name": npc_name,
                        "status": npc_info.get("status", "alive"),
                        "death_arc": npc_info.get("death_arc"),
                        "aliases": npc_info.get("aliases", []),
                    }
                )
            validation_context["encyclopedia"] = {"npcs": encyclopedia_npcs}

        if isinstance(prev_hud, dict) and prev_hud:
            validation_context["prev_hud"] = prev_hud
            validation_context["martial_hud"] = prev_hud
        return validation_context

    def _prepare_director_validation_payload(
        self,
        *,
        blueprint: dict,
        arc_data: dict,
        prev_blueprint: dict | None,
        entity_registry: dict | None,
        state_tracker,
        prev_hud: dict | None,
        working_ep: int,
    ) -> dict:
        integrated_scenario = blueprint.get("integrated_scenario", "")
        if not isinstance(integrated_scenario, str):
            integrated_scenario = str(integrated_scenario) if integrated_scenario else ""

        arc_tactical_doc = arc_data.get("tactical_doc", "")
        if isinstance(arc_tactical_doc, dict):
            arc_tactical_doc = json.dumps(arc_tactical_doc, ensure_ascii=False)

        prev_ms_ending = ""
        if prev_blueprint:
            prev_ms_ending = prev_blueprint.get("ending_hook", "")

        ep_start = arc_data.get("ep_start", working_ep)
        arc_pos = working_ep - ep_start + 1
        total_eps = arc_data.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)

        ensemble_meta = blueprint.get("_ensemble_meta", {})
        python_warnings = ensemble_meta.get("python_warnings", [])
        if python_warnings:
            focus_header = "[Director Focus Header]\n"
            for warning in python_warnings:
                focus_header += f"  - {warning.get('message', '?')}: {warning.get('focus', '')}\n"
            focus_header += "\n[Blueprint Under Review]\n"
            manuscript_with_focus = focus_header + integrated_scenario
        else:
            manuscript_with_focus = integrated_scenario

        return {
            "ep_num": working_ep,
            "manuscript": manuscript_with_focus,
            "arc_doc": arc_tactical_doc,
            "history_summary": self._safe_causal_history(),
            "prev_full_text": prev_ms_ending,
            "arc_pos": arc_pos,
            "total_eps": total_eps,
            "target_len": self.min_chars,
            "retry_count": 0,
            "entity_registry": entity_registry,
            "state_tracker": state_tracker,
            "validation_context": self._build_blueprint_validation_context(
                state_tracker=state_tracker,
                prev_hud=prev_hud,
            ),
        }

    def _build_director_validation_result(
        self,
        *,
        blueprint: dict,
        pre_result: dict,
        director_result: dict,
    ) -> tuple[str, dict]:
        director_verdict = director_result.get("decision", "PASS")
        director_reason = director_result.get("reason", "")
        director_feedback = director_result.get("feedback", "")
        director_score = _safe_int(director_result.get("score", 50), 50)

        all_issues = pre_result["issues"][:]
        if director_verdict == "REJECT":
            all_issues.append(
                {
                    "severity": "MAJOR",
                    "category": "director",
                    "issue": f"Director REJECT: {director_reason}",
                    "evidence": director_feedback,
                    "fix_hint": director_feedback,
                }
            )

        final_verdict = director_verdict
        python_warnings, quality_risk = self._build_python_warning_entries(pre_result["issues"])
        if python_warnings:
            ensemble_meta = blueprint.get("_ensemble_meta", {}) if isinstance(blueprint, dict) else {}
            if not isinstance(ensemble_meta, dict):
                ensemble_meta = {}
            ensemble_meta["python_warnings"] = python_warnings
            ensemble_meta["quality_risk"] = quality_risk
            if isinstance(blueprint, dict):
                blueprint["_ensemble_meta"] = ensemble_meta

        result = {
            "verdict": final_verdict,
            "phase": "director",
            "issues": all_issues,
            "summary": director_reason,
            "score": director_score,
            "score_breakdown": {
                "director_score": director_score,
                "pre_issues_count": len(pre_result["issues"]),
            },
            "feedback": director_feedback if final_verdict in ("REJECT", "PASS_WITH_FIX") else "",
            "pre_issues": len(pre_result["issues"]),
            "confidence": 0.9 if director_score >= 70 else 0.6,
            "fix_scope": director_result.get("fix_scope", ""),
            "fix_scope_reasoning": director_result.get("fix_scope_reasoning", ""),
            "re_slice_instruction": director_result.get("re_slice_instruction", ""),
            "selection_reason": director_result.get("selection_reason", "") or director_reason,
            "verdict_reason": director_result.get("verdict_reason", "") or director_reason,
            "quality_risk": quality_risk,
            "revision_required": final_verdict in ("PASS_WITH_FIX", "PASS_WITH_WARNING"),
            "candidate_count": 1,
        }

        status = "PASS" if final_verdict in ("PASS", "PASS_WITH_FIX") else "REJECT"
        logging.warning(f"[{status}] Director score={director_score} reason={(director_reason or '')[:50]}")
        return final_verdict, result

    def _build_director_error_result(self, pre_result: dict, exc: Exception) -> tuple[str, dict]:
        return "REJECT", {
            "verdict": "REJECT",
            "phase": "director_error",
            "issues": pre_result["issues"],
            "summary": "Director validation error - retry required",
            "feedback": (
                "[Director error triggered retry]\n"
                f"error: {str(exc)[:100]}\n"
                "please regenerate and review again"
            ),
        }

    def validate(
        self,
        blueprint: dict,
        arc_data: dict,
        constraint_block: dict,
        prev_blueprint: dict | None = None,
        director=None,  # final Director authority
        working_ep: int = 1,
        arc_idx: int = 0,
        entity_registry: dict | None = None,
        state_tracker=None,
        all_candidates: list[dict] | None = None,
        prev_hud: dict | None = None,
    ) -> tuple[str, dict]:
        """Run Python prevalidation and then defer the final verdict to Director."""
        if all_candidates and len(all_candidates) > 1 and director:
            return self._run_compare_validation(
                all_candidates=all_candidates,
                arc_data=arc_data,
                constraint_block=constraint_block,
                prev_blueprint=prev_blueprint,
                director=director,
                entity_registry=entity_registry,
                state_tracker=state_tracker,
                working_ep=working_ep,
                arc_idx=arc_idx,
            )

        pre_result = self._run_python_prevalidation_phase(
            blueprint=blueprint,
            arc_data=arc_data,
            constraint_block=constraint_block,
            prev_blueprint=prev_blueprint,
            state_tracker=state_tracker,
            working_ep=working_ep,
            arc_idx=arc_idx,
        )
        if director is None:
            return self._build_no_director_validation_result(pre_result)

        logging.warning("[Director] Blueprint audit started")
        try:
            director_result = director.audit_manuscript(
                **self._prepare_director_validation_payload(
                    blueprint=blueprint,
                    arc_data=arc_data,
                    prev_blueprint=prev_blueprint,
                    entity_registry=entity_registry,
                    state_tracker=state_tracker,
                    prev_hud=prev_hud,
                    working_ep=working_ep,
                )
            )
            return self._build_director_validation_result(
                blueprint=blueprint,
                pre_result=pre_result,
                director_result=director_result,
            )
        except Exception as e:
            logging.warning(f"[Director] audit error: {str(e)[:50]}")
            return self._build_director_error_result(pre_result, e)

    @staticmethod
    def _normalize_integrated_scenario(integrated) -> str:
        if isinstance(integrated, str):
            return integrated
        return str(integrated) if integrated else ""

    @staticmethod
    def _count_scene_entries(scenes) -> int:
        if isinstance(scenes, (dict, list)):
            return len(scenes)
        return 0

    @staticmethod
    def _iter_scene_entries(scenes):
        if isinstance(scenes, dict):
            return scenes.values()
        if isinstance(scenes, list):
            return scenes
        return ()

    @staticmethod
    def _extract_prev_blueprint_end_location(prev_blueprint: dict | None) -> str:
        if not isinstance(prev_blueprint, dict):
            return ""

        prev_end_location = prev_blueprint.get("end_location", "")
        if prev_end_location:
            return prev_end_location

        prev_scenes = prev_blueprint.get("scene_breakdown", {})
        if prev_scenes and isinstance(prev_scenes, dict):
            scene_keys = sorted(prev_scenes.keys())
            if scene_keys:
                last_scene = prev_scenes.get(scene_keys[-1], {})
                if isinstance(last_scene, dict):
                    return last_scene.get("location", "")
        return ""

    def _collect_structure_prevalidation_issues(
        self,
        *,
        blueprint: dict,
        integrated: str,
        scenes,
        scene_count: int,
    ) -> list[dict]:
        issues: list[dict] = []

        required_fields = ["scene_breakdown", "integrated_scenario"]
        for field in required_fields:
            if field not in blueprint or not blueprint[field]:
                issues.append(
                    {
                        "severity": "MAJOR",
                        "category": "structure",
                        "issue": f"필수 필드 누락: {field}",
                        "evidence": f"{field} 필드가 없거나 비어있음",
                        "fix_hint": f"{field} 필드를 올바르게 작성",
                    }
                )

        if len(integrated) < self.min_chars:
            issues.append(
                {
                    "severity": "MAJOR",
                    "category": "structure",
                    "issue": f"분량 부족: {len(integrated)}자 < {self.min_chars}자",
                    "evidence": "integrated_scenario 길이 부족",
                    "fix_hint": f"최소 {self.min_chars}자 이상 작성",
                }
            )

        if scene_count < 3:
            issues.append(
                {
                    "severity": "MAJOR",
                    "category": "structure",
                    "issue": f"씬 부족: {scene_count}개 < 3개",
                    "evidence": f"scene_breakdown에 {scene_count}개 씬만 있음",
                    "fix_hint": "최소 3개 이상의 씬으로 구성",
                }
            )

        if scene_count <= 0:
            return issues

        shallow_count = 0
        for scene_value in self._iter_scene_entries(scenes):
            if isinstance(scene_value, str):
                shallow_count += 1
                continue
            if not isinstance(scene_value, dict):
                shallow_count += 1
                continue
            has_goal = bool(
                scene_value.get("goal")
                or scene_value.get("목표")
                or scene_value.get("summary")
                or scene_value.get("요약")
            )
            if not has_goal:
                shallow_count += 1

        if shallow_count > 0:
            issues.append(
                {
                    "severity": "MINOR",
                    "category": "structure",
                    "issue": f"씬 구조 미비: {shallow_count}/{scene_count}개 씬에 goal/summary 없음",
                    "evidence": "scene_breakdown 항목에 goal 또는 summary 필드 필요",
                    "fix_hint": "각 씬에 goal/summary를 명시하여 intent를 보존",
                }
            )

        return issues

    def _collect_fidelity_prevalidation_issues(self, *, integrated: str, arc_data) -> list[dict]:
        if not arc_data or not integrated:
            return []

        arc_state_constraints = (arc_data.get("state_constraints") or {}) if isinstance(arc_data, dict) else {}
        arc_relationship_changes = arc_state_constraints.get("relationship_changes") or []
        arc_npcs: set[str] = set()
        for relationship in arc_relationship_changes:
            if isinstance(relationship, dict):
                npc_name = relationship.get("target") or relationship.get("npc")
                if npc_name and isinstance(npc_name, str) and len(npc_name) >= 2:
                    arc_npcs.add(npc_name)

        if not arc_npcs:
            return []

        mentioned_count = sum(1 for npc_name in arc_npcs if npc_name in integrated)
        if mentioned_count > 0:
            return []

        return [
            {
                "severity": "MINOR",
                "category": "fidelity",
                "issue": f"intent 불일치: Arc 관계 변화 NPC {len(arc_npcs)}명 blueprint 미언급",
                "evidence": f"NPC: {', '.join(list(arc_npcs)[:3])}",
                "fix_hint": "Arc 관계 변화 NPC가 blueprint 시나리오에 등장해야 함",
            }
        ]

    def _collect_arc_compliance_prevalidation_issues(self, *, constraint_block: dict, integrated: str) -> list[dict]:
        stop_line = constraint_block.get("stop_line", {}) if isinstance(constraint_block, dict) else {}
        stop_content = stop_line.get("content", "") if isinstance(stop_line, dict) else ""
        if not stop_content or len(stop_content) <= 10:
            return []

        stop_violation = self._detect_stop_line_violation(stop_content, integrated)
        if not stop_violation:
            return []

        evidence = stop_violation.get("evidence", "") or stop_content[:30].strip()
        overlap_tokens = stop_violation.get("overlap_tokens") or []
        evidence_suffix = ""
        if overlap_tokens:
            evidence_suffix = f" (overlap: {', '.join(overlap_tokens)})"

        return [
            {
                "severity": "CRITICAL",
                "category": "arc_compliance",
                "issue": "정지선 위반: 다음 화 내용 포함",
                "evidence": f"'{evidence}...'가 본문에서 발견됨{evidence_suffix}",
                "fix_hint": "다음 화 내용을 제거하고 이번 화 범위 내에서만 작성",
            }
        ]

    def _collect_continuity_prevalidation_issues(
        self,
        *,
        blueprint: dict,
        prev_blueprint: dict | None,
    ) -> list[dict]:
        if not isinstance(prev_blueprint, dict):
            return []

        prev_end_location = self._extract_prev_blueprint_end_location(prev_blueprint)
        curr_start_location = blueprint.get("start_location", blueprint.get("location", ""))
        if not prev_end_location or not curr_start_location:
            return []
        if prev_end_location == curr_start_location:
            return []
        if self._is_location_transition_valid(prev_end_location, curr_start_location):
            return []

        return [
            {
                "severity": "MAJOR",
                "category": "continuity",
                "issue": f"위치 불연속: {prev_end_location} → {curr_start_location}",
                "evidence": "이전 화 종료 위치와 현재 화 시작 위치 불일치",
                "fix_hint": "위치 이동 경위를 설명하거나 시작 위치 수정",
            }
        ]

    @staticmethod
    def _build_python_prevalidation_result(issues: list[dict]) -> dict:
        has_critical = any(issue["severity"] == "CRITICAL" for issue in issues)
        major_count = sum(1 for issue in issues if issue["severity"] == "MAJOR")
        critical_items = [issue["issue"] for issue in issues if issue["severity"] == "CRITICAL"]
        return {
            "issues": issues,
            "has_critical": has_critical,
            "has_major_excess": major_count >= 3,
            "critical_summary": "; ".join(critical_items) if critical_items else "",
        }

    def _python_pre_validate(
        self,
        blueprint: dict,
        constraint_block: dict,
        prev_blueprint: dict | None,
        state_tracker=None,  # [V60.95] 고밀도 HUD 검증용
        arc_data=None,  # [ValidationHardening] intent fidelity check용
    ) -> dict:
        """Python 사전검사 (무료, 빠름)"""
        blueprint = blueprint if isinstance(blueprint, dict) else {}
        integrated = self._normalize_integrated_scenario(blueprint.get("integrated_scenario", ""))
        scenes = blueprint.get("scene_breakdown", {})
        scene_count = self._count_scene_entries(scenes)

        issues: list[dict] = []
        issues.extend(
            self._collect_structure_prevalidation_issues(
                blueprint=blueprint,
                integrated=integrated,
                scenes=scenes,
                scene_count=scene_count,
            )
        )
        issues.extend(self._collect_fidelity_prevalidation_issues(integrated=integrated, arc_data=arc_data))
        issues.extend(
            self._collect_arc_compliance_prevalidation_issues(
                constraint_block=constraint_block,
                integrated=integrated,
            )
        )
        issues.extend(
            self._collect_continuity_prevalidation_issues(
                blueprint=blueprint,
                prev_blueprint=prev_blueprint,
            )
        )
        return self._build_python_prevalidation_result(issues)

    def _is_location_transition_valid(self, prev_loc: str, curr_loc: str) -> bool:
        """위치 전환이 유효한지 체크"""
        prev_area = self._extract_area(prev_loc)
        curr_area = self._extract_area(curr_loc)

        if prev_area and curr_area and prev_area == curr_area:
            return True

        if prev_loc in curr_loc or curr_loc in prev_loc:
            return True

        return False

    def _extract_area(self, location: str) -> str:
        """위치에서 대분류 지역 추출"""
        match = re.search(r"^([가-힣]{2,5})", location)
        return match.group(1) if match else ""


def create_unified_blueprint_validator(context, client, model_tier: str = "gemini-2.5-flash"):
    """UnifiedBlueprintValidator 생성 헬퍼"""
    return UnifiedBlueprintValidator(context, client, model_tier)
