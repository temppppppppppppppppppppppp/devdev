"""
[V58] Character Voice Profiler

캐릭터 음성/어투 프로파일링 시스템:
- NPC별 어투/성격 프로파일 DB
- 대사 생성 시 프로파일 주입
- 어투 일탈 자동 감지
- 캐릭터 일관성 검증

지원 속성:
- 말투 (formal/informal/archaic)
- 성격 (aggressive/calm/humorous 등)
- 특징적 표현 (말버릇, 입버릇)
- 관계별 호칭 패턴
"""

import logging
import re
from collections import Counter
from dataclasses import asdict, dataclass, field, fields
from typing import Any


@dataclass
class VoiceProfile:
    """캐릭터 음성 프로파일"""

    character_name: str
    speech_level: str = "formal"  # formal/informal/archaic
    personality: str = "neutral"  # aggressive/calm/humorous/cold/warm
    speech_speed: str = "normal"  # fast/normal/slow (장문/단문 성향)
    catchphrases: list[str] = field(default_factory=list)  # 입버릇
    forbidden_words: list[str] = field(default_factory=list)  # 사용 안 하는 표현
    address_patterns: dict[str, str] = field(default_factory=dict)  # 대상별 호칭
    sample_dialogues: list[str] = field(default_factory=list)  # 예시 대사
    emotion_expressions: dict[str, list[str]] = field(default_factory=dict)  # 감정별 표현

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "VoiceProfile":
        """[V61.5] 미지 키 무시"""
        valid_keys = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_keys})


