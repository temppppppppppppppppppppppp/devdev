# T10. Stage3 → Stage4 Handoff + Stage4 Writer Smarts Audit

- Parent Order: `docs/2026-04-13/s2-s3-s4-runtime-improvement-10-terminal-parallel-investigation-order.md`
- Terminal: T10
- Date: 2026-04-13
- Mode: survey-only, read-only, parallel
- Baseline Commit (at spawn): `32d6f0c8b56898fd8a370ae13684043d4cfda91a`
- Baseline Dirty Summary: dirty — `M` on `0_temp.txt`, `config/models.yaml`, `config/prompts/ensemble.yaml`, `modules/core/response_schemas.py`, `modules/core/scene_obligation_heuristics.py`, `modules/domain/agents/arc_ensemble.py`, `blueprint_ensemble.py`, `chief_writer.py`, `three_phase_blueprint_runtime.py`, runtime logs + db, several tests; untracked 2026-04-13 docs and a fresh `metrics_20260413_194343.json`. Workspace matches the `32d6f0c8` anchor declared in §4 of the parent order.
- Resume Commit: `32d6f0c8b56898fd8a370ae13684043d4cfda91a` (same — no drift)
- Resume Drift Summary: none (no new commits during T10 run)
- Side-Effect Coverage: `read-only static + frozen live-run artifact reads; no mutation` (only `git rev-parse HEAD`, `git status --short`, `sqlite3 file:...?mode=ro`, `Read`/`Grep`/`Glob`)
- Confidence: `96%`

## Purpose

> given that Stage3 often closes as `PASS_WITH_WARNING`, does Stage4 (chief writer + manuscript runtime) (a) actually rescue the remaining contract drift, (b) silently compound the drift into manuscript, or (c) reject-and-retry like Stage3 — and are the current Stage4 writer-side contract gates inside `_build_manuscript_contract_diagnostics` (`chief_writer.py:194`) and `_finalize_generate_ensemble_candidates` (`chief_writer.py:857`) strong enough to prevent downstream bleed?

## Evidence Anchors

Code (all at head `32d6f0c8`, anchored live — stale survey line numbers re-verified):

- `modules/domain/agents/chief_writer.py`
  - `_build_retry_reuse_feedback_block` at `chief_writer.py:117`
  - `_build_manuscript_contract_diagnostics` at `chief_writer.py:194`
  - `_manuscript_candidate_admission_reason` at `chief_writer.py:239`
  - `_score_manuscript_contract_diag` at `chief_writer.py:261`
  - `_qualify_manuscript_candidates_for_director` at `chief_writer.py:282` (degraded fallback path at `chief_writer.py:329-349`)
  - `_finalize_generate_ensemble_candidates` at `chief_writer.py:857`
  - `generate_ensemble` entry at `chief_writer.py:894`, finalize handoff at `chief_writer.py:1040`
  - `regenerate_with_feedback` + `_build_regeneration_feedback` at `chief_writer.py:1293/1330`
  - `_normalize_fix_pack` / `_build_fix_pack_guidance` at `chief_writer.py:1444/1506`
  - `_classify_structural_patch_focus` at `chief_writer.py:1534`
  - `_build_structural_patch_plan` / `_attempt_structural_inplace_patch` / `_resolve_inplace_patch_strategy` at `chief_writer.py:1607/1715/1876`
  - `_build_inplace_patch_prompt` at `chief_writer.py:1945`
  - `_extract_inplace_patch_payload` at `chief_writer.py:1998`
  - `_build_patch_with_feedback_section` at `chief_writer.py:2232`
  - `patch_with_feedback` at `chief_writer.py:2316`
  - `_build_retry_history_feedback` at `chief_writer.py:2382`
- `modules/core/writer_template.py`
  - `WriterTemplate.generate_template` at `writer_template.py:141`
  - `WriterTemplate.validate_against_template` at `writer_template.py:356`
  - `_template_scene_issue_required` at `writer_template.py:87`
