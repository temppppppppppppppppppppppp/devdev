# Single SSOT Roadmap Contract

Date: 2026-03-14
Status: active
Applies To: global or multi-area system-track survey bundles

## 1. Purpose
- Keep roadmap authority singular even when many execution SSOTs are active.
- Prevent roadmap fragmentation from creating conflicting execution order.

## 2. Rule
For one active survey bundle, there must be exactly one roadmap with SSOT authority.

Allowed:
- many execution SSOT docs
- one canonical roadmap in `docs/YYYY-MM-DD/`
- one temp roadmap mirror in `docs/temp/execution-roadmap.md`
- multiple thematic lanes or sections inside that roadmap

Not allowed:
- two canonical SSOT roadmaps governing the same active bundle
- per-area roadmaps that compete with the master roadmap
- temp-only roadmaps with no canonical authority

## 3. Operational Interpretation
- area execution SSOTs define what should be realized for each area
- the single roadmap defines the realization order, dependencies, and queue semantics across the whole bundle
- if the bundle grows complex, add sections, phases, or lanes to the master roadmap rather than creating parallel SSOT roadmaps

## 4. Escalation Rule
If the current roadmap becomes too large:
- split execution SSOTs into lanes inside the master roadmap
- keep one top-level dependency graph
- keep one status ledger
- keep one temp roadmap mirror

Do not solve roadmap complexity by introducing a second SSOT roadmap.
