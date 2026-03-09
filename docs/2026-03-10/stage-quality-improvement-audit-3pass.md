# 시스템 전반 품질 개선 방향 감사 보고서

작성일: 2026-03-10

## 범위

본 문서는 Stage 0~4 전 구간의 품질 개선 방향을 정리한 설계 감사 문서다.  
직접적인 코드 수정은 수행하지 않았고, 현행 구현을 기준으로 개선 우선순위와 오탐 제거 결과만 기록한다.

## 조사 방법

### Pass 1. 구조 전수 조사

- 진입점과 스테이지 맵 확인:
  - `main_a.py`
  - `docs/stage_map/stage0.md`
  - `docs/stage_map/stage1.md`
  - `docs/stage_map/stage2.md`
  - `docs/stage_map/stage3.md`
  - `docs/stage_map/stage4.md`
  - `docs/stage_map/agent_graph.md`
- 기존 품질/컨텍스트 감사 문서 확인:
  - `docs/2026-03-09/quality-improvement-spec.md`
  - `docs/2026-03-09/context-window-utilization-audit.md` (용량 headroom 및 예산 병목 참고용 보조 문서)
  - `docs/2026-02-28/long-term-memory-evaluation.md` (장기 기억 구조와 시나리오 평가의 과거 기준점)
  - `docs/codex_memory_roi_boost_plan.md` (저장량보다 회수율을 우선하는 개선 원칙 참고)
  - `docs/기억 개선 작업.md` (이미 완료된 메모리 개선 항목과 과거 오탐 후보 확인용)
  - `docs/2026-03-09/ui-system-audit.md` (운영 UI 계층과 브리지 구조 참고)
  - `docs/implementation/api-contract-v1.yaml`
  - `docs/implementation/prompt-map-v1.json`

### Pass 2. 구현 경로 재검증

- Stage 0:
  - `modules/core/stage0/style_extractor.py`
  - `modules/core/stage01_helpers.py`
- Stage 1:
  - `modules/core/stage01_helpers.py`
- Stage 2:
  - `modules/core/stage2_orchestrator.py`
  - `modules/core/stage2_preflight.py`
  - `modules/core/stage2_validation_pipeline.py`
  - `modules/core/stage2_finalizer.py`
- Stage 3:
  - `modules/core/stage3_orchestrator.py`
  - `modules/domain/agents/three_phase_blueprint_generator.py`
- Stage 4:
  - `modules/core/stage4_orchestrator.py`
  - `modules/core/stage4_context_builder.py`
  - `modules/core/stage4_interview_round.py`
- 운영/관측/자동화 경계:
  - `modules/api/process_runner.py`
  - `modules/api/prompt_broker.py`
  - `modules/core/context_advisor.py`
  - `modules/core/quality_dashboard.py`

### Pass 3. 오탐 축소 감리

- 관련 테스트와 문서 불일치를 다시 대조:
  - `tests/test_stage01_helpers.py`
  - `tests/test_sweep28.py`
  - `tests/test_pass_with_fix.py`
  - `tests/test_stage4_context_builder.py`
  - `tests/test_stage4_orchestrator.py`
  - `tests/test_blueprint_preflight.py`
  - `tests/test_sc6_observability.py`
  - `tests/test_api_contract.py`
- 이미 구현 또는 테스트로 방어된 항목은 “개선 방향”에서 제외하고, 문서 불일치 또는 정책 문제로 재분류했다.

## 참고 문서 평가

### `docs/2026-03-09/context-window-utilization-audit.md`

평가:

- 이 문서는 Stage 0~4의 컨텍스트 예산이 실제 모델 용량 대비 얼마나 보수적으로 잡혀 있는지 보여주는 보조 감사 문서로는 유효하다.
- 특히 `Stage 0~3은 용량보다 salience/정책 문제가 더 클 수 있다`, `Stage 4는 문맥 총량보다 우선순위 관리가 중요하다`는 판단 근거로는 참고 가치가 높다.
- 다만 이 문서를 곧바로 “현재 코드의 확정 결함 목록”으로 쓰면 오탐 위험이 있다.

제한 사항:

- 일부 제안은 이미 후속 구현에서 선반영됐거나 확대됐다.
  - 예: Stage 0 샘플링/발췌량 관련 제안은 현행 `style_extractor.py` 기준으로 상당 부분 상향 반영돼 있다.
- 일부 수치 제안은 “더 많이 넣자”에 가까워, 현재 감사의 핵심 결론인 `salience`, `threshold 분리`, `advisory 구조화`와는 결이 다르다.
- 라인 번호와 하드캡 표는 작성 시점 기준이므로, 실제 개선 우선순위 판단에는 항상 현행 코드 재검증이 선행돼야 한다.

본 문서에서의 활용 원칙:

- `context-window-utilization-audit.md`는 “예산 여유와 병목 후보를 보여주는 참고 문서”로 채택한다.
- 실제 개선 방향 채택은 본 감사 문서의 3pass 재검증 결과를 우선한다.
- 따라서 본 문서의 Stage 3/4 salience 관련 권고와 Stage 0/2/3 문맥 과소활용 판단에는 해당 문서를 보조 근거로 사용했다.

## `quality-improvement-spec.md`(QI-1) 관계 정의

QI-1은 원고 표현 품질 SSOT이고, 본 문서는 Stage 0~4 구조/정책 품질 SSOT다. 2026-03-10 코드베이스 3pass 재검증 기준으로 QI-1은 `A1~A6 + B2~B5 + C1~C4`가 이미 구현돼 있고, `B1`만 사용자 제공 레퍼런스 원고 대기다. 따라서 QI-1을 “미착수 설계서”로 분류하는 것은 오탐이다. 다만 일부 항목은 dedicated regression test가 얕고, `C3`는 주경로 완료 기준으로 보는 편이 정확하다.

재검증 요약:

- 구현 완료: `A1~A6`, `B2~B5`, `C1~C4`
- 외부 자산 대기: `B1`
- 오탐 제외: `C1/C2는 하드코딩 삭제가 아니라 검출용/예시 풀 전환`, `C3는 주경로 완료`

| QI-1 문제군 | 대응 렌즈 | 본 문서와의 관계 | SSOT 판단 |
| --- | --- | --- | --- |
| 엔딩 반복 (`E-1~E-6`) | 품질 게이트, 입력 계약, CW/Director 프롬프트 계약 | 병렬(구현 완료) | 엔딩 표현 다양성의 상세 규칙과 현재 구현 상태는 QI-1이 SSOT, 본 문서는 그 규칙이 어느 경로로 전달/검증돼야 하는지 다룬다 |
| 투자물 클로닝 (`C-1~C-5`) | Stage 0 입력 계약, Style Guide 설명 가능성, 장르 분기 | `C-1`은 외부 자산 대기, `C-2~C-5`는 병렬(구현 완료) | 레퍼런스 자산 계약과 신뢰도 표기는 본 문서가, 장르 특화 추출 규칙과 현재 적용 상태는 QI-1이 맡는다 |
| 감성/톤 하드코딩 (`T-1~T-8`) | 입력 계약, 프롬프트 기본값, 운영 정책 | `T-1~T-3`,`T-8`은 구현 완료, 나머지는 병렬 백로그 | 하드코딩 제거 상세는 QI-1이, 설정 중앙화/정책화는 본 문서가 맡는다 |

| QI-1 항목군 | 본 문서 대응 | 관계 | 메모 |
| --- | --- | --- | --- |
| `E-1~E-6` | `P1-1 advisory packet`, `P1-4 degraded 공통 스키마`, `P2-6 UI/프롬프트 계약 공통화` | 병렬(구현 완료) | 본 문서는 구조적 전달 경로를 정리하고, 엔딩 품질 규칙의 세부 명세와 구현 상태는 QI-1에 남긴다 |
| `C-1` | Stage 0 `reference manifest + confidence report` | 포함 | 레퍼런스 수량/가중치/제외 규칙은 본 문서가 직접 흡수한다. 자산 배치는 사용자 입력 대기다 |
| `C-2~C-5` | Stage 0 장르 분기 강화, `StyleGuide` 설명 가능성 | 병렬(구현 완료) | 투자물 특화 scoring/prompt 규칙은 QI-1이 상세, 본 문서는 자산 계약과 관측을 정리한다 |
| `T-1~T-3`, `T-8` | 입력 계약과 기본값 중앙화 | 선후에서 병렬로 재분류 | 주경로 구현은 이미 들어가 있으므로, 남은 과제는 운영 정책과 관측 가능성 정비다 |
| `T-4~T-7` | 낮은 ROI의 표현 taxonomy 개선 | 병렬 | 구조 개선과 직접 충돌하지 않으므로 별도 백로그로 유지한다 |

SSOT 원칙:

- Stage 0 문체/표현/클로닝 품질은 QI-1이 SSOT다.
- Stage 1~4 구조, threshold, memory projection, automation, observability 품질은 본 문서가 SSOT다.
- 두 문서가 겹치는 항목은 `코드 → 테스트/계약 → 로그/메트릭 → 문서` 순으로 다시 판정한다.

## 총평

이번 감리 기준에서 가장 큰 개선 레버는 “가드 추가”가 아니다.  
현 시스템은 이미 Stage 2~4에 다층 검증이 많다. 실제 병목은 아래 다섯 가지다.

