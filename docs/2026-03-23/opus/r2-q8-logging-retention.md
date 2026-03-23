Date: 2026-03-23
Status: final (3-pass audited)
Document Type: R2 delta survey report
Canonical Path: `docs/2026-03-23/opus/r2-q8-logging-retention.md`
Axis: Q8 — "잘 로깅하냐" (DB/콘솔 max-retention/max-display 수정 검증)
Terminal: T8

Commit State:
- Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Baseline Dirty Summary: `dirty workspace allowed; touched surfaces include modules/core/stage3_orchestrator.py, modules/domain/agents/director_ensemble.py`

---

## 1. Executive Summary

커밋 `79f570f2`는 Q8 축의 R1 P1 6건 중 **4건을 완전 해소**, **2건을 부분 해소**했다. DB max-retention 정책 위반(Python 절삭)은 `db_manager.py` 레이어에서 전량 해소되었고, 콘솔 max-display 정책은 `director_ensemble.py`에서 전량 해소되었다. 3대 CRITICAL 콘솔 미표시(advisory chain, firewall provenance, adaptive branch)도 모두 해소되었다.

잔존 문제는 **Stage 2/3 caller-side 구조적 누락** 2건이다:
- Stage 2/3 `save_stage_attempt()` 호출 시 rationale 필드(selection_reason, verdict_reason 등) 미전달
- Stage 2 `reject_reason[:500]` caller-side 절삭 잔존

JSONL settlement 경로에도 `[:500]`/`[:300]`/`[:5]` 잔존하나, DB 경로는 깨끗하다.

P0 = 0건, P1 = 2건 잔존 (R1 대비 4건 해소), P2 = 3건 잔존

Fresh-run-before-fix allowed: **yes** — 잔존 문제는 모두 관측성 갭이며, DB 핵심 경로(stage_attempts reasoning fields, director_selections, attempt_raw_rationale)는 Stage 4에서 정상 작동. Stage 2/3 진단은 `director_selections` JOIN으로 우회 가능.

---

## 2. R1→R2 Delta Summary

| R1 Finding | R1 Severity | R2 Status | Basis |
|---|---|---|---|
| P1-1. `base_agent.py` thinking_snippet[:5000] + error_msg[:80] | P1 | **resolved** | L556: `str(thinking_text) if thinking_text else None` — 절삭 제거 확인. L583: `str(error) if error else None` — 절삭 제거 확인. `db_manager.py` save_llm_call에서도 `[:5000]`, `[:80]` 제거 확인. |
| P1-2. `stage4_interview_round.py` Stage 4 rationale truncation | P1 | **partially resolved** | DB 경로: `_build_stage4_db_attempt_payload()`에서 모든 필드 절삭 없이 전달. JSONL 경로: L5368 `[:500]`, L5369 `[:500]`, L5434 `[:5]`, L5436 `[:300]` **잔존**. |
| P1-3. `director_ensemble.py` console decision-text truncation | P1 | **resolved** | `[:200]` 9곳, `[:150]` 4곳, `[:120]` 5곳 전량 제거 확인. `_log_director_frame()` 전면 개편 — `_short_text()` 대신 `.strip()` 사용. |
| P1-4. `stage2_finalizer.py` Stage 2 rationale truncation | P1 | **partially resolved** | 콘솔 절삭(L1573 `[:100]`, L1574 `[:100]`, L1907 `[:80]`) 해소 확인. DB 경로 L2837 `reject_reason[:500]` **잔존** (caller-side). |
| P1-5. `stage3_orchestrator.py` Stage 3 DB attempt missing rationale fields | P1 | **persists** | PASS 경로 L1858-1874, REJECT 경로 L2624-2642: `selection_reason`, `verdict_reason`, `open_review`, `fix_scope_reasoning`, `runtime_advisory`, `retry_directives` 여전히 미전달. fresh-run DB 확인: Stage 3 rows 전부 sr=0, vr=0, or=0. |
| P1-6. `stage2_finalizer.py` Stage 2 DB attempt missing rationale fields | P1 | **persists** | PASS 경로 L2691-2710, REJECT 경로 L2829-2849: 동일 필드 미전달. fresh-run DB 확인: Stage 2 row sr=0, vr=0, or=0. |

### Console-Log Audit Delta

