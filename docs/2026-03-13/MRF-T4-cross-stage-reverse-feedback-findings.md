# [MRF-T4] Cross-Stage Reverse Feedback Findings

> 작성일: 2026-03-13
> 상태: `executed / PASS3 completed`
> 조사 모드: `static / read-only / code-and-test verification / UTF-8 only`
> 기준 오더: `docs/2026-03-13/main_a-retry-feedback-detail-full-survey-audit-order.md`
> 최종 판정: `retained P1 1건, retained P2 2건, duplicate candidate 1건 제거`

이 문서는 `main_a.py`의 reverse feedback / structured feedback / enrich surface를 기준으로,
Stage 4 -> 3 -> 2 연결이 실제 코드에서 어떻게 소비되는지 조사한 결과다.
코드 직접 수정은 수행하지 않았다.

---

## 조사 범위

- `main_a.py`
  - `_enrich_director_result()`
  - `_generate_structured_arc_feedback()`
  - `_generate_reverse_feedback_stage4_to_3()`
  - `_generate_reverse_feedback_stage3_to_2()`
  - `_generate_reverse_feedback_stage4_to_2()`
- 직접 consumer
  - `modules/core/stage2_context.py`
  - `modules/core/stage2_preflight.py`
  - `modules/core/stage2_validation_pipeline.py`
- Stage 3 / Stage 4 연결 경계
  - `modules/core/stage3_context.py`
  - `modules/core/stage4_orchestrator.py`
  - `modules/core/stage4_interview_round.py`
  - `modules/core/pass_rate_monitor.py`
  - `modules/core/feedback_system.py`

## 필수 근거

- `docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md`
- `tests/test_feedback_system.py`
- `tests/test_stage2_context.py`
- `tests/test_stage2_validation_pipeline.py`
- `tests/test_stage2_preflight_helpers.py`
- `tests/test_stage3_orchestrator.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_arc_difficulty.py`

## 실행 확인

아래 테스트를 실제 실행했다.

- `pytest tests/test_feedback_system.py -q` -> `59 passed`
- `pytest tests/test_stage2_context.py -q` -> `16 passed`
- `pytest tests/test_stage2_validation_pipeline.py -q` -> `22 passed`
- `pytest tests/test_stage2_preflight_helpers.py -q` -> `44 passed`
- `pytest tests/test_stage3_orchestrator.py -q` -> `60 passed`

테스트는 모두 통과했지만, 아래 blind spot은 여전히 남아 있다.

---

## PASS 1 - 후보 수집

초기 후보는 4건이었다.

1. `Stage4->3` reverse feedback helper가 실제 pipeline에 연결되지 않았을 가능성
2. `Stage3->2` callback이 optional인데 실제 주입 지점에서 optional 계약이 일관되지 않을 가능성
3. `Stage4->2` feedback가 난이도 수치로만 압축되어 의미를 잃을 가능성
4. Stage 4 inner patch loop의 `action_items` 축약 문제가 이번 범위와 중복될 가능성

## PASS 2 - 교차 검증

PASS 2에서 아래 1건은 제거했다.

- `duplicate candidate`
  - 내용: Stage 4 inner patch loop의 second-pass feedback 축약
  - 판정: `already-covered-do-not-reopen`
  - 근거: `docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md`가 이미 동일 책임 경계를 retained finding으로 보유

나머지 3건은 `main_a.py callback surface` 책임 경계에서 신규 finding으로 유지 가능하다고 판단했다.

---

## PASS 3 - 확정 Findings

### [MRF-T4-001]

1. ID
   - `[MRF-T4-001]`
2. Severity
   - `P1`
3. 현상 요약
   - `main_a.py`와 `feedback_system.py`에는 `Stage4->3` reverse feedback helper가 존재하고 unit test도 있다.
   - 그러나 실제 Stage 3 consumer 경계에는 이 callback이 주입되지 않는다.
   - live Stage 4 -> 3 번역은 `_generate_reverse_feedback_stage4_to_3()`가 아니라 `Stage4Orchestrator` 내부의 별도 advisory 로직으로 우회된다.
   - 결과적으로 Stage 4 reject reason이 helper가 의도한 의미 체계와 다른 규칙으로 Stage 3에 번역된다.
