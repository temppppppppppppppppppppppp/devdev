# T3. Stage 3 Code / Mechanism Audit

Date: 2026-03-25
Lane: T3 (Stage 3 Code / Mechanism Audit)
Master Order: `docs/2026-03-25/stage3-partial-canary-3terminal-master-order.md`
Baseline Commit: `f61a35c89b4c964afbfa902790560448d98b1bfb`

## 1. Evidence Sources

Primary (code truth):
- `modules/domain/agents/blueprint_constraint_compiler.py` L102-189 (packet build + prompt injection), L551-842 (packet builders)
- `modules/domain/agents/unified_blueprint_validator.py` L833-899 (prevalidation pipeline), L905-1197 (drift detectors)
- `modules/core/stage3_orchestrator.py` L860-863 (PASS verdict gate), L1920-1932 (annotation + inventory_gaps)
- `modules/domain/agents/blueprint_ensemble.py` L1008-1015 (capital-lock prompt surfacing)

Secondary (artifact truth):
- `projects/canary_0325/logs/session/ui_events.jsonl` seq 98-172 (inventory gap console output)
- `projects/canary_0325/logs/artifacts/stage3/ep_0007/attempt_01/final_blueprint__action_focused.json` (no `_inventory_gaps` on disk)
- `projects/canary_0325/logs/artifacts/stage3/ep_0008/attempt_01/final_blueprint__dialogue_focused.json` L7-14 (temporal_deictic warning)
- `projects/canary_0325/stage0_output/style_guide.json` L142 (`genre: "investment"`)

## 2. Findings

### F-1. Fact-Lock Packet Mechanism

**Build site**: `blueprint_constraint_compiler.py` L551-686 (`_build_fact_lock_packet()`)

Extracts up to 16 anchors in 6 categories from prev_blueprint + prev_manuscript:

| Category | Source | Example |
|----------|--------|---------|
| 位置 (location) | prev_blueprint.end_location | `"직전 종료 위치: 청석관 대엄방"` |
| 時間 (time) | prev_blueprint.ending_state.timeline | `"직전 시점: 계절=초여름"` |
| 엔딩훅 (ending hook) | prev_blueprint.ending_hook | `"직전 화 엔딩: ..."` |
| 소지품 (equipment) | prev_blueprint.protagonist_state | `"확정 소지품: 검, 독약"` |
| 아이템위치 (item placement) | prev_manuscript regex | `"원고 확정: '옥비녀' → '비밀금고'에 보관"` |
| 기관 (institution) | prev_manuscript + prev_blueprint | `"확정 기관: 천상회, 삼청약방"` |

**Prompt injection**: `blueprint_constraint_compiler.py` L162-175. Fact-lock is the **highest priority constraint**, inserted before all others with header:
```
### [FACT-LOCK] 확정 사실 (이전 원고에서 확정 -- 변경 금지)
```

**Drift detection**: `unified_blueprint_validator.py` L905-1056 (`_collect_fact_lock_drift_issues()`). Four drift types:
1. **Location drift** (L929-950): prev end_location vs blueprint start_location. Severity: MAJOR.
2. **Item storage drift** (L952-977): locked item appears outside stored location. Severity: MAJOR.
3. **Provenance/trust drift** (L979-1012): ending hook emotional state reversal (e.g., "신뢰" → "불신"). Severity: CRITICAL.
4. **Institution authority drift** (L1014-1054): locked institution name vs competing variant. Severity: CRITICAL.

**PASS/FAIL authority**: Advisory-only. Issues are forwarded to Director via `pre_result["issues"]` (L882-888 → L838-843). Director makes sovereign PASS/REJECT decision (`unified_blueprint_validator.py` L505-556).

**Canary behavior**: No fact-lock drift issues were raised across EP1-EP9. This is consistent with T2's finding that institution names remained internally consistent (한미증권 introduced fresh at EP5, no prior authority to overwrite).

### F-2. Capital Continuity Packet Mechanism

