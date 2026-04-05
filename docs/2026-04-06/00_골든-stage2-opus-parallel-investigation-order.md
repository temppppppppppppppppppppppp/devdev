# 00_골든 Stage2 Opus Parallel Investigation Order

Date: 2026-04-06
Status: final
Mode: system-track, read-only bounded survey
Scope: latest Stage2 run in `projects/00_골든`
Authoritative session: `20260406_013527`

## Purpose

This order is for parallel Opus investigation of the latest Stage2 run for
`00_골든`.

This is not a new lane proposal.
This is not a Stage4 reprioritization.
This is a bounded investigation of the concrete Stage2 defects visible in the
latest run evidence.

## Fixed Premises

- Use the latest `00_골든` Stage2 run only.
- Treat these as authoritative sinks:
  - `projects/00_골든/logs/session/decisions.jsonl`
  - `projects/00_골든/logs/session/ui_events.jsonl`
  - `projects/00_골든/logs/runtime_audit.jsonl`
  - `projects/00_골든/logs/quality_metrics.jsonl`
  - `projects/00_골든/logs/artifacts/stage2/`
  - `projects/00_골든/plans/arcs/`
- Do not reopen `retrieval empty` as the primary issue unless the evidence
  directly contradicts current sinks.
- Do not propose a new Stage2 lane or queue promotion in this turn.
- Code edits are prohibited for this survey wave.
- `docs/temp/` mutation is prohibited.

## Current Stage2 Verdict Snapshot

- Arc 1: PASS 100
- Arc 2: PASS 90
- Arc 3: PASS_WITH_FIX 95 -> arc_design PASS
- Arc 4: PASS_WITH_FIX 92 -> arc_design PASS
- Arc 5 attempt 1: REJECT 40
- Arc 5 attempt 2: PASS 98 -> arc_design PASS

Primary evidence:

- `projects/00_골든/logs/session/decisions.jsonl`
- `projects/00_골든/logs/session/ui_events.jsonl`
- `projects/00_골든/logs/runtime_audit.jsonl`

## Known Issue Clusters

### 1. Arc 3 continuity and metadata drift

What is already visible:

- location discrepancy between tactical document and summary/state surfaces
- mandated recovery beat omission across the six-week gap
- repeated auto-correct pressure on location and state vocabulary

What must be answered:

- is this mainly generation drift, finalizer drift, or sync drift
- which artifact surface is authoritative and which one is leaking stale state
- whether the recovery-beat omission is missing in the source tactical plan or
  lost during later normalization

## 2. Arc 4 numeric continuity and asset arithmetic drift

What is already visible:

- Director PASS_WITH_FIX had to correct start-state and end-state arithmetic
- cash and total-asset math needed explicit correction
- repeated location and state cleanup still occurred in the same arc

What must be answered:

- whether the arithmetic error originates in ensemble generation, post-pass
  normalization, or finalizer sync
- whether the same defect family is likely to recur in later arcs
- what the narrowest owner file set is

## 3. Arc 5 entity registry reject and retry

What is already visible:

- attempt 1 hard REJECT for entity naming mismatch
- attempt 2 PASS after focus-mode retry
- entity canonicalization ran, but attempt 1 still leaked variants

What must be answered:

- exactly where attempt 1 leaked entity alias variants
- whether attempt 2 passed because of canonicalization, focus-mode pressure, or
  both
- whether this is still a front blocker or now a recoverable residue

## 4. Persistent auto-correct pressure across arcs 3 to 5

What is already visible:

- repeated tactical_doc meta term cleanup
- repeated `internal_energy` removal
- repeated location sync
- repeated deterministic `physical_inventory` carryover

What must be answered:

- what is only visible in runtime audit and not operator-visible console/UI
- which owner files actually emit these corrections
- whether any of these are harmless residue versus real front blockers

## Read List For All Terminals

Mandatory:

- `AGENTS.md`
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
- `tttt.txt`
- `projects/00_골든/logs/session/decisions.jsonl`
- `projects/00_골든/logs/session/ui_events.jsonl`
- `projects/00_골든/logs/runtime_audit.jsonl`
- `projects/00_골든/logs/quality_metrics.jsonl`

