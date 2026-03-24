Date: 2026-03-24
Status: final
Document Type: survey report (T6 lane — Stage 3 Prompt Injection)
Canonical Path: `docs/2026-03-24/opus-residual/t6-stage3-prompt-injection.md`
Evidence Path: `docs/2026-03-24/opus-residual/t6-stage3-prompt-injection-evidence.md`
Source Survey: `docs/2026-03-24/stage2-stage3-residual-leakage-resurvey-10terminal-master-order.md`
Source Evidence:
- `modules/core/stage3_orchestrator.py` (prompt injection surfaces)
- `modules/domain/agents/blueprint_constraint_compiler.py` (constraint prompt assembly)
- `projects/00_001/logs/session/llm_io.jsonl` (LLM prompt trace)
- `projects/00_001/logs/artifacts/stage3/ep_0001/attempt_09/final_blueprint__emotion_focused.json`
- `projects/00_0324/logs/artifacts/stage3/ep_0001/attempt_01/final_blueprint__emotion_focused.json`
- `treatments/01_tr_투자물_골든_카나리아 테스트.json` (treatment block structure)
- `docs/2026-03-24/console.txt` (fresh live-run evidence)
Commit State:
- Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Baseline Dirty Summary: `dirty workspace; Wave 1 closed, Wave 2 survey finalized, fresh live-run evidence updated`

---

# T6. Stage 3 Prompt Injection — Residual Leakage Re-Survey

## 1. Executive Summary

Wave 1 successfully quarantined the three primary leakage vectors in Stage 3 prompt injection: `state_changes` is now filtered by episode, treatment block event fields (`event_villain`, `solution`, `reward`, `power_shift`) are removed, and stop line covers all future episodes.

However, two residual prompt injection surfaces still carry arc-global material into early-episode blueprint prompts:

1. **`genre_ext` in treatment block** — unfiltered investment-specific outcome data (`capital_after: 20억`, `method: 자산 정리 및 법인 설립`) enters the prompt for ALL episodes including ep1
2. **`semantic_carryover` in constraint prompt** — arc-end state descriptions (`continuity_checkpoints: 20억 자본금 확보 완료, 법인 설립 완료`) enter as `### ARC semantic carryover` header before the constraint block

Fresh live evidence shows these residuals are **secondary amplifiers**, not primary culprits: 00_0324 achieved 100% Stage 3 first-attempt pass rate despite both surfaces being active. However, 00_001 ep1 required 9 attempts and the final blueprint still absorbed ep3/ep4 scope — indicating these residuals can interact with sparse `episode_details` to cause overconsumption under certain conditions.

**Classification: secondary amplifier (not the sole culprit)**

---

## 2. Included Coverage / Exclusions

### Included
- `_inject_stage3_treatment_block_context()` — `stage3_orchestrator.py:1115-1171`
- `_inject_stage3_timeline_advisory()` — `stage3_orchestrator.py:1173-1215`
- `_finalize_stage3_blueprint_semantic_bundle()` — `stage3_orchestrator.py:1217-1322`
- `_build_stage3_blueprint_semantic_bundle()` — `stage3_orchestrator.py:1324-1367`
- Advisory builder functions:
  - `_build_world_state_advisory()` — `stage3_orchestrator.py:221-235`
  - `_build_fact_ledger_advisory()` — `stage3_orchestrator.py:204-218`
  - `_build_stale_seed_advisory()` — `stage3_orchestrator.py:172-201`
  - `_build_style_guide_advisory()` — `stage3_orchestrator.py:238-249`
  - `_build_stage3_work_focus_advisory()` — `stage3_orchestrator.py:323-412`
- `_compose_stage3_work_focus_text()` — `stage3_orchestrator.py:252-291`
- Continuity pins: `apply_continuity_pins()` call at `stage3_orchestrator.py:1958-1975`
- Constraint prompt assembly: `compile_to_prompt()` at `blueprint_constraint_compiler.py:119-212`
- `_normalize_semantic_carryover()` at `blueprint_constraint_compiler.py:653+`
- LLM I/O trace for ep1 blueprint calls in `projects/00_001/logs/session/llm_io.jsonl`
- Blueprint artifacts for both 00_001 and 00_0324 projects

### Excluded
- Stage 2 arc generation (T2/T3 scope)
- Constraint compiler internal logic (T5 scope — except `compile_to_prompt` which is the injection surface)
- Blueprint synthesis / integrated scenario (T7 scope)
- Stage 4 contradiction detection (T8 scope)
- LLM retrieval / context budget optimization (T9 scope)

---

## 3. Key Evidence

