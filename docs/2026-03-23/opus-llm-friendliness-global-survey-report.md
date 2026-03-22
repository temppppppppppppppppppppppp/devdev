Date: 2026-03-23
Status: provisional (3-pass audited, below confidence gate)
Document Type: system-track survey report
Canonical Path: `docs/2026-03-23/opus-llm-friendliness-global-survey-report.md`
Source Order: `docs/2026-03-23/opus-llm-friendliness-global-survey-order.md`
Source Orientation Pack: `docs/2026-03-23/llm-codebase-orientation-pack.md`
Source Integrity Report: `docs/2026-03-23/opus-pass-reject-logging-integrity-survey-report.md`

Commit State:
- Baseline Commit: `203b328fb35633f9a23fe986862994c8b6dddab7`

---

## 1. Executive Summary

The codebase is **navigation-ready and authority-readable** for an LLM after the long-function decomposition campaign. The orientation pack reading order is accurate and the owner/runtime/sink boundary pattern is consistent.

However, **contract readability and local readability still carry material friction** in specific areas. The top comprehension hazards are not about function length — they are about implicit data channels, mojibake, and navigational density in God Objects.

Axis-level verdict:

| Axis | Status | Confidence |
|---|---|---|
| Navigation | Ready | 90% — orientation pack is accurate; God Object file sizes still slow search |
| Authority | Readable | 92% — owner/runtime/sink boundaries are clear; `_god1_*` smuggling is the main exception |
| Contract | Partially Readable | 78% — verdict contracts are consistent; internal result schemas and parameter forwarding are not |
| Observability | Readable | 88% — sinks are traceable; single-try/except fragility creates silent loss risk |
| Local Readability | Partially Readable | 75% — mojibake, unicode escapes, and envelope/parameter proliferation are the main blockers |

---

## 2. Heatmap by Area

| Area | Nav | Auth | Contract | Observ | Read | Worst Surface |
|---|---|---|---|---|---|---|
| `main_a.py` | C | C | C | B | C | `\uXXXX` escapes, stale thin delegates, cache duplication |
| Stage 0 | A | A | B | A | A | Stale `utf8-hygiene` pragma (minor) |
| Stage 2 orchestrator | B | B | A | B | A | 142-line bootstrap no phase markers |
| Stage 2 finalizer | D | C | B | D | **F** | **Duplicate method defs + severe mojibake** |
| Stage 3 orchestrator | C | A | C | B | C | Single try/except REJECT sink; dead `_legacy` method |
| Stage 4 orchestrator | C | A | A | A | C | 25 dataclasses header wall |
| Stage 4 interview round | **E** | C | C | A | **E** | **`run()` at L2248; 140 methods no dividers; `_god1_*`** |
| Stage 4 director runtime | C | C | C | A | C | `_god1_*` getattr smuggling; string-based module lookup |
| Stage 4 post-processor | A | A | A | A | B | Early-return blast radius undocumented |
| Stage 4 post-pass runtime | C | C | D | B | C | Void atomic save; bible_delta gap; dual rollback |
| Domain: base_agent | C | B | C | B | D | `_extract_json_robust` 5-strategy cascade; lock cluster |
| Domain: chief_writer | B | C | C | B | C | 82 methods; 35-param forwarding duplication |
| Domain: four_phase_arc_runtime | C | C | D | C | C | 10 near-identical envelope dataclasses |
| Domain: director_auditor | B | B | B | B | B | V0128 config assembly (minor) |
| Validation: orchestrator | C | C | C | C | C | Tier-specific result schema inconsistency |
| Validation: continuity | B | B | B | B | C | **Mojibake in `growth_keywords` (latent bug)** |
| Persistence: db_manager | **E** | C | D | B | D | **136 methods no ToC; mixed return conventions** |
| Persistence: world_state | B | B | B | B | B | Per-section try/except boilerplate |
| Persistence: fact_ledger | A | A | A | A | A | Cleanest file in survey |

---

## 3. Top 20 Comprehension Hotspots