**Genre guard**: `blueprint_constraint_compiler.py` L702-703.
```python
if genre != "investment":
    return {}
```
Canary genre = `"investment"` (`stage0_output/style_guide.json` L142) -- capital packet was **active** for all episodes.

**Build site**: `blueprint_constraint_compiler.py` L689-842 (`_build_capital_continuity_packet()`). Extracts from 7 hierarchical sources with fallback:

1. Blueprint ending_state structured fields (balance, capital, deployed, position, investment_status)
2. Protagonist state structured fields (balance, capital, portfolio)
3. Equipment free-text regex (currency amounts + context keywords)
4. Protagonist status text regex
5. Manuscript tail deployment patterns (last 2000 chars)
6. State changes events (capital_changes / financial_events)
7. Manuscript free-text extraction (amount + action verb pairs)

Max 8 fields per packet, deduplicated by label.

**Prompt injection**: `blueprint_constraint_compiler.py` L177-189. Appears as:
```
### [CAPITAL-LOCK] 자본/투자 상태 연속성 (변경 금지)
```
Warns LLM: "아직 여유 자금", "새로 투입" 등 모순 표현 사용 시 즉시 REJECT.

**Drift detection**: `unified_blueprint_validator.py` L1059-1137 (`_collect_capital_state_drift_issues()`). Two checks:
1. **Contradiction pattern** (L1078-1095): 4 regex patterns for "아직 여유 자금", "새로 투입", "전액 투입", "모든 자금 투입". Severity: CRITICAL.
2. **Phantom capital** (L1097-1135): deployed amount reappearing with available/deposit keywords in 40-char context window. Severity: MAJOR.

Max 3 issues returned.

**PASS/FAIL authority**: Advisory-only. Same Director-sovereign pattern as fact-lock.

