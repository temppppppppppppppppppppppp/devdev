# TF-ADV: ArcDraftValidator 딥다이브

| Field | Value |
|-------|-------|
| Baseline | bbb00a77 |
| Date | 2026-03-15 |
| Scope | ArcDraftValidator: duplicate items, location continuity, injury state, grant timeline, tactical minimum, 3x call pattern, error handling, LLM/Python split |
| Source files | `modules/domain/agents/arc_draft_validator.py` (905줄), `modules/core/stage2_validation_pipeline.py` (caller) |
| TF Items | 14 (CRITICAL 3 / IMPORTANT 7 / INSIGHT 4) |

---

## 1. Executive Summary

ArcDraftValidator is a purely Python-based pre-validation layer that runs before LLM-based validators (ConsensusValidator, ContinuityInspector). It operates in **advisory mode** -- it cannot REJECT an arc except for dead-NPC appearances. All other findings are warnings/advisories passed to the LLM for final judgment.

Key architectural properties:
- **Stateless**: No mutable instance state; each `validate()` call creates fresh locals. The 3x call pattern is safe.
- **Pure Python**: Zero LLM cost, but relies on regex/keyword pattern matching with inherent limitations.
- **Single REJECT gate**: Only `_validate_dead_npc_appearance` (delegated to StateTracker) can set `valid=False`.

Critical findings center on: (1) substring-based item matching producing false positives for Korean compound words, (2) location continuity checking only the immediately previous arc, enabling multi-arc teleportation, and (3) a dead-code end-marker loop in episode section extraction.

---

## 2. Architecture / Data Flow Diagram (ASCII)

```
Stage2ValidationPipeline.run_validation()
  |
  +--[B1] _run_pre_validation_checks()
  |        |
  |        +-- validate() .................. 1st call (advisory collection)
  |        |     - NO constraint_block       for Consensus/SelfReflector
  |        |     - NO forbidden_items
  |        |
  |        +-- SelfReflector
  |        +-- ConsensusValidator
  |        +-- ArcMapping + AutoCorrector
  |
  +--[B2] _run_flow_and_duplicate_guards()
  |
  +--[B3] _run_draft_validator_full()
  |        |
  |        +-- validate() .................. 2nd call (full validation)
  |        |     - WITH constraint_block
  |        |     - draft_validator_passed flag set here
  |        |
  |        +-- if FAIL + no CRITICAL + has MAJOR:
  |             +-- ArcCorrector.correct()
  |             +-- validate() .............. 3rd call (revalidation)
  |                  - WITH constraint_block
  |
  +--[B4] _run_continuity_inspection()
  |
  +-- Return to Director


validate() internal pipeline:
  +--[0] _validate_dead_npc_appearance()  <-- only REJECT gate
  |       (delegates to StateTracker.check_dead_npc_appearance)
  |
  +--[1] _validate_required_fields()
  |
  +--[2] _validate_duplicate_acquisition()  <-- prev_arcs required
  |       +-- _is_same_item()
  |
  +--[3] _validate_location_continuity()    <-- prev_arcs[-1] only
  |       +-- _locations_compatible()
  |
  +--[4] _validate_injury_continuity()      <-- prev_arcs[-1] only
  |
  +--[5] _validate_grant_timeline()         <-- all prev_arcs
  |
  +--[6] _validate_tactical_doc()
  |       +-- _extract_episode_sections()
  |       +-- _count_tactical_beats()
  |       +-- _check_structural_elements()
  |       +-- _validate_state_checkpoints()
  |
  +--[7] _validate_against_constraints()    <-- constraint_block/forbidden_items
  |
  +-- advisory/REJECT classification
  +-- Return result dict
```

---

## 3. TF Items

### TF-ADV-01: `_is_same_item()` Korean Compound Word False Positives -- CRITICAL

