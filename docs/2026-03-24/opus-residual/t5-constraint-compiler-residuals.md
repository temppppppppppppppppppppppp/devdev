Date: 2026-03-24
Status: final
Document Type: survey report (T5 lane — Constraint Compiler Residuals)
Canonical Path: `docs/2026-03-24/opus-residual/t5-constraint-compiler-residuals.md`
Source Survey Order: `docs/2026-03-24/stage2-stage3-residual-leakage-resurvey-10terminal-master-order.md`
Evidence Artifacts:
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `projects/00_001/logs/artifacts/stage2/arc_001/attempt_01/final_arc__balanced.json`
- `projects/00_001/logs/artifacts/stage3/ep_0001/attempt_09/final_blueprint__emotion_focused.json`
- `projects/00_001/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__dialogue_focused.json`
- `projects/00_001/logs/artifacts/stage3/ep_0004/attempt_02/final_blueprint__emotion_focused.json`
- `projects/00_001/logs/episode_production.jsonl`
- `docs/2026-03-24/console.txt`
- `docs/2026-03-24/stage2-stage3-episode-boundary-expanded-survey-report.md`
- `docs/2026-03-24/stage2-stage3-episode-boundary-wave1-execution-ssot.md`
- `docs/2026-03-24/stage2-stage3-episode-boundary-wave2-survey-report.md`
Commit State:
- Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Baseline Dirty Summary: `dirty workspace; Wave 1 closed, Wave 2 survey finalized, fresh live-run evidence updated`

---

# T5. Constraint Compiler Residuals — Re-Survey Report

## 1. Executive Summary

After Wave 1 closed, `BlueprintConstraintCompiler` has two correctly applied fixes (`_within_ep()` on state_changes, stop_line expansion to all future episodes) and two residual seams:

1. **`_extract_immutable_fact_carryover()` bypasses the Wave 1 `_within_ep()` filter** — reads arc-wide state_changes without episode filtering. Active for `arc_position > 1` only; inactive for ep1.
2. **`semantic_carryover` continuity checkpoints describe arc-end state** — "20억 자본금 확보 완료", "법인 설립 완료" enter ep1's prompt as arc-wide continuity facts. By design (Wave 1 deferred), but contributes to ep1's blueprint absorbing later-episode scope.

Neither residual alone explains ep1 overconsumption. The dominant remaining vector for ep1 is outside the compiler — likely in Stage 3 prompt injection or blueprint synthesis (T6/T7 lanes).

The IFC residual IS a confirmed leak for ep2+ and should be fixed alongside any next wave.

---

## 2. Included Coverage / Exclusions

### Included

| # | Surface | File:Line | Inspected |
|---|---------|-----------|-----------|
| 1 | `compile()` orchestration | `bcc:43-117` | Yes |
| 2 | `_extract_episode_focus()` | `bcc:230-268` | Yes |
| 3 | `_extract_stop_line()` | `bcc:312-373` | Yes |
| 4 | `_extract_continuity()` | `bcc:375-443` | Yes |
| 5 | `_extract_inherited_state()` | `bcc:445-503` | Yes |
| 6 | `_extract_immutable_fact_carryover()` | `bcc:505-550` | Yes |
| 7 | `_summarize_state_changes()` | `bcc:552-651` | Yes |
| 8 | `_normalize_semantic_carryover()` | `bcc:653-699` | Yes |
| 9 | `_format_semantic_carryover_lines()` | `bcc:701-729` | Yes |
| 10 | `compile_to_prompt()` | `bcc:119-228` | Yes |

File abbreviation: `bcc` = `modules/domain/agents/blueprint_constraint_compiler.py`

### Excluded

- Stage 3 orchestrator prompt injection (T6 lane)
- Blueprint ensemble / runtime synthesis (T7 lane)
- Stage 4 contradiction detection (T8 lane)
- Stage 2 validation / guardrails (T3 lane)
- Treatment block scoping (T6 lane)

---

## 3. Key Evidence

### E1. Wave 1 `_within_ep()` filter on `_summarize_state_changes()` — CLEAN

`bcc:564-575`: The filter correctly excludes entries where `int(episode) > ep_num`.

