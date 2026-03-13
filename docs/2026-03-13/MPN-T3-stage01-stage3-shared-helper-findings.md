# [MPN-T3] Stage01 Shared Helper Findings

> 작성일: 2026-03-13
> 상태: `completed`
> 조사 모드: `static / read-only / code-and-test verification / UTF-8 only`
> 기준 오더: `main_a-persistence-narrative-detail-full-survey-audit-order.md`

코드 직접 수정 없이 `main_a.py`의 `_validate_volume_boundaries()`와 `Stage01Helpers.stage_1_volumes()` 소비 경계를 조사했다.

---

## 조사 범위

- `main_a.py`: `_validate_volume_boundaries()`, `_stage_1_volumes()`
- `modules/core/stage01_helpers.py`
- `modules/core/stage2_preflight.py`
- `modules/domain/agents/analyst.py`
- `modules/protocols/app_services.py`
- `docs/stage_map/stage1.md`

## 필수 근거

- `tests/test_stage01_helpers.py`
- `tests/test_stage01_fixes.py`
- `tests/test_stage2_pipeline.py`
- `tests/test_ui_service.py`
- `docs/stage_map/stage1.md`

## 실행 로그

- `pytest tests/test_stage01_helpers.py tests/test_stage01_fixes.py tests/test_ui_service.py -q` -> `69 passed`
- `pytest tests/test_stage2_pipeline.py -q -k "plan_single_volume or tactic_to_strategy or protagonist_config"` -> `1 passed, 79 deselected`

## PASS 기록

- PASS 1: 후보 4건 수집
  - 비문자열 `strategy_doc` fail-open
  - `Stage01Helpers`의 `main_a.py` private helper 결합
  - Stage 1 성공 경로 테스트의 callback 우회
  - 문서-코드 간 `WARNING` 정책 drift 가능성
- PASS 2: `WARNING` 정책 drift 후보 제거
  - `docs/stage_map/stage1.md:107-110`와 `main_a.py:2640-2647`가 동일하게 `WARNING`은 통과, `REJECT`만 차단으로 정렬되어 있음
- PASS 3: 최종 3건 확정
  - `[MPN-T3-001]`
  - `[MPN-T3-002]`
  - `[MPN-T3-003]`

## Finding Ledger

| ID | Sev | 상태 | 파일/함수 | 요약 |
|----|-----|------|-----------|------|
| [MPN-T3-001] | P1 | confirmed | `main_a.py::_validate_volume_boundaries` | 비문자열 `strategy_doc`가 경계 검증을 우회한 채 Stage 2 입력으로 전파된다. |
| [MPN-T3-002] | P2 | confirmed | `modules/core/stage01_helpers.py::stage_1_volumes` | Stage 1 helper가 `main_a.py` private validator에 숨은 결합을 유지해 facade 분리 회귀 위험이 남아 있다. |
| [MPN-T3-003] | P2 | confirmed | `tests/test_stage01_helpers.py` | Stage 1 성공 경로 테스트가 실제 boundary callback을 실행하지 않아 길이/경계/invalid 구조 검증 공백이 남아 있다. |

---

## [MPN-T3-001] 비문자열 `strategy_doc` fail-open으로 권 경계 검증 우회

1. ID
   - `[MPN-T3-001]`
2. Severity
   - `P1`
3. 현상 요약
   - `_validate_volume_boundaries()`는 `strategy_doc`가 문자열이 아니면 즉시 `PASS`를 반환한다.
   - 반면 `Stage01Helpers.stage_1_volumes()`는 dict 형태 `strategy_doc`를 길이 계산용으로만 JSON 문자열화한 뒤 원본 `vol_data`를 그대로 `volumes` 앵커에 저장한다.
   - 이후 Stage 2는 저장된 `strategy_doc`를 다시 문자열화하거나 그대로 prompt 인자로 전달하므로, 구조화된 전략 문서가 미래 권 누수 검증 없이 downstream 입력으로 유입될 수 있다.