- **Location**: `arc_draft_validator.py:L779-L843`
- **Description**: The `_is_same_item()` method uses substring containment (`shorter in longer`) to determine if two items are the same. For Korean text, this produces systematic false positives because Korean compound nouns commonly embed shorter nouns. The 60% overlap ratio threshold and 2x length ratio guard are insufficient for Korean morphology.
- **Evidence**:
  ```python
  # L818-824
  if len1 >= 3 and len2 >= 3:
      shorter, longer = (item1, item2) if len1 <= len2 else (item2, item1)
      overlap_ratio = len(shorter) / len(longer)
      if overlap_ratio >= 0.6:  # 60% 이상 겹쳐야 함
          if shorter in longer:
              return True
  ```
  Example false positives:
  - "천잠비룡검" (5자) vs "비룡검" (3자) = ratio 0.6 = MATCH (different swords)
  - "흑철장갑" (4자) vs "철장갑" (3자) = ratio 0.75 = MATCH (different armor)
  - "만금통장" (4자) vs "금통장" (3자) = ratio 0.75 = MATCH (different accounts)
  - "계약서" (3자) vs "하도급계약서" (6자) = ratio 0.5 = NO MATCH (correctly rejected by ratio)

  The 0.6 threshold passes too many 3-vs-5 char pairs in Korean.

- **Impact**: False "duplicate acquisition" warnings fed to LLM may cause unnecessary arc regeneration or misleading Director feedback. Since this is advisory-only, the impact is bounded by LLM judgment, but pollutes the signal.
- **Suggested fix direction**: (1) Raise minimum length for substring matching from 3 to 4 chars; (2) For Korean items, require core-match (suffix-stripped) equality rather than substring containment; (3) Consider Jamo-level edit distance as a more linguistically appropriate similarity measure.

---

### TF-ADV-02: Location Continuity Checks Only Immediate Previous Arc -- CRITICAL

- **Location**: `arc_draft_validator.py:L136-L141`, `L285-L310`
- **Description**: `_validate_location_continuity()` only compares the current arc's start location against `prev_arcs[-1]` (the immediately preceding arc). If Arc N ends at location A, Arc N+1 starts at B (detected), but Arc N+2 starts at C with no travel from B, this is NOT detected because the check only looks at Arc N+1's end location. More critically, if `prev_arc.joint_docs.final_location` is empty (common for poorly structured arcs), the check silently passes.
- **Evidence**:
  ```python
  # L136-137 -- only prev_arcs[-1] is used
  location_result = self._validate_location_continuity(arc, prev_arcs[-1])

  # L297 -- empty locations silently pass
  if prev_location and curr_location:
      # ... only executes when both are non-empty
  ```
  The travel detection at L302 is also weak -- it checks only the first 500 chars of tactical_doc for 5 Korean keywords ("이동", "도착", "길을", "향해", "출발"), which can be trivially satisfied by unrelated content.

- **Impact**: Teleportation (location discontinuity across arcs) can go completely undetected if: (a) the previous arc's `final_location` is missing, or (b) any of the 5 travel keywords appears in the first 500 chars of tactical_doc for unrelated reasons. Since location is only checked against the immediate predecessor, cumulative location drift is invisible.
- **Suggested fix direction**: (1) Check location against the most recent arc that HAS a non-empty `final_location`; (2) Require travel keywords to be proximate to the location name; (3) Extend travel keyword search beyond first 500 chars, or at least to the first episode section.

---

### TF-ADV-03: Dead-Code End-Marker Loop in Episode Extraction -- CRITICAL

- **Location**: `arc_draft_validator.py:L710-L716`
- **Description**: The for loop that searches for end markers in episode sections finds a match but takes no action -- the `content` variable is never modified. The loop iterates, finds a marker, and `break`s, but the `content = raw_content` assignment on L711 is never overridden.
- **Evidence**:
  ```python
  # L710-716
  content = raw_content
  for marker in end_markers:
      marker_match = re.search(marker, raw_content)
      if marker_match:
          # 종료 마커 포함하여 내용 유지 (상태 정보도 분량에 포함)
          break  # <-- marker_match found but never used
  ```
  The comment says "keep content including the end marker" but there is no truncation logic. The `marker_match` result is discarded. This means:
  - If the intent was to include content up to and including the marker: NOT IMPLEMENTED
  - If the intent was to keep all content (no truncation): the loop is dead code

  The `end_markers` list (`【화 종료 상태】`, `[종료 상태]`, `---$`) is defined at L695-699 but never functionally used.

