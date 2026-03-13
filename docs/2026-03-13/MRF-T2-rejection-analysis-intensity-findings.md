# [MRF-T2] Rejection Analysis / Intensity Findings

> 작성일: 2026-03-13
> 상태: `executed`
> 조사 모드: `static / read-only / code-and-test verification / source-report cross-check / UTF-8 only`
> 기준 오더: `main_a-retry-feedback-detail-full-survey-audit-order.md`

이 문서는 `main_a.py`의 rejection normalization, pattern analysis, intensity helper 표면에 대한 T2 실행 결과다. 조사 중 코드 수정은 하지 않았다.

---

## 조사 범위

- `main_a.py`
  - `_quantify_reject_feedback()`
  - `_analyze_score_breakdown()`
  - `_get_adaptive_feedback_intensity()`
  - `_analyze_rejection_pattern_v60()`
  - `_normalize_rejection_reason()`
  - `_get_rejection_fix_guide()`
- 직접 consumer
  - `modules/core/stage2_context.py`
  - `modules/core/stage2_orchestrator.py`
  - `modules/core/stage2_validation_pipeline.py`
  - `modules/core/stage2_finalizer.py`
- 교차 검증 근거
  - `tests/test_stage2_context.py`
  - `tests/test_stage2_preflight_helpers.py`
  - `tests/test_feedback_system.py`
  - `docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md`
  - `docs/2026-03-13/main_a-control-plane-detail-consolidated-findings.md`

## 실행 확인

- `pytest tests/test_stage2_context.py -q` -> `16 passed`
- `pytest tests/test_feedback_system.py -q -k "QuantifyRejectFeedback or GetAdaptiveFeedbackIntensity or GenerateStructuredBlueprintFeedback"` -> `14 passed`
- `pytest tests/test_stage2_preflight_helpers.py -q -k "rejection_history_format"` -> `1 passed`

## PASS 기록

- PASS 1: `main_a.py` T2 helper, Stage2 consumer, required tests, 기존 문서를 전수 확인했다. 후보 finding은 3건이었다.
- PASS 2: 코드와 테스트, 기존 감리 문서를 대조했다. `_analyze_score_breakdown()`의 legacy schema drift는 후보로 남았지만 현재 retry-feedback live consumer를 입증하지 못해 확정에서 제외했다.
- PASS 3: 최종 2건을 retained finding으로 확정했다.

## Finding Ledger

| ID | Sev | 상태 | 파일 / 함수 | 요약 |
|----|-----|------|-------------|------|
| `MRF-T2-01` | `P2` | retained | `main_a.py::_analyze_rejection_pattern_v60`, `modules/core/stage2_finalizer.py` | `specific_issue` 기반 상세 분석 블록이 현재 Stage2 rejection history 경로에서는 사실상 dead field다 |
| `MRF-T2-02` | `P2` | retained | `main_a.py::_normalize_rejection_reason`, `_get_rejection_fix_guide`, `modules/core/stage2_orchestrator.py` | 자유서술형 Stage2 REJECT reason이 좁은 정규화 버킷 밖으로 떨어지면 반복 패턴 분석이 `기타`와 무가이드로 수렴한다 |

---

## `MRF-T2-01` - `specific_issue` 상세 블록은 현재 Stage2 경로에서 채워지지 않는다

1. ID
   - `MRF-T2-01`
2. Severity
   - `P2`
3. 현상 요약
   - `_analyze_rejection_pattern_v60()`는 repeated reject를 요약할 때 `specific_issue`를 모아 `구체적 문제 지점` 섹션을 붙이도록 작성돼 있다.
   - 그러나 현재 Stage2 rejection history producer는 `stage`, `arc_no`, `reason`, `attempt`만 기록한다. 그 결과 live Stage2 경로에서는 상세 섹션이 사실상 비활성 상태다.
4. 코드 근거
   - `main_a.py:776-787`은 `reject["specific_issue"]`가 있을 때만 구체 항목을 수집한다.
   - `main_a.py:812-816`은 수집된 항목이 있을 때만 `📋 구체적 문제 지점` 블록을 출력한다.
   - `modules/core/stage2_finalizer.py:1690-1697`은 Stage2 rejection history에 `specific_issue` 없이 `reason`과 `attempt`만 append한다.
   - `modules/core/stage2_orchestrator.py:487-498`은 이 history를 그대로 `_analyze_rejection_pattern_v60()`에 넣고, 반환 문자열을 `current_feedback` 앞에 주입한다.