4. 코드 근거
   - `main_a.py:738-742`는 `_generate_reverse_feedback_stage4_to_3()` wrapper를 노출한다.
   - `modules/core/feedback_system.py:576-624`는 `writer_reject_reason`과 `pre_checklist_result`를 받아 후반 밀도, 분량, 설정 모순, 대화/지문 문제를 Blueprint 지침으로 바꾸는 구현을 가진다.
   - `modules/core/stage3_context.py:10-13`, `modules/core/stage3_context.py:16-42`, `modules/core/stage3_context.py:95-119`에는 해당 callback slot이나 `from_app` 주입이 없다.
   - 반대로 실제 Stage 4 -> 3 escalation은 `modules/core/stage4_orchestrator.py:1033-1149`에서 `error_category`, `reject_bucket`, `contradiction_types` 기반 advisory로 수행된다.
   - repo 전역 검색 기준 `generate_reverse_feedback_stage4_to_3`의 실사용은 정의와 `tests/test_feedback_system.py`뿐이다.
5. downstream 영향 경계
   - Stage 4 reject reason이 `후반 밀도 부족`, `분량 부족`, `설정 모순`처럼 helper가 직접 다루는 케이스여도,
     Stage 3은 그 helper의 정규화된 지침을 받지 못한다.
   - 현재 Stage 3은 `logic_error streak`, `reject_bucket`, `contradiction type` 같은 별도 휴리스틱에 의존하므로,
     동일 실패 원인이 다른 의미로 번역되거나 아예 번역되지 않을 수 있다.
   - 영향 범위는 `Stage4 manuscript reject -> Stage3 blueprint correction` 경계다.
6. 현재 테스트 근거 또는 테스트 부재
   - 존재하는 테스트:
     - `tests/test_feedback_system.py:408-427`은 helper 문자열 생성만 검증한다.
     - `tests/test_stage3_orchestrator.py:909-936`은 `Stage3Context` slot 집합을 검증하지만 해당 callback 자체가 없다.
   - 부재:
     - `Stage4 reject -> Stage3 reverse feedback injection` 통합 테스트가 없다.
7. 기존 문서와의 중복 여부
   - `related-but-new-callback-surface`
   - 기존 Stage 4 감리는 `Director-CW` inner loop를 다뤘고, 이번 항목은 `main_a.py helper surface가 실제 Stage 3 경계에 닿지 않는다`는 별도 계약 문제다.
8. 권장 후속 조치
   - 선택지는 둘 중 하나다.
   - `Stage3Context/Stage3Orchestrator`에 `Stage4->3` callback 경로를 실제로 연결한다.
   - 또는 helper와 unit test를 정리하고, 현재의 advisory 기반 경로를 SSOT로 재문서화한다.
   - 어느 쪽이든 `Stage4 reject reason + pre_checklist_result -> Stage3 correction prompt` 통합 테스트가 필요하다.

### [MRF-T4-002]

1. ID
   - `[MRF-T4-002]`
2. Severity
   - `P2`
3. 현상 요약
   - `Stage3->2` reverse feedback callback은 `Stage2Context`에서 optional이다.
   - 하지만 실제 주입 지점은 `callable` 가드 없이 바로 호출한다.
   - callback이 비어 있으면 broad `except`로 흡수되어 feedback injection이 사라지고 audit event만 남는다.
   - 같은 reverse feedback family 안에서 `Stage4->2`는 explicit guard가 있고 `Stage3->2`는 없어서 optional field 기대치가 서로 다르다.
