# Repo Generated Project Residue Execution SSOT

Date: 2026-04-25
Status: in-progress (generated project and root temp removal complete; spikes preservation follow-up next)
Canonical Path: `docs/2026-04-25/repo-generated-project-residue-execution-ssot.md`
Temp Mirror Path: `docs/temp/repo-generated-project-residue-execution-ssot.md`
Commit State:
- Baseline Commit: `f93b5749c38e6374669b199fb8a0da65d0f2aac0`
- Baseline Dirty Summary: `clean branch feat/repo-hygiene-next-wave-survey opened from main after PR #21 merge`
- Resume Commit: `217bfb7d6b2619ff682abd7f892aa6a1d0fb86f2`
- Resume Drift Summary: `PR #23 merged generated-project removal into main; branch feat/repo-root-temp-residue-cleanup opened and removed only the 11 preflight-approved root/temp paths while preserving 0_temp.txt`
Source Survey Docs:
- `docs/2026-04-24/repo-trashbox-candidate-survey.md`
- `docs/2026-04-25/repo-trashbox-quarantine-move-plan.md`
- `docs/2026-04-25/repo-trashbox-low-risk-tracked-removal-manifest.md`
- `docs/2026-04-25/repo-trashbox-low-risk-removal-preflight-reaudit.md`
- `docs/2026-04-25/repo-generated-project-residue-removal-preflight-reaudit.md`
- `docs/2026-04-25/repo-root-temp-residue-removal-preflight-reaudit.md`
Evidence Artifacts:
- `.gitignore`
- `tests/test_surface_containment_contract.py`
- `docs/implementation/surface-containment-contract-v1.json`
Post-Removal Evidence:
- `git ls-files -- test_mode/projects lite_mode/projects`
- `git ls-files -- test_mode/bridge lite_mode/bridge`
- `git ls-files -- temp-electron-paths.js temp-proc-poll-oswarn.ps1 temp-proc-poll.ps1 temp-proc-trace.ps1 temp-run-packaged-ascii.ps1 temp-run-packaged.ps1 temp.txt temp/yt_test temp_triage_test.json temp_시리즈.txt`
- `git ls-files -- 0_temp.txt`
- `git check-ignore --no-index temp-electron-paths.js temp-run-packaged.ps1 temp.txt temp_시리즈.txt temp_triage_test.json temp/yt_test/example.json`
Side-Effect Coverage: covered

## 0. Execution Metadata Block

```yaml
execution_meta:
  schema_version: execution-meta-block-v1
  topic: repo-generated-project-residue
  github_issue: 9
  depends_on: []
  status: in_progress
  queue_role: front_active
  roadmap_rank: 1
  tranches:
    - id: generated-project-removal
      title: Remove duplicated generated project residue under test_mode/projects and lite_mode/projects
    - id: root-temp-followup
      title: Survey remaining root temp residue after generated project cleanup
    - id: spikes-preservation-followup
      title: Preserve useful spike notes before any spikes cleanup
```

## 1. Intent

Continue repository hygiene after the bounded repo-trashbox cleanup closure by targeting generated project residue and root temp residue that can be removed without touching live runtime surfaces.

This SSOT does not authorize broad removal of `test_mode/`, `lite_mode/`, or `spikes/`. The generated project removal tranche removed only `test_mode/projects/` plus `lite_mode/projects/`, and the root temp tranche removed only the 11 paths authorized by the fresh preflight re-audit while preserving `0_temp.txt`.

## 2. Baseline Facts

Current live tracked inventory:

| Candidate | Tracked files | Bytes | Classification | First action |
| --- | ---: | ---: | --- | --- |
| `test_mode/projects/` | 1522 | 42091969 | generated project residue | manifest-bound `git rm` |
| `lite_mode/projects/` | 1522 | 42091969 | generated project residue | manifest-bound `git rm` |
| `test_mode/` total | 1554 | 42428086 | mixed manual source plus generated project residue | do not remove whole tree |
| `lite_mode/` total | 1554 | 42426849 | mixed manual source plus generated project residue | do not remove whole tree |
| root/temp removable set | 11 | 1127159 | YouTube-test residue and helper scripts | completed manifest-bound `git rm` |
| `0_temp.txt` | 1 | 22445 | historical evidence anchor | preserve |
| `spikes/` | 7 | 26468 | prototype notes/code | preserve useful notes before cleanup |

