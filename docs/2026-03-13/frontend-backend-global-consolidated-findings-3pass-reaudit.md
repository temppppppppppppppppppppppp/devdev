# 프론트엔드-백엔드 전역 전량 전수조사 통합본 3PASS 재감리

> 작성일: 2026-03-13
> 상태: `completed`
> 대상: `frontend-backend-global-consolidated-findings.md`
> 방식: `PASS 1 ledger rebuild -> PASS 2 dedupe/false-positive removal -> PASS 3 final verdict`

## Executive Summary

- 최종 판정: `survey-complete`
- 최종 확신도: `95%`
- retained `P0`: 0건
- retained `P1`: 0건
- retained `P2`: 6건
- retained `P3`: 1건
- 결론: 이번 트랜치는 코드 수정 없이도 프론트엔드-백엔드 live surface를 문서형 SSOT로 닫을 수 있는 수준까지 도달했다.

## PASS 1

통합 ledger 재구성 결과:

- 개별 트랙 문서 6개 존재
- 각 문서에 `PASS 1`, `PASS 2`, `PASS 3`와 `Resume Packet` 존재
- retained finding 총계는 `P2 6건`, `P3 1건`으로 재구성됨
- runtime proof:
  - `npm --prefix geuldobi-desktop run start:spike` 성공
  - splash 표시
  - backend uvicorn 기동
  - `/status` 200
  - `WS /events` accepted
  - 5초 후 자동 종료
- expanded regression proof:
  - `151 passed in 3.48s`

## PASS 2

오탐 제거 결과:

- `FBX-T4` coverage note는 retained finding으로 올리지 않았다.
  - 현재 회귀군이 style cache injection과 missing engine fallback을 직접 검증하기 때문이다.
- `T1 risk approval window.prompt`는 operator-surface 메모로만 유지하고 retained defect에서는 제거했다.
  - live backend contract drift를 만들지는 않기 때문이다.
- `T2 dead-candidate IPC`는 `P3`로만 유지했다.
  - 실제 runtime break가 아니라 stale surface inventory 문제다.

중복 제거 결과:

- websocket coverage gap은 `FBX-T3-001`로 유지하고,
- package test omission은 더 넓은 release gate 문제이므로 `FBX-T6-001`로 분리 유지했다.

## PASS 3

### 최종 retained open set

| ID | Severity | 요약 |
|----|----------|------|
| `FBX-T1-001` | `P2` | renderer network surface split |
| `FBX-T2-001` | `P2` | desktop bridge transport error code drift |
| `FBX-T3-001` | `P2` | websocket `/events` contract omission |
| `FBX-T5-001` | `P2` | `engine.exe` packaged contract drift |
| `FBX-T5-002` | `P2` | stale root `main.js` drift source |
| `FBX-T6-001` | `P2` | official desktop gate omission |
| `FBX-T2-002` | `P3` | dead-candidate IPC surfaces |

### 95% Confidence Ledger

| 항목 | 점수 |
|------|------:|
| 전역 surface inventory 완료 | +60 |
| expanded pytest gate 녹색 | +10 |
| renderer -> preload -> main -> backend -> runner chain 교차 검증 | +10 |
| build/package/dev parity 검증 | +10 |
| stale duplicate / direct bypass 분류 완료 | +5 |
| 합계 | **95** |

감점 검토:

- `start:spike` 성공으로 runtime proof 감점 없음
- unresolved `P1`가 없어 감점 없음
- UTF-8 오염 검증을 통과해 감점 없음

## Final Judgment

- 본 조사 체인은 `survey-complete / 95% confidence`로 닫는다.
- 지금 남아 있는 항목은 모두 `P2` 이하의 contract/test/build drift다.
- 즉시 코드 수정 없이도 다음 턴부터는 이 문서 체인을 remediation backlog의 SSOT로 사용할 수 있다.

## Resume Packet

- `Current phase`: `consolidated 3PASS completed`
- `Last completed pass`: `PASS 3`
- `Last completed surface`: `global retained open set + confidence ledger`
- `Next surface`: `frontend-backend-global-remediation-execution-ssot.md`
- `Reopen reason codes used`: `none`
- `Stop gate or blocker`: `none`
