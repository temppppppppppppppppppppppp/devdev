"""
[V0128] ActionSceneEvaluator - 전투/액션 씬 평가 (장르 특화)

전투 씬의 동선 명확성, 전투력 일관성, 긴장감 상승을 평가합니다.
"""
import re
from typing import Dict, List, Any, Tuple


class ActionSceneEvaluator:
    """
    전투/액션 씬 평가 (장르 특화)

    무협: 무공, 내공, 경지 기반 전투
    헌터: 스킬, 마나, 레벨 기반 전투
    투자: 협상, 심리전, 경쟁 (비물리적 액션)
    """

    # 장르별 액션 키워드
    ACTION_KEYWORDS = {
        "wuxia": [
            "검", "도", "창", "권", "장", "각",
            "초식", "내공", "기공", "검기", "도기", "장풍",
            "공격", "방어", "피", "회피", "격돌", "충돌",
            "일격", "연타", "반격", "카운터", "막"
        ],
        "hunter": [
            "스킬", "마나", "데미지", "HP", "MP",
            "공격", "방어", "회피", "크리티컬", "버프", "디버프",
            "소환", "시전", "캐스팅", "쿨타임"
        ],
        "investment": [
            "협상", "거래", "계약", "인수", "매각",
            "압박", "설득", "협박", "회유", "포위"
        ]
    }

    # 공간 인식 키워드
    SPATIAL_KEYWORDS = [
        "앞", "뒤", "좌", "우", "위", "아래",
        "옆", "가운데", "중앙", "구석", "모서리",
        "거리", "간격", "보", "장", "척",
        "다가", "물러", "뛰어", "날아", "구르"
    ]

    # 결과 명시 키워드
    OUTCOME_KEYWORDS = [
        "맞", "피", "베", "찔", "관통", "스쳐",
        "막", "피하", "회피", "튕겨", "흘려",
        "쓰러", "무릎", "비틀", "휘청", "후퇴",
        "상처", "피", "부상", "골절", "기절",
        "격파", "파괴", "분쇄", "박살"
    ]

    # [V44] 장르별 액션 씬 감지 임계값 (100자당 키워드 수)
    ACTION_DENSITY_THRESHOLDS = {
        "wuxia": 1.0,      # 무협: 물리적 액션이 밀집
        "hunter": 0.8,     # 헌터: 스킬+액션 혼합
        "investment": 0.5  # 투자: 심리전/협상은 밀도 낮음
    }

    def __init__(self, genre: str = "wuxia"):
        """
        Args:
            genre: 장르 (wuxia, hunter, investment)
        """
        self.genre = genre
        self.action_density_threshold = self.ACTION_DENSITY_THRESHOLDS.get(genre, 1.0)

    def evaluate(self, manuscript: str, context: Dict = None) -> Dict:
        """
        액션 씬 종합 평가

        Args:
            manuscript: 원고 텍스트
            context: 평가 컨텍스트 (HUD, technique_effects 등)

        Returns:
            {
                "total_score": float (0-10),
                "choreography": {...},
                "power_consistency": {...},
                "stakes_escalation": {...},
                "action_scene_count": int,
                "suggestions": [...]
            }
        """
        context = context or {}

        # 액션 씬 추출
        action_scenes = self._extract_action_scenes(manuscript)

        if not action_scenes:
            return {
                "total_score": 10,  # 액션 없으면 만점 (감점 사유 없음)
                "choreography": {"score": 10, "message": "액션 씬 없음"},
                "power_consistency": {"score": 10, "message": "액션 씬 없음"},
                "stakes_escalation": {"score": 10, "message": "액션 씬 없음"},
                "action_scene_count": 0,
                "suggestions": []
            }

        # 세부 평가
        choreography = self.evaluate_choreography(action_scenes)
        power_consistency = self.evaluate_power_consistency(manuscript, context)
        stakes_escalation = self.evaluate_stakes_escalation(action_scenes)

        # 종합 점수 (가중 평균)
        weights = {"choreography": 0.4, "power_consistency": 0.3, "stakes_escalation": 0.3}
        total_score = (
            choreography["score"] * weights["choreography"] +
            power_consistency["score"] * weights["power_consistency"] +
            stakes_escalation["score"] * weights["stakes_escalation"]
        )

        # 개선 제안 수집
        suggestions = []
        if choreography.get("issues"):
            suggestions.extend(choreography["issues"])
        if power_consistency.get("inconsistencies"):
            for inc in power_consistency["inconsistencies"]:
                suggestions.append(f"기술 '{inc['technique']}' 효과 불일치")
        if stakes_escalation.get("suggestion"):
            suggestions.append(stakes_escalation["suggestion"])

        return {
            "total_score": round(total_score, 1),
            "choreography": choreography,
            "power_consistency": power_consistency,
            "stakes_escalation": stakes_escalation,
            "action_scene_count": len(action_scenes),
            "suggestions": suggestions
        }

    def evaluate_choreography(self, action_scenes: List[str]) -> Dict:
        """
        전투 동선 명확성 평가

        Args:
            action_scenes: 추출된 액션 씬 리스트

        Returns:
            {
                "score": float (0-10),
                "issues": [...],
                "details": {...}
            }
        """
        issues = []
        spatial_scores = []
        continuity_scores = []
        outcome_scores = []

        for i, scene in enumerate(action_scenes):
            # 1. 공간 인식 체크
            spatial_clarity = self._check_spatial_clarity(scene)
            spatial_scores.append(spatial_clarity)
            if spatial_clarity < 0.5:
                issues.append(f"씬 {i+1}: 공간 배치 불명확")

            # 2. 동작 연결성 체크
            continuity = self._check_action_continuity(scene)
            continuity_scores.append(continuity)
            if continuity < 0.5:
                issues.append(f"씬 {i+1}: 동작 연결 부자연스러움")

            # 3. 결과 명시 체크
            outcome_clarity = self._check_outcome_clarity(scene)
            outcome_scores.append(outcome_clarity)
            if outcome_clarity < 0.5:
                issues.append(f"씬 {i+1}: 공격 결과 불명확")

        # 평균 점수 계산
        avg_spatial = sum(spatial_scores) / len(spatial_scores) if spatial_scores else 0.5
        avg_continuity = sum(continuity_scores) / len(continuity_scores) if continuity_scores else 0.5
        avg_outcome = sum(outcome_scores) / len(outcome_scores) if outcome_scores else 0.5

        score = ((avg_spatial + avg_continuity + avg_outcome) / 3) * 10

        return {
            "score": round(max(2, score), 1),
            "issues": issues[:5],  # 최대 5개
            "details": {
                "spatial_clarity": round(avg_spatial, 2),
                "action_continuity": round(avg_continuity, 2),
                "outcome_clarity": round(avg_outcome, 2)
            }
        }

    def evaluate_power_consistency(self, manuscript: str, context: Dict) -> Dict:
        """
        전투력 일관성 평가

        같은 기술인데 효과가 다른 경우 감지

        Args:
            manuscript: 원고 텍스트
            context: {"technique_effects": {기술명: 효과 설명}}

        Returns:
            {
                "score": float (0-10),
                "inconsistencies": [...],
                "techniques_used": [...]
            }
        """
        # 사용된 기술 추출
        techniques_used = self._extract_techniques(manuscript)

        if not techniques_used:
            return {
                "score": 10,
                "inconsistencies": [],
                "techniques_used": []
            }

        inconsistencies = []
        technique_effects = context.get('technique_effects', {})

        for tech in techniques_used:
            historical_effect = technique_effects.get(tech)
            if historical_effect:
                current_effect = self._analyze_technique_effect(manuscript, tech)

                if current_effect and self._effects_differ(historical_effect, current_effect):
                    inconsistencies.append({
                        "technique": tech,
                        "historical": historical_effect,
                        "current": current_effect
                    })

        score = 10 - min(len(inconsistencies) * 2, 8)

        return {
            "score": max(2, score),
            "inconsistencies": inconsistencies,
            "techniques_used": list(techniques_used)
        }

    def evaluate_stakes_escalation(self, action_scenes: List[str]) -> Dict:
        """
        전투 긴장감 상승 평가

        Args:
            action_scenes: 추출된 액션 씬 리스트

        Returns:
            {
                "score": float (0-10),
                "stakes_curve": [...],
                "is_escalating": bool,
                "suggestion": str (optional)
            }
        """
        if not action_scenes:
            return {"score": 10, "stakes_curve": [], "is_escalating": True}

        # 각 씬의 긴장도 측정
        stakes_curve = []
        for scene in action_scenes:
            stakes = self._measure_stakes(scene)
            stakes_curve.append(stakes)

        # 상승 곡선인지 체크
        if len(stakes_curve) >= 2:
            # 전체적으로 상승하는지 (마지막이 처음보다 높은지)
            overall_escalation = stakes_curve[-1] >= stakes_curve[0]

            # 중간에 급격히 떨어지는 구간이 있는지
            drops = sum(1 for i in range(len(stakes_curve)-1)
                       if stakes_curve[i+1] < stakes_curve[i] * 0.7)

            is_escalating = overall_escalation and drops <= 1
        else:
            is_escalating = True

        score = 10 if is_escalating else 6
        suggestion = None if is_escalating else "긴장감이 중간에 떨어짐. 클라이맥스를 향해 상승 유지 권장."

        return {
            "score": score,
            "stakes_curve": [round(s, 2) for s in stakes_curve],
            "is_escalating": is_escalating,
            "suggestion": suggestion
        }

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _extract_action_scenes(self, manuscript: str) -> List[str]:
        """원고에서 액션 씬 추출"""
        # 액션 키워드 밀도가 높은 구간 추출
        action_keywords = self.ACTION_KEYWORDS.get(self.genre, self.ACTION_KEYWORDS["wuxia"])

        # 문단 단위로 분리
        paragraphs = manuscript.split('\n\n')

        action_scenes = []
        for para in paragraphs:
            if len(para) < 50:
                continue

            # 액션 키워드 밀도 계산
            keyword_count = sum(1 for kw in action_keywords if kw in para)
            density = keyword_count / (len(para) / 100)  # 100자당 키워드 수

            # [V44] 장르별 임계값 사용
            if density >= self.action_density_threshold:
                action_scenes.append(para)

        return action_scenes

    def _check_spatial_clarity(self, scene: str) -> float:
        """공간 인식 명확성 체크 (0~1)"""
        spatial_count = sum(1 for kw in self.SPATIAL_KEYWORDS if kw in scene)
        # 정규화: 100자당 1개 이상이면 명확
        normalized = min(1.0, spatial_count / max(1, len(scene) / 100))
        return normalized

    def _check_action_continuity(self, scene: str) -> float:
        """동작 연결성 체크 (0~1)"""
        # 연결어 체크
        connectors = ["그리고", "이어", "연이어", "곧바로", "동시에", "순간", "찰나"]
        connector_count = sum(1 for c in connectors if c in scene)

        # 문장 전환 체크 (마침표 수)
        sentence_count = scene.count('.') + scene.count('!') + scene.count('?')

        if sentence_count <= 1:
            return 0.5  # 문장이 하나면 연결성 판단 불가

        # 연결어 비율
        ratio = connector_count / sentence_count
        return min(1.0, ratio * 3)  # 3배 스케일링

    def _check_outcome_clarity(self, scene: str) -> float:
        """결과 명시 체크 (0~1)"""
        outcome_count = sum(1 for kw in self.OUTCOME_KEYWORDS if kw in scene)
        # 정규화: 100자당 0.5개 이상이면 명확
        normalized = min(1.0, outcome_count / max(1, len(scene) / 200))
        return normalized

    def _extract_techniques(self, manuscript: str) -> set:
        """사용된 기술명 추출"""
        # 한글 기술명 패턴 (XX공, XX법, XX술, XX검, XX도, XX권, XX장, XX각)
        pattern = r'[가-힣]{2,6}(?:공|법|술|검|도|권|장|각|식|초)'
        techniques = set(re.findall(pattern, manuscript))
        return techniques

    def _analyze_technique_effect(self, manuscript: str, technique: str) -> str:
        """기술의 현재 효과 분석"""
        # 기술명 주변 텍스트에서 효과 추출
        idx = manuscript.find(technique)
        if idx == -1:
            return None

        # 기술명 전후 50자 추출
        start = max(0, idx - 20)
        end = min(len(manuscript), idx + len(technique) + 50)
        context = manuscript[start:end]

        return context

    def _effects_differ(self, historical: str, current: str) -> bool:
        """효과 차이 감지"""
        if not historical or not current:
            return False

        # 간단한 키워드 기반 비교
        # 위력 관련 키워드
        power_keywords = ["일격", "치명", "파괴", "관통", "분쇄", "강력", "약한"]

        historical_power = [kw for kw in power_keywords if kw in historical]
        current_power = [kw for kw in power_keywords if kw in current]

        # 극단적 차이 감지 (강력 vs 약한 등)
        if ("강력" in historical_power and "약한" in current_power) or \
           ("약한" in historical_power and "강력" in current_power):
            return True

        return False

    def _measure_stakes(self, scene: str) -> float:
        """씬의 긴장도 측정 (0~1)"""
        # 긴장감 키워드
        high_stakes = ["죽", "생사", "절체절명", "위기", "치명", "최후", "마지막"]
        medium_stakes = ["위험", "급박", "긴박", "다급", "절박", "피"]
        low_stakes = ["여유", "쉽", "간단", "가벼"]

        high_count = sum(1 for kw in high_stakes if kw in scene)
        medium_count = sum(1 for kw in medium_stakes if kw in scene)
        low_count = sum(1 for kw in low_stakes if kw in scene)

        # 가중 점수
        score = (high_count * 1.0 + medium_count * 0.5 - low_count * 0.3)

        # 0~1 정규화
        normalized = max(0.0, min(1.0, (score + 2) / 5))

        return normalized
