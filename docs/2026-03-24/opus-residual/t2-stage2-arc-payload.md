Date: 2026-03-24
Status: final
Document Type: lane survey report (T2)
Lane: Stage 2 Arc Payload
Canonical Path: `docs/2026-03-24/opus-residual/t2-stage2-arc-payload.md`
Master Order: `docs/2026-03-24/stage2-stage3-residual-leakage-resurvey-10terminal-master-order.md`
Evidence Ledger: `docs/2026-03-24/opus-residual/t2-stage2-arc-payload-evidence.md`
Commit State:
- Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Baseline Dirty Summary: `dirty workspace; Wave 1 closed, Wave 2 survey finalized, fresh live-run evidence updated`

---

# T2. Stage 2 Arc Payload — Residual Leakage Survey

## 1. Executive Summary

The Stage 2 arc payload (`final_arc__balanced.json`) is correctly structured for per-episode use. The `episode_details`, `tactical_doc`, `beat_sequence`, and `must_focus` extraction surfaces all scope content to the current episode. The Wave 1 `_within_ep()` filter successfully blocks future-episode `state_changes` entries with explicit episode tags.

**However, the dominant residual vector is `semantic_carryover`.** This field is arc-global by design and enters the blueprint prompt without any episode filtering. For EP1, it presents arc-END achievements ("20억 자본금 확보 완료", "여의도 임시 사무실 계약 및 법인 설립 완료") as continuity checkpoints that the LLM interprets as current-episode obligations.

Two secondary gaps also remain:
- `_extract_immutable_fact_carryover()` has no episode filtering (EP2+ leak)
- `_within_ep()` passes entries with `episode: null` (low severity in 00_001, potentially higher elsewhere)

**Residual culprit candidate: `semantic_carryover` is the dominant remaining seam for EP1 overconsumption.**

---

## 2. Included Coverage / Exclusions

### Included
- `projects/00_001/logs/artifacts/stage2/arc_001/attempt_01/final_arc__balanced.json` (full)
- `modules/domain/agents/blueprint_constraint_compiler.py` (full, post-Wave-1 state)
- `modules/domain/agents/blueprint_ensemble.py` (arc_focus resolution + prompt assembly)
- `modules/core/stage3_orchestrator.py` (treatment block injection)
- Stage 3 blueprint artifacts: ep1/attempt_09, ep3/attempt_01, ep4/attempt_02
- `projects/00_001/logs/episode_production.jsonl` (production pattern)

### Exclusions
- Stage 2 validation pipeline (covered by T3)
- Stage 3 prompt injection surfaces beyond constraint compiler (covered by T6)
- Stage 4 contradiction detection (covered by T8)
- LLM I/O raw traces (covered by T9)
- Code changes (survey only)

---

## 3. Key Evidence

### E1. Arc Payload Field-by-Field Temporal Scope

| # | Field | Temporal Scope | EP-Filtered? | Arc-Global Content for EP1 | Verdict |
|---|-------|---------------|-------------|---------------------------|---------|
| 1 | `episode_details` | Per-episode | YES | None | CLEAN |
| 2 | `tactical_doc` → `must_focus` | Per-episode (extracted) | YES | None | CLEAN |
| 3 | `beat_sequence` | Arc-global | Fallback only | N/A | CLEAN |
| 4 | `state_changes` | Per-entry tagged | YES (Wave 1 `_within_ep`) | 3x `episode: null` entries pass | MOSTLY CLEAN |
| 5 | **`semantic_carryover`** | **Arc-global** | **NO** | **continuity_checkpoints, growth, foreshadow, relationships** | **SUSPECT** |
| 6 | `joint_docs` | Arc-global | NO (but overridden) | physical_inventory = EP4 items | CLEAN (overridden by arc_start_state) |
| 7 | `state_constraints` | Arc-global | N/A | arc_start_state correct for EP1 | CLEAN |
| 8 | `constraint_summary` | Empty | N/A | N/A | N/A |

### E2. `semantic_carryover` Content in 00_001 Arc

Source: `final_arc__balanced.json:155-184`

