# Lane 4: Stage4 Chain-Link / Post-Pass Persistence / Next-Episode State Pressure

Date: 2026-04-06
Lane Owner: Terminal 4
Status: survey complete
Mode: read-only survey, no code changes
Audit Order: `docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-full-survey-audit-order.md`

## 1. Scope

Primary question: after a Stage4 PASS, does manuscript-derived `chain_link` turn soft fatigue into a sticky next-episode obligation?

This lane inspects the full lifecycle of chain_link data: extraction → persistence → load → consumption, with specific focus on whether `physical_state` and `pending_actions` create false hard-fail pressure for non-wuxia genres.

## 2. Files Inspected

| File | Relevance |
| --- | --- |
| `modules/core/stage4_orchestrator.py` L1027-1077 | `_extract_chain_link()` — LLM extraction prompt |
| `modules/core/stage4_post_processor.py` L872-879 | DB save flow (`chain_link_{ep}` anchor) |
| `modules/core/stage4_context_builder.py` L1653-1704 | `load_chain_link_section()` — DB load + prompt formatting |
| `modules/core/stage4_context_builder.py` L844-929 | `_build_work_identity_authority_packet()` — Opening Scene Authority injection |
| `modules/core/stage4_context_builder.py` L1074-1087 | `_extract_chain_link_carryover_fields()` — carryover field parser |
| `modules/core/stage4_context_builder.py` L1906-2059 | `_build_tier0_mandatory_sections()` — tier-0 mandatory context assembly |
| `modules/core/stage4_immutable_fact_contract.py` L64-113, L172-190, L548-575 | ImmutableFactPacket — carryover fields → "즉시 불합격" binding |
| `modules/domain/agents/chief_writer_prompts.py` L78-136 | Writer prompt template — chain_link_section at authority level 2 |
| `modules/core/stage4_interview_round.py` L3145-3218 | `chain_link_section` passthrough to writer kwargs |
| `modules/core/stage4_types.py` L45 | `_RoundContext.chain_link_section` field |
| `modules/core/state_delta_tracker.py` L23-92 | `InjuryLevel` enum + wuxia-only recovery times |
| `modules/core/writer_prompt_builders.py` L145-169 | Injury anomaly detection (급회복 guard) |
| `tests/test_stage4_context_builder.py` L215-248, L2334-2391 | Chain link load + Opening Scene Authority test codification |
| `tests/test_stage4_post_processor.py` L329-342, L488-503 | Chain link save test codification |
| `tests/test_stage4_context.py` L346-372 | Orchestrator chain_link helper tests |

## 3. Evidence

### E-1. Extraction Is Genre-Blind

`stage4_orchestrator.py` L1048-1061:

```python
prompt = f"""아래 원고의 마지막 상황을 분석하여 다음 화에서 반드시 이어받아야 할 요소를 추출하세요.
...
{{
    "cliffhanger": "현재 진행 중인 상황/위기/긴장 (없으면 빈 문자열)",
    "pending_actions": ["다음 화에서 해야 할 행동 목록 (최대 5개)"],
    "emotional_state": "주인공의 현재 감정 상태 (한 줄)",
    "physical_state": "부상/피로/상태 (정상이면 '정상')",
    "location": "현재 위치 (구체적으로)",
    "time_marker": "작중 시간대 (알 수 있으면, 모르면 빈 문자열)"
}}"""
```

The prompt has no genre parameter. The `physical_state` field description lumps injury and fatigue: "부상/피로/상태". For an investment work, the LLM will extract "야근으로 인한 가벼운 피로" (mild fatigue from overtime), "스트레스" (stress), "두통" (headache), etc. as non-"정상" physical_state values. These are genre-ordinary conditions, not narratively significant physical injuries.

Default fallback at L1070: `chain_link.setdefault("physical_state", "정상")` — only "정상" is treated as "no state."

### E-2. Persistence Has No Genre Filter

`stage4_post_processor.py` L872-879:

```python
chain_link = {}
if extract_chain_link_fn:
    chain_link = extract_chain_link_fn(next_ep, final_manuscript, blueprint)
if chain_link:
    self.ctx.current_project.db.save_anchor(f"chain_link_{next_ep}", chain_link)
```

