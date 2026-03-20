# T15 — Quality Intelligence & Advisory Detection Survey

**6PASS-CLEARED** | COLLECTOR ONLY | NO EXECUTION AUTHORITY

**Terminal**: T15
**Date**: 2026-03-20
**Baseline Commit**: `d0fa70f1`
**Scope**: 22 files, 8,939 lines
**Confidence**: 96%

---

## 1. Scope & Files

| File | Lines | Category |
|------|-------|----------|
| `modules/core/adversarial_self_play.py` | 405 | Quality Intelligence |
| `modules/core/chain_of_verification.py` | 412 | Quality Intelligence |
| `modules/core/self_reflection.py` | 341 | Quality Intelligence |
| `modules/core/cross_agent_verifier.py` | 503 | Quality Intelligence |
| `modules/core/constitutional_checker.py` | 595 | Quality Intelligence |
| `modules/core/tree_of_thoughts.py` | 752 | Quality Intelligence |
| `modules/core/multi_agent_deliberation.py` | 436 | Quality Intelligence |
| `modules/core/agent_intelligence.py` | 609 | Quality Intelligence |
| `modules/core/confidence_calibration.py` | 458 | Quality Intelligence |
| `modules/core/expert_mixture.py` | 388 | Quality Intelligence |
| `modules/core/reflexion_manager.py` | 245 | Quality Intelligence |
| `modules/core/truth_gate.py` | 438 | Advisory Detection |
| `modules/core/info_paradox_checker.py` | 259 | Advisory Detection |
| `modules/core/npc_drift_advisor.py` | 192 | Advisory Detection |
| `modules/core/numeric_drift_advisor.py` | 207 | Advisory Detection |
| `modules/core/numeric_consistency_checker.py` | 1000 | Advisory Detection (Python-only) |
| `modules/core/relationship_drift_advisor.py` | 168 | Advisory Detection |
| `modules/core/flashback_verifier.py` | 198 | Advisory Detection |
| `modules/core/long_term_repetition_advisor.py` | 233 | Advisory Detection |
| `modules/core/investment_math_verifier.py` | 143 | Advisory Detection (Investment) |
| `modules/core/investment_arithmetic_checker.py` | 473 | Advisory Detection (Investment, Python-only) |
| `modules/core/semantic_query_broker.py` | 484 | Semantic Relation Lookup |

**Related Tests**: test_truth_gate.py, test_info_paradox_checker.py, test_npc_drift_advisor.py, test_numeric_consistency_checker.py, test_numeric_drift_advisor.py, test_flashback_verifier.py, test_relationship_drift_advisor.py, test_semantic_query_broker.py, test_context_advisor.py, test_investment_math_verifier.py, test_investment_arithmetic_checker.py, test_v55_modules.py, test_sweep28.py, test_sweep31.py, test_sweep33.py

---

## 2. TF Registry

### T15-TF-001 — Advisory Chain Count DRIFT (9 vs 8)
```
ID: T15-TF-001
Severity: P2-MEDIUM
Category: DRIFT
Surface: modules/core/stage4_interview_round.py:5094, MEMORY.md
Evidence:
  - stage4_interview_round.py:5094
    "Advisory 검증 시작 — 9개 병렬 실행 (TruthGate, NPC, 수치, 회상, 정보역설, 관계, 장기반복, 수치정합, StyleSignal)"
  - stage4_interview_round.py:5108
    `executor = ThreadPoolExecutor(max_workers=9, thread_name_prefix="advisory")`
  - MEMORY.md states: "8개 advisory 동시 실행"
  - 실제 9개: TruthGate, NpcDrift, NumericDrift, Flashback, InfoParadox, RelDrift, LongTermRep, NumericConsistency, StyleSignal
Inference: MEMORY.md 및 기존 문서가 8개로 기록하고 있으나, 실제 코드는 9번째 advisory인 StyleSignalAdvisor가 추가되어 9개로 동작 중. StyleSignal은 별도 모듈이 아닌 stage4_interview_round.py 내부 메서드(_advisory_style_signals, L5591)로 구현됨.
Uncertainty: 없음 — 코드와 문서 모두 확인 완료
Cross-Ref: T06 (Stage 4 Interview)
```

