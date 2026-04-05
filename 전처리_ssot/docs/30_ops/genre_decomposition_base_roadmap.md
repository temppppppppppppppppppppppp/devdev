# Genre Decomposition Base Roadmap and Operating Contract v1

Date: 2026-03-20
Status: final
Scope: preprocess-only
Authority: canonical under `전처리_ssot`
Execution Audience: Opus, Sonnet, and human operators
Confidence Target: 95%
Current Confidence: 95% for roadmap-contract adequacy only; execution confidence must be revalidated after Tranche 0 companion artifacts exist

## 1. Intent

- Build a reusable `작품 분해 기지` so new `Phase 0 -> TR -> BI` work starts from distilled structure assets instead of re-reading raw corpus every time.
- Keep this effort strictly inside preprocess. It must not require runtime wiring changes or `글도비 시스템` realization work.
- Start with `무협` and `현판 business-power` because they have the highest immediate reuse value and the clearest transfer surface.

This document is not a loose brainstorm. It is the operating contract for how the decomposition base will be built, audited, and published.

## 2. Decision Summary

The correct starting structure is a split-authority model, not a single-folder model.

### 2.1 Canonical Decision

- `manual raw-corpus workspace` is the raw-corpus harbor and scratch workbench.
- `전처리_ssot` is the canonical home for distilled labels, contracts, roadmaps, audits, and reusable genre packs.
- `treatments\preprocess\{work_id}\` remains the work-specific handoff zone for actual `source_manifest`, `profile_lock`, `material_bundle_summary`, and `phase0_ready_snapshot`.

### 2.2 Why This Is Better Than Either Extreme

If everything starts in `수동_글도비`, canonical drift appears later during absorption.

If raw corpus itself is moved into `전처리_ssot` from day one, repo weight, path sprawl, and copyright-risk surface grow too early.

The stable split is:

- raw bytes and scratch extraction: `수동_글도비`
- canonical abstraction and audit: `전처리_ssot`
- work-specific handoff outputs: `treatments/preprocess/{work_id}`

This minimizes future migration pain because only distilled outputs are promoted into SSOT. The heavy raw source layer never becomes the governing authority.

## 3. Non-Goals

- Do not directly wire raw corpus into runtime prompt injection.
- Do not treat a real manuscript as an unquestionable SSOT.
- Do not start with "few-shot first" and invent the rest later.
- Do not mix `현판 business-power` and `현판 hunter/urban action` into one first-generation pack.
- Do not allow a single popular title to dominate label definitions for the whole genre.

## 4. Authority Model and Path Contract

| Layer | Role | Canonical Path | Allowed Scratch | Authority Rule |
| --- | --- | --- | --- | --- |
| L0 raw corpus | source bytes, title intake, extraction scratch | none inside main repo | `수동_글도비/raw_corpus/`, `수동_글도비/workbench/` | authoritative only for raw source existence and bytes |
| L1 distilled genre assets | taxonomy, cards, slot contracts, benchmark packs | `전처리_ssot/docs/20_db_and_materials/` and `전처리_ssot/docs/30_ops/` | scratch copies allowed outside SSOT | authoritative for reuse, labeling, and audit |
| L2 work-specific preprocess | per-`work_id` handoff outputs | `treatments/preprocess/{work_id}/` | local notes allowed under work folder | authoritative for that work's `Phase 0` gate |
| L3 final narrative outputs | `Phase 0`, `TR`, `BI` | `treatments/`, `bible/` | none | authoritative final artifacts |

## 5. What Is Actually Being Built

`작품 분해 기지` is not one artifact. It is a layered asset system.

### 5.1 Core Asset Families

1. `corpus_manifest`
- tracks what raw works exist, where they live, what episodes are available, and what legal or operational notes apply.

2. `title_registry_card`
- identifies one work as a decomposition target and records why it belongs in a genre pack.

3. `world_rule_card`
- extracts genre-world rules that must survive transfer into new projects.

4. `arc_cadence_map`
- captures macro rhythm: escalation interval, payoff timing, recovery spacing, revelation spacing, cliffhanger recurrence.

5. `block_archetype_card`
- defines reusable block-level progression units for `TR`.

6. `scene_card`
- defines reusable scene-level units for prompt assets, structural borrowing, and later few-shot construction.

7. `hook_payoff_ledger`
- captures setup, deferred payoff, callback timing, and cliffhanger conversion patterns.

8. `voice_card`
- captures character-voice behavior, not whole-work prose imitation.

9. `anti_pattern_card`
- records seductive but harmful patterns that create fake density, fake expertise, or genre contamination.

10. `bi_state_slot_contract`
- maps what must be preserved into `BI` state truth, especially current status, faction standing, reputation, resource state, and unresolved risk.

11. `few_shot_exemplar`
- short distilled exemplar for LLM use. This is one artifact, not the whole methodology.

12. `anti_shot_exemplar`
- short negative exemplar that shows what a tempting but invalid imitation looks like and why it fails.

13. `blind_benchmark_set`
- comparison set used after generation or pack publication to test whether the distilled contract still produces genre-faithful structure.

### 5.2 Few-Shot Position

Few-shot is downstream, not upstream.

The correct order is:

`raw work -> decomposition -> labeled cards -> distilled contract -> few-shot`

The wrong order is:

`raw work -> excerpt some passages -> call it methodology`

### 5.3 Minimum Fields for Core Artifacts

The operator must not invent schemas ad hoc. The minimum fields below are mandatory.

For bundle artifacts such as `scene_cards__...json`, `block_cards__...json`, and `hook_payoff__...md`, the fields below define one entry inside the bundle unless explicitly stated otherwise.

#### `corpus_manifest`

- `corpus_id`
- `snapshot_date`
- `genre_family`
- `title_entries`
- `source_root`
- `availability_status`
- `legal_or_ops_notes`
- `status`

#### `title_registry_card`

- `title_id`
- `title_slug`
- `display_title`
- `genre_family`
- `subtype`
- `source_root`
- `episodes_available`
- `selection_role`
- `representative_why`
- `overfit_risks`
- `intake_decision`
- `status`

#### `world_rule_card`

- `rule_id`
- `rule_statement`
- `genre_family`
- `supporting_title_ids`
- `evidence_anchors`
- `transferable_core`
- `must_not_copy`
- `related_bi_slots`
- `status`

#### `arc_cadence_map`

- `cadence_id`
- `title_id`
- `arc_id`
- `episode_start`
- `episode_end`
- `escalation_interval`
- `payoff_interval`
- `recovery_interval`
- `revelation_interval`
- `cliffhanger_pattern`
- `confidence`
- `notes`

#### `block_archetype_card`

- `archetype_id`
- `genre_family`
- `function_label`
- `trigger`
- `core_objective`
- `pressure_source`
- `reward_type`
- `state_change`
- `common_failure_mode`
- `evidence_anchors`
- `status`

#### `scene_card`

- `scene_id`
- `title_id`
- `episode_range`
- `function_label`
- `entry_state`
- `conflict_kernel`
- `turn_point`
- `exit_state`
- `carryover_signal`
- `evidence_anchors`
- `evidence_summary`
- `must_not_copy`
- `status`

#### `hook_payoff_ledger`

- `seed_id`
- `title_id`
- `introduced_at`
- `seed_type`
- `callback_due_window`
- `payoff_mode`
- `if_unresolved_cost`
- `evidence_anchors`
- `evidence_summary`
- `status`

#### `voice_card`

- `voice_id`
- `genre_family`
- `character_role`
- `speech_rhythm`
- `preferred_move`
- `dominance_signal`
- `deference_signal`
- `taboo_phrases`
- `evidence_anchors`
- `must_not_copy`
- `status`

#### `anti_pattern_card`

- `anti_pattern_id`
- `genre_family`
- `failure_label`
- `why_it_looks_good_at_first`
- `why_it_fails_structurally`
- `evidence_anchors`
- `prevention_rule`
- `status`

#### `bi_state_slot_contract`

- `slot_name`
- `genre_family`
- `slot_purpose`
- `source_evidence_rule`
- `update_trigger`
- `expected_tr_support`
- `disallowed_placeholder_examples`
- `status`

#### `few_shot_exemplar`

- `exemplar_id`
- `genre_family`
- `target_asset`
- `input_shape`
- `expected_output_shape`
- `max_length_rule`
- `why_this_is_safe`
- `status`

#### `anti_shot_exemplar`

- `anti_shot_id`
- `genre_family`
- `failure_type`
- `bad_pattern_summary`
- `why_it_fails`
- `rejection_signal`
- `status`

#### `blind_benchmark_case`

- `benchmark_id`
- `genre_family`
- `input_bundle`
- `expected_signals`
- `failure_signals`
- `grading_rule`
- `status`

### 5.4 Canonical Format, Granularity, ID Model, and Label Grammar

#### 5.4.1 Canonical File Format

- JSON is mandatory for structured bundle artifacts: `corpus_manifest`, `arc_cadence_map`, `scene_cards`, `block_cards`, `bi_state_slot_contract`, `tranche_manifest`, and `dry_run_scorecard`.
- Markdown is mandatory for interpretive card or review artifacts: `title_registry_card`, `world_rule_card`, `voice_card`, `anti_pattern_card`, `hook_payoff_ledger`, `few_shot_exemplar`, `anti_shot_exemplar`, `audit_checklist`, and `consolidation_summary`.
- No canonical artifact may switch file type after publication without a version bump and audit note.

#### 5.4.2 One-File-Per-Card vs Bundle Rule

- One file per card: `title_registry_card`, `world_rule_card`, `voice_card`, `anti_pattern_card`, `few_shot_exemplar`, `anti_shot_exemplar`, `blind_benchmark_case`.
- One file per title tranche: `arc_cadence_map`, `scene_cards`, `block_cards`, `hook_payoff`.
- One file per genre version: `taxonomy`, `bi_state_slot_contract`, `benchmark_rubric`, `genre_pack_registry_entry`.
- No operator may mix card and bundle granularity inside the same artifact family.

#### 5.4.3 Stable ID Model

- `title_id = {genre_family}__title__{title_slug}`
- `rule_id = {genre_family}__rule__{rule_slug}__v{n}`
- `archetype_id = {genre_family}__block__{function_label}__v{n}`
- `scene_id = {title_id}__ep{start:03d}-{end:03d}__scene_{local_index:03d}`
- `voice_id = {genre_family}__voice__{role_slug}__v{n}`
- `anti_pattern_id = {genre_family}__anti__{failure_slug}__v{n}`
- `benchmark_id = {genre_family}__benchmark__case_{index:03d}__v{n}`
- Once an ID becomes `canonical`, the ID is immutable. Revisions use `version`, `supersedes`, or `merged_into`; they do not silently rename.

#### 5.4.4 Controlled Status Enum

- Allowed statuses are `candidate`, `provisional`, `canonical`, and `rejected`.
- `candidate` is allowed for one-title evidence or unresolved disagreement.
- `provisional` is allowed only after a consolidation pass with at least two supporting titles.
- `canonical` is allowed only after the publication gates in section 13 are satisfied.
- `rejected` must be preserved in archive or audit records; it is not deleted from history.

#### 5.4.5 Label Grammar

- Labels must be lower `snake_case`.
- Labels must describe function, pressure, reward, or state change; never title-specific nouns.
- Labels must not contain proper nouns, signature move names, or proprietary twist names from the source.
- Labels should usually fit within `3` to `8` tokens.
- If two operators cannot distinguish a label from a neighboring label in one sentence, the label is too vague and must be rewritten.

### 5.5 Cloning Mode to Asset Map

If a future operator says "clone X", translate it into asset work, not raw copying.

| Target | Primary Asset | Secondary Asset | Must Not Be Copied Directly |
| --- | --- | --- | --- |
| narrative cloning | `arc_cadence_map` | `hook_payoff_ledger` | source-specific twist order |
| worldbuilding cloning | `world_rule_card` | `bi_state_slot_contract` | proper nouns, house lore furniture |
| scene cloning | `scene_card` | `block_archetype_card` | literal beat-by-beat choreography |
| progression cloning | `block_archetype_card` | `arc_cadence_map` | one-title-only growth ladder |
| style cloning | `voice_card`, short `few_shot_exemplar` | anti-pattern bank | long raw passages and signature prose blocks |

## 6. Minimum Labeling Principles

### 6.1 Label the Function, Not the Surface

Bad:

- `곤륜 회의`
- `재벌가 이사회`
- `파공검제식 결말`

Good:

- `sect_politics_public_humiliation_pressure`
- `succession_vote_with_hidden_financial_trigger`
- `ending_hook_reversal_after_local_victory`

### 6.2 Every Reusable Claim Needs Evidence

Each card must carry:

- `source_title`
- `episode_range`
- `evidence_anchor`
- `evidence_excerpt_summary`
- `why_this_pattern_is_reusable`
- `what_must_not_be_copied`

If the operator cannot point to evidence, the label is provisional and cannot be canonized.

The canonical `evidence_anchor` tuple is:

- `title_id`
- `episode_start`
- `episode_end`
- `scene_id` or `scene_local_id`
- `paragraph_span`
- `anchor_kind` such as `direct_event`, `dialogue_move`, `state_change`, or `callback`

Evidence policy:

- `evidence_excerpt_summary` must be paraphrase-first and short enough to verify the claim without copying raw text.
- Full raw excerpts stay only in the raw-corpus harbor or scratch layer.
- Canonical SSOT artifacts may include only short quoted fragments when absolutely necessary for audit, and the quote must be explicitly marked as a quote.
- A claim with no reproducible anchor tuple is invalid even if the operator "remembers" the scene correctly.

### 6.3 Separate Source Fidelity From Transfer Abstraction

Every artifact must distinguish:

- what the source literally did
- what pattern can be transferred
- what source-specific proper nouns, setting furniture, or signature twists must be excluded

### 6.4 Multi-Scale Is Mandatory

A good decomposition base covers at least four scales:

- work scale
- arc scale
- block scale
- scene scale

If one of these is missing, later `TR/BI` reuse becomes lopsided.

### 6.5 Controlled Namespace Rule

- `genre_family`, `subtype`, `function_label`, `failure_label`, and `slot_name` must come from the active tranche namespace or be proposed as a new namespace entry during consolidation.
- Title-local experiments may introduce a tentative label only inside `candidate` artifacts.
- A tentative label must either be promoted into the namespace, merged into an existing label, or rejected during consolidation.
- No operator may invent a new canonical label directly inside a publication pass.

## 7. Required Directory Strategy

### 7.1 Raw and Scratch Layer

Recommended structure under `manual raw-corpus workspace`:

```text
수동_글도비/
  raw_corpus/
    wuxia/
      <title_slug>/
        manifest.json
        ep001.txt
        ...
    modern_fantasy_business_power/
      <title_slug>/
        manifest.json
        ep001.txt
        ...
  workbench/
    intake/
    extraction/
    rejected/
    diff_checks/
