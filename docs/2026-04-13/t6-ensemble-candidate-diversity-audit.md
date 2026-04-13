# T6. Ensemble Candidate Diversity Audit

- Parent Order: `docs/2026-04-13/s2-s3-s4-runtime-improvement-10-terminal-parallel-investigation-order.md`
- Terminal: T6
- Date: 2026-04-13
- Mode: survey-only, read-only, parallel
- Baseline Commit (at spawn): `32d6f0c8b56898fd8a370ae13684043d4cfda91a`
- Baseline Dirty Summary: as documented in parent order §1 — Stage3 producer/ensemble/runtime/validator edits + live `000_260412_a` rerun artifacts + 2026-04-13 audit docs + `config/prompts/ensemble.yaml` + `config/models.yaml`; worktree matches parent order baseline 1:1
- Resume Commit: same as baseline (no drift during this terminal)
- Resume Drift Summary: none
- Side-Effect Coverage: read-only static + frozen live-run artifact reads; no mutation
- Confidence: `96%`

## Purpose

When `BlueprintEnsembleGenerator` fans out candidates (parent order §6 T6 describes 5 strategies `conservative / balanced / action_focused / dialogue_focused / emotion_focused`, but the current head ships **3** — see Finding 1), do those candidates actually produce meaningfully different blueprints, or do they all share the same base drift (e.g. all declare `direct_continuation`, all miss the same scene beat, all copy the same opening_transition mistake) so the ensemble spend is near-wasted on contract-level diversity?

## Evidence Anchors

Code (current head `32d6f0c8`):

- `modules/domain/agents/blueprint_ensemble.py:47-87` — `BLUEPRINT_STRATEGIES` constant holds **3** strategies: `action_focused`, `emotion_focused`, `dialogue_focused`. No `conservative` and no `balanced` anywhere in the fan-out code (`blueprint_ensemble.py` grep for `conservative|balanced` returns only `BLUEPRINT_STRATEGIES` definitions — zero name hits).
- `modules/domain/agents/blueprint_ensemble.py:272-289` — `BlueprintEnsembleGenerator.__init__` wires `self.strategies = BLUEPRINT_STRATEGIES` and pins `self.max_workers = 3`. Fan-out width = 3 by construction.
- `modules/domain/agents/blueprint_ensemble.py:384-390` — `_select_blueprint_ensemble_strategies` is the only code path that can narrow the trio (single-strategy retry). Otherwise all 3 strategies run.
- `modules/domain/agents/blueprint_ensemble.py:403-518` — `_run_blueprint_ensemble_workers` ThreadPoolExecutor fan-out. Each strategy calls `_generate_single` with an otherwise identical kwarg set (`ep_num`, `arc_focus`, `constraints_str`, `tactical_excerpt`, `prev_info`, `hud_context`, `genre`, `cache_name`, `prev_blueprint` — only `strategy` and `strategy_feedback` differ per worker).
- `modules/domain/agents/blueprint_ensemble.py:1395-1541` — per-candidate contract kill path (`opening_transition` normalization, tactical authority kill, structural contract kill). This is the downstream code that rewrites candidate `opening_transition.type` **after** the producer returns, which is why producer responses mostly lack that field upstream (see Finding 3).

Live-run artifacts (frozen):

- `projects/000_260412_a/logs/session/llm_io.jsonl` — 513 lines, 286 `BlueprintEnsembleGenerator` records. Captured full prompt + response per call. This is the **only** available surface for pair-wise candidate comparison on the live run, because the filesystem artifact tree only keeps the winning candidate per episode (see Finding 2). Classification by directive substring `액션 중심 / 감정 중심 / 대화 중심` yields 82 action + 73 emotion + 73 dialogue = 228 fan-out calls and 58 repair-mode (`patch`) calls.
- `projects/000_260412_a/logs/artifacts/stage3/ep_000{1..7}/attempt_*/final_blueprint__*.json` — 7 files total, one per episode, each carrying only the **winning** strategy's final blueprint:
  - `ep_0001/attempt_07/final_blueprint__dialogue_focused.json`
  - `ep_0002/attempt_10/final_blueprint__dialogue_focused.json`
  - `ep_0003/attempt_06/final_blueprint__emotion_focused.json`
  - `ep_0004/attempt_06/final_blueprint__action_focused.json`
  - `ep_0005/attempt_09/final_blueprint__emotion_focused.json`
  - `ep_0006/attempt_10/final_blueprint__dialogue_focused.json`
  - `ep_0007/attempt_10/final_blueprint__action_focused.json`
