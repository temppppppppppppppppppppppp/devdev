Date: 2026-03-24
Status: final (3-pass audited)
Document Type: system-track parallel survey master order
Canonical Path: `docs/2026-03-24/stage2-stage3-residual-leakage-resurvey-10terminal-master-order.md`
Temp Mirror Path: none
Source Survey Docs:
- `docs/2026-03-24/stage2-stage3-episode-boundary-expanded-survey-report.md`
- `docs/2026-03-24/stage2-stage3-episode-boundary-wave1-execution-ssot.md`
- `docs/2026-03-24/stage2-stage3-episode-boundary-wave2-survey-report.md`
- `docs/2026-03-24/console.txt`
- `docs/2026-03-24/현상황요약.txt`
Evidence Artifacts:
- `projects/00_001/logs/episode_production.jsonl`
- `projects/00_001/logs/session/llm_io.jsonl`
- `projects/00_001/logs/artifacts/stage2/arc_001/attempt_01/final_arc__balanced.json`
- `projects/00_001/logs/artifacts/stage3/ep_0001/attempt_09/final_blueprint__emotion_focused.json`
- `projects/00_001/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__dialogue_focused.json`
- `projects/00_001/logs/artifacts/stage3/ep_0004/attempt_02/final_blueprint__emotion_focused.json`
Commit State:
- Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Baseline Dirty Summary: `dirty workspace; Wave 1 closed, Wave 2 survey finalized, fresh live-run evidence updated in docs/2026-03-24/console.txt and projects/00_001/logs/*`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Purpose

This document defines a parallel re-survey order for the residual Stage 2 -> Stage 3 leakage problem after Wave 1.

Goal:
- find the real remaining culprit, not the loudest secondary symptom
- use fresh live-run evidence to isolate the still-open seam that lets early-episode blueprints absorb later-episode material
- avoid opening the wrong Wave 2 based on stale assumptions about density

This is a survey-only master order, not an execution SSOT.

## 2. Why Re-Survey Now

Fresh live-run evidence invalidates the comforting interpretation that Wave 1 was enough and that only density remained.

Representative anchors:
- ep1 blueprint still ends in `20억 확보 + 법인 설립 완료 + 첫 투자 직전`
  - `projects/00_001/logs/artifacts/stage3/ep_0001/attempt_09/final_blueprint__emotion_focused.json:26`
  - `projects/00_001/logs/artifacts/stage3/ep_0001/attempt_09/final_blueprint__emotion_focused.json:34`
  - `projects/00_001/logs/artifacts/stage3/ep_0001/attempt_09/final_blueprint__emotion_focused.json:127`
  - `projects/00_001/logs/artifacts/stage3/ep_0001/attempt_09/final_blueprint__emotion_focused.json:146`
- ep3 still trips continuity firewall because `20억 현금화 / OTP 수령` replays after ep1 already consumed it
  - `projects/00_001/logs/episode_production.jsonl:5`
  - `projects/00_001/logs/episode_production.jsonl:6`
- ep4 still trips continuity firewall because `오피스텔 계약 / HTS 세팅 / WTI 진입` replays after ep3
  - `projects/00_001/logs/episode_production.jsonl:9`
  - `projects/00_001/logs/episode_production.jsonl:10`

Working implication:
- the dominant remaining problem is still leakage or overconsumption
- `episode_details` sparseness may still matter, but it is no longer the leading suspect for the next fix wave

## 3. Primary Questions

1. Which exact residual seam still allows ep1 to absorb ep3/ep4 material after Wave 1?
2. Is the culprit in:
   - Stage 2 arc payload composition
   - Stage 3 current-episode extraction
   - Stage 3 prompt assembly
   - Blueprint integrated-scenario synthesis
   - retrieval/context carryover
   - or a narrow combination of those?
3. Which previously suspected fields are now cleared by fresh live evidence?
4. Is `episode_details` density still only secondary, or is it interacting with a still-open leakage seam?
5. What is the smallest next execution scope that would actually cut the live residual culprit?

## 4. Hard Constraints

- survey-only; no code changes
- do not create an execution SSOT unless Codex explicitly asks for one after merge
- do not touch `docs/temp/`; queue is currently empty and must stay empty
- do not reopen Stage 4 redesign as the primary story
- do not default back to `episode_details density` unless the lane evidence positively rules out the residual leakage seams
- do not default to `move ep_count to Python`
- workspace is dirty; do not revert unrelated edits
- all P0/P1 claims must carry file anchors
- if a lane cannot prove a claim, it must mark it `not proven` instead of stretching

