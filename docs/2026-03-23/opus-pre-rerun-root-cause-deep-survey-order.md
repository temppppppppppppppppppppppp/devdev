Date: 2026-03-23
Status: active
Document Type: parallel deep survey order
Canonical Path: `docs/2026-03-23/opus-pre-rerun-root-cause-deep-survey-order.md`
Temp Mirror Path: none
Source Evidence:
- `docs/2026-03-23/console.txt`
- `projects/0_0323/project_data.db`
- `projects/0_0323/logs/session_20260323_134127.log`
- `projects/0_0323/logs/runtime_audit.jsonl`
- `projects/0_0323/logs/episode_production.jsonl`
- `projects/0_0323/logs/session/decisions.jsonl`
- `projects/0_0323/logs/session/ui_events.jsonl`
- `projects/0_0323/logs/artifacts/stage2/**`
- `projects/0_0323/logs/artifacts/stage3/**`
- `projects/0_0323/logs/artifacts/stage4/**`
- `projects/0_0323/plans/arcs/**`
- `projects/0_0323/plans/blueprints/**`
- `projects/0_0323/drafts/**`

Commit State:
- Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Baseline Dirty Summary: `dirty workspace allowed; touched surfaces include modules/core/stage3_orchestrator.py, modules/domain/agents/director_ensemble.py, tests/test_stage3_orchestrator.py, tests/test_director_modules.py, docs/temp/queue-state.json, docs/2026-03-23/console.txt, projects/0_0323/`
- Resume Commit: `must be refreshed by each Opus terminal before final save if local state drifted`
- Resume Drift Summary: `must be refreshed before any resolved/regressed claim`

## 1. Purpose
- Define the Opus order for a pre-rerun root-cause deep survey using up to 10 terminals in parallel.
- Treat the current fresh run as evidence, not as a success verdict.
- Reconstruct why Stage 2, Stage 3, and Stage 4 diverged, especially around Arc 1 Episode 3.
- Produce per-lane deep-dive reports that Codex will later merge-audit into one bounded fix direction.

This is survey-only. It is not a realization wave.

## 2. Current Runtime Constraint
- A fresh run already produced useful evidence and may still be running.
- This survey must not interrupt, restart, or compete with that run.
- Do not launch another fresh run.
- Do not close active execution SSOTs.
- Use saved console, DB, audit, and artifact evidence plus live source.
- If the user later stops the run, that is outside this order.

## 3. Parallel Operating Mode
- Up to 10 terminals may run in parallel.
- Each terminal is one bounded Opus TF lane.
- Each lane writes:
  - one final deep-dive report
  - one optional evidence manifest
- No lane creates execution SSOTs or temp queue artifacts.
- Codex remains the only merge authority after the 10 lane reports arrive.

## 4. Primary Diagnosis Questions
1. Did Stage 2 pass with a tactically thin arc that later destabilized Stage 3 and Stage 4?
2. Did Stage 3 over-pass weak blueprints or lose critical context?
3. Did Stage 4 fail because it could not write well, could not fix well, or was judged inconsistently?
4. Did the Director primary verdict and post-select gates diverge in a way that indicates real split-brain judgment?
5. Which findings are root causes, and which are downstream symptoms or observability artifacts?

## 5. Evidence Priority
Use this evidence order when claims conflict:
1. live source
2. artifact text
3. DB rows
4. saved runtime/session logs
5. console transcript
6. prior survey wording

Do not let console-only impressions outrank artifact or DB truth when those disagree.

## 6. Terminal Plan

