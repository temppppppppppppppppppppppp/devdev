# OPUS Pantech Active Promotion Order

Date: 2026-03-27
Track: narrative pipeline
Status: active
Scope: single-work OPUS order for `pantech_cyworld_reborn`

## 1. Order Intent

This order fixes the target to `pantech_cyworld_reborn` and asks OPUS to advance exactly one remaining revival-ladder unit.

Current lane truth:
- family: `blockguide`
- entry type: existing `TR + BI` pair revival
- current pair location: `_quarantine`
- smallest remaining unproven step: `active promotion` (ladder Step 7)

This is not a fresh Planning or fresh TR/BI generation order.

## 2. Non-Negotiable Rules

- UTF-8 only
- read router → family SSOT → revival ladder before doing anything else
- one work, one owner, one unit
- no same-work concurrent editing
- no code or system edits
- do not regenerate TR
- do not redesign BI
- do not modify narrative content — this is a promotion-only unit
- do not run Stage 4 canary in the same run
- preserve quarantine originals for provenance (copy, not move)
- confirm byte-identical promotion

## 3. Canonical Target

- work_id: `pantech_cyworld_reborn`
- TR source: `treatments/_quarantine/07_pantech_cyworld_reborn_tr_block_070_draft.json`
- BI source: `bible/_quarantine/07_pantech_cyworld_reborn_bi.json`

Treat these quarantine files as the authoritative pair for this order.

## 4. Proven Prior Steps

The following steps are already evidenced and should not be re-litigated unless the live files contradict them.

1. Pair consumability survey:
   - `docs/2026-03-26/pantech-cyworld-bi-tr-consumability-survey.md`
2. Pair consumability repair:
   - `docs/2026-03-26/pantech-cyworld-bi-tr-consumability-repair-report.md`
3. TR static audit:
   - `docs/2026-03-27/pantech-cyworld-tr-static-quality-audit.md`
   - verdict: `usable spine but mixed`
4. BI repair:
   - `docs/2026-03-27/pantech-cyworld-bi-repair-note.md`
   - verdict: `pass`
5. Revival canary:
   - `docs/2026-03-27/pantech-cyworld-revival-canary-report.md`
   - verdict: `pass`
6. Revival-stage probe:
   - `docs/2026-03-27/pantech-cyworld-revival-stage-probe-report.md`
   - verdict: `pass`

Interpretation:
- ladder Steps 1-6 are all proven with pass verdicts
- the pair is qualified for active promotion
- no promotion patch was needed (probe passed without trivial blockers)

## 5. Preprocess Gate Truth

The work already has Stage 0 artifacts and locked manual audit.

Required truth:
- `treatments/preprocess/pantech_cyworld_reborn/source_manifest.json`
- `treatments/preprocess/pantech_cyworld_reborn/profile_lock.json`
- `treatments/preprocess/pantech_cyworld_reborn/material_bundle_summary.json`
- `treatments/preprocess/pantech_cyworld_reborn/phase0_ready_snapshot.json`

Expected gate:
- `manual_audit_pass == true`

Do not spend this run rebuilding preprocess artifacts unless the live files contradict the saved gate.

## 6. Mandatory Reads

Read these in order:

1. `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
2. `docs/blockguide/SSOT_blockguide-integrated-order.md`
3. `docs/narrative-router/material-revival-ladder-harness.md`
4. `docs/2026-03-27/pantech-cyworld-revival-stage-probe-report.md`

## 7. Immediate Goal

Execute exactly one bounded `active promotion` (ladder Step 7) for `pantech_cyworld_reborn`.

The promotion must:
- copy the quarantine pair to the active candidate path
- verify byte-identical promotion
- run post-promotion consumability check at the active path
- save a promotion note

## 8. Promotion Method

### 8.1 Destination Active Paths

Follow the shared output path contract in `docs/narrative-router/SSOT_narrative-router-integrated-order.md` Section 6:

- BI destination: `bible/0_bi_pantech_cyworld_reborn.json`
- TR destination: `treatments/pantech_cyworld_reborn_tr_block_070_draft.json`

### 8.2 Copy, Not Move

Copy both files from quarantine to active paths. Do not delete the quarantine originals — they are provenance evidence.

### 8.3 Byte-Identical Verification

After copy, compute SHA-256 (or equivalent hash) for both source and destination. Confirm the hashes match exactly.

### 8.4 Post-Promotion Consumability

After promotion, verify at the active paths:
- pair loads without contract failure
- BI standalone roadmap readiness passes
- TR consumability passes
- no bible_errors or treatment_errors
- no missing runtime protagonist keys
- no embedded roadmap warnings

### 8.5 Post-Promotion Content Confirmation

Confirm no narrative content changed during promotion. The promoted pair must be the exact same pair proven in Steps 1-6.

## 9. Deliverable

Save exactly one main note:

- `docs/2026-03-27/pantech-cyworld-promotion-note.md`

The note should include:
- source quarantine paths
- destination active paths
- promotion method (copy, not move)
- SHA-256 verification result
- post-promotion consumability result
- content confirmation
- prior proven steps reference

Use the same format as `docs/2026-03-27/chaebol-ent-empire-promotion-note.md` for consistency.

## 10. Stop Conditions

Stop immediately and report if any of the following occurs:

- quarantine source files are missing or corrupted
- quarantine files differ from what was proven in Steps 1-6
- copy fails or produces non-identical files
- post-promotion consumability fails at active paths
- active path already contains a different version of this work_id
- confidence falls below 95%

If a trivial blocker appears (e.g., missing field that the active path requires), do not run a full promotion patch in the same run. Record the blocker and stop with `promotion patch` as next-unit recommendation.

## 11. Expected Next Unit After This Order

- if promotion passes: `bounded Stage 4 canary`
- if promotion fails due to trivial contract blocker: `promotion patch`
- if quarantine file integrity fails: `re-probe` or `re-repair`, then stop

## 12. Handoff Format

End with this exact flat report:

```text
work_id: pantech_cyworld_reborn
current_stage: audit_or_repair
finished_unit: active promotion
changed_files: ...
next_unit: ...
stop_reason: ...
```

## 13. 3-Pass Self Audit

### Pass 1. Contract Alignment

- target is fixed to one `work_id`
- order stays inside router + blockguide + revival-ladder boundaries
- no same-work parallel editing is authorized
- no narrative content modification permitted
- this is a copy-only promotion unit

### Pass 2. Operational Usefulness

- the next unit is singular and concrete: `active promotion`
- all prior proven steps (1-6) are enumerated so OPUS does not restart the ladder
- deliverable and stop conditions are explicit
- chaebol_ent_empire promotion note provides proven format reference

### Pass 3. Integrity

- saved under dated `docs/2026-03-27/`
- UTF-8 only
- no code-edit instructions
- no multi-unit overreach beyond one bounded revival step
- quarantine provenance preserved by copy-not-move

Confidence:
- 97% that `active promotion` is the correct next OPUS unit for this pair
