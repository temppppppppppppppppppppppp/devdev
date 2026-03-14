# GMR-D Control Plane, Bridge & Desktop Findings

> Date: 2026-03-13
> Commit: `d9825a69`
> Workspace State: dirty

## PASS 1 관찰

- `bridge_server.py`는 `ProcessRunner`를 통해 `main_a.py` subprocess를 제어한다.
- `process_runner.py`는 menu key, sub_key, Mode A/B stdin 주입을 유지한다.
- `geuldobi-desktop/package.json`의 active Electron entry는 `src/main.js`다.

## PASS 2 교차 검증

- `geuldobi-desktop/src/main.js:395-402`는 renderer IPC를 `/run` HTTP body로 변환한다.
- `modules/api/bridge_server.py:1265-1363`는 `validate_run_request()` -> `RiskApprovalGate.validate()` -> `ProcessRunner.start()` 순서다.
- `modules/api/risk_approval.py`의 `register()` 호출은 검색상 테스트에서만 확인되며, lifespan 초기화는 빈 `RiskApprovalGate()`를 만든다.

## PASS 3 최종 findings

### [GMR-D-001] 데스크톱 제어면은 domain-native API가 아니라 CLI protocol wrapper다

- Severity: `P2`
- Evidence:
  - `modules/api/process_runner.py:1-120`
  - `modules/api/bridge_server.py:1265-1363`
  - `main_a.py:2283-2333`
- Why macro risk:
  - UI가 직접 stage API를 호출하는 구조가 아니라 콘솔 키/프롬프트 프로토콜을 HTTP/WS로 감싼 구조다.
  - 엔진 메뉴 계약이 바뀌면 desktop/backend가 동시에 깨질 수 있다.

### [GMR-D-002] risk approval gate는 live 등록 경로가 없어 운영상 closed gate 상태다

- Severity: `P1`
- Evidence:
  - `modules/api/bridge_server.py:1233-1247`
  - `modules/api/risk_approval.py:97-180`
  - `tests/test_bridge_server_desktop_risk_gate.py:56-80`
- Why macro risk:
  - 서버는 `approval_id`를 요구하지만, lifespan에서는 빈 in-memory store만 만들고 실제 approval record를 로드/등록하는 운영 경로가 없다.
  - 현재 구현 기준으로 risk key는 “정책상 보호됨”을 넘어 “실운영에서 통과시킬 수단이 문서화되지 않은 상태”에 가깝다.
- Recommended next order:
  - approval record source와 load path를 별도 control-plane SSOT로 명시해야 한다.

### [GMR-D-003] active entry와 shadow copy가 동시에 남아 있어 desktop drift source가 존재한다

- Severity: `P2`
- Evidence:
  - `geuldobi-desktop/package.json:5`
  - `geuldobi-desktop/src/main.js:761-774`
  - `geuldobi-desktop/main.js`
  - 루트 `main.js`
- Why macro risk:
  - `src/main.js`만 active entry인데 shadow copy가 병존한다.
  - work guard template IPC는 `src/main.js`에만 있어, 잘못된 파일을 편집하면 변경이 제품에 반영되지 않는다.
- Recommended next order:
  - active/shadow file inventory를 문서 상단에 고정 표시.

## Last Verified
- Date: 2026-03-13
- Commit: `d9825a69`
- Workspace State: dirty
- Code Sync (Yes/No): Yes
- Verified By: Codex
