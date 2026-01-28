# 글도비 V0128 MANIFESTO

## AI 소설 제작 시스템 설계서

**시스템명**: 글도비
**버전**: V0128
**목표**: 250화 연재 시 설정 붕괴율 0% + 문학적 품질 확보
**예산**: 프로젝트당 최대 50만원
**지원 장르**: 무협, 헌터, 투자 (확장 가능)

---

## 1. Executive Summary

### 1.1 핵심 설계 원칙

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         글도비 V0128 핵심 원칙                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. Volume 계층 제거 → Arc가 최상위 계획 단위                               │
│  2. RAG 기반 직접 참조 → 합본 원문에서 관련 장면 직접 검색                  │
│  3. 계층화된 검증 → BLOCKING / SCORING / ADVISORY 분리                      │
│  4. 품질 다차원 평가 → 일관성 + 문장력 + 감정선 + 상업성                    │
│  5. 장르 독립 아키텍처 → 핵심 로직은 동일, 설정만 분리                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 검증 과다 문제 해결: 3-Tier Validation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    3-TIER VALIDATION SYSTEM                                  │
│                    (검증 과다로 인한 통과율 저하 방지)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TIER 1: BLOCKING (차단)                                            │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │  • 실패 시 REJECT → 반드시 수정 필요                                │   │
│  │  • 항목: 설정 붕괴, 사망 NPC 재등장, 미획득 아이템 사용              │   │
│  │  • 목표: 최소한의 핵심 일관성만 강제                                 │   │
│  │  • 검증 수: 5개 이하 (엄선)                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ↓ PASS                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TIER 2: SCORING (점수화)                                           │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │  • 점수 합산 → 임계값 이상이면 PASS                                 │   │
│  │  • 항목: 문장력, 감정선, 페이싱, 대화품질, 패턴다양성 등            │   │
│  │  • 가중치 적용 → 중요도에 따라 차등                                 │   │
│  │  • 70점 이상 PASS (조정 가능)                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ↓ PASS                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TIER 3: ADVISORY (권고)                                            │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │  • 통과에 영향 없음 → 개선 제안만 제공                              │   │
│  │  • 항목: 더 나은 표현 제안, 스타일 힌트, 미세 조정                  │   │
│  │  • 로그로 기록 → 추후 학습/개선용                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  결과: BLOCKING만 통과하면 최소 PASS                                        │
│        SCORING 높으면 고품질 PASS                                           │
│        ADVISORY는 참고용                                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 예상 통과율

| 시나리오 | 예상 통과율 | 설명 |
|----------|------------|------|
| BLOCKING만 적용 | 90-95% | 핵심 설정만 체크 |
| BLOCKING + SCORING 70점 | 80-85% | 품질 기준 포함 |
| 기존 방식 (전부 BLOCKING) | 50-60% | 과다 검증으로 병목 |

---

## 2. 품질 평가 체계 (Quality Evaluation Framework)

### 2.1 전체 품질 차원

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         품질 평가 7대 차원                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [일관성 차원] ─────────────────────────────────────────────────────────    │
│  │                                                                          │
│  ├─ 1. SETTING CONSISTENCY (설정 일관성) ............... BLOCKING          │
│  │     └─ NPC/아이템/장소/HUD 일관성                                       │
│  │                                                                          │
│  ├─ 2. CHARACTER CONSISTENCY (캐릭터 일관성) ........... SCORING           │
│  │     └─ 성격/말투/행동 패턴 일관성                                       │
│  │                                                                          │
│  [문학성 차원] ─────────────────────────────────────────────────────────    │
│  │                                                                          │
│  ├─ 3. PROSE QUALITY (문장 품질) ....................... SCORING           │
│  │     └─ 문장력/어휘/리듬/묘사력                                          │
│  │                                                                          │
│  ├─ 4. EMOTIONAL ARC (감정선) .......................... SCORING           │
│  │     └─ 몰입도/긴장감/카타르시스                                         │
│  │                                                                          │
│  ├─ 5. DIALOGUE QUALITY (대화 품질) .................... SCORING           │
│  │     └─ 캐릭터 음성/서브텍스트/자연스러움                                │
│  │                                                                          │
│  [상업성 차원] ─────────────────────────────────────────────────────────    │
│  │                                                                          │
│  ├─ 6. COMMERCIAL APPEAL (상업성) ...................... SCORING           │
│  │     └─ 후킹/클리프행어/사이다 타이밍                                    │
│  │                                                                          │
│  └─ 7. ORIGINALITY (신선함) ............................ ADVISORY          │
│        └─ 클리셰 회피/창의적 전개                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 TIER 1: BLOCKING 검증 (5개 - 엄선)

```python
class BlockingValidator:
    """
    TIER 1: 반드시 통과해야 하는 핵심 검증

    실패 시 즉시 REJECT - 수정 필수
    최소한의 항목만 포함하여 통과율 유지
    """

    BLOCKING_CHECKS = {
        # 1. 사망 NPC 재등장
        "dead_npc_resurrection": {
            "description": "사망한 NPC가 살아서 등장",
            "severity": "CRITICAL",
            "auto_fixable": False
        },

        # 2. 미획득 아이템 사용
        "unowned_item_usage": {
            "description": "소유하지 않은 아이템 사용",
            "severity": "CRITICAL",
            "auto_fixable": False
        },

        # 3. 파괴된 장소 방문
        "destroyed_location_visit": {
            "description": "파괴된 장소를 정상적으로 방문",
            "severity": "CRITICAL",
            "auto_fixable": False
        },

        # 4. 분량 미달
        "minimum_length": {
            "description": "최소 분량 4,000자 미달",
            "severity": "CRITICAL",
            "auto_fixable": False,  # Writer가 재작성
            "threshold": 4000
        },

        # 5. 필수 씬 누락
        "required_scenes_missing": {
            "description": "블루프린트 필수 씬 미반영",
            "severity": "HIGH",
            "auto_fixable": False,
            "min_scenes": 4
        }
    }

    def validate(self, manuscript: str, context: dict) -> dict:
        """BLOCKING 검증 실행"""
        failures = []

        for check_name, config in self.BLOCKING_CHECKS.items():
            result = self._run_check(check_name, manuscript, context)
            if not result['passed']:
                failures.append({
                    "check": check_name,
                    "reason": result['reason'],
                    "severity": config['severity']
                })

        return {
            "tier": "BLOCKING",
            "passed": len(failures) == 0,
            "failures": failures,
            "message": "REJECT - 필수 수정 필요" if failures else "PASS"
        }
```

