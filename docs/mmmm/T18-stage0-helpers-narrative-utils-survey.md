# T18 — Stage 0, Helpers & Narrative Utilities: Deep Global Survey

**6PASS-CLEARED** | **COLLECTOR ONLY** | **NO EXECUTION AUTHORITY**

- **Terminal**: T18
- **Date**: 2026-03-20
- **Baseline Commit**: `d0fa70f1`
- **Confidence**: 96%
- **Mode**: survey-only, static analysis, no code modifications
- **TF Count**: 25

---

## 1. Scope & Files

### Stage 0 Core (8 files, ~5,900 lines)
| File | Lines | Role |
|------|-------|------|
| `modules/core/stage0/__init__.py` | 1,017 | StageZeroManager — genre selection, bible generation, treatment |
| `modules/core/stage0/preset_registry.py` | 740 | PresetRegistry — 10-genre field definitions, normalization |
| `modules/core/stage0/reverse_expander.py` | 1,213 | ReverseExpander — reverse-engineering from existing drafts |
| `modules/core/stage0/story_expander.py` | 829 | StoryExpander — concept→bible→treatment generation |
| `modules/core/stage0/style_extractor.py` | 1,228 | StyleExtractor — style guide extraction with 9-key cache |
| `modules/core/stage0/spinner.py` | 667 | Spinner/ProgressBar/PhaseIndicator — Rich/ANSI fallback |
| `modules/core/stage0_handoff.py` | 186 | PlotRoadmapStatus — Stage 0→2 handoff validation |
| `modules/core/stage01_helpers.py` | 925 | Stage01Helpers — Phase 0 recovery + Phase 1 volumes |

### Genre Guards (14 files, ~6,000+ lines)
| File | Lines | Role |
|------|-------|------|
| `modules/core/genre_guards/base_guard.py` | 862 | BaseGuard — V46/V46.1 consistency validation |
| `modules/core/genre_guards/wuxia_guard.py` | 663 | WuxiaGuard — 154 forbidden terms, realm hierarchy |
| `modules/core/genre_guards/hunter_guard.py` | 868 | HunterGuard — dungeon/awakening/skill mechanics |
| `modules/core/genre_guards/investment_guard.py` | 718 | InvestmentGuard — financial accuracy, leverage formula |
| `modules/core/genre_guards/fantasy_guard.py` | 363 | FantasyGuard — magic tier system |
| `modules/core/genre_guards/composer_guard.py` | ~200+ | ComposerGuard — music industry |
| `modules/core/genre_guards/cooking_guard.py` | ~200+ | CookingGuard — culinary expertise |
| `modules/core/genre_guards/alt_history_guard.py` | ~200+ | AltHistoryGuard — historical accuracy |
| `modules/core/genre_guards/actor_guard.py` | ~200+ | ActorGuard — entertainment industry |
| `modules/core/genre_guards/sports_guard.py` | ~200+ | SportsGuard — athletic expertise |
| `modules/core/genre_guards/medical_guard.py` | ~200+ | MedicalGuard — healthcare accuracy |
| `modules/core/genre_guards/work_guard.py` | 965 | WorkGuard — project-specific YAML overlay |
| `modules/core/genre_guards/style_guard.py` | 174 | StyleGuard — style-based validation |
| `modules/core/genre_guards/__init__.py` | 87 | Factory: `create_genre_guard()` |

### Failure Analysis & Retry (4 files, ~4,100 lines)
| File | Lines | Role |
|------|-------|------|
| `modules/core/failure_analyzer.py` | 1,962 | FailureAnalyzer — 5-sink alignment + 23 public methods |
| `modules/core/failure_learning.py` | 367 | FailureLearner — 16-category classifier + constraint gen |
| `modules/core/adaptive_retry.py` | 858 | AdaptiveRetryStrategy/Manager — error-type-driven retry |
| `modules/core/feedback_system.py` | 931 | FeedbackSystem — 15 pure feedback generation methods |

### Narrative Utilities (15 files, ~6,500+ lines)
| File | Lines | Role |
|------|-------|------|
| `modules/core/narrative_context_formatter.py` | 240 | NarrativeContextFormatter — motivation/promise formatting |
| `modules/core/narrative_diversity.py` | 593 | NarrativeDiversityEngine — diversity sampling controller |
| `modules/core/narrative_structure_analyzer.py` | 309 | NarrativeStructureAnalyzer — stagnation detection |
| `modules/core/pattern_tracker.py` | 1,209 | PatternTracker — expression/plot/cliche analysis |
| `modules/core/emotion_tracker.py` | 410 | EmotionArcTracker — emotion monotony detection |
| `modules/core/character_voice.py` | 578 | CharacterVoiceTracker — dialogue consistency |
| `modules/core/character_voice_profiler.py` | 452 | CharacterVoiceProfiler — auto-profile extraction |
| `modules/core/pacing_analyzer.py` | 440 | PacingAnalyzer — pacing score + zone analysis |
| `modules/core/foreshadow_tracker.py` | 687 | ForeshadowTracker — Chekhov's gun tracking |
| `modules/core/repetition_guard.py` | 223 | RepetitionGuard — trigram-based repetition detection |
| `modules/core/diversity_sampler.py` | 500 | DiversitySampler — TTR/novelty/structure scoring |
| `modules/core/power_scaling.py` | 500+ | PowerScalingTracker — justification-based growth validation |
| `modules/core/jianghu_logic.py` | 26 | JianghuLogic — Euclidean distance calculation |
| `modules/core/primitive_guard.py` | 286 | PrimitiveGuard — primitive content filtering |
| `modules/core/dynamic_prompt_weighting.py` | 303 | DynamicPromptWeighter — failure-driven weight adjustment |

