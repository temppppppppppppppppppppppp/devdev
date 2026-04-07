# Lane 1: Stage2 Origin / Prompt / State-Lock Producer

Date: 2026-04-06
Lane: 1 of 5
Owner: Terminal 1
Mode: read-only survey
Audit Order: `docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-full-survey-audit-order.md`

## 1. Scope

Stage2 producer-side surfaces that first create or harden non-wuxia fatigue/stress into structured recovery obligations. This lane covers: prompt wording, deterministic state extraction, constraint compilation, scoring penalties, and natural-healing carveouts already present on the producer side.

## 2. Files Inspected

| File | Lines | Role |
|------|-------|------|
| `modules/domain/agents/arc_ensemble.py` | 2,209 | Arc candidate scoring + [NR-1] non-wuxia recovery block |
| `modules/domain/agents/state_extractor.py` | 868 | State extraction + `recovery_scene_required` injection |
| `modules/domain/agents/analyst_prompts.py` | ~660 | Prompt templates (PLAN_ARC_PROMPT_V25, SELF_CRITIC) |
| `config/prompts/analyst.yaml` | 698 | YAML prompt SSOT (V60.10 HARD LOCK, NR-1 carve-out) |
| `modules/domain/agents/preflight_checker.py` | ~500 | Preflight constraint output + `must_start_with` |
| `modules/domain/agents/four_phase_arc_generator.py` | ~1,700 | `_sanitize_injuries()`, `_check_arc_end_state()`, carryover lines |
| `modules/domain/agents/constraint_compiler.py` | ~280 | V62.2 forced reset (injuries="", energy=100) |
| `modules/domain/agents/analyst.py` | ~1,880 | `_build_genre_placeholders()` — wuxia vs non-wuxia energy rules |
| `tests/test_arc_ensemble_lane_a.py` | ~630 | 2 tests explicitly lock non-wuxia recovery behavior |

## 3. Evidence

### E-1. V60.10 HARD LOCK prompt — physical vs mental fatigue carve-out

**Source:** `config/prompts/analyst.yaml` L211-212, mirrored in `analyst_prompts.py` L224-227

```
[V60.10 HARD LOCK] 위 상태에서 명시된:
- 부상/상태: 물리적 부상은 회복 없이 활동 불가. 회복 장면 필수.
  단, 정신적 피로/스트레스는 수면·식사·대화 등 일상 활동 1문장으로 회복 가능.
- 소지품: 이미 있으면 다시 획득 금지.
- 위치: 순간이동 금지, 이동 과정 명시.
```

**Observation:** The V60.10 HARD LOCK itself already distinguishes physical injury (hard recovery obligation) from mental fatigue (one-sentence daily-activity recovery). This is the foundational carve-out.

### E-2. [NR-1] non-wuxia recovery block — dual enforcement path

**Source:** `arc_ensemble.py` L762-780 (`_build_non_wuxia_energy_block()`)

```
### [V62.2] 주인공 자연 회복 원칙
- 주인공은 소설 주인공이다. 절대 약해지지 않는다.
- 아크 시작: 부상="없음". 예외 없음.
- 이 장르는 내공/기력 시스템이 없음. "내공" 표현 절대 금지.

### [NR-1] 정신적 피로 자연 회복 원칙 (비무협 장르)
- 정신적 마모/스트레스/피로는 물리적 부상이 아니다. 일상적 활동으로 자연 회복된다.
- 회복 경로: 수면, 식사, 산책, 대화, 취미, 음주, 휴식 등 — 1문장 언급이면 충분.
- 회복은 opening beat에서 명시적으로 보여라.
- "시간이 지나며 회복했다" 같은 추상 문장만으로는 부족하다. 장면 안에서 보이는 회복 행동 1개는 필요하다.
- Arc 내에서 정신적 피로가 화를 거듭하며 악화만 하는 것은 금지. 반드시 회복 구간을 설계하라.
- 회복 없이 정신적 마모가 3화 연속 누적되면 REJECT 사유.
- 병원/정신과 방문은 선택사항이지 필수가 아니다. 일상적 회복이 기본이다.
```

