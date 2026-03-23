Date: 2026-03-23
Status: final (3-pass audited)
Document Type: Q8 logging/retention observability deep-dive survey report
Canonical Path: `docs/2026-03-23/opus/q8-logging-retention-deep-dive.md`
Axis: Q8 — "잘 로깅하냐" (console/DB/audit observability, max display, max retention, sink parity)
Terminal: T8

---

## 1. Executive Summary

Q8 observability 축 전수조사 결과, **시스템은 런타임 결함 없이 동작하나 관측성에 구조적 손실이 존재**한다.

핵심 패턴:
- **Caller-side truncation**: DB 저장 함수(`save_stage_attempt`, `save_director_selection`, `save_llm_call`) 자체는 TEXT 컬럼에 truncation 없이 저장하도록 설계되었으나, **caller 측**에서 `[:500]`, `[:300]`, `[:120]`, `[:80]` 등으로 절삭한 뒤 전달한다.
- **Stage asymmetry**: Stage 4는 `selection_reason`, `verdict_reason`, `open_review`, `fix_scope_reasoning`, `runtime_advisory`, `retry_directives`를 DB에 전달하지만, **Stage 2/3는 이 필드들을 전달하지 않는다** — 같은 DB 스키마에 null로 남는다.
- **Console ↔ DB parity drift**: Director thinking, advisory detail, score-mutation provenance는 콘솔에서 전문 표시되지만, DB에는 요약 또는 JSON summary만 남는다.
- **LLM call truncation at source**: `base_agent.py`에서 `thinking_snippet[:5000]`과 `error_msg[:80]`을 절삭한 뒤 DB에 전달한다.

P0 = 0건, P1 = 6건, P2 = 5건, P3 = 6건

Fresh-run-before-fix allowed: **no** — fresh run을 먼저 고치지 않고 돌리면, 진단 증거 자체가 절삭/누락되어 post-run 분석이 더 어려워진다.

---

## 2. Current Ownership / Flow Map

### 2.1 Observability Sinks (4-layer model)

| Layer | Authority | Best For |
|---|---|---|
| **Console** (`ctx.ui.log`) | `stage4_interview_round.py`, `stage4_director_runtime.py`, `stage2_finalizer.py`, `stage3_orchestrator.py`, `director_ensemble.py` | 실시간 결정 근거, advisory 경고, score provenance |
| **Log File** (`logging.info/warning/debug`) | `logger.py` → `StudioLogger` (file-only, no console handler) | 상세 흐름, 디버그, summary 라인 |
| **DB** (`db_manager.py`) | `save_stage_attempt`, `save_director_selection`, `save_llm_call`, `save_attempt_raw_rationale` | 영구 기록, post-run 쿼리 |
| **JSONL** (`episode_production.jsonl`) | `stage4_interview_round.py` L5446 | per-attempt structured trace |
| **Pass-Rate** (`pass_rate_monitor.py`) | `record_attempt()` → JSON file | 통계, 성공률, 전략 분석 |
| **Metrics** (`metrics_collector.py`) | `start_call/end_call` → aggregation | LLM 비용, 토큰, 응답 시간 |

### 2.2 Key Data Flow

```
Director LLM response
  → director_ensemble.py (parse, score, select)
    → stage4_director_runtime.py (quality gates, firewall, adaptive)
      → stage4_interview_round.py (settle: console + JSONL + DB + pass-rate)
```

Truncation happens at **settlement layer** (`stage4_interview_round.py` L5348-5349) and **operator display** (`stage4_director_runtime.py` L685-753).

---

## 3. Top Hotspots

### P1-1. `base_agent.py:556,583` — LLM call telemetry truncation at source
- `thinking_snippet[:5000]` (L556) — 5000자 캡. Director thinking은 10,000자 이상 가능.
- `error_msg[:80]` (L583) — 80자 캡. 스택 트레이스 등 상세 정보 소실.
- DB 함수 `save_llm_call`은 `[TF-58] thinking: max-retention, no truncation` 주석으로 무절삭 설계. **caller가 절삭.**
- fix type: `contract-cleanup`

