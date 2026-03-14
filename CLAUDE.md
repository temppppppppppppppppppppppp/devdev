# CLAUDE.md Compatibility Shim

This file is not the workspace SSOT.

Current workspace SSOT:
- `AGENTS.md`

Read order:
1. `AGENTS.md`
2. For system-track orders: `docs/implementation/system-order-init-harness.md`
3. Then follow the companion harnesses selected by the init harness

Conflict rule:
- if `CLAUDE.md` and `AGENTS.md` differ, `AGENTS.md` wins
- if a companion harness differs from old `CLAUDE.md` guidance, the harness wins

Historical note:
- older docs in this repository may still reference `CLAUDE.md`
- treat those references as historical context, not as the current operating authority
