# 5-Arc Terminal 3: Context Cache / Project Namespace / DB-Log-Artifact Sink Isolation Survey

Date: 2026-04-06
Terminal: 3
Owner: context caching, project namespace, DB/log/artifact sink separation
Baseline Commit: `0d7c077a9e6f14575aba7fc509b836d218db610d`
Baseline Dirty Summary: active Stage2/Stage4 execution edits, queue docs, material/work-guard docs present; this survey mutated nothing
Mode: read-only bounded survey
Order: `docs/2026-04-06/5arc-parallel-vertex-pool-guard-bounded-survey-order.md`

---

## 1. Verdict

**no live P0-P1 found in this lane** — under multi-process topology.

Under single-process topology, there is one **P1** (class-level context cache shared dict with cross-project eviction side-effect) and one **structural concern** (shared LLM router singleton). Neither constitutes content bleed (P0), but both create operational fragility that makes same-process multi-project runs inadvisable.

---

## 2. Evidence

### 2A. DB Isolation — Per-Project, Clean

`ProjectContext.__init__` (`modules/core/project_manager.py:48-57`) resolves a **per-project directory** via `resolve_project_dir(project_name, default_root)` and sets:

```
self.base_path = projects_root / self.name
self.db_path   = self.base_path / "project_data.db"
```

`DBManager.__init__` (`modules/core/db_manager.py:81-82`) takes `db_path` as a `Path` argument. The connection is `sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)`.

**Conclusion**: Each `ProjectContext` instance opens its own SQLite file at `projects/<project_name>/project_data.db`. There is no shared DB singleton. Two projects in two processes — or even two projects in one process — will never share a DB file unless `project_name` collides.

**Content bleed risk**: None.

### 2B. Log / JSONL Sink Isolation — Per-Project, Clean

All runtime log sinks resolve paths via `resolve_project_log_dir(project)` (`modules/core/soft_failure.py:54-63`), which returns `project.paths.root / "logs"` — i.e., `projects/<project_name>/logs/`.

Specific sinks verified:

| Sink | Path | Evidence |
|------|------|----------|
| `episode_production.jsonl` | `projects/<name>/logs/episode_production.jsonl` | `stage4_outcome_runtime.py:450`, `stage4_post_pass_runtime.py:1202`, `stage4_orchestrator.py:2227` |
| `decisions.jsonl` | `projects/<name>/logs/session/decisions.jsonl` | `session_logger.py:8`, `failure_analyzer.py:188` |
| Artifact snapshots | `projects/<name>/logs/artifacts/stage{N}/...` | `artifact_logging.py:58-67` |
| Soft failure log | `projects/<name>/logs/` | `soft_failure.py:54-63` |

**Fallback path**: When `resolve_project_log_dir` returns `None` (no project object), `stage4_outcome_runtime.py:437` falls back to `Path("projects") / project_name / "logs"` — still project-namespaced.

**Content bleed risk**: None. Every JSONL/artifact sink is rooted under the project directory.

### 2C. Context Cache — Class-Level Shared Dict (P1 under same-process)

`BaseAgent._context_caches` (`base_agent.py:2128`) is a **class variable** (dict), not instance variable. All `BaseAgent` subclass instances in the same Python process share this dict.

Cache key construction (`_get_or_create_context_cache`, line 2159):
```python
cache_key = f"{cache_type}_{project_name}_{content_hash}"
```

Namespace helper (`_context_cache_project_namespace`, lines 2112-2126) builds a token from `work_id` or `project.name`, so keys **do include project identity**.

**Content bleed risk from cache lookup**: None. A lookup for project A will not accidentally return cached content from project B because the `project_name` portion of the key differs.

**However — operational side-effect risk (P1-class)**:

1. **Key rotation clears all caches**: `_try_rotate_key` (line 259) calls `cls._context_caches.clear()`. If project A triggers a quota exhaustion and rotates the API key, **all cached contexts for project B are evicted**. This does not cause content bleed but creates a performance cliff and unexpected re-caching cost for concurrent projects in the same process.

2. **Eviction is global**: When `len(_context_caches) > _CONTEXT_CACHE_MAX`, oldest entries are evicted regardless of project (lines 2205-2209). Project A's high cache pressure can evict project B's entries.

3. **`reset_class_state()` is global**: `BaseAgent.reset_class_state()` (line 230) calls `_context_caches.clear()`, clearing all projects' caches.

### 2D. LLM Router — Process-Global Singleton

`get_shared_llm_router()` (`modules/core/llm_router.py:196-203`) maintains a module-level `_SHARED_ROUTER` singleton. All projects in the same process share one router instance.

The router itself is stateless (it resolves provider config from `models.yaml`), so this is not a content bleed vector. But if one project's error handling calls `force_reload=True`, the other project's mid-flight routing state is disrupted.

### 2E. API Key State — Class-Level Shared

`BaseAgent._api_keys`, `_current_key_idx`, `_rotation_count`, `_quota_exhausted_models` are all class variables (lines 194-195). In a single process, one project's quota exhaustion triggers key rotation that affects all projects.

