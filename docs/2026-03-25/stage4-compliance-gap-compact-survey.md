# Stage 4 Compliance Gap — Compact Survey

Date: 2026-03-25
Type: static survey (compact, post-canary classification)
Scope: remaining Stage 4 ChiefWriter/Director compliance seam after Wave 1
Mode: survey-only, no code changes
Prior Evidence: `docs/2026-03-25/stage4-chiefwriter-state-injection-wave1-canary-report.md`

## Evidence Surfaces Inspected

| Surface | Path | Key Lines |
|---------|------|-----------|
| CW prompt template | `chief_writer_prompts.py` | L104 (IFC slot), L129-134 (authority hierarchy), L152 (opening anchor) |
| Director ensemble selection | `director_prompts.py` | L80-106 (7-item contradiction checklist), L91-96 (investment math) |
| Director audit rubric | `director_prompts.py` | L433-495 (6-category scoring, 설정 일관성 20pt) |
| Retry runtime | `stage4_retry_runtime.py` | L849-896 (patch mode decision) |
| Post-select feedback | `stage4_interview_round.py` | L3754-3764 (error classification), L3774-3806 (previous_attempt) |
| CW feedback injection | `chief_writer.py` | L1078-1111 (regenerate), L1923-1944 (patch) |
| Failure analyzer | `failure_analyzer.py` | L1971-1985 (telemetry-only, no prompt feedback) |
| IFC extraction | `stage4_immutable_fact_contract.py` | L161-185 (committed-state), L188-218 (completed-event) |
| EP4 canary artifacts | `canary_0325_stage4_fix/logs/artifacts/stage4/ep_0004/attempt_01-03/` | |
| EP5 canary artifacts | `canary_0325_stage4_fix/logs/artifacts/stage4/ep_0005/attempt_01-03/` | |
| Production JSONL | `canary_0325_stage4_fix/logs/episode_production.jsonl` | 27 entries |

## Findings

### F1. IFC committed_state_facts are monetary-only — structural facts missing

**File:** `stage4_immutable_fact_contract.py` L169-175

The `_extract_committed_state_facts()` function matches lines by monetary/resource keywords: `억`, `만원`, `원`, `달러`, `$`, `계좌`, `자본`, `잔고`, `자산`, `capital`, `won`, `balance`, `account`, `fund`.

After Wave 1, the fact_ledger data reaches this function and yields:
```
capital: 2000000000.0 won (ep3 기준)
```

This tells the CW "capital = 20억 원" at ⛔ authority. It does NOT tell the CW:
- "this capital is in a **personal** derivatives account, not the SW Investment corporate account"
- "account setup was **completed** in EP3 (OTP received, HTS access confirmed)"
- "start location is **압구정 증권사 인근 라운지 카페**, not 증권사 VIP 라운지"

**Canary evidence:** EP5 R1 — CW correctly tracked the 20억 원value but wrote "SW인베스트먼트 법인 계좌" (corporate account) instead of "개인 명의 파생 계좌" (personal account). The monetary fact was obeyed; the structural fact was blurred.

### F2. Director Audit Rubric collapses all consistency into one 20pt bucket

**File:** `director_prompts.py` L433-439

```
1. 설정 일관성 (20점): [setting_consistency]
   - 20점: 설정 완벽 준수 (무공, 인물, 물리적 인과 모두 정상)
   - 12점: 경미한 설정 미비 (보조 NPC 이름 오타 등)
   - 0점: Hard Constraint 위반 (미습득 무공, 죽은 자 부활 등)
```

The rubric does NOT enumerate:
- Opening-anchor place name violation
- Account ownership mismatch
- Committed-state numeric regression
- Completed-event reopening

These are all collapsed into generic "설정 일관성." The Director Ensemble Selection prompt (L80-106) has a 7-item contradiction checklist that IS more specific, but the scoring rubric that produces the actual score does not enforce these as distinct penalty items.

**Canary evidence:** EP4 R1 — Director scored 96 despite CW writing the wrong opening location. The 20pt "설정" bucket absorbs location errors as "경미한 설정 미비" (12pt) rather than "Hard Constraint 위반" (0pt), because opening-anchor place violation is not explicitly listed as a hard constraint in the rubric.

### F3. Patch mode is NOT score-triggered — it is reject_bucket + fix_scope triggered

**File:** `stage4_retry_runtime.py` L849-896

