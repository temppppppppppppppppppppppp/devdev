# Terminal 1 — Stage2 Carryover Authority Parity (`000_260408_B`)

- Target project: `projects/000_260408_B/`
- Target session: `20260408_161433`
- Role: Terminal 1 of the Stage2/Stage3 proof-wave evidence harvest
- Mode: evidence harvest only — no code edits, no rerun, no DB mutation
- Authority rule applied: persisted sinks > console text

## 1. What was checked

Four persistence layers for Stage2 carryover authority, plus the Stage2 artifact payloads that feed them:

1. `stage_attempts.advisory_flags.carryover_authority` (DB)
2. `director_selections.advisory_warnings.carryover_authority` (DB)
3. `ui_events` rows where `event_kind='carryover_authority'` (DB)
4. `logs/session/ui_events.jsonl` rows where `event_kind='carryover_authority'` (session sink)
5. Stage2 arc artifact payloads under `logs/artifacts/stage2/arc_00{1,2,3}/attempt_01/final_arc__*.json`, specifically:
   - `state_constraints.arc_start_state.{location,capital,total_assets,portfolio_position}`
   - `state_constraints.arc_end_state.{location,capital,total_assets,portfolio_position}`
   - `joint_docs.final_location`
   - `joint_docs.physical_inventory`
   - `semantic_carryover.continuity_checkpoints`

All queries filtered on `stage=2` and / or `session_id='20260408_161433'`. Korean text was decoded with `PYTHONIOENCODING=utf-8`; all values below are the authentic DB / file strings.

## 2. Concrete evidence

### 2.1 Row counts per sink (stage=2, session `20260408_161433`)

| Sink | Rows |
|---|---|
| `stage_attempts` (stage=2) | **3** (ep1/arc1, ep2/arc2, ep3/arc3; all attempt_num=1, verdict=PASS) |
| `director_selections` (stage=2) | **3** (ep1 creative, ep2 creative, ep3 conservative; all verdict=PASS) |
| DB `ui_events` (`event_kind='carryover_authority'`) | **3** (ids 307, 332, 359) |
| Session `ui_events.jsonl` (`event_kind='carryover_authority'`) | **3** |
| Stage2 artifacts on disk | **3** (`arc_001/attempt_01/final_arc__creative.json`, `arc_002/attempt_01/final_arc__creative.json`, `arc_003/attempt_01/final_arc__conservative.json`) |

Attempt keys are identical across all four sinks:

- `s2:ep1:arc1:a1:20260408_161433`
- `s2:ep2:arc2:a1:20260408_161433`
- `s2:ep3:arc3:a1:20260408_161433`

### 2.2 Arc 3 latest carryover authority snapshot (deliverable)

Source: all four sinks agree byte-for-byte on the canonical fields. Values reproduced from `ui_events` id 359 (`session_id=20260408_161433`, `attempt_key=s2:ep3:arc3:a1:20260408_161433`, `stage=2`, `ep_num=3`, `arc_num=3`, `level=info`, `component=stage2_carryover`).

| Field | Value |
|---|---|
| `start_location` | 장례식장 지하 1층, 3번 화물 게이트 앞 임시 관제 구역 |
| `end_location` | 새롭게 분리된 일반 조문객 셔틀버스 승강장 |
| `start_inventory_count` | 5 |
| `end_inventory_count` | 8 |
| `start_inventory_preview` | [결제 기능 정지된 법인카드, 제로라인파트너스 명의 임시 운영 총괄 책임 위임 계약서, 의전팀 연락망 동기화된 구형 스마트폰] *(3 of 5)* |
| `end_inventory_preview` | [결제 기능 정지된 법인카드, 제로라인파트너스 명의 임시 운영 총괄 책임 위임 계약서, 의전팀 연락망 동기화된 구형 스마트폰] *(3 of 8)* |
| `start_total_assets` | 2억 500만원 + 장례식장 뒷문 운영권 |
| `end_total_assets` | 1억 500만원 + 장례식장 운영권 일체 |
| `start_capital` | 2억원 |
| `end_capital` | 1억원 |
| `start_portfolio_position` | 제로라인파트너스 지분 100% (현금 2억원, 장례식장 임시 운영권 보유) |
| `end_portfolio_position` | 제로라인파트너스 지분 100% (현금 1억원, 장례식장 운영권 일체 보유) |
| `investment_calc_final_total_assets` | 105000000 |
| `investment_calc_final_cash` | 100000000 |
| `continuity_checkpoint_count` | 3 |
| `semantic_carryover_keys` | [relationship_rationale, growth_justification, foreshadow_anchors, continuity_checkpoints] |

Pretty-printed message (identical in DB and session sinks):
`📎 [Stage2 Carryover Authority] start=장례식장 지하 1층, 3번 화물 게이트 앞 임시 관제 구역 (5 items) -> end=새롭게 분리된 일반 조문객 셔틀버스 승강장 (8 items) | assets=1억 500만원 + 장례식장 운영권 일체`

### 2.3 Per-arc parity — start/end location, inventory count, capital, total assets, portfolio position

