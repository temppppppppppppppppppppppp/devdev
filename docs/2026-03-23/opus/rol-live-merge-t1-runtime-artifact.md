Date: 2026-03-23
Status: final
Document Type: ROL live-merge T1 lane report (Runtime / Artifact Flow)
Canonical Path: `docs/2026-03-23/opus/rol-live-merge-t1-runtime-artifact.md`
Temp Mirror Path: none
Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
Baseline Dirty Summary: `dirty workspace with fresh-run artifacts under projects/0_0323/, runtime/test/doc edits, and prior survey docs`
Resume Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
Resume Drift Summary: `same HEAD; fresh run was user-stopped during Arc 2 Stage 2 batch enrich; projects/0_0323/ contains 3 episodes plus partial Arc 2 state`
Source Survey Docs:
- `docs/2026-03-23/rol-live-merge-3terminal-order.md`
- `docs/2026-03-23/rol-freshrun-evidence-bottleneck-remediation-plan.md`
- `docs/2026-03-23/pre-rerun-root-cause-merge-audit.md`
- `docs/2026-03-23/q1-q8-r2-merge-audit.md`
Evidence Artifacts:
- `docs/2026-03-23/console.txt`
- `projects/0_0323/logs/artifacts/stage3/**`
- `projects/0_0323/logs/artifacts/stage4/**`
- `projects/0_0323/drafts/ep_0001.txt`, `ep_0002.txt`, `ep_0003.txt`
Side-Effect Coverage:
- artifact truth: yes
- metadata truth: partial (DB not queried directly this lane)
- console/operator truth: yes
- JSONL/metrics truth: referenced from prior surveys
- config/bootstrap: not primary

---

# T1 Runtime / Artifact Flow -- Live-Merge Lane Report

## 1. Executive Summary

The fresh run reached a **user-stopped** terminal state (console line 1144: `사용자 중단 요청`) during Arc 2 Stage 2 batch enrich. Because the run was user-stopped rather than crashed, the accumulated evidence from Arc 1 (3 episodes produced, Ep3 required 5 rounds) is valid for diagnostic purposes.

Key lane-level findings:

1. **Scene-completeness false positive is still the dominant noise source** but is now partially stale as a blocker claim: the scene validator code was already patched with a header-first path (`_SCENE_HEADER_RE` at `blocking_validator_scene_checks.py:130-132`), and the final Ep3 manuscript (attempt 05) does contain properly formatted `### 씬 N:` headers. The residual problem is that earlier manuscript candidates (rounds 1-4) did not emit scene headers, so the keyword-window fallback still produced false `0/5` warnings on every round until the Writer finally adopted headers by round 5.

2. **Opening-anchor packet (TF-2) is now implemented and live** (`chief_writer_context.py:271-297`). The Ep3 attempt_05 manuscript opens at the correct location (`유성그룹 회장 자택`) with the correct date (`2006년 1월 18일 저녁`), matching the blueprint. The prior bottleneck claim about "no opening-anchor packet" is **stale** -- the fix has landed.

3. **Post-select downgrade from PASS to REJECT is working as designed** and now correctly classifies failure categories (`POST_SELECT_CONTINUITY_AND_HISTORY`, etc.) at `stage4_interview_round.py:3696-3703`. The prior claim about NULL failure categories on post-select rejects is **stale** for Stage 4.

4. **Retry feedback accumulation remains a live concern**: the console shows the full R0-through-R4 feedback chain being replayed to the Writer, which grows monotonically. By round 4 the feedback section exceeded the actual manuscript content. Fix Pack `patch_targets` was empty on rounds 3-4 (console lines 901, 1061), confirming the retry-loop degradation pattern from prior surveys is still present.

5. **The CONDITIONAL_PASS downstream recognition bug (Q3) remains live** at `director_ensemble.py:1187-1204` and `stage4_interview_round.py:3787`. This did not trigger in this run but is still structurally present.

**Rerun blocker assessment for this lane**: No P0 rerun blocker. The opening-anchor and scene-validator header path both landed. The residual retry inefficiency (P1) and CONDITIONAL_PASS bug (P1) are not crash blockers but will reduce quality and waste rounds.