Patch mode triggers when:
1. `reject_bucket == "post_select_conflict"` AND `fix_scope != "full"` AND `round_num <= 1` (force_patch)
2. OR `fix_scope in ("inplace", "partial")` (optional patch)

There is NO score threshold for patch mode. The earlier hypothesis "score 96 triggers patch mode that preserves structural errors" is **incorrect**. What happens instead:

- Post-select sets fix_scope to "full" → patch mode is NOT triggered → R2 gets full rewrite
- R2 Director gives fix_scope "inplace" → patch mode IS triggered → R3 gets patch

**Canary evidence:** EP4 R1 (post_select_conflict, fix_scope=full) → R2 full rewrite. EP4 R3 (director_primary_pass_with_fix, fix_scope=inplace) → patch applied → reaudit PASS. The retry path is working correctly.

### F4. Failure classification is coarse — no structural-fact differentiation

**File:** `stage4_interview_round.py` L3754-3763

Post-select conflicts are classified into only 4 categories:
- `POST_SELECT_CONTINUITY_CONFLICT`
- `POST_SELECT_HISTORY_CONFLICT`
- `POST_SELECT_CONTINUITY_AND_HISTORY`
- `POST_SELECT_CHECK_ERROR`

"Resource balance failure", "place name error", "account ownership mismatch", and "completed-event regression" all collapse into the same `POST_SELECT_HISTORY_CONFLICT` bucket. The error_category is stored in DB (telemetry) but NOT fed into the CW prompt for the next round.

**File:** `failure_analyzer.py` L1971-1985 — `top_failure_categories()` reads aggregated failure stats but does NOT inject anything into runtime prompts. It is observation-only.

### F5. Director newly caught EP5 R2 due to Wave 1 + feedback priming

**Canary evidence:** EP5 R2 — Director REJECT (score 83), reason: "파생 계좌의 소유 주체(개인 vs 법인) 설정 혼동"

Two factors enabled this:
1. **Wave 1 gave the Director reference data.** With committed_state_facts now populated, the Director's 7-item contradiction checklist (L80-106) had numeric anchors to compare against.
2. **Post-select R1 feedback was injected.** The R1 post-select rejection message ("20억 원이 들어간 계좌가 'SW인베스트먼트 법인 계좌'로 묘사") was appended to director_feedback (L3764) and propagated into R2's context. The Director was primed for the specific ownership issue.

The Director did NOT catch EP4 R1's place name error because:
- The opening-anchor place constraint is not enumerated in the audit rubric (F2)
- R1 had no prior feedback to prime the Director for the specific error
- The 20pt "설정 일관성" bucket treated it as minor (12pt penalty), not a hard violation (0pt)

## Classification: What CW Is Receiving But Not Obeying

| Fact | Authority Level | In ⛔ IFC? | CW Compliance | Evidence |
|------|----------------|-----------|---------------|----------|
| Capital = 20억 원 | ⛔ HIGH (IFC committed_state_facts) | **Yes** (Wave 1) | **Compliant by R3** | EP4 R3: "파텍필립 처분" workaround |
| Account = personal, not corporate | MEDIUM (chain_link prose) | **No** | **Non-compliant R1** | EP5 R1: "SW인베스트먼트 법인 계좌" |
| Start location = 라운지 카페 | ⛔ HIGH (IFC opening_anchor) | **Yes** | **Non-compliant R1** | EP4 R1: "서울 모처의 라운지" |
| Account setup completed | MEDIUM (prev_digest/chain_link) | **No** | **Non-compliant R1** | EP5 R1: "최종 서명 필요" reopening |

**Pattern:** CW complies with ⛔ IFC **monetary** facts (capital value) but does NOT comply with:
- ⛔ IFC **spatial** facts (opening-anchor location) — the ⛔ marker is present but the CW substitutes similar-sounding locations
- MEDIUM-authority **structural** facts (account ownership, procedural completion) — these are NOT in the ⛔ IFC section at all

## Classification: What Director Is Failing to Catch Early

| Issue | Director Ensemble Selection? | Director Audit Rubric? | Caught? |
|-------|------------------------------|----------------------|---------|
| Monetary regression (20억 불일치) | Yes (L91-96 자본금 정합) | No (generic 설정) | EP5 R2 only (feedback-primed) |
| Account ownership mismatch | No | No | EP5 R2 only (feedback-primed) |
| Opening-anchor place drift | No | No (generic 설정) | Not caught by Director |
| Completed-event reopening | Partially (L82-84 상태 연속성) | No (generic 설정) | Not caught by Director |

