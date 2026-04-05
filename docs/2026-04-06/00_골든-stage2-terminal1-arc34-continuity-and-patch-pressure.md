# 00_골든 Stage2 Terminal 1: Arc 3/4 Continuity and Patch-Pressure

Date: 2026-04-06
Status: final
Mode: read-only bounded survey
Scope: Arc 3 and Arc 4 from latest `00_골든` Stage2 run (session `20260406_013527`)
Authoritative Sinks:
- `projects/00_골든/logs/session/decisions.jsonl`
- `projects/00_골든/logs/session/ui_events.jsonl`
- `projects/00_골든/logs/runtime_audit.jsonl`
- `projects/00_골든/logs/quality_metrics.jsonl`
- `projects/00_골든/logs/artifacts/stage2/arc_003/attempt_01/final_arc__creative.json`
- `projects/00_골든/logs/artifacts/stage2/arc_004/attempt_01/final_arc__balanced.json`
- `projects/00_골든/plans/arcs/arc_003.txt`
- `projects/00_골든/plans/arcs/arc_004.txt`

---

## Findings First

### F-1. Arc 3 Location Truth Divergence — Generation Drift, Not Sync Drift

**Origin of the split**: The LLM ensemble (arc_ensemble.py) generated Arc 3 with a `tactical_doc` that consistently places the office in **여의도** throughout all 5 episodes. However, the Block 3 treatment source and the auto-corrector produced a different end-location.

**Evidence chain**:

| Surface | Location Value | Source |
|---|---|---|
| tactical_doc (all episodes 12-16) | 서울 여의도, SW인베스트먼트 개인 사무실 | LLM generation |
| selected packet `state_constraints.arc_end_state.location` (pre-autocorrect) | 서울 여의도, SW인베스트먼트 개인 사무실 | LLM generation |
| auto-correct log (runtime_audit L7) | `arc_end_state 위치 동기화: '서울 여의도, SW인베스트먼트 개인 사무실' → '서울 강남, SW인베스트먼트 오피스'` | `stage2_optimizer.py:486` `_sync_final_location()` |
| Director PASS_WITH_FIX reason | "tactical document consistently places the office in '여의도', while the summary block ('Block 3') and Python auto-corrections place it in '강남'" | Director LLM |
| End Location Sync (ui_events L319) | `Arc 3 종료 위치 → 서울 여의도, SW인베스트먼트 개인 사무실` | `stage2_finalizer.py:1313` `_sync_stage2_end_location_contract()` |
| final arc_003.txt Carryover `end_location` | 서울 여의도, SW인베스트먼트 개인 사무실 | finalizer output |
| final arc JSON `joint_docs.final_location` | 서울 여의도, SW인베스트먼트 개인 사무실 | finalizer output |

**Flow reconstruction**:

1. Ensemble generates arc with `joint_docs.final_location = "서울 강남, SW인베스트먼트 오피스"` (the LLM hallucinated or inferred a location upgrade based on narrative context of growing success)
2. `ArcAutoCorrector._sync_final_location()` at `stage2_optimizer.py:486` sees that `arc_end_state.location` ("여의도") differs from `joint_docs.final_location` ("강남") and **syncs arc_end_state toward joint_docs**, writing correction `'서울 여의도 ...' → '서울 강남 ...'`
3. Director catches the discrepancy between tactical_doc (여의도) and the now-강남 end_state, issues PASS_WITH_FIX
4. After fix patch, `_sync_stage2_end_location_contract()` at `stage2_finalizer.py:324` re-resolves the canonical location by preferring the arc_end_state's corrected value, which by this point has been restored to 여의도
5. Final artifacts emit 여의도 consistently

**Verdict**: The location discrepancy is **generation drift** in the ensemble's `joint_docs.final_location` output. The auto-corrector then **propagated** the bad joint_docs value into `arc_end_state`, which the Director caught. The finalizer's second sync pass restored the correct value. The final arc txt is consistent. The issue is that the auto-corrector's sync direction (joint_docs → arc_end_state) trusts the wrong surface when the LLM hallucinated in joint_docs.

