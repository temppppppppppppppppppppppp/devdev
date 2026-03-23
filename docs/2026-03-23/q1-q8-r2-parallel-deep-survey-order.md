Date: 2026-03-23
Status: active
Document Type: parallel deep survey order (R2)
Canonical Path: `docs/2026-03-23/q1-q8-r2-parallel-deep-survey-order.md`
Temp Mirror Path: none
Source Evidence:
- `docs/2026-03-23/daily-roadmap-2026-03-23.md`
- `docs/2026-03-23/q1-q8-current-state-merge-audit.md`
- `docs/2026-03-23/q1-q8-current-state-parallel-deep-survey-order.md` (1차 오더)
- `docs/2026-03-23/opus/q1~q8-*-deep-dive.md` (1차 보고서 16건)
- `docs/2026-03-23/opus/pre-rerun-root-cause-t1~t10-*.md` (T1-T10 보고서 20건)
- `docs/2026-03-23/fresh-run-3pass-audit-report.md`
- `docs/2026-03-23/director-pipeline-7axis-deep-dive.md`
- `docs/2026-03-23/generation-coherence-deep-dive-report.md`

Commit State:
- Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Baseline Dirty Summary: `dirty workspace allowed; touched surfaces include modules/core/stage3_orchestrator.py, modules/domain/agents/director_ensemble.py, tests/test_stage3_orchestrator.py, tests/test_director_modules.py, docs/temp/queue-state.json`

## 1. Purpose

- 1차 Q1-Q8 전수조사 이후 코드 수정(`79f570f2`: pre-rerun 3축 수정 + DB/콘솔 max-retention/max-display 전량)이 반영된 상태에서 **2차 검증 조사**를 수행한다.
- 1차 보고서의 finding이 해소/잔존/악화되었는지 delta 판정한다.
- T1-T10 pre-rerun root-cause 보고서의 cross-layer 발견을 Q축별로 흡수한다.
- fresh run 증거(`projects/0_0323/`)와 live source를 대조하여 실증 근거를 확보한다.
- 최종 목표: **다음 fresh run 실행 가능 여부** 축별 판정.

이 문서는 survey-only이다. 코드 수정을 포함하지 않는다.

## 2. 1차 대비 Delta Context

### 2.1 코드 수정 반영 (커밋 `79f570f2`)

| 수정 축 | 내용 | 1차 보고서 참조 |
|---------|------|----------------|
| Q3 verdict accuracy | V60.97 swap 재평가, adaptive decision guard, ep_type forwarding | Q3 P0/P1 |
| Q4 feedback fidelity | rejection_reason 원본 보존, contradiction_details 축소 완화, multi-layer truncation 제거 | Q4 P1 |
| Q6 retrieval observability | multi-query fallback warning, advisor fallback warning, embedding cache invalidation | Q6 P1 |
| Q8 DB max-retention | Python truncation 제거 (TEXT 컬럼), failure_category 추가, raw adjunct retention | Q8 P1 |
| Q8 console max-display | Director thinking/advisory/판정 사유 최대 표시 | Q8 P1 |

### 2.2 1차 Merge Audit 요약 (`q1-q8-current-state-merge-audit.md`)

| 축 | 1차 상태 | Merge 판정 | R2 초점 |
|----|---------|------------|---------|
| Q1 | final, 96% | mostly valid, 1 stale | 앙상블 수렴 패턴 재검증 + T10 scene detection 교차 |
| Q2 | final, 95% | valid, 1 stale | fix/retry 경로 코드 수정 후 검증 |
| Q3 | final, 95% | **fix before rerun** | **수정 검증 최우선** |
| Q4 | final, 96% | **fix before rerun** | **수정 검증 최우선** |
| Q5 | **provisional**, 94% | mixed, 2 shifted/stale | 구조적 위험 재평가 + fresh run 실증 |
| Q6 | final, 95% | **min observability before rerun** | **수정 검증** |
| Q7 | **provisional**, 94% | long-run structural | 구조적 위험 재평가 + fresh run 실증 |
| Q8 | final, 96% | largely absorbed by active SSOTs | **수정 완료 검증** |

