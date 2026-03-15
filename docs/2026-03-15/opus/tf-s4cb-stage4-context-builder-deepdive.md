# TF-S4CB: Stage4ContextBuilder Deep-Dive

| Field | Value |
|-------|-------|
| Baseline | bbb00a77 |
| Date | 2026-03-15 |
| Scope | Stage4ContextBuilder: canonical facts, NPC tokens, context size, state integration, BP mapping |
| Source files | `modules/core/stage4_context_builder.py` (2,717 lines) |
| TF Items | 18 (CRITICAL 2 / IMPORTANT 9 / INSIGHT 7) |

---

## 1. Executive Summary

Stage4ContextBuilder is the single most important context-assembly subsystem in the entire codebase. It collects data from 15+ sources (DB, WorldState, FactLedger, StateTracker, VecMemory, AnchorSystem, etc.), assembles it into a single `mandatory_context` string, and feeds it to both ChiefWriter and Director. At ~2,700 lines, it is the largest non-orchestrator module.

Key findings:

1. **Two CRITICAL issues**: (a) A `NameError`-grade scoping risk where `current_arc_no` at L2504 depends on a variable assigned inside a prior `try` block that could fail to execute; (b) Raw SQL bypass at L1804-1816 that circumvents DBManager's abstraction layer, creating a maintenance/schema-evolution hazard and potential KeyError.
2. **Context truncation is positional, not semantic**: `_smart_trim` (L187-199 in context_compression.py) keeps 60% from the start and 40% from the end, which means mid-context critical facts (NPC deaths, canonical numbers) can be silently dropped.
3. **54 `except Exception` blocks** -- all non-fatal, all logged -- but the cumulative effect is that a context builder run that silently swallows 5-10 errors will produce a dramatically degraded context with no single alarm.
4. **Canonical facts filter by substring match** (`fact_key not in full_text` at L49), so homograph keys like "100억" matching blueprint text about an unrelated "100억" figure can inject wrong facts.

---

## 2. Architecture / Data Flow Diagram (ASCII)

```
                        build_mandatory_context()
                              (L2115-2651)
                                  |
        +-----------+-------------+-------------+-----------+
        |           |             |             |           |
   [L0 Canon]  [CP Packet]  [WorldState]  [FactLedger]  [Timeline]
   L2280-2295  L2324-2337   L2217-2229    L2266-2278    L2231-2241
        |           |             |             |           |
        v           v             v             v           v
    _mc_parts[] (ordered list of context sections)
        |
        +--- [StageTracker summaries L2349-2403]
        +--- [Arc summaries L2405-2417]
        +--- [Vector retrieval L2419-2509]
        +--- [Extended lookback L2511-2516]
        +--- [Foreshadow L2518-2524]
        +--- [SemanticPlotGuard L2526-2537]
        +--- [Pacing L2539-2546]
        +--- [Narrative summaries L2548-2553]
        +--- [Future arc context L2555-2558]
        |
        v
  _apply_context_budget(_mc_parts, budget)     ---- trim loop (L1339-1442)
        |
        v
  _compose_mandatory_context_with_headroom(_sc_parts, _mc_parts)  (L1444-1516)
        |
        +--- SC retrieval results from _execute_retrieval_plan() (L1205-1306)
        |
        v
  mandatory_context (single string) --> CW + Director prompts


  prepare_episode_context() (L1755-2002)
        |
        +--- Tier 1: recent 30 full-text manuscripts (L1772-1796)
        +--- Tier 2: 21-60 ep summaries via RAW SQL   (L1798-1834)  <-- CRITICAL bypass
        +--- Tier 3: older arc summaries               (L1836-1882)
        +--- Long-term anchor (ep>=60)                 (L1892-1905)
        +--- Episode digest                            (L1907-1910)
        +--- HUD snapshot                              (L1912-1933)
        +--- Dead NPCs from cumulative bible           (L1953-1957)
        +--- ChainLink (V68)                           (L1961-1964)
        +--- WorldState summary                        (L1966-1972)
        +--- Scene keywords                            (L1974-1983)
        |
        v
  ep_ctx dict --> build_round_context() --> _RoundContext dataclass
```

