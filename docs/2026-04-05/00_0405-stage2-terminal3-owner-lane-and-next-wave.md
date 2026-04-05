# 00_0405 Stage2 Terminal 3: Owner Lane and Next Wave

Date: 2026-04-05
Status: final
Document Type: terminal survey output
Canonical Path: `docs/2026-04-05/00_0405-stage2-terminal3-owner-lane-and-next-wave.md`
Track: system
Mode: read-only terminal survey; no code patching; docs-only output
Parent Order: `docs/2026-04-05/00_0405-stage2-three-terminal-parallel-survey-order.md`
Evidence Source: `docs/2026-04-05/00_0405-stage2-artifact-truth-observability-evidence.json`
Survey Source: `docs/2026-04-05/00_0405-stage2-artifact-truth-observability-bounded-survey.md`
Confidence: `96%`

## 1. Coverage

Inputs consumed:

- `AGENTS.md` (workspace SSOT, queue governance, complexity guardrails)
- `docs/2026-04-05/00_0405-stage2-artifact-truth-observability-bounded-survey.md` (merged survey reading)
- `docs/2026-04-05/00_0405-stage2-artifact-truth-observability-evidence.json` (line-level evidence)
- `docs/2026-04-05/00_0405-stage2-three-terminal-parallel-survey-order.md` (terminal assignment and questions)
- `docs/temp/0_0-stage2-contract-normalization-remediation-execution-ssot.md` (parked Stage2 contract lane)
- `docs/temp/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md` (blocked parent lane)
- `docs/temp/execution-roadmap.md` (active queue with 16 items)

Questions addressed:

1. Which parked Stage2 lane best matches the observed debt?
2. Which owner file group should absorb the eventual bounded realization wave?
3. What is the smallest queue-safe next wave after this survey stack?
4. Why should this stop at survey/proposal rather than immediate realization?

## 2. Findings

### 2.1 This evidence lands on `0_0-stage2-contract-normalization-remediation` (roadmap priority 12)

The `00_0405` evidence splits into two families. Both converge on the same parked lane.

**Family A: artifact round-trip drift**

- arc2 txt ends in Yeouido SOHO; selected Stage2 artifact already moved to Gangnam representative office
- arc4 selected artifact carries Ecuador memo at start-state; arc4 txt does not

These are exactly the `keep-or-drop normalization weakness` and `packet-to-txt round-trip inconsistency` that the existing `0_0-stage2-contract-normalization-remediation` SSOT §3.3 and §4.1 describe:

> mission truth trapped in `tactical_doc` prose; Stage2-owned fields without explicit keep-or-drop policy

The location drift is a packet extraction problem: the selected artifact packet updates state before the final human-readable txt reflects it. The item drift is a keep-drop problem: the packet retains the Ecuador memo but the txt drops it without explicit policy.

This is not a new lane. It is fresh evidence for an already-declared parked lane.

**Family B: observability weakness**

- auto-correct reasons (genre-field removal, `[PATCH-B]` repair, location rewrite) visible only in `runtime_audit.jsonl`, not operator console
- retrieval coverage emptiness (`work_focus_present=false`, `vector_context_chars=0`) visible only in `quality_metrics.jsonl`, not console
- three-sink fragmentation (`ui_events`, `runtime_audit`, `quality_metrics`) leaves the strongest Stage2 reasons audit-only

This observability weakness is secondary to artifact truth in the current evidence, but it shares the same owner boundary: the Stage2 emission and validation surfaces that decide what reaches the operator versus what stays audit-only.

The observability finding also touches `0_0-stage234-cross-stage-contract-normalization-remediation` (roadmap priority 9, parked) because the sink fragmentation is a cross-stage operator-visibility debt. But the primary owner for the `00_0405` evidence is the Stage2-scoped contract lane, not the broader cross-stage substrate.

**Lane match verdict:**

| Evidence family | Best-match parked lane | Roadmap position |
| --- | --- | --- |
| artifact round-trip drift | `0_0-stage2-contract-normalization-remediation` | priority 12 |
| observability weakness | `0_0-stage2-contract-normalization-remediation` (primary) / `0_0-stage234-cross-stage-contract-normalization-remediation` (secondary) | priority 12 / priority 9 |

Neither family justifies a new execution lane. Both enrich the existing parked lane's problem statement.

### 2.2 The eventual bounded realization wave owns two file groups

**Group 1: artifact truth / packet round-trip (contract normalization scope)**

These files own Stage2 packet production and the emission boundary where txt and selected artifact diverge:

- `modules/domain/agents/arc_ensemble.py` — Stage2 arc packet production and `tactical_doc` emission
- `config/prompts/ensemble.yaml` — Stage2 prompt configuration and field authority

These are the files already identified in the parked `0_0-stage2-contract-normalization-remediation` SSOT §3 scope.

**Group 2: observability / console mirror (observability scope)**

These files own the Stage2 audit trail and the operator-visibility gap:

- `modules/core/stage2_validation_pipeline.py` — auto-correct patch emission, audit-only correction trail
- `modules/core/stage2_preflight.py` — retrieval observation, preflight coverage metrics
- `modules/core/quality_dashboard.py` — quality metrics sink, retrieval coverage persistence
- `modules/core/services/audit_service.py` — audit event routing, `runtime_audit.jsonl` writer
- `modules/core/session_logger.py` — UI event telemetry, operator console feed

These are the files identified in the `00_0405` bounded survey §6 as the strongest file-level owners.

**Combined owner file bundle for the eventual realization wave:**