### 2.3 TIER 2: SCORING 검증 (가중치 기반)

```python
class ScoringValidator:
    """
    TIER 2: 점수 기반 품질 평가

    각 항목별 점수 합산 → 임계값 이상이면 PASS
    개별 항목 실패해도 다른 항목으로 보완 가능
    """

    SCORING_CRITERIA = {
        # ═══════════════════════════════════════════════════════════════
        # 캐릭터 일관성 (15점 만점)
        # ═══════════════════════════════════════════════════════════════
        "character_voice_consistency": {
            "weight": 5,
            "description": "NPC 말투 일관성"
        },
        "character_behavior_consistency": {
            "weight": 5,
            "description": "NPC 행동 패턴 일관성"
        },
        "character_deviation_check": {
            "weight": 5,
            "description": "캐릭터 일탈 여부 (엄근진 울며 굴복 등)"
        },

        # ═══════════════════════════════════════════════════════════════
        # 문장 품질 (20점 만점)
        # ═══════════════════════════════════════════════════════════════
        "prose_rhythm": {
            "weight": 5,
            "description": "문장 길이 변화율 (단조로움 방지)"
        },
        "vocabulary_diversity": {
            "weight": 5,
            "description": "어휘 다양성 (동일 단어 반복 방지)"
        },
        "sensory_balance": {
            "weight": 5,
            "description": "오감 묘사 균형"
        },
        "show_dont_tell": {
            "weight": 5,
            "description": "직접 서술 vs 묘사 비율"
        },

        # ═══════════════════════════════════════════════════════════════
        # 감정선 (20점 만점)
        # ═══════════════════════════════════════════════════════════════
        "emotion_arc_flow": {
            "weight": 7,
            "description": "감정 곡선 자연스러움"
        },
        "tension_management": {
            "weight": 7,
            "description": "긴장감 관리"
        },
        "catharsis_timing": {
            "weight": 6,
            "description": "카타르시스 타이밍"
        },

        # ═══════════════════════════════════════════════════════════════
        # 대화 품질 (15점 만점)
        # ═══════════════════════════════════════════════════════════════
        "dialogue_naturalness": {
            "weight": 5,
            "description": "대화 자연스러움"
        },
        "dialogue_subtext": {
            "weight": 5,
            "description": "서브텍스트 존재 여부"
        },
        "dialogue_balance": {
            "weight": 5,
            "description": "대화 턴 균형 (독백 방지)"
        },

        # ═══════════════════════════════════════════════════════════════
        # 상업성 (20점 만점)
        # ═══════════════════════════════════════════════════════════════
        "hook_quality": {
            "weight": 7,
            "description": "화 시작 후킹력"
        },
        "cliffhanger_effectiveness": {
            "weight": 7,
            "description": "화 끝 클리프행어"
        },
        "reward_timing": {
            "weight": 6,
            "description": "보상(획득/성장/인정) 타이밍"
        },

        # ═══════════════════════════════════════════════════════════════
        # 패턴 다양성 (10점 만점)
        # ═══════════════════════════════════════════════════════════════
        "narrative_pattern_diversity": {
            "weight": 4,
            "description": "서사 패턴 다양성"
        },
        "reaction_pattern_diversity": {
            "weight": 3,
            "description": "리액션 패턴 다양성"
        },
        "scene_length_variance": {
            "weight": 3,
            "description": "씬 길이 다양성"
        }
    }

    # 총점: 100점
    PASS_THRESHOLD = 70  # 70점 이상 PASS

    def validate(self, manuscript: str, context: dict) -> dict:
        """SCORING 검증 실행"""
        scores = {}
        total_score = 0
        max_score = sum(c['weight'] for c in self.SCORING_CRITERIA.values())

        for criterion, config in self.SCORING_CRITERIA.items():
            score = self._evaluate_criterion(criterion, manuscript, context)
            scores[criterion] = {
                "score": score,
                "max": config['weight'],
                "percentage": (score / config['weight']) * 100
            }
            total_score += score

        passed = total_score >= self.PASS_THRESHOLD

        return {
            "tier": "SCORING",
            "passed": passed,
            "total_score": total_score,
            "max_score": max_score,
            "percentage": (total_score / max_score) * 100,
            "threshold": self.PASS_THRESHOLD,
            "breakdown": scores,
            "message": f"{'PASS' if passed else 'FAIL'} - {total_score}/{max_score}점"
        }
```

### 2.4 TIER 3: ADVISORY 권고

