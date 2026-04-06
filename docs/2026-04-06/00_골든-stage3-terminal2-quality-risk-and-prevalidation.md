# Terminal 2: Quality-Risk, Semantic Coverage, and Prevalidation Residue

Date: 2026-04-06
Status: final
Scope: `00_골든` latest Stage3 run — ep2 and ep5 quality warnings only
Mode: read-only bounded survey

---

## Findings Summary

| Episode | Warning Family | Severity | Binding? | Front Blocker? |
|---------|---------------|----------|----------|----------------|
| ep2 | intent 불일치 (NPC 4명 미언급) | MINOR | No | No |
| ep2 | 시나리오 구체성 부족 (anchors 3 < 5) | MINOR | No | No |
| ep5 | intent 불일치 (NPC 4명 미언급) | MINOR | No | No |
| ep5 | 시나리오 구체성 부족 (anchors 0 < 5) | MINOR | No | No |
| ep5 | binding prevalidation (4 hidden issues) | MAJOR+ | Yes | **No** (persisted anyway) |

**Verdict: All warnings are bounded readiness residue. None are front blockers for S4.**

---

## Q1: Is ep2 intent mismatch a real semantic hole?

**No. It is incomplete episode-level mention coverage against arc-level NPC requirements.**

### Evidence

The `_collect_fidelity_prevalidation_issues` method (`modules/domain/agents/unified_blueprint_validator.py:873-901`) works as follows:

1. Extract all NPC names from `arc_data.state_constraints.relationship_changes`
2. Check if ANY of those names appear in the episode's `integrated_scenario` text
3. If zero names match, flag as MINOR fidelity issue

For ep2, Arc 1's relationship_changes list 4 NPCs. The ep2 scenario is exclusively a father-son confrontation scene between 한시우 and 한정호. The 4 unnamed NPCs are arc-wide characters (likely 서주희, brothers) who will appear in later episodes within the same arc.

The check is arc-scoped but applied at episode granularity. Ep2 mentions 한시우 + 한정호 (plus 집사 as a minor character). One of the 4 arc NPCs might be 한정호 himself, but the check requires ALL to match.

### Artifact evidence

- `logs/artifacts/stage3/ep_0002/attempt_01/final_blueprint__action_focused.json` L9-15:
  ```json
  "python_warnings": [{
    "category": "fidelity",
    "severity": "MINOR",
    "message": "intent 불일치: Arc 관계 변화 NPC 4명 blueprint 미언급",
    "source": "python_prevalidate"
  }]
  ```
- Director still scored ep2 at **94** and gave positive selection reasoning
- `fix_scope: "inplace"` — Director says text-level additions suffice, no structural change needed

### Assessment

This is a conservative check that casts too wide. A father-son confrontation scene in ep2 of a 5-episode arc is not required to mention every NPC whose relationship will change across the entire arc. The check is useful as an advisory signal but should not be read as a real semantic gap.

---

## Q2: Is scenario specificity residue still visible in the final ep2 blueprint?

**Yes. The MINOR warning persists in the artifact metadata. But the narrative content is substantively rich.**

### Evidence

The `_collect_scenario_density_issues` method (`unified_blueprint_validator.py:1767-1815`) counts concrete anchors using this regex:

```python
r"[가-힣]{2,6}(?:증권|은행|투자|...|약방|산장|무관)"
r"|\d[\d,.]*\s*(?:억|만|천만|백만|원|달러|...)"
```

Minimum required: 5 anchors. In ep2's 1,544-char scenario, the regex finds 3 matches (e.g., "200억", "18년"). Tokens like "코어밸류 캐피탈" and "성북동 본가" don't match the institution suffix pattern.

### Artifact vs persisted blueprint

- Artifact JSON shows: `"시나리오 구체성 부족: 구체적 앵커(기관/인물/수치) 3개 < 5개 (1544자 중)"`
- Persisted `blueprint_0002.txt`: Full narrative with "200억", "코어밸류 캐피탈", "한정호 회장", "성북동 본가 서재" — actually rich in specifics

The regex is narrower than the actual density of concrete information. The narrative mentions specific capital amounts, company names, and locations, but the pattern-matching misses several because the suffix list doesn't include "캐피탈" or "본가".

### Assessment

The specificity check is a blunt regex instrument. The ep2 narrative is substantively specific — it names a company, a capital amount, a location, and characters. The regex simply can't catch all valid anchor forms. This is pure advisory noise for ep2.

---

## Q3: What exactly does "binding prevalidation repair required" mean in ep5?

**It means MAJOR/CRITICAL severity issues were found in binding prevalidation categories, triggering an internal verdict change from PASS to PASS_WITH_FIX — but the orchestrator persisted the result as PASS anyway.**

### Mechanism trace

1. **Binding categories** (`unified_blueprint_validator.py:53-58`):
   ```python
   _BINDING_PREVALIDATION_CATEGORIES = {
       "scene_completeness", "arc_timeline", "capital_unit",
       "opening_anchor", "mission_clarity",
   }
   ```

2. **Binding filter** (`unified_blueprint_validator.py:195-209`): Only issues with `severity ∈ {MAJOR, CRITICAL}` AND `category ∈ _BINDING_PREVALIDATION_CATEGORIES` trigger the contract.

3. **Contract effect** (`unified_blueprint_validator.py:211-239`):
   - Changes verdict: `PASS → PASS_WITH_FIX`
   - Appends to reason: `"; binding prevalidation repair required"`
   - Sets `fix_scope = "inplace"`
   - Sets `fix_scope_reasoning = "Binding Python prevalidation invariants require bounded repair before plain PASS."`