**Narrowest owner**: `stage2_optimizer.py` `_sync_final_location()` — its sync direction makes joint_docs authoritative over arc_end_state, but joint_docs is the less constrained LLM output surface.

---

### F-2. Arc 3 Recovery-Scene Omission — Generation Problem, Not Normalization

**Evidence**: Director PASS_WITH_FIX flagged: "The V60.10 STATE LOCK mandates a '회복 장면 필수 (최소 1일)' (mandatory recovery scene), but the tactical document skips the 6-week time gap without explicitly mentioning any recovery, jumping straight into a state of accumulated pressure."

The tactical_doc for Arc 3 opens with: "지난 6주간의 기다림은 정신적 피로를 회복하는 시간이기도 했지만, 동시에 새로운 압박이 쌓이는 시간이었다." — This implicitly references recovery but does not include a dedicated recovery beat.

The `beat_sequence` in the selected packet has no recovery beat entry. All 5 beats are pressure → counterattack → analysis → climax → aftermath.

**Verdict**: The omission is a **generation problem**. The ensemble LLM did not include a recovery beat in its tactical plan. No normalization step removed a recovery beat that was once present. The fix patch instructed adding a brief recovery sentence at the beginning of Episode 12, which was applied advisory-only (patch pressure exceeded).

**Narrowest owner**: `arc_ensemble.py` generation prompts — the constraint compiler (`stage2_optimizer.py` ConstraintCompiler) injected the STATE LOCK mandate, but the ensemble LLM chose to skip it.

---

### F-3. Arc 4 Numeric Arithmetic Drift — Generation Problem

**Evidence from Director PASS_WITH_FIX** (decisions.jsonl L7, ui_events L344-349):

Two arithmetic errors in the ensemble-generated Arc 4:

1. **Episode 21 start-state**: Portfolio position listed as 23억 total, but half-sell yielding 5억 profit (with 7.5억 principal) requires position value of 12.5억, hence total should be 25억 not 23억.
2. **Episode 21 end-state**: Cash should be 28억 (existing 15.5억 + 매도대금 12.5억), but was listed as 27.5억. Total assets should be 40.5억 not 40억.

**Where the error originates**: The selected arc_004 packet (`final_arc__balanced.json`) shows the post-fix values are correct:
- `state_constraints.arc_end_state.capital`: "약 28억원"
- `state_constraints.arc_end_state.total_assets`: "약 40.5억원"
- `investment_calc.final_cash`: 2,800,000,000
- `investment_calc.final_total_assets`: 4,050,000,000

The final arc_004.txt also shows corrected values (총자산 40.5억원, 현금 약 28억).

**Flow**: Ensemble LLM generated arc with arithmetic errors in episode_details and state_constraints → Director caught both with PASS_WITH_FIX → fix patch corrected → Director re-review PASS (score=100) → "Patch pressure exceeded → advisory only, PASS 유지" → finalizer emitted corrected values.

**Verdict**: The arithmetic error is **pure generation drift** in the ensemble LLM. No post-generation normalization introduced the error. The Director successfully caught and patched it before final emission.

**Narrowest owner**: `arc_ensemble.py` generation — the LLM miscalculated. The fix loop in `stage2_finalizer.py` PASS_WITH_FIX mechanism correctly resolved it.

---

### F-4. Arc 4 Location Drift — Same Pattern as Arc 3

**Evidence** (runtime_audit L10):
```
Auto-correct arc 4: arc_end_state 위치 동기화: '서울 여의도, SW인베스트먼트 개인 사무실' → '서울 강남구 테헤란로, SW인베스트먼트 개인 오피스'
```

The ensemble generated Arc 4 with `tactical_doc` placing all episodes in 여의도, but `joint_docs.final_location` as "서울 강남구 테헤란로, SW인베스트먼트 개인 오피스". Same pattern as F-1.

However, unlike Arc 3, the **final arc txt** kept the 강남 end-location:
- arc_004.txt Carryover `end_location`: "서울 강남구 테헤란로, SW인베스트먼트 개인 오피스"
- ui_events L354: "End Location Sync Arc 4 종료 위치 → 서울 강남구 테헤란로, SW인베스트먼트 개인 오피스"