```python
class AdvisoryValidator:
    """
    TIER 3: 개선 권고 (통과에 영향 없음)

    더 나은 원고를 위한 제안 제공
    로그로 기록하여 추후 분석/학습용
    """

    ADVISORY_CHECKS = {
        # 클리셰 감지
        "cliche_detection": {
            "description": "진부한 전개 감지",
            "examples": ["기절했다 깨보니", "알고보니 천재", "숨겨진 혈통"]
        },

        # 더 나은 표현 제안
        "expression_enhancement": {
            "description": "더 강렬한 표현 제안",
            "type": "suggestion"
        },

        # 복선 기회
        "foreshadowing_opportunity": {
            "description": "복선 심기 좋은 지점",
            "type": "opportunity"
        },

        # 캐릭터 심화 기회
        "character_depth_opportunity": {
            "description": "캐릭터 깊이 추가 가능 지점",
            "type": "opportunity"
        },

        # 페이싱 미세 조정
        "pacing_suggestion": {
            "description": "페이싱 미세 조정 제안",
            "type": "suggestion"
        }
    }

    def validate(self, manuscript: str, context: dict) -> dict:
        """ADVISORY 검증 실행"""
        suggestions = []

        for check_name, config in self.ADVISORY_CHECKS.items():
            result = self._analyze(check_name, manuscript, context)
            if result['has_suggestion']:
                suggestions.append({
                    "type": check_name,
                    "suggestion": result['suggestion'],
                    "location": result.get('location', 'general')
                })

        return {
            "tier": "ADVISORY",
            "passed": True,  # 항상 PASS
            "suggestions": suggestions,
            "message": f"{len(suggestions)}개 개선 제안"
        }
```

---

## 3. 품질 평가 상세 모듈

### 3.1 감정선 평가 (Emotion Arc)

```python
class EmotionArcEvaluator:
    """
    감정선 평가 모듈

    화별 감정 곡선을 추적하고 단조로움을 방지합니다.
    """

    # 감정 상태 정의
    EMOTION_STATES = {
        "tension": ["긴장", "위기", "공포", "불안", "초조"],
        "relief": ["안도", "휴식", "평화", "여유"],
        "excitement": ["흥분", "기대", "설렘", "열정"],
        "sadness": ["슬픔", "비통", "상실", "이별"],
        "anger": ["분노", "격분", "울분", "복수심"],
        "joy": ["기쁨", "환희", "승리감", "성취감"],
        "curiosity": ["호기심", "의문", "탐구", "발견"]
    }

    def evaluate_emotion_arc(self, manuscript: str, context: dict) -> dict:
        """감정 곡선 평가"""

        # 씬별 감정 추출
        scenes = self._split_into_scenes(manuscript)
        emotion_sequence = []

        for scene in scenes:
            dominant_emotion = self._detect_dominant_emotion(scene)
            intensity = self._measure_intensity(scene)
            emotion_sequence.append({
                "emotion": dominant_emotion,
                "intensity": intensity
            })

        # 평가 기준
        scores = {
            "variety": self._check_emotion_variety(emotion_sequence),
            "flow": self._check_emotion_flow(emotion_sequence),
            "climax": self._check_climax_presence(emotion_sequence),
            "resolution": self._check_resolution(emotion_sequence)
        }

        return {
            "sequence": emotion_sequence,
            "scores": scores,
            "total": sum(scores.values()) / len(scores) * 10,
            "suggestions": self._generate_suggestions(emotion_sequence, scores)
        }

    def _check_emotion_variety(self, sequence: list) -> float:
        """감정 다양성 체크 (0-1)"""
        emotions = [s['emotion'] for s in sequence]
        unique_emotions = len(set(emotions))
        # 6개 씬에 최소 3가지 감정
        return min(1.0, unique_emotions / 3)

    def _check_emotion_flow(self, sequence: list) -> float:
        """감정 흐름 자연스러움 (0-1)"""
        # 급격한 감정 변화 페널티
        penalties = 0
        for i in range(1, len(sequence)):
            prev = sequence[i-1]
            curr = sequence[i]

            # 정반대 감정으로 급변 (기쁨 → 슬픔)
            if self._is_opposite_emotion(prev['emotion'], curr['emotion']):
                if abs(prev['intensity'] - curr['intensity']) > 0.5:
                    penalties += 0.2

        return max(0, 1.0 - penalties)

    def _check_climax_presence(self, sequence: list) -> float:
        """클라이맥스 존재 여부 (0-1)"""
        intensities = [s['intensity'] for s in sequence]
        max_intensity = max(intensities)
        max_index = intensities.index(max_intensity)

        # 클라이맥스가 후반부(60% 이후)에 있으면 좋음
        position_score = max_index / len(intensities)
        intensity_score = max_intensity

        if position_score >= 0.6:
            return (position_score + intensity_score) / 2
        return intensity_score * 0.7


class CatharsisTimer:
    """
    카타르시스(사이다) 타이밍 관리

    답답한 전개가 너무 길어지지 않도록 관리합니다.
    """

    MAX_FRUSTRATION_EPISODES = 3  # 최대 연속 답답함 허용

    def check_catharsis_timing(self, ep_num: int, manuscript: str,
                               history: list) -> dict:
        """카타르시스 타이밍 체크"""

        # 현재 화의 카타르시스 요소 감지
        has_catharsis = self._detect_catharsis(manuscript)

        # 최근 답답한 전개 연속 횟수
        frustration_streak = self._count_frustration_streak(history)

        if frustration_streak >= self.MAX_FRUSTRATION_EPISODES and not has_catharsis:
            return {
                "status": "warning",
                "streak": frustration_streak,
                "message": f"연속 {frustration_streak}화 답답한 전개. 사이다 필요.",
                "suggestion": "이번 화에 작은 승리/인정/보상 요소 추가 권장"
            }

        return {
            "status": "ok",
            "streak": frustration_streak if not has_catharsis else 0,
            "has_catharsis": has_catharsis
        }

    def _detect_catharsis(self, manuscript: str) -> bool:
        """카타르시스 요소 감지"""
        catharsis_indicators = [
            "통쾌", "시원", "승리", "인정", "감탄", "경악",
            "꿇", "굴복", "사과", "보상", "획득", "성장",
            "돌파", "각성", "깨달음"
        ]
        return any(indicator in manuscript for indicator in catharsis_indicators)
```

### 3.2 문장 품질 평가 (Prose Quality)

