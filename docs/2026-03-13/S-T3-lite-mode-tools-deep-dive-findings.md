# [S-T3] Lite Mode & Tools 심층 감사 보고서

> 작성일: 2026-03-13
> 터미널: Terminal 3
> 범위: `lite_mode/`, `tools/`, `tools2/`, `main_tools/blueprint_editor.py`
> 방법: static / read-only / runtime path inspection / host-bound tooling survey

---

## 요약

Lite Mode와 보조 도구군은 프로덕션 파이프라인 밖에 놓여 있지만, 실제로는 프로덕션 DB와 API 키, 로컬 브라우저 세션을 직접 만지는 스크립트가 많다. 이번 심층 감사에서 확인한 공통 패턴은 세 가지다.

- Lite Mode 일부 경로는 production `llm_router`를 우회해 raw Gemini HTTP를 직접 호출한다.
- 테스트처럼 보이는 파일이 실은 `.env`와 live network에 의존하는 수동 진단 스크립트다.
- 오래된 도구군은 절대경로/직접 SQLite mutation 패턴이 광범위하게 남아 있다.

즉, 이 영역은 "죽은 코드"라기보다 **개발자 로컬에서만 성립하는 host-bound 수동 운영 도구 묶음**에 가깝다.

---

## 확정 발견사항

### [S-T3-001] P2 | `ui_discovery.py`가 production router를 우회하고 API 키를 URL query로 실어 보낸다

- 파일:
  - `lite_mode/bridge/ui_discovery.py:195-216`
  - `lite_mode/bridge/gemini_driver.py:186-193`
- 현상:
  - `_call_gemini_api()`는 `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key=...` 형식으로 raw HTTP 요청을 직접 보낸다.
  - `GeminiDriver`는 API 키가 있으면 `UIDiscovery`를 초기화하고 이 경로를 활성화한다.
  - 이 흐름은 프로덕션 `llm_router`/provider abstraction을 거치지 않는다.
- 영향:
  - provider 정책, 공통 retry/observability, 키 관리 규칙이 Lite Mode 경로에서 분기된다.
  - API 키가 query string에 실려 로컬 프록시/브라우저/로그 환경에서 더 넓게 노출될 수 있다.
- 기존 보고서와의 관계:
  - 기존 T1~T5 ledger에는 Lite Mode raw Gemini 경로가 정식 finding으로 올라오지 않았다.

### [S-T3-002] P2 | `lite_mode/test_ui_discovery.py`는 pytest형 이름을 가진 live-network 진단 스크립트다

- 파일:
  - `lite_mode/test_ui_discovery.py:15-44`
  - `lite_mode/test_ui_discovery.py:88-163`
  - `lite_mode/test_ui_discovery.py:166-200`
- 현상:
  - `test_api_call()`과 `test_api_discovery()`는 실제 API 키를 `.env`에서 읽어 live Gemini 호출을 수행한다.
  - 파일 하단은 `main()` 엔트리로 수동 실행 흐름까지 갖고 있다.
- 영향:
  - 이름은 테스트처럼 보이지만, hermetic/CI-safe 단위 테스트가 아니라 로컬 수동 진단 스크립트다.
  - 테스트 디렉토리/네이밍 관례와 충돌해 잘못된 기대를 만든다.
- 판정:
  - 코드 자체보다 **운영·테스트 분류가 잘못된 상태**다.

### [S-T3-003] P2 | host-bound 절대경로 + 직접 DB mutation 도구가 여러 세대에 걸쳐 잔존한다

- 파일:
  - `tools/normalize_arcs_db.py:7-8`, `85-113`
  - `tools/db_porter.py:9-12`, `66-123`
  - `tools/fix_future_items.py:7-11`, `74-99`
  - `tools/make_BP.py:9-12`, `20-25`
  - `tools/concat_txt.py:3-5`
  - `tools2/expand_ep15.py:13-24`, `35-80`
- 현상:
  - 여러 스크립트가 `C:\Users\...` 절대경로 또는 특정 프로젝트명/특정 DB 경로를 하드코딩한다.
  - 일부는 `UPDATE anchors ...`, `INSERT OR REPLACE ...`, `DELETE` 같은 직접 mutation을 수행한다.
  - 경로/대상 프로젝트/데이터 형식이 모두 개발자 로컬 환경 전제다.
- 영향:
  - 다른 환경에서는 즉시 깨지고, 같은 환경에서도 잘못된 대상 DB를 건드릴 위험이 있다.
  - "도구"라는 이름과 달리 범용 재사용보다 일회성 운영 스크립트 집합에 가깝다.
