# T5: Validator / Retry / PASS_WITH_FIX Semantics

Date: 2026-03-24
Status: final (3-pass audited)
Document Type: lane survey report
Lane: T5 — Validator / Retry / PASS_WITH_FIX Semantics
Master Order: `docs/2026-03-24/ep5-ep7-midarc-residual-6terminal-master-order.md`
Primary Evidence Anchors:
- `docs/2026-03-24/console.txt` (L1210-1850)
- `projects/0324_00_/logs/episode_production.jsonl` (L16-25)
- `projects/0324_00_/logs/session/decisions.jsonl` (L23-29)
- `modules/core/stage4_interview_round.py` (L1740-1826, L2320-2370, L3635-3808, L3850-3970, L4000-4066, L5202-5320)
- `modules/core/stage4_reject_runtime.py` (L48-100)
- `modules/core/stage4_retry_runtime.py` (L84-100)
- `modules/core/stage4_outcome_runtime.py` (L800-850)
- `modules/domain/agents/director_ensemble.py` (L287-303, L619-627, L1040-1089, L1253-1296)
- `modules/domain/agents/director_auditor.py` (L1098-1129)

## 1. Gate Taxonomy — Four Active Gates in EP5-EP7

### 1.1 `post_select_conflict` — Post-Selection Continuity/History LLM Firewall

- **Code**: `stage4_interview_round.py` L3635-3808 `_run_post_select_checks()`
- **Trigger**: After Director selects a candidate and PASSES it, runs two LLM checks in parallel (`ThreadPoolExecutor(max_workers=2)`):
  - `check_manuscript_continuity_with_cache()` — compares new manuscript against DB-stored previous episodes (limit=10)
  - `check_manuscript_history_conflicts()` — compares against raw manuscript history text
- **If either returns `decision=CONFLICT`**: provisional PASS → REJECT downgrade, `gate_basis=post_select_conflict`, `repair_scope=full`
- **Error categorization**: `POST_SELECT_CONTINUITY_AND_HISTORY`, `POST_SELECT_CONTINUITY_CONFLICT`, `POST_SELECT_HISTORY_CONFLICT`, or `POST_SELECT_CHECK_ERROR` (L3756-3763)
- **Classification**: `confirmed primary cause` for EP5 rescue rounds

### 1.2 `continuity_firewall` (V75-C) — Contradiction Firewall

- **Code**: `director_ensemble.py` L1040-1089
- **Trigger**: During Director ensemble review, if contradiction check finds ≥1 CRITICAL or ≥2 MAJOR contradictions:
  - First classifies whether fixable → `PASS_WITH_FIX` path (score capped at 97)
  - If not fixable → `firewall_triggered=True`, score capped at 44, forced REJECT
- **Gate derivation**: `_derive_gate_basis()` at L287-303: `firewall_triggered → "continuity_firewall"`
- **Classification**: `confirmed primary cause` for EP6 hidden round

### 1.3 `director_primary_reject` — Direct LLM REJECT

- **Code**: `director_ensemble.py` L303 (default fallback in `_derive_gate_basis`)
- **Trigger**: Director LLM itself judges REJECT
- **Classification**: `confirmed secondary amplifier` for EP6 R1, EP7 R1/R2

### 1.4 `PASS_WITH_FIX` — Inplace Fix Contract

- **Code**: `stage4_interview_round.py` L1776-1826 `_enforce_pass_with_fix_contract()`
- **Contract enforcement**: Checks fix_scope is `inplace`, fix_pack has patch_targets/must_fix/do_not_regress/success_condition. If contract fails → downgrade to REJECT.
- **Loop**: `_execute_pass_with_fix_loop()` at L3810+ delegates to `Stage4RetryRuntime.execute_pass_with_fix_loop()`
- **Classification**: `validator-only signal` — functional but creates wasted work before post_select_conflict catches blueprint-level errors

## 2. Per-Episode Gate Trace

### EP5: 3 Rounds (post_select_conflict primary)