4. 코드 근거
   - `modules/core/stage2_context.py:142-144`, `modules/core/stage2_context.py:193-195`, `modules/core/stage2_context.py:246-248`은 `generate_reverse_feedback_stage3_to_2`를 optional / `None` 허용으로 다룬다.
   - `modules/core/stage2_preflight.py:895-916`은 stage3 실패 3회 이상이면 `self.ctx.generate_reverse_feedback_stage3_to_2(...)`를 직접 호출한다.
   - `modules/core/stage2_preflight.py:916-920`은 예외를 `v60_9_stage3to2_error` audit event로만 남기고 계속 진행한다.
   - 대조적으로 `modules/core/stage2_preflight.py:924-929`의 `Stage4->2` 경로는 callback 존재 여부를 먼저 확인한다.
5. downstream 영향 경계
   - app/context drift로 callback 주입이 빠진 상태에서 Stage 3 실패가 3회 누적되면,
     Stage 2는 원래 받아야 할 Blueprint 실패 패턴 분석을 받지 못한 채 같은 Arc를 재시도한다.
   - 즉시 crash는 막지만, reverse feedback chain은 조용히 비활성화된다.
   - 영향 범위는 `Stage3 blueprint 반복 실패 -> Stage2 arc 재검토` 경계다.
6. 현재 테스트 근거 또는 테스트 부재
   - 존재하는 테스트:
     - `tests/test_stage2_context.py:108-115`는 callback 기본값이 `None`임을 확인한다.
     - `tests/test_feedback_system.py:435-456`은 helper 함수 단독 동작만 검증한다.
     - `tests/test_stage2_preflight.py:65`는 fixture에서 callback을 강제로 채워 둔다.
   - 부재:
     - callback이 `None`이고 stage3 실패가 3회 누적된 실제 branch test가 없다.
     - 정상 주입 branch에서 enhanced context에 어떤 문구가 붙는지도 검증하지 않는다.
7. 기존 문서와의 중복 여부
   - `related-but-new-callback-surface`
8. 권장 후속 조치
   - `Stage3->2`도 `Stage4->2`와 같은 방식으로 `callable` guard를 추가한다.
   - callback 부재 시 `audit-only`로 끝내지 말고, 최소한 deterministic fallback 문구 또는 explicit warning injection을 넣는다.
   - `callback 없음 + stage3 실패 3회` 회귀 테스트와 `callback 있음 + 실제 주입 문자열` 테스트를 분리해 추가한다.

### [MRF-T4-003]

1. ID
   - `[MRF-T4-003]`
2. Severity
   - `P2`
3. 현상 요약
   - active `Stage4->2` reverse feedback chain은 Stage 4 reject semantics를 거의 보존하지 못한다.
   - 실제 입력은 `PassRateMonitor.get_arc_difficulty()`가 만든 `difficulty / avg_attempts / hard_episodes` 요약뿐이다.
   - helper는 이 요약을 받아 "씬 구조 단순화", "다중 NPC 최소화", "비선형 시간 전개 최소화" 같은 generic guidance만 만든다.
   - 반면 `main_a.py`의 `_enrich_director_result()`는 `score_breakdown`, `quantified_feedback`, `responsibility_guide`를 만들 수 있게 설계돼 있지만, 현재 live chain에서는 호출되지 않는다.
4. 코드 근거
   - `main_a.py:418-555`는 `breakdown_feedback`, `quantified_feedback`, `responsibility`, `responsibility_guide`를 추가하는 enrich helper를 가진다.
   - repo 전역 검색 기준 `_enrich_director_result()` 호출 지점은 확인되지 않았다.
   - `modules/core/stage4_interview_round.py:4472-4490`은 Stage 4 시도 기록을 `pass_rate_monitor`에 저장하지만, reverse feedback으로 재사용되는 값은 결국 난이도 추정에 필요한 attempt count다.
   - `modules/core/pass_rate_monitor.py:478-533`의 `get_arc_difficulty()`는 Stage 4 기록 중 `stage`, `arc`, `episode`, 시도 횟수만 사용해 `difficulty / avg_attempts / hard_episodes`를 계산한다.
   - `modules/core/stage2_preflight.py:922-944`는 그 난이도 dict만 `generate_reverse_feedback_stage4_to_2()`에 넘긴다.
   - `modules/core/feedback_system.py:667-682`의 helper는 `difficulty == hard`일 때만 generic simplification advice를 반환한다.