For 00_001 ep1:
- `major_items`: both entries have `episode: 4` → excluded (int(4) > 1)
- `npc_introductions`: not processed by this method
- `relationship_changes` with `episode: 2` → excluded (int(2) > 1)
- `relationship_changes` with `episode: null` → **included** (null passes filter)

The null-episode relationship entries contain arc-global summaries ("한정호: 기대 제로 → 의외라는 시선"). These describe arc-end relationships, not ep1 state. However, the content is mild ("무관심 유지") and unlikely to drive overconsumption in isolation.

**Verdict: CLEAN with minor null-episode pass-through.**

### E2. Wave 1 stop_line expansion — CLEAN

`bcc:353-366`: The `future_eps` list collects all `ep_details` entries beyond `next_ep`.

For 00_001 ep1: stop_line would include ep2 content (next_ep) plus ep3, ep4 content as `future_eps`. The blanket prohibition at `bcc:170-174` covers all future episodes.

`compile_to_prompt()` at `bcc:156-174` correctly renders all future episodes and adds the blanket REJECT warning.

**Verdict: CLEAN.**

### E3. `_extract_immutable_fact_carryover()` — CONFIRMED RESIDUAL LEAKAGE (ep2+ only)

`bcc:505-550`: This method reads `state_changes` **without** the `_within_ep()` filter. Activated only when `arc_position > 1`.

For 00_001 ep2 (`arc_position=2`), the IFC section would produce:

```
- 관계 확정: 한정호 → 의외라는 시선
- 관계 확정: 한정호 (아버지) → 의외라는 시선, 약간의 관심...
- 관계 확정: 한태준 (큰형) → 무관심 유지...
- 관계 확정: 한태민 (둘째형) → 무관심 유지...
- 아이템 확정: SW인베스트먼트 법인 인감도장 (획득)
- 아이템 확정: 20억 예치 법인 계좌 OTP (획득)
```

The last two items are `episode: 4` acquisitions presented as "확정" (committed) facts in the ep2 prompt. This directly contradicts Wave 1's intent: the `_summarize_state_changes()` filter excludes these, but the IFC path re-introduces them through an unpatched seam.

The prompt label at `bcc:218-222` says "이전 Arc에서 확정된 불변 조건" — but the code reads from the **current** arc's state_changes, not from a prior arc. The label is misleading.

For ep1 (`arc_position=1`), IFC returns `""` at `bcc:512-513` — this seam is **inactive for ep1**.

**Verdict: confirmed residual leakage for ep2+. Inactive for ep1. Wave 1 bypass.**

### E4. `semantic_carryover` continuity checkpoints — SECONDARY AMPLIFIER

`bcc:653-699` normalizes, `bcc:701-729` formats, `bcc:132-136` injects into the prompt header.

For 00_001, the arc's `semantic_carryover.continuity_checkpoints` are:
- "20억 자본금 확보 완료"
- "가족의 감시망에서 완전히 벗어남"
- "여의도 임시 사무실 계약 및 법인 설립 완료"

These are arc-end state items that enter the prompt as:
```
### ARC semantic carryover
...
- continuity: 20억 자본금 확보 완료; 가족의 감시망에서 완전히 벗어남; 여의도 임시 사무실 계약 및 법인 설립 완료
```

This section appears **before** the constraint block in the compiled prompt (bcc:132-136 comes before MUST_FOCUS at bcc:145). The LLM receives arc-end continuity checkpoints as the first structured context, with no episode-level qualification.

The `growth_justification` adds: "미래 18년 치의 거시경제 지식 각성 및 초기 투자 자본 20억 원 확보" — reinforcing "20억 확보" as a growth target.

The foreshadow anchors mention "저녁 뉴스에서 '유가 상승세, 이란 핵 문제 재점화'" and "한시우의 '그룹 돈은 한 푼도 안 받겠다'는 선언" — these describe events from later episodes presented as arc-wide foreshadowing anchors.

This was explicitly deferred from Wave 1 scope (Wave 1 SSOT residual risk: "semantic_carryover foreshadow anchors can still describe arc-end state abstractly"). However, the fresh evidence shows ep1 still overconsumes, and this section is the loudest remaining positive-signal vector within the compiler.

**Verdict: secondary amplifier. Not the sole cause of ep1 overconsumption, but contributes arc-end-state signals that the LLM incorporates into early-episode blueprints.**

