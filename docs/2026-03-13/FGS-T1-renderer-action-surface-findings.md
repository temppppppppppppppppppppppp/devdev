# FGS-T1 Renderer Action Surface Findings

> 작성일: 2026-03-13
> 상태: `PASS3 complete`
> 범위: `geuldobi-desktop/src/index.html`, `sprite_test.html`

## 조사 범위

- Stage 0 submenu, Stage 2~4, One-Stop, Frontier Lag, 운영 버튼
- quality dashboard, safe ops preview, review 입력, artifact ladder
- renderer sanitization helper, sprite/canvas asset wiring

## PASS 1 사실 수집

- `index.html`은 Stage 0 `sub_key 1..7`, 스타일 캐시 selector, work_guard template surface, Safe Ops Preview, approval ID 입력 흐름을 모두 renderer에 노출한다.
- `Frontier Lag` surface는 버튼, action meta, pipeline order, animated stage set까지 일관되게 등록돼 있다.
- 동적 HTML 표면은 `escapeHtml()`, `sanitizeToken()` helper를 통해 주입 문자열과 class token을 제한하는 구조다.
- `officeCanvas`는 `sprites/*.png`를 로드해 사무실 애니메이션을 그린다.

## PASS 2 교차 검증

- `tests/test_frontend_stage0_connectivity.py`, `tests/test_frontend_frontier_lag_wiring.py`, `tests/test_ui_renderer_sanitization.py`를 읽었고, 표적 pytest 묶음 실행에서도 모두 green이었다.
- Stage 0 라벨/번호 체계는 `modules/core/stage01_helpers.py`의 실제 메뉴 출력 `1..7`과 일치한다.
- `quality`/`safe ops` 패널은 bridge payload fallback/merge 구조를 갖고 있어, 단순 key 누락만으로 즉시 renderer 붕괴가 발생하는 형태는 아니다.

## PASS 3 오탐 제거

- `FGS-T1-H1`: Stage 0 submenu 라벨 drift
  - 판정: `rejected`
  - 이유: renderer `1..7` 노출과 `stage01_helpers.py`의 실제 메뉴가 현재는 일치한다.
- `FGS-T1-H2`: 동적 HTML surface unsanitized
  - 판정: `rejected`
  - 이유: `escapeHtml`, `sanitizeToken` helper와 source-string 회귀 테스트가 현재 고위험 surface를 덮고 있다.
- `FGS-T1-H3`: Frontier Lag 노출 누락
  - 판정: `rejected`
  - 이유: 버튼, action meta, pipeline order, agent set, package test script가 모두 연결돼 있다.

## 확정 findings

- 없음

## 기각 findings

- Stage 0 renderer label drift
- Frontier Lag wiring 누락
- sanitization helper 부재

## coverage gap / open question

- sprite asset 로드 실패 시 renderer가 어떻게 degrade 되는지는 정적 조사와 source-string 테스트만으로는 닫히지 않는다.
- offline mode, canvas asset load, quality panel 실제 렌더링은 live Electron 검증이 없으므로 `needs-live-check`다.

## PASS 요약

- PASS1 후보 3건
- PASS2 제거 3건
- 최종 0건