class CharacterVoiceProfiler:
    """
    [V58] 캐릭터 음성 프로파일러

    기능:
    1. 프로파일 생성/관리
    2. 대사에서 자동 프로파일 추출
    3. 대사 일관성 검증
    4. Writer 프롬프트 주입용 가이드 생성
    """

    # 말투 패턴
    SPEECH_LEVEL_PATTERNS = {
        "formal": {
            "markers": [r"습니다", r"입니까", r"십시오", r"하십시오"],
            "endings": ["습니다", "입니다", "합니다", "됩니다"],
        },
        "informal": {
            "markers": [r"어\b", r"야\b", r"지\b", r"네\b", r"군\b"],
            "endings": ["어", "야", "지", "네", "는데"],
        },
        "archaic": {  # 무협 고어체
            "markers": [r"하오", r"하시오", r"로다", r"이니라", r"하겠네"],
            "endings": ["하오", "하시오", "로다", "이니라", "하겠네", "일세"],
        },
    }

    # [QI-1-C1] 성격별 표현 패턴 — 검출용 참고 예시
    # 캐릭터의 상황·관계·감정에 따라 LLM이 자유롭게 변형합니다.
    # 아래 키워드는 원고에서 성격 경향을 추론하기 위한 신호일 뿐,
    # 프롬프트에 직접 주입되지 않습니다.
    PERSONALITY_PATTERNS = {
        "aggressive": {
            "keywords": ["죽여", "박살", "꺼져", "닥쳐", "빌어먹을", "망할", "찢어", "때려", "부숴"],
            "punctuation": ["!", "!!"],
            "sentence_length": "short",
        },
        "calm": {
            "keywords": ["그렇군", "알겠네", "생각해보면", "아마도", "천천히", "살펴보지"],
            "punctuation": [".", "..."],
            "sentence_length": "medium",
        },
        "humorous": {
            "keywords": ["하하", "농담", "재밌", "웃기", "장난", "별걸"],
            "punctuation": ["~", "ㅋ", "ㅎ"],
            "sentence_length": "varied",
        },
        "cold": {
            "keywords": ["상관없", "필요없", "그만", "됐", "알아서", "끝났"],
            "punctuation": ["."],
            "sentence_length": "short",
        },
        "warm": {
            "keywords": ["걱정", "괜찮", "고마워", "미안", "힘내", "함께"],
            "punctuation": [".", "..."],
            "sentence_length": "medium",
        },
    }

    def __init__(self, db_manager=None, genre: str = "wuxia"):
        """
        Args:
            db_manager: DBManager 인스턴스 (영속성)
            genre: 장르
        """
        self.db = db_manager
        self.genre = genre
        self.profiles: dict[str, VoiceProfile] = {}
        self._load_from_db()

    def _load_from_db(self) -> None:
        """DB에서 프로파일 로드"""
        if self.db is None:
            return

        try:
            data = self.db.load_anchor("character_voice_profiles")
            if data and isinstance(data, dict):
                for name, profile_data in data.items():
                    self.profiles[name] = VoiceProfile.from_dict(profile_data)
                logging.info(f"[VoiceProfiler] {len(self.profiles)}개 프로파일 로드 완료")
        except Exception as e:
            logging.warning(f"[VoiceProfiler] 로드 실패: {e}")

    def _save_to_db(self) -> None:
        """DB에 프로파일 저장"""
        if self.db is None:
            return

        try:
            data = {name: p.to_dict() for name, p in self.profiles.items()}
            self.db.save_anchor("character_voice_profiles", data)
        except Exception as e:
            logging.warning(f"[VoiceProfiler] 저장 실패: {e}")

    def create_profile(
        self,
        character_name: str,
        speech_level: str = "formal",
        personality: str = "neutral",
        catchphrases: list[str] = None,
        sample_dialogues: list[str] = None,
        **kwargs,
    ) -> VoiceProfile:
        """
        캐릭터 프로파일 생성

        Args:
            character_name: 캐릭터 이름
            speech_level: 말투 레벨 (formal/informal/archaic)
            personality: 성격 유형
            catchphrases: 입버릇 목록
            sample_dialogues: 예시 대사
            **kwargs: 추가 속성

        Returns:
            생성된 VoiceProfile
        """
        profile = VoiceProfile(
            character_name=character_name,
            speech_level=speech_level,
            personality=personality,
            catchphrases=catchphrases or [],
            sample_dialogues=sample_dialogues or [],
            **kwargs,
        )

        self.profiles[character_name] = profile
        self._save_to_db()

        logging.info(f"[VoiceProfiler] '{character_name}' 프로파일 생성 완료")
        return profile

    def extract_profile_from_text(self, character_name: str, text: str, min_dialogues: int = 5) -> VoiceProfile | None:
        """
        텍스트에서 캐릭터 프로파일 자동 추출

        Args:
            character_name: 캐릭터 이름
            text: 분석할 텍스트
            min_dialogues: 최소 필요 대사 수

        Returns:
            추출된 VoiceProfile 또는 None
        """
        # 해당 캐릭터의 대사 추출
        dialogues = self._extract_character_dialogues(character_name, text)

        if len(dialogues) < min_dialogues:
            logging.info(f"[VoiceProfiler] '{character_name}' 대사 부족 ({len(dialogues)}/{min_dialogues})")
            return None

        # 말투 분석
        speech_level = self._analyze_speech_level(dialogues)

        # 성격 분석
        personality = self._analyze_personality(dialogues)

        # 입버릇 추출
        catchphrases = self._extract_catchphrases(dialogues)

        # 문장 길이 성향
        avg_length = sum(len(d) for d in dialogues) / len(dialogues)
        speech_speed = "fast" if avg_length < 20 else ("slow" if avg_length > 50 else "normal")

        # 프로파일 생성
        profile = self.create_profile(
            character_name=character_name,
            speech_level=speech_level,
            personality=personality,
            speech_speed=speech_speed,
            catchphrases=catchphrases,
            sample_dialogues=dialogues[:5],
        )

        return profile

    def _extract_character_dialogues(self, character_name: str, text: str) -> list[str]:
        """텍스트에서 특정 캐릭터의 대사 추출"""
        dialogues = []
        character_name_esc = re.escape(character_name)

        # 패턴: "캐릭터명...대사" 또는 대사 후 캐릭터명
        patterns = [
            rf'{character_name_esc}[이가은는]\s*[^"]*"([^"]+)"',
            rf'{character_name_esc}[이가은는][^"]*말했다[^"]*"([^"]+)"',
            rf'"([^"]+)"[^"]*{character_name_esc}',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            dialogues.extend(matches)

        return list(set(dialogues))  # 중복 제거

    def _analyze_speech_level(self, dialogues: list[str]) -> str:
        """대사에서 말투 레벨 분석"""
        scores = {"formal": 0, "informal": 0, "archaic": 0}

        for dialogue in dialogues:
            for level, patterns in self.SPEECH_LEVEL_PATTERNS.items():
                for marker in patterns["markers"]:
                    if re.search(marker, dialogue):
                        scores[level] += 1

        if sum(scores.values()) == 0:
            return "formal"  # 기본값

        return max(scores, key=scores.get)

    def _analyze_personality(self, dialogues: list[str]) -> str:
        """대사에서 성격 분석"""
        scores = {p: 0 for p in self.PERSONALITY_PATTERNS}

        combined = " ".join(dialogues)

        for personality, patterns in self.PERSONALITY_PATTERNS.items():
            for keyword in patterns.get("keywords", []):
                if keyword in combined:
                    scores[personality] += 1

            for punct in patterns.get("punctuation", []):
                scores[personality] += combined.count(punct) * 0.5

        if sum(scores.values()) == 0:
            return "neutral"

        return max(scores, key=scores.get)

    def _extract_catchphrases(self, dialogues: list[str], min_freq: int = 2) -> list[str]:
        """반복되는 표현(입버릇) 추출"""
        # 2-gram, 3-gram 추출
        ngrams = Counter()

        for dialogue in dialogues:
            words = dialogue.split()
            for n in [2, 3]:
                for i in range(len(words) - n + 1):
                    ngram = " ".join(words[i : i + n])
                    if len(ngram) >= 4:  # 최소 길이
                        ngrams[ngram] += 1

        # 최소 빈도 이상인 것만 반환
        return [phrase for phrase, count in ngrams.items() if count >= min_freq][:5]

    def validate_dialogue(self, character_name: str, dialogue: str) -> dict[str, Any]:
        """
        대사가 캐릭터 프로파일과 일치하는지 검증

        Args:
            character_name: 캐릭터 이름
            dialogue: 검증할 대사

        Returns:
            {"consistent": bool, "issues": [...], "score": float}
        """
        result = {"consistent": True, "issues": [], "score": 100.0}

        profile = self.profiles.get(character_name)
        if not profile:
            result["issues"].append({"type": "no_profile", "message": f"'{character_name}' 프로파일 없음"})
            return result

        # 1. 말투 일치 검증
        detected_level = self._analyze_speech_level([dialogue])
        if detected_level != profile.speech_level:
            result["issues"].append(
                {
                    "type": "speech_level_mismatch",
                    "severity": "WARNING",
                    "message": f"말투 불일치: 기대 '{profile.speech_level}', 감지 '{detected_level}'",
                }
            )
            result["score"] -= 15

        # 2. 금지 단어 체크
        for forbidden in profile.forbidden_words:
            if forbidden in dialogue:
                result["issues"].append(
                    {"type": "forbidden_word", "severity": "WARNING", "message": f"금지 표현 사용: '{forbidden}'"}
                )
                result["score"] -= 10

        # 3. 문장 길이 성향 체크
        if profile.speech_speed == "fast" and len(dialogue) > 80:
            result["issues"].append(
                {"type": "length_mismatch", "severity": "INFO", "message": f"성향과 다른 긴 대사 ({len(dialogue)}자)"}
            )
            result["score"] -= 5
        elif profile.speech_speed == "slow" and len(dialogue) < 15:
            result["issues"].append(
                {"type": "length_mismatch", "severity": "INFO", "message": f"성향과 다른 짧은 대사 ({len(dialogue)}자)"}
            )
            result["score"] -= 5

        result["consistent"] = len([i for i in result["issues"] if i.get("severity") == "WARNING"]) == 0
        result["score"] = max(0, result["score"])

        return result

    def generate_writer_prompt(self, character_name: str) -> str:
        """
        Writer 에이전트용 캐릭터 가이드 프롬프트 생성

        Args:
            character_name: 캐릭터 이름

        Returns:
            프롬프트 문자열
        """
        profile = self.profiles.get(character_name)
        if not profile:
            return f"[캐릭터: {character_name}] 프로파일 없음 - 자유롭게 설정"

        lines = [f"[V58 캐릭터 음성 가이드: {character_name}]"]

        # 말투
        level_desc = {
            "formal": "존댓말 (습니다, 입니다)",
            "informal": "반말 (어, 지, 네)",
            "archaic": "고어체 (하오, 하시오, 로다)",
        }
        lines.append(f"  말투: {level_desc.get(profile.speech_level, profile.speech_level)}")

        # 성격
        personality_desc = {
            "aggressive": "공격적/거친",
            "calm": "차분한/사려깊은",
            "humorous": "유머러스한",
            "cold": "냉정한/무뚝뚝한",
            "warm": "따뜻한/배려하는",
            "neutral": "중립적",
        }
        lines.append(f"  성격: {personality_desc.get(profile.personality, profile.personality)}")

        # 대사 길이 성향
        speed_desc = {"fast": "짧고 간결한 대사", "normal": "보통 길이", "slow": "길고 설명적인 대사"}
        lines.append(f"  성향: {speed_desc.get(profile.speech_speed, profile.speech_speed)}")

        # 입버릇
        if profile.catchphrases:
            lines.append(f"  입버릇: {', '.join(profile.catchphrases[:3])}")

        # 예시 대사
        if profile.sample_dialogues:
            lines.append("  예시 대사:")
            for sample in profile.sample_dialogues[:2]:
                lines.append(f'    "{sample[:50]}..."')

        # 금지 표현
        if profile.forbidden_words:
            lines.append(f"  금지 표현: {', '.join(profile.forbidden_words[:3])}")

        return "\n".join(lines)

    def generate_all_profiles_prompt(self, character_names: list[str] = None) -> str:
        """
        여러 캐릭터의 프로파일 프롬프트 일괄 생성

        Args:
            character_names: 포함할 캐릭터 (None이면 전체)

        Returns:
            통합 프롬프트
        """
        if character_names is None:
            character_names = list(self.profiles.keys())

        prompts = []
        for name in character_names:
            if name in self.profiles:
                prompts.append(self.generate_writer_prompt(name))

        if not prompts:
            return "[V58] 등록된 캐릭터 프로파일 없음"

        return "\n\n".join(prompts)

    def get_profile(self, character_name: str) -> VoiceProfile | None:
        """프로파일 조회"""
        return self.profiles.get(character_name)

    def list_profiles(self) -> list[str]:
        """등록된 프로파일 목록"""
        return list(self.profiles.keys())

    def get_statistics(self) -> dict[str, Any]:
        """프로파일 통계"""
        if not self.profiles:
            return {"total": 0}

        by_speech_level = Counter(p.speech_level for p in self.profiles.values())
        by_personality = Counter(p.personality for p in self.profiles.values())

        return {
            "total": len(self.profiles),
            "by_speech_level": dict(by_speech_level),
            "by_personality": dict(by_personality),
        }


def create_voice_profiler(db_manager=None, genre: str = "wuxia") -> CharacterVoiceProfiler:
    """CharacterVoiceProfiler 인스턴스 생성 헬퍼"""
    return CharacterVoiceProfiler(db_manager=db_manager, genre=genre)
