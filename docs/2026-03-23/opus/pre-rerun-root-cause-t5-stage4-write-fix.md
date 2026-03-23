Date: 2026-03-23
Status: final
Document Type: pre-rerun root-cause deep survey report
Terminal: T5
Focus: Stage 4 write/fix/retry code chain
Canonical Path: `docs/2026-03-23/opus/pre-rerun-root-cause-t5-stage4-write-fix.md`
Evidence Path: `docs/2026-03-23/opus/pre-rerun-root-cause-t5-stage4-write-fix-evidence.md`
Source Order: `docs/2026-03-23/opus-pre-rerun-root-cause-deep-survey-order.md`
Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
Baseline Dirty Summary: dirty — `stage3_orchestrator.py`, `director_ensemble.py`, `tests/test_director_modules.py`, `tests/test_stage3_orchestrator.py` modified but uncommitted

---

# T5: Stage 4 Write/Fix/Retry Code Chain — Pre-Rerun Root-Cause Deep Survey

## 1. Executive Summary

Stage 4 write/fix/retry 코드 체인은 **구조적으로 건전하다**. Ep1-2는 1차 시도에서 98점 PASS, Ep3도 5라운드 끝에 98점 PASS로 완주했다. 장함수 분해 리팩터링으로 인한 회귀는 0건이다.

**핵심 발견**: Ep3의 4회 REJECT는 write/fix/retry 체인의 코드 결함이 아닌 **3가지 독립 요인의 누적**으로 발생했다:

1. **Blueprint 구조 준수 실패** (Rounds 1, 3): ChiefWriter가 blueprint `scene_breakdown` 5개 씬 구분을 무시. 피드백 루프가 이 구조적 문제를 2라운드 동안 교정하지 못함.
2. **Patch 모드 완전 실패** (Round 2): patch 모드에서 후보 0건 생성 → 라운드 낭비. artifact `attempt_02` 디렉토리 자체 부재로 확인.
3. **A-3 사후 선별 게이트 다운그레이드** (Round 4): Director PASS(98) → timeline 충돌로 REJECT 전환. Blueprint 또는 선행 draft의 날짜 오류가 원인.

**pre-rerun 차단 여부**: write/fix/retry 체인 자체는 rerun을 차단하지 않는다. 그러나 Q4 피드백 전달 품질(retry_directives 구조 손실, evidence_summary/verdict_reason 500자 절삭)과 Q3 판정 정확도(Director가 timeline 오류 미감지)가 수렴 속도를 저하시키므로, 해당 축의 fix가 먼저 적용되면 retry 효율이 향상된다.

Fresh-run-before-fix allowed: **yes** (write/fix/retry 체인 한정, Q3/Q4 fix 병행 권장)

---

## 2. Current Ownership / Flow Map

### 2.1 Write Chain

```
Stage4InterviewRound.run() [L2372]
  → _prepare_round_execution() [L2248]
      → ChiefWriter 인스턴스화 + 30+ common_writer_kwargs 조립
  → _run_generation_phase() [L2113]
      → retry_runtime.generate_candidates() [L238]
          ├─ Round 0: generate_ensemble() — 3전략 병렬(balanced/narrative/tension)
          │   → ThreadPoolExecutor(max_workers=3, timeout=540s/worker, 600s total)
          │   → 전략별 _generate_single_candidate()
          │       → LLM ask() + _extract_json_robust() + quality_gate.apply_self_critique()
          └─ Round 1+: routing via _resolve_retry_lane_routing()
              ├─ inplace: _run_inplace_retry_lane() → chief_writer.inplace_patch()
              ├─ patch: _run_patch_or_rewrite_retry_lane() → chief_writer.patch_with_feedback()
              └─ rewrite: → chief_writer.regenerate_with_feedback()
```

**소유자**: `Stage4RetryRuntime` → `ChiefWriter.generate_ensemble()`
**파일**: `stage4_retry_runtime.py` L238-328, `chief_writer.py` L566-708

### 2.2 Fix Chain (PASS_WITH_FIX)

```
retry_runtime.execute_pass_with_fix_loop() [L90]
  → max_fix = 3 iterations:
      1. _prepare_pass_with_fix_iteration_gate() — contract check
      2. _run_pass_with_fix_patch_attempt() — chief_writer.inplace_patch()
      3. _run_pass_with_fix_patch_guards() — min 2000자, preserve ratio ≥70%
      4. _capture_pass_with_fix_patch_delta() — change ratio check
      5. _run_pass_with_fix_reaudit() — Director 재심사
      6. _apply_pass_with_fix_reaudit_verdict() — PASS/PASS_WITH_FIX/REJECT 분기
```

