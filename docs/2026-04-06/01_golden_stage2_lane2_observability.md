# Lane 2: Observability Survey

Date: 2026-04-06
Lane: `observability`
Scope: `01_투자물_골든_ Stage 2 console / sink visibility / stale-summary mapping`
Mode: read-only survey; no regeneration; no code patching

## 1. Coverage

Sinks inspected:

| Sink | Lines / Records | Session | Inspected |
| ---- | ---- | ---- | ---- |
| `logs/session/ui_events.jsonl` | 605 lines | two sessions appended: `20260406_145605` (244 lines) + `20260406_151038` (361 lines) | full |
| `logs/session/decisions.jsonl` | 11 records | `20260406_151038` only | full |
| `logs/quality_metrics.jsonl` | 7 records | both sessions | full |
| `logs/pass_rate_monitor.json` | 1 object, 0 records | `20260406_145605` shutdown only | full |
| `logs/runtime_audit_summary.json` | 1 object | `20260406_145605` shutdown only | full |
| `logs/session_20260406_151023.log` | 2471 lines | `20260406_151038` | full |

Session structure:

- **Session 1** (`20260406_145605`): 14:56:05 → 14:56:40. Stage 0 only. Clean shutdown with full metrics sequence (all zeros). Wrote `pass_rate_monitor.json` and `runtime_audit_summary.json`.
- **Session 2** (`20260406_151038`): 15:10:38 → interrupted at ~16:18:56. Stage 0 re-run + Stage 2 production (Arc 1–5 start). No shutdown event. No update to `pass_rate_monitor.json` or `runtime_audit_summary.json`.

## 2. Findings

### F-1. Console claims `internal_energy` removal; saved artifact truth disagrees (P1-supporting)

Console auto-correct events (`[S2-OBS]`) claim `arc_start_state에서 무협 전용 필드 제거: ['internal_energy']` and/or `arc_end_state에서 무협 전용 필드 제거: ['internal_energy']` for:

| Arc | ui_events line | Claim |
| ---- | ---- | ---- |
| Arc 1 | 456 | `arc_start_state` + `arc_end_state` removal claimed |
| Arc 3 | 517 | `arc_start_state` removal claimed |
| Arc 4 (attempt 2, accepted) | 574 | `arc_start_state` + `arc_end_state` removal claimed |

Arc 2 auto-correct (line 489) does **not** mention `internal_energy` removal — it performs location sync and term replacement only.

The survey order's provisional severity map states the saved accepted artifacts for Arc 1, Arc 3, and Arc 4 still contain `internal_energy`. If confirmed by Lane 1, this is a **false-closure claim**: the console reports repair completed while the saved artifact preserves the field.

Observable severity from this lane alone: the console log misleads the operator into believing the genre-contract repair succeeded.

### F-2. `pass_rate_monitor.json` is stale (P2-supporting)

```json
"session_start": "2026-04-06T14:56:07.795412",
"last_updated": "2026-04-06T14:56:40.803941",
"total_records": 0,
"records": []
```

Written during Session 1 shutdown. Session 2 produced 4 accepted arcs and 1 rejected attempt with formal `decisions.jsonl` records but never refreshed `pass_rate_monitor.json`. An operator reading this sink alone sees zero pass-rate records for a run that passed 4 of 5 attempted arcs.

### F-3. `runtime_audit_summary.json` is stale (P2-supporting)

```json
"tag": "shutdown_final",
"timestamp": "2026-04-06 14:56:40",
"total_events": 0,
"session_decisions_exists": false
```

Written during Session 1 shutdown. Key misleading fields:

- `total_events: 0` — actual Stage 2 run emitted 605 ui_events lines and 2471 session log lines
- `session_decisions_exists: false` — `decisions.jsonl` exists and contains 11 records
- `proof_digest.available: false` — meanwhile DB, ui_events, decisions, and quality_metrics all contain substantial Stage 2 evidence
- `session_lineage.plain_log_token: "20260406_145601"` — points to Session 1 log, not Session 2 (`20260406_151023`)

An operator trusting `runtime_audit_summary.json` would conclude the system ran for 35 seconds with zero events and no decisions — entirely wrong.

### F-4. `ui_events.jsonl` ends abruptly with no shutdown marker (P3-supporting)

Last event (line 606, seq 361):
```
ts: 2026-04-06T16:18:13
message: "🔎 [TF-38] 벡터 검색 완료 (388자)"
component: UI, event_kind: log
```

Session 1 has a clean `shutdown` event sequence (lines 237–244: shutdown progress → metrics summary → pass rate → failure learner → voice → foreshadow → emotion). Session 2 has **none of these**. No `🛑 [System] 시스템 종료 시퀀스 가동...` event.

