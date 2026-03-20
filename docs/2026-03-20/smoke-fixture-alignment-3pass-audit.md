# Smoke Fixture Alignment — 3Pass Audit

Date: 2026-03-20
Status: final
Canonical Path: `docs/2026-03-20/smoke-fixture-alignment-3pass-audit.md`
Source Survey Docs:
- `docs/2026-03-20/rol-global-live-run-preflight-watchlist.md`
- `docs/2026-03-20/rol-live-run-fixture-target-selection-audit.md`
- `docs/2026-03-20/rol-global-live-run-evidence-manifest.md`
- `docs/2026-03-20/rol-global-post-run-merge-audit.md`
Evidence Artifacts:
- `projects/코덱스_테스트__seed_live_run_capture_20260320_092956/`
- `projects/코덱스_테스트/`
- `scripts/run_stage2_smoke.py`
- `scripts/run_stage3_smoke.py`
- `scripts/run_stage4_smoke.py`
- `geuldobi-desktop/scripts/build_workspace_seed.py`
Commit State:
- Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
- Baseline Dirty Summary: `dirty: 128 tracked/other, 17 untracked; hotspots: geuldobi-desktop/, modules/core/, modules/domain/agents/, docs/2026-03-20/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Intent

이 문서는 `desktop spike + Stage2/3/4 smoke` live-merge 결과를 바탕으로,
현재 smoke fixture contract가 실제 seeded sample과 어떻게 어긋나는지 고정한다.

이 문서는 아직 execution SSOT가 아니다.
먼저 문제의 shape와 추천 방향을 bounded하게 잠그는 역할을 한다.

## 2. Stable Facts

- smoke scripts 3개는 모두 hardcoded target으로 `projects/코덱스_테스트`를 기대한다
- current packaged/sample seed lineage는 `investment_canary_demo`다
- `investment_canary_demo` disposable clone은:
  - desktop spike: usable
  - Stage4 smoke: usable
  - Stage3 smoke: unusable as-is (`arcs=2`)
- richer disposable clone (`0_260318` derived)은 Stage3 smoke를 통과시켰다
- Stage2 smoke on seed-based clone은 terminal 완료는 했지만 실제 export는 2 arcs만 남겼고 `arc_3_failure_report.txt`를 생성했다

## 3. Problem Statement

현재 문제는 `코덱스_테스트 DB missing` 하나가 아니다.

더 본질적인 문제는 아래 셋이 같은 contract로 맞물려 있지 않다는 점이다.

1. smoke script hardcoded target name
2. desktop/package workspace seed lineage
3. Stage2/3/4 smoke가 요구하는 fixture richness

즉 nominal contract는 하나인데, 실제 요구사항은 lane별로 다르다.

## 4. Lane-by-Lane Reading

### Desktop spike

의미:
- lightweight operator/control-plane proof

현재 fixture 의존성:
- 거의 없음

판정:
- current seed lineage와 정렬됨

### Stage2 smoke

의미:
- Stage2 bounded mutation proof

현재 fixture 의존성:
- Bible
- `plot_roadmap`
- usable `arcs` anchor or ability to derive/export arcs

live finding:
- seed-based clone에서 completed로 끝났지만 3-block expectation을 충족했다고 보기 어렵다

### Stage3 smoke

의미:
- Stage3 blueprint path bounded proof

현재 fixture 의존성:
- `arcs >= 3`

live finding:
- seed-based clone은 이 전제를 못 맞춘다

### Stage4 smoke

의미:
- Stage4 manuscript path bounded proof

현재 fixture 의존성:
- `arcs >= 1`
- `blueprints >= 3`

live finding:
- seed-based clone과 정렬된다

## 5. Interpretation

현재 smoke stack은 “하나의 공식 disposable fixture”를 전제하는 것처럼 보이지만,
실제로는 그렇지 않다.

현재 상태는 아래 중간형에 가깝다.

- desktop + Stage4는 seed sample에 맞춰져 있음
- Stage3는 richer project를 요구함
- Stage2는 seed sample로도 돌긴 하지만 proof quality가 애매함

따라서 `same fixture contract`라는 외형과
`different richness expectations`라는 실질이 어긋난 상태다.

## 6. Recommended Direction

추천 순서는 이렇다.

### 1순위. 공식 smoke fixture를 하나 세운다

요건:
- `코덱스_테스트` lineage를 유지하거나 같은 역할의 canonical disposable project를 만든다
- 최소한 Stage2/3/4 smoke가 모두 같은 fixture contract에서 돌 수 있어야 한다
- `arcs >= 3`, `blueprints >= 3`, clean manuscript reset semantics를 명시한다

### 2순위. seed builder와 smoke fixture contract를 정렬한다

선택지:
- `investment_canary_demo`를 richer sample로 강화
- 또는 별도의 `smoke_fixture_demo` 계열을 packaged seed에 포함

### 3순위. hardcoded target name을 parameterize한다

이건 유용하지만 1순위는 아니다.
먼저 canonical disposable fixture contract가 있어야 parameterization도 의미가 있다.

## 7. Explicit Non-Recommendations

- `0_260318` 같은 historical audit project를 direct smoke target으로 쓰는 것
- smoke script를 먼저 임시 패치해서 다른 프로젝트 이름으로 돌리는 것
- lane별로 서로 다른 hidden fixture를 계속 쓰면서 nominal target name만 유지하는 것

## 8. Action-Bearing Outcome

이 audit 기준으로 다음 bounded execution topic은 하나다.

- `smoke-fixture-alignment`

추천 implementation shape:
- official disposable smoke fixture contract 정의
- builder/seed와 smoke scripts 전제를 맞춤
- Stage2/3/4 smoke가 동일 lineage fixture에서 반복 가능하도록 정렬

## 9. Confidence

현재 confidence: `0.97`

근거:
- desktop spike, Stage2/3/4 smoke를 실제로 실행했다
- seed-based disposable fixture와 richer disposable fixture를 모두 써 봤다
- blocked/partial/completed lane를 실제 artifact와 terminal-state로 확인했다
- 결론을 fixture alignment 하나로 제한했다
