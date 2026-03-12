# Decisions

- Decision: `chaebol_allowance_zero` is the first real preprocess base instance.
  - Why: canonical pitch, TR, BI, failed pair, and comparison history already exist.
  - Impact: this work becomes the reference case for Stage 0 hub operation.

- Decision: primary profile is `business_growth_profile`, secondary profile is `office_power_profile`.
  - Why: growth comes from operating cashflow and approval-line control, not market trading first.
  - Impact: capital, deal_type, HUD, and conflict interpretation stay aligned with support-system growth.

- Decision: failed numbered assets remain reference-only.
  - Why: they are useful for audit history but unsafe as overwrite targets.
  - Impact: canonical reruns must always write to unnumbered paths.

- Decision: current phase0 file is reference-usable but parser normalization remains an open follow-up.
  - Why: story structure is valuable, but strict deterministic tooling may choke on formatting.
  - Impact: Stage 0 can proceed now, builder hardening is deferred.

- Decision: preprocess `phase0_candidate.json` and `phase0_fixed.json` use the normalized 5-sheet shape.
  - Why: the preprocess base should hand off a stable contract with `work_id`, `arcs`, `npc_timeline`, `foreshadow_map`, and `opponent_transition_plan`.
  - Impact: later planning and production checks can consume the preprocess work area without depending on the richer legacy wrapper structure.

- Decision: `03_tr_blocks/block_001/` is seeded from the accepted canonical unnumbered TR, not the numbered failed draft.
  - Why: the first preprocess production unit should lock a known-good working reference before fresh reruns start.
  - Impact: block-level prompt/audit flow can be exercised without reintroducing failed numbered history into the live production base.

- Decision: `03_tr_blocks/block_002..070/` and `04_tr_final/` are completed as a canonical seed pass, not a fresh rerun.
  - Why: the immediate goal of the preprocess production base is to become a structurally complete working base that operators can inspect, diff, and reuse.
  - Impact: the preprocess base is now structurally complete as a seed baseline, but it is **not** a sequential production completion. Future reruns must still start at `Block 001` unless explicit sequential audit credit exists.