### E5. `_extract_inherited_state()` joint_docs fallback — LATENT VULNERABILITY (masked)

`bcc:452-459`: `joint_docs.physical_inventory` contains arc-end items ("SW인베스트먼트 법인 인감도장, 20억 예치 법인 계좌 OTP...").

`bcc:478-487`: `state_constraints.arc_start_state.equipment` overwrites with correct arc-start items ("개인 명의 예금통장, 신탁 펀드 증서, 승마 스폰서십 계약서").

For 00_001, the overwrite masks the joint_docs leakage. But if `state_constraints` or `arc_start_state` were missing/empty, the arc-end equipment would leak into inherited_state.

**Verdict: latent vulnerability. Not active in 00_001. Defense depends on upstream data completeness.**

### E6. `_extract_episode_focus()` — CLEAN

`bcc:230-268`: Uses `extract_episode_tactical()` which filters by `ep_num`. Falls back to `beat_sequence[arc_position-1]` which is correctly episode-indexed.

**Verdict: CLEAN.**

### E7. Fresh-run ep1 blueprint still overconsumes

`projects/00_001/logs/artifacts/stage3/ep_0001/attempt_09/final_blueprint__emotion_focused.json`:
- `ending_state.protagonist_status`: "자본금 20억 확보 및 법인 설립을 완료하고 첫 투자를 목전에 둔 상태"
- `integrated_scenario` includes: "SW인베스트먼트 법인 인감도장과 20억 예치 법인 계좌 OTP가 쥐어졌다", "여의도에 임시 사무실을 얻고 절차를 밟았다", "3배 레버리지 진입 타이밍을 계산"

This is ep3/ep4 content in ep1's blueprint. Since the compiler's `state_changes_summary` and `stop_line` are clean for ep1, and `IFC` is inactive for ep1, the remaining compiler contributions to this overconsumption are:
1. `semantic_carryover` (secondary amplifier)
2. Whatever other injection surfaces exist outside the compiler (T6/T7 scope)

---

## 4. Findings Ranked

| Rank | Finding | Classification | Severity | File:Line |
|------|---------|---------------|----------|-----------|
| F1 | IFC reads arc-wide state_changes without `_within_ep()` filter | **confirmed residual leakage** | P0 (ep2+) / N/A (ep1) | `bcc:505-550` |
| F2 | `semantic_carryover` continuity checkpoints describe arc-end state | **secondary amplifier** | P1 | `bcc:653-699`, `bcc:701-729`, `bcc:132-136` |
| F3 | null-episode relationship_changes pass through `_within_ep()` | **noise / not the culprit** | P2 | `bcc:564-575` |
| F4 | joint_docs physical_inventory in inherited_state | **latent vulnerability** (masked) | P2 | `bcc:452-459` |

---

## 5. Cleared Non-Culprits

| Surface | Reason Cleared | File:Line |
|---------|---------------|-----------|
| `_summarize_state_changes()` ep filter | `_within_ep()` correctly excludes future episodes | `bcc:564-575` |
| `_extract_stop_line()` expansion | All future episodes covered by `future_eps` + blanket prohibition | `bcc:353-374` |
| `_extract_episode_focus()` | Episode-filtered via `extract_episode_tactical()` | `bcc:230-268` |
| `arc_constraint_summary` | Empty in 00_001; arc-global by design (prohibitions) | `bcc:91` |
| `_extract_continuity()` | Reads from `prev_blueprint` (episode-specific) and past-verified state | `bcc:375-443` |
| `compile_to_prompt()` headers | Correctly labeled: "현재 화까지 확정된 이벤트", "현재 화 이후 모든 사건 — 절대 침범 금지" | `bcc:156-214` |

---

## 6. Residual Culprit Candidate

**Within the Constraint Compiler:**

The compiler's Wave 1 fixes are clean. The dominant remaining compiler-side vector is a combination of:

1. **IFC bypass (P0 for ep2+)** — confirmed leak that re-introduces future-episode items into blueprint prompts for mid-arc episodes. This is the single most actionable finding from this lane.

2. **semantic_carryover (P1 secondary amplifier)** — arc-end continuity checkpoints provide positive-signal fuel for overconsumption. This is by design but interacts with whatever other leakage vectors remain in T6/T7.

