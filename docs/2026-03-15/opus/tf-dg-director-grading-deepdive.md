# TF-DG: DirectorGrading 딥다이브

| Field | Value |
|-------|-------|
| Baseline | bbb00a77 |
| Date | 2026-03-15 |
| Scope | DirectorGrading: grade classification, adaptive threshold, revision guides, score mapping, state approval |
| Source files | director_grading.py:689줄 |
| TF Items | 12 (CRITICAL 2 / IMPORTANT 6 / INSIGHT 4) |

---

## 1. Executive Summary

`DirectorGradingSystem`은 원고 품질을 A/B/C/D 등급으로 분류하고, 적응형 PASS 기준선을 계산하며, 수정 가이드를 생성하고, 상태 업데이트를 승인하는 순수 데이터 가공 모듈이다 (LLM 호출 없음).

주요 발견:
- **CRITICAL**: `on_approve_workflow`의 `is_approved` 로직이 거부된 항목이 있어도 적용된 항목이 하나라도 있으면 `approved=True`를 반환하여, 부분 거부가 효과적으로 무시됨 (TF-DG-01)
- **CRITICAL**: `_extract_category_score`에서 `commercial_appeal`이 engagement와 commercial에, `emotion_arc`가 engagement와 satisfaction에 중복 매핑되어, 가중합 왜곡 발생 (TF-DG-02)
- **IMPORTANT**: `apply_adaptive_decision`이 `ep_type` 파라미터를 `get_adaptive_threshold`에 전달하지 않아, 에피소드 타입 조정이 적응형 판정에서 누락됨 (TF-DG-03)
- **IMPORTANT**: 적응형 임계값에서 arc_position 도입부(-5)와 ep_type 도입부(-5) 및 retry(-10)가 중첩 가능하여, clamp(45) 덕에 제한되지만 설계 의도와 다를 수 있음 (TF-DG-04)
- **IMPORTANT**: `on_approve_workflow`에서 `ep_num`과 `martial_manager` 파라미터가 전혀 사용되지 않음 (TF-DG-05)
- 등급 분류 자체는 monotonic하고 올바름. QUALITY_WEIGHTS 합은 정확히 1.0.

---

## 2. Architecture / Data Flow Diagram (ASCII)