```python
class ProseQualityEvaluator:
    """
    문장 품질 평가 모듈
    """

    def evaluate_prose_rhythm(self, manuscript: str) -> dict:
        """문장 리듬 평가"""
        sentences = self._split_sentences(manuscript)
        lengths = [len(s) for s in sentences]

        # 표준편차가 너무 낮으면 단조로움
        import statistics
        std_dev = statistics.stdev(lengths) if len(lengths) > 1 else 0
        mean_len = statistics.mean(lengths)

        # 변동계수 (CV) 계산
        cv = std_dev / mean_len if mean_len > 0 else 0

        # CV가 0.3-0.6 사이가 이상적
        if 0.3 <= cv <= 0.6:
            score = 5
        elif 0.2 <= cv < 0.3 or 0.6 < cv <= 0.7:
            score = 4
        elif cv < 0.2:
            score = 2  # 너무 단조로움
        else:
            score = 3  # 너무 들쭉날쭉

        return {
            "score": score,
            "cv": cv,
            "mean_length": mean_len,
            "std_dev": std_dev,
            "suggestion": self._rhythm_suggestion(cv)
        }

    def evaluate_vocabulary_diversity(self, manuscript: str) -> dict:
        """어휘 다양성 평가"""
        words = self._tokenize(manuscript)

        # Type-Token Ratio
        unique_words = set(words)
        ttr = len(unique_words) / len(words) if words else 0

        # 반복 단어 감지
        from collections import Counter
        word_counts = Counter(words)
        overused = [w for w, c in word_counts.items()
                   if c > 5 and w not in self.ALLOWED_REPEATS]

        score = 5 if ttr > 0.4 and len(overused) == 0 else \
                4 if ttr > 0.35 else \
                3 if ttr > 0.3 else 2

        return {
            "score": score,
            "ttr": ttr,
            "overused_words": overused[:5],
            "suggestion": f"과다 사용 단어: {', '.join(overused[:3])}" if overused else None
        }

    def evaluate_sensory_balance(self, manuscript: str) -> dict:
        """오감 묘사 균형 평가"""
        senses = {
            "visual": ["보", "빛", "색", "형", "모습", "눈"],
            "auditory": ["소리", "들", "울", "고요", "시끄"],
            "tactile": ["촉", "차가", "따뜻", "부드", "거칠", "아프"],
            "olfactory": ["냄새", "향", "악취", "향기"],
            "gustatory": ["맛", "달", "써", "짜", "시"]
        }

        counts = {}
        for sense, keywords in senses.items():
            counts[sense] = sum(1 for kw in keywords if kw in manuscript)

        total = sum(counts.values())
        if total == 0:
            return {"score": 2, "message": "감각 묘사 부족"}

        # 시각 편중도 체크
        visual_ratio = counts["visual"] / total

        if visual_ratio > 0.8:
            score = 2
            suggestion = "시각 외 다른 감각 묘사 추가 권장"
        elif visual_ratio > 0.6:
            score = 3
            suggestion = "청각/촉각 묘사 추가하면 좋음"
        else:
            score = 5
            suggestion = None

        return {
            "score": score,
            "distribution": counts,
            "visual_ratio": visual_ratio,
            "suggestion": suggestion
        }

    def evaluate_show_dont_tell(self, manuscript: str) -> dict:
        """Show don't tell 평가"""

        # 직접 서술 패턴
        tell_patterns = [
            r'정말 .+했다',
            r'매우 .+했다',
            r'너무 .+했다',
            r'굉장히 .+했다',
            r'.+라는 느낌이',
            r'기분이 .+했다',
            r'마음이 .+했다'
        ]

        import re
        tell_count = sum(
            len(re.findall(pattern, manuscript))
            for pattern in tell_patterns
        )

        # 1000자당 직접 서술 횟수
        ratio = tell_count / (len(manuscript) / 1000)

        if ratio < 1:
            score = 5
        elif ratio < 2:
            score = 4
        elif ratio < 3:
            score = 3
        else:
            score = 2

        return {
            "score": score,
            "tell_count": tell_count,
            "ratio_per_1000": ratio,
            "suggestion": "감정을 직접 서술하지 말고 행동/묘사로 보여주세요" if score < 4 else None
        }
```

### 3.3 대화 품질 평가 (Dialogue Quality)

```python
class DialogueQualityEvaluator:
    """
    대화 품질 평가 모듈
    """

    def evaluate_dialogue_naturalness(self, manuscript: str) -> dict:
        """대화 자연스러움 평가"""
        dialogues = self._extract_dialogues(manuscript)

        issues = []

        for dialogue in dialogues:
            # 너무 긴 대사
            if len(dialogue['text']) > 200:
                issues.append({"type": "too_long", "text": dialogue['text'][:50]})

            # 설명조 대사
            if self._is_expository(dialogue['text']):
                issues.append({"type": "expository", "text": dialogue['text'][:50]})

        score = 5 - min(len(issues), 3)

        return {
            "score": max(2, score),
            "issues": issues,
            "dialogue_count": len(dialogues)
        }

    def evaluate_voice_fingerprint(self, manuscript: str,
                                   npc_profiles: dict) -> dict:
        """캐릭터별 음성 일관성"""
        dialogues = self._extract_dialogues_with_speaker(manuscript)

        inconsistencies = []

        for speaker, lines in dialogues.items():
            if speaker not in npc_profiles:
                continue

            profile = npc_profiles[speaker]
            expected_patterns = profile.get('speech_pattern', [])

            for line in lines:
                if not self._matches_pattern(line, expected_patterns):
                    inconsistencies.append({
                        "speaker": speaker,
                        "line": line[:50],
                        "expected": expected_patterns
                    })

        score = 5 if not inconsistencies else max(2, 5 - len(inconsistencies))

        return {
            "score": score,
            "inconsistencies": inconsistencies[:3]
        }

    def evaluate_dialogue_balance(self, manuscript: str) -> dict:
        """대화 턴 균형 (독백 방지)"""
        dialogues = self._extract_dialogues_with_speaker(manuscript)

        # 화자별 대사 수
        speaker_counts = {speaker: len(lines) for speaker, lines in dialogues.items()}

        if not speaker_counts:
            return {"score": 3, "message": "대화 없음"}

        # 한 사람이 70% 이상 말하면 불균형
        total = sum(speaker_counts.values())
        max_ratio = max(speaker_counts.values()) / total if total > 0 else 0

        if max_ratio > 0.7:
            score = 2
            suggestion = "대화 균형 필요 - 한 캐릭터가 너무 많이 말함"
        elif max_ratio > 0.5:
            score = 4
            suggestion = None
        else:
            score = 5
            suggestion = None

        return {
            "score": score,
            "speaker_distribution": speaker_counts,
            "max_ratio": max_ratio,
            "suggestion": suggestion
        }
```

