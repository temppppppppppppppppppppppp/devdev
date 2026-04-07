# Lane 3: Stage4 Opening Authority / Preflight / Consumer Intake

Date: 2026-04-06
Status: survey complete
Lane: 3 of 5
Authority: `docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-full-survey-audit-order.md`
Mode: read-only survey, no code changes

## 1. Scope

Primary question: once Stage4 receives a blueprint, how hard does it bind opening continuity and state carryover before manuscript generation?

This lane inspects the Stage4 **consumer intake** surfaces — the code that transforms blueprint + chain_link + arc data into mandatory LLM context — for evidence of genre-blind hardening that could force false continuity failures in non-wuxia works.

## 2. Files Inspected

| File | Lines of Interest | Role |
|------|-------------------|------|
| `modules/core/stage4_context_builder.py` | L844-985, L1653-1704, L1906-2059 | Opening authority builder, chain_link loader, tier0 assembly |
| `modules/core/stage4_orchestrator.py` | L706-764, L794-1018, L1154-1163 | V75-D correction contract, blueprint preflight, episode loop inputs |
| `modules/core/continuity_pin_guard.py` | L133-207 | Deterministic continuity pin patching |
| `modules/core/constitutional_checker.py` | L505-558 | REJECT examples including recovery rule |
| `config/prompts/blueprint_generator.yaml` | L24-67 | Blueprint preflight prompt template |
| `tests/test_stage4_preflight_continuity.py` | full file | Preflight + continuity pin tests |
| `tests/test_stage4_context_builder.py` | L215-249, L2334-2391 | Chain link + opening authority tests |
| `tests/test_stage4_interview_round.py` | selected grep results | Interview round opening/carryover references |

## 3. Evidence

### E-1: `[Stage4 Opening Scene Authority]` — Genre-Blind Hard Canon Declaration

**Source**: `stage4_context_builder.py:898-916`

The `_build_work_identity_authority_packet()` method produces the `[Stage4 Opening Scene Authority]` block. This block is injected at tier-0 priority (insert at position 0 of mandatory context) for **every genre** without any genre gating.

Key hardening lines (verbatim):

```
"- opening scene continuity below is hard canon. Do not improvise a different movement path or camera reset."
"- alternate openings are allowed only with an explicit transition/cut and immediate state declaration."
"- if the opening changes location, dominant action, or time band, use an explicit transition sentence or `* * *` first."
"- without a transition signal, do not jump to a new room, vehicle, exterior route, or later time band."
```

**Impact on non-wuxia**: An investment protagonist who finishes a meeting in a conference room and starts the next episode in their office (natural and genre-ordinary) would trigger the same "do not jump to a new room" pressure as a wuxia character teleporting across provinces. The phrase "hard canon" gives the LLM no room to distinguish severity.

**Genre gate check**: The only genre-gated tier0 content in the same method is the `[무협 기술/경지 권위]` clause (line 2006: `_genre_name in ("무협", "wuxia")`). The Opening Scene Authority section has **zero genre branching**.

### E-2: Carryover Field Injection — Unconditional Obligation Language

**Source**: `stage4_context_builder.py:919-929`

When chain_link carryover fields exist, they are injected with obligation language:

| Carryover Field | Prompt Wording | Severity Implied |
|----------------|----------------|------------------|
| `cliffhanger` | "resolve or explicitly transition from" | Hard obligation |
| `location` | "honor or explicitly transition from" | Hard obligation |
| `time_marker` | "honor or explicitly advance from" | Hard obligation |
| `pending_actions` | "resolve before new thread or explicitly transition away" | Hard obligation |

There is **no soft/hard distinction** in these injections. Investment work actions like "계약서 검토 마무리하기" (finish reviewing a contract) receive identical treatment to "적 추격에서 벗어나기" (escape enemy pursuit). Both become things the LLM is told to "resolve before new thread."

### E-3: Chain Link Loading — `physical_state` Filter Is Minimal

**Source**: `stage4_context_builder.py:1666-1678`

```python
if _cl_data.get("physical_state") and _cl_data["physical_state"] != "정상":
    _cl_parts.append(f"- 신체 상태: {_cl_data['physical_state']}")
```

The chain_link section header is `"### [V68] 직전 화 연결고리 - 반드시 이어받을 것"` (prior episode chain link — **MUST** carry over).

The only filter is `!= "정상"` (not "normal"). This means:
- "피로" (fatigue) → included → "반드시 이어받을 것"
- "과로" (overwork) → included → "반드시 이어받을 것"
- "두통" (headache) → included → "반드시 이어받을 것"
- "스트레스" (stress) → included → "반드시 이어받을 것"

None of these are physical injuries requiring wuxia-grade recovery, but the "반드시" (MUST) header makes them effectively mandatory for the next episode's opening.

Note: `physical_state` is **not** propagated into the `carryover_*` fields that feed `[Stage4 Opening Scene Authority]`. It appears only in the `[V68]` chain link digest section. However, both are tier-0 mandatory context, and the "반드시" language still pressures the LLM.

### E-4: Continuity Pin Guard — Genre-Blind Pattern Matching

