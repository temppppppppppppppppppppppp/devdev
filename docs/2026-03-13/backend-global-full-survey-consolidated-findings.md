# Backend Global Full Survey Consolidated Findings

> 작성일: 2026-03-13
> 상태: `executed / consolidated`
> 기준 오더: `backend-global-full-survey-master-audit-order.md`
> 대상 문서: `BGA-T1` .. `BGA-T5`
> 정리 결과: `raw 15건 -> 중복 제거 후 12건 (P0 1 / P1 3 / P2 8 / P3 0)`

## Executive Summary

이번 통합본의 핵심 결론은 세 가지다.

- 현재 백엔드 전역에서 가장 즉각적인 결함은 `Stage4Context` import-time crash다.
- 그 다음 축은 `destructive op 이후 state convergence 실패`, `attempt-level evidence chain 불완전`, `operator-facing proof surface 부족`이다.
- 남은 P2 다수는 서로 따로 놀아도 불편하지만, 합쳐 보면 `stage contract / provider / observability / proof net`이 단일 SSOT로 아직 닫히지 않았다는 뜻이다.

이번 통합은 터미널 raw finding 15건을 그대로 복제하지 않고 세 가지 규칙으로 줄였다.

1. 같은 lifecycle의 cleanup contamination은 하나로 병합했다.
2. 같은 operator proof 문제를 다른 artifact/UI 표면에서 반복한 항목은 하나로 병합했다.
3. regression blind spot은 `test-only`, `canary-only`로 따로 남기지 않고 `live path proof gap`으로 재구성했다.

## Terminal Summary

| Terminal | 문서 | raw 건수 | 통합 반영 |
|----------|------|----------|-----------|
| T1 | `BGA-T1-entry-control-plane-safe-ops-findings.md` | 2 | 2건 retained |
| T2 | `BGA-T2-persistence-db-memory-recovery-findings.md` | 3 | 2건 retained + 1건 merged |
| T3 | `BGA-T3-facade-helper-di-live-consumer-findings.md` | 3 | 2건 retained + 1건 merged |
| T4 | `BGA-T4-stage-contract-provider-config-context-findings.md` | 3 | 3건 retained |
| T5 | `BGA-T5-observability-artifact-bridge-regression-findings.md` | 4 | 2건 retained + 2건 merged |

## Severity Summary

| Severity | 건수 |
|----------|------|
| P0 | 1 |
| P1 | 3 |
| P2 | 8 |
| P3 | 0 |
| 합계 | 12 |

## Top Risk Groups

- `Live Stage 4 path 붕괴`
  - `Stage4Context` import crash와 이를 충분히 못 잡는 regression/proof blind spot이 겹친다.
- `Destructive op 이후 state convergence 실패`
  - 복구 soft-fail success false positive와 cleanup contamination window가 함께 남아 있다.
- `Attempt-level evidence chain 불완전`
  - session JSONL, runtime summary, desktop dashboard, canary proof가 하나의 증거 사슬로 수렴하지 않는다.
- `Stage/provider/config continuity drift`
  - model config, provider return contract, reference excerpt budget이 같은 SSOT로 잠기지 않았다.

## 통합 Ledger