---

## 3. TF Items

### TF-S4CB-01: `current_arc_no` cross-try-block scoping risk -- CRITICAL

- **Location**: `stage4_context_builder.py:L2407, L2504`
- **Description**: `current_arc_no` is assigned at L2407 inside a `try` block (L2405-2417). It is referenced at L2504 in a completely separate `try` block (L2421-2509). If the first try block fails before L2407 executes, `current_arc_no` will be undefined, causing a `NameError` at L2504. Although L2407 itself (`arc_data.get("arc_no", 1)`) is unlikely to raise, the entire block from L2405-2417 includes calls to `load_v20_anchor` and `format_arc_summary_for_prompt` which can fail. If Arc summary loading fails early (before L2407), the outer except at L2416 catches it and control reaches L2421.
- **Evidence**:
  ```python
  # L2405-2407
  try:
      arc_summaries = []
      current_arc_no = arc_data.get("arc_no", 1) if arc_data else 1
      ...
  except Exception as e:
      self.ctx.ui.log(...)  # current_arc_no may never have been set

  # L2498-2504 (separate try)
  if _mq_queries:
      _vector_memory = self.ctx.memory.retrieve_multi_query_context(
          ...
          current_arc_no=current_arc_no,  # NameError if L2407 never ran
      )
  ```
- **Impact**: If `arc_data` is `None` and the code at L2407 executes as `1`, this is safe. But if the line at L2406 (`arc_summaries = []`) is what actually executes and then a different exception occurs later in the block, `current_arc_no` is still set. The true risk is if `arc_data` itself is malformed in a way that causes `arc_data.get` to raise (extremely unlikely for dict). Practical risk: LOW but architecturally a latent defect. In Python, the variable is function-scoped and survives the try block IF the assignment line executes.
- **Suggested fix direction**: Move `current_arc_no = arc_data.get("arc_no", 1) if arc_data else 1` above both try blocks (e.g., to L2404) so it is always defined. Or initialize it with a default before the first try block.

---

### TF-S4CB-02: Direct raw SQL bypass of DBManager for Tier 2 summaries -- CRITICAL

- **Location**: `stage4_context_builder.py:L1804-1816`
- **Description**: Tier 2 summary loading directly accesses `_db._lock` and `_db.conn.cursor()` to execute raw SQL against `episode_meta`. This bypasses DBManager's abstraction, creating three problems: (1) schema changes to `episode_meta` won't be caught by DBManager's API contract, (2) the row format handling at L1819-1825 assumes both dict-like and tuple-like access without clarity, (3) it depends on internal `_lock` and `conn` attributes.
- **Evidence**:
  ```python
  # L1804-1816
  if hasattr(_db, "_lock"):
      with _db._lock:
          _cur = _db.conn.cursor()
          try:
              _cur.execute(
                  "SELECT ep_num, summary FROM episode_meta "
                  "WHERE ep_num >= ? AND ep_num < ? ORDER BY ep_num ASC",
                  (_tier2_start, _tier2_end),
              )
              _rows = _cur.fetchall()
          finally:
              _cur.close()
  else:
      _rows = []
  ```
- **Impact**: If DBManager's connection factory or lock mechanism changes, this code silently breaks. Also, if `_db` has no `_lock` attribute, the else branch returns `_rows = []`, meaning Tier 2 summaries are silently dropped -- no warning logged.
- **Suggested fix direction**: Add a `get_episode_summaries_range(start_ep, end_ep)` method to DBManager and use it here instead of raw SQL. At minimum, log a warning when the else branch (L1816-1817) is taken.

---

### TF-S4CB-03: Canonical facts substring matching can inject wrong facts -- IMPORTANT

