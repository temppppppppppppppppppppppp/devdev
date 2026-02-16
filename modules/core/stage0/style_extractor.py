"""
Style Extractor V2 - 문체 DNA 추출기
====================================
기존 원고에서 작문 스타일을 정밀 추출하여 AI 생성 원고의 "AI티"를 줄임.
한 번 분석 → DB 캐싱 → 매 원고 생성 시 자동 주입.

[V61.8] 강화: 리듬 분석, 감정 렌더링, anti-AI 패턴, 모범 문단 큐레이션
"""

import json
import logging
import os
import re
import time
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any


@dataclass
class StyleGuide:
    """스타일 가이드 V2 - 문체 DNA"""

    # === 기존 필드 (V1 호환) ===
    tone: str = "중립"  # 냉소적/유머/진지/가벼움/어두움
    pov: str = "1인칭"  # 1인칭/3인칭/전지적/혼합
    sentence_length: str = "medium"  # short/medium/long
    dialogue_ratio: float = 0.3  # 대화 비율 (0.0-1.0)
    description_style: str = "균형"  # 간결/균형/묘사적
    vocabulary_level: str = "medium"  # easy/medium/hard
    paragraph_style: str = "mixed"  # short/mixed/long
    action_style: str = "dynamic"  # static/dynamic/cinematic

    sample_sentences: list[str] = None  # 대표 문장 (V2: 20-30개)
    sample_dialogues: list[str] = None  # 대표 대화 (V2: 10-15개)
    signature_expressions: list[str] = None  # 자주 쓰는 표현
    forbidden_expressions: list[str] = None  # 피해야 할 표현

    # === V2 신규 필드 ===
    sentence_rhythm: str = ""  # 문장 리듬 패턴
    emotion_rendering: str = ""  # 감정 표현 방식
    scene_transitions: list[str] = None  # 장면 전환 문장 5-8개
    dialogue_narration_pattern: str = ""  # 대화-서술 연결 패턴
    anti_ai_patterns: list[str] = None  # AI 패턴 금지 목록
    action_scene_density: str = ""  # 액션씬 묘사 밀도
    calm_scene_density: str = ""  # 일상씬 묘사 밀도
    exemplary_passages: list[str] = None  # 모범 문단 5-8개 (200-500자)

    # === 메타데이터 ===
    source_episode_count: int = 0
    source_char_count: int = 0
    analysis_version: str = "v2"
    reference_works: list[str] = None

    def __post_init__(self) -> None:
        for f in fields(self):
            if f.type == list[str] and getattr(self, f.name) is None:
                setattr(self, f.name, [])

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StyleGuide":
        valid_keys = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_keys})

    def _get_pov_rules(self) -> str:
        """[V70] 시점(POV)별 상세 집필 규칙"""
        if self.pov == "1인칭":
            return """## 🎯 시점 규칙: 1인칭 (절대 준수 — 위반 시 REJECT)
- 모든 서술을 '나'의 시점으로 기술한다. ("나는", "내가", "내 ~")
- 주인공이 직접 보고/듣고/느낀 것만 서술 가능
- 다른 캐릭터의 내면·생각을 직접 서술 금지 → 행동·표정·말투로 추론만 허용
  ❌ "그는 배신감을 느꼈다" → ✅ "그의 주먹이 미세하게 떨렸다"
  ❌ "그녀는 속으로 계획을 세웠다" → ✅ "그녀의 눈이 한순간 차갑게 빛났다"
- 주인공 부재 장면 금지: '나'가 없는 곳의 사건은 서술 불가 (나중에 전해 듣는 형식으로만)
- 3인칭 서술 전환 금지: "그는 ~했다", "시우는 ~했다" 식의 외부 시선 서술 금지
- 독백: "~인가." "~해야 했다." 등 내면 독백은 자유롭게 사용"""
        elif self.pov == "3인칭":
            return """## 🎯 시점 규칙: 3인칭 제한적 (절대 준수)
- 주인공을 이름 또는 '그/그녀'로 지칭한다
- "나는", "내가" 등 1인칭 서술자 대명사 사용 금지 (대화 속 '나'는 허용)
- 주인공의 내면 묘사는 허용하되, 타 캐릭터의 내면은 제한적으로만 사용
  ✅ "시우는 이를 악물었다. 여기서 물러서면 끝이라는 것을 알았다."
  ⚠️ 타 캐릭터 내면: 씬 전환(***) 후 1-2문장 이내로만 허용
- 주인공 부재 장면: 씬 전환 후 제한적 허용 (악역 음모, 조연 반응 등)
- "그는 아직 몰랐다" 같은 전지적 개입은 최소화 (화당 1회 이내)"""
        elif self.pov == "전지적":
            return """## 🎯 시점 규칙: 전지적 작가 시점
- 서술자가 모든 캐릭터의 내면에 자유롭게 접근 가능
- 시간·공간 제약 없이 장면 전환 가능
- "나는" 등 1인칭 대명사는 대화 속에서만 사용
- 단, 긴장감을 위해 정보 공개 타이밍을 조절할 것 (모든 것을 미리 알려주지 마라)"""
        # "혼합"이거나 미지정이면 빈 문자열
        return ""

    def to_prompt(self) -> str:
        """[V2] 강화된 프롬프트 - 문체 DNA 가이드"""
        sections = []

        # 1. 핵심 DNA
        sections.append(f"""## 문체 DNA (절대 준수)
- 톤: {self.tone}
- 시점: {self.pov}
- 대화 비율: {self.dialogue_ratio:.0%}
- 문장 길이: {self.sentence_length}
- 묘사: {self.description_style}
- 어휘: {self.vocabulary_level}""")

        # 1.5 [V70] 시점(POV) 상세 규칙
        pov_rules = self._get_pov_rules()
        if pov_rules:
            sections.append(pov_rules)

        # 2. 문장 리듬 (AI티 방지 핵심)
        if self.sentence_rhythm:
            sections.append(f"""## 문장 리듬 패턴 (AI티 방지 핵심)
{self.sentence_rhythm}
※ 모든 문장이 비슷한 길이면 AI티. 반드시 위 리듬 따를 것.""")

        # 3. 감정 표현 규칙
        if self.emotion_rendering:
            sections.append(f"""## 감정 표현 규칙
{self.emotion_rendering}""")

        # 4. AI 패턴 금지 목록 (가장 중요)
        if self.anti_ai_patterns:
            lines = "\n".join(f"- 금지: {p}" for p in self.anti_ai_patterns[:10])
            sections.append(f"""## AI 패턴 금지 목록 (위반 시 즉시 REJECT)
{lines}""")

        # 5. 모범 문단 (show, don't tell)
        if self.exemplary_passages:
            passage_lines = []
            for i, p in enumerate(self.exemplary_passages[:5], 1):
                passage_lines.append(f'[예시 {i}]\n"{p[:400]}"')
            sections.append(f"""## 참고 문체 (이 느낌으로 작성)
{chr(10).join(passage_lines)}""")

        # 6. 대화-서술 연결
        if self.dialogue_narration_pattern:
            sections.append(f"""## 대화-서술 연결 패턴
{self.dialogue_narration_pattern}""")
        if self.sample_dialogues:
            dialog_ex = "\n".join(f'  "{d[:150]}"' for d in self.sample_dialogues[:5])
            sections.append(f"### 대화 스타일 참고:\n{dialog_ex}")

        # 7. 장면 전환
        if self.scene_transitions:
            trans_ex = "\n".join(f'  "{t[:100]}"' for t in self.scene_transitions[:5])
            sections.append(f"## 장면 전환 스타일\n{trans_ex}")

        # 8. 묘사 밀도
        if self.action_scene_density or self.calm_scene_density:
            sections.append(f"""## 묘사 밀도
- 액션씬: {self.action_scene_density or "짧은 문장, 빠른 리듬"}
- 일상씬: {self.calm_scene_density or "긴 문장, 심리/풍경 묘사 확장"}""")

        # 9. 활용/금지 표현
        if self.signature_expressions:
            sections.append(f"## 활용할 표현: {', '.join(self.signature_expressions[:8])}")
        if self.forbidden_expressions:
            sections.append(f"## 사용 금지 표현: {', '.join(self.forbidden_expressions[:8])}")

        return "\n\n".join(sections)


