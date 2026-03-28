# Gold Manuscript Benchmark MVP Survey

Date: 2026-03-27
Mode: survey-only
Scope: `gold manuscript benchmark` MVP setup survey only. No code, schema, harness, DB, or benchmark implementation was performed in this turn.
Workspace baseline commit: `155906f3adb1c2f4a3810ce359f6b59124d8556a`
Primary source brief: `docs/2026-03-27/gold-manuscript-benchmark-compact-handoff.md`

## Recommendation Snapshot

- recommended MVP type: `manuscript-only`
- recommended source corpus candidates: `projects/코덱스_테스트__seed_live_run_capture_20260320_092956`, `projects/canary_0325`, `projects/기록용/00_260315`
- reusable seams: terminal manuscript truth resolver, manuscript DB/range loaders, prompt excerpt compaction, continuity validator, validation/scoring surface, optional world-state/fact-ledger/state-text verifier
- scoring split: auto = artifact truth and deterministic continuity/text metrics; semi-auto = LLM scoring plus mismatch review; manual = long-horizon payoff, voice, ambiguous contradiction adjudication
- next execution step: `compact SSOT not needed`

## Handoff Hypothesis Check

The handoff says this lane is not a live-canary replacement and should stay focused on long-form narrative understanding, state retention, continuity preservation, and forward-constraint inference (`docs/2026-03-27/gold-manuscript-benchmark-compact-handoff.md:14-16`). That premise is valid for this workspace survey. The same handoff also says the package can stay compact and that build order should be manuscript-only first, lightweight ledger second (`docs/2026-03-27/gold-manuscript-benchmark-compact-handoff.md:186-205`). Current code seams support that ordering better than a ledger-first design.

## Corpus Candidates

### 1. `projects/코덱스_테스트__seed_live_run_capture_20260320_092956`

This is the best starter corpus for a 2-week MVP because it already has structured manuscript payloads and a clean terminal authority trail. Structured manuscript JSONs already exist for at least episodes 1 to 3 with `ep_num`, `title`, and `content_length` fields in `projects/코덱스_테스트__seed_live_run_capture_20260320_092956/plans/manuscripts/manuscript_ep1.json:2-5`, `projects/코덱스_테스트__seed_live_run_capture_20260320_092956/plans/manuscripts/manuscript_ep2.json:2-5`, and `projects/코덱스_테스트__seed_live_run_capture_20260320_092956/plans/manuscripts/manuscript_ep3.json:2-5`. Stage 4 coverage is complete in `projects/코덱스_테스트__seed_live_run_capture_20260320_092956/logs/runtime_audit_summary.json:101-110`, and episode 6 has a final PASS authority row pointing at a terminal manuscript artifact in `projects/코덱스_테스트__seed_live_run_capture_20260320_092956/logs/episode_production.jsonl:11`.

Recommendation: use this as the first MVP work because it minimizes packaging work. The benchmark can start from already-materialized manuscripts instead of inventing a new extraction layer.

### 2. `projects/canary_0325`

This is the best second corpus if the MVP wants more continuity pressure than the seed project. Stage 3 coverage shows nine considered attempts with matching pass-rate and director-selection counts in `projects/canary_0325/logs/stage34_canary_summary.json:13-19`. Stage 4 has nineteen complete final attempts in `projects/canary_0325/logs/runtime_audit_summary.json:102-111`. Episode 9 has a final PASS authority row, with the terminal artifact resolved to `patched_after_fix__A_InPlace.txt`, in `projects/canary_0325/logs/episode_production.jsonl:38`.

Recommendation: make this the second work once the first single-work loop is stable. It provides stronger repair-path and continuity stress than the seed corpus.

### 3. `projects/기록용/00_260315`

This is the best longer-horizon candidate after the first two because it already reaches episode 11 and still has a final PASS terminal row. Stage 4 reports fourteen complete final attempts in `projects/기록용/00_260315/logs/runtime_audit_summary.json:100-110`. Episode 11 has a final PASS authority row pointing at `final_manuscript__A.txt` in `projects/기록용/00_260315/logs/episode_production.jsonl:19`.

Recommendation: use this as the third candidate when testing longer-horizon state retention and future-constraint inference. It is better as wave 2 than as the very first corpus because it lacks the seed corpus's ready-made manuscript JSON payloads.

### Deferred External Corpus Route

