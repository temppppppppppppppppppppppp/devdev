# [MDH-T5] Call Graph / Runtime Artifact / Regression Findings

> 작성일: 2026-03-13
> 상태: `executed / PASS3 completed`
> 조사 모드: `static / read-only / code-and-test verification / source-report cross-check / UTF-8 only`
> 기준 오더: `main_a-dormant-helper-live-consumer-detail-full-survey-audit-order.md`
> 작성자: `opus`
> 최종 판정: `retained P2 3건, PASS2 제거 2건`

이 문서는 T1~T4 범위의 25개 helper에 대해 repo 전역 정적 검색, e2e/canary/smoke runtime artifact, 기존 감리 문서 3트랙(MRF/MFS/MPN) 통합본을 교차 대조한 PASS3 결과다.
코드 직접 수정은 수행하지 않았다.

---

## 조사 범위

- repo 전역 검색 결과 (grep 기반 call graph)
- `tests/e2e/test_l3_golden_route.py`
- `tests/e2e/test_l3_stage3_smoke.py`
- `tests/e2e/test_l3_stage4_smoke.py`
- `tests/e2e/test_npc_continuity_e2e.py`
- `tests/e2e/test_retry_recovery_e2e.py`
- `tests/e2e/test_lm_advisory_smoke.py`
- `tests/e2e/test_smoke_pipeline.py`
- `tests/test_run_stage4_canary.py`
- `tests/test_stage4_canary_tools.py`
- `scripts/run_stage2_smoke.py`
- `scripts/run_stage3_smoke.py`
- `scripts/run_stage4_smoke.py`
- `scripts/run_stage4_canary.py`
- 기존 감리 통합본
  - `main_a-retry-feedback-detail-consolidated-findings.md` (MRF, 13건)
  - `main_a-facade-shim-detail-consolidated-findings.md` (MFS, 12건)
  - `main_a-persistence-narrative-detail-consolidated-findings.md` (MPN, 16건)
  - 각각의 3pass 재감리본 (전부 `pass` 판정)
- 추가 참조
  - `MFS-T3-stage3-stage4-audit-callback-findings.md`
  - `MFS-T4-ui-stage01-presentation-findings.md`
  - `MRF-T3-prompt-guidance-context-findings.md`
  - `MRF-T4-cross-stage-reverse-feedback-findings.md`
  - `MCP-T2-agent-bootstrap-di-findings.md`

---

## PASS 기록

### PASS 1 — 표면 수집

T1~T4 범위의 25개 helper에 대해 repo 전역 grep을 수행하고, e2e/canary/smoke 10개 파일, script 4개 파일을 전부 읽어 call graph를 재구성했다. 후보 5건을 뽑았다.

- 후보 A: 6개 helper가 production caller 0건, DI export 0건, test-only caller 0건 — 순수 dead surface 클러스터
- 후보 B: `_classify_rejection_feedback`가 정의와 underlying 구현 테스트만 있고, production caller와 DI export가 없다
- 후보 C: e2e/smoke 테스트가 main_a helper를 lambda/MagicMock으로 주입해 DI signature drift를 숨긴다
- 후보 D: `_generate_reverse_feedback_stage4_to_3`가 Stage3 consumer 없이 dormant
- 후보 E: `_load_v50_history`가 no-op stub

### PASS 2 — 교차 검증

후보 2건을 제거했다.

- 후보 D 제거
  - 판정: `already-covered-do-not-reopen`
  - 근거: `MRF-T4-001`이 동일 helper의 Stage3 consumer 부재를 `P1`으로 이미 확정. dormant-helper inventory 관점에서도 새 정보가 없다.

- 후보 E 제거
  - 판정: `already-covered-do-not-reopen`
  - 근거: `MCP-T2` coverage gap log가 이미 "No-op stub at `main_a.py:2026-2038`; no required test demonstrates a real restore contract"로 기록. helper 자체의 no-op 상태는 이미 잠겨 있다.

