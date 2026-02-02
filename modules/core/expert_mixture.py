"""
[V52.3] Expert Mixture (전문가 혼합)
씬 유형별 전문화된 프롬프트 분기 시스템

핵심: 추가 비용 없이 씬별 최적화된 가이드 제공

원리:
1. Blueprint에서 씬 유형 감지
2. 유형별 전문가 프롬프트 생성
3. Writer에게 주입

씬 유형:
- ACTION: 전투, 추격, 대결
- DIALOGUE: 대화, 협상, 논쟁
- EMOTIONAL: 감정, 회상, 관계
- EXPOSITION: 설명, 묘사, 전개
- CLIMAX: 클라이맥스, 반전
- TRANSITION: 장면 전환, 이동

사용:
    expert = ExpertMixture(genre='wuxia')
    prompt = expert.get_scene_prompt(scene_type, context)
    # 또는 Blueprint에서 자동 감지
    prompts = expert.analyze_blueprint(blueprint)
"""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import re


class SceneType(Enum):
    """씬 유형"""
    ACTION = "action"           # 전투, 추격, 대결
    DIALOGUE = "dialogue"       # 대화, 협상, 논쟁
    EMOTIONAL = "emotional"     # 감정, 회상, 관계
    EXPOSITION = "exposition"   # 설명, 묘사, 전개
    CLIMAX = "climax"           # 클라이맥스, 반전
    TRANSITION = "transition"   # 장면 전환, 이동
    MYSTERY = "mystery"         # 미스터리, 복선
    COMEDY = "comedy"           # 유머, 사이다


@dataclass
class SceneAnalysis:
    """씬 분석 결과"""
    scene_id: str
    scene_type: SceneType
    description: str
    expert_prompt: str
    weight: float = 1.0  # 중요도


