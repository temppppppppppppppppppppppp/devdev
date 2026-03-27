Date: 2026-03-27
Status: final (3-pass audited, order scope)
Document Type: parallel static survey master order
Canonical Path: `docs/2026-03-27/rol-llm-friendliness-gimmick-elegance-6terminal-master-order.md`
Temp Mirror Path: none
Source Survey Docs:
- `docs/2026-03-23/llm-codebase-orientation-pack.md`
- `docs/2026-03-23/llm-friendliness-post-survey-execution-ssot.md`
- `docs/2026-03-24/rol-llm-friendliness-6terminal-master-order.md`
- `docs/2026-03-26/llm-multi-provider-context-note.md`
- `docs/2026-03-27/per-work-fact-system-synthesis-memo.md`
- `docs/2026-03-27/per-work-fact-contract-alignment-residual-survey.md`

Commit State:
- Baseline Commit: `eb7a41d86a52b075861bcbd59a402622ab08d6cc`
- Baseline Dirty Summary: `dirty: tracked llm_router/provider/context/validator surfaces, docs/temp/queue-state.json, project logs/artifacts; untracked multi-provider docs, fact docs, anthropic_vertex provider scaffolding/tests`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Purpose

This document defines a bounded `ROL` master survey order for:
- `LLM friendliness`
- `gimmick elegance`

The target is the current live workspace, not historical intent.

For this order, `gimmick elegance` means:
- special behavior is localized
- ownership is explicit
- precedence is explicit
- provider or genre tricks are not smuggled through hidden state
- an LLM can trace the gimmick without replaying repo history

This is a survey order only. It is not an implementation order.

## 2. Current Frame

- `docs/2026-03-23/llm-friendliness-post-survey-execution-ssot.md` is already closed.
  - Earlier low-blast comment/doc quick wins were landed.
  - This wave must not reopen already-settled clarity items as the main story.
- `docs/2026-03-26/llm-multi-provider-context-note.md` makes provider/router elegance a live system question.
- `docs/2026-03-27/per-work-fact-system-synthesis-memo.md` and `docs/2026-03-27/per-work-fact-contract-alignment-residual-survey.md` make prompt-facing authority, injection precedence, and genre-specific gimmick handling a live system question.
- `docs/temp/queue-state.json` currently reports:
  - `queue_mode: empty`
  - `active_item_count: 0`
- The workspace is dirty in live source areas. Treat that as evidence to inspect, not as a patch invitation.

This wave is for static survey, ranking, and merge-ready lane reports.

## 3. Absolute Constraints

These constraints are mandatory.

- `STATIC SURVEY ONLY.`
- `NO CODE MODIFICATION.`
- `NO TEST / CONFIG / SCRIPT / SOURCE PATCHING.`
- `NO docs/temp EDITS.`
- `NO queue-state UPDATE.`
- `NO execution SSOT creation.`
- `NO roadmap creation.`
- `NO live run, no pytest, no patch wave, no git cleanup.`

Allowed writes for each terminal:
- its assigned final report path
- its optional evidence path

Forbidden writes:
- any production code file
- any test file
- any config file
- any script file
- any runtime artifact
- any file already dirty in the worktree
- any `docs/temp/*` file
- any queue or closure artifact

If a finding seems to demand a patch:
- record the finding only
- classify the fix type
- do not implement

If a terminal cannot complete the survey without changing code:
- stop
- report the blocker
- do not improvise a patch

## 4. Survey Model

Every finding must map to one or more of these axes.

| Axis | Question | Primary Focus |
| --- | --- | --- |
| Navigation | Can a cold LLM find where to start and what to read next? | entrypoint, reading order, stale maps, owner shell visibility |
| Authority | Can the final owner of a decision or side effect be identified quickly? | orchestrator vs runtime vs sink owner |
| Contract | Can payload meaning be decoded without file-hopping chaos? | dict/dataclass/result envelope meaning |
| Observability | Can an LLM explain what happened and why? | console, audit, DB, JSONL, metrics, operator truth |
| Gimmick Elegance | Are special mechanisms explicit, localized, and composable rather than hidden? | provider/backend/family split, prompt injection precedence, fact authority, retry heuristics, genre gates |
| Local Readability | Does a local code block reveal phase, mutation, and blast radius honestly? | naming honesty, boundary comments, mutation visibility |