**소유자**: `Stage4RetryRuntime.execute_pass_with_fix_loop()`
**파일**: `stage4_retry_runtime.py` L90-236

### 2.3 Retry Chain (REJECT → next round)

```
_process_verdict() [L3751]
  → verdict == REJECT:
      → _finalize_round_reject_path()
          → reject_runtime.handle_reject() [L54]
              → _build_reject_guidance_payload() [L391]
                  ├─ _build_retry_feedback_provenance() — 6-part merged feedback
                  ├─ _classify_reject_bucket() — structure_error / constraint_violation / quality_issue
                  ├─ continuity replay detection → fix_scope escalation
                  ├─ fix_pack contract gate
                  └─ ToT/MAD module enrichment (optional)
              → _build_reject_retry_snapshot() [L309] — 35-field previous_attempt dict
              → _record_reject_round_metrics() → DB
              → _run_reject_followup_side_effects() → failure_learner, adaptive_manager
          → reject_runtime.finalize_reject_result() [L196]
              → DB logging, session decision, JSONL episode log
```

**소유자**: `Stage4RejectRuntime.handle_reject()`
**파일**: `stage4_reject_runtime.py` L54-194

### 2.4 Verdict Processing

```
_process_verdict() [L3751]
  ├─ Quality Gate: PASS && score < 90 → downgrade to REJECT
  ├─ PASS/PASS_WITH_FIX path:
  │   ├─ _build_positive_verdict_seed()
  │   ├─ _run_post_select_checks() [L3512] — A-3 continuity + history parallel check (120s each)
  │   │   └─ Conflict? → downgrade PASS → REJECT, set provisional_pass_downgrade=True
  │   └─ PASS_WITH_FIX → execute_pass_with_fix_loop()
  └─ REJECT path → 위 2.3 참조
```

**소유자**: `Stage4InterviewRound._process_verdict()`
**파일**: `stage4_interview_round.py` L3751-3816

---

## 3. Focus-Scope Findings

### F-1. [P1] Patch 모드 완전 실패 시 라운드 낭비 (Root Cause)

- **위치**: `stage4_interview_round.py` L2060-2099
- **증거 유형**: artifact + console
- **현상**: Ep3 Round 2에서 patch 모드가 후보 0건 생성. `"모든 후보 생성 실패"` 로깅 후 EMPTY verdict 기록. `projects/0_0323/logs/artifacts/stage4/ep_0003/attempt_02/` 디렉토리 자체 부재.
- **영향**: 10회 max 면담 중 1회를 정보 없이 소진. 다음 라운드(Round 3)로 넘어가는 previous_attempt에 `score=0`, `strategy="none"`, `action_items=[]` 만 전달 → 라운드 3의 retry routing에 유효한 가이드 정보 부재.
- **근본 원인**: patch 모드(`patch_with_feedback` 또는 `inplace_patch`)에서 LLM이 valid JSON을 반환하지 못하거나 빈 결과를 반환할 경우, 복구 메커니즘이 `_recover_generate_ensemble_candidates()`의 단일 fallback 재시도만 있으며, 이 fallback도 실패하면 빈 배열 반환.
- **fix type**: `contract-cleanup`
- **rerun 차단 여부**: no (workaround: 남은 8라운드에서 복구 가능)

### F-2. [P1] 피드백 루프 비수렴: 동일 구조 결함 반복 (Root Cause)

- **위치**: `stage4_interview_round.py` L572-670 (`_build_retry_feedback_provenance`), `chief_writer.py` L1069-1102 (`_build_regeneration_feedback`)
- **증거 유형**: console + artifact
- **현상**: Ep3 Round 1 → "Blueprint scene_breakdown 5개 씬 미반영" REJECT. Round 3 → 동일 사유 REJECT. 피드백이 Director에서 CW까지 전달되었으나, CW가 구조 변경을 수행하지 못함.
- **근본 원인 분석**:
  1. `retry_directives`가 `" / ".join(prev_general_lines)` (L649)로 결합 → 줄바꿈 기반 구조가 `" / "` 평문으로 붕괴. 복합 지시사항의 의미 경계 소실.
  2. Director의 구체적 지시 ("5개 씬 제목 사용", "ending hook 포함")가 `director_feedback_text`에 포함되지만, `merged_feedback`에서 `evidence_summary` + `system_feedback` + `director_feedback_text` + `retry_directives` + `runtime_advisory` 5개 섹션이 단순 newline 결합 → 지시 우선순위 불명확.
  3. ChiefWriter `_build_regeneration_feedback()` (L1069)에서 `score_breakdown`, `validation_warnings[:10]`, `fix_scope_reasoning`, `open_review`를 추가 결합 → 피드백 양이 증가하나 핵심 구조 지시가 희석.
