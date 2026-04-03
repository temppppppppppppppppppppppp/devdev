# 0_0 Stage4 Numeric Asset Authority Carryover Bounded Survey

Date: 2026-04-03
Status: final
Canonical Path: `docs/2026-04-03/0_0-stage4-numeric-asset-authority-carryover-bounded-survey.md`
Source Docs:
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-03/0_0-stage34-ep2-fresh-run-post-run-merge-audit.md`
- `docs/2026-04-03/0_0-stage4-ep2-sinkproof-r2-runtime-closure-audit.md`
- `docs/이전/2026-03-24/opus-live-run-residual/t6-stage4-carryover-consumption.md`
- `docs/이전/2026-03-24/opus-live-run-residual/t9-artifact-truth-diff-ledger.md`
Evidence Artifacts:
- `docs/2026-04-03/0_0-stage4-numeric-asset-authority-carryover-bounded-survey-evidence.json`
- `projects/00_20260403/plans/arcs/arc_001.txt`
- `projects/00_20260403/plans/blueprints/blueprint_0002.txt`
- `projects/00_20260403/drafts/ep_0002.txt`
- `projects/canary_0_0_stage4_ep2_sinkproof_r2/project_data.db`
Confidence: `96%`

## 1. Answer First

The next bounded Stage4 question is no longer `flashback/replay` first.

- the `1천만원 / 20억 / 200억` split is real across artifacts and DB truth
- the `r2` Stage4-only canary is not malformed for this question; it correctly replays the `ep1 -> ep2` carryover boundary
- the active seam is now `numeric asset authority / carryover owner-boundary`, not `NpcDrift` and not the old replay-first interpretation

This does not prove Stage4 is the sole owner. It proves the live reject now manifests through Stage4 while the upstream numeric authority surfaces are already split before the final manuscript is generated.

## 2. Scope

Included:

- `projects/00_20260403` full-run artifacts for `arc_001`, `blueprint_0002`, and final `ep_0002`
- `projects/canary_0_0_stage4_ep2_sinkproof_r2` runtime evidence and sqlite truth
- archived Stage4 carryover / artifact-truth surveys from 2026-03-24 as historical substrate

Excluded:

- new code patching
- Stage2/3 global reopen
- fresh canary
- global Stage4 closure declaration

## 3. Inventory

### 3.1 Artifact truth is already split before the final Stage4 pass

`arc_001.txt` encodes a protagonist cash/asset band around `20억`.

- asset liquidation completes at `20억 3천만 원`
- personal account is described as `20억`
- later CME funding is described as `19억 7천만원`

But `blueprint_0002.txt` and the final `ep_0002.txt` both present the protagonist's starting business capital as `200억`.

This means the numeric authority chain is already inconsistent across the artifact ladder:

- arc layer: about `20억`
- ep2 blueprint layer: `200억`
- ep2 final manuscript layer: `200억`

### 3.2 The Stage4-only canary exposes a separate ep1 carryover truth

The `r2` canary DB still carries `ep1` FactLedger truth:

- `capital = 0.0 won`
- `total_assets = 10000000.0 won`
- canonical summary renders this as `EP1 기준`

So the canary is not inventing a contradiction out of nowhere. It is exposing that the resumed `ep1` carryover truth and the `ep2` blueprint/manuscript asset claim are on different numeric authority surfaces.

### 3.3 The failed Stage4 round is typed as numeric, not replay

The `r2` canary's first failed Stage4 attempt is not a pure replay seam.

- `gate_basis = continuity_firewall`
- `contradiction_type = 수치`
- the candidate/selection reasoning explicitly centers on the protagonist's `200억` asset formation story

Some wrapper text still mentions replay-style phrasing, but the typed contradiction and the selection reasoning both point to a numeric authority collision.

## 4. Merged Findings

### 4.1 The current live seam is mixed, but numeric-first

The strongest merged reading is:

- Stage4 is where the reject manifests
- but the contradiction is enabled by pre-existing split authority across arc, blueprint, and carryover truth

So the correct label is not:

- `flashback residual`

and not:

- `Stage4-only bug`

It is:

- `numeric asset authority / carryover owner-boundary seam`

### 4.2 The Stage4-only canary design is valid, but must not be over-attributed

For this question, the canary unit is correct because it intentionally tests:

- frozen prior-episode truth
- preserved blueprint authority
- live Stage4 consumption

That makes it a valid probe of the carryover boundary.

But it is not valid to read the canary as proof that Stage4 alone created the `1천만원 / 20억 / 200억` split. The split already exists across upstream artifacts and persisted carryover truth.

### 4.3 The archived T6/T9 findings are consistent with the current run

The older 2026-03-24 carryover/artifact surveys already documented the same class of problem:

- stale or mismatched numeric state can appear in blueprint/manuscript authority
- Stage4 carryover packets can lose to stale blueprint numeric statements

The current `ep2` evidence does not contradict those archived findings. It reproduces the same family in a newer, narrower form.

## 5. Execution Consequence

Keep:

- `0_0-stage4-consumer-contract-normalization-remediation` as the active umbrella lane

Demote:

- `0_0-stage4-flashback-continuity-localfix-remediation` from front-of-queue interpretation
- `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation` from immediate blocker status

Promote:

- the next bounded child seam to `numeric asset authority / carryover owner-boundary investigation`

Primary code-owner surfaces for that next lane are likely:

- `modules/core/stage4_context_builder.py`
- `modules/domain/agents/chief_writer_context_packets.py`
- `modules/domain/agents/director_ensemble.py`
- `modules/core/fact_ledger.py`
- `modules/core/numeric_consistency_checker.py`

Do not do next:

- do not reopen broad Stage2/3 realization yet
- do not treat the Stage4-only canary as malformed
- do not keep using `flashback/replay` as the primary explanation for the latest live reject

## 6. 3-Pass Audit Record

Pass 1, structure and scope:

- bounded the question to the latest `ep2` numeric contradiction evidence
- kept the result at owner-boundary classification rather than premature code realization

Pass 2, evidence and consistency:

- triangulated full-run artifacts, canary DB truth, and archived carryover surveys
- verified the latest failed Stage4 attempt is typed as `수치`

Pass 3, execution and readability:

- separated `canary validity` from `owner attribution`
- kept the execution consequence narrow: demote flashback, promote numeric carryover
