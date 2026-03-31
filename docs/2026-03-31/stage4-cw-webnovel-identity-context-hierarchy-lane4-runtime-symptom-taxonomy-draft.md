# Lane 4: Runtime Symptom Taxonomy & Downstream Family Misclassification

Date: 2026-03-31
Status: draft-bounded-partial-evidence
Terminal: Opus Terminal 4
Master Order: `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-parallel-master-order.md`

---

## 1. Coverage

| Surface | Read | Evidence Extracted |
|---------|------|--------------------|
| `0_temp.txt` L620-760 | yes | EP2 round 1-3 full runtime trace |
| `flashback_verifier.py` full | yes | marker list, LLM prompt, parse logic |
| `stage4_interview_round.py` advisory chain L4963-5082 | yes | 9 advisory parallel structure |
| `stage4_interview_round.py` post-select L3984-4171 | yes | continuity + history conflict checks |
| `stage4_interview_round.py` advisory tier classification L1582-1598 | yes | tier 3/2/1 ranking |
| `quality_signal_metrics.py` ai_slop patterns L23-35 | yes | 11 cliche patterns, no meta/briefing |
| `pre_director_style_checker.py` | yes (grep) | sentence variety, pacing rhythm only |
| `director.py` check_manuscript_history_conflicts | yes | facade to _continuity sub-module |
| `projects/0_2/drafts/ep_0001.txt` | yes | EP1 canonical asset breakdown |
| `projects/0_2/logs/artifacts/stage4/ep_0002/attempt_01/` | yes | Round 1 rejected C |
| `projects/0_2/logs/artifacts/stage4/ep_0002/attempt_02/` | yes | Round 2 rejected A — THE symptom |
| `projects/0_2/logs/artifacts/stage4/ep_0002/attempt_03/` | yes | Round 3 PASS B |
| `projects/0_2/logs/session/decisions.jsonl` | yes | EP2 decision records |
| `projects/0_2/logs/session/llm_io.jsonl` | yes (grep) | FlashbackVerifier LLM exchange confirmed |
| `projects/0_2/logs/session/ui_events.jsonl` | navigational | via 0_temp trace |

---

## 2. Findings

### F-1. The Bad Sentence — Sentence-Level Classification

**Location**: `attempt_02/selected_before_fix__A.txt` lines 19-25 (Round 2, candidate A)

**The sentence**:
> 휴대전화를 책상 위에 내려놓자, 텅 빈 허공 위로 반투명한 홀로그램 창이 일렁이며 떠올랐다.
> [... status window display ...]
> 직전 화에서 확인했던 자신의 상태창이었다. 이상이 없음을 확인한 뒤 시선을 돌렸다.

**Three stacked defects**:

| # | Defect | Family | Severity |
|---|--------|--------|----------|
| D-1 | Hologram status window (홀로그램 상태창) fabricated — EP1 has no such system element | **Fabricated entity** (hard truth conflict sub-type) | CRITICAL |
| D-2 | Asset breakdown: 15억 금융 + 5억 부동산 = 20억 contradicts EP1's canonical 12억 부동산 + 5억 펀드 + 3억 예금 = 20억 | **Numeric history conflict** | CRITICAL |
| D-3 | "직전 화에서 확인했던 수치 그대로였다" — recap-register phrasing that reads like an analyst confirming data rather than a character experiencing a moment | **Meta/briefing prose** (webnovel voice failure) | MODERATE |

**Primary classification**: D-1 + D-2 are **hard truth conflicts**. D-3 is a secondary **webnovel voice failure** layered on top.

**Key insight**: The sentence is bad primarily because it fabricates a world element and gets the numbers wrong, NOT primarily because it is meta-prose. The meta-prose quality (D-3) makes it aesthetically worse but would not alone trigger a REJECT.

### F-2. FlashbackVerifier — Correct Finding, Imprecise Detection Path

**Detection mechanism**:
- Marker '떠올랐다' matched `FLASHBACK_MARKERS` list (line 26 of `flashback_verifier.py`)
- 200-char window extracted around marker
- LLM asked to check if flashback content contradicts past episode context