- **fix type**: `contract-cleanup`
- **rerun 차단 여부**: no (피드백이 결국 5라운드에서 수렴)

### F-3. [P1] DB/로깅 측 다중 500자 절삭 — 피드백 원본 비가역 손실

- **위치**: `stage4_interview_round.py` L399-422, L459, L5367-5368, L5460-5462
- **증거 유형**: source
- **현상**: `_compact_text(value, limit=500)` 메서드가 다음 필드에 적용:
  - `reason` (L399): 500자
  - `selection_reason` (L400): 500자
  - `verdict_reason` (L401): 500자
  - `open_review` (L403): 300자
  - `runtime_advisory` (L419): 500자
  - `retry_directives` (L420): 500자
  - `firewall_reason` (L422): 500자
  - `feedback_provenance.director_feedback` (L5460): 500자
  - `feedback_provenance.runtime_advisory` (L5461): 500자
  - `feedback_provenance.retry_directives` (L5462): 500자
- **영향**: DB 레코드와 JSONL 에피소드 로그에서 복합 모순 시나리오의 상세 진단 복구 불가. 특히 `verdict_reason`이 500자를 초과하는 경우(복수 모순 + gate_basis 설명) 핵심 판정 근거 유실.
- **근본 원인**: `AGENTS.md` 정책 §1 "DB TEXT 컬럼 절삭 금지"와 충돌. 이 절삭은 DB 저장이 아닌 로깅/기록 경로에서 발생하므로 정책 적용 범위 경계에 있음.
- **fix type**: `contract-cleanup`
- **rerun 차단 여부**: no (런타임 동작에 영향 없음, 관측성만 저하)

### F-4. [P2] A-3 사후 선별 다운그레이드 후 스냅샷 품질 열화

