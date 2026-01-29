"""
[V0128] TIER 1: BLOCKING Validator
Python 기반 필수 검증 (LLM 호출 불필요)

[Phase 4.2] Justification 제안 기능 추가
"""
import re
from typing import Dict, List, Any

# [Phase 4.2] Justification pattern 임포트
try:
    from modules.core.justification_patterns import get_justification_guide, get_pattern_description
    JUSTIFICATION_AVAILABLE = True
except ImportError:
    JUSTIFICATION_AVAILABLE = False
    print("⚠️ [BlockingValidator] justification_patterns 모듈 로드 실패 - 제안 기능 비활성화")


class BlockingValidator:
    """
    TIER 1: 반드시 통과해야 하는 핵심 검증

    실패 시 즉시 REJECT - 수정 필수
    최소한의 항목만 포함하여 통과율 유지
    """

    def __init__(self, context=None, enable_justification_checks=False):
        """
        Args:
            context: ProjectContext 객체 (정보 일관성 체크용)
            enable_justification_checks: Phase 4 정당화 체크 활성화 (기본값: False)
                - True 시 물리적 능력, 권위 행사 등 제약 위반을 감지하고 정당화 패턴 제안
                - 서사 관성 극복을 위한 옵션 (통과율 약간 감소 가능)
        """
        self.context = context
        self.enable_justification_checks = enable_justification_checks

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

        # [Phase 2.1] 6. 관계 일관성 체크 (관계 역행 방지)
        relationship_check = self._check_relationship_consistency(manuscript, validation_context)
        if not relationship_check['passed']:
            failures.append(relationship_check)

        # [Phase 2.2] 7. 정보 일관성 체크 (NPC가 알아야 할 것을 모르는가?)
        information_check = self._check_information_consistency(manuscript, validation_context)
        if not information_check['passed']:
            failures.append(information_check)

        # [Phase 4.2] 8. 물리적 능력 체크 (옵션, 정당화 제안 포함)
        if self.enable_justification_checks:
            physical_check = self._check_physical_capability(manuscript, validation_context)
            if not physical_check['passed']:
                failures.append(physical_check)

        # [Phase 4.2] 9. 권위 행사 체크 (옵션, 정당화 제안 포함)
        if self.enable_justification_checks:
            authority_check = self._check_authority_exercise(manuscript, validation_context)
            if not authority_check['passed']:
                failures.append(authority_check)

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
                # "[아이템]을 보았다"는 OK, "[아이템]을 휘둘렀다"는 NG
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

                        # [V44 Fix] 문장 경계 찾기 (find() -1 반환 안전 처리)
                        def find_sentence_start(text, pos):
                            """위치 이전의 가장 가까운 문장 끝 찾기"""
                            candidates = []
                            for delim in '.!?':
                                idx = text.rfind(delim, 0, pos)
                                if idx != -1:
                                    candidates.append(idx + 1)
                            return max(candidates) if candidates else 0

                        def find_sentence_end(text, pos):
                            """위치 이후의 가장 가까운 문장 끝 찾기"""
                            candidates = []
                            for delim in '.!?':
                                idx = text.find(delim, pos)
                                if idx != -1:
                                    candidates.append(idx)
                            return min(candidates) if candidates else len(text)

                        sentence_start = find_sentence_start(manuscript, location)
                        sentence_end = find_sentence_end(manuscript, location + len(pattern))

                        context = manuscript[sentence_start:sentence_end + 1]

                        # 부정문이면 pass - 같은 문장 내에 부정 표현이 있어야 함
                        is_negation = any(neg in context for neg in negation_patterns)
                        # [V44 Fix] 추가 부정 키워드 체크 (문장 내 직접 부정)
                        negation_keywords = ["않았", "못했", "없었", "아니었", "안 했", "못 했", "아직"]
                        has_direct_negation = any(nk in context for nk in negation_keywords)
                        if is_negation or has_direct_negation:
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

    def _check_physical_capability(self, manuscript: str, context: dict) -> dict:
        """
        [Phase 4.2] 물리적 능력 제약 체크

        나약한 신체 상태에서 강력한 행동을 수행하는 경우 감지
        정당화 패턴 제안 포함
        """
        if not JUSTIFICATION_AVAILABLE:
            return {"check": "physical_capability", "passed": True}

        martial_hud = context.get('martial_hud', {})
        genre = context.get('genre', 'wuxia')

        # HUD에서 신체 상태 태그 추출
        actual_truth = martial_hud.get('actual_truth', {})
        physical_tags = actual_truth.get('physical_tags', [])

        if not isinstance(physical_tags, list):
            physical_tags = []

        # 나약함 태그
        weak_tags = ['나약', '중독', '부상', '중상', '쇠약', '기력고갈', '기혈역류']
        is_weak = any(tag in physical_tags for tag in weak_tags)

        if not is_weak:
            return {"check": "physical_capability", "passed": True}

        # 강력한 행동 패턴
        strong_action_patterns = [
            r'무거운.{0,5}들어올',
            r'\d{2,}근.{0,5}대도',
            r'일격에.{0,5}박살',
            r'단번에.{0,5}격파',
            r'힘껏.{0,5}휘두',
            r'거대한.{0,5}무기',
            r'돌진하여.{0,5}부딪',
            r'벽을.{0,5}부수',
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
                    '발경', '기혈', '폭발', '대가', '고통', '뼈마디',
                    '전생', '체득', '기억', '경험', '요령',
                    '순간적', '짜내', '역류'
                ]

                has_justification = any(kw in violation_context for kw in justification_keywords)

                if not has_justification:
                    # 정당화 없음 - 제안 제공
                    pattern_desc = get_pattern_description(genre, 'weak_body_strong_action')
                    justification_guide = get_justification_guide(genre, 'weak_body_strong_action')

                    return {
                        "check": "physical_capability",
                        "passed": False,
                        "reason": f"나약한 신체 상태({', '.join([t for t in physical_tags if t in weak_tags])})에서 강력한 행동 수행",
                        "severity": "MEDIUM",
                        "location": violation_location,
                        "context": violation_context,
                        "suggested_pattern": pattern_desc,
                        "justification_guide": justification_guide,
                        "fix_template": "'{행동}' 직전 또는 중간에 정당화 문구를 추가하십시오. 예: '전생의 발경법으로 팔목 기혈을 폭발시켰다. 뼈마디가 어긋나는 고통이 밀려왔지만...'",
                        "quick_fixes": [
                            "전생 기억/경험을 활용한 효율적 방법",
                            "기혈을 짜내며 순간 폭발력 (부작용 명시)",
                            "특수 기법으로 힘의 방향 전환 (대가 표현)"
                        ]
                    }

        return {"check": "physical_capability", "passed": True}

    def _check_authority_exercise(self, manuscript: str, context: dict) -> dict:
        """
        [Phase 4.2] 권위 행사 제약 체크

        낮은 지위에서 높은 권위를 행사하는 경우 감지
        정당화 패턴 제안 포함
        """
        if not JUSTIFICATION_AVAILABLE:
            return {"check": "authority_exercise", "passed": True}

        martial_hud = context.get('martial_hud', {})
        genre = context.get('genre', 'wuxia')

        # HUD에서 권위 관련 데이터 추출
        actual_truth = martial_hud.get('actual_truth', {})
        status_tags = actual_truth.get('status_tags', [])
        reputation = actual_truth.get('reputation', 0)

        if not isinstance(status_tags, list):
            status_tags = []

        # 낮은 지위 태그
        low_status_tags = ['하인', '노예', '평민', '무명', '낭인', '거지']
        has_low_status = any(tag in status_tags for tag in low_status_tags)
        has_low_reputation = reputation < 20

        if not (has_low_status or has_low_reputation):
            return {"check": "authority_exercise", "passed": True}

        # 높은 권위 행동 패턴
        high_authority_patterns = [
            r'명령했다',
            r'지시했다',
            r'단호하게.{0,5}말했다',
            r'복종하라',
            r'따르라고',
            r'감히.{0,5}거역',
            r'명을.{0,5}내렸다'
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
                    '살기', '기세', '압도', '눈빛', '위압',
                    '전생', '경험', '자신감',
                    '실력', '무력', '힘'
                ]

                has_justification = any(kw in violation_context for kw in justification_keywords)

                if not has_justification:
                    pattern_desc = get_pattern_description(genre, 'low_status_high_authority')
                    justification_guide = get_justification_guide(genre, 'low_status_high_authority')

                    return {
                        "check": "authority_exercise",
                        "passed": False,
                        "reason": f"낮은 지위(reputation: {reputation}, tags: {status_tags})에서 명령/지시 행위",
                        "severity": "MEDIUM",
                        "location": violation_location,
                        "context": violation_context,
                        "suggested_pattern": pattern_desc,
                        "justification_guide": justification_guide,
                        "fix_template": "'{행동}' 전에 권위 정당화 추가. 예: '전생의 기억이 만든 절대적 자신감이 눈빛에 담겼다.'",
                        "quick_fixes": [
                            "전생 경험에서 나오는 자연스러운 기세/눈빛",
                            "무력 시연으로 두려움 유발",
                            "살기/위압으로 본능적 복종 유도"
                        ]
                    }

        return {"check": "authority_exercise", "passed": True}

    def _check_relationship_consistency(self, manuscript: str, context: dict) -> dict:
        """[Phase 2.1] 관계 일관성 체크 (관계 역행 방지)"""
        try:
            from modules.core.relationship_tracker import RelationshipTracker

            tracker = RelationshipTracker()
            encyclopedia = context.get('encyclopedia', {})
            npcs = encyclopedia.get('npcs', [])
            current_ep = context.get('ep_num', 0)

            for npc in npcs:
                if not isinstance(npc, dict):
                    continue

                name = npc.get('name', '')
                if not name or name not in manuscript:
                    continue  # 등장하지 않으면 스킵

                # 이전 관계 상태 (Bible 또는 encyclopedia에서)
                prev_relationship = npc.get('relationship_state', '중립')

                # 원고에서 현재 관계 추론
                current_relationship = tracker.infer_state_from_manuscript(name, manuscript)

                if current_relationship != "알 수 없음":
                    # 전환 가능성 검증
                    validation = tracker.validate_transition(name, prev_relationship, current_relationship)

                    if not validation['valid']:
                        return {
                            "check": "relationship_consistency",
                            "passed": False,
                            "reason": validation['reason'],
                            "severity": "HIGH",
                            "npc": name,
                            "transition": f"{prev_relationship} → {current_relationship}",
                            "allowed_transitions": validation.get('allowed_transitions', []),
                            "required_fix": validation.get('required', '')
                        }
        except Exception as e:
            # 모듈 로드 실패 등의 경우 조용히 통과
            print(f"      ⚠️ [Blocking] 관계 일관성 체크 실패: {e}")

        return {"check": "relationship_consistency", "passed": True}

    def _check_information_consistency(self, manuscript: str, context: dict) -> dict:
        """[Phase 2.2] 정보 일관성 체크 (NPC가 알아야 할 것을 모르는가?)"""
        try:
            from modules.core.information_diffusion import InformationDiffusion

            # context 객체가 필요 (self.context가 있는 경우에만 동작)
            if not self.context:
                return {"check": "information_consistency", "passed": True}

            diffusion = InformationDiffusion(self.context)
            current_ep = context.get('ep_num', 0)
            encyclopedia = context.get('encyclopedia', {})
            npcs = encyclopedia.get('npcs', [])

            # 주요 사건 로드
            major_events = diffusion.load_major_events()

            if not major_events:
                return {"check": "information_consistency", "passed": True}

            for npc in npcs:
                if not isinstance(npc, dict):
                    continue

                name = npc.get('name', '')
                if not name or name not in manuscript:
                    continue  # 등장하지 않으면 스킵

                # 최근 3개 주요 사건만 체크 (성능 고려)
                for event in major_events[-3:]:
                    knowledge_check = diffusion.should_npc_know(npc, event, current_ep)

                    if knowledge_check['should_know']:
                        # NPC가 알아야 하는 사건인데, 원고에서 모르는 것처럼 행동하는가?
                        ignorance_patterns = [
                            f"{name}.*알지 못",
                            f"{name}.*처음 듣",
                            f"{name}.*누구",
                            f"{name}.*모르",
                            f"{name}.*들어본 적 없"
                        ]

                        import re
                        for pattern in ignorance_patterns:
                            if re.search(pattern, manuscript):
                                # 정당화 체크 (정보 차단 알리바이)
                                alibis = [
                                    "정보가 없는",
                                    "소문이 닿지 않",
                                    "격리된",
                                    "은둔",
                                    "변방",
                                    "오지"
                                ]

                                # NPC 주변 문맥에서 알리바이 확인
                                npc_idx = manuscript.find(name)
                                context_text = manuscript[max(0, npc_idx-200):min(len(manuscript), npc_idx+200)]

                                has_alibi = any(alibi in context_text for alibi in alibis)

                                if not has_alibi:
                                    return {
                                        "check": "information_consistency",
                                        "passed": False,
                                        "reason": f"{name}가 '{event.get('description', '사건')[:50]}'을 몰라서는 안됨",
                                        "severity": "MEDIUM",
                                        "should_know_reason": knowledge_check['reason'],
                                        "required_fix": "NPC가 이미 알고 있는 것으로 수정하거나, 정보 차단 알리바이(정보 없는 변방, 격리 등) 추가 필요"
                                    }
        except Exception as e:
            # 모듈 로드 실패 등의 경우 조용히 통과
            print(f"      ⚠️ [Blocking] 정보 일관성 체크 실패: {e}")

        return {"check": "information_consistency", "passed": True}
