# Stage3 Runtime Quality — 10-Terminal Parallel Investigation Order

Date: 2026-04-14
Status: order (execution pending)
Type: system-order / parallel-investigation
Canonical Path: `docs/2026-04-14/stage3-runtime-quality-10terminal-parallel-investigation-order.md`
Prior Art: `docs/2026-04-13/s2-s3-s4-runtime-improvement-10-terminal-parallel-investigation-order.md`

---

## 0. Investigation Intent

Stage3의 런타임 품질을 3대 축으로 해부한다.

**3대 축:**

| 축 | 핵심 질문 |
|---|---|
| A. Producer Stupidity | 왜 S3 생산자(ensemble generator)는 첫 시도에서 품질이 낮은가? 어디에서 정보를 잃는가? |
| B. Director Adequacy | Director의 판정/디렉팅은 정확한가? 오판(false positive/negative)은 어디서 발생하는가? |
| C. Runtime Pass Dynamics | "처음부터 잘 통과하기" vs "잘 수정해서 통과하기" — retry loop의 실제 효과는 무엇인가? |

**범위:** `Stage3Orchestrator` → `ThreePhaseBlueprint.generate()` → `Director.select_and_judge_ensemble()` → retry/feedback loop → `_handle_success` / `_handle_failure` 전체 경로.

**범위 밖:** Stage2 Arc 생성 품질, Stage4 원고 생성 품질 (S3가 넘기는 인터페이스 품질만 본다).

---

## 1. Terminal Assignment

총 10개 터미널. 각 터미널은 **완전 독립 조사 + 적대적 감리 3회**를 수행한다.

### Axis A — Producer Stupidity (Terminal 1-4)

#### Terminal 1: Producer Initial Prompt Forensics (재진입)

**질문:** Producer(ensemble generator)에게 전달되는 프롬프트가 실제로 필요한 정보를 다 담고 있는가?

**조사 대상:**
- `config/prompts/ensemble.yaml` — 프롬프트 템플릿 원문
- `modules/domain/agents/blueprint_ensemble.py` — `generate_ensemble()` 메서드에서 프롬프트 조립 로직
- `modules/domain/agents/three_phase_blueprint_runtime.py` — `_run_retry_cycle()` → phase2 호출 시 넘기는 인자
- `modules/core/stage3_orchestrator.py` — `_build_stage3_blueprint_semantic_bundle()`, `_run_stage3_blueprint_generation_handoff()` 에서의 context 조립

**핵심 검증 항목:**
1. Arc tactical_doc → producer prompt까지 정보 유실/절삭 지점 식별
2. prev_blueprint / prev_manuscripts_text → 연속성 컨텍스트 적재율
3. entity_registry → producer prompt 내 활용 방식과 정보 밀도
4. semantic_context (SemanticQueryBroker) → 실제 주입량 vs 예산 대비 활용률
5. state_tracker HUD → producer가 받는 상태 정보의 충분성
6. protagonist_config → 주인공 설정이 producer에게 얼마나 구체적으로 전달되는가

**적대적 감리 포인트:**
- "정보가 프롬프트에 들어 있다"와 "LLM이 그 정보를 실제 활용하기 쉬운 형태로 들어 있다"는 다르다
- 프롬프트 길이 vs 핵심 정보 밀도 비율 측정
- 동일 정보의 중복 전달 vs 핵심 정보의 누락 비교

**산출물:** `t1-producer-prompt-forensics.md` + `t1-evidence.json`

---

#### Terminal 2: Producer Cheap-Admission Gate Effectiveness

**질문:** Cheap-admission gate가 실제로 나쁜 후보를 걸러내고 있는가, 아니면 허수인가?

**조사 대상:**
- `modules/domain/agents/blueprint_ensemble.py` — `_sanitize_and_validate_candidate()`, `_detect_unauthorized_tactical_intrusion()`, cheap-admission 관련 전체 로직
- `modules/core/response_schemas.py` — `BLUEPRINT_SCHEMA` 정의
- `modules/domain/agents/unified_blueprint_validator.py` — validator 대비 cheap-admission의 중복/갭

