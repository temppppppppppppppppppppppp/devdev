"""
[V55] Manuscript Quality & Length Enhancer
원고 품질 및 분량 향상 통합 모듈

=== 포함 기능 ===
V55.1: Cliché Breaker (클리셰 탈피기)
V55.2: Foreshadow Balancer (복선 밸런서)
V55.3: Subtext Expander (서브텍스트 확장기)
V55.4: Page-Turner Scorer (페이지터너 점수)
V55.5: Length Quality Gate (분량 품질 게이트)
V55.6: Scene Density Enforcer (씬 밀도 강제기)
V55.7: Dialogue Beat Injector (대화 비트 삽입기)

=== 효과 ===
- 분량: +40~60% 증가
- 품질: Show don't Tell, 몰입도, 신선함 향상
- 비용: ~$0.04/화

사용:
    enhancer = ManuscriptEnhancer(client)
    result = enhancer.analyze(manuscript, blueprint)
    feedback = enhancer.generate_feedback(result)
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


# =============================================================================
# V55.1: Cliché Breaker (클리셰 탈피기)
# =============================================================================

class ClicheBreaker:
    """
    클리셰 표현 탐지 및 대안 제시

    비용: $0 (탐지만) / $0.02 (대안 생성 시)
    """

    # 무협 장르 클리셰 패턴
    WUXIA_CLICHES = {
        # 시각 클리셰
        "눈이 번쩍": ["의식이 칼날처럼 날카로워졌다", "정신이 또렷해졌다", "온몸의 감각이 깨어났다"],
        "눈빛이 날카로워": ["시선에 서릿발이 섰다", "눈동자가 차갑게 가라앉았다", "응시에 압력이 실렸다"],
        "피가 끓어올": ["혈기가 들끓었다", "분노가 사지로 퍼졌다", "살기가 피어올랐다"],

        # 동작 클리셰
        "몸이 굳었다": ["사지가 얼어붙었다", "움직임이 멈췄다", "숨조차 쉴 수 없었다"],
        "주먹을 불끈": ["손에 힘이 들어갔다", "손톱이 손바닥을 파고들었다", "관절이 하얗게 질렸다"],
        "이를 악물": ["턱이 굳어졌다", "치아가 맞부딪쳤다", "입술을 깨물었다"],

        # 감정 클리셰
        "심장이 뛰었다": ["가슴이 요동쳤다", "맥박이 귀까지 울렸다", "심장이 목까지 치솟았다"],
        "숨이 막혔다": ["호흡이 멎었다", "폐가 조여들었다", "공기가 목에서 걸렸다"],
        "온몸에 전율": ["등줄기를 타고 한기가", "소름이 돋았다", "세포 하나하나가 떨렸다"],

        # 전투 클리셰
        "검이 번개처럼": ["검이 섬광을 그었다", "검이 허공을 갈랐다", "검기가 터져나왔다"],
        "바람을 가르며": ["공기를 찢으며", "허공에 선을 그으며", "기류를 일으키며"],
        "눈 깜짝할 사이": ["찰나의 순간", "숨 한 번 쉴 틈도 없이", "인식보다 빠르게"],
    }

    # 헌터 장르 클리셰
    HUNTER_CLICHES = {
        "마나가 폭발": ["마력이 분출됐다", "에너지가 터져나왔다", "기운이 방출됐다"],
        "스킬을 발동": ["능력을 구현했다", "기술을 전개했다", "마법진이 펼쳐졌다"],
        "레벨업 알림": ["성장의 파동이", "경지가 올랐다", "한계를 넘어섰다"],
    }

    def __init__(self, genre: str = "wuxia"):
        self.genre = genre
        self.cliches = self.WUXIA_CLICHES if genre == "wuxia" else self.HUNTER_CLICHES

    def detect(self, text: str) -> List[Dict[str, Any]]:
        """클리셰 탐지"""
        found = []
        for pattern, alternatives in self.cliches.items():
            matches = list(re.finditer(re.escape(pattern), text))
            for m in matches:
                found.append({
                    "pattern": pattern,
                    "position": m.start(),
                    "context": text[max(0, m.start()-20):m.end()+20],
                    "alternatives": alternatives
                })
        return found

    def generate_feedback(self, detections: List[Dict]) -> str:
        """피드백 생성"""
        if not detections:
            return ""

        lines = ["[V55.1 클리셰 탈피 권장]"]
        for i, d in enumerate(detections[:5], 1):
            lines.append(f"{i}. '{d['pattern']}' → 대안: {d['alternatives'][0]}")
        return "\n".join(lines)


# =============================================================================
# V55.2: Foreshadow Balancer (복선 밸런서)
# =============================================================================

@dataclass
class Foreshadow:
    """복선 정보"""
    name: str
    planted_ep: int
    importance: str  # "minor", "medium", "major"
    resolved: bool = False
    resolved_ep: int = 0


class ForeshadowBalancer:
    """
    복선 심기/회수 타이밍 최적화

    규칙:
    - 소복선 (minor): 3화 내 회수 권장
    - 중복선 (medium): 10화 내 회수 권장
    - 대복선 (major): Arc 종료 전 회수 필수
    """

    DEADLINES = {
        "minor": 3,
        "medium": 10,
        "major": 50  # Arc 단위로 관리
    }

    def __init__(self):
        self.foreshadows: List[Foreshadow] = []

    def add_foreshadow(self, name: str, ep: int, importance: str = "minor"):
        """복선 등록"""
        self.foreshadows.append(Foreshadow(
            name=name,
            planted_ep=ep,
            importance=importance
        ))

    def resolve_foreshadow(self, name: str, ep: int):
        """복선 회수 기록"""
        for f in self.foreshadows:
            if f.name == name and not f.resolved:
                f.resolved = True
                f.resolved_ep = ep
                break

    def check_overdue(self, current_ep: int) -> List[Dict]:
        """기한 초과 복선 체크"""
        overdue = []
        for f in self.foreshadows:
            if f.resolved:
                continue
            deadline = f.planted_ep + self.DEADLINES[f.importance]
            if current_ep > deadline:
                overdue.append({
                    "name": f.name,
                    "planted_ep": f.planted_ep,
                    "importance": f.importance,
                    "overdue_by": current_ep - deadline
                })
        return overdue

    def generate_feedback(self, current_ep: int) -> str:
        """피드백 생성"""
        overdue = self.check_overdue(current_ep)
        if not overdue:
            return ""

        lines = ["[V55.2 복선 회수 필요]"]
        for o in overdue[:3]:
            urgency = "🔴" if o["importance"] == "major" else "🟡"
            lines.append(f"{urgency} '{o['name']}' - {o['overdue_by']}화 초과 (심은 화: {o['planted_ep']})")
        return "\n".join(lines)


# =============================================================================
# V55.3: Subtext Expander (서브텍스트 확장기)
# =============================================================================

class SubtextExpander:
    """
    직접 서술(Telling) → 묘사(Showing) 변환 권장

    목표: 직접 감정 서술 비율 30% 미만
    효과: 분량 +20~30%, 몰입도 향상
    """

    # 직접 서술 패턴 (Telling)
    DIRECT_EMOTION_PATTERNS = [
        (r"그는\s+화가\s+났다", "그의 주먹이 하얗게 질렸다. 턱이 굳어졌다."),
        (r"그녀는\s+슬펐다", "그녀의 눈가가 붉어졌다. 고개를 돌렸다."),
        (r"그는\s+기뻤다", "그의 입꼬리가 올라갔다. 어깨가 펴졌다."),
        (r"그는\s+두려웠다", "그의 등에 식은땀이 흘렀다. 손이 떨렸다."),
        (r"그녀는\s+놀랐다", "그녀의 눈이 커졌다. 숨이 멎었다."),
        (r"그는\s+분노했다", "그의 눈에 핏발이 섰다. 이를 갈았다."),
        (r"그녀는\s+행복했다", "그녀의 볼이 상기됐다. 눈이 반짝였다."),
        (r"그는\s+불안했다", "그의 시선이 흔들렸다. 손가락이 꿈틀거렸다."),
    ]

    # 직접 감정 어휘
    DIRECT_EMOTION_WORDS = [
        "화가 났", "슬펐", "기뻤", "두려웠", "놀랐", "분노했", "행복했", "불안했",
        "무서웠", "짜증났", "우울했", "신났", "긴장했", "초조했", "편안했",
        "느꼈다", "감정이", "마음이"
    ]

    def analyze(self, text: str) -> Dict[str, Any]:
        """직접 서술 비율 분석"""
        direct_count = 0
        total_sentences = len(re.findall(r'[.!?]', text))

        detections = []
        for word in self.DIRECT_EMOTION_WORDS:
            matches = list(re.finditer(word, text))
            direct_count += len(matches)
            for m in matches:
                context = text[max(0, m.start()-30):m.end()+30]
                detections.append({
                    "word": word,
                    "context": context,
                    "position": m.start()
                })

        ratio = direct_count / max(total_sentences, 1)

        return {
            "direct_count": direct_count,
            "total_sentences": total_sentences,
            "ratio": ratio,
            "is_healthy": ratio < 0.3,
            "detections": detections[:10]  # 상위 10개만
        }

    def generate_feedback(self, analysis: Dict) -> str:
        """피드백 생성"""
        if analysis["is_healthy"]:
            return ""

        lines = [f"[V55.3 Show Don't Tell 권장] (현재 비율: {analysis['ratio']:.1%}, 목표: <30%)"]
        lines.append("직접 서술을 묘사로 변환하세요:")

        for d in analysis["detections"][:5]:
            lines.append(f"  - '{d['word']}' → 신체 반응/행동으로 표현")

        lines.append("\n예시: '그는 화가 났다' → '그의 주먹이 하얗게 질렸다. 턱 근육이 굳어졌다.'")
        return "\n".join(lines)


# =============================================================================
# V55.4: Page-Turner Scorer (페이지터너 점수)
# =============================================================================

class PageTurnerScorer:
    """
    각 문단 끝의 '다음 읽고 싶은 정도' 측정

    측정 요소:
    - 미완결 상황 (궁금증)
    - 긴장 상태 유지
    - 질문 제기
    - 예상치 못한 전개 암시
    """

    # 페이지터너 긍정 패턴
    HOOK_PATTERNS = [
        r"그때[,.]",           # 전환점
        r"그 순간",            # 긴장
        r"하지만",             # 반전
        r"그러나",             # 반전
        r"문제는",             # 갈등
        r"\?$",                # 질문 종결
        r"\.\.\.+",            # 여운
        r"이었다\.$",          # 강조 종결
        r"아니었다\.$",        # 부정 강조
    ]

    # 페이지터너 부정 패턴 (읽기 멈춤 유발)
    STOP_PATTERNS = [
        r"그리하여.*완료되었다",    # 완결감
        r"모든 것이.*끝났다",       # 종결감
        r"평화로웠다\.$",           # 이완
        r"아무 일도 없었다",        # 무사건
    ]

    def score_paragraph(self, paragraph: str) -> Dict[str, Any]:
        """문단 페이지터너 점수"""
        score = 50  # 기본 점수
        hooks = []
        stops = []

        # 긍정 패턴
        for pattern in self.HOOK_PATTERNS:
            if re.search(pattern, paragraph):
                score += 10
                hooks.append(pattern)

        # 부정 패턴
        for pattern in self.STOP_PATTERNS:
            if re.search(pattern, paragraph):
                score -= 20
                stops.append(pattern)

        # 문단 길이 보정 (너무 길면 감점)
        if len(paragraph) > 500:
            score -= 10

        return {
            "score": min(100, max(0, score)),
            "hooks": hooks,
            "stops": stops
        }

    def analyze(self, text: str) -> Dict[str, Any]:
        """전체 텍스트 분석"""
        paragraphs = text.split('\n\n')
        scores = []
        low_score_positions = []

        for i, p in enumerate(paragraphs):
            if len(p.strip()) < 50:
                continue
            result = self.score_paragraph(p)
            scores.append(result["score"])
            if result["score"] < 40:
                low_score_positions.append({
                    "index": i,
                    "score": result["score"],
                    "preview": p[:50] + "..."
                })

        avg_score = sum(scores) / len(scores) if scores else 0

        return {
            "average_score": avg_score,
            "paragraph_count": len(scores),
            "low_score_count": len(low_score_positions),
            "low_score_positions": low_score_positions[:5]
        }

    def generate_feedback(self, analysis: Dict) -> str:
        """피드백 생성"""
        if analysis["average_score"] >= 60:
            return ""

        lines = [f"[V55.4 페이지터너 개선 필요] (평균: {analysis['average_score']:.0f}점, 목표: 60+)"]
        lines.append("다음 문단에 훅(hook) 추가 권장:")

        for pos in analysis["low_score_positions"][:3]:
            lines.append(f"  - 문단 {pos['index']+1}: {pos['preview']}")

        lines.append("\n훅 예시: 질문, 반전 암시, 긴장 유지, 미완결 상황")
        return "\n".join(lines)


# =============================================================================
# V55.5: Length Quality Gate (분량 품질 게이트)
# =============================================================================

class LengthQualityGate:
    """
    씬별 최소 분량 체크 + 이탈 위험 지점 탐지

    분량 기준:
    - 액션 씬: 800자
    - 대화 씬: 600자
    - 내면 씬: 500자
    - 전환 씬: 300자

    이탈 위험:
    - 설명 3문단 연속
    - 대화 없이 1000자
    - 긴장도 급락
    """

    SCENE_MIN_LENGTH = {
        "action": 800,
        "dialogue": 600,
        "emotional": 500,
        "transition": 300,
        "default": 500
    }

    def check_length(self, scenes: List[Dict]) -> List[Dict]:
        """씬별 분량 체크"""
        issues = []
        for scene in scenes:
            scene_type = scene.get("type", "default")
            min_len = self.SCENE_MIN_LENGTH.get(scene_type, 500)
            actual_len = len(scene.get("content", ""))

            if actual_len < min_len:
                issues.append({
                    "scene_id": scene.get("id"),
                    "scene_type": scene_type,
                    "actual": actual_len,
                    "required": min_len,
                    "deficit": min_len - actual_len
                })
        return issues

    def detect_dropout_risk(self, text: str) -> List[Dict]:
        """이탈 위험 지점 탐지"""
        risks = []

        # 대화 없이 긴 서술
        paragraphs = text.split('\n\n')
        consecutive_narration = 0
        narration_start = 0

        for i, p in enumerate(paragraphs):
            has_dialogue = '"' in p or '"' in p or '「' in p
            if not has_dialogue and len(p) > 200:
                if consecutive_narration == 0:
                    narration_start = i
                consecutive_narration += 1
            else:
                if consecutive_narration >= 3:
                    risks.append({
                        "type": "consecutive_narration",
                        "start_paragraph": narration_start,
                        "count": consecutive_narration,
                        "suggestion": "대화 또는 액션 삽입 권장"
                    })
                consecutive_narration = 0

        # 긴 설명 블록
        explanation_pattern = r'(?:이었다|였다|한다|이다)[.]\s*(?:그것은|이것은|그는|그녀는)'
        matches = list(re.finditer(explanation_pattern, text))
        if len(matches) > 5:
            risks.append({
                "type": "excessive_explanation",
                "count": len(matches),
                "suggestion": "설명을 행동/대화로 전환 권장"
            })

        return risks

    def generate_feedback(self, length_issues: List[Dict], dropout_risks: List[Dict]) -> str:
        """통합 피드백"""
        lines = []

        if length_issues:
            lines.append("[V55.5 분량 부족]")
            for issue in length_issues[:3]:
                lines.append(f"  - 씬 {issue['scene_id']} ({issue['scene_type']}): "
                           f"{issue['actual']}자 → {issue['required']}자 필요 (+{issue['deficit']})")

        if dropout_risks:
            lines.append("\n[V55.5 이탈 위험 지점]")
            for risk in dropout_risks[:3]:
                lines.append(f"  - {risk['type']}: {risk['suggestion']}")

        return "\n".join(lines) if lines else ""


# =============================================================================
# V55.6: Scene Density Enforcer (씬 밀도 강제기)
# =============================================================================

class SceneDensityEnforcer:
    """
    씬별 필수 요소 체크

    필수 요소:
    □ 공간 묘사 (최소 2문장)
    □ 인물 외양/동작 (최소 1문장)
    □ 감각 묘사 (최소 1개)
    □ 대화 시 리액션 비트
    """

    # 공간 묘사 키워드
    SPACE_KEYWORDS = [
        "방", "전각", "객잔", "거리", "산", "숲", "강", "하늘", "벽", "문",
        "바닥", "천장", "창", "탁자", "의자", "침대", "등불", "촛불"
    ]

    # 감각 키워드
    SENSORY_KEYWORDS = {
        "visual": ["보", "바라", "눈", "빛", "색", "어둠", "밝"],
        "auditory": ["소리", "들", "울", "고요", "시끄", "속삭"],
        "tactile": ["차갑", "뜨겁", "거칠", "부드", "딱딱", "촉감"],
        "olfactory": ["냄새", "향기", "악취", "향"],
        "gustatory": ["맛", "달", "쓴", "짠", "신"]
    }

    def analyze_scene(self, scene_text: str) -> Dict[str, Any]:
        """씬 밀도 분석"""
        result = {
            "has_space_description": False,
            "has_character_action": False,
            "sensory_count": 0,
            "sensory_types": [],
            "has_dialogue_beats": True,  # 기본값
            "missing_elements": []
        }

        # 공간 묘사 체크
        space_count = sum(1 for kw in self.SPACE_KEYWORDS if kw in scene_text)
        result["has_space_description"] = space_count >= 2
        if not result["has_space_description"]:
            result["missing_elements"].append("공간 묘사 (최소 2요소)")

        # 감각 묘사 체크
        for sense, keywords in self.SENSORY_KEYWORDS.items():
            if any(kw in scene_text for kw in keywords):
                result["sensory_count"] += 1
                result["sensory_types"].append(sense)
        if result["sensory_count"] == 0:
            result["missing_elements"].append("감각 묘사 (시각/청각/촉각 등)")

        # 대화 리액션 비트 체크
        dialogues = re.findall(r'[""「].*?[""」]', scene_text)
        if len(dialogues) >= 3:
            # 대화 사이에 비트가 있는지 체크
            between_dialogues = re.split(r'[""「].*?[""」]', scene_text)
            beats = [b for b in between_dialogues if len(b.strip()) > 30]
            if len(beats) < len(dialogues) // 2:
                result["has_dialogue_beats"] = False
                result["missing_elements"].append("대화 비트 (리액션, 행동 묘사)")

        return result

    def generate_feedback(self, scene_id: str, analysis: Dict) -> str:
        """피드백 생성"""
        if not analysis["missing_elements"]:
            return ""

        lines = [f"[V55.6 씬 {scene_id} 밀도 부족]"]
        for elem in analysis["missing_elements"]:
            lines.append(f"  □ {elem} 추가 필요")
        return "\n".join(lines)


# =============================================================================
# V55.7: Dialogue Beat Injector (대화 비트 삽입기)
# =============================================================================

class DialogueBeatInjector:
    """
    연속 대화에 액션/리액션 비트 삽입 권장
    + 환경 앵커 체크
    """

    def analyze_dialogues(self, text: str) -> Dict[str, Any]:
        """대화 연속성 분석"""
        # 대화 패턴 찾기
        dialogue_pattern = r'[""「].*?[""」]'
        parts = re.split(dialogue_pattern, text)
        dialogues = re.findall(dialogue_pattern, text)

        consecutive_count = 0
        max_consecutive = 0
        issues = []

        for i, between in enumerate(parts[1:], 1):  # 첫 부분 제외
            # 대화 사이가 너무 짧으면 연속 대화
            if len(between.strip()) < 20:
                consecutive_count += 1
            else:
                if consecutive_count >= 3:
                    issues.append({
                        "position": i,
                        "consecutive": consecutive_count,
                        "suggestion": "대화 비트 삽입 (행동, 표정, 환경 반응)"
                    })
                max_consecutive = max(max_consecutive, consecutive_count)
                consecutive_count = 0

        return {
            "total_dialogues": len(dialogues),
            "max_consecutive": max_consecutive,
            "issues": issues
        }

    def check_environment_anchors(self, text: str) -> Dict[str, Any]:
        """환경 앵커 체크"""
        # 장소 전환 탐지
        location_keywords = ["로 들어", "에 도착", "로 향", "를 나서", "에서 나"]
        transitions = []

        for kw in location_keywords:
            for m in re.finditer(kw, text):
                # 전환 후 100자 내에 환경 묘사가 있는지 체크
                after_text = text[m.end():m.end()+150]
                has_description = any(sk in after_text for sk in
                    SceneDensityEnforcer.SPACE_KEYWORDS)

                if not has_description:
                    transitions.append({
                        "position": m.start(),
                        "context": text[m.start()-20:m.end()+30],
                        "needs_description": True
                    })

        return {
            "transitions": len(transitions),
            "missing_descriptions": [t for t in transitions if t["needs_description"]]
        }

    def generate_feedback(self, dialogue_analysis: Dict, env_analysis: Dict) -> str:
        """통합 피드백"""
        lines = []

        if dialogue_analysis["issues"]:
            lines.append("[V55.7 대화 비트 삽입 필요]")
            for issue in dialogue_analysis["issues"][:3]:
                lines.append(f"  - 위치 {issue['position']}: {issue['consecutive']}개 연속 대화")
            lines.append("  → 행동, 표정, 주변 반응 등 비트 삽입")

        if env_analysis["missing_descriptions"]:
            lines.append("\n[V55.7 환경 앵커 필요]")
            for missing in env_analysis["missing_descriptions"][:3]:
                lines.append(f"  - 장소 전환 후 환경 묘사 추가: ...{missing['context'][:30]}...")

        return "\n".join(lines) if lines else ""


# =============================================================================
# 통합 Enhancer
# =============================================================================

@dataclass
class EnhancementResult:
    """향상 분석 결과"""
    cliche_count: int = 0
    subtext_ratio: float = 0.0
    page_turner_score: float = 0.0
    length_issues: int = 0
    density_issues: int = 0
    dialogue_issues: int = 0

    total_feedback: str = ""
    estimated_length_increase: str = ""
    priority_fixes: List[str] = field(default_factory=list)


class ManuscriptEnhancer:
    """
    [V55] 원고 품질 & 분량 통합 향상기

    사용:
        enhancer = ManuscriptEnhancer()
        result = enhancer.analyze(manuscript)
        print(result.total_feedback)
    """

    def __init__(self, genre: str = "wuxia"):
        self.genre = genre
        self.cliche_breaker = ClicheBreaker(genre)
        self.foreshadow_balancer = ForeshadowBalancer()
        self.subtext_expander = SubtextExpander()
        self.page_turner_scorer = PageTurnerScorer()
        self.length_gate = LengthQualityGate()
        self.density_enforcer = SceneDensityEnforcer()
        self.dialogue_injector = DialogueBeatInjector()

    def analyze(
        self,
        manuscript: str,
        scenes: List[Dict] = None,
        current_ep: int = 1
    ) -> EnhancementResult:
        """종합 분석"""
        result = EnhancementResult()
        feedbacks = []

        # V55.1: 클리셰 탐지
        cliches = self.cliche_breaker.detect(manuscript)
        result.cliche_count = len(cliches)
        if cliches:
            feedbacks.append(self.cliche_breaker.generate_feedback(cliches))
            result.priority_fixes.append("클리셰 표현 대체")

        # V55.2: 복선 체크 (외부에서 등록된 복선 기준)
        foreshadow_fb = self.foreshadow_balancer.generate_feedback(current_ep)
        if foreshadow_fb:
            feedbacks.append(foreshadow_fb)
            result.priority_fixes.append("미회수 복선 처리")

        # V55.3: 서브텍스트 분석
        subtext = self.subtext_expander.analyze(manuscript)
        result.subtext_ratio = subtext["ratio"]
        if not subtext["is_healthy"]:
            feedbacks.append(self.subtext_expander.generate_feedback(subtext))
            result.priority_fixes.append("Show don't Tell 적용")
            result.estimated_length_increase = "+20~30%"

        # V55.4: 페이지터너 점수
        page_turner = self.page_turner_scorer.analyze(manuscript)
        result.page_turner_score = page_turner["average_score"]
        if page_turner["average_score"] < 60:
            feedbacks.append(self.page_turner_scorer.generate_feedback(page_turner))
            result.priority_fixes.append("문단 훅 강화")

        # V55.5: 분량/이탈 위험
        if scenes:
            length_issues = self.length_gate.check_length(scenes)
            result.length_issues = len(length_issues)
        dropout_risks = self.length_gate.detect_dropout_risk(manuscript)
        if scenes or dropout_risks:
            fb = self.length_gate.generate_feedback(
                length_issues if scenes else [],
                dropout_risks
            )
            if fb:
                feedbacks.append(fb)
                result.priority_fixes.append("분량 보강")

        # V55.6: 씬 밀도
        density_fb_list = []
        if scenes:
            for scene in scenes:
                density = self.density_enforcer.analyze_scene(scene.get("content", ""))
                if density["missing_elements"]:
                    result.density_issues += 1
                    density_fb_list.append(
                        self.density_enforcer.generate_feedback(scene.get("id", "?"), density)
                    )
            if density_fb_list:
                feedbacks.extend(density_fb_list[:2])
                result.priority_fixes.append("씬 밀도 보강")

        # V55.7: 대화 비트 + 환경 앵커
        dialogue = self.dialogue_injector.analyze_dialogues(manuscript)
        env = self.dialogue_injector.check_environment_anchors(manuscript)
        result.dialogue_issues = len(dialogue["issues"]) + len(env["missing_descriptions"])
        beat_fb = self.dialogue_injector.generate_feedback(dialogue, env)
        if beat_fb:
            feedbacks.append(beat_fb)
            result.priority_fixes.append("대화 비트/환경 묘사 추가")

        # 종합 피드백
        result.total_feedback = "\n\n".join(f for f in feedbacks if f)

        return result

    def get_summary(self, result: EnhancementResult) -> str:
        """요약 리포트"""
        lines = [
            "=" * 50,
            "[V55 원고 향상 분석 요약]",
            "=" * 50,
            f"클리셰 발견: {result.cliche_count}개",
            f"직접 서술 비율: {result.subtext_ratio:.1%} {'✅' if result.subtext_ratio < 0.3 else '❌'}",
            f"페이지터너 점수: {result.page_turner_score:.0f}/100 {'✅' if result.page_turner_score >= 60 else '❌'}",
            f"분량 이슈: {result.length_issues}개",
            f"밀도 이슈: {result.density_issues}개",
            f"대화/환경 이슈: {result.dialogue_issues}개",
            "",
            f"예상 분량 증가: {result.estimated_length_increase or '분석 필요'}",
            "",
            "우선 수정 항목:",
        ]
        for i, fix in enumerate(result.priority_fixes[:5], 1):
            lines.append(f"  {i}. {fix}")

        return "\n".join(lines)


# 편의 함수
def create_enhancer(genre: str = "wuxia") -> ManuscriptEnhancer:
    """ManuscriptEnhancer 생성 헬퍼"""
    return ManuscriptEnhancer(genre)
