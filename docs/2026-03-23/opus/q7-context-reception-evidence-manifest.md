Date: 2026-03-23
Document Type: Q7 context reception evidence manifest
Terminal: T7

---

## Evidence Sources

### Primary Scope Files Read

| File | Lines Read | Key Findings |
|---|---|---|
| `modules/domain/agents/chief_writer_context.py` | 1-511 (전수) | build_common_context 30+ 파라미터, _fit_compact_text head_ratio=0.55 고정 |
| `modules/domain/agents/chief_writer_context_packets.py` | 1-600 | prev_manuscripts_text에 smart_truncate() 기본값 적용 (L158), episode digest regex 기반 |
| `modules/core/stage4_context_builder.py` | 1-1200 | _apply_context_budget 보호 목록 2개만 (L1164-1170), _fit_context_text head=0.55 |
| `modules/core/stage4_context_packets.py` | 1-555 | build_continuity_packet budget=7000 하드코딩, NPC history [:100] 잘림 |
| `modules/core/prompt_builder.py` | 1-600 | Pure 가이드 생성, budget 인식 없음, 가이드 길이 1-3K |
| `modules/domain/agents/base_agent.py` | 1-900 | _apply_prompt_size_gate MAX_CONTEXT_CHARS=1M, ask() 최종 게이트 |

### Configuration Values Verified

| Key | Value | Source |
|---|---|---|
| `context.max_context_chars` | 1,000,000 | `config/settings/validation.yaml:76` |
| `smart_retrieval.stage2_total_budget` | 50,000 | `config/settings/validation.yaml:184` |
| `smart_retrieval.stage3_total_budget` | 80,000 | `config/settings/validation.yaml:185` |
| `smart_retrieval.stage4_total_budget` | 300,000 | `config/settings/validation.yaml:186` |
| `smart_retrieval.director_total_budget` | 300,000 | `config/settings/validation.yaml:187` |
| `smart_truncate` defaults | max_chars=1M, head_chars=80K | `modules/core/constants.py:145` |

### Truncation Points Inventoried

| Location | Mechanism | Max Chars | Head Ratio | Budget Aware |
|---|---|---|---|---|
| `chief_writer_context_packets.py:158` | `smart_truncate()` default | 1,000,000 | 80K/920K | No |
| `director_ensemble.py:729` | `smart_truncate(max_chars=200000)` | 200,000 | 110K/90K | No (hardcoded) |
| `director_ensemble.py:830` | `smart_truncate(max_chars=150000)` | 150,000 | ~82K | No (hardcoded) |
| `stage4_context_builder.py:113-126` | `_fit_context_text` | varies | 0.55 | Partially |
| `stage4_context_builder.py:1114` | `_apply_context_budget` | stage4_total_budget | N/A (compression) | Yes |
| `base_agent.py:310-334` | `_apply_prompt_size_gate` | 1,000,000 | 0.55 | N/A (final gate) |
| `stage4_context_packets.py:258` | `_fit_context_text(budget)` | 7,000 (CP) | varies | Fixed |
| `stage4_context_packets.py:470,555` | `_fit_context_text(max_chars)` | varies | varies | Partially |

### Budget Protection Targets

| Protected Prefix | File:Line | Protected From |
|---|---|---|
| `[작품 추적 슬롯 요약]` | `stage4_context_builder.py:1144` | _apply_context_budget compression |
| `[SC:arc_semantic_carryover]` | `stage4_context_builder.py:1168` | _apply_context_budget compression |
| **NOT protected**: `=== [Continuity Packet]` | — | Compressed with regular sections |
| **NOT protected**: World State condensed header | — | Compressed with regular sections |

### Cross-Reference with Fresh Run Report

| Finding | Fresh Run (4화) Status | Structural Risk |
|---|---|---|
| P1-1 prev_manuscripts 기본 1M 잘림 | 미발현 (4화 × 5K = 20K) | 200화+ 에서 발현 |
| P1-2 head/tail 비율 고정 | 미발현 (budget 미초과) | 에피소드 경계 깨짐 가능 |
| P1-3 CP/WS 비보호 | 미발현 (budget 50-70% 사용) | 장기연재에서 발현 |
| P1-4 Director 200K 하드코딩 | 미발현 (budget 미초과) | SSOT 원칙 위반 |
| P1-5 CW budget mismatch | 미발현 (텍스트 소량) | 장기연재에서 발현 |

### Grep Evidence Summary

| Pattern | Match Count | Key Observation |
|---|---|---|
| `smart_truncate` | 70+ usages across modules | 대부분 에이전트별 하드코딩 한도 사용 |
| `MAX_CONTEXT_CHARS` | 15 references | validation.yaml SSOT, constants.py 지연 로드 |
| `_apply_prompt_size_gate` | 3 call sites | ask() + ask_with_cached_context, 최종 게이트 |
| `_fit_context_text` | 18 usages | stage4_context_builder + packets 전용 |
| `context_budget\|total_budget` | 50+ references | context_advisor + stage4_context_builder 중심 |