**핵심 검증 항목:**
1. cheap-admission이 reject하는 후보 유형 목록 vs validator가 reject하는 유형 목록 → 갭 분석
2. `opening_transition`, `protagonist_state`, `key_events` 검증의 실효성
3. schema required 필드와 cheap-admission 필드의 불일치 (04-13 audit에서 P2로 발견됨 — 현재 상태 재확인)
4. tactical_intrusion 탐지의 false negative율 (backstory authority 우회 04-13 발견 재확인)
5. cheap-admission 통과 후 validator에서 reject되는 비율 = cheap-admission의 진짜 실효성

**적대적 감리 포인트:**
- cheap-admission이 "통과시키기 쉬운 것만 걸러내고 있지 않은지" (쉬운 문제만 잡고 어려운 문제는 통과시킴)
- admission gate 우회 가능한 최소 공격 벡터 3개 구성

**산출물:** `t2-cheap-admission-effectiveness.md` + `t2-evidence.json`

---

#### Terminal 3: Producer Context Packet Quality

**질문:** Producer가 받는 context packet(Arc/Bible/State/Style)의 품질이 blueprint 품질에 얼마나 영향을 주는가?

**조사 대상:**
- `modules/core/stage3_orchestrator.py` — `_build_stage3_blueprint_semantic_bundle()` 전체
- `modules/core/context_advisor.py` — `build_context_observation()`, `build_context_budget_ledger()`
- `modules/core/semantic_query_broker.py` — SemanticQueryBroker의 실제 context 수집 로직
- `modules/domain/agents/chief_writer_context_packets.py` — CW context packet 참고 (S4 대비 S3의 context 차이)
- `modules/core/project_support.py` — `build_style_guide_summary()`, `resolve_project_pov_contract()`

**핵심 검증 항목:**
1. context budget ledger에서 실제 배분 비율 — Arc tactical이 몇 %, entity가 몇 %, semantic이 몇 %
2. 총 context 크기 vs LLM context window 활용률
3. prev_manuscripts_text의 품질 — 요약인가 원문인가, 얼마나 recent인가
4. state_tracker HUD의 정보 밀도 — 무엇이 빠져 있는가
5. pov_contract, style_guide_summary → producer가 이것을 어떻게 활용하는가 (활용 불가 형태로 전달되고 있지 않은가)

**적대적 감리 포인트:**
- context가 풍부해도 producer가 활용 못 하면 무의미 — 활용 증거 vs 무시 증거 구분
- context 과적재로 인한 핵심 정보 매몰 가능성

**산출물:** `t3-context-packet-quality.md` + `t3-evidence.json`

---

#### Terminal 4: Ensemble Candidate Diversity & Selection Quality

**질문:** 3개 앙상블 후보가 실제로 다양한가, 아니면 비슷한 쓰레기 3개인가?

**조사 대상:**
- `modules/domain/agents/blueprint_ensemble.py` — `generate_ensemble()` 메서드
- `modules/domain/agents/three_phase_blueprint_runtime.py` — phase2 전체 로직
- `modules/domain/agents/director_ensemble.py` — `compare_and_select_blueprint()`, `select_and_judge_ensemble()`
- `modules/core/adversarial_self_play.py` — ASP가 후보 개선에 기여하는 정도

**핵심 검증 항목:**
1. 3개 후보의 구조적 다양성 — scene 수, 전략, opening_transition type 분포
2. 후보 간 실질적 차이 vs 표면적 차이 (같은 뼈대에 살만 다른 경우)
3. Director 선택 시 후보 간 점수 차이 분포 — 유의미한 차이가 있는가
4. adversarial_self_play가 실제로 호출되는 조건과 개선 효과
5. "best of 3"이 실제로 "best of 1"보다 유의미하게 나은 결과를 내는지

