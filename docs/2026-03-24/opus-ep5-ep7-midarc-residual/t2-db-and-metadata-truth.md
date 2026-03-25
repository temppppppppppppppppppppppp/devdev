# T2: DB / Metadata Truth — EP5-EP7 Mid-Arc Residual Survey

Date: 2026-03-24
Status: final (3-pass audited)
Lane: T2 — DB / Metadata Truth
Scope: `project_data.db`, `quality_metrics.jsonl`, `state_changes.jsonl`, `episode_production.jsonl`, `runtime_audit.jsonl`, artifact path linkage
Master Order: `docs/2026-03-24/ep5-ep7-midarc-residual-6terminal-master-order.md`

---

## 1. Executive Summary

DB and JSONL sinks are **structurally consistent** for EP5-7. No missing episodes, no orphaned attempts, no phantom DB rows. The content-hash chain from `director_selections` through `stage_attempts` to physical artifact files is intact for every PASS verdict.

However, four recording-level concerns exist:

1. **Stage 3 non-winning attempts are silently discarded** (DB + artifacts)
2. **Artifact path dual-naming creates apparent sink mismatch** (by design, but confusing)
3. **PASS_WITH_FIX → patch path is invisible to runtime_audit pathology tracking**
4. **Blueprint coverage 60% accepted as PASS for EP6 and EP7**

None of these explain a real rescue round by themselves. The rescue rounds originate in **Stage 4 content generation**, not in DB/metadata integrity.

---

## 2. Lane Questions — Answered

### Q1. Do DB and JSONL agree on selected candidate, verdict chain, and artifact path?

**Yes, with nuance.**

Verdict chains match across sinks:

| EP | Stage 3 | Stage 4 a1 | Stage 4 a2 | Stage 4 a3 | Final |
|---|---|---|---|---|---|
| 5 | PASS (95) | REJECT (93, post_select_conflict) | REJECT (93, post_select_conflict) | PASS (95) | PASS |
| 6 | PASS (95) | REJECT (78, director_primary_reject) | REJECT (44, continuity_firewall) | PASS (98) | PASS |
| 7 | PASS (95) | PASS (90, patch_reaudit_pass) | — | — | PASS |

These chains are confirmed identical in:
- `stage_attempts` table (DB)
- `director_selections` table (DB)
- `quality_metrics.jsonl` validation rows
- `episode_production.jsonl` pathology rows
- `cost_log` rejection events

**Content-hash integrity for all PASS verdicts:**

| EP | Stage | stage_attempts hash | director_sel hash | Match? |
|---|---|---|---|---|
| 5 | 3 | `b1838d9a...` | `b1838d9a...` | YES |
| 5 | 4 | `e00050bd...` | `e00050bd...` | YES |
| 6 | 3 | `8fbbe6ef...` | `8fbbe6ef...` | YES |
| 6 | 4 | `c7a34baa...` | `c7a34baa...` | YES |
| 7 | 3 | `8c9dc95e...` | `8c9dc95e...` | YES |
| 7 | 4 | `70688882...` | `cbf852bd...` (pre-patch) | Expected: patch changed content |

EP7 Stage 4 hash differs because `director_selections` records the pre-patch candidate (B, hash `cbf852bd...`) while `stage_attempts` records the post-patch result (A_InPlace, hash `70688882...`). This is correct behavior — the patch genuinely changed the content.

### Q2. Are any episode attempts missing from DB while present in console or artifacts?

**Partially yes — Stage 3 non-winning attempts are not persisted.**

EP6 Stage 3 `attempt_num=3` is recorded in DB, but attempts 1-2 have:
- No rows in `stage_attempts`
- No rows in `director_selections`
- No artifact directories (`stage3/ep_0006/` only contains `attempt_03/`)

EP5 and EP7 Stage 3 both passed on attempt 1, so no loss there. But EP6 Stage 3 needed 3 attempts — the first two are completely gone from all sinks.

| Sink | EP6 S3 a1 | EP6 S3 a2 | EP6 S3 a3 |
|---|---|---|---|
| stage_attempts | MISSING | MISSING | Present |
| director_selections | MISSING | MISSING | Present |
| artifacts/ | MISSING | MISSING | Present |
| quality_metrics.jsonl | MISSING | MISSING | Present (L34) |

**Classification: `confirmed secondary amplifier`** — the missing rows don't cause rescue rounds, but they prevent retrospective analysis of *why* EP6 Stage 3 failed twice before succeeding. If the blueprint oscillated across those attempts, that information is lost.

### Q3. Is there any metadata-to-artifact linkage break?

**No true linkage break. Dual-write naming is cosmetic.**

Every Stage 4 attempt directory contains exactly 2 files with identical content (same byte size):

