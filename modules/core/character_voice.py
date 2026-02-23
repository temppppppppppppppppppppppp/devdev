"""
[V51.5] Character Voice Tracker (캐릭터 음성 추적기)
캐릭터별 말투/어조 패턴 추적 및 일관성 유지

핵심: LLM 비용 0원으로 캐릭터 일관성 향상

원리:
1. 대화문에서 화자별 패턴 추출
2. 어휘, 문장 구조, 특징적 표현 분석
3. 캐릭터 프로필 자동 구축
4. 일관성 위반 감지 및 가이드 제공

사용:
    tracker = CharacterVoiceTracker()
    tracker.analyze_manuscript(ep_num, manuscript)
    guidance = tracker.get_voice_guidance(character_name)
    warnings = tracker.check_consistency(character_name, dialogue)
"""

import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class VoiceStyle(Enum):
    """말투 스타일"""

    FORMAL = "formal"  # 정중체 (존댓말)
    INFORMAL = "informal"  # 반말
    ARCHAIC = "archaic"  # 고어체 (무협용)
    CRUDE = "crude"  # 거친 말투
    NOBLE = "noble"  # 귀족/양반 말투
    MARTIAL = "martial"  # 무인 말투
    SCHOLARLY = "scholarly"  # 학자 말투
    MERCHANT = "merchant"  # 상인 말투


@dataclass
class VoicePattern:
    """말투 패턴"""

    endings: list[str] = field(default_factory=list)  # 문장 종결어미
    honorifics: bool = True  # 존칭 사용 여부
    exclamations: list[str] = field(default_factory=list)  # 감탄사
    filler_words: list[str] = field(default_factory=list)  # 말버릇
    vocabulary_level: str = "normal"  # 어휘 수준 (low/normal/high)
    sentence_length: str = "normal"  # 문장 길이 (short/normal/long)
    characteristic_phrases: list[str] = field(default_factory=list)  # 특징적 표현


@dataclass
class CharacterVoiceProfile:
    """캐릭터 음성 프로필"""

    name: str
    style: VoiceStyle = VoiceStyle.INFORMAL
    pattern: VoicePattern = field(default_factory=VoicePattern)
    sample_dialogues: list[str] = field(default_factory=list)  # 대표 대사 샘플
    dialogue_count: int = 0  # 분석된 대사 수
    consistency_score: float = 1.0  # 일관성 점수 (0-1)
    last_seen_episode: int = 0  # 마지막 등장 화


