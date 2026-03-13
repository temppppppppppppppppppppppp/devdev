# Runtime Observability Provenance Artifact Detail Consolidated Findings

> 작성일: 2026-03-13
> 상태: `executed / consolidated`
> 범위: `ROP-T1` .. `ROP-T5`
> 기준 오더: `runtime-observability-provenance-artifact-detail-full-survey-audit-order.md`
> 정정 결과: `총 11건 (P0 0 / P1 6 / P2 4 / P3 1)`

이번 통합본은 context log, soft failure relay, structured sink alignment, Stage0 POV provenance,
canary/runtime proof surface를 evidence-layer 관점에서 통합한 SSOT다.
핵심 결론은 "runtime evidence layer는 green sink가 있어도 single proof chain이 아니다"는 점이다.

## Terminal Summary

| Terminal | 문서 | 최종 건수 | 핵심 주제 |
|----------|------|-----------|-----------|
| T1 | `ROP-T1-main-a-context-log-wiring-findings.md` | 2 | Stage3 decision joinability, Stage4 degraded completion split |
| T2 | `ROP-T2-soft-failure-audit-utf8-findings.md` | 2 | validation/audit relay gap, snapshot soft-failure summary blind spot |
| T3 | `ROP-T3-structured-sink-alignment-findings.md` | 3 | Stage3 rationale sink split, historical artifact generation split, summary heartbeat blind spot |
| T4 | `ROP-T4-stage0-pov-styleguide-provenance-findings.md` | 2 | Stage0 POV provenance artifact drift, operator-facing raw POV exposure |
| T5 | `ROP-T5-runtime-proof-regression-findings.md` | 2 | canary proof coverage gap, archived proof path drift |

## Severity Summary

| Severity | 건수 |
|----------|------|
| P0 | 0 |
| P1 | 6 |
| P2 | 4 |
| P3 | 1 |
| 합계 | 11 |

## Key Clusters

| Cluster | 포함 surface | 설명 |
|---------|--------------|------|
| Stage3/Stage4 sink joinability split | `ROP-T1-001`, `ROP-T1-002`, `ROP-T3-001` | session decision row, degraded completion, Stage3 rationale sink가 단일 join contract로 닫히지 않는다 |
| Structured sink alignment gap | `ROP-T2-001`, `ROP-T2-002`, `ROP-T3-002`, `ROP-T3-003` | soft-failure relay, historical artifact generation split, heartbeat summary blind spot가 함께 남아 있다 |
| POV provenance drift | `ROP-T4-001`, `ROP-T4-002` | current code contract와 live artifact/operator support surface가 아직 같은 provenance bundle을 보존하지 않는다 |
| Canary proof gap | `ROP-T5-001`, `ROP-T5-002` | canary green은 최신 rationale/provenance sink proof를 자동으로 닫지 못하고 archived proof path도 current workspace와 어긋난다 |

## Representative Findings

| ID | Sev | 요약 |
|----|-----|------|
| `ROP-T1-001` | `P1` | Stage3 decision row가 `attempt_key` 없이 저장돼 session sink 단독 포렌식이 끊긴다 |
| `ROP-T1-002` | `P1` | Stage4 degraded completion이 `soft_failures.jsonl`과 `runtime_audit_summary.json`에 서로 다른 사실로 남는다 |
| `ROP-T3-001` | `P1` | Stage3 rationale SSOT가 아직 단일 sink로 수렴하지 않는다 |
| `ROP-T3-002` | `P2` | historical runtime artifact는 세대별 structured sink가 달라 같은 문장을 다른 뜻으로 만든다 |
| `ROP-T4-001` | `P1` | live Stage0 evidence layer가 아직 post-fix POV provenance 계약으로 refresh되지 않았다 |
| `ROP-T5-001` | `P2` | canary green이 current rationale/provenance sink proof를 자동으로 닫지 못한다 |
| `ROP-T5-002` | `P3` | archived proof reference가 current workspace path를 보존하지 못한다 |

## 결론

이 트랙의 통합 결론은 `single evidence SSOT 부재`, `historical artifact generation split`,
`POV provenance refresh gap`, `canary proof coverage gap` 네 축으로 요약된다.
다음 단계는 `sink join contract 정리 -> artifact refresh / stale-artifact 분리 -> canary proof matrix 보강`
순서의 remediation이다.
