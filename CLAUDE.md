# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Wuxia Studio V40** (Sovereign App) - AI-powered multi-genre novel writing system using Google Gemini API to orchestrate specialized agents for serialized fiction production.

**Supported Genres:**
- Wuxia (무협) - Martial arts fiction
- Hunter (헌터) - Modern dungeon/gate fiction
- Investment (투자) - Financial reincarnation fiction

## Running the Application

```bash
# Install dependencies (from requirements in backup folder)
pip install google-generativeai google-genai chromadb python-dotenv rich

# For dashboard UI (optional)
pip install streamlit

# Create .env file with your API key
echo "GOOGLE_API_KEY=your_key_here" > .env

# Run main application
python main_a.py

# Run dashboard (optional)
streamlit run studio_dashboard.py
```

## Utility Tools

Located in `tools/` directory:
- `RESET.py` - Selective project reset (clears DB/ChromaDB for chosen project)
- `make_md.py` - Convert manuscripts to markdown
- `concat_txt.py` - Concatenate episode text files
- `db_porter.py` - Database migration utilities
- `normalize_arcs_db.py` - Arc data normalization

## Production Pipeline (5 Stages)

```
Phase 0: Bible Recovery & DNA Sync → Load lore + treatment, sync to SQLite
Stage 1: Volume Strategy          → Plan 10 volumes
Stage 2: Arc Tactical Design      → Design 50 arcs (5 per volume)
Stage 3: Episode Blueprinting     → Scene-by-scene plans
Stage 4: Sovereign Production     → Final manuscript writing
```

## Architecture

### Core System
```
SovereignApp (main_a.py) - Main orchestrator with UTF-8 encoding, audit logging
├── StudioSystem (modules/core/system.py)
│   ├── ProjectContext (modules/core/project_manager.py)
│   │   └── DBManager (modules/core/db_manager.py) - SQLite operations
│   ├── LoreManager (modules/core/lore_manager.py) - Encyclopedia/asset management
│   ├── MartialManager (modules/core/martial_manager.py) - Character progression HUDs
│   ├── JianghuLogic (modules/core/jianghu_logic.py) - World state simulation
│   ├── GenreGuard (modules/core/genre_guard.py) - Genre-specific validation
│   │   └── Genre-specific guards (modules/core/genre_guards/)
│   ├── KarmaService (modules/core/karma_service.py) - Causality tracking
│   ├── TechniqueWeaver (modules/core/technique_weaver.py) - Skill system
│   └── ConfigManager (modules/core/config_manager.py) - Settings loader
├── LongTermMemory (modules/core/memory_engine.py) - ChromaDB vector search
├── StudioVisualizer (modules/core/studio_visualizer.py) - Console UI with Rich
└── Agent Orchestra (modules/domain/agents/)
    ├── BaseAgent - API client + JSON healing
    ├── Analyst - Strategic planning (volumes)
    ├── Architect - Blueprint creation (episodes)
    ├── Writer - Manuscript generation
    ├── Director - Quality validation
    ├── Weaver - Foreshadowing management
    └── Manager - Production coordination
```

**Service Injection Pattern:**
`StudioSystem.boot_v20_project(name)` initializes all services. Agents receive orchestrator config via `get_v20_orchestrator_config()` which includes: `project`, `api_client`, `martial`, `world`, `techniques`, `guard`, `karma`, `models`.

**Audit System:**
`SovereignApp` maintains `runtime_audit[]` list. Use `_audit_event(event, details, metadata)` for tracking. Events defined in `constants.py:AuditEvents`.

### Triple Database System

| Database | Location | Purpose |
|----------|----------|---------|
| SQLite | `projects/{name}/project_data.db` | **Primary source of truth** - anchors, manuscripts, blueprints, HUD snapshots |
| ChromaDB | `projects/{name}/chroma_db/` | Vector embeddings for semantic episode recall |
| Files | `projects/{name}/drafts/` | Human-readable manuscript backups |

**Critical:** SQLite DB is authoritative. If `bible.json` and DB diverge, DB wins.

### Genre Architecture

Genre selection happens at runtime in `SovereignApp._select_genre()`. Once selected, `self.selected_genre` is set and guard is dynamically initialized.

Genre-specific behavior injected via:
- **GenreGuard** (`modules/core/genre_guards/`) - Validation rules per genre
  - `WuxiaGuard` - Martial power rules, jianghu logic
  - `HunterGuard` - Gate/dungeon mechanics, awakened abilities
  - `InvestmentGuard` - Financial realism, stock market rules
- **HUD Systems** (`modules/core/genre_hud_manager.py`) - State tracking
  - `MartialHUD` - 무력/내공/경공/검법/장법 metrics
  - `HunterHUD` - 각성등급/마나/스킬 metrics
  - `FinanceHUD` - 자산/주식/인맥 metrics