**적대적 감리 포인트:**
- 후보 3개가 같은 프롬프트에서 나오므로 본질적으로 비슷할 수밖에 없다는 구조적 한계
- 선택 과정이 "제일 나은 것"을 고르는 것인지 "제일 덜 나쁜 것"을 고르는 것인지

**산출물:** `t4-ensemble-diversity-selection.md` + `t4-evidence.json`

---

### Axis B — Director Adequacy (Terminal 5-7)

#### Terminal 5: Director Scoring & Threshold Accuracy

**질문:** Director의 점수 산정과 PASS/REJECT threshold가 실제 품질과 정합하는가?

**조사 대상:**
- `modules/domain/agents/director_grading.py` — `DirectorGradingSystem` 전체
- `modules/domain/agents/director_auditor.py` — `DirectorQualityAuditor.audit_manuscript()` (blueprint 감사 참고)
- `modules/validation/scoring_validator.py` — validator 점수 산정 로직
- `modules/validation/threshold_helper.py` — `_threshold()` YAML 기반 임계값
- `config/validation.yaml` — 실제 임계값 값

**핵심 검증 항목:**
1. `QUALITY_WEIGHTS` 배분 (structure 0.15, prose 0.15, consistency 0.25, engagement 0.15, commercial 0.20, satisfaction 0.10) — 이 비율이 "좋은 blueprint"의 실제 기여도와 일치하는가
2. 적응형 threshold (`get_adaptive_threshold()`) — arc position, genre, retry count에 따른 조정이 합리적인가
3. retry_count >= 3 → 기준 10점 하향 — 이것이 "포기 통과"를 유발하지 않는가
4. `apply_adaptive_decision()` — REJECT을 CONDITIONAL_PASS로 뒤집는 조건이 과도하지 않은가
5. `_extract_category_score()` — validation breakdown에서 category로 매핑하는 로직의 정확성

**적대적 감리 포인트:**
- threshold가 3회 재시도 후 10점 낮아지면, 처음부터 3회 실패를 유도하는 것이 통과 전략이 될 수 있는가
- 점수 60점(default pass)이 실제로 "게재 가능 수준"인가

**산출물:** `t5-director-scoring-threshold.md` + `t5-evidence.json`

---

#### Terminal 6: Director Ensemble Selection Judgment

**질문:** Director가 3개 후보 중 "최선"을 고르는 판정이 실제로 정확한가?

**조사 대상:**
- `modules/domain/agents/director_ensemble.py` — `DirectorEnsembleSelector` 전체 (1065줄 클래스)
  - `select_and_judge_ensemble()` — 메인 선택 로직
  - `compare_and_select_blueprint()` — Blueprint 비교 선택
  - `quick_judge_single()` — 단일 후보 판정
- `modules/domain/agents/director_prompts.py` — `ENSEMBLE_SELECTION_PROMPT`
- `modules/domain/agents/director.py` — Director facade의 위임 구조

**핵심 검증 항목:**
1. ENSEMBLE_SELECTION_PROMPT의 판정 기준이 명시적이고 일관적인가
2. LLM이 반환하는 선택 이유(selection_reason)가 실제 blueprint 품질과 상관하는가
3. prev_manuscripts_text, story_context가 선택 판정에 유의미하게 반영되는가
4. `mandatory_context`, `decision_core`, `candidate_evidence`, `reference_appendix` 패킹 — Director에게 과부하를 주고 있지 않은가
5. Director가 동점 또는 근접 점수에서 어떤 기준으로 tie-break하는가

**적대적 감리 포인트:**
- Director 판정 프롬프트가 너무 길어서 핵심 판정 기준이 묻히지 않는가
- 3개 후보가 비슷할 때 Director가 무작위에 가까운 선택을 하는가

**산출물:** `t6-director-ensemble-judgment.md` + `t6-evidence.json`

---

#### Terminal 7: Director Continuity & Validation Overlap

**질문:** Director의 연속성 검증과 Validator의 검증이 이중 작업인가, 보완적인가?