- **Location**: `stage4_context_builder.py:L49`
- **Description**: `_build_canonical_facts_section` filters canonical facts by checking `fact_key not in full_text` (L49). This is a plain substring check. If the blueprint text contains "100억원 자산" and a canonical fact has `fact_key="100억"`, it matches. But if there is another canonical fact with `fact_key="자산"`, it also matches. Worse, if the blueprint discusses a different character's "100억" figure, the protagonist's canonical "100억" fact gets injected as if it's relevant.
- **Evidence**:
  ```python
  # L49
  if full_text and fact_key not in full_text:
      continue
  ```
- **Impact**: The LLM receives incorrect canonical facts as if they are established truth for this episode, potentially causing narrative contradictions. Mitigated by the `[:10]` limit (L43) and `[:8]` output limit (L66), but the semantic mismatch remains.
- **Suggested fix direction**: Use entity-aware matching (check that the fact_key appears in the context of the same entity it was established for), or add an entity/subject field to canonical_facts and filter by entity match.

---

### TF-S4CB-04: NPC token extraction has no Korean morphological awareness -- IMPORTANT

- **Location**: `stage4_context_builder.py:L109-154`
- **Description**: `_extract_npc_tokens` splits query text on whitespace/punctuation and filters by stopwords. It has no Korean morphological analysis, so a query like "무영검의 과거 행적" produces tokens `["무영검의"]` (with the possessive particle `의` attached) instead of `["무영검"]`. This means NPC name matching against the registry will fail unless the name happens to include the particle.
- **Evidence**:
  ```python
  # L146
  for token in re.split(r"[\s,|/:;()\[\]{}]+", str(query)):
      text = token.strip()
      if len(text) < 2:
          continue
      if text.lower() in stopwords:
          continue
  ```
- **Impact**: NPC retrieval queries may miss relevant NPCs whose names are embedded in Korean particles. The fallback `_collect_npc_roster` at L157-222 compensates by using arc state_changes and blueprint data, but pure query-based retrieval (e.g., via `DB_NPC_HISTORY` source at L1247-1253) will pass these particle-contaminated tokens to the memory system.
- **Suggested fix direction**: Strip common Korean particles (의, 이, 가, 을, 를, 에게, 은, 는, 에, 와, 과, 로, 으로) from token tails before matching. Alternatively, match against a known NPC registry and use fuzzy/prefix matching.

---

### TF-S4CB-05: Context budget trim is positional, not semantic -- IMPORTANT

- **Location**: `stage4_context_builder.py:L1339-1442`, context_compression.py:L187-199
- **Description**: When the total context exceeds budget, `_apply_context_budget` trims sections using `ContextCompressor._smart_trim`, which keeps 60% from the start and 40% from the end of each section. Critical information in the middle of a section (e.g., a death event, a numerical fact, a relationship change) is silently dropped in the `[...중략...]` gap.
- **Evidence**:
  ```python
  # context_compression.py L192-199
  start_len = int(max_length * 0.6)
  end_len = max_length - start_len - 20
  start = text[:start_len]
  end = text[-end_len:] if end_len > 0 else ""
  return f"{start}\n\n[...중략...]\n\n{end}"
  ```
- **Impact**: When context is large (common for episodes > 30), the trim can remove factual anchors from the middle of world_state or fact_ledger summaries. The LLM then writes without those constraints, potentially contradicting established facts. The tiered trim (regular 0.7x, protected 0.88x, emergency 0.5x at L1423-1435) is a good mitigation but the underlying trim function is semantically blind.
- **Suggested fix direction**: Consider paragraph-level scoring (keep paragraphs containing entity names from the current blueprint, drop paragraphs with no entity overlap) instead of positional truncation.

---

### TF-S4CB-06: `_build_continuity_packet` budget accounting uses character count, not semantic priority -- IMPORTANT

