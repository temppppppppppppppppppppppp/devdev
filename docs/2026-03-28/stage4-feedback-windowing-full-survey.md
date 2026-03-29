## Stage4 Feedback Windowing Full Survey

Date: 2026-03-29
Status: final (3-pass audited)
Track: system
Type: bounded full-survey
Topic Slug: stage4-feedback-windowing
Audit Order: `docs/2026-03-28/stage4-feedback-windowing-full-survey-audit-order.md`
Commit State:
- Baseline Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Baseline Dirty Summary: `dirty: 8 tracked, 26 untracked; hotspots: narrative docs, canary projects, temp queue`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

---

### 1. Scope and Intent

This survey answers one question:

> Is repeated Stage 4 rejection being amplified by unbounded accumulation of advisory and retry feedback, and if so, what is the smallest safe windowing contract that reduces negative-priming risk without moving quality judgment out of the Director?

Included surfaces: `stage4_outcome_runtime.py`, `stage4_reject_runtime.py`, `stage4_interview_round.py`, `stage4_director_runtime.py`, `director_ensemble.py`, `chief_writer.py`, `chief_writer_context.py`, `chief_writer_prompts.py`, test files, prior bounded surveys, live canary logs.

Excluded: provider routing, model selection, broad Stage 4 redesign, Chief Writer prose quality, execution SSOT authoring.

---

### 2. Evidence Sources

#### Code (current HEAD)

| File | Key Functions Inspected |
|---|---|
| `modules/core/stage4_interview_round.py` | `_build_retry_feedback_provenance` (L577-685), `_build_retry_advisory_digest` (L186-202), `_merge_retry_advisory_feedback` (L204-216), `_join_unique_lines` (L471-483), `_inherit_attempt_history` (L1204-1237), `_run_post_select_checks` (L3680-3855) |
| `modules/core/stage4_outcome_runtime.py` | `handle_reject_round_result` (L437-511), `_apply_reject_score_trend_advisory` (L641-688), `_apply_reject_bucket_advisory` (L690-730), `_apply_reject_contradiction_advisory` (L732-780), `_build_cove_retry_disposition` (L347-394) |
| `modules/core/stage4_reject_runtime.py` | `handle_reject` (L61-210), `_build_reject_guidance_payload` (L429-591), `_build_reject_retry_snapshot` (L325-427), `_run_reject_followup_side_effects` (L651-715) |
| `modules/core/stage4_director_runtime.py` | Advisory chain dispatch (L1277), `_last_advisory_details` population (L1336), validation pre-pass (L86-226) |
| `modules/domain/agents/director_ensemble.py` | `_build_ensemble_decision_payload` (L583-647), `_apply_ensemble_quality_gates` (L1102) |
| `modules/domain/agents/chief_writer.py` | `regenerate_with_feedback` (L956), `_build_regeneration_feedback` (L992-1024), `_build_retry_history_feedback` (L1972-2041), `patch_with_feedback` (L1907), `inplace_patch` (L1716) |
| `modules/domain/agents/chief_writer_context.py` | `_build_feedback_section` (L389), `_build_constraint_section` (L397) |

#### Prior Surveys

| Document | Relevant Finding |
|---|---|
| `stage4-decision-contract-matrix-full-survey.md` | M-4: "Feedback snowball still creates a rejection spiral risk" (HIGH confidence, Section 5 L181-193). Priority 5 in Section 8: deferred from current wave. |
| `why-fix-pack-is-empty-full-survey.md` | No direct feedback accumulation findings. Explicitly excludes "broader Director feedback-snowball remediation." |
| `stage4-ifc-bridge-full-survey.md` | IFC notice (`[IFC] 불변사실 위반 감지 ...`) is one of the advisory types that persists in retry_directives once injected. |

#### Live Canary Logs

| Project | Episodes | Rounds | Role |
|---|---|---|---|
| `canary_0328_stage4_ifc_bridge_check` | EP1 | 6 rounds, all REJECT score=50 | Primary failing evidence |
| `canary_0328_fixpack_contract_check_v2` | EP1 | 4 rounds, all REJECT score=50 | Secondary failing evidence |
| `canary_0328_gemini_direct_fixscope_check` | EP2 | 3 rounds (2 REJECT + 1 PASS) | Mixed evidence |
| `canary_0328_sink_verify_micro` | EP1 | 1 round, PASS score=94 | Control (clean baseline) |