| Terminal | Focus | Primary Scope | Final Report Path | Optional Evidence Path |
|---|---|---|---|---|
| T1 | Stage 2 contract and pacing static | `modules/core/stage2_orchestrator.py`, `modules/core/stage2_finalizer.py` | `docs/2026-03-23/opus/pre-rerun-root-cause-t1-stage2-contract.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t1-stage2-contract-evidence.md` |
| T2 | Stage 2 arc artifact and DB truth | `projects/0_0323/logs/artifacts/stage2/**`, `projects/0_0323/plans/arcs/**`, Stage 2 DB/audit rows | `docs/2026-03-23/opus/pre-rerun-root-cause-t2-stage2-artifact-truth.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t2-stage2-artifact-evidence.md` |
| T3 | Stage 3 blueprint contract and context static | `modules/core/stage3_orchestrator.py`, `modules/domain/agents/three_phase_blueprint_generator.py`, `modules/domain/agents/blueprint_ensemble.py` | `docs/2026-03-23/opus/pre-rerun-root-cause-t3-stage3-contract.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t3-stage3-contract-evidence.md` |
| T4 | Stage 3 blueprint artifact and DB truth | `projects/0_0323/logs/artifacts/stage3/**`, `projects/0_0323/plans/blueprints/**`, Stage 3 DB/audit rows | `docs/2026-03-23/opus/pre-rerun-root-cause-t4-stage3-artifact-truth.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t4-stage3-artifact-evidence.md` |
| T5 | Stage 4 write/fix/retry code chain | `modules/core/stage4_interview_round.py`, `modules/core/stage4_retry_runtime.py`, `modules/core/stage4_reject_runtime.py`, `modules/domain/agents/chief_writer.py` | `docs/2026-03-23/opus/pre-rerun-root-cause-t5-stage4-write-fix.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t5-stage4-write-fix-evidence.md` |
| T6 | Stage 4 attempt artifact truth | `projects/0_0323/logs/artifacts/stage4/**`, `projects/0_0323/drafts/**` | `docs/2026-03-23/opus/pre-rerun-root-cause-t6-stage4-artifact-truth.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t6-stage4-artifact-evidence.md` |
| T7 | Director verdict and post-select static chain | `modules/domain/agents/director_ensemble.py`, `modules/domain/agents/director_auditor.py`, `modules/core/stage4_director_runtime.py`, `modules/core/stage4_post_pass_runtime.py`, `modules/core/stage4_outcome_runtime.py` | `docs/2026-03-23/opus/pre-rerun-root-cause-t7-verdict-chain.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t7-verdict-chain-evidence.md` |
| T8 | Director and post-select DB/console parity | `docs/2026-03-23/console.txt`, `projects/0_0323/logs/session/**`, `projects/0_0323/logs/runtime_audit.jsonl`, relevant DB rows | `docs/2026-03-23/opus/pre-rerun-root-cause-t8-verdict-parity.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t8-verdict-parity-evidence.md` |
| T9 | Context and retrieval support factors | `modules/core/stage4_context_builder.py`, `modules/core/stage4_context_packets.py`, `modules/core/context_advisor.py`, `modules/core/vec_memory.py`, `modules/domain/agents/chief_writer_context.py`, `modules/domain/agents/chief_writer_context_packets.py`, `modules/domain/agents/continuity_arc.py`, `modules/validation/continuity_validator.py` | `docs/2026-03-23/opus/pre-rerun-root-cause-t9-context-retrieval.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t9-context-retrieval-evidence.md` |
| T10 | Cross-layer artifact continuity | compare Stage 2 arc, Stage 3 blueprints, Stage 4 manuscripts/rejects for Arc 1 Episode 3 continuity and executable pressure | `docs/2026-03-23/opus/pre-rerun-root-cause-t10-cross-layer-artifact.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t10-cross-layer-artifact-evidence.md` |

## 7. Output Contract

### 7.1 Final Report
- Path: each terminal writes only to its assigned `Final Report Path`
- Format: human-readable markdown
- Status: `final` or `provisional`
- If confidence is below 95%, the report must be `provisional`

### 7.2 Optional Evidence Manifest
- Path: each terminal writes only to its assigned `Optional Evidence Path`
- Purpose:
  - raw source anchors
  - artifact path inventory
  - DB table/query notes
  - console/log line anchors
- It is supporting evidence, not the interpreted report

### 7.3 No Temp Queue Artifacts
- This is survey-only
- Do not create `docs/temp/` execution docs
- Do not mutate `docs/temp/queue-state.json`

### 7.4 Codex Merge Layer
- Opus does not write the merged master report
- Codex will later create the merge layer, likely at:
  - `docs/2026-03-23/pre-rerun-root-cause-merge-audit.md`
- Codex alone decides which findings become execution SSOT candidates

## 8. Mandatory Report Structure
Each terminal report must contain:
1. Executive Summary
2. Current Ownership / Flow Map
3. Focus-Scope Findings
4. Root-Cause Relevance
5. Quick Wins
6. False Leads / Non-Causes
7. Fresh-Run Relevance
8. Confidence And Limits

For every P0 or P1 item include:
- file path or artifact path
- line anchor or artifact identifier
- evidence type:
  - source
  - DB
  - console
  - artifact text
- why it is root-causal rather than merely symptomatic
- whether it blocks the next rerun

Every recommendation must carry one `fix type`:
- `comment-only`
- `doc-only`
- `observability-only`
- `contract-cleanup`
- `boundary-refactor`
- `ignore`

## 9. Hard Constraints
- Survey-only. No code patches.
- Do not interrupt or restart the live run.
- Do not close active execution SSOTs.
- Do not create execution SSOTs.
- Do not mutate queue state.
- Do not stop at logs; inspect artifact text and DB truth where applicable.
- Do not treat Stage 3 or Stage 4 scores alone as authoritative without artifact comparison.
- Do not overclaim from old reports when live code or artifact truth disagrees.