| Stage | Pattern | director_selections path | stage_attempts path |
|---|---|---|---|
| Selected then REJECT | `selected_before_fix__*.txt` | `rejected_best__*.txt` |
| Selected then PASS (patched) | `selected_candidate__*.txt` | `patched_after_fix__*.txt` |
| Selected then PASS (no patch) | `selected_candidate__*.txt` | `final_manuscript__*.txt` |

Example for EP5 attempt_01:
- `selected_before_fix__B.txt` (13,051 bytes, written 18:34)
- `rejected_best__B_balanced.txt` (13,051 bytes, written 18:37)

Both files exist, same size. The director writes the first copy at selection time; the verdict pipeline writes the second copy at resolution time with a verdict-appropriate name. This is **by design** but creates surface-level confusion when cross-referencing sinks.

**Classification: `artifact-truth mismatch` (cosmetic only, content intact)**

---

## 3. Additional Findings

### F-1. Verdict Override Transparency (EP5)

EP5 Stage 4 attempts 1-2 show a **Director→System override**:

| Attempt | Director Verdict | System Final | Gate Basis | Score |
|---|---|---|---|---|
| a1 | PASS_WITH_FIX | REJECT | post_select_conflict | 93 |
| a2 | PASS_WITH_FIX | REJECT | post_select_conflict | 93 |
| a3 | PASS | PASS | director_primary_pass | 95 |

- `director_selections.verdict = PASS_WITH_FIX`
- `stage_attempts.verdict = REJECT`
- `stage_attempts.advisory_flags.gate_semantics.gate_basis = post_select_conflict`

The post-selection conflict validator **overrode the Director's provisional pass twice** due to capital/leverage arithmetic contradictions. This is well-recorded: `advisory_flags.gate_semantics` captures both the Director's verdict and the system's final verdict with the override reason.

Root cause: Stage 4 generated manuscripts with leverage calculation errors (레버리지 산술 불일치) that the Director scored 93 but the arithmetic validator caught.

**Classification: `confirmed primary cause` — Stage 4 content generation, not DB**

### F-2. Continuity Firewall Escalation (EP6)

EP6 Stage 4 attempt 2 shows a **firewall escalation**:

- Director pre-firewall score: 69 (from `director_selections.pre_firewall_score`)
- System final score: 44 (from `stage_attempts.score`)
- `firewall_triggered = 1`
- `gate_basis = continuity_firewall`
- Contradiction: 20억 원 capital appearing when 전 재산 was already invested in WTI

The `cost_log` records this as `reject_bucket: post_select_conflict`, while `stage_attempts` records `failure_category: LOGIC_ERROR`. Different semantic levels (reject_bucket vs failure_category) but both correctly identify the rejection.

**Classification: `confirmed primary cause` — Stage 4 capital-state contradiction**

### F-3. CoVe Runtime Failure (EP6 Round 3)

`episode_production.jsonl` logs a `STAGE4_COVE_RUNTIME_ADVISORY` for EP6:
```
error_type: ChainOfVerificationParseError
error_message: JSONDecodeError: Expecting value: line 1 column 1 (char 0)
director_pass_preserved: true
```

The Chain of Verification LLM check returned empty/unparseable JSON, but the Director's PASS was preserved anyway (`director_pass_preserved: true`). This means EP6's final PASS at score 98 was accepted **without CoVe validation**.

Quick warning attached: "직전 화 아이템(패)이 현재 화에서 언급되지 않음" — a carryover item was flagged but not enforced.

**Classification: `validator-only signal`** — the CoVe failure didn't cause a rescue round, but it may have allowed a weaker final manuscript through.

### F-4. Blueprint Coverage Gap (EP6, EP7)

| EP | Blueprint Expected | Blueprint Reflected | Coverage | Verdict |
|---|---|---|---|---|
| 5 | 5 | 5 | 100% | PASS (95) |
| 6 | 5 | 3 | 60% | PASS (98) |
| 7 | 5 | 3 | 60% | PASS (90) |

EP6 and EP7 were accepted at 60% blueprint coverage. The `blueprint_coverage` metric is logged in `quality_metrics.jsonl` with `valid: false` but this didn't block the PASS verdict. The Director overrode the coverage gap.

**Classification: `confirmed secondary amplifier`** — incomplete blueprint coverage means Stage 4 dropped 2/5 blueprint elements, which may indicate Stage 3→4 contract leakage.

### F-5. PASS_WITH_FIX Invisible to Runtime Audit (EP7)

`runtime_audit.jsonl` records:
- EP5: 2 `stage4_retry_pathology_signal` (matches 2 REJECTs)
- EP6: 2 `stage4_retry_pathology_signal` + 1 `cove_runtime_advisory` (matches 2 REJECTs + CoVe error)
- EP7: 0 `stage4_*` events