**Observation:** [NR-1] is the key overreach surface. It says mental fatigue "is NOT physical injury" and "daily-activity recovery suffices" — but then:
- Demands **explicit scene-level recovery action** in the opening beat (not just a mention)
- Forbids abstract temporal recovery ("시간이 지나며 회복했다")
- Creates a **3-episode hard-fail rule** (3 consecutive episodes without recovery = REJECT)
- Effectively converts a soft advisory into a scene-level mandate

### E-3. Deterministic scoring penalty for vague opening recovery

**Source:** `arc_ensemble.py` L386-491 (`_collect_non_wuxia_recovery_issues()`)

Key logic chain:
1. **Gate:** `if is_wuxia(genre): return []` — wuxia is exempt (L388)
2. **Fatigue detection tokens (L407-418):** "회복", "피로", "스트레스", "지친", "탈진", "기다림", "6주", "몇 주", "며칠"
3. **Fatigue regex (L419-429):** `\brecovery\b`, `\bfatigue\b`, `\bstress\b`, `\bburnout\b`, `\bexhausted\b`, `\bwaiting\b`, `\bweeks?\b`, `\bdays?\b`
4. **Explicit action tokens (L430-461):** "수면", "잠", "식사", "샤워", "산책", "휴식", "대화", "술", "커피"
5. **Vague recovery tokens (L462-473):** "회복하는 시간", "시간이 지나", "버티는 시간"
6. **Decision (L475-490):**
   - No fatigue signal → pass
   - Fatigue + explicit action → pass
   - Fatigue + NO explicit action → **hard reject: "opening recovery beat too implicit for non-wuxia carryover fatigue"**

**Scoring (L565-568):**
```python
recovery_issues = _collect_non_wuxia_recovery_issues(candidate, genre)
if recovery_issues:
    penalty += min(6, len(recovery_issues) * 6)  # -6 per issue
    issues.extend(recovery_issues[:1])
```

**Observation:** This is the **deterministic Python-side hardening** — not prompt advice, but a scoring gate that penalizes candidates and produces a rejection-level issue string. The token lists are extremely broad: "weeks", "days", "waiting" alone can trigger the fatigue signal, meaning a perfectly normal investment work opening like "After weeks of preparation, he returned to the office" would fire the fatigue detector even though there is no actual fatigue.

### E-4. State extractor — `recovery_scene_required` auto-injection

**Source:** `state_extractor.py` L520-536 (`_validate_and_fix_result()`)

```python
recovery_needed = bool(injuries) or energy.get("current_percent", 100) < 50
result["next_arc_constraints"] = {
    "must_start_with": "이전 상태 계승" if recovery_needed else None,
    "recovery_scene_required": recovery_needed,
    "min_time_skip_days": min_days,
    "mandatory_items_in_possession": inv.get("current_items", []),
}
```

**Fallback path (L624-627):**
```python
"recovery_scene_required": bool(injuries) or loss_percent > 30,
```

**Observation:** `recovery_scene_required` is injected into `next_arc_constraints` for ALL genres. **No genre check exists.** Any LLM-reported injury or energy below 50% triggers `must_start_with: "이전 상태 계승"` + `recovery_scene_required: true`. The fallback is even more aggressive (energy loss > 30%). For non-wuxia works, "internal_energy" may not even be a meaningful concept, but the extraction schema still forces it.

### E-5. State extractor — V60.10 HARD LOCK prompt generation

**Source:** `state_extractor.py` L417-420 (`generate_constraint_prompt()`)

```python
lines = [
    "=" * 60,
    "🚨🚨🚨 [V60.10 STATE LOCK - 위반 시 즉시 REJECT] 🚨🚨🚨",
    "=" * 60,
    "",
    "### 1. 부상/내공 상태 (RECOVERY REQUIRED)",
]
```