No genre check, no severity classification, no soft/hard distinction before save. Every chain_link dict with any content is persisted unconditionally.

### E-3. Load Creates "반드시 이어받을 것" Header

`stage4_context_builder.py` L1666-1700:

```python
_cl_parts = ["### [V68] 직전 화 연결고리 - 반드시 이어받을 것"]
# ...
if _cl_data.get("physical_state") and _cl_data["physical_state"] != "정상":
    _cl_parts.append(f"- 신체 상태: {_cl_data['physical_state']}")
```

The only filter is `!= "정상"`. Anything else — including "약간 피곤함" — gets the "반드시 이어받을 것" (MUST carry over) label. The physical_state field itself stays descriptive (not promoted to `carryover_` contract). But the section header "반드시 이어받을 것" is authoritative language that LLMs interpret as mandatory.

`pending_actions` and `location` ARE promoted to the carryover contract section (L1683-1698):

```python
_carryover_parts.append(f"- carryover_pending_actions: {actions}")
_carryover_parts.append(f"- carryover_location: {_cl_data['location']}")
```

### E-4. Triple Consumption — Three Hardening Paths

Chain_link data enters the LLM through three independent hardening paths:

**Path A — Writer Prompt Direct Injection (Authority Level 2)**

`chief_writer_prompts.py` L117-128:

```
### [STEP 0.5: 권위 우선순위]
1. Opening Anchor
2. Immutable Facts / world-state / mandatory truth / chain_link / ...
3. Structured scene breakdown
4. Advisory integrated scenario prose
5. Feedback / constraints / HUD-heavy cues / style guidance
```

The entire `chain_link_section` text (including "반드시 이어받을 것" header) is injected at L136 at authority level 2 — same tier as immutable facts and world state.

**Path B — Opening Scene Authority (Hard Canon)**

`stage4_context_builder.py` L910-929:

```python
"- opening scene continuity below is hard canon. Do not improvise a different movement path or camera reset.",
# ...
if carryover_pending_actions:
    lines.append(
        "- opening carryover pending_actions to resolve before new thread or explicitly transition away: "
        f"{carryover_pending_actions}"
    )
```

Carryover fields from chain_link are extracted and injected into `[Stage4 Opening Scene Authority]` with "hard canon" language. `pending_actions` must be "resolved." `location` must be "honored."

**Path C — Immutable Fact Contract (즉시 불합격)**

`stage4_immutable_fact_contract.py` L172-190, L561-575:

```python
def _extract_chain_link_carryover(packet: ImmutableFactPacket, chain_link_section: str) -> None:
    # extracts carryover_cliffhanger, carryover_pending_actions,
    # carryover_location, carryover_time_marker into the packet
```

```python
lines.append(
    "- carryover pending_actions to resolve before new thread or explicitly transition away: "
    f"{packet.carryover_pending_actions}"
)
lines.append(
    "⛔ 위 anchor를 무전환으로 덮어쓰거나, 직전 화에서 이미 끝난 행동을 opening에서 다시 재연하면 즉시 불합격."
)
```

Chain_link carryover fields become part of the ImmutableFactPacket, which ends with "⛔ 즉시 불합격" (immediate fail). This is the strongest hardening layer — not advisory, not warning, but "즉시 불합격."

### E-5. physical_state Is Descriptive But Effectively Normative

`physical_state` is NOT promoted to the `carryover_` contract (unlike pending_actions, location, cliffhanger, time_marker). So it does NOT enter Paths B or C. However:

1. It is injected as "- 신체 상태: ..." under the "반드시 이어받을 것" header
2. The header + authority level 2 placement makes it effectively mandatory for LLMs
3. No natural healing concept exists in the chain_link pipeline

Contrast with `state_delta_tracker.py` L88-92, which does define recovery durations:

```python
INJURY_RECOVERY_TIME = {
    "경상": 1,  # 1 에피소드
    "중상": 3,  # 3 에피소드
    "위독": 5,  # 5 에피소드
}
```

But this is in the HUD/state tracking system, not in the chain_link pipeline. The chain_link extraction and consumption never reference `StateDeltaTracker` or `InjuryLevel`. The two systems are disconnected.

