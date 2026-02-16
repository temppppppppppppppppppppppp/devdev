"""
[Phase 2.2] Information Diffusion Model
정보(소문) 전파 시뮬레이션 - NPC가 특정 사건을 알고 있어야 하는지 판단

[V49.7] 정보 비대칭 추적 - NPC별 알고 있는 정보 관리 및 검증
"""

import logging
from dataclasses import dataclass
from typing import Any


@dataclass
class KnowledgeEntry:
    """[V49.7] NPC 지식 엔트리"""

    info_id: str  # 정보 식별자
    description: str  # 정보 내용
    learned_arc: int
    learned_episode: int
    source: str  # 어떻게 알게 되었는지


class InformationDiffusion:
    """정보(소문) 전파 시뮬레이션"""

    # 정보 전파 속도 (화 단위)
    DIFFUSION_RATES = {
        "same_location": 0,  # 같은 장소: 즉시
        "same_faction": 1,  # 같은 세력: 1화 후
        "nearby_region": 2,  # 인접 지역: 2화 후
        "distant_region": 5,  # 먼 지역: 5화 후
        "isolated": 999,  # 격리된 곳: 전파 안됨
    }

    def __init__(self, context) -> None:
        self.context = context
        self.events = []

    def load_major_events(self) -> list:
        """DB에서 주요 사건 로드 (소문날 만한 사건만)"""
        events = []

        try:
            # major_events 앵커에서 로드 (있다면)
            stored_events = self.context.db.load_anchor("major_events", default=[])
            if isinstance(stored_events, list):
                events.extend(stored_events)

            # [V66.1] 전체 에피소드의 state_log에서 추출 (이전: 최근 10화만 → 장기 사건 누락)
            latest_ep = self.context.db.get_latest_episode_number()
            for ep in range(1, latest_ep):  # [V70] latest_ep은 MAX+1이므로 +1 불필요
                log_data = self.context.db.load_state_log(ep)

                if log_data and isinstance(log_data, dict):
                    summary = log_data.get("summary", "")

                    # "비무", "승리", "처단", "획득" 같은 주요 키워드 포함 시
                    major_keywords = ["비무", "승리", "처단", "획득", "신물", "고수", "전설"]
                    if any(kw in summary for kw in major_keywords):
                        events.append(
                            {
                                "episode": ep,
                                "description": summary,
                                "location": self._extract_location_from_summary(summary),
                                "importance": self._calculate_importance(summary),
                            }
                        )
        except Exception as e:
            logging.warning(f"⚠️ [InfoDiffusion] 주요 사건 로드 실패: {e}")

        self.events = events
        return events

    def should_npc_know(self, npc: dict, event: dict, current_ep: int) -> dict:
        """
        NPC가 특정 사건을 알고 있어야 하는가?

        Args:
            npc: NPC 정보 dict
            event: 사건 정보 dict
            current_ep: 현재 에피소드

        Returns:
            {
                "should_know": bool,
                "reason": str,
                "event": str,
                "npc": str
            }
        """
        event_ep = event.get("episode", 0)
        event_location = event.get("location", "")
        npc_location = npc.get("current_location", "")
        npc_faction = npc.get("faction", "")

        # 시간 경과
        time_passed = current_ep - event_ep

        # Bible에서 주인공 세력 확인
        protagonist_faction = self._get_protagonist_faction()

        # 지리적/조직적 거리 계산
        if event_location and npc_location and event_location == npc_location:
            distance_type = "same_location"
        elif npc_faction and protagonist_faction and npc_faction == protagonist_faction:
            distance_type = "same_faction"
        elif npc.get("isolated", False):
            distance_type = "isolated"
        elif self._is_nearby(event_location, npc_location):
            distance_type = "nearby_region"
        else:
            distance_type = "distant_region"

        # 전파 속도와 비교
        required_time = self.DIFFUSION_RATES[distance_type]
        should_know = time_passed >= required_time

        return {
            "should_know": should_know,
            "reason": f"{distance_type} (전파 소요: {required_time}화, 실제 경과: {time_passed}화)",
            "event": event.get("description", ""),
            "npc": npc.get("name", ""),
        }

    def _get_protagonist_faction(self) -> str:
        """주인공의 세력 추출"""
        try:
            bible = getattr(self.context, "master_bible", {})
            bible_root = bible.get("MasterBible", bible)
            proj_data = bible_root.get("ProjectData", {})
            return proj_data.get("protagonist_faction", "")
        except Exception:
            return ""

    def _is_nearby(self, loc1: str, loc2: str) -> bool:
        """
        두 지역이 인접한가? (간단한 휴리스틱)

        같은 광역 지역명을 공유하면 인접으로 간주
        """
        if not loc1 or not loc2:
            return False

        # 무협 주요 지역명
        regions_wuxia = ["하북", "강남", "산서", "산동", "하남", "중원", "사천", "강북"]

        # 헌터 주요 지역명
        regions_hunter = ["서울", "경기", "강원", "충청", "전라", "경상", "제주"]

        # 투자 주요 지역명
        regions_investment = ["강남", "여의도", "종로", "서초", "판교"]

        all_regions = regions_wuxia + regions_hunter + regions_investment

        for region in all_regions:
            if region in loc1 and region in loc2:
                return True

        return False

    def _extract_location_from_summary(self, summary: str) -> str:
        """요약문에서 장소 추출 (간단한 휴리스틱)"""
        # "~에서", "~의" 패턴 추출
        import re

        location_patterns = [r"([가-힣]{2,5})(에서|의|로|에)", r"([가-힣]{2,5})(가문|장|객잔|산장)"]

        for pattern in location_patterns:
            match = re.search(pattern, summary)
            if match:
                return match.group(1)

        return ""

    def _calculate_importance(self, summary: str) -> int:
        """
        사건의 중요도 계산 (0-10)

        중요도가 높을수록 빨리 퍼짐
        """
        importance = 5  # 기본값

        # 중요도 증가 키워드
        high_importance_keywords = ["전설", "신물", "맹주", "고수", "처단"]
        for kw in high_importance_keywords:
            if kw in summary:
                importance += 2

        # 중요도 감소 키워드
        low_importance_keywords = ["일상", "휴식", "대화"]
        for kw in low_importance_keywords:
            if kw in summary:
                importance -= 2

        return max(0, min(10, importance))

    # ═══════════════════════════════════════════════════════════════
    # [V49.7] 정보 비대칭 추적 메서드
    # ═══════════════════════════════════════════════════════════════

    def __init_knowledge_tracker(self) -> None:
        """지식 추적기 초기화 (필요시 호출)"""
        if not hasattr(self, "npc_knowledge"):
            self.npc_knowledge: dict[str, list[KnowledgeEntry]] = {}
            self.global_events: dict[str, dict] = {}  # {event_id: event_data}

    def register_event(
        self, event_id: str, description: str, arc: int, episode: int, location: str = "", witnesses: list[str] = None
    ) -> None:
        """
        사건 등록 및 목격자에게 지식 부여

        Args:
            event_id: 사건 식별자 (예: "arc1_ep4_비무승리")
            description: 사건 설명
            arc: Arc 번호
            episode: 에피소드 번호
            location: 사건 장소
            witnesses: 목격한 NPC 목록
        """
        self.__init_knowledge_tracker()

        event_data = {"id": event_id, "description": description, "arc": arc, "episode": episode, "location": location}
        self.global_events[event_id] = event_data

        # 목격자에게 즉시 지식 부여
        if witnesses:
            for npc_name in witnesses:
                self.grant_knowledge(
                    npc_name=npc_name,
                    info_id=event_id,
                    description=description,
                    arc=arc,
                    episode=episode,
                    source="직접 목격",
                )

    def grant_knowledge(
        self, npc_name: str, info_id: str, description: str, arc: int, episode: int, source: str = "소문"
    ) -> None:
        """
        NPC에게 지식 부여

        Args:
            npc_name: NPC 이름
            info_id: 정보 식별자
            description: 정보 내용
            arc: 습득 Arc
            episode: 습득 에피소드
            source: 습득 경로
        """
        self.__init_knowledge_tracker()

        if npc_name not in self.npc_knowledge:
            self.npc_knowledge[npc_name] = []

        # 중복 체크
        existing = [k for k in self.npc_knowledge[npc_name] if k.info_id == info_id]
        if not existing:
            entry = KnowledgeEntry(
                info_id=info_id, description=description, learned_arc=arc, learned_episode=episode, source=source
            )
            self.npc_knowledge[npc_name].append(entry)

    def npc_knows(self, npc_name: str, info_id: str) -> bool:
        """
        NPC가 특정 정보를 알고 있는지 확인

        Args:
            npc_name: NPC 이름
            info_id: 정보 식별자

        Returns:
            알고 있으면 True
        """
        self.__init_knowledge_tracker()

        if npc_name not in self.npc_knowledge:
            return False

        return any(k.info_id == info_id for k in self.npc_knowledge[npc_name])

    def npc_knows_about(self, npc_name: str, keyword: str) -> bool:
        """
        NPC가 특정 키워드 관련 정보를 알고 있는지 확인

        Args:
            npc_name: NPC 이름
            keyword: 검색 키워드

        Returns:
            관련 정보를 알고 있으면 True
        """
        self.__init_knowledge_tracker()

        if npc_name not in self.npc_knowledge:
            return False

        return any(keyword in k.description for k in self.npc_knowledge[npc_name])

    def get_npc_knowledge(self, npc_name: str) -> list[dict]:
        """
        NPC가 알고 있는 모든 정보 조회

        Args:
            npc_name: NPC 이름

        Returns:
            지식 목록
        """
        self.__init_knowledge_tracker()

        if npc_name not in self.npc_knowledge:
            return []

        return [
            {
                "info_id": k.info_id,
                "description": k.description,
                "learned_arc": k.learned_arc,
                "learned_episode": k.learned_episode,
                "source": k.source,
            }
            for k in self.npc_knowledge[npc_name]
        ]

    def validate_npc_reaction(self, npc_name: str, reaction_text: str, required_knowledge: list[str]) -> dict[str, Any]:
        """
        NPC 반응이 그들의 지식과 일치하는지 검증

        Args:
            npc_name: NPC 이름
            reaction_text: NPC의 반응/대사
            required_knowledge: 이 반응에 필요한 정보 ID 목록

        Returns:
            {
                "valid": bool,
                "violations": [],
                "warnings": []
            }
        """
        self.__init_knowledge_tracker()

        violations = []
        warnings = []

        for info_id in required_knowledge:
            if not self.npc_knows(npc_name, info_id):
                # 이 정보를 모르는데 반응함
                event_data = self.global_events.get(info_id, {})
                violations.append(
                    {
                        "type": "knowledge_violation",
                        "npc": npc_name,
                        "missing_info": info_id,
                        "event_description": event_data.get("description", info_id),
                        "message": f"'{npc_name}'은(는) '{info_id}' 사건을 모르는데 이에 반응함",
                    }
                )

        return {"valid": len(violations) == 0, "violations": violations, "warnings": warnings}

    def propagate_event(
        self, event_id: str, current_arc: int, current_episode: int, npc_locations: dict[str, str]
    ) -> list[str]:
        """
        사건 정보를 자연스럽게 전파 (시간 경과에 따라)

        Args:
            event_id: 전파할 사건 ID
            current_arc: 현재 Arc
            current_episode: 현재 에피소드
            npc_locations: {npc_name: location} 맵

        Returns:
            새로 정보를 습득한 NPC 목록
        """
        self.__init_knowledge_tracker()

        if event_id not in self.global_events:
            return []

        event = self.global_events[event_id]
        event_ep = event.get("episode", 0)
        event_location = event.get("location", "")
        time_passed = current_episode - event_ep

        newly_informed = []

        for npc_name, npc_location in npc_locations.items():
            if self.npc_knows(npc_name, event_id):
                continue  # 이미 앎

            # 전파 조건 확인
            if npc_location == event_location:
                distance_type = "same_location"
            elif self._is_nearby(event_location, npc_location):
                distance_type = "nearby_region"
            else:
                distance_type = "distant_region"

            required_time = self.DIFFUSION_RATES.get(distance_type, 999)

            if time_passed >= required_time:
                self.grant_knowledge(
                    npc_name=npc_name,
                    info_id=event_id,
                    description=event.get("description", ""),
                    arc=current_arc,
                    episode=current_episode,
                    source=f"소문 ({distance_type})",
                )
                newly_informed.append(npc_name)

        return newly_informed

    def generate_knowledge_prompt(self, npc_name: str) -> str:
        """
        NPC의 지식 상태를 LLM 프롬프트용 텍스트로 생성

        Args:
            npc_name: NPC 이름

        Returns:
            프롬프트 텍스트
        """
        knowledge = self.get_npc_knowledge(npc_name)

        if not knowledge:
            return f"\n[{npc_name}의 지식 상태: 주요 사건에 대해 아는 것이 없음]\n"

        lines = ["", f"[{npc_name}의 지식 상태]", f"알고 있는 정보 ({len(knowledge)}개):"]

        # [V66.1] 전체 지식 표시 (이전: [:5] 제한 → 100화+ 정보 누락 방지)
        for k in knowledge:
            lines.append(f"  - {k['description'][:80]} (Ep{k['learned_episode']}에 {k['source']})")

        lines.append("")
        return "\n".join(lines)
