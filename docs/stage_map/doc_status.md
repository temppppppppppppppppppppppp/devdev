# Doc Status

Purpose:
- Show stage_map freshness and code-sync status at a glance.
- Distinguish active SSOT docs from deprecated historical helpers.

## Status Legend
- `Active`: Used in current operation.
- `Deprecated`: Historical reference only. Do not treat as current code truth.

## Tracking Table

| Document | Status | Code Sync (Yes/No) | Last Verified Date | Commit | Workspace State | Owner | Notes |
|---|---|---|---|---|---|---|---|
| `README.md` | Active | Yes | 2026-03-13 | `e18f9910` | dirty | Codex | stage_map navigation and metadata rule updated to current workspace |
| `UPDATE_ORDER.md` | Active | Yes | 2026-03-27 | `eb7a41d8` | dirty | Codex | canonical refresh order; metrics baseline source provenance corrected |
| `doc_status.md` | Active | Yes | 2026-03-27 | `eb7a41d8` | dirty | Codex | active/deprecated ledger resynced after baseline provenance correction |
| `stage0.md` | Active | Yes | 2026-03-13 | `e18f9910` | dirty | Codex | Stage0 provenance, reference_excerpt risk, preset/UI drift synced |
| `stage1.md` | Active | Yes | 2026-03-13 | `e18f9910` | dirty | Codex | Stage1 live-but-weak UI seam and operator caveats synced |
| `stage2.md` | Active | Yes | 2026-03-13 | `e18f9910` | dirty | Codex | Stage2 callback seam, missing world_state slot, schema risks synced |
| `stage3.md` | Active | Yes | 2026-03-13 | `e18f9910` | dirty | Codex | Stage3 gate=90, patch accumulation, entity-registry/test gaps synced |
| `stage4.md` | Active | Yes | 2026-03-13 | `e18f9910` | dirty | Codex | Stage4 1M-context truth, EMPTY nuance, NPC profile resolution synced |
| `interfaces.md` | Active | Yes | 2026-03-13 | `e18f9910` | dirty | Codex | stage handoff and verdict invariants re-locked to current code |
| `gotchas.md` | Active | Yes | 2026-03-13 | `e18f9910` | dirty | Codex | obsolete 80-gate assumptions removed; live pitfalls only |
| `agent_graph.md` | Active | Yes | 2026-03-13 | `e18f9910` | dirty | Codex | Stage2/3/4 call graph and DI seams refreshed |
| `runbook.md` | Active | Yes | 2026-03-13 | `e18f9910` | dirty | Codex | safe-op semantics verified against main_a/project_service current workspace |
| `metrics_baseline.md` | Active | Yes | 2026-03-27 | `eb7a41d8` | dirty | Codex | full-suite baseline source corrected to dated audit evidence |
| `SYNC_CHECK.md` | Active | Yes | 2026-03-13 | `e18f9910` | dirty | Codex | sync check now starts from UPDATE_ORDER and dirty workspace diff |
| `FILL_ORDER.md` | Deprecated | No | 2026-03-13 | `e18f9910` | dirty | Codex | historical fill helper; superseded by `UPDATE_ORDER.md` |
| `ENHANCE_ORDER.md` | Deprecated | No | 2026-03-13 | `e18f9910` | dirty | Codex | historical enhancement helper; superseded by `UPDATE_ORDER.md` |

## Update Rule
- When active stage_map content changes, update the matching document footer and this table in the same session.
- Deprecated rows may preserve history, but must not contain live operational guidance that conflicts with current code.

## Last Verified
- Date: 2026-03-27
- Commit: `eb7a41d8`
- Workspace State: dirty
- Code Sync (Yes/No): Yes
- Verified By: Codex
