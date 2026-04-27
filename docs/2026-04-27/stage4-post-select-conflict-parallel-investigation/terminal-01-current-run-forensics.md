# T01 Current-Run Forensic Baseline

Track: system order
Mode: read-only forensic investigation (parallel terminal T01 of #58)
Workspace: `C:\Users\wjjo\Desktop\글도비`
Workspace anchor branch (per handoff): `run/gcp-iam-5arc-clean-proof`
Repo HEAD at investigation start: `a3d82697` (`a3d826978d530ab61d3765e5e095890fa6533ea7`)
GitHub issue: #58 `[Stage4] Reduce POST_SELECT_CONFLICT carryover drift in 5-arc runs`
Authority chain respected: AGENTS.md → init harness → live-run-merge harness → this dispatch.
Encoding: UTF-8. All evidence reads use `read_bytes()` + explicit UTF-8 decode; console rendering is treated as exploratory only per AGENTS.md Encoding Guardrails.
Save path: `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/terminal-01-current-run-forensics.md`.

## Scope

T01 establishes the factual current-run baseline behind #58 and nothing more:

- Confirm which DB / log / artifact tree the cited handoff actually points at.
- Extract the `stage_attempts` rows for Stage4 ep4–ep9 in the current live session.
- Cross-check `director_selections`, `manuscripts`, `episode_meta`, `blueprints`, `canonical_facts`, `anchors`, `context_cache_attempts`, and `llm_calls` only enough to pin who said what at which layer.
- Verify on-disk artifact existence and DB↔file hash consistency for those rows.
- Surface candidate root-cause families and explicit dependencies on other terminals.

Out of scope for T01 (handed to other terminals):

- Reading source code under `modules/` or `tests/` to map handlers (T02, T03, T04, T05, T06, T07).
- Designing concrete tests (T08).
- Walking the actual narrative truth of generated manuscripts (T09).
- Synthesis (T10).

T01 is read-only. It writes only this report. No DB write, no source/test/doc edits, no GitHub or git mutation.

## Commands / Evidence

All commands were run from the workspace root. Outputs were captured via Python with `sys.stdout.reconfigure(encoding='utf-8')` to avoid CP949 console drift; quoted byte fragments below were validated through UTF-8 byte-level decode, not console preview.

### E1 — Project anchor and live run identifiers

Source docs (read in full):

- `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md`
- `docs/2026-04-27/auto-frontier-lag-5arc-runtime-analysis-ssot.md`
- `docs/2026-04-26/frontier-lag-5arc-post-run-merge-audit.md`

The handoff names:

- target project `projects/01_골든카나리아/`,
- DB `projects/01_골든카나리아/project_data.db`,
- live run id `20260427_070602_68e560f5d2`,
- Stage attempt session id `20260427_070604`,
- explicit operator-stop after the handoff snapshot, with manifest left at `frontier_running` because of the force-stop.

DB exists at `projects/01_골든카나리아/project_data.db`, 18,427,904 bytes.

A session-named log file `session_20260427_070604.log` was not present at the path the handoff cited; structured session sinks instead live under `projects/01_골든카나리아/logs/session/` as `decisions.jsonl`, `llm_io.jsonl`, `state_changes.jsonl`, `ui_events.jsonl`. This delta is recorded as an Open Question, not as evidence of corruption.

### E2 — Manifest / worker-result / failure-digest lineage check

```text
auto_frontier_lag_harness_manifest.json
  run_id            = 20260427_070602_68e560f5d2
  status            = frontier_running                 (stale due to operator force-stop)
  reuse_reset_after_ep = 16
  reuse_db_hash_before = 8a734979bd42d069...
  reuse_db_hash_after  = 8746b339384b6817...

auto_frontier_lag_worker_result.json
  run_id            = 20260427_063608_4ae67b3b85       <-- different run_id
  status            = success
  objective_status  = failed
  objective_root_cause = stage3_strict_failure_stop
  frontier_result.arcs_advanced = 0

auto_frontier_lag_failure_digest.json
  run_id            = 20260427_063608_4ae67b3b85       <-- earlier run
  judgment          = failed
  root_cause        = stage3_strict_failure_stop
  continuity_canary_status = not_available

runtime_audit_summary.json
  tag               = stage3_complete
  timestamp         = 2026-04-27 08:37:01
  proof_digest.session_lineage.plain_log_token       = 20260427_070604
  proof_digest.session_lineage.structured_session_id = 20260427_070604
  stage4_live_session.status   = absent                (snapshot pre-Stage4)
  stage4_live_session.attempt_count = 0
```

So the harness summary triplet (worker_result, failure_digest, generated SSOT) all reference the **earlier** failed Stage3-strict run `20260427_063608_4ae67b3b85`. The actual current Stage4 evidence for #58 is in `stage_attempts` under session id `20260427_070604` and starts at `2026-04-27T08:45:18`, after `runtime_audit_summary.json` was already frozen at `stage3_complete`. The summary file is therefore stale relative to the live POST_SELECT_CONFLICT activity.

### E3 — `stage_attempts` rows by session

```text
session_id          stage  count
20260427_022220     2      2
20260427_022220     3      3
20260427_022220     4      5     <-- yesterday's Stage4 carryover history
20260427_050220     2      1
20260427_052648     2      1
20260427_052648     3      9
20260427_062407     2      1
20260427_063610     2      1
20260427_063610     3      3
20260427_070604     2      1
20260427_070604     3      12
20260427_070604     4      15    <-- current Stage4 ep4..ep9 rows
```

Window for current Stage4 attempts: `2026-04-27T08:45:18` → `2026-04-27T10:27:06`.

### E4 — Current Stage4 ep4–ep9 attempt summary (session `20260427_070604`)

```text
ep  attempts  sequence
4   2         REJECT:POST_SELECT_CONFLICT | PASS
5   2         REJECT:POST_SELECT_CONFLICT | PASS
6   4         REJECT:LOGIC_ERROR | REJECT:CONSTRAINT_VIOLATION | REJECT:POST_SELECT_CONFLICT | PASS
7   2         REJECT:POST_SELECT_CONFLICT | PASS
8   3         REJECT:POST_SELECT_CONFLICT | REJECT:POST_SELECT_CONFLICT | PASS
9   2         REJECT:POST_SELECT_CONFLICT | REJECT:POST_SELECT_CONFLICT
```

This row-for-row matches the dispatch's "Direct local evidence confirmed for dispatch" block and the handoff doc's "Current live Stage4 status after stop" list. So the dispatch's Stage4 sequence is faithful to the persisted DB at investigation time.

### E5 — Per-attempt verdict / layer / patch / gate basis

Compact extract from `stage_attempts` (15 rows, all model = `vertexai:gemini-3.1-pro-preview`, all `is_patch=1` except ep5 a2). Free-text fields are truncated; column `gate_basis` is parsed from `advisory_flags.gate_semantics.gate_basis`.

```text
ep  att  verdict  failure_category        primary_failure_layer  initial_verdict  gate_basis              dur(ms)
4   1    REJECT   POST_SELECT_CONFLICT    downstream_gate        None             post_select_conflict    454312
4   2    PASS     -                       none                   PASS             patch_reaudit_pass      337500
5   1    REJECT   POST_SELECT_CONFLICT    downstream_gate        None             post_select_conflict    300000
5   2    PASS     -                       none                   PASS             director_primary_pass   281093
6   1    REJECT   LOGIC_ERROR             director_quality       None             continuity_firewall     229313
6   2    REJECT   CONSTRAINT_VIOLATION    director_quality       None             director_primary_reject 699077
6   3    REJECT   POST_SELECT_CONFLICT    downstream_gate        None             post_select_conflict    482375
6   4    PASS     -                       none                   PASS             patch_reaudit_pass      501921
7   1    REJECT   POST_SELECT_CONFLICT    downstream_gate        None             post_select_conflict    252655
7   2    PASS     -                       none                   PASS             patch_reaudit_pass      389266
8   1    REJECT   POST_SELECT_CONFLICT    downstream_gate        None             post_select_conflict    379531
8   2    REJECT   POST_SELECT_CONFLICT    downstream_gate        None             post_select_conflict    251561
8   3    PASS     -                       none                   PASS             patch_reaudit_pass      344750
9   1    REJECT   POST_SELECT_CONFLICT    downstream_gate        None             post_select_conflict    341921
9   2    REJECT   POST_SELECT_CONFLICT    downstream_gate        None             post_select_conflict    300358
```

Two patterns are visible immediately:

1. Every `POST_SELECT_CONFLICT` row is `primary_failure_layer = downstream_gate`, `gate_basis = post_select_conflict`. ep6 a1/a2 are the only non-POST_SELECT rejects in the current session and they were stopped earlier in the chain (Director-side `continuity_firewall` and `director_primary_reject`).
2. Every successful retry in this session except ep5 a2 used `gate_basis = patch_reaudit_pass`, i.e. an in-place patch that was re-audited and passed. ep5 a2 PASSed through `director_primary_pass`. ep9 never reached either path before the stop.

### E6 — `gate_semantics` carrier on POST_SELECT_CONFLICT rejects

Each REJECT POST_SELECT_CONFLICT row carries (truncated to relevant keys):

```text
director_verdict        = PASS or PASS_WITH_FIX
final_verdict           = REJECT
runtime_route_verdict   = REJECT
verdict_contract_version= verdict-layer-v1
gate_basis              = post_select_conflict
final_judgment_authority= director_llm
runtime_gate_authority  = python_runtime_routing_gate
runtime_gate_role       = ... (truncated: routing/firewall enforcement)
authoritative_fix_scope = inplace
```

So the runtime route is intentionally downgrading a Director PASS / PASS_WITH_FIX to REJECT when a continuity hard conflict is detected post-selection, and instructing the next round to redo the work as `inplace` rather than as a local patch. This is exactly the "Conflict-first retry" string seen in `reject_reason`:

> `[Conflict-first retry] post-select hard conflict invalidated the provisional PASS. 다음 라운드는 local patch가 아니라 authoritative carryover 기준 재작성으로 처리하세요.`

That tells T01 the runtime route is doing what AGENTS.md authorizes: Director keeps narrative-quality authority, but Python-side runtime routing keeps a continuity firewall. T01 therefore does **not** classify these REJECTs as Python overriding narrative judgment.

### E7 — Cross-table verdict consistency

`director_selections` was queried for the same 15 attempt keys:

```text
matches = 15 / 15
created_at on director rows is offset roughly -8h55m vs stage_attempts.ts.
  (e.g. attempt_key s4:ep4:arc1:a1:20260427_070604:
       stage_attempts.ts        = 2026-04-27T08:45:18
       director_selections.created_at = 2026-04-26 23:44:50)
```

The 9-hour drift is consistent with one stamp using KST (UTC+9) and the other using UTC. This is an observability inconsistency, not a missing-row issue: every Stage4 attempt in the current session **does** have a director row.

Director-side verdicts on the rejected rows:

```text
ep4 a1   director PASS_WITH_FIX -> stage_attempts REJECT POST_SELECT_CONFLICT
ep5 a1   director PASS_WITH_FIX -> stage_attempts REJECT POST_SELECT_CONFLICT
ep6 a1   director REJECT        -> stage_attempts REJECT LOGIC_ERROR              (matches)
ep6 a2   director REJECT        -> stage_attempts REJECT CONSTRAINT_VIOLATION     (matches)
ep6 a3   director PASS_WITH_FIX -> stage_attempts REJECT POST_SELECT_CONFLICT
ep7 a1   director PASS_WITH_FIX -> stage_attempts REJECT POST_SELECT_CONFLICT
ep8 a1   director PASS          -> stage_attempts REJECT POST_SELECT_CONFLICT
ep8 a2   director PASS          -> stage_attempts REJECT POST_SELECT_CONFLICT
ep9 a1   director PASS_WITH_FIX -> stage_attempts REJECT POST_SELECT_CONFLICT
ep9 a2   director PASS_WITH_FIX -> stage_attempts REJECT POST_SELECT_CONFLICT
```

Eight of ten POST_SELECT downgrades occurred after a Director PASS/PASS_WITH_FIX. The other two REJECTs in this session (ep6 a1/a2) are Director-side rejects with separate failure_categories. POST_SELECT_CONFLICT in this session is therefore mechanically a downstream-gate continuity firewall, not the same path as `LOGIC_ERROR` / `CONSTRAINT_VIOLATION` / `continuity_firewall` (Director-side `director_quality`).

### E8 — `reject_reason` themes (verbatim fragments)

UTF-8 decoded, lightly trimmed:

- ep4 a1 (POST_SELECT_CONFLICT) — `[V67] History Conflict: 제4화는 제2화 및 제3화에서 이미 완료된 지시 사항(법인 설립을 위한 로펌 수배)을 마치 처음 지시하는 것처럼 중복 묘사하고 있으며, 제3화에서 설정된 엄격한 데드라인('내일 오전')을 무시하고 '며칠 뒤'로 시간적 배경을 미루는 타임라인 충돌이 발생했습니다.` (duplicated continuation beat + date drift)
- ep5 a1 (POST_SELECT_CONFLICT) — `[Continuity Conflict] 주거래 증권사 및 박성호 PB의 소속 증권사 이름이 'H&T 증권'에서 '한미증권'으로 설명 없이 변경되는 설정 충돌` (institution naming drift)
- ep6 a1 (LOGIC_ERROR) — `[A-4 continuity replay] 직전 화와 충돌하는 frontier/연속성 신호가 방화벽 REJECT로 재발했습니다. ... 도입부부터 15억 매수 지시, 박성호의 만류, 우선 회신권 요구 및 설정 과정을 처음부터 다시 반복 서술함.` (duplicated continuation beat) plus `[FACT] [수치 불일치] 원고 '15억 원의 현금' (15.0억) vs FactLedger 'capital'=23.0억`
- ep6 a3 (POST_SELECT_CONFLICT) — `[Continuity Conflict] 현재 원고는 이전 회차들에서 확립된 핵심 설정(초기 자본금 20억 원, 2006년 2월 1일 이란 핵 선언 및 첫 투자 성공)을 완전히 무시하고, 자본금을 15억 원으로 축소시키며 시간적 배경을 4월로 변경하는 등 심각한 설정 충돌` (capital regression + date drift)
- ep7 a1 (POST_SELECT_CONFLICT) — `[Continuity Conflict] 제5화에서 이미 보도되어 수익 실현의 배경이 된 이란 핵 관련 속보가 제7화에서 다시 최초 발생 사건처럼 묘사되는 치명적인 타임라인 오류 ... 증권사 명칭(H&T 증권 -> 한미증권)의 일관성 누락` (event repetition + institution naming drift)
- ep8 a1 (POST_SELECT_CONFLICT) — `'H&T 증권'으로 설정되었던 핵심 배경 장소의 이름이 현재 원고에서 '한미증권'으로 변경되어 등장하는 설정 충돌` (institution naming drift)
- ep8 a2 (POST_SELECT_CONFLICT) — `7화 엔딩에서 유가 급등을 촉발한 핵심 뉴스(나이지리아 피격 및 EIA 재고 감소)가 8화 도입부에서 '이란 우라늄 농축 재개 선언'으로 잘못 기재되는 설정 충돌` (event identity drift)
- ep9 a1 (POST_SELECT_CONFLICT) — `이전 회차(제5화)에서 2월 1일에 이미 발생하여 보도된 '이란 우라늄 농축 전면 재개' 속보가 제9화에서 2월 28일에 다시 새로운 속보로 등장하는 타임라인 및 사건 중복 충돌 ... 증권사 명칭(H&T 증권 vs 한미증권)의 혼용` (event-replay + date drift + institution drift) plus `[FACT] [수치 불일치] 원고 '원금 15억 원' vs FactLedger 'capital'=23.0억`
- ep9 a2 (POST_SELECT_CONFLICT) — `현재 원고는 이전 회차에서 이미 완료된 두 가지 행동(VIP 예외 승인선 개설, 가죽 노트에 다음 투자처 기록)을 마치 처음 수행하는 것처럼 중복 묘사하여 타임라인 및 상태 충돌` (duplicated completed actions, no successful resolution before stop)

The four bug shapes flagged in #58 (institution naming drift, duplicated continuation beats, date drift, prior-failure replay) are all empirically present.

### E9 — Persisted carryover surfaces visible to Stage4 ep5+

Pulled from `episode_meta.summary` (single-row `summary` field per ep). All rows in `episode_meta` for ep4–ep8 carry `created_at` between `2026-04-26 23:53:54` and `2026-04-27 01:15:02`, i.e. predate the current Stage4 session window (`08:45 onwards`):

```text
ep4  장소: H&T 증권 VVIP 전용 트레이딩룸                              (correct anchor)
ep5  장소: 여의도 한미증권 VIP룸                                       <-- "한미증권" already poisoned
ep6  장소: 여의도 한미증권 VIP룸                                       <-- "한미증권" persists
ep7  장소: 여의도 카페                                                 (no institution)
ep8  장소: 여의도 횡단보도                                             (no institution)
ep9  no row (no PASS persisted)
```

`canonical_facts` is a single-row anchor:

```text
fact_key = capital
fact_type = numerical
value_json = {"value": 2300000000.0, "unit": "won", "authority_scope": "carryover_baseline"}
first_ep=1, last_ep=8, confidence=confirmed
```

So `FactLedger.capital = 23억` is the persisted carryover authority, and the rejects in E8 cite that exact value.

`anchors.chain_link_5` (preserved from yesterday's PASS, used for ep5+ context) records `"location": "H&T 증권 VIP룸"` — the **correct** institution name. `anchors.chain_link_6` records `"location": "VIP룸"` (no institution). Meanwhile `episode_meta.ep5.summary` says `여의도 한미증권 VIP룸`.

This means two persisted carryover surfaces disagree about the same fact for ep5:

- `anchors.chain_link_5` ✅ `H&T 증권 VIP룸`
- `episode_meta.ep5.summary` ❌ `여의도 한미증권 VIP룸`

`canonical_facts.capital = 23억` is the only persisted economic anchor. Drafts mid-arc keep regressing to 15억 and 26억, which are stage-level outdated values. The post-select conflict explicitly cites `vs FactLedger 'capital'=23.0억`, so the runtime gate is faithfully enforcing the canonical value, but the upstream context that fed the candidate did not respect it.

### E10 — `manuscripts` table vs current Stage4 PASSes

```text
ep  size_chars  title                                        created_at
1   6445        깨어난 겨울밤                                   2026-04-26 17:46:53
2   4484        제2화: 서재에서의 선언                          2026-04-26 18:02:44
3   4977        제3화: 자산 유동화                              2026-04-26 19:16:37
4   4134        에피소드 4: 붉은 지표와 새로운 룰               2026-04-26 23:52:00
5   7221        제5화: 출격 준비                                2026-04-27 00:04:35
6   7595        제6화: 강제 진입                                2026-04-27 00:39:06
7   4666        폭풍 전야                                       2026-04-27 00:53:47
8   5104        폭발                                           2026-04-27 01:13:47
```

All `created_at` values predate the **current** session's Stage4 PASSes (08:52–10:13). The current PASS attempts produced `patched_after_fix__A_InPlace.txt` artifacts on disk but the row-level `manuscripts` content for ep4–ep8 still reflects the older drafts. This is a metadata-truth gap T01 records but does not declare a corruption finding for; T09 owns end-to-end artifact↔DB↔narrative verification.

### E11 — On-disk artifact existence and DB hash check

All 15 cited `artifact_path` files exist with non-zero size (10,757 – 18,245 bytes). Computed SHA-256 over the file bytes and compared against `stage_attempts.content_hash` (64-hex):

```text
match  ep att  verdict  category               file
True   4  1    REJECT   POST_SELECT_CONFLICT   .../ep_0004/attempt_01/rejected_best__C_balanced.txt
True   4  2    PASS     -                      .../ep_0004/attempt_02/patched_after_fix__A_InPlace.txt
True   5  1    REJECT   POST_SELECT_CONFLICT   .../ep_0005/attempt_01/rejected_best__C_narrative.txt
False  5  2    PASS     -                      .../ep_0005/attempt_02/final_manuscript__C.txt
False  6  1    REJECT   LOGIC_ERROR            .../ep_0006/attempt_01/rejected_best__B_balanced.txt
False  6  2    REJECT   CONSTRAINT_VIOLATION   .../ep_0006/attempt_02/rejected_best__C_narrative.txt
True   6  3    REJECT   POST_SELECT_CONFLICT   .../ep_0006/attempt_03/rejected_best__A_balanced.txt
True   6  4    PASS     -                      .../ep_0006/attempt_04/patched_after_fix__A_InPlace.txt
True   7  1    REJECT   POST_SELECT_CONFLICT   .../ep_0007/attempt_01/rejected_best__A_narrative.txt
True   7  2    PASS     -                      .../ep_0007/attempt_02/patched_after_fix__A_InPlace.txt
True   8  1    REJECT   POST_SELECT_CONFLICT   .../ep_0008/attempt_01/rejected_best__B_narrative.txt
True   8  2    REJECT   POST_SELECT_CONFLICT   .../ep_0008/attempt_02/rejected_best__A_narrative.txt
True   8  3    PASS     -                      .../ep_0008/attempt_03/patched_after_fix__A_InPlace.txt
False  9  1    REJECT   POST_SELECT_CONFLICT   .../ep_0009/attempt_01/rejected_best__A_tension.txt
True   9  2    REJECT   POST_SELECT_CONFLICT   .../ep_0009/attempt_02/rejected_best__B_balanced.txt
```

For the four mismatches the recorded `content_hash` is 64-hex (SHA-256 length) but is not SHA-256, SHA-1, MD5, BLAKE2b-256, or SHA-256 over `strip()`/CRLF-normalized text. So either `content_hash` is computed over a different payload (e.g. the pre-firewall candidate text, the selected text before in-place patch, or a normalized JSON envelope) or over a different bytestream than what was eventually persisted to the file. T09 / T03 are better placed to walk this; T01 records it as observed metadata-truth slack without claiming corruption.

### E12 — LLM call accounting in current session (`>= 2026-04-27T07:06:00`)

```text
model                                  calls  input_tokens   output_tokens  cached_tokens     window
vertexai:gemini-3.1-pro-preview        436    14,331,629     1,398,949      8,520,521         07:06:52..10:30:42
```

Stage4 window only (`08:45..10:30`):

```text
calls=248  cached_tokens=549,836  input_tokens=2,714,656  output_tokens=4,880,504
```

So Gemini 3.1 Pro Preview through Vertex was active throughout, and context cache was being exercised at session level (8.5M cached tokens, with Stage4 window contributing ~0.55M cached). This corroborates the handoff's "memory/cache transport is operating" framing without proving correctness.

### E13 — Recurrence vs prior runs (handoff claim sanity)

Per the handoff's comparison snapshot (cross-checked against `stage_attempts` rows for older sessions):

```text
2026-04-27 current live run (session 20260427_070604):
  ep4 -> 2 attempts to PASS
  ep5 -> 2 attempts to PASS
  ep6 -> 4 attempts to PASS
  ep7 -> 2 attempts to PASS
  ep8 -> 3 attempts to PASS
  ep9 -> 2 attempts, no PASS (operator stop)
Prior 2026-04-03 / 2026-04-20 runs cited in handoff used 4–9+ attempts per ep.
```

Bounded recovery is real: 5 of 6 episodes recovered within ≤4 attempts via the patch-reaudit path. ep9 was force-stopped before its third attempt, so the handoff's "not clean 5-arc proof" framing is preserved. T01 does not promote this run to a clean-pass claim.

## Findings

T01 records the following factual findings, ordered by confidence and bounded to the current run.

F1. The DB rows behind #58 exist as cited, in `projects/01_골든카나리아/project_data.db`, session `20260427_070604`, Stage4 ep4–ep9 inclusive, ts `2026-04-27T08:45:18`–`10:27:06`. Confidence 99%.

F2. POST_SELECT_CONFLICT in this session is mechanically a runtime downstream-gate downgrade. Director's primary verdict for 8 of 10 POST_SELECT_CONFLICT rows was PASS or PASS_WITH_FIX; the runtime continuity firewall flipped them to REJECT through `gate_basis = post_select_conflict`. The other two rejects in the session (ep6 a1, a2) are Director-side `LOGIC_ERROR` / `CONSTRAINT_VIOLATION` rejects with `gate_basis = continuity_firewall` / `director_primary_reject`. Confidence 96%.

F3. The post-select downgrade sequence is consistent with AGENTS.md authority rules: Director keeps narrative-quality authority; the runtime route enforces a continuity firewall and explicitly directs the next round to do an authoritative carryover-based rewrite, not a local patch. T01 therefore does not classify the runtime gate as overriding narrative judgment. Confidence 94%.

F4. The four bug shapes named in the dispatch are all empirically present in the current session, with verbatim evidence quoted in §E8: institution naming drift (ep5/ep7/ep8/ep9: `H&T 증권 ↔ 한미증권`), duplicated continuation beats (ep4/ep6/ep9), date / event-identity drift (ep6/ep7/ep8/ep9: 2월 1일 vs 2월 28일, EIA/나이지리아 vs 이란 우라늄 농축 등), and prior-failure replay (ep9 a2 reproduces the same continuity_conflict shape from a1). Confidence 95%.

F5. There is at least one disagreement between persisted carryover surfaces. For ep5 specifically: `anchors.chain_link_5.location = "H&T 증권 VIP룸"` (correct) but `episode_meta.ep5.summary` contains `여의도 한미증권 VIP룸` (incorrect). `episode_meta.ep5.summary` was created `2026-04-27 00:06:46`, predates the current session's Stage4 window, and was not overwritten when the current session re-PASSed ep5 at `09:04:17`. Whether downstream Stage4 context actually consumes `episode_meta.summary` is a code question for T03/T04. Confidence 92% on the persisted disagreement; ~50% on whether it is the dominant root surface.

F6. `canonical_facts.capital = 2,300,000,000 KRW` (`authority_scope = carryover_baseline`, `last_ep = 8`, `confidence = confirmed`) is the persisted economic anchor, and the runtime gate's `[FACT]` rejects cite that value verbatim. Drafts in the current session keep regressing to 15억 and 26억, both of which are stage-internal values. The runtime is enforcing the canonical anchor; the upstream context-building or candidate generation is not respecting it. Confidence 95%.

F7. `manuscripts` rows for ep4–ep8 still carry `created_at` from yesterday's earlier session and were not overwritten by the current session's Stage4 PASSes. The current PASSes wrote `patched_after_fix__A_InPlace.txt` artifacts on disk but the row-level body in `manuscripts.content` does not reflect those patched outputs. T01 flags this as a metadata-truth slack point, not a confirmed corruption. Confidence 70% on factual mismatch, 0% on causal claim — T09 owns final classification.

F8. Four of fifteen attempt rows have a `content_hash` field that does not match the SHA-256 of the on-disk artifact (ep5 a2, ep6 a1, ep6 a2, ep9 a1). The hash field length is 64 hex, consistent with SHA-256, but does not match SHA-256/SHA-1/MD5/BLAKE2b on the file bytes nor on UTF-8-stripped or CRLF-normalized text. Either the hash is taken at a different lifecycle point (pre-firewall vs post-firewall, candidate vs in-place rewrite) or over a normalized envelope. T01 flags as observability risk, not corruption. Confidence 80% on mismatch, 20% on root cause.

F9. The harness summary triplet (`auto_frontier_lag_worker_result.json`, `auto_frontier_lag_failure_digest.json`, `auto-frontier-lag-5arc-runtime-analysis-ssot.md`) is locked to the **earlier** run id `20260427_063608_4ae67b3b85` whose objective failed at Stage3-strict, and `runtime_audit_summary.json` is frozen at `stage3_complete` from `2026-04-27 08:37:01` (before Stage4 began). For #58 the authoritative attempt truth must come from `stage_attempts` + `director_selections` + `episode_production.jsonl`, not from those summary JSONs. Confidence 95%.

F10. `director_selections.created_at` runs ~9h behind `stage_attempts.ts` for the same `attempt_key`. This is consistent with one column stamping in KST (UTC+9) and the other in UTC, and every Stage4 attempt key in the current session does have a director row. T01 records as observability inconsistency, not missing data. Confidence 90%.

F11. The session-named log file `session_20260427_070604.log` cited in the handoff does not exist at the cited path. Structured session sinks live under `projects/01_골든카나리아/logs/session/{decisions,llm_io,state_changes,ui_events}.jsonl` instead. T01 does not interpret this as evidence of cleanup or tampering — only as a doc-vs-disk mismatch. Confidence 99% on the path mismatch.

F12. Bounded recovery in this session is real: 5 of 6 in-scope episodes recovered within ≤4 attempts via `patch_reaudit_pass`. This is consistent with the handoff's framing. T01 does not promote this to a clean 5-arc proof — ep9 has zero PASS and the run was force-stopped. Confidence 99% on numbers, 99% on the no-clean-proof framing.

## Root-Cause Candidates

T01 surfaces candidate root-cause families only. Each candidate is paired with the terminal that owns the deeper diagnosis. T01 does not pick a winner.

C1. **Stale persisted carryover summaries.** `episode_meta.ep5.summary` continues to carry `한미증권 VIP룸` from yesterday's run after a successful in-place rewrite today. If Stage4 context-building consumes `episode_meta.summary` for the prior episode anchor, every ep ≥ 6 that touches the institution will read the wrong name. Owner: **T03** (handoff lineage), **T04** (continuity authority), **T05** (memory side effects).

C2. **Carryover summary disagreement across surfaces.** `anchors.chain_link_5` carries `H&T 증권 VIP룸` but `episode_meta.ep5.summary` carries `한미증권 VIP룸`. Whichever surface the candidate generation reads first and treats as authoritative will determine the ep6+ candidate text. Owner: **T04** (which carrier is authoritative), **T07** (which surface ends up cached).

C3. **Outdated context cache lineage on ep5+.** Vertex `cachedContents` is heavily exercised in this session (≈0.55M cached tokens in the Stage4 window, ≈8.5M total since 07:06). If yesterday's `한미증권` context is being reused via cache without lineage invalidation tied to today's correction, every ep ≥ 6 will see the stale name even after today's in-place patch. Owner: **T07** (cache lineage and stale source suppression), **T05** (memory side effects).

C4. **Prior-failure / candidate-of-record replay.** ep9 a2's reject_reason cites the same V67 history-conflict family as ep9 a1. ep6 a3 still regressed to 자본금 15억 even after ep6 a1 / ep6 a2 had been rejected on related grounds. If retry feedback or previous-attempt hydration is leaking older failed candidates into the next prompt, prior failures can replay even when Director already issued a corrective directive. Owner: **T06** (retry hydration & prior-failure replay), **T08** (regression test design).

C5. **Post-select classifier scope.** Almost every Director PASS / PASS_WITH_FIX in the current Stage4 window was downgraded to REJECT under a single category (POST_SELECT_CONFLICT), with the actual root failures spanning institution naming, date drift, completed-event repetition, NPC drift, and FactLedger capital regression. Whether POST_SELECT_CONFLICT is over-broad or whether sub-categories are intentionally collapsed is a code question. Owner: **T02** (post-select conflict classifier and route).

C6. **Stage3↔Stage4 source lineage / blueprint hand-off.** ep5 a1's `verdict_reason` says `Blueprint의 오기로 인해 박성호 PB의 소속 증권사가 'H&T 증권'에서 '한미증권'으로 잘못 표기됨`, i.e. the Stage4 Director attributed the institution drift to a Blueprint error originating earlier. If Stage3 re-emits a blueprint that contains the wrong institution, Stage4 will inherit the drift even when its own context surfaces are correct. Owner: **T03** (Stage3-to-Stage4 handoff and blueprint lineage), **T07** (whether the blueprint went through a stale cache).

C7. **Manuscript row not refreshed on patched re-PASS.** `manuscripts` rows for ep4–ep8 retain yesterday's `created_at`, while today's PASSes wrote new `patched_after_fix` artifacts on disk. If `manuscripts.content` is treated as the authoritative previous-episode context for the next episode's Stage4, ep6+ would be reading an outdated body even after today's in-place fix. Owner: **T09** (artifact↔DB↔narrative mapping), **T03** (handoff source selection), **T06** (retry hydration).

T01 does not rule any of C1–C7 in or out.

## Regression / Test Candidates

T01 lists tripwire candidates. Final test design is **T08**'s scope; T01 does not propose final names or fixtures.

R1. **Cross-surface carryover fact agreement guardrail.** Compare `anchors.chain_link_<N>.location`, `episode_meta.ep<N>.summary`, `canonical_facts` (institution-flavored), and the most recent PASS artifact text for the same fact (institution name, capital amount, latest news event). REJECT (in test) when surfaces disagree on a value the post-select gate later cites.

R2. **Conflict-first retry replay tripwire.** Given `stage_attempts` for episode N where attempt a-th REJECT cites bug shape S, attempt (a+1) must not produce a candidate whose reject_reason cites the same shape S. Today ep9 a1 / a2 fail this tripwire.

R3. **Patched re-PASS persistence guardrail.** When a Stage4 attempt PASSes with `gate_basis = patch_reaudit_pass`, validate that `manuscripts.<ep>.content` body matches the chosen `patched_after_fix__*.txt` artifact bytes (or a documented normalization), so that the next episode's context-builder cannot read an outdated body.

R4. **Stale-cache lineage tripwire on context cache reuse.** When Stage4 uses Vertex `cachedContents` for episode N, the cache content must not contain canonical facts (institution name, capital baseline, completed events) that have been corrected since the cache was created.

R5. **Capital regression canary.** A Stage4 candidate whose draft body asserts a `capital`-class number that disagrees with `canonical_facts.capital` by ≥ 5% must be a categorized failure (not collapsed under POST_SELECT_CONFLICT) so it is visible in failure_category cardinality. Today such cases are surfaced inside `[FACT]` lines but persist under POST_SELECT_CONFLICT — the post-select bucket may be over-broad.

R6. **Director vs runtime route divergence visibility test.** Validate that whenever Director verdict ≠ runtime route verdict for the same attempt, `advisory_flags.gate_semantics.gate_basis` is recorded with a sub-cause specific enough to drive a fix. The current session already records `post_select_conflict` / `continuity_firewall` / `director_primary_pass` / `director_primary_reject` / `patch_reaudit_pass`, which is good — the regression should pin that surface so it can't regress to "REJECT" without a sub-cause.

These are tripwires for Director / operator review, not narrative pass/reject judges.

## Dependencies On Other Terminals

T01's findings cascade into the other terminals as follows:

- **T02** Post-select conflict route — needs to confirm whether POST_SELECT_CONFLICT is intentionally collapsing institution / date / event / capital / npc-drift sub-causes (C5, F4, R5) and whether the runtime-route verdict downgrade path correctly preserves Director's narrative judgment for downstream replay (F2, F3).
- **T03** Stage3-to-Stage4 handoff — needs to confirm whether Stage3 blueprint re-emission inherits stale institution names and whether Stage4 context-builder consumes `episode_meta.summary`, `anchors.chain_link_*`, blueprint envelope, or all three (C1, C2, C6).
- **T04** Continuity authority carriers — needs to confirm which carrier is authoritative when `anchors.chain_link_5` and `episode_meta.ep5.summary` disagree (F5, C2), and whether `canonical_facts.capital` is being read by the candidate generation path or only by the post-select gate (F6, C5).
- **T05** Memory and cache side effects — needs to confirm whether session/vector memory writes from yesterday's wrong-institution PASS persisted into today's session retrieval (C1, C3).
- **T06** Retry hydration and prior-failure replay — needs to confirm whether retry feedback or prior-attempt rehydration is causing ep9 a2 to inherit ep9 a1's failure shape, and whether ep6 a3 inheriting capital=15억 is a hydration vs cache vs blueprint-source regression (C4).
- **T07** Context-cache lineage — needs to confirm whether yesterday's `한미증권` context survived in the Vertex `cachedContents` cache and whether lineage invalidation is tied to today's PASS / in-place patch (C3, C6).
- **T08** Regression gap design — should design final tests for R1–R6, plus institution-naming, date-drift, completed-event-replay, and capital-regression tripwires.
- **T09** Artifact truth samples — should walk ep4–ep9 artifacts on disk against `stage_attempts`, `manuscripts`, and `episode_meta`. T01's E11 hash mismatches and F7 manuscript-not-refreshed observation are starting evidence (F7, F8).
- **T10** Synthesis — must merge T01–T09 without promoting C1–C7 to a single locked root cause until at least T03/T04/T07 return.

## Open Questions

OQ1. Is `episode_meta.summary` actually consumed as carryover context by Stage4 context-building, or only by Stage3 / observability? (T03/T04 owns; affects C1 and F5.)

OQ2. Which surface is authoritative when `anchors.chain_link_<N>.location` disagrees with `episode_meta.ep<N>.summary` for the same episode? (T04 owns.)

OQ3. Why is `manuscripts.<ep>.content` not refreshed when the current session's Stage4 ep PASSes via `patch_reaudit_pass`? Is this an `INSERT OR IGNORE` artifact or an intentional skip? (T03/T06/T09; affects C7 and F7.)

OQ4. Why do four of fifteen `stage_attempts.content_hash` values not match the SHA-256 of the on-disk artifact, while sharing 64-hex SHA-256 length? Is the hash computed on a different lifecycle slice (pre-firewall vs post-firewall, candidate vs rewrite, or normalized JSON envelope)? (T09; affects F8.)

OQ5. Where was the session-named log file `session_20260427_070604.log` cited by the handoff supposed to be written, and is that path still wired in code or is the structured session-sink layout (`logs/session/*.jsonl`) the new SSOT? (T05 / system init harness owns observability.)

OQ6. Does the 9-hour KST/UTC offset between `stage_attempts.ts` and `director_selections.created_at` reflect two sinks that should agree, or two sinks that intentionally use different time bases? (T02; affects F10.)

OQ7. Is the current Vertex `cachedContents` lineage scoped per-session, per-day, or per-correction-event? (T07.)

OQ8. Was the operator-stop after ep9 a2 a hard kill at the parent process or did the worker get a chance to flush retry directives that would have led to a third ep9 attempt under a stricter rewrite directive? (Ops; out of scope for T01 but matters for whether ep9's stuck state would have unstuck itself.)

## Closure Recommendation

T01 closes with the following posture:

- The factual baseline behind #58 is reproduced from the live workspace at `a3d82697`. The Stage4 ep4–ep9 sequence in the dispatch matches `stage_attempts` row-for-row and the four bug shapes named by #58 are empirically visible in `reject_reason` text.
- POST_SELECT_CONFLICT is mechanically a runtime continuity-firewall downgrade after Director PASS / PASS_WITH_FIX. The runtime route is doing what AGENTS.md authorizes; it is not overriding narrative judgment.
- The bottleneck is specifically that Director-side PASS does not survive the post-select continuity firewall on ep4, ep5, ep7, ep8, ep9, with bounded recovery via in-place patch on every episode except ep9 within the current run window.
- ep9 has no PASS persisted and the run was operator-force-stopped. T01 therefore does **not** claim 5-arc clean readiness, and explicitly reaffirms the handoff and PR/main sync framing that this run is not a clean 5-arc proof.
- Of the seven candidate root-cause families (C1–C7), the persisted-summary disagreement (C2 / F5), capital-regression vs FactLedger anchor (C5 / F6), and conflict-first retry replay shape (C4 / F4) are the three with the strongest direct evidence in T01's data.
- T01 does **not** recommend a code patch lane based on its own evidence alone. T03 (handoff lineage), T04 (continuity authority), and T07 (cache lineage) need to return before any source-code execution SSOT is opened. T08's regression design should consume R1–R6 as input, not as a final list.
- Until T03 / T04 / T07 return, the only T01 actions that should be considered safe are:
  - Add the cross-surface agreement guardrail (R1) to the planning queue;
  - Add the conflict-first retry replay tripwire (R2) to the planning queue;
  - Hold off restarting any 5-arc live run on `projects/01_골든카나리아/` until at least T03 + T04 + T07 close.
- T01 is read-only and complete with this report.

T01 confidence on baseline factual reproduction: 95%.
T01 confidence on root-cause direction: not finalized — deferred to T03 / T04 / T07 / T10.

## 3-Pass Save Audit

Pass 1 — Evidence coverage:

- DB read-only queries cover `stage_attempts`, `director_selections`, `manuscripts`, `episode_meta`, `blueprints`, `canonical_facts`, `anchors`, `context_cache_attempts` schema, and `llm_calls` window.
- On-disk artifact existence and DB↔file SHA-256 verified for all 15 current Stage4 attempts.
- Source docs (handoff, runtime SSOT, post-run merge audit) read in full and cross-checked against the persisted DB.

Pass 2 — Risk and authority check:

- Does not claim 5-arc readiness or clean run.
- Does not classify the runtime continuity firewall as overriding Director judgment.
- Does not promote any single candidate (C1–C7) to a locked root cause.
- Does not edit source, tests, docs (other than this report), DBs, GitHub, or git state.
- Does not let Python become the final narrative judge — runtime gate is treated strictly as a tripwire that defers final narrative judgment to Director on the rewrite round.

Pass 3 — Handoff usability:

- Each finding (F1–F12) is anchored to an evidence section (E1–E13) and labeled with confidence.
- Each candidate (C1–C7) names the terminals that own the next step.
- Open questions (OQ1–OQ8) are explicitly assigned to terminals or marked out-of-scope.
- Closure recommendation is bounded and lists which terminals must return before opening a code-fix lane.

Estimated T01 confidence at save: 95% on baseline reproduction; root-cause attribution explicitly deferred.
