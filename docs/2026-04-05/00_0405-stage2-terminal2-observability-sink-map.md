# 00_0405 Stage2 Terminal 2: Observability / Sink Map

Date: 2026-04-05
Status: final
Document Type: read-only terminal survey
Canonical Path: `docs/2026-04-05/00_0405-stage2-terminal2-observability-sink-map.md`
Parent Order: `docs/2026-04-05/00_0405-stage2-three-terminal-parallel-survey-order.md`
Evidence Base: `docs/2026-04-05/00_0405-stage2-artifact-truth-observability-evidence.json`
Track: system
Mode: read-only survey; no code patching
Confidence: `96%`
3-Pass Audit: `completed`

## 1. Coverage

### Sinks Inspected

| Sink File | Role | Lines Inspected |
|---|---|---|
| `projects/00_0405/logs/session/ui_events.jsonl` | Operator-visible telemetry (best-effort, not authoritative) | 327 records |
| `projects/00_0405/logs/runtime_audit.jsonl` | Audit-only correction trail | 13 records (4 auto-correct + 4 db_commit + 4 state_extracted + 1 final) |
| `projects/00_0405/logs/quality_metrics.jsonl` | Retrieval / coverage observation | 4 records (1 per arc) |
| `projects/00_0405/logs/metrics/metrics_20260405_101441.json` | Session-end aggregate metrics | 1 file |

### Owner Code Inspected

| File | Relevant Lines | Role |
|---|---|---|
| `modules/core/stage2_validation_pipeline.py` | L56, L143, L468-476 | Auto-correct emission to audit only |
| `modules/core/stage2_preflight.py` | L433-440, L1179-1199 | Retrieval observation recording; conditional vector log |
| `modules/core/quality_dashboard.py` | L271-322 | `record_retrieval_observation` → `quality_metrics.jsonl` only |
| `modules/core/services/audit_service.py` | L61-88 | `audit_event` → memory buffer + `runtime_audit.jsonl`; no console mirror |
| `modules/core/session_logger.py` | L1-19, L208-264 | `ui_events.jsonl` writer; docstring declares non-authoritative |
| `modules/core/prompt_builder.py` | L578-586 | State extraction event → `_audit_event` only |

## 2. Findings

### F-1. Auto-correct detail is audit-only

The four arcs each triggered `v60_25_auto_correct` events with high-signal correction reasons:

| Arc | Corrections (from `runtime_audit.jsonl`) |
|---|---|
| 1 | location sync, genre-field removal (`internal_energy`), abstract-item removal |
| 2 | `[C-1]` tactical_doc meta term, `[PATCH-B]` item disappearance repair, location rewrite (Yeouido -> Gangnam), genre-field removal |
| 3 | `[C-1]` tactical_doc meta term, `[PATCH-B]` item disappearance, location sync, genre-field removal |
| 4 | `[C-1]` tactical_doc meta term, `[PATCH-B]` item disappearance, location sync x2, location sync end |

**Console visibility**: zero. The validation pipeline at `stage2_validation_pipeline.py:468` calls `self.ctx.audit_event(...)` but does not call `self.ctx.ui.log(...)` for the individual correction items. The operator sees only the envelope messages:

- `"Pre-Director 검증 체인 시작"` (L56)
- `"Pre-Director 검증 완료 → Director 심사 대기"` (L143)

**Owner**: `stage2_validation_pipeline.py` L466-473 — the `_run_arc_mapping_and_auto_correction` method.

### F-2. Retrieval / context coverage emptiness is quality-metrics-only

All four `quality_metrics.jsonl` records show:

```
work_focus_present=false
tracking_slots_count=0
scene_engines_count=0
vector_context_chars=0
mandatory_context_chars=0
```

**Console visibility**: zero. Two reasons:

1. `stage2_preflight.py:1179` routes the observation to `quality_dashboard.record_retrieval_observation()`, which writes to `quality_metrics.jsonl` only. There is no parallel `ui.log` call for the observation payload.

2. The conditional UI line at `stage2_preflight.py:1199` — `"벡터 검색 완료 ({len(s2_vector_ctx):,}자)"` — is gated on `if s2_vector_ctx:`. Since the vector context was 0 chars across all arcs, this line was never emitted. The operator receives no signal about retrieval being empty.

**Owner**: `stage2_preflight.py` L1179-1199 (emission path) + `quality_dashboard.py` L271-310 (sink).

### F-3. State extraction truth is audit-only

`prompt_builder.py:578` emits `v60_10_state_extracted` via `_audit_event`, recording `arc_count`, `target_arc_no`, and `items_tracked`. This detail lands in `runtime_audit.jsonl` only.

The console shows status-only messages:

- `"StateExtractor 누적 상태 추출 중..."` (visible in `ui_events.jsonl` seq 257/280/303)
- `"StateExtractor 누적 상태 추출 완료"` (seq 258/281/304)

The operator sees that extraction ran, but not what was extracted or how many items were tracked.

**Owner**: `prompt_builder.py` L578-586 (emission) + `audit_service.py` L61-72 (sink).

### F-4. Post-Director sync effects are console-visible but reason-blind

After each Director PASS, the console does show:

- `"physical_inventory deterministic carryover 적용: [item list]"` (seq 270/294/317)
- `"Equipment Sync Arc N 시작 소지품 → 이전 Arc 종료 소지품으로 동기화"` (seq 271)
- `"State Sync Arc N 첫 화 시작 상태 텍스트 동기화"` (seq 272/295/318)

