# Stage4 CW Webnovel Identity Context Hierarchy Remediation Execution SSOT

Date: 2026-03-31
Status: code-landed-static-validation-closed
Confidence: 96%
Document Type: execution SSOT
Canonical Path: `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage4-cw-webnovel-identity-context-hierarchy-remediation-execution-ssot.md`
Baseline Commit: `170963d34d30d3076a57926c5d1ed250f13ec421`
Baseline Dirty Summary: `0_2 frontier-run logs/db/ui mutation had been active during survey drafting`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `run was operator-aborted mid frontier; post-run merge audit confirmed the remediation ordering remains stable`
Source Survey Docs:
- `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-parallel-bounded-survey.md`
- `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-actionability-audit.md`
- `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-post-run-merge-audit.md`
Evidence Artifacts:
- `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-parallel-evidence.json`
- `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-actionability-evidence.json`
- `projects/0_2/logs/session/decisions.jsonl`
- `projects/0_2/logs/artifacts/stage4/ep_0002/attempt_01/patched_blueprint_after_fix__V75-D_blueprint_inplace.json`
- `projects/0_2/logs/artifacts/stage4/ep_0002/attempt_02/selected_before_fix__A.txt`
- `projects/0_2/drafts/ep_0001.txt`
- `0_temp.txt`
Side-Effect Coverage: covered

## 1. Intent

Realize the smallest safe cross-stage wave that addresses the now-closed diagnosis:

- `CW first-pass` is being shaped too much like an analyst/summarizer task
- `Stage 3 blueprint prose` is still injecting briefing/system/authority drift into Stage 4 input
- `retry` is compensating for bad task shape more than proving that first-pass quality is intrinsically low

This wave therefore does not try to:

- replace models
- redesign the full detector stack
- rewrite Stage 2 tactical authoring
- weaken truth gates

It does four bounded things:

1. strengthen `CW` writer identity and anti-briefing register constraints
2. physically separate Stage 4 prompt hierarchy so hard canon appears as hard canon
3. harden Stage 3 blueprint generation against briefing/HUD/system contamination and previous-blueprint register leakage
4. verify the effect only after the current live frontier run finishes

## 2. Baseline Facts

- `CW` role framing exists, but is thin relative to surrounding analytical context:
  - `modules/domain/agents/chief_writer_prompts.py:93-205`
- hard canon exists, but is physically scattered and mixed with soft guidance:
  - `modules/domain/agents/chief_writer_context.py:177-272`
  - `modules/domain/agents/chief_writer_context.py:494-523`
- `EP2` Stage 4 showed:
  - R0 `95` -> REJECT
  - R1 `95` -> REJECT
  - R2 `94` -> PASS
  - anchor: `projects/0_2/logs/session/decisions.jsonl:8-10`
- `EP2` failure cluster included:
  - fabricated status window / hologram
  - wrong asset decomposition
  - briefing-style recap phrasing
  - anchors:
    - `projects/0_2/logs/artifacts/stage4/ep_0002/attempt_02/selected_before_fix__A.txt:19-25`
    - `projects/0_2/drafts/ep_0001.txt:91-97`
- current live run also shows Stage 3 authority drift at EP4:
  - anonymous NPC naming
  - `강남센터` drifting to `강남 PB센터`
  - anchor: `0_temp.txt:920-930`

## 3. Scope

Included:

- `modules/domain/agents/chief_writer_prompts.py`
- `modules/domain/agents/chief_writer_context.py`
- `modules/domain/agents/chief_writer_context_packets.py`
- `config/prompts/ensemble.yaml`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/core/stage4_interview_round.py` for bounded writer-facing blueprint handling and writer-ingress ordering only
- bounded tests around prompt hierarchy, blueprint anti-contamination, and writer-facing blueprint shaping
- canonical execution SSOT draft only

Excluded:

- model/provider/fallback redesign
- Stage 2 tactical-doc rewrite
- anti-meta detector implementation
- Flashback family relabeling
- broad Director/post-select policy changes
- DB schema changes
- `docs/temp/` mirror hotfixing without canonical sync

## 4. Pass 1. Inventory Summary

Primary owners:

- `chief_writer_prompts.py`
  - Stage 4 prompt block order
  - writer identity and anti-pattern framing
- `chief_writer_context.py`
  - writer-core section composition
  - blueprint advisory wrapping
- `chief_writer_context_packets.py`
  - prior-manuscript and carryover packet shaping
- `ensemble.yaml`
  - Stage 3 blueprint generation contract
- `blueprint_ensemble.py`
  - prompt-bundle assembly
  - post-parse blueprint sanitation / candidate qualification
  - previous blueprint feed into new blueprint generation
- `stage4_interview_round.py`
  - bounded writer-facing blueprint minimization
  - writer ingress ordering for `mandatory_context` / `preflight_advisory`

Primary operator/runtime surfaces affected:

- Stage 3 generated blueprint prose and structured key-events
- Stage 4 CW prompt layout
- downstream Stage 4 manuscript quality before retry
- future frontier-lag throughput by reducing contaminated first-pass attempts

## 5. Pass 2. Semantic Classification

### Class A. Writer identity hardening

Problem:

- the prompt says `Chief Writer`
- the surrounding prompt still feels like a report/contract/dashboard task

Execution choice:

- strengthen top-of-prompt identity framing
- add explicit negative register rules:
  - not a summarizer
  - not a briefing engine
  - not a status reporter
  - not a recap narrator

Primary patch site:
- `modules/domain/agents/chief_writer_prompts.py:93-110`
- `modules/core/stage4_interview_round.py:2225-2305`
- `modules/core/stage4_interview_round.py:2824-2850`

### Class B. Hard-canon / soft-guidance separation

Problem:

- hard canon is physically scattered
- `writer_core_section` mixes authority and guidance
- advisory demotion exists, but advisory echo containment is weak

Execution choice:

- split `writer_core_section` into hard-canon and soft-guidance subsections
- reorder prompt blocks so hard canon clusters before advisory and HUD-heavy sections
- harden advisory wrapper language to forbid echoing episode-reference, HUD, or system-register phrasing unless canonically established
- preserve deterministic ingress ordering so `mandatory_context` and `preflight_advisory` do not reintroduce duplicate analytical pressure

Primary patch sites:
- `modules/domain/agents/chief_writer_context.py:274-324`
- `modules/domain/agents/chief_writer_context.py:494-523`
- `modules/domain/agents/chief_writer_prompts.py:104-205`
- `modules/core/stage4_interview_round.py:929-943`

### Class C. Prior-truth salience support

Problem:

- previous manuscript truth exists, but is mainly framed as contradiction-prevention evidence
- hierarchy cleanup may still need a compact prior-truth reminder surface early in the prompt

Execution choice:

- keep existing full prior-manuscript section
- preserve current carryover ceiling behavior
- use bounded compact prior-truth reminder support only as part of prompt hierarchy cleanup

Primary patch site:
- `modules/domain/agents/chief_writer_context_packets.py:171-276`

### Class D. Stage 3 anti-contamination hardening

Problem:

- `integrated_scenario` currently allows briefing prose and HUD/system contamination
- `scene_breakdown.key_events` can carry the same contamination into structured authority
- there is currently no centralized post-parse reject/sanitize seam before contaminated blueprint prose is reused downstream

Execution choice:

- add bounded centralized post-parse contamination sanitation/rejection before selection where necessary
- harden the blueprint generation prompt with explicit anti-briefing and anti-contamination rules
- tell the generator that the output is downstream scene authority, not planning prose

Primary patch site:
- `config/prompts/ensemble.yaml:334-402`
- `modules/domain/agents/blueprint_ensemble.py:649-748`

### Class E. Previous-blueprint register leakage

Problem:

- previous blueprint `integrated_scenario` is re-fed verbatim as `[시나리오] ...`
- contaminated long-form register can snowball across episodes

Execution choice:

- stop feeding raw previous scenario prose verbatim
- replace it with bounded structured carryover fields only

Primary patch site:
- `modules/domain/agents/blueprint_ensemble.py:1123-1142`

### Class F. Stage 4 writer-facing blueprint handling

Problem:

- `integrated_scenario` demotion is already correct
- first wave should not overreach into broad runtime sanitization

Execution choice:

- preserve current demotion behavior
- add only bounded advisory echo warnings if needed
- leave deeper detector/sanitizer work deferred

Primary patch site:
- `modules/core/stage4_interview_round.py:929-943`

## 6. Side-Effect Map

- file writes:
  - `modules/domain/agents/chief_writer_prompts.py`
  - `modules/domain/agents/chief_writer_context.py`
  - `modules/domain/agents/chief_writer_context_packets.py`
  - `config/prompts/ensemble.yaml`
  - `modules/domain/agents/blueprint_ensemble.py`
  - optionally `modules/core/stage4_interview_round.py`
  - bounded tests
  - canonical execution SSOT draft

- DB / persistence:
  - no schema change intended
  - future runtime evidence will land through normal Stage 3/4 logs and artifacts

- JSONL / log / audit sinks:
  - no sink contract change is required in this wave
  - expected impact is indirect through cleaner generated content and fewer downstream rejects

- console / UI output:
  - no new operator sink required
  - existing logs should become easier to interpret because contaminated Stage 3/4 outputs are reduced

- rollback / retry:
  - retry policy is not directly changed here
  - expected effect is lower need for retry, not routing redesign

- cache / global state:
  - previous blueprint feed adjustments must stay bounded and not break cached blueprint assembly assumptions

- config / env:
  - prompt/config text only
  - no env mutation

## 7. Realization Architecture

### Tranche 0. Post-Run Revalidation Gate

Before code edits:

- re-audit this canonical SSOT against the live workspace
- confirm no newer run evidence has displaced this wave
- confirm the current workspace still matches the bounded tranche order below

Guardrail:

- if a later rerun shows a stronger alternative root cause, reopen the audit before patching

### Tranche 1. Stage 4 Writer Identity / Anti-Briefing Contract

Files:

- `modules/domain/agents/chief_writer_prompts.py`
- `modules/core/stage4_interview_round.py`

Tasks:

- strengthen top identity block
- add explicit anti-briefing / anti-recap register rules
- keep current contradiction and authority warnings
- keep Stage 4 ingress ordering deterministic for the new top contract

Guardrail:

- additive wording first
- do not yet delete legacy blocks in this tranche

### Tranche 2. Stage 4 Hierarchy Separation and Consumer Containment

Files:

- `modules/domain/agents/chief_writer_prompts.py`
- `modules/domain/agents/chief_writer_context.py`
- `modules/domain/agents/chief_writer_context_packets.py`
- `modules/core/stage4_interview_round.py`

Tasks:

- split `writer_core_section`
- cluster hard canon before advisory/HUD-heavy surfaces
- harden `integrated_scenario_advisory_section` against stylistic echo
- keep `_normalize_writer_blueprint()` as the bounded containment seam
- preserve existing full prior-manuscript truth source

Guardrail:

- keep data payloads substantially the same
- change ordering and labeling first, not retrieval substrate
- prefer Stage 4 containment ahead of broader Stage 3 behavior changes

### Tranche 3. Stage 3 Centralized Sanitation and Previous-Blueprint Feed Cleanup

Files:

- `config/prompts/ensemble.yaml`
- `modules/domain/agents/blueprint_ensemble.py`

Tasks:

- add bounded post-parse contamination sanitation/rejection in the centralized blueprint request path
- add anti-briefing / anti-HUD / anti-system / anti-cross-genre rules
- replace raw previous-scenario feed with bounded structured carryover

Guardrail:

- sanitize or reject only clearly contaminated blueprint prose
- do not reduce blueprint completeness requirements
- do not strip valid recall/continuity language globally

### Tranche 4. Stage 3 Prompt Hardening

Files:

- `config/prompts/ensemble.yaml`
- `modules/domain/agents/blueprint_ensemble.py`

Tasks:

- explicitly require scene-authoritative prose, not planning prose
- add prompt-level anti-briefing / anti-HUD / anti-system / anti-cross-genre rules

Guardrail:

- prompt hardening follows centralized sanitation, not the reverse

### Tranche 5. Verification

Static verification:

- targeted prompt/context tests
- targeted blueprint-generation contract tests
- UTF-8 hygiene

Current realization status:

- code landed for bounded Stage 4 writer-facing blueprint sanitize and Stage 3 prompt hardening
- static validation closed on `2026-03-31`
- validation evidence:
  - `python -m py_compile modules/core/stage4_interview_round.py modules/domain/agents/blueprint_ensemble.py`
  - `python -m ruff check modules/core/stage4_interview_round.py modules/domain/agents/blueprint_ensemble.py tests/test_stage4_handoff_carryover_guardrail.py tests/test_stage3_blueprint_self_audit_wave.py tests/test_tier4_ensemble_caching.py tests/test_blueprint_ensemble_generate_ensemble.py`
  - `python scripts/check_utf8_hygiene.py modules/core/stage4_interview_round.py modules/domain/agents/blueprint_ensemble.py tests/test_stage4_handoff_carryover_guardrail.py tests/test_stage3_blueprint_self_audit_wave.py tests/test_tier4_ensemble_caching.py tests/test_blueprint_ensemble_generate_ensemble.py config/prompts/ensemble.yaml`
  - `pytest tests/test_stage4_handoff_carryover_guardrail.py tests/test_stage4_cw_false_miss_remediation.py tests/test_chief_writer_context.py -q`
  - `pytest tests/test_blueprint_ensemble_generate_ensemble.py tests/test_tier4_ensemble_caching.py tests/test_stage3_blueprint_self_audit_wave.py -q`
- fresh Stage 3 -> Stage 4 rerun evidence is still pending before closure

Live verification:

- fresh Stage 3 -> Stage 4 bounded rerun after the current frontier run finishes
- validate:
  - no HUD/status-window contamination in new blueprint/manuscript path
  - reduced briefing/recap register in first-pass manuscripts
  - no regression in opening-anchor and continuity compliance

## 8. Regression Risks

1. Over-hardening the prompt may flatten prose or overconstrain natural recall.
2. Reordering prompt blocks may accidentally weaken existing opening-anchor or scene-header compliance.
3. Pruning previous blueprint scenario feed too aggressively may hurt long-range continuity.
4. Anti-HUD / anti-system wording may overfire in works where such elements are canonical.

## 9. Test Plan

Extend or add bounded tests in these areas:

- `tests/test_stage4_cw_false_miss_remediation.py`
  - writer identity / anti-briefing preface
  - prompt order and authority clustering
- `tests/test_stage4_handoff_carryover_guardrail.py`
  - contaminated blueprint prose does not reach writer-facing prompt authority unbounded
- `tests/test_chief_writer_context.py`
  - `writer_core_section` split
  - advisory wrapper anti-echo contract
- `tests/test_chief_writer_context_packets_wave7.py` or adjacent packet tests
  - compact prior-truth / carryover support behavior
- `tests/test_blueprint_ensemble_generate_ensemble.py`
  - centralized sanitize/reject seam
  - previous blueprint feed no longer injects raw long-form scenario prose
- a new or adjacent Stage 3 prompt contract test
  - anti-briefing / anti-HUD / anti-cross-genre instructions present in blueprint prompt

## 10. Defer Ledger

Deferred to later wave unless rerun evidence still demands them:

- dedicated anti-meta / recap-register detector
- Flashback family relabeling
- Stage 2 tactical specificity rewrite
- model-tier changes
- broad taxonomy or post-select policy redesign

## 11. Save Gate

This SSOT is `code-landed-static-validation-closed`.

Implementation gate:

1. rerun 3-pass audit against the live workspace immediately before code edits
2. keep canonical and temp mirror synchronized
3. after realization, validate with fresh Stage 3 -> Stage 4 rerun evidence before closure