### E-6. No Soft/Hard Distinction in Chain-Link Schema

The chain_link dict has exactly 6 fields: `cliffhanger`, `pending_actions`, `emotional_state`, `physical_state`, `location`, `time_marker`. There is no `severity`, `binding`, `genre_relevance`, or `decay_after` field. Every field is flat and treated identically regardless of genre.

### E-7. Director Does Not Validate Chain-Link Directly

`director.py` and `director_continuity.py` have zero references to `chain_link` or `physical_state`. The Director does not receive chain_link data as a separate validation input. However, the Director validates manuscripts that were shaped by chain_link pressure through the writer prompt. If the writer ignores chain_link authority (e.g., doesn't mention the character's fatigue), the manuscript may be REJECTed for continuity drift — not because the Director saw chain_link, but because the Immutable Fact Contract check surfaces the violation.

### E-8. Tests Intentionally Codify the Current Behavior

`tests/test_stage4_context_builder.py` L2342-2386: The test `test_build_mandatory_context_promotes_opening_scene_authority_even_without_work_focus` explicitly asserts that chain_link carryover fields appear in Opening Scene Authority text:

```python
ctx.current_project.db.load_anchor.return_value = {
    "cliffhanger": "전화가 오기 직전 멈칫했다.",
    "pending_actions": ["전화를 받기", "현관으로 이동하기"],
    "location": "서재 앞 복도",
    "time_marker": "직후",
}
# ...
assert "opening carryover pending_actions to resolve before new thread or explicitly transition away: ..." in text
```

The test uses `s4_genre_type="investment"` — this is an investment genre test that still asserts hard canon carryover behavior. The test codifies the overreach.

## 4. Findings

### F-1. Chain-Link Post-Pass Persistence Is a Real Overreach Surface [CONFIRMED, >95%]

The chain_link pipeline converts any LLM-extracted state — including genre-ordinary conditions like fatigue, stress, headache — into a sticky next-episode obligation through three independent hardening paths. The hardest path (ImmutableFactPacket) uses "즉시 불합격" language.

### F-2. physical_state Is Descriptive But Effectively Normative [CONFIRMED, >95%]

While `physical_state` is NOT promoted to the carryover contract or ImmutableFactPacket, it is injected under the "반드시 이어받을 것" header at authority level 2. For non-wuxia works, this means "약간 피곤한 상태" becomes a de facto mandatory next-episode constraint.

Confidence note: physical_state is the WEAKEST of the four hardening paths, but not zero-pressure.

### F-3. pending_actions Is the Strongest Overreach Channel [CONFIRMED, >95%]

`pending_actions` is promoted through ALL THREE hardening paths:
1. Writer prompt at authority level 2
2. Opening Scene Authority as "hard canon" with "resolve before new thread"
3. ImmutableFactPacket with "⛔ 즉시 불합격"

For investment works, mundane actions like "회의 참석하기" (attend meeting) receive identical treatment to wuxia-critical actions like "독침 해독 치료 받기" (receive antidote treatment).

### F-4. Chain-Link Schema Lacks Soft/Hard Distinction [CONFIRMED, >95%]

The 6-field flat schema has no severity, binding, or genre-relevance classification. This is a schema-level limitation that cannot be addressed by prompt-only changes.

### F-5. Extraction Prompt Is Genre-Blind [CONFIRMED, >95%]

The extraction prompt at `stage4_orchestrator.py` L1048-1061 has no genre parameter and no guidance to distinguish narratively significant state (injury, poisoning, critical plot hook) from genre-ordinary state (fatigue, routine tasks, mild stress).

### F-6. State Delta Tracker and Chain-Link Are Disconnected Systems [CONFIRMED, 90%]

`state_delta_tracker.py` has a structured injury/recovery model (`InjuryLevel`, `INJURY_RECOVERY_TIME`) but chain_link extraction never references it. The two systems independently track physical state with different schemas, different authorities, and different consumption paths.

Confidence note: 90% because there may be an indirect connection through HUD data flow that I did not trace in this lane. However, no direct code path between chain_link and state_delta_tracker was found.