| # | File | Line Anchor | Axis | Sev | Description | Fix Type |
|---|---|---|---|---|---|---|
| 1 | `stage4_interview_round.py` | L2127-2133, L2146 + `stage4_director_runtime.py` L102-107 | Authority | **P0** | `_god1_*` implicit parameter smuggling: 7 attributes passed via instance mutation between two files, invisible to method signatures | comment-only (document the channel) or contract-cleanup (convert to explicit params) |
| 2 | `stage2_finalizer.py` | L1130-1173, L1250-1337 | Local Read | **P0** | Duplicate method definitions with mojibake first copies. Dead code + source corruption | boundary-refactor (delete first copies) |
| 3 | `continuity_validator.py` | L1007-1016 | Local Read | **P0** | `growth_keywords` contains mojibake (corrupted placeholder chars) — latent bug preventing personality growth detection from matching | boundary-refactor (fix strings) | <!-- utf8-hygiene: allow-line -- archival evidence of source corruption -->
| 4 | `stage3_orchestrator.py` | L2351-2496 | Observability | **P0** | `_record_stage3_failure_attempt`: single try/except over 146 lines. Any early exception silently kills all 5 REJECT sinks | boundary-refactor (split into per-sink try/except) |
| 5 | `stage4_interview_round.py` | L2248 | Navigation | **P1** | `run()` entry buried at line 2,248 in a 5,739-line file with 140 methods and zero section dividers | comment-only (add section dividers + ToC) |
| 6 | `db_manager.py` | L1-3343 | Navigation | **P1** | 136 methods in 3,343 lines with 3 section comments. Key methods (`save_manuscript`, `save_stage_attempt`) require blind scrolling | comment-only (add method-group ToC) |
| 7 | `main_a.py` | L618-632 | Local Read | **P1** | `\uXXXX` unicode escapes for Korean keyword lists — unreadable inline by any LLM | contract-cleanup (replace with literal Korean) |
| 8 | `stage4_orchestrator.py` | L225-455 | Navigation | **P1** | 25 dataclasses in 230-line preamble before the class definition. Overlapping fields across envelopes | comment-only (add grouping headers) |
| 9 | `four_phase_arc_runtime.py` | L1-135 | Contract | **P1** | 10 dataclass envelopes with 80% field overlap. Manual unpack/repack repeated 3 times | contract-cleanup (consolidate to fewer envelopes) |
| 10 | `chief_writer.py` | L566-614 | Contract | **P1** | `generate_ensemble` has 35 parameters. `patch_with_feedback` and `regenerate_with_feedback` each duplicate 30+ of them | contract-cleanup (extract request dataclass) |
| 11 | `base_agent.py` | L1771-1894 | Local Read | **P1** | `_extract_json_robust`: 120 lines mixing 5 repair strategies + recursive flattening + agent-specific regex | boundary-refactor (split per strategy) |
| 12 | `stage4_post_pass_runtime.py` | L977-989 | Observability | **P1** | `bible_delta` update failure caught locally, doesn't trigger atomic rollback. Partial state committed permanently | observability-only (add warning + `_meta_save_failed` flag) |
| 13 | `stage4_post_pass_runtime.py` | L1070-1113 | Contract | **P1** | `_save_world_state_atomic` returns void. Success/failure signaled only through exceptions caught 4 levels up | contract-cleanup (add bool return) |
| 14 | `stage01_helpers.py` | L529-534 | Navigation | **P1** | Silent choice number remapping (4→5, 5→6). Menu display ≠ handler keys | comment-only (add mapping comment) |
| 15 | `validation_orchestrator.py` | L82-181 | Contract | **P1** | Tier-specific result schemas all different (`passed`/`failures`/`violations`/`warnings` vs `unjustifiable_violations`/`score_penalty`). No unified contract doc | doc-only (add tier result schema reference) |
| 16 | `main_a.py` | L2919-2943 | Authority | **P1** | 5 thin delegates to `_stage2_orch` with names suggesting primary implementations | comment-only (mark `# [COMPAT]`) |
| 17 | `main_a.py` | L3422-3552 | Local Read | **P1** | 4 near-identical cache-invalidation blocks (~30 lines each) | boundary-refactor (extract shared helper) |
| 18 | `stage4_director_runtime.py` | L237-318 | Authority | **P1** | 3 optional validation modules discovered via string-based `get_module("...")` with zero log on `None` | observability-only (add debug log on skip) |
| 19 | `base_agent.py` | L163-192 | Local Read | **P2** | 10+ class-level mutable state fields with 3 locks. No grouping comment explaining which lock protects which field | comment-only |
| 20 | `main_a.py` | L2755-2774 | Contract | **P2** | Shutdown sequence: 9 ordered steps with no phase-boundary comments | comment-only |