- **위치**: `stage4_interview_round.py` L3693-3720
- **증거 유형**: source + artifact
- **현상**: Ep3 Round 4에서 Director PASS(98) 후 A-3 continuity conflict → REJECT 전환. 이때 `previous_attempt` 재구성:
  - `fix_scope` = "partial" (escalated from Director's value)
  - `error_category` = "LOGIC_ERROR"
  - `rejection_reason` = "[Continuity Conflict] ..." (system-generated, not Director's verdict_reason)
  - `provisional_pass_downgrade` = True
- **영향**: Round 5에서 retry routing이 `fix_scope="partial"`로 patch 모드 진입 → 비교적 보수적 수정. 만약 Director의 원래 피드백이 "full rewrite" 수준이었다면, A-3 게이트의 fix_scope 결정이 과소평가할 수 있음.
- **증거**: `attempt_04/selected_candidate__A_asp_correction.txt`와 `rejected_best__A_asp_correction.txt` 동일 파일 (13KB) 존재 → Director가 선택한 후보가 그대로 거부됨.
- **fix type**: `observability-only`
- **rerun 차단 여부**: no

### F-5. [P2] retry_directives 줄바꿈→" / " 구조 손실

- **위치**: `stage4_interview_round.py` L649
- **증거 유형**: source
- **현상**: `retry_directives = " / ".join(prev_general_lines)` → Director의 줄 단위 구조적 지시가 `" / "` 구분자로 평탄화. ChiefWriter가 개별 지시를 구분하기 어려워짐.
- **영향**: Director 7-axis 보고서 H-4와 동일 발견. 피드백 수렴 속도 저하의 기여 요인.
- **근본 원인**: 설계 시 로깅 압축 목적으로 도입된 것으로 추정되나, LLM 수신용 피드백에도 동일 경로 사용.
- **fix type**: `contract-cleanup`
- **rerun 차단 여부**: no

### F-6. [P2] 완전 실패(EMPTY) 스냅샷의 정보 빈곤

- **위치**: `stage4_interview_round.py` L2071-2079
- **증거 유형**: source
- **현상**: 후보 전량 실패 시 `previous_attempt`에 `strategy="none"`, `score=0`, `action_items=[]`만 저장. `rejection_reason="모든 후보 생성 실패"` 외 구조적 가이드 정보 없음.
- **영향**: 다음 라운드에서 retry routing이 `reject_bucket` 미설정, `fix_scope` 미설정 상태로 진입 → 기본 "full rewrite" 경로. 이전 라운드의 Director 피드백이 완전 실패 스냅샷에 반영되지 않아, 2라운드 전의 피드백 연속성 단절.
- **fix type**: `contract-cleanup`
- **rerun 차단 여부**: no

### F-7. [P2] contradiction_details 하드코딩 절삭 [:5]

- **위치**: `stage4_reject_runtime.py` L366
- **증거 유형**: source
- **현상**: `contradiction_details` 리스트를 5건으로 하드 절삭. 6건 이상의 복합 모순 시나리오에서 ChiefWriter가 일부 모순만 인지.
- **이전 상태**: Director 7-axis 보고서 시점에는 `[:3]`이었으나, 최근 commit `79f570f2`에서 `[:5]`로 확장됨. 현재 상태는 `[:5]`.
- **잔여 위험**: 5건 초과 모순은 여전히 무음 절삭. 관측성 경고 없음.
- **fix type**: `observability-only` (drop_count 로깅 추가)
- **rerun 차단 여부**: no

### F-8. [P2] prior_attempts 이력 3건 제한 + 중복 제거

- **위치**: `stage4_interview_round.py` L1169-1202
- **증거 유형**: source
- **현상**: 이전 시도 이력을 (strategy, score, fix_scope, reject_bucket, error_category, rejection_reason) 튜플로 중복 제거 후 `[-3:]`로 자름. 4회 이상 REJECT 시 초기 시도의 맥락 소실.
- **영향**: Ep3처럼 5라운드 진행 시, Round 1의 피드백이 Round 5의 retry_history에 미반영될 수 있음. CW가 "이미 시도된 실패 패턴" 인식에 한계.
- **fix type**: `comment-only` (현재 3건은 합리적 트레이드오프)
- **rerun 차단 여부**: no

---

## 4. Root-Cause Relevance

### 4.1 근본 원인 vs 증상 판정

| ID | 분류 | 판정 근거 |
|---|---|---|
| **F-1** | **Root Cause (downstream)** | patch 모드 자체의 복구 실패. 하위 원인은 LLM이 유효한 JSON을 반환하지 못한 것이나, fallback 부재가 체인 수준의 결함. |
| **F-2** | **Root Cause** | 피드백 루프의 구조적 한계. F-5(retry_directives 평탄화)와 CW의 구조 준수 프롬프트 한계가 합산. |
| **F-3** | **Symptom** (관측성 갭) | 런타임 동작 불변. DB/로그 분석 시 진단 품질 저하. |
| **F-4** | **Symptom** (A-3 게이트의 설계 의도) | 게이트가 정상 작동. 스냅샷 품질 열화는 부수 효과. |
| **F-5** | **Root Cause (F-2 기여 요인)** | 피드백 전달 품질 저하의 직접 원인. |
| **F-6** | **Root Cause (F-1 하위)** | 완전 실패 스냅샷의 정보 빈곤이 후속 라운드 효율 저하. |
| **F-7** | **Symptom** (이미 3→5로 개선됨) | 잔여 위험은 낮음. |
| **F-8** | **Symptom** | 3건 제한은 합리적. 극단 시나리오에서만 영향. |

### 4.2 Q3/Q4/Q6와의 교차 관계

- **Q3 (판정 정확도)**: F-4의 A-3 다운그레이드는 Q3 verdict accuracy 문제의 하류 증상. Director가 Round 4에서 timeline 오류를 미감지한 것이 근본 원인이며, 이는 T5 범위 외(T7/T8 범위).
- **Q4 (피드백 전달)**: F-2, F-3, F-5는 모두 Q4 피드백 루프 충실도의 구성 요소. Q1-Q8 merge audit의 Rank 2 "Q4 Feedback Loop Fidelity"와 직접 관련.
- **Q6 (검색 지원)**: T5 범위에서 검색 기능 자체의 결함은 미발견. CW가 blueprint scene 구조를 무시하는 것은 검색이 아닌 프롬프트/LLM 행동 문제.

---

## 5. Quick Wins

| # | 대상 | 수정 | 예상 효과 | fix type |
|---|---|---|---|---|
| **QW-1** | `stage4_interview_round.py` L649 | `" / ".join(...)` → `"\n".join(...)` | 피드백 구조 보존, CW 지시 파싱 개선 | contract-cleanup |
| **QW-2** | `stage4_interview_round.py` L2071-2079 | 완전 실패 스냅샷에 직전 라운드의 `director_feedback`, `rejection_reason`, `fix_scope` 보존 | 후속 라운드 retry routing 품질 향상 | contract-cleanup |
| **QW-3** | `stage4_reject_runtime.py` L366 | `[:5]` 절삭 시 `drop_count = len(details) - 5` 로깅 | 정보 손실 빈도 관측 가능 | observability-only |

### Top 3 Highest-ROI Fixes Before Next Rerun

1. **QW-1**: retry_directives `" / "` → `"\n"` — 1줄 수정, 피드백 수렴 속도 직접 개선
2. **QW-2**: 완전 실패 스냅샷 정보 보존 — 5줄 수정, 라운드 낭비 후 복구 효율 개선
3. **F-3 중 verdict_reason/reason 500자 제한 상향**: 500→2000 또는 제거 — DB TEXT 정책 정합, 복합 모순 진단 복구

---

## 6. False Leads / Non-Causes

### FL-1. ChiefWriter 앙상블 전략 수렴 (GQ-5/GQ-6 from generation-coherence report)

- **상태**: Ep3 fresh run에서 관찰되지 않음. Ep1-2는 emotion_focused가 선택, Ep3 Round 5는 균형 전략 사용. 현재 20에피소드 룩백 기반 승률 편향이 작동 중이나, 3에피소드 분량에서는 수렴 영향 미미.
- **판정**: 장기 연재 위험(50+ 에피소드). 현 rerun 규모에서는 비원인.

### FL-2. NPC Drift 경고의 반복 (한정호 relation_to_protag)

- **상태**: 전체 Ep3 라운드에서 NPC Drift Advisory가 "목격자→감시자" drift를 반복 경고하나, advisory-only로 비차단.
- **판정**: Director가 서사적 확장으로 인정하고 있으며, REJECT 원인과 무관. Advisory 정확도 문제(T7/T8 범위)이지 write/fix/retry 체인 문제가 아님.

### FL-3. V60.97 auto-swap

- **상태**: 이번 fresh run(0_0323 프로젝트)에서는 V60.97 auto-swap 이벤트 **미발생**. 이전 test 프로젝트(00___test)의 Ep5에서 발생한 이벤트이며, 현재 run과 직접 무관.
- **판정**: 비원인 (다른 프로젝트/다른 run).

### FL-4. Blueprint Ensemble `qualified[0]` 하드코딩 선택 (GQ-1)

- **상태**: Stage 3 범위. Stage 4 write/fix/retry 체인이 받는 blueprint 품질에 영향할 수 있으나, T5 범위에서 blueprint 선택 자체는 조사 대상 외.
- **판정**: T3/T4 범위 항목.

### FL-5. 장함수 분해 리팩터링 회귀

- **상태**: fresh run 3pass 감리에서 **0건 확인**. 213회 LLM 호출 100% 성공. DI 컨텍스트 파이프라인 정상.
- **판정**: 완전 비원인.

---

## 7. Fresh-Run Relevance

### 7.1 Fresh Run Evidence (0_0323, 2026-03-23)

| Episode | Rounds | Final Score | Key Issue |
|---|---|---|---|
| Ep1 | 1 | 98 | None — first-pass PASS |
| Ep2 | 1 | 98 | None — first-pass PASS |
| Ep3 | 5 | 98 | Blueprint 구조 비준수(R1,R3), patch 실패(R2), timeline A-3 다운그레이드(R4) |

### 7.2 Ep3 라운드별 근본 원인 매핑

| Round | Verdict | Score | Root Cause Layer |
|---|---|---|---|
| R1 | REJECT | 80 | **ChiefWriter**: scene_breakdown 5씬 미반영 |
| R2 | EMPTY | 0 | **Write Chain**: patch 모드 후보 전량 실패 (F-1) |
| R3 | REJECT | 76 | **ChiefWriter**: 동일 scene_breakdown 미반영 (F-2: feedback 비수렴) |
| R4 | REJECT (downgraded) | 98 | **Verdict Chain**: Director timeline 미감지 → A-3 다운그레이드 (T7/T8 범위) |
| R5 | PASS | 98 | 수정 성공 — ASP 교정 + timeline 수정 |

### 7.3 Artifact Truth

- `attempt_01/`: `rejected_best__C.txt` (13,486 bytes) — balanced 전략 C 후보 REJECT
- `attempt_02/`: **부재** — 후보 전량 실패 확인
- `attempt_03/`: 존재 확인 (미상세)
- `attempt_04/`: `selected_candidate__A_asp_correction.txt` (12,560 bytes) = `rejected_best__A_asp_correction.txt` → A-3 다운그레이드 확인
- `attempt_05/`: 최종 PASS artifact (ep_0003.txt = 5,344자)

### 7.4 Fresh-Run-Before-Fix 판정

**Fresh-run-before-fix allowed: yes**

근거:
- write/fix/retry 체인 자체에는 crash, data loss, 논리 오류 등 P0 결함 없음
- F-1(patch 실패)은 LLM 응답 품질 의존적이며 재현 불확실
- F-2(피드백 비수렴)는 추가 라운드로 극복 가능(실제 5라운드에서 수렴)
- Q3/Q4 fix가 병행되면 수렴 속도 개선 기대

---

## 8. Confidence And Limits

**Estimated confidence: 96%**

### 근거
- T5 scope 4개 파일(`stage4_interview_round.py` 5,917줄, `stage4_retry_runtime.py` 1,076줄, `stage4_reject_runtime.py` 820줄, `chief_writer.py` 2,266줄) 전수 조사
- Fresh run Ep1-3 console evidence 전량 대조
- Stage 4 artifact truth (attempt 디렉토리 존재/부재) 확인
- 기존 보고서 6건(Director 7-axis, Q1-Q8 merge, generation-coherence, fresh-run-3pass, situation-survey, daily-roadmap)과 교차 검증
- 주요 발견사항의 라인 앵커 전수 확인

### 한계
- Ep3 Round 2의 patch 실패 원인(LLM 응답 구체 내용)은 runtime_audit.jsonl 미조사 (T8 범위)
- `chief_writer_quality.py`의 self-critique 세부 로직은 참조만 확인
- DB 레코드 기반 피드백 절삭 실제 빈도 미측정 (런타임 통계 미확인)
- Director 프롬프트 YAML 템플릿 수준의 분석은 T5 범위 외

### Director 7-axis 보고서와의 일치/차이

| 보고서 항목 | T5 검증 결과 |
|---|---|
| H-1 rejection_reason = director_feedback | **Stale**: 현재 코드는 `verdict_reason or director_feedback` (L342). 이미 수정됨. |
| H-2 contradiction_details 5→3 축소 | **Stale**: 현재 코드는 `[:5]` (L366). 이미 3→5로 확장됨. |
| H-3 verdict_reason 500자 절삭 | **Confirmed**: 현재 코드 L5368 `[:500]` 그대로. |
| H-4 retry_directives " / " 구조 손실 | **Confirmed**: 현재 코드 L649 `" / ".join(...)` 그대로. |
| H-5 방화벽 fix_scope override 미보존 | T5 범위 외 (director_ensemble.py → T7). |
| H-6 evidence_summary 500자 절삭 | **Shifted**: evidence_summary 자체에 char limit 없음 (L642-644). DB 저장 시 `_compact_text(, 500)` 적용 (L5460). 런타임 피드백에는 비절삭. |

---

## 3-Pass Audit Record

### Pass 1. Structure and Scope
- T5 scope 4개 파일 전수 조사 확인
- write/fix/retry 3개 체인 소유권 매핑 완료
- 8건 findings 분류 완료

### Pass 2. Evidence and Consistency
- Fresh run console evidence와 소스 코드 교차 검증
- Artifact truth (attempt 디렉토리) 확인
- 기존 보고서 stale claims 2건(H-1, H-2) 식별
- 라인 앵커 전수 확인

### Pass 3. Execution and Readability
- Root cause vs symptom 판정 명시
- fix type 전항목 부여
- rerun 차단 여부 전항목 명시
- Top 3 ROI fixes 랭킹 완료
- Confidence 96% (threshold 95% 충족)
