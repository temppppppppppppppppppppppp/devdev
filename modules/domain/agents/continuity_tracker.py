"""
[V64.P3] ContinuityTrackerIntegration — V49.7 품질 향상 트래커 통합 모듈

ContinuityInspector God Object 분해의 네 번째 모듈.
StateDeltaTracker, RelationshipTracker, PowerScalingTracker,
ForeshadowingTracker 등 V49.7 품질 향상 트래커 초기화 및 검증을 담당.
inspector reference를 통해 BaseAgent 메서드 및 공유 상태 접근.
"""

from typing import Any

# [V49.7] 품질 향상 모듈 임포트
try:
    from modules.core.foreshadow_tracker import ForeshadowTracker
    from modules.core.information_diffusion import InformationDiffusion
    from modules.core.power_scaling import PowerScalingTracker
    from modules.core.relationship_tracker import RelationshipTracker
    from modules.core.state_delta_tracker import StateDeltaTracker

    V49_7_MODULES_AVAILABLE = True
except ImportError:
    V49_7_MODULES_AVAILABLE = False


class ContinuityTrackerIntegration:
    """
    [V64.P3] ContinuityInspector에서 분리된 V49.7 트래커 통합 모듈

    담당:
    - _init_v49_7_trackers(): 트래커 초기화
    - _validate_with_v49_7_trackers(): 트래커 기반 검증
    - _check_relationship_with_tracker(): 관계 전이 검증
    - _check_power_with_tracker(): 파워 스케일링 검증
    - _check_foreshadowing_with_tracker(): 복선 상태 검증
    - _check_state_with_tracker(): 내공/부상 상태 검증
    - load_trackers_from_db(): DB에서 트래커 상태 로드
    """

    def __init__(self, inspector) -> None:
        """
        Args:
            inspector: ContinuityInspector 인스턴스 (BaseAgent 상속, 공유 상태 접근용)
        """
        self._ci = inspector

    def init_trackers(self) -> None:
        """
        [V49.7] 품질 향상 모듈 트래커 초기화

        ContinuityInspector.__init__에서 호출됨.
        inspector에 트래커 인스턴스를 직접 설정.
        """
        if V49_7_MODULES_AVAILABLE:
            self._ci.state_tracker = StateDeltaTracker(
                initial_energy=100, protagonist_name=self._get_protagonist_name()
            )
            self._ci.relationship_tracker = RelationshipTracker()
            self._ci.power_tracker = PowerScalingTracker()
            self._ci.foreshadow_tracker = ForeshadowTracker()

            try:
                self._ci.info_diffusion = InformationDiffusion(self._ci.context)
            except Exception:
                self._ci.info_diffusion = None

            self._ci.v49_7_enabled = True
        else:
            self._ci.state_tracker = None
            self._ci.relationship_tracker = None
            self._ci.power_tracker = None
            self._ci.foreshadow_tracker = None
            self._ci.info_diffusion = None
            self._ci.v49_7_enabled = False

    def _get_protagonist_name(self) -> str:
        """프로젝트에서 주인공 이름 추출"""
        try:
            bible = getattr(self._ci.context, "master_bible", {})
            bible_root = bible.get("MasterBible", bible)
            proj_data = bible_root.get("ProjectData", {})
            return proj_data.get("protagonist", "주인공")
        except Exception:
            return "주인공"

    def validate_with_trackers(
        self, arc: int, episode: int, content: str, content_type: str = "blueprint"
    ) -> dict[str, Any]:
        """
        [V49.7] 트래커 기반 검증 실행

        Args:
            arc: 현재 Arc 번호
            episode: 현재 에피소드 번호
            content: 검증할 내용 (blueprint scenario 또는 manuscript)
            content_type: "blueprint" 또는 "manuscript"

        Returns:
            {warnings, violations, tracker_results}
        """
        if not self._ci.v49_7_enabled:
            return {"warnings": [], "violations": [], "tracker_results": {}}

        warnings = []
        violations = []
        tracker_results = {}

        # 1. 관계 상태 검증
        if self._ci.relationship_tracker:
            rel_result = self._check_relationship_with_tracker(arc, episode, content)
            if rel_result.get("violations"):
                violations.extend(rel_result["violations"])
            if rel_result.get("warnings"):
                warnings.extend(rel_result["warnings"])
            tracker_results["relationship"] = rel_result.get("details", {})

        # 2. 파워 스케일링 검증
        if self._ci.power_tracker:
            power_result = self._check_power_with_tracker(arc, episode, content)
            if power_result.get("warnings"):
                warnings.extend(power_result["warnings"])
            tracker_results["power_scaling"] = power_result.get("details", {})

        # 3. 복선 상태 검증
        if self._ci.foreshadow_tracker:
            foreshadow_result = self._check_foreshadowing_with_tracker(arc, episode, content)
            if foreshadow_result.get("warnings"):
                warnings.extend(foreshadow_result["warnings"])
            tracker_results["foreshadowing"] = foreshadow_result.get("details", {})

        # 4. 상태 델타 검증 (manuscript에서만)
        if self._ci.state_tracker and content_type == "manuscript":
            state_result = self._check_state_with_tracker(arc, episode, content)
            if state_result.get("warnings"):
                warnings.extend(state_result["warnings"])
            tracker_results["state_delta"] = state_result.get("details", {})

        return {"warnings": warnings, "violations": violations, "tracker_results": tracker_results}

    def _check_relationship_with_tracker(self, arc: int, episode: int, content: str) -> dict[str, Any]:
        """RelationshipTracker를 사용한 관계 전이 검증"""
        warnings = []
        violations = []
        details = {}

        group_keywords = ["사병", "무사들", "병사들", "부하들", "수하들", "호위", "교두", "장로들"]

        for group in group_keywords:
            if group in content:
                current_state = self._ci.relationship_tracker.infer_state_from_manuscript(group, content)

                if current_state:
                    prev_history = self._ci.relationship_tracker.get_transition_history(group)

                    if prev_history:
                        prev_state = prev_history[-1].get("to_state", "무시")

                        validation = self._ci.relationship_tracker.validate_transition_with_justification(
                            npc_name=group,
                            from_state=prev_state,
                            to_state=current_state,
                            proposed_justification="",
                            arc=arc,
                            episode=episode,
                        )

                        if not validation.get("valid"):
                            severity = validation.get("severity", "MINOR")
                            if severity in ["CRITICAL", "MAJOR"]:
                                violations.append(
                                    {
                                        "type": "relationship_violation",
                                        "severity": severity,
                                        "description": validation.get("message", "관계 전이 오류"),
                                    }
                                )
                            else:
                                warnings.append(
                                    {
                                        "type": "relationship_warning",
                                        "severity": "MINOR",
                                        "description": validation.get("message", "관계 전이 경고"),
                                    }
                                )

                        details[group] = {
                            "from": prev_state,
                            "to": current_state,
                            "valid": validation.get("valid", True),
                        }

        return {"warnings": warnings, "violations": violations, "details": details}

    def _check_power_with_tracker(self, arc: int, episode: int, content: str) -> dict[str, Any]:
        """PowerScalingTracker를 사용한 파워 스케일링 검증"""
        warnings = []
        details = {}

        protagonist = self._get_protagonist_name()

        power_keywords = {
            "각성": 25,
            "돌파": 20,
            "비급": 20,
            "영약": 15,
            "수련": 15,
            "깨달음": 15,
            "경지 상승": 20,
            "내공 증가": 10,
        }

        detected_growth = 0
        growth_reason = ""

        for keyword, power_delta in power_keywords.items():
            if keyword in content:
                detected_growth = max(detected_growth, power_delta)
                growth_reason = keyword

        if detected_growth > 0:
            current_power = self._ci.power_tracker.get_power(protagonist) or 30
            new_power = current_power + detected_growth

            validation = self._ci.power_tracker.validate_growth(
                character=protagonist, arc=arc, new_power=new_power, justification=growth_reason
            )

            if validation.get("severity") == "CRITICAL":
                warnings.append(
                    {
                        "type": "power_scaling_critical",
                        "severity": "MAJOR",
                        "description": validation.get("message", "급격한 파워업"),
                    }
                )
            elif validation.get("severity") == "WARNING":
                warnings.append(
                    {
                        "type": "power_scaling_warning",
                        "severity": "MINOR",
                        "description": validation.get("suggestion", "성장 속도 조절 권장"),
                    }
                )

            details["detected_growth"] = detected_growth
            details["reason"] = growth_reason
            details["validation"] = validation

        return {"warnings": warnings, "details": details}

    def _check_foreshadowing_with_tracker(self, arc: int, episode: int, content: str) -> dict[str, Any]:
        """ForeshadowingTracker를 사용한 복선 상태 검증"""
        warnings = []
        details = {}

        pending = self._ci.foreshadow_tracker.get_pending_foreshadowings(arc)

        critical_pending = [p for p in pending if p.get("severity") == "CRITICAL"]
        warning_pending = [p for p in pending if p.get("severity") == "WARNING"]

        if critical_pending:
            warnings.append(
                {
                    "type": "foreshadowing_critical",
                    "severity": "MAJOR",
                    "description": f"미회수 복선 {len(critical_pending)}개가 10개 Arc 이상 방치됨: "
                    + ", ".join([p["id"] for p in critical_pending[:3]]),
                }
            )

        if warning_pending:
            warnings.append(
                {
                    "type": "foreshadowing_warning",
                    "severity": "MINOR",
                    "description": f"미회수 복선 {len(warning_pending)}개가 5개 Arc 이상 방치됨",
                }
            )

        foreshadow_keywords = ["암시", "복선", "떡밥", "비밀", "예언", "숨겨진"]
        detected_foreshadows = [kw for kw in foreshadow_keywords if kw in content]

        details["pending_count"] = len(pending)
        details["critical_count"] = len(critical_pending)
        details["detected_keywords"] = detected_foreshadows

        return {"warnings": warnings, "details": details}

    def _check_state_with_tracker(self, arc: int, episode: int, content: str) -> dict[str, Any]:
        """StateDeltaTracker를 사용한 내공/부상 상태 검증"""
        warnings = []
        details = {}

        injury_level = "정상"
        if any(kw in content for kw in ["위독", "사경", "기절", "의식 잃"]):
            injury_level = "위독"
        elif any(kw in content for kw in ["중상", "심한 부상", "피투성이", "골절"]):
            injury_level = "중상"
        elif any(kw in content for kw in ["경상", "가벼운 상처", "찰과상"]):
            injury_level = "경상"

        energy_delta = 0
        if any(kw in content for kw in ["내공 고갈", "기력 소진", "탈진"]):
            energy_delta = -50
        elif any(kw in content for kw in ["내공 소모", "기력 사용", "힘이 빠져"]):
            energy_delta = -20
        elif any(kw in content for kw in ["운기조식", "회복", "휴식"]):
            energy_delta = 15

        if energy_delta != 0:
            result = self._ci.state_tracker.apply_energy_delta(
                arc=arc, episode=episode, delta=energy_delta, reason="자동 탐지"
            )
            if result.get("warning"):
                warnings.append({"type": "energy_warning", "severity": "MINOR", "description": result["warning"]})
            details["energy"] = result

        if injury_level != "정상":
            result = self._ci.state_tracker.apply_injury(
                arc=arc, episode=episode, level=injury_level, body_part="전신", cause="자동 탐지"
            )
            if result.get("warning"):
                warnings.append({"type": "injury_warning", "severity": "MINOR", "description": result["warning"]})
            details["injury"] = result

        details["current_energy"] = self._ci.state_tracker.get_current_energy()
        details["current_injury"] = self._ci.state_tracker.get_current_injury_level()

        return {"warnings": warnings, "details": details}

    def load_trackers_from_db(self, arcs_data: list[dict] = None) -> dict[str, int]:
        """
        [V49.7] DB에서 트래커 상태 로드

        Args:
            arcs_data: Arc 데이터 리스트 (None이면 DB에서 로드)

        Returns:
            로드 결과 {foreshadowings, relationships, power_entries}
        """
        if not self._ci.v49_7_enabled:
            return {"error": "V49.7 modules not available"}

        results = {"foreshadowings": 0, "relationships": 0, "power_entries": 0}

        if arcs_data is None:
            try:
                arcs_data = self._ci.context.db.load_anchor("arcs") or []
            except Exception:
                arcs_data = []

        if self._ci.foreshadow_tracker and arcs_data:
            results["foreshadowings"] = self._ci.foreshadow_tracker.load_from_arcs(arcs_data)

        for arc in arcs_data:
            if not isinstance(arc, dict):
                continue

            arc_no = arc.get("arc_no", 0)
            state_constraints = arc.get("state_constraints", {})

            if self._ci.power_tracker:
                protagonist = self._get_protagonist_name()
                arc_end = state_constraints.get("arc_end_state", {})
                if "power_level" in arc_end:
                    self._ci.power_tracker.set_power(
                        character=protagonist, arc=arc_no, power=arc_end.get("power_level", 30), reason="Arc 종료 상태"
                    )
                    results["power_entries"] += 1

            if self._ci.relationship_tracker:
                rel_changes = arc.get("relationship_changes", [])
                for change in rel_changes:
                    if isinstance(change, dict):
                        self._ci.relationship_tracker.record_transition(
                            arc=arc_no,
                            episode=arc.get("ep_end", 0),
                            npc_name=change.get("target", ""),
                            from_state=change.get("from", "무시"),
                            to_state=change.get("to", "무시"),
                            trigger=change.get("trigger", ""),
                            justification=change.get("justification", ""),
                        )
                        results["relationships"] += 1

        return results
