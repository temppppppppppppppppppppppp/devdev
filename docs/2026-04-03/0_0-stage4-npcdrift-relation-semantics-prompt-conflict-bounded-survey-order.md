# 0_0 Stage4 NPC Relation-Semantics And Prompt-Conflict Bounded Survey Order

Date: 2026-04-03
Status: final (3-pass audited)
Confidence: 96%
Document Type: survey order
Canonical Path: `docs/2026-04-03/0_0-stage4-npcdrift-relation-semantics-prompt-conflict-bounded-survey-order.md`
Temp Mirror Path: `(none - operator order only; no docs/temp mirror)`
Baseline Commit: `ecd58d57943a91ad5b946077eeacba224f49641a`
Baseline Dirty Summary: `dirty: active Stage0/Stage4 code deltas, large unrelated narrative-doc deletions, untracked canary/runtime artifacts present`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `fresh Stage4-only canary evidence added under projects/canary_0_0_stage4_ep2_sinkproof_r1/`
Track: system
Mode: bounded post-run read-only survey, no realization, no new canary
Source Harnesses:
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/implementation/execution-synthesis-harness.md`
Related Context:
- `docs/2026-04-02/0_0-stage4-npcdrift-relation-tag-local-fix-bounded-survey.md`
- `docs/2026-04-02/0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`
- `projects/00_20260403/`
- `projects/canary_0_0_stage4_ep2_sinkproof_r1/`

## 1. Purpose

This is a bounded read-only survey order for one concrete question:

- did the latest `ep2` Stage4-only failure reveal a real `Stage4 NPC relation semantics + gate escalation + prompt authority conflict` seam, and if so, what is the smallest correct owner boundary for the next implementation wave?

This order exists because the latest canary changed the picture:

- `genre misbinding` is no longer the leading hypothesis
- `replay/opening continuity` is no longer the dominant observed failure family in this run
- the evidence now clusters around:
  - `relation_to_protag = 오해 대상`
  - Director open-review vs final gate escalation mismatch
  - prompt-authority collisions such as `대화 비율: 0%`
  - numeric authority collisions such as `FactLedger 1천만원 vs manuscript 200억`

## 2. Working Answer-First Hypothesis

Use the following as a working hypothesis to test, not as a foregone conclusion:

1. `investment` genre binding is correct and should be treated as currently ruled out unless contradictory evidence appears.
2. The primary seam is not generic Director overreaction but a contract-semantics problem:
   - `relation_to_protag: 오해 대상` is directionally or semantically underspecified for this regressor/investment setup
   - the Stage4 advisory/gate chain appears to treat that ambiguity too harshly
3. A secondary seam exists in prompt authority:
   - the writer prompt contains a `대화 비율: 0%` style-DNA instruction while other runtime layers push for higher dialogue density
   - additional authority collisions may be amplifying retry churn even when they are not the primary blocker

The survey must prove, narrow, or falsify those three statements.

## 3. Scope

Minimum runtime evidence scope:

- source run:
  - `projects/00_20260403/stage0_output/style_guide.json`
  - `projects/00_20260403/logs/session/ui_events.jsonl`
  - `projects/00_20260403/drafts/ep_0002.txt`
- fresh canary:
  - `projects/canary_0_0_stage4_ep2_sinkproof_r1/logs/episode_production.jsonl`
  - `projects/canary_0_0_stage4_ep2_sinkproof_r1/logs/session/llm_io.jsonl`
  - `projects/canary_0_0_stage4_ep2_sinkproof_r1/logs/session/ui_events.jsonl`
  - `projects/canary_0_0_stage4_ep2_sinkproof_r1/project_data.db`
  - `projects/canary_0_0_stage4_ep2_sinkproof_r1/logs/artifacts/stage4/ep_0002/`

Minimum code surfaces:

- `modules/core/npc_drift_advisor.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/world_state.py`
- `modules/core/stage4_context_builder.py`
- `modules/domain/agents/chief_writer_context.py`
- any direct prompt/style-DNA injection surface discovered while tracing `대화 비율: 0%`

Minimum document context:

- `docs/2026-04-02/0_0-stage4-npcdrift-relation-tag-local-fix-bounded-survey.md`
- `docs/2026-04-02/0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation-execution-ssot.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`

## 4. Explicit Non-Goals

1. Do not reopen broad Stage2 or Stage3 realization.
2. Do not widen this into a whole-genre or whole-Director redesign.
3. Do not run a new canary.
4. Do not edit code, DB, `docs/temp`, or execution SSOTs.
5. Do not treat every observed warning as a new active owner lane.
6. Do not collapse this into “LLM nondeterminism” without tracing the concrete contract and prompt path first.

## 5. Required Questions

The survey must answer all of these.

1. Is `investment` genre binding actually correct at source, prompt, and runtime surface?
2. In this run, why did Director free review treat the `NpcDrift` finding as genre-compatible while the final chain still produced `strong_advisory_escalation_non_local_fix` and REJECT?
3. Is the core problem merely `compressed relation tag -> no semantic bridge`, or is the canonical label `오해 대상` itself directionally wrong or too ambiguous for this work?
4. Does `relation_to_protag` currently encode:
   - protagonist misunderstanding the NPC
   - NPC misunderstanding the protagonist
   - either direction
   - or an underspecified mixed tag that different layers interpret differently?
5. Should this subtype stay `strong advisory`, become thresholded, or become advisory-only unless a clear contradiction exists?
6. Where does `대화 비율: 0%` enter the ChiefWriter prompt, and is it authoritative, advisory, stale, or mis-prioritized relative to dialogue-density checks?
7. Are the `1천만원 vs 200억` and timeline findings independent primary blockers, or are they secondary contamination introduced after the initial relation-semantics failure path?
8. Can the existing `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation` lane absorb this cleanly, or does the evidence justify splitting:
   - `relation semantics / directionality`
   - `prompt authority conflict`
   into separate bounded child lanes?

## 6. Required Evidence Discipline

1. Treat console rendering as non-authoritative.
2. Read text artifacts with explicit UTF-8 handling.
3. Prefer artifact truth over summary claims when they disagree.
4. Separate:
   - primary blocker
   - supporting contributor
   - ruled-out explanation
5. If a claim depends on a single log sentence, verify it against either:
   - manuscript/artifact text
   - DB/JSONL payload
   - prompt text in `llm_io.jsonl`
6. Keep direct quotations short and compliant.

## 7. Output Contract For Opus

Return one bounded survey document and one raw evidence file:

- survey doc:
  - `docs/2026-04-03/0_0-stage4-npcdrift-relation-semantics-prompt-conflict-bounded-survey.md`
- evidence json:
  - `docs/2026-04-03/0_0-stage4-npcdrift-relation-semantics-prompt-conflict-evidence.json`

The Opus survey doc must remain a draft, not a final canonical claim:

- use `Status: draft-bounded-post-run-evidence`
- do not mark the survey `final`
- leave final closure, SSOT mutation, and roadmap mutation to the Codex post-survey audit step

Required survey sections:

1. `Coverage`
2. `Findings`
3. `Non-Issues`
4. `Primary Owner Verdict`
5. `Minimal Next Wave`
6. `Open Questions`
7. `Stop`

Required stop line:

- `read-only bounded survey complete; no files mutated outside docs/2026-04-03 survey outputs`

## 8. Expected Finding Shape

The survey should try to end in this form if the evidence supports it:

- `genre misbinding`: ruled out
- `opening replay`: not the dominant family in this run
- `primary seam`: Stage4 `relation_to_protag` semantics / gate escalation mismatch
- `secondary seam`: prompt authority conflict (`대화 비율: 0%`, possibly other stale style guidance)
- `additional contributors`: numeric authority and timeline authority collisions
- `owner`: still Stage4 bounded child seam, not Stage2/3 reactivation

If the evidence does not support that shape, say so explicitly and reassign owner with concrete reasons.

## 9. Codex Follow-Up Contract

After Opus returns the bounded survey:

1. Codex re-audits the new survey in 3 passes against the live workspace.
2. If confidence is still below 95%, Codex does not implement yet.
3. If confidence reaches 95%+, Codex implements the smallest bounded Stage4 fix set supported by the survey.
4. Implementation should update the existing Stage4 NPC relation-tag SSOT and roadmap rather than opening a broad new Stage2/3 lane unless the audited evidence explicitly forces that conclusion.
