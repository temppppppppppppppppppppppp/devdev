"""
[Phase 2.1] Relationship State Machine
NPC-주인공 관계의 상태 전환 추적 및 검증

[V49.7] 전이 사유 필수화 - 관계 변화 시 trigger/justification 강제
[V59] 집단/세력 관계 및 파벌 역학 추가
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import re


@dataclass
class RelationshipEvent:
    """[V49.7] 관계 전이 이벤트 기록"""
    arc: int
    episode: int
    npc_name: str
    from_state: str
    to_state: str
    trigger: str  # 전이를 유발한 사건
    justification: str  # 서사적 근거
    is_valid: bool = True


@dataclass
class FactionRelationshipEvent:
    """[V59] 세력 간 관계 전이 이벤트 기록"""
    arc: int
    episode: int
    faction_a: str  # 세력 A
    faction_b: str  # 세력 B
    from_state: str
    to_state: str
    trigger: str  # 전이 유발 사건
    justification: str  # 서사적 근거
    power_shift: float = 0.0  # 파워 밸런스 변화 (-1.0 ~ 1.0)
    is_valid: bool = True


@dataclass
class FactionInfo:
    """[V59] 세력 정보"""
    name: str
    power_level: float = 50.0  # 0-100 스케일
    members: List[str] = field(default_factory=list)
    territory: List[str] = field(default_factory=list)
    allies: List[str] = field(default_factory=list)
    enemies: List[str] = field(default_factory=list)
    stance: str = "중립"  # 주인공에 대한 기본 태도


class RelationshipTracker:
    """NPC-주인공 관계의 상태 전환 추적 (유한 상태 머신)"""

    # [V55.5] 관계 상태 정의 (State Machine) - 강화된 규칙
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
        "희생": {"can_transition_to": []}   # 최종 상태
    }

    # [V55.5] 위험한 전환 (허용은 되지만 강한 정당화 필요)
    RISKY_TRANSITIONS = {
        ("무시", "의심"): "주인공의 실력 또는 정체 의심이 시작되어야 함",
        ("의심", "경외"): "압도적 무력 시현 또는 지위 확인 필요",
        ("경외", "충성"): "지속적 존경 + 결정적 은혜/구명 필요",
        ("적대", "의심"): "적대 감정을 누그러뜨릴 사건 필요",
        ("굴복", "충성"): "용서 + 새로운 기회 부여 필요",
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

    # [V49.7] 전이에 필요한 최소 justification 예시
    # [V55.5] 강화: 더 엄격한 규칙 + 불가능한 전환 명시
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

    # ═══════════════════════════════════════════════════════════════
    # [V59] 세력/파벌 관계 상수 정의
    # ═══════════════════════════════════════════════════════════════

    # [V59] 세력 간 관계 상태 (Faction State Machine)
    FACTION_STATES = {
        "동맹": {"can_transition_to": ["우호", "중립", "와해"]},  # 긴밀한 협력 관계
        "우호": {"can_transition_to": ["동맹", "중립", "경계"]},  # 긍정적 관계
        "중립": {"can_transition_to": ["우호", "경계", "무관심"]},  # 중립 상태
        "무관심": {"can_transition_to": ["중립", "경계"]},  # 서로 인식 없음
        "경계": {"can_transition_to": ["우호", "중립", "적대"]},  # 긴장 상태
        "적대": {"can_transition_to": ["경계", "전쟁", "굴복"]},  # 적대 관계
        "전쟁": {"can_transition_to": ["적대", "굴복", "멸망"]},  # 무력 충돌
        "굴복": {"can_transition_to": ["예속", "와해", "경계"]},  # 패배 후 굴복
        "예속": {"can_transition_to": ["굴복", "반란", "흡수"]},  # 종속 관계
        "반란": {"can_transition_to": ["전쟁", "와해", "독립"]},  # 반란 상태
        "독립": {"can_transition_to": ["중립", "경계", "우호"]},  # 독립 획득
        "와해": {"can_transition_to": []},  # 최종 상태: 세력 해체
        "멸망": {"can_transition_to": []},  # 최종 상태: 세력 소멸
        "흡수": {"can_transition_to": []}   # 최종 상태: 다른 세력에 흡수
    }

    # [V59] 세력 관계 전환 요구사항
    FACTION_TRANSITION_REQUIREMENTS = {
        # 긍정적 관계 발전
        ("중립", "우호"): "공통의 적 대응 또는 상호 이익 합의 필요",
        ("우호", "동맹"): "정식 동맹 선언 또는 대규모 협력 사업 필요",
        ("경계", "우호"): "오해 해소 + 신뢰 구축 사건 필요",

        # 부정적 관계 발전
        ("경계", "적대"): "직접적 충돌 또는 이권 다툼 필요",
        ("적대", "전쟁"): "대규모 무력 충돌 발생 필요",
        ("전쟁", "굴복"): "결정적 패배 또는 지도자 사망/포획",
        ("굴복", "예속"): "항복 조건 수락 및 종속 조약 체결",

        # 급격한 변화 (강한 정당화 필요)
        ("동맹", "적대"): "불가능 - 우호→경계 단계 거쳐야 함",
        ("예속", "독립"): "내부 혼란 + 외부 지원 또는 반란 성공 필요",
        ("반란", "독립"): "반란 성공 + 독립 선언 + 국제 인정 필요",
    }

    # [V59] 세력 관계 감지 키워드
    FACTION_STATE_KEYWORDS = {
        "동맹": ["동맹", "연합", "협약", "맹주", "함께 싸우"],
        "우호": ["우호", "친선", "협력", "거래", "교류"],
        "중립": ["중립", "관망", "불간섭", "독자 노선"],
        "무관심": ["무관", "신경 쓰지", "알 바 아니"],
        "경계": ["경계", "견제", "감시", "긴장", "불신"],
        "적대": ["적대", "원수", "앙숙", "철천지원수"],
        "전쟁": ["전쟁", "침공", "정벌", "토벌", "진군"],
        "굴복": ["굴복", "항복", "무릎 꿇", "백기"],
        "예속": ["예속", "속국", "조공", "복종"],
        "반란": ["반란", "봉기", "반기", "거병"],
        "와해": ["와해", "해체", "분열", "붕괴"],
        "멸망": ["멸망", "전멸", "소멸", "궤멸"],
        "흡수": ["흡수", "합병", "편입", "통합"]
    }

    # [V59] 장르별 파벌 역학 패턴
    GENRE_FACTION_PATTERNS = {
        "wuxia": {
            "power_sources": ["무력", "문파 규모", "비급/보물", "강호 평판", "역사"],
            "typical_factions": ["무림맹", "사파", "마교", "문파", "가문", "방파"],
            "alliance_triggers": ["공동의 적", "혼인 동맹", "의형제", "사제 관계"],
            "conflict_triggers": ["영역 다툼", "보물 쟁탈", "복수", "명예 훼손", "이념 충돌"]
        },
        "hunter": {
            "power_sources": ["헌터 수", "고레벨 헌터", "던전 권리", "자금력", "기술력"],
            "typical_factions": ["대형 길드", "중소 길드", "헌터 협회", "정부 기관", "재벌"],
            "alliance_triggers": ["레이드 협력", "독점 계약", "인수합병", "공동 방어"],
            "conflict_triggers": ["던전 권리", "스카우트 전쟁", "영역 다툼", "배신", "이권 충돌"]
        },
        "investment": {
            "power_sources": ["자본", "정보력", "인맥", "기술력", "시장 점유율"],
            "typical_factions": ["대기업", "펀드", "은행", "벤처", "재벌가", "국가 기관"],
            "alliance_triggers": ["합작 투자", "M&A", "전략적 제휴", "컨소시엄"],
            "conflict_triggers": ["시장 쟁탈", "적대적 M&A", "특허 분쟁", "내부자 거래 폭로"]
        }
    }

    def __init__(self) -> None:
        """[V49.7] 초기화, [V59] 파벌 추적 추가"""
        self.npc_states: Dict[str, str] = {}  # {npc_name: current_state}
        self.transition_history: List[RelationshipEvent] = []

        # [V59] 세력/파벌 관계 추적
        self.factions: Dict[str, FactionInfo] = {}  # {faction_name: FactionInfo}
        self.faction_relations: Dict[Tuple[str, str], str] = {}  # {(faction_a, faction_b): state}
        self.faction_transition_history: List[FactionRelationshipEvent] = []
        self.protagonist_faction: Optional[str] = None  # 주인공 소속 세력

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
                "risky": False
            }

        # [V55.5] 위험한 전환 체크
        transition_key = (old_state, new_state)
        if transition_key in self.RISKY_TRANSITIONS:
            return {
                "valid": True,
                "risky": True,
                "risk_warning": self.RISKY_TRANSITIONS[transition_key],
                "reason": f"위험한 전환: '{old_state}' → '{new_state}'는 강한 정당화 필요"
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
                    path = positive_path[from_idx:to_idx + 1]
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

    # ═══════════════════════════════════════════════════════════════
    # [V49.7] 전이 사유 필수화 메서드
    # ═══════════════════════════════════════════════════════════════

    def record_transition(
        self,
        npc_name: str,
        from_state: str,
        to_state: str,
        arc: int,
        episode: int,
        trigger: str,
        justification: str
    ) -> Dict[str, Any]:
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
        if not trigger or len(trigger.strip()) < 5:
            return {
                "valid": False,
                "event": None,
                "error": f"[V49.7] trigger 누락: '{from_state}' → '{to_state}' 전이에 구체적 사건 필요"
            }

        if not justification or len(justification.strip()) < 10:
            return {
                "valid": False,
                "event": None,
                "error": f"[V49.7] justification 누락: '{from_state}' → '{to_state}' 전이에 서사적 근거 필요"
            }

        # 전이 가능 여부 검증
        validation = self.validate_transition(npc_name, from_state, to_state)
        if not validation.get("valid", True):
            return {
                "valid": False,
                "event": None,
                "error": validation.get("reason", "전이 불가")
            }

        # 이벤트 기록
        event = RelationshipEvent(
            arc=arc,
            episode=episode,
            npc_name=npc_name,
            from_state=from_state,
            to_state=to_state,
            trigger=trigger,
            justification=justification,
            is_valid=True
        )

        self.transition_history.append(event)
        self.npc_states[npc_name] = to_state

        return {
            "valid": True,
            "event": event,
            "error": None
        }

    def validate_transition_with_justification(
        self,
        npc_name: str,
        from_state: str,
        to_state: str,
        trigger: str = "",
        justification: str = ""
    ) -> Dict[str, Any]:
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
                "suggestion": base_validation.get("required", "")
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
                        req = self.TRANSITION_REQUIREMENTS.get(
                            (from_state, to_state),
                            "충분한 서사적 근거 필요"
                        )
                        return {
                            "valid": False,
                            "severity": "CRITICAL",
                            "message": f"급격한 관계 변화: '{from_state}' → '{to_state}' ({jump}단계 점프)",
                            "suggestion": req
                        }
        except ValueError:
            pass  # 특수 상태는 순서 계산 생략

        # 사유 충분성 체크
        if not trigger:
            return {
                "valid": False,
                "severity": "WARNING",
                "message": "trigger(전이 유발 사건) 누락",
                "suggestion": "어떤 사건이 관계 변화를 유발했는지 명시하세요"
            }

        return {
            "valid": True,
            "severity": "OK",
            "message": "전이 유효",
            "suggestion": ""
        }

    def get_npc_current_state(self, npc_name: str) -> str:
        """NPC의 현재 관계 상태 조회"""
        return self.npc_states.get(npc_name, "알 수 없음")

    def get_transition_history(self, npc_name: str = None) -> List[Dict]:
        """
        전이 이력 조회

        Args:
            npc_name: 특정 NPC만 조회 (None이면 전체)

        Returns:
            전이 이벤트 목록
        """
        events = self.transition_history
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
                "justification": e.justification
            }
            for e in events
        ]

    def generate_transition_prompt(self, from_state: str, to_state: str) -> str:
        """
        전이에 필요한 프롬프트 가이드 생성

        Args:
            from_state: 이전 상태
            to_state: 목표 상태

        Returns:
            프롬프트 가이드 텍스트
        """
        req = self.TRANSITION_REQUIREMENTS.get(
            (from_state, to_state),
            None
        )

        if req:
            return f"""