This means the finalizer's `_sync_stage2_end_location_contract()` chose the 강남 value as canonical this time. The Director did not flag this location change (its PASS_WITH_FIX was about arithmetic only).

**Impact**: Arc 4 ends in 강남, but its tactical_doc prose ends in 여의도. The next arc (Arc 5) must start in 강남. This is the **packet-to-txt round-trip inconsistency** described in the 0_0 SSOT appendix §15.1.

**Narrowest owner**: `stage2_optimizer.py` `_sync_final_location()` (same as F-1).

---

### F-5. Persistent Auto-Correct Families Across Arcs 3-5

| Correction Family | Arc 3 | Arc 4 | Arc 5 (att 1) | Arc 5 (att 2) | Owner |
|---|---|---|---|---|---|
| `internal_energy` wuxia field removal | start + end | start + end | start + end | start + end | `stage2_optimizer.py:513` `_strip_wuxia_fields()` |
| `[C-1]` tactical_doc meta term `Arc` → 서사 용어 | — | Yes | Yes | Yes | `stage2_optimizer.py:712` `_sanitize_tactical_meta_terms()` |
| `arc_end_state 위치 동기화` | 여의도→강남 | 여의도→강남 테헤란로 | 강남→강남 (minor) | — | `stage2_optimizer.py:486` `_sync_final_location()` |
| `items_consumed 추상 개념 제거` | — | WTI 계약서 1건 | 금 계약서 1건 | 금 계약서 1건 | `stage2_optimizer.py:594` `_filter_abstract_items_consumed()` |
| `[PATCH-B]` 소지품 출처 불명 | — | — | — | — | `stage2_optimizer.py:645` (arc 2 only in this run) |
| End Location Sync | 여의도 | 강남 테헤란로 | — | — | `stage2_finalizer.py:324` `_sync_stage2_end_location_contract()` |
| End Inventory Sync | — | — | — | — | `stage2_finalizer.py:1307` (arc 1 only) |
| physical_inventory deterministic carryover | Yes (3 items) | Yes (3 items) | — | — | ui_events visible, V49.6 |

**Analysis**:

1. **`internal_energy` removal**: This fires on every arc for non-wuxia genres. It is **harmless residue** — the ensemble LLM keeps generating the field because it exists in the prompt/schema templates, and the auto-corrector strips it. Does not affect narrative content.

2. **`[C-1]` meta term sanitization**: Fires when the LLM writes "Arc" in tactical_doc prose. **Harmless residue** — cosmetic cleanup.

3. **Location sync**: This is the **real recurring issue**. The auto-corrector's `_sync_final_location()` propagates a potentially-hallucinated `joint_docs.final_location` into `arc_end_state.location`, which can overwrite the location consistently used in the tactical_doc prose. The finalizer's `_sync_stage2_end_location_contract()` then cements whichever value survived. Whether the final result is correct depends on which surface the Director prioritized during PASS_WITH_FIX.

4. **`items_consumed` abstract concept removal**: Fires when the LLM puts a financial instrument (계약서) in items_consumed. **Harmless residue** — these are conceptual assets, not physical items.

---

## Required Question Answers

### Q1. Where exactly does Arc 3 location truth diverge across tactical_doc, joint_docs, and state_constraints?

The divergence originates in `joint_docs.final_location`. The ensemble LLM generated `tactical_doc` consistently in 여의도, but set `joint_docs.final_location` to 강남. The auto-corrector at `stage2_optimizer.py:486` then synced `arc_end_state.location` toward the 강남 value. The Director caught the inconsistency. The finalizer's second location sync at `stage2_finalizer.py:324` resolved it back to 여의도 for Arc 3.

The split point is: **ensemble generation** → `joint_docs.final_location` hallucinated a different location than `tactical_doc`.

### Q2. Is the Arc 3 recovery-scene omission present in the generated tactical plan, or introduced by later normalization?

