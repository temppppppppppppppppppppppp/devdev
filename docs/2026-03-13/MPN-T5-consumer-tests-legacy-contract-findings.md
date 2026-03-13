# [MPN-T5] Consumer Tests / Legacy Contract Findings

> 작성일: 2026-03-13
> 상태: `completed`
> 조사 모드: `static / read-only / code-and-test verification / UTF-8 only`
> 기준 오더: `main_a-persistence-narrative-detail-full-survey-audit-order.md`

코드 직접 수정 없이 Stage 2/3/4 consumer, 관련 테스트, legacy patch 문서의 shared helper 계약 회귀를 조사했다.

---

## 조사 범위

- `modules/core/stage2_context.py`
- `modules/core/stage3_context.py`
- `modules/core/stage4_context.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/services/project_service.py`
- `tests/test_stage2_finalizer.py`
- `tests/test_stage3_orchestrator.py`
- `tests/test_stage4_context.py`
- `tests/test_stage4_orchestrator.py`
- `tests/test_project_service.py`
- `tests/test_sweep36.py`
- `tests/test_stage234_fixes.py`
- `tests/e2e/test_l3_golden_route.py`
- `tests/e2e/test_l3_stage2_realproject.py`
- `tests/property/test_db_rollback_props.py`
- `tests/chaos/test_partial_commit.py`
- `docs/2026-02-23/opus_tf6_system_audit_order.md`
- `docs/2026-02-23/opus_tf6_patch_order.md`

## 필수 근거

- `tests/test_stage3_orchestrator.py`
- `tests/test_stage4_context.py`
- `tests/test_stage4_orchestrator.py`
- `tests/e2e/test_l3_golden_route.py`
- `tests/e2e/test_l3_stage2_realproject.py`
- `docs/2026-02-23/opus_tf6_system_audit_order.md`
- `docs/2026-02-23/opus_tf6_patch_order.md`

## 실행 로그

- `pytest tests/test_stage2_finalizer.py tests/test_stage3_orchestrator.py tests/test_stage4_context.py tests/test_project_service.py tests/test_sweep36.py -q` -> `133 passed in 3.35s`
- `pytest tests/e2e/test_l3_stage2_realproject.py::TestPipelineSmoke::test_stage2_runs_3_blocks -q -rs` -> `1 skipped`
  - `Real project DB not found: C:\Users\User\Desktop\글도비\projects\코덱스_테스트\project_data.db`
- `pytest tests/e2e/test_l3_golden_route.py::TestL3PipelineSmoke::test_stage2_pipeline_smoke_with_real_data -q -rs` -> `1 skipped`
  - `No *_tr_block_ALL.json found under treatments/`

## PASS 기록

- PASS 1: 후보 6건 수집
  - episode -> arc helper drift
  - Stage4의 `_safe_commit` 소비 의미 불일치
  - Stage2 smoke fixture의 `safe_commit_async` 계약 drift
  - Stage3 `from_app` 슬롯 테스트의 MagicMock auto-attr 오탐 가능성
  - `ProjectService` direct commit legacy drift 후보
  - Stage4 summary callback fail-open 후보
- PASS 2: 후보 2건 제거
  - `ProjectService` direct commit 경로는 T1 primary surface와 직접 중복되어 이 문서에서는 재오픈하지 않음
  - Stage4 summary callback fail-open은 T4 primary surface라 T5에서는 coverage gap만 유지
- PASS 3: 최종 4건 확정
  - `[MPN-T5-001]`
  - `[MPN-T5-002]`
  - `[MPN-T5-003]`
  - `[MPN-T5-004]`

## Finding Ledger

| ID | Sev | 상태 | 파일/함수 | 요약 |
|----|-----|------|-----------|------|
| [MPN-T5-001] | P1 | confirmed | `main_a.py::_calculate_arc_from_episode`, `modules/core/stage2_orchestrator.py` | Stage2 smart skip이 4화 기준 시스템 위에서 여전히 5화 버킷 helper를 소비하고, 테스트도 그 stale 계약을 함께 고정하고 있다. |
| [MPN-T5-002] | P2 | confirmed | `modules/core/stage4_orchestrator.py::stage_4_v2_chief_writer` | 같은 commit helper를 Stage2/3은 실패 게이트로 다루지만 Stage4는 예외 정리 경로에서 반환값을 무시한다. |
| [MPN-T5-003] | P2 | confirmed | `tests/e2e/test_l3_golden_route.py`, `tests/e2e/test_l3_stage2_realproject.py` | Stage2 smoke fixture가 `safe_commit_async -> bool` 계약을 잘못 모사하고, 두 smoke 모두 현재 workspace에서는 skip되어 commit semantics를 검증하지 못한다. |
| [MPN-T5-004] | P3 | confirmed | `tests/test_stage3_orchestrator.py::test_from_app_all_slots` | Stage3 DI slot coverage test가 unspecced `MagicMock` auto-attribute에 기대어 실제 app surface drift를 놓칠 수 있다. |

