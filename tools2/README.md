# 글도비 (Geuldobi) - AI Novel Production System

> **V41 (January 2026)** - AI-powered multi-genre web novel writing system using Google Gemini API

**시스템명**: 글도비 (Wuxia Studio / Sovereign App)
**목표**: 250화 연재 시 설정 붕괴율 0% + 문학적 품질 확보
**지원 장르**: 무협(Wuxia), 헌터(Hunter), 투자(Investment)

---

## 📖 Overview

글도비는 Google Gemini API를 활용하여 여러 AI 에이전트가 협업하며 장편 웹소설을 자동으로 생성하는 시스템입니다. 단순한 텍스트 생성을 넘어, **인과율 추적**, **캐릭터 상태 관리**, **복선 설계**, **품질 검증**까지 수행하는 완전한 소설 제작 공정을 구현합니다.

### Core Features

- ✅ **Multi-Agent Orchestration** - 6개의 전문화된 AI 에이전트가 역할 분담
- ✅ **3-Tier Validation System (V0128)** - BLOCKING/SCORING/ADVISORY 계층화 검증으로 80-85% 통과율 달성
- ✅ **Progressive Model Tiers (V40+)** - 거부 횟수에 따른 점진적 모델 업그레이드 (Flash → Pro → 3.0)
- ✅ **Genre-Agnostic Architecture** - 무협/헌터/투자 장르 간 코드 공유, 설정만 분리
- ✅ **Triple Database System** - SQLite (primary) + ChromaDB (vector) + Files (backup)
- ✅ **Quad-Cache System (V31)** - API 비용 90% 절감

---

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.9 이상 필요
pip install google-generativeai google-genai chromadb python-dotenv rich

# Optional: Dashboard UI
pip install streamlit
```

### Environment Setup

Create a `.env` file in the root directory:

```env
GOOGLE_API_KEY=your_google_api_key_here
```

### Run Application

```bash
# Main production interface
python main_a.py

# Optional: Dashboard (if Streamlit installed)
streamlit run studio_dashboard.py
```

### Usage Flow

1. **Select Genre**: Wuxia(1) / Hunter(2) / Investment(3)
2. **Select/Create Project**: Choose existing or create new
3. **Execute Stages**:
   - `[0] Phase 0`: Bible Recovery & DNA Sync (required once)
   - `[1] Stage 1`: Volume Strategy (10 volumes) - **Can skip if exists (V41)**
   - `[2] Stage 2`: Arc Tactical Design (50 arcs)
   - `[3] Stage 3`: Episode Blueprinting (scene-by-scene plans)
   - `[4] Stage 4`: Sovereign Production (final manuscript writing)

---

## 🏗️ System Architecture

### Multi-Agent Orchestra

```
SovereignApp (main_a.py)
├── Analyst      - Strategic planning, pattern design, arc reconstruction
├── Architect    - Blueprint creation, 10-scene structural design
├── Writer       - Manuscript generation (5000+ chars)
├── Director     - Quality validation (3-tier system)
├── Manager      - Arc coordination
└── Weaver       - Foreshadowing & desire engine
```

### Progressive Model Tiers (V40+)

| Agent | Tier 1 (1st try) | Tier 2 (after 1 reject) | Tier 3 (after 2+ rejects) |
|-------|------------------|-------------------------|---------------------------|
| **Architect** | gemini-2.5-flash | gemini-2.5-pro | gemini-3-pro-preview |
| **Writer** | gemini-2.5-flash | gemini-2.5-pro | gemini-3-pro-preview |
| **Writer (Stage 4)** | gemini-3-pro-preview | *fixed* | *fixed* |
| **Analyst** | gemini-3-pro-preview | *fixed* | *fixed* |
| **Director** | gemini-2.0-flash | *fixed* | *fixed* |

**Note**: Stage 4 Writer uses fixed `gemini-3-pro-preview` to maintain quality consistency during retries.

### 3-Tier Validation System (V0128)

```
┌─────────────────────────────────────────────────┐
│  TIER 1: BLOCKING (차단)                        │
│  • 설정 붕괴, 사망 NPC 재등장 등                │
│  • 실패 시 즉시 REJECT                          │
│  → 5개 핵심 검증만 수행                         │
└─────────────────────────────────────────────────┘
              ↓ PASS
