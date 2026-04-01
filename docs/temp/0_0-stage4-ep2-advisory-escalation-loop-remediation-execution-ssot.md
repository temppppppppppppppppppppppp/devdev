# 0_0 Stage4 ep2 Advisory Escalation Loop Remediation Execution SSOT

Date: 2026-04-01
Status: partially_realized (code landed, static validation closed; runtime closure pending)
Canonical Path: `docs/2026-04-01/0_0-stage4-ep2-advisory-escalation-loop-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage4-ep2-advisory-escalation-loop-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `094ee9b50cad33b1aec89ca4f097103ece5b1938`
- Baseline Dirty Summary: `dirty: canary runtime logs/db/artifacts active; ctxnorm_r1 stage4 attempt artifacts untracked; 2026-04-01 bounded-survey + closure audit docs modified`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `T1-T3 landed in live code; targeted py_compile/ruff/pytest/UTF-8 hygiene passed; runtime closure still pending`
Source Survey Docs:
- `docs/2026-04-01/0_0-stage4-ep2-advisory-escalation-loop-bounded-survey.md`
- `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-context-normalization-runtime-closure-audit.md`
- `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md`
Evidence Artifacts:
- `docs/2026-04-01/0_0-stage4-ep2-advisory-escalation-loop-evidence.json`
- `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-context-normalization-runtime-closure-evidence.json`
- `projects/canary_0_0_stage34_arc2_ctxnorm_r1/logs/session/ui_events.jsonl`
- `projects/canary_0_0_stage34_arc2_ctxnorm_r1/logs/artifacts/stage4/ep_0002/attempt_10/selected_before_fix__B.txt`
- `projects/0_0/drafts/ep_0001.txt`
Side-Effect Coverage: covered
Parent Lane: `0_0-stage2-stage3-stage4-readiness-remediation` (partial — Stage3 closure_candidate; Stage4 blocked)

## 1. Answer First

ep2 Stage4 loop의 직접 원인은 3점이며, 각각 독립적인 bounded patch로 해소된다.

1. **FlashbackVerifier LLM 프롬프트가 기기-유형 과추론을 허용한다.** ep1은 "차가운 금속 소재의 폴더폰"과 "휴대전화 화면의 통화 버튼"을 같은 문맥에서 쓴다 (`ep_0001.txt` L93-99). ep2도 "폴더폰"과 "휴대전화 화면의 종료 버튼"을 쓴다. FlashbackVerifier LLM은 "화면의 버튼"만으로 "스마트폰/터치스크린"을 추론해 MAJOR를 반복 발화시킨다. 프롬프트에 기기-유형 추론 방지 조항이 없다.

2. **strong advisory family 정보가 operator sink에 남지 않는다.** `_normalize_director_gate_semantics`의 escalation 경고(`stage4_interview_round.py` L2093, L2199)는 `logging.warning`만 호출하고 `ctx.ui.log`를 호출하지 않는다. 따라서 `ui_events.jsonl`에 어떤 family가 escalation을 일으켰는지 기록되지 않아, 사후 진단이 어렵다.

3. **post_select_conflict의 실제 충돌 내용이 operator sink에 남지 않는다.** `_execute_round_post_select_validation` (`stage4_interview_round.py` L4168)은 conflict 건수와 유형(continuity/history)만 `ctx.ui.log`에 남기고, 실제 conflict 문자열(`_post_select_conflicts` 리스트 원소)은 `director_feedback`에만 합류한다. final round에서 이 feedback은 다음 round가 없으므로 소멸한다.

이 3건은 모두 Stage4 advisory/finalize seam의 **정밀도 + 관측성** 문제이며, Stage2/3 context normalization 회귀가 아니다.

## 2. Hard Conclusions

### 2.1 FlashbackVerifier는 artifact truth가 아니라 detector inference를 우선시한다

`flashback_verifier.py` L135-143의 LLM 프롬프트는:
- "사실 관계가 틀린 회상만 지적하세요"
- 그 외 기기-유형 추론을 제한하는 조항 없음

결과: LLM이 "화면의 버튼" → "터치스크린" → "스마트폰"으로 3단 추론 → 폴더폰과 모순이라고 판정.

artifact truth (`ep_0001.txt` L93-99): 같은 단락에서 "폴더폰"과 "화면의 통화 버튼"을 함께 사용. 이는 폴더폰의 물리 LCD 화면과 버튼을 가리키는 것이지, 터치스크린을 의미하지 않는다.

### 2.2 strong advisory escalation은 REJECT 전환 시 family를 ui_events에 남기지 않는다

코드 경로:
1. `stage4_director_runtime.py` L1290: `advisory_summary["flashback"] = 1` → `owner._last_advisory_summary` 저장
2. `stage4_interview_round.py` L2080-2096: `_STRONG_ADVISORY_KEYS`에 `flashback` 포함 → `PASS → PASS_WITH_FIX` escalation → `logging.warning` 호출
3. `stage4_interview_round.py` L2159-2204: Lane2-G2b local fix contract 불충족 → `PASS_WITH_FIX → REJECT` 강등 → `logging.warning` 호출

2, 3 모두 `self.ctx.ui.log`를 호출하지 않는다. `_last_advisory_summary` dict는 `advisory_flags` 경유로 DB/JSONL에 들어가지만, 구조화된 `triggered_by` family 리스트가 ui_events 수준 operator observability에 노출되지 않는다.

### 2.3 post_select_conflict downgrade는 conflict body를 ui sink에 남기지 않는다

코드 경로:
1. `stage4_interview_round.py` L4159-4170: `_post_select_conflicts` 비어있지 않으면 `ctx.ui.log`에 건수+유형만 기록
2. L4195: `director_feedback += "\n" + "\n".join(_post_select_conflicts)` — conflict 본문을 feedback에 합류
3. L4206-4242: `previous_attempt` dict에 `conflict_contract`를 기록하지만, 이 dict는 다음 round 재시도용이지 operator audit 목적이 아니다
4. final round (max_rounds 도달) 시 다음 round가 없으므로 conflict body는 소멸한다

### 2.4 이 문제는 Stage2/3 context normalization 회귀가 아니다

- closure audit의 parent lane verdict = `partial` (Stage3 closure_candidate, Stage4 blocked)
- Stage4 block 원인 = advisory escalation loop (이 문서의 범위)
- Tranche D runtime coverage는 Stage3 완결, Stage4는 ep2 advisory loop에 의한 별도 차단

## 3. Scope

### Included

| File | Seam | Tranche |
|---|---|---|
| `modules/core/flashback_verifier.py` | LLM 프롬프트 정밀도 | T1 |
| `modules/core/stage4_interview_round.py` | strong advisory ui.log 추가 (L2083-2096, L2159-2204 영역) | T2 |
| `modules/core/stage4_interview_round.py` | post_select_conflict detail ui.log 추가 (L4159-4195 영역) | T3 |
| 관련 테스트 파일 | 신규 또는 기존 테스트 보강 | T1-T3 |

### Excluded

- `stage4_retry_runtime.py` — TF-PATCH-GATE / TF-4 로직 자체는 정상 작동; 과해석 advisory가 사라지면 escalation 연쇄도 사라짐
- `stage4_reject_runtime.py` — reject snapshot의 rationale elision은 관측성 개선과 별도 문제 (defer)
- `stage4_outcome_runtime.py` — pass/reject outcome governance 자체는 정상
- `stage4_director_runtime.py` — advisory_summary 조립 로직은 정상; 문제는 caller의 ui.log 미호출
- `director_ensemble.py` — Director LLM 판정 자체는 정상 (advisory를 올바르게 소비)
- Stage2/3 context normalization 코드
- `0_0` source project 파일
- config/YAML 파일

## 4. Non-Goals

- fix_pack 체계 전면 개편
- Stage4 전체 정책 리라이트
- TruthGate 전면 수정
- Stage4 global resume 선언
- broad Stage4 redesign
- Stage2/3 재개편
- fresh canary 실행 (이 문서에서)
- resolved 또는 resume-ready 선언

## 5. Pass 1. Inventory Summary

### 5.1 FlashbackVerifier 프롬프트 (T1)

Target: `flashback_verifier.py` L135-143 `_llm_check` 메서드 내 프롬프트 문자열

현재 프롬프트 구조:
```
"다음 원고의 회상/플래시백 장면이 과거 에피소드 맥락과 모순되는 부분을 찾아주세요.\n"
+ ms_note (원문 우선 참조 지침)
+ "서사적 의도가 있는 변형 ... 은 정상입니다.\n"
+ "사실 관계가 틀린 회상만 지적하세요.\n\n"
+ formatted (회상 구간 + 참조 컨텍스트)
+ ep_num
+ JSON 포맷 지침
```

누락된 precision clause:
- 같은 기기를 다른 단어로 묘사한 경우 (폴더폰 ↔ 휴대전화, 화면의 버튼 ↔ 액정 화면 등)는 기종 변경이 아님
- 물리 LCD 화면과 물리 버튼이 있는 구형 휴대전화도 "화면의 버튼"으로 서술될 수 있음
- 단어 수준 표현 차이만으로 물리 형태가 바뀌었다고 추론 금지

### 5.2 strong advisory escalation ui.log (T2)

Target: `stage4_interview_round.py` `_normalize_director_gate_semantics` 메서드

현재 logging 경로:
- L2093: `logging.warning("[Stage4Gate] strong advisory escalation: PASS → PASS_WITH_FIX (classes=%s)", ...)` — Python logger only
- L2151: `logging.warning("[Stage4Gate] PASS_WITH_FIX → REJECT: ...")` — Python logger only
- L2199: `logging.warning("[Stage4Gate] strong advisory escalation forced REJECT: ...")` — Python logger only

누락된 operator sink:
- 세 지점 모두 `self.ctx.ui.log(...)` 호출 없음
- `triggered_by` family 리스트를 ui_events.jsonl에 기록하지 않음

### 5.3 post_select_conflict detail ui.log (T3)

Target: `stage4_interview_round.py` `_execute_round_post_select_validation` 리턴 직전 영역

현재 logging 경로:
- L4168-4171: `self.ctx.ui.log(f"   [TF-3] Provisional PASS → REJECT downgrade: {len(...)} post-select conflicts ({...})")` — 건수+유형만
- L4195: `director_feedback += "\n" + "\n".join(_post_select_conflicts)` — feedback 합류 (다음 round용)

누락된 operator sink:
- `_post_select_conflicts` 리스트 원소의 실제 conflict 문자열이 ui_events에 기록되지 않음
- final round 시 feedback은 소멸하므로 conflict body가 어디에도 남지 않음

## 6. Pass 2. Semantic Classification

### Class A. Primary realization (이번 wave)

1. **T1 — FlashbackVerifier 프롬프트 precision**: LLM 프롬프트에 기기-유형 과추론 방지 조항 추가. 구조/파이프라인 변경 없이 프롬프트 문자열만 수정.
2. **T2 — strong advisory escalation operator persistence**: Lane2-G1/G2b escalation 시 `ctx.ui.log` 호출 추가. `triggered_by` family 리스트를 ui_events event_kind=`policy`로 기록.
3. **T3 — post_select_conflict detail operator persistence**: downgrade 시 개별 conflict 문자열을 `ctx.ui.log`에 event_kind=`detail`로 기록.

### Class B. Residual but related (defer)

- `stage4_reject_runtime.py` rationale elision 정책 개선 (snapshot_fix_pack 비우기 vs 보존)
- TF-PATCH-GATE / TF-4 rewrite escalation 정책 완화 (현재는 과해석 advisory가 원인이므로 T1으로 해소)
- advisory_summary → DB/JSONL 구조화 (현재도 advisory_flags 경유로 들어가지만 nested dict라서 쿼리 어려움)

### Class C. Explicitly deferred outside this lane

- fix_pack 체계 리디자인
- Stage4 retry architecture 개편
- TruthGate precision 개선
- Stage4 global resume 선언
- Stage2/3 Tranche C residuals

## 7. Side-Effect Map

### file writes / artifacts
- T1: 프롬프트 문자열 변경 → future FlashbackVerifier advisory output이 달라짐 (MAJOR 발화 감소 예상)
- T2, T3: ui_events.jsonl에 추가 행 생성 (기존 구조, 신규 필드 없음)
- artifact file 직접 수정 없음

### DB / schema / transaction boundaries
- 해당 없음. 3 tranche 모두 DB schema 무변경.

### JSONL / log / audit sinks
- T2: `ui_events.jsonl`에 `event_kind=policy` 행 추가 (strong advisory escalation 시)
- T3: `ui_events.jsonl`에 `event_kind=detail` 행 추가 (post_select_conflict 시)
- 기존 JSONL 스키마 내에서 확장 — 신규 필드 불필요

### console / UI / operator output
- T2: operator console에 `[Stage4Gate]` advisory escalation family 정보 노출
- T3: operator console에 post_select conflict 개별 문자열 노출

### rollback / recovery / retry
- T1: FlashbackVerifier MAJOR 감소 → `strong_advisory_escalation_non_local_fix` REJECT 감소 → retry 횟수 감소 예상
- T2, T3: retry 동작 자체 무변경 (관측성만 보강)

### cache / global state
- 해당 없음.

### bootstrap fallback / config-env mutation
- 해당 없음.

## 8. Realization Architecture

이 wave는 3개의 독립 tranche로 구성된다. 각 tranche는 서로 의존성이 없으며, 병렬 또는 순차 실행 모두 가능하다. 단, T1이 가장 높은 ROI(loop 원인 제거)를 가지므로 우선 실행을 권장한다.

### Tranche 1. FlashbackVerifier Prompt Precision

**Goal**: "화면의 버튼" 표현만으로 기종 변경을 추론하는 MAJOR advisory 발화를 막는다.

**Realization**:
- `flashback_verifier.py` `_llm_check` 메서드의 프롬프트에 precision clause 추가
- 추가 내용 (의미):
  - 같은 기기의 다른 표현(폴더폰 ↔ 휴대전화, 화면의 버튼 ↔ 액정)은 모순이 아님
  - 구형 휴대전화(폴더폰, 슬라이드폰 등)도 LCD 화면과 물리 버튼이 있으므로 "화면의 버튼" 서술 가능
  - 단어 수준 표현 차이만으로 기기 형태가 변했다고 추론 금지
- 프롬프트 구조나 파싱 로직 무변경
- `_parse_llm_response` 무변경
- 테스트: FlashbackVerifier 단위테스트 추가 — 폴더폰/화면의 버튼 시나리오에서 빈 배열 반환 확인

**Why first**: 이 과해석이 ep2 strong advisory loop의 직접 발화 원인이다. 이것만 막아도 `strong_advisory_escalation_non_local_fix` REJECT 연쇄가 끊긴다.

### Tranche 2. Strong Advisory Escalation Operator Persistence

**Goal**: strong advisory family가 escalation을 일으켰을 때 어떤 family인지 `ui_events`에 남긴다.

**Realization**:
- `stage4_interview_round.py` `_normalize_director_gate_semantics` 메서드 내 3개 지점에 `self.ctx.ui.log` 호출 추가:
  1. L2093 영역 (PASS → PASS_WITH_FIX): family 리스트를 `meta`에 포함
  2. L2151 영역 (PASS_WITH_FIX → REJECT: fix_scope contract violation): gate_basis를 `meta`에 포함
  3. L2199 영역 (PASS_WITH_FIX → REJECT: non_local_fix): family 리스트 + contract reason을 `meta`에 포함
- `event_kind="policy"`, `component="director_gate"`로 통일
- 기존 `logging.warning` 호출은 유지 (Python log와 ui_events 이중 기록)
- 테스트: 기존 gate semantics 테스트에 ui.log 호출 검증 추가

**Why second**: loop 원인 제거(T1) 후에도 future advisory escalation 사후 진단을 위해 필요.

### Tranche 3. Post-Select Conflict Detail Operator Persistence

**Goal**: post_select_conflict downgrade 시 실제 conflict 문자열을 `ui_events`에 남긴다.

**Realization**:
- `stage4_interview_round.py` `_execute_round_post_select_validation` 내 L4168 영역에 추가 `ctx.ui.log` 호출:
  - 각 `_post_select_conflicts` 원소를 개별 `event_kind="detail"`, `component="post_select_validation"`으로 기록
  - 또는 전체 conflicts를 `meta={"conflict_details": _post_select_conflicts}`로 한 번에 기록
- 기존 L4168-4171의 건수+유형 summary log는 유지
- `director_feedback` 합류 로직 (`L4195`) 무변경
- 테스트: post_select_conflict 시나리오에서 ui.log 호출에 conflict detail 포함 확인

**Why third**: R10 final round처럼 다음 round가 없을 때 conflict body 소멸 방지.

## 9. Execution Tranches

1. **T1** — `flashback_verifier.py` 프롬프트 precision clause 추가 + 단위테스트
2. **T2** — `stage4_interview_round.py` strong advisory escalation `ctx.ui.log` 추가 + 테스트 보강
3. **T3** — `stage4_interview_round.py` post_select_conflict detail `ctx.ui.log` 추가 + 테스트 보강

## 10. Acceptance Criteria

- [ ] FlashbackVerifier LLM 프롬프트에 기기-유형 과추론 방지 조항이 포함됨
- [ ] FlashbackVerifier 단위테스트: 폴더폰/화면의 버튼 시나리오에서 MAJOR 미발화 (빈 배열 반환)
- [ ] `_normalize_director_gate_semantics`의 3개 escalation 지점에서 `ctx.ui.log`가 호출됨
- [ ] strong advisory escalation ui.log 호출에 `triggered_by` family 리스트가 `meta`에 포함됨
- [ ] post_select_conflict downgrade 시 개별 conflict 문자열이 `ctx.ui.log`에 기록됨
- [ ] 기존 테스트 전량 pass (regression 없음)
- [ ] ruff 0 violations
- [ ] `180+ LOC` 신규 함수 없음

## 11. Verification Plan

- `pytest tests/ -q` — 전체 regression
- `python -m py_compile modules/core/flashback_verifier.py modules/core/stage4_interview_round.py` — syntax
- `ruff check modules/core/flashback_verifier.py modules/core/stage4_interview_round.py` — lint
- FlashbackVerifier 신규 단위테스트: mock LLM이 폴더폰+화면 버튼 시나리오에서 빈 배열 반환하는지 확인
- strong advisory escalation 테스트: mock ctx.ui.log 호출 카운트 + meta 내 family 리스트 확인
- post_select_conflict 테스트: mock ctx.ui.log 호출 카운트 + meta 또는 개별 로그 내 conflict body 확인

### Canary 후속 검증 (이번 문서에서 즉시 실행 계획으로 승격하지 않음)

- 3 tranche patch 완료 + 전체 테스트 pass 후, 별도 오더로 canary 재검증 결정
- canary 재검증 조건:
  1. T1-T3 모두 구현 + 테스트 pass
  2. ruff 0 violations
  3. operator가 canary 실행을 명시적으로 승인
- canary 범위: `canary_0_0_stage34_arc2` 신규 copy, Arc 2 ep5-9, Stage3+Stage4
- canary 성공 기준: ep2 Stage4 round ≤ 5 이내 PASS 도달, strong_advisory_escalation_non_local_fix 0회

## 12. Guardrails

- 코드 패치를 이 문서 안에서 실행하지 않는다
- fresh canary를 이 문서 안에서 실행하지 않는다
- `0_0` source project를 수정하지 않는다
- Stage4 global resume를 선언하지 않는다
- `resolved` 또는 `resume-ready`를 선언하지 않는다
- Stage2/3를 재개편하지 않는다
- fix_pack 체계를 전면 개편하지 않는다
- TruthGate를 전면 수정하지 않는다
- Stage4 retry architecture를 개편하지 않는다
- FlashbackVerifier의 detect_flashbacks (Python 수집) 로직은 변경하지 않는다 — LLM 프롬프트만 수정
- `_parse_llm_response` 파싱 로직은 변경하지 않는다
- Stage4 paused 상태를 유지한다

## 13. Temp Queue Notes

- temp status: `partial`
- cleanup condition: 3 tranche 구현 + 테스트 pass + closure audit 후 temp mirror 제거
- roadmap dependency: parent lane `0_0-stage2-stage3-stage4-readiness-remediation`의 Stage4 blocked 상태를 해소하기 위한 prerequisite
- parent lane 관계: 이 SSOT가 완료되어야 parent lane의 Stage4 sub-verdict를 `blocked` → `verification_pending`으로 전환할 수 있음

## 14. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 15. 3-Pass Audit Record

### Pass 1. Structure and Scope

- scope를 ep2 Stage4 advisory escalation loop 3점으로 한정했다
- FlashbackVerifier precision / strong advisory persistence / post_select_conflict observability 3 tranche만 포함
- Stage2/3 regression, Stage4 global resume, fix_pack redesign을 명시적으로 제외했다
- execution-ssot-template.md 구조를 따랐다
- side-effect coverage를 모든 카테고리에 대해 명시했다

### Pass 2. Evidence and Consistency

- FlashbackVerifier 과해석 판정: `ep_0001.txt` L93-99 artifact truth와 `selected_before_fix__B.txt` L5/L31 artifact truth를 직접 대조 확인
- strong advisory escalation logging 누락: `stage4_interview_round.py` L2093/L2151/L2199에서 `logging.warning`만 호출하고 `self.ctx.ui.log` 미호출을 코드에서 직접 확인
- post_select_conflict detail 누락: L4168-4170의 `ctx.ui.log`가 건수+유형만 기록하고, L4195에서 feedback 합류만 하는 것을 코드에서 직접 확인
- advisory_summary → `_last_advisory_summary` → `_STRONG_ADVISORY_KEYS` → escalation 파이프라인을 `stage4_director_runtime.py` L1279-1298 → `stage4_interview_round.py` L2080-2204로 추적 완료
- evidence.json의 `code_truth` 섹션과 live code line 참조가 일치
- canonical path / temp mirror path 정확

### Pass 3. Execution and Readability

- 3 tranche가 독립적이며 각각 구체적인 코드 위치를 지정
- acceptance criteria가 검증 가능한 체크리스트 형태
- canary를 후속 검증 단계로만 기술하고 즉시 실행 계획으로 승격하지 않았다
- Stage4 paused 유지를 guardrails에 명시
- non-goals가 명확하고 누락 없음

Confidence: `96%`

Remaining 4%:
- FlashbackVerifier LLM의 실제 과해석 패턴이 프롬프트 정밀도 조항 추가만으로 100% 해소되는지는 canary 검증 전까지 medium confidence
- post_select_conflict의 R10 최종 conflict body가 정확히 어떤 문자열이었는지는 ui_events에 기록되지 않아 추정에 의존 (이 문서의 T3이 해소할 예정)