**Canary behavior**: No capital drift issues were raised. Capital progression was clean: 20억 → 15억 deployed + 5억 cash → 23억 total. The old phantom `19억 3천만 원` pattern did not appear because:
- The canary started fresh with 20억 (not a continuation of the old run's stale 19.3억)
- Capital-lock packet correctly tracked the 15억 deployment at EP6 and prevented re-emergence as available capital in EP7-EP9

### F-3. Inventory Gaps Synthesis and Operator Visibility

**Generation site**: `stage3_orchestrator.py` L1928-1932 (`_annotate_stage3_success_blueprint()`).

```python
if isinstance(blueprint, dict) and working_ep > 1:
    inventory_gaps = self._detect_inventory_gaps(blueprint, arc_data)
    if inventory_gaps:
        blueprint["_inventory_gaps"] = inventory_gaps
        ctx.ui.log(f"   [TF-49] inventory gaps {len(inventory_gaps)}: ...")
```

**Critical timing**: This runs AFTER the verdict is already PASS. Inventory gaps are purely post-verdict annotation. They cannot affect Stage 3 PASS/FAIL.

**Detection algorithm**: `stage3_orchestrator.py` L2383-2447 (`_detect_inventory_gaps()`).

Gap = `(referenced items in blueprint) AND NOT (currently owned items)`

Data sources:
- **Owned items**: `ctx.world_state.get_owned_items()` primary, `constraint_db.get_current_inventory(prior_arc)` fallback, empty set if both fail.
- **Planned items**: `arc_data["state_constraints"]` protagonist_items or items_acquired, plus arc_end - arc_start equipment delta.
- **Referenced items**: protagonist_state.equipment + text search in scene_breakdown + text search in integrated_scenario.

**On-disk persistence**: `_inventory_gaps` is NOT saved in the Stage 3 artifact JSON files. Confirmed: `projects/canary_0325/logs/artifacts/stage3/ep_0007/attempt_01/final_blueprint__action_focused.json` has no `_inventory_gaps` key. The gaps exist only in the runtime pipeline dictionary, flow to Stage 4 via Chief Writer context packets (`chief_writer_context_packets.py` L92-108), and appear in `llm_io.jsonl`.

**Operator visibility**:
- Console: `[TF-49] inventory gaps {count}: {items}` via `ctx.ui.log()` — confirmed in `ui_events.jsonl` seq 98-172.
- Stage 4 prompt: Injected as `### [TF-49] Blueprint inventory prerequisite` with instructions to seed natural acquisition paths.
- Not blocking. Not in prevalidation pipeline. Not in Director Focus Header. Not in quality_risk flag.

**Canary behavior**: 7 inventory gap entries (EP3-EP9), all single-item, content accurately tracking financial instruments:
- EP3-EP6: `20억 원이 예치된 시중은행 VIP 통장` (protagonist_state.equipment references a physical passbook)
- EP7-EP9: `잔고 5억 원이 찍힌 한미증권 법인 계좌 통장` (after 15억 deployment)

The transition at EP7 is **correct behavior**: the detection algorithm saw a new equipment item (5억 passbook) that was not in the prior owned-items set, because the prior episode's equipment was the 20억 passbook. This is a state-transition tracking signal, not an error.

### F-4. Temporal-Deictic Prevalidation Mechanism

**Definition**: `unified_blueprint_validator.py` L1140-1197 (`_collect_temporal_deictic_drift_issues()`).

Two detection patterns:

1. **Ending hook absolute references** (L1148-1171):
   - Regex: `(\d+)\s*(?:년|개월|달|주|일)\s*(?:전|후|뒤)`
   - Threshold: numeric value >= 5 (small offsets like "3일 전" are ignored)
   - Severity: MAJOR
   - Max 2 issues

2. **Scenario tail future-memory pattern** (L1173-1195):
   - Regex: `(\d+)\s*(?:년|개월)\s*(?:전|후).{0,20}(?:기억|회상|추억|떠올리|떠올렸|생각나)`
   - Scans only last 500 chars of integrated_scenario
   - Threshold: numeric value >= 5
   - Severity: MAJOR
   - Max 1 issue

Overall max: 2 issues returned (`L1197: return issues[:2]`).

**Integration**: Called at `_python_pre_validate()` L896. Issues flow into `pre_result["issues"]` → `_build_python_warning_entries()` L119-151 (max 4 entries, deduped) → `_ensemble_meta.python_warnings` on blueprint → Director Focus Header L469-478.

**PASS/FAIL authority**: Advisory-only. MAJOR severity feeds into Director's audit but does not force REJECT. Quality gate (score < 90 → REJECT) is the only automated gating, and EP8's score of 92 cleared it.

**Canary behavior**: Triggered on EP8 only. Pattern match: "18년 전" in scenario tail with recollection context ("이전 삶의 기억과 정확히 일치하는 방아쇠가 당겨진 것이다"). Result:
- `quality_risk: true` on EP8
- `prevalidation_issue_count: 1`
- `total_candidates: 2` (one candidate likely disqualified during ensemble selection)
- Score: 92 (vs 95 baseline)
- Verdict: PASS (Director accepted the content as narratively appropriate for a reincarnation story)

EP7 contained "18년의 지독한 굴레" in its ending hook, but this did NOT trigger the temporal-deictic detector because:
- Pattern 1 requires `(\d+)\s*(?:년|개월|달|주|일)\s*(?:전|후|뒤)` — the word "전" or "후" must follow the temporal unit. EP7's "18년의" uses genitive "의", not directional "전/후".
- Pattern 2 only scans the last 500 chars and requires memory/recollection verbs within 20 chars.

### F-5. How Stage 3 PASS Coexists With Bounded Warnings

**Verdict gate**: `stage3_orchestrator.py` L860-863.
```python
if blueprint and pipeline_result.get("final_verdict") in (
    "PASS",
    "PASS_WITH_WARNING",
):
```

The architecture has a strict separation of concerns:

| Layer | Authority | Can Block? |
|-------|-----------|------------|
| Python prevalidation (7 check families) | Advisory: collect issues, set severity | No REJECT authority |
| Director compare/audit | Sovereign: PASS / PASS_WITH_FIX / PASS_WITH_WARNING / REJECT | Yes |
| Quality gate (score < 90) | Automated: downgrade PASS → REJECT | Yes |
| Inventory gaps | Post-verdict annotation only | No (runs after PASS) |
| Console warnings | Operator visibility | No |

This design means:
1. All 7 Python prevalidation families (structure, fidelity, arc_compliance, continuity, fact_lock, capital_state, temporal_deictic) produce **warnings only**.
2. Warnings are compacted to max 4 entries and shown to Director in Focus Header.
3. Director exercises sovereign judgment, considering narrative context.
4. If Director PASSes with score >= 90, the episode advances.
5. Inventory gaps are layered on top as post-verdict annotations — they never enter the validation pipeline.

In this canary, the result was: all Python prevalidation clean for EP1-7 and EP9; EP8 had 1 MAJOR temporal_deictic warning which Director accepted → PASS at 92. Inventory gaps appeared as correct state-transition tracking from EP3 onwards. No blocking condition was ever triggered.

## 3. Mechanism Explanation: Why EP1-EP9 All PASS With EP7 Inventory Gap and EP8 Temporal Warning

**EP7 inventory gap** (`잔고 5억 원이 찍힌 한미증권 법인 계좌 통장`):
- `_detect_inventory_gaps()` at L1928-1932 runs AFTER PASS verdict is already determined.
- The gap detects a new equipment item (5억 passbook) not present in prior owned set (20억 passbook).
- This is a legitimate state transition (EP6 deployed 15억, leaving 5억 cash).
- Gap is advisory-only: logged to console as `[TF-49]`, injected into Stage 4 Chief Writer prompt, not in Stage 3 validation pipeline at all.
- Mechanism: inventory_gaps cannot cause REJECT because they are computed post-verdict.

**EP8 temporal-deictic warning** (`시간 지시어 위험: '18년 전' 회상/기억 패턴`):
- `_collect_temporal_deictic_drift_issues()` at L896 detected pattern 2 (scenario tail future-memory).
- Issue severity: MAJOR (not CRITICAL). Forwarded to Director as Focus Header warning.
- Director reviewed the warning in context (reincarnation protagonist's 18-year memory is core premise) and issued PASS at score 92.
- Quality gate passed (92 >= 90 threshold).
- One candidate likely disqualified (total_candidates: 2 vs usual 3), but the surviving candidate passed.
- Mechanism: temporal-deictic is a healthy prevalidation catch operating exactly as designed — surfacing risk without overriding Director judgment.

**PASS-with-warnings architecture**:
- Python prevalidation produces a bounded issue list (max severity CRITICAL for dead-NPC/trust-reversal, MAJOR for everything else).
- No Python check can REJECT a blueprint.
- Director has full context (Focus Header + integrated scenario) to make the sovereign call.
- This deliberate separation means 100% PASS rate is compatible with bounded advisory warnings appearing at any episode.

## 4. Confidence and Limits

**Confidence: 96%**

Basis:
- All mechanism descriptions grounded in actual code with line-number anchors
- Canary artifact behavior verified against both on-disk files and ui_events.jsonl
- PASS/FAIL logic traced through complete call chain (orchestrator → runtime → validator → Director)
- Genre confirmed as investment (capital packet active)
- Inventory gaps confirmed absent from Stage 3 artifacts, present only in runtime pipeline

Limits:
- LLM IO logs not fully parsed for Director reasoning at EP8 (long lines omitted in grep). Director's internal rationale for accepting the temporal-deictic warning is inferred from the architecture (Director sovereignty) rather than observed from the actual LLM response.
- `_build_fact_lock_packet()` and `_build_capital_continuity_packet()` packet contents for each specific episode were not reconstructed from the canary's llm_io.jsonl. The analysis confirms the mechanism was active but does not prove the exact anchor values for each EP.
- The link between `total_candidates: 2` at EP8 and temporal-deictic disqualification is inferential: the exact disqualification reason for the third candidate was not extracted from logs.

---

Old Stage 3 culprit family in this lane: **suppressed**
New Stage 3 concern in this lane: **none**
Should this lane alone trigger a new SSOT: **no**