There is a real-manuscript ingestion route in the workspace, but it is not the smallest MVP path. `scripts/extract_manuscript_samples.py` imports EPUB extraction helpers from `scripts.investment_corpus_support` and points at a NAS-rooted corpus path in `scripts/extract_manuscript_samples.py:22-30`. The same script extracts title samples through an offline path in `scripts/extract_manuscript_samples.py:88-95`. The prior OPUS survey also classifies this route as offline corpus tooling and benchmark ground-truth material, not a live runtime lane (`docs/2026-03-18/OPUS/real-manuscript-quality-corpus-usage-direction-3pass-audit.md:43-44`, `docs/2026-03-18/OPUS/real-manuscript-quality-corpus-usage-direction-3pass-audit.md:87-88`, `docs/2026-03-18/OPUS/real-manuscript-quality-corpus-usage-direction-3pass-audit.md:117-121`, `docs/2026-03-18/OPUS/real-manuscript-quality-corpus-usage-direction-3pass-audit.md:195-201`).

Recommendation: treat the external EPUB route as a post-MVP corpus expansion lane, not the first MVP source.

## Data Model MVP

The smallest MVP should be one UTF-8 JSON manifest per work, path-referenced into the existing `projects/...` artifacts, with `gold_ledger` nullable. Do not start with a larger benchmark family or separate schema package.

Recommended shape:

```json
{
  "work_id": "seed_live_run_capture_20260320",
  "source_project": "projects/코덱스_테스트__seed_live_run_capture_20260320_092956",
  "cases": [
    {
      "case_id": "ep3_to_ep4",
      "checkpoint": {
        "episode_span": [1, 3],
        "manuscript_refs": [
          {"ep_num": 1, "path": "projects/.../manuscript_ep1.json"},
          {"ep_num": 2, "path": "projects/.../manuscript_ep2.json"},
          {"ep_num": 3, "path": "projects/.../manuscript_ep3.json"}
        ],
        "prompt_excerpt_strategy": "head_middle_tail_v1"
      },
      "gold_continuation": {
        "ep_num": 4,
        "artifact_path": "projects/.../logs/artifacts/stage4/ep_0004/attempt_XX/final_manuscript__A.txt",
        "artifact_sha256": "..."
      },
      "gold_ledger": null
    }
  ]
}
```

Why this is the smallest viable format:

- `ManuscriptCandidate` already normalizes the payload shape around `manuscript`, `title`, `state_updates`, and `metadata`, so the benchmark package should stay close to a compact JSON object instead of inventing a large new schema (`modules/models/manuscript.py:18-30`).
- The terminal authority resolver already computes `artifact_path`, `artifact_sha256`, `selection_artifact_path`, `first_line`, and `last_narrative_line` from PASS rows in `logs/episode_production.jsonl`, so path-referenced gold continuation is already a natural seam (`modules/core/stagewise_manuscript_truth_report.py:186-218`).
- Existing prompt compaction logic already slices manuscripts into head/middle/tail excerpts, which is enough for a checkpoint MVP without storing a second derived corpus copy (`main_a.py:3671-3699`).

Checkpoint format recommendation:

- keep checkpoint as JSON, not plain text
- store ordered episode refs, episode span, and one excerpt strategy tag
- do not store a full derived ledger in checkpoint v1

Gold continuation format recommendation:

- store gold continuation as a JSON object with terminal `artifact_path` and `artifact_sha256`
- resolve the actual raw text from the authority artifact on load
- keep the first MVP at full-episode continuation, not sub-scene slices

Optional gold ledger format recommendation:

- if added, keep it as a narrow nullable JSON object under the same case
- first families should be only `relationships`, `active_items`, `active_pressure_vectors`, `world_laws`, `timeline`, and protagonist `assets` or `injuries`
- do not attempt full BI-equivalent state

The narrow-family recommendation matches the current world-state and ledger surfaces. `WorldState` already centers protagonist status, NPC life state, relationships, active items, active pressure vectors, world laws, timeline, motivations, and promises in `modules/core/world_state.py:91-115`. `FactLedger` already keeps `characters`, `numbers`, `items`, `locations`, and `organizations` in `modules/core/fact_ledger.py:166-175`. The reason to keep ledger optional is that both update flows currently consume `state_changes` rather than raw manuscript text, in `modules/core/world_state.py:768-792` and `modules/core/fact_ledger.py:206-224`, so a ledger-first benchmark would require a new extraction or annotation step immediately.

## Reusable Seams

### Manuscript Truth and Loading

`modules/core/stagewise_manuscript_truth_report.py:100-106` already classifies terminal artifact kinds, and `modules/core/stagewise_manuscript_truth_report.py:186-218` already materializes authoritative PASS rows with resolved artifact path, SHA, and terminal line snippets. This is the strongest seam for gold continuation authority.