- **Location**: `stage4_context_builder.py:L538-721`
- **Description**: The Continuity Packet uses a hard 7,000-character budget (L544). NPCs are processed first (L554-597), then plots (L599-604), then items (L606-611), then locations (L613-618), then relationships (L620-672), then numbers (L674-710), then canonical facts (L712-715). If early NPCs consume most of the budget, later sections (relationships, numbers, canonical facts) are silently dropped. There is no priority ordering within the NPC list -- the first 10 NPCs from `entities["npcs"]` get all the budget.
- **Evidence**:
  ```python
  # L544
  budget = 7000
  used = 0
  # L554 - NPCs first, no priority sort
  for npc_name in (entities.get("npcs") or [])[:10]:
      ...
      if used + len(section) > budget:
          break
  ```
- **Impact**: For episodes with many NPCs (e.g., battle scenes with 8+ NPCs), the relationship trajectory data (L620-672) and numerical fact data (L674-710) may be entirely omitted. This is exactly when those facts matter most (complex scenes need more constraint data).
- **Suggested fix direction**: Sort NPCs by relevance to the current blueprint before iterating. Or reserve sub-budgets (e.g., 4000 for NPCs, 1500 for relationships, 1500 for numbers/facts).

---

### TF-S4CB-07: World state summary uses private `_state` attribute -- IMPORTANT

- **Location**: `stage4_context_builder.py:L392, L457, L550, L972`
- **Description**: Multiple methods access `world_state._state` directly (e.g., `getattr(world_state, "_state", {})` at L392, L457, L550, L972). This bypasses any validation or transformation that WorldState's public API might provide. If WorldState's internal representation changes, all these access points silently return `{}` and the context degrades without error.
- **Evidence**:
  ```python
  # L972
  state = getattr(world_state, "_state", {}) if hasattr(world_state, "_state") else {}
  # L392
  ws_state = getattr(world_state, "_state", {}) if world_state else {}
  ```
- **Impact**: Context builder silently produces empty/degraded world state sections if the internal `_state` dict structure changes. No error is raised -- the code simply falls through to fallback paths that produce less detailed output.
- **Suggested fix direction**: Use `world_state.get_state_dict()` (which exists, per L89) consistently. Or add a dedicated public accessor for the alive/dead NPC pools.

---

### TF-S4CB-08: Fact ledger private `_ledger` access -- IMPORTANT

- **Location**: `stage4_context_builder.py:L552, L1132`
- **Description**: Similar to TF-S4CB-07, the code accesses `fact_ledger._ledger` directly. Both `_build_continuity_packet` (L552) and `_build_condensed_fact_ledger_summary` (L1132) reach into the private dict. This duplicates the coupling pattern seen with WorldState.
- **Evidence**:
  ```python
  # L552
  ledger = getattr(fact_ledger, "_ledger", {}) if fact_ledger else {}
  # L1132
  ledger = getattr(fact_ledger, "_ledger", {}) if hasattr(fact_ledger, "_ledger") else {}
  ```
- **Impact**: Same as TF-S4CB-07 -- degraded context without error if internal structure changes.
- **Suggested fix direction**: Add a public `get_ledger_dict()` method to FactLedger and use it here.

---

### TF-S4CB-09: 54 exception handlers create silent degradation cascade -- IMPORTANT

- **Location**: Throughout the file (see grep output above)
- **Description**: The file contains 54 `except Exception` blocks. Each one logs at debug/warning level and returns a fallback value (usually `""` or `{}`). Individually, each is correct -- these are non-fatal enrichment steps. Collectively, if 5-10 of them trigger in a single `build_mandatory_context` call, the resulting context is severely degraded: missing world state, missing fact ledger, missing NPC boundaries, missing canonical facts, missing chain links, etc. There is no aggregated error counter or "context quality score" that would alert the operator.
- **Evidence**: 54 blocks across L67-2642. The `_record_retrieval_observation` at L2583-2601 records some metadata but doesn't track how many enrichment steps failed.
- **Impact**: A single broken DB connection or corrupt project data causes a cascade of silent failures, producing a minimal context that the LLM uses to write a disconnected episode. The operator sees only individual `⚠️` lines in the log, not a summary like "WARNING: 8/15 context enrichment steps failed."
- **Suggested fix direction**: Add a counter/set tracking which enrichment steps succeeded vs failed. At the end of `build_mandatory_context`, if failures exceed a threshold (e.g., >= 3), log a WARNING with the full list and optionally record it in the retrieval observation.