These are the only Stage2 data-level signals visible to the operator. They confirm that sync happened, but do not explain why the system had to sync — i.e., what the auto-corrector found wrong.

### F-5. SessionLogger classification is explicit: not authoritative truth

`session_logger.py` L12-18 docstring states:

> Session JSONL files are OPTIONAL best-effort telemetry. They are NOT authoritative truth for verdict adjudication. Authoritative truth lives in db_manager (stage_attempts, director_selections) and episode_production.jsonl.

This means `ui_events.jsonl` itself is not intended as the observability anchor. It is a replay log. The gap is not that `ui_events.jsonl` is incomplete; the gap is that the console (operator's live view) lacks the audit-level signals.

## 3. Non-Issues

### N-1. Stage1 bypass is not treated as the defect

Per order premises. The retrieval emptiness (`vector_context_chars=0`) is a factual observation, not a Stage1 bypass indictment.

### N-2. DraftValidator detail was not suppressed

The validation pipeline code does emit DraftValidator pass/fail/advisory detail to `ui.log` (L679-707). In the `00_0405` run, all arcs passed DraftValidator without CRITICAL issues, so the advisory detail was minimal. This is not a suppression; it is a clean pass.

### N-3. Director verdict is console-visible

Director PASS and score are clearly emitted in `ui_events.jsonl` (seq 269/293/316). This is working as intended.

### N-4. Session metrics summary is console-visible

The shutdown metrics report (seq 324) shows agent stats, cost, and duration. This is working as intended.

## 4. Sink Map Summary

| Signal Family | Console/UI | `runtime_audit.jsonl` | `quality_metrics.jsonl` | `metrics_*.json` |
|---|---|---|---|---|
| Director PASS/score | visible | - | - | - |
| Pre-Director chain envelope | visible (start/end) | - | - | - |
| Deterministic carryover items | visible (item list) | - | - | - |
| Equipment/State sync | visible (count only) | - | - | - |
| **Auto-correct corrections** | **not visible** | **visible (full detail)** | - | - |
| **Auto-correct reasons** (genre field, PATCH-B, location rewrite) | **not visible** | **visible** | - | - |
| **Retrieval emptiness** (0 chars, no slots) | **not visible** | - | **visible** | - |
| **State extraction detail** (items_tracked, arc_count) | **not visible** | **visible** | - | - |
| DraftValidator advisory | visible (when triggered) | visible (on fail) | - | - |
| Session aggregate metrics | visible (shutdown) | - | - | visible |

## 5. Owner Verdict

The operator visibility gap has three distinct owners:

### Owner 1: `modules/core/stage2_validation_pipeline.py`

- **Gap**: Auto-correct corrections and reasons go to `audit_event` only (L468-473)
- **Why operator misses it**: The method `_run_arc_mapping_and_auto_correction` calls `self.ctx.audit_event(...)` but not `self.ctx.ui.log(...)` for correction detail
- **Severity**: HIGH — the strongest Stage2 "why did the system fix the arc" signal is invisible

### Owner 2: `modules/core/stage2_preflight.py`

- **Gap**: Retrieval observation goes to `quality_dashboard` only (L1179-1197); the "벡터 검색 완료" console line is conditional on non-empty context (L1198-1199) and was never emitted
- **Why operator misses it**: Empty retrieval silently produces no console output
- **Severity**: MEDIUM — retrieval emptiness should at minimum produce a warning, not silence

### Owner 3: `modules/core/prompt_builder.py`

- **Gap**: State extraction event goes to `_audit_event` only (L578-586)
- **Why operator misses it**: Console shows "추출 중/완료" but not what was extracted
- **Severity**: LOW — the console status messages are adequate for progress; the detail gap is lower priority than F-1 and F-2

Supporting infrastructure files that are not the gap owners but shape the sink topology:

- `modules/core/services/audit_service.py` — defines `audit_event` as buffer + file, not console mirror
- `modules/core/quality_dashboard.py` — defines `record_retrieval_observation` as file-only
- `modules/core/session_logger.py` — defines `ui_events.jsonl` as best-effort telemetry

## 6. Minimal Next Wave

If this survey is later promoted to realization, the smallest bounded fix set is:

1. **stage2_validation_pipeline.py L466-473**: Add a console mirror for auto-correct correction summary (e.g., `ui.log(f"🔧 [AutoCorrect] {len(corrections)}개 수정: {corrections[:3]}")`)
2. **stage2_preflight.py L1198-1199**: Invert the conditional — emit a warning when `s2_vector_ctx` is empty (e.g., `ui.log("⚠️ [Retrieval] Stage2 벡터 컨텍스트 없음 (0자)")`)
3. **prompt_builder.py L578**: Optional — add `items_tracked` count to the existing StateExtractor console line

This is a 3-file, ~10-line patch. It does not require structural changes to the sink architecture.

## 7. Stop

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-05 output

## 8. 3-Pass Audit Note

Pass 1:

- traced all emission points in the five owner files against the four sink files
- mapped which signals reach console vs which are audit-only or quality-metrics-only
- confirmed auto-correct, retrieval, and state extraction are the three invisible signal families

Pass 2:

- re-checked that DraftValidator visibility is not a gap (it is conditional on advisory issues existing)
- re-checked that the "벡터 검색 완료" silence is due to the `if s2_vector_ctx:` guard, not a bug
- confirmed `session_logger.py` docstring explicitly classifies ui_events as non-authoritative

Pass 3:

- validated the sink map table against every signal family
- confirmed the three owner files and their specific line ranges
- confirmed the minimal next wave is bounded and does not require sink architecture changes
