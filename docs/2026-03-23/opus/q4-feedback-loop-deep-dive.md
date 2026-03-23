Date: 2026-03-23
Status: final (3-pass audited)
Document Type: Q4 feedback loop quality deep-dive report
Terminal: T4
Axis: Q4 — "잘 설명하냐" (reject/fix feedback quality, instruction handoff, explanation fidelity)
Canonical Path: `docs/2026-03-23/opus/q4-feedback-loop-deep-dive.md`
Primary Scope: `stage4_reject_runtime.py`, `stage2_finalizer.py`, `director_auditor.py`, `stage3_orchestrator.py`

---

## 1. Executive Summary

Q4 축은 REJECT 판정 시 Director가 생산한 피드백이 다음 생성 라운드(ChiefWriter/Blueprint)에 **정확하고 완전하게 전달되는지**를 평가한다.

현재 시스템은 **피드백 합성(provenance tracking)과 구조화된 reject guidance 체계를 갖추고 있으며**, feedback_provenance dict, reject_bucket 분류, fix_scope 정제, retry_budget_axes 할당이 모두 작동한다. 이는 대부분의 동급 시스템 대비 우수한 설계다.

그러나 **피드백 전달 파이프라인 중간에 정보 축소/변환이 다수 발생**하며, 이로 인해 LLM이 원래 지적한 문제를 ChiefWriter가 완전히 인지하지 못할 위험이 존재한다. 핵심 문제는 3개 클래스로 분류된다:

1. **필드 손실**: 구조화된 데이터가 문자열로 합성되며 원본 복구 불가 (P1)
2. **다단계 절삭**: 각 레이어에서 독립적으로 `[:N]` 절삭이 적용되어 누적 손실 (P1)
3. **Stage 2/3 피드백 루프 비대칭**: Stage 4는 정교한 provenance 체계가 있으나, Stage 2/3은 상대적으로 단순한 reject→retry 경로 (P2)

**P0: 0건 | P1: 4건 | P2: 5건**

Fresh-run-before-fix allowed: **no** — P1 항목들이 피드백 루프 단절의 직접 원인이며, 수정 전 재실행 시 동일 패턴 재발 예상.

---

## 2. Current Ownership / Flow Map

### 2.1 Stage 4 Feedback Flow (가장 정교)

```
Director LLM 응답
  ├─ verdict_reason, feedback.issues, action_items, open_review
  ├─ contradiction_details, contradiction_types
  ├─ fix_scope, fix_scope_reasoning, fix_pack
  └─ score_breakdown, consistency_checklist
        │
        ↓
_build_retry_feedback_provenance()      [stage4_interview_round.py:556-658]
  ├─ system_feedback   (시스템 접두사 라인 분리)
  ├─ evidence_summary  (검증 근거 요약)
  ├─ director_feedback_text (LLM 피드백 + issues 합성)
  ├─ runtime_advisory  (advisory digest)
  └─ retry_directives  (이전 라운드 일반 피드백)
        │
        ↓ merged_feedback
_build_reject_guidance_payload()         [stage4_reject_runtime.py:390-502]
  ├─ reject_bucket 분류 (constraint_violation / structure_error / quality_issue)
  ├─ fix_scope 정제 (연속성 replay, fix_pack 계약 검증)
  ├─ ToT/MAD 조건부 보강
  └─ feedback_provenance dict 보존
        │
        ↓
_build_reject_retry_snapshot()           [stage4_reject_runtime.py:309-388]
  ├─ rejection_reason = director_feedback (★ 합성 문자열)
  ├─ contradiction_details[:3] (★ 5→3건 축소)
  ├─ retry_budget_axes 할당
  └─ prior_attempts 누적 히스토리
        │
        ↓ previous_attempt dict
ChiefWriter._build_regeneration_feedback()  [chief_writer.py:1069-1102]
  ├─ director_feedback 전문 주입
  ├─ previous_attempt.rejection_reason 주입
  ├─ score_breakdown, validation_warnings, fix_scope_reasoning, open_review 주입
  └─ retry_history (prior_attempts) 주입
```

**소유권 경계**:
- `DirectorEnsembleSelector` → 원본 verdict/feedback 생산
- `Stage4InterviewRound` → feedback provenance 합성
- `Stage4RejectRuntime` → reject guidance, retry snapshot 조립
- `ChiefWriter` → 재생성 프롬프트에 feedback 주입

### 2.2 Stage 2 Feedback Flow

