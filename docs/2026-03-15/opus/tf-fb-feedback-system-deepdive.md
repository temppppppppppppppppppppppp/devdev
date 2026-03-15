# TF-FB: FeedbackSystem 딥다이브

| Field | Value |
|-------|-------|
| Baseline | bbb00a77 |
| Date | 2026-03-15 |
| Scope | FeedbackSystem: structured feedback, quantification, reverse feedback, adaptive intensity |
| Source files | feedback_system.py:886줄 |
| TF Items | 14 (CRITICAL 2 / IMPORTANT 7 / INSIGHT 5) |

## 1. Executive Summary

`FeedbackSystem`은 SovereignApp의 피드백 생성 로직을 캡슐화한 순수 함수 모음 클래스다. 15개 메서드가 6개 카테고리(구조화/정량화/Stage별/역방향/적응형/재시도)로 조직되어 있다.

핵심 발견:

1. **Dead code 비율이 높다.** 15개 메서드 중 4개(`build_structured_feedback`, `format_feedback_for_prompt`, `generate_structured_blueprint_feedback`, `build_strong_kind_feedback_legacy`)는 production caller가 전무하고, 2개(`classify_rejection_feedback`, `simplify_prompt_for_retry`)는 wrapper만 존재하고 production consumer가 없다. 전체의 40%가 dead surface다.

2. **정량화 피드백이 실측이 아닌 하드코딩 추정치에 의존한다.** 대화 비율을 항상 15%로 가정하고, 후반부 분량을 35%로 가정한다. 실제 원고 분석 결과와 무관한 피드백이 LLM에 전달된다.

3. **`pass_threshold`/`feedback_level`/`strictness` 반환값이 완전히 무시된다.** `get_adaptive_feedback_intensity()`가 반환하는 4개 키 중 `guidance` 문자열만 소비되고, 나머지 3개(특히 `pass_threshold`)는 실제 scoring/validation 파이프라인과 연결되지 않는다.

4. **역방향 피드백이 정방향 피드백과 동시 주입되어 상충 가능성이 있다.** Stage4->3, Stage3->2 역방향 피드백이 `enhanced_context` 선두에 prepend되므로, 정방향 피드백보다 시각적으로 앞서지만 의미적 우선순위가 불분명하다.

## 2. Architecture / Data Flow Diagram (ASCII)

```
                        FeedbackSystem (Pure Functions, 15 methods)
                        ============================================

  ┌───────────────────────────────────────────────────────────────────────────┐
  │                          LIVE Production Path                            │
  │                                                                          │
  │   Stage2 Preflight                                                       │
  │   ─────────────────                                                      │
  │   build_minimal_arc_context()─────┐                                      │
  │   generate_reverse_feedback_      │                                      │
  │     stage3_to_2()────────────────┐│                                      │
  │   generate_reverse_feedback_     ││   ┌──── enhanced_context ──────────┐ │
  │     stage4_to_2()───────────────┐││   │                               │ │
  │                                 │││   │  [reverse 4→2 feedback]       │ │
  │                                 ││└──>│  [reverse 3→2 feedback]       │ │
  │                                 │└───>│  [current_feedback]           │ │
  │                                 └────>│  [minimal_arc_context]        │ │
  │                                       │                               │ │
  │                                       └───────────────────────────────┘ │
  │                                                                          │
  │   Stage2 Validation Pipeline                                             │
  │   ──────────────────────────                                             │
  │   get_adaptive_feedback_intensity()──┐  (only 'guidance' key consumed)   │
  │   generate_structured_arc_feedback()─┤                                   │
  │   build_strong_kind_feedback()───────┤  ┌─ _ci_feedback[:3000] ────────┐ │
  │   build_focused_context()────────────┘  │  strong_kind + focused       │ │
  │                                         │  + structured + banned       │ │
  │                                         │  + prev_state_reminder       │ │
  │                                         └─ → Director advisory ────────┘ │
  │                                                                          │
  │   Stage2 Finalizer                                                       │
  │   ────────────────                                                       │
  │   get_adaptive_feedback_intensity()──── (only 'guidance' key consumed)   │
  │                                                                          │
  │   Stage4 Orchestrator                                                    │
  │   ───────────────────                                                    │
  │   generate_reverse_feedback_                                             │
  │     stage4_to_3()────────────────────── merged into blueprint feedback   │
  │                                                                          │
  │   main_a.py (Stage4 REJECT path)                                         │
  │   ──────────────────────────────                                         │
  │   quantify_reject_feedback()─────────── appended to action_items         │
  │                                                                          │
  └───────────────────────────────────────────────────────────────────────────┘

  ┌───────────────────────────────────────────────────────────────────────────┐
  │                         DEAD / TEST-ONLY Surface                         │
  │                                                                          │
  │   build_structured_feedback()        ── 0 production callers             │
  │   format_feedback_for_prompt()       ── 0 production callers             │
  │   generate_structured_blueprint_     ── 0 production callers             │
  │     feedback()                                                           │
  │   build_strong_kind_feedback_        ── 0 production callers             │
  │     legacy()                         ── 0 callers at all (incl. tests)   │
  │   classify_rejection_feedback()      ── dormant facade, 0 prod callers   │
  │   simplify_prompt_for_retry()        ── dormant facade, 0 prod callers   │
  │                                                                          │
  └───────────────────────────────────────────────────────────────────────────┘

  ┌───────────────────────────────────────────────────────────────────────────┐
  │                    Feedback Injection Ordering                            │
  │                                                                          │
  │   Stage2 Preflight enhanced_context assembly:                            │
  │                                                                          │
  │   1. [Stage4→2 reverse feedback]     ← prepend (가장 앞)                 │
  │   2. [Stage3→2 reverse feedback]     ← prepend                           │
  │   3. [V51 Analyst intelligence]      ← prepend                           │
  │   4. [Constitutional checker]        ← prepend                           │
  │   5. [current_feedback]              ← base                              │
  │   6. [constraint_block]              ← via Focus Mode                    │
  │   7. [minimal_arc_context]           ← via Focus Mode                    │
  │                                                                          │
  │   Note: reverse feedback is at the TOP, potentially far from              │
  │   the actual instructions the LLM should prioritize.                     │
  │                                                                          │
  └───────────────────────────────────────────────────────────────────────────┘
```