```json
{
  "continuity_checkpoints": [
    "20억 자본금 확보 완료",           // EP3 event
    "가족의 감시망에서 완전히 벗어남",    // EP2 event
    "여의도 임시 사무실 계약 및 법인 설립 완료"  // EP4 event
  ],
  "foreshadow_anchors": [
    "저녁 뉴스에서 '유가 상승세, 이란 핵 문제 재점화' 보도",  // EP4 event
    "아버지가 '그룹 일은 형들이 알아서 할 거다'라고 발언",      // EP2 event
    "한시우의 '그룹 돈은 한 푼도 안 받겠다'는 선언"            // EP2 event
  ],
  "growth_justification": "미래 18년 치의 거시경제 지식 각성 및 초기 투자 자본 20억 원 확보",  // EP3 result
  "relationship_rationale": [
    { "npc": "한정호 (아버지)", "trigger": "독자적인 투자사 설립 및 자립 선언" },  // EP2 event
    { "npc": "한태준 (큰형)", "trigger": "막내의 사업 선언" },                     // EP2 event
    { "npc": "한태민 (둘째형)", "trigger": "막내의 사업 선언" }                     // EP2 event
  ]
}
```

All four sub-fields describe EP2-4 events. All are injected into EP1's blueprint prompt via `_format_semantic_carryover_lines()`.

### E3. How `semantic_carryover` Enters the EP1 Prompt

Path: `compile()` L97 → `_normalize_semantic_carryover()` L654 → `compile_to_prompt()` L132-136 → `_format_semantic_carryover_lines()` L702-729

The prompt section rendered for EP1:
```
### ARC semantic carryover
- relationship 한정호 (아버지): 독자적인 투자사 설립 및 자립 선언
- relationship 한태준 (큰형): 막내의 사업 선언
- relationship 한태민 (둘째형): 막내의 사업 선언
- growth_justification: 미래 18년 치의 거시경제 지식 각성 및 초기 투자 자본 20억 원 확보
- foreshadow: 저녁 뉴스에서 '유가 상승세, 이란 핵 문제 재점화' 보도
- foreshadow: 아버지가 '그룹 일은 형들이 알아서 할 거다'라고 발언
- foreshadow: 한시우의 '그룹 돈은 한 푼도 안 받겠다'는 선언
- continuity: 20억 자본금 확보 완료; 가족의 감시망에서 완전히 벗어남; 여의도 임시 사무실 계약 및 법인 설립 완료
```

**No episode filtering.** No "this is the arc-end target, not EP1's target" framing. The LLM reads `continuity: 20억 자본금 확보 완료; ... 법인 설립 완료` as something the current episode should achieve.

### E4. EP1 Blueprint Confirms Overconsumption

Source: `stage3/ep_0001/attempt_09/final_blueprint__emotion_focused.json`

- `ending_state.protagonist_status`: "자본금 20억 확보 및 법인 설립을 완료하고 첫 투자를 목전에 둔 상태"
- `protagonist_state.equipment`: ["SW인베스트먼트 법인 인감도장", "20억 예치 법인 계좌 OTP"] (EP4 items)
- `integrated_scenario`: Contains 자산 정리 → 여의도 사무실 → 법인 설립 → OTP → WTI 차트 → 이란 뉴스 (EP2-4 events compressed into EP1)

This matches the `semantic_carryover` continuity checkpoints exactly. The LLM treated arc-end checkpoints as EP1 obligations.

### E5. `_extract_immutable_fact_carryover()` Has No Episode Filter

Source: `blueprint_constraint_compiler.py:506-550`

For `arc_position > 1` (EP2+), IFC reads ALL `state_changes` sub-categories without episode filtering:
- `npc_deaths`: all entries (correct here, 0 in 00_001)
- `relationship_changes`: first 5 entries regardless of `episode` tag → includes `episode: null` and `episode: 4` entries
- `major_items`: first 5 entries regardless of `episode` tag → includes EP4 items (법인 인감도장, 20억 OTP)
- `skill_acquisitions`: all entries (0 in 00_001)

For EP2 in 00_001, IFC would emit:
```
- 관계 확정: 한정호 (아버지) → 의외라는 시선...  (episode=null)
- 관계 확정: 한태준 (큰형) → 무관심 유지          (episode=null)
- 관계 확정: 한태민 (둘째형) → 무관심 유지         (episode=null)
- 관계 확정: 한정호 → 의외라는 시선                (episode=2)
- 아이템 확정: SW인베스트먼트 법인 인감도장 (획득) (episode=4)
- 아이템 확정: 20억 예치 법인 계좌 OTP (획득)      (episode=4)
```