| Round | Console | Director Verdict | Score | Final Gate | Final Verdict | Root Cause |
|---|---|---|---|---|---|---|
| R1 | L1221-1293 | PASS_WITH_FIX | 92 | `post_select_conflict` | REJECT | NPC 박성호 시중은행→한미증권 소속 충돌 (blueprint error) |
| R2 | L1296-1385 | REJECT | 78 | `director_primary_reject` | REJECT | 박성호 태도 리셋 + blueprint 장소 오류 잔류 |
| R3 | L1387-1435 | PASS | 95 | `director_primary_pass` | PASS | ASP red-team 교정 + patch mode 성공 |

**Gate grounding assessment**: `post_select_conflict` is **well-grounded**. The continuity/history LLM checks correctly detect that NPC 박성호 was established at 시중은행 in EP3 but the EP5 blueprint erroneously references 한미증권. Director's initial PASS_WITH_FIX (for style issues) cannot catch this because the Director treats the blueprint as authoritative.

### EP6: 3 Rounds (director_primary_reject + continuity_firewall)

| Round | Console | Director Verdict | Score | Final Gate | Final Verdict | Root Cause |
|---|---|---|---|---|---|---|
| R1 | L1462-1545 | REJECT | 75 | `director_primary_reject` | REJECT | 장소 연속성 단절 (한미증권), 산술 오류 (잔액 5억→4.7억) |
| R2 | *not visible* | REJECT (firewall) | 44 | `continuity_firewall` | REJECT | 자본금 정합: 전 재산 소진 후 설명 없이 20억 법인통장 등장 |
| R3 | L1546-1585 | PASS | 90 | `director_primary_pass` | PASS | Blueprint 한미증권 오류 자체 교정 → PASS |

**Gate grounding assessment**:
- `director_primary_reject` at R1: **well-grounded** — correctly catches 한미증권 장소 오류 + 산술 오류.
- `continuity_firewall` at R2: **well-grounded** — correctly catches 자본금 정합 위반 (≥1 CRITICAL contradiction → score capped at 44).
- **Critical sink observation**: R2 (firewall REJECT) is invisible in console but fully recorded in decisions.jsonl (R1: REJECT s=44 gate=continuity_firewall fw=True). Console shows Round 2 as PASS, skipping the hidden rejection. See §4 for details.

### EP7: 3 Rounds (director_primary_reject primary)

| Round | Console | Director Verdict | Score | Final Gate | Final Verdict | Root Cause |
|---|---|---|---|---|---|---|
| R1 | L1613-1687 | REJECT | 86 | `director_primary_reject` | REJECT | 한미증권 장소 오류 (blueprint error) |
| R2 | L1688-1768 | REJECT | 75 | `director_primary_reject` | REJECT | 1인칭 시점 위반 (3인칭 작품) |
| R3 | L1769-1822 | PASS | 96 | `director_primary_pass` | PASS | 피드백 완벽 반영 + ASP 교정 성공 |

**Gate grounding assessment**: All three Director verdicts are **well-grounded**. The Director correctly catches both the blueprint-inherited 장소 오류 and the LLM-generated 시점 위반.

## 3. PASS_WITH_FIX Coexistence Analysis

### 3.1 Processing Order

The positive-verdict transition chain is:
1. Director issues verdict (PASS / PASS_WITH_FIX / REJECT)
2. `_process_verdict()` (L3855) → quality floor gate (PASS < quality_gate_score → REJECT)
3. `_process_positive_verdict()` (L3920) → builds seed payload
4. `_run_positive_verdict_transition()` (L4000):
   - **First**: `_run_post_select_checks()` — LLM continuity/history check
   - **Then**: `_execute_pass_with_fix_loop()` (only if still PASS_WITH_FIX)
5. If post_select downgrades to REJECT, the PASS_WITH_FIX loop never runs

**File/line anchors**: `stage4_interview_round.py` L4018-4049

### 3.2 Coexistence Semantics

The architecture is **correct but inefficient**:
- Post-select checks run BEFORE the PASS_WITH_FIX loop (L4018-4032 precedes L4035-4049)
- If post-select finds a conflict, verdict becomes REJECT and the fix loop is skipped
- This prevents PASS_WITH_FIX from coexisting with a later post_select_conflict in the same round

**However**: In EP5 R1, the console shows the full PASS_WITH_FIX flow completing (TF-32-V patch applied) BEFORE post-select runs. Console L1130 shows `🔩 [TF-32-V] PASS_WITH_FIX patch #1/3` for EP4, not EP5. For EP5 R1, the post-select check catches the conflict immediately after Director selection, before any fix patches are applied. This is architecturally sound.

