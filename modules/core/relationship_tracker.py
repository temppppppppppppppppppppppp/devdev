"""
[Phase 2.1] Relationship State Machine
NPC-주인공 관계의 상태 전환 추적 및 검증
"""


class RelationshipTracker:
    """NPC-주인공 관계의 상태 전환 추적 (유한 상태 머신)"""

    # 관계 상태 정의 (State Machine)
    STATES = {
        "적대": {"can_transition_to": ["굴복", "사망", "추방", "배신"]},
        "무시": {"can_transition_to": ["의심", "적대", "경외", "중립"]},
        "의심": {"can_transition_to": ["경외", "무시", "적대", "중립"]},
        "중립": {"can_transition_to": ["의심", "경외", "적대", "무시"]},
        "경외": {"can_transition_to": ["충성", "배신"]},  # 경외 → 무시는 불가능!
        "충성": {"can_transition_to": ["배신", "희생", "사망"]},
        "굴복": {"can_transition_to": ["복수", "충성", "사망"]},
        "배신": {"can_transition_to": ["사망", "추방", "굴복"]},
        "사망": {"can_transition_to": []},  # 최종 상태
        "추방": {"can_transition_to": []},  # 최종 상태
        "희생": {"can_transition_to": []}   # 최종 상태
    }

    # 상태 감지 키워드 (원고에서 자동 추론)
    STATE_KEYWORDS = {
        "경외": ["경외", "두려워", "떨며", "감히 못", "눈을 피", "공포", "벌벌 떨"],
        "무시": ["무시", "비웃", "하찮", "하인 취급", "깔보", "대수롭지 않"],
        "적대": ["적대", "원수", "죽이겠", "공격", "증오", "살의"],
        "굴복": ["굴복", "용서를", "목숨을 구걸", "바닥을 기", "살려주", "복종"],
        "사망": ["죽었", "숨이 끊", "사망", "절명", "목숨을 잃"],
        "충성": ["충성", "목숨 바쳐", "명을 따르", "충복", "따르겠"],
        "배신": ["배신", "뒤통수", "배반", "거짓", "등을 돌"],
        "추방": ["추방", "쫓겨", "내쫓", "떠나라", "출입 금지"],
        "의심": ["의심", "수상", "이상하", "믿을 수 없", "의구심"],
        "중립": ["중립", "무관심", "평범", "별다른", "무덤덤"]
    }

    def validate_transition(self, npc_name: str, old_state: str, new_state: str) -> dict:
        """
        관계 상태 전환 가능 여부 검증

        Args:
            npc_name: NPC 이름
            old_state: 이전 관계 상태
            new_state: 새로운 관계 상태

        Returns:
            {
                "valid": bool,
                "reason": str,
                "allowed_transitions": list,
                "required": str
            }
        """
        # 알 수 없는 상태는 통과
        if old_state == "알 수 없음" or new_state == "알 수 없음":
            return {"valid": True}

        # 상태가 변하지 않으면 항상 통과
        if old_state == new_state:
            return {"valid": True}

        # 허용된 전환인지 확인
        allowed = self.STATES.get(old_state, {}).get("can_transition_to", [])

        if new_state not in allowed:
            return {
                "valid": False,
                "reason": f"{npc_name}의 관계: '{old_state}' → '{new_state}' 전환 불가능",
                "allowed_transitions": allowed,
                "required": f"'{old_state}'에서 '{new_state}'로 가려면 중간 단계 또는 명시적 사건 필요"
            }

        return {"valid": True}

    def infer_state_from_manuscript(self, npc_name: str, manuscript: str) -> str:
        """
        원고에서 NPC의 현재 관계 상태 추론

        Args:
            npc_name: NPC 이름
            manuscript: 원고 텍스트

        Returns:
            str: 추론된 관계 상태
        """
        # NPC가 등장하지 않으면 알 수 없음
        if npc_name not in manuscript:
            return "알 수 없음"

        # NPC 주변 문맥 추출 (앞뒤 200자)
        npc_idx = manuscript.find(npc_name)
        context_start = max(0, npc_idx - 200)
        context_end = min(len(manuscript), npc_idx + 200)
        context = manuscript[context_start:context_end]

        # 키워드 매칭 (우선순위: 최종 상태 > 강한 감정 > 중립)
        priority_order = [
            "사망", "추방", "희생",  # 최종 상태
            "배신", "적대", "굴복",  # 강한 감정
            "경외", "충성",          # 긍정적 강한 관계
            "무시", "의심",          # 부정적 약한 관계
            "중립"                   # 기본
        ]

        for state in priority_order:
            keywords = self.STATE_KEYWORDS.get(state, [])
            if any(kw in context for kw in keywords):
                return state

        return "중립"

    def get_relationship_history(self, context, npc_name: str, current_ep: int) -> list:
        """
        NPC의 관계 변화 이력 조회

        Args:
            context: ProjectContext
            npc_name: NPC 이름
            current_ep: 현재 에피소드

        Returns:
            list: [{ep_num, state}, ...]
        """
        history = []

        try:
            for ep in range(1, current_ep):
                # state_log에서 관계 정보 추출
                log_data = context.db.load_state_log(ep)

                if log_data and isinstance(log_data, dict):
                    data = log_data.get('data', {})
                    if isinstance(data, dict):
                        npc_states = data.get('npc_relationships', {})
                        if npc_name in npc_states:
                            history.append({
                                'ep_num': ep,
                                'state': npc_states[npc_name]
                            })
        except Exception:
            pass  # 조용히 실패

        return history