4. 코드 근거
   - `main_a.py:2620-2623`에서 비문자열 `strategy_doc`를 무조건 `PASS` 처리한다.
   - `modules/core/stage01_helpers.py:768-776`은 dict `strategy_doc`를 길이 계산에는 허용한 뒤 같은 `vol_data`로 boundary check를 호출한다.
   - `modules/core/stage01_helpers.py:808-813`은 후처리에서도 dict `strategy_doc`를 허용하고 원본 `vol_data`를 `final_volumes`에 적재한다.
   - `modules/domain/agents/analyst.py:283-301`은 `strategy_doc` 존재와 `vol_no`만 보정할 뿐 타입 정규화를 하지 않는다.
   - `modules/core/stage2_preflight.py:376-379`는 `current_vol_strategy["strategy_doc"]`를 `str(...)`로 prompt focus에 주입한다.
   - `modules/core/stage2_preflight.py:1259-1281`는 같은 값을 Stage 2 생성/패치 입력 `vol_strategy`로 그대로 사용한다.
   - `tests/test_ui_service.py:118-123`는 dict `strategy_doc`가 downstream 표시 계층에서 허용되는 계약임을 보여준다.
5. downstream 영향 경계
   - Stage 1 `volumes` 앵커 오염
   - `current_project.volumes` 메모리 상태 오염
   - Stage 2 preflight work-focus 텍스트
   - Stage 2 `four_phase.generate()` / `patch_arc_with_feedback()`의 `vol_strategy` 입력
6. 현재 테스트 근거 또는 테스트 부재
   - `_validate_volume_boundaries()` 직접 테스트는 발견되지 않았다. 검색 결과 정의/호출은 `main_a.py:2618`, `modules/core/stage01_helpers.py:776` 두 곳뿐이다.
   - `tests/test_stage01_helpers.py:529-544`는 validator를 `{"status": "PASS"}`로 고정하고 success tuple만 주입해 실제 경계 검증 의미를 확인하지 않는다.
7. 기존 문서와의 중복 여부
   - `none`
8. 권장 후속 조치
   - `_validate_volume_boundaries()`가 dict/list를 fail-open 하지 않도록 직렬화 기반 검증 또는 fail-closed 경고를 추가한다.
   - Stage 1에서 `strategy_doc`를 저장 전에 문자열로 정규화하거나, 비문자열이면 별도 schema 오류로 재시도시킨다.
   - 단위 테스트에 `str`, `dict`, `None`, 미래 권 번호 포함 payload를 직접 추가한다.

## [MPN-T3-002] Stage 1 helper가 `main_a.py` private validator에 숨은 결합 유지

1. ID
   - `[MPN-T3-002]`
2. Severity
   - `P2`
3. 현상 요약
   - `main_a.py`는 Stage 1 실행 자체를 `Stage01Helpers.stage_1_volumes()`로 thin delegate 했지만, 권 경계 검증은 여전히 `main_a.py` private method `_validate_volume_boundaries()`에 남겨 두었다.
   - 따라서 Stage01 helper는 독립 helper 모듈처럼 보이지만 실제로는 `SovereignApp`의 사설 메서드 존재를 전제로 한다.
   - facade/service 분리 관점에서 이 의존성은 명시적 protocol에도 올라와 있지 않아 회귀가 런타임까지 밀릴 수 있다.
4. 코드 근거
   - `main_a.py:2498-2500`은 Stage 1 엔트리를 `Stage01Helpers`로 위임한다.
   - `modules/core/stage01_helpers.py:776-785`는 성공 판정 핵심 로직에서 `app._validate_volume_boundaries(...)`를 직접 호출한다.
   - `docs/stage_map/stage1.md:66-71`은 `_validate_volume_boundaries`를 `main_a.py` 의존성으로 적시한다.
   - `docs/stage_map/stage1.md:172-174`는 이 helper가 `main_a.py`에 남아 있어 재사용성과 테스트 분리가 약하다고 이미 open risk로 기록한다.
   - `modules/protocols/app_services.py:20-107`는 UI/Audit/Project protocol은 정의하지만 volume boundary validator에 해당하는 분리된 서비스 계약은 제공하지 않는다.