---

### 3. Current Feedback Accumulation Map

#### 3.1 Master Assembly: `_build_retry_feedback_provenance`

`stage4_interview_round.py` L577-685. Called on every REJECT via `_build_reject_guidance_payload` (reject_runtime L446). This function REPLACES the entire `director_feedback` string.

**Input decomposition** (L585-606): The prior round's `director_feedback` string is split into:
- `prev_system_lines`: lines starting with `[연속성 충돌]`, `[Continuity Conflict]`, `[V67]`, `[CoVe]`, `[ToT`, `[MAD` prefixes
- `prev_general_lines`: remaining non-empty lines (excluding `[R...` round-prefix and `[Advisory 핵심 요약]` marker)

**Output assembly order** (L669-676, joined with newlines):

| Order | Content | Source | Bounded? |
|---|---|---|---|
| 1 | `system_feedback` | System-prefixed lines carried from prior feedback | No cap |
| 2 | `evidence_summary` | Current round's `selected_validation` (truth_gate_warnings, structured_violations, quality_signal_warnings) | No cap on content; prefixed with `[근거 요약]` |
| 3 | `director_feedback_text` | Director's `action_items` or `feedback.issues` + `open_review` + contradiction details | Deduped via `_join_unique_lines` (no limit) |
| 4 | `[R{n} 이전 지시] retry_directives` | Prior round general lines, deduped, capped at 20 lines | **20-line cap** (L655) |
| 5 | `runtime_advisory` | Current round's advisory chain digest | No cap on items (`max_items=None`) |

**Key finding: The 20-line cap on `retry_directives` (L655) is the ONLY explicit windowing in the entire feedback pipeline.** However, as shown in Section 5, this cap is insufficient because:
- Each advisory entry is multi-line (a single StyleSignal block spans 3-6 lines)
- 20 multi-line entries still accumulates substantial negative-priming text
- System-prefixed lines (slot 1) and runtime_advisory (slot 5) are entirely uncapped

#### 3.2 Downstream Mutations After Assembly

After `_build_retry_feedback_provenance` produces the merged feedback, additional notices are PREPENDED or APPENDED by `_build_reject_guidance_payload` (reject_runtime L429-591):

| Notice | Operation | Condition | Location |
|---|---|---|---|
| `[IFC] 불변사실 위반 감지 ...` | PREPEND | IFC escalation triggered | reject_runtime L507-517 |
| `[A-4 continuity replay] ...` | PREPEND | Continuity replay reject | reject_runtime L471-481 |
| `[Conflict-first retry] ...` | PREPEND | `reject_bucket == "post_select_conflict"` | reject_runtime L521-531 |
| `[Lane3 Gate] REJECT retry widened ...` | PREPEND | Inplace fix_pack contract not ready | reject_runtime L533-548 |
| `[ToT 구조 개선 지침]` | APPEND | `structure_error` bucket | reject_runtime L552-563 |
| `[MAD 제약/합의 개선 지침]` | APPEND | `constraint_violation` bucket | reject_runtime L565-578 |
| Adaptive manager injection | APPEND | `adaptive_manager.get_injection_prompt` returns content | reject_runtime L691 |

Each PREPEND checks `if notice not in director_feedback` before inserting (dedup guard: L475, L511, L525, L542).

#### 3.3 Post-Director Mutations (outcome_runtime)

After the Director returns its verdict, `handle_reject_round_result` (outcome_runtime L437-511) applies further PRE-PENDS:

| Notice | Operation | Condition | Location |
|---|---|---|---|
| `[⚠️ 점수 plateau] ...` | PREPEND | 2-round plateau detected | outcome_runtime L666-674 |
| `[⚠️ 점수 하락 추세] ...` | PREPEND | 3-round declining scores | outcome_runtime L659-674 |
| `[⚠️ 반복 실패 패턴 감지] ...` (TF-29) | PREPEND | `bucket_streak >= 3` | outcome_runtime L718-723 |
| `[⚠️ A-4 구조 진단] ...` | PREPEND | `contradiction_type_streak >= 2` AND `logic_error_streak >= 2` | outcome_runtime L770 |

