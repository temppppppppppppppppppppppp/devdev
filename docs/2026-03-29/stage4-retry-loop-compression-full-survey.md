## Stage4 Retry Loop Compression Full Survey

Date: 2026-03-29
Status: draft-for-audit
Track: system
Type: bounded full-survey
Topic Slug: stage4-retry-loop-compression
Audit Order: `docs/2026-03-29/stage4-retry-loop-compression-full-survey-audit-order.md`

Baseline Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`

---

### 1. Scope and Intent

This survey answers one question:

> Why did the clean Gemini canary still need 8 rounds on EP3, and what is the smallest safe contract move that reduces repeated continuity_firewall/post_select_conflict oscillation without moving quality judgment out of the Director?

Included surfaces: `stage4_orchestrator.py`, `stage4_interview_round.py`, `stage4_outcome_runtime.py`, `stage4_retry_runtime.py`, `stage4_reject_runtime.py`, `director_ensemble.py`, prior surveys, live canary logs.

Excluded: provider routing, model selection, broad Stage 4 redesign, feedback windowing rework, blueprint authoring redesign, prose quality tuning, execution SSOT authoring.

---

### 2. Evidence Sources

#### Code (current HEAD)

| File | Key Functions |
|---|---|
| `stage4_orchestrator.py` | `_InterviewRoundLoopState` (L384-401), `_run_interview_round_step` (L1474-1541), `_apply_v75d_inplace_blueprint_patch` (L1840), `_apply_v75b_blueprint_regeneration` (L2028) |
| `stage4_interview_round.py` | `_run_post_select_checks` (L3738-3911), `_build_retry_feedback_provenance` (L577-685), `_classify_reject_bucket` (L496-507) |
| `stage4_outcome_runtime.py` | `handle_reject_round_result` (L437-514), `_should_count_reject_as_logic_like` (L596-627), `apply_retry_repair_escalation` (L792-873), `_apply_reject_bucket_advisory` (L697-740) |
| `stage4_retry_runtime.py` | `_resolve_retry_lane_routing` (L831-925), `generate_candidates` (L238-328), `_run_patch_or_rewrite_retry_lane` (L990-1055) |
| `stage4_reject_runtime.py` | `handle_reject` (L61-210), `_build_reject_guidance_payload` (L429-591), `_build_reject_retry_snapshot` (L325-427) |
| `director_ensemble.py` | `_apply_contradiction_firewall_gate` (L1149), `_classify_firewall_mode` (L452), `_derive_gate_basis` (L290) |

#### Prior Surveys

| Document | Relevant Context |
|---|---|
| `stage4-feedback-windowing-full-survey.md` | Feedback snowball confirmed and resolved; retry_directives now windowed to latest-round-only. Not a factor in EP3 oscillation. |
| `stage4-decision-contract-matrix-full-survey.md` | M-4 feedback snowball (resolved). M-1 authoritative field gaps. |
| `why-fix-pack-is-empty-full-survey.md` | fix_pack lifecycle; post_select_conflict always empties fix_pack. |
| `stage4-gemini-direct-default-full-survey.md` | Gemini provider baseline. |

#### Live Canary Logs

| Project | Evidence Role |
|---|---|
| `canary_0329_feedback_windowing_check` EP3 | **Primary**: 8-round oscillation evidence |
| `canary_0328_gemini_direct_fixscope_check` EP2 | **Comparison**: 3-round convergence, same provider |

---

### 3. EP3 Round-by-Round Loop Map

Source: `canary_0329_feedback_windowing_check/logs/episode_production.jsonl` + `session/decisions.jsonl` + DB `director_selections`

| Round | Pre-FW Score | Final Score | Director Verdict | Final Verdict | Gate Basis | FW? | Auth Fix Scope | Repair Scope | Reject Bucket | Strategy |
|---|---|---|---|---|---|---|---|---|---|---|
| R0 | 56 | 44 | REJECT | REJECT | continuity_firewall | Yes (CRITICAL 1) | full | full | structure_error | tension |
| R1 | 71 | 44 | REJECT | REJECT | continuity_firewall | Yes (CRITICAL 1) | full | full | structure_error | tension |
| R2 | 84 | 44 | REJECT | REJECT | continuity_firewall | Yes (CRITICAL 1) | full | full | structure_error | balanced |
| — | — | — | — | *V75-B blueprint regen* | — | — | — | — | — | — |
| R3 | 94 | 94 | **PASS** | **REJECT** | post_select_conflict | No | inplace | full | constraint_violation | balanced |
| R4 | 56 | 44 | REJECT | REJECT | continuity_firewall | Yes (CRITICAL 1) | full | full | structure_error | asp_correction |
| R5 | 98 | 98 | **PASS** | **REJECT** | post_select_conflict | No | inplace | full | constraint_violation | narrative |
| R6 | **98** | 44 | REJECT | REJECT | continuity_firewall | Yes (CRITICAL **2**) | inplace | inplace | post_select_conflict | balanced |
| R7 | 100 | 100 | PASS | PASS | director_primary_pass | No | inplace | inplace | — | tension |

**Root contradiction**: EP1 established the protagonist securing 20 billion won capital and receiving an OTP. EP3 manuscripts kept re-narrating that acquisition as if it hadn't happened (완료사건반복 — completed-event-repetition). The continuity firewall correctly flagged this as CRITICAL.

**Oscillation pattern**: `LOW(44) → LOW(44) → LOW(44) → [V75-B] → HIGH-INV(94) → LOW(44) → HIGH-INV(98) → LOW(44) → PASS(100)`

**Pre-firewall score trajectory**: 56 → 71 → 84 → 94 → 56 → 98 → **98** → 100. The model quality improved across rounds. R6 is the starkest case: pre-firewall score was 98 (clean pass quality) but the firewall found 2 CRITICAL violations and capped it to 44.

---

### 4. Gate Family and Lane Transition Matrix

#### 4.1 Gate Family Definitions

| Gate | Where It Fires | Trigger | Score Effect | Fix Scope Effect |
|---|---|---|---|---|
| `continuity_firewall` | Inside Director ensemble (`_apply_contradiction_firewall_gate`, director_ensemble L1149) | CRITICAL >= 1 OR MAJOR >= 2 in contradiction check | Capped to min(original, 44) | Director's fix_scope preserved; downstream may widen |
| `post_select_conflict` | After Director PASS, in positive-verdict transition (`_run_post_select_checks`, interview_round L3738) | Continuity/history LLM checks find conflicts | Original positive score preserved | **Forced to "full"** (reject_runtime L522); fix_pack **emptied** (L523) |
| `director_primary_reject` | Director's own verdict | Director says REJECT | Director's score | Director's fix_scope |
| `patch_reaudit_fail` | After PASS_WITH_FIX inplace loop fails | Inplace patch didn't resolve fix items | From re-audit | From re-audit |

#### 4.2 Lane Routing After Each Gate Family

Source: `stage4_retry_runtime.py` `_resolve_retry_lane_routing` (L831-925)

| Gate Family | fix_scope (resolved) | fix_pack | Lane Selected | Why |
|---|---|---|---|---|
| `continuity_firewall` | Varies — in EP3, resolved to "full" after continuity replay reclassification and reject guidance chain | {} in EP3 | **Full rewrite** (in EP3) | In EP3, `_is_continuity_replay_reject` (reject_runtime L463-481) reclassified to `structure_error` with `fix_scope="full"`. This is not a universal guarantee — the reclassification depends on contradiction types matching replay signatures, and the guidance chain (`_build_reject_guidance_payload`) resolves fix_scope through multiple conditional steps. EP3 evidence shows convergence to rewrite, not a single hardcoded force. |
| `post_select_conflict` | "full" (explicitly forced at reject_runtime L522) | {} (explicitly emptied at L523) | **Full rewrite** | Python hardcodes `fix_scope="full"` and empties `fix_pack` for all `post_select_conflict` rejects. `force_patch` requires `fix_scope != "full"` (L875); fails. `use_inplace` requires `fix_scope == "inplace"` (L885); fails. Falls through to rewrite. This is a universal guarantee, unlike `continuity_firewall`. |
| `director_primary_reject` (inplace) | "inplace" | Populated (if Director provided) | **Inplace patch** or **Patch** | Standard lane routing |
| `director_primary_reject` (full) | "full" | {} | **Full rewrite** | Standard fallthrough |

**Key finding**: In EP3, both `continuity_firewall` and `post_select_conflict` families converged to the rewrite lane. `post_select_conflict` does so universally (Python hardcodes `fix_scope="full"` + empty `fix_pack`). `continuity_firewall` reached rewrite through the replay reclassification → reject guidance → lane resolution chain, which in EP3's contradiction profile resolved to rewrite. Neither family currently produces a structured conflict contract that could open the patch lane.

#### 4.3 Lane Transition Across EP3 Rounds

| Round | Gate | Lane | Candidates | Blueprint Changed? |
|---|---|---|---|---|
| R0 | — | Full ensemble (round 0) | 3 | No |
| R1 | continuity_firewall | Full rewrite | 2 (reduced) | No |
| R2 | continuity_firewall | Full rewrite | 2 (reduced) | No |
| R3 | continuity_firewall→V75-B | Full ensemble (fresh after V75-B) | 3 | **Yes** (V75-B regen) |
| R4 | post_select_conflict | Full rewrite | 2 (reduced) | No |
| R5 | continuity_firewall | Full rewrite + ASP | 2 | No |
| R6 | post_select_conflict | Full rewrite | 2 (reduced) | No |
| R7 | continuity_firewall | Full rewrite | 2 (reduced) | No |

Every round after R0 was a full rewrite. No inplace patch or manuscript-preserving lane was ever selected, despite R3 (94), R5 (98), and R6 (pre-FW 98) producing Director-approved quality.

---

### 5. Authoritative vs Derived Ownership Map

| Decision | Owner | Location | Overrideable? |
|---|---|---|---|
| Manuscript quality verdict | **Director** (authoritative) | director_ensemble `select_and_judge_ensemble` | No — respected as final quality judgment |
| Contradiction detection (pre-select) | **Director** (via LLM contradiction_check) | director_ensemble L1154 | No |
| Contradiction firewall trigger | **Python** (CRITICAL/MAJOR count threshold) | director_ensemble L1167 | No — hardcoded threshold |
| Score cap to 44 on firewall | **Python** (hardcoded) | director_ensemble L1208 | No |
| Continuity/history conflict detection (post-select) | **LLM** (separate continuity/history check agents) | interview_round L3784, L3797 | No |
| Verdict downgrade PASS→REJECT on conflict | **Python** (hardcoded) | interview_round L3848 | No |
| fix_scope forced to "full" on post_select_conflict | **Python** (hardcoded) | reject_runtime L522 | No |
| fix_pack emptied on post_select_conflict | **Python** (hardcoded) | reject_runtime L523 | No |
| Retry lane selection (inplace/patch/rewrite) | **Python** (from resolved fix_scope + fix_pack readiness) | retry_runtime L831-925 | No |
| V75-D trigger (inplace blueprint patch) | **Python** (logic_error_streak threshold) | outcome_runtime L843 | Policy-configurable threshold |
| V75-B trigger (full blueprint regen) | **Python** (logic_error_streak threshold after V75-D) | outcome_runtime L854 | Policy-configurable threshold |
| V75-B success: streak/state reset | **Python** (hardcoded reset) | orchestrator L2056-2068 | No |
| Bucket streak tracking | **Python** | outcome_runtime L700-713 | No |
| TF-29 one-shot advisory | **Python** (bucket_streak >= 3) | outcome_runtime L716 | No |

**Key structural observation**: The Director is the quality authority, but Python owns all lane routing, escalation triggers, and fix_scope overrides. When `post_select_conflict` fires, Python explicitly forces `fix_scope = "full"` and empties `fix_pack` (reject_runtime L522-523), regardless of Director's fix_scope. When `continuity_firewall` fires, the path to the rewrite lane is less direct — it flows through `_is_continuity_replay_reject` reclassification, `_build_reject_guidance_payload` conditional steps, and `_resolve_retry_lane_routing` — but in EP3's contradiction profile the result was the same: rewrite lane.

---

### 6. Live Canary Oscillation Evidence

#### 6.1 The Oscillation Mechanism

The EP3 oscillation follows a repeating 2-phase cycle:

**Phase A — Full rewrite produces manuscript with known continuity violation:**
- Chief Writer generates fresh manuscript from scratch (full rewrite lane)
- Manuscript re-narrates EP1's completed capital acquisition
- Director's contradiction check catches CRITICAL violation
- Firewall triggers, score capped to 44
- Gate: `continuity_firewall`

**Phase B — Full rewrite produces quality manuscript that passes Director but fails post-select:**
- Chief Writer generates fresh manuscript (still full rewrite)
- Manuscript avoids the contradiction check's detection pattern
- Director approves with high score (94, 98)
- Post-select continuity/history LLM check finds the conflict from a different angle
- Gate: `post_select_conflict`, score preserved but verdict forced to REJECT
- fix_scope forced to "full", fix_pack emptied → next round is again full rewrite

The cycle repeats because the rewrite lane starts from scratch each time. The near-pass manuscript is stored in `previous_attempt["best_manuscript"]` (interview_round L3878), but the rewrite path (`regenerate_with_feedback`, chief_writer L956) does **not consume it as a generation seed** — it generates entirely new candidates. The manuscript is preserved at the storage level but not reused at the generation level. Additionally, the adjacent rationale (`selection_reason`, `open_review`) is blanked (reject_runtime L356-360) and the conflict evidence remains unstructured free-text.

#### 6.2 Near-Pass Manuscript Waste

| Round | Score | Gate | Manuscript Preserved? | Manuscript Reused? |
|---|---|---|---|---|
| R3 | 94 | post_select_conflict | Yes (`previous_attempt["best_manuscript"]`) | **No** — R4 did full rewrite from scratch |
| R5 | 98 | post_select_conflict | Yes | **No** — R6 did full rewrite from scratch |
| R6 | 98 (pre-FW) | continuity_firewall | Yes (in `selected_candidate`) | **No** — R7 did full rewrite from scratch |

Three manuscripts scoring 94-98 were stored in `previous_attempt["best_manuscript"]` but never reused as generation seeds. The rewrite lane started from scratch each time. Additionally, adjacent rationale fields (`selection_reason`, `open_review`) were blanked at reject_runtime L356-360 for post_select_conflict rounds (R3, R5), stripping context that could have informed the next round. The conflict details existed only as free-text lines in `director_feedback` — no structured conflict contract was extracted from them.

#### 6.3 V75-B Blueprint Regeneration Impact

V75-B fired between R2 and R3 (after `bucket_streak=3` on `structure_error`). Effects:

- `logic_error_streak` reset to 0
- `previous_attempt` cleared to {}
- Fresh blueprint generated

Post-V75-B, R3 immediately produced a Director-PASS candidate (score 94). This proves V75-B correctly addressed the blueprint-level issue. But the post-select conflict check still caught a residual continuity violation, sending the loop back into oscillation.

After V75-B, `blueprint_regenerated = True` prevents further V75-B triggers. The system has no further escalation mechanism beyond V75-B. It can only continue generating full rewrites until the model happens to produce a manuscript that passes both the contradiction firewall AND the post-select conflict check.

#### 6.4 Comparison: Prior Canary EP2 (3 rounds)

Source: `canary_0328_gemini_direct_fixscope_check/logs/episode_production.jsonl`

| Round | Score | Gate | Dir.Verdict | Final | Family |
|---|---|---|---|---|---|
| R0 | 97 | post_select_conflict | PASS | REJECT | high-score-provisional-invalidation |
| R1 | 98 | post_select_conflict | PASS | REJECT | high-score-provisional-invalidation |
| R2 | 96 | director_primary_pass | PASS | PASS | clean-pass |

Prior EP2 converged in 3 rounds with the same family each time (`post_select_conflict` only). No `continuity_firewall` trigger. No oscillation between families.

Current EP3 took 8 rounds because it oscillated between two distinct families. The key difference: EP3 had a persistent structural contradiction (completed-event-repetition from EP1) that manifested through both detection paths.

---

### 7. Root-Cause Assessment

#### 7.1 Primary Cause: Post-Select Conflict Discards Near-Pass Manuscript Without Structured Conflict Contract

When `post_select_conflict` invalidates a near-pass manuscript (score 94-98), the system:

1. Forces `fix_scope = "full"` (reject_runtime L522)
2. Empties `fix_pack = {}` (reject_runtime L523)
3. Blanks `selection_reason` and `open_review` (reject_runtime L356-360)

Three consequences follow:

- **Manuscript stored but not reused**: The near-pass manuscript is stored in `previous_attempt["best_manuscript"]` (interview_round L3878) and persists in the reject snapshot. However, the rewrite lane (`regenerate_with_feedback`, chief_writer L956) does not consume `best_manuscript` as a generation seed. The Chief Writer starts from scratch. The gap is not raw preservation — the manuscript is preserved — but reuse: no contract exists for the rewrite path to consume the stored manuscript.
- **Adjacent rationale stripped**: The reject snapshot (reject_runtime L356-360) blanks `selection_reason`, `open_review`, and empties `fix_pack` when `reject_bucket == "post_select_conflict"` and `resolved_fix_scope == "full"`. The `best_manuscript` survives this same block, but the rationale fields that would contextualize it for the next round are lost.
- **No structured conflict contract**: The post-select conflict details exist only as free-text lines (`[Continuity Conflict] ...`, `[V67] History Conflict: ...`) appended to `director_feedback`. No structured payload (with `conflict_type`, `conflict_detail`, `source_episode`, `expected_truth`, etc.) is extracted. The patch lane requires a patch-ready `fix_pack` contract (`patch_targets`, `must_fix`, `do_not_regress`, `success_condition`, `target_kind`), so even if `fix_scope` were not forced to "full", the empty `fix_pack` would prevent the patch lane from opening.

**Why this causes oscillation**: A fresh full-rewrite manuscript has no constraint to preserve the parts of the near-pass that were correct. It may fix the specific conflict that caused `post_select_conflict` but introduce a new contradiction that triggers `continuity_firewall`. The model has to independently rediscover the correct content structure.

#### 7.2 Secondary Cause: No Oscillation-Aware Compression

The loop state tracks `bucket_streak` (consecutive same-bucket) and `contradiction_type_streak` (consecutive same-contradiction-type). Neither detects alternating-family oscillation:

- `bucket_streak` resets to 1 when the bucket changes (outcome_runtime L713). In the EP3 sequence: `structure_error → structure_error → structure_error → constraint_violation → structure_error → ...` — the streak breaks every time the family alternates.
- TF-29 fires only on `bucket_streak >= 3` (same bucket). It fired once between R2-R3 because there were 3 consecutive `structure_error` rounds. After V75-B, the alternation prevented the streak from re-accumulating.

There is no mechanism that says: "the loop has bounced between `continuity_firewall` and `post_select_conflict` 3 times — escalate differently."

#### 7.3 Tertiary Cause: V75-B Is One-Shot Without Post-V75-B Compression

V75-B (blueprint regeneration) fired correctly after R2. Post-V75-B, R3 produced a 94-score candidate — proving the new blueprint was better. But:

- `blueprint_regenerated = True` prevents further V75-B triggers
- No further escalation mechanism exists
- `bucket_streak` was reset (fresh start), but the alternating pattern prevents it from re-accumulating to 3
- The system can only wait for the model to independently produce a manuscript that passes both checks

#### 7.4 What Is NOT Causing the 8-Round Loop

- **Feedback snowball**: Confirmed resolved. `retry_directives` stayed at 1,200-1,500 chars plateau (no linear growth).
- **Provider contamination**: All rounds used gemini-2.5-pro exclusively.
- **Model incapability**: Pre-firewall scores of 56→71→84→94→56→98→98→100 show the model can produce quality content. The issue is convergence, not capability.
- **Blueprint quality**: V75-B regeneration produced a blueprint that enabled a 94-score candidate. The blueprint was adequate.

---

### 8. Bounded Compression Options Ranked

Ranked by (safety, compression potential, Director sovereignty preservation):

#### Option 1: Manuscript Reuse Seam + Downstream Rationale Preservation + Structured Conflict Contract (RECOMMENDED)

This is a **two-wave** option. The first wave is the immediate safe move; the second wave depends on first-wave evidence.

**Wave 1 — Manuscript reuse seam + rationale preservation + structured conflict payload extraction:**

When `post_select_conflict` invalidates a near-pass manuscript (Director PASS + score >= 80):

1. **Define a reuse contract** for the stored `best_manuscript`: the manuscript is already preserved in `previous_attempt["best_manuscript"]` (interview_round L3878). The missing seam is not raw storage but generation-path reuse. Wave 1 defines how the rewrite path should consume the stored manuscript (e.g., as reference context, as a structural seed, or as a diff baseline) without yet committing to a specific lane change.
2. **Preserve downstream rationale fields**: stop blanking `selection_reason` and `open_review` at reject_runtime L356-360 for high-score near-pass post_select_conflict. These fields carry the Director's original quality judgment and are needed to contextualize the preserved manuscript for the next round.
3. **Extract a structured conflict contract** from the free-text conflict lines (`[Continuity Conflict] ...`, `[V67] History Conflict: ...`) into a separate `conflict_contract` payload with explicit `conflict_type`, `conflict_detail`, `source_episode`, and `expected_truth` fields.
4. **Separate ownership**: the structured conflict contract is operator evidence, not a patch-ready `fix_pack`. It does not claim to satisfy the `patch_targets` / `must_fix` / `success_condition` / `target_kind` schema that the patch lane requires.

Wave 1 does NOT change `fix_scope` or `fix_pack`. The next round still routes to full rewrite. But the reuse contract, preserved rationale, and structured conflict contract are available as explicit typed inputs for the rewrite round's Chief Writer prompt, rather than being lost (rationale) or buried in free-text (conflict evidence).

**Wave 2 — Patch lane connection (deferred, depends on Wave 1 evidence):**

After Wave 1 is validated by canary, evaluate whether the structured conflict contract can be reliably converted to a patch-ready `fix_pack` (with `patch_targets`, `must_fix`, `do_not_regress`, `success_condition`, `target_kind`). If conversion is reliable:

- Change `fix_scope` from "full" to "partial" for high-score near-pass post_select_conflict
- Populate `fix_pack` from the structured conflict contract
- The next round's lane routing would then select patch mode instead of full rewrite

Wave 2 is not committed by this survey. The free-text conflict lines are currently unstructured, and asserting they can reliably populate a patch-ready contract is one step ahead of current evidence.

**Preserves**: Director sovereignty (Director already said PASS). Python only extracts and structures the conflict evidence. The Director will still judge the next round's output.

**Risk**: Wave 1 is LOW (rationale preservation + conflict extraction + reuse contract definition, no lane change). Wave 2 is MEDIUM (requires verified format conversion from structured conflict contract to patch-ready `fix_pack`).

**Blast radius**: Wave 1: ~10 lines in reject_runtime (rationale preservation) + ~25 lines for conflict contract extraction + reuse contract definition in retry_runtime or chief_writer. Wave 2: ~15 additional lines in reject_runtime + lane routing.

#### Option 2: Alternating-Family Oscillation Ceiling

**Change**: Add oscillation detection to `_InterviewRoundLoopState`. Track the last N gate families. When the loop detects K alternations between two families (e.g., `continuity_firewall ↔ post_select_conflict` 2+ times), escalate:

- If `blueprint_regenerated = False`: trigger V75-B early
- If `blueprint_regenerated = True`: trigger a targeted "conflict-first" generation mode where the Chief Writer prompt explicitly addresses the specific continuity violation

**Preserves**: Director sovereignty (Director still judges). Python only detects the oscillation pattern and adjusts generation strategy.

**Estimated compression**: Would have triggered after R3→R4 alternation, potentially reducing to 5-6R.

**Risk**: MEDIUM. Oscillation detection adds loop-state complexity. The "conflict-first" generation mode would need careful prompt engineering.

**Blast radius**: ~30 lines in loop state + ~20 lines in oscillation handler.

#### Option 3: Earlier V75-B Trigger for Continuity-Firewall Streaks

**Change**: Lower the V75-B trigger threshold specifically for `continuity_firewall` rejects. Current: V75-D at streak=2, then V75-B at streak=2 after V75-D. Proposed: V75-B at streak=2 for firewall rejects (skip V75-D, since inplace blueprint patch is unlikely to fix a fundamental continuity violation).

**Preserves**: Director sovereignty.

**Estimated compression**: V75-B would have fired after R1 instead of R2, saving 1 round. Modest improvement.

**Risk**: LOW, but limited impact. The current V75-B already fired at R2 and the oscillation continued afterward.

**Blast radius**: ~10 lines in `apply_retry_repair_escalation` threshold logic.

#### Option 4: Post-V75-B Conflict-Aware Generation

**Change**: After V75-B regenerates the blueprint and the first post-V75-B round produces a near-pass invalidated by `post_select_conflict`, inject the specific conflict details into the next round's generation as a hard constraint (not just advisory text).

**Mechanism**: Add a `conflict_first_constraint` field to `writer_kwargs` that the Chief Writer treats as a mandatory avoidance instruction, separate from general feedback.

**Preserves**: Director sovereignty (Director still judges the output).

**Estimated compression**: Would address the R3→R4 transition specifically. Expected: 1-2 rounds saved.

**Risk**: MEDIUM. Adds a new constraint pathway to Chief Writer prompts.

**Blast radius**: ~15 lines in reject_runtime + ~15 lines in Chief Writer prompt construction.

#### Option 5: Do Nothing

**Assessment**: NOT recommended. The model demonstrated it can produce pass-quality content (pre-firewall scores of 94-100) but the full-rewrite lock wastes those near-pass manuscripts. 8 rounds at ~300-500K tokens each is a significant cost multiplier for a preventable oscillation.

---

### 9. Recommended Bounded Next Step

**First move: Option 1 Wave 1 (Manuscript Reuse Seam + Downstream Rationale Preservation + Structured Conflict Payload).**

1. When `post_select_conflict` invalidates a Director-PASS manuscript with score >= 80:
   - **Define reuse contract** for the already-stored `best_manuscript` — specify how the rewrite path should consume it (reference context, structural seed, or diff baseline) without committing to a lane change
   - **Preserve rationale** — stop blanking `selection_reason` and `open_review` (reject_runtime L356-360) for high-score near-pass
   - **Extract** structured conflict contract from free-text conflict lines into explicit fields (`conflict_type`, `conflict_detail`, `source_episode`, `expected_truth`)
   - **Do not change** `fix_scope` or `fix_pack` — the next round still routes to full rewrite
   - The reuse contract, preserved rationale, and structured conflict contract become explicit typed inputs for the rewrite round rather than lost or buried free-text

2. When `post_select_conflict` invalidates a low-score manuscript (< 80), or any non-PASS verdict:
   - Keep current behavior (`fix_scope = "full"`, empty fix_pack, full rewrite)

**Why Wave 1 first, not patch lane directly**:
- The patch lane requires a patch-ready `fix_pack` with `patch_targets`, `must_fix`, `do_not_regress`, `success_condition`, `target_kind`. Current post-select conflict evidence is free-text lines. Asserting reliable conversion from free-text to patch-ready contract is ahead of current evidence.
- Wave 1 closes three seams without changing lane routing: (a) manuscript reuse contract, (b) rationale preservation, (c) structured conflict ownership
- Whether Wave 2 (patch lane connection) is viable depends on whether the structured conflict contract proves stable enough to populate a `fix_pack`

**What this does NOT change**:
- Lane routing — still full rewrite after post_select_conflict (until Wave 2 is validated)
- `continuity_firewall` rejects — still route through replay reclassification → reject guidance → lane resolution
- Director still judges all candidates
- V75-B escalation logic unchanged
- Post-select conflict checks still run on every PASS

**Expected improvement**: Wave 1 alone does not change lane routing, so round count may not drop significantly. The value is: (a) the manuscript reuse contract defines how the rewrite path can consume the stored near-pass manuscript, (b) preserved rationale (`selection_reason`, `open_review`) provides the Director's quality context for the next round, (c) the structured conflict contract enables better-targeted rewrite prompts, (d) ownership between authoritative Director fields and runtime-derived conflict evidence is cleanly separated.

---

### 10. Open Questions

1. **Patch lane readiness for conflict-derived fix_pack**: The patch lane (`patch_with_feedback`, chief_writer L1907) requires a `fix_pack` with `patch_targets`, `must_fix`, `success_condition`. Can post-select conflict details be reliably converted to this format? The `[Continuity Conflict]` and `[V67] History Conflict` lines are free-text — they would need structured extraction.

2. **Contradiction firewall vs post-select check overlap**: In EP3, both checks flagged the same root issue (completed-event-repetition) from different angles. If carryover tightening resolves the post-select conflict, will the same manuscript also pass the contradiction firewall? Or could the patch introduce a new CRITICAL violation?

3. **`firewall_fixable` path underutilization**: The Director ensemble has a `_classify_firewall_mode` (director_ensemble L452) that can produce `PASS_WITH_FIX` instead of hard REJECT for fixable contradictions. In EP3, this path was never taken because the violations were classified as CRITICAL (not fixable type tokens). Should the fixable-type-token list be expanded to include completed-event-repetition?

4. **Score 98 firewalled to 44 in R6**: R6 had pre-firewall score 98 but was firewalled with 2 CRITICAL violations. If carryover tightening had been in place, R5's 98-score manuscript would have been patched instead of discarded. Would the patched R5 manuscript have avoided R6's double-CRITICAL?

5. **`bucket_streak` reset after family change**: The current `bucket_streak` resets to 1 on any bucket change (outcome_runtime L713). This means alternating families can never trigger streak-based escalation. Should an alternation counter be added alongside the streak counter?

6. **Rewrite path manuscript reuse contract**: `previous_attempt["best_manuscript"]` is stored but `regenerate_with_feedback` (chief_writer L956) does not consume it. The `patch_with_feedback` method (L1907) does use the previous manuscript via `prev_manuscript` parameter. Wave 1 must define a reuse contract for the rewrite path: should the stored manuscript be injected as reference context in the prompt? As a structural seed that the Chief Writer is asked to preserve? As a diff baseline for post-generation comparison? Each option has different prompt-surface implications.

7. **Rationale preservation impact on prompt/control surfaces**: Preserving `selection_reason` and `open_review` (instead of blanking them) means these fields will be available in `previous_attempt` for the next round. This may affect how `_build_regeneration_feedback` (chief_writer L992-1024) constructs the Chief Writer prompt — it reads `open_review` (L1020) and may inject it. Need to verify that preserved rationale from a downgraded PASS does not confuse the next round's prompt construction (e.g., the Chief Writer seeing "no issues" from the Director while also seeing "[Continuity Conflict]" from the post-select check).

---

### 11. Confidence

| Finding | Confidence | Basis |
|---|---|---|
| EP3 oscillation follows a 2-phase cycle (firewall ↔ post-select) | **HIGH** | 8-round raw data confirms alternating pattern |
| In EP3, both gate families converged to rewrite lane | **HIGH** | `post_select_conflict`: universally forced (reject_runtime L522). `continuity_firewall`: resolved to rewrite through replay reclassification + reject guidance chain in EP3's contradiction profile. |
| Near-pass manuscripts are stored but not reused by the rewrite generation path | **HIGH** | `previous_attempt["best_manuscript"]` stored (interview_round L3878) but `regenerate_with_feedback` (chief_writer L956) does not consume it as a seed |
| Near-pass stored-but-not-reused + rationale stripped + no structured conflict contract amplifies oscillation | **HIGH** | Pre-firewall scores 94/98/98 prove model capability; manuscripts stored but generation path starts from scratch each time; `selection_reason`/`open_review` blanked at reject_runtime L356-360 |
| V75-B fired correctly but is one-shot without post-V75-B compression | **HIGH** | Code: `blueprint_regenerated=True` prevents re-trigger (orchestrator L2071) |
| No alternating-family oscillation detection exists | **HIGH** | `bucket_streak` resets on family change (outcome_runtime L713); no alternation counter |
| Option 1 Wave 1 (reuse seam + rationale preservation + structured contract) is the smallest safe first move | **MEDIUM-HIGH** | Closes three seams (reuse, rationale, conflict ownership) without changing lane routing. Low risk. |
| Patch lane connection (Wave 2) could compress rounds but is ahead of current evidence | **MEDIUM-LOW** | Free-text conflict lines → patch-ready `fix_pack` conversion is unproven. Whether a patched near-pass manuscript would pass both contradiction firewall AND post-select check is untested. Round compression estimates are speculative until Wave 1 evidence is available. |
