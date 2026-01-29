"""
[Phase 2.2] Information Diffusion Model
정보(소문) 전파 시뮬레이션 - NPC가 특정 사건을 알고 있어야 하는지 판단
"""


class InformationDiffusion:
    """정보(소문) 전파 시뮬레이션"""

    # 정보 전파 속도 (화 단위)
    DIFFUSION_RATES = {
        "same_location": 0,      # 같은 장소: 즉시
        "same_faction": 1,       # 같은 세력: 1화 후
        "nearby_region": 2,      # 인접 지역: 2화 후
        "distant_region": 5,     # 먼 지역: 5화 후
        "isolated": 999          # 격리된 곳: 전파 안됨
    }

    def __init__(self, context):
        self.context = context
        self.events = []

    def load_major_events(self) -> list:
        """DB에서 주요 사건 로드 (소문날 만한 사건만)"""
        events = []

        try:
            # major_events 앵커에서 로드 (있다면)
            stored_events = self.context.db.load_anchor('major_events', default=[])
            if isinstance(stored_events, list):
                events.extend(stored_events)

            # 최근 10화의 state_log에서도 추출
            latest_ep = self.context.db.get_latest_episode_number()
            for ep in range(max(1, latest_ep - 10), latest_ep + 1):
                log_data = self.context.db.load_state_log(ep)

                if log_data and isinstance(log_data, dict):
                    summary = log_data.get('summary', '')

                    # "비무", "승리", "처단", "획득" 같은 주요 키워드 포함 시
                    major_keywords = ["비무", "승리", "처단", "획득", "신물", "고수", "전설"]
                    if any(kw in summary for kw in major_keywords):
                        events.append({
                            'episode': ep,
                            'description': summary,
                            'location': self._extract_location_from_summary(summary),
                            'importance': self._calculate_importance(summary)
                        })
        except Exception as e:
            print(f"      ⚠️ [InfoDiffusion] 주요 사건 로드 실패: {e}")

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
        event_ep = event.get('episode', 0)
        event_location = event.get('location', '')
        npc_location = npc.get('current_location', '')
        npc_faction = npc.get('faction', '')

        # 시간 경과
        time_passed = current_ep - event_ep

        # Bible에서 주인공 세력 확인
        protagonist_faction = self._get_protagonist_faction()

        # 지리적/조직적 거리 계산
        if event_location and npc_location and event_location == npc_location:
            distance_type = "same_location"
        elif npc_faction and protagonist_faction and npc_faction == protagonist_faction:
            distance_type = "same_faction"
        elif npc.get('isolated', False):
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
            "event": event.get('description', ''),
            "npc": npc.get('name', '')
        }

    def _get_protagonist_faction(self) -> str:
        """주인공의 세력 추출"""
        try:
            bible = getattr(self.context, 'master_bible', {})
            bible_root = bible.get('MasterBible', bible)
            proj_data = bible_root.get('ProjectData', {})
            return proj_data.get('protagonist_faction', '')
        except Exception:
            return ''

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
        location_patterns = [
            r'([가-힣]{2,5})(에서|의|로|에)',
            r'([가-힣]{2,5})(가문|장|객잔|산장)'
        ]

        for pattern in location_patterns:
            match = re.search(pattern, summary)
            if match:
                return match.group(1)

        return ''

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