| 공통 패턴 | 확인 근거 | 품질 리스크 | 개선 방향 | 신뢰도 |
| --- | --- | --- | --- | --- |
| 수동 입력 의존 | `modules/core/stage01_helpers.py`, `modules/core/stage2_orchestrator.py`, `modules/core/stage4_orchestrator.py` | 운영자 판단 편차가 품질 편차로 직결됨 | 인터랙티브 입력을 정책 레이어로 분리하고, 비대화식 실행 정책을 명시 | 높음 |
| 전역 임계치 결합 | `modules/core/stage2_preflight.py`, `modules/core/stage2_finalizer.py`, `modules/domain/agents/three_phase_blueprint_generator.py` | Arc/Blueprint/Manuscript가 같은 점수 경계에 묶여 artifact 특성이 희석됨 | 스테이지별/아티팩트별 threshold profile 분리 | 높음 |
| advisory 과다 누적 | `modules/core/stage2_validation_pipeline.py`, `modules/core/stage4_interview_round.py`, `modules/core/failure_analyzer.py:241-301`, `modules/core/db_manager.py:511-527` | Director/CW에 전달되는 신호가 많아져 핵심 원인 식별력이 떨어질 수 있음 | advisory를 `severity/owner/must_fix/evidence` 기준으로 구조화하고 dedupe. 검증 방법: `FailureAnalyzer.advisory_reject_correlation()` 또는 `stage_attempts.advisory_flags` 상관 분석. 현재 상태: 실측 데이터 미수집 | 중간 |
| 문맥은 풍부하지만 설명 가능성은 약함 | `modules/core/stage4_context_builder.py`, `modules/core/stage0/style_extractor.py` | “무엇이 들어갔고 무엇이 잘렸는지” 불명확하면 품질 튜닝이 어려움 | salience score, dropped section report, confidence report 추가 | 높음 |
| 문서와 런타임의 드리프트 | `docs/stage_map/stage1.md`, `docs/stage_map/stage3.md` vs 실제 코드 | 잘못된 개선 논의와 잘못된 운영 판단 유발 | stage map을 코드 기준으로 재동기화 | 높음 |

실측 대기 가설:

- `advisory 과다 누적`은 코드상 충분히 개연적이지만, 현재 문서 시점에는 실파이프라인 데이터 상관 분석이 없다.
- `mandatory_context salience 관리 부족`도 구조상 개연적이지만, 블록별 크기와 합격률의 실측 상관은 아직 저장되지 않는다.

## 이 문서를 SSOT로 쓰는 원칙

- 본 문서는 “현재 코드 기준 개선 방향”의 SSOT로 사용한다.
- 다른 감사 문서와 회고 문서는 참고 자료로만 사용하고, 우선순위 결정은 항상 이 문서의 3pass 재검증 결과를 따른다.
- 판단 우선순위는 `코드 → 테스트/계약 → 런타임 로그/메트릭 → 과거 문서` 순서다.
- 제안이 여러 축에 걸치면 아래 “시스템 정비 관점 프레임”의 순서대로 본다.
  - 앞단 렌즈에서 결함이 확인되면, 뒷단 렌즈의 최적화는 보류하거나 재분류한다.
- 특히 아래 항목은 금지에 가깝게 본다.
  - salience/관측 근거 없이 context cap만 확대
  - owner/severity 분류 없이 validator만 추가
  - 실행 정책 정의 없이 `input()` 흐름만 GUI/자동화로 감싸기
  - 코드 재검증 없이 과거 문서 수치나 라인 번호를 작업 명세로 채택

## 시스템 정비 관점 프레임

SSOT 관점에서 이 시스템은 최소 아래 12개 렌즈로 봐야 한다.

| 렌즈 | 이번 전수 조사에서 본 실체 | 현재 코드 증거 | 핵심 질문 | 1차 정비 포인트 | 신뢰도 |
| --- | --- | --- | --- | --- | --- |
| 목표 적합성 | `quality_dashboard.py`는 `total_validations`, `stage_stats`, `hud_anomaly_rate`, `avg_blueprint_coverage`, `common_violations`를 추적하지만 사용자 체감 성과를 대표하는 단일 north-star는 없다 | `modules/core/quality_dashboard.py:43-46`, `modules/core/quality_dashboard.py:208-243` | 지금 올리는 품질이 “점수”인지 “장편 연재 성공률”인지 분명한가 | `연재 지속 통과율`, `장기 기억 모순률`, `사용자 재작업 시간` 같은 north-star 후보를 stage 점수와 분리 | 중간 |
| 책임 경계 | Stage 2/3/4 orchestrator가 호출 그래프를 분리하지만, 수동 정책과 degraded 상태는 경계에 걸쳐 있다 | `modules/core/stage2_orchestrator.py:793-838`, `modules/core/stage3_orchestrator.py:808-859`, `modules/core/stage4_orchestrator.py:1011-1123` | 이 문제를 어느 Stage가 책임져야 하는가 | Stage별 책임/입출력 계약을 먼저 잠근 뒤 개선 논의 | 높음 |
| 입력 계약 | `load_reference_manuscripts()`, Stage 1 `volumes`, Mode B prompt contract가 존재하지만 계약 강도가 제각각이다 | `modules/core/stage0/style_extractor.py:739-804`, `modules/core/stage01_helpers.py:614-623`, `modules/api/prompt_broker.py:95-117` | 좋은 입력이 들어오지 않아도 뒤에서 막겠다는 구조인가 | 레퍼런스/권 전략/프롬프트 입력 계약을 명시 자산으로 승격 | 높음 |
| 장기 기억/회수 | 저장 계층과 retrieval 계층은 이미 두텁지만, projection과 salience가 별도 정책으로 닫혀 있지 않다 | `modules/core/world_state.py:659-790`, `modules/core/vec_memory.py:405-788`, `modules/core/stage4_context_builder.py:329-383` | 저장된 기억이 필요한 순간에 올바르게 회수되는가 | cap 확대보다 retrieval/salience/projection 설계 우선 | 높음 |
| 품질 게이트/임계치 | `PatchModeThresholds`, Stage 2/3 gate, Stage 4 fix_scope fallback이 강하게 결합돼 있다 | `modules/core/constants.py:633-645`, `modules/core/stage2_finalizer.py:515-720`, `modules/domain/agents/three_phase_blueprint_generator.py:418-538` | artifact별로 다른 실패를 같은 점수 축으로 보고 있지 않은가 | Arc/Blueprint/Manuscript threshold profile 분리 | 높음 |
| degraded 상태 관리 | `PASS_WITH_WARNING`, `quality_risk`, `PASS_WITH_FIX`는 있으나 전 스테이지 공통 상태 스키마는 없다 | `modules/domain/agents/three_phase_blueprint_generator.py:656-658`, `modules/core/stage3_orchestrator.py:808-859`, `modules/core/stage4_orchestrator.py:1011-1016` | “통과했지만 위험함”을 실제로 별도 상태로 운영하는가 | degraded 상태를 정식 운영 상태로 승격 | 높음 |
| 인간 개입/자동화 경계 | `input()`는 여전히 많지만 브리지 계층도 이미 존재한다 | `modules/core/stage01_helpers.py:508-514`, `modules/core/stage2_orchestrator.py:793-838`, `modules/api/process_runner.py:356-418` | 사람 판단이 필요한 지점과 자동화 가능한 지점이 구분돼 있는가 | input 흐름을 정책 객체와 API contract로 분리 | 높음 |
| 관측 가능성 | quality/reject/prompt 크기 로그는 있으나, trim 근거와 실패 원인의 통합 보고는 약하다 | `modules/core/quality_dashboard.py:208-243`, `modules/core/failure_analyzer.py:241-344`, `modules/core/db_manager.py:475-527` | 왜 실패했고 무엇이 잘렸는지 한눈에 보이는가 | dropped-context, degraded, retrieval 근거를 단일 리포트화 | 높음 |
| UI/운영 경험 | UI는 `bridge_server -> prompt_broker -> process_runner` 체인으로 작동하지만, 상태/프롬프트/실패 이유가 단일 스키마로 묶여 있지 않다 | `modules/api/bridge_server.py:209-224`, `modules/api/prompt_broker.py:53-117`, `modules/api/process_runner.py:356-418` | 사용자가 “지금 시스템이 무엇을 하는지” 직관적으로 이해하는가 | 상태/프롬프트/실패 이유를 동일 스키마로 노출 | 중간 |
| 성능/비용 | `ContextBudgetTracker`는 예산 사용량과 압축 대상을 계산하고, `MetricsCollector`는 모델별 비용/속도를 집계하지만 가격표는 현재 Gemini 중심이다 | `modules/core/context_advisor.py:130-153`, `modules/core/metrics_collector.py:69-78`, `modules/core/metrics_collector.py:280` | 품질 향상이 latency/token/operator time을 무너뜨리지 않는가 | budget tracking과 품질 지표를 같은 회고 표에 묶고, 멀티벤더 비용표를 따로 정리 | 중간 |
| 회귀 방지 | 핵심 경로 테스트는 이미 있으나 장기 연재 golden scenario는 아직 약하다 | `tests/test_stage4_context_builder.py`, `tests/test_api_contract.py`, `tests/test_sc6_observability.py`, `tests/test_pass_with_fix.py` | 이번 개선이 어떤 회귀를 만들 수 있는가 | 기능 추가 전에 golden scenario와 계약 테스트부터 고정 | 높음 |
| 문서/런타임 동기화 | Stage 1/3 stage map과 실제 코드 간 드리프트가 확인됐다 | `docs/stage_map/stage3.md:15,85,92`, `modules/core/stage3_orchestrator.py:768`, `modules/domain/agents/three_phase_blueprint_generator.py:418` | 팀이 실제 시스템이 아닌 문서를 기준으로 움직이고 있지 않은가 | stage map, gotchas, metrics baseline을 코드 기준으로 갱신 | 높음 |

## 개선 제안 분류 규칙

새로운 개선 아이디어는 아래 순서로 분류한다.

1. `어느 렌즈의 문제인가`를 먼저 붙인다.
2. `어느 Stage/모듈이 1차 책임자인가`를 정한다.
3. `정책 문제인지`, `데이터 계약 문제인지`, `retrieval/salience 문제인지`, `UI/운영 문제인지`를 구분한다.
4. 테스트나 계약으로 이미 방어된 영역이면, 결함이 아니라 운영/문서/가시성 문제로 재분류한다.
5. `README.md:46-52`와 TF-36 계열 가드(`modules/domain/agents/unified_blueprint_validator.py:187-188`, `modules/core/world_state.py:321-323`) 기준으로 대원칙 정합성을 먼저 통과시킨다.

작업화 기준:

- `입력 계약`이 약한 문제는 validator 추가보다 upstream contract 설계가 먼저다.
- `장기 기억` 문제는 저장량보다 retrieval/salience 증거가 먼저다.
- `품질 게이트` 문제는 점수 상향/하향보다 owner와 degraded 상태 정의가 먼저다.
- `자동화` 문제는 프롬프트 계약과 fallback default를 먼저 잠근 뒤 UI에 반영해야 한다.
- `UI 개선` 문제는 렌더링 미화보다 상태 스키마와 실패 이유 노출 정리가 먼저다.

