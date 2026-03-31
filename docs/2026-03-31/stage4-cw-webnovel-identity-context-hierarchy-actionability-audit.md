# Stage4 CW Webnovel Identity Context Hierarchy Actionability Audit

Date: 2026-03-31
Status: draft-live-run-pending
Confidence: 94% (final save and temp promotion blocked until the active `0_2` frontier run reaches terminal state)
Document Type: actionability audit
Canonical Path: `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-actionability-audit.md`
Temp Mirror Path: `(none - live run active)`
Baseline Commit: `170963d34d30d3076a57926c5d1ed250f13ec421`
Baseline Dirty Summary: `active 0_2 frontier-run logs/db/ui mutation in progress; 0_temp console scratch dirty`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `decisions/ui/log sinks continued advancing during audit; Stage 3 moved through ep4 and ep5 while this audit was written`
Track: system
Mode: live-merge actionability audit
Source Survey Docs:
- `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-parallel-bounded-survey.md`
- `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-lane1-prompt-topology-draft.md`
- `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-lane2-context-delta-draft.md`
- `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-lane3-stage2-stage3-upstream-draft.md`
- `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-lane4-runtime-symptom-taxonomy-draft.md`
Evidence Artifact:
- `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-actionability-evidence.json`

## 1. Findings

### Finding 1. Final execution promotion is still blocked by live-run state

The current `0_2` frontier run is still moving, so this topic cannot be closed as a final execution-ready queue item yet.

Evidence:
- `0_temp.txt:861-940` shows the run continuing through Stage 2 and Stage 3 during this audit.
- `projects/0_2/logs/session/decisions.jsonl:15` shows a Stage 3 `ep_num=5` PASS at `2026-03-31T10:31:01`.
- `docs/implementation/live-run-merge-survey-harness.md:45-80` forbids final SSOT conclusions and `docs/temp/` execution mirrors while the run is still active.

Impact:
- execution planning is justified
- final closure is not
- any execution doc created now must remain `draft-live-run-pending`

### Finding 2. The problem is not EP2-only; Stage 3 authority drift is still visible later in the same frontier run

The current run produced fresh Stage 3 evidence that the upstream seam remains active beyond the original EP2 case.

Evidence:
- `0_temp.txt:920-930`
  - Director notes for EP4 blueprint mention:
    - anonymous NPC naming instead of concrete expected NPCs
    - institution fact-lock violation: `강남센터` drifting to `강남 PB센터`
- `projects/0_2/logs/session/decisions.jsonl:14`
  - Stage 3 EP4 blueprint PASS still carries `quality_risk=true`
- `projects/0_2/logs/session/decisions.jsonl:15`
  - Stage 3 EP5 blueprint is still being generated in the same live session

Impact:
- this is not only a `CW first-pass` problem
- execution scope should remain `Stage 3 + Stage 4`, not `Stage 4 only`

### Finding 3. Additional broad survey is not required; bounded execution-seam survey is enough

The existing four-lane survey plus this audit already closes the main decision questions:

- `CW role conditioning is weak and analytically contaminated`
- `hard canon is present but physically scattered`
- `retry wins by narrow task framing, not by cleaner base prompt`
- `Stage 3 blueprint prose is actively contaminating Stage 4 input`
- `the current EP2 failure family is hard truth first, briefing register second`

What remained open was narrower:
- exact patch seams
- tranche order
- defer list

That bounded addendum is now closed with direct file/function anchors:
- `modules/domain/agents/chief_writer_prompts.py:93-205`
- `modules/domain/agents/chief_writer_context.py:177-272`
- `modules/domain/agents/chief_writer_context.py:494-523`
- `modules/domain/agents/chief_writer_context_packets.py:171-276`
- `modules/core/stage4_interview_round.py:2225-2305`
- `modules/core/stage4_interview_round.py:2824-2850`
- `config/prompts/ensemble.yaml:334-402`
- `modules/domain/agents/blueprint_ensemble.py:649-748`
- `modules/domain/agents/blueprint_ensemble.py:1123-1142`
- `modules/core/stage4_interview_round.py:929-943`

### Finding 4. The smallest safe remediation wave is three action tranches plus one post-run gate

Recommended bounded wave:

1. `Stage 4 writer identity / anti-briefing hardening`
2. `Stage 4 hierarchy separation and advisory echo containment`
3. `Stage 3 blueprint anti-contamination hardening`
4. `post-run merge audit + fresh Stage3->Stage4 rerun validation`

This is smaller and safer than:
- detector-family redesign
- Stage 2 tactical-doc rewrite
- model/provider tier changes
- broad truth-gate taxonomy work

### Finding 5. Detector work should defer unless the rerun still shows pure briefing-style misses

The current evidence does not justify making `anti-meta detector` work part of the first remediation tranche.