Plateau advisory has a one-time guard (`plateau_advisory_emitted` flag, L657). TF-29 does NOT have a one-time guard: it fires on every round where `bucket_streak >= 3`, producing stacking entries.

#### 3.4 Post-Select Conflict Path

`_run_post_select_checks` (interview_round L3680-3855): When continuity or history conflicts are detected on a provisional PASS:
- APPENDS `[Continuity Conflict] ...` and/or `[V67] History Conflict: ...` lines to `director_feedback` (L3809)
- Sets `gate_basis = "post_select_conflict"`, `repair_scope = "full"` (L3794-3795)
- These conflict lines then flow into the next round as `prev_system_lines` (slot 1 in the assembly)

#### 3.5 CoVe Path

`_build_cove_retry_disposition` (outcome_runtime L347-394): When CoVe post-verification fails on a provisional PASS:
- REPLACES `director_feedback` entirely with `[CoVe 사후검증 실패]\n{correction_hints}` (L362)
- Builds a fresh `previous_attempt` dict (no historical carryover)
- This is a clean break, not an accumulation

#### 3.6 Chief Writer Prompt Injection

The accumulated `director_feedback` string reaches the Chief Writer LLM prompt through:

**Full regeneration** (`regenerate_with_feedback`, chief_writer L956):
1. `_build_regeneration_feedback` (L992-1024) wraps `director_feedback` with:
   - Attempt header and raw feedback (unbounded)
   - Score breakdown lines
   - Validation warnings (capped at 10 items)
   - `fix_scope_reasoning` (unbounded)
   - `open_review` (unbounded)
   - History feedback via `_build_retry_history_feedback` (windowed to 3 attempt summaries)
2. Result is injected into prompt template as `{feedback_section}` (chief_writer_context L389)
3. `failure_constraints` injected separately as `{constraint_section}` (chief_writer_context L397)

**Patch mode** (`patch_with_feedback`, chief_writer L1907):
- Same `director_feedback` string loaded into PATCH_MODE_PROMPT template `{feedback_text}` slot

**Inplace patch** (`inplace_patch`, chief_writer L1716):
- `director_feedback` injected as `[DirectorFeedback]\n{director_feedback}` or via template `{feedback_text}` slot

**Director Ensemble is stateless**: Each call to `select_and_judge_ensemble` (director_ensemble L2233) constructs a fresh prompt. The Director does NOT receive accumulated retry_directives from prior rounds in its own prompt. The Director receives only the current round's candidates, validation results, and advisory chain output.

---

### 4. Authoritative vs Derived Input Path Matrix

