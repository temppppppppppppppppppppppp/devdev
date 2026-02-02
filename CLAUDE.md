# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Wuxia Studio V60.24** (Sovereign App) - AI-powered multi-genre novel writing system using Google Gemini API to orchestrate specialized agents for serialized fiction production.

**Supported Genres:**
- Wuxia (무협) - Martial arts fiction
- Hunter (헌터) - Modern dungeon/gate fiction
- Investment (투자) - Financial reincarnation fiction

## Running the Application

```bash
# Install dependencies (from requirements in backup folder)
pip install google-generativeai google-genai chromadb python-dotenv rich

# For dashboard UI (optional)
pip install streamlit

# Create .env file with your API key
echo "GOOGLE_API_KEY=your_key_here" > .env

# Run main application
python main_a.py

# Run dashboard (optional)
streamlit run studio_dashboard.py
```

## Utility Tools

Located in `tools/` directory:
- `concat_txt.py` - Concatenate episode text files
- `db_porter.py` - Database migration utilities
- `normalize_arcs_db.py` - Arc data normalization
- `fix_future_items.py` - Fix future items in manuscripts
- `make_BP.py` - Blueprint generation utility

Located in root:
- `RESET.py` - Selective project reset (clears DB/ChromaDB for chosen project)
- `make_md.py` - Convert manuscripts to markdown

## Production Pipeline (5 Stages)

```
Phase 0: Bible Recovery & DNA Sync → Load lore + treatment, sync to SQLite
Stage 1: Volume Strategy          → Plan 10 volumes (can be skipped if volumes exist)
Stage 2: Arc Tactical Design      → Design 50 arcs (5 per volume) + [V49] Arc 연속성 검증
Stage 3: Episode Blueprinting     → Scene-by-scene plans + Episode 연속성 검증
Stage 4: Sovereign Production     → Final manuscript writing + [V49.1] 원고 연속성 검증
```

**Stage 2 Continuity Check (V49 NEW):**
Arc 설계 후 Director 검증 전에 `ContinuityInspector.inspect_arc()` 호출. Arc 간 아이템/수여물 타임라인 + 단일 Arc 내 모순을 검증하여 REJECT 시 재설계 요청.

**Stage 4 Manuscript Continuity Check (V49.1 NEW):**
Writer 원고 생성 후 Director 검증 전에 `ContinuityInspector.inspect_manuscript()` 호출. 이전 원고들과의 연속성 + Blueprint 일치성을 검증하여 REJECT 시 재생성 요청. 최대 2회 재시도 후 경고와 함께 진행.

**V60 Quality Enhancements:**
- **Stage 2**: Arc 상태 계승 검증 + 화간 연속성 + Joint Docs 자동보정
- **Stage 3**: 씬 구조 검증 (최소 6개) + 아이템 추출 false positive 필터링
- **Stage 4**: Blueprint 완전성 검증 (70% 씬 반영) + HUD 급변 감지 + 무한 재시도 방지 (강제 통과)

**V60.10 Stage 2 고도화 (StateExtractor 통합):**
- **StateExtractor 에이전트**: 이전 Arc들의 상태(부상/내공/소지품/위치/관계/수여물)를 구조화된 JSON으로 추출
- **_generate_arc_context_v60()**: StateExtractor 활용한 정밀 맥락 생성 (Python 폴백 포함)
- **TwoPhaseArcGenerator 통합**: StateExtractor 제약 자동 주입, flash 모델로 속도 향상
- **REJECT 패턴 분석**: `_analyze_rejection_pattern_v60()` - 반복 REJECT 사유 분석 및 타겟 피드백 생성
- **피드백 루프 수정**: REJECT 후 `refined_arc = None` 설정으로 Analyst 재호출 보장

**V60.11 Stage 2 비용 3x 고도화 (Ensemble + Pre-Validation):**
- **ArcEnsembleGenerator**: 3개 Arc 후보 병렬 생성 후 최적 선택
  - Conservative(온도 0.3): 안정성/연속성 우선
  - Balanced(온도 0.5): 연속성과 새로움의 균형
  - Creative(온도 0.7): 서사적 흥미 우선
  - 100점 만점 휴리스틱 평가 (필드완성도 20 + 제약준수 30 + 연속성 25 + tactical품질 25)
- **ArcDraftValidator**: Python 기반 사전 검증 (LLM 비용 0원)
  - 필수 필드 완전성 검사
  - 중복 아이템 획득 탐지
  - 위치 연속성 검증
  - 부상 상태 계승 확인
  - 수여물 타임라인 체크
  - tactical_doc 분량 확인 (최소 2000자)
- **ConstraintCompiler**: 구조화된 제약 체크리스트 생성
  - MUST NOT DO: 금지 아이템/수여물 목록
  - INHERITED STATE: 시작 위치/소지품/부상/내공
  - MUST DO: 필수 계승 사항
  - SELF-CHECK: 생성 후 자체 검증 항목

**V60.12 Stage 2 비용 5x 초기통과율 극대화 (Four-Phase Pipeline):**
- **FourPhaseArcGenerator**: 4단계 파이프라인 오케스트레이터 (~$0.15-0.20/Arc)
  - Phase 1 (Preflight): 완벽한 제약 맵 구축
  - Phase 2 (Generate): Ensemble 생성 (3개 후보)
  - Phase 3 (Critique): 즉시 비평 + 자동 수정
  - Phase 4 (Validate): 3-LLM 합의 검증
- **PreflightChecker**: 생성 전 완벽 분석 (gemini-2.5-pro)
  - 아이템/수여물 타임라인 분석
  - 관계 맵 + 세계 상태
  - 절대 금지 사항 목록화
- **ArcCritic**: 생성된 Arc 즉시 비평
  - 7개 항목 70점 만점 평가
  - PASS/NEEDS_REVISION/REJECT 판정
  - 자동 수정 가능 항목 적용
- **ConsensusValidator**: 3-LLM 합의 검증
  - 연속성/구조/서사 전문가 3관점
  - CRITICAL 이슈 있으면 즉시 REJECT
  - 2/3 이상 REJECT시 최종 REJECT
- **NegativeExampleInjector**: 실패 사례 기반 Few-Shot
  - 6가지 실패 패턴 라이브러리
  - REJECT 히스토리 학습
- **예상 초기 PASS율: 90%+**

**V60.14 StateLockedArcGenerator - 상태 잠금 Arc 생성:**
- **StateLockedArcGenerator**: 이전 Arc 종료 상태를 정확히 계승하는 Arc 생성
  - `_extract_state()`: LLM 기반 arc_end_state 추출 (flash 모델)
  - `_build_state_locked_prompt()`: 상태 잠금 프롬프트 구축
  - 주인공 이름 자동 주입 (`protagonist_name` 파라미터)
  - 템플릿에 "🔒 주인공 정보" 섹션으로 이름 사용 강제
- **적용 시점**: Stage 2에서 이전 Arc 종료 상태를 다음 Arc 시작 상태로 강제 연결

**V60.15 NarrativeStructureAnalyzer - 진짜 서사 구조 분석:**
- **NarrativeStructureAnalyzer**: 코사인 유사도 대신 LLM 기반 서사 요소 추출
  - 행위(action), 장소(location), 결과(outcome) 3요소 추출
  - 연속 5개 이상 동일 시에만 STAGNATION 판정 (관대한 기준)
  - 부분 반복(4/5 동일)은 WARNING 수준으로만 처리
  - "진도가 하나도 안 나가는" 극단적 경우만 탐지
- **비용**: ~$0.005/Arc (flash 모델)
- **장르 특성 반영**: 무협 장르에서 비슷한 패턴은 자연스러움으로 인정

**V60.16 버그 픽스:**
- **model_tier → primary_model**: StateLockedArcGenerator에서 올바른 속성 사용
- **protagonist_name 전파**: main_a.py → StateLockedArcGenerator → 템플릿 완전 연결
- **JSON 파싱 강화**: 다중 방법 파싱 (직접 → 코드블록 제거 → 정규식 추출)
- **Pattern Index 버그**: _detect_stagnation에서 연속 구간 정확한 인덱스 추적

**V60.17 Speculative Generation + Preflight 캐싱:**
- **Speculative Generation (투기적 생성)**:
  - Flash 모델로 초안 빠르게 생성 (`draft_model: gemini-2.5-flash`)
  - Pro 모델로 초안 정제 (`refine_model: gemini-3-pro-preview`)
  - 50% 속도 향상 (Flash 선제 처리로 Pro 대기 시간 감소)
  - `use_speculative` 플래그로 활성화/비활성화
- **Preflight 캐싱**:
  - 첫 시도에서 constraint_block 캐시 저장
  - 재시도 시 캐시 재사용 (Preflight 스킵)
  - `cached_preflight`, `cached_constraint_block` 변수 활용
  - 재시도당 ~$0.02 절감

**V60.18 주인공 이름 일관성 강제 (Protagonist Name Injection):**
- **문제**: 재시도 시 LLM이 주인공 이름을 환각 (팽무진 → 이현)
- **원인**: StateLockedArcGenerator만 protagonist_name 파라미터를 받고, 나머지 폴백 경로는 받지 않음
- **수정된 파일**:
  - `two_phase_generator.py`: TwoPhaseArcGenerator에 protagonist_name 추가
  - `tree_of_thoughts.py`: TreeOfThoughts.explore_arc()에 protagonist_name 추가
  - `arc_ensemble.py`: ArcEnsembleGenerator에 protagonist_name 추가
  - `four_phase_arc_generator.py`: FourPhaseArcGenerator에 protagonist_name 추가
  - `main_a.py`: 모든 Arc 생성 호출부에 protagonist_name 전달
- **프롬프트 주입**: 모든 Arc 생성 프롬프트에 주인공 이름 강제 블록 추가
  ```
  ##############################################################
  # 🔒 [V60.18] 주인공 정보 - 반드시 이 이름을 사용!
  ##############################################################
  주인공 이름: {protagonist_name}
  → tactical_doc에서 반드시 '{protagonist_name}'을 사용하세요!
  → 다른 이름(이현, 강민수 등)은 절대 사용 금지!
  ##############################################################
  ```

**V60.19 강하고 친절한 피드백 (Strong-Kind Feedback Injection):**
- **문제**: Analyst가 Director의 REJECT 피드백을 받고도 같은 실수를 반복
- **원인**: 피드백이 컨텍스트 **하단**에 배치되어 LLM이 무시 (최근 토큰 선호 현상)
- **해결**:
  1. `_build_strong_kind_feedback()` 함수 추가: 위반사항을 시각적으로 강조
  2. 피드백을 컨텍스트 **최상단**에 주입 (LLM이 먼저 읽도록)
- **피드백 형식**:
  ```
  ████████████████████████████████████████████████████████████████
  █  🚨 [V60.19] 필수 수정 사항 - 이것만 고치면 통과!  🚨  █
  ████████████████████████████████████████████████████████████████
  ⚠️ 재시도 {attempt}회차 - 아래 사항만 수정하면 됩니다!

  ❌ 반드시 수정해야 할 사항:
     1. [위반사항]
     2. [위반사항]

  ✅ 수정 방법:
     - [구체적 가이드]

  🔒 주인공: {protagonist_name} (절대 변경 금지!)
  ████████████████████████████████████████████████████████████████
  ```
- **수정 파일**: `main_a.py` - `_build_strong_kind_feedback()` 추가, 피드백 주입 위치 변경

**V60.20 아이템 비교 False Positive 방지 (Item Comparison Fix):**
- **문제**: "장"이 "비자금 장부"와 100% 유사하다고 판정 (false positive)
- **원인**: `_is_same_item()` 함수가 길이 차이를 무시하고 포함 관계만 체크
- **수정 로직** (`arc_draft_validator.py`):
  1. **완전 일치 우선**: 길이와 무관하게 완전 일치는 True
  2. **최소 길이 체크**: 1글자는 부분 매칭 불가 (완전 일치 제외)
  3. **길이 비율 체크**: 2배 이상 차이나면 다른 아이템
     - 예: "비자금 장부"(5자) vs "장"(1자) → 5배 차이 → False
  4. **포함 관계 강화**: 양쪽 3자 이상 + 짧은쪽이 긴쪽의 60% 이상일 때만 인정
  5. **코어 비교 강화**: 접미사 제거 후에도 길이 비율 1.5배 이내만 인정

**V60.21 Focus Mode - 정보 과부하 방지 (Context Minimization):**
- **문제**: LLM이 재시도 시 너무 많은 정보(8개 컴포넌트)에 익사하여 피드백 무시
- **원인**: 재시도 시에도 V51 주입 + Constitutional + 상세 피드백 등 모두 포함
- **해결 (Focus Mode)**:
  1. **재시도 시 V51 주입 스킵**: LLM이 이미 규칙을 알고 있음
  2. **피드백 극소화**: 8개 → 1개 핵심 메시지만 (XML 태그로 강조)
  3. **컨텍스트 최소화**: `_build_minimal_arc_context()` - 이전 상태 핵심만