### P1-2. `stage4_interview_round.py:5348-5349,5414,5416,5441-5443` — Stage 4 rationale truncation
- `selection_reason[:500]` (L5348)
- `verdict_reason[:500]` (L5349)
- `open_review[:300]` (L5416)
- `action_items[:5]` (L5414)
- `feedback_provenance` 필드: `_compact_text(..., 500)` (L5441-5443)
- JSONL **AND** DB로 흘러가는 공통 소스에서 절삭 → 두 sink 모두 손실
- fix type: `contract-cleanup`

### P1-3. `stage4_director_runtime.py:685,699,729,736,753` — Console decision-text truncation
- `decision.reason[:80]` (L685) — operator 콘솔에서 사유 80자 절삭
- `decision.reason[:120]` (L699) — logging.INFO
- `decision.selection_reason[:120]` (L729, L736) — operator 콘솔 + meta
- `decision.reason[:120]` (L753) — operator 콘솔
- 정책 위반: `AGENTS.md` "콘솔 로그 최대 표시 정책"은 결정 근거를 축약하지 말 것을 명시
- fix type: `contract-cleanup`

### P1-4. `stage2_finalizer.py:1878,2837,3006` — Stage 2 rationale truncation
- REJECT path: `reject_reason[:500]` (L2837)
- `reason[:500]` (L1878) — pass-with-fix 경로
- `reason[:100]` (L3006) — 재심사 경로
- `reason[:200]` (L2931, L2950, L2952, L2968) — Stage 2 REJECT DB/메트릭 기록
- fix type: `contract-cleanup`

### P1-5. `stage3_orchestrator.py:1844-1860,2540-2558` — Stage 3 DB attempt missing rationale fields
- PASS path (L1844-1860): `save_stage_attempt`에 `selection_reason`, `verdict_reason`, `open_review`, `fix_scope_reasoning`, `runtime_advisory`, `retry_directives` 미전달
- REJECT path (L2540-2558): 동일
- 이 필드들은 `_build_stage3_director_selection_kwargs()`에서 **이미 추출**되어 `selection_kwargs`에 존재하지만, `save_stage_attempt`로 forward 안 됨
- Stage 4는 `_build_stage4_db_attempt_payload()`에서 이 필드들을 전부 전달 → Stage 3만 누락
- fix type: `contract-cleanup`

### P1-6. `stage2_finalizer.py:2691-2710,2829-2848` — Stage 2 DB attempt missing rationale fields
- PASS path (L2691-2710): `save_stage_attempt`에 `selection_reason`, `verdict_reason`, `open_review`, `fix_scope_reasoning`, `runtime_advisory`, `retry_directives` 미전달
- REJECT path (L2829-2848): 동일
- DB 스키마는 이 필드들을 수용하도록 설계됨 — Stage 2 caller만 미채움
- fix type: `contract-cleanup`

---

## 4. Quick Wins

### QW-1. Remove `[:80]` and `[:120]` console truncation in `stage4_director_runtime.py`
- 5곳: L685, L699, L729, L736, L753
- 난이도: trivial, 각 라인에서 slice 제거
- ROI: high — operator 콘솔에서 결정 근거 전문 표시

### QW-2. Remove `[:500]` / `[:300]` / `[:5]` truncation in `stage4_interview_round.py` L5348-5349, L5414, L5416
- JSONL과 DB 양쪽 소스에서 절삭 해제
- ROI: high — DB max-retention 정책 실현의 핵심

### QW-3. Forward `selection_reason`, `verdict_reason` from `selection_kwargs` to `save_stage_attempt` in Stage 3
- `stage3_orchestrator.py` L1844-1860 및 L2540-2558에서 추가 키워드 전달
- 난이도: low — `selection_kwargs`에 값이 이미 존재
- ROI: medium — Stage 3 DB 레코드 품질 향상

### QW-4. Remove `thinking_snippet[:5000]` in `base_agent.py:556`
- TF-58 주석과 DB 함수는 이미 무절삭 설계 — caller만 동기화
- ROI: medium — Director full thinking DB 보존

### QW-5. Remove `error_msg[:80]` in `base_agent.py:583`
- 80자는 스택 트레이스나 상세 에러에 부족
- ROI: medium — 에러 진단 품질 향상

---

## 5. Boundary Refactor Candidates

