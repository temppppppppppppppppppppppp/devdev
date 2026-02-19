# Opus Handoff: Actionable Only (2026-02-18)

- 목적: Opus가 바로 고칠 항목만 전달
- 기준: 의도된 설계 가능성 높은 항목, 정책/하드닝 성격(글자수 제한류 포함)은 제외
- 범위: 코드 수정 필요 이슈만

## 1) 즉시 수정 필요 (실버그/오동작)

### P0 (데이터 무결성/성공판정 왜곡)

1. Stage2 PASS 경로에서 commit 결과 무시
- `modules/core/stage2_finalizer.py`

2. Stage3 commit 결과 무시
- `modules/core/stage3_orchestrator.py`

3. Stage4 PASS 저장 구간 비원자성(부분 커밋 가능)
- `modules/core/stage4_post_processor.py`

4. 성공 로그/성공 반환이 실제 저장 실패와 어긋나는 경로 다수
- `modules/core/stage4_post_processor.py`
- `modules/core/stage0/reverse_expander.py`
- `modules/core/pattern_tracker.py`
- `modules/core/project_manager.py`
- `modules/core/stage01_helpers.py`
- `modules/core/stage2_preflight.py`
- `main_a.py`

### P1 (계약/타입 불일치로 런타임 실패 가능)

5. `joint_docs` 계약 불일치 (중첩 vs 상위)
- `modules/domain/agents/analyst.py`
- `modules/core/stage2_finalizer.py`

6. Stage2 fallback 타입 위반 (`physical_inventory` string/list)
- `modules/core/stage2_finalizer.py`
- `modules/core/response_schemas.py`

7. Stage2 finalizer의 타입-unsafe `.get()` 사용
- `modules/core/stage2_finalizer.py`

8. `validate_arc_data_fields` 보정 전 크래시 가능
- `modules/core/services/state_service.py`
- 호출: `modules/core/stage3_orchestrator.py`

9. Arc 매핑 시 `ep_count` 누락이면 `ep_end` 과팽창 가능
- `modules/core/services/state_service.py`

10. Analyst 연속성 검증 사실상 비활성화 경로
- `modules/domain/agents/analyst.py`

11. Analyst fallback `arcs` shape 드리프트(dict/list)
- `modules/domain/agents/analyst.py`

12. ArcCorrector 변경량 가드 우회
- `modules/domain/agents/arc_corrector.py`

### P2 (운영 가시성/디버깅 방해)

13. 내부 오류를 무해로 둔갑시키는 경로
- `modules/domain/agents/chief_writer_context.py`
- `modules/core/reference_anchor.py`

14. 사용자 UI에 raw 예외 문자열 노출
- `modules/core/stage2_orchestrator.py`

15. Traceback 과다 노출 (콘솔/로그)
- `main_a.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/services/project_service.py`
- 기타 traceback 출력 파일들

## 2) 이번 전달본에서 제외한 항목 (의도/정책/하드닝)

1. `projects/` 폴더 미생성 크래시 의심
2. `get_latest_episode_number()` off-by-one 의심(현재 계약상 next-ep 반환)
3. Stage4 `max_loops +5`
4. `detect_score_regression(stage=2)` 호출
5. `except Exception` 전체 건수 자체를 단독 결함으로 취급한 항목

## 3) Opus 작업 순서 (실행용)

1. P0부터: commit/성공판정 진실성 + 비원자 저장 경로 정리
2. P1: 계약/타입 불일치 제거
3. P2: 오류 표면 정리(로그/사용자 메시지 분리)
4. 운영권고: 동시성/락 일관성 보강

## 4) Root Cause Classes (재발 방지용)

1. RC-01 저장 성공 판정 전파 실패 (Write-Ack Gap)
- 저장 API가 `bool` 반환인데 호출부에서 결과 확인이 누락됨.
- 근거: `modules/core/stage2_finalizer.py:282`, `modules/core/stage2_finalizer.py:283`, `modules/core/stage3_orchestrator.py:479`, `modules/core/project_manager.py:253`, `modules/core/db_manager.py:778`

2. RC-02 모듈 간 스키마 드리프트 (Contract Drift)
- 동일 키가 구간마다 다른 타입/구조로 취급됨 (`joint_docs`, `physical_inventory`, `arcs`).
- 근거: `modules/core/stage2_finalizer.py:191`, `modules/core/stage2_finalizer.py:193`, `modules/core/stage2_finalizer.py:200`, `modules/domain/agents/analyst.py:951`, `modules/domain/agents/analyst.py:1472`

