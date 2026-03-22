# DB Bootstrap Runtime Module-Split Design

Status: final
Date: 2026-03-22
Commit: `41067be5156ce0efb1c675d3bd847bfc073c2a2b`
Confidence: 0.96
3-pass audit:
- Pass 1: scope and cohesion check passed
- Pass 2: code-evidence and dependency check passed
- Pass 3: tranche ordering and contract-boundary check passed

## Decision

`DBManager._boot_db()` has crossed the point where the next readability ROI is a bounded bootstrap-runtime split, not more same-file helper extraction.

The next tranche should introduce `DBBootstrapRuntime` and move the boot-time schema/bootstrap sequencing there while keeping `DBManager` as the owner of connection recovery, public initialization, transactional APIs, data migrations, and DML/public persistence contracts.

## Why Now

The pressure is concentrated in one owner method:

- `DBManager._boot_db()` (`695 LOC`)

Its body is not a thin shell. It still mixes:

- connection bootstrap and WAL/PRAGMA setup
- optional `sqlite-vec` extension loading
- base table creation across many domains
- compatibility migrations via `ALTER TABLE`
- index creation and boot-time schema normalization
- one-shot post-boot migration handoff

The live code evidence is broad enough that same-file leaf extraction will mostly create wrapper churn:

- `33` `CREATE TABLE IF NOT EXISTS` statements
- `33` `CREATE INDEX IF NOT EXISTS` statements
- `17` `ALTER TABLE` compatibility migrations

That is a cohesive bootstrap concern, not a residual wrapper problem.

## Why This Boundary Is Viable

The boot-time schema/bootstrap sequence is cohesive enough to move as one bounded concern.

At the same time, several responsibilities should remain on `DBManager` in tranche 1 because they are owner/public or connection-contract concerns, not readability-only helpers:

- `__init__()` and `initialize_db()`
- `_connect_with_integrity_recovery()`, `_is_db_corruption_error()`, `_quarantine_corrupt_db()`
- `_ensure_open()` and transaction APIs such as `begin()`, `commit()`, `rollback()`, and `transaction()`
- generic compatibility helpers such as `_get_table_columns()` and `_ensure_columns_exist()`
- post-boot one-shot migrations:
  - `_migrate_vec_memory_db()`
  - `_migrate_world_state_timeline_if_needed()`
- all DML/read-write/public persistence methods (`save_*`, `load_*`, telemetry sinks, quality sinks, etc.)

This makes the bootstrap split viable without rewriting connection ownership or public DB contracts.

## Proposed Boundary

Create:

- `modules/core/db_bootstrap_runtime.py`

Recommended shape:

```python
class DBBootstrapRuntime:
    def __init__(self, owner: "DBManager") -> None:
        self.owner = owner

    def boot(self) -> None:
        ...
```

The owner should keep `_boot_db()` as a thin shell in tranche 1 and delegate to `self.bootstrap_runtime.boot()` for the schema/bootstrap sequence, then run the two existing owner-side post-boot migrations.

## First Tranche Scope

1. Add `modules/core/db_bootstrap_runtime.py`
2. Attach `self.bootstrap_runtime` inside `DBManager.__init__()`
3. Move the main bootstrap sequence out of `_boot_db()`:
   - connection acquisition and cursor handoff
   - WAL/PRAGMA setup
   - optional `sqlite-vec` extension load
   - base table creation
   - compatibility `ALTER TABLE` work that is currently inline
   - boot-time index creation and schema normalization
4. Leave `DBManager._boot_db()` as a thin owner shell that:
   - acquires the runtime path
   - delegates the schema/bootstrap sequence
   - runs `_migrate_vec_memory_db()`
   - runs `_migrate_world_state_timeline_if_needed()`

## Keep On Owner

In tranche 1, keep these concerns on `DBManager`:

- `__init__()` and `initialize_db()`
- corruption detection and connection recovery
- transaction control APIs
- generic compatibility helpers
- post-boot one-shot migrations
- all DML/read-write/public persistence methods
- any public/test-facing DB contract that already assumes `DBManager` ownership

This keeps the first split bounded and avoids mixing readability work with connection-lifecycle or persistence-contract changes.

## Why This Ordering

This ordering gives the readability win without forcing broad external churn.

It keeps stable:

- the existing `DBManager` public construction and initialization path
- corruption-recovery semantics and integrity-check behavior
- transaction and cursor ownership
- one-shot vec/timeline migration contracts
- the large surface of downstream `save_*` / `load_*` callsites and tests

That lets tranche 1 target the real problem, which is the oversized bootstrap/schema sequence itself.

## Non-Goals

Do not do these in the first tranche:

- move connection-recovery helpers out of `DBManager`
- move transaction/public persistence APIs out of `DBManager`
- redesign sqlite corruption recovery or WAL semantics
- merge DB bootstrap with unrelated runtime modules
- rewrite DML methods or broader repository contracts

## Stop Condition

Stop and write a follow-up design note if tranche 1 requires:

- moving connection recovery out of `DBManager`
- changing transaction/public DB contracts
- broad rewrites across unrelated `save_*` / `load_*` APIs
- mixing readability work with repository/protocol redesign

## Recommended Next Step

Implement the first bootstrap-runtime split tranche:

- add `modules/core/db_bootstrap_runtime.py`
- move the large schema/bootstrap sequence out of `_boot_db()`
- keep connection recovery, post-boot migrations, transaction control, and public persistence authority on `DBManager`