**Present in the generated tactical plan**. The ensemble LLM's beat_sequence contains no recovery beat. No normalization step removed it. The constraint compiler injected the STATE LOCK mandate (회복 장면 필수), but the LLM chose not to include an explicit recovery beat. The implicit mention of "6주간의 기다림" in the tactical_doc was deemed insufficient by the Director.

### Q3. Where exactly does Arc 4 asset arithmetic become inconsistent?

**In the ensemble's LLM generation**. The LLM wrote 제21화 start_state with portfolio valuation of 23억 (should be 25억) and end_state cash of 27.5억 (should be 28억). These are pure calculation errors in the generated text. The Director's PASS_WITH_FIX correctly identified both. After the fix patch, the final arc artifact and arc txt contain the corrected values (total 40.5억, cash 28억).

The error family is: **LLM arithmetic miscalculation during tactical_doc generation**.

### Q4. Is the smallest owner set `arc_ensemble + stage2_finalizer`, or does `stage2_optimizer` still materially own part of the drift?

**`stage2_optimizer` materially owns the location drift**, and `arc_ensemble` owns the generation problems.

The narrowest owner decomposition:

| Defect | Primary Owner | Secondary Owner |
|---|---|---|
| Location hallucination in joint_docs | `arc_ensemble.py` (LLM generation) | — |
| Location sync propagating bad joint_docs value | `stage2_optimizer.py:486` `_sync_final_location()` | — |
| Location finalization direction | `stage2_finalizer.py:324` `_sync_stage2_end_location_contract()` | — |
| Recovery-beat omission | `arc_ensemble.py` (LLM generation) | Prompt/constraint injection |
| Arithmetic errors | `arc_ensemble.py` (LLM generation) | — |
| Repeated `internal_energy` / `[C-1]` / abstract items | `stage2_optimizer.py` (auto-corrector) | Harmless residue |

**The three-file owner set is `arc_ensemble.py` + `stage2_optimizer.py` + `stage2_finalizer.py`**, but the active defect responsibility splits clearly:

- `arc_ensemble.py` owns content quality (arithmetic, recovery-beat, location hallucination in joint_docs)
- `stage2_optimizer.py` owns the **sync direction bug** where `_sync_final_location()` trusts `joint_docs.final_location` over `arc_end_state.location` — when it is `joint_docs` that is more likely to be hallucinated
- `stage2_finalizer.py` owns the **final location arbitration** — its `_sync_stage2_end_location_contract()` provides a second pass that sometimes corrects and sometimes cements the wrong value

---

## Recurrence Assessment

The location drift pattern (F-1, F-4) is **likely to recur in later arcs** because:

1. The ensemble LLM systematically generates `joint_docs.final_location` values that do not match `tactical_doc` prose — this appears to be a prompt/template issue where joint_docs is filled separately from tactical_doc
2. The auto-corrector's sync direction (`joint_docs → arc_end_state`) amplifies rather than corrects the LLM hallucination
3. The Director only catches location drift when it is severe enough to be flagged as a contradiction — minor location wording differences may pass undetected

The arithmetic drift (F-3) is **less likely to recur frequently** because:
- It depends on complex multi-step calculations that vary by arc
- The Director's numeric validation is effective at catching these
- The PASS_WITH_FIX mechanism successfully resolved it

The recovery-beat omission (F-2) is **moderately likely to recur** when arcs span time gaps — the STATE LOCK mandate exists but the LLM can choose to handle it implicitly rather than as a dedicated beat.

---

## 3-Pass Audit Record

Pass 1, structure and scope:
- Confirmed survey is bounded to Arc 3/4 continuity and patch-pressure only
- Confirmed all required sinks were read
- Confirmed output path is correct

Pass 2, evidence and consistency:
- All location values cross-checked against runtime_audit, ui_events, decisions.jsonl, and artifact JSON
- Arithmetic values cross-checked against both artifact JSON and final arc txt
- Owner file paths verified against grep results in production code
- Auto-correct log timestamps verified as monotonically consistent with the session timeline

Pass 3, execution and readability:
- Findings placed first
- Required questions answered with file paths
- Recurrence assessment provided
- No code edits, no docs/temp mutation, no retrieval-empty reopening

Confidence: 0.96

---

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-06 output
