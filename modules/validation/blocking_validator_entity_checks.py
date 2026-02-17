"""[R5-2a] BlockingValidator entity checks submodule."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modules.validation.blocking_validator import BlockingValidator


class BlockingValidatorEntityChecks:
    """Entity-level blocking checks for NPC/item/location states."""

    def __init__(self, host: BlockingValidator) -> None:
        self.host = host

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
            logging.warning(f"[WARNING] owned_items is not a list after processing: {type(owned_items).__name__}")
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
