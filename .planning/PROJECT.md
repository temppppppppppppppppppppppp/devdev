# PROJECT: 글도비 (Wuxia Studio)

## Overview

AI 기반 장편 웹소설 자동 생성 시스템. 47개 LLM 에이전트가 협업하여 Arc(전술 설계) → Blueprint(에피소드 설계) → Manuscript(원고 집필) 파이프라인을 실행한다. Director가 최종 품질 게이트를 담당하는 내각제 구조.

## Tech Stack

| Layer | Stack |
|-------|-------|
| Language | Python 3.12 |
| Entry Point | `main_a.py` — `SovereignApp` (7,069 LOC facade) |
| LLM Providers | Gemini (primary), Anthropic, OpenAI, Vertex |
| Database | SQLite + sqlite-vec (vector search) |
| Desktop | Electron (`geuldobi-desktop/`) + HTTP bridge (`modules/api/bridge_server.py`) |
| Testing | pytest (2,114 passed + 68 xfailed), 383 test files |
| Lint | Ruff (0 violations), pre-commit hooks |
| Config | YAML (system.yaml, validation.yaml, genre configs, prompt templates) |

## Architecture

### Production Pipeline (4 Stages)

```
Stage 0: 세계관 초기화 (POV 선택, 스타일 가이드, 작품 설정)
    ↓
Stage 2: Arc 생성 (Stage2Orchestrator → 4-phase ensemble)
    ↓
Stage 3: Blueprint 생성 (Stage3Orchestrator → 3-phase ensemble)
    ↓
Stage 4: Manuscript 집필 (Stage4Orchestrator → Interview Round → 6-Tier Validation → Director 판정)
```

### Key Modules

| Module | Path | LOC | Role |
|--------|------|-----|------|
| SovereignApp | `main_a.py` | 7,069 | Main facade, stage orchestration |
| Stage2Orchestrator | `modules/core/stage2_orchestrator.py` | 1,731 | Arc generation |
| Stage3Orchestrator | `modules/core/stage3_orchestrator.py` | 2,774 | Blueprint generation |
| Stage4Orchestrator | `modules/core/stage4_orchestrator.py` | 2,414 | Manuscript writing |
| Stage4InterviewRound | `modules/core/stage4_interview_round.py` | ~5,000 | Director round-robin + advisory |
| BaseAgent | `modules/domain/agents/base_agent.py` | 2,288 | LLM client base (context caching) |
| Director | `modules/domain/agents/director.py` | 387 | Quality gate facade + 5 sub-modules |
| ChiefWriter | `modules/domain/agents/chief_writer.py` | 2,274 | Manuscript generation |
| DBManager | `modules/core/db_manager.py` | ~3,000 | SQLite persistence, vector retrieval |
| ValidationOrchestrator | `modules/validation/validation_orchestrator.py` | ~1,200 | 6-tier validation pipeline |
| PromptBuilder | `modules/core/prompt_builder.py` | 968 | Dynamic prompt composition |

### DI Context Pattern (Phase 4C Standard)

각 Stage Orchestrator는 `StageNContext` 슬롯 클래스를 통해 의존성을 주입받음:
- `Stage2Context` (44 slots) — `modules/core/stage2_context.py`
- `Stage3Context` (19 slots) — `modules/core/stage3_context.py`
- `Stage4Context` (5+13+7 slots) — `modules/core/stage4_context.py`

### 6-Tier Validation Pipeline

1. **PreLLM** — Python-only 빠른 검사 (no LLM)
2. **Continuity** — 상태/NPC drift 감지
3. **Blocking** — 하드 게이트 (entity, scene, consistency)
4. **Consistency** — 서사 정합성
5. **Scoring** — 6차원 품질 점수 (character, emotion, dialogue, commercial, pattern, satisfaction)
6. **Advisory** — 8개 병렬 LLM 검증 (TruthGate, NpcDrift, NumericDrift 등)

### Genre Support (10 genres)