4. **Orchestrator persistence** (`stage3_orchestrator.py:2152`):
   ```python
   "decision": final_verdict if final_verdict in ("PASS", "PASS_WITH_WARNING") else "PASS",
   ```
   `PASS_WITH_FIX` is mapped to `PASS` in the dashboard. Blueprint is saved regardless.

5. **Pass rate recording** (`stage3_orchestrator.py:1921`):
   ```python
   success=final_verdict in ("PASS", "PASS_WITH_WARNING"),
   ```
   `PASS_WITH_FIX` records as `success=False` — but this is monitoring only, not blocking.

### ep5 specifics

- `prevalidation_issue_count: 6` (artifact JSON L7)
- `python_warnings`: Only 2 visible (both MINOR, non-binding)
- **4 hidden issues**: At least one had MAJOR/CRITICAL severity in a binding category
- These 4 hidden issues are NOT stored in `python_warnings` because `_build_python_warning_entries` caps at 4 entries and the binding issues may have lacked message content or been ordered after the cap

The 4 hidden issues likely come from `scene_completeness`, `capital_unit`, `opening_anchor`, or `mission_clarity` checks. Examining the ep5 blueprint:
- Scene_2 and scene_3 lack `title` fields → possible `scene_completeness` trigger
- `capital_unit` alignment between "200억" (bible) and "2,000,000,000" / "20억" (scenario) → possible numeric mismatch
- Blueprint `start_location` is "성북동 본가" without explicit timeline anchor → possible `opening_anchor` trigger

### Code-path inconsistency found

The binding contract changes the verdict to `PASS_WITH_FIX`, but:
- Dashboard records it as `PASS` (L2152)
- `decisions.jsonl` records it as `PASS` (via `pass_rate_monitor`)
- `revision_required = True` is set (L1736) but only used in warning labels
- `success = False` in pass_rate_monitor (L1921)

This means the monitoring system sees ep5 as a **failure** while the pipeline treats it as a **success**. The operator sees "binding prevalidation repair required" in the console but the decisions log shows PASS.

---

## Q4: Are these front blockers or bounded readiness residue?

**Bounded readiness residue. None block S4 progression.**

### Why they are NOT blockers

1. **All 6 episodes persisted successfully.** The orchestrator does not gate on `PASS_WITH_FIX` — it saves the blueprint and proceeds.

2. **Scores confirm quality.** ep1=92, ep2=94, ep3=95, ep4=92, ep5=84, ep6=92. Even ep5 at 84 is well above any implicit rejection threshold.

3. **Narrative content is complete.** Both ep2 and ep5 blueprints have:
   - Full 4-scene breakdowns with goals, key_events, locations
   - Complete integrated scenarios with proper story arcs
   - Coherent ending hooks connecting to next episodes
   - Proper protagonist state tracking

4. **The binding contract's effect is advisory.** It sets `revision_required=True` and appends a note, but the orchestrator's save path ignores the distinction.

5. **The fidelity and scenario_density warnings are pattern-matching limitations.** The regex doesn't cover all valid anchor forms. The NPC check is arc-scoped but applied at episode level.

### If later fixes were needed

**Narrowest owner file set: 1 file.**

`modules/domain/agents/unified_blueprint_validator.py` owns 100% of the warning families in this terminal's scope:

| Method | Warning | Lines |
|--------|---------|-------|
| `_collect_fidelity_prevalidation_issues` | intent 불일치 | 873-901 |
| `_collect_scenario_density_issues` | 시나리오 구체성 부족 | 1767-1815 |
| `_collect_binding_prevalidation_issues` | binding filter | 195-209 |
| `_apply_binding_prevalidation_contract` | PASS → PASS_WITH_FIX | 211-239 |

Secondary concern (verdict persistence inconsistency): `modules/core/stage3_orchestrator.py` L2152 — maps `PASS_WITH_FIX → PASS` in dashboard while `pass_rate_monitor` records it as `success=False` (L1921).

### Potential bounded fixes (not proposed for this wave, noted for reference)

1. **Fidelity check narrowing**: Change `_collect_fidelity_prevalidation_issues` to check per-episode expected NPCs rather than all arc NPCs. Currently it casts too wide.
2. **Anchor regex expansion**: Add more institution suffixes ("캐피탈", "본가", "오피스") to `_anchor_re` in `_collect_scenario_density_issues`.
3. **Verdict mapping alignment**: Either `PASS_WITH_FIX` should be in the dashboard's PASS set, or `pass_rate_monitor` should not record it as failure. Current state creates a monitoring signal that contradicts the actual outcome.

---

## Test Coverage

`tests/test_stage3_clarity_density_wave1.py` covers:
- **Tranche A**: Authority re-banding in constraint formatting (8 tests) — IMMUTABLE/HARD/CONTINUITY/ADVISORY band ordering
- **Tranche B**: Scene-specificity prevalidation (thin goals detection, character coverage)

The binding prevalidation contract itself (`_apply_binding_prevalidation_contract`) and the fidelity NPC check are NOT covered by dedicated tests in this file. The scenario density anchor regex is tested implicitly through the scene-specificity tests.

---

## Cross-Reference with Other Terminals

- **Terminal 1 (throughput)**: ep5's 17m runtime and attempt_02 persistence may correlate with the 6-issue prevalidation count — more issues → more LLM repair cycles
- **Terminal 3 (continuity)**: ep5's `[PinGuard][WARN]` and `[TF-49] inventory gaps 2` are separate from the prevalidation residue examined here. The inventory gap items ("SW인베스트먼트 법인 통장", "사업자등록증") appear correctly in ep5's `protagonist_state.equipment`, indicating the blueprint captured them even though TF-49 flags them
- **Terminal 4 (observability)**: The verdict persistence inconsistency (PASS_WITH_FIX → PASS in dashboard, success=False in monitor) is an observability concern that Terminal 4 should note

---

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-06 output
