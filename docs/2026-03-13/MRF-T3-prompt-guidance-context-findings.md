# [MRF-T3] Prompt Guidance / Context Findings

> 작성일: 2026-03-13
> 상태: `executed / PASS3 finalized`
> 조사 모드: `static / read-only / code-and-test verification / UTF-8 only`
> 기준 오더: `main_a-retry-feedback-detail-full-survey-audit-order.md`
> 실행 검증: `pytest -q tests/test_prompt_builder.py tests/test_feedback_system.py tests/test_stage2_context.py tests/test_stage2_preflight.py tests/test_stage2_preflight_helpers.py tests/test_stage2_validation_pipeline.py tests/test_arc_retry.py tests/test_stage2_finalizer.py` = `233 passed`, `pytest -q tests/test_stage4_context_builder.py` = `45 passed`

이 문서는 `main_a.py`의 retry / guidance / context helper 표면과 `prompt_builder`, Stage 2 consumer 배선을 교차 조사한 PASS3 결과다. 코드 직접 수정은 수행하지 않았다.

---

## 조사 범위

- `main_a.py`
  - `_simplify_prompt_for_retry()`
  - `_build_strong_kind_feedback()`
  - `_build_focused_context()`
  - `_build_minimal_arc_context()`
  - `_generate_arc_position_guide()`
  - `_get_dynamic_critical_keywords()`
  - `_generate_writer_guidance_v60_8()`
  - `_generate_arc_context_v60()`
- 구현체
  - `modules/core/feedback_system.py`
  - `modules/core/prompt_builder.py`
- 직접 consumer / 교차 검증 보강
  - `modules/core/stage2_context.py`
  - `modules/core/stage2_preflight.py`
  - `modules/core/stage2_validation_pipeline.py`
  - `modules/core/stage2_orchestrator.py`
  - `modules/core/stage2_finalizer.py`
  - `modules/core/stage4_context_builder.py`
  - `modules/core/stage4_orchestrator.py`

## 필수 근거

- `tests/test_prompt_builder.py`
- `tests/test_feedback_system.py`
- `tests/test_stage2_context.py`
- `tests/test_stage2_preflight.py`
- `tests/test_stage2_preflight_helpers.py`
- `tests/test_stage2_validation_pipeline.py`
- `tests/test_arc_retry.py`
- `tests/test_stage2_finalizer.py`
- 추가 교차 근거
  - `tests/test_stage4_context_builder.py`
  - `docs/2026-03-03/TF-49-arc-state-reconciliation-spec.md`
  - `docs/2026-02-27/context_quality_audit.md`

## PASS 기록

### PASS 1 - 초벌 스캔

- `main_a.py` thin delegate 8개와 `feedback_system.py`, `prompt_builder.py` 본문을 대조했다.
- Stage 2 retry / validation / batch enrich consumer와 Stage 4 writer prompt 조립 경로를 따라 실제 사용 여부를 확인했다.
- 후보 4건을 뽑았다.
  - 후보 A: writer guidance / retry helper 다수가 export만 되고 live consumer가 없다
  - 후보 B: `generate_arc_context_v60(..., current_arc_no=...)` 시그니처가 target arc 번호를 받지만 실제로는 쓰지 않는다
  - 후보 C: retry 전용 `build_minimal_arc_context()`의 에너지 계산이 full arc context와 다르게 누적 손실을 버린다
  - 후보 D: `build_focused_context()`가 `violations` 인자를 전혀 사용하지 않는다

### PASS 2 - 교차 검증

- 후보 D는 PASS3 finding에서 제거했다.
  - 이름상 drift 가능성은 있으나 현재 validation path는 `strong_kind_feedback`와 `structured_feedback`가 이미 위반 유형을 전달하고 있어, `focused_context`의 역할을 "직전 상태 압축"으로 해석하는 반론이 가능했다.
  - 다만 관련 semantic test 부재는 coverage gap으로 유지했다.