## 대원칙 정합성 체크

본 문서에서 사용하는 대원칙 4개는 아래 근거를 합쳐 해석한다.

- 대원칙 1: Python은 수집/포맷/가드 중심이고 최종 판정은 LLM/Director가 맡는다. (`README.md:46-52`, `modules/validation/validation_orchestrator.py:343-391`)
- 대원칙 2: 사실 수정과 해석은 LLM 경유로 처리하고, Python은 기존 상태와 원자료를 보존한다. (`README.md:48`, `tests/test_pass_with_fix.py:1781-1804`)
- 대원칙 3: Director가 최종 품질 결정권을 가진다. (`README.md:46`, `modules/domain/agents/unified_blueprint_validator.py:187-188`)
- 대원칙 4: 사망 NPC와 하드 제약은 Python/LLM 어느 쪽에서도 회귀시키지 않는다. (`modules/core/world_state.py:321-323`, `tests/test_pass_with_fix.py:1686-1708`)

| 제안 | 대원칙 1 (Python 수집만) | 대원칙 2 (LLM만 팩트 수정) | 대원칙 3 (Director 주권) | 대원칙 4 (사망 NPC) | Director 주권 준수 조건 |
| --- | --- | --- | --- | --- | --- |
| `P0-1 stage map 재동기화` | OK | OK | OK | OK | 문서 갱신만 수행 |
| `P0-2 interactive policy 분리` | OK | OK | OK | OK | Python은 default/timeout만 제공하고 품질 판정은 하지 않음 |
| `P0-3 artifact별 threshold profile` | OK | OK | ⚠️ Python hard REJECT로 확장되면 주권 침해 가능 | OK | threshold는 `routing/advisory`로만 쓰고 REJECT는 Director verdict로만 확정 |
| `P0-4 continuity packet` | OK | OK | OK | OK | continuity packet은 context 주입용이며 판정권을 갖지 않음 |
| `P0-5 SSOT 동기화 규칙` | OK | OK | OK | OK | 코드/테스트 우선 순서만 강화 |
| `P1-1 advisory packet 표준화` | OK | OK | OK | OK | advisory는 구조화만 하고 verdict 필드는 두지 않음 |
| `P1-2 mandatory_context salience/ranking` | OK | OK | OK | OK | trim 결과를 보고만 하고 자동 REJECT와 연결하지 않음 |
| `P1-3 reference manifest + confidence report` | OK | OK | OK | OK | 입력 자산 검증만 수행하고 생성 품질 판정은 하지 않음 |
| `P1-4 degraded 공통 스키마` | OK | OK | ⚠️ degraded를 Python 판정으로 오해하면 주권 침해 가능 | OK | degraded는 상태 표기와 escalation 신호로만 쓰고 PASS/REJECT는 Director가 결정 |
| `P1-5 지목형 장기 retrieval` | OK | OK | OK | OK | retrieval는 관련 사실을 보여주기만 하고 수정하지 않음 |
| `P1-6 VecMemory 메타데이터 강화` | OK | OK | OK | OK | 저장 포맷 개선만 수행 |
| `P1-7 운영 지표 팩` | OK | OK | OK | OK | 사후 회고 지표이며 런타임 판정권 없음 |

## 기존 구현과의 교차 검증

사용자가 지목한 완료 항목명은 저장 위치가 분산돼 있어 `CLAUDE.md` 자체보다 현재 코드와 테스트 흔적으로 교차 검증했다.

| 본 문서 제안 | 이미 완료된 항목 | 현재 코드 근거 | 상태 | 잔여 갭 |
| --- | --- | --- | --- | --- |
| advisory 구조화 | TF-D Advisory 시각화 (`CRITICAL/MAJOR/INFO` 태그) | `modules/core/stage4_interview_round.py:517-534` | 부분 완료 | severity 태그는 있으나 `owner`, `must_fix`, `evidence`, `source_file` 필드가 없다 |
| advisory 구조화 | NC-3 `consistency_checklist` | `modules/domain/agents/director_ensemble.py:937-1068`, `tests/test_nc3_checklist.py` | 부분 완료 | Director 응답 내부 체크리스트이며 upstream advisory packet과 합쳐지지 않았다 |
| advisory 구조화 | TF-54 `WritingDirective` | `modules/core/stage4_types.py:77-133`, `modules/core/stage4_interview_round.py:471-478`, `tests/test_pipeline_wiring.py` | 부분 완료 | CW/Director용 구조화 지시이지만 Stage 2/3 advisory와 스키마가 다르다 |
| degraded 상태 관리 | S3-META `quality_risk -> Stage 4 escalation` | `modules/domain/agents/three_phase_blueprint_generator.py:656-658`, `modules/core/stage4_orchestrator.py:1011-1016`, `tests/test_pass_with_fix.py:2189-2248` | 부분 완료 | `quality_risk`는 있으나 Stage 2/4까지 통일된 degraded 상태 schema는 없다 |
| threshold 분리 | TF-46 `PASS_WITH_FIX` bypass | `modules/core/stage2_finalizer.py:545`, `modules/domain/agents/three_phase_blueprint_generator.py:436-444`, `tests/test_pass_with_fix.py:717-741` | 부분 완료 | 일부 경로에서만 `PASS_WITH_FIX` 우회가 분리돼 있고 artifact별 threshold profile은 없다 |
| salience 관리 | SC-0~6 Smart Context Retrieval | `modules/core/stage4_context_builder.py:329-383`, `tests/test_sc6_observability.py` | 부분 완료 | retrieval 우선순위와 예산 추적은 있으나 dropped-section report와 stage verdict 상관 리포트는 없다 |

## Stage 0

### 현재 상태

- 스타일 추출 샘플링은 이미 크게 확장돼 있다.
  - `MAX_ANALYSIS_CHARS = 1_000_000`
  - 5분할 샘플링
  - `batch_size=10000`, `num_batches=6` 기반 2회 LLM 심층 분석
  - `reference_excerpt` 50,000자 생성
- 투자물 장르에 대한 문장/문단 스코어링 분기가 이미 들어가 있다.
- 레퍼런스 변경 시 `mtime` 기반 캐시 무효화도 구현돼 있다.

### 확인된 병목

| 항목 | 확인 근거 | 리스크 | 개선 방향 | 신뢰도 |
| --- | --- | --- | --- | --- |
| 레퍼런스 입력 계약 부재 | `load_reference_manuscripts()`는 폴더 내 `*.txt`를 전부 합산 로드 | 잘못 들어온 파일, 편향된 작품 비중, 중복 원고가 그대로 품질 상한을 결정 | 레퍼런스 manifest 도입: 기대 작품 수, 화수, 가중치, 제외 규칙, 중복 검사 | 높음 |
| 상위 점수 위주 큐레이션 편향 | `_curate_samples()`가 상위 문장 50개/대화 30개/문단 15개를 단순 정렬 | 특정 국소 패턴이 과대표집될 수 있음 | 다양성 제약 추가: 작품별 quota, 유사 샘플 클러스터링, 누락 패턴 리포트 | 높음 |
| 결과 설명 가능성 부족 | `StyleGuide`에 분석 버전/출처 수는 있으나 confidence·편향 경고 없음 | Stage 4 주입 전 “이 guide를 얼마나 믿어야 하는지” 알기 어려움 | `analysis_confidence`, `source_balance`, `cache_reason`, `warning_flags` 추가 설계 | 중간 |

### Stage 0 개선 방향

1. 레퍼런스 폴더를 “파일 저장소”가 아니라 “검증된 스타일 자산”으로 승격해야 한다.
2. 샘플량을 더 늘리는 것보다, 어떤 작품/구간이 추출 결과를 지배했는지 보여주는 편이 효과가 크다.
3. Style Guide를 단일 텍스트가 아니라 “근거가 보이는 진단 결과”로 다뤄야 Stage 4 튜닝이 쉬워진다.

## Stage 1

### 현재 상태

- `main_a.py:2486-2488`은 thin delegate이고, 실제 Stage 1 본체는 `modules/core/stage01_helpers.py:499-689`에 있다.
- Stage 1은 optional처럼 보이지만 실제로는 강한 품질 게이트가 있다.
  - 시작부 수동 스킵 분기: `modules/core/stage01_helpers.py:508-514`
  - `plot_roadmap` 복구 경로: `modules/core/stage01_helpers.py:532-547`
  - `retry_with_feedback()` + `RetryLimits.DIRECTOR_MAX_ATTEMPTS=10`: `modules/core/stage01_helpers.py:639-645`, `modules/core/constants.py:109-113`
  - `strategy_doc >= 2000자` + `_validate_volume_boundaries()`: `modules/core/stage01_helpers.py:614-623`, `main_a.py:2606-2641`
- 다운스트림의 실제 소비 계약은 생각보다 얕다.
  - Stage 2는 `vol_no`, `strategy_doc` 중심으로만 읽는다: `modules/core/stage2_orchestrator.py:440-442`
  - Analyst는 누락된 `strategy_doc`를 `tactical_doc`로 자동 보정한다: `modules/domain/agents/analyst.py:208-209`

### 확인된 병목

