# Pre-Director Self-Audit Stagewise Survey Order

Date: 2026-03-25
Status: survey-order (execution deferred)
Document Type: system-track survey order
Canonical Path: `docs/2026-03-25/pre-director-self-audit-stagewise-survey-order.md`
Temp Mirror Path: none (survey-only)
Commit State:
- Baseline Commit: `f61a35c89b4c964afbfa902790560448d98b1bfb`
- Baseline Dirty Summary: `dirty: live-run console/log/db artifacts, closed Stage 3 wave edits, dated residual survey docs, temp queue state`

## 1. Intent

Survey the major writer-side LLM stages for explicit self-audit, self-critique, reasoning capture, and pre-Director gating before candidate submission.

This is a survey-only order.

This order exists to answer one bounded question:

- before Director compare / Director selection, where does each writer-side stage already self-audit, where does it only rely on Python prevalidation, and where is explicit self-audit missing or too weak?

After the survey returns, Codex will decide whether to open a bounded execution SSOT for prompt-level self-audit reinforcement.

## 2. Scope

Included stages:
- Stage 2 writer path
  - `modules/domain/agents/four_phase_arc_generator.py`
  - `modules/domain/agents/arc_ensemble.py`
  - `modules/domain/agents/arc_draft_validator.py`
  - `modules/core/stage2_validation_pipeline.py`
- Stage 3 writer path
  - `modules/domain/agents/blueprint_ensemble.py`
  - `modules/domain/agents/blueprint_constraint_compiler.py`
  - `modules/domain/agents/unified_blueprint_validator.py`
  - `modules/core/stage3_orchestrator.py`
- Stage 4 writer path
  - `modules/domain/agents/chief_writer.py`
  - `modules/domain/agents/chief_writer_quality.py`
  - `modules/domain/agents/chief_writer_prompts.py`
  - `modules/domain/agents/chief_writer_context.py`
  - `modules/domain/agents/chief_writer_context_packets.py`
  - `modules/core/pre_director_checklist.py`
  - `modules/core/stage4_interview_round.py`
  - `modules/validation/validation_orchestrator.py`

Included concepts:
- explicit self-audit / self-critique loops
- reasoning fields and rationale capture
- Python prevalidation before Director
- prompt-level instructions that require candidate self-checking
- operator-visible reasoning surfaces before Director submission
- persistence / sink surfaces for reasoning and quality-risk metadata

Excluded:
- post-Director retry redesign
- Stage 4 patch-mode redesign after Director reject
- Director policy redesign itself
- sink reconciliation overhaul
- DB schema redesign
- narrative-level work planning

## 3. Investigation Goal

For each major writer stage, determine:

1. whether the generation model is explicitly instructed to self-audit before finalizing candidate output
2. whether a separate self-critique or quality gate exists before Director compare
3. whether the stage relies mostly on Python-side prevalidation instead of writer-side self-audit
4. which reasoning artifacts are:
   - created
   - surfaced to operators
   - persisted
   - fed into later retry/fix loops
5. where the best bounded prompt-level self-audit insertion point would be if a later wave is justified

## 4. Stage Map

### Stage 2

Primary writer surfaces:
- `four_phase_arc_generator.py`
- `arc_ensemble.py`

Expected reasoning surfaces to inspect:
- `ep_count_reasoning`
- pacing / density reasoning
- candidate-generation prompt instructions
- Stage 2 Python validation before Director selection

### Stage 3

Primary writer surfaces:
- `blueprint_ensemble.py`
- `blueprint_constraint_compiler.py`

Expected self-audit / gating surfaces to inspect:
- constraint rendering into writer prompt
- any explicit instruction to self-check continuity / future leakage / fact-lock
- `unified_blueprint_validator.py` Python prevalidation
- `quality_risk`, `fix_scope_reasoning`, selection rationale exposure in `stage3_orchestrator.py`

### Stage 4

Primary writer surfaces:
- `chief_writer.py`
- `chief_writer_quality.py`
- `chief_writer_prompts.py`

Expected self-audit / gating surfaces to inspect:
- `ChiefWriterQualityGate.apply_self_critique()`
- `_self_critique()` checks and fix loop
- pre-Director checklist
- validation orchestrator output and advisory side-channel
- what is prompt-level vs Python-level vs posthoc repair

## 5. Required Questions

The survey must answer all of these.

1. Stage 2: does the writer LLM itself perform any real self-audit before Director submission, or is reasoning limited to heuristic `ep_count_reasoning` plus Python validation?
2. Stage 3: does the blueprint writer get an explicit "do not finalize until self-checked" contract, or does Stage 3 mostly rely on constraint injection plus Python prevalidation?
3. Stage 4: how strong is `ChiefWriter` self-critique in practice before Director submit, and which failure families are still left to Director / post-select catches?
4. For each stage, what reasoning fields exist and what is their actual lifecycle:
   - generated only
   - operator-visible
   - persisted
   - consumed by later retries
5. Which stages currently have no explicit prompt-level self-audit even though they have strong Python-side gating?
6. If a later prompt wave is justified, what is the minimal bounded insertion scope:
   - Stage 2 only
   - Stage 3 only
   - Stage 4 only
   - paired small wave
7. Is there already enough built-in self-audit that a new prompt wave would be low ROI?

## 6. Evidence Surfaces