- 후보 A/B/C는 retained finding으로 유지했다.
  - 후보 A는 `prompt_builder.py`와 `main_a.py` export, `stage4_context_builder.py` / `stage4_orchestrator.py` 실제 writer path, `tests/test_prompt_builder.py` / `tests/test_stage4_context_builder.py`를 교차 대조해 배선 누락이 현재 코드 기준 사실로 고정됐다.
  - 후보 B는 Stage 2가 실제로 `current_arc_no`를 넘기는 반면 구현 본문에서는 인자가 완전히 미사용인 점을 확인했다.
  - 후보 C는 실제 구현체를 그대로 불러 2-arc 샘플로 비교했을 때 `build_minimal_arc_context()`는 `70%`, `generate_arc_context_v60()` fallback은 `50%`를 내는 재현값을 확인했다.
- 기존 문서 중복 여부를 대조했다.
  - `TF-49-arc-state-reconciliation-spec.md`와 `context_quality_audit.md`는 `generate_arc_context_v60()` 보강 필요성을 다루지만, 이번 finding처럼 `main_a.py` callback contract와 retry-helper drift를 직접 채택하지는 않았다.

### PASS 3 - 최종 확정

- PASS1 후보 `4건`
- PASS2 제거 `1건`
- 최종 확정 `3건`

## Finding Ledger

| ID | Sev | 상태 | 파일/함수 | 요약 | duplicate status |
|----|-----|------|-----------|------|------------------|
| `MRF-T3-01` | `P1` | confirmed | `main_a.py`, `modules/core/prompt_builder.py`, `modules/core/stage4_context_builder.py`, `modules/core/stage4_orchestrator.py` | retry / writer guidance helper 다수가 export만 되고 실제 writer prompt 경로에는 전혀 주입되지 않는다 | `none` |
| `MRF-T3-02` | `P2` | confirmed | `main_a.py`, `modules/core/prompt_builder.py`, `modules/core/stage2_orchestrator.py`, `modules/core/stage2_finalizer.py` | `generate_arc_context_v60()`는 `current_arc_no`를 시그니처로 받지만 구현 본문은 인자를 완전히 무시한다 | `related-but-new-callback-surface` |
| `MRF-T3-03` | `P1` | confirmed | `modules/core/feedback_system.py`, `modules/core/prompt_builder.py`, `modules/core/stage2_preflight.py` | retry focus mode가 쓰는 `build_minimal_arc_context()`가 누적 내공 소모를 버려 full arc context와 다른 시작 상태를 주입할 수 있다 | `related-but-new-callback-surface` |

## Findings

### [MRF-T3-01] P1 | retry / writer guidance helper 다수가 export만 되고 실제 writer prompt 경로에서는 죽어 있다

- ID
  - `MRF-T3-01`
- Severity
  - `P1`
- 현상 요약
  - `main_a.py`는 `_simplify_prompt_for_retry()`, `_generate_arc_position_guide()`, `_get_dynamic_critical_keywords()`, `_generate_writer_guidance_v60_8()`를 helper surface로 남겨 둔다.
  - 그러나 repo 전체 호출 그래프를 보면 이 helper들과 그 구현체인 `PromptBuilder.generate_writer_guidance_v60_8()`, `PromptBuilder.generate_arc_position_guide()`, `FeedbackSystem.simplify_prompt_for_retry()`는 unit test 외 live consumer가 없다.
  - 실제 Stage 4 writer prompt 경로는 `build_mandatory_context()`가 돌려주는 5개 키와 `mandatory_context`만 쓰며, writer guidance 통합 문자열을 전달하는 슬롯 자체가 없다.
  - 결과적으로 `High Impact Zone`, 관계 전환 정당화, 시간/공간 연속성, 클리셰 회피, retry simplification 계열 설계가 helper 표면에만 남고 실 집필 프롬프트에는 닿지 않는다.