### E1. Treatment Block `genre_ext` — Confirmed Residual

**File**: `stage3_orchestrator.py:1141-1149`

```python
_genre_ext = _block.get("genre_ext", {})
if isinstance(_genre_ext, dict) and _genre_ext:
    _ge_lines = []
    for _gk, _gv in _genre_ext.items():
        if isinstance(_gv, dict | list):
            _ge_lines.append(f"    {_gk}: {_json.dumps(_gv, ensure_ascii=False)}")
        else:
            _ge_lines.append(f"    {_gk}: {_gv}")
    _block_fields.append("  genre_ext:\n" + "\n".join(_ge_lines))
```

Wave 1 removed `event_villain`, `solution`, `reward`, `power_shift` from the `content` dict. But `genre_ext` passes through with no filtering. For investment genre, this includes:

```
capital_before: 0 (정리 전)
capital_after: 20억 (정리 후)
capital_delta: +20억 (자산 정리)
method: 자산 정리 및 법인 설립
investment_type: 준비 단계
```

**Source**: `treatments/01_tr_투자물_골든_카나리아 테스트.json` block 0 `genre_ext`

**LLM I/O confirmation**: `projects/00_001/logs/session/llm_io.jsonl` L9 (first BlueprintEnsembleGenerator call) contains `genre_ext:\n    capital_before: 0 (정리 전)\n    capital_after: 20억 (정리 후)\n    capital_delta: +20억 (자산 정리)\n    ...method: 자산 정리 및 법인 설립`

This tells the ep1 LLM that the block outcome is "20억 확보" and "법인 설립", which are ep3/ep4 events.

### E2. `semantic_carryover` — Confirmed Residual

**File**: `blueprint_constraint_compiler.py:132-136`

```python
semantic_lines = self._format_semantic_carryover_lines(constraint_block.get("semantic_carryover"))
if semantic_lines:
    lines.append("### ARC semantic carryover")
    lines.extend(semantic_lines)
```

The `semantic_carryover` is arc-global by design. For 00_001:

```json
{
  "continuity_checkpoints": [
    "20억 자본금 확보 완료",
    "가족의 감시망에서 완전히 벗어남",
    "여의도 임시 사무실 계약 및 법인 설립 완료"
  ],
  "foreshadow_anchors": [
    "저녁 뉴스에서 '유가 상승세, 이란 핵 문제 재점화' 보도",
    ...
  ],
  "growth_justification": "미래 18년 치의 거시경제 지식 각성 및 초기 투자 자본 20억 원 확보"
}
```

**Source**: `projects/00_001/logs/artifacts/stage2/arc_001/attempt_01/final_arc__balanced.json`

The `continuity_checkpoints` describe arc-END state ("20억 자본금 확보 완료", "법인 설립 완료") that enters the ep1 prompt as if they are known checkpoints. No episode filtering exists in `_normalize_semantic_carryover()`.

**LLM I/O confirmation**: `projects/00_001/logs/session/llm_io.jsonl` L9 contains `[Arc Semantic Carryover]` section with these arc-end state descriptions.

### E3. Treatment Block Event Fields — Confirmed Clean (Wave 1)

**File**: `stage3_orchestrator.py:1128-1140`

```python
# [W1] Arc 개요 필드만 허용 — per-episode 이벤트 필드 제거
for _f in ("title", "emotional_beat", "foreshadow",):
    ...
# [W1] content.context만 허용, event_villain/solution 제거
for _cf in ("context",):
    ...
```

Only `title`, `emotional_beat`, `foreshadow`, and `content.context` are allowed. Event-specific fields (`event_villain`, `solution`, `reward`, `power_shift`) are removed. The structural header guard (L1152-1157) explicitly warns the LLM that specific events have been removed.

### E4. Advisory Surfaces — All Clean

| Advisory | File:Line | Temporal Scope | Leakage? |
|---|---|---|---|
| WorldState | `s3o:221-235` | Past-verified only | NO |
| FactLedger | `s3o:204-218` | Past-verified only | NO |
| StaleSeeds | `s3o:172-201` | 20+ episode old seeds only | NO |
| StyleGuide | `s3o:238-249` | No temporal content | NO |
| WorkFocus | `s3o:323-412` | Vector search from past-verified DB | NO |
| Timeline | `s3o:1173-1215` | Arc-to-arc time markers only | NO |

File abbreviation: `s3o` = `stage3_orchestrator.py`

### E5. Continuity Pins — Clean

**File**: `stage3_orchestrator.py:1958-1975`

`apply_continuity_pins()` takes:
- `previous_published_text` — prior episode manuscript (past-verified)
- `arc_tactical_text` — extracted via `extract_episode_tactical()` which filters by current episode

