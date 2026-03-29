## Stage4 Retry Loop Compression Full Survey Audit Order

Date: 2026-03-29
Status: active
Track: system
Type: bounded full-survey audit order
Topic Slug: stage4-retry-loop-compression

Commit State:
- Baseline Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Baseline Dirty Summary: `dirty tracked drift in stage4/provider/runtime/tests plus narrative assets, temp queue, and canary artifacts; latest live control canary is canary_0329_feedback_windowing_check`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

### 1. Goal

Run a bounded system-track survey on the Stage 4 `retry loop compression` problem before any new code changes.

The purpose is not to redesign Stage 4 broadly.
The purpose is to answer one concrete question:

`Why did the clean Gemini canary still need 8 rounds on EP3, and what is the smallest safe contract move that reduces repeated continuity_firewall/post_select_conflict oscillation without moving quality judgment out of the Director?`

This survey exists because current evidence suggests:

- the `fix_scope` seam is now closed enough for operator evidence
- `feedback windowing` passed and removed the earlier advisory snowball
- a clean Gemini canary still showed one expensive retry family:
  - `continuity_firewall` rejects at low score
  - near-pass candidates later fail via `post_select_conflict`
  - the episode eventually passes, but only after 8 rounds
- this looks less like one static plateau and more like a `gate oscillation / lane thrash` family

### 2. Required Output Artifact

Produce exactly one draft survey document here:

`docs/2026-03-29/stage4-retry-loop-compression-full-survey.md`

Document status must be:

`Status: draft-for-audit`

This is intentionally not a final execution SSOT.
Do not create a temp mirror.
Do not create an execution roadmap yet.

### 3. Scope

Included surfaces:

- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_outcome_runtime.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_orchestrator.py`
- `modules/domain/agents/director_ensemble.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_stage4_orchestrator.py`
- prior bounded survey / execution context only as support:
  - `docs/2026-03-28/stage4-feedback-windowing-full-survey.md`
  - `docs/2026-03-28/stage4-feedback-windowing-execution-ssot.md`
  - `docs/2026-03-28/stage4-decision-contract-matrix-full-survey.md`
  - `docs/2026-03-28/why-fix-pack-is-empty-full-survey.md`
  - `docs/2026-03-29/stage4-gemini-direct-default-full-survey.md`
- live evidence under:
  - `projects/canary_0329_feedback_windowing_check/logs/`
  - support comparison only:
    - `projects/canary_0328_stage4_ifc_bridge_check/logs/`
    - `projects/canary_0328_gemini_direct_fixscope_check/logs/`
- inspect raw artifacts where present:
  - `episode_production.jsonl`
  - `runtime_audit.jsonl`
  - `session/decisions.jsonl`
  - `session/ui_events.jsonl`
  - `session/llm_io.jsonl`
  - `session_*.log`

Excluded surfaces:

- provider-default or model-default redesign
- `.env`, `config/models.yaml`, provider routing policy changes
- fallback observability wave
- feedback windowing rework unless it directly affects loop compression proof
- broad blueprint-authoring redesign
- general prose-quality tuning
- execution SSOT authoring

### 4. Survey Questions

The survey must answer all of these.

1. Oscillation truth
- In the EP3 clean Gemini canary, what exact round sequence produced the 8-round path?
- Which rounds were blocked by `continuity_firewall`, which by `post_select_conflict`, and which by other gates?
- Did the retry family alternate between low-score hard rejects and high-score provisional-pass invalidations?

2. Lane-transition truth
- After each reject family, what retry lane was actually selected?
- When `continuity_firewall` fires with `fix_scope=full`, why does the next useful candidate still return to the same family?
- When `post_select_conflict` invalidates a near-pass candidate, why is the follow-up path still a broad rewrite instead of a more compressed carryover path?

3. Ownership truth
- Which decisions are Director-authored versus runtime-derived?
- Which fields are authoritative for:
  - reject family
  - retry lane
  - escalation
  - blueprint-patch or carryover state
- Where does Python currently choose transition mechanics versus only surfacing metadata?

4. Compression leverage truth
- What is the smallest bounded move that would likely reduce `8R -> 3-4R` without violating Director sovereignty?
- Evaluate bounded options only, such as:
  - repeated-family ceiling by fingerprint or bucket
  - continuity_firewall to blueprint-patch escalation earlier
  - provisional-pass preservation / conflict-first carryover tightening
  - lane-transition table tightening
  - loop-state based compression after repeated alternating gates

5. Minimal safe next step
- After the survey, what is the smallest safe next move?
- Rank only bounded options, not broad redesign.
- Explicitly state whether the first move should be:
  - `continuity/post_select oscillation compression`
  - `earlier blueprint/frontier escalation`
  - `retry lane transition tightening`
  - `provisional-pass preservation tightening`
  - `do nothing; current evidence is insufficient`

### 5. Required Findings Format

The draft survey document must contain these sections in order.

1. Scope and Intent
2. Evidence Sources
3. EP3 Round-by-Round Loop Map
4. Gate Family and Lane Transition Matrix
5. Authoritative vs Derived Ownership Map
6. Live Canary Oscillation Evidence
7. Root-Cause Assessment
8. Bounded Compression Options Ranked
9. Recommended Bounded Next Step
10. Open Questions
11. Confidence

### 6. Evidence Rules

Use real code and real logs only.
Every important finding must include file references and line references where possible.

When using the clean Gemini canary:

- treat `projects/canary_0329_feedback_windowing_check/logs/` as the mainline control evidence
- prefer EP3 round-by-round raw rows over summary prose
- explicitly separate:
  - low-score continuity-firewall rounds
  - high-score post-select-conflict rounds
  - the final successful round

When discussing retry families:

- distinguish `same family plateau` from `alternating family loop`
- do not call the EP3 behavior a simple plateau if the gate family changed materially across rounds
- do not collapse `continuity_firewall` and `post_select_conflict` into one bucket unless code ownership proves they share the same authoritative transition path

When discussing compression:

- do not recommend Python-side quality substitution
- do not recommend skipping Director review
- do not recommend deleting firewall checks
- do not recommend broad `max_rounds` reduction without family-aware evidence

When discussing blueprint/frontier repair:

- distinguish:
  - local manuscript patch
  - blueprint patch snapshot or frontier correction
  - full regenerate
- preserve the current rule that Python may choose a lane contract, but not invent story-quality judgment

### 7. Guardrails

Do not change code.
Do not change config.
Do not write an execution SSOT yet.
Do not create a roadmap yet.
Do not widen this into a full Stage 4 redesign survey.

Do not reopen:

- provider-default work
- fallback observability work
- fix_scope contract work
- feedback windowing work

unless the inspected code proves one of those directly causes the EP3 8-round loop.

Do not propose:

- generic `reduce max rounds`
- unconditional forced PASS
- Python-authored story fixes
- disabling `continuity_firewall`
- masking `post_select_conflict`

This survey is about safer loop compression, not bypassing quality control.

### 8. Preferred Operating Conclusion

The survey should aim to determine whether the safest first move is:

`compress repeated continuity_firewall ↔ post_select_conflict oscillation by tightening lane transitions or escalating earlier to the correct blueprint/frontier path, instead of letting near-pass candidates fall back into another broad rewrite loop`

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
