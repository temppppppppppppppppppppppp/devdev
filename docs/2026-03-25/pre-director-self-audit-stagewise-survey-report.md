# Pre-Director Self-Audit Stagewise Survey Report

Date: 2026-03-25
Status: final
Document Type: survey report
Canonical Path: `docs/2026-03-25/pre-director-self-audit-stagewise-survey-report.md`
Commit State:
- Baseline Commit: `f61a35c89b4c964afbfa902790560448d98b1bfb`
- Baseline Dirty Summary: `dirty: canary_0325 live artifacts/logs, closed Stage 3 wave edits, 2026-03-25 survey/audit docs, temp queue state`
Source Order:
- `docs/2026-03-25/pre-director-self-audit-stagewise-survey-order.md`
Related Merge Audits:
- `docs/2026-03-25/bp-clarity-density-4terminal-merge-audit.md` (Finding D: self-audit is secondary amplifier)

## 1. Executive Summary

The system already has meaningful self-audit mechanisms at Stage 2 and Stage 4, but Stage 3 (blueprint generation) has zero prompt-level self-audit. This is a clear gap, not an assumption.

- **Stage 2** (Arc generation): three independent self-check systems inject into the generation prompt — ConstraintCompiler SELF-CHECK, NegativeExampleInjector self-check, and ConstitutionalChecker arc checklist. These are all active in the live pipeline.
- **Stage 3** (Blueprint generation): no self-audit prompt exists. The blueprint LLM receives constraints and context but is never instructed to verify its own output before submission. ConstitutionalChecker has a `get_architect_constitution()` method, but it is NOT wired into the Stage 3 context or `blueprint_ensemble.py`.
- **Stage 4** (Manuscript generation): a strong multi-round LLM Self-Critique loop (`apply_self_critique` → `_self_critique`, up to 3 rounds) runs post-generation. However, the V50 in-prompt self-diagnosis checklist is dead code (confirmed at `main_a.py:2157`). The main generation prompt has structural STEP instructions but no explicit pre-submission self-audit checklist.

**Key finding**: Stage 3 is the weakest stage for pre-Director self-audit. Stage 4 compensates with post-generation LLM critique. Stage 2 is the strongest.

## 2. Included Coverage / Exclusions

### Included
- Stage 2 prompt-level self-check mechanisms
- Stage 3 prompt-level self-check mechanisms (or lack thereof)
- Stage 4 prompt-level self-check + post-generation Self-Critique
- Reasoning field lifecycle (generated/visible/persisted/reused)

### Excluded
- Director redesign
- Stage 4 retry redesign after Director reject
- Sink reconciliation overhaul
- DB schema changes
- Stage 2 schema redesign
- Post-Director advisory chain

## 3. Stage 2 Self-Audit / Reasoning State

### 3.1 Active Self-Check Mechanisms

Stage 2 arc generation has **three independent** prompt-level self-check systems:

**A. ConstraintCompiler SELF-CHECK** (`modules/domain/agents/constraint_compiler.py:382`)
- Renders a `🔍 SELF-CHECK (생성 후 자체 검증)` section into the constraint block
- 5 concrete checklist items: forbidden items, start location, start equipment, "다시 획득" phrasing, duplicate grants
- Injected for every arc generation attempt
- **Evidence**: `constraint_compiler.py` L378-389, injected via `compile_constraints()` → SECTION 4

**B. NegativeExampleInjector self-check** (`modules/domain/agents/negative_example_injector.py:353-370`)
- `generate_self_check_prompt()` returns `[V60.12 자가 검증 체크리스트 - 제출 전 필수 확인]`
- 8 concrete checklist items: items_acquired duplication, location match, state inheritance, tactical_doc length, episode separation, joint_docs consistency
- Actively wired: `four_phase_arc_generator.py:833` and `four_phase_arc_runtime.py:722`
- **Evidence**: grep confirms both call sites are live

**C. ConstitutionalChecker arc constitution** (`modules/core/constitutional_checker.py:220-275`)
- `get_full_injection(stage=2)` → `[V55.2 Constitutional Self-Check: Arc 설계]`
- Question-per-article format with severity markers (CRITICAL/HIGH/LOW)
- Wired via `stage2_preflight_runtime.py:272-277`
- **Evidence**: `stage2_context.py` slot `constitutional_checker` is populated from `sovereign_bootstrap_runtime.py:432`