All four sinks (`stage_attempts`, `director_selections`, DB `ui_events`, session `ui_events.jsonl`) agree on every canonical field below for every arc. The rightmost "Artifact" column is the disk-level source-of-truth (from `state_constraints.arc_{start,end}_state.*` and `joint_docs.*`).

#### Arc 1 (ep1, attempt_key `s2:ep1:arc1:a1:20260408_161433`, candidate `creative`)

| Field | Sink value | Artifact value | Match |
|---|---|---|---|
| start_location | 윤성가 장례식장 임시 법률 집행실 | `state_constraints.arc_start_state.location` = 윤성가 장례식장 임시 법률 집행실 | ✓ |
| end_location | 장례식장 지하 1층 의전팀 임시 사무실 | `state_constraints.arc_end_state.location` = 장례식장 지하 1층 의전팀 임시 사무실; `joint_docs.final_location` identical | ✓ |
| start_inventory_count | 2 | *(artifact does not store pre-arc inventory list; derived upstream)* | n/a |
| end_inventory_count | 3 | `joint_docs.physical_inventory` length = **3** | ✓ |
| start_total_assets | 500만원 | `arc_start_state.total_assets` = 500만원 | ✓ |
| end_total_assets | 500만원 + 장례식장 뒷문 운영권 | `arc_end_state.total_assets` = 500만원 + 장례식장 뒷문 운영권 | ✓ |
| start_capital | 0원 | `arc_start_state.capital` = 0원 | ✓ |
| end_capital | 0원 | `arc_end_state.capital` = 0원 | ✓ |
| start_portfolio_position | 제로라인파트너스 지분 100% | `arc_start_state.portfolio_position` identical | ✓ |
| end_portfolio_position | 제로라인파트너스 지분 100% (장례식장 임시 운영권 보유) | `arc_end_state.portfolio_position` identical | ✓ |
| continuity_checkpoint_count | 3 | `semantic_carryover.continuity_checkpoints` len = 3 | ✓ |

`end_inventory_preview` contains all 3 items → matches `joint_docs.physical_inventory` exactly for arc 1.

#### Arc 2 (ep2, attempt_key `s2:ep2:arc2:a1:20260408_161433`, candidate `creative`)

| Field | Sink value | Artifact value | Match |
|---|---|---|---|
| start_location | 장례식장 지하 1층 의전팀 임시 사무실 | `arc_start_state.location` identical | ✓ |
| end_location | 장례식장 지하 1층, 3번 화물 게이트 앞 임시 관제 구역 | `arc_end_state.location` identical; `joint_docs.final_location` identical | ✓ |
| start_inventory_count | 3 | (carries arc1 end) | ✓ continuity |
| end_inventory_count | 5 | `joint_docs.physical_inventory` length = **5** | ✓ |
| start_total_assets | 500만원 + 장례식장 뒷문 운영권 | `arc_start_state.total_assets` identical | ✓ |
| end_total_assets | 2억 500만원 + 장례식장 뒷문 운영권 | `arc_end_state.total_assets` identical | ✓ |
| start_capital | 0원 | `arc_start_state.capital` = 0원 | ✓ |
| end_capital | 2억원 | `arc_end_state.capital` = 2억원 | ✓ |
| start_portfolio_position | 제로라인파트너스 지분 100% (장례식장 임시 운영권 보유) | identical | ✓ |
| end_portfolio_position | 제로라인파트너스 지분 100% (현금 2억원, 장례식장 임시 운영권 보유) | identical | ✓ |
| continuity_checkpoint_count | 3 | `semantic_carryover.continuity_checkpoints` len = 3 | ✓ |

`end_inventory_preview` on all sinks lists only 3 items (`결제 기능 정지된 법인카드`, `제로라인파트너스 명의 임시 운영 총괄 책임 위임 계약서`, `의전팀 연락망 동기화된 구형 스마트폰`); the artifact `physical_inventory` contains two additional real items (`태블릿 PC`, `한유림의 자필 메모 ...`). Count is preserved; preview is truncated.

#### Arc 3 (ep3, attempt_key `s2:ep3:arc3:a1:20260408_161433`, candidate `conservative`)

| Field | Sink value | Artifact value | Match |
|---|---|---|---|
| start_location | 장례식장 지하 1층, 3번 화물 게이트 앞 임시 관제 구역 | `arc_start_state.location` identical | ✓ |
| end_location | 새롭게 분리된 일반 조문객 셔틀버스 승강장 | `arc_end_state.location` identical; `joint_docs.final_location` identical | ✓ |
| start_inventory_count | 5 | (carries arc2 end) | ✓ continuity |
| end_inventory_count | 8 | `joint_docs.physical_inventory` length = **8** | ✓ |
| start_total_assets | 2억 500만원 + 장례식장 뒷문 운영권 | `arc_start_state.total_assets` identical | ✓ |
| end_total_assets | 1억 500만원 + 장례식장 운영권 일체 | `arc_end_state.total_assets` identical | ✓ |
| start_capital | 2억원 | `arc_start_state.capital` = 2억원 | ✓ |
| end_capital | 1억원 | `arc_end_state.capital` = 1억원 | ✓ |
| start_portfolio_position | 제로라인파트너스 지분 100% (현금 2억원, 장례식장 임시 운영권 보유) | identical | ✓ |
| end_portfolio_position | 제로라인파트너스 지분 100% (현금 1억원, 장례식장 운영권 일체 보유) | identical | ✓ |
| continuity_checkpoint_count | 3 | `semantic_carryover.continuity_checkpoints` len = 3 | ✓ |