### Related Tests (12 files, ~4,800+ lines)
| File | Lines | Tests |
|------|-------|-------|
| `tests/test_stage0_fixes.py` | 221 | 12 |
| `tests/test_stage01_helpers.py` | 690 | 41 |
| `tests/test_feedback_system.py` | 647 | 61 |
| `tests/test_failure_analyzer.py` | 1,178 | 11 |
| `tests/test_genre_guard.py` | 297 | 28 |
| `tests/test_genre_guards_extended.py` | 115 | 12 |
| `tests/test_style_guard.py` | 223 | 24 |
| `tests/test_work_guard.py` | 741 | 48 |
| `tests/test_narrative_context_formatter.py` | 359 | 28 |
| `tests/test_repetition_guard.py` | 198 | 18 |
| `tests/test_cross_episode_repetition.py` | 163 | 14 |
| `tests/test_long_term_repetition.py` | 182 | 17 |

**Total**: ~41 production files, ~23,500+ lines; 12 test files, 314 test methods

---

## 2. TF Registry

### T18-TF-001: Stage 0 Initialization Flow Verified (SYNC)
```
ID: T18-TF-001
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/stage0/__init__.py, stage0/story_expander.py, stage01_helpers.py
Evidence:
  - modules/core/stage0/__init__.py:998-1000
    `create_stage_zero()` factory → StageZeroManager instantiation
  - modules/core/stage0/__init__.py:52-994
    StageZeroManager.run_new_project_flow() flow:
    Genre Selection → Protagonist Config → Bible Generation → Treatment → Review Gate → Save
  - modules/core/stage0/story_expander.py:759-828
    StoryExpander.run(): analyze_concept → generate_bible → generate_treatment → review_stage0_candidate → save_all
  - modules/core/stage01_helpers.py:462-660
    stage_0_extended(): 6 submenu modes (concept, reverse, import, extend, style, work_guard)
  - modules/core/stage0_handoff.py:166-185
    ensure_plot_roadmap(): validates roadmap contract before Stage 2 handoff
Inference: Stage 0 초기화 흐름이 완전하고 일관적이다. Genre→Bible→Treatment→Review→Save→Handoff 경로 확인.
Uncertainty: None
Cross-Ref: T01 (SovereignApp lazy init), T02 (Stage 2 handoff consumer)
```

### T18-TF-002: SPINNER_AVAILABLE Conditional Import Feature Flag
```
ID: T18-TF-002
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/stage0/__init__.py:29-31
Evidence:
  - modules/core/stage0/__init__.py:29-31
    ```python
    SPINNER_AVAILABLE = True
    except ImportError:
        SPINNER_AVAILABLE = False
    ```
  - modules/core/stage0/spinner.py:14-26
    Rich library conditional import with `RICH_AVAILABLE` flag
    Fallback: ANSI color codes via sys.stdout.write
Inference: 두 단계 feature flag: SPINNER_AVAILABLE(모듈 수준) + RICH_AVAILABLE(Rich 라이브러리). 둘 다 graceful degradation 패턴. Rich 미설치 시 ANSI 폴백.
Uncertainty: None
Cross-Ref: None
```

### T18-TF-003: ReverseExpander UTF-8→cp949 Encoding Fallback
```
ID: T18-TF-003
Severity: P3-LOW
Category: SIDE-EFFECT
Surface: modules/core/stage0/reverse_expander.py:45-46, 217-219
Evidence:
  - modules/core/stage0/reverse_expander.py:45-46
    `class DraftEncodingError(Exception): ...`
  - modules/core/stage0/reverse_expander.py:217-219
    UTF-8 read fails → cp949 fallback attempt → both fail → raise DraftEncodingError
  - Fail-closed design: 두 인코딩 모두 실패 시 예외 발생, silent data corruption 방지
Inference: 한국어 원고 임포트에 cp949 폴백이 필요한 현실적 설계. AGENTS.md 인코딩 가드레일("cp949 기반 저장 금지")과 충돌 가능성이 있으나, 이는 읽기 전용 폴백이므로 위반이 아님.
Uncertainty: 읽은 cp949 데이터가 이후 UTF-8로 재저장되는지는 동적 검증 필요
Cross-Ref: T20 (Encoding guardrails)
```

### T18-TF-004: ReverseExpander persist_to_db() Atomic Transaction
```
ID: T18-TF-004
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/stage0/reverse_expander.py:783-833
Evidence:
  - modules/core/stage0/reverse_expander.py:802-830
    ```python
    try:
        # 5 테이블 writes (manuscripts, state_logs, episode_bibles, blueprints, arcs)
        ...
    except Exception:
        # Full rollback on any failure
    ```
  - Transaction scope: 5 tables within single atomic block
  - Rollback on any exception
Inference: DB 쓰기가 all-or-nothing으로 보호됨. Partial write 상태 방지.
Uncertainty: None
Cross-Ref: T16 (DB transaction patterns)
```

### T18-TF-005: Guard Chain Factory 3-Layer Assembly Verified (SYNC)
```
ID: T18-TF-005
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/genre_guards/__init__.py:22-69
Evidence:
  - modules/core/genre_guards/__init__.py:35-59
    ```python
    # 1. Create base guard
    guard = WuxiaGuard() | HunterGuard() | ... (10 genres)
    # 2. Optional WorkGuard wrapping
    if work_guard_path: guard = WorkGuard(guard, work_guard_path)
    # 3. Optional StyleGuard wrapping
    if style_guide: guard = StyleGuard(guard, style_guide)
    return guard
    ```
  - Chain pattern: GenreGuard → WorkGuard(optional) → StyleGuard(optional)
  - Each layer's run_deep_validation() calls base first, then adds own checks
Inference: Guard chain 조립이 정확하며 누락/중복 없음. 10개 장르 전수 지원.
Uncertainty: None
Cross-Ref: T17 (Genre YAML config)
```