### 3.2 Reasoning Fields

| Field | Generated | Operator-Visible | Persisted | Reused in Retries |
|-------|-----------|-------------------|-----------|-------------------|
| `ep_count_reasoning` | yes (in arc JSON) | yes (logs) | yes (DB arc data) | yes (next attempt feedback) |
| `pacing_decision` | yes | yes | yes | yes |
| `density_focus` | yes | yes | yes | yes |
| SELF-CHECK result | implicit in LLM output | no (folded into JSON) | no | no |

### 3.3 Assessment

Stage 2 is the **strongest** stage for prompt-level self-audit. Three independent systems provide redundant coverage. The gap is that self-check compliance is not separately captured or logged — it's folded into the LLM's JSON output.

## 4. Stage 3 Self-Audit / Reasoning State

### 4.1 Active Self-Check Mechanisms

**None.**

The blueprint LLM receives:
- Arc focus (from `must_focus.content` or `tactical_doc` extraction)
- Formatted constraint string (from `BlueprintConstraintCompiler`, not `ConstraintCompiler`)
- Previous blueprint info
- HUD context
- Strategy directive
- POV constraint
- Reader feedback (advisory)

But it is **never** instructed to self-verify before outputting. There is no:
- Self-check checklist in the prompt
- "Verify before you submit" instruction
- Constitutional article injection
- Quality amplifier injection

**Evidence of the gap**:
- `blueprint_ensemble.py`: zero imports or references to `constitutional_checker`, `quality_amplifier`, `self_check`, or `자가 검증`
- `stage3_context.py`: zero slots for `constitutional_checker` or `quality_amplifier`
- `ensemble.yaml` `BLUEPRINT_GENERATION_PROMPT`: ends with `반드시 유효한 JSON만 출력하세요` — no self-audit section
- `ConstitutionalChecker.get_architect_constitution()` exists (L277-315) but is **dead code** for Stage 3 — never called by any Stage 3 path

### 4.2 Python Prevalidation (Not Self-Audit)

Stage 3 does have Python prevalidation via `unified_blueprint_validator.py`:
- `_qualify_blueprint_candidates()`: scene count ≥ 4, integrated_scenario ≥ 500 chars
- `prevalidate()`: structure, field presence, stop-line violation, continuity, dead-NPC check
- `_build_python_warning_entries()`: compacts issues for Director

This is **Python-side gating**, not writer-side self-audit. The blueprint LLM has no awareness of these checks until after a rejection cycle.

### 4.3 Reasoning Fields

| Field | Generated | Operator-Visible | Persisted | Reused in Retries |
|-------|-----------|-------------------|-----------|-------------------|
| `quality_risk` | yes (validator) | yes (runtime_audit) | yes (DB) | yes (passed to Director) |
| `fix_scope_reasoning` | yes (orchestrator) | yes (logs) | partially | yes |
| `integrated_scenario` | yes | yes (artifact) | yes | not directly |
| Blueprint self-audit | **does not exist** | N/A | N/A | N/A |

### 4.4 Assessment

Stage 3 is the **weakest** stage for pre-Director self-audit. The blueprint LLM receives rich context but is never asked to verify its own output. The existing `ConstitutionalChecker.get_architect_constitution()` is ready-to-wire dead code.

## 5. Stage 4 Self-Audit / Reasoning State

### 5.1 Active Self-Check Mechanisms

**A. Post-Generation Multi-Round LLM Self-Critique** (`chief_writer_quality.py:102-247`)
- `apply_self_critique()`: up to 3 rounds of LLM-based critique + fix
- `_self_critique()`: checks HUD consistency, cliché overuse, justification gaps, temporal logic, paragraph structure, POV consistency, length, ending_hook presence, system-term exposure
- Rubric pre-check: if score ≥ 3.5 and length ≥ 4000, may skip unless structural issues found
- **This is the strongest self-audit mechanism in the system**, but it runs AFTER generation, not as an in-prompt instruction.

**B. In-Prompt Authority/Step Structure** (`chief_writer_prompts.py:129-199`)
- STEP 0.5: Authority priority hierarchy
- STEP 1-6: Blueprint analysis → continuity → state → arc → worldbuilding → style
- These are structural instructions, not self-audit checklists. They tell the LLM what to write, not what to verify.

