# 비TF-DB 코드베이스 재판정 메모

> 작성: 2026-03-10
> 범위: `docs/2026-03-10` 내 문서 중 `TF-DB-quality-boost-audit.md` 제외
> 제외 사유: 사용자 기준 코드 작업 진행 중
> 판정 원칙: 문서 헤더/서술은 근거에서 제외하고, 코드/테스트 흔적만으로 판정

## 결론

남은 문서들 중에서 `미실현`이라고 **99% 이상 확신으로 단정**할 수 있는 문서는 없다.

- `continuity-packet-codex-order.md`, `continuity-packet-ext-codex-order.md`, `db-utilization-boost-codex-order.md`
  - 이미 구현 흔적이 명확하므로 `미실현` 후보에서 제외
- `quality-boost-beyond-db-audit.md`
  - 미실현 항목이 적지 않지만, 문서 전체를 `미실현`으로 99% 이상 확정할 수는 없음
- `stage-quality-improvement-audit-3pass.md`
  - 열린 갭은 남아 있으나, 핵심 구조 항목 다수가 이미 실현되어 있어 문서 전체를 `미실현`으로 99% 이상 확정할 수는 없음

## 이미 구현 흔적이 명확한 문서

### 1. `continuity-packet-codex-order.md` / `continuity-packet-ext-codex-order.md`

- CP 생성/주입이 실제 코드에 존재:
  - `modules/core/stage4_context_builder.py:308`
  - `modules/core/stage4_context_builder.py:1366`
- 확장 항목인 `npc_history`, 관계 변천사, `established_value` 반영 흔적 존재:
  - `modules/core/stage4_context_builder.py:342`
  - `modules/core/stage4_context_builder.py:385`
  - `modules/core/stage4_context_builder.py:453`
- 회귀 테스트 존재:
  - `tests/test_continuity_packet.py:120`
  - `tests/test_continuity_packet.py:219`
  - `tests/test_continuity_packet.py:241`
  - `tests/test_continuity_packet.py:446`

### 2. `db-utilization-boost-codex-order.md`

- 문서의 §1~§10과 직접 대응되는 테스트 묶음 존재:
  - `tests/test_db_utilization.py:36`
  - `tests/test_db_utilization.py:112`
  - `tests/test_db_utilization.py:147`
  - `tests/test_db_utilization.py:216`
  - `tests/test_db_utilization.py:267`

따라서 위 3건은 이번 메모의 `미실현 문서화` 대상이 아니다.

## 99% 미실현 판정 보류 문서

### 1. `quality-boost-beyond-db-audit.md`

`미실현`으로 99% 이상 단정하지 않은 이유:

- 문서가 제안한 축 중 일부는 이미 코드에 존재한다.
  - `WritingDirective` 체인:
    - `modules/core/stage4_types.py:77`
    - `modules/core/writing_directive_generator.py:23`
    - `modules/core/stage4_interview_round.py:610`
    - `modules/domain/agents/chief_writer_context.py:260`
    - `modules/domain/agents/chief_writer_quality.py:262`
  - Director `consistency_checklist`:
    - `modules/domain/agents/director_ensemble.py:937`
    - `modules/domain/agents/director_ensemble.py:1068`
  - 품질 추세/회귀 관측:
    - `modules/core/quality_dashboard.py:730`
    - `modules/core/quality_dashboard.py:833`
    - `modules/core/stage2_preflight.py:468`
    - `modules/core/stage4_post_processor.py:1183`
  - `quality_risk` 전달:
    - `modules/domain/agents/three_phase_blueprint_generator.py:658`
    - `modules/core/stage3_orchestrator.py:848`
    - `modules/core/stage4_orchestrator.py:1011`
    - `modules/core/stage4_interview_round.py:599`

동시에, 문서의 일부 제안은 현재 코드에서 확인되지 않았다.

- `modules/` 전체 검색 기준 no-match:
  - `previous_attempt.history`
  - `episode_quality_labels`
  - `top_success_patterns`
  - `quality_distribution`

판정:

- `부분 실현 + 미실현 혼재`
- 따라서 문서 전체를 `미실현`으로 문서화하지 않음

### 2. `stage-quality-improvement-audit-3pass.md`

`미실현`으로 99% 이상 단정하지 않은 이유:

- 문서가 말하는 주요 구조 항목 다수가 이미 실현돼 있다.
  - Continuity Packet:
    - `modules/core/stage4_context_builder.py:308`
    - `modules/core/stage4_context_builder.py:1366`
  - `quality_risk` 기반 degraded/escalation 경로:
    - `modules/domain/agents/three_phase_blueprint_generator.py:658`
    - `modules/core/stage3_orchestrator.py:848`
    - `modules/core/stage4_orchestrator.py:1011`
  - advisory/quality observability:
    - `modules/core/quality_dashboard.py:833`
    - `modules/core/stage2_preflight.py:468`
    - `modules/core/stage4_post_processor.py:1183`
  - Director checklist 구조:
    - `modules/domain/agents/director_ensemble.py:937`
    - `modules/domain/agents/director_ensemble.py:1068`

다만 문서의 일부 후속 산출물은 현재 코드에서 확인되지 않았다.

- `modules/` 전체 검색 기준 no-match:
  - `must_fix`
  - `handoff_hint`
  - `dropped-section`
  - `reference manifest`

판정:

- `핵심 구조는 일부 이상 실현, 후속 스키마/보고물은 미완`
- 따라서 문서 전체를 `미실현`으로 문서화하지 않음

## 최종 집계

- `TF-DB-quality-boost-audit.md`
  - 사용자 기준 코드 작업 중이므로 이번 판정에서 제외
- 99% 이상 확신으로 `미실현` 문서화 가능한 나머지 문서
  - 없음
