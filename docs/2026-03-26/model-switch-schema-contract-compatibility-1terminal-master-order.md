# Model-Switch Schema Contract Compatibility 1-Terminal Master Order

Date: 2026-03-26
Status: survey-master-order
Document Type: system-track survey master order
Canonical Path: `docs/2026-03-26/model-switch-schema-contract-compatibility-1terminal-master-order.md`
Temp Mirror Path: none (survey-only)
Commit State:
- Baseline Commit: `e3f2771699cb5d596aefaf994a8a177bbbad0a3e`
- Baseline Dirty Summary: `dirty: Stage 4 Wave 1/2 code and tests, observability files, dated docs, no active temp execution queue`

## 1. Intent

Run one compact survey on one bounded topic:

- model-switch schema and output-contract compatibility

This is not a provider benchmark order.
This is not a model recommendation order.
This is not an execution SSOT bundle yet.

The purpose is only:
- identify where the current codebase is implicitly tuned to current model output habits
- identify where switching major writing models could break schema, parser, or retry behavior
- separate true contract surfaces from provider-specific quirks
- decide whether a bounded compatibility wave should open later

## 2. Core Question

If the writing stack later shifts from the current Gemini-centered runtime to Claude/Opus/Codex-class models, where would schema or output-contract friction most likely appear first?

This survey must answer:

1. which parsers, validators, and bridges assume current model output shape
2. which prompts or retry paths rely on current model wording/format habits
3. which surfaces are robust across model families already
4. whether one bounded compatibility hardening wave is justified later

## 3. Scope

Included:
- response parsing and schema enforcement surfaces
- prompt slots that expect strict JSON or structured blocks
- retry / validation paths that may assume current model behavior
- canary / summary / session logging surfaces only where they expose output-shape assumptions
- bridge / provider adaptation surfaces already present in the repo

Excluded:
- external model benchmarking
- price/performance comparison
- provider migration policy
- new execution SSOT creation
- code changes
- temp queue edits
- broad quality debates about which model is "better"

## 4. Common Rules

- Survey only. No code changes.
- Do not create execution SSOTs.
- Do not modify `docs/temp/`.
- Findings first.
- Prefer live code and parser truth over speculation.
- Distinguish:
  - current robust contract surfaces
  - likely brittle Gemini-shaped assumptions
  - bounded future compatibility hardening candidates
- If confidence is below 95%, do not recommend immediate execution SSOT opening.

## 5. Required Evidence Surfaces

Required code surfaces:
- `modules/api/bridge_server.py`
- `modules/core/session_logger.py`
- `modules/core/metrics_collector.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/domain/agents/base_agent.py`
- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/core/response_parser.py` if present
- any provider adapter / usage-metadata / JSON parse helpers discovered during the survey

Optional evidence surfaces:
- recent `projects/*/logs/session/llm_io.jsonl`
- recent canary summaries
- recent `episode_production.jsonl` entries that expose parse/retry behavior

## 6. Single Lane Assignment

### T1. Model-Switch Schema / Output-Contract Compatibility

Purpose:
- determine where model-family switching would most likely break output contracts first

Focus:
- strict JSON assumptions
- enum / missing-field tolerance
- retry loops caused by parse or structure drift
- places where current logic depends on current model-specific phrasing or metadata shape

Questions:
- Which surfaces are already provider-agnostic?
- Which surfaces appear tuned to current Gemini-style output or metadata?
- Where would Claude/Opus/Codex-class outputs most likely break parsing or validation first?
- What is the best bounded compatibility hardening candidate:
  - parser tolerance hardening
  - provider adapter normalization
  - schema/enum normalization
  - or no wave yet

Save paths:
- `docs/2026-03-26/model-switch-schema-contract-compatibility-survey.md`
- optional: `docs/2026-03-26/model-switch-schema-contract-compatibility-evidence.md`

## 7. Required Output Shape

The lane must:
- list findings first
- include file/line anchors
- separate:
  - robust contract surfaces
  - brittle model-shaped assumptions
  - bounded future hardening candidates
- avoid external provider claims not grounded in local code

Mandatory final lines:
- `Dominant compatibility seam: parser / schema / provider-adapter / retry-shape / mixed / none`
- `Best bounded compatibility candidate: <short label>`
- `Should Codex open an execution SSOT now: yes / no`

## 8. Merge Rule

There is no parallel merge step for this order.

After the single lane returns, Codex will decide:
- whether the result is only a backlog note
- whether one bounded compatibility-hardening execution SSOT should open later
- or whether fresh evidence is still needed before any wave

## 9. Common Survey Prompt

```text
System-track survey-only order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/document-3pass-audit-harness.md
4. docs/2026-03-26/model-switch-schema-contract-compatibility-1terminal-master-order.md

Task:
Run one compact survey for model-switch schema/output-contract compatibility only.
Survey only. No code changes.

Primary goal:
Identify where the current codebase is implicitly shaped to current model output behavior, and determine the best bounded future compatibility hardening move.

Hard constraints:
- Survey only. Do not patch code.
- Do not create execution SSOTs.
- Do not edit docs/temp or queue-state.
- Keep scope to schema/output-contract compatibility only.
- Do not turn this into provider benchmarking or model hype.
- Prefer live code and parser truth over assumptions.
- If confidence is below 95%, do not recommend immediate execution SSOT opening.

Required evidence surfaces:
- modules/api/bridge_server.py
- modules/core/session_logger.py
- modules/core/metrics_collector.py
- modules/core/stage4_interview_round.py
- modules/core/stage4_retry_runtime.py
- modules/domain/agents/base_agent.py
- modules/domain/agents/chief_writer.py
- modules/domain/agents/blueprint_ensemble.py
- modules/domain/agents/unified_blueprint_validator.py
- response/parser/provider helper surfaces discovered during the audit

Required investigation questions:
1. Which parser or schema surfaces are already model-agnostic?
2. Which surfaces appear tuned to current Gemini-style output or metadata?
3. Where would model-family switching most likely break first:
   - parser tolerance
   - schema/enum handling
   - provider metadata normalization
   - retry/validation assumptions
4. What single bounded future hardening move has the best ROI?
5. What should explicitly stay untouched for now?

Required output:
- one report saved to docs/2026-03-26/model-switch-schema-contract-compatibility-survey.md
- findings first
- file/line anchors
- one recommendation only

Mandatory final lines:
- Dominant compatibility seam: parser / schema / provider-adapter / retry-shape / mixed / none
- Best bounded compatibility candidate: <short label>
- Should Codex open an execution SSOT now: yes / no
```

## 10. Dispatch Line

Use:

- `docs/2026-03-26/model-switch-schema-contract-compatibility-1terminal-master-order.md + terminal 1`

## 11. 3-Pass Audit Notes

- Pass 1: document type and scope are correct for a survey-only master order
- Pass 2: paths, save locations, and excluded surfaces are coherent with the current workspace
- Pass 3: output shape is actionable and bounded; no execution or queue side effects are implied
- Confidence: 96%