And at L471-474:
```python
if constraints.get("recovery_scene_required"):
    lines.append(f"   ✅ 회복 장면 필수 (최소 {constraints.get('min_time_skip_days', 1)}일)")
if constraints.get("must_start_with"):
    lines.append(f"   ✅ 도입부: {constraints.get('must_start_with')}")
```

**Observation:** This generates a "RECOVERY REQUIRED" prompt header with "즉시 REJECT" language, injected into the Analyst. No genre-conditional wording. "내공 상태" is presented even for non-wuxia works if `internal_energy < 100`.

### E-6. Constraint compiler — V62.2 forced reset

**Source:** `constraint_compiler.py` L228-230

```python
# [V62.2] 내공 + 부상: 아크 간 자연 회복 → 항상 100% / 없음
internal_energy = 100
injuries = ""
```

**Observation:** The constraint compiler unconditionally resets injuries to empty and energy to 100% between arcs for the fallback path. This is the **natural healing implementation** — it treats inter-arc gaps as sufficient for full recovery. However, this only applies to the compiler fallback. The state extractor (E-4) can still inject `recovery_scene_required: true` before this reset takes effect.

### E-7. `_sanitize_injuries()` — inter-arc healing factor

**Source:** `four_phase_arc_generator.py` L1655-1662

```python
def _sanitize_injuries(self, raw: str) -> str:
    """[V62.2] 이전 Arc → 다음 Arc 전파 시 부상은 항상 '없음'.
    소설 세계관: 아크 간 시간 경과로 자연 치유 가정 (힐링팩터).
    """
    if not raw or raw.strip() in ("없음", "정상", ""):
        return "없음"
    logging.info(f" [V62.2] 자연 치유: '{raw[:50]}' → '없음' (아크 간 회복)")
    return "없음"
```

**Observation:** Physical injuries are **unconditionally reset** to "없음" between arcs. This is the natural healing the operator wants to preserve. It works correctly — but the problem is that the **prompt-side obligation** (NR-1, E-2) demands explicit recovery scenes even though the code-side resets the state.

### E-8. `_check_arc_end_state()` — NR-1 mental fatigue advisory

**Source:** `four_phase_arc_generator.py` L1686-1692

```python
_mental_keywords = ("정신", "마모", "스트레스", "피로", "mental", "fatigue", "burnout")
_is_mental = any(k in ei.lower() for k in _mental_keywords)
if _is_mental:
    warnings.append(f"status_shadow 정신적 피로 잔류: '{ei}' (일상 휴식으로 자연 회복 가능)")
else:
    warnings.append(f"status_shadow 부상 잔류: '{ei}'")
```

**Observation:** This is advisory-only (I-12 compliance). It correctly distinguishes mental fatigue from physical injury and downgrades mental fatigue to "일상 휴식으로 자연 회복 가능". This is **not** the overreach — it's a properly bounded advisory.

### E-9. Genre placeholder divergence — wuxia vs non-wuxia

**Source:** `analyst.py` L1828-1873 (`_build_genre_placeholders()`)

Wuxia path: detailed 내공 tracking with explicit recovery mechanics (운기조식, 영약, 비급).
Non-wuxia path: generic "핵심 수치" tracking with "내공 표현 절대 금지" guard.

**Observation:** The energy_tracking_rules diverge correctly by genre. Non-wuxia does NOT get wuxia recovery mechanics. But the **state_extractor** (E-4) still uses `internal_energy` as a generic field and triggers `recovery_scene_required` based on it regardless of genre.

### E-10. Continuity Absolute Rule — injury hardening

**Source:** `analyst.yaml` L234-243

```
### 연속성 절대 준수 (CONTINUITY ABSOLUTE RULE) [V49.2]
위 [실전 연표]에 명시된 직전 Arc의 종료 상태는 성경과 같은 불변의 진실이다.

2. 부상 연속성: 직전 Arc에서 입은 부상/{energy_stat_name} 소모는
   현재 Arc 도입부에 반드시 반영되어야 한다.
   - 부상 상태에서 무리한 행동은 회복/치료 장면이 선행되어야 한다.
   - "갑자기 멀쩡해지는" 설정은 CRITICAL 위반이다.
```

