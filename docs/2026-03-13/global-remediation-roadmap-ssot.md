# 전역 remediation 로드맵 SSOT

> 작성일: 2026-03-13
> 상태: `execution-ready`
> 역할: 2026-03-13 기준으로 작성된 전역 remediation execution SSOT들을 실제 실행 큐 하나로 압축하는 상위 로드맵
> 금지사항: 본 문서는 세부 execution SSOT를 대체하지 않는다. 구현 범위, acceptance, 검증 항목은 각 원본 SSOT를 따른다.

## 0. 소스 문서

- `docs/2026-03-13/backend-global-remediation-execution-ssot.md`
- `docs/2026-03-13/00_test-log-global-full-survey-remediation-execution-ssot.md`
- `docs/2026-03-13/frontend-global-remediation-execution-ssot.md`
- `docs/2026-03-13/frontend-backend-global-remediation-execution-ssot.md`
- `docs/2026-03-13/global-detail-full-survey-remediation-execution-ssot.md`
- `docs/2026-03-13/global-macro-reset-remediation-execution-ssot.md`
- `docs/2026-03-13/mojibake-global-remediation-execution-ssot.md`

참고 실아티팩트:

- `00_test_print.txt`

## 1. 로드맵 역할

이 문서는 세부 SSOT들 사이의 실행 충돌을 정리한다.

- `P0 live blocker`는 문서 정리나 packaging drift보다 먼저 닫는다.
- `state truth / evidence truth`는 gate 확장과 runtime proof보다 먼저 닫는다.
- `public contract drift`는 evidence layer가 다시 흔들리지 않는 시점에 닫는다.
- `historical hygiene / mojibake quarantine`은 live path와 공식 gate가 안정된 뒤에 묶는다.
- 한 번에 `1 execution unit`만 진행한다.

즉, 이 문서는 세부 SSOT의 순서를 다시 쓰는 문서가 아니라, 여러 SSOT를 한 큐로 병합하는 `상위 실행 순서 SSOT`다.

## 2. 현재 기준 최우선 사실

2026-03-13 현재 repo에서 아래 live blocker가 실제로 재현된다.

- 실행 확인: `pytest tests/test_stage4_context.py -q`
- 현재 오류: `'generate_writer_guidance_v60_8' in __slots__ conflicts with class variable`
- 직접 영향 파일: `modules/core/stage4_context.py`
- 참고 실아티팩트: `00_test_print.txt`에도 같은 Stage 4 오류가 반복 기록돼 있다.

의미:

- `BGR-E1. Live Stage 4 Path Recovery`는 문서상 가설이 아니라 현재 실테스트 수집을 막는 `live P0`다.
- `00_test_print.txt`는 위 blocker가 survey 문서뿐 아니라 실제 실행 로그에서도 드러났다는 보조 근거다.
- 따라서 거시 문서 정리나 frontend/shipping 정렬보다 앞에 둬야 한다.

## 3. 최종 실행 단계

### Stage A. Live Backend Unblock

실행 유닛:

1. `BGR-E1`

이 단계의 목적:

- Stage 4 import/build blocker 제거
- Stage 4 live path 회귀 수집 복구

진입 이유:

- 현재 유일한 `P0`다.
- 다른 backend/global proof unit의 검증 기반 자체가 여기서 막힌다.

종료 게이트:

- `tests/test_stage4_context.py` collection blocker 제거
- `Stage4Context.from_app()` live path 검증 가능

### Stage B. State / Evidence Truth Recovery

실행 유닛:

1. `BGR-E3`
2. `BGR-E4`
3. `00T-E1`
4. `00T-E2`

보조 문서 유닛:

1. `GMR-R2`

이 단계의 목적:

- destructive success semantics를 runtime truth와 다시 맞춘다.
- Stage 3/4 attempt lineage와 operator 증거 연속성을 복구한다.
- `00_test` 로그 포렌식과 전역 evidence chain을 같은 방향으로 닫는다.

이 순서로 두는 이유:

- `BGR-E3`가 닫히지 않으면 reset/rollback 이후 상태 truth가 흔들린다.
- `BGR-E4`가 닫히지 않으면 operator proof surface가 attempt 단위로 join되지 않는다.
- `00T-E1`, `00T-E2`는 실제 로그/JSONL 증거 연속성을 강화하는 고ROI 보강이다.
- `GMR-R2`는 구현 후 safe-op semantics를 재분산시키지 않기 위한 freeze 문서로 둔다.

종료 게이트:

- destructive op success가 partial failure를 숨기지 않는다.
- decision row 기준으로 attempt join이 가능하다.
- root boot log에서 project log까지 session continuity가 이어진다.

### Stage C. Public Contract Normalization

실행 유닛:

1. `BGR-E2`
2. `GDFS-E1`
3. `GDFS-E2`
4. `GDFS-E3`

보조 문서 유닛:

1. `GMR-R5`
2. `GMR-R3`
3. `GMR-R1`

이 단계의 목적:

- interactive entry contract, cross-stage producer/consumer contract, persistence boundary, config/API/operator single truth를 정렬한다.

이 순서로 두는 이유:

- `BGR-E2`는 public `/run`과 desktop/menu drift를 직접 닫는 isolated P1 fix다.
- `GDFS-E1`은 producer-consumer split을 다시 오염시키지 않기 위한 선행 수리다.
- `GDFS-E2`는 transaction/recovery 경계를 잠가 앞 단계 산출물이 partial restore gap에 흔들리지 않게 한다.
- `GDFS-E3`는 operator-facing truth와 runtime truth를 같은 의미로 맞춘다.
- `GMR-R5`, `GMR-R3`, `GMR-R1`은 각각 control-plane provenance, DB access inventory, runtime ownership을 문서 SSOT로 고정하는 후행 freeze다.