- 기존 보고서와의 관계:
  - `D-T5`의 일부 루트 스크립트 잔류와 결은 비슷하지만, 본 건은 **Lite/Tools 군 전체의 host-bound 패턴**을 묶어 새로 정리한 것이다.

### [S-T3-004] P2 | `blueprint_editor.py`는 DBManager 없이 SQLite를 직접 수정하고 외부 에디터 실행을 신뢰한다

- 파일:
  - `main_tools/blueprint_editor.py:23-33`
  - `main_tools/blueprint_editor.py:52-78`
  - `main_tools/blueprint_editor.py:81-96`
  - `main_tools/blueprint_editor.py:98-159`
- 현상:
  - Blueprint 조회/저장/삭제가 전부 `sqlite3.connect()` 직접 호출로 수행된다.
  - 저장 전 DB 백업, audit trail, DBManager guard는 없다.
  - 외부 편집기는 Windows 기본 연결, `open`, 혹은 Linux의 `EDITOR` 환경변수 값으로 그대로 실행한다.
- 영향:
  - 수동 편집 도구가 프로덕션 DB 경계와 분리돼 있다.
  - DB 일관성/복구 책임이 전적으로 사용자 수동 절차에 남는다.
- 판정:
  - 보안 취약점이라기보다 **운영 안전장치가 없는 수동 변조 도구**다.

---

## 생존/폐기 판정

### Lite Mode

- `lite_mode/bridge/gemini_driver.py`는 Selenium, Chrome remote debugging, `.env` 키 로딩, `gemini.google.com/app` 로그인 세션에 의존한다.
- 따라서 현재 트리에서 Lite Mode는 "경량 대체 프로덕션"이 아니라 **개인 작업 보조 환경**으로 보는 편이 정확하다.

### Tools

- `tools/`, `tools2/`, `main_tools/`에는 범용 도구와 1회성 수선 스크립트가 혼재한다.
- 절대경로/특정 작품명/직접 DB mutation이 있는 파일은 범용 도구로 간주하면 안 된다.

---

## 삭제 또는 격리 권고

- `lite_mode/test_ui_discovery.py`
  - 테스트 스위트가 아니라 수동 진단 스크립트로 분리 권고
- `tools/normalize_arcs_db.py`
  - 특정 DB 직접 mutation 레거시 스크립트로 격리 권고
- `tools/db_porter.py`
  - 범용 포터가 아니라 특정 DB 운영 도구로 명시 필요
- `tools/fix_future_items.py`
  - 특정 작품 수선 스크립트로 분리 권고
- `tools/make_BP.py`, `tools/concat_txt.py`, `tools2/expand_ep15.py`
  - host-bound 1회성 스크립트로 묶어 archive 또는 legacy 폴더 이동 권고

---

## 3PASS 감리 로그

### PASS 1 — 후보 9건

- raw Gemini direct call
- live API dependent tests
- Selenium/Chrome remote-debugging 의존
- host-bound absolute paths
- direct DB mutation scripts
- blueprint editor DB bypass
- external editor trust boundary
- tool dead code 여부
- tool 범용성 여부

### PASS 2 — 제거 5건

- Selenium 의존 자체: Lite Mode 설계 특성으로 간주
- tool dead code 일반론: 파일별 활성도보다 host-bound 패턴이 핵심
- 범용성 부족 일부: 단순 편의 스크립트 수준으로 하향
- `open_in_editor()` 단독 command injection: shell 문자열 결합이 아니라 argv 배열 사용
- raw Gemini 경로와 live test를 하나로 합칠지 여부: 성격이 달라 분리 유지

### PASS 3 — 최종 4건 확정

- `PASS1 9건 → PASS2 5건 제거 → 최종 4건 확정`

---

## 결론

Lite Mode & Tools 심층 감사의 결론은 "레거시가 좀 남아 있다" 정도가 아니다. 현재 이 영역은 **로컬 세션·로컬 DB·로컬 경로에 강하게 결박된 수동 운영 도구 묶음**이며, production abstraction을 우회하는 경로도 일부 남아 있다.

후속 조치 우선순위는 다음과 같다.

1. Lite Mode raw Gemini 호출과 live-network 진단 스크립트를 명시적으로 `manual-only`로 재분류
2. 절대경로·특정 작품 하드코딩 도구를 `legacy/` 또는 `archive/`로 격리
3. DB를 직접 만지는 수동 도구는 최소한 대상/백업/위험 표시를 붙여 운영 범위를 축소