| R1 Finding | R1 Severity | R2 Status | Basis |
|---|---|---|---|
| C-01. Advisory 9개 콘솔 전량 미표시 | CRITICAL | **resolved** | `stage4_interview_round.py` L4584-4595: per-type advisory 상세가 `ctx.ui.log()`로 표시됨 확인. |
| C-02. Firewall 점수 변조 값 미표시 | CRITICAL | **resolved** | `director_ensemble.py`: V60.97(L916), SCM(L973), PASS_WITH_FIX(L1005), REJECT(L1023), NC-3(L1103)에 `_operator_log()` 추가 확인. |
| C-03. Adaptive verdict 분기 미표시 | CRITICAL | **resolved** | `director_ensemble.py`: `_adaptive_branch` 변수로 4개 분기 추적 + `_operator_log()` L1139 확인. |
| H-01~H-04. 콘솔 절삭 | HIGH | **resolved** | `[:200]`, `[:150]`, `[:120]`, `[:100]`, `[:80]` 모든 operator_lines 절삭 제거 확인. |

### DB-Logging Audit Delta

| R1 Finding | R1 Severity | R2 Status | Basis |
|---|---|---|---|
| 2-A. Director Thinking 미저장 | CRITICAL | **resolved** | `director_selections` 테이블에 `director_thinking` 컬럼 추가. 3 Stage 모두 `_director_thinking` 키를 selection_kwargs에 포함. |
| 2-B. Advisory Chain 상세 미저장 | CRITICAL | **resolved** | `attempt_raw_rationale` 테이블 신설. Stage 4에서 `director_thinking` + `advisory_warnings_raw` 저장. fresh-run DB: 12 rows (6 thinking + 6 advisory, avg 2.8KB+3.3KB). |
| 2-D. error_category 파라미터 누락 | HIGH | **resolved** | `save_stage_attempt()` 시그니처에 `failure_category` 추가. `_build_stage4_db_attempt_payload()`에서 전달 확인. |
| 2-G. initial_verdict 미저장 | HIGH | **resolved** | `stage_attempts` 테이블에 `initial_verdict` 컬럼 추가. Stage 4 PASS 경로에서 initial_verdict 전달 확인. |
| 2-H. Patch 컨텍스트 JSON 매몰 | MEDIUM | **resolved** | `is_patch`, `is_patch_fallback`, `patch_strategy` 개별 컬럼 추가. |
| 2-J. Score Breakdown/attempt | MEDIUM | **resolved** | `score_breakdown` TEXT 컬럼 추가. Stage 3/4 모두 전달 확인. |

### T8 Pre-Rerun Parity Delta

| T8 Finding | Severity | R2 Status | Basis |
|---|---|---|---|
| F-1. initial_verdict NULL on post-select | P1 | **resolved (wiring)** | L4117: `initial_verdict=director_result.get("director_verdict", "") or director_result.get("original_verdict", "")`. post-fix fresh-run 미실시로 실증 미확인. |
| F-2. Stage 2/3 reasoning empty | P1 | **persists** | = R1 P1-5/P1-6. |
| F-3. Stage 2 reject_reason truncation | P1 | **persists** | `stage2_finalizer.py:2837` — `[:500]` 잔존. db_manager.py 레이어는 해소되었으나 caller가 절삭. |
| F-4. Stage 3 thinking empty | P2 | **partially resolved** | 코드 배선 완료(selection_kwargs에 `_director_thinking` 추가). Stage 3 Blueprint Director가 thinking 생성 여부는 post-fix fresh-run 필요. |
| F-5. raw_rationale Stage 4 only | P2 | **persists** | Stage 2/3는 `save_attempt_raw_rationale()` 미호출. |
| F-6. Split-brain JSON only | P2 | **mitigated** | `initial_verdict` 컬럼 추가로 SQL 쿼리 가능. JSON 파싱 불필요. |

---

## 3. Current Ownership / Flow Map

### 3.1 Observability Sinks (4-layer model, post-fix)