- Stage3→Stage4 handoff surface (read to scope the T10 question — not scored as Stage3 behaviour):
  - `modules/core/stage3_orchestrator.py:2384-2431` — `blueprint["_stage3_meta"]` population: `final_verdict`, `quality_gate_failed`, `quality_risk`, `revision_required`, `last_score`, `binding_prevalidation_*`, `partial_fix_eval`, `fix_pack`, `repair_contract`, `scope_authority`
  - `modules/core/stage4_director_runtime.py:1220-1244` — `_stage3_meta` → Director advisory block (quality_risk / revision_required / binding note)
  - `modules/core/stage4_outcome_runtime.py:1041-1066` — `_stage3_meta` → v75d retry threshold drop (2 → 1) when `stage3_repair_signal=True`
  - `modules/core/stage4_post_processor.py:171` — copies `_stage3_meta` forward in post pass
  - `modules/core/stage4_context_builder.py:1957-1994` — Stage4 context builder only queries `get_stage_attempts_for_arc(..., stages=(2,), ...)` — Stage3 attempt rows are **not** pulled into Stage4 context

Live-run artifact evidence (frozen, readonly sqlite):

- `projects/000_260412_a/project_data.db` — tables `stage_attempts`, `director_selections`, `manuscripts`, `blueprints`, `attempt_raw_rationale`
- `projects/000_260412_a/logs/pass_rate_monitor.json` — 12 records
- `projects/000_260412_a/logs/runtime_audit_summary.json`
- `projects/000_260412_a/logs/artifacts/` — contains `stage2/`, `stage3/`; **no `stage4/`**
- `0_temp.txt:400-469` — Stage3 ep8 REJECT loop in flight

Per-ep Stage3 final verdict ledger (authoritative: `stage_attempts` + `pass_rate_monitor.json`, cross-checked):

| ep | Stage3 final | attempt | score | fix_scope | token_cost | duration_ms |
|----|--------------|---------|-------|-----------|-----------:|------------:|
| 1 | PASS | a7 | 92 | — | 2.25 | 1,261,839 |
| 2 | PASS_WITH_WARNING | a10 | 85 | inplace | 6.61 | 2,399,290 |
| 3 | PASS | a6 | 92 | — | 3.66 | 969,722 |
| 4 | FAILED→FAILED→PASS_WITH_WARNING | a1/a1/a6 | 0/0/85 | —/—/inplace | 3.62 (last ok) | 915,340 (last ok) |
| 5 | PASS_WITH_WARNING | a9 | 85 | inplace | 5.82 | 1,593,364 |
| 6 | PASS_WITH_WARNING | a10 | 88 | — | 6.76 | 2,264,554 |
| 7 | PASS_WITH_WARNING | a10 | 85 | inplace | 7.36 | 2,708,901 |

Per-ep Stage4 verdict: **no rows**. `stage_attempts.stage` distinct set is `{2, 3}` (no `4`); `manuscripts` table is empty (0 rows); `director_selections` rows with `stage=4` = 0; `logs/artifacts/stage4/` does not exist; `logs/pass_rate_monitor.json` carries zero `stage=4` records; `0_temp.txt` tail still shows Stage3 ep8 REJECT cycles at the moment this survey spawned.

## Findings

1. **[visibility-gap | TP]** Stage4 has **not executed even once** for the current live corpus `projects/000_260412_a/` at head `32d6f0c8`. `stage_attempts.stage DISTINCT = {2, 3}`, `manuscripts` 0 rows, `director_selections` has zero `stage=4` rows, `logs/artifacts/stage4/` does not exist, `pass_rate_monitor.json` has no `s4:*` entries, and `0_temp.txt:400-469` shows the runtime still looping on Stage3 ep8 REJECT. The §6 Required Analysis 3 matrix (Stage3 verdict × Stage4 verdict for ep1–ep7) is therefore empty: rescue/bleed/reject classification cannot be measured from current evidence. This is itself the finding — Stage3 has not handed anything off to Stage4 yet, so **every downstream claim below is code-forward only**, not artifact-validated. (anchors: `project_data.db` readonly query; `pass_rate_monitor.json`; `0_temp.txt:400-469`)

2. **[gap | TP]** `chief_writer.generate_ensemble` (`chief_writer.py:894-1046`) is **warning-blind to `_stage3_meta` on first pass**. A live grep of `chief_writer.py` for `_stage3_meta` / `stage3_meta` returns zero matches; `fix_pack` is consulted only via `previous_attempt.get("fix_pack")` inside `regenerate_with_feedback` (`chief_writer.py:1293/1330`), `patch_with_feedback` (`chief_writer.py:2316/2340`), and `inplace_patch` (`chief_writer.py:2119/2129`). For a Stage3 PASS_WITH_WARNING blueprint where Stage3 already packaged a concrete `fix_pack` / `binding_prevalidation_categories` / `quality_risk` payload at `stage3_orchestrator.py:2384-2431`, none of that structured warning vocabulary reaches the Stage4 writer prompt on the **first** Stage4 attempt — it only reaches the Director advisory text at `stage4_director_runtime.py:1220-1244`. The writer must generate blind, then wait for Director to reject, before any Stage3-origin vocabulary enters the next prompt.