## 2. Included Coverage

### Files inspected (static)
- `modules/validation/blocking_validator_scene_checks.py` -- scene completeness check, header regex, keyword fallback
- `modules/domain/agents/chief_writer_context.py` -- blueprint section extraction, opening anchor packet, scene breakdown injection
- `modules/domain/agents/chief_writer_prompts.py` -- prompt template with opening_anchor_section
- `modules/core/writer_template.py` -- ManuscriptTemplate generation from blueprint
- `modules/core/stage4_interview_round.py` -- verdict processing, post-select checks, retry directives, fix-pack evaluation, failure category assignment
- `modules/domain/agents/director_ensemble.py` -- CONDITIONAL_PASS handling, ensemble quality gates

### Artifacts inspected (live)
- `projects/0_0323/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__action_focused.json` -- blueprint metadata
- `projects/0_0323/logs/artifacts/stage4/ep_0003/attempt_01/rejected_best__C.txt` -- no scene headers
- `projects/0_0323/logs/artifacts/stage4/ep_0003/attempt_03/rejected_best__A.txt` -- has scene headers
- `projects/0_0323/logs/artifacts/stage4/ep_0003/attempt_05/selected_candidate__A.txt` -- has scene headers, correct opening
- `projects/0_0323/logs/artifacts/stage4/ep_0003/attempt_05/patched_after_fix__A.txt` -- final patched version
- `projects/0_0323/drafts/ep_0001.txt`, `ep_0002.txt`, `ep_0003.txt` -- no scene headers in Ep1/Ep2, headers in Ep3
- `docs/2026-03-23/console.txt` -- full run transcript (1234 lines)

## 3. Static Watchlist

### W-1. Writer does not consistently emit scene headers on first generation

- Evidence type: `static+live`
- `chief_writer_prompts.py:132` injects `scene_breakdown` as JSON but does not explicitly instruct the Writer to use `### 씬 N:` markdown headers.
- Ep1 and Ep2 passed without scene headers; Ep3 first 2 candidates had no headers; only Ep3 round 3+ produced headers.
- The opening-anchor section (`chief_writer_prompts.py:148`) does not mention scene header format either.
- The `writer_template.py` generates `SceneSlot` objects but these are not injected into the Writer prompt as explicit header instructions.

### W-2. Keyword-window fallback produces unreliable results

- Evidence type: `static+live`
- `blocking_validator_scene_checks.py:231-256`: extracts up to 5 keywords, searches for them in a 500-char window, measures window length against 300-char threshold.
- When keywords happen to be short or common, the fallback can produce 0 matches for structurally valid manuscripts.
- Ep1 and Ep2 both show `0/5 씬만 완성` warnings despite being accepted by the Director.

### W-3. Retry directive monotonic growth

- Evidence type: `static+live`
- `stage4_interview_round.py:647-670`: `retry_directives` is built by joining all previous general feedback lines. Each round's full feedback is prepended with `[R{n} 이전 지시]`.
- Console shows that by round 4 the feedback section contains the full text from R0, R1, R2, and R3, including manuscript excerpts.
- `_compact_text` at line 420 has `limit=None`, meaning no truncation is applied to retry directives.

### W-4. CONDITIONAL_PASS falls through to reject path

- Evidence type: `static-only`
- `director_ensemble.py:1187-1204`: CONDITIONAL_PASS is mapped to PASS only in specific branches (V60.97 swap, adjusted pass-through, fallback). But `stage4_interview_round.py` `_process_verdict()` at L3808 only checks `verdict in ("PASS", "PASS_WITH_FIX")`.
- If `_apply_ensemble_quality_gates` returns CONDITIONAL_PASS and none of the resolution branches fire, it falls through to the else block at L1203 which maps to PASS. But if the resolution branches yield REJECT, the downstream `_process_verdict` correctly handles it.
- The real risk is in the fallback branch at L1203: `final_verdict = "PASS"` with `_adaptive_branch = "CONDITIONAL_PASS->PASS (fallback)"`. This path exists and may produce unexpected behavior if the original verdict was actually REJECT-worthy.

## 4. Live Evidence Snapshot

