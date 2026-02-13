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
from typing import Dict, List, Any, Optional, Tuple

from .base_agent import _get_agent_default_model


# Blueprint 검증용 최소 분량
BLUEPRINT_MIN_CHARS = 800  # integrated_scenario 최소 길이


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
        self.model_tier = model_tier or _get_agent_default_model("unified_blueprint_validator") or "gemini-2.5-flash"
        self.min_chars = BLUEPRINT_MIN_CHARS

    def validate(
        self,
        blueprint: Dict,
        arc_data: Dict,
        constraint_block: Dict,
        prev_blueprint: Optional[Dict] = None,
        director=None,  # [V60.80] Director 인스턴스 (최종 판정용)
        working_ep: int = 1,
        arc_idx: int = 0,
        entity_registry: Optional[Dict] = None,  # [V61] Entity 일관성 검증용
        state_tracker=None,  # [V60.96] StateTracker (죽은 NPC 검증용)
        all_candidates: Optional[List[Dict]] = None  # [V60.85] 전체 후보 리스트
    ) -> Tuple[str, Dict]:
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
            logging.info(f"🎭 [V60.85] Director 비교 선택 모드 ({len(all_candidates)}개 후보)")

            compare_result = director.compare_and_select_blueprint(
                candidates=all_candidates,
                arc_data=arc_data,
                ep_num=working_ep,
                prev_blueprint=prev_blueprint,
                entity_registry=entity_registry,
                state_tracker=state_tracker
            )

            verdict = compare_result.get("decision", "REJECT")
            selected_bp = compare_result.get("selected_blueprint")

            result = {
                "verdict": verdict,
                "phase": "director_compare",
                "issues": [],
                "summary": compare_result.get("reason", ""),
                "score": compare_result.get("score", 0),
                "feedback": compare_result.get("feedback", ""),
                "confidence": 0.9 if compare_result.get("score", 0) >= 70 else 0.6,
                "selected_index": compare_result.get("selected_index", 0),
                "selected_blueprint": selected_bp,
                "comparison_notes": compare_result.get("comparison_notes", "")
            }

            status = "✅ PASS" if verdict == "PASS" else "❌ REJECT"
            logging.info(f"{status} [Director] 후보 {compare_result.get('selected_index', 0)+1} 선택, 점수: {compare_result.get('score', 0)}")

            return verdict, result

        # ═══════════════════════════════════════════════════════════════
        # Phase A: Python 사전검사 (무료) - 경고만, REJECT 권한 없음
        # ═══════════════════════════════════════════════════════════════
        pre_result = self._python_pre_validate(blueprint, constraint_block, prev_blueprint, state_tracker)

        # [V60.96] 죽은 NPC 등장 체크 - 경고로 Director에게 전달 (디렉터주권주의)
        # [V60.97] arc_no 추출 (타임라인 비교용)
        arc_no = arc_data.get("arc_no", 0) if arc_data else arc_idx
        if arc_no <= 0:
            arc_no = arc_idx

        dead_npc_violations = []
        if state_tracker:
            dead_npc_violations = state_tracker.check_dead_npc_in_blueprint(blueprint, working_ep, arc_no)
            if dead_npc_violations:
                violation_names = [v["npc_name"] for v in dead_npc_violations]
                logging.info(f"💀 [V60.96] 죽은 NPC 감지 → Director에게 전달: {', '.join(violation_names)}")
                # Director 주의 포인트로 추가 (Python은 REJECT 안 함)
                pre_result["issues"].append({
                    "severity": "CRITICAL",
                    "category": "dead_npc",
                    "issue": f"죽은 NPC 등장: {', '.join(violation_names)}",
                    "evidence": dead_npc_violations[0]["reason"],
                    "fix_hint": "사망한 NPC는 회상/언급만 가능"
                })
                pre_result["has_critical"] = True

        # [V60.80] Python은 경고만 - REJECT 권한 없음, Director가 최종 판정
        if pre_result["has_critical"]:
            logging.warning(f"⚠️ [PreValidator] Python 경고: CRITICAL 이슈 발견 (Director가 최종 판정)")
            for issue in pre_result["issues"]:
                if issue.get("severity") == "CRITICAL":
                    logging.info(f"- {issue.get('issue', '?')}")
        elif pre_result["issues"]:
            logging.info(f"⚠️ [PreValidator] Python 경고: {len(pre_result['issues'])}개 이슈 (Director가 최종 판정)")

        # ═══════════════════════════════════════════════════════════════
        # Phase B: Director 최종 판정 (디렉터주권주의) - 항상 호출
        # ═══════════════════════════════════════════════════════════════
        if director is None:
            # [V60.80] Director 없으면 PASS 처리 (Python은 REJECT 권한 없음)
            logging.info(f"⚠️ [PreValidator] Director 없음 - 경고 출력 후 PASS 처리")
            logging.warning(f"(Python은 REJECT 권한 없음, Director 전달 필수)")
            return "PASS", {
                "verdict": "PASS",
                "phase": "no_director",
                "issues": pre_result["issues"],
                "summary": "Director 없이 통과 (Python 경고만)",
                "feedback": ""
            }

        logging.info(f"🎬 [Director] Blueprint 최종 판정 중...")

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
            total_eps = arc_data.get("ep_count", 5)

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

            # Director.audit_manuscript() 호출
            director_result = director.audit_manuscript(
                ep_num=working_ep,
                manuscript=manuscript_with_focus,  # 주의 포인트 포함
                arc_doc=arc_tactical_doc,
                history_summary=str(self.context.get_causal_history_summary()) if hasattr(self.context, 'get_causal_history_summary') else "",
                prev_full_text=prev_ms_ending,
                arc_pos=arc_pos,
                total_eps=total_eps,
                target_len=self.min_chars,  # Blueprint용 짧은 기준
                retry_count=0,
                entity_registry=entity_registry,  # [V61] Entity 일관성 검증
                state_tracker=state_tracker  # [V61.5] 죽은 NPC 검증 (BUG FIX: 누락되어 있었음)
            )

            # Director 결과 처리
            director_verdict = director_result.get("decision", "PASS")
            director_reason = director_result.get("reason", "")
            director_feedback = director_result.get("feedback", "")
            director_score = director_result.get("score", 50)

            # 이슈 병합 (사전검사 + Director)
            all_issues = pre_result["issues"][:]
            if director_verdict == "REJECT":
                all_issues.append({
                    "severity": "MAJOR",
                    "category": "director",
                    "issue": f"Director REJECT: {director_reason}",
                    "evidence": director_feedback,
                    "fix_hint": director_feedback
                })

            # Director의 verdict가 최종 결정!
            final_verdict = director_verdict

            result = {
                "verdict": final_verdict,
                "phase": "director",
                "issues": all_issues,
                "summary": director_reason,
                "score": director_score,
                "feedback": director_feedback if final_verdict == "REJECT" else "",
                "pre_issues": len(pre_result["issues"]),
                "confidence": 0.9 if director_score >= 70 else 0.6
            }

            status = "✅ PASS" if final_verdict == "PASS" else "❌ REJECT"
            logging.info(f"{status} [Director] 점수: {director_score}, 사유: {director_reason[:50]}...")

            return final_verdict, result

        except Exception as e:
            logging.warning(f"⚠️ [Director] 오류: {str(e)[:50]}")
            # [V60.80] Director 오류 시에도 Python은 REJECT 권한 없음
            # Director 재시도 유도를 위해 REJECT 반환하되, 피드백으로 오류 원인 전달
            return "REJECT", {
                "verdict": "REJECT",
                "phase": "director_error",
                "issues": pre_result["issues"],
                "summary": f"Director 호출 오류 - 재시도 필요",
                "feedback": f"[Director 오류로 인한 재시도]\n오류: {str(e)[:100]}\n다시 생성해 주세요."
            }

    def _python_pre_validate(
        self,
        blueprint: Dict,
        constraint_block: Dict,
        prev_blueprint: Optional[Dict],
        state_tracker=None  # [V60.95] 고밀도 HUD 검증용
    ) -> Dict:
        """Python 사전검사 (무료, 빠름)"""
        issues = []

        # 1. 필수 필드 체크
        required_fields = ["scene_breakdown", "integrated_scenario"]
        for field in required_fields:
            if field not in blueprint or not blueprint[field]:
                issues.append({
                    "severity": "MAJOR",
                    "category": "structure",
                    "issue": f"필수 필드 누락: {field}",
                    "evidence": f"{field} 필드가 없거나 비어있음",
                    "fix_hint": f"{field} 필드를 올바르게 작성"
                })

        # 2. 분량 체크
        integrated = blueprint.get("integrated_scenario", "")
        if not isinstance(integrated, str):
            integrated = str(integrated) if integrated else ""

        if len(integrated) < self.min_chars:
            issues.append({
                "severity": "MAJOR",
                "category": "structure",
                "issue": f"분량 부족: {len(integrated)}자 < {self.min_chars}자",
                "evidence": f"integrated_scenario 길이 부족",
                "fix_hint": f"최소 {self.min_chars}자 이상 작성"
            })

        # 3. 씬 개수 체크
        scenes = blueprint.get("scene_breakdown", {})
        if isinstance(scenes, dict):
            scene_count = len(scenes)
        elif isinstance(scenes, list):
            scene_count = len(scenes)
        else:
            scene_count = 0

        if scene_count < 3:
            issues.append({
                "severity": "MAJOR",
                "category": "structure",
                "issue": f"씬 부족: {scene_count}개 < 3개",
                "evidence": f"scene_breakdown에 {scene_count}개 씬만 있음",
                "fix_hint": "최소 3개 이상의 씬으로 구성"
            })

        # 4. 정지선 위반 체크 (CRITICAL)
        stop_line = constraint_block.get("stop_line", {})
        stop_content = stop_line.get("content", "")
        if stop_content and len(stop_content) > 10:
            stop_keywords = stop_content[:30].strip()
            if stop_keywords in integrated:
                issues.append({
                    "severity": "CRITICAL",
                    "category": "arc_compliance",
                    "issue": f"정지선 위반: 다음 화 내용 포함",
                    "evidence": f"'{stop_keywords}...'가 본문에서 발견됨",
                    "fix_hint": "다음 화 내용을 제거하고 이번 화 범위 내에서만 작성"
                })

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
                        issues.append({
                            "severity": "MAJOR",
                            "category": "continuity",
                            "issue": f"위치 불연속: {prev_end_location} → {curr_start_location}",
                            "evidence": "이전 화 종료 위치와 현재 화 시작 위치 불일치",
                            "fix_hint": "위치 이동 경위를 설명하거나 시작 위치 수정"
                        })

        has_critical = any(i["severity"] == "CRITICAL" for i in issues)
        major_count = sum(1 for i in issues if i["severity"] == "MAJOR")
        critical_items = [i["issue"] for i in issues if i["severity"] == "CRITICAL"]

        return {
            "issues": issues,
            "has_critical": has_critical,
            "has_major_excess": major_count >= 3,
            "critical_summary": "; ".join(critical_items) if critical_items else ""
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
        match = re.search(r'^([가-힣]{2,5})', location)
        return match.group(1) if match else ""

    def _generate_feedback(self, issues: List[Dict]) -> str:
        """재생성용 피드백 생성"""
        if not issues:
            return ""

        lines = ["[검증 실패 - 다음 문제 해결 필요]", ""]

        critical = [i for i in issues if i.get("severity") == "CRITICAL"]
        if critical:
            lines.append("[CRITICAL - 필수 수정]:")
            for c in critical:
                lines.append(f"  - {c.get('issue', '?')}")
                if c.get("fix_hint"):
                    lines.append(f"    -> {c['fix_hint']}")

        major = [i for i in issues if i.get("severity") == "MAJOR"]
        if major:
            lines.append("")
            lines.append("[MAJOR - 수정 권장]:")
            for m in major[:3]:
                lines.append(f"  - {m.get('issue', '?')}")

        return "\n".join(lines)


def create_unified_blueprint_validator(context, client, model_tier: str = "gemini-2.5-flash"):
    """UnifiedBlueprintValidator 생성 헬퍼"""
    return UnifiedBlueprintValidator(context, client, model_tier)