후보 A/B/C는 retained finding으로 유지했다.
- 후보 A: 기존 트랙들이 개별 helper를 건드렸지만 (MRF-T3-01은 writer guidance 3개, MRF-T4-003은 `_enrich_director_result`, MCP-T2는 `_ignite_quad_cache_system`), "dead helper 전체를 한 ledger로 모았는가"는 아니었다. T5의 call graph inventory 책임 경계에서 신규다.
- 후보 B: MFS-T3가 coverage gap으로 이관했지만 dormant 확정은 하지 않았다. T5 전역 grep으로 production caller 0건을 확인했으므로 신규 dormant 확정이다.
- 후보 C: 개별 트랙들이 MagicMock blind spot을 부분적으로 언급했지만 (MPN-T5-004, MFS-T2-002), e2e/smoke 전체에서 lambda/MagicMock injection 패턴이 DI contract 전체를 가리는 구조적 문제를 T5 관점으로 모은 것은 신규다.

---

## PASS 3 — 확정 Findings

### Finding Ledger

| ID | Sev | 상태 | 파일/함수 | 요약 | duplicate status |
|----|-----|------|-----------|------|------------------|
| `MDH-T5-001` | `P2` | confirmed | `main_a.py` (6개 helper) | 6개 helper가 production caller 0건, DI export 0건으로 순수 dead surface를 구성한다 | `related-but-new-live-consumer-surface` |
| `MDH-T5-002` | `P2` | confirmed | `main_a.py::_classify_rejection_feedback`, `state_service.py`, `feedback_system.py` | `_classify_rejection_feedback()`는 정의와 underlying 테스트만 있고 production caller가 없는 dormant surface다 | `related-but-new-live-consumer-surface` |
| `MDH-T5-003` | `P2` | confirmed | `tests/e2e/*.py`, `scripts/run_stage*_smoke.py` | e2e/smoke 테스트가 main_a helper를 lambda/MagicMock으로 주입해 DI signature drift를 구조적으로 가린다 | `related-but-new-live-consumer-surface` |

---

## 상세 Findings

### [MDH-T5-001] P2 | 6개 helper가 production caller 0건으로 dead surface 클러스터를 구성한다

1. ID
   - `MDH-T5-001`
2. Severity
   - `P2`
3. 현상 요약
   - repo 전역 grep 결과, 아래 6개 helper는 정의부(main_a.py) 외에 production caller, DI context export, test call site가 모두 없다.
     - `_generate_writer_guidance_v60_8` (main_a.py:733)
     - `_generate_arc_position_guide` (main_a.py:685)
     - `_simplify_prompt_for_retry` (main_a.py:669)
     - `_enrich_director_result` (main_a.py:432)
     - `_ignite_quad_cache_system` (main_a.py:1148)
     - `_is_cache_alive` (main_a.py:1293)
   - 이 helper들은 SovereignApp의 API 표면에 남아 있지만 어떤 Stage orchestrator, DI context, e2e, smoke, canary에서도 호출되지 않는다.
   - `_is_cache_alive`의 유일한 caller는 `_ignite_quad_cache_system` 내부(main_a.py:1189,1215,1238)이며, 그 caller 자체가 dead이므로 연쇄 dead다.
4. 코드 근거
   - `_generate_writer_guidance_v60_8`: main_a.py:733 정의. grep 결과 추가 참조 0건. Stage2Context/Stage4Context `from_app()` 미포함.
   - `_generate_arc_position_guide`: main_a.py:685 정의. grep 결과 추가 참조 0건.
   - `_simplify_prompt_for_retry`: main_a.py:669 정의. grep 결과 추가 참조 0건.
   - `_enrich_director_result`: main_a.py:432 정의. grep 결과 추가 참조 0건. MRF-T4-003이 "호출 지점이 확인되지 않았다"고 기록.
   - `_ignite_quad_cache_system`: main_a.py:1148 정의. grep 결과 외부 caller 0건. MCP-T2 coverage gap이 "dead code"로 기록.
   - `_is_cache_alive`: main_a.py:1293 정의. 유일한 caller가 `_ignite_quad_cache_system` 내부.
5. downstream 영향 경계
   - 이 helper들이 존재해도 runtime에 영향을 주지 않는다.
   - 그러나 SovereignApp의 API 표면을 넓히고, 코드 리뷰와 감리에서 live surface와 혼동을 만든다.
   - 특히 `_generate_writer_guidance_v60_8`과 `_generate_arc_position_guide`는 MRF-T3-01이 "export만 되고 실제 writer prompt에 닿지 않는다"고 확정한 helper들과 같은 family로, 설계 의도 대비 배선 누락인지 의도된 폐기인지 판단이 필요하다.