```

Rule:

- raw bytes live here
- temporary extraction notes live here
- nothing here is canonical for future operators unless promoted into SSOT

### 7.2 Canonical Distillation Layer

Recommended structure under `전처리_ssot\docs\20_db_and_materials\`:

```text
materials/
  genre_notes/
    wuxia/
      by_title/
      canonical/
        taxonomy/
        world_rules/
        arc_cadence/
        bi_slots/
        anti_patterns/
    modern_fantasy_business_power/
      by_title/
      canonical/
        taxonomy/
        world_rules/
        arc_cadence/
        bi_slots/
        anti_patterns/
  scene_bank/
    wuxia/
      by_title/
        <title_slug>/
          block_cards/
          scene_cards/
          hook_payoff/
          voice/
      canonical/
        block_cards/
        scene_cards/
        hook_payoff/
        voice/
    modern_fantasy_business_power/
      by_title/
        <title_slug>/
          block_cards/
          scene_cards/
          hook_payoff/
          voice/
      canonical/
        block_cards/
        scene_cards/
        hook_payoff/
        voice/
samples/
  golden/
    wuxia/
      few_shot/
      anti_shot/
      benchmark/
    modern_fantasy_business_power/
      few_shot/
      anti_shot/
      benchmark/
```

Recommended structure under `전처리_ssot\docs\30_ops\`:

```text
30_ops/
  genre_decomposition_base_roadmap.md
  genre_pack_registry.md
  tranche_manifests/
  source_manifest_reviews/
  profile_lock_reviews/
  phase0_ready_reviews/
  handoff_templates/
  audit_checklists/
  dry_run_scorecards/