| 항목 | 확인 근거 | 리스크 | 개선 방향 | 신뢰도 |
| --- | --- | --- | --- | --- |
| 문서 공백 | `docs/stage_map/stage1.md`가 템플릿 상태이고, 실제 로직은 `modules/core/stage01_helpers.py:499-689`에 몰려 있다 | 운영자가 Stage 1을 “없거나 가벼운 단계”로 오인하기 쉽다 | Stage 1 stage map을 실제 코드 기준으로 채우고 스킵 정책을 명문화 | 높음 |
| 수동 스킵 의존 | `modules/core/stage01_helpers.py:508-514`에서 `input()`으로 진행/스킵 선택, `main_a.py:2154-2155`에도 별도 skip confirm이 있다 | 프로젝트마다 Stage 1 활용 정도가 들쭉날쭉해질 수 있음 | 장르/프로젝트 규모/기존 anchor 상태 기반의 skip policy 표준화 | 높음 |
| 재시도는 있으나 피드백은 비어 있음 | `retry_with_feedback()`는 구조화돼 있으나 `_vol_on_failure()`가 빈 문자열을 반환한다 (`modules/core/stage01_helpers.py:635-645`). `adaptive_retry.py:822-858` 기준 다음 시도는 빈 `feedback`으로 호출돼 사실상 기본 프롬프트를 재사용한다 | 재시도가 “같은 요청 반복”으로 흐를 수 있어 Stage 1 품질 상한이 낮아진다 | Stage 1도 최소한 `boundary violation`, `density 부족`, `plot_roadmap 결손` 유형별 feedback packet을 남기게 설계 | 중간 |
| 다운스트림 계약이 약함 | Stage 2는 `volumes_strategy`에서 사실상 `vol_no`, `strategy_doc`만 읽고 (`modules/core/stage2_orchestrator.py:440-442`), Analyst가 누락 필드를 자동 보정한다 (`modules/domain/agents/analyst.py:208-209`) | 권별 전략이 이후 Stage 2~4에 얼마나 강하게 반영되는지 일관성이 약할 수 있음 | `volumes`에 `theme`, `must_payoff`, `forbidden_regression`, `risk_flags` 같은 최소 공통 contract를 정의 | 높음 |

### Stage 1 개선 방향

1. Stage 1은 “있으면 좋은 단계”가 아니라, 장기 품질의 상한을 정하는 구조 단계라는 점을 문서와 UI에 동시에 명확히 해야 한다.
2. 스킵 허용 조건을 장르별로 분리해야 한다. 특히 장기 연재형 구조물은 Stage 1 스킵 비용이 크다.
3. 권 단위 전략의 핵심 목표를 Stage 2/4가 읽기 쉬운 표준 필드로 고정하고, 재시도 피드백도 같은 스키마를 쓰게 해야 한다.

## Stage 2

### 현재 상태

- Preflight, validation pipeline, director finalizer가 분리돼 있고 검증 체인이 가장 촘촘하다.
- Flow Guard, Duplicate Guard, DraftValidator, ContinuityInspector, PASS_WITH_FIX loop, QualityGate가 모두 있다.
- Stage 3→2, Stage 4→2 역방향 피드백도 이미 주입한다.

### 확인된 병목

| 항목 | 확인 근거 | 리스크 | 개선 방향 | 신뢰도 |
| --- | --- | --- | --- | --- |
| patch/rewrite 라우팅이 전역 점수 경계에 강하게 묶임 | `stage2_preflight.py`, `stage2_finalizer.py`에서 `PatchModeThresholds.REWRITE`, `fix_scope` fallback 사용 | Arc 품질과 Arc 수정 가능성이 동일 점수 축으로 합쳐짐 | Arc 전용 patchability score와 final quality score를 분리 | 높음 |
| Reject가 advisory로 많이 전환됨 | `stage2_validation_pipeline.py`의 consensus/flow/duplicate/continuity 경로 | Director 주권은 지키지만, 경고가 많아질수록 원인 우선순위가 흐려질 수 있음 | advisory packet 구조화: `owner`, `severity`, `must_fix`, `evidence` 필드 강제 | 높음 |
| 수동 개입 메뉴 | `stage2_orchestrator.py`의 `1 skip / 2 stop / 3 auto retry / 4 manual intervention` | 운영자 숙련도 차이가 결과 일관성을 깨뜨릴 수 있음 | interactive menu를 실행 정책으로 추출하고 선택 결과를 audit log에 정규 저장 | 높음 |
| retry 시 context 축소 정책이 정성적 | `modules/core/stage2_preflight.py:539-597`의 `[V60.21] Focus Mode`가 retry 시 `current_feedback + preserved_constraints + minimal_prev_context`로 `enhanced_context`를 재구성한다 | 지나친 축소 또는 불균형 축소가 원인 해결보다 정보 손실을 만들 수 있음 | retry context에 대한 A/B 측정 기준 수립: 통과율, 평균 점수, reject bucket 분포 | 중간 |

### Stage 2 개선 방향

1. Stage 2는 가드가 부족한 단계가 아니라, 가드와 정책이 서로 얽혀 있는 단계다.
2. 향후 개선은 검증기 추가보다 “어떤 reject를 누가 바로 고쳐야 하는지”를 더 선명하게 만드는 방향이 맞다.
3. Arc 생성 실패의 수동 처리 흐름은 유지하더라도, 선택 근거가 구조화돼야 품질 회고가 가능하다.

## Stage 3

### 현재 상태

- 이전 Blueprint 누락 시 강제 중단하는 연속성 게이트가 있다.
- Semantic context, Treatment block, timeline markers, 최근 원고, prev HUD가 모두 주입된다.
- `max_retries=9`로 총 10회 시도하며, `quality_gate_score=90` 기준 PASS 재평가가 있다.
- `_stage3_meta`에 `final_verdict`, `quality_gate_failed`, `quality_risk`, `last_score`를 저장한다.

### 확인된 병목

| 항목 | 확인 근거 | 리스크 | 개선 방향 | 신뢰도 |
| --- | --- | --- | --- | --- |
| 문서-런타임 드리프트 | `docs/stage_map/stage3.md:15,85,92`와 실제 코드(`modules/core/stage3_orchestrator.py:768`, `modules/domain/agents/three_phase_blueprint_generator.py:418,436-444`)의 retry/gate/fallback 설명 차이 | 운영/감리 문서가 잘못된 기준으로 논의될 수 있음 | Stage 3 stage map 재작성: retry=10회, gate=90, degraded fallback 조건 명시 | 높음 |
| degraded fallback의 의미가 강하지만 이름은 약함 | `PASS_WITH_WARNING`, `quality_risk=True` 경로 존재 | “일단 통과”가 아니라 “리스크를 안고 통과”인데 후속 단계에서 다르게 취급되지 않을 수 있음 | degraded blueprint를 정식 상태로 분리하고 Stage 4/UI/로그에서 더 강하게 표시 | 높음 |
| Blueprint도 전역 임계치 논리에 묶임 | `PatchModeThresholds.REWRITE`, `quality_gate_score` 재사용 | Arc/Blueprint/Manuscript 간 artifact 차이가 임계치에 반영되지 않음 | Blueprint 전용 threshold set 분리, patchability와 publishability 분리 | 높음 |
| 문맥 증량보다 salience 문제가 더 큼 | 최근 원고, semantic context, timeline이 이미 풍부하게 주입됨 | 더 많은 문맥 추가는 비용만 늘리고 품질 이득이 제한될 수 있음 | 어떤 컨텍스트가 실제 통과에 기여하는지 stage_attempt 데이터로 역분석 | 중간 |

### Stage 3 드리프트 대비표

| 항목 | `stage3.md` 기재값 | 실제 코드값 | 파일:라인 |
| --- | --- | --- | --- |
| `max_retries` | `4` (총 5회) | `9` (총 10회) | `modules/core/stage3_orchestrator.py:768` |
| `quality_gate_score` | `80` | `90` | `modules/domain/agents/three_phase_blueprint_generator.py:418` |

같은 계열의 문서 드리프트로 `docs/stage_map/stage1.md`도 여전히 빈 템플릿 상태다. 따라서 `P0-1 stage map 재동기화`는 추상 권고가 아니라, 위 대비표와 Stage 1 공백 자체를 근거로 한 즉시 작업 항목이다.

### Stage 3 개선 방향

1. Stage 3의 핵심 이슈는 “문맥 부족”보다 “fallback 의미 관리”다.
2. `quality_risk`는 이미 좋은 신호이므로, 이 값을 이후 단계의 강한 정책 신호로 승격하는 것이 맞다.
3. Stage 3 문서는 구현보다 뒤처져 있으므로 우선 문서 동기화가 필요하다.

## Stage 4

### 현재 상태

- mandatory context는 world state, fact ledger, canonical facts, genre_ext, state summaries, vector retrieval, lookback, foreshadow, semantic guard, pacing, future arc context까지 폭넓게 수집한다.
- Preflight advisory, CoVe fail-closed 검증, PASS_WITH_FIX 재심사, blueprint escalation, operator handoff가 이미 있다.
- Stage 3 `quality_risk`를 받아 escalation threshold를 낮추는 연결도 구현돼 있다.

### 확인된 병목

| 항목 | 확인 근거 | 리스크 | 개선 방향 | 신뢰도 |
| --- | --- | --- | --- | --- |
| mandatory_context의 salience 관리 부족 | `modules/core/stage4_context_builder.py:329-383,1257-1265`, `modules/core/context_advisor.py:130-153` 기준으로 다수 블록을 누적한 뒤 예산 적용 | 좋은 문맥은 많지만, 무엇이 최우선인지 불투명할 수 있음 | section별 priority score, dropped-section report, `llm_calls.prompt_chars` 및 trim 로그와 Stage 4 합격률 상관 분석 도입. 현재 상태: 실측 대기 | 중간 |
| 라운드 소진 후 handoff가 사람 의존 | `stage4_orchestrator.py`의 `최선 결과물로 진행 / 건너뛰기`, “인간 검토 필요” 경로 | 마지막 판단이 운영자 직감에 의존할 수 있음 | handoff packet 표준화: unresolved issues, last best score, blueprint risk, 추천 액션 | 높음 |
| degraded blueprint 경고가 강한 정책 신호로 완전히 승격되진 않음 | `quality_risk`는 escalation threshold에만 반영 | Blueprint 리스크가 Manuscript 단계 품질 전략 전체를 충분히 바꾸지 못할 수 있음 | `quality_risk` 기반으로 context priority, retry budget, final logging을 차등화 | 중간 |
| 사용자에게 보이는 “왜 실패했는가” 정보가 분산 | preflight advisory, Director feedback, CoVe 경고가 서로 다른 경로 | 품질 개선 회고와 운영 판단이 어려움 | Stage 4 실패 요약의 단일 스키마 정의: 원인, 증거, 수정 책임자, 재시도 추천 여부 | 높음 |

### Stage 4 개선 방향