## 3. TF Items

### TF-FB-01: `quantify_reject_feedback` uses hardcoded estimates instead of actual content analysis -- CRITICAL

- **Location**: `feedback_system.py:L109-L168`
- **Description**: The dialogue ratio quantification (section 2, L112-113) hardcodes the current dialogue ratio as 15% and target as 30%, regardless of actual content analysis. The scene density section (L129-131) assumes the latter half is always 35% of total length. The sensory description section (L156-157) calculates `target_sensory` as `4 * (content_length // 1000)` and `estimated_sensory` as `1 * (content_length // 1000)`, producing a constant 3:1 ratio regardless of actual content.
- **Evidence**:
  ```python
  # L112-113: hardcoded 15% / 30%
  current_dialogue_chars = int(content_length * 0.15)
  target_dialogue_chars = int(content_length * 0.30)

  # L129-131: hardcoded 35%
  target_latter_half = content_length // 2
  estimated_latter_half = int(content_length * 0.35)

  # L156-157: constant ratio
  target_sensory = (content_length // 1000) * 4
  estimated_sensory = (content_length // 1000) * 1
  ```
- **Impact**: The LLM receives quantified feedback (e.g., "대화 750자 추가 필요") that is entirely fabricated. For a 5000-character manuscript, dialogue feedback always says "750자 추가 필요" regardless of whether the actual dialogue count is 0% or 40%. This can cause the LLM to add unnecessary dialogue when dialogue is already sufficient, or provide insufficient guidance when dialogue is truly lacking.
- **Suggested fix direction**: Accept the actual `audit_result` data (which is already a parameter but unused for sections 2-6). Use `score_breakdown` values from the audit to compute actual deficits. The `audit_result.get("score_breakdown", {})` call at L110 already exists but its result is discarded (statement with no effect).

---

### TF-FB-02: `audit_result.get("score_breakdown", {})` is a no-op expression -- CRITICAL

- **Location**: `feedback_system.py:L110`
- **Description**: Line 110 calls `audit_result.get("score_breakdown", {})` as a bare expression statement. The return value is not assigned to any variable. This appears to be a bug where the developer intended to use the score breakdown data in subsequent quantification logic but forgot the assignment.
- **Evidence**:
  ```python
  # L110 — bare expression, return value discarded
  audit_result.get("score_breakdown", {})
  if "대화" in reason or "건조" in reason:
      current_dialogue_chars = int(content_length * 0.15)  # hardcoded instead
  ```