- **Impact**: Episode section extraction includes ALL content between episode headers, including content that might belong to metadata sections after end markers. This inflates per-episode character counts, potentially masking short episodes that should trigger warnings. The dead code is confusing for maintainers.
- **Suggested fix direction**: Either (1) remove the dead end-marker loop entirely and update the comment, or (2) implement the intended truncation: `content = raw_content[:marker_match.end()]` or `content = raw_content[:marker_match.start()]`.

---

### TF-ADV-04: Injury Continuity Uses Only `prev_arcs[-1]`, Missing Multi-Arc Recovery -- IMPORTANT

- **Location**: `arc_draft_validator.py:L144-L147`, `L312-L341`
- **Description**: `_validate_injury_continuity()` checks only the immediately previous arc's end state. If a character is severely injured in Arc N, Arc N+1 acknowledges it, but Arc N+2 silently drops the injury, this goes undetected. The recovery keyword check (`회복`, `치료`, `조식`, `휴식`, `요양`) also only examines the first 1000 chars of tactical_doc.
- **Evidence**:
  ```python
  # L332-335
  tactical = arc.get("tactical_doc", "")
  if isinstance(tactical, dict):
      tactical = "\n".join(f"{k}: {v}" for k, v in tactical.items())
  has_recovery = any(kw in tactical[:1000] for kw in ["회복", "치료", "조식", "휴식", "요양"])
  ```
  Note: L332 reads `tactical_doc` raw (not via `_safe_tactical()`), but L333-334 handles the dict case inline -- a minor inconsistency with other methods that use `_safe_tactical()`.

  Also: the whitelist includes "조식" (breakfast), which is likely a typo or overly generous -- eating breakfast does not imply injury recovery.

- **Impact**: Healed injuries can persist or vanish without explanation across a 2+ arc span. The "조식" keyword allows breakfast scenes to suppress injury continuity warnings. Since this is advisory-only, the LLM should catch egregious cases, but the signal is weakened.
- **Suggested fix direction**: (1) Track injury state across all previous arcs, not just the last one; (2) Remove "조식" from recovery keywords or replace with "식사 후 회복" pattern; (3) Use `_safe_tactical()` consistently; (4) Extend search beyond first 1000 chars.

---

### TF-ADV-05: Grant Timeline Lacks Expiry/Revocation Detection -- IMPORTANT

- **Location**: `arc_draft_validator.py:L343-L380`
- **Description**: `_validate_grant_timeline()` accumulates all grants from all previous arcs but has no concept of grant expiry, revocation, or conditional grants. Once granted, an item stays in `all_granted` forever. It also only detects *duplicate* granting, not *premature use* of an ungranted item.
- **Evidence**:
  ```python
  # L348-361 -- grants only accumulate, never expire
  all_granted = set()
  for prev_arc in prev_arcs:
      grants = prev_arc.get("state_constraints", {}).get("grants_received", [])
      if isinstance(grants, list):
          all_granted.update(grants)
      # ... also from tactical_doc patterns
  ```
  The method checks: "is the current arc trying to receive something already granted?" But it does NOT check: "is the current arc using a grant that was revoked?" or "is the current arc exercising a grant before it was given?"

