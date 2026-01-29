"""
[V0128] TIER 2: SCORING Validator
LLM 기반 점수 평가 (가중치 합산)
"""
import statistics
import re
from typing import Dict, List, Any
from collections import Counter


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
        'wuxia': 70,      # 무협: 기본값
        'hunter': 68,     # 헌터: 액션 위주로 약간 낮게
        'investment': 72  # 투자: 논리성 중요로 약간 높게
    }

    def __init__(self, client=None, model="gemini-2.5-pro", constitution="",
                 pass_threshold: int = None, genre: str = None):
        self.client = client
        self.model = model
        self.constitution = constitution
        self.genre = genre  # [V46] 장르 저장

        # [V46] GenreGuard 동적 로드
        self.guard = self._load_guard_for_genre(genre)

        # [V44] 설정 가능한 PASS_THRESHOLD
        if pass_threshold is not None:
            self.pass_threshold = pass_threshold
        elif genre and genre in self.GENRE_THRESHOLDS:
            self.pass_threshold = self.GENRE_THRESHOLDS[genre]
        else:
            self.pass_threshold = self.DEFAULT_PASS_THRESHOLD

    def _load_guard_for_genre(self, genre: str):
        """[V46] 장르에 맞는 Guard 동적 로드"""
        if not genre:
            return None
        try:
            if genre == 'wuxia':
                from modules.core.genre_guards.wuxia_guard import WuxiaGuard
                return WuxiaGuard()
            elif genre == 'hunter':
                from modules.core.genre_guards.hunter_guard import HunterGuard
                return HunterGuard()
            else:
                return None
        except Exception as e:
            print(f"[WARNING] Guard 로드 실패 ({genre}): {e}")
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
        sanitized = ''.join(char for char in sanitized if char.isprintable() or char in '\n\r\t')

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

        total_score = sum(score['score'] for score in all_scores.values())
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
            "message": f"{'PASS' if passed else 'FAIL'} - {total_score}/{max_score}점 (기준: {self.pass_threshold}점)"
        }

    def _calculate_python_scores(self, manuscript: str, context: dict) -> dict:
        """Python으로 직접 계산 가능한 점수"""
        scores = {}

        # 문장 품질 (20점 중 15점은 Python 계산 가능)
        scores['prose_rhythm'] = self._evaluate_prose_rhythm(manuscript)
        scores['vocabulary_diversity'] = self._evaluate_vocabulary_diversity(manuscript)
        scores['sensory_balance'] = self._evaluate_sensory_balance(manuscript)
        scores['show_dont_tell'] = self._evaluate_show_dont_tell(manuscript)

        return scores

    def _calculate_llm_scores(self, manuscript: str, context: dict) -> dict:
        """LLM으로 평가해야 하는 점수"""
        if not self.client:
            # LLM 없으면 경고 후 fallback (검증 품질 저하)
            print("[WARNING] LLM client가 없어 Python 기반 fallback 사용 - 검증 정확도 저하")
            print("[WARNING] Constitutional AI 평가 불가 - 중간 점수로 대체")
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

