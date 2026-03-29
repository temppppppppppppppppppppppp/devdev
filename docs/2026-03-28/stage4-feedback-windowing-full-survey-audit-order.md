## Stage4 Feedback Windowing Full Survey Audit Order

Date: 2026-03-28
Status: active
Track: system
Type: bounded full-survey audit order
Topic Slug: stage4-feedback-windowing

Commit State:
- Baseline Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Baseline Dirty Summary: `dirty: 8 tracked, 26 untracked; hotspots: narrative docs, canary projects, temp queue`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

### 1. Goal

Run a bounded system-track survey on the Stage 4 `feedback snowball` / `feedback windowing` problem before any new code changes.

The purpose is not to redesign Stage 4 broadly.
The purpose is to answer one concrete question:

`Is repeated Stage 4 rejection being amplified by unbounded accumulation of advisory and retry feedback, and if so, what is the smallest safe windowing contract that reduces negative-priming risk without moving quality judgment out of the Director?`

This survey exists because current evidence suggests:

- `plateau`, `TF-29`, `IFC`, `post_select_conflict`, and other derived notices are prepended into later-round feedback
- the Stage4 decision-contract survey already marked `Feedback snowball` as a HIGH-confidence mismatch (`M-4`)
- earlier failing canaries showed repeated historical warning accumulation across rounds
- the latest clean Gemini canary passed, which means the next bounded move should target a remaining structural amplifier, not reopen the closed `fix_scope` seam

### 2. Required Output Artifact

Produce exactly one draft survey document here:

`docs/2026-03-28/stage4-feedback-windowing-full-survey.md`

Document status must be:

`Status: draft-for-audit`

This is intentionally not a final execution SSOT.
Do not create a temp mirror.
Do not create an execution roadmap yet.

### 3. Scope

Included surfaces:

- `modules/core/stage4_outcome_runtime.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_director_runtime.py`
- `modules/domain/agents/director_ensemble.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_stage4_orchestrator.py`
- prior bounded survey context only as support:
  - `docs/2026-03-28/stage4-decision-contract-matrix-full-survey.md`
  - `docs/2026-03-28/why-fix-pack-is-empty-full-survey.md`
  - `docs/2026-03-28/stage4-ifc-bridge-full-survey.md`
- live canary evidence under:
  - `projects/canary_0328_stage4_ifc_bridge_check/logs/`
  - `projects/canary_0328_fixpack_contract_check_v2/logs/`
  - `projects/canary_0328_gemini_direct_fixscope_check/logs/`
  - `projects/canary_0328_sink_verify_micro/logs/` as support only
- inspect raw artifacts where present:
  - `episode_production.jsonl`
  - `runtime_audit.jsonl`
  - `session/decisions.jsonl`
  - `session/ui_events.jsonl`
  - `session/llm_io.jsonl`
  - `session_*.log`

Excluded surfaces:

- provider-default or model-default redesign
- `.env`, `config/models.yaml`, Vertex/Claude/Gemini routing policy changes
- broad Stage 4 escalation redesign
- fix_scope contract redesign beyond what is needed to distinguish authoritative vs derived feedback ownership
- Chief Writer prose quality or manuscript-content diagnosis
- execution SSOT authoring

### 4. Survey Questions

The survey must answer all of these.

1. Accumulation truth
- Where exactly are `plateau`, `TF-29`, `IFC`, `post_select_conflict`, CoVe, and other advisories inserted into later-round feedback?
- Which paths prepend, append, dedupe, or fully replace existing feedback?
- Which fields are authoritative Director output vs runtime-derived notices?

2. Prompt-path truth
- Which accumulated text reaches:
  - Chief Writer generation prompts
  - Director follow-up evidence or review prompts
  - operator JSONL / DB / console sinks
- Are the same notices duplicated across multiple paths in the same round?

3. Growth truth
- In failing canaries, does round-by-round feedback actually grow linearly or near-linearly?
- Quantify at least one concrete failing case using raw artifacts where possible.
- Separate authoritative Director rationale from later derived retry/advisory layering.

4. Safe windowing truth
- What is the smallest bounded move that reduces snowball risk while preserving Director sovereignty?
- Evaluate only bounded options such as:
  - latest-derived-advisory windowing
  - category de-duplication
  - keep authoritative reason verbatim, compact historical derived notices
  - N-round recent window
  - evidence-only compaction without prompt compaction

5. Minimal safe next step
- After the survey, what is the smallest safe next move?
- Rank only bounded options, not broad redesign.
- Explicitly state whether the first move should be:
  - `derived-advisory feedback windowing`
  - `authoritative-vs-derived feedback split tightening`
  - `operator evidence compaction only`
  - `post_select_conflict notice narrowing`
  - `do nothing; current evidence is insufficient`

### 5. Required Findings Format

The draft survey document must contain these sections in order.

1. Scope and Intent
2. Evidence Sources
3. Current Feedback Accumulation Map
4. Authoritative vs Derived Input Path Matrix
5. Live Canary Growth Evidence
6. Root-Cause Assessment
7. Bounded Windowing Options Ranked
8. Recommended Bounded Next Step
9. Open Questions
10. Confidence

### 6. Evidence Rules

Use real code and real logs only.
Every important finding must include file references and line references where possible.

When using failing canary evidence:

- distinguish provider contamination from structural accumulation behavior
- do not dismiss a contaminated run if it still proves line-level accumulation
- do not claim "feedback snowball caused the reject" unless the survey shows the actual accumulation path into prompts or decision inputs

When using the latest clean Gemini canary:

- treat it as control evidence
- use it to test whether the same accumulation family appears in successful runs
- do not overclaim from a short successful run if the failing family needed more rounds to manifest

When discussing authoritative vs derived fields:

- do not collapse them into one `fix_scope`/`repair_scope` style narrative
- preserve the distinction between:
  - Director-authored rationale
  - runtime advisory
  - retry directives
  - operator-only evidence annotations

### 7. Guardrails

Do not change code.
Do not change config.
Do not write an execution SSOT yet.
Do not create a roadmap yet.
Do not widen this into a full Stage 4 redesign survey.

Do not recommend Python-side quality substitution.
This survey is about windowing and ownership, not about letting Python decide what quality problems matter.

Do not recommend silently clipping or deleting authoritative Director rationale.
If compaction is recommended, it must preserve authoritative reasoning and target only derived historical advisory layering unless evidence proves otherwise.

Do not conflate:

- authoritative Director reason
- retry-derived advisory
- operator-facing summary text
- prompt payload text

Those may share strings, but they are different contract layers.

### 8. Preferred Operating Conclusion

The survey should aim to determine whether the safest first move is:

`keep Director-authored rationale verbatim, but window or dedupe runtime-derived historical advisories before they snowball into later rounds`

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
