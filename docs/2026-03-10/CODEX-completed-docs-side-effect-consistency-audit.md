# CODEX 완료 문서 묶음 사이드 이펙트 및 정합성 전수조사

> 상태: 4-pass 감리 완료 (코드 수정 금지 준수, UTF-8 기준, 확신도 96%)
> 범위: `TF-DB-quality-boost-audit.md`, `quality-boost-beyond-db-audit.md`, `TF-QR-quality-remaining-audit.md`, `TF-250-long-serial-scale-audit.md`, `TF-QI-structural-quality-gaps-audit.md`, `context-window-utilization-audit.md`, `TF-OPT-optimization-audit.md`
> 최종 판정: PASS

## 결론

- P0/P1급 사이드 이펙트나 상호 충돌은 확인되지 않았다.
- 현재 워크트리 기준 전체 회귀는 `3816 passed, 16 skipped, 1 warning`이다.
- 현재 `pytest --collect-only -q tests` 기준선은 `3832 collected`다.
- 남은 이슈는 코드 버그가 아니라 `문서 드리프트 2건 + 해석 주의 1건`이다.

## 조사 원칙

- 코드 수정 금지
- UTF-8 고정
- 완료된 7개 문서와 실제 구현 경로만 대조
- 문서의 당시 기준선과 현재 기준선을 분리
- 보류 항목은 `의도적 제외`인지 `미완료`인지 구분

## Pass 1 - 문서 상호 정합성

| 공용 표면 | 관련 문서 | 현재 코드 상태 | 판정 |
|---|---|---|---|
| `stage_attempts` / 실패 피드백 루프 | TF-DB G2, Beyond-DB FL-2/3/5, TF-QR QR-7, TF-OPT OPT-3 | `four_phase_arc_generator.py`, `stage4_orchestrator.py`, `db_manager.py`, `failure_analyzer.py`에서 공용 경로로 연결됨 | OK |
| Context budget / summary cap / CP 축약 | TF-DB A3/B3, TF-250 LS-5, context-window, TF-OPT OPT-2 | `world_state.py`, `fact_ledger.py`, `stage4_context_builder.py`, `director_ensemble.py`가 상호 보완 관계로 동작 | OK |
| POV / NPC 지식 경계 / character constraints | TF-QI, TF-QR | `pre_llm_validator.py`, `chief_writer_quality.py`, `stage4_interview_round.py`, `work_guard.py`, `director_auditor.py`로 배선 완료 | OK |
| 품질 라벨 / 버전 추적 | Beyond-DB QM-4, TF-OPT OPT-3 | `episode_quality_labels` sidecar + `prompt_version` 저장/분석 경로 정합 | OK |
| Stage 0~4 입력 손실 완화 | context-window, TF-250, TF-OPT | Stage 0 샘플링 확장, Stage 2/3 보강, Stage 4 headroom 정책이 충돌 없이 누적됨 | OK |

## Pass 2 - 코드 기준 사이드 이펙트 점검

- `stage_attempts`는 더 이상 FailureAnalyzer 내부 전용이 아니다. `modules/domain/agents/four_phase_arc_generator.py:1728`에서 Arc 실패 요약을 직접 소비하고, `modules/core/db_manager.py:518`의 `prompt_version`과 `modules/core/failure_analyzer.py:258`의 버전 비교까지 이어진다.
- `episode_quality_labels`는 additive sidecar로 일관된다. `modules/core/db_manager.py:597`, `modules/core/stage4_post_processor.py:308`, `modules/core/failure_analyzer.py:81` 경로가 맞물리고 기존 `manuscripts` 스키마와 충돌하지 않는다.
- WorldState/FactLedger 확장과 context-window/long-serial 패치가 서로 발목을 잡지 않는다. `modules/core/world_state.py:747`, `modules/core/fact_ledger.py:469`, `modules/core/stage4_context_builder.py:804`, `modules/core/stage4_context_builder.py:1134`, `modules/domain/agents/director_ensemble.py:756` 기준으로 `CP 상세 참조` + headroom 재배분이 함께 동작한다.
- POV 관련 패치는 다층 배선으로 정합하다. `modules/validation/pre_llm_validator.py:424`의 `전지적/혼합` 검사, `modules/domain/agents/chief_writer_quality.py:289`의 self-critique 재사용, `modules/core/stage4_interview_round.py:974`의 Director POV 주입이 서로 보완적이다.
- WorkGuard 강화도 대원칙을 깨지 않는다. `modules/core/genre_guards/work_guard.py:299`는 warning-only로 누적하고, `modules/domain/agents/director_auditor.py:1225`는 이를 advisory로만 전달한다.
- Analyst cache와 prompt version tracking도 독립적이다. `modules/domain/agents/analyst.py:145`의 캐시는 비용 최적화 경로이고, `modules/core/prompt_loader.py:250` 이하의 버전 태그는 분석/회귀 비교 경로라 상호 간섭이 없다.