**조사 대상:**
- `modules/domain/agents/director_continuity.py` — `DirectorContinuityValidator` 전체
  - `check_manuscript_history_conflicts()` — 원고 역사 충돌
  - `check_blueprint_continuity_with_cache()` — blueprint 연속성
  - `validate_entity_consistency()` — entity 일관성
  - `_validate_blueprint_completeness_v60()` — blueprint 완전성
- `modules/domain/agents/unified_blueprint_validator.py` — validator 측 연속성 검증
- `modules/core/pre_director_checklist.py` — Director 전 사전 체크리스트
- `modules/core/cross_agent_verifier.py` — 교차 검증 로직

**핵심 검증 항목:**
1. Director 연속성 검증 vs Validator 연속성 검증 — 겹치는 영역 비율
2. Director-only 검증 항목 (Validator가 안 하는 것) 목록
3. Validator-only 검증 항목 (Director가 안 하는 것) 목록
4. 두 검증이 동일 항목에 대해 다른 판정을 내리는 경우가 있는가
5. pre_director_checklist가 실제로 Director 부담을 줄이는 효과

**적대적 감리 포인트:**
- 이중 검증이 "안전"이 아니라 "비용 낭비 + 판정 모순"을 유발할 수 있다
- 어느 한쪽만 통과하면 되는 것인지, 둘 다 통과해야 하는 것인지 계약이 명확한가

**산출물:** `t7-director-continuity-overlap.md` + `t7-evidence.json`

---

### Axis C — Runtime Pass Dynamics (Terminal 8-10)

#### Terminal 8: First-Pass Success Rate Root Cause

**질문:** 첫 시도(retry=0)에서 PASS되는 비율은 얼마이고, 첫 시도 실패의 근본 원인 패턴은 무엇인가?

**조사 대상:**
- `modules/domain/agents/three_phase_blueprint_runtime.py` — `generate()` 메인 루프
  - `_run_retry_cycle()` — retry=0 시점의 로직
  - `_bootstrap_runtime_context()` — 초기 설정
- `modules/core/stage3_orchestrator.py` — pipeline_result의 `attempt_num` 분포
- 기존 live run 증거:
  - `docs/temp/stage3_run_output.txt`
  - `docs/2026-04-13/stage3-live-run-*` 관련 문서
  - DB `stage_attempts` 테이블 (가능하면)

**핵심 검증 항목:**
1. retry=0 PASS율 통계 (live run 증거 기반)
2. retry=0 REJECT 시 가장 빈번한 reject_reason 카테고리 Top 5
3. retry=0 실패 후 retry=1에서 같은 문제로 다시 실패하는 비율
4. 첫 시도 실패의 원인이 producer(생산 품질)인가, director(판정 기준 과잉)인가, validator(검증 오탐)인가
5. ep_num별 first-pass 성공률 차이 — 초반 에피소드가 더 쉬운가 어려운가

**적대적 감리 포인트:**
- first-pass 실패가 구조적이라면, retry loop 자체가 "실패를 전제로 한 설계"가 아닌가
- first-pass 성공률이 충분히 높다면, retry loop의 비용 정당성이 약해진다

**산출물:** `t8-first-pass-root-cause.md` + `t8-evidence.json`

---

#### Terminal 9: Retry Feedback Loop Effectiveness

**질문:** REJECT 후 재시도에서 피드백이 실제로 품질을 개선시키는가?

**조사 대상:**
- `modules/domain/agents/three_phase_blueprint_runtime.py`:
  - `_ThreePhaseRetryState` — retry 상태 누적 방식
  - `_Stage3RepairRouter.build_retry_material()` — 수리 재료 조립
  - `_Stage3RepairRouter.decide_phase2_retry()` — inplace vs full 결정
  - `_Stage3RepairRouter.decide_pass_with_fix()` — PASS_WITH_FIX 처리
  - `_build_stage3_retry_plateau_reasons()` — plateau 탐지
- `modules/core/feedback_system.py` — `FeedbackSystem` 전체
  - `quantify_reject_feedback()` — reject 피드백 정량화
  - `classify_rejection_feedback()` — 피드백 분류
  - `simplify_prompt_for_retry()` — retry용 프롬프트 단순화