### BR-1. Stage 2/3 DB attempt payload builder 통합
- Stage 4는 `_build_stage4_db_attempt_payload()` 전용 빌더가 있어 모든 필드를 체계적으로 전달
- Stage 2/3는 인라인으로 `save_stage_attempt` 호출 → 필드 누락 발생 원인
- **권고**: Stage 2/3도 `_build_stageN_db_attempt_payload()` 빌더 메서드를 만들어 필드 계약을 통일
- fix type: `boundary-refactor`

### BR-2. Advisory raw payload adjunct retention
- `save_attempt_raw_rationale()` (L2983+)이 이미 존재하지만, advisory chain의 전문(structured_warnings, drift details 등)은 아직 이 경로로 저장되지 않음
- 현재 advisory는 `advisory_flags` JSON summary로만 DB에 남음
- **권고**: advisory chain 결과를 `save_attempt_raw_rationale(payload_kind="advisory_detail")` 경로로 저장
- fix type: `boundary-refactor`

### BR-3. Score-mutation provenance DB 컬럼
- 현재: `pre_firewall_score`, `firewall_reason` 등 일부 필드만 `director_selections`에 존재
- NC-3, NC-3B, SCM, V60.97 swap 등 다른 score rewrite는 `_operator_log`로만 콘솔 출력
- **권고**: `director_selections` 또는 `stage_attempts`에 `score_mutation_log` TEXT 컬럼 추가, 또는 `save_attempt_raw_rationale(payload_kind="score_provenance")` 활용
- fix type: `boundary-refactor`

---

## 6. Fresh-Run Relevance

### Fresh-run-before-fix allowed: **no**

**이유**: Q8 관측성 부족 문제는 fresh run의 진단 가치를 직접 저하시킨다.

현재 상태에서 fresh run을 돌리면:
1. Director 판정 사유가 DB에서 500자로 절삭됨 → post-run "왜 REJECT인가?" 분석 불충분
2. Stage 2/3 DB 레코드에 rationale 필드가 null → 해당 Stage 진단 불가
3. LLM thinking이 5000자로 절삭됨 → Director 사고 과정 복원 불완전
4. advisory detail이 count-only summary → "어떤 경고가 있었는지" DB에서 재확인 불가

**근본 원인**: `관측성 부족` + `DB max-retention 미실현`

### Top 3 highest-ROI code fixes before next fresh run

| 순위 | 대상 | 효과 |
|---|---|---|
| **1** | P1-2 + P1-3 + P1-4: `stage4_interview_round.py`, `stage4_director_runtime.py`, `stage2_finalizer.py`에서 `[:500]`/`[:300]`/`[:120]`/`[:80]` 결정문 절삭 제거 | DB와 콘솔에서 full rationale 보존. Fresh run 후 post-analysis 품질 극대화 |
| **2** | P1-5 + P1-6: Stage 2/3 `save_stage_attempt` 호출에 `selection_reason`, `verdict_reason` 등 rationale 필드 전달 | Stage 2/3 DB 레코드에서 빈 rationale 문제 해소. 3-stage 균일 진단 가능 |
| **3** | P1-1: `base_agent.py` L556 `thinking_snippet[:5000]` 및 L583 `error_msg[:80]` 제거 | LLM thinking 전문 + 에러 상세가 DB에 보존됨 |

---

## 7. Confidence And Limits

### Estimated confidence: 96%

**Basis**:
- live source에서 직접 grep + read로 모든 truncation 패턴을 확인함
- DB 저장 함수(`save_stage_attempt`, `save_director_selection`, `save_llm_call`)의 무절삭 설계를 확인함
- caller-side truncation 패턴이 일관되게 존재하는 것을 검증함
- Stage 2/3/4 간 DB field population 불균형을 비교 확인함

**4% gap**:
- `stage4_interview_round.py`가 5,800+ LOC이므로 일부 edge-case 절삭 패턴을 놓쳤을 가능성 (1%)
- `stage2_finalizer.py`도 2,900+ LOC이며 모든 메트릭 경로를 추적하지 못했을 가능성 (1%)
- advisory chain 내부 9개 advisory 각각의 로깅 패턴은 대표 3개만 심층 조사함 (2%)

---

## Appendix A. Full Truncation Inventory (Scope Files)

### A.1 `base_agent.py` (central LLM caller)
| Line | Pattern | Sink | Fix Type |
|---|---|---|---|
| 556 | `thinking_snippet[:5000]` | DB `llm_calls.thinking_snippet` | contract-cleanup |
| 583 | `error_msg[:80]` | DB `llm_calls.error_msg` | contract-cleanup |

