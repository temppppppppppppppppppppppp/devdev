# stage4-chiefwriter-state-injection-wave1 Execution SSOT

Date: 2026-03-25
Status: closed (closure-audited)
Canonical Path: `docs/2026-03-25/stage4-chiefwriter-state-injection-wave1-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage4-chiefwriter-state-injection-wave1-execution-ssot.md`
Commit State:
- Baseline Commit: `e3f2771699cb5d596aefaf994a8a177bbbad0a3e`
- Baseline Dirty Summary: `dirty: observability telemetry wave files, dated docs, queue-state`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-25/stage4-chiefwriter-state-injection-path-audit.md`
Evidence Artifacts:
- `docs/2026-03-25/console.txt`
- `projects/00_0000001/logs/episode_production.jsonl`
- `projects/00_0000001/logs/artifacts/stage4/ep_0004/`
- `projects/00_0000001/logs/artifacts/stage4/ep_0005/`
Side-Effect Coverage: covered

## 1. Intent
- Restore the high-authority Stage 4 ChiefWriter state-contract injection path for committed state and completed events.
- Fix the confirmed severed fact-ledger path before opening any broader Stage 4 redesign wave.
- Keep the wave bounded to data injection and extraction vocabulary only; do not reopen Director, post-select, retry policy, or Stage 3.

## 2. Baseline Facts
- `modules/domain/agents/chief_writer_context.py` passes `world_state_summary` into `fact_ledger_summary` at the IFC build site, severing the intended fact-ledger path.
- `world_state_summary` is not a reliable substitute for fact-ledger numeric truth in this project; the audit found empty protagonist asset fields there.
- `modules/core/stage4_immutable_fact_contract.py` committed-state extraction is biased toward Korean numeric vocabulary and misses English-style ledger lines such as `capital: 2000000000.0 won`.
- Completed-event extraction vocabulary is skewed toward wuxia/action verbs and under-covers investment-fiction completion verbs such as `개설`, `구축`, `이체`, `계약`.
- Time/place continuity already enters Stage 4 via opening anchor and chain-link surfaces. That path is not the primary failure in this wave.
- Stage 4 already receives lower-authority fact-ledger context through mandatory context assembly in `modules/core/stage4_context_builder.py`; this wave targets the missing high-authority IFC packet, not the flat context lane.

## 3. Scope
Included:
- `modules/domain/agents/chief_writer_context.py`
- `modules/core/stage4_immutable_fact_contract.py`
- `tests/test_chief_writer_context.py`
- `tests/test_stage4_immutable_fact_contract.py`

Excluded:
- `modules/core/stage4_context_builder.py`
- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/chief_writer_prompts.py`
- `modules/domain/agents/director_prompts.py`
- `modules/core/stage4_retry_runtime.py`
- Stage 3 blueprint contracts and prompts
- `world_state` population redesign
- post-select hang root-cause work
- retry / ASP / timeout policy changes
- DB schema, JSONL path/naming, dashboard/UI

## 4. Pass 1. Inventory Summary
- Primary defect count: 1 direct wiring defect (`fact_ledger_summary=world_state_summary`)
- Secondary extraction defects: 2
  - committed-state numeric keyword language gap
  - completed-event genre vocabulary gap
- Existing lower-authority fallback lane: present in Stage 4 context builder mandatory context
- Evidence quality: high
  - live console pathology
  - authoritative `episode_production.jsonl`
  - targeted static code inspection

## 5. Pass 2. Semantic Classification
- Class A. Wiring defect
  - IFC builder receives the wrong substrate for `fact_ledger_summary`.
- Class B. Extraction-contract defect
  - committed-state extraction does not recognize English-formatted financial ledger text.
- Class C. Genre-vocabulary defect
  - completed-event extraction under-recognizes investment-fiction completion verbs.
- Deferred, not in this wave
  - LLM compliance with already-injected time/place anchors
  - post-select hang classification beyond content-coupled evidence
  - world-state field completeness redesign

## 6. Side-Effect Map
- file writes / artifacts:
  - none expected beyond tests
- DB / schema / transaction boundaries:
  - not applicable
- JSONL / log / audit sinks:
  - no new sinks or path changes
- console / UI / operator output:
  - non-applicable aside from possible existing debug/log wording
- rollback / recovery / retry:
  - no retry policy change
- cache / global state:
  - none intended
- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture
- Keep the repair inside the existing IFC path.
- `ChiefWriterContextBuilder._build_immutable_fact_section()` must supply actual fact-ledger summary text to `build_packet()`.
- `build_packet()` / extraction helpers in `stage4_immutable_fact_contract.py` must recognize both:
  - Korean-form numeric/resource expressions
  - English-form ledger labels for investment-fiction runs
