# Stage4 CW Webnovel Identity Context Hierarchy — Lane 3: Stage2/Stage3 Upstream Draft

Date: 2026-03-31
Status: draft-bounded-partial-evidence
Lane: 3 — Stage 2 / Stage 3 upstream scene-authority and blueprint leak
Terminal: Opus
Master Order: `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-parallel-master-order.md`

## 1. Coverage

| Surface | Read | Relevant Lines |
|---------|------|---------------|
| `projects/0_2/plans/arcs/arc_001.txt` | full | EP1-4 tactical doc, beat sequence |
| `projects/0_2/plans/arcs/arc_002.txt` | full | EP5-9 tactical doc (cross-reference) |
| `projects/0_2/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json` | full | Arc 2 structured output |
| `projects/0_2/logs/artifacts/stage4/ep_0002/attempt_01/patched_blueprint_after_fix__V75-D_blueprint_inplace.json` | full | EP2 active blueprint |
| `projects/0_2/logs/artifacts/stage4/ep_0002/attempt_01/rejected_best__C_balanced.txt` | first 100 lines | attempt_01 rejected manuscript |
| `projects/0_2/logs/artifacts/stage4/ep_0002/attempt_02/rejected_best__A_balanced.txt` | first 60 lines | attempt_02 rejected manuscript (bad sentence found) |
| `projects/0_2/logs/artifacts/stage4/ep_0002/attempt_03/final_manuscript__B.txt` | first 100 lines | attempt_03 accepted manuscript |
| `modules/core/stage2_context.py` | full | Stage2Context DI |
| `modules/core/stage3_context.py` | full | Stage3Context DI |
| `modules/core/stage4_context_builder.py` | L1-150, L460-559 | Blueprint entity extraction |
| `modules/core/stage4_interview_round.py` | L890-943 | `_minimize_writer_blueprint` |
| `modules/domain/agents/chief_writer_context.py` | L274-324 | `_extract_blueprint_sections` |
| `modules/domain/agents/chief_writer_prompts.py` | L79-156 | prompt template placement |
| `modules/domain/agents/blueprint_ensemble.py` | L10-14, L439-455, L680-748, L1123-1139 | blueprint generation + prev blueprint feed |
| `config/prompts/ensemble.yaml` | L264-414 | BLUEPRINT_GENERATION_PROMPT template |
| `0_temp.txt` | L1-200, L680-800 | Runtime console evidence |

## 2. Findings

### F-1: Stage 2 Tactical Doc is ADEQUATE for EP2

Arc 1 tactical doc EP2 (`arc_001.txt:16-18`) provides concrete scene-level narrative prose:

> "다음 날 아침, 아버지 한정호 회장이 막내를 서재로 부른다. 묵직한 마호가니 문을 열고 들어가자, 매캐한 시가 냄새와 함께 아버지, 그리고 이미 그룹 핵심 계열사를 꿰차고 후계 경쟁에 돌입한 두 형 한태준과 한태민이 앉아 있다."

Evidence:
- Named characters: 한시우, 한정호, 한태준, 한태민
- Concrete sensory detail: "묵직한 마호가니 문", "매캐한 시가 냄새"
- Clear scene goal: 사업 선언 + 방관 환경 확보
- Scene-driving dialogue: "사업 하겠습니다. 투자사 차릴 겁니다."
- No meta-structural language (no "직전 화에서" or similar references)
- No game/system language (no HUD, 상태창, 무공)

**Stage 2 prose quality is scene-writing quality, not briefing quality.**

### F-2: Stage 2 Capital Facts are Under-Specified for EP2

The tactical doc chain:
- EP1: No capital amount mentioned
- EP2: "자본금은 제 돈으로 합니다. 그룹 돈 한 푼 안 받겠습니다." — declares self-funding but states NO AMOUNT
- EP3: "정확히 20억 원이라는 숫자가 찍힌다" — capital first specified in EP3
- EP4: "20억 원이 예치된 증권 계좌" — confirmed in EP4

This creates a gap: EP2's scene requires the protagonist to declare self-funding, but the tactical doc doesn't specify how much. Stage 3's blueprint then invents a decomposition:

