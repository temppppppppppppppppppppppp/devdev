# Repository Trashbox Candidate Survey

Date: 2026-04-24

## Purpose

This note records directories and files that should not stay in the operator's normal field of view when working on the Geuldobi production pipeline.

The goal is not immediate deletion. The goal is to separate production code, formal tests, operational queue files, and old experiment/runtime residue so repository review and security review do not have to wade through unrelated material.

Proposed local holding area name:

```text
C:\Users\wjjo\Desktop\글도비_쓰레기통
```

## Keep In Main Repo

| Path | Reason |
| --- | --- |
| `tests/` | Formal pytest regression suite. This is the one official test surface. |
| `docs/temp/` | Hold. Despite the name, this is tied to the active operational queue/roadmap mirror. `scripts/ops_validator.py` and queue tooling refer to it directly. |
| `modules/`, `scripts/`, `geuldobi-desktop/`, `contracts/`, `config/` | Production/runtime/supporting code surfaces. |

## Primary Trashbox Candidates

| Path | Observed Size | Tracked Files | Reason |
| --- | ---: | ---: | --- |
| `test_mode/` | ~40.46 MB | 917 | Manual/experimental mode, not part of supported runtime. `modules/core/runtime_paths.py` already labels it maintenance-only. |
| `lite_mode/` | ~40.68 MB | 917 | Separate lightweight/legacy experiment surface, not part of supported runtime. It also risks accidental packaging visibility if not explicitly excluded. |
| `spikes/` | ~53.08 MB | 7 | One-off technical probes. Useful conclusions can be kept as notes, but build/dist outputs and prototype code should not sit in the normal source view. |
| `MagicMock/` | ~0 MB | 2 | Mock/runtime residue, not production source. |
| `tmp_stage2_digest_debug/` | ~0.37 MB | 6 | Debug residue. |
| `rlhf_data/test_project/` | ~0 MB | 6 | Test project data, not production source. |
| `datasets/test_project/` | ~0.04 MB | 3 | Test fixture/project data, not production source. |
| root temp/result files | mixed | 22 | `0_temp.txt`, `temp.txt`, `temp_시리즈.txt`, `temp_triage_test.json`, `test_results.xml`, `tmp_project_00*.db`, crash/error logs, and similar local run residue. |

## Canary Position

`projects/_canary/` is noisy and large:

```text
projects/_canary/
  approx size: 933.61 MB
  tracked files: 3,825
```

However, do not migrate it as part of the first cleanup pass.

Reason: current helper code, especially `scripts/canary_path_utils.py`, assumes the canary root is under `projects/_canary`. Moving it safely would require a small runtime/config change, not just file relocation.

Current decision:

- Keep canary migration on hold.
- Treat old canary outputs as visual noise and repository hygiene debt.
- Isolate future canary output through the separate plan in `docs/2026-04-24/canary-root-isolation-plan.md`.
- Do not move old runs until the new root is proven and a separate cleanup decision is made.

## Cleanup Principle

Use this split:

```text
Geuldobi repo
  production code
  formal tests
  current docs
  active operational queue mirrors

글도비_쓰레기통
  retired manual modes
  old experiments
  local debug residue
  generated test/demo project data
```

Do not treat `글도비_쓰레기통` as a permanent archive. It is a quarantine area for things that should stop cluttering the main repository view. If something in it becomes important again, promote it intentionally into a named supported surface.

## First Safe Move Set

If cleanup work is approved later, the safest first move set is:

1. Move `test_mode/` to `C:\Users\wjjo\Desktop\글도비_쓰레기통\test_mode`.
2. Move `lite_mode/` to `C:\Users\wjjo\Desktop\글도비_쓰레기통\lite_mode`.
3. Move `spikes/` to `C:\Users\wjjo\Desktop\글도비_쓰레기통\spikes`, or preserve only `spikes/**/result.md` as docs and quarantine the rest.
4. Move local root temp/result files into `C:\Users\wjjo\Desktop\글도비_쓰레기통\root_residue`.
5. Add or strengthen ignore rules after moving.

Before changing Git tracking, run a reference check for each candidate path and separate:

- working tree move only
- `git rm --cached` cleanup
- docs-only preservation
- runtime/config change needed

## Security Review Response Framing

Recommended response language:

> The formal automated test suite is isolated under `tests/`. Legacy manual modes, experimental probes, local debug outputs, and generated canary/project artifacts have been surveyed and classified for repository hygiene cleanup. Operational queue mirrors under `docs/temp/` are intentionally retained because they are active workflow state, not arbitrary temporary files.