### 3.4 상업성 평가 (Commercial Appeal)

```python
class CommercialAppealEvaluator:
    """
    상업성 평가 모듈
    """

    def evaluate_hook_quality(self, manuscript: str) -> dict:
        """화 시작 후킹력 평가"""

        # 첫 500자 추출
        opening = manuscript[:500]

        hook_elements = {
            "action": self._has_immediate_action(opening),
            "mystery": self._has_mystery_element(opening),
            "conflict": self._has_conflict_hint(opening),
            "sensory": self._has_strong_sensory(opening)
        }

        score = sum(hook_elements.values()) + 3  # 기본 3점

        return {
            "score": min(7, score),
            "elements": hook_elements,
            "suggestion": self._hook_suggestion(hook_elements)
        }

    def evaluate_cliffhanger(self, manuscript: str) -> dict:
        """화 끝 클리프행어 평가"""

        # 마지막 500자 추출
        ending = manuscript[-500:]

        cliffhanger_types = {
            "question": self._ends_with_question(ending),
            "revelation": self._has_revelation(ending),
            "danger": self._has_danger_hint(ending),
            "arrival": self._has_new_arrival(ending),
            "decision": self._has_pending_decision(ending)
        }

        score = sum(cliffhanger_types.values()) + 2

        return {
            "score": min(7, score),
            "types": cliffhanger_types,
            "suggestion": "클리프행어 요소 추가 권장" if score < 4 else None
        }

    def evaluate_reward_timing(self, ep_num: int, manuscript: str,
                               history: list) -> dict:
        """보상 타이밍 평가"""

        rewards = {
            "power_gain": self._detect_power_gain(manuscript),
            "item_acquire": self._detect_item_acquire(manuscript),
            "recognition": self._detect_recognition(manuscript),
            "relationship": self._detect_relationship_progress(manuscript)
        }

        has_reward = any(rewards.values())

        # 최근 보상 없던 횟수
        episodes_since_reward = self._count_episodes_without_reward(history)

        if episodes_since_reward >= 3 and not has_reward:
            score = 3
            suggestion = "3화 연속 보상 없음. 작은 성취 추가 권장"
        elif has_reward:
            score = 6
            suggestion = None
        else:
            score = 4
            suggestion = None

        return {
            "score": score,
            "rewards": rewards,
            "episodes_since_last": episodes_since_reward,
            "suggestion": suggestion
        }
```

### 3.5 신선함 평가 (Originality)

```python
class OriginalityEvaluator:
    """
    신선함 평가 모듈 (ADVISORY)
    """

    COMMON_CLICHES = {
        "회귀물": ["다시 눈을 떴다", "과거로 돌아왔다", "알고 있는 미래"],
        "천재물": ["숨겨진 재능", "알고보니 천재", "각성"],
        "복수물": ["반드시 복수", "피의 대가", "잊지 않겠다"],
        "가문물": ["쫓겨난", "버림받은", "폐가문", "재건"],
        "전개": ["기절했다 깨보니", "위기의 순간 각성", "숨겨진 혈통"]
    }

    def evaluate_cliche_usage(self, manuscript: str,
                              recent_episodes: list) -> dict:
        """클리셰 사용 분석"""

        detected = []

        for category, patterns in self.COMMON_CLICHES.items():
            for pattern in patterns:
                if pattern in manuscript:
                    detected.append({
                        "category": category,
                        "pattern": pattern
                    })

        # 최근 10화에서 같은 클리셰 반복 체크
        repeated = self._check_repeated_cliches(detected, recent_episodes)

        return {
            "detected_cliches": detected,
            "repeated_cliches": repeated,
            "suggestion": self._cliche_suggestion(detected, repeated)
        }

    def suggest_subversion(self, cliche: str) -> str:
        """클리셰 반전 제안"""

        subversions = {
            "기절했다 깨보니": [
                "기절한 척 상황 파악",
                "깨어났지만 기억 조작됨",
                "꿈과 현실 구분 불가"
            ],
            "위기의 순간 각성": [
                "각성 실패로 다른 방법 모색",
                "각성했지만 부작용",
                "각성 없이 지혜로 극복"
            ],
            "숨겨진 혈통": [
                "혈통 자체가 거짓",
                "혈통 알아도 무시",
                "혈통이 오히려 저주"
            ]
        }

        return subversions.get(cliche, ["예상을 비트는 전개 권장"])
```

### 3.6 전투/액션 평가 (장르 특화)