Reason:
- the blocking EP2 defect is still hard truth conflict first
- Stage 3 and Stage 4 contract/prompt cleanup have higher ROI
- a detector wave before prompt/input cleanup risks measuring contamination that the system itself is still injecting

Defer list:
- dedicated anti-meta / recap-register detector
- Flashback family relabeling
- Stage 2 tactical-doc specificity rewrite
- model-tier changes
- broad post-select taxonomy rewrite

## 2. Bounded Addendum Survey

### Stage 4 exact patch seams

#### Seam A. Writer identity and anti-briefing contract

Primary site:
- `modules/domain/agents/chief_writer_prompts.py:93-205`
- `modules/core/stage4_interview_round.py:2225-2305`
- `modules/core/stage4_interview_round.py:2824-2850`

Why:
- top-of-prompt role/task framing is too thin
- analytical blocks dominate before the strongest writing rules land

Patch shape:
- strengthen the top identity contract
- add explicit anti-briefing / anti-recap / anti-report negative rules
- keep existing authority preface, but make writer-role and register constraints stronger than current single-line framing
- keep Stage 4 ingress ordering deterministic so `mandatory_context` and `preflight_advisory` do not accidentally outrank the new writer contract

#### Seam B. Physical prompt hierarchy and advisory containment

Primary sites:
- `modules/domain/agents/chief_writer_prompts.py:104-205`
- `modules/domain/agents/chief_writer_context.py:274-324`
- `modules/domain/agents/chief_writer_context.py:494-523`
- `modules/core/stage4_interview_round.py:929-943`

Why:
- hard canon is scattered
- `writer_core_section` mixes hard canon and soft guidance
- `integrated_scenario_advisory` is demoted for authority, but not for stylistic echo

Patch shape:
- split `writer_core_section` into hard-canon and soft-guidance subsections
- physically group hard canon earlier in the prompt
- harden the advisory wrapper so CW is told not to echo episode-reference / HUD / system-register prose from advisory text
- keep Stage 4 consumer-side containment ahead of broader Stage 3 changes for the safest first patch

#### Seam C. Carryover / prior-truth salience

Primary site:
- `modules/domain/agents/chief_writer_context_packets.py:171-276`

Why:
- prior manuscript truth exists, but is framed mainly as contradiction-prevention evidence
- a compact earlier truth reminder is still useful even when full-text prior manuscripts remain in the prompt

Patch shape:
- keep full prior-manuscript section
- preserve existing carryover ceiling
- use bounded compact prior-truth reminder placement as part of hierarchy cleanup rather than inventing a new large substrate

### Stage 3 exact patch seams

#### Seam D. Blueprint prompt anti-contamination contract

Primary site:
- `config/prompts/ensemble.yaml:334-402`
- `modules/domain/agents/blueprint_ensemble.py:649-748`

Why:
- `integrated_scenario` asks for long prose, but does not forbid:
  - briefing prose
  - episode-reference carryover language
  - HUD/system/game terms
  - cross-genre contamination in structured scene contract text

Patch shape:
- add negative instructions for:
  - recap/report language
  - HUD/status-window/system terminology unless canonically established
  - cross-genre contamination in `scene_breakdown.key_events`
- state the downstream consumer explicitly: this prose will guide a scene-writing agent, so it must be scene-authoritative, not planning prose

#### Seam E. Previous-blueprint contamination feed

Primary site:
- `modules/domain/agents/blueprint_ensemble.py:1123-1142`

Why:
- raw previous `integrated_scenario` prose is re-fed as `[시나리오] ...`
- this can compound contaminated register across episodes

Patch shape:
- stop feeding raw previous long-form scenario prose verbatim
- replace it with compact structured carryover or selected safe fields only
- if needed, add bounded post-parse contamination rejection before selection rather than opening a broad validator wave first

#### Seam F. Stage 4 writer-facing blueprint minimization

Primary site:
- `modules/core/stage4_interview_round.py:929-943`

Why:
- `integrated_scenario` is already demoted to advisory, which is correct
- but current minimization does not solve contaminated structured key-events

Patch shape:
- keep demotion behavior
- do not overexpand runtime sanitization in this first wave
- rely primarily on Stage 3 prompt/feed correction, with only bounded advisory echo warnings on the Stage 4 side

## 3. Execution Decision

Execution is justified now, but only as a `draft-live-run-pending` SSOT.

Reason:
- the remediation seams are closed enough to plan safely
- the live frontier run is still active, so final queue promotion and `docs/temp/` mirroring must wait

## 4. Open Questions

None that block execution drafting.

Remaining open items are post-remediation validation questions, not pre-execution research blockers.

## 5. Save Gate

This audit is intentionally saved as `draft-live-run-pending`.

Upgrade condition:
- wait for the current `0_2` frontier run to reach terminal state
- run post-run merge audit against completed Stage 3/4 evidence
- then re-audit this topic and promote the execution doc from draft to canonical execution-ready status