┌─────────────────────────────────────────────────┐
│  TIER 2: SCORING (점수화)                       │
│  • 문장력, 감정선, 페이싱, 대화품질             │
│  • 가중치 합산 → 70점 이상 PASS                 │
└─────────────────────────────────────────────────┘
              ↓ PASS
┌─────────────────────────────────────────────────┐
│  TIER 3: ADVISORY (권고)                        │
│  • 개선 제안만 제공, 통과 여부에 영향 없음      │
└─────────────────────────────────────────────────┘

통과율: ~80-85% (기존 50-60% 대비 개선)
```

### Triple Database System

| Database | Location | Purpose | Critical Files |
|----------|----------|---------|----------------|
| **SQLite** | `projects/{name}/project_data.db` | Primary source of truth | Entire file |
| **ChromaDB** | `projects/{name}/chroma_db/` | Vector embeddings | `chroma.sqlite3`, `*.wal` |
| **Files** | `projects/{name}/drafts/` | Human-readable backups | `*.txt` |

**CRITICAL**: SQLite DB is authoritative. Never delete ChromaDB `chroma.sqlite3` or `*.wal` files.

---

## 📁 Project Structure

```
글도비/
├── main_a.py                    # Main application entry point
├── .env                         # API key configuration
├── README.md                    # This file
├── CLAUDE.md                    # AI agent guidance
│
├── modules/
│   ├── core/                    # Core services layer
│   │   ├── system.py            # StudioSystem - service orchestrator
│   │   ├── project_manager.py   # ProjectContext - data I/O hub
│   │   ├── db_manager.py        # DBManager - SQLite operations
│   │   ├── memory_engine.py     # LongTermMemory - ChromaDB wrapper
│   │   ├── constants.py         # Centralized constants (V40+)
│   │   ├── lore_manager.py      # Encyclopedia/asset management
│   │   ├── martial_manager.py   # Character progression (HUD tracking)
│   │   ├── jianghu_logic.py     # World state simulation
│   │   ├── karma_service.py     # Causality chain logging
│   │   ├── technique_weaver.py  # Skill system management
│   │   ├── studio_visualizer.py # Rich-based console UI
│   │   ├── genre_hud_manager.py # Genre-specific HUD systems
│   │   └── genre_guards/        # Genre-specific validation
│   │       ├── wuxia_guard.py   # Martial arts validation
│   │       ├── hunter_guard.py  # Gate/dungeon validation
│   │       └── investment_guard.py # Financial validation
│   │
│   └── domain/
│       ├── agents/              # AI agent implementations
│       │   ├── base_agent.py    # Common API logic
│       │   ├── analyst.py       # Strategic planner
│       │   ├── architect.py     # Blueprint designer
│       │   ├── writer.py        # Manuscript generator
│       │   ├── director.py      # Quality validator
│       │   ├── manager.py       # Arc coordinator
│       │   └── weaver.py        # Desire engine
│       │
│       └── strategies/          # Genre-specific strategies
│
├── config/                      # Global configuration
│   ├── settings.json            # Model tier assignments
│   ├── prompts/                 # Agent instruction manifests
│   │   ├── analyst_libraries.json
│   │   ├── architect_rules.json
│   │   ├── writer_rules.json
│   │   └── weaver_rules.json
│   ├── rules/                   # Genre-specific rules
│   └── terms/                   # Terminology dictionaries
│
├── projects/                    # Per-project workspaces
│   └── {project_name}/
│       ├── project_data.db      # SQLite database (PRIMARY)
│       ├── chroma_db/           # Vector store (DO NOT DELETE)
│       ├── config/
│       │   ├── bible.json       # Master lore (synced from DB)
│       │   ├── treatment.json   # Plot outline
│       │   ├── author_directives.txt # Custom rules
│       │   └── cash/
│       │       └── style_seeds_final.txt # Writing style
│       └── drafts/              # Final manuscripts
│           ├── 1.txt
│           └── ...
│
├── bible/                       # Template bibles for new projects
├── treatments/                  # Template treatments
├── tools/                       # Utility scripts
│   ├── RESET.py                 # Selective project reset
│   ├── concat_txt.py            # Concatenate episode files
│   ├── db_porter.py             # Database migration
│   ├── normalize_arcs_db.py     # Arc data normalization
│   └── fix_future_items.py      # Manuscript repair
├── docs/
│   └── 글도비_V0128_MANIFESTO.md # V0128 design specification
└── make_md.py                   # Convert manuscripts to markdown
```

---

## 🔄 Production Pipeline

### Stage Overview

```
Phase 0: Bible Recovery & DNA Sync
    ↓ Load lore + treatment, sync to SQLite