The two generated project trees have:

- identical tracked file counts: 1522 each
- identical byte size: 42091969 each
- identical relative path set: 1522 common relative paths
- identical file content hashes: 0 mismatches

Future generated project residue is already ignored:

```text
test_mode/projects/
lite_mode/projects/
```

## 3. Included Scope

- completed: `git rm -r -- test_mode/projects lite_mode/projects`
- completed: contract/test update so generated project residue absence is asserted
- completed: `git rm -r --` the 11 preflight-approved root/temp residue paths
- completed: root-only ignore policy for future temp residue
- in progress: spikes preservation follow-up decision after validation

## 4. Excluded Scope

- `test_mode/` non-project manual helpers
- `lite_mode/` non-project manual helpers
- `spikes/`
- `0_temp.txt`
- `projects/_canary/`
- runtime code, packaging code, and source entrypoints
- local trashbox directory creation
- history rewrite

## 5. Pass 1 - Inventory

The largest remaining cleanup candidate is not the whole manual-mode tree; it is the duplicated generated project subtree under both manual-mode directories. Removing only `*/projects/` leaves the smaller manual helper/source surfaces in place for later explicit decisions.

Pass 1 result: pass.

## 6. Pass 2 - Semantic Classification

`test_mode/projects/` and `lite_mode/projects/` are generated project artifacts, not the formal pytest suite and not runtime source. The current reference scan found only docs, `.gitignore`, and surface-containment test references for these exact paths.

The non-project `test_mode/` and `lite_mode/` files are mixed manual helper/source surfaces and should not be removed in this tranche.

Pass 2 result: pass.

## 7. Side-Effect Map

File writes / artifacts:

- Completed implementation deleted tracked generated project artifacts via Git.
- Completed implementation deleted the 11 preflight-approved root/temp residue paths via Git.
- No local trashbox copy was created.

DB / schema / transaction boundaries:

- Not applicable. These generated project trees are file artifacts only.

JSONL / log / audit sinks:

- Not applicable for runtime. Some deleted files may be old generated logs or metadata, but they are static tracked residue.

Console / UI / operator output:

- Not applicable. No runtime output path changes.

Rollback / recovery / retry:

- Rollback is a normal PR revert.

Cache / global state:

- Not applicable.

Bootstrap fallback / config-env mutation:

- `.gitignore` prevents future generated project residue from re-entering the tracked surface.
- `.gitignore` now prevents future root `temp-*`, `temp.txt`, `temp_*.txt`, `temp_triage_test.json`, and `temp/` residue from re-entering the tracked surface without ignoring `docs/temp/`.

## 8. Pass 3 - Execution Shape

Tranche 1 was a single focused removal PR:

```text
git rm -r -- test_mode/projects lite_mode/projects
```

The PR verifies that:

- `git ls-files -- test_mode/projects lite_mode/projects` returns no files after removal
- `test_mode/bridge` and `lite_mode/bridge` remain tracked
- `.gitignore` still contains `test_mode/projects/` and `lite_mode/projects/`
- no runtime code changes are bundled

Tranche 2 was a separate focused root-temp removal PR:

```text
git rm -r -- <11 preflight-approved root/temp paths>
```

The PR verifies that:

- the 11 removable root/temp paths have zero tracked files after removal
- `0_temp.txt` remains tracked as a historical evidence anchor
- root-only `.gitignore` rules prevent future temp residue while leaving `docs/temp/` available for queue mirrors
- no runtime code changes are bundled

Tranche 3 may handle `spikes/` only after useful `spikes/**/result.md` conclusions are preserved or explicitly judged unnecessary.

Pass 3 result: pass.

## 9. Acceptance Criteria