6. 현재 테스트 근거 또는 테스트 부재
   - 6개 helper 모두 직접 테스트가 없다.
   - underlying 구현체(`PromptBuilder.generate_writer_guidance_v60_8()` 등)에는 unit test가 있지만, thin delegate 호출 경로는 미검증이다.
   - `_ignite_quad_cache_system`과 `_is_cache_alive`는 underlying 구현체 테스트도 없다.
7. 기존 문서와의 중복 여부
   - `related-but-new-live-consumer-surface`
   - MRF-T3-01은 writer guidance 3개의 callback contract drift를, MRF-T4-003은 `_enrich_director_result`의 live wiring 부재를, MCP-T2는 `_ignite_quad_cache_system`의 dead code 상태를 각각 건드렸다. 그러나 "6개를 dead cluster로 통합해 live helper와 분리한 inventory"는 이번이 처음이다.
8. 권장 후속 조치
   - 의도된 활성 기능이라면: 6개 helper를 실제 pipeline에 배선한다 (특히 writer guidance family).
   - 의도된 폐기라면: main_a.py에서 정의를 제거하고 underlying 구현체의 dead helper도 함께 정리한다.
   - 최소한 dead/live 경계를 문서화해 감리와 리뷰에서 혼동을 줄인다.

### [MDH-T5-002] P2 | `_classify_rejection_feedback()`는 production caller가 없는 dormant surface다

1. ID
   - `MDH-T5-002`
2. Severity
   - `P2`
3. 현상 요약
   - `main_a.py:2780`에 정의된 `_classify_rejection_feedback()`는 `self._state_service.classify_rejection_feedback()`에 위임하는 thin delegate다.
   - underlying 구현체인 `FeedbackSystem.classify_rejection_feedback()`에는 unit test 7건이 있고(`test_feedback_system.py:523-553`), `StateService.classify_rejection_feedback()`에도 위임 테스트가 있다(`test_state_service.py:230-236`).
   - 그러나 `self._classify_rejection_feedback()`를 호출하는 production code가 repo 전역에 없다. Stage2Context, Stage3Context, Stage4Context 어느 DI context에도 export되지 않는다.
   - MFS-T3가 "이번 T3 직접 downstream에서 사용처를 찾지 못해 finding이 아니라 coverage gap으로 이관"했지만, T5 전역 grep으로 production caller가 0건임을 확정한다.
4. 코드 근거
   - `main_a.py:2780-2783` 정의 (thin delegate to StateService)
   - `modules/core/services/state_service.py:236-239` StateService 위임 (thin delegate to FeedbackSystem)
   - `modules/core/feedback_system.py:759` 실제 구현
   - repo 전역 `_classify_rejection_feedback` grep: 정의(main_a.py:2780), 위임 호출(main_a.py:2782)만 존재. 외부 caller 0건.
   - `modules/core/stage2_context.py`, `stage3_context.py`, `stage4_context.py`: `classify_rejection_feedback` slot 또는 `from_app` 주입 없음.
5. downstream 영향 경계
   - 현재 runtime에 영향 없음.
   - rejection feedback 분류가 pipeline에서 빠져 있다면, REJECT reason에 따른 적응적 재시도 전략이 작동하지 않을 수 있다.
   - MRF-T2-02가 지적한 "자유서술형 REJECT reason이 좁은 정규화 버킷 밖으로 떨어지면 기타/무가이드로 수렴"하는 문제의 한 원인일 수 있다.
6. 현재 테스트 근거 또는 테스트 부재
   - underlying 구현: `test_feedback_system.py:516-553` (7건, 카테고리별 분류 검증)
   - StateService 위임: `test_state_service.py:230-236`
   - main_a thin delegate: 직접 테스트 없음
   - production caller: 없음
7. 기존 문서와의 중복 여부
   - `related-but-new-live-consumer-surface`
   - MFS-T3 coverage gap이 "별도 audit" 요청으로 남겼고, 이번 T5가 그 audit을 전역 grep으로 실행해 dormant 확정한 것이다.
