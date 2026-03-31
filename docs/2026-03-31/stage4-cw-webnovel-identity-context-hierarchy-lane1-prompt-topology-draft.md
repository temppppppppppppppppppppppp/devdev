# Lane 1: CW First-Pass Prompt Topology / Writer Identity / Anti-Meta Contamination

Date: 2026-03-31
Status: draft-bounded-partial-evidence
Lane: Opus Terminal 1
Master Order: `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-parallel-master-order.md`
Baseline Commit: `170963d34d30d3076a57926c5d1ed250f13ec421`

## 1. Coverage

Surfaces inspected:

| Surface | LOC | Inspected |
| --- | --- | --- |
| `modules/domain/agents/chief_writer_prompts.py` | 305 | full |
| `modules/domain/agents/chief_writer_context.py` | 604 | full |
| `modules/domain/agents/chief_writer_context_packets.py` | ~400 | L1-400 (build_common_context_packets + carryover_ceiling) |
| `modules/core/stage4_context_builder.py` | 2801 | L1-800 (class shell + entity extraction + NPC boundary + work focus) |
| `modules/domain/agents/chief_writer.py` | 2246 | L1-300, L627-770 (generate_ensemble + _generate_single_candidate) |
| `config/prompts/chief_writer.yaml` | 181 | full |
| `projects/0_2/logs/session/llm_io.jsonl` | 156 | full scan (agent/prompt-head only; encoding renders Korean unreadable for deep content, but agent roles confirmed) |

## 2. Findings

### Finding F-1: Writer Identity Is a Single Sentence

**Evidence**: `chief_writer_prompts.py` L94-95 — `build_chief_writer_main_prompt()`:

```
[Role] 웹소설 1타 작가 (Chief Writer)
[Task] 제{ep_num}화 원고를 Blueprint 기반으로 집필하라.
```

This is the **entire** writer identity conditioning. Two sentences, ~40 characters of Korean.

There is no:
- Extended "you are a serialized webnovel author who writes immersive prose, not an analyst or summarizer" persona block
- Negative conditioning ("you are NOT a summarizer, analyst, briefing engine, or report writer")
- Craft voice framing ("your output is prose that a reader would pay to read, not a report for a reviewer")
- Creative process guidance ("think as a storyteller: visualize the scene, hear the dialogue, feel the tension")

**Severity**: HIGH — a single role line is trivially overridden by the register of the following ~40 prompt blocks.

### Finding F-2: Prompt Block Order Creates Analyst Register

**Evidence**: `chief_writer_prompts.py` L93-206 — the full block sequence in the first-pass prompt.

The exact first-pass block order (40 named blocks) is:

| Pos | Block | Register | Token Weight |
| --- | --- | --- | --- |
| 1 | `[Role] 웹소설 1타 작가` | writer | ~40 chars |
| 2 | `[Task] 제N화 원고를 Blueprint 기반으로 집필하라` | task | ~40 chars |
| 3 | `핵심 철학` | mission | ~30 chars |
| 4 | `[V67] 모순 절대 금지` | constraint | ~80 chars |
| 5 | `immutable_fact_section` | **analytical/contract** | variable, potentially 2K+ |
| 6 | `[STEP 0: Read This Authority First]` | **analytical hierarchy** | ~200 chars |
| 7 | `incarnation_context_section` | guidance | ~300 chars |
| 8 | `chain_link_section` | data | variable |
| 9 | `ending_hook_section` | guidance | variable |
| 10 | `dna_instruction` | guidance | variable |
| 11 | `purism_section` | constraint | variable |
| 12 | `world_origin_constraint_section` | constraint | variable |
| 13 | `feedback_section` | **Director feedback** | variable |
| 14 | `constraint_section` | **REJECT pattern list** | variable |
| 15 | `future_guard_section` | **inventory/guard list** | variable |
| 16 | `past_guard_section` | **guard list** | variable |
| 17 | `writer_core_section` | **mixed: world_state + directives + mandatory_context + anti_trope + justification + reflexion** | potentially 3K+ |
| 18 | `hud_anomaly_section` | **anomaly report** | variable |
| 19 | `[STEP 1: Blueprint 분석]` + `scene_breakdown` | **structured JSON** | 1K-3K |
| 20 | `integrated_scenario_advisory_section` | **advisory prose** | 1K-3K |
| 21 | `emotional_beat_section` | guidance | variable |
| 22 | `[STEP 2: 연속성 확인]` | heading | ~100 chars |
| 23 | `opening_anchor_section` | **contract** | ~400 chars |
| 24 | `prev_digest` | **Python-generated structured report** | 500-1500 chars |
| 25 | `carryover_ceiling_section` | **analytical authority ceiling** | 500-1500 chars |
| 26 | `prev_ending` | prose (last 2500 chars of prior ms) | ~2500 chars |
| 27 | `[STEP 3: 현재 상태 반영]` | heading | ~50 chars |
| 28 | `hud_report` | **HUD dashboard data** | variable |
| 29 | `high_density_hud_section` | **HUD dashboard data** | variable |
| 30 | `hud_trend_section` | **trend analysis** | variable |
| 31 | `npc_equipment_section` | **inventory list** | variable |
| 32 | `npc_frequency_section` | **frequency statistics** | variable |
| 33 | `[STEP 4: Arc 전술 참조]` | **tactical document** | variable |
| 34 | `[STEP 5: 세계관 설정]` | data | ~100 chars |
| 35 | `[STEP 6: 문체 DNA 가이드]` | **style guide** | variable |
| 36 | `reference_excerpt_section` | reference prose | variable |
| 37 | `satisfaction_guide_section` | guidance | ~200 chars |
| 38 | `common_rules` (YAML) | **writing rules** | ~2000 chars |
| 39 | `writing_guidelines` (YAML) | **writing guidelines** | ~800 chars |
| 40 | `prev_manuscripts_section` | **prior ms full-text** | potentially 30K+ |