**Source**: `continuity_pin_guard.py:133-207`

`apply_continuity_pins()` operates entirely on Korean text pattern matching. It checks:
- Proper noun alignment (quoted tokens between source and blueprint)
- Elapsed time alignment (time bucket patterns)
- Opening action continuity (father call + nonstop exit + reversal pattern)

There is **no genre awareness** in this module. The `opening_action_continuity_pin` type currently fires on a very specific father-calling dramatic exit pattern, so its false positive risk for generic investment works is **low** today. However, the mechanism has no architectural guard preventing future patterns from applying genre-inappropriately.

### E-5: Blueprint Preflight — No Physical/Recovery State Check

**Source**: `stage4_orchestrator.py:794-1018`, `config/prompts/blueprint_generator.yaml:24-67`

The preflight checks: numeric consistency, NPC consistency, timeline, location, item/equipment integrity. It does **not** check:
- Whether `physical_state` claims in blueprint match genre norms
- Whether fatigue recovery is appropriate for the genre
- Whether opening state assumptions are too rigid for a business/investment work

The preflight prompt explicitly says: "이것은 학술 논문이나 역사서가 아닌 **상업 웹소설**입니다" and lists things NOT to flag (historical anachronisms, minor tech timing). But it does not have a comparable carveout for physical state or fatigue appropriateness.

The preflight's false_positive_patterns (lines 943-955) filter out "출처 불분명", "고증", "시대" etc. but do not filter out false fatigue/recovery rigidity claims.

### E-6: V75-D Correction Contract — Opening-Only, No Physical State Awareness

**Source**: `stage4_orchestrator.py:706-764`

The correction contract activates only when Director feedback contains opening/replay/numeric signals. It enforces location and time consistency during blueprint patching. It has **no fatigue/physical_state awareness** and does not add or remove recovery pressure.

This is not an overreach source but is also not a relief valve.

### E-7: Constitutional Checker — Wuxia-Centric Recovery Example

**Source**: `constitutional_checker.py:512-516`

```
❌ 사례 6: 부상 무시 (V55.5 NEW)
   직전 화 끝: "검에 깊이 베여 피를 쏟으며 쓰러졌다"
   → 이번 화 시작: "화창한 아침, 가볍게 검을 휘둘렀다"
   → REJECT: 중상 후 즉시 활동 (회복 과정 필수)
```

The example is framed as "중상 후 즉시 활동 (회복 과정 필수)" — recovery required after **severe** injury. The checker is invoked at constitutional level (cross-stage). While the rule itself is reasonable for true physical injury, a broad LLM interpretation could apply this to non-physical fatigue in investment works. There are no non-wuxia examples showing where this rule does NOT apply.

### E-8: Tests Codify Current Genre-Blind Behavior

**Source**: `tests/test_stage4_context_builder.py:2334-2391`

Test `test_build_mandatory_context_promotes_opening_scene_authority_even_without_work_focus` explicitly asserts:
- `"[Stage4 Opening Scene Authority]"` is present
- `"opening carryover pending_actions to resolve before new thread"` is present
- `"do not replay a completed prior-episode event"` is present
- `"alternate openings are allowed only with an explicit transition/cut"` is present

The test is intentionally designed to verify the current "hard canon" behavior for a chain_link with `pending_actions: ["전화를 받기", "현관으로 이동하기"]` — which is a non-wuxia domestic scenario. This means current tests would need updating if the behavior were normalized.

**Source**: `tests/test_stage4_context_builder.py:215-249`

Test `test_loads_chain_link_data` verifies `physical_state: "부상"` (injury) is included in chain link output. No test exists that verifies soft-fatigue states like "피로" or "과로" are treated differently.

## 4. Findings

### F-1 (P1): `[Stage4 Opening Scene Authority]` is the strongest single hardening surface

The phrase "hard canon" at line 910 is the most authoritative opening-binding language in the entire pipeline. It applies to ALL genres without branching. For non-wuxia investment works, this language is disproportionate: an investment protagonist's natural movement between rooms, buildings, or time-of-day shifts gets the same prohibition as a wuxia character's spatial teleportation.

**Confidence**: 98%. Directly readable from code, confirmed by test assertions.

### F-2 (P2): Carryover obligation language lacks soft/hard gradation

The four carryover fields (cliffhanger, location, time_marker, pending_actions) all use "resolve/honor/explicitly transition" language without severity markers. Investment-grade pending_actions like "계약서 검토 마무리" are treated with the same LLM pressure as wuxia-grade "적 추격 탈출."

**Confidence**: 97%. Language is explicit in code; impact is inferred from LLM behavior under hard obligation framing.

### F-3 (P2): `physical_state` in chain link section has only a `!= "정상"` guard

Any non-normal physical state (including mild fatigue, stress, ordinary exhaustion) is injected under a "반드시 이어받을 것" (MUST carry over) header. The filter does not distinguish injury severity, and there is no genre-aware softening. However, `physical_state` does NOT flow into the Opening Scene Authority's `carryover_*` fields — it sits in a separate V68 chain link digest. Its impact is indirect but real because the V68 section is also tier-0 mandatory context.