- Completed-event extraction must gain a bounded investment-fiction verb set without removing existing wuxia/action coverage.
- Preserve backward compatibility:
  - empty or missing fact ledger still yields no committed-state facts
  - no schema change
  - no new prompt slots outside the existing IFC packet

## 8. Execution Tranches
1. Tranche A: IFC wiring repair
   - replace the `fact_ledger_summary=world_state_summary` substitution with actual fact-ledger summary sourcing inside `chief_writer_context.py`
   - keep `world_state_summary` unchanged for its own lane
2. Tranche B: committed-state bilingual extraction
   - extend committed-state extraction patterns/keywords to recognize English-form financial labels relevant to investment-fiction ledgers
3. Tranche C: completed-event vocabulary broadening
   - extend completion extraction with bounded investment-fiction verbs
   - verify existing non-investment coverage does not regress
4. Tranche D: targeted regression tests
   - prove the IFC packet now surfaces committed-state facts for ledger-backed investment data
   - prove completed-event extraction catches investment completion verbs

## 9. Acceptance Criteria
- The Stage 4 IFC path no longer substitutes `world_state_summary` for `fact_ledger_summary`.
- A ledger summary containing `capital ... won` yields non-empty committed-state facts.
- An investment-fiction completion digest containing terms such as `개설`, `구축`, `이체`, or `계약` yields completed-event facts.
- Existing Stage 4 immutable fact contract tests continue to pass.
- No Stage 4 policy, Director, Stage 3, or schema surface is changed.

## 10. Verification Plan
- `python -m py_compile modules/domain/agents/chief_writer_context.py modules/core/stage4_immutable_fact_contract.py`
- `set PYTHONIOENCODING=utf-8 && pytest tests/test_chief_writer_context.py -q`
- `set PYTHONIOENCODING=utf-8 && pytest tests/test_stage4_immutable_fact_contract.py -q`
- run any additional new targeted test file only if created
- `python scripts/check_utf8_hygiene.py modules/domain/agents/chief_writer_context.py modules/core/stage4_immutable_fact_contract.py tests/test_chief_writer_context.py tests/test_stage4_immutable_fact_contract.py docs/2026-03-25/stage4-chiefwriter-state-injection-wave1-execution-ssot.md docs/temp/stage4-chiefwriter-state-injection-wave1-execution-ssot.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 11. Guardrails
- Do not reopen Stage 4 broad architecture.
- Do not change `world_state` population logic in this wave.
- Do not modify post-select conflict policy, retry budgets, ASP behavior, or hang handling.
- Do not touch Director scoring or downgrade logic.
- Do not broaden this into generic ownership theory or Stage 3 contract work.
- If live code already diverges before implementation starts, shrink scope rather than expanding it.

## 12. Temp Queue Notes
- temp status: pending
- cleanup condition:
  - remove the temp mirror only after implementation is realized, closure-audited, and queue state returns to empty
- roadmap dependency:
  - none; single-item queue expected

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Notes
- Pass 1: scope narrowed to IFC state-contract repair only; broad Stage 4 redesign excluded
- Pass 2: evidence matches live code
  - wiring defect confirmed at `chief_writer_context.py`
  - existing lower-authority fact-ledger lane in `stage4_context_builder.py` explicitly acknowledged and excluded from change scope
- Pass 3: realization is actionable and bounded
  - two production files
  - two targeted test files
  - no policy or schema blast-radius
- Confidence: 97%

## 15. Closure Audit
- Closure result: accepted with no blocking findings.
- Realized scope matched the active SSOT:
  - `modules/domain/agents/chief_writer_context.py`
  - `modules/core/stage4_immutable_fact_contract.py`
  - `tests/test_chief_writer_context.py`
  - `tests/test_stage4_immutable_fact_contract.py`
- Confirmed realized tranches:
  - Tranche A: IFC wiring now derives real fact-ledger summary text instead of substituting `world_state_summary`
  - Tranche B: committed-state extraction recognizes bounded English-form financial ledger labels
  - Tranche C: completed-event extraction recognizes bounded investment-fiction completion verbs
  - Tranche D: targeted regression tests cover the repaired path and non-regression expectations
- Re-run verification during closure audit:
  - `python -m py_compile modules/domain/agents/chief_writer_context.py modules/core/stage4_immutable_fact_contract.py`
  - `pytest tests/test_chief_writer_context.py -q` -> `50 passed`
  - `pytest tests/test_stage4_immutable_fact_contract.py -q` -> `49 passed`
  - `python scripts/check_utf8_hygiene.py ...` -> pass
  - `python scripts/ops_validator.py` -> `0 errors, 0 warnings`
- Residual risk:
  - This wave restores high-authority injected facts, but it does not by itself prove perfect Stage 4 compliance under fresh live retry loops. A subsequent Stage 4 canary remains the live proof step.
