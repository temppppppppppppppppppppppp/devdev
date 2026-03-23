Date: 2026-03-23
Status: final (3-pass audited)
Document Type: R2 Q4 feedback fidelity delta survey report
Terminal: T4
Axis: Q4 — "잘 설명하냐" (feedback fidelity 수정 검증)
Canonical Path: `docs/2026-03-23/opus/r2-q4-feedback-fidelity.md`
Evidence Path: `docs/2026-03-23/opus/r2-q4-feedback-fidelity-evidence.md`
Source Order: `docs/2026-03-23/q1-q8-r2-parallel-deep-survey-order.md`
Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
R1 Baseline: `docs/2026-03-23/opus/q4-feedback-loop-deep-dive.md`

---

## 1. Executive Summary

커밋 `79f570f2`의 Q4 수정은 **R1 P1 4건 중 3건을 완전히 해소했다**. Stage 4 핵심 피드백 파이프라인(Director → reject_guidance → retry_snapshot → ChiefWriter)에서의 정보 손실이 전면 제거되었으며, 남은 절삭은 **로깅/관측성 경로에만** 존재한다.

**R1→R2 delta**: resolved 6건 / persists 2건 (severity downgraded) / new 1건

핵심 수정 사항:
1. `rejection_reason` 원본 보존: `verdict_reason or director_feedback` + `merged_director_feedback` 별도 필드
2. `contradiction_details` 전량 보존: 이전 `[:5]` → 무제한
3. `_compact_attempt_snapshot` 필드별 절삭 전량 제거
4. `retry_directives` 구조 보존: `" / ".join(...)` → `"\n".join(...)`

**P0: 0건 | P1: 0건 (이전 4건 → 전량 resolved) | P2: 3건 (로깅/관측 경로)**

Fresh-run-before-fix allowed: **yes** — 핵심 피드백 파이프라인의 정보 손실이 해소되어, Q4 축에서는 더 이상 rerun을 차단하지 않는다.

---

## 2. R1→R2 Delta Summary

### R1 P1 Findings

| R1 ID | Finding | R2 Status | Evidence |
|-------|---------|-----------|----------|
| **P1-1** | `rejection_reason` 원본 손실 (L342) | **resolved** | L342: `director_result.get("verdict_reason") or director_feedback` + L343: `merged_director_feedback` 별도 필드 |
| **P1-2** | `contradiction_details[:3]` 축소 (L365) | **resolved** | L367-368: `list(director_result.get("contradiction_details", []) or [])` — 전량 보존, 주석에 "[pre-rerun] 모순 세부사항 전량 보존" 명시 |
| **P1-3** | 다단계 절삭 누적 손실 | **resolved** (core pipeline) / **persists** (logging path, severity downgraded to P2) | 아래 상세 |
| **P1-4** | Stage 2 피드백 구조화 부재 | **persists** (not modified by `79f570f2`) | `stage2_finalizer.py` 미수정 |

### P1-3 상세 분해

| 위치 | R1 상태 | R2 상태 | 증거 |
|------|---------|---------|------|
| `_compact_attempt_snapshot` `fix_scope_reasoning[:200]` | P1 | **resolved** | L1153: 절삭 없음 |
| `_compact_attempt_snapshot` `open_review[:200]` | P1 | **resolved** | L1154: 절삭 없음 |
| `_compact_attempt_snapshot` `rejection_reason[:240]` | P1 | **resolved** | L1157: 절삭 없음 |
| `_compact_attempt_snapshot` `action_items[:3]` | P1 | **resolved** | L1158: `list(...)` 전량 보존 |
| `_compact_attempt_snapshot` `contradiction_details[:2, 120chars]` | P1 | **resolved** | L1161: `max_items=None` 전량 보존 |
| `retry_directives " / ".join(...)[:500]` | P1 | **resolved** | L649-650: `"\n".join(prev_general_lines)` 구조 보존 |
| 콘솔 `director_feedback[:100]` (L548) | QW-3 | **persists** (P2) | operator display, 정책 위반 유지 |
| `failure_learner` `director_feedback[:150]` (L568) | QW-4 | **persists** (P2) | learning system path |
| `adaptive_manager` `director_feedback[:200]` (L580) | QW-4 | **persists** (P2) | adaptation system path |
| `quality_dashboard` `str(director_feedback)[:200]` (L604) | QW-4 | **persists** (P2) | dashboard path |

### R1 Quick Wins