Required code surfaces:
- `modules/domain/agents/four_phase_arc_generator.py`
- `modules/domain/agents/arc_ensemble.py`
- `modules/domain/agents/arc_draft_validator.py`
- `modules/core/stage2_validation_pipeline.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/core/stage3_orchestrator.py`
- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/chief_writer_quality.py`
- `modules/domain/agents/chief_writer_prompts.py`
- `modules/domain/agents/chief_writer_context.py`
- `modules/domain/agents/chief_writer_context_packets.py`
- `modules/core/pre_director_checklist.py`
- `modules/core/stage4_interview_round.py`
- `modules/validation/validation_orchestrator.py`

Optional evidence surfaces:
- recent live-run logs under `projects/0324_00_/logs/`
- `project_data.db` if reasoning persistence needs confirmation
- dated docs that already mention writer-context / validation contract clarity

## 7. Output Contract

Required outputs:
- `docs/2026-03-25/pre-director-self-audit-stagewise-survey-report.md`
- optional: `docs/2026-03-25/pre-director-self-audit-stagewise-evidence-ledger.md`

Required report sections:
1. Executive Summary
2. Included Coverage / Exclusions
3. Stage 2 Self-Audit / Reasoning State
4. Stage 3 Self-Audit / Reasoning State
5. Stage 4 Self-Audit / Reasoning State
6. Cross-Stage Reasoning Lifecycle Map
7. Missing Or Weak Self-Audit Surfaces
8. Cleared Non-Culprits
9. Best Bounded Next Wave
10. Confidence And Limits

Mandatory final lines:
- Stage with weakest pre-Director self-audit: `stage2 / stage3 / stage4 / mixed / none`
- Best next bounded prompt wave: `stage2 / stage3 / stage4 / paired small wave / no action`
- Should Codex open an execution SSOT immediately: `yes / no`

## 8. Guardrails

- Survey only. No code changes.
- Do not create an execution SSOT directly.
- Do not modify `docs/temp/`.
- Do not close or reopen existing queue items.
- Prefer live code over dated doc claims.
- Do not overclaim "self-audit exists" unless a concrete prompt loop or explicit critique loop is present.
- Distinguish:
  - prompt-level self-audit
  - Python prevalidation
  - Director catch
  - post-Director retry feedback
- If a stage only has Python checks and no model-side self-audit, say that plainly.
- If confidence stays below 95%, do not propose an execution SSOT as if it were settled.

## 9. Promotion Rule

If confidence reaches 95% or higher, the report may include an exact proposed execution scope for a later self-audit prompt wave.

It must still not create the execution SSOT itself.

Codex will decide promotion after reviewing the survey.

## 10. Opus Survey Order

```text
System-track survey-only order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/system-full-survey-execution-harness.md
4. docs/implementation/document-3pass-audit-harness.md
5. docs/2026-03-25/pre-director-self-audit-stagewise-survey-order.md
6. docs/2026-03-24/console.txt

Task:
Survey the major writer-side LLM stages for explicit self-audit, self-critique, reasoning capture, and pre-Director gating before candidate submission.

Primary goal:
Determine, stage by stage, whether the current system already has meaningful writer-side self-audit before Director submission, or whether it mostly relies on Python prevalidation and Director/post-select catches.

Hard constraints:
- Survey only. No code changes.
- Do not create execution SSOTs.
- Do not touch docs/temp or queue state.
- Do not broaden into Director redesign, retry redesign, sink reconciliation, or DB schema changes.
- Prefer live code over dated document claims.
- Distinguish prompt-level self-audit from Python-only validation.
- If a stage has no explicit prompt-level self-audit, say so directly.

Required investigation:
1. Stage 2 self-audit / reasoning state
2. Stage 3 self-audit / reasoning state
3. Stage 4 self-audit / reasoning state
4. Cross-stage reasoning field lifecycle:
   - generated
   - operator-visible
   - persisted
   - reused in retries
5. Weakest stage before Director submission
6. Best bounded prompt-level self-audit insertion point if a later wave is justified

Required code surfaces:
- modules/domain/agents/four_phase_arc_generator.py
- modules/domain/agents/arc_ensemble.py
- modules/domain/agents/arc_draft_validator.py
- modules/core/stage2_validation_pipeline.py
- modules/domain/agents/blueprint_ensemble.py
- modules/domain/agents/blueprint_constraint_compiler.py
- modules/domain/agents/unified_blueprint_validator.py
- modules/core/stage3_orchestrator.py
- modules/domain/agents/chief_writer.py
- modules/domain/agents/chief_writer_quality.py
- modules/domain/agents/chief_writer_prompts.py
- modules/domain/agents/chief_writer_context.py
- modules/domain/agents/chief_writer_context_packets.py
- modules/core/pre_director_checklist.py
- modules/core/stage4_interview_round.py
- modules/validation/validation_orchestrator.py

Required outputs:
- docs/2026-03-25/pre-director-self-audit-stagewise-survey-report.md
- optional: docs/2026-03-25/pre-director-self-audit-stagewise-evidence-ledger.md

Mandatory final lines:
- Stage with weakest pre-Director self-audit: stage2 / stage3 / stage4 / mixed / none
- Best next bounded prompt wave: stage2 / stage3 / stage4 / paired small wave / no action
- Should Codex open an execution SSOT immediately: yes / no
```

## 11. Short Dispatch

```text
docs/2026-03-25/pre-director-self-audit-stagewise-survey-order.md 읽고 survey-only로 진행. Stage2/3/4 writer LLM의 pre-director self-audit / reasoning 상태만 조사하고, SSOT/코드수정/temp queue는 건드리지 마.
```