1. Stage 4는 컨텍스트를 더 넣는 것보다, 중요한 컨텍스트를 앞세우고 덜 중요한 컨텍스트를 설명 가능하게 버리는 쪽이 맞다.
2. 사람에게 넘길 때는 “원고를 살릴지 버릴지”만 묻지 말고, 왜 그런 선택을 해야 하는지 기계가 먼저 정리해 줘야 한다.
3. Stage 3의 `quality_risk`가 Stage 4 운영 전략 전체를 바꾸는 핵심 스위치가 되도록 설계를 정리할 필요가 있다.

### 실측이 필요한 가설과 검증 경로

- `advisory 과다 누적`
  - 현행 저장 근거: `modules/core/db_manager.py:511-527`, `modules/core/db_manager.py:2539-2568`
  - SQL 예시:
    ```sql
    SELECT
        verdict,
        AVG((SELECT COUNT(*) FROM json_each(COALESCE(advisory_flags, '{}')))) AS avg_advisory_flags,
        COUNT(*) AS sample_count
    FROM stage_attempts
    WHERE stage IN (2, 4)
    GROUP BY verdict;
    ```
  - 또는 `modules/core/failure_analyzer.py:241-301`의 `advisory_reject_correlation()` 사용
  - 현재 상태: 실파이프라인 실측 데이터 미수집
- `salience 관리 부족`
  - 현행 로그 근거: `modules/core/stage4_context_builder.py:348-383`의 `[SC] Context budget`, `[SC:TRIM]`
  - 검증 방법: mandatory context 블록별 크기 로그를 별도 저장한 뒤 `llm_calls.prompt_chars`/`stage_attempts.verdict`와 상관 분석
  - 현재 상태: 블록별 크기 DB 적재가 없어 실측 대기

## 장기 기억 감사 (200화 관점)

### 조사 범위

- 장기 기억 저장소와 투입 경로를 별도 3회 재점검했다.
  - 저장 계층: `modules/core/world_state.py`, `modules/core/fact_ledger.py`, `modules/domain/agents/state_tracker.py`, `modules/domain/agents/state_tracker_plots.py`, `modules/core/vec_memory.py`, `modules/core/reference_anchor.py`
  - 주입 계층: `modules/core/stage4_context_builder.py`, `modules/domain/agents/chief_writer_context.py`, `main_a.py`
  - 회귀 방어 확인: `tests/test_stage4_context_builder.py`, `tests/test_vec_memory.py`, `tests/test_state_tracker.py`
- 이번 섹션은 “장기 기억이 아예 없는가”가 아니라, “200화 시점에도 저장된 기억이 필요한 순간에 충분한 해상도로 노출되는가”를 기준으로 판단했다.

### 장기 기억 SSOT 구분

| 문서 | SSOT 범위 | 본 문서와의 관계 |
| --- | --- | --- |
| `docs/2026-03-09/context-window-utilization-audit.md` | 토큰 예산, 하드캡, Tier별 용량, LM-P/LM-F 수치 제안 | 예산 데이터와 과거 cap 제안의 참고 문서로만 사용 |
| `docs/2026-02-28/long-term-memory-evaluation.md` | 50/100/200화 시나리오별 기억 내구성 평가 | 과거 기준점 참고용 |
| `본 문서의 장기 기억 섹션` | projection, salience, retrieval, observability 정책 개선 방향 | 장기 기억 운영 정책의 SSOT |

### 기존 장기 기억 문서와의 대응표

| 이전 문서 항목 | 이전 제안 요지 | 본 문서 대응 | 관리 기준 |
| --- | --- | --- | --- |
| `LM-P1` | Tier 2 화별 요약 확대 | `continuity packet`보다 recent summary tier를 어디에 쓰는지 분리 | cap 상세는 해당 문서, 운영 방향은 본 문서 |
| `LM-P2` | Tier 3 Arc 요약 확대 | 저장된 상위 요약 자산과 주입 정책의 비대칭 해소 | 본 문서에서 통합 관리 |
| `LM-P3` | NPC 관계 이력 확대 | `NPC/관계 지목형 retrieval` + continuity packet | 본 문서에서 통합 관리 |
| `LM-P4` | NPC 속성 이력 추가 | `VecMemory 메타데이터 설명력` + 엔티티 이력 retrieval | 본 문서에서 통합 관리 |
| `LM-P5` | 타임라인 세부 확대 | continuity packet 내 timeline slot 분리 | 본 문서에서 통합 관리 |
| `LM-P6` | Volume/Series 요약 전체 노출 | `summary asset 사용 계약`과 Stage 4 주입 규칙 동기화 | 본 문서에서 통합 관리 |
| `LM-P7` | Extended lookback 총량 확대 | recent bridge용 lookback과 long retrieval를 분리 | 해당 문서가 cap 상세, 본 문서는 방향만 |
| `LM-F1` | 남은 EP scenario 확대 | `future intent seed`와 현재 Arc 잔여분을 분리 | 해당 문서가 상세, 본 문서는 방향만 |
| `LM-F2` | 다음 Arc tactical 확대 | `다음 Arc 상세 + 그 이후 희미한 방향성` 이원화 | 해당 문서가 상세, 본 문서는 방향만 |
| `LM-F3` | 다음 Arc beats 전량 노출 | low ROI 후보로 유지 | 해당 문서가 상세, 본 문서는 방향만 |
| `LM-F4` | Arc N+2 가시성 추가 | `Arc N+2 / volume intent` seed 설계 | 본 문서에서 통합 관리 |
| `LM-F5` | `vol_strategy` Stage 4 전달 | Stage 1~4 계약과 summary asset 사용 정책 정리 | 본 문서에서 통합 관리 |

### 현재 구조 요약

| 계층 | 현재 구현 | 200화 관점 해석 |
| --- | --- | --- |
| 영구 상태 | `WorldState`, `FactLedger`, `StateTracker`가 NPC/관계/플롯/시간선/아이템/수치 이력을 장기 보존 | 저장 자체는 비교적 강하다 |
| 계층형 요약 | `prepare_episode_context()`가 Tier 1(최근 30화 전문), Tier 2(31~60화 요약), Tier 3(60화 이전 Arc 요약), Tier 4(장기 앵커)를 조립 | 장기 기억 계층은 이미 존재한다 |
| 검색형 기억 | `VecMemory` hybrid retrieval, `ReferenceAnchor`, narrative/series/volume summary | 장기 회수 경로도 복수로 존재한다 |
| 실제 병목 | prompt 투입 시 상위 N/최근 N/요약 캡이 반복 적용됨 | 저장 대비 노출 밀도가 장편에서 평평해진다 |

### 확인된 장기 기억 병목

| 항목 | 확인 근거 | 200화 리스크 | 개선 방향 | 신뢰도 |
| --- | --- | --- | --- | --- |
| 저장 대비 prompt-visible projection 상한 | `world_state.py`의 `get_summary()`는 생존 NPC 30, 사망 20, 관계 20, 아이템 20, 타임라인 최근 5만 노출. `fact_ledger.py`의 `to_summary()`는 인물 30, 보유 아이템 20, 장소/조직 10, 수치 15만 노출. `state_tracker_plots.py`는 완결 플롯 30, 시간 마커 20만 요약 | 저장은 남아 있어도 프롬프트에는 최근/상위 항목만 반복적으로 보여 장기 인과가 흐려질 수 있음 | 전역 cap 확대보다 salience 기반 continuity packet, 엔티티/플롯 지목형 retrieval로 전환 | 높음 |
| 확장 lookback의 범위가 좁고 발췌 기반 | `build_extended_lookback_digest()`는 `ep-10 ~ ep-4`만 보며 화당 발췌와 총량 cap을 둠 | 4~10화 브리지는 보완되지만, 장기 회수 자체를 대체하지는 못함 | 최근 회수용 lookback과 장기 회수용 retrieval를 분리해 설계 | 높음 |
| 미래 계획 노출 범위가 얕음 | `_build_future_arc_context()`는 현재 Arc 잔여분과 다음 Arc 1개만 노출하고, 시나리오/긴장/전술 문서를 짧게 절삭 | 100~200화 구간의 장거리 복선, 후반 회수, 볼륨 단위 방향 정렬이 약해질 수 있음 | 다음 Arc 상세와 별도로 Arc N+2 또는 volume intent를 저비용 힌트로 분리 | 높음 |
| VecMemory 메타데이터 절삭 | `vec_memory.py`의 `memorize_v20_episode()`는 summary 1000자, causal 2000자, event_types 500자, entity_names 1000자로 저장 | 오래된 화일수록 retrieval 후보에 붙는 설명력이 얕아져 “찾아와도 왜 중요한지”가 약해질 수 있음 | summary slot 구조 강화, 엔티티/이벤트 필드 정규화, alias 대응 강화 | 높음 |
| 저장된 계층형 요약과 런타임 사용 정책의 비대칭 | `main_a.py`의 `_load_narrative_summaries()`는 5화 단위 요약과 시리즈/최대 20개 볼륨 요약을 폭넓게 로드하지만, `stage4_context_builder.py`는 현재 볼륨 기준 직전 2개까지만 붙임 | 이미 생성한 상위 요약 자산이 장편 런타임에서 충분히 활용되지 않을 수 있음 | 저장 정책과 주입 정책을 같은 기준으로 맞추고, 왜 제외됐는지 표시 | 중간 |
| Writer 보조 헬퍼의 recent window가 짧음 | `chief_writer_context.py`의 `_extract_recent_events()`는 기본 3화, 최대 5개 이벤트만 반환 | Stage4 hybrid tier보다 보조 힌트 창이 더 짧아 helper 계층에서 기억 비대칭이 생길 수 있음 | Writer helper도 Stage4 tier 정책과 맞춰 recency/salience를 분리 | 중간 |

### 200화 내구성 강화 아이디어

1. `continuity packet` 계층을 별도로 두는 편이 ROI가 높다.
   `WorldState`, `FactLedger`, `StateTracker` 전체를 평평하게 붙이기보다, 현재 화와 직접 관련된 인물/조직/아이템/플롯만 “절대 잊으면 안 되는 사실” 패킷으로 압축해 주입하는 방식이 더 효과적이다.