| ID | Severity | 분류 | Source Findings | 전역 요약 |
|----|----------|------|-----------------|-----------|
| `BGA-G-001` | `P0` | retained | `BGA-T3-001` | `Stage4Context`가 import 시점에 즉시 깨져 Stage 4 live auto-build path와 관련 테스트 수집 자체를 막는다 |
| `BGA-G-002` | `P1` | retained | `BGA-T1-001` | public `/run` contract가 Frontier Lag key `7`을 interactive mode에서 누락해 entry/control plane이 실제 메뉴 surface와 어긋난다 |
| `BGA-G-003` | `P1` | retained | `BGA-T2-001` | destructive op가 runtime restore 일부 실패에도 성공처럼 닫혀 persistence/recovery lifecycle truth를 왜곡한다 |
| `BGA-G-004` | `P1` | retained | `BGA-T5-001` | `session/decisions.jsonl`가 stage-wide attempt join ledger가 아니라 operator evidence chain의 첫 고리가 비어 있다 |
| `BGA-G-005` | `P2` | retained | `BGA-T1-002` | `ui_only_action: exit_app`인 key `5`가 backend public `/run`으로 그대로 노출된다 |
| `BGA-G-006` | `P2` | merged | `BGA-T2-002`, `BGA-T2-003` | destructive op 뒤 `emotion_history`와 `BaseAgent._context_caches`가 함께 남아 post-reset contamination window를 만든다 |
| `BGA-G-007` | `P2` | retained | `BGA-T3-002` | Stage 3 lazy init이 injected ctx tracker보다 `self.app`를 우선해 DI context authority를 무너뜨린다 |
| `BGA-G-008` | `P2` | retained | `BGA-T4-001` | model config SSOT가 project-local loader / root loader / import-time constant로 갈라져 있다 |
| `BGA-G-009` | `P2` | retained | `BGA-T4-002` | provider helper가 여전히 `response.raw`를 반환해 caller를 Gemini native shape에 묶는다 |
| `BGA-G-010` | `P2` | retained | `BGA-T4-003` | Stage 0 `reference_excerpt`가 Stage 4 chief writer prompt에 무예산으로 직접 주입된다 |
| `BGA-G-011` | `P2` | merged | `BGA-T5-002`, `BGA-T5-003` | operator-facing proof surface가 `runtime_audit_summary heartbeat + dashboard health view` 수준에 머물러 structured sink proof를 노출하지 못한다 |
| `BGA-G-012` | `P2` | merged | `BGA-T3-003`, `BGA-T5-004` | regression/canary net이 injected-context / Stage 4 중심으로 짜여 live context-bound multi-stage observability regression을 자동 검출하지 못한다 |

## Merge / Elevation Notes

### `BGA-G-006` - cleanup contamination window

- `BGA-T2-002`와 `BGA-T2-003`은 표면이 다르지만 둘 다 destructive op 이후 derived state가 즉시 정합화되지 않는다는 동일 lifecycle 문제다.
- 하나는 DB-backed `emotion_history`, 다른 하나는 in-process `BaseAgent._context_caches`다.
- 전역 관점에서는 둘을 분리하기보다 `post-reset contamination window` 하나로 보는 편이 정확하다.

### `BGA-G-011` - operator proof surface gap

- `BGA-T5-002`는 file artifact인 `runtime_audit_summary.json`의 heartbeat 한계를 지적했고, `BGA-T5-003`은 desktop dashboard가 그 공백을 메우지 못함을 지적했다.
- 둘을 합치면 문제는 "summary file이 약하다"가 아니라 "operator-facing proof surface 전체가 structured proof가 아니다"로 정리된다.

### `BGA-G-012` - proof-net blind spot

- `BGA-T3-003`은 Stage 4 regression net이 injected context를 써서 broken live auto-build path를 비껴 간다는 문제였다.
- `BGA-T5-004`는 canary tooling이 Stage 4 중심이라 Stage 3 observability retained defect를 자동 proof로 닫지 못한다는 문제였다.
- 전역 의미는 하나다. 현재 proof net은 `real app-bound live path`를 backend-wide로 잠그지 못한다.

## Integrated Findings

### `BGA-G-001` | `P0` | live Stage 4 path import crash

- source: `BGA-T3-001`
- 이유: Stage 4 live entry 자체를 깨뜨리는 import-time defect라 전역 백엔드 최고 우선순위로 유지한다.
- 전역 영향 경계:
  - Stage 4 실행
  - Stage 4 DI auto-build path
  - Stage 4 관련 test collection
  - 후속 observability / budget / callback 검증

### `BGA-G-002` | `P1` | Frontier Lag entry contract drift

- source: `BGA-T1-001`
- 이유: public runner/bridge/menu가 같은 key surface를 공유하지 못해 control plane truth가 깨진다.
- 전역 영향 경계:
  - `/run` contract
  - desktop interactive flow
  - main menu / prompt-map coherence