- 코드 근거
  - `main_a.py:655-657` `_simplify_prompt_for_retry()`는 thin delegate지만 repo 내 추가 call site가 없다.
  - `main_a.py:671-673`, `719-730`도 각각 `_generate_arc_position_guide()`, `_generate_writer_guidance_v60_8()` thin delegate만 제공한다.
  - `main_a.py:675-712` `_get_dynamic_critical_keywords()`는 helper 구현을 가지지만 repo 내 call site가 정의부뿐이다.
  - `modules/core/prompt_builder.py:486-524` `generate_writer_guidance_v60_8()`는 5개 guide를 합성한다고 명시하지만, repo 내 소비자는 없다.
  - `modules/core/prompt_builder.py:732-796` `generate_v50_writer_prompt()` 역시 self-diagnosis를 포함한 writer prompt 집계기지만 호출 그래프가 정의부에서 끊긴다.
  - `modules/core/stage4_context_builder.py:2035-2526` `build_mandatory_context()` 반환값은 `reference_anchor_prompt`, `mandatory_context`, `anti_trope_prompt`, `justification_prompt`, `reflexion_prompt`뿐이다.
  - `modules/core/stage4_orchestrator.py:676-692` Stage 4는 위 dict에서 `mandatory_context`와 `anti_trope_prompt`를 꺼내 다음 단계로 넘긴다.
  - `modules/core/stage4_context_builder.py:2555-2592` 최종 `_RoundContext`에도 `writer_guidance` 또는 `arc_position_guide` 슬롯은 없다.
- downstream 영향 경계
  - Stage 4 manuscript generation의 사전 guidance 강화 경로 전체
  - retry 횟수가 늘어날수록 단순화/고밀도 가이드가 들어와야 한다는 설계 기대
  - prompt-builder unit test가 “가이드가 생성된다”는 사실만 보장하고, 실제 ChiefWriter prompt에 도달하는지에 대한 운영 신뢰
- 현재 테스트 근거 또는 테스트 부재
  - `tests/test_prompt_builder.py:83-295`는 pure helper 결과만 검증한다.
  - `tests/test_stage4_context_builder.py:534-560`은 `build_mandatory_context()` 반환 key를 정확히 5개로 고정하며, 이 고정 집합에 writer guidance 관련 키는 없다.
  - `tests/test_stage4_context_builder.py`와 `tests/test_stage4_orchestrator.py`는 actual Stage 4 wiring에서 `generate_writer_guidance_v60_8()` 또는 `generate_arc_position_guide()` 출력 포함 여부를 검증하지 않는다.
  - 이번 실행 검증에서도 `233 passed`, `45 passed`가 모두 green이지만, 이는 pure helper와 현재의 누락된 wiring을 동시에 통과시키는 상태다.
- 기존 문서와의 중복 여부
  - `duplicate status: none`
  - 2026-03-13 control-plane 문서는 Stage 4 entry / context DI drift를 다뤘고, 이번처럼 guidance helper 자체가 pipeline-dead라는 표면은 직접 채택하지 않았다.
- 권장 후속 조치
  - 의도된 활성 기능이라면 Stage 4 context builder 또는 ChiefWriter round context에 `writer_guidance` slot을 실제로 배선한다.
  - 의도적으로 폐기된 기능이라면 `main_a.py` export와 `PromptBuilder` dead helper를 정리해 callback surface를 줄인다.
  - 최소 회귀로는 “Stage 4 round context에 High Impact Zone 또는 temporal guide가 실제 포함되는지”를 검증하는 integration test를 추가해야 한다.

### [MRF-T3-02] P2 | `generate_arc_context_v60()`는 `current_arc_no`를 받는 척하지만 실제로는 쓰지 않는다

- ID
  - `MRF-T3-02`
- Severity
  - `P2`
- 현상 요약
  - Stage 2 consumer는 `generate_arc_context_v60(all_refined_arcs, next_arc_no)` 형태로 다음 Arc 번호를 넘긴다.
  - `main_a.py` thin delegate도 이 시그니처를 그대로 유지한다.
  - 그런데 `PromptBuilder.generate_arc_context_v60()` 본문은 state extractor path와 fallback path 모두에서 `current_arc_no`를 한 번도 참조하지 않는다.
  - 결과적으로 callback 표면은 “target arc-aware context builder”처럼 보이지만 실제 출력은 항상 `all_refined_arcs`만으로 결정된다.