### Gimmick-Elegance Test

Call a gimmick `elegant` only if most of these are true:
- one obvious owner exists
- its input contract is explicit
- precedence over neighboring gimmicks is explicit
- hidden mutable side channels are minimal or clearly annotated
- the gimmick can be traced in 2-4 file hops, not 8-12

Call a gimmick `inelegant` if it mainly survives by:
- provider-native assumptions leaking into shared code
- duplicated precedence rules
- silent fallbacks
- undocumented side-channel state
- genre-specific exceptions with no SSOT note

## 5. Fix-Type Priority Rule

This wave is not a refactor-hunting contest.

Lane reports must prefer:
1. `comment-only`
2. `doc-only`
3. `observability-only`
4. `contract-cleanup`
5. `boundary-refactor`
6. `ignore`

Rules:
- `Top Quick Wins` must contain at least 5 items.
- More than half of `Top Quick Wins` must be `comment-only`, `doc-only`, or `observability-only`.
- `Deferred Refactor Candidates` must be capped at 3.
- If a gimmick can be made understandable by a map, contract note, or observability aid, do not escalate it into refactor-first.

## 6. Terminal Plan

All 6 terminals are static-survey lanes.

| Terminal | Lane | Primary Scope | Final Report Path | Optional Evidence Path |
| --- | --- | --- | --- | --- |
| T1 | Navigation / Entry / Read Order | `AGENTS.md`, `main_a.py`, `modules/api/**/*.py`, `stage01_helpers.py`, `stage2_orchestrator.py`, `stage3_orchestrator.py`, `stage4_orchestrator.py`, orientation-pack drift | `docs/2026-03-27/opus/rol-llm-gimmick-t1-navigation-entry.md` | `docs/2026-03-27/opus/rol-llm-gimmick-t1-navigation-entry-evidence.md` |
| T2 | Provider / Router / Backend-Family-Capability Elegance | `config/models.yaml`, `modules/core/models_config.py`, `modules/core/llm_provider.py`, `modules/core/llm_router.py`, `modules/core/providers/**/*.py`, `modules/api/process_runner.py`, `tests/test_llm_router.py`, `docs/2026-03-26/llm-multi-provider-context-note.md` | `docs/2026-03-27/opus/rol-llm-gimmick-t2-provider-router-elegance.md` | `docs/2026-03-27/opus/rol-llm-gimmick-t2-provider-router-elegance-evidence.md` |
| T3 | Stage 4 Authority / Verdict / Retry Gimmicks | `modules/core/stage4_interview_round.py`, `modules/core/stage4_director_runtime.py`, `modules/core/stage4_post_processor.py`, `modules/core/stage4_post_pass_runtime.py`, `modules/core/stage4_reject_runtime.py`, `modules/core/stage4_retry_runtime.py`, `modules/domain/agents/director_ensemble.py` | `docs/2026-03-27/opus/rol-llm-gimmick-t3-stage4-authority-verdict.md` | `docs/2026-03-27/opus/rol-llm-gimmick-t3-stage4-authority-verdict-evidence.md` |
| T4 | Writer / Prompt / Context Injection Elegance | `modules/domain/agents/chief_writer.py`, `modules/domain/agents/chief_writer_context.py`, `modules/domain/agents/chief_writer_context_packets.py`, `modules/domain/agents/chief_writer_prompts.py`, `modules/core/writer_template.py`, `modules/core/prompt_builder.py`, `modules/core/stage4_context_builder.py`, `modules/core/stage4_context_packets.py` | `docs/2026-03-27/opus/rol-llm-gimmick-t4-writer-context-injection.md` | `docs/2026-03-27/opus/rol-llm-gimmick-t4-writer-context-injection-evidence.md` |
| T5 | Fact Authority / Genre Gimmick / Contract State | `modules/core/stage3_orchestrator.py`, `modules/core/world_state.py`, `modules/core/fact_ledger.py`, `modules/domain/agents/state_tracker*.py`, `modules/validation/blocking_validator*.py`, `docs/2026-03-27/per-work-fact-system-synthesis-memo.md`, `docs/2026-03-27/per-work-fact-contract-alignment-residual-survey.md`, genre-specific rule surfaces needed for technique/realm or similar gates | `docs/2026-03-27/opus/rol-llm-gimmick-t5-fact-authority-genre-state.md` | `docs/2026-03-27/opus/rol-llm-gimmick-t5-fact-authority-genre-state-evidence.md` |
| T6 | Observability / Peripheral / No-Action Sweep | `modules/core/db_manager.py`, `modules/core/pass_rate_monitor.py`, `modules/core/logger.py`, `modules/core/metrics_collector.py`, `modules/core/session_logger.py`, `scripts/`, `tests/`, `UI/`, `geuldobi-desktop/`, `docs/implementation/`, stale authority/reference sweep, settled-zone collection | `docs/2026-03-27/opus/rol-llm-gimmick-t6-observability-peripheral.md` | `docs/2026-03-27/opus/rol-llm-gimmick-t6-observability-peripheral-evidence.md` |

