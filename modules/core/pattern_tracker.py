"""
[V48 Premium] 서사 관성 극복을 위한 고급 패턴 추적 시스템

기존 RepetitionGuard(3-gram)를 확장하여:
1. 플롯 패턴 추적 (도발→전투→승리 등)
2. 씬 타입 분포 추적 (Core/Buffer 비율)
3. 클리셰 키워드 빈도 추적
4. 문장 구조 패턴 추적 (시작어, 종결어)
5. 캐릭터 반응 패턴 추적

[V59] 장르별 패턴 확장 및 트렌드 분석 추가
"""

import logging
import re
from collections import Counter
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# [TF-54a] 반복 표현 추적 패턴
TRACKED_EXPRESSIONS: list[str] = [
    "사무실의 공기",
    "동공이 흔들",
    "입꼬리를 비틀",
    "폐부 깊숙이",
    r"단순한 .{1,15}(아니다|아니었다)",
    "거의 비명에 가까운",
    "강철 같은",
    "얼음처럼 차가운",
    "모든 것은 시나리오대로",
    "눈에 불꽃이 타올",
    "얼굴이 하얗게 질",
    r"사냥감|맹수|포식자",
    r"제국의 (왕|지휘석|기둥|영토)",
    "나는 알고 있었다",
    "그때였다",
    "텅 빈 사무실",
]

# [TF-54a] 은유 카테고리
METAPHOR_CATEGORIES: dict[str, list[str]] = {
    "군사": ["전쟁", "총알", "참호", "사령관", "전함", "함교", "무기", "탄창"],
    "사냥": ["사냥감", "맹수", "포식자", "먹잇감", "조준경", "미끼"],
    "제국": ["제국", "왕", "왕국", "기사", "신하", "왕좌"],
    "자연": ["바람", "파도", "폭풍", "태양", "달빛", "강물"],
    "음식": ["요리", "맛", "조리", "재료", "양념"],
    "건축": ["기둥", "주춧돌", "벽돌", "설계", "건물"],
    "게임": ["바둑", "장기", "체스", "카드", "판"],
}

# [TF-54a] 엔딩 패턴 분류 키워드
ENDING_CLASSIFIERS: dict[str, list[str]] = {
    "선언문": ["시작이었다", "서막이 올랐다", "전쟁이 시작", "사냥이 시작"],
    "수사의문문": ["것인가?", "것일까?", "될 것인가?"],
    "차가운미소": ["미소가 걸렸다", "미소를 지었다", "입꼬리를"],
    "조용한여운": [],
}


@dataclass
class PatternReport:
    """[TF-54a] PatternTracker가 집계한 직전 N화 패턴 요약."""

    expression_freq: dict[str, int] = field(default_factory=dict)
    ending_patterns: list[str] = field(default_factory=list)
    recent_ending_texts: list[str] = field(default_factory=list)  # [QI-1-A3] 직전 N화 엔딩 실제 문구
    npc_reaction_patterns: dict[str, list[str]] = field(default_factory=dict)
    metaphor_categories: dict[str, int] = field(default_factory=dict)
    emotion_diversity: float = 0.0
    protagonist_emotions: list[str] = field(default_factory=list)

    def to_summary_text(self, min_freq: int = 2) -> str:
        """LLM 주입용 요약 텍스트 생성."""
        lines: list[str] = []

        freq_items = [(expr, cnt) for expr, cnt in self.expression_freq.items() if cnt >= min_freq]
        if freq_items:
            freq_items.sort(key=lambda x: -x[1])
            lines.append("【반복 표현】 " + ", ".join(f"'{expr}'({cnt}회)" for expr, cnt in freq_items[:6]))

        if self.ending_patterns:
            ending_counter: dict[str, int] = {}
            for pattern in self.ending_patterns:
                ending_counter[pattern] = ending_counter.get(pattern, 0) + 1
            lines.append("【엔딩 패턴】 " + ", ".join(f"{k}:{v}회" for k, v in ending_counter.items()))

        # [QI-1-A3] 직전 엔딩 실제 문구 요약
        if self.recent_ending_texts:
            lines.append("【직전 엔딩】 " + " / ".join(f"'{t[-30:]}'" for t in self.recent_ending_texts[-3:]))

        heavy = [(cat, cnt) for cat, cnt in self.metaphor_categories.items() if cnt >= 3]
        unused = [cat for cat, cnt in self.metaphor_categories.items() if cnt == 0]
        if heavy:
            lines.append("【과사용 은유】 " + ", ".join(f"{cat}({cnt}회)" for cat, cnt in heavy))
        if unused:
            lines.append("【미사용 은유】 " + ", ".join(unused[:3]))

        if self.emotion_diversity < 0.4 and self.protagonist_emotions:
            dominant = max(set(self.protagonist_emotions), key=self.protagonist_emotions.count)
            lines.append(f"【감정 빈곤】 주인공 감정이 '{dominant}'에 편중 (다양성={self.emotion_diversity:.2f})")

        for npc, reactions in list(self.npc_reaction_patterns.items())[:2]:
            if isinstance(reactions, list) and len(reactions) >= 3:
                lines.append(f"【NPC 반응 고정】 {npc}: {' → '.join(reactions[-3:])}")

        return "\n".join(lines)[:500]