2. 미해결 플롯과 관계 변화는 `요약 상위 N`보다 `지목형 retrieval`이 맞다.
   현재 화 Blueprint나 Arc 문서에 등장한 인물/플롯명을 기준으로 DB history를 다시 읽어 오는 쪽이 200화에서 더 안정적이다.
3. 미래 기억은 `다음 Arc 상세 + 그 이후 희미한 방향성`으로 이원화해야 한다.
   다음 Arc는 지금처럼 상세하게 두되, 그다음 Arc나 볼륨 단위 의도는 짧은 seed 형태로 유지하는 편이 장거리 회수와 복선 안정성에 유리하다.
4. VecMemory는 저장 건수보다 `메타데이터 설명력`이 중요하다.
   요약 4-slot, 엔티티 alias 정규화, 사건/결말/장소 분리처럼 검색 후 설명 가능한 메타를 늘리는 쪽이 단순 result 수 확대보다 낫다.
5. 장기 기억은 스테이지별로 다른 모드가 필요하다.
   Stage 3은 구조 연속성, Stage 4는 문장 단위 회수와 금지 사실을 우선해야 하므로 같은 cap을 키우는 방식보다 stage-specific memory profile이 적합하다.
6. 사용자와 운영자에게 기억 사용 현황을 보여 줘야 한다.
   어떤 continuity packet이 선택됐는지, 어떤 장기 기억이 예산 때문에 빠졌는지, retrieval가 어떤 과거 화를 근거로 했는지를 로그/리포트로 노출해야 장편 튜닝이 가능하다.

### 추가 조사로 남긴 전반 개선 아이디어

| 항목 | 확인 근거 | 리스크 | 개선 방향 | 신뢰도 |
| --- | --- | --- | --- | --- |
| 내러티브 요약 로더의 하드코딩 상한 | `main_a.py`의 `_load_narrative_summaries()`가 `range(5, 500, 5)`와 볼륨 20개 상한을 사용 | 200화는 버티지만, 장기 운영 관점에서는 구조적 상한이 코드에 박혀 있음 | DB 존재 구간 기반 로드 또는 설정 기반 상한으로 전환 | 높음 |
| 저장된 상위 요약 자산과 Stage 4 주입 규칙의 정책 분리 | 시리즈/볼륨/5화 요약은 넓게 생성되지만 실제 mandatory context는 현재 볼륨 인접 구간만 우대 | 자산 생성 비용과 실제 활용 정책이 따로 놀 수 있음 | 요약 자산의 사용 계약을 Stage 4 주입 정책과 같이 정의 | 중간 |
| 장기 기억 회수 품질의 가시성 부족 | retrieval, lookback, 요약 블록은 많지만 “이번 화에서 무엇이 선택됐고 무엇이 탈락했는지”를 한 번에 보여 주는 단일 리포트는 약함 | 실제 품질 병목이 저장 부족인지 선택 실패인지 구분하기 어려움 | long-memory observability 리포트와 회수 실패 케이스 로그를 별도로 설계 | 높음 |

## 3pass 감리 후 제외한 오탐 후보

아래 항목은 처음엔 문제 후보였지만, 재검증 후 “주요 개선안”에서 제외했다.

| 제외 항목 | 제외 이유 |
| --- | --- |
| “Stage 0은 분석량이 너무 적다” | 현재 구현은 이미 100만자 샘플, 5분할, 6배치, 2회 분석, 50K excerpt까지 확장돼 있음 |
| “Stage 1은 품질 게이트가 없다” | 실제 코드는 retry, 길이 체크, boundary validation, 실패 시 중단을 모두 수행함 |
| “Stage 2는 검증 체인이 약하다” | 실제로는 가장 촘촘한 검증 체인을 보유. 문제는 검증 부족보다 signal routing과 manual policy임 |
| “Stage 3은 quality gate가 없다” | `PASS`에 대해 90점 gate가 존재함. 핵심 이슈는 degraded fallback 의미 관리와 문서 불일치 |
| “Stage 4 CoVe는 fail-open이다” | quick_verify/LLM verify 예외와 치명 모순 모두 REJECT로 전환하는 fail-closed 경로가 구현돼 있음 |
| “장기 기억 레이어가 부족하다” | `WorldState`, `FactLedger`, `StateTracker`, Tier1~4 hybrid context, narrative summary, vec retrieval이 이미 깔려 있음. 병목은 부재보다 투영/선택 정책임 |
| “Stage 4는 60화 이후 과거를 거의 못 본다” | 실제로는 최근 30화 전문, 31~60화 요약, 그 이전 Arc 요약, 장기 앵커가 모두 주입됨. 문제는 salience와 활용 정책이다 |
| “해결책은 context cap을 전역으로 키우는 것뿐이다” | 기존 코드도 이미 50K/25K/장기 요약 등 큰 블록을 보유한다. 더 중요한 것은 어떤 블록을 남기고 버릴지 설명 가능하게 만드는 일이다 |
| “ReferenceAnchor cap이 주병목이다” | `reference_anchor.py`는 1000개 보존과 critical type 보존을 수행한다. 200화 내구성의 일차 병목은 이보다는 projection 평탄화에 가깝다 |
| “자동화 브리지가 없다” | `process_runner.py`, `prompt_broker.py`, `bridge_server.py` 기준으로 입력 브리지와 timeout/default 계약은 이미 있다. 문제는 부재보다 정책화 수준이다 |
| “관측 가능성이 거의 없다” | `quality_dashboard.py`, SC-6 observability, retrieval/perf log는 이미 있다. 핵심 부족은 단일 실패 이유/trim 근거의 통합 리포트다 |

### 역방향 오탐 검토

- 이번 3pass는 주로 `X가 없다 → 실제로는 이미 있다` 유형의 부재 오탐을 우선 제거했다.
- 반대 방향인 `X가 있다 → 실제로는 미작동/미배선이다` 유형도 범위 밖으로 무시한 것은 아니다.
- dead code / dead feature 계열은 별도 전수조사에서 이미 반복 점검됐다 (`docs/2026-03-02/system-evaluation.md:184-193`, `docs/2026-02-23/opus_tf7_system_audit_order.md:351-356`).
- 후속 감리에서 계속 볼 역방향 후보는 `문서에는 있으나 런타임에 반영되지 않는 설정`, `UI/bridge에 노출되지만 실제 파이프라인에서 소비되지 않는 옵션`이다.

## 우선순위 제안

### P0

1. stage map 재동기화
   - 관련 코드: `modules/core/stage01_helpers.py:499-689`, `modules/core/stage3_orchestrator.py:768`, `modules/domain/agents/three_phase_blueprint_generator.py:418`
   - Stage 1 실제 동작 문서화와 Stage 3 retry/gate/fallback 문서화를 한 세트로 묶는다.
   - 구체 근거:
     - `docs/stage_map/stage1.md`는 빈 템플릿 상태
     - `docs/stage_map/stage3.md`는 `max_retries=4`, `quality_gate_score=80`로 기록돼 있지만 실제 코드는 `9 / 90`
2. interactive policy 분리
   - 관련 코드: `modules/core/stage01_helpers.py:508-514`, `modules/core/stage2_orchestrator.py:793-838`, `modules/core/stage4_orchestrator.py:1109-1123`
   - Stage 1 skip, Stage 2 failure menu, Stage 4 best-manuscript handoff를 공통 정책 객체로 추출한다.
   - 최소 필드 초안: `policy_id`, `allowed_actions`, `default_action`, `timeout_action`, `audit_reason`
3. artifact별 threshold profile 설계
   - 관련 코드: `modules/core/constants.py:633-645`, `modules/core/stage2_finalizer.py:515-720`, `modules/domain/agents/three_phase_blueprint_generator.py:418-538`
   - 현재 공유 임계값:
     - `PatchModeThresholds.REWRITE=50`
     - `PatchModeThresholds.INPLACE=60`
     - `quality_gate_score=90`
   - 초안 스키마:
     ```yaml
     threshold_profiles:
       arc:
         patch_rewrite_below: 45
         patch_inplace_below: 55
         quality_gate_target: 88
         enforcement: advisory_only
       blueprint:
         patch_rewrite_below: 50
         patch_inplace_below: 60
         quality_gate_target: 90
         degraded_band: [80, 89]
         enforcement: advisory_only
       manuscript:
         patch_rewrite_below: 60
         patch_inplace_below: 70
         quality_gate_target: 92
         enforcement: advisory_only
     ```
   - 현행 공유값 대비 diff:

     | artifact | rewrite_below | inplace_below | quality_gate | 공유값 대비 해석 |
     | --- | --- | --- | --- | --- |
     | Arc | `45` | `55` | `88` | `50/60/90` 대비 `-5/-5/-2` |
     | Blueprint | `50` | `60` | `90` | 공유값 유지 + `degraded_band`만 추가 |
     | Manuscript | `60` | `70` | `92` | `50/60/90` 대비 `+10/+10/+2` |
   - 분리 후보 해석:
     - Arc `patch_rewrite_below=45`: 현행 `50` 공유값보다 5점 낮춘 시험값이다. Arc는 tactical coherence 중심이라 구조 재생성 비용이 manuscript보다 낮다.
     - Arc `patch_inplace_below=55`: 현행 `60`보다 5점 낮춰, 애매한 저점 Arc를 국소 패치보다 재생성 쪽으로 더 빨리 보낸다.
     - Arc `quality_gate_target=88`: publishability보다 구조 일관성이 우선인 산출물이므로 현행 `90`보다 2점 완화 시험이 가능하다.
     - Blueprint `degraded_band=[80,89]`: `quality_gate=90`은 유지하되, hard reject와 degraded handoff를 분리하기 위한 상태 밴드를 명시한다.
     - Manuscript `patch_rewrite_below=60`: 현행 `50`보다 10점 높인 시험값이다. 최종 노출물은 저점 상태에서 `previous_best` 보존보다 전면 재작성 쪽이 안전하다.
     - Manuscript `patch_inplace_below=70`: 현행 `60`보다 10점 높여, 최종 노출물의 국소 패치 진입 기준을 더 엄격하게 잡는다.
     - Manuscript `quality_gate_target=92`: 현행 `90`보다 2점 높여, 최종 사용자 노출물의 publishability 기준을 별도로 상향한다.
   - 위 수치는 실파이프라인 A/B 실측 후 조정 대상이다.
   - Director 주권 준수 조건:
     - Python은 `routing/advisory`만 생성한다
     - `REJECT`, `PASS`, `PASS_WITH_FIX`, `PASS_WITH_WARNING` 확정은 Director만 수행한다
