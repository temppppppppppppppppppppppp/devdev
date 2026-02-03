# CHANGELOG

버전별 변경 내역. 최신 버전이 상단에 위치.

---

## V60.32 - Stage 2 폴백 체인 수정

**문제 1**: FourPhase/StateLocked가 `attempt == 0`에서만 사용 가능
- 재시도 시 최고 품질 생성기를 사용할 수 없었음

**수정**: 모든 attempt에서 FourPhase/StateLocked 사용 가능

**문제 2**: Analyst 폴백 시 protagonist_name 미전달
- LLM이 주인공 이름을 환각하는 문제 발생

**수정**: Analyst 호출 시 protagonist_name 파라미터 추가

**문제 3**: SelfReflector가 `attempt == 0`에서만 동작

**수정**: Analyst 방식에서 모든 attempt에 SelfReflector 적용

**수정된 폴백 체인**:
```
모든 attempt:
├── 1순위: FourPhaseArcGenerator (90%+ 통과율)
├── 2순위: StateLockedArcGenerator (상태 잠금)
├── 3순위 (attempt≥1): TwoPhaseArcGenerator
├── 4순위 (attempt≥2): TreeOfThoughts 필살기
└── 최종 폴백: Analyst + SelfReflector
```

---

## V60.31 - 가변 페이싱 복원

**문제**: 가변 페이싱이 작동하지 않음 - 모든 Arc가 5화로 고정됨
**원인**: `curr_block.get('logic', {})` - Block에 'logic' 키가 없음

**수정**:
1. Block 구조 기반 분석 - `content.context/event_villain/solution/reward` 분석
2. LLM에 결정권 부여 - 시스템은 권장값만 제시
3. LLM 결정 존중 - 후처리에서 LLM이 결정한 ep_count 사용

**페이싱 기준**:
| 페이싱 | ep_count | 적용 기준 |
|--------|----------|-----------|
| Blitz | 2-3화 | 짧은 전투/탈출, 800자 미만 |
| Standard | 3-4화 | 일반적인 사건, 800-1500자 |
| Epic | 5-6화 | 대규모 전투/전환점, 1500자 초과 |

---

## V60.30 - ArcDraftValidator 화별 분할 검증 강화

tactical_doc의 화별 구분 검증 3가지 새로운 체크 추가:

1. **화별 비트 수 검증** - 각 화당 최소 3개의 비트(사건)
2. **화별 구조 요소 검증** - 공간/인과/상태 요소 존재 확인
3. **ep_count 동기화 검증** - 선언된 ep_count와 실제 화 개수 일치

---

## V60.29 - 화별 분할 검증 강화

**검증 항목**:
- 화 존재 여부 (누락 감지)
- 각 화 최소 300자
- 화간 균형 (max/min < 5배)
- 화 순서 연속
- 화 내용 품질 (대사/행동 포함)

---

## V60.28 - Stage 2 초기 통과율 개선

- **ThinkingConfig 수정**: `thinking_level` 문자열을 정수로 변환 (Gemini 3 API 호환)
- **Arc 1 Consensus 최적화**: 이전 Arc 없을 시 `continuity_focused` 검증 스킵
- **중복 아이템 방지 강화**: ConstraintCompiler, PreflightChecker, FourPhaseArcGenerator 개선

---

## V60.23 - 내공 바닥 방지

**문제**: 무협 주인공이 5화 연속 내공 0%는 서사적으로 불가능

**해결**: 2단계 안전장치
1. Arc 레벨: `final_energy` 최소 10% 보장
2. Episode 레벨: 내공 5% 이하 3화 연속 시 강제 회복 20%

---

## V60.22 - 내공 0% 버그 수정

**문제**: HUD에서 내공이 5화 연속 0%로 표시

**원인**:
1. `convert_to_numeric`에서 "무" 키워드가 "무공", "무형" 등에도 매칭
2. Writer가 "+50" 델타값 출력 → HUD가 절대값으로 오해석