**Content bleed risk**: None (API keys are credential state, not content).
**Operational risk**: P1 — one project's quota event destabilizes another project's API access flow.

### 2F. Gemini API Context Cache (Server-Side)

`_get_or_create_context_cache` (line 2187) calls `self.client.caches.create(...)` with `display_name=f"{cache_type}_cache_{project_name}"`. The server-side cache is keyed by the returned `cache.name` (opaque Gemini identifier), not by any local namespace.

If two processes use the same API key and same model, Gemini's implicit caching may reuse server-side cached content. This is a **Vertex pool throughput consideration** (Terminal 1 scope), not a content bleed vector — Gemini caching is per-request content matching, not cross-request leakage.

---

## 3. Live Risk

| Risk | Severity | Topology | Description |
|------|----------|----------|-------------|
| DB content bleed | Not present | Any | Per-project SQLite file, no shared state |
| Log/JSONL content bleed | Not present | Any | All sinks rooted under project dir |
| Artifact content bleed | Not present | Any | Artifact paths include project root |
| Context cache content bleed | Not present | Any | Cache keys include project name |
| Context cache cross-eviction | P1 | Same-process only | Key rotation / LRU eviction is global |
| API key rotation cross-effect | P1 | Same-process only | Rotation event from project A affects project B |
| LLM router reload cross-effect | Low | Same-process only | `force_reload` disrupts shared singleton |

---

## 4. Owner Files

| File | Relevance |
|------|-----------|
| `modules/domain/agents/base_agent.py` | Context cache (`_context_caches`, `_context_cache_project_namespace`, `_get_or_create_context_cache`), API key rotation (`_try_rotate_key`, `reset_class_state`) |
| `modules/core/project_manager.py` | `ProjectContext.__init__` — per-project dir/DB resolution |
| `modules/core/runtime_paths.py` | `resolve_project_dir`, `resolve_projects_root` — path isolation logic |
| `modules/core/db_manager.py` | `DBManager.__init__` — per-path SQLite connection |
| `modules/core/soft_failure.py` | `resolve_project_log_dir` — log sink path resolution |
| `modules/core/artifact_logging.py` | `snapshot_logged_artifact` — artifact snapshot path resolution |
| `modules/core/stage4_outcome_runtime.py` | JSONL sink writes (`episode_production.jsonl`) |
| `modules/core/stage4_post_pass_runtime.py` | JSONL sink writes |
| `modules/core/session_logger.py` | `decisions.jsonl` session log sink |
| `modules/core/llm_router.py` | `_SHARED_ROUTER` singleton |
| `modules/api/prompt_broker.py` | `run_id`-scoped prompt tracking (no project bleed) |

---

## 5. What This Means For 5-Arc Parallel

### Multi-process topology (recommended):

Content isolation is **structurally safe**. Each process gets its own:
- `ProjectContext` → own SQLite DB
- Own log/JSONL/artifact directory tree
- Own `BaseAgent` class state (API keys, context cache, rotation counters)
- Own `_SHARED_ROUTER` singleton

No app-level namespace collision is possible because nothing crosses the process boundary.

The remaining risk is the **shared Vertex API pool** (same API key, same project/location hitting the same quota). This is Terminal 1's scope, not Terminal 3's.

### Same-process topology (not recommended):

Content isolation is still safe — cache keys and all sink paths are project-namespaced. But operational stability is compromised by shared class-level state:
- One project's quota event rotates keys and clears caches for all projects
- LRU eviction is global
- LLM router reload is global

These create unpredictable performance coupling, not content corruption. But for 5-arc parallel, unpredictable coupling means an operator cannot reason about one arc's behavior independently.

---

## 6. Need Fresh Probe?

**No** for the content isolation question. The DB/log/artifact/cache namespace separation is structural and statically verifiable from the code paths enumerated above.

**No** for the same-process P1 concerns. These are architectural properties of class-level state, not runtime-dependent behavior.

**Yes, if and only if** the operator wants to verify that Gemini server-side caching (implicit or explicit) does not create cross-request interference when two processes share the same API key. This is a Terminal 1 / Vertex pool concern, not Terminal 3's cache/sink isolation scope.

---

## 7. 3-Pass Audit Record

Pass 1, structure and scope:

- scoped to the four required questions (cache key separation, DB/log/artifact path separation, app-level namespace vs provider-level, wrong-project bleed)
- did not expand into Stage semantics, queue changes, or code modification

Pass 2, evidence and consistency:

- every claim anchored to specific file:line in live code
- verified DB path, log path, JSONL path, artifact path, and context cache key construction independently
- identified class-level shared state as the only structural concern
- confirmed the concern is operational (P1), not content bleed (P0)

Pass 3, execution and readability:

- used required output shape (6 sections)
- verdict sentence included as required
- risk table distinguishes topology-dependent severity
- 5-arc parallel recommendation is explicit

Confidence: `97%`
