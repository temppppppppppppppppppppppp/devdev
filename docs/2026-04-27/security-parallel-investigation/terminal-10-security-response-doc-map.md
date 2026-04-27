# T10 Security Response Documentation Map

Date: 2026-04-27
Workspace: `C:\Users\wjjo\Desktop\글도비`
Baseline commit: `a3d826978d530ab61d3765e5e095890fa6533ea7`
Primary issue: [#71](https://github.com/temppppppppppppppppppppppp/devdev/issues/71) `[DOCS] Document security response and current mitigation status`
Related issues: #66, #67, #68, #69, #70
Document type: read-only investigation report. Not an execution SSOT and not a security-response document itself.

## Scope

This terminal does not produce the final response document. It produces the map needed before that document can be written safely. Concretely:

1. Identify the canonical doc that should eventually consolidate security feedback, current mitigation status, decisions, owners, evidence pointers, and residual risk for issues #66-#71.
2. Inventory pre-existing security-, config-, auth-, and release-related docs already in the repo so the future canonical doc does not duplicate, contradict, or silently override material that has already passed governance.
3. Record the present status of sibling terminal reports T01-T09 so the future canonical doc only claims closure that the evidence trail actually supports.
4. Surface dependencies, open questions, and a closure recommendation in the schema required by the dispatch.

Explicitly out of scope for T10:

- Writing or rewriting the canonical security-response document itself.
- Modifying `.env`, `secrets/`, `config/`, `geuldobi-desktop/`, `modules/`, GitHub issues, branches, commits, or PRs.
- Re-running T01-T09 surveys. T10 only summarizes what does or does not yet exist.
- Pasting any secret value, private key, recovery code, token, or credential JSON into evidence or findings.

## Commands / Evidence

T10 operated read-only. The following safe inspections were performed.

Sibling terminal reports under `docs/2026-04-27/security-parallel-investigation/`:

- `Bash: ls -la docs/2026-04-27/security-parallel-investigation/`
  - Result: only `security-issues-parallel-investigation-dispatch.md` is present. Reports `terminal-01-secret-inventory.md` through `terminal-09-ci-release-guardrails.md` are absent at the snapshot time.

Dispatch document confirmation:

- `Read: docs/2026-04-27/security-parallel-investigation/security-issues-parallel-investigation-dispatch.md`
  - Confirms baseline commit `a3d826978d530ab61d3765e5e095890fa6533ea7`, terminal matrix T01-T10, save paths, and global rules.

Workspace governance read order:

- `Read: AGENTS.md`
  - Confirms `AGENTS.md` is the workspace SSOT, UTF-8 is a global invariant, and dated docs under `docs/YYYY-MM-DD/` are the canonical save root.
- `Read: CLAUDE.md`
  - Confirms `CLAUDE.md` is a compatibility shim and defers to `AGENTS.md`. No security guidance is hosted there.

Tracked security-, secret-, credential-, GCP/Vertex-, AppData-, release-, packaging-, license-, and access-control-related docs already in the repo:

- `Bash: git ls-files docs/ | grep -iE "(security|secret|credential|access-control|gcp|vertex|barobook|appdata|release|packag)"`
  - Result paths recorded under §3 Findings. Notable hits: `docs/2026-04-19/survey/T10-security-ops.md`, `docs/2026-04-19/survey/AUDIT-REPORT.md`, `docs/2026-04-19/survey/T08-config-data.md`, `docs/2026-04-19/survey/T09-peripherals.md`, `docs/2026-04-27/gcp-iam-5arc-cleanrun-prep-context.md`, `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md`, `docs/2026-04-27/gcp-iam-5arc-sleep-ops-context.md`, `docs/poc/vertex_ai_migration.md`, `docs/implementation/release-gate-v1.md`, `docs/2026-04-06/5arc-parallel-vertex-pool-guard-bounded-survey-order.md`, `docs/2026-04-13/stage234-context-memory-vertex-live-3pass-audit.md`, `docs/2026-04-13/stage234-context-memory-vertex-live-parallel-survey.md`, `docs/2026-04-25/repo-trashbox-packaging-scope-fresh-reaudit.md`.

Additional repo-root and `secrets/` checks:

- `Glob: **/SECURITY*.md`
  - Result: zero project-owned `SECURITY*.md` at repo root, `docs/`, or `geuldobi-desktop/` source. All hits are inside `geuldobi-desktop/node_modules/*/SECURITY.md` (third-party packages) and are not authoritative for this project.
- `Read: secrets/README.md`
  - Confirms `secrets/` is intentionally visible, `secrets/*.env` is gitignored, and the documented loader path is `scripts/sync_clickup_queue.py` reading root `.env` first then `secrets/clickup.env`.
- `Read: docs/implementation/release-gate-v1.md` (lines 1-60)
  - Confirms release gate v1 already names a security evidence artifact: `security-signoff.md` under G5 with owner `Ops/Security`. This is the only pre-existing canonical-style name for a security response artifact in the repo.
- `Read: docs/poc/vertex_ai_migration.md` (lines 1-40)
  - 2026-03-03 doc explaining the move from direct Gemini API key auth to Vertex AI. Records the rationale (503/500 surge on `gemini-3.1-pro-preview`) but does not record an account-governance decision around the shared Barobook account that #67 targets.
- `Read: docs/2026-04-27/gcp-iam-5arc-cleanrun-prep-context.md`
  - Records that `modules/core/providers/vertex_provider.py` now lets `GEULDOBI_VERTEX_AUTH_MODE` override provider config `auth_mode`, and that `tests/test_llm_router.py` reports 51 passed at the prep snapshot.
- `Read: docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md` (lines 1-60)
  - Records a stopped provisional handoff for the `gcp_iam_vertex_global_31pro_strict_5arc_rerun_after_vehicle_intrusion_guard_patch` run on `projects/01_골든카나리아` and warns that conclusions stay provisional until a future post-run 3-pass merge audit completes.

No raw secret values, private keys, recovery codes, tokens, or credential JSON fields were read or written in this report.

## Findings

### F1. Sibling terminal reports T01-T09 are absent at this snapshot

The dispatch matrix expects nine peer reports under `docs/2026-04-27/security-parallel-investigation/`. None exist at snapshot time. Status matrix:

| Terminal | Primary issue(s) | Expected report path | Status at T10 snapshot |
| --- | --- | --- | --- |
| T01 | #66 | `terminal-01-secret-inventory.md` | absent |
| T02 | #66, #68 | `terminal-02-runtime-config-topology.md` | absent |
| T03 | #67, #66 | `terminal-03-vertex-auth-flow.md` | absent |
| T04 | #66, #68, #70 | `terminal-04-desktop-config-surfaces.md` | absent |
| T05 | #68, #66 | `terminal-05-windows-settings-paths.md` | absent |
| T06 | #69, #70, #66 | `terminal-06-release-packaging.md` | absent |
| T07 | #69 | `terminal-07-dev-test-separation.md` | absent |
| T08 | #70, #68 | `terminal-08-exe-access-control.md` | absent |
| T09 | #66, #69 | `terminal-09-ci-release-guardrails.md` | absent |
| T10 | #71 | this document | written by T10 in pending-evidence mode |

T10 therefore writes in the dispatch-defined "pending evidence" mode. The canonical security-response doc must not be authored as a closure or "current mitigation status" document until T01-T09 (or substantive equivalent evidence) exist and have been merged.

### F2. No project-owned canonical security response document exists

There is no `SECURITY.md` at repo root, no project-owned `SECURITY.md` under `docs/`, no `docs/SECURITY.md`, and no equivalent under `geuldobi-desktop/` source paths. All `SECURITY.md` matches in the workspace come from `geuldobi-desktop/node_modules/*` and are third-party package files, not authoritative for this project.

This means #71 cannot be closed by linking to an existing doc. A new canonical doc must be authored. Today there are only adjacent partial docs (see F3, F4, F5).

### F3. Pre-existing security-adjacent surveys that the canonical doc must reconcile

These docs already exist and contain conclusions that overlap with #66, #67, #68, #69, and #70. The canonical security-response doc must explicitly cite them or supersede them with a delta note, otherwise readers will see contradictory authority across the repo.

| Doc | Date | Relevance to issues |
| --- | --- | --- |
| `docs/2026-04-19/survey/T10-security-ops.md` | 2026-04-19 | Direct precursor. Lists P0 secret exposure in `.env`, bridge endpoint auth, WebDriver leak, log rotation, and lower-priority items. Overlaps strongly with #66 and partially with #68. Authored before #66-#71 dispatch and may now be stale on resolved items. |
| `docs/2026-04-19/survey/T08-config-data.md` | 2026-04-19 | Config and data ownership. Overlaps with #66 runtime config standardization and #68 settings location. |
| `docs/2026-04-19/survey/T09-peripherals.md` | 2026-04-19 | Peripheral subsystems. May overlap with #69 dev/test separation and #70 EXE access control depending on scope. |
| `docs/2026-04-19/survey/AUDIT-REPORT.md` | 2026-04-19 | Integrated audit report from the same 2026-04-19 survey wave. Likely the closest existing aggregation doc. The new canonical doc must either supersede it for security-only scope or cite it as the cross-cutting parent. |
| `docs/2026-04-19/audit-report-candidate-revalidation-3pass-audit.md` | 2026-04-19 | Revalidation audit of the 04-19 audit report. Same caveat as above. |
| `docs/2026-04-19/audit-report-candidate-revalidation-remediation-execution-ssot.md` | 2026-04-19 | Remediation execution SSOT spawned from the 04-19 audit. The new doc must check what was already executed before claiming open status. |

### F4. Pre-existing Vertex/GCP/IAM material that #67 must reconcile

| Doc | Date | Relevance |
| --- | --- | --- |
| `docs/poc/vertex_ai_migration.md` | 2026-03-03 | Original transition rationale from direct Gemini API key to Vertex AI. Provides historical context for #67 but does not contain account-governance decisions for the shared Barobook account. |
| `docs/2026-04-06/5arc-parallel-vertex-pool-guard-bounded-survey-order.md` | 2026-04-06 | Vertex pool guard survey order. Touches provider/env guard surface for #66 and #67. |
| `docs/2026-04-13/stage234-context-memory-vertex-live-parallel-survey.md` | 2026-04-13 | Live Vertex survey across stages. Provides runtime evidence relevant to #67 closure path. |
| `docs/2026-04-13/stage234-context-memory-vertex-live-3pass-audit.md` | 2026-04-13 | 3-pass audit on the same. |
| `docs/2026-04-27/gcp-iam-5arc-cleanrun-prep-context.md` | 2026-04-27 | Records the explicit `GEULDOBI_VERTEX_AUTH_MODE=project_credentials` patch that prevents `VERTEX_API_KEY` from silently overriding project credentials. This is a partial mitigation directly relevant to #67. |
| `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md` | 2026-04-27 | Stopped provisional handoff for the 5-arc clean proof run. Conclusions remain provisional until a post-run 3-pass merge audit. The canonical doc must label this evidence as provisional, not closure. |
| `docs/2026-04-27/gcp-iam-5arc-sleep-ops-context.md` | 2026-04-27 | Sleep-ops context for the same run; same provisional caveat. |
| `docs/2026-04-27/gcp-iam-5arc-cleanrun-prerun-baseline.json`, `docs/2026-04-27/gcp-iam-5arc-strict31-prestart-baseline.json` | 2026-04-27 | Raw baseline evidence files referenced by the GCP IAM context docs above. |

### F5. Pre-existing release/packaging/dev-test separation material that #69 and #70 must reconcile

| Doc | Date | Relevance |
| --- | --- | --- |
| `docs/implementation/release-gate-v1.md` | implementation harness | Defines G1-G6 release gates and explicitly names a `security-signoff.md` evidence artifact owned by Ops/Security under G5. This is the only pre-existing canonical-style placeholder for the response document. |
| `docs/2026-04-25/repo-trashbox-packaging-scope-fresh-reaudit.md` | 2026-04-25 | Packaging-scope reaudit. Overlaps with #69 and #70 release-build inclusion concerns. |
| `docs/2026-04-25/repo-trashbox-quarantine-move-plan.md` | 2026-04-25 | Quarantine plan for repo trashbox. Touches dev/test/temp separation for #69. |
| `docs/2026-04-25/repo-trashbox-cleanup-fresh-reaudit.md`, `docs/2026-04-25/repo-trashbox-low-risk-removal-preflight-reaudit.md`, `docs/2026-04-25/repo-trashbox-low-risk-tracked-removal-manifest.md`, `docs/2026-04-25/repo-trashbox-reference-check.md`, `docs/2026-04-25/repo-spikes-preservation-removal-preflight-reaudit.md`, `docs/2026-04-25/repo-generated-project-residue-execution-ssot.md`, `docs/2026-04-25/repo-generated-project-residue-removal-preflight-reaudit.md`, `docs/2026-04-25/repo-root-temp-residue-removal-preflight-reaudit.md` | 2026-04-25 | Repo cleanup wave. The canonical doc must check which of these were executed and which remained advisory before claiming #69 status. |
| `secrets/README.md` | repo root | Documents `secrets/*.env` as gitignored and lists the loader path. Sets ground-truth for what "approved" looks like for ClickUp tokens. Must be cited but not duplicated. |

### F6. Naming and location decision is unresolved

There is no existing repo convention for where the security-response doc should live. The candidates are:

- **C1**: top-level `SECURITY.md`. Pros: GitHub auto-renders this on the security tab and is discoverable to external readers. Cons: project-internal evidence is normally under `docs/` and `AGENTS.md` keeps repo root narrow.
- **C2**: dated canonical under `docs/2026-04-27/security-response-mitigation-status.md`. Pros: aligns with `AGENTS.md` "execution SSOT 정본은 `docs/YYYY-MM-DD/`" rule and with the dispatch dating. Cons: not surfaced on GitHub security UI.
- **C3**: implementation-tier canonical at `docs/implementation/security-signoff.md`. Pros: matches the existing `release-gate-v1.md` G5 evidence name. Cons: `docs/implementation/` is reserved in this workspace for harnesses and contracts, not for status documents, so dropping a status doc there can confuse the implementation-tier vs dated-canonical separation.
- **C4** (recommended): both C2 and C1 with C2 as primary canonical and C1 as a thin pointer that links to C2 plus the dispatch and the consolidated remediation roadmap. This satisfies governance (C2 wins under `AGENTS.md`), discoverability (C1 surfaces on GitHub), and release evidence naming (C2 can be referenced from `release-gate-v1.md` G5 in the same wave that introduces it, or `release-gate-v1.md` can be left untouched until a separate change wave).

T10 surfaces this as a finding rather than a decision. The owner of #71 should pick.

### F7. Required canonical doc structure (proposal, not yet authored)

#71 explicitly asks for: security feedback, current mitigation status, decisions, owners, evidence, residual risk. T10 maps that to the following structure for the future canonical doc, so the doc-map is concrete:

1. Header: title, date, baseline commit, baseline dirty state, governance pointer to `AGENTS.md`.
2. Source feedback summary: one paragraph per issue #66-#70 reproducing the feedback intent in neutral language without paraphrasing the reporter into agreement.
3. Mitigation status table: one row per issue with columns `issue`, `priority`, `current status`, `evidence path`, `owner`, `residual risk`. Status values constrained to `not started`, `in progress`, `partial mitigation`, `mitigated pending verification`, `mitigated`, `accepted risk`. No `closed` until the dispatch's merge plan §7 has produced a consolidated remediation roadmap and the evidence trail covers it.
4. Decisions log: each decision dated and tied to the doc that records it (for example: "#67 partial mitigation by `GEULDOBI_VERTEX_AUTH_MODE=project_credentials` per `docs/2026-04-27/gcp-iam-5arc-cleanrun-prep-context.md`, account-governance decision still pending owner sign-off").
5. Owners: one row per area (secrets, runtime config, Vertex auth, desktop config, Windows paths, release packaging, dev/test separation, EXE access control, CI guardrails, response doc upkeep). Owners may be `unassigned` rather than fabricated.
6. Evidence index: pointer table back to T01-T10 reports, the consolidated remediation roadmap (`docs/2026-04-27/security-remediation-roadmap.md` per dispatch §7), the 2026-04-19 audit set, the GCP IAM 04-27 set, and `secrets/README.md`.
7. Residual risk: items that the response wave knowingly does not solve, with rationale and re-review trigger conditions.
8. 3-pass audit trail per `AGENTS.md` document save rule. Final save only after pass 3 with confidence ≥ 95%.

T10 does not write this doc itself. The map above is the deliverable.

## Remediation Candidates

These are documentation candidates only. They do not modify source code.

| Candidate | Priority | Description |
| --- | --- | --- |
| RC1 | P1 | After T01-T09 produce reports, draft the canonical security-response doc at `docs/2026-04-27/security-response-mitigation-status.md` using the §F7 structure. Run 3-pass audit per `AGENTS.md` before final save. |
| RC2 | P1 | Build the consolidated security remediation roadmap at `docs/2026-04-27/security-remediation-roadmap.md` per dispatch §7 before the response doc declares mitigation status, so status rows can cite roadmap items rather than restating raw findings. |
| RC3 | P2 | After RC1 lands, add a thin top-level `SECURITY.md` that points to the canonical dated doc and the dispatch, so external readers and GitHub security UI find the right entry. Keep it short to avoid drift. |
| RC4 | P2 | Reconcile `docs/2026-04-19/survey/T10-security-ops.md` and `docs/2026-04-19/survey/AUDIT-REPORT.md` against the new response doc by adding a header note pointing forward, so the two surveys do not stay as competing authority. Do not delete the 04-19 docs; they are evidence. |
| RC5 | P3 | After the canonical doc exists, update `docs/implementation/release-gate-v1.md` G5 owner row to point at the canonical doc as the supplier of `security-signoff.md` evidence, or harmonize the artifact name. Do this in a separate change wave to keep the security-response wave bounded. |
| RC6 | P3 | Decide whether `secrets/README.md` should grow into a "Secrets and runtime config policy" doc or stay as a folder README. The canonical response doc should cite the policy doc, not duplicate it. |

These candidates are docs-only. T10 does not endorse any code, config, IAM, packaging, or CI change here. Those decisions belong to T01-T09 and to the consolidated roadmap.

## Dependencies On Other Terminals

- **T01 (#66 secret inventory)**: hard dependency. The canonical doc cannot list mitigation status for #66 P0 items without T01's redacted inventory and tracked/ignored classification.
- **T02 (#66, #68 runtime config topology)**: hard dependency for the runtime-config standardization rows of the mitigation table.
- **T03 (#67, #66 Vertex auth flow)**: hard dependency for the #67 row. T10 already has partial evidence from `docs/2026-04-27/gcp-iam-5arc-cleanrun-prep-context.md` but cannot determine whether the Barobook account-governance concern is resolved without T03.
- **T04 (#66, #68, #70 desktop config surfaces)**: hard dependency for the desktop bridge rows.
- **T05 (#68, #66 Windows settings paths)**: hard dependency for the approved-path policy decision.
- **T06 (#69, #70, #66 release packaging)**: hard dependency for #69 release-build inclusion claims.
- **T07 (#69 dev/test separation)**: hard dependency for #69 separation inventory.
- **T08 (#70, #68 EXE access control)**: hard dependency for #70 design rows.
- **T09 (#66, #69 CI/release guardrails)**: hard dependency for "guardrail in place" claims that the canonical doc would otherwise be tempted to assume.

T10 does not block T01-T09. T10's output is consumable in pending-evidence mode and will be supplemented after the merge plan §7 step runs.

## Open Questions

- **OQ1 (location)**: Does the owner of #71 want the canonical doc at `docs/2026-04-27/security-response-mitigation-status.md` (dated, governance-aligned), at top-level `SECURITY.md` (GitHub-discoverable), at `docs/implementation/security-signoff.md` (release-gate naming), or at all of the above with one as primary? T10 recommends C4 (dated canonical primary + thin top-level pointer).
- **OQ2 (owners)**: There is no existing security owner roster in `AGENTS.md`. Should the canonical doc list named owners, role-based owners (`Ops/Security`, `Backend Lead`, `Release Manager` per `release-gate-v1.md`), or `unassigned` placeholders that the project lead later fills?
- **OQ3 (relationship to 04-19 surveys)**: The 2026-04-19 audit set already published security findings as part of a broader audit. Should the new canonical doc supersede those for security-only scope, or live alongside them as a focused response while the 04-19 audit retains cross-cutting authority? T10 recommends supersede-for-security-scope with explicit forward-pointers added to the 04-19 docs.
- **OQ4 (issue-comment update)**: Once the canonical doc exists, should the GitHub issues #66-#71 be updated with a single comment linking to it? The dispatch global rules forbid editing GitHub state during this wave, so any such update must happen in a later, separately-authorized step.
- **OQ5 (re-review cadence)**: Should the canonical doc include a re-review trigger (for example, "re-review if any item in the residual-risk list is touched by code or config change", or "re-review at next release gate")? This affects whether residual risk decays into stale risk.
- **OQ6 (release-gate evidence name)**: `docs/implementation/release-gate-v1.md` G5 names the evidence file as `security-signoff.md` with owner Ops/Security, but the dispatch and #71 frame the doc as a "security response and mitigation status" document. Should these names be unified, or should one be a subset of the other (sign-off as the gate-passing document, response doc as the broader mitigation-status document)?

## Closure Recommendation

T10 recommends the following closure path for #71:

1. **Do not close #71 yet**, and do not author the canonical security-response doc yet. Wait for T01-T09 to land, or until merge plan §7 produces the consolidated remediation roadmap. Authoring the response doc in pending-evidence mode would create either an empty status table or a guessed one, both of which would conflict with `AGENTS.md` document save and 3-pass audit rules.
2. Once T01-T09 are present, pick a location per §F6 (T10 recommends C4: dated canonical at `docs/2026-04-27/security-response-mitigation-status.md` plus a thin top-level `SECURITY.md` pointer).
3. Author the canonical doc using the §F7 structure, citing the 04-19 survey set (F3), the Vertex/GCP set (F4), the release/packaging/dev-test set (F5), `secrets/README.md`, and T01-T09 reports.
4. Run a 3-pass document audit on the canonical doc per `AGENTS.md`. Final save only at confidence ≥ 95%.
5. Mirror to `docs/temp/` only after the dated canonical is finalized, per `AGENTS.md` execution SSOT mirror rule. The response doc is a status doc rather than an execution SSOT, so the mirror step is optional unless the project lead promotes it.
6. Update GitHub issue #71 in a later, separately-authorized step with a single comment linking to the canonical doc. Do not modify other issue state during this wave.
7. T10's own status under #71 is `pending evidence`, not `closed`. T10 considers its output complete for the dispatch wave.

T10 deliberately does not declare any of #66-#70 mitigated, partially mitigated, or open. Those judgments belong to T01-T09 plus the canonical doc author working from the merged evidence trail.