## Terminal Ownership

### Terminal 1

Owner:
- Arc 3 and Arc 4 continuity, numeric drift, patch-pressure

Read additionally:

- `projects/00_골든/plans/arcs/arc_003.txt`
- `projects/00_골든/plans/arcs/arc_004.txt`
- `projects/00_골든/logs/artifacts/stage2/arc_003/attempt_01/`
- `projects/00_골든/logs/artifacts/stage2/arc_004/attempt_01/`
- `modules/domain/agents/arc_ensemble.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_optimizer.py`

Required questions:

- Where exactly does Arc 3 location truth diverge across tactical_doc,
  `joint_docs`, and `state_constraints`?
- Is the Arc 3 recovery-scene omission present in the generated tactical plan,
  or introduced by later normalization?
- Where exactly does Arc 4 asset arithmetic become inconsistent?
- Is the smallest owner set `arc_ensemble + stage2_finalizer`, or does
  `stage2_optimizer` still materially own part of the drift?

Output:

- `docs/2026-04-06/00_골든-stage2-terminal1-arc34-continuity-and-patch-pressure.md`

### Terminal 2

Owner:
- Arc 5 entity registry reject versus retry-pass

Read additionally:

- `projects/00_골든/plans/arcs/arc_005.txt`
- `projects/00_골든/logs/artifacts/stage2/arc_005/attempt_01/`
- `projects/00_골든/logs/artifacts/stage2/arc_005/attempt_02/`
- `modules/core/stage2_entity_contract.py`
- `modules/core/stage2_finalizer.py`
- `modules/domain/agents/arc_ensemble.py`

Required questions:

- Which exact entity variants triggered the attempt 1 REJECT?
- In which surface did those variants survive: tactical_doc, episode_details,
  state_constraints, or joint_docs?
- Why did attempt 2 pass: stronger focus-mode retrieval, canonicalization,
  different candidate selection, or a combination?
- Is entity naming still a front blocker after this run, or now a retry-only
  residue?

Output:

- `docs/2026-04-06/00_골든-stage2-terminal2-arc5-entity-reject-and-retry.md`

### Terminal 3

Owner:
- Observability, sink map, and repeated auto-correct owner mapping

Read additionally:

- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage2_preflight.py`
- `modules/core/quality_dashboard.py`
- `modules/core/services/audit_service.py`
- `modules/core/session_logger.py`

Required questions:

- Which correction families are only visible in runtime audit versus visible in
  UI/console?
- Which repeated corrections are harmless operator noise versus real front
  blockers?
- Which owner files are responsible for emitting each correction family?
- Is current observability sufficient for operators, or is there still a
  material visibility gap for Stage2?

Output:

- `docs/2026-04-06/00_골든-stage2-terminal3-observability-and-owner-map.md`

## Output Contract

Each terminal must:

- stay read-only
- write exactly one output document under `docs/2026-04-06/`
- put findings first
- cite exact file paths
- end with this exact line:

`read-only terminal survey complete; no files mutated outside assigned docs/2026-04-06 output`

## Paste-Ready Orders

### Opus Terminal 1

```text
시스템 오더다. `00_골든` 최신 Stage2 run의 `Arc 3/4 continuity + patch-pressure`만 조사해라.

읽을 것:
- AGENTS.md
- docs/implementation/system-order-init-harness.md
- docs/implementation/document-3pass-audit-harness.md
- docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md
- tttt.txt
- projects/00_골든/logs/session/decisions.jsonl
- projects/00_골든/logs/session/ui_events.jsonl
- projects/00_골든/logs/runtime_audit.jsonl
- projects/00_골든/plans/arcs/arc_003.txt
- projects/00_골든/plans/arcs/arc_004.txt
- projects/00_골든/logs/artifacts/stage2/arc_003/attempt_01/
- projects/00_골든/logs/artifacts/stage2/arc_004/attempt_01/
- modules/domain/agents/arc_ensemble.py
- modules/core/stage2_finalizer.py
- modules/core/stage2_optimizer.py