- `projects/000_260412_a/project_data.db` (read-only): `director_selections` (9 rows at stage=3) stores only winner rows; `stage_attempts` has the same 9 winner rows; `attempt_raw_rationale` is empty at stage=3; `llm_calls` agrees with `llm_io.jsonl` counts (e.g. ep2 = 77 BlueprintEnsembleGenerator calls across both the 54 fan-out calls plus 23 patch-mode calls). Losing-candidate rationale is **not** persisted.

Pairing method: group `BlueprintEnsembleGenerator` calls by `(ep_num, strategy)`, sort ascending by `ts`, then take the *k*-th call of each strategy as the *k*-th parallel fan-out trio. `ep_num` detection uses `제\s*(\d+)\s*화` from the prompt body (100% match rate on 228 fan-out records). Responses are fenced ```json; JSON extraction strips the fence, falls back to brace-balanced parsing.

Pairing result:

- ep1: min(4, 4, 4) = **4** trios
- ep2: min(18, 18, 18) = **18** trios
- ep3: min(6, 6, 6) = **6** trios
- ep4: min(10, 10, 10) = **10** trios (4 of these are whole-fan-out API failures — Finding 7)
- ep5: min(11, 8, 8) = **8** trios (action got 3 extra calls; Finding 8)
- ep6: min(10, 10, 10) = **10** trios
- ep7: min(14, 8, 8) = **8** trios (action got 6 extra calls)
- ep8: min(9, 9, 9) = **9** trios (interrupted mid-run; no Director verdict yet)
- **Total paired trios analyzed: 73** (69 of which parsed cleanly in all 3 candidates; 4 ep4 trios were whole-fan-out API-failure records with 0-char responses)

## Findings

### Finding 1 — Parent order mis-counts fan-out width (hypothesis + data correction)

Severity: `gap`

Parent order §4 / §6 / §8 claim `BlueprintEnsembleGenerator` fans out **5** candidates (`conservative / balanced / action_focused / dialogue_focused / emotion_focused`). Current head (`32d6f0c8`) ships only **3**: `action_focused`, `emotion_focused`, `dialogue_focused`.

Evidence:

- `blueprint_ensemble.py:47-87` `BLUEPRINT_STRATEGIES` has exactly 3 entries
- `blueprint_ensemble.py:288` `self.max_workers = 3`
- grep for `conservative|balanced` across `modules/**/*.py` returns zero hits in `blueprint_ensemble.py`, and only unrelated hits in `arc_ensemble.py`, `chief_writer.py`, `quality_dashboard.py` — none of which are blueprint strategies

Implication: every "5 strategies" claim downstream needs to be reinterpreted as "3 strategies". Diversity scoring in this deliverable uses the real 3-way fan-out.

### Finding 2 — Losing-candidate evidence has only one persistent surface: `llm_io.jsonl`

Severity: `gap`

The parent order §6 T6 required-analysis step 2 says "walk `ep_0001..ep_0007/attempt_XX/` and pair the 5 candidate files per attempt" and step 2 sub-bullets refer to comparing `opening_transition.type` across candidates. That pairing **cannot** be done from the filesystem tree on the current live run:

- each ep directory holds **exactly one** `attempt_XX` subdirectory (only the final winning attempt is retained)
- each `attempt_XX` holds **exactly one** `final_blueprint__<strategy>.json` (only the winner strategy is retained)
- `project_data.db` `director_selections` and `stage_attempts` have only **9** rows at stage=3 — matching the 9 winner rounds across ep1-ep7, with no per-candidate rows
- `attempt_raw_rationale` is empty at stage=3 (0 rows)

So the only ground truth for candidate-wise comparison on the live `000_260412_a` session is `projects/000_260412_a/logs/session/llm_io.jsonl`, which captures the raw LLM response text per call. This terminal used `llm_io.jsonl` for all pair-wise measurement.

Implication: a future retention policy that writes losing candidates to `ep_XXXX/attempt_YY/candidate__<strat>.json` would make this audit reproducible without scraping the session log. Recording this only as a visibility gap for synthesis — not a retune proposal.

### Finding 3 — Producer-side `opening_transition` field is **almost never emitted** on ep1-ep7; binding contract lives downstream

Severity: `leak` (cross-terminal adjacent — this terminal flags and hands off)

Of **69** cleanly-paired trios across ep1-ep8:

- 62 trios (**89.9%**) had all 3 candidates return **no** `opening_transition` field at all (`has_ot=(False,False,False)`)
- 7 trios (**10.1%**) had all 3 candidates emit a dict-shaped `opening_transition` — and **all 7 are from ep8** (the ep that the downstream contract gate started requiring it on)
- 0 trios had a partial (some strategies emit, some don't) pattern in ep1-ep7

Concretely: ep1-ep7 producer LLM is not returning the `opening_transition` contract object at all. The live `apply_opening_transition_contract` path (`blueprint_ensemble.py:1506`) writes the field downstream using a normalization route, which means when the validator later complains "declared `direct_continuation` vs normalized `explicit_transition`", the mismatch is between **two downstream inferences**, not between a producer-declared value and a validator-expected value. The producer never got a vote.

Scope note: this belongs to T1 (prompt forensics — does the prompt ask for this?) and T5 (validator heuristic — is the normalized/declared comparison sound?). T6 records only the diversity dimension: **the ensemble cannot diversify the opening_transition contract because no strategy emits the field at all on ep1-ep7**.

Cross-terminal pointer: T1 + T5.

### Finding 4 — Prompt delta between strategies is 16 lines in a ~12,850-char prompt

Severity: `waste` (structural diversity ceiling)

Unified-diffing the ep1 attempt-1 trio's prompts (`action` vs `emotion`, `action` vs `dialogue`) yields exactly **16 diff lines each**, covering only:

- 1 banner line (`[V60.80 BLUEPRINT ENSEMBLE - 액션 중심]` → `- 감정 중심` or `- 대화 중심`)
- 1 header line (`[전략: 액션 중심]`)
- 5 directive bullets (tension range, focus pattern, pace/modality, emotion/dialogue mix, ending-hook style)

Total body sizes: `action` 12,848 chars, `emotion` 12,851 chars, `dialogue` 12,854 chars. Delta ≈ **0.1%** of prompt bytes. The cheap admission contract block, arc focus, constraint block, HUD context, opening-transition contract block, and every other structural field are **byte-identical** across all 3 strategies for the same attempt.

Implication: the upper bound on contract-level diversity is whatever the 6-bullet style directive can deflect during sampling at `temperature=0.7` — that is small, because none of the 6 bullets speaks to `opening_transition.type`, `protagonist_state` shape, `scene_breakdown` cardinality, or any validator-blocking field. The contract fields are all in the shared 99.9% block and thus sampled under the same posterior by all three strategies.

### Finding 5 — Diversity scoring on 69 paired trios

Severity: `hypothesis` (quantitative)

Using a **contract-relevant diversity score** — "share of trios where ≥1 candidate differs from the other 2 on this field":

| Field | Category | SAME rate | DIFF rate |
|---|---|---|---|
| `opening_transition.type` | contract-blocking (T1/T5 surface) | 67 / 69 = **97.1%** | 2 / 69 = 2.9% |
| `opening_transition` presence (has_ot) | contract-blocking | 69 / 69 = **100%** | 0 / 69 = 0.0% |
| `protagonist_state` key-set shape | contract-adjacent | 69 / 69 = **100%** | 0 / 69 = 0.0% |
| `scene_breakdown` cardinality (n_scenes) | contract-relevant | 32 / 69 = 46.4% | 37 / 69 = **53.6%** |
| `scene_breakdown` type-sequence | contract-relevant | 6 / 69 = 8.7% | 63 / 69 = **91.3%** |
| `integrated_scenario` head 60 chars | stylistic | 0 / 69 = 0% | 69 / 69 = **100%** |
| `ending_hook` head 60 chars | stylistic | 0 / 69 = 0% | 69 / 69 = **100%** |
| `core_tension` head 60 chars | stylistic | 0 / 69 = 0% | 69 / 69 = **100%** |
| `protagonist_state.mood` text | stylistic | 2 / 69 = 2.9% | 67 / 69 = **97.1%** |

Interpretation:

- **Stylistic diversity is near-complete.** Every trio writes a different opening sentence, different ending hook, different one-line core tension, and different mood description.
- **Structural diversity is partial.** Scene type-sequence diverges in 91% of trios (91% of the time at least one strategy picks a different scene-preset ordering) and scene count diverges in 54% of trios.
- **Contract-level diversity is zero or near-zero.** `protagonist_state` key-set shape is 100% convergent (every trio emits the same `(equipment, injuries, mood)` tuple on this live run). `opening_transition` presence is 100% convergent in each direction — either all 3 emit the field (ep8) or none do (ep1-ep7). `opening_transition.type` only differs on 2 of 69 trios, and both diff events are ep8 `direct_continuation` vs `explicit_transition`.

The 2 `opening_transition.type` diff trios are:

- ep8 k7: `action` + `emotion` both declared `direct_continuation`, `dialogue` declared `explicit_transition`. Director selected — but the session was interrupted before writing a verdict row for ep8.
- ep8 k9: same pattern — 2x `direct_continuation` + 1x `explicit_transition`.

### Finding 6 — Ensemble-wasted-on-contract rate is effectively 100% on ep1-ep7 for binding-contract rejections

Severity: `waste`

Definition per parent order §6 T6 step 4: a trio is `ensemble-wasted` if all 3 candidates share the same contract failure, so the fan-out did not help the contract at all. Applying the definition:

- **62 / 69 trios (89.9%)** had all 3 candidates return the SAME state on `has_ot=False`. On any attempt where the downstream `opening_transition` family rejected the round, fan-out contributed zero contract-level escape hatches — the validator's complaint was uniform across all 3 candidates because all 3 candidates were uniformly blind to the field.
- **69 / 69 trios (100%)** had all 3 candidates return the SAME `protagonist_state` key-set shape. Any `protagonist_state` placeholder / shape rejection would have killed all 3 identically.
- **32 / 69 trios (46.4%)** had all 3 candidates agree on `scene_breakdown` count — so roughly half the fan-outs also have zero structural escape hatch on scene-count contract.
- **6 / 69 trios (8.7%)** had all 3 candidates agree on scene type-sequence — so type-sequence convergence is rare but non-zero (and ep1 k1 is one of them).

Aggregated: for any rejection whose blocking condition touches `opening_transition`, `protagonist_state` shape, or (~half the time) `scene_breakdown` cardinality, the ensemble fan-out on this session gave the Director a choice of 3 identical-on-contract candidates. Those rejections therefore had to be resolved by retry — not by selection.

Cost of wasted spend (order of magnitude only; T8 owns the exact attribution):

- 228 fan-out calls across the 73 paired trios
- sample token cost from `llm_io.jsonl` = $0.06 ± $0.01 per call (claude-sonnet-4-6 at ~12.8K in, ~3K out)
- rough total fan-out cost ≈ **$13-15** across ep1-ep8 in this session
- rough subset spent on trios where all 3 converged on `has_ot=False` (62 trios × 3 calls × ~$0.06) ≈ **$11** — the portion that could not have contributed to defeating an `opening_transition` rejection no matter which candidate Director picked

### Finding 7 — ep4 had 4 whole-fan-out API-failure rounds

Severity: `waste`

Trios 1-4 of ep4 have 12 `BlueprintEnsembleGenerator` records (4 per strategy) where every response is 0 characters and `success=False` at 2026-04-13T10:16:31. `llm_calls` stage=3 shows `context_tag='backup_recovery'` on 6 of ep4's BlueprintEnsembleGenerator calls — confirming these are provider-side failures that triggered the backup-recovery retry path. These count as "fan-out spend with zero candidate output" and are distinct from contract-level convergence — they are provider reliability failures.

Not a diversity issue, but they do **inflate** the apparent count of fan-out rounds per ep4 without delivering any candidate. Flagging so synthesis does not double-count them as contract-convergent.

### Finding 8 — Asymmetric strategy counts on ep5 and ep7 signal strategy-specific re-rolls

Severity: `hypothesis`

Call counts per (ep, strategy):

- ep5: action=**11**, emotion=8, dialogue=8
- ep7: action=**14**, emotion=8, dialogue=8
- ep6: 10 / 10 / 10 (symmetric)
- ep2: 18 / 18 / 18 (symmetric)

On ep5 the action strategy got 3 extra calls; on ep7 it got 6 extra. These match a pattern where `_select_blueprint_ensemble_strategies(single_strategy="action_focused")` was invoked — i.e. the retry loop narrowed the fan-out to a single strategy (`blueprint_ensemble.py:384-390` is the only path that can produce this kind of single-strategy ensemble). The Director selected `action_focused` as the final winner on ep7 (round_num=10, `director_selections` row) but not on ep5 (where `emotion_focused` won). So on ep7 the single-strategy extra calls matched the eventual winner; on ep5 they did not.

This does not directly change the diversity score (the parallel-k pairing uses `min` per strategy, so extra single-strategy calls are dropped from the paired-trio sample). But it is relevant context for T2 and T7:

- the retry loop **does** sometimes collapse to 1-way fan-out — so diversity drops from 3 to 1 for those attempts entirely
- whether this collapse is triggered by a deliberate "single_strategy" retry or by per-strategy timeout at `_run_blueprint_ensemble_workers` is **not** determinable from `llm_io.jsonl` alone

Cross-terminal pointer: T2 (retry feedback loop audit — did the retry loop pin strategy?) and T8 (cost attribution — the extra single-strategy calls are cost that was not paired with fan-out diversity).

### Finding 9 — Directly on required-analysis step 5: ensemble-wasted → full-regenerate correlation is observationally consistent but not fully provable from this terminal's evidence

Severity: `hypothesis` / `gap`

Parent order §6 T6 step 5: "Cross-check whether `ensemble-wasted` attempts correlate with later-attempt full regenerate cycles."

What this terminal can verify:

- On ep1-ep7, the winning `round_num` values are 7, 10, 6, 6 (after 2x round-1 `FAILED`), 9, 10, 10. That is an average of **8.4 rounds per successful episode**.
- Every rejection on ep1-ep7 that blocked on `opening_transition` or `protagonist_state` (as per the `0_temp.txt:400-469` tail family documented in parent order §2.1) faced a trio that had all 3 candidates converging on the failed field (Finding 6). So Director could not select a contract-surviving candidate and the runtime had to loop.
- From `director_selections.fix_scope`, 5 of 9 winning rounds used `inplace` (local patch) and 4 used `''` (clean pass). None used `full`, but that's the winner — losing rounds' `fix_scope` is not persisted.

What this terminal **cannot** verify:

- the per-round verdict of losing rounds (whether they were `full` regenerate or `inplace` or `reject`) is not in the DB (`stage_attempts` only holds the winning row)
- the exact mapping from "ensemble-wasted trio" to "retry loop triggered full regenerate" requires reading T2's output (retry feedback loop audit); this terminal flags the correlation hypothesis but does not close it

Hypothesis handed to synthesis: **if** the retry loop sees no contract-diverse candidate in a fan-out, and **if** the repair router falls back to `fix_scope=full` when local repair is not feasible, then ensemble-wasted trios drive full regenerate cycles and the full-regenerate cost per ep is the largest correctable slice of Stage3 spend. T2 and T8 must close the loop.

## Cross-Terminal Pointers

- **T1 (prompt forensics)** — shared base prompt for all 3 strategies is ~12,835 chars and carries the `opening_transition` contract block, yet ep1-ep7 producer responses never emit the field. T1 should decide whether the prompt actually *teaches* `opening_transition` rather than just declaring it. (Finding 3, Finding 4)
- **T2 (retry feedback loop)** — asymmetric strategy counts on ep5 (+3 action) and ep7 (+6 action) suggest single-strategy retries. T2 should verify whether the retry loop collapses fan-out width on specific retry shapes, and whether feedback per strategy is strategy-preserving. (Finding 8)
- **T5 (validator heuristic)** — since ep1-ep7 producers never emit `opening_transition`, the validator's `direct_continuation` vs `explicit_transition` mismatch is between two **downstream** inferences. T5 should decide whether this comparison is sound when the producer gives no signal. (Finding 3)
- **T7 (director/validator rubric gap)** — the 2 `opening_transition.type` diff trios in ep8 (k7, k9) are the only real selection opportunities for this field in the whole session; T7 should check whether Director's rubric actually uses the declared value when it finally exists. (Finding 5)
- **T8 (cost attribution)** — rough fan-out cost ≈ $13-15 with roughly $11 spent on ensemble-wasted-on-`has_ot` trios. T8 should close the exact split. (Finding 6)
- **T10 (Stage4 writer smarts)** — not directly relevant; no cross-terminal pointer.

## Hypothesis Candidates For Synthesis

All labeled `candidate` only — not directives.

1. **Candidate H6-A: contract-level ensemble diversity on this live run is measurably zero for the rejection families that actually fire.** 62/69 (90%) of ep1-ep8 fan-out trios had all 3 candidates agree on `has_ot=False`; 69/69 (100%) agreed on `protagonist_state` key-set shape. On any rejection whose blocking condition touches these fields, Director chooses between 3 identical-on-contract candidates and the runtime has to loop. Evidence: Finding 5, Finding 6.
2. **Candidate H6-B: the 3-strategy prompt delta (16 lines out of ~12,850) is too narrow to force contract-level divergence.** The directive bullets only speak to tension range, focus pattern, pace, and ending-hook style — none of them speaks to contract-relevant fields. The stylistic diversity the ensemble does produce (100% on opening sentence, 100% on ending hook, 100% on core tension, 91% on scene-type sequence) rides almost entirely on sampling noise at temperature 0.7 on the shared 99.9% of the prompt, not on strategic divergence. Evidence: Finding 4, Finding 5.
3. **Candidate H6-C: "ensemble-wasted trios cause full regenerate cycles" is the most likely single correlation behind the 8.4-rounds-per-episode average**, but closing the loop requires T2 (retry feedback) and T8 (cost attribution) output before the claim can be bounded. This terminal has the diversity half of the equation; the retry-shape half is cross-terminal. Evidence: Finding 6, Finding 9.
4. **Candidate H6-D: the parent order's "5 strategies" count needs updating before the synthesis pass runs.** Current head fans out 3 strategies. Any math that assumed 5 will be off by 5/3 ≈ 1.67×. Evidence: Finding 1.
5. **Candidate H6-E: losing-candidate retention is a visibility gap that blocks reproducibility of this audit.** Without either writing losing-candidate `final_blueprint__<strat>.json` files per attempt or persisting per-candidate rows in `stage_attempts`/`attempt_raw_rationale`, every future diversity audit will have to re-scrape `llm_io.jsonl` and infer attempt boundaries from timestamps. Recording as a visibility gap, **not** as a retune proposal. Evidence: Finding 2.

## 3-Pass Audit Record

### Pass 1 — Scope and structure

- Every finding stays in T6's own axis: fan-out strategy parameterization, per-candidate divergence on contract fields, ensemble ROI under contract stress (parent order §6 T6 Scope IN). 
- T1 (prompt-text quality ranking), T5 (validator heuristic calibration), T7 (Director rubric composition), and T8 (cost attribution) findings are labeled as cross-terminal pointers, not ranked as conclusions here.
- No retune proposal; every finding is either observational (measured diversity rate) or labeled `hypothesis` / `candidate`.
- 3-way fan-out width is called out as a **data correction** to the parent order's 5-strategy claim — not as a defect in the ensemble.
- Non-goal check: no proposal to remove a strategy; no treatment of stylistic-only diversity as contract-level diversity (stylistic fields are tagged `stylistic` in the diversity table).

### Pass 2 — Evidence anchoring and arithmetic

- Re-verified `BLUEPRINT_STRATEGIES` has 3 entries (grep confirmed: `action_focused`, `emotion_focused`, `dialogue_focused`; no `conservative` / `balanced` hits anywhere in `modules/domain/agents/blueprint_ensemble.py`).
- Re-verified call counts per (ep, strategy) against `llm_io.jsonl`:
  - ep1: 4/4/4, ep2: 18/18/18, ep3: 6/6/6, ep4: 10/10/10, ep5: 11/8/8, ep6: 10/10/10, ep7: 14/8/8, ep8: 9/9/9
  - totals match the 82+73+73 = 228 fan-out calls reported in Evidence Anchors
- Re-verified paired-trio count at 73 (min-per-strategy within each ep: 4+18+6+10+8+10+8+9 = 73)
- Re-verified parse success: 69 trios parsed cleanly in all 3 candidates; 4 ep4 trios (at `2026-04-13T10:16:31`) failed because all 3 candidates returned empty strings — matches `llm_calls` `context_tag='backup_recovery'` for ep4 BlueprintEnsembleGenerator calls
- Re-verified the 62 vs 7 `has_ot` split: 62 trios with `has_ot=(False,False,False)` are ep1-ep7 + ep8 k1-k2, 7 trios with `has_ot=(True,True,True)` are all ep8 k3-k9
- Re-verified the 2 `opening_transition.type` diff trios: both ep8 (k7, k9), each with 2x `direct_continuation` + 1x `explicit_transition`
- Re-verified prompt byte delta: ep1 attempt-1 trio prompts are 12,848 / 12,851 / 12,854 chars; unified diff yields 16 diff lines per pair, covering exactly the banner line + the 6-bullet directive block
- Re-verified the `director_selections` winner rows (9 stage-3 rows across ep1-ep7) and `stage_attempts` winner rows (same 9); `attempt_raw_rationale` confirmed empty at stage=3
- Re-verified ep4 backup-recovery path via `llm_calls` `context_tag='backup_recovery'` (6 rows on ep4)
- Arithmetic cross-check on cost ballpark: 82+73+73 = 228 fan-out calls × ~$0.06 ≈ $13.7 — consistent with the $13-15 range quoted in Finding 6

### Pass 3 — Readability, non-overlap, residual uncertainty

- Each finding carries a file:line or artifact:path anchor (parent order §7 requirement)
- Cross-terminal pointers enumerated in their own section and referenced from the findings that produced them
- Every quantitative claim has the underlying raw count attached (e.g. "62 / 69 = 89.9%") so synthesis can re-derive the percentages without re-reading this deliverable's raw data
- UTF-8 check: all Korean substrings (action / emotion / dialogue strategy labels and similar) render as intended; no replacement-character or triple-question-mark placeholders observed; quoted log lines are anchored to their source file paths so the synthesis step can re-decode bytes if needed
- Non-overlap invariants re-checked against parent order §8:
  - did not rank Director rubric composition (T7 territory) — only cited that the 2 ep8 diff trios existed
  - did not judge validator heuristic correctness on `opening_transition` normalization (T5 territory) — only flagged that the producer never emitted the field on ep1-ep7
  - did not rank cheap admission effectiveness (T4 territory)
  - did not propose prompt rewrites (T1 territory)
  - did not propose removing any of the 3 strategies (parent order §6 T6 non-goal)
- Residual uncertainty items that keep this deliverable below 100% confidence:
  - whether the asymmetric ep5/ep7 counts are from `_select_blueprint_ensemble_strategies(single_strategy=...)` retries vs from per-strategy timeouts at `ENSEMBLE_TIMEOUT` — undecidable from `llm_io.jsonl` alone; handed to T2 (Finding 8)
  - whether losing rounds' `fix_scope` was `full` or `inplace` on each ensemble-wasted trio — undecidable from the DB (losing-round `stage_attempts` rows don't exist); handed to T2 (Finding 9)
  - whether 4 ep4 API-failure trios count in the denominator or not for future retention-policy decisions — this terminal kept them in the "paired trios analyzed" count (73) but excluded them from the "cleanly parsed" count (69), which is the count the diversity table uses
- None of the residuals change the three headline numbers (97.1% `opening_transition.type` SAME, 100% `protagonist_state` key-set SAME, 89.9% `has_ot` (False,False,False)), so the headline conclusion is stable at 96% confidence.

## Final Confidence

`96%`.