Both `start_inventory_preview` and `end_inventory_preview` list only 3 items (same first-three trio as arc 2); the artifact `physical_inventory` holds 8 real items (adds `태블릿 PC`, `한유림의 자필 메모 ...`, `장례식장 외부 교통 관제권 계약서 (48시간)`, `서도윤이 뒤섞은 VIP 번호표 사진`, `수기로 수정한 셔틀 회차 시간표 ...`). Count preserved; preview truncated.

### 2.4 Cross-arc handoff continuity

| Boundary | arc N end | arc N+1 start | Match |
|---|---|---|---|
| arc1 → arc2 | location = 장례식장 지하 1층 의전팀 임시 사무실; inv_count=3; capital=0원; total_assets=500만원 + 장례식장 뒷문 운영권; portfolio=지분 100% (장례식장 임시 운영권 보유) | identical | ✓ all fields |
| arc2 → arc3 | location = 장례식장 지하 1층, 3번 화물 게이트 앞 임시 관제 구역; inv_count=5; capital=2억원; total_assets=2억 500만원 + 장례식장 뒷문 운영권; portfolio=지분 100% (현금 2억원, 장례식장 임시 운영권 보유) | identical | ✓ all fields |

No numeric or string contradictions at either boundary. `investment_calc_final_total_assets` and `investment_calc_final_cash` are consistent across the handoffs (5,000,000→205,000,000→105,000,000 for total; 0→200,000,000→100,000,000 for cash), which align with the narrative "1억원 소모" between arc 2 and arc 3.

## 3. Mismatches or blanks

- **No blanks** on the canonical carryover authority fields in any of the four sinks for any of the three arcs. All three rows are present in all four sinks with identical attempt_keys and identical field values.
- **No numeric contradictions.** Every cash / total-asset / portfolio figure is consistent between (a) the artifact `state_constraints` block and (b) the four sink copies, and consistent across arc-to-arc handoff boundaries.
- **One remaining drift — preview truncation only.** The `start_inventory_preview` and `end_inventory_preview` fields are capped at 3 items in every sink (this is a log-side snapshot, not a canonical store). For arc 2 this silently hides items 4–5 (`태블릿 PC`, `한유림의 자필 메모 (EXEC-77B)`). For arc 3 it silently hides items 4–8. The underlying `*_inventory_count` is correct, and the artifact `joint_docs.physical_inventory` carries the full list, so the truncation does not corrupt downstream carryover math — it only degrades the preview string in logs and in the rendered UI event `message`.
- **`director_selections.selected_label` is empty on all three rows** (`selected_label = ''`), while `selected_strategy` is populated (`creative`, `creative`, `conservative`). This is not a carryover_authority field, but it is an adjacent minor blank in the sink that a reader of `director_selections` would notice while looking at these rows. Noted for Terminal 2 visibility.

## 4. Gap classification

| Item | Classification |
|---|---|
| Four-sink carryover authority parity (location / inventory count / capital / total_assets / portfolio / investment_calc / continuity_checkpoint_count) | **no gap** |
| arc1→arc2 and arc2→arc3 handoff continuity | **no gap** |
| Inventory preview truncated to 3 items while true count is 5 / 8 | **logging gap** — preview is a display-only snapshot; canonical count and full artifact list are intact |
| Empty `director_selections.selected_label` | **sink drift (cosmetic)** — adjacent to, but outside of, the carryover authority contract |

No evidence of an upstream semantic / runtime issue for carryover authority on this run. No evidence of operator-choice exclusion: all three arcs were executed and persisted.

## 5. Verdict

Stage2 carryover authority survives cleanly across `stage_attempts.advisory_flags`, `director_selections.advisory_warnings`, DB `ui_events`, and session `ui_events.jsonl` for all three arcs of session `20260408_161433`. All canonical fields (start/end location, inventory count, capital, total assets, portfolio position, investment calc totals, continuity checkpoint count) are byte-identical across the four sinks and match the disk artifacts. Arc-to-arc handoff is semantically clean: arc1.end ≡ arc2.start and arc2.end ≡ arc3.start on every canonical field. The only remaining drift is a **logging-only preview truncation** that caps `*_inventory_preview` at 3 items even when the true count is 5 or 8; this does not affect the canonical `*_inventory_count` nor the artifact `joint_docs.physical_inventory`, so it is not a proof-blocking issue for Stage2 carryover authority. The "DB 3 vs preview short" shape is **logging gap**, not sink drift, and almost certainly not the field that is driving `proof_digest.status = "warn"` — Terminal 1 finds no carryover-authority-side reason for that warn.