Blueprint EP2 `integrated_scenario`:
> "현재 주식 계좌 잔고와 즉시 해지 가능한 예금을 합치면 정확히 15억 원입니다. 부동산 5억을 포함하면 총자산은 20억이고요."

This 15+5=20 decomposition does not exist in the tactical doc. It's a Stage 3 invention that then propagates inconsistently:
- Attempt 01 (rejected C): "20억 4천만 원" — yet another figure
- Attempt 02 (rejected A): "총자산은 20억...15억 가용 자금, 5억 부동산"
- Attempt 03 (accepted B): "금융 자산 8억은 당장 현금화...성북동 상가 12억" — 8+12=20

Each attempt invents a different decomposition because the upstream (Stage 2) doesn't anchor one. The blueprint's 15+5 decomposition fails to become canonical because the CW doesn't treat `integrated_scenario` as hard authority (correctly, since Stage 4 de-prioritizes it).

**Severity: MINOR-to-MODERATE.** The amount ambiguity doesn't directly cause the "meta-briefing" symptom but contributes to numeric truth conflicts detected by FlashbackVerifier and A-3.

### F-3: Stage 3 `integrated_scenario` Contains BRIEFING PROSE and GENRE CONTAMINATION (PRIMARY UPSTREAM DEFECT)

The EP2 blueprint `integrated_scenario` (`patched_blueprint_after_fix__V75-D_blueprint_inplace.json:58`) opens with:

> "2006년 본가 저택 한시우의 방. 한시우는 눈앞에 떠오른 **HUD 상태창을 통해 직전 화에서 전이된** 자신의 신체 상태와 **사용 가능한 무공 목록**을 점검했다."

Three distinct contaminations in one sentence:

| Contamination | Text | Category |
|--------------|------|----------|
| Meta-structural reference | "직전 화에서 전이된" | meta/briefing prose |
| System/game language | "HUD 상태창을 통해" | system/game meta |
| Genre contamination | "사용 가능한 무공 목록" | wuxia language in investment fiction |

The `integrated_scenario` then continues in SUMMARY/BRIEFING register:
- "한시우의 건조한 질문에 수화기 너머 한국투자증권 최민호 차장의 타자 소리가 잠시 멈췄다" — functional summary
- "한시우는 등받이에 몸을 기댔다" — minimal scene direction
- "서재에 무거운 정적이 내려앉았다" — recycled from the tactical doc

The entire `integrated_scenario` reads as a **plot-point checklist in prose form**, not as scene authority or narrative direction. It is structured like "First X happens, then Y happens, then Z happens" rather than providing concrete sensory/emotional anchoring for scene writing.

### F-4: Blueprint Generation Prompt Lacks Anti-Briefing Guidance

The `BLUEPRINT_GENERATION_PROMPT` (`config/prompts/ensemble.yaml:354`) defines the output field as:

```
"integrated_scenario": "전체 에피소드 시나리오 (1000자 이상, 씬별 흐름을 자연스럽게 연결)",
```

Missing guardrails:
1. No instruction to write concrete scene-level prose vs. abstract summaries
2. No instruction to avoid meta-structural references ("직전 화", "이전 화에서 전이된")
3. No genre-specific guardrails against wuxia contamination in non-wuxia works (e.g., "무공" in investment fiction)
4. No anti-briefing examples or negative patterns
5. No instruction to ground the scenario in sensory/concrete details rather than plot-point enumeration
6. No instruction about the intended CONSUMER of this field (i.e., that CW will read it as advisory context)

The prompt DOES tell the blueprint generator "당신은 웹소설 에피소드 설계 전문가입니다" (you are a webnovel episode design expert) — but "설계 전문가" (design expert) actually encourages planning/briefing register rather than scene-writing register.

### F-5: Stage 3 `scene_breakdown` Also Carries Genre Contamination

The EP2 blueprint `scene_breakdown.scene_1.key_events` contains:

```json
"key_events": [
    "HUD 상태창 및 사용 가능한 무공 점검",
    "정확히 15억 원의 가용 자산 확인 (부동산 포함 총자산 20억)",
    "저녁 뉴스에서 이란 핵 문제 재점화 및 유가 상승세 보도 시청",
    "다음 날 오전 강남센터 방문 예약"
]
```