- **새 함수**:
  - `_build_strong_kind_feedback()`: XML 우선순위 태그 + 단일 핵심 지시 (~300자)
  - `_build_focused_context()`: 이전 상태 3줄 요약
  - `_build_minimal_arc_context()`: 재시도용 최소 컨텍스트 (~500자)
- **효과**:
  | 항목 | 이전 | V60.21 |
  |------|------|--------|
  | 피드백 크기 | ~3000자 | **~300자** |
  | 재시도 컨텍스트 | 동일+피드백 | **최소화** |
  | V51 주입 | 매번 | **첫 시도만** |

**V60.23 내공 바닥 방지 (Internal Energy Floor):**
- **문제**: 무협 주인공이 5화 연속 내공 0%는 서사적으로 불가능 (죽거나 폐인)
- **해결**: 2단계 안전장치 추가
  1. **Arc 레벨** (`main_a.py`): `final_energy` 최소 10% 보장
  2. **Episode 레벨** (`martial_manager.py`):
     - 내공 5% 이하가 2화 연속 → 경고 로그
     - 내공 5% 이하가 3화 연속 → **강제 회복 20%**
     - 절대 하한선: 5% (폐인/사망 상태 아닌 한)
- **내부 추적**: `_internal_energy_zero_streak` 카운터로 연속 바닥 감지

**V60.22 내공 0% 버그 수정 (Internal Energy Fix):**
- **문제**: HUD에서 내공이 5화 연속 0%로 표시
- **원인 1**: `convert_to_numeric`에서 "무" 키워드가 "무공", "무형" 등에도 매칭되어 0 반환
- **원인 2**: Writer가 "+50" 델타값 출력 → HUD가 절대값 50으로 오해석
- **수정 파일**:
  - `base_guard.py`: `convert_to_numeric(text, current_value)` - 델타값 처리 + "무" 정확 매칭
  - `martial_manager.py`: 현재 값 전달하여 델타 계산 지원
  - `writer.py`: 델타값 대신 절대 퍼센트 출력 (예: "70%")
- **새 로직**:
  - "+20" + 현재값 50 → 70 (델타 계산)
  - "현상 유지" → 현재값 유지
  - "무공 80%" → 80 추출 (기존: 0)
  - "무" 단독 → 0 (정확 매칭)

**V60.28 Stage 2 초기 통과율 개선:**
- **ThinkingConfig 수정**: `thinking_level` 문자열을 정수로 변환 (Gemini 3 API 호환)
- **Arc 1 Consensus 최적화**: 이전 Arc 없을 시 `continuity_focused` 검증 스킵 (2개 검증기로 합의)
- **중복 아이템 방지 강화**:
  - ConstraintCompiler: 금지 아이템 최상단 대형 경고
  - PreflightChecker: 시각적 경고 블록 추가
  - FourPhaseArcGenerator: Phase 2.5 Python 기반 빠른 중복 체크

**V60.29 화별 분할 검증 강화:**
- **목적**: Block → Arc 변환 시 각 화가 적절히 분할되었는지 검증
- **검증 항목**:
  - 화 존재 여부 (누락 감지)
  - 각 화 최소 300자
  - 화간 균형 (max/min < 5배)
  - 화 순서 연속
  - 화 내용 품질 (대사/행동 포함)
- **수정 파일**: `arc_draft_validator.py`, `analyst.py`

**V60.30 화별 구조 검증 추가:**
- **비트 수 검증**: 각 화에 최소 3개의 전술 비트 필요
- **구조 요소 검증**: 공간/행동/상태변화 키워드 존재 확인
- **ep_count 동기화**: 선언된 ep_count와 실제 화 수 일치 검증
- **수정 파일**: `arc_draft_validator.py`

**Stage 1 Skip Option (V41):**
If volumes already exist in DB, Stage 1 offers skip option. Useful for continuing existing projects or when volumes are manually edited.

## Architecture

### Core System
```
SovereignApp (main_a.py) - Main orchestrator with UTF-8 encoding, audit logging
├── StudioSystem (modules/core/system.py)
│   ├── ProjectContext (modules/core/project_manager.py)
│   │   └── DBManager (modules/core/db_manager.py) - SQLite operations
│   ├── LoreManager (modules/core/lore_manager.py) - Encyclopedia/asset management
│   ├── MartialManager (modules/core/martial_manager.py) - Character progression HUDs
│   ├── JianghuLogic (modules/core/jianghu_logic.py) - World state simulation
│   ├── GenreGuard (modules/core/genre_guard.py) - Genre-specific validation
│   │   └── Genre-specific guards (modules/core/genre_guards/)
│   ├── KarmaService (modules/core/karma_service.py) - Causality tracking
│   ├── TechniqueWeaver (modules/core/technique_weaver.py) - Skill system
│   ├── ConfigManager (modules/core/config_manager.py) - Settings loader
│   ├── NarrativeDiversityEngine (modules/core/narrative_diversity.py) - [V48] 서사 다양성 통합
│   ├── PatternTracker (modules/core/pattern_tracker.py) - [V48] 패턴 반복 감지
│   ├── DiversitySampler (modules/core/diversity_sampler.py) - [V48] 앙상블 다양성 선택
│   ├── RelationshipTracker (modules/core/relationship_tracker.py) - NPC 관계 상태 전환
│   ├── InformationDiffusion (modules/core/information_diffusion.py) - 정보 전파 시뮬레이션
│   ├── TensionCurveManager (modules/core/tension_curve.py) - [V50.1] 긴장도 곡선 관리
│   ├── DialogueQualityEngine (modules/core/dialogue_engine.py) - [V50.2] 대사 DNA 엔진
│   ├── SubplotWeaver (modules/core/subplot_weaver.py) - [V50.3] 서브플롯 관리
│   ├── ReaderSimulator (modules/core/reader_simulator.py) - [V50.4] 가상 독자 시뮬레이션
│   ├── PacingAnalyzer (modules/core/pacing_analyzer.py) - [V51.1] 호흡 분석 (LLM 비용 0원)
│   ├── QualityAmplifier (modules/core/quality_amplifier.py) - [V51.2] 품질 증폭 (성공률 향상)
│   ├── AgentIntelligence (modules/core/agent_intelligence.py) - [V51.3] 에이전트 지능 향상
│   └── NarrativeStructureAnalyzer (modules/core/narrative_structure_analyzer.py) - [V60.15] 서사 구조 분석
├── LongTermMemory (modules/core/memory_engine.py) - ChromaDB vector search
├── StudioVisualizer (modules/core/studio_visualizer.py) - Console UI with Rich
└── Agent Orchestra (modules/domain/agents/)
    ├── BaseAgent - API client + JSON healing
    ├── Analyst - Strategic planning (volumes)
    ├── Architect - Blueprint creation (episodes) [V49.5: relationship_changes, time_flow 필드 추가]
    ├── Writer - Manuscript generation [V60: HUD 급변 감지]
    ├── Director - Quality validation
    ├── ContinuityInspector - Arc/Episode/Manuscript validation [V49.5 UPDATE]
    │   ├── inspect_arc() - Stage 2 Arc 연속성 + 단일 Arc 내 모순 검증
    │   ├── inspect() - Stage 3 에피소드 연속성 검증
    │   └── inspect_manuscript() - Stage 4 원고 연속성 + 서사 품질 검증 [V49.5: 9개 Python 체크]
    ├── StateExtractor - [V60.10 NEW] 이전 Arc 상태 구조화 추출
    │   ├── extract_state() - 단일 Arc 상태 추출 (부상/내공/소지품/위치/관계)
    │   ├── extract_cumulative_state() - 여러 Arc 누적 상태 추출
    │   └── generate_constraint_prompt() - Analyst 프롬프트용 제약 텍스트 생성
    ├── ArcEnsembleGenerator - [V60.11 NEW] 3개 Arc 후보 병렬 생성
    │   ├── generate_ensemble() - 3가지 전략으로 병렬 Arc 생성
    │   ├── _generate_single() - 단일 전략 Arc 생성
    │   └── _evaluate_candidate() - 휴리스틱 후보 평가 (100점 만점)
    ├── ArcDraftValidator - [V60.11 NEW] Python 기반 Arc 사전 검증 (LLM 비용 0)
    │   ├── validate() - 종합 검증 (필드/아이템/위치/부상/수여물/분량)
    │   └── 6가지 검증: 필수필드, 중복획득, 위치연속성, 부상계승, 수여물타임라인, 분량
    ├── ConstraintCompiler - [V60.11 NEW] 구조화된 제약 체크리스트 생성
    │   ├── compile() - 이전 Arc들에서 제약 컴파일
    │   └── 4개 섹션: MUST NOT DO, INHERITED STATE, MUST DO, SELF-CHECK
    ├── FourPhaseArcGenerator - [V60.12 NEW] 4단계 Arc 생성 파이프라인
    │   ├── generate() - 4단계 파이프라인 오케스트레이션
    │   └── Preflight → Generate → Critique → Validate
    ├── PreflightChecker - [V60.12 NEW] 생성 전 완벽 분석
    │   ├── analyze() - 이전 Arc 완전 분석
    │   └── generate_analyst_injection() - Analyst 프롬프트 주입
    ├── ArcCritic - [V60.12 NEW] Arc 즉시 비평
    │   ├── critique() - Arc 비평 + 자동 수정
    │   └── 7개 항목 70점 만점 평가
    ├── ConsensusValidator - [V60.12 NEW] 3-LLM 합의 검증
    │   ├── validate_with_consensus() - 3개 관점 병렬 검증
    │   └── 연속성/구조/서사 전문가 합의
    ├── NegativeExampleInjector - [V60.12 NEW] 실패 사례 주입
    │   ├── generate_injection() - 실패 사례 프롬프트
    │   └── record_rejection() - REJECT 사례 학습
    ├── StateLockedArcGenerator - [V60.14 NEW] 상태 잠금 Arc 생성
    │   ├── generate() - 이전 Arc 상태 계승 Arc 생성
    │   ├── _extract_state() - LLM 기반 arc_end_state 추출
    │   ├── _build_state_locked_prompt() - 상태 잠금 프롬프트 구축
    │   └── Speculative Generation (Flash→Pro 2단계)
    ├── Weaver - Foreshadowing management
    ├── Manager - Production coordination
    ├── Evaluator - Context evaluation (narrative flow)
    ├── Editor - Style polishing (persona-based)
    ├── Critic - [V52.2] 원고 비평
    └── Cleaner - Readability optimization (hanja removal)
```

**Service Injection Pattern:**
`StudioSystem.boot_v20_project(name)` initializes all services. Agents receive orchestrator config via `get_v20_orchestrator_config()` which includes: `project`, `api_client`, `martial`, `world`, `techniques`, `guard`, `karma`, `models`.

**Audit System:**
`SovereignApp` maintains `runtime_audit[]` list. Use `_audit_event(event, details, metadata)` for tracking. Events defined in `constants.py:AuditEvents`.

### Triple Database System

| Database | Location | Purpose |
|----------|----------|---------|
| SQLite | `projects/{name}/project_data.db` | **Primary source of truth** - anchors, manuscripts, blueprints, HUD snapshots |
| ChromaDB | `projects/{name}/chroma_db/` | Vector embeddings for semantic episode recall |
| Files | `projects/{name}/drafts/` | Human-readable manuscript backups |

**Critical:** SQLite DB is authoritative. If `bible.json` and DB diverge, DB wins.

### Genre Architecture

Genre selection happens at runtime in `SovereignApp._select_genre()`. Once selected, `self.selected_genre` is set and guard is dynamically initialized.

Genre-specific behavior injected via:
- **GenreGuard** (`modules/core/genre_guards/`) - Validation rules per genre
  - `WuxiaGuard` - Martial power rules, jianghu logic
  - `HunterGuard` - Gate/dungeon mechanics, awakened abilities
  - `InvestmentGuard` - Financial realism, stock market rules
- **HUD Systems** (`modules/core/genre_hud_manager.py`) - State tracking
  - `MartialHUD` - 무력/내공/경공/검법/장법 metrics
  - `HunterHUD` - 각성등급/마나/스킬 metrics
  - `FinanceHUD` - 자산/주식/인맥 metrics
- **Constants** (`modules/core/constants.py`) - Centralized thresholds and mappings
- **Genre Laws** (`modules/core/laws/{genre}.json`) - Genre-specific rules and seed pools
  - `wuxia.json`, `hunter.json`, `investment.json`
  - Seed pools: `items_pool`, `npc_pool`, `location_pool`, `cliche_pool`, `technique_pool`

## Key Files