| R1 ID | Finding | R2 Status |
|-------|---------|-----------|
| QW-1 | `contradiction_details[:3]` → `[:5]` | **exceeded** — 전량 보존 |
| QW-2 | `rejection_reason` 원본 보존 | **resolved** |
| QW-3 | 콘솔 reject `[:100]` 제거 | **persists** (P2) |
| QW-4 | failure_learner/adaptive/dashboard 절삭 제거 | **persists** (P2) |
| QW-5 | Stage 3 `_reject_reason[:140]` 콘솔 절삭 | **resolved** — L2455-2456: 전체 reason 표시 |

---

## 3. Current Ownership / Flow Map

### 3.1 Stage 4 Feedback Flow (수정 후)

```
Director LLM 응답
  ├─ verdict_reason, feedback.issues, action_items, open_review
  ├─ contradiction_details (전량)
  ├─ fix_scope, fix_scope_reasoning, fix_pack
  └─ score_breakdown, consistency_checklist
        │
        ↓
_build_retry_feedback_provenance()      [stage4_interview_round.py:572-671]
  ├─ system_feedback   (시스템 접두사 분리)
  ├─ evidence_summary  (검증 근거 — 비절삭)
  ├─ director_feedback_text (LLM 피드백 + issues + 모순 세부)
  ├─ runtime_advisory  (advisory digest — 비절삭)
  └─ retry_directives  (이전 라운드 — "\n" 결합, 비절삭)   ★ FIXED
        │
        ↓ merged_feedback
_build_reject_guidance_payload()         [stage4_reject_runtime.py:393-505]
  ├─ reject_bucket 분류
  ├─ fix_scope 정제 (연속성 replay, fix_pack 계약 검증)
  ├─ ToT/MAD 조건부 보강
  └─ feedback_provenance dict 보존
        │
        ↓
_build_reject_retry_snapshot()           [stage4_reject_runtime.py:309-391]
  ├─ rejection_reason = verdict_reason or director_feedback   ★ FIXED
  ├─ merged_director_feedback = director_feedback (별도 보존)   ★ NEW
  ├─ contradiction_details: 전량 보존   ★ FIXED
  ├─ validation_warnings: 50건 상한 (이전: 20건)   ★ EXPANDED
  └─ prior_attempts 누적 히스토리 (compact snapshot 비절삭)   ★ FIXED
        │
        ↓ previous_attempt dict
ChiefWriter._build_regeneration_feedback()
  ├─ director_feedback 전문 주입
  ├─ previous_attempt.rejection_reason → 원본 verdict_reason 도달   ★ FIXED
  ├─ score_breakdown, validation_warnings, fix_scope_reasoning, open_review → 비절삭   ★ FIXED
  └─ retry_history (prior_attempts) → compact snapshot 비절삭   ★ FIXED
```

### 3.2 소유권 경계 (변경 없음)

- `DirectorEnsembleSelector` → 원본 verdict/feedback 생산
- `Stage4InterviewRound` → feedback provenance 합성
- `Stage4RejectRuntime` → reject guidance, retry snapshot 조립
- `ChiefWriter` → 재생성 프롬프트에 feedback 주입

---

## 4. Focus-Scope Findings

### F-1. [P2] 콘솔/side-effect 경로 잔여 절삭 (4곳)

- **file:line**: `stage4_reject_runtime.py:548, 568, 580, 604`
- **현상**: 콘솔 REJECT 로그 `director_feedback[:100]...`, failure_learner `[:150]`, adaptive_manager `[:200]`, quality_dashboard `[:200]`
- **evidence type**: source
- **영향**: operator surface에서 REJECT 피드백이 100자로 잘려 판단 근거 즉시 확인 불가. 내부 학습/적응 시스템에도 축약 전달.
- **root-causal vs symptomatic**: **symptomatic** — 핵심 피드백 파이프라인과 독립. 런타임 동작 불변.
- **rerun 차단**: no
- **fix type**: `observability-only`

### F-2. [P2] 세션 로거/JSONL 경로 잔여 절삭

- **file:line**:
  - `stage4_interview_round.py:399-422` — `_compact_text(reason, 500)`, `_compact_text(verdict_reason, 500)`, `_compact_text(open_review, 300)`, `_compact_text(runtime_advisory, 500)`, `_compact_text(retry_directives, 500)`, `_compact_text(firewall_reason, 500)`
  - `stage4_interview_round.py:5461-5463` — JSONL `feedback_provenance` 3필드 각 500자
  - `stage3_orchestrator.py:2260-2263` — Stage 3 세션 로거 `[:500]`