- **Impact**: This is the root cause of TF-FB-01. The `score_breakdown` data that could provide actual content metrics is fetched but thrown away. All subsequent quantification uses hardcoded estimates instead. Combined with TF-FB-01, this means the entire `quantify_reject_feedback` method produces fabricated numbers.
- **Suggested fix direction**: Assign the result: `score_breakdown = audit_result.get("score_breakdown", {})` and use its values (e.g., `score_breakdown.get("dialogue_ratio")`) to compute actual deficits.

---

### TF-FB-03: `classify_rejection_feedback` discards `feedback.lower()` result -- IMPORTANT

- **Location**: `feedback_system.py:L794`
- **Description**: Similar to TF-FB-02, line 794 computes `feedback.lower()` but does not assign it. The `feedback` parameter is later used at L836-838 via `structured_feedback.get('feedback')` but never in lowercase form for keyword matching. Only `reason_lower` is used for classification.
- **Evidence**:
  ```python
  # L793-794
  reason_lower = reason.lower() if reason else ""
  feedback.lower() if feedback else ""   # <-- result discarded
  ```
- **Impact**: If classification keywords appear in `feedback` but not in `reason`, the classification falls through to the generic "기타 문제" catch-all (L832-834). This means feedback containing only `feedback`-based context (without keywords in `reason`) always gets the least specific classification. Additionally, if `feedback` is `None`, this line would raise `AttributeError` since `None` has no `.lower()` method -- though the ternary prevents that specific case.
- **Suggested fix direction**: Either assign `feedback_lower = feedback.lower() if feedback else ""` and include it in keyword matching, or remove the dead expression.

---

### TF-FB-04: `get_adaptive_feedback_intensity` returns `pass_threshold`/`feedback_level`/`strictness` but no caller consumes them -- IMPORTANT

- **Location**: `feedback_system.py:L720-L789`; Callers at `stage2_finalizer.py:L1307-1309`, `stage2_validation_pipeline.py:L487-489,L885-887`
- **Description**: The method returns a dict with 4 keys: `pass_threshold`, `feedback_level`, `strictness`, `guidance`. All 3 production callers extract only `adaptive_intensity['guidance']` or `adaptive['guidance']`. The `pass_threshold` (which decreases from 70 to 55 across retries) is never fed back to `ScoringValidator` or `ValidationOrchestrator`, which have their own independent threshold management.
- **Evidence**:
  ```python
  # stage2_finalizer.py:L1309
  intensity_guide = f"...\n{adaptive_intensity['guidance']}"
  # stage2_validation_pipeline.py:L489
  structured_parts.append(f"\n[재시도 {attempt + 1}회차] {adaptive['guidance']}")
  # stage2_validation_pipeline.py:L887
  intensity_guide = f"...\n{adaptive_intensity['guidance']}"
  ```
  The actual pass/fail threshold is controlled by `ValidationOrchestrator.scoring.pass_threshold` and `DirectorGrading._compute_adaptive_threshold()`, which are completely separate code paths.
- **Impact**: The adaptive `pass_threshold` values create a false impression that retry relaxation is happening through FeedbackSystem. In reality, threshold relaxation is managed independently by `ValidationOrchestrator` (L361-365, L1160-1164) and `DirectorGrading` (L477-549). This dual-track design risks future bugs if someone starts consuming the FeedbackSystem thresholds assuming they control validation behavior.
- **Suggested fix direction**: Either remove the unused keys from the returned dict (keeping only `guidance`), or wire the `pass_threshold` into the actual validation pipeline to create a single source of truth for threshold relaxation.

---

### TF-FB-05: 6 of 15 methods (40%) are dead code with no production caller -- IMPORTANT

- **Location**:
  - `build_structured_feedback()`: L32-43 -- 0 production callers
  - `format_feedback_for_prompt()`: L59-76 -- 0 production callers
  - `generate_structured_blueprint_feedback()`: L434-548 -- 0 production callers (115 lines)
  - `build_strong_kind_feedback_legacy()`: L241-310 -- 0 callers at all, not even tests reference it as a caller (70 lines)
  - `classify_rejection_feedback()`: L791-840 -- dormant facade (confirmed by MDH-T2 audit)
  - `simplify_prompt_for_retry()`: L846-885 -- dormant facade (confirmed by MDH-T1 audit)
