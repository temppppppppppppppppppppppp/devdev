# Stage2/Stage3 Proof-Wave Terminal 1 Report — Stage2 Carryover Authority

Date: 2026-04-08
Terminal: 1 / 5
Source orders: `docs/2026-04-08/stage23-proof-wave-opus-survey-orders.md`
Target project: `projects/000_260408` (latest fresh run, session_id `20260408_131356`)
Mode: evidence harvest only — no code patch, no rerun

## 0. TL;DR

- Stage2 `carryover_authority` is **fully populated** on every Stage2 attempt row in this fresh run, on three of the four expected sinks.
- Cross-episode chain integrity (ep1.end → ep2.start → ep3.start) is **structurally intact** across location, inventory_count, capital, total_assets, and portfolio_position.
- One **sink drift** found: the DB `ui_events` mirror has zero `event_kind='carryover_authority'` rows, while `logs/session/ui_events.jsonl` has all three.
- One **summary surface gap**: `runtime_audit_summary.json::proof_digest.operational_metadata` exposes `stage3_live_session` and `stage4_live_session` but **no `stage2_live_session`** key — Stage2 carryover cannot be triaged from the summary alone.
- One **partial preview gap**: `end_inventory_preview` for ep2/ep3 still echoes only the first 3 items even though `end_inventory_count` is 5/7.
- One **possible semantic divergence** worth a deeper look: arc_003 structured `end_inventory_count=7` but the artifact prose's last `[종료 상태]` records 소지품 = "변경 없음" (i.e., still 5).
- Artifact-level structured carryover does **not** exist as a json field. The artifact only carries the carryover state inside the `tactical_doc` Korean prose block (`[시작 상태]` / `[종료 상태]` paragraphs). The structured projection lives in `stage_attempts.advisory_flags` + `director_selections.advisory_warnings` + `ui_events.jsonl` only.

## 1. What was checked

| sink | path | status |
|------|------|--------|
| stage_attempts.advisory_flags.carryover_authority | `project_data.db` | populated |
| director_selections.advisory_warnings.carryover_authority | `project_data.db` | populated |
| ui_events table, event_kind='carryover_authority' | `project_data.db` | **0 rows** |
| ui_events.jsonl, event_kind='carryover_authority' | `logs/session/ui_events.jsonl` | 3 rows (one per Stage2 ep) |
| Stage2 artifact payload | `logs/artifacts/stage2/arc_{001,002,003}/attempt_01/final_arc__*.json` | structured carryover absent; only prose inside `tactical_doc` |
| proof_digest.operational_metadata.stage2_live_session | `logs/runtime_audit_summary.json` | **absent** |

Stage2 attempt cardinality: 3 PASS rows (ep1/arc1, ep2/arc2, ep3/arc3), all `attempt_num=1`, all share `session_id` lineage `20260408_131356`.

## 2. Latest Stage2 carryover_authority snapshot (per attempt)

All values below are from `stage_attempts.advisory_flags.carryover_authority` (identical to `director_selections.advisory_warnings.carryover_authority` and to the `meta` block of the matching `ui_events.jsonl` line).

### attempt_key `s2:ep1:arc1:a1:20260408_131356` (stage_attempts.id=1)

| field | value |
|---|---|
| start_location | 윤성병원 장례식장 운영실 |
| end_location | 윤성병원 장례식장 지하 1층 후방 복도 |
| start_inventory_count | 1 |
| end_inventory_count | 3 |
| start_total_assets | 500만원 |
| end_total_assets | 500만원 + 장례식장 후방 운영권 (가치 미산정) |
| start_capital | 0원 |
| end_capital | 500만원 |
| start_portfolio_position | 해당 없음 |
| end_portfolio_position | 장례식장 후방 운영권 임시 확보 |
| investment_calc_final_total_assets | 5000000 |
| investment_calc_final_cash | 5000000 |
| start_inventory_preview | ["'제로라인파트너스' 법인 인감이 든 낡은 서류 가방"] |
| end_inventory_preview | ["'제로라인파트너스' 법인 인감이 든 낡은 서류 가방", "장례식장 전 구역 임시 출입증", "의전팀 내부 연락망이 동기화된 개인 스마트폰"] |

### attempt_key `s2:ep2:arc2:a1:20260408_131356` (stage_attempts.id=2)

