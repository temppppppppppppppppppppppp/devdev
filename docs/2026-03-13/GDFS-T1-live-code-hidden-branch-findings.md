# GDFS-T1 Live Code Hidden Branch Findings

> 작성일: 2026-03-13
> 상태: `PASS3 confirmed`
> 조사 모드: `static / read-only / baseline-aware / UTF-8 only`
> 기준 오더: `docs/2026-03-13/global-detail-full-survey-master-audit-order.md`
> baseline 참조: `S-T1-stage0-ui-flow-deep-dive-findings.md`, `S-T2-cross-stage-root-cause-deep-dive-findings.md`, `D-T1-detail-infra-audit.md`, `main_a-cross-stage-semantic-preservation-detail-consolidated-findings.md`

---

## 요약

이번 T1의 목적은 기존 Stage 0 / cross-stage / infra detail 문서를 다시 복붙하는 것이 아니라, **현재 코드 기준으로 아직 살아 있는 hidden-branch 성격의 live-path 결함만 retained set으로 재구성하는 것**이다.

결론:

- 신규 P0는 없다.
- retained P1 1건, retained P2 2건을 확인했다.
- 기존 baseline 중 `S-T1-001 외부 시점 정책 저장 오염`은 현재 코드에서 해소되어 재오픈하지 않았다.

핵심은 아래 3건이다.

1. `Stage3 -> Stage2 reverse feedback`는 여전히 consumer만 있고 live producer가 없다.
2. `plot_roadmap`는 여전히 생성 결과가 아니라 save hook에서만 보정된다.
3. `ReflexionManager`는 여전히 `DBManager`의 transaction contract를 우회해 직접 commit한다.

---

## 조사 범위

- `modules/core/stage0/__init__.py`
- `modules/core/stage01_helpers.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/project_support.py`
- `modules/core/reflexion_manager.py`
- `tests/test_stage01_helpers.py`
- `tests/test_feedback_system.py`
- baseline 문서 4종

---

## PASS 1 후보

1. Stage 0 helper 경로의 외부 시점 정책 저장 드리프트
2. `plot_roadmap` 생성 경계 미보장
3. `Stage3 -> Stage2` reverse feedback dead branch
4. `ReflexionManager` direct commit bypass
5. `stage0/__init__.py` 메뉴 mojibake 잔존

---

## PASS 2 제거

### 제거 1. Stage 0 helper 경로 외부 시점 정책 저장 드리프트

- 기존 baseline:
  - `S-T1-001`
- 현재 코드:
  - `modules/core/stage01_helpers.py:201-230`는
    - `EXTERNAL_POV_INSERT_POLICY_OPTIONS`
    - `default_external_pov_insert_policy(...)`
    - `resolve_external_pov_insert_policy_choice(...)`
    경로를 사용한다.
- 판정:
  - `live-code-changed`
  - baseline 시점 결함은 현재 트리에서 재현되지 않으므로 reopen 금지

### 제거 2. `stage0/__init__.py` 메뉴 mojibake 잔존

- 기존 baseline:
  - `D-T1-002`
- 현재 코드:
  - `modules/core/stage0/__init__.py:303-329` 범위에서 POV/외부 시점 정책 메뉴는 UTF-8 정상 문자열로 읽힌다.
- 판정:
  - `live-code-changed`
  - 현재 T1 retained finding으로 올리지 않음

---

## PASS 3 확정 Findings

### [GDFS-T1-001] P1 | `Stage3 -> Stage2` reverse feedback는 현재도 consumer-only dead branch다

1. ID
   - `GDFS-T1-001`
2. Severity
   - `P1`
3. 현상 요약
   - `modules/core/stage2_preflight.py`는 `stage_rejection_history`에서 `stage == 3`이고 같은 `arc_no`인 실패가 3회 이상 쌓여야만 `generate_reverse_feedback_stage3_to_2(...)`를 주입한다.
   - 그러나 현재 live writer로 확인되는 `modules/core/stage2_finalizer.py`는 reject history에 항상 `"stage": 2`만 기록한다.
   - `modules/core/stage3_orchestrator.py`의 Stage 3 reject path는 `pass_rate_monitor`, `save_stage_attempt`, `save_director_selection`에는 기록하지만 `stage_rejection_history`에는 쓰지 않는다.
   - 결과적으로 `Stage3 -> Stage2 reverse feedback`는 consumer는 살아 있지만 producer가 없어 live runtime에서 사실상 dead branch다.
4. 코드 근거
   - `main_a.py:275` — `self.stage_rejection_history = []`
   - `modules/core/stage2_preflight.py:942-950` — `r.get("stage") == 3` 필터 + callback 호출
   - `modules/core/stage2_finalizer.py:1690-1698` — reject history append 시 `"stage": 2`
   - `modules/core/stage3_orchestrator.py:1850-1912` — Stage3 REJECT 기록은 남기지만 `stage_rejection_history` write 없음