- **Description**: 40% of FeedbackSystem's surface area (approximately 350 lines) consists of methods that are never invoked in production. `build_strong_kind_feedback_legacy` is particularly notable as it has zero callers anywhere in the codebase including tests. `generate_structured_blueprint_feedback` is a 115-line method designed for Stage 3 Blueprint feedback but is never wired into the Stage 3 pipeline.
- **Impact**: Dead code increases maintenance burden, creates false sense of coverage, and risks accidental activation with incorrect assumptions. The Stage 3 Blueprint feedback path relies on entirely different feedback mechanisms, making `generate_structured_blueprint_feedback` misleading about the actual architecture.
- **Suggested fix direction**: Mark with `# [DEAD]` annotations, or extract to a separate module, or delete after confirming no planned usage.

---

### TF-FB-06: Reverse feedback (Stage3->2) has a minimum failure threshold of 3 that can delay critical structural feedback -- IMPORTANT

- **Location**: `feedback_system.py:L606`; Caller at `stage2_preflight.py:L946`
- **Description**: `generate_reverse_feedback_stage3_to_2` returns empty string if `architect_failures` is fewer than 3. The caller at `stage2_preflight.py:L946` also gates on `len(arc_stage3_failures) >= 3`. This means structural issues identified by Blueprint failures in Stage 3 are only fed back to Stage 2 Arc design after 3 consecutive failures.
- **Evidence**:
  ```python
  # feedback_system.py:L606
  def generate_reverse_feedback_stage3_to_2(self, architect_failures: list = None, arc_no: int = 1) -> str:
      if not architect_failures or len(architect_failures) < 3:
          return ""

  # stage2_preflight.py:L946
  if len(arc_stage3_failures) >= 3:
  ```
- **Impact**: If an Arc has a structural flaw that makes Blueprint design inherently difficult (e.g., conflicting constraints, impossible NPC schedules), the system will waste 2 full Blueprint generation attempts (each potentially with multiple retries) before the reverse feedback kicks in. At the LLM API cost per attempt, this represents significant waste.
- **Suggested fix direction**: Consider a graduated approach: provide hints after 1 failure, warnings after 2, and the full structural feedback at 3. The threshold=3 gate could be made configurable.

---

### TF-FB-07: Forward and reverse feedback can contradict each other in the same prompt -- IMPORTANT

- **Location**: `stage2_preflight.py:L974-982,L984-998`; `feedback_system.py:L554-602,L604-643,L645-714`
- **Description**: Reverse feedback (Stage4->2, Stage3->2) is prepended to `enhanced_context` ahead of forward feedback. This means the LLM receives a prompt like:
  ```
  [Stage4→2] "씬 구조를 단순화하고 집필 난이도를 낮추세요" (L691)
  ...
  [current_feedback from Director] "장면 수 부족. 최소 5개 이상 설계 필요"
  ```
  The reverse feedback says "simplify scene structure" while the forward feedback says "add more scenes". There is no arbitration mechanism to detect or resolve such contradictions.
- **Impact**: The LLM receives contradictory instructions within the same prompt. Since LLMs tend to weight later instructions more heavily (recency bias), the reverse feedback at the top may be overridden by the forward feedback at the bottom, making the reverse feedback system ineffective. Alternatively, the LLM may attempt to satisfy both, producing incoherent results.
- **Suggested fix direction**: Implement a contradiction detection pass before injection. At minimum, when reverse feedback recommends "simplify", the forward feedback's minimum scene count should be adjusted downward to match. Consider a `FeedbackArbiter` that resolves conflicts before final prompt assembly.

---

### TF-FB-08: `build_strong_kind_feedback` focuses on violations[0] only, discarding all other violations -- IMPORTANT

- **Location**: `feedback_system.py:L183-217`
- **Description**: The method takes a `violations` list but only processes `violations[0]`. All remaining violations are silently discarded. The docstring says "단 하나의 핵심 문제" (single core issue) which is intentional, but the problem is that the caller at `stage2_validation_pipeline.py:L891-893` passes the full violations list without any indication that only the first will be used.
- **Evidence**:
  ```python
  # L192: only first violation used
  v = violations[0]
  v_type = v.get("type", "unknown")
  ```
- **Impact**: If violations are not pre-sorted by severity before calling this method, the most critical violation might not be the one selected. The `get_violation_priority` method exists (L45-57) and sorts by type, but `build_strong_kind_feedback` does not call it internally. The caller is responsible for pre-sorting, but no enforcement exists.
- **Suggested fix direction**: Either (a) internally sort violations using `get_violation_priority` before selecting the first one, or (b) accept only a single violation instead of a list to make the API contract explicit.

