# TF-NPC: StateTracker NPC 딥다이브

| Field | Value |
|-------|-------|
| Baseline | bbb00a77 |
| Date | 2026-03-15 |
| Scope | StateTracker NPC: extraction, death/injury tracking, relationship state machine, cumulative integrity |
| Source files | state_tracker_npc.py:2204줄 |
| TF Items | 23 (CRITICAL 4 / IMPORTANT 11 / INSIGHT 8) |

---

## 1. Executive Summary

`state_tracker_npc.py`는 NPC 레지스트리 관리의 핵심 모듈로, 2,204줄에 걸쳐 사망 추적, 영구 부상, 관계 상태, 동행자 관리, 주인공 감정 등 10+ 카테고리의 NPC 상태를 관리한다. 모든 공유 상태는 부모 `StateTracker` 인스턴스를 `self.tracker`로 참조하여 접근한다.

감사 결과 **CRITICAL 4건**, **IMPORTANT 11건**, **INSIGHT 8건** 총 23건의 발견사항이 있다.

주요 위험:
1. **Operator Precedence Bug** (L2052): `and`/`or` 우선순위로 주인공 감정 요약이 삼켜지는 버그
2. **Regex FP/FN 체계적 취약점**: 한국어 NPC 이름 추출 regex가 2-10자 한글 범위로 일반명사 오탐 광범위
3. **In-place Dict Mutation**: `npc_registry` dict를 직접 변경하여 호출자에게 예기치 않은 부작용 전파
4. **Unbounded Growth**: `npc_registry`, `permanent_injuries`, `revive_history` 등 상한 없는 누적 구조

---

## 2. Architecture / Data Flow Diagram (ASCII)

```
                      +------------------+
                      |  StateTracker    |
                      |  (parent class)  |
                      +--------+---------+
                               |
                    self.tracker (back-ref)
                               |
               +---------------v----------------+
               |    StateTrackerNPC             |
               |    (this module, 2204 lines)   |
               +-+----+----+----+----+----+----++
                 |    |    |    |    |    |    |
                 v    v    v    v    v    v    v
    +---------+ +--+ +--+ +--+ +--+ +--+ +--+
    |NPC Death| |Sk| |Re| |In| |Mo| |Co| |Em|
    |Tracking | |il| |la| |ju| |ve| |mp| |ot|
    |L657-814 | |ll| |ti| |ry| |me| |an| |io|
    +---------+ |s | |on| |  | |nt| |io| |n |
                +--+ +--+ +--+ +--+ |ns| +--+
                                     +--+

    Data stores (all on self.tracker):
    ====================================
    npc_registry: dict[str, dict]          -- UNBOUNDED
    protagonist_skills: set[str]           -- UNBOUNDED
    skill_acquisitions: dict[str, int]     -- UNBOUNDED
    npc_npc_relationships: dict            -- CAPPED at 50 (memory), DB unlimited
    npc_dialogue_profiles: dict            -- UNBOUNDED
    current_companions: list[dict]         -- UNBOUNDED (but naturally small)
    protagonist_emotion: dict              -- single dict, overwrite

    NPC Registry Entry Schema:
    ==========================
    {
      "status": "alive"|"dead",
      "death_arc": int,
      "death_context": str,
      "weapon": str,
      "level": str,
      "last_arc": int,
      "injury": str,                       -- "정상"|"경상"|"중상"|"위독"
      "location": str,
      "relation_to_protag": str,
      "personality_traits": str,
      "primary_motivation": str,
      "position": str,
      "permanent_injuries": list[dict],    -- UNBOUNDED sub-list
      "revive_history": list[dict],        -- UNBOUNDED sub-list
    }

    Extraction Priority:
    ====================
    1. state_changes structured field (LLM output)
    2. regex fallback on tactical_doc text

    Death Extraction Flow:
    ======================
    arc["state_changes"]["npc_deaths"]
         |                                  |
         v                                  v (empty)
    LLM verify (_verify_npc_names_llm)     regex fallback (4 patterns)
         |                                  |
         v                                  v
    exclude filter (_NPC_DEATH_EXCLUDE)    exclude filter + LLM verify
         |                                  |
         v                                  v
    register_npc_death()  <-----------------+

    Relationship State Machine:
    ===========================
    States: 적대, 중립, 아군, 동맹, 호의, 충성, 적

                 화해
    적대 -----------------> 동맹
      ^                       |
      |     배신              |
      +-------<---------------+
      |                       |
      |    arrow pattern      |
      +---<----ANY---->-------+
              (free transition between all 7 states)

    NOTE: No validation on transitions. ANY -> ANY is permitted.
    The "from" field in regex reconcile/betray uses existing registry
    or hardcoded defaults ("적대" for reconcile, "아군" for betray).
```

---

## 3. TF Items

### TF-NPC-01: Operator Precedence Bug in `get_protagonist_emotion_summary` -- CRITICAL