EP4 items presented as "불변 사실" at EP2.

### E6. `episode: null` Entries Bypass `_within_ep()`

Source: `blueprint_constraint_compiler.py:564-575`

```python
def _within_ep(entry: object) -> bool:
    ...
    ep_val = entry.get("episode")
    if ep_val is None:
        return True  # ← passes through
```

Three `relationship_changes` entries in 00_001 have `"episode": null`:
- 한정호: "기대 제로" → "의외라는 시선" (EP2 reaction)
- 한태준: "무관심" → "무관심 유지" (benign)
- 한태민: "무관심" → "무관심 유지" (benign)

Low severity for 00_001. Pattern risk is higher for arcs where null-episode entries describe significant state changes.

### E7. `joint_docs` Is Arc-Global But Correctly Overridden

Source: `blueprint_constraint_compiler.py:445-503`

`_extract_inherited_state()` reads `joint_docs.physical_inventory` (EP4 items) into `inherited_state.equipment`, but then `state_constraints.arc_start_state.equipment` overrides it (L478-487) for EP1. For EP2+, `prev_blueprint.protagonist_state.equipment` overrides both (L490-501).

Not a practical leak for inherited_state.

---

## 4. Findings Ranked

| Rank | Finding | Classification | Severity | File Anchor |
|------|---------|---------------|----------|-------------|
| F1 | `semantic_carryover` injected arc-globally into every episode prompt with no episode scoping | **confirmed residual leakage** | HIGH | `bcc:97,654-729` + `bcc:132-136` |
| F2 | `_extract_immutable_fact_carryover()` reads all state_changes without episode filter | **confirmed residual leakage** | MEDIUM (EP2+ only) | `bcc:506-550` |
| F3 | `_within_ep()` passes `episode: null` entries | **likely residual leakage** | LOW (benign in 00_001, pattern risk) | `bcc:564-575` |
| F4 | `episode_details` sparseness (2 items/ep) | **secondary amplifier** | LOW (Wave 2 topic) | arc JSON L103-131 |
| F5 | `joint_docs` describes arc-end state | **noise / not the culprit** | NONE (correctly overridden) | `bcc:452-459,478-487` |

File abbreviations: `bcc` = `blueprint_constraint_compiler.py`

---

## 5. Cleared Non-Culprits

| Field | Why Cleared |
|-------|------------|
| `episode_details` | Per-episode filtered, 2 items each, correctly scoped |
| `tactical_doc` → `must_focus` | Per-episode extraction via `extract_episode_tactical()` confirmed correct |
| `beat_sequence` | Fallback only, not primary content source |
| `joint_docs` → `inherited_state.equipment` | Overridden by `arc_start_state` (EP1) or `prev_blueprint` (EP2+) |
| `state_constraints.arc_start_state` | Correctly describes EP1 start, not arc-end |
| `constraint_summary` | Empty string in 00_001, not a factor |
| `state_changes` (explicit episode entries) | Wave 1 `_within_ep()` correctly filters EP4 items, EP3 NPC, EP2 relations |
| Treatment block event fields | Wave 1 quarantine confirmed at `s3o:1127-1157` |

---

## 6. Residual Culprit Candidate

**`semantic_carryover` is the dominant remaining seam.**

Evidence chain:
1. Arc payload generates `semantic_carryover` with arc-global continuity_checkpoints, growth_justification, foreshadow_anchors, and relationship_rationale
2. `BlueprintConstraintCompiler` normalizes and formats these without any episode awareness
3. The formatted lines appear at the TOP of the constraint prompt as "ARC semantic carryover"
4. The EP1 LLM reads "continuity: 20억 자본금 확보 완료; 법인 설립 완료" and absorbs these as current-episode targets
5. EP1 blueprint ending_state confirms: "자본금 20억 확보 및 법인 설립 완료"

**The causal link is concrete:** the exact content from `semantic_carryover.continuity_checkpoints` appears as accomplished facts in the EP1 blueprint's ending_state.