```
DirectorQualityAuditor.audit_strategic_plan()  [director_auditor.py:970-1125]
  ├─ decision, score, reason, re_slice_instruction
  ├─ contradiction 방화벽 (CRITICAL≥1 / MAJOR≥2 → REJECT 강제)
  └─ self_consistency 투표 결과
        │
        ↓
Stage2Finalizer._handle_stage2_reject_path()    [stage2_finalizer.py:1538-1632]
  ├─ base_feedback = audit["re_slice_instruction"] or "밀도 보강 필요"
  ├─ reject_reason = audit["reason"] or "사유 미상"
  ├─ adaptive_feedback_intensity (attempt별 가이드 주입)
  └─ director_feedback_for_fourphase = "[Director REJECT 사유]\n{reason}\n[수정 지시]\n{feedback}"
        │
        ↓ current_feedback + director_feedback_for_fourphase
FourPhaseArcRuntime (재생성)
```

### 2.3 Stage 3 Feedback Flow

```
ThreePhaseBlueprintRuntime (pipeline)
  ├─ final_verdict, phases.validate, contradictions, comparison_notes
  └─ last_score, quality_gate_failed
        │
        ↓
Stage3Orchestrator._build_stage3_reject_reason()  [stage3_orchestrator.py:2089-2135]
  ├─ error[:240] + score + strategy + contradictions[:2]
  └─ 500자 전체 절삭
        │
        ↓
_append_stage3_rejection_history()                [stage3_orchestrator.py:2586-2618]
  ├─ reason[:200], specific_issue[:200], failure_category
  └─ score_breakdown (5건 제한)
        │
        ↓ stage_rejection_history (app-level list)
다음 시도에서 ThreePhaseBlueprintRuntime이 이전 실패 참조
```

---

## 3. Top Hotspots

### P1-1. `rejection_reason` 필드 원본 손실 (Stage 4)
- **file:line**: `stage4_reject_runtime.py:342`
- **현상**: retry snapshot의 `rejection_reason` 필드에 원본 `director_result.verdict_reason`이 아닌 합성된 `director_feedback` 문자열이 저장됨. `director_feedback`는 system_lines + evidence_summary + director_text + retry_directives가 합쳐진 긴 문자열이므로, 원본 LLM reject_reason이 복구 불가.
- **영향**: ChiefWriter가 `previous_attempt["rejection_reason"]`를 읽을 때 원본 사유가 아닌 합성 피드백을 받아, 핵심 문제를 정확히 특정하기 어려움.
- **fix type**: `contract-cleanup`
- **ROI**: HIGH — `_build_reject_retry_snapshot()`에서 `rejection_reason`을 원본 `director_result.get("verdict_reason")`로 설정하고, `merged_feedback`은 별도 `merged_director_feedback` 필드로 보존.

### P1-2. `contradiction_details` 다단계 축소 (Stage 4)
- **file:line**: `stage4_reject_runtime.py:365`
- **현상**: LLM이 생산한 모순 리스트가 director_ensemble에서 5건으로 제한되고(`_compact_contradiction_details`), retry snapshot에서 `[:3]`으로 추가 축소. 모순이 4건 이상이면 ChiefWriter가 일부 모순만 교정하고 나머지를 놓칠 위험.
- **영향**: 다중 모순 시나리오에서 REJECT 반복 (Fresh run P1-1 ep5 패턴과 관련).
- **fix type**: `contract-cleanup`
- **ROI**: HIGH — `[:3]` 제한을 `[:5]`로 확대하여 director_ensemble 생산량과 일치시킴.

### P1-3. Stage 4 피드백 필드 다단계 절삭 누적 손실
- **file:line**: 다수
  - `stage4_interview_round.py:1139` — `fix_scope_reasoning[:200]`
  - `stage4_interview_round.py:1140` — `open_review[:200]`
  - `stage4_interview_round.py:1143` — `rejection_reason[:240]`
  - `stage4_interview_round.py:1144` — `action_items[:3]`
  - `stage4_interview_round.py:637` — `retry_directives[:500]`
  - `stage4_reject_runtime.py:545` — `director_feedback[:100]` (콘솔 표시)
  - `stage4_reject_runtime.py:565` — `director_feedback[:150]` (failure_learner)
  - `stage4_reject_runtime.py:577` — `director_feedback[:200]` (adaptive_manager)
  - `stage4_reject_runtime.py:601` — `director_feedback[:200]` (quality_dashboard)
- **현상**: `_compact_attempt_snapshot()`에서 각 필드가 독립 절삭됨. 이 축약된 snapshot이 `prior_attempts`로 누적되면서, 3라운드 이후에는 초기 reject 사유가 200→240자로 극도로 축약.
- **영향**: 장기 retry 시 초기 라운드의 핵심 피드백 소실. 특히 `fix_scope_reasoning`과 `open_review`가 200자이므로 Director의 상세 서사 관찰이 잘림.
- **fix type**: `contract-cleanup`
- **ROI**: MEDIUM — `_compact_attempt_snapshot` 내 필드 한도를 현재 2배(400/480자)로 확대하되, `prior_attempts[-3:]` 유지로 메모리 증가 억제.