# ═══════════════════════════════════════════════════════════════
# 감각어/클리셰 사전 (샘플 큐레이션용)
# ═══════════════════════════════════════════════════════════════

_SENSORY_WORDS = set(
    "시큰|찌릿|매캐|눅눅|축축|서늘|화끈|뻣뻣|쏟아|찢어|으스스|쿵|퍽|철컥|우두둑|사각|촉촉|아릿|싸늘|뜨끈".split("|")
)

_CLICHE_MARKERS = set(
    "깊은 슬픔|마음이 무거|가슴이 먹먹|눈물이 흘|한숨을 쉬|고개를 끄덕|미소를 지|결국|마침내|드디어|그러나|하지만|물론".split(
        "|"
    )
)

_ACTION_VERBS = set(
    "내리쳤|베었|찔렀|막았|피했|날렸|휘둘|밀쳐|때렸|잡았|던졌|쓰러|뛰어|구르|꿰뚫|쏘았|찢었|부딪|꺾었|움켜".split("|")
)

_TRANSITION_MARKERS = set(
    "그때|한편|잠시 후|얼마 뒤|이윽고|다음 날|그로부터|시간이 흘러|해가 지고|날이 밝자|자리를 옮기|장소를 바꿔".split(
        "|"
    )
)


class StyleExtractor:
    """[V2] 문체 DNA 추출기 - 정밀 클로닝"""

    API_DELAY = 0.5  # LLM 호출 간격

    def __init__(self, llm_client=None) -> None:
        self.client = llm_client

    # ═══════════════════════════════════════════════════════════════
    # 메인 추출 메서드
    # ═══════════════════════════════════════════════════════════════

    def extract_from_drafts(self, drafts: list[str], reference_name: str = "") -> StyleGuide:
        """
        [V2] 원고에서 문체 DNA 추출 (전체 원고 대상)

        Args:
            drafts: 에피소드 텍스트 리스트
            reference_name: 참조 작품 이름

        Returns:
            StyleGuide: 추출된 문체 가이드
        """
        if not drafts:
            return StyleGuide()

        all_text = "\n\n".join(drafts)
        total_chars = len(all_text)
        total_episodes = len(drafts)

        logging.info(f"[V2] 문체 분석 시작: {total_episodes}화, {total_chars:,}자")

        # Phase 1: Python 통계 분석 (전체 원고)
        logging.info("[1/5] 통계 분석...")
        stats = self._analyze_statistics_v2(drafts)

        # Phase 2: 샘플 큐레이션
        logging.info("[2/5] 샘플 큐레이션...")
        curated = self._curate_samples(drafts)

        # Phase 3: 리듬 분석
        logging.info("[3/5] 리듬 분석...")
        rhythm = self._analyze_rhythm(drafts)

        # Phase 4: LLM 심층 분석
        qualitative = {}
        if self.client or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
            logging.info("[4/5] LLM 심층 분석...")
            qualitative = self._deep_llm_analysis(drafts)

            # Phase 5: Anti-AI 패턴 생성
            logging.info("[5/5] Anti-AI 패턴 생성...")
            anti = self._generate_anti_patterns(drafts, curated.get("exemplary_passages", []))
            qualitative.update(anti)
        else:
            logging.info("[4/5] LLM 없음 - 통계 분석만 사용")
            logging.info("[5/5] 스킵")

        # 병합
        merged = {**stats, **curated, **rhythm, **qualitative}
        merged["source_episode_count"] = total_episodes
        merged["source_char_count"] = total_chars
        merged["analysis_version"] = "v2"
        if reference_name:
            merged["reference_works"] = [reference_name]

        guide = StyleGuide(**{k: v for k, v in merged.items() if k in {f.name for f in fields(StyleGuide)}})
        logging.info(f"[OK] 문체 DNA 추출 완료 (v2, {total_episodes}화 분석)")
        return guide

    # ═══════════════════════════════════════════════════════════════
    # Phase 1: 통계 분석 V2
    # ═══════════════════════════════════════════════════════════════

    def _analyze_statistics_v2(self, drafts: list[str]) -> dict[str, Any]:
        """전체 원고 통계 분석"""
        result = {}
        all_text = "\n\n".join(drafts)

        # 문장 분리 (한국어 인식)
        sentences = self._split_sentences(all_text)

        # 대화 추출
        dialogues = re.findall(r'["""]([^"""]+)["""]', all_text)

        # 문장 길이 분석
        if sentences:
            lengths = [len(s) for s in sentences]
            avg_len = sum(lengths) / len(lengths)
            if avg_len < 25:
                result["sentence_length"] = "short"
            elif avg_len < 50:
                result["sentence_length"] = "medium"
            else:
                result["sentence_length"] = "long"

        # 대화 비율
        dialogue_chars = sum(len(d) for d in dialogues)
        total_chars = len(all_text)
        if total_chars > 0:
            result["dialogue_ratio"] = round(dialogue_chars / total_chars, 2)

        # 시점 감지
        first_person = len(re.findall(r"(나는|나의|내가|나를|나에게|내 )", all_text))
        third_person = len(re.findall(r"(그는|그녀는|그의|그녀의|그가|그를)", all_text))
        if first_person > third_person * 2:
            result["pov"] = "1인칭"
        elif third_person > first_person * 2:
            result["pov"] = "3인칭"
        else:
            result["pov"] = "혼합"

        # 단락 스타일
        paragraphs = [p.strip() for p in all_text.split("\n\n") if p.strip()]
        if paragraphs:
            avg_para_len = sum(len(p) for p in paragraphs) / len(paragraphs)
            if avg_para_len < 100:
                result["paragraph_style"] = "short"
            elif avg_para_len < 300:
                result["paragraph_style"] = "mixed"
            else:
                result["paragraph_style"] = "long"

        return result

    # ═══════════════════════════════════════════════════════════════
    # Phase 2: 샘플 큐레이션
    # ═══════════════════════════════════════════════════════════════

    def _curate_samples(self, drafts: list[str]) -> dict[str, Any]:
        """점수 기반 최상위 샘플 선별"""
        result = {}
        all_text = "\n\n".join(drafts)

        sentences = self._split_sentences(all_text)
        dialogues = re.findall(r'["""]([^"""]+)["""]', all_text)

        # 문장 점수 매기기
        scored_sentences = []
        for s in sentences:
            if len(s) < 15 or len(s) > 120:
                continue
            score = self._score_sentence(s)
            scored_sentences.append((score, s))

        scored_sentences.sort(key=lambda x: -x[0])

        # 상위 20-30개 대표 문장
        result["sample_sentences"] = [s for _, s in scored_sentences[:25]]

        # 대화 큐레이션 (길이+다양성)
        good_dialogues = [d for d in dialogues if 10 < len(d) < 120]
        result["sample_dialogues"] = good_dialogues[:15]

        # 모범 문단 추출 (200-500자 블록)
        paragraphs = [p.strip() for p in all_text.split("\n\n") if p.strip()]
        scored_passages = []
        for p in paragraphs:
            if 150 < len(p) < 600:
                score = sum(1 for w in _SENSORY_WORDS if w in p) * 3
                score += sum(1 for v in _ACTION_VERBS if v in p)
                score -= sum(1 for c in _CLICHE_MARKERS if c in p) * 2
                # 대화+서술 혼합 보너스
                if '"' in p or '"' in p:
                    score += 2
                scored_passages.append((score, p))

        scored_passages.sort(key=lambda x: -x[0])
        result["exemplary_passages"] = [p for _, p in scored_passages[:8]]

        # 장면 전환 문장 추출
        transitions = []
        for s in sentences:
            if any(m in s for m in _TRANSITION_MARKERS) and 10 < len(s) < 80:
                transitions.append(s)
        result["scene_transitions"] = transitions[:8]

        return result

    def _score_sentence(self, sentence: str) -> float:
        """문장 품질 점수 (높을수록 좋은 문장)"""
        score = 0.0

        # 감각어 포함 → +3
        for w in _SENSORY_WORDS:
            if w in sentence:
                score += 3

        # 의성어/의태어 패턴 → +2
        if re.search(r"[가-힣]{2,3}[!]", sentence):
            score += 2

        # 클리셰 → -3
        for c in _CLICHE_MARKERS:
            if c in sentence:
                score -= 3

        # 짧고 강렬한 문장 보너스 (15-40자)
        if 15 <= len(sentence) <= 40:
            score += 1

        # 동사로 끝나는 문장 보너스
        if re.search(r"[았었였했]다$", sentence):
            score += 0.5

        return score

    # ═══════════════════════════════════════════════════════════════
    # Phase 3: 리듬 분석
    # ═══════════════════════════════════════════════════════════════

    def _analyze_rhythm(self, drafts: list[str]) -> dict[str, Any]:
        """문장 리듬 패턴 분석"""
        result = {}
        all_text = "\n\n".join(drafts[:20])  # 20화까지 분석
        paragraphs = [p.strip() for p in all_text.split("\n\n") if p.strip()]

        # 단락별 문장 길이 시퀀스
        rhythm_sequences = []
        action_lengths = []
        calm_lengths = []

        for para in paragraphs:
            sents = self._split_sentences(para)
            if len(sents) < 2:
                continue

            lengths = [len(s) for s in sents]
            # 분류: S(짧음 <20), M(중간 20-50), L(긴 >50)
            pattern = ""
            for l in lengths:
                if l < 20:
                    pattern += "S"
                elif l < 50:
                    pattern += "M"
                else:
                    pattern += "L"
            rhythm_sequences.append(pattern)

            # 액션씬 vs 일상씬 분류
            is_action = any(v in para for v in list(_ACTION_VERBS)[:10])
            if is_action:
                action_lengths.extend(lengths)
            else:
                calm_lengths.extend(lengths)

        # 리듬 패턴 요약
        if rhythm_sequences:
            # 가장 흔한 3자 패턴 추출
            trigrams = {}
            for seq in rhythm_sequences:
                for i in range(len(seq) - 2):
                    tri = seq[i : i + 3]
                    trigrams[tri] = trigrams.get(tri, 0) + 1

            top_patterns = sorted(trigrams.items(), key=lambda x: -x[1])[:5]
            pattern_desc = ", ".join(f"{p}({c}회)" for p, c in top_patterns)

            # S=짧은문장, M=중간문장, L=긴문장 설명
            result["sentence_rhythm"] = (
                f"주요 리듬: {pattern_desc}\n"
                f"(S=20자 미만 단문, M=20-50자 중문, L=50자+ 장문)\n"
                f"- 핵심: 단조로운 MMMMM 패턴 금지. S와 L을 섞어 리듬감 생성"
            )

        # 액션/일상 밀도
        if action_lengths:
            avg_action = sum(action_lengths) / len(action_lengths)
            result["action_scene_density"] = f"평균 {avg_action:.0f}자/문장, 단문 위주 빠른 리듬"
        if calm_lengths:
            avg_calm = sum(calm_lengths) / len(calm_lengths)
            result["calm_scene_density"] = f"평균 {avg_calm:.0f}자/문장, 묘사/심리 확장"

        return result

    # ═══════════════════════════════════════════════════════════════
    # Phase 4: LLM 심층 분석
    # ═══════════════════════════════════════════════════════════════

    def _deep_llm_analysis(self, drafts: list[str]) -> dict[str, Any]:
        """[V2] 3배치 LLM 심층 분석"""
        self._ensure_client()
        if not self.client:
            return {}

        # 초반/중반/후반에서 8000자씩 샘플링
        samples = self._sample_batches(drafts, batch_size=8000, num_batches=3)
        combined_sample = "\n\n---\n\n".join(samples)[:20000]

        prompt = f"""당신은 한국 웹소설 문체 분석 전문가입니다.
아래 원고 샘플 3개(초반/중반/후반)를 분석하세요.

## 원고 샘플
{combined_sample}

## 분석 항목 (JSON으로 출력)
```json
{{
  "tone": "이 작품의 전반적 톤 (예: 냉소적, 유머, 진지, 어두움, 가벼움)",
  "description_style": "간결/균형/묘사적 중 하나",
  "vocabulary_level": "easy/medium/hard 중 하나",
  "action_style": "static/dynamic/cinematic 중 하나",
  "emotion_rendering": "이 작가의 감정 표현 방식을 2-3문장으로 설명 (예: 직접 감정어 대신 신체 반응과 행동으로 간접 표현, 내면 독백 최소화)",
  "dialogue_narration_pattern": "대화와 서술이 어떻게 연결되는지 2-3문장 (예: 대화 전 1줄 행동묘사, 대화 후 짧은 반응, 지문 최소화)",
  "signature_expressions": ["이 작가가 자주 쓰는 특징적 표현 10개"],
  "forbidden_expressions": ["이 작가가 절대 안 쓰는 표현 5개"]
}}
```
JSON만 출력하세요.
"""
        try:
            result = self._llm_call(prompt)
            return result
        except Exception as e:
            logging.warning(f"[!] LLM 심층 분석 실패: {e}")
            return {}

    # ═══════════════════════════════════════════════════════════════
    # Phase 5: Anti-AI 패턴 생성
    # ═══════════════════════════════════════════════════════════════

    def _generate_anti_patterns(self, drafts: list[str], passages: list[str]) -> dict[str, Any]:
        """[V2] 참조 원고 기반 AI 금지 패턴 생성"""
        self._ensure_client()
        if not self.client:
            return {}

        # 모범 문단 + 초반 원고 샘플
        sample = "\n\n".join(passages[:5]) if passages else drafts[0][:5000]

        prompt = f"""당신은 한국 웹소설 AI 탐지 전문가입니다.
아래 인간 작가의 원고 샘플을 분석하고, AI가 글을 쓸 때 반드시 피해야 할 패턴을 추출하세요.

## 인간 작가 원고 샘플
{sample[:8000]}

## 추출 항목 (JSON)
이 작가의 문체를 모방할 때, AI가 빠지기 쉬운 함정과 금지 패턴을 구체적으로 나열하세요.
```json
{{
  "anti_ai_patterns": [
    "구체적 금지 패턴 1 (예: '그는 깊은 슬픔을 느꼈다' 같은 감정 직접 서술 금지)",
    "구체적 금지 패턴 2",
    "...(총 10개)"
  ]
}}
```
각 패턴은 구체적 예시와 함께 작성하세요. JSON만 출력.
"""
        try:
            time.sleep(self.API_DELAY)
            result = self._llm_call(prompt)
            return result
        except Exception as e:
            logging.warning(f"[!] Anti-AI 패턴 생성 실패: {e}")
            return {}

    # ═══════════════════════════════════════════════════════════════
    # 레퍼런스 원고 로딩
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def load_reference_manuscripts(genre: str) -> dict[str, list[str]]:
        """
        장르별 레퍼런스 원고 로드

        Args:
            genre: 장르 타입 (wuxia/hunter/investment/fantasy)

        Returns:
            {"작품명": [에피소드1, 에피소드2, ...], ...}
        """
        base_path = Path("config/style_references") / genre
        if not base_path.exists():
            logging.info(f"[!] 레퍼런스 폴더 없음: {base_path}")
            return {}

        works = {}
        for work_dir in sorted(base_path.iterdir()):
            if not work_dir.is_dir():
                continue
            episodes = []
            for txt_file in sorted(work_dir.glob("*.txt")):
                try:
                    text = txt_file.read_text(encoding="utf-8")
                    if text.strip():
                        episodes.append(text)
                except Exception as e:
                    logging.warning(f"[!] 파일 로드 실패: {txt_file.name}: {e}")
            if episodes:
                works[work_dir.name] = episodes
                logging.info(f"[+] {work_dir.name}: {len(episodes)}화 로드")

        return works

    def extract_from_references(self, genre: str) -> StyleGuide | None:
        """
        장르별 레퍼런스 폴더에서 스타일 추출

        Args:
            genre: 장르 타입

        Returns:
            StyleGuide 또는 None
        """
        works = self.load_reference_manuscripts(genre)
        if not works:
            return None

        # 모든 작품의 에피소드 합치기
        all_drafts = []
        work_names = []
        for name, episodes in works.items():
            all_drafts.extend(episodes)
            work_names.append(f"{name}({len(episodes)}화)")

        logging.info(f"[*] 총 {len(all_drafts)}화, 작품 {len(works)}개 분석")

        guide = self.extract_from_drafts(all_drafts, reference_name=", ".join(work_names))
        guide.reference_works = list(works.keys())
        return guide

    # ═══════════════════════════════════════════════════════════════
    # 유틸리티
    # ═══════════════════════════════════════════════════════════════

    def _split_sentences(self, text: str) -> list[str]:
        """한국어 문장 분리"""
        # 대화 내 마침표는 분리하지 않음
        # 한국어 종결어미 + 마침표/느낌표/물음표 기준
        sents = re.split(r"(?<=[다요죠음함임까])[.!?]\s*|\n", text)
        return [s.strip() for s in sents if s.strip() and len(s.strip()) > 3]

    def _sample_batches(self, drafts: list[str], batch_size: int = 8000, num_batches: int = 3) -> list[str]:
        """초반/중반/후반에서 균등 샘플링"""
        if len(drafts) <= num_batches:
            return [d[:batch_size] for d in drafts]

        step = max(1, len(drafts) // num_batches)
        samples = []
        for i in range(num_batches):
            idx = min(i * step, len(drafts) - 1)
            samples.append(drafts[idx][:batch_size])
        return samples

    def _ensure_client(self) -> None:
        """LLM 클라이언트 자동 초기화"""
        if self.client:
            return
        try:
            from google import genai

            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            if api_key:
                self.client = genai.Client(api_key=api_key)
        except Exception:
            pass

    def _llm_call(self, prompt: str) -> dict[str, Any]:
        """LLM 호출 + JSON 파싱 (폴백: 3-pro → 2.5-pro → 2.5-flash)"""
        from google.genai import types

        time.sleep(self.API_DELAY)

        models = ["gemini-3-pro-preview", "gemini-2.5-pro", "gemini-2.5-flash"]
        last_err = None
        for model_name in models:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3, max_output_tokens=4000, response_mime_type="application/json"
                    ),
                )
                return self._parse_json(response.text)
            except Exception as e:
                last_err = e
                logging.warning(f"[!] {model_name} 실패, 다음 모델 시도...")
                time.sleep(1)
        raise last_err if last_err else RuntimeError("All models failed")

    def _parse_json(self, text: str) -> dict[str, Any]:
        """JSON 파싱 (자가 치유)"""
        if not text:
            return {}
        try:
            # 직접 파싱
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        try:
            # 코드 블록 추출
            json_str = text
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            return json.loads(json_str.strip())
        except (json.JSONDecodeError, IndexError):
            return {}

    # ═══════════════════════════════════════════════════════════════
    # 기존 호환 메서드
    # ═══════════════════════════════════════════════════════════════

    def compare_styles(self, guide1: StyleGuide, guide2: StyleGuide) -> dict[str, Any]:
        """두 스타일 비교"""
        differences = {}
        for field_name in ["tone", "pov", "sentence_length", "description_style", "vocabulary_level"]:
            v1 = getattr(guide1, field_name)
            v2 = getattr(guide2, field_name)
            if v1 != v2:
                differences[field_name] = {"original": v1, "current": v2}

        ratio_diff = abs(guide1.dialogue_ratio - guide2.dialogue_ratio)
        if ratio_diff > 0.1:
            differences["dialogue_ratio"] = {
                "original": guide1.dialogue_ratio,
                "current": guide2.dialogue_ratio,
                "diff": ratio_diff,
            }
        return differences