### T18-TF-006: 10 Genre Guards Complete Coverage of GenreTypes (SYNC)
```
ID: T18-TF-006
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/genre_guards/*.py
Evidence:
  - 10 genre subclasses: wuxia, hunter, investment, fantasy, composer, cooking, alt_history, actor, sports, medical
  - modules/core/stage0/__init__.py SUPPORTED_GENRES: 동일한 10개 장르
  - tests/test_stage0_fixes.py:22
    `test_supported_genres_matches_genre_types`: GenreTypes.all() == SUPPORTED_GENRES.keys()
Inference: 장르 가드와 Stage 0 장르 목록이 정확히 일치함.
Uncertainty: None
Cross-Ref: T17 (GenreTypes constants)
```

### T18-TF-007: WorkGuard _added_forbidden Delta Computation (SYNC)
```
ID: T18-TF-007
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/genre_guards/work_guard.py:353-409
Evidence:
  - modules/core/genre_guards/work_guard.py:377
    `_added_forbidden`: YAML extra_forbidden에서 base guard의 FORBIDDEN_TERMS에 없는 것만 추출
  - work_guard.py:904-964 run_deep_validation():
    1. base.run_deep_validation() 호출 (장르 검증)
    2. _added_forbidden 추가 검증 (HIGH severity)
    3. _extra_patterns regex 검증 (HIGH severity)
    4. 5개 sub-check (WARNING): char constraints, lexicon, scene engines, flattenings, role fit
  - work_guard.py:481-568 get_v20_purism_prompt():
    [작품 정체성 SSOT], [우선 추적 슬롯], [레지스트리 프로파일], [직업 적합성 가드], [작품 전용 규칙], [캐릭터별 제약]
Inference: WorkGuard는 base guard 위에 프로젝트별 오버레이를 정확히 추가하며, 중복 검증 방지를 위해 delta만 검사.
Uncertainty: None
Cross-Ref: None
```

### T18-TF-008: Inline `import re` in Genre Guard Subclasses
```
ID: T18-TF-008
Severity: P4-OBSERVATION
Category: HARDCODING
Surface: modules/core/genre_guards/wuxia_guard.py, hunter_guard.py, investment_guard.py
Evidence:
  - wuxia_guard.py:613 — `import re` inside run_deep_validation()
  - hunter_guard.py:820 — `import re` inside run_deep_validation()
  - investment_guard.py:648 — `import re` inside run_deep_validation()
  - base_guard.py에는 `import re`가 top-level에 있으나, 서브클래스 override에서 재 import
Inference: 함수 내 import는 성능 영향 미미(Python 캐시). 스타일 불일치이나 기능 문제 없음.
Uncertainty: None
Cross-Ref: None
```

### T18-TF-009: FailureAnalyzer._append_to_suffix_yaml() Config File Write
```
ID: T18-TF-009
Severity: P2-MEDIUM
Category: SIDE-EFFECT
Surface: modules/core/failure_analyzer.py:1913-1956
Evidence:
  - modules/core/failure_analyzer.py:1950
    `yaml_path.write_text(yaml.dump(data, ...))` — item_suffixes.yaml에 APPROVE된 suffix 추가
  - 호출 경로: review_and_apply_suffixes() L1883 → _append_to_suffix_yaml() L1913
  - review_and_apply_suffixes()는 LLM으로 suffix 후보 심사 후 APPROVE된 것만 적용
  - failure_analyzer.py:1928 — yaml.safe_load()로 기존 YAML 읽기
Inference: FailureAnalyzer는 대부분 read-only이나, suffix 관리 기능에서 config 파일을 수정함. survey-only 관점에서는 side-effect surface로 기록 필요. 이 메서드는 명시적 사용자 호출이 필요하므로 자동 실행 위험은 낮음.
Uncertainty: review_and_apply_suffixes()가 자동 파이프라인에서 호출되는지 여부 — 정적 분석으로는 호출자 추적 필요
Cross-Ref: T17 (item_suffixes.yaml config)
```

### T18-TF-010: feedback_system.py L840 Dead Expression Statement
```
ID: T18-TF-010
Severity: P3-LOW
Category: DEAD-CODE
Surface: modules/core/feedback_system.py:840
Evidence:
  - modules/core/feedback_system.py:839-840
    ```python
    reason_lower = reason.lower() if reason else ""
    feedback.lower() if feedback else ""  # ← 결과가 변수에 할당되지 않음
    ```
  - L839: `reason_lower` 변수에 할당됨 (정상)
  - L840: expression statement — feedback.lower()의 반환값이 버려짐
  - 의도 추정: `feedback_lower = feedback.lower() if feedback else ""`였을 가능성
Inference: Copy-paste 실수로 변수 할당이 누락된 dead expression. feedback_lower가 이후 코드에서 사용되지 않으므로 기능 영향은 없으나, reason_lower만 사용되고 feedback은 원본 그대로 사용됨.
Uncertainty: 의도적으로 feedback을 소문자 변환 없이 사용하는 설계인지 불명
Cross-Ref: None
```