종료 게이트:

- `/run`, prompt-map, desktop action inventory가 같은 key inventory를 본다.
- Stage 3 sink와 downstream consumer가 같은 artifact lineage를 본다.
- transaction boundary와 API/operator contract가 단일 의미를 가진다.

### Stage D. Frontend / Shipping Alignment

실행 유닛:

1. `FG-E1`
2. `FG-E2`
3. `FBX-E1`
4. `FBX-E2`
5. `FBX-E3`
6. `FG-E4`
7. `FBX-E4`

보조 문서 유닛:

1. `GMR-R6`

이 단계의 목적:

- packaging model, Stage 0 external contract, renderer direct surface, bridge transport, packaged artifact meaning, stale entry/shadow surface를 하나의 shipping reality로 맞춘다.

이 순서로 두는 이유:

- frontend-global의 `P1`은 존재하지만 current `P0`처럼 수집 자체를 막지는 않는다.
- `FG-E1`, `FG-E2`가 닫혀야 문서/build/env와 public Stage 0 contract가 먼저 정렬된다.
- `FBX-E1~E3`는 direct network surface, websocket contract, artifact topology를 formal contract로 고정한다.
- `FG-E4`, `FBX-E4`는 active contract가 정해진 뒤 처리해야 stale shadow를 안전하게 분리할 수 있다.
- `GMR-R6`은 shipping reality와 live/shadow surface 문서를 마지막에 잠그는 보조 유닛이다.

종료 게이트:

- packaged runtime primary path가 단일 의미를 가진다.
- Stage 0 external contract와 desktop renderer가 같은 submenu 집합을 본다.
- stale root entry와 dead IPC가 live surface와 섞이지 않는다.

### Stage E. Official Gate / Runtime Proof

실행 유닛:

1. `FG-E3`
2. `FBX-E5`
3. `BGR-E6`
4. `GDFS-E4`
5. `00T-E3`
6. `00T-E4`

보조 문서 유닛:

1. `GMR-R4`

이 단계의 목적:

- 앞 단계에서 정리한 live contract와 shipping semantics를 공식 gate, canary, runtime proof, operator summary까지 올린다.

이 순서로 두는 이유:

- `FG-E3`, `FBX-E5`가 desktop 공식 gate를 실표면에 맞게 넓힌다.
- `BGR-E6`은 backend blind spot을 real app-bound proof net으로 끌어올린다.
- `GDFS-E4`는 fresh runtime proof와 archived evidence를 current truth 기준으로 다시 닫는다.
- `00T-E3`, `00T-E4`는 renderer/splash durable relay와 runtime summary contract를 보강한다.
- `GMR-R4`는 Stage 4 PASS와 artifact completeness를 분리 설명하는 문서 freeze다.

종료 게이트:

- official gate가 live bridge/dashboard/risk/package surface를 false green 없이 대표한다.
- canary/runtime proof가 current rationale/provenance sink를 반영한다.
- `runtime_audit_summary.json`의 역할이 `runtime heartbeat + compact proof digest`이며 sole attempt SSOT는 아니라는 점이 오해 없이 고정된다.

### Stage F. Historical Hygiene / Mojibake Closure

실행 유닛:

1. `GDFS-E5`
2. `MJB-E1`
3. `MJB-E2`
4. `MJB-E3`
5. `MJB-E4`
6. `MJB-E5`

이 단계의 목적:

- manual-only / legacy / residue surface를 live path와 분리하고,
- historical corrupt evidence와 live mojibake 재오염 경계를 닫는다.

이 단계를 뒤로 미루는 이유:

- 현재 기준으로는 live `P0`나 runtime gate blocker보다 후순위다.
- archive quarantine과 source string cleanup은 중요하지만, Stage 4 live path와 current operator proof를 먼저 복구하는 편이 ROI가 높다.

종료 게이트:

- manual-only / shadow / residue surface가 live path와 혼동되지 않는다.
- archived corrupt evidence는 provenance를 유지한 채 quarantine된다.
- rerun scanner가 same-class mojibake finding을 새로 추가하지 않는다.

## 4. 오늘의 즉시 실행 큐

오늘 바로 들어갈 유닛은 아래로 고정한다.

1. `BGR-E1`
2. `BGR-E3`
3. `BGR-E4`
4. `00T-E1`

해석:

- 첫 유닛은 `P0 unblock`이다.
- 다음 셋은 `state truth + evidence truth` 복구다.
- 이 네 유닛이 닫히기 전에는 frontend/shipping과 historical hygiene를 앞당기지 않는다.

## 5. 보류 규칙

아래 항목은 `선행 단계 완료 전` 우선 착수하지 않는다.

- `GMR-R1~R6` 단독 선행
- `FG-E1~E4`, `FBX-E1~E5` 선행
- `MJB-E1~E5` 선행
- `GDFS-E4` canary/proof 선행

예외:

- 현재 진행 유닛을 수정하는 과정에서 touched file에 `MJB-E4` 수준의 live source string cleanup이 필수로 끼어드는 경우만, 같은 변경 묶음 안에서 최소 범위로 동반 처리할 수 있다.

## 6. 최종 판정

- 현재 전역 remediation의 최고 ROI 다음 스텝은 `BGR-E1`이다.
- 그 다음 로드맵 축은 `BGR-E3 -> BGR-E4 -> 00T-E1 -> 00T-E2`로 본다.
- 거시 reset 문서는 선행 planning이 아니라, 각 코드 unit이 닫힌 뒤 truth를 재분산시키지 않기 위한 후행 freeze로 배치한다.
- frontend/shipping, canary/proof, mojibake/historical hygiene는 모두 필요하지만, 현재 live backend unblock과 evidence truth 복구보다 앞세우지 않는다.