- 코드 근거
  - `main_a.py:752-754` `_generate_arc_context_v60()`는 `current_arc_no`를 그대로 전달한다.
  - `modules/core/stage2_orchestrator.py:277-278`는 batch 시작 전에 `batch_start + 1`을 넘긴다.
  - `modules/core/stage2_finalizer.py:1155-1156`도 PASS 직후 `global_arc_no + 1`을 넘긴다.
  - `modules/core/prompt_builder.py:549`에서 `current_arc_no`가 시그니처에 존재하지만, 파일 내 추가 `current_arc_no` 사용처는 정의부뿐이다.
  - `modules/core/prompt_builder.py:561-595`, `597-726` 어느 경로에서도 target arc 번호 기반 분기나 포맷팅이 없다.
- downstream 영향 경계
  - Stage 2 batch enrich의 `transfused_history`
  - Stage 2 finalizer가 다음 Arc 준비용으로 재생성하는 latest context
  - future/current arc boundary를 명시적으로 넘기고 있다고 믿는 consumer contract
  - 장기적으로 `current_arc_no` 기반 suspended plot / elapsed-time / boundary-aware formatting을 붙일 여지를 이미 시그니처가 약속하고 있으므로, 현재 no-op 상태는 조용한 drift다
- 현재 테스트 근거 또는 테스트 부재
  - `tests/test_prompt_builder.py:459-469`는 `generate_arc_context_v60()`가 문자열을 돌려준다는 사실만 본다.
  - `tests/test_stage2_context.py:91-105`는 callback이 app에서 추출되는지만 확인한다.
  - `tests/test_arc_retry.py`, `tests/test_stage2_preflight_helpers.py`, `tests/test_stage2_finalizer.py`는 `generate_arc_context_v60`를 `MagicMock("context_text")`로 대체해 semantic contract를 검증하지 않는다.
  - `current_arc_no` 값이 달라도 출력이 달라져야 하는지, 혹은 현재처럼 무시해도 되는지 고정하는 test가 없다.
- 기존 문서와의 중복 여부
  - `duplicate status: related-but-new-callback-surface`
  - `TF-49-arc-state-reconciliation-spec.md`와 `context_quality_audit.md`는 arc context 품질 보강을 다뤘지만, 이번 finding처럼 `main_a.py` callback signature가 실질적으로 no-op 인자를 가진다는 contract drift는 직접 채택하지 않았다.
- 권장 후속 조치
  - `current_arc_no`가 정말 필요 없다면 시그니처에서 제거해 consumer 기대를 줄인다.
  - 필요하다면 `generate_arc_context_v60()`가 next/current arc 번호를 기준으로 최소한 boundary-aware block이나 formatting 차이를 내도록 구현을 보강해야 한다.
  - 회귀 테스트는 같은 `all_refined_arcs`에 `current_arc_no=3`과 `current_arc_no=7`을 넣었을 때 기대 차이가 있음을 명시하거나, 반대로 no-op 인자를 제거하는 쪽으로 계약을 축소해야 한다.

### [MRF-T3-03] P1 | retry focus mode의 `build_minimal_arc_context()`가 full arc context와 다른 내공 시작값을 줄 수 있다

- ID
  - `MRF-T3-03`
- Severity
  - `P1`
- 현상 요약
  - retry focus mode는 `stage2_preflight.py`에서 `build_minimal_arc_context()`를 사용해 이전 Arc 상태를 축약 주입한다.
  - 그런데 `build_minimal_arc_context()`는 `arc_end_state.internal_energy`가 비어 있으면 마지막 Arc의 `internal_energy_loss`만 보고 `100 - loss`를 계산한다.
  - 반면 `generate_arc_context_v60()` fallback은 모든 이전 Arc의 누적 소모를 합산해 `final_energy`를 계산한다.
  - 따라서 `arc_end_state.internal_energy`가 비어 있는 long-running state에서 retry path와 일반 arc-context path가 서로 다른 시작 내공을 말할 수 있다.