**수정**:
- `base_guard.py`: 델타값 처리 + "무" 정확 매칭
- `writer.py`: 델타값 대신 절대 퍼센트 출력

---

## V60.21 - Focus Mode (정보 과부하 방지)

**문제**: LLM이 재시도 시 너무 많은 정보(8개 컴포넌트)에 익사

**해결**:
1. 재시도 시 V51 주입 스킵
2. 피드백 극소화: 8개 → 1개 핵심 메시지
3. 컨텍스트 최소화

| 항목 | 이전 | V60.21 |
|------|------|--------|
| 피드백 크기 | ~3000자 | ~300자 |
| 재시도 컨텍스트 | 동일+피드백 | 최소화 |

---

## V60.20 - 아이템 비교 False Positive 방지

**문제**: "장"이 "비자금 장부"와 100% 유사하다고 판정

**수정 로직** (`arc_draft_validator.py`):
1. 완전 일치 우선
2. 최소 길이 체크: 1글자는 부분 매칭 불가
3. 길이 비율 체크: 2배 이상 차이나면 다른 아이템
4. 포함 관계 강화: 양쪽 3자 이상 + 60% 이상

---

## V60.19 - 강하고 친절한 피드백

**문제**: Analyst가 REJECT 피드백을 받고도 같은 실수 반복
**원인**: 피드백이 컨텍스트 하단에 배치되어 LLM이 무시

**해결**: 피드백을 컨텍스트 최상단에 주입 + 시각적 강조

---

## V60.18 - 주인공 이름 일관성 강제

**문제**: 재시도 시 LLM이 주인공 이름을 환각 (팽무진 → 이현)

**수정**: 모든 Arc 생성 프롬프트에 주인공 이름 강제 블록 추가
- `two_phase_generator.py`
- `tree_of_thoughts.py`
- `arc_ensemble.py`
- `four_phase_arc_generator.py`
- `main_a.py`

---

## V60.17 - Speculative Generation + Preflight 캐싱

**Speculative Generation**:
- Flash 모델로 초안 빠르게 생성
- Pro 모델로 초안 정제
- 50% 속도 향상

**Preflight 캐싱**:
- 첫 시도에서 constraint_block 캐시 저장
- 재시도 시 캐시 재사용 (재시도당 ~$0.02 절감)

---

## V60.16 - 버그 픽스

- `model_tier → primary_model`: StateLockedArcGenerator 수정
- `protagonist_name` 전파 완전 연결
- JSON 파싱 강화: 다중 방법 파싱
- Pattern Index 버그 수정

---

## V60.15 - NarrativeStructureAnalyzer

코사인 유사도 대신 LLM 기반 서사 요소 추출:
- 행위(action), 장소(location), 결과(outcome) 3요소 추출
- 연속 5개 이상 동일 시에만 STAGNATION 판정
- 비용: ~$0.005/Arc (flash 모델)

---

## V60.14 - StateLockedArcGenerator

이전 Arc 종료 상태를 정확히 계승하는 Arc 생성:
- `_extract_state()`: LLM 기반 arc_end_state 추출
- `_build_state_locked_prompt()`: 상태 잠금 프롬프트 구축
- 주인공 이름 자동 주입

---

## V60.12 - Four-Phase Pipeline

Stage 2 초기 통과율 극대화 (예상 90%+):

```
Phase 1: Preflight   → 완벽한 제약 맵 구축
Phase 2: Generate    → Ensemble 생성 (3개 후보)
Phase 3: Critique    → 즉시 비평 + 자동 수정
Phase 4: Validate    → 3-LLM 합의 검증
```

**새 에이전트**:
- `FourPhaseArcGenerator`
- `PreflightChecker`
- `ArcCritic`
- `ConsensusValidator`
- `NegativeExampleInjector`

**비용**: ~$0.15-0.20/Arc (기존 대비 약 5x)

---

## V60.11 - Ensemble Generation + Pre-Validation

Stage 2 PASS율 향상 (3x 비용 투자):