---

## 4. Quick Wins

### Comment-Only (no code change beyond comments)

| Target | Action |
|---|---|
| `stage4_interview_round.py` | Add `# ═══════` section dividers: imports/dataclasses, init, utility, run+phases, verdict, advisory chain, metrics |
| `db_manager.py` | Add method-group ToC comment at top: Read/Write/Migration/Lifecycle sections with line ranges |
| `stage4_orchestrator.py` L225 | Add grouping headers before dataclass families: Session, Round, Episode, V75 |
| `stage01_helpers.py` L529 | Add `# NOTE: menu choice 4→handler 5, choice 5→handler 6 (remapped for legacy compat)` |
| `main_a.py` L2755 | Add `# Shutdown Phase 1: metrics / Phase 2: cost / ... / Phase 9: close` comments |
| `main_a.py` L2919 | Add `# [COMPAT] thin delegate — authority is _stage2_orch` to each stub |
| `stage4_director_runtime.py` L237 | Add `# NOTE: returns None if module not configured; skip is silent by design` |
| `stage4_post_pass_runtime.py` L1070 | Add docstring: "Void return. Raises on failure → caught by _handle_atomic_metadata_failure" |
| `base_agent.py` L163 | Add grouping comment: "# --- Key rotation state (protected by _rotation_lock) ---" etc. |
| `stage4_post_processor.py` L905 | Add `# WARNING: early return here skips sinks 2-7. Manuscript already saved.` |

### Doc-Only

| Target | Action |
|---|---|
| Orientation pack §5.2 | Add tier-result schema reference for validation_orchestrator |
| Orientation pack §4 | Note `_god1_*` channel between interview_round and director_runtime |

### Observability-Only

| Target | Action |
|---|---|
| `stage4_director_runtime.py` L265-318 | Add `logging.debug("Module %s not configured, skipping", name)` for each `None` module |
| `stage4_post_pass_runtime.py` L987 | Add `self._meta_save_failed = True` after bible_delta update failure |

---

## 5. Boundary Refactor Candidates

These require code changes beyond comments. Ordered by ROI.

| # | Target | Action | Blast Radius | Orientation-Pack Impact |
|---|---|---|---|---|
| 1 | `stage2_finalizer.py` L1130-1337 | Delete first (mojibake) copies of 2 duplicate methods | None — Python already uses second copy | No |
| 2 | `continuity_validator.py` L1007-1016 | Fix `growth_keywords` mojibake to correct Korean strings | None — restores intended functionality | No |
| 3 | `stage3_orchestrator.py` L2351-2496 | Split `_record_stage3_failure_attempt` into per-sink try/except | None — same sinks, better isolation | No |
| 4 | `main_a.py` L618-632 | Replace `\uXXXX` escapes with literal Korean | None — identical runtime behavior | No |
| 5 | `main_a.py` L3422-3552 | Extract shared cache-invalidation helper | Low — internal to SovereignApp | No |
| 6 | `stage4_post_pass_runtime.py` L1070 | Add `bool` return to `_save_world_state_atomic` | Low — callers already handle via exception | No |

---

## 6. Orientation Pack Refresh Candidates

| Item | Current State | Recommended Update |
|---|---|---|
| `_god1_*` implicit channel | Not mentioned | Add to §4.5 Stage 4 Authority: "7 attributes smuggled via instance mutation between `stage4_interview_round.py` and `stage4_director_runtime.py`" |
| Tier result schemas | Not mentioned | Add to §5.2 Verdict Contracts: "Internal tier results use tier-specific schemas; see `validation_orchestrator.py` L82-181" |
| Stage 2 finalizer mojibake | Covered in integrity report but not orientation pack | Add to §10 Known Limits: "stage2_finalizer.py contains duplicate method definitions with mojibake first copies (dead code)" |

