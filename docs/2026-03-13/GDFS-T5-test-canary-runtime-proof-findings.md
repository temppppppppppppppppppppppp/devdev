# GDFS T5 Test / Canary / Runtime Proof Findings

작성일: 2026-03-13
상태: `PASS3 complete`
범위: `tests/test_api_contract.py`, `tests/test_bridge_quality_summary.py`, `tests/test_run_stage4_canary.py`, `tests/test_stage4_canary_tools.py`, `modules/core/stage4_canary_tools.py`, `scripts/run_stage4_canary.py`, archived canary artifacts, runtime-proof note/docs
조사 모드: `read-only`, `test-and-artifact cross-check`, `UTF-8 only`

## Executive Summary

- canary pre-run fail-open 의심은 현재 archived proof 기준으로 기각된다.
- 이미 별도 SSOT에 남겨 둔 Stage 0 POV refresh, `0w` continuity proof, `03` integrity proof는 재오픈하지 않는다.
- retained issue는 세 가지다.
  - contract regression이 T4의 requiredness/WS drift를 잡지 못한다.
  - canary green은 여전히 최신 rationale/provenance sink proof를 자동으로 닫지 못한다.
  - archive locator note는 지금 workspace 사실과 충돌해 operator evidence reopen을 오도한다.

## PASS 1 - 후보 수집

- 후보 A: API contract regression이 live surface semantic drift를 놓친다
- 후보 B: canary green이 March 13 rationale sink hardening proof까지 닫는지 불명확하다
- 후보 C: archived proof path drift가 여전히 current workspace에서 reopening을 막는다
- 후보 D: prep-only canary analyze가 fail-open으로 풀렸을 수 있다
- 후보 E: Stage 0 POV refresh / `0w` / `03` runtime proof 부족

## PASS 2 - 교차 검증

### 제거 1. prep-only canary fail-open suspicion

- `projects/기록용/00_test_06/logs/canary_summary.json:17,20-24`는 `status=fail`과 `pass_rate_monitor_missing`, `sink_alignment_summary_empty`, `runtime_audit_summary_missing`를 그대로 보존한다.
- 판정: fail-open 의심 기각.

### 제거 2. Stage 0 POV refresh / `0w` / `03` runtime proof 부족 재오픈

- 이 세 축은 기존 runtime-proof / four-project ledger가 이미 `runtime-only` 또는 `stale-artifact`로 분리해 둔 상태와 현재 artifact가 일치한다.
- 판정: `already-covered-do-not-reopen`.

## PASS 3 - 최종 확정 Findings

### [GDFS-T5-001] API contract regression은 path subset만 잠그고 semantic surface drift를 놓친다

- Severity: `P2`
- 현상 요약:
  - current contract regression은 server URL, HTTP path subset, error code enum, status enum만 확인한다.
  - 그래서 `project` requiredness drift와 websocket `/events` omission이 green test 상태로 남을 수 있다.
- 코드 근거:
  - `tests/test_api_contract.py:541-567`
  - `docs/implementation/api-contract-v1.yaml:111,146,181`
  - `tests/test_bridge_quality_summary.py:59-64`
  - `docs/implementation/api-contract-v1.yaml`에는 `/events` path 부재
- downstream 영향 경계:
  - OpenAPI/formal contract trust
  - desktop bridge caller confidence
  - future regression gate의 false green
- 현재 테스트 근거 또는 테스트 부재:
  - quality summary만 missing-project reject regression이 있다.
  - dashboard/safe-ops missing-project reject를 잠그는 테스트가 없다.
  - websocket `/events` contract를 잠그는 테스트가 없다.
- baseline과의 관계:
  - `related-but-new-test-illusion-surface`
- 권장 후속 조치:
  - contract regression에 query requiredness assert를 추가한다.
  - dashboard/safe-ops missing-project reject regression을 추가한다.
  - `/events` formal contract 또는 dedicated desktop event spec regression을 추가한다.

### [GDFS-T5-002] canary green은 current rationale/provenance sink proof를 자동으로 닫지 못한다