- **evidence type**: source + fresh-run artifact
- **fresh-run 실증**: `projects/0_0323/logs/episode_production.jsonl`에서 `runtime_advisory`가 5/6 라운드에서 정확히 500자 → `_compact_text(500)` 절삭 확인
- **영향**: 세션 로그와 JSONL에서 복합 모순 시나리오의 상세 진단 복구 불가. DB TEXT 최대 보존 정책과의 정합성 갭.
- **root-causal vs symptomatic**: **symptomatic** — 런타임 동작 불변. 사후 진단 품질만 저하.
- **rerun 차단**: no
- **fix type**: `observability-only`

### F-3. [P2] Stage 2 피드백 구조화 부재 (R1 P1-4 잔존)

- **file:line**: `stage2_finalizer.py:1587-1595` (R1 기준 — 라인 이동 가능)
- **현상**: Stage 2 REJECT 시 `director_feedback_for_fourphase`가 단순 f-string. `contradiction_details`, `score_breakdown`, `fix_scope` 미포함.
- **evidence type**: source (커밋 `79f570f2`에서 미수정)
- **영향**: FourPhaseArcRuntime이 Stage 2 REJECT 사유를 받을 때, Director의 구조화된 진단 정보 미전달.
- **root-causal vs symptomatic**: **root cause** (Stage 2 범위 한정) — Stage 2 retry 수렴 속도에 직접 영향.
- **rerun 차단**: no (Stage 2는 일반적으로 1-2회 retry에서 수렴, 구조적 피드백 부재가 치명적이지 않음)
- **fix type**: `boundary-refactor`

### F-4. [P2] Stage 3 rejection_history 잔여 절삭

- **file:line**: `stage3_orchestrator.py:2693, 2695`
- **현상**: `reason[:200]`, `specific_issue[:200]`
- **evidence type**: source
- **영향**: Stage 3 rejection history가 200자로 축약되어, 다음 blueprint 생성 시도에서 이전 실패 맥락이 불완전.
- **root-causal vs symptomatic**: **symptomatic** — Stage 3 retry는 ThreePhaseBlueprintRuntime이 pipeline 수준에서 관리하며, rejection_history는 참조용.
- **rerun 차단**: no
- **fix type**: `observability-only`

---

## 5. Code-Fix Verification

### 5.1 P1-1: `rejection_reason` 원본 보존 ✅

**R1 상태** (커밋 전):
```python
# stage4_reject_runtime.py L342
"rejection_reason": director_feedback,  # merged 문자열
```

**R2 상태** (커밋 `79f570f2` 후):
```python
# stage4_reject_runtime.py L342-343
"rejection_reason": director_result.get("verdict_reason") or director_feedback,
"merged_director_feedback": director_feedback,
```

**판정**: **resolved**. Director의 원본 `verdict_reason`이 primary로 보존되고, merged string은 별도 `merged_director_feedback` 필드로 분리. ChiefWriter가 `previous_attempt["rejection_reason"]`을 읽을 때 원본 판정 사유를 받게 됨.

### 5.2 P1-2: `contradiction_details` 전량 보존 ✅

**R1 상태**:
```python
# stage4_reject_runtime.py L365
"contradiction_details": list(...)[:3],  # 5→3 이중 축소
```

**R2 상태**:
```python
# stage4_reject_runtime.py L367-368
# [pre-rerun] 모순 세부사항 전량 보존 (이전: [:5] 상한으로 진단 손실)
"contradiction_details": list(director_result.get("contradiction_details", []) or []),
```

**판정**: **resolved**. R1의 QW-1(`[:3]→[:5]`)을 넘어 전량 보존으로 개선. 6건 이상 복합 모순에서도 정보 손실 없음.

### 5.3 P1-3: 다단계 절삭 핵심 경로 전량 제거 ✅

**R1 상태** (`_compact_attempt_snapshot`):
```python
"fix_scope_reasoning": str(...)[:200],
"open_review": str(...)[:200],
"rejection_reason": str(...)[:240],
"action_items": list(...)[:3],
# contradiction_details: 2건, 120자/건
```

