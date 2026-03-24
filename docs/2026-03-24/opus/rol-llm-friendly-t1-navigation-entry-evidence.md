Date: 2026-03-24
Document Type: evidence manifest
Lane: T1 — Navigation / Entry / Reading Order
Parent Report: `docs/2026-03-24/opus/rol-llm-friendly-t1-navigation-entry.md`

## 1. File Inventory (Primary Scope)

| File | Lines | Inspected Ranges |
|---|---|---|
| `main_a.py` | 4,781 | L1-100 (bootstrap), L346-445 (SovereignApp init), L600-650 (keyword lists), L910-990 (writer guidance), L1373-1495 (boot), L2145-2230 (main menu), L2740-2800 (shutdown), L2900-3000 (delegates), L3020-3070 (state service delegates), L3550-3630 (narrative summary), L3775-3900 (stage 4 gateway), L4200-4280 (frontier lag), L4680-4781 (one-stop + __main__) |
| `modules/core/stage01_helpers.py` | 1,023 | L1-80 (module doc + class def), L520-550 (menu remap) |
| `modules/core/stage2_orchestrator.py` | 1,731 | L1-140 (TypedDicts + class def), L880-910 (main pipeline entry) |
| `modules/core/stage3_orchestrator.py` | 2,774 | L1-80 (module doc), L478-575 (class def + main entry) |
| `modules/core/stage4_orchestrator.py` | 2,414 | L1-100 (module doc + dataclass preamble), L226-460 (dataclass families), L461-540 (class def + lazy init) |
| `modules/api/bridge_server.py` | 2,372 | L1-80 (module doc + imports) |
| `modules/api/process_runner.py` | 808 | L1-60 (module doc) |
| `modules/api/control_plane_contract.py` | 92 | L1-92 (full file) |
| `modules/api/prompt_broker.py` | 205 | existence confirmed |
| `modules/api/run_validator.py` | 95 | existence confirmed |
| `modules/api/risk_approval.py` | 214 | existence confirmed |
| `modules/api/prompt_classifier.py` | 172 | existence confirmed |
| `modules/api/__init__.py` | 13 | existence confirmed |

## 2. Orientation Pack Drift Verification

| Check | Method | Result |
|---|---|---|
| Reading order file existence | glob + read | All 8 reading order entries exist at listed paths |
| Section divider presence in stage4_orchestrator.py | grep `═══` | Found at L60, 110, 166, 226, 293, 400, 623, 647, 880 |
| Section divider presence in stage3_orchestrator.py | grep `─────` | Found at L544, 696, 761, 877, 1010, 1642 |
| Section divider presence in stage2_orchestrator.py | grep `═══` | Found at L885, L1676 |
| `modules/api/` mentioned in orientation pack | grep `api\|bridge_server\|process_runner` | **0 matches** — confirmed gap |
| `[COMPAT]` markers on Stage 2 delegates | grep `\[COMPAT\]` in main_a.py | Found at L2924, L2933, L2937, L2941, L2945 |
| `\uXXXX` escape patterns | grep `\\u[0-9a-fA-F]{4}` in main_a.py | **0 matches** — confirmed resolved |
| Menu remap comment in stage01_helpers.py | direct read L529-536 | Present: `# Menu remap: show_menu returns 4 (style analysis) / 5 (work guard)...` |

## 3. Prior Survey Finding Resolution Status

| Prior Finding # | Description | Status | Evidence |
|---|---|---|---|
| #5 (P1) | `stage4_interview_round.py` `run()` entry at L2248, no dividers | T2 lane scope | — |
| #6 (P1) | `db_manager.py` 136 methods, no ToC | T5 lane scope | — |
| #7 (P1) | `main_a.py` L618-632 `\uXXXX` unicode escapes | **Resolved** | grep returns 0 matches |
| #8 (P1) | `stage4_orchestrator.py` L225 dataclass preamble, no grouping | **Resolved** | `# ── Dataclass family:` headers present at L60, L226, L293, L400 |
| #14 (P1) | `stage01_helpers.py` L529 silent choice remap | **Resolved** | Comment present at L531-532 |
| #16 (P1) | `main_a.py` L2919 thin delegates without `[COMPAT]` | **Resolved** | `[COMPAT]` on L2924, L2933, L2937, L2941, L2945 |
| #20 (P2) | `main_a.py` L2755 shutdown no phase comments | **Resolved** | Phase 1/2/3/4 comments at L2759-2778 |

## 4. Key Entry Points

| Entry | File:Line | Method |
|---|---|---|
| Console boot | `main_a.py:4771` | `SovereignApp().boot()` |
| Boot sequence | `main_a.py:1373` | `boot()` |
| Main menu loop | `main_a.py:2145` | `_run_main_process()` |
| Menu dispatch | `main_a.py:2217` | `_dispatch_main_process_choice()` |
| Stage 0 entry | `main_a.py:2780` | `_phase_0_recovery()` → stage01_helpers |
| Stage 2 entry | `main_a.py:2891` | `_stage_2_arcs()` → stage2_orchestrator |
| Stage 3 entry | `main_a.py:3148` | `_stage_3_batch_blueprinting()` → stage3_orchestrator |
| Stage 4 entry | `main_a.py:3780` | `_stage_4_v2_chief_writer()` — **lazy init gateway** |
| OneStop entry | `main_a.py:4682` | `_one_stop_pipeline()` |
| API entry | `modules/api/bridge_server.py:1` | FastAPI `app` (uvicorn) |
| API subprocess | `modules/api/process_runner.py:1` | `ProcessRunner.start()` |

## 5. Section Divider Map — main_a.py

| Line | Divider Text |
|---|---|
| L926-928 | `[V60.8] Writer 사전 가이드 시스템 - Director REJECT 방지` |
| L3029-3031 | `[V45] Validation Context 구성 헬퍼` |
| L3041-3043 | `[V41] Director Sovereignty 헬퍼 메서드` |
| L3558-3560 | `[V60.80] Stage 4 V2 - Chief Writer 주권주의 아키텍처` |
| L3562-3564 | `[V63.2] 10화 단위 내러티브 요약 시스템` |
| L3854-3856 | `[OneStop] Arc-by-Arc 자동 파이프라인` |

**Gap**: No dividers between L346 (class def) and L926 (first divider) — 580 lines.
