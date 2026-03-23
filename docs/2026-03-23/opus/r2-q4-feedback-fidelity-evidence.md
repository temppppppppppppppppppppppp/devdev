Date: 2026-03-23
Document Type: R2 Q4 evidence manifest
Terminal: T4
Canonical Path: `docs/2026-03-23/opus/r2-q4-feedback-fidelity-evidence.md`

---

## Source File Inventory

| File | Lines | R2 Relevance |
|------|-------|-------------|
| `modules/core/stage4_reject_runtime.py` | 823 | **Primary** — P1-1, P1-2 수정 검증. side-effect 잔여 절삭 |
| `modules/core/stage4_interview_round.py` | ~5900 | **Primary** — feedback provenance, compact snapshot, JSONL 로깅 |
| `modules/core/stage3_orchestrator.py` | ~2730 | **Primary** — Stage 3 session logger, rejection history |
| `modules/core/stage4_retry_runtime.py` | ~1076 | Reference — retry lane routing, PASS_WITH_FIX loop |

---

## Fix Verification Evidence (Commit `79f570f2`)

### P1-1: rejection_reason 원본 보존

**Before** (R1 기준):
```python
# stage4_reject_runtime.py L342
"rejection_reason": director_feedback,
```

**After** (live source):
```python
# stage4_reject_runtime.py L342-343
"rejection_reason": director_result.get("verdict_reason") or director_feedback,
"merged_director_feedback": director_feedback,
```

**Verification**: L342의 `director_result.get("verdict_reason")` → Director LLM의 원본 `verdict_reason` 우선. `director_feedback`는 fallback (verdict_reason 미제공 시). `merged_director_feedback`로 합성 피드백도 별도 보존.

### P1-2: contradiction_details 전량 보존

**Before**:
```python
# stage4_reject_runtime.py L365
"contradiction_details": list(director_result.get("contradiction_details", []) or [])[:3],
```

**After** (live source L367-368):
```python
# [pre-rerun] 모순 세부사항 전량 보존 (이전: [:5] 상한으로 진단 손실)
"contradiction_details": list(director_result.get("contradiction_details", []) or []),
```

**Verification**: `[:3]` 슬라이싱 완전 제거. 주석에 변경 의도 명시.

### P1-3a: _compact_attempt_snapshot 필드 절삭 제거

**Before** (R1 기준):
```python
"fix_scope_reasoning": str(...)[:200],
"open_review": str(...)[:200],
"rejection_reason": str(...)[:240],
"action_items": list(...)[:3],
```

**After** (live source L1149-1164):
```python
"fix_scope_reasoning": str(previous_attempt.get("fix_scope_reasoning", "") or ""),
"open_review": str(previous_attempt.get("open_review", "") or ""),
"rejection_reason": str(previous_attempt.get("rejection_reason", "") or ""),
"action_items": list(previous_attempt.get("action_items", []) or []),
```

```python
# contradiction_details (L1161-1164)
contradiction_details = Stage4InterviewRound._compact_contradiction_detail_lines(
    previous_attempt.get("contradiction_details"),
    max_items=None,       # ★ 건수 무제한
    line_limit=120,       # 건당 120자 (포맷팅 한도)
)
```

**Verification**: 모든 `[:N]` 슬라이싱 제거. `contradiction_details`도 `max_items=None`으로 건수 무제한.

### P1-3b: retry_directives 구조 보존

**Before**:
```python
# stage4_interview_round.py L649
retry_directives = " / ".join(prev_general_lines)
```

**After** (live source L649-650):
```python
# [pre-rerun] 구조 보존: " / " 평탄화 → 줄바꿈 유지
retry_directives = "\n".join(prev_general_lines)
```

**Verification**: `" / "` → `"\n"` 변경으로 Director 지시의 줄 단위 구조 보존.

### P1-3c: validation_warnings 상한 확대

**Before** (R1 기준):
```python
"validation_warnings": owner._collect_validation_warning_lines(validation_results, limit=20),
```

**After** (live source L355):
```python
# [pre-rerun] 검증 경고 상한 완화 (이전: 20건 → 50건)
"validation_warnings": owner._collect_validation_warning_lines(validation_results, limit=50),
```

### evidence_summary 비절삭 확인

Live source L642-644:
```python
evidence_summary = ""
if evidence_lines:
    evidence_summary = "[근거 요약 - 수정 시 반드시 반영]\n" + "\n".join(f"  {line}" for line in evidence_lines)
```

No truncation. T5 H-6 `evidence_summary` 절삭은 DB 저장 경로(L5461 `_compact_text`)에만 해당.

---

## Fresh-Run Evidence

### DB stage_attempts.reject_reason 길이 확인

Source: `projects/0_0323/project_data.db`

```sql
SELECT attempt_key, verdict, score, length(reject_reason) as rr_len
FROM stage_attempts WHERE stage=4 AND verdict='REJECT'
```

| attempt_key | verdict | score | reject_reason 길이 |
|-------------|---------|-------|-------------------|
| s4:ep3:arc1:a1:20260323_134135 | REJECT | 80 | **2,576** |
| s4:ep3:arc1:a3:20260323_134135 | REJECT | 76 | **4,338** |
| s4:ep3:arc1:a4:20260323_134135 | REJECT | 98 | **3,394** |

500자 이상 전량 저장 확인. Python 절삭 없음.

### JSONL episode_production.jsonl feedback_provenance 필드 길이

Source: `projects/0_0323/logs/episode_production.jsonl`