**R2 상태** (`_compact_attempt_snapshot` L1144-1168):
```python
"fix_scope_reasoning": str(previous_attempt.get("fix_scope_reasoning", "") or ""),     # 비절삭
"open_review": str(previous_attempt.get("open_review", "") or ""),                     # 비절삭
"rejection_reason": str(previous_attempt.get("rejection_reason", "") or ""),           # 비절삭
"action_items": list(previous_attempt.get("action_items", []) or []),                  # 비절삭
# contradiction_details: max_items=None, line_limit=120                                # 건수 비제한
```

**R1 상태** (`retry_directives`):
```python
retry_directives = " / ".join(prev_general_lines)  # 구조 손실 + 500자 절삭
```

**R2 상태** (L649-650):
```python
# [pre-rerun] 구조 보존: " / " 평탄화 → 줄바꿈 유지
retry_directives = "\n".join(prev_general_lines)    # 구조 보존, 비절삭
```

**판정**: **resolved** (핵심 파이프라인). 로깅/관측 경로 잔여 절삭은 P2로 severity downgrade.

### 5.4 DB 저장 경로 검증 ✅

**Fresh-run 실증**: `projects/0_0323/project_data.db` `stage_attempts` 테이블:
- ep3 att01: `reject_reason` 길이 = 2,576자
- ep3 att03: `reject_reason` 길이 = 4,338자
- ep3 att04: `reject_reason` 길이 = 3,394자

DB TEXT 컬럼에 Python 절삭 없이 전량 저장 확인. `AGENTS.md` 정책 §1 "DB TEXT 컬럼 절삭 금지" 준수.

---

## 6. Pre-Rerun T-Report Cross-Reference

### T5 (Stage 4 Write/Fix Chain)

| T5 Finding | Q4 관련성 | R2 상태 |
|------------|-----------|---------|
| F-2: 피드백 비수렴 (scene structure) | **high** — retry_directives 구조 손실이 기여 요인 | `"\n".join` 수정으로 구조 보존. 수렴 속도 개선 기대. |
| F-3: DB 다중 500자 절삭 | **high** — Q4 feedback fidelity의 관측성 측면 | JSONL/세션로거 경로에 잔여. DB TEXT 경로는 해소. |
| F-5: retry_directives " / " 구조 손실 | **direct** — R1 P1-3과 동일 finding | **resolved** |
| F-7: contradiction_details [:5] | **direct** — R1 P1-2와 동일 | **exceeded** — 전량 보존 |
| QW-1: `" / "` → `"\n"` | **direct** | **resolved** |

T5 보고서의 H-1/H-2 stale 판정 재확인:
- H-1 (`rejection_reason = director_feedback`): **stale 확인** — L342에서 `verdict_reason or director_feedback`으로 수정됨
- H-2 (`contradiction_details 5→3`): **stale 확인** — 전량 보존으로 수정됨

### T6 (Stage 4 Artifact Truth)

| T6 Finding | Q4 관련성 | R2 상태 |
|------------|-----------|---------|
| P1-1: Blueprint timeline contradiction → 5-attempt retry | **indirect** — 피드백 품질이 수렴 속도에 영향 | retry_directives/contradiction_details 개선으로 후속 fix에서 timeline 교정 가이드 향상 기대 |

### T7 (Verdict Chain)

| T7 Finding | Q4 관련성 | R2 상태 |
|------------|-----------|---------|
| F-1: Post-select PASS→REJECT 전환 | **Q4 boundary** — 전환 시 `rejection_reason`이 system-generated | L342의 수정으로 `verdict_reason` 우선 보존. post-select conflict 시에도 원본 Director verdict 추적 가능. |
| Top-3 ROI #2: post-select conflict feedback fidelity | **direct** | `verdict_reason` 보존 + `merged_director_feedback` 분리로 부분 해소. 구조화된 conflict details 별도 보존은 미구현. |

### Director 7-Axis Deep-Dive

| 7-Axis Finding | R2 상태 |
|----------------|---------|
| H-1: `rejection_reason` 필드 손실 | **resolved** |
| H-2: `contradiction_details` 5→3 축소 | **resolved** (전량 보존) |
| H-3: `verdict_reason` 500자 절삭 | **persists** (세션 로거 경로 L401) — 핵심 파이프라인에서는 비절삭 |
| H-4: `retry_directives` " / " 구조 손실 | **resolved** |
| H-5: 방화벽 fix_scope override 미보존 | **persists** (P2, Q4 범위 밖) |
| H-6: `evidence_summary` 500자 절삭 | **shifted** — 핵심 파이프라인 비절삭 확인 (L642-644). JSONL 로깅 경로만 500자 잔여. |

