# tests/

Automated test suite for the production codebase.

## Layout

- `tests/*.py` — unit and integration tests (pytest)
- `tests/e2e/` — end-to-end smoke tests
- `tests/integration/` — cross-module integration tests
- `tests/chaos/` — chaos/fault-injection tests
- `tests/property/` — property-based tests
- `tests/stage3_isolated_test/` — Stage 3 isolated test fixtures
- `tests/stage4_v2_test/` — Stage 4 v2 isolated test fixtures
- `tests/conftest.py` — shared fixtures

## Running

```bash
# Memory-conservative mode (recommended on Windows):
python scripts/run_pytest_lowmem.py

# Targeted shard:
set PYTHONIOENCODING=utf-8 && pytest tests/test_director_modules.py -q

# Full suite (ensure memory headroom):
set PYTHONIOENCODING=utf-8 && pytest tests/ -q
```

## Conventions

- Tests must not import from `projects/` or `docs/`.
- `PYTHONIOENCODING=utf-8` is required on Windows.
- Parallel execution (`-n`, `xdist`) requires explicit operator approval.