---

## 7. No-Action / Settled Areas

| Area | Reason |
|---|---|
| `fact_ledger.py` | Cleanest file. Schema docstring, consistent contracts, good section dividers |
| `stage0/__init__.py` | Well-structured after refactor. Section comments present. Authority clear |
| `stage4_post_processor.py` | Clear single entry, bool return, good error handling |
| `stage2_validation_pipeline.py` | All sinks reachable, advisory downgrade pattern consistent |
| `stage2_preflight_runtime.py` | Settled per TF audit — thin entry shells, runtime authority clear |
| `stage4_retry_runtime.py` | Settled — dedicated retry authority |
| `stage4_reject_runtime.py` | Settled — dedicated reject authority |
| `stage4_context_packets.py` | Settled — dedicated packet rendering |
| `db_bootstrap_runtime.py` | Settled — bounded schema bootstrap |
| `three_phase_blueprint_runtime.py` | Settled after T432 — `generate()` is 84 LOC shell |
| `director_auditor.py` | `audit_manuscript` shell is clean after decomposition |
| `world_state.py` `update_from_state_changes` | 41 LOC shell over 5 numbered family helpers |
| All 11 runtime modules | Cohesive authority, reasonable size, section comments present |

---

## 8. Confidence and Limits

**Overall confidence: 88%**

Breakdown:
- Navigation axis: 90%. Orientation pack reading order confirmed accurate. God Object file sizes remain the main navigation cost but are documented.
- Authority axis: 92%. Owner/runtime/sink boundaries are clear in all inspected files. `_god1_*` is the sole systematic authority gap.
- Contract axis: 78%. Verdict contracts (`final_verdict`, `gate_basis`, `score`) are consistent. Internal envelopes, parameter forwarding, and tier-specific result schemas are not.
- Observability axis: 88%. Sinks are traceable. Single-try/except fragility (Stage 3 REJECT, post-pass bible_delta) creates bounded silent-loss risk.
- Local readability axis: 75%. Mojibake (stage2_finalizer, continuity_validator), unicode escapes (main_a), and dataclass/parameter proliferation (four_phase_arc_runtime, chief_writer) are the main friction sources.

**Limits:**
- This survey is static-only. No fresh run was executed during this pass.
- `stage4_interview_round.py` internal method interactions were sampled, not exhaustively traced (5,739 lines, 140 methods).
- `scripts/` directory was excluded per the survey order scope.
- The `modules/api/bridge_server.py` was only lightly touched by one agent; deep analysis may find additional surfaces.

---

## 9. 3-Pass Audit Record

### Pass 1 — Structure and Scope
- All 5 required axes evaluated
- Every P0/P1 item has file path and line anchor
- Every recommendation has a fix type
- Orientation-pack-impacting items separated in §6
- No-action list produced in §7
- PASS

### Pass 2 — Evidence and Consistency
- Hotspot rankings cross-checked against all 3 parallel agent reports
- No contradiction between agent findings
- Mojibake findings corroborated by multiple agents independently discovering the same files
- `_god1_*` finding confirmed by both Stage 4 agents from different entry points
- Severity assignments consistent: P0 = causes wrong edits or silent data loss; P1 = slows work; P2 = cleanup
- PASS

### Pass 3 — Readability and Operational Use
- Executive summary answers all 5 primary questions from the survey order
- Heatmap is scannable by area
- Quick wins are actionable without opening new refactor waves
- Boundary refactor candidates have explicit blast radius assessments
- Report does not recommend reopening the long-function campaign
- PASS

### Confidence Gate
- Estimated confidence: 88%
- Threshold: 95% required for final-save implementation guidance. This report remains provisional until fresh-run evidence or re-audit lifts confidence above the gate.
- The 12% gap is from: no fresh run evidence (8%), incomplete `stage4_interview_round.py` internal trace (3%), `bridge_server.py` light coverage (1%).