3. RC-03 타입 정규화 순서 오류 (Repair Order Bug)
- 보정 전에 계산/연산이 먼저 수행되어 왜곡/크래시가 발생함.
- 근거: `modules/core/services/state_service.py:69`, `modules/core/services/state_service.py:83`, `modules/core/services/state_service.py:249`, `modules/core/services/state_service.py:250`, `modules/core/stage3_orchestrator.py:284`

4. RC-04 다중 저장소 원자성 분리 (Cross-Store Atomicity Split)
- DB/파일/벡터/앵커가 분리 커밋되어 부분 성공 상태가 생김.
- 근거: `modules/core/stage4_post_processor.py:46`, `modules/core/stage4_post_processor.py:340`, `modules/core/services/project_service.py:185`, `modules/core/services/project_service.py:258`

5. RC-05 정책 가드와 결함 신호 혼재 (Policy vs Bug Noise)
- 길이 제한/루프 상한/최소 분량 가드가 버그와 섞여 스윕이 길어짐.
- 근거: `modules/core/stage4_orchestrator.py:350`, `modules/core/stage4_orchestrator.py:479`, `modules/core/stage4_orchestrator.py:510`, `modules/core/services/state_service.py:331`, `modules/domain/agents/chief_writer_context.py:794`

## 5) Exclusion Rule (정책성 항목 분리)

1. 아래는 기본적으로 버그가 아니라 정책 이벤트로 분류:
- 컨텍스트 글자수 절단 (예: 50,000자)
- 최소 분량 가드 (예: tactical_doc 500자)
- 루프 상한 (max_loops)

2. 위 정책 위반은 버그 트래커가 아니라 운영/품질 정책 트래커에서 관리.

## 6) 추가 조사/보강 포인트 (비용/성능 제외 5카테고리)

1. 재실행/멱등성
- 리스크: 진행률을 `len(arcs)`로 계산하여 중복 Arc 저장 시 다음 실행 진입점 왜곡 가능.
- 근거: `modules/core/stage2_orchestrator.py:151`, `modules/core/stage2_orchestrator.py:152`, `modules/core/stage2_finalizer.py:278`
- 보강: `arc_no` 유니크 보장 후 저장, 진행률은 `max(arc_no)` 기준으로 계산.

2. 중단복구
- 리스크: `KeyboardInterrupt` 처리 범위가 Stage4/메인 중심이고 Stage2는 중간 `return` 경로가 많아 정리/요약 누락 가능.
- 근거: `modules/core/stage4_orchestrator.py:808`, `main_a.py:1898`, `modules/core/stage2_orchestrator.py:328`, `modules/core/stage2_orchestrator.py:715`, `modules/core/stage2_orchestrator.py:725`, `modules/core/stage2_orchestrator.py:749`
- 보강: Stage2/3에도 `try/finally`로 `write_audit_summary`/flush 강제.

3. 계약고정 (스키마/컨테이너 일관성)
- 리스크: `arcs`를 dict/list 혼용 가정하는 경로가 공존하고, 상태검증 함수가 비활성화되어 연속성 검증 공백 발생.
- 근거: `modules/domain/agents/analyst.py:951`, `modules/domain/agents/analyst.py:1472`, `modules/domain/agents/analyst.py:1451`
- 보강: `arcs` 컨테이너 타입 단일화(list 고정), 비활성 검증 로직 복구 또는 명시적 제거.

4. 원자성 (부분 성공 상태)
- 리스크: Stage4에서 초기 DB 커밋 후 후속 저장 실패를 비차단 처리하여 부분 성공 상태가 남음.
- 근거: `modules/core/stage4_post_processor.py:46`, `modules/core/stage4_post_processor.py:292`, `modules/core/stage4_post_processor.py:340`, `modules/core/stage4_post_processor.py:373`, `modules/core/stage4_post_processor.py:394`, `modules/core/stage4_post_processor.py:328`, `modules/core/stage4_post_processor.py:347`, `modules/core/stage4_post_processor.py:375`, `modules/core/stage4_post_processor.py:399`
- 보강: “에피소드 단위 완료 조건”을 정의하고 미충족 시 명시적 failed 상태 기록.