### F-7. The Overreach Is Not Opening-Motion Only [CONFIRMED, >95%]

While the Opening Scene Authority section focuses on location and motion continuity, the chain_link pipeline also carries `physical_state`, `emotional_state`, and `pending_actions` — these extend the overreach beyond opening-motion into broader physical-state and action-obligation pressure.

## 5. Open Questions

1. **Q-1**: Does the LLM typically extract non-wuxia soft conditions as non-"정상" physical_state? Evidence from live runs (Lane 5) would confirm frequency.

2. **Q-2**: Is the ImmutableFactPacket violation check actually enforced in the interview round, or is it advisory-only? The docstring says "Director remains final judge," but the "즉시 불합격" language is strong. Lane 3 may have more clarity on how the immutable fact contract affects actual PASS/REJECT decisions.

3. **Q-3**: Should `emotional_state` be considered part of the overreach? It is extracted and persisted (E-1) but NOT included in the descriptive chain_link section or carryover contract. It appears to be extracted but silently dropped.

4. **Q-4**: How does `stage4_orchestrator._build_next_round_correction_contract` (L720-763) interact with chain_link? It uses `chain_link_excerpt` in correction feedback, potentially reinforcing the overreach during retry loops.

## 6. Provisional Severity

**P1**: Real operator-facing false hard-fail or hard contract mismatch.

Justification: For non-wuxia works, the chain_link pipeline creates a measurable false hardening path. Mundane `pending_actions` and soft `physical_state` are promoted to "hard canon" and "즉시 불합격" level. This can produce real false REJECTs or force writers to waste opening space resolving genre-ordinary obligations. The triple-path hardening (writer prompt + Opening Scene Authority + ImmutableFactPacket) means the overreach is not merely cosmetic — it has structural teeth.

## 7. Recommended Merge Notes

### For the Final Merged Survey

1. **Post-pass persistence is a confirmed overreach layer**, not merely a passive recorder. Chain_link actively hardened through three independent consumption paths.

2. **The strongest overreach channel is `pending_actions`**, not `physical_state`. While physical_state gets the attention (because it maps to the operator's fatigue complaint), pending_actions has the hardest binding — promoted to all three paths including ImmutableFactPacket.

3. **This is NOT a prompt-only fix**. The flat 6-field chain_link schema needs a `binding` or `severity` field to distinguish hard carryover (plot-critical cliffhanger, physical injury) from soft carryover (routine tasks, mild fatigue). Without schema change, prompt-level softening would fight against the ImmutableFactPacket's "즉시 불합격" language.

4. **Smallest future patch surface**:
   - Add `binding: "hard"|"soft"` to chain_link extraction schema
   - Genre-aware extraction prompt: different physical_state guidance for wuxia vs non-wuxia
   - `load_chain_link_section()`: filter soft-binding fields out of carryover contract
   - `_extract_chain_link_carryover()` in ImmutableFactPacket: skip soft-binding fields
   - This would require changes in 3 files: `stage4_orchestrator.py` (extraction), `stage4_context_builder.py` (load + authority packet), `stage4_immutable_fact_contract.py` (ImmutableFactPacket builder)

5. **Preserve natural healing**: The current pipeline has no concept of natural healing for chain_link fields. Adding `decay_after: N` (episodes until natural reset) would align with the existing `INJURY_RECOVERY_TIME` pattern in `state_delta_tracker.py` but applied to the chain_link system.

6. **Test migration**: `test_stage4_context_builder.py` L2342-2386 explicitly codifies the overreach for `s4_genre_type="investment"`. Future fix must update this test.

---

3-Pass Audit Record:

Pass 1:
- Scope matches Lane 4 assignment from audit order
- All minimum-inspect files covered
- Focus areas (chain_link extraction, physical_state, pending_actions, DB flow, next-episode re-entry) all addressed

Pass 2:
- File paths verified against live codebase
- Line numbers verified against current file content
- Evidence quotes are verbatim from source

Pass 3:
- Findings are bounded to inspected evidence
- Severity is justified by specific code paths
- Open questions are explicitly flagged where confidence < 95%
- Merge notes are actionable without overclaiming

Estimated confidence: 96%