class CharacterVoiceTracker:
    """캐릭터 음성 추적기"""

    # 문장 종결어미 패턴
    ENDING_PATTERNS = {
        VoiceStyle.FORMAL: [r"습니다[.!?]?$", r"습니까[.!?]?$", r"세요[.!?]?$", r"시오[.!?]?$", r"오[.!?]?$"],
        VoiceStyle.INFORMAL: [r"야[.!?]?$", r"지[.!?]?$", r"어[.!?]?$", r"냐[.!?]?$", r"해[.!?]?$", r"군[.!?]?$"],
        VoiceStyle.ARCHAIC: [
            r"하오[.!?]?$",
            r"시오[.!?]?$",
            r"리라[.!?]?$",
            r"로다[.!?]?$",
            r"구나[.!?]?$",
            r"도다[.!?]?$",
        ],
        VoiceStyle.CRUDE: [r"냐[.!?]?$", r"냐고[.!?]?$", r"놈[아아]?[.!?]?$", r"새끼[.!?]?$", r"씨[.!?]?$"],
        VoiceStyle.NOBLE: [r"하오[.!?]?$", r"것이오[.!?]?$", r"이시다[.!?]?$", r"거라[.!?]?$", r"허허[.!?]?$"],
        VoiceStyle.MARTIAL: [r"이다[.!?]?$", r"도다[.!?]?$", r"하라[.!?]?$", r"하겠다[.!?]?$", r"것이다[.!?]?$"],
    }

    # 감탄사 패턴
    EXCLAMATION_PATTERNS = {
        VoiceStyle.ARCHAIC: ["허허", "허어", "음", "흠", "허"],
        VoiceStyle.CRUDE: ["쳇", "젠장", "씨발", "빌어먹을"],
        VoiceStyle.NOBLE: ["허허", "호호", "음", "그래"],
        VoiceStyle.MARTIAL: ["흠", "음", "크하", "허"],
        VoiceStyle.SCHOLARLY: ["흠", "음", "그러하군"],
    }

    # 존칭 관련 패턴
    HONORIFIC_PATTERNS = [
        r"님",
        r"공",
        r"장",
        r"주",
        r"대인",
        r"각하",
        r"어르신",
        r"아버님",
        r"어머님",
        r"형님",
        r"사형",
        r"사제",
    ]

    def __init__(self, max_samples: int = 10):
        self.max_samples = max_samples
        self.profiles: dict[str, CharacterVoiceProfile] = {}
        self.dialogue_pattern = re.compile(r'"([^"]+)"|「([^」]+)」|\'([^\']+)\'|"([^"]+)"')
        self.speaker_pattern = re.compile(
            r"([가-힣A-Za-z]+)(?:이|가|은|는)?\s*(?:말|외치|소리|속삭|중얼|웃으며|답|물|묻)"
        )

    def extract_dialogues(self, manuscript: str) -> list[tuple[str, str]]:
        """원고에서 화자-대사 쌍 추출"""
        dialogues = []

        # 문단 단위로 분석
        paragraphs = manuscript.split("\n")

        for para in paragraphs:
            # 대화문 추출
            dialogue_matches = self.dialogue_pattern.findall(para)
            if not dialogue_matches:
                continue

            # 대화문 내용 (그룹 중 하나만 매칭됨)
            dialogue = next((m for group in dialogue_matches for m in group if m), None)
            if not dialogue:
                continue

            # 화자 추출 시도
            speaker_match = self.speaker_pattern.search(para)
            if speaker_match:
                speaker = speaker_match.group(1)
            else:
                # 앞부분에서 이름 추출 시도
                name_match = re.match(r"^([가-힣]{2,4})", para)
                speaker = name_match.group(1) if name_match else "UNKNOWN"

            dialogues.append((speaker, dialogue))

        return dialogues

    def analyze_dialogue(self, dialogue: str) -> dict[str, Any]:
        """단일 대사 분석"""
        analysis = {
            "length": len(dialogue),
            "word_count": len(dialogue.split()),
            "endings": [],
            "exclamations": [],
            "honorifics": False,
            "detected_style": None,
        }

        # 문장 종결어미 분석
        sentences = re.split(r"[.!?]", dialogue)
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue

            for style, patterns in self.ENDING_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, sent):
                        analysis["endings"].append(style.value)
                        break

        # 감탄사 분석
        for style, exclamations in self.EXCLAMATION_PATTERNS.items():
            for excl in exclamations:
                if excl in dialogue:
                    analysis["exclamations"].append(excl)

        # 존칭 분석
        for pattern in self.HONORIFIC_PATTERNS:
            if re.search(pattern, dialogue):
                analysis["honorifics"] = True
                break

        # 스타일 추론
        if analysis["endings"]:
            from collections import Counter

            style_counts = Counter(analysis["endings"])
            most_common = style_counts.most_common(1)
            if most_common:
                analysis["detected_style"] = most_common[0][0]

        return analysis

    def analyze_manuscript(self, ep_num: int, manuscript: str, known_characters: list[str] = None) -> dict[str, Any]:
        """원고 전체 분석 및 프로필 업데이트"""
        dialogues = self.extract_dialogues(manuscript)

        character_dialogues: dict[str, list[str]] = defaultdict(list)
        for speaker, dialogue in dialogues:
            character_dialogues[speaker].append(dialogue)

        updates = {}
        for character, lines in character_dialogues.items():
            if character == "UNKNOWN":
                continue

            # 대사 분석
            analyses = [self.analyze_dialogue(d) for d in lines]

            # 프로필 업데이트 또는 생성
            if character not in self.profiles:
                self.profiles[character] = CharacterVoiceProfile(name=character)

            profile = self.profiles[character]

            # 스타일 추론
            style_votes = []
            for a in analyses:
                if a["detected_style"]:
                    style_votes.append(a["detected_style"])

            if style_votes:
                from collections import Counter

                most_common_style = Counter(style_votes).most_common(1)
                if most_common_style:
                    try:
                        profile.style = VoiceStyle(most_common_style[0][0])
                    except ValueError:
                        pass

            # 패턴 업데이트
            all_exclamations = []
            for a in analyses:
                all_exclamations.extend(a["exclamations"])

            profile.pattern.exclamations = list(set(all_exclamations))[:5]
            profile.pattern.honorifics = any(a["honorifics"] for a in analyses)

            # 샘플 대사 저장 (가장 특징적인 것들)
            sorted_lines = sorted(lines, key=len, reverse=True)
            profile.sample_dialogues = sorted_lines[: self.max_samples]
            profile.dialogue_count += len(lines)
            profile.last_seen_episode = ep_num

            updates[character] = {
                "dialogue_count": len(lines),
                "style": profile.style.value,
                "honorifics": profile.pattern.honorifics,
            }

        return {
            "episode": ep_num,
            "total_dialogues": len(dialogues),
            "characters_analyzed": len(updates),
            "updates": updates,
        }

    def get_voice_guidance(self, character_name: str) -> str:
        """캐릭터별 음성 가이드 생성"""
        if character_name not in self.profiles:
            return ""

        profile = self.profiles[character_name]

        lines = [f"[{character_name} 말투 가이드]"]

        # 스타일
        style_desc = {
            VoiceStyle.FORMAL: "정중체 (존댓말 사용)",
            VoiceStyle.INFORMAL: "반말 사용",
            VoiceStyle.ARCHAIC: "고어체 ('~하오', '~로다' 등)",
            VoiceStyle.CRUDE: "거친 말투",
            VoiceStyle.NOBLE: "귀족/양반 말투",
            VoiceStyle.MARTIAL: "무인 말투 (간결하고 힘있게)",
            VoiceStyle.SCHOLARLY: "학자 말투 (사색적)",
            VoiceStyle.MERCHANT: "상인 말투 (실용적)",
        }
        lines.append(f"- 기본 스타일: {style_desc.get(profile.style, profile.style.value)}")

        # 존칭
        if profile.pattern.honorifics:
            lines.append("- 존칭 사용: 예")
        else:
            lines.append("- 존칭 사용: 아니오")

        # 감탄사
        if profile.pattern.exclamations:
            lines.append(f"- 자주 쓰는 감탄사: {', '.join(profile.pattern.exclamations)}")

        # 샘플 대사
        if profile.sample_dialogues:
            lines.append("- 대표 대사 예시:")
            for sample in profile.sample_dialogues[:3]:
                if len(sample) > 50:
                    sample = sample[:47] + "..."
                lines.append(f'  "{sample}"')

        return "\n".join(lines)

    def check_consistency(self, character_name: str, dialogue: str) -> list[dict[str, str]]:
        """대사 일관성 체크"""
        warnings = []

        if character_name not in self.profiles:
            return warnings

        profile = self.profiles[character_name]
        analysis = self.analyze_dialogue(dialogue)

        # 스타일 불일치 체크
        if analysis["detected_style"]:
            detected = analysis["detected_style"]
            expected = profile.style.value
            if detected != expected:
                warnings.append(
                    {
                        "type": "style_mismatch",
                        "message": f"{character_name}의 말투가 불일치합니다. 예상: {expected}, 감지: {detected}",
                    }
                )

        # 존칭 불일치 체크
        if profile.pattern.honorifics != analysis["honorifics"]:
            expected_hon = "사용" if profile.pattern.honorifics else "미사용"
            actual_hon = "사용" if analysis["honorifics"] else "미사용"
            warnings.append(
                {
                    "type": "honorific_mismatch",
                    "message": f"{character_name}의 존칭 사용이 불일치합니다. 예상: {expected_hon}, 실제: {actual_hon}",
                }
            )

        return warnings

    def get_all_guidance(self) -> str:
        """모든 캐릭터 가이드 통합"""
        if not self.profiles:
            return ""

        lines = ["[V51.5 캐릭터 음성 가이드]"]
        lines.append("다음 캐릭터들의 말투를 일관되게 유지하세요:\n")

        for name, profile in sorted(self.profiles.items(), key=lambda x: x[1].dialogue_count, reverse=True)[
            :10
        ]:  # 상위 10명만
            lines.append(self.get_voice_guidance(name))
            lines.append("")

        return "\n".join(lines)

    def get_writer_injection(self, characters: list[str] = None) -> str:
        """Writer용 주입 프롬프트 생성"""
        if not self.profiles:
            return ""

        if characters:
            target_chars = [c for c in characters if c in self.profiles]
        else:
            # 최근 등장 상위 5명
            target_chars = sorted(self.profiles.keys(), key=lambda x: self.profiles[x].last_seen_episode, reverse=True)[
                :5
            ]

        if not target_chars:
            return ""

        lines = ["[V51.5 캐릭터 말투 일관성]"]
        lines.append("다음 캐릭터의 말투를 유지하세요:\n")

        for name in target_chars:
            profile = self.profiles[name]
            style_short = {
                VoiceStyle.FORMAL: "존댓말",
                VoiceStyle.INFORMAL: "반말",
                VoiceStyle.ARCHAIC: "고어체",
                VoiceStyle.CRUDE: "거친",
                VoiceStyle.NOBLE: "귀족체",
                VoiceStyle.MARTIAL: "무인체",
                VoiceStyle.SCHOLARLY: "학자체",
                VoiceStyle.MERCHANT: "상인체",
            }
            style = style_short.get(profile.style, profile.style.value)

            excl = f" (감탄사: {', '.join(profile.pattern.exclamations[:2])})" if profile.pattern.exclamations else ""
            lines.append(f"- {name}: {style}{excl}")

        return "\n".join(lines)

    def save_to_json(self, filepath: str):
        """프로필 저장"""
        data = {}
        for name, profile in self.profiles.items():
            data[name] = {
                "name": name,
                "style": profile.style.value,
                "pattern": {
                    "endings": profile.pattern.endings,
                    "honorifics": profile.pattern.honorifics,
                    "exclamations": profile.pattern.exclamations,
                    "filler_words": profile.pattern.filler_words,
                    "vocabulary_level": profile.pattern.vocabulary_level,
                    "sentence_length": profile.pattern.sentence_length,
                    "characteristic_phrases": profile.pattern.characteristic_phrases,
                },
                "sample_dialogues": profile.sample_dialogues,
                "dialogue_count": profile.dialogue_count,
                "consistency_score": profile.consistency_score,
                "last_seen_episode": profile.last_seen_episode,
            }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_to_db(self, db) -> None:
        """[DB-Eff-P1] character_voice 테이블에 저장."""
        if not db or not hasattr(db, "conn") or db.conn is None:
            return

        lock = getattr(db, "_lock", None)

        def _save() -> None:
            try:
                for name, profile in self.profiles.items():
                    profile_data = {
                        "name": name,
                        "style": profile.style.value,
                        "pattern": {
                            "endings": profile.pattern.endings,
                            "honorifics": profile.pattern.honorifics,
                            "exclamations": profile.pattern.exclamations,
                            "filler_words": profile.pattern.filler_words,
                            "vocabulary_level": profile.pattern.vocabulary_level,
                            "sentence_length": profile.pattern.sentence_length,
                            "characteristic_phrases": profile.pattern.characteristic_phrases,
                        },
                        "sample_dialogues": profile.sample_dialogues,
                        "dialogue_count": profile.dialogue_count,
                        "consistency_score": profile.consistency_score,
                        "last_seen_episode": profile.last_seen_episode,
                    }
                    db.conn.execute(
                        """INSERT OR REPLACE INTO character_voice(npc_name, profile_data, updated_at)
                           VALUES (?, ?, datetime('now'))""",
                        (name, json.dumps(profile_data, ensure_ascii=False)),
                    )
                db.conn.commit()
            except Exception as e:
                try:
                    db.conn.rollback()
                except Exception:
                    pass
                logging.warning(f"[CharacterVoiceTracker] DB save rollback: {e}")

        if lock:
            with lock:
                _save()
        else:
            _save()

    def load_from_json(self, filepath: str):
        """프로필 로드"""
        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)

            for name, profile_data in data.items():
                pattern = VoicePattern(
                    endings=profile_data.get("pattern", {}).get("endings", []),
                    honorifics=profile_data.get("pattern", {}).get("honorifics", True),
                    exclamations=profile_data.get("pattern", {}).get("exclamations", []),
                    filler_words=profile_data.get("pattern", {}).get("filler_words", []),
                    vocabulary_level=profile_data.get("pattern", {}).get("vocabulary_level", "normal"),
                    sentence_length=profile_data.get("pattern", {}).get("sentence_length", "normal"),
                    characteristic_phrases=profile_data.get("pattern", {}).get("characteristic_phrases", []),
                )

                try:
                    style = VoiceStyle(profile_data.get("style", "informal"))
                except ValueError:
                    style = VoiceStyle.INFORMAL

                self.profiles[name] = CharacterVoiceProfile(
                    name=name,
                    style=style,
                    pattern=pattern,
                    sample_dialogues=profile_data.get("sample_dialogues", []),
                    dialogue_count=profile_data.get("dialogue_count", 0),
                    consistency_score=profile_data.get("consistency_score", 1.0),
                    last_seen_episode=profile_data.get("last_seen_episode", 0),
                )

        except FileNotFoundError:
            pass
        except Exception as e:
            logging.warning(f"[CharacterVoiceTracker] Load error: {e}")

    def load_from_db(self, db) -> int:
        """[DB-Eff-P1] character_voice 테이블에서 로드. 로드된 수 반환."""
        if not db or not hasattr(db, "conn") or db.conn is None:
            return 0

        lock = getattr(db, "_lock", None)

        def _load_rows():
            return db.conn.execute(
                "SELECT npc_name, profile_data FROM character_voice"
            ).fetchall()

        try:
            if lock:
                with lock:
                    rows = _load_rows()
            else:
                rows = _load_rows()
        except Exception as e:
            logging.warning(f"[CharacterVoiceTracker] DB load error: {e}")
            return 0

        loaded_profiles: dict[str, CharacterVoiceProfile] = {}
        for row in rows:
            if isinstance(row, tuple):
                name, raw_data = row
            else:
                name = row["npc_name"]
                raw_data = row["profile_data"]

            try:
                profile_data = json.loads(raw_data) if raw_data else {}
                if not isinstance(profile_data, dict):
                    continue
            except Exception:
                continue

            pattern_data = profile_data.get("pattern", {})
            pattern = VoicePattern(
                endings=pattern_data.get("endings", []),
                honorifics=pattern_data.get("honorifics", True),
                exclamations=pattern_data.get("exclamations", []),
                filler_words=pattern_data.get("filler_words", []),
                vocabulary_level=pattern_data.get("vocabulary_level", "normal"),
                sentence_length=pattern_data.get("sentence_length", "normal"),
                characteristic_phrases=pattern_data.get("characteristic_phrases", []),
            )

            try:
                style = VoiceStyle(profile_data.get("style", "informal"))
            except ValueError:
                style = VoiceStyle.INFORMAL

            loaded_profiles[name] = CharacterVoiceProfile(
                name=name,
                style=style,
                pattern=pattern,
                sample_dialogues=profile_data.get("sample_dialogues", []),
                dialogue_count=profile_data.get("dialogue_count", 0),
                consistency_score=profile_data.get("consistency_score", 1.0),
                last_seen_episode=profile_data.get("last_seen_episode", 0),
            )

        self.profiles = loaded_profiles
        return len(loaded_profiles)

    def clear(self) -> None:
        """모든 프로필 초기화"""
        self.profiles = {}