---

## [MPN-T5-001] Stage2 smart skip이 4화 시스템 위에서 5화 버킷 helper를 계속 소비

1. ID
   - `[MPN-T5-001]`
2. Severity
   - `P1`
3. 현상 요약
   - 중앙 설정은 이미 `EPISODES_PER_ARC = 4`로 이동했는데, `main_a.py::_calculate_arc_from_episode()`는 여전히 `// 5 + 1` 하드코딩을 유지한다.
   - `Stage2Orchestrator`는 원고가 존재할 때 smart skip 경고 경계 계산을 이 helper에 그대로 위임한다.
   - 결과적으로 5화, 9화, 13화 같은 경계에서 실제 아크 번호보다 1아크 늦게 판정할 수 있다.
   - 테스트 쪽은 이 drift를 잡지 못하는 수준이 아니라, 한쪽 테스트는 4를, 다른 쪽 테스트는 5를 동시에 SSOT처럼 고정하고 있다.
4. 코드 근거
   - `main_a.py:2524-2529`는 각 Arc를 5화로 가정한다.
   - `modules/core/constants.py:335-340`는 중앙 SSOT를 `EPISODES_PER_ARC = 4`로 정의한다.
   - `modules/core/stage2_orchestrator.py:219-224`는 manuscript 감지 후 `ctx.calculate_arc_from_episode(existing_ms_max_ep)`를 호출한다.
   - `tests/test_stage234_fixes.py:49-53`는 `DEFAULT_EP_COUNT == VolumeSettings.EPISODES_PER_ARC`를 검사해 4화 기준을 고정한다.
   - `tests/test_sweep36.py:51-56`는 오히려 `_calculate_arc_from_episode()` 내부에 `// 5 + 1` 문자열이 남아 있어야 통과하도록 고정한다.
   - `tests/e2e/test_l3_stage2_realproject.py:217-223`와 `tests/e2e/test_l3_golden_route.py:241-247`는 `calculate_arc_from_episode=lambda _ep: 0`으로 helper 자체를 우회한다.
5. downstream 영향 경계
   - Stage2 smart skip 경고 문구와 재개 기준 설명
   - manuscript-frontier와 Arc DB의 동기화 경고
   - frontier-lag 수동 운영 판단
   - helper를 재사용하는 다른 resume/diagnostic 경로의 경계값 판단
6. 현재 테스트 근거 또는 테스트 부재
   - 실행한 관련 테스트 133개는 모두 통과했지만, 그 안에 상충 계약이 동시에 존재한다.
   - 두 e2e smoke는 현재 workspace에서 모두 skip되었고, 설령 실행되더라도 `calculate_arc_from_episode`를 stubbed lambda로 대체해 실제 helper drift를 검증하지 않는다.
7. 기존 문서와의 중복 여부
   - `related-but-new-shared-helper-surface`
8. 권장 후속 조치
   - `_calculate_arc_from_episode()`를 `VolumeSettings.EPISODES_PER_ARC` 기반으로 계산하도록 통일한다.
   - `tests/test_sweep36.py`의 5화 고정 단언은 제거하거나 설정 기반 단언으로 바꾼다.
   - e2e/smoke는 helper를 lambda로 우회하지 말고 실제 구현을 호출한 상태에서 `ep=4/5/8/9` 경계 케이스를 추가한다.

## [MPN-T5-002] Stage4만 `_safe_commit` 반환값을 무시해 shared persistence 계약이 분기됨

1. ID
   - `[MPN-T5-002]`
2. Severity
   - `P2`