- **Constants** (`modules/core/constants.py`) - Centralized thresholds and mappings
- **Genre Laws** (`modules/core/laws/{genre}.json`) - Genre-specific rules and seed pools
  - `wuxia.json`, `hunter.json`, `investment.json`
  - Seed pools: `items_pool`, `npc_pool`, `location_pool`, `cliche_pool`, `technique_pool`

## Key Files

| File | Purpose |
|------|---------|
| `main_a.py` | Entry point, `SovereignApp` orchestrator |
| `modules/core/project_manager.py` | `ProjectContext` - all data I/O |
| `modules/core/db_manager.py` | `DBManager` - SQLite operations |
| `modules/core/constants.py` | Global constants, `GenreTypes` |
| `modules/domain/agents/base_agent.py` | `BaseAgent` - API calling, JSON healing |
| `modules/domain/agents/writer.py` | `Writer.write_v20_manuscript()` |
| `config/settings.json` | Model tier assignments |
| `config/prompts/` | Agent instruction manifesto files |

## Agent System Patterns

All agents inherit from `BaseAgent` (`modules/domain/agents/base_agent.py`) which provides:

**Core Methods:**
- `ask(prompt, temperature)` - JSON-mode API call with automatic continuation on MAX_TOKENS
  - Injects `author_directives` from project context
  - Escapes braces via `_escape_braces()` to prevent KeyError
  - Overlap-aware merging for multi-chunk responses (100-char overlap detection)
  - Automatic failover to `backup_model` on primary model error
- `_extract_json_robust()` - Self-healing JSON parser with fallback chain

**JSON Parsing Fallback Chain:**
1. `json.loads(strict=False)`
2. `ast.literal_eval()` (handles single quotes)
3. Regex extraction of key fields
4. Return partial data with `"parsing_error": True`

**Continuation Logic:**
When API hits MAX_TOKENS, automatically continues from last 50 chars as anchor point. Critical for preventing "Beat 3" truncation in blueprints.

## Caching System (V31 Quad-Cache)

Four dedicated caches stored in `sys_caches` anchor (24-hour TTL per `constants.py:RetryLimits.CACHE_TTL_SECONDS`):
- `writer_cache` - Writing manifesto + style seeds from `config/cash/style_seeds_final.txt`
- `architect_cache` - Structural rules
- `analyst_cache` - Strategy libraries
- `weaver_cache` - Foreshadowing rules

Each cache contains prompt manifest + timestamp. Auto-created on first use if missing. Cleared by restart or manual DB deletion.

**Style Seeds:**
Located at `projects/{name}/config/cash/style_seeds_final.txt`. Auto-created with default content during project init. Writer agent loads this for stylistic consistency.

## Naming Conventions

| Term | Meaning |
|------|---------|
| `v20_*` | Version 20 architecture (current stable) |
| `anchor` | DB-persisted JSON data |
| `HUD` | Character/world state (Head-Up Display) |
| `tactical_doc` | Strategic plan for an arc |
| `blueprint` | Scene-by-scene plan for an episode |
| `master_bible` | Root lore document |

## Critical Safety Rules

1. **Never delete ChromaDB files** - Especially `chroma.sqlite3` and `*.wal`. Only delete `LOCK` and `*-shm` if locked. Use `RESET.py` for safe cleanup.
2. **Always commit after DB writes** - Use `_safe_commit()` in sync contexts or `_safe_commit_async()` in async contexts. Never commit directly.
3. **Escape user content in prompts** - Use `_escape_braces()` to prevent KeyError from `{}` characters in f-strings.
4. **Validate episode numbers** - Use `get_latest_episode_number()`, don't assume. DB is source of truth.
5. **Check genre context** - Always verify `self.selected_genre` before genre-specific logic.
6. **Handle JSON truncation** - `BaseAgent.ask()` auto-continues on MAX_TOKENS but verify complete JSON structure.
7. **Windows UTF-8 encoding** - Main app already handles this in `main_a.py` lines 5-11. Don't re-wrap stdout.

## Adding a New Genre

1. Create guard in `modules/core/genre_guards/{genre}_guard.py` (inherit from `BaseGuard`)
2. Add HUD class in `modules/core/genre_hud_manager.py` (define metrics dict)
3. Register in `constants.py:GenreTypes`:
   - Add constant (e.g., `ROMANCE = 'romance'`)
   - Add to `all()` classmethod
   - Add to `get_name()` mapping
4. Create genre laws file `modules/core/laws/{genre}.json`
5. Create seed pools in `modules/core/laws/seeds/{name}_pool_{genre}.json`
6. Update `main_a.py:_select_genre()` menu with new option
7. Test guard initialization in `StudioSystem.boot_v20_project()`

## Modifying Agent Behavior

