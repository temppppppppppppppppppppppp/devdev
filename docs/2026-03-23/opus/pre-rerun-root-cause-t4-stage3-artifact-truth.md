Date: 2026-03-23
Status: final
Document Type: pre-rerun root-cause deep survey report
Terminal: T4
Focus: Stage 3 blueprint artifact and DB truth
Canonical Path: `docs/2026-03-23/opus/pre-rerun-root-cause-t4-stage3-artifact-truth.md`
Evidence Path: `docs/2026-03-23/opus/pre-rerun-root-cause-t4-stage3-artifact-evidence.md`
Source Order: `docs/2026-03-23/opus-pre-rerun-root-cause-deep-survey-order.md`
Commit State:
- Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Baseline Dirty Summary: dirty workspace allowed; Stage 3 orchestrator and director_ensemble touched

---

## 1. Executive Summary

Stage 3 blueprint artifacts for the 0_0323 project (Arc 1, ep 1-4) are structurally sound and narratively coherent. All 4 blueprints exist on disk, decode cleanly, and match their DB content hashes. The integrated scenarios flow logically from the Stage 2 arc plan. No artifact corruption, truncation, or content-level contradiction was found.

However, the **DB metadata layer** has significant gaps that impair post-run diagnosis:

1. **stage_attempts metadata absence** (P1): Stage 3 `save_stage_attempt()` does not pass `selection_reason`, `verdict_reason`, `open_review`, `score_breakdown`, `fix_scope_reasoning`, or `initial_verdict`. All these fields are empty/null for every Stage 3 record, while Stage 4 populates them fully.
2. **attempt_raw_rationale absence** (P1): Stage 3 saves zero entries to `attempt_raw_rationale`. Stage 4 saves 12. Director thinking and ensemble reasoning for blueprint selections are not persisted.
3. **Blueprint scene-level goal/summary empty** (P1): At least ep1 and ep3 blueprint JSON artifacts have empty `goal` and `summary` fields for all scenes, despite the prevalidation warning flagging this. Director still passed them.

These DB gaps are **not root-causal for the Arc 1 Episode 3 Stage 4 failure** (the blueprints themselves are usable). They are, however, root-causal for the inability to diagnose Stage 3 decisions post-run, and the empty scene goals/summaries reduce Stage 4 ChiefWriter's granularity signal.

**Fresh-run-before-fix allowed: yes** — Stage 3 artifact quality is adequate; the DB metadata gaps are observability issues, not decision-path correctness issues.

---

## 2. Current Ownership / Flow Map

### Blueprint Production Pipeline

```
Stage3Orchestrator._run_single_episode_blueprint()
  -> ThreePhaseBlueprintGenerator (3 strategies in parallel)
     -> blueprint_ensemble_generator (3 LLM calls)
  -> BlueprintEnsemble.generate_ensemble()
     -> qualified_candidates filtering
     -> qualified[0] selection (P0 from gen-coherence report)
  -> Director audit (LLM call)
     -> PASS / PASS_WITH_FIX / REJECT
  -> If PASS_WITH_FIX: fix round (1 LLM call) + Director re-audit
  -> save_stage_attempt() -> stage_attempts (metadata sparse)
  -> save_director_selection() -> director_selections (metadata populated)
  -> save blueprint artifact -> logs/artifacts/stage3/ep_NNNN/
  -> save blueprint text -> plans/blueprints/blueprint_NNNN.txt
  -> save blueprint DB row -> blueprints table
```

### DB Save Ownership

| Sink | Owner | Fields Populated |
|------|-------|-----------------|
| `stage_attempts` | `stage3_orchestrator.py:1858-1874` | stage, verdict, attempt_num, ep_num, arc_num, score, model, session_id, attempt_key, prompt_version, duration_ms, advisory_flags, candidate_key, content_hash, artifact_path |
| `director_selections` | `stage3_orchestrator.py:1875-1879` | selection_reason, verdict_reason, pre_firewall_score, firewall_triggered, firewall_reason, director_thinking, advisory_warnings, + common fields |
| `blueprints` | blueprint save path | ep_num, data (JSON) |
| `attempt_raw_rationale` | NOT saved for Stage 3 | (no records) |

