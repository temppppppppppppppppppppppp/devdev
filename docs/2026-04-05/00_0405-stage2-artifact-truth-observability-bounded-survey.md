# 00_0405 Stage2 Artifact Truth And Observability Bounded Survey

Date: 2026-04-05
Status: final
Canonical Path: `docs/2026-04-05/00_0405-stage2-artifact-truth-observability-bounded-survey.md`
Source Docs:
- `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`
Evidence Artifacts:
- `docs/2026-04-05/00_0405-stage2-artifact-truth-observability-evidence.json`
- `tttt.txt`
- `projects/00_0405/plans/arcs/arc_001.txt`
- `projects/00_0405/plans/arcs/arc_002.txt`
- `projects/00_0405/plans/arcs/arc_003.txt`
- `projects/00_0405/plans/arcs/arc_004.txt`
- `projects/00_0405/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json`
- `projects/00_0405/logs/artifacts/stage2/arc_004/attempt_01/final_arc__balanced.json`
- `projects/00_0405/logs/runtime_audit.jsonl`
- `projects/00_0405/logs/session/ui_events.jsonl`
- `projects/00_0405/logs/quality_metrics.jsonl`
Confidence: `96%`
3-Pass Audit: `completed`

## 1. Answer First

`00_0405` Stage2 is not a content-collapse case.

- all four arcs passed Director
- the numeric/business spine is broadly coherent
- but the human-readable arc txt and the selected Stage2 artifact do not always round-trip to the same state truth
- key Stage2 judgment and correction evidence is still hidden in downstream sinks instead of the operator console

So the correct reading is:

- `Stage2 passed, but artifact truth packaging and observability remain weak`

and not:

- `Stage2 failed`
- `Stage1 bypass alone explains the issue`

For this survey, `Stage1 bypass` is intentionally not treated as the defect because the declared operating direction is gradual Stage1 retirement.

## 2. Scope

Included:

- `00_0405` Stage2 human-readable arc txt truth
- selected Stage2 artifact JSON truth where the carryover packet can be inspected
- runtime audit, UI event, and quality metrics sinks for observability mapping
- queue alignment against the current parked Stage2 execution docs

Excluded:

- new code patching
- Stage3 or Stage4 reopen
- execution SSOT promotion
- closure claims

## 3. Artifact Truth Findings

### 3.1 Arc2 and Arc3 do not fully round-trip the same location truth

The strongest concrete mismatch is the `arc2 -> arc3` boundary.

- `arc_002.txt` ends in the Yeouido SOHO office
- the selected Stage2 artifact for arc 2 already ends in the Gangnam representative office
- `arc_003.txt` starts in the Gangnam representative office

This means the selected Stage2 packet moved the protagonist and office state before the final txt artifact fully reflected that move.

This is not a numeric contradiction. It is an `artifact round-trip inconsistency`.

### 3.2 Arc4 start-state items still show packet/txt divergence

The selected Stage2 artifact for arc 4 still carries the Ecuador memo at start-state, while the human-readable `arc_004.txt` start-state item list does not.

That matters because it shows the same class of issue in a different field family:

- selected artifact packet truth survives
- final txt truth drops part of that packet

This is exactly the kind of keep-drop normalization weakness described by the parked Stage2 contract wave.

### 3.3 Numeric state is comparatively healthier than packet packaging

The strongest counter-signal is that the business-state spine is mostly coherent:

- Arc 1 secures about `2.0B KRW`
- Arc 2 selected artifact lands around `2.3B KRW`
- Arc 3 txt lands at `3.0B KRW`
- Arc 4 txt lands at `4.5B KRW`

So the immediate Stage2 story is not `broken business progression`.

It is `acceptable business progression with weak artifact packet round-trip`.

## 4. Observability Findings

### 4.1 Console shows sync effects, but not the real auto-correct reasons

The operator-visible UI log does show:

- deterministic inventory carryover
- equipment sync
- state sync

But the actual correction reasons remain in `runtime_audit.jsonl`.

That hidden layer contains the higher-signal truth:

- genre-field removal such as `internal_energy`
- `[PATCH-B]` item disappearance repair
- tactical-doc wording normalization
- location rewrites

So the current console view shows that something was synchronized, but not why the system had to repair the arc in the first place.

### 4.2 Retrieval coverage weakness is practically invisible from the console

`quality_metrics.jsonl` shows that Stage2 retrieval/context coverage was effectively empty across the run:

- `work_focus_present=false`
- `tracking_slots_count=0`
- `scene_engines_count=0`
- `vector_context_chars=0`
- `mandatory_context_chars=0`

That is a meaningful Stage2 runtime fact, but it is not surfaced through the operator console in a usable way.

### 4.3 The sink split explains the operator discomfort

The current split is:

- `ui_events.jsonl`: best-effort operator telemetry
- `runtime_audit.jsonl`: audit-only correction trail
- `quality_metrics.jsonl`: retrieval / coverage truth

This architecture is not inherently wrong, but it is weak for live operator understanding because the highest-signal Stage2 reasons are fragmented across three sinks.

## 5. Merged Reading

The merged reading is:

- `00_0405` Stage2 passed Director and produced broadly usable arcs
- the first visible problem is not narrative collapse but `artifact packet to txt round-trip drift`
- the second visible problem is `observability weakness`: the operator console hides the strongest Stage2 evidence

This matches the existing parked Stage2 execution lane much better than a new `Stage2 content failure` interpretation.

The best queue-aligned label is still:

- `Stage2 content-sufficient but schema-fragile`

not:

- `Stage2 as the primary active blocker`

## 6. Owner Lanes

If this survey is later promoted into realization, the likely owners are:

- Stage2 artifact emission / packet round-trip owners around Stage2 arc artifact production
- Stage2 validation and post-process owners that emit audit-only auto-correct detail
- Stage2 preflight / retrieval observation owners
- operator console mirroring for high-signal Stage2 audit facts

The strongest current file-level owners from this survey are:

- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage2_preflight.py`
- `modules/core/quality_dashboard.py`
- `modules/core/services/audit_service.py`
- `modules/core/session_logger.py`

## 7. Queue Position

This survey does not justify immediate Stage2 execution promotion above the active Stage4 queue.

It does justify:

- preserving `Stage2 contract normalization` as a real future wave
- carrying forward `artifact truth + observability` as the concrete Stage2 problem statement

That is consistent with the current roadmap and Stage2 execution SSOT:

- Stage2 remains a parked upstream wave
- the active queue is still Stage4-first
- but the Stage2 debt is now better specified with fresh `00_0405` evidence

## 8. 3-Pass Audit Note

Pass 1:

- checked `tttt.txt`, arc txt files, selected Stage2 artifact JSON, runtime audit, UI events, and quality metrics for direct evidence

Pass 2:

- re-checked whether the observed issue was really Stage1 bypass, Stage2 content failure, or Stage2 packet/observability debt
- rejected the first two readings

Pass 3:

- aligned the findings against the current Stage2 execution SSOT and active roadmap
- confirmed the queue-safe reading is `parked Stage2 contract/readiness debt`, not active blocker promotion
