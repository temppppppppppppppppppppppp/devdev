# Terminal 4: Observability, Owner Map, and Next-Wave Assessment

Date: 2026-04-06
Status: final
Mode: read-only bounded survey
Scope: `00_골든` latest Stage3 run — observability / warning surfacing / next-wave owner map

---

## Findings First

### 1. Current Stage3 evidence supports continuing to S4. No bounded fix wave is required before S4.

- All 6 episodes PASS (scores 84–95). Zero REJECTs in Stage3.
- All warning families are advisory-only. None block Director verdict.
- ep5 (score 84) is the weakest, but its issues are bounded (`fix_scope: inplace`).
- Stage4 has its own retry/correction pipeline to catch manuscript issues from weak blueprints.
- ep7 was user-stopped, not hung. No evidence of runtime blocking.

### 2. `quality_risk: true` is non-discriminating — always on for every episode.

`quality_risk` is set to `true` for all 6 persisted episodes. It triggers whenever any `python_warning` entry exists, and the fidelity check (`intent 불일치`) fires on every episode because the arc has relationship NPCs that aren't literally name-matched in blueprint text. This flag currently has zero discriminatory power in this run.

### 3. The operator has no single-line per-episode summary.

The operator must mentally aggregate 4–8 fragmented console lines per episode. There is no `[Stage3 Summary] ep 5: PASS 84 | attempt 2 | TF-49:2 | PinGuard:unresolved` style line. Warning context requires cross-referencing `decisions.jsonl` or artifact JSON.

---

## Q1: Which Warning Families Are Operator-Visible vs Implicit?

### Operator-Visible (console + `ui_events.jsonl`)

| Family | Emitter | Lines | Example |
|---|---|---|---|
| **Score + Verdict + Strategy** | `stage3_orchestrator.py:1524-1543` | `📊 제N화 Blueprint 결과: PASS (score=XX)` / `└─ 선택 전략: xxx_focused` | All episodes |
| **Director reasoning** | `stage3_orchestrator.py:2262-2311` via `_build_stage3_success_operator_lines()` | `└─ Director 판정:` / `비교 메모:` / `보완 포인트:` / `주의:` | ep2, ep5 |
| **TF-49 inventory gaps** | `stage3_orchestrator.py:2015` | `[TF-49] inventory gaps N: item1, item2` | ep2–ep6 |
| **PinGuard unresolved** | `stage3_orchestrator.py:2052` | `[PinGuard][WARN] ep N unresolved continuity pins` | ep3, ep5 |
| **Completion stats** | `stage3_orchestrator.py:677-683` | `성공: X개 \| 실패: Y개` / `통과율:` | End of run |

### Implicit / Hidden from Operator

| Family | Storage | Why hidden |
|---|---|---|
| **`quality_risk: true`** | `decisions.jsonl` meta, artifact `_ensemble_meta`, `quality_dashboard` | No explicit `[quality_risk]` console line; only a meta field |
| **`prevalidation_issue_count`** | artifact JSON `_ensemble_meta` | ep5 had 6 issues — never shown as a number to operator |
| **`binding_prevalidation_issue_count`** | pipeline_result internal | Count of binding-class issues, not surfaced |
| **Attempt number (a1 vs a2)** | `decisions.jsonl` `attempt_key` field | No `[Attempt 2/10]` operator line. Operator infers from console timing or checks JSONL |
| **Detailed python_warnings list** | artifact JSON `_ensemble_meta.python_warnings` | Only selectively surfaced via `주의:` lines. ep1/ep3/ep4/ep6 had warnings in artifacts but no `주의:` console output |
| **`fix_scope: inplace`** | `decisions.jsonl` meta | Not shown as a distinct operator line |

### Key Observation: ep1/ep3/ep4/ep6 Warnings Are Suppressed

All 6 episodes had `python_warnings` in their artifact JSONs (at minimum `fidelity` + `scenario_density`). However, the `주의:` operator lines only appeared for ep2 and ep5.