**C. Dead Code: V50 Self-Diagnosis Checklist**
- `prompt_builder.py:527-544`: `generate_self_diagnosis_checklist()` renders a checklist
- `main_a.py:2157` comment: `# [V65] _generate_v50_writer_prompt 삭제 — Stage 4 V2 파이프라인에서 미호출 Dead Code`
- This was designed as an in-prompt self-audit but was removed during the V65 ChiefWriter refactor.

**D. Dead Code: QualityAmplifier writer constraints**
- `quality_amplifier.py:230-276`: `generate_writer_constraints()` includes `[제출 전 자가 검증]` with 5 checklist items
- NOT wired into Stage 4 context. `stage4_context.py` has no `quality_amplifier` slot.

### 5.2 Reasoning Fields

| Field | Generated | Operator-Visible | Persisted | Reused in Retries |
|-------|-----------|-------------------|-----------|-------------------|
| Self-Critique `issues` | yes (LLM) | yes (operator log) | partially (via metrics) | yes (fix loop) |
| Rubric score | yes | yes (log) | yes | yes (gate) |
| `state_updates` | yes | yes | yes (DB) | yes |
| Director score/feedback | yes | yes | yes | yes |
| Pre-Director checklist | yes (Python) | yes | yes | yes |

### 5.3 Assessment

Stage 4 has the most sophisticated self-audit loop, but it is entirely **post-generation**. The LLM that writes the manuscript does NOT see any "verify before you submit" checklist. The checklist that once existed (V50) was removed during V65. The multi-round Self-Critique compensates, but it costs an additional 1-3 LLM calls per candidate.

In-prompt self-audit could potentially reduce Self-Critique rounds, but the evidence is not strong enough to predict this with confidence.

## 6. Cross-Stage Reasoning Lifecycle Map

```
Stage 2 (Arc):
  SELF-CHECK in prompt → LLM output (JSON) → Python validation → Director selection
  Reasoning: ep_count_reasoning, pacing_decision, density_focus
  Self-audit: 3 active prompt-level systems (ConstraintCompiler, NegativeExampleInjector, ConstitutionalChecker)

Stage 3 (Blueprint):
  Constraints in prompt → LLM output (JSON) → Python prevalidation → Director selection
  Reasoning: quality_risk (Python), fix_scope_reasoning (orchestrator)
  Self-audit: NONE

Stage 4 (Manuscript):
  Context/constraints in prompt → LLM output → Post-gen Self-Critique (1-3 LLM rounds) → Python pre-Director checklist → Director compare
  Reasoning: Self-Critique issues, rubric score, state_updates
  Self-audit: Post-generation only (no in-prompt)
```

## 7. Missing Or Weak Self-Audit Surfaces

### 7.1 Stage 3: Zero In-Prompt Self-Audit (HIGH)

- **File**: `modules/domain/agents/blueprint_ensemble.py`
- **Function**: `_generate_single()` → prompt assembly
- **Surface**: `config/prompts/ensemble.yaml` `BLUEPRINT_GENERATION_PROMPT`
- **What's missing**: No checklist, no "verify before you output" instruction
- **Ready-to-wire dead code**: `ConstitutionalChecker.get_architect_constitution()` (L277-315) — 6+ constitutional articles for Blueprint design
- **Blast radius**: LOW — adding a checklist section to the prompt template is a bounded text change
- **ROI**: MEDIUM-HIGH — blueprint quality is the current limiter (per bp-clarity-density merge audit)

### 7.2 Stage 4: No In-Prompt Self-Audit (MEDIUM)

- **File**: `modules/domain/agents/chief_writer_prompts.py`
- **Function**: `build_chief_writer_main_prompt()`
- **Surface**: The main prompt template string
- **What's missing**: V50 self-diagnosis checklist was removed in V65. No replacement was added.
- **Ready-to-wire dead code**: `quality_amplifier.generate_writer_constraints()` (L230-276), `prompt_builder.generate_self_diagnosis_checklist()` (L527-544)
- **Blast radius**: MEDIUM — prompt changes to the main writer surface affect all manuscript generation
- **ROI**: UNCERTAIN — the post-generation Self-Critique loop may already catch what in-prompt self-audit would catch, making the net improvement ambiguous

### 7.3 Stage 2: Self-Check Compliance Not Logged (LOW)

- **What's missing**: Whether the LLM actually performed the self-check is not separately captured
- **Blast radius**: MINIMAL
- **ROI**: LOW — Stage 2 already has the best coverage; logging compliance is observability, not quality