- `modules/domain/agents/director_grading.py` — `generate_revision_guide_v59()` — 수정 가이드

**핵심 검증 항목:**
1. retry 피드백에 포함되는 정보: reject_reason, fix_scope, fix_pack, repair_contract, scope_authority
2. 이 피드백이 producer 프롬프트에 어떻게 주입되는가 — `external_feedback` → prompt injection 경로
3. retry=N에서 retry=N+1로 갈 때 실제 점수 변화 패턴 (상승/정체/하락)
4. inplace patch vs full regeneration — 어느 쪽이 실제로 개선 효과가 큰가
5. plateau 탐지(`inplace_reject_streak >= 2`, `repeated_reject_score_streak >= 2`)가 조기 탈출에 기여하는가
6. `PASS_WITH_FIX` → 수정 루프 → 실제로 fix가 적용되는 비율

**적대적 감리 포인트:**
- retry가 "같은 실수를 반복하면서 threshold만 낮아지기를 기다리는" 패턴이 아닌가
- 피드백이 너무 추상적이어서 producer가 구체적으로 무엇을 고쳐야 하는지 모르는 경우
- inplace patch가 "문제를 국소적으로 봉합"하고 전체 구조는 개선하지 못하는 경우

**산출물:** `t9-retry-feedback-effectiveness.md` + `t9-evidence.json`

---

#### Terminal 10: PASS_WITH_FIX / CONDITIONAL_PASS Actual Outcome

**질문:** "조건부 통과"한 blueprint의 실제 다운스트림 품질은 어떤가?

**조사 대상:**
- `modules/core/stage3_orchestrator.py` — `_handle_success()` 에서 `PASS_WITH_FIX`, `PASS_WITH_WARNING` 처리
- `modules/domain/agents/director_grading.py` — `apply_adaptive_decision()` → `CONDITIONAL_PASS` 변환
- `modules/domain/agents/three_phase_blueprint_runtime.py` — `decide_pass_with_fix()` 라우팅
- `modules/domain/agents/stage3_blueprint_patch_ir.py` — blueprint patch IR
- 다운스트림 영향: Stage4가 이 blueprint를 사용할 때의 품질 (인터페이스 관점)

**핵심 검증 항목:**
1. PASS_WITH_FIX로 통과한 blueprint의 fix가 실제로 적용된 비율
2. CONDITIONAL_PASS(adaptive threshold 완화)로 통과한 blueprint의 실제 점수 분포
3. 조건부 통과 blueprint → Stage4 원고 생성 시 품질 차이 (clean PASS 대비)
4. `revision_required=True`로 마킹된 blueprint에 대한 후속 처리가 실제로 존재하는가
5. quality_risk=True, quality_gate_failed=True 플래그의 다운스트림 활용도
6. blueprint에 annotate되는 메타데이터(`_stage3_observability`, `pov_contract` 등)의 Stage4 활용도

**적대적 감리 포인트:**
- "조건부 통과"가 사실상 "포기 통과"와 구분되지 않는 경우
- PASS_WITH_FIX의 fix가 never applied이면 사실상 PASS(무조건 통과)
- adaptive threshold 완화가 "품질 기준을 유지한다"는 시스템 철학과 모순

**산출물:** `t10-conditional-pass-outcome.md` + `t10-evidence.json`

---

## 2. Per-Terminal Execution Protocol

모든 터미널은 아래 프로토콜을 **동일하게** 적용한다.

### 2.1 격리 원칙

- 각 터미널은 자신의 조사 범위만 조사한다.
- 다른 터미널의 산출물을 참조하지 않는다 (노이즈 차단).
- 코드 수정은 절대 금지 — 읽기 전용 조사만.
- 산출물 파일명은 `t{N}-*.md`, `t{N}-evidence.json`으로 통일.

### 2.2 적대적 감리 3회 (Adversarial Audit x3)

각 터미널은 조사 완료 후 **반드시 적대적 감리 3회**를 수행한다.