8. 권장 후속 조치
   - 의도된 활성 기능이라면: Stage2Context 또는 Stage4Context에 callback으로 export하고, retry loop에서 rejection 분류 결과를 실제 활용하도록 배선한다.
   - 의도된 폐기라면: main_a.py thin delegate를 제거한다. underlying 구현은 별도 판단.

### [MDH-T5-003] P2 | e2e/smoke 테스트가 main_a helper를 lambda/MagicMock으로 주입해 DI signature drift를 구조적으로 가린다

1. ID
   - `MDH-T5-003`
2. Severity
   - `P2`
3. 현상 요약
   - e2e/smoke/canary 테스트 전체에서 main_a.py helper를 실제 호출하지 않고, lambda 또는 MagicMock으로 대체해 DI contract를 조립한다.
   - 이 패턴은 helper의 signature, 반환 타입, side effect가 변경되어도 e2e/smoke 테스트가 자동으로 통과하게 만든다.
   - 결과적으로 "helper가 live consumer와 올바르게 연결돼 있는가"라는 질문에 대해 e2e/smoke regression net이 답할 수 없다.
4. 코드 근거
   - `tests/e2e/test_l3_golden_route.py:237-254`: Stage2Context 조립 시 15개 callback을 전부 lambda/빈문자열로 주입
     - `build_focused_context=lambda **_kw: ""`
     - `build_minimal_arc_context=lambda *_a, **_k: ""`
     - `analyze_rejection_pattern_v60=lambda *_a, **_k: ""`
     - `generate_arc_context_v60=lambda _arcs, _arc_no: ""`
   - `tests/e2e/test_l3_stage3_smoke.py:125-146`: app mock에 5개 helper를 MagicMock으로 직접 할당
     - `app._get_arc_context_for_episode = MagicMock(side_effect=...)`
     - `app._validate_arc_data_fields = MagicMock(side_effect=lambda arc, _idx: arc)`
     - `app._validate_blueprint_integrity = MagicMock(return_value={"passed": True, ...})`
     - `app._audit_event = MagicMock()`
     - `app._write_audit_summary = MagicMock()`
   - `scripts/run_stage3_smoke.py:110-129`: 동일 패턴
   - `scripts/run_stage4_smoke.py`: Stage4Context를 MagicMock callback으로 조립
   - `tests/test_run_stage4_canary.py:8-15`: SimpleNamespace에 `_flush_audit_buffer=MagicMock()`
   - `tests/e2e/test_retry_recovery_e2e.py:36-75`: mock_app fixture에서 Stage4Orchestrator에 주입할 때 helper를 전부 MagicMock auto-attribute로 남김
5. downstream 영향 경계
   - 실제 helper signature가 변경되어도 e2e 테스트가 MagicMock auto-attribute 또는 `**kwargs` lambda로 흡수해 green을 유지한다.
   - 이로 인해 facade shim drift(MFS 트랙), callback contract drift(MRF 트랙), shared helper semantics drift(MPN 트랙)가 모두 e2e/smoke regression에서 감지 불가능하다.
   - helper가 dead인지 live인지도 e2e 테스트만으로는 구별할 수 없다 — dead helper를 MagicMock으로 주입하면 테스트가 통과하기 때문이다.
6. 현재 테스트 근거 또는 테스트 부재
   - e2e/smoke 10개 파일, script 4개 파일을 전수 확인했다.
   - real SovereignApp 인스턴스를 boot하는 테스트는 `scripts/run_stage4_canary.py`뿐이다. 이 스크립트도 `_stage_4_v2_chief_writer()`, `_flush_audit_buffer()`, `_get_int_input`만 직접 사용하고 나머지 helper는 간접적으로만 live된다.
   - 나머지 모든 e2e/smoke는 MagicMock/lambda injection으로 helper를 대체한다.
   - helper signature parity를 검증하는 e2e 테스트는 0건이다.
7. 기존 문서와의 중복 여부
   - `related-but-new-live-consumer-surface`
   - MPN-T5-004는 Stage3 DI slot coverage의 MagicMock auto-attr 공백을, MFS-T2-002는 facade bound-method drift가 MagicMock 분할 테스트에만 잠기는 문제를 각각 부분적으로 다뤘다.
   - 이번 finding은 e2e/smoke 전체에서 lambda/MagicMock injection이 DI contract 전체를 구조적으로 가리는 패턴을 통합한 것이다.
