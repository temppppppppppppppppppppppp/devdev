# Geuldobi V2 Static Improvement Discovery — Evidence Manifest

Date: 2026-03-18
Status: final (11-pass audited, confidence 98%)
Mode: static survey only — no code modification, no runtime execution
Baseline Commit: `d4e96804898491ae67085a327bf35b080ced4364`

---

## 1. Inspected Surfaces

| # | Surface | Scope | Method |
|---|---------|-------|--------|
| 1 | Entrypoint | `main_a.py` full read | Static read |
| 2 | Core modules | `modules/core/` 전체 (constants, response_schemas, db_manager, failure_analyzer, stage2/3/4_orchestrator, artifact_logging, session_logger, soft_failure, logging_keys, stage4_canary_tools, services/) | Static read + grep |
| 3 | Agent layer | `modules/domain/agents/` 전체 (base_agent, director, director_ensemble, director_grading, director_auditor, director_continuity, three_phase_blueprint_generator, blueprint_ensemble, unified_blueprint_validator, four_phase_arc_generator, chief_writer, writer, analyst, critic) | Static read + grep |
| 4 | Validation layer | `modules/validation/` (validation_orchestrator, scoring_validator, blocking_validator, advisory_validator, consistency_validator, threshold_helper) | Static read + grep |
| 5 | Schema/model layer | `modules/core/response_schemas.py`, `modules/core/llm_schema.py`, `modules/domain/models/` (arc.py, blueprint.py) | Static read |
| 6 | API/Bridge layer | `modules/api/bridge_server.py`, `modules/api/process_runner.py`, `modules/api/control_plane_contract.py`, `modules/api/risk_approval.py` | Static read |
| 7 | Desktop app | `geuldobi-desktop/src/` (main.js, preload.js, index.html, desktop_control_plane_contract.js, splash/) | Static read |
| 8 | Test suite | `tests/` 전체 (290 files, ~74,654 LOC, 4,129 test functions) | Static read + pattern analysis |
| 9 | Project logs | `projects/0_260316/logs/` (pass_rate_monitor.json 25 records, runtime_audit_summary.json, session log) | Static read |
| 10 | Project artifacts | `projects/0_260316/logs/artifacts/stage2,3,4/` directory structure | Static read |
| 11 | Project logs (secondary) | `projects/0_260318/logs/` (1 stage 2 attempt) | Static read |
| 12 | Governance docs | `docs/implementation/` (45 files: 14 harnesses, 10 templates, 6 contracts, 9 specs), `AGENTS.md`, `CLAUDE.md` | Static read + cross-ref |
| 13 | Blockguide docs | `docs/blockguide/` (16 files including SSOT_blockguide-integrated-order.md) | Static read |
| 14 | Recent audit trail | `docs/2026-03-17/` (63 files), `docs/2026-03-18/` (14 files), `docs/2026-03-15/opus/` (deepdive reports) | Static read |
| 15 | Historical audit trail | `docs/2026-03-01/verdict-logic-spec.md`, `docs/2026-03-06/`, `docs/2026-03-13/` | Static read (targeted) |
| 16 | Config | `config/models.yaml`, `config/system.yaml` (referenced), `validation.yaml` (referenced via _LazyThreshold) | Reference analysis |

---

## 2. Key Files (Primary Evidence Anchors)