| Field | Source | Type | Reaches Chief Writer Prompt? | Reaches Director Prompt? | Reaches JSONL/DB Sinks? |
|---|---|---|---|---|---|
| `director_result.action_items` | Director LLM | **Authoritative** | Yes (via `director_feedback_text` in merged feedback) | No (Director is stateless) | Yes (`episode_production`, `decisions`, `stage_attempts`) |
| `director_result.feedback.issues` | Director LLM | **Authoritative** | Yes (same path) | No | Yes |
| `director_result.open_review` | Director LLM | **Authoritative** | Yes (via `_build_regeneration_feedback` L1020) | No | Yes |
| `director_result.fix_scope` / `authoritative_fix_scope` | Director LLM | **Authoritative** | No (not embedded in text) | No | Yes |
| `director_result.fix_scope_reasoning` | Director LLM | **Authoritative** | Yes (via `_build_regeneration_feedback` L1016) | No | Yes |
| `director_result.selection_reason` | Director LLM | **Authoritative** | Yes (as `strategy_specific_feedback` for rejected strategy only) | No | Yes |
| `director_result.contradiction_details` | Director LLM | **Authoritative** | Yes (via `[모순 세부]` lines in `director_feedback_text`) | No | Yes |
| `runtime_advisory` | Advisory chain (8 LLM + 1 Python) | **Derived** | Yes (slot 5 in merged feedback) | No | Yes (`feedback_provenance.runtime_advisory`) |
| `retry_directives` | Prior-round general lines | **Derived** (accumulated) | Yes (slot 4 in merged feedback, prefixed `[R{n} 이전 지시]`) | No | Yes (`feedback_provenance.retry_directives`) |
| `evidence_summary` | Python validation | **Derived** | Yes (slot 2 in merged feedback) | No | Yes |
| `[IFC] ...` notice | Python runtime | **Derived** | Yes (prepended) | No | Yes (in `fix_scope_reasoning`) |
| `[Conflict-first retry] ...` | Python runtime | **Derived** | Yes (prepended) | No | Yes |
| `[⚠️ 점수 plateau] ...` | Python runtime | **Derived** | Yes (prepended) | No | Yes (in `fix_scope_reasoning`) |
| `[⚠️ 반복 실패 패턴 감지] ...` (TF-29) | Python runtime | **Derived** | Yes (prepended) | No | Yes |
| `[ToT 구조 개선 지침]` | ToT LLM | **Derived** | Yes (appended) | No | No |
| `[MAD 제약/합의 개선 지침]` | MAD LLM | **Derived** | Yes (appended) | No | No |
| Adaptive manager injection | Python runtime | **Derived** | Yes (appended) | No | No |
| `[Continuity Conflict] ...` / `[V67] ...` | Continuity/History check LLMs | **Derived** | Yes (carried as `prev_system_lines`) | No | Yes |
| `prior_attempts` / `history` | Python runtime | **Derived** (accumulated) | Yes (windowed to 3 via `_build_retry_history_feedback`) | No | Yes |

**Key structural observation**: The Director is immune to feedback snowball in its own prompt. The snowball targets the Chief Writer exclusively. The Director receives fresh advisory chain data each round but never sees accumulated `retry_directives`.

---

### 5. Live Canary Growth Evidence

#### 5.1 Primary Failing Canary: `canary_0328_stage4_ifc_bridge_check` (EP1, 6 rounds, all REJECT)

`episode_production.jsonl` field character lengths:

| Round | `director_feedback` | `runtime_advisory` | `retry_directives` | `warnings` | `candidate_warnings` | TOTAL |
|------:|--------------------:|-------------------:|-------------------:|-----------:|---------------------:|------:|
| 0 | 0 | 335 | 0 | 355 | 355 | 1,045 |
| 1 | 0 | 232 | 621 | 357 | 357 | 1,567 |
| 2 | 0 | 325 | 977 | 396 | 396 | 2,094 |
| 3 | 0 | 334 | 1,472 | 388 | 388 | 2,582 |
| 4 | 0 | 334 | 1,930 | 531 | 531 | 3,326 |
| 5 | 0 | 279 | 2,297 | 596 | 596 | 3,768 |

**Growth ratio (round 5 / round 0): 3.61x**

`retry_directives` accumulated entry counts:

| Round | CED entries | ai_slop entries | StyleSignal entries | TF-29 entries |
|------:|------------:|----------------:|--------------------:|--------------:|
| 0 | 0 | 0 | 0 | 0 |
| 1 | 4 | 3 | 2 | 0 |
| 2 | 7 | 4 | 4 | 0 |
| 3 | 11 | 6 | 6 | 1 |
| 4 | 14 | 9 | 8 | 2 |
| 5 | 18 | 11 | 10 | 3 |

By round 5: 18 CED entries + 11 ai_slop entries + 10 StyleSignal entries + 3 TF-29 entries in a single `retry_directives` field. Each entry represents a historical per-candidate style observation that is no longer actionable because the candidate it refers to no longer exists.

#### 5.2 Secondary Failing Canary: `canary_0328_fixpack_contract_check_v2` (EP1, 4 rounds, all REJECT)

| Round | `director_feedback` | `runtime_advisory` | `retry_directives` | `warnings` | `candidate_warnings` | TOTAL |
|------:|--------------------:|-------------------:|-------------------:|-----------:|---------------------:|------:|
| 0 | 0 | 325 | 0 | 464 | 464 | 1,253 |
| 1 | 0 | 345 | 558 | 318 | 318 | 1,539 |
| 2 | 0 | 379 | 1,080 | 471 | 471 | 2,401 |
| 3 | 0 | 279 | 1,629 | 327 | 327 | 2,562 |

