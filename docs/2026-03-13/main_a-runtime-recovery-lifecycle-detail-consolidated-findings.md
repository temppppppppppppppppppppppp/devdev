# main_a Runtime Recovery Lifecycle Detail Consolidated Findings

> 작성일: 2026-03-13
> 상태: `executed / consolidated`
> 범위: `MRL-T1` .. `MRL-T5`
> 기준 오더: `main_a-runtime-recovery-lifecycle-detail-full-survey-audit-order.md`
> 정정 결과: `총 11건 (P0 0 / P1 5 / P2 6 / P3 0)`

이번 통합본은 boot, project switch, cache/history, preset registry, rollback/recovery, test/doc proof surface를
하나의 lifecycle graph로 재배열한 SSOT다. `MRL-T5`는 restored `opus_tf5_patch_order.md`를 기준으로 rerun 완료됐고,
현재 runtime lifecycle 문제는 "code drift"와 "proof drift"가 함께 남아 있는 상태로 정리된다.

## Terminal Summary

| Terminal | 문서 | 최종 건수 | 핵심 주제 |
|----------|------|-----------|-----------|
| T1 | `MRL-T1-bootstrap-runtime-state-restore-findings.md` | 2 | boot/project object split, file-backed support contract drift |
| T2 | `MRL-T2-cache-anchor-history-lifecycle-findings.md` | 2 | emotion history next-boot contamination, cache/history live authority split |
| T3 | `MRL-T3-project-switch-preset-registry-findings.md` | 2 | selected genre vs preset registry truth-source split, partial-success recovery |
| T4 | `MRL-T4-commit-rollback-recovery-contract-findings.md` | 2 | post-commit recovery exception semantics, world/fact silent success |
| T5 | `MRL-T5-lifecycle-tests-docs-regression-findings.md` | 3 | rollback regression net blind spot, next-boot proof gap, legacy patch proof drift |

## Severity Summary

| Severity | 건수 |
|----------|------|
| P0 | 0 |
| P1 | 5 |
| P2 | 6 |
| P3 | 0 |
| 합계 | 11 |

## Key Clusters

| Cluster | 포함 surface | 설명 |
|---------|--------------|------|
| Boot / project context split | `MRL-T1-001`, `MRL-T1-002`, `MRL-T3-001` | boot, project switch, preset/base genre가 단일 truth source로 잠기지 않는다 |
| Recovery / next-boot contamination | `MRL-T2-001`, `MRL-T2-002`, `MRL-T3-002`, `MRL-T4-001`, `MRL-T4-002` | destructive recovery success 판정과 next-boot observable state가 서로 어긋난다 |
| Proof surface gap | `MRL-T5-001`, `MRL-T5-002`, `MRL-T5-003` | 현재 regression net은 tracker pair와 same-process checks에 치우쳐 있고, historical patch closure는 current proof를 대체하지 못한다 |

## Representative Findings

| ID | Sev | 요약 |
|----|-----|------|
| `MRL-T1-001` | `P1` | boot graph가 dynamic binding service와 boot-captured project object로 갈라져 restart-less switch 계약이 없다 |
| `MRL-T2-001` | `P1` | destructive recovery가 `emotion_history`를 DB에 남겨 다음 boot에서 오염을 재주입한다 |
| `MRL-T3-002` | `P2` | preset restore failure가 recovery success 판정에 반영되지 않는다 |
| `MRL-T4-002` | `P2` | `world_state`/`fact_ledger` recovery failure가 success로 통과한다 |
| `MRL-T5-001` | `P1` | rollback regression net이 `world_state`/`fact_ledger`/preset restore를 실제로 잠그지 못한다 |
| `MRL-T5-002` | `P2` | destructive recovery 뒤 `next boot / restart / reload` semantics를 검증하는 proof가 없다 |
| `MRL-T5-003` | `P2` | legacy patch closure 문구가 current regression surface보다 강하게 읽힌다 |

## 결론

runtime lifecycle의 현재형 문제는 `boot truth-source split`, `destructive recovery partial-success`, `next-boot proof gap` 세 축으로 요약된다.
조사 단계는 이번 통합본과 re-audit로 종료 가능하며, 다음 단계는 `fresh lifecycle regression tests + recovery semantics remediation`
문서로 넘어가는 것이 맞다.