**Register analysis**:
- **Writer/creative register blocks**: #1 (role), #38 (common_rules), #39 (writing_guidelines) — ~3 blocks, ~3K chars
- **Analytical/contract/HUD/report register blocks**: #5, #6, #13, #14, #15, #16, #17, #18, #19, #20, #23, #24, #25, #28, #29, #30, #31, #32, #33 — ~19 blocks, potentially 15K-25K chars
- **Neutral/data blocks**: remaining ~18 blocks

**Key problem**: The 3 strongest writing-identity blocks (role + common_rules + writing_guidelines) are at positions 1, 38, and 39. The LLM reads through 15K-25K tokens of analytical/structured content before encountering the detailed writing rules. By that point, the analytical register is deeply primed.

**Severity**: HIGH — the prompt architecture is an analyst task with a writer hat.

### Finding F-3: STEP Structure Reads Like Research Workflow

**Evidence**: `chief_writer_prompts.py` L106, 135, 142, 156, 174, 191, 194, 197.

The 7 STEPs are:
1. `STEP 0: Read This Authority First` — "read authority" is an analyst instruction
2. `STEP 0.5: 권위 우선순위` — "authority priority ranking" is governance language
3. `STEP 1: Blueprint 분석` — "분석" (analysis) is explicitly non-creative
4. `STEP 2: 연속성 확인` — "확인" (verify) is analytical
5. `STEP 3: 현재 상태 반영` — "상태 반영" (reflect status) is dashboard language
6. `STEP 4: Arc 전술 참조` — "전술 참조" (tactical reference) is planning language
7. `STEP 5: 세계관 설정` / `STEP 6: 문체 DNA 가이드` — worldbuilding/style, more neutral

This reads as: "Read → Rank → Analyze → Verify → Reflect status → Reference tactics → Configure output."

A writer-native STEP structure would read more like: "Enter the scene → Hear the characters → Feel the tension → Write the scene → Hook the reader."

**Severity**: MEDIUM — the STEP naming reinforces analyst register but is not the primary contamination vector (the block content is).

### Finding F-4: Bad Few-Shot Contamination Table

Blocks that model briefing/analytical output register for the LLM:

| Block | Contamination Type | Why Bad |
| --- | --- | --- |
| `prev_digest` | **Report format** | Python regex-extracted digest with headers like "사망 NPC:", "획득 아이템:", "부상 상태:", "마지막 위치:" — pure structured report |
| `hud_report` | **Dashboard** | HUD status display in game-like data format |
| `high_density_hud_section` | **Dashboard** | More detailed HUD dashboard data |
| `hud_trend_section` | **Trend analysis** | "최근 5화 HUD 변화 추세" with numerical trends |
| `hud_anomaly_section` | **Anomaly report** | Alert-style diagnostic output |
| `npc_frequency_section` | **Statistics** | Frequency count data: "주요 NPC 등장 빈도 (최근 10화)" |
| `npc_equipment_section` | **Inventory list** | Equipment status report |
| `carryover_ceiling_section` | **Authority ceiling document** | "prior/current authority only" — governance language |
| `immutable_fact_section` | **Fact contract** | Structured fact-ledger summary |
| `integrated_scenario_advisory_section` | **Advisory prose** | Explicitly labeled "advisory" — marked lower priority but still present in context window |
| `opening_anchor_section` | **Contract** | "이 화의 시작 계약 (불변)" — contract language |
| `constraint_section` | **Pattern list** | "이전 REJECT 패턴 - 회피 필수" — QA report |
| `future_guard_section` | **Guard list** | Inventory/dead-NPC/item guard data |

These 13 blocks collectively create a strong "you are analyzing data and producing a structured output" few-shot environment. The LLM processes thousands of tokens of report-style, dashboard-style, and contract-style prose before it encounters the actual scene-writing instructions.

**Severity**: HIGH — this is the most likely primary vector for briefing-style prose contamination.

### Finding F-5: Anti-Meta / Anti-Briefing Guardrails Are Narrow

**Evidence**: `config/prompts/chief_writer.yaml` COMMON_RULES_SECTION item 14:

```
14. [🚫 메타 월] 집필 시스템 내부 용어 금지: 원고 대사/서술에 "Block 1", "Block 2", "Arc 4",
    "Stage 3", "Blueprint", "treatment" 등 집필 시스템 메타용어를 사용하지 마세요.
```

This is a **4th-wall system-term ban**, not a briefing-voice ban. It prevents CW from writing "Blueprint에 따르면..." but does NOT prevent:
- "직전 화에서 확인했던 수치 그대로였다" (briefing-style recall)
- "현재 상태를 점검한 결과..." (status-check prose)
- "이전에 계산한 바에 따르면..." (analytical reference)
- Summary-style scene closings that read like report conclusions

There is no explicit:
- "Do not write as if you are summarizing events for a reader who was absent"
- "Do not write as if you are filing a status report"
- "Do not use retrospective/analytical phrasing like '확인했던', '점검한', '분석한'"
- "Write as if the reader is living the moment, not reviewing a briefing"

**Severity**: HIGH — the anti-meta guardrail has the right intent but wrong scope.

### Finding F-6: Anti-Trope Instructions Are Creative But Late

**Evidence**: `chief_writer_prompts.py` L268-304 — `get_anti_trope_instructions()`.

The anti-trope section is well-crafted for webnovel-specific quality:
- Bans "약해 보이는 주인공" cliche
- Bans "무시-사이다" loop
- Bans "순간 회복"
- Bans "NPC 기억상실"
- Bans "AI 티 문장" (AI-tell sentences)

This section (item 6 of anti-trope) is the closest to an anti-briefing voice rule:
```
6. "AI 티 문장" 금지
   - X "어느새", "말 그대로", "그야말로", "숨을 삼켰다", "시선을 돌렸다" 같은 상투구를 짧은 간격으로 반복
```

But this targets AI-tell *phrases*, not AI-tell *register/structure*. A sentence like "직전 화에서 확인했던 수치 그대로였다" uses no banned phrases but is structurally briefing-like.