- 코드 근거
  - `modules/core/stage2_preflight.py:871-893` retry focus mode는 `build_minimal_arc_context()` 출력으로 `enhanced_context`를 재조립한다.
  - `modules/core/feedback_system.py:324-330` `build_minimal_arc_context()`는 마지막 Arc의 `internal_energy_loss`만으로 `100 - loss`를 계산한다.
  - `modules/core/prompt_builder.py:654-679` fallback arc context는 모든 `all_refined_arcs`의 `internal_energy_loss`를 누적하고, `arc_end_state.internal_energy`가 없으면 누적 소모 기준으로 최종 내공을 산출한다.
  - 실제 구현체 비교 재현:
    - 2개 Arc에서 손실이 `20%`, `30%`이고 마지막 `arc_end_state.internal_energy`가 비어 있을 때
    - `FeedbackSystem.build_minimal_arc_context()`는 `내공: 70%`
    - `PromptBuilder.generate_arc_context_v60()` fallback은 `[⚡ 최종 내공]: 50%`
- downstream 영향 경계
  - Stage 2 retry focus mode의 Analyst prompt
  - same project / same arc에서도 일반 context path와 retry path가 다른 시작 상태를 설명하는 semantic drift
  - retry 횟수가 올라갈수록 “더 적은 정보”가 아니라 “다른 정보”가 주입될 위험
- 현재 테스트 근거 또는 테스트 부재
  - `tests/test_feedback_system.py:287-312`는 single-arc 입력에서 `100 - loss` 계산만 검증한다.
  - `tests/test_prompt_builder.py:459-469`는 fallback path가 문자열을 돌려주는지만 본다.
  - 다중 Arc 누적 손실 상태에서 `build_minimal_arc_context()`와 `generate_arc_context_v60()`가 같은 시작 상태를 말하는지 비교하는 회귀는 없다.
  - 이번 조사에서 실제 구현체 비교를 수행해 drift를 재현했다.
- 기존 문서와의 중복 여부
  - `duplicate status: related-but-new-callback-surface`
  - 기존 context quality / reconciliation 문서는 arc context 보강 일반론을 다뤘고, 이번처럼 retry callback이 full context와 다른 에너지 값을 줄 수 있다는 `main_a.py` helper contract 문제는 직접 다루지 않았다.
- 권장 후속 조치
  - `build_minimal_arc_context()`는 최소한 `generate_arc_context_v60()`와 같은 누적 소모 계산 규칙을 공유해야 한다.
  - 가장 단순한 방향은 누적 에너지 계산 로직을 공용 유틸로 뽑아 minimal / fallback 모두 재사용하게 만드는 것이다.
  - 회귀 테스트로 “2개 이상 Arc, 마지막 arc_end_state.energy 없음” 케이스를 추가해 retry path와 full context path의 final energy가 같음을 잠가야 한다.

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| writer guidance live wiring | 부재 | `Stage4ContextBuilder.build_mandatory_context()` 또는 `_RoundContext`에 `generate_writer_guidance_v60_8()` 출력이 실제 실리는지 보는 integration test |
| `current_arc_no` semantic contract | 부재 | 같은 Arc 집합에 서로 다른 `current_arc_no`를 넣었을 때 기대 출력 차이 또는 no-op 제거를 고정하는 test |
| retry minimal vs full context 정합성 | 부재 | 다중 Arc 누적 손실 상태에서 `build_minimal_arc_context()`와 `generate_arc_context_v60()`의 내공/부상/위치가 합치되는지 비교하는 test |
| `build_focused_context()`의 `violations` 활용도 | 불명확 | 위반 유형별로 focused context가 실제로 달라져야 하는지, 아니면 “직전 상태 압축”이 계약인지 고정하는 semantic test |

## 마감 체크

- 코드 근거 포함: 완료
- downstream 영향 경계 포함: 완료
- 현재 테스트 근거 또는 테스트 부재 포함: 완료
- 기존 문서와의 중복 여부 포함: 완료
- PASS1 후보 `4건 -> PASS2 제거 1건 -> PASS3 확정 3건`: 완료