5. downstream 영향 경계
   - Stage 4에서 실제 문제 원인이 `분량`, `설정`, `수치`, `문체`, `논리` 중 무엇이었는지와 무관하게,
     Stage 2는 이전 Arc가 "집필 난이도가 높았다"는 정보만 받고 다음 Arc를 단순화하는 방향으로 유도된다.
   - 즉 `same failure cause`가 아니라 `same retry cost`가 전달되는 구조라, 의미 보존이 약하다.
   - 영향 범위는 `Stage4 manuscript reject history -> Stage2 next-arc design guidance` 경계다.
6. 현재 테스트 근거 또는 테스트 부재
   - 존재하는 테스트:
     - `tests/test_stage4_interview_round.py:880-909`은 Stage 4 reject가 `reject_reason` 문자열로 기록됨을 확인한다.
     - `tests/test_arc_difficulty.py:33-48`은 hard 판정이 시도 횟수 평균에서만 결정됨을 확인한다.
     - `tests/test_stage2_preflight_helpers.py:1011-1045`는 Stage4->2 주입 여부와 audit event만 검증한다.
   - 부재:
     - `error_category`, `score_breakdown`, `action_items`, `open_review`가 Stage4->2 feedback로 보존되는지 검증하는 테스트가 없다.
     - `_enrich_director_result()` 산출물이 live reverse chain에 연결되는지 검증하는 테스트도 없다.
7. 기존 문서와의 중복 여부
   - `related-but-new-callback-surface`
8. 권장 후속 조치
   - `PassRateMonitor` 기반 난이도 요약과 별도로, Stage 4의 `error_category`, `reject_bucket`, `score_breakdown` 요약을 다음 Arc feedback payload에 함께 실어야 한다.
   - `_enrich_director_result()`를 실제 Stage 4 결과 경로에 연결할지, 아니면 dead helper로 정리할지 결정이 필요하다.
   - `Stage4 record_attempt -> Stage2 injected reverse feedback` 통합 테스트에서 semantic field 보존을 확인해야 한다.

---

## Rejected / Removed Candidates

### RC-1. Stage 4 inner patch loop의 second-pass feedback 축약

- 판정: `already-covered-do-not-reopen`
- 이유:
  - `docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md`가 이미 retained finding으로 확정
  - 이번 T4 문서는 `main_a.py callback surface`와 `cross-stage reverse translation` 책임 경계만 유지

---

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| `Stage4->3` live injection | helper unit test만 존재 | Stage 3 consumer integration test |
| `Stage3->2` missing callback branch | 미검증 | `callback=None + failure>=3` 회귀 테스트 |
| `Stage4->2` semantic preservation | hard/normal gating만 검증 | `error_category/score_breakdown` 보존 테스트 |
| `_enrich_director_result` live wiring | 정의만 확인, call site 없음 | Stage 4 result assembly 경로 명시 또는 dead-code 정리 |

---

## PASS 요약

- PASS1 후보: `4`
- PASS2 제거: `1`
- PASS3 확정: `3`

정리하면, 이번 범위의 핵심 문제는 `helper가 없다`가 아니라 `helper가 서로 다른 방식으로만 부분 연결돼 있다`는 점이다.

- `Stage4->3`는 사실상 live consumer가 없다.
- `Stage3->2`는 optional 계약이 일관되지 않다.
- `Stage4->2`는 연결은 돼 있지만 의미가 지나치게 압축된다.

즉 현재 cross-stage feedback chain은 "존재 여부" 기준으론 일부 살아 있지만,
"같은 실패 원인을 같은 의미로 번역하는가" 기준으론 아직 SSOT로 잠기지 않았다.

## 마감 체크

- 코드 근거 포함
- downstream 영향 경계 포함
- 현재 테스트 근거 또는 테스트 부재 포함
- 기존 문서와의 중복 여부 포함
- `PASS1 -> PASS2 -> PASS3` 요약 포함