---

### TF-S4CB-10: Tier 2 row format ambiguity (dict vs sqlite3.Row) -- IMPORTANT

- **Location**: `stage4_context_builder.py:L1819-1825`
- **Description**: After the raw SQL query at L1813, the code handles rows with two branches: `isinstance(_row, dict)` using `.get()`, else using bracket access `_row["ep_num"]`. The `else` branch at L1824 does `int(_row["ep_num"] or 0)` which can raise `KeyError` if the row is a tuple (default sqlite3 behavior without `row_factory`). The DBManager uses `sqlite3.Row` factory, so bracket access works, but if the `_lock`/`conn` access pattern changes, this breaks.
- **Evidence**:
  ```python
  # L1819-1825
  for _row in _rows:
      if isinstance(_row, dict):
          _ep_no = int(_row.get("ep_num", 0) or 0)
          _summary = str(_row.get("summary", "") or "")
      else:
          _ep_no = int(_row["ep_num"] or 0)   # KeyError if tuple
          _summary = str(_row["summary"] or "")
  ```
- **Impact**: If sqlite3 row factory is changed or reset, the else branch throws `KeyError`/`TypeError`, caught by the outer except at L1828, silently dropping all Tier 2 summaries.
- **Suggested fix direction**: Use the DBManager API instead of raw SQL (see TF-S4CB-02). If raw SQL must remain, force `_db.conn.row_factory = sqlite3.Row` or always convert rows to dicts.

---

### TF-S4CB-11: `_mc_parts` insertion order is fragile and non-obvious -- IMPORTANT

- **Location**: `stage4_context_builder.py:L2192-2345`
- **Description**: `_mc_parts` is built by a series of `append` and `insert(0, ...)` calls. The final order depends on which branches execute:
  - L2192: mandatory_context (base)
  - L2200: `insert(0, _slot_summary)` -- pushes to front
  - L2206: `insert(1 if _slot_summary else 0, _stage2_failure_context)`
  - L2226: `insert(0, _ws_summary)` -- pushes everything right
  - L2238: `insert(0, _timeline_text)` -- pushes everything right again
  - L2275: `insert(0, _fl_summary)` -- pushes everything right again
  - L2292: `insert(0, _l0_block)` -- pushes everything right again
  - L2319: `insert(2, genre_ext)` -- inserts at position 2
  - L2328: `insert(0, cp_text)` -- pushes everything right again
  - L2345: `insert(0, _npc_boundary_block)` -- pushes everything right yet again

  The cumulative effect of 7+ `insert(0, ...)` calls means the actual final order is the *reverse* of the insertion order. The `insert(2, genre_ext)` at L2319 is particularly fragile because position 2 means different things depending on how many prior `insert(0)` calls have executed.
- **Evidence**: The insertion sequence above.
- **Impact**: The genre_ext Treatment block may end up at an unexpected position relative to canonical constraints and world state data, potentially being trimmed by the budget system (which processes sections in list order). Hard to maintain and debug.
- **Suggested fix direction**: Use named slots/dict with explicit priority ordering, then assemble into a list at the end. E.g., `{0: "npc_boundary", 1: "cp_text", 2: "l0_block", ...}` sorted by key.

---

### TF-S4CB-12: `_suggest_ambient_npcs` returns hardcoded Korean location hints -- INSIGHT

