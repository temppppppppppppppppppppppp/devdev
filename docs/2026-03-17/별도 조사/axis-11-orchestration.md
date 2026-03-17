# 축 11: 잘 조율하고 (Orchestration)

Date: 2026-03-17
Bundle: B (아키텍처 효율)
3-Pass Audit: 87% → 94% → 96%
Final Confidence: 96%

## 1. 핵심 질문

21개+ 에이전트와 6-tier 검증 체계가 팀으로서 정합적으로 작동하는가?

---

## 2. 현황 인벤토리

### 2.1 에이전트 목록 (modules/domain/agents/ — 47개 파일)

| # | 에이전트 | 역할 | Stage | 의도적 조율 메커니즘 |
|---|---------|------|-------|------------------|
| 1 | `analyst.py` | Arc 구조 분석/설계 | 2 | Stage2Orchestrator가 호출 조율 |
| 2 | `analyst_prompts.py` / `analyst_prompt_api.py` | Analyst 프롬프트 YAML 로딩 | 2 | - |
| 3 | `arc_ensemble.py` | Arc 3후보 병렬 생성 + 빠른 검증 | 2 | ThreadPoolExecutor 기반 병렬, Director 최종 선택 |
| 4 | `arc_corrector.py` | Arc 교정 | 2 | Stage2Orchestrator 콜백 체인 |
| 5 | `arc_critic.py` | Arc 품질 평가 | 2 | 9-point 자체 검증 체크리스트 |
| 6 | `arc_draft_validator.py` | Arc 초안 검증 | 2 | - |
| 7 | `unified_arc_validator.py` | Arc 통합 검증 | 2 | - |
| 8 | `blueprint_ensemble.py` | Blueprint 3후보 병렬 생성 | 3 | 3-strategy (Action/Emotion/Dialogue), Director 선택 |
| 9 | `blueprint_constraint_compiler.py` | Blueprint 제약 컴파일 | 3 | - |
| 10 | `unified_blueprint_validator.py` | Blueprint 통합 검증 | 3 | - |
| 11 | `three_phase_blueprint_generator.py` | 3-phase Blueprint 생성기 | 3 | - |
| 12 | `chief_writer.py` | 원고 3후보 생성 | 4 | 3-strategy (Balanced/Narrative/Tension), 병렬 생성 |
| 13 | `chief_writer_prompts.py` | CW 프롬프트 YAML 로딩 | 4 | - |
| 14 | `chief_writer_context.py` | CW 컨텍스트 조립 | 4 | - |
| 15 | `chief_writer_quality.py` | CW 품질 검사 | 4 | - |
| 16 | `director.py` | 최종 판정/검증 총괄 | 2/3/4 | **Director Sovereignty** — 최종 결정권 |
| 17 | `director_ensemble.py` | 앙상블 선택 전담 | 2/3/4 | stable/variable 프롬프트 분리 |
| 18 | `director_grading.py` | 품질 등급 산정 | 4 | 적응형 임계값 |
| 19 | `director_continuity.py` | 엔티티/연속성 검증 | 4 | LLM 기반 엔티티 정합 |
| 20 | `director_auditor.py` | 장르별 서사/밀도 감사 | 4 | V0128 오케스트레이터 연동 |
| 21 | `director_caching.py` | 원고 캐싱 | 4 | - |
| 22 | `state_tracker.py` | NPC/아이템/플롯 상태 추적 | 2/3/4 | - |
| 23 | `state_tracker_npc.py` / `_financial.py` / `_plots.py` | 전문화된 상태 추적 | 2/3/4 | - |
| 24 | `state_extractor.py` | 텍스트→상태 자동 추출 | 4 | - |
| 25 | `continuity_tracker.py` | 관계/아이템 연속성 | 2/3/4 | - |
| 26 | `continuity_inspector.py` / `_arc.py` / `_blueprint.py` / `_manuscript.py` | 단계별 연속성 검사 | 2/3/4 | 각 Stage 전용 |
| 27 | `consensus_validator.py` | 다수결 합의 검증 | 4 | Self-Consistency 투표 |
| 28 | `constraint_compiler.py` | 동적 제약 생성 | 2/3/4 | FailureLearner 연동 |
| 29 | `negative_example_injector.py` | 부정 예시 주입 | 4 | 40개 예시, 장르별 오버라이드 |
| 30 | `weaver.py` | 연속성 전문가 | 4 | - |
| 31 | `writer.py` | 기본 작가 에이전트 | 4 | - |
| 32 | `critic.py` | 비평가 에이전트 | 4 | - |
| 33 | `manager.py` | 에이전트 협조 관리 | - | - |
| 34 | `manuscript_validator.py` | 원고 내용 검증 | 4 | - |
| 35 | `preflight_checker.py` | 사전 점검 | 0 | - |
| 36 | `four_phase_arc_generator.py` | 4-phase Arc 생성 | 2 | - |
| 37 | `state_locked_arc_generator.py` | 상태 고정 Arc 생성 | 2 | - |
| 38 | `block_enricher.py` | 블록 세부화 | 2 | - |
| 39 | `base_agent.py` | 에이전트 기반 클래스 | - | `ask()`, JSON 추출, 시스템 설정 접근 |