**What actually happened**:
- '떠올랐다' in this context describes the hologram window **physically appearing** ("홀로그램 창이 일렁이며 떠올랐다"), not a character performing a mental flashback
- The marker hit was **incidental** — the word happened to be nearby the real problem
- However, the LLM step **correctly identified** the real truth conflict: "요약된 1화의 결말은 자산 규모를 묻는 질문으로 끝났으므로 직전 화에서 이미 구체적인 수치를 확인했다는 서술은 과거 맥락과 모순됩니다"

**Classification**: FlashbackVerifier labeled this as "회상 오염" (flashback contamination). The label is **imprecise but the underlying finding is valid**. This is not flashback contamination — it is a false recall of a fabricated entity. The FlashbackVerifier acted as an unintentional proxy detector for a truth conflict that overlapped with a recall-type verb.

**Impact**: Advisory-only. FlashbackVerifier's finding was presented to Director but did NOT directly cause the REJECT. The REJECT came from the **post-select continuity + history conflict checks**, which independently caught the same problem with more precise classification.

### F-3. Post-Select Checks — Correct Classification

The post-select checks (L3984-4171 of `stage4_interview_round.py`) fired two independent LLM checks after Director selected candidate A:

| Check | Finding | Classification | Correct? |
|-------|---------|----------------|----------|
| Continuity conflict | "1화에 존재하지 않았던 상태창(시스템) 설정이 2화에서 '직전 화에서 확인했다'는 서술과 함께 갑자기 등장" + 스마트폰 명칭 충돌 | `[Continuity Conflict]` | **YES** — fabricated entity correctly caught |
| History conflict | "제1화에서 확립된 자산의 세부 구성 금액(부동산과 금융자산의 비율)을 다르게 서술" + 홀로그램 상태창 + 피처폰→스마트폰 | `[V67] History Conflict` | **YES** — numeric truth + entity truth correctly caught |

**TF-3 downgrade**: Both conflicts triggered `Provisional PASS → REJECT downgrade` with `error_category = POST_SELECT_CONTINUITY_AND_HISTORY`. This is **correctly classified** and the downgrade is **correctly warranted**.

### F-4. Retry Fixed the Problem — Not by Style, by Task Narrowing

**Attempt 03 (Round 3, PASS, candidate B)**:
- No hologram status window (D-1 eliminated)
- Asset breakdown 12억/5억/3억 matches EP1 (D-2 eliminated)
- No "직전 화에서 확인했던" phrasing (D-3 eliminated)
- Uses physical sensory detail instead ("은색 슬라이드 휴대전화의 금속 질감", "이면지에 갈겨쓴 숫자들")

Retry feedback included explicit conflict citations:
> `[Conflict-first retry] post-select hard conflict invalidated the provisional PASS. 다음 라운드는 local patch가 아니라 authoritative carryover 기준 재작성으로 처리하세요.`
> `[Continuity Conflict] 1화에 존재하지 않았던 상태창(시스템) 설정이 2화에서...`
> `[V67] History Conflict: 제2화는 제1화에서 확립된 자산의 세부 구성 금액...`

**Why retry worked**: CW received explicit truth constraints in retry feedback. The task shape narrowed from "write EP2" to "write EP2 without these specific conflicts". This is correct behavior — the feedback loop worked as designed.

### F-5. Detector Coverage Inventory

#### Current Detector Map (9 Advisory + 2 Post-Select + 2 Pre-Director)

| Detector | Phase | Mode | Family Covered | Tier |
|----------|-------|------|----------------|------|
| TruthGate | Advisory | LLM | World law violations | 3 |
| NpcDrift | Advisory | LLM | NPC personality/behavior drift | 2 |
| FlashbackVerifier | Advisory | LLM | Flashback scene content contamination | 2 |
| InfoParadox | Advisory | LLM | Information paradox (character knows too much/little) | 2 |
| RelDrift | Advisory | LLM | Relationship consistency drift | 2 |
| NumericDrift | Advisory | LLM | Numeric trend anomalies | 1 |
| NumericConsistency | Advisory | Python | Numeric self-consistency within manuscript | 1 |
| LongTermRepetition | Advisory | LLM | Cross-episode phrase/plot repetition | 1 |
| StyleSignal | Advisory | Python | AI slop cliches + CED error density | 1 |
| Continuity Check | Post-select | LLM | Sequential episode continuity conflicts | blocking |
| History Check | Post-select | LLM | Full manuscript history conflicts | blocking |
| PreDirectorChecklist | Pre-Director | Python | Blueprint compliance, length, ratios | pre-filter |
| PreDirectorStyleChecker | Pre-Director | Python | Sentence variety, pacing rhythm | pre-filter |

