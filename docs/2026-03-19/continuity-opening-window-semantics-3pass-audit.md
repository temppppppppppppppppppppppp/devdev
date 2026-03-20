# continuity-opening-window-semantics-3pass-audit

Date: 2026-03-19
Status: final
Confidence: `0.96`
Canonical Path: `docs/2026-03-19/continuity-opening-window-semantics-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `dirty: large active worktree; git status --short count = 112`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-19/opus-modification-governing-3pass-reaudit.md`
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
Evidence Basis:
- `modules/validation/continuity_validator.py`
- `modules/domain/agents/continuity_manuscript.py`
- `tests/test_validation.py`
- `tests/test_continuity_modules.py`
Scope:
- audit whether live `opening_text` / `current_start` slices in continuity checks are accidental truncation bugs or intentional policy windows
- determine whether these paths should be converted to tail-preserving or full-manuscript scans
- clarify which parts are safe to leave as-is and which parts require per-rule policy review before any change
- non-goal: modify runtime behavior in this document

---

## Pass 1. Structure and Scope

This audit is intentionally narrow.

It covers only continuity rules that explicitly inspect the opening of the current manuscript.

Covered files:
- `modules/validation/continuity_validator.py`
- `modules/domain/agents/continuity_manuscript.py`

Key operator question:
- are these opening-only slices another generic `head-only truncation` problem, or are they deliberate continuity semantics that should not be blanket-converted?

This audit does not cover:
- general prompt-budget truncation in LLM-facing code
- Stage 4 context building
- whether the opening windows should later be re-tuned from `300/500/800/1000` to other sizes

---

## Pass 2. Evidence and Consistency

### 1. `continuity_validator.py` opening windows are explicit policy semantics

The validator-side code is not written like accidental truncation.

Observed live rules:
- `_check_active_pressure_continuity()` uses `opening_text = manuscript[:1000]`
- `_check_inventory_count_continuity()` uses `opening_text = manuscript[:800]`
- `_check_weapon_continuity()` uses `first_part = manuscript[:500]`
- `_check_injury_continuity()` uses `first_500 = manuscript[:500]`
- `_check_location_continuity()` uses `first_part = manuscript[:300]`

Why this matters:
- the docstrings are policy-shaped, not implementation leftovers
- `_check_active_pressure_continuity()` explicitly says persisted pressure vectors should still surface `in the opening unless intentionally cleared`
- `_check_inventory_count_continuity()` explicitly says it warns when the `opening count` drops below the persisted count

Supporting test evidence:
- `tests/test_validation.py::test_inventory_count_drift_warning_when_opening_count_drops`
- `tests/test_validation.py::test_threat_carryover_warning_when_opening_drops_pressure_cues`

Rerun evidence:
- `python -m pytest tests/test_validation.py -k "inventory_count_drift_warning_when_opening_count_drops or threat_carryover_warning_when_opening_drops_pressure_cues" -q`
- result: `2 passed, 29 deselected`

Conclusion:
- these validator windows are intentional continuity-policy windows
- blanket conversion to tail-preserving or full-manuscript scans would change rule meaning, not merely improve context retention

### 2. `continuity_manuscript.py` also appears opening-focused by design, and now has direct opening-window regression coverage

Observed live heuristics:
- rapid recovery check uses `current_start = manuscript[:500]`
- same-day / time-passed / recovery keyword heuristics inspect `manuscript[:500]`

Why this likely is intentional:
- these checks are about whether the current episode opening immediately acknowledges prior injury/event state
- the keyword sets are explicitly named `SAME_DAY_KEYWORDS`, `TIME_PASS_KEYWORDS`, `RECOVERY_KEYWORDS`
- the heuristics are written around early carry-over, not whole-manuscript semantic search

Direct regression evidence now covers:
- rapid recovery warning when recovery language appears in the opening
- same-day follow-up warning when a new major event starts without recovery evidence
- explicit time-passage override suppressing those same-day injury warnings

Rerun evidence:
- `python -m pytest tests/test_continuity_modules.py -k "rapid_recovery_in_opening or same_day_followup_ignores_injury or time_passage_in_opening_suppresses_same_day_injury_warning or test_time_flow_warning" -q`
- result: `4 passed, 66 deselected`
- `python -m pytest tests/test_continuity_modules.py -q`
- result: `70 passed`
- `python -m pytest tests/test_continuity_modules.py -k "test_intra_arc_injury_state_discontinuity or test_joint_docs_extractor_prompt_preserves_tail_context" -q`
- result: `2 passed, 65 deselected`

Conclusion:
- these manuscript-side opening slices should still be treated as policy heuristics, not as obvious truncation bugs
- there is now enough direct regression coverage to treat this area as an explicit policy boundary
- further changes should still be rule-by-rule, not blanket truncation cleanup

### 3. OPUS-style "generic truncation" framing would be misleading here

This area looks different from the many low-risk prompt hard cuts already fixed.

Those earlier fixes were mostly:
- LLM prompt budget paths
- head-only cuts that lost recent context accidentally
- places where tail-preserving truncation preserved intent while reducing distortion

This area is different because:
- the code is not asking "what context should the model see"
- the code is asking "does the opening itself acknowledge carry-over state"

Operational meaning:
- converting these checks into full-manuscript or tail-preserving scans would weaken the opening-pressure / opening-carryover gate
- that would be a policy change, not a safe hygiene fix

Conclusion:
- OPUS should not be trusted if it implicitly groups these opening windows with generic head-cut defects
- live code says these are continuity semantics first, slicing mechanics second

---

## Pass 3. Operational Meaning and Next Step

### Final judgment

1. `continuity_validator.py` opening windows should be kept as-is unless there is an explicit policy decision to redefine what "opening continuity" means.

2. `continuity_manuscript.py` opening heuristics should also be left unchanged for now.
The right next move is not automatic patching.
The right next move is targeted rule-by-rule review plus stronger direct tests if a behavior change is desired.

3. This is a medium-risk boundary.
It is no longer in the same class as low-risk truncation cleanup.

### Safe operating rule from this audit

Do:
- keep the current opening-window rules
- treat future changes here as policy work
- add direct tests before any change to `continuity_manuscript.py` opening heuristics

Do not:
- blanket-convert these slices to tail-preserving helpers
- replace opening windows with whole-manuscript scans without an explicit rule rewrite
- classify this area as a simple truncation bug based on OPUS text alone

### Recommended next actions

1. Record this result as a "keep unless policy rewrite" zone in ongoing medium-risk tracking.
2. If continuity semantics become a target, split work per rule:
   - pressure
   - inventory count
   - weapon carry-over
   - injury recovery
   - location / timeskip
3. Before changing `continuity_manuscript.py` further, keep and extend the current direct tests for:
   - rapid recovery in opening
   - same-day carry-over without recovery evidence
   - explicit time-passage override

### Audit result

- runtime code change: not recommended from this audit alone
- documentation conclusion: opening-window semantics are intentional enough to block blanket truncation cleanup
- next status: medium-risk item clarified, no patch applied
