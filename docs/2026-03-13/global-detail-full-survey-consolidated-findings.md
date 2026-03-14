# Global Detail Full Survey Consolidated Findings

작성일: 2026-03-13
상태: `executed`
대상 문서: `GDFS-T1` ~ `GDFS-T6`
조사 모드: `read-only`, `cross-track dedupe`, `UTF-8 only`

## Executive Summary

- 전역 retained open set은 `21건`이다.
  - `P1 6건`
  - `P2 14건`
  - `P3 1건`
- `P0`는 없다.
- 이번 통합본의 핵심은 "새 거시 결론"이 아니라, `live code / contract / artifact / operator surface / test gate / manual tool surface`를 중복 없이 한 ledger로 다시 잠그는 것이다.

## Cluster Ledger

| Cluster | IDs | 요약 |
|---|---|---|
| Hidden branch / silent contract | `GDFS-T1-001`, `GDFS-T1-002`, `GDFS-T1-003` | Stage handoff dead branch, save-hook only contract, direct commit bypass |
| Persistence / evidence joinability | `GDFS-T2-001`, `GDFS-T2-002`, `GDFS-T2-003`, `GDFS-T2-004` | Stage3 sink join key/rationale gap, runtime summary thinness, restore compensation gap |
| SSOT / contract drift | `GDFS-T3-001`, `GDFS-T3-002`, `GDFS-T3-003`, `GDFS-T3-004` | threshold split, `phase0_design` wrapper/flat split, fallback threshold drift, preprocess resume guide drift |
| Operator contract false green | `GDFS-T4-001`, `GDFS-T4-002`, `GDFS-T4-003`, `GDFS-T5-001` | optional-vs-required project, undocumented websocket, raw POV operator surface, contract regression blind spot |
| Runtime proof / archived evidence gap | `GDFS-T5-002`, `GDFS-T5-003` | canary green proof coverage gap, stale archive locator note |
| Legacy / manual-only / residue surface | `GDFS-T6-001`, `GDFS-T6-002`, `GDFS-T6-003`, `GDFS-T6-004` | Lite Mode raw provider path, shadow Electron mains, host-bound DB mutation tools, residue/temp scripts |

## Cross-Track Dedupe Decisions

- `GDFS-T4-002`와 `GDFS-T5-001`은 합치지 않았다.
  - 전자는 live websocket contract omission이고, 후자는 그 omission을 green으로 통과시킨 regression blind spot이다.
- `GDFS-T4-003`은 기존 `ROP-T4-002` carry-forward이지만, current operator surface에서 그대로 남아 있어 유지했다.
- `GDFS-T5-003`은 기존 archived path drift보다 한 단계 더 강한 operator-surface mismatch다.
  - note 자체가 "archived proof가 없다"는 false signal을 내므로 별도 유지했다.
- `GDFS-T6-002`는 T4 contract 문제로 흡수하지 않았다.
  - 이 항목의 핵심은 active contract가 아니라 shadow live-consumer 분류 실패다.

## Retained Open Set

| ID | Track | Severity | 현상 요약 |
|---|---|---|---|
| `GDFS-T1-001` | T1 | `P1` | Stage3 -> Stage2 reverse-feedback sink가 producer 없이 consumer만 남아 있다 |
| `GDFS-T1-002` | T1 | `P2` | `plot_roadmap`는 여전히 save-hook 보정에 의존한다 |
| `GDFS-T1-003` | T1 | `P2` | `ReflexionManager`가 `DBManager` transaction contract를 우회한다 |
| `GDFS-T2-001` | T2 | `P1` | Stage3 `session/decisions.jsonl`는 attempt/artifact join key를 아직 못 담는다 |
| `GDFS-T2-002` | T2 | `P1` | Stage3 rationale은 여전히 `director_selections` 중심이고 `stage_attempts`는 얇다 |
| `GDFS-T2-003` | T2 | `P2` | `runtime_audit_summary.json`는 structured digest가 아니라 heartbeat에 가깝다 |
| `GDFS-T2-004` | T2 | `P2` | `_restore_runtime_state()`는 tracker rollback 예외를 비보호 호출한다 |
| `GDFS-T3-001` | T3 | `P1` | validation threshold truth가 YAML `60`과 settings/code `70`로 갈라져 있다 |
| `GDFS-T3-002` | T3 | `P1` | `phase0_design` contract는 flat/wrapper를 허용하지만 BI consumer는 wrapper만 받는다 |
| `GDFS-T3-003` | T3 | `P2` | vector retrieval fallback과 tests가 `validation.yaml` 최신 threshold를 따르지 않는다 |
| `GDFS-T3-004` | T3 | `P2` | preprocess README가 deprecated MD-first resume를 여전히 유도한다 |
| `GDFS-T4-001` | T4 | `P1` | quality/safe-ops contract는 optional project를 광고하지만 runtime은 required를 강제한다 |
| `GDFS-T4-002` | T4 | `P2` | live websocket `/events` surface가 formal contract 바깥에 있다 |
| `GDFS-T4-003` | T4 | `P2` | operator support surface가 `effective_pov` 대신 raw POV를 대표값으로 쓴다 |
| `GDFS-T5-001` | T5 | `P2` | API contract regression은 semantic drift를 막지 못하는 subset gate다 |
| `GDFS-T5-002` | T5 | `P2` | canary green은 current rationale/provenance sink proof를 자동으로 닫지 못한다 |
| `GDFS-T5-003` | T5 | `P2` | archive locator note가 current archived canary proof 존재와 충돌한다 |
| `GDFS-T6-001` | T6 | `P2` | Lite Mode는 raw Gemini direct-call live consumer를 유지한다 |
| `GDFS-T6-002` | T6 | `P2` | shadow Electron main surfaces가 active shell과 split-brain 상태다 |
| `GDFS-T6-003` | T6 | `P2` | host-bound direct DB mutation 도구가 manual-only guard 없이 남아 있다 |
| `GDFS-T6-004` | T6 | `P3` | residue artifact와 temp debug script가 live defect 해석을 오염시킬 수 있다 |

## Global Judgment

- `전역 live surface 중 미분류 영역 없음`: `confirmed`
- `execution-ready for follow-up`: `yes`
- `추가 전수조사 필요`: `no`
- 다음 단계는 추가 조사보다 `remediation / documentation refresh / runtime proof refresh`다.

## Resume Packet

- `Current phase`: `consolidated findings completed`
- `Last completed pass`: `cross-track dedupe`
- `Last completed surface`: `global retained open set`
- `Next surface`: `global 3PASS re-audit`
- `Reopen reason codes used`: `live-code-changed`, `operator-surface-mismatch`, `new-consumer-scope`
- `Stop gate or blocker`: `none`