EP7's PASS_WITH_FIX → inplace_patch → patch_reaudit_pass path produced **zero runtime_audit entries**. The patch cycle (fixing '18년 전' → '전생에' timeline error) is only visible in `stage_attempts` and `director_selections`, not in the runtime audit trail.

**Classification: `sink mismatch`** — runtime_audit only logs hard REJECTs as pathology signals, missing the PASS_WITH_FIX → patch repair path entirely.

### F-6. Score Plateau Detection (EP5)

`episode_production.jsonl` for EP5 round 2 records `plateau_detected: true`:
> "최근 두 라운드의 점수가 93점으로 동일합니다. 동일 수정 루프를 반복 중일 수 있습니다."

The system correctly identified that EP5 was stuck at score 93 across two consecutive REJECT rounds. The third round broke the plateau (score 95, PASS). This detection is **only in `episode_production.jsonl`**, not in `stage_attempts` or `runtime_audit`.

**Classification: `cleared / not primary`** — plateau detection worked, but it's a single-sink signal.

### F-7. State Logs Capital Unit Mismatch

`state_logs` and `state_changes.jsonl` record capital in different units:

| EP | state_logs.capital | state_changes.capital |
|---|---|---|
| 5 | 1,958,762.88 (USD) | "19억 원 (약 195만 달러)" |
| 6 | 1,950,000.0 (ambiguous) | "19억 원 (전액 WTI 증거금)" |
| 7 | 0 (KRW, free cash) | "19억 + 15억 (positions)" |

EP5 state_logs is in USD, while state_changes describes it in KRW with USD parenthetical. EP6 state_logs is ambiguous (1.95M could be USD or a truncated KRW). EP7 state_logs correctly shows `capital: 0, total_assets: 3,400,000,000` (all invested, no free cash).

**Classification: `sink mismatch`** — no impact on rescue rounds, but complicates cross-episode capital reconciliation.

---

## 4. Attempt Count Summary

| EP | Stage 3 | Stage 4 | Total Attempts | Rescue Rounds |
|---|---|---|---|---|
| 5 | 1 (PASS) | 3 (R, R, P) | 4 | 2 |
| 6 | 3* (PASS on a3) | 3 (R, R, P) | 6 | 4* |
| 7 | 1 (PASS) | 1 (PWF→patch→P) | 2 | 0-1** |

*EP6 Stage 3 attempts 1-2 are lost from DB; rescue round count may be higher.
**EP7 PASS_WITH_FIX required a patch but was not a full rescue round.

---

## 5. DB Truth Authority Map

| Sink | Authoritative For | EP5-7 Integrity |
|---|---|---|
| `stage_attempts` | Final attempt verdict, score, artifact_path | INTACT |
| `director_selections` | Director's raw verdict, pre-firewall score | INTACT |
| `manuscripts` | Final accepted content | INTACT (5585/4876/5641 chars) |
| `blueprints` | Accepted blueprint data | INTACT (6392/7957/4991 chars) |
| `state_changes.jsonl` | Post-episode world state + fact ledger | INTACT |
| `state_logs` | Numeric capital/asset truth | INTACT (unit ambiguity noted) |
| `episode_production.jsonl` | Pathology fingerprint, retry directives | INTACT |
| `quality_metrics.jsonl` | Validation + retrieval + blueprint coverage | INTACT |
| `runtime_audit.jsonl` | Runtime heartbeat (NOT attempt-authoritative) | GAP (EP7 patch invisible) |
| `cost_log` | Per-episode cost breakdown | INTACT |
| `sync_status` | Vector sync state | INTACT (all synced) |

---

## 6. Mandatory Lane Answers

**Dominant seam in this lane: mixed (Stage 4 primary for content; sink-reconciliation secondary for observability)**

The rescue rounds are caused by Stage 4 content contradictions (capital/leverage/timeline), not by DB/metadata failures. The metadata correctly records everything it's asked to record. The gaps are in recording completeness (Stage 3 losing non-winning attempts, runtime_audit missing PASS_WITH_FIX patches).

**Can this lane explain a real EP5-EP7 rescue round by itself: no**

No DB/metadata failure triggered a rescue round. All rescue rounds trace to Stage 4 generating manuscripts with factual contradictions that validators caught.

**Would this lane justify a bounded next execution wave: no**

The recording gaps (F-2 Stage 3 persistence, F-5 runtime_audit completeness, F-7 capital unit normalization) are observability improvements, not rescue-round fixes. They belong in a hygiene wave, not a rescue-round reduction wave.