```
                    +--------------------------+
                    |  ValidationOrchestrator   |
                    |  (breakdown dict 생성)    |
                    +-----------+--------------+
                                |
                    validation_result = {
                      "breakdown": {
                        "scene_completeness": {"score": N, "max": M},
                        "commercial_appeal": {"score": N, "max": M},
                        ...
                      }
                    }
                                |
                                v
+---------------------------------------------------------------+
|           DirectorGradingSystem                                |
|                                                                |
|  grade_manuscript_v59(ep_num, manuscript, validation_result)   |
|    |                                                           |
|    |  1. _extract_category_score(breakdown, category)          |
|    |     category_mapping:                                     |
|    |       structure  -> [scene_completeness, scope_overflow,  |
|    |                      required_scenes]                     |
|    |       prose      -> [prose_rhythm, vocabulary_diversity,  |
|    |                      show_dont_tell]                      |
|    |       consistency-> [char_consistency, rel_consistency,   |
|    |                      continuity]                          |
|    |       engagement -> [emotion_arc(*), commercial_appeal(*),|
|    |                      cliffhanger]                         |
|    |       commercial -> [commercial_appeal(*), pattern_div]   |
|    |       satisfaction->[reader_satisfaction, emotion_arc(*)]  |
|    |                                                           |
|    |     (*) = OVERLAP: same item counted in multiple cats     |
|    |                                                           |
|    |  2. weighted_total = SUM(cat_score * cat_weight)          |
|    |     weights: structure=0.15, prose=0.15, consistency=0.25 |
|    |              engagement=0.15, commercial=0.20, satisf=0.10|
|    |     sum = 1.00                                            |
|    |                                                           |
|    |  3. Grade assignment (descending, first match):           |
|    |     A >= 85  |  B >= 70  |  C >= 50  |  D >= 0           |
|    |                                                           |
|    |  4. Strengths (score>=80) / Weaknesses (score<60)         |
|    |                                                           |
|    |  5. generate_revision_guide_v59()                         |
|    |     -> priority, tasks, examples, effort estimate         |
|    +-----------------------------------------------------------+
|                                                                |
|  get_adaptive_threshold(arc_pos, total_eps, ep_type, retry)    |
|    |                                                           |
|    |  base = director.base_pass_threshold (default 60)         |
|    |  + arc_position adjustments (-5 to +10)                   |
|    |  + genre adjustments (0 to +3)                            |
|    |  + ep_type adjustments (-5 to +10)                        |
|    |  + retry relaxation (-5 to -10)                           |
|    |  clamp to [45, 85]                                        |
|    +-----------------------------------------------------------+
|                                                                |
|  apply_adaptive_decision(score, original_decision, ...)        |
|    |  *** ep_type NOT forwarded (TF-DG-03) ***                 |
|    |                                                           |
|    |  score >= threshold?                                      |
|    |    YES + original=REJECT -> CONDITIONAL_PASS              |
|    |    NO  + original=PASS/PASS_WITH_FIX -> CONDITIONAL_PASS  |
|    |                                                           |
|    +-----> DirectorEnsemble (L1244-1262):                      |
|            CONDITIONAL_PASS is further resolved:               |
|              - original was REJECT -> stays REJECT             |
|              - original was PASS/PASS_WITH_FIX -> stays orig   |
|              - else -> PASS (catch-all, see TF-DE-05)          |
|                                                                |
|  on_approve_workflow(ep_num, state_updates, current_hud, ...)  |
|    |  Validates state change magnitudes                        |
|    |  approved = (no rejections) OR (any applied) [TF-DG-01]  |
+---------------------------------------------------------------+

                    GRADING MODULE CALL SITES
                    =========================

  Director facade (director.py)
    |
    +-- grade_manuscript_v59() --> _grading.grade_manuscript_v59()
    +-- generate_revision_guide_v59() --> _grading.generate_revision_guide_v59()
    +-- format_revision_report_v59() --> _grading.format_revision_report_v59()
    +-- get_adaptive_threshold() --> _grading.get_adaptive_threshold()
    +-- apply_adaptive_decision() --> _grading.apply_adaptive_decision()
    +-- on_approve_workflow() --> _grading.on_approve_workflow()
    |
    |  NOTE: grade_manuscript_v59() is NOT called from main_a.py or
    |        any orchestrator. It exists as a utility but its integration
    |        into the production pipeline is indirect or dormant.
    |
    |  apply_adaptive_decision() IS actively called from:
    |  - DirectorEnsembleSelector.select_and_judge_ensemble() (L1244)
    |
    |  on_approve_workflow() IS actively called from:
    |  - Stage4PostProcessor.process_pass_result() (L382)
```

---

## 3. TF Items

### TF-DG-01: `on_approve_workflow` Partial Rejection Masked as Approval — CRITICAL

- **Location**: `director_grading.py:L686`
- **Description**: The `is_approved` boolean is computed as `len(rejected) == 0 or len(applied) > 0`. This means:
  - If 5 updates are submitted, 4 are rejected, and 1 is applied, `is_approved = True`
  - The caller (Stage4PostProcessor L382) checks only `approved` to proceed
  - Rejected updates and their warnings are returned but the `approved=True` signal implies the workflow passed validation
- **Evidence**:
  ```python
  # L686
  is_approved = len(rejected) == 0 or len(applied) > 0
  ```
  The intent appears to be "approve if there's anything valid to apply," but the semantics are "approve even if critical state changes were rejected." For example, an internal_energy increase of +999 (rejected) alongside a realm change (applied) would still result in `approved=True`.
- **Impact**: High. State integrity violation risk. A Writer could propose dangerous state changes (e.g., internal_energy +999) bundled with harmless ones, and the workflow would still be approved. The caller has no clear signal that some changes were rejected.
- **Suggested fix direction**: Change to `is_approved = len(rejected) == 0` (strict: all or nothing), or return a `partial_approval` flag so the caller can distinguish full approval from partial approval. At minimum, log a WARNING when partial approval occurs.

---

### TF-DG-02: Score Extraction Category Overlap — Double-Counting `commercial_appeal` and `emotion_arc` — CRITICAL

