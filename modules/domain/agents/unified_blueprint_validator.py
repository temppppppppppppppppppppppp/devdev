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

    def validate(
        self,
        blueprint: dict,
        arc_data: dict,
        constraint_block: dict,
        prev_blueprint: dict | None = None,
        director=None,  # [V60.80] Director 인스턴스 (최종 판정용)
        working_ep: int = 1,
        arc_idx: int = 0,
        entity_registry: dict | None = None,  # [V61] Entity 일관성 검증용
        state_tracker=None,  # [V60.96] StateTracker (죽은 NPC 검증용)
        all_candidates: list[dict] | None = None,  # [V60.85] 전체 후보 리스트
        prev_hud: dict | None = None,  # [TF-4] 직전 HUD (BlockingValidator consistency checks용)
    ) -> tuple[str, dict]:
        """
        Blueprint 통합 검증 (사전검사 + Director 최종 판정)

        [V60.85] all_candidates가 있으면 Director가 비교 선택

        Args:
            blueprint: 검증할 Blueprint (단일 후보 또는 대표 후보)
            arc_data: 현재 Arc 데이터
            constraint_block: 제약 조건 블록
            prev_blueprint: 직전 Blueprint
            director: Director 에이전트 (최종 판정)
            working_ep: 현재 에피소드 번호
            arc_idx: Arc 인덱스
            entity_registry: [V61] Entity 일관성 검증용
            state_tracker: [V60.96] StateTracker (죽은 NPC 검증용)
            all_candidates: [V60.85] 전체 후보 리스트 (있으면 Director 비교 선택)

        Returns:
            (verdict, result) - "PASS"/"REJECT", 상세 결과
        """
        # ═══════════════════════════════════════════════════════════════
        # [V60.85] 여러 후보가 있으면 Director 비교 선택 모드
        # ═══════════════════════════════════════════════════════════════
        if all_candidates and len(all_candidates) > 1 and director:
            logging.warning(f" [V60.85] Director 비교 선택 모드 ({len(all_candidates)}개 후보)")

            compare_pre_results: list[dict] = []
            candidate_advisories: list[dict] = []
            for idx, candidate in enumerate(all_candidates):
                _pre_result, _advisory = self._prepare_compare_candidate(
                    candidate,
                    candidate_index=idx,
                    arc_data=arc_data,
                    constraint_block=constraint_block,
                    prev_blueprint=prev_blueprint,
                    state_tracker=state_tracker,
                    working_ep=working_ep,
                    arc_idx=arc_idx,
                )
                compare_pre_results.append(_pre_result)
                candidate_advisories.append(_advisory)

            compare_result = director.compare_and_select_blueprint(
                candidates=all_candidates,
                arc_data=arc_data,
                ep_num=working_ep,
                prev_blueprint=prev_blueprint,
                entity_registry=entity_registry,
                state_tracker=state_tracker,
            )

            verdict = compare_result.get("decision", "REJECT")
            selected_idx = _safe_int(compare_result.get("selected_index", 0), 0)
            if selected_idx < 0 or selected_idx >= len(all_candidates):
                selected_idx = 0
            selected_bp = compare_result.get("selected_blueprint")
            if not isinstance(selected_bp, dict) and 0 <= selected_idx < len(all_candidates):
                selected_bp = all_candidates[selected_idx]

            _contradictions = compare_result.get("contradictions", [])
            if not isinstance(_contradictions, list):
                _contradictions = []

            if 0 <= selected_idx < len(compare_pre_results):
                selected_pre_result = compare_pre_results[selected_idx]
            else:
                selected_pre_result = {"issues": [], "has_critical": False}
            selected_candidate_advisory = (
                candidate_advisories[selected_idx]
                if 0 <= selected_idx < len(candidate_advisories)
                else {"candidate_index": selected_idx, "quality_risk": False}
            )
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
                "contradictions": _contradictions,
                "fix_scope": compare_result.get("fix_scope", ""),  # [TF-33] Director 수정 범위 전파
                "fix_scope_reasoning": compare_result.get("fix_scope_reasoning", ""),  # [TF-33]
                "selection_reason": selection_reason,
                "verdict_reason": verdict_reason,
                "quality_risk": quality_risk,
                "revision_required": revision_required,
                "candidate_count": len(all_candidates),
                "candidate_advisories": candidate_advisories,
                "selected_candidate_advisory": selected_candidate_advisory,
            }

            status = "✅ PASS" if verdict in ("PASS", "PASS_WITH_FIX", "PASS_WITH_WARNING") else "❌ REJECT"
            logging.info(f"{status} [Director] 후보 {selected_idx + 1} 선택, 점수: {compare_result.get('score', 0)}")

            return verdict, result

        # ═══════════════════════════════════════════════════════════════
        # Phase A: Python 사전검사 (무료) - 경고만, REJECT 권한 없음
        # ═══════════════════════════════════════════════════════════════
        pre_result = self._python_pre_validate(
            blueprint, constraint_block, prev_blueprint, state_tracker, arc_data=arc_data
        )

        # [V60.96] 죽은 NPC 등장 체크 - 경고로 Director에게 전달 (디렉터주권주의)
        # [V60.97] arc_no 추출 (타임라인 비교용)
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
            logging.warning(f" [V60.96] 죽은 NPC 감지 → Director에게 전달: {', '.join(violation_names)}")

        # [V60.80] Python은 경고만 - REJECT 권한 없음, Director가 최종 판정
        if pre_result["has_critical"]:
            logging.warning(" [PreValidator] Python 경고: CRITICAL 이슈 발견 (Director가 최종 판정)")
            for issue in pre_result["issues"]:
                if issue.get("severity") == "CRITICAL":
                    logging.warning(f"- {issue.get('issue', '?')}")
        elif pre_result["issues"]:
            logging.warning(f" [PreValidator] Python 경고: {len(pre_result['issues'])}개 이슈 (Director가 최종 판정)")

        # ═══════════════════════════════════════════════════════════════
        # Phase B: Director 최종 판정 (디렉터주권주의) - 항상 호출
        # ═══════════════════════════════════════════════════════════════
        if director is None:
            # [TF-36] 대원칙 3: Director 없으면 REJECT — 디렉터 주권주의 위반 방지
            logging.error("❌ [대원칙3] Director가 None — Blueprint 판정 불가, REJECT 처리")
            return "REJECT", {
                "verdict": "REJECT",
                "phase": "no_director",
                "issues": pre_result["issues"],
                "summary": "Director 에이전트 미주입 — 디렉터 주권주의에 의해 REJECT",
                "feedback": "Director 없이는 Blueprint를 승인할 수 없습니다.",
                "score": 0,
            }

        logging.warning(" [Director] Blueprint 최종 판정 중...")

        try:
            # Director 호출을 위한 데이터 준비
            integrated_scenario = blueprint.get("integrated_scenario", "")
            if not isinstance(integrated_scenario, str):
                integrated_scenario = str(integrated_scenario) if integrated_scenario else ""

            arc_tactical_doc = arc_data.get("tactical_doc", "")
            if isinstance(arc_tactical_doc, dict):
                arc_tactical_doc = json.dumps(arc_tactical_doc, ensure_ascii=False)

            # 이전 화 엔딩 추출
            prev_ms_ending = ""
            if prev_blueprint:
                prev_ms_ending = prev_blueprint.get("ending_hook", "")

            # Arc 내 위치 계산
            ep_start = arc_data.get("ep_start", working_ep)
            arc_pos = working_ep - ep_start + 1
            total_eps = arc_data.get("ep_count", Stage2Limits.DEFAULT_EP_COUNT)

            # [V60.80] Python 경고를 Director 주의 포인트로 전달
            ensemble_meta = blueprint.get("_ensemble_meta", {})
            python_warnings = ensemble_meta.get("python_warnings", [])

            # 경고가 있으면 manuscript 앞에 주의 포인트 추가
            if python_warnings:
                focus_header = "[⚠️ Director 주의 포인트 - 특히 집중 검토 필요]\n"
                for w in python_warnings:
                    focus_header += f"  - {w.get('message', '?')}: {w.get('focus', '')}\n"
                focus_header += "\n[검토 대상 Blueprint]\n"
                manuscript_with_focus = focus_header + integrated_scenario
            else:
                manuscript_with_focus = integrated_scenario

            # [TF-4] validation_context 보강 — encyclopedia.npcs + prev_hud 주입
            _bp_vc = {"skip_continuity": True, "mode": "BLUEPRINT"}
            if state_tracker:
                _enc_npcs = []
                for _npc_name, _npc_info in getattr(state_tracker, "npc_registry", {}).items():
                    _enc_npcs.append(
                        {
                            "name": _npc_name,
                            "status": _npc_info.get("status", "alive"),
                            "death_arc": _npc_info.get("death_arc"),
                            "aliases": _npc_info.get("aliases", []),
                        }
                    )
                _bp_vc["encyclopedia"] = {"npcs": _enc_npcs}

            # [TF-4] prev_hud 주입 — 호출자(stage3_orchestrator)가 ctx.sys.hud.pro_root에서 추출하여 전달
            # ContinuityValidator는 skip_continuity=True일 때 최상단에서 PASS 반환하므로 안전
            # BlockingValidator의 physical_capability/authority_exercise에서 사용
            if isinstance(prev_hud, dict) and prev_hud:
                _bp_vc["prev_hud"] = prev_hud
                _bp_vc["martial_hud"] = prev_hud

            # Director.audit_manuscript() 호출 (Blueprint 모드)
            director_result = director.audit_manuscript(
                ep_num=working_ep,
                manuscript=manuscript_with_focus,  # 주의 포인트 포함
                arc_doc=arc_tactical_doc,
                history_summary=self._safe_causal_history(),
                prev_full_text=prev_ms_ending,
                arc_pos=arc_pos,
                total_eps=total_eps,
                target_len=self.min_chars,  # Blueprint용 짧은 기준
                retry_count=0,
                entity_registry=entity_registry,  # [V61] Entity 일관성 검증
                state_tracker=state_tracker,  # [V61.5] 죽은 NPC 검증
                validation_context=_bp_vc,
            )

            # Director 결과 처리
            director_verdict = director_result.get("decision", "PASS")
            director_reason = director_result.get("reason", "")
            director_feedback = director_result.get("feedback", "")
            director_score = _safe_int(director_result.get("score", 50), 50)

            # 이슈 병합 (사전검사 + Director)
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

            # Director의 verdict가 최종 결정!
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
                "score_breakdown": {  # [TF-S3-11] patch mode 피드백용
                    "director_score": director_score,
                    "pre_issues_count": len(pre_result["issues"]),
                },
                "feedback": director_feedback
                if final_verdict in ("REJECT", "PASS_WITH_FIX")
                else "",  # [TF-34] PASS_WITH_FIX 피드백 보존
                "pre_issues": len(pre_result["issues"]),
                "confidence": 0.9 if director_score >= 70 else 0.6,
                "fix_scope": director_result.get("fix_scope", ""),  # [TF-33] Director 수정 범위 전파
                "fix_scope_reasoning": director_result.get("fix_scope_reasoning", ""),  # [TF-33]
                "re_slice_instruction": director_result.get("re_slice_instruction", ""),  # [TF-35] 수정 지시 전파
                "selection_reason": director_result.get("selection_reason", "") or director_reason,
                "verdict_reason": director_result.get("verdict_reason", "") or director_reason,
                "quality_risk": quality_risk,
                "revision_required": final_verdict in ("PASS_WITH_FIX", "PASS_WITH_WARNING"),
                "candidate_count": 1,
            }

            status = "✅ PASS" if final_verdict in ("PASS", "PASS_WITH_FIX") else "❌ REJECT"
            logging.warning(f"{status} [Director] 점수: {director_score}, 사유: {(director_reason or '')[:50]}...")

            return final_verdict, result

        except Exception as e:
            logging.warning(f" [Director] 오류: {str(e)[:50]}")
            # [V60.80] Director 오류 시에도 Python은 REJECT 권한 없음
            # Director 재시도 유도를 위해 REJECT 반환하되, 피드백으로 오류 원인 전달
            return "REJECT", {
                "verdict": "REJECT",
                "phase": "director_error",
                "issues": pre_result["issues"],
                "summary": "Director 호출 오류 - 재시도 필요",
                "feedback": f"[Director 오류로 인한 재시도]\n오류: {str(e)[:100]}\n다시 생성해 주세요.",
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
        issues = []

        # 1. 필수 필드 체크
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

        # 2. 분량 체크
        integrated = blueprint.get("integrated_scenario", "")
        if not isinstance(integrated, str):
            integrated = str(integrated) if integrated else ""

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

        # 3. 씬 개수 체크
        scenes = blueprint.get("scene_breakdown", {})
        if isinstance(scenes, dict):
            scene_count = len(scenes)
        elif isinstance(scenes, list):
            scene_count = len(scenes)
        else:
            scene_count = 0

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

        # [ValidationHardening] 3-A. 씬 내부 구조 검사
        if scene_count > 0:
            _shallow = 0
            _scene_items = scenes.values() if isinstance(scenes, dict) else scenes
            for _sv in _scene_items:
                if isinstance(_sv, str):
                    _shallow += 1
                elif isinstance(_sv, dict):
                    _has_goal = bool(_sv.get("goal") or _sv.get("목표") or _sv.get("summary") or _sv.get("요약"))
                    if not _has_goal:
                        _shallow += 1
                else:
                    _shallow += 1
            if _shallow > 0:
                issues.append(
                    {
                        "severity": "MINOR",
                        "category": "structure",
                        "issue": f"씬 구조 미비: {_shallow}/{scene_count}개 씬에 goal/summary 없음",
                        "evidence": "scene_breakdown 항목에 goal 또는 summary 필드 필요",
                        "fix_hint": "각 씬에 goal/summary를 명시하여 intent를 보존",
                    }
                )

        # [ValidationHardening] 3-C. Intent fidelity — Arc NPC mention check
        if arc_data and integrated:
            _arc_sc = (arc_data.get("state_constraints") or {}) if isinstance(arc_data, dict) else {}
            _arc_rels = _arc_sc.get("relationship_changes") or []
            _arc_npcs: set[str] = set()
            for _r in _arc_rels:
                if isinstance(_r, dict):
                    _n = _r.get("target") or _r.get("npc")
                    if _n and isinstance(_n, str) and len(_n) >= 2:
                        _arc_npcs.add(_n)
            if _arc_npcs:
                _mentioned = sum(1 for n in _arc_npcs if n in integrated)
                if _mentioned == 0:
                    issues.append(
                        {
                            "severity": "MINOR",
                            "category": "fidelity",
                            "issue": f"intent 불일치: Arc 관계 변화 NPC {len(_arc_npcs)}명 blueprint 미언급",
                            "evidence": f"NPC: {', '.join(list(_arc_npcs)[:3])}",
                            "fix_hint": "Arc 관계 변화 NPC가 blueprint 시나리오에 등장해야 함",
                        }
                    )

        # 4. 정지선 위반 체크 (CRITICAL)
        stop_line = constraint_block.get("stop_line", {})
        stop_content = stop_line.get("content", "")
        if stop_content and len(stop_content) > 10:
            stop_violation = self._detect_stop_line_violation(stop_content, integrated)
            if stop_violation:
                evidence = stop_violation.get("evidence", "") or stop_content[:30].strip()
                overlap_tokens = stop_violation.get("overlap_tokens") or []
                evidence_suffix = ""
                if overlap_tokens:
                    evidence_suffix = f" (overlap: {', '.join(overlap_tokens)})"
                issues.append(
                    {
                        "severity": "CRITICAL",
                        "category": "arc_compliance",
                        "issue": "정지선 위반: 다음 화 내용 포함",
                        "evidence": f"'{evidence}...'가 본문에서 발견됨{evidence_suffix}",
                        "fix_hint": "다음 화 내용을 제거하고 이번 화 범위 내에서만 작성",
                    }
                )

        # 5. 연속성 체크 (위치)
        if prev_blueprint:
            prev_end_location = prev_blueprint.get("end_location", "")
            if not prev_end_location:
                prev_scenes = prev_blueprint.get("scene_breakdown", {})
                if prev_scenes and isinstance(prev_scenes, dict):
                    scene_keys = sorted(prev_scenes.keys())
                    if scene_keys:
                        last_scene = prev_scenes.get(scene_keys[-1], {})
                        prev_end_location = last_scene.get("location", "") if isinstance(last_scene, dict) else ""

            curr_start_location = blueprint.get("start_location", blueprint.get("location", ""))

            if prev_end_location and curr_start_location:
                if prev_end_location != curr_start_location:
                    if not self._is_location_transition_valid(prev_end_location, curr_start_location):
                        issues.append(
                            {
                                "severity": "MAJOR",
                                "category": "continuity",
                                "issue": f"위치 불연속: {prev_end_location} → {curr_start_location}",
                                "evidence": "이전 화 종료 위치와 현재 화 시작 위치 불일치",
                                "fix_hint": "위치 이동 경위를 설명하거나 시작 위치 수정",
                            }
                        )

        has_critical = any(i["severity"] == "CRITICAL" for i in issues)
        major_count = sum(1 for i in issues if i["severity"] == "MAJOR")
        critical_items = [i["issue"] for i in issues if i["severity"] == "CRITICAL"]

        return {
            "issues": issues,
            "has_critical": has_critical,
            "has_major_excess": major_count >= 3,
            "critical_summary": "; ".join(critical_items) if critical_items else "",
        }

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
