# T2. Stage 4 In-Prompt Self-Audit Restoration — Triage Report

Date: 2026-03-25
Status: final
Document Type: lane triage report
Lane: T2 (of 7)
Canonical Path: `docs/2026-03-25/opus-deferred-triage/t2-stage4-inprompt-self-audit-restoration.md`

## 1. Question

Is restoring Stage 4 in-prompt self-audit worth opening now, or is the existing Self-Critique loop already enough?

## 2. Findings

### 2.1 What Was Removed (V50/V65)

Three dead-code artifacts prove Stage 4 once had in-prompt self-audit:

**A. `prompt_builder.py:527-544` — `generate_self_diagnosis_checklist()`**
- Renders 5 checklist items: length, scene coverage, pacing, setting consistency, style
- Called only from `generate_v50_writer_prompt()` (L757), which is itself dead code
- Dead since V65 refactor

**B. `prompt_builder.py:701-765` — `generate_v50_writer_prompt()`**
- Wrapper that assembled the full V50 writer prompt including the self-diagnosis checklist
- `main_a.py:2157`: `# [V65] _generate_v50_writer_prompt 삭제 — Stage 4 V2 파이프라인에서 미호출 Dead Code`

**C. `quality_amplifier.py:209-276` — `generate_writer_constraints()`**
- Includes a `[제출 전 자가 검증]` block with 5 checkbox items (ending continuity, item persistence, relationship change limit, blueprint scene coverage, cliffhanger ending)
- Never wired: `stage4_context.py` has zero `quality_amplifier` slots; `chief_writer.py` has zero `quality_amplifier` references

**D. `config/prompts/writer_rules.json:87+` — `self_diagnosis_checklist` data**
- Detailed JSON-based checklist: 분량(15점), 장면구성(25점), 서사흐름(20점), 설정일관성(25점), 문체(15점)
- No live consumer

### 2.2 What Currently Covers Stage 4 Self-Audit

**A. Post-Generation Multi-Round LLM Self-Critique** (`chief_writer_quality.py:102-247`)
- `apply_self_critique()`: up to 3 rounds of LLM-based critique + fix
- `_self_critique()` (`chief_writer_quality.py:249-369`): 17 concrete check categories:
  1. HUD consistency (L285)
  2. Cliche overuse (L289)
  3. Justification gaps (L292)
  4. NPC relationship consistency (L297)
  5. Motivation/promise abandonment (L300-303)
  6. WritingDirective compliance (L306)
  7. Expression freshness (L309)
  8. AI-tell patterns (L312)
  9. ending_hook presence (L315)
  10. Arithmetic consistency (L318)
  11. System term exposure / meta wall (L321)
  12. Ending novelty (L324)
  13. Temporal logic (L327)
  14. Paragraph structure (L330)
  15. Tonal consistency (L333)
  16. POV consistency (L336)
  17. Scene transition markers (L339)
- Plus: manuscript length check (L342-355), rubric pre-check (L146-167), gate checks for ending_hook + length + meta_wall (L175-202)
- **This is the strongest self-audit mechanism in the entire system.**

**B. In-Prompt Structural STEPs** (`chief_writer_prompts.py:129-199`)
- STEP 0.5: Authority priority hierarchy
- STEP 1-6: Blueprint analysis, continuity, state, arc, worldbuilding, style
- These are writing instructions, not self-audit. They tell the LLM what to write, not what to verify.

### 2.3 Overlap Analysis: V50 Checklist vs Current Self-Critique

| V50 / Dead-Code Item | Self-Critique Coverage | Gap? |
|---|---|---|
| 분량 4,500자+ | manuscript_length check (L342) | No |
| 6개 씬 모두 반영 | scene_transition_markers (L339) | No |
| 씬 분량 균등 | paragraph_structure (L330) — partial | Minor |
| High Impact Zone 상세 | Not checked | Yes |
| 서사 폭주 금지 | tonal_consistency (L333) — weak | Minor |
| 서사 정체 금지 | tonal_consistency — weak | Minor |
| 미습득 무공 사용 금지 | HUD consistency (L285) | No |
| 장비/아이템 일관성 | HUD consistency (L285) | No |
| 인물 이름 일치 | NPC relationship (L297) — partial | Minor |
| 사망 인물 부활 방지 | Not in Self-Critique (pre-LLM validator covers) | Minor |
| 직전 화 엔딩 연결 | Not explicitly checked | Yes |
| 클리프행어 종료 | ending_hook check (L315) | No |
| 대화 4개+ | Not checked | Yes |
| 감각 묘사 포함 | Not checked | Yes |

