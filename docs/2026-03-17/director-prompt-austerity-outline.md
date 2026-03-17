# Director Prompt Austerity Outline

Date: 2026-03-17
Status: draft
Canonical Path: `docs/2026-03-17/director-prompt-austerity-outline.md`
Document Type: planning note
Commit State:
- Baseline Commit: `100ecd03557e1b8c7a3544b5285fc80e7105050c`
- Baseline Dirty Summary: `dirty: 2 tracked docs, 1 tracked runtime log; hotspots: docs/2026-03-16/post-remediation-later-hardening-autopilot-prompt*.md, projects/test_project/logs/episode_production.jsonl`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Scope:
- preserve brainstorming context around Stage 4 Director prompt slimming and input-channel separation
- focus on what Director must see first, what should stay candidate evidence, and what belongs in low-priority reference appendices
- keep the note at planning level without opening an execution queue
Non-Goals:
- no code changes in this note
- no claim that the note is 3-pass finalized
- no execution SSOT, roadmap, or implementation order in this note

## 0. Live Snapshot
- current Director path is not starved for information; it is overloaded with multiple overlapping context channels
- Director already receives stable narrative context, candidate manuscripts, candidate Python warnings, and a very large caller-built `mandatory_context`
- much of the current problem appears to be hierarchy blur, channel duplication, and lack of a clear distinction between decision-critical inputs and reference-only bulk
- this makes prompt austerity a high-ROI topic because it affects verdict quality, retry clarity, and advisory authority all at once

### Current Code Touchpoints
- Stage 4 caller-side Director input assembly: `modules/core/stage4_interview_round.py`
- Director ensemble input contract: `modules/domain/agents/director_ensemble.py` -> `select_and_judge_ensemble()`
- Director Stage 4 prompt template: `modules/domain/agents/director_prompts.py` -> `ENSEMBLE_SELECTION_PROMPT`
- retry re-audit patch history injection: `modules/core/stage4_interview_round.py` -> `_build_reaudit_story_context()`

## 0A. Working Assumptions
- Director should see a thinner, more hierarchical prompt rather than an ever-growing "better safe than sorry" blob
- stable story facts, candidate evidence, and reference-only advisory should not share the same semantic lane
- advisory can still matter without being front-loaded into the main decision block
- retry rounds may justify more context than round 0; austerity should be round-sensitive

## 1. Main Finding
- current Director path already has at least four channels:
  - stable context (`story_context`, `blueprint`, `episode_digest`, `previous_ending`, previous manuscripts)
  - candidate evidence (candidate manuscripts + validation warnings)
  - caller-built `mandatory_context`
  - retry/process context such as patch-history re-audit story blocks
- the caller-built `mandatory_context` currently absorbs too many conceptually different items and behaves like a giant mixed authority block

## 2. Current Overload Structure

### 2.1 Stable Context
- `story_context`
- `blueprint`
- `episode_digest`
- `previous_ending`
- `prev_manuscripts_text`

These are already supplied directly to the Director ensemble and belong to the primary decision frame.

### 2.2 Candidate Evidence
- candidate manuscripts A/B/C
- per-candidate Python warnings from `validation_results`

These are already passed in the candidate/validation channel and do not need to be heavily duplicated elsewhere.

### 2.3 Caller-Built Mandatory Context
Current caller-side additions include:
- writing directive
- POV/external POV policy
- advisory chain output
- timeline notes
- arc time markers
- scene similarity advisory
- candidate diversity advisory
- preflight advisory
- Python warning bulk for Director
- conflict warning text
- DB pacing/satisfaction/reveals/reflexion advisory
- strategy win-rate and `fix_scope` stats
- work-review advisory

Many of these are helpful in isolation, but they do not all belong in the same rank or urgency tier.

### 2.4 Retry / Process Context
- patch-history snippets are injected into `story_context` during re-audit
- this is useful, but should likely remain conditional and explicit rather than merged into first-pass decision layers

## 3. Why This Matters
- a prompt that is too thick can blur decision priority even when all the ingredients are individually useful
- prompt austerity is upstream of:
  - verdict quality
  - advisory authority clarity
  - retry efficiency
  - operator trust in Director outcomes

