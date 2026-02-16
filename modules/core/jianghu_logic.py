class JianghuLogic:
    """[V24 Sovereign] 고정된 지도를 넘어 강호 전역을 무대로 쓰는 지리 전략 엔진"""

    def __init__(self, context) -> None:
        """[수정] 프로젝트 컨텍스트를 주입받도록 생성자 추가"""
        self.context = context

    # 주요 대도시 간의 '절대 기준' (물리적 일관성용)
    ANCHORS = {"낙양": (0, 0), "장안": (-300, 0), "항주": (500, -500), "북경": (200, 600), "사천": (-600, -400)}

    def calculate_travel_v20(self, departure: str, arrival: str) -> dict:
        """[V24] 거리는 AI가 추론하되, 시스템은 '여정의 무게'만 설정함"""
        dep_pos = self.ANCHORS.get(departure, (0, 0))
        arr_pos = self.ANCHORS.get(arrival, (100, 100))

        # 피타고라스 정리로 대략적인 '리' 단위 환산
        approx_dist = int(((dep_pos[0] - arr_pos[0]) ** 2 + (dep_pos[1] - arr_pos[1]) ** 2) ** 0.5 * 3)
        approx_dist = max(100, approx_dist)

        return {
            "departure": departure,
            "arrival": arrival,
            "approx_distance": f"{approx_dist}리",
            "instruction": (f"현재 {departure}에서 {arrival}로 향하는 여정이다. "),
        }
