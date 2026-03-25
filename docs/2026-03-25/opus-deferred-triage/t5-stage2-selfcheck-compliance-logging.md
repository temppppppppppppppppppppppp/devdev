# T5. Stage 2 Self-Check Compliance Logging — Triage Report

Date: 2026-03-25
Status: final
Document Type: triage lane report
Canonical Path: `docs/2026-03-25/opus-deferred-triage/t5-stage2-selfcheck-compliance-logging.md`
Lane: T5 of 7
Source Order: `docs/2026-03-25/deferred-followups-yesno-triage-7terminal-master-order.md`

## 1. Lane Question

Is Stage 2 self-check compliance logging worth a wave now, or should it stay deferred?

## 2. Findings

### 2.1 Three Self-Check Systems Exist And Are Active

Stage 2 arc generation injects three independent self-check systems into the LLM prompt:

**A. ConstraintCompiler SELF-CHECK**
- `modules/domain/agents/constraint_compiler.py:378-389`
- Section 4: VERIFICATION CHECKLIST — 5 checkbox items
- Items: forbidden-item check, start-location match, start-equipment match, re-acquisition phrasing, duplicate grants
- Injected via `compile_constraints()` into every arc generation attempt

**B. NegativeExampleInjector self-check**
- `modules/domain/agents/negative_example_injector.py:353-370`
- `generate_self_check_prompt()` → 8-item checklist
- Call sites: `four_phase_arc_generator.py:833`, `four_phase_arc_runtime.py:722`
- Both call sites are live and injected into the full constraint block

**C. ConstitutionalChecker arc constitution**
- `modules/core/constitutional_checker.py:213-275`
- ARC_CONSTITUTION: 6 articles (A1-A6) with severity markers (CRITICAL/HIGH/LOW)
- Wired via `stage2_preflight_runtime.py:272-277` → analyst prompt

### 2.2 Zero Compliance Logging Exists

After exhaustive search, no downstream compliance capture was found:

- **LLM output parsing** (`four_phase_arc_generator.py:662,679`): `_extract_json_robust()` extracts JSON but does not check whether self-check items were honored
- **arc_draft_validator.py**: advisory mode, Python pattern matching only — no self-check compliance field in its result dict
- **unified_arc_validator.py**: validates for CRITICAL contradictions, does not attribute findings to self-check items
- **runtime_audit.jsonl**: no `self_check_compliance` entry type exists
- **stage2_orchestrator.py**: no self-check verification at stage completion
- **audit_service.py**: generic audit buffering, no self-check-specific instrumentation
- **DB schema**: no self-check compliance field in any table

The validation result object from `arc_draft_validator.py` returns `{valid, score, critical_issues, warnings}` — there is no `self_check_passed` or `self_check_issues` field.

### 2.3 Implicit Coverage Already Exists Through Python Validation

Although no explicit self-check compliance logging exists, the Python validation layer already catches most of the same issues the self-checks target:

- Forbidden-item usage → caught by `constraint_compiler.py` forbidden-list checks
- Location mismatch → caught by `unified_arc_validator.py` continuity checks
- Duplicate acquisition → caught by `arc_draft_validator.py` pattern matching
- Tactical-doc scope violations → caught by prevalidation

The self-check prompts reinforce the LLM's behavior, but the Python-side validation is the operational gate. Compliance logging would tell us *whether the LLM self-corrected before submission*, but the Python gate already catches violations regardless.

### 2.4 Operator Decision Impact Assessment

Would explicit self-check compliance logging change any operator decision today?

- **Retry decisions**: governed by Python validation score and Director verdict, not self-check compliance
- **Quality-risk routing**: governed by `quality_risk` flag from prevalidation, not self-check state
- **Prompt tuning decisions**: could theoretically benefit from knowing compliance rates, but this is a development-time signal, not an operational one
- **Canary interpretation**: canary triage uses artifact truth and runtime_audit patterns — self-check compliance is not currently in the evaluation surface

No current operator workflow depends on self-check compliance data. Adding it would create a new observability channel without an existing consumer.

### 2.5 Blast Radius

- **If implemented**: requires adding a post-extraction compliance check in the arc generation path, a new field in the validation result dict, a new runtime_audit entry type, and possibly a DB column
- **Files touched**: `four_phase_arc_generator.py`, `four_phase_arc_runtime.py`, `arc_draft_validator.py` or a new compliance checker, `audit_service.py`
- **Risk**: LOW per file, but the aggregate blast radius is MODERATE (4+ files across the Stage 2 generation pipeline)
- **Token overhead**: minimal (compliance check is string matching, not LLM call)

### 2.6 ROI Assessment

| Dimension | Rating | Reasoning |
|-----------|--------|-----------|
| Quality impact | NONE | Python validation already gates; compliance logging does not change what passes/fails |
| Operator decision change | NONE | No current workflow consumes this signal |
| Development insight | LOW | Useful for prompt-tuning but not urgent |
| Blast radius | MODERATE | 4+ production files in the arc generation hot path |
| Attribution cost | LOW | Easy to attribute in canary |
| Net ROI | LOW | Observability-only improvement with no existing consumer |

## 3. Comparison With Other Deferred Lanes

The pre-director self-audit survey (§7.3) already assessed this as:
- Blast radius: MINIMAL
- ROI: LOW — "Stage 2 already has the best coverage; logging compliance is observability, not quality"

The self-audit wave execution SSOT (§5 Class B) deferred this as:
- "Stage 2 self-check compliance logging → low ROI, defer"

This triage confirms both prior assessments with live code evidence.

## 4. Verdict Reasoning

**Against `yes now`:**
- No operator decision would change from having this data
- Stage 2 already has the strongest self-audit surface (3 systems, all active)
- Python validation already covers the same violation categories
- The wave would touch 4+ production files with zero quality-gate improvement

**Against `later after canary`:**
- There is no canary observation that would change this assessment. Self-check compliance logging is a structural observability choice, not something a canary reveals. Either we want this signal or we don't — and currently no workflow consumes it.

**For `no`:**
- This is observability for a surface that already works. The three self-check systems influence LLM behavior, and the Python validation layer catches violations independently. Logging the intermediate compliance step adds data without adding decisions.
- If a future wave identifies a specific prompt-tuning need that requires knowing compliance rates, it can be reopened with a concrete consumer. But opening it speculatively is not justified.

## 5. Final Lines

Lane verdict: no
Best bounded next wave from this lane: none
Should Codex open an execution SSOT from this lane now: no