---

## 3. Focus-Scope Findings

### F-1. stage_attempts metadata parity gap (P1)

**File**: `modules/core/stage3_orchestrator.py:1858-1874` (PASS path), `L2624-2642` (REJECT path)

**Evidence**:
- DB query: `stage_attempts` Stage 3 records have `sr_len=0, vr_len=0, or_len=0, sb_len=None` for all 4 episodes
- DB query: `stage_attempts` Stage 4 records have `sr_len=147-239, vr_len=76-239, or_len=80-237, sb_len=119-120`
- Source: PASS path `save_stage_attempt()` at L1858 passes 14 keyword args, omitting `selection_reason`, `verdict_reason`, `open_review`, `score_breakdown`, `fix_scope_reasoning`, `initial_verdict`
- Contrast: `save_director_selection()` at L1877 passes `selection_kwargs` which DOES contain `selection_reason` and `verdict_reason`

**Impact**: Post-run query of `stage_attempts WHERE stage=3` cannot answer "why was this blueprint selected?" or "what did the Director think?". The data exists in `director_selections` but the two tables are not cross-referenced in standard diagnostic queries.

**Fix type**: `contract-cleanup`

### F-2. attempt_raw_rationale absence for Stage 3 (P1)

**Evidence**:
- DB query: `SELECT stage, COUNT(*) FROM attempt_raw_rationale GROUP BY stage` returns only `stage=4: 12`
- No Stage 3 entries exist

**Impact**: Director thinking, ensemble selection reasoning, and detailed per-candidate comparison for Stage 3 are not persisted in the raw rationale table. Only the compact `selection_reason` in `director_selections` survives.

**Fix type**: `contract-cleanup`

### F-3. Blueprint scene goal/summary empty (P1)

**Evidence**:
- `projects/0_0323/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__action_focused.json` — all 5 scenes have `"goal": ""` and `"summary": ""`
- Same artifact's `_ensemble_meta.python_warnings` records: `"씬 구조 미비: 5/5개 씬에 goal/summary 없음"` (severity: MINOR)
- `plans/blueprints/blueprint_0003.txt` confirms: all scene entries show `goal:` and `summary:` as empty
- ep1 artifact (`emotion_focused.json`) has the same pattern: empty `characters`, `key_events`, `content` fields for scenes

**Impact**: ChiefWriter receives blueprints with a detailed `integrated_scenario` but no per-scene writing targets. The writer must infer scene boundaries and goals from the scenario narrative alone. This reduces structural precision but does not prevent manuscript generation.

**Root-cause context**: The LLM generates scene `title`, `location`, `tension_level`, and `type` but leaves structured detail fields empty. The prevalidation flags this as MINOR, and the Director does not penalize it because the integrated_scenario is complete.

**Fix type**: `contract-cleanup` (either prompt the LLM to populate scene goals, or raise the prevalidation severity to force retry)

### F-4. Ep1 two-attempt pattern with ensemble collapse (P2)

**Evidence**:
- `director_selections` ep1: `round_num=2`, `candidate_count=1`, `selected_strategy=emotion_focused`
- `stage_attempts` ep1: `attempt_num=2`
- LLM calls: 10 calls for ep1 (4 generators + 6 directors) vs 4-7 calls for ep2-4
- Artifact directory: only `attempt_02` exists for ep1; `attempt_01` artifacts not preserved

**Impact**: First attempt got PASS_WITH_FIX, fix round executed, but then a full second attempt was needed with only 1 candidate (ensemble collapsed). Not root-causal for ep3 failure.

**Fix type**: `observability-only`

### F-5. Pass rate display 83.3% (P3)

