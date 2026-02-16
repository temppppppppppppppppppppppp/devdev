"""
[Phase 3] Retrospective Consistency Validator
장기 일관성 검증 - 과거 여러 에피소드와 현재 화의 일관성 체크
"""

import logging
import re

_logger = logging.getLogger(__name__)


class RetrospectiveValidator:
    """
    장기 일관성 검증 (과거 에피소드와 비교)

    과거 N화와 현재 화를 비교하여 장기적 모순 감지:
    - 경지/능력 역행
    - NPC 관계 역행
    - 소유 아이템 무설명 소실
    - 이미 해결된 갈등의 재발
    """

    def __init__(self, context, lookback_episodes: int = 5):
        """
        Args:
            context: ProjectContext
            lookback_episodes: 과거 몇 화까지 체크할지 (기본 5화)
        """
        self.context = context
        self.lookback = lookback_episodes

    def validate_long_term_consistency(self, current_ep: int, manuscript: str, validation_context: dict) -> dict:
        """
        장기 일관성 검증 실행

        Args:
            current_ep: 현재 에피소드 번호
            manuscript: 현재 원고
            validation_context: 검증 컨텍스트

        Returns:
            {
                "passed": bool,
                "violations": list,
                "severity_level": str,
                "total_violations": int
            }
        """
        violations = []

        # 1. 주인공 경지/능력 역행 체크
        realm_violations = self._check_realm_regression(current_ep, manuscript, validation_context)
        violations.extend(realm_violations)

        # 2. NPC 관계 역행 체크
        relationship_violations = self._check_relationship_regression(current_ep, manuscript, validation_context)
        violations.extend(relationship_violations)

        # 3. 소유 아이템 소실 체크
        item_violations = self._check_item_disappearance(current_ep, manuscript, validation_context)
        violations.extend(item_violations)

        # 4. 해결된 갈등 재발 체크
        conflict_violations = self._check_resolved_conflict_recurrence(current_ep, manuscript)
        violations.extend(conflict_violations)

        # 심각도 판정
        severity_level = self._calculate_severity(violations)

        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "severity_level": severity_level,
            "total_violations": len(violations),
            "message": "PASS" if len(violations) == 0 else f"{len(violations)}개 장기 일관성 위반 감지",
        }

    def _check_realm_regression(self, current_ep: int, manuscript: str, context: dict) -> list[dict]:
        """경지/능력 역행 체크"""
        violations = []

        try:
            # 현재 원고에서 경지 추출
            current_realm = self._extract_realm_from_manuscript(manuscript)

            if not current_realm:
                return violations

            # 과거 경지 추적
            past_realms = self._get_past_realms(current_ep)

            if past_realms:
                last_realm = past_realms[-1]

                # 경지 위계 정의 (낮음 → 높음)
                realm_hierarchy = ["초출", "삼류", "이류", "일류", "후천", "선천", "절정", "화경", "천인"]

                # 현재 경지가 과거보다 낮은가?
                if current_realm in realm_hierarchy and last_realm["realm"] in realm_hierarchy:
                    current_idx = realm_hierarchy.index(current_realm)
                    last_idx = realm_hierarchy.index(last_realm["realm"])

                    if current_idx < last_idx:
                        violations.append(
                            {
                                "type": "realm_regression",
                                "reason": f"경지 역행: 제{last_realm['ep']}화 '{last_realm['realm']}' → 현재 '{current_realm}'",
                                "severity": "CRITICAL",
                                "past_ep": last_realm["ep"],
                                "past_value": last_realm["realm"],
                                "current_value": current_realm,
                            }
                        )
        except Exception as e:
            logging.warning(f"⚠️ [Retrospective] 경지 역행 체크 실패: {e}")

        return violations

    def _check_relationship_regression(self, current_ep: int, manuscript: str, context: dict) -> list[dict]:
        """NPC 관계 역행 체크"""
        violations = []

        try:
            from modules.core.relationship_tracker import RelationshipTracker

            tracker = RelationshipTracker()
            encyclopedia = context.get("encyclopedia", {})
            npcs = encyclopedia.get("npcs", [])

            for npc in npcs:
                if not isinstance(npc, dict):
                    continue

                name = npc.get("name", "")
                if not name or name not in manuscript:
                    continue

                # 과거 관계 이력 조회
                history = tracker.get_relationship_history(self.context, name, current_ep)

                if not history:
                    continue

                # 현재 관계 추론
                current_rel = tracker.infer_state_from_manuscript(name, manuscript)

                if current_rel == "알 수 없음":
                    continue

                # 최근 관계와 비교
                last_rel = history[-1]["state"]

                # 역행 체크
                validation = tracker.validate_transition(name, last_rel, current_rel)

                if not validation["valid"]:
                    violations.append(
                        {
                            "type": "relationship_regression",
                            "reason": f"{name}: 제{history[-1]['ep_num']}화 '{last_rel}' → 현재 '{current_rel}' (불가능한 전환)",
                            "severity": "HIGH",
                            "npc": name,
                            "past_ep": history[-1]["ep_num"],
                            "past_value": last_rel,
                            "current_value": current_rel,
                            "allowed_transitions": validation.get("allowed_transitions", []),
                        }
                    )
        except Exception as e:
            logging.warning(f"⚠️ [Retrospective] 관계 역행 체크 실패: {e}")

        return violations

    def _check_item_disappearance(self, current_ep: int, manuscript: str, context: dict) -> list[dict]:
        """소유 아이템 무설명 소실 체크"""
        violations = []

        try:
            # 과거 소유 아이템 추적
            past_items = self._get_past_items(current_ep)

            if not past_items:
                return violations

            # 현재 원고에서 아이템 언급 체크
            current_items = self._extract_items_from_manuscript(manuscript)

            # 소실된 아이템 확인
            lost_items = set(past_items) - set(current_items)

            if lost_items:
                # 원고에 소실 설명이 있는가?
                if not self._has_item_loss_explanation(manuscript, lost_items):
                    violations.append(
                        {
                            "type": "item_disappearance",
                            "reason": f"아이템 무설명 소실: {list(lost_items)}",
                            "severity": "MEDIUM",
                            "lost_items": list(lost_items),
                            "required_fix": "아이템 소실 사유 명시 (잃어버림, 버림, 도난 등)",
                        }
                    )
        except Exception as e:
            logging.warning(f"⚠️ [Retrospective] 아이템 소실 체크 실패: {e}")

        return violations

    def _check_resolved_conflict_recurrence(self, current_ep: int, manuscript: str) -> list[dict]:
        """해결된 갈등 재발 체크"""
        violations = []

        try:
            # 과거 해결된 갈등 로드
            resolved_conflicts = self._get_resolved_conflicts(current_ep)

            for conflict in resolved_conflicts:
                conflict_keyword = conflict.get("keyword", "")
                resolved_ep = conflict.get("resolved_ep", 0)

                # 현재 원고에 같은 갈등이 재발했는가?
                if conflict_keyword and conflict_keyword in manuscript:
                    # 재발 정당화 체크
                    recurrence_justifications = ["다시", "재발", "또다시", "새로운", "다른"]

                    has_justification = any(just in manuscript for just in recurrence_justifications)

                    if not has_justification:
                        violations.append(
                            {
                                "type": "resolved_conflict_recurrence",
                                "reason": f"해결된 갈등 재발: '{conflict_keyword}' (제{resolved_ep}화에서 해결됨)",
                                "severity": "LOW",
                                "conflict": conflict_keyword,
                                "resolved_ep": resolved_ep,
                                "required_fix": "재발 정당화 필요 (새로운 상황, 다른 원인 등)",
                            }
                        )
        except Exception as e:
            logging.warning(f"⚠️ [Retrospective] 갈등 재발 체크 실패: {e}")

        return violations

    def _extract_realm_from_manuscript(self, manuscript: str) -> str:
        """원고에서 경지 추출 (간단한 패턴 매칭)"""
        realm_keywords = ["초출", "삼류", "이류", "일류", "후천", "선천", "절정", "화경", "천인"]

        for realm in realm_keywords:
            if realm in manuscript:
                return realm

        return ""

    def _get_past_realms(self, current_ep: int) -> list[dict]:
        """과거 경지 이력 조회"""
        realms = []

        try:
            for ep in range(max(1, current_ep - self.lookback), current_ep):
                # state_log 또는 manuscripts의 hud_snapshot에서 추출
                ms_data = self.context.db.get_manuscript(ep)

                if ms_data and isinstance(ms_data, dict):
                    hud = ms_data.get("hud_snapshot", {})
                    if isinstance(hud, dict):
                        realm = hud.get("realm", "")
                        if realm:
                            realms.append({"ep": ep, "realm": realm})
        except Exception:
            _logger.warning("[RetrospectiveValidator] _get_past_realms DB 읽기 실패", exc_info=True)

        return realms

    def _get_past_items(self, current_ep: int) -> set:
        """과거 소유 아이템 목록"""
        items = set()

        try:
            for ep in range(max(1, current_ep - self.lookback), current_ep):
                ms_data = self.context.db.get_manuscript(ep)

                if ms_data and isinstance(ms_data, dict):
                    hud = ms_data.get("hud_snapshot", {})
                    if isinstance(hud, dict):
                        equipment = hud.get("equipment", [])
                        if isinstance(equipment, list):
                            items.update(equipment)
                        elif isinstance(equipment, str):
                            items.add(equipment)
        except Exception:
            _logger.warning("[RetrospectiveValidator] _get_past_items DB 읽기 실패", exc_info=True)

        return items

    def _extract_items_from_manuscript(self, manuscript: str) -> set:
        """원고에서 아이템 언급 추출 (간단한 휴리스틱)"""
        # 특정 아이템 패턴 추출
        item_patterns = [
            r"([\w]+패)",  # ~패
            r"([\w]+검)",  # ~검
            r"([\w]+도)",  # ~도
            r"([\w]+창)",  # ~창
            r"([\w]+비기)",  # ~비기
        ]

        items = set()
        for pattern in item_patterns:
            matches = re.findall(pattern, manuscript)
            items.update(matches)

        return items

    def _has_item_loss_explanation(self, manuscript: str, lost_items: set) -> bool:
        """아이템 소실 설명이 있는가?"""
        loss_keywords = ["잃어버", "버렸", "도난", "빼앗", "사라졌", "잃었"]

        for item in lost_items:
            # 아이템 주변 문맥에서 소실 설명 확인
            if item in manuscript:
                item_idx = manuscript.find(item)
                context = manuscript[max(0, item_idx - 100) : min(len(manuscript), item_idx + 100)]

                if any(kw in context for kw in loss_keywords):
                    return True

        return False

    def _get_resolved_conflicts(self, current_ep: int) -> list[dict]:
        """해결된 갈등 목록 로드"""
        conflicts = []

        try:
            # DB에서 resolved_conflicts 앵커 로드
            stored = self.context.db.load_anchor("resolved_conflicts", default=[])
            if isinstance(stored, list):
                # 과거 lookback 화 이내에 해결된 갈등만
                conflicts = [
                    c
                    for c in stored
                    if isinstance(c, dict) and current_ep - self.lookback <= c.get("resolved_ep", 0) < current_ep
                ]
        except Exception:
            _logger.warning("[RetrospectiveValidator] _get_resolved_conflicts DB 읽기 실패", exc_info=True)

        return conflicts

    def _calculate_severity(self, violations: list[dict]) -> str:
        """위반 목록의 종합 심각도 계산"""
        if not violations:
            return "NONE"

        severity_scores = {"CRITICAL": 10, "HIGH": 5, "MEDIUM": 2, "LOW": 1}

        total_score = sum(severity_scores.get(v.get("severity", "LOW"), 1) for v in violations)

        if total_score >= 10:
            return "CRITICAL"
        elif total_score >= 5:
            return "HIGH"
        elif total_score >= 2:
            return "MEDIUM"
        else:
            return "LOW"
