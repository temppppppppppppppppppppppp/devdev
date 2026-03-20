# ROL Global Live-Run Merge Audit Order

Date: 2026-03-20
Status: final
Canonical Path: `docs/2026-03-20/rol-global-live-run-merge-audit-order.md`
Related Survey Backbone: `docs/2026-03-20/rol-global-integrity-survey-3pass-audit.md`
Related Evidence Manifest: `docs/2026-03-20/rol-global-integrity-evidence-manifest.md`
Mode: `live-merge`
Commit State:
- Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
- Baseline Dirty Summary: `dirty: 128 tracked/other, 17 untracked; hotspots: geuldobi-desktop/, modules/core/, modules/domain/agents/, docs/2026-03-20/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Intent

이 order는 전역 static survey backbone 위에 `fresh live run + post-run merge audit`를 얹기 위한 bounded 실행 지시다.

목표:
- static survey에서 남은 큰 빈칸을 live evidence로 메운다
- collector draft의 stale/noise를 completed run evidence로 다시 걸러낸다
- final canonical survey confidence를 95% 쪽으로 끌어올린다

이번 order는 아직 execution SSOT realization이 아니다.
이번 order의 산출물은 watchlist, raw evidence, post-run merge audit이다.

## 2. Governing Rules

- `docs/implementation/live-run-merge-survey-harness.md`를 따른다
- run 완료 전에는 final closure claim을 저장하지 않는다
- run 중에는 raw evidence와 draft watchlist만 확정한다
- `docs/temp/` mirror는 이번 order에서 새로 만들지 않는다
- 기존 unrelated temp item은 그대로 둔다

## 3. Scope Lock

### Included live surfaces

- desktop/operator shell proof
- Stage 2 smoke
- Stage 3 smoke
- Stage 4 smoke
- bridge/process runner/desktop linkage evidence
- produced logs / JSONL / summary artifacts from these bounded runs

### Excluded from default run set

- full canary proof by default
- repo-wide expensive real API proof runs
- prompt ownership refactor or runtime authority changes
- execution SSOT creation during active run

### Escalation-only surfaces

- `scripts/run_stage4_canary.py`
- `scripts/run_stage34_canary.py`
- `scripts/e2e_menu_smoke.ps1`

이 셋은 anomaly가 잡혔을 때만 2차로 올린다.

## 4. Recommended Minimal Sample Set

### Lane R1. Desktop Spike

Purpose:
- operator shell / preload / bridge / renderer boot
- desktop-contract surfaces

Entry:
- `cd geuldobi-desktop`
- `npm run start:desktop-spike`

Evidence targets:
- app boot success/failure
- bridge startup
- renderer quality/operator surface rendering
- desktop logs if emitted

### Lane R2. Stage 2 Smoke

Purpose:
- Stage 2 runtime skeleton
- arc generation / persistence / Stage2 sink activity

Entry:
- `python scripts/run_stage2_smoke.py`

Evidence targets:
- stdout/stderr
- smoke output status
- DB / JSONL side effects if produced

### Lane R3. Stage 3 Smoke

Purpose:
- Stage 3 blueprint path
- quality dashboard / Stage3 sink behavior

Entry:
- `python scripts/run_stage3_smoke.py`

Evidence targets:
- stdout/stderr
- Stage3 outputs
- quality dashboard related sinks and summaries

### Lane R4. Stage 4 Smoke

Purpose:
- Stage 4 manuscript path
- interview/post-processor/proof-facing sink behavior

Entry:
- `python scripts/run_stage4_smoke.py`

Evidence targets:
- stdout/stderr
- stage4 logs
- manuscript/proof/summary artifacts if produced

## 5. Escalation Rule

기본 4-lane run에서 아래가 발생하면 canary로 올린다.

- smoke가 fail 또는 abort
- sink mismatch
- expected artifact missing
- operator shell and backend state disagreement
- Stage 4 proof-facing sink discrepancy
- control-plane provenance mismatch

Escalation order:
1. `scripts/run_stage4_canary.py`
2. `scripts/run_stage34_canary.py`
3. `scripts/e2e_menu_smoke.ps1`

## 6. Pre-Run Watchlist

run 전에 아래 항목을 draft watchlist로 고정한다.

- desktop preload method / gate inventory drift
- bridge/process runner authority chain
- Stage 2 sink coverage and sink alignment gap
- Stage 3 `PASS_WITH_WARNING` / quality signals persistence
- Stage 4 proof digest / companion audit / post-processor sink integrity
- control-plane provenance vs companion snapshots
- script mutation boundaries and persistent artifact leftovers

## 7. Evidence Capture Policy

### Save during run

- raw terminal output
- bounded stdout/stderr captures
- produced JSONL/log/summaries
- DB row-count snapshots or narrow evidence snapshots
- operator notes with terminal-state markers

### Do not finalize during run

- canonical survey closure
- execution SSOT
- roadmap
- resolved/regressed claims

## 8. Post-Run Merge Audit Targets

run 완료 후 아래를 다시 비교한다.

- static watchlist vs actual produced evidence
- collector draft claims vs completed run evidence
- sink inventory vs actual writes
- desktop/operator expectations vs actual shell behavior
- Stage 2/3/4 result summaries vs contract tests

## 9. Suggested Output Set

- `docs/2026-03-20/rol-global-live-run-preflight-watchlist.md`
- `docs/2026-03-20/rol-global-live-run-evidence-manifest.md`
- `docs/2026-03-20/rol-global-live-run-evidence.txt`
- `docs/2026-03-20/rol-global-post-run-merge-audit.md`

execution SSOT and roadmap는 post-run merge audit 결과 action-bearing area가 2개 이상일 때만 만든다.

## 10. Confidence Gate

현재 order confidence: `0.96`

근거:
- live-run merge harness와 global survey harness를 다시 읽었다
- 현재 workspace의 run/canary entrypoints를 live code에서 다시 확인했다
- desktop spike, Stage2/3/4 smoke, canary escalation surfaces를 모두 직접 확인했다
- high-cost canary를 기본 run set에서 제외해 bounded order로 줄였다

## 11. Immediate Next Action

다음 실제 실행 순서:

1. `rol-global-live-run-preflight-watchlist.md` 작성
2. R1~R4 run 수행
3. raw evidence 저장
4. `rol-global-post-run-merge-audit.md` 작성