**ArcEnsembleGenerator**: 3개 Arc 후보 병렬 생성
- Conservative (온도 0.3): 안정성/연속성 우선
- Balanced (온도 0.5): 균형
- Creative (온도 0.7): 서사적 흥미 우선

**ArcDraftValidator**: Python 기반 사전 검증 (LLM 비용 0원)
- 필수 필드 검사
- 중복 아이템 획득 탐지
- 위치 연속성 검증
- 부상 상태 계승 확인
- 수여물 타임라인 체크
- tactical_doc 분량 확인

**ConstraintCompiler**: 구조화된 제약 체크리스트 생성

---

## V60.10 - StateExtractor 통합

이전 Arc 상태를 구조화된 JSON으로 추출:
- `extract_state()` - 단일 Arc 상태 추출
- `extract_cumulative_state()` - 여러 Arc 누적 상태
- `generate_constraint_prompt()` - Analyst용 제약 프롬프트

**추출 필드**: protagonist_state, inventory, relationships, grants_received, next_arc_constraints

---

## V60.1 - Integration & Dashboard

- V0128 Config Fallback
- HUD Anomaly Audit Logging
- Blueprint Completeness Pre-LLM Filter
- Quality Dashboard (`modules/core/quality_dashboard.py`)

---

## V60 - Quality Pipeline Enhancement

8가지 품질 개선 (LLM 비용 0):

1. Arc State Succession Verification
2. Tactical Doc Continuity Validation
3. Joint Docs Auto-Correction
4. Stage 4 Retry Limit with Force Pass
5. Blueprint Completeness Verification
6. Enhanced Item Acquisition Extraction
7. Scene Structure Validation
8. HUD Sudden Change Detection
9. Asyncio Compatibility

**예상 효과**:
- Stage 2 PASS율: +15%
- Stage 3 PASS율: +10%
- Stage 4 PASS율: +20%

---

## V55.2 - Constitutional Self-Check + ToT 4분기

**Constitutional Self-Check**: LLM이 출력 전에 자가 검증

| Stage | 조항 수 | 핵심 체크 |
|-------|---------|----------|
| 2 (Arc) | 6개 | 아이템 중복, 수여물 중복, joint_docs 계승 |
| 3 (Blueprint) | 5개 | cliffhanger 계승, 씬 개수, ending_hook |
| 4 (Manuscript) | 7개 | 미획득 아이템, 관계 급변, Show Don't Tell |

---

## V55.1 - Stage 2 향상 모듈 통합

**재시도 분기 로직**:
| Attempt | 전략 | 모듈 |
|---------|------|------|
| 0 | 일반 Analyst + 자기 비판 | SelfReflector |
| 1 | 2단계 생성 | TwoPhaseArcGenerator |
| ≥2 | ToT 필살기 | TreeOfThoughts.explore_arc |

---

## V55 - Manuscript Quality & Length Enhancement

**ManuscriptEnhancer** 7개 서브모듈:
1. ClicheBreaker - 클리셰 탐지 + 대안
2. ForeshadowBalancer - 복선 타이밍 최적화
3. SubtextExpander - Telling → Showing 변환
4. PageTurnerScorer - 몰입도 측정
5. LengthQualityGate - 씬별 최소 분량
6. SceneDensityEnforcer - 씬 필수 요소
7. DialogueBeatInjector - 액션/리액션 비트

---

## V54 - Cost Optimization & Enhancement

1. **SemanticCache** - 의미론적 캐싱
2. **ContextCompressor** - 토큰 30-40% 절감
3. **AdaptiveRetryManager** - 에이전트별 실패 통계
4. **TwoPhaseGenerator** - 2단계 생성 (Skeleton → Flesh)
5. **SuccessPatternMemory** - 성공 패턴 학습

---

## V53 - Advanced AI Techniques

1. **DynamicPromptWeighter** - 실패 패턴 기반 가중치
2. **TreeOfThoughts** - 분기 탐색 최적 경로
3. **AdversarialSelfPlay** - 적대적 자기 대결
4. **MultiAgentDeliberation** - 다중 에이전트 토론
5. **NarrativeDiversityEngine** - 서사 다양성 통합