- **Location**: `stage4_context_builder.py:L305-355`
- **Description**: The method uses a hardcoded dictionary mapping Korean location keywords to NPC role suggestions (L310-327). This is genre-agnostic -- the same hints apply to wuxia, investment, fantasy, etc. A wuxia scene set in a "거리" (street) gets suggestions like "행인, 노점상, 경찰" (passerby, street vendor, **police**), which is anachronistic.
- **Evidence**:
  ```python
  _location_hints = {
      "거리": "행인, 노점상, 경찰",  # police in wuxia?
      "은행": "은행원, 지점장, 대기 고객",  # bank in wuxia?
  }
  ```
- **Impact**: Low -- the hint text explicitly says "반드시 사용할 필요는 없습니다" (not mandatory). But it could subtly bias the LLM toward modern-setting NPCs in historical-setting stories.
- **Suggested fix direction**: Make the location hints genre-aware, or delegate to the GenreGuard to provide location-appropriate NPC role lists.

---

### TF-S4CB-13: Protagonist name resolution has 3-layer fallback with no reconciliation -- INSIGHT

- **Location**: `stage4_context_builder.py:L78-106`
- **Description**: `_resolve_protagonist_name` tries three sources in order: (1) `ctx.get_protagonist_name()` callback, (2) `world_state.get_state_dict()["protagonist"]["name"]`, (3) `master_bible["MasterBible"]["protagonist_config"]["name"]`. If sources 1 and 2 return different names (e.g., due to a name change event), the method returns whichever succeeds first. There is no reconciliation or conflict detection.
- **Evidence**:
  ```python
  # L79-83 -- first source
  if getattr(self.ctx, "get_protagonist_name", None):
      name = self.ctx.get_protagonist_name()
      if name: return str(name).strip()
  # L87-95 -- second source
  ws = getattr(self.ctx, "world_state", None)
  ...
  # L100-106 -- third source
  master_bible = getattr(self.ctx.current_project, "master_bible", None) or {}
  ```
- **Impact**: If the protagonist's name changes mid-story (e.g., title acquisition, alias revelation), different subsystems may hold different names, and this method will always return the callback version without warning about the mismatch.
- **Suggested fix direction**: Log a warning if multiple sources return different non-empty names.

---

### TF-S4CB-14: `_collect_npc_roster` has no deduplication across alias forms -- INSIGHT

- **Location**: `stage4_context_builder.py:L157-222`
- **Description**: `_collect_npc_roster` collects NPC names from arc `state_changes` and blueprint, deduplicating by exact string match (`if text and text not in names`). However, the same NPC might appear as "무영검" in state_changes and "무영검 (본명: 장철)" in the blueprint. These are treated as two separate NPCs.
- **Evidence**:
  ```python
  # L183-184
  if text and text not in names:
      names.append(text)
  ```
- **Impact**: NPC roster inflation. The roster cap at L222 (`[:50]`) mitigates overflow, but the downstream NPC boundary block (L442-536) and Continuity Packet (L538-721) will waste budget on duplicate NPC entries that are really the same character.
- **Suggested fix direction**: Normalize NPC names by stripping parenthetical annotations before dedup. Or match against a canonical NPC registry from WorldState.

---

### TF-S4CB-15: Tier 1 full-text load has no size cap -- INSIGHT

- **Location**: `stage4_context_builder.py:L1772-1796`
- **Description**: Tier 1 loads the full text of the most recent 30 episodes with no per-episode or total size cap. Each episode can be 5,000-15,000 characters (ManuscriptLimits), so Tier 1 alone can produce 150,000-450,000 characters. This entire blob is passed as `prev_manuscripts_text` in the episode context dict.
- **Evidence**:
  ```python
  # L1795-1796
  if _content and len(_content) > 100:
      _prev_manuscripts_parts.append(f"[EP {_ep_no}]\n{_content}")
  ```
  No truncation per episode or total.
- **Impact**: Memory and token cost. The downstream prompt builder should handle truncation, but the ep_ctx dict itself carries a potentially 450K+ string. With the 1M context window, this is within limits but wasteful for episodes where only the most recent 5-10 are truly relevant.
- **Suggested fix direction**: Consider a Tier 1 total budget (e.g., 200K chars) and truncate older episodes within the tier first.

