"""
[V40 Premium] 감정선 아크 추적 시스템 (웹소설 특화)

주인공의 감정 상태를 에피소드별로 추적하여 단조로움을 방지합니다.
웹소설 특성상 "절망 속 희망" 공식을 강제하여 독자 이탈을 막습니다.
"""

import json
import re
from collections import Counter


class EmotionArcTracker:
    """
    감정선 아크 추적 시스템

    주인공의 감정 상태를 5화 단위로 추적하여 단조로움 방지
    웹소설 특화: 부정적 감정 지속 시 "희망 씨앗" 강제 삽입
    """

    # 감정 상태 정의 (숫자가 클수록 긍정적)
    EMOTION_STATES = {
        'despair': -2,      # 절망
        'frustration': -1,  # 좌절
        'neutral': 0,       # 평온
        'hope': 1,          # 희망
        'triumph': 2        # 승리
    }

    def __init__(self, project_context) -> None:
        """
        Args:
            project_context: ProjectContext 인스턴스
        """
        self.context = project_context
        self.history = []  # [(ep_num, emotion_state, intensity)]

    def analyze_manuscript_emotion(self, manuscript_content: str) -> tuple:
        """
        원고에서 감정 상태 자동 추출

        Args:
            manuscript_content: 원고 텍스트

        Returns:
            Tuple (emotion_state: str, intensity: float)
            - emotion_state: 'despair', 'frustration', 'neutral', 'hope', 'triumph'
            - intensity: 0.0 - 1.0 (해당 감정의 강도)
        """
        # 감정 키워드 사전 (웹소설에 특화된 표현 포함)
        emotion_keywords = {
            'despair': [
                '절망', '포기', '무력', '좌절', '패배', '암담', '비참', '끝',
                '죽음', '파멸', '막막', '어둠', '나락', '벼랑', '고립'
            ],
            'frustration': [
                '분노', '억울', '원망', '답답', '막막', '짜증', '화',
                '적개심', '증오', '원한', '복수', '치욕', '굴욕'
            ],
            'neutral': [
                '평온', '일상', '담담', '무심', '고요', '평범', '보통',
                '차분', '침착', '냉정', '이성', '계산'
            ],
            'hope': [
                '희망', '기대', '설렘', '가능성', '빛', '기회', '실마리',
                '돌파구', '단서', '조짐', '예감', '기운', '각성'
            ],
            'triumph': [
                '승리', '환희', '쾌감', '통쾌', '압도', '제압', '성공',
                '극복', '달성', '획득', '정복', '우위', '지배', '제압'
            ]
        }

        # 키워드 빈도 분석
        emotion_scores = {}
        for emotion, keywords in emotion_keywords.items():
            count = sum(manuscript_content.count(kw) for kw in keywords)
            emotion_scores[emotion] = count

        # 가장 높은 빈도의 감정 선택
        if not any(emotion_scores.values()):
            return ('neutral', 0.0)

        dominant_emotion = max(emotion_scores, key=emotion_scores.get)
        max_count = emotion_scores[dominant_emotion]

        # 강도 계산 (0.0 - 1.0)
        total_count = sum(emotion_scores.values())
        intensity = max_count / total_count if total_count > 0 else 0.0

        return (dominant_emotion, intensity)

    def check_monotony(self, last_n_episodes: int = 5) -> tuple:
        """
        최근 N화의 감정선이 단조로운지 검사

        Args:
            last_n_episodes: 검사할 최근 에피소드 수

        Returns:
            Tuple (is_monotonous: bool, recommendation: str)
        """
        if len(self.history) < last_n_episodes:
            return (False, "")

        recent = self.history[-last_n_episodes:]
        states = [self.EMOTION_STATES[ep[1]] for ep in recent if ep[1] in self.EMOTION_STATES]

        # [V44] 빈 리스트 체크 (ZeroDivisionError 방지)
        if not states:
            return (False, "")

        # 분산 계산 (감정 변화 정도)
        avg = sum(states) / len(states)
        variance = sum((x - avg) ** 2 for x in states) / len(states)

        # 분산이 0.5 미만이면 단조로움
        if variance < 0.5:
            current_state = recent[-1][1]

            recommendation = self._generate_recommendation(current_state, last_n_episodes)

            return (True, recommendation)

        return (False, "")

    def _generate_recommendation(self, current_state: str, n_episodes: int) -> str:
        """
        현재 감정 상태에 따른 추천 생성 (웹소설 특화)

        Args:
            current_state: 현재 감정 상태
            n_episodes: 지속된 에피소드 수

        Returns:
            추천 텍스트
        """
        if current_state in ['despair', 'frustration']:
            # 🔥 웹소설 핵심: 부정적 감정 속 희망 씨앗
            recommendation = f"""
[🌱 웹소설 특화: 절망 속 희망 씨앗 삽입 필수]
최근 {n_episodes}화 동안 부정적 감정(절망/좌절)이 지속되고 있습니다.
웹소설 독자는 3화 이상 부정 감정이 지속되면 이탈합니다.

[다음 에피소드 필수 요소]
1. **주인공의 상황은 여전히 어렵지만**
2. **작은 돌파구/희망 요소를 반드시 포함**:
   - 숨겨진 기연 발견 (고서, 영약, 비기)
   - 예상치 못한 조력자 출현
   - 적의 약점 포착
   - 새로운 깨달음/각성의 실마리
   - 과거 인연의 도움

[연출 가이드]
- 에피소드 마지막 20%에 "희망 씨앗" 배치
- 독자에게 "이제 좀 나아지려나?" 기대감 제공
- 완전 해결은 아니지만 "가능성"을 보여줌

[예시 구조]
- 80%: 절망 심화 (적의 포위, 내공 고갈, 배신 등)
- 20%: 희망 발견 (바닥에 떨어진 고서 발견 → "이것은...?")

[금지 사항]
❌ 5화 연속 절망 → 독자 우울증 유발
❌ 희망 없는 파국 → 독자 이탈
✅ 절망 속 작은 빛 → 독자 몰입 유지
"""

        elif current_state in ['hope', 'triumph']:
            recommendation = f"""
[⚡ 긴장감 회복 필수]
최근 {n_episodes}화 동안 긍정적 감정(희망/승리)이 지속되고 있습니다.
웹소설은 긴장과 이완의 리듬이 필요합니다.

[다음 에피소드 필수 요소]
1. **새로운 위기나 장애물 제시**:
   - 더 강력한 적 등장
   - 예상치 못한 배신
   - 시간 제약/데드라인
   - 소중한 것의 위협
   - 과거의 업보 회귀

2. **승리의 댓가 암시**:
   - 힘을 쓴 후유증
   - 적이 남긴 복선
   - 새로운 적대 세력의 주목

[연출 가이드]
- 승리 직후 새로운 문제 발견
- "한 고비 넘었지만 진짜는 이제부터"
- 독자: "어? 이제 또 뭐가 나오는 거야?"

[금지 사항]
❌ 5화 연속 승승장구 → 긴장감 제로
❌ 위기 없는 평탄함 → 지루함
✅ 승리 후 새로운 복선 → 긴장 유지
"""

        else:  # neutral
            recommendation = f"""
[📈 감정 진폭 강화 필요]
최근 {n_episodes}화 동안 감정 변화가 미미합니다 (평온/중립).
웹소설은 감정의 롤러코스터가 핵심입니다.

[다음 에피소드 필수 요소]
1. **강렬한 감정 유발 사건**:
   - 분노: 소중한 사람의 위협, 과거 원수 재등장
   - 환희: 대역전, 압도적 승리, 기연 획득

2. **평온을 깨는 사건**:
   - 갑작스러운 암습
   - 예상치 못한 만남
   - 비밀의 폭로

[연출 가이드]
- 독자가 "어? 뭐야?" 하는 반전
- 평온한 일상 → 갑작스러운 사건
"""

        return recommendation

    def get_recommended_emotion_for_next(self) -> tuple:
        """
        다음 에피소드에 권장되는 감정 상태

        Returns:
            Tuple (recommended_state: str, reasoning: str)
        """
        if len(self.history) < 2:
            return ('neutral', "초반부는 상황 설정 중심")

        # 최근 3화 분석
        recent_3 = self.history[-3:] if len(self.history) >= 3 else self.history
        states_numeric = [self.EMOTION_STATES[ep[1]] for ep in recent_3 if ep[1] in self.EMOTION_STATES]  # [V70] KeyError 방어
        if not states_numeric:  # [V70] 유효한 감정 상태 없으면 중립 반환
            return ('neutral', "유효한 감정 이력 없음")
        avg_emotion = sum(states_numeric) / len(states_numeric)

        # 🔥 웹소설 특화: 부정 감정 과다 → 희망 강제
        if avg_emotion < -1.0:
            return ('hope', "최근 부정 감정 과다 → 독자 환기 필수 (웹소설 생존 규칙)")

        # 감정선이 너무 높으면 하강 추천
        elif avg_emotion > 1.0:
            return ('frustration', "최근 긍정 감정 과다 → 긴장감 회복 필요")

        # 최근 3화가 전부 같은 방향이면 반전 추천
        elif len(set(states_numeric)) == 1:
            current = recent_3[-1][1]
            if current in ['despair', 'frustration']:
                return ('hope', "감정선 단조로움 → 희망 주입 (웹소설 필수)")
            else:
                return ('frustration', "감정선 단조로움 → 위기 투입")

        return ('neutral', "현재 감정선 적정 수준")

    def add_episode_emotion(self, ep_num: int, emotion_state: str, intensity: float) -> None:
        """
        에피소드 감정 이력에 추가

        Args:
            ep_num: 에피소드 번호
            emotion_state: 감정 상태
            intensity: 강도 (0.0 - 1.0)
        """
        self.history.append((ep_num, emotion_state, intensity))

        # 최근 50화만 유지 (메모리 절약)
        if len(self.history) > 50:
            self.history = self.history[-50:]

    def get_emotion_report(self) -> dict:
        """
        현재 감정선 리포트 생성

        Returns:
            Dict with emotion statistics
        """
        if not self.history:
            return {"status": "no_data"}

        recent_10 = self.history[-10:] if len(self.history) >= 10 else self.history
        emotions = [ep[1] for ep in recent_10 if len(ep) >= 2]  # 안전한 접근
        emotion_counts = Counter(emotions)

        # 안전한 튜플 언패킹 (구조 검증)
        last_entry = self.history[-1]
        current_emotion = last_entry[1] if len(last_entry) >= 2 else "unknown"
        current_intensity = last_entry[2] if len(last_entry) >= 3 else 0.0

        return {
            "total_episodes": len(self.history),
            "recent_10_distribution": dict(emotion_counts),
            "current_emotion": current_emotion,
            "current_intensity": current_intensity,
            "monotony_detected": self.check_monotony()[0]
        }

    def save_to_db(self, db_manager) -> None:
        """
        감정 이력을 DB에 저장

        Args:
            db_manager: DBManager 인스턴스
        """
        history_data = [
            {"ep_num": ep[0], "emotion": ep[1], "intensity": ep[2]}
            for ep in self.history
            if isinstance(ep, (tuple, list)) and len(ep) >= 3  # [V70] 비정상 튜플 방어
        ]
        db_manager.save_anchor('emotion_history', history_data)

    def load_from_db(self, db_manager) -> None:
        """
        DB에서 감정 이력 로드

        Args:
            db_manager: DBManager 인스턴스
        """
        history_data = db_manager.load_anchor('emotion_history', default=[]) or []  # [V70] None 방어
        self.history = [
            (ep['ep_num'], ep['emotion'], ep['intensity'])
            for ep in history_data
            if isinstance(ep, dict) and all(k in ep for k in ('ep_num', 'emotion', 'intensity'))  # [V70] 3개 키 전부 확인
        ]