The session log (`session_20260406_151023.log`) also ends mid-flight at line 2471: `receive_response_headers.started request=<Request [b'POST']>` — three `ArcEnsembleGenerator` HTTP calls were dispatched but no response was ever received.

There is no explicit `interrupted` / `aborted` / `partial_shutdown` marker in any sink.

### F-5. `decisions.jsonl` accurately records all verdicts (non-issue turned positive finding)

`decisions.jsonl` contains 11 records covering:

| Record | Arc | Round | Result | Score |
| ---- | ---- | ---- | ---- | ---- |
| 1 | ep_num=1 | 0 | PASS_WITH_FIX | 98 |
| 2 | arc_design 1 | 0 | PASS | 0 |
| 3 | ep_num=2 | 0 | PASS | 100 |
| 4 | arc_design 2 | 0 | PASS | 0 |
| 5 | ep_num=3 | 0 | PASS_WITH_FIX | 93 |
| 6 | arc_design 3 | 0 | PASS | 0 |
| 7 | ep_num=4 | 0 | REJECT | 88 |
| 8 | arc_design 4 | 0 | REJECT | 88 |
| 9 | ep_num=4 | 1 | PASS_WITH_FIX | 93 |
| 10 | arc_design 4 | 1 | PASS | 0 |
| 11 | (no Arc 5 entry) | — | — | — |

This sink is authoritative and consistent with the session log. Absent Arc 5 record correctly reflects the interrupted state.

### F-6. `quality_metrics.jsonl` provides complete retrieval telemetry (non-issue)

7 `retrieval_observation` records covering ep_num 1, 6, 12, 17 (twice — rejected + accepted), and 22 (Arc 5 preflight). All show:

- `work_focus_present: true`
- `coverage_warnings: []`
- No overflow or trim events
- Budget headroom available on all calls

The ep_num=22 record (Arc 5, timestamp 16:18:13) confirms Arc 5 reached retrieval stage before interruption.

### F-7. Console Director verdicts are fully visible (non-issue)

All Director verdicts for Arc 1–4 (including the Arc 4 REJECT with detailed financial-mismatch feedback) appear in `ui_events.jsonl` with `visible: true`. The REJECT reason, contradiction details, and fix instructions are all rendered to console. The re-attempt cycle (attempt 2/10) and re-acceptance (PASS_WITH_FIX score=93) are also fully visible.

### F-8. `visible: false` events are restricted to user-input responses (non-issue)

All 45 `visible: false` events are `prompt_response` or `selection` type events recording operator input choices during Stage 0 (genre selection, project selection, treatment choice, arc count). No Stage 2 production events are hidden.

## 3. Non-Issues

- **Director thinking visibility**: All Director verdicts, scores, reasons, and fix instructions are rendered with `visible: true`. The "콘솔 로그 최대 표시 정책" from `AGENTS.md` appears honored for Stage 2 Director events.
- **`decisions.jsonl` integrity**: 11 records, all properly structured, timestamps consistent with session log and ui_events. No identity collision, no duplicate, no orphan.
- **`quality_metrics.jsonl` integrity**: 7 records, all properly structured retrieval observations with complete provenance and budget ledgers. No budget overflow.
- **Session log completeness for Arc 1–4**: Full verdict chain, ensemble generation, selection, patch, re-examination, acceptance all logged with timestamps.
- **Auto-correct visibility**: All `[S2-OBS]` auto-correct messages are `visible: true` and rendered to console. The operator can see what auto-correct claims to have done.

## 4. Severity Hint

| ID | Candidate Severity | Description | Lane 2 Evidence Strength |
| ---- | ---- | ---- | ---- |
| F-1 | P1 | Console claims `internal_energy` removal completed; if saved artifacts disagree, this is false-closure | **Strong from observability side** — console messages explicitly claim removal. Requires Lane 1 artifact byte-level confirmation to close. |
| F-2 | P2 | `pass_rate_monitor.json` shows 0 records for a 4-arc accepted run | **Confirmed** — timestamp proves Session 1 origin; no Session 2 refresh |
| F-3 | P2 | `runtime_audit_summary.json` reports zero events, no decisions, wrong session lineage | **Confirmed** — every field contradicts actual run state |
| F-4 | P3 | No explicit interrupted-run marker in any sink after Arc 5 preflight | **Confirmed** — operator must cross-reference ui_events tail + session log tail + absent shutdown sequence to infer interruption |

## 5. Stop

read-only lane survey complete; no project artifacts mutated