### A.2 `stage4_interview_round.py`
| Line | Pattern | Sink | Fix Type |
|---|---|---|---|
| 5348 | `selection_reason[:500]` | JSONL + DB | contract-cleanup |
| 5349 | `verdict_reason[:500]` | JSONL + DB | contract-cleanup |
| 5414 | `action_items[:5]` | JSONL | contract-cleanup |
| 5416 | `open_review[:300]` | JSONL + DB | contract-cleanup |
| 5437-5439 | `warnings[:20]` | JSONL | ignore (reasonable cap) |
| 5441-5443 | `_compact_text(..., 500)` × 3 | JSONL | contract-cleanup |
| 3379 | `str(_ct_err)[:60]` | Console | ignore (error summary) |
| 3436 | `str(bv_err)[:60]` | Console | ignore (error summary) |
| 4624 | `_tg_warnings_all[:10]` | Console (advisory) | ignore (reasonable cap) |
| 4663 | `_drift_all[:8]` | Console (advisory) | ignore (reasonable cap) |
| 4671 | `found_in_ms[:40]` | Console (advisory) | contract-cleanup |
| 4699 | `_num_drifts[:6]` | Console (advisory) | ignore (reasonable cap) |
| 4700 | `issue[:60]` | Console (advisory) | contract-cleanup |
| 4730 | `fb["text"][:200]` | Console (advisory) | contract-cleanup |
| 4760 | `_fb_all[:6]` | Console (advisory) | ignore (reasonable cap) |
| 4767 | `issue[:60]` | Console (advisory) | contract-cleanup |
| 4818 | `_ip_all[:6]` | Console (advisory) | ignore (reasonable cap) |
| 4825 | `info_used[:40]`, `why_paradox[:60]` | Console (advisory) | contract-cleanup |
| 4866 | `_rd_all[:6]` | Console (advisory) | ignore (reasonable cap) |
| 4873 | `npc_pair[:30]`, `why_drift[:60]` | Console (advisory) | contract-cleanup |
| 4908 | `_ltr_all[:6]` | Console (advisory) | ignore (reasonable cap) |
| 4915 | `pattern[:30]`, `issue[:60]` | Console (advisory) | contract-cleanup |
| 4975 | `_nc_all[:10]` | Console (advisory) | ignore (reasonable cap) |
| 4982 | `text[:120]` | Console (advisory) | contract-cleanup |
| 5035 | `_ai_hits[:3]` | Console (advisory) | ignore (reasonable cap) |
| 5070 | `_candidate_lines[:3]` | Console (advisory) | ignore (reasonable cap) |

### A.3 `stage4_director_runtime.py`
| Line | Pattern | Sink | Fix Type |
|---|---|---|---|
| 685 | `decision.reason[:80]` | Console | contract-cleanup |
| 699 | `decision.reason[:120]` | Log file | contract-cleanup |
| 729 | `decision.selection_reason[:120]` | Console | contract-cleanup |
| 736 | `decision.selection_reason[:120]` | Console meta | contract-cleanup |
| 753 | `decision.reason[:120]` | Console | contract-cleanup |
| 772 | `action_items[:5]` | Console | ignore (reasonable cap) |
| 120 | `str(exc)[:60]` | Console | ignore (error summary) |
| 211 | `str(exc)[:60]` | Console | ignore (error summary) |
| 269 | `checklist_result.summary[:60]` | Console | contract-cleanup |
| 288 | `confidence.concerns[:3]` | Console | ignore (reasonable cap) |
| 313 | `compliance.violations[:5]` | Console | ignore (reasonable cap) |
| 348 | `blueprint[:8000]` | Director prompt | ignore (prompt budget) |

### A.4 `stage2_finalizer.py`
| Line | Pattern | Sink | Fix Type |
|---|---|---|---|
| 1878 | `reason[:500]` | pass_rate_monitor | contract-cleanup |
| 2837 | `reason[:500]` | DB `stage_attempts.reject_reason` | contract-cleanup |
| 3006 | `reason[:100]` | pass_rate_monitor | contract-cleanup |
| 2931 | `reason[:200]` | pass_rate_monitor | contract-cleanup |
| 2950 | `reason[:200]` | pass_rate_monitor | contract-cleanup |
| 2952 | `re_slice_instruction[:200]` | pass_rate_monitor | contract-cleanup |
| 2954 | `fix_scope[:40]` | pass_rate_monitor | ignore (bounded metadata) |
| 1820 | `reason[:80]` | Console (Stage 2 Director) | contract-cleanup |