## 4. Three-Pack Target Model

### Pack A. Decision Core
Only the things Director should need for a first, principled judgment.

Candidate contents:
- story-context core summary
- blueprint
- episode digest / previous ending
- previous manuscripts text
- must-hold truth and continuity constraints
- shared high-severity failure notices
- only essential POV/policy rules

Principle:
- short, stable, high-authority
- should be seen first
- should not be crowded by low-value reference bulk

### Pack B. Candidate Evidence
Evidence tied directly to the candidate manuscripts being judged.

Candidate contents:
- candidate A/B/C manuscripts
- per-candidate validation warnings
- compact structured validation evidence
- candidate-specific coverage or contradiction cues

Principle:
- keep candidate evidence close to the candidates
- avoid re-injecting the same evidence as bulky global `mandatory_context`

### Pack C. Reference Appendix
Low-priority but possibly useful supporting material.

Candidate contents:
- DB pacing/satisfaction/reveals/reflexion trend notes
- win-rate and fix-scope statistics
- diversity advisory
- scene similarity advisory
- broad work-review advisory
- some preflight or process notes
- retry-only patch history when applicable

Principle:
- do not let this appendix dominate the first decision pass
- ideal for conditional or later-round exposure

## 5. Current Mismatch
- `mandatory_context` is currently used as if it were all of the following at once:
  - truth layer
  - advisory layer
  - Python warning surface
  - reference appendix
  - operational memo
- this mixes authority and urgency in one channel
- Director prompt text in `director_ensemble.py` already describes the block as "참고자료", but in practice the block is too large to remain psychologically reference-only

## 6. Five-Step Sequential Hardening

### Step 1. Channel De-Duplication
- stop duplicating the same warning or evidence across `validation_results` and large `mandatory_context` text where possible
- first goal is not smarter prompts but fewer repeated signals

### Step 2. Decision Core Freeze
- define a minimal, stable Director core
- make sure round 0 always starts from this thin core before any broader advisory appendices are added

### Step 3. Reference Appendix Split
- move low-priority trend and operational notes out of the main decision block
- keep them as explicit low-priority appendix material rather than hidden inside the same authority band

### Step 4. Retry-Conditional Expansion
- allow thicker support only for retries or specific reject buckets
- round 0 should be slim-first by default
- retries may reopen some appendix material or patch-history blocks as needed

### Step 5. Prompt-Budget Policy
- protect the Decision Core first
- keep candidate evidence second
- trim the appendix first under pressure
- this mirrors the proposed Stage 4 context-tier model on the Director side

## 7. Suggested Stop Line
- the best near-term ROI is Step 1 through Step 3
- Step 4 and Step 5 become more valuable after the semantic and context-tier notes are stabilized
- going beyond that too soon would likely drift into implementation design before the conceptual separation is settled

## 8. Relationship To Other Draft Notes
- aligns with `stage4-context-composition-ranking-outline.md`
  - that note focuses on CW-side context ranking
  - this note focuses on Director-side prompt austerity
- aligns with `quality-gate-semantics-outline.md`
  - thinner Director prompts make it easier to preserve meaning separation between verdict, advisory, and gate basis
- aligns with `pass-with-fix-local-repair-contract-outline.md`
  - cleaner Director prompts should reduce accidental semantic spread around `PASS_WITH_FIX`

## 9. Why This Topic Has High ROI
- it is upstream of both verdict quality and retry cost
- it can reduce decision noise without requiring stronger models
- it creates a cleaner base for later retry-budget or routing-policy work

## 10. Open Questions To Resume Later
- which current advisory families deserve round-0 visibility versus retry-only visibility
- whether some current `story_context` content should also be slimmed, not just `mandatory_context`
- whether candidate-specific warnings should be compacted inside Director ensemble formatting rather than pushed from the caller
- whether the reference appendix should be entirely hidden on round 0 for some genres or only shortened
- how to keep Director prompt austerity aligned with the separate CW-side context-tier model without duplicating all the same concepts