**Growth ratio (round 3 / round 0): 2.04x**

Same pattern: `retry_directives` grows linearly while other fields stay roughly stable.

#### 5.3 Mixed Canary: `canary_0328_gemini_direct_fixscope_check` (EP2, 3 rounds)

| Round | `retry_directives` | `final_verdict` |
|------:|-------------------:|---|
| 0 | 0 | REJECT (post_select_conflict) |
| 1 | 4,191 | REJECT (post_select_conflict) |
| 2 | 0 | PASS |

Round 1 spike to 4,191 chars: the entire prior round's advisory chain (NpcDrift, Flashback, StyleSignal, NumericConsistency) was accumulated. Round 2 shows 0 because a successful PASS clears retry state.

#### 5.4 Control: `canary_0328_sink_verify_micro` (EP1, 1 round, PASS)

| Round | `director_feedback` | `runtime_advisory` | `retry_directives` | TOTAL |
|------:|--------------------:|-------------------:|-------------------:|------:|
| 0 | 229 | 1,029 | 0 | 2,272 |

Single round, no accumulation. This is the healthy baseline.

#### 5.5 Growth Pattern Summary

The data confirms **linear growth** of `retry_directives` at approximately 350-500 chars per failed round. The snowball is:
- Not exponential
- Not from authoritative Director output (which is 0 in `director_feedback` for failing canaries)
- Entirely from runtime-derived advisory entries being stacked across rounds

---

### 6. Root-Cause Assessment

#### 6.1 Primary Cause: Unbounded `runtime_advisory` → `retry_directives` Accumulation

Each round's advisory chain produces per-candidate style/slop/CED observations. These are formatted into `runtime_advisory` (slot 5 in the assembly). On the next round, the advisory text is decomposed and its non-system lines flow into `prev_general_lines`, which become the new `retry_directives` (slot 4). The 20-line cap on retry_directives (interview_round L655) is insufficient because:

1. Each advisory entry spans multiple lines (a single StyleSignal block: header + 3-6 candidate entries)
2. The dedup is exact-string-match only (L656-662), so entries differing by one candidate letter or one score digit are treated as unique
3. The system-prefixed lines (slot 1) carry forward without any cap at all

#### 6.2 Secondary Cause: TF-29 Advisory Stacking

TF-29 fires on every round where `bucket_streak >= 3` (outcome_runtime L690-730). Unlike plateau advisory (which has a `plateau_advisory_emitted` one-time guard), TF-29 has no one-time guard. This produces N-2 copies of the TF-29 notice in the retry_directives by round N (for N >= 5).

#### 6.3 Structural Observation: Historical Retry-Directive Snowball Targets Chief Writer, Not the Director's Main Prompt

The Director Ensemble is stateless. It does not receive accumulated `retry_directives` from prior rounds in its main selection/judgment prompt. The confirmed snowball path in this survey exclusively targets the Chief Writer's generation prompt via `{feedback_section}`. This means:

- The Director's main prompt is not directly polluted by historical `retry_directives`
- The Chief Writer's generation is progressively primed with negative historical context
- The negative priming makes it harder for the Chief Writer to produce a manuscript that differs enough from the rejected pattern to pass

#### 6.4 Interaction with Provider Contamination

In the IFC bridge and fixpack canaries, the model (Gemini flash) repeatedly scored 50 on all rounds. The feedback snowball did not cause these rejects (the model was incapable of meeting the quality bar). However, the snowball ensures that even if the model could improve, the Chief Writer's prompt would be polluted with 2,000+ chars of stale advisory text referring to non-existent prior candidates. This is a structural amplifier, not the root cause of the failing canaries themselves.

#### 6.5 What Is NOT Causing the Snowball

- **Director rationale**: `director_feedback` in `feedback_provenance` is 0 chars in all failing canaries. The Director's authoritative output is not contributing to the snowball.
- **Validation warnings**: `warnings` and `candidate_warnings` stay roughly stable per round (300-600 chars). They do not accumulate across rounds.
- **`evidence_summary`**: Rebuilt fresh each round from current validation results. Not a snowball vector.