### 2.3 T1-T10 Pre-Rerun Cross-Reference Map

| Q축 | 관련 T-보고서 | 핵심 교차 발견 |
|-----|-------------|---------------|
| Q1 | T5 write/fix, T6 artifact, T10 cross-layer | scene detection false-positive, empty scene_breakdown fields, ensemble convergence |
| Q2 | T5 write/fix, T7 verdict chain | fix_scope override chain, rejection retry pathology |
| Q3 | T7 verdict chain, T8 verdict parity, T10 cross-layer | gate sequence, post-select continuity, date contamination |
| Q4 | T5 write/fix, T6 artifact, T7 verdict chain | feedback field loss, contradiction_details shrinkage |
| Q5 | T1 stage2 contract, T2 stage2 artifact, T10 cross-layer | blueprint time_flow date error, non-atomic save |
| Q6 | T9 context/retrieval | hybrid retrieval routing, slot cap, NPC cap |
| Q7 | T9 context/retrieval | Tier 2/3 silent deletion, work focus truncation, emergency truncation |
| Q8 | T8 verdict parity | console/DB/audit sink parity, truncation removal verification |

## 3. Parallel Operating Mode

- 8개 터미널이 병렬로 실행한다.
- 각 터미널은 하나의 Q축에 대해 bounded delta survey를 수행한다.
- 각 터미널이 생산하는 산출물:
  - 최종 보고서 1건 (final 또는 provisional)
  - 선택적 evidence manifest 1건
- 어떤 터미널도 execution SSOT, temp queue artifact, 코드 패치를 생성하지 않는다.
- Codex가 8건의 보고서를 모아 merge-audit하고, action-bearing finding만 execution SSOT로 승격한다.

## 4. Primary Diagnosis Questions (R2 Focus)

1. **Q3/Q4/Q6 코드 수정이 실제로 1차 P0/P1 finding을 해소했는지 검증한다.** (검증)
2. **Q8 DB/콘솔 max-retention/max-display 수정이 관측성 갭을 해소했는지 검증한다.** (검증)
3. **Q1 앙상블 수렴 패턴과 scene detection 오탐이 여전히 존재하는지 재평가한다.** (재평가)
4. **Q5 비원자 저장/3시스템 동기화 부재가 fresh run에서 실제로 발현되었는지 실증한다.** (실증)
5. **Q7 Tier 2/3 무음 삭제/긴급 절삭 경로가 fresh run에서 exercised되었는지 실증한다.** (실증)
6. **모든 축을 종합하여 다음 fresh run 실행 안전 여부를 판정한다.** (종합 판정)

## 5. Evidence Priority

live source > artifact text > DB rows > runtime/session logs > console transcript > 1차 보고서 서술

- 1차 보고서의 claim이 live code와 다르면, live code가 우선한다.
- T1-T10 보고서의 claim이 1차 보고서와 다르면, 더 최근 증거를 가진 쪽이 우선한다.
- 코드 수정 후 claim은 반드시 live source에서 재확인한다.

## 6. Terminal Plan