`modules/core/db_manager.py:501-513` persists manuscripts with title and content, and `modules/core/db_manager.py:520-538` reloads them with `hud_snapshot`. `modules/core/db_manager.py:1990-2008` and `modules/core/db_manager.py:2013-2027` already provide recent/range manuscript fetches. `modules/core/db_manager.py:2079-2097` already provides excerpt-only retrieval. These are the right checkpoint loading seams.

`main_a.py:3645-3649` already asks the DB for the recent manuscript batch, and `main_a.py:3671-3699` already compacts long manuscripts into head/middle/tail excerpts for prompt use. That compaction logic can be reused directly as a benchmark checkpoint builder pattern.

### Continuity and Validator Surface

`modules/validation/validation_orchestrator.py:338-376` defines the authoritative validation public surface, including `blocking_result`, `scoring_result`, `advisory_result`, `continuity_result`, and `total_score`. `modules/validation/validation_orchestrator.py:379-418` already stages the run into pre-scoring validators, scoring, retrospective validation, advisory penalties, and finalization. This is the correct benchmark scoring entry seam if the MVP wants to reuse current validator output instead of inventing a second scoring contract.

`modules/validation/continuity_validator.py:290-315` already fetches the previous manuscript from explicit context, history, or DB. `modules/validation/continuity_validator.py:435-465` checks opening carryover for active pressure vectors. `modules/validation/continuity_validator.py:467-497` checks duplicate item reacquisition drift. `modules/validation/continuity_validator.py:540-568` checks opening inventory count drift. These are directly reusable for automatic continuity checks against checkpoint-to-continuation transitions.

### Optional Ledger and State Verification

`main_a.py:3855-3863` binds the runtime state tracker to `world_state` and lazily initializes `FactLedger`. `modules/core/world_state.py:1106-1130` and `modules/core/world_state.py:1137-1159` already expose summary text that includes pressure vectors, world laws, timeline, and other retained state. `modules/core/fact_ledger.py:607-625` already exposes a prompt-ready ledger summary.

`modules/core/state_text_verifier.py:85-144` already provides an advisory `verify()` surface that returns `verified`, `mismatches`, and `corrections` after checking extracted truth against manuscript text. This is reusable for lightweight-ledger mismatch review, but not as a purely automatic lane because it depends on an agent call and returns advisory, non-blocking output.

### Lightweight Comparison Pattern

`scripts/block_continuity_checker.py:46-52` and `scripts/block_continuity_checker.py:77-83` already show a simple scalar continuity-checking pattern for adjacent blocks. It is treatment-oriented rather than manuscript-oriented, but the comparison shape is relevant for a compact benchmark scorer.

## Scoring Architecture

The handoff says the first useful benchmark tasks are next-arc constraint inference, gold continuation contrast, contradiction counting, and later payoff recall and voice checks (`docs/2026-03-27/gold-manuscript-benchmark-compact-handoff.md:103-149`, `docs/2026-03-27/gold-manuscript-benchmark-compact-handoff.md:180-190`, `docs/2026-03-27/gold-manuscript-benchmark-compact-handoff.md:215-221`). Current workspace seams support a split scorer better than a monolithic one.

### Auto

- artifact truth: PASS-row authority, artifact-path resolution, artifact hash, and terminal artifact kind via `modules/core/stagewise_manuscript_truth_report.py:186-218`
- deterministic checkpoint packaging: DB range/recent/excerpt retrieval via `modules/core/db_manager.py:1990-2027`, `modules/core/db_manager.py:2079-2097`, and prompt excerpt compaction via `main_a.py:3671-3699`
- deterministic continuity checks: previous-manuscript fetch, active-pressure carryover, item reacquisition drift, and inventory-count drift via `modules/validation/continuity_validator.py:290-315`, `modules/validation/continuity_validator.py:435-465`, `modules/validation/continuity_validator.py:467-497`, and `modules/validation/continuity_validator.py:540-568`
- deterministic manuscript metrics: sanitize/truncation metadata and Python-computable style metrics via `modules/validation/scoring_validator.py:120-127`, `modules/validation/scoring_validator.py:172-179`, and `modules/validation/scoring_validator.py:181-191`

### Semi-Auto