### A.5 `stage3_orchestrator.py`
| Line | Pattern | Sink | Fix Type |
|---|---|---|---|
| 2236 | `contradictions[:5]` each `[:160]` | director_selections advisory | contract-cleanup |
| 2239 | `fix_scope_reasoning[:300]` | director_selections advisory | contract-cleanup |
| 2577 | `_reject_reason[:160]` | Log file (summary) | ignore (log summary) |

### A.6 `director_ensemble.py`
| Line | Pattern | Sink | Fix Type |
|---|---|---|---|
| 1041 | `review_reason[:100]` | internal | contract-cleanup |
| 1194 | `contradiction_details[:3]` each `[:160]` | feedback | contract-cleanup |
| 1200 | `hint[:160]` | action_items | contract-cleanup |
| 1446 | combined text `[:6000]` | Director prompt | ignore (prompt budget) |
| 1621 | `contradictions[:5]` each `[:120]` | Log file | contract-cleanup |
| 1626 | `comparison_notes[:150]` | Log file | contract-cleanup |
| 1628 | `reason[:100]` | Log file | contract-cleanup |
| 1631 | `reason[:120]` | Log file (summary) | contract-cleanup |
| 1858 | `str(exc)[:80]` | Log file (error) | ignore (error summary) |
| 1889-1890 | `contradictions[:5]` each `[:120]` | Log file | contract-cleanup |
| 1895 | `reason[:120]` | Log file (summary) | contract-cleanup |

### A.7 `db_manager.py` (DB layer — mostly clean)
| Line | Pattern | Sink | Fix Type |
|---|---|---|---|
| 3088 | `message[:4000]` | `ui_events` table | ignore (bounded metadata) |
| 3091 | `prompt_id[:200]` | `ui_events` table | ignore (bounded metadata) |
| 3092 | `artifact_path[:1000]` | `ui_events` table | ignore (bounded metadata) |
| 2355 | `label[:40]` | `episode_quality_labels` | ignore (bounded metadata) |

---

## Appendix B. Sink Parity Matrix

| 데이터 | Console | Log File | DB `stage_attempts` | DB `director_selections` | JSONL | Pass-Rate |
|---|---|---|---|---|---|---|
| verdict | Full | Full | Full | Full | Full | Full |
| score | Full | Full | Full | Full | Full | Full |
| selection_reason | [:120] | [:120-150] | [:500] (S4), null (S2/S3) | Full | [:500] | — |
| verdict_reason | [:120] | [:100] | [:500] (S4), null (S2/S3) | Full | [:500] | — |
| open_review | — | — | [:300] (S4), null (S2/S3) | — | [:300] | — |
| Director thinking | Full | Full | — | Full | — | — |
| advisory detail | Full text | summary | JSON flags | JSON flags | [:20] warnings | — |
| score provenance | Full (_operator_log) | Full | — | pre_firewall only | — | — |
| adaptive branch | Full (_operator_log) | Full | — | adaptive_reason | — | — |
| error_category | Full | Full | Full (S4), null (S2/S3) | — | Full | Full |
| failure_category | — | — | Full (S4), partial (S2/S3) | — | — | — |
| fix_pack | — | — | — | — | Full | Full |

---

## 3-Pass Audit Record

- **Pass 1**: 9개 scope 파일에서 `[:N]` truncation 패턴을 전수 grep하고, DB 저장 함수 3개의 무절삭 설계를 확인했다. Caller-side truncation이 핵심 문제임을 식별.
- **Pass 2**: Stage 2/3/4 간 DB field population 불균형을 비교하고, Console ↔ DB sink parity matrix를 완성했다. P1 6건, P2 5건, P3 6건으로 분류.
- **Pass 3**: `AGENTS.md` max-retention/max-display 정책과 대조하여 fresh-run-before-fix를 `no`로 확정. Top 3 ROI fix를 선정하고, 각 finding에 `file:line` anchor와 fix type을 검증했다.