---

### TF-FB-09: `simplify_prompt_for_retry` hardcodes conflicting thresholds -- INSIGHT

- **Location**: `feedback_system.py:L857,L870,L882`
- **Description**: The method (currently dormant, see TF-FB-05) contains three different length thresholds:
  - L857: "4,500자 이상 확보" (keyword-triggered)
  - L870: "분량 4,500자 이상" (default fallback)
  - L882: "분량 4,000자 이상이면 통과 가능" (PASS conditions)

  Meanwhile `ManuscriptLimits.MIN_LENGTH=4000`, `WARNING_LENGTH=4500`, `TARGET_LENGTH=5000`. The method hardcodes 4,500 and 4,000 instead of referencing these constants, and worse, the PASS condition says 4,000 while the feedback says 4,500 -- creating conflicting signals.
- **Impact**: If this method is ever activated, the LLM receives contradictory guidance: "aim for 4,500" but "4,000 is enough to pass". Currently dormant so no production impact.
- **Suggested fix direction**: Use `ManuscriptLimits` constants and present a single consistent target.

---

### TF-FB-10: `quantify_reject_feedback` keyword matching is sensitive to Korean morphological variations -- INSIGHT

- **Location**: `feedback_system.py:L91,L111,L128,L144,L155,L171`
- **Description**: All 6 quantification sections trigger on simple substring matching against the `reason` string (e.g., `"분량" in reason`, `"대화" in reason`). Korean morphology means the same concept can appear in many surface forms. For example, "대화가 부족합니다" triggers section 2, but "대사가 적습니다" does not even though both mean "insufficient dialogue". Similarly, "자" in L856 of `simplify_prompt_for_retry` would match any reason containing the common Korean particle "자".
- **Impact**: False negatives: legitimate feedback reasons that use synonyms or different morphological forms will miss quantification. False positives: the particle "자" appears in many unrelated Korean words, potentially triggering length feedback inappropriately.
- **Suggested fix direction**: Use a curated set of keyword patterns with word boundary awareness, or classify reasons into categories using a more robust NLP approach before quantification.

---

### TF-FB-11: `_ci_feedback` truncation at 3000 chars can cut structured priority information -- INSIGHT

- **Location**: `stage2_validation_pipeline.py:L908-918`
- **Description**: The ContinuityInspector feedback is assembled from multiple FeedbackSystem outputs: `strong_kind_feedback + focused_context + structured_feedback + banned_items_warning + prev_state_reminder`. This composite string is then truncated at 3000 characters (L917: `_ci_feedback[:3000]`). The `structured_feedback` from `generate_structured_arc_feedback` contains priority-ordered violations, but it is placed third in the concatenation order. If `strong_kind_feedback` and `focused_context` are lengthy, the structured feedback (with its priority-sorted violation list) may be partially or fully truncated.
- **Evidence**:
  ```python
  # L908-911: concatenation order
  _ci_feedback = (
      f"{strong_kind_feedback}\n\n"
      f"{focused_context}{structured_feedback or ''}{banned_items_warning}{prev_state_reminder}"
  )
  # L917: hard truncation
  "message": _ci_feedback[:3000],
  ```
- **Impact**: Critical violations from `generate_structured_arc_feedback` (which are already sorted by priority in `get_violation_priority`) may be truncated. The `strong_kind_feedback` (which focuses on only violations[0]) consumes the beginning of the budget, while the full structured feedback with all categorized violations gets the remainder.
- **Suggested fix direction**: Reverse the concatenation order to put highest-priority content first, or implement smart truncation that preserves the first N violations from each category rather than applying a blind character cut.

---

### TF-FB-12: `generate_reverse_feedback_stage4_to_3` uses keyword-based classification that can produce empty feedback for novel rejection reasons -- IMPORTANT

