# writer-template-opening-anchor-semantics-3pass-audit

Date: 2026-03-19
Status: final
Confidence: `0.95`
Canonical Path: `docs/2026-03-19/writer-template-opening-anchor-semantics-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `dirty: large active worktree; git status --short count = 112`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-19/opus-modification-governing-3pass-reaudit.md`
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
Evidence Basis:
- `modules/core/writer_template.py`
- `tests/test_v55_modules.py`
- `tests/test_chief_writer.py`
Scope:
- audit whether `WriterTemplate` opening-anchor slices are accidental truncation or intentional opening-link semantics
- determine whether `prev_ending[-300:]` and `manuscript[:600]` should be treated as policy boundaries
- add direct regression coverage if the current semantics are judged intentional
- non-goal: redesign writer opening policy or modify runtime logic

---

## Pass 1. Structure and Scope

This audit is narrow.

It covers only `modules/core/writer_template.py` behavior around:
- how `opening_anchor` is built from the previous episode ending
- how `validate_against_template()` checks whether the current manuscript opening reconnects to that anchor

It does not cover:
- ChiefWriter generation strategy
- Stage 4 patch-mode behavior
- general prompt-budget truncation

Key operator question:
- is `prev_ending[-300:]` plus `manuscript[:600]` a bug-shaped slice, or an intentional opening-link rule?

---

## Pass 2. Evidence and Consistency

### 1. Live code treats this as opening structure, not generic truncation

The code is explicit.

Observed live behavior:
- `ManuscriptTemplate.opening_anchor` is documented as `직전 화 연결 앵커`
- `generate_template()` sets `opening_anchor=prev_ending[-300:] if prev_ending else ""`
- `validate_against_template()` extracts anchor keywords from that anchor
- it then checks only `opening_part = manuscript[:600]`
- if those keywords do not appear in the opening portion, it warns `직전 화와의 연결이 약함`

Why this matters:
- this is not an LLM prompt budget path
- this is a structural rule about whether the new episode opening reconnects to the previous ending
- the choice of `tail of previous ending` and `opening of current manuscript` matches that rule directly

Conclusion:
- this is policy-shaped code
- blanket conversion to tail-preserving or full-manuscript scan would change what the rule means

### 2. Existing tests covered `WriterTemplate` broadly, but not this policy boundary directly

Before this audit, `tests/test_v55_modules.py` covered:
- template generation
- slot typing
- prompt injection
- general validation shape

What it did not directly freeze:
- that `opening_anchor` intentionally keeps the tail of `prev_ending`
- that validation intentionally looks only at the first `600` characters of the current manuscript

Supporting neighboring evidence:
- `tests/test_chief_writer.py` already treats `opening` and `ending` as distinct structural patch targets
- that is consistent with `WriterTemplate` enforcing opening-specific linkage rather than whole-manuscript fuzzy matching

### 3. Direct regression coverage added in this audit

New regression coverage now fixes current semantics into contract:
- `generate_template()` keeps the tail of `prev_ending` for `opening_anchor`
- `validate_against_template()` warns when anchor terms appear only after the first `600` characters
- `validate_against_template()` does not warn when anchor terms appear within the first `600` characters

Rerun evidence:
- `python -m pytest tests/test_v55_modules.py -k "opening_anchor or test_validation or test_generate_template" -q`
- `python -m pytest tests/test_v55_modules.py -q`

Conclusion:
- there is now direct regression coverage for this opening-link policy boundary

---

## Pass 3. Operational Meaning and Next Step

### Final judgment

1. `WriterTemplate` opening-anchor behavior should be kept as-is unless there is an explicit policy decision to redefine what counts as "opening reconnection".

2. `prev_ending[-300:]` is intentional.
It captures the immediate tail of the previous ending, which is the right local source for an opening carry-over anchor.

3. `manuscript[:600]` is also intentional.
It checks whether the reconnection happens in the opening, not somewhere later in the episode.

### Safe operating rule from this audit

Do:
- keep the current `prev_ending[-300:]` anchor model
- keep the current `opening 600 chars` validation window
- treat future changes here as opening-structure policy work

Do not:
- classify this as another generic truncation cleanup target
- replace the opening window with whole-manuscript search without an explicit policy rewrite

### Recommended next actions

1. Keep this area in the same `keep unless policy rewrite` bucket as continuity opening-window semantics.
2. If opening-anchor policy is ever revised, decide separately:
   - anchor source length
   - opening validation window
   - keyword extraction heuristic
3. Preserve the new regression tests before any such change.

### Audit result

- runtime code change: not needed
- regression hardening: completed
- documentation conclusion: opening-anchor slices are intentional structure semantics, not low-risk truncation defects