```python
class ActionSceneEvaluator:
    """
    전투/액션 씬 평가 (장르 특화)
    """

    def evaluate_choreography(self, manuscript: str, genre: str) -> dict:
        """전투 동선 명확성"""

        action_scenes = self._extract_action_scenes(manuscript)

        issues = []
        for scene in action_scenes:
            # 공간 인식 체크
            if not self._has_spatial_clarity(scene):
                issues.append("공간 배치 불명확")

            # 동작 연결성 체크
            if not self._has_action_continuity(scene):
                issues.append("동작 연결 부자연스러움")

            # 결과 명시 체크
            if not self._has_clear_outcome(scene):
                issues.append("공격 결과 불명확")

        score = 5 - min(len(issues), 3)

        return {
            "score": max(2, score),
            "issues": issues,
            "action_scene_count": len(action_scenes)
        }

    def evaluate_power_consistency(self, manuscript: str,
                                   context: dict) -> dict:
        """전투력 일관성"""

        # 같은 기술인데 효과가 다른 경우 감지
        techniques_used = self._extract_techniques(manuscript)

        inconsistencies = []
        for tech in techniques_used:
            historical_effect = context.get('technique_effects', {}).get(tech)
            current_effect = self._analyze_technique_effect(manuscript, tech)

            if historical_effect and self._effects_differ(historical_effect, current_effect):
                inconsistencies.append({
                    "technique": tech,
                    "historical": historical_effect,
                    "current": current_effect
                })

        return {
            "score": 5 if not inconsistencies else max(2, 5 - len(inconsistencies)),
            "inconsistencies": inconsistencies
        }

    def evaluate_stakes_escalation(self, manuscript: str) -> dict:
        """전투 긴장감 상승"""

        action_scenes = self._extract_action_scenes(manuscript)

        if not action_scenes:
            return {"score": 5, "message": "액션 씬 없음"}

        stakes_curve = []
        for scene in action_scenes:
            stakes = self._measure_stakes(scene)
            stakes_curve.append(stakes)

        # 상승 곡선인지 체크
        is_escalating = all(
            stakes_curve[i] <= stakes_curve[i+1]
            for i in range(len(stakes_curve)-1)
        )

        return {
            "score": 5 if is_escalating else 3,
            "stakes_curve": stakes_curve,
            "suggestion": "긴장감이 중간에 떨어짐" if not is_escalating else None
        }
```

---

## 4. 통합 검증 파이프라인

### 4.1 ValidationOrchestrator

```python
class ValidationOrchestrator:
    """
    글도비 V0128 통합 검증 오케스트레이터

    3-Tier 검증을 순차적으로 실행하고 최종 결과를 반환합니다.
    """

    def __init__(self, config: dict):
        self.config = config

        # TIER 1: BLOCKING
        self.blocking = BlockingValidator(config)

        # TIER 2: SCORING
        self.scoring = ScoringValidator(config)
        self.scoring.PASS_THRESHOLD = config.get('scoring_threshold', 70)

        # TIER 3: ADVISORY
        self.advisory = AdvisoryValidator(config)

        # 품질 평가 모듈들
        self.emotion_eval = EmotionArcEvaluator()
        self.prose_eval = ProseQualityEvaluator()
        self.dialogue_eval = DialogueQualityEvaluator()
        self.commercial_eval = CommercialAppealEvaluator()
        self.originality_eval = OriginalityEvaluator()
        self.action_eval = ActionSceneEvaluator()

        # 카타르시스 타이머
        self.catharsis_timer = CatharsisTimer()

    async def validate(self, ep_num: int, manuscript: str,
                      context: dict) -> dict:
        """
        전체 검증 실행

        Returns:
            {
                "final_decision": "PASS" | "CONDITIONAL_PASS" | "REJECT",
                "blocking_result": {...},
                "scoring_result": {...},
                "advisory_result": {...},
                "quality_scores": {...},
                "total_score": float,
                "feedback": str
            }
        """

        results = {}

        # ═══════════════════════════════════════════════════════════════
        # TIER 1: BLOCKING (필수 통과)
        # ═══════════════════════════════════════════════════════════════
        blocking_result = self.blocking.validate(manuscript, context)
        results['blocking_result'] = blocking_result

        if not blocking_result['passed']:
            return {
                "final_decision": "REJECT",
                "reason": "BLOCKING 검증 실패",
                "failures": blocking_result['failures'],
                **results
            }

        # ═══════════════════════════════════════════════════════════════
        # TIER 2: SCORING (점수 기반)
        # ═══════════════════════════════════════════════════════════════

        # 개별 품질 평가 실행
        quality_scores = await self._run_quality_evaluations(
            ep_num, manuscript, context
        )
        results['quality_scores'] = quality_scores

        # SCORING 검증
        scoring_result = self.scoring.validate(manuscript, context)
        results['scoring_result'] = scoring_result

        # ═══════════════════════════════════════════════════════════════
        # TIER 3: ADVISORY (권고)
        # ═══════════════════════════════════════════════════════════════
        advisory_result = self.advisory.validate(manuscript, context)
        results['advisory_result'] = advisory_result

        # ═══════════════════════════════════════════════════════════════
        # 최종 판정
        # ═══════════════════════════════════════════════════════════════
        total_score = scoring_result['total_score']
        results['total_score'] = total_score

        if total_score >= 85:
            final_decision = "PASS"
            feedback = f"우수한 품질 ({total_score}점)"
        elif total_score >= self.scoring.PASS_THRESHOLD:
            final_decision = "CONDITIONAL_PASS"
            feedback = f"통과 ({total_score}점) - 개선 권장사항 확인"
        else:
            final_decision = "REJECT"
            feedback = f"품질 미달 ({total_score}점) - 재작성 필요"

        results['final_decision'] = final_decision
        results['feedback'] = feedback

        # 상세 피드백 생성
        results['detailed_feedback'] = self._generate_detailed_feedback(results)

        return results

    async def _run_quality_evaluations(self, ep_num: int, manuscript: str,
                                       context: dict) -> dict:
        """개별 품질 평가 실행"""

        return {
            # 감정선
            "emotion_arc": self.emotion_eval.evaluate_emotion_arc(
                manuscript, context
            ),
            "catharsis": self.catharsis_timer.check_catharsis_timing(
                ep_num, manuscript, context.get('history', [])
            ),

            # 문장 품질
            "prose_rhythm": self.prose_eval.evaluate_prose_rhythm(manuscript),
            "vocabulary": self.prose_eval.evaluate_vocabulary_diversity(manuscript),
            "sensory": self.prose_eval.evaluate_sensory_balance(manuscript),
            "show_dont_tell": self.prose_eval.evaluate_show_dont_tell(manuscript),

            # 대화 품질
            "dialogue_natural": self.dialogue_eval.evaluate_dialogue_naturalness(
                manuscript
            ),
            "voice_consistency": self.dialogue_eval.evaluate_voice_fingerprint(
                manuscript, context.get('npc_profiles', {})
            ),
            "dialogue_balance": self.dialogue_eval.evaluate_dialogue_balance(
                manuscript
            ),

            # 상업성
            "hook": self.commercial_eval.evaluate_hook_quality(manuscript),
            "cliffhanger": self.commercial_eval.evaluate_cliffhanger(manuscript),
            "reward_timing": self.commercial_eval.evaluate_reward_timing(
                ep_num, manuscript, context.get('history', [])
            ),

            # 신선함 (ADVISORY)
            "originality": self.originality_eval.evaluate_cliche_usage(
                manuscript, context.get('recent_episodes', [])
            ),

            # 액션 (장르별)
            "action": self.action_eval.evaluate_choreography(
                manuscript, context.get('genre', 'wuxia')
            )
        }

    def _generate_detailed_feedback(self, results: dict) -> str:
        """상세 피드백 생성"""

        feedback_parts = []

        # 점수 요약
        feedback_parts.append(f"## 총점: {results['total_score']}/100")

        # 강점
        strengths = self._identify_strengths(results)
        if strengths:
            feedback_parts.append("\n### 강점")
            for s in strengths:
                feedback_parts.append(f"- {s}")

        # 개선 필요
        weaknesses = self._identify_weaknesses(results)
        if weaknesses:
            feedback_parts.append("\n### 개선 필요")
            for w in weaknesses:
                feedback_parts.append(f"- {w}")

        # ADVISORY 제안
        suggestions = results.get('advisory_result', {}).get('suggestions', [])
        if suggestions:
            feedback_parts.append("\n### 추가 제안")
            for s in suggestions[:3]:
                feedback_parts.append(f"- {s['suggestion']}")

        return "\n".join(feedback_parts)
```