## 5. Survey Model

Every lane must classify its findings into one or more of:
- `confirmed residual leakage`
- `likely residual leakage`
- `secondary amplifier`
- `noise / not the culprit`
- `follow-up only`

Every lane must also state:
- `Can this seam alone explain ep1 overconsumption? yes/no`
- `Does this seam plausibly explain the ep3/ep4 continuity-firewall replay? yes/no`
- `Can this seam be fixed without reopening broad refactor work? yes/no`

## 6. Terminal Plan

Use 10 terminals. This scope is evidence-heavy enough to justify high parallelism, and the write surface is zero because this is survey-only.

| Terminal | Lane | Primary Scope | Final Report Path | Optional Evidence Path |
|---|---|---|---|---|
| T1 | Live Run Chronology | `docs/2026-03-24/console.txt`, `projects/00_001/logs/episode_production.jsonl`, `quality_metrics.jsonl`, `runtime_audit.jsonl` | `docs/2026-03-24/opus-residual/t1-live-run-chronology.md` | `docs/2026-03-24/opus-residual/t1-live-run-chronology-evidence.md` |
| T2 | Stage 2 Arc Payload | `final_arc__balanced.json`, `episode_details`, `joint_docs`, `state_changes`, `semantic_carryover`, `constraint_summary` | `docs/2026-03-24/opus-residual/t2-stage2-arc-payload.md` | `docs/2026-03-24/opus-residual/t2-stage2-arc-payload-evidence.md` |
| T3 | Stage 2 Validation / Guardrails | `stage2_validation_pipeline.py`, `arc_draft_validator.py`, `four_phase_arc_generator.py` | `docs/2026-03-24/opus-residual/t3-stage2-validation-guardrails.md` | `docs/2026-03-24/opus-residual/t3-stage2-validation-guardrails-evidence.md` |
| T4 | Current-Episode Extraction | `modules/core/tactical_utils.py`, `extract_episode_tactical`, `must_focus` path, episode focus extraction | `docs/2026-03-24/opus-residual/t4-current-episode-extraction.md` | `docs/2026-03-24/opus-residual/t4-current-episode-extraction-evidence.md` |
| T5 | Constraint Compiler Residuals | `blueprint_constraint_compiler.py`, `stop_line`, `state_changes`, `inherited_state`, `continuity`, `arc_constraint_summary` | `docs/2026-03-24/opus-residual/t5-constraint-compiler-residuals.md` | `docs/2026-03-24/opus-residual/t5-constraint-compiler-residuals-evidence.md` |
| T6 | Stage 3 Prompt Injection | `stage3_orchestrator.py`, treatment overview, advisory injection, continuity pins, semantic context assembly | `docs/2026-03-24/opus-residual/t6-stage3-prompt-injection.md` | `docs/2026-03-24/opus-residual/t6-stage3-prompt-injection-evidence.md` |
| T7 | Blueprint Synthesis / Integrated Scenario | `blueprint_ensemble.py`, `three_phase_blueprint_runtime.py`, integrated scenario fields, blueprint artifact structure | `docs/2026-03-24/opus-residual/t7-blueprint-synthesis-integrated-scenario.md` | `docs/2026-03-24/opus-residual/t7-blueprint-synthesis-integrated-scenario-evidence.md` |
| T8 | Stage 4 Contradiction Detection | `stage4_reject_runtime.py`, `stage4_post_pass_runtime.py`, conflict gates, V75-D blueprint patch path | `docs/2026-03-24/opus-residual/t8-stage4-contradiction-detection.md` | `docs/2026-03-24/opus-residual/t8-stage4-contradiction-detection-evidence.md` |
| T9 | LLM I/O / Retrieval Trace | `llm_io.jsonl`, retrieval observations, context budgets, surviving context slots | `docs/2026-03-24/opus-residual/t9-llm-io-retrieval-trace.md` | `docs/2026-03-24/opus-residual/t9-llm-io-retrieval-trace-evidence.md` |
| T10 | Artifact Truth Diff Ledger | stage2 arc -> stage3 blueprint -> stage4 reject for ep1-4; cross-episode replay ledger | `docs/2026-03-24/opus-residual/t10-artifact-truth-diff-ledger.md` | `docs/2026-03-24/opus-residual/t10-artifact-truth-diff-ledger-evidence.md` |

## 7. Lane Questions

