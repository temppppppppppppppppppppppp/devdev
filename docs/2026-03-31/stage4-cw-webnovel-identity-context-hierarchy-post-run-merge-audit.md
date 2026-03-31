# Stage4 CW Webnovel Identity Context Hierarchy Post-Run Merge Audit

Date: 2026-03-31
Status: final (3-pass audited)
Confidence: 96%
Document Type: post-run merge audit
Canonical Path: `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-post-run-merge-audit.md`
Temp Mirror Path: `(none - audit doc only)`
Baseline Commit: `170963d34d30d3076a57926c5d1ed250f13ec421`
Baseline Dirty Summary: `0_2 frontier-run logs/db/ui mutation had been active during survey drafting`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `run was operator-aborted mid frontier; no later Stage4 continuation evidence beyond the already collected EP2 runtime cluster`
Track: system
Mode: live-merge -> post-run merge
Source Draft Docs:
- `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-parallel-bounded-survey.md`
- `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-actionability-audit.md`
- `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-remediation-execution-ssot.md`
Evidence Artifacts:
- `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-parallel-evidence.json`
- `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-actionability-evidence.json`
- `projects/0_2/logs/session/decisions.jsonl`
- `projects/0_2/logs/artifacts/stage4/ep_0002/attempt_01/patched_blueprint_after_fix__V75-D_blueprint_inplace.json`
- `projects/0_2/logs/artifacts/stage4/ep_0002/attempt_02/selected_before_fix__A.txt`
- `projects/0_2/drafts/ep_0001.txt`
- `0_temp.txt`

## 1. Answer-First

The run stop does not materially change the diagnosis.

The merged conclusion is now stable enough for execution:

1. `CW first-pass failure` is primarily a `hierarchy/conditioning/input-shape` problem, not a clean “CW or model tier is bad” problem.
2. `Stage 4 prompt hierarchy` is real debt:
   - writer identity is too thin
   - hard canon is scattered
   - analytical/HUD/advisory blocks dominate the prompt surface
3. `Stage 3 blueprint contamination` is also real and still visible later in the same frontier run:
   - EP2 carried HUD/status-window and recap contamination
   - EP4 still showed authority drift such as anonymous NPC treatment and institution fact-lock drift
4. `retry success` is mostly evidence that explicit conflict framing rescues the task, not evidence that the base first-pass prompt is healthy.
5. Additional broad survey is unnecessary. A bounded remediation wave is justified now.

## 2. Terminal-State Handling

Run classification:
- `aborted by operator`

Why this still supports execution planning:
- the objective of this live-merge cycle was to validate whether the draft diagnosis survived contact with a real run
- enough real-run evidence was already captured before the stop
- the stop happened after the critical EP2 Stage 4 symptom cluster and after additional Stage 3 authority-drift evidence appeared at EP4

What the stop does prevent:
- claiming remediation effectiveness
- claiming runtime closure
- claiming reduced retry counts after a fix

What the stop does not prevent:
- finalizing the diagnosis
- finalizing an execution-ready remediation SSOT

## 3. Merged Findings

### Finding 1. Stage 4 hierarchy debt is confirmed

Primary anchors:
- `modules/domain/agents/chief_writer_prompts.py:93-205`
- `modules/domain/agents/chief_writer_context.py:177-272`
- `modules/domain/agents/chief_writer_context.py:494-523`
- `modules/domain/agents/chief_writer_context_packets.py:171-276`

Merged conclusion:
- the system gives CW enough information, but not in a clean authority stack
- role conditioning is weak
- prior truth is present but not salient enough
- advisory/report/dashboard register is too prominent

### Finding 2. Stage 3 contamination is confirmed

Primary anchors:
- `projects/0_2/logs/artifacts/stage4/ep_0002/attempt_01/patched_blueprint_after_fix__V75-D_blueprint_inplace.json:59`
- `projects/0_2/logs/artifacts/stage4/ep_0002/attempt_01/patched_blueprint_after_fix__V75-D_blueprint_inplace.json:95-101`
- `0_temp.txt:920-930`
- `projects/0_2/logs/session/decisions.jsonl:14-15`

Merged conclusion:
- Stage 3 is not just handing off neutral scene authority
- it is still capable of injecting briefing/system/fact-lock drift into Stage 4 input
- execution scope must therefore include Stage 3, not only Stage 4

### Finding 3. EP2 symptom family remains mixed, with truth conflict primary

Primary anchors:
- `projects/0_2/logs/artifacts/stage4/ep_0002/attempt_02/selected_before_fix__A.txt:19-25`
- `projects/0_2/drafts/ep_0001.txt:91-97`
- `projects/0_2/logs/session/decisions.jsonl:8-10`

Merged conclusion:
- the aesthetically bad recap/register problem is real
- but the blocking defect in the observed EP2 failure is still:
  - fabricated status window
  - wrong asset truth

This means:
- prompt/input cleanup is the first wave
- detector redesign is defer

### Finding 4. The stop does not create a new contradictory signal

No late evidence emerged that reverses the draft thesis.

The later live-run evidence that did appear before stop was consistent with the draft:
- Stage 3 authority drift remained visible
- no evidence appeared that the issue was actually model-tier or Stage 2-primary

## 4. Final Execution Decision

Execution is warranted now.

Recommended bounded remediation wave:

1. Stage 4 writer identity / anti-briefing hardening
2. Stage 4 hierarchy separation and consumer-side containment
3. Stage 3 centralized sanitation and previous-blueprint feed cleanup
4. Stage 3 prompt hardening
5. fresh post-patch rerun validation

## 5. Defer Ledger

Still deferred:
- dedicated anti-meta / recap-register detector
- Flashback family relabeling
- Stage 2 tactical specificity rewrite
- model/provider tier changes
- broad taxonomy or post-select redesign

## 6. Promotion Result

This audit upgrades the topic from:
- `draft-live-run-pending`

to:
- `execution-ready remediation planning`

Canonical execution SSOT should now be treated as queue-eligible and may be mirrored into `docs/temp/`.