| field | value |
|---|---|
| start_location | 윤성병원 장례식장 지하 1층 후방 복도 |
| end_location | 장례식장 지하 1층, 임시 상황실 (구 식자재 검수실) |
| start_inventory_count | 3 |
| end_inventory_count | 5 |
| start_total_assets | 500만원 + 장례식장 후방 운영권 (가치 미산정) |
| end_total_assets | 2억 500만원 + 장례식장 후방 운영권 (가치 미산정) |
| start_capital | 500만원 |
| end_capital | 2억 500만원 |
| start_portfolio_position | 장례식장 후방 운영권 임시 확보 |
| end_portfolio_position | 장례식장 급식 라인 운영권 확보 및 반복매출 후보 라인 선점 |
| investment_calc_final_total_assets | 205000000 |
| investment_calc_final_cash | 205000000 |
| end_inventory_preview | only echoes the first 3 items (still ep1's 3-item inventory), even though count=5 |

### attempt_key `s2:ep3:arc3:a1:20260408_131356` (stage_attempts.id=3)

| field | value |
|---|---|
| start_location | 장례식장 지하 1층, 임시 상황실 (구 식자재 검수실) |
| end_location | 장례식장 주차 관제 타워 최상층 |
| start_inventory_count | 5 |
| end_inventory_count | 7 |
| start_total_assets | 2억 500만원 + 장례식장 후방 운영권 (가치 미산정) |
| end_total_assets | 1억 500만원 + 장례식장 후방 운영권 + 장례식장 외부 교통 관제권 (48시간) |
| start_capital | 2억 500만원 |
| end_capital | 1억 500만원 |
| start_portfolio_position | 장례식장 급식 라인 운영권 확보 및 반복매출 후보 라인 선점 |
| end_portfolio_position | 장례식장 급식 및 외부 교통 운영권 확보 |
| investment_calc_final_total_assets | 105000000 |
| investment_calc_final_cash | 105000000 |
| end_inventory_preview | only echoes the first 3 items, even though count=7 |

## 3. Cross-sink alignment (DB ↔ JSONL ↔ Artifact)

### 3.a Structured-vs-structured (stage_attempts ↔ director_selections ↔ ui_events.jsonl)

For all 3 Stage2 episodes, every field above matches **field-for-field, byte-for-byte** across:
- `stage_attempts.advisory_flags.carryover_authority`
- `director_selections.advisory_warnings.carryover_authority`
- `logs/session/ui_events.jsonl[meta]` for `event_kind='carryover_authority'`

No drift on the structured side.

### 3.b Structured-vs-prose (carryover_authority ↔ artifact `tactical_doc`)

Each arc artifact's `tactical_doc` contains `ep_count` `[시작 상태]` and `[종료 상태]` paragraph blocks. The arc-end carryover should match the **last** `[종료 상태]` block in the doc.

| arc | side | structured carryover | last [종료 상태] in tactical_doc | verdict |
|---|---|---|---|---|
| 001 | end_location | 윤성병원 장례식장 지하 1층 후방 복도 | 윤성병원 장례식장 지하 1층 후방 복도 | match |
| 001 | end_inventory_count | 3 | 소지품 prose lists 3 items | match |
| 001 | start_location | 윤성병원 장례식장 운영실 | "윤성병원 장례식장 최상층, 임시 법률 집행실로 쓰이는 운영실" | **lossy normalization** — same room, structured drops the qualifier |
| 002 | start_location | 윤성병원 장례식장 지하 1층 후방 복도 | (matches arc_001 end) | match (chain) |
| 002 | end_location | 장례식장 지하 1층, 임시 상황실 (구 식자재 검수실) | 장례식장 지하 1층, 임시 상황실 (구 식자재 검수실) | match |
| 002 | end_inventory_count | 5 | 소지품 prose lists 5 items | match |
| 003 | start_location | 장례식장 지하 1층, 임시 상황실 (구 식자재 검수실) | (matches arc_002 end) | match (chain) |
| 003 | end_location | 장례식장 주차 관제 타워 최상층 | 장례식장 주차 관제 타워 최상층 | match |
| 003 | end_capital | 1억 500만원 | "- 자본: 1억 500만원" | match |
| 003 | end_inventory_count | 7 | "- 소지품: 변경 없음" (i.e., still 5) | **mismatch** — count claims +2 but prose says no change |

### 3.c Cross-episode chain (DB → DB)

| boundary | end side | next start side | match |
|---|---|---|---|
| ep1 → ep2 | location: 지하 1층 후방 복도 / inv=3 / capital=500만 / assets=500만+후방운영권 | same | ✓ |
| ep2 → ep3 | location: 임시 상황실 (식자재 검수실) / inv=5 / capital=2억500만 / assets=2억500만+후방운영권 | same | ✓ |

The chain is **clean** at the structured layer. Whatever ep_n records as its end-state is exactly what ep_{n+1} reads as its start-state.

## 4. Gap classification

| # | finding | type | severity |
|---|---|---|---|
| G1 | DB `ui_events` table has 0 rows for `event_kind='carryover_authority'` while `ui_events.jsonl` has 3 | **sink drift** (DB writer skips this event_kind, or it is filtered before insert) | medium — JSONL still authoritative, but operators querying the DB will see nothing |
| G2 | `proof_digest.operational_metadata` lacks `stage2_live_session` (only stage3 / stage4 keys exist) | **logging gap** at the summary tier | medium — Terminal 5 owns this, but it directly affects whether a summary-only triage answers Stage2 carryover questions |
| G3 | `end_inventory_preview` for ep2/ep3 only echoes the first 3 items though `end_inventory_count` is 5 / 7 | **logging gap** in the preview projection (count is correct, preview is stale) | low — count is the proof field, preview is the cosmetic digest |
| G4 | arc_001 structured `start_location` drops the "최상층, 임시 법률 집행실로 쓰이는" qualifier present in tactical_doc prose | **lossy normalization** at carryover-extraction time | low — same room, no contradiction |
| G5 | arc_003 structured `end_inventory_count=7` vs prose 소지품 "변경 없음" (still 5) | **possible upstream semantic/runtime issue** — extractor and tactical_doc author disagree on whether the 교통 관제권 + 자본 deltas added inventory items | medium — needs deeper read of the inventory accumulation rule before escalating |
| G6 | Artifact json has no structured `carryover_authority` field at all (prose only) | **logging gap** by design — the structured projection is computed at attempt-runtime and persisted to advisory_flags / advisory_warnings / jsonl, never folded back into the artifact | informational — affects the merge-rule "prefer artifact truth" clause: there is no artifact-level json truth to prefer for this surface |

## 5. Answer to the orders question

> does Stage2 now expose authoritative carryover location / inventory / finance truth clearly enough for proof use?

**Yes, for structured/automated proof consumers** that read `stage_attempts.advisory_flags.carryover_authority` (or the equivalent `director_selections.advisory_warnings.carryover_authority`, or the `ui_events.jsonl` sink). The data is present, internally consistent across those three sinks, and the cross-episode chain holds.

**Not yet, for two specific consumer paths:**
1. operators who query the DB `ui_events` table — sink drift G1.
2. operators who triage from `runtime_audit_summary.json` alone — gap G2 (`stage2_live_session` is not in `proof_digest.operational_metadata`).

**Caveats for proof writers** that follow the merge-rule "artifact truth → DB truth → session sink → summary":
- there is no artifact-level structured carryover (G6) — the artifact-tier evidence is the Korean prose inside `tactical_doc`. A proof writer that wants to verify against the artifact must either grep the prose blocks or accept advisory_flags/advisory_warnings as the authoritative tier.
- one prose-vs-structured mismatch worth a deeper Stage2 read before escalation: arc_003 inventory delta (G5).

## 6. What still requires raw DB / JSONL join

To answer "what is the latest Stage2 end-state for ep_N" without joining DB or jsonl, today you would need:
- `proof_digest.operational_metadata.stage2_live_session.carryover_authority.{start_location,end_location,start_inventory_count,end_inventory_count,start_capital,end_capital,start_total_assets,end_total_assets,start_portfolio_position,end_portfolio_position,investment_calc_final_*}` — none of which exists in the summary yet.

Until that summary block lands, the canonical query path for this surface is:

```sql
SELECT id, ep_num, attempt_key, json_extract(advisory_flags, '$.carryover_authority')
FROM stage_attempts
WHERE stage = 2
ORDER BY id;
```

## 7. Anchors used

- `projects/000_260408/project_data.db` — `stage_attempts`, `director_selections`, `ui_events` tables
- `projects/000_260408/logs/session/ui_events.jsonl` — 382 total lines, 3 carryover_authority lines
- `projects/000_260408/logs/artifacts/stage2/arc_001/attempt_01/final_arc__balanced.json`
- `projects/000_260408/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json`
- `projects/000_260408/logs/artifacts/stage2/arc_003/attempt_01/final_arc__conservative.json`
- `projects/000_260408/logs/runtime_audit_summary.json`
