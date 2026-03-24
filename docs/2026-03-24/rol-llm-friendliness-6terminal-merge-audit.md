Date: 2026-03-24
Status: final (3-pass audited)
Document Type: 6-terminal LLM-friendliness merge-audit report
Canonical Path: `docs/2026-03-24/rol-llm-friendliness-6terminal-merge-audit.md`
Temp Mirror Path: none
Source Order: `docs/2026-03-24/rol-llm-friendliness-6terminal-master-order.md`
Source Survey Docs:
- `docs/2026-03-24/opus/rol-llm-friendly-t1-navigation-entry.md`
- `docs/2026-03-24/opus/rol-llm-friendly-t2-stage4-authority-verdict.md`
- `docs/2026-03-24/opus/rol-llm-friendly-t3-writer-context-prompt.md`
- `docs/2026-03-24/opus/rol-llm-friendly-t4-contract-validation-envelope.md`
- `docs/2026-03-24/opus/rol-llm-friendly-t5-persistence-observability.md`
- `docs/2026-03-24/opus/rol-llm-friendly-t6-peripheral-regression-noaction.md`
Evidence Artifacts:
- `docs/2026-03-24/opus/rol-llm-friendly-t1-navigation-entry-evidence.md`
- `docs/2026-03-24/opus/rol-llm-friendly-t2-stage4-authority-verdict-evidence.md`
- `docs/2026-03-24/opus/rol-llm-friendly-t3-writer-context-prompt-evidence.md`
- `docs/2026-03-24/opus/rol-llm-friendly-t4-contract-validation-envelope-evidence.md`
- `docs/2026-03-24/opus/rol-llm-friendly-t5-persistence-observability-evidence.md`
- `docs/2026-03-24/opus/rol-llm-friendly-t6-peripheral-regression-noaction-evidence.md`
- inline live recheck against `docs/2026-03-23/llm-codebase-orientation-pack.md`, `modules/domain/agents/director_ensemble.py`, `docs/implementation/prompt_broker.py`, `docs/implementation/input_route.py`, `scripts/tf_c1_patch.py`, `docs/temp/queue-state.json`
Commit State:
- Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Baseline Dirty Summary: `dirty: tracked stage4/state/writer/validator surfaces, docs/temp/queue-state.json, docs/2026-03-23/console.txt; many project artifacts deleted; new docs/2026-03-24/ survey outputs`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

---

# ROL LLM Friendliness 6-Terminal Merge Audit

## 1. Executive Summary

All 6 lane reports arrived in `final` state and remain usable after live recheck. The merged judgment is narrower than "repo-wide refactor needed":

- the workspace is broadly LLM-navigable enough for a bounded clarity wave
- the only merged `P0` is the verdict-field precedence ambiguity at `modules/domain/agents/director_ensemble.py:1346-1388`
- the dominant follow-up shape is still `comment/doc/observability/contract-cleanup`, not boundary refactor
- one lane note is already stale:
  - T6 still mentions `docs/temp/queue-state.json` with `1` active item
  - live queue is now `empty` after the 2026-03-24 closure work

Merge outcome:

- `cheap-fix-first`: **yes**
- `boundary-refactor can wait`: **yes**
- `fresh live rerun before clarity fixes`: **no**
- `execution SSOT promotion`: **yes, one compact single-item wave**

Promoted follow-up:
- `docs/2026-03-24/llm-friendliness-clarity-wave-execution-ssot.md`

## 2. Lane Status Matrix

| Lane | Status | Confidence | Merge Verdict |
| --- | --- | --- | --- |
| T1 Navigation / Entry | final | 96% | valid; entry-map and `main_a.py` navigation gaps remain open |
| T2 Stage 4 Authority / Verdict | final | 95% | valid; contains the only merged `P0` |
| T3 Writer / Prompt / Context | final | 95% | valid; quick-fix-first comment/doc wave is sufficient |
| T4 Contract / Validation / Envelope | final | 95% | valid; contract docs lag live payload reality |
| T5 Persistence / Observability | final | 96% | valid; mostly doc/comment/observability-only |
| T6 Peripheral / Regression / No-Action | final | 96% | valid with one stale queue-state note; stale-authority cleanup cluster remains open |

## 3. Stale, Settled, and Deferred Classification

### 3.1 Stale Now

1. T6 `docs/temp/queue-state.json` note
- report text says the temp queue carries `1` pending item
- live queue now shows:
  - `queue_mode: empty`
  - `active_item_count: 0`
- merge handling:
  - keep the stale note out of any promoted execution scope

### 3.2 Already Settled, Do Not Reopen

These were correctly marked as settled in the lane reports and should not spawn duplicate work:

- `main_a.py` Stage 2 `[COMPAT]` delegate markers
- `main_a.py` shutdown phase comments
- `stage4_orchestrator.py` dataclass-family grouping
- `modules/domain/agents/base_agent.py` lock and shared-state grouping comments
- `modules/core/stage4_director_runtime.py` missing-module debug note
- `stage01_helpers.py` menu remap clarifier
- prior 2026-03-24 closures:
  - immutable-fact convergence SSOT
  - genre-contamination guardrail SSOT

### 3.3 Real but Explicitly Deferred

These remain real costs, but they are not the story of this wave:

- `main_a.py` / `SovereignApp` owner-surface reduction
- `bridge_server.py` route-module split
- `chief_writer.py` `WriterEnsembleRequest` dataclass extraction
- `chief_writer_context.py` context-config object extraction
- `four_phase_arc_runtime.py` envelope consolidation
- `db_manager.py` shared-cursor to local-cursor migration
- `base_agent.py` `_extract_json_robust()` split
- `geuldobi-desktop/src/index.html` component split

Merge rule:
- keep these as `long-term` or `defer`
- do not let them block the compact clarity wave

## 4. Cross-Lane Priority Clusters

| Rank | Cluster | Severity | Primary Anchors | Fix Shape | Merge Judgment |
| --- | --- | --- | --- | --- | --- |
| 1 | Verdict and validation contract visibility | `P0/P1` | `director_ensemble.py:1346-1388`, `validation_orchestrator.py:329-354`, `validation_orchestrator.py:777-822`, `validation_orchestrator.py:456`, `stage4_interview_round.py:2767-2794`, `four_phase_arc_runtime.py:19-135` | comment-only + doc-only | highest ROI; no logic rewrite required |
| 2 | Entry, authority, and writer-context navigation | `P1` | orientation-pack `modules/api/` omission, `main_a.py:346-925`, `main_a.py:3780-3852`, `stage4_context_builder.py:1-2729`, `chief_writer.py:2148-2270`, `chief_writer_context_packets.py:30-40` | comment-only + doc-only | strong LLM search-cost reduction without refactor |
| 3 | Peripheral stale-authority cleanup | `P1` | `docs/implementation/prompt_broker.py`, `docs/implementation/input_route.py`, `scripts/` no README, `tests/` no README, `UI/` no README, `scripts/tf_c1_patch.py`, `geuldobi-desktop/temp-electron-*.js` | doc-only + contract-cleanup | safe if pre-delete reference check passes |
| 4 | Persistence and operator-truth clarity | `P1/P2` | `db_manager.py:2804-3178`, `episode_production.jsonl` write owners, `session_logger.py:49`, `pass_rate_monitor.py:252-256` | comment-only + doc-only + observability-only | worthwhile, but lower urgency than cluster 1 |

## 5. Top Merged Quick Wins

1. `director_ensemble.py:1346`
- add an inline contract comment defining `final_verdict`, `director_verdict`, `original_verdict`, `verdict`, and `gate_basis`
- why first:
  - only merged `P0`
  - affects T2 and T4 simultaneously

2. `validation_orchestrator.py:329` and nearby advisory-key sites
- expand `validate()` docstring to the actual return envelope
- document underscore advisory side-channel keys at class level

3. `docs/2026-03-23/llm-codebase-orientation-pack.md`
- add `modules/api/` to the reading order
- add the writer-context two-pipeline note

4. `main_a.py:346` and `main_a.py:3780`
- add a `SovereignApp` class ToC
- restate `_stage_4_v2_chief_writer()` as a lazy-init gateway, not a thin delegate

5. `stage4_context_builder.py` and `chief_writer_context_packets.py`
- add section dividers / ToC
- document the delegation chain and expected parameter shapes

6. `scripts/README.md`, `tests/README.md`, `UI/README.md`
- give cold-entry classification for three high-noise directories

7. stale-authority file cleanup
- delete or archive `docs/implementation/prompt_broker.py`
- delete or archive `docs/implementation/input_route.py`
- delete or archive `scripts/tf_c1_patch.py`
- delete `geuldobi-desktop/temp-electron-loadcheck.js`
- delete `geuldobi-desktop/temp-electron-paths.js`
- guardrail:
  - re-run live reference checks before deletion

8. persistence observability notes
- add telemetry sink section dividers in `db_manager.py`
- note `pass_rate_monitor.json` as non-authoritative cache
- add one bounded startup-state log in `session_logger.py`

## 6. Execution SSOT Promotion Judgment

Promotion decision: **yes**

Why:

- there is one live `P0`, but its fix shape is comment/doc, not runtime logic surgery
- the next 3 clusters are low-blast and can ship together without a roadmap
- no active temp execution item already absorbs this clarity work
- deferring execution-doc promotion would leave a large amount of high-confidence low-cost work unqueued

Promoted artifact:

- canonical:
  - `docs/2026-03-24/llm-friendliness-clarity-wave-execution-ssot.md`
- temp mirror:
  - `docs/temp/llm-friendliness-clarity-wave-execution-ssot.md`

Queue judgment:

- single-item temp queue is sufficient
- no aggregate roadmap required

## 7. Confidence And Limits

Estimated confidence: **96%**

Basis:

- all 6 lane reports were inspected
- the only clear stale claim was rechecked and removed from promotion logic
- the merged `P0/P1` items were re-anchored against live files
- previous settled items from the 2026-03-23 follow-up wave were separated from still-open findings

Limits:

- not every `P2` item was rechecked line by line
- no code realization or pytest rerun happened in this merge turn
- stale-file deletions remain conditional on a fresh reference sweep at execution time

## 8. 3-Pass Audit Record

### Pass 1. Scope and Structure

- confirmed this document is a merge-audit, not an execution SSOT
- fixed the output shape to stale-filtering, cluster ranking, and promotion judgment

### Pass 2. Evidence and Consistency

- reconciled the 6 lane reports against current live code and queue state
- removed the stale temp-queue note from action-bearing promotion logic
- separated prior settled items from newly promoted items

### Pass 3. Actionability

- ranked the work into 4 compact clusters
- rejected broad refactor escalation
- promoted exactly one compact execution SSOT instead of a multi-item queue