8. 권장 후속 조치
   - 최소 1개 e2e 테스트에서 real SovereignApp 또는 real `from_app()` factory를 사용해 DI callback signature가 live helper와 일치하는지 검증한다.
   - 또는 `Stage2Context.from_app()`, `Stage3Context.from_app()`, `Stage4Context.from_app()`에 대해 signature parity assertion을 추가한다 (예: `inspect.signature` 비교).
   - MagicMock auto-attribute 흡수를 방지하려면 `spec=SovereignApp` 또는 `spec_set=True`를 사용한다.

---

## Rejected / Removed Candidates

### RC-1. `_generate_reverse_feedback_stage4_to_3` dormant

- 판정: `already-covered-do-not-reopen`
- 근거: `MRF-T4-001`이 동일 helper의 Stage3 consumer 부재를 `P1`으로 이미 확정. dormant-helper inventory 관점에서도 신규 정보가 없다.

### RC-2. `_load_v50_history` no-op stub

- 판정: `already-covered-do-not-reopen`
- 근거: `MCP-T2` coverage gap log가 "No-op stub at `main_a.py:2026-2038`; no required test demonstrates a real restore contract"로 이미 기록.

---

## Comprehensive Ledger: dead / dormant / bypassed-live / live / unknown

아래는 T1~T4 범위 25개 helper의 전수 inventory다.

### dead (6건)

| Helper | 정의 위치 | 근거 |
|--------|-----------|------|
| `_generate_writer_guidance_v60_8` | main_a.py:733 | production caller 0, DI export 0, test caller 0 |
| `_generate_arc_position_guide` | main_a.py:685 | production caller 0, DI export 0, test caller 0 |
| `_simplify_prompt_for_retry` | main_a.py:669 | production caller 0, DI export 0, test caller 0 |
| `_enrich_director_result` | main_a.py:432 | production caller 0, DI export 0, test caller 0 |
| `_ignite_quad_cache_system` | main_a.py:1148 | production caller 0, 내부적으로만 `_is_cache_alive` 호출 |
| `_is_cache_alive` | main_a.py:1293 | 유일한 caller `_ignite_quad_cache_system`이 dead |

### dormant (5건)

| Helper | 정의 위치 | 근거 |
|--------|-----------|------|
| `_classify_rejection_feedback` | main_a.py:2780 | 정의 + underlying 테스트 있음, production caller 0, DI export 0 |
| `_generate_reverse_feedback_stage4_to_3` | main_a.py:752 | 정의 + unit test 있음, Stage3 DI export 없음 (MRF-T4-001) |
| `_load_v50_history` | main_a.py:2083 | `_init_v50_modules`에서 호출되지만 no-op stub (MCP-T2) |
| `_load_character_archetypes` | main_a.py:2772 | 정의만 있음, production caller 0, DI export 0 |
| `_get_archetype_reference_for_npcs` | main_a.py:2776 | 정의만 있음, production caller 0, DI export 0 |

### bypassed-live (2건)

| Helper | 정의 위치 | 근거 |
|--------|-----------|------|
| `_extract_npc_profiles` | main_a.py:2764 | facade 존재, Stage4 live consumer가 bypass (MFS-T4-001) |
| `_get_character_traits` | main_a.py:2768 | facade 존재, live production caller 없음, test만 존재 |

### live (12건)

| Helper | 정의 위치 | DI export | production caller |
|--------|-----------|-----------|-------------------|
| `_build_focused_context` | main_a.py:677 | Stage2Context:253 | stage2_validation_pipeline.py:897 |
| `_build_minimal_arc_context` | main_a.py:681 | Stage2Context:252 | stage2_preflight.py retry focus |
| `_audit_event` | main_a.py:2786 | — (직접 내부 + StateService) | main_a.py 12곳+, StateService 10곳+ |
| `_flush_audit_buffer` | main_a.py:2790 | Stage4Context:172 | atexit, canary, emergency shutdown |
| `_write_audit_summary` | main_a.py:2794 | Stage3Context (DI) | Stage3/4 orchestrator |
| `_get_arc_context_for_episode` | main_a.py:2798 | Stage3Context:120 | Stage3 orchestrator |
| `_validate_arc_data_fields` | main_a.py:2847 | Stage3Context:124 | Stage3 orchestrator, Stage2 finalizer |
| `_validate_blueprint_integrity` | main_a.py:2859 | Stage3Context:125 | Stage3 orchestrator |
| `_build_item_acquisition_timeline` | main_a.py:2718 | Stage4Context:172 | Stage4 context builder |
| `_validate_volume_boundaries` | main_a.py:2685 | — (직접 호출) | stage01_helpers.py:776 |
| `_show_volume_table` | main_a.py:2863 | — (직접 호출) | stage01_helpers.py:838 |
| `_restore_preset_registry` | main_a.py:379 | — (callback 주입) | ProjectService (main_a.py:328) |