### T1. Live Run Chronology
- What exactly happened in the fresh run, in time order?
- Which rejections are true regressions of the old failure family, and which are new/local?
- Did Stage 3 appear to succeed while Stage 4 later disproved it?

### T2. Stage 2 Arc Payload
- Which Stage 2 fields already contain multi-episode collapsed state?
- Is the problem already present in `final_arc__balanced.json` before Stage 3 touches it?
- Which fields are safe current-episode guidance vs arc-global plan?

### T3. Stage 2 Validation / Guardrails
- What guardrails exist today?
- Which of them protect `tactical_doc` only and miss `episode_details` or other payloads?
- Is any existing guard strong enough that allocation balance can be demoted confidently?

### T4. Current-Episode Extraction
- Does the shared extraction path really isolate `ep_num`, or does it still carry wider arc material?
- Is `must_focus` clean while other derived fields are dirty, or is the extraction layer itself leaking?
- Can this seam alone explain why ep1 still absorbs ep3/ep4?

### T5. Constraint Compiler Residuals
- After Wave 1, what residual leakage remains in `BlueprintConstraintCompiler`?
- Are stop-line and state-change fixes now clean, or are other compiler outputs still arc-global in practice?
- Is `inherited_state` or another compiler output still too permissive?

### T6. Stage 3 Prompt Injection
- Which prompt injections still carry arc-global or future-episode material?
- Did treatment block quarantine help at all in the live run, or is another injection surface dominating now?
- Are continuity pins or advisory sections over-loud relative to episode-local instructions?

### T7. Blueprint Synthesis / Integrated Scenario
- Which component synthesizes the overgrown `integrated_scenario`?
- Is the blueprint runtime or ensemble layer re-inflating full-arc narrative even when prompt constraints are cleaner?
- Is there a hidden `arc summary -> integrated scenario` transform that ignores episode boundaries?

### T8. Stage 4 Contradiction Detection
- What exact contradiction patterns are still caught at ep3/ep4?
- Do those contradictions point upstream to Stage 3 blueprint design, or to Stage 4 candidate generation?
- Is Stage 4 correctly diagnosing an upstream blueprint fault?

### T9. LLM I/O / Retrieval Trace
- What actually reached the model in the fresh run?
- Which context blocks survived truncation and which were loudest?
- Do live prompts still contain future-episode narrative fuel despite the Wave 1 patch?

### T10. Artifact Truth Diff Ledger
- For ep1-4, what did Stage 2 say, what did Stage 3 blueprint, and what did Stage 4 reject?
- Build the exact replay chain showing where later-episode content was first consumed
- Produce the clearest possible culprit shortlist for Codex merge

## 8. Required Output Contract

Each lane writes:
- one final markdown report
- one optional raw evidence ledger

Common report sections:
1. Executive Summary
2. Included Coverage / Exclusions
3. Key Evidence
4. Findings Ranked
5. Cleared Non-Culprits
6. Residual Culprit Candidate
7. Next-Scope Recommendation
8. Confidence And Limits

Mandatory lines in every report:
- `Can this seam alone explain ep1 overconsumption: yes/no`
- `Can this seam explain ep3/ep4 continuity-firewall replay: yes/no`
- `Can this seam be fixed in a bounded next wave: yes/no`

Do not create execution SSOTs, roadmaps, or temp queue items.

## 9. Read Order

Every terminal should read these first:
1. `AGENTS.md`
2. `docs/implementation/system-order-init-harness.md`
3. `docs/implementation/system-full-survey-execution-harness.md`
4. `docs/implementation/document-3pass-audit-harness.md`
5. `docs/2026-03-24/stage2-stage3-episode-boundary-expanded-survey-report.md`
6. `docs/2026-03-24/stage2-stage3-episode-boundary-wave1-execution-ssot.md`
7. `docs/2026-03-24/stage2-stage3-episode-boundary-wave2-survey-report.md`
8. `docs/2026-03-24/console.txt`
9. `docs/2026-03-24/현상황요약.txt`
10. `docs/2026-03-24/stage2-stage3-residual-leakage-resurvey-10terminal-master-order.md`

## 10. Common Opus Prompt

Use this as the common launch prompt. Only substitute the lane-specific values from section 11.

