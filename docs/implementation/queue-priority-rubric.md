# Queue Priority Rubric

Date: 2026-03-14
Status: active
Applies To: aggregate execution roadmaps and multi-item temp queues

## 1. Purpose
- Give a repeatable basis for ordering multiple execution SSOT items.
- Prefer substrate-first realization over ad hoc convenience ordering.

## 2. Core Ordering Rule
When two or more execution SSOT mirrors are active, order work by dependency and shared leverage first, not by whichever item looks shortest.

## 3. Scoring Dimensions
Score each item from `0` to `3` per dimension unless the dependency is absolute.

### A. Dependency / Blocker Weight
- `3`: blocks one or more other queue items
- `2`: strongly influences another item
- `1`: mostly independent
- `0`: leaf task with no dependents

### B. Shared Substrate Leverage
- `3`: creates infrastructure reused by many items
- `2`: creates infrastructure reused by one other item
- `1`: limited local reuse
- `0`: isolated implementation

### C. Operator or Runtime Risk
- `3`: high operator visibility or high runtime blast radius
- `2`: moderate risk or rollback concern
- `1`: narrow risk
- `0`: low-risk leaf work

### D. Verification Readiness
- `3`: verification path already exists and gives quick confidence
- `2`: verification is possible with modest setup
- `1`: verification is expensive or indirect
- `0`: verification path is currently weak

### E. Cleanup Simplification
- `3`: finishing this item collapses multiple queue branches or temp artifacts
- `2`: meaningfully simplifies roadmap state
- `1`: small cleanup benefit
- `0`: no meaningful cleanup impact

## 4. Ordering Heuristic
Default order:
1. absolute dependency blockers
2. high shared-substrate items
3. high operator-risk items with strong verification paths
4. lower-risk leaf conversions
5. cleanup-only or cosmetic items

## 5. Tie-Breakers
If scores are close:
1. prefer the item that unlocks the most downstream work
2. prefer the item with the clearer rollback path
3. prefer the smaller blast radius
4. prefer the smaller implementation slice

## 6. Guardrails
- Do not let `easy first` override hard dependency order.
- Do not hide priority decisions inside free-form prose; put them in the roadmap.
- Do not keep the rubric numeric when the dependency graph already makes the order obvious.
