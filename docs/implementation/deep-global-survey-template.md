# Deep Global Survey Template

Use this template for high-rigor codebase-global survey bundles that need one master survey doc, multiple execution SSOTs, and one SSOT roadmap.

---

# <topic> Deep Global Integrity Survey

Date: YYYY-MM-DD
Status: draft | final
Canonical Path: `docs/YYYY-MM-DD/<topic>-deep-global-survey.md`
Related Evidence Manifest: `docs/YYYY-MM-DD/<topic>-evidence-manifest.md`
Roadmap Policy: `single-ssot`
Confidence Model: `docs/implementation/integrity-confidence-scoring-contract.md`
Confidence Target: 95%
Commit State:
- Baseline Commit: `<git rev-parse HEAD at survey start>`
- Baseline Dirty Summary: `clean | dirty: ...`
- Resume Commit: `same-as-baseline | <git rev-parse HEAD at re-audit or continuation>`
- Resume Drift Summary: `none | ...`

## 1. Intent
- Why this deep survey exists.
- Why lighter survey modes are insufficient.

## 2. Scope Lock
- included paths:
- excluded paths:
- change-lock or canary constraints:
- baseline docs read:

## 3. Coverage Matrix
- macro views covered:
- micro views covered:
- cross-cut views covered:
- operational views covered:
- deferred surfaces:

## 4. Macro View
- topology:
- authority map:
- runtime/control-flow spine:
- subsystem boundaries:

## 5. Micro View
- hotspot ranking:
- high-risk files/modules:
- dominant mutable state surfaces:
- dense side-effect clusters:

## 6. Cross-Cut Integrity Matrix
- include the matrix inline or reference a companion matrix doc
- required rows should cover observability, persistence, operator surface, contracts/config, recovery, subprocess/network, cache/global state, regression/canary, and stale/shadow authority

## 7. Operational and Regression View
- tests:
- smoke/canary:
- repair tooling:
- read-only vs mutation-heavy boundaries:

## 8. Contradiction and Uncertainty Ledger
- contradictions closed:
- contradictions still open:
- uncertainty items:
- confidence caps still in effect:

## 9. Severity and Action Map
- `P0` items:
- `P1` items:
- action-bearing areas:
- areas with `no-execution-doc-required`:

## 10. Execution SSOT Mapping

| Area | Classification | Canonical Execution Doc | Notes |
| --- | --- | --- | --- |
| `<area>` | action-bearing | `docs/YYYY-MM-DD/<topic>-execution-ssot.md` | `<note>` |

## 11. Single SSOT Roadmap Lineage
- canonical roadmap:
- temp roadmap mirror:
- execution order basis:
- lane or phase structure:

## 12. Confidence Summary
- estimated score:
- score rationale:
- closed gaps:
- remaining gaps:
- final statement:

---

Before final save:
- complete document 3-pass audit
- reach at least 95% confidence under the integrity confidence contract
- create canonical execution SSOTs first
- create or refresh exactly one canonical roadmap
- refresh temp mirrors
- run `python scripts/ops_validator.py --strict`
- run `python scripts/validate_deep_global_survey_bundle.py --survey-doc <canonical-survey-doc>`