[관계 변화 요구사항]
'{from_state}' → '{to_state}' 전이 조건: {req}

반드시 아래를 포함하세요:
1. trigger: 전이를 유발한 구체적 사건 (예: "고깃국 지급", "목숨을 구해줌")
2. justification: 왜 이 변화가 자연스러운지 서사적 근거 (최소 20자)
"""
        return ""

    # ═══════════════════════════════════════════════════════════════
    # [V59] 세력/파벌 관계 관리 메서드
    # ═══════════════════════════════════════════════════════════════

    def register_faction_v59(
        self,
        name: str,
        power_level: float = 50.0,
        members: List[str] = None,
        territory: List[str] = None,
        stance: str = "중립"
    ) -> FactionInfo:
        """
        [V59] 새로운 세력 등록

        Args:
            name: 세력 이름
            power_level: 파워 레벨 (0-100)
            members: 주요 구성원 목록
            territory: 영역/거점 목록
            stance: 주인공에 대한 기본 태도

        Returns:
            등록된 FactionInfo
        """
        faction = FactionInfo(
            name=name,
            power_level=max(0, min(100, power_level)),
            members=members or [],
            territory=territory or [],
            stance=stance
        )
        self.factions[name] = faction
        return faction

    def set_faction_relation_v59(
        self,
        faction_a: str,
        faction_b: str,
        state: str
    ) -> bool:
        """
        [V59] 두 세력 간 관계 설정

        Args:
            faction_a: 세력 A 이름
            faction_b: 세력 B 이름
            state: 관계 상태

        Returns:
            성공 여부
        """
        if state not in self.FACTION_STATES:
            return False

        # 양방향 관계 설정 (대칭)
        key1 = (faction_a, faction_b)
        key2 = (faction_b, faction_a)
        self.faction_relations[key1] = state
        self.faction_relations[key2] = state

        # 동맹/적대 관계 시 allies/enemies 업데이트
        if faction_a in self.factions and faction_b in self.factions:
            fa = self.factions[faction_a]
            fb = self.factions[faction_b]

            if state == "동맹":
                if faction_b not in fa.allies:
                    fa.allies.append(faction_b)
                if faction_a not in fb.allies:
                    fb.allies.append(faction_a)
                # 적 목록에서 제거
                if faction_b in fa.enemies:
                    fa.enemies.remove(faction_b)
                if faction_a in fb.enemies:
                    fb.enemies.remove(faction_a)

            elif state in ["적대", "전쟁"]:
                if faction_b not in fa.enemies:
                    fa.enemies.append(faction_b)
                if faction_a not in fb.enemies:
                    fb.enemies.append(faction_a)
                # 동맹 목록에서 제거
                if faction_b in fa.allies:
                    fa.allies.remove(faction_b)
                if faction_a in fb.allies:
                    fb.allies.remove(faction_a)

        return True

    def validate_faction_transition_v59(
        self,
        faction_a: str,
        faction_b: str,
        old_state: str,
        new_state: str
    ) -> Dict[str, Any]:
        """
        [V59] 세력 간 관계 전환 가능 여부 검증

        Args:
            faction_a: 세력 A 이름
            faction_b: 세력 B 이름
            old_state: 이전 관계 상태
            new_state: 새로운 관계 상태

        Returns:
            {
                "valid": bool,
                "reason": str,
                "allowed_transitions": list,
                "required": str,
                "suggested_path": str
            }
        """
        # 알 수 없는 상태는 통과
        if old_state == "알 수 없음" or new_state == "알 수 없음":
            return {"valid": True}

        # 상태가 변하지 않으면 항상 통과
        if old_state == new_state:
            return {"valid": True}

        # 상태 존재 여부 확인
        if old_state not in self.FACTION_STATES:
            return {
                "valid": False,
                "reason": f"알 수 없는 세력 관계 상태: '{old_state}'"
            }

        if new_state not in self.FACTION_STATES:
            return {
                "valid": False,
                "reason": f"알 수 없는 세력 관계 상태: '{new_state}'"
            }

        # 허용된 전환인지 확인
        allowed = self.FACTION_STATES.get(old_state, {}).get("can_transition_to", [])

        if new_state not in allowed:
            suggested = self._suggest_faction_transition_path(old_state, new_state)
            return {
                "valid": False,
                "reason": f"'{faction_a}'-'{faction_b}' 관계: '{old_state}' → '{new_state}' 전환 불가능",
                "allowed_transitions": allowed,
                "required": f"'{old_state}'에서 '{new_state}'로 가려면 중간 단계 필요",
                "suggested_path": suggested
            }

        # 전환 요구사항 확인
        req_key = (old_state, new_state)
        requirement = self.FACTION_TRANSITION_REQUIREMENTS.get(req_key)

        return {
            "valid": True,
            "allowed_transitions": allowed,
            "requirement": requirement
        }

    def _suggest_faction_transition_path(self, from_state: str, to_state: str) -> str:
        """
        [V59] 불가능한 세력 관계 전환에 대해 권장 경로 제안
        """
        # 일반적인 관계 발전 경로
        positive_path = ["무관심", "중립", "우호", "동맹"]
        negative_path = ["중립", "경계", "적대", "전쟁"]
        submission_path = ["전쟁", "굴복", "예속"]
        liberation_path = ["예속", "반란", "독립"]

        paths = {
            ("동맹", "적대"): "동맹 → 우호 → 중립 → 경계 → 적대",
            ("동맹", "전쟁"): "동맹 → 우호 → 중립 → 경계 → 적대 → 전쟁",
            ("무관심", "동맹"): "무관심 → 중립 → 우호 → 동맹",
            ("적대", "동맹"): "적대 → 경계 → 중립 → 우호 → 동맹",
            ("예속", "동맹"): "예속 → 반란 → 독립 → 중립 → 우호 → 동맹",
            ("전쟁", "동맹"): "전쟁 → 적대 → 경계 → 중립 → 우호 → 동맹",
        }

        return paths.get((from_state, to_state), f"{from_state} → (중간 단계) → {to_state}")

    def record_faction_transition_v59(
        self,
        faction_a: str,
        faction_b: str,
        from_state: str,
        to_state: str,
        arc: int,
        episode: int,
        trigger: str,
        justification: str,
        power_shift: float = 0.0
    ) -> Dict[str, Any]:
        """
        [V59] 세력 관계 전이 기록

        Args:
            faction_a: 세력 A
            faction_b: 세력 B
            from_state: 이전 상태
            to_state: 새 상태
            arc: Arc 번호
            episode: 에피소드 번호
            trigger: 전이 유발 사건
            justification: 서사적 근거
            power_shift: 파워 밸런스 변화 (양수: A 유리, 음수: B 유리)

        Returns:
            {
                "valid": bool,
                "event": FactionRelationshipEvent or None,
                "error": str or None
            }
        """
        # 사유 필수 체크
        if not trigger or len(trigger.strip()) < 5:
            return {
                "valid": False,
                "event": None,
                "error": f"[V59] trigger 누락: '{from_state}' → '{to_state}' 전이에 구체적 사건 필요"
            }

        if not justification or len(justification.strip()) < 10:
            return {
                "valid": False,
                "event": None,
                "error": f"[V59] justification 누락: '{from_state}' → '{to_state}' 전이에 서사적 근거 필요"
            }

        # 전이 가능 여부 검증
        validation = self.validate_faction_transition_v59(
            faction_a, faction_b, from_state, to_state
        )
        if not validation.get("valid", True):
            return {
                "valid": False,
                "event": None,
                "error": validation.get("reason", "전이 불가")
            }

        # 이벤트 기록
        event = FactionRelationshipEvent(
            arc=arc,
            episode=episode,
            faction_a=faction_a,
            faction_b=faction_b,
            from_state=from_state,
            to_state=to_state,
            trigger=trigger,
            justification=justification,
            power_shift=max(-1.0, min(1.0, power_shift)),
            is_valid=True
        )

        self.faction_transition_history.append(event)
        self.set_faction_relation_v59(faction_a, faction_b, to_state)

        # 파워 밸런스 업데이트
        if power_shift != 0 and faction_a in self.factions and faction_b in self.factions:
            shift_amount = power_shift * 10  # 최대 ±10 포인트
            self.factions[faction_a].power_level = max(0, min(100,
                self.factions[faction_a].power_level + shift_amount))
            self.factions[faction_b].power_level = max(0, min(100,
                self.factions[faction_b].power_level - shift_amount))

        return {
            "valid": True,
            "event": event,
            "error": None
        }

    def get_faction_relation_v59(self, faction_a: str, faction_b: str) -> str:
        """
        [V59] 두 세력 간 현재 관계 조회

        Returns:
            관계 상태 문자열 (없으면 "알 수 없음")
        """
        key1 = (faction_a, faction_b)
        key2 = (faction_b, faction_a)
        return self.faction_relations.get(key1, self.faction_relations.get(key2, "알 수 없음"))

    def infer_faction_state_from_manuscript_v59(
        self,
        faction_a: str,
        faction_b: str,
        manuscript: str
    ) -> str:
        """
        [V59] 원고에서 세력 간 관계 상태 추론

        Args:
            faction_a: 세력 A 이름
            faction_b: 세력 B 이름
            manuscript: 원고 텍스트

        Returns:
            추론된 관계 상태
        """
        # 두 세력 모두 언급되지 않으면 알 수 없음
        if faction_a not in manuscript or faction_b not in manuscript:
            return "알 수 없음"

        # 두 세력이 함께 언급된 문맥 추출
        contexts = []
        for match in re.finditer(f"({re.escape(faction_a)}|{re.escape(faction_b)})", manuscript):  # [V70] regex 메타문자 방어
            start = max(0, match.start() - 300)
            end = min(len(manuscript), match.end() + 300)
            context = manuscript[start:end]
            # 다른 세력도 포함된 경우만
            if faction_a in context and faction_b in context:
                contexts.append(context)

        if not contexts:
            return "알 수 없음"

        combined_context = " ".join(contexts)

        # 우선순위 순서대로 키워드 매칭
        priority_order = [
            "멸망", "와해", "흡수",  # 최종 상태
            "전쟁", "반란",  # 극단적 충돌
            "동맹", "예속",  # 강한 관계
            "적대", "굴복",  # 부정적 관계
            "우호", "독립",  # 긍정적 관계
            "경계", "무관심",  # 약한 관계
            "중립"  # 기본
        ]

        for state in priority_order:
            keywords = self.FACTION_STATE_KEYWORDS.get(state, [])
            if any(kw in combined_context for kw in keywords):
                return state

        return "중립"

    def track_faction_dynamics_v59(
        self,
        manuscripts: List[str],
        genre: str = "wuxia"
    ) -> Dict[str, Any]:
        """
        [V59] 파벌 역학 추적 - 복수의 원고에서 세력 간 역학 분석

        Args:
            manuscripts: 원고 목록 (시간순)
            genre: 장르

        Returns:
            {
                "power_rankings": [{faction, power, trend}],
                "alliance_network": {faction: [allies]},
                "conflict_zones": [{faction_a, faction_b, tension_level}],
                "rising_factions": [factions gaining power],
                "declining_factions": [factions losing power],
                "predictions": [predicted events]
            }
        """
        genre_patterns = self.GENRE_FACTION_PATTERNS.get(genre, self.GENRE_FACTION_PATTERNS["wuxia"])

        # 원고별 세력 언급 빈도 추적
        faction_mentions: Dict[str, List[int]] = {}  # {faction: [count_per_episode]}
        for faction_name in self.factions:
            faction_mentions[faction_name] = []

        for manuscript in manuscripts:
            for faction_name in self.factions:
                count = manuscript.count(faction_name)
                faction_mentions[faction_name].append(count)

        # 파워 트렌드 계산
        power_rankings = []
        rising_factions = []
        declining_factions = []

        for faction_name, mentions in faction_mentions.items():
            if not mentions:
                continue

            faction = self.factions.get(faction_name)
            if not faction:
                continue

            # 최근 5화 vs 이전 평균 비교
            recent = mentions[-5:] if len(mentions) >= 5 else mentions
            earlier = mentions[:-5] if len(mentions) > 5 else []

            recent_avg = sum(recent) / len(recent) if recent else 0
            earlier_avg = sum(earlier) / len(earlier) if earlier else recent_avg

            if earlier_avg > 0:
                trend = (recent_avg - earlier_avg) / earlier_avg
            else:
                trend = 0.0

            power_rankings.append({
                "faction": faction_name,
                "power": faction.power_level,
                "trend": round(trend, 2),
                "trend_label": "상승" if trend > 0.2 else ("하락" if trend < -0.2 else "유지")
            })

            if trend > 0.3:
                rising_factions.append(faction_name)
            elif trend < -0.3:
                declining_factions.append(faction_name)

        # 파워 순으로 정렬
        power_rankings.sort(key=lambda x: x["power"], reverse=True)

        # 동맹 네트워크 구축
        alliance_network = {}
        for faction_name, faction in self.factions.items():
            alliance_network[faction_name] = faction.allies.copy()

        # 갈등 지대 식별
        conflict_zones = []
        for (fa, fb), state in self.faction_relations.items():
            if state in ["경계", "적대", "전쟁"]:
                tension_level = {"경계": 3, "적대": 7, "전쟁": 10}.get(state, 5)
                # 중복 방지
                if not any(cz["faction_a"] == fb and cz["faction_b"] == fa for cz in conflict_zones):
                    conflict_zones.append({
                        "faction_a": fa,
                        "faction_b": fb,
                        "state": state,
                        "tension_level": tension_level
                    })

        # 예측 생성
        predictions = []

        # 급상승 세력 + 높은 긴장도 = 전쟁 가능성
        for cz in conflict_zones:
            if cz["tension_level"] >= 7:
                for rising in rising_factions:
                    if rising in [cz["faction_a"], cz["faction_b"]]:
                        predictions.append({
                            "type": "war_escalation",
                            "factions": [cz["faction_a"], cz["faction_b"]],
                            "probability": "high",
                            "description": f"{rising}의 세력 확장으로 {cz['faction_a']}-{cz['faction_b']} 간 전쟁 가능성"
                        })

        # 급하락 세력 = 흡수/와해 가능성
        for declining in declining_factions:
            if self.factions.get(declining, FactionInfo(declining)).power_level < 30:
                predictions.append({
                    "type": "faction_collapse",
                    "faction": declining,
                    "probability": "medium",
                    "description": f"{declining} 세력 약화로 와해 또는 흡수 가능성"
                })

        return {
            "power_rankings": power_rankings,
            "alliance_network": alliance_network,
            "conflict_zones": conflict_zones,
            "rising_factions": rising_factions,
            "declining_factions": declining_factions,
            "predictions": predictions,
            "genre_context": genre_patterns
        }

    def get_faction_power_balance_v59(self) -> Dict[str, Any]:
        """
        [V59] 현재 세력 간 파워 밸런스 분석

        Returns:
            {
                "dominant_faction": str,
                "power_distribution": {faction: power_percentage},
                "balance_type": "monopoly" | "bipolar" | "multipolar" | "fragmented",
                "stability_score": float (0-100)
            }
        """
        if not self.factions:
            return {
                "dominant_faction": None,
                "power_distribution": {},
                "balance_type": "fragmented",
                "stability_score": 50.0
            }

        # 파워 분포 계산
        total_power = sum(f.power_level for f in self.factions.values())
        if total_power == 0:
            total_power = 1  # 0으로 나누기 방지

        power_distribution = {
            name: round((f.power_level / total_power) * 100, 1)
            for name, f in self.factions.items()
        }

        # 최강 세력 찾기
        sorted_factions = sorted(
            self.factions.items(),
            key=lambda x: x[1].power_level,
            reverse=True
        )
        dominant = sorted_factions[0][0] if sorted_factions else None
        dominant_share = power_distribution.get(dominant, 0)

        # 밸런스 타입 결정
        if dominant_share >= 60:
            balance_type = "monopoly"  # 일극 체제
            stability_score = 80.0  # 안정적이지만 억압적
        elif len([p for p in power_distribution.values() if p >= 30]) >= 2:
            balance_type = "bipolar"  # 양극 체제
            stability_score = 50.0  # 긴장 상태
        elif len([p for p in power_distribution.values() if p >= 15]) >= 3:
            balance_type = "multipolar"  # 다극 체제
            stability_score = 60.0  # 동맹으로 균형
        else:
            balance_type = "fragmented"  # 분열 상태
            stability_score = 30.0  # 불안정

        # 전쟁 상태가 있으면 안정성 감소
        war_count = sum(1 for state in self.faction_relations.values() if state == "전쟁")
        stability_score = max(0, stability_score - (war_count * 15))

        return {
            "dominant_faction": dominant,
            "power_distribution": power_distribution,
            "balance_type": balance_type,
            "stability_score": round(stability_score, 1)
        }

    def generate_faction_dynamics_prompt_v59(
        self,
        genre: str = "wuxia"
    ) -> str:
        """
        [V59] 파벌 역학 정보를 프롬프트에 주입할 형태로 생성

        Args:
            genre: 장르

        Returns:
            프롬프트 텍스트
        """
        if not self.factions:
            return ""

        power_balance = self.get_faction_power_balance_v59()

        lines = [
            "\n[세력 역학 현황]",
            f"체제 유형: {power_balance['balance_type']}",
            f"안정성: {power_balance['stability_score']}점",
            ""
        ]

        # 세력 목록
        lines.append("【등록된 세력】")
        for name, faction in sorted(self.factions.items(), key=lambda x: -x[1].power_level):
            allies_str = ", ".join(faction.allies[:3]) if faction.allies else "없음"
            enemies_str = ", ".join(faction.enemies[:3]) if faction.enemies else "없음"
            lines.append(f"- {name}: 파워 {faction.power_level:.0f}, 태도 '{faction.stance}'")
            lines.append(f"  동맹: {allies_str} | 적대: {enemies_str}")

        # 현재 갈등 상황
        conflicts = [(k, v) for k, v in self.faction_relations.items() if v in ["경계", "적대", "전쟁"]]
        if conflicts:
            lines.append("")
            lines.append("【긴장/충돌 상황】")
            seen = set()
            for (fa, fb), state in conflicts:
                key = tuple(sorted([fa, fb]))
                if key not in seen:
                    seen.add(key)
                    lines.append(f"- {fa} vs {fb}: {state}")

        # 장르별 가이드
        genre_patterns = self.GENRE_FACTION_PATTERNS.get(genre, {})
        if genre_patterns:
            lines.append("")
            lines.append(f"【{genre} 장르 파벌 가이드】")
            lines.append(f"파워 원천: {', '.join(genre_patterns.get('power_sources', [])[:3])}")
            lines.append(f"동맹 계기: {', '.join(genre_patterns.get('alliance_triggers', [])[:2])}")
            lines.append(f"충돌 원인: {', '.join(genre_patterns.get('conflict_triggers', [])[:2])}")

        return "\n".join(lines)

    def get_faction_transition_history_v59(
        self,
        faction_name: str = None
    ) -> List[Dict]:
        """
        [V59] 세력 관계 전이 이력 조회

        Args:
            faction_name: 특정 세력만 조회 (None이면 전체)

        Returns:
            전이 이벤트 목록
        """
        events = self.faction_transition_history
        if faction_name:
            events = [e for e in events if e.faction_a == faction_name or e.faction_b == faction_name]

        return [
            {
                "arc": e.arc,
                "episode": e.episode,
                "faction_a": e.faction_a,
                "faction_b": e.faction_b,
                "from": e.from_state,
                "to": e.to_state,
                "trigger": e.trigger,
                "justification": e.justification,
                "power_shift": e.power_shift
            }
            for e in events
        ]

    def analyze_protagonist_faction_position_v59(self) -> Dict[str, Any]:
        """
        [V59] 주인공 소속 세력의 위치 분석

        Returns:
            {
                "faction": str,
                "power_rank": int,
                "allies_count": int,
                "enemies_count": int,
                "threat_level": "low" | "medium" | "high" | "critical",
                "opportunities": [str],
                "threats": [str]
            }
        """
        if not self.protagonist_faction or self.protagonist_faction not in self.factions:
            return {
                "faction": None,
                "power_rank": 0,
                "threat_level": "unknown",
                "opportunities": [],
                "threats": []
            }

        pf = self.factions[self.protagonist_faction]
        power_balance = self.get_faction_power_balance_v59()

        # 파워 순위 계산
        sorted_power = sorted(self.factions.values(), key=lambda x: x.power_level, reverse=True)
        power_rank = next((i + 1 for i, f in enumerate(sorted_power) if f.name == self.protagonist_faction), 0)

        # 위협 수준 평가
        enemies_power = sum(
            self.factions.get(e, FactionInfo(e)).power_level
            for e in pf.enemies if e in self.factions
        )
        allies_power = sum(
            self.factions.get(a, FactionInfo(a)).power_level
            for a in pf.allies if a in self.factions
        )

        combined_power = pf.power_level + allies_power

        if enemies_power > combined_power * 2:
            threat_level = "critical"
        elif enemies_power > combined_power * 1.5:
            threat_level = "high"
        elif enemies_power > combined_power:
            threat_level = "medium"
        else:
            threat_level = "low"

        # 기회와 위협 식별
        opportunities = []
        threats = []

        # 약한 적 = 기회
        for enemy in pf.enemies:
            if enemy in self.factions:
                if self.factions[enemy].power_level < pf.power_level * 0.7:
                    opportunities.append(f"{enemy} 세력 약화로 정벌/흡수 기회")

        # 강한 적 = 위협
        for enemy in pf.enemies:
            if enemy in self.factions:
                if self.factions[enemy].power_level > pf.power_level * 1.5:
                    threats.append(f"{enemy} 세력의 압도적 우위")

        # 고립 = 위협
        if not pf.allies and len(pf.enemies) >= 2:
            threats.append("동맹 없이 다수의 적대 세력에 포위")

        # 잠재적 동맹 = 기회
        for faction_name, faction in self.factions.items():
            if faction_name == self.protagonist_faction:
                continue
            relation = self.get_faction_relation_v59(self.protagonist_faction, faction_name)
            if relation in ["중립", "우호"]:
                # 공통의 적이 있으면 동맹 기회
                common_enemies = set(pf.enemies) & set(faction.enemies)
                if common_enemies:
                    opportunities.append(f"{faction_name}과 공동의 적({', '.join(common_enemies)}) 대응 동맹 가능")

        return {
            "faction": self.protagonist_faction,
            "power_rank": power_rank,
            "total_factions": len(self.factions),
            "allies_count": len(pf.allies),
            "enemies_count": len(pf.enemies),
            "threat_level": threat_level,
            "opportunities": opportunities[:3],  # 최대 3개
            "threats": threats[:3]  # 최대 3개
        }

    def generate_faction_report_v59(self, genre: str = "wuxia") -> str:
        """
        [V59] 전체 세력 역학 리포트 생성

        Returns:
            사람이 읽기 좋은 형태의 리포트 문자열
        """
        lines = [
            "═" * 50,
            "         [V59] 세력 역학 분석 리포트",
            "═" * 50,
            ""
        ]

        # 파워 밸런스
        balance = self.get_faction_power_balance_v59()
        lines.append(f"【체제 분석】")
        lines.append(f"  유형: {balance['balance_type']}")
        lines.append(f"  지배 세력: {balance['dominant_faction'] or '없음'}")
        lines.append(f"  안정성: {balance['stability_score']:.0f}점")
        lines.append("")

        # 파워 분포
        lines.append("【세력 파워 분포】")
        for name, share in sorted(balance['power_distribution'].items(), key=lambda x: -x[1]):
            bar_len = int(share / 5)  # 20칸 스케일
            bar = "█" * bar_len + "░" * (20 - bar_len)
            lines.append(f"  {name:12s} [{bar}] {share:5.1f}%")
        lines.append("")

        # 세력 관계 매트릭스 (간략)
        if len(self.factions) <= 6:
            lines.append("【세력 관계】")
            for fa in self.factions:
                relations = []
                for fb in self.factions:
                    if fa != fb:
                        rel = self.get_faction_relation_v59(fa, fb)
                        if rel not in ["알 수 없음", "중립", "무관심"]:
                            relations.append(f"{fb}({rel})")
                if relations:
                    lines.append(f"  {fa}: {', '.join(relations)}")
            lines.append("")

        # 주인공 세력 분석
        if self.protagonist_faction:
            pf_analysis = self.analyze_protagonist_faction_position_v59()
            lines.append(f"【주인공 세력 '{self.protagonist_faction}' 분석】")
            lines.append(f"  파워 순위: {pf_analysis['power_rank']}/{pf_analysis['total_factions']}")
            lines.append(f"  위협 수준: {pf_analysis['threat_level']}")
            lines.append(f"  동맹: {pf_analysis['allies_count']}개 | 적대: {pf_analysis['enemies_count']}개")

            if pf_analysis['opportunities']:
                lines.append("  기회:")
                for opp in pf_analysis['opportunities']:
                    lines.append(f"    ✓ {opp}")

            if pf_analysis['threats']:
                lines.append("  위협:")
                for threat in pf_analysis['threats']:
                    lines.append(f"    ✗ {threat}")
            lines.append("")

        # 최근 전이 이력
        recent_events = self.faction_transition_history[-5:]
        if recent_events:
            lines.append("【최근 세력 관계 변화】")
            for event in reversed(recent_events):
                lines.append(f"  Arc{event.arc}Ep{event.episode}: "
                           f"{event.faction_a} vs {event.faction_b} "
                           f"'{event.from_state}' → '{event.to_state}'")
                lines.append(f"    사유: {event.trigger[:30]}...")
            lines.append("")

        lines.append("═" * 50)
        return "\n".join(lines)
