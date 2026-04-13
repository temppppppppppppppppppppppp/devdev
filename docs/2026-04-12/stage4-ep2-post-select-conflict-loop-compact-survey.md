# Stage4 EP2 Post-Select Conflict Loop Compact Survey

Status: final (3-pass audited on 2026-04-12 against the live workspace and `0_temp.txt`; confidence `96%`)

## Scope

Bounded compact survey for the `Stage4 ep2` retry loop observed in the current live run. This survey does **not** open a new queue topic. It exists to confirm whether the failure belongs under the existing cross-stage contract lane and to pin the smallest safe fail-only patch before the next rerun.

## Evidence Anchors

- runtime console evidence: `0_temp.txt`
- consumer gate / retry lane owner:
  - `modules/core/stage4_retry_runtime.py`
  - `modules/core/stage4_postselect_runtime.py`
- writer retry consumer:
  - `modules/domain/agents/chief_writer.py`
- existing execution lane:
  - `docs/2026-04-02/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md`

## Findings

### 1. This is not a crash; it is a bounded Stage4 ep2 logic loop

- the run ends via user stop, not a Python crash
- before the stop, `ep2` repeats `PASS_WITH_FIX -> post-select conflict -> REJECT`
- the second rejection adds both `continuity` and `history`, then the runtime still reopens a bounded post-select patch lane

Key console anchors:

- `0_temp.txt:451`
- `0_temp.txt:460`
- `0_temp.txt:465`
- `0_temp.txt:583`
- `0_temp.txt:592`
- `0_temp.txt:604`
- `0_temp.txt:675`
- `0_temp.txt:680`

### 2. The dominant failure is shared truth drift, not one bad candidate

- the same family-group drift appears across `A/B/C`
- the same protagonist asset-state drift survives into the selected retry path
- this indicates a shared truth-routing weakness, not a one-off candidate hallucination

Key console anchors:

- `0_temp.txt:557`
- `0_temp.txt:563`
- `0_temp.txt:567`
- `0_temp.txt:593`
- `0_temp.txt:601`
- `0_temp.txt:616`
- `0_temp.txt:623`

### 3. The current bounded retry gate is too permissive for this failure family

- `_should_allow_bounded_post_select_patch_retry(...)` currently accepts bounded local retry mainly from `fix_pack` readiness, local target kind, and a contradiction-type subset
- the contract still lacks typed truth pins for cases like canonical group name and protagonist asset state
- plateau handling exists, but it is too late if the bounded retry lane is reopened first for the same semantic family

Relevant code anchors:

- `modules/core/stage4_retry_runtime.py:142`
- `modules/core/stage4_retry_runtime.py:1134`
- `modules/core/stage4_postselect_runtime.py:14`
- `modules/core/stage4_postselect_runtime.py:436`
- `modules/core/stage4_postselect_runtime.py:460`

## Diagnosis

The first-priority problem is **not** “make inplace smarter” and it is **not** “Chief Writer is too dumb.” The immediate issue is:

1. authoritative truth is not strong enough in the post-select conflict contract
2. bounded local patch retry is allowed for conflict families that should be rewrite-only
3. the writer retry prompt does not receive a strong enough must-preserve truth block for those same facts

## Execution Consequence

This failure should be realized under the existing lane:

- `0_0-stage234-cross-stage-contract-normalization-remediation`

Bounded Stage4 fail-only tranche:

1. enrich post-select conflict contracts with typed truth pins plus a stable conflict fingerprint
2. deny bounded post-select local retry for:
   - `continuity + history` dual-conflict
   - proper-noun / group-name drift
   - protagonist asset or capital-state drift
   - plateau-marked repeats of the same post-select conflict family
3. surface the same truth pins to Chief Writer retry prompts as a must-preserve block

## Out of Scope

- broad Stage4 architecture reduction
- full `inplace` intelligence expansion
- reopening Stage3 or Stage2 work
- DB schema migration

## 3-Pass Audit Record

Pass 1. Scope and ownership

- the failure is bounded to Stage4 ep2 post-select retry behavior
- ownership fits the existing Stage234 cross-stage contract lane because the seam is truth-routing plus retry-contract vocabulary, not a new standalone Stage4 family

Pass 2. Evidence and diagnosis

- console evidence consistently shows the same truth drift across multiple candidates plus repeated downgrade/retry behavior
- code evidence confirms the current retry gate and conflict contract are the narrowest safe patch points

Pass 3. Execution readiness

- the fail-only patch path is clear and does not require a new queue topic
- the operator-facing next step is document promotion inside the existing lane, then a bounded code patch, then focused validation and rerun