| Terminal | Q축 | Focus | Primary Scope | Final Report Path | Evidence Path |
|----------|-----|-------|---------------|-------------------|---------------|
| T1 | Q1 | 잘 쓰냐 — 첫 생성 품질 delta | `modules/domain/agents/chief_writer.py`, `chief_writer_quality.py`, `arc_ensemble.py`, `blueprint_ensemble.py`, fresh run drafts/artifacts | `docs/2026-03-23/opus/r2-q1-generation-quality.md` | `docs/2026-03-23/opus/r2-q1-generation-quality-evidence.md` |
| T2 | Q2 | 잘 고치냐 — fix/retry 품질 delta | `modules/core/stage4_retry_runtime.py`, `stage4_reject_runtime.py`, `modules/domain/agents/director_ensemble.py` (fix_pack/fix_scope), fresh run runtime_audit | `docs/2026-03-23/opus/r2-q2-fix-retry.md` | `docs/2026-03-23/opus/r2-q2-fix-retry-evidence.md` |
| T3 | Q3 | 잘 판단하냐 — verdict accuracy **수정 검증** | `modules/domain/agents/director_ensemble.py`, `director_grading.py`, `modules/core/stage4_interview_round.py`, `stage4_director_runtime.py` | `docs/2026-03-23/opus/r2-q3-verdict-accuracy.md` | `docs/2026-03-23/opus/r2-q3-verdict-accuracy-evidence.md` |
| T4 | Q4 | 잘 설명하냐 — feedback fidelity **수정 검증** | `modules/core/stage4_reject_runtime.py`, `stage4_retry_runtime.py`, `modules/core/stage4_interview_round.py` | `docs/2026-03-23/opus/r2-q4-feedback-fidelity.md` | `docs/2026-03-23/opus/r2-q4-feedback-fidelity-evidence.md` |
| T5 | Q5 | 잘 기억하냐 — 장기 일관성 재평가 | `modules/domain/agents/world_state.py`, `fact_ledger.py`, `modules/core/state_tracker.py`, `modules/validation/continuity_validator.py`, `modules/domain/agents/continuity_arc.py`, fresh run anchors DB | `docs/2026-03-23/opus/r2-q5-long-term-consistency.md` | `docs/2026-03-23/opus/r2-q5-long-term-consistency-evidence.md` |
| T6 | Q6 | 잘 찾냐 — retrieval observability **수정 검증** | `modules/core/vec_memory.py`, `stage4_context_builder.py`, `context_advisor.py`, fresh run vec_episodes/episode_meta DB | `docs/2026-03-23/opus/r2-q6-selective-retrieval.md` | `docs/2026-03-23/opus/r2-q6-selective-retrieval-evidence.md` |
| T7 | Q7 | 잘 받냐 — 컨텍스트 수신 재평가 | `modules/core/stage4_context_builder.py`, `stage4_context_packets.py`, `modules/domain/agents/chief_writer_context.py`, `chief_writer_context_packets.py`, `modules/core/prompt_builder.py`, `modules/api/base_agent.py` | `docs/2026-03-23/opus/r2-q7-context-reception.md` | `docs/2026-03-23/opus/r2-q7-context-reception-evidence.md` |
| T8 | Q8 | 잘 로깅하냐 — DB/콘솔 max-retention **수정 검증** | `modules/domain/agents/director_ensemble.py`, `modules/core/stage4_interview_round.py`, `modules/core/db_manager.py`, `modules/core/logger.py`, `modules/core/pass_rate_monitor.py`, `modules/core/metrics_collector.py`, fresh run console/DB/audit | `docs/2026-03-23/opus/r2-q8-logging-retention.md` | `docs/2026-03-23/opus/r2-q8-logging-retention-evidence.md` |

## 7. Output Contract

### 7.1 Final Report
- Path: 각 터미널은 자기 할당된 `Final Report Path`에만 작성
- Format: human-readable markdown
- Status: `final` 또는 `provisional`
- confidence 95% 미만이면 `provisional`

### 7.2 Optional Evidence Manifest
- Path: 각 터미널은 자기 할당된 `Evidence Path`에만 작성
- 용도: raw source anchors, artifact path inventory, DB table/query notes, console/log line anchors

### 7.3 No Temp Queue Artifacts
- survey-only
- `docs/temp/` 실행 문서 생성 금지
- `docs/temp/queue-state.json` 변경 금지

### 7.4 Codex Merge Layer
- Opus는 merged master report를 작성하지 않는다
- Codex가 나중에 merge layer를 생성한다 (예상 경로: `docs/2026-03-23/q1-q8-r2-merge-audit.md`)
- Codex만이 어떤 finding을 execution SSOT 후보로 승격할지 결정한다

## 8. Mandatory Report Structure

각 터미널 보고서는 반드시 다음 섹션을 포함한다:

1. **Executive Summary**
2. **R1→R2 Delta Summary** — 1차 finding 중 해소/잔존/악화/신규 분류
3. **Current Ownership / Flow Map**
4. **Focus-Scope Findings** — R2에서 발견한 사항
5. **Code-Fix Verification** — 해당 축 관련 코드 수정이 있었다면, 수정 전후 비교
6. **Pre-Rerun T-Report Cross-Reference** — 관련 T-보고서 finding 흡수
7. **Fresh-Run Evidence** — `projects/0_0323/` 실증 결과
8. **Root-Cause vs Symptom Classification**
9. **Quick Wins**
10. **False Leads / Non-Causes**
11. **Fresh-Run Readiness** — 이 축 기준 다음 rerun 가능 여부
12. **Confidence And Limits**

### P0/P1 항목 필수 기재 사항:
- file path 또는 artifact path
- line anchor 또는 artifact identifier
- evidence type: `source` / `DB` / `console` / `artifact text`
- root-causal인지 symptomatic인지
- rerun을 block하는지 여부

### 모든 recommendation 필수 fix type:
- `resolved` — 이미 수정 완료됨
- `comment-only`
- `doc-only`
- `observability-only`
- `contract-cleanup`
- `boundary-refactor`
- `ignore`

## 9. Hard Constraints

- Survey-only. 코드 패치 금지.
- 실행 중인 live run 방해/재시작 금지.
- execution SSOT 생성 금지.
- `docs/temp/` queue artifact 생성/변경 금지.
- 로그/DB/hash만 보지 말고 artifact 본문과 live source도 직접 조사한다.
- Stage 3/4 점수만으로 판정하지 말고 artifact 비교를 수행한다.
- 1차 보고서의 서술을 live code와 대조 없이 반복하지 않는다.
- 코드 수정이 있었던 축(Q3/Q4/Q6/Q8)은 반드시 수정 전후 diff를 확인한다.

## 10. Acceptance Criteria

- Q3/Q4/Q6/Q8 수정 검증 터미널(T3/T4/T6/T8)은 수정이 1차 P0/P1을 해소했는지 명시적으로 판정한다.
- Q1/Q2/Q5/Q7 재평가 터미널(T1/T2/T5/T7)은 1차 finding의 잔존/해소/악화를 명시적으로 분류한다.
- 각 터미널은 root cause와 symptom을 명확히 분리한다.
- 각 터미널은 `Fresh-run-before-fix allowed: yes/no`를 명시한다.
- 전체 보고서 세트가 Codex의 merge-audit에서 one pre-rerun fix cluster를 rank할 수 있어야 한다.
- confidence 95% 이상이거나, 보고서가 provisional로 남는다.

## 11. Common Opus Prompt

아래 프롬프트를 모든 터미널에 사용한다. 교체할 항목:
- `TERMINAL_ID`
- `Q_AXIS`
- `Q_LABEL`
- `PRIMARY_SCOPE`
- `R1_REPORT_PATH`
- `R1_EVIDENCE_PATH`
- `RELATED_T_REPORTS`
- `FINAL_REPORT_PATH`
- `EVIDENCE_PATH`