class PatternTracker:
    """
    서사 관성 극복을 위한 다층 패턴 추적 시스템

    Attributes:
        window_size: 분석할 이전 에피소드 수 (기본 10화)
        thresholds: 각 패턴 유형별 경고 임계값
    """

    # 무협 클리셰 키워드 (장르별 확장 가능)
    CLICHE_KEYWORDS = {
        "wuxia": [
            "살기",
            "기세",
            "경악",
            "전율",
            "경지",
            "내공",
            "진기",
            "눈빛이 빛났다",
            "입꼬리가 올라갔다",
            "차가운 미소",
            "순식간에",
            "찰나",
            "일순",
            "눈 깜짝할 사이",
            "감히",
            "어찌",
            "놀랍게도",
            "예상대로",
            "피가 솟구쳤다",
            "뼈가 으스러졌다",
            "고통에 몸부림쳤다",
        ],
        "hunter": [
            "각성",
            "스킬",
            "마나",
            "던전",
            "게이트",
            "몬스터",
            "레벨업",
            "스테이터스",
            "버프",
            "디버프",
            "눈앞이 하얘졌다",
            "메시지가 떴다",
            "시스템 알림",
        ],
        "investment": [
            "주가",
            "폭등",
            "폭락",
            "매수",
            "매도",
            "차트",
            "눈이 번쩍",
            "미소를 지었다",
            "심장이 뛰었다",
            "예상대로",
            "역시나",
            "드디어",
        ],
    }

    # 플롯 패턴 시퀀스 (감지 대상)
    PLOT_PATTERNS = [
        ("도발", "전투", "승리"),  # 가장 흔한 패턴
        ("위기", "각성", "역전"),  # 회귀물 패턴
        ("모욕", "복수", "통쾌"),  # 복수물 패턴
        ("수련", "돌파", "인정"),  # 성장물 패턴
        ("은혜", "보답", "동맹"),  # 관계물 패턴
        ("발견", "획득", "성장"),  # 파밍물 패턴
    ]

    # 문장 시작 패턴 (과다 사용 감지)
    SENTENCE_STARTERS = [
        "그는",
        "그녀는",
        "주인공은",
        "나는",
        "하지만",
        "그러나",
        "그리고",
        "그래서",
        "순간",
        "그때",
        "바로",
        "이윽고",
    ]

    def __init__(self, window_size: int = 10, genre: str = "wuxia"):
        """
        Args:
            window_size: 분석할 이전 에피소드 수
            genre: 장르 (wuxia/hunter/investment)
        """
        self.window_size = window_size
        self.genre = genre
        self.cliche_keywords = self.CLICHE_KEYWORDS.get(genre, self.CLICHE_KEYWORDS["wuxia"])

        # 패턴 저장소
        self.pattern_history = {
            "plot_sequences": [],  # 플롯 패턴 시퀀스
            "scene_types": {"Core": 0, "Buffer": 0, "Cliffhanger": 0, "Unknown": 0},  # 씬 타입 분포 (dict)
            "cliche_counts": Counter(),  # 클리셰 사용 빈도
            "starter_counts": Counter(),  # 문장 시작어 빈도
            "reaction_patterns": {},  # 캐릭터 반응 패턴 (dict)
        }

        # 임계값 설정
        self.thresholds = {
            "plot_repeat": 2,  # 동일 플롯 패턴 2회 이상 = 경고
            "cliche_ratio": 0.15,  # 클리셰 비율 15% 이상 = 경고
            "starter_dominance": 0.25,  # 특정 시작어 25% 이상 = 경고
            "core_imbalance": 0.7,  # Core 씬 70% 이상 = 경고
        }

    # [TF-54a] -----------------------------------------------------------------
    # 직전 N화 원고에서 반복 패턴 집계 (LLM 0회)

    def build_report(self, db, ep_num: int, lookback: int = 5) -> PatternReport:
        """DB에서 직전 lookback화 원고를 로드해 PatternReport 반환."""
        manuscripts = self._load_manuscripts(db, ep_num, lookback)
        if not manuscripts:
            return PatternReport()

        report = PatternReport()
        report.expression_freq = self._count_expressions(manuscripts)
        report.ending_patterns = self._classify_endings(manuscripts)
        # [QI-1-A3] 직전 N화 엔딩 실제 문구 수집 (마지막 50자)
        report.recent_ending_texts = [
            m[-50:].strip() for m in manuscripts if len(m) >= 20
        ]
        report.metaphor_categories = self._count_metaphors(manuscripts)

        combined = "\n".join(manuscripts)
        report.protagonist_emotions = self._extract_emotions(combined)
        unique = len(set(report.protagonist_emotions))
        total = len(report.protagonist_emotions)
        report.emotion_diversity = (unique / total) if total else 0.0

        return report

    def _load_manuscripts(self, db, ep_num: int, lookback: int) -> list[str]:
        if db is None:
            return []

        manuscripts: list[str] = []
        for ep in range(max(1, ep_num - lookback), ep_num):
            try:
                row = db.get_manuscript(ep)
                if isinstance(row, dict):
                    content = row.get("content", "")
                else:
                    content = str(row or "")
                if isinstance(content, str) and content.strip():
                    manuscripts.append(content)
            except Exception as e:
                logger.debug("[PatternTracker:TF-54] ep%d 로드 실패 (비치명): %s", ep, str(e)[:80])
        return manuscripts

    def _count_expressions(self, manuscripts: list[str]) -> dict[str, int]:
        combined = "\n".join(manuscripts)
        freq: dict[str, int] = {}
        for pattern in TRACKED_EXPRESSIONS:
            try:
                count = len(re.findall(pattern, combined))
                if count > 0:
                    freq[pattern] = count
            except re.error:
                continue
        return freq

    def _classify_endings(self, manuscripts: list[str]) -> list[str]:
        patterns: list[str] = []
        for manuscript in manuscripts:
            tail = manuscript[-200:] if len(manuscript) > 200 else manuscript
            classified = "조용한여운"
            for label, keywords in ENDING_CLASSIFIERS.items():
                if label == "조용한여운":
                    continue
                if any(keyword in tail for keyword in keywords):
                    classified = label
                    break
            patterns.append(classified)
        return patterns

    def _count_metaphors(self, manuscripts: list[str]) -> dict[str, int]:
        combined = "\n".join(manuscripts)
        return {cat: sum(combined.count(keyword) for keyword in keywords) for cat, keywords in METAPHOR_CATEGORIES.items()}

    def _extract_emotions(self, text: str) -> list[str]:
        """간단한 감정 키워드 추출 (regex/문자열 기반)."""
        emotion_patterns = [
            "차가운 만족",
            "차가운 분노",
            "씁쓸",
            "안도",
            "두려움",
            "기쁨",
            "슬픔",
            "허탈",
            "흥분",
            "죄책감",
        ]
        found: list[str] = []
        for emotion in emotion_patterns:
            count = text.count(emotion)
            found.extend([emotion] * count)
        return found

    def analyze_manuscripts(self, manuscripts: list[str], blueprints: list[dict] = None) -> dict:
        """
        여러 원고를 분석하여 패턴 히스토리 구축

        Args:
            manuscripts: 원고 텍스트 리스트 (최근 N화)
            blueprints: 블루프린트 리스트 (씬 타입 분석용)

        Returns:
            분석 결과 딕셔너리
        """
        if not manuscripts:
            return {"status": "no_data", "warnings": []}

        # [TF7-P2-04] 분석 전 pattern_history 초기화 (이전 분석 누적 방지)
        for key in self.pattern_history:
            if isinstance(self.pattern_history[key], Counter):
                self.pattern_history[key] = Counter()
            elif isinstance(self.pattern_history[key], list):
                self.pattern_history[key] = []
            elif isinstance(self.pattern_history[key], dict):
                self.pattern_history[key] = {}

        # 최근 window_size 화만 분석
        recent_ms = manuscripts[-self.window_size :]
        recent_bp = blueprints[-self.window_size :] if blueprints else []

        # 1. 클리셰 빈도 분석
        self._analyze_cliches(recent_ms)

        # 2. 문장 시작어 분석
        self._analyze_sentence_starters(recent_ms)

        # 3. 플롯 패턴 분석 (LLM 없이 키워드 기반)
        self._analyze_plot_patterns(recent_ms)

        # 4. 씬 타입 분포 분석 (블루프린트 기반)
        if recent_bp:
            self._analyze_scene_types(recent_bp)

        # 5. 캐릭터 반응 패턴 분석
        self._analyze_reaction_patterns(recent_ms)

        return self._generate_analysis_report()

    def _analyze_cliches(self, manuscripts: list[str]):
        """클리셰 키워드 빈도 분석"""
        combined = "\n".join(manuscripts)
        total_chars = len(combined)

        if total_chars == 0:
            return

        for keyword in self.cliche_keywords:
            count = combined.count(keyword)
            if count > 0:
                self.pattern_history["cliche_counts"][keyword] = count

    def _analyze_sentence_starters(self, manuscripts: list[str]):
        """문장 시작어 패턴 분석"""
        combined = "\n".join(manuscripts)

        # 문장 분리 (. ! ? 기준)
        sentences = re.split(r"[.!?]\s*", combined)
        total_sentences = len([s for s in sentences if s.strip()])

        if total_sentences == 0:
            return

        for starter in self.SENTENCE_STARTERS:
            count = sum(1 for s in sentences if s.strip().startswith(starter))
            if count > 0:
                self.pattern_history["starter_counts"][starter] = count

    def _analyze_plot_patterns(self, manuscripts: list[str]):
        """플롯 패턴 시퀀스 감지 (키워드 기반)"""
        detected_patterns = []

        for i, ms in enumerate(manuscripts):
            for pattern in self.PLOT_PATTERNS:
                # [TF7-P2-05] 순차 포인터 방식: 이전 매치 위치 이후에서 탐색
                positions = []
                pos = 0
                for keyword in pattern:
                    found = ms.find(keyword, pos)
                    if found == -1:
                        break
                    positions.append(found)
                    pos = found + len(keyword)

                # 모든 키워드가 순서대로 존재
                if len(positions) == len(pattern):
                    detected_patterns.append(
                        {"episode_index": i, "pattern": pattern, "pattern_name": "→".join(pattern)}
                    )

        self.pattern_history["plot_sequences"] = detected_patterns

    def _analyze_scene_types(self, blueprints: list[dict]):
        """씬 타입 분포 분석"""
        scene_types = {"Core": 0, "Buffer": 0, "Cliffhanger": 0, "Unknown": 0}

        for bp in blueprints:
            scene_breakdown = bp.get("scene_breakdown", {})
            if isinstance(scene_breakdown, dict):
                for scene_key, scene_content in scene_breakdown.items():
                    if isinstance(scene_content, str):
                        if "[Core]" in scene_content:
                            scene_types["Core"] += 1
                        elif "[Buffer]" in scene_content:
                            scene_types["Buffer"] += 1
                        elif "[Cliffhanger]" in scene_content:
                            scene_types["Cliffhanger"] += 1
                        else:
                            scene_types["Unknown"] += 1

        self.pattern_history["scene_types"] = scene_types

    def _analyze_reaction_patterns(self, manuscripts: list[str]):
        """캐릭터 반응 패턴 분석"""
        reaction_keywords = [
            "눈을 가늘게 떴다",
            "미간을 찌푸렸다",
            "고개를 끄덕였다",
            "한숨을 내쉬었다",
            "이를 악물었다",
            "주먹을 불끈 쥐었다",
            "눈빛이 차가워졌다",
            "입꼬리가 올라갔다",
            "표정이 굳었다",
        ]

        combined = "\n".join(manuscripts)
        reaction_counts = Counter()

        for reaction in reaction_keywords:
            count = combined.count(reaction)
            if count >= 2:  # 최소 2회 이상 사용된 것만
                reaction_counts[reaction] = count

        self.pattern_history["reaction_patterns"] = dict(reaction_counts.most_common(10))

    def _generate_analysis_report(self) -> dict:
        """분석 결과 리포트 생성"""
        warnings = []

        # 1. 클리셰 과다 사용 체크
        total_cliche = sum(self.pattern_history["cliche_counts"].values())
        top_cliches = self.pattern_history["cliche_counts"].most_common(5)
        if top_cliches:
            most_used = top_cliches[0]
            if most_used[1] >= self.window_size * 3:  # 화당 3회 이상
                warnings.append(
                    {
                        "type": "CLICHE_OVERUSE",
                        "severity": "HIGH",
                        "message": f"'{most_used[0]}' 표현 과다 사용 ({most_used[1]}회/{self.window_size}화)",
                        "suggestion": "대체 표현 사용 권장",
                    }
                )

        # 2. 문장 시작어 편중 체크
        total_starters = sum(self.pattern_history["starter_counts"].values())
        if total_starters > 0:
            top_starter = self.pattern_history["starter_counts"].most_common(1)
            if top_starter:
                ratio = top_starter[0][1] / total_starters
                if ratio >= self.thresholds["starter_dominance"]:
                    warnings.append(
                        {
                            "type": "STARTER_DOMINANCE",
                            "severity": "MEDIUM",
                            "message": f"'{top_starter[0][0]}'로 시작하는 문장 비율 과다 ({ratio:.1%})",
                            "suggestion": "다양한 문장 시작 패턴 사용",
                        }
                    )

        # 3. 플롯 패턴 반복 체크
        plot_counter = Counter(p["pattern_name"] for p in self.pattern_history["plot_sequences"])
        for pattern_name, count in plot_counter.items():
            if count >= self.thresholds["plot_repeat"]:
                warnings.append(
                    {
                        "type": "PLOT_REPEAT",
                        "severity": "HIGH",
                        "message": f"'{pattern_name}' 플롯 패턴 {count}회 반복",
                        "suggestion": "다른 전개 방식 시도 필요",
                    }
                )

        # 4. 씬 타입 불균형 체크
        scene_types = self.pattern_history["scene_types"]
        total_scenes = sum(scene_types.values())
        if total_scenes > 0:
            core_ratio = scene_types.get("Core", 0) / total_scenes
            if core_ratio >= self.thresholds["core_imbalance"]:
                warnings.append(
                    {
                        "type": "CORE_IMBALANCE",
                        "severity": "MEDIUM",
                        "message": f"Core 씬 비율 과다 ({core_ratio:.1%})",
                        "suggestion": "Buffer 씬 추가로 완급 조절",
                    }
                )

        # 5. 캐릭터 반응 패턴 반복 체크
        reaction_patterns = self.pattern_history["reaction_patterns"]
        for reaction, count in reaction_patterns.items():
            if count >= self.window_size:  # 화당 1회 이상
                warnings.append(
                    {
                        "type": "REACTION_REPEAT",
                        "severity": "LOW",
                        "message": f"'{reaction}' 반응 과다 사용 ({count}회)",
                        "suggestion": "다양한 신체 반응 묘사 사용",
                    }
                )

        return {
            "status": "analyzed",
            "window_size": self.window_size,
            "warnings": warnings,
            "high_severity_count": sum(1 for w in warnings if w["severity"] == "HIGH"),
            "statistics": {
                "total_cliches": total_cliche,
                "top_cliches": top_cliches[:5],
                "plot_patterns_detected": len(self.pattern_history["plot_sequences"]),
                "scene_distribution": scene_types,
                "top_reactions": list(reaction_patterns.items())[:5],
            },
        }

    def should_activate_diversity_sampling(self, report: dict = None) -> tuple[bool, str]:
        """
        Diversity Sampling 활성화 여부 판단

        Returns:
            (활성화 여부, 이유)
        """
        if report is None:
            report = self._generate_analysis_report()

        high_count = report.get("high_severity_count", 0)

        if high_count >= 2:
            return True, f"HIGH 심각도 경고 {high_count}개 감지 - Diversity Sampling 필수"
        elif high_count == 1:
            return True, "HIGH 심각도 경고 감지 - Diversity Sampling 권장"
        else:
            return False, "패턴 반복 수준 양호 - 기본 생성 유지"

    def generate_writer_injection(self, report: dict = None) -> str:
        """
        Writer 프롬프트에 주입할 경고 문구 생성

        Returns:
            프롬프트 주입 문자열
        """
        if report is None:
            report = self._generate_analysis_report()

        warnings = report.get("warnings", [])
        if not warnings:
            return ""

        # 심각도별 분류
        high_warnings = [w for w in warnings if w["severity"] == "HIGH"]
        medium_warnings = [w for w in warnings if w["severity"] == "MEDIUM"]

        injection = f"""
[V48 PATTERN TRACKER: 서사 관성 경고]
최근 {self.window_size}화 분석 결과, 아래 패턴 반복이 감지되었습니다.
이번 원고에서는 반드시 다른 방식을 사용하십시오.

"""

        if high_warnings:
            injection += "[HIGH 심각도 - 반드시 회피]\n"
            for w in high_warnings[:3]:
                injection += f"- {w['message']}\n  → {w['suggestion']}\n"
            injection += "\n"

        if medium_warnings:
            injection += "[MEDIUM 심각도 - 권장 회피]\n"
            for w in medium_warnings[:3]:
                injection += f"- {w['message']}\n  → {w['suggestion']}\n"

        # 구체적 대체 표현 제안
        top_cliches = report.get("statistics", {}).get("top_cliches", [])
        if top_cliches:
            injection += "\n[과다 사용 표현 대체 제안]\n"
            alternatives = self._suggest_alternatives(top_cliches[:3])
            for original, alts in alternatives.items():
                injection += f"- '{original}' 대신 → {', '.join(alts)}\n"

        return injection

    def _suggest_alternatives(self, top_cliches: list[tuple[str, int]]) -> dict[str, list[str]]:
        """클리셰 표현 대체안 제안"""
        alternatives_db = {
            "살기": ["적의", "해의", "흉한 기운", "음습한 기세"],
            "기세": ["위압감", "분위기", "존재감", "압도적 느낌"],
            "경악": ["놀람", "당혹", "충격", "어안이 벙벙"],
            "순식간에": ["눈 깜짝할 새", "찰나에", "일순간", "전광석화처럼"],
            "눈빛이 빛났다": ["눈동자가 반짝였다", "시선이 예리해졌다", "눈가에 힘이 들어갔다"],
            "입꼬리가 올라갔다": ["미소를 머금었다", "씩 웃었다", "희미한 미소가 번졌다"],
            "차가운 미소": ["냉소", "비웃음", "서늘한 웃음", "냉담한 표정"],
            "고개를 끄덕였다": ["수긍했다", "동의를 표했다", "묵묵히 인정했다"],
            "이를 악물었다": ["치아를 꽉 깨물었다", "분을 삼켰다", "울분을 참았다"],
        }

        result = {}
        for cliche, count in top_cliches:
            if cliche in alternatives_db:
                result[cliche] = alternatives_db[cliche]
            else:
                # 기본 대체안
                result[cliche] = ["(다른 표현으로 변경)", "(동의어 활용)", "(문장 재구성)"]

        return result

    def save_to_db(self, db_manager) -> bool:
        """패턴 히스토리를 DB에 저장"""
        try:
            data = {
                "window_size": self.window_size,
                "genre": self.genre,
                "pattern_history": {
                    "cliche_counts": dict(self.pattern_history["cliche_counts"]),
                    "starter_counts": dict(self.pattern_history["starter_counts"]),
                    "plot_sequences": self.pattern_history["plot_sequences"],
                    "scene_types": self.pattern_history["scene_types"],
                    "reaction_patterns": self.pattern_history["reaction_patterns"],
                },
            }
            db_manager.save_anchor("pattern_tracker", data)  # [V70] update_anchor → save_anchor
            return True
        except Exception as e:
            logging.warning(f"[PatternTracker] DB 저장 실패: {e}")
            return False

    def load_from_db(self, db_manager) -> bool:
        """DB에서 패턴 히스토리 로드"""
        try:
            data = db_manager.load_anchor("pattern_tracker")  # [V70] get_anchor → load_anchor
            if data:
                self.window_size = data.get("window_size", 10)
                self.genre = data.get("genre", "wuxia")
                history = data.get("pattern_history", {})
                self.pattern_history["cliche_counts"] = Counter(history.get("cliche_counts", {}))
                self.pattern_history["starter_counts"] = Counter(history.get("starter_counts", {}))
                self.pattern_history["plot_sequences"] = history.get("plot_sequences", [])
                self.pattern_history["scene_types"] = history.get("scene_types", {})
                self.pattern_history["reaction_patterns"] = history.get("reaction_patterns", {})
                return True
            return False
        except Exception as e:
            logging.warning(f"[PatternTracker] DB 로드 실패: {e}")
            return False

    # ========================================================================
    # [V59] 장르별 패턴 확장
    # ========================================================================

    # [V59] 장르별 확장 플롯 패턴
    GENRE_PLOT_PATTERNS = {
        "wuxia": {
            "revenge": [
                ("원수", "추적", "대결", "복수"),
                ("스승", "사망", "수련", "복수"),
                ("가문", "멸문", "은거", "재기"),
            ],
            "growth": [
                ("수련", "고난", "깨달음", "돌파"),
                ("비급", "발견", "수련", "체득"),
                ("사부", "전수", "연마", "완성"),
            ],
            "jianghu": [
                ("모함", "위기", "동맹", "반격"),
                ("비무", "패배", "수련", "재대결"),
                ("음모", "발각", "탈출", "역전"),
            ],
            "romance": [
                ("만남", "오해", "위기", "화해"),
                ("구출", "감사", "동행", "정"),
            ],
        },
        "hunter": {
            "dungeon": [
                ("진입", "탐색", "보스", "클리어"),
                ("함정", "위기", "스킬", "탈출"),
                ("레이드", "협력", "전투", "보상"),
            ],
            "awakening": [
                ("각성", "훈련", "테스트", "등급"),
                ("재각성", "고통", "진화", "강화"),
                ("잠재력", "발현", "폭주", "제어"),
            ],
            "guild": [
                ("가입", "테스트", "인정", "활동"),
                ("갈등", "경쟁", "협력", "성장"),
                ("배신", "위기", "탈퇴", "재기"),
            ],
        },
        "investment": {
            "trade": [
                ("분석", "매수", "변동", "익절"),
                ("하락", "공포", "인내", "반등"),
                ("정보", "확신", "배팅", "대박"),
            ],
            "crisis": [
                ("폭락", "손절", "반성", "재기"),
                ("파산", "도피", "재기", "복귀"),
                ("공황", "기회", "매수", "수익"),
            ],
            "insider": [
                ("정보", "분석", "확인", "선매수"),
                ("소문", "조사", "진실", "활용"),
            ],
        },
        "actor": {
            "audition": [
                ("오디션", "준비", "경쟁", "결과"),
                ("캐스팅", "면접", "테스트", "합격"),
                ("제안", "고민", "수락", "촬영"),
            ],
            "career": [
                ("무명", "기회", "주목", "도약"),
                ("슬럼프", "각오", "재도전", "부활"),
                ("성공", "교만", "실패", "성장"),
            ],
            "scandal": [
                ("루머", "확산", "대응", "반전"),
                ("노출", "위기", "해명", "회복"),
            ],
            "industry": [
                ("소속사", "갈등", "협상", "결과"),
                ("라이벌", "경쟁", "대결", "인정"),
            ],
        },
    }

    # [V59] 장르별 감정 패턴
    GENRE_EMOTION_PATTERNS = {
        "wuxia": {
            "positive": ["통쾌", "희열", "자부심", "경외", "감동"],
            "negative": ["분노", "좌절", "굴욕", "비통", "복수심"],
            "neutral": ["냉정", "관조", "의연", "무심"],
        },
        "hunter": {
            "positive": ["성취감", "쾌감", "희열", "안도", "자신감"],
            "negative": ["공포", "절망", "좌절", "분노", "후회"],
            "neutral": ["긴장", "집중", "계산", "판단"],
        },
        "investment": {
            "positive": ["희열", "자신감", "만족", "안도", "흥분"],
            "negative": ["공포", "탐욕", "후회", "좌절", "분노"],
            "neutral": ["냉정", "분석", "관망", "인내"],
        },
        "actor": {
            "positive": ["열정", "감동", "희열", "자부심", "성취감"],
            "negative": ["불안", "질투", "좌절", "슬럼프", "자괴감"],
            "neutral": ["긴장", "집중", "관찰", "몰입"],
        },
    }

    def analyze_genre_patterns_v59(self, manuscripts: list[str]) -> dict:
        """[V59] 장르별 확장 패턴 분석 — [TF-5-05] 외부 호출 없음, dead code 후보.

        Args:
            manuscripts: 원고 리스트

        Returns:
            장르 특화 패턴 분석 결과
        """
        if not manuscripts:
            return {"status": "no_data"}

        genre_patterns = self.GENRE_PLOT_PATTERNS.get(self.genre, {})
        emotion_patterns = self.GENRE_EMOTION_PATTERNS.get(self.genre, {})

        combined = "\n".join(manuscripts[-self.window_size :])

        result = {"plot_patterns": {}, "emotion_distribution": {}, "genre_health": "unknown", "recommendations": []}

        # 플롯 패턴 매칭
        for category, patterns in genre_patterns.items():
            category_matches = []
            for pattern in patterns:
                if self._check_pattern_sequence(combined, pattern):
                    category_matches.append("→".join(pattern))

            if category_matches:
                result["plot_patterns"][category] = {"count": len(category_matches), "patterns": category_matches}

        # 감정 분포 분석
        for emotion_type, keywords in emotion_patterns.items():
            count = sum(combined.count(kw) for kw in keywords)
            result["emotion_distribution"][emotion_type] = count

        # 장르 건강도 평가
        result["genre_health"] = self._evaluate_genre_health(result, self.genre)

        # 권장 사항 생성
        result["recommendations"] = self._generate_genre_recommendations(result, self.genre)

        return result

    def _check_pattern_sequence(self, text: str, pattern: tuple) -> bool:
        """패턴 시퀀스가 순서대로 등장하는지 확인
        [TF7-P2-05] 순차 포인터 방식으로 교체 (첫 매치에만 의존하는 오탐 방지)
        """
        pos = 0
        for keyword in pattern:
            found = text.find(keyword, pos)
            if found == -1:
                return False
            pos = found + len(keyword)

        return True

    def _evaluate_genre_health(self, analysis: dict, genre: str) -> str:
        """장르 건강도 평가"""
        plot_count = sum(len(p.get("patterns", [])) for p in analysis["plot_patterns"].values())
        emotion_dist = analysis["emotion_distribution"]

        # 감정 균형 체크
        total_emotion = sum(emotion_dist.values())
        if total_emotion == 0:
            return "poor"

        negative_ratio = emotion_dist.get("negative", 0) / total_emotion

        # 장르별 기준
        if genre == "wuxia":
            # 무협은 적절한 갈등(부정 감정)이 필요
            if plot_count >= 3 and 0.3 <= negative_ratio <= 0.5:
                return "excellent"
            elif plot_count >= 2 and 0.2 <= negative_ratio <= 0.6:
                return "good"
            elif plot_count >= 1:
                return "fair"
        elif genre == "hunter":
            # 헌터는 성장과 긴장이 중요
            if plot_count >= 3 and 0.25 <= negative_ratio <= 0.45:
                return "excellent"
            elif plot_count >= 2:
                return "good"
        elif genre == "investment":
            # 투자는 감정 기복이 핵심
            if plot_count >= 2 and 0.3 <= negative_ratio <= 0.5:
                return "excellent"
            elif plot_count >= 1 and 0.2 <= negative_ratio <= 0.6:
                return "good"

        return "fair"

    def _generate_genre_recommendations(self, analysis: dict, genre: str) -> list[str]:
        """장르별 권장 사항 생성"""
        recommendations = []
        emotion_dist = analysis["emotion_distribution"]

        if genre == "wuxia":
            if emotion_dist.get("negative", 0) < emotion_dist.get("positive", 0) * 0.5:
                recommendations.append("갈등/위기 요소를 추가하여 긴장감 강화 필요")
            if not analysis["plot_patterns"].get("growth"):
                recommendations.append("성장 요소(수련, 깨달음) 추가 고려")

        elif genre == "hunter":
            if not analysis["plot_patterns"].get("dungeon"):
                recommendations.append("던전/전투 씬 추가 고려")
            if not analysis["plot_patterns"].get("awakening"):
                recommendations.append("각성/성장 이벤트 배치 고려")

        elif genre == "investment":
            if emotion_dist.get("neutral", 0) > sum(emotion_dist.values()) * 0.5:
                recommendations.append("감정적 기복 추가 (탐욕/공포 묘사)")
            if not analysis["plot_patterns"].get("trade"):
                recommendations.append("거래/투자 씬 추가 필요")

        return recommendations[:5]

    # ========================================================================
    # [V59] 트렌드 분석 시스템
    # ========================================================================

    def analyze_trend_v59(self, manuscripts: list[str], window_splits: int = 3) -> dict:
        """[V59] 패턴 트렌드 분석 — [TF-5-05] 외부 호출 없음, dead code 후보.

        시간에 따른 패턴 변화 추적.

        Args:
            manuscripts: 전체 원고 리스트
            window_splits: 분석 구간 수 (기본 3: 초반/중반/최근)

        Returns:
            트렌드 분석 결과
        """
        if window_splits <= 0:
            return {"status": "invalid_window_splits"}

        if len(manuscripts) < window_splits * 2:
            return {"status": "insufficient_data", "min_required": window_splits * 2}

        # 구간별 분할
        split_size = len(manuscripts) // window_splits
        windows = []
        for i in range(window_splits):
            start = i * split_size
            end = start + split_size if i < window_splits - 1 else len(manuscripts)
            windows.append(manuscripts[start:end])

        # 구간별 분석
        window_analyses = []
        for i, window in enumerate(windows):
            analysis = {
                "window_index": i,
                "window_name": ["초반", "중반", "최근"][min(i, 2)],
                "episode_range": f"{i * split_size + 1}~{(i + 1) * split_size if i < window_splits - 1 else len(manuscripts)}화",
                "cliche_density": self._calculate_cliche_density(window),
                "diversity_score": self._calculate_diversity_score(window),
                "emotion_balance": self._calculate_emotion_balance(window),
            }
            window_analyses.append(analysis)

        # 트렌드 계산
        trends = self._calculate_trends(window_analyses)

        # 트렌드 해석
        interpretations = self._interpret_trends(trends)

        return {
            "status": "analyzed",
            "total_episodes": len(manuscripts),
            "window_count": window_splits,
            "windows": window_analyses,
            "trends": trends,
            "interpretations": interpretations,
            "overall_health": self._assess_overall_health(trends),
        }

    def _calculate_cliche_density(self, manuscripts: list[str]) -> float:
        """클리셰 밀도 계산 (1000자당 클리셰 수)"""
        combined = "\n".join(manuscripts)
        total_chars = len(combined)

        if total_chars == 0:
            return 0

        cliche_count = sum(combined.count(kw) for kw in self.cliche_keywords)
        return round(cliche_count / (total_chars / 1000), 2)

    def _calculate_diversity_score(self, manuscripts: list[str]) -> float:
        """다양성 점수 계산 (0-100)"""
        combined = "\n".join(manuscripts)

        if not combined:
            return 0

        # 문장 시작 다양성
        sentences = re.split(r"[.!?]\s*", combined)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) < 5:
            return 50

        starters = [s[:3] for s in sentences if len(s) >= 3]
        unique_ratio = len(set(starters)) / len(starters) if starters else 0

        # 어휘 다양성 (간단 TTR)
        words = re.findall(r"[가-힣]{2,}", combined)
        word_ttr = len(set(words)) / len(words) if words else 0

        # 종합 점수
        score = unique_ratio * 50 + word_ttr * 50
        return round(score, 1)

    def _calculate_emotion_balance(self, manuscripts: list[str]) -> dict:
        """감정 균형 계산"""
        combined = "\n".join(manuscripts)
        emotion_patterns = self.GENRE_EMOTION_PATTERNS.get(self.genre, {})

        counts = {}
        for emotion_type, keywords in emotion_patterns.items():
            counts[emotion_type] = sum(combined.count(kw) for kw in keywords)

        total = sum(counts.values())
        if total == 0:
            return {"positive": 0.33, "negative": 0.33, "neutral": 0.34}

        return {emotion_type: round(count / total, 2) for emotion_type, count in counts.items()}

    def _calculate_trends(self, window_analyses: list[dict]) -> dict:
        """구간별 분석에서 트렌드 추출"""
        if len(window_analyses) < 2:
            return {}

        first = window_analyses[0]
        last = window_analyses[-1]

        return {
            "cliche_trend": {
                "direction": "increasing" if last["cliche_density"] > first["cliche_density"] else "decreasing",
                "change": round(last["cliche_density"] - first["cliche_density"], 2),
            },
            "diversity_trend": {
                "direction": "improving" if last["diversity_score"] > first["diversity_score"] else "declining",
                "change": round(last["diversity_score"] - first["diversity_score"], 1),
            },
            "emotion_shift": {
                "from": (
                    max(first["emotion_balance"], key=first["emotion_balance"].get)
                    if first.get("emotion_balance")
                    else "neutral"
                ),
                "to": (
                    max(last["emotion_balance"], key=last["emotion_balance"].get)
                    if last.get("emotion_balance")
                    else "neutral"
                ),
            },
        }

    def _interpret_trends(self, trends: dict) -> list[str]:
        """트렌드 해석"""
        interpretations = []

        cliche = trends.get("cliche_trend", {})
        if cliche.get("direction") == "increasing" and cliche.get("change", 0) > 0.5:
            interpretations.append("⚠️ 클리셰 사용이 증가하고 있습니다. 표현 다양화 필요.")
        elif cliche.get("direction") == "decreasing":
            interpretations.append("✅ 클리셰 사용이 감소하고 있습니다. 좋은 추세입니다.")

        diversity = trends.get("diversity_trend", {})
        if diversity.get("direction") == "declining" and diversity.get("change", 0) < -5:
            interpretations.append("⚠️ 표현 다양성이 감소하고 있습니다. 어휘 확장 필요.")
        elif diversity.get("direction") == "improving":
            interpretations.append("✅ 표현 다양성이 개선되고 있습니다.")

        emotion = trends.get("emotion_shift", {})
        if emotion.get("from") != emotion.get("to"):
            interpretations.append(f"📊 감정 톤 변화: {emotion.get('from', '?')} → {emotion.get('to', '?')}")

        return interpretations

    def _assess_overall_health(self, trends: dict) -> str:
        """전체 건강도 평가"""
        issues = 0

        cliche = trends.get("cliche_trend", {})
        if cliche.get("direction") == "increasing":
            issues += 1

        diversity = trends.get("diversity_trend", {})
        if diversity.get("direction") == "declining":
            issues += 1

        if issues == 0:
            return "excellent"
        elif issues == 1:
            return "good"
        else:
            return "needs_improvement"

    def generate_trend_report_v59(self, trend_result: dict) -> str:
        """[V59] 트렌드 분석 결과를 읽기 좋은 형태로 포맷 — [TF-5-05] 외부 호출 없음, dead code 후보.

        Args:
            trend_result: analyze_trend_v59() 결과

        Returns:
            포맷팅된 리포트 텍스트
        """
        if trend_result.get("status") == "insufficient_data":
            return f"📊 트렌드 분석에 최소 {trend_result.get('min_required', 6)}화 이상 필요합니다."

        lines = [
            f"\n{'=' * 50}",
            "📊 [V59] 패턴 트렌드 분석 리포트",
            f"{'=' * 50}",
            f"총 분석 화수: {trend_result.get('total_episodes', 0)}화",
            f"전체 건강도: {trend_result.get('overall_health', '?')}\n",
        ]

        # 구간별 요약
        windows = trend_result.get("windows", [])
        if windows:
            lines.append("📈 구간별 분석:")
            for w in windows:
                lines.append(f"  [{w['window_name']}] {w['episode_range']}")
                lines.append(f"    - 클리셰 밀도: {w['cliche_density']}/1000자")
                lines.append(f"    - 다양성 점수: {w['diversity_score']}/100")

        # 트렌드
        trends = trend_result.get("trends", {})
        if trends:
            lines.append("\n📉 변화 추세:")
            cliche = trends.get("cliche_trend", {})
            lines.append(f"  - 클리셰: {cliche.get('direction', '?')} ({cliche.get('change', 0):+.2f})")
            diversity = trends.get("diversity_trend", {})
            lines.append(f"  - 다양성: {diversity.get('direction', '?')} ({diversity.get('change', 0):+.1f}점)")

        # 해석
        interpretations = trend_result.get("interpretations", [])
        if interpretations:
            lines.append("\n💡 분석 결과:")
            for interp in interpretations:
                lines.append(f"  {interp}")

        lines.append(f"{'=' * 50}\n")

        return "\n".join(lines)