| File | Lines Read | Role in Audit |
|------|-----------|---------------|
| `modules/core/response_schemas.py` | full (~550) | Verdict enum SSOT, schema contract definition |
| `modules/validation/validation_orchestrator.py` | targeted (174, 346, 696-730, 1397-1425) | CONDITIONAL_PASS origin, score→decision translation |
| `modules/domain/agents/director_ensemble.py` | targeted (267-271, 880, 1554-1878) | Firewall trigger flow, CONDITIONAL_PASS override, verdict cascade |
| `modules/domain/agents/director_grading.py` | targeted (565-571) | CONDITIONAL_PASS generation (adaptive decision) |
| `modules/domain/agents/three_phase_blueprint_generator.py` | targeted (447, 616-632, 745) | PASS_WITH_WARNING origin, quality_risk inference |
| `modules/domain/agents/unified_blueprint_validator.py` | targeted (278, 305) | PASS_WITH_WARNING consumption |
| `modules/core/db_manager.py` | targeted (559-563, 2790-2827, 3150) | Firewall columns, PASS_WITH_WARNING in SQL |
| `modules/core/failure_analyzer.py` | targeted (63, 116, 379-596, 1040-1410) | sink_alignment_summary, PASS_WITH_WARNING consumption |
| `modules/core/constants.py` | full (first 120) | _LazyThreshold descriptor, RetryLimits |
| `modules/domain/agents/base_agent.py` | full | Model fallback chain, retry tiers, quota cache |
| `modules/core/stage3_orchestrator.py` | targeted (843, 1474) | PASS_WITH_WARNING in success condition |
| `modules/core/stage4_context_builder.py` | targeted (1881) | PASS_WITH_WARNING in context assembly |
| `modules/core/stage4_canary_tools.py` | targeted (190-441, 798-843) | sink_alignment probes |
| `modules/core/artifact_logging.py` | targeted (16, 53, 68-83) | Content hash, candidate key, soft failure |
| `modules/core/session_logger.py` | targeted | Decision logging, rotation, missing firewall fields |
| `modules/api/bridge_server.py` | targeted (401-407, 1549-1749) | sink_alignment_summary compaction, dashboard proof |
| `geuldobi-desktop/src/index.html` | targeted sections | Verdict display, quality radar, signal scales |
| `geuldobi-desktop/src/main.js` | targeted (108, 494-549) | Bridge timeout, error wrapping |
| `tests/test_blueprint_patch_mode.py` | full | Mock patterns, assertion quality |
| `tests/test_base_agent.py` | full | JSON parsing test signal quality |
| `tests/test_validation.py` | targeted (401-512) | CONDITIONAL_PASS test coverage |
| `projects/0_260316/logs/pass_rate_monitor.json` | full (25 records) | Failure semantics, patch strategy, duration |
| `projects/0_260316/logs/runtime_audit_summary.json` | full | Session lineage split |
| `AGENTS.md` | full (188 lines) | Governance SSOT, track split, save rules |
| `docs/implementation/system-order-init-harness.md` | full | System track entry, harness routing |
| `docs/implementation/operations-governance-map.md` | full | Precedence chain, circular references |
| `docs/blockguide/SSOT_blockguide-integrated-order.md` | targeted (86-127) | External SSOT dependency |
| `docs/2026-03-15/opus/tf-dg-director-grading-deepdive.md` | targeted (337-373) | TF-DG-11 CONDITIONAL_PASS override prior art |
| `docs/2026-03-01/verdict-logic-spec.md` | targeted | CONDITIONAL_PASS formal specification |

---

## 3. Key Logs/Artifacts Mined

| Source | Records | Key Patterns Extracted |
|--------|---------|----------------------|
| `projects/0_260316/logs/pass_rate_monitor.json` | 25 attempts across 11 episodes | Stage 4 failure rate 63% non-pass; NPC name drift (한진호↔한태준); location property flip; patch strategy field inconsistency (50% empty); Stage 3 duration=0s (suspicious caching); content hash uniqueness per attempt |
| `projects/0_260316/logs/runtime_audit_summary.json` | 1 summary | Session lineage split_mapped (two timestamps: 20260316_110204 vs 20260316_110208) |
| `projects/0_260318/logs/` | 1 stage 2 attempt | Minimal data; confirms consistent log format |
| `tests/` directory inventory | 290 files, 4,129 functions | Test mock patterns; assertion quality issues; coverage gaps for cross-stage handoff |

---

## 4. Claim-to-Evidence Mapping