```

Authority rule:

- `docs/30_ops/*` is review, registry, template, and scorecard space only.
- Canonical per-`work_id` JSON outputs must exist only under `treatments/preprocess/{work_id}/`.
- If a review copy of a work-specific artifact is stored under `docs/30_ops/*`, the filename must end with `__review` or `__template`. It must never be named as if it were the canonical runtime handoff file.

### 7.3 Work-Specific Handoff Layer

No change to the current work-specific contract:

```text
treatments/preprocess/{work_id}/
  source_manifest.json
  profile_lock.json
  material_bundle_summary.json
  phase0_ready_snapshot.json
```

The new decomposition base exists to make these four outputs faster and more defensible.

Additional rule:

- `source_manifest.json`, `profile_lock.json`, `material_bundle_summary.json`, and `phase0_ready_snapshot.json` are authoritative only in this folder.
- Genre-pack outputs may inform them, but may not replace them.

### 7.4 File Naming Contract

Use stable file names so future operators do not fork the naming scheme.

- `corpus_manifest__{genre_family}__{snapshot_date}.json`
- `tranche_manifest__{genre_family}__t{n}__{snapshot_date}.json`
- `title_registry__{genre_family}__{title_slug}.md`
- `world_rule__{genre_family}__{rule_slug}__v{n}.md`
- `arc_cadence__{genre_family}__{title_slug}__ep{start:03d}-{end:03d}.json`
- `block_cards__{genre_family}__{title_slug}__ep{start:03d}-{end:03d}.json`
- `scene_cards__{genre_family}__{title_slug}__ep{start:03d}-{end:03d}.json`
- `hook_payoff__{genre_family}__{title_slug}__ep{start:03d}-{end:03d}.md`
- `voice_card__{genre_family}__{role_slug}__v{n}.md`
- `bi_slots__{genre_family}__v{n}.json`
- `anti_pattern__{genre_family}__{failure_slug}__v{n}.md`
- `anti_pattern_notes__{genre_family}__{title_slug}__ep{start:03d}-{end:03d}.md`
- `few_shot__{genre_family}__{target_asset}__case_{index:03d}__v{n}.md`
- `anti_shot__{genre_family}__case_{index:03d}__v{n}.md`
- `benchmark_case__{genre_family}__case_{index:03d}__v{n}.md`
- `status_matrix__{genre_family}__{title_slug}__ep{start:03d}-{end:03d}.md`
- `handoff_note__{genre_family}__{title_slug}__ep{start:03d}-{end:03d}.md`
- `consolidation_summary__{genre_family}__t{n}__v{n}.md`
- `dedupe_map__{genre_family}__t{n}__v{n}.json`
- `promotion_matrix__{genre_family}__t{n}__v{n}.md`
- `open_disputes__{genre_family}__t{n}__v{n}.md`
- `audit_checklist__{scope_slug}__v{n}.md`
- `findings__{scope_slug}__v{n}.md`
- `pass_fail_decision__{scope_slug}__v{n}.md`
- `required_remediation__{scope_slug}__v{n}.md`
- `status_transition__{scope_slug}__v{n}.md`
- `dry_run_scorecard__{genre_family}__{work_id}__v{n}.json`

If an operator wants a new naming pattern, they must justify it before creating canonical files.

### 7.5 Bundle Granularity and Supersession Rule

- Title-local candidate artifacts live under `by_title/{title_slug}/`.
- Genre-level reusable assets live only under `canonical/`.
- When two cards are merged, the losing card must record `merged_into`; the winning card may record `supersedes`.
- Rejected cards are archived, not deleted.
- If a genre family exceeds `60` candidate scene cards or `20` candidate block cards without a dedupe pass, a consolidation pass is mandatory before new title intake.

## 8. Decomposition Methodology

### 8.1 Stage A: Intake and Candidate Selection

Goal:

- decide which titles are worth canonical decomposition

Required output:

- `tranche_manifest`
- `title_registry_card`

Gate:

- at least one sentence each for `why representative`, `what subtype it covers`, `what it must not overfit`
- explicit `include`, `exclude`, or `defer` decision
- dated corpus snapshot recorded in the tranche manifest

Stop if:

- title is selected only because it is famous
- subtype coverage is unclear
- the work does not actually match the target genre family

Intake classification checklist:

- `wuxia` requires at least `3` of the following: realm ladder, martial lineage/manuals, sect or clan politics, jianghu reputation or grievance economy.
- `modern_fantasy_business_power` requires at least `3` of the following: compounding resource loop, approval or control chain, negotiation leverage, irreversible business or career downside.
- Exclude titles whose primary loop is combat-raid clearance, dungeon progression, or urban vigilantism when building the first `business-power` pack.
- Exclude titles whose primary loop is modern corporate power when building the first `wuxia` pack.
- If a title satisfies both families weakly, mark it `defer` and keep it out of the tranche until a mixed-family rule exists.

Reproducibility rule:

- Every tranche must start from a dated `tranche_manifest`.
- The manifest must record selected titles, reserve titles, excluded titles, source locations, and the reason for each decision.
- If a title becomes unavailable or is replaced, the operator must create a new manifest version instead of silently swapping titles.

### 8.2 Stage B: First-Pass Structural Segmentation

Goal:

- break source episodes into arcs, blocks, and scenes before deep labeling

Required output:

- episode registry
- arc candidate map
- scene boundary sheet
- shard summary sheet

Rule:

- do not label quality too early
- only segment and summarize what happens, in order
- segment in bounded shards before tranche merge

Stop if:

- scene boundaries are invented from memory instead of evidence
- operator starts abstracting before segmentation is stable

Sharding contract:

- One segmentation shard may cover at most `10` episodes or `35` scenes, whichever hits first.
- One functional-labeling shard may cover at most `5` episodes or `20` scenes, whichever hits first.
- Each shard must end with `open boundary issues`, `suspected carryover seeds`, and `follow-up labels to verify`.
- Merge sequence is fixed: `segmentation shard -> tranche boundary reconciliation -> labeling shard -> tranche merge -> consolidation pass -> audit pass`.

### 8.3 Stage C: Second-Pass Functional Labeling

Goal:

- attach functional labels at block and scene scale

Required output:

- `block_archetype_card`
- `scene_card`
- `hook_payoff_ledger`

Rule:

- use function labels
- preserve evidence anchors
- separate "observed" from "interpreted"

Stop if:

- labels contain unique source nouns
- labels are too generic to be reusable
- the same label means different things across titles

### 8.4 Stage D: Third-Pass Distillation

Goal:

- collapse multiple title-specific cards into a genre-level contract

Required output:

- taxonomy draft
- world rule draft
- cadence draft
- BI slot draft
- anti-pattern draft
- dedupe map
- promotion matrix

Rule:

- one-source patterns may exist only as `candidate`
- at least two source works must support a reusable claim before it becomes `provisional`
- no artifact becomes `canonical` during the same pass that first created it
- title-local drafts and genre-level drafts must stay physically separated

Stop if:

- the pack is secretly a disguised clone of one dominant title

### 8.5 Stage E: Few-Shot and Benchmark Packaging

Goal:

- make the distilled contract actually usable by future operators or LLMs

Required output:

- few-shot exemplar bank
- anti-shot bank
- blind benchmark set
- benchmark rubric

Rule:

- short, high-signal exemplars only
- do not dump long raw passages
- use the benchmark set to judge transfer quality after pack publication
- Stage E starts only after Stage D produced a stable `provisional` pack draft
- `few_shot_exemplar` is positive instruction support, not a hidden source dump
- `anti_shot_exemplar` is a negative test case that shows what the operator must reject
- `blind_benchmark_set` must be held out from the titles used to author the final few-shot examples whenever the corpus allows it

## 9. Operator Contract for Opus or Sonnet

This section is written for future delegated execution.

### 9.1 Unit of Work

One agent handles only one of the following at a time:

- one segmentation shard
- one labeling shard
- one title-tranche merge
- one genre-level consolidation pass
- one audit pass on an already-produced tranche

Forbidden:

- one agent decomposes multiple genres in one pass
- one agent both authors and approves the same canonical pack without an independent audit turn
- one audit run that reuses the author's full working context as-is

### 9.2 Mandatory Output Bundle

For a title-tranche merge, the operator must return:

1. `title_registry_card`
2. `episode segmentation note`
3. `scene card set`
4. `block archetype candidates`
5. `hook/payoff ledger`
6. `anti-pattern observations`
7. `open questions`
8. `confidence estimate`
9. `status recommendation`

If any of the nine are missing, the tranche is incomplete.

### 9.3 Mandatory Claim Format

Every reusable claim must be expressed as:

- `claim`
- `evidence`
- `evidence_anchor`
- `transferable core`
- `non-transferable residue`
- `confidence`
- `recommended status`

### 9.4 Mandatory Refusal Conditions

Opus or Sonnet must refuse to canonize a claim when:

- evidence comes from only one ambiguous scene
- the label depends on a named proprietary twist
- the pattern is really prose style, but is being misfiled as structure
- the operator cannot say how the pattern changes `TR` or `BI`
- the claim lacks a reproducible anchor tuple
- the claim would require copying a source-specific signature block to "work"

### 9.5 Mandatory Title-Tranche File Bundle

For each title tranche, the operator must save or hand off the bundle below as one unit.

1. `title_registry__...`
2. `arc_cadence__...`
3. `scene_cards__...`
4. `block_cards__...`
5. `hook_payoff__...`
6. one or more `voice_card__...` files if character voice is materially distinct
7. `anti_pattern_notes__...` or a clearly named equivalent memo
8. `status_matrix__...`
9. `handoff_note__...`

If any item is missing, the tranche cannot be promoted out of scratch.

Interpretation rule:

- `status_matrix__...` carries confidence estimates and status recommendations for the tranche artifacts.
- `handoff_note__...` carries open questions, unresolved boundaries, and follow-up work.

Every title-tranche output is capped at `candidate`. It does not become `provisional` inside the same unit of work.

### 9.6 Mandatory Genre-Consolidation Bundle

For one genre-level consolidation pass, the operator must return:

1. `consolidation_summary__...`
2. `dedupe_map__...`
3. updated `taxonomy` draft
4. updated `world_rule` draft set
5. updated `arc_cadence` draft
6. updated `bi_state_slot_contract` draft
7. `promotion_matrix__...`
8. `open_disputes__...`

Done criteria:

- every promoted claim cites at least `2` distinct titles
- every merged candidate card records `merged_into` or remains explicitly unmerged
- every unresolved disagreement is listed in `open_disputes__...`

### 9.7 Mandatory Audit Bundle

For one audit pass, the reviewer must return:

1. `audit_checklist__...`
2. `findings__...`
3. `pass_fail_decision__...`
4. `required_remediation__...`
5. `status_transition__...`

Done criteria:

- every audited artifact gets an explicit `pass`, `fail`, or `return_for_remediation`
- the reviewer states whether the artifact may stay `candidate`, advance to `provisional`, advance to `canonical`, or be `rejected`
- a failed audit cannot be bypassed with a new confidence number alone

### 9.8 Audit Independence Rule

- The reviewer must be a different operator identity or a fresh delegated run with no authoring context loaded beyond the audit packet.
- The audit packet must include the artifact bundle, the tranche manifest, and the checklist; it must not include hidden reasoning or unpublished scratch notes by default.
- If the same model family performs authorship and audit, the audit must still be a separate run with fresh context and a different reviewer label.
- No artifact may claim `canonical` without an explicit audit artifact produced by that separate review pass.

### 9.9 Confidence Scoring Rule

- Confidence is an integer from `0` to `100`.
- `0-59`: weak or unfit for promotion
- `60-74`: `candidate` only
- `75-89`: may be recommended for `provisional` if support rules are satisfied
- `90-94`: strong but still requires independent audit
- `95-100`: reserved for post-audit or post-dry-run confidence, not author self-certification alone

Every confidence claim must cite:

- supporting title count
- supporting anchor count
- known disagreement count
- reason the score is not `10` points lower

## 10. Genre-First Roadmap

The roadmap is tranche-based, not calendar-based.

### 10.1 Tranche 0: Schema Lock

Objective:

- fix naming, artifact types, and go/no-go gates before any large decomposition effort

Outputs:

- this roadmap
- `genre_pack_registry`
- first-pass naming contract
- first-pass artifact template list
- tranche manifest template
- audit checklist template
- dry-run scorecard template

Definition of done:

- future operator can name every intended artifact without improvising new categories
- future operator can tell title-local `candidate` output from genre-level `canonical` output without guessing

### 10.2 Tranche 1: Wuxia Pilot Corpus

Priority: first

Authority anchor:

- create `tranche_manifest__wuxia__t1__2026-03-20.json` before selecting or replacing any title

Recommended v1 title pool from currently available corpus:

- `무협_곤륜마협`
- `무협_파공검제`
- `무협_자하검신`

Reserve as challenge set, not primary pack driver:

- `무협_검신재림`

Pilot slice:

- first `20` episodes per selected title
- execute as shard pairs of `10 + 10` episodes, not a single undivided pass

Target outputs:

- `3` title registry cards minimum
- `1` wuxia taxonomy draft
- `1` wuxia world-rule draft
- `1` wuxia cadence draft
- `30+` scene cards
- `12+` block archetype cards
- `12+` hook/payoff records
- `1` wuxia BI slot draft

Status rule:

- all title-local outputs remain `candidate`
- any genre-level summary produced here is a `candidate` draft only and cannot be published as `canonical`

Why wuxia first:

- growth axes are explicit
- faction and grievance mechanics are structurally visible
- world-rule extraction is easier than in broader modern-fantasy buckets

### 10.3 Tranche 2: Wuxia Genre Pack v1

Objective:

- publish the first reusable wuxia preprocess pack

Required pack components:

- `taxonomy`
- `world_rules`
- `arc_cadence`
- `block_archetype_bank`
- `scene_bank`
- `hook_payoff_bank`
- `voice_bank`
- `bi_state_slot_contract`
- `anti_pattern_bank`
- `few_shot_bank`
- `blind_benchmark_set`

Definition of done:

- the pack reaches at least `provisional` status through consolidation
- a new wuxia `work_id` can produce defensible `source_manifest` and `profile_lock` without re-reading all raw source works
- an independent audit pass decides whether the pack may become `canonical`

### 10.4 Tranche 3: Modern Fantasy Business-Power Pilot

Priority: second

Scope is intentionally narrow.

Authority anchor:

- create `tranche_manifest__modern_fantasy_business_power__t1__2026-03-20.json` before selecting or replacing any title

This tranche is not "all 현판". It is:

- `현판 business-power`
- `재벌/투자/오피스/산업권력 중심`

Do not include:

- hunter dungeon action
- urban action power fantasy without business-power control structures

Recommended v1 title pool from currently available corpus:

- `재벌물_독식하는 재벌 3세`
- `재벌물_재벌 3세는 총수가 되고 싶다`
- `투자물_금수저생활백서`

Optional reserve set:

- `투자물_회귀 후 몰빵투자로 재벌 되기`

Pilot slice:

- first `20` episodes per selected title
- execute as shard pairs of `10 + 10` episodes, not a single undivided pass

Target outputs:

- `3` title registry cards minimum
- business-power taxonomy draft
- business-power world-rule draft
- `resource/power/control/payoff/failure` axis bank
- `12+` business-power block archetype cards
- `12+` hook/payoff records
- BI slot draft for `business-power`

Status rule:

- all title-local outputs remain `candidate`
- any genre-level summary produced here is a `candidate` draft only and cannot be published as `canonical`

### 10.5 Tranche 4: Modern Fantasy Business-Power Pack v1

Objective:

- publish a reusable pack for `blockguide`-style planning work

Definition of done:

- the pack reaches at least `provisional` status through consolidation
- a new business-power work can lock `profile_lock` and `source_manifest` using the pack without ad hoc category invention
- an independent audit pass decides whether the pack may become `canonical`

### 10.6 Tranche 5: Cross-Genre Benchmark and Handoff Hardening

Objective:

- make the pack system durable enough for routine preprocess use

Required outputs:

- cross-genre confusion test
- benchmark rubric
- handoff checklist from genre pack to `work_id` preprocess
- audit report on where packs still fail to fill `source_manifest` or `profile_lock`
- held-out dry run on a new `work_id` by two independent operators
- dry-run scorecard with reproducibility comparison

Definition of done:

- the operator can explain exactly where genre-pack help ends and work-specific research still begins
- both operators produce materially aligned `source_manifest` and `profile_lock` drafts with no ad hoc label invention

## 11. Wuxia-Specific Start Contract

### 11.1 Wuxia Must Extract

- realm ladder
- internal-energy movement
- martial-art acquisition and refinement
- sect/clan/faction standing shifts
- grievance and revenge chain
- treasure/manual/elixir as conflict source
- public reputation and rumor shifts
- cost-bearing breakthrough pattern

### 11.2 Wuxia Must Not Fake

- "stronger enemy appears" without faction consequence
- generic martial arts without rule or lineage
- breakthrough with no price, no context, and no later burden
- sect politics reduced to disposable shouting scenes

### 11.3 Wuxia BI Slot Minimum

- current_realm
- current_internal_energy
- current_martial_arts
- current_faction_position
- current_jianghu_reputation
- current_enemy_pressure
- unresolved_grievances
- known_treasures_or_manuals
- body_or_meridian_damage

## 12. Modern Fantasy Business-Power Start Contract

### 12.1 Business-Power Must Extract

- what resource actually compounds
- who controls approval, distribution, budget, or access
- what public-facing metric misleads others
- what hidden leverage changes negotiations
- what failure creates irreversible career or ownership damage
- what operational detail gives realism instead of vague "smartness"

### 12.2 Business-Power Must Not Fake

- abstract "politics" without concrete approval chains
- profit, capital, or influence language with no mechanism
- boardroom or office conflict that is emotionally loud but structurally empty
- expertise that works only because other characters become stupid

### 12.3 Business-Power BI Slot Minimum

- current_resource_axis
- current_control_axis
- current_power_axis
- current_reputation_state
- current_hidden_leverage
- active_approval_chain
- current_failure_risk
- live_counterparties
- next_operational_constraint

## 13. Publication Rules

### 13.1 A Genre Pack Is Not Canonical Until

- at least `3` representative titles were decomposed
- at least `2` titles support each canonical reusable rule
- the pack passes `pass1`, `pass2`, `pass3`, and adversarial review
- the pack can be used to draft a mock `source_manifest` and `profile_lock` without raw re-read
- a held-out dry run on a new `work_id` is completed and scored
- the final publication bundle includes the audit artifact and scorecard reference

### 13.2 Candidate vs Canonical

Use these statuses only:

- `candidate`
- `provisional`
- `canonical`
- `rejected`

Never promote `candidate` to `canonical` without an explicit audit turn.

### 13.3 Promotion Matrix

- `candidate`:
  - allowed evidence base: one title or unresolved disagreement
  - allowed location: `by_title/` or tranche draft bundle
  - allowed promotion: to `provisional` only through consolidation
- `provisional`:
  - allowed evidence base: at least two supporting titles and resolved label mapping
  - allowed location: genre-level draft bundle
  - allowed promotion: to `canonical` only through independent audit and publication gate
- `canonical`:
  - allowed evidence base: section 13.1 satisfied
  - allowed location: genre-level canonical bank only
  - allowed promotion: no higher state
- `rejected`:
  - allowed evidence base: failed audit, duplicate, contamination, or non-transferable pattern
  - allowed location: audit or archive record
  - allowed promotion: none without a new authored artifact

### 13.4 Consolidation and Card-Explosion Control

- Title-local cards and canonical genre cards must remain in separate directories.
- Every consolidation pass must produce a `dedupe_map`.
- If two candidate cards are materially the same pattern, one must point to `merged_into` and the survivor may point to `supersedes`.
- No canonical bank may keep near-duplicate cards only because they came from different favorite titles.
- If a family exceeds the thresholds in section 7.5, new intake pauses until consolidation finishes.

## 14. 3-Pass Audit Contract

### Pass 1: Structural Audit

Questions:

- Are paths and artifact boundaries explicit?
- Can a future operator tell raw storage from canonical labels?
- Are units of work small enough for delegated execution?
- Are `TR` and `BI` implications named separately?

Fail if:

- "few-shot" is treated as the whole system
- raw corpus and canonical cards share the same authority level
- genre scope is too broad for a first pack

### Pass 2: Execution Audit

Questions:

- Could Opus or Sonnet execute this without inventing missing concepts?
- Does each tranche have concrete outputs and gates?
- Are evidence anchors mandatory?
- Can the output be checked by another operator from fresh context?

Fail if:

- a tranche has no measurable outputs
- labels are too vague to normalize
- one agent would have to do too much at once
- the audit bundle does not force explicit pass/fail and remediation

### Pass 3: Durability Audit

Questions:

- Will this still work after dozens of titles are added?
- Is overfitting prevented?
- Is work-specific preprocess clearly separated from reusable genre assets?
- Is the path layout discoverable enough that future migration is not required?

Fail if:

- every new title would force a schema rewrite
- the pack becomes a landfill of excerpts instead of a structured registry

## 15. Adversarial Review Contract

This roadmapped system must also survive red-team review.

### 15.1 Mandatory Adversarial Questions

1. Is this secretly a cloning scheme for one favorite title?
2. Are labels leaking copyrighted source furniture instead of reusable structure?
3. Will different operators give the same label to the same scene?
4. Does the BI slot contract actually connect to what TR blocks produce?
5. Is the "현판" scope still too broad?
6. Could a lazy operator skip evidence and still look compliant?
7. Will scene cards explode in count with no consolidation rule?
8. Are anti-patterns strong enough to stop fake expertise and fake density?
9. Can one benchmark set expose overfitting?
10. If raw corpus disappears tomorrow, do the canonical packs still remain usable?

### 15.2 Required Adversarial Mitigations

- multi-title support before canonization
- evidence anchor required on every reusable claim
- functional labels only
- `candidate/provisional/canonical/rejected` status discipline
- separate benchmark set and reserve challenge set
- separate `현판 business-power` and `현판 hunter/urban action`
- mandatory dedupe map and `merged_into` or `supersedes` tracking
- independent audit run with fresh context
- held-out dry run before canonical publication

## 16. Final Start Order

Use this exact start order.

1. Lock schema and naming first.
2. Build wuxia pilot tranche.
3. Publish wuxia pack v1.
4. Build modern-fantasy business-power pilot tranche.
5. Publish business-power pack v1.
6. Run cross-genre benchmark and adversarial review.
7. Only then use the packs as regular preprocess accelerators for new `work_id`.

Do not start by decomposing everything at once.

Do not start with hunter, sports, actor, fantasy, and wuxia all in parallel.

The first victory condition is narrow:

- `무협 v1 pack` works
- `현판 business-power v1 pack` works
- both can help produce better `source_manifest` and `profile_lock`

## 17. Immediate Next Actions

The next operator should do only the following:

1. Create `genre_pack_registry.md`.
2. Create the directory skeleton for `wuxia` and `modern_fantasy_business_power` under `genre_notes/` and `scene_bank/`, including `by_title/` and `canonical/`.
3. Create the first dated `tranche_manifest` for wuxia.
4. Register the first wuxia title pool against that manifest.
5. Decompose the first `20` episodes of one wuxia title only, as `10 + 10` episode shards.
6. Merge the shard outputs into one title-tranche bundle.
7. Run pass1, pass2, pass3, and adversarial review on that single-title tranche before touching title two.

That keeps the system narrow enough to remain correct.

## 18. 3-Pass Record for This Document

### Pass 1 Result

- Fixed the initial false binary between `수동_글도비` and `전처리_ssot`.
- Rewrote the path model into a split-authority contract.
- Added explicit artifact families so "few-shot only" drift cannot happen.
- Locked file format, bundle granularity, stable IDs, and label grammar.

### Pass 2 Result

- Added tranche-by-tranche outputs and gates.
- Added operator contract for Opus/Sonnet.
- Added explicit refusal conditions and mandatory claim format.
- Added separate bundles for title work, consolidation, audit, and dry-run validation.

### Pass 3 Result

- Added durability rules, publication rules, and candidate/provisional/canonical statuses.
- Added separate scope for `현판 business-power` versus `현판 hunter/urban action`.
- Added immediate next actions to prevent over-expansion on day one.
- Added dedupe, supersession, and card-explosion control.

## 19. Adversarial Review Record for This Document

Primary attacks considered:

- overfitting to one source work
- using excerpts as a substitute for structure
- mixing broad modern-fantasy branches too early
- creating too many cards without consolidation
- producing packs that do not actually help `source_manifest` or `profile_lock`

Countermeasures added:

- multi-title canonization rule
- challenge set reservation
- functional label discipline
- direct linkage to `TR` and `BI` slot contracts
- tranche order that forces one-title validation before scale-up
- fresh-context audit independence
- held-out dry-run gate before canonical publication

## 20. Final Conclusion

The correct foundation is:

- raw corpus harbor in `수동_글도비`
- canonical distillation and audit in `전처리_ssot`
- work-specific preprocess outputs in `treatments/preprocess/{work_id}`

The correct first targets are:

- `무협`
- `현판 business-power`

The correct first deliverable is not a giant few-shot bank.

It is a disciplined decomposition system that can later produce:

- better `source_manifest`
- better `profile_lock`
- better `material_bundle_summary`
- better `phase0_ready_snapshot`

without redoing the same manual reasoning from zero every time.