### 4.1 Run Terminal State

- **Status**: `user-stopped` (console line 1144: `⚠️ 사용자 중단 요청. 저장 후 종료합니다.`)
- **Session**: 20260323_182320, duration 0:58:45
- **Progress**: Arc 1 completed (Ep1-Ep3 produced), Arc 2 Stage 2 started but stopped during batch enrich
- **LLM calls**: 107 total, 100% success, $3.67 cost, 1.35M tokens
- **Pass rate**: Ep1 round 1, Ep2 round 1, Ep3 round 5 (user-stopped during round 5 assembly but Ep3 draft was saved)

### 4.2 Ep3 Artifact Truth (projects/0_0323)

| Attempt | File | Scene Headers | Opening Location | Opening Time |
|---|---|---|---|---|
| 01 | rejected_best__C.txt | none | not checked (rejected round 1) | not checked |
| 03 | rejected_best__A.txt | 5 headers (`### 씬 1:` through `### 씬 5:`) | (post-select rejected) | (post-select rejected) |
| 05 | selected_candidate__A.txt | 5 headers | 유성그룹 회장 자택 | 2006년 1월 18일 저녁 |
| 05 | patched_after_fix__A.txt | 5 headers | same | same |

### 4.3 Blueprint Metadata (Ep3)

- Blueprint: `final_blueprint__action_focused.json`
- `scene_count`: 5
- `start_location`: present (encoding display issue in console but file reads correctly)
- `time_flow`: 2006년 1월 17일 저녁 ~ 1월 18일 저녁

### 4.4 Console Key Signals

- **Every round 1-4** showed `[HIGH] 씬 완성도 부족: 0/5 씬만 완성` for all candidates (console lines 496, 567-571, 651-654, 857-860, 994-997)
- **Round 1** REJECT: continuity firewall (매수 주문 체결 모순)
- **Round 2** Director PASS_WITH_FIX (score 90) -> post-select REJECT (hotel location + history conflict)
- **Round 3** Director PASS (score 95) -> post-select REJECT (history conflict: father conversation repeat)
- **Round 4** Director PASS (score 95) -> post-select REJECT (timeline: "어제" vs same-day)
- **Round 5** user-stopped during assembly, but Ep3 was saved with 5 scene headers

### 4.5 Ep1/Ep2 Scene Header Status

- `projects/0_0323/drafts/ep_0001.txt`: **no scene headers** (passed round 1 anyway)
- `projects/0_0323/drafts/ep_0002.txt`: **no scene headers** (passed round 1 anyway)

This confirms that the Writer does not inherently produce scene headers. When it does (Ep3 rounds 3+), it is because accumulated feedback and constraints eventually push it into that format.

## 5. Top Provisional Findings

### F-1. Scene-header emission is not enforced in the Writer prompt contract

- **Severity**: P1
- **Evidence type**: static+live
- **Fix type**: contract-cleanup
- **Anchors**:
  - `modules/domain/agents/chief_writer_prompts.py:132` (scene_breakdown injection as JSON, no header format instruction)
  - `modules/domain/agents/chief_writer_context.py:263` (scene breakdown as raw JSON dump)
  - `modules/core/writer_template.py:115-176` (template generation produces SceneSlot objects not injected into prompt)
- **Run relevance**: Ep1 and Ep2 passed without headers; Ep3 took 5 rounds partly because the validator kept flagging 0/5 scene completeness on headerless manuscripts.
- **Provisional status**: The finding is live and confirmed by artifact evidence. Not provisional.

### F-2. Keyword-window fallback inflates false-positive rate on headerless manuscripts

- **Severity**: P1
- **Evidence type**: static+live
- **Fix type**: contract-cleanup
- **Anchors**:
  - `modules/validation/blocking_validator_scene_checks.py:231-256` (keyword extraction + 500-char window)
  - `modules/validation/blocking_validator_scene_checks.py:179` (50% threshold for REJECT)
