# Lead Rehydrate Checklist

Use this when a new session starts with `코덱스 리드`, `시스템 리드`, or equivalent.

## Read Order

1. Open the target GitHub issue.
2. Find the comment containing `<!-- lead-memory:v1 -->`.
3. Read `Issue Card`.
4. Read only active or blocked lane blocks in `Lane Card`.
5. Read `Canary Card`.
6. Open PRs only if `active_prs` is not `none`.
7. If the memory card is missing or contradictory, say `memory drift` and rebuild once instead of guessing.

## Return Format

Reply in this shape first:

- `Current issue:`
- `Issue state:`
- `Active lanes:`
- `Blockers:`
- `Waiting decision:`
- `Recommended next action:`

## Guardrails

- Do not reread the entire issue history by default.
- Do not treat `n8n` or ClickUp as the work truth.
- Do not expand worker count until the lane board is clear.
- If the card is getting long, shrink it instead of adding more sections.