No future-episode content enters through this path.

### E6. Fresh Live Run Contrast

| Project | EP1 Attempts | EP1 Overconsumption? | EP3/EP4 Cascade? |
|---|---|---|---|
| 00_001 (pre-Wave-1 arc) | 9 | YES — ending_state = "20억 확보 + 법인 설립 + 첫 투자 직전" | YES — timeline reversal at ep3/ep4 |
| 00_0324 (fresh arc + Wave 1) | 1 | NO — ending_state = "감정 통제, 가족 대면 준비" | NO — 4/4 blueprints PASS R0 |

**Source**: Blueprint artifacts compared:
- `projects/00_001/logs/artifacts/stage3/ep_0001/attempt_09/final_blueprint__emotion_focused.json:26-30`
- `projects/00_0324/logs/artifacts/stage3/ep_0001/attempt_01/final_blueprint__emotion_focused.json`
- `docs/2026-03-24/console.txt:424-433`

---

## 4. Findings Ranked

### F1. `genre_ext` Unfiltered in Treatment Block — `likely residual leakage`

- **Severity**: MEDIUM
- **Mechanism**: `genre_ext` carries investment-genre-specific arc-level outcome data (`capital_after`, `method`, `deal_type`) that describes the BLOCK outcome, not the current episode's scope
- **Impact**: For investment genre, the LLM sees "this block ends with 20억 확보 + 법인 설립" at ep1, creating temptation to compress the entire block into one episode
- **Why not primary**: The 00_0324 run passed cleanly despite `genre_ext` being active — the expanded stop line and structural header guard were sufficient to contain it in that case
- **Interaction**: Amplifies when combined with sparse `episode_details` (only 2 items in 00_001 ep1)

### F2. `semantic_carryover` Arc-End State — `likely residual leakage`

- **Severity**: MEDIUM
- **Mechanism**: `continuity_checkpoints` and `foreshadow_anchors` describe arc-END state as "known checkpoints", entering the constraint prompt as `### ARC semantic carryover` with no episode filtering
- **Impact**: The LLM treats "20억 자본금 확보 완료" and "법인 설립 완료" as established narrative milestones that must appear, causing scope compression
- **Why not primary**: This is deliberately arc-global by design (meant for arc-level coherence). The issue is that it enters EVERY episode prompt equally, including ep1 where it overwhelms sparse positive authority
- **Note**: This overlaps with T5 (constraint compiler) scope — the injection surface is in the constraint prompt, but the carryover data originates from Stage 2 arc payload

### F3. Treatment Block Event Fields — `noise / not the culprit` (Wave 1 fix confirmed)

- `event_villain`, `solution`, `reward`, `power_shift` are all removed
- Only `title`, `emotional_beat`, `foreshadow`, `content.context` remain
- The structural header guard explicitly warns against consuming specific events
- **Confirmed clean by code audit and live evidence**

### F4. Advisory Injections — `noise / not the culprit`

- All six advisory surfaces inject past-verified or non-temporal content
- WorldState and FactLedger reflect only committed state up to the current episode
- StaleSeeds only surfaces 20+ episode old seeds
- StyleGuide has no temporal content
- WorkFocus uses arc_data for vector search queries but retrieves from past-verified DB
- **Confirmed clean by code audit**

### F5. Continuity Pins — `noise / not the culprit`

- Uses previous manuscript text and current-episode tactical extract only
- No future-episode content enters through this path
- **Confirmed clean by code audit**

---

## 5. Cleared Non-Culprits

| Surface | Verdict | Reason |
|---|---|---|
| Treatment block event fields | CLEAN (Wave 1) | `event_villain`/`solution`/`reward`/`power_shift` removed; only `title`/`emotional_beat`/`foreshadow`/`content.context` remain |
| WorldState advisory | CLEAN | Past-verified only |
| FactLedger advisory | CLEAN | Past-verified only |
| StaleSeeds advisory | CLEAN | Only 20+ episode old |
| StyleGuide advisory | CLEAN | Non-temporal |
| WorkFocus advisory | CLEAN | Vector search from past-verified DB |
| Timeline advisory | CLEAN | Arc-to-arc markers only (only active for arc_idx > 0) |
| Continuity pins | CLEAN | Previous manuscript + current-episode tactical only |
| Semantic context budget | CLEAN | Has cap and truncation |

---

## 6. Residual Culprit Candidate

**`genre_ext` in treatment block injection is the primary residual from this lane.**