Stage 1: Volume Strategy (V41: Can skip if exists)
    ↓ Plan 10 volumes

Stage 2: Arc Tactical Design
    ↓ Design 50 arcs (5 per volume)

Stage 3: Episode Blueprinting
    ↓ Scene-by-scene plans (10 scenes per episode)

Stage 4: Sovereign Production
    ↓ Final manuscript writing (5000+ chars)
```

### Data Flow

```
Treatment (50 blocks)
    ↓ [Phase 0: Analyst]
MasterBible (world lore + HUD)
    ↓ [Stage 1: Analyst]
Volume Strategy (10 volumes × 1000 chars)
    ↓ [Stage 2: Analyst + Director]
Arc Tactical Docs (50 arcs with beats)
    ↓ [Stage 3: Weaver → Architect + Director]
Episode Blueprints (10 scenes each)
    ↓ [Stage 4: Writer + Director + Services]
Final Manuscript (5000+ chars) + HUD snapshot
    ↓
SQLite + ChromaDB + drafts/*.txt
```

---

## 🧩 Genre-Specific Systems

### HUD (Head-Up Display) Systems

Each genre tracks different character progression metrics:

**Wuxia (무협)**
- `realm` - 경지 (선천, 후천, 절정고수 등)
- `internal_energy` - 내공 수치
- `martial_arts` - 보유 무공 리스트
- `equipment`, `wealth`, `reputation`

**Hunter (헌터)**
- `hunter_rank` - 각성 등급 (E~S급)
- `gate_cleared` - 게이트 클리어 이력
- `skills` - 보유 스킬
- `stats` - STR/AGI/INT 등

**Investment (투자)**
- `wealth` - 현금 및 자산
- `companies` - 보유 기업
- `stocks` - 주식 포트폴리오
- `influence` - 영향력 지수

### Genre Guards

Validation rules enforce genre-specific logic:

- `wuxia_guard.py` - Martial power consistency, technique prerequisites
- `hunter_guard.py` - Gate mechanics, awakening logic
- `investment_guard.py` - Financial realism, market rules

---

## ⚙️ Advanced Features

### Quad-Cache System (V31)

Reduces API costs by ~90% using Google Gemini's cached content feature:

- **Writer Cache**: Writing manifesto + style seeds
- **Architect Cache**: Structural design rules
- **Analyst Cache**: Pattern libraries
- **Weaver Cache**: Foreshadowing rules

Caches stored in `sys_caches` anchor with 24-hour TTL. Auto-created on first use.

### V35 Emergency Surgery

When Director rejects the same episode 3+ times with LOGIC_ERROR:

1. Analyst performs "Arc Reconstruction Surgery"
2. 3-Window context analysis (prev/curr/next arc)
3. Causal relationship welding
4. 5x density increase in tactical docs
5. Architect enters "Bible Mode" for strict adherence

### Stage 1 Skip Option (V41)

If volumes already exist in database, Stage 1 menu offers skip option. Useful for:
- Continuing existing projects
- Manual volume editing workflows
- Iterative arc refinement

---

## 🐛 Troubleshooting

### ChromaDB Lock Error

**Symptom**: `PermissionError: [Errno 13] Permission denied: 'chroma.sqlite3'`

**Solution**:
1. Close all Python processes
2. Delete only `LOCK` and `*-shm` files in `projects/{name}/chroma_db/`
3. **Never** delete `chroma.sqlite3` or `*.wal` files
4. Or use `tools/RESET.py` for safe cleanup

### Agent Initialization Failure

**Symptom**: `🚨 [Critical] analyst 에이전트 초기화 실패`

**Solution**:
1. Verify `GOOGLE_API_KEY` in `.env`
2. Check model names in `config/settings.json`
3. Verify API quota (rate limits)

### HUD Not Updating

**Symptom**: Character state doesn't change after episodes

**Solution**:
1. Check if `commit_full_episode_data()` was called
2. Query `martial_tracker` table: `SELECT * FROM martial_tracker ORDER BY ep_num DESC LIMIT 1`
3. See `TEST_GUIDE.md` for detailed HUD verification procedures

### Bible Data Missing

**Symptom**: Lore information disappears after restart

**Solution**:
1. Check if `project_data.db` exists
2. Query: `SELECT * FROM anchors WHERE key='bible'`
3. SQLite DB is primary source, `config/bible.json` is backup only

---

## 📊 Performance & Costs

### API Costs (Gemini 3.0 Pro)

- **Without Cache**: ~$0.05-$0.10 per episode (~100K tokens)
- **With Cache**: ~$0.005-$0.01 per episode (~10K tokens)
- **Savings**: ~90% cost reduction

### Processing Time

- **Phase 0**: ~30 seconds
- **Stage 1**: ~5 minutes (10 volumes)
- **Stage 2**: ~30 minutes (50 arcs with validation)
- **Stage 3**: ~20 seconds per episode (blueprint)
- **Stage 4**: ~40 seconds per episode (writing + validation)

### Budget Estimate

- **250-episode project**: ~$12-15 (with caching)
- **Project goal**: Under ₩500,000 per project

---

## 🔧 Development & Customization

### Modifying Agent Behavior

1. Edit JSON manifests in `config/prompts/{agent}_rules.json`
2. Don't edit Python code directly
3. Invalidate cache:
   - Restart application, OR
   - Delete specific cache from `sys_caches` anchor in DB, OR
   - Use `tools/RESET.py`

### Adding a New Genre

1. Create guard: `modules/core/genre_guards/{genre}_guard.py`
2. Add HUD class: `modules/core/genre_hud_manager.py`
3. Register in `constants.py:GenreTypes`
4. Create laws file: `modules/core/laws/{genre}.json`
5. Update menu: `main_a.py:_select_genre()`

### Database Schema Changes

1. Edit: `modules/core/db_manager.py:_init_tables()`
2. Delete test `project_data.db`
3. Restart to recreate with new schema

---

## 📚 Key Documentation

- **CLAUDE.md** - AI agent operational guidance
- **TEST_GUIDE.md** - HUD update verification procedures
- **docs/글도비_V0128_MANIFESTO.md** - V0128 design specification (3-tier validation)
- **DEEP_CHECK_REPORT.md** - System stability audit
- **HUD_DIAGNOSIS_REPORT.md** - HUD system diagnostics

---

## 🔮 Version History

- **V41** (2026-01): Stage 1 skip option, flexible arc pacing
- **V40** (2024-01): Multi-genre architecture, centralized constants, progressive model tiers
- **V38** (2023-12): Agent initialization validation, NoneType guards
- **V35** (2023-11): Emergency surgery system, NPC HUD tracking
- **V31** (2023-10): Quad-cache system
- **V27** (2023-09): Treatment sync, author directives
- **V25** (2023-08): High-resolution strategy prompts
- **V20** (2023-07): Stable SQLite anchor architecture

Current Version: **V41**

---

## ⚠️ Important Safety Rules

1. **Never delete ChromaDB files** - Especially `chroma.sqlite3` and `*.wal`
2. **Always commit after DB writes** - Use `_safe_commit()` / `_safe_commit_async()`
3. **SQLite DB is primary** - If bible.json and DB diverge, DB wins
4. **Validate episode numbers** - Use `get_latest_episode_number()`, don't assume
5. **Check genre context** - Verify `self.selected_genre` before genre-specific logic
6. **Stage 4 fixed model** - Writer uses gemini-3-pro-preview regardless of retries
7. **Windows UTF-8 encoding** - Already handled in `main_a.py:5-11`, don't re-wrap

---

## 📄 License

본 프로젝트는 교육 및 연구 목적으로 제공됩니다.

**주의사항**:
- 생성된 소설의 저작권은 사용자에게 있습니다
- 상업적 사용 시 Google Gemini API 이용 약관을 준수하세요
- 프롬프트 엔지니어링 개선 제안은 환영합니다

---

**Created by**: Wuxia Studio Team
**Current Version**: V41 (January 2026)
**Powered by**: Google Gemini API
**System Goal**: 250화 연재 시 설정 붕괴율 0% + 문학적 품질 확보