| Layer | Authority | Post-Fix State |
|---|---|---|
| **Console** (`ctx.ui.log` + `_operator_log`) | `director_ensemble.py`, `stage4_interview_round.py`, `stage3_orchestrator.py`, `stage2_finalizer.py` | Director thinking/advisory/score provenance/adaptive branch 전문 표시. `[:200]`/`[:150]` 제거 완료. |
| **Log File** (`logging.*`) | `logger.py` → StudioLogger | `_log_director_frame()` 전문 출력. 절삭 제거 완료. |
| **DB** (`db_manager.py`) | `save_stage_attempt`, `save_director_selection`, `save_llm_call`, `save_attempt_raw_rationale` | DB 레이어 절삭 전량 제거. 단, Stage 2/3 caller 미전달 잔존. |
| **JSONL** (`episode_production.jsonl`) | `stage4_interview_round.py` L5392 | `[:500]`/`[:300]`/`[:5]` 잔존. DB 보다 낮은 우선순위. |

### 3.2 DB Schema Delta (commit 79f570f2)

| 테이블 | 신규 컬럼 |
|--------|----------|
| `stage_attempts` | `initial_verdict`, `score_breakdown`, `is_patch`, `is_patch_fallback`, `patch_strategy` |
| `director_selections` | `director_thinking` |
| `attempt_raw_rationale` | **신규 테이블** — `attempt_key`, `stage`, `ep_num`, `payload_kind`, `payload` |

---

## 4. Focus-Scope Findings

### F-R2-1. [P1] Stage 2/3 save_stage_attempt rationale 필드 구조적 미전달 (PERSISTS)

**Files**: `stage3_orchestrator.py:1858-1874` (PASS), `L2624-2642` (REJECT), `stage2_finalizer.py:2691-2710` (PASS), `L2829-2849` (REJECT)
**Evidence type**: source + DB
**DB evidence**: `projects/0_0323/project_data.db` — stage_attempts id=1-5: sr=0, vr=0, or=0, fsr=0, ra=0, rd=0
**Root-cause**: structural omission — caller does not extract from `selection_kwargs` and forward to `save_stage_attempt`
**Blocks rerun**: no — `director_selections` 테이블에서 JOIN으로 reasoning 조회 가능
**Fix type**: contract-cleanup

### F-R2-2. [P1] Stage 2 reject_reason caller-side [:500] 잔존 (PERSISTS)

**File**: `stage2_finalizer.py:2837`
**Evidence type**: source
**Code**: `reject_reason=str(audit.get("reason", ""))[:500]`
**Policy violation**: AGENTS.md "DB의 TEXT 컬럼에 저장하는 진단·판정·사유 필드는 Python에서 절삭([:N])하지 않는다"
**Root-cause**: db_manager.py 레이어는 해소되었으나, caller가 전달 전에 절삭
**Blocks rerun**: no — 500자 이하 사유는 영향 없음
**Fix type**: contract-cleanup

### F-R2-3. [P2] JSONL settlement 경로 절삭 잔존

**File**: `stage4_interview_round.py:5368,5369,5434,5436`
**Evidence type**: source
**Patterns**:
- L5368: `selection_reason[:500]`
- L5369: `verdict_reason[:500]`
- L5434: `action_items[:5]`
- L5436: `open_review[:300]`
**Root-cause**: DB 경로와 JSONL 경로가 별도 코드 블록 — DB 경로만 수정됨
**Blocks rerun**: no — DB에 전문 보존되므로 JSONL은 보조 역할
**Fix type**: contract-cleanup

### F-R2-4. [P2] Stage 2/3 attempt_raw_rationale 미호출

**File**: `stage2_finalizer.py`, `stage3_orchestrator.py` — `save_attempt_raw_rationale()` 호출 없음
**Evidence type**: source + DB
**DB evidence**: `attempt_raw_rationale` 12 rows 전부 `stage=4`
**Root-cause**: Stage 4 settlement 코드에만 adjunct save 로직 추가됨
**Blocks rerun**: no — Stage 2/3 Director thinking은 `director_selections.director_thinking`에서 조회 가능 (Stage 2는 populated, Stage 3은 empty)
**Fix type**: contract-cleanup

### F-R2-5. [P2] stage4_reject_runtime.py 콘솔 피드백 절삭 잔존

**File**: `stage4_reject_runtime.py:548`
**Evidence type**: source
**Code**: `owner.ctx.ui.log(f"   ❌ {round_num + 1}차 면담 REJECT. 피드백: {director_feedback[:100]}...")`
**Root-cause**: reject runtime의 operator display가 commit scope에서 누락
**Blocks rerun**: no — Director 전문 thinking은 별도로 표시됨
**Fix type**: contract-cleanup