- LLM-scored narrative axes through the existing scoring validator. The default breakdown is `character_consistency`, `emotion_arc`, `dialogue_quality`, `commercial_appeal`, `pattern_diversity`, and `reader_satisfaction` in `modules/validation/scoring_validator.py:53-60`, and the validator explicitly separates Python scores from LLM-evaluated scores in `modules/validation/scoring_validator.py:181-206`
- gold-ledger mismatch review via `modules/core/state_text_verifier.py:85-144`
- next-arc or next-block constraint inference against later gold text, which the handoff defines but which still needs model judgment rather than pure deterministic rules (`docs/2026-03-27/gold-manuscript-benchmark-compact-handoff.md:103-117`)

### Manual

- long-horizon foreshadow and payoff judgment, because the handoff's later-payoff comparison is conceptually clear but not yet backed by a stable workspace annotator (`docs/2026-03-27/gold-manuscript-benchmark-compact-handoff.md:137-149`)
- voice consistency against gold dialogue, because the handoff explicitly wants it but current reusable seams do not expose a stable automatic voice judge (`docs/2026-03-27/gold-manuscript-benchmark-compact-handoff.md:180`)
- ambiguous contradiction adjudication when the gold corpus itself contains repair history or multiple acceptable phrasings

## Risks and Unknowns

The biggest MVP risk is not loading manuscripts. It is pretending that gold-ledger truth already exists for raw manuscripts. Current `world_state` and `fact_ledger` update paths both expect `state_changes`, not free-form manuscript text (`modules/core/world_state.py:768-792`, `modules/core/fact_ledger.py:206-224`). That is why manuscript-only should come first.

The second risk is corpus authority quality. The recommended starter corpora are workspace-generated final artifacts, not externally curated published novels. That is acceptable for an MVP whose immediate target is continuity, state retention, and forward-constraint benchmarking inside the current system lane, but it is weaker than a true external gold corpus for broader quality claims. The external EPUB route exists, but it is still offline and NAS-bound (`scripts/extract_manuscript_samples.py:22-30`, `scripts/extract_manuscript_samples.py:88-95`).

The third risk is repair-noise in some corpora. `projects/canary_0325` and `projects/기록용/00_260315` both show complete final-attempt coverage but `warn` stage-4 status in their audit summaries (`projects/canary_0325/logs/runtime_audit_summary.json:102-111`, `projects/기록용/00_260315/logs/runtime_audit_summary.json:100-110`). That does not block benchmark use if the benchmark takes terminal PASS artifacts as gold truth, but it means artifact provenance must stay explicit.

`projects/0324_00_` is a valid compact backup corpus rather than a top-3 recommendation. It has sixteen complete final attempts in `projects/0324_00_/logs/runtime_audit_summary.json:106-115` and a final PASS authority row for episode 8 in `projects/0324_00_/logs/episode_production.jsonl:28`.

## Recommendation

Use a manuscript-only MVP first. That is both the handoff's recommended build order and the best match for the current codebase (`docs/2026-03-27/gold-manuscript-benchmark-compact-handoff.md:201-205`). Start with one work only, specifically `projects/코덱스_테스트__seed_live_run_capture_20260320_092956`, because it already has structured manuscript payloads plus terminal PASS artifact authority (`projects/코덱스_테스트__seed_live_run_capture_20260320_092956/plans/manuscripts/manuscript_ep1.json:2-5`, `projects/코덱스_테스트__seed_live_run_capture_20260320_092956/logs/runtime_audit_summary.json:101-110`, `projects/코덱스_테스트__seed_live_run_capture_20260320_092956/logs/episode_production.jsonl:11`). Add `projects/canary_0325` second if the first loop proves stable. Add a lightweight gold ledger only after the manuscript-only loop is producing stable authority loading and useful contrast scores.

The benchmark should remain a separate lane from live canaries and soak canaries, exactly as the handoff requires (`docs/2026-03-27/gold-manuscript-benchmark-compact-handoff.md:14-16`, `docs/2026-03-27/gold-manuscript-benchmark-compact-handoff.md:310-311`). For the next execution step, a separate compact SSOT is not needed yet. This survey plus the existing handoff is already narrow enough for a single-work manuscript-only MVP implementation request.

## 3-Pass Audit

Pass 1, scope check: the document stayed within survey-only boundaries and answered the five required questions.

Pass 2, evidence check: every recommendation was tied to live workspace file evidence or the stated handoff lines; speculative claims about ledger automation were explicitly downgraded to risk or semi-auto status.

Pass 3, execution check: the recommendation stayed narrow, prioritized 2-week ROI over larger architecture, and did not require a new harness, schema, or benchmark family design.

Confidence: 0.96
Final decision: save approved
