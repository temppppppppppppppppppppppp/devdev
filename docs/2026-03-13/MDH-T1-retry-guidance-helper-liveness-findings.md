# MDH-T1: Retry / Guidance Helper Liveness Findings

> 작성일: 2026-03-13
> 작성자: `claude-opus-4-6`
> 트랙: main_a.py dormant helper / live consumer inventory — Terminal 1
> 상태: `PASS 3 확정`
> 범위: 7개 retry/guidance helper의 실제 runtime consumer 전량 조사

---

## 1. 요약

| # | Helper | Line | Status | Severity | Prod Callers | Test Callers |
|---|--------|------|--------|----------|-------------|-------------|
| 1 | `_generate_writer_guidance_v60_8` | 733 | **DORMANT** | P3 | 0 | 0 (delegate: 2) |
| 2 | `_generate_arc_position_guide` | 685 | **DORMANT** | P3 | 0 | 0 (delegate: 7) |
| 3 | `_simplify_prompt_for_retry` | 669 | **DORMANT** | P3 | 0 | 0 (delegate: 3) |
| 4 | `_build_focused_context` | 677 | **LIVE** | — | 1 (Stage2Context → stage2_validation_pipeline) | 5+ |
| 5 | `_build_minimal_arc_context` | 681 | **LIVE** | — | 1 (Stage2Context → stage2_preflight) | 5+ |
| 6 | `_generate_reverse_feedback_stage4_to_3` | 752 | **DORMANT** | P2 | 0 | 0 (delegate: 4) |
| 7 | `_enrich_director_result` | 432 | **DORMANT** | P2 | 0 | 0 |

**DORMANT 5건, LIVE 2건, P0 0건, P1 0건**

---

## 2. 확정 Findings

### MDH-T1-01: `_generate_writer_guidance_v60_8` — Dead Facade

- **ID**: MDH-T1-01
- **Severity**: P3
- **현상 요약**: `main_a.py:733-744`에 정의된 thin delegate. `PromptBuilder.generate_writer_guidance_v60_8()`에 위임. wrapper 자체를 호출하는 코드가 repo 전역에 없음. delegate 대상도 production caller 0.
- **코드 근거**: `main_a.py:733` 정의만 존재. `grep -r` 결과 정의 1건 외 0건.
- **downstream 영향 경계**: 없음. 호출되지 않으므로 삭제해도 production 영향 0.
- **현재 테스트 근거**: wrapper 직접 테스트 0건. delegate인 `PromptBuilder.generate_writer_guidance_v60_8()`는 `tests/test_prompt_builder.py` L278-293에서 2건 테스트.
- **기존 문서와의 중복 여부**: `related-but-new-live-consumer-surface` — 기존 facade/retry 문서에서 dead facade 언급 있으나 live consumer inventory 관점 독립 finding.
- **권장 후속 조치**: wrapper 삭제 가능. delegate 자체의 production 연결 여부는 별도 판단.

### MDH-T1-02: `_generate_arc_position_guide` — Dead Facade

- **ID**: MDH-T1-02
- **Severity**: P3
- **현상 요약**: `main_a.py:685`에 정의. `PromptBuilder.generate_arc_position_guide()`에 위임. wrapper/delegate 모두 production caller 0.
- **코드 근거**: `main_a.py:685` 정의만 존재. repo 전역 caller 0건.
- **downstream 영향 경계**: 없음.
- **현재 테스트 근거**: wrapper 0건. delegate `tests/test_prompt_builder.py` L76-114에서 7건 테스트.
- **기존 문서와의 중복 여부**: `related-but-new-live-consumer-surface`
- **권장 후속 조치**: wrapper 삭제 가능.

### MDH-T1-03: `_simplify_prompt_for_retry` — Dead Facade

