# main_a Cross-Stage Semantic Preservation Detail Consolidated Findings

> 작성일: 2026-03-13
> 상태: `executed / consolidated`
> 범위: `MCS-T1` .. `MCS-T5`
> 기준 오더: `main_a-cross-stage-semantic-preservation-detail-full-survey-audit-order.md`
> 정정 결과: `총 15건 (P0 0 / P1 6 / P2 8 / P3 1)`

이번 통합본은 `Stage4 -> Stage3`, `Stage3 -> Stage2`, `Stage4 -> Stage2`,
shared summary/context, regression proof surface를 한 문서로 묶은 SSOT다.
전체 결론은 semantic preservation이 일부 경계에서 `semantic-loss`가 아니라
`semantic-bypass`와 `semantic-rewrite`로 나타난다는 것이다.

## Terminal Summary

| Terminal | 문서 | 최종 건수 | 핵심 주제 |
|----------|------|-----------|-----------|
| T1 | `MCS-T1-stage4-to-stage3-semantic-findings.md` | 3 | full regeneration bypass, inplace patch rewrite, enrich contract drift |
| T2 | `MCS-T2-stage3-to-stage2-semantic-findings.md` | 3 | reverse feedback producer 부재, structured reject payload collapse |
| T3 | `MCS-T3-stage4-to-stage2-semantic-findings.md` | 2 | difficulty-only carrier rewrite, hard-only cutoff bypass |
| T4 | `MCS-T4-shared-context-summary-semantic-findings.md` | 3 | summary/future-context trim drift, dual-channel past-history split |
| T5 | `MCS-T5-cross-stage-tests-docs-regression-findings.md` | 4 | regression proof gap, stale doc claim, mock/shadow proof quality drift |

## Severity Summary

| Severity | 건수 |
|----------|------|
| P0 | 0 |
| P1 | 6 |
| P2 | 8 |
| P3 | 1 |
| 합계 | 15 |

## Key Clusters

| Cluster | 포함 surface | 설명 |
|---------|--------------|------|
| Stage4 -> Stage3 bypass / rewrite | `MCS-T1-001`, `MCS-T1-002`, `MCS-T1-003` | Stage4 rejection semantics가 full regeneration에서는 아예 우회되고, inplace patch에서는 문자열 blob로 재작성된다 |
| Stage3 -> Stage2 collapse | `MCS-T2-001`, `MCS-T2-002`, `MCS-T2-003` | live producer 부재, reason-count text collapse, taxonomy drift가 함께 존재한다 |
| Stage4 -> Stage2 rewrite / bypass | `MCS-T3-001`, `MCS-T3-002` | Stage4 rich reject semantics가 difficulty-only carrier로 납작해지고 hard-only cutoff 아래에서는 완전히 사라진다 |
| Shared context semantic drift | `MCS-T4-001`, `MCS-T4-002`, `MCS-T4-003` | past summary / future context / Stage1 boundary policy가 single SSOT로 잠기지 않는다 |
| Regression proof quality | `MCS-T5-001` .. `MCS-T5-004` | live payload를 잠그는 tests가 약하고, shadow/source-string assertion과 stale docs가 confidence를 흐린다 |

## Representative Findings

| ID | Sev | 요약 |
|----|-----|------|
| `MCS-T1-001` | `P1` | Stage4 logic-error full regeneration은 Stage3 semantic contract를 통과하지 않고 bypass한다 |
| `MCS-T2-001` | `P1` | Stage3 reject producer가 없어 `Stage3->2` reverse feedback branch가 사실상 dead다 |
| `MCS-T2-002` | `P1` | Stage3 reject의 구조화 의미가 Stage2 경계에서 reason-count 문자열로 붕괴한다 |
| `MCS-T3-001` | `P1` | Stage4 rich reject semantics가 Stage2에서는 difficulty-only carrier로 rewrite된다 |
| `MCS-T4-001` | `P1` | mandatory context trim이 past summary를 future context보다 먼저 탈락시킨다 |
| `MCS-T5-003` | `P2` | shadow/source-string proof가 false green과 false red를 함께 만든다 |
| `MCS-T5-004` | `P3` | 기존 감리 문서 1건이 현재 테스트 상태와 어긋난 stale claim을 가진다 |

## 결론

cross-stage semantic preservation의 현재형 문제는 `bypass`, `rewrite`, `dual-channel drift`, `proof-gap` 네 축이다.
다음 단계는 `structured payload handoff 승격 -> Stage2/Stage3 live producer-consumer alignment -> summary/context SSOT 정리`
순서의 remediation으로 넘어가는 것이 맞다.
