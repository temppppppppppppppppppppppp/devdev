Date: 2026-03-16
Status: final
Canonical Path: `docs/2026-03-16/release-1.5.6-desktop-workspace-seed-bounded-audit.md`
Evidence Artifact: `docs/2026-03-16/release-1.5.6-desktop-workspace-seed-bounded-audit-evidence.txt`

Commit State:
- Baseline Commit: `d6c81c1976d9812d447c2a78e2aeb36f7aed666a`
- Baseline Dirty Summary: `dirty: 53 tracked, 57 untracked; hotspots: docs/2026-03-15/backend-front-control-plane-connectivity-remediation-execution-ssot.md, docs/2026-03-15/codebase-global-cleanroom-source-only-execution-roadmap.md, docs/2026-03-15/opus/3pass-audit-master-summary.md, docs/implementation/desktop-runtime-contract-v1.json, geuldobi-desktop/DESKTOP-GUIDE.md, geuldobi-desktop/package-lock.json`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

# 1. Scope
This is a bounded release audit for the `1.5.6` desktop rebuild only.

Included surfaces:
- version bump and packaging contract
- packaged workspace-seed staging
- packaged artifact presence in `dist/` and `win-unpacked/`
- packaged runtime smoke for missing-only seed copy

Excluded surfaces:
- installer click-through UX
- full story-generation runtime
- unrelated historical docs and queues

# 2. Executive Verdict
The `1.5.6` release package is structurally correct and the packaged sample materials are present in the build output. Static contract checks, artifact checks, and targeted desktop regression all passed.

The only unresolved item is packaged first-run runtime proof. During this audit, `win-unpacked/Geuldobi.exe` exited with code `0`, but it did not append a fresh packaged boot breadcrumb to `%LOCALAPPDATA%\Geuldobi\electron-main.log` and it did not create the missing sample files under `C:\Users\User\Documents\글도비`. That means the release artifact is built correctly, but first-run seed copy behavior is not yet empirically proven in this bounded audit.

Operational verdict:
- `build integrity`: pass
- `packaged content inclusion`: pass
- `packaged first-run seed proof`: inconclusive

# 3. Pass 1 Summary: Structure and Scope
The release change is scoped correctly:
- [package.json](c:\Users\User\Desktop\글도비\geuldobi-desktop\package.json) is `1.5.6`
- [package-lock.json](c:\Users\User\Desktop\글도비\geuldobi-desktop\package-lock.json) matches
- [main.js](c:\Users\User\Desktop\글도비\geuldobi-desktop\src\main.js) owns packaged seed sync
- [build_workspace_seed.py](c:\Users\User\Desktop\글도비\geuldobi-desktop\scripts\build_workspace_seed.py) stages the canary BI/TR and `projects/0`
- [build_release.ps1](c:\Users\User\Desktop\글도비\build\build_release.ps1) rebuilds backend, engine, and installer
- [desktop-runtime-contract-v1.json](c:\Users\User\Desktop\글도비\docs\implementation\desktop-runtime-contract-v1.json) includes `workspace-seed/seed-manifest.json`

This audit did not create or modify any execution SSOT queue items. `docs/temp/` remained non-queue state with [README.md](c:\Users\User\Desktop\글도비\docs\temp\README.md) only.

# 4. Pass 2 Summary: Evidence and Artifact Consistency
Packaged sample materials are present and coherent.

Confirmed inclusions:
- [Geuldobi Setup 1.5.6.exe](c:\Users\User\Desktop\글도비\geuldobi-desktop\dist\Geuldobi%20Setup%201.5.6.exe)
- [seed-manifest.json](c:\Users\User\Desktop\글도비\geuldobi-desktop\dist\win-unpacked\resources\workspace-seed\seed-manifest.json)
- [01_bi_투자물_골든_카나리아 테스트.json](c:\Users\User\Desktop\글도비\geuldobi-desktop\dist\win-unpacked\resources\workspace-seed\bible\01_bi_투자물_골든_카나리아%20테스트.json)
- [01_tr_투자물_골든_카나리아 테스트.json](c:\Users\User\Desktop\글도비\geuldobi-desktop\dist\win-unpacked\resources\workspace-seed\treatments\01_tr_투자물_골든_카나리아%20테스트.json)
- [investment_canary_demo](c:\Users\User\Desktop\글도비\geuldobi-desktop\dist\win-unpacked\resources\workspace-seed\projects\investment_canary_demo)

The packaged seed payload is not stubbed. It includes:
- `project_data.db`
- `drafts/ep_0001.txt` through `drafts/ep_0006.txt`
- Stage 2/3/4 artifacts
- `stage0_output/style_guide.json`
- `author_directives.txt`

`app.asar` also contains the new packaged branch, not just the source tree:
- `syncPackagedWorkspaceSeed`
- `copyMissingTree`
- `path.join(process.resourcesPath, "workspace-seed")`
- the `["bible", "treatments", "projects"]` folder loop

That is enough to conclude the build artifact itself contains the intended seed-sync code and payload.

# 5. Pass 3 Summary: Runtime Smoke
The runtime pass was bounded to a packaged smoke using `win-unpacked/Geuldobi.exe`.

Pre-smoke state:
- `C:\Users\User\Documents\글도비\bible\01_bi_투자물_골든_카나리아 테스트.json` was missing
- `C:\Users\User\Documents\글도비\treatments\01_tr_투자물_골든_카나리아 테스트.json` was missing
- `C:\Users\User\Documents\글도비\projects\investment_canary_demo` was missing

Smoke result:
- the packaged process exited with code `0`
- no fresh packaged boot breadcrumb appeared in `%LOCALAPPDATA%\Geuldobi\electron-main.log`
- the three missing seed targets remained missing
- repeating the smoke with `win-unpacked` as the working directory produced the same result

This does not prove the packaged seed branch is broken, but it does mean the audit could not observe it executing successfully on this machine in the bounded smoke window.

# 6. Risk Assessment
Current release risk is asymmetric.

Low-risk / supported:
- versioning and packaging metadata
- seed staging script
- inclusion of sample BI/TR/project materials in build output
- static desktop contract and bridge regressions

Open risk:
- packaged first-run seed copy is not yet runtime-proven
- there is no direct automated test covering the `app.isPackaged` branch against the real `Documents\글도비` target on this machine

# 7. Recommended Next Step
Do one targeted packaged-startup debug pass before treating `1.5.6` as fully signed off for sample-seed behavior.

Recommended bounded follow-up:
1. Add one packaged-boot breadcrumb that cannot be missed before `syncPackagedWorkspaceSeed()`
2. Re-run `win-unpacked/Geuldobi.exe` smoke
3. Confirm either:
   - seed files appear in `Documents\글도비`, or
   - a precise failure breadcrumb is written to the desktop log

No new execution SSOT was opened in this audit because the user asked for audit/revalidation, not a new patch queue.

# 8. Confidence
Estimated confidence: `97%`

Why this clears the save gate:
- the conclusion is bounded to observed evidence
- artifact inclusion claims are directly verified
- the unresolved runtime point is explicitly disclosed, not hand-waved
- the document is safe to use as an operator readout of current `1.5.6` release state
