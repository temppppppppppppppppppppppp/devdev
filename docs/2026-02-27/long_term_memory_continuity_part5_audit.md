# 장기기억 연속성 시나리오 통과 가능성 점검 보고서

- 작성일: 2026-02-27
- 범위: `docs/diagnosis/continuity_violation_scenarios.md` PART 5 (L1~L7, #1~#35)
- 점검 방식: 코드 정적 감사 + 프로젝트 DB 샘플(최신 5개) 확인

## 1) 최종 결론

현재 시스템은 PART 5 시나리오를 **전부 통과하지 못합니다**.

- L1(NPC 장기 속성): 부분 통과
- L2(세계관 절대 법칙): 실패 위험 높음
- L3(관계도 장기 누적): 부분 통과
- L4(수치 누적 드리프트): 실패 위험 매우 높음
- L5(회상/플래시백 왜곡): 실패 위험 높음
- L6(정보 역설): 실패 위험 높음
- L7(장기 서사 구조): 실패 위험 높음

## 2) 영역별 판정표

| 영역 | 판정 | 근거 요약 |
|---|---|---|
| L1 | 부분 통과 | Dead NPC/아이템/파괴 장소 차단 체크는 존재. 다만 Stage4 인터뷰 라운드에서 Python 검증 결과가 Director 전달용 경고로 처리되는 경로가 남아 있음. |
| L2 | 실패 위험 높음 | `world_laws`/`role_at_intro` 장기 앵커는 존재하지만, 절대 법칙 위반을 강제 차단하는 전용 하드 블로킹 루트는 약함. TruthGate도 advisory-only. |
| L3 | 부분 통과 | 관계 일관성/정보 일관성 체크는 존재. 그러나 retrospective lookback 기본 5화, Director history 참조 상한 30화로 장기 누적 변질 탐지 깊이가 제한됨. |
| L4 | 실패 위험 매우 높음 | FactLedger 수치 추출은 특정 필드 기반(`financial_events`, `power_level`, `numerical_facts`) 중심. 장기 누적 드리프트(예: 143배 왜곡) 전용 검출기가 없음. |
| L5 | 실패 위험 높음 | Retrospective 검사는 4종(경지/관계/아이템/해결 갈등)으로 좁고 lookback도 짧음. 60화+ 구간은 요약 기반 비중이 높아 회상 왜곡 역검증이 약함. |
| L6 | 실패 위험 높음 | 정보 일관성 체크가 주로 "알아야 하는데 모르는" 방향. "알 수 없는데 알고 있음" 역방향 검출은 약함. |
| L7 | 실패 위험 높음 | 장기 서사 구조(아크 목표/서약/해결 충돌 재개)의 구조적 완결성 전용 validator가 부재. |

## 3) 근거(코드)

### 3.1 차단/검증 레이어

- TruthGate는 advisory-only이며 blocking을 강제하지 않음
  - `modules/core/truth_gate.py:1`
  - `modules/core/truth_gate.py:14`
  - `modules/core/truth_gate.py:34`
- BlockingValidator는 엔티티 차단 규칙을 보유
  - `modules/validation/blocking_validator.py:60`
  - `modules/validation/blocking_validator_entity_checks.py:88` (dead NPC)
  - `modules/validation/blocking_validator_entity_checks.py:138` (unowned item)
  - `modules/validation/blocking_validator_entity_checks.py:486` (destroyed location)
- Stage4 인터뷰 라운드에서 Python 검증은 Director 참고 경고로 전달되는 경로 존재
  - `modules/core/stage4_interview_round.py:514`
  - `modules/core/stage4_interview_round.py:516`
  - `modules/core/stage4_interview_round.py:527`
  - `modules/core/stage4_interview_round.py:785`

### 3.2 장기 기억 범위/회고 검증 깊이

- RetrospectiveValidator 기본 lookback 5화
  - `modules/validation/retrospective_validator.py:23`
  - `modules/validation/retrospective_validator.py:30`
- ValidationOrchestrator에서도 retrospective 초기화가 lookback 5로 고정
  - `modules/validation/validation_orchestrator.py:576`
- Director history 충돌 참조 상한 30화
  - `modules/domain/agents/director.py:57`
- Stage4ContextBuilder는 30화 full text + 60화 요약 + 그 이전 arc 요약의 tier 구조
  - `modules/core/stage4_context_builder.py:421`
  - `modules/core/stage4_context_builder.py:447`
  - `modules/core/stage4_context_builder.py:485`

### 3.3 세계관 앵커/정보 일관성

- world_laws / role_at_intro / known_attrs 장기 앵커 존재
  - `modules/core/world_state.py:38`
  - `modules/core/world_state.py:695`
- 정보 일관성 체크는 should_know 중심
  - `modules/validation/blocking_validator_consistency_checks.py:332`
  - `modules/validation/blocking_validator_consistency_checks.py:334`

### 3.4 수치 누적 검증 한계

- FactLedger 수치 추출 대상은 구조화 필드 중심
  - `modules/core/fact_ledger.py:295`
  - `modules/core/fact_ledger.py:310`
  - `modules/core/fact_ledger.py:315`

## 4) Graph 보조 레이어 연결 상태

결론: **Write 경로는 존재, Read/활용 경로는 사실상 미연결**.

- 테이블 생성 및 저장 구현은 존재
  - `modules/core/db_manager.py:246` (`causal_graph` 생성)
  - `modules/core/db_manager.py:1620` (`save_causal_links`)
  - `modules/core/stage4_post_processor.py:619` (dual-write)
- 코드 전역 검색 기준, `causal_graph`는 저장/복제/서비스 테이블 목록 중심 참조만 확인되고,
  Retrieval/Validator 단계에서 실사용 read 경로는 확인되지 않음.

## 5) DB 샘플 확인 (최신 5개 project_data.db)

샘플 결과 요약:

- `causal_graph`: 5개 모두 `0`
- 일부 DB는 `timeline_entries`, `npc_relationship_edges`, `episode_meta` 자체가 없음

대표 샘플:

- `projects/이전/테스트/project_data.db`
  - manuscripts: 25
  - state_logs: 25
  - episode_meta: 25
  - causal_graph: 0
  - character_voice: 105
  - timeline_entries: MISSING
  - npc_relationship_edges: MISSING

## 6) POC 관점에서의 해석

현재 상태는 "장기 기억 보조 레이어가 코드상 부분 도입된 상태"이며,
PART 5 전체 통과를 기준으로 하면 **POC 성립 전 단계**입니다.

POC 성립으로 보려면 최소 아래가 필요합니다.

1. L2/L4/L6/L7에 대한 차단 가능 검증기(또는 fail-closed 게이트) 추가
2. retrospective lookback 확장 및 60화+ 구간 전용 검증 경로 확보
3. `causal_graph` read 경로를 Retrieval/Validator 중 최소 1곳에 실연결
4. PART 5 시나리오 재실행 시 pass/fail 로그를 에피소드 단위로 재현 가능하게 저장

