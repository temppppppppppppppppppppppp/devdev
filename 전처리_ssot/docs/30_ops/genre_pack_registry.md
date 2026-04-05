# Genre Pack Registry

Date: 2026-03-20
Status: final
Scope: preprocess-only registry
Authority: canonical under `전처리_ssot/docs/30_ops`
Confidence Target: 95%
Current Confidence: 95% for registry readiness

## 1. Intent

- Track which genre-pack lanes exist.
- Separate lane-level progress from artifact-level status.
- Give future operators one place to check the active tranche, canonical roots, and next execution gate.

This registry does not replace the artifact status enum from the roadmap. It tracks operational lane state only.

## 2. Registry Contract

### 2.1 Lane Phase Vocabulary

Use these lane phases only:

- `schema_locked`
- `pilot_active`
- `pilot_complete_pending_consolidation`
- `consolidation_active`
- `provisional_pack_available`
- `canonical_pack_available`
- `queued_pending_manifest`
- `blocked`

These are lane states. They are not substitutes for artifact statuses such as `candidate`, `provisional`, `canonical`, or `rejected`.

### 2.2 Required Fields Per Entry

Each registry entry must state:

- `genre_family`
- `lane_phase`
- `current_tranche_id`
- `current_manifest_path`
- `canonical_genre_root`
- `canonical_scene_root`
- `sample_root`
- `source_corpus_root`
- `work_specific_handoff_target`
- `active_title_count`
- `reserve_title_count`
- `next_gate`
- `blocking_risks`
- `owner_note`

## 3. Active Registry

| genre_family | lane_phase | current_tranche_id | active_title_count | reserve_title_count | next_gate |
| --- | --- | --- | --- | --- | --- |
| `wuxia` | `pilot_active` | `wuxia__t1__2026-03-20` | `3` | `1` | decompose first selected title in `10 + 10` episode shards |
| `modern_fantasy_business_power` | `queued_pending_manifest` | none | `0` | `0` | verify corpus availability and lock the first tranche manifest |

## 4. Entry Details

### 4.1 `wuxia`

- `genre_family`: `wuxia`
- `lane_phase`: `pilot_active`
- `current_tranche_id`: `wuxia__t1__2026-03-20`
- `current_manifest_path`: `전처리_ssot\docs\30_ops\tranche_manifests\tranche_manifest__wuxia__t1__2026-03-20.json`
- `canonical_genre_root`: `전처리_ssot\docs\20_db_and_materials\materials\genre_notes\wuxia`
- `canonical_scene_root`: `전처리_ssot\docs\20_db_and_materials\materials\scene_bank\wuxia`
- `sample_root`: `전처리_ssot\docs\20_db_and_materials\samples\golden\wuxia`
- `source_corpus_root`: `docs\실물기반 사각지대 테스트\원고`
- `work_specific_handoff_target`: `treatments\preprocess\{work_id}`
- `active_title_count`: `3`
- `reserve_title_count`: `1`
- `next_gate`: first title tranche must finish segmentation shard 1, segmentation shard 2, tranche merge, pass1, pass2, pass3, and adversarial review before title two starts
- `blocking_risks`: label drift during first tranche; scene-card explosion before dedupe; accidental leakage of source-specific furniture
- `owner_note`: this is the first lane because world rules, faction pressure, grievance chains, and BI slot extraction are structurally explicit

### 4.2 `modern_fantasy_business_power`

- `genre_family`: `modern_fantasy_business_power`
- `lane_phase`: `queued_pending_manifest`
- `current_tranche_id`: none
- `current_manifest_path`: none
- `canonical_genre_root`: `전처리_ssot\docs\20_db_and_materials\materials\genre_notes\modern_fantasy_business_power`
- `canonical_scene_root`: `전처리_ssot\docs\20_db_and_materials\materials\scene_bank\modern_fantasy_business_power`
- `sample_root`: `전처리_ssot\docs\20_db_and_materials\samples\golden\modern_fantasy_business_power`
- `source_corpus_root`: pending corpus validation
- `work_specific_handoff_target`: `treatments\preprocess\{work_id}`
- `active_title_count`: `0`
- `reserve_title_count`: `0`
- `next_gate`: verify available real-manuscript corpus, write tranche manifest, then start the first `10 + 10` episode pilot title
- `blocking_risks`: mixed intake with hunter or urban action lanes; vague business language entering the bank without mechanism anchors
- `owner_note`: this lane remains intentionally narrower than all `현판`; the first pack is business-power only

## 5. Operating Rules

- Every registry update that changes `lane_phase`, `current_tranche_id`, or `current_manifest_path` must cite the changed artifact path directly.
- A lane may not advance to `pilot_complete_pending_consolidation` until the first title tranche passes `pass1`, `pass2`, `pass3`, and adversarial review.
- A lane may not advance to `canonical_pack_available` until the publication gates in the roadmap are satisfied.
- If a lane becomes blocked, the blocking reason must be written here before any replacement tranche is started.

## 6. 3-Pass Record

### Pass 1 Result

- Separated lane-level registry state from artifact-level status.
- Locked the required fields so future operators do not invent a second registry shape.

### Pass 2 Result

- Added direct path fields for manifest, canonical roots, and handoff target.
- Added a next-gate field so the registry is actionable, not just descriptive.

### Pass 3 Result

- Added blocking-risk and lane-transition rules.
- Kept the initial scope narrow to `wuxia` active and `modern_fantasy_business_power` queued.

## 7. Adversarial Review Record

Primary failure modes considered:

- lane state being confused with artifact status
- broad `현판` scope sneaking into the first business-power lane
- operators skipping the manifest and updating the registry by memory

Mitigations added:

- separate lane phase vocabulary
- manifest path as a required field
- explicit narrow-scope note for `modern_fantasy_business_power`
