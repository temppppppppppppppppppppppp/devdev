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
| `stage1.md` | Draft | No | TBD | TBD | TBD | |
| `stage2.md` | Active | Yes | 2026-02-25 | ENHANCE_ORDER 실행 | Codex | Stage2 호출 흐름 + Why(4Phase, 다중검증, Director audit 분리) 반영 |
| `stage3.md` | Active | Yes | 2026-02-25 | ENHANCE_ORDER 실행 | Codex | Stage3 호출 흐름 + Why(3후보 병렬, in-place, quality gate 80) 반영 |
| `stage4.md` | Active | Yes | 2026-02-25 | ENHANCE_ORDER 실행 | Codex | Stage4 호출 흐름 + Why(DB SSOT, Writer/Director 분리, post-select 검증) 반영 |
| `interfaces.md` | Active | Yes | 2026-02-25 | `f99119d` | Codex | DB 계약/Arc·Blueprint 모델/테이블 목록 반영 |
| `gotchas.md` | Active | Yes | 2026-02-25 | ENHANCE_ORDER 실행 | Codex | G-1~G-8 |
| `agent_graph.md` | Active | Yes | 2026-02-25 | ENHANCE_ORDER 실행 | Codex | 호출 트리 |
| `runbook.md` | Active | Yes | 2026-02-25 | `f99119d` | Codex | Menu 44/77/88/99 rollback-wipe-reset-rewind runbook and NPC history policy synced to code |
| `metrics_baseline.md` | Active | Yes | 2026-02-25 | `f99119d` | Codex | validation/constants/CLAUDE 기준값 반영 |

## Update Rule
- If behavior changes, update the matching row in the same PR/session.

