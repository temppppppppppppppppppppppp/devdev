# Opus Genre Decomposition Operator Manual

Date: 2026-03-20
Status: final
Scope: human-facing operating manual for Opus-driven genre decomposition
Authority: canonical under `전처리_ssot/docs/30_ops/handoff_templates`
Confidence Target: 95%
Current Confidence: 95% for first-generation operator use

## 1. Purpose

This manual exists for one reason:

- a human operator should be able to run the first decomposition lane with Opus without reconstructing the workflow from scattered notes

This is the human manual.

Use this before using the runbook.

Primary companion files:

1. `C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\30_ops\genre_decomposition_base_roadmap.md`
2. `C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\30_ops\genre_pack_registry.md`
3. `C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\30_ops\handoff_templates\opus_wuxia_title_tranche_runbook.md`

## 2. What You Are Actually Doing

You are not telling Opus to:

- write a genre pack
- summarize a whole work
- decide canon for the genre

You are telling Opus to do one bounded production unit at a time.

For the first wuxia lane, the bounded sequence is:

1. shard 1 segmentation
2. shard 2 segmentation
3. boundary reconciliation
4. title-tranche merge
5. pass1 audit
6. pass2 audit
7. pass3 audit
8. adversarial audit

Each number above is a separate Opus conversation.

## 3. The One Rule That Prevents Most Failure

Never tell Opus:

- "무협 pack 만들어"
- "곤륜마협 전체 분석해"
- "세 작품 비교해서 구조 뽑아"

Always tell Opus:

- one title
- one scope
- one task type
- one output bundle
- one stop condition

If the ask contains two verbs such as "분해하고 감리해라", it is already too broad.

## 4. Conversation Model

### 4.1 One Job = One Fresh Chat

Open a new Opus chat for each of the following:

1. `ep001-010` segmentation
2. `ep011-020` segmentation
3. boundary reconciliation
4. title-tranche merge
5. `pass1_structural`
6. `pass2_execution`
7. `pass3_durability`
8. `adversarial_red_team`

Do not continue all eight steps in one chat.

Reason:

- context drift
- self-approval theater
- missing file boundaries
- accidental overreach into genre-level claims

### 4.2 Why Fresh Chat Matters

Fresh chat is not cosmetic.

It prevents:

- Opus defending its own earlier mistake
- audit turning into author continuation
- silent carryover of hidden assumptions

## 5. The Operator Menu

Use this table before starting any Opus run.

| If your current state is... | Then run... | Do not run yet... |
| --- | --- | --- |
| no shard output exists | segmentation shard 1 | merge, any audit |
| shard 1 exists but shard 2 does not | segmentation shard 2 | merge, any audit |
| shard 1 and shard 2 both exist | boundary reconciliation | audit |
| reconciliation memo exists | title-tranche merge | audit |
| title-tranche bundle exists | `pass1_structural` | title 2 |
| pass1 passes | `pass2_execution` | title 2 |
| pass2 passes | `pass3_durability` | title 2 |
| pass3 passes | `adversarial_red_team` | title 2 |
| adversarial passes | title 2 may start | genre-level consolidation |

## 6. Current First-Lane Target

Use only this title first:

- `title_id`: `wuxia__title__gonryun_mahyeop`
- title: `곤륜마협`
- shard 1: `ep001-010`
- shard 2: `ep011-020`

Do not touch:

- `파공검제`
- `자하검신`
- `검신재림`

until the first title survives the full audit sequence.

## 7. Files You Must Give Opus

### 7.1 Always Attach or Point Opus To

1. roadmap
2. registry
3. tranche manifest

In file form, those are:

1. `C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\30_ops\genre_decomposition_base_roadmap.md`
2. `C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\30_ops\genre_pack_registry.md`
3. `C:\Users\wjjo\Desktop\글도비\전처리_ssot\docs\30_ops\tranche_manifests\tranche_manifest__wuxia__t1__2026-03-20.json`

### 7.2 What To Attach For Each Step

For segmentation shard:

- the three common files
- the target episode raw files only

For boundary reconciliation:

- the three common files
- both shard outputs

For title-tranche merge:

- the three common files
- both shard outputs
- the reconciliation memo

For audit:

- roadmap
- tranche manifest
- audit checklist
- completed title-tranche bundle
- reconciliation memo

Do not attach all 100 episodes for a 10-episode shard run.

## 8. The Exact Operating Sequence

### Step 1. Run Shard 1

Goal:

- segment `곤륜마협 ep001-010`

Expected outputs:

- episode segmentation note
- scene boundary sheet
- arc candidate map
- shard summary sheet

Stop condition:

- Opus reports files written, unresolved boundary questions, and tranche-merge readiness for this shard only

### Step 2. Run Shard 2

Goal:

- segment `곤륜마협 ep011-020`

Expected outputs:

- episode segmentation note
- scene boundary sheet
- arc candidate map
- shard summary sheet

Important:

- if Opus additionally produced shard-level scene cards, treat them as `candidate shard artifact` only
- do not let that collapse the workflow

### Step 3. Run Boundary Reconciliation

Goal:

- decide whether shard 1 and shard 2 have consistent arc and scene boundaries