3. 현상 요약
   - 동일한 commit helper 계열을 Stage2와 Stage3는 실패 게이트로 취급한다.
   - 반면 Stage4는 `KeyboardInterrupt` 또는 일반 예외 정리 경로에서 `safe_commit()`을 호출만 하고 `False` 반환을 무시한다.
   - 결과적으로 shared helper의 의미가 stage마다 달라져, commit helper 변경이나 실패 상황에서 Stage4만 조용히 persistence 손실을 숨길 수 있다.
4. 코드 근거
   - `modules/core/stage2_finalizer.py:1091-1094`는 `safe_commit_async()`가 `False`를 반환하면 즉시 `RuntimeError`를 발생시킨다.
   - `modules/core/stage3_orchestrator.py:1503-1507`은 `safe_commit()` 실패를 `db_commit_error`로 기록하고 해당 화 처리를 중단한다.
   - `modules/core/stage4_orchestrator.py:1539-1549`는 interrupt/exception 정리 경로에서 `self.ctx.safe_commit()`을 호출만 하고 반환값을 확인하지 않는다.
   - `tests/test_stage4_orchestrator.py:205-217`과 `tests/test_stage4_orchestrator.py:232-244`는 Stage4 cleanup에서 `safe_commit`이 "호출되었는지"만 본다.
   - `tests/test_stage4_context.py:267-273`도 callback wiring과 1회 호출만 검증한다.
5. downstream 영향 경계
   - Stage4 예외 종료 시 audit buffer flush 이후 commit 실패 은닉
   - stage4 post-pass metadata, audit trail, sidecar 기록의 미영속화 가능성
   - `_safe_commit` 계약 변경 시 Stage2/3과 Stage4가 서로 다른 의미로 분기되는 회귀
6. 현재 테스트 근거 또는 테스트 부재
   - Stage4 관련 테스트는 cleanup 경로에서 `safe_commit.assert_called_once()`만 확인한다.
   - `safe_commit=MagicMock(return_value=False)`인 경우 로그/중단/재시도 정책을 검증하는 테스트는 없다.
   - 실행한 133개 테스트는 이 불일치를 전부 허용한 채 통과했다.
7. 기존 문서와의 중복 여부
   - `related-but-new-shared-helper-surface`
8. 권장 후속 조치
   - Stage4 cleanup도 Stage2/3과 동일하게 `False` 반환을 명시적으로 로그/감사 이벤트로 승격한다.
   - interrupt/exception 경로 테스트에 `safe_commit` 실패 케이스를 추가한다.
   - shared persistence helper 계약을 stage 공통 문서 또는 protocol로 고정한다.

## [MPN-T5-003] Stage2 smoke는 잘못된 `safe_commit_async` 더블을 들고 있고 현재 workspace에서는 둘 다 skip된다

1. ID
   - `[MPN-T5-003]`
2. Severity
   - `P2`
3. 현상 요약
   - Stage2 finalizer는 `safe_commit_async()`가 `True/False`를 반환하는 계약을 전제로 한다.
   - 그러나 두 개의 Stage2 smoke fixture는 `db.conn.commit()`만 호출하고 아무 값도 반환하지 않는 async 함수를 주입한다.
   - 동시에 두 smoke 모두 현재 workspace에서 fixture 부재로 skip되므로, 실제 commit-helper contract는 e2e에서 전혀 검증되지 않는다.
4. 코드 근거
   - `modules/core/stage2_finalizer.py:1091-1094`는 falsy 반환을 즉시 오류로 처리한다.
   - `tests/test_stage2_finalizer.py:33`은 unit layer에서 `AsyncMock(return_value=True)`로 올바른 bool contract를 가정한다.
   - `tests/e2e/test_l3_stage2_realproject.py:151-152`와 `tests/e2e/test_l3_golden_route.py:173-174`의 `_safe_commit_async()`는 `db.conn.commit()` 후 `return True`가 없다.
   - `tests/e2e/test_l3_stage2_realproject.py:17-24`는 실 DB 파일이 없으면 skip된다.
   - `tests/e2e/test_l3_golden_route.py:19-21`는 `*_tr_block_ALL.json`이 없으면 skip된다.
   - 이번 실행에서도 위 두 테스트는 각각 해당 사유로 실제 skip됐다.
5. downstream 영향 경계
   - Stage2 commit gate의 e2e 검증 공백
   - smoke fixture 자체가 prod contract와 어긋나 향후 fixture가 살아나면 오탐 FAIL 가능성
   - rollback/partial-commit 회귀가 unit 범위 밖에서는 잡히지 않는 상태