**Within the compiler, neither residual alone explains ep1 overconsumption.** The ep1 blueprint still absorbs ep3/ep4 material despite clean state_changes, clean stop_line, and inactive IFC. The dominant remaining vector for ep1 is outside the compiler.

**Cross-lane assessment:** The ep1 overconsumption likely originates from:
- Treatment block injection still carrying arc-plan-level detail (T6 scope)
- Blueprint synthesis re-inflating full-arc narrative from whatever context remains (T7 scope)
- semantic_carryover from this lane acting as secondary reinforcement

---

## 7. Next-Scope Recommendation

### Bounded fix: IFC episode filter (high priority, ~10 lines)

Add the `_within_ep()` filter (or equivalent) to `_extract_immutable_fact_carryover()` so that only `entry.episode <= current_ep` entries enter the IFC section.

This would close the confirmed bypass where the Wave 1 state_changes filter is negated by the unpatched IFC path.

### Bounded fix: joint_docs fallback guard (low priority, ~5 lines)

Add a guard so that `joint_docs.physical_inventory` is only used when `state_constraints.arc_start_state` is missing. This makes the latent vulnerability explicit rather than relying on upstream data completeness.

### Design decision: semantic_carryover episode scoping (medium priority, requires discussion)

The `semantic_carryover` continuity checkpoints currently describe arc-end state without episode attribution. Options:
- (a) Add episode-level attribution to continuity_checkpoints so the compiler can filter them
- (b) Label the section explicitly as "arc-end state, not current-episode obligations"
- (c) Suppress continuity_checkpoints entirely for early-arc episodes
- (d) Leave as-is and rely on other boundary fixes to provide sufficient counter-signal

Option (b) is the most conservative; option (a) requires Stage 2 arc generator changes. This decision should wait for T6/T7 lane findings to assess whether other leakage vectors dominate.

---

## 8. Confidence And Limits

- **Confidence: 93%**
- **Basis:**
  - Code-level audit of all 10 compiler surfaces is complete and consistent
  - Wave 1 fixes are confirmed clean within their targeted seams
  - IFC bypass is proven by code path analysis (no `_within_ep()` call)
  - semantic_carryover assessment is based on both code and fresh artifact evidence
- **Limits:**
  - Did not trace the full LLM prompt as received (llm_io.jsonl is very large); relied on code-path analysis and artifact evidence
  - Cannot quantify the relative weight of semantic_carryover vs. other injection surfaces without an LLM prompt-level trace (T9 lane scope)
  - The 7% uncertainty comes from: the compiler's secondary amplifier role may be larger or smaller than assessed, depending on T6/T7 findings

### Mandatory Conclusions

- Can this seam alone explain ep1 overconsumption: **no**
- Can this seam explain ep3/ep4 continuity-firewall replay: **partially** (IFC bypass contributes for ep2+; semantic_carryover amplifies but does not cause)
- Can this seam be fixed in a bounded next wave: **yes** (IFC filter ~10 lines, joint_docs guard ~5 lines, semantic_carryover scoping ~15 lines if chosen)

---

## 9. 3-Pass Audit Record

- Pass 1
  - confirmed this document is a survey report, not an execution SSOT
  - confirmed scope is limited to the constraint compiler and does not invade T6/T7/T8 lanes
  - confirmed all 10 compiler surfaces are covered in section 2
  - confirmed output contract matches the master order's required sections

- Pass 2
  - confirmed evidence anchors use concrete file:line references
  - confirmed Wave 1 fix verification is based on code inspection, not stale assumptions
  - confirmed IFC bypass claim is provable from code path (no `_within_ep()` in `bcc:505-550`)
  - confirmed the null-episode pass-through claim is based on `_within_ep()` logic at `bcc:569-571`
  - confirmed ep1 blueprint overconsumption evidence matches fresh-run artifact at `attempt_09`

- Pass 3
  - confirmed the mandatory three-question answers are consistent with the findings
  - confirmed the recommendation is bounded and does not propose Wave 2 density work or broad refactor
  - confirmed the report does not claim closure of Wave 1 residuals or create an execution SSOT
  - confirmed cross-lane references (T6, T7, T9) are directional, not prescriptive