**Overlap rate**: ~70% of V50 items are already covered by Self-Critique or existing STEP instructions.

**Genuine gaps**: High Impact Zone density, pacing balance (폭주/정체), previous-episode ending continuity, dialogue count, sensory description. These are real, but moderate — and all are things the LLM should do from the existing STEP instructions and blueprint.

### 2.4 Token Budget Impact

- Current `build_chief_writer_main_prompt()` already has 30+ injected sections across STEP 0.5-6 plus numerous context blocks
- Adding a self-audit checklist: ~200-400 tokens per candidate (3 candidates = ~600-1200 tokens total)
- Stage 4 uses Gemini context caching (`chief_writer.py` L265 per memory): prompt text changes invalidate cache, increasing cost during transition
- Marginal token cost is low, but the context-cache invalidation cost is non-trivial

### 2.5 ROI Assessment

**Arguments for restoration now:**
- Dead code proves the workspace once valued this pattern
- Stage 3 just received self-audit successfully
- 4 genuine coverage gaps exist in Self-Critique

**Arguments against restoration now:**
- Self-Critique already provides 17-category post-gen verification — the strongest mechanism in the system
- ~70% of V50 items are already covered by Self-Critique
- ROI is genuinely UNCERTAIN: in-prompt self-audit tells the LLM "verify before outputting," but Self-Critique catches the same issues POST-generation where they're concrete, not hypothetical
- In-prompt checklists in very long prompts risk being ignored by the LLM (attention dilution on a prompt that already has 30+ sections)
- Blast radius is MEDIUM: the Stage 4 writer prompt is the most sensitive surface — all manuscript generation flows through it
- Attribution is HARD: separating in-prompt checklist effect from Self-Critique effect in a canary is nearly impossible
- No canary evidence exists yet from the Stage 3 self-audit wave (just closed today) — waiting for that signal first would make the Stage 4 decision materially better-informed
- The prior survey report (`pre-director-self-audit-stagewise-survey-report.md` Section 9, Rank 2) already assessed Stage 4 self-audit ROI as UNCERTAIN and recommended deferral

### 2.6 Blast Radius

- `chief_writer_prompts.py` `build_chief_writer_main_prompt()` is the single most impactful prompt surface in the system
- Every manuscript candidate (3 per episode) sees this prompt
- Prompt changes affect context cache validity (Gemini API, 600s TTL)
- Incorrect self-audit items could cause the LLM to over-correct (worse than no checklist)
- Testing requires live LLM runs — unit tests can verify presence but not behavioral effect

## 3. Verdict Reasoning

1. **Self-Critique already compensates strongly.** 17 check categories with up to 3 LLM rounds is the deepest self-audit in the system. The V50 checklist covered fewer items.

2. **Wait for Stage 3 canary signal.** Stage 3 self-audit was just closed today. If Stage 3 self-audit shows positive canary signal, the same pattern for Stage 4 becomes more credible. If it doesn't, investing in Stage 4 self-audit becomes even more questionable.

3. **Attribution is nearly impossible.** With Self-Critique running post-generation, any quality improvement from an in-prompt checklist cannot be cleanly attributed. This violates the workspace's single-culprit-first operating rule.

4. **The genuine gaps are moderate, not urgent.** High Impact Zone density, dialogue count, and sensory description are nice-to-have verifications, but the LLM already receives these instructions via STEP 1-6 and the blueprint scene breakdown.

5. **Confidence: 97%.** This is a clear defer decision, not a marginal one.

## 4. Mandatory Final Lines

- Lane verdict: later after canary
- Best bounded next wave from this lane: Stage 4 in-prompt self-audit checklist insertion (after Stage 3 canary confirms self-audit ROI pattern)
- Should Codex open an execution SSOT from this lane now: no