**Evidence**: Console line 458: "통과율: 83.3%". 4 successes out of 4 episodes should be 100%. The denominator includes LLM-level attempts not episode-level attempts.

**Fix type**: `contract-cleanup` (already identified in fresh-run-3pass-audit P3-2)

### F-6. Continuity pin unresolved for ep4 (P2)

**Evidence**: `runtime_audit.jsonl` entry — `continuity_pin_unresolved` for ep4, proper_noun_pin "SW인베스트먼트" expected but not matched in blueprint text.

**Impact**: Advisory-only warning. Did not block blueprint PASS. May propagate to Stage 4 as a continuity gap if the entity name form changes between blueprint and manuscript.

**Fix type**: `observability-only`

### F-7. quality_risk=True for all 4 episodes (P3)

**Evidence**: All `director_selections` Stage 3 records show `quality_risk: True` in advisory_warnings.

**Impact**: The flag has no discriminatory value for Stage 3 in this run. It may always be set due to the prevalidation warnings (NPC fidelity + scene structure) which are common.

**Fix type**: `comment-only`

### F-8. DB encoding display issue (non-issue)

**Evidence**: Raw bytes from `director_selections` `selection_reason` for ep2-4 are valid UTF-8 Korean (`\xec\xba\x90\xeb\xa6\xad\xed\x84\xb0` = "캐릭터"). Terminal display shows mojibake due to Windows cp949 codec.

**Impact**: Data integrity is fine. Operator console visibility is impaired on Windows terminals that use cp949.

**Fix type**: `ignore` (terminal encoding configuration, not a code issue)

---

## 4. Root-Cause Relevance

### Root-Causal for Post-Run Diagnosis Failure (Indirect)

| Finding | Root-Causal? | Why |
|---------|-------------|-----|
| F-1 stage_attempts metadata gap | YES (for diagnosis) | Without selection_reason/verdict_reason in stage_attempts, post-run queries cannot explain Stage 3 decisions without joining to director_selections |
| F-2 attempt_raw_rationale absence | YES (for diagnosis) | Director thinking for Stage 3 is lost entirely |
| F-3 empty scene goals/summaries | CONTRIBUTING | Reduces Stage 4 ChiefWriter signal, but integrated_scenario compensates |

### Root-Causal for Arc 1 Episode 3 Stage 4 Failure

| Finding | Root-Causal? | Why |
|---------|-------------|-----|
| F-1 | NO | Metadata gap doesn't affect blueprint content quality |
| F-2 | NO | Rationale absence doesn't affect blueprint content quality |
| F-3 | POSSIBLY CONTRIBUTING | Empty scene goals mean ChiefWriter has less structural guidance, but the integrated_scenario for ep3 is complete and detailed |
| F-4 | NO | Ep1-specific issue, ep3 had 3 candidates and clean selection |
| F-5 | NO | Display bug only |
| F-6 | NO | Ep4-specific, and advisory-only |

**Assessment**: Stage 3 blueprint artifacts are NOT the primary root cause of Arc 1 Episode 3 Stage 4 divergence. The blueprints are narratively sound and consistent with the arc plan. The root cause more likely lies in Stage 4 write/fix/verdict chain (T5/T7 scope) or in context/retrieval degradation (T9 scope).

---

## 5. Quick Wins

| # | Target | Change | Expected Benefit | Fix Type |
|---|--------|--------|-----------------|----------|
| QW-1 | `stage3_orchestrator.py:1858-1874` | Add `selection_reason`, `verdict_reason`, `open_review`, `score_breakdown` from director result dict to `save_stage_attempt()` call | Stage 3 post-run diagnosis via stage_attempts becomes possible | contract-cleanup |
| QW-2 | `stage3_orchestrator.py` (PASS + REJECT paths) | Add `attempt_raw_rationale` save for Stage 3, matching Stage 4 pattern | Director thinking for blueprint selections persisted | contract-cleanup |
| QW-3 | Blueprint prevalidation | Raise "씬 구조 미비" severity from MINOR to HIGH when scene_count >= 4 and 0 goals populated | Force LLM retry to populate scene goals | contract-cleanup |

