# ROL Live-Run Fixture Target Selection Audit

Date: 2026-03-20
Status: final
Canonical Path: `docs/2026-03-20/rol-live-run-fixture-target-selection-audit.md`
Related Order: `docs/2026-03-20/rol-global-live-run-merge-audit-order.md`
Related Watchlist: `docs/2026-03-20/rol-global-live-run-preflight-watchlist.md`
Commit State:
- Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
- Baseline Dirty Summary: `dirty: 128 tracked/other, 17 untracked; hotspots: geuldobi-desktop/, modules/core/, modules/domain/agents/, docs/2026-03-20/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Question

`desktop spike + Stage2/3/4 smoke` live-merge order를 진행하려면,

- 비어 있는 `projects/코덱스_테스트`를 되살릴지
- 다른 seeded project를 run target으로 쓸지

를 먼저 정해야 했다.

## 2. Live Findings

### 2.1 Current smoke target

`scripts/run_stage2_smoke.py`, `scripts/run_stage3_smoke.py`, `scripts/run_stage4_smoke.py`는 모두 hardcoded target으로:

- `PROJECT_NAME = "코덱스_테스트"`
- `DB_PATH = projects/코덱스_테스트/project_data.db`

를 전제한다.

현재 live filesystem:

- `projects/코덱스_테스트/` exists
- `projects/코덱스_테스트/project_data.db` missing
- `plans/arcs`, `plans/blueprints`, `plans/manuscripts` missing

즉 현재 상태 그대로는 smoke run이 blocked다.

### 2.2 Candidate alternatives

#### Candidate A. `projects/0`

- exists
- but `project_data.db` missing
- smoke target로는 부적합

#### Candidate B. `projects/0_260318`

- `project_data.db` exists
- `plans/arcs` exists
- `plans/blueprints` exists
- `plans/manuscripts` missing

이 경로는 live audit용 historic project로는 유용하지만,
smoke script가 hardcoded로 `코덱스_테스트`를 가리키고 있고,
packaged sample/desktop seed와도 직접 연결되지 않는다.

#### Candidate C. `dist/workspace-seed/projects/investment_canary_demo`

live 확인 결과:
- `project_data.db` exists
- `plans/arcs` exists
- `plans/blueprints` exists
- `logs` exists
- `plans/manuscripts`는 없지만 Stage4 smoke가 생성 가능
- DB live check:
  - `blueprints`: `7`
  - `manuscripts`: `6`
  - `bible` anchor present
  - `arcs` anchor present (`2` arcs)

또한 이 경로는:
- desktop workspace seed가 공식적으로 stage하는 sample project이고
- `geuldobi-desktop/scripts/build_workspace_seed.py`와
- `dist/workspace-seed/seed-manifest.json`
- `geuldobi-desktop/DESKTOP-GUIDE.md`

와도 정렬된다.

## 3. Decision

추천 경로는 `Candidate C`다.

정확한 방식:
- smoke script는 그대로 둔다
- `dist/workspace-seed/projects/investment_canary_demo`를
  임시 live-run fixture clone으로
  `projects/코덱스_테스트`에 복구/대체한다

이 방식이 좋은 이유:
- smoke script를 패치할 필요가 없다
- packaged seed와 같은 계열의 sample project를 쓴다
- Stage2/3/4 smoke prerequisite를 모두 거의 충족한다
- `0_260318` 같은 historical audit project를 live-run fixture로 오염시키지 않는다

## 4. Rejected Paths

### 4.1 Hard-patching smoke scripts to another project

이번 단계에서는 비추천.

이유:
- survey/live-run 준비 단계인데 code patch를 늘린다
- smoke script contract를 unnecessary하게 흔든다

### 4.2 Using `0_260318` directly

이번 단계에서는 비추천.

이유:
- historical audit 대상 project다
- packaged sample lineage와도 다르다
- live-run fixture로 쓰면 later audit provenance가 혼합된다

## 5. Recommended Next Action

다음 bounded action:

1. 기존 `projects/코덱스_테스트`는 backup or rename
2. `dist/workspace-seed/projects/investment_canary_demo`를 `projects/코덱스_테스트`로 clone
3. 그 다음 `R1 desktop spike`, `R2/R3/R4 smoke` 순서로 run

## 6. Confidence

현재 confidence: `0.97`

근거:
- smoke scripts 3개와 desktop workspace seed builder를 직접 읽었다
- current project directories와 seeded project surfaces를 live filesystem으로 확인했다
- seeded sample DB inside counts and anchor presence를 직접 확인했다
- code patch 없이 smoke contract를 유지하는 path를 선택했다