5. downstream 영향 경계
   - `Stage3 blueprint reject 누적 -> Stage2 preflight retry planning`
   - Stage2는 원래 내려와야 할 Stage3 실패 semantic을 전혀 받지 못한다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_feedback_system.py:431-456`은 helper 단독 동작만 본다.
   - live producer/consumer alignment를 잠그는 통합 테스트는 없다.
7. baseline과의 관계
   - `related-but-retained`
   - `MCS-T2-001`과 같은 루트코즈이며, 현재 코드 재확인 결과 여전히 open
8. 권장 후속 조치
   - Stage3 REJECT path가 `stage_rejection_history`에 최소 `stage=3`, `arc_no`, `reason`을 기록하게 하거나
   - Stage2가 별도 Stage3 reject ledger를 읽게 구조를 바꿔야 한다.

### [GDFS-T1-002] P2 | `plot_roadmap` 계약은 여전히 생성 결과가 아니라 save hook에서만 보정된다

1. ID
   - `GDFS-T1-002`
2. Severity
   - `P2`
3. 현상 요약
   - `StageZeroManager.generate_from_concept()`는 Bible/Treatment를 생성하지만, 반환 직전 `plot_roadmap`를 강제 주입하지 않는다.
   - 실제 보장은 `Stage01Helpers._s0_save_results()`의 `_ensure_plot_roadmap()` save hook에서 이뤄진다.
   - 즉 Stage 2가 요구하는 핵심 필드는 생성기 산출물의 intrinsic contract가 아니라 저장 경계 patch에 기대고 있다.
4. 코드 근거
   - `modules/core/stage0/__init__.py:369-404` — `generate_from_concept()`는 `expander.generate_bible(...)` 후 바로 반환
   - `modules/core/stage01_helpers.py:566-592` — `_build_plot_roadmap_from_treatment()` / `_ensure_plot_roadmap()`
   - `tests/test_stage01_helpers.py:389-397` — save-time roadmap injection만 회귀 테스트로 잠김
5. downstream 영향 경계
   - `Stage 0 -> Stage 2` handoff
   - save 이전 in-memory consumer, 예외 중단 경로, helper 우회 경로는 불완전 Bible을 볼 수 있다.
6. 현재 테스트 근거 또는 테스트 부재
   - save hook 보정은 테스트가 있다.
   - 생성기 반환값 자체가 `plot_roadmap`를 내장하는지 검증하는 테스트는 없다.
7. baseline과의 관계
   - `related-but-retained`
   - `S-T2-001`의 현재형 재확인. 완전 해소가 아니라 `caller patch present` 상태
8. 권장 후속 조치
   - `plot_roadmap`를 save hook이 아니라 생성 결과 contract로 승격
   - `generate_from_concept()` 반환값 자체를 검증하는 테스트 추가

### [GDFS-T1-003] P2 | `ReflexionManager`는 여전히 `DBManager` transaction contract를 우회해 직접 commit한다

1. ID
   - `GDFS-T1-003`
2. Severity
   - `P2`
3. 현상 요약
   - `ReflexionManager`는 `execute_update()` 호출 직후 `self.context.db.conn.commit()`을 직접 부른다.
   - 이 구조는 `DBManager`의 commit 정책을 호출자 쪽으로 새게 만들고, `ReflexionManager`만 내부 구현인 `conn`에 직접 결합시킨다.
4. 코드 근거
   - `modules/core/reflexion_manager.py:94-103` — update 후 direct commit
   - `modules/core/reflexion_manager.py:109-117` — insert 후 direct commit
   - `modules/core/db_manager.py:1039-1047` — `execute_update()`는 execute만 하고 commit은 자체 수행하지 않음
5. downstream 영향 경계
   - reflexion memory write path
   - 다른 caller가 같은 write contract를 재사용할 때 commit semantics를 오해할 수 있다.
6. 현재 테스트 근거 또는 테스트 부재
   - reflexion write path의 transaction boundary를 잠그는 전용 테스트는 현재 조사 범위에서 찾지 못했다.
7. baseline과의 관계
   - `related-but-retained`
   - `D-T1-004`의 현재형 재확인
8. 권장 후속 조치
   - `DBManager`에 transaction-aware write contract를 올리거나
   - `ReflexionManager` 전용 persistence wrapper로 경계를 명확히 분리해야 한다.

---

## Current Phase / Resume Packet

1. `Current phase`
   - `T1 completed`
2. `Last completed pass`
   - `PASS3`
3. `Last completed surface`
   - `live code hidden branch`
4. `Next surface`
   - `T2 persistence / artifact / evidence layer`
5. `Reopen reason codes used`
   - `live-code-changed` for removed baseline items
6. `Stop gate or blocker`
   - `없음`

---

## 3PASS 요약

- `PASS1 5건 -> PASS2 2건 제거 -> PASS3 최종 3건 확정`
- 최종 retained set:
  - `P1 1건`
  - `P2 2건`
  - `P3 0건`