3. **[gap | TP]** `_qualify_manuscript_candidates_for_director` (`chief_writer.py:282-349`) is a **soft-reorder** gate, not an admission gate. When every candidate trips `_manuscript_candidate_admission_reason`, the function falls through `chief_writer.py:329-349` to `degraded_candidates or candidates` — **nothing is actually rejected**, the degraded set is re-ordered least-bad-first and returned. `_finalize_generate_ensemble_candidates` (`chief_writer.py:857-892`) then forwards that degraded set straight to the director for scoring. If the director is distracted or the Stage3 warning is not in the director rubric, a candidate that failed every writer-side contract still survives into the manuscript sink.

4. **[gap | TP]** `_manuscript_candidate_admission_reason` (`chief_writer.py:239-258`) admission vocabulary has **zero overlap with the Stage3 reject vocabulary**. It flags only `template_contract_failed`, `scene_obligation_under_materialized:<r>/<c>`, `tail_scene_not_reflected`, and `opening_anchor_missing`. None of Stage3's recurring reject families — `opening_transition.type` mismatch, `tactical_semantic_fidelity`, `scenario_density` (anchor counts), `protagonist_state` drift, `binding_prevalidation_*` — are enumerated here, so the Stage4 writer has no language to even detect Stage3-class drift in its own candidate output.

5. **[gap | TP]** `WriterTemplate.validate_against_template` (`writer_template.py:356-406`) is a keyword-substring heuristic, not a semantic contract. Length check uses `ManuscriptLimits.MIN_LENGTH` (`writer_template.py:27`, `writer_template.py:206`), which is a Stage4 floor and does **not** inherit from the Stage3 contract's min/max. Scene materialization comes from `measure_manuscript_scene_materialization` → `_template_to_blueprint` (`writer_template.py:70-84`) → keyword match on `required_beats`. The closing-hook check (`writer_template.py:384-388`) extracts 3 × `[\w가-힣]{2,}` tokens and accepts if **any** appear in the last 600 chars; the opening-anchor check (`writer_template.py:391-395`) does the same on the first 600 chars. Three 2-char Korean tokens will fire on almost any prose, so both anchors are statistically near-always green.

6. **[leak | TP]** `_build_manuscript_contract_diagnostics` (`chief_writer.py:218-235`) derives `opening_anchor_keywords` with `re.findall(r"[\w가-힣]{3,}", template.opening_anchor)[:3]` and passes if **any** of those three tokens appears in the first 600 chars of the manuscript. When the Stage3 warning is specifically `opening_transition.type declared 'direct_continuation' vs normalized 'explicit_transition'` (a structural type mismatch — see `0_temp.txt:412-413/463-464`), the Stage4 writer-side gate cannot detect it: vocabulary-match on prior-ending tail tokens says nothing about transition **type**. The Stage4 writer therefore cannot catch the exact recurring ep8 Stage3 symptom even after Stage3 hands it off.

7. **[gap | TP]** `_build_retry_reuse_feedback_block` (`chief_writer.py:117-152`) only fires when `previous_attempt["reuse_contract"]` is a non-empty dict. There is no "forward from Stage3" equivalent — on the **first** Stage4 attempt after Stage3 PASS_WITH_WARNING, `previous_attempt` is `{}`, so `reuse_contract` is empty, so no baseline-preservation / truth-pin block is injected. The retry-time rescue lane is exclusively reactive; nothing pre-emptively carries Stage3's structured warnings into attempt 1.

8. **[gap | TP]** `_classify_structural_patch_focus` (`chief_writer.py:1534-1543`) is a hard-coded Korean-keyword keyword list for 5 focuses. Anything outside the `_STRUCTURAL_PATCH_LOCAL_HINTS` / `_STRUCTURAL_PATCH_GLOBAL_HINTS` dictionaries falls through to empty focus → `_resolve_inplace_patch_strategy` (`chief_writer.py:1876-1943`) records `fallback_reason="unclassified_feedback"` → `_attempt_structural_inplace_patch` is skipped → whole-text or LLM inplace patch. A director feedback phrased as "`opening_transition` should be `explicit_transition`, not `direct_continuation`" is not in either dictionary (no Korean keyword match) and therefore bypasses the scene-aware structural patch lane entirely — falling straight through to the heavier full-regenerate loop.