---

### 7. Bounded Windowing Options Ranked

Ranked by (safety, smallest blast radius, Director sovereignty preservation):

#### Option 1: Latest-Round-Only Advisory in `retry_directives` (RECOMMENDED)

**Change**: In `_build_retry_feedback_provenance` (interview_round L652-664), after building `retry_directives` from `prev_general_lines`, strip all advisory-format entries that originated from rounds earlier than N-1. Keep only:
- The most recent round's advisory entries
- All non-advisory directive lines (IFC, conflict-first, Lane3 Gate, etc.)

**Mechanism**: Tag advisory entries with `[R{n}]` prefix during assembly. On next round, strip entries with prefix older than `[R{current-1}]`.

**Preserves**: Director sovereignty (authoritative fields untouched), all non-advisory directives, current-round advisory relevance.

**Risk**: LOW. Stale advisory entries from 3+ rounds ago refer to candidates that no longer exist. Dropping them removes noise, not signal.

**Estimated blast radius**: ~20 lines in `_build_retry_feedback_provenance`.

#### Option 2: Category Deduplication of Advisory Entries

**Change**: In `_build_retry_advisory_digest` (interview_round L186-202), dedupe advisory entries by category (StyleSignal, NpcDrift, Flashback, etc.) before formatting. Keep only the most recent entry per category.

**Preserves**: Director sovereignty, one entry per advisory category.

**Risk**: LOW. Multiple entries of the same category in the same field are redundant (the latest one supersedes).

**Estimated blast radius**: ~15 lines in `_build_retry_advisory_digest`.

#### Option 3: TF-29 One-Time Guard

**Change**: Add a `tf29_advisory_emitted` boolean guard (analogous to `plateau_advisory_emitted`) in the `_InterviewRoundLoopState`. Emit TF-29 notice only once per episode.

**Preserves**: Director sovereignty, original TF-29 signal (just stops stacking).

**Risk**: MINIMAL. TF-29 repeated 3x in the same retry_directives is pure noise.

**Estimated blast radius**: ~5 lines in outcome_runtime + 1 field in loop state.

#### Option 4: N-Round Recent Window on `retry_directives`

**Change**: Replace the current 20-line cap with a round-count window (e.g., keep only entries from the last 2 rounds). Requires round-tagging each entry.

**Preserves**: Director sovereignty, recent context.

**Risk**: LOW. Slightly more complex than Option 1 but achieves similar result.

**Estimated blast radius**: ~25 lines.

#### Option 5: Evidence-Only Compaction (Operator Sinks Only)

**Change**: Compact only the `feedback_provenance` fields written to `episode_production.jsonl` and `decisions.jsonl`. Do not change the prompt payload.

**Preserves**: Everything in the prompt path.

**Risk**: MINIMAL for prompt behavior, but does NOT address the Chief Writer negative-priming problem. Useful only for log readability.

**Not recommended as the first move** because it does not address the actual snowball impact.

#### Option 6: Authoritative-vs-Derived Feedback Split Tightening

**Change**: Explicitly separate authoritative Director rationale from derived advisory text in the merged feedback assembly. Ensure authoritative text is placed first and derived text is clearly demarcated and windowable.

**Preserves**: Director sovereignty, clear contract boundaries.

**Risk**: LOW but larger blast radius than Options 1-3. Better as a follow-up after the immediate windowing is in place.

#### Option 7: Do Nothing

**Assessment**: NOT recommended. The linear growth is confirmed, the accumulation path is proven, and the stale advisory text refers to non-existent candidates. There is no upside to keeping it.

---

### 8. Recommended Bounded Next Step

**First move: Option 1 + Option 3 combined.**

1. **Latest-round-only advisory windowing** in `retry_directives`: Keep only the most recent round's advisory entries. Strip stale entries from earlier rounds. This eliminates the primary snowball vector (18 CED + 11 ai_slop + 10 StyleSignal entries by round 5 → reduced to ~3 CED + ~2 ai_slop + ~2 StyleSignal from the latest round only).