각 Article의 점수를 JSON으로 반환하십시오:
{{
    "character_consistency": {{"score": X, "max": 15, "reason": "..."}},
    "emotion_arc": {{"score": X, "max": 20, "reason": "..."}},
    "dialogue_quality": {{"score": X, "max": 15, "reason": "..."}},
    "commercial_appeal": {{"score": X, "max": 20, "reason": "..."}},
    "pattern_diversity": {{"score": X, "max": 10, "reason": "..."}}
}}
"""

        try:
            from google.genai import types

            config = types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json"
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config
            )

            import json
            result = json.loads(response.text)
            return result

        except Exception as e:
            print(f"[ERROR] LLM 평가 실패: {e}")
            print(f"[WARNING] Fallback으로 전환 - Constitutional AI 평가 불가")
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
        emotion_markers = manuscript.count('!') + manuscript.count('?') + manuscript.count('…')
        emotion_score = min(20, 10 + int(emotion_markers / 5))

        # 대화 품질 (따옴표 빈도로 추정)
        # [V44] 서로 다른 유형의 따옴표 카운트 (직선형 + 곡선형)
        dialogue_count = manuscript.count('"') + manuscript.count('\u201C') + manuscript.count('\u201D')
        dialogue_score = min(15, 5 + int(dialogue_count / 10))

        # 상업성 (길이와 구조로 추정)
        commercial_score = min(20, 10 + int(ms_length / 500))

        # 패턴 다양성 (단순 중간값)
        pattern_score = 6

        return {
            'character_consistency': {
                'score': char_score,
                'max': 15,
                'reason': '⚠️ LLM 없음 - Fallback 추정치'
            },
            'emotion_arc': {
                'score': emotion_score,
                'max': 20,
                'reason': '⚠️ LLM 없음 - Fallback 추정치'
            },
            'dialogue_quality': {
                'score': dialogue_score,
                'max': 15,
                'reason': '⚠️ LLM 없음 - Fallback 추정치'
            },
            'commercial_appeal': {
                'score': commercial_score,
                'max': 20,
                'reason': '⚠️ LLM 없음 - Fallback 추정치'
            },
            'pattern_diversity': {
                'score': pattern_score,
                'max': 10,
                'reason': '⚠️ LLM 없음 - Fallback 추정치'
            }
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
        martial_hud = context.get('martial_hud', {})
        actual_truth = {}
        if isinstance(martial_hud, dict):
            actual_truth = martial_hud.get('actual_truth', martial_hud)

        if actual_truth:
            parts.append("===== [V46] 주인공 현재 상태 =====")
            # 핵심 필드만 추출
            key_fields = ['realm', 'rank', 'causal_injuries', 'internal_energy',
                          'mana', 'status', 'equipment', 'body_condition']
            filtered_state = {k: v for k, v in actual_truth.items()
                              if k in key_fields and v}
            if filtered_state:
                try:
                    parts.append(json.dumps(filtered_state, ensure_ascii=False, indent=2))
                except:
                    parts.append(str(filtered_state))

        # 2. Guard 기반 불가능 행동 목록
        if self.guard and actual_truth:
            impossible_actions = self.guard.get_impossible_actions(actual_truth)
            if impossible_actions:
                parts.append("\n===== 현재 상태로 불가능한 행동 =====")
                for action in impossible_actions[:5]:  # 최대 5개
                    reason = action.get('reason', '')
                    parts.append(f"- {reason}")

        # 3. 정당화 인정 패턴
        if self.guard:
            justifications = self.guard.get_justification_patterns()
            if justifications:
                parts.append("\n===== 정당화 시 인정되는 표현 =====")
                # 정규식을 사람이 읽기 쉽게 변환
                readable_patterns = []
                for p in justifications[:5]:
                    readable = p.replace(r'.*', '...').replace(r'\s+', ' ')
                    readable_patterns.append(f'"{readable}"')
                parts.append(', '.join(readable_patterns))

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
            return {'score': 3, 'max': 5, 'reason': '문장 수 부족'}

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

        return {'score': score, 'max': 5, 'reason': reason, 'cv': cv}

    def _evaluate_vocabulary_diversity(self, manuscript: str) -> dict:
        """어휘 다양성 평가 (TTR 계산)"""
        words = self._tokenize(manuscript)
        if len(words) < 10:
            return {'score': 3, 'max': 5, 'reason': '단어 수 부족 (10단어 미만)'}

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

        return {'score': score, 'max': 5, 'reason': reason, 'ttr': ttr}

    def _evaluate_sensory_balance(self, manuscript: str) -> dict:
        """오감 묘사 균형 평가"""
        senses = {
            "visual": ["보", "빛", "색", "형", "모습", "눈", "보이"],
            "auditory": ["소리", "들", "울", "고요", "시끄", "귀"],
            "tactile": ["촉", "차가", "따뜻", "부드", "거칠", "아프"],
            "olfactory": ["냄새", "향", "악취", "향기"],
            "gustatory": ["맛", "달", "써", "짜", "시"]
        }

        counts = {}
        for sense, keywords in senses.items():
            counts[sense] = sum(manuscript.count(kw) for kw in keywords)

        total = sum(counts.values())
        if total == 0:
            return {'score': 2, 'max': 5, 'reason': '감각 묘사 부족'}

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

        return {'score': score, 'max': 5, 'reason': reason, 'distribution': counts}

    def _evaluate_show_dont_tell(self, manuscript: str) -> dict:
        """Show Don't Tell 평가"""
        # 직접 감정 서술 패턴
        tell_patterns = [
            r'정말 .+했다',
            r'매우 .+했다',
            r'너무 .+했다',
            r'굉장히 .+했다',
            r'.+라는 느낌이',
            r'기분이 .+했다',
            r'마음이 .+했다'
        ]

        tell_count = sum(len(re.findall(pattern, manuscript)) for pattern in tell_patterns)

        # 1000자당 직접 서술 횟수
        ratio = tell_count / (len(manuscript) / 1000) if len(manuscript) > 0 else 0

        if ratio < 1:
            score = 5
            reason = f"직접 서술 {ratio:.1f}/1000자 (우수)"
        elif ratio < 2:
            score = 4
            reason = f"직접 서술 {ratio:.1f}/1000자 (양호)"
        elif ratio < 3:
            score = 3
            reason = f"직접 서술 {ratio:.1f}/1000자 (보통)"
        elif ratio < 4:
            score = 2
            reason = f"직접 서술 {ratio:.1f}/1000자 (과다)"
        else:
            score = 1
            reason = f"직접 서술 {ratio:.1f}/1000자 (극심)"

        return {'score': score, 'max': 5, 'reason': reason, 'ratio': ratio}

    # ========================================================================
    # 유틸리티 메서드
    # ========================================================================

    def _split_sentences(self, text: str) -> List[str]:
        """텍스트를 문장으로 분리"""
        # 간단한 문장 분리 (마침표, 물음표, 느낌표 기준)
        sentences = re.split(r'[.!?]\s+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 0]

    def _tokenize(self, text: str) -> List[str]:
        """텍스트를 단어로 분리"""
        # 한글 단어 추출 (2글자 이상)
        words = re.findall(r'[가-힣]{2,}', text)
        # 불용어 제거
        stopwords = {'것이다', '있다', '없다', '하다', '되다', '이다', '그', '저', '이'}
        return [w for w in words if w not in stopwords]