9. **[leak | TP]** `_extract_inplace_patch_payload` (`chief_writer.py:1998-2070`) hard-requires both `len(response) >= 2000` **and** the presence of a literal `[원고_끝]` end marker to return a non-None payload; otherwise the inplace patch is silently `None` and the caller drops to the whole-text rewrite fallback (`chief_writer.py:2181-2197`). A legitimate but slightly-truncated model response (token budget trim, provider timeout mid-stream) is indistinguishable from a broken output — the gate always fails closed and re-routes to the expensive path. No "salvage" lane exists.

10. **[gap | TP]** `patch_with_feedback` (`chief_writer.py:2316-2349`) fail-closes on a "non-ready fix_pack contract" when the normalized fix pack is missing **any** of `patch_targets`, `must_fix`, `do_not_regress`, `success_condition`, `target_kind`. Stage3's `_stage3_meta["fix_pack"]` (`stage3_orchestrator.py:2401-2423`) is assembled from `validate_meta.get("fix_pack")` and frequently omits one or more of those five keys — in particular `do_not_regress` is often empty for first-class opening_transition / scenario_density warnings. Result: **the `patch_with_feedback` fast-repair lane is structurally inaccessible for Stage3-origin warnings**; Stage4 can only enter `patch_with_feedback` after it has itself produced a qualifying fix_pack in a prior Stage4 attempt. This collapses one of Stage4's two documented repair lanes into "Stage4-internal only".

11. **[gap | FP-risk]** `_score_manuscript_contract_diag` (`chief_writer.py:261-279`) ranks candidates by `(-validation_issue_count, reflected_scenes, overall_ratio, tail_scene_reflected, opening_anchor_hit)`. Because issue count is a simple count of template-validation `issues`, and all four heuristics are keyword-substring (see finding 5), ties are very common. On ties the python stable sort preserves ensemble order (balanced → narrative → tension) which effectively pins `balanced` at the top. The writer-side contract gate has no semantic discriminator — it is ordering by a discrete 5-tuple that collapses to `(0, 2, 0.0, 1, 1)` for most passing candidates. Stage4 diversity measurement (`_annotate_candidate_diversity`, `chief_writer.py:513-568`) reports Jaccard but does not feed back into the score tuple, so a near-duplicate candidate family all scoring identically is routed to Director without a diversity penalty.

12. **[waste | hypothesis]** Because finding 11 collapses ties deterministically, and finding 2 shows the Stage3 warning vocabulary never reaches the writer prompt, a Stage3 PASS_WITH_WARNING blueprint on ep₍ₙ₎ will (hypothesis — unobserved) tend to produce Stage4 candidates that are near-identical in contract posture, all failing the same (Stage3-class) semantic check, all tying in the Stage4 writer-side score, and all surviving into Director evaluation. This is the theoretical "bleed" pathway. It is **unverified** at `32d6f0c8` because Stage4 has not executed (finding 1); it is logged as a hypothesis, not a measurement.

13. **[gap | TP]** `Stage4ContextBuilder._build_stage2_failure_context` (`stage4_context_builder.py:1957-1994`) pulls prior-stage failure context **only for stages=(2,)**. There is no equivalent Stage3 pull. The writer therefore learns about Stage2 arc failures via Stage4 context injection but not about Stage3 blueprint failures from the same arc or prior eps. This asymmetry is consistent with finding 2: the writer is aware of Stage2 memory but blind to Stage3 memory.

## Cross-Terminal Pointers

