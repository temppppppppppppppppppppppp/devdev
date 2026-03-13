# main_a Live Wiring Contract Detail Consolidated Findings

> 작성일: 2026-03-13
> 상태: `executed / consolidated`
> 범위: `MLW-T1` .. `MLW-T5`
> 기준 오더: `main_a-live-wiring-contract-detail-full-survey-audit-order.md`
> 정정 결과: `총 21건 (P0 2 / P1 3 / P2 11 / P3 5)`

이번 통합본은 `main_a.py` live wiring / facade / `from_app()` / runtime bridge surface에 대한
T1~T5 결과를 한데 묶은 SSOT다. 핵심은 "mock green"과 "real app green"이 다르다는 점이며,
특히 Stage4 real entry, Stage2/Stage3/Stage4 context pinning, protocol/runtime bridge split이
같은 축에서 반복 확인됐다.

## Terminal Summary

| Terminal | 문서 | 최종 건수 | 핵심 주제 |
|----------|------|-----------|-----------|
| T1 | `MLW-T1-stage2-real-app-binding-findings.md` | 4 | Stage2 real path proof gap, cache/write-back asymmetry |
| T2 | `MLW-T2-stage3-real-app-binding-findings.md` | 4 | Stage3 real-app slot drift, unspecced mock false green |
| T3 | `MLW-T3-stage4-real-app-binding-findings.md` | 5 | Stage4Context real entry failure, retrieval/audit wiring drift |
| T4 | `MLW-T4-protocol-facade-runtime-bridge-findings.md` | 5 | protocol/runtime bridge split, Stage4 callback contract split-brain |
| T5 | `MLW-T5-test-realism-regression-findings.md` | 4 | test realism, source-string guard, surrogate app overuse |

## Severity Summary

| Severity | 건수 |
|----------|------|
| P0 | 2 |
| P1 | 3 |
| P2 | 11 |
| P3 | 5 |
| 합계 | 21 |

## Key Clusters

| Cluster | 포함 surface | 설명 |
|---------|--------------|------|
| Stage4 live entry red baseline | `MLW-T3-001`, `MLW-T4-001`, `MLW-T5-001` | Stage4Context slot drift가 runtime failure, facade contract split, regression baseline 붕괴로 각각 다시 확인됐다 |
| `from_app()` pinning gap | `MLW-T1-001`, `MLW-T2-003`, `MLW-T5-002`, `MLW-T5-004` | Stage2/3/4 real slot surface를 spec-less mock과 surrogate app가 충분히 잠그지 못한다 |
| Runtime bridge fragmentation | `MLW-T3-002`, `MLW-T3-004`, `MLW-T4-002`, `MLW-T4-003`, `MLW-T4-004`, `MLW-T4-005` | protocol, ctx slot, direct `self.app`, fire-and-forget callback 해석이 서로 갈라져 있다 |
| Proof-quality overstatement | `MLW-T1-004`, `MLW-T5-003`, `MLW-T5-004` | green tests가 곧 live wiring guarantee라는 해석을 허용하는 메타/proof drift가 남아 있다 |

## Representative Findings

| ID | Sev | 요약 |
|----|-----|------|
| `MLW-T3-001` | `P0` | real app Stage4 entry가 `Stage4Context.from_app()`에서 즉시 붕괴한다 |
| `MLW-T1-001` | `P1` | `SovereignApp -> Stage2Context.from_app() -> consumer` 실경로를 끝까지 잠그는 test가 없다 |
| `MLW-T3-002` | `P1` | Stage4 smart retrieval의 `ctx.db` 경로가 real app에서 silent no-op다 |
| `MLW-T4-003` | `P2` | audit summary bridge가 Protocol, ctx slot, direct app call로 분열돼 있다 |
| `MLW-T5-003` | `P2` | `inspect.getsource` 중심 regression guard가 의미 보존보다 코드 모양 고정에 치우쳐 있다 |
| `MLW-T5-004` | `P3` | `SimpleNamespace` surrogate가 wrapper/control-plane parity 검증을 대체한다 |

## 결론

이 트랙의 통합 판단은 "실제 live wiring을 기준으로 보면 Stage4는 아직 red baseline이고,
Stage2/Stage3도 green test가 곧 real-app contract green을 뜻하지 않는다"는 것이다.
우선 remediation 순서는 `Stage4Context slot sync -> real from_app slot pinning 확장 -> protocol/runtime bridge 단일화`
가 적절하다.