## Pass 3 - 오탐 제거

### 오탐 1. 이전 문서의 테스트 수집 수 불일치

이건 구현 충돌이 아니라 `시점 차이`다. 초기 문서가 당시 기준선을 적고, 후속 문서가 더 늦은 기준선을 적었기 때문이다.

| 문서 | 문서 내 collect-only 기준 | 현재 기준 | 판정 |
|---|---:|---:|---|
| `TF-DB-quality-boost-audit.md` | 3756 | 3832 | 역사적 기준선, 현재 SSOT 아님 |
| `quality-boost-beyond-db-audit.md` | 3756 | 3832 | 역사적 기준선, 현재 SSOT 아님 |
| `TF-QR-quality-remaining-audit.md` | 3785 | 3832 | 역사적 기준선, 현재 SSOT 아님 |
| `TF-250-long-serial-scale-audit.md` | 3794 | 3832 | 역사적 기준선, 현재 SSOT 아님 |
| `TF-OPT-optimization-audit.md` | 3832 | 3832 | 최신 기준과 일치 |

### 오탐 2. `TF-DB`의 `stage_attempts` 진단 전체가 아직 유효하다는 해석

- `TF-DB-G2`의 "`stage_attempts`는 FailureAnalyzer 내부만 소비" 문구는 후속 문서 반영 이후에는 더 이상 현재 상태가 아니다.
- 다만 이건 `당시 진단이 틀렸다`가 아니라 `후속 배치에서 실제로 닫혔다`에 가깝다.
- 따라서 `TF-DB`는 실행 감사 문서로는 여전히 가치가 있지만, 현재 상태 문서로 재사용하면 안 된다.

### 오탐 3. 보류 항목이 남았으니 완료 문서가 아니라는 해석

이 해석은 기각한다. 아래 항목들은 문서와 실제 구현 모두에서 `의도적 제외` 또는 `후순위 유지`로 처리됐다.

| 문서 | 항목 | 현재 해석 |
|---|---|---|
| `quality-boost-beyond-db-audit.md` | `QI-QM-3` | 높은 비용으로 보류, 누락 아님 |
| `TF-250-long-serial-scale-audit.md` | `LS-7`, `LS-8` | 모니터링 우선, 누락 아님 |
| `TF-OPT-optimization-audit.md` | `OPT-2` | 부분 해소 후 잔여, deferred 유지가 맞음 |
| `TF-QI-structural-quality-gaps-audit.md` | `P3/NO-GO` 묶음 | 문서 자체가 제외를 명시함 |

## Pass 4 - 기준선 재확인

- `pytest --collect-only -q tests`: `3832 collected`
- `pytest tests/ -q`: `3816 passed, 16 skipped, 1 warning`
- 경고 1건은 기존 `tests/stage4_v2_test/test_batch_1_to_10.py:28`의 `PytestCollectionWarning`으로 신규 사이드 이펙트가 아니다.

## 최종 판정

- 완료된 7개 문서는 현재 코드 기준으로 서로 충돌하지 않는다.
- 공용 표면인 `stage_attempts`, `prompt_version`, `episode_quality_labels`, `CP 축약`, `POV`, `character_constraints`, `context cap`은 상호 정합하다.
- 지금 남아 있는 문제는 `문서의 시점 정보 드리프트`뿐이다. 즉, 구현 리스크가 아니라 감사 문서를 현재 운영 기준으로 읽을 때의 해석 리스크다.
- 이후 Opus 문서를 덧붙여 대조할 때는 이 문서를 `현재 기준선 문서`로 쓰고, 개별 감사 문서는 `당시 실행 문서`로 취급하는 편이 안전하다.

## CODEX 의견

- 이번 묶음은 `코드 레벨 PASS / 문서 레벨 저강도 드리프트`로 보는 게 맞다.
- 추가 코드 수정은 권장하지 않는다.
- 나중에 메타 감리 문서를 하나 더 만든다면, 핵심은 새 패치가 아니라 `현재 기준선 SSOT(3832 collected, 3816 passed)`를 어디에 고정할지 정하는 일이다.