- **→ T5**: Whether Stage3's `opening_transition.type`, `tactical_semantic_fidelity`, `scenario_density`, `protagonist_state`, and `binding_prevalidation_*` family are calibrated correctly (true-positive vs false-positive rate) is a validator-heuristic question. T10 flags only that **Stage4 writer has no parallel gate for these families**, not whether the families themselves are sound.
- **→ T2**: Stage3 retry-time feedback fidelity (`_Stage3RepairRouter` / `_build_stage3_fix_pack_guidance` at `three_phase_blueprint_runtime.py:182/789`) is T2-owned per §8 invariant 2 and per §12 Pass-3 boundary. T10 read `_stage3_meta` **only** to understand what Stage3 hands to Stage4; T10 did not score Stage3's retry-loop composition. If the Stage3 retry loop itself is dropping fix_pack fields before they reach `_stage3_meta["fix_pack"]`, that is T2 territory.
- **→ T7**: `stage4_director_runtime.py:1220-1244` is where Stage3 warning text becomes a Director advisory block. Whether Director's rubric actually down-weights a candidate when that advisory fires is a Director/validator authority overlap question (T7-owned). T10 only observes that the writer-side gate does not also consume the same advisory.
- **→ T9**: Stage2 → Stage3 arc handoff quality drives the Stage3 PASS_WITH_WARNING rate, which drives T10's incoming pressure. If most Stage3 warnings trace back to Stage2 arc gaps, T9's pointers are the root cause and T10's hardening is a symptom fix. This is the T9/T10 boundary and T10 leaves it to T9.
- **→ T8**: ep-level token_cost above reflects Stage3 spend only (no Stage4 cost exists yet). When Stage4 eventually runs, re-attribution per-lane is T8's job.
- **→ T6**: `_annotate_candidate_diversity` at `chief_writer.py:513-568` is Stage4-local diversity. T6 owns **Stage3** ensemble diversity per §8 invariant 6. If Stage4 candidate diversity turns out to tie-collapse in practice (finding 12 hypothesis), the decision whether to fix it with writer-side temperature spread or Director-side tie-break belongs at synthesis, not inside T10.

## Hypothesis Candidates For Synthesis

Labelled explicitly as **candidates**, not directives. Each must be re-validated against live Stage4 evidence once Stage4 actually runs (finding 1), since T10's entire code-forward analysis is today un-anchored to Stage4 artifacts.

- **H1. Forward `_stage3_meta` to the Stage4 writer prompt on the first attempt.** Inject `fix_pack` + `binding_prevalidation_categories` + `quality_risk` / `revision_required` into `common_context` assembly inside `_prepare_generate_ensemble_context` (`chief_writer.py:592-680`) so the writer starts attempt 1 already knowing Stage3's warning vocabulary. Minimal surface: a new Stage3-warning block in `_build_common_context`, no schema change. Evidence: findings 2 + 6 + 7. Severity: **gap**.

- **H2. Convert `_qualify_manuscript_candidates_for_director` from a soft-reorder to a hard admission gate with explicit re-generate trigger when all candidates fail.** Replace the `chief_writer.py:329-349` degraded fallback with a bounded re-spawn that re-calls `_run_generate_ensemble_workers` once with a Stage3-vocabulary-injected prompt. Evidence: finding 3. Severity: **gap**. Note: must be bounded (e.g. one extra fan-out per episode) to stay inside T8's cost envelope.

- **H3. Extend `_manuscript_candidate_admission_reason` admission vocabulary to name Stage3 reject families.** Enumerate at least `opening_transition_type_mismatch`, `tactical_semantic_fidelity_gap`, `scenario_density_low`, `protagonist_state_drift` as recognised reasons and run a lightweight detector (even if regex + `stage_cross_stage_contract.py` normalizer). This **does not** require a new Stage4 validator; it just needs the writer-side admission reason enum to mirror the Stage3 contract so the two stages speak the same language. Evidence: findings 4 + 5 + 6 + 11. Severity: **gap**.

- **H4. Make `_classify_structural_patch_focus` multilingual/anchored.** Expand the keyword dictionaries to include English contract field names (`opening_transition`, `scenario_density`, `tactical_semantic_fidelity`) so that a director feedback sentence referencing the Stage3 contract vocabulary is routed to a scene-aware structural patch instead of a full regenerate. Evidence: finding 8. Severity: **gap**.

Lower-priority candidates, listed for completeness:

- **H5.** Stop fail-closing `_extract_inplace_patch_payload` on a single missing `[원고_끝]` marker when response length is within `[min, 2*min]` — add a salvage lane. Evidence: finding 9.
- **H6.** Relax the `patch_with_feedback` five-field hard gate for Stage3-origin fix_packs: if `patch_targets` + `must_fix` + `target_kind` are present, synthesise a `do_not_regress` default from the prior manuscript snapshot. Evidence: finding 10. (Tension with safety rule — must be approved at synthesis.)