class ExpertMixture:
    """전문가 혼합 시스템"""

    # 씬 유형 감지 키워드
    SCENE_KEYWORDS = {
        SceneType.ACTION: [
            "전투", "대결", "격돌", "교전", "추격", "도주", "습격",
            "공격", "방어", "회피", "타격", "검격", "권격", "발경",
            "fight", "battle", "combat", "chase", "attack"
        ],
        SceneType.DIALOGUE: [
            "대화", "협상", "논쟁", "설득", "심문", "회담", "논의",
            "대담", "면담", "토론", "언쟁", "맞서다",
            "dialogue", "conversation", "negotiation"
        ],
        SceneType.EMOTIONAL: [
            "감정", "회상", "추억", "슬픔", "기쁨", "분노", "공포",
            "그리움", "후회", "결의", "다짐", "이별", "재회", "화해",
            "emotional", "flashback", "memory"
        ],
        SceneType.EXPOSITION: [
            "설명", "배경", "묘사", "소개", "관찰", "탐색",
            "상황", "환경", "분위기",
            "description", "setting", "exposition"
        ],
        SceneType.CLIMAX: [
            "클라이맥스", "절정", "반전", "폭로", "진실", "결전",
            "최후", "결말", "결정적",
            "climax", "twist", "revelation"
        ],
        SceneType.TRANSITION: [
            "이동", "전환", "시간경과", "장면전환", "도착", "출발",
            "transition", "travel", "timeskip"
        ],
        SceneType.MYSTERY: [
            "미스터리", "의문", "복선", "단서", "수수께끼", "암시",
            "정체", "비밀",
            "mystery", "clue", "foreshadowing"
        ],
        SceneType.COMEDY: [
            "유머", "코미디", "사이다", "통쾌", "웃음", "해학",
            "comedy", "humor", "satisfaction"
        ],
    }

    # 장르별 전문가 프롬프트
    EXPERT_PROMPTS = {
        "wuxia": {
            SceneType.ACTION: """[⚔️ 전투 씬 전문가 가이드]
1. **초식 묘사**: 단순히 "공격했다"가 아닌, 구체적 초식명과 동작 묘사
   - 예: "왼발을 축으로 회전하며 검을 비스듬히 올려쳤다 (비화류격)"
2. **감각 묘사**: 검풍, 살기, 내공 충돌의 촉각/청각 묘사
3. **리듬 조절**: 빠른 교환 후 정적, 호흡 묘사로 긴장 유지
4. **부상 반영**: 기존 부상이 전투에 미치는 영향 명시
5. **심리전**: 표정, 눈빛, 기선제압 묘사""",

            SceneType.DIALOGUE: """[💬 대화 씬 전문가 가이드]
1. **서브텍스트**: 말 뒤에 숨은 의도를 보여주되 직접 설명하지 않기
2. **캐릭터 말투**: 각 캐릭터의 고유한 어투/어휘 유지
3. **침묵 활용**: 말하지 않는 순간도 의미있게
4. **물리적 행동**: 대화 중 손짓, 시선, 자세 변화
5. **무협 예절**: 높임말, 호칭, 격식 반영""",

            SceneType.EMOTIONAL: """[💔 감정 씬 전문가 가이드]
1. **Show Don't Tell**: "슬펐다" 대신 "목이 메어 말을 잇지 못했다"
2. **신체 반응**: 떨림, 눈물, 숨막힘 등 물리적 증상
3. **환경 연동**: 감정과 날씨/풍경 연결 (비, 바람 등)
4. **기억 활용**: 과거 장면 단편 삽입
5. **호흡 조절**: 짧은 문장으로 긴장, 긴 문장으로 회상""",

            SceneType.EXPOSITION: """[📜 설명 씬 전문가 가이드]
1. **행동 통합**: 설명 중에도 캐릭터 동작 삽입
2. **오감 활용**: 시각만이 아닌 청각/후각/촉각
3. **분량 제한**: 순수 설명은 3문장 이내, 행동 삽입
4. **관점 유지**: 주인공 시점에서 관찰 가능한 것만
5. **복선 삽입**: 나중에 중요해질 디테일 슬쩍""",

            SceneType.CLIMAX: """[🔥 클라이맥스 전문가 가이드]
1. **템포 가속**: 문장 짧게, 동사 강조
2. **감각 과부하**: 모든 감각 동원
3. **시간 왜곡**: 결정적 순간 슬로모션 효과
4. **복선 회수**: 앞서 심은 요소 활용
5. **반전 여운**: 독자 예상 뒤집기""",

            SceneType.TRANSITION: """[🚶 전환 씬 전문가 가이드]
1. **시간 표시**: 명확한 시간 경과 언급
2. **공간 이동**: 이동 경로 간략 묘사
3. **심리 변화**: 이동 중 생각/결심
4. **복선**: 다음 사건 암시
5. **간결함**: 불필요하게 늘리지 않기""",

            SceneType.MYSTERY: """[🔍 미스터리 씬 전문가 가이드]
1. **단서 배치**: 명확하지만 눈에 띄지 않게
2. **오해 유도**: 독자를 잘못된 방향으로
3. **긴장 유지**: 의문을 품게 하는 묘사
4. **관찰력**: 주인공의 분석 과정 보여주기
5. **암시**: 직접 말하지 않고 느끼게""",

            SceneType.COMEDY: """[😄 유머/사이다 전문가 가이드]
1. **타이밍**: 긴장 후 해소, 예상치 못한 순간
2. **캐릭터성**: 캐릭터 특성 활용한 유머
3. **상황 역전**: 고구마 후 통쾌한 반전
4. **자연스러움**: 억지 웃음 유발 금지
5. **과하지 않게**: 분위기 파괴 주의""",
        },

        "hunter": {
            SceneType.ACTION: """[⚔️ 전투 씬 전문가 가이드 - 헌터]
1. **스킬 묘사**: 스킬명, 시전 동작, 이펙트 구체화
2. **마나 관리**: 마나 소모와 잔량 언급
3. **몬스터 특성**: 적의 패턴, 약점 활용
4. **파티 협동**: 역할 분담, 콤보 공격
5. **긴장감**: 위험도, 등급 차이 강조""",

            SceneType.DIALOGUE: """[💬 대화 씬 전문가 가이드 - 헌터]
1. **길드 정치**: 이해관계, 정보전
2. **헌터 용어**: 등급, 던전, 스킬 등 자연스럽게
3. **거래 협상**: 아이템, 정보, 동맹
4. **현대적 대화**: 스마트폰, 인터넷 언급 가능
5. **계급 의식**: 등급별 대우 차이""",
        },

        "investment": {
            SceneType.ACTION: """[💰 협상/거래 전문가 가이드 - 투자]
1. **심리전**: 포커페이스, 허세, 블러핑
2. **숫자 구체화**: 금액, 비율, 기한 명시
3. **리스크 언급**: 실패 가능성 암시
4. **전문 용어**: 주식/부동산 용어 자연스럽게
5. **긴장감**: 타이밍, 데드라인""",

            SceneType.EMOTIONAL: """[💔 감정 씬 전문가 가이드 - 투자]
1. **실패의 무게**: 경제적 손실의 심리적 영향
2. **성공의 허무**: 돈으로 살 수 없는 것
3. **인간관계**: 돈과 관계의 갈등
4. **회귀자 고뇌**: 미래 지식의 부담
5. **가족/친구**: 부와 인간관계""",
        },
    }

    def __init__(self, genre: str = "wuxia"):
        self.genre = genre
        self.prompts = self.EXPERT_PROMPTS.get(genre, self.EXPERT_PROMPTS["wuxia"])

    def detect_scene_type(self, scene_text: str) -> Tuple[SceneType, float]:
        """
        씬 텍스트에서 유형 감지

        Returns:
            (SceneType, confidence)
        """
        text_lower = scene_text.lower()

        scores = {}
        for scene_type, keywords in self.SCENE_KEYWORDS.items():
            score = 0
            for kw in keywords:
                if kw.lower() in text_lower:
                    score += 1
            scores[scene_type] = score

        if not any(scores.values()):
            return SceneType.EXPOSITION, 0.3  # 기본값

        best_type = max(scores, key=scores.get)
        max_score = scores[best_type]
        total_keywords = len(self.SCENE_KEYWORDS[best_type])
        confidence = min(1.0, max_score / max(total_keywords * 0.3, 1))

        return best_type, confidence

    def get_scene_prompt(
        self,
        scene_type: SceneType,
        context: Dict[str, Any] = None
    ) -> str:
        """
        씬 유형에 맞는 전문가 프롬프트 반환
        """
        base_prompt = self.prompts.get(scene_type, "")

        if not base_prompt:
            # 해당 장르에 없으면 무협 기본값
            base_prompt = self.EXPERT_PROMPTS["wuxia"].get(
                scene_type,
                "[씬 작성 가이드] 장면의 목적을 명확히 하고, 감각적 묘사를 포함하세요."
            )

        return base_prompt

    def analyze_blueprint(self, blueprint: Dict[str, Any]) -> List[SceneAnalysis]:
        """
        Blueprint에서 씬들을 분석하고 각각에 맞는 프롬프트 생성
        """
        analyses = []

        scene_breakdown = blueprint.get('scene_breakdown', {})
        if not scene_breakdown:
            # 대안: integrated_scenario에서 추출
            scenario = blueprint.get('integrated_scenario', '')
            if scenario:
                scene_type, conf = self.detect_scene_type(scenario)
                analyses.append(SceneAnalysis(
                    scene_id="main",
                    scene_type=scene_type,
                    description=scenario[:100],
                    expert_prompt=self.get_scene_prompt(scene_type),
                    weight=conf
                ))
            return analyses

        for scene_id, scene_data in scene_breakdown.items():
            if isinstance(scene_data, dict):
                description = scene_data.get('description', scene_data.get('content', ''))
            else:
                description = str(scene_data)

            scene_type, confidence = self.detect_scene_type(description)

            analyses.append(SceneAnalysis(
                scene_id=scene_id,
                scene_type=scene_type,
                description=description[:100],
                expert_prompt=self.get_scene_prompt(scene_type),
                weight=confidence
            ))

        return analyses

    def generate_writer_injection(
        self,
        blueprint: Dict[str, Any],
        max_prompts: int = 3
    ) -> str:
        """
        Writer에게 주입할 통합 전문가 가이드 생성
        """
        analyses = self.analyze_blueprint(blueprint)

        if not analyses:
            return ""

        # 중요도 순 정렬
        analyses.sort(key=lambda x: x.weight, reverse=True)

        # 상위 씬들의 프롬프트 수집
        seen_types = set()
        prompts = []

        for analysis in analyses:
            if analysis.scene_type not in seen_types:
                prompts.append(analysis.expert_prompt)
                seen_types.add(analysis.scene_type)

            if len(prompts) >= max_prompts:
                break

        if not prompts:
            return ""

        header = "[V52.3 Expert Mixture - 씬별 전문가 가이드]"
        return header + "\n\n" + "\n\n".join(prompts)

    def get_dominant_scene_type(self, blueprint: Dict[str, Any]) -> SceneType:
        """Blueprint의 지배적 씬 유형 반환"""
        analyses = self.analyze_blueprint(blueprint)

        if not analyses:
            return SceneType.EXPOSITION

        # 가중 투표
        votes = {}
        for a in analyses:
            votes[a.scene_type] = votes.get(a.scene_type, 0) + a.weight

        return max(votes, key=votes.get)