5. 회귀셋 (테스트 공백)
- 리스크: 성공 경로 가정 테스트가 많고 실패/복구 경로 테스트가 부족.
- 근거: `tests/test_stage2_finalizer.py:32`, `tests/test_stage3_orchestrator.py:67`, `tests/test_stage3_orchestrator.py:276`, `tests/test_stage2_pipeline.py:280`, `tests/e2e/test_l3_stage2_realproject.py:151`, `tests/e2e/test_l3_stage2_realproject.py:152`, `tests/e2e/test_l3_golden_route.py:173`, `tests/e2e/test_l3_golden_route.py:174`, `tests/test_stage4_post_processor.py:113`
- 보강: commit 실패 반환, 중단 후 재시작, 부분 저장 후 재실행 시나리오를 고정 회귀셋으로 추가.

## 7) 유형 심화 매트릭스 (추가 조사 결과)

1. TG-01 Fail-Open 검증 게이트
- 분류: 운영 리스크(의도 설계 가능성 높음, 이번 즉시 픽스 제외 후보)
- 증상: 파싱 실패 시 검증이 `PASS`/중립값으로 통과됨.
- 근거: `modules/core/chain_of_verification.py:154`, `modules/core/cross_agent_verifier.py:155`, `modules/core/cross_agent_verifier.py:157`, `modules/core/narrative_structure_analyzer.py:98`, `modules/core/narrative_structure_analyzer.py:104`, `modules/core/narrative_structure_analyzer.py:109`
- 테스트 현황: 정상 shape 위주(`tests/test_sweep28.py:15`, `tests/test_sweep28.py:23`).
- 권고: strict 모드(예: `fail_open=False`)에서 파싱 실패를 `DEGRADED/REJECT`로 승격.

2. TG-02 검증 약화 상태 지속 (Degraded Latch)
- 분류: 운영 리스크(의도 설계 가능성 높음, 이번 즉시 픽스 제외 후보)
- 증상: 누적 상태 추출 실패 시 “NPC 검증 약화”를 기록하고 공정은 계속 진행.
- 근거: `modules/core/stage2_preflight.py:149`, `modules/core/stage2_preflight.py:151`, `modules/core/stage2_preflight.py:157`
- 테스트 현황: 비전파 동작을 허용하는 회귀 존재(`tests/test_stage2_preflight.py:181`).
- 권고: 결과물 메타에 `degraded_reason` 강제 기록 후 후속 Stage에서 가중 감점 또는 재검증 강제.

3. TG-03 중단-요약 비대칭 (Abort/Finalize Asymmetry)
- 분류: 실수정 권고(P1)
- 증상: 사용자 중단 경로에서 `return`으로 빠지며, 정상 종료 요약 기록 지점에 도달하지 못함.
- 근거: `modules/core/stage2_orchestrator.py:715`, `modules/core/stage2_orchestrator.py:725`, `modules/core/stage2_orchestrator.py:749`
- 권고: Stage2 본문을 `try/finally`로 감싸 `write_audit_summary`를 종료 원인과 무관하게 실행.

4. TG-04 Stage3 Commit Ack 미전파 + 테스트 공백
- 분류: 실수정 권고(P0/P1)
- 증상: blueprint 저장 후 `safe_commit()` 호출만 있고 성공/실패 분기 검증이 없음.
- 근거: `modules/core/stage3_orchestrator.py:478`, `modules/core/stage3_orchestrator.py:479`
- 테스트 현황: 호출 여부만 검증(`tests/test_stage3_orchestrator.py:275`, `tests/test_stage3_orchestrator.py:276`), commit 실패 반환 시나리오 부재.
- 권고: commit 실패 시 `blueprint_success` 이벤트 금지 + 실패 이벤트로 전환.

5. TG-05 Stage4 후행 저장 실패의 누적 은닉
- 분류: 실수정 권고(P0/P1)
- 증상: 초기 DB commit 이후 Bible/ChainLink/WorldState/FactLedger 저장 실패가 비차단 처리되어 부분 성공 상태가 축적될 수 있음.
- 근거: `modules/core/stage4_post_processor.py:46`, `modules/core/stage4_post_processor.py:50`, `modules/core/stage4_post_processor.py:292`, `modules/core/stage4_post_processor.py:328`, `modules/core/stage4_post_processor.py:340`, `modules/core/stage4_post_processor.py:347`, `modules/core/stage4_post_processor.py:373`, `modules/core/stage4_post_processor.py:375`, `modules/core/stage4_post_processor.py:394`, `modules/core/stage4_post_processor.py:399`
- 권고: “필수 저장 세트” 완료 여부를 별도 상태로 남기고, 미완료 시 재처리 큐로 강제 편입.

---

본 문서는 “실수정 대상”만 남긴 축약본이다.