6. 현재 테스트 근거 또는 테스트 부재
   - unit test는 bool contract를 전제로 통과한다.
   - e2e smoke는 현재 환경에서 둘 다 skip이므로 contract mismatch를 검증하지도, 수정 유도도 못 한다.
7. 기존 문서와의 중복 여부
   - `none`
8. 권장 후속 조치
   - smoke fixture의 `_safe_commit_async()`는 `db.conn.commit(); return True`로 맞춘다.
   - 별도 negative smoke/unit로 `return False` 경로를 추가한다.
   - CI 또는 hermetic fixture에 real-project DB / treatment seed를 포함해 skip 의존을 줄인다.

## [MPN-T5-004] Stage3 DI slot coverage test가 MagicMock auto-attribute 때문에 실제 app surface drift를 놓칠 수 있다

1. ID
   - `[MPN-T5-004]`
2. Severity
   - `P3`
3. 현상 요약
   - `Stage3Context.from_app()` slot mapping 테스트는 `app = MagicMock()` 기반 fixture를 사용한다.
   - 이 fixture는 `adversarial_self_play`를 명시적으로 설정하지 않는데, 검증부에서는 `ctx.adversarial_self_play is app_mock.adversarial_self_play`를 단언한다.
   - `MagicMock`는 없는 속성을 자동 생성하므로, 실제 앱 surface에서 해당 속성이 누락되거나 이름이 바뀌어도 테스트가 쉽게 초록으로 남을 수 있다.
4. 코드 근거
   - `tests/test_stage3_orchestrator.py:18-20`의 fixture는 spec 없는 `MagicMock()`를 만든다.
   - `tests/test_stage3_orchestrator.py:48-70`은 여러 필드를 설정하지만 `adversarial_self_play`는 정의하지 않는다.
   - `tests/test_stage3_orchestrator.py:919`는 그 미정의 속성을 그대로 매핑 성공으로 단언한다.
   - `modules/core/stage3_context.py:95-115`의 `from_app()`는 `getattr(app, "adversarial_self_play", None)`로 읽기 때문에, spec 없는 double에서는 실제 누락을 감지할 수 없다.
   - `tests/test_stage3_orchestrator.py:971-979`의 None-guard 테스트는 callback absent 처리만 검증할 뿐 slot presence 검증의 auto-attr 문제를 막아 주지 않는다.
5. downstream 영향 경계
   - Stage3 `from_app()` slot drift
   - facade/app refactor 시 숨은 속성 누락
   - 테스트가 존재해도 runtime에서만 드러나는 DI wiring 회귀
6. 현재 테스트 근거 또는 테스트 부재
   - 현재 slot coverage 테스트는 존재하지만, 일부 속성은 auto-created mock라서 실질적 보장이 약하다.
   - spec 있는 fake/app protocol 기반의 slot coverage 테스트는 없다.
7. 기존 문서와의 중복 여부
   - `none`
8. 권장 후속 조치
   - `test_from_app_all_slots`는 `MagicMock(spec=[...])` 또는 명시적 fake app 객체로 바꾼다.
   - auto-created attribute에 의존하는 단언을 제거하고, 각 slot를 fixture에서 명시적으로 주입한 뒤 검증한다.
   - Stage2/Stage4의 `from_app` mapping test도 같은 패턴이 없는지 함께 정리한다.

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| Stage2 e2e commit semantics | open | skip 없는 hermetic smoke fixture와 `safe_commit_async=True/False` 두 경로가 필요 |
| Stage4 summary callback fallback | open | `Stage4ContextBuilder`와 `Stage4PostProcessor`에서 summary callback이 non-callable 또는 stale policy일 때의 consumer test가 필요하나, primary surface는 T4와 조율 필요 |
| `ProjectService` destructive op의 `_safe_commit` 소비 일관성 | open | direct `db.commit()` 경로와 legacy TF-6 patch 문서 사이 차이는 T1 primary surface와 재조율 필요 |

## 마감 체크

- 코드 근거 포함: yes
- downstream 영향 경계 포함: yes
- 현재 테스트 근거 또는 테스트 부재 포함: yes
- 기존 문서와의 중복 여부 포함: yes
