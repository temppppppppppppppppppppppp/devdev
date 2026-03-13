# 체크리스트 3-Pass 코드 감리 결과

> 대상: `docs/2026-03-13/today-detail-sideeffect-connectivity-liverun-checklist.md`
> 재감리일: 2026-03-13
> 방법: 현재 워크트리 기준 코드 직접 확인 + 타깃 테스트 재실행
> 코드 수정: 있음 (Stage4 로그 경로/append 일관성 보정)

---

## 결론

이 문서의 이전 판정은 현재 코드와 맞지 않았다. 특히 아래 5개 주장은 더 이상 open defect로 둘 수 없다.

- Desktop risk approval boundary open
- Stage0 recovery menu silent wrong result open
- packaged mode project root divergence open
- `engine.exe` missing
- `build_release.ps1` incomplete

반대로, 이번 재감리에서 실제로 확인된 문제는 Stage4의 `episode_production.jsonl` 기록 경로가 프로젝트 루트를 따르지 않고 상대경로로 흘러갈 수 있다는 점이었다. 이 문제는 이번 감리 중 코드로 수정했다.

---

## 재검증 결과

### 닫힌 것으로 확인된 항목

| 항목 | 현재 판정 | 근거 |
|------|-----------|------|
| Desktop approval boundary | **Closed** | Desktop renderer가 위험 키 실행 전 `approvalId` 입력을 요구하고, preload/main이 `approval_id`를 backend로 전달하며, backend 테스트도 `403 RISK_APPROVAL_REQUIRED`를 검증한다. |
| Stage0 recovery POV silent default | **Closed** | `phase_0_recovery()`가 `POV_OPTIONS`/정규화 helper를 사용하고, 회귀 테스트도 정상 선택값 경로를 검증한다. |
| Packaged root divergence | **Closed** | Electron packaged 실행 시 `GEULDOBI_PROJECTS_ROOT`/`GEULDOBI_ENGINE_EXE`를 주입하고, runtime path resolver가 이를 우선 사용한다. |
| `engine.exe` missing | **Closed** | `dist/engine/engine.exe` 실파일 존재 확인. |
| `build_release.ps1` incomplete | **Closed** | Step 1에서 `engine.exe` 빌드를 수행하도록 구현되어 있다. |

### 문서 drift로 남는 항목

| 항목 | 현재 판정 | 메모 |
|------|-----------|------|
| `save_world_state_atomic` 관련 서술 | **Inaccurate** | public 함수는 아니지만, `Stage4PostProcessor._save_world_state_atomic()` private 메서드는 실제 존재한다. |
| Context 슬롯 수 서술 | **Drift** | 실측 기준 `Stage2=51`, `Stage3=24`, `Stage4=35`. |
| Ruff 수치 서술 | **Drift 가능성** | 문서 숫자는 재실측 결과와 맞춰야 하므로 고정 사실처럼 쓰면 안 된다. |

### 이번 감리에서 확인된 실제 결함

| ID | 항목 | 심각도 | 상태 |
|----|------|--------|------|
| AUDIT-20260313-STAGE4-LOG | `episode_production.jsonl`가 상대경로 `projects/<name>/logs`로 기록될 수 있어 실제 프로젝트 루트와 drift 가능 | **P3** | **Fixed in audit** |

문제 상세:

- `Stage4InterviewRound._append_episode_log()`
- `Stage4Orchestrator._log_escalation_event()`
- `Stage4PostProcessor` 일부 로그 디렉터리 준비 코드

위 경로들이 실제 `current_project.paths.root` 대신 상대경로 fallback에 의존할 수 있었다. 또한 `episode_production.jsonl` append 경로가 여러 곳에 흩어져 있어 향후 병렬 확장 시 일관성 리스크가 있었다.

---

## 적용한 수정

### 코드

- `modules/core/jsonl_io.py`
  - 프로세스 내 공용 `threading.Lock()` 기반 `append_jsonl_record()` 추가
- `modules/core/stage4_interview_round.py`
  - 로그 경로를 `resolve_project_log_dir(current_project)` 기준으로 우선 해석
  - JSONL append를 공용 helper로 통일
- `modules/core/stage4_orchestrator.py`
  - escalation event 기록도 동일한 로그 경로/append helper 사용
- `modules/core/stage4_post_processor.py`
  - 로그 디렉터리 생성 경로를 `_resolve_project_log_dir()` 기준으로 정렬

### 테스트

- `tests/test_stage4_interview_round.py`
  - 실제 프로젝트 루트로 로그가 기록되고 fallback 상대경로가 생성되지 않음을 검증하는 테스트 추가
- `tests/test_stage4_orchestrator.py`
  - escalation event도 동일 규칙을 따르는 테스트 추가

---

## 현재 판정

### 체크리스트 범위 기준 open set

| 레벨 | 상태 |
|------|------|
| P0 | **확인된 open 없음** |
| P1 | **확인된 open 없음** |
| P2 | **확인된 open 없음** |
| P3 | **이번 감리에서 1건 확인, 수정 완료** |

주의:

- 이 판정은 `today-detail-sideeffect-connectivity-liverun-checklist.md`가 주장하던 쟁점 범위 기준이다.
- 저장소 전체의 모든 잠재 이슈가 0건이라는 뜻은 아니다.

### Go / No-Go

현재 코드 기준으로는, 이 체크리스트가 주장하던 blocker들은 재현되지 않았다. 이번 감리에서 발견된 Stage4 로그 경로 결함도 수정했으므로, 체크리스트 범위 안에서는 추가 blocker를 확인하지 못했다.

---

## 검증

실행:

- `pytest -q tests/test_stage4_interview_round.py tests/test_stage4_orchestrator.py tests/test_stage4_post_processor.py tests/test_runtime_paths.py tests/test_process_runner.py tests/test_bridge_server_desktop_risk_gate.py tests/test_desktop_work_guard_template_contract.py tests/test_stage0_pov.py tests/test_stage01_helpers.py tests/test_project_support.py tests/test_stage4_canary_tools.py`
- `ruff check modules/core/jsonl_io.py modules/core/stage4_interview_round.py modules/core/stage4_orchestrator.py modules/core/stage4_post_processor.py tests/test_stage4_interview_round.py tests/test_stage4_orchestrator.py`

핵심 확인:

- Desktop approval 경계: 코드/테스트 기준 정상
- Stage0 POV recovery: 코드/테스트 기준 정상
- packaged root / engine.exe / release script: 현재 트리 기준 정상
- Stage4 로그 경로 drift: 수정 후 테스트 추가