## 7. Lane Questions

### T1. Navigation / Entry / Read Order
- Can a cold LLM identify the starting file and lane-expansion order quickly?
- Is the orientation pack still live, or already stale against current source?
- Are owner shells and runtime modules distinguishable without history replay?
- Are there gimmicks hidden inside entry routing or compat shells?

### T2. Provider / Router / Backend-Family-Capability Elegance
- Is the provider story still clean, or does shared code remain Gemini-first in disguised form?
- Can `backend`, `family`, `model`, and `capability` be distinguished without guesswork?
- Are provider-specific gimmicks localized in adapters, or leaking into shared owners?
- Are launch-time credential and observability contracts clean enough for an LLM to reason about safely?

### T3. Stage 4 Authority / Verdict / Retry Gimmicks
- Can an LLM find the final verdict owner quickly?
- Are retry, reject, post-pass, and persistence boundaries explicit?
- Are there silent or implicit channels that make Stage 4 reasoning fragile?
- Which gimmicks are real design moves, and which are legacy hidden-state residue?

### T4. Writer / Prompt / Context Injection Elegance
- Can an LLM understand what reaches the writer, in what order, and why?
- Is context assembly explicit about precedence, truncation, and packet ownership?
- Are stage4/context/writer gimmicks composed cleanly, or layered by accretion?
- Which quick wins reduce comprehension cost without touching behavior?

### T5. Fact Authority / Genre Gimmick / Contract State
- Is fact authority explicit enough for cross-episode and genre-specific gimmicks?
- Can an LLM tell which layer wins on conflict?
- Are technique/realm, membership, or other genre gates modeled elegantly or only implied?
- Which residual seams are prompt-only, validator-only, pre-check candidates, or deferred modeling?

### T6. Observability / Peripheral / No-Action Sweep
- Can an LLM explain operator truth across console, audit, DB, JSONL, and metrics?
- Which peripheral directories increase search cost without adding authority?
- Which stale references should be recorded as no-action, settled, or cleanup candidates?
- Which areas should explicitly stay out of the next execution wave?

## 8. Output Contract

Each terminal may create:
- one final report
- one optional evidence manifest

### 8.1 Final Report
- Path: lane-specific `Final Report Path`
- Format: human-readable markdown
- Status:
  - `final` if confidence is `95%` or higher
  - `provisional` if confidence is below `95%`
- Must pass a document 3-pass audit before save

### 8.2 Optional Evidence Manifest
- Path: lane-specific `Optional Evidence Path`
- Purpose:
  - raw path inventory
  - anchor list
  - short evidence ledger
- Not a substitute for the final report

