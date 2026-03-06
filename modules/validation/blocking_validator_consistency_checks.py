"""[R5-2a] BlockingValidator consistency checks submodule."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modules.validation.blocking_validator import BlockingValidator

# [Phase 4.2] Justification pattern ???
try:
    from modules.core.justification_patterns import get_justification_guide, get_pattern_description

    JUSTIFICATION_AVAILABLE = True
except ImportError:
    JUSTIFICATION_AVAILABLE = False
    logging.warning("?? [BlockingValidator] justification_patterns ?? ?? ?? - ?? ?? ????")


class BlockingValidatorConsistencyChecks:
    """Consistency checks for capability/authority/relationship/information."""

    def __init__(self, host: BlockingValidator) -> None:
        self.host = host

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

        violation_location = 0
        violation_context = ""

        for pattern in strong_action_patterns:
            match = re.search(pattern, manuscript)
            if match:
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
        reputation = actual_truth.get("reputation")
        # [TF-3] dict/list/None → "미초기화"로 간주하여 체크 스킵
        if isinstance(reputation, dict | list) or reputation is None:
            reputation = -1  # 미초기화 센티널
        else:
            try:  # [V70] DB TEXT 타입 방어
                reputation = int(reputation) if not isinstance(reputation, int | float) else reputation
            except (ValueError, TypeError):
                reputation = -1  # 변환 불가 → 미초기화

        if not isinstance(status_tags, list):
            status_tags = []

        # 낮은 지위 태그
        low_status_tags = ["하인", "노예", "평민", "무명", "낭인", "거지"]
        has_low_status = any(tag in status_tags for tag in low_status_tags)
        # [TF-3] reputation < 0 = 미초기화 → low_reputation 판정 제외
        has_low_reputation = 0 <= reputation < 20

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
        except (ImportError, TypeError, AttributeError):
            raise  # [V-I4] 프로그래밍 오류는 조기 발견을 위해 re-raise
        except (ValueError, KeyError, RuntimeError) as e:
            logging.warning(f"[C-3] relationship consistency check failed (degraded): {e}")
            return {"check": "relationship_consistency", "passed": True, "degraded": True, "error": str(e)}

        return {"check": "relationship_consistency", "passed": True}

    def _check_information_consistency(self, manuscript: str, context: dict) -> dict:
        """[Phase 2.2] 정보 일관성 체크 (NPC가 알아야 할 것을 모르는가?)"""
        try:
            from modules.core.information_diffusion import InformationDiffusion

            # context 객체가 필요 (self.host.context가 있는 경우에만 동작)
            if not self.host or not self.host.context:
                return {"check": "information_consistency", "passed": True}

            diffusion = InformationDiffusion(self.host.context)
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
                        name_esc = re.escape(name)
                        ignorance_patterns = [
                            f"{name_esc}.*알지 못",
                            f"{name_esc}.*처음 듣",
                            f"{name_esc}.*누구",
                            f"{name_esc}.*모르",
                            f"{name_esc}.*들어본 적 없",
                        ]

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
        except (ImportError, TypeError, AttributeError):
            raise  # [V-I4] 프로그래밍 오류는 조기 발견을 위해 re-raise
        except (ValueError, KeyError, RuntimeError) as e:
            logging.warning(f"[C-3] information consistency check failed (degraded): {e}")
            return {"check": "information_consistency", "passed": True, "degraded": True, "error": str(e)}

        return {"check": "information_consistency", "passed": True}

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