- **Run relevance**: All Ep3 rounds 1-4 showed `0/5` even when round 3 manuscript (rejected_best__A.txt) had proper scene headers. The `0/5` on round 3 suggests the candidates presented to the validator were the pre-persistence versions, and the round 3 candidate that was persisted as rejected_best is different from what was checked.
- **Provisional status**: Confirmed by artifact + console evidence. The header regex path works correctly when headers exist; the residual issue is in the fallback and in Writer prompt enforcement.

### F-3. Retry directive chain grows without bound and replays stale round 1 context

- **Severity**: P1
- **Evidence type**: static+live
- **Fix type**: contract-cleanup
- **Anchors**:
  - `modules/core/stage4_interview_round.py:647-670` (retry_directives join with no dedup)
  - `modules/core/stage4_interview_round.py:420` (`_compact_text` with `limit=None`)
- **Run relevance**: Console rounds 3-4 show the full R0+R1+R2 feedback chain being replayed, including manuscript excerpts and stale contradiction context from round 1. Fix Pack patch_targets was empty on rounds 3-4 (console lines 901, 1061).
- **Provisional status**: Confirmed by console evidence.

### F-4. CONDITIONAL_PASS downstream recognition gap

- **Severity**: P1
- **Evidence type**: static-only
- **Fix type**: contract-cleanup
- **Anchors**:
  - `modules/domain/agents/director_ensemble.py:1187-1204`
  - `modules/core/stage4_interview_round.py:3808`
- **Run relevance**: Did not trigger in this run. The Director always returned PASS or REJECT. But the structural gap remains.
- **Provisional status**: Static finding, not dependent on run completion.

### F-5. Post-select failure classification is now correct (stale claim correction)

- **Severity**: not a finding -- correction of prior claim
- **Evidence type**: static+live
- **Anchors**:
  - `modules/core/stage4_interview_round.py:3692-3703` (explicit error_category assignment)
- The prior bottleneck plan (section 8, "Bottleneck E") claimed `failure_category = NULL` on post-select rejects. This is now **stale**: the code at lines 3696-3703 explicitly sets `POST_SELECT_CONTINUITY_AND_HISTORY`, `POST_SELECT_CONTINUITY_CONFLICT`, `POST_SELECT_HISTORY_CONFLICT`, or `POST_SELECT_CHECK_ERROR`.

## 6. Stale-vs-Live Corrections

| Prior Claim | Source | Current Status | Evidence |
|---|---|---|---|
| "No opening-anchor packet" | bottleneck plan section 5 | **STALE** -- TF-2 is implemented | `chief_writer_context.py:271-297`, live Ep3 attempt_05 opens at correct location |
| "Stage 4 failure_category = NULL on post-select" | bottleneck plan section 8 | **STALE** -- explicit category assignment landed | `stage4_interview_round.py:3696-3703` |
| "Scene validator is the main problem" | bottleneck plan section 4 | **PARTIALLY STALE** -- header regex path landed, but Writer still does not consistently emit headers | `blocking_validator_scene_checks.py:130-132` landed; Ep1/Ep2 still have no headers |
| "Director PASS and post-select REJECT are split-brain" | bottleneck plan section 6 | **STALE** -- confirmed as designed defense-in-depth | pre-rerun merge audit section 7, N-2 |
| "Blueprint timeline handoff contamination" | bottleneck plan section 5 | **LIVE but partially addressed** -- TF-2 now injects opening anchor, but the underlying `time_flow` field derivation was not checked in this run; Ep3 blueprint still shows a range format |
| "Retry loop degradation" | bottleneck plan section 7 | **LIVE** -- empty patch_targets on rounds 3-4, feedback grows without bound | console lines 901, 1061 |
| "CONDITIONAL_PASS not recognized downstream" | Q3 R2 merge audit | **LIVE** -- code still shows the gap | `director_ensemble.py:1187-1204` |

## 7. Highest-ROI Fixes After Run

### Fix 1. Add explicit scene-header instruction to the Chief Writer prompt

- **Fix type**: contract-cleanup
- **Target**: `modules/domain/agents/chief_writer_prompts.py` and/or `modules/domain/agents/chief_writer_context.py`
- **What**: Add a clear instruction in the Writer prompt that manuscripts MUST use `### 씬 N: [제목]` headers to demarcate scenes when a `scene_breakdown` is provided.
- **Why highest ROI**: This is the single change that would eliminate the `0/5` false positive on rounds 1-2, saving 2-4 retry rounds per episode. The validator header-first path already works correctly; it just needs the Writer to actually produce headers.
- **Blast radius**: Low -- prompt-only change, no runtime logic change.