**Pattern:** Director catches issues only when (a) post-select feedback primes it, or (b) the violation is extreme enough to trigger the Ensemble Selection 7-item checklist. The Audit Rubric's 20pt "설정 일관성" bucket is too coarse to penalize specific IFC violations.

## Classification: What Post-Select Is Catching Late

All 7 post-select REJECTs across EP2-EP5 were for continuity or history conflicts. Post-select uses separate LLM calls that read prior manuscripts directly — it is NOT constrained by IFC extraction filters. It catches:
- Resource balance contradictions
- Account ownership mismatches
- Location continuity errors
- Completed-event regressions

Post-select is the safety net that compensates for both CW non-compliance and Director blind spots. But it costs 1-2 extra retry rounds per episode.

## Root Cause Summary

The dominant remaining gap is NOT:
- ~~Prompt compliance weakness~~ — CW complies with ⛔ monetary facts when present
- ~~Patch-mode preservation~~ — patch mode is correctly governed by fix_scope, not score
- ~~Post-select-only dependence~~ — post-select is a symptom, not a cause

The dominant remaining gap IS:
- **IFC committed_state_facts extraction is too narrow** — extracts monetary values but not structural state (entity ownership, procedural completion, place identity)
- **Director Audit Rubric is too coarse** — collapses all consistency into one 20pt bucket without enumerating IFC-specific violation types

Of these two, **IFC extraction narrowness** is the root cause. If structural facts were in the ⛔ section, CW compliance would improve (proven by the monetary fact compliance pattern), and Director would have explicit facts to check against (proven by the EP5 R2 feedback-primed catch).

## Single Recommendation

**IFC committed_state_facts extraction broadening** — expand `_extract_committed_state_facts()` in `stage4_immutable_fact_contract.py` to extract structural facts beyond monetary keywords.

Specifically:
1. Extract entity-ownership lines from fact_ledger summary (e.g., "개인 명의", "법인", "계좌 소유")
2. Extract procedural-completion lines from chain_link/prev_digest into completed_event_facts (e.g., "세팅 완료", "OTP 수령", "접속 확인")
3. Keep the same ⛔-marked rendering path in `render_packet_for_cw()`

Why this lane:
- **Highest ROI**: CW demonstrably complies with ⛔ IFC facts (capital value compliance by R3). Putting structural facts in the same ⛔ section should yield the same compliance improvement.
- **Lowest blast radius**: Only touches `_extract_committed_state_facts()` and `_extract_completed_event_facts()` in one file. No Director, retry, post-select, or Stage 3 changes needed.
- **Proven mechanism**: Wave 1 proved that restoring the fact_ledger → IFC path reduced retry loops by 50%. Broadening what gets extracted uses the same proven path.

Why NOT the alternatives:
- Director rubric patch: helps detection but doesn't prevent CW errors; higher blast radius (touches Director prompt that affects all genres)
- Post-select feedback improvement: feedback already reaches CW; the problem is it takes 1-2 rounds; doesn't address root cause
- CW prompt compliance hardening: the prompt already has ⛔ markers and authority hierarchy; diminishing returns on stronger language

## Guardrails

- Do not open Stage 3, world_state population, or timeout/ASP policy
- Do not modify Director prompts in this wave (separate investigation if needed after IFC broadening)
- Do not change post-select or retry routing logic
- Keep the expansion bounded to fact_ledger and chain_link/prev_digest content already available to `build_packet()`

---

## 3-Pass Audit Notes

- Pass 1: scope explicitly bounded to Stage 4 compliance seam; 6 code surfaces + canary artifacts inspected; excluded surfaces listed
- Pass 2: all findings anchored to file/line references and canary attempt_key evidence; no overclaiming; IFC extraction narrowness confirmed against both static code and live canary artifacts
- Pass 3: single recommendation is actionable and bounded; blast radius is one file; no scope creep
- Confidence: 96%

---

- Dominant remaining Stage 4 seam: **IFC-extraction-too-narrow** (monetary facts extracted, structural facts missing from ⛔ section)
- Best next single move: **IFC committed_state_facts extraction broadening** (entity ownership + procedural completion into ⛔ IFC)
- Should Codex open an execution SSOT now: **yes**