| File | Purpose |
|------|---------|
| `main_a.py` | Entry point, `SovereignApp` orchestrator |
| `modules/core/project_manager.py` | `ProjectContext` - all data I/O |
| `modules/core/db_manager.py` | `DBManager` - SQLite operations |
| `modules/core/constants.py` | Global constants, `GenreTypes`, AI parameters |
| `modules/core/narrative_diversity.py` | [V48] `NarrativeDiversityEngine` - 서사 다양성 통합 |
| `modules/core/pattern_tracker.py` | [V48] `PatternTracker` - 패턴 반복 감지 |
| `modules/core/diversity_sampler.py` | [V48] `DiversitySampler` - 앙상블 다양성 선택 |
| `modules/core/relationship_tracker.py` | `RelationshipTracker` - NPC 관계 상태 전환 |
| `modules/core/information_diffusion.py` | `InformationDiffusion` - 정보 전파 시뮬레이션 |
| `modules/core/tension_curve.py` | [V50.1] `TensionCurveManager` - 긴장도 곡선 관리 |
| `modules/core/dialogue_engine.py` | [V50.2] `DialogueQualityEngine` - 대사 DNA 엔진 |
| `modules/core/subplot_weaver.py` | [V50.3] `SubplotWeaver` - 서브플롯 관리 |
| `modules/core/reader_simulator.py` | [V50.4] `ReaderSimulator` - 가상 독자 시뮬레이션 |
| `modules/core/pacing_analyzer.py` | [V51.1] `PacingAnalyzer` - 호흡 분석기 (LLM 비용 0원) |
| `modules/core/quality_amplifier.py` | [V51.2] `QualityAmplifier` - 품질 증폭기 (성공률 향상) |
| `modules/core/agent_intelligence.py` | [V51.3] `AgentIntelligence` - 에이전트 지능 향상 |
| `modules/core/justification_patterns.py` | 정당화 패턴 Few-Shot 라이브러리 |
| `modules/core/self_reflection.py` | [V52.1] `SelfReflectionEngine` - 자기성찰 평가 (3단계 비판) |
| `modules/core/expert_mixture.py` | [V52.3] `ExpertMixture` - 전문가 혼합 (장르별 페르소나) |
| `modules/core/cross_agent_verifier.py` | [V52.4] `CrossAgentVerifier` - 교차 검증 (다중 에이전트) |
| `modules/core/dynamic_prompt_weighting.py` | [V53.1] `DynamicPromptWeighting` - 동적 프롬프트 가중치 |
| `modules/core/tree_of_thoughts.py` | [V53.5] `TreeOfThoughts` - 사고의 나무 (분기 탐색) |
| `modules/core/adversarial_self_play.py` | [V53.6] `AdversarialSelfPlay` - 적대적 자기대결 |
| `modules/core/multi_agent_deliberation.py` | [V53.7] `MultiAgentDeliberation` - 다중 에이전트 숙의 |
| `modules/core/semantic_cache.py` | [V54.1] `SemanticCache` - 의미 기반 캐시 |
| `modules/core/context_compression.py` | [V54.2] `ContextCompressor` - 컨텍스트 압축 |
| `modules/core/failure_learner.py` | [V54.3] `FailureLearner` - 실패 패턴 학습 |
| `modules/core/adaptive_retry.py` | [V54.3] `AdaptiveRetryManager` - 적응형 재시도 |
| `modules/core/two_phase_generator.py` | [V54.4/V55.1] `TwoPhaseGenerator` - 2단계 생성 (Manuscript/Blueprint/Arc) |
| `modules/core/blueprint_memory.py` | [V54.5] `BlueprintMemory` - 블루프린트 패턴 기억 |
| `modules/core/manuscript_enhancer.py` | [V55] `ManuscriptEnhancer` - 원고 품질/길이 향상 |
| `modules/core/constitutional_checker.py` | [V55.2] `ConstitutionalChecker` - 헌법적 자기검증 |
| `modules/domain/agents/base_agent.py` | `BaseAgent` - API calling, JSON healing |
| `modules/domain/agents/writer.py` | `Writer.write_v20_manuscript()` [V60: HUD 급변 감지] |
| `modules/domain/agents/continuity_inspector.py` | [V49.5] Arc + Episode + Manuscript 연속성 + 서사 품질 검증 |
| `modules/domain/agents/arc_ensemble.py` | [V60.11] `ArcEnsembleGenerator` - 3개 Arc 병렬 생성 + 최적 선택 |
| `modules/domain/agents/arc_draft_validator.py` | [V60.11] `ArcDraftValidator` - Python 기반 Arc 사전 검증 (0원) |
| `modules/domain/agents/constraint_compiler.py` | [V60.11] `ConstraintCompiler` - 구조화된 제약 체크리스트 |
| `modules/domain/agents/four_phase_arc_generator.py` | [V60.12] `FourPhaseArcGenerator` - 4단계 Arc 생성 파이프라인 |
| `modules/domain/agents/preflight_checker.py` | [V60.12] `PreflightChecker` - 생성 전 완벽 분석 |
| `modules/domain/agents/arc_critic.py` | [V60.12] `ArcCritic` - Arc 즉시 비평 + 자동 수정 |
| `modules/domain/agents/consensus_validator.py` | [V60.12] `ConsensusValidator` - 3-LLM 합의 검증 |
| `modules/domain/agents/negative_example_injector.py` | [V60.12] `NegativeExampleInjector` - 실패 사례 주입 |
| `modules/domain/agents/state_locked_arc_generator.py` | [V60.14] `StateLockedArcGenerator` - 상태 잠금 Arc 생성 + Speculative Generation |
| `modules/core/narrative_structure_analyzer.py` | [V60.15] `NarrativeStructureAnalyzer` - LLM 기반 서사 구조 분석 (코사인 유사도 대체) |
| `modules/domain/agents/evaluator.py` | `Evaluator` - 맥락 평가 (narrative flow) |
| `modules/domain/agents/editor.py` | `Editor` - 문체 교정 (persona-based) |
| `modules/domain/agents/cleaner.py` | `Cleaner` - 가독성 최적화 (hanja removal) |
| `config/settings.json` | Base model tier assignments |
| `config/prompts/` | Agent instruction manifesto files |
| `docs/글도비_V0128_MANIFESTO.md` | V0128 design spec (3-tier validation) |

## Agent System Patterns

All agents inherit from `BaseAgent` (`modules/domain/agents/base_agent.py`) which provides:

**Core Methods:**
- `ask(prompt, temperature)` - JSON-mode API call with automatic continuation on MAX_TOKENS
  - Injects `author_directives` from project context
  - Escapes braces via `_escape_braces()` to prevent KeyError
  - Overlap-aware merging for multi-chunk responses (100-char overlap detection)
  - Automatic failover to `backup_model` on primary model error
- `_extract_json_robust()` - Self-healing JSON parser with fallback chain

**JSON Parsing Fallback Chain:**
1. `json.loads(strict=False)`
2. `ast.literal_eval()` (handles single quotes)
3. Regex extraction of key fields
4. Return partial data with `"parsing_error": True`

**Continuation Logic:**
When API hits MAX_TOKENS, automatically continues from last 50 chars as anchor point. Critical for preventing "Beat 3" truncation in blueprints.

## Caching System (V31 Quad-Cache)

Four dedicated caches stored in `sys_caches` anchor (24-hour TTL per `constants.py:RetryLimits.CACHE_TTL_SECONDS`):
- `writer_cache` - Writing manifesto + style seeds from `projects/{name}/config/cash/style_seeds_final.txt`
- `architect_cache` - Structural rules
- `analyst_cache` - Strategy libraries
- `weaver_cache` - Foreshadowing rules

Each cache contains prompt manifest + timestamp. Auto-created on first use if missing. Cleared by restart or manual DB deletion.

**Style Seeds:**
Located at `projects/{name}/config/cash/style_seeds_final.txt`. Auto-created with default content during project init. Writer agent loads this for stylistic consistency.

## Naming Conventions

| Term | Meaning |
|------|---------|
| `v20_*` | Version 20 architecture (current stable) |
| `anchor` | DB-persisted JSON data |
| `HUD` | Character/world state (Head-Up Display) |
| `tactical_doc` | Strategic plan for an arc |
| `blueprint` | Scene-by-scene plan for an episode |
| `master_bible` | Root lore document |

## Critical Safety Rules

1. **Never delete ChromaDB files** - Especially `chroma.sqlite3` and `*.wal`. Only delete `LOCK` and `*-shm` if locked. Use `RESET.py` for safe cleanup.
2. **Always commit after DB writes** - Use `_safe_commit()` in sync contexts or `_safe_commit_async()` in async contexts. Never commit directly.
3. **Escape user content in prompts** - Use `_escape_braces()` to prevent KeyError from `{}` characters in f-strings.
4. **Validate episode numbers** - Use `get_latest_episode_number()`, don't assume. DB is source of truth.
5. **Check genre context** - Always verify `self.selected_genre` before genre-specific logic.
6. **Handle JSON truncation** - `BaseAgent.ask()` auto-continues on MAX_TOKENS but verify complete JSON structure.
7. **Windows UTF-8 encoding** - Main app already handles this in `main_a.py` lines 5-11. Don't re-wrap stdout.
8. **Model tier progression** - Don't manually override tier upgrades. Let rejection count drive Tier 1→2→3 progression naturally.
9. **Stage 4 fixed model** - In Stage 4, Writer always uses `gemini-3-pro-preview` regardless of retry count (prevents quality degradation).

## Adding a New Genre

1. Create guard in `modules/core/genre_guards/{genre}_guard.py` (inherit from `BaseGuard`)
2. Add HUD class in `modules/core/genre_hud_manager.py` (define metrics dict)
3. Register in `constants.py:GenreTypes`:
   - Add constant (e.g., `ROMANCE = 'romance'`)
   - Add to `all()` classmethod
   - Add to `get_name()` mapping
4. Create genre laws file `modules/core/laws/{genre}.json`
5. Create seed pools in `modules/core/laws/seeds/{name}_pool_{genre}.json`
6. Update `main_a.py:_select_genre()` menu with new option
7. Test guard initialization in `StudioSystem.boot_v20_project()`

## Modifying Agent Behavior

Agent prompts are loaded from `config/prompts/{agent}_rules.json`:
- `analyst_libraries.json` - Strategic planning libraries
- `architect_rules.json` - Blueprint construction rules
- `weaver_rules.json` - Foreshadowing management
- `writer_rules.json` - Writing manifesto

Edit the JSON manifesto files, not Python code. Cache invalidation:
- Restart application, OR
- Delete specific cache from `sys_caches` anchor in DB, OR
- Use `RESET.py` for full project reset

## Validation System (V49 Update)

**7-Tier Validation Architecture:**

The V49 validation system extends ContinuityInspector to **Arc level (Stage 2)**, catching timeline errors before they propagate to blueprints. This reduces arc-level contradictions from 15% → 2%.

### TIER -1: ARC CONTINUITY Inspector (`modules/domain/agents/continuity_inspector.py`) [V49 NEW]
LLM-based **Arc 수준 전체 타임라인 검증** (Stage 2에서 실행):
- **Model**: `gemini-2.5-pro` (대용량 컨텍스트, 고정밀 추론)
- **범위**: Arc 1부터 현재 직전까지 **전체 Arc 분석** + **단일 Arc 내 모순 탐지**
- **메서드**: `inspect_arc(current_arc, prev_arcs)`

**검증 항목:**
- **Cross-Arc Item Timeline** - 이전 Arc들에서 획득한 아이템 추적, 중복 획득 감지
- **Cross-Arc Grant Timeline** - 수여물/복권의 정확한 수여 시점 추적, 위상 변화 일관성
- **Cross-Arc State Timeline** - 부상/내공 상태의 연속적 누적 검증
- **Intra-Arc Consistency** [V49 핵심] - 단일 Arc 내 화 사이의 모순 탐지
- **Setting Consistency** - 무기/아이템 물리적 특성의 일관성 검증

**Execution Point:** Stage 2에서 Analyst 설계 → **ContinuityInspector.inspect_arc()** → Director 검증

**Three-Phase Validation [V49.2 UPDATE]:**
1. **Python Precheck** (무료) - 정규식 기반 빠른 필터링, 명백한 위반 즉시 REJECT
2. **Joint Docs Auto-Correction** [V49.2 NEW] - tactical_doc 마지막 화에서 정확한 joint_docs 추출
   - Analyst가 tactical_doc과 joint_docs를 동시 생성하면서 발생하는 불일치 문제 해결
   - 마지막 화 내용에서 `final_location`, `physical_inventory`, `world_joint` 정밀 추출
   - 추출된 joint_docs로 원본 자동 교체 → 검증 PASS율 향상
3. **LLM Deep Check** (~$0.02-0.05) - 전체 Arc 타임라인 분석으로 미묘한 모순 탐지