**Observation:** This rule uses `{energy_stat_name}` which for non-wuxia resolves to e.g. "투자 핵심 수치" — meaning investment capital fluctuation is tracked with the **same injury-continuity framework** as physical wounds. The "부상 상태에서 무리한 행동" language is wuxia-native and creates confusion when applied to an investment protagonist who merely had a stressful week.

### E-11. Tests that lock the current behavior

**Source:** `tests/test_arc_ensemble_lane_a.py` L509-584

Two tests explicitly codify the non-wuxia recovery penalty:

1. **`test_evaluate_candidate_penalizes_implicit_non_wuxia_recovery_opening()`** (L509-546):
   - Genre: `investment`
   - Candidate: "After six weeks of waiting and accumulated stress, he had time to recover over time"
   - Assertion: `assert "opening recovery beat too implicit for non-wuxia carryover fatigue" in issues`

2. **`test_evaluate_candidate_accepts_explicit_non_wuxia_recovery_opening()`** (L548-584):
   - Genre: `investment`
   - Candidate: "he takes a shower, eats, and sleeps before returning to the trading desk"
   - Assertion: the rejection message is NOT present

**Observation:** These tests intentionally lock the current behavior. Any future patch that relaxes the non-wuxia recovery penalty would need to update or remove these tests.

## 4. Findings

### F-1. [NR-1] prompt creates a scene-level mandate from a soft premise (P2)

[NR-1] correctly states that "정신적 마모/스트레스/피로는 물리적 부상이 아니다" — but then demands:
- Explicit action in opening beat (not abstract recovery)
- 3-episode hard-fail rule

This converts a soft "daily-activity recovery suffices" principle into a **scene-level deterministic gate** at the scoring layer. The operator's concern — that investment/office/business-power arcs get rejected because the opening doesn't stage a recovery beat — is **confirmed as structurally present**.

**Confidence: 98%**

### F-2. Fatigue detection tokens are over-broad (P2)

`_collect_non_wuxia_recovery_issues()` treats "weeks", "days", "waiting" as fatigue signals. An investment opening like "After weeks of preparation, he entered the trading floor" would fire the detector even though no actual fatigue is described. The token set conflates **temporal markers** with **fatigue state**.

**Confidence: 97%**

### F-3. `state_extractor` injects `recovery_scene_required` without genre check (P2)

`_validate_and_fix_result()` and `_fallback_extraction()` set `recovery_scene_required: true` based on `internal_energy < 50` or `loss_percent > 30`, with no genre conditional. For non-wuxia works where `internal_energy` is not a meaningful concept, a stray LLM-reported number can trigger a recovery obligation.

**Confidence: 95%**

### F-4. The carve-out IS present but NOT consistently enforced (P2)

The system already has the right distinction in multiple places:
- `analyst.yaml` L212: "정신적 피로/스트레스는 수면·식사·대화 등 일상 활동 1문장으로 회복 가능"
- `four_phase_arc_generator.py` L1686-1692: mental fatigue advisory downgrade
- `_sanitize_injuries()`: unconditional inter-arc injury reset

But the **scoring layer** (`_collect_non_wuxia_recovery_issues`) does NOT read the carve-out distinction. It treats ALL fatigue signals the same regardless of whether the source is physical injury or office stress.

**Confidence: 96%**

### F-5. Constraint compiler's V62.2 reset is correct but downstream prompt can re-harden (P3)

`constraint_compiler.py` L228-230 correctly resets injuries="" and energy=100. But `state_extractor.generate_constraint_prompt()` can still emit "RECOVERY REQUIRED" headers before this reset reaches the next arc. The prompt and the code disagree on authority.

**Confidence: 93%**

### F-6. Tests intentionally lock the overreach (P2)

Two tests in `test_arc_ensemble_lane_a.py` explicitly assert the current penalty behavior for investment genre. These are not accidental — they were written to codify the [NR-1] recovery mandate. Any fix must update these tests.