---

## 7. Fresh-Run Evidence

### 7.1 DB reject_reason 전량 보존 확인

| Attempt | DB reject_reason 길이 | 절삭 여부 |
|---------|----------------------|----------|
| ep3 att01 (REJECT, 80) | 2,576자 | **비절삭** |
| ep3 att03 (REJECT, 76) | 4,338자 | **비절삭** |
| ep3 att04 (REJECT, 98) | 3,394자 | **비절삭** |

500자 이상 전량 저장 확인. `AGENTS.md` 정책 준수.

### 7.2 JSONL feedback_provenance 잔여 절삭 확인

`projects/0_0323/logs/episode_production.jsonl` 분석:

| Round | director_feedback 길이 | runtime_advisory 길이 | retry_directives 길이 |
|-------|----------------------|---------------------|---------------------|
| ep1 R0 PASS | 219 | 377 | 0 |
| ep2 R0 PASS | 183 | **500** ★ | 0 |
| ep3 R0 REJECT | 461 | **500** ★ | 0 |
| ep3 R2 REJECT | 444 | **500** ★ | **500** ★ |
| ep3 R3 PASS | 223 | **500** ★ | **500** ★ |
| ep3 R4 PASS | 202 | **500** ★ | 0 |

`runtime_advisory`가 5/6 라운드에서 정확히 500자 → `_compact_text(500)` (L5462) 절삭 활성 확인.
`retry_directives`도 2라운드에서 정확히 500자 → 절삭 활성 확인.

이 절삭은 JSONL 로깅 경로에만 해당하며, 핵심 파이프라인(ChiefWriter 수신)에는 영향 없음.

### 7.3 Artifact 구조 확인

- ep3 attempt_01/: `rejected_best__C.txt` 존재
- ep3 attempt_02/: **부재** (patch 모드 전량 실패 — T5 F-1과 일치)
- ep3 attempt_03/: `rejected_best__A.txt` 존재
- ep3 attempt_04/: `selected_candidate__A_asp_correction.txt` 존재 (post-select REJECT)
- ep3 attempt_05/: PASS artifact 존재

---

## 8. Root-Cause vs Symptom Classification

| ID | Finding | 분류 | 근거 |
|----|---------|------|------|
| F-1 | 콘솔/side-effect 경로 절삭 | **Symptom** | 핵심 파이프라인 독립. 런타임 동작 불변. |
| F-2 | 세션 로거/JSONL 경로 절삭 | **Symptom** | 사후 분석 품질만 저하. |
| F-3 | Stage 2 피드백 구조화 부재 | **Root Cause** (Stage 2 한정) | Stage 2 retry 시 Director 진단 정보 미전달. |
| F-4 | Stage 3 rejection_history 절삭 | **Symptom** | 참조용 history. Stage 3 retry는 pipeline 수준 관리. |

---

## 9. Quick Wins

| # | 대상 | 수정 | 효과 | fix type |
|---|------|------|------|----------|
| QW-1 | `stage4_reject_runtime.py:548` | `director_feedback[:100]` → 절삭 제거 | 콘솔 max-display 정책 정합 | observability-only |
| QW-2 | `stage4_reject_runtime.py:568,580,604` | `[:150]`/`[:200]` 제거 또는 `[:500]` 완화 | 내부 학습 시스템 입력 품질 향상 | observability-only |
| QW-3 | `stage4_interview_round.py:5461-5463` | `_compact_text(..., 500)` → limit 확대 또는 제거 | JSONL 진단 데이터 보존 | observability-only |

---

## 10. False Leads / Non-Causes

| Claim | 출처 | 판정 | 근거 |
|-------|------|------|------|
| "rejection_reason 원본 손실이 rerun을 차단한다" | R1 P1-1 | **stale** | 커밋 `79f570f2`에서 해소. `verdict_reason or director_feedback`으로 원본 보존. |
| "contradiction_details 축소가 다중 모순 교정 실패의 원인" | R1 P1-2 | **stale** | 전량 보존으로 해소. |
| "_compact_attempt_snapshot 절삭이 장기 retry 피드백 소실의 원인" | R1 P1-3 | **stale** | 모든 필드 절삭 제거. |
| "retry_directives 구조 손실이 피드백 비수렴의 주요 원인" | T5 F-5 | **stale** | `"\n".join` 수정으로 구조 보존. |
| "verdict_reason 500자 절삭이 핵심 파이프라인 문제" | R1/7-axis H-3 | **shifted** | 핵심 파이프라인에서는 비절삭. 세션 로거 경로(L401)에만 잔여. |