**Severity Levels:**
- CRITICAL: 명백한 타임라인 오류 (중복 획득, 수여 전 소지) → 즉시 REJECT
- MAJOR: 심각한 연속성 오류 (상태 급변, 설정 충돌) → REJECT
- MINOR: 경미한 불일치 (반응 속도, 정보 전파) → WARNING으로 PASS

**Use Case (Arc Level):**
- ARC1 제2화에서 대도 획득 → ARC2 제5화에서 다시 대도 획득하러 가는 모순 방지
- ARC1 제4화에서 복권 선포 → ARC2 제5화에서 여전히 무시당하는 모순 방지
- 단일 Arc 내에서 무기 두께/특성이 화마다 다르게 묘사되는 모순 방지
- [V49.2] joint_docs의 final_location/physical_inventory가 마지막 화 내용과 불일치 → 자동 수정

### TIER 0: EPISODE CONTINUITY Inspector (`modules/domain/agents/continuity_inspector.py`) [V48.1]
LLM-based **전체 에피소드 타임라인 검증** (Director 산하 에이전트):
- **Model**: `gemini-2.5-pro` (대용량 컨텍스트, 고정밀 추론)
- **범위**: 제1화부터 현재 직전까지 **전체 블루프린트** 분석
- **메서드**: `inspect(current_ep, current_blueprint, prev_blueprints)`

**검증 항목:**
- **Item acquisition timeline** - 전체 에피소드에서 획득한 아이템 추적, 중복 획득 감지
- **Grant/Award timeline** - 수여물(철혈사자패 등)의 정확한 수여 시점 추적
- **State continuity** - 캐릭터 상태(부상, 경지) 누적 변화 추적
- **Reaction plausibility** - 관계 변화의 일관성 검증

**Execution Point:** Stage 3에서 Architect 생성 → **ContinuityInspector.inspect()** → Director 검증

**Use Case (Episode Level):** 
- EP2에서 대도 획득 → EP5에서 다시 대도 획득하러 가는 모순 방지
- EP4에서 철혈사자패 수여 → EP2-3에서 이미 소지한 것처럼 묘사하는 모순 방지
- EP10에서 경지 상승 → 이전 에피소드들과의 일관성 검증

### TIER 0.1: MANUSCRIPT CONTINUITY Inspector (`modules/domain/agents/continuity_inspector.py`) [V49.5 UPDATE]
LLM-based **원고 수준 연속성 검증** (Stage 4에서 실행):
- **Model**: `gemini-2.5-pro` (대용량 컨텍스트)
- **범위**: 이전 원고들(최근 5화) + 현재 Blueprint와의 일치성
- **메서드**: `inspect_manuscript(current_ep, manuscript, blueprint, prev_manuscripts)`

**검증 항목:**
- **이전 원고 연속성:**
  - 아이템 소지/사용 일관성 (획득 안 한 아이템 사용 방지)
  - 상태 연속성 (부상/회복/경지 변화의 자연스러운 연결)
  - 관계 연속성 (적대/우호 관계 역행 방지)
- **Blueprint 일치성:**
  - 핵심 씬(Core Scene) 반영 여부
  - Cliffhanger 엔딩 준수 여부
  - 설계된 공간/시간 일치 여부

**Two-Phase Validation:**
1. **Python Precheck** (무료) - 정규식 기반 빠른 필터링, 명백한 위반 즉시 REJECT
2. **LLM Deep Check** (~$0.02) - 미묘한 연속성 모순 탐지

**[V49.5] Python Precheck 확장 (9개 체크, LLM 비용 0원):**
1. 미획득 아이템 사용
2. 부상 상태 연속성
3. Blueprint 핵심 씬 반영
4. **관계 급변 탐지** - 무시→충성 같은 2단계 이상 점프 시 REJECT
5. **악역 지능 보호** - 과소평가 3회 연속 + 경계 묘사 없음 시 WARNING
6. **시간 흐름 검증** - 같은 날 연속 대형 이벤트, 부상 후 즉시 활동 WARNING
7. **공짜 파워업 감지** - 성장 있는데 대가 묘사 없음 WARNING
8. **갑작스러운 능력** - 복선 없이 비급/절기 등장 WARNING
9. **주인공 무쌍 과다** - 승리만 있고 고전 없음 WARNING

**Execution Point:** Stage 4에서 Writer 생성 → **ContinuityInspector.inspect_manuscript()** → Director 검증

**Use Case (Manuscript Level):**
- 직전 화에서 대도를 소지하고 끝났는데 다음 화 시작에 대도가 없는 모순 방지
- Blueprint에서 6개 씬을 설계했는데 원고가 2개 씬만 반영한 경우 REJECT
- 직전 화 끝에서 중상인데 다음 화 시작에 멀쩡하게 활동하는 모순 방지
- **[V49.5]** 사병들이 한 화 만에 "무시"→"충성" 급변 시 REJECT

### TIER 0.5: CONTINUITY Validator (`modules/validation/continuity_validator.py`) [V47]
Python-based **episode-to-episode continuity checks** with **zero LLM cost**:
- **Duplicate item acquisition** - 이미 소유한 아이템을 다시 획득하러 가는 패턴 감지
- **Weapon state reset** - 직전 에피소드 끝에서 들고 있던 무기가 사라지는 문제
- **Injury continuity** - 부상 상태에서 무리한 행동 (경고)
- **Location continuity** - 순간이동 방지 (경고)

**Instant REJECT** on duplicate acquisition or weapon reset. Warnings for injury/location.

**Note:** V49에서 ContinuityInspector가 Stage 2(Arc), Stage 3(Episode) 양쪽에서 정밀한 검증을 수행하므로, 이 Validator는 빠른 Python 보조 역할로 전환됨.

### TIER 1: BLOCKING Validator (`modules/validation/blocking_validator.py`)
Python-based checks with **zero LLM cost**:
- Dead NPC resurrection check
- Unowned item usage check
- Destroyed location visit check
- Minimum length check (4000 chars for MANUSCRIPT, 500 for BLUEPRINT)
- Required scenes check (MANUSCRIPT mode only)
- **[V49 NEW] Scope overflow check** - Writer가 Blueprint 범위를 초과하여 과잉 생성 방지
  - Blueprint의 씬 개수 추출 (`## scene_N` 패턴 카운트)
  - 원고 길이가 (씬 개수 × 1500자)의 1.3배 초과 시 REJECT
  - 예: 6개 씬 Blueprint인데 11700자 초과 시 "Blueprint 범위 초과" REJECT

**Instant REJECT** on any failure. No retry allowed until fixed.

### TIER 2: SCORING Validator (`modules/validation/scoring_validator.py`)
Weighted 100-point system with **70-point PASS threshold**:

**Python Metrics (no LLM):**
- Prose rhythm (CV: 0.3-0.6) - 5pts
- Vocabulary diversity (TTR ≥ 0.3) - 5pts
- Sensory balance (visual ≤ 60%) - 5pts
- Show don't tell (direct emotion < 2/1000chars) - 5pts

**LLM Metrics (via Constitutional AI):**
- Character consistency - 15pts
- Emotion arc - 20pts
- Dialogue quality - 15pts
- Commercial appeal - 20pts
- Pattern diversity - 10pts

**Self-Consistency Mode:**
When enabled, performs 3 evaluations and uses median score + majority vote for PASS/REJECT. Reduces LLM hallucination from 30% → 5%.

**Cost:** $0.01 per manuscript (single) or $0.03 (with Self-Consistency)

### TIER 3: ADVISORY Validator (`modules/validation/advisory_validator.py`)
Non-blocking suggestions that **always PASS**:
- Cliché detection (회귀물, 천재물, 복수물 patterns)
- Expression improvements (LLM-based, optional)
- Foreshadowing opportunities (휴리스틱)

**Cost:** $0.005 per manuscript (flash model)

### Additional Validators

**CatharsisTimer** (`modules/validation/catharsis_timer.py`):
- Manages catharsis (사이다) timing across episodes
- Max consecutive frustration: 3 episodes (default)
- Genre-specific catharsis indicators and weights
- Verdict: "ok" | "warning" | "critical"

**ActionSceneEvaluator** (`modules/validation/action_scene_evaluator.py`):
- Evaluates fight/action scenes (genre-specific)
- Metrics: Choreography (40%), Power Consistency (30%), Stakes Escalation (30%)
- Score: 0-10 points

**RetrospectiveValidator** (`modules/validation/retrospective_validator.py`):
- Long-term consistency checks (past N episodes)
- Detects: power regression, relationship regression, unexplained item loss, resolved conflict recurrence
- Lookback window: 5 episodes (default)

### ValidationOrchestrator (`modules/validation/validation_orchestrator.py`)
Integrates all 5 tiers with configurable Self-Consistency:

**Validation Order:** CONTINUITY → BLOCKING → CONSISTENCY → SCORING → ADVISORY

```python
config = {
    'scoring_model': 'gemini-2.5-pro',
    'advisory_model': 'gemini-2.5-flash',
    'scoring_threshold': 70,
    'use_self_consistency': True,
    'consistency_votes': 3
}

orchestrator = ValidationOrchestrator(config, client, genre='wuxia')
result = orchestrator.validate(ep_num, manuscript, validation_context)
```

**Final Decision Mapping:**
- 85+ score → "PASS"
- 70-84 score → "CONDITIONAL_PASS"
- <70 score → "REJECT"

### Director Integration
Director agent now has dual validation paths:

```python
# Legacy validation (V40)
result = director.audit_manuscript(...)

# V0128 validation (new)
result = director.audit_manuscript_v0128(
    ep_num=1,
    manuscript=manuscript,
    validation_context={
        'encyclopedia': {...},
        'martial_hud': {...},
        'blueprint': {...},
        'mode': 'MANUSCRIPT',  # or 'BLUEPRINT'
        'history': [...],
        'npc_profiles': {...}
    },
    config=config,
    genre='wuxia'
)
```

**Toggle in `config/settings.json`:**
```json
{
  "validation": {
    "use_v0128": true,
    "scoring_threshold": 70,
    "use_self_consistency": true,
    "consistency_votes": 3
  }
}
```

**Quality Constitution:**
Located in `modules/core/quality_constitution.py`. Defines 8 Articles covering all quality dimensions with genre-specific amendments for Wuxia/Hunter/Investment.

**Testing:**
Run `python test_v0128_validation.py` to verify all 3 tiers + orchestrator + Director integration.

**Cost Impact:**
Adds $3.75-$8.75 to total project cost (250 episodes) while reducing quality errors by 80%.

This tiered approach improves pass rates from ~50% (old all-blocking) to 80-85% while maintaining quality standards.

## AI Strategy Enhancements

### Phase 1: COMPLETE ✅

1. **Constitutional AI** - Explicit quality rules (Articles 1-8)
2. **3-Tier Validation** - BLOCKING/SCORING/ADVISORY system
3. **Self-Consistency** - 3-vote majority reduces errors 30% → 5%
4. **JSON Schema** - Structured output enforcement
5. **Chain-of-Thought** - Step-by-step reasoning in prompts

### Phase 2: COMPLETE ✅

1. **Model Cascading** - Already implemented in V40 (77% cost reduction on blueprints)
2. **Batch Validation** - Parallel processing with asyncio (3x speed increase)
3. **A/B Testing** - Compare Legacy vs V0128 systems with statistical analysis
4. **JSON Schema Enforcement** - 8 structured schemas (0% parsing errors)
5. **Data Collection** - Automatic dataset gathering for fine-tuning/RLHF

**Files Created:**
- `modules/validation/batch_validator.py` - Batch processing
- `modules/core/ab_testing.py` - A/B testing framework
- `modules/core/response_schemas.py` - JSON schemas
- `modules/core/data_collector.py` - Training data collection
- `modules/core/model_cascading.py` - Cascade utilities

**Total Cost:** $0 (all optimizations, no added expenses)

See `PHASE2_COMPLETE.md` for detailed documentation.

### Phase 3: COMPLETE ✅

1. **Fine-tuning Automation** - Complete pipeline (check → prepare → validate → train)
2. **RLHF Interface** - Human feedback collection with AI comparison
3. **Performance Dashboard** - Real-time Streamlit monitoring with charts
4. **Prompt Optimizer** - Meta-learning based automatic improvement

**Files Created:**
- `performance_dashboard.py` - Streamlit real-time dashboard
- `rlhf_interface.py` - Human feedback UI
- `modules/core/prompt_optimizer.py` - Automatic prompt improvement
- `modules/core/finetuning_automation.py` - Gemini fine-tuning pipeline
- `test_phase3_systems.py` - Integration tests (4/4 passed)
- `PHASE3_QUICKSTART.md` - Quick start guide

**Total Cost:** $0 (infrastructure only, fine-tuning optional ~$100)

See `PHASE3_COMPLETE.md` and `AI_STRATEGY_COMPLETE.md` for full documentation.

### Code Review & Stabilization: COMPLETE ✅