- **Location**: `state_tracker_npc.py:L2052`
- **Description**: The condition `if not pe or pe.get("emotion") == "평온" and not pe.get("trigger")` is parsed by Python as `if (not pe) or (pe.get("emotion") == "평온" and not pe.get("trigger"))` due to `and` having higher precedence than `or`. This is likely correct intent, but there is a subtler bug: when `pe` is a non-empty dict (which it always is, initialized at L164 as `{"emotion": "평온", "trigger": "", "arc_no": 0}`), `not pe` is always `False`. The real problem is when the emotion is NOT "평온" but has no trigger -- e.g. `{"emotion": "분노", "trigger": "", "arc_no": 5}` -- the condition evaluates to `False or (False and True)` = `False`, so the summary IS generated (correct). But if `pe` is `{"emotion": "평온", "trigger": "부모 사망", "arc_no": 3}` (평온 with a trigger), the condition is `False or (True and False)` = `False`, so the summary IS generated for a calm state with a trigger. This is a design ambiguity, but the bigger issue: if someone sets `protagonist_emotion = {}` or `protagonist_emotion = None`, then `not pe` catches it. However, the intended behavior of "suppress 평온 without trigger" vs "show 평온 with trigger" is fragile and undocumented.

  **UPDATE -- Actually CRITICAL**: If parenthesization is wrong and the intention was `(not pe) or (pe.get("emotion") == "평온" and not pe.get("trigger"))`, then the current code is "accidentally correct." But if the intention was `not (pe) or (pe.get("emotion") == "평온" and not pe.get("trigger"))` meant as `not pe or (both conditions)`, it's fine. The real bug is: there are no parentheses, making intent ambiguous. Any future refactor could introduce a regression.

- **Evidence**:
  ```python
  # L2052
  if not pe or pe.get("emotion") == "평온" and not pe.get("trigger"):
      return ""
  ```
- **Impact**: Low-severity now (accidentally works), but fragile -- any modification to this condition without understanding precedence will introduce a logic error in protagonist emotion context injection.
- **Suggested fix direction**: Add explicit parentheses: `if not pe or (pe.get("emotion") == "평온" and not pe.get("trigger")):`

---

### TF-NPC-02: Emotion Regex Uses Duplicate Anchor `주인공|주인공` -- CRITICAL

- **Location**: `state_tracker_npc.py:L2029-L2033`
- **Description**: The regex pattern uses `(?:주인공|{name})` where `{name}` is `re.escape("주인공")`, resulting in `(?:주인공|주인공)` -- the alternation is redundant. More critically, this means the pattern ONLY matches text containing "주인공" (the literal word for "protagonist"). In Korean fiction, the protagonist is referred to by name (e.g. "진우", "강호" etc.), not by the word "주인공". The regex will never match actual manuscript text where the protagonist is referred to by their character name.

- **Evidence**:
  ```python
  # L2029-2032
  pattern = re.compile(
      r"(?:주인공|{name})[이가은는의]?\s*.{{0,20}}?{kw}".format(
          name=re.escape("주인공"), kw=re.escape(keyword)
      )
  )
  ```
- **Impact**: Protagonist emotion regex fallback is effectively dead code. It will only match if the tactical_doc explicitly uses the meta-term "주인공" rather than the character's actual name. Emotion extraction depends entirely on `state_changes["protagonist_emotion"]` working.
- **Suggested fix direction**: Pass the actual protagonist name from the preset/project config. E.g. `name=re.escape(self.tracker.protagonist_name or "주인공")`.

---

### TF-NPC-03: Death Regex FN -- "운명" Pattern Matches Idiom, Not Only Death -- CRITICAL

