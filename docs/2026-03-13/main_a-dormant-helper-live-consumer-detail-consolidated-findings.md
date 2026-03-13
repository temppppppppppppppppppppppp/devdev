# main_a Dormant Helper Live Consumer Detail Consolidated Findings

> 작성일: 2026-03-13
> 상태: `executed / consolidated`
> 범위: `MDH-T1` .. `MDH-T5`
> 기준 오더: `main_a-dormant-helper-live-consumer-detail-full-survey-audit-order.md`
> 정정 결과: `총 14건 (P0 1 / P1 1 / P2 7 / P3 5)`

이번 통합본은 dormant/live inventory 자체보다 "무엇이 진짜 dormant이고 무엇이 live인데 잘못 분류됐는가"
를 다시 잠그는 데 초점을 둔다. 가장 큰 정정은 Stage4 callback 2종이 dormant가 아니라 intended live surface이며,
현재는 binding bug 때문에 막혀 있다는 점이다.

## Terminal Summary

| Terminal | 문서 | 최종 건수 | 핵심 주제 |
|----------|------|-----------|-----------|
| T1 | `MDH-T1-retry-guidance-helper-liveness-findings.md` | 3 | retry/guidance helper live vs dormant 재분류 |
| T2 | `MDH-T2-audit-validation-helper-liveness-findings.md` | 4 | audit/validation facade dormant, already-covered runtime wiring |
| T3 | `MDH-T3-stage01-npc-ui-helper-liveness-findings.md` | 2 | NPC/archetype facade dormant, UI helper weak contract |
| T4 | `MDH-T4-bootstrap-history-cache-helper-liveness-findings.md` | 5 | bootstrap/history/cache helper dead-chain vs inline bypass |
| T5 | `MDH-T5-callgraph-runtime-artifact-regression-findings.md` | 3 | exact-name grep / artifact proof quality gap |

## Severity Summary

| Severity | 건수 |
|----------|------|
| P0 | 1 |
| P1 | 1 |
| P2 | 7 |
| P3 | 5 |
| 합계 | 14 |

## Key Clusters

| Cluster | 포함 surface | 설명 |
|---------|--------------|------|
| Misclassified live Stage4 callbacks | `MDH-T1-01` | `_generate_writer_guidance_v60_8`, `_enrich_director_result`는 dormant가 아니라 live surface이며 현재는 slot bug로 막혀 있다 |
| Dormant facade vs live underlying service | `MDH-T2-001`, `MDH-T2-003`, `MDH-T3-001` | facade helper는 dormant인데 하위 service/test는 살아 있는 split surface가 반복된다 |
| Weak or bypassed live helper contract | `MDH-T3-002`, `MDH-T4-003`, `MDH-T4-004`, `MDH-T4-005` | live helper가 있어도 duck-typed contract, stub body, inline bypass, cold optional slot이 남아 있다 |
| Proof-quality gap | `MDH-T5-001`, `MDH-T5-002`, `MDH-T5-003` | callgraph grep, smoke/canary artifact만으로 live consumer 여부를 닫으면 false negative/false positive가 생긴다 |

## Representative Findings

| ID | Sev | 요약 |
|----|-----|------|
| `MDH-T1-01` | `P0` | Stage4 callback 2종은 dormant가 아니라 live surface인데 current binding bug로 runtime에서 막혀 있다 |
| `MDH-T2-001` | `P2` | `_classify_rejection_feedback()` facade는 production caller가 없는 dormant surface다 |
| `MDH-T2-003` | `P1` | `_validate_arc_data_fields()` facade는 Stage2 기준 dormant이며 기존 runtime finding과 맞물린다 |
| `MDH-T3-001` | `P2` | NPC/archetype facade 4종은 현행 runtime consumer가 없는 dormant surface다 |
| `MDH-T4-003` | `P2` | boot chain에 실제 도달하지만 body가 guard + `pass`뿐인 dormant stub가 남아 있다 |
| `MDH-T5-003` | `P2` | e2e/smoke/canary artifact만으로는 live consumer drift와 dormant misclassification을 막지 못한다 |

## 결론

이 트랙의 통합 결론은 "dormant helper inventory는 단순 dead-code 목록이 아니라,
live callback misclassification, dormant facade, bypassed helper chain, proof-quality gap이 섞인 구조"라는 것이다.
우선순위는 `Stage4 callback live bug 정리 -> dormant facade 정리 기준 통일 -> bootstrap/cache helper dead-chain 정리`
가 적절하다.
