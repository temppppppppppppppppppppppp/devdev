# Stage4-Only Canary Blueprint Baseline Integrity Audit

Date: 2026-04-02
Type: evidence sanitization audit
Scope: Stage4-only canary blueprint baseline contamination verification
Evidence: `docs/2026-04-02/0_0-stage4-only-canary-blueprint-baseline-integrity-evidence.json`

## Answer First

**Blueprint baseline: CONTAMINATED.**
V75-B full blueprint regeneration fired during the sole completed Stage4-only canary (`canary_0_0_stage4_ep2_tier25`), irreversibly overwriting the ep2 Stage 3 blueprint in the DB. No hash pinning, no versioning, no rollback mechanism exists. The remaining two requested canaries (ep3, ep4) were never run.

**Stage4-only canary interpretation rule: `not authoritative`.**
Conclusions from this canary cannot be attributed to the original Stage 3 baseline.

**Next canary recommendation: `Stage4-only + blueprint hash pin` (minimum).**
A `Stage34 full` canary is the safer option if hash pinning is not implemented first.

---

## 1. Canary Project Inventory

| Requested | Exists | Terminal State |
|-----------|--------|---------------|
| canary_0_0_stage4_ep2_tier25 | YES | HUMAN_REVIEW (R10, no manuscript produced) |
| canary_0_0_stage4_ep3_tier25 | NO | not-run |
| canary_0_0_stage4_ep4_tier25 | NO | not-run |

Reference Stage34 canaries inspected for comparison:
- `canary_0_0_stage34_arc2_fixpack_r1` — stage4_complete, V75-D only (no V75-B)
- `canary_0_0_stage34_arc2_tier25_r2` — prepared, not executed

---

## 2. Artifact Truth

### 2.1 Blueprint Data Length: Source (0_0) vs Canary

| ep | source | canary | match |
|----|--------|--------|-------|
| 1 | 5,021 | 5,021 | YES |
| **2** | **5,481** | **5,263** | **NO (delta -218)** |
| 3 | 6,202 | 6,202 | YES |
| 4 | 5,633 | 5,633 | YES |
| 5 | 7,105 | 7,105 | YES |
| 6 | 5,151 | 5,151 | YES |
| 7 | 6,371 | 6,371 | YES |
| 8 | 5,912 | 5,912 | YES |
| 9 | 5,925 | 5,925 | YES |

Eps 1, 3-9: **frozen baseline confirmed** (byte-identical to source).
Ep 2: **baseline contamination detected** — 218 chars shorter, 2 keys missing (`_inventory_gaps`, `_stage3_meta`).

### 2.2 Three-Way Blueprint Comparison (ep2)

| State | Keys | Source |
|-------|------|--------|
| Source (0_0 DB) | 20 | Original Stage 3 output |
| V75-D patch artifact (R3) | 20 | Inplace fix of 3 fields, all keys preserved |
| Canary DB (post-V75-B) | 18 | Full regen, missing 2 metadata keys, different content |

The current canary DB ep2 row is the V75-B full regen output, not the original Stage 3 baseline.

### 2.3 Verdict

```
ep1:     frozen baseline confirmed
ep2:     baseline contamination detected
ep3-9:   frozen baseline confirmed (untouched by Stage 4 run — only ep2 was target)
```

---

## 3. Metadata Truth

### 3.1 Stage Attempts Sink

`stage_attempts` table contains **zero Stage 4 rows** despite 10 rounds running for ep2. This is a complete sink failure — Stage 4 lifecycle events exist only in `director_selections` and `episode_production.jsonl`.

### 3.2 Director Selections (ep2, stage=4)

10 rounds recorded. Key events:

| Round | Verdict | Score | Firewall | V75 Event |
|-------|---------|-------|----------|-----------|
| R0 | REJECT | 96 | 0 | — |
| R1 | REJECT | 44 | 1 (Contradiction) | — |
| R2 | REJECT | 96 | 0 | — |
| R3 | PASS | 96 | 0 | V75-D after this round |
| R4 | REJECT | 94 | 0 | — |
| R5 | REJECT | 96 | 0 | — |
| R6 | REJECT | 92 | 0 | — |
| R7 | REJECT | 98 | 0 | — |
| R8 | PASS | 98 | 0 | — |
| R9 | REJECT | 44 | 1 (Contradiction) | V75-B after this round |