Agent prompts are loaded from `config/prompts/{agent}_rules.json`:
- `analyst_libraries.json` - Strategic planning libraries
- `architect_rules.json` - Blueprint construction rules
- `weaver_rules.json` - Foreshadowing management
- `writer_rules.json` - Writing manifesto

Edit the JSON manifesto files, not Python code. Cache invalidation:
- Restart application, OR
- Delete specific cache from `sys_caches` anchor in DB, OR
- Use `RESET.py` for full project reset

## Debugging and Logging

**Console UI:**
`StudioVisualizer` (via Rich library) provides formatted console output:
- `ui.log(message)` - Standard logging
- `ui.error(message)` - Error display
- Emoji constants in `constants.py:Emojis`

**Log Files:**
Located in `logs/` directory at project root (not per-project).

**Audit Events:**
Runtime audit stored in `SovereignApp.runtime_audit[]`. Event types in `constants.py:AuditEvents`:
- `DB_COMMIT`, `DB_ROLLBACK`
- `STAGE_START`, `STAGE_COMPLETE`
- `CACHE_HIT`, `CACHE_MISS`

**ChromaDB Lock Issues:**
If ChromaDB fails with lock error:
1. Close all Python processes
2. Delete only `LOCK` and `.db-shm` files from `projects/{name}/chroma_db/`
3. Never delete `chroma.sqlite3` or `.db-wal` files

**Common Error Patterns:**
- KeyError in f-strings → Use `_escape_braces()` on user content
- JSON parsing fails → Check `BaseAgent._extract_json_robust()` fallback chain
- Truncated blueprints → Verify MAX_TOKENS continuation in `BaseAgent.ask()`
- HUD state mismatch → Check `MartialManager.snapshot()` and DB storage

## Database Schema

**anchors table** (key-value store):
- `bible` - Master lore document
- `volumes` - 10-volume strategic plan
- `arcs` - 50-arc tactical designs (5 per volume)
- `sys_caches` - Agent prompt caches (writer_cache, architect_cache, analyst_cache, weaver_cache)

**blueprints table**:
- `ep_num` (PK) - Episode number
- `data` - Scene-by-scene plan JSON

**manuscripts table**:
- `ep_num` (PK) - Episode number
- `text` - Final manuscript text
- `hud_snapshot` - Character state at end of episode

**state_logs table**:
- `ep_num` (PK) - Episode number
- `data` - Full state log JSON
- `summary` - Human-readable summary

**causal_graph table**:
- Karma tracking and causality chains

All tables commit through `ProjectContext.db` which wraps `DBManager`. Always use `_safe_commit()`.

## Vector Memory System

`LongTermMemory` class (`modules/core/memory_engine.py`):
- Uses ChromaDB with custom `GoogleEmbeddingFunction`
- Embedding model: `gemini-embedding-001`
- Narrative sampling strategy: First 6000 chars + last 3000 chars (prevents dilution)
- Location: `projects/{name}/chroma_db/`
- Retry logic: 3 attempts with exponential backoff

**Collection naming**: `{project_name}_episodes`

## Model Tier System

Defined in `config/settings.json`:
```json
{
  "architect": "gemini-3-pro-preview",
  "analyst": "gemini-3-pro-preview",
  "writer": "gemini-3-pro-preview",
  "reviewer": "gemini-2.0-flash",
  "evaluator": "gemini-3-pro-preview"
}
```

Agents receive model tier from `StudioSystem.get_v20_orchestrator_config()`.

## Async/Sync Patterns

**Critical:** SQLite operations are synchronous but may be called from async contexts.

- `SovereignApp._safe_commit()` - Synchronous DB commit with rollback protection
- `SovereignApp._safe_commit_async()` - Async wrapper using `asyncio.to_thread()` for thread safety
- Always check `self.current_project.db.conn.in_transaction` before committing
- Use `_emergency_shutdown()` for critical errors (defined in `main_a.py:99`)

**Transaction Safety:**
```python
# In sync context
self._safe_commit()

# In async context
await self._safe_commit_async()
```

## Data Flow Patterns

**Episode Production Flow:**
```
1. Analyst plans volumes (Stage 1) → Saved to anchors["volumes"]
2. Analyst designs arcs (Stage 2) → Saved to anchors["arcs"]
3. Architect creates blueprint (Stage 3) → Saved to blueprints table
4. Writer generates manuscript (Stage 4) → Saved to manuscripts table + drafts/
5. Director validates → Loops back to Writer if rejected
6. Weaver updates foreshadowing → Updates causal_graph
7. LongTermMemory.embed() → ChromaDB collection
8. MartialManager.snapshot() → Saved in manuscripts.hud_snapshot
```

**Data Synchronization:**
- SQLite DB is always authoritative
- ChromaDB embeddings built from DB manuscripts
- File drafts are human-readable backups only
- `ProjectContext._load_from_db()` runs on init to hydrate memory