- `test_mode/projects/` has zero tracked files. (complete)
- `lite_mode/projects/` has zero tracked files. (complete)
- Non-project manual helper files under `test_mode/` and `lite_mode/` remain tracked.
- The 11 preflight-approved root/temp residue paths have zero tracked files. (complete)
- `0_temp.txt` remains tracked. (complete)
- `spikes/` remains untouched.
- `docs/temp/queue-state.json` reflects the active or closed state honestly.
- `python scripts/ops_validator.py --strict` passes.

## 10. Verification Plan

After implementation:

- `git ls-files -- test_mode/projects lite_mode/projects`
- `git ls-files -- test_mode/bridge lite_mode/bridge`
- `git ls-files -- temp-electron-paths.js temp-proc-poll-oswarn.ps1 temp-proc-poll.ps1 temp-proc-trace.ps1 temp-run-packaged-ascii.ps1 temp-run-packaged.ps1 temp.txt temp/yt_test temp_triage_test.json temp_시리즈.txt`
- `git ls-files -- 0_temp.txt`
- `git check-ignore --no-index temp-electron-paths.js temp-run-packaged.ps1 temp.txt temp_시리즈.txt temp_triage_test.json temp/yt_test/example.json`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`
- `python scripts/check_utf8_hygiene.py docs/2026-04-25/repo-root-temp-residue-removal-preflight-reaudit.md docs/2026-04-25/repo-generated-project-residue-execution-ssot.md docs/temp/repo-generated-project-residue-execution-ssot.md docs/temp/queue-state.json tests/test_surface_containment_contract.py docs/implementation/surface-containment-contract-v1.json .gitignore`
- `python -m pytest tests/test_surface_containment_contract.py tests/test_runtime_authority_contract.py -q`

## 11. Generated Project Removal Closure Note

Implemented:

- removed exactly `test_mode/projects/` and `lite_mode/projects/`
- left `test_mode/bridge` and `lite_mode/bridge` tracked
- left `spikes/`, root `temp*`, `projects/_canary/`, runtime code, packaging code, and source entrypoints untouched
- updated `docs/implementation/surface-containment-contract-v1.json` and `tests/test_surface_containment_contract.py` so the generated project residue directories are expected to be absent and still ignored for future regeneration

Residual queue:

- `spikes/` still requires notes-preservation review before cleanup

## 12. Root Temp Removal Closure Note

Implemented:

- removed exactly the 11 root/temp paths authorized by `docs/2026-04-25/repo-root-temp-residue-removal-preflight-reaudit.md`
- preserved `0_temp.txt` because historical audit docs cite it as a direct evidence anchor
- updated `docs/implementation/surface-containment-contract-v1.json` and `tests/test_surface_containment_contract.py` so root-temp residue is expected to be absent and `0_temp.txt` is expected to remain
- added root-only `.gitignore` rules for future temp residue without ignoring `docs/temp/`

Residual queue:

- `spikes/` still requires notes-preservation review before cleanup

## 13. Guardrails

- Do not delete all of `test_mode/`.
- Do not delete all of `lite_mode/`.
- Do not touch `spikes/` in the root-temp PR.
- Do not delete `0_temp.txt` unless a separate evidence-preservation decision supersedes this SSOT.
- Do not treat old size estimates as authority when live `git ls-files -z` evidence differs.
- Do not proceed to cleanup without a fresh current-state re-audit of this SSOT.

## 14. Document 3-Pass Audit

Pass 1 - Structure and scope:

- The document is an execution SSOT, not an implementation PR.
- Included and excluded surfaces are explicit.
- Canonical/temp queue semantics are present.

Pass 2 - Evidence and consistency:

- Counts and byte sizes come from current `git ls-files -z` plus filesystem stat evidence.
- The two generated project trees were compared by relative path and SHA-256 content hashes.
- Reference findings are bounded to scoped `rg` scans over docs, modules, scripts, tests, config, packaging, and desktop surfaces.

Pass 3 - Execution and readability:

- The first implementation command is intentionally narrow.
- Larger manual/prototype/root-temp cleanup is deferred into follow-up SSOTs or manifests.
- Rollback and validation are explicit.

Confidence: 96/100