#### Detector Coverage Gap Table

| Gap | Family | What It Would Catch | Current Nearest Detector | Why Nearest Is Insufficient |
|-----|--------|---------------------|--------------------------|----------------------------|
| **G-1: Anti-meta/briefing prose** | Webnovel voice | "직전 화에서 확인했던 수치 그대로였다", recap register, analyst confirmation phrasing, HUD-reading narration | StyleSignal (ai_slop) | ai_slop only catches 11 fixed cliche patterns; does NOT detect analytical/briefing/summarizer register |
| **G-2: Fabricated entity** | Hard truth (sub-type) | CW invents world elements (status window, systems, items) and falsely attributes them to prior episodes | Post-select history check | History check catches this AFTER Director selection — burns a full LLM round; no pre-selection advisory |
| **G-3: Anachronism** | Historical truth | 2006년 setting에서 "스마트폰" 언급 (피처폰 시대) | Post-select continuity | Same post-hoc detection; no Python-level period-correct vocabulary guard |
| **G-4: Recap register** | Webnovel voice (sub-type) | Sentences that read like "지난 시간 줄거리" instead of immersive scene prose | None | No detector exists for this specific pattern |

### F-6. Current EP2 Symptom Taxonomy Table

| Symptom | Attempt | Round | Source | Family | Detector That Caught | Correctly Classified? |
|---------|---------|-------|--------|--------|---------------------|-----------------------|
| Hologram status window fabricated | 02 | 2 | CW (candidate A+C) | Fabricated entity | Post-select continuity + history | YES |
| Asset breakdown 15+5 ≠ 12+5+3 | 01, 02 | 1, 2 | CW (all candidates) | Numeric history conflict | Post-select history | YES |
| "직전 화에서 확인했던" false recall | 02 | 2 | CW (candidate A+C) | False recall + mild meta | FlashbackVerifier (incidental marker) + Post-select | PARTIALLY — FlashbackVerifier label "회상 오염" is imprecise; post-select labels are correct |
| 스마트폰 anachronism (2006) | 02, 03 | 2, 3 | CW | Anachronism | Post-select continuity | YES (in 02); 03 has it in final_manuscript line 21 but passed — **gap** |
| "입을 열었다" AI slop | 01, 02 | 1, 2 | CW | Style cliche | StyleSignal | YES |
| CED python warnings 4-5건 | 01, 02 | 1, 2 | CW | Error density | StyleSignal | YES |

---

## 3. Non-Issues

### NI-1. FlashbackVerifier Is Not Structurally Broken
The marker list is reasonable for its intended purpose (actual flashback scenes). The '떠올랐다' hit in this case was a false positive on the marker level, but the LLM step compensated correctly. The verifier produced a valid finding through an imprecise path. No structural repair needed — this is within acceptable advisory tolerance.

### NI-2. Post-Select Checks Are Working As Designed
Both continuity and history checks correctly identified the hard truth conflicts and correctly triggered the TF-3 downgrade. The classification labels are accurate. The rejection feedback to CW was specific enough for retry to succeed.

### NI-3. Director Selection Quality Is Not the Primary Issue
Director selected candidates that happened to contain truth conflicts, but Director's job is creative quality judgment, not truth verification. The post-select truth checks exist precisely to catch what Director cannot. The system's layered defense worked — Director gave provisional PASS, post-select caught the truth conflicts, retry succeeded.

### NI-4. TruthGate Did Not Fire — Expected Behavior
TruthGate checks world law violations (e.g., deceased NPC acting). A fabricated status window doesn't violate a known world law — it introduces something that WASN'T established, not something that contradicts an established rule. TruthGate's non-firing is correct for this symptom type.

---

## 4. Verdict

**`mixed: true-conflict-primary with style-gap-secondary`**

Detailed breakdown:

| Component | Assessment |
|-----------|------------|
| Is the EP2 sentence primarily a truth conflict? | **YES** — fabricated entity + wrong numbers (D-1, D-2) |
| Is it primarily meta/briefing prose? | **NO** — meta quality (D-3) is secondary |
| Is FlashbackVerifier misclassifying? | **PARTIALLY** — correct finding via imprecise marker path; label "회상 오염" is misleading for this specific case |
| Are post-select checks misclassifying? | **NO** — correct labels, correct downgrade |
| Is there a meaningful detector gap? | **YES** — G-1 (anti-meta/briefing prose) and G-4 (recap register) have no dedicated detector |
| Did retry fix the problem? | **YES** — via explicit conflict feedback, not via style improvement |