5. downstream 영향 경계
   - 영향은 Stage2의 repeated REJECT retry guidance 경계에 한정된다.
   - 패턴 분석 블록은 생성되지만 실제로는 요약 reason count만 전달하고, “어느 지점이 반복해서 깨지는가”에 대한 세부 cue는 Analyst/FourPhase 재시도 프롬프트에 실리지 않는다.
   - 배치 전체를 중단시키지는 않지만, 반복 재시도에서 피드백 밀도를 낮춘다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_stage2_preflight_helpers.py:224-238`은 rejection history 형식을 고정하지만 `specific_issue` 필드는 요구하지 않는다.
   - `tests/test_stage2_context.py:91-115`는 일부 callback binding만 확인할 뿐, `_analyze_rejection_pattern_v60()` 출력 구조는 검증하지 않는다.
   - 이번 조사에서 `pytest tests/test_stage2_preflight_helpers.py -q -k "rejection_history_format"`를 실행했고 통과했다. 즉 현재 테스트도 minimal history shape만 잠근다.
7. 기존 문서와의 중복 여부
   - `none`
   - `docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md`는 Stage4 reverse feedback loop를 다루며, Stage2 rejection-history payload detail 손실은 다루지 않는다.
8. 권장 후속 조치
   - Stage2 rejection history producer에 `specific_issue` 또는 동등한 structured detail field를 추가한다.
   - 최소 한 개의 regression test로 repeated reject history에 `specific_issue`가 들어갈 때 pattern analysis output에 상세 섹션이 나타나는지 고정한다.
   - detail field를 계속 쓰지 않을 계획이면 helper의 dead branch를 제거하거나 명시적으로 deprecated 처리한다.

---

## `MRF-T2-02` - 자유서술형 REJECT reason이 `기타`로 붕괴하면 수정 가이드가 사라진다

1. ID
   - `MRF-T2-02`
2. Severity
   - `P2`
3. 현상 요약
   - `_normalize_rejection_reason()`는 9개 안팎의 키워드 버킷만 지원하고, 나머지는 전부 `기타`로 떨어뜨린다.
   - `_analyze_rejection_pattern_v60()`는 정규화 결과를 그대로 repeated-pattern 집계와 수정 가이드 lookup에 사용한다.
   - 따라서 실제 Stage2 history에 기록되는 자유서술형 reason이 버킷 밖이면 반복 reject 분석이 `기타: N회`만 남기고 actionable guide를 잃는다.
4. 코드 근거
   - `modules/core/stage2_finalizer.py:1691-1697`은 Director의 raw `audit.reason`을 잘라서 그대로 history에 저장한다.
   - `tests/test_stage2_preflight_helpers.py:226-237`은 실제 저장 예시로 자유서술 reason `반복 전개`를 고정한다.
   - `main_a.py:822-846`의 정규화는 `중복`, `수여`, `부상`, `위치`, `소지`, `내공`, `json`, `길이`, `범위` 외에는 `기타`를 반환한다.
   - `main_a.py:805-810`은 normalized reason별 fix guide를 붙이는데, `main_a.py:848-861`에서 `기타`는 guide가 비어 있다.
   - `modules/core/stage2_orchestrator.py:495-497`은 이 pattern analysis 결과를 다음 재시도 feedback 앞에 바로 prepend한다.
5. downstream 영향 경계
   - 영향은 repeated Stage2 REJECT의 retry guidance 품질에 한정된다.
   - Stage2가 자주 내는 자연어 사유가 정규화되지 않으면, 재시도 프롬프트는 count 정보만 늘고 수정 방향은 비어 있는 generic block을 받게 된다.
   - hard crash는 아니지만, rejection reason normalization과 fix guide의 계약 일관성이 약하다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_feedback_system.py`는 `quantify_reject_feedback()`와 `get_adaptive_feedback_intensity()`는 검증하지만, `_normalize_rejection_reason()`, `_get_rejection_fix_guide()`, `_analyze_rejection_pattern_v60()`에 대한 직접 테스트는 없다.
   - `tests/test_stage2_context.py:91-115`도 해당 helper semantics를 검증하지 않는다.
   - 이번 조사에서 관련 pytest는 모두 통과했지만, 실제 recorded reason이 정규화 버킷 안에 들어오는지 보장하는 테스트는 확인하지 못했다.
7. 기존 문서와의 중복 여부
   - `none`
   - 검토한 기존 문서는 Stage4 loop 보존성, control-plane DI, bootstrap 경계에 집중돼 있었고, `main_a.py` reason normalization bucket coverage 문제는 다루지 않았다.
8. 권장 후속 조치
   - Stage2에서 실제로 저장되는 reject reason 샘플을 기준으로 normalization taxonomy를 재작성한다.
   - `반복 전개`, `설정 충돌`, `인과 붕괴`, `밀도 부족` 등 현재 history에 실리는 reason class를 직접 golden test로 추가한다.
   - `기타` fallback에는 최소한 generic fix guide를 붙여 empty guidance를 피한다.

---

## PASS 2 제거 후보

### C1. `_analyze_score_breakdown()`의 schema drift

- 후보 근거:
  - `main_a.py:571-623`은 `setting_consistency`, `scene_composition`, `narrative_flow`, `length_fulfillment`, `prose_quality` 키를 기대한다.
  - `modules/domain/agents/director_ensemble.py:44-60`의 canonical breakdown은 `continuity_contradiction`, `blueprint_coverage`, `quality_engagement`, `length`, `python_warnings` 체계를 쓴다.
  - `modules/core/stage2_finalizer.py:1299-1305`도 modern Stage2 retry payload에는 `votes`, `pass_votes`, `median_score`만 모은다.
- 제거 사유:
  - 현재 조사 범위에서 `_enrich_director_result()`의 live retry-feedback consumer를 입증하지 못했다.
  - schema mismatch 자체는 강한 냄새지만, 이번 T2 pass에서는 실제 downstream break를 입증하지 못해 retained로 승격하지 않았다.

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| `_normalize_rejection_reason()` 직접 회귀 테스트 | 없음 | Stage2 history에 실제 저장되는 reason class를 fixture로 고정한 unit test |
| `_analyze_rejection_pattern_v60()` 출력 구조 | 없음 | `specific_issue` 유무에 따라 output block이 달라지는지 검증하는 테스트 |
| `Stage2Context.from_app()`의 T2 callback binding | 부분 검증 | `analyze_rejection_pattern_v60`, `get_adaptive_feedback_intensity`가 실제 app callback으로 추출되는지 직접 확인하는 테스트 |
| `_analyze_score_breakdown()` live consumer | open question | 현재 runtime에서 `_enrich_director_result()`가 어디서 호출되는지 추가 caller inventory 또는 로그 근거 |

## 마감 요약

- PASS1 후보: 3건
- PASS2 제거: 1건
- PASS3 확정: 2건
- 최종 요약: `PASS1 3 -> PASS2 remove 1 -> PASS3 final 2`