## 10. Acceptance Criteria
- Arc 1 Episode 3 is covered across the 10 lanes without major blind spots.
- Each lane clearly separates root causes from symptoms.
- Each lane states `Fresh-run-before-fix allowed: yes/no`.
- The full set of reports makes it possible for Codex to rank one pre-rerun fix cluster.
- Confidence is at least 95%, or the lane report remains provisional.

## 11. Common Opus Prompt
Use this prompt for every terminal. Replace only:
- `TERMINAL_ID`
- `FOCUS_NAME`
- `PRIMARY_SCOPE`
- `FINAL_REPORT_PATH`
- `EVIDENCE_PATH`

```text
System-track deep survey order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/system-full-survey-execution-harness.md
4. docs/implementation/document-3pass-audit-harness.md
5. docs/2026-03-23/opus-pre-rerun-root-cause-deep-survey-order.md
6. docs/2026-03-23/console.txt
7. docs/2026-03-23/fresh-run-3pass-audit-report.md
8. docs/2026-03-23/q1-q8-current-state-merge-audit.md
9. docs/2026-03-23/director-pipeline-7axis-deep-dive.md
10. docs/2026-03-23/generation-coherence-deep-dive-report.md
11. docs/2026-03-23/current-state-situation-survey-report.md
12. docs/2026-03-23/daily-roadmap-2026-03-23.md

Task:
You are TERMINAL_ID. Run a bounded pre-rerun root-cause deep survey for FOCUS_NAME over the current live workspace state.

Hard constraints:
- Survey-only. No code changes.
- Do not interrupt or restart the live run.
- Do not create execution SSOTs.
- Do not create docs/temp queue artifacts.
- Prefer live source, artifact text, and DB truth over stale report wording.
- If an older claim is already fixed in live code, mark it stale instead of repeating it.

Primary scope:
PRIMARY_SCOPE

Required outputs:
- Final report: FINAL_REPORT_PATH
- Optional evidence manifest: EVIDENCE_PATH

Required report sections:
1. Executive Summary
2. Current Ownership / Flow Map
3. Focus-Scope Findings
4. Root-Cause Relevance
5. Quick Wins
6. False Leads / Non-Causes
7. Fresh-Run Relevance
8. Confidence And Limits

Rules:
- Every P0/P1 item must include file:line or artifact identifiers.
- Every recommendation must have one fix type:
  - comment-only
  - doc-only
  - observability-only
  - contract-cleanup
  - boundary-refactor
  - ignore
- Explicitly state:
  - Fresh-run-before-fix allowed: yes/no
  - Top 3 highest-ROI fixes before the next rerun

After saving, run:
- python scripts/check_utf8_hygiene.py FINAL_REPORT_PATH
- python scripts/ops_validator.py

In your final response:
- summarize the primary blocker first
- then the ranked root causes
- then the 3 highest-ROI fixes
- then confidence
- keep it concise
```

## 12. Terminal Overrides

| Terminal | FOCUS_NAME | PRIMARY_SCOPE | FINAL_REPORT_PATH | EVIDENCE_PATH |
|---|---|---|---|---|
| T1 | `Stage 2 contract and pacing static` | `modules/core/stage2_orchestrator.py, modules/core/stage2_finalizer.py` | `docs/2026-03-23/opus/pre-rerun-root-cause-t1-stage2-contract.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t1-stage2-contract-evidence.md` |
| T2 | `Stage 2 arc artifact and DB truth` | `projects/0_0323/logs/artifacts/stage2/**, projects/0_0323/plans/arcs/**, Stage 2 DB rows, Stage 2 runtime audit/session rows` | `docs/2026-03-23/opus/pre-rerun-root-cause-t2-stage2-artifact-truth.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t2-stage2-artifact-evidence.md` |
| T3 | `Stage 3 blueprint contract and context static` | `modules/core/stage3_orchestrator.py, modules/domain/agents/three_phase_blueprint_generator.py, modules/domain/agents/blueprint_ensemble.py` | `docs/2026-03-23/opus/pre-rerun-root-cause-t3-stage3-contract.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t3-stage3-contract-evidence.md` |
| T4 | `Stage 3 blueprint artifact and DB truth` | `projects/0_0323/logs/artifacts/stage3/**, projects/0_0323/plans/blueprints/**, Stage 3 DB rows, Stage 3 runtime audit/session rows` | `docs/2026-03-23/opus/pre-rerun-root-cause-t4-stage3-artifact-truth.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t4-stage3-artifact-evidence.md` |
| T5 | `Stage 4 write/fix/retry code chain` | `modules/core/stage4_interview_round.py, modules/core/stage4_retry_runtime.py, modules/core/stage4_reject_runtime.py, modules/domain/agents/chief_writer.py` | `docs/2026-03-23/opus/pre-rerun-root-cause-t5-stage4-write-fix.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t5-stage4-write-fix-evidence.md` |
| T6 | `Stage 4 attempt artifact truth` | `projects/0_0323/logs/artifacts/stage4/**, projects/0_0323/drafts/**` | `docs/2026-03-23/opus/pre-rerun-root-cause-t6-stage4-artifact-truth.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t6-stage4-artifact-evidence.md` |
| T7 | `Director verdict and post-select static chain` | `modules/domain/agents/director_ensemble.py, modules/domain/agents/director_auditor.py, modules/core/stage4_director_runtime.py, modules/core/stage4_post_pass_runtime.py, modules/core/stage4_outcome_runtime.py` | `docs/2026-03-23/opus/pre-rerun-root-cause-t7-verdict-chain.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t7-verdict-chain-evidence.md` |
| T8 | `Director and post-select DB/console parity` | `docs/2026-03-23/console.txt, projects/0_0323/logs/session/**, projects/0_0323/logs/runtime_audit.jsonl, relevant director and stage attempt DB rows` | `docs/2026-03-23/opus/pre-rerun-root-cause-t8-verdict-parity.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t8-verdict-parity-evidence.md` |
| T9 | `Context and retrieval support factors` | `modules/core/stage4_context_builder.py, modules/core/stage4_context_packets.py, modules/core/context_advisor.py, modules/core/vec_memory.py, modules/domain/agents/chief_writer_context.py, modules/domain/agents/chief_writer_context_packets.py, modules/domain/agents/continuity_arc.py, modules/validation/continuity_validator.py` | `docs/2026-03-23/opus/pre-rerun-root-cause-t9-context-retrieval.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t9-context-retrieval-evidence.md` |
| T10 | `Cross-layer artifact continuity` | `compare Stage 2 arc artifact, Stage 3 blueprints, and Stage 4 manuscripts/rejects for Arc 1 Episode 3 executable pressure and continuity` | `docs/2026-03-23/opus/pre-rerun-root-cause-t10-cross-layer-artifact.md` | `docs/2026-03-23/opus/pre-rerun-root-cause-t10-cross-layer-artifact-evidence.md` |