### 4.2 검증 설정 (Configurable)

```json
// config/validation_config.json
{
    "validation": {
        "blocking": {
            "enabled": true,
            "checks": ["dead_npc", "unowned_item", "destroyed_location",
                      "min_length", "required_scenes"]
        },

        "scoring": {
            "enabled": true,
            "pass_threshold": 70,
            "weights": {
                "character_consistency": 15,
                "prose_quality": 20,
                "emotion_arc": 20,
                "dialogue_quality": 15,
                "commercial_appeal": 20,
                "pattern_diversity": 10
            }
        },

        "advisory": {
            "enabled": true,
            "log_to_file": true
        }
    },

    "thresholds": {
        "min_length": 4000,
        "min_scenes": 4,
        "catharsis_max_gap": 3,
        "vocabulary_ttr_min": 0.3,
        "visual_ratio_max": 0.8
    }
}
```

---

## 5. Entity Registry System (기존 유지)

*[이전 설계와 동일 - 생략]*

---

## 6. RAG Memory System (기존 유지)

*[이전 설계와 동일 - 생략]*

---

## 7. Production Pipeline (업데이트)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      글도비 V0128 PRODUCTION PIPELINE                        │
│                      (3-Tier Validation 적용)                                │
└─────────────────────────────────────────────────────────────────────────────┘

╔═══════════════════════════════════════════════════════════════════════════════╗
║  STAGE 3: Manuscript Production (Writer)                                      ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  Writer가 원고 생성 시 참조하는 정보:                                         ║
║  ├─ RAG Context (NPC/아이템/장소 과거 장면)                                   ║
║  ├─ Sliding Window (최근 5화 전문)                                            ║
║  ├─ Quality Guidelines (품질 가이드라인 주입)                                 ║
║  │   ├─ "문장 길이에 변화를 주세요"                                           ║
║  │   ├─ "오감 묘사를 균형있게 배치하세요"                                     ║
║  │   ├─ "화 시작은 강렬하게, 끝은 궁금하게"                                   ║
║  │   └─ "직접 감정 서술 대신 행동으로 보여주세요"                             ║
║  └─ Previous Feedback (이전 피드백 반영)                                      ║
╚═══════════════════════════════════════════════════════════════════════════════╝
                                    ↓