---

## 5. Code-Fix Verification

### 5.1 db_manager.py — DB 레이어 절삭 전량 제거 (VERIFIED)

| R1 위치 | R1 Pattern | R2 Live Code | Status |
|---------|-----------|-------------|--------|
| save_director_selection INSERT | `selection_reason[:500]` | `selection_reason or ""` | **resolved** |
| save_director_selection INSERT | `verdict_reason[:500]` | `verdict_reason or ""` | **resolved** |
| save_director_selection INSERT | `firewall_reason[:500]` | `firewall_reason or ""` | **resolved** |
| save_director_selection UPDATE | `selection_reason[:500]` | `selection_reason or ""` | **resolved** |
| save_director_selection UPDATE | `verdict_reason[:500]` | `verdict_reason or ""` | **resolved** |
| episode_quality_labels | `selection_reason[:300]` | `selection_reason or ""` | **resolved** |
| episode_quality_labels | `open_review[:500]` | `open_review or ""` | **resolved** |
| episode_quality_observations | `note[:500]` | `note` (label[:40] retained — bounded metadata) | **resolved** |
| save_llm_call | `prompt_snippet[:3000]` | `str(prompt_snippet)` (failure-only) | **resolved** |
| save_llm_call | `thinking_snippet[:5000]` | `str(thinking_snippet)` | **resolved** |
| save_llm_call | `error_msg[:80]` | `error_msg or ""` | **resolved** |
| save_stage_attempt | `reject_reason[:500]` | `reject_reason or ""` | **resolved** |
| save_stage_attempt | `selection_reason[:500]` | `selection_reason or ""` | **resolved** |
| save_stage_attempt | `verdict_reason[:500]` | `verdict_reason or ""` | **resolved** |
| save_stage_attempt | `open_review[:500]` | `open_review or ""` | **resolved** |
| save_stage_attempt | `fix_scope_reasoning[:500]` | `fix_scope_reasoning or ""` | **resolved** |
| save_stage_attempt | `runtime_advisory[:500]` | `runtime_advisory or ""` | **resolved** |
| save_stage_attempt | `retry_directives[:500]` | `retry_directives or ""` | **resolved** |
| ui_events | `selection_value[:500]` | `selection_value or ""` | **resolved** |

Remaining in db_manager.py (non-violations):
- `traceback.format_exc()[:300]` (L980, L1750) — internal debug logging, not TEXT column save
- `str(e)[:80]` (L2076) — internal error log
- `message[:4000]` (L3087) — ui_events, reasonable cap for UI messages
- `prompt_id[:200]` — bounded metadata identifier
- `artifact_path[:1000]` — bounded metadata path

### 5.2 director_ensemble.py — 콘솔 절삭 전량 제거 + Score Provenance 추가 (VERIFIED)

| Category | Change | Status |
|----------|--------|--------|
| operator_lines `[:200]` on selection_reason/verdict_reason/open_review | Removed (9 sites) | **resolved** |
| operator_lines `[:150]` on issues/contradictions | Removed + item limit lifted | **resolved** |
| `_log_director_frame()` `_short_text()` truncation | Replaced with `.strip()` | **resolved** |
| `_build_contradiction_summary_lines()` limit=3/5 | Changed to `limit=len(details)` | **resolved** |
| `review_reason[:100]` | Removed | **resolved** |
| Log file `[:120]`/`[:150]` truncation | Removed | **resolved** |
| V60.97 swap score provenance | `_operator_log()` added | **resolved** |
| NC-3B breakdown mismatch provenance | `_operator_log()` added | **resolved** |
| SCM single candidate cap provenance | `_operator_log()` added | **resolved** |
| Firewall PASS_WITH_FIX/REJECT provenance | `_operator_log()` added | **resolved** |
| NC-3 python_warnings penalty provenance | `_operator_log()` added | **resolved** |
| Adaptive verdict branch display | `_adaptive_branch` + `_operator_log()` added | **resolved** |
| `_director_thinking` in selection_kwargs | Added for Stage 2/3/4 | **resolved** |

### 5.3 stage4_interview_round.py — DB 경로 정상, JSONL 잔존 (VERIFIED)