**Date**: 2026-01-28
**Scope**: Full Phase 1-3 code audit and bug fixes

**Issues Fixed**:
- **Critical**: 7/8 bugs fixed (7 actual bugs + 1 confirmed safe)
- **High Priority**: 3/12 key issues fixed (context-aware matching, TTR sampling, AB statistics)
- **Test Coverage**: 100% (13/13 tests passed)

**Key Improvements**:
- HUD equipment type safety (list/str/dict handling)
- LLM fallback with clear warnings + heuristics
- Constitution load error handling
- Event loop stability (Jupyter/Streamlit compatible)
- File versioning (no data loss on re-validation)
- Context-aware keyword matching (negation detection)
- Fair TTR calculation (sampling for long texts)
- Statistical significance testing (Welch's t-test)

**Production Readiness**: ✅ **95% Ready** (Updated after 2nd inspection)
- Code Safety: 65% → 98% (+51%)
- Crash Risk: High → Very Low (-90%)
- Data Integrity: 100% (Thread-safe + Atomic write)
- All critical bugs resolved (9/10)
- **APPROVED FOR PRODUCTION**

**2차 심층 검사** (2026-01-28):
- 8개 추가 이슈 발견 (3 Critical/High, 5 Medium/Low)
- 3개 Critical/High 즉시 수정:
  - Equipment 타입 안전성 강화 (BLOCKING 우회 방지)
  - Race condition 해결 (Thread-safe 파일 저장)
  - Event loop 안정성 (모든 async 환경 호환)
- 실행 흐름 시뮬레이션 + 동시성 테스트 통과

**Files Modified**: 11 files total, ~330 lines changed
- 1차 검사: 8 files, ~250 lines
- 2차 검사: 3 files, ~80 lines

See `DEEP_INSPECTION_COMPLETE.md` for 2nd round results, `CODE_REVIEW_COMPLETE.md` for 1st round, and `CRITICAL_FIXES_COMPLETE.md` for detailed fixes.

### Chain-of-Thought Implementation

CoT is integrated into 3 key evaluation points:

**SCORING Validator** (`modules/validation/scoring_validator.py`):
- 5-step evaluation process (Articles 2-7)
- Each step analyzes specific quality dimension
- Result: +15% accuracy

**Director Manuscript Audit** (`modules/domain/agents/director.py`):
- 5-step review process (setting → scenes → flow → quality → decision)
- Systematic PASS/REJECT with clear reasoning
- Result: +25% consistency

**Director Strategic Audit** (`modules/domain/agents/director.py`):
- 4-step arc validation (future contamination → uniqueness → pacing → density)
- Prevents loops and future item leaks
- Result: +35% REJECT reason clarity

**Cost:** $0 (prompt-only, minimal token increase)

See `COT_UPGRADE_COMPLETE.md` for details.

### V48 Premium: Narrative Diversity Engine

Addresses "narrative inertia" - tendency for LLMs to repeat plot patterns across episodes.

**Core Components:**

1. **PatternTracker** (`modules/core/pattern_tracker.py`)
   - Detects recurring patterns across episodes
   - Tracks: clichés, sentence starters, plot sequences, scene types, reaction patterns
   - `should_activate_diversity_sampling()` returns True when patterns exceed threshold
   - `generate_writer_injection()` creates warning prompts for Writer

2. **DiversitySampler** (`modules/core/diversity_sampler.py`)
   - Ensemble technique: generates N candidates, selects most diverse
   - `sample_and_select()` for manuscripts
   - `sample_blueprints()` for blueprints
   - Diversity score = TTR + sentence variety + freshness + structural diversity

3. **NarrativeDiversityEngine** (`modules/core/narrative_diversity.py`)
   - Integrates PatternTracker + DiversitySampler + Contrastive CoT
   - `analyze_recent_episodes()` analyzes last N episodes
   - `generate_diverse_blueprint()` for Stage 3
   - `generate_diverse_manuscript()` for Stage 4 (conditional on pattern flags)
   - `get_writer_injection()` / `get_architect_injection()` for prompt injection

4. **Contrastive CoT**
   - Negative example-based prompting
   - Genre-specific anti-patterns (wuxia/hunter/investment)
   - "Instead of X, try Y" style guidance

**Activation Points:**
- Stage 3 (Architect): Always active - samples 3 blueprints, picks most diverse
- Stage 4 (Writer): Conditional - activates when PatternTracker detects repetition

**RelationshipTracker** (`modules/core/relationship_tracker.py`):
- Finite state machine for NPC-protagonist relationships
- States: 적대, 무시, 의심, 중립, 경외, 충성, 굴복, 배신, 사망, 추방, 희생
- `validate_transition()` checks if state changes are valid
- `infer_state_from_manuscript()` extracts relationship from text

**InformationDiffusion** (`modules/core/information_diffusion.py`):
- Simulates rumor/information spread across NPCs
- `should_npc_know(npc, event)` checks if NPC should know about an event
- Propagation speed: same location (instant), same faction (1 ep), adjacent region (2 ep), far region (5 ep)

**JustificationPatterns** (`modules/core/justification_patterns.py`):
- Few-shot learning library for unlikely actions
- Pattern types: `weak_body_strong_action`, `low_status_high_authority`, `sudden_power_increase`
- `get_justification_guide()` generates genre-specific guidance

### V50: Narrative Quality Enhancement Suite

V50 introduces four interconnected modules for comprehensive narrative quality management.

**1. TensionCurveManager** (`modules/core/tension_curve.py`) - [V50.1]
Episode-by-episode tension level tracking and arc curve analysis:
- `TensionLevel` enum: CALM(1), LOW(3), MEDIUM(5), HIGH(7), PEAK(9), CLIMAX(10)
- `record_tension(episode, level, description)` - Record tension for an episode
- `validate_arc_curve(arc_num)` - Analyze tension curve shape for an arc
- `suggest_next_tension(episode)` - Recommend optimal tension level
- `generate_tension_prompt()` - Create Writer injection prompt
- Detects: flat curves, missing peaks, sudden drops

**2. DialogueQualityEngine** (`modules/core/dialogue_engine.py`) - [V50.2]
Character speech pattern extraction and validation:
- `DialogueDNA` dataclass: speech patterns, formality, vocabulary, catchphrases
- `learn_character(name, manuscript)` - Extract dialogue DNA from text
- `validate_dialogue(name, dialogue)` - Check dialogue consistency
- `compare_characters(name1, name2)` - Ensure character distinction
- `generate_dialogue_prompt(character)` - Create Writer guidance
- Genre-specific speech markers (wuxia/hunter/investment)

**3. SubplotWeaver** (`modules/core/subplot_weaver.py`) - [V50.3]
Multi-storyline tracking with neglect detection:
- `SubplotType` enum: ROMANCE, REVENGE, MYSTERY, GROWTH, RIVALRY, FAMILY, SECRET
- `SubplotStatus` enum: DORMANT, ACTIVE, CLIMAX, RESOLVED, ABANDONED
- `register_subplot(name, type, description)` - Create new subplot
- `update_subplot(name, episode, event)` - Record subplot progress
- `get_neglected_subplots(threshold)` - Find subplots needing attention
- `suggest_subplot_beat(name)` - Recommend next plot beat
- Prevents subplot abandonment (threshold: 3 episodes default)

**4. ReaderSimulator** (`modules/core/reader_simulator.py`) - [V50.4]
Virtual reader perspective feedback:
- `ReaderType` enum: CASUAL, HARDCORE, CRITIC, FIRST_TIME
- `ReaderMood` enum: BORED, NEUTRAL, INTERESTED, EXCITED, FRUSTRATED
- `simulate_reading(manuscript)` - Single reader simulation
- `simulate_all_readers(manuscript)` - All reader types
- `calculate_engagement_score()` - 0-100 engagement metric
- `analyze_episode_series(manuscripts)` - Series-level analysis
- Detects: pacing issues, exposition dumps, hook weakness, cliffhanger strength

**Integration Points:**
- **Stage 4 Pre-Writing**: `_generate_v50_writer_prompt()` injects tension/dialogue/subplot guidance
- **Stage 4 Post-Writing**: `_process_v50_post_episode()` records data and generates feedback
- **Project Init**: `_load_v50_history()` loads existing episode data into modules

**Activation:**
V50 modules are automatically initialized when available. Set `V50_MODULES_AVAILABLE = False` to disable.

### V51: Zero-Cost Analysis Suite

V51 adds analysis modules that require **zero LLM API calls**.

**1. PacingAnalyzer** (`modules/core/pacing_analyzer.py`) - [V51.1]
Pure Python text analysis for manuscript pacing:
- `analyze(manuscript)` - Full pacing analysis
- `generate_pacing_prompt()` - Writer guidance based on issues
- `compare_episodes(analyses)` - Multi-episode comparison

**Metrics Analyzed (no API cost):**
- Sentence length distribution (avg, std)
- Dialogue:narration ratio
- Short sentence ratio (<20 chars)
- Long sentence ratio (>80 chars)
- Scene break frequency
- Pacing zone classification (RAPID/FLOWING/DENSE/DIALOGUE/MIXED)

**Ideal Ranges:**
- Dialogue ratio: 25-45%
- Average sentence: 25-50 characters
- Short sentences: 15-35%
- Long sentences: 5-20%

**Issues Detected:**
- Monotonous sentence lengths (low variety)
- Excessive dialogue or narration
- Too many rapid/dense zones in sequence
- Missing scene breaks in long manuscripts

**Cost:** $0 per manuscript (pure regex + statistics)

**2. QualityAmplifier** (`modules/core/quality_amplifier.py`) - [V51.2]
Pre-generation constraint injection to improve pass rates:
- `generate_writer_constraints()` - Writer용 제약 조건 생성
- `generate_architect_constraints()` - Architect용 제약 조건 생성
- `generate_analyst_constraints()` - Analyst용 제약 조건 생성
- `extract_items_from_manuscript()` - 소지 아이템 추출
- `record_failure()` - 실패 패턴 학습

**Stage별 주요 제약:**
- Stage 2: 아이템 중복 획득 금지, 수여물 타임라인, 상태 연속성
- Stage 3: 씬 개수 4-6개 제한, 클리프행어 필수, 연속성
- Stage 4: 관계 1단계 변화, Blueprint 반영, 아이템 연속성

**성공률 향상 원리:**
1. 과거 REJECT 패턴 분석
2. 생성 전 명시적 제약 주입
3. 자가 검증 체크리스트 제공

**Cost:** $0 (프롬프트 강화만)

**3. AgentIntelligence** (`modules/core/agent_intelligence.py`) - [V51.3]
에이전트 지능 향상 통합 모듈 (3가지 기법):

**Few-Shot Exemplar Library:**
- 우수한 출력 예시를 프롬프트에 주입
- 장르별 맞춤 예시 (wuxia/hunter/investment)
- Analyst: Arc 설계 예시 (복수극, 성장극)
- Architect: Blueprint 예시 (대결, 훈련)
- Writer: 문장/문단 예시 (전투, 감정, 대화)

**Anti-Pattern Injection:**
- "하지 말아야 할 것" 명시적 주입
- 흔한 실수 패턴 회피 유도
- 예: "매우/정말 남발", "감정 직접 명명", "대화 태그 반복"

**Self-Critique Chain:**
- 제출 전 자가 검토 템플릿
- 점수 기반 품질 게이트
- 개선 포인트 자동 도출

**Methods:**
- `get_analyst_enhancement()` - Analyst용 통합 프롬프트
- `get_architect_enhancement()` - Architect용 통합 프롬프트
- `get_writer_enhancement()` - Writer용 통합 프롬프트
- `quick_quality_check()` - LLM 없이 빠른 품질 체크

**예상 효과:**
- 품질: +20-30%
- 반복 패턴: -50%
- 검수 통과율: +15%

**Cost:** Few-Shot/Anti-Pattern = $0, Self-Critique = ~$0.01/회

### V52: Self-Improvement Suite

V52 adds self-improvement and cross-verification capabilities.

**1. SelfReflector** (`modules/core/self_reflection.py`) - [V52.1]
생성 후 자기 성찰 및 자동 개선:
- `reflect_and_improve()`: 출력물 분석 후 개선
- 대상: Blueprint(integrated_scenario), Manuscript
- 개선점 자동 적용 후 반환

**2. AdaptiveRetry (Base)** (`modules/core/adaptive_retry.py`) - [V52.2]
에러 타입별 맞춤 재시도 전략:
- CONSTRAINT_VIOLATION: 제약 블록 강화
- QUALITY_ISSUE: 온도 상향, 예시 추가
- STRUCTURE_ERROR: 온도 하향, 스키마 강제
- `get_retry_strategy()`: 에러 타입별 전략 반환

**3. ExpertMixture** (`modules/core/expert_mixture.py`) - [V52.3]
씬 유형별 전문가 프롬프트 분기:
- 8개 씬 유형: ACTION, DIALOGUE, EMOTIONAL, EXPOSITION, CLIMAX, TRANSITION, MYSTERY, COMEDY
- `analyze_blueprint()`: Blueprint에서 씬 유형 자동 감지
- `generate_writer_injection()`: 씬별 전문화 프롬프트 생성

**4. CrossAgentVerifier** (`modules/core/cross_agent_verifier.py`) - [V52.4]
에이전트 간 교차 검증:
- Architect → Arc 설계 준수 검증
- Writer → Blueprint 준수 검증
- `verify_architect_compliance()`, `verify_writer_compliance()`

### V53: Advanced AI Techniques

V53 adds advanced AI techniques for quality enhancement.

**1. DynamicPromptWeighter** (`modules/core/dynamic_prompt_weighting.py`) - [V53.1]
실패 패턴 기반 프롬프트 가중치 동적 조정:
- FailureLearner와 연동
- 고빈도 실패 영역에 가중치 증가
- `get_weighted_prompt()`: 에이전트/스테이지별 가중치 프롬프트

**2. TreeOfThoughts** (`modules/core/tree_of_thoughts.py`) - [V53.5]
분기 탐색 기반 최적 경로 선택:
- N개 분기 생성 → 평가 → 최선 선택
- Blueprint/Arc 설계에 적용
- `explore_blueprint()`: 3회 이상 실패 시 필살기로 발동

**3. AdversarialSelfPlay** (`modules/core/adversarial_self_play.py`) - [V53.6]
적대적 자기 대결 품질 향상:
- Critic이 공격적 검토
- Writer가 방어적 개선
- 품질 수렴까지 반복

**4. MultiAgentDeliberation** (`modules/core/multi_agent_deliberation.py`) - [V53.7]
다중 에이전트 토론:
- Analyst(전략) + Architect(구조) + Writer(문학) 3자 토론
- 합의된 최종안 도출
- `deliberate()`: 복잡한 의사결정에 활용

**5. NarrativeDiversityEngine** (`modules/core/narrative_diversity.py`) - [V48→V53]
서사 다양성 통합 엔진:
- PatternTracker + DiversitySampler + Contrastive CoT
- Stage 3: 항상 활성화 (Blueprint 다양성)
- Stage 4: 패턴 반복 감지 시 활성화

### V54: Cost Optimization & Enhancement

V54 adds cost reduction and quality enhancement modules.

**1. SemanticCache** (`modules/core/semantic_cache.py`) - [V54.1]
의미론적 유사성 기반 캐싱:
- Jaccard 유사도로 유사 요청 탐지
- 캐시 히트 시 LLM 호출 절감
- `get()`, `set()`: Blueprint 구조 캐싱

**2. ContextCompressor** (`modules/core/context_compression.py`) - [V54.2]
컨텍스트 토큰 압축:
- 목표 압축률 60%
- 필수 필드 보존, 불필요 필드 제거
- `compress()`: 토큰 30-40% 절감

**3. AdaptiveRetryManager** (`modules/core/adaptive_retry.py`) - [V54.3]
V52.2 확장 + FailureLearner 연동:
- 에이전트별 실패 통계 추적
- 필살기 발동 권장 (ToT/ASP/MAD)
- `connect_failure_learner()`: FailureLearner 연동
- `get_injection_prompt()`: 학습된 제약 자동 주입

**4. TwoPhaseGenerator** (`modules/core/two_phase_generator.py`) - [V54.4]
2단계 생성 시스템:
- **Arc**: Skeleton(구조) → Flesh(상세)
- **Blueprint**: Skeleton(씬구조) → Flesh(시나리오) [V54.4.1]
- **Manuscript**: Structure(구조) → Content(본문)
- Phase 1 검증 후 Phase 2 진행 → 재시도율 감소

**5. SuccessPatternMemory** (`modules/core/blueprint_memory.py`) - [V54.5]
성공 패턴 학습 및 가이드:
- Director PASS 패턴 자동 수집
- 유사 컨텍스트에서 성공 패턴 주입
- `record_success()`, `get_guidance_from_patterns()`

### V55: Manuscript Quality & Length Enhancement

V55 adds 7 submodules for manuscript quality and length improvement.

**ManuscriptEnhancer** (`modules/core/manuscript_enhancer.py`) - [V55]
원고 품질 및 분량 통합 향상기:

**1. ClicheBreaker** - [V55.1]
- 클리셰 표현 탐지 + 대안 제시
- 무협/헌터 장르별 클리셰 DB
- 예: "눈이 번쩍" → "의식이 칼날처럼 날카로워졌다"

**2. ForeshadowBalancer** - [V55.2]
- 복선 심기/회수 타이밍 최적화
- 소복선 3화, 중복선 10화, 대복선 Arc 내 회수 권장
- 미회수 복선 경고

**3. SubtextExpander** - [V55.3]
- 직접 서술(Telling) → 묘사(Showing) 변환 권장
- 목표: 직접 감정 서술 비율 30% 미만
- 효과: 분량 +20~30%

**4. PageTurnerScorer** - [V55.4]
- 문단별 "다음 읽고 싶은 정도" 측정
- 훅 패턴 탐지 (질문, 반전, 긴장)
- 목표: 평균 60점 이상

**5. LengthQualityGate** - [V55.5]
- 씬별 최소 분량 체크 (액션 800자, 대화 600자 등)
- 이탈 위험 지점 탐지 (연속 서술, 대화 부족)

**6. SceneDensityEnforcer** - [V55.6]
- 씬 필수 요소 체크 (공간묘사, 감각묘사, 대화비트)
- 미충족 시 구체적 피드백

**7. DialogueBeatInjector** - [V55.7]
- 연속 대화에 액션/리액션 비트 삽입 권장
- 장소 전환 시 환경 앵커 체크

**통합 사용:**
```python
enhancer = ManuscriptEnhancer(genre='wuxia')
result = enhancer.analyze(manuscript, current_ep=10)
print(result.total_feedback)
print(result.priority_fixes)  # ['클리셰 표현 대체', 'Show don't Tell 적용', ...]
```

**예상 효과:**
- 분량: +40~60% 증가
- 품질: 클리셰↓, 묘사↑, 몰입도↑
- 비용: ~$0.04/화 (분석만 시 $0)

### V55.1: Stage 2 향상 모듈 통합

Stage 2 (Arc Tactical Design) 성공률 향상을 위한 3단계 향상 시스템.

**재시도 분기 로직:**
| Attempt | 전략 | 모듈 | 비용 |
|---------|------|------|------|
| 0 (첫 시도) | 일반 Analyst + 자기 비판 | SelfReflector | ~$0.02 |
| 1 (2번째) | 2단계 생성 | TwoPhaseArcGenerator | ~$0.04 |
| ≥2 (3번째+) | ToT 필살기 | TreeOfThoughts.explore_arc | ~$0.08 |

**1. SelfReflector for Analyst** (attempt == 0)
- Analyst가 Arc 생성 후 자기 비판 수행
- 품질 < 6 또는 심각도 high/medium 시 자동 개선
- `ReflectionTarget.ANALYST` 사용

**2. TwoPhaseArcGenerator** (attempt == 1) - [V55.1 NEW]
- Phase 1: Skeleton (구조적 뼈대) - 온도 0.3
  - 회차별 핵심 사건, 아이템/수여물 타임라인
- Phase 2: Flesh (상세 내용) - 온도 0.5
  - tactical_doc, joint_docs, state_constraints

**3. TreeOfThoughts.explore_arc** (attempt >= 2) - 필살기
- 3가지 접근 방식으로 병렬 생성:
  - 인과율 중심: 연속성, 이전 Arc 계승 철저
  - 긴장감 중심: 몰입도, 긴장-이완 곡선 최적화
  - 캐릭터 중심: 감정선, 관계 변화/성장 집중
- 휴리스틱 평가 후 최고 점수 Arc 선택

**기존 Stage 2 검증 레이어 (유지):**
- V49.4 ConstraintDB Pre-Validation
- V49 ContinuityInspector.inspect_arc()
- V51.3 AgentIntelligence
- V51.4 FailureLearner
- Flow Guard, Duplicate Guard

### V55.2: Constitutional Self-Check + ToT 4분기

품질 기반 첫 시도 통과율 향상을 위한 시스템.

**1. Constitutional Self-Check** (`modules/core/constitutional_checker.py`)
- LLM이 출력 전에 자가 검증하도록 프롬프트 주입
- Stage별 REJECT 기준 명시 + REJECT 사례 포함
- 비용: $0 (프롬프트 주입만)

**Stage별 헌법 조항:**
| Stage | 조항 수 | 핵심 체크 |
|-------|---------|----------|
| 2 (Arc) | 6개 | 아이템 중복, 수여물 중복, joint_docs 계승 |
| 3 (Blueprint) | 5개 | cliffhanger 계승, 씬 개수, ending_hook |
| 4 (Manuscript) | 7개 | 미획득 아이템, 관계 급변, Show Don't Tell |

**2. ToT 4분기 확장**
- 기존 3분기 → 4분기로 확장
- Stage 2: +복선/회수 중심 접근
- Stage 3: +연속성 중심 접근

**3. REJECT 사례 강화 (Contrastive Few-Shot)**
```
❌ 나쁜 예: "철혈사자패를 획득했다" (이미 Arc 2에서 획득)
✅ 좋은 예: "품 안의 철혈사자패를 내보였다" (기존 수여물 활용)
```

**예상 효과:**
| Stage | 이전 첫 시도 | V55.2 적용 후 |
|-------|-------------|--------------|
| 2 | 55% | **70%** |
| 3 | 50% | **65%** |
| 4 | 40% | **55%** |

### V60: Quality Pipeline Enhancement

V60 adds 8 quality improvements across Stage 2-4 with zero LLM cost overhead.

**1. Arc State Succession Verification** (`modules/domain/agents/analyst.py`) - [V60.1]
Stage 2 Arc 생성 시 이전 Arc의 종료 상태가 현재 Arc의 시작 상태로 정확히 계승되었는지 검증:
- **Location**: 마지막 위치 계승 확인
- **Inventory**: 소지품 목록 동기화
- **Internal Energy**: 내공 수치 연속성
- **Injury States**: 부상 상태 계승

```python
def _validate_arc_state_continuity_v60(self, current_arc: dict, prev_arc: dict) -> dict:
    # Returns: {'valid': bool, 'issues': [...]}
```

**2. Tactical Doc Continuity Validation** (`modules/domain/agents/analyst.py`) - [V60.2]
Arc 내 화 간 연속성 검증 - 아이템/부상 상태 추적:
- 제N화에서 획득한 아이템이 제N+1화에서 잊혀지는 문제 방지
- 제N화 종료 부상 상태가 제N+1화 시작에서 무시되는 문제 방지
- tactical_doc 파싱하여 화별 상태 변화 추출

```python
def _validate_tactical_doc_continuity_v60(self, tactical_doc: str, ep_count: int) -> dict:
    # Returns: {'valid': bool, 'issues': [...]}
```

**3. Joint Docs Auto-Correction** (`modules/domain/agents/analyst.py`) - [V60.3]
마지막 화 내용에서 joint_docs 자동 추출하여 보정:
- Analyst가 tactical_doc과 joint_docs를 동시 생성하면서 발생하는 불일치 문제 해결
- `final_location`: 마지막 화 종료 시 위치
- `physical_inventory`: 소지품 목록
- `world_joint`: 상태 변화 요약

```python
def _auto_correct_joint_docs_v60(self, tactical_doc: str, arc_data: dict) -> dict:
    # Returns: {'corrected': bool, 'joint_docs': {...}}
```

**4. Stage 4 Retry Limit with Force Pass** (`main_a.py`) - [V60.4]
무한 재시도 방지 및 최후 수단:
- 최대 재시도 횟수 후 마지막 생성 원고 강제 사용
- 경고와 함께 진행 (완전 실패 방지)
- `_v60_last_manuscript`: 마지막 시도 원고 저장
- `_v60_force_passed`: 강제 통과 여부 플래그

**5. Blueprint Completeness Verification** (`modules/domain/agents/director.py`) - [V60.5]
원고가 Blueprint 설계 씬을 충분히 반영했는지 검증:
- 최소 70% 씬 반영 필요
- 미반영 씬 목록 제공
- 키워드 매칭 기반 씬 반영 감지

```python
def _validate_blueprint_completeness_v60(self, manuscript: str, blueprint: dict) -> dict:
    # Returns: {'valid': bool, 'scene_coverage': float, 'missing_scenes': [...]}
```

**6. Enhanced Item Acquisition Extraction** (`modules/domain/agents/architect.py`) - [V60.6]
False positive 필터링 강화:
- "획득하러 간다", "찾으러 간다" 같은 예정 표현 제외
- 실제 획득 완료 표현만 추출: "획득했다", "손에 넣었다", "얻었다"
- Blueprint 컨텍스트 윈도우 5화 → 10화로 확장

**7. Scene Structure Validation** (`modules/domain/agents/architect.py`) - [V60.7]
최소 씬 개수 및 자동 생성:
- 최소 씬 개수: 4개 → 6개로 상향
- 부족 시 자동 생성: `_auto_generate_missing_scenes_v60()`
- 씬 타입 로테이션: Buffer → Core → Buffer → Core → Buffer → Cliffhanger

```python
def _auto_generate_missing_scenes_v60(self, blueprint: dict, target_count: int = 6) -> dict:
    # Auto-generates missing scenes with placeholder content
```

**8. HUD Sudden Change Detection** (`modules/domain/agents/writer.py`) - [V60.8]
내공/경지/부상 상태의 급격한 변화 탐지:
- **내공 급상승**: 단일 화 +500 이상 → 비정상 경고
- **경지 급상승**: 2단계 이상 동시 상승 → 필수 정당화
- **부상 급회복**: 중상/빈사 → 정상 → 치료 과정 필요
- **연속 급성장**: 3화 동안 +1000 이상 → 인플레이션 경고

```python
def _check_hud_anomalies_v60(self, current_ep: int) -> dict:
    # Returns: {'has_anomalies': bool, 'anomalies': [...]}
```

**9. Asyncio Compatibility** (`modules/validation/validation_orchestrator.py`) - [V60.9]
Python 3.10+ 호환성 강화:
- `asyncio.get_event_loop()` → `asyncio.get_running_loop()` 변경
- nest_asyncio 미설치 시 순차 검증으로 fallback
- 모듈 가용성 플래그 추가: `RETROSPECTIVE_AVAILABLE`, `REFLEXION_AVAILABLE`, `CONSTITUTION_AVAILABLE`

### V60.1: Integration & Dashboard Enhancement

**10. V0128 Config Fallback** (`main_a.py`) - [V60.1.1]
- 프로젝트 config 없으면 루트 config로 fallback
- `config/settings.json`의 `validation.use_v0128: true` 자동 적용
- 6-tier 검증 시스템 자동 활성화

**11. HUD Anomaly Audit Logging** (`main_a.py` + `writer.py`) - [V60.1.2]
- Writer가 HUD 급변 감지 결과를 `last_hud_anomalies`에 저장
- main_a.py에서 audit 이벤트로 기록: `hud_anomaly_detected`
- 대시보드에서 HUD 이상 패턴 추적 가능

**12. Blueprint Completeness Pre-LLM Filter** (`main_a.py`) - [V60.1.3]
- ContinuityInspector 호출 전에 Python 사전 검증
- 70% 미만 씬 커버리지 시 즉시 REJECT (LLM 비용 절감)
- `_validate_blueprint_completeness_v60()` 통합

**13. Quality Dashboard** (`modules/core/quality_dashboard.py`) - [V60.1.4]
품질 메트릭 추적 및 분석:
- Stage별 PASS/REJECT 비율 추적
- HUD 급변 이력 관리
- Blueprint 커버리지 추이
- 실패 패턴 분석
- Streamlit 대시보드 데이터 제공

```python
dashboard = QualityDashboard(project_path)
dashboard.record_validation(ep_num, result, stage)
summary = dashboard.get_summary()
dashboard.print_console_summary()
```

**적용 지점:**
| Stage | V60 기능 | 비용 |
|-------|---------|------|
| 2 | 상태 계승 검증, 화간 연속성, Joint Docs 자동보정 | $0 |
| 3 | 씬 구조 검증, 아이템 추출 강화 | $0 |
| 4 | Blueprint 완전성, HUD 급변 감지, 강제 통과 | $0 |

**예상 효과:**
- Stage 2 PASS율: +15%
- Stage 3 PASS율: +10%
- Stage 4 PASS율: +20%
- 무한 루프 방지: 100%

### V60.10: StateExtractor Integration

Stage 2 Arc 생성 시 이전 Arc 상태를 구조화된 JSON으로 추출.

**StateExtractor** (`modules/domain/agents/state_extractor.py`):
- `extract_state(arc)` - 단일 Arc 상태 추출
- `extract_cumulative_state(arcs)` - 여러 Arc 누적 상태
- `generate_constraint_prompt()` - Analyst용 제약 프롬프트

**추출 필드:**
- `protagonist_state`: location, injuries, internal_energy
- `inventory`: current_items, recently_acquired
- `relationships`: NPC별 현재 상태
- `grants_received`: 수여물 목록
- `next_arc_constraints`: must_start_with, must_not_do

**비용:** ~$0.01/Arc (flash 모델 사용)

### V60.11: Ensemble Generation + Pre-Validation

Stage 2 PASS율 향상을 위한 3x 비용 투자 시스템.

**ArcEnsembleGenerator** (`modules/domain/agents/arc_ensemble.py`):
3개 Arc 후보를 서로 다른 전략으로 병렬 생성 후 최적 선택.

```python
GENERATION_STRATEGIES = [
    {"name": "conservative", "temperature": 0.3, "focus": "안정성과 연속성 우선"},
    {"name": "balanced", "temperature": 0.5, "focus": "연속성과 새로움의 균형"},
    {"name": "creative", "temperature": 0.7, "focus": "서사적 흥미 우선"}
]
```

**평가 기준 (100점 만점):**
| 항목 | 배점 | 내용 |
|------|------|------|
| 필수 필드 완성도 | 20점 | arc_no, ep_count, tactical_doc 등 |
| 제약 조건 준수 | 30점 | 금지 아이템 획득 시 -15점/개 |
| 연속성 | 25점 | 시작 위치/소지품 불일치 시 감점 |
| tactical_doc 품질 | 25점 | 분량 2000자 미만 시 -15점 |

**ArcDraftValidator** (`modules/domain/agents/arc_draft_validator.py`):
ContinuityInspector 호출 전 Python 기반 사전 검증 (LLM 비용 0원).

**검증 항목:**
1. **필수 필드 검사** - arc_no, ep_count, tactical_doc, joint_docs 등
2. **중복 아이템 획득** - items_acquired가 이전 Arc에서 이미 획득한 것과 중복
3. **위치 연속성** - arc_start_state.location ≠ 이전 Arc joint_docs.final_location
4. **부상 상태 계승** - 이전 Arc 부상 상태가 현재 Arc에서 무시됨
5. **수여물 타임라인** - grants_received가 이미 수여받은 것과 중복
6. **tactical_doc 분량** - 최소 2000자 (REJECT) / 3000자 (WARNING)

**ConstraintCompiler** (`modules/domain/agents/constraint_compiler.py`):
이전 Arc들에서 제약 조건을 추출하여 구조화된 체크리스트 생성.

**출력 형식:**
```
╔══════════════════════════════════════════════════════════════════════╗
║       [V60.11 CONSTRAINT CHECKLIST - 다음 Arc 설계 시 필수 준수]      ║
╚══════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────┐
│ 🚫 MUST NOT DO (절대 금지 - 위반 시 즉시 REJECT)                      │
├──────────────────────────────────────────────────────────────────────┤
│ [아이템 획득 금지 - 이미 보유 중]                                      │
│   ❌ 대도 (Arc 1에서 획득)                                           │
│   ❌ 철혈사자패 (Arc 2에서 획득)                                      │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ 📋 INHERITED STATE (반드시 계승할 상태 - Arc 시작점)                   │
├──────────────────────────────────────────────────────────────────────┤
│ 🗺️ 시작 위치: 철혈단 본거지                                          │
│ 📦 소지품: 대도, 철혈사자패, 금창약                                   │
│ 💔 부상 상태: 왼팔 경상                                               │
│ ⚡ 내공: 85%                                                         │
└──────────────────────────────────────────────────────────────────────┘
```

**통합 실행 흐름:**
```
1. ConstraintCompiler.compile() → 구조화된 제약 블록 생성
2. attempt == 0: ArcEnsembleGenerator.generate_ensemble() → 3 후보 중 최적 선택
3. ArcDraftValidator.validate() → Python 사전 검증 (무료)
4. ContinuityInspector.inspect_arc() → LLM 심층 검증 (유료)
```

**예상 효과:**
- Stage 2 첫 시도 PASS율: 55% → 75%
- Stage 2 최종 PASS율: 85% → 95%
- 비용: ~3x 증가 (Ensemble 3회 생성)

### V60.12: Four-Phase Pipeline (초기 통과율 극대화)

**비용 무제한** Stage 2 초기 통과율 극대화를 위한 4단계 파이프라인.

**비용:** ~$0.15-0.20/Arc (기존 대비 약 5x)
**예상 초기 통과율:** 90%+

**FourPhaseArcGenerator** (`modules/domain/agents/four_phase_arc_generator.py`):
4단계 파이프라인 오케스트레이터.

```
Phase 1: Preflight   → 완벽한 제약 맵 구축
Phase 2: Generate    → Ensemble 생성 (3개 후보)
Phase 3: Critique    → 즉시 비평 + 자동 수정
Phase 4: Validate    → 3-LLM 합의 검증
```

**Phase 1: PreflightChecker** (`modules/domain/agents/preflight_checker.py`):
생성 전 완벽 분석 (gemini-2.5-pro 사용).

```python
preflight_result = preflight.analyze(prev_arcs)
# Returns:
# - timeline_analysis: 아이템/수여물 타임라인
# - relationship_map: NPC별 관계 상태
# - world_state: 현재 위치/상태
# - absolute_prohibitions: 절대 금지 사항
# - next_arc_guidance: 다음 Arc 가이드
```

**Phase 2: ArcEnsembleGenerator** (V60.11, 재사용):
3개 Arc 후보를 서로 다른 전략으로 병렬 생성.

**Phase 3: ArcCritic** (`modules/domain/agents/arc_critic.py`):
생성된 Arc를 즉시 비평하고 자동 수정.

```python
critique_result, fixed_arc = critic.critique(arc, prev_arcs, constraints)
# Returns:
# - scores: 7개 항목별 점수 (각 10점)
# - verdict: PASS / NEEDS_REVISION / REJECT
# - critical_issues: 심각한 문제 목록
# - auto_fixes: 자동 수정 적용 가능한 항목
```

**비평 기준 (70점 만점):**
| 항목 | 배점 | 내용 |
|------|------|------|
| 아이템 연속성 | 10점 | 중복 획득, 누락 체크 |
| 위치 연속성 | 10점 | 시작 위치 일치 |
| 상태 연속성 | 10점 | 부상/내공 계승 |
| 수여물 타임라인 | 10점 | 중복 수여 체크 |
| tactical_doc 품질 | 10점 | 분량, 화별 구분 |
| joint_docs 정합성 | 10점 | 마지막 화와 일치 |
| 서사적 일관성 | 10점 | 갈등 계승, 캐릭터 |

**Phase 4: ConsensusValidator** (`modules/domain/agents/consensus_validator.py`):
3개 LLM이 서로 다른 관점으로 검증, 합의 도출.

**검증 관점:**
| 관점 | 역할 | 온도 |
|------|------|------|
| continuity_focused | 연속성 전문가 | 0.1 |
| structure_focused | 구조 전문가 | 0.1 |
| narrative_focused | 서사 전문가 | 0.2 |

**합의 로직:**
- CRITICAL 이슈 1개 이상 → REJECT
- 3개 중 2개 이상 REJECT → REJECT
- 그 외 → PASS

**NegativeExampleInjector** (`modules/domain/agents/negative_example_injector.py`):
실패 사례 기반 Few-Shot 학습 (LLM 비용 0원).

```python
# 실패 사례 라이브러리
WUXIA_NEGATIVE_EXAMPLES = {
    "duplicate_acquisition": {...},  # 중복 획득
    "location_teleport": {...},      # 위치 순간이동
    "state_discontinuity": {...},    # 상태 불연속
    "joint_docs_mismatch": {...},    # joint_docs 불일치
    "tactical_doc_quality": {...},   # tactical_doc 품질
    "power_inflation": {...}         # 파워 인플레이션
}
```

**통합 실행 흐름:**
```
attempt == 0:
  1. FourPhaseArcGenerator.generate()
     ├── Phase 1: PreflightChecker.analyze()
     ├── Phase 2: ArcEnsembleGenerator.generate_ensemble()
     ├── Phase 3: ArcCritic.critique() + auto_fix
     └── Phase 4: ConsensusValidator.validate_with_consensus()
  2. (실패 시) ArcEnsembleGenerator (폴백)
  3. (실패 시) Analyst (폴백)
```

**예상 효과:**
| 지표 | V60.11 | V60.12 |
|------|--------|--------|
| Stage 2 초기 PASS율 | 75% | **90%+** |
| Stage 2 최종 PASS율 | 95% | **98%** |
| 비용 | ~3x | ~5x |
| 내부 재시도 | 없음 | 최대 2회 |

### V60.28: ConsensusValidator Arc 1 최적화

**문제**: Arc 1은 이전 Arc가 없어 연속성 검증이 불필요함에도 3개 관점 모두 검증
**수정**: Arc 1에서 `continuity_focused` 관점 스킵, `structure_focused`와 `narrative_focused`만 검증

```python
# consensus_validator.py
if not prev_arcs:
    print("      ⏭️ [Consensus] Arc 1 - 연속성 검증 스킵, 구조/서사만 검증")
    active_perspectives = [p for p in self.perspectives if p["name"] != "continuity_focused"]
```

**효과**: Arc 1 검증 비용 ~33% 절감

### V60.30: ArcDraftValidator 화별 분할 검증 강화

tactical_doc의 화별 구분이 제대로 되었는지 검증하는 3가지 새로운 체크 추가:

**1. 화별 비트 수 검증 (최소 3개)**
```python
# 각 화당 최소 3개의 비트(사건)가 있어야 함
for ep_no, content in episode_sections.items():
    beat_count = self._count_tactical_beats(content)
    if beat_count < 3:
        low_beat_eps.append(f"{ep_no}화({beat_count}비트)")
```

**2. 화별 구조 요소 검증**
```python
# 각 화에 공간/인과/상태 요소가 있어야 함
missing_elements = self._check_structural_elements(content)
# 예: ["공간", "인과"] - 해당 요소 누락
```

**3. ep_count 동기화 검증**
```python
# 선언된 ep_count와 실제 화 개수의 불일치 감지
if abs(actual_ep_count - declared_ep_count) >= 2:
    warnings.append(f"ep_count 불일치: 선언={declared_ep_count}, 실제={actual_ep_count}")
```

### V60.31: 가변 페이싱 복원 (Variable Pacing Fix)

**문제**: 가변 페이싱이 작동하지 않음 - 모든 Arc가 5화로 고정됨
**원인**: `curr_block.get('logic', {})` - Block에 'logic' 키가 없음 (잘못된 구조 참조)

**수정**:
1. **Block 구조 기반 분석** - `content.context/event_villain/solution/reward` 분석
```python
# [V60.31] 페이싱 계산 - Block 구조에 맞게 수정
content_obj = curr_block.get('content', {})
if isinstance(content_obj, dict):
    for key in ['context', 'event_villain', 'solution', 'reward']:
        if content_obj.get(key):
            content_parts.append(str(content_obj[key]))
```

2. **LLM에 결정권 부여** - 시스템은 권장값만 제시
```python
"ep_count": "{ep_count_suggestion} (시스템 추천) 또는 2~6 중 사건 밀도에 맞게 직접 결정"
```

3. **LLM 결정 존중** - 후처리에서 LLM이 결정한 ep_count 사용
```python
llm_ep_count = draft_result.get("ep_count")
actual_ep_count = max(2, min(6, llm_ep_count))
if actual_ep_count != target_ep_count:
    print(f"      📊 [V60.31] 가변 페이싱: 권장 {target_ep_count}화 → LLM 결정 {actual_ep_count}화")
```

**페이싱 기준**:
| 페이싱 | ep_count | 적용 기준 |
|--------|----------|-----------|
| Blitz | 2-3화 | 짧은 전투/탈출, 800자 미만 |
| Standard | 3-4화 | 일반적인 사건, 800-1500자 |
| Epic | 5-6화 | 대규모 전투/전환점, 1500자 초과 |

### V60.32: Stage 2 폴백 체인 수정

**문제 1**: FourPhase/StateLocked가 `attempt == 0`에서만 사용 가능
- 재시도 시 최고 품질 생성기를 사용할 수 없었음

**수정**: 모든 attempt에서 FourPhase/StateLocked 사용 가능
```python
# [V60.32] 1순위: FourPhaseArcGenerator - 모든 attempt에서 사용 가능
if refined_arc is None and 'four_phase' in self.agents:
    # attempt 조건 제거됨
```

**문제 2**: Analyst 폴백 시 protagonist_name 미전달
- LLM이 주인공 이름을 환각하는 문제 발생

**수정**: Analyst 호출 시 protagonist_name 파라미터 추가
```python
refined_arc = self.agents['analyst'].plan_single_arc_v20(
    # ... other params ...
    protagonist_name=protagonist_name or "주인공"  # [V60.32]
)
```

**문제 3**: SelfReflector가 `attempt == 0`에서만 동작
- Analyst 방식에서도 재시도 시 자기 비판 불가

**수정**: Analyst 방식에서 모든 attempt에 SelfReflector 적용
```python
# [V60.32] SelfReflector: Analyst 방식에만 적용 (모든 attempt에서)
if V50_MODULES_AVAILABLE and self.self_reflector and refined_arc:
    if generation_method == "analyst":
        # attempt 조건 제거됨
```

**수정된 폴백 체인**:
```
모든 attempt:
├── 1순위: FourPhaseArcGenerator (90%+ 통과율)
├── 2순위: StateLockedArcGenerator (상태 잠금)
├── 3순위 (attempt≥1): TwoPhaseArcGenerator
├── 4순위 (attempt≥2): TreeOfThoughts 필살기
└── 최종 폴백: Analyst + SelfReflector
```

### Module Summary (V50-V60)

| Version | Modules | Focus |
|---------|---------|-------|
| V50 | 3 | 긴장도, 대사, 서브플롯 |
| V51 | 6 | 호흡, 감정, 실패학습, 캐릭터음성 |
| V52 | 4 | 자기성찰, 적응형재시도, 전문가혼합 |
| V53 | 5 | ToT, ASP, MAD, 서사다양성 |
| V54 | 5 | 캐시, 압축, 2단계생성, 성공패턴 |
| V55 | 7 | 분량/품질 향상 (클리셰, 서브텍스트 등) |
| V55.1 | +1 | Stage 2 TwoPhaseArcGenerator |
| V55.2 | +1 | Constitutional Self-Check |
| V60 | +9 | Stage 2-4 품질 파이프라인 강화 (상태계승, 연속성, HUD 급변감지) |
| V60.1 | +4 | V0128 통합, HUD 로깅, Blueprint 사전필터, 품질 대시보드 |
| V60.10 | +1 | StateExtractor - Arc 상태 구조화 추출 |
| V60.11 | +3 | ArcEnsembleGenerator, ArcDraftValidator, ConstraintCompiler |
| V60.12 | +5 | FourPhaseArcGenerator, PreflightChecker, ArcCritic, ConsensusValidator, NegativeExampleInjector |
| V60.28 | - | ConsensusValidator Arc 1 최적화 (연속성 검증 스킵) |
| V60.30 | - | ArcDraftValidator 화별 분할 검증 강화 (3개 신규 체크) |
| V60.31 | - | 가변 페이싱 복원 (Block 구조 기반 ep_count 계산) |
| V60.32 | - | 폴백 체인 수정 (attempt 제한 해제, protagonist_name 전파) |
| **Total** | **54** | - |

## Debugging and Logging

**Console UI:**
`StudioVisualizer` (via Rich library) provides formatted console output:
- `ui.log(message)` - Standard logging
- `ui.error(message)` - Error display
- Emoji constants in `constants.py:Emojis`

**Log Files:**
Located in `logs/` directory at project root (not per-project).

**Audit Events:**
Runtime audit stored in `SovereignApp.runtime_audit[]`. Event types in `constants.py:AuditEvents`:
- `DB_COMMIT`, `DB_ROLLBACK`
- `STAGE_START`, `STAGE_COMPLETE`
- `CACHE_HIT`, `CACHE_MISS`

**ChromaDB Lock Issues:**
If ChromaDB fails with lock error:
1. Close all Python processes
2. Delete only `LOCK` and `.db-shm` files from `projects/{name}/chroma_db/`
3. Never delete `chroma.sqlite3` or `.db-wal` files

**Common Error Patterns:**
- KeyError in f-strings → Use `_escape_braces()` on user content
- JSON parsing fails → Check `BaseAgent._extract_json_robust()` fallback chain
- Truncated blueprints → Verify MAX_TOKENS continuation in `BaseAgent.ask()`
- HUD state mismatch → Check `MartialManager.snapshot()` and DB storage

**HUD Update Verification:**
See `TEST_GUIDE.md` for detailed HUD update testing procedures. Key success indicators:
- `✅ [HUD] actual_truth 데이터 정상 추출` log message
- `🔥 [HUD Update]` messages showing state changes
- No `🚨 [WARNING]` messages about nested structures

## Database Schema

**anchors table** (key-value store):
- `bible` - Master lore document
- `volumes` - 10-volume strategic plan
- `arcs` - 50-arc tactical designs (5 per volume)
- `sys_caches` - Agent prompt caches (writer_cache, architect_cache, analyst_cache, weaver_cache)

**blueprints table**:
- `ep_num` (PK) - Episode number
- `data` - Scene-by-scene plan JSON

**manuscripts table**:
- `ep_num` (PK) - Episode number
- `text` - Final manuscript text
- `hud_snapshot` - Character state at end of episode

**state_logs table**:
- `ep_num` (PK) - Episode number
- `data` - Full state log JSON
- `summary` - Human-readable summary

**causal_graph table**:
- Karma tracking and causality chains

**episode_bibles table** [V49.5 NEW]:
- `ep_num` (PK) - Episode number
- `new_items` - JSON: 새로 획득한 아이템
- `lost_items` - JSON: 잃어버린/파괴된 아이템
- `new_npcs` - JSON: 새로 등장한 NPC
- `npc_deaths` - JSON: 사망한 NPC
- `relationship_changes` - JSON: [{target, from, to, justification}]
- `state_changes` - JSON: 상태 변화 (부상, 경지 등)
- `time_passed` - 경과 시간 (예: "같은 날 밤", "3일 후")
- `reveals` - JSON: 밝혀진 사실/복선 회수

**Episode Bible 롤백**: `delete_episode_bibles_after(ep_num)` - 특정 화 이후 설정만 삭제

All tables commit through `ProjectContext.db` which wraps `DBManager`. Always use `_safe_commit()`.

## Vector Memory System

`LongTermMemory` class (`modules/core/memory_engine.py`):
- Uses ChromaDB with custom `GoogleEmbeddingFunction`
- Embedding model: `gemini-embedding-001`
- Narrative sampling strategy: First 6000 chars + last 3000 chars (prevents dilution)
- Location: `projects/{name}/chroma_db/`
- Retry logic: 3 attempts with exponential backoff

**Collection naming**: `{project_name}_episodes`

## Model Tier System

### Progressive Tier Upgrades (V40+)

Architect and Writer agents use progressive model upgrades based on rejection count:

**Architect Tiers:**
- Tier 1 (1st attempt): `gemini-2.5-flash`
- Tier 2 (after 1 reject): `gemini-2.5-pro`
- Tier 3 (after 2+ rejects): `gemini-3-pro-preview`

**Writer Tiers:**
- Tier 1 (1st attempt): `gemini-2.5-flash`
- Tier 2 (after 1 reject): `gemini-2.5-pro`
- Tier 3 (after 2+ rejects): `gemini-3-pro-preview`
- **Stage 4 Fixed**: `gemini-3-pro-preview` (no tier changes during retries)

**Fixed Assignments:**
- Analyst: `gemini-3-pro-preview`
- Reviewer/Director: `gemini-2.0-flash`

Model constants defined in `constants.py:AIModels`. Base settings in `config/settings.json`.

Agents receive model tier from `StudioSystem.get_v20_orchestrator_config()`.

## Async/Sync Patterns

**Critical:** SQLite operations are synchronous but may be called from async contexts.

- `SovereignApp._safe_commit()` - Synchronous DB commit with rollback protection
- `SovereignApp._safe_commit_async()` - Async wrapper using `asyncio.to_thread()` for thread safety
- Always check `self.current_project.db.conn.in_transaction` before committing
- Use `_emergency_shutdown()` for critical errors (defined in `main_a.py:99`)

**Transaction Safety:**
```python
# In sync context
self._safe_commit()

# In async context
await self._safe_commit_async()
```

## Data Flow Patterns

**Episode Production Flow:**
```
1. Analyst plans volumes (Stage 1) → Saved to anchors["volumes"]
2. Analyst designs arcs (Stage 2) → Saved to anchors["arcs"]
3. Architect creates blueprint (Stage 3) → Saved to blueprints table
4. Writer generates manuscript (Stage 4) → Saved to manuscripts table + drafts/
5. Director validates → Loops back to Writer if rejected
6. Weaver updates foreshadowing → Updates causal_graph
7. LongTermMemory.embed() → ChromaDB collection
8. MartialManager.snapshot() → Saved in manuscripts.hud_snapshot
```

**Data Synchronization:**
- SQLite DB is always authoritative
- ChromaDB embeddings built from DB manuscripts
- File drafts are human-readable backups only
- `ProjectContext._load_from_db()` runs on init to hydrate memory
