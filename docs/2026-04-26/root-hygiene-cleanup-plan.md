# Root Hygiene Cleanup Plan

Date: 2026-04-26
Status: final - planning only; no file move or deletion authorized
Canonical Path: `docs/2026-04-26/root-hygiene-cleanup-plan.md`
GitHub Issue: `https://github.com/temppppppppppppppppppppppp/devdev/issues/45`
Temp Mirror: not applicable; this is a cleanup plan, not an execution SSOT

Commit State:
- Baseline Branch: `main`
- Baseline Commit: `ef7a4b83a26550c1dc79772fc920070174db3f25`
- Baseline Dirty Summary: `0_temp.txt` modified by the active live run; `docs/2026-04-26/frontier-lag-5arc-live-run-watchlist.md` and `projects/0_골든카나리아/` untracked as live-run artifacts

Source Documents:
- `docs/2026-04-25/repo-trashbox-reference-check.md`
- `docs/2026-04-25/repo-root-temp-residue-removal-preflight-reaudit.md`
- `docs/2026-04-25/repo-generated-project-residue-execution-ssot.md`
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`

## 1. Purpose

This document is a human-facing root hygiene plan for non-critical clutter around the repository root.

It intentionally does not move, delete, ignore, or rewrite any file. Its job is to classify candidates and define the safest future order.

## 2. Hard Freeze While Frontier Lag Run Is Active

Do not touch these paths during the current 5-arc background run:

```text
0_temp.txt
projects/0_골든카나리아/
projects/0_골든카나리아/logs/
logs/frontier_lag_5arc_20260426_171121.out.log
logs/frontier_lag_5arc_20260426_171121.err.log
docs/2026-04-26/frontier-lag-5arc-live-run-watchlist.md
```

Reason:

- `0_temp.txt` is tracked, currently modified, and historically treated as an evidence anchor.
- `projects/0_골든카나리아/` is the live project output surface for the active run.
- live-run conclusions must wait for the terminal run state plus post-run merge audit.

## 3. Candidate Classification

| Path | Current state | Reference evidence | Cleanup class | Proposed action |
| --- | --- | --- | --- | --- |
| `0_temp.txt` | tracked, modified | preserved by 2026-04-25 root-temp preflight; active run context | freeze | Do not move or delete in this wave. Revisit only after a separate evidence-preservation decision. |
| `projects/0_골든카나리아/` | untracked live-run project | active 5-arc run output | freeze | Do not clean while run is active. Post-run audit decides what is durable evidence. |
| `temp_inspect.txt` | ignored local scratch | referenced only in 2026-04-25 trashbox docs | low-risk local scratch | After user confirmation, delete or move to `scratch/ignored/`; do not commit unless there is a clear reason. |
| `p1_rerun_1arc_input.txt` | tracked root file | referenced only in 2026-04-25 trashbox docs | tracked rerun residue | Move in a small later PR to `docs/archive/run-inputs/2026-04-26/` or `ops/run-inputs/archive/`, with docs references updated. |
| `ops_hardening_rerun_input.txt` | tracked root file | referenced only in 2026-04-25 trashbox docs | tracked rerun residue | Move together with `p1_rerun_1arc_input.txt`; keep the PR tiny and reversible. |
| `RESET.py` | tracked root tool | referenced by `tools2/*` and `modules/core/error_helper.py` | root tool, not trash | Do not move without a reference update and operator-path test. Candidate home: `scripts/dev/` or `tools/`. |
| `smoke_sc.py` | tracked root smoke tool | self-reference observed; script mutates `config/settings/validation.yaml` with atexit restore | risky smoke helper | Do not move or run casually. First document expected usage, then relocate to `scripts/smoke/` with a targeted smoke-run command. |
| `로직_리서치/` | tracked legacy research pointer tree | referenced by `material_ssot/*`, older docs, and collector README | legacy material-side pointer | Do not delete casually. Either keep as pointer-only root with clearer README, or migrate through a separate material-side registry update. |

## 4. Recommended Sequence

Phase 0 - live-run-safe freeze:

- Do nothing to `0_temp.txt`, live project outputs, or live logs until the Frontier Lag run reaches a terminal state.
- Keep this plan documentation-only.

Phase 1 - local scratch cleanup:

- Confirm whether `temp_inspect.txt` is still useful to the user.
- If not useful, delete locally because it is ignored and not tracked.
- If it should be preserved, move it to a clearly ignored scratch area rather than committing it.

Phase 2 - rerun input residue PR:

- Move only `p1_rerun_1arc_input.txt` and `ops_hardening_rerun_input.txt`.
- Update references in the 2026-04-25 trashbox document if needed.
- Validate with `git status --short`, `rg`, and UTF-8 hygiene for touched docs.

Phase 3 - root tool relocation plan:

- Treat `RESET.py` and `smoke_sc.py` as tools, not trash.
- Before moving, inspect caller expectations and operator documentation.
- If moved, use a separate PR and add a compatibility note or explicit new command path.

Phase 4 - `로직_리서치/` legacy decision:

- Treat this as material-side governance cleanup, not simple file cleanup.
- If migrating, update the material-side registry and all references in the same small PR.
- If not migrating, make `로직_리서치/README.md` explicitly say it is a legacy pointer surface and not canonical authority.

## 5. Non-Goals

This plan does not authorize:

- deleting `0_temp.txt`
- cleaning active `projects/0_골든카나리아/` output
- deleting or moving live-run logs
- moving `로직_리서치/` without material-side reference updates
- moving `RESET.py` or `smoke_sc.py` without operator-path validation
- changing `.gitignore`
- opening a broad repo-trashbox cleanup wave

## 6. Validation For Future Cleanup

Before any future cleanup PR:

```powershell
git status --short --branch
rg --fixed-strings -l -- "p1_rerun_1arc_input.txt"
rg --fixed-strings -l -- "ops_hardening_rerun_input.txt"
rg --fixed-strings -l -- "RESET.py"
rg --fixed-strings -l -- "smoke_sc.py"
rg --fixed-strings -l -- "로직_리서치"
python scripts/check_utf8_hygiene.py <touched-docs-or-code>
```

If the cleanup touches executable Python:

```powershell
python -m py_compile <touched-python-files>
```

If the cleanup touches operator-facing docs or root containment rules, also run the surface-containment validation that is current at that time.

## 7. Adversarial Audit Pass 1 - Overreach Attack

Attack question:

Could this plan accidentally authorize deletion or movement of active run evidence?

Finding:

- The plan explicitly freezes `0_temp.txt`, `projects/0_골든카나리아/`, live-run logs, and the live-run watchlist.
- The plan is marked planning-only and authorizes no mutation.
- Live-run final conclusions are deferred until terminal state plus post-run merge audit.

Pass 1 result: pass.

## 8. Adversarial Audit Pass 2 - Reference Integrity Attack

Attack question:

Could a future cleanup break references or operator commands because the plan classifies something too aggressively as trash?

Finding:

- `RESET.py` and `smoke_sc.py` are not classified as trash.
- `로직_리서치/` is not classified as safe deletion because many material-side references exist.
- The two rerun input files are classified as small tracked residue only because current evidence found references limited to prior trashbox docs.
- Future movement still requires a fresh `rg` reference check before mutation.

Pass 2 result: pass.

## 9. Adversarial Audit Pass 3 - Human Operations Attack

Attack question:

Could this create cognitive load, a giant cleanup wave, or an irreversible change path?

Finding:

- The sequence is split into small phases.
- Phase 1 is local scratch only.
- Phase 2 is a tiny tracked-file move PR.
- Tool relocation and material-side legacy migration are separated and deferred.
- Rollback for future tracked-file moves is normal Git revert.

Pass 3 result: pass.

## 10. Confidence Gate

Confidence: 96/100.

Reason:

- Claims are bounded to inspected tracked state, ignored state, prior dated docs, and reference scans.
- The plan avoids destructive action while the live run is active.
- The main uncertainty is whether the user personally wants to keep `temp_inspect.txt`; that uncertainty is explicitly left for confirmation before any local cleanup.