The rendering path is `_build_stage3_success_operator_lines()` at `stage3_orchestrator.py:2305-2311`: it reads `validate.selected_candidate_advisory.python_warnings` from the pipeline_result. Whether this key is populated depends on which validation flow was taken (compare mode vs ensemble mode vs fallback). For ep1/ep3/ep4/ep6, the Director validation returned with `score strong (XX.0)` — a clean enough verdict that the advisory details were not forwarded to the operator lines.

This means: **the operator sees python_warnings only when the Director explicitly embeds them in the verdict structure, not when they actually exist.**

---

## Q2: Which Warnings Would Actually Matter Before Continuing to S4?

| Warning | Priority | S4 Blocker? | Reasoning |
|---|---|---|---|
| `TF-49 inventory gaps` worsening (1→2 items) | MEDIUM | No | Items may be acquired during episode as planned by arc; but if not acquired, S4 manuscript will have continuity errors. Terminal 3 lane owns the root cause. |
| `binding prevalidation repair required` (ep5) | MEDIUM | No | ep5 has the most issues (6) and lowest score (84). S4 will likely need an extra retry for ep5 manuscript. Bounded risk. |
| `PinGuard unresolved` (ep3, ep5) | LOW | No | Conservative check; Director already approved. PinGuard is advisory-only. |
| `quality_risk: true` | NOT ACTIONABLE | No | Always true for every episode. Zero discriminatory power. |
| `intent 불일치: NPC 4명 미언급` | LOW | No | Fires on every episode due to sensitive exact-name matching. The NPC names may appear in actual manuscripts. |
| `시나리오 구체성 부족` | LOW | No | Anchor regex threshold (5) too aggressive for early investment fiction blueprints. Calibration issue. |

**Bottom line**: No warning family is an S4 blocker. ep5 is the highest-risk blueprint for S4 — predict it may need S4 retry. All others are clean enough to proceed.

---

## Q3: Narrowest Next-Wave Owner Files

### Primary Owner: `modules/domain/agents/unified_blueprint_validator.py`

This single file is the source of:

- **All Python prevalidation checks**: `_collect_structure_prevalidation_issues` (line 795), `_collect_fidelity_prevalidation_issues` (line 873), `_collect_arc_compliance_prevalidation_issues` (line 903), `_collect_continuity_prevalidation_issues` (line 929), scenario density check (line 1795–1815)
- **Binding prevalidation contract**: `_apply_binding_prevalidation_contract` (line 211) — controls when PASS becomes PASS_WITH_FIX and what `fix_scope_reasoning` text appears
- **`quality_risk` decision**: `_build_python_warning_entries` (line 160) — returns `bool(entries)`, meaning any warning triggers quality_risk
- **`python_warnings` list**: feeds the `주의:` operator lines

A fix wave here could:
- Tune fidelity check sensitivity (Arc relationship NPC matching too broad)
- Tune scenario_density anchor threshold (5 too aggressive for short early blueprints)
- Make `quality_risk` discriminatory (only MAJOR/CRITICAL, not MINOR)

### Secondary Owner: `modules/core/stage3_orchestrator.py`

This file controls:

- **TF-49 warning** emission (line 2011–2015)
- **PinGuard warning** emission (line 2041–2058)
- **Operator line rendering** via `_build_stage3_success_operator_lines` (line 2249–2313)
- **Decision logging** via `_log_stage3_session_decision` (line 2325+)
- **Quality dashboard** recording (line 2134–2165)
- **Completion summary** (line 677–683)

A fix wave here could:
- Add attempt number to console output (currently invisible)
- Add a one-line per-episode summary at blueprint save time
- Make TF-49 and PinGuard show detail (which items, which pins) not just counts/labels
- Surface python_warnings consistently, not only when Director verdict structure happens to include them

### Files NOT in the owner set

| File | Reason to exclude |
|---|---|
| `three_phase_blueprint_generator.py` | Only has `[TF-49b]` arc excerpt prep, not the warning emission |
| `chief_writer.py` | Not involved in Stage3 warning pipeline |
| `session_logger.py` | Pure sink — writes whatever it's given; no filtering or decision logic |
| `continuity_pin_guard.py` | Produces the pin data but the warning rendering is in `stage3_orchestrator.py` |

---

## Q4: Continue to S4 or Bounded Fix Wave First?

### Recommendation: Continue to S4.

**Evidence supporting S4 continuation:**