```text
System-track deep survey order (R2).

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/system-full-survey-execution-harness.md
4. docs/implementation/document-3pass-audit-harness.md
5. docs/2026-03-23/q1-q8-r2-parallel-deep-survey-order.md
6. R1_REPORT_PATH
7. R1_EVIDENCE_PATH
8. docs/2026-03-23/q1-q8-current-state-merge-audit.md
9. docs/2026-03-23/fresh-run-3pass-audit-report.md
10. RELATED_T_REPORTS
11. docs/2026-03-23/daily-roadmap-2026-03-23.md

Task:
You are TERMINAL_ID. Run a bounded R2 delta survey for Q_AXIS (Q_LABEL) over the current live workspace state.

This is the SECOND round. Your R1 baseline is R1_REPORT_PATH. Focus on:
1. Code-fix verification: if code was modified for this axis, verify the fix resolved the R1 P0/P1 findings
2. Stale claim detection: check if R1 findings are still valid in live code
3. T-report cross-reference: absorb relevant pre-rerun root-cause findings from RELATED_T_REPORTS
4. Fresh-run evidence: use projects/0_0323/ artifacts, DB, and logs to validate or refute claims
5. New findings: anything not covered by R1 or T-reports

Hard constraints:
- Survey-only. No code changes.
- Do not create execution SSOTs.
- Do not create docs/temp queue artifacts.
- Prefer live source, artifact text, and DB truth over stale report wording.
- If an R1 claim is already fixed in live code, mark it resolved instead of repeating it.
- For Q3/Q4/Q6/Q8: you MUST verify code fixes from commit 79f570f2.

Primary scope:
PRIMARY_SCOPE

Required outputs:
- Final report: FINAL_REPORT_PATH
- Optional evidence manifest: EVIDENCE_PATH

Required report sections:
1. Executive Summary
2. R1→R2 Delta Summary
3. Current Ownership / Flow Map
4. Focus-Scope Findings
5. Code-Fix Verification
6. Pre-Rerun T-Report Cross-Reference
7. Fresh-Run Evidence
8. Root-Cause vs Symptom Classification
9. Quick Wins
10. False Leads / Non-Causes
11. Fresh-Run Readiness
12. Confidence And Limits

Rules:
- Every P0/P1 item must include file:line or artifact identifiers.
- Every recommendation must have one fix type:
  - resolved (already fixed)
  - comment-only
  - doc-only
  - observability-only
  - contract-cleanup
  - boundary-refactor
  - ignore
- Explicitly state:
  - Fresh-run-before-fix allowed: yes/no
  - Top 3 highest-ROI remaining fixes (or "none — all resolved" if applicable)
- R1→R2 delta: for each R1 P0/P1 finding, classify as:
  - resolved (code fix verified)
  - stale (no longer applicable)
  - persists (still present, unchanged)
  - worsened (still present, worse than R1)
  - new (not in R1)

After saving, run:
- python scripts/check_utf8_hygiene.py FINAL_REPORT_PATH
- python scripts/ops_validator.py

In your final response:
- summarize the R1→R2 delta first (how many resolved / persists / new)
- then the primary blocker (if any)
- then the ranked remaining fixes
- then fresh-run readiness
- then confidence
- keep it concise
```

## 12. Terminal Overrides