- Severity: `P2`
- 현상 요약:
  - archived clean canary는 draft count, sink alignment, hard gate pass를 보여 준다.
  - 그러나 이 proof는 March 13 이후 richer rationale/provenance sink가 실제 live row에 채워졌는지까지는 증명하지 못한다.
- 코드 근거:
  - `modules/core/stage4_canary_tools.py:86-151`
  - `modules/core/stage4_canary_tools.py:257-322`
  - `scripts/run_stage4_canary.py:83-114`
  - `projects/기록용/00_test_07/logs/canary_summary.json:48,75,77-78`
  - `tests/test_run_stage4_canary.py:7-52`
  - `tests/test_stage4_canary_tools.py:105-232`
- downstream 영향 경계:
  - canary `pass`를 observability/rationale closure의 전부로 오판하는 경로
  - DB-only postmortem 신뢰도
  - runtime proof matrix
- 현재 테스트 근거 또는 테스트 부재:
  - canary runner tests는 save/flush/analyze orchestration과 synthetic summary gate만 잠근다.
  - canary pass artifact와 current `stage_attempts` rationale/provenance 컬럼 populated 여부를 결합하는 end-to-end 회귀는 없다.
- baseline과의 관계:
  - `related-but-retained`
  - 기존 `ROP-T5-001`을 current global track에서 carry-forward했다.
- 권장 후속 조치:
  - fresh canary 또는 equivalent rerun 1회를 새 project로 남기고 DB rationale/provenance row까지 함께 캡처한다.
  - canary analyze 후 companion DB audit를 필수 단계로 고정한다.

### [GDFS-T5-003] archive locator note가 현재 workspace의 archived canary proof 존재와 충돌한다

- Severity: `P2`
- 현상 요약:
  - archive locator note는 `projects/기록용/00_test_07`도 없고 `canary_summary.json`도 없다고 적는다.
  - 하지만 현재 workspace에는 `projects/기록용/00_test_05`, `00_test_06`, `00_test_07`의 canary summary가 실제로 존재한다.
  - 이 note는 generic path drift를 넘어, operator에게 “reopenable proof가 없다”는 거짓 신호를 준다.
- 코드 근거:
  - `docs/2026-03-13/stage4-canary-archive-locator-note.md:8-10,31`
  - `projects/기록용/00_test_07/logs/canary_summary.json:3,77-78`
  - `projects/기록용/00_test_06/logs/canary_summary.json:17,20-24`
  - actual archived files:
    - `projects/기록용/00_test_05/logs/canary_summary.json`
    - `projects/기록용/00_test_06/logs/canary_summary.json`
    - `projects/기록용/00_test_07/logs/canary_summary.json`
- downstream 영향 경계:
  - runtime-proof reopening
  - archived evidence retrieval
  - audit note trustworthiness
- 현재 테스트 근거 또는 테스트 부재:
  - archive relocation or evidence-index freshness를 검증하는 자동화는 없다.
  - runtime-proof docs freshness를 감시하는 regression도 없다.
- baseline과의 관계:
  - `operator-surface-mismatch`
  - 기존 `ROP-T5-002`의 path drift를 넘어서, current locator note 자체가 false라는 새 증거가 생겼다.
- 권장 후속 조치:
  - locator note를 현재 archived path 사실에 맞게 갱신한다.
  - archived proof index를 별도 문서로 고정하고 `project_root` stale caveat를 함께 남긴다.

## PASS 요약

- PASS1 후보: `5`
- PASS2 제거: `2`
  - prep-only canary fail-open suspicion
  - already-covered runtime-only proof gaps
- PASS3 확정: `3`
  - `GDFS-T5-001`
  - `GDFS-T5-002`
  - `GDFS-T5-003`

## Resume Packet

- `Current phase`: `T5 completed`
- `Last completed pass`: `PASS 3`
- `Last completed surface`: `test-contract gate + canary proof + archived runtime evidence`
- `Next surface`: `T6 tools / lite mode / legacy live consumer / residue`
- `Reopen reason codes used`: `operator-surface-mismatch`, `new-consumer-scope`
- `Stop gate or blocker`: `none`