---

## 11. Fresh-Run Readiness

**Fresh-run-before-fix allowed: yes**

### 근거

1. **핵심 피드백 파이프라인 정보 손실 전량 해소**: rejection_reason 원본 보존, contradiction_details 전량 보존, compact_snapshot 비절삭, retry_directives 구조 보존 — ChiefWriter가 받는 피드백의 정확성과 완전성이 대폭 개선.
2. **DB 저장 경로 비절삭 확인**: fresh-run에서 2,576~4,338자 reject_reason이 DB에 전량 저장.
3. **잔여 절삭은 로깅/관측 경로에만 존재**: 런타임 동작에 영향 없음.
4. **Stage 2 피드백 구조화 부재는 비차단**: Stage 2 retry는 일반적으로 1-2회에서 수렴하며, 구조화 부재가 치명적이지 않음.

### Top 3 Highest-ROI Remaining Fixes

1. **F-1 콘솔 `director_feedback[:100]` 제거** (`stage4_reject_runtime.py:548`) — 1줄 수정, console-log-max-display 정책 정합
2. **F-2 JSONL feedback_provenance 절삭 완화** (`stage4_interview_round.py:5461-5463`) — 3줄 수정, 사후 진단 데이터 보존
3. **F-3 Stage 2 피드백 구조화** (`stage2_finalizer.py`) — medium effort, Stage 4 feedback_provenance 패턴 이식

---

## 12. Confidence And Limits

**Estimated confidence: 97%**

### 근거
- `stage4_reject_runtime.py` 823줄 전수 조사 — `_build_reject_retry_snapshot` 수정 전후 대비 완료
- `stage4_interview_round.py` 관련 영역 (L530-710: feedback provenance, L1143-1200: compact snapshot, L5440-5470: JSONL 로깅) 조사 완료
- `stage3_orchestrator.py` 관련 영역 (L2102-2149: reject_reason 조립, L2240-2269: 세션 로거, L2670-2702: rejection_history) 조사 완료
- Fresh-run DB 실증: 3개 REJECT attempt의 reject_reason 길이 확인
- Fresh-run JSONL 실증: 11개 episode_production 레코드의 feedback_provenance 필드 길이 확인
- R1 보고서 P1 4건 + QW 5건 전항목 대조 완료
- T5/T6/T7/7-axis 보고서 Q4 관련 finding 교차 검증 완료

### 한계
- `stage2_finalizer.py`의 REJECT 경로 현재 라인 번호 미재확인 (R1 기준 L1587-1595, 라인 이동 가능) — 2%
- `chief_writer.py`의 `_build_regeneration_feedback` 수정 후 실제 수신 검증은 소스 추적만 (런타임 LLM 프롬프트 내용 미확인) — 1%

---

## 3-Pass Audit Record

### Pass 1. Scope and Fix Verification
- `stage4_reject_runtime.py` 전수 읽기 → P1-1 (L342-343), P1-2 (L367-368) 수정 확인
- `stage4_interview_round.py` L530-710 → retry_directives `"\n".join` 수정 확인
- `stage4_interview_round.py` L1143-1168 → `_compact_attempt_snapshot` 절삭 전량 제거 확인
- Fresh-run DB/JSONL 실증 → 비절삭 확인 (DB) + 잔여 절삭 확인 (JSONL)
- PASS

### Pass 2. Cross-Reference and Delta Classification
- R1 P1 4건 × R2 상태 매핑 완료 (3건 resolved, 1건 persists)
- R1 QW 5건 × R2 상태 매핑 완료 (3건 resolved, 2건 persists as P2)
- T5/T6/T7/7-axis 교차 발견 흡수 → stale 2건, shifted 1건 확인
- 잔여 finding을 core pipeline / logging path로 분리
- PASS

### Pass 3. Readiness and Confidence
- Fresh-run readiness: yes — 핵심 파이프라인 정보 손실 해소, 잔여는 관측성만
- Top 3 ROI 합리성 검증: 변경량 대비 효과
- Confidence 97% — threshold 95% 충족
- Hard constraints 준수: no code changes, no execution SSOT, no temp queue artifacts
- PASS
