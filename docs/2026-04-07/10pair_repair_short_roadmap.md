# 10pair Repair Short Roadmap

Date: 2026-04-07
Status: active
Scope: post-benchmark repair triage for active and retired slots `01~10`

## Decision

- `02` is locked as the current benchmark winner.
- `08`, `09` go to `micro-fix` lane.
- `01`, `03`, `04`, `07` go to `full flagged-block sweep` lane.
- `05`, `06`, `10` are retired and deleted from the active candidate pool.

## Hard Rule

- `any no-cider block = YELLOW ceiling`
- therefore:
- partial repair is useful for progress tracking
- but grade unlock happens only when `no-cider count = 0`

## Slot Policy

- vacant slots `05/06/10` are deferred
- do not refill retired numbers during the current repair wave
- current repair wave touches active pairs only
- re-entry or renumbering is a later decision, not part of repair execution

## Retired Slots

- pair `05`
- pair `06`
- pair `10`

Current policy:

- do not repair
- do not rewrite
- do not resurface as fresh candidates
- keep only historical benchmark documents as residue
- core pair assets are intentionally deleted

Why:

- `05`: no-cider `32`
- `06`: no-cider `27`
- `10`: no-cider `22`
- the concepts themselves are retired, not salvage targets

## Repair Lane

- pair `08`: 4-block micro-fix
- pair `09`: 3-block micro-fix
- pair `07`: 10-block sweep
- pair `03`: 8-block sweep
- pair `04`: 13-block sweep
- pair `01`: 11-block sweep

## Execution Order

1. `08`
2. `09`
3. `07`
4. `03`
5. `04`
6. `01`

## Step-by-Step Rule

- repair one pair at a time
- finish pair repair before reopening benchmark on the next pair
- `08` and `09` use micro-fix only
- `07`, `03`, `04`, `01` use full flagged-block sweep
- `02` stays locked unless a new contradiction appears
## Operating Note

- `05/06/10` are not repair targets
- `05/06/10` are not rewrite targets
- `05/06/10` are retired slots
- do not reintroduce them into canon, benchmark, or fresh-candidate lanes without an explicit new-number re-entry decision