질문:
1. Arc 3 위치 truth는 어느 surface에서 처음 갈라지나
2. Arc 3 회복 장면 omission은 generation 문제인가, later normalization 문제인가
3. Arc 4 숫자/자산 arithmetic drift는 어디서 생기나
4. 가장 좁은 owner file 1~2개는 무엇인가

산출물:
- docs/2026-04-06/00_골든-stage2-terminal1-arc34-continuity-and-patch-pressure.md

규칙:
- read-only only
- code 수정 금지
- docs/temp 수정 금지
- retrieval-empty 재조사 금지
- findings 먼저
- 마지막 줄은 정확히:
  read-only terminal survey complete; no files mutated outside assigned docs/2026-04-06 output
```

### Opus Terminal 2

```text
시스템 오더다. `00_골든` 최신 Stage2 run의 `Arc 5 entity registry reject and retry`만 조사해라.

읽을 것:
- AGENTS.md
- docs/implementation/system-order-init-harness.md
- docs/implementation/document-3pass-audit-harness.md
- docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md
- tttt.txt
- projects/00_골든/logs/session/decisions.jsonl
- projects/00_골든/logs/session/ui_events.jsonl
- projects/00_골든/logs/runtime_audit.jsonl
- projects/00_골든/plans/arcs/arc_005.txt
- projects/00_골든/logs/artifacts/stage2/arc_005/attempt_01/
- projects/00_골든/logs/artifacts/stage2/arc_005/attempt_02/
- modules/core/stage2_entity_contract.py
- modules/core/stage2_finalizer.py
- modules/domain/agents/arc_ensemble.py

질문:
1. attempt 1 REJECT의 exact entity variant는 무엇인가
2. 그 variant는 tactical_doc, episode_details, state_constraints, joint_docs 중 어디에서 남았나
3. attempt 2 PASS는 canonicalization 효과인가, focus-mode 효과인가, 둘 다인가
4. entity naming은 아직 front blocker인가, 아니면 retry-only residue인가

산출물:
- docs/2026-04-06/00_골든-stage2-terminal2-arc5-entity-reject-and-retry.md

규칙:
- read-only only
- code 수정 금지
- docs/temp 수정 금지
- Stage4 확장 금지
- findings 먼저
- 마지막 줄은 정확히:
  read-only terminal survey complete; no files mutated outside assigned docs/2026-04-06 output
```

### Opus Terminal 3

```text
시스템 오더다. `00_골든` 최신 Stage2 run의 `observability + repeated auto-correct owner map`만 조사해라.

읽을 것:
- AGENTS.md
- docs/implementation/system-order-init-harness.md
- docs/implementation/document-3pass-audit-harness.md
- docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md
- tttt.txt
- projects/00_골든/logs/session/ui_events.jsonl
- projects/00_골든/logs/runtime_audit.jsonl
- projects/00_골든/logs/quality_metrics.jsonl
- modules/core/stage2_validation_pipeline.py
- modules/core/stage2_preflight.py
- modules/core/quality_dashboard.py
- modules/core/services/audit_service.py
- modules/core/session_logger.py

질문:
1. 어떤 correction family가 runtime_audit에만 남고 UI에는 안 보이나
2. 반복 auto-correct 중 real blocker와 harmless residue는 어떻게 갈리나
3. 각 correction family의 owner file은 어디인가
4. 현재 Stage2 operator observability는 충분한가, 아직 visibility gap이 남았나

산출물:
- docs/2026-04-06/00_골든-stage2-terminal3-observability-and-owner-map.md

규칙:
- read-only only
- code 수정 금지
- docs/temp 수정 금지
- retrieval는 non-issue로 두고 시작
- findings 먼저
- 마지막 줄은 정확히:
  read-only terminal survey complete; no files mutated outside assigned docs/2026-04-06 output
```

## 3-Pass Audit Note

- Pass 1: scope bounded to latest `00_골든` Stage2 run and its authoritative sinks
- Pass 2: issue clusters cross-checked against `tttt.txt`, `decisions`, `ui_events`,
  `runtime_audit`, and `quality_metrics`
- Pass 3: terminal ownership narrowed so each Opus lane has a distinct output and
  does not duplicate investigation

Confidence: 0.97