- **Location**: `director_grading.py:L148-155`
- **Description**: The `category_mapping` dict maps validation breakdown items to grading categories. Two items are used in multiple categories:
  - `commercial_appeal` appears in both `engagement` (weight 0.15) and `commercial` (weight 0.20)
  - `emotion_arc` appears in both `engagement` (weight 0.15) and `satisfaction` (weight 0.10)

  This means these validation items exert disproportionate influence on the final weighted score:
  - `commercial_appeal` effective weight contribution: 0.15 (as 1/3 of engagement) + 0.20 (as 1/2 of commercial) = 0.05 + 0.10 = **0.15** of total score
  - `emotion_arc` effective weight contribution: 0.15 (as 1/3 of engagement) + 0.10 (as 1/2 of satisfaction) = 0.05 + 0.05 = **0.10** of total score

  Meanwhile, `pattern_diversity` only contributes 0.10 (as 1/2 of commercial) and `reader_satisfaction` only contributes 0.05 (as 1/2 of satisfaction).

- **Evidence**:
  ```python
  # L148-155
  category_mapping = {
      ...
      "engagement": ["emotion_arc", "commercial_appeal", "cliffhanger"],
      "commercial": ["commercial_appeal", "pattern_diversity"],
      "satisfaction": ["reader_satisfaction", "emotion_arc"],
  }
  ```
- **Impact**: High. A manuscript with a very high `commercial_appeal` score will be boosted in both engagement AND commercial categories, inflating the overall grade. Conversely, a low `commercial_appeal` will be penalized twice. This creates a hidden non-uniform weighting that contradicts the explicitly declared `QUALITY_WEIGHTS`.
- **Suggested fix direction**: Deduplicate the mappings. Each validation breakdown item should appear in exactly one category. For example:
  - Move `commercial_appeal` out of `engagement` (engagement already has `emotion_arc` + `cliffhanger`)
  - Move `emotion_arc` out of `satisfaction` (satisfaction should rely on `reader_satisfaction` alone, or add a dedicated item)

---

### TF-DG-03: `apply_adaptive_decision` Drops `ep_type` Parameter — IMPORTANT

- **Location**: `director_grading.py:L555-559`
- **Description**: `apply_adaptive_decision()` accepts `arc_pos`, `total_eps`, and `retry_count` but does NOT accept or forward `ep_type` to `get_adaptive_threshold()`. Since `get_adaptive_threshold()` defaults `ep_type` to `"normal"`, the episode type adjustments (climax: +10, intro: -5, transition: -3) are **never applied** when grading decisions are made through `apply_adaptive_decision`.

  The only caller is `DirectorEnsembleSelector.select_and_judge_ensemble()` (L1244-1250), which also does not pass `ep_type`.

- **Evidence**:
  ```python
  # L555-559
  def apply_adaptive_decision(
      self, score: int, original_decision: str, arc_pos: int = 1, total_eps: int = 5, retry_count: int = 0
  ) -> dict:
      threshold_info = self.get_adaptive_threshold(arc_pos=arc_pos, total_eps=total_eps, retry_count=retry_count)
      # ep_type is missing ^ -- defaults to "normal"
  ```
- **Impact**: Medium-High. Episode type is a significant modifier (+10/-5/-3). Climax episodes are supposed to be judged more strictly, but this adjustment is silently dropped. The arc_position ratio partially compensates (arc_pos=5/total_eps=5=1.0 >= 0.8 triggers +10 anyway), but `ep_type=climax` at arc midpoint would have no effect.
- **Suggested fix direction**: Add `ep_type: str = "normal"` parameter to `apply_adaptive_decision()` and forward it to `get_adaptive_threshold()`. Update the ensemble caller to pass the episode type.

---

### TF-DG-04: Adaptive Threshold Double-Dip on Arc Position + Episode Type — IMPORTANT

- **Location**: `director_grading.py:L481-528`
- **Description**: The arc position adjustment (L484-494) and episode type adjustment (L517-527) are independent and additive. Both can describe the same narrative position:
  - `arc_pos=1, total_eps=5` (ratio 0.2) triggers "도입부(-5점)" on L486
  - `ep_type="intro"` triggers "도입부(-5점)" on L522
  - Combined: -10 from the same conceptual adjustment

  Similarly for climax:
  - `arc_pos=5, total_eps=5` (ratio 1.0) triggers "절정부(+10점)" on L489
  - `ep_type="climax"` triggers "클라이맥스(+10점)" on L518
  - Combined: +20 (though clamped to 85)

  The `reason_parts` list will show both "도입부(-5점)" and "도입부(-5점)" — identical strings for different sources.