╔═══════════════════════════════════════════════════════════════════════════════╗
║  VALIDATION: 3-Tier System                                                    ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  ┌─ TIER 1: BLOCKING ──────────────────────────────────────────────────────┐ ║
║  │  □ 사망 NPC 재등장 체크                                                 │ ║
║  │  □ 미획득 아이템 사용 체크                                              │ ║
║  │  □ 파괴된 장소 방문 체크                                                │ ║
║  │  □ 최소 분량 (4,000자) 체크                                             │ ║
║  │  □ 필수 씬 포함 체크                                                    │ ║
║  │  ──────────────────────────────────────────────────────────────────── │ ║
║  │  실패 시 → REJECT (Writer 재작성)                                       │ ║
║  └─────────────────────────────────────────────────────────────────────────┘ ║
║                              ↓ PASS                                           ║
║  ┌─ TIER 2: SCORING (100점 만점) ──────────────────────────────────────────┐ ║
║  │                                                                         │ ║
║  │  [캐릭터 일관성: 15점]                                                  │ ║
║  │   └─ 말투/행동/성격 일탈 검사                                           │ ║
║  │                                                                         │ ║
║  │  [문장 품질: 20점]                                                      │ ║
║  │   ├─ 리듬 (5점): 문장 길이 변화율                                       │ ║
║  │   ├─ 어휘 (5점): 다양성 및 반복 방지                                    │ ║
║  │   ├─ 감각 (5점): 오감 묘사 균형                                         │ ║
║  │   └─ Show (5점): 직접 서술 vs 묘사                                      │ ║
║  │                                                                         │ ║
║  │  [감정선: 20점]                                                         │ ║
║  │   ├─ 흐름 (7점): 감정 곡선 자연스러움                                   │ ║
║  │   ├─ 긴장 (7점): 텐션 관리                                              │ ║
║  │   └─ 해소 (6점): 카타르시스 타이밍                                      │ ║
║  │                                                                         │ ║
║  │  [대화 품질: 15점]                                                      │ ║
║  │   ├─ 자연 (5점): 대화 자연스러움                                        │ ║
║  │   ├─ 함축 (5점): 서브텍스트                                             │ ║
║  │   └─ 균형 (5점): 대화 턴 배분                                           │ ║
║  │                                                                         │ ║
║  │  [상업성: 20점]                                                         │ ║
║  │   ├─ 후킹 (7점): 시작 후킹력                                            │ ║
║  │   ├─ 끝맺 (7점): 클리프행어                                             │ ║
║  │   └─ 보상 (6점): 사이다 타이밍                                          │ ║
║  │                                                                         │ ║
║  │  [패턴 다양성: 10점]                                                    │ ║
║  │   ├─ 서사 (4점): 전개 패턴 다양성                                       │ ║
║  │   ├─ 반응 (3점): 리액션 다양성                                          │ ║
║  │   └─ 구조 (3점): 씬 길이 다양성                                         │ ║
║  │                                                                         │ ║
║  │  ──────────────────────────────────────────────────────────────────── │ ║
║  │  70점 이상 → PASS / 85점 이상 → 우수 PASS                               │ ║
║  │  70점 미만 → REJECT (피드백과 함께 재작성)                              │ ║
║  └─────────────────────────────────────────────────────────────────────────┘ ║
║                              ↓ PASS                                           ║
║  ┌─ TIER 3: ADVISORY ──────────────────────────────────────────────────────┐ ║
║  │  • 클리셰 감지 및 반전 제안                                             │ ║
║  │  • 더 나은 표현 제안                                                    │ ║
║  │  • 복선 기회 알림                                                       │ ║
║  │  • 캐릭터 심화 기회                                                     │ ║
║  │  ──────────────────────────────────────────────────────────────────── │ ║
║  │  통과에 영향 없음 - 로그 기록 및 참고용                                 │ ║
║  └─────────────────────────────────────────────────────────────────────────┘ ║
║                                                                               ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  최종 결과:                                                                   ║
║  • PASS (85점+): 저장 + "우수" 마크                                          ║
║  • CONDITIONAL_PASS (70-84점): 저장 + 개선 제안 로그                         ║
║  • REJECT (<70점): Writer 재작성 + 구체적 피드백                             ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 8. 예상 성과

### 8.1 통과율 비교

| 시스템 | 예상 1차 통과율 | 평균 재시도 |
|--------|----------------|------------|
| 기존 (전부 BLOCKING) | 50-60% | 2.0회 |
| V0128 (3-Tier) | **80-85%** | **1.2회** |

### 8.2 품질 향상 예상

| 차원 | 기존 | V0128 |
|------|------|-------|
| 설정 일관성 | 중 | **상** (Entity Registry) |
| 문장 품질 | 중 | **중상** (SCORING 피드백) |
| 감정선 | 하 | **중상** (Emotion Arc 추적) |
| 상업성 | 중 | **상** (Hook/Cliffhanger 평가) |
| 패턴 다양성 | 하 | **상** (Pattern Guard) |

---

## 9. 설정 파일

```json
// config/geuldobi_v0128_settings.json
{
    "system": {
        "name": "글도비",
        "version": "V0128"
    },

    "validation": {
        "tier1_blocking": {
            "enabled": true,
            "checks": ["dead_npc", "unowned_item", "destroyed_location",
                      "min_length", "required_scenes"]
        },
        "tier2_scoring": {
            "enabled": true,
            "pass_threshold": 70,
            "excellent_threshold": 85
        },
        "tier3_advisory": {
            "enabled": true,
            "log_suggestions": true
        }
    },

    "quality_weights": {
        "character_consistency": 15,
        "prose_quality": 20,
        "emotion_arc": 20,
        "dialogue_quality": 15,
        "commercial_appeal": 20,
        "pattern_diversity": 10
    },

    "thresholds": {
        "min_length": 4000,
        "min_scenes": 4,
        "catharsis_max_gap": 3,
        "vocabulary_ttr_min": 0.3,
        "prose_rhythm_cv_min": 0.3,
        "prose_rhythm_cv_max": 0.6
    },

    "memory": {
        "sliding_window_size": 5,
        "rag_chunk_size": 1500,
        "rag_results_per_query": 5
    }
}
```

---

## 10. Appendix: 용어 정의

| 용어 | 정의 |
|------|------|
| **BLOCKING** | 반드시 통과해야 하는 필수 검증. 실패 시 REJECT |
| **SCORING** | 점수 기반 품질 평가. 가중치 합산으로 판정 |
| **ADVISORY** | 통과에 영향 없는 개선 제안 |
| **Type-Token Ratio (TTR)** | 어휘 다양성 지표. 고유 단어 / 전체 단어 |
| **Coefficient of Variation (CV)** | 변동계수. 표준편차 / 평균 |
| **Catharsis Timer** | 사이다(카타르시스) 간격 관리 |
| **Hook Quality** | 화 시작의 후킹력 |
| **Cliffhanger** | 화 끝의 긴장감/궁금증 유발 요소 |

---

**문서 끝**

*글도비 V0128 MANIFESTO - 3-Tier Validation + 7대 품질 차원*

**핵심 변경사항**:
1. 3-Tier Validation으로 통과율 저하 방지 (80-85% 목표)
2. 7대 품질 차원 정의 (일관성 + 문학성 + 상업성)
3. BLOCKING은 5개 핵심 항목만 (엄선)
4. SCORING은 가중치 기반 (개별 실패해도 보완 가능)
5. ADVISORY는 로그만 (통과에 무영향)
6. 모든 품질 평가 모듈 상세 설계 포함
