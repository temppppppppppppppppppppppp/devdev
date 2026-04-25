# Repo Generated Project Residue Execution SSOT

Date: 2026-04-25
Status: in-progress (generated project residue manifest ready; no tracked removal performed)
Canonical Path: `docs/2026-04-25/repo-generated-project-residue-execution-ssot.md`
Temp Mirror Path: `docs/temp/repo-generated-project-residue-execution-ssot.md`
Commit State:
- Baseline Commit: `f93b5749c38e6374669b199fb8a0da65d0f2aac0`
- Baseline Dirty Summary: `clean branch feat/repo-hygiene-next-wave-survey opened from main after PR #21 merge`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-04-24/repo-trashbox-candidate-survey.md`
- `docs/2026-04-25/repo-trashbox-quarantine-move-plan.md`
- `docs/2026-04-25/repo-trashbox-low-risk-tracked-removal-manifest.md`
- `docs/2026-04-25/repo-trashbox-low-risk-removal-preflight-reaudit.md`
Evidence Artifacts:
- `.gitignore`
- `tests/test_surface_containment_contract.py`
- `docs/implementation/surface-containment-contract-v1.json`
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

Continue repository hygiene after the bounded repo-trashbox cleanup closure by targeting the largest remaining generated residue that is already excluded from future tracking: `test_mode/projects/` and `lite_mode/projects/`.

This SSOT does not authorize broad removal of `test_mode/`, `lite_mode/`, or `spikes/`. It authorizes only a dedicated follow-up PR for the two generated project trees named above.

## 2. Baseline Facts

Current live tracked inventory:

| Candidate | Tracked files | Bytes | Classification | First action |
| --- | ---: | ---: | --- | --- |
| `test_mode/projects/` | 1522 | 42091969 | generated project residue | manifest-bound `git rm` |
| `lite_mode/projects/` | 1522 | 42091969 | generated project residue | manifest-bound `git rm` |
| `test_mode/` total | 1554 | 42428086 | mixed manual source plus generated project residue | do not remove whole tree |
| `lite_mode/` total | 1554 | 42426849 | mixed manual source plus generated project residue | do not remove whole tree |
| `spikes/` | 7 | 26468 | prototype notes/code | preserve useful notes before cleanup |
| `temp*` tracked set | 11 | 1127159 | root/temp YouTube-test residue and helper scripts | separate follow-up manifest |

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

- `git rm -- test_mode/projects lite_mode/projects`
- contract/test update only if the current surface-containment test needs to assert absence after cleanup
- queue-state refresh and closure after validation

## 4. Excluded Scope

- `test_mode/` non-project manual helpers
- `lite_mode/` non-project manual helpers
- `spikes/`
- `temp*` root files and `temp/yt_test/`
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

- Future implementation deletes tracked generated project artifacts via Git.
- No local trashbox copy is created by default.

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

- Not applicable. `.gitignore` already prevents future generated project residue from re-entering the tracked surface.

## 8. Pass 3 - Execution Shape

Tranche 1 should be a single focused removal PR:

```text
git rm -- test_mode/projects lite_mode/projects
```

The PR must verify that:

- `git ls-files -- test_mode/projects lite_mode/projects` returns no files after removal
- `test_mode/bridge` and `lite_mode/bridge` remain tracked
- `.gitignore` still contains `test_mode/projects/` and `lite_mode/projects/`
- no runtime code changes are bundled

Tranche 2 may survey the remaining `temp*` tracked set, but it must not be bundled with Tranche 1.

Tranche 3 may handle `spikes/` only after useful `spikes/**/result.md` conclusions are preserved or explicitly judged unnecessary.

Pass 3 result: pass.

## 9. Acceptance Criteria

- `test_mode/projects/` has zero tracked files.
- `lite_mode/projects/` has zero tracked files.
- Non-project manual helper files under `test_mode/` and `lite_mode/` remain tracked.
- `spikes/` remains untouched.
- Root temp files remain untouched.
- `docs/temp/queue-state.json` reflects the active or closed state honestly.
- `python scripts/ops_validator.py --strict` passes.

## 10. Verification Plan

Before implementation:

- re-audit this SSOT against current `main`
- confirm `git ls-files -- test_mode/projects lite_mode/projects` still returns 3044 files

After implementation:

- `git ls-files -- test_mode/projects lite_mode/projects`
- `git ls-files -- test_mode/bridge lite_mode/bridge`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`
- `python scripts/check_utf8_hygiene.py docs/2026-04-25/repo-generated-project-residue-execution-ssot.md docs/temp/repo-generated-project-residue-execution-ssot.md docs/temp/queue-state.json tests/test_surface_containment_contract.py docs/implementation/surface-containment-contract-v1.json`
- `python -m pytest tests/test_surface_containment_contract.py tests/test_runtime_authority_contract.py -q`

## 11. Guardrails

- Do not delete all of `test_mode/`.
- Do not delete all of `lite_mode/`.
- Do not touch `spikes/` in the generated-project PR.
- Do not touch root `temp*` files in the generated-project PR.
- Do not treat old size estimates as authority when live `git ls-files -z` evidence differs.
- Do not proceed to cleanup without a fresh current-state re-audit of this SSOT.

## 12. Document 3-Pass Audit

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