| Terminal | Q_AXIS | Q_LABEL | PRIMARY_SCOPE | R1_REPORT_PATH | R1_EVIDENCE_PATH | RELATED_T_REPORTS | FINAL_REPORT_PATH | EVIDENCE_PATH |
|----------|--------|---------|---------------|----------------|------------------|-------------------|-------------------|---------------|
| T1 | Q1 | `잘 쓰냐 — 첫 생성 품질` | `modules/domain/agents/chief_writer.py, chief_writer_quality.py, arc_ensemble.py, blueprint_ensemble.py, projects/0_0323/drafts/**, projects/0_0323/logs/artifacts/stage4/**` | `docs/2026-03-23/opus/q1-generation-quality-deep-dive.md` | `docs/2026-03-23/opus/q1-generation-quality-evidence-manifest.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t5-stage4-write-fix.md, docs/2026-03-23/opus/pre-rerun-root-cause-t6-stage4-artifact-truth.md, docs/2026-03-23/opus/pre-rerun-root-cause-t10-cross-layer-artifact.md, docs/2026-03-23/generation-coherence-deep-dive-report.md` | `docs/2026-03-23/opus/r2-q1-generation-quality.md` | `docs/2026-03-23/opus/r2-q1-generation-quality-evidence.md` |
| T2 | Q2 | `잘 고치냐 — fix/retry 품질` | `modules/core/stage4_retry_runtime.py, stage4_reject_runtime.py, modules/domain/agents/director_ensemble.py, projects/0_0323/logs/runtime_audit.jsonl` | `docs/2026-03-23/opus/q2-fix-retry-deep-dive.md` | `docs/2026-03-23/opus/q2-fix-retry-evidence-manifest.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t5-stage4-write-fix.md, docs/2026-03-23/opus/pre-rerun-root-cause-t7-verdict-chain.md, docs/2026-03-23/director-pipeline-7axis-deep-dive.md` | `docs/2026-03-23/opus/r2-q2-fix-retry.md` | `docs/2026-03-23/opus/r2-q2-fix-retry-evidence.md` |
| T3 | Q3 | `잘 판단하냐 — verdict accuracy 수정 검증` | `modules/domain/agents/director_ensemble.py, director_grading.py, modules/core/stage4_interview_round.py, stage4_director_runtime.py, projects/0_0323/logs/runtime_audit.jsonl, projects/0_0323/logs/session/decisions.jsonl` | `docs/2026-03-23/opus/q3-verdict-accuracy-deep-dive.md` | `docs/2026-03-23/opus/q3-verdict-accuracy-evidence-manifest.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t7-verdict-chain.md, docs/2026-03-23/opus/pre-rerun-root-cause-t8-verdict-parity.md, docs/2026-03-23/opus/pre-rerun-root-cause-t10-cross-layer-artifact.md, docs/2026-03-23/director-pipeline-7axis-deep-dive.md` | `docs/2026-03-23/opus/r2-q3-verdict-accuracy.md` | `docs/2026-03-23/opus/r2-q3-verdict-accuracy-evidence.md` |
| T4 | Q4 | `잘 설명하냐 — feedback fidelity 수정 검증` | `modules/core/stage4_reject_runtime.py, stage4_retry_runtime.py, modules/core/stage4_interview_round.py, projects/0_0323/logs/runtime_audit.jsonl` | `docs/2026-03-23/opus/q4-feedback-loop-deep-dive.md` | `docs/2026-03-23/opus/q4-feedback-loop-evidence-manifest.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t5-stage4-write-fix.md, docs/2026-03-23/opus/pre-rerun-root-cause-t6-stage4-artifact-truth.md, docs/2026-03-23/opus/pre-rerun-root-cause-t7-verdict-chain.md, docs/2026-03-23/director-pipeline-7axis-deep-dive.md` | `docs/2026-03-23/opus/r2-q4-feedback-fidelity.md` | `docs/2026-03-23/opus/r2-q4-feedback-fidelity-evidence.md` |
| T5 | Q5 | `잘 기억하냐 — 장기 일관성 재평가` | `modules/domain/agents/world_state.py, fact_ledger.py, modules/core/state_tracker.py, state_tracker_npc.py, modules/validation/continuity_validator.py, modules/domain/agents/continuity_arc.py, projects/0_0323/project_data.db (anchors: world_state, fact_ledger)` | `docs/2026-03-23/opus/q5-long-term-consistency-deep-dive.md` | `docs/2026-03-23/opus/q5-long-term-consistency-evidence-manifest.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t1-stage2-contract.md, docs/2026-03-23/opus/pre-rerun-root-cause-t2-stage2-artifact-truth.md, docs/2026-03-23/opus/pre-rerun-root-cause-t10-cross-layer-artifact.md, docs/2026-03-23/generation-coherence-deep-dive-report.md` | `docs/2026-03-23/opus/r2-q5-long-term-consistency.md` | `docs/2026-03-23/opus/r2-q5-long-term-consistency-evidence.md` |
| T6 | Q6 | `잘 찾냐 — retrieval observability 수정 검증` | `modules/core/vec_memory.py, stage4_context_builder.py, context_advisor.py, projects/0_0323/project_data.db (vec_episodes, episode_meta)` | `docs/2026-03-23/opus/q6-selective-retrieval-deep-dive.md` | `docs/2026-03-23/opus/q6-selective-retrieval-evidence-manifest.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t9-context-retrieval.md, docs/2026-03-23/generation-coherence-deep-dive-report.md` | `docs/2026-03-23/opus/r2-q6-selective-retrieval.md` | `docs/2026-03-23/opus/r2-q6-selective-retrieval-evidence.md` |
| T7 | Q7 | `잘 받냐 — 컨텍스트 수신 재평가` | `modules/core/stage4_context_builder.py, stage4_context_packets.py, modules/domain/agents/chief_writer_context.py, chief_writer_context_packets.py, modules/core/prompt_builder.py, modules/api/base_agent.py` | `docs/2026-03-23/opus/q7-context-reception-deep-dive.md` | `docs/2026-03-23/opus/q7-context-reception-evidence-manifest.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t9-context-retrieval.md, docs/2026-03-23/generation-coherence-deep-dive-report.md` | `docs/2026-03-23/opus/r2-q7-context-reception.md` | `docs/2026-03-23/opus/r2-q7-context-reception-evidence.md` |
| T8 | Q8 | `잘 로깅하냐 — DB/콘솔 max-retention 수정 검증` | `modules/domain/agents/director_ensemble.py, modules/core/stage4_interview_round.py, modules/core/db_manager.py, modules/core/logger.py, modules/core/pass_rate_monitor.py, modules/core/metrics_collector.py, projects/0_0323/logs/runtime_audit.jsonl, docs/2026-03-23/console.txt` | `docs/2026-03-23/opus/q8-logging-retention-deep-dive.md` | `docs/2026-03-23/opus/q8-logging-retention-evidence-manifest.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t8-verdict-parity.md, docs/2026-03-23/opus/console-log-max-display-audit.md, docs/2026-03-23/opus/db-logging-integrity-audit.md` | `docs/2026-03-23/opus/r2-q8-logging-retention.md` | `docs/2026-03-23/opus/r2-q8-logging-retention-evidence.md` |

