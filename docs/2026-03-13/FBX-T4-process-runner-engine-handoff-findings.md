# FBX-T4 Process Runner / Engine Handoff Findings

> 작성일: 2026-03-13
> 상태: `completed`
> 범위: `modules/api/process_runner.py`, `main_a.py` boot/menu entry surface, `build/backend_entry.py`
> 방법: `stdin/env/runtime handoff audit + 3PASS`

## 결론

- retained `P0`: 0건
- retained `P1`: 0건
- retained `P2`: 0건
- retained `P3`: 0건
- 핵심 결론: boot/menu handoff, Mode A/B, stage0 style cache injection, workspace/project env propagation은 현재 회귀와 일치한다.

## PASS 1

- `MODE_B_KEYS`는 `0,1,2,3,4,5,6,44,77,88,99`다.
- `_build_stdin_sequence()`는 Mode B에서 boot sequence만 주입하고 stdin을 열어 둔다.
- `stage0_style_cache_mode` 주입은 `key=0`, `sub_key=6`일 때만 추가 `y + choice`를 넣는다.
- `_build_env()`는 API key, 추가 API key, slack webhook을 넘긴다.
- `build/backend_entry.py`는 frozen 모드에서 `GEULDOBI_ENGINE_ROOT`, `GEULDOBI_PYTHON_PATH`, `GEULDOBI_PROJECTS_ROOT`를 세팅한다.

## PASS 2

- `tests/test_process_runner_stage0_inputs.py`는 style cache choice 주입을 고정한다.
- `tests/test_process_runner.py`는 missing `engine.exe` fallback to embedded python + `main_a.py`를 고정한다.
- `tests/test_bridge_server_desktop_risk_gate.py`는 destructive key handoff 이전 risk gate를 검증한다.
- `main_a.py` boot/menu 진입 자체를 바꾸는 코드 drift는 현재 조사 범위에서 발견되지 않았다.

## PASS 3

- retained finding 없음
- 다만 packaged runtime의 `engine.exe` contract와 build artifact parity 문제는 `FBX-T5`에서 별도 처리한다.

## Retained Open Set

- 없음

## Resume Packet

- `Current phase`: `FBX-T4 completed`
- `Last completed pass`: `PASS 3`
- `Last completed surface`: `runner stdin/env handoff`
- `Next surface`: `FBX-T5 build/package/stale drift`
- `Reopen reason codes used`: `none`
- `Stop gate or blocker`: `none`