- **Evidence**:
  ```python
  # L484-494
  if arc_position_ratio <= 0.2:
      base -= 5   # arc position: intro
      ...
  # L517-524
  if ep_type == "climax":
      base += 10  # ep type: climax
  elif ep_type == "intro":
      base -= 5   # ep type: intro
  ```
- **Impact**: Medium. Currently mitigated because (a) `apply_adaptive_decision` doesn't pass `ep_type` (TF-DG-03), so the double-dip never actually fires through the main path, and (b) the clamp [45, 85] limits extremes. However, if TF-DG-03 is fixed, this stacking becomes live and could cause -10 intro penalty or +20 climax bonus before clamp.
- **Suggested fix direction**: Arc position and episode type encode overlapping information. Consider making them mutually exclusive (ep_type overrides arc_position adjustment) or clarifying that intentional stacking is desired. At minimum, differentiate reason strings: "arc도입부(-5)" vs "ep_type도입부(-5)".

---

### TF-DG-05: Unused Parameters in `on_approve_workflow` — IMPORTANT

- **Location**: `director_grading.py:L582`
- **Description**: The `on_approve_workflow` method signature includes `ep_num` and `martial_manager` parameters, but neither is referenced anywhere in the method body. The `ep_num` is passed by the caller (Stage4PostProcessor L382) but serves no purpose. The `martial_manager` parameter suggests planned integration with martial arts validation that was never implemented.
- **Evidence**:
  ```python
  # L582
  def on_approve_workflow(self, ep_num, state_updates, current_hud, martial_manager=None) -> dict:
      # ep_num: never used in method body (L588-688)
      # martial_manager: never used in method body (L588-688)
  ```
- **Impact**: Low-Medium. Dead parameters suggest incomplete integration. The `martial_manager` was likely intended to enable martial arts system-specific validations (e.g., realm progression rules, technique compatibility) but remains wired but unused. `ep_num` could be used for episode-specific validation rules (e.g., early episodes should not have realm advancement).
- **Suggested fix direction**: Either implement the intended `martial_manager` validation logic (realm progression rules, technique compatibility checks) or remove the parameter and update all callers. Use `ep_num` for context-aware validation (e.g., "realm change only allowed every N episodes").

---

### TF-DG-06: `_extract_category_score` Default 50 Hides Missing Validation Data — IMPORTANT

- **Location**: `director_grading.py:L168`
- **Description**: When a category has no matching items in the breakdown (either because the validation items are missing from the result, or the category mapping points to non-existent items), the method returns a default score of 50 instead of signaling the absence. This 50 is then treated as a real score — it contributes to the weighted total, and (since 50 < 60) can even generate a weakness entry.
- **Evidence**:
  ```python
  # L168
  return sum(scores) / len(scores) if scores else 50
  ```
  If the `ValidationOrchestrator` does not produce `reader_satisfaction` or `emotion_arc` for the satisfaction category, it silently scores 50. If only `reader_satisfaction` is present (not `emotion_arc`), it becomes the sole basis for the category. The default 50 is indistinguishable from an actual score of 50.
- **Impact**: Medium. In production, if the validation breakdown is sparse (e.g., during early development, after ValidationOrchestrator changes, or when certain checks are disabled), grades will cluster around C (since weighted 50s map to total ~50). This makes it impossible to distinguish "genuinely mediocre" from "we couldn't measure it."
- **Suggested fix direction**: Return a sentinel (e.g., `None`) or a tuple `(score, is_estimated)` when falling back to default. At minimum, log a WARNING when defaulting so operators can detect silent data loss.

---

### TF-DG-07: `_get_revision_example` Satisfaction Branch — Convoluted but Correct — INSIGHT

- **Location**: `director_grading.py:L383-391`
- **Description**: The `satisfaction` example is handled via a special `if` branch outside the main examples dict. The logic:
  1. `examples.get(category)` returns `None` for `category="satisfaction"` (not in dict)
  2. `not None` is `True`, enters the `if` block
  3. `category == "satisfaction"` is `True`, returns the satisfaction example

  This is functionally correct but fragile. If someone adds `"satisfaction": {...}` to the examples dict, the special branch would never execute (since `not dict_instance` is `False`). The pattern was likely added as a quick fix for Phase 3-D1.