## 13. Terminal Dispatch One-Liners

```
넌 1번 터미널. docs/2026-03-23/q1-q8-r2-parallel-deep-survey-order.md를 읽고 T1 규칙대로 진행해.
넌 2번 터미널. docs/2026-03-23/q1-q8-r2-parallel-deep-survey-order.md를 읽고 T2 규칙대로 진행해.
넌 3번 터미널. docs/2026-03-23/q1-q8-r2-parallel-deep-survey-order.md를 읽고 T3 규칙대로 진행해.
넌 4번 터미널. docs/2026-03-23/q1-q8-r2-parallel-deep-survey-order.md를 읽고 T4 규칙대로 진행해.
넌 5번 터미널. docs/2026-03-23/q1-q8-r2-parallel-deep-survey-order.md를 읽고 T5 규칙대로 진행해.
넌 6번 터미널. docs/2026-03-23/q1-q8-r2-parallel-deep-survey-order.md를 읽고 T6 규칙대로 진행해.
넌 7번 터미널. docs/2026-03-23/q1-q8-r2-parallel-deep-survey-order.md를 읽고 T7 규칙대로 진행해.
넌 8번 터미널. docs/2026-03-23/q1-q8-r2-parallel-deep-survey-order.md를 읽고 T8 규칙대로 진행해.
```

## 14. Codex Merge Rule

- Opus는 8건의 lane 보고서를 수집하고 작성한다.
- Codex가 나중에:
  - stale claim 제거
  - cross-lane 중복 병합
  - root cause 순위 매기기
  - execution SSOT 후보 결정
  - **fresh-run readiness 종합 판정**
- Opus는 merged root-cause master conclusion을 작성하지 않는다.

## 15. 3-Pass Audit Record

- Pass 1
  - 1차 Q1-Q8 오더 구조를 기반으로 R2 delta survey 프레임 구성
  - 커밋 `79f570f2`의 수정 축(Q3/Q4/Q6/Q8)과 미수정 축(Q1/Q2/Q5/Q7)을 분리
  - T1-T10 cross-reference map을 terminal override에 반영
- Pass 2
  - 8개 터미널의 disjoint primary scope, report path, evidence path 할당 확인
  - 수정 검증 터미널(T3/T4/T6/T8)의 mandatory verification 요구사항 명시
  - Opus collection과 Codex merge authority 분리 확인
- Pass 3
  - common prompt 템플릿에 R2 delta 특화 지시사항 반영 (R1→R2 분류, code-fix verification, T-report absorption)
  - 오더가 survey-only이고 live run을 방해하지 않음을 재확인
  - dispatch one-liner와 terminal override 테이블 정합성 확인

## 16. Confidence

- Confidence: 97%
- Basis:
  - 오더는 bounded, survey-only이며 불안정한 외부 데이터에 의존하지 않는다
  - 8-lane 분할은 1차 Q1-Q8 프레임워크를 그대로 계승하되, R2 delta 초점을 추가한다
  - 수정 검증 축과 재평가 축의 분리가 명확하다
  - 산출물 경로와 merge 책임이 명시적이다
