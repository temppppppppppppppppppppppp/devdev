"""
[V50.2] Dialogue Quality Engine
대사 품질 엔진 - 캐릭터별 말투 DNA 추출 및 일관성 검증

기능:
1. 캐릭터별 대사 DNA 추출 (어휘, 문장 길이, 말버릇, 호칭)
2. 대사 일관성 검증 (캐릭터다운 대사인가?)
3. 캐릭터 간 유사도 비교 (너무 비슷하면 경고)
4. 대사 개선 제안

사용:
    engine = DialogueQualityEngine()
    engine.learn_character("팽무진", sample_dialogues)
    result = engine.validate_dialogue("팽무진", "이것이 나의 길이다!")
    similarity = engine.compare_characters("팽무진", "장로")
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import Counter
import re
import math


@dataclass
class DialogueDNA:
    """캐릭터 대사 DNA"""
    character: str

    # 어휘 특성
    vocabulary_formality: float = 0.5  # 0=비격식, 1=격식
    vocabulary_archaic: float = 0.5    # 0=현대적, 1=고어체
    unique_words: Set[str] = field(default_factory=set)  # 자주 쓰는 특징적 단어

    # 문장 특성
    avg_sentence_length: float = 15.0  # 평균 문장 길이 (음절)
    sentence_length_variance: float = 5.0  # 문장 길이 분산

    # 말버릇
    speech_endings: Dict[str, float] = field(default_factory=dict)  # 어미 분포
    catchphrases: List[str] = field(default_factory=list)  # 말버릇/감탄사

    # 호칭 패턴
    address_patterns: Dict[str, str] = field(default_factory=dict)  # {대상: 호칭}
    self_reference: str = ""  # 자신을 부르는 방식

    # 감정 표현
    emotion_intensity: float = 0.5  # 0=절제, 1=격정적
    exclamation_frequency: float = 0.1  # 감탄/물음 빈도

    # 메타 정보
    sample_count: int = 0
    confidence: float = 0.0


@dataclass
class DialogueValidation:
    """대사 검증 결과"""
    is_valid: bool
    score: int  # 0-100
    issues: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class DialogueQualityEngine:
    """
    [V50.2] 대사 품질 엔진

    캐릭터별 고유한 말투를 학습하고
    대사의 일관성을 검증합니다.
    """

    # ═══════════════════════════════════════════════════════════════
    # 말투 분석용 패턴
    # ═══════════════════════════════════════════════════════════════

    # 격식체 어미
    FORMAL_ENDINGS = [
        "습니다", "입니다", "옵니다", "됩니다", "겠습니다",
        "하십시오", "하시오", "하소서", "하옵소서",
        "하겠나이다", "하옵나이다", "로소이다"
    ]

    # 비격식체 어미
    INFORMAL_ENDINGS = [
        "해", "야", "어", "지", "네", "나", "냐",
        "거든", "잖아", "거야", "는데", "걸",
        "다고", "래", "대", "다니까"
    ]

    # 고어체 어휘
    ARCHAIC_WORDS = [
        "그대", "소생", "폐하", "전하", "각하", "대인",
        "하오", "하시오", "되오", "하겠소", "이로다",
        "아니로다", "함이", "것이오", "무엇이오",
        "어찌", "진정", "과연", "실로", "참으로",
        "가히", "능히", "마땅히", "모름지기"
    ]

    # 현대어 어휘
    MODERN_WORDS = [
        "진짜", "완전", "대박", "쩔어", "개",
        "좀", "약간", "되게", "엄청", "짱",
        "그냥", "막", "뭐", "어떻게", "왜"
    ]

    # 감정 강도 표현
    HIGH_EMOTION_MARKERS = [
        "!", "?!", "!!", "...", "―",
        "크악", "으악", "헉", "와", "오오",
        "젠장", "빌어먹을", "망할", "제기랄"
    ]

    LOW_EMOTION_MARKERS = [
        "음", "흠", "글쎄", "그렇군", "그런가",
        "알겠네", "보자", "생각해보면"
    ]

    # 무협 호칭 패턴
    WUXIA_ADDRESS_PATTERNS = {
        "superior": ["사부", "사조", "장문인", "맹주", "교주", "대인", "전하"],
        "equal": ["형", "도형", "벗", "친구", "동료"],
        "inferior": ["제자", "녀석", "놈", "자네", "그대"],
        "enemy": ["악당", "마두", "놈", "쥐새끼", "자"],
        "self": ["나", "본좌", "소생", "이 몸", "본인", "소인"]
    }

    def __init__(self):
        self.characters: Dict[str, DialogueDNA] = {}
        self.dialogue_samples: Dict[str, List[str]] = {}

    def learn_character(
        self,
        character: str,
        dialogues: List[str],
        role: str = "protagonist",
        merge: bool = True
    ) -> DialogueDNA:
        """
        캐릭터 대사 패턴 학습

        Args:
            character: 캐릭터 이름
            dialogues: 대사 샘플 리스트
            role: 역할 (protagonist, ally, enemy, elder, etc.)
            merge: True면 기존 학습에 추가, False면 새로 시작

        Returns:
            학습된 DialogueDNA
        """
        if not dialogues:
            return self.characters.get(character, DialogueDNA(character=character))

        # 기존 샘플 병합 또는 초기화
        if merge and character in self.dialogue_samples:
            samples = self.dialogue_samples[character] + dialogues
        else:
            samples = dialogues
        self.dialogue_samples[character] = samples[-100:]  # 최근 100개만 유지

        # DNA 추출
        dna = self._extract_dna(character, samples)
        dna.sample_count = len(samples)
        dna.confidence = min(1.0, len(samples) / 20)  # 20개 이상이면 신뢰도 100%

        self.characters[character] = dna
        return dna

    def _extract_dna(self, character: str, dialogues: List[str]) -> DialogueDNA:
        """대사에서 DNA 추출"""
        dna = DialogueDNA(character=character)

        if not dialogues:
            return dna

        all_text = " ".join(dialogues)

        # 1. 격식/비격식 분석
        formal_count = sum(1 for e in self.FORMAL_ENDINGS if e in all_text)
        informal_count = sum(1 for e in self.INFORMAL_ENDINGS if e in all_text)
        total = formal_count + informal_count + 1
        dna.vocabulary_formality = formal_count / total

        # 2. 고어/현대어 분석
        archaic_count = sum(1 for w in self.ARCHAIC_WORDS if w in all_text)
        modern_count = sum(1 for w in self.MODERN_WORDS if w in all_text)
        total = archaic_count + modern_count + 1
        dna.vocabulary_archaic = archaic_count / total

        # 3. 문장 길이 분석
        sentences = []
        for d in dialogues:
            sents = re.split(r'[.!?]', d)
            sentences.extend([s.strip() for s in sents if s.strip()])

        if sentences:
            lengths = [len(s) for s in sentences]
            dna.avg_sentence_length = sum(lengths) / len(lengths)
            if len(lengths) > 1:
                mean = dna.avg_sentence_length
                dna.sentence_length_variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)

        # 4. 어미 분포
        ending_counter = Counter()
        for d in dialogues:
            for ending in self.FORMAL_ENDINGS + self.INFORMAL_ENDINGS:
                if d.endswith(ending) or d.endswith(ending + "!") or d.endswith(ending + "?"):
                    ending_counter[ending] += 1
        total_endings = sum(ending_counter.values()) + 1
        dna.speech_endings = {e: c / total_endings for e, c in ending_counter.most_common(5)}

        # 5. 말버릇/감탄사 추출
        catchphrase_patterns = [
            r'[가-힣]+[!?]{1,3}',  # 감탄사
            r'"[^"]{2,10}"',  # 짧은 반복 표현
        ]
        catchphrases = []
        for pattern in catchphrase_patterns:
            matches = re.findall(pattern, all_text)
            catchphrases.extend(matches)
        dna.catchphrases = list(set(catchphrases))[:5]

        # 6. 감정 강도
        high_count = sum(all_text.count(m) for m in self.HIGH_EMOTION_MARKERS)
        low_count = sum(all_text.count(m) for m in self.LOW_EMOTION_MARKERS)
        total = high_count + low_count + 1
        dna.emotion_intensity = high_count / total

        # 7. 감탄/물음 빈도
        total_chars = len(all_text) + 1
        exclamation_count = all_text.count("!") + all_text.count("?")
        dna.exclamation_frequency = exclamation_count / total_chars

        # 8. 자주 쓰는 특징적 단어
        words = re.findall(r'[가-힣]{2,6}', all_text)
        word_counter = Counter(words)
        # 상위 빈도 단어 중 일반적이지 않은 것
        common_words = {"그것", "이것", "저것", "하지", "않는", "있는", "없는", "된다", "한다"}
        unique = [w for w, c in word_counter.most_common(20) if w not in common_words and c >= 2]
        dna.unique_words = set(unique[:10])

        return dna

    def validate_dialogue(
        self,
        character: str,
        dialogue: str,
        context: str = ""
    ) -> DialogueValidation:
        """
        대사가 캐릭터에 맞는지 검증

        Args:
            character: 캐릭터 이름
            dialogue: 검증할 대사
            context: 대사 맥락 (선택적)

        Returns:
            DialogueValidation
        """
        if character not in self.characters:
            return DialogueValidation(
                is_valid=True,
                score=50,
                issues=[{"type": "unknown_character", "message": f"'{character}' DNA 없음 - 검증 불가"}],
                suggestions=["이 캐릭터의 대사 샘플을 먼저 학습시키세요."]
            )

        dna = self.characters[character]
        issues = []
        score = 100

        # 1. 격식체 일관성 검사
        formality_score = self._check_formality_consistency(dialogue, dna)
        if formality_score < 0.6:
            score -= 15
            expected = "격식체" if dna.vocabulary_formality > 0.5 else "비격식체"
            issues.append({
                "type": "formality_mismatch",
                "severity": "MAJOR",
                "message": f"이 캐릭터는 주로 {expected}를 사용합니다."
            })

        # 2. 고어체/현대어 일관성
        archaic_score = self._check_archaic_consistency(dialogue, dna)
        if archaic_score < 0.6:
            score -= 10
            expected = "고어체" if dna.vocabulary_archaic > 0.5 else "현대어"
            issues.append({
                "type": "vocabulary_mismatch",
                "severity": "MINOR",
                "message": f"이 캐릭터는 주로 {expected}를 사용합니다."
            })

        # 3. 문장 길이 일관성
        length_score = self._check_length_consistency(dialogue, dna)
        if length_score < 0.5:
            score -= 10
            if len(dialogue) > dna.avg_sentence_length * 2:
                issues.append({
                    "type": "too_long",
                    "severity": "MINOR",
                    "message": f"이 캐릭터의 평균 대사 길이는 {dna.avg_sentence_length:.0f}자입니다."
                })
            else:
                issues.append({
                    "type": "too_short",
                    "severity": "MINOR",
                    "message": f"이 캐릭터의 평균 대사 길이는 {dna.avg_sentence_length:.0f}자입니다."
                })

        # 4. 감정 강도 일관성
        emotion_score = self._check_emotion_consistency(dialogue, dna)
        if emotion_score < 0.5:
            score -= 10
            expected = "격정적" if dna.emotion_intensity > 0.5 else "절제된"
            issues.append({
                "type": "emotion_mismatch",
                "severity": "MINOR",
                "message": f"이 캐릭터는 주로 {expected} 표현을 사용합니다."
            })

        # 최종 판정
        is_valid = score >= 70
        suggestions = self._generate_suggestions(dialogue, dna, issues)

        return DialogueValidation(
            is_valid=is_valid,
            score=max(0, score),
            issues=issues,
            suggestions=suggestions
        )

    def _check_formality_consistency(self, dialogue: str, dna: DialogueDNA) -> float:
        """격식체 일관성 점수"""
        formal_count = sum(1 for e in self.FORMAL_ENDINGS if e in dialogue)
        informal_count = sum(1 for e in self.INFORMAL_ENDINGS if e in dialogue)
        total = formal_count + informal_count

        if total == 0:
            return 0.8  # 판단 불가 - 관대하게

        dialogue_formality = formal_count / total
        diff = abs(dialogue_formality - dna.vocabulary_formality)
        return max(0, 1 - diff * 2)

    def _check_archaic_consistency(self, dialogue: str, dna: DialogueDNA) -> float:
        """고어체 일관성 점수"""
        archaic_count = sum(1 for w in self.ARCHAIC_WORDS if w in dialogue)
        modern_count = sum(1 for w in self.MODERN_WORDS if w in dialogue)
        total = archaic_count + modern_count

        if total == 0:
            return 0.8

        dialogue_archaic = archaic_count / total
        diff = abs(dialogue_archaic - dna.vocabulary_archaic)
        return max(0, 1 - diff * 2)

    def _check_length_consistency(self, dialogue: str, dna: DialogueDNA) -> float:
        """문장 길이 일관성 점수"""
        length = len(dialogue)
        expected = dna.avg_sentence_length
        std = math.sqrt(dna.sentence_length_variance) + 1

        # 표준편차 2배 이내면 정상
        z_score = abs(length - expected) / std
        return max(0, 1 - z_score / 4)

    def _check_emotion_consistency(self, dialogue: str, dna: DialogueDNA) -> float:
        """감정 강도 일관성 점수"""
        high_count = sum(dialogue.count(m) for m in self.HIGH_EMOTION_MARKERS)
        total_chars = len(dialogue) + 1

        dialogue_intensity = min(1.0, high_count / (total_chars / 20))
        diff = abs(dialogue_intensity - dna.emotion_intensity)
        return max(0, 1 - diff * 2)

    def _generate_suggestions(
        self,
        dialogue: str,
        dna: DialogueDNA,
        issues: List[Dict]
    ) -> List[str]:
        """개선 제안 생성"""
        suggestions = []

        for issue in issues:
            issue_type = issue.get("type", "")

            if issue_type == "formality_mismatch":
                if dna.vocabulary_formality > 0.5:
                    suggestions.append("어미를 '-습니다', '-입니다' 등 격식체로 변경해보세요.")
                else:
                    suggestions.append("어미를 '-어', '-야', '-지' 등 비격식체로 변경해보세요.")

            elif issue_type == "vocabulary_mismatch":
                if dna.vocabulary_archaic > 0.5:
                    suggestions.append("'그대', '소생', '하오' 등 고어체 어휘를 사용해보세요.")
                else:
                    suggestions.append("'진짜', '좀', '되게' 등 현대적 어휘를 사용해보세요.")

            elif issue_type == "too_long":
                suggestions.append(f"대사를 {int(dna.avg_sentence_length)}자 내외로 줄여보세요.")

            elif issue_type == "too_short":
                suggestions.append("대사에 더 많은 내용을 담아보세요.")

            elif issue_type == "emotion_mismatch":
                if dna.emotion_intensity > 0.5:
                    suggestions.append("감탄사나 강조 표현을 추가해보세요. (!, ?, 크악 등)")
                else:
                    suggestions.append("감탄 표현을 줄이고 담담하게 표현해보세요.")

        # 말버릇 제안
        if dna.catchphrases:
            suggestions.append(f"이 캐릭터의 말버릇: {', '.join(dna.catchphrases[:3])}")

        return suggestions

    def compare_characters(self, char1: str, char2: str) -> Dict[str, Any]:
        """
        두 캐릭터의 대사 유사도 비교

        Returns:
            {
                "similarity": float (0-1),
                "too_similar": bool,
                "differences": [],
                "suggestion": str
            }
        """
        if char1 not in self.characters or char2 not in self.characters:
            return {
                "similarity": 0.5,
                "too_similar": False,
                "differences": ["비교할 DNA 없음"],
                "suggestion": "두 캐릭터의 대사 샘플을 먼저 학습시키세요."
            }

        dna1 = self.characters[char1]
        dna2 = self.characters[char2]

        # 각 특성별 유사도 계산
        similarities = []
        differences = []

        # 격식체
        formality_diff = abs(dna1.vocabulary_formality - dna2.vocabulary_formality)
        similarities.append(1 - formality_diff)
        if formality_diff < 0.2:
            differences.append(f"격식체 수준이 유사함 ({dna1.vocabulary_formality:.1%} vs {dna2.vocabulary_formality:.1%})")

        # 고어체
        archaic_diff = abs(dna1.vocabulary_archaic - dna2.vocabulary_archaic)
        similarities.append(1 - archaic_diff)
        if archaic_diff < 0.2:
            differences.append("고어체/현대어 사용이 유사함")

        # 문장 길이
        length_diff = abs(dna1.avg_sentence_length - dna2.avg_sentence_length)
        length_sim = max(0, 1 - length_diff / 30)
        similarities.append(length_sim)
        if length_sim > 0.8:
            differences.append(f"문장 길이가 유사함 ({dna1.avg_sentence_length:.0f} vs {dna2.avg_sentence_length:.0f}자)")

        # 감정 강도
        emotion_diff = abs(dna1.emotion_intensity - dna2.emotion_intensity)
        similarities.append(1 - emotion_diff)
        if emotion_diff < 0.2:
            differences.append("감정 표현 강도가 유사함")

        # 어휘 중복
        vocab_overlap = len(dna1.unique_words & dna2.unique_words)
        total_vocab = len(dna1.unique_words | dna2.unique_words) + 1
        vocab_sim = vocab_overlap / total_vocab
        similarities.append(vocab_sim)
        if vocab_sim > 0.3:
            differences.append(f"특징적 어휘가 중복됨: {dna1.unique_words & dna2.unique_words}")

        # 종합 유사도
        avg_similarity = sum(similarities) / len(similarities)
        too_similar = avg_similarity > 0.75

        # 개선 제안
        if too_similar:
            suggestion = f"'{char1}'과(와) '{char2}'의 말투가 너무 유사합니다. "
            if formality_diff < 0.2:
                suggestion += f"'{char2}'의 격식체 수준을 조정하세요. "
            if emotion_diff < 0.2:
                suggestion += f"'{char2}'의 감정 표현 강도를 다르게 하세요. "
        else:
            suggestion = "두 캐릭터의 말투가 충분히 구분됩니다."

        return {
            "similarity": avg_similarity,
            "too_similar": too_similar,
            "differences": differences if too_similar else [],
            "suggestion": suggestion,
            "char1_formality": dna1.vocabulary_formality,
            "char2_formality": dna2.vocabulary_formality
        }

    def get_character_profile(self, character: str) -> Dict[str, Any]:
        """캐릭터 대사 프로필 반환"""
        if character not in self.characters:
            return {"error": f"'{character}' DNA 없음"}

        dna = self.characters[character]
        return {
            "character": character,
            "formality": "격식체" if dna.vocabulary_formality > 0.5 else "비격식체",
            "formality_score": dna.vocabulary_formality,
            "vocabulary": "고어체" if dna.vocabulary_archaic > 0.5 else "현대어",
            "vocabulary_score": dna.vocabulary_archaic,
            "avg_sentence_length": dna.avg_sentence_length,
            "emotion": "격정적" if dna.emotion_intensity > 0.5 else "절제된",
            "emotion_score": dna.emotion_intensity,
            "catchphrases": dna.catchphrases,
            "unique_words": list(dna.unique_words),
            "top_endings": dna.speech_endings,
            "sample_count": dna.sample_count,
            "confidence": dna.confidence
        }

    def generate_dialogue_prompt(self, character: str) -> str:
        """Writer용 대사 가이드 프롬프트 생성"""
        if character not in self.characters:
            return f"\n[대사 가이드] '{character}' 캐릭터 DNA가 없습니다.\n"

        dna = self.characters[character]
        profile = self.get_character_profile(character)

        lines = [
            "",
            "=" * 50,
            f"[V50.2 대사 가이드 - {character}]",
            "=" * 50,
            f"말투: {profile['formality']} + {profile['vocabulary']}",
            f"문장 길이: 평균 {profile['avg_sentence_length']:.0f}자",
            f"감정 표현: {profile['emotion']}",
            "",
        ]

        if dna.catchphrases:
            lines.append(f"말버릇: {', '.join(dna.catchphrases)}")

        if dna.unique_words:
            lines.append(f"자주 쓰는 단어: {', '.join(list(dna.unique_words)[:5])}")

        if dna.speech_endings:
            top_endings = list(dna.speech_endings.keys())[:3]
            lines.append(f"주요 어미: {', '.join(top_endings)}")

        lines.append("")
        lines.append("이 캐릭터의 대사는 위 특성을 유지해야 합니다.")
        lines.append("=" * 50)

        return "\n".join(lines)

    def extract_dialogues_from_manuscript(self, manuscript: str) -> Dict[str, List[str]]:
        """
        원고에서 대사 추출

        Returns:
            {character_name: [dialogues]}
        """
        # 대사 패턴: "대사" 또는 「대사」 앞에 화자 표시
        patterns = [
            r'([가-힣]{2,10})(?:이|가|은|는)?\s*(?:말했다|외쳤다|중얼거렸다|속삭였다|소리쳤다)[^"]*"([^"]+)"',
            r'"([^"]+)"[^가-힣]*([가-힣]{2,10})(?:이|가|은|는)?\s*(?:말했다|외쳤다)',
            r'([가-힣]{2,10})의\s*(?:목소리|말)[^"]*"([^"]+)"',
        ]

        dialogues = {}
        for pattern in patterns:
            matches = re.findall(pattern, manuscript)
            for match in matches:
                if len(match) == 2:
                    char, dialogue = match[0], match[1]
                    if len(dialogue) > 5:  # 너무 짧은 건 제외
                        if char not in dialogues:
                            dialogues[char] = []
                        dialogues[char].append(dialogue)

        return dialogues

    def auto_learn_from_manuscript(self, manuscript: str) -> Dict[str, int]:
        """
        원고에서 자동으로 캐릭터 대사 학습

        Returns:
            {character: learned_dialogue_count}
        """
        extracted = self.extract_dialogues_from_manuscript(manuscript)
        results = {}

        for char, dialogues in extracted.items():
            if len(dialogues) >= 3:  # 최소 3개 이상 있어야 학습
                self.learn_character(char, dialogues, merge=True)
                results[char] = len(dialogues)

        return results