None of the candidates above propose a new Stage4 semantic judge, and none propose retuning Stage3 or the validator. They are all writer-side contract strengthenings and carry-over plumbing inside the `chief_writer.py` / `writer_template.py` surface that T10 owns.

## 3-Pass Audit Record

### Pass 1. Draft
- walked `chief_writer.py` anchors 117/194/239/261/282/857/894/1040/1293/1330/1506/1534/1607/1715/1876/1945/1998/2119/2232/2316/2382 and `writer_template.py` 87/141/356 once linearly
- ran readonly sqlite join over `stage_attempts` / `director_selections` / `manuscripts` / `blueprints`
- read `0_temp.txt:400-469` once
- draft finding list carried 9 findings; assumed Stage4 had rows and the pair-matrix would be measurable

### Pass 2. Re-verify
- re-queried `SELECT DISTINCT stage FROM stage_attempts` → `{2, 3}` only → forced a full rewrite of finding 1 from "pair matrix sparse" to "pair matrix empty (visibility gap)"
- walked `modules/**/stage4*.py` to check whether any Stage4 module does consume `_stage3_meta` → found three: `stage4_director_runtime.py:1220-1244` (advisory), `stage4_outcome_runtime.py:1041-1066` (retry threshold), `stage4_post_processor.py:171` (forward). Added these as evidence anchors; updated findings 2, 10, 13 to reflect that the **writer** is the only Stage4 component that does not consult `_stage3_meta`.
- cross-checked `chief_writer.py` live grep for `_stage3_meta` and `stage3_meta` → 0 matches → finding 2 upgraded from "partial" to "first-pass is fully warning-blind"
- re-checked the stage line anchors listed in parent §12 Pass 2 (`chief_writer.py:117/194/1040/1330/1506/1945/2232/2382` and `chief_writer.py:857`); each matches the live file at `32d6f0c8`
- added findings 11 (score tie collapse), 12 (bleed hypothesis), 13 (stage2-only context pull) that surfaced during the re-walk
- added cross-terminal pointers to T5, T2, T7, T9, T8, T6; removed any implicit claim that T10 is scoring Stage3 or validator behaviour

### Pass 3. Non-overlap + non-goal sweep
- checked every finding against §8 non-overlap invariants:
  - none scores initial-prompt quality (T1) — findings 2, 3, 4 speak only about the writer admission path, not about ensemble.yaml authoring quality
  - none scores Stage3 retry feedback (T2) — finding 10 talks about the Stage4 lane's consumption of Stage3's fix_pack, not the Stage3 retry loop itself
  - none scores producer context packet composition (T3)
  - none scores cheap admission / validator heuristic calibration / ensemble diversity / director overlap / cost / Stage2 handoff — T4/T5/T6/T7/T8/T9 respectively
  - all Stage3-side observations are framed as cross-terminal pointers, not rankings
- checked every finding against §10 non-goals: no code edits, no config/prompt/YAML edits, no schema changes, no live rerun, no pytest, no DB write, no PR — all read-only
- confirmed every anchor is a file:line or artifact:path; zero `unanchored` findings
- confirmed the entire deliverable is UTF-8, no U+FFFD, no triple-question placeholders; quoted Stage3 console text has its live source (`0_temp.txt:412/463`) re-anchored so it is re-decodable
- final confidence bumped: evidence is code-forward but every anchor is live-verified and every hypothesis is labelled as a candidate (not a directive)

## Final Confidence

`96%`

Residual uncertainty (the 4%):

- Finding 12 (tie-collapse bleed) is a code-forward hypothesis, not a measurement, because the live run has zero Stage4 rows (finding 1). It would move from hypothesis to measurement once Stage4 actually runs on ep1–ep7; at that point synthesis should re-open H2/H3 against artifacts.
- Findings 10 and 13 assume the `_stage3_meta["fix_pack"]` contract that Stage3 hands off is sometimes missing `do_not_regress`. This was inferred from the fix_pack builder code at `stage3_orchestrator.py:2401-2423` plus the `_compact_stage3_contract_list` shape; it was **not** observed in an actual Stage3→Stage4 payload because no such payload exists in the corpus. A single post-Stage3 ep trace would confirm or falsify it — that confirmation is outside the §10 non-goals and belongs to the synthesis step.
