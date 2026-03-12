# Doc Status

Purpose:
- Show documentation freshness and code-sync status at a glance.

## Status Legend
- `Active`: Used in current operation.
- `Draft`: Skeleton or work-in-progress.
- `Deprecated`: Kept for history, not for current operation.

## Tracking Table

| Document | Status | Code Sync (Yes/No) | Last Verified Date | Commit | Owner | Notes |
|---|---|---|---|---|---|---|
| `stage0.md` | Active | Yes | 2026-02-25 | `f99119d` | Codex | Stage0 확장/역설계/스타일분석 및 DB 동기화 경로 반영 |
| `stage1.md` | Active | Yes | 2026-03-10 | `d2d935b` | Codex | Stage 1 volume split / Stage01Helpers 경계 / 검증 리스크 원장 동기화 |
| `stage2.md` | Active | Yes | 2026-03-02 | `8476bc2` | Opus | TF-47 constraint_block 누적 방지, PASS_WITH_FIX 재심사, LM-G NarrativeContextFormatter, SC-0~6 Smart Context, CentralSchemaBuilder 반영 |
| `stage3.md` | Active | Yes | 2026-03-02 | `8476bc2` | Opus | PASS_WITH_FIX 3-tier 라우팅, CentralSchemaBuilder(TF-45) 반영 |
| `stage4.md` | Active | Yes | 2026-03-02 | `8476bc2` | Opus | LM-A~F advisory 체인, PASS_WITH_FIX 3-tier+InPlace state_updates, QualityGate bypass(TF-46), JSON 파싱 강화(TF-47), Hybrid Retrieval 반영 |
| `interfaces.md` | Active | Yes | 2026-03-02 | `8476bc2` | Opus | PASS_WITH_FIX verdict 스키마, state_updates 전파 우선순위, npc_relationship_history 추가 |
| `gotchas.md` | Active | Yes | 2026-03-02 | `8476bc2` | Opus | G-9~G-12 추가 (QualityGate bypass, constraint_block 초기화, JSON rfind, state_updates 우선순위) |
| `agent_graph.md` | Active | Yes | 2026-03-02 | `8476bc2` | Opus | LM-A~F advisory 체인, LM-G Stage2 advisory, PASS_WITH_FIX 경로, Context Caching 6사이트, SC 반영 |
| `runbook.md` | Active | Yes | 2026-02-25 | `f99119d` | Codex | Menu 44/77/88/99 rollback-wipe-reset-rewind runbook and NPC history policy synced to code |
| `metrics_baseline.md` | Active | Yes | 2026-03-02 | `8476bc2` | Opus | 테스트 기준선 3,040 passed, Ruff 0 violations 반영 |

## Update Rule
- If behavior changes, update the matching row in the same PR/session.