### unknown (0건)

- 전 항목이 dead / dormant / bypassed-live / live 중 하나로 분류되었다.

---

## T5 관점 핵심 검사 결과

### 1. static grep과 runtime artifact가 같은 caller inventory를 가리키는가

- **일치함**. e2e/smoke/canary runtime artifact에서 발견된 helper 참조는 static grep 결과의 부분집합이다.
- e2e/smoke가 MagicMock/lambda로 주입하는 helper는 static grep에서도 DI export 경로로 확인된다.
- runtime artifact가 static grep에 없는 숨겨진 caller를 보여주는 경우는 0건이다.

### 2. e2e/smoke/canary에서만 살아 있는 helper가 있는가

- **없음**. e2e/smoke에서 참조되는 helper는 모두 DI context export 또는 직접 internal caller가 있다.
- 단, dead helper 6개는 e2e/smoke에서도 참조되지 않으므로 "e2e-only alive"가 아니라 "completely dead"다.

### 3. 문서상 dead로 보였지만 runtime artifact가 live consumer를 암시하지 않는가

- **암시하지 않는다**. MCP-T2 coverage gap의 `_ignite_quad_cache_system`, `_load_v50_history`는 runtime artifact에서도 확인되지 않았다.
- `_enrich_director_result`도 동일.

### 4. 이미 닫힌 finding을 dormant-helper inventory 명목으로 다시 여는 오탐은 없는가

- **없음**. PASS2에서 `MRF-T4-001` (Stage4→3 reverse feedback)과 `MCP-T2` (load_v50_history)를 `already-covered-do-not-reopen`으로 명시 제거했다.
- retained finding 3건은 모두 기존 트랙에서 부분적으로만 다루어진 표면을 T5 관점(call graph inventory)으로 통합한 것이다.

### 5. 최종 통합 시 ledger를 재구성할 수 있는가

- **가능**. 위 Comprehensive Ledger에 25개 helper 전수가 `dead(6) / dormant(5) / bypassed-live(2) / live(12) / unknown(0)`으로 분류되어 있다.

---

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| dead helper 6개의 의도된 폐기 여부 | 불명확 | writer guidance family는 설계 의도 대비 배선 누락일 수 있고, cache system은 의도된 폐기일 수 있다. 판단은 remediation 단계에서 |
| `_classify_rejection_feedback` 의도된 활성 여부 | 불명확 | rejection feedback 분류가 retry 전략에 실제로 필요한지 설계 의도 확인 필요 |
| e2e signature parity | 전무 | real `from_app()` 또는 `inspect.signature` 기반 parity assertion 0건 |

---

## PASS 요약

- PASS1 후보: 5건
- PASS2 제거: 2건
  - `_generate_reverse_feedback_stage4_to_3` → `already-covered-do-not-reopen` (MRF-T4-001)
  - `_load_v50_history` → `already-covered-do-not-reopen` (MCP-T2 coverage gap)
- PASS3 확정: 3건
  - `MDH-T5-001` P2 (dead helper cluster)
  - `MDH-T5-002` P2 (`_classify_rejection_feedback` dormant)
  - `MDH-T5-003` P2 (e2e/smoke lambda/MagicMock DI drift blindness)

---

## 마감 체크

- 코드 근거 포함: 완료
- downstream 영향 경계 포함: 완료
- 현재 테스트 근거 또는 테스트 부재 포함: 완료
- 기존 문서와의 중복 여부 포함: 완료
- PASS1 -> PASS2 -> PASS3 요약 포함: 완료
- Comprehensive Ledger (dead/dormant/bypassed-live/live/unknown) 포함: 완료
