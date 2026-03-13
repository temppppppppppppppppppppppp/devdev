# UI Codebase Health Remediation Postfix 3Pass Closure

작성일: 2026-03-13  
기준 문서:
- [ui-codebase-health-remediation-execution-ssot.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/ui-codebase-health-remediation-execution-ssot.md)
- [ui-codebase-health-remediation-3pass-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/ui-codebase-health-remediation-3pass-audit.md)

## Executive Summary

- 판정: `closed`
- 최종 확신도: `95%`
- post-fix 기준 retained `P0/P1/P2`: 없음

이번 수정으로 닫은 항목:
- `key 7` UI-bridge dead path
- renderer 동적 `innerHTML` escape 부재
- desktop `test/docs gate` stale 상태

## Pass 1

수정 사실:
- [run_validator.py](C:/Users/User/Desktop/글도비/modules/api/run_validator.py)에서 `ALLOWED_KEYS`에 `7` 추가
- [api-contract-v1.yaml](C:/Users/User/Desktop/글도비/docs/implementation/api-contract-v1.yaml), [prompt-map-v1.json](C:/Users/User/Desktop/글도비/docs/implementation/prompt-map-v1.json)에서 `key 7` 계약 동기화
- [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html)에 `escapeHtml`, `sanitizeToken` helper 추가 후 high-risk `innerHTML` 동적 surface에 적용
- [package.json](C:/Users/User/Desktop/글도비/geuldobi-desktop/package.json)의 desktop `test` script를 focused regression gate로 교체
- 새 focused test 추가:
  - [test_ui_renderer_sanitization.py](C:/Users/User/Desktop/글도비/tests/test_ui_renderer_sanitization.py)
  - [test_desktop_contract_refresh.py](C:/Users/User/Desktop/글도비/tests/test_desktop_contract_refresh.py)

## Pass 2

교차 검증:
- validator probe:
  - `validate_run_request("7", None, "idle") -> True / 202 / OK`
- focused regression:
  - `python -m pytest -q tests/test_run_validator.py tests/test_api_contract.py tests/test_frontend_frontier_lag_wiring.py tests/test_ui_renderer_sanitization.py tests/test_desktop_contract_refresh.py`
  - 결과: `111 passed`
- desktop gate:
  - `npm test` in [geuldobi-desktop](C:/Users/User/Desktop/글도비/geuldobi-desktop)
  - 결과: `111 passed`
- Electron spike:
  - `npm run start:spike`
  - splash 표시, backend startup, main window 전환, `/status 200`, `/quality/dashboard 200`

판정:
- UI에 노출된 `key 7`이 backend contract와 일치한다.
- renderer audited surface에서 user/DB/file-name 문자열이 raw HTML로 주입되지 않는다.
- desktop package 자체가 placeholder test gate를 더 이상 사용하지 않는다.

## Pass 3

오탐 제거:
- `unsafe-inline` CSP가 남아 있으므로 이번 수정이 무효라는 주장: 기각
  - 이번 턴 목표는 CSP 전면 개편이 아니라 injection surface 제거였다.
  - audited dynamic `innerHTML` 경로에는 escape helper가 들어갔다.
- spike 종료 직후 `Bridge fetch failed`를 runtime blocker로 볼 주장: 기각
  - auto-close 이후 backend shutdown race로 재현됐고, 부팅/전환/핵심 GET은 모두 성공했다.

잔여 observation:
- [index.html](C:/Users/User/Desktop/글도비/geuldobi-desktop/src/index.html) monolith 구조는 그대로다.
- `unsafe-inline` CSP 자체는 남아 있다.
- 둘 다 이번 remediation 범위 밖 구조 debt이며, 현재 retained runtime blocker는 아니다.

## Confidence Ledger

- `70`: 수정 범위 3축이 코드/문서/테스트에 모두 반영됨
- `+10`: validator/API contract/prompt map/key 7 교차 검증
- `+10`: sanitization helper와 focused test 고정
- `+5`: desktop package test gate 실동작 확인
- `+5`: Electron spike로 boot/bridge/runtime surface 재확인
- `-5`: packaged installer/실사용 payload fuzz까지는 이번 턴에서 하지 않음

최종 확신도: `95%`

## Final Judgment

- UI codebase health remediation 범위는 `closed`
- 새 `P0/P1/P2` 없음
- 다음 단계가 필요하다면 그것은 `구조 개선` 또는 `CSP/renderer refactor`이며, 이번 retained bugfix 범위와는 분리해야 한다.