- **Evidence**:
  ```python
  # L383-391
  if not examples.get(category):
      if category == "satisfaction":
          return { ... }
  return examples.get(category)
  ```
- **Impact**: Low. Works correctly today. Code readability issue only.
- **Suggested fix direction**: Simply add `"satisfaction": {...}` as a regular entry in the examples dict, removing the special branch.

---

### TF-DG-08: No NaN/Infinity/Negative Score Guard in `grade_manuscript_v59` — IMPORTANT

- **Location**: `director_grading.py:L94-144`
- **Description**: The `grade_manuscript_v59` method computes `weighted_total` from validation scores but does not guard against:
  - **NaN**: If a breakdown item has `score=float('nan')`, the category average becomes NaN, and the weighted total becomes NaN. `NaN >= 85` is `False`, `NaN >= 70` is `False`, etc., so the grade defaults to D. However, `round(NaN, 1)` returns `nan`, and downstream consumers may fail.
  - **Infinity**: If `max_score` is 0 in `_extract_category_score` (L166), the guard `if max_score > 0` prevents division by zero, returning 0 instead. But if `max_score` is a very small float, the score can be extremely large.
  - **Negative scores**: `_extract_category_score` can return negative values if `score` is negative (e.g., from LLM hallucination). No floor is applied.
  - **Scores > 100**: If `score > max`, the percentage exceeds 100. No ceiling is applied.
- **Evidence**:
  ```python
  # L164-166
  score = item_data.get("score", 0)
  max_score = item_data.get("max", 1)
  scores.append((score / max_score) * 100 if max_score > 0 else 0)
  # No clamp to [0, 100]
  ```
- **Impact**: Medium. LLM-generated validation scores are not guaranteed to be in valid ranges. A single `score: -50, max: 10` entry would yield -500%, which would drag the weighted total far below 0 and assign grade D even if all other categories are excellent.
- **Suggested fix direction**: Clamp per-item scores to `[0, 100]` after the percentage calculation in `_extract_category_score`. Add `math.isnan`/`math.isinf` guards. Log a WARNING for out-of-range inputs.

---

### TF-DG-09: Adaptive Threshold `total_eps=0` Division Safety — INSIGHT

- **Location**: `director_grading.py:L482`
- **Description**: The code handles `total_eps <= 0` by defaulting to `0.5`:
  ```python
  arc_position_ratio = arc_pos / total_eps if total_eps > 0 else 0.5
  ```
  This is correct and prevents ZeroDivisionError. The default 0.5 means the arc is treated as mid-point, which is a reasonable neutral assumption. This is a positive finding.
- **Impact**: None. Correctly handled.
- **Suggested fix direction**: None needed.

---

### TF-DG-10: `manuscript` Parameter Unused in `grade_manuscript_v59` — INSIGHT

- **Location**: `director_grading.py:L74`
- **Description**: The `grade_manuscript_v59` method accepts `manuscript: str` but never uses it. All grading is based solely on `validation_result`. The manuscript text is not directly examined (e.g., for length checks, keyword analysis, etc.).
- **Evidence**:
  ```python
  # L74
  def grade_manuscript_v59(self, ep_num: int, manuscript: str, validation_result: dict) -> dict:
      # manuscript is never referenced in the method body (L94-144)
  ```
- **Impact**: Low. The manuscript was likely included for future use (e.g., direct text analysis) or to maintain a consistent interface. Currently no functional impact.
- **Suggested fix direction**: Either implement direct text checks (e.g., length validation against ManuscriptLimits) or document that the parameter is reserved for future use.

---

### TF-DG-11: CONDITIONAL_PASS Semantics Mismatch Between Grading and Ensemble — IMPORTANT

- **Location**: `director_grading.py:L565-572` + `director_ensemble.py:L1252-1262`
- **Description**: `apply_adaptive_decision` returns `CONDITIONAL_PASS` in two opposite scenarios:
  1. **Score above threshold, original was REJECT**: "Score is good enough despite Director rejection" (L566-568)
  2. **Score below threshold, original was PASS/PASS_WITH_FIX**: "Score is too low despite Director approval" (L570-572)

  Both cases produce `decision: "CONDITIONAL_PASS"`, but they represent fundamentally different situations. The ensemble (L1252-1262) then resolves this:
  - Case 1 (REJECT -> CONDITIONAL_PASS): Reverted to REJECT (L1255-1256, "Director 주권")
  - Case 2 (PASS -> CONDITIONAL_PASS, adjusted=True): Reverted to original PASS (L1259-1260)
  - Else: Falls through to PASS (L1262, the TF-DE-05 catch-all)

  In practice, CONDITIONAL_PASS is **always overridden** by the ensemble. It never reaches the caller as a final verdict. This makes the adaptive decision layer effectively a no-op in the current integration.