Expected output:

- `boundary_reconciliation__wuxia__gonryun_mahyeop__ep001-020.md`

This memo must answer:

1. Does `arc_001` continue into shard 2?
2. Where does `arc_001` close?
3. Where does `arc_002` open?
4. Is `ep013` a hinge episode?
5. Which items remain open carryover seeds?
6. What exact merge directives must be followed next?

Current expected judgment for this title:

- `ep013` is a hinge episode
- `arc_001` closes at `ep013`
- `arc_002` opens at `ep013`
- unresolved seeds remain open, not force-closed

### Step 4. Run Title-Tranche Merge

Goal:

- merge `ep001-010` and `ep011-020` into one `ep001-020` title-local bundle

Expected outputs:

- `title_registry__wuxia__gonryun_mahyeop.md`
- `arc_cadence__wuxia__gonryun_mahyeop__ep001-020.json`
- `scene_cards__wuxia__gonryun_mahyeop__ep001-020.json`
- `block_cards__wuxia__gonryun_mahyeop__ep001-020.json`
- `hook_payoff__wuxia__gonryun_mahyeop__ep001-020.md`
- voice card file(s) if needed
- `anti_pattern_notes__wuxia__gonryun_mahyeop__ep001-020.md`
- `status_matrix__wuxia__gonryun_mahyeop__ep001-020.md`
- `handoff_note__wuxia__gonryun_mahyeop__ep001-020.md`

Status cap:

- every output remains `candidate`

### Step 5. Run Pass 1

Audit type:

- `pass1_structural`

What this checks:

- file naming
- path correctness
- artifact boundaries
- shard-to-tranche consistency
- hinge-episode treatment

### Step 6. Run Pass 2

Audit type:

- `pass2_execution`

What this checks:

- evidence anchors
- output completeness
- whether another operator could reproduce the work

### Step 7. Run Pass 3

Audit type:

- `pass3_durability`

What this checks:

- whether title-local and genre-level boundaries stayed separate
- whether the card set is sustainable
- whether the lane will break when title two is added

### Step 8. Run Adversarial Review

Audit type:

- `adversarial_red_team`

What this checks:

- overfitting to `곤륜마협`
- source-specific noun leakage
- fake reusable labels
- weak `TR` or `BI` linkage

## 9. Decision Rules After Each Step

### 9.1 When You May Continue

Continue to the next step only if:

- required files for the current step were actually written
- the step-specific stop condition was explicitly satisfied
- no hard fail was reported

### 9.2 When You Must Stop

Stop and remediate if:

- Opus skipped one required file
- Opus wrote genre-level claims during title-local work
- Opus promoted status above `candidate`
- Opus failed to cite evidence anchors
- Opus merged unresolved seeds into false closure

### 9.3 When You Must Re-Run The Same Step

Re-run the same step in a new chat if:

- the ask was too broad
- wrong files were attached
- the output path was wrong
- the bundle is incomplete
- the audit says `return_for_remediation`

## 10. Common Failure Modes

### Failure 1. "Opus summarized instead of segmenting"

Cause:

- prompt too broad

Fix:

- rerun only the shard with explicit output list and stop condition

### Failure 2. "Opus started comparing other titles"

Cause:

- prompt implied genre work too early

Fix:

- rerun in fresh chat
- restate `title_id` and `task type`

### Failure 3. "Opus tried to audit and rewrite in one pass"

Cause:

- audit instruction was mixed with authoring instruction

Fix:

- split authoring and audit into separate chats

### Failure 4. "Opus made canonical claims"

Cause:

- the operator forgot the current title-local cap

Fix:

- reject that status call
- keep the bundle at `candidate`

### Failure 5. "Opus over-closed open seeds"

Cause:

- pressure to make the arc summary look neat

Fix:

- restore them as carryover seeds in reconciliation or audit

## 11. Minimal Human Checklist

Before sending any Opus job, check:

- is this exactly one task type
- is this exactly one title
- is this exactly one scope
- did I open a fresh chat
- did I attach only the files needed for this step
- did I name the output bundle explicitly
- did I state the stop condition

If any answer is `no`, do not send yet.

## 12. What To Use In Practice

If you want exact copy-paste prompts:

- use `opus_wuxia_title_tranche_runbook.md`

If you want to know what step comes next and why:

- use this manual

Short version:

- manual = operator explanation
- runbook = execution script

## 13. 3-Pass Record

### Pass 1 Result

- Converted the scattered run instructions into one human-facing workflow.
- Fixed the sequence so reconciliation is explicit instead of implied.

### Pass 2 Result

- Added step-by-step decision rules, failure handling, and attachment boundaries.
- Added a menu table so the operator can tell what to run next.

### Pass 3 Result

- Added hard stop conditions and common failure patterns.
- Kept the manual scoped to the first lane instead of promising a generic universal manual too early.

## 14. Adversarial Review Record

Primary failure modes considered:

- operator sends one giant prompt
- operator keeps using one chat all the way through
- operator forgets when audit begins
- operator cannot tell whether to continue or rerun

Mitigations added:

- one-job-one-chat rule
- exact step menu
- continue or stop decision rules
- explicit separation between manual and runbook
