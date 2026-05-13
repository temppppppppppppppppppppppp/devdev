# S4 Writer-Facing Interface Observation Log

Date: 2026-05-13
Status: observation-only
Callsign: SCOUT-1
Scope: S4 writer-facing interface read-only diagnosis

## Non-Goals

- No patch.
- No design decision.
- No issue creation.
- No experiment-path attribution.
- No source/work excerpt reproduction.

## Observation

S4 Chief Writer currently appears to receive a high-volume mixed context packet rather than a clean prose-only writer brief.

The writer-facing path includes prose instructions, but also exposes operationally shaped material such as strict JSON output schema, state update schema, scene breakdown JSON, template/checklist language, hard-canon packets, continuity/world-state/fact-ledger packets, previous manuscript packets, style/reference excerpt, advisory wording, and Director/validation-oriented language.

This is an over-input and terminology-leakage risk, not a confirmed runtime failure in this note.

## Evidence Anchors

- `main_a.py` routes S4 into `Stage4Orchestrator`.
- `modules/core/stage4_orchestrator.py` prepares the S4 session and episode loop.
- `modules/core/stage4_context_builder.py` assembles mandatory context, retrieval context, WorkGuard/work-identity packets, continuity packets, world-state/fact-ledger summaries, and previous-manuscript material.
- `modules/core/stage4_context_packets.py` and `modules/domain/agents/chief_writer_context_packets.py` package previous ending, digest, full prior text tiers, future/past guards, HUD/equipment/frequency, and carryover ceilings.
- `modules/domain/agents/chief_writer_context.py` builds the common Chief Writer prompt context and passes mandatory context, scene breakdown, integrated scenario advisory, soft guidance, and style/reference surfaces into the writer prompt.
- `modules/domain/agents/chief_writer_prompts.py` and `config/prompts/chief_writer.yaml` define the writer-facing prompt template, rules, strict JSON output contract, and anti-meta guardrails.
- `material_ssot/20_pitch/work-guard-translation-map.md` shows that a compact material-side runtime doctrine layer is intended, but current S4 viability is not hard-gated on that layer.

## Diagnostic Note

There is a partial "before compression -> during writing -> after audit" structure:

- Before writing: context is budgeted, tiered, and partly compressed through summaries, retrieval selection, WorkGuard packets, and reference clamping.
- During writing: Chief Writer is asked to produce prose inside hard canon and scene obligations, but still sees schema/checklist/validation-facing language.
- After writing: Python validation is advisory and Director remains final authority.

The weak point is the pre-writing layer. It behaves more like accumulated context packing than a dedicated author-facing compression layer.

## Risk

- Schema/checklist language may compete with prose generation.
- Internal terms may leak into manuscript surface despite anti-meta guardrails.
- Raw planning structures may bias the writer toward report-like execution.
- Large previous-text/reference surfaces may dilute attention or increase imitation risk.
- Works without a strong WorkGuard packet may receive less compact identity guidance.

## Recommended Next Read-Only Action

Trace the final S4 prompt render path without calling the LLM, then mark each visible block as one of:

- writer-facing prose brief
- hard canon needed by writer
- Director/validator-only evidence
- schema/output machinery
- internal planning language that may need compression later

Suggested next files:

- `modules/core/writer_template.py`
- `modules/core/writer_prompt_builders.py`
- `modules/core/prompt_builder.py`
- `modules/domain/agents/writer.py`
- `config/prompts/director.yaml`
- `config/prompts/writing_directive.yaml`
- `config/settings/validation.yaml`

## Needs CMD-0 Decision

Yes. Any fix would require a CMD-0 policy choice before design or patching:

- whether S4 needs a dedicated clean writer brief layer
- whether schema and validation language should be separated from prose-generation context
- whether WorkGuard should become a stronger S4 writer-interface precondition
- whether previous full text and reference excerpt injection should be capped or transformed further

## 3-Pass Save Check

- Pass 1, structure/scope: bounded to an observation log, not an execution plan.
- Pass 2, evidence/consistency: claims are tied to files inspected during SCOUT-1 and do not assert a confirmed runtime failure.
- Pass 3, readability/operating consequence: next action is read-only and requires CMD-0 before any design or patch.
- Estimated confidence for this bounded observation: 95%.
