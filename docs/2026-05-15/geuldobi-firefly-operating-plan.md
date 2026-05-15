# Geuldobi / Firefly Operating Plan

Date: 2026-05-15
Status: active
Document Type: operating plan
Canonical Path: `docs/2026-05-15/geuldobi-firefly-operating-plan.md`
Track: ClickUp companion planning for Geuldobi and Firefly

## 1. Purpose

This document is the planning body for the Geuldobi and Firefly work surfaces.

ClickUp should stay shallow:

- show the current execution cards
- show weekly review cards
- point back to this document when context is needed

This document should carry the deeper operating logic:

- current reality
- track separation
- readiness gates
- weekly WBS
- what not to judge yet

Repo-specific development units live in GitHub Issues. ClickUp cards should mirror only the issues that need to stay visible in the human operating board.

## 2. Current Reality

The current plan is not a direct production push.

Geuldobi needs more system-development time before production candidates can be judged cleanly. If a candidate is judged too early, the result may mix three different failures:

- the work candidate is weak
- the system cannot evaluate the candidate reliably yet
- the operating surface is asking for a decision before evidence exists

Firefly is also in a system-improvement phase. Its short-term target is not "six-work survival judgment." The short-term target is to define what evidence would make that judgment meaningful.

## 3. Track Split

### Geuldobi

Geuldobi means the main system and production pipeline.

Current focus:

- system blocker identification
- production-restart readiness
- Phase0 / work_guard / TR / BI path clarity
- smoke or dry run evidence contract

Do not treat candidate survival as the first-order goal.

### Firefly

Firefly means the `글도비_파이어플라이` lane.

Current focus:

- yellow reason inventory
- green gate definition
- judgment rubric before actual judgment
- minimum smoke or dry run condition

Do not force six-work survival judgment before the green gate is defined.

## 4. ClickUp Surface

Target ClickUp lists are intentionally few:

- `00 · 인박스`
- `10 · 글도비 · 현재 실행`
- `20 · 파이어플라이 · 현재 실행`
- `30 · 통합 · 주간 리뷰`
- `90 · 자료 · 생산/판정 현황`

Detailed planning lists are not the long-term target. If they exist during setup, they should be considered temporary scaffolding or archived context.

The `90 · 자료 · 생산/판정 현황` list is a reference surface. It is not an execution queue and does not authorize production or survival judgment by itself.

Implementation authority:

- GitHub Issues are the repo-side development units.
- ClickUp cards with `GH · repo#number` are mirror cards, not the source of implementation truth.
- A ClickUp mirror card should link to exactly one GitHub Issue.
- For GitHub activity attachment, include `#<ClickUp task id>` in PR title/body and commit messages.

## 5. Active Execution Cards

### Geuldobi Current Execution

Keep only the next few cards visible:

- `GH · devdev#154 · 시스템 blocker 3개 선정`
- `GH · devdev#155 · 생산 재개 readiness gate`
- `GH · devdev#156 · smoke/dry evidence contract`

### Firefly Current Execution

Keep only the next few cards visible:

- `GH · firefly#14 · yellow 원인 정리`
- `GH · firefly#15 · green gate 정의`
- `GH · firefly#16 · 6작품 판정 기준표`
- `GH · firefly#17 · 최소 smoke/dry run 조건`

### Integrated Weekly Review

Keep one weekly review card visible:

- `주간 리뷰 · 글도비/FF 다음 행동 갱신`
- `GH · Daycare#1 · GitHub→ClickUp trace proof`

Trace proof note:

- `Daycare` PR #2 attached to ClickUp task `86exm7y8f` after `#86exm7y8f` was added to the PR and commit signal.
- GitHub-to-ClickUp attachment is proven.
- Mobile push notification remains phone-side confirmation.

### Consolidated Reference Surface

Keep material and status references in one list:

- `90 · 자료 · 생산/판정 현황`

Do not split Firefly production status and Firefly development status into separate active lists unless each becomes a recurring operational surface.

## 6. Readiness Gates

### Production Restart Gate

Production restart is not ready until:

- system blockers are named and bounded
- candidate readiness is separated from candidate quality
- a smoke or dry run can produce readable evidence
- ClickUp remains a companion surface, not the SSOT

### Firefly Green Gate

Firefly is not green until:

- yellow reasons are listed
- green conditions are reduced to three to five checks
- the six-work judgment rubric exists
- a failed run can be classified as system, material, or operating failure

## 7. Weekly WBS

### 2026-05 W3

Goal: stabilize the planning surface.

Done when:

- ClickUp lists are reduced to current-execution surfaces
- this document becomes the planning body
- old detailed planning surfaces are archived or treated as setup scaffolding

### 2026-05 W4

Goal: define judgment prerequisites.

Geuldobi:

- select three system blockers
- define production-restart readiness

Firefly:

- list yellow reasons
- draft green gate
- draft six-work judgment rubric

### 2026-05 W5

Goal: define the minimum proof run.

Geuldobi:

- smoke/dry run evidence contract
- GitHub-to-ClickUp development trace on one real task

Firefly:

- minimum smoke/dry run condition
- separate failure classes

### 2026-06 W1

Goal: review whether either lane is ready for a controlled run.

Done when:

- next Geuldobi action is one line
- next Firefly action is one line
- any production or survival judgment remains explicitly blocked unless gates passed

## 8. Non-Goals

Do not do these yet:

- force a selected anchor
- force six-work survival judgment
- treat ClickUp as the source of technical truth
- split every planning thought into a separate ClickUp list
- duplicate every GitHub Issue into ClickUp
- start production before readiness gates pass

## 9. 3-Pass Audit

Pass 1. Scope:

- The document is a ClickUp companion operating plan, not a canonical technical verdict.
- It separates Geuldobi main-system work from Firefly work.

Pass 2. Evidence:

- The plan reflects the current ClickUp state after list cleanup and the user's correction that both lanes are system-improvement-bound.
- It preserves the repo-side SSOT rule: GitHub Issues and repo docs carry implementation truth; ClickUp is a human-facing execution surface only.
- It reflects the migration of active development cards to GitHub Issue mirror cards.
- It records the trace-proof rule that `#<ClickUp task id>` is the reliable GitHub signal format.

Pass 3. Closure:

- The plan reduces ClickUp list pressure.
- It makes production judgment explicitly conditional on readiness gates.
- It gives a near-term weekly WBS without pretending that production is immediately ready.

Estimated Confidence: 98%
