"""
[V0128] TIER 1: BLOCKING Validator
Python 기반 필수 검증 (LLM 호출 불필요)

[Phase 4.2] Justification 제안 기능 추가
[V59] 씬 완성도/클리프행어 검증 추가
"""

import re

from modules.core.constants import ManuscriptLimits  # [V64.P4]

# [Phase 4.2] Justification pattern 임포트
try:
    from modules.core.justification_patterns import get_justification_guide, get_pattern_description

    JUSTIFICATION_AVAILABLE = True
except ImportError:
    JUSTIFICATION_AVAILABLE = False
    logging.warning("⚠️ [BlockingValidator] justification_patterns 모듈 로드 실패 - 제안 기능 비활성화")


class BlockingValidator:
    """
    TIER 1: 반드시 통과해야 하는 핵심 검증

    실패 시 즉시 REJECT - 수정 필수
    최소한의 항목만 포함하여 통과율 유지
    """

    def __init__(self, context=None, enable_justification_checks=True) -> None:
        """
        Args:
            context: ProjectContext 객체 (정보 일관성 체크용)
            enable_justification_checks: [V66.1] Phase 4 정당화 체크 활성화 (기본값: True)
                - True 시 물리적 능력, 권위 행사 등 제약 위반을 감지하고 정당화 패턴 제안
                - 서사 관성 극복을 위한 옵션 (통과율 약간 감소 가능)
        """
        self.context = context
        self.enable_justification_checks = enable_justification_checks
        # [V66.1] 비활성화 시 경고 로그
        if not enable_justification_checks:
            import logging

            logging.getLogger(__name__).warning(
                "[V66.1] BlockingValidator: justification checks disabled - "
                "physical capability and authority checks will be skipped"
            )

    def validate(self, manuscript: str, validation_context: dict) -> dict:
        """
        BLOCKING 검증 실행

        Args:
            manuscript: 검증 대상 원고
            validation_context: {
                'encyclopedia': {...},  # NPC/아이템 정보
                'martial_hud': {...},   # 주인공 상태
                'blueprint': {...}      # 설계도 (MANUSCRIPT 모드 시)
            }

        Returns:
            {
                "tier": "BLOCKING",
                "passed": True/False,
                "failures": [...],
                "message": "..."
            }
        """
        failures = []

        # 1. 사망 NPC 재등장
        dead_npc_check = self._check_dead_npc_resurrection(manuscript, validation_context)
        if not dead_npc_check["passed"]:
            failures.append(dead_npc_check)

        # 2. 미획득 아이템 사용
        unowned_item_check = self._check_unowned_item_usage(manuscript, validation_context)
        if not unowned_item_check["passed"]:
            failures.append(unowned_item_check)

        # 3. 파괴된 장소 방문
        destroyed_location_check = self._check_destroyed_location_visit(manuscript, validation_context)
        if not destroyed_location_check["passed"]:
            failures.append(destroyed_location_check)

        # 4. 분량 미달
        length_check = self._check_minimum_length(manuscript, validation_context)
        if not length_check["passed"]:
            failures.append(length_check)

        # 5. 필수 씬 누락 (MANUSCRIPT 모드만)
        if validation_context.get("mode") == "MANUSCRIPT":
            scene_check = self._check_required_scenes(manuscript, validation_context)
            if not scene_check["passed"]:
                failures.append(scene_check)

        # [V49] 6. 씬 범위 초과 체크 (MANUSCRIPT 모드만) - Writer가 Blueprint 범위를 넘어서 과잉 생성 방지
        if validation_context.get("mode") == "MANUSCRIPT":
            scope_check = self._check_scope_overflow(manuscript, validation_context)
            if not scope_check["passed"]:
                failures.append(scope_check)

        # [V66.1] 6. 파괴/분실/소모된 아이템 사용
        damaged_item_check = self._check_damaged_item_usage(manuscript, validation_context)
        if not damaged_item_check["passed"]:
            failures.append(damaged_item_check)

        # [Phase 2.1] 7. 관계 일관성 체크 (관계 역행 방지)
        relationship_check = self._check_relationship_consistency(manuscript, validation_context)
        if not relationship_check["passed"]:
            failures.append(relationship_check)

        # [Phase 2.2] 8. 정보 일관성 체크 (NPC가 알아야 할 것을 모르는가?)
        information_check = self._check_information_consistency(manuscript, validation_context)
        if not information_check["passed"]:
            failures.append(information_check)

        # [Phase 4.2] 9. 물리적 능력 체크 (옵션, 정당화 제안 포함)
        if self.enable_justification_checks:
            physical_check = self._check_physical_capability(manuscript, validation_context)
            if not physical_check["passed"]:
                failures.append(physical_check)

        # [Phase 4.2] 10. 권위 행사 체크 (옵션, 정당화 제안 포함)
        if self.enable_justification_checks:
            authority_check = self._check_authority_exercise(manuscript, validation_context)
            if not authority_check["passed"]:
                failures.append(authority_check)

        # [V59] 11. 씬별 완성도 체크 (MANUSCRIPT 모드만)
        if validation_context.get("mode") == "MANUSCRIPT":
            scene_completeness_check = self._check_scene_completeness(manuscript, validation_context)
            if not scene_completeness_check["passed"]:
                failures.append(scene_completeness_check)

        # [V59] 12. 클리프행어 엔딩 체크 (MANUSCRIPT 모드만)
        if validation_context.get("mode") == "MANUSCRIPT":
            cliffhanger_check = self._check_cliffhanger_ending(manuscript, validation_context)
            if not cliffhanger_check["passed"]:
                failures.append(cliffhanger_check)

        return {
            "tier": "BLOCKING",
            "passed": len(failures) == 0,
            "failures": failures,
            "message": "REJECT - 필수 수정 필요" if failures else "PASS",
            "failure_count": len(failures),
        }

    # [Phase 3-5A-2] 회상/언급 패턴 (사망 NPC 등장 허용)
    _RECALL_PATTERNS = (
        "회상",
        "과거",
        "기억",
        "떠올리",
        "그때",
        "예전에",
        "했었다",
        "했던",
        "였던",
        "이었다",
        "말했었",
        "죽은",
        "생전에",
        "살아있을 때",
        "고인",
        "영전에",
        "추모",
    )
    # [Phase 3-5A-2] 행동/대사 패턴 (사망 NPC 등장 금지)
    _ACTION_PATTERNS = (
        "말했다",
        "말한다",
        "외쳤다",
        "소리쳤다",
        "웃었다",
        "웃으며",
        "걸어",
        "달려",
        "싸우",
        "공격",
        "막았다",
        "들었다",
        "일어나",
        "나타나",
        "등장",
        "다가와",
        "다가오",
    )

    def _check_dead_npc_resurrection(self, manuscript: str, context: dict) -> dict:
        """[Phase 3-5A-2] 사망한 NPC 재등장 체크 — 행동/대사 vs 회상/언급 구분"""
        encyclopedia = context.get("encyclopedia", {})
        npcs = encyclopedia.get("npcs", [])

        dead_npcs = [npc for npc in npcs if npc.get("status") == "dead"]

        for npc in dead_npcs:
            name = npc.get("name", "")
            aliases = npc.get("aliases", [])

            for identifier in [name] + aliases:
                if not identifier or identifier not in manuscript:
                    continue

                # 모든 등장 위치에서 주변 텍스트 검사
                start = 0
                while True:
                    pos = manuscript.find(identifier, start)
                    if pos == -1:
                        break
                    start = pos + 1

                    window_start = max(0, pos - 100)
                    window_end = min(len(manuscript), pos + len(identifier) + 100)
                    context_window = manuscript[window_start:window_end]

                    # 회상/언급 패턴이면 허용 → 다음 위치로
                    if any(p in context_window for p in self._RECALL_PATTERNS):
                        continue

                    # 행동/대사 패턴이면 CRITICAL
                    if any(p in context_window for p in self._ACTION_PATTERNS):
                        return {
                            "check": "dead_npc_resurrection",
                            "passed": False,
                            "reason": f"사망한 NPC '{name}' 행동/대사 감지 (회상 아님)",
                            "severity": "CRITICAL",
                            "location": pos,
                        }

        return {"check": "dead_npc_resurrection", "passed": True}

    def _check_unowned_item_usage(self, manuscript: str, context: dict) -> dict:
        """
        미획득 아이템 사용 체크 (타입 안전성 강화)

        [V55.5] alias 매칭 + word boundary 체크 추가
        - "대도" 검색 시 "백근대도" 오탐 방지
        - aliases 필드 지원으로 동일 아이템 다른 명칭 처리
        """
        encyclopedia = context.get("encyclopedia", {})
        martial_hud = context.get("martial_hud", {})

        # HUD에서 소유 아이템 목록 (방어적 추출)
        owned_items = []
        owned_items_with_aliases = []  # [V55.5] 소유 아이템 + 별칭 모두 저장

        if isinstance(martial_hud, dict):
            actual_truth = martial_hud.get("actual_truth", {})
            if isinstance(actual_truth, dict):
                equipment = actual_truth.get("equipment", [])

                # 다양한 타입 처리 (강화된 검증)
                if equipment is None:
                    owned_items = []
                elif isinstance(equipment, list):
                    # 리스트의 각 원소가 문자열인지 검증
                    owned_items = [str(item) for item in equipment if item and len(str(item)) > 0]
                elif isinstance(equipment, str):
                    owned_items = [equipment] if equipment.strip() else []
                elif isinstance(equipment, dict):
                    # dict의 key가 문자열이고 value가 truthy인 경우만
                    owned_items = [
                        str(k) for k, v in equipment.items() if k and v and isinstance(k, str | int) and len(str(k)) > 0
                    ]
                else:
                    # 예상치 못한 타입
                    logging.warning(f"[WARNING] Unexpected equipment type: {type(equipment).__name__}")
                    logging.warning(f"[WARNING] Equipment value: {repr(equipment)[:100]}")
                    owned_items = []

        # 최종 안전성 확인 (강화)
        if not isinstance(owned_items, list):
            logging.warning(f"[ERROR] owned_items is not a list after processing: {type(owned_items).__name__}")
            owned_items = []

        # 각 원소가 문자열이고 비어있지 않은지 확인
        owned_items = [item for item in owned_items if isinstance(item, str) and len(item) > 0]

        # [V55.5] 소유 아이템의 별칭도 추가
        owned_items_with_aliases = list(owned_items)  # 복사
        all_items = encyclopedia.get("items", [])

        for item in all_items:
            item_name = item.get("name", "")
            item_aliases = item.get("aliases", [])

            # 소유한 아이템의 별칭도 owned로 처리
            if item_name in owned_items:
                if isinstance(item_aliases, list):
                    owned_items_with_aliases.extend(item_aliases)

        for item in all_items:
            item_name = item.get("name", "")
            item_aliases = item.get("aliases", []) if isinstance(item.get("aliases"), list) else []

            if not item_name:
                continue

            # [V55.5] 검사할 모든 이름 (primary + aliases)
            all_names = [item_name] + item_aliases

            # 소유 여부 확인 (이름 또는 별칭 중 하나라도 소유하면 OK)
            is_owned = any(name in owned_items_with_aliases for name in all_names)

            if is_owned:
                continue  # 소유한 아이템은 스킵

            # [V55.5] word boundary 체크로 부분 매칭 방지
            # "대도"가 "백근대도" 안에서 매칭되지 않도록
            for check_name in all_names:
                if not check_name or len(check_name) < 2:
                    continue

                # 단순 문자열 매칭 대신 word boundary 체크
                # 한글은 word boundary가 다르므로 앞뒤 문자 체크
                matches = []
                start = 0
                while True:
                    idx = manuscript.find(check_name, start)
                    if idx == -1:
                        break

                    # 앞뒤 문자가 한글이면 부분 매칭 (스킵)
                    prev_char = manuscript[idx - 1] if idx > 0 else ""
                    next_char = manuscript[idx + len(check_name)] if idx + len(check_name) < len(manuscript) else ""

                    # 한글 범위: 가-힣
                    is_prev_hangul = prev_char and "\uac00" <= prev_char <= "\ud7a3"
                    is_next_hangul = next_char and "\uac00" <= next_char <= "\ud7a3"

                    # 앞뒤 모두 한글이 아니면 독립된 단어로 판단
                    if not is_prev_hangul and not is_next_hangul:
                        matches.append(idx)
                    # 특수 케이스: "백근대도" 안의 "대도"는 부분 매칭이므로 스킵
                    # 하지만 "대도를 휘둘렀다"는 독립 단어이므로 감지
                    elif not is_prev_hangul or not is_next_hangul:
                        # 앞 또는 뒤 한쪽만 한글인 경우 (예: "대도를" → 앞 없음, 뒤 "를")
                        matches.append(idx)

                    start = idx + 1

                if not matches:
                    continue

                # 매칭된 위치에서 사용 패턴 체크
                # [V55.5] check_name 기반으로 패턴 생성
                usage_patterns = [
                    f"{check_name}을 휘둘",
                    f"{check_name}를 휘둘",
                    f"{check_name}으로",
                    f"{check_name}를 사용",
                    f"{check_name}을 사용",
                    f"{check_name}를 꺼내",
                    f"{check_name}을 꺼내",
                    f"{check_name}를 움켜",
                    f"{check_name}을 움켜",
                    f"{check_name}를 뽑",
                    f"{check_name}을 뽑",
                ]

                # 부정문 패턴 (오탐 방지)
                negation_patterns = [
                    f"{check_name}을 휘두르지",
                    f"{check_name}를 휘두르지",
                    f"{check_name}을 사용하지",
                    f"{check_name}를 사용하지",
                    f"{check_name}을 꺼내지",
                    f"{check_name}를 꺼내지",
                    f"{check_name}을 보았다",
                    f"{check_name}를 보았다",
                    f"{check_name}을 보며",
                    f"{check_name}를 보며",
                    f"{check_name}을 회상",
                    f"{check_name}를 회상",
                    f"{check_name}에 대해",
                ]

                for pattern in usage_patterns:
                    if pattern in manuscript:
                        # 부정문 체크 (오탐 방지)
                        location = manuscript.find(pattern)

                        # [V44 Fix] 문장 경계 찾기 (find() -1 반환 안전 처리)
                        def find_sentence_start(text, pos):
                            """위치 이전의 가장 가까운 문장 끝 찾기"""
                            candidates = []
                            for delim in ".!?":
                                idx = text.rfind(delim, 0, pos)
                                if idx != -1:
                                    candidates.append(idx + 1)
                            return max(candidates) if candidates else 0

                        def find_sentence_end(text, pos):
                            """위치 이후의 가장 가까운 문장 끝 찾기"""
                            candidates = []
                            for delim in ".!?":
                                idx = text.find(delim, pos)
                                if idx != -1:
                                    candidates.append(idx)
                            return min(candidates) if candidates else len(text)

                        sentence_start = find_sentence_start(manuscript, location)
                        sentence_end = find_sentence_end(manuscript, location + len(pattern))

                        context = manuscript[sentence_start : sentence_end + 1]

                        # 부정문이면 pass - 같은 문장 내에 부정 표현이 있어야 함
                        is_negation = any(neg in context for neg in negation_patterns)
                        # [V44 Fix] 추가 부정 키워드 체크 (문장 내 직접 부정)
                        negation_keywords = ["않았", "못했", "없었", "아니었", "안 했", "못 했", "아직"]
                        has_direct_negation = any(nk in context for nk in negation_keywords)
                        if is_negation or has_direct_negation:
                            continue

                        # [V55.5] 아이템 이름 표시 개선 (별칭인 경우 원본 이름도 표시)
                        display_name = check_name if check_name == item_name else f"{check_name} ({item_name})"
                        return {
                            "check": "unowned_item_usage",
                            "passed": False,
                            "reason": f"미획득 아이템 '{display_name}' 사용",
                            "severity": "CRITICAL",
                            "owned_items": owned_items,
                            "location": location,
                            "context": context,
                            "item_name": item_name,
                            "matched_alias": check_name if check_name != item_name else None,
                        }

        return {"check": "unowned_item_usage", "passed": True}

    def _check_damaged_item_usage(self, manuscript: str, context: dict) -> dict:
        """
        [V66.1] 파괴/분실/소모된 아이템 사용 체크

        item_state_registry에서 아이템 상태(파괴/분실/소모)를 읽고,
        해당 아이템이 원고에서 사용 패턴으로 등장하면 REJECT.
        """
        item_states = context.get("item_states", {})

        if not item_states or not isinstance(item_states, dict):
            return {"check": "damaged_item_usage", "passed": True}

        # 조건 → REJECT 사유 매핑
        condition_reason_map = {
            "파괴": "파괴된 아이템 사용",
            "분실": "분실된 아이템 사용",
            "소모": "소모된 아이템 사용",
        }

        for item_name, condition in item_states.items():
            if not isinstance(condition, str):
                continue
            # "정상" 상태는 스킵
            if condition == "정상":
                continue

            # 매핑에 없는 상태도 스킵 (알 수 없는 상태)
            reason_template = condition_reason_map.get(condition)
            if not reason_template:
                continue

            if not item_name or len(item_name) < 2:
                continue

            # word boundary 체크로 부분 매칭 방지 (unowned_item_usage와 동일 방식)
            matches = []
            start = 0
            while True:
                idx = manuscript.find(item_name, start)
                if idx == -1:
                    break

                prev_char = manuscript[idx - 1] if idx > 0 else ""
                next_char = manuscript[idx + len(item_name)] if idx + len(item_name) < len(manuscript) else ""

                is_prev_hangul = prev_char and "\uac00" <= prev_char <= "\ud7a3"
                is_next_hangul = next_char and "\uac00" <= next_char <= "\ud7a3"

                if not is_prev_hangul and not is_next_hangul:
                    matches.append(idx)
                elif not is_prev_hangul or not is_next_hangul:
                    matches.append(idx)

                start = idx + 1

            if not matches:
                continue

            # 사용 패턴 체크 (unowned_item_usage와 동일 패턴)
            usage_patterns = [
                f"{item_name}을 휘둘",
                f"{item_name}를 휘둘",
                f"{item_name}으로",
                f"{item_name}를 사용",
                f"{item_name}을 사용",
                f"{item_name}를 꺼내",
                f"{item_name}을 꺼내",
                f"{item_name}를 움켜",
                f"{item_name}을 움켜",
                f"{item_name}를 뽑",
                f"{item_name}을 뽑",
                f"{item_name}를 들",
                f"{item_name}을 들",
                f"{item_name}를 잡",
                f"{item_name}을 잡",
                f"{item_name}를 착용",
                f"{item_name}을 착용",
                f"{item_name}를 먹",
                f"{item_name}을 먹",
            ]

            # 부정문 패턴 (오탐 방지)
            negation_patterns = [
                f"{item_name}을 사용하지",
                f"{item_name}를 사용하지",
                f"{item_name}을 꺼내지",
                f"{item_name}를 꺼내지",
                f"{item_name}을 보았다",
                f"{item_name}를 보았다",
                f"{item_name}을 보며",
                f"{item_name}를 보며",
                f"{item_name}을 회상",
                f"{item_name}를 회상",
                f"{item_name}에 대해",
                f"{item_name}이 부서진",
                f"{item_name}가 부서진",
                f"{item_name}을 잃어",
                f"{item_name}를 잃어",
            ]

            for pattern in usage_patterns:
                if pattern in manuscript:
                    location = manuscript.find(pattern)

                    # 문장 경계 찾기
                    def _find_sentence_start(text, pos):
                        candidates = []
                        for delim in ".!?\n":
                            idx = text.rfind(delim, 0, pos)
                            if idx != -1:
                                candidates.append(idx + 1)
                        return max(candidates) if candidates else 0

                    def _find_sentence_end(text, pos):
                        candidates = []
                        for delim in ".!?\n":
                            idx = text.find(delim, pos)
                            if idx != -1:
                                candidates.append(idx)
                        return min(candidates) if candidates else len(text)

                    sentence_start = _find_sentence_start(manuscript, location)
                    sentence_end = _find_sentence_end(manuscript, location + len(pattern))
                    sentence_context = manuscript[sentence_start : sentence_end + 1]

                    # 부정문이면 pass
                    is_negation = any(neg in sentence_context for neg in negation_patterns)
                    negation_keywords = ["않았", "못했", "없었", "아니었", "안 했", "못 했", "아직"]
                    has_direct_negation = any(nk in sentence_context for nk in negation_keywords)
                    if is_negation or has_direct_negation:
                        continue

                    return {
                        "check": "damaged_item_usage",
                        "passed": False,
                        "reason": f"{reason_template}: '{item_name}' (상태: {condition})",
                        "severity": "CRITICAL",
                        "item_name": item_name,
                        "item_condition": condition,
                        "location": location,
                        "context": sentence_context,
                    }

        return {"check": "damaged_item_usage", "passed": True}

    def _check_destroyed_location_visit(self, manuscript: str, context: dict) -> dict:
        """파괴된 장소 방문 체크"""
        encyclopedia = context.get("encyclopedia", {})
        locations = encyclopedia.get("locations", [])

        destroyed_locations = [loc for loc in locations if loc.get("status") == "destroyed"]

        for loc in destroyed_locations:
            name = loc.get("name", "")
            if not name:
                continue

            # "불탄 객잔"은 OK, "객잔에 들어갔다"는 NG
            visit_patterns = [f"{name}에 들어", f"{name}로 들어", f"{name}에 도착", f"{name}에서 묵", f"{name}의 방"]

            for pattern in visit_patterns:
                if pattern in manuscript:
                    return {
                        "check": "destroyed_location_visit",
                        "passed": False,
                        "reason": f"파괴된 장소 '{name}' 정상 방문",
                        "severity": "CRITICAL",
                        "location": manuscript.find(pattern),
                    }

        return {"check": "destroyed_location_visit", "passed": True}

    def _check_minimum_length(self, manuscript: str, context: dict) -> dict:
        """최소 분량 체크"""
        mode = context.get("mode", "MANUSCRIPT")

        if mode == "BLUEPRINT":
            threshold = 500
        else:  # MANUSCRIPT
            threshold = ManuscriptLimits.MIN_LENGTH  # [V64.P4]

        length = len(manuscript)

        if length < threshold:
            return {
                "check": "minimum_length",
                "passed": False,
                "reason": f"분량 미달: {length}자 (최소 {threshold}자)",
                "severity": "CRITICAL",
                "current_length": length,
                "threshold": threshold,
            }

        return {"check": "minimum_length", "passed": True}

    def _check_required_scenes(self, manuscript: str, context: dict) -> dict:
        """필수 씬 포함 체크 (MANUSCRIPT 모드만)"""
        blueprint = context.get("blueprint", {})
        scene_breakdown = blueprint.get("scene_breakdown", {})

        if not scene_breakdown:
            # Blueprint 없으면 체크 불가 → 통과 처리
            return {"check": "required_scenes", "passed": True}

        # 최소 4개 장면이 원고에 반영되었는지 체크
        scene_count = len(scene_breakdown)
        min_required = 4

        # 각 Scene의 키워드가 원고에 있는지 체크
        scenes_found = 0
        for scene_name, scene_desc in scene_breakdown.items():
            # Scene 설명에서 핵심 키워드 추출 (간단한 휴리스틱)
            # 예: "주인공이 객잔에 도착" → ["객잔", "도착"]
            if isinstance(scene_desc, dict):  # [V70] dict 타입 방어
                scene_desc = scene_desc.get("description", scene_desc.get("content", str(scene_desc)))
            keywords = self._extract_keywords(str(scene_desc))

            # 키워드 중 하나라도 원고에 있으면 Scene 반영됨
            if any(kw in manuscript for kw in keywords if kw):
                scenes_found += 1

        if scenes_found < min_required:
            return {
                "check": "required_scenes",
                "passed": False,
                "reason": f"필수 씬 누락: {scenes_found}/{scene_count} 반영 (최소 {min_required}개)",
                "severity": "HIGH",
                "scenes_found": scenes_found,
                "total_scenes": scene_count,
            }

        return {"check": "required_scenes", "passed": True}

    def _check_scope_overflow(self, manuscript: str, context: dict) -> dict:
        """
        [V49] 씬 범위 초과 체크 - Writer가 Blueprint 범위를 넘어서 과잉 생성하는 것을 방지

        [V55.5] 기준 강화: 1.3배 → 1.2배
        Blueprint에 6개 씬이 있는데 원고가 과잉 생성되면 REJECT
        - 씬당 평균 700-1200자 가정
        - 씬 개수 * 1500자 * 1.2배를 초과하면 범위 초과로 판단
        """
        blueprint = context.get("blueprint", {})
        blueprint_text = context.get("blueprint_text", "")  # 원본 텍스트

        # 1. 씬 개수 추출 (두 가지 방법 시도)
        scene_count = 0

        # 방법 1: scene_breakdown dict에서 추출
        scene_breakdown = blueprint.get("scene_breakdown", {})
        if scene_breakdown and isinstance(scene_breakdown, dict):
            scene_count = len(scene_breakdown)

        # 방법 2: blueprint_text에서 "## scene_" 패턴 카운트
        if scene_count == 0 and blueprint_text:
            scene_pattern = r"##\s*scene_\d+"
            matches = re.findall(scene_pattern, blueprint_text, re.IGNORECASE)
            scene_count = len(matches)

        # 방법 3: blueprint dict 자체에서 scenes 키 확인
        if scene_count == 0:
            scenes = blueprint.get("scenes", [])
            if isinstance(scenes, list):
                scene_count = len(scenes)

        # 씬 개수를 못 찾으면 체크 불가 → 통과
        if scene_count == 0:
            return {"check": "scope_overflow", "passed": True, "reason": "씬 개수 추출 불가 - 체크 스킵"}

        # 2. 원고 길이 vs 예상 범위 비교
        manuscript_length = len(manuscript)

        # 씬당 최대 허용 글자 수 (충분히 여유있게 설정)
        max_chars_per_scene = 1500  # 6개 씬 = 9000자 상한
        max_allowed_length = scene_count * max_chars_per_scene

        # 3. 범위 초과 판정
        if manuscript_length > max_allowed_length:
            overflow_ratio = manuscript_length / max_allowed_length

            # [V55.5] 1.2배 초과 시 REJECT (예: 6개 씬에 10800자 이상)
            if overflow_ratio > 1.2:
                return {
                    "check": "scope_overflow",
                    "passed": False,
                    "reason": f"Blueprint 범위 초과: {manuscript_length}자 (씬 {scene_count}개 기준 최대 {max_allowed_length}자, {overflow_ratio:.1f}배 초과)",
                    "severity": "HIGH",
                    "details": {
                        "manuscript_length": manuscript_length,
                        "scene_count": scene_count,
                        "max_allowed": max_allowed_length,
                        "overflow_ratio": round(overflow_ratio, 2),
                    },
                    "suggestion": "Writer가 Arc 전체를 한 화에 압축 생성한 것으로 보입니다. Blueprint의 씬 분해(Scene Breakdown)만 따라 작성하세요.",
                }

            # [V55.5] 1.0~1.2배는 경고만 (통과)
            return {
                "check": "scope_overflow",
                "passed": True,
                "warning": f"분량 약간 초과: {manuscript_length}자 (권장 {max_allowed_length}자 이하)",
                "overflow_ratio": round(overflow_ratio, 2),
            }

        return {"check": "scope_overflow", "passed": True}

    def _extract_keywords(self, text: str, max_keywords: int = 3) -> list[str]:
        """텍스트에서 핵심 키워드 추출 (간단한 휴리스틱)"""
        # 명사 추출 (한글 2글자 이상)
        pattern = r"[가-힣]{2,}"
        words = re.findall(pattern, text)

        # 불용어 제거
        stopwords = {"것이다", "있다", "없다", "하다", "되다", "이다", "그", "저", "이", "그것", "저것"}
        keywords = [w for w in words if w not in stopwords]

        # 상위 N개 반환
        return keywords[:max_keywords]

    def _check_physical_capability(self, manuscript: str, context: dict) -> dict:
        """
        [Phase 4.2] 물리적 능력 제약 체크

        나약한 신체 상태에서 강력한 행동을 수행하는 경우 감지
        정당화 패턴 제안 포함

        [V67.1] 회귀자 incarnation_type 인식: 전생 경험으로 설명 가능한 경우 메시지 완화
        """
        if not JUSTIFICATION_AVAILABLE:
            return {"check": "physical_capability", "passed": True}

        martial_hud = context.get("martial_hud", {})
        genre = context.get("genre", "wuxia")
        # [V67.1] incarnation_type 추출
        incarnation_type = context.get("incarnation_type", "")

        # HUD에서 신체 상태 태그 추출
        actual_truth = martial_hud.get("actual_truth", {})
        physical_tags = actual_truth.get("physical_tags", [])

        if not isinstance(physical_tags, list):
            physical_tags = []

        # 나약함 태그
        weak_tags = ["나약", "중독", "부상", "중상", "쇠약", "기력고갈", "기혈역류"]
        is_weak = any(tag in physical_tags for tag in weak_tags)

        if not is_weak:
            return {"check": "physical_capability", "passed": True}

        # 강력한 행동 패턴
        strong_action_patterns = [
            r"무거운.{0,5}들어올",
            r"\d{2,}근.{0,5}대도",
            r"일격에.{0,5}박살",
            r"단번에.{0,5}격파",
            r"힘껏.{0,5}휘두",
            r"거대한.{0,5}무기",
            r"돌진하여.{0,5}부딪",
            r"벽을.{0,5}부수",
        ]

        import re

        violation_found = False
        violation_location = 0
        violation_context = ""

        for pattern in strong_action_patterns:
            match = re.search(pattern, manuscript)
            if match:
                violation_found = True
                violation_location = match.start()

                # 주변 100자 문맥 추출
                start = max(0, violation_location - 50)
                end = min(len(manuscript), violation_location + 100)
                violation_context = manuscript[start:end]

                # 정당화 키워드가 이미 있는지 체크
                justification_keywords = [
                    "발경",
                    "기혈",
                    "폭발",
                    "대가",
                    "고통",
                    "뼈마디",
                    "전생",
                    "체득",
                    "기억",
                    "경험",
                    "요령",
                    "순간적",
                    "짜내",
                    "역류",
                ]

                has_justification = any(kw in violation_context for kw in justification_keywords)

                if not has_justification:
                    # 정당화 없음 - 제안 제공
                    pattern_desc = get_pattern_description(genre, "weak_body_strong_action")
                    justification_guide = get_justification_guide(genre, "weak_body_strong_action")

                    # [V67.1] 회귀자 맥락 메시지 완화
                    _reason_suffix = ""
                    if incarnation_type == "회귀자":
                        _reason_suffix = " [회귀자 — 전생 경험으로 가능할 수 있음]"

                    return {
                        "check": "physical_capability",
                        "passed": False,
                        "reason": f"나약한 신체 상태({', '.join([t for t in physical_tags if t in weak_tags])})에서 강력한 행동 수행{_reason_suffix}",
                        "severity": "MEDIUM",
                        "location": violation_location,
                        "context": violation_context,
                        "suggested_pattern": pattern_desc,
                        "justification_guide": justification_guide,
                        "fix_template": "'{행동}' 직전 또는 중간에 정당화 문구를 추가하십시오. 예: '전생의 발경법으로 팔목 기혈을 폭발시켰다. 뼈마디가 어긋나는 고통이 밀려왔지만...'",
                        "quick_fixes": [
                            "전생 기억/경험을 활용한 효율적 방법",
                            "기혈을 짜내며 순간 폭발력 (부작용 명시)",
                            "특수 기법으로 힘의 방향 전환 (대가 표현)",
                        ],
                    }

        return {"check": "physical_capability", "passed": True}

    def _check_authority_exercise(self, manuscript: str, context: dict) -> dict:
        """
        [Phase 4.2] 권위 행사 제약 체크

        낮은 지위에서 높은 권위를 행사하는 경우 감지
        정당화 패턴 제안 포함

        [V67.1] 회귀자 incarnation_type 인식: 전생 경험에서 나오는 권위감 고려
        """
        if not JUSTIFICATION_AVAILABLE:
            return {"check": "authority_exercise", "passed": True}

        martial_hud = context.get("martial_hud", {})
        genre = context.get("genre", "wuxia")
        # [V67.1] incarnation_type 추출
        incarnation_type = context.get("incarnation_type", "")

        # HUD에서 권위 관련 데이터 추출
        actual_truth = martial_hud.get("actual_truth", {})
        status_tags = actual_truth.get("status_tags", [])
        reputation = actual_truth.get("reputation", 0)
        try:  # [V70] DB TEXT 타입 방어
            reputation = int(reputation) if not isinstance(reputation, int | float) else reputation
        except (ValueError, TypeError):
            reputation = 0

        if not isinstance(status_tags, list):
            status_tags = []

        # 낮은 지위 태그
        low_status_tags = ["하인", "노예", "평민", "무명", "낭인", "거지"]
        has_low_status = any(tag in status_tags for tag in low_status_tags)
        has_low_reputation = reputation < 20

        if not (has_low_status or has_low_reputation):
            return {"check": "authority_exercise", "passed": True}

        # 높은 권위 행동 패턴
        high_authority_patterns = [
            r"명령했다",
            r"지시했다",
            r"단호하게.{0,5}말했다",
            r"복종하라",
            r"따르라고",
            r"감히.{0,5}거역",
            r"명을.{0,5}내렸다",
        ]

        import re

        for pattern in high_authority_patterns:
            match = re.search(pattern, manuscript)
            if match:
                violation_location = match.start()

                # 주변 문맥
                start = max(0, violation_location - 50)
                end = min(len(manuscript), violation_location + 100)
                violation_context = manuscript[start:end]

                # 정당화 키워드 체크
                justification_keywords = [
                    "살기",
                    "기세",
                    "압도",
                    "눈빛",
                    "위압",
                    "전생",
                    "경험",
                    "자신감",
                    "실력",
                    "무력",
                    "힘",
                ]

                has_justification = any(kw in violation_context for kw in justification_keywords)

                if not has_justification:
                    pattern_desc = get_pattern_description(genre, "low_status_high_authority")
                    justification_guide = get_justification_guide(genre, "low_status_high_authority")

                    # [V67.1] 회귀자 맥락 메시지 완화
                    _reason_suffix = ""
                    if incarnation_type == "회귀자":
                        _reason_suffix = " [회귀자 — 전생 경험에서 나오는 권위감으로 가능할 수 있음]"

                    return {
                        "check": "authority_exercise",
                        "passed": False,
                        "reason": f"낮은 지위(reputation: {reputation}, tags: {status_tags})에서 명령/지시 행위{_reason_suffix}",
                        "severity": "MEDIUM",
                        "location": violation_location,
                        "context": violation_context,
                        "suggested_pattern": pattern_desc,
                        "justification_guide": justification_guide,
                        "fix_template": "'{행동}' 전에 권위 정당화 추가. 예: '전생의 기억이 만든 절대적 자신감이 눈빛에 담겼다.'",
                        "quick_fixes": [
                            "전생 경험에서 나오는 자연스러운 기세/눈빛",
                            "무력 시연으로 두려움 유발",
                            "살기/위압으로 본능적 복종 유도",
                        ],
                    }

        return {"check": "authority_exercise", "passed": True}

    def _check_relationship_consistency(self, manuscript: str, context: dict) -> dict:
        """
        [Phase 2.1] 관계 일관성 체크 (관계 역행 방지)

        [V67.1] 회귀자 incarnation_type 인식: 전생 관계 재연으로 급변 설명 가능
        """
        try:
            from modules.core.relationship_tracker import RelationshipTracker

            tracker = RelationshipTracker()
            encyclopedia = context.get("encyclopedia", {})
            npcs = encyclopedia.get("npcs", [])
            current_ep = context.get("ep_num", 0)
            # [V67.1] incarnation_type 추출
            incarnation_type = context.get("incarnation_type", "")

            for npc in npcs:
                if not isinstance(npc, dict):
                    continue

                name = npc.get("name", "")
                if not name or name not in manuscript:
                    continue  # 등장하지 않으면 스킵

                # 이전 관계 상태 (Bible 또는 encyclopedia에서)
                prev_relationship = npc.get("relationship_state", "중립")

                # 원고에서 현재 관계 추론
                current_relationship = tracker.infer_state_from_manuscript(name, manuscript)

                if current_relationship != "알 수 없음":
                    # 전환 가능성 검증
                    validation = tracker.validate_transition(name, prev_relationship, current_relationship)

                    if not validation["valid"]:
                        # [V67.1] 회귀자 맥락 메시지 완화
                        _rel_reason = validation["reason"]
                        if incarnation_type == "회귀자":
                            _rel_reason += " [회귀자 — 전생 관계 재연으로 급변 가능]"
                        return {
                            "check": "relationship_consistency",
                            "passed": False,
                            "reason": _rel_reason,
                            "severity": "HIGH",
                            "npc": name,
                            "transition": f"{prev_relationship} → {current_relationship}",
                            "allowed_transitions": validation.get("allowed_transitions", []),
                            "required_fix": validation.get("required", ""),
                        }
        except Exception as e:
            # 모듈 로드 실패 등의 경우 조용히 통과
            logging.warning(f"⚠️ [Blocking] 관계 일관성 체크 실패: {e}")

        return {"check": "relationship_consistency", "passed": True}

    def _check_information_consistency(self, manuscript: str, context: dict) -> dict:
        """[Phase 2.2] 정보 일관성 체크 (NPC가 알아야 할 것을 모르는가?)"""
        try:
            from modules.core.information_diffusion import InformationDiffusion

            # context 객체가 필요 (self.context가 있는 경우에만 동작)
            if not self.context:
                return {"check": "information_consistency", "passed": True}

            diffusion = InformationDiffusion(self.context)
            current_ep = context.get("ep_num", 0)
            encyclopedia = context.get("encyclopedia", {})
            npcs = encyclopedia.get("npcs", [])

            # 주요 사건 로드
            major_events = diffusion.load_major_events()

            if not major_events:
                return {"check": "information_consistency", "passed": True}

            for npc in npcs:
                if not isinstance(npc, dict):
                    continue

                name = npc.get("name", "")
                if not name or name not in manuscript:
                    continue  # 등장하지 않으면 스킵

                # [V66.1] 전체 주요 사건 체크 (이전: [-3:] 제한 → 100화+ 정보 누락 방지)
                for event in major_events:
                    knowledge_check = diffusion.should_npc_know(npc, event, current_ep)

                    if knowledge_check["should_know"]:
                        # NPC가 알아야 하는 사건인데, 원고에서 모르는 것처럼 행동하는가?
                        ignorance_patterns = [
                            f"{name}.*알지 못",
                            f"{name}.*처음 듣",
                            f"{name}.*누구",
                            f"{name}.*모르",
                            f"{name}.*들어본 적 없",
                        ]

                        import re

                        for pattern in ignorance_patterns:
                            if re.search(pattern, manuscript):
                                # 정당화 체크 (정보 차단 알리바이)
                                alibis = ["정보가 없는", "소문이 닿지 않", "격리된", "은둔", "변방", "오지"]

                                # NPC 주변 문맥에서 알리바이 확인
                                npc_idx = manuscript.find(name)
                                context_text = manuscript[max(0, npc_idx - 200) : min(len(manuscript), npc_idx + 200)]

                                has_alibi = any(alibi in context_text for alibi in alibis)

                                if not has_alibi:
                                    return {
                                        "check": "information_consistency",
                                        "passed": False,
                                        "reason": f"{name}가 '{event.get('description', '사건')[:50]}'을 몰라서는 안됨",
                                        "severity": "MEDIUM",
                                        "should_know_reason": knowledge_check["reason"],
                                        "required_fix": "NPC가 이미 알고 있는 것으로 수정하거나, 정보 차단 알리바이(정보 없는 변방, 격리 등) 추가 필요",
                                    }
        except Exception as e:
            # 모듈 로드 실패 등의 경우 조용히 통과
            logging.warning(f"⚠️ [Blocking] 정보 일관성 체크 실패: {e}")

        return {"check": "information_consistency", "passed": True}

    def _check_scene_completeness(self, manuscript: str, context: dict) -> dict:
        """
        [V59] 씬별 완성도 체크 - 각 씬이 최소 분량을 충족하는지 검증

        Blueprint의 각 씬에 대해:
        - 최소 300자 이상의 내용이 있어야 함
        - 너무 짧게 넘어가는 씬이 있으면 WARNING
        - 반 이상의 씬이 미달이면 REJECT
        """
        blueprint = context.get("blueprint", {})
        scene_breakdown = blueprint.get("scene_breakdown", {})

        if not scene_breakdown or not isinstance(scene_breakdown, dict):
            return {"check": "scene_completeness", "passed": True, "reason": "Blueprint 씬 정보 없음 - 체크 스킵"}

        scene_count = len(scene_breakdown)
        if scene_count == 0:
            return {"check": "scene_completeness", "passed": True}

        # 씬 키워드별로 원고 분할 시도
        scene_analysis = []
        min_scene_length = 300  # 씬당 최소 300자

        for scene_name, scene_desc in scene_breakdown.items():
            if isinstance(scene_desc, dict):  # [V70] dict 타입 방어
                scene_desc = scene_desc.get("description", scene_desc.get("content", str(scene_desc)))
            keywords = self._extract_keywords(str(scene_desc), max_keywords=5)

            # 키워드 주변 텍스트 분량 측정
            found_length = 0
            for kw in keywords:
                if kw and kw in manuscript:
                    # 키워드 위치 찾기
                    idx = manuscript.find(kw)
                    if idx != -1:
                        # 키워드 전후 500자 범위를 해당 씬으로 간주
                        start = max(0, idx - 250)
                        end = min(len(manuscript), idx + 250)
                        found_length = max(found_length, end - start)

            scene_analysis.append(
                {"scene": scene_name, "found_length": found_length, "is_complete": found_length >= min_scene_length}
            )

        # 완성된 씬 비율 계산
        complete_scenes = sum(1 for s in scene_analysis if s["is_complete"])
        incomplete_scenes = [s for s in scene_analysis if not s["is_complete"] and s["found_length"] > 0]

        # 50% 이상 씬이 미달이면 REJECT
        if complete_scenes < scene_count * 0.5:
            return {
                "check": "scene_completeness",
                "passed": False,
                "reason": f"씬 완성도 부족: {complete_scenes}/{scene_count} 씬만 완성 (최소 50% 필요)",
                "severity": "HIGH",
                "details": {
                    "complete_scenes": complete_scenes,
                    "total_scenes": scene_count,
                    "incomplete": [s["scene"] for s in incomplete_scenes],
                    "min_scene_length": min_scene_length,
                },
                "suggestion": "각 씬에 충분한 분량(최소 300자)을 할당하세요. 특히 다음 씬이 부족합니다: "
                + ", ".join([s["scene"] for s in incomplete_scenes[:3]]),
            }

        # 일부 미달이면 WARNING (통과)
        if incomplete_scenes:
            return {
                "check": "scene_completeness",
                "passed": True,
                "warning": f"일부 씬 분량 부족: {len(incomplete_scenes)}개 씬이 300자 미만",
                "details": {"incomplete_scenes": [s["scene"] for s in incomplete_scenes]},
            }

        return {"check": "scene_completeness", "passed": True}

    def _check_cliffhanger_ending(self, manuscript: str, context: dict) -> dict:
        """
        [V59] 클리프행어 엔딩 필수 검증 - 연재물의 핵심 요소

        원고 마지막 부분(500자)에서 긴장감/기대감 요소 확인:
        - 위기 상황 암시
        - 의문/미스터리 제시
        - 새로운 인물/사건 등장
        - 결정적 순간 직전 중단

        Blueprint에 cliffhanger 지시가 있으면 필수 검증
        """
        blueprint = context.get("blueprint", {})

        # Blueprint에서 cliffhanger 관련 지시 확인
        cliffhanger_required = False
        cliffhanger_hint = ""

        # 다양한 키에서 cliffhanger 찾기
        for key in ["cliffhanger", "ending", "ending_hook", "episode_ending"]:
            if key in blueprint:
                value = blueprint.get(key, "")
                if value:
                    cliffhanger_required = True
                    cliffhanger_hint = str(value)[:100]
                    break

        # Blueprint에 명시적 cliffhanger 지시가 없으면 기본 체크만
        if not cliffhanger_required:
            # 기본 체크: 원고 끝이 너무 평이하면 경고
            ending_text = manuscript[-500:] if len(manuscript) > 500 else manuscript

            # 평이한 엔딩 패턴 (문제가 될 수 있음)
            flat_ending_patterns = [
                r"잠들었다[.。]?\s*$",
                r"잠이 들었다[.。]?\s*$",
                r"평화로웠다[.。]?\s*$",
                r"아무 일 없이[.。]?\s*$",
                r"무사히 끝났다[.。]?\s*$",
                r"돌아갔다[.。]?\s*$",
                r"끝이었다[.。]?\s*$",
            ]

            for pattern in flat_ending_patterns:
                if re.search(pattern, ending_text):
                    return {
                        "check": "cliffhanger_ending",
                        "passed": True,  # 경고만 (Blueprint 미지시 시)
                        "warning": "엔딩이 평이함 - 클리프행어 요소 권장",
                        "matched_pattern": pattern,
                        "suggestion": "독자의 다음 화 기대감을 위해 긴장감 있는 엔딩 추가 고려",
                        "cliffhanger_strength": 15,  # [V60.7] 평이한 엔딩 = 낮은 점수
                        "strength_grade": "D",
                    }

            return {
                "check": "cliffhanger_ending",
                "passed": True,
                "cliffhanger_strength": 50,  # [V60.7] 기본 통과 = 중간 점수
                "strength_grade": "B",
            }

        # Blueprint에 cliffhanger 지시가 있는 경우 필수 검증
        ending_text = manuscript[-800:] if len(manuscript) > 800 else manuscript

        # 클리프행어 긍정 패턴 (있어야 함)
        cliffhanger_patterns = [
            # 위기/긴장
            r"그때[,]?\s",
            r"순간[,]?\s",
            r"갑자기",
            r"돌연",
            r"느닷없이",
            r"바로\s+그때",
            # 등장/출현
            r"나타났다",
            r"등장했다",
            r"모습을\s+드러",
            r"그림자가",
            r"발소리가",
            # 의문/미스터리
            r'\?["\']?\s*$',  # 의문문으로 끝남
            r"누구[인지]?",
            r"무엇[인지]?",
            r"어째서",
            r"왜[?]",
            # 긴박함
            r"다가오고\s+있",
            r"시작이[었]?다",
            r"끝이\s+아니",
            r"시작에\s+불과",
            r"이제부터",
            # 반전/충격
            r"그러나",
            r"하지만",
            r"그런데",
            r"예상[과]?\s+달리",
            r"뜻밖에[도]?",
            # 대화 긴장
            r"말을\s+끊",
            r"입을\s+열",
            r"목소리가\s+들려",
        ]

        has_cliffhanger = False
        matched_patterns = []

        for pattern in cliffhanger_patterns:
            if re.search(pattern, ending_text):
                has_cliffhanger = True
                matched_patterns.append(pattern)

        # Blueprint의 cliffhanger 키워드가 반영되었는지도 체크
        if cliffhanger_hint:
            hint_keywords = self._extract_keywords(cliffhanger_hint, max_keywords=5)
            hint_reflected = any(kw and kw in ending_text for kw in hint_keywords)
            if hint_reflected:
                has_cliffhanger = True

        if not has_cliffhanger:
            return {
                "check": "cliffhanger_ending",
                "passed": False,
                "reason": "Blueprint 지시된 클리프행어 누락",
                "severity": "MEDIUM",
                "details": {
                    "blueprint_cliffhanger": cliffhanger_hint,
                    "ending_excerpt": ending_text[-200:],
                },
                "suggestion": f"Blueprint에서 지시한 클리프행어를 원고 끝에 반영하세요: '{cliffhanger_hint}'",
                "quick_fixes": [
                    "위기 상황 암시로 마무리 (예: '그때, 문이 열렸다.')",
                    "의문문으로 마무리 (예: '과연 그의 정체는?')",
                    "새로운 인물 등장 암시 (예: '그림자가 다가오고 있었다.')",
                    "긴박한 상황 직전 중단 (예: '바로 그 순간이었다.')",
                ],
                "cliffhanger_strength": 0,  # [V60.7] 누락 = 0점
                "strength_grade": "F",
            }

        # [V60.7] Cliffhanger 강도 점수 계산
        strength_score = self._calculate_cliffhanger_strength(ending_text, matched_patterns, cliffhanger_hint)

        return {
            "check": "cliffhanger_ending",
            "passed": True,
            "cliffhanger_detected": True,
            "matched_patterns": matched_patterns[:3],  # 상위 3개만
            "cliffhanger_strength": strength_score,  # [V60.7] 0-100 강도 점수
            "strength_grade": self._get_strength_grade(strength_score),
        }

    def _calculate_cliffhanger_strength(
        self, ending_text: str, matched_patterns: list[str], blueprint_hint: str
    ) -> int:
        """
        [V60.7] Cliffhanger 강도 점수 계산 (0-100)

        점수 구성:
        - 기본 점수: 매칭된 패턴 수 × 15 (최대 60)
        - 위치 보너스: 마지막 100자 내 패턴 +20
        - Blueprint 힌트 반영 보너스: +15
        - 긴장감 키워드 보너스: +5 (각각)
        """
        score = 0

        # 1. 기본 점수: 패턴 매칭 수
        pattern_count = len(matched_patterns)
        score += min(pattern_count * 15, 60)

        # 2. 위치 보너스: 마지막 100자 내 패턴 존재
        last_100 = ending_text[-100:] if len(ending_text) > 100 else ending_text
        has_ending_pattern = False
        for pattern in matched_patterns:
            try:
                if re.search(pattern, last_100):
                    has_ending_pattern = True
                    break
            except re.error:
                continue

        if has_ending_pattern:
            score += 20

        # 3. Blueprint 힌트 반영 보너스
        if blueprint_hint:
            hint_keywords = [w for w in blueprint_hint.split() if len(w) >= 2][:5]
            reflected = sum(1 for kw in hint_keywords if kw in ending_text)
            if reflected > 0:
                score += min(reflected * 5, 15)

        # 4. 고강도 긴장 키워드 보너스
        high_tension_keywords = [
            "죽음",
            "위기",
            "절체절명",
            "최후",
            "비밀",
            "충격",
            "반전",
            "배신",
            "정체",
            "진실",
            "비극",
            "운명",
            "결전",
            "대결",
        ]
        tension_count = sum(1 for kw in high_tension_keywords if kw in ending_text)
        score += min(tension_count * 3, 15)

        return min(score, 100)

    def _get_strength_grade(self, score: int) -> str:
        """[V60.7] 강도 점수를 등급으로 변환"""
        if score >= 80:
            return "S"  # 매우 강함
        elif score >= 60:
            return "A"  # 강함
        elif score >= 40:
            return "B"  # 보통
        elif score >= 20:
            return "C"  # 약함
        else:
            return "D"  # 매우 약함