### 3.3 Is PASS_WITH_FIX Creating Residual Architecture Smell?

**Not directly.** PASS_WITH_FIX operates at the style/local-fix level (inplace fix_scope). The rescue rounds in EP5-EP7 are caused by:
- Blueprint-level errors (한미증권 → should be 시중은행) — this is a Stage 3 problem
- Capital/timeline continuity errors — these are Stage 3 + Stage 4 mixed problems
- LLM perspective violations (1인칭 vs 3인칭) — this is a Stage 4 generation problem

PASS_WITH_FIX addresses none of these. It is functionally orthogonal to the rescue causes.

## 4. Sink Mismatch Inventory (Validator Recording Fidelity)

### 4.1 EP5 Round 2 Gate Mismatch

| Sink | R1 (0-indexed) Gate | R1 Score |
|---|---|---|
| Console (L1328) | `director_primary_reject` | 78 |
| decisions.jsonl (L24) | `post_select_conflict` | 93 |
| episode_production (L18) | `post_select_conflict` | 93 |

**Assessment**: `sink mismatch`. The decisions.jsonl and episode_production appear to carry forward the R0 `previous_attempt` fields (gate_basis, score) rather than recording the R1 Director's actual verdict. Console truth is authoritative here.

### 4.2 EP6 Hidden Round

| Sink | Round Count | R1 (hidden) |
|---|---|---|
| Console | 2 rounds visible | Not shown |
| decisions.jsonl | 3 entries | R1: REJECT s=44 gate=continuity_firewall fw=True |
| episode_production | pathology at round_num=2 | firewall_triggered=True, score=69 |

**Assessment**: `sink mismatch`. Console undercounts rounds. The firewall-forced REJECT (score capped at 44) is logged to decisions but not displayed in operator console. This means the operator cannot see when the firewall triggers mid-session.

### 4.3 EP6 Score Drift

| Round | Console Score | decisions.jsonl Score | ep_production Score |
|---|---|---|---|
| R0 | 75 | 78 | 83 |
| R1 (hidden) | — | 44 | 69 |
| R2 | 90 | 98 | — |

**Assessment**: `sink mismatch`. Three sinks record different scores for the same events. Likely cause: each sink captures score at a different processing point (Director raw score vs post-gate score vs pathology-inferred score).

### 4.4 EP7 Recording Gap

| Sink | Entries | Content |
|---|---|---|
| Console | 3 rounds (R1 REJECT 86, R2 REJECT 75, R3 PASS 96) | Complete |
| decisions.jsonl | 1 entry: R0 PASS s=90 gate=patch_reaudit_pass | 2 rejection rounds missing; score/gate disagree with console |

**Assessment**: `sink mismatch`. EP7 has a catastrophic decisions.jsonl recording failure. Two REJECT rounds are completely absent. The sole entry has wrong gate (`patch_reaudit_pass` instead of `director_primary_pass`), wrong score (90 vs 96), and wrong round semantics (appears to be a PASS_WITH_FIX re-audit result, but console shows no PASS_WITH_FIX for EP7).

## 5. Patch-Bias Assessment

### 5.1 Patch Mode Engagement Pattern

| Episode | Round | Patch Mode | Score In | Director Out | Result |
|---|---|---|---|---|---|
| EP5 R2 | L1298 | `[TF-23] InPlace: fix_scope='inplace', score=92` | 92 | REJECT 78 | Patch failed |
| EP5 R3 | L1390 | `[Phase 3-5B] 패치 모드: score=83` + ASP | 83 | PASS 95 | ASP broke patch loop |
| EP6 R2 | L1550 | `[Phase 3-5B] 패치 모드: score=80` | 80 | PASS 90 | Patch succeeded |
| EP7 R2 | L1692 | `[Phase 3-5B] 패치 모드: score=86` | 86 | REJECT 75 | Patch failed (시점 위반) |
| EP7 R3 | L1773 | `[Phase 3-5B] 패치 모드: score=78` + ASP | 78 | PASS 96 | ASP broke patch loop |

### 5.2 Assessment