---

## V52 - Self-Improvement Suite

1. **SelfReflector** - 자기 성찰 및 자동 개선
2. **AdaptiveRetry** - 에러 타입별 재시도 전략
3. **ExpertMixture** - 씬 유형별 전문가 프롬프트
4. **CrossAgentVerifier** - 에이전트 간 교차 검증

---

## V51 - Zero-Cost Analysis Suite

1. **PacingAnalyzer** - 호흡 분석 (LLM 비용 0원)
2. **QualityAmplifier** - 제약 주입으로 성공률 향상
3. **AgentIntelligence** - Few-Shot + Anti-Pattern + Self-Critique

---

## V50 - Narrative Quality Enhancement Suite

1. **TensionCurveManager** - 긴장도 곡선 관리
2. **DialogueQualityEngine** - 대사 DNA 엔진
3. **SubplotWeaver** - 서브플롯 관리
4. **ReaderSimulator** - 가상 독자 시뮬레이션

---

## V49.5 - Manuscript Continuity Inspector

**Python Precheck 9개 체크** (LLM 비용 0원):
1. 미획득 아이템 사용
2. 부상 상태 연속성
3. Blueprint 핵심 씬 반영
4. 관계 급변 탐지
5. 악역 지능 보호
6. 시간 흐름 검증
7. 공짜 파워업 감지
8. 갑작스러운 능력
9. 주인공 무쌍 과다

---

## V49 - Arc Continuity Inspector

Stage 2에서 Arc간 타임라인 검증:
- Cross-Arc Item Timeline
- Cross-Arc Grant Timeline
- Cross-Arc State Timeline
- Intra-Arc Consistency
- Setting Consistency

**Three-Phase Validation**:
1. Python Precheck (무료)
2. Joint Docs Auto-Correction
3. LLM Deep Check (~$0.02-0.05)

---

## V48 - Narrative Diversity Engine

**Core Components**:
1. **PatternTracker** - 패턴 반복 감지
2. **DiversitySampler** - 앙상블 다양성 선택
3. **NarrativeDiversityEngine** - 통합 엔진
4. **Contrastive CoT** - 부정 예시 프롬프팅

**RelationshipTracker**: NPC 관계 FSM
**InformationDiffusion**: 정보 전파 시뮬레이션
**JustificationPatterns**: Few-shot 정당화 라이브러리

---

## V47 - Continuity Validator

Python 기반 에피소드간 연속성 체크 (LLM 비용 0원):
- 중복 아이템 획득 감지
- 무기 상태 리셋 감지
- 부상 연속성 (경고)
- 위치 연속성 (경고)

---

## V41 - Stage 1 Skip Option

DB에 volumes 존재 시 Stage 1 스킵 옵션 제공.

---

## V40 - Model Tier System

Architect/Writer 에이전트 점진적 모델 업그레이드:
- Tier 1: gemini-2.5-flash (첫 시도)
- Tier 2: gemini-2.5-pro (1회 실패)
- Tier 3: gemini-3-pro-preview (2회+ 실패)

77% 비용 절감 (블루프린트 기준)

---

## V31 - Quad-Cache System

4개 전용 캐시 (24시간 TTL):
- writer_cache
- architect_cache
- analyst_cache
- weaver_cache

---

## Module Summary

| Version | Modules | Focus |
|---------|---------|-------|
| V50 | 3 | 긴장도, 대사, 서브플롯 |
| V51 | 6 | 호흡, 감정, 실패학습 |
| V52 | 4 | 자기성찰, 적응형재시도 |
| V53 | 5 | ToT, ASP, MAD |
| V54 | 5 | 캐시, 압축, 2단계생성 |
| V55 | 7 | 분량/품질 향상 |
| V60 | 9+ | 품질 파이프라인 강화 |
| **Total** | **54+** | - |