R3 and R8 showed PASS in director_selections but were overridden by post_select_conflict gates.

### 3.3 V75 Events

1. **V75-D (R3, 08:46:19)**: Inplace blueprint patch. Contradiction type: `history`. **Not saved to DB.** Artifact at `logs/artifacts/stage4/ep_0002/attempt_04/`.
2. **V75-B (R9, 09:23:46)**: Full blueprint regeneration. Contradiction type: `수치` (numeric). **Saved to DB via `INSERT OR REPLACE`.** Trigger: `logic_error_streak >= 2`.

### 3.4 Verdict

V75-B at R9 is the contamination event. The `blueprints` table row for ep2 was overwritten. No backup was taken. The original Stage 3 blueprint for ep2 is irrecoverable from the canary DB.

---

## 4. Narrative Truth

### 4.1 Was the Blueprint Truly Frozen?

**No.** Two intervention paths engaged:

- V75-D (R3): In-memory patch, not persisted — subsequent rounds still read the patched version from `round_ctx.blueprint`. Moderate: changes runtime behavior but does not corrupt DB baseline.
- V75-B (R9): Full regeneration, **persisted to DB**. The original Stage 3 blueprint is gone from the canary.

### 4.2 Recurring Contradictions

The root cause of escalation was a numeric inconsistency:
- Ep1 established: trust fund principal = **20억 원**
- Ep2 blueprint stated: **25억 원** (with 20% penalty = 5억 원, net = 20억 원)
- This persisted across all 10 rounds and triggered both V75-D and V75-B.

NPC drift (한정호 relation_to_protag) was a secondary persistent issue across rounds 0-7.

### 4.3 Was the Blueprint Stale or Source-Baseline?

At prepare time, the ep2 blueprint was copied from source project 0_0 (byte-identical, confirmed by eps 1/3-9 match). The blueprint was a valid Stage 3 artifact — not stale, not fabricated. Contamination occurred during run, not during prepare.

### 4.4 Verdict

```
frozen baseline confirmed:   prepare → R2 (blueprint unchanged)
frozen baseline ambiguous:    R3 → R8 (V75-D in-memory patch active, DB untouched)
baseline contamination detected: R9 onward (V75-B overwrote DB)
```

---

## 5. Code Path Analysis

### 5.1 Safe Paths (No DB Blueprint Writes)

| File | Access Pattern | Risk |
|------|---------------|------|
| stage4_interview_round.py | deepcopy normalization, read-only | SAFE |
| stage4_retry_runtime.py | ephemeral `_inplace_patch_blueprint` attr, cleared in finally | SAFE |
| stage4_reject_runtime.py | read-only context | SAFE |
| stage4_post_pass_runtime.py | validation-only (`_validate_blueprint_completeness_v60`) | SAFE |

### 5.2 Contamination Paths

| Path | Mechanism | DB Write | Risk |
|------|-----------|----------|------|
| V75-D `_attempt_v75d_inplace_blueprint_patch()` | `dataclasses.replace(round_ctx, blueprint=patched_bp)` | NO | MODERATE |
| **V75-B `_regenerate_blueprint()`** | **`save_episode_blueprint()` → `INSERT OR REPLACE INTO blueprints`** | **YES** | **HIGH** |

### 5.3 Missing Safeguards

- No blueprint hash computed at prepare time
- No hash validation at run completion
- No immutability flag or read-only lock
- No versioning or rollback mechanism
- No audit trail column for blueprint mutations
- `canary_summary.json` reports `blueprint_db_count` but not content hash

---

## 6. Per-Episode Verdicts

### ep2 (canary_0_0_stage4_ep2_tier25)

