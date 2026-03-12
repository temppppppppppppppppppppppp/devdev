# Phase 0 Check

- Required sheets present:
  - PASS
  - `arcs=7`, `npc_timeline=10`, `foreshadow_map=6`, `opponent_transition_plan=3`
- Profile interpretation consistent:
  - PASS
  - story interpretation stays aligned with `business_growth_profile + office_power_profile`
  - profile semantics remain locked in `../profile_lock.json`
- Opponent allocation present:
  - PASS
  - each arc has `main_opponents`
  - `opponent_transition_plan` defines early / mid / final opponent factions
- Weakness pool present:
  - PARTIAL PASS
  - faction-level weakness is present in `opponent_transition_plan`
  - arc-level `weakness pool` is not yet expanded into the newer 3-variant style for every arc
- Manual fix list:
  - if this work is freshly rerun under the reinforced harness, add per-arc weakness pools with at least 3 structurally distinct weakness variants
  - keep `support-system cashflow` emphasis and do not drift into stock-spectacle framing
  - keep failed numbered assets reference-only

- Final judgment:
  - GO for preprocess planning handoff
  - usable as normalized Stage 0 fixed reference