Wuxia, Hunter, Investment, Fantasy, Composer, Cooking, Alt History, Actor, Sports, Medical
- Guard chain: `GenreGuard → WorkGuard(optional) → StyleGuard(optional)`
- Config: `config/genres/*.yaml`

### Long-run Consistency Systems (V68)

- **WorldStateManager** (`world_state.py`) — 세계 상태 문서
- **FactLedger** (`fact_ledger.py`) — 누적 팩트 원장
- **Episode Chain Links** — 에피소드 연결고리
- **Volume/Series Summary** — 계층적 요약 피라미드

## Codebase Metrics

| Metric | Value |
|--------|-------|
| Production .py files | ~266 (`modules/`) |
| Test files | 383 (`tests/`) |
| Genre guard files | 14 |
| Config YAML/JSON | ~170 |
| Scripts | 47 (`scripts/`) |
| LLM agents | 47 |
| Validators | 16 |

## Directory Structure

```
글도비/
├── main_a.py                    # Entry point
├── AGENTS.md                    # Workspace SSOT (governance)
├── pyproject.toml               # Python 3.12, Ruff config
├── modules/
│   ├── core/          (143)     # Orchestrators, DB, state, validation infra
│   ├── domain/agents/ (50)      # LLM agents (Director, ChiefWriter, Analyst...)
│   ├── validation/    (16)      # 6-tier validation pipeline
│   ├── api/           (8)       # HTTP bridge, control plane
│   ├── models/        (5)       # Data models (Arc, Blueprint, Manuscript, NPC)
│   ├── narrative_router/ (6)    # Genre family routing
│   └── protocols/     (4)       # Interface contracts
├── config/
│   ├── system.yaml              # API, cache, timeout
│   ├── settings/validation.yaml # Validation thresholds SSOT
│   ├── genres/                  # 11 genre YAML configs
│   ├── prompts/                 # LLM prompt templates
│   └── models.yaml              # LLM model selection
├── tests/                       # 383 test files
├── scripts/                     # 47 utility scripts
├── docs/                        # Dated audits, harnesses, implementation docs
├── geuldobi-desktop/            # Electron desktop app
├── bible/                       # Story bible JSON
├── treatments/                  # Story treatment JSON
└── work_guards/                 # Per-work guard YAML
```

## Governance (AGENTS.md)

### 4 Absolute Principles
1. Python은 수집만, 판단은 LLM이
2. 팩트시트 수정 권한은 LLM만
3. Director 주권주의 (내각제)
4. 사망 캐릭터는 회상/언급만

### Track Split
- **System Track**: 코드/테스트/런타임/DB/리팩터/성능
- **Narrative Track**: 작품 기획/Treatment/BI/감리/정합성

### Key Policies
- DB TEXT 필드 절삭 금지 (최대 보존)
- 콘솔 로그 축약 금지 (최대 표시)
- UTF-8 전역 불변식
- Production 함수 180+ LOC 금지
- 50+ direct methods → module split 검토
- Document 3-pass 감리 후 저장

## Completed Work

- **Opus TF Audit**: 35건 전량 완료 (3 CRITICAL + 20 IMPORTANT + 12 INSIGHT)
- **Debug Sweep 1-3차**: 전량 완료 (DI sync, StateTracker 통합, 27건 위생)
- **Phase 4C Architecture**: DI Context 표준화, Stage3 lazy init, facade+sub-module 패턴
- **V64-V69**: Delegation, long-run consistency, NPC registry 수정, context 확장
- **Post-Sweep Stabilization**: DB-SSOT 통합, Patch Mode, Passrate 전략, Ensemble Feedback

## Current Priority (2026-03-24)

**Stage 4 Immutable Fact Convergence** — Stage 4 time-to-convergence 개선. 반복적인 hard continuity/history/state drift로 인한 2-3 라운드 churn 감소가 목표.
- 대상: `four_phase_arc_runtime.py`, `blueprint_constraint_compiler.py`, `chief_writer_context.py`, `stage4_interview_round.py`, `world_state.py`, `fact_ledger.py`
- 접근: immutable fact packet assembly/classification
