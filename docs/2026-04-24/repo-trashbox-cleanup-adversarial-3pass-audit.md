# Repo Trashbox Cleanup Adversarial 3-Pass Audit

Date: 2026-04-24
Status: final (parking audit; no file move authorized)
Canonical Path: `docs/2026-04-24/repo-trashbox-cleanup-adversarial-3pass-audit.md`
Source Survey: `docs/2026-04-24/repo-trashbox-candidate-survey.md`
Target Holding Area: `C:\Users\wjjo\Desktop\글도비_쓰레기통`

## 1. Audit Question

Can the repository hygiene cleanup be turned into an execution lane without accidentally moving real runtime surfaces, breaking Git tracking, or hiding security-review evidence?

Decision:

- Yes, but only as a parked future wave.
- No physical move, delete, `git rm`, packaging change, or history cleanup is authorized by this audit.
- Canary output is not part of this cleanup lane; it is handled by `docs/2026-04-24/canary-root-isolation-execution-ssot.md`.

## 2. Pass 1 - Classification Attack

Adversarial question:

What if a noisy path is actually active workflow state?

Findings:

- `tests/` must stay in the repo. It is the formal pytest suite, not trash.
- `docs/temp/` must stay visible while active. Despite the name, it is the operational queue mirror used by queue tooling and validators.
- `modules/`, `scripts/`, `geuldobi-desktop/`, `contracts/`, and `config/` remain production or support surfaces.
- `projects/_canary/` is noisy, but a blind move would violate current canary path assumptions.

Safe conclusion:

- The trashbox lane should target only maintenance-only/manual/experimental residue after a fresh reference check.
- The first intended candidates remain `test_mode/`, `lite_mode/`, `spikes/`, `MagicMock/`, `tmp_stage2_digest_debug/`, test project data, and root temp/result residue.
- Canary output must stay out of the trashbox move set until the canary-root-isolation lane is implemented or explicitly superseded.

Pass 1 result: pass with constraints.

## 3. Pass 2 - Git And Destructive-Operation Attack

Adversarial question:

What if a cleanup move silently breaks tracked history, reviewability, or local recovery?

Findings:

- `test_mode/` and `lite_mode/` contain many tracked files. A simple file-system move would leave Git in a large delete/add state.
- Moving tracked artifacts outside the repo requires an explicit Git policy decision:
  - keep history and remove from active tree with `git rm --cached`
  - move to another tracked archive
  - preserve only conclusions as docs
  - leave local-only quarantine outside Git
- Root temp/result files need per-file treatment because some may be tracked evidence while others are local run residue.
- `글도비_쓰레기통` should not become a second unmanaged source repository.

Safe conclusion:

- Future execution must begin with a reference scan and a Git tracking table before moving anything.
- Use copy/quarantine plus verification first when a path has uncertain references.
- Do not delete original material until the user explicitly approves a cleanup commit strategy.

Pass 2 result: pass with constraints.

## 4. Pass 3 - Packaging And Security-Review Attack

Adversarial question:

What if the cleanup makes the security review cleaner visually but leaves packaging or secret-handling risk unchanged?

Findings:

- `modules/core/runtime_paths.py` already labels `lite_mode/` and `test_mode/` as maintenance-only, not supported runtime.
- `배포_패키징.ps1` excludes several noisy surfaces including `projects`, `test_mode`, `rlhf_data`, and `datasets`, but `lite_mode` needs explicit packaging-scope review before any future security response claims are made.
- `geuldobi-vertex-key.json` is already excluded locally and has also been added to `.gitignore`.
- Canary generated output needs separate ignore/root policy rather than a trashbox move.
- ClickUp and GitHub issue visibility do not replace repo-side canonical docs.

Safe conclusion:

- The trashbox lane should include a packaging-scan tranche.
- Security response language should say "surveyed and classified" until the actual quarantine move and packaging scope updates are implemented.
- The repo-side docs remain the SSOT for why something was kept, moved, or ignored.

Pass 3 result: pass with constraints.

## 5. Execution Readiness Verdict

Verdict: execution-ready, parked future wave.

Confidence: 95/100.

Reasons confidence is not higher:

- Some candidates are tracked and may need Git policy decisions.
- `lite_mode` packaging visibility needs a focused check.
- Canary cleanup is intentionally split into a separate lane, so broad repository cleanup must wait on or consciously exclude that lane.

## 6. Hard Guardrails

- Do not move `tests/`.
- Do not move `docs/temp/` as arbitrary temp residue.
- Do not move `projects/_canary/` through this lane.
- Do not delete candidate files as part of the first execution tranche.
- Do not claim GitHub Issues or ClickUp are automatic SSOT mirrors.
- Do not run broad cleanup without `python scripts/ops_validator.py --strict` passing after document and queue updates.