```text
System-track survey-only order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/system-full-survey-execution-harness.md
4. docs/implementation/document-3pass-audit-harness.md
5. docs/2026-03-24/stage2-stage3-episode-boundary-expanded-survey-report.md
6. docs/2026-03-24/stage2-stage3-episode-boundary-wave1-execution-ssot.md
7. docs/2026-03-24/stage2-stage3-episode-boundary-wave2-survey-report.md
8. docs/2026-03-24/console.txt
9. docs/2026-03-24/현상황요약.txt
10. docs/2026-03-24/stage2-stage3-residual-leakage-resurvey-10terminal-master-order.md

Task:
Run a bounded residual-leakage re-survey for LANE_NAME using the fresh live-run evidence.

Primary goal:
Determine whether this lane contains the still-open culprit that lets early-episode blueprints absorb later-episode content after Wave 1.

Hard constraints:
- Survey only. No code changes.
- Do not create execution SSOTs, roadmaps, or docs/temp artifacts.
- Prefer fresh live-run evidence over older survey assumptions.
- Do not default back to density or ep_count redesign unless your lane actually proves that.
- Workspace is dirty. Do not revert unrelated edits.
- Findings must be anchored to concrete file paths and line numbers where possible.
- If your lane cannot prove a claim, mark it not proven.

Primary scope:
PRIMARY_SCOPE

Required outputs:
- Final report: FINAL_REPORT_PATH
- Optional evidence ledger: EVIDENCE_PATH

Required report sections:
1. Executive Summary
2. Included Coverage / Exclusions
3. Key Evidence
4. Findings Ranked
5. Cleared Non-Culprits
6. Residual Culprit Candidate
7. Next-Scope Recommendation
8. Confidence And Limits

Mandatory conclusions:
- Can this seam alone explain ep1 overconsumption: yes/no
- Can this seam explain ep3/ep4 continuity-firewall replay: yes/no
- Can this seam be fixed in a bounded next wave: yes/no

Document save rule:
- Run a document 3-pass audit before saving.
- If confidence is 95% or higher, save status as final.
- If confidence is below 95%, save status as provisional.

After saving, run:
- python scripts/check_utf8_hygiene.py FINAL_REPORT_PATH

In your final response:
- findings first
- then your residual culprit candidate
- then confidence
- then one bounded next-scope recommendation
```

## 11. Terminal Overrides

| Terminal | LANE_NAME | PRIMARY_SCOPE | FINAL_REPORT_PATH | EVIDENCE_PATH |
|---|---|---|---|---|
| T1 | `Live Run Chronology` | `docs/2026-03-24/console.txt, projects/00_001/logs/episode_production.jsonl, quality_metrics.jsonl, runtime_audit.jsonl` | `docs/2026-03-24/opus-residual/t1-live-run-chronology.md` | `docs/2026-03-24/opus-residual/t1-live-run-chronology-evidence.md` |
| T2 | `Stage 2 Arc Payload` | `projects/00_001/logs/artifacts/stage2/arc_001/attempt_01/final_arc__balanced.json, episode_details, joint_docs, state_changes, semantic_carryover, constraint_summary` | `docs/2026-03-24/opus-residual/t2-stage2-arc-payload.md` | `docs/2026-03-24/opus-residual/t2-stage2-arc-payload-evidence.md` |
| T3 | `Stage 2 Validation / Guardrails` | `modules/core/stage2_validation_pipeline.py, modules/domain/agents/arc_draft_validator.py, modules/domain/agents/four_phase_arc_generator.py` | `docs/2026-03-24/opus-residual/t3-stage2-validation-guardrails.md` | `docs/2026-03-24/opus-residual/t3-stage2-validation-guardrails-evidence.md` |
| T4 | `Current-Episode Extraction` | `modules/core/tactical_utils.py, extract_episode_tactical, episode focus extraction, must_focus derivation path` | `docs/2026-03-24/opus-residual/t4-current-episode-extraction.md` | `docs/2026-03-24/opus-residual/t4-current-episode-extraction-evidence.md` |
| T5 | `Constraint Compiler Residuals` | `modules/domain/agents/blueprint_constraint_compiler.py, stop_line, state_changes, continuity, inherited_state, arc_constraint_summary` | `docs/2026-03-24/opus-residual/t5-constraint-compiler-residuals.md` | `docs/2026-03-24/opus-residual/t5-constraint-compiler-residuals-evidence.md` |
| T6 | `Stage 3 Prompt Injection` | `modules/core/stage3_orchestrator.py, treatment overview, advisory injection, continuity pins, semantic context assembly` | `docs/2026-03-24/opus-residual/t6-stage3-prompt-injection.md` | `docs/2026-03-24/opus-residual/t6-stage3-prompt-injection-evidence.md` |
| T7 | `Blueprint Synthesis / Integrated Scenario` | `modules/domain/agents/blueprint_ensemble.py, modules/domain/agents/three_phase_blueprint_runtime.py, integrated_scenario fields, blueprint artifact contract` | `docs/2026-03-24/opus-residual/t7-blueprint-synthesis-integrated-scenario.md` | `docs/2026-03-24/opus-residual/t7-blueprint-synthesis-integrated-scenario-evidence.md` |
| T8 | `Stage 4 Contradiction Detection` | `modules/core/stage4_reject_runtime.py, modules/core/stage4_post_pass_runtime.py, continuity_firewall, post_select_conflict, V75-D blueprint patch path` | `docs/2026-03-24/opus-residual/t8-stage4-contradiction-detection.md` | `docs/2026-03-24/opus-residual/t8-stage4-contradiction-detection-evidence.md` |
| T9 | `LLM I/O / Retrieval Trace` | `projects/00_001/logs/session/llm_io.jsonl, retrieval_observation records, context budget survivors, stage3/stage4 prompt trace` | `docs/2026-03-24/opus-residual/t9-llm-io-retrieval-trace.md` | `docs/2026-03-24/opus-residual/t9-llm-io-retrieval-trace-evidence.md` |
| T10 | `Artifact Truth Diff Ledger` | `stage2 arc -> stage3 blueprint -> stage4 reject for ep1-4; replay ledger for 20억/OTP/오피스텔/WTI chain` | `docs/2026-03-24/opus-residual/t10-artifact-truth-diff-ledger.md` | `docs/2026-03-24/opus-residual/t10-artifact-truth-diff-ledger-evidence.md` |