---

### TF-S4CB-16: `_build_condensed_world_state_summary` alive NPC cap at 12 -- INSIGHT

- **Location**: `stage4_context_builder.py:L1054`
- **Description**: The condensed world state summary only includes 12 alive NPCs that are NOT in the Continuity Packet (L1054). For long-running stories with 50+ alive NPCs, 38+ NPCs are silently excluded from the world state context. The CP covers the "important" ones for this episode, but the LLM has no awareness of the other NPCs' existence.
- **Evidence**:
  ```python
  # L1054
  for name, info in remaining_alive[:12]:
  ```
- **Impact**: In scenes where a background NPC from 30 episodes ago suddenly becomes relevant (e.g., a chance encounter), the LLM may not know they exist and may introduce them as a new character, creating a continuity error.
- **Suggested fix direction**: Include a count line like "외 {N}명 생존 NPC 있음" after the 12-NPC list, so the LLM at least knows they exist. Or increase the cap for long-running stories.

---

### TF-S4CB-17: `build_extended_lookback_digest` range filtering is redundant -- INSIGHT

- **Location**: `stage4_context_builder.py:L1555-1605`
- **Description**: `build_extended_lookback_digest` fetches 10 manuscripts via `get_recent_manuscript_excerpts(before_ep=next_ep, limit=10)`, then filters by `ep_num < start_ep or ep_num >= end_ep` at L1581. However, `get_recent_manuscript_excerpts` returns the 10 most recent episodes before `next_ep` ordered by `ep_num DESC`. The method then re-filters to keep only episodes in the [next_ep-10, next_ep-3) range. If `next_ep` is 15, the DB returns eps 14,13,...,5 (10 episodes), but the filter keeps only eps 5-12, discarding eps 13-14 (which are the "recent 3" covered by another lookback). This works correctly but the double-query (DB fetches 10, code keeps 7) wastes I/O.
- **Evidence**:
  ```python
  # L1581
  if ep_num < start_ep or ep_num >= end_ep:
      continue
  ```
- **Impact**: Minor I/O waste. The DB query could be parameterized to fetch only the desired range directly.
- **Suggested fix direction**: Pass `start_ep` and `end_ep` to the DB query instead of post-filtering.

---

### TF-S4CB-18: `_format_npc_meta_value` recursive call on `known_by` -- INSIGHT

- **Location**: `stage4_context_builder.py:L280-302`
- **Description**: `_format_npc_meta_value` calls itself recursively at L287 to format the `known_by` field. If `known_by` is a deeply nested dict (e.g., `{"known_by": {"known_by": {"known_by": ...}}}`), this could cause deep recursion. In practice, `known_by` is always a list of character names, so the recursion depth is 1. But there is no depth guard.
- **Evidence**:
  ```python
  # L287-288
  known_by = Stage4ContextBuilder._format_npc_meta_value(
      value.get("known_by") or value.get("known_by_characters") or []
  )
  ```
- **Impact**: Extremely low practical risk (the data source constrains `known_by` to be a list). But architecturally, a self-recursive formatter without depth limit is a latent risk.
- **Suggested fix direction**: Add a `depth` parameter with a max of 2-3, or handle only the expected `list` type for `known_by` without recursion.

---

## 4. Summary Matrix