5. downstream 영향 경계
   - Stage01 helper의 독립 재사용 불가
   - `SovereignApp` 대체 app/facade 주입 시 런타임 결합 파손 위험
   - 향후 `main_a.py` facade 정리 또는 Stage 1 분리 시 callback/validator 회귀 집중
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_stage01_helpers.py:17-20`의 app fixture는 spec 없는 `MagicMock`이라 helper가 요구하는 app contract가 타입 수준에서 검증되지 않는다.
   - `tests/test_stage01_helpers.py:529-544`는 `_validate_volume_boundaries`를 임의 속성으로 추가해 통과시키므로, 실제 facade 계약이 누락돼도 테스트가 경고하지 못한다.
7. 기존 문서와의 중복 여부
   - `related-but-new-shared-helper-surface`
8. 권장 후속 조치
   - `_validate_volume_boundaries()`를 `Stage01Helpers` 내부로 이동하거나 별도 `Stage1ValidationService` 같은 명시적 계약으로 승격한다.
   - Stage01 helper 테스트는 spec 있는 app double 또는 protocol 기반 fake를 사용해 숨은 의존성을 드러내야 한다.
   - facade 분리 전, Stage 1이 요구하는 app surface 목록을 독립 SSOT로 고정한다.

## [MPN-T3-003] Stage 1 성공 경로 테스트가 실제 boundary callback을 실행하지 않음

1. ID
   - `[MPN-T3-003]`
2. Severity
   - `P2`
3. 현상 요약
   - Stage 1의 핵심 성공 판정은 `_vol_on_success()` 내부에 있다.
   - 그러나 현재 성공 테스트는 `retry_with_feedback()` 전체를 mock해 `(result, attempts, passed)` tuple만 주입하므로 `_vol_on_success()`의 분량 검사, `_validate_volume_boundaries()` 호출, invalid 구조 거부 로직이 실제로는 실행되지 않는다.
   - 결과적으로 테스트 목록에는 "권 설계 성공 저장"이 있지만, 실제로는 저장 후처리만 확인하고 품질 게이트 의미는 검증하지 못한다.
4. 코드 근거
   - `modules/core/stage01_helpers.py:759-787`에 실제 성공 판정 로직이 들어 있다.
   - `tests/test_stage01_helpers.py:529-544`는 `_validate_volume_boundaries`를 `PASS`로 stub한 뒤 `retry_with_feedback` 반환값만 설정한다.
   - `tests/test_stage01_helpers.py:535-542`는 wrapper를 통째로 mock해 callback 체인을 우회한다.
   - `docs/stage_map/stage1.md:139-158`는 현재 테스트 범위를 단위 테스트 중심으로 적고, Stage 1 전용 E2E 부재를 별도 명시한다.
5. downstream 영향 경계
   - 길이 기준 회귀
   - boundary `REJECT` / `WARNING` semantics 회귀
   - invalid `vol_data` 구조 수용 회귀
   - facade 분리 과정에서 Stage 1 품질 게이트 무력화 회귀
6. 현재 테스트 근거 또는 테스트 부재
   - 실행한 관련 테스트는 모두 통과했지만, 통과 자체가 boundary semantics 보장을 의미하지는 않는다.
   - `tests/test_stage01_helpers.py`에는 `_validate_volume_boundaries()` 직접 테스트도 없고, dict/non-string `strategy_doc`, `WARNING` 경로, invalid `vol_data` 경로도 없다.
7. 기존 문서와의 중복 여부
   - `related-but-new-shared-helper-surface`
8. 권장 후속 조치
   - `retry_with_feedback()`를 완전 mock하지 않는 focused unit test를 추가해 `_vol_on_success()`가 실제로 실행되게 한다.
   - 최소 케이스로 `REJECT`, `WARNING`, `dict strategy_doc`, `strategy_doc` 누락, `vol_data` 비dict를 각각 검증한다.
   - Stage 1 전용 integration/e2e에서 multi-volume 누적과 boundary gate 상호작용을 검증한다.

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| Stage 1 다권 누적 + boundary 상호작용 | open | 실제 `context_accumulator`가 2권 이상에서 future leakage를 어떻게 증폭/완화하는지 integration 또는 e2e 로그 필요 |
| `WARNING` 정책의 운영 적합성 | open question | 현재 문서와 코드는 일치하나, `WARNING` 통과가 제품 의도인지 별도 운영 결정 기록 필요 |

## 마감 체크

- 코드 근거 포함: yes
- downstream 영향 경계 포함: yes
- 현재 테스트 근거 또는 테스트 부재 포함: yes
- 기존 문서와의 중복 여부 포함: yes
