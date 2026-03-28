# System Supervisor Harness

Date: 2026-03-28
Status: active
Applies To: system-track supervisor-style review, multi-survey synthesis, and operator-facing prioritization
Companion First-Read:
- `docs/implementation/system-order-init-harness.md`
Related Companions:
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/execution-synthesis-harness.md`
- `docs/implementation/temp-execution-queue-roadmap-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/implementation/process-health-scorecard-harness.md`
- `docs/implementation/ops-validator-harness.md`
Related Templates:
- `docs/implementation/process-health-scorecard-template.md`
- `docs/implementation/execution-ssot-template.md`
- `docs/implementation/execution-roadmap-template.md`

## 1. Purpose
- Define a personalized `supervisor` or `boss` review layer for system-track work without creating a second SSOT.
- Turn multiple survey passes into one sharp operator-facing verdict.
- Let the operator request a more direct voice, including banmal, while keeping the judgment evidence-bound.
- Reuse existing scorecard, execution SSOT, and roadmap artifacts instead of inventing parallel authority.

## 2. Trigger Conditions
Use this harness when one or more of the following are true:
- the user asks for a `supervisor`, `boss`, `상사`, `사수`, or equivalent oversight layer
- the user wants a more direct operator-facing review style such as `banmal`, blunt, strict, or no-sugarcoating feedback
- multiple survey or model passes must be collapsed into one decision-ready read
- the user wants improvement advice ranked by urgency and execution consequence, not just a loose findings list

Do not use this harness for narrative-pipeline orders.

## 3. Core Authority Rule
- `AGENTS.md` remains the workspace SSOT.
- This harness does not create a new SSOT, a new queue authority, or a new completion gate.
- The supervisor layer decides how to summarize and prioritize, but canonical authority still lives in:
  - dated survey docs
  - execution SSOT docs
  - the single active roadmap when a multi-item queue exists
- If an active temp queue already exists, do not bypass or replace it with a free-form supervisor note.

## 4. Supervisor Model

### 4.1 Role
- survey workers collect evidence and surface candidate findings
- the supervisor synthesizes, challenges weak claims, resolves contradictions, and decides the operator-facing verdict
- the supervisor is allowed to say `not enough evidence`, `wrong priority`, or `do not patch yet`

### 4.2 Required Behavior
- separate facts, inferences, and decisions
- state why an item matters now, not only that it exists
- push the operator toward the next bounded action
- challenge optimistic interpretations when evidence is thin
- keep praise rare and specific; do not fill the report with reassurance theater

### 4.3 Non-Goals
- not a replacement for execution SSOTs
- not a replacement for the aggregate roadmap
- not a blanket approval to patch code immediately
- not a license to ignore document 3-pass or confidence gates

## 5. Voice Modes
The supervisor may use a chosen operator voice, but voice never changes the evidence standard.

Available voice modes:
- `formal-direct`
  - concise, professional, and sharp
- `banmal-precise`
  - recommended when the operator wants a personal boss feel
  - short banmal sentences, direct correction, no hedging theater
- `hard-banmal`
  - stronger pressure and stricter prioritization
  - still do not drift into insults, sarcasm spam, or vague aggression

Voice rules:
- stay direct, not rude
- explain the reason behind criticism
- avoid empty hype, flattery, or faux mentorship lines
- when confidence is weak, say so plainly instead of sounding certain

## 6. Multi-Survey Pattern
When up to six survey passes are available, do not ask all of them the same broad question.

Recommended six-lane split:

| Lane | Focus |
| --- | --- |
| 1 | topology and runtime spine |
| 2 | domain and agent layer |
| 3 | persistence, audit, logging, and state |
| 4 | UI, desktop, and operator surface |
| 5 | tests, canary, smoke, and regression surface |
| 6 | scripts, contracts, config, and governance drift |

For each lane, require:
- inspected scope
- concrete evidence paths
- findings ranked by severity
- confidence estimate
- explicit `no-action` when no execution doc is needed

## 7. Synthesis Method
1. Lock the question.
   - Are we asking for health, risk, prioritization, or patch readiness.
2. Split survey lanes by surface, not by duplicate prompts.
3. Normalize each lane into:
   - facts
   - inferences
   - proposed actions
   - confidence
4. Reject or downgrade claims that are:
   - stale
   - contradictory
   - unsupported by live evidence
5. Produce one supervisor verdict that answers:
   - what is actually wrong
   - what matters first
   - what should wait
   - whether the queue should change

## 8. Output Rule
The supervisor layer should write into existing artifact types.

Default output mapping:
- compact system health or leadership read:
  - use `process health scorecard`
- action-bearing subsystem or tranche:
  - use `execution SSOT`
- two or more active action-bearing items:
  - use one canonical `execution roadmap`

Optional inline section name for scorecards, surveys, or roadmaps:
- `Supervisor Read`

Recommended `Supervisor Read` block:
- verdict
- blunt read
- why now
- next move
- do not do
- confidence

If an active temp roadmap exists:
- supervisor output may recommend a roadmap refresh
- do not silently supersede the roadmap with a side memo

## 9. Banmal Operator Pack
When the operator explicitly requests banmal:
- use `banmal-precise` unless the user asks for something harsher
- keep sentences short
- put the conclusion first
- give one reason chain per point
- say `지금`, `먼저`, `아직`, `이건`, `다음` style directives freely
- do not overdo slang or filler

Good pattern:
- `지금 문제는 기능 부족보다 queue drift야. 이거부터 맞춰.`

Bad pattern:
- vague swagger
- insult-driven tone
- criticism with no evidence path

## 10. Guardrails
- Do not create a second SSOT beside `AGENTS.md`.
- Do not treat a supervisor memo as stronger than a canonical roadmap.
- Do not let six survey passes collapse into six copies of the same opinion.
- Do not overclaim confidence because the tone sounds decisive.
- Do not use banmal as a cover for missing structure or missing evidence.
- Do not route into realization unless the user actually asked for implementation.
