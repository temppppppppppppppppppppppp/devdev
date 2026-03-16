# Legacy Manuscript Contradiction Synthesis Master Report

Date: 2026-03-16
Status: final
Canonical Path: `docs/2026-03-16/legacy-manuscript-contradiction-synthesis-master-report.md`
Source Docs:
- `docs/2026-03-16/manuscript-contradiction-audit-opus-revalidation.md`
- `docs/2026-03-16/legacy-real-manuscript-contradiction-survey.md`
- `docs/2026-03-16/legacy-manuscript-current-recurrence-supplemental-survey.md`
- `docs/2026-03-16/legacy-manuscript-contradiction-manual-survey-and-current-risk-assessment.md`
- `docs/2026-03-16/legacy-manuscript-fresh-run-post-run-merge-audit.md`
Commit State:
- Baseline Commit: `d6c81c1976d9812d447c2a78e2aeb36f7aed666a`
- Baseline Dirty Summary: `dirty: runtime/stage modules and tests, desktop package/icon/version files, project 0/000 artifacts and db, OPUS manuscript docs, and untracked 2026-03-16 survey docs`
- Resume Commit: `d6c81c1976d9812d447c2a78e2aeb36f7aed666a`
- Resume Drift Summary: `same commit; fresh run artifacts and db rows changed in projects/0 and projects/000, so post-run merge evidence superseded earlier static-only live inference`
Confidence: `98%`

## 1. Intent

Collapse the broad OPUS contradiction audit package, the higher-authority real-manuscript/current-code surveys, and the fresh post-run merge audit into one operational truth set.

This report decides:

- what remains authoritative
- what is demoted to memo-only
- what is strong enough to drive one execution SSOT now

## 2. Source Hierarchy

The authority order is:

1. completed fresh live evidence plus real Stage 4 final/patched artifacts, DB `manuscripts`, and DB `stage_attempts`
2. live current code and targeted tests
3. manual survey method and risk framing
4. OPUS broad contradiction package

Anything contradicted by a higher layer is downgraded automatically.

## 3. Merged Findings

### 3.1 Final-authority manuscript truth

The highest-authority manuscript outcome remains stable:

- in the bounded real-project set, no `surviving hard contradiction` was confirmed in the final/patched authority manuscripts
- multiple contradiction candidates were real at candidate or pre-fix stage, but were closed by patch or reselection before publication

That means the earlier OPUS broad contradiction counts cannot be promoted as if they all survived into final authority.

### 3.2 Confirmed issue class after fresh-run merge

One issue class survives all cross-check layers, but it is narrower after fresh-run merge:

- `stale metadata authority after patch`

Current merged judgment:

- historically confirmed: `projects/00_260315 ep4-5`
- fresh bounded live reproduction: not reproduced in `projects/0`
- fresh control interpretation: `projects/000` startup-only run did not add new manuscript evidence, and its persisted real production rows remained aligned
- surviving operational risk: authority-contract ambiguity, consumer misread, and legacy stale-row handling

So the promoted lane is no longer "fix a currently reproduced fresh-run drift bug." It is "formalize final-authority semantics, harden consumers, and bound legacy stale-row handling."

### 3.3 Bounded but not execution-promoted classes

The following classes remain plausible, but are not strong enough yet to drive code changes from this synthesis alone:

- numeric carryover drift
- title / identity drift
- relationship drift
- event-repeat / event-state carryover drift
- long-lookback continuity loss

Reason:

- the OPUS package still supplies watchlist value
- current code still has advisory-first continuity seams
- but neither the bounded real-manuscript survey nor the fresh post-run merge audit confirmed these as surviving final-authority defects

They stay as watchlist items, not execution scope.

## 4. Promotion Matrix

| Class | OPUS package | Real final-authority survey | Fresh-run / current recurrence | Promotion |
| --- | --- | --- | --- | --- |
| final hard contradiction in published text | broad candidate support | not confirmed in real final authority | bounded by stronger fail-closed checks | no |
| stale metadata authority after patch | not directly isolated | confirmed historically | fresh run non-reproduced; consumer misread and legacy stale rows still real | yes, narrowed |
| numeric continuity drift | supported as lead list | mostly resolved-by-patch in real set | still plausible upstream | watchlist |
| title / identity drift | supported as lead list | not confirmed in bounded final authority | plausible | watchlist |
| event continuity drift | supported as lead list | mostly resolved or low-authority | plausible | watchlist |

## 5. What Gets Demoted

Demote the following to memo-only:

- package-wide contradiction totals from the OPUS audit
- package-wide severity totals
- package-wide `code-fixable` percentages
- remediation order derived from mixed real + archival + proof + test surfaces
- the earlier static-only claim that stale metadata drift remained actively reproduced on fresh/live surfaces

Keep the following:

- contradiction taxonomy
- historical candidate watchlist
- project pointers for future manual re-read work

## 6. Execution Consequence

The synthesis still produces exactly one execution-worthy lane:

- `legacy manuscript authority sink alignment hardening`

That lane now exists to:

- make final authority explicit after patch/finalization
- stop operators, analyzers, and future survey code from treating `director_selections` as standalone final truth
- define how legacy stale rows are surfaced, backfilled, or explicitly marked historical

The lane is not justified by a freshly reproduced hash-drift bug on active bounded runs. It is justified by:

- historically confirmed stale rows
- current consumer-interpretation risk
- live evidence showing that active surfaces are aligned but still need an explicit authority contract

Everything else remains out of execution scope until higher-authority real-manuscript evidence justifies it.

## 7. Final Conclusion

The merged truth is narrower than the raw OPUS package and narrower than the earlier static-only synthesis:

- the real risk is not a broad field of surviving final-manuscript contradictions
- the real confirmed risk is `authority sink misread after patch`, plus pre-existing legacy stale rows
- the latest bounded fresh run did not reproduce stale content-hash drift on active surfaces
- the right next document remains one narrow execution SSOT, framed as contract hardening and legacy-row handling rather than a reproduced live-defect fix