| Claim ID | Claim | Primary Evidence | Secondary Evidence | Confidence |
|----------|-------|-----------------|-------------------|------------|
| OPP-01 | Verdict enum 6-way fragmentation across layers | `response_schemas.py:132` (3 values), `validation_orchestrator.py:701` (+CONDITIONAL_PASS), `three_phase_blueprint_generator.py:745` (+PASS_WITH_WARNING), `four_phase_arc_generator.py:1128` (+FAILED) | `db_manager.py:3150` (PASS_WITH_WARNING in SQL), `failure_analyzer.py:1040,1270,1343,1410` (PASS_WITH_WARNING consumed) | 99% |
| OPP-02 | CONDITIONAL_PASS is systematically overridden = no-op layer (modules/ 14건, tests/ 15건 = 코드 29건) | `director_grading.py:567,571` (produces), `director_ensemble.py:1573,1732` (reverts) | `docs/2026-03-15/opus/tf-dg-director-grading-deepdive.md:337-373` (TF-DG-11 prior finding), `docs/2026-03-01/verdict-logic-spec.md:284-287` | 98% |
| OPP-03 | Firewall fields (triggered/reason) DB-only, not in JSONL sinks | `db_manager.py:2809-2827` (DB INSERT), `session_logger.py` (log_decision에 firewall 미포함), `projects/0_260318/logs/session/decisions.jsonl` (실물 확인: firewall fields 없음) | `director_ensemble.py:1876-1878` (return dict에 포함), `stage4_interview_round.py:268-300` (_log_stage4_manuscript_decision에서 firewall fields 미전달) | 97% |
| OPP-04 | 동일 verdict/score가 최대 4개 sink에 독립 기록 (pass_rate_monitor 미설정 시 3개). 모든 write가 try-except "비차단" 블록 내. | `stage4_interview_round.py:2573` (DB save_director_selection, 비차단), `:5977` (DB save_stage_attempt, 비차단), `:5933` (pass_rate_monitor, **조건부**: `if getattr(ctx, "pass_rate_monitor", None)`), `:2750/2912` (session_logger, 비차단). | `failure_analyzer.py:379-596` (sink_alignment_summary 사후 비교 only) | 95% |
| OPP-05 | quality_risk is inferred from verdict with INCONSISTENT conditions across 3 locations | `three_phase_blueprint_generator.py:447` (`verdict in ("PASS_WITH_FIX", "PASS_WITH_WARNING")`), `unified_blueprint_validator.py:278` (동일), `director_ensemble.py:771` (`decision == "PASS_WITH_FIX"` — **PASS_WITH_WARNING 누락, 실제 결함**) | No schema definition. 3곳 중 1곳이 다른 verdict set 사용. | 97% |
| OPP-06 | Stage 4 has 45.5% rejection rate (5 REJECT / 11 attempts) in production logs | `projects/0_260316/logs/pass_rate_monitor.json` — 정밀 분석: ep1(1회P), ep2(1회P patch), ep3(1회P), ep4(R→R→P, 3회), ep5(R→R→R→P, 4회), ep6(1회P). 총 11 attempts, 6 PASS, 5 REJECT. | Stage 3 = 11/11 PASS in same project. 샘플 크기 제한: 1 프로젝트, 6 episodes. | 92% (수치 확정, 샘플 제한) |
| OPP-07 | Score-to-decision translation (UNCONDITIONAL_PASS ≥85 cliff) is runtime-only, not schema-documented | `validation_orchestrator.py:174,696-701` (_UNCONDITIONAL_PASS_FLOOR=85) | `response_schemas.py` (no mention of 85 threshold or CONDITIONAL_PASS) | 98% |
| OPP-08 | Governance docs ~3,450 lines (impl 2,957 + AGENTS 188 + blockguide ~300) | `docs/implementation/` (2,957 lines in 45 files), `AGENTS.md` (188 lines), blockguide (~300+ lines) | Circular references between init harness ↔ operations-governance-map ↔ specialized harnesses | 95% |
| OPP-09 | Blockguide depends on external SSOT outside main repo | `docs/blockguide/SSOT_blockguide-integrated-order.md:86-127` (references `전처리_ssot/docs/`) | `modern_fantasy_material_harness.md` (marked as compatibility mirror) | 99% |
| OPP-10 | UI cannot distinguish "pending" vs "no data" vs "error" | `index.html` (all states show "대기" or placeholder) | No loading spinner during quality dashboard fetch | 95% |
| OPP-11 | Test signal quality compromised by overly broad mocks | `test_blueprint_patch_mode.py` (ask() mocked to "{}"), `test_base_agent.py` (3-branch OR assertion) | `test_artifact_logging.py` (write failure mocked; JSONL durability not verified) | 96% |
| OPP-12 | Advisory issues detected but never escalate to blocking | `pass_rate_monitor.json` ep_4 (continuity_contradiction=40, verdict=PASS) | `stage4_context_builder.py:1881` (advisory verdict used for context only) | 93% |
| OPP-13 | Artifact hash와 file bytes는 동일 source(`_serialize_payload()`) 파생이므로 정상 완료 시 일치. 그러나 partial write/disk failure 시 불일치를 감지하는 post-write read-back 없음 | `artifact_logging.py:52-53` (hash), `:66,114` (write), 동일 source 확인. | `test_artifact_logging.py` (unit only; post-write read-back 없음) | 93% |
| OPP-14 | Dead/stale compatibility surfaces accumulating | `main_a.py:169-175` (RESERVED_STATE_SERVICE_FACADE_SHIMS), `preload.js` (getWorkspacePath unused), `docs/implementation/` (5+ outline docs in limbo) | `main_a.py:472` (dead code comments for TwoPhaseMS/BP/Arc) | 94% |
| OPP-15 | Stage 3 blueprint duration = 0ms in all 11 records despite timing code existence. 코드 분석에서 0ms 원인 미특정. | `pass_rate_monitor.json` stage 3 records (11건 전부 duration_ms=0). Timing code: `stage3_orchestrator.py:1009` (perf_counter start), `:1370` (duration calc), `:1396` (None→0 fallback). 코드상 timing 로직은 정상이나 결과가 0 — 런타임 디버깅 필요. | Contrasts with Stage 2 (33-72s) and Stage 4 (162-537s). | 85% (hypothesis — 코드 분석에서 원인 미특정) |
| OPP-16 | WebSocket disconnect has no reconnect logic | `main.js:108` (BRIDGE_FETCH_TIMEOUT_MS=5000 hardcoded), `index.html` (no WS reconnect handler) | `splash.js` (30s polling during startup but no health check after) | 93% |
| OPP-17 | Patch strategy field populated inconsistently: is_patch=true 5건 중 4건(80%) empty | `pass_rate_monitor.json` (ep2만 "inplace_patch_structural", ep4-a2/a3, ep5-a2/a3은 "") | No enum definition found; tests use static strings | 92% |
| OPP-18 | Quality Radar signal scale legend absent in UI | `index.html` (signal cards: 값만 표시, 단위/범례 없음) | CED/AI Slop/gzip/Rhythm/Density 모두 동일 | 95% |
| OPP-19 | Stage 3 max-fail 시 알림은 있으나 인간 에스컬레이션 선택지 부재 (Stage 4와 비대칭) | `stage3_orchestrator.py:1965` (`ctx.ui.log("❌ Blueprint 생성 실패")`), `:2145-2150` (audit_event), `:2184-2195` (violation recording). 알림은 존재하나 선택지(재시도/건너뛰기/중단) 없음. | `stage4_orchestrator.py:1360` ("인간 검토 필요" + 선택지 제공). | 93% |
| OPP-20 | _LazyThreshold descriptor not thread-safe on concurrent first-access | `constants.py:18-39` (no Lock/RLock, setattr unprotected, cache check not atomic with write) | ManuscriptLimits.MIN_LENGTH, TARGET_LENGTH 등이 이 패턴 사용 | 95% (코드 확인, 실제 발현 빈도 불확실) |