| 회차 | 역할 | 핵심 질문 |
|---|---|---|
| 1회 (자기 검증) | 조사자가 자기 결론에 반박 | "내 결론의 가장 약한 고리는 어디인가? 반대 증거를 찾아라." |
| 2회 (악의적 개발자) | 악의적 개발자 시점 | "이 시스템의 약점을 악용해 quality gate를 우회하려면 어떻게 하겠는가?" |
| 3회 (운영자 시점) | 실제 운영자 시점 | "이 조사 결과대로라면 운영자가 즉시 해야 할 행동과 하면 안 되는 행동은 무엇인가?" |

**감리 결과 기록 형식:**

```markdown
## Adversarial Audit Round {N}

### Perspective: {자기 검증 / 악의적 개발자 / 운영자}

**Challenge:** {반박/공격/행동 질문}

**Finding:** {감리 결과}

**Confidence Adjustment:** {감리 후 원래 결론의 확신도 변경 여부}
- Before: {N}%
- After: {N}%
- Reason: {변경 사유}
```

### 2.3 산출물 구조

각 터미널의 `.md` 산출물은 아래 구조를 따른다:

```
# T{N}: {Title}
Date: 2026-04-14
Terminal: {N}/10
Axis: {A|B|C} — {Producer Stupidity|Director Adequacy|Runtime Pass Dynamics}
Status: final

## 1. Investigation Question
## 2. Scope & Files Examined
## 3. Findings (numbered)
## 4. Adversarial Audit Round 1 (자기 검증)
## 5. Adversarial Audit Round 2 (악의적 개발자)
## 6. Adversarial Audit Round 3 (운영자)
## 7. Final Verdict (감리 후 최종)
   - Confidence: {N}%
   - Key Takeaway: {1문장}
   - Recommended Action: {구체적 행동}
## 8. Evidence References
```

### 2.4 Evidence JSON 구조

```json
{
  "terminal": N,
  "axis": "A|B|C",
  "date": "2026-04-14",
  "files_examined": ["path1", "path2"],
  "line_ranges": [{"file": "path", "start": N, "end": N, "finding": "description"}],
  "adversarial_rounds": [
    {"round": 1, "perspective": "self", "confidence_before": N, "confidence_after": N},
    {"round": 2, "perspective": "adversary", "confidence_before": N, "confidence_after": N},
    {"round": 3, "perspective": "operator", "confidence_before": N, "confidence_after": N}
  ],
  "verdict": "final one-line verdict",
  "recommended_priority": "P0|P1|P2|P3"
}
```

---

## 3. Terminal → File Quick Reference

| Terminal | Axis | 산출물 | Evidence |
|---|---|---|---|
| T1 | A | `t1-producer-prompt-forensics.md` | `t1-evidence.json` |
| T2 | A | `t2-cheap-admission-effectiveness.md` | `t2-evidence.json` |
| T3 | A | `t3-context-packet-quality.md` | `t3-evidence.json` |
| T4 | A | `t4-ensemble-diversity-selection.md` | `t4-evidence.json` |
| T5 | B | `t5-director-scoring-threshold.md` | `t5-evidence.json` |
| T6 | B | `t6-director-ensemble-judgment.md` | `t6-evidence.json` |
| T7 | B | `t7-director-continuity-overlap.md` | `t7-evidence.json` |
| T8 | C | `t8-first-pass-root-cause.md` | `t8-evidence.json` |
| T9 | C | `t9-retry-feedback-effectiveness.md` | `t9-evidence.json` |
| T10 | C | `t10-conditional-pass-outcome.md` | `t10-evidence.json` |

---

## 4. Post-Investigation Synthesis (조사 후)

10개 터미널 완료 후 별도 세션에서 synthesis:

1. **Cross-terminal correlation** — 터미널 간 발견의 교차 검증
2. **Root cause tree** — 3대 축의 근본 원인이 공유 뿌리를 갖는가
3. **Priority ranking** — P0/P1 항목만 추려서 action plan
4. **Cost-benefit** — 각 개선안의 구현 비용 vs 품질 개선 기대값