"HUD 상태창 및 사용 가능한 무공 점검" — "check HUD status window and available martial arts" is a wuxia concept forced into an investment fiction blueprint. This is not advisory text — it's in the **structured scene contract** which CW treats as authoritative.

Unlike `integrated_scenario` (which gets demoted to advisory), the `scene_breakdown` is fed directly to CW as the primary structural authority. The genre contamination in `key_events` bypasses the advisory demotion path entirely.

### F-6: Stage 4 Advisory Demotion is Partially Effective but has Three Gaps

Three mitigations exist in the Stage 4 pipeline:

1. **`_minimize_writer_blueprint()`** (`stage4_interview_round.py:930-943`): Moves `integrated_scenario` → `integrated_scenario_advisory`, clears original field
2. **`_extract_blueprint_sections()`** (`chief_writer_context.py:285-291`): Wraps advisory with:
   > "### [Advisory] 통합 시나리오 초안 (낮은 우선순위)
   > 이 블록은 흐름 참고용이다. Opening Anchor / Immutable Facts / prev digest / structured scene contract와 충돌하면 아래 prose는 버려라."
3. **Prompt placement** (`chief_writer_prompts.py:152`): Advisory appears AFTER scene_breakdown

**Gap A**: The advisory text still contains meta-structural language ("직전 화에서 전이된") verbatim. There is no instruction to CW that says "do not echo episode-reference language from this advisory." CW reads and parrots it.

**Gap B**: The `scene_breakdown.key_events` genre contamination ("무공 점검") is NOT advisory — it's in the primary scene contract. Stage 4's demotion only covers `integrated_scenario`, not scene_breakdown content.

**Gap C**: The advisory demotion label says "낮은 우선순위" (low priority) and "충돌하면 버려라" (discard on conflict) — but there is no instruction about **stylistic echo avoidance**. The priority hierarchy is about factual conflicts, not about style/register contamination.

### F-7: The Contamination Chain That Produced the Current EP2 Symptom

```
Stage 2 tactical doc EP2 (adequate, no meta language)
  ↓
Stage 3 blueprint LLM generates integrated_scenario
  → Injects "직전 화에서 전이된" (meta-structural)
  → Injects "HUD 상태창", "무공 목록" (genre contamination)
  → Injects "유동 자산 15억" (capital invention)
  ↓
Stage 3 blueprint LLM generates scene_breakdown
  → scene_1.key_events: "HUD 상태창 및 사용 가능한 무공 점검" (genre contamination in structured contract)
  ↓
Stage 4 _minimize_writer_blueprint: integrated_scenario → advisory
  → Meta language still present verbatim in advisory text
  → Genre contamination in scene_breakdown NOT demoted
  ↓
CW reads advisory + scene_breakdown
  → CW echoes: "직전 화에서 확인했던 자신의 상태창이었다"
  → CW echoes: "반투명한 홀로그램 창이 일렁이며 떠올랐다" (status window from advisory)
  ↓
FlashbackVerifier catches: truth conflict (EP1 had no status window)
Post-select A-3 catches: continuity + history conflict
  ↓
REJECT → retry needed (Round 2 → Round 3)
```

### F-8: Stage 3 Previous Blueprint Feed Amplifies Contamination

When generating EP2's blueprint, Stage 3 feeds EP1's blueprint as context (`blueprint_ensemble.py:1123-1139`):

```python
for bp in prev_blueprints:
    bp_scenario = bp.get("integrated_scenario", "")
    bp_lines.append(f"[시나리오] {bp_scenario}")
```

If EP1's blueprint also contained briefing-like prose or meta-structural language, it would contaminate EP2's generation as few-shot context. This creates a **compounding contamination effect** where each blueprint learns from the previous blueprint's bad patterns.

## 3. Non-Issues

| Surface | Reason |
|---------|--------|
| Stage 2 orchestrator code structure | DI context, delegation patterns are clean; not relevant to prose quality |
| Stage 2 validation pipeline | Validates arc structure/consistency, not prose quality; working correctly |
| Blueprint constraint compiler | `constraint_summary` correctly guards items; not related to meta-prose |
| Blueprint ensemble selection strategy | 3-candidate parallel generation + quality gates are sound |
| Stage 3 orchestrator storage | No data loss, corruption, or handoff error in blueprint persistence |
| Unified blueprint validator | Validates structural completeness, not prose register |
| Stage 2 preflight runtime | Preflight checks are about arc-level validity, not scene-level prose |