| Dimension | Verdict |
|-----------|---------|
| Artifact truth | **contamination detected** — ep2 DB row differs from source (5263 vs 5481, 18 vs 20 keys) |
| Metadata truth | **contamination detected** — V75-B saved at R9, stage_attempts sink gap |
| Narrative truth | **contamination detected** — original irrecoverably overwritten |
| **Overall** | **baseline contamination detected** |

### ep3 (canary_0_0_stage4_ep3_tier25)

Not-run. No evidence. No verdict possible.

### ep4 (canary_0_0_stage4_ep4_tier25)

Not-run. No evidence. No verdict possible.

---

## 7. Stage4-Only Canary Conclusions: Trust Boundary

### What Is Valid (frozen baseline)

- Ep 1, 3-9 blueprint integrity: confirmed frozen
- Stage4 escalation machinery behavior (V75-D, V75-B triggers, advisory chain, firewall gates): valid observation of runtime mechanics
- Sink alignment issues (stage_attempts gap, key mismatches): valid infrastructure finding
- NPC drift detection pattern: valid advisory behavior observation

### What Requires Conservative Reading (contamination risk)

- **Any ep2-specific Stage4 quality conclusion after R3**: the blueprint changed in-memory (V75-D), so manuscript quality reflects a patched baseline, not the original
- **Any ep2-specific Stage4 quality conclusion after R9**: the blueprint was fully regenerated (V75-B), so all subsequent attempts used a different blueprint entirely
- **Canary pass/fail rate for ep2**: not comparable to a frozen-baseline canary
- **The HUMAN_REVIEW terminal state**: may reflect V75-B blueprint quality as much as Stage4 machinery quality

### What Is Not Authoritative

- "Stage4-only canary proves Stage4 seam quality for ep2" — **invalid**, because the blueprint input changed mid-run
- "Blueprint baseline was frozen throughout" — **disproved**

---

## 8. Interpretation Rule

**`not authoritative`**

The sole completed Stage4-only canary has confirmed V75-B contamination. The blueprint input was not frozen. Stage4 conclusions from this canary cannot be cleanly separated from blueprint baseline effects.

This does not mean the canary was useless — the runtime mechanics observations (escalation paths, sink gaps, advisory chains) are valid. But the canary cannot serve as proof of Stage4 seam quality against a known-good baseline.

---

## 9. Next Canary Recommendation

| Option | Verdict |
|--------|---------|
| Stage4-only continue (as-is) | **NOT RECOMMENDED** — V75-B can fire on any episode, no hash pin exists |
| **Stage4-only + blueprint hash pin** | **MINIMUM** — hash at prepare, validate at completion, abort or flag if mismatch |
| Stage34 full only | **SAFEST** — Stage3 produces blueprints within the canary, no frozen-baseline assumption needed |

**Recommended: `Stage4-only + blueprint hash pin`** if the goal is to isolate Stage4 seam behavior. Implementation requires:
1. Compute SHA-256 of each blueprint row at prepare time, store in `canary_prep.json`
2. At canary completion, recompute hashes and compare
3. If mismatch detected: flag the episode as `baseline_contaminated` in canary_summary
4. Optionally: disable V75-B during canary runs (read-only blueprint mode)

If blueprint hash pinning is not implemented before the next canary, use **`Stage34 full`** to avoid the contamination ambiguity entirely.

---

## 10. Hard Gate / Sink Gap Summary

The ep2_tier25 canary also exposed infrastructure issues independent of blueprint contamination:

- `stage_attempts` has zero Stage 4 rows (complete sink failure)
- `draft_count_mismatch` (ep1 only, ep2 never finalized)
- `artifact_metadata_missing` (10 ep2 attempts missing `artifact_path`)
- `gate_basis_mismatches` (R3, R8: `director_primary_pass` vs `post_select_conflict`)
- `repair_scope_mismatches` (R3, R8: `inplace` vs `full`)

These are valid findings regardless of blueprint contamination status.

---

Baseline Commit: c5c5180b
Audit Confidence: 97%
3-Pass Status: complete