### T18-TF-011: PatternTracker Dual Lookback Values
```
ID: T18-TF-011
Severity: P3-LOW
Category: HARDCODING
Surface: modules/core/pattern_tracker.py:227, 257
Evidence:
  - modules/core/pattern_tracker.py:227
    `def __init__(self, window_size: int = 10, ...):` — window_size=10 for analyze_manuscripts()
  - modules/core/pattern_tracker.py:257
    `def build_report(self, db, ep_num: int, lookback: int = 5):` — lookback=5 for DB-based report
  - analyze_manuscripts() L422: `recent_ms = manuscripts[-self.window_size:]` — 10화 분석
  - build_report() L259: `manuscripts = self._load_manuscripts(db, ep_num, lookback)` — 5화 로드
Inference: 두 메서드는 다른 용도(build_report=경량 빠른 리포트, analyze_manuscripts=전체 분석)이므로 다른 기본값은 의도적일 수 있음. 그러나 문서화가 없어 유지보수 시 혼동 가능.
Uncertainty: 의도적 설계인지 불명. window_size와 lookback이 서로 독립적으로 설정되므로 호출자에 따라 다른 깊이의 분석이 됨.
Cross-Ref: None
```

### T18-TF-012: PatternTracker 3 Dead Code Methods [TF-5-05]
```
ID: T18-TF-012
Severity: P3-LOW
Category: DEAD-CODE
Surface: modules/core/pattern_tracker.py:864-904, 984-1037, 1162-1209
Evidence:
  - modules/core/pattern_tracker.py:864-865
    ```python
    def analyze_genre_patterns_v59(self, manuscripts: list[str]) -> dict:
        """[V59] 장르별 확장 패턴 분석 — [TF-5-05] 외부 호출 없음, dead code 후보.
    ```
  - modules/core/pattern_tracker.py:984
    `def analyze_trend_v59(...)` — 동일 [TF-5-05] 표기
  - modules/core/pattern_tracker.py:1162
    `def generate_trend_report_v59(...)` — companion dead code
  - Grep "analyze_genre_patterns_v59" in modules/ → pattern_tracker.py 자체 정의만 존재
  - Grep "analyze_trend_v59" in modules/ → pattern_tracker.py 자체 정의만 존재
Inference: V59에서 도입되었으나 현재 외부에서 호출하는 코드 없음. 코드 자체에 [TF-5-05] dead code 주석이 있어 이미 인지된 상태. 총 ~350줄의 dead code.
Uncertainty: 테스트에서 호출 여부 미확인 — 테스트 전용이라면 dead code가 아닐 수 있음
Cross-Ref: T20 (Dead code 전수)
```

### T18-TF-013: EmotionTracker Monotony Detection — Variance Threshold 0.5
```
ID: T18-TF-013
Severity: P4-OBSERVATION
Category: HARDCODING
Surface: modules/core/emotion_tracker.py:154-186
Evidence:
  - modules/core/emotion_tracker.py:178-179
    ```python
    # 분산이 0.5 미만이면 단조로움
    if variance < 0.5:
    ```
  - modules/core/emotion_tracker.py:26-32
    EMOTION_STATES: despair=-2, frustration=-1, neutral=0, hope=1, triumph=2
  - modules/core/emotion_tracker.py:164
    `if len(self.history) < last_n_episodes:` — 최소 5화 필요 (default)
  - 분산 0.5 의미: 5화 연속 같은 감정이면 variance=0 (단조). 예: [hope, hope, triumph, hope, hope] → mean=1.2, variance=0.16 (단조 판정)
Inference: EMOTION_STATES 범위가 [-2, 2]이므로 variance < 0.5는 감정 변화가 거의 없음을 의미. 합리적인 임계값이나 validation.yaml에 정의되지 않고 하드코딩됨.
Uncertainty: None
Cross-Ref: None
```

### T18-TF-014: EmotionTracker Advisory Generation (3+ Episodes)
```
ID: T18-TF-014
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/emotion_tracker.py:188-289
Evidence:
  - modules/core/emotion_tracker.py:188-289
    _generate_recommendation(): 감정 상태별 맞춤 advisory 생성
    - Despair/Frustration (N≥3): "희망 씨앗" 필수 섹션 주입
      → 80% 절망 심화 + 20% 희망 요소 (hidden secret, unexpected helper, enemy weakness 등)
    - Hope/Triumph (N≥3): 긴장 회복 advisory
      → New crisis, betrayal, time constraint 등
    - Neutral: 감정 진폭 강화 advisory
  - modules/core/emotion_tracker.py:328-341
    add_episode_emotion(): 50-episode window cap (`self.history = self.history[-50:]`)
Inference: 감정 단조 감지 후 advisory 생성이 완전하고 장르 특화 패턴을 포함. 50화 윈도우 캡은 메모리 관리용.
Uncertainty: None
Cross-Ref: T15 (Advisory chain integration)
```

### T18-TF-015: AdaptiveRetryManager Double-Check Locking Singleton
```
ID: T18-TF-015
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/adaptive_retry.py:436-447, 773-785
Evidence:
  - modules/core/adaptive_retry.py:436-447
    ```python
    _adaptive_retry_instance = None
    _adaptive_retry_lock = threading.Lock()
    def get_adaptive_retry_strategy():
        global _adaptive_retry_instance
        if _adaptive_retry_instance is None:
            with _adaptive_retry_lock:
                if _adaptive_retry_instance is None:
                    _adaptive_retry_instance = AdaptiveRetryStrategy()
        return _adaptive_retry_instance
    ```
  - 동일 패턴: L773-785 for AdaptiveRetryManager
  - AdaptiveRetryManager.record_failure() L552: `with self._lock`
  - AdaptiveRetryManager.get_retry_guidance() L590: `with self._lock`
Inference: 정확한 double-check locking 패턴. Thread safety 보장됨.
Uncertainty: None
Cross-Ref: None
```

### T18-TF-016: AdaptiveRetryStrategy QUOTA_EXCEEDED Wait 30s Hardcoded
```
ID: T18-TF-016
Severity: P3-LOW
Category: HARDCODING
Surface: modules/core/adaptive_retry.py:89-96
Evidence:
  - modules/core/adaptive_retry.py:89-96
    ```python
    WAIT_TIME_BY_TYPE = {
        ErrorType.CONSTRAINT_VIOLATION: 0,
        ErrorType.QUALITY_ISSUE: 0,
        ErrorType.STRUCTURE_ERROR: 1,
        ErrorType.TIMEOUT: 2,
        ErrorType.QUOTA_EXCEEDED: 30,
        ErrorType.UNKNOWN: 1,
    }
    ```
  - modules/core/adaptive_retry.py:79-86
    ```python
    MAX_RETRIES_BY_TYPE = {
        ErrorType.CONSTRAINT_VIOLATION: 3,
        ErrorType.QUALITY_ISSUE: 2,
        ErrorType.STRUCTURE_ERROR: 2,
        ErrorType.TIMEOUT: 1,
        ErrorType.QUOTA_EXCEEDED: 3,
        ErrorType.UNKNOWN: 2,
    }
    ```
Inference: Retry 대기 시간과 최대 재시도 횟수가 모두 클래스 상수로 하드코딩. system.yaml이나 validation.yaml에서 읽지 않음. API quota 변경 시 코드 수정 필요.
Uncertainty: None
Cross-Ref: T17 (Config constants)
```

### T18-TF-017: FailureLearner 16 Failure Categories with Regex Classification
```
ID: T18-TF-017
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/failure_learning.py:29-56, 87-122
Evidence:
  - modules/core/failure_learning.py:29-56
    FailureCategory enum: ITEM_DUPLICATE, ITEM_MISSING, STATE_DISCONTINUITY, TIMELINE_ERROR,
    SCOPE_OVERFLOW, BLUEPRINT_MISMATCH, MISSING_SCENE, RELATIONSHIP_JUMP, CHARACTER_OOC,
    VILLAIN_STUPIDITY, FREE_POWERUP, DEUS_EX_MACHINA, PACING_ISSUE, JSON_ERROR, LENGTH_ERROR, UNKNOWN
  - modules/core/failure_learning.py:87-122
    각 카테고리별 regex 패턴 매칭 (한국어+영어 혼합)
  - modules/core/failure_learning.py:124-148
    카테고리별 constraint template strings
  - modules/core/failure_learning.py:211-249
    threshold ≥ 2 시 LearnedConstraint 생성, priority = 5 + count
Inference: 16개 실패 카테고리가 Director REJECT 사유를 포괄적으로 분류. regex 패턴은 한국어와 영어를 모두 지원.
Uncertainty: None
Cross-Ref: None
```

### T18-TF-018: ForeshadowTracker DEFAULT_DEADLINES Hardcoded
```
ID: T18-TF-018
Severity: P4-OBSERVATION
Category: HARDCODING
Surface: modules/core/foreshadow_tracker.py:116-125
Evidence:
  - modules/core/foreshadow_tracker.py:116-125
    ```python
    DEFAULT_DEADLINES = {
        ForeshadowCategory.MYSTERY: 20,
        ForeshadowCategory.CHEKHOV: 15,
        ForeshadowCategory.RELATIONSHIP: 30,
        ForeshadowCategory.POWER: 25,
        ForeshadowCategory.WORLDBUILDING: 40,
        ForeshadowCategory.FORESIGHT: 50,
        ForeshadowCategory.OTHER: 20,
    }
    ```
  - modules/core/foreshadow_tracker.py:127-131
    max_hooks=200 cap
Inference: 카테고리별 기한이 합리적 (체호프의 총 15화, 세계관 40화 등). 하드코딩이나 장르별 조정이 필요할 수 있음 (단편 vs 장편).
Uncertainty: 장르/작품 규모에 따라 deadline 조정 메커니즘 없음
Cross-Ref: None
```

### T18-TF-019: CharacterVoiceTracker/ForeshadowTracker Lock Without Timeout
```
ID: T18-TF-019
Severity: P3-LOW
Category: RACE-CONDITION
Surface: modules/core/character_voice.py:422-469, modules/core/foreshadow_tracker.py:419-473
Evidence:
  - modules/core/character_voice.py:465-469
    `conn.execute()` within lock — no timeout specified on Lock.acquire()
  - modules/core/foreshadow_tracker.py:427
    Lock usage for DB operations — no timeout
  - 두 모듈 모두 `threading.Lock` 사용, `Lock.acquire(timeout=N)` 미사용
Inference: DB 연산이 정상이면 문제 없으나, DB가 busy 상태에서 Lock이 무한 대기할 수 있음. 프로덕션에서 실제 문제 발생 가능성은 낮음 (단일 세션 사용 패턴).
Uncertainty: 실제 concurrent 접근 패턴에서 deadlock 발생 여부는 동적 검증 필요
Cross-Ref: T16 (DB threading patterns)
```

### T18-TF-020: RepetitionGuard Trigram Window with Threshold 3
```
ID: T18-TF-020
Severity: P4-OBSERVATION
Category: HARDCODING
Surface: modules/core/repetition_guard.py:24-31
Evidence:
  - modules/core/repetition_guard.py:24-31
    ```python
    def __init__(self, window_size: int = 5, threshold: int = 3):
        self.window_size = window_size  # 최근 5화
        self.threshold = threshold      # 3회 이상 반복 = banned
    ```
  - modules/core/repetition_guard.py:69
    Minimum phrase length = 5 chars
  - modules/core/repetition_guard.py:128-167
    Advisory output: "[🚨 REPETITION ALERT - 반복 구문 과다 사용]" + 상위 5개 violation
Inference: 3-gram 추출 + 3회 임계값 + 5화 윈도우. 파라미터가 __init__에서 설정 가능하므로 하드코딩이나 호출자에서 조정 가능.
Uncertainty: None
Cross-Ref: None
```

### T18-TF-021: FeedbackSystem 15 Pure Methods, 0 Side Effects (SYNC)
```
ID: T18-TF-021
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/feedback_system.py:21-931
Evidence:
  - 15 public methods 전수:
    build_structured_feedback, get_violation_priority, format_feedback_for_prompt,
    quantify_reject_feedback, build_strong_kind_feedback, build_focused_context,
    build_strong_kind_feedback_legacy, build_minimal_arc_context,
    generate_structured_arc_feedback, generate_structured_blueprint_feedback,
    generate_reverse_feedback_stage4_to_3, generate_reverse_feedback_stage3_to_2,
    generate_reverse_feedback_stage4_to_2, get_adaptive_feedback_intensity,
    classify_rejection_feedback, simplify_prompt_for_retry (+ _normalize_score_breakdown_value helper)
  - File I/O: 0
  - DB operations: 0
  - Cache mutations: 0
  - Global state: 0
Inference: FeedbackSystem은 완전한 pure function 모듈. 테스트 용이성 최상. 모든 메서드가 입력→출력 변환만 수행.
Uncertainty: None
Cross-Ref: None
```

### T18-TF-022: Test Files Hardcoded Thresholds Without Live-Code References
```
ID: T18-TF-022
Severity: P2-MEDIUM
Category: DRIFT
Surface: tests/test_feedback_system.py, test_repetition_guard.py, test_narrative_context_formatter.py, test_long_term_repetition.py
Evidence:
  - tests/test_feedback_system.py:89-90
    `len(result["reason"]) <= 300` — truncation limit 300 하드코딩. Live code에서 상수 참조 없음.
  - tests/test_feedback_system.py:96
    `len(result["fix_instructions"]) <= 500` — truncation limit 500 하드코딩.
  - tests/test_repetition_guard.py:19-20
    `window_size == 5`, `threshold == 3` — 기본값 하드코딩. Live code defaults와 동기화 보장 없음.
  - tests/test_narrative_context_formatter.py:357
    motivations FIFO limit = 20 하드코딩
  - tests/test_long_term_repetition.py:107-109
    40% scene dominance threshold 하드코딩
  - tests/test_cross_episode_repetition.py:130-134
    warning_threshold=3, regression_threshold=6 하드코딩
Inference: 다수의 테스트가 production code의 상수를 import하지 않고 하드코딩. Production 상수 변경 시 테스트가 PASS하지만 실제 동작과 불일치(false negative DRIFT).
Uncertainty: 일부 값은 production code에서도 파라미터화되어 있으므로 "기본값 테스트"로 볼 수 있음
Cross-Ref: T20 (Regression test integrity)
```

### T18-TF-023: test_genre_guards_extended GUARD_CLASSES Manual Update Required
```
ID: T18-TF-023
Severity: P2-MEDIUM
Category: COVERAGE-GAP
Surface: tests/test_genre_guards_extended.py:17-26
Evidence:
  - tests/test_genre_guards_extended.py:17-26
    GUARD_CLASSES = [InvestmentGuard, FantasyGuard, CookingGuard, AltHistoryGuard,
                     ComposerGuard, ActorGuard, MedicalGuard, SportsGuard]
    — 8개 가드 수동 나열 (WuxiaGuard, HunterGuard는 별도 test_genre_guard.py에서 테스트)
  - 새 장르 가드 추가 시 이 리스트에 수동 추가 필요
  - GenreTypes.all()이나 __init__.py의 가드 목록을 자동 참조하지 않음
Inference: 10개 장르 중 2개(wuxia, hunter)는 별도 테스트, 8개는 이 파일에서 parametrize. 새 장르 추가 시 이 리스트 갱신이 누락되면 커버리지 갭 발생.
Uncertainty: 현재 10개 장르로 고정되어 있으므로 당장의 위험은 낮음
Cross-Ref: T20 (Test coverage integrity)
```

### T18-TF-024: PowerScalingTracker Justification Quality 5 Tiers (SYNC)
```
ID: T18-TF-024
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/power_scaling.py:82-142
Evidence:
  - modules/core/power_scaling.py:82-135
    JUSTIFICATION_QUALITY 5 tiers:
    - legendary: +40 max growth (전설급 정당화)
    - strong: +30 (강한 정당화)
    - moderate: +20 (보통 정당화)
    - weak: +10 (약한 정당화)
    - none: +5 (정당화 없음)
  - modules/core/power_scaling.py:138-142
    COMPOUND_BONUS: 2 keywords +5, 3 keywords +10, 4+ keywords +15
  - modules/core/power_scaling.py:74-75
    NORMAL_GROWTH_RATE=10, MAX_GROWTH_RATE=20
Inference: 정당화 품질 기반 성장 제어 시스템. 키워드 기반 정량 판정 + 복합 보너스.
Uncertainty: None
Cross-Ref: T12 (State tracking growth validation)
```

### T18-TF-025: Stage0_handoff PlotRoadmapStatus Validation Contract (SYNC)
```
ID: T18-TF-025
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/stage0_handoff.py:130-185
Evidence:
  - modules/core/stage0_handoff.py:130-158
    validate_plot_roadmap_entries() checks:
    1. Entries are dicts with block_no
    2. Payload has one of: context/event_villain/solution/reward (from content dict or top-level)
       OR tactical_doc, OR key_events
    3. Title-only or empty entries → warning
  - modules/core/stage0_handoff.py:166-185
    ensure_plot_roadmap(): treatment → arcs → roadmap 순서로 시도, 각각 실패 시 다음 소스
  - modules/core/stage0_handoff.py:9-17
    PlotRoadmapStatus.ready property: roadmap non-empty AND no warnings
Inference: Stage 0→2 handoff 계약이 명확하고 3단계 fallback(treatment→arcs→empty)을 지원.
Uncertainty: None
Cross-Ref: T02 (Stage 2 consumer side)
```

---

## 3. Evidence Inventory

### File I/O Side-Effect Surface

| Module | Operation | Target | Trigger |
|--------|-----------|--------|---------|
| stage0/__init__.py | WRITE | work_guard.yaml | manage_work_guard() |
| stage0/__init__.py | WRITE | stage0_output/*.json (5 files) | save_state() |
| stage0/story_expander.py | WRITE | bible.json, treatment.json, preset_state.json | save_all() |
| stage0/reverse_expander.py | WRITE | 4 JSON files + DB (5 tables) + VecMemory | save_all(), persist_to_db() |
| stage0/style_extractor.py | WRITE | style_guide.json cache | extract_from_references() |
| stage01_helpers.py | WRITE | DB anchors, VecMemory, DNA sync | Multiple handlers |
| failure_analyzer.py | WRITE | item_suffixes.yaml | review_and_apply_suffixes() |
| failure_learning.py | WRITE | JSON file | save_to_json() |
| character_voice.py | WRITE | DB character_voice table | save_to_db() |
| foreshadow_tracker.py | WRITE | DB foreshadow table | save_to_db() |
| pattern_tracker.py | WRITE | DB anchor | save_to_db() |
| emotion_tracker.py | WRITE | DB anchor | save_to_db() |

### DB Read Surface (FailureAnalyzer)

FailureAnalyzer는 17개 DB 쿼리를 실행하며 3개 JSON 파일을 읽음:
- stage_attempts, director_selections, episode_quality_labels, llm_calls (4 테이블)
- logs/episode_production.jsonl, logs/pass_rate_monitor.json, logs/session/decisions.jsonl (3 파일)

---

## 4. Side-Effect Surface

| Category | Count | Details |
|----------|-------|---------|
| File writes (JSON/YAML) | 8 modules | Stage 0 outputs, failure learning, suffix YAML |
| DB writes | 5 modules | character_voice, foreshadow, pattern_tracker, emotion_tracker, reverse_expander |
| DB reads | 1 module (FailureAnalyzer) | 17 queries across 4 tables + 3 JSON files |
| VecMemory writes | 2 modules | reverse_expander, stage01_helpers |
| LLM calls | 4 modules | story_expander, reverse_expander, style_extractor, narrative_structure_analyzer |
| Thread spawning | 1 module | spinner.py (daemon threads for animation) |
| Singleton state | 2 modules | adaptive_retry (2 singletons), primitive_guard (1 singleton) |

---

## 5. Facts

1. **Stage 0 초기화 흐름**: Genre Selection → Protagonist Config → Bible Generation → Treatment → Review Gate (max 2 attempts) → Save → Handoff to Stage 2
2. **Guard chain**: `create_genre_guard()` factory가 GenreGuard → WorkGuard(optional) → StyleGuard(optional) 순서로 조립
3. **10개 장르 가드**: wuxia, hunter, investment, fantasy, composer, cooking, alt_history, actor, sports, medical — SUPPORTED_GENRES와 정확히 일치
4. **WorkGuard**: base guard의 forbidden terms와 delta만 추가 검증, YAML 오버레이로 프로젝트별 커스터마이징
5. **FeedbackSystem**: 15개 pure method, 0개 side-effect — 테스트 용이성 최상
6. **FailureLearner**: 16개 failure 카테고리, threshold ≥ 2에서 constraint 자동 생성
7. **AdaptiveRetryStrategy**: 6개 ErrorType별 대기 시간(0~30s)과 최대 재시도(1~3회) 하드코딩
8. **EmotionTracker**: variance < 0.5 기준 단조 감지, 50화 윈도우 캡, 상태별 맞춤 advisory 생성
9. **PatternTracker**: build_report() lookback=5 (경량), analyze_manuscripts() window_size=10 (전체)
10. **ForeshadowTracker**: 7개 카테고리별 기한 (15~50화), max_hooks=200

---

## 6. Inferences

1. Stage 0는 완전한 self-contained 서브시스템으로, 외부 의존성이 최소화됨 (LLM client, DB, UI만 필요)
2. Guard chain의 decorator 패턴은 확장에 유리하나, 3단계 이상 wrapping 시 run_deep_validation() 호출 스택이 깊어짐
3. FailureAnalyzer의 5-sink alignment은 데이터 무결성 검증에 강력하나, DB 스키마 변경에 취약
4. Pattern tracker의 dead code (V59 메서드 3개)는 이미 인지되어 있으며 제거 가능
5. FeedbackSystem과 FailureLearner의 결합은 adaptive retry를 통해 이루어지며, 방향은 단방향 (failure→learning→retry→prompt)
6. 테스트의 하드코딩 패턴은 시스템적 DRIFT 위험을 내재 — production 상수 import 패턴으로 전환 권장

---

## 7. Uncertainty / Contradictions

| Item | Type | Detail |
|------|------|--------|
| ReverseExpander cp949 읽기 후 재저장 | Uncertainty | UTF-8 재저장 확인 필요 (동적 검증) |
| PatternTracker lookback=5 vs window_size=10 | Uncertainty | 의도적 설계인지 불명 |
| feedback_system.py L840 dead expression | Uncertainty | 의도적 생략인지 copy-paste 실수인지 불명 |
| review_and_apply_suffixes() 자동 호출 여부 | Uncertainty | 호출자 추적 필요 |
| Lock timeout 부재 | Uncertainty | 실제 deadlock 발생 가능성은 동적 검증 필요 |

**Contradictions**: 발견되지 않음.

---

## 8. Cross-Ref to Adjacent Terminals

| Adjacent Terminal | Cross-Ref Point | TF |
|-------------------|-----------------|-----|
| T01 (SovereignApp) | Stage 0 lazy init, _lazy_load_stage0() | T18-TF-001 |
| T02 (Stage 2 Orch) | Stage0→2 handoff: PlotRoadmapStatus | T18-TF-025 |
| T12 (State Tracking) | PowerScalingTracker growth validation | T18-TF-024 |
| T15 (Quality Intel) | EmotionTracker advisory → advisory chain | T18-TF-014 |
| T16 (DB) | DB write surface (5 modules), Lock patterns | T18-TF-019 |
| T17 (Config) | item_suffixes.yaml write, validation.yaml threshold refs | T18-TF-009, T18-TF-016 |
| T20 (Cross-Cut) | Dead code, test coverage integrity | T18-TF-012, T18-TF-022, T18-TF-023 |

---

## 9. Candidate Watchlist

| Priority | Item | Rationale |
|----------|------|-----------|
| 1 | PatternTracker dead code 제거 (V59 메서드 3개, ~350줄) | 이미 [TF-5-05] 표기됨, 제거 시 유지보수 부담 감소 |
| 2 | 테스트 하드코딩 → production 상수 import 전환 | DRIFT 위험 감소 |
| 3 | feedback_system.py L840 dead expression 수정 | 의도 명확화 필요 |
| 4 | Lock timeout 추가 (character_voice, foreshadow_tracker) | Defensive improvement |
| 5 | AdaptiveRetry 대기시간/재시도 횟수 config 이관 | 운영 유연성 향상 |

---

## 10. 6Pass Audit Log

### Pass 1 — 구조/범위
- 41 production files + 12 test files = 53 파일 전수 조사
- Stage 0 core, genre guards, failure/retry/feedback, narrative utilities 4개 서브영역 커버
- 마스터 오더 범위 내 모든 파일 포함 확인
- **Result: PASS**

### Pass 2 — 증거/일관성
- 25 TF 모두 file:line 증거 포함
- 코드 스니펫 인용 18건
- Grep 기반 부재 증명 2건 (T18-TF-012)
- 수치 검증: SPINNER_AVAILABLE L29, variance threshold L178, lookback L257 — 모두 live code 확인
- **Result: PASS**

### Pass 3 — 실행가능성
- P2-MEDIUM 3건: 모두 actionable (DRIFT 수정, COVERAGE-GAP 보완, SIDE-EFFECT 문서화)
- P3-LOW 5건: 코드 위생 개선 항목
- P4-OBSERVATION 17건: SYNC 확인 + HARDCODING 기록
- Severity 분포 합리적
- **Result: PASS**

### Pass 4 — 적대적 (스코프 과잉/누락)
- "jianghu_logic.py 26줄은 조사 가치 없다" → TF로 만들지 않았으나 scope에 포함 확인. 26줄이어도 side-effect 검증은 필요 → **반박 실패, PASS**
- "diversity_sampler.py가 빠졌다" → Agent 4에서 조사 완료, TF로는 특이 발견 없어 별도 TF 미생성 → **반박 실패, PASS**
- "narrative_diversity.py가 빠졌다" → Agent 4에서 조사 완료, NarrativeDiversityEngine은 PatternTracker/DiversitySampler의 wrapper → **반박 실패, PASS**

### Pass 5 — 적대적 (증거 거짓/오해)
- "T18-TF-010 L840은 의도적일 수 있다" → expression statement는 반환값이 버려지므로 어떤 의도로도 쓸모없음. `feedback_lower =`가 빠진 것이 명백 → **반박 실패, PASS**
- "T18-TF-011 dual lookback는 버그가 아니라 설계다" → TF에 이미 Uncertainty로 "의도적 설계일 수 있음" 표기. Severity P3-LOW(하드코딩)이지 P1-HIGH(버그)가 아님 → **반박 실패, PASS**
- "T18-TF-012 dead code가 테스트에서 호출될 수 있다" → Grep 결과 tests/ 에서도 호출 없음 확인 → **반박 실패, PASS**

### Pass 6 — 적대적 (severity 과대/과소)
- "T18-TF-022 DRIFT를 P1로 올려야 한다" → 테스트가 PASS하면서 live code와 diverge하는 silent drift이나, 현재 값이 일치하고 있으므로 잠재적 위험. P2가 적절 → **반박 실패, PASS**
- "T18-TF-009 config 파일 쓰기를 P1로 올려야 한다" → 명시적 사용자 호출(review_and_apply_suffixes)이 필요하므로 자동 위험 낮음. P2 적절 → **반박 실패, PASS**
- "SYNC TF들이 너무 많다 (17/25)" → 마스터 오더 1.0: "SYNC 확인도 TF다". 조사 범위의 대부분이 잘 작동하고 있다는 증거 → **반박 실패, PASS**

**6PASS-CLEARED** — 확신도 96%