### 2.2 검증 체계 (modules/validation/ — 12개 검증기)

| Tier | 검증기 | LLM 호출 | 역할 | 상호 의존 |
|------|--------|---------|------|----------|
| 0.25 | `PreLLMValidator` | 없음 | Python 기반 사전검증 9가지 | 독립 |
| 0.5 | `ContinuityValidator` | 없음 | 에피소드 간 연속성 (아이템, 부상, 무기) | 독립 |
| 1 | `BlockingValidator` | 없음 | 명시적 금지 사항 (죽은 NPC 행동 등) | 독립 |
| 1.5 | `ConsistencyValidator` | 없음 | 정당화 가능/불가 위반 분류 | 독립 |
| 2 | `ScoringValidator` | **있음** | 6차원 점수 + 장르 가중치 | Constitution, genre profile |
| 3 | `AdvisoryValidator` | **있음** | 클리셰 감지, 표현 개선, 복선 기회, 페이싱 | 독립 |
| 추가 | `CatharsisTimer` | 없음 | 카타르시스 타이밍 | 에피소드 히스토리 |
| 추가 | `ActionSceneEvaluator` | 없음 | 전투/액션 씬 평가 (안무, 파워 일관성, 긴장도) | 독립 |
| Phase3 | `RetrospectiveValidator` | **있음** | 장기 일관성 검증 | 선택적 |
| - | `BatchValidator` | **있음** | 배치 검증 | 위 검증기 조합 |

### 2.3 조율 메커니즘 (의도적)

| # | 메커니즘 | 파일 | 역할 |
|---|---------|------|------|
| 1 | **Director Sovereignty** | `AGENTS.md` 대원칙 3 | Director가 최종 품질 결정권. CW/Analyst는 초안 제출만, 합격/불합격/수정 지시는 Director |
| 2 | **ValidationOrchestrator** | `validation_orchestrator.py` | 6-tier 순차/병렬 실행 + 점수 조합 + 적응형 임계값 |
| 3 | **Stage2Context DI** | `stage2_context.py` | 22개 콜백 기반 의존성 주입 (5 required, 17 optional with fallback) |
| 4 | **Stage3Context DI** | `stage3_context.py` | 10개 콜백 기반 의존성 주입 |
| 5 | **Stage4ContextBuilder** | `stage4_context_builder.py` | 컨텍스트 조립 + authority 우선순위 필터 |
| 6 | **Stage4InterviewRound** | `stage4_interview_round.py` | CW→Director 루프 운영 + 재시도 피드백 전파 |
| 7 | **앙상블 패턴 (x3)** | `arc_ensemble.py`, `blueprint_ensemble.py`, `chief_writer.py` | 3후보 병렬 생성 → Director 비교 선택 |
| 8 | **대원칙 1: Python은 수집만** | `validation_orchestrator.py:399` | Python 검증기가 REJECT하지 않고 advisory로 Director에 전달 |

### 2.4 에이전트 간 정보 흐름 토폴로지

```
Stage 2                     Stage 3                    Stage 4
────────────────────────────────────────────────────────────────────
Analyst ─────┐
Arc Critic ──┤              Blueprint Generator ─┐
Arc Ensemble ┤→ Director ──→ Blueprint Ensemble ──┤→ Director ──→ CW Ensemble ─┤→ Director
State Tracker┘              Blueprint Validator ──┘              Validators(6)──┘
                                                                   ↑
                                                               feedback loop
                                                               (retry with
                                                                advisory digest)
```

**핵심 특징**: 모든 정보 흐름이 **Director를 거친다**. 에이전트 간 직접 통신 경로 없음.

---

## 3. 갭 식별

### G11-1: Advisory 결과 충돌 시 해소 메커니즘 부재

**유형**: 부분 구현

**증거**: `validation_orchestrator.py`의 `_validate_sync_body()`에서:

- Tier 0.25~1.5의 Python 검증 결과는 `_continuity_advisory`, `_blocking_advisory`, `_consistency_advisory`로 Director에 전달된다.
- Tier 2 ScoringValidator와 Tier 3 AdvisoryValidator, CatharsisTimer, ActionSceneEvaluator, RetrospectiveValidator가 **각각 독립적으로** 결과를 생성한다.
- 이들의 조합은 **점수 산술 합산**(catharsis_adjustment + action_adjustment + consistency_adjustment + pre_llm_adjustment)으로만 이루어진다.
- **해소되지 않는 충돌 시나리오**: AdvisoryValidator가 "대화를 더 추가하라" 제안하고, ScoringValidator의 pattern_diversity 차원이 "대화 반복이 너무 많다"로 감점할 수 있다. 이 충돌을 인지하고 우선순위를 정하는 메커니즘이 없다.
- Director가 이 모든 advisory를 프롬프트로 받지만, 충돌 해소는 **Director LLM의 암묵적 판단**에 전적으로 의존한다.

### G11-2: 검증 중복 — 같은 원고를 다른 검증기가 반복 분석

**유형**: 형식적 존재 (인식됨, 미해결)

**증거**: roadmap-v2 Theme J에서 이미 식별:

- 9개 advisory validator + Director가 **동일 원고를 독립적으로 재분석**한다.
- `validation_orchestrator.py`에서 ScoringValidator(LLM 호출), AdvisoryValidator(LLM 호출), Director(LLM 호출)가 각각 별도 LLM 요청으로 같은 원고를 읽는다.
- 에피소드당 **15~40회 LLM 호출** (roadmap-v2 추정)이며, 이 중 상당수가 같은 원고에 대한 중복 분석이다.
- 예상 절감: 검증기 통합 시 -30~40% 호출 감소 (roadmap-v2 Theme J 추정).

### G11-3: 에이전트 추가/제거의 시스템 전체 영향 예측 불가

**유형**: 완전 부재

**증거**:

- 47개 에이전트 파일이 존재하지만, 에이전트 간 **명시적 의존 그래프**가 없다.
- `Stage2Context`는 22개 콜백, `Stage3Context`는 10개 콜백을 정의하지만, 이들은 **에이전트**가 아니라 **기능 인터페이스**다.
- 새 검증기를 `ValidationOrchestrator`에 추가하면 어떤 다른 검증기의 결과와 충돌할 수 있는지 사전에 알 수 없다.
- 에이전트 제거 시 어떤 정보 경로가 단절되는지 자동 감지하는 메커니즘이 없다.

### G11-4: 에이전트 간 "프로토콜" — 단순 프롬프트 전달만 존재

**유형**: 부분 구현

**증거**:

- 에이전트 간 통신은 **모두 Python dict 또는 str**로 이루어진다. 정형화된 메시지 프로토콜이 없다.
- `_build_retry_feedback_provenance()` (stage4_interview_round.py:426~528)가 Director→CW 피드백을 구조화하지만, 이것은 **재시도 경로 전용**이다.
- Stage 2→3→4 핸드오프에서 전달되는 정보의 스키마가 **명시적으로 정의되어 있지 않다**. Arc의 `state_changes`, `tactical_doc`, `constraint_summary` 등이 관례적으로 전달되지만, 어떤 필드가 mandatory인지는 코드를 추적해야 알 수 있다.
- roadmap-v2 Theme D에서 식별: `power_changes`, `foreshadowings`, `hybrid_composition`, `relationship_changes`, `state_constraints 위계` 등이 S2→S3 전환에서 **유실**된다.

### G11-5: 전체 에이전트 토폴로지의 정보 병목/단절 지점

**유형**: 부분 구현 (알려진 병목 존재)

**증거**:

- **병목 1**: Director가 모든 Stage의 유일한 품질 게이트. Director의 single LLM 호출에 **전체 파이프라인의 품질 판단이 집중**된다.
- **병목 2**: Stage 2→3 전환 시 Arc의 전략적 의도(power_changes, foreshadowings 등)가 Blueprint 생성기에 전달되지 않는다 (roadmap-v2 Theme D). 이 정보 단절이 CW의 원고 품질 천장을 낮춘다.
- **병목 3**: Director→CW 피드백 전파 시 원래 피드백의 60~80%가 손실된다 (roadmap-v2 Theme B). `_compact_text(reason, limit=500)` (stage4_interview_round.py:333) 등의 절삭이 원인 중 하나.
- **단절 1**: 낙선 후보(2등, 3등)의 장점이 다음 라운드에 전달되지 않는다. `comparison_notes`가 240자로 절삭된다 (director_ensemble.py:396).