Patch-bias **exists but is bounded**:
- Patch mode engages on retry rounds when score ≥ 50 (`[Phase 3-5B]`)
- It preserves the original manuscript and applies targeted fixes
- **Failure mode**: Patch cannot address structural problems (NPC affiliation, perspective). It succeeds only on local/surface issues (장소 명칭, 산술).
- **Mitigation**: ASP red-team correction triggers at Round 3 and effectively breaks the patch loop by generating fresh alternatives alongside the patch

The escalation chain is: Patch Mode → fails if structural → ASP Red-Team at R3 → fresh generation with full context. This is working as designed.

## 6. Answers to Lane Questions

### Are `post_select_conflict`, `continuity_firewall`, and `director_primary_reject` well-grounded?

**Yes, all three are well-grounded.**

- `post_select_conflict`: Correctly catches NPC 박성호 시중은행→한미증권 affiliation drift (EP5). This is a real continuity violation originating from the Stage 3 blueprint.
- `continuity_firewall`: Correctly catches 자본금 정합 (capital consistency) violation (EP6). Score cap at 44 is appropriate for CRITICAL severity.
- `director_primary_reject`: Correctly catches 장소 오류, 산술 오류, 시점 위반 across EP6-EP7. Director LLM reviews are accurate.

### Is PASS_WITH_FIX coexisting with later conflict in a sane way or a residual architecture smell?

**Sane, not a smell.** The processing order (L4018-4049) runs post-select checks BEFORE the PASS_WITH_FIX loop. If post-select downgrades the verdict, the fix loop is skipped entirely. PASS_WITH_FIX and post_select_conflict cannot coexist in the final verdict of the same round.

EP5 R1 demonstrates this correctly: Director gives PASS_WITH_FIX → post-select detects 한미증권 conflict → verdict becomes REJECT before any fix patches run.

### Is patch-bias still present in the rescue path?

**Present but mitigated.** Patch mode fails on structural issues (EP5 R2, EP7 R2), and the ASP red-team escalation at Round 3 successfully breaks the loop in both EP5 and EP7. The 3-round rescue pattern (R1 fail → R2 patch fail → R3 ASP success) is the actual production pattern observed.

## 7. Root Cause Attribution

The EP5-EP7 rescue rounds have **two distinct families**:

### Family A: Blueprint-Level Location Error (한미증권)
- **Source**: Stage 3 blueprint (confirmed by T3 lane scope)
- **Episodes**: EP5 R1 (post_select_conflict), EP6 R1 (director_primary_reject), EP7 R1 (director_primary_reject)
- **Mechanism**: Blueprint says "여의도 한미증권" but episode truth established "시중은행 본점" in EP3-EP4
- **Resolution**: Director or post-select catches it, ChiefWriter self-corrects on retry

### Family B: Stage 4 Generation Errors
- **Episodes**: EP5 R2 (박성호 태도 리셋), EP6 hidden R2 (자본금 정합), EP7 R2 (시점 위반)
- **Mechanism**: ChiefWriter generates structurally incorrect content independent of blueprint truth
- **Resolution**: Director rejects, patch mode fails, ASP escalation succeeds

### Family C: Sink Recording Fidelity (Cross-Cutting)
- **Episodes**: EP5 R1 gate mismatch, EP6 hidden round + score drift, EP7 recording gap
- **Mechanism**: decisions.jsonl records from different pipeline points than console, with stale data inheritance and conditional write bugs
- **This does not cause rescue rounds** but makes post-mortem analysis unreliable

## 8. Mandatory Lane Closure

- **Dominant seam in this lane**: mixed (Stage 3 primary for Family A, Stage 4 primary for Family B, sink-reconciliation for Family C)
- **Can this lane explain a real EP5-EP7 rescue round by itself**: yes — Family A (blueprint 한미증권 error) directly explains EP5 R1, EP6 R1, EP7 R1 rejections; Family B explains the remaining rescue rounds
- **Would this lane justify a bounded next execution wave**: yes — two separable targets:
  1. **Sink recording fidelity** (decisions.jsonl gate/score inheritance + conditional write bugs) — bounded code fix in `stage4_interview_round.py` decision recording path and `stage4_outcome_runtime.py` pathology recording path
  2. **Console visibility for firewall REJECT** — bounded fix to ensure `continuity_firewall` REJECT rounds are visible in operator console