## 13. Terminal Dispatch One-Liners
- `넌 1번 터미널. docs/2026-03-23/opus-pre-rerun-root-cause-deep-survey-order.md를 읽고 T1 규칙대로 진행해.`
- `넌 2번 터미널. docs/2026-03-23/opus-pre-rerun-root-cause-deep-survey-order.md를 읽고 T2 규칙대로 진행해.`
- `넌 3번 터미널. docs/2026-03-23/opus-pre-rerun-root-cause-deep-survey-order.md를 읽고 T3 규칙대로 진행해.`
- `넌 4번 터미널. docs/2026-03-23/opus-pre-rerun-root-cause-deep-survey-order.md를 읽고 T4 규칙대로 진행해.`
- `넌 5번 터미널. docs/2026-03-23/opus-pre-rerun-root-cause-deep-survey-order.md를 읽고 T5 규칙대로 진행해.`
- `넌 6번 터미널. docs/2026-03-23/opus-pre-rerun-root-cause-deep-survey-order.md를 읽고 T6 규칙대로 진행해.`
- `넌 7번 터미널. docs/2026-03-23/opus-pre-rerun-root-cause-deep-survey-order.md를 읽고 T7 규칙대로 진행해.`
- `넌 8번 터미널. docs/2026-03-23/opus-pre-rerun-root-cause-deep-survey-order.md를 읽고 T8 규칙대로 진행해.`
- `넌 9번 터미널. docs/2026-03-23/opus-pre-rerun-root-cause-deep-survey-order.md를 읽고 T9 규칙대로 진행해.`
- `넌 10번 터미널. docs/2026-03-23/opus-pre-rerun-root-cause-deep-survey-order.md를 읽고 T10 규칙대로 진행해.`

## 14. Codex Merge Rule
- Opus gathers and writes the 10 lane reports.
- Codex later:
  - removes stale claims
  - merges cross-lane duplicates
  - ranks root causes
  - decides what becomes an execution SSOT
- Opus does not write the merged root-cause master conclusion.

## 15. 3-Pass Audit Record
- Pass 1
  - converted the prior single-lane order into a 10-terminal parallel survey bundle
  - fixed the scope around Stage 2, Stage 3, Stage 4, verdict chain, context, DB, console, and artifact truth
- Pass 2
  - assigned disjoint primary scopes, report paths, and optional evidence paths for T1 through T10
  - separated Opus collection from Codex merge authority
- Pass 3
  - embedded a reusable launch prompt plus per-terminal overrides and one-line dispatch text
  - rechecked that the order remains survey-only and non-interfering with the current run

## 16. Confidence
- Confidence: 98%
- Basis:
  - the order is bounded, survey-only, and does not depend on unstable external data
  - 10-lane split materially lowers cross-terminal duplication while preserving cross-layer coverage
  - output and merge responsibilities are explicit