4. 장기 기억 projection 정책 분리
   - 관련 코드: `modules/core/world_state.py:689-782`, `modules/core/fact_ledger.py:447-520`, `modules/domain/agents/chief_writer_context.py:1153-1185`, `main_a.py:3224-3245`
   - 현재 `WorldState.get_summary()` 노출 상한:
     - 생존 NPC `30`
     - 사망 NPC `20`
     - 관계 `20`
     - 보유 아이템 `20`
     - 진행 중 플롯 `10`
     - 타임라인 최근 `5`
   - continuity packet 후보 필드:
     - 현재 화 Blueprint 등장 엔티티
     - 관련 `FactLedger` 인물/아이템/장소 항목
     - 관련 active/resolved plot
     - 사망 NPC/금지 아이템 같은 hard constraint
     - 현재 화와 직접 연결되는 timeline marker
   - 토큰 예산 초안:
     - 단위는 `토큰` 기준이다.
     - 엔티티 목록 `120~200 tokens`
     - must-hold facts `300~500 tokens`
     - plot obligations `200~300 tokens`
     - timeline + hard constraint `200~300 tokens`
     - 총량 목표 `900~1400 tokens`, hard cap `1800 tokens`
   - 한국어 기준 환산:
     - 한국어 `1 token ≈ 1.5~2자` 가정 시 `900~1800 tokens`는 대략 `1,350~3,600자` 범위다.
   - 현행 `WorldState.get_summary(max_chars=50000)`는 상태량에 따라 길이가 달라지지만 상한이 `50,000자`이고, 한국어 기준 대략 `25K~33K tokens` 규모까지 갈 수 있다 (`modules/core/world_state.py:659-782`).
   - 따라서 continuity packet은 `WorldState.get_summary()`를 대체하는 것이 아니라, 현재 화 관련 고우선 기억만 별도 압축해 Stage 4 projection을 보완하는 층으로 두는 편이 맞다.
   - dropped-memory report와 stage-specific profile은 같은 묶음으로 설계한다.
5. SSOT 동기화 규칙 반영
   - 관련 코드/문서: `README.md:46-52`, `tests/test_pass_with_fix.py:1683-1804`, `docs/stage_map/stage3.md:15,85,92`
   - `코드/테스트/로그/문서` 우선순위와 개선 제안 분류 템플릿을 고정한다.
   - 모든 참고 문서는 `문서 성격(계획/감사/완료 회고)`과 `구현 상태(미착수/부분 완료/완료)`를 함께 표기한다.

### P1

1. Stage 2 advisory packet 표준화
   - 관련 코드: `modules/core/stage2_validation_pipeline.py:279-281`, `modules/core/stage4_interview_round.py:500-534`, `modules/core/stage4_orchestrator.py:612-761`
   - 현재 구조:
     - upstream은 `{"source","severity","message"}`류 dict가 일부 존재
     - downstream은 `[CRITICAL · TruthGate] ...` 같은 flat string으로 수렴
   - 제안 JSON 초안:
     ```json
     {
       "owner": "continuity_inspector",
       "severity": "CRITICAL",
       "must_fix": true,
       "evidence": [
         "duplicate_acquisition: 만년한철검이 이미 ep12에서 획득됨"
       ],
       "source_file": "modules/core/stage2_validation_pipeline.py:856",
       "action_hint": "state transition 정정 후 재심사"
     }
     ```
   - 마이그레이션 경로:
     - 현행 대표 직렬화 지점은 `modules/core/stage4_interview_round.py:517-534`이며, `[CRITICAL · TruthGate] ...`, `[MAJOR · NpcDrift] ...`, `[INFO] ...` 같은 flat string으로 수렴한다.
     - 1단계: 내부 표현을 `dict` 스키마로 통일한다.
     - 2단계: 직렬화 시점에는 flat string 래퍼를 유지해 기존 소비자를 깨지 않게 한다.
     - 3단계: 소비자를 순차 전환한 뒤 최종적으로 structured advisory를 기본 계약으로 승격한다.
   - breaking change 여부:
     - 내부 `dict` 전환 후 `str()`/serializer 래퍼를 두면 하위호환 유지가 가능하므로, 즉시 breaking change로 볼 필요는 없다.
   - 전환 대상 파일:
     - `modules/core/stage2_validation_pipeline.py`
     - `modules/core/stage2_finalizer.py`
     - `modules/core/stage4_interview_round.py`
     - `modules/core/stage4_orchestrator.py`
2. Stage 4 mandatory_context salience/ranking 설계
   - 관련 코드: `modules/core/stage4_context_builder.py:329-383`, `modules/core/stage4_context_builder.py:1257-1265`
   - 필수 출력:
     - section별 `priority_score`
     - trim 전/후 chars
     - dropped section 목록
     - verdict 상관 분석용 `stage_attempt` 연결 키
3. Stage 0 reference manifest + confidence report 설계
   - 관련 코드: `modules/core/stage0/style_extractor.py:380-447`, `modules/core/stage0/style_extractor.py:739-804`
   - 최소 필드: `work_id`, `episode_count`, `weight`, `exclude_patterns`, `source_balance`, `analysis_confidence`
4. degraded 상태(`quality_risk`, `PASS_WITH_WARNING`)의 전 단계 공통 스키마 정의
   - 관련 코드: `modules/domain/agents/three_phase_blueprint_generator.py:656-658`, `modules/core/stage3_orchestrator.py:856-859`, `modules/core/stage4_orchestrator.py:1011-1016`
   - 최소 필드: `stage`, `artifact`, `status`, `reason`, `score`, `must_escalate`, `handoff_hint`
5. 지목형 장기 기억 retrieval 설계
   - 관련 코드: `modules/core/vec_memory.py:737-788`, `modules/core/world_state.py:739-782`, `modules/core/fact_ledger.py:447-520`
   - NPC/관계/플롯/아이템 히스토리 조회와 `Arc N+2/volume intent seed`를 같은 retrieval plan 안에서 다룬다
6. VecMemory 메타데이터 설명력 강화 설계
   - 관련 코드: `modules/core/vec_memory.py:405-443`, `modules/core/vec_memory.py:607-726`
   - `summary slot`, `entity alias normalization`, `causal/event/entity field` 분리를 우선한다
7. 운영 지표 팩 정의
   - 관련 코드: `modules/core/quality_dashboard.py:208-243`, `modules/core/context_advisor.py:140-153`, `modules/core/metrics_collector.py:69-78`
   - `north-star`, `품질/비용/속도`, `long-memory recall`을 같은 회고 표준으로 묶는다

### P2

1. 장르별 golden route 품질 기준 정의
2. stage_attempt/quality_dashboard 기반의 reject 패턴 회고 자동화
3. Stage 0~4 품질 계약을 통합한 운영자용 runbook 정리
4. narrative summary/volume summary 로더의 하드코딩 상한 제거
5. long-memory observability 대시보드 또는 감사 리포트 설계
6. UI 상태 스키마와 운영 프롬프트 계약의 공통화

## 권고 결론

현 시스템은 이미 Stage 2~4에 방어 로직이 많다.  
따라서 다음 품질 상향은 “더 많은 검사기 추가”보다 아래 순서가 더 효과적이다.

1. 정책과 임계치를 artifact별로 분리한다.
2. manual intervention을 기록 가능한 실행 정책으로 바꾼다.
3. advisory와 degraded 상태를 구조화해 오탐과 신호 희석을 줄인다.
4. Stage 0/1 입력 계약과 문서를 정비해 앞단 품질 상한을 올린다.

이 네 축이 정리되면, 현재 구조를 크게 흔들지 않고도 각 스테이지의 실제 품질 편차를 줄일 수 있다.

## 참고 문서

- `docs/2026-03-09/quality-improvement-spec.md`
- `docs/2026-03-09/context-window-utilization-audit.md`
- `docs/2026-02-28/long-term-memory-evaluation.md`
- `docs/2026-03-05/글도비_블록메이커_VertexAI_대량원고_학습전략.md`
- `docs/codex_memory_roi_boost_plan.md`
- `docs/기억 개선 작업.md`
- `docs/2026-03-09/ui-system-audit.md`
- `docs/stage_map/agent_graph.md`
- `docs/implementation/api-contract-v1.yaml`
- `docs/implementation/prompt-map-v1.json`

## 부록

### A. 장르별 대규모 코퍼스 활용 전략 (상업성 관점)

본 감사의 핵심 범위(Stage 0~4 구조/정책 품질)를 벗어나는 참고 자료다. 별도 문서로 분리 검토 가능하다.

#### 3pass 조사 결과

- Pass 1 구조 확인:
  - Stage 0은 이미 장르별 `config/style_references/<genre>`를 읽고 `reference_works`, `reference_excerpt`, 장르별 prompt 섹션까지 생성한다 (`modules/core/stage0/style_extractor.py:48-55`, `modules/core/stage0/style_extractor.py:117-186`, `modules/core/stage0/style_extractor.py:739-818`).
  - 상업성은 이미 품질 체계 안에 있다. `validation.yaml`은 `commercial_appeal=15`를 별도 가중치로 두고, `quality_constitution.py`는 후킹력/클리프행어/보상 타이밍을 명시한다 (`config/settings/validation.yaml:52-58`, `modules/core/quality_constitution.py:139-156`).
- Pass 2 구현 재검증:
  - `DataCollector`는 승인/거절 원고, training pair, JSONL export까지 제공한다 (`modules/core/data_collector.py:18-27`, `modules/core/data_collector.py:68-101`, `modules/core/data_collector.py:183-247`).
  - 다만 현재 리포지토리에서 `DataCollector` 호출 흔적은 자기 파일 내부뿐이라, 프로덕션 파이프라인에 학습 데이터 루프가 실배선된 상태는 아니다.