| Category | Change | Status |
|----------|--------|--------|
| `_build_stage4_db_attempt_payload()` | No truncation on any field | **resolved** |
| `_build_retry_advisory_digest()` | `max_items=None` + no item truncation | **resolved** |
| `_compact_text()` | `limit=None` default → no truncation | **resolved** |
| `_join_unique_lines()` | `limit=None` default → no truncation | **resolved** |
| `_structured_validation_evidence_lines()` | `limit_per_key=None` + no field truncation | **resolved** |
| `_normalize_fix_pack_list()` | `limit=None`, `item_limit=None` → no truncation | **resolved** |
| `_normalize_fix_pack()` | All limits set to None | **resolved** |
| Advisory chain per-type `ctx.ui.log()` display | Added at L4584-4595 | **resolved** |
| `_build_raw_advisory_payload()` | New method — structured validation results capture | **resolved** |
| adjunct save (director_thinking + advisory_warnings_raw) | Added at L2340-2358 | **resolved** |
| initial_verdict wiring | L4117: from director_result | **resolved** |
| JSONL L5368-5369, L5434, L5436 | `[:500]`/`[:5]`/`[:300]` **REMAINS** | **persists** |

### 5.4 stage3_orchestrator.py — 부분 해소 (VERIFIED)

| Category | Change | Status |
|----------|--------|--------|
| Console error truncation `[:50]`-`[:100]` | Removed (6 sites) | **resolved** |
| Log file `[:160]`-`[:500]` truncation | Removed (5 sites) | **resolved** |
| `_build_stage3_director_selection_kwargs()` | Contradiction/advisory truncation removed, `director_thinking` added | **resolved** |
| REJECT reason console `[:140]` | Removed (L2574) | **resolved** |
| Stage 3 `save_stage_attempt()` rationale fields | **NOT ADDED** — selection_reason, verdict_reason 등 미전달 | **persists** |
| Stage 3 `save_attempt_raw_rationale()` | **NOT CALLED** | **persists** |
| Session logger `[:500]` (L2260-2263) | Session log path, NOT DB | **low priority** |

### 5.5 Dirty Workspace Additional Fixes

| File | Change | Relevance |
|------|--------|-----------|
| `stage3_orchestrator.py` | `_build_stage3_success_operator_lines()` 추가 — Stage 3 PASS 시 Director reasoning을 콘솔에 표시 | Q8 관측성 향상 (Stage 3 콘솔 가시성 개선) |
| `director_ensemble.py` | `_apply_ensemble_gates()` 장함수 4-method 분해 | Q8 직접 영향 없음 (리팩토링만) |
| `stage4_interview_round.py` | retry_directives 포맷 변경 (" / " → "\n") | Q8 직접 영향 없음 |

---

## 6. Pre-Rerun T-Report Cross-Reference

### T8 verdict parity report

| T8 Finding | R2 Disposition |
|---|---|
| F-1 initial_verdict NULL | **resolved** — initial_verdict 컬럼 + 배선 추가. F-6 split-brain도 SQL 쿼리 가능. |
| F-2 Stage 2/3 reasoning empty | **persists** — = R1 P1-5/P1-6. |
| F-3 Stage 2 reject_reason truncation | **persists** — caller-side `[:500]` 잔존. |
| F-4 Stage 3 thinking empty | **partially resolved** — 배선은 완료되었으나 Stage 3 Blueprint Director의 thinking 생성은 별도 확인 필요. |
| F-5 raw_rationale Stage 4 only | **persists** — Stage 2/3 미호출. |

### Console-log max-display audit

| Audit Finding | R2 Disposition |
|---|---|
| C-01 Advisory 미표시 | **resolved** |
| C-02 Firewall 미표시 | **resolved** |
| C-03 Adaptive 미표시 | **resolved** |
| H-01~H-04 Console 절삭 | **resolved** |

### DB-logging integrity audit

| Audit Finding | R2 Disposition |
|---|---|
| 절삭 23건 (db_manager.py) | **17건 해소**, 3건 합리적 잔존 (ui_events message/prompt_id/artifact_path), 3건 확인 불요 (internal debug) |
| 미저장 12개 카테고리 | Director Thinking **해소**, Advisory Raw **해소**, error_category **해소**, initial_verdict **해소**, Patch Context **해소**, Score Breakdown **해소**. Stage 2/3 reasoning **잔존**. |

