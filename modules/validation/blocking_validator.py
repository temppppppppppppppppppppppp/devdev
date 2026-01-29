"""
[V0128] TIER 1: BLOCKING Validator
Python 기반 필수 검증 (LLM 호출 불필요)
"""
import re
from typing import Dict, List, Any


class BlockingValidator:
    """
    TIER 1: 반드시 통과해야 하는 핵심 검증

    실패 시 즉시 REJECT - 수정 필수
    최소한의 항목만 포함하여 통과율 유지
    """

    def __init__(self, context=None):
        self.context = context

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
        if not dead_npc_check['passed']:
            failures.append(dead_npc_check)

        # 2. 미획득 아이템 사용
        unowned_item_check = self._check_unowned_item_usage(manuscript, validation_context)
        if not unowned_item_check['passed']:
            failures.append(unowned_item_check)

        # 3. 파괴된 장소 방문
        destroyed_location_check = self._check_destroyed_location_visit(manuscript, validation_context)
        if not destroyed_location_check['passed']:
            failures.append(destroyed_location_check)

        # 4. 분량 미달
        length_check = self._check_minimum_length(manuscript, validation_context)
        if not length_check['passed']:
            failures.append(length_check)

        # 5. 필수 씬 누락 (MANUSCRIPT 모드만)
        if validation_context.get('mode') == 'MANUSCRIPT':
            scene_check = self._check_required_scenes(manuscript, validation_context)
            if not scene_check['passed']:
                failures.append(scene_check)

        return {
            "tier": "BLOCKING",
            "passed": len(failures) == 0,
            "failures": failures,
            "message": "REJECT - 필수 수정 필요" if failures else "PASS",
            "failure_count": len(failures)
        }

    def _check_dead_npc_resurrection(self, manuscript: str, context: dict) -> dict:
        """사망한 NPC 재등장 체크"""
        encyclopedia = context.get('encyclopedia', {})
        npcs = encyclopedia.get('npcs', [])

        dead_npcs = [npc for npc in npcs if npc.get('status') == 'dead']

        for npc in dead_npcs:
            name = npc.get('name', '')
            aliases = npc.get('aliases', [])

            # 이름 또는 별칭이 원고에 등장하는지 체크
            for identifier in [name] + aliases:
                if identifier and identifier in manuscript:
                    return {
                        "check": "dead_npc_resurrection",
                        "passed": False,
                        "reason": f"사망한 NPC '{name}' 재등장",
                        "severity": "CRITICAL",
                        "location": manuscript.find(identifier)
                    }

        return {"check": "dead_npc_resurrection", "passed": True}

    def _check_unowned_item_usage(self, manuscript: str, context: dict) -> dict:
        """미획득 아이템 사용 체크 (타입 안전성 강화)"""
        encyclopedia = context.get('encyclopedia', {})
        martial_hud = context.get('martial_hud', {})

        # HUD에서 소유 아이템 목록 (방어적 추출)
        owned_items = []
        if isinstance(martial_hud, dict):
            actual_truth = martial_hud.get('actual_truth', {})
            if isinstance(actual_truth, dict):
                equipment = actual_truth.get('equipment', [])

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
                        str(k) for k, v in equipment.items()
                        if k and v and isinstance(k, (str, int)) and len(str(k)) > 0
                    ]
                else:
                    # 예상치 못한 타입
                    print(f"[WARNING] Unexpected equipment type: {type(equipment).__name__}")
                    print(f"[WARNING] Equipment value: {repr(equipment)[:100]}")
                    owned_items = []

        # 최종 안전성 확인 (강화)
        if not isinstance(owned_items, list):
            print(f"[ERROR] owned_items is not a list after processing: {type(owned_items).__name__}")
            owned_items = []

        # 각 원소가 문자열이고 비어있지 않은지 확인
        owned_items = [item for item in owned_items if isinstance(item, str) and len(item) > 0]

        # 아이템 풀
        all_items = encyclopedia.get('items', [])

        for item in all_items:
            item_name = item.get('name', '')
            if not item_name:
                continue

            # 원고에 등장하는데 소유하지 않음
            if item_name in manuscript and item_name not in owned_items:
                # "혼철대도를 보았다"는 OK, "혼철대도를 휘둘렀다"는 NG
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
                    f"{item_name}을 뽑"
                ]

                # 부정문 패턴 (오탐 방지)
                negation_patterns = [
                    f"{item_name}을 휘두르지",
                    f"{item_name}를 휘두르지",
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
                    f"{item_name}에 대해"
                ]

                for pattern in usage_patterns:
                    if pattern in manuscript:
                        # 부정문 체크 (오탐 방지)
                        location = manuscript.find(pattern)
                        context_start = max(0, location - 50)
                        context_end = min(len(manuscript), location + len(pattern) + 50)
                        context = manuscript[context_start:context_end]

                        # 부정문이면 pass
                        is_negation = any(neg in context for neg in negation_patterns)
                        if is_negation:
                            continue

                        return {
                            "check": "unowned_item_usage",
                            "passed": False,
                            "reason": f"미획득 아이템 '{item_name}' 사용",
                            "severity": "CRITICAL",
                            "owned_items": owned_items,
                            "location": location,
                            "context": context
                        }

        return {"check": "unowned_item_usage", "passed": True}

    def _check_destroyed_location_visit(self, manuscript: str, context: dict) -> dict:
        """파괴된 장소 방문 체크"""
        encyclopedia = context.get('encyclopedia', {})
        locations = encyclopedia.get('locations', [])

        destroyed_locations = [loc for loc in locations if loc.get('status') == 'destroyed']

        for loc in destroyed_locations:
            name = loc.get('name', '')
            if not name:
                continue

            # "불탄 객잔"은 OK, "객잔에 들어갔다"는 NG
            visit_patterns = [
                f"{name}에 들어",
                f"{name}로 들어",
                f"{name}에 도착",
                f"{name}에서 묵",
                f"{name}의 방"
            ]

            for pattern in visit_patterns:
                if pattern in manuscript:
                    return {
                        "check": "destroyed_location_visit",
                        "passed": False,
                        "reason": f"파괴된 장소 '{name}' 정상 방문",
                        "severity": "CRITICAL",
                        "location": manuscript.find(pattern)
                    }

        return {"check": "destroyed_location_visit", "passed": True}

    def _check_minimum_length(self, manuscript: str, context: dict) -> dict:
        """최소 분량 체크"""
        mode = context.get('mode', 'MANUSCRIPT')

        if mode == 'BLUEPRINT':
            threshold = 500
        else:  # MANUSCRIPT
            threshold = 4000

        length = len(manuscript)

        if length < threshold:
            return {
                "check": "minimum_length",
                "passed": False,
                "reason": f"분량 미달: {length}자 (최소 {threshold}자)",
                "severity": "CRITICAL",
                "current_length": length,
                "threshold": threshold
            }

        return {"check": "minimum_length", "passed": True}

    def _check_required_scenes(self, manuscript: str, context: dict) -> dict:
        """필수 씬 포함 체크 (MANUSCRIPT 모드만)"""
        blueprint = context.get('blueprint', {})
        scene_breakdown = blueprint.get('scene_breakdown', {})

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
            keywords = self._extract_keywords(scene_desc)

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
                "total_scenes": scene_count
            }

        return {"check": "required_scenes", "passed": True}

    def _extract_keywords(self, text: str, max_keywords: int = 3) -> List[str]:
        """텍스트에서 핵심 키워드 추출 (간단한 휴리스틱)"""
        # 명사 추출 (한글 2글자 이상)
        pattern = r'[가-힣]{2,}'
        words = re.findall(pattern, text)

        # 불용어 제거
        stopwords = {'것이다', '있다', '없다', '하다', '되다', '이다', '그', '저', '이', '그것', '저것'}
        keywords = [w for w in words if w not in stopwords]

        # 상위 N개 반환
        return keywords[:max_keywords]