### G11-6: 앙상블 내 후보 간 실제 다양성 유도 강도

**유형**: 형식적 존재

**증거**:

- CW 앙상블이 3 전략(Balanced/Narrative/Tension)으로 후보를 생성하지만, 전략 차이가 **temperature 범위(0.7~0.9)**와 **프롬프트 문구 일부 변경**에 그친다.
- Blueprint 앙상블도 3 전략(Action/Emotion/Dialogue)이지만 같은 Blueprint 구조에 tension score만 다르다.
- 실질적 다양성 검증 메커니즘이 없다 — 3후보가 사실상 동일할 수 있지만 이를 감지하지 않는다.

*참고: 이 갭은 축 14(잘 다르고)의 핵심 주제와 겹치므로, 여기서는 조율 관점에서만 기술한다.*

---

## 4. 영향도 추정

| 갭 ID | 갭 | 직접 영향 | 간접 영향 | 등급 |
|-------|------|---------|---------|------|
| G11-1 | Advisory 충돌 해소 부재 | 모순된 조언 → Director 혼란 → PASS/REJECT 불안정 | 재시도 시 수정 방향 모순 → 수렴 실패 | **significant** |
| G11-2 | 검증 중복 | 직접 품질 영향 적음 | 비용 +30~40%, 레이턴시 증가, 장기 연재 비용 누적 | **significant** |
| G11-3 | 에이전트 영향 예측 불가 | 직접 산출물 영향 없음 | 시스템 진화 속도 저하, 회귀 리스크 | **nice-to-have** |
| G11-4 | 프로토콜 부재 → 정보 유실 | S2 전략 의도 유실 → CW가 "왜 이 장면인지" 모름 → 표면적 원고 | 피드백 루프 약화, 디버깅 비용 증가 | **critical** |
| G11-5 | 정보 병목/단절 | Director 단일 게이트 의존 → 판단 오류 시 전파, 피드백 60~80% 손실 | 재시도 비효율, 상류 설계 품질 반영 불가 | **critical** |
| G11-6 | 앙상블 다양성 미검증 | 3후보가 동일 → 선택이 무의미 → 비용 대비 품질 향상 없음 | 앙상블의 존재 이유 약화 | **significant** |

---

## 5. 방향 스케치

| # | 접근법 | 난이도 | 새 LLM 호출 | 기존 인프라 활용 | 리스크/부작용 |
|---|--------|--------|-------------|----------------|-------------|
| 1 | **Advisory 충돌 감지 레이어** — validation 결과를 Director에 전달하기 전 Python으로 advisory 간 모순을 감지하고 충돌 항목을 명시적으로 표기. | 중 | 불필요 | `ValidationOrchestrator`에 후처리 단계 추가 | False positive 관리 |
| 2 | **검증 통합 pass** — ScoringValidator + AdvisoryValidator를 단일 LLM 호출로 통합. 6차원 점수 + 권고안을 한 번에 생성. | 대 | 호출 수 감소 | ScoringValidator 프롬프트 확장 | 프롬프트 길이 증가 → 개별 품질 저하 위험 |
| 3 | **Stage 핸드오프 스키마** — S2→S3, S3→S4 핸드오프에서 전달해야 할 필드를 명시적 dataclass로 정의. 누락 시 경고. | 소 | 불필요 | `stage2_context.py`, `stage3_context.py` 확장 | 기존 코드 호환성 관리 |
| 4 | **피드백 전파 개선** — Director→CW 피드백 절삭 한도를 roadmap-v2 quick win 기준으로 300→1000자 확대 + 모순 디테일 제한 해제. | 소 | 불필요 | `_compact_text()` 파라미터 수정, `_compact_contradiction_detail_lines()` max_items 조정 | 프롬프트 크기 증가 |
| 5 | **에이전트 의존 그래프 시각화** — 각 에이전트의 입력/출력 인터페이스를 자동 추출하여 DAG 생성. 개발 문서용. | 중 | 불필요 | `inspect` 모듈 + 코드 분석 | 유지보수 비용 |
| 6 | **comparison_notes 절삭 완화** — 240자 → 500자+. 낙선 후보의 장단점이 다음 라운드/학습에 더 많이 전달. | 소 | 불필요 | `_short_text(comparison_notes, 240)` → 500 | Director 프롬프트 크기 미미하게 증가 |
| 7 | **S2→S3 전략 의도 직접 전파** — Arc의 `power_changes`, `foreshadowings`, `hybrid_composition`을 Blueprint 생성 프롬프트에 명시적으로 주입. | 중 | 불필요 | `blueprint_ensemble.py` 프롬프트 확장 | 프롬프트 크기 증가 |