### 8.3 No Temp Queue Artifacts
- This wave is survey-only.
- Do not create execution SSOTs.
- Do not create roadmaps.
- Do not create or refresh `docs/temp/*` queue artifacts.
- Do not modify `docs/temp/queue-state.json`.

### 8.4 Codex Merge Layer
After all 6 lane reports are complete, Codex may create:
- `docs/2026-03-27/rol-llm-friendliness-gimmick-elegance-6terminal-merge-audit.md`

Lane terminals must not create the merge document.

## 9. Mandatory Report Structure

Every lane report must contain:
1. `Executive Summary`
2. `Included Coverage / Exclusions`
3. `Current Read Order / Ownership / Gimmick Map`
4. `Top Hotspots`
5. `Top Quick Wins`
6. `Gimmick Elegance Judgment`
7. `Deferred Refactor Candidates`
8. `No-Action / Settled Areas`
9. `Cross-Lane Handoff Notes`
10. `Confidence And Limits`

Mandatory rules:
- Every `P0` or `P1` finding must have `file:line` anchors.
- Every recommendation must have one fix type.
- Allowed fix types:
  - `comment-only`
  - `doc-only`
  - `observability-only`
  - `contract-cleanup`
  - `boundary-refactor`
  - `ignore`
- Every report must explicitly state:
  - `Navigation-ready for this lane: yes/no`
  - `Cheap-fix-first verdict: yes/no`
  - `Gimmick-elegance verdict: elegant / mixed / inelegant`
  - `Boundary-refactor can wait: yes/no`
  - `Top 3 highest-ROI quick wins in this lane`

## 10. Read Order

Every terminal reads these first, in this exact order:

1. `AGENTS.md`
2. `docs/implementation/system-order-init-harness.md`
3. `docs/implementation/system-full-survey-execution-harness.md`
4. `docs/implementation/document-3pass-audit-harness.md`
5. `docs/implementation/commit-state-minimal-contract.md`
6. `docs/2026-03-23/llm-codebase-orientation-pack.md`
7. `docs/2026-03-23/llm-friendliness-post-survey-execution-ssot.md`
8. `docs/2026-03-24/rol-llm-friendliness-6terminal-master-order.md`
9. `docs/2026-03-26/llm-multi-provider-context-note.md`
10. `docs/2026-03-27/per-work-fact-system-synthesis-memo.md`
11. `docs/2026-03-27/per-work-fact-contract-alignment-residual-survey.md`
12. `docs/2026-03-27/rol-llm-friendliness-gimmick-elegance-6terminal-master-order.md`

## 11. Launch Prompt

Use this shared launch prompt, replacing `LANE_NAME`, `PRIMARY_SCOPE`, `FINAL_REPORT_PATH`, and `EVIDENCE_PATH` per terminal.

