# GDFS T6 Tools / Lite Mode / Legacy Live Consumer / Residue Findings

작성일: 2026-03-13
상태: `PASS3 complete`
범위: `lite_mode/`, `tools/`, `tools2/`, `main_tools/`, root `main.js`, `geuldobi-desktop/main.js`, `temp-*`, `MagicMock/`
조사 모드: `read-only`, `live-consumer classification`, `UTF-8 only`

## Executive Summary

- `lite_mode/test_ui_discovery.py` pytest-like naming 이슈는 현재 파일 rename으로 닫혔다.
- 하지만 manual-only로 분류해야 할 우회 경로와 stale shadow surface는 여전히 남아 있다.
- retained issue는 네 가지다.
  - Lite Mode raw Gemini path는 production router를 우회한다.
  - shadow Electron mains가 active shell과 이미 갈라졌다.
  - 여러 도구가 특정 프로젝트/DB를 직접 mutation하는 host-bound manual surface로 남아 있다.
  - `MagicMock/`, root `temp-*` 같은 residue가 live defect와 섞여 보일 수 있다.

## PASS 1 - 후보 수집

- 후보 A: Lite Mode raw Gemini direct-call
- 후보 B: pytest형 live-network probe
- 후보 C: shadow Electron main files
- 후보 D: direct SQLite mutation / hardcoded project tools
- 후보 E: temp debug scripts / MagicMock residue

## PASS 2 - 교차 검증

### 제거 1. pytest형 `lite_mode/test_ui_discovery.py` misclassification

- 현재 해당 파일은 존재하지 않는다.
- 대신 `lite_mode/manual_ui_discovery_probe.py:5`는 manual-only probe임을 명시하고 pytest collection path 밖에 두었다.
- 판정: old naming/collection issue는 `live-code-changed`로 닫힘.

## PASS 3 - 최종 확정 Findings

### [GDFS-T6-001] Lite Mode는 여전히 production router를 우회하는 raw Gemini live consumer를 유지한다

- Severity: `P2`
- 현상 요약:
  - Lite Mode는 UI 자동 탐지 단계에서 raw Gemini HTTP 호출을 직접 사용한다.
  - manual probe 파일도 pytest collection에서는 빠졌지만, 여전히 same path를 전제로 한 live API/manual workflow를 유지한다.
- 코드 근거:
  - `lite_mode/bridge/ui_discovery.py:197-212`
  - `lite_mode/bridge/ui_discovery.py:199`
  - `lite_mode/bridge/gemini_driver.py:194`
  - `lite_mode/manual_ui_discovery_probe.py:5,17`
- downstream 영향 경계:
  - Lite Mode operator workflow
  - local browser/session based automation
  - provider policy / observability split
- 현재 테스트 근거 또는 테스트 부재:
  - manual probe는 pytest collection 밖으로 이동했지만 hermetic regression으로 대체되지 않았다.
  - raw Gemini path가 production router와 동일 정책을 따르는지 검증하는 regression은 없다.
- baseline과의 관계:
  - `related-but-retained`
  - 기존 `S-T3-001` root cause가 현재 코드에도 남아 있다.
- 권장 후속 조치:
  - Lite Mode를 공식적으로 `manual-only` surface로 고정한다.
  - production abstraction을 따르지 않는 raw provider path를 문서와 폴더 레벨에서 분리한다.

### [GDFS-T6-002] shadow Electron main surfaces가 active shell과 split-brain 상태로 남아 있다

- Severity: `P2`
- 현상 요약:
  - active package entry는 `geuldobi-desktop/src/main.js`다.
  - 그러나 `geuldobi-desktop/main.js`와 workspace root `main.js`가 별도로 남아 있고, live shell과 이미 기능이 갈라졌다.
  - 특히 root `main.js`는 `approvalId` forwarding도 없고 work_guard template IPC도 없다.
- 코드 근거:
  - `geuldobi-desktop/package.json:5`
  - `geuldobi-desktop/src/main.js:395,400,761,774`
  - `geuldobi-desktop/main.js:395,400`
  - `main.js:315,331`
  - `tests/test_desktop_work_guard_template_contract.py:5,17,23-29`
- downstream 영향 경계:
  - desktop shell maintenance
  - local manual launch/debug path
  - operator/developer가 잘못된 main file을 수정하거나 읽는 경우
- 현재 테스트 근거 또는 테스트 부재:
  - desktop contract test는 `geuldobi-desktop/src/main.js`만 읽는다.
  - shadow files가 stale 상태로 남아 있어도 실패시키는 regression은 없다.
