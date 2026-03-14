# Execution Synthesis Harness

Date: 2026-03-14
Status: active
Applies To: turning one or more survey/audit/evidence inputs into an execution SSOT or roadmap
Related Documents:
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/evidence-manifest-harness.md`
- `docs/implementation/execution-ssot-template.md`
- `docs/implementation/execution-roadmap-template.md`

## 1. Purpose
- Standardize how multiple evidence inputs are collapsed into one execution-ready artifact.
- Prevent execution docs from becoming loose prose detached from the underlying survey basis.

## 2. When To Use
Use this harness when:
- more than one survey or evidence artifact informs the execution doc
- a dated survey needs to be upgraded into an execution SSOT
- multiple queued execution items share substrate and need one roadmap

## 3. Synthesis Inputs
Allowed input classes:
- survey docs
- audit docs
- evidence `.txt` / `.json` artifacts
- side-effect notes
- live code inspection findings

## 4. Synthesis Method
1. identify all candidate sources
2. discard stale or contradictory sources that are no longer authoritative
3. preserve lineage in `Source Survey Docs` and `Evidence Artifacts`
4. separate facts, inferences, and decisions
5. produce one execution shape with tranches, guardrails, and acceptance criteria

## 5. Output Rule
- one canonical execution SSOT or roadmap should cite all material inputs
- if evidence volume is large, create an evidence manifest rather than overloading the execution doc body

## 6. Guardrails
- Do not merge contradictory sources without resolving which one is current.
- Do not hide synthesis decisions; surface them in the execution doc.
- Do not create an execution doc without a traceable evidence basis.