```text
System-track static survey order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/system-full-survey-execution-harness.md
4. docs/implementation/document-3pass-audit-harness.md
5. docs/implementation/commit-state-minimal-contract.md
6. docs/2026-03-23/llm-codebase-orientation-pack.md
7. docs/2026-03-23/llm-friendliness-post-survey-execution-ssot.md
8. docs/2026-03-24/rol-llm-friendliness-6terminal-master-order.md
9. docs/2026-03-26/llm-multi-provider-context-note.md
10. docs/2026-03-27/per-work-fact-system-synthesis-memo.md
11. docs/2026-03-27/per-work-fact-contract-alignment-residual-survey.md
12. docs/2026-03-27/rol-llm-friendliness-gimmick-elegance-6terminal-master-order.md

Task:
Run a bounded static survey for LANE_NAME over the current live workspace state.

Primary goal:
Assess whether this lane is easy for an LLM to navigate, reason about, and modify safely, and whether its gimmicks are elegant rather than hidden or accreted.

Absolute constraints:
- STATIC SURVEY ONLY.
- NO CODE MODIFICATION.
- NO TEST / CONFIG / SCRIPT / SOURCE PATCHING.
- NO docs/temp EDITS.
- NO queue-state UPDATE.
- NO execution SSOT creation.
- NO roadmap creation.
- NO live run, no pytest, no patch wave, no git cleanup.
- The only allowed writes are FINAL_REPORT_PATH and optional EVIDENCE_PATH.
- Do not edit any already-dirty source file.
- If a finding seems to need a patch, record it only. Do not implement.

Primary scope:
PRIMARY_SCOPE

Required output:
- Final report: FINAL_REPORT_PATH
- Optional evidence manifest: EVIDENCE_PATH

Required report sections:
1. Executive Summary
2. Included Coverage / Exclusions
3. Current Read Order / Ownership / Gimmick Map
4. Top Hotspots
5. Top Quick Wins
6. Gimmick Elegance Judgment
7. Deferred Refactor Candidates
8. No-Action / Settled Areas
9. Cross-Lane Handoff Notes
10. Confidence And Limits

Rules:
- Every P0/P1 finding must have file:line anchors.
- Every recommendation must have one fix type:
  - comment-only
  - doc-only
  - observability-only
  - contract-cleanup
  - boundary-refactor
  - ignore
- Top Quick Wins must contain at least 5 items.
- More than half of Top Quick Wins must be comment/doc/observability items.
- Deferred Refactor Candidates must be capped at 3.
- Explicitly state:
  - Navigation-ready for this lane: yes/no
  - Cheap-fix-first verdict: yes/no
  - Gimmick-elegance verdict: elegant / mixed / inelegant
  - Boundary-refactor can wait: yes/no
  - Top 3 highest-ROI quick wins in this lane

Document save rule:
- Run a document 3-pass audit before saving.
- If confidence is 95% or higher, save status as final.
- If confidence is below 95%, save status as provisional.

After saving, run:
- python scripts/check_utf8_hygiene.py FINAL_REPORT_PATH

In your final response:
- summarize top findings first
- then confidence
- then the top 3 quick wins
- keep it concise
```

## 12. Terminal Overrides

| Terminal | LANE_NAME | PRIMARY_SCOPE | FINAL_REPORT_PATH | EVIDENCE_PATH |
| --- | --- | --- | --- | --- |
| T1 | `Navigation / Entry / Read Order` | `AGENTS.md, main_a.py, modules/api/**/*.py, stage01_helpers.py, stage2_orchestrator.py, stage3_orchestrator.py, stage4_orchestrator.py, orientation-pack drift` | `docs/2026-03-27/opus/rol-llm-gimmick-t1-navigation-entry.md` | `docs/2026-03-27/opus/rol-llm-gimmick-t1-navigation-entry-evidence.md` |
| T2 | `Provider / Router / Backend-Family-Capability Elegance` | `config/models.yaml, modules/core/models_config.py, modules/core/llm_provider.py, modules/core/llm_router.py, modules/core/providers/**/*.py, modules/api/process_runner.py, tests/test_llm_router.py, llm-multi-provider-context-note.md` | `docs/2026-03-27/opus/rol-llm-gimmick-t2-provider-router-elegance.md` | `docs/2026-03-27/opus/rol-llm-gimmick-t2-provider-router-elegance-evidence.md` |
| T3 | `Stage 4 Authority / Verdict / Retry Gimmicks` | `modules/core/stage4_interview_round.py, modules/core/stage4_director_runtime.py, modules/core/stage4_post_processor.py, modules/core/stage4_post_pass_runtime.py, modules/core/stage4_reject_runtime.py, modules/core/stage4_retry_runtime.py, modules/domain/agents/director_ensemble.py` | `docs/2026-03-27/opus/rol-llm-gimmick-t3-stage4-authority-verdict.md` | `docs/2026-03-27/opus/rol-llm-gimmick-t3-stage4-authority-verdict-evidence.md` |
| T4 | `Writer / Prompt / Context Injection Elegance` | `modules/domain/agents/chief_writer.py, modules/domain/agents/chief_writer_context.py, modules/domain/agents/chief_writer_context_packets.py, modules/domain/agents/chief_writer_prompts.py, modules/core/writer_template.py, modules/core/prompt_builder.py, modules/core/stage4_context_builder.py, modules/core/stage4_context_packets.py` | `docs/2026-03-27/opus/rol-llm-gimmick-t4-writer-context-injection.md` | `docs/2026-03-27/opus/rol-llm-gimmick-t4-writer-context-injection-evidence.md` |
| T5 | `Fact Authority / Genre Gimmick / Contract State` | `modules/core/stage3_orchestrator.py, modules/core/world_state.py, modules/core/fact_ledger.py, modules/domain/agents/state_tracker*.py, modules/validation/blocking_validator*.py, per-work-fact-system-synthesis-memo.md, per-work-fact-contract-alignment-residual-survey.md, genre-specific technique/realm or similar gate surfaces as needed` | `docs/2026-03-27/opus/rol-llm-gimmick-t5-fact-authority-genre-state.md` | `docs/2026-03-27/opus/rol-llm-gimmick-t5-fact-authority-genre-state-evidence.md` |
| T6 | `Observability / Peripheral / No-Action Sweep` | `modules/core/db_manager.py, modules/core/pass_rate_monitor.py, modules/core/logger.py, modules/core/metrics_collector.py, modules/core/session_logger.py, scripts/, tests/, UI/, geuldobi-desktop/, docs/implementation/, stale authority/reference sweep, settled-zone collection` | `docs/2026-03-27/opus/rol-llm-gimmick-t6-observability-peripheral.md` | `docs/2026-03-27/opus/rol-llm-gimmick-t6-observability-peripheral-evidence.md` |