## 12. Terminal Dispatch One-Liners

Use the format the user requested: `path + 넌 n번 터미널`.

- `docs/2026-03-24/stage2-stage3-residual-leakage-resurvey-10terminal-master-order.md + 넌 1번 터미널`
- `docs/2026-03-24/stage2-stage3-residual-leakage-resurvey-10terminal-master-order.md + 넌 2번 터미널`
- `docs/2026-03-24/stage2-stage3-residual-leakage-resurvey-10terminal-master-order.md + 넌 3번 터미널`
- `docs/2026-03-24/stage2-stage3-residual-leakage-resurvey-10terminal-master-order.md + 넌 4번 터미널`
- `docs/2026-03-24/stage2-stage3-residual-leakage-resurvey-10terminal-master-order.md + 넌 5번 터미널`
- `docs/2026-03-24/stage2-stage3-residual-leakage-resurvey-10terminal-master-order.md + 넌 6번 터미널`
- `docs/2026-03-24/stage2-stage3-residual-leakage-resurvey-10terminal-master-order.md + 넌 7번 터미널`
- `docs/2026-03-24/stage2-stage3-residual-leakage-resurvey-10terminal-master-order.md + 넌 8번 터미널`
- `docs/2026-03-24/stage2-stage3-residual-leakage-resurvey-10terminal-master-order.md + 넌 9번 터미널`
- `docs/2026-03-24/stage2-stage3-residual-leakage-resurvey-10terminal-master-order.md + 넌 10번 터미널`

## 13. Codex Merge Rule

Opus lanes stop at their own lane reports.

Codex owns:
- stale claim cleanup
- duplicate finding merge
- culprit ranking across lanes
- deciding whether the next artifact is:
  - another compact survey
  - a bounded execution SSOT
  - or a live-run-plus-patch hybrid

Lane agents must not create the merge audit or the next execution SSOT.

## 14. 3-Pass Audit Record

- Pass 1
  - confirmed this is a survey master order, not an execution SSOT
  - confirmed parallel lane split is justified by the evidence-heavy nature of the task
- Pass 2
  - confirmed the document is grounded in fresh live-run evidence rather than stale pre-Wave-1 assumptions
  - confirmed canonical/temp semantics are correct for a survey-only artifact
- Pass 3
  - confirmed lane scopes are disjoint enough to reduce overlap
  - confirmed the output contract stops premature implementation and keeps Codex as merge owner

## 15. Confidence

- Confidence: 97%
- Basis:
  - fresh live-run evidence clearly shows the old failure signature still exists
  - the next step is investigation, not blind Wave 2 density work
  - 10-way lane decomposition is bounded and materially useful for culprit isolation
