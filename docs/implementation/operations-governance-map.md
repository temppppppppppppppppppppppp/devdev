# Operations Governance Map

Date: 2026-03-14
Status: active
Applies To: system-track operational documents and execution workflow

## 1. Purpose
- Define the precedence order for operational instructions in this workspace.
- Resolve conflicts between SSOT documents, companion harnesses, templates, mirrors, and historical shims.
- Keep future process hardening additive instead of ambiguous.

## 2. Precedence Order
Apply higher entries before lower ones.

1. Explicit user instruction for the current turn
2. `AGENTS.md`
3. `docs/implementation/system-order-init-harness.md`
4. Specialized harnesses directly relevant to the task
5. Contracts and templates used by those harnesses
6. Local operating notes such as `docs/temp/README.md`
7. Compatibility shims such as `CLAUDE.md`

Within item 4, use this order when multiple specialized harnesses are relevant:
1. `docs/implementation/system-order-preflight-harness.md`
2. `docs/implementation/system-full-survey-execution-harness.md`
3. `docs/implementation/deep-global-integrity-survey-harness.md`
4. `docs/implementation/execution-synthesis-harness.md`
5. `docs/implementation/temp-execution-queue-roadmap-harness.md`
6. `docs/implementation/document-3pass-audit-harness.md`
7. `docs/implementation/evidence-manifest-harness.md`
8. `docs/implementation/ops-validator-harness.md`
9. `docs/implementation/execution-closure-harness.md`
10. `docs/implementation/exception-registry-harness.md`
11. `docs/implementation/process-health-scorecard-harness.md`
12. `docs/implementation/stale-reference-sweep-harness.md`

Specific-over-general rule:
- if two documents at the same precedence level do not agree, the more specific one wins for that task
- if specificity is equal, prefer the newer canonical document with the narrower scope

## 3. Canonical vs Mirror Policy
- Canonical dated documents in `docs/YYYY-MM-DD/` beat mirror copies in `docs/temp/`.
- Mirror files are operational queue artifacts, not authorities.
- If canonical and mirror content drift, repair the canonical file first and then overwrite the mirror.
- Do not let a temp file become newer in meaning than its canonical source.

## 4. Live Evidence Policy
- Live workspace code beats stale survey text.
- Newly generated evidence beats recalled counts or older snapshots.
- Historical documents remain useful for lineage, not for overriding current facts.
- For ROL surveys, re-audits, execution SSOTs, and roadmaps, use `docs/implementation/commit-state-minimal-contract.md` to anchor baseline and resume state without turning documents into git transcripts.

## 5. Queue Governance
- An aggregate roadmap controls multi-item realization once two or more execution SSOT mirrors are present.
- A deep global survey bundle may have many execution SSOTs but only one SSOT roadmap.
- Queue order should use `docs/implementation/queue-priority-rubric.md`.
- Queue state snapshots should be generated with `scripts/sync_temp_queue_state.py` when machine-readable state is needed.
- Queue closure should use `docs/implementation/execution-closure-harness.md`.
- Queue integrity should be checked with `docs/implementation/ops-validator-harness.md`.

## 6. Document Governance
- Human-facing documents must complete the 3-pass audit and reach at least 95% confidence before final save.
- Execution SSOT documents must exist canonically before they are mirrored into `docs/temp/`.
- Before code modification starts from an execution SSOT or aggregate roadmap, re-audit the governing document against the current workspace state and confirm at least 95% confidence again.
- Evidence-heavy topics should prefer `docs/implementation/evidence-manifest-harness.md`.
- Deep global survey claims should follow `docs/implementation/evidence-triangulation-contract.md`.
- Deep global survey confidence claims should follow `docs/implementation/integrity-confidence-scoring-contract.md`.
- Filenames should follow `docs/implementation/canonical-naming-contract.md`.
- Closure notes, if created, are canonical documents first and temp artifacts never.
- Optional queue state files must follow `docs/implementation/temp-queue-state-contract-v1.json`.

## 7. Conflict Resolution Examples
- If `CLAUDE.md` says one thing and `AGENTS.md` says another, `AGENTS.md` wins.
- If a temp roadmap differs from the canonical roadmap, fix the canonical roadmap and refresh the temp mirror.
- If an execution template omits a rule that a harness requires, the harness wins.
- If an old survey count conflicts with a fresh AST inventory, the fresh inventory wins.

## 8. Guardrails
- Do not invent a second SSOT beside `AGENTS.md`.
- Do not rely on temp files as archival history.
- Do not bypass the init harness when system-track process documents conflict.
- Do not let templates become implicit policy documents.
