Date: 2026-03-27
Type: evidence manifest (T4 lane)
Parent Report: `docs/2026-03-27/opus/rol-llm-gimmick-t4-writer-context-injection.md`

## Path Inventory

| File | Lines | Role |
|---|---|---|
| `modules/domain/agents/chief_writer.py` | 2,283 | Ensemble engine + facade |
| `modules/domain/agents/chief_writer_context.py` | 604 | CW prompt assembly orchestrator |
| `modules/domain/agents/chief_writer_context_packets.py` | 1,126 | Bounded packet rendering |
| `modules/domain/agents/chief_writer_prompts.py` | 298 | YAML-SSOT prompt externalization |
| `modules/core/writer_template.py` | 420 | Blueprint-to-template mapping |
| `modules/core/prompt_builder.py` | 968 | SovereignApp prompt generation |
| `modules/core/stage4_context_builder.py` | 2,787 | Episode context + tier composition |
| `modules/core/stage4_context_packets.py` | 802 | Continuity/fact/relationship packets |

Total: 9,288 lines.

## Key Anchor List

| Anchor | File:Line | Gimmick |
|---|---|---|
| Tier composition | `stage4_context_builder.py:1261-1378` | G1 tier model |
| Advisory suppression | `stage4_context_builder.py:939-971` | G2 |
| Authority statement | `stage4_context_builder.py:996-1008` | G3 |
| Immutable fact call | `chief_writer_context.py:525-560` | G4 |
| STEP 0.5 precedence | `chief_writer_prompts.py:129-135` | G5 |
| Wuxia authority gate | `stage4_context_builder.py:1702-1718` | G8 |
| Investment gate | `chief_writer_context.py:226-227` | G6 |
| Incarnation type gate | `chief_writer_context.py:334-359` | G6 |
| Budget trim | `stage4_context_builder.py:1145-1255` | G7 |
| 35-param generate_ensemble | `chief_writer.py:566-615` | G9 |
| Genre code map duplication | `chief_writer.py:37-48` | G10 |
| Delegation band | `chief_writer.py:2144-2183` | Compat stubs |
| Navigation ToC | `stage4_context_builder.py:4-18` | Settled |
| Delegation chain docstring | `chief_writer_context_packets.py:1-11` | Settled |
| Canonical constraint inject | `stage4_context_builder.py:1681-1700` | Tier0 block |
| World state inject | `stage4_context_builder.py:1636-1651` | Tier0 body |
| Fact ledger inject | `stage4_context_builder.py:1664-1679` | Tier0 body |
| Timeline inject | `stage4_context_builder.py:1653-1662` | Tier0 body |
| Continuity packet inject | `stage4_context_builder.py:1720-1729` | Tier0 body |
| build_mandatory_context entry | `stage4_context_builder.py:2340-2378` | T3 handoff |
| build_round_context entry | `stage4_context_builder.py:2723` | Round-level entry |

## Prior Survey Findings Status

| Prior Finding | Status |
|---|---|
| ToC for stage4_context_builder.py (QW-1) | Landed (L4-18) |
| Delegation chain docstring for context_packets (QW-2) | Landed (L1-11) |
| generate_ensemble param docstring (QW-3) | Not landed |
| Compat stubs header (QW-4) | Landed (L2144-2155) |
| Prompt escape note (QW-5) | Not landed |
| Genre code map note (QW-6) | Not landed |
| Orientation pack dual-pipeline note (QW-7) | Landed (orientation pack section 9) |
| build_common_context debug log (QW-8) | Not verified |
| DR-1 WriterEnsembleRequest dataclass | Not started (still valid) |
| DR-2 Genre map consolidation | Not started (still valid) |
| DR-3 Compat stub removal | Not started (stubs reduced from ~22 to 9) |
