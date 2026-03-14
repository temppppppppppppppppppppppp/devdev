# FGS-T4 Bridge Runner Contract Findings

> 작성일: 2026-03-13
> 상태: `PASS3 complete`
> 범위: bridge, runner, validator, prompt-map, Stage 0 interactive contract

## 조사 범위

- `modules/api/bridge_server.py`
- `modules/api/process_runner.py`
- `modules/api/run_validator.py`
- `build/backend_entry.py`
- `modules/core/stage01_helpers.py`
- `docs/implementation/api-contract-v1.yaml`
- `docs/implementation/prompt-map-v1.json`

## PASS 1 사실 수집

- `run_validator.py`는 Stage 0 허용 `sub_key`를 `{"0","1","2","3","4","5","6","7"}`로 정의한다.
- `prompt-map-v1.json`도 key `0`의 `allowed_sub_keys`에 `"0"`을 포함한다.
- renderer와 frontend 회귀 테스트는 Stage 0 surface를 `1..7`만 노출·검증한다.
- `stage01_helpers.py`에서 `mode == 0`은 다시 CLI submenu를 띄우는 interactive branch다.

## PASS 2 교차 검증

- `tests/test_frontend_stage0_connectivity.py`는 `data-sub-key="1"`부터 `"7"`까지만 확인한다.
- `tests/test_run_validator.py`는 반대로 `"0"`도 valid sub_key로 통과시킨다.
- `tests/test_bridge_server_http_contract.py`는 real app `/run` contract를 검증하지만, Stage 0 `sub_key="0"` hidden path 자체를 별도로 닫지는 않는다.
- 현재 desktop UI는 `sub_key 0`을 전혀 노출하지 않으므로, external contract 상으로만 살아 있는 메뉴 의미가 남아 있다.

## PASS 3 오탐 제거

- `FGS-T4-H1`: packaged project root split
  - 판정: `rejected`
  - 이유: `GEULDOBI_PROJECTS_ROOT` 우선 해석과 관련 pytest가 현재는 root split을 닫고 있다.
- `FGS-T4-H2`: work_guard/style cache Stage 0 parity completely broken
  - 판정: `rejected`
  - 이유: `1..7` renderer path와 `stage01_helpers.py` `1..7` 메뉴는 현재 일치한다.

## 확정 findings

### FGS-T4-001

- Severity: `P2`
- 현상 요약: Stage 0 `sub_key 0` interactive submenu path가 validator와 prompt-map에는 남아 있지만, desktop UI와 frontend 회귀망에서는 비노출 상태다.
- 코드 근거:
  - `modules/api/run_validator.py:27`
  - `docs/implementation/prompt-map-v1.json:7`
  - `modules/core/stage01_helpers.py:403`
- 보조 근거:
  - `tests/test_frontend_stage0_connectivity.py`는 `1..7`만 확인한다.
  - `tests/test_run_validator.py`는 `"0"`을 valid sub_key로 통과시킨다.
- counter-evidence review:
  - 이 경로는 즉시 renderer bug를 일으키지 않는다.
  - 다만 external caller나 future automation 입장에서는 hidden interactive branch를 계속 허용하는 split contract다.
- 상태: `confirmed`
- 권장 후속 조치:
  - Stage 0 external contract를 `1..7`로 닫거나
  - `0`을 명시적 internal-only branch로 문서화하고 validator/test/contract에 동일하게 표시

## 기각 findings

- packaged project root split
- Stage 0 1..7 contract 붕괴

## coverage gap / open question

- `/run key=0 sub_key=0`의 실제 live 대화 흐름은 자동화 evidence가 부족해 `runtime-only`에 가깝다.

## PASS 요약

- PASS1 후보 3건
- PASS2 제거 2건
- 최종 1건