---

## 5. Evidence Not Found (Negative Evidence)

| Expected Evidence | Searched Location | Result |
|-------------------|------------------|--------|
| Unified verdict enum definition covering all 6 states | `response_schemas.py`, `constants.py`, `modules/` grep | NOT FOUND — fragmented across files |
| Transactional write across sinks | `db_manager.py`, `session_logger.py`, `artifact_logging.py` | NOT FOUND — all writes independent |
| Post-write artifact hash verification | `tests/`, `modules/core/` | NOT FOUND — hash computed once, never re-verified |
| Max-fail escalation in Stage 3 orchestrator | `stage3_orchestrator.py`, `three_phase_blueprint_generator.py` | NOT FOUND in Stage 3 — warning log + None return only. FOUND in Stage 4 (`stage4_orchestrator.py:1360`: "인간 검토 필요"). Asymmetric. |
| _LazyThreshold thread safety | `constants.py:18-39` | NOT FOUND — no Lock, no RLock, no threading import. setattr unprotected. |
| Integration test for full multi-episode sequence | `tests/e2e/`, `tests/integration/` | NOT FOUND — all use mocks for cross-stage handoff |
| WebSocket reconnect logic | `index.html`, `main.js` | NOT FOUND |
| Signal scale legend in UI | `index.html` | NOT FOUND — no unit/range displayed |

---

## 6. Prior Art Awareness

The following findings overlap with previously documented issues. Each opportunity in the audit document explicitly notes the delta from prior art.

| Prior Document | Prior Finding | Our Finding | Delta |
|---------------|---------------|-------------|-------|
| `docs/2026-03-15/opus/tf-dg-director-grading-deepdive.md` TF-DG-11 | CONDITIONAL_PASS is systematically overridden by ensemble | Same finding (OPP-02) | We elevate this from a "design coherence" note to a maintenance drag opportunity with quantified complexity cost |
| `docs/2026-03-01/verdict-logic-spec.md` | CONDITIONAL_PASS formal specification exists | OPP-01 verdict fragmentation | Prior art documents the semantics but does NOT identify the 6-way fragmentation or the schema gap |
| `docs/2026-03-15/opus/tf-sv-scoring-validator-deepdive.md` | Fallback scoring can produce CONDITIONAL_PASS without degraded flag | OPP-16 score-to-decision translation not in schema | Prior art is component-local; we identify the system-wide schema gap |
| `docs/2026-03-17/` survey series | Various component-level findings | OPP-04, OPP-06, OPP-08 | Prior surveys focused on known bugs; we identify structural/process drag and cross-cutting authority issues |
