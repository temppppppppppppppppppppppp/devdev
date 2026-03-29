# Stage4 Gemini Direct Default - Full Survey Audit Order

Date: 2026-03-29
Status: final
Track: system
Topic Slug: stage4-gemini-direct-default
Intent: make Gemini Developer API direct the default runtime and canary path before any further Stage 4 contract work

---

## 1. Mission

Produce a bounded system survey that answers one concrete operating question:

> How do we make Geuldobi runtime and Stage 4 canary default to Gemini Developer API direct (`GOOGLE_API_KEY`) while demoting Claude and Vertex to explicit opt-in paths?

This is not a provider-feature comparison.
This is a default-routing and operator-discipline survey.

The desired end state is:

- normal Geuldobi runs default to Gemini direct
- Stage 4 canaries default to Gemini direct
- Vertex is not used unless the operator explicitly opts in
- Claude is not used unless the operator explicitly opts in
- operator flow no longer depends on temporary `models.yaml` backup/restore hacks for clean Gemini canaries

---

## 2. Required Reading

Read these before surveying:

1. `AGENTS.md`
2. `docs/implementation/system-order-init-harness.md`
3. `docs/implementation/system-full-survey-execution-harness.md`

Use system-track rules only.
Do not invoke narrative-router documents.

---

## 3. Scope

### Included

- `config/models.yaml`
- `modules/core/llm_router.py`
- `modules/core/models_config.py`
- `modules/domain/agents/base_agent.py`
- `scripts/run_stage4_canary.py`
- any directly related canary helper or bootstrap seam that controls model/provider defaults
- desktop/process launch env injection surfaces if they affect default provider selection:
  - `modules/api/process_runner.py`

### Excluded

- changing prompt contracts
- Stage 4 quality/reject/escalation logic
- provider SDK rewrites
- pricing or benchmark tuning
- `.env` content edits
- model quality comparison between Gemini and Claude
- long-term schema redesign of logging sinks

Keep the survey tightly bounded to:

- default provider selection
- default model selection
- default env interpretation
- canary runner override seams
- operator safety / contamination risk

---

## 4. Core Questions

Answer these with direct code evidence:

1. What surface is authoritative for default agent model selection today?
   - `config/models.yaml`
   - `models_config`
   - role constants
   - any hidden fallback shell

2. What surface is authoritative for provider routing today?
   - direct Gemini
   - Vertex
   - Anthropic
   - prefixed-model routing

3. Why does current runtime still behave Claude-first for Stage 4 core roles?

4. Why do current clean Gemini canaries require process-local `models.yaml` edits instead of first-class runner options?

5. What is the smallest safe path to:
   - make Gemini direct the default for Geuldobi
   - make Gemini direct the default for Stage 4 canary
   - keep Claude and Vertex available as explicit opt-in only

6. What side effects must be controlled?
   - desktop/app launch env
   - process runner env injection
   - canary reproducibility
   - tests assuming old defaults
   - docs/operator instructions

---

## 5. Required Evidence

Survey must cite direct evidence from:

- `config/models.yaml`
- `modules/core/llm_router.py`
- `modules/core/models_config.py`
- `modules/domain/agents/base_agent.py`
- `scripts/run_stage4_canary.py`
- `modules/api/process_runner.py`

If another file is needed, include it only if it is directly on the selection path.
Do not widen the survey into unrelated provider or prompt files.

At minimum, capture:

- current default role models for `analyst`, `chief_writer`, `director`
- current fallback chain
- current provider enablement defaults
- current model-prefix routing rules
- current env names accepted for Gemini / Vertex / Claude
- current canary runner limitations for per-run provider/model override

---

## 6. Deliverable Requirements

Write one bounded survey doc:

- canonical path:
  - `docs/2026-03-29/stage4-gemini-direct-default-full-survey.md`

The survey must contain:

1. scope and intent
2. baseline evidence
3. current default-routing map
4. mismatch / contamination / operator-risk findings
5. bounded implementation options
6. recommended first move
7. excluded/deferred items
8. explicit confidence score

Do not write execution SSOT in this step.
Stop after the draft survey is saved.

---

## 7. Decision Frame

The survey must explicitly judge these alternatives:

### Option A. Config-only default swap

- change `models.yaml` defaults to Gemini direct-friendly models
- leave runner behavior mostly unchanged

### Option B. Config + canary runner seam

- config defaults move to Gemini direct
- canary runner gains explicit per-run override seam for Gemini direct mode

### Option C. Larger provider-policy overhaul

- broader router/provider redesign

The survey should presumptively favor the smallest safe option unless evidence shows that it is insufficient.

---

## 8. Guardrails

- Python must not add new quality judgment logic
- do not redesign Stage 4 contracts in this wave
- do not mutate `.env`
- do not change prompt docs
- do not implement code in this survey step
- do not write `docs/temp/` execution mirrors yet
- do not claim “resolved” or “default switched” before implementation and live validation

---

## 9. Specific Questions To Resolve

The survey must explicitly answer:

1. Can `config/models.yaml` alone make Stage 4 runtime Gemini-first in practice?
2. Is `vertex_ai.enabled: true` acceptable if default models are plain `gemini-*`, or should Vertex be default-disabled?
3. What exact seam is missing in `run_stage4_canary.py`?
   - explicit `--model-profile`
   - explicit `--provider-mode`
   - explicit temporary override API
4. Does `modules/api/process_runner.py` currently reintroduce Claude/Vertex by default for desktop/app flows?
5. What is the minimum code surface to touch for a safe default switch?

---

## 10. Output Stop Condition

After saving:

- `docs/2026-03-29/stage4-gemini-direct-default-full-survey.md`

stop immediately.

No code changes.
No execution SSOT.
No canary run.

---

## 11. Final Operator Handoff Line

Use this exact handoff posture at the end:

> Draft survey saved. Status: draft-for-audit. Stopped per handoff rule — no audit, no execution SSOT, no code changes.