It is a secondary amplifier that carries genre-specific arc-outcome data into every episode prompt. Alone, it is insufficient to cause overconsumption (00_0324 passed cleanly). But in combination with sparse `episode_details` and `semantic_carryover` arc-end state, it creates a prompt signal environment where:

- Positive authority (MUST_FOCUS, episode_details) = sparse, 2 items
- Negative authority (stop line, structural guard) = strong but requires LLM compliance
- Arc-outcome signals (genre_ext + semantic_carryover) = vivid, specific, and describe the ending state

The LLM resolves this signal conflict by attempting to reach the arc outcome within the current episode, overriding the negative constraints.

**The fix is bounded**: filter or quarantine `genre_ext` fields that describe arc-level outcomes (`capital_after`, `capital_delta`, `method`) so they do not enter early-episode prompts. Per-episode genre metrics (if they exist in the treatment) could still be allowed.

---

## 7. Next-Scope Recommendation

**Bounded patch scope for `genre_ext`**:

In `stage3_orchestrator.py:1141-1149`, apply the same Wave 1 pattern used for `content` fields:
- Remove or quarantine investment-outcome fields (`capital_after`, `capital_delta`, `method`, `deal_type`, `profit_loss`) from `genre_ext` when they describe arc-level (not current-episode) outcomes
- Alternatively, suppress the entire `genre_ext` section from the treatment block injection and document it as a deferred enhancement
- This is ~10-15 lines of code change in `_inject_stage3_treatment_block_context()`

**Separate recommendation for `semantic_carryover`**:
- This is partially T5 scope (constraint compiler) and partially T6 scope (prompt injection)
- The minimal fix: filter `continuity_checkpoints` entries by episode relevance, similar to how `_within_ep()` filters `state_changes`
- However, `semantic_carryover` lacks per-entry episode annotations, so filtering requires heuristic matching or structural redesign
- Defer to Codex merge for cross-lane coordination

---

## 8. Confidence And Limits

- **Confidence**: 93%
- **Basis**:
  - Code audit of all 9 prompt injection surfaces is complete and grounded in file:line anchors
  - Fresh live evidence from 2 projects (00_001, 00_0324) provides contrast for before/after comparison
  - LLM I/O trace confirms `genre_ext` and `semantic_carryover` reach the LLM in ep1 blueprint prompts
  - The 7% uncertainty comes from: (a) not having the exact prompt text for each failed 00_001 ep1 attempt to confirm which signal dominated, and (b) the `semantic_carryover` overlap with T5 scope makes it unclear which lane should own the fix

- **Limits**:
  - The llm_io.jsonl entries lack explicit `ep_num` fields, making per-episode prompt tracing imprecise
  - Whether `genre_ext` filtering would have prevented the 00_001 ep1 overconsumption is counterfactual — it can be confirmed only with a fresh run after the fix

---

## Mandatory Conclusions

- Can this seam alone explain ep1 overconsumption: **no** — `genre_ext` and `semantic_carryover` are secondary amplifiers that interact with sparse `episode_details` (T2 scope) to cause overconsumption; neither alone is sufficient
- Can this seam explain ep3/ep4 continuity-firewall replay: **partially** — the downstream cascade originates from ep1 overconsumption; if ep1 scope is properly bounded, ep3/ep4 replay disappears (confirmed by 00_0324 clean run)
- Can this seam be fixed in a bounded next wave: **yes** — `genre_ext` quarantine is ~10-15 lines in `_inject_stage3_treatment_block_context()`; `semantic_carryover` fix requires cross-lane coordination with T5 but is still bounded

---

## 3-Pass Audit Record

- Pass 1
  - confirmed this document is a survey report for the Stage 3 Prompt Injection lane
  - confirmed scope covers all prompt injection surfaces in stage3_orchestrator.py
  - confirmed treatment block, advisory, continuity pin, and semantic context surfaces are all addressed
  - confirmed findings are anchored to file:line references

- Pass 2
  - confirmed evidence: `genre_ext` enters unfiltered at `stage3_orchestrator.py:1141-1149`
  - confirmed evidence: `semantic_carryover` enters via `blueprint_constraint_compiler.py:132-136`
  - confirmed evidence: LLM I/O trace shows both surfaces in ep1 prompt
  - confirmed contrast: 00_0324 ep1 passed R0 with clean scope vs 00_001 ep1 required 9 attempts
  - confirmed Wave 1 event field quarantine is working correctly

- Pass 3
  - confirmed findings are ranked with explicit severity and interaction analysis
  - confirmed no overclaiming: findings are classified as "secondary amplifier" not "primary culprit"
  - confirmed next-scope recommendation is bounded and implementable
  - confirmed no execution SSOT or roadmap is created (survey only)