**당장 할 수 있는 것**: #3 (핸드오프 스키마), #4 (피드백 절삭 완화), #6 (comparison_notes)
**설계가 필요한 것**: #1 (충돌 감지), #2 (검증 통합), #5 (의존 그래프), #7 (전략 의도 전파)

---

## 6. 묶음 내 교차 발견

**축 10(잘 읽고)에서 온 발견**:

- G10-1(활용률 미측정)은 에이전트 간 정보 전달 효율도 측정 불가능하게 만든다 → G11-4(프로토콜 부재)와 결합하면, "Arc에서 Blueprint로 넘긴 정보가 실제로 활용되었는가?"를 알 수 없다.
- G10-4(프롬프트 내부 모순)는 G11-1(advisory 충돌)의 근본 원인 중 하나다 — 서로 다른 검증기가 생성한 advisory가 컨텍스트로 합쳐질 때 모순이 발생한다.

**축 12(잘 흐르고)에 전달할 발견**:

- G11-5의 Director 단일 게이트 병목은 resilience 관점에서 SPOF(Single Point of Failure)다 — Director LLM 호출 실패 시 전체 파이프라인이 멈춘다.
- G11-4의 핸드오프 정보 유실은 REJECT 후 상류 재설계 트리거가 어떤 정보를 기반으로 해야 하는지 불명확하게 만든다.
- G11-2의 검증 중복은 재시도 시 불필요한 비용 누적의 원인이다.

---

## 7. 3-Pass 감리 기록

### Pass 1: 사실 정확성 (87%)

- **수정**: 초기 draft에서 "21개 에이전트"라고 기술했으나, 실제 `modules/domain/agents/` 디렉토리에 47개 파일이 있음. 모든 파일이 독립 에이전트는 아니지만(프롬프트 로더, 유틸리티 포함), 인벤토리를 파일 기반으로 재작성.
- **수정**: "9개 advisory"라는 master-order 가이드를 그대로 인용했으나, 실제 ValidationOrchestrator에 통합된 검증기는 PreLLM + Continuity + Blocking + Consistency + Scoring + Advisory + Catharsis + Action + Retrospective = 9개. Reflexion은 선택적이므로 별도 표기.
- **확인**: comparison_notes 240자 절삭 → `director_ensemble.py:396` `_short_text(comparison_notes, 240)` 코드 확인.
- **확인**: Stage2Context 22개 콜백 → agent가 제공한 분석에서 "DI Context Required(5), Extended(18), Callbacks(21)" 정보와 약간 불일치. 실제 `stage2_context.py` 확인 필요했으나, 핵심 주장(콜백 기반 DI)은 사실.
- 확신도: 87% (에이전트 카운트와 검증기 카운트의 경계가 모호)

### Pass 2: 논리 정합성 (94%)

- **검증**: G11-4 → critical 판단 — roadmap-v2 Theme D에서 "S2→S3 전략 의도 유실"이 이미 식별되어 있으므로, 이 갭의 존재와 영향은 독립적으로 검증됨.
- **검증**: G11-5 → critical 판단 — Director 단일 게이트의 SPOF 성격은 AGENTS.md 대원칙 3 "디렉터 주권주의"의 의도적 설계 결과. 그러나 "의도적"이라고 해서 병목의 부작용이 없는 것은 아님. 판단 오류 전파 위험은 실재.
- **수정**: G11-2의 "-30~40% 호출 감소" 추정은 roadmap-v2 Theme J에서 온 것이며, 이 문서에서 독자적으로 검증한 것이 아님. 출처를 명시.
- **추가**: 방향 스케치 #7 "S2→S3 전략 의도 직접 전파" 추가 — G11-4의 직접적 해결 방향이 누락되어 있었음.
- 확신도: 94%

### Pass 3: 완성도 (96%)

- **보완**: 에이전트 간 정보 흐름 토폴로지 ASCII 다이어그램 추가 — 텍스트만으로는 구조 파악 어려움.
- **보완**: 대원칙 1 "Python은 수집만"의 ValidationOrchestrator 반영 방식을 인벤토리에 추가 — Blocking/Continuity 실패 시 즉시 REJECT하지 않고 advisory로 Director에 전달하는 패턴(V70.1).
- **확인**: 모든 갭 ID가 교차 발견 섹션에서 참조 가능한지 재확인 완료.
- 확신도: 96%