- **Evidence**:
  ```python
  # director_grading.py L565-572
  if score >= threshold:
      if original_decision == "REJECT":
          new_decision = "CONDITIONAL_PASS"  # Case 1
  else:
      if original_decision in ("PASS", "PASS_WITH_FIX"):
          new_decision = "CONDITIONAL_PASS"  # Case 2

  # director_ensemble.py L1252-1262
  if final_verdict == "CONDITIONAL_PASS":
      if original_verdict == "REJECT":
          final_verdict = "REJECT"              # Case 1 -> REJECT
      elif v60_97_swapped:
          final_verdict = "REJECT"
      elif adaptive_result.get("adjusted") and original_verdict in ("PASS", "PASS_WITH_FIX"):
          final_verdict = original_verdict       # Case 2 -> original
      else:
          final_verdict = "PASS"                 # catch-all -> PASS
  ```
- **Impact**: Medium. The adaptive layer creates complexity but its outputs are systematically overridden. The only observable effect is the `adaptive_threshold` and `adaptive_reason` fields in the ensemble result (L1367-1368), used for operator logging. The actual PASS/REJECT decision is never altered by adaptive logic in the current integration.
- **Suggested fix direction**: Either (a) make adaptive decisions actually influential (e.g., allow REJECT -> CONDITIONAL_PASS to stand in certain conditions), or (b) simplify to a pure logging/observability layer without pretending to make decisions. Document the intended behavior clearly.

---

### TF-DG-12: `on_approve_workflow` String-Prefix Validation is Regex Import Inside Loop — INSIGHT

- **Location**: `director_grading.py:L641-672`
- **Description**: The `re` module is imported inside the loop body (L642: `import re`) on every iteration where a string value starts with "+" or "-". While Python caches module imports so subsequent `import re` calls are cheap (just a dict lookup), this is an unusual pattern. The import was likely placed inline to avoid a top-level import for a rarely-used feature.

  More substantively, the string-prefix numeric extraction (L640-672) is a code duplication of the numeric validation above it (L615-638). Both paths perform the same LIMITS checks with identical logic, just for different input types (int/float vs string-encoded).

- **Evidence**:
  ```python
  # L640-642
  if isinstance(value, str) and (value.startswith("+") or value.startswith("-")):
      try:
          import re  # imported inside loop
  ```
- **Impact**: Low. Performance negligible (Python module cache). Code duplication is a maintenance burden.
- **Suggested fix direction**: Move `import re` to module top level. Extract the LIMITS validation into a helper to eliminate the ~30-line code duplication between the int/float path (L615-638) and string path (L640-672).

---

## 4. Summary Matrix

| ID | Title | Severity | Location | Category |
|----|-------|----------|----------|----------|
| TF-DG-01 | Partial rejection masked as approval in `on_approve_workflow` | CRITICAL | L686 | State Integrity |
| TF-DG-02 | Score extraction double-counts `commercial_appeal` and `emotion_arc` | CRITICAL | L148-155 | Scoring Accuracy |
| TF-DG-03 | `apply_adaptive_decision` drops `ep_type` parameter | IMPORTANT | L555-559 | Feature Completeness |
| TF-DG-04 | Adaptive threshold double-dip on arc position + episode type | IMPORTANT | L481-528 | Threshold Design |
| TF-DG-05 | Unused `ep_num` and `martial_manager` parameters | IMPORTANT | L582 | Code Hygiene |
| TF-DG-06 | Default score 50 hides missing validation data | IMPORTANT | L168 | Observability |
| TF-DG-07 | `_get_revision_example` satisfaction branch convoluted but correct | INSIGHT | L383-391 | Code Quality |
| TF-DG-08 | No NaN/Infinity/negative score guard | IMPORTANT | L164-168 | Input Validation |
| TF-DG-09 | `total_eps=0` division handled correctly | INSIGHT | L482 | Positive Finding |
| TF-DG-10 | `manuscript` parameter unused in `grade_manuscript_v59` | INSIGHT | L74 | Code Hygiene |
| TF-DG-11 | CONDITIONAL_PASS systematically overridden by ensemble | IMPORTANT | L565-572 + ensemble L1252-1262 | Design Coherence |
| TF-DG-12 | Inline `import re` + duplicated LIMITS validation | INSIGHT | L641-672 | Code Quality |