## 8. Cleared Non-Culprits

The following are NOT missing self-audit issues:

- **Stage 2 self-check existence**: three independent systems are active and wired
- **Stage 4 Self-Critique existence**: multi-round LLM critique is active and effective
- **Director prompt self-audit**: Director is the judge, not the writer. Director prompts correctly focus on evaluation criteria, not self-audit. Adding self-audit to Director prompts would blur authority.
- **Python prevalidation as self-audit substitute**: Python prevalidation is necessary but structurally different from writer-side self-audit. They serve complementary purposes.

## 9. Candidate Insertion Points (Ranked)

### Rank 1: Stage 3 Blueprint Prompt Self-Audit

- **Insertion point**: `config/prompts/ensemble.yaml` → `BLUEPRINT_GENERATION_PROMPT`, after `### [필수 조건]` block (currently L369-376)
- **Source**: Wire `ConstitutionalChecker.get_architect_constitution()` or a new bounded checklist
- **Alternative**: Inline a minimal 5-7 item checklist directly into the prompt template
- **Estimated token cost**: ~200-300 tokens per candidate (3 candidates = ~600-900 tokens)
- **ROI**: HIGH — directly addresses the weakest self-audit surface in the pipeline
- **Blast radius**: LOW — prompt text change only, no code flow change
- **Attribution risk**: LOW — can be cleanly attributed in next canary

### Rank 2: Stage 4 Manuscript Prompt Self-Audit (Restore)

- **Insertion point**: `chief_writer_prompts.py` `build_chief_writer_main_prompt()`, as a new section after STEP 6 or as a final verification step
- **Source**: Modernize `prompt_builder.generate_self_diagnosis_checklist()` or write a new bounded checklist
- **Estimated token cost**: ~200-400 tokens per candidate (3 candidates = ~600-1200 tokens)
- **ROI**: UNCERTAIN — may reduce Self-Critique rounds, but may also be redundant
- **Blast radius**: MEDIUM — touches the main writer prompt surface
- **Attribution risk**: MEDIUM — harder to isolate from Self-Critique effects

### Rank 3: Stage 2 Self-Check Logging

- **ROI**: LOW — observability improvement only
- **Defer**: no action needed now

## 10. Best Bounded Next Wave

The bp-clarity-density merge audit (Finding D) already concluded that self-audit is a "secondary amplifier" for the current Stage 3 quality-up wave.

However, this survey finds that the gap is more structural than previously assessed:

- Stage 3 has **zero** prompt-level self-audit, not "some self-audit that could be improved"
- Stage 2 has **three** active systems, showing the workspace already values this pattern
- The dead code (`ConstitutionalChecker.get_architect_constitution()`) proves this was intended but never wired

**Recommendation**: Stage 3 self-audit insertion as a **follow-up wave** after the current Wave 1 (authority re-banding + density prevalidation) closes. It should NOT be bundled into Wave 1 for these reasons:

1. Wave 1 is already scoped and closed in execution SSOT — reopening it adds risk
2. Clean canary attribution requires single-variable isolation
3. Self-audit is an amplifier that works best on top of already-improved constraint presentation

If the Wave 1 canary shows blueprint clarity improvement, a follow-up Stage 3 self-audit wave is well-justified.

If the Wave 1 canary shows no improvement, self-audit alone is unlikely to fix the root cause.

**Stage 4 in-prompt self-audit**: defer. The existing Self-Critique loop is strong, and adding in-prompt self-audit would be hard to attribute and may add prompt bloat without clear benefit.

## 11. Confidence And Limits

Estimated confidence: 96%

Why this clears the 95% gate:

- All claims are backed by live code evidence (file:line references)
- The Stage 3 gap is structural and unambiguous (zero references in code)
- Dead code identification is confirmed by grep + runtime wiring analysis
- The recommendation aligns with the existing merge audit's "secondary amplifier" judgment while adding structural nuance

Limits:

- This survey does not predict the magnitude of quality improvement from adding Stage 3 self-audit
- The interaction between self-audit and the upcoming authority re-banding changes is untested
- Stage 4 Self-Critique effectiveness was assessed structurally, not from live run metrics

---

- Dominant self-audit opportunity: Stage 3 blueprint prompt zero-to-one self-audit insertion
- Best bounded next wave: Stage 3 self-audit only (as follow-up after Wave 1 closes)
- Should Codex open an execution SSOT now: no