### Fix 2. Cap and deduplicate retry directives

- **Fix type**: contract-cleanup
- **Target**: `modules/core/stage4_interview_round.py:647-670`
- **What**: Deduplicate repeated feedback across rounds, keep only the latest 2-3 rounds of directives, and cap total retry directive length. Remove stale manuscript excerpts from older rounds.
- **Why second**: Directly reduces the noise-to-signal ratio in later rounds and prevents the feedback section from exceeding the manuscript itself.
- **Blast radius**: Medium -- affects retry behavior, needs careful testing.

### Fix 3. CONDITIONAL_PASS downstream recognition

- **Fix type**: contract-cleanup
- **Target**: `modules/domain/agents/director_ensemble.py:1187-1204` and `modules/core/stage4_interview_round.py:3808`
- **What**: Either (a) add `CONDITIONAL_PASS` to the positive verdict set in `_process_verdict`, or (b) ensure `_apply_ensemble_quality_gates` never leaves `final_verdict` as `CONDITIONAL_PASS` by exhaustively resolving it to PASS or REJECT before returning.
- **Why third**: Structural correctness bug that has not yet caused a live failure but will eventually if the V60.97 swap path triggers with edge-case parameters.
- **Blast radius**: Low -- bounded to verdict resolution logic.

## 8. Confidence And Limits

**Estimated confidence: 95%**

### Basis

- The fresh run reached a user-stopped terminal state, so all evidence from Arc 1 is valid.
- Artifact truth was directly inspected: blueprint JSON, manuscript files for attempts 01/03/05, and final drafts.
- Console transcript was read in full (1234 lines).
- Scene-header regex was independently tested and confirmed to match the expected format.
- Static source was inspected for scene validator, Writer prompt, opening anchor, verdict chain, retry directives, and failure classification.
- Cross-referenced against 3 prior merge audits (pre-rerun, Q1-Q8 R2, bottleneck plan).

### Limits

- DB was not directly queried in this lane (delegated to T2 lane). Claims about DB row content are from prior surveys.
- The run was user-stopped during Arc 2, so no Arc 2+ evidence exists. All findings are from Arc 1 (3 episodes).
- The CONDITIONAL_PASS finding is static-only; it did not trigger in this run.
- The blueprint `time_flow` field derivation was not traced end-to-end from the constraint compiler in this lane. The prior bottleneck plan already covers that path.

### Probable rerun blocker in this lane

**No.** The opening-anchor packet and scene-validator header path both landed. The remaining issues (F-1 through F-4) are quality and efficiency issues that waste rounds but do not prevent episode completion.

### Findings that are only provisional because the run was active

**None.** The run reached user-stopped terminal state before this report was saved. All findings are based on completed evidence.

## 9. 3-Pass Audit Record

### Pass 1. Structure and Scope

- Confirmed this is a T1 lane report, not an execution SSOT or merge audit.
- Bounded scope to runtime/artifact flow: scene validator, Writer prompt, opening anchor, verdict chain, retry directives, artifact truth.
- Excluded DB/JSONL/session-logger detail (T2 lane) and config/bootstrap/test surfaces (T3 lane).

### Pass 2. Evidence and Consistency

- Confirmed the scene-header regex matches the actual manuscript format by independent test.
- Confirmed attempt_01 has no scene headers, attempt_03 has headers, attempt_05 has headers.
- Confirmed the opening-anchor code is live at `chief_writer_context.py:271-297`.
- Confirmed post-select failure classification code is live at `stage4_interview_round.py:3696-3703`.
- Cross-checked all stale-vs-live claims against current source.

### Pass 3. Execution and Readability

- Reduced findings to 4 actionable items plus 1 stale-claim correction.
- Ranked the top 3 fixes by ROI.
- Stated rerun blocker assessment explicitly.
- Kept the report within the required 8-section structure.
