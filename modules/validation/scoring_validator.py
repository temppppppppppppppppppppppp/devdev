"""
[V0128] TIER 2: SCORING Validator
LLM 기반 점수 평가 (가중치 합산)

[V59] 장르별 가중치 / 세분화된 피드백 고도화
"""

import logging
import re
import statistics
from collections import Counter

from modules.validation.threshold_helper import _threshold  # [Phase 5-B-2c]


class ScoringValidator:
    """
    TIER 2: 점수 기반 품질 평가
    [V46] GenreGuard 기반 동적 컨텍스트 삽입

    각 항목별 점수 합산 → 임계값 이상이면 PASS
    개별 항목 실패해도 다른 항목으로 보완 가능
    """

    # 총점: 100점
    DEFAULT_PASS_THRESHOLD = 70  # 기본값: 70점 이상 PASS

    # 장르별 권장 임계값
    GENRE_THRESHOLDS = {
        "wuxia": 70,  # 무협: 기본값
        "hunter": 68,  # 헌터: 액션 위주로 약간 낮게
        "investment": 72,  # 투자: 논리성 중요로 약간 높게
    }

    def __init__(
        self, client=None, model="gemini-2.5-pro", constitution="", pass_threshold: int = None, genre: str = None
    ):
        self.client = client
        self.model = model
        self.constitution = constitution
        self.genre = genre  # [V46] 장르 저장

        # [V46] GenreGuard 동적 로드
        self.guard = self._load_guard_for_genre(genre)

        # [V44] 설정 가능한 PASS_THRESHOLD
        default_threshold = _threshold(
            "scoring.default_pass_threshold",
            self.DEFAULT_PASS_THRESHOLD,
        )
        genre_thresholds = {
            name: _threshold(f"scoring.genre_thresholds.{name}", value) for name, value in self.GENRE_THRESHOLDS.items()
        }

        if pass_threshold is not None:
            self.pass_threshold = pass_threshold
        elif genre and genre in genre_thresholds:
            self.pass_threshold = genre_thresholds[genre]
        else:
            self.pass_threshold = default_threshold

    def _load_guard_for_genre(self, genre: str):
        """[V46] 장르에 맞는 Guard 동적 로드"""
        if not genre:
            return None
        try:
            if genre == "wuxia":
                from modules.core.genre_guards.wuxia_guard import WuxiaGuard

                return WuxiaGuard()
            elif genre == "hunter":
                from modules.core.genre_guards.hunter_guard import HunterGuard

                return HunterGuard()
            else:
                return None
        except Exception as e:
            logging.warning(f"[WARNING] Guard 로드 실패 ({genre}): {e}")
            return None

    def _sanitize_manuscript(self, text: str) -> str:
        """
        🔒 Prompt Injection 방지 - 원고 텍스트 sanitization

        1. 중괄호 이스케이프 (f-string KeyError 방지)
        2. 제어 문자 제거
        3. 길이 제한 적용
        """
        if not isinstance(text, str):
            return str(text)

        # 중괄호 이스케이프
        sanitized = text.replace("{", "{{").replace("}", "}}")

        # 제어 문자 제거 (개행/탭 제외)
        sanitized = "".join(char for char in sanitized if char.isprintable() or char in "\n\r\t")

        # 길이 제한 (3000자)
        return sanitized[:3000]

    def validate(self, manuscript: str, validation_context: dict) -> dict:
        """
        SCORING 검증 실행

        Returns:
            {
                "tier": "SCORING",
                "passed": True/False,
                "total_score": int,
                "max_score": 100,
                "percentage": float,
                "threshold": 70,
                "breakdown": {...},
                "message": "..."
            }
        """
        # Python으로 계산 가능한 항목 (LLM 불필요)
        python_scores = self._calculate_python_scores(manuscript, validation_context)

        # LLM으로 평가해야 하는 항목
        llm_scores = self._calculate_llm_scores(manuscript, validation_context)

        # 통합
        all_scores = {**python_scores, **llm_scores}

        # [V69] 값 타입 방어 — LLM이 비정상 구조 반환 시 안전 합산
        total_score = sum(v.get("score", 0) if isinstance(v, dict) else 0 for v in all_scores.values())
        max_score = 100
        passed = total_score >= self.pass_threshold

        return {
            "tier": "SCORING",
            "passed": passed,
            "total_score": total_score,
            "max_score": max_score,
            "percentage": (total_score / max_score) * 100,
            "threshold": self.pass_threshold,
            "breakdown": all_scores,
            "message": f"{'PASS' if passed else 'FAIL'} - {total_score}/{max_score}점 (기준: {self.pass_threshold}점)",
        }

    def _calculate_python_scores(self, manuscript: str, context: dict) -> dict:
        """Python으로 직접 계산 가능한 점수"""
        scores = {}

        # 문장 품질 (20점 중 15점은 Python 계산 가능)
        scores["prose_rhythm"] = self._evaluate_prose_rhythm(manuscript)
        scores["vocabulary_diversity"] = self._evaluate_vocabulary_diversity(manuscript)
        scores["sensory_balance"] = self._evaluate_sensory_balance(manuscript)
        scores["show_dont_tell"] = self._evaluate_show_dont_tell(manuscript)

        return scores

    def _calculate_llm_scores(self, manuscript: str, context: dict) -> dict:
        """LLM으로 평가해야 하는 점수"""
        if not self.client:
            # LLM 없으면 경고 후 fallback (검증 품질 저하)
            logging.warning("[WARNING] LLM client가 없어 Python 기반 fallback 사용 - 검증 정확도 저하")
            logging.warning("[WARNING] Constitutional AI 평가 불가 - 중간 점수로 대체")
            return self._fallback_llm_scores(manuscript, context)

        # 🔒 Prompt Injection 방지 - 원고 텍스트 sanitization
        safe_manuscript = self._sanitize_manuscript(manuscript)

        # [V46] GenreGuard 기반 동적 컨텍스트 생성
        dynamic_context = self._generate_dynamic_context(context)

        # LLM 호출 with Chain-of-Thought
        prompt = f"""
{self.constitution}

다음 원고를 Article 2-7에 따라 평가하십시오:

===== 원고 시작 =====
{safe_manuscript}
===== 원고 끝 =====

{dynamic_context}

[Chain-of-Thought Evaluation Process]
각 Article을 단계별로 평가하십시오:

Step 1: Article 2 (캐릭터 일관성) 분석
- 등장인물의 행동이 설정과 일치하는가?
- 성격 변화에 합리적 근거가 있는가?
- [V46] 위 "주인공 현재 상태"에서 불가능한 행동이 정당화 없이 등장하는가?
→ 점수와 이유 도출

Step 2: Article 3 (감정선) 분석
- 감정 변화가 자연스러운가?
- 독자가 공감할 수 있는 감정 묘사인가?
→ 점수와 이유 도출

Step 3: Article 4 (대화 품질) 분석
- 대사가 캐릭터 특성을 반영하는가?
- 대화가 서사 전개에 기여하는가?
→ 점수와 이유 도출

Step 4: Article 5 (상업성) 분석
- 독자를 끌어당기는 요소가 있는가?
- 다음 화를 기대하게 만드는가?
→ 점수와 이유 도출

Step 5: Article 6 (패턴 다양성) 분석
- 전개 패턴이 신선한가?
- 클리셰를 피하고 있는가?
→ 점수와 이유 도출

Step 6: Article 7 (독자 대리만족) 분석
- 보상 시점(Payoff): 주인공이 성취/승리/인정받는 장면이 있는가? (0~4점)
  장르별 보상 예시: 무협(경지돌파/강자제압/비급획득), 헌터(각성/레이드보상/레어아이템), 투자(의사결정보상/자산성장), 판타지(마법각성/관계보상)
- 주인공 유능함: 자력으로 문제를 해결하는가? 타인 구출 의존이 아닌가? (0~3점)
- 좌절-보상 균형: 좌절만 반복되지 않고, 독자가 공감·기대할 수 있는 감정 묘사가 있는가? (0~3점)
→ 점수와 이유 도출

각 Article의 점수를 JSON으로 반환하십시오:
{{
    "character_consistency": {{"score": X, "max": 15, "reason": "..."}},
    "emotion_arc": {{"score": X, "max": 15, "reason": "..."}},
    "dialogue_quality": {{"score": X, "max": 15, "reason": "..."}},
    "commercial_appeal": {{"score": X, "max": 15, "reason": "..."}},
    "pattern_diversity": {{"score": X, "max": 10, "reason": "..."}},
    "reader_satisfaction": {{"score": X, "max": 10, "reason": "..."}}
}}
"""

        try:
            from google.genai import types

            config = types.GenerateContentConfig(temperature=0.3, response_mime_type="application/json")

            response = self.client.models.generate_content(model=self.model, contents=prompt, config=config)

            import json

            result = json.loads(response.text)

            # [V69] LLM이 list로 감싸서 반환하는 경우 방어
            if isinstance(result, list):
                if len(result) == 1 and isinstance(result[0], dict):
                    result = result[0]
                else:
                    # list 내 dict 찾기
                    for item in result:
                        if isinstance(item, dict) and "character_consistency" in item:
                            result = item
                            break
                    else:
                        logging.warning("[WARNING] LLM이 예상치 못한 list 반환 - Fallback 전환")
                        return self._fallback_llm_scores(manuscript, context)

            if not isinstance(result, dict):
                logging.warning(f"[WARNING] LLM 응답이 dict가 아님 ({type(result).__name__}) - Fallback 전환")
                return self._fallback_llm_scores(manuscript, context)

            # [V70] LLM 점수 클램핑: score가 max를 초과하지 않도록 방어
            for _cat, _val in result.items():
                if isinstance(_val, dict) and "score" in _val and "max" in _val:
                    try:
                        _val["score"] = min(int(_val["score"]), int(_val["max"]))
                    except (ValueError, TypeError):
                        logging.warning(
                            f"[ScoringValidator] 점수 변환 실패: score={_val.get('score')}, max={_val.get('max')} — 0 대입"
                        )
                        _val["score"] = 0

            return result

        except Exception as e:
            logging.warning(f"[WARNING] LLM 평가 실패: {e}")
            logging.warning("[WARNING] Fallback으로 전환 - Constitutional AI 평가 불가")
            return self._fallback_llm_scores(manuscript, context)

    def _fallback_llm_scores(self, manuscript: str, context: dict) -> dict:
        """
        LLM 실패 시 Python 기반 fallback 평가

        주의: Constitutional AI 평가 불가 - 정확도 크게 저하됨
        실제 프로덕션에서는 LLM 호출 필수
        """
        # 간단한 휴리스틱 평가
        ms_length = len(manuscript)

        # 캐릭터 일관성 (길이 기반 단순 추정)
        char_score = min(15, int(ms_length / 300))

        # 감정선 (문장 부호 다양성으로 추정)
        emotion_markers = manuscript.count("!") + manuscript.count("?") + manuscript.count("…")
        emotion_score = min(15, 8 + int(emotion_markers / 5))

        # 대화 품질 (따옴표 빈도로 추정)
        # [V44] 서로 다른 유형의 따옴표 카운트 (직선형 + 곡선형)
        dialogue_count = manuscript.count('"') + manuscript.count("\u201c") + manuscript.count("\u201d")
        dialogue_score = min(15, 5 + int(dialogue_count / 10))

        # 상업성 (길이와 구조로 추정)
        commercial_score = min(15, 8 + int(ms_length / 500))

        # 패턴 다양성 (단순 중간값)
        pattern_score = 6

        # [Phase 3-D1] 독자 대리만족 (단순 중간값)
        satisfaction_score = 5

        return {
            "character_consistency": {"score": char_score, "max": 15, "reason": "⚠️ LLM 없음 - Fallback 추정치"},
            "emotion_arc": {"score": emotion_score, "max": 15, "reason": "⚠️ LLM 없음 - Fallback 추정치"},
            "dialogue_quality": {"score": dialogue_score, "max": 15, "reason": "⚠️ LLM 없음 - Fallback 추정치"},
            "commercial_appeal": {"score": commercial_score, "max": 15, "reason": "⚠️ LLM 없음 - Fallback 추정치"},
            "pattern_diversity": {"score": pattern_score, "max": 10, "reason": "⚠️ LLM 없음 - Fallback 추정치"},
            "reader_satisfaction": {"score": satisfaction_score, "max": 10, "reason": "⚠️ LLM 없음 - Fallback 추정치"},
        }

    # ========================================================================
    # [V46] 동적 컨텍스트 생성
    # ========================================================================

    def _generate_dynamic_context(self, context: dict) -> str:
        """
        [V46] GenreGuard 기반 동적 컨텍스트 생성

        LLM 프롬프트에 삽입할 주인공 상태 및 검증 규칙
        """
        import json

        parts = []

        # 1. 주인공 현재 상태 (HUD actual_truth)
        martial_hud = context.get("martial_hud", {})
        actual_truth = {}
        if isinstance(martial_hud, dict):
            actual_truth = martial_hud.get("actual_truth", martial_hud)

        if actual_truth:
            parts.append("===== [V46] 주인공 현재 상태 =====")
            # 핵심 필드만 추출
            key_fields = [
                "realm",
                "rank",
                "causal_injuries",
                "internal_energy",
                "mana",
                "status",
                "equipment",
                "body_condition",
            ]
            filtered_state = {k: v for k, v in actual_truth.items() if k in key_fields and v}
            if filtered_state:
                try:
                    parts.append(json.dumps(filtered_state, ensure_ascii=False, indent=2))
                except (TypeError, ValueError):  # [V64.P4] JSON serialize fallback
                    parts.append(str(filtered_state))

        # 2. Guard 기반 불가능 행동 목록
        # [FIX] AttributeError 방지 - 메서드 존재 여부 확인
        if self.guard and actual_truth and hasattr(self.guard, "get_impossible_actions"):
            try:
                impossible_actions = self.guard.get_impossible_actions(actual_truth)
                if impossible_actions:
                    parts.append("\n===== 현재 상태로 불가능한 행동 =====")
                    for action in impossible_actions[:5]:  # 최대 5개
                        reason = action.get("reason", "") if isinstance(action, dict) else str(action)
                        parts.append(f"- {reason}")
            except (AttributeError, Exception) as e:
                pass  # Guard 메서드 오류 시 조용히 무시

        # 3. 정당화 인정 패턴
        # [FIX] AttributeError 방지 - 메서드 존재 여부 확인
        if self.guard and hasattr(self.guard, "get_justification_patterns"):
            try:
                justifications = self.guard.get_justification_patterns()
                if justifications:
                    parts.append("\n===== 정당화 시 인정되는 표현 =====")
                    # 정규식을 사람이 읽기 쉽게 변환
                    readable_patterns = []
                    for p in justifications[:5]:
                        readable = p.replace(r".*", "...").replace(r"\s+", " ")
                        readable_patterns.append(f'"{readable}"')
                    parts.append(", ".join(readable_patterns))
            except (AttributeError, Exception) as e:
                pass  # Guard 메서드 오류 시 조용히 무시

        # 4. 검증 지침
        if parts:
            parts.append("\n===== 검증 지침 =====")
            parts.append("위 '불가능한 행동'이 원고에 등장하되 '정당화 표현'이 없다면,")
            parts.append("Article 2 (캐릭터 일관성) 점수를 -3~-5점 감점하십시오.")
            parts.append("단, 정당화 표현이 함께 등장하면 감점하지 마십시오.")

        return "\n".join(parts) if parts else ""

    # ========================================================================
    # Python 기반 평가 메서드
    # ========================================================================

    def _evaluate_prose_rhythm(self, manuscript: str) -> dict:
        """문장 리듬 평가 (CV 계산)"""
        sentences = self._split_sentences(manuscript)
        if len(sentences) < 2:
            return {"score": 3, "max": 5, "reason": "문장 수 부족"}

        lengths = [len(s) for s in sentences]
        mean_len = statistics.mean(lengths)
        std_dev = statistics.stdev(lengths) if len(lengths) > 1 else 0

        # 변동계수 (CV) 계산
        cv = std_dev / mean_len if mean_len > 0 else 0

        # 점수 매기기
        if 0.35 <= cv <= 0.55:
            score = 5
            reason = f"CV={cv:.2f} (이상적)"
        elif 0.30 <= cv < 0.35 or 0.55 < cv <= 0.60:
            score = 4
            reason = f"CV={cv:.2f} (양호)"
        elif 0.25 <= cv < 0.30 or 0.60 < cv <= 0.65:
            score = 3
            reason = f"CV={cv:.2f} (보통)"
        elif 0.20 <= cv < 0.25 or 0.65 < cv <= 0.70:
            score = 2
            reason = f"CV={cv:.2f} (미흡)"
        else:
            score = 1
            reason = f"CV={cv:.2f} (부적합)"

        return {"score": score, "max": 5, "reason": reason, "cv": cv}

    def _evaluate_vocabulary_diversity(self, manuscript: str) -> dict:
        """어휘 다양성 평가 (TTR 계산)"""
        words = self._tokenize(manuscript)
        if len(words) < 10:
            return {"score": 3, "max": 5, "reason": "단어 수 부족 (10단어 미만)"}

        # [V44] TTR 개선: 길이별 차등 적용
        # - 10-50 단어: 기본 점수 보정 (짧은 텍스트 불이익 해소)
        # - 51-200 단어: 직접 계산
        # - 201+ 단어: 샘플링 기반 평균
        short_text_bonus = 0
        if len(words) <= 50:
            # 매우 짧은 텍스트: TTR이 높게 나오기 쉬우므로 보정
            short_text_bonus = -0.05  # 5% 하향 보정
        elif len(words) <= 200:
            short_text_bonus = 0  # 보정 없음

        if len(words) <= 200:
            # 짧은 텍스트: 직접 계산
            unique_words = set(words)
            ttr = len(unique_words) / len(words) + short_text_bonus
            ttr = max(0, ttr)  # 음수 방지
        else:
            # 긴 텍스트: 200단어 윈도우로 샘플링 후 평균
            sample_size = 200
            num_samples = max(1, min(5, len(words) // sample_size))
            ttr_samples = []

            if num_samples > 0:
                step = len(words) // num_samples

                for i in range(num_samples):
                    start = i * step
                    end = min(start + sample_size, len(words))
                    sample = words[start:end]

                    if len(sample) >= 10:  # 최소 10단어 필요
                        sample_ttr = len(set(sample)) / len(sample)
                        ttr_samples.append(sample_ttr)

            # fallback: 샘플이 없으면 전체로 계산
            if not ttr_samples:
                unique_words = set(words)
                ttr = len(unique_words) / len(words)
            else:
                ttr = statistics.mean(ttr_samples)

        # [V44] TTR 범위 정규화 (이론적 범위: 0~1)
        ttr = max(0.0, min(1.0, ttr))

        # 점수 매기기
        if ttr >= 0.40:
            score = 5
            reason = f"TTR={ttr:.2f} (우수)"
        elif ttr >= 0.35:
            score = 4
            reason = f"TTR={ttr:.2f} (양호)"
        elif ttr >= 0.30:
            score = 3
            reason = f"TTR={ttr:.2f} (보통)"
        elif ttr >= 0.25:
            score = 2
            reason = f"TTR={ttr:.2f} (미흡)"
        else:
            score = 1
            reason = f"TTR={ttr:.2f} (부족)"

        # 과다 사용 단어 체크
        word_counts = Counter(words)
        overused = [w for w, c in word_counts.most_common(10) if c > 5]

        if overused:
            reason += f" (과다: {', '.join(overused[:3])})"

        return {"score": score, "max": 5, "reason": reason, "ttr": ttr}

    def _evaluate_sensory_balance(self, manuscript: str) -> dict:
        """오감 묘사 균형 평가"""
        senses = {
            "visual": ["보", "빛", "색", "형", "모습", "눈", "보이"],
            "auditory": ["소리", "들", "울", "고요", "시끄", "귀"],
            "tactile": ["촉", "차가", "따뜻", "부드", "거칠", "아프"],
            "olfactory": ["냄새", "향", "악취", "향기"],
            "gustatory": ["맛", "달", "써", "짜", "시"],
        }

        counts = {}
        for sense, keywords in senses.items():
            counts[sense] = sum(manuscript.count(kw) for kw in keywords)

        total = sum(counts.values())
        if total == 0:
            return {"score": 2, "max": 5, "reason": "감각 묘사 부족"}

        visual_ratio = counts["visual"] / total

        if visual_ratio <= 0.60:
            score = 5
            reason = f"시각 {visual_ratio:.0%} (균형)"
        elif visual_ratio <= 0.70:
            score = 4
            reason = f"시각 {visual_ratio:.0%} (양호)"
        elif visual_ratio <= 0.80:
            score = 3
            reason = f"시각 {visual_ratio:.0%} (편중)"
        elif visual_ratio <= 0.90:
            score = 2
            reason = f"시각 {visual_ratio:.0%} (과다)"
        else:
            score = 1
            reason = f"시각 {visual_ratio:.0%} (극심한 편중)"

        return {"score": score, "max": 5, "reason": reason, "distribution": counts}

    def _evaluate_show_dont_tell(self, manuscript: str) -> dict:
        """
        Show Don't Tell 평가

        [V56] 강화: 패턴 8개 → 22개, 감각 묘사 누락 체크 추가
        """
        # [V56] 확장된 직접 감정/상태 서술 패턴 (22개)
        tell_patterns = {
            "강조부사": [
                r"정말 .+했다",
                r"매우 .+했다",
                r"너무 .+했다",
                r"굉장히 .+했다",
                r"아주 .+했다",
                r"몹시 .+했다",
            ],
            "직접감정": [
                r".+라는 느낌이",
                r"기분이 .+했다",
                r"마음이 .+했다",
                r"기쁨이 .+했다",
                r"분노가 .+했다",
                r"슬픔이 .+했다",
                r"두려움이 .+했다",
            ],
            "약한서술": [
                r"어떻게든 .+했다",
                r"뭔가 .+했다",
                r"그냥 .+했다",
                r"아무튼 .+했다",
            ],
            "설명동사": [
                r"생각했다[.!?\s]",
                r"느꼈다[.!?\s]",
                r"알았다[.!?\s]",
                r"깨달았다[.!?\s]",
            ],
        }

        # 카테고리별 카운트
        category_counts = {}
        total_tell_count = 0

        for category, patterns in tell_patterns.items():
            count = sum(len(re.findall(pattern, manuscript)) for pattern in patterns)
            category_counts[category] = count
            total_tell_count += count

        # 1000자당 직접 서술 횟수
        ratio = total_tell_count / (len(manuscript) / 1000) if len(manuscript) > 0 else 0

        # [V56] 감각 묘사 균형 체크
        sensory_keywords = {
            "visual": ["보았다", "보이", "빛", "색", "형태", "눈에", "모습"],
            "auditory": ["소리", "들렸다", "들었다", "울렸다", "고요", "시끄"],
            "tactile": ["느껴졌다", "차가", "따뜻", "부드", "거칠", "아팠다"],
            "olfactory": ["냄새", "향기", "악취", "향이"],
            "martial": ["기혈", "내공", "기운", "살기", "검기", "파동"],  # 무협 특화
        }

        sensory_counts = {}
        total_sensory = 0
        for sense, keywords in sensory_keywords.items():
            count = sum(manuscript.count(kw) for kw in keywords)
            sensory_counts[sense] = count
            total_sensory += count

        # 감각 묘사 부족 페널티
        sensory_penalty = 0
        if total_sensory < len(manuscript) / 500:  # 500자당 1회 미만
            sensory_penalty = 1
            sensory_note = "감각 묘사 부족"
        elif sensory_counts.get("visual", 0) > total_sensory * 0.7:  # 시각 70% 초과
            sensory_penalty = 0.5
            sensory_note = "시각 편중"
        else:
            sensory_note = "감각 균형 양호"

        # 점수 계산
        if ratio < 1:
            base_score = 5
            reason = f"직접 서술 {ratio:.1f}/1000자 (우수)"
        elif ratio < 2:
            base_score = 4
            reason = f"직접 서술 {ratio:.1f}/1000자 (양호)"
        elif ratio < 3:
            base_score = 3
            reason = f"직접 서술 {ratio:.1f}/1000자 (보통)"
        elif ratio < 4:
            base_score = 2
            reason = f"직접 서술 {ratio:.1f}/1000자 (과다)"
        else:
            base_score = 1
            reason = f"직접 서술 {ratio:.1f}/1000자 (극심)"

        # [V56] 최종 점수 = 기본 점수 - 감각 페널티
        final_score = max(1, base_score - sensory_penalty)

        return {
            "score": final_score,
            "max": 5,
            "reason": f"{reason}, {sensory_note}",
            "ratio": ratio,
            "category_counts": category_counts,
            "sensory_counts": sensory_counts,
            "sensory_penalty": sensory_penalty,
            # [V56] 사전 REJECT 신호 (극심한 경우)
            "pre_reject": ratio > 5 or total_sensory < 3,
        }

    # ========================================================================
    # 유틸리티 메서드
    # ========================================================================

    def _split_sentences(self, text: str) -> list[str]:
        """텍스트를 문장으로 분리"""
        # 간단한 문장 분리 (마침표, 물음표, 느낌표 기준)
        sentences = re.split(r"[.!?]\s+", text)
        return [s.strip() for s in sentences if len(s.strip()) > 0]

    def _tokenize(self, text: str) -> list[str]:
        """텍스트를 단어로 분리"""
        # 한글 단어 추출 (2글자 이상)
        words = re.findall(r"[가-힣]{2,}", text)
        # 불용어 제거
        stopwords = {"것이다", "있다", "없다", "하다", "되다", "이다", "그", "저", "이"}
        return [w for w in words if w not in stopwords]

    # ========================================================================
    # [V59] 장르별 가중치 시스템
    # ========================================================================

    # [V59] 장르별 점수 항목 가중치
    GENRE_WEIGHTS = {
        "wuxia": {
            # 무협: 액션 묘사와 긴장감이 중요
            "prose_rhythm": 1.2,  # 문장 리듬 중요 (전투 장면)
            "vocabulary_diversity": 1.0,
            "sensory_balance": 1.3,  # 감각 묘사 중요 (무술 동작)
            "show_dont_tell": 1.0,
            "character_consistency": 1.0,
            "emotion_arc": 0.9,  # 감정선 약간 덜 중요
            "dialogue_quality": 1.0,
            "commercial_appeal": 1.1,  # 상업성 약간 중요
            "pattern_diversity": 1.1,  # 패턴 다양성 약간 중요
            "reader_satisfaction": 1.3,  # [Phase 3-D1] 무협: 경지돌파/복수 쾌감
        },
        "hunter": {
            # 헌터: 시스템/스킬 묘사와 성장이 중요
            "prose_rhythm": 1.0,
            "vocabulary_diversity": 0.9,
            "sensory_balance": 1.1,  # 스킬 이펙트 묘사
            "show_dont_tell": 1.2,  # 설명 대신 묘사 중요
            "character_consistency": 1.1,
            "emotion_arc": 1.0,
            "dialogue_quality": 0.9,
            "commercial_appeal": 1.3,  # 상업성 매우 중요
            "pattern_diversity": 1.0,
            "reader_satisfaction": 1.2,  # [Phase 3-D1] 헌터: 레벨업/아이템 획득
        },
        "investment": {
            # 투자: 논리적 전개와 긴장감이 중요
            "prose_rhythm": 0.9,
            "vocabulary_diversity": 1.2,  # 금융 용어 다양성
            "sensory_balance": 0.8,  # 감각 묘사 덜 중요
            "show_dont_tell": 1.1,
            "character_consistency": 1.2,  # 인물 일관성 중요
            "emotion_arc": 1.2,  # 감정선 중요 (돈에 대한 감정)
            "dialogue_quality": 1.1,
            "commercial_appeal": 1.0,
            "pattern_diversity": 1.2,  # 패턴 다양성 중요 (뻔한 전개 방지)
            "reader_satisfaction": 0.8,  # [Phase 3-D1] 투자: 서스펜스 위주
        },
    }

    def validate_v59(self, manuscript: str, validation_context: dict) -> dict:
        """
        [V59] 장르별 가중치 적용 + 세분화된 피드백 제공

        Returns:
            {
                "tier": "SCORING",
                "passed": True/False,
                "total_score": int,  # 가중치 적용 후
                "raw_score": int,    # 가중치 적용 전
                "weighted_breakdown": {...},  # 가중치 적용된 세부 점수
                "detailed_feedback": {...},   # 세분화된 피드백
                "improvement_priorities": [...],  # 우선 개선 항목
            }
        """
        # 기본 검증 수행
        base_result = self.validate(manuscript, validation_context)

        # [V59] 장르별 가중치 적용
        genre = self.genre or validation_context.get("genre", "wuxia")
        weights = self.GENRE_WEIGHTS.get(genre, self.GENRE_WEIGHTS["wuxia"])

        weighted_breakdown = {}
        weighted_total = 0
        raw_total = base_result["total_score"]

        for item_name, item_data in base_result["breakdown"].items():
            if not isinstance(item_data, dict):
                continue

            raw_score = item_data.get("score", 0)
            max_score = item_data.get("max", 0)
            weight = weights.get(item_name, 1.0)

            # 가중치 적용
            weighted_score = raw_score * weight
            weighted_max = max_score * weight

            weighted_breakdown[item_name] = {
                **item_data,
                "raw_score": raw_score,
                "weighted_score": round(weighted_score, 1),
                "weight": weight,
                "weighted_max": round(weighted_max, 1),
                "genre_note": self._get_genre_item_note(genre, item_name),
            }
            weighted_total += weighted_score

        # [V59] 세분화된 피드백 생성
        detailed_feedback = self._generate_detailed_feedback(manuscript, weighted_breakdown, genre)

        # [V59] 우선 개선 항목 도출
        improvement_priorities = self._get_improvement_priorities(weighted_breakdown, genre)

        # 가중치 적용된 총점으로 PASS/FAIL 재계산
        weighted_max_total = sum(w.get("weighted_max", 0) for w in weighted_breakdown.values() if isinstance(w, dict))
        if weighted_max_total > 0:
            weighted_percentage = weighted_total / weighted_max_total * 100
        elif raw_total > 0:
            raw_max_total = sum(
                d.get("max", 0) for d in base_result.get("breakdown", {}).values() if isinstance(d, dict)
            )
            logging.warning(f"[ScoringValidator] weighted_max_total=0 — raw_total({raw_total}) 기반 폴백 계산")
            weighted_percentage = (raw_total / max(raw_max_total, 1)) * 100
        else:
            weighted_percentage = 0
        passed = weighted_percentage >= self.pass_threshold

        return {
            "tier": "SCORING",
            "version": "V59",
            "passed": passed,
            "total_score": round(weighted_total, 1),
            "raw_score": raw_total,
            "max_score": round(weighted_max_total, 1),
            "percentage": round(weighted_percentage, 1),
            "threshold": self.pass_threshold,
            "genre": genre,
            "breakdown": base_result["breakdown"],  # 원본 유지
            "weighted_breakdown": weighted_breakdown,
            "detailed_feedback": detailed_feedback,
            "improvement_priorities": improvement_priorities,
            "message": f"{'PASS' if passed else 'FAIL'} - {round(weighted_total, 1)}/{round(weighted_max_total, 1)}점 "
            f"(기준: {self.pass_threshold}%, 장르: {genre})",
        }

    def _get_genre_item_note(self, genre: str, item_name: str) -> str:
        """[V59] 장르별 항목 설명 반환"""
        notes = {
            "wuxia": {
                "prose_rhythm": "무협 전투 장면에서 리듬감 있는 문장이 필수",
                "sensory_balance": "무술 동작과 내공 묘사에 다양한 감각 필요",
                "commercial_appeal": "사이다 요소와 긴장감이 독자 유입에 영향",
                "pattern_diversity": "뻔한 복수극/성장물 패턴 탈피 필요",
                "reader_satisfaction": "경지 돌파, 강자 제압, 비급 획득 등 무협 쾌감",
            },
            "hunter": {
                "show_dont_tell": "스킬/시스템 설명보다 체감 묘사가 중요",
                "commercial_appeal": "레벨업/성장의 쾌감이 핵심 상업성",
                "character_consistency": "헌터/각성자 능력치 일관성 필수",
                "reader_satisfaction": "레벨업, 레어 아이템, 던전 클리어 쾌감",
            },
            "investment": {
                "vocabulary_diversity": "금융 용어와 시장 표현의 다양성",
                "character_consistency": "투자 결정의 논리적 일관성",
                "emotion_arc": "돈과 성공에 대한 감정 변화가 핵심",
                "pattern_diversity": "예측 가능한 성공 패턴 탈피 필요",
                "reader_satisfaction": "투자 성공, 정보 선점, 자산 증가 체감",
            },
        }
        return notes.get(genre, {}).get(item_name, "")

    def _generate_detailed_feedback(self, manuscript: str, breakdown: dict, genre: str) -> dict:
        """[V59] 세분화된 피드백 생성"""
        feedback = {
            "strengths": [],  # 강점
            "weaknesses": [],  # 약점
            "suggestions": [],  # 개선 제안
            "genre_specific": [],  # 장르 특화 피드백
        }

        # 각 항목별 피드백 생성
        for item_name, item_data in breakdown.items():
            if not isinstance(item_data, dict):
                continue

            score = item_data.get("weighted_score", 0)
            max_score = item_data.get("weighted_max", 1)
            ratio = score / max_score if max_score > 0 else 0
            reason = item_data.get("reason", "")

            # 강점/약점 분류
            if ratio >= 0.8:
                feedback["strengths"].append(
                    {
                        "item": item_name,
                        "score": f"{score:.1f}/{max_score:.1f}",
                        "note": self._get_strength_note(item_name, reason),
                    }
                )
            elif ratio < 0.5:
                weakness = {
                    "item": item_name,
                    "score": f"{score:.1f}/{max_score:.1f}",
                    "issue": reason,
                    "suggestion": self._get_improvement_suggestion(item_name, item_data, genre),
                }
                feedback["weaknesses"].append(weakness)
                feedback["suggestions"].append(weakness["suggestion"])

        # 장르 특화 피드백
        genre_feedback = self._get_genre_specific_feedback(manuscript, breakdown, genre)
        feedback["genre_specific"] = genre_feedback

        return feedback

    def _get_strength_note(self, item_name: str, reason: str) -> str:
        """강점 설명 생성"""
        notes = {
            "prose_rhythm": "문장 리듬이 자연스러워 읽기 편합니다",
            "vocabulary_diversity": "다양한 어휘를 사용하여 풍부한 표현력을 보입니다",
            "sensory_balance": "다양한 감각 묘사로 생동감 있는 장면을 연출합니다",
            "show_dont_tell": "직접 설명보다 묘사를 통해 효과적으로 전달합니다",
            "character_consistency": "캐릭터의 행동이 설정과 잘 부합합니다",
            "emotion_arc": "감정 변화가 자연스럽고 공감됩니다",
            "dialogue_quality": "대사가 캐릭터를 잘 드러냅니다",
            "commercial_appeal": "독자를 끄는 매력적인 요소가 있습니다",
            "pattern_diversity": "신선하고 예측하기 어려운 전개입니다",
            "reader_satisfaction": "독자가 대리만족을 느낄 수 있는 장면이 있습니다",
        }
        return notes.get(item_name, reason)

    def _get_improvement_suggestion(self, item_name: str, item_data: dict, genre: str) -> str:
        """개선 제안 생성"""
        suggestions = {
            "prose_rhythm": {
                "default": "문장 길이에 변화를 주세요. 짧은 문장과 긴 문장을 번갈아 사용하면 리듬감이 생깁니다.",
                "wuxia": "전투 장면에서는 짧고 강렬한 문장을, 묘사 장면에서는 긴 문장을 사용해보세요.",
            },
            "vocabulary_diversity": {
                "default": "같은 단어의 반복을 피하고 유의어를 활용하세요.",
                "investment": "금융 용어를 다양하게 활용하되, 설명 없이 남발하지 마세요.",
            },
            "sensory_balance": {
                "default": "시각 외에 청각, 촉각, 후각 묘사를 추가하세요.",
                "wuxia": "내공의 흐름, 검기의 파동, 살기의 무게 같은 무협 특유의 감각을 묘사하세요.",
            },
            "show_dont_tell": {
                "default": '"슬펐다" 대신 "눈물이 볼을 타고 흘렀다"처럼 행동/묘사로 감정을 전달하세요.',
                "hunter": "스킬 설명 대신 사용 시 체감되는 감각으로 묘사하세요.",
            },
            "character_consistency": {
                "default": "캐릭터의 과거 행동과 현재 행동이 일관되게 연결되어야 합니다.",
                "investment": "투자 결정에는 항상 논리적 근거가 있어야 합니다.",
            },
            "emotion_arc": {
                "default": "감정 변화에 계기와 과정을 명시하세요. 갑작스러운 변화는 독자를 놓칩니다.",
                "investment": "돈에 대한 탐욕, 두려움, 희열의 감정을 입체적으로 그리세요.",
            },
            "dialogue_quality": {
                "default": "각 캐릭터만의 말투와 어휘를 설정하세요.",
            },
            "commercial_appeal": {
                "default": "다음 화에 대한 기대감을 유발하는 떡밥이나 클리프행어를 추가하세요.",
                "hunter": "레벨업, 스킬 획득 등 성장의 쾌감을 더 강조하세요.",
            },
            "pattern_diversity": {
                "default": "예상 가능한 전개를 의도적으로 비틀어보세요.",
                "wuxia": '단순 복수극이나 "스승 복수" 패턴을 넘어서는 동기를 부여하세요.',
            },
            "reader_satisfaction": {
                "default": "주인공이 성취/승리/성장하는 장면을 추가하세요. 독자가 대리만족을 느낄 수 있어야 합니다.",
                "wuxia": "경지 돌파, 강자 제압, 비급 획득 등 무협 특유의 쾌감 장면을 삽입하세요.",
                "hunter": "레벨업, 레어 아이템 획득, 던전 클리어 등 성장 쾌감을 강조하세요.",
            },
        }

        item_suggestions = suggestions.get(item_name, {})
        return item_suggestions.get(genre, item_suggestions.get("default", "이 항목을 개선해주세요."))

    def _get_genre_specific_feedback(self, manuscript: str, breakdown: dict, genre: str) -> list[str]:
        """장르 특화 피드백 생성"""
        feedback = []

        if genre == "wuxia":
            # 무협 특화 체크
            martial_keywords = ["내공", "검기", "장풍", "경공", "비급", "검법", "장법"]
            martial_count = sum(manuscript.count(kw) for kw in martial_keywords)
            if martial_count < 3:
                feedback.append("무협 장르임에도 무술 관련 묘사(내공, 검기 등)가 부족합니다.")

            # 클리셰 체크
            cliche_patterns = ["피가 끓어오르", "복수의 칼날", "스승의 원수"]
            cliche_count = sum(1 for p in cliche_patterns if p in manuscript)
            if cliche_count >= 2:
                feedback.append("무협 클리셰 표현이 다수 발견됩니다. 신선한 표현을 시도해보세요.")

        elif genre == "hunter":
            # 헌터 특화 체크
            system_keywords = ["레벨", "스킬", "스탯", "던전", "게이트", "마나", "각성"]
            system_count = sum(manuscript.count(kw) for kw in system_keywords)
            if system_count < 5:
                feedback.append("헌터 장르 특유의 시스템 요소(스킬, 레벨, 던전 등) 언급이 부족합니다.")

            # 성장 묘사 체크
            growth_patterns = ["강해졌", "올랐다", "상승", "레벨업", "각성"]
            if not any(p in manuscript for p in growth_patterns):
                feedback.append("성장/강화 묘사가 부족합니다. 헌터물의 핵심 재미 요소입니다.")

        elif genre == "investment":
            # 투자 특화 체크
            finance_keywords = ["주식", "투자", "수익", "시장", "매수", "매도", "차트"]
            finance_count = sum(manuscript.count(kw) for kw in finance_keywords)
            if finance_count < 3:
                feedback.append("투자 장르임에도 금융/투자 관련 용어가 부족합니다.")

            # 논리적 설명 체크
            explanation_patterns = ["때문에", "왜냐하면", "따라서", "결과적으로"]
            if not any(p in manuscript for p in explanation_patterns):
                feedback.append("투자 결정의 논리적 근거 설명이 부족합니다.")

        return feedback

    def _get_improvement_priorities(self, breakdown: dict, genre: str) -> list[dict]:
        """[V59] 우선 개선 항목 도출 (가중치 × 부족분 기준)"""
        priorities = []

        weights = self.GENRE_WEIGHTS.get(genre, self.GENRE_WEIGHTS["wuxia"])

        for item_name, item_data in breakdown.items():
            if not isinstance(item_data, dict):
                continue

            score = item_data.get("weighted_score", 0)
            max_score = item_data.get("weighted_max", 1)
            weight = weights.get(item_name, 1.0)

            # 부족분 계산 (가중치 반영)
            deficit = (max_score - score) * weight

            if deficit > 0:
                priorities.append(
                    {
                        "item": item_name,
                        "deficit": round(deficit, 2),
                        "weight": weight,
                        "current_ratio": round(score / max_score * 100, 1) if max_score > 0 else 0,
                        "genre_importance": "높음" if weight > 1.1 else ("중간" if weight >= 1.0 else "낮음"),
                    }
                )

        # 부족분 기준 정렬 (큰 것부터)
        priorities.sort(key=lambda x: x["deficit"], reverse=True)

        return priorities[:5]  # 상위 5개만 반환