- baseline과의 관계:
  - `related-but-retained`
  - 기존 `FBX-T5-002`, `FGS-T3-001`, `GMR-G-002`, `D-T5-001`의 current carry-forward다.
- 권장 후속 조치:
  - `geuldobi-desktop/main.js`와 root `main.js`를 `dead/stale/manual debug only` 중 하나로 공식 분류한다.
  - live entry 문서와 tests가 shadow files를 비활성 surface로 명시하도록 맞춘다.

### [GDFS-T6-003] host-bound direct DB mutation 도구가 manual-only guard 없이 남아 있다

- Severity: `P2`
- 현상 요약:
  - 여러 도구가 특정 작품 DB 경로를 하드코딩하거나 `sqlite3.connect()`로 직접 mutation한다.
  - 일부는 대상 DB 백업/guard 없이 바로 `UPDATE`, `INSERT OR REPLACE`, `DELETE`를 수행한다.
- 코드 근거:
  - `tools/normalize_arcs_db.py:7,109`
  - `tools2/expand_ep15.py:13,100`
  - `tools2/style_transfer.py:19,26`
  - `main_tools/blueprint_editor.py:16,33,44,61,64,76,78`
- downstream 영향 경계:
  - legacy/manual project surgery
  - 특정 작품 대상 수선 스크립트
  - operator가 범용 도구로 오인할 수 있는 local mutation path
- 현재 테스트 근거 또는 테스트 부재:
  - 이 도구군을 범용/안전한 manual surface로 검증하는 regression은 없다.
  - `blueprint_editor.py`는 manual-only notice를 추가했지만 DBManager guard나 backup enforcement는 없다.
- baseline과의 관계:
  - `related-but-retained`
  - 기존 `S-T3-003`, `S-T3-004`를 current workspace 기준으로 재확인했다.
- 권장 후속 조치:
  - `tools*`와 `main_tools/`에서 host-bound mutation scripts를 `legacy/` 또는 `manual-only/`로 재분류한다.
  - 최소한 대상 project 표시와 backup precondition을 파일 헤더/문서에 고정한다.

### [GDFS-T6-004] residue artifact와 temp debug script가 live defect 해석을 오염시킬 수 있다

- Severity: `P3`
- 현상 요약:
  - `MagicMock/` soft-failure residue와 root `temp-*` debug scripts가 현재 workspace에 실제로 남아 있다.
  - 이들은 active runtime surface는 아니지만, live defect처럼 읽히기 쉬운 증거 오염원이다.
- 코드 근거:
  - residue:
    - `MagicMock/mock.current_project.paths.root/*/logs/soft_failures.jsonl`
  - temp debug scripts:
    - `temp-electron-paths.js`
    - `temp-proc-poll.ps1`
    - `temp-proc-poll-oswarn.ps1`
    - `temp-proc-trace.ps1`
    - `temp-run-packaged.ps1`
    - `temp-run-packaged-ascii.ps1`
  - sample content:
    - `temp-electron-paths.js`
    - `temp-run-packaged.ps1`
- downstream 영향 경계:
  - live artifact inventory
  - audit evidence reading
  - manual cleanup / packaging sanity check
- 현재 테스트 근거 또는 테스트 부재:
  - residue 존재 자체를 fail시키는 regression이나 workspace hygiene gate는 없다.
- baseline과의 관계:
  - `related-but-retained`
  - 기존 `D-T5-014`와 system-wide residue observation을 current workspace에서 재확인했다.
- 권장 후속 조치:
  - residue와 temp scripts를 live inventory에서 제외하는 규칙을 문서에 계속 명시한다.
  - cleanup 단계가 따로 열리면 `MagicMock/`와 root `temp-*`를 정리 대상으로 묶는다.

## PASS 요약

- PASS1 후보: `5`
- PASS2 제거: `1`
  - pytest형 Lite Mode probe naming issue
- PASS3 확정: `4`
  - `GDFS-T6-001`
  - `GDFS-T6-002`
  - `GDFS-T6-003`
  - `GDFS-T6-004`

## Resume Packet

- `Current phase`: `T6 completed`
- `Last completed pass`: `PASS 3`
- `Last completed surface`: `lite_mode + tools/manual surfaces + shadow Electron main + residue`
- `Next surface`: `global consolidated findings`
- `Reopen reason codes used`: `live-code-changed`, `new-consumer-scope`, `operator-surface-mismatch`
- `Stop gate or blocker`: `none`