| File | Role | Evidence family |
| --- | --- | --- |
| `modules/domain/agents/arc_ensemble.py` | packet production, tactical_doc emission | artifact truth |
| `config/prompts/ensemble.yaml` | prompt field authority | artifact truth |
| `modules/core/stage2_validation_pipeline.py` | auto-correct audit trail | observability |
| `modules/core/stage2_preflight.py` | retrieval coverage observation | observability |
| `modules/core/quality_dashboard.py` | quality metrics sink | observability |
| `modules/core/services/audit_service.py` | audit event routing | observability |
| `modules/core/session_logger.py` | UI event telemetry | observability |

### 2.3 The queue-safe next wave is evidence enrichment, not realization

The smallest queue-safe next action after this survey stack completes is:

> Append the `00_0405` artifact-truth and observability evidence as a new section to the canonical `0_0-stage2-contract-normalization-remediation` execution SSOT, without changing its `parked` status, without changing its roadmap priority 12 position, and without activating any realization tranche.

Concretely this means:

1. **Evidence appendix to the canonical SSOT** — add a dated section referencing the `00_0405` survey doc and evidence JSON as fresh backing for the parked lane's §4 inventory and §7 realization architecture
2. **Owner file group update** — add the five observability files to the parked SSOT's scope as a secondary file group, alongside the existing `arc_ensemble.py` and `ensemble.yaml` primary scope
3. **No temp queue mutation** — the `docs/temp/` mirror is not touched in this wave; it receives the enrichment only when the canonical is updated in a later dedicated pass
4. **No priority change** — the lane stays at roadmap priority 12, below active Stage4 (1-8), below cross-stage substrate (9), below Stage3 future waves (10-11)
5. **No realization** — no code patching, no canary, no tranche activation

This is expressible as a single future operator order:

```
Enrich the parked 0_0-stage2-contract-normalization-remediation execution SSOT
with 00_0405 artifact-truth and observability evidence.
Do not change parked status. Do not change roadmap priority.
Do not activate realization tranches.
Update canonical first, then mirror to docs/temp/ in a separate pass.
```

## 3. Non-Issues

- **Stage1 bypass**: not treated as the defect per the three-terminal order's fixed premise. Stage1 is on a declared gradual retirement path. The `00_0405` evidence does not change that reading.
- **Stage2 content collapse**: the survey already ruled this out. The business-state spine is coherent (2.0B → 2.3B → 3.0B → 4.5B KRW). The problem is packaging and observability, not missing narrative content.
- **Numeric contradiction**: the numeric spine is broadly healthy. The divergence is in location and item carryover packaging, not in the financial progression itself.
- **Active Stage4 queue disruption**: this survey creates no new execution pressure on the active Stage4 lanes (priorities 1-8). Stage2 stays parked.

## 4. Owner Verdict

The `00_0405` Stage2 evidence enriches the already-parked `0_0-stage2-contract-normalization-remediation` lane. It does not create a new lane, does not justify queue promotion, and does not displace any active Stage4 work.

The evidence sharpens the parked lane's problem statement from:

> Stage2 is content-sufficient but schema-fragile

to the more concrete:

> Stage2 is content-sufficient but packet-to-txt round-trip is inconsistent and the strongest Stage2 correction/retrieval evidence is hidden from the operator console

The observability family is a newly evidenced secondary dimension for this lane. When the lane is eventually reactivated, the realization architecture should include both:

- Tranche A (already declared): mission authority extraction + alias normalization + keep-drop cleanup
- Tranche B (new from `00_0405`): bounded console mirroring of high-signal auto-correct reasons and retrieval coverage facts

## 5. Minimal Next Wave

**Why this must stop at survey/proposal, not immediate realization:**

1. **Queue order**: the active roadmap has 8 items ahead of this lane. Priority 1 is the aggregate Stage4 consumer-contract wave. Priority 2 is the repair-contract grammar lane. The Stage2 contract lane sits at priority 12. Promoting it now would violate the queue-priority rubric and the three-terminal order's explicit guardrail: `do not promote Stage2 above the active Stage4 queue`.

2. **Parent lane still blocked**: `0_0-stage2-stage3-stage4-readiness-remediation` (priority 6) is blocked by unresolved Stage4 consumer-side numeric authority and repair-contract seams. Until those Stage4 seams clear, the parent lane cannot advance, and the child Stage2 lane has no operational path to realization.

3. **No new blocker evidence**: the `00_0405` findings are `enrichment`, not `escalation`. The artifact round-trip drift and observability weakness were already known categories from the 2026-04-02 survey. The new evidence is more concrete and line-level, but it does not change the severity classification from `parked future wave` to `active blocker`.

4. **Realization prerequisites not met**: the parked SSOT's §13 execution-start rule requires a fresh 3-pass audit at 95%+ confidence against the current workspace state before any code patching. That audit has not been performed against the post-`00_0405` evidence baseline. Running it now would consume the realization budget of a separate operator turn that is better spent on the active Stage4 front.

5. **Survey stack integrity**: this is terminal 3 of a read-only parallel survey. The three-terminal order's global guardrail §3.2 says `do not patch code in this wave`. Ending at survey/proposal preserves the integrity of the parallel survey architecture and lets the operator decide reactivation timing independently.

**Minimal next wave expression:**

```
When the operator is ready to enrich the parked Stage2 lane:

1. Update canonical docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md
   - Add §X: 00_0405 Evidence Appendix (artifact truth + observability)
   - Add Group 2 observability files to §3 scope
   - Keep status: parked
   - Keep roadmap position: priority 12

2. Mirror to docs/temp/ after canonical update

3. Do not activate realization tranches
4. Do not change roadmap order
5. Do not run canary from this lane
```

## 6. Stop

This terminal produced exactly one output file under `docs/2026-04-05/`.

No code was patched. No `docs/temp/` file was mutated. No Stage2 lane was promoted above active Stage4 queue items. Stage1 bypass was not treated as the defect.

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-05 output