---

## 6. False Leads / Non-Causes

1. **DB encoding corruption** — CONFIRMED FALSE. Raw bytes are valid UTF-8. Mojibake is Windows terminal cp949 display issue only. Evidence: `sr.encode('utf-8')[:80]` shows correct UTF-8 byte sequences for Korean characters.

2. **Blueprint narrative quality** — CONFIRMED NOT A CAUSE. The ep3 blueprint integrated_scenario (1,375 chars) tells a complete, coherent story of Han Siwoo liquidating personal assets to raise 20 billion KRW seed capital, exactly matching the arc plan's ep3 description. No content-level contradiction with the arc plan.

3. **Arc-to-blueprint continuity gap** — CONFIRMED FALSE. Comparing `arc_001.txt` ep3 ("자산 정리... 20억원의 현금 확보") with `blueprint_0003.txt` ("가족의 감시망 속에서 의심을 사지 않고 하루 만에 20억의 종잣돈을 확보하려는 한시우의 시간 싸움") shows consistent narrative progression. The blueprint elaborates rather than contradicts.

4. **Blueprint context caching failure** — CONFIRMED FALSE. LLM calls show cached_tokens appearing from ep3 onward (2,534 tokens cached). Context caching is functioning.

5. **Blueprint Director verdict inconsistency** — CONFIRMED FALSE. Ep1-3 got PASS_WITH_FIX initially, then PASS after fix rounds. Ep4 got clean PASS. This is normal Director behavior with fix iteration.

---

## 7. Fresh-Run Relevance

**Fresh-run-before-fix allowed: yes**

Stage 3 findings are observability gaps (F-1, F-2) and structural precision issues (F-3), not decision-path correctness bugs. A fresh run will produce functionally equivalent blueprints. The metadata gaps will persist but do not affect blueprint quality.

### Top 3 Highest-ROI Fixes Before Next Rerun

1. **QW-1: Populate stage_attempts metadata for Stage 3** — Low effort, high diagnostic value. Without this, the next rerun's Stage 3 decisions are equally opaque.

2. **QW-2: Save attempt_raw_rationale for Stage 3** — Low effort, captures Director thinking that is currently lost.

3. **QW-3: Enforce scene goal/summary population** — Medium effort, improves Stage 4 ChiefWriter structural precision.

---

## 8. Confidence And Limits

**Estimated confidence: 97%**

### Basis
- All 4 blueprint artifacts (JSON) inspected: structure, encoding, content integrity verified
- All 4 blueprint text files inspected
- `stage_attempts`, `director_selections`, `blueprints`, `attempt_raw_rationale` DB tables fully queried
- `runtime_audit.jsonl` and `decisions.jsonl` Stage 3 entries analyzed
- `llm_calls` for Stage 3 (28 entries) fully analyzed
- `ui_events` for Stage 3 (16 entries) enumerated
- Console output Stage 3 section read and cross-referenced
- Arc plan (`arc_001.txt`) compared with all 4 blueprints for content continuity
- Source code `stage3_orchestrator.py` PASS path (L1858-1874) and REJECT path (L2624-2642) read and analyzed
- DB encoding verified at byte level (valid UTF-8)

### Limits
- Did not inspect all 28 LLM call prompt/response snippets in detail (verified success=1 and verdict for all)
- Did not inspect ep1 attempt_01 artifacts (directory does not exist; only attempt_02 preserved)
- Scene goal/summary emptiness verified for ep1 and ep3 only; ep2 and ep4 not individually verified but pattern is consistent
- Did not trace the `selection_kwargs` construction path from `BlueprintEnsemble` through to `save_director_selection()` to confirm exactly which fields populate `director_selections`