| Round | director_feedback | runtime_advisory | retry_directives |
|-------|-------------------|------------------|-----------------|
| ep1 R0 PASS | 219 | 377 | 0 |
| ep2 R0 PASS | 183 | **500** ★ | 0 |
| ep3 R0 REJECT | 461 | **500** ★ | 0 |
| ep3 R2 REJECT | 444 | **500** ★ | **500** ★ |
| ep3 R3 PASS | 223 | **500** ★ | **500** ★ |
| ep3 R4 PASS | 202 | **500** ★ | 0 |

★ = 정확히 500자 → `_compact_text(value, 500)` 절삭 활성 (L5461-5463)

### Artifact Directory Structure

```
projects/0_0323/logs/artifacts/stage4/
  ep_0001/attempt_01/  → PASS artifacts
  ep_0002/attempt_01/  → PASS artifacts
  ep_0003/
    attempt_01/  → rejected_best__C.txt (REJECT, 80)
    (attempt_02 absent — patch 전량 실패)
    attempt_03/  → rejected_best__A.txt (REJECT, 76)
    attempt_04/  → selected_candidate__A_asp_correction.txt (post-select REJECT, 98)
    attempt_05/  → PASS artifacts
```

---

## Remaining Truncation Inventory (R2)

### Core Pipeline (RESOLVED — 0건)

핵심 피드백 파이프라인(Director → reject_guidance → retry_snapshot → ChiefWriter)에서 절삭 0건.

### Logging/Observability Path (PERSISTS — downgraded to P2)

| Location | Field | Limit | Severity | Path |
|----------|-------|-------|----------|------|
| `stage4_reject_runtime.py:548` | `director_feedback` (console) | `[:100]` | P2 | operator display |
| `stage4_reject_runtime.py:568` | `director_feedback` (failure_learner) | `[:150]` | P2 | learning system |
| `stage4_reject_runtime.py:580` | `director_feedback` (adaptive_manager) | `[:200]` | P2 | adaptation |
| `stage4_reject_runtime.py:604` | `director_feedback` (quality_dashboard) | `[:200]` | P2 | dashboard |
| `stage4_interview_round.py:399` | `reason` (session logger) | `_compact_text(500)` | P3 | session JSONL |
| `stage4_interview_round.py:400` | `selection_reason` (session logger) | `_compact_text(500)` | P3 | session JSONL |
| `stage4_interview_round.py:401` | `verdict_reason` (session logger) | `_compact_text(500)` | P3 | session JSONL |
| `stage4_interview_round.py:403` | `open_review` (session logger) | `_compact_text(300)` | P3 | session JSONL |
| `stage4_interview_round.py:419` | `runtime_advisory` (session logger) | `_compact_text(500)` | P3 | session JSONL |
| `stage4_interview_round.py:420` | `retry_directives` (session logger) | `_compact_text(500)` | P3 | session JSONL |
| `stage4_interview_round.py:422` | `firewall_reason` (session logger) | `_compact_text(500)` | P3 | session JSONL |
| `stage4_interview_round.py:5461` | `director_feedback` (episode JSONL) | `_compact_text(500)` | P2 | JSONL log |
| `stage4_interview_round.py:5462` | `runtime_advisory` (episode JSONL) | `_compact_text(500)` | P2 | JSONL log |
| `stage4_interview_round.py:5463` | `retry_directives` (episode JSONL) | `_compact_text(500)` | P2 | JSONL log |
| `stage3_orchestrator.py:2260` | `reject_reason` (session logger) | `[:500]` | P3 | session JSONL |
| `stage3_orchestrator.py:2261` | `reason` (session logger) | `[:500]` | P3 | session JSONL |
| `stage3_orchestrator.py:2262` | `selection_reason` (session logger) | `[:500]` | P3 | session JSONL |
| `stage3_orchestrator.py:2263` | `verdict_reason` (session logger) | `[:500]` | P3 | session JSONL |
| `stage3_orchestrator.py:2693` | `reason` (rejection history) | `[:200]` | P2 | retry context |
| `stage3_orchestrator.py:2695` | `specific_issue` (rejection history) | `[:200]` | P2 | retry context |

---

## T-Report Cross-Reference Summary

| T-Report | Finding | Q4 Overlap | R2 Status |
|----------|---------|------------|-----------|
| T5 F-2 | feedback 비수렴 | retry_directives 구조 손실 기여 | resolved |
| T5 F-3 | DB 500자 절삭 | 관측성 측면 | DB TEXT 해소, JSONL 잔여 |
| T5 F-5 | retry_directives " / " | 직접 동일 | resolved |
| T5 F-7 | contradiction_details [:5] | 직접 동일 | resolved (전량 보존) |
| T5 QW-1 | " / " → "\n" | 직접 동일 | resolved |
| T6 P1-1 | Blueprint timeline → retry storm | 간접 (피드백 품질이 수렴에 영향) | 개선됨 |
| T7 F-1 | Post-select PASS→REJECT | rejection_reason 보존 | verdict_reason 우선 보존으로 부분 해소 |
| 7-axis H-1 | rejection_reason 필드 손실 | 직접 동일 | resolved |
| 7-axis H-2 | contradiction_details 5→3 | 직접 동일 | resolved |
| 7-axis H-3 | verdict_reason 500자 절삭 | 세션 로거 경로 | shifted (핵심 비절삭, 로거만 잔여) |
| 7-axis H-4 | retry_directives " / " | 직접 동일 | resolved |
| 7-axis H-6 | evidence_summary 500자 | JSONL 경로 | shifted (핵심 비절삭) |
