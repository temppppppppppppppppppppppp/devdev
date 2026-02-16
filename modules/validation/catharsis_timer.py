"""
[V0128] CatharsisTimer - 카타르시스(사이다) 타이밍 관리

답답한 전개가 너무 길어지지 않도록 관리합니다.
연속 N화 이상 답답한 전개 시 경고를 발생시킵니다.
"""


class CatharsisTimer:
    """
    카타르시스(사이다) 타이밍 관리

    답답한 전개가 너무 길어지지 않도록 관리합니다.
    웹소설 상업성의 핵심 요소인 '사이다' 타이밍을 최적화합니다.
    """

    # 최대 연속 답답함 허용 화수 (기본값: 3화)
    MAX_FRUSTRATION_EPISODES = 3

    # [V44] 장르별 카타르시스 지표 (강도 가중치 추가)
    # 형식: {"indicator": weight} - 1.0=기본, 1.5=강함, 2.0=매우 강함
    CATHARSIS_INDICATORS = {
        "common": [
            "통쾌",
            "시원",
            "승리",
            "인정",
            "감탄",
            "경악",
            "꿇",
            "굴복",
            "사과",
            "보상",
            "획득",
            "성장",
            "돌파",
            "각성",
            "깨달음",
            "성공",
            "달성",
        ],
        "wuxia": ["제압", "일격", "격파", "승전", "무찌", "꺾", "복수", "설욕", "천하", "무림", "절정", "경지"],
        "hunter": ["클리어", "레벨업", "각성", "랭크업", "보스 처치", "드랍", "레어", "유니크", "레전더리", "SSS급"],
        "investment": ["수익", "대박", "인수", "상한가", "텐배거", "역전", "성공", "계약", "합병", "IPO"],
    }

    # [V44] 강한 카타르시스 키워드 (가중치 1.5~2.0)
    STRONG_CATHARSIS_WEIGHTS = {
        "common": {"통쾌": 1.5, "굴복": 1.5, "경악": 1.3},
        "wuxia": {"복수": 2.0, "일격": 1.5, "절정": 1.5, "천하": 1.8},
        "hunter": {"SSS급": 2.0, "레전더리": 1.8, "보스 처치": 1.5},
        "investment": {"텐배거": 2.0, "대박": 1.5, "상한가": 1.5},
    }

    # 장르별 좌절 지표 (답답함)
    FRUSTRATION_INDICATORS = {
        "common": ["패배", "실패", "좌절", "무력", "절망", "도망", "후퇴", "포기", "배신", "손실"],
        "wuxia": ["중상", "패퇴", "탈출", "굴욕", "농락", "함정", "독", "부상", "격차", "무력화"],
        "hunter": ["파티 전멸", "실패", "리타이어", "페널티", "장비 파괴", "경험치 손실", "강등"],
        "investment": ["손절", "폭락", "파산", "실패", "배신", "소송", "부도", "적자", "하한가"],
    }

    def __init__(self, max_frustration: int = None, genre: str = "wuxia"):
        """
        Args:
            max_frustration: 최대 연속 답답함 허용 (기본 3화)
            genre: 장르 (wuxia, hunter, investment)
        """
        self.max_frustration = max_frustration or self.MAX_FRUSTRATION_EPISODES
        self.genre = genre

    def check_catharsis_timing(self, ep_num: int, manuscript: str, history: list[dict] = None) -> dict:
        """
        카타르시스 타이밍 체크

        Args:
            ep_num: 현재 에피소드 번호
            manuscript: 원고 텍스트
            history: 이전 에피소드들의 카타르시스 기록
                     [{"ep_num": 1, "has_catharsis": True}, ...]

        Returns:
            {
                "status": "ok" | "warning" | "critical",
                "streak": int,  # 연속 답답함 화수
                "has_catharsis": bool,
                "catharsis_score": float,  # 0.0 ~ 1.0
                "message": str,
                "suggestion": str (optional)
            }
        """
        history = history or []

        # 현재 화의 카타르시스 분석
        catharsis_result = self._analyze_catharsis(manuscript)
        has_catharsis = catharsis_result["has_catharsis"]
        catharsis_score = catharsis_result["score"]

        # 최근 답답한 전개 연속 횟수
        frustration_streak = self._count_frustration_streak(history)

        # 상태 판정
        if frustration_streak >= self.max_frustration and not has_catharsis:
            status = "critical" if frustration_streak >= self.max_frustration + 2 else "warning"
            return {
                "status": status,
                "streak": frustration_streak,
                "has_catharsis": has_catharsis,
                "catharsis_score": catharsis_score,
                "message": f"연속 {frustration_streak}화 답답한 전개. 사이다 필요.",
                "suggestion": self._generate_suggestion(frustration_streak),
            }

        return {
            "status": "ok",
            "streak": 0 if has_catharsis else frustration_streak,
            "has_catharsis": has_catharsis,
            "catharsis_score": catharsis_score,
            "message": "적절한 카타르시스 배치" if has_catharsis else f"답답함 {frustration_streak}화 진행 중",
        }

    def _analyze_catharsis(self, manuscript: str) -> dict:
        """[V44] 카타르시스 요소 상세 분석 (가중치 기반)"""
        # 장르별 + 공통 지표 결합
        indicators = self.CATHARSIS_INDICATORS["common"] + self.CATHARSIS_INDICATORS.get(self.genre, [])

        # 좌절 지표
        frustration_indicators = self.FRUSTRATION_INDICATORS["common"] + self.FRUSTRATION_INDICATORS.get(self.genre, [])

        # [V44] 가중치 맵 결합
        weights = {}
        weights.update(self.STRONG_CATHARSIS_WEIGHTS.get("common", {}))
        weights.update(self.STRONG_CATHARSIS_WEIGHTS.get(self.genre, {}))

        # [V44] 가중치 적용 카타르시스 점수 계산
        catharsis_score = 0.0
        catharsis_count = 0
        for ind in indicators:
            if ind in manuscript:
                catharsis_count += 1
                weight = weights.get(ind, 1.0)
                catharsis_score += weight

        # 좌절 지표는 단순 카운트 (가중치 1.0)
        frustration_count = sum(1 for ind in frustration_indicators if ind in manuscript)

        # [V44] 순 카타르시스 점수 (가중치 적용)
        net_score = catharsis_score - frustration_count

        # 0~1 스케일로 정규화 (가중치 고려해 범위 확장)
        if catharsis_count + frustration_count > 0:
            score = max(0.0, min(1.0, (net_score + 5) / 12))  # 12로 조정 (가중치 고려)
        else:
            score = 0.5  # 중립

        return {
            "has_catharsis": catharsis_score > frustration_count,
            "score": round(score, 3),
            "catharsis_count": catharsis_count,
            "catharsis_weighted_score": round(catharsis_score, 2),
            "frustration_count": frustration_count,
            "net_score": round(net_score, 2),
        }

    def _count_frustration_streak(self, history: list[dict]) -> int:
        """최근 연속 답답함 화수 계산"""
        if not history:
            return 0

        # 최근 순으로 정렬
        sorted_history = sorted(history, key=lambda x: x.get("ep_num", 0), reverse=True)

        streak = 0
        for record in sorted_history:
            if record.get("has_catharsis", False):
                break
            streak += 1

        return streak

    def _generate_suggestion(self, streak: int) -> str:
        """상황에 맞는 개선 제안 생성"""
        if streak >= 5:
            return "독자 이탈 위험! 이번 화에 반드시 명확한 승리/보상 장면 필요."
        elif streak >= 4:
            return "답답함이 누적됨. 작은 승리라도 반드시 포함 필요."
        else:
            return "이번 화에 작은 승리/인정/보상 요소 추가 권장."

    def get_recommended_catharsis_type(self, context: dict = None) -> list[str]:
        """현재 맥락에 맞는 카타르시스 유형 추천"""
        context = context or {}

        recommendations = []

        # 장르별 추천
        if self.genre == "wuxia":
            recommendations = [
                "전투 승리 (일격에 제압)",
                "경지 돌파 (내공 상승)",
                "복수 달성 (원수 처단)",
                "인정 획득 (무림 인사의 감탄)",
                "비급/보물 획득",
            ]
        elif self.genre == "hunter":
            recommendations = ["보스 클리어", "레벨업/랭크업", "레어 아이템 드랍", "파티원 인정", "각성 능력 해금"]
        elif self.genre == "investment":
            recommendations = ["큰 수익 실현", "기업 인수 성공", "경쟁자 제압", "투자 성공 인정", "새로운 기회 발견"]
        else:
            recommendations = ["목표 달성", "적대자 제압", "주변 인물의 인정", "성장/능력 향상", "보상 획득"]

        return recommendations

    def record_episode(self, ep_num: int, manuscript: str) -> dict:
        """에피소드의 카타르시스 기록 생성"""
        result = self._analyze_catharsis(manuscript)

        return {
            "ep_num": ep_num,
            "has_catharsis": result["has_catharsis"],
            "catharsis_score": result["score"],
            "timestamp": None,  # 호출 시 채워짐
        }