| ID | Title | Severity | Location | Risk Area |
|----|-------|----------|----------|-----------|
| TF-S4CB-01 | `current_arc_no` cross-try scoping | CRITICAL | L2407/L2504 | NameError |
| TF-S4CB-02 | Raw SQL bypass for Tier 2 | CRITICAL | L1804-1816 | Schema coupling |
| TF-S4CB-03 | Canonical facts substring injection | IMPORTANT | L49 | Fact accuracy |
| TF-S4CB-04 | NPC tokens lack Korean morphology | IMPORTANT | L109-154 | Retrieval accuracy |
| TF-S4CB-05 | Positional trim drops mid-context | IMPORTANT | L1339-1442 | Context quality |
| TF-S4CB-06 | CP budget favors early NPCs | IMPORTANT | L538-721 | Context balance |
| TF-S4CB-07 | Private `_state` access on WorldState | IMPORTANT | L392/457/550/972 | Coupling |
| TF-S4CB-08 | Private `_ledger` access on FactLedger | IMPORTANT | L552/1132 | Coupling |
| TF-S4CB-09 | 54 silent exception cascade | IMPORTANT | Throughout | Observability |
| TF-S4CB-10 | Tier 2 row format ambiguity | IMPORTANT | L1819-1825 | Data access |
| TF-S4CB-11 | `_mc_parts` insert(0) fragility | IMPORTANT | L2192-2345 | Maintainability |
| TF-S4CB-12 | Genre-agnostic ambient NPC hints | INSIGHT | L305-355 | Genre fidelity |
| TF-S4CB-13 | Protagonist 3-layer no reconciliation | INSIGHT | L78-106 | Name consistency |
| TF-S4CB-14 | NPC roster no alias dedup | INSIGHT | L157-222 | Efficiency |
| TF-S4CB-15 | Tier 1 no size cap | INSIGHT | L1772-1796 | Memory |
| TF-S4CB-16 | Alive NPC summary cap at 12 | INSIGHT | L1054 | Completeness |
| TF-S4CB-17 | Extended lookback redundant filtering | INSIGHT | L1555-1605 | I/O waste |
| TF-S4CB-18 | Recursive `_format_npc_meta_value` | INSIGHT | L280-302 | Safety |

---

## 5. Key Code References (Appendix)

### A. `_build_canonical_facts_section` (L31-69)
- Module-level function (not a method), takes `db` and `full_text`
- Retrieves only `fact_type="numerical"` facts
- Hard limits: `[:10]` fetch, `[:8]` output
- Substring filter at L49 is the source of TF-S4CB-03

### B. Context Budget Pipeline (L1339-1516)
```
_apply_context_budget(sections, budget)
  |-- ContextBudgetTracker.register_section()
  |-- get_compression_targets() -> indices
  |-- _trim_indices(regular, ratio=0.7)     # pass 1
  |-- _trim_indices(protected, ratio=0.88)  # pass 2
  |-- _trim_indices(regular, ratio=0.5)     # emergency pass 3
  |-- _trim_indices(protected, ratio=0.68)  # emergency pass 4

_compose_mandatory_context_with_headroom(sc_parts, mc_parts)
  |-- headroom = min(20000, limit//20)
  |-- mc_body trim if sc_header too large
  |-- sc_header trim if mc_body too large
  |-- final combined trim if still over limit
```

### C. `prepare_episode_context` Tier Structure (L1755-2002)
- **Tier 1** (L1772-1796): Full text of last 30 episodes. No size cap.
- **Tier 2** (L1798-1834): Summaries of episodes 31-60 back. RAW SQL. 5000 chars/ep.
- **Tier 3** (L1836-1882): Arc summaries older than 60 episodes. 8000 chars/arc.
- **Long-term anchor** (L1892-1905): Only for ep >= 60.

### D. `build_mandatory_context` Assembly Order (L2115-2651)
Final `_mc_parts` order after all `insert(0)` calls (most recent insert first):
1. NPC boundary block
2. Continuity Packet
3. L0 Canonical constraints
4. Fact Ledger summary
5. Timeline
6. World State summary
7. Slot summary (or stage2 failure context)
8. Genre ext Treatment
9. Mandatory context (base)
10. Ambient NPC hints
11. Arc constraints
12. V68 series/volume summaries
13. StateTracker 16 summaries
14. Arc summaries
15. Vector retrieval / extended lookback / foreshadow / pacing / etc.
16. Future arc context