## 4. Verdict: `upstream-mixed`

**Primary cause: Stage 3 `integrated_scenario` generation (F-3, F-4, F-5)**

The Stage 3 blueprint generation prompt does not instruct the LLM to:
- Avoid meta-structural references
- Avoid genre contamination in non-primary genres
- Write concrete scene prose rather than plot-point summaries
- Consider the downstream consumer (CW) when choosing register

The result is `integrated_scenario` text that reads like a briefing/summary and contains meta/game/cross-genre language that CW echoes.

**Secondary cause: Stage 2 capital fact under-specification (F-2)**

The tactical doc leaves EP2's capital amount unspecified, allowing Stage 3 to invent a decomposition that then varies across CW attempts.

**Tertiary cause: Stage 4 advisory demotion gaps (F-6)**

The demotion covers factual priority but not stylistic echo avoidance, and it does not cover `scene_breakdown.key_events` genre contamination.

**This is NOT primarily a Stage 2 problem.** Stage 2's tactical doc is adequate scene-level prose. The contamination enters at Stage 3's blueprint generation and propagates through insufficient Stage 4 mitigation.

## 5. Required Artifacts

### Stage2/3 → Stage4 Authority Handoff Map

| Field | Source Stage | Authority Level at CW | Content Quality for EP2 | Problem? |
|-------|------------|----------------------|------------------------|----------|
| tactical_doc | Stage 2 | Hard Canon (via arc context) | Scene-writing prose, concrete | No |
| beat_sequence | Stage 2 | Hard Canon (via arc context) | Clean scene beats | No |
| state_constraints | Stage 2 | Hard Canon (via arc context) | Clean structured data | No |
| scene_breakdown | Stage 3 | Primary Structured Contract | **Genre contamination in key_events** | Yes (F-5) |
| integrated_scenario | Stage 3 | Advisory (demoted) | **Briefing prose + meta + genre** | Yes (F-3) |
| ending_hook | Stage 3 | Episode Mission | Clean | No |
| start_location | Stage 3 | Hard Anchor | Clean | No |
| end_location | Stage 3 | Episode Mission | Clean | No |
| core_tension | Stage 3 | Episode Mission | Clean | No |
| protagonist_state | Stage 3 | Episode State | Clean | No |
| ending_state | Stage 3 | Episode Mission | Clean | No |

### Upstream Ambiguity Table for Current EP2 Symptom

| Upstream Surface | EP2 Content | Problem Family | Severity |
|-----------------|-------------|----------------|----------|
| Arc1 tactical_doc EP2 | "자본금은 제 돈으로 합니다" (no amount) | capital under-specification | MINOR |
| Blueprint integrated_scenario | "유동 자산 15억 원...총자산 20억" | capital invention (15+5=20) | MODERATE |
| Blueprint integrated_scenario | "직전 화에서 전이된 자신의 신체 상태" | meta-structural reference | MAJOR |
| Blueprint scene_1.key_events | "HUD 상태창 및 사용 가능한 무공 점검" | genre contamination (wuxia in investment) | MAJOR |
| Blueprint integrated_scenario | "사용 가능한 무공 목록을 점검했다" | genre contamination | MAJOR |
| CW attempt_02 line 25 | "직전 화에서 확인했던 자신의 상태창이었다" | echoed meta language (downstream symptom) | CRITICAL |

### Bounded Remediation Seams (Lane 3 perspective)

| Seam | ROI | Complexity |
|------|-----|-----------|
| Add anti-briefing/anti-meta instructions to `BLUEPRINT_GENERATION_PROMPT` for `integrated_scenario` | HIGH | LOW |
| Add genre-consistency guard to scene_breakdown key_events generation | HIGH | MODERATE |
| Specify capital amounts in Stage 2 EP2 tactical doc when EP3 depends on them | MODERATE | LOW |
| Add "do not echo meta language from advisory" instruction to CW prompt | MODERATE | LOW |
| Strip genre-contaminated key_events from scene_breakdown before CW consumption | MODERATE | MODERATE |

## Stop

read-only lane complete; no files mutated