- **Location**: `feedback_system.py:L554-602`
- **Description**: The method classifies rejection reasons using 4 keyword groups (L570, L576, L582, L588). If the `writer_reject_reason` does not contain any of these Korean keywords, the method produces a feedback string with only the header/footer but no actionable content (the `lines` list will have header lines but no `⚠️` warning blocks).
- **Evidence**:
  ```python
  # L570-588: four if-blocks, no else/fallback
  if "후반" in reason_lower or "요약" in reason_lower or "밀도" in reason_lower:
      ...
  if "분량" in reason_lower or "짧" in reason_lower or "부족" in reason_lower:
      ...
  if "설정" in reason_lower or "모순" in reason_lower or "일관" in reason_lower:
      ...
  if "대화" in reason_lower or "지문" in reason_lower:
      ...
  # No else clause -- novel reasons produce empty body
  ```
- **Impact**: When Stage 4 rejects with a reason like "인물 간 갈등 구조 미흡" (character conflict structure insufficient), none of the keyword groups match. The resulting feedback is just decorative headers with no actual guidance, wasting a reverse feedback opportunity. The `pre_checklist_result` section (L593-599) provides a partial fallback but only if the checklist has failed items.
- **Suggested fix direction**: Add an `else` clause that passes through the raw rejection reason as a generic warning, similar to `classify_rejection_feedback`'s "기타 문제" fallback at L832-834.

---

### TF-FB-13: No feedback loop convergence guarantee -- oscillation is structurally possible -- INSIGHT

- **Location**: `feedback_system.py` (systemic); `stage2_validation_pipeline.py:L878-919`; `stage2_preflight.py:L941-982`
- **Description**: The feedback system has no mechanism to detect or prevent oscillation. Consider this scenario:
  1. Retry 1: Director rejects for "분량 부족" (length shortage)
  2. `quantify_reject_feedback` tells LLM to add 800 characters
  3. Retry 2: LLM adds 800 chars of padding, Director rejects for "후반부 밀도 부족" (lacking density in latter half)
  4. `quantify_reject_feedback` tells LLM to add content to Scene 5-6
  5. Retry 3: LLM redistributes content, Director rejects for "분량 부족" again (because redistribution removed content from earlier scenes)
  6. Cycle repeats

  The system tracks `stage_rejection_history` for reverse feedback triggering but does not analyze whether the same rejection patterns are recurring. The adaptive intensity relaxes thresholds (`pass_threshold` 70->65->55) but as shown in TF-FB-04, this relaxation is not actually consumed by the validation pipeline.
- **Impact**: Retries can oscillate between competing feedback axes (length vs. density vs. scene coverage) without convergence. Each retry consumes LLM API credits. The practical mitigation is the maximum retry count (typically 3-5), which forces termination but at the cost of accepting a suboptimal result.
- **Suggested fix direction**: Track feedback categories across retries and suppress or de-prioritize feedback axes that have already been addressed. If "분량" feedback was given in retry N, and retry N+1 satisfies length but fails on density, do not re-emit "분량" feedback even if length slightly decreased during density improvement. A simple feedback history deduplication per retry session would suffice.

---

### TF-FB-14: `generate_reverse_feedback_stage4_to_2` gracefully degrades but silently ignores non-dict semantic failures -- INSIGHT

- **Location**: `feedback_system.py:L662-664`
- **Description**: The method iterates over `semantic_failures` and skips entries where `not isinstance(failure, dict)`. This is a defensive guard but it silently drops malformed entries without logging.
- **Evidence**:
  ```python
  # L662-664
  for failure in semantic_failures:
      if not isinstance(failure, dict):
          continue
  ```
- **Impact**: If upstream code inadvertently passes string or list entries in `semantic_failures`, they are silently ignored. This is a minor resilience pattern that follows the project's "non-blocking update" convention. Low impact but worth noting for debugging visibility.
- **Suggested fix direction**: Add a `logging.debug` or `logging.info` for skipped non-dict entries to aid future debugging.

---

## 4. Summary Matrix

