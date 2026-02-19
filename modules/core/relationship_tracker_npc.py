"""[R5-2b] RelationshipTracker NPC submodule."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from modules.core.relationship_tracker import RelationshipEvent

if TYPE_CHECKING:
    from modules.core.relationship_tracker import RelationshipTracker


class RelationshipTrackerNPC:
    """NPC relationship state machine and transition tracking."""

    def __init__(self, host: RelationshipTracker) -> None:
        self.host = host

    STATES = {
        "적대": {"can_transition_to": ["굴복", "사망", "추방", "의심"]},  # [V55.5] 의심 추가 (화해 가능)
        "무시": {"can_transition_to": ["의심", "적대", "중립"]},  # [V55.5] 경외 직행 제거 (의심 거쳐야 함)
        "의심": {"can_transition_to": ["경외", "무시", "적대", "중립"]},
        "중립": {"can_transition_to": ["의심", "적대", "무시"]},  # [V55.5] 경외 직행 제거
        "경외": {"can_transition_to": ["충성", "의심"]},  # [V55.5] 배신→의심으로 변경 (급변 방지)
        "충성": {"can_transition_to": ["경외", "희생", "사망"]},  # [V55.5] 배신 제거 (배신은 경외 거쳐야)
        "굴복": {"can_transition_to": ["의심", "충성", "사망"]},  # [V55.5] 복수→의심 (더 자연스러움)
        "배신": {"can_transition_to": ["사망", "추방", "굴복"]},
        "사망": {"can_transition_to": []},  # 최종 상태
        "추방": {"can_transition_to": []},  # 최종 상태
        "희생": {"can_transition_to": []},  # 최종 상태
    }

    RISKY_TRANSITIONS = {
        ("무시", "의심"): "주인공의 실력 또는 정체 의심이 시작되어야 함",
        ("의심", "경외"): "압도적 무력 시현 또는 지위 확인 필요",
        ("경외", "충성"): "지속적 존경 + 결정적 은혜/구명 필요",
        ("적대", "의심"): "적대 감정을 누그러뜨릴 사건 필요",
        ("굴복", "충성"): "용서 + 새로운 기회 부여 필요",
    }

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
        "중립": ["중립", "무관심", "평범", "별다른", "무덤덤"],
    }

    TRANSITION_REQUIREMENTS = {
        # 불가능한 전환 (FSM에서 차단됨)
        ("무시", "경외"): "불가능 - 의심 단계를 거쳐야 함 (무시→의심→경외)",
        ("무시", "충성"): "불가능 - 경외 단계를 거쳐야 함 (무시→의심→경외→충성)",
        ("의심", "충성"): "불가능 - 경외 단계를 거쳐야 함 (의심→경외→충성)",
        ("적대", "충성"): "불가능 - 굴복과 경외 단계를 거쳐야 함",
        ("중립", "경외"): "불가능 - 의심 단계를 거쳐야 함 (중립→의심→경외)",
        ("중립", "충성"): "불가능 - 의심과 경외 단계를 거쳐야 함",
        # 가능하지만 정당화 필요한 전환
        ("의심", "경외"): "압도적 무력 시현 또는 정체 확인 필요 (예: 전설적 무공 시전)",
        ("경외", "충성"): "지속적인 존경 + 결정적 은혜 필요 (예: 목숨을 구해줌)",
        ("굴복", "충성"): "용서 + 새로운 기회 부여 필요 (예: 죄를 묻지 않고 재기 기회 부여)",
        ("적대", "의심"): "적대 감정을 누그러뜨릴 사건 필요 (예: 공통의 적 등장)",
        ("무시", "의심"): "주인공의 실력 또는 정체 의심 시작 (예: 기이한 행동 목격)",
    }

    def validate_transition(self, npc_name: str, old_state: str, new_state: str) -> dict:
        """
        관계 상태 전환 가능 여부 검증

        [V55.5] 강화: 위험한 전환도 경고 반환

        Args:
            npc_name: NPC 이름
            old_state: 이전 관계 상태
            new_state: 새로운 관계 상태

        Returns:
            {
                "valid": bool,
                "reason": str,
                "allowed_transitions": list,
                "required": str,
                "risky": bool,  # [V55.5] 위험한 전환 여부
                "risk_warning": str  # [V55.5] 위험 경고 메시지
            }
        """
        # 알 수 없는 상태는 통과
        if old_state == "알 수 없음" or new_state == "알 수 없음":
            return {"valid": True, "risky": False}

        # 상태가 변하지 않으면 항상 통과
        if old_state == new_state:
            return {"valid": True, "risky": False}

        # 허용된 전환인지 확인
        allowed = self.STATES.get(old_state, {}).get("can_transition_to", [])

        if new_state not in allowed:
            # [V55.5] 더 구체적인 에러 메시지
            suggested_path = self._suggest_transition_path(old_state, new_state)
            return {
                "valid": False,
                "reason": f"{npc_name}의 관계: '{old_state}' → '{new_state}' 전환 불가능",
                "allowed_transitions": allowed,
                "required": f"'{old_state}'에서 '{new_state}'로 가려면 중간 단계 필요",
                "suggested_path": suggested_path,
                "risky": False,
            }

        # [V55.5] 위험한 전환 체크
        transition_key = (old_state, new_state)
        if transition_key in self.RISKY_TRANSITIONS:
            return {
                "valid": True,
                "risky": True,
                "risk_warning": self.RISKY_TRANSITIONS[transition_key],
                "reason": f"위험한 전환: '{old_state}' → '{new_state}'는 강한 정당화 필요",
            }

        return {"valid": True, "risky": False}

    def _suggest_transition_path(self, from_state: str, to_state: str) -> str:
        """
        [V55.5] 불가능한 전환에 대해 권장 경로 제안

        Args:
            from_state: 시작 상태
            to_state: 목표 상태

        Returns:
            권장 경로 문자열
        """
        # 일반적인 긍정적 관계 발전 경로
        positive_path = ["무시", "의심", "경외", "충성"]

        # 부정적 관계 경로
        negative_path = ["무시", "적대", "굴복"]

        try:
            if from_state in positive_path and to_state in positive_path:
                from_idx = positive_path.index(from_state)
                to_idx = positive_path.index(to_state)
                if to_idx > from_idx:
                    path = positive_path[from_idx : to_idx + 1]
                    return " → ".join(path)
        except ValueError:
            pass

        # 기본 제안
        suggestions = {
            ("무시", "충성"): "무시 → 의심 → 경외 → 충성",
            ("무시", "경외"): "무시 → 의심 → 경외",
            ("적대", "충성"): "적대 → 굴복 → 의심 → 경외 → 충성",
            ("중립", "충성"): "중립 → 의심 → 경외 → 충성",
            ("충성", "적대"): "충성 → 경외 → 의심 → 적대",
        }

        return suggestions.get((from_state, to_state), f"{from_state} → (중간 단계) → {to_state}")

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
            "사망",
            "추방",
            "희생",  # 최종 상태
            "배신",
            "적대",
            "굴복",  # 강한 감정
            "경외",
            "충성",  # 긍정적 강한 관계
            "무시",
            "의심",  # 부정적 약한 관계
            "중립",  # 기본
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
                    data = log_data.get("data", {})
                    if isinstance(data, dict):
                        npc_states = data.get("npc_relationships", {})
                        if npc_name in npc_states:
                            history.append({"ep_num": ep, "state": npc_states[npc_name]})
        except (KeyError, AttributeError, TypeError) as e:
            logging.warning(f"⚠️ [V64.P4-fix] NPC '{npc_name}' 이력 조회 실패 (ep ~{current_ep}): {e}")

        return history

    def record_transition(
        self, npc_name: str, from_state: str, to_state: str, arc: int, episode: int, trigger: str, justification: str
    ) -> dict[str, Any]:
        """
        관계 전이 기록 (사유 필수)

        Args:
            npc_name: NPC 이름
            from_state: 이전 상태
            to_state: 새 상태
            arc: Arc 번호
            episode: 에피소드 번호
            trigger: 전이 유발 사건 (필수)
            justification: 서사적 근거 (필수)

        Returns:
            {
                "valid": bool,
                "event": RelationshipEvent or None,
                "error": str or None
            }
        """
        # 사유 필수 체크
        if not isinstance(trigger, str):
            trigger = str(trigger) if trigger else ""
        if not isinstance(justification, str):
            justification = str(justification) if justification else ""
        if not trigger or len(trigger.strip()) < 5:
            return {
                "valid": False,
                "event": None,
                "error": f"[V49.7] trigger 누락: '{from_state}' → '{to_state}' 전이에 구체적 사건 필요",
            }

        if not justification or len(justification.strip()) < 10:
            return {
                "valid": False,
                "event": None,
                "error": f"[V49.7] justification 누락: '{from_state}' → '{to_state}' 전이에 서사적 근거 필요",
            }

        # 전이 가능 여부 검증
        validation = self.validate_transition(npc_name, from_state, to_state)
        if not validation.get("valid", True):
            return {"valid": False, "event": None, "error": validation.get("reason", "전이 불가")}

        # 이벤트 기록
        event = RelationshipEvent(
            arc=arc,
            episode=episode,
            npc_name=npc_name,
            from_state=from_state,
            to_state=to_state,
            trigger=trigger,
            justification=justification,
            is_valid=True,
        )

        self.host.transition_history.append(event)
        self.host.npc_states[npc_name] = to_state

        return {"valid": True, "event": event, "error": None}

    def validate_transition_with_justification(
        self, npc_name: str, from_state: str, to_state: str, trigger: str = "", justification: str = ""
    ) -> dict[str, Any]:
        """
        전이 유효성 + 사유 충분성 검증

        Returns:
            {
                "valid": bool,
                "severity": "CRITICAL" | "WARNING" | "OK",
                "message": str,
                "suggestion": str
            }
        """
        # 기본 전이 검증
        base_validation = self.validate_transition(npc_name, from_state, to_state)
        if not base_validation.get("valid", True):
            return {
                "valid": False,
                "severity": "CRITICAL",
                "message": base_validation.get("reason", "전이 불가"),
                "suggestion": base_validation.get("required", ""),
            }

        # 급격한 변화 감지 (2단계 이상 점프)
        state_order = ["적대", "무시", "의심", "중립", "경외", "충성"]
        try:
            from_idx = state_order.index(from_state) if from_state in state_order else -1
            to_idx = state_order.index(to_state) if to_state in state_order else -1

            if from_idx >= 0 and to_idx >= 0:
                jump = abs(to_idx - from_idx)
                if jump >= 2:
                    # 2단계 이상 점프는 강한 사유 필요
                    if not justification or len(justification) < 20:
                        req = self.TRANSITION_REQUIREMENTS.get((from_state, to_state), "충분한 서사적 근거 필요")
                        return {
                            "valid": False,
                            "severity": "CRITICAL",
                            "message": f"급격한 관계 변화: '{from_state}' → '{to_state}' ({jump}단계 점프)",
                            "suggestion": req,
                        }
        except ValueError:
            pass  # 특수 상태는 순서 계산 생략

        # 사유 충분성 체크
        if not trigger:
            return {
                "valid": False,
                "severity": "WARNING",
                "message": "trigger(전이 유발 사건) 누락",
                "suggestion": "어떤 사건이 관계 변화를 유발했는지 명시하세요",
            }

        return {"valid": True, "severity": "OK", "message": "전이 유효", "suggestion": ""}

    def get_npc_current_state(self, npc_name: str) -> str:
        """NPC의 현재 관계 상태 조회"""
        return self.host.npc_states.get(npc_name, "알 수 없음")

    def get_transition_history(self, npc_name: str = None) -> list[dict]:
        """
        전이 이력 조회

        Args:
            npc_name: 특정 NPC만 조회 (None이면 전체)

        Returns:
            전이 이벤트 목록
        """
        events = self.host.transition_history
        if npc_name:
            events = [e for e in events if e.npc_name == npc_name]

        return [
            {
                "arc": e.arc,
                "episode": e.episode,
                "npc": e.npc_name,
                "from": e.from_state,
                "to": e.to_state,
                "trigger": e.trigger,
                "justification": e.justification,
            }
            for e in events
        ]

    def generate_transition_prompt(self, from_state: str, to_state: str) -> str:
        """
        ??? ??? ???? ??? ??

        Args:
            from_state: ?? ??
            to_state: ?? ??

        Returns:
            ???? ??? ???
        """
        req = self.TRANSITION_REQUIREMENTS.get((from_state, to_state), None)

        if req:
            return f"""
[?? ?? ????]
'{from_state}' ? '{to_state}' ?? ??: {req}

??? ??? ?????:
1. trigger: ??? ??? ??? ?? (?: "??? ??", "??? ???")
2. justification: ? ? ??? ?????? ??? ?? (?? 20?)
"""
        return ""