### `BGA-G-003` | `P1` | destructive op success false positive

- source: `BGA-T2-001`
- 이유: persistence/recovery lifecycle에서 "성공" 의미가 runtime restored truth와 분리되면 operator와 다음 boot가 모두 오판한다.
- 전역 영향 경계:
  - rollback / restore / reset / wipe lifecycle
  - post-op boot safety
  - runtime state integrity

### `BGA-G-004` | `P1` | session decisions sink non-joinable

- source: `BGA-T5-001`
- 이유: attempt-level evidence chain의 가장 앞단 JSONL이 비어 있어 operator evidence SSOT가 성립하지 않는다.
- 전역 영향 경계:
  - session JSONL 포렌식
  - Stage 3 / Stage 4 attempt lineage
  - support / audit 대응

### `BGA-G-005` | `P2` | ui-only exit action public exposure

- source: `BGA-T1-002`
- 이유: destructive 급은 아니지만, public backend action set이 UI contract보다 넓어 control plane hygiene가 무너진다.

### `BGA-G-006` | `P2` | post-reset contamination window

- source: `BGA-T2-002`, `BGA-T2-003`
- 이유: reset/wipe/rollback 이후 stale derived state가 남아 다음 agent or next boot 판단을 오염시킨다.
- merged 이유:
  - DB-backed tracker residue와 process-local cache residue가 같은 cleanup gap으로 수렴한다.

### `BGA-G-007` | `P2` | Stage 3 ctx authority drift

- source: `BGA-T3-002`
- 이유: injected context보다 app global을 우선하는 lazy init은 DI contract를 깨고 테스트/실행 해석을 어렵게 만든다.

### `BGA-G-008` | `P2` | model config SSOT split

- source: `BGA-T4-001`
- 이유: project-local override, root loader, import-time constant가 동시에 살아 있으면 provider/model rollout을 backend-wide로 통제할 수 없다.

### `BGA-G-009` | `P2` | provider raw return contract

- source: `BGA-T4-002`
- 이유: provider abstraction이 normalized response가 아니라 native raw object로 새어 나와 multi-provider continuity를 깨뜨린다.

### `BGA-G-010` | `P2` | reference excerpt budget leak

- source: `BGA-T4-003`
- 이유: Stage 0 artifact가 Stage 4 prompt budget을 잠식하는 cross-stage context drift다.

### `BGA-G-011` | `P2` | operator proof surface is not structured proof

- source: `BGA-T5-002`, `BGA-T5-003`
- 이유: summary file과 dashboard가 모두 completion/health view일 뿐 structured sink proof view가 아니다.
- merged 이유:
  - file artifact와 desktop surface가 서로의 공백을 메우지 못하고 같은 blind spot을 만든다.

### `BGA-G-012` | `P2` | backend-wide proof net blind to real live path

- source: `BGA-T3-003`, `BGA-T5-004`
- 이유: injected test path와 Stage 4 중심 canary가 합쳐져 `real app-bound`, `multi-stage` regression을 자동으로 잡지 못한다.
- merged 이유:
  - 둘 다 "현재 green proof가 실제 live path를 pin하지 못한다"는 동일 구조 문제다.

## Conclusion

전역 기준으로 지금 가장 먼저 닫아야 할 것은 `live Stage 4 path crash`, `destructive op success semantics`, `attempt-level evidence chain` 세 축이다. 그 다음 단계는 `cleanup contamination`, `operator proof surface`, `proof net blind spot`을 같은 remediation 묶음으로 잠그는 편이 효율적이다.

이번 통합본은 `raw 15 -> final 12`로 정리됐고, 삭제된 3건은 오탐 제거라기보다 같은 lifecycle 문제의 중복 병합이다. 다음 단계는 이 통합본을 기준으로 3PASS 재감리를 수행해 숫자, dedupe, severity, runtime-only 경계를 다시 검증하는 것이다.