Secondary:
- `_extract_immutable_fact_carryover()` compounds the problem for EP2+ by presenting unfiltered EP4 items as "불변 사실"
- `episode: null` entries in `_within_ep()` are a latent risk

---

## 7. Next-Scope Recommendation

**Bounded fix scope (additive to Wave 1):**

1. **`semantic_carryover` episode-aware rendering** — `blueprint_constraint_compiler.py:654-729`
   - Options:
     - (a) Add an episode-framing header: "아래는 Arc 전체 종료 시점의 목표/복선입니다. 이번 화(제N화)에서 모두 달성할 필요 없습니다."
     - (b) Filter `continuity_checkpoints` and `growth_justification` to only include items achievable by `ep_num`
     - (c) Demote `semantic_carryover` to a deferred-reference section clearly labeled as arc-end target, not current-episode obligation
   - Option (a) is most conservative — no structural change, adds framing
   - Option (c) is most effective — prevents LLM from treating arc-end as current-ep

2. **`_extract_immutable_fact_carryover()` episode filter** — `blueprint_constraint_compiler.py:506-550`
   - Apply the same `_within_ep()` pattern used in `_summarize_state_changes()`
   - Filter so only `episode <= ep_num` entries appear as immutable facts

3. **`_within_ep()` null-episode policy** — `blueprint_constraint_compiler.py:564-575`
   - Change `ep_val is None → return True` to `ep_val is None → return False` (conservative: exclude ambiguous entries)
   - OR: treat null as arc-global and exclude when `ep_num` < arc `ep_end`

All three are bounded to `blueprint_constraint_compiler.py` and can be fixed without reopening Wave 2 density/allocation work.

---

## 8. Confidence and Limits

- **Confidence: 96%**
- **Basis:**
  - The causal chain from `semantic_carryover` → EP1 prompt → EP1 blueprint overconsumption is directly traceable through code paths and artifact content
  - The IFC leak is confirmed by code inspection (no episode filter present)
  - The null-episode bypass is confirmed by code inspection
  - Fresh live evidence (attempt_09 blueprint) confirms the problem persists after Wave 1

- **Limits:**
  - This lane only covers the arc payload composition and constraint compiler surfaces
  - Whether `semantic_carryover` is the SOLE remaining culprit or one of several requires cross-lane analysis (T5, T6, T7, T9 may find additional surfaces)
  - The severity of `semantic_carryover` may vary by genre and content richness

---

## Mandatory Conclusions

- **Can this seam alone explain ep1 overconsumption: YES** — `semantic_carryover.continuity_checkpoints` directly maps to the EP1 blueprint's overconsumption pattern. The exact content ("20억 자본금 확보 완료", "법인 설립 완료") appears as accomplished facts in the EP1 ending_state.
- **Can this seam explain ep3/ep4 continuity-firewall replay: YES (indirectly)** — EP1 overconsumption caused by `semantic_carryover` cascades into EP3/EP4 contradictions. Additionally, `_extract_immutable_fact_carryover()` compounds the problem for EP2+ by presenting EP4 items as confirmed facts.
- **Can this seam be fixed in a bounded next wave: YES** — All three fixes are bounded to `blueprint_constraint_compiler.py:506-729` and require no Stage 2 redesign, no Stage 4 changes, and no broad refactor.

---

## 3-Pass Audit Record

- Pass 1
  - confirmed this document is a lane survey report (T2), not an execution SSOT
  - confirmed scope covers the primary question: which arc payload fields already contain multi-episode collapsed state
  - confirmed all arc payload fields are individually classified
- Pass 2
  - confirmed evidence anchors are concrete: file:line for code, JSON line numbers for arc artifact, blueprint artifact content for causal chain
  - confirmed `semantic_carryover` causal chain is traceable end-to-end (arc JSON → compiler → prompt → blueprint)
  - confirmed Wave 1 fixes are verified in current code state
  - confirmed no overclaiming: `joint_docs` was investigated and found correctly overridden rather than assumed clean
- Pass 3
  - confirmed the next-scope recommendation is bounded and actionable
  - confirmed the findings do not reopen Wave 2 density/allocation topics
  - confirmed mandatory conclusion lines are present and consistent with evidence
