## Stage4 Provider Fallback Observability Gap Full Survey Audit Order

Date: 2026-03-29
Status: active
Track: system
Type: bounded full-survey audit order
Topic Slug: stage4-provider-fallback-observability-gap

Commit State:
- Baseline Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Baseline Dirty Summary: `dirty: 14 tracked, 368 untracked; hotspots: feedback-windowing code/tests, narrative docs, canary projects, temp queue`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

### 1. Goal

Run a bounded system-track survey on the Stage 4 `provider fallback observability gap` before any provider-routing or runner changes.

The purpose is not to redesign multi-provider strategy broadly.
The purpose is to answer one concrete question:

`When a primary Stage 4 model call fails and fallback serves the request, do llm_io, token/cost accounting, audit sinks, and operator-facing canary evidence still describe the same underlying truth, or are they currently split across contradictory sinks?`

This survey exists because current evidence suggests:

- one contaminated canary recorded `llm_io.jsonl` as effectively `100% FAIL` while episode-level artifacts still showed Gemini token/cost usage and real progression
- the workspace currently runs `Claude-first` by default and often recovers through Gemini fallback, which makes clean interpretation dependent on sink accuracy
- recent Gemini direct-only canaries improved result quality, which increases the value of understanding whether past failures were structural, provider-contaminated, or both
- canary decision-making is now increasingly contract-driven, so observability drift between `primary failure`, `fallback success`, and `cost truth` is becoming a top interpretation risk

### 2. Required Output Artifact

Produce exactly one draft survey document here:

`docs/2026-03-29/stage4-provider-fallback-observability-gap-full-survey.md`

Document status must be:

`Status: draft-for-audit`

This is intentionally not a final execution SSOT.
Do not create a temp mirror.
Do not create an execution roadmap yet.

### 3. Scope

Included surfaces:

- `modules/domain/agents/base_agent.py`
- `modules/core/llm_provider.py`
- `modules/core/providers/anthropic_provider.py`
- `modules/core/providers/gemini_provider.py`
- `modules/core/providers/vertex_provider.py`
- `modules/core/providers/anthropic_vertex_provider.py`
- provider/model resolution support paths that materially affect fallback truth:
  - `config/models.yaml`
  - `scripts/run_stage4_canary.py`
- Stage 4 operator evidence sinks that consume or expose provider outcomes:
  - `logs/session/llm_io.jsonl`
  - `logs/session/decisions.jsonl`
  - `logs/session/ui_events.jsonl`
  - `logs/runtime_audit.jsonl`
  - `logs/episode_production.jsonl`
  - any session summary or cost/token sink directly linked from the inspected code
- prior canary evidence as support:
  - `projects/canary_0328_fixpack_contract_check_v2/logs/`
  - `projects/canary_0328_gemini_direct_fixscope_check/logs/`
  - `projects/canary_0328_sink_verify_micro/logs/`
  - `projects/canary_0329_feedback_windowing_check/logs/` if present

Excluded surfaces:

- broad Stage 4 quality-policy redesign
- fix_scope / fix_pack / retry-lane contract redesign except where logging ownership depends on them
- prompt wording changes
- `.env` editing or secret rotation
- default provider-policy changes as an implementation recommendation
- execution SSOT authoring

### 4. Survey Questions

The survey must answer all of these.

1. Provider truth path
- How is the primary model chosen?
- How is backup or fallback chosen?
- Which branch counts as `same request recovered by fallback` versus `new attempt`?
- Where does the authoritative `served model` truth live today?

2. Sink truth split
- For one Stage 4 request that fails primary and succeeds on fallback, which sinks record:
  - attempted primary model
  - actual served fallback model
  - token usage
  - cost usage
  - error category
  - operator-facing narrative of what happened
- Do those sinks agree on one request identity, or do they fragment?

3. llm_io truth
- Does `llm_io.jsonl` currently record only failed primary attempts, only final served attempts, or both?
- If both can appear, are they correlated by request id, attempt id, model, or timestamp well enough for canary post-mortem use?
- If only one side appears, identify exactly where the other side is lost.

4. Cost and token truth
- Which sink is authoritative for token and cost accounting during fallback?
- Can episode-level token/cost totals show served fallback usage while `llm_io.jsonl` looks like total failure?
- If yes, pinpoint the exact owner and write path causing the divergence.

5. Operator interpretation risk
- Which contradictory patterns can currently fool an operator during canary review?
- Rank the highest-risk contradictions, such as:
  - `llm_io all fail` while episode artifacts progress
  - `model_breakdown` implying fallback success without a matching request trace
  - provider contamination being over-attributed to core Stage 4 logic

6. Smallest safe next move
- After the survey, what is the smallest safe next move?
- Rank only bounded options such as:
  - fallback-served model annotation in `llm_io`
  - request lineage or correlation id propagation
  - operator-facing sink split between `attempted_model` and `served_model`
  - token/cost truth-source tightening
  - no code change yet because current evidence is insufficient

### 5. Required Findings Format

The draft survey document must contain these sections in order.

1. Scope and Intent
2. Evidence Sources
3. Provider Selection and Fallback Path Map
4. Sink-by-Sink Truth Matrix
5. Live Canary Contradiction Evidence
6. Root-Cause Assessment
7. Highest-Risk Operator Misreads
8. Bounded Remediation Options Ranked
9. Recommended Bounded Next Step
10. Confidence

### 6. Evidence Rules

Use real code and real logs only.
Every important finding must include file references and line references where possible.

When using contaminated canary evidence:

- do not dismiss it just because the run is contaminated
- do separate `provider failure truth` from `fallback observability truth`
- do not claim `fallback definitely served` unless at least one sink materially supports it
- if the conclusion is inference rather than direct proof, label it explicitly as inference

When using clean Gemini direct-only canaries:

- treat them as control evidence for what non-contaminated sinks should look like
- do not overclaim that a clean run proves the contaminated sink was correct or incorrect

When comparing sinks:

- preserve distinction between:
  - attempted primary model
  - actual served model
  - fallback chain choice
  - token/cost accounting source
  - operator summary text
- do not merge these into one generic `model used` statement

### 7. Guardrails

Do not change code.
Do not change config.
Do not write an execution SSOT yet.
Do not create a roadmap yet.
Do not widen this into a full provider-platform redesign survey.

Do not recommend changing provider defaults as the first move unless the evidence proves the observability gap cannot be fixed independently.

Do not erase the distinction between:

- `attempted_model`
- `served_model`
- `backup_model`
- `fallback_chain entry`
- `token/cost truth source`

Those are different contract layers and must remain separated in the survey.

Do not treat `llm_io` as automatically authoritative just because it is low-level.
The survey must determine which sink is authoritative for which aspect of truth.

### 8. Preferred Operating Conclusion

The survey should aim to determine whether the safest first move is:

`tighten observability around attempted-model vs served-model lineage so contaminated canaries stop misleading operators, without forcing a provider-policy redesign in the same wave`

Do not force that conclusion if evidence contradicts it.
But do test it directly against the inspected code and raw canary artifacts.

### 9. Handoff Rule

After saving the draft survey doc, stop.

Do not audit it.
Do not produce execution docs.
Do not patch code.

The next step will be:

1. internal 3-pass audit of the draft survey
2. bounded execution SSOT creation
3. only then code changes