- **ID**: MDH-T1-03
- **Severity**: P3
- **현상 요약**: `main_a.py:669`에 정의. `FeedbackSystem.simplify_prompt_for_retry()`에 위임. wrapper/delegate 모두 production caller 0.
- **코드 근거**: `main_a.py:669` 정의만 존재. repo 전역 caller 0건.
- **downstream 영향 경계**: 없음.
- **현재 테스트 근거**: wrapper 0건. delegate `tests/test_feedback_system.py` L558-579에서 3건 테스트.
- **기존 문서와의 중복 여부**: `related-but-new-live-consumer-surface`
- **권장 후속 조치**: wrapper 삭제 가능.

### MDH-T1-04: `_generate_reverse_feedback_stage4_to_3` — Dormant (Bypassed by Design)

- **ID**: MDH-T1-04
- **Severity**: P2
- **현상 요약**: `main_a.py:752-756`에 정의. `FeedbackSystem.generate_reverse_feedback_stage4_to_3()`에 위임. 동일 패밀리의 `_generate_reverse_feedback_stage4_to_2`는 `Stage2Context`에 DI 바인딩되어 **LIVE**이나, `stage4_to_3` variant는 어떤 StageContext에도 바인딩되지 않음. Stage 4→3 reverse feedback 경로 자체가 미연결.
- **코드 근거**: `main_a.py:752` 정의. `stage2_context.py:248`에 `_stage4_to_2`만 바인딩. `stage3_context.py`, `stage4_context.py` 어디에도 `stage4_to_3` 미등록.
- **downstream 영향 경계**: Stage 4→3 역방향 피드백이 의도되었다면 미연결 상태. 현재 파이프라인은 Stage 4→2 역방향만 동작.
- **현재 테스트 근거**: wrapper 0건. delegate `tests/test_feedback_system.py` L411-427에서 4건 테스트.
- **기존 문서와의 중복 여부**: `related-but-new-live-consumer-surface` — 기존 MRF-T4 문서에서 reverse feedback 토폴로지 언급 있으나 이 helper의 DI 미연결은 신규 발견.
- **권장 후속 조치**: Stage 4→3 reverse feedback가 설계상 필요한지 확인. 불필요하면 wrapper 삭제. 필요하면 Stage3Context 또는 Stage4Context에 DI 바인딩 추가.

### MDH-T1-05: `_enrich_director_result` — Dormant (Bypassed by Implementation)

- **ID**: MDH-T1-05
- **Severity**: P2
- **현상 요약**: `main_a.py:432-569` (137줄). Director 결과를 Python 후처리로 enrichment하는 메서드. `action_items`, `error_category`, `responsibility`, `score_breakdown` 분석 등을 수행. 그러나 이 필드들은 `director_ensemble.py`(L846, 859, 862, 1353, 1358)에서 Director LLM이 직접 출력하여 이미 채워진 상태. 이 helper는 한 번도 호출된 적 없음.
- **코드 근거**: `main_a.py:432` 정의. repo 전역 caller 0건 (정의 제외). `stage4_interview_round.py`가 `action_items`/`error_category`를 소비하지만 source는 `director_ensemble.py` output.
- **downstream 영향 경계**: 없음. 삭제해도 production 영향 0. Director ensemble이 동일 필드를 직접 생산.
- **현재 테스트 근거**: 0건 (wrapper도 delegate도 테스트 없음).
- **기존 문서와의 중복 여부**: `related-but-new-live-consumer-surface` — 137줄 실체 코드가 완전 dormant인 점은 기존 문서에서 미다룸.
- **권장 후속 조치**: 삭제 가능. Director ensemble 직접 생산으로 대체 완료된 상태. 대원칙 3(Director 주권주의)에도 부합 — Python이 아닌 LLM이 판단.

---

## 3. LIVE 확인 항목 (Finding 해당 없음)

### `_build_focused_context` (L677) — LIVE