**Confidence**: 96%. Code path is clear; the indirect vs direct hardening distinction reduces certainty of operator-facing impact.

### F-4 (P3): Blueprint preflight has no physical/fatigue state awareness

The preflight does not validate whether physical_state or fatigue claims in the blueprint are genre-appropriate. This is not itself an overreach source, but it is a missing relief valve — a place where genre-appropriate softening could be applied before the blueprint enters the manuscript pipeline.

**Confidence**: 95%. The preflight prompt template and `_resolve_blueprint_preflight_result` code are clear.

### F-5 (P3): Constitutional checker recovery example is wuxia-centric but rule is genre-universal

The "중상 후 즉시 활동 (회복 과정 필수)" rule is illustrated only with wuxia examples but is declared as a universal rejection criterion. For investment/business works, an LLM could over-apply this to mental fatigue or stress states.

**Confidence**: 90%. The checker's examples are one-sided, but how much the LLM over-generalizes depends on model behavior, which is not directly testable from source alone.

### F-6 (P3): Continuity pin guard is genre-blind but currently low false-positive risk for non-wuxia

The `opening_action_continuity_pin` fires on a very specific dramatic exit pattern (father calling + nonstop exit + reversal). Its current false-positive risk for investment works is low, but the architecture does not prevent future patterns from applying genre-inappropriately.

**Confidence**: 97%.

## 5. Open Questions

1. **Is `physical_state` actually populated with mild fatigue strings in real investment work chain_links?** Lane 4 (post-pass persistence) should confirm what the LLM actually writes into `physical_state` for non-wuxia works.

2. **Does the V68 "반드시" header actually cause LLM manuscript rejections for mild fatigue non-carryover?** Lane 5 (runtime evidence) should confirm whether operator-facing symptoms include this pathway.

3. **How much of the false hardening is attributable to the "hard canon" string vs the structural obligation language?** A prompt-only normalization that softens "hard canon" to "opening continuity baseline (soft for non-injury states)" might resolve a significant portion of the issue without code changes.

4. **Would a severity-tagged carryover field set (e.g., `carryover_severity: soft | hard`) be sufficient, or does the fix require genre branching at the Opening Scene Authority level?**

## 6. Provisional Severity

| Finding | Severity | Justification |
|---------|----------|---------------|
| F-1 | P1 | "hard canon" applied genre-blind is a real false hard-fail pressure source |
| F-2 | P2 | Obligation language without gradation produces meaningful overreach |
| F-3 | P2 | `physical_state` under "반드시" header can persist mild fatigue as mandatory |
| F-4 | P3 | Missing relief valve, not an active overreach source |
| F-5 | P3 | Indirect risk via LLM over-generalization of recovery examples |
| F-6 | P3 | Low current risk but unguarded architecture |

**Overall Lane 3 Severity: P1** — Stage4 is currently the strongest hardening layer for opening continuity, and this hardening is genre-blind.

## 7. Recommended Merge Notes

For the merged survey:

1. **Stage4 is the primary hardening layer.** The `[Stage4 Opening Scene Authority]` block is where "soft carryover" becomes "hard canon." This is a Stage4 context_builder surface, not Stage2 or Stage3.

2. **The overreach is primarily prompt wording + structural obligation language**, not deterministic code patching. The continuity pin guard's actual code mutations are narrow and well-targeted. The problem is the surrounding framing language injected into LLM mandatory context.

3. **Smallest future patch surface for Stage4**:
   - (a) Genre-branch the "hard canon" string: replace with severity-aware language that distinguishes physical injury/spatial discontinuity (hard) from ordinary state transitions (soft advisory).
   - (b) Add a soft/hard flag to carryover fields: `_extract_chain_link_carryover_fields` could tag each field with severity based on the nature of the state.
   - (c) Soften `physical_state` injection in `load_chain_link_section`: add a severity filter that downgrades "피로/과로/두통/스트레스" from "반드시" to "참고" (reference).
   - (d) None of these require Stage2 or Stage3 changes — Stage4 context_builder is the primary owner.

4. **Natural healing is currently implicitly preserved** — no Stage4 code explicitly blocks natural healing. But the "반드시 이어받을 것" + "hard canon" framing makes the LLM reluctant to allow natural time-skip healing without explicit on-page recovery beats, even when genre conventions would permit it.

5. **Test impact**: `test_build_mandatory_context_promotes_opening_scene_authority_even_without_work_focus` would need updating if the "hard canon" language is softened. The test currently asserts exact obligation strings.

---

3-Pass Audit Record:

Pass 1:
- All 7 files from the lane scope were inspected
- Findings map to the primary question
- Evidence citations include file:line references

Pass 2:
- No overclaims beyond inspected code
- Confidence levels are explicitly stated per finding
- Open questions are separated from confirmed findings

Pass 3:
- Findings format matches required structure (Scope, Files Inspected, Evidence, Findings, Open Questions, Provisional Severity, Recommended Merge Notes)
- Severity uses the bounded P0-P3 scale
- No implementation recommendations — survey only

Estimated confidence: 96%