**Severity**: LOW (anti-trope is good for what it does; it just doesn't cover the briefing register gap).

### Finding F-7: YAML Common Rules Writing Quality Is Strong But Positionally Weak

**Evidence**: `config/prompts/chief_writer.yaml` L16-55.

The COMMON_RULES_SECTION contains excellent craft instructions:
- Rule 1: "감정어 삭제 → 행동 변환" (delete emotion words, convert to action)
- Rule 2: "감각적 묘사 강화" (enhance sensory description)
- Rule 3: "요약된 대화의 장면화" (convert summarized dialogue into scenes)
- Rule 7: "캐릭터 고유 반응" (character-specific reactions)

Rule 3 is especially relevant — it explicitly says not to summarize dialogue. But it does not extend this principle to narrative prose.

These rules are injected at **position 38 of 40** in the prompt. By the time the LLM reaches them, it has already internalized thousands of tokens of analytical register.

**Severity**: MEDIUM — the rules exist but their positional weight is dramatically reduced by the prior analytical context.

### Finding F-8: `prev_manuscripts_section` at Position 40 Is a Double-Edged Sword

**Evidence**: `chief_writer_context_packets.py` L171-182.

When active (V67 lookback mode), this block inserts up to 30 episodes of prior manuscripts as "진실의 원천 (truth source)." This can be 30K+ tokens of actual webnovel prose.

In theory, this is the strongest few-shot signal for writing register. In practice:
- It appears at the very end of the prompt (position 40)
- It is framed as "truth source for contradiction prevention" — analytical framing
- The header is: "이전 원고 전문 — 진실의 원천 (모순 절대 금지)" — "truth source, contradiction absolutely forbidden"

This reframes prior narrative prose as evidence to be fact-checked, not as craft to be emulated.

**Severity**: MEDIUM — the content is webnovel prose but the framing transforms it into analytical evidence.

## 3. Non-Issues

### NI-1: CW Does Know It Is Writing a Webnovel
The role line `웹소설 1타 작가 (Chief Writer)` does exist. The problem is not that the role is absent but that it is **thin** and **positionally overwhelmed**.

### NI-2: The YAML Craft Rules Are Good
`COMMON_RULES_SECTION` and `WRITING_GUIDELINES_SECTION` contain solid webnovel craft guidance. The problem is not their content but their **position** at the end of the prompt.

### NI-3: Anti-Trope Is Effective for Cliche Prevention
The anti-trope system properly targets webnovel-specific cliches and AI-tell phrases. It is not responsible for the briefing register problem.

### NI-4: `integrated_scenario_advisory_section` Is Already Marked Lower Priority
The advisory block header says: "이 블록은 흐름 참고용이다. Opening Anchor / Immutable Facts / prev digest / structured scene contract와 충돌하면 아래 prose는 버려라."

This correctly labels advisory as lower authority. But the **register contamination** from having advisory prose in the context window persists regardless of the authority label.

## 4. Verdict

**identity-mixed**

CW's writer identity conditioning is:
- **Present** (role line exists)
- **Thin** (single sentence, ~40 characters)
- **Positionally overwhelmed** (38 blocks of analytical/structured content before the detailed writing rules)
- **Not negatively bounded** (no "you are NOT an analyst/summarizer" conditioning)
- **Not register-reinforced** (no extended craft persona, no creative process guidance)

The first-pass prompt architecture is structurally an **analyst task with a writer label**. The LLM is given a thin writer hat and then asked to process 15K-25K tokens of analytical data (HUDs, digests, contracts, authority ceilings, frequency statistics, inventory lists, advisory prose) before encountering the actual craft rules.

This creates a strong prior for briefing-style output that the thin identity conditioning cannot override.

## 5. Artifacts

### Block-Order Table
(See Finding F-2 — the 40-block table is the artifact.)

### Authority-Rank Table

| Rank | Authority Layer | Blocks in This Layer | First-Pass Position |
| --- | --- | --- | --- |
| 1 | Writer Identity | Role line (#1) | Top |
| 2 | Hard Canon | immutable_fact (#5), opening_anchor (#23), chain_link (#8) | Early/mid |
| 3 | Episode Mission | scene_breakdown (#19), ending_hook (#9), emotional_beat (#21) | Mid |
| 4 | Carryover Truth | prev_digest (#24), prev_ending (#26), carryover_ceiling (#25), prev_manuscripts (#40) | Mid/late |
| 5 | Soft Guidance | feedback (#13), constraint (#14), integrated_scenario_advisory (#20), hud_report (#28), hud_trend (#30), npc_freq (#32) | Scattered, mostly mid |
| 6 | Anti-Pattern | anti_trope (inside #17), common_rules (#38), writing_guidelines (#39), meta-wall (inside #38) | Late |

**Gap**: Writer Identity (Rank 1) has the fewest tokens and the weakest reinforcement. Anti-Pattern (Rank 6, where craft rules live) comes latest. Soft Guidance (Rank 5) has the most blocks and the strongest register contamination.

### Bad Few-Shot Contamination Table
(See Finding F-4 — the 13-block contamination table is the artifact.)

## 6. Stop

read-only lane complete; no files mutated