The current EP2 symptom is **primarily a hard truth conflict** (fabricated entity + numeric mismatch) that **also happens to carry meta/briefing prose qualities**. The meta/briefing quality is a contributing aesthetic defect but would not alone have caused rejection.

The most important gap is **G-1**: no dedicated anti-meta/briefing prose detector exists. Current ai_slop patterns catch fixed cliches but miss analytical/briefing register. If CW had fabricated the status window with perfectly immersive prose, the truth conflict would still have been caught by post-select — but if CW writes meta/briefing prose WITHOUT a truth conflict, no current detector would flag it.

---

## 5. Stop

read-only lane complete; no files mutated

---

## Appendix: Artifact Tables

### A-1. Symptom Taxonomy Table (Required)

| ID | Symptom | Family | Sub-Family | Detection Path | Detection Phase | Blocking? |
|----|---------|--------|------------|----------------|-----------------|-----------|
| S-1 | Fabricated hologram status window | Hard truth conflict | Fabricated entity | Post-select continuity + history | Post-select | YES (TF-3) |
| S-2 | Asset breakdown 15+5 vs 12+5+3 | History conflict | Numeric mismatch | Post-select history | Post-select | YES (TF-3) |
| S-3 | "직전 화에서 확인했던" false recall | False recall | Recap-register overlap | FlashbackVerifier (incidental) + Post-select | Advisory + Post-select | Advisory: no. Post-select: YES |
| S-4 | 스마트폰 anachronism (2006) | Anachronism | Period-incorrect vocabulary | Post-select continuity | Post-select | YES (R2), missed (R3) |
| S-5 | "입을 열었다" cliche | AI slop | Fixed pattern | StyleSignal | Advisory | NO (advisory-only) |
| S-6 | CED 4-5 python warnings | Error density | Python check count | StyleSignal | Advisory | NO (advisory-only) |

### A-2. Detector Coverage Gap Table (Required)

| Gap ID | Missing Family | Pattern Example | ROI if Fixed | Difficulty |
|--------|---------------|-----------------|--------------|------------|
| G-1 | Anti-meta/briefing prose | "직전 화에서 확인했던 수치 그대로였다", "~를 확인한 뒤", recap-style exposition | **HIGH** — only gap with no alternative path | MEDIUM — needs LLM or pattern list |
| G-2 | Fabricated entity pre-advisory | New world elements falsely attributed to prior episodes | MEDIUM — post-select already catches; would save 1 LLM round | HIGH — requires entity tracking |
| G-3 | Anachronism | "스마트폰" in 2006 setting | LOW — rare, post-select catches most | LOW — Python vocabulary + era check |
| G-4 | Recap register | "지난 시간 줄거리" style narration | HIGH — overlaps with G-1 but narrower | LOW — Python pattern list |

### A-3. Current EP2 Sentence-Level Classification Note (Required)

**Target sentence**: "직전 화에서 확인했던 자신의 상태창이었다. 이상이 없음을 확인한 뒤 시선을 돌렸다."

**Surrounding context**: Hologram window appears with [Name/Capital/Goal] display. Character glances at it, confirms nothing changed, looks away at TV news.

**Classification**:
- The hologram status window is a **fabricated world element** — EP1 has no such system. This is the most critical defect.
- The numbers shown (15억+5억) are a **numeric history conflict** — EP1 establishes 12억+5억+3억.
- The phrase "직전 화에서 확인했던" is a **false recall claim** — there was nothing to confirm in EP1.
- The prose register ("확인했던 수치 그대로였다", "이상이 없음을 확인한 뒤") reads like **briefing/analyst confirmation** rather than immersive character experience.
- **Primary family**: Hard truth conflict (fabricated entity + numeric mismatch)
- **Secondary family**: Webnovel voice failure (meta/briefing register)
- **Detector correctly caught primary**: Post-select continuity + history (YES)
- **Detector correctly caught secondary**: No dedicated detector (GAP)
- **FlashbackVerifier**: Caught via incidental marker match; label imprecise but finding valid