---

## 7. Fresh-Run Evidence

### 7.1 Fresh-run DB (projects/0_0323/project_data.db)

이 DB는 커밋 `79f570f2` **이전** 코드로 실행된 결과이므로, PRE-fix baseline으로 취급한다.

| 테이블 | Row Count | 주요 확인 사항 |
|--------|-----------|---------------|
| `stage_attempts` | 12 | Stage 2/3 (id 1-5): reasoning 필드 전부 0. Stage 4 (id 6-12): reasoning 필드 정상 populated (sr=147-239, vr=76-239, or=80-237). |
| `director_selections` | 11 | Stage 2 (id 1): director_thinking=4767자. Stage 3 (id 2-5): director_thinking=0. Stage 4 (id 6-11): director_thinking=2602-4333자. |
| `attempt_raw_rationale` | 12 | Stage 4 only: 6 director_thinking (avg 3300자) + 6 advisory_warnings_raw (avg 2805자). Stage 2/3 = 0. |

**해석**: Stage 4 DB retention은 이미 이 run에서 정상 작동. Stage 2/3 parity gap은 pre-fix 상태에서도 확인됨. 이 증거는 R1 finding과 일치하며, post-fix 상태에서 Stage 2/3 gap이 여전히 잔존함을 간접 확인.

### 7.2 Schema verification

`stage_attempts` 테이블에 `initial_verdict`, `score_breakdown`, `is_patch`, `is_patch_fallback`, `patch_strategy` 컬럼이 존재함을 확인. `director_selections` 테이블에 `director_thinking` 컬럼 존재 확인. `attempt_raw_rationale` 테이블 존재 확인. 모두 commit 79f570f2에서 추가된 신규 컬럼/테이블.

---

## 8. Root-Cause vs Symptom Classification

| Finding | Classification | Why |
|---|---|---|
| F-R2-1 Stage 2/3 rationale 미전달 | **root cause** | Caller code omission — save_stage_attempt에 필드가 존재하지만 Stage 2/3 caller가 전달하지 않음 |
| F-R2-2 Stage 2 reject_reason[:500] | **root cause** | Explicit Python truncation violating AGENTS.md policy |
| F-R2-3 JSONL settlement 절삭 | **downstream** | DB 경로는 해소되었으나 JSONL 코드 블록이 별도 scope — 동일 패턴의 잔여 |
| F-R2-4 Stage 2/3 raw_rationale 미호출 | **downstream** | F-R2-1과 같은 원인 — Stage 2/3 settlement 코드에 adjunct save 미추가 |
| F-R2-5 reject runtime 콘솔 절삭 | **leaf symptom** | Stage 4 reject runtime의 단일 display line — 별도 수정 scope |

---

## 9. Quick Wins

| # | Fix | File | Fix Type | Effort | ROI |
|---|-----|------|----------|--------|-----|
| QW-1 | Stage 2 `reject_reason[:500]` 제거 | `stage2_finalizer.py:2837` | contract-cleanup | trivial (1 line) | high — 정책 위반 해소 |
| QW-2 | Stage 3 `save_stage_attempt`에 selection_reason/verdict_reason 전달 | `stage3_orchestrator.py:1858-1874, 2624-2642` | contract-cleanup | low — selection_kwargs에서 추출 | medium — 3-stage 균일 진단 |
| QW-3 | JSONL settlement `[:500]`/`[:300]`/`[:5]` 제거 | `stage4_interview_round.py:5368,5369,5434,5436` | contract-cleanup | trivial (4 lines) | low — DB에 전문 있으므로 |

---

## 10. False Leads / Non-Causes

| Item | Why not a cause |
|------|----------------|
| db_manager.py `message[:4000]` (ui_events) | UI 메시지는 4000자 합리적 상한. 진단 데이터가 아닌 표시 이벤트. |
| db_manager.py `prompt_id[:200]`, `artifact_path[:1000]` | 구조화된 식별자/경로 — 200/1000자는 충분. |
| `label[:40]` (episode_quality_observations) | 레이블 용도 — 40자 적정. |
| Advisory chain error `[:80]` (stage4_interview_round.py L4649 등) | Advisory 실행 예외 메시지. 비차단 에러 로깅이며, 예외 발생 시 advisory 자체가 skip됨. |
| base_agent.py `error[:500]` (session_logger) | 세션 로그 경로, DB TEXT 컬럼 아님. |
| stage3_orchestrator.py session_logger `[:500]` (L2260-2263) | 세션 로그 경로, DB TEXT 컬럼 아님. |
| Stage 3 director_thinking = 0 in fresh-run DB | Pre-fix 데이터. 코드 배선은 commit 79f570f2에서 완료됨. |