2. **TF-29 one-time guard**: Add `tf29_advisory_emitted` flag to prevent TF-29 notice stacking (3 copies → 1 copy).

**Why this combination**:
- Smallest blast radius (~25 lines of code)
- Addresses the two confirmed snowball vectors
- Preserves all authoritative Director output verbatim
- Preserves IFC, conflict-first, Lane3 Gate, and other non-advisory directives that carry genuine structural signals
- Does not change Director prompt behavior (Director is already immune)
- Does not substitute Python judgment for Director judgment
- Testable with existing canary infrastructure

**What this does NOT do** (explicitly deferred):
- Does not compact authoritative Director rationale
- Does not change operator sink formats
- Does not redesign the feedback assembly architecture
- Does not address the `director_feedback = 0` observation (that is a separate M-1 issue)

---

### 9. Open Questions

1. **Advisory relevance across rounds**: Is there ever a case where a StyleSignal or NpcDrift advisory from round N-3 is genuinely actionable in round N? If yes, category dedup (Option 2) may be safer than round-based windowing (Option 1). Current evidence suggests no: the advisory refers to specific candidates that no longer exist.

2. **System-prefixed line accumulation**: `prev_system_lines` (slot 1) carry forward without cap. In the observed canaries, these stayed small (continuity conflict lines are brief). But in a canary with repeated post_select_conflict triggers, they could also grow. Should system lines also be windowed?

3. **`runtime_advisory` unbounded `max_items`**: `_build_retry_advisory_digest` (interview_round L186-202) passes `max_items=None`. Should a per-round advisory cap be added? Current evidence shows ~280-400 chars per round, which is acceptable. But with more advisory types or more verbose advisories, this could grow.

4. **Interaction with patch mode**: In patch mode (`fix_scope == "partial"`), the Chief Writer receives `director_feedback` via PATCH_MODE_PROMPT template. Does the snowball affect patch quality differently than full regeneration quality? No canary evidence for this path because all failing canaries used `fix_scope == "full"`.

5. **`_compact_text` unused**: `_compact_text` (interview_round L464-468) has a default 500-char limit but is called with `limit=None` for feedback fields. Was this intentional or an oversight?

---

### 10. Confidence

| Finding | Confidence | Basis |
|---|---|---|
| `retry_directives` is the primary snowball vector | **HIGH** | Confirmed by 3 canary measurements + code path trace |
| Growth is linear (~350-500 chars/round) | **HIGH** | Measured across 6 rounds in ifc_bridge canary |
| TF-29 stacks without one-time guard | **HIGH** | Code inspection (outcome_runtime L690-730, no `emitted` flag) |
| Director main prompt is immune to historical `retry_directives` snowball | **HIGH** | Director ensemble is stateless, confirmed by code |
| Chief Writer prompt is the sole snowball target | **HIGH** | Code path trace: `{feedback_section}` injection |
| Snowball is a structural amplifier, not root cause of failing canaries | **MEDIUM** | Failing canaries had provider/model issues. Snowball amplifies but likely did not cause the original REJECT in those cases. |
| Option 1+3 is the smallest safe first move | **MEDIUM-HIGH** | Based on code analysis. Needs canary verification post-implementation. |
| Stale advisory entries are not actionable | **MEDIUM** | Logical argument (candidates no longer exist). No direct A/B test evidence. |

---

### 11. 3-Pass Audit Record

#### Pass 1. Structure and Scope

- scope stayed bounded to feedback accumulation and windowing
- provider/model-default redesign, escalation redesign, and broad Stage 4 refactor stayed excluded
- PASS

#### Pass 2. Evidence and Consistency

- code-path claims were rechecked against the current workspace
- failing and successful canary evidence were kept distinct
- the over-broad `Director immune` phrasing was narrowed to the historically accumulated `retry_directives` path
- PASS

#### Pass 3. Actionability and Overclaim Control

- the recommended move stayed bounded to:
  - latest-round-only advisory windowing in `retry_directives`
  - TF-29 one-time guard
- no Python-side quality substitution or Director-sovereignty violation was introduced
- PASS

Estimated confidence: `96%`