## 13. Terminal Dispatch One-Liners

Use these verbatim if needed.

- `docs/2026-03-27/rol-llm-friendliness-gimmick-elegance-6terminal-master-order.md + 넌 1번 터미널로 실행해. T1 규칙으로 진행해.`
- `docs/2026-03-27/rol-llm-friendliness-gimmick-elegance-6terminal-master-order.md + 넌 2번 터미널로 실행해. T2 규칙으로 진행해.`
- `docs/2026-03-27/rol-llm-friendliness-gimmick-elegance-6terminal-master-order.md + 넌 3번 터미널로 실행해. T3 규칙으로 진행해.`
- `docs/2026-03-27/rol-llm-friendliness-gimmick-elegance-6terminal-master-order.md + 넌 4번 터미널로 실행해. T4 규칙으로 진행해.`
- `docs/2026-03-27/rol-llm-friendliness-gimmick-elegance-6terminal-master-order.md + 넌 5번 터미널로 실행해. T5 규칙으로 진행해.`
- `docs/2026-03-27/rol-llm-friendliness-gimmick-elegance-6terminal-master-order.md + 넌 6번 터미널로 실행해. T6 규칙으로 진행해.`

## 14. Codex Merge Rule

Lane terminals stop at:
- evidence gathering
- lane report writing
- lane-level triage

Codex handles:
- stale-finding removal
- cross-lane merge
- duplicate collapse
- quick-win vs contract-cleanup vs long-term refactor sorting
- merge-audit drafting
- later execution-doc promotion judgment if explicitly requested

Lane terminals do not decide implementation.

## 15. 3-Pass Audit Record

- Pass 1
  - Fixed document type as `parallel static survey master order`.
  - Kept scope at survey-only and excluded realization authority.
- Pass 2
  - Rebased the order on current workspace state:
    - queue empty
    - provider/router work active
    - fact-authority residuals active
    - earlier comment/doc wave already closed
- Pass 3
  - Strengthened the no-code-change rule.
  - Added 6 lane paths, launch prompt, and `넌 n번 터미널` dispatch lines.
  - Added explicit gimmick-elegance grading so the order does not collapse back into generic readability review.

## 16. Confidence

- Confidence: 98%
- Basis:
  - grounded in current canonical orientation, prior LLM-friendliness order, current multi-provider note, and current per-work fact surveys
  - 6 lanes cover entry, provider/router, Stage 4, writer/context, fact authority, and observability/peripheral surfaces without collapsing them into one vague lane
  - the document strongly separates static survey from any realization work, which matches the user constraint