### P1-4. Stage 2 피드백 구조화 부재
- **file:line**: `stage2_finalizer.py:1587-1595`
- **현상**: Stage 2 REJECT 시 `director_feedback_for_fourphase`가 단순 f-string 문자열로 조립됨. `reject_reason`과 `base_feedback`(re_slice_instruction)만 포함하며, `contradiction_details`, `score_breakdown`, `fix_scope`, `fix_pack` 등 구조화된 필드가 모두 빠짐.
- **영향**: FourPhaseArcRuntime이 Stage 2 REJECT 사유를 받을 때, Director가 실제로 지적한 모순 상세나 점수 분포를 알 수 없음. Stage 4의 정교한 feedback_provenance 체계와 대비됨.
- **fix type**: `contract-cleanup`
- **ROI**: MEDIUM — audit dict에서 `contradictions`, `score_breakdown`, `fix_scope` 등을 추출하여 `director_feedback_for_fourphase`에 구조적으로 포함.

---

## 4. Quick Wins

### QW-1. `contradiction_details[:3]` → `[:5]` 확대
- **file:line**: `stage4_reject_runtime.py:365`
- **변경량**: 1줄
- **위험**: 없음 (메모리 증가 미미)
- **fix type**: `contract-cleanup`

### QW-2. `rejection_reason` 원본 보존
- **file:line**: `stage4_reject_runtime.py:342`
- **변경량**: 2줄 (원본 verdict_reason 저장 + merged_feedback 별도 필드)
- **위험**: ChiefWriter 소비측 `previous_attempt["rejection_reason"]` 호환 확인 필요
- **fix type**: `contract-cleanup`

### QW-3. Stage 4 콘솔 reject 표시 `[:100]` 제거
- **file:line**: `stage4_reject_runtime.py:545`
- **현상**: `director_feedback[:100]...` — console-log-max-display SSOT 정책 위반
- **변경량**: 1줄 (슬라이싱 제거)
- **위험**: 콘솔 출력 길이 증가 (운영 정책상 의도된 방향)
- **fix type**: `observability-only`

### QW-4. `failure_learner` / `adaptive_manager` / `quality_dashboard` 피드백 절삭 제거
- **file:line**: `stage4_reject_runtime.py:565,577,601`
- **현상**: `director_feedback[:150]`, `[:200]`, `[:200]` — 내부 학습/적응 시스템에 전달되는 피드백이 절삭됨
- **변경량**: 3줄
- **위험**: failure_learner reason 필드가 무한정 커질 수 있으므로 `[:500]` 정도로 완화 권장
- **fix type**: `observability-only`

### QW-5. Stage 3 reject_reason 콘솔 절삭 완화
- **file:line**: `stage3_orchestrator.py:2372`
- **현상**: `_reject_reason[:140]` — Stage 3 REJECT 사유가 140자로 잘려 운영자가 원인 파악 어려움
- **변경량**: 1줄
- **fix type**: `observability-only`

---

## 5. Boundary Refactor Candidates

### BR-1. Stage 2 feedback_provenance 체계 도입
- **현재**: Stage 2 REJECT 시 `reject_reason` + `base_feedback` 문자열만 전달
- **제안**: Stage 4의 `_build_retry_feedback_provenance()` 패턴을 Stage 2에 이식. `audit` dict에서 contradiction_details, score_breakdown, fix_scope 등을 추출하여 구조화된 feedback_provenance dict로 조립.
- **범위**: `stage2_finalizer.py:1538-1632` + FourPhaseArcRuntime 소비측
- **fix type**: `boundary-refactor`

### BR-2. Stage 3 rejection history → ThreePhaseBlueprintRuntime 피드백 연결
- **현재**: `_append_stage3_rejection_history()`가 app-level list에 저장하지만, `reason[:200]`으로 절삭됨. 다음 시도에서 이 히스토리가 ThreePhaseBlueprintRuntime에 **어떻게** 전달되는지 명시적 계약이 없음.
- **제안**: Stage 3 retry 시 직전 rejection_history를 pipeline_config에 명시적으로 전달하는 계약 추가. 현재는 blueprint generation이 이전 실패를 인지하는 경로가 간접적(app.stage_rejection_history).
- **fix type**: `boundary-refactor`

### BR-3. `_compact_attempt_snapshot` 절삭 정책 SSOT화
- **현재**: 각 필드의 절삭 한도가 `_compact_attempt_snapshot` 내 하드코딩 (200/240/3건/5건 등)
- **제안**: 절삭 한도를 `system.yaml` 또는 constants.py에 모아서 SSOT화. max-retention 정책과 일관성 확보.
- **fix type**: `boundary-refactor`

---

## 6. Fresh-Run Relevance