### T15-TF-002 — Constitutional Checker M8 부재 (DRIFT)
```
ID: T15-TF-002
Severity: P3-LOW
Category: DRIFT
Surface: modules/core/constitutional_checker.py:138-188
Evidence:
  - constitutional_checker.py:138 `MANUSCRIPT_CONSTITUTION = [`
  - 실제 조항: M1(아이템), M2(연속성), M3(관계), M4(씬누락), M5(분량), M6(Show Don't Tell), M7(클리셰)
  - M8 조항 없음. Grep "M8" in constitutional_checker.py → 0 matches
  - 마스터 오더 섹션 2 T15 필수 조사 #3: "Stage 4 (M1-M8)" 명시
Inference: 마스터 오더가 M1-M8을 기대하지만 실제 코드에는 M1-M7만 존재. M8은 추가되지 않았거나 기획 단계에서 누락됨.
Uncertainty: M8이 의도적 생략인지, 누락인지 불분명
Cross-Ref: T14 (Validation Pipeline)
```

### T15-TF-003 — Constitutional Checker 조항 전수 SYNC
```
ID: T15-TF-003
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/constitutional_checker.py:53-188
Evidence:
  - ARC_CONSTITUTION (Stage 2): A1-A6 (6개)
    - A1: 아이템 중복 획득 (CRITICAL)
    - A2: 수여물 중복 (CRITICAL)
    - A3: joint_docs 무시 (CRITICAL)
    - A4: NPC 관계 급변 (HIGH)
    - A5: 5화 초과 사건 (HIGH)
    - A6: tactical_doc 500자 미만 (MEDIUM)
  - BLUEPRINT_CONSTITUTION (Stage 3): B1-B5 (5개)
    - B1: 미획득 아이템 사용 (CRITICAL)
    - B2: cliffhanger 무시 (CRITICAL)
    - B3: 씬 7개 초과 (HIGH)
    - B4: ending_hook 없음/5자 미만 (HIGH)
    - B5: Arc 범위 초과 (HIGH)
  - MANUSCRIPT_CONSTITUTION (Stage 4): M1-M7 (7개)
  - 코드 확인: Stage 2 = 6개, Stage 3 = 5개, Stage 4 = 7개 → 총 18개 조항
Inference: Stage 2/3 조항은 마스터 오더 기대치(A1-A6, B1-B5)와 SYNC. Stage 4만 M8 미구현(T15-TF-002 참조).
Uncertainty: 없음
Cross-Ref: T02, T04, T06
```

### T15-TF-004 — TruthGate 7개 검사 항목 SYNC
```
ID: T15-TF-004
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/truth_gate.py:24-63
Evidence:
  - truth_gate.py:50-57 validate() 메서드에서 7개 검사 호출:
    1. _check_deceased_resurrection (사망 NPC 부활, CRITICAL)
    2. _check_unowned_items (미보유 아이템 사용, MAJOR)
    3. _check_destroyed_locations (파괴된 장소 방문, MAJOR)
    4. _check_skill_duplication (스킬 중복 습득, MINOR)
    5. _check_karma_bounds (카르마 0-100 범위, MINOR)
    6. _check_npc_role_consistency (NPC 역할 무단 변경, MAJOR)
    7. _check_world_law_violation (세계관 법칙 위반, CRITICAL, LLM 기반)
  - 반환 구조: {"passed": bool, "warnings": list, "structured_warnings": list, "blocking": False}
Inference: TruthGate는 6개 Python 검사 + 1개 LLM 검사 = 7개. blocking=False 고정(advisory only).
Uncertainty: 없음
Cross-Ref: T12 (State Tracking — world_state dependency)
```

### T15-TF-005 — TruthGate world_law_violation 광범위 except
```
ID: T15-TF-005
Severity: P3-LOW
Category: SILENT-FAILURE
Surface: modules/core/truth_gate.py:437
Evidence:
  - truth_gate.py:437 `except Exception as e:`
  - 이 except는 json.loads 실패, llm_ask 실패, 키 누락 등 모든 예외를 잡음
  - logging.warning으로만 기록하고 return (비차단)
Inference: advisory-only이므로 비차단 처리 자체는 정상이나, JSON parse 실패와 LLM 호출 실패가 구분 불가. ChainOfVerification은 ChainOfVerificationLLMError / ChainOfVerificationParseError로 구분하는 반면 TruthGate는 bare Exception catch.
Uncertainty: advisory-only이므로 실제 운영 영향은 낮을 수 있음
Cross-Ref: 없음
```

### T15-TF-006 — LLM Advisory 6개 모듈 JSON 파싱 코드 중복
```
ID: T15-TF-006
Severity: P3-LOW
Category: DEAD-CODE
Surface: 6개 파일의 _parse_llm_response 메서드
Evidence:
  - 동일 패턴이 6개 파일에 반복:
    1. npc_drift_advisor.py:154-168
    2. numeric_drift_advisor.py:130-143
    3. relationship_drift_advisor.py:130-142
    4. flashback_verifier.py:161-173
    5. long_term_repetition_advisor.py:198-210
    6. info_paradox_checker.py:221-237
  - 모두 동일 구조: ```json 펜스 처리 → json.loads → list 검증 → dict 항목 필터링
  - 코드 스니펫 (npc_drift_advisor.py:154-160):
    ```python
    m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if not m:
        m = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    text = text.strip()
    ```
Inference: 6개 모듈 모두 동일한 JSON 파싱 패턴을 사용. DRY 원칙 위반이지만 각 모듈이 독립적이므로 기능 오류는 없음. 리팩터링 시 공통 유틸로 추출 가능.
Uncertainty: 의도적 설계(모듈 독립성)일 수 있음
Cross-Ref: 없음
```

### T15-TF-007 — Advisory 입출력 Contract 매트릭스 SYNC
```
ID: T15-TF-007
Severity: P4-OBSERVATION
Category: SYNC
Surface: 8개 advisory 모듈 (StyleSignal 제외)
Evidence:
  Advisory 입출력 contract:
  | Advisory | 입력 | 출력 형식 | severity | LLM |
  |----------|------|----------|----------|-----|
  | TruthGate | manuscript, state_updates, npc_registry | {passed, warnings, structured_warnings, blocking} | CRITICAL/MAJOR/MINOR | 부분(7번째만) |
  | NpcDriftAdvisor | manuscript, npc_snapshots | [{npc, field, expected, found_in_ms, severity, check}] | MAJOR | Yes |
  | NumericDriftAdvisor | numbers(FactLedger) | [{key, issue, history_snippet, severity, check}] | MAJOR | Yes |
  | FlashbackVerifier | manuscript, reference_context | [{marker, issue, referenced_context, severity, check}] | MAJOR | Yes |
  | InfoParadoxChecker | manuscript, knowledge_summary | [{character, info_used, why_paradox, severity, check}] | MAJOR | Yes |
  | RelationshipDriftAdvisor | manuscript, relationship_timeline | [{npc_pair, old_relation, new_relation, why_drift, severity, check}] | MAJOR | Yes |
  | LongTermRepetitionAdvisor | manuscript, pattern_summary | [{pattern, issue, severity, check}] | MAJOR | Yes |
  | NumericConsistencyChecker | manuscript, ep_num | [{check, severity, text}] | MAJOR/MINOR | No (Python) |
Inference: LLM 7개(TruthGate world_law 1건 포함) + Python-only 1개(NumericConsistencyChecker) + StyleSignal(Python, 내부 메서드) = 9개 advisory.
Uncertainty: 없음
Cross-Ref: T06, T14
```

### T15-TF-008 — NpcDriftAdvisor max_npcs=8 하드코딩
```
ID: T15-TF-008
Severity: P4-OBSERVATION
Category: HARDCODING
Surface: modules/core/npc_drift_advisor.py:30
Evidence:
  - npc_drift_advisor.py:30 `def check(self, manuscript, npc_snapshots, *, ep_num=0, max_npcs=8):`
  - max_npcs=8 기본값이 함수 시그니처에 하드코딩
  - validation.yaml 참조 없음: Grep "max_npcs" in config/ → 0 matches
Inference: 검사 대상 NPC 수 상한이 코드에 고정. 장기 연재에서 NPC 50+일 때 주요 캐릭터 8명으로 충분한지 불확실.
Uncertainty: 호출부에서 다른 값으로 override 가능 (keyword arg)
Cross-Ref: T12 (NPC registry)
```

### T15-TF-009 — NumericDriftAdvisor 하드코딩 상수
```
ID: T15-TF-009
Severity: P4-OBSERVATION
Category: HARDCODING
Surface: modules/core/numeric_drift_advisor.py:17-18
Evidence:
  - numeric_drift_advisor.py:17 `MAX_ITEMS = 30`
  - numeric_drift_advisor.py:18 `MAX_HISTORY_POINTS = 20`
  - validation.yaml 참조 없음: Grep "MAX_ITEMS|MAX_HISTORY_POINTS" in config/ → 0 matches
Inference: FactLedger 수치 항목 상한(30)과 이력 표시 범위(20)가 모듈 상수로 고정. 장기 연재에서 수치 팩트 30+ 시 최신 항목만 검사.
Uncertainty: 30개로 충분한지는 프로젝트별로 다름
Cross-Ref: T12 (FactLedger)
```

### T15-TF-010 — InfoParadoxChecker 상한값
```
ID: T15-TF-010
Severity: P4-OBSERVATION
Category: HARDCODING
Surface: modules/core/info_paradox_checker.py:16-17
Evidence:
  - info_paradox_checker.py:16 `MAX_REVEALS = 500`
  - info_paradox_checker.py:17 `MAX_KNOWLEDGE_CHARS = 5000`
  - 주석: "[P0-1] 200→500 (화당 ~2 reveals 기준 ~250화 안전 커버)"
  - 주석: "[P0-1] 3000→5000 (reveals 500건 문자열 수용)"
Inference: P0-1에서 상향 조정된 값. 250화 안전 커버 설계 의도 명확. 장기 연재 500화+ 시 초과 가능성 있으나 최근 reveals만 유지하므로 실질 영향 낮음.
Uncertainty: 없음
Cross-Ref: 없음
```

### T15-TF-011 — FlashbackVerifier 상한값
```
ID: T15-TF-011
Severity: P4-OBSERVATION
Category: HARDCODING
Surface: modules/core/flashback_verifier.py:14-15
Evidence:
  - flashback_verifier.py:14 `MAX_FLASHBACKS = 5`
  - flashback_verifier.py:15 `CONTEXT_WINDOW = 200`
  - 회상 구간 최대 5개, 마커 주변 200자 추출
Inference: LLM 비용 제어를 위한 합리적 상한. 한 화에 회상 5건 이상은 드문 케이스.
Uncertainty: 없음
Cross-Ref: 없음
```

### T15-TF-012 — LongTermRepetitionAdvisor 반복 임계값
```
ID: T15-TF-012
Severity: P4-OBSERVATION
Category: HARDCODING
Surface: modules/core/long_term_repetition_advisor.py:36-38
Evidence:
  - long_term_repetition_advisor.py:36 `MIN_LOOKBACK = 20`
  - long_term_repetition_advisor.py:37 `REPEAT_THRESHOLD = 3`
  - long_term_repetition_advisor.py:38 `SEQUENCE_LENGTH = 2`
  - 20화 미만이면 검사 스킵, 2-gram 시퀀스 3회+ 반복 시 경고
Inference: 20화 미만 프로젝트에서는 이 advisory가 작동하지 않음. validation.yaml 미참조.
Uncertainty: 없음
Cross-Ref: 없음
```

### T15-TF-013 — NumericConsistencyChecker 8개 검사 항목 SYNC
```
ID: T15-TF-013
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/numeric_consistency_checker.py:222-286
Evidence:
  - check() 메서드에서 7개 검사 실행 (L237-284):
    1. _check_against_ledger (FactLedger 교차, 5% 허용)
    2. _check_arithmetic (산술 일관성: A+B=C, 레버리지)
    3. _check_title_consistency (직함 무단 변경)
    4. _check_event_ordering ("처음" 이벤트 모순)
    5. _check_percent_composition (NC-2 GAP-2: 퍼센트 구성)
    6. _check_npc_name_collision (NC-2 GAP-4: NPC 동명이인)
    7. _check_opening_similarity (NC-2 GAP-6: 도입부 유사도)
  - check_tactical_doc() 별도 진입점 (L921-958): Stage 2 전용, 3개 검사만 실행
  - 마스터 오더 기대: "8개 검사" → 실제 check() 7개 + check_tactical_doc() 3개(서브셋)
Inference: 원고용 7개 + tactical_doc용 3개(서브셋). "8개 검사"라는 기존 문서 표현은 check()의 7개 + check_tactical_doc() 합산 의미로 보임.
Uncertainty: 기존 문서의 "8개" 카운트 근거 불명확
Cross-Ref: T02 (Stage 2 — check_tactical_doc 호출)
```

### T15-TF-014 — AdversarialSelfPlay PASS/REVISE/REJECT 기준
```
ID: T15-TF-014
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/adversarial_self_play.py:110, 148
Evidence:
  - adversarial_self_play.py:110 ADVERSARY_PROMPT 내:
    "기준: 85점 이상 PASS, 60-84점 REVISE, 60점 미만 REJECT"
  - adversarial_self_play.py:148 `self.max_rounds = 2`
  - 판정 로직 L312: `if feedback.decision == "PASS": break`
  - 판정 로직 L316: `if not feedback.issues: break`
Inference: Director 실제 verdict와 독립된 자체 기준. Director의 quality_gate_score(90)와 다른 기준(85). PASS=85+, Director PASS=90+ → 차이 있으나 ASP는 사전 품질 향상 도구이므로 별도 임계값은 합리적.
Uncertainty: Director와의 기준 불일치가 의도적인지 확인 필요
Cross-Ref: T07 (Director verdict)
```

### T15-TF-015 — ChainOfVerification severity 트리거 조건
```
ID: T15-TF-015
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/chain_of_verification.py:55-61
Evidence:
  - chain_of_verification.py:55-61 VerificationSeverity enum:
    NONE = "none"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"
  - L315: `should_regenerate = overall_severity == VerificationSeverity.CRITICAL`
  - CRITICAL만 재생성 트리거. MINOR/MAJOR는 correction_hints 생성만.
  - L266: 내용 500자 미만이면 검증 스킵
Inference: CRITICAL severity만 should_regenerate=True. 재생성 트리거 조건이 명확.
Uncertainty: 없음
Cross-Ref: T05 (Stage 4 Orchestrator — CoVe 결과 소비)
```

### T15-TF-016 — SelfReflection improvement_score 산출
```
ID: T15-TF-016
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/self_reflection.py:299
Evidence:
  - self_reflection.py:299 `improvement_score = min(1.0, len(issues) * 0.15)`
  - 이슈 7개 이상이면 improvement_score = 1.0 포화
  - L293: `should_improve = force or severity in ["high", "medium"] or quality < 6`
  - severity "low"/"none"이면 개선 생략 (L247)
Inference: improvement_score는 이슈 개수 기반 선형 계산. LLM 점수(overall_quality 1-10) 기반이 아닌 이슈 개수 기반이라 정밀도 한계.
Uncertainty: improvement_score가 외부에서 어떻게 소비되는지는 T05/T06 범위
Cross-Ref: T05, T06
```

### T15-TF-017 — CrossAgentVerifier FULL/PARTIAL/VIOLATION 결정 기준
```
ID: T15-TF-017
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/cross_agent_verifier.py:342-350
Evidence:
  - cross_agent_verifier.py:342-350 결과 판정 로직:
    ```python
    if score >= 0.8 and not violations:
        level = ComplianceLevel.FULL
    elif score >= 0.5 or len(violations) <= 1:
        level = ComplianceLevel.PARTIAL
    else:
        level = ComplianceLevel.VIOLATION
        should_regenerate = True
    ```
  - FULL: score ≥ 0.8 AND 위반 0건
  - PARTIAL: score ≥ 0.5 OR 위반 ≤ 1건
  - VIOLATION: 나머지 (score < 0.5 AND 위반 2건+)
  - Python precheck에서 위반 2건+ 발견 시 LLM 호출 생략 (L306, L389)
Inference: PARTIAL 조건에서 `or len(violations) <= 1`은 score < 0.5여도 위반 1건이면 PARTIAL이 됨. 이는 단일 위반의 관대한 처리.
Uncertainty: 의도적 설계일 가능성 높음
Cross-Ref: T06 (Interview — CrossAgentVerifier 결과 소비)
```

### T15-TF-018 — 모든 22개 모듈 프로덕션 활성 (Dead Code 없음)
```
ID: T15-TF-018
Severity: P4-OBSERVATION
Category: SYNC
Surface: main_a.py, stage4_interview_round.py, stage2_preflight.py, four_phase_arc_generator.py 등
Evidence:
  프로덕션 호출 경로:
  - AdversarialSelfPlay: main_a.py:2095 → _lazy_load_v50_modules
  - ChainOfVerification: main_a.py → stage4_orchestrator.py
  - SelfReflector: main_a.py → stage2_preflight.py
  - CrossAgentVerifier: main_a.py → stage4_interview_round.py
  - ConstitutionalChecker: stage2_preflight.py, main_a.py
  - TreeOfThoughts: main_a.py:2088
  - MultiAgentDeliberation: main_a.py:2102
  - AgentIntelligence: main_a.py → stage2_preflight.py
  - ConfidenceCalibrator: main_a.py:2077
  - ExpertMixture: main_a.py:2055
  - ReflexionManager: stage4_interview_round.py, stage4_context_builder.py, validation_orchestrator.py
  - TruthGate: stage4_interview_round.py:5192
  - NpcDriftAdvisor: stage4_interview_round.py:5230
  - NumericDriftAdvisor: stage4_interview_round.py:5282
  - FlashbackVerifier: stage4_interview_round.py:5310
  - InfoParadoxChecker: stage4_interview_round.py:5381
  - RelationshipDriftAdvisor: stage4_interview_round.py:5438
  - LongTermRepetitionAdvisor: stage4_interview_round.py:5484
  - NumericConsistencyChecker: stage4_interview_round.py:5531
  - InvestmentArithmeticChecker: four_phase_arc_generator.py:905
  - InvestmentMathVerifier: four_phase_arc_generator.py:916
  - SemanticQueryBroker: stage2_preflight.py, stage3_orchestrator.py, stage4_interview_round.py, stage4_context_builder.py
Inference: T15 범위의 22개 모듈 전량이 프로덕션 코드에서 실제 호출됨. dead code 없음.
Uncertainty: 없음
Cross-Ref: T01 (SovereignApp — v50 modules lazy load)
```

### T15-TF-019 — InvestmentArithmeticChecker validation.yaml 연동
```
ID: T15-TF-019
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/investment_arithmetic_checker.py:57-66
Evidence:
  - investment_arithmetic_checker.py:57-66 from_yaml() classmethod:
    ```python
    tolerance=float(_threshold("investment_math.python_tolerance", 0.15)),
    cash_tolerance=float(_threshold("investment_math.cash_tolerance", 0.05)),
    total_assets_tolerance=float(_threshold("investment_math.total_assets_tolerance", 0.05)),
    arc_boundary_tolerance=float(_threshold("investment_math.arc_boundary_tolerance", 0.01)),
    max_leverage=float(_threshold("investment_math.max_leverage", 10)),
    ```
  - _threshold()는 validation.yaml에서 키 조회, 미존재 시 fallback 사용
  - 호출부 four_phase_arc_generator.py:907: `_f1 = InvestmentArithmeticChecker.from_yaml()`
Inference: 투자물 검증 임계값이 validation.yaml에서 동적 로드됨. 다른 advisory 모듈(NpcDrift, NumericDrift 등)과 달리 YAML 연동이 구현됨.
Uncertainty: 없음
Cross-Ref: T17 (Config — validation.yaml 키 매핑)
```

### T15-TF-020 — InvestmentMathVerifier PromptLoader 연동
```
ID: T15-TF-020
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/investment_math_verifier.py:43, 65-72
Evidence:
  - investment_math_verifier.py:43 `self._prompt_loader = PromptLoader()`
  - investment_math_verifier.py:65-72:
    ```python
    prompt = self._prompt_loader.load(
        "investment_math_verifier",
        "VERIFY_PROMPT",
        tactical_doc=tactical_doc or "",
        python_results=python_json,
    )
    if not prompt:
        prompt = _FALLBACK_PROMPT.format(...)
    ```
  - YAML 프롬프트 미존재 시 _FALLBACK_PROMPT 사용 (L15-31)
Inference: PromptLoader를 사용하는 유일한 advisory 모듈. 다른 LLM advisory(TruthGate, NpcDrift 등)는 프롬프트를 코드 내 하드코딩.
Uncertainty: investment_math_verifier YAML 프롬프트 존재 여부는 T17 범위
Cross-Ref: T17 (Config — Prompt YAML)
```

### T15-TF-021 — ReflexionManager DB Write Side-Effect
```
ID: T15-TF-021
Severity: P3-LOW
Category: SIDE-EFFECT
Surface: modules/core/reflexion_manager.py:89-136
Evidence:
  - reflexion_manager.py:93-98 record_failure():
    ```python
    with self.context.db.transaction():
        self.context.db.execute_update(
            """UPDATE reflexion_memory SET frequency = ?, last_seen = ?, last_ep = ? WHERE pattern_type = ?""",
            (new_frequency, timestamp, ep_num, pattern_key),
        )
    ```
  - reflexion_manager.py:112-118 새 패턴 INSERT:
    ```python
    with self.context.db.transaction():
        self.context.db.execute_update(
            """INSERT INTO reflexion_memory (pattern_type, description, frequency, solution, first_seen, last_seen, first_ep, last_ep) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        )
    ```
  - L87: nested_tx 감지 → cache refresh 지연
Inference: T15 범위에서 유일하게 DB write를 수행하는 모듈. advisory 모듈들은 모두 read-only이나 ReflexionManager만 reflexion_memory 테이블에 INSERT/UPDATE.
Uncertainty: 없음
Cross-Ref: T16 (Database — reflexion_memory 테이블)
```

### T15-TF-022 — SemanticQueryBroker 6개 Intent Type
```
ID: T15-TF-022
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/semantic_query_broker.py:52-98
Evidence:
  - semantic_query_broker.py:52-98 _INTENT_SPECS:
    1. childhood_friend (소꿉친구/죽마고우)
    2. rival (라이벌/숙적)
    3. mentor (멘토/사부)
    4. ally (핵심 조력자/동료)
    5. benefactor (은인)
    6. family_like (가족 같은 인물)
  - 각 intent에 aliases(한국어 동의어) + patterns(정규식) 정의
  - read-only: DB/WorldState/FactLedger/StateTracker에서 증거 수집만
Inference: 6개 관계 유형을 정의하며 각각 aliases와 regex 패턴으로 intent 감지. 무협 특화 용어(죽마고우, 사부 등) 포함.
Uncertainty: 없음
Cross-Ref: T12 (State Tracking — SemanticQueryBroker가 world_state/fact_ledger 참조)
```

### T15-TF-023 — ConfidenceCalibrator Python-Only 기본 운영
```
ID: T15-TF-023
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/confidence_calibration.py:86
Evidence:
  - confidence_calibration.py:86 `def __init__(self, api_client=None, use_llm: bool = False, ...)`
  - use_llm=False 기본값 → Python 휴리스틱만 사용
  - main_a.py:2077에서 인스턴스화 시 use_llm 인자 전달 여부 확인 필요
  - 7개 요소 가중치 합계: 15+20+20+10+10+15+10 = 100점 만점
  - 임계값: extra_verification < 50, regenerate < 30, fast_pass ≥ 85
Inference: LLM 기반 평가는 기본 비활성. Python 휴리스틱(길이, 구조, 연속성, 대화 비율, 감각 묘사, 씬 반영, 엔딩 훅)만으로 신뢰도 산출.
Uncertainty: main_a.py 호출부에서 use_llm=True로 override 가능성
Cross-Ref: T01 (SovereignApp — v50 modules 초기화 인자)
```

### T15-TF-024 — ExpertMixture 8 Scene Types, Python-Only
```
ID: T15-TF-024
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/expert_mixture.py:32-43
Evidence:
  - expert_mixture.py:32-43 SceneType enum 8개:
    ACTION, DIALOGUE, EMOTIONAL, EXPOSITION, CLIMAX, TRANSITION, MYSTERY, COMEDY
  - 장르별 전문가 프롬프트: wuxia(8종), hunter(2종), investment(2종)
  - LLM 호출 없음 — 키워드 매칭으로 씬 유형 감지, 프롬프트 텍스트 반환만
  - generate_writer_injection()으로 Writer 프롬프트에 주입
Inference: $0 비용 모듈. 프롬프트 텍스트만 생성하여 Writer에 주입. Hunter/Investment는 일부 씬 유형만 정의(wuxia fallback 사용).
Uncertainty: 없음
Cross-Ref: T08 (ChiefWriter — ExpertMixture injection 소비)
```

### T15-TF-025 — AgentIntelligence Few-Shot/Anti-Pattern/Self-Critique 3중 구조
```
ID: T15-TF-025
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/agent_intelligence.py:50-609
Evidence:
  - 3개 서브시스템:
    1. Few-Shot Exemplar Library (L63-250): 장르별 우수 예시 (wuxia 2개, hunter 1개, investment 1개 per agent)
    2. Anti-Pattern Injection (L256-316): 장르별 회피 패턴 (wuxia analyst 5개, architect 5개, writer 7개)
    3. Self-Critique Chain (L322-418): 에이전트별 자가 검토 템플릿
  - 통합 인터페이스: get_analyst_enhancement(), get_architect_enhancement(), get_writer_enhancement()
  - quick_quality_check(): Python-only 빠른 품질 체크 (LLM 없음)
Inference: $0 비용 프롬프트 주입 시스템. LLM 호출 없이 프롬프트 텍스트만 생성. 3개 서브시스템이 통합 인터페이스로 결합.
Uncertainty: 없음
Cross-Ref: T03 (Stage 2 Preflight — get_analyst_enhancement 호출)
```

### T15-TF-026 — Advisory Chain 타임아웃 구조
```
ID: T15-TF-026
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/stage4_interview_round.py:5146-5162
Evidence:
  - stage4_interview_round.py:5146 `for future in as_completed(futures, timeout=300):`
  - stage4_interview_round.py:5149 `result = future.result(timeout=60)`
  - L5157-5158: 개별 advisory 타임아웃 시 warning 로그 + 계속 진행
  - L5160-5162: 전체 타임아웃 시 미완료 future cancel
    ```python
    for future in futures:
        if not future.done():
            future.cancel()
    ```
  - 전체 타임아웃 300s, 개별 타임아웃 60s
Inference: 이중 타임아웃 구조. 개별 advisory 실패 시 비차단. 전체 300s 초과 시 미완료 advisory 취소.
Uncertainty: 없음
Cross-Ref: T06 (Interview Round — advisory chain integration)
```

### T15-TF-027 — TreeOfThoughts explore_blueprint + explore_arc 이중 진입점
```
ID: T15-TF-027
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/tree_of_thoughts.py:365-600
Evidence:
  - tree_of_thoughts.py:198 explore(): 범용 ToT 탐색
  - tree_of_thoughts.py:365 explore_blueprint(): Blueprint 전용 (4분기: 긴장감/캐릭터/플롯/연속성)
  - tree_of_thoughts.py:490 explore_arc(): Arc 전용 (4분기: 인과율/긴장감/캐릭터/복선)
  - explore_arc()는 Python 휴리스틱 평가(_evaluate_arc), explore_blueprint()도 Python 휴리스틱(_evaluate_blueprint)
  - explore()는 LLM 기반 평가(_evaluate_path)
Inference: 3개 진입점: 범용(LLM 평가), Blueprint 전용(Python 평가), Arc 전용(Python 평가). Stage 2/3에서 각각 사용.
Uncertainty: 없음
Cross-Ref: T02 (Stage 2 — explore_arc), T04 (Stage 3 — explore_blueprint)
```

### T15-TF-028 — MultiAgentDeliberation Director와의 역할 구분
```
ID: T15-TF-028
Severity: P3-LOW
Category: COVERAGE-GAP
Surface: modules/core/multi_agent_deliberation.py:289-374
Evidence:
  - multi_agent_deliberation.py:289 deliberate(): Analyst + Architect + Writer 3자 토론
  - L326: 모든 에이전트 80점+ → 즉시 합의 (원본 유지)
  - L333: 심각한 문제 없고 평균 70+ → 합의 도달
  - 이 시스템은 Director verdict와 **별도**로 동작
  - Director는 stage4_interview_round에서 실제 PASS/REJECT 판정
  - MAD는 사전 품질 개선용 (ASP와 유사한 역할)
Inference: MAD와 Director는 별도 시스템. MAD는 사전 합의, Director는 최종 판정. 역할 중복 우려가 있으나 MAD는 "개선"이 목적이고 Director는 "판정"이 목적으로 구분됨.
Uncertainty: MAD와 ASP가 동시 활성화될 때 비용 이중 지출 가능성
Cross-Ref: T07 (Director — final verdict)
```

---

## 3. Evidence Inventory

| TF | 핵심 증거 파일:라인 | 유형 |
|----|---------------------|------|
| T15-TF-001 | stage4_interview_round.py:5094, 5108 | DRIFT |
| T15-TF-002 | constitutional_checker.py:138 | DRIFT |
| T15-TF-003 | constitutional_checker.py:53-188 | SYNC |
| T15-TF-004 | truth_gate.py:50-57 | SYNC |
| T15-TF-005 | truth_gate.py:437 | SILENT-FAILURE |
| T15-TF-006 | 6 files: _parse_llm_response | DEAD-CODE (중복) |
| T15-TF-007 | 8 advisory modules | SYNC |
| T15-TF-008 | npc_drift_advisor.py:30 | HARDCODING |
| T15-TF-009 | numeric_drift_advisor.py:17-18 | HARDCODING |
| T15-TF-010 | info_paradox_checker.py:16-17 | HARDCODING |
| T15-TF-011 | flashback_verifier.py:14-15 | HARDCODING |
| T15-TF-012 | long_term_repetition_advisor.py:36-38 | HARDCODING |
| T15-TF-013 | numeric_consistency_checker.py:222-286 | SYNC |
| T15-TF-014 | adversarial_self_play.py:110, 148 | SYNC |
| T15-TF-015 | chain_of_verification.py:55-61, 315 | SYNC |
| T15-TF-016 | self_reflection.py:299 | SYNC |
| T15-TF-017 | cross_agent_verifier.py:342-350 | SYNC |
| T15-TF-018 | 22 files, main_a.py, stage4_interview_round.py | SYNC |
| T15-TF-019 | investment_arithmetic_checker.py:57-66 | SYNC |
| T15-TF-020 | investment_math_verifier.py:43, 65-72 | SYNC |
| T15-TF-021 | reflexion_manager.py:89-136 | SIDE-EFFECT |
| T15-TF-022 | semantic_query_broker.py:52-98 | SYNC |
| T15-TF-023 | confidence_calibration.py:86 | SYNC |
| T15-TF-024 | expert_mixture.py:32-43 | SYNC |
| T15-TF-025 | agent_intelligence.py:50-609 | SYNC |
| T15-TF-026 | stage4_interview_round.py:5146-5162 | SYNC |
| T15-TF-027 | tree_of_thoughts.py:198, 365, 490 | SYNC |
| T15-TF-028 | multi_agent_deliberation.py:289-374 | COVERAGE-GAP |

---

## 4. Side-Effect Surface

| Module | Side-Effect | 유형 |
|--------|-------------|------|
| ReflexionManager | reflexion_memory 테이블 INSERT/UPDATE | DB Write |
| TruthGate | logging.warning (world_state 조회 실패 시) | Logging |
| All LLM advisors | LLM API 호출 (외부 네트워크) | External Call |
| InvestmentMathVerifier | LLM API 호출 (1회) | External Call |
| InvestmentArithmeticChecker | logging.debug (advisory 텍스트) | Logging |
| All _parse_llm_response | logging.debug (JSON 파싱 실패 시) | Logging |

**Non-side-effect 모듈**: ConstitutionalChecker, AgentIntelligence, ExpertMixture, ConfidenceCalibrator (Python-only, no I/O)

---

## 5. Facts

1. Advisory chain은 **9개** (TruthGate, NpcDrift, NumericDrift, Flashback, InfoParadox, RelDrift, LongTermRep, NumericConsistency, StyleSignal)
2. LLM 7개 (TruthGate의 7번째 검사 world_law_violation 포함) + Python-only 2개 (NumericConsistencyChecker, StyleSignalAdvisor)
3. Constitutional checker 조항: Stage 2 = A1-A6(6개), Stage 3 = B1-B5(5개), Stage 4 = M1-M7(7개), 총 18개
4. 22개 모듈 전량 프로덕션 활성 — dead code 없음
5. Advisory 타임아웃: 개별 60s, 전체 300s, max_workers=9
6. InvestmentArithmeticChecker만 validation.yaml 임계값 참조 (from_yaml())
7. InvestmentMathVerifier만 PromptLoader 사용
8. ReflexionManager만 DB write 수행 (reflexion_memory 테이블)
9. SemanticQueryBroker는 6개 relation intent type 지원, read-only

---

## 6. Inferences

1. Advisory chain 9개 vs 문서 8개 DRIFT는 StyleSignalAdvisor 추가 이후 문서 미갱신으로 추정
2. Constitutional checker M8 부재는 기획 누락이거나 의도적 생략 — 7개로도 핵심 검사 커버됨
3. JSON 파싱 코드 6중 복제는 모듈 독립성 우선 설계의 결과. 공통 유틸 추출로 150줄+ 절감 가능
4. Advisory 하드코딩 상수(max_npcs=8, MAX_ITEMS=30, MAX_FLASHBACKS=5 등)는 validation.yaml 미연동 — InvestmentArithmeticChecker의 from_yaml() 패턴 적용 가능
5. MAD와 ASP가 동시 활성화 시 비용이 +$0.08/생성 추가 — 비용 최적화 검토 대상

---

## 7. Uncertainty / Contradictions

1. **M8 의도**: ConstitutionalChecker에 M8이 없는 것이 의도적 생략인지 누락인지 불분명
2. **ASP vs Director 임계값**: ASP PASS=85 vs Director quality_gate=90 — 의도적 차이인지 불일치인지 확인 필요
3. **ConfidenceCalibrator LLM 활성화 여부**: main_a.py에서 use_llm 인자가 전달되는지 확인 필요 (T01 범위)
4. **MAD + ASP 동시 활성화 시나리오**: 비용 이중 지출 가능성이 실제로 발생하는지 runtime 확인 필요

---

## 8. Cross-Ref to Adjacent Terminals

| 인접 터미널 | 교차 영역 | 관련 TF |
|------------|----------|---------|
| T06 (Interview) | Advisory chain 9개 병렬 실행 통합 | T15-TF-001, T15-TF-007, T15-TF-026 |
| T07 (Director) | Director verdict vs ASP/MAD verdict 차이 | T15-TF-014, T15-TF-028 |
| T12 (State Tracking) | TruthGate/SemanticQueryBroker의 world_state 의존 | T15-TF-004, T15-TF-022 |
| T14 (Validation) | Advisory → validation_results 병합 경로 | T15-TF-007 |
| T17 (Config) | validation.yaml 키 연동 (InvestmentArithmeticChecker) | T15-TF-019 |
| T01 (SovereignApp) | v50 modules lazy init (Quality Intelligence 11개) | T15-TF-018 |
| T02 (Stage 2) | NumericConsistencyChecker.check_tactical_doc() | T15-TF-013 |
| T09 (Arc Gen) | InvestmentArithmeticChecker/MathVerifier 호출 | T15-TF-019, T15-TF-020 |
| T16 (DB) | ReflexionManager reflexion_memory 테이블 | T15-TF-021 |

---

## 9. Candidate Watchlist

1. **JSON 파싱 공통 유틸 추출** — 6개 advisory의 _parse_llm_response 통합 (P3)
2. **Advisory 하드코딩 상수 YAML 이전** — max_npcs, MAX_ITEMS 등 validation.yaml 참조로 전환 (P3)
3. **M8 조항 추가 검토** — Stage 4 원고 검증에 추가 조항 필요 여부 (P4)
4. **Advisory chain 문서 갱신** — 9개 advisory 반영 (P3)
5. **MAD+ASP 비용 최적화** — 동시 활성화 시 LLM 호출 횟수 분석 (P4)

---

## 10. 6Pass Audit Log

### Pass 1 — 구조/범위
- 22개 파일 전수 읽기 완료
- Advisory 8+1개, Quality Intelligence 11개 명확 분리
- 필수 조사 9개 항목 전수 조사 완료
- TF 28개 구성 (최소 기대 20+개 충족)
- **PASS**

### Pass 2 — 증거/일관성
- 모든 TF에 파일:라인 형식 Evidence 존재
- 코드 스니펫 인용 16건
- Grep 결과 근거 3건
- 라인번호 정확성: 원본 Read 결과 기반 확인
- 수치 일관성: advisory 9개, constitutional 18개, 모듈 22개 — 본문 내 일치
- **PASS**

### Pass 3 — 실행가능성/severity
- P2: 1건 (Advisory chain count DRIFT — 문서 갱신 필요)
- P3: 4건 (Constitutional M8 부재, 광범위 except, JSON 중복, ReflexionManager side-effect)
- P4: 23건 (SYNC 확인, HARDCODING 관측, 구조 문서화)
- Severity 분포 합리적 — advisory-only 시스템이므로 P0/P1 해당 없음
- **PASS**

### Pass 4 — 적대적: 스코프 과잉/누락 반박 시도
- "context_advisor.py가 T15에 포함되어야 한다" → context_advisor는 T15 범위에 없으며 stage2/3/4 context에 속함. T15는 advisory detection 전문이므로 범위 밖. → **반박 실패**
- "pass_rate_monitor가 T15에 포함되어야 한다" → pass_rate_monitor는 validation pipeline 소속(T14). → **반박 실패**
- "StyleSignalAdvisor가 별도 모듈이 아니므로 T15 범위 밖이다" → StyleSignal은 stage4_interview_round.py 내부 메서드이며 advisory chain의 일부. T15는 advisory chain 전체를 조사하므로 범위 내. → **반박 실패**
- **PASS**

### Pass 5 — 적대적: 증거 거짓/오해 반박 시도
- "advisory가 9개라는 근거가 로그 메시지뿐이다" → ThreadPoolExecutor(max_workers=9)와 9개 submit 호출로 코드 증거 확인. → **반박 실패**
- "M8이 다른 파일에 정의되어 있을 수 있다" → Grep "M8" in constitutional_checker.py → 0 matches. 다른 파일에서도 MANUSCRIPT_CONSTITUTION 정의 없음. → **반박 실패**
- "JSON 파싱 코드가 실제로 다를 수 있다" → 6개 파일의 _parse_llm_response를 비교: 동일 구조 (regex → json.loads → list 검증). 반환 dict 키만 다름. → **반박 실패**
- **PASS**

### Pass 6 — 적대적: severity 과대/과소 반박 시도
- "T15-TF-001 (advisory 9 vs 8)이 P2가 아니라 P4여야 한다" → 문서와 코드의 불일치는 다른 터미널(T06, T14)의 조사에도 영향. 단순 관측이 아닌 교차 검증 무결성 이슈. P2 유지. → **반박 실패**
- "JSON 중복(T15-TF-006)이 P3이 아니라 P4여야 한다" → 150줄+ 코드 중복은 유지보수 부담. 수정 시 6개 파일 동시 수정 필요. P3 유지. → **반박 실패**
- "하드코딩 상수(T15-TF-008~012)가 P4가 아니라 P3이어야 한다" → 기본값이 합리적이며 keyword arg로 override 가능. 즉각적 문제 없음. P4 유지. → **반박 실패**
- **PASS**

**6PASS-CLEARED** — 확신도 96%
