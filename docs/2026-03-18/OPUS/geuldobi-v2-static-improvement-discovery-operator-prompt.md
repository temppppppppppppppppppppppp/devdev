# Geuldobi V2 Static Improvement Discovery Operator Prompt

Date: 2026-03-18
Status: final (3-pass audited)
Audience: OPUS
Canonical Path: `docs/2026-03-18/OPUS/geuldobi-v2-static-improvement-discovery-operator-prompt.md`
Companion Order: `docs/2026-03-18/OPUS/geuldobi-v2-static-improvement-discovery-full-survey-audit-order.md`

## Paste-To-OPUS Prompt
```text
You are conducting a static-only improvement discovery audit for the Geuldobi workspace.

Read and obey this order document first:
`docs/2026-03-18/OPUS/geuldobi-v2-static-improvement-discovery-full-survey-audit-order.md`

Your mission is not to fix known bugs. Your mission is to discover non-obvious, high-leverage improvement opportunities that the user has not explicitly asked about yet.

Hard constraints:
- Do not modify any code, config, docs, tests, or artifacts.
- Do not run the app, backend, pytest, builds, migrations, or any live runtime flow.
- Do not create execution SSOTs, execution roadmaps, or execution closures.
- Do not use external web research.
- Use only static inspection of the local workspace and existing logs/artifacts.

Priority:
- unknown unknown improvements over known issue restatement
- evidence-backed claims over speculation
- structural/operator/observability/process improvements, not just refactor ideas

Required outputs:
1. `docs/2026-03-18/OPUS/geuldobi-v2-static-improvement-discovery-evidence-manifest.md`
2. `docs/2026-03-18/OPUS/geuldobi-v2-static-improvement-discovery-3pass-audit.md`

Minimum bar:
- at least 12 evidence-backed opportunities
- at least 5 non-obvious or counterintuitive opportunities
- at least 3 operator/process/observability opportunities
- every opportunity must include why it is non-obvious, evidence anchors, upside, tradeoff, confidence, and next verification

Method:
- build an authority map first
- audit contract drift across schema/model/prompt/validator/sink
- mine existing logs and artifacts for repeated failure semantics without running anything new
- apply the discovery lenses from the order doc
- rank findings by leverage, novelty, evidence density, blast radius, reversibility, operator value, and implementation independence

Do not stop at obvious findings. Push for surprising but defensible opportunities.
```