- Pass 3 오탐 제거:
  - “좋은 작품이 많으면 바로 frontier model fine-tuning이 정답”은 오탐다.
  - “상업성은 문체 모사만 맞추면 해결된다”도 오탐다.
  - “장르 데이터를 한 바구니에 많이 넣을수록 좋다”도 오탐다.

#### 판단 요약

당신이 가진 장르별 수십 편 코퍼스는 분명 큰 자산이다. 다만 이 시스템에서 ROI가 가장 높은 첫 사용처는 `모델 가중치 학습`보다 `장르별 biasing + 평가셋 + preference data`다. 원본 원고가 많다는 사실만으로는 상업성이 올라가지 않는다. 웹소설 상업성은 `장르 문체`, `후킹 패턴`, `보상 간격`, `연재 리텐션`까지 같이 라벨링돼야 품질 개선 레버가 생긴다.

#### 활용 경로별 판단

| 경로 | 가능 여부 | 현재 시스템 적합도 | ROI | 핵심 리스크 | 판단 |
| --- | --- | --- | --- | --- | --- |
| 장르별 inference-time biasing | 가능 | 높음 | 매우 높음 | 작품 수가 늘어도 편향 추적이 없으면 특정 작품 쏠림 | 최우선 |
| 장르별 상업성 평가셋 구축 | 가능 | 높음 | 매우 높음 | “좋은 작품” 기준이 추상적이면 라벨 품질이 흔들림 | 최우선 |
| 승인/거절 기반 preference pair 구축 | 가능 | 중간 | 높음 | 현재 `DataCollector`가 배선되지 않아 수집 자동화가 비어 있음 | P1 |
| Gemini/Vertex 계열 SFT | 가능 | 중간 | 중간 | 원본 원고만으로는 prompt-output pair 품질이 부족 | P2 |
| OpenAI 계열 weight tuning | 부분 가능 | 중간 | 중간 | Frontier 최신 모델 직접 튜닝이 아니라 지원 모델군으로 우회해야 함 | P2 |
| Anthropic 계열 weight tuning | 현재 공개 경로 약함 | 낮음 | 낮음 | 공개 fine-tuning 경로 부재 | 제외 |

#### 상업성 관점에서 권장하는 데이터 설계

1. 장르별로 폴더만 나누지 말고 `manifest`를 둬야 한다.
   - 최소 필드: `genre`, `subgenre`, `era`, `pov`, `tone`, `hook_type`, `ending_type`, `reward_cadence`, `work_weight`, `exclude_patterns`
2. “좋은 작품”을 그대로 학습시키기 전에 `상업성 라벨`을 먼저 붙이는 편이 낫다.
   - 최소 라벨: `opening_hook_strength`, `cliffhanger_strength`, `reward_density`, `dialogue_drive`, `market_novelty`, `bingeability`
3. 장르별 코퍼스는 `문체 자산`과 `구조 자산`으로 분리하는 편이 안전하다.
   - 문체 자산: Stage 0 style extraction, reference excerpt
   - 구조 자산: Arc/Blueprint ending pattern, reward cadence, plot acceleration 패턴
4. training은 “원본 full text 대량 투입”보다 `approved/rejected + feedback + 수정본` pair가 더 낫다.
   - 현재 코드의 `DataCollector.create_training_pair()`와 `export_for_finetuning()`는 이 경로와 맞는다 (`modules/core/data_collector.py:183-247`)

#### 장르 코퍼스 관련 3pass 감리 후 제외한 오탐 후보

| 제외 항목 | 제외 이유 |
| --- | --- |
| “코퍼스가 많으니 지금 바로 frontier 모델 가중치 학습이 최선이다” | 현재 시스템은 inference-time biasing과 평가셋 구축의 ROI가 더 높고, raw manuscript만으로는 supervised pair 품질이 부족하다 |
| “상업성은 문체 모사만 높이면 따라온다” | 현행 품질 체계도 상업성을 `후킹력`, `클리프행어`, `보상 타이밍`으로 따로 본다 |
| “장르 데이터를 전부 합치면 장르 이해가 넓어져 더 좋다” | Stage 0은 현재 폴더 내 txt를 전부 합산 로드하므로, 혼합 코퍼스는 오히려 장르 편향과 작품 쏠림을 키울 수 있다 |
| “Anthropic 최신 모델도 현재 공개 방식으로 weight tuning 가능하다” | 최신 모델 사용은 가능해도, 공개 fine-tuning 경로는 공식 문서상 확인되지 않았다 |
| “GPT-5.4 자체를 바로 fine-tuning하면 된다” | 공식 문서상 GPT-5.4는 distillation/custom models 경로는 있지만, 일반 fine-tuning 지원 모델로 표기되지 않는다 |

### B. 주요 에이전트 LLM 모델 권고 (2026-03-10 공식 문서 재검증)

본 감사의 핵심 범위(Stage 0~4 구조/정책 품질)를 벗어나는 참고 자료다. 별도 문서로 분리 검토 가능하다.

2026-03-10 시점 공식 문서 기준이며, 모델 세대 교체 시 별도 문서로 분리 관리하는 편이 안전하다.

전제:

- provider abstraction, cached context, structured output, tool use, fallback chain이 벤더별로 동등하게 갖춰졌다고 가정한다.
- 다만 현재 구현은 `config/models.yaml:2-40`, `modules/domain/agents/base_agent.py:1599-1814`, `modules/core/metrics_collector.py:69-78` 기준으로 Gemini native 구조다.

#### 벤더별 최신 확인 요약

| 벤더 | 최신 확인 | 캐시/도구 측면 | tuning 측면에서의 해석 |
| --- | --- | --- | --- |
| OpenAI | `GPT-5.4`가 공식 모델로 존재 | 1,050,000 context, cached input, tool use 지원 | `GPT-5.4` 자체보다 `GPT-4.1` 계열 SFT/DPO, `o4-mini` RFT가 현실적인 튜닝 경로 |
| Anthropic | `Claude Sonnet 4.6`, `Claude Opus 4.6`가 공식 모델로 존재 | prompt caching, extended thinking, 1M beta context | 최신 추론 모델은 강하지만 공개 fine-tuning 경로는 확인되지 않음 |
| Google | 현재 시스템과 가장 잘 맞는 `Gemini 2.5 Pro/Flash` 중심 | 현재 코드가 Gemini cache path와 fallback에 밀착 | Vertex AI supervised tuning 경로가 가장 곧바로 이어진다 |

#### 현 구조 유지 시 권고

| 역할 | 1순위 (현 구조 친화) | Gemini 외 대안 | 판단 근거 |
| --- | --- | --- | --- |
| Director | `Gemini 2.5 Pro` | `GPT-5.4`, `Claude Opus 4.6` | 최종 판정은 긴 컨텍스트, 구조화 응답, 고비용 reasoning에 유리한 상위 모델이 맞다. 다만 현재 캐시 경로는 Gemini에 가장 밀착돼 있다 |
| Chief Writer | `Gemini 2.5 Pro` | `Claude Sonnet 4.6`, `GPT-5.4`, `GPT-4.1` | 장문 mandatory context와 style/reference excerpt를 함께 다루므로 long-context 안정성이 중요하다 |
| Stage 3 Blueprint Generator | `Gemini 2.5 Pro` | `GPT-5.4`, `Claude Sonnet 4.6` | Blueprint는 구조 reasoning과 retry loop 내 일관성이 핵심이라 상위 reasoning 모델이 유리하다 |
| Analyst / Arc Generator | `Gemini 2.5 Pro` | `GPT-5.4`, `Claude Sonnet 4.6` | Arc/Volume 설계는 장문 reasoning이 필요하지만 final prose quality보다 비용 효율도 중요하다 |
| Manager / Preflight / Lightweight Validator | `Gemini 2.5 Flash` | `GPT-5 mini`, `GPT-4.1 mini` | 현재 구조상 저지연/저비용 validator는 Flash 계열이 가장 자연스럽다. 비-Gemini는 provider abstraction 뒤에만 검토 가치가 있다 |

#### 멀티벤더 패리티까지 완료됐을 때의 권고

| 역할 | 추천 후보군 | 비고 |
| --- | --- | --- |
| Director | `GPT-5.4`, `Claude Opus 4.6`, `Gemini 2.5 Pro` | 고난도 최종 판정과 장문 비교 심사 |
| Chief Writer | `Claude Sonnet 4.6`, `GPT-5.4`, `Gemini 2.5 Pro` | 장문 생성 안정성과 문체 재현력의 균형 |
| Blueprint / Analyst | `GPT-5.4`, `Claude Sonnet 4.6`, `Gemini 2.5 Pro` | 구조 reasoning과 consistency 우선 |
| 경량 Validator | `Gemini 2.5 Flash`, `GPT-5 mini`, `GPT-4.1 mini` | 속도/비용 우선 |

정리:

- `가장 안전한 기본안`은 여전히 Gemini 중심이다. 현재 코드가 이미 Gemini cache path와 fallback 체인에 묶여 있기 때문이다.
- 다만 지난 버전 문서의 `GPT-5.4 미기재`, `Claude 4.6 미기재`는 최신 공식 문서 기준으로 갱신돼야 하는 항목이었다. 현 시점에는 이 모델들을 대안 후보군에서 제외할 이유가 약하다.
- 반대로 `tuning 관점`에서는 여전히 구분이 필요하다.
  - `GPT-5.4`는 inference 최상위 후보이지만 일반 fine-tuning 주력 모델로 보긴 어렵다.
  - `Claude Sonnet/Opus 4.6`은 inference 최상위 후보지만 공개 fine-tuning 경로가 확인되지 않는다.
  - 장르 코퍼스의 weight tuning 실험은 현재 시점에서 `Gemini tuned path` 또는 `OpenAI GPT-4.1/o4-mini path`가 더 현실적이다.
- 따라서 실제 전략은 `frontier 모델 = 심사/생성`, `튜닝 모델 = 장르별 writer head`, `공통 메모리/정책 계층 = SSOT 유지`의 3분리가 가장 합리적이다.