**Fresh-run-before-fix allowed: no**

| # | Finding | Fix-Before-Rerun | 근거 분류 |
|---|---------|------------------|-----------|
| 1 | rejection_reason 원본 손실 (P1-1) | **yes** | LLM-Director 정합성 불일치 |
| 2 | contradiction_details 축소 (P1-2) | **yes** | LLM-Director 정합성 불일치 |
| 3 | 다단계 절삭 누적 (P1-3) | **yes** | 컨텍스트 손실 |
| 4 | Stage 2 피드백 구조화 부재 (P1-4) | recommended | 피드백 루프 단절 |

**Top 3 highest-ROI code fixes before next fresh run:**

1. **P1-1 rejection_reason 원본 보존** (`stage4_reject_runtime.py:342`) — 2줄 변경, ChiefWriter가 정확한 reject 사유를 받아 교정 적중률 향상
2. **P1-2 contradiction_details[:3] → [:5]** (`stage4_reject_runtime.py:365`) — 1줄 변경, 다중 모순 시 교정 누락 방지
3. **QW-3 콘솔 reject 표시 절삭 제거** (`stage4_reject_runtime.py:545`) — 1줄 변경, 운영자 판단 근거 즉시 확보, console-log-max-display 정책 정합

---

## 7. Confidence And Limits

**Estimated confidence: 96%**

Basis:
- Stage 4 feedback flow는 `_build_retry_feedback_provenance()` → `_build_reject_guidance_payload()` → `_build_reject_retry_snapshot()` → `ChiefWriter._build_regeneration_feedback()` 전 경로를 source-level로 추적 완료
- Stage 2 feedback flow는 `_handle_stage2_reject_path()` → `director_feedback_for_fourphase` 경로를 source-level로 추적 완료
- Stage 3 feedback flow는 `_build_stage3_reject_reason()` → `_append_stage3_rejection_history()` 경로를 source-level로 추적 완료
- 기존 `director-pipeline-7axis-deep-dive.md`의 Q4 findings와 cross-reference 완료, 일관성 확인됨

The 4% gap is from:
- Stage 3 rejection_history가 다음 blueprint 생성에서 실제로 어떻게 소비되는지는 `three_phase_blueprint_runtime.py` 내부까지 추적해야 완전 확인 (이번 scope 외) (2%)
- `adaptive_feedback_intensity` 콜백의 실제 구현 상세 미확인 (1%)
- FourPhaseArcRuntime의 `director_feedback_for_fourphase` 소비 상세 미확인 (1%)

---

## 8. Cross-Reference with Prior Reports

| Prior Finding | This Survey | Status |
|---------------|-------------|--------|
| 7-axis deep-dive P1: rejection_reason 필드 손실 | P1-1 재확인 | **live — 미수정** |
| 7-axis deep-dive P1: verdict_reason 500자 절삭 | P1-3 포함 | **live — 미수정** |
| 7-axis deep-dive P1: contradiction_details 5→3건 축소 | P1-2 재확인 | **live — 미수정** |
| console-log SSOT: operator truncation 제거 | QW-3,4 관련 | **pending — SSOT 작성됨, 미실현** |
| fresh-run P1-1: ep5 swap→REJECT cascade | P1-2 관련 (모순 정보 부족이 교정 실패 기여 가능) | **confirmed pattern** |

---

## 9. 3-Pass Audit Record

### Pass 1. Scope and Evidence Gathering
- Stage 4 전체 reject/feedback 경로 (stage4_reject_runtime.py 819줄 전량, stage4_interview_round.py 관련 메서드) source-level 추적 완료
- Stage 2 reject 경로 (stage2_finalizer.py:1538-1632) source-level 추적 완료
- Stage 3 reject 경로 (stage3_orchestrator.py:2089-2618) source-level 추적 완료
- director_auditor.py audit_strategic_plan (L970-1125) source-level 추적 완료
- ChiefWriter feedback 소비 (chief_writer.py:1069-1116) source-level 추적 완료
- PASS

### Pass 2. Finding Classification and Cross-Reference
- P1 4건: 모두 feedback 전달 정확성에 직접 영향, file:line anchor 확인
- P2 5건: 관측성/절삭 완화, console-log SSOT와 정합
- 7-axis deep-dive 기존 findings 3건과 cross-reference — 전부 live 상태 재확인
- fix type 분류 규칙 준수
- PASS

### Pass 3. Fresh-Run Relevance and ROI Ranking
- P1-1, P1-2는 LLM-Director 정합성 불일치 범주로 재실행 전 수정 필수
- Top 3 ROI 순서 합리성 검증: 변경량 대비 효과, 기존 fresh-run 실패 패턴 연관성
- no 코드 수정, no execution SSOT 생성, no temp queue artifact 생성 — hard constraints 준수
- PASS