---

## 5. Cross-References to Prior TF Findings

| This Finding | Related Prior Finding | Relationship |
|---|---|---|
| TF-DG-03 (ep_type dropped) | TF-DE-03 (retry decay gaming) | Both relate to adaptive threshold parameter handling. TF-DE-03 noted retry-based decay can be gamed; TF-DG-03 shows ep_type is entirely lost in the adaptive decision path. |
| TF-DG-11 (CONDITIONAL_PASS overridden) | TF-DE-05 (catch-all PASS in else branch) | TF-DE-05 identified the catch-all `PASS` in the ensemble's CONDITIONAL_PASS resolution. TF-DG-11 shows the root cause: the grading module creates a state that the ensemble systematically undoes. |
| TF-DG-04 (threshold double-dip) | TF-DE-03 (retry decay gaming) | Both are threshold manipulation vectors. If TF-DG-03 is fixed (ep_type forwarding), TF-DG-04 stacking becomes live and compounds with TF-DE-03's retry gaming. |

---

## 6. 핵심 코드 참조 (Appendix)

### A. Grade Classification Logic (L106-111)

```python
grade = "D"
for g, criteria in self.QUALITY_GRADES.items():
    if weighted_total >= criteria["min_score"]:
        grade = g
        break
```

Relies on Python 3.7+ dict insertion order: A(85) -> B(70) -> C(50) -> D(0). First match wins. The mapping is strictly monotonic and correct:
- score >= 85: A
- 70 <= score < 85: B
- 50 <= score < 70: C
- 0 <= score < 50: D
- score < 0: D (since 0 >= 0 would match D, but negative scores also match D since the loop checks D last with min_score=0, and negative < 0 so D matches via the initial `grade = "D"`)

### B. QUALITY_WEIGHTS (L65-72)

```python
QUALITY_WEIGHTS = {
    "structure": 0.15,
    "prose": 0.15,
    "consistency": 0.25,   # highest weight
    "engagement": 0.15,
    "commercial": 0.20,
    "satisfaction": 0.10,  # lowest weight
}
# Sum = 1.00 (verified)
```

### C. Adaptive Threshold Adjustment Table (L481-538)

| Factor | Condition | Adjustment | Stacks With |
|--------|-----------|------------|-------------|
| Arc position | ratio <= 0.2 | -5 score, -300 length | ep_type intro |
| Arc position | ratio >= 0.8 | +10 score, +300 length | ep_type climax |
| Arc position | 0.4-0.6 | +3 score | - |
| Genre | hunter/actor/sports/medical | +2 | all |
| Genre | investment | +3 | all |
| Genre | wuxia | +0 | - |
| Episode type | climax | +10 score, +500 length | arc position |
| Episode type | intro | -5 score, -200 length | arc position |
| Episode type | transition | -3 score | arc position |
| Retry | >= 3 | -10 | all |
| Retry | >= 2 | -5 | all |
| **Clamp** | always | [45, 85] score; [3500, 6000] length | - |

### D. State Update LIMITS (L600-608)

| Key | Limit Type | Value |
|-----|-----------|-------|
| misunderstanding | max_change | +/-30 |
| obsession | max_change | +/-30 |
| wealth | max_change | +/-10000 |
| internal_energy (wuxia only) | max_increase | +200 |
| internal_energy (wuxia only) | max_decrease | -500 |

### E. `is_approved` Truth Table (L686)

| rejected count | applied count | is_approved | Correct? |
|---|---|---|---|
| 0 | 0 | True | OK (empty after filtering "현상 유지") |
| 0 | 5 | True | OK |
| 3 | 0 | False | OK |
| 3 | 2 | True | **PROBLEMATIC** (TF-DG-01) |
| 1 | 4 | True | **PROBLEMATIC** (TF-DG-01) |
