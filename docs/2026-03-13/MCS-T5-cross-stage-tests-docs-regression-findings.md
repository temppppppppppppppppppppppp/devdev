# [MCS-T5] Cross-Stage Tests / Docs / Regression Findings

> 작성일: 2026-03-13
> 상태: `executed / PASS3 completed`
> 조사 모드: `static / read-only / code-and-test verification / source-report cross-check / UTF-8 only`
> 기준 오더: `docs/2026-03-13/main_a-cross-stage-semantic-preservation-detail-full-survey-audit-order.md`
> 최종 판정: `retained P2 3건, retained P3 1건, PASS2 제거 2건`

코드 수정은 수행하지 않았다. 이번 문서는 `Terminal 5 - Tests / Docs / Regression Surface` 범위에서
현재 테스트와 기존 감리 문서가 cross-stage semantic preservation을 얼마나 신뢰성 있게 증명하는지만 다룬다.

---

## 조사 범위

- 기존 감리 문서
  - `docs/2026-03-13/MRF-T4-cross-stage-reverse-feedback-findings.md`
  - `docs/2026-03-13/MPN-T4-stage4-summary-cache-findings.md`
  - `docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md`
- cross-stage 관련 코드
  - `main_a.py`
  - `modules/core/stage2_context.py`
  - `modules/core/stage2_preflight.py`
  - `modules/core/stage3_context.py`
  - `modules/core/stage4_context.py`
  - `modules/core/stage4_context_builder.py`
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage4_post_processor.py`
- 관련 테스트
  - `tests/test_feedback_system.py`
  - `tests/test_stage2_preflight.py`
  - `tests/test_stage2_preflight_helpers.py`
  - `tests/test_stage3_orchestrator.py`
  - `tests/test_stage4_context.py`
  - `tests/test_stage4_context_builder.py`
  - `tests/test_stage4_interview_round.py`
  - `tests/test_stage4_post_processor.py`
  - `tests/test_pass_with_fix.py`
  - `tests/test_director_feedback_loop.py`
  - `tests/test_a2_open_review_cw.py`
  - `tests/test_sweep23.py`

## 실행 로그

- `pytest tests/test_feedback_system.py tests/test_stage2_preflight.py tests/test_stage2_preflight_helpers.py tests/test_stage3_orchestrator.py tests/test_stage4_context.py tests/test_stage4_context_builder.py tests/test_sweep23.py -q`
  - 결과: `271 passed in 8.08s`
- `pytest tests/test_pass_with_fix.py -q`
  - 결과: `82 passed in 67.66s`
- `pytest tests/test_stage4_post_processor.py tests/test_director_feedback_loop.py tests/test_a2_open_review_cw.py -q`
  - 결과: `47 passed in 3.02s`
- `pytest tests/test_stage4_interview_round.py -q`
  - 결과: `1 failed, 68 passed in 65.17s`
  - 실패 테스트: `tests/test_stage4_interview_round.py::TestModuleStructure::test_main_a_stage4_context_includes_pass_rate_monitor`

## Executive Summary

- 확정 findings: `4`
- 핵심 결론:
  - 현재 회귀망은 helper 단위와 callback wiring 단위에는 일부 강하지만, `semantic payload가 실제 consumer까지 같은 의미로 살아남는지`를 직접 잠그는 테스트는 여전히 부족하다.
  - 특히 Stage 4 structured payload와 summary/context 보존은 live chain보다 mock/stub에 더 많이 의존한다.
  - 테스트 일부는 production semantics 대신 source string 또는 테스트 내부 재구현 로직에 기대고 있어 false green과 false red를 함께 만든다.
  - 관련 감리 문서 중 1건은 현재 테스트 상태와 이미 어긋난 서술을 포함한다.

## PASS 기록

- PASS 1: 후보 6건 수집
  - Stage 4 semantic-rich payload regression gap
  - Stage 4 summary/context live-chain mock skew
  - shadow/source-string proof quality 문제
  - existing audit doc stale claim 후보
  - Stage 2 callback pinning narrow surface
  - narrative summary direct-commit/open-question 재확정 후보
- PASS 2: 후보 2건 제거
  - `Stage2 callback pinning narrow surface`
    - 판정: `already-covered-do-not-reopen`
    - 근거: `docs/2026-03-13/MRF-T5-consumer-tests-regression-findings.md`의 `MRF-T5-001`, `MRF-T5-002`, `MRF-T5-003`가 동일 책임 경계를 이미 확정했다.
  - `narrative summary direct-commit/open-question`
    - 판정: `already-covered-do-not-reopen`
    - 근거: `docs/2026-03-13/MPN-T4-stage4-summary-cache-findings.md`가 summary persistence와 loader drift를 primary surface로 이미 보유한다.
- PASS 3: `MCS-T5-001` ~ `MCS-T5-004` 4건 확정

---

## Pass 3 - Final Findings

### [MCS-T5-001]

1. ID
   - `MCS-T5-001`
2. Severity
   - `P2`
3. 현상 요약
   - cross-stage semantic preservation의 핵심 후보였던 Stage 4 structured payload surface가 현재 회귀 테스트에 거의 잠기지 않았다.
   - `main_a.py`는 `_enrich_director_result()`에서 `breakdown_feedback`, `responsibility_guide`, `quantified_feedback` 같은 semantic-rich 필드를 만들 수 있게 설계돼 있다.
   - 그러나 현재 테스트는 pure helper 결과나 reject reason 일부만 보고, 이 structured payload가 실제 stage handoff에서 유지되는지는 검증하지 않는다.
4. 코드 근거
   - `main_a.py:432-569`는 `_enrich_director_result()`, `_analyze_score_breakdown()`, `_quantify_reject_feedback()`를 통해 `action_items`, `breakdown_feedback`, `responsibility`, `responsibility_guide`, `quantified_feedback`를 조립한다.
   - 반면 `tests/` 전역 검색 기준 `_enrich_director_result`, `_analyze_score_breakdown`, `_quantify_reject_feedback`, `responsibility_guide`, `quantified_feedback`에 대한 직접 테스트 참조는 없다.
   - 현재 존재하는 근접 테스트는 pure helper 레벨이다.
     - `tests/test_feedback_system.py:170-203`
     - `tests/test_feedback_system.py:363-477`
   - consumer 쪽 검증도 semantic-rich payload 전체가 아니라 일부 필드에 국한된다.
     - `tests/test_stage2_preflight_helpers.py:1011-1045`는 Stage4->2 injection 존재와 hard/normal difficulty만 본다.
     - `tests/test_stage4_interview_round.py:1586-1621`, `tests/test_stage4_interview_round.py:2291-2330`은 `selection_reason`, `verdict_reason`, `open_review`, `score_breakdown` 일부 persistence만 본다.
5. downstream 영향 경계
   - `Stage4 -> Stage3`, `Stage4 -> Stage2` semantic contract 전반이 영향권이다.
   - 특히 `error_category`, `score_breakdown`, `action_items`, `responsibility_guide`, `quantified_feedback`처럼 원래 압축되기 쉬운 필드가 빠지거나 의미가 바뀌어도, 현재 회귀망은 helper PASS만으로 녹색이 될 수 있다.
6. 현재 테스트 근거 또는 테스트 부재
   - 있음: pure helper semantics와 일부 persistence smoke.
   - 부재: `main_a structured payload -> consumer-visible prompt/retry context`를 한 번에 검증하는 live consumer test.
7. 기존 문서와의 중복 여부
   - `related-but-new-cross-stage-semantic-surface`
   - 이유: `MRF-T4`는 live chain의 dead/weak wiring을 다뤘고, 본 finding은 그 semantic-rich payload를 잠그는 regression net 자체의 부재를 다룬다.
8. 권장 후속 조치
   - 최소 1개는 실제 `main_a.py` wrapper를 거쳐 `Stage2Preflight` 또는 `Stage4InterviewRound` consumer까지 가는 통합 테스트가 필요하다.
   - assertion은 문자열 존재가 아니라 `semantic field -> consumer-visible meaning` 기준으로 잡아야 한다.

### [MCS-T5-002]

1. ID
   - `MCS-T5-002`
2. Severity
   - `P2`
3. 현상 요약
   - Stage 4 summary/context semantic preservation은 현재 live chain보다 mock/stub에 더 많이 의존한다.
   - 그래서 stale summary, `ep_range` 오표기, summary 중복 주입처럼 이미 문서화된 blind spot을 막는 직접 회귀 테스트가 없다.
4. 코드 근거
   - `tests/test_stage4_context_builder.py:32`는 `ctx.load_narrative_summaries = MagicMock(return_value="")`로 loader를 기본적으로 비운다.
   - `tests/test_stage4_post_processor.py:93`, `tests/test_stage4_post_processor.py:616`, `tests/test_stage4_post_processor.py:807`, `tests/test_stage4_post_processor.py:857`, `tests/test_stage4_post_processor.py:917`는 `generate_narrative_summary = MagicMock()`만 주입한다.
   - `tests/test_stage4_context.py:162-179`는 callback wiring만 확인한다.
   - `tests/test_sweep23.py:19-27`은 `_generate_narrative_summary()`의 `None` manuscript crash 방지만 본다.
   - 기존 문서도 같은 공백을 이미 지적한다.
     - `docs/2026-03-13/MPN-T4-stage4-summary-cache-findings.md:84-87`
     - `docs/2026-03-13/MPN-T4-stage4-summary-cache-findings.md:155-158`
5. downstream 영향 경계
   - `narrative_summary`, `series_summary`, `volume_summary`, `focused/minimal context`가 Stage 4 builder에 어떻게 합쳐지는지 직접 영향받는다.
   - stale future summary, sparse `ep_range`, duplicated summary budget loss가 재발해도 현재 테스트는 callback 호출 또는 빈 mock 반환만 보고 지나갈 수 있다.
6. 현재 테스트 근거 또는 테스트 부재
   - 있음: callback 배선, crash 방지, builder 일부 budget logic.
   - 부재: 실제 loader/generator 산출물이 mandatory context에 어떤 의미로 들어가는지, destructive op 이후 어떻게 필터되는지 보는 live regression test.
7. 기존 문서와의 중복 여부
   - `related-but-new-cross-stage-semantic-surface`
   - 이유: `MPN-T4`는 code bug/contract drift를 확정했고, 본 finding은 그 문제를 막아 줄 regression surface가 아직 없다는 점을 별도로 잠근다.
8. 권장 후속 조치
   - mock 빈 문자열 대신 실제 `_load_narrative_summaries()` 산출 예시를 사용하는 Stage4ContextBuilder test가 필요하다.
   - rollback/reset 이후 summary loader filtering과 `ep_range` 라벨 정확성을 별도 회귀 테스트로 추가해야 한다.

### [MCS-T5-003]

1. ID
   - `MCS-T5-003`
2. Severity
   - `P2`
3. 현상 요약
   - cross-stage regression proof 일부가 live consumer semantics가 아니라 shadow implementation 또는 brittle source-string assertion에 의존한다.
   - 이 패턴은 false green과 false red를 동시에 만든다.
   - 실제로 현재 `tests/test_stage4_interview_round.py`에는 semantic contract가 살아 있는데도 refactor된 배선 방식을 따라가지 못해 실패하는 source-string test가 존재한다.
4. 코드 근거
   - `tests/test_director_feedback_loop.py:4-32`는 production 코드를 import하지 않고 `_build_evidence_block()`, `_apply_evidence_to_feedback()`를 테스트 파일 안에서 다시 구현한다.
   - 실제 runtime 로직은 `modules/core/stage4_interview_round.py:318-332`에 있으며, `_compact_text()` 사용과 summary 조립 방식이 test shadow code와 완전히 동일하다고 보장되지 않는다.
   - `tests/test_stage4_interview_round.py:2391-2393`는 `main_a.py` source string에 `pass_rate_monitor=getattr(self, "pass_rate_monitor", None),`가 직접 남아 있어야 한다고 단언한다.
   - 현재 runtime 배선은 이미 `main_a.py:3497-3499`의 `Stage4Context.from_app(self)`로 이동했고, 실제 slot 매핑은 `modules/core/stage4_context.py:168`에서 유지된다.
   - 실실행 결과도 이 brittleness를 증명한다.
     - `pytest tests/test_stage4_interview_round.py -q` -> `1 failed, 68 passed`
5. downstream 영향 경계
   - false green:
     - production evidence block semantics가 변해도 shadow test가 같이 낡은 규칙을 유지하면 회귀를 놓칠 수 있다.
   - false red:
     - semantic contract는 유지되는데 구현 위치만 바뀌어도 source-string assertion 때문에 suite가 붉게 변할 수 있다.
   - 둘 다 통합 감리의 proof quality를 떨어뜨린다.
6. 현재 테스트 근거 또는 테스트 부재
   - 있음: 위 failing test와 shadow test 자체가 현재 패턴의 직접 증거다.
   - 부재: 해당 surface를 production callable 또는 consumer-visible output으로 직접 잠그는 테스트.
7. 기존 문서와의 중복 여부
   - `none`
8. 권장 후속 조치
   - source-string assertion은 제거하고 `Stage4Context.from_app(app).pass_rate_monitor is app.pass_rate_monitor` 같은 semantic assertion으로 바꾼다.
   - `tests/test_director_feedback_loop.py`는 local copy를 유지하지 말고 `Stage4InterviewRound`의 실제 callable을 통해 검증하도록 바꾼다.

### [MCS-T5-004]

1. ID
   - `MCS-T5-004`
2. Severity
   - `P3`
3. 현상 요약
   - 관련 기존 감리 문서 중 하나가 현재 테스트 surface와 이미 어긋난다.
   - `stage4-director-cw-feedback-loop-full-survey-3pass-audit.md`는 multi-pass PASS_WITH_FIX 테스트가 second-pass에서 `fix_scope_reasoning/open_review`를 검증하지 않는다고 적지만, 현재 test file에는 그 케이스를 직접 보는 테스트가 존재하고 실제 실행도 통과한다.
4. 코드 근거
   - 문서 주장:
     - `docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md:187-188`
     - `docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md:249`
   - 현재 테스트:
     - `tests/test_pass_with_fix.py:2122-2161`의 `test_pf3_pass_with_fix_reaudit_preserves_reasoning_and_open_review`
   - 실행 결과:
     - `pytest tests/test_pass_with_fix.py -q` -> `82 passed`
5. downstream 영향 경계
   - 통합 감리에서 proof gap 크기를 과장하거나, 이미 메워진 test coverage를 놓친 채 finding을 재오픈할 위험이 있다.
   - duplicate 판정과 confidence ledger가 현재 상태보다 더 비관적으로 기록될 수 있다.
6. 현재 테스트 근거 또는 테스트 부재
   - 있음: `tests/test_pass_with_fix.py`의 direct assertion과 실제 green run.
   - 문제는 테스트 부재가 아니라 기존 문서의 stale claim이다.
7. 기존 문서와의 중복 여부
   - `none`
8. 권장 후속 조치
   - 통합본 작성 시 위 문서의 해당 문구는 stale note로 정정하고, blind spot ledger에는 남기지 않는 것이 맞다.
   - 향후 감리 문서는 "실행 당시 본 테스트/라인"과 "후속 추가된 테스트"를 구분해 기록해야 한다.

---

## Rejected / Removed Candidates

### RC-1. Stage2 callback export 면적 대비 pinning 부족

- 판정: `already-covered-do-not-reopen`
- 이유:
  - `docs/2026-03-13/MRF-T5-consumer-tests-regression-findings.md`가 이미
    - `MRF-T5-001`
    - `MRF-T5-002`
    - `MRF-T5-003`
    로 동일 책임 경계를 유지한다.

### RC-2. narrative summary direct-commit/open question 재확정

- 판정: `already-covered-do-not-reopen`
- 이유:
  - `docs/2026-03-13/MPN-T4-stage4-summary-cache-findings.md`의 coverage gap과 retained findings가 이미 이 표면을 primary로 관리한다.

---

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| `semantic-loss / semantic-rewrite / semantic-bypass` 분류 | manual-only | 현재 T1~T4 관련 문서들은 duplicate status는 있으나 각 finding에 위 3분류 태그를 직접 달지 않는다. 통합본에서 수동 재분류가 필요하다. |
| Stage4 structured payload live handoff | 미검증 | `main_a._enrich_director_result()` 산출물이 실제 Stage3/2 consumer prompt에 어떤 의미로 들어가는지 보는 통합 테스트 |
| Stage4 summary/context live chain | 미검증 | 실제 `_load_narrative_summaries()`와 `_generate_narrative_summary()`를 켠 상태의 builder/post-processor regression test |
| proof-quality hygiene | 부분 실패 | `tests/test_stage4_interview_round.py::test_main_a_stage4_context_includes_pass_rate_monitor` 같은 source-string assertion을 semantic assertion으로 교체해야 함 |

## Finding Ledger

| ID | Sev | 상태 | 파일/함수 | 요약 |
|----|-----|------|-----------|------|
| `MCS-T5-001` | `P2` | retained | `main_a.py::_enrich_director_result`, related tests | Stage4 semantic-rich payload surface를 잠그는 regression net이 없다 |
| `MCS-T5-002` | `P2` | retained | `tests/test_stage4_context_builder.py`, `tests/test_stage4_post_processor.py` | Stage4 summary/context live chain이 mock/stub에 과의존한다 |
| `MCS-T5-003` | `P2` | retained | `tests/test_director_feedback_loop.py`, `tests/test_stage4_interview_round.py` | shadow/source-string proof가 false green과 false red를 함께 만든다 |
| `MCS-T5-004` | `P3` | retained | `stage4-director-cw-feedback-loop-full-survey-3pass-audit.md` | 기존 감리 문서 1건이 현재 테스트 상태와 어긋난 stale claim을 가진다 |

## PASS 요약

- PASS1 후보 `6건`
- PASS2 제거 `2건`
- PASS3 확정 `4건`

## 마감 체크

- 코드 근거 포함: `yes`
- downstream 영향 경계 포함: `yes`
- 현재 테스트 근거 또는 테스트 부재 포함: `yes`
- 기존 문서와의 중복 여부 포함: `yes`
- `PASS1 -> PASS2 -> PASS3` 요약 포함: `yes`
- 코드 직접 수정 금지 준수: `yes`