---

## 5. Execution Instructions (터미널 운영자용)

각 터미널을 여는 운영자는:

1. 이 오더 문서를 먼저 읽는다
2. 자신의 터미널 번호에 해당하는 섹션만 수행한다
3. 조사 대상 파일을 읽기 전용으로 조사한다 (코드 수정 금지)
4. 조사 완료 후 적대적 감리 3회를 수행한다
5. 산출물을 `docs/2026-04-14/` 에 저장한다
6. 3pass 감리 규칙을 적용한다 (AGENTS.md §Document Save Rule)
7. 확신도 95% 미만이면 추가 감리 반복 후 저장한다

**각 터미널 프롬프트 템플릿:**

```
시스템 오더다.
docs/2026-04-14/stage3-runtime-quality-10terminal-parallel-investigation-order.md 를 읽고,
Terminal {N}의 조사를 수행해라.

규칙:
- 코드 수정 금지, 읽기 전용 조사만
- 적대적 감리 3회 필수
- 산출물: docs/2026-04-14/t{N}-*.md + t{N}-evidence.json
- 3pass 감리 후 확신도 95% 이상에서만 최종 저장
- 다른 터미널 산출물 참조 금지
```

---

## 6. Key Code Paths Quick Reference

조사 시 빠른 탐색을 위한 핵심 코드 경로:

| 모듈 | 파일 | 핵심 진입점 |
|---|---|---|
| Stage3 Orchestrator | `modules/core/stage3_orchestrator.py` | `stage_3_batch_blueprinting()`, `_process_single_episode()`, `_generate_blueprint()`, `_handle_success()`, `_handle_failure()` |
| Stage3 Context | `modules/core/stage3_context.py` | `Stage3Context` DI 컨텍스트 |
| Three Phase Runtime | `modules/domain/agents/three_phase_blueprint_runtime.py` | `generate()` 메인 루프, `_run_retry_cycle()`, retry state/repair router |
| Blueprint Ensemble | `modules/domain/agents/blueprint_ensemble.py` | `generate_ensemble()`, cheap-admission |
| Director Facade | `modules/domain/agents/director.py` | 위임 허브 |
| Director Ensemble | `modules/domain/agents/director_ensemble.py` | `DirectorEnsembleSelector.select_and_judge_ensemble()` |
| Director Grading | `modules/domain/agents/director_grading.py` | `DirectorGradingSystem`, adaptive threshold |
| Director Continuity | `modules/domain/agents/director_continuity.py` | `DirectorContinuityValidator` |
| Director Auditor | `modules/domain/agents/director_auditor.py` | `DirectorQualityAuditor` |
| Feedback System | `modules/core/feedback_system.py` | retry 피드백 생성 |
| Adversarial Self-Play | `modules/core/adversarial_self_play.py` | producer 자기 개선 |
| Validator | `modules/domain/agents/unified_blueprint_validator.py` | blueprint 검증 |
| Blueprint Patch IR | `modules/domain/agents/stage3_blueprint_patch_ir.py` | inplace patch |
| Scoring Validator | `modules/validation/scoring_validator.py` | 점수 산정 |
| Threshold Config | `config/validation.yaml` | 임계값 SSOT |
| Prompt Config | `config/prompts/ensemble.yaml` | producer 프롬프트 |
| Response Schema | `modules/core/response_schemas.py` | `BLUEPRINT_SCHEMA` |
| Context Advisor | `modules/core/context_advisor.py` | context 예산/관찰 |
| Semantic Broker | `modules/core/semantic_query_broker.py` | semantic context 수집 |
| HUD Utils | `modules/core/hud_utils.py` | state_tracker HUD 빌드 |
| Pre-Director | `modules/core/pre_director_checklist.py` | Director 전 체크리스트 |
| Cross-Agent Verifier | `modules/core/cross_agent_verifier.py` | 교차 검증 |

---

*End of Order*
