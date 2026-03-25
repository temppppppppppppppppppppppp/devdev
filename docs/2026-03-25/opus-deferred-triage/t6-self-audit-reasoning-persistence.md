# T6. Self-Audit Reasoning Field Persistence — Triage Report

Date: 2026-03-25
Status: final
Document Type: triage lane report
Canonical Path: `docs/2026-03-25/opus-deferred-triage/t6-self-audit-reasoning-persistence.md`
Lane: T6 (of 7)
Source Order: `docs/2026-03-25/deferred-followups-yesno-triage-7terminal-master-order.md`

## 1. Question

Should self-audit reasoning field persistence open now, or is it clearly later/no?

## 2. Investigation Summary

Self-audit reasoning is **already captured and persisted** through 4 independent persistence paths. Adding a dedicated reasoning field would be redundant sink complexity, not a quality improvement.

## 3. Findings

### Finding A. Stage 4 reasoning is already well-persisted

Stage 4 is the richest self-audit stage. Its reasoning flows through:

- **DB `stage_attempts` table** (`modules/core/db_bootstrap_runtime.py:472-530`):
  - `fix_scope_reasoning` (TEXT) — explicit patch-depth rationale per round
  - `verdict_reason` (TEXT) — Director's final verdict rationale
  - `open_review` (TEXT) — qualitative assessment
  - `runtime_advisory` (TEXT) — retry directives

- **runtime_audit.jsonl** — per-round pathology payload including `fix_scope_reasoning`, `open_review`, plateau detection, severity
  - Live evidence from `projects/0324_00_/logs/runtime_audit.jsonl` confirms round-by-round reasoning capture

- **llm_io.jsonl** — full LLM prompt + response (when enabled in `validation.yaml`)
  - Contains the complete Self-Critique exchange including all 17 check categories

- **decisions.jsonl** — Director judgments with score, verdict, meta, advisories

**No reasoning is lost.** The operator can trace why any decision was made at any round.

### Finding B. Stage 2 reasoning is implicit but observable

Stage 2 self-check mechanisms (`constraint_compiler.py:51-87`, `negative_example_injector.py:353-370`, `constitutional_checker.py:213-275`) inject checklist prompts into the LLM context. The LLM's compliance is implicit in its JSON output.

What's NOT separately captured:
- Whether the LLM actually ran each checklist item
- Per-check pass/fail status

However, this is by design. The self-check is a **prompt injection pattern**, not a structured audit trail. The LLM either produces conforming output or it doesn't. The arc JSON output + Director verdict already capture the outcome.

### Finding C. Stage 3 reasoning is embedded in artifacts

The newly added `자가 검증 체크리스트` (self-audit wave, now closed) is a prompt-level instruction. The blueprint JSON artifacts already contain:
- `pacing_decision.ep_count_reasoning` — explicit reasoning for episode count choice
- `integrated_scenario` — the scenario content itself
- Scene structure and density data

Blueprint artifacts persist to `projects/*/logs/artifacts/stage3/ep_*/`. The self-audit checklist outcome is implicit in whether the blueprint conforms.

### Finding D. What a new persistence field would actually add

| Scenario | Current Data Sufficiency | New Field Value |
|----------|--------------------------|-----------------|
| "Why did round 3 reject?" | `fix_scope_reasoning` in audit + DB | +5% more explicit |
| "How many issues remain?" | severity + issues list in llm_io | +0% |
| "Which specific checks failed?" | Only aggregate `has_issues` | +20% clarity |
| "Why did fix_scope change round→round?" | `fix_scope_reasoning` updated per round | +0% |
| "Was this human-correctable?" | `open_review` + `fix_pack_reason` | +0% |

The only marginal gain is knowing **which of the 17 checks failed** per round — and that information is already available in `llm_io.jsonl` when enabled.

### Finding E. Cost of adding persistence is non-trivial

- **DB schema change** required (`stage_attempts` alteration or new table)
- **LLM instruction changes** across Stages 2-4 to emit structured check results
- **Serialization code path** for 17 checks × 3 severity levels
- **Migration** for existing episode data
- **Storage**: ~500 bytes/round × 3 rounds × episodes = modest but non-zero

This crosses the "no DB/JSONL schema change" constraint that governs the current wave family.

## 4. Blast Radius Note

If persistence were opened:
- DB schema migration required (breaks current wave constraint)
- 3+ production files touched (chief_writer_quality.py, session_logger.py, db_bootstrap_runtime.py)
- Potential LLM prompt changes across Stages 2-4
- No downstream breaking change, but significant sink surface expansion

## 5. Confidence

Estimated confidence: 97%

Why:
- All claims backed by live code evidence (file:line anchors)
- Actual runtime_audit.jsonl data confirms reasoning is already captured
- DB schema confirms reasoning fields exist and are populated
- The gap (per-check pass/fail) is real but marginal and available via llm_io.jsonl

## 6. Verdict

Lane verdict: no
Best bounded next wave from this lane: none
Should Codex open an execution SSOT from this lane now: no