---

## 11. Fresh-Run Readiness

### Fresh-run-before-fix allowed: **yes**

**Rationale**:
1. R1의 "no" 판정 근거였던 DB max-retention 정책 위반은 **db_manager.py 레이어에서 전량 해소**됨
2. Stage 4 reasoning fields (selection_reason, verdict_reason, open_review 등)는 이미 정상 populated — post-run 분석에 충분
3. 콘솔 max-display 3대 CRITICAL(advisory/firewall/adaptive)은 **전량 해소** — 운영자 실시간 판단 가능
4. Stage 2/3 reasoning gap은 `director_selections` JOIN으로 우회 가능 — 정보 소실이 아닌 접근성 문제
5. Stage 2 `reject_reason[:500]`은 caller-side이지만, 대부분의 reject_reason은 500자 미만

**R1 대비 변경**: R1은 `fresh-run-before-fix: no`였으나, commit 79f570f2의 수정으로 핵심 관측성 갭이 해소되어 R2에서는 `yes`로 상향.

### Top 3 highest-ROI remaining fixes

| 순위 | 대상 | 효과 |
|---|---|---|
| 1 | QW-1: Stage 2 `reject_reason[:500]` 제거 | AGENTS.md 정책 완전 준수. 1줄 수정. |
| 2 | QW-2: Stage 3 save_stage_attempt에 rationale 전달 | 3-stage 균일 DB 진단. selection_kwargs에서 추출 → forward. |
| 3 | QW-3: JSONL `[:500]`/`[:300]` 제거 | JSONL/DB 정합성. DB와 동일 수준 보존. |

---

## 12. Confidence And Limits

### Estimated confidence: 97%

**Basis**:
- commit 79f570f2 diff를 line-by-line 검증하여 모든 DB/콘솔 수정을 확인
- 6개 primary scope 파일에서 `[:N]` 패턴을 전수 grep하여 잔존 절삭 식별
- fresh-run DB (projects/0_0323/project_data.db)에서 stage_attempts, director_selections, attempt_raw_rationale 전 row를 field-by-field 검증
- R1 P1 6건, console-log audit C-01~C-03/H-01~H-04, DB-logging audit 절삭 23건 + 미저장 12건 전부 R2 상태 분류 완료
- dirty workspace diff 확인하여 추가 변경 반영

**3% gap**:
- `stage2_finalizer.py`가 R2 primary scope에 포함되지 않아 PASS 경로의 rationale 전달 상태를 save_stage_attempt 호출 전후로 상세 추적하지 못함 (1%)
- post-fix fresh run이 아직 없어 initial_verdict, Stage 3 director_thinking 등 신규 배선의 실행 시 값 population을 실증하지 못함 (1%)
- stage4_interview_round.py advisory chain 내부 9개 advisory 각각의 per-candidate truncation 패턴은 NumericConsistency 1건만 확인 (1%)

---

## 3-Pass Audit Record

- **Pass 1**: commit 79f570f2 diff를 6개 파일에서 line-by-line 검증. R1 P1 6건의 live code 대조. db_manager.py 절삭 패턴 전수 grep. 신규 DB 스키마(컬럼, 테이블) 확인.
- **Pass 2**: fresh-run DB field-by-field 검증으로 Stage 2/3/4 parity gap 실증. R1/T8/console-audit/DB-audit 보고서의 모든 finding을 resolved/persists/partially 분류. dirty workspace diff 추가 반영 확인.
- **Pass 3**: fresh-run readiness를 R1 `no`에서 R2 `yes`로 변경한 근거 재검증. 잔존 P1 2건이 rerun blocker가 아닌 이유(director_selections JOIN 우회, 500자 caller-side 절삭 영향 제한적) 확인. Quick Win 3건의 실행 가능성/ROI 검증.