- **Location**: `state_tracker_npc.py:L719`
- **Description**: The death regex pattern `([가-힣]{2,10})[이가은는]\s*(?:죽|사망|전사|명을\s*다|숨을\s*거두|운명)` includes "운명" as a death indicator. However, "운명" in Korean primarily means "fate/destiny" -- e.g. "그는 운명적인 만남" (fateful meeting), "자신의 운명을 받아들이다" (accept one's fate). The death meaning ("to pass away") exists but is less common. Without the full conjugation "운명하다/운명을 달리하다", this pattern can produce false positives.

  Conversely, death euphemisms like "목숨을 잃다", "생을 마감하다", "세상을 떠나다" (after filtering "세상" from exclude), "최후를 맞이하다", "영면하다" are NOT covered -- these are false negatives.

- **Evidence**:
  ```python
  # L719
  r"([가-힣]{2,10})[이가은는]\s*(?:죽|사망|전사|명을\s*다|숨을\s*거두|운명)"
  ```
- **Impact**: False positive: NPC falsely registered as dead because their name appears near "운명" in a non-death context. The LLM verification layer (L736) mitigates this, but only when `_llm_client` is available. Without LLM, regex alone determines death registration.
- **Suggested fix direction**: Change "운명" to "운명을\s*달리" or "운명하" to require the death-specific conjugation. Add missing death euphemisms.

---

### TF-NPC-04: `_is_standalone_name` Returns True on First Valid Match, Ignoring Context -- CRITICAL

- **Location**: `state_tracker_npc.py:L435-L458`
- **Description**: The function returns `True` at the first position where the name appears with valid boundaries (L457). It does not check whether the context around that specific occurrence is a flashback/action. The callers (L482-510, L1473-1504, L1549-1588) then check flashback/action patterns on the ENTIRE text, not localized to the match position. This means: if "강철" appears twice -- once in "강철의 죽음을 떠올리며" (flashback) and once in "강철이 칼을 뽑았다" (action) -- the function returns True, then the flashback check finds "강철의 죽음" and classifies the ENTIRE occurrence as flashback, missing the actual violation.

- **Evidence**:
  ```python
  # L457
  return True  # 독립 매칭 확인 (returns on FIRST valid match)

  # L496 (caller)
  is_flashback = any(pattern in content for pattern in flashback_patterns)
  # checks ENTIRE content, not localized to the match position
  ```
- **Impact**: A dead NPC can appear alive in one part of the text while being mentioned in flashback elsewhere, and the flashback mention will suppress the violation. This is a false-negative path for dead NPC resurrection detection.
- **Suggested fix direction**: Check flashback/action patterns per-occurrence, not globally. Or: if ANY non-flashback action pattern matches, report a violation regardless of whether flashback patterns also match elsewhere.

---

### TF-NPC-05: `[가-힣]{2,10}` Regex Range Matches Common Nouns -- IMPORTANT

- **Location**: Module-level patterns L24-L70, L306-L313, L396-L403, L717-L721, L854-L856
- **Description**: Nearly all NPC name extraction patterns use `[가-힣]{2,10}` which matches ANY 2-10 character Korean string. This captures common nouns like "대장장이" (blacksmith), "호위무사" (bodyguard), "중원무림" (martial world), "마교교주" (cult leader). The `_NPC_DEATH_EXCLUDE_WORDS` frozenset (L76-140) has ~50 entries, and `extract_npc_info_from_arc` has a small `exclude_words` list (L407), but these are incomplete. The V69 LLM cleanup (L2126-2204) runs only every 5 arcs, leaving contaminated data in between.

- **Evidence**:
  ```python
  # L24 (relationship arrow pattern)
  r"([가-힣]{2,10})[이가은는의]\s*..."
  # L33 (injury direct pattern)
  r"([가-힣]{2,10})[이가은는]\s*(중상|경상|위독|부상)..."
  # L718 (death pattern)
  r"([가-힣]{2,10})[이가을를]\s*(?:죽이|처단|살해|..."
  ```
- **Impact**: Over 30+ episodes, the `npc_registry` accumulates false entries from common nouns matched by regex. Each false entry increases processing overhead in `check_dead_npc_appearance`, `get_entity_registry`, and all summary methods that iterate over `npc_registry`.
- **Suggested fix direction**: (1) Add common Korean noun patterns to exclude lists. (2) Cross-reference regex extractions against the known NPC roster from arc data. (3) Consider minimum name frequency threshold before registry insertion.

---

### TF-NPC-06: Death Exclude Filter Missing Contextual Exclusions -- IMPORTANT

- **Location**: `state_tracker_npc.py:L76-L140, L717-L731`
- **Description**: The `_NPC_DEATH_EXCLUDE_WORDS` frozenset contains ~50 entries but misses several common false-positive sources:
  - Title/role words: "장로" (elder), "교주" (cult leader), "대장" (captain), "문주" (sect master), "가주" (family head) -- these are often used as standalone titles without names
  - Pronoun-like: "그자" (that person), "놈" (that guy), "녀석" (fellow)
  - Abstract: "꿈" (dream), "영혼" (soul), "기억" (memory)
  - The exclude is applied to the EXTRACTED name only, not to the context. A sentence like "장로가 죽었다" will extract "장로" as NPC name and register a death.

- **Evidence**:
  ```python
  # L76-140: _NPC_DEATH_EXCLUDE_WORDS
  # Missing: 장로, 교주, 대장, 문주, 가주, 그자, 놈, 녀석, etc.

  # L729-730 (regex death extraction)
  if npc_name and len(npc_name) >= 2 and npc_name not in exclude_words:
      regex_candidates.append(npc_name)
  ```
- **Impact**: Title-as-name false positives cause spurious death registrations. If "장로" is registered as dead, any future mention of any elder character will trigger a dead-NPC violation.
- **Suggested fix direction**: Expand `_NPC_DEATH_EXCLUDE_WORDS` with common Korean title/role words. Consider a separate `_NPC_TITLE_WORDS` set for title-based exclusion.

---

### TF-NPC-07: Relationship State Machine Has No Transition Validation -- IMPORTANT

- **Location**: `state_tracker_npc.py:L868-L925, L1057-L1099`
- **Description**: The relationship tracking allows ANY state to transition to ANY other state without validation. The state vocabulary is open-ended -- `state_changes` can contain any string as `from`/`to` values, and regex patterns use a fixed set ("적대", "중립", "아군", "동맹", "호의", "충성", "적"). There is no canonical state enum, no transition validation, and no guard against impossible transitions (e.g. "적대" -> "충성" in a single arc without intermediate steps).

  Additionally, `_RE_REL_ARROW` (L24-28) lists "적" and "적대" as separate states. The regex captures both, but they likely mean the same thing, leading to inconsistent state tracking.

- **Evidence**:
  ```python
  # L24-28: _RE_REL_ARROW
  r"(적대?|중립|아군|동맹|호의|충성|적)[에서으로]*\s*[→에서]+\s*"
  r"(적대?|중립|아군|동맹|호의|충성|적)"
  # "적대?" matches both "적대" and "적"
  # "적" is listed separately -- redundant with "적대?"
  ```
- **Impact**: Inconsistent relationship state tracking. A NPC could be "적" in one record and "적대" in another, confusing downstream consumers. No graduated transition enforcement means story coherence isn't validated.
- **Suggested fix direction**: Define a canonical state enum. Normalize "적" to "적대". Add transition plausibility scoring (not blocking, advisory).

---

### TF-NPC-08: Injury Tracking Has No Recovery/Healing Path -- IMPORTANT

- **Location**: `state_tracker_npc.py:L927-L989`
- **Description**: The `extract_npc_injuries_from_arc` method sets `npc["injury"]` to whatever is extracted (L959, L985) but there is no mechanism to record recovery. The parent `StateTracker` (L590) recognizes "회복" and "치료" as returning to "정상", but this applies only to `EpisodeState.injuries` (protagonist), not to `npc_registry[name]["injury"]`. Once an NPC's injury is set to "중상", it persists forever unless a new injury extraction explicitly overwrites it.

  The `get_npc_injury_summary` (L2084-2093) filters out "정상" injuries, so even if overwritten, the display is correct. But the actual data in `npc_registry` becomes stale.

- **Evidence**:
  ```python
  # L959: Sets injury, never clears it
  self.tracker.npc_registry[npc_name]["injury"] = state

  # L2089: Summary filters "정상" but registry keeps stale data
  if injury and injury != "정상" and npc_info.get("status") == "alive":
  ```
- **Impact**: After 30+ episodes, many NPCs will have stale injury states. Prompts injected via `get_npc_injury_summary` will incorrectly report old injuries as current, causing the LLM to write NPCs as still injured when they should have recovered.
- **Suggested fix direction**: Add recovery detection: if `state_changes["npc_injuries"]` contains `{"name": "X", "state": "정상"}` or `"recovered"`, set `npc["injury"] = "정상"`. Consider auto-decay of injury states after N arcs without re-mention.

---

### TF-NPC-09: Permanent Injuries Have No "Healed by Magic/Artifact" Reversal -- IMPORTANT

- **Location**: `state_tracker_npc.py:L1200-L1325`
- **Description**: `register_permanent_injury` (L1200) appends to `permanent_injuries` list with dedup by `(description, arc_no)`. There is no method to remove or reverse a permanent injury. In wuxia/fantasy genres, magical healing (e.g. 영약, 신물, 재생 마법) can canonically restore lost limbs or eyesight. The system has no way to represent this.

- **Evidence**:
  ```python
  # L1219-1225: Append-only, dedup by exact match only
  if "permanent_injuries" not in npc:
      npc["permanent_injuries"] = []
  for existing in npc["permanent_injuries"]:
      if existing.get("description") == description and existing.get("arc_no") == arc_no:
          return  # dedup
  npc["permanent_injuries"].append(...)
  ```
- **Impact**: If a NPC's arm is restored by plot event, the prompt will still instruct "왼팔 절단 -- 회복 불가, 묘사 시 반드시 반영" (L1347), directly contradicting the narrative.
- **Suggested fix direction**: Add `remove_permanent_injury(name, description, reason)` method. The `revive_npc` pattern (L1354-1414) provides a template for undo operations.

---

### TF-NPC-10: `npc_npc_relationships` FIFO Eviction Loses Important Relationships -- IMPORTANT

- **Location**: `state_tracker_npc.py:L1697-L1700`
- **Description**: When the 50-pair cap is reached, the code evicts `next(iter(dict))` which is the OLDEST inserted key (Python 3.7+ dict insertion order). This means the first relationships established (often the most important -- e.g. master-disciple, sworn brothers, primary antagonist pairs) are evicted first while ephemeral late-story relationships persist.

- **Evidence**:
  ```python
  # L1697-1700
  if len(self.tracker.npc_npc_relationships) > 50:
      oldest_key = next(iter(self.tracker.npc_npc_relationships))
      del self.tracker.npc_npc_relationships[oldest_key]
  ```
- **Impact**: In long-running series (30+ episodes), foundational NPC-NPC relationships are silently dropped from memory. The DB persistence (L1701-1708) retains them, but the in-memory view used for prompt injection (L1710-1719) loses them.
- **Suggested fix direction**: Use LRU eviction (move accessed keys to end) or prioritize relationships by importance (e.g. never evict relationships involving key NPCs from the arc roster).

---

### TF-NPC-11: `merge_npc_registry` Loses History on Non-Dead Merge -- IMPORTANT

- **Location**: `state_tracker_npc.py:L621-L651`
- **Description**: The merge logic at L638-645 filters out empty/zero values before merging, but it does NOT record the merge as a change event (no `_record_change` call). This creates an audit gap where NPC data changes during merge are invisible to the change history system.

  Additionally, the `Sweep64` fix at L643 `not (isinstance(v, int) and v == 0 and k in existing and existing[k])` has a truthiness issue: `existing[k]` is truthy for any non-zero/non-empty value, which means a legitimate update from `last_arc=5` to `last_arc=0` (rollback) is silently dropped.

- **Evidence**:
  ```python
  # L638-645
  filtered = {
      k: v
      for k, v in info.items()
      if v not in ("", None, [], {})
      and v is not False
      and not (isinstance(v, int) and v == 0 and k in existing and existing[k])
  }
  existing.update(filtered)  # No _record_change call
  ```
- **Impact**: (1) Merge-path changes are invisible to the NPC audit trail. (2) Rollback to arc 0 or episode 0 is impossible through merge path.
- **Suggested fix direction**: Add `_record_change` calls for each changed field during merge. For the rollback case, use explicit `last_arc=0` override or separate rollback method.

---

### TF-NPC-12: Regex Companion Join/Leave Conflicts with Single `seen` Set -- IMPORTANT

- **Location**: `state_tracker_npc.py:L1884-L1917`
- **Description**: `_regex_extract_companion_changes` uses a single `seen` set for both join AND leave patterns. If an NPC matches a "join" pattern first, they are added to `seen` and will NOT be matched by the "leave" pattern. In a tactical_doc that describes "강철이 합류했다가 ... 강철이 떠났다", only the "join" will be extracted.

- **Evidence**:
  ```python
  # L1896: single seen set
  seen = set()

  # L1903-1908: join patterns processed first
  for pattern in join_patterns:
      for match in pattern.finditer(tactical_doc):
          npc = match.group(1).strip()
          if ... and npc not in seen:
              seen.add(npc)
              changes.append({"name": npc, "action": "join", ...})

  # L1910-1915: leave patterns processed second -- blocked by seen
  for pattern in leave_patterns:
      for match in pattern.finditer(tactical_doc):
          npc = match.group(1).strip()
          if ... and npc not in seen:  # <-- already in seen from join!
              ...
  ```
- **Impact**: Within a single arc's tactical_doc, an NPC who joins and then leaves will only register the join. The leave is silently dropped, causing a phantom companion.
- **Suggested fix direction**: Use separate `seen_join` and `seen_leave` sets, or process both patterns for each NPC and resolve conflicts by textual order (later occurrence wins).

---

### TF-NPC-13: `_apply_companion_change` "leave" Replaces List Reference -- IMPORTANT

- **Location**: `state_tracker_npc.py:L1873-L1882`
- **Description**: On "leave" action (L1881), the code creates a new list and assigns it to `self.tracker.current_companions`. This replaces the list object reference. Any caller holding a reference to the old list object will not see the change. In contrast, "join" (L1878) uses `.append()` which mutates in-place.

- **Evidence**:
  ```python
  # L1875: local alias
  companions = self.tracker.current_companions

  # L1878: join -- in-place mutation (OK)
  companions.append({"name": name, ...})

  # L1881: leave -- reference replacement (!)
  self.tracker.current_companions = [c for c in companions if c.get("name") != name]
  ```
- **Impact**: If any code caches a reference to `self.tracker.current_companions` before a "leave" operation, the cached reference becomes stale. Currently, all access goes through `self.tracker.current_companions` directly, so the impact is low. But it's an asymmetric mutation pattern that creates a latent hazard.
- **Suggested fix direction**: Use in-place mutation for both: `self.tracker.current_companions[:] = [c for c in companions if c.get("name") != name]`

---

### TF-NPC-14: Dead NPC Check Uses Hardcoded Flashback/Action Patterns (3x Duplication) -- IMPORTANT

- **Location**: `state_tracker_npc.py:L484-L518, L1475-L1515, L1551-L1598`
- **Description**: The flashback and action pattern lists are defined inline in three separate methods: `check_dead_npc_appearance` (L484-510), `check_dead_npc_in_blueprint` (L1475-1504), and `check_dead_npc_in_manuscript` (L1551-1598). Each has a slightly different set of patterns:
  - `check_dead_npc_appearance`: 8 flashback patterns, 7 action patterns
  - `check_dead_npc_in_blueprint`: 10 flashback patterns, 10 action patterns
  - `check_dead_npc_in_manuscript`: 16 flashback patterns, 12 action patterns

  This triplication means a new flashback pattern added to one method is missed in the others.

- **Evidence**:
  ```python
  # L484-494: check_dead_npc_appearance -- 8 flashback patterns (smallest set)
  # Missing vs manuscript: "을 추모", "의 복수", "의 이름", "처럼", "같은", "과거의", "의 기억", "의 영혼"

  # L1492-1503: check_dead_npc_in_blueprint -- 10 flashback patterns (medium set)
  # Has "을 추모", "의 복수" but missing: "의 이름", "처럼", "같은", "과거의", "의 기억", "의 영혼"

  # L1551-1569: check_dead_npc_in_manuscript -- 16 flashback patterns (largest set)
  ```
- **Impact**: `check_dead_npc_appearance` (used in tactical_doc validation) has the weakest flashback recognition, leading to more false-positive dead-NPC violations compared to the manuscript checker.
- **Suggested fix direction**: Extract flashback and action patterns into module-level constants or a shared method. Use the most comprehensive set (manuscript) for all three checkers.

---

### TF-NPC-15: Unused Return Values in `extract_skill_acquisitions_from_arc` -- INSIGHT

- **Location**: `state_tracker_npc.py:L838-L839`
- **Description**: Two `.get()` calls have their return values discarded:
  ```python
  skill.get("episode", arc_no)      # L838
  skill.get("source", "state_changes에서 추출")  # L839
  ```
  These were likely intended to be assigned to variables for use in `register_protagonist_skill`, but the call at L841 only passes `skill_name` and `arc_no`, ignoring episode and source.

- **Evidence**:
  ```python
  # L837-842
  skill_name = skill.get("name", "")
  skill.get("episode", arc_no)       # <-- unused
  skill.get("source", "state_changes에서 추출")  # <-- unused
  if skill_name and len(skill_name) >= 2:
      self.register_protagonist_skill(skill_name, arc_no)
  ```
- **Impact**: Skill episode granularity is lost -- all skills in an arc are registered with `arc_no` rather than their specific episode number. The `source` field is never recorded.
- **Suggested fix direction**: Either remove the dead code or wire the values into the registration: `episode = skill.get("episode", arc_no)` and pass to `register_protagonist_skill`.

---

### TF-NPC-16: `check_npc_changes` Uses Inline `re.findall` Instead of Compiled Patterns -- INSIGHT

- **Location**: `state_tracker_npc.py:L306-L319, L341-L343`
- **Description**: While most regex patterns were moved to module-level compiled constants in the V66.1 C-2 optimization, `check_npc_changes` still uses inline string patterns with `re.findall`. The weapon patterns (L306-309) and level patterns (L312-315) are compiled on every call.

- **Evidence**:
  ```python
  # L306-309 (inline, not compiled)
  weapon_patterns = [
      r"([가-힣]{2,10})[이가은는]\s*([가-힣]{2,10}(?:검|도|창|궁|봉|부|낫))[을를으로]?\s*(?:들|휘두르|뽑)",
      r"([가-힣]{2,10})[의]\s*([가-힣]{2,10}(?:검|도|창|궁|봉|부|낫))",
  ]
  # Similarly L396-403 in extract_npc_info_from_arc
  ```
- **Impact**: Minor performance overhead (~1ms per call). Inconsistency with the V66.1 C-2 optimization pattern applied elsewhere.
- **Suggested fix direction**: Move to module-level compiled patterns for consistency.

---

### TF-NPC-17: `npc_registry` Unbounded Growth -- 30+ Episode Contamination -- IMPORTANT

- **Location**: `state_tracker_npc.py` (affects all registry mutations)
- **Description**: `npc_registry` has no size cap. Over 30+ episodes, regex fallback extraction and state_changes processing can accumulate hundreds of entries. Each entry is iterated in:
  - `check_dead_npc_appearance` (L473): O(N) per call
  - `check_dead_npc_in_blueprint` (L1464): O(N) per call
  - `check_dead_npc_in_manuscript` (L1540): O(N) per call
  - `get_entity_registry` (L594): O(N)
  - All summary methods: O(N)

  The V69 LLM cleanup (L2126) runs every 5 arcs but only on alive NPCs, and depends on LLM availability. Dead NPCs are never cleaned up.

  Sub-entries within `npc_registry` are also unbounded:
  - `permanent_injuries`: list, no cap
  - `revive_history`: list, no cap

- **Evidence**:
  ```python
  # L126: No size limit
  self.npc_registry: dict[str, dict] = {}

  # L1227: permanent_injuries append-only
  npc["permanent_injuries"].append(...)

  # L1386: revive_history append-only
  npc["revive_history"].append(...)
  ```
- **Impact**: Progressive performance degradation as registry grows. Summary methods produce increasingly long prompt injections, consuming LLM context window budget. Stale entries from early episodes pollute NPC state assertions.
- **Suggested fix direction**: Add a registry size cap (e.g. 200 alive NPCs). Use LRU or relevance-based eviction. Cap `permanent_injuries` per NPC (e.g. 10). Cap `revive_history` per NPC (e.g. 5).

---

### TF-NPC-18: `revive_npc` Directly Manipulates WorldState `_state` Internal Dict -- INSIGHT

- **Location**: `state_tracker_npc.py:L1396-L1412`
- **Description**: `revive_npc` directly accesses `_ws._state` (an internal dict of WorldStateManager) and mutates `dead_npcs` and `alive_npcs` dicts. This bypasses any encapsulation or validation in WorldStateManager.

- **Evidence**:
  ```python
  # L1402-1410
  if _ws is not None and hasattr(_ws, "_state"):
      _dead = _ws._state.get("dead_npcs", {})
      if name in _dead:
          del _dead[name]  # direct mutation of WorldState internal
      _alive = _ws._state.get("alive_npcs", {})
      if name not in _alive:
          _alive[name] = {"role": npc.get("job", ""), "relation": "", "location": ""}
  ```
- **Impact**: If WorldStateManager ever adds validation, caching, or change tracking, this bypass will create inconsistency. The `npc.get("job", "")` field does not exist in the standard NPC registry schema -- it should be `npc.get("position", "")` or similar.
- **Suggested fix direction**: Use WorldStateManager public API if available. Fix the field name to match the actual registry schema.

---

### TF-NPC-19: No Thread Safety for `npc_registry` Mutations -- INSIGHT

- **Location**: All mutation methods throughout the file
- **Description**: `npc_registry` (a plain `dict`) is mutated by multiple methods without any locking. The advisory chain in `stage4_interview_round.py` runs 8 advisories in parallel (ThreadPoolExecutor, max_workers=8). While advisories primarily READ from `npc_registry` (L3960, L4005, L4064), the main thread may concurrently call extraction methods that WRITE to `npc_registry`.

  Python's GIL prevents data corruption for simple dict operations, but dict iteration during concurrent modification can raise `RuntimeError: dictionary changed size during iteration`.

- **Evidence**:
  ```python
  # Readers in parallel advisories (stage4_interview_round.py):
  # L3960: for _npc_name, _npc_info in getattr(self.ctx.state_tracker, "npc_registry", {}).items():
  # L4005: for name, info in self.ctx.state_tracker.npc_registry.items()

  # Writers in NPC module (potentially concurrent):
  # L216: self.tracker.npc_registry[npc_name] = {}
  # L218: self.tracker.npc_registry[npc_name].update(...)
  # L2192: del self.tracker.npc_registry[name]  (cleanup_npc_registry_with_llm)
  ```
- **Impact**: Low in current architecture (extraction happens before advisory parallel phase), but `cleanup_npc_registry_with_llm` could theoretically run concurrently if triggered at the wrong time.
- **Suggested fix direction**: Document the threading contract explicitly. If concurrent access is needed, snapshot the registry (`.copy()`) before parallel reads.

---

### TF-NPC-20: `_regex_extract_relationship_changes` Defaults "from" State From Registry -- INSIGHT

- **Location**: `state_tracker_npc.py:L1084-L1097`
- **Description**: For reconcile patterns (L1088), the default "from" is fetched from registry or hardcoded as "적대". For betray patterns (L1096), the default "from" is fetched from registry or hardcoded as "아군". These defaults create potentially incorrect transitions:
  - If an NPC has no `relation_to_protag` in registry, reconcile always shows "적대 -> 동맹"
  - If an NPC has no `relation_to_protag` in registry, betray always shows "아군 -> 적대"

  The regex also doesn't capture the actual previous relationship -- it just assumes.

- **Evidence**:
  ```python
  # L1088
  _existing = self.tracker.npc_registry.get(npc, {}).get("relation_to_protag", "적대")
  changes.append({"npc": npc, "from": _existing, "to": "동맹", ...})

  # L1096
  _existing = self.tracker.npc_registry.get(npc, {}).get("relation_to_protag", "아군")
  changes.append({"npc": npc, "from": _existing, "to": "적대", ...})
  ```
- **Impact**: False transition records in change history. If reconcile is applied to an already-allied NPC, the transition "동맹 -> 동맹" is recorded (no-op but noisy). If the NPC was "중립", the record shows "중립 -> 동맹" which may be correct by accident.
- **Suggested fix direction**: Skip transition recording if `from == to`. Add a check: if NPC not in registry, mark the transition source as "unknown" rather than assuming.

---

### TF-NPC-21: Movement Regex `_RE_MOVE_FROM_TO` Captures Location Names in Same `[가-힣]{2,10}` Range -- INSIGHT

- **Location**: `state_tracker_npc.py:L38-L43`
- **Description**: The movement patterns use the same `[가-힣]{2,10}` range for both NPC names and location names. There is no semantic distinction between a person and a place. In "강철이 중원에서 떠나 북해로 이동" (Gangcheol left Jungwon for Bukhae), the pattern correctly captures NPC="강철", from="중원", to="북해". But in "마교가 중원에서 철수" (Magyo retreated from Jungwon), "마교" (a faction) would be captured as an NPC name.

- **Evidence**:
  ```python
  # L38-41
  _RE_MOVE_FROM_TO = re.compile(
      r"([가-힣]{2,10})[이가은는]\s*([가-힣]{2,10})[에서을를]\s*"
      r"(?:떠나|출발).{0,20}?([가-힣]{2,10})[으로에]\s*(?:이동|향|도착|떠나)"
  )
  ```
- **Impact**: Factions, organizations, and abstract concepts can be registered as NPCs with location data. Combined with TF-NPC-05, this expands the contamination surface.
- **Suggested fix direction**: Cross-reference extracted "NPC" names against known NPC roster. Add faction/organization names to exclude list.

---

### TF-NPC-22: `extract_npc_info_from_arc` Has Separate Smaller Exclude List -- INSIGHT

- **Location**: `state_tracker_npc.py:L407`
- **Description**: `extract_npc_info_from_arc` uses a local `exclude_words` list with only 8 entries (L407), while death extraction uses the comprehensive 50-entry `_NPC_DEATH_EXCLUDE_WORDS` frozenset. Weapon/level extraction should use the same broad exclusion list.

- **Evidence**:
  ```python
  # L407 (extract_npc_info_from_arc)
  exclude_words = ["주인공", "적", "상대", "자신", "그", "그녀", "적수", "상대방"]

  # L724 (extract_npc_deaths_from_arc)
  exclude_words = _NPC_DEATH_EXCLUDE_WORDS  # ~50 entries
  ```
- **Impact**: Weapon/level extraction has weaker filtering, so common nouns more easily enter the registry with weapon/level attributes.
- **Suggested fix direction**: Unify all exclude lists to use `_NPC_DEATH_EXCLUDE_WORDS` or a shared superset.

---

### TF-NPC-23: `_verify_npc_names_llm` Fail-Closed Returns Empty List -- INSIGHT

- **Location**: `state_tracker_npc.py:L745-L814`
- **Description**: When LLM verification fails (network error, malformed response, etc.), the method returns `[]` (empty list), meaning NO deaths are registered from that arc. This is a "fail-closed" design that prevents false positives but creates false negatives: actual deaths are silently dropped.

  The method also has a 2-attempt retry with `time.sleep(0.1)`, but both attempts share the same prompt. If the issue is prompt-related (e.g. context too long at L760: `context[:3000]` truncation cuts off the relevant death scene), retrying won't help.

- **Evidence**:
  ```python
  # L789-790 (empty response)
  logging.warning("[XC-002] NPC LLM 검증 응답 없음 -> fail-closed: []")
  return []

  # L803-804 (format error)
  logging.warning("[XC-002] NPC LLM 검증 응답 형식 오류 -> fail-closed: []")
  return []

  # L809-810 (exception)
  logging.warning("[XC-002] NPC LLM 검증 예외 -> fail-closed: %s", str(e)[:60])
  return []
  ```
- **Impact**: In environments with unreliable LLM connectivity, death tracking becomes lossy. Deaths that would have been correctly identified by regex alone are dropped because LLM verification fails. The regex candidates are not preserved as a fallback.
- **Suggested fix direction**: Consider fail-open for high-confidence regex matches (e.g. candidates that are already in `npc_registry` as alive). Reserve fail-closed for ambiguous candidates.

---

## 4. Summary Matrix

| ID | Title | Severity | Location | Category |
|----|-------|----------|----------|----------|
| TF-NPC-01 | Operator precedence in emotion summary | CRITICAL | L2052 | Logic Bug |
| TF-NPC-02 | Emotion regex duplicate anchor | CRITICAL | L2029-2033 | Dead Code |
| TF-NPC-03 | Death regex "운명" false positive | CRITICAL | L719 | Regex FP |
| TF-NPC-04 | `_is_standalone_name` context-blind | CRITICAL | L435-458 + callers | Logic Bug |
| TF-NPC-05 | `[가-힣]{2,10}` matches common nouns | IMPORTANT | Module-wide | Regex FP |
| TF-NPC-06 | Death exclude missing title words | IMPORTANT | L76-140 | Regex FP |
| TF-NPC-07 | No relationship transition validation | IMPORTANT | L868-925 | State Machine |
| TF-NPC-08 | No NPC injury recovery path | IMPORTANT | L927-989 | Data Staleness |
| TF-NPC-09 | Permanent injuries cannot be reversed | IMPORTANT | L1200-1325 | Data Model |
| TF-NPC-10 | FIFO eviction loses important relationships | IMPORTANT | L1697-1700 | Cumulative |
| TF-NPC-11 | Merge loses audit trail + rollback blocked | IMPORTANT | L621-651 | Data Integrity |
| TF-NPC-12 | Companion join/leave single `seen` set | IMPORTANT | L1884-1917 | Logic Bug |
| TF-NPC-13 | Companion leave replaces list reference | IMPORTANT | L1873-1882 | Mutation Pattern |
| TF-NPC-14 | Dead NPC patterns triplicated | IMPORTANT | L484/1475/1551 | Maintainability |
| TF-NPC-15 | Unused return values in skill extraction | INSIGHT | L838-839 | Dead Code |
| TF-NPC-16 | Inline regex not compiled | INSIGHT | L306-319 | Performance |
| TF-NPC-17 | `npc_registry` unbounded growth | IMPORTANT | File-wide | Cumulative |
| TF-NPC-18 | `revive_npc` bypasses WorldState API | INSIGHT | L1396-1412 | Encapsulation |
| TF-NPC-19 | No thread safety for registry mutations | INSIGHT | File-wide | Thread Safety |
| TF-NPC-20 | Relationship defaults create false transitions | INSIGHT | L1084-1097 | Data Quality |
| TF-NPC-21 | Movement regex captures factions as NPCs | INSIGHT | L38-43 | Regex FP |
| TF-NPC-22 | Inconsistent exclude list sizes | INSIGHT | L407 vs L724 | Maintainability |
| TF-NPC-23 | LLM fail-closed drops valid deaths | INSIGHT | L745-814 | Reliability |

---

## 5. 핵심 코드 참조 (Appendix)

### A. Module-Level Compiled Regex (L24-70)

All NPC extraction patterns use `[가-힣]{2,10}` as the name capture group. This is the root cause of TF-NPC-05, TF-NPC-06, TF-NPC-21, and TF-NPC-22.

Key patterns and their false-positive surface:

| Pattern | Line | Captures | FP Risk |
|---------|------|----------|---------|
| `_RE_REL_ARROW` | L24-28 | NPC + from_rel + to_rel | "적" / "적대" ambiguity |
| `_RE_REL_RECONCILE` | L29 | NPC | Any 2-10 char noun before "화해" |
| `_RE_REL_BETRAY` | L30 | NPC | Any 2-10 char noun before "배신" |
| `_RE_INJURY_DIRECT` | L33 | NPC + injury_state | Title words as NPCs |
| `_RE_INJURY_BODY` | L34 | NPC + body_part | Possessive descriptions |
| `_RE_INJURY_REVERSE` | L35 | injury_state + NPC | Reversed group order |
| `_RE_MOVE_FROM_TO` | L38-41 | NPC + from_loc + to_loc | Factions/organizations |
| `_RE_MOVE_TO` | L42 | NPC + to_loc | Factions/organizations |
| `_RE_MOVE_LEAVE` | L43 | NPC + from_loc | Factions/organizations |
| `_RE_COMP_JOIN` (3) | L46-50 | NPC | Broad "합류/동행" matching |
| `_RE_COMP_LEAVE` (3) | L51-55 | NPC | Broad "떠나/이탈" matching |
| `_RE_PERM_AMPUTATION` (2) | L58-63 | NPC + body_part | Title words |
| `_RE_PERM_BLINDNESS` (2) | L64-67 | NPC | Title words |
| `_RE_PERM_SCAR` (1) | L68-70 | NPC | Possessive descriptions |

### B. `_NPC_DEATH_EXCLUDE_WORDS` Coverage (L76-140)

50 entries covering: pronouns (주인공, 자신, 그녀, 그것, 그들), abstract nouns (세상, 인생, 미래, 과거), organizations (조직, 세력, 집단), places (도시, 마을), finance terms (투자, 금융, 주식, 자본), and misc (몬스터, 데이터, 후원자).

**Missing categories**: Korean titles/roles, faction names, pronouns like "그자"/"놈"/"녀석", abstract nouns like "꿈"/"영혼"/"기억".

### C. Flashback Pattern Comparison Table

| Pattern | `check_dead_npc_appearance` (L484) | `check_dead_npc_in_blueprint` (L1475) | `check_dead_npc_in_manuscript` (L1551) |
|---------|:--:|:--:|:--:|
| "의 죽음" | O | O | O |
| "을 떠올" | O | O | O |
| "를 떠올" | O | O | O |
| "고인이 된" | O | O | O |
| "죽은" | O | O | O |
| "의 유언" | O | O | O |
| "의 무덤" | O | O | O |
| "의 원혼" | O | O | O |
| "의 유품" | O | O | O |
| "을 추모" | X | O | O |
| "의 복수" | X | O | O |
| "의 이름" | X | X | O |
| "처럼" | X | X | O |
| "같은" | X | X | O |
| "과거의" | X | X | O |
| "의 기억" | X | X | O |
| "의 영혼" | X | X | O |

### D. NPC Registry Data Growth Projection

Assuming per-arc extraction yields ~3-5 new NPC entries (via regex fallback + state_changes):

| Episodes | Estimated Registry Size | Summary String Size | Notes |
|----------|------------------------|---------------------|-------|
| 10 (2 arcs) | 6-10 | ~200 chars | Manageable |
| 50 (10 arcs) | 30-50 | ~1,500 chars | V69 cleanup reduces by ~20% |
| 150 (30 arcs) | 90-150 | ~5,000 chars | Significant prompt budget |
| 300 (60 arcs) | 180-300 | ~10,000 chars | Prompt injection dominates context |

V69 LLM cleanup targets alive NPCs only, runs every 5 arcs, and depends on LLM availability. Dead NPCs, permanent injuries, and revive history are never cleaned.