**Confidence: 99%**

## 5. Open Questions

1. **Does `state_extractor.generate_constraint_prompt()` ever run for non-wuxia genres in production?** If it only fires for wuxia, F-3 severity drops. (Requires Lane 5 runtime evidence or fresh run verification.)

2. **Is the 3-episode hard-fail rule in [NR-1] actually enforced by Python scoring, or only by LLM prompt?** The current `_collect_non_wuxia_recovery_issues()` does NOT count consecutive episodes — it only checks the current opening. If the 3-episode rule is prompt-only, it's LLM-discretionary. If it's ever backed by Python counting, it would be a harder lock.

3. **Does `_collect_non_wuxia_recovery_issues()` ever fire on false positives in production investment runs?** The token-overlap risk (E-3 observation) is structural but may or may not manifest in practice. (Requires Lane 5 runtime evidence.)

## 6. Provisional Severity

| Finding | Severity | Confidence |
|---------|----------|------------|
| F-1: NR-1 scene mandate from soft premise | P2 | 98% |
| F-2: Over-broad fatigue detection tokens | P2 | 97% |
| F-3: `recovery_scene_required` no genre check | P2 | 95% |
| F-4: Carve-out present but scoring ignores it | P2 | 96% |
| F-5: Compiler reset vs prompt re-hardening | P3 | 93% |
| F-6: Tests lock overreach | P2 | 99% |

**Overall Lane 1 severity: P2** — meaningful overreach that can produce bad rejects or poor runtime pressure for non-wuxia works. Not P1 because `_sanitize_injuries()` prevents physical state from persisting cross-arc, and the V60.10 prompt does contain a partial carve-out. The issue is that the scoring layer does not honor the carve-out.

## 7. Recommended Merge Notes

### For cross-lane synthesis:

1. **The overreach origin is primarily Stage2 producer-side** — specifically `arc_ensemble.py` L386-491 (scoring) and `arc_ensemble.py` L762-780 (NR-1 prompt block). Stage2 creates the structured obligation that downstream stages consume.

2. **The carve-out already exists in prompt text** (`analyst.yaml` L212) but is NOT reflected in the deterministic scoring path. The fix surface is likely the scoring function `_collect_non_wuxia_recovery_issues()` and the fatigue token set, not the prompt text itself.

3. **`state_extractor.py`'s `recovery_scene_required` injection is a secondary amplifier** — it adds a structured boolean that downstream stages can consume as hard authority, without genre awareness.

4. **Natural healing (`_sanitize_injuries()`) works correctly** and should be preserved as-is. The operator concern is NOT about natural healing being broken — it's about prompt/scoring surfaces that demand explicit recovery scenes for soft fatigue before natural healing can take effect.

5. **Smallest future patch surface for Stage2:**
   - Add genre awareness to `_collect_non_wuxia_recovery_issues()` fatigue token set — narrow temporal tokens ("weeks", "days") that are not inherently fatigue
   - Consider softening the [NR-1] 3-episode rule from REJECT to advisory for non-wuxia genres
   - Add genre check to `state_extractor._validate_and_fix_result()` for `recovery_scene_required`
   - Update 2 tests in `test_arc_ensemble_lane_a.py`

6. **Cross-stage question for Lanes 2-4:** Does `recovery_scene_required: true` from state_extractor actually reach Stage3/Stage4 as a hard gate, or is it consumed only by the Analyst prompt? This determines whether the fix is Stage2-local or cross-stage.

---

3-Pass Audit Record:

Pass 1: Document type matches lane survey format. Scope is bounded to Stage2 producer surfaces. All 7 survey questions from the order are addressed.

Pass 2: All file paths verified against live workspace. Line numbers verified against agent inspection results. Evidence quotes are exact. No code patches proposed.

Pass 3: Findings are bounded to inspected evidence. Severity assignments use the order's rubric. Open questions are explicitly flagged. No overclaim beyond inspected scope.

Estimated confidence: 96%