- **DI 경로**: `main_a.py:677` → `Stage2Context.from_app()` (stage2_context.py:253) → `stage2_validation_pipeline.py:897`
- **Runtime consumer**: `Stage2ValidationPipeline._run_validation_loop()` — arc 검증 retry 시 violation 기반 focused context 구축
- **Test coverage**: `test_stage2_context.py:96,104`, `test_stage2_validation_pipeline.py:33`, `test_stage2_preflight_helpers.py:60,700`, e2e tests
- **Conclusion**: Stage2 validation retry path에서 활성 사용. Dormant 아님.

### `_build_minimal_arc_context` (L681) — LIVE

- **DI 경로**: `main_a.py:681` → `Stage2Context.from_app()` (stage2_context.py:252) → `stage2_preflight.py:882`
- **Runtime consumer**: `Stage2Preflight` Focus Mode — retry 누적 시 컨텍스트 축소용 minimal arc summary 구축
- **Test coverage**: `test_stage2_preflight.py:66,250`, `test_sc6_observability.py:54`, e2e tests
- **Conclusion**: Stage2 preflight Focus Mode에서 활성 사용. Dormant 아님.

---

## 4. PASS 추적 요약

### PASS 1 → PASS 2 → PASS 3

| Helper | PASS 1 후보 | PASS 2 교차검증 | PASS 3 확정 |
|--------|------------|----------------|------------|
| `_generate_writer_guidance_v60_8` | DORMANT (HIGH) | 확인 — repo 전역 caller 0 | **DORMANT 확정** |
| `_generate_arc_position_guide` | DORMANT (HIGH) | 확인 — repo 전역 caller 0 | **DORMANT 확정** |
| `_simplify_prompt_for_retry` | DORMANT (HIGH) | 확인 — repo 전역 caller 0 | **DORMANT 확정** |
| `_build_focused_context` | LIVE (HIGH) | 확인 — Stage2Context DI → stage2_validation_pipeline | **LIVE 확정** |
| `_build_minimal_arc_context` | LIVE (HIGH) | 확인 — Stage2Context DI → stage2_preflight | **LIVE 확정** |
| `_generate_reverse_feedback_stage4_to_3` | DORMANT (HIGH) | 확인 — DI 미연결, `_stage4_to_2`만 바인딩 | **DORMANT 확정** |
| `_enrich_director_result` | DORMANT (HIGH) | 확인 — 137줄 완전 미호출, director_ensemble 대체 | **DORMANT 확정** |

- PASS 1 후보 7건 → PASS 2 제거 0건 → PASS 3 확정 5건 DORMANT + 2건 LIVE
- Coverage gap: 없음
- Open question: `_generate_reverse_feedback_stage4_to_3`의 설계 의도 (Stage4→3 역방향)가 향후 필요한지는 제품 판단 필요

---

## 5. 조사 근거 목록

- `main_a.py` L432-756 (7개 helper 정의)
- `modules/core/stage2_context.py` (DI 바인딩 전량)
- `modules/core/stage2_validation_pipeline.py` L897 (build_focused_context 소비)
- `modules/core/stage2_preflight.py` L882 (build_minimal_arc_context 소비)
- `modules/core/feedback_system.py` L218, L311, L576 (delegate 대상)
- `modules/core/prompt_builder.py` (delegate 대상)
- `modules/domain/agents/director_ensemble.py` L846, 859, 862, 1353, 1358 (action_items/error_category 생산)
- `modules/core/stage4_interview_round.py` (action_items/error_category 소비)
- `tests/test_feedback_system.py`, `tests/test_prompt_builder.py`, `tests/test_stage2_context.py`
- `tests/test_stage2_preflight.py`, `tests/test_stage2_preflight_helpers.py`
- `tests/test_stage2_validation_pipeline.py`
- `tests/e2e/test_l3_golden_route.py`, `tests/e2e/test_l3_stage2_realproject.py`
- `scripts/run_stage2_smoke.py`
- repo 전역 grep (5개 dormant helper 각각 정의 외 caller 0건 확인)