1. 6/6 episodes PASS. Score range 84–95. No REJECT.
2. All warning families are advisory-only. Director approved every episode.
3. ep5 (weakest, 84) has `fix_scope: inplace` — bounded repair, not structural rewrite.
4. Stage4 has its own validation/retry loop to catch manuscript quality issues.
5. TF-49 inventory gaps and PinGuard unresolved are conservative checks, not truth leaks (Terminal 3 to confirm).
6. ep7 was user-stopped, not evidence of a runtime bug.

**Two quality-of-life improvements worth noting (not blockers):**

1. **(Low effort, `stage3_orchestrator.py` only)** Add attempt number to console output. The operator currently cannot distinguish attempt_01 from attempt_02 without reading `decisions.jsonl`. A `[Attempt 2]` tag on the result line would suffice.

2. **(Medium effort, `stage3_orchestrator.py` only)** Add a single-line per-episode summary at blueprint save time:
   ```
   [Stage3 Summary] ep 5: PASS 84 | attempt 2 | TF-49:2 | PinGuard:unresolved | prevalidation:6
   ```
   This would give the operator instant triage capability without cross-referencing logs.

Both are operator visibility improvements in the secondary owner file. They do not change pipeline behavior, scoring, or validation logic.

---

## Warning Flow Diagram (Simplified)

```
unified_blueprint_validator.py
  ├─ _python_pre_validate()
  │    ├─ _collect_structure_prevalidation_issues()
  │    ├─ _collect_fidelity_prevalidation_issues()     → "intent 불일치"
  │    ├─ _collect_arc_compliance_prevalidation_issues()
  │    └─ _collect_continuity_prevalidation_issues()
  │
  ├─ scenario density check (L1795-1815)               → "시나리오 구체성 부족"
  │
  ├─ _build_python_warning_entries()                    → python_warnings list + quality_risk bool
  │
  └─ _apply_binding_prevalidation_contract()            → "binding prevalidation repair required"
       │
       ▼
stage3_orchestrator.py
  ├─ _build_stage3_success_operator_lines()             → Console: "주의:", "보완 포인트:", "Director 판정:" 
  ├─ _detect_inventory_gaps()                           → Console: "[TF-49]"
  ├─ apply_continuity_pins() + unresolved check         → Console: "[PinGuard][WARN]"
  ├─ _log_stage3_session_decision()                     → decisions.jsonl
  ├─ _record_stage3_success_completion()                → quality_dashboard, audit_event
  └─ Completion summary (L677-683)                      → Console: success/fail counts
       │
       ▼
session_logger.py                                       → ui_events.jsonl (pure sink, no filtering)
```

---

## Evidence Sources

| Evidence | Path | Role |
|---|---|---|
| Authoritative decisions | `projects/00_골든/logs/session/decisions.jsonl` | 19 lines, S2+S3 combined |
| UI event log | `projects/00_골든/logs/session/ui_events.jsonl` | ~630+ entries |
| Stage3 artifacts | `projects/00_골든/logs/artifacts/stage3/ep_0001..0006/` | Per-episode blueprint JSON with `_ensemble_meta` |
| Console evidence | `tttt.txt` | Convenience only — confirmed consistent with JSONL sinks |
| Warning emission code | `modules/core/stage3_orchestrator.py` L2011-2058, L2249-2313, L2134-2165 | Rendering + recording |
| Prevalidation code | `modules/domain/agents/unified_blueprint_validator.py` L160-239, L795-1815 | Check logic + quality_risk |
| Logging infrastructure | `modules/core/session_logger.py` L152-179, L208-250 | Pure sink |
| Pin guard | `modules/core/continuity_pin_guard.py` L133+ | Pin data generation |

---

## Confidence

- Q1 (warning visibility): 0.97 — verified against both source code and actual JSONL output
- Q2 (S4 priority): 0.95 — all warnings confirmed advisory-only; ep5 risk assessment from artifact evidence
- Q3 (owner map): 0.97 — code-traced to exact line ranges; negative checked 4 excluded files
- Q4 (continue/fix): 0.96 — 6/6 PASS with no runtime blocking evidence; QoL items bounded to one file

---

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-06 output