- **Impact**: (1) Revoked permissions (e.g., a character's authority stripped in a later arc) remain in `all_granted`, preventing legitimate re-granting from being flagged. (2) A grant used in Arc 5 that was only given in Arc 7 is invisible to this check. The validator only looks at grants_received duplication, not usage-before-granting.
- **Suggested fix direction**: (1) Add revocation tracking (e.g., check for `grants_revoked` in state_constraints); (2) Cross-reference tactical_doc for grant usage against the timeline of when each grant was received.

---

### TF-ADV-06: 1st Call Missing `constraint_block` Creates Asymmetric Validation -- IMPORTANT

- **Location**: `stage2_validation_pipeline.py:L233-L237` (1st call), `L559-L564` (2nd call), `L639-L644` (3rd call)
- **Description**: The 1st validate() call in `_run_pre_validation_checks()` does NOT pass `constraint_block` or `forbidden_items`. This means Step 7 (`_validate_against_constraints`) is completely skipped in the 1st invocation. Advisory issues collected from the 1st call and fed to Consensus/SelfReflector will never include constraint violations.
- **Evidence**:
  ```python
  # 1st call (L233-237) -- no constraint_block
  draft_result = self.ctx.arc_draft_validator.validate(
      arc=refined_arc,
      prev_arcs=all_refined_arcs,
      state_tracker=self.ctx.state_tracker,
  )

  # 2nd call (L559-564) -- WITH constraint_block
  draft_result = self.ctx.arc_draft_validator.validate(
      arc=refined_arc,
      prev_arcs=all_refined_arcs,
      constraint_block=constraint_block or "",
      state_tracker=self.ctx.state_tracker,
  )
  ```
  The `validate()` method at L164 checks `if constraint_block or forbidden_items or arc.get("_forbidden_items")`, so Step 7 only triggers when at least one of these is provided.

- **Impact**: The SelfReflector and ConsensusValidator receive advisory information that is INCOMPLETE -- missing all constraint violation data. They may approve an arc that violates forbidden item constraints because they were never told about the violations. The 2nd call catches these, but by then the Consensus decision has already been made.
- **Suggested fix direction**: Pass `constraint_block` in the 1st call as well, or document clearly why this is intentionally omitted (e.g., to avoid premature rejection influencing consensus).

---

### TF-ADV-07: `_locations_compatible()` 2-Char Korean Overlap Is Too Permissive -- IMPORTANT

- **Location**: `arc_draft_validator.py:L845-L868`
- **Description**: The location compatibility check extracts all 2+ character Korean substrings and checks for set intersection. This is extremely permissive because common Korean location components like "산", "강", "성", "문" are filtered out (< 2 chars), but 2-char components like "마을", "객잔", "광장", "대전" appear in many different locations.
- **Evidence**:
  ```python
  # L861-866
  loc1_parts = set(re.findall(r"[가-힣]{2,}", loc1))
  loc2_parts = set(re.findall(r"[가-힣]{2,}", loc2))
  if loc1_parts & loc2_parts:
      return True  # any overlap = compatible
  ```
  Examples of false compatibility:
  - "화산파 객잔" vs "숭산 객잔" -- share "객잔" but are completely different locations
  - "남경 대전각" vs "북경 대전각" -- share "대전각" but different cities
  - "태원 마을 입구" vs "낙양 마을 광장" -- share "마을" but different regions

- **Impact**: Location teleportation is masked when two unrelated locations happen to share a common Korean location noun. Given how common 2-char location descriptors are in Korean wuxia fiction, this produces frequent false negatives (missed teleportation).
- **Suggested fix direction**: (1) Require the FIRST (most significant) location component to match, not just any component; (2) Filter out generic location nouns ("마을", "객잔", "광장", etc.) from the intersection check; (3) Use a weighted matching where proper nouns (city/region names) have higher weight than generic descriptors.

---

### TF-ADV-08: Tactical Doc Minimum Can Be Gamed with Repetitive Content -- IMPORTANT

- **Location**: `arc_draft_validator.py:L382-L523`
- **Description**: The tactical_doc validation checks character count, episode section presence, beat counts, and structural elements. However, all checks are keyword-based with no semantic validation. A tactical_doc filled with repeated keywords or boilerplate can pass all checks.
- **Evidence**:
  The minimum per-episode is 300 chars (L446), and the beat count check (L486-495) counts keyword occurrences from a fixed list of 14 structural keywords. A tactical_doc containing "공간 행동 반응 상태 변화 획득 소모 수련 전투 공격 방어" repeated N times will score high on beats while containing zero actual tactical content.

  Similarly, the structural elements check (L590-658) only verifies the PRESENCE of keywords from broad categories:
  - "공간" category: 17 keywords including generic "방", "길", "거리"
  - "행동" category: 14 keywords including "했다", "한다" (extremely common)
  - "상태" category: 12 keywords including "변화", "성장"

  Minimum threshold: `ep_count * 400` chars for the severe warning, `ep_count * 450` for the mild warning. With `DEFAULT_EP_COUNT = 4`, that's 1,600 chars minimum before severe warning.

- **Impact**: An LLM generating low-quality arcs can satisfy all Python-level tactical_doc checks with minimal meaningful content. The actual quality gate is the LLM-based ContinuityInspector/Director, but the validator's score (which influences retry decisions) will be inflated.
- **Suggested fix direction**: (1) Add vocabulary diversity check (unique words / total words ratio); (2) Check for consecutive duplicate sentences; (3) Verify episode sections have distinct content (not copy-pasted); (4) Consider TF-IDF or simple n-gram overlap between episodes.

---

### TF-ADV-09: Error Handling Catches Narrow Exception Types -- IMPORTANT

- **Location**: `stage2_validation_pipeline.py:L250`, `L565`
- **Description**: Both the 1st and 2nd validate() call sites catch `(RuntimeError, ValueError, OSError)`. This misses `TypeError` (common with None arguments or malformed dicts), `KeyError` (missing expected keys in arc data), and `AttributeError` (when state_tracker is a mock or unexpected type).
- **Evidence**:
  ```python
  # 1st call (L250)
  except (RuntimeError, ValueError, OSError) as dv_err:
      logging.warning(f" [DraftValidator] 스킵: {str(dv_err)[:50]}")

  # 2nd call (L565)
  except (RuntimeError, ValueError, OSError) as _dv_err:
      logging.warning(f"[G6] DraftValidator 호출 실패 — fail-closed: {_dv_err!s:.100}")
  ```
  The 1st call silently SKIPS on error (fail-open). The 2nd call returns fail-closed (`valid=False, score=0`). This asymmetry means: a TypeError in the 1st call crashes the entire pipeline (unhandled), while the same error in the 2nd call is caught and treated as validation failure.

- **Impact**: Uncaught `TypeError`/`KeyError`/`AttributeError` in the 1st call can crash the entire Stage 2 pipeline. In the 2nd call, the same errors are properly handled. The 1st call's fail-open behavior also means a broken validator silently produces no advisories.
- **Suggested fix direction**: (1) Use `Exception` or at minimum add `TypeError, KeyError, AttributeError` to the catch list; (2) Align the 1st call's error handling with the 2nd call (fail-closed or at least logged at WARNING level with clear indication).

---

### TF-ADV-10: `_validate_against_constraints()` Double-Penalty for Same Item -- IMPORTANT

- **Location**: `arc_draft_validator.py:L757-L776`
- **Description**: When a forbidden item appears in BOTH `items_acquired` AND `tactical_doc`, the validator applies the penalty twice (35 + 35 = 70) and adds two separate critical issues for the same item.
- **Evidence**:
  ```python
  # L761-766 -- first check: items_acquired
  for item in items_acquired:
      if self._is_same_item(forbidden, item):
          critical.append(f"제약 위반: 금지 아이템 '{forbidden}' 획득 시도")
          penalty += 35
          break

  # L768-775 -- second check: tactical_doc (independent, no dedup)
  if forbidden in tactical:
      if any(kw in tactical for kw in ["획득", "얻", "손에"]):
          acq_pattern = rf"{re.escape(forbidden)}[를을]?\s*(?:획득|얻|받|손에\s*넣|입수)"
          if re.search(acq_pattern, tactical):
              critical.append(f"제약 위반: 금지 아이템 '{forbidden}' 획득 시도 (tactical_doc)")
              penalty += 35
  ```
  The two checks are independent -- finding the item in `items_acquired` does NOT skip the `tactical_doc` check. An arc that properly lists a forbidden item in both structured data and narrative text gets double-penalized.

- **Impact**: Score is over-penalized (70 instead of 35), which may trigger unnecessary ArcCorrector intervention or inflate advisory severity sent to the LLM. Since `items_acquired` is typically extracted from `tactical_doc` content, most violations will hit both paths.
- **Suggested fix direction**: Use a `found_forbidden` set to track already-detected violations and skip the tactical_doc check for items already found in `items_acquired`.

---

### TF-ADV-11: Regex Acquire Patterns Can Match Inside Narrative Dialogue -- INSIGHT

- **Location**: `arc_draft_validator.py:L46-L50`
- **Description**: The `acquire_patterns` regex matches Korean item-acquisition patterns in tactical_doc text. However, these patterns can match inside quoted dialogue or hypothetical/conditional statements, leading to false positive item detection.
- **Evidence**:
  ```python
  # L47
  rf"([가-힣A-Za-z0-9]{{0,20}}(?:{_suffix_group}))[를을]?\s*(?:획득|얻|받|손에\s*넣|입수)",
  ```
  This matches:
  - `"그 비급을 획득하면 안 된다"` (conditional/prohibition -- NOT acquisition)
  - `"적이 천마검을 얻었다"` (enemy acquisition, not protagonist)
  - `"전설에 따르면 용천검을 손에 넣은 자는..."` (lore reference)

  Items extracted by these patterns are added to `current_items` (L266-271) and then checked against `all_acquired` for duplicates.

- **Impact**: False duplicate warnings when narrative text mentions an already-acquired item in non-acquisition context (dialogue, flashback, enemy actions, conditional statements). This is partially mitigated by the advisory-only nature, but adds noise.
- **Suggested fix direction**: (1) Exclude content within quotation marks from pattern matching; (2) Add negative lookbehind for negation words ("안", "못", "불가"); (3) Verify the subject of the acquisition sentence matches the protagonist.

---

### TF-ADV-12: `_validate_state_checkpoints()` Has Commented-Out Logic -- INSIGHT

- **Location**: `arc_draft_validator.py:L525-L551`
- **Description**: The `state_mismatches` list is initialized but never populated. The start-state check at L540-542 has its action commented out with `pass` and a BUG-4 note. The method effectively only checks for missing state keywords.
- **Evidence**:
  ```python
  # L540-542
  if i > 0:
      has_start_state = any(kw in content for kw in ["시작 상태", "이전", "직전", "에서 이어"])
      if not has_start_state and len(content) > 300:
          pass  # [BUG-4] 복잡한 연속성 검증은 LLM에 위임

  # L528 -- initialized but never populated
  state_mismatches = []
  ```

- **Impact**: The `state_mismatches` key in the return dict is always empty. Callers checking `checkpoint_result.get("state_mismatches")` (L519-521) will never trigger the 3-point penalty per mismatch. This is effectively dead validation logic.
- **Suggested fix direction**: Either implement the state mismatch detection or remove the dead code and the corresponding penalty logic at L519-521.

---

### TF-ADV-13: 1st Call Logs "검증 통과" Unconditionally -- INSIGHT

- **Location**: `stage2_validation_pipeline.py:L247`
- **Description**: The 1st validate() call always logs "사전 검증 통과!" regardless of the result, because the 1st call is advisory-collection-only. But the log message is misleading.
- **Evidence**:
  ```python
  # L247 -- always executed after validate() returns (outside the if-advisory block)
  logging.info("✅ [DraftValidator] 사전 검증 통과!")
  # [S2-P1-4] draft_validator_passed는 2차 호출(L256)에서만 설정
  # 1차 호출은 Consensus용 advisory 수집 전용
  ```
  Even if `draft_result["valid"]` is `False` (dead NPC REJECT), this log line still says "통과" (passed). The comment at L248-249 explains the intent but the log is confusing for debugging.

- **Impact**: Log analysis during debugging will show "DraftValidator passed" even when the validator found critical issues. This is a pure observability issue, not a logic bug.
- **Suggested fix direction**: Change log message to "DraftValidator advisory 수집 완료" or gate it on `draft_result["valid"]`.

---

### TF-ADV-14: Duplicate Acquisition Collects from Multiple Sources Without Deduplication -- INSIGHT

- **Location**: `arc_draft_validator.py:L222-L283`
- **Description**: `_validate_duplicate_acquisition()` collects items from three sources per arc: `state_constraints.items_acquired/protagonist_items`, `joint_docs.physical_inventory`, and tactical_doc regex extraction. For the current arc, items from `state_constraints` and tactical_doc regex are combined into `current_items`. This can produce self-duplicates: if the same item appears in both `state_constraints` and is also regex-matched from `tactical_doc`, it appears twice in `current_items`.
- **Evidence**:
  ```python
  # L258-271
  current_items = _csc_dup.get("protagonist_items") or _csc_dup.get("items_acquired", [])
  # ...
  # tactical_doc에서도 획득 패턴 추출
  for pattern in self.acquire_patterns:
      matches = re.findall(pattern, tactical)
      for m in matches:
          # ...
          current_items.append(item)  # <-- no dedup against existing current_items

  # L274-281 -- each current_item is checked against all_acquired
  for item in current_items:
      for prev_item in all_acquired:
          if self._is_same_item(item, prev_item):
              critical.append(...)  # <-- can fire multiple times for same item
  ```
  If "천마검" appears in both `items_acquired` and is regex-matched from tactical_doc, the duplicate check runs twice against `all_acquired`, potentially generating two identical warnings.

- **Impact**: Minor: duplicate advisory messages for the same item. The score penalty could be inflated (30 points per duplicate detection).
- **Suggested fix direction**: Deduplicate `current_items` (convert to set) before running the comparison loop against `all_acquired`. Also deduplicate `all_acquired` entries that come from multiple sources within the same prev_arc.

---

## 4. Summary Matrix

| ID | Title | Severity | Category | Line(s) | Stateless-safe | Advisory-only |
|----|-------|----------|----------|---------|---------------|---------------|
| TF-ADV-01 | Korean compound word FP in `_is_same_item` | CRITICAL | Duplicate Item | L779-843 | Yes | Yes |
| TF-ADV-02 | Location check only uses prev_arcs[-1] | CRITICAL | Location Continuity | L136-141, L285-310 | Yes | Yes |
| TF-ADV-03 | Dead-code end-marker loop | CRITICAL | Tactical Doc | L710-716 | Yes | Yes |
| TF-ADV-04 | Injury check single-arc lookback | IMPORTANT | Injury State | L312-341 | Yes | Yes |
| TF-ADV-05 | Grant timeline no expiry/revocation | IMPORTANT | Grant Timeline | L343-380 | Yes | Yes |
| TF-ADV-06 | 1st call missing constraint_block | IMPORTANT | 3x Call Pattern | Pipeline L233 | N/A | Yes |
| TF-ADV-07 | Location 2-char Korean overlap too permissive | IMPORTANT | Location Continuity | L845-868 | Yes | Yes |
| TF-ADV-08 | Tactical doc minimum gameable | IMPORTANT | Tactical Doc | L382-523 | Yes | Yes |
| TF-ADV-09 | Narrow exception catch types | IMPORTANT | Error Handling | Pipeline L250, L565 | N/A | N/A |
| TF-ADV-10 | Double penalty for same forbidden item | IMPORTANT | Constraints | L757-776 | Yes | Yes |
| TF-ADV-11 | Regex matches dialogue/conditionals | INSIGHT | Duplicate Item | L46-50 | Yes | Yes |
| TF-ADV-12 | State checkpoint logic commented out | INSIGHT | Tactical Doc | L525-551 | Yes | Yes |
| TF-ADV-13 | 1st call misleading "통과" log | INSIGHT | 3x Call Pattern | Pipeline L247 | N/A | N/A |
| TF-ADV-14 | Current items no dedup before check | INSIGHT | Duplicate Item | L258-281 | Yes | Yes |

### Severity Distribution
- **CRITICAL**: 3 (items that produce incorrect validation results)
- **IMPORTANT**: 7 (items that weaken validation coverage or have error-handling gaps)
- **INSIGHT**: 4 (code hygiene, minor logic, observability)

### Investigation Points Answered
1. **Duplicate Item Detection**: Regex pattern extraction + `_is_same_item()` substring matching. FP risk from Korean compound words (TF-ADV-01), dialogue context (TF-ADV-11), self-duplication (TF-ADV-14).
2. **Location Continuity**: Single-arc lookback with permissive Korean overlap (TF-ADV-02, TF-ADV-07). Teleportation easily missed.
3. **Injury State Tracking**: Single-arc lookback, "조식" in recovery whitelist, inconsistent `_safe_tactical` usage (TF-ADV-04).
4. **Grant Timeline**: Accumulate-only with no expiry/revocation. Detects duplicate granting but not premature use (TF-ADV-05).
5. **Tactical Doc Minimum**: 400*ep_count chars severe / 450*ep_count mild. Keyword-only structural checks, easily gamed (TF-ADV-08). Dead end-marker code (TF-ADV-03).
6. **3x Call Pattern**: SAFE -- validator is stateless. But 1st call missing constraints is an asymmetry (TF-ADV-06), and misleading log (TF-ADV-13).
7. **Error Handling**: Narrow catch types, asymmetric fail-open vs fail-closed between 1st and 2nd calls (TF-ADV-09).
8. **LLM vs Python Split**: All 7 checks are pure Python. Dead NPC check delegates to StateTracker (also Python). The LLM gate is ContinuityInspector/UnifiedArcValidator downstream. Python blind spots: semantic context, dialogue vs narration, conditional statements.

---

## 5. 핵심 코드 참조 (Appendix)

### A. `_is_same_item()` Core Logic (L779-843)
```python
def _is_same_item(self, item1: str, item2: str) -> bool:
    # Exact match: always True
    if item1 == item2: return True
    # Parenthetical normalization (e.g., "계좌 (220억)" vs "계좌 (300억)")
    _item1_base = re.sub(r"\s*\([^)]*\)", "", item1).strip()
    _item2_base = re.sub(r"\s*\([^)]*\)", "", item2).strip()
    if _item1_base == _item2_base and len(_item1_base) >= 4: return True
    # Length ratio > 2.0 → different
    # Substring containment: both >= 3 chars, overlap >= 60%
    # Suffix-stripped core comparison: exact match only, ratio <= 1.5
```

### B. 3x Call Sites in Pipeline
```
1st: _run_pre_validation_checks() L233  -- advisory collection, no constraints
2nd: _run_draft_validator_full()  L559  -- full validation, with constraints
3rd: _run_draft_validator_full()  L639  -- revalidation after ArcCorrector
```

### C. Validation Score Penalties
| Check | Max Penalty | Gate |
|-------|------------|------|
| Dead NPC (Step 0) | 100 per NPC | REJECT |
| Required fields (Step 1) | 10 per field | Advisory |
| Important fields (Step 1) | 5 per field | Advisory |
| Duplicate items (Step 2) | 30 per item | Advisory |
| Location continuity (Step 3) | 10 | Advisory |
| Injury continuity (Step 4) | 5 | Advisory |
| Grant timeline (Step 5) | 25 per grant | Advisory |
| Tactical doc severe (Step 6) | 25 | Advisory |
| Tactical doc mild (Step 6) | 10 | Advisory |
| Missing episodes (Step 6) | 15 | Advisory |
| Short episodes (Step 6) | 3 per ep | Advisory |
| Balance (Step 6) | 5 | Advisory |
| Order mismatch (Step 6) | 5 | Advisory |
| Low beats (Step 6) | 2 per ep | Advisory |
| ep_count mismatch (Step 6) | 5 | Advisory |
| Missing checkpoints (Step 6) | 2 per ep | Advisory |
| State mismatches (Step 6) | 3 per ep | Dead code |
| Constraint violation (Step 7) | 35 per item | Advisory |

### D. Dead-Code Inventory
| Location | Description | Risk |
|----------|-------------|------|
| L710-716 | End-marker loop (no-op) | Inflated episode lengths |
| L525-551 | State mismatches (always empty) | Missing penalty |
| L695-699 | End-marker pattern list (unused) | Dead code |