| ID | Title | Severity | Location | Dead Code? | Production Impact |
|------|-------|----------|----------|------------|-------------------|
| TF-FB-01 | Hardcoded content estimates in quantify_reject_feedback | CRITICAL | L109-168 | No | Fabricated numbers sent to LLM |
| TF-FB-02 | score_breakdown fetched but discarded (no-op expression) | CRITICAL | L110 | No | Root cause of TF-FB-01 |
| TF-FB-03 | feedback.lower() result discarded in classify_rejection_feedback | IMPORTANT | L794 | Yes (dormant) | Classification fallthrough |
| TF-FB-04 | pass_threshold/feedback_level/strictness never consumed | IMPORTANT | L720-789 | Partially | Misleading adaptive thresholds |
| TF-FB-05 | 6 of 15 methods (40%) are dead code | IMPORTANT | Multiple | Yes | Maintenance burden |
| TF-FB-06 | Reverse feedback gate requires 3 failures minimum | IMPORTANT | L606 | No | Delayed structural feedback |
| TF-FB-07 | Forward/reverse feedback contradiction possible | IMPORTANT | Systemic | No | Conflicting LLM instructions |
| TF-FB-08 | build_strong_kind_feedback uses only violations[0] | IMPORTANT | L183-217 | No | May select wrong violation |
| TF-FB-09 | simplify_prompt_for_retry hardcodes conflicting thresholds | INSIGHT | L857-882 | Yes (dormant) | None currently |
| TF-FB-10 | Korean keyword matching is morphologically fragile | INSIGHT | L91-171 | No | False positive/negative triggers |
| TF-FB-11 | 3000-char truncation can cut priority-sorted violations | INSIGHT | VP:L917 | No | Priority information loss |
| TF-FB-12 | Stage4->3 reverse feedback empty for novel reasons | IMPORTANT | L554-602 | No | Wasted reverse feedback |
| TF-FB-13 | No feedback loop convergence guarantee | INSIGHT | Systemic | No | Oscillation risk |
| TF-FB-14 | Non-dict semantic_failures silently skipped | INSIGHT | L662-664 | No | Silent data loss |

Priority grouping:

- **Fix now (CRITICAL)**: TF-FB-01 + TF-FB-02 -- the quantification pipeline produces fabricated data
- **Fix soon (IMPORTANT, live)**: TF-FB-07, TF-FB-08, TF-FB-12, TF-FB-06 -- affect production feedback quality
- **Cleanup (IMPORTANT, dead/dormant)**: TF-FB-04, TF-FB-05, TF-FB-03 -- dead code and misleading APIs
- **Track (INSIGHT)**: TF-FB-09 through TF-FB-14 -- design observations for future improvement

## 5. 핵심 코드 참조 (Appendix)

### A. No-op expression (TF-FB-02)

```python
# feedback_system.py:L110
# This line fetches score_breakdown but discards the result
audit_result.get("score_breakdown", {})
# Should be:
# score_breakdown = audit_result.get("score_breakdown", {})
```

### B. No-op expression (TF-FB-03)

```python
# feedback_system.py:L793-794
reason_lower = reason.lower() if reason else ""
feedback.lower() if feedback else ""   # discarded
# Should be:
# feedback_lower = feedback.lower() if feedback else ""
```

### C. Adaptive intensity -- only `guidance` consumed

```python
# feedback_system.py:L720-742 returns dict with 4 keys
return {
    "pass_threshold": 70,      # NEVER consumed
    "feedback_level": "detailed",  # NEVER consumed
    "strictness": "high",      # NEVER consumed
    "guidance": "...",         # ONLY THIS consumed
}

# stage2_finalizer.py:L1309 -- only guidance used
intensity_guide = f"...\n{adaptive_intensity['guidance']}"
```

### D. Truncation risk in CI feedback assembly

```python
# stage2_validation_pipeline.py:L908-917
_ci_feedback = (
    f"{strong_kind_feedback}\n\n"                     # can be ~500 chars
    f"{focused_context}"                               # can be ~200 chars
    f"{structured_feedback or ''}"                     # can be 1000+ chars (violations)
    f"{banned_items_warning}"                          # variable
    f"{prev_state_reminder}"                           # ~200 chars
)
# Hard cut at 3000 chars -- structured_feedback at position 3 is at risk
_python_advisories.append({
    "message": _ci_feedback[:3000],
})
```

### E. Dead surface inventory

| Method | Lines | Test Coverage | Production Callers |
|--------|-------|---------------|-------------------|
| `build_structured_feedback` | L32-43 | Yes (test_feedback_system.py) | 0 |
| `format_feedback_for_prompt` | L59-76 | Yes (test_feedback_system.py) | 0 |
| `generate_structured_blueprint_feedback` | L434-548 | Yes (test_feedback_system.py) | 0 |
| `build_strong_kind_feedback_legacy` | L241-310 | **No tests** | 0 |
| `classify_rejection_feedback` | L791-840 | Yes (test_feedback_system.py) | 0 (dormant facade) |
| `simplify_prompt_for_retry` | L846-885 | Yes (test_feedback_system.py) | 0 (dormant facade) |
