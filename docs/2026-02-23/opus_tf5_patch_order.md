# Opus TF-5: 전체 시스템 패치 오더 (32건)

> 상태: `historical record / UTF-8 reconstructed`
> 기준일: `2026-02-23`
> 복원일: `2026-03-13`
> 베이스라인: 글도비 HEAD, TF-5 감사 완료, `32/32 CONFIRMED`
> 테스트 기준선: `2,324 passed`, `ruff 0 violations`
> 최종 결과: `2,377 passed`, `ruff 0 violations`, commit `5e7f7c04`

## 복원 메모

- 기존 `docs/2026-02-23/opus_tf5_patch_order.md`는 mojibake와 ASCII `?` 치환이 섞인 손상 상태였다.
- 손상 파일 안에 남아 있던 진행 표, 체크포인트, 일부 패치 지시를 보존했다.
- 누락된 한글 본문은 아래 근거로 재구성했다.
  - commit `5e7f7c04` 메시지
  - `git show 5e7f7c04:docs/2026-02-22/opus_tf5_consolidated_debug_report.md`
  - `git show 5e7f7c04:docs/2026-02-22/opus_tf5_*_debug_audit.md`
- 따라서 이 문서는 "원문 바이트 복구"가 아니라 "운영 의미를 보존한 UTF-8 재구성본"이다.
- 손상 과정에서 일부 문자가 이미 `?`로 치환되었으므로, 원문 literal을 100% 동일하게 되살리는 것은 불가능하다.

---

## Codex 실행 규칙 (복원본)

### 도구 제한

- `rg`, `grep`, `fgrep`, `ag`, `ack` 등 자동 검색 도구 사용 금지
- 반드시 해당 파일을 직접 열어 line 단위로 확인
- 파일 경로, 라인 번호, 수치, 코드 존재/부재를 주장할 때는 직접 읽은 뒤 기록

### 패치 원칙

- 한 번에 1건씩 패치
- 각 패치 직후 `pytest tests/ -q` 회귀 확인
- 테스트 실패 시 해당 패치를 즉시 롤백하고 진행표에 `BLOCKED` 기록 후 다음 항목으로 이동
- 기존 테스트가 없는 수정은 최소 1개 테스트 추가
- 수정 범위는 최소화하고 리팩터링/스타일 변경은 금지
- `ruff check` 및 `ruff format --check` 통과 확인

### 진행 업데이트 규칙

- 각 패치 완료 직후 진행표 상태를 즉시 갱신
- 5건마다 체크포인트를 기록
- 컨텍스트가 끊기면 이 문서를 처음부터 다시 읽고 마지막 완료 항목 다음부터 이어서 진행
- 상태 값은 `대기 중`, `완료`, `BLOCKED`, `SKIP`

---

## 진행표

| # | ID | 심각도 | 파일 | 요약 | 상태 | 테스트 |
|---|---|---|---|---|---|---|
| 1 | B-1 | HIGH | `stage4_post_processor.py` | Manager 비동기 타임아웃 시 정산 결과 유실 | 완료 | `pytest tests/ -q` (2340 passed) |
| 2 | F-1 | HIGH | `project_service.py` | Stage2 reset가 `_safe_commit` 실패를 무시 | 완료 | `pytest tests/ -q` (2341 passed) |
| 3 | F-2 | HIGH | `project_service.py` | rollback commit 실패 후에도 파일/벡터 삭제 진행 | 완료 | `pytest tests/ -q` (2342 passed) |
| 4 | K-2 | HIGH | `stage4_interview_round.py` | `_cv_context`에 `blueprint` 누락 | 완료 | `pytest tests/ -q` (2343 passed) |
| 5 | K-1 | HIGH | `blocking_validator_scene_checks.py` | `min_required=4` 하드코딩 | 완료 | `pytest tests/ -q` (2344 passed) |
| 6 | C-1 | HIGH | `project_service.py` | rollback 시 `npc_history` 정리 누락 | 완료 | `pytest tests/ -q` (2345 passed) |
| 7 | J-1 | HIGH | `four_phase_arc_generator.py` | `pre_collected_items` dict 직렬화로 검증 우회 | 완료 | `pytest tests/ -q` (2346 passed) |
| 8 | J-2 | HIGH | `four_phase_arc_generator.py` | `pre_collected_grants` 타입 정규화 누락 | 완료 | `pytest tests/ -q` (2347 passed) |
| 9 | L-1 | HIGH | `stage4_post_processor.py` | `record_validation(stage=4)` 미배선 | 완료 | `pytest tests/ -q` (2348 passed) |
| 10 | L-2 | HIGH | `stage2_optimizer.py` | dict 아이템 `name/item` 정규화 비대칭 | 완료 | `pytest tests/ -q` (2349 passed) |
| 11 | D-1 | HIGH | `arc_ensemble.py` | ArcEnsemble 캐시 본문 중복 전송 | 완료 | `pytest tests/ -q` (2350 passed) |
| 12 | D-2 | HIGH | `blueprint_ensemble.py` | BlueprintEnsemble 캐시 본문 중복 전송 | 완료 | `pytest tests/ -q` (2351 passed) |
| 13 | G-1 | HIGH | `stage3_orchestrator.py` | Stage3 DI 콜백 None 호출 가능 | 완료 | `pytest tests/ -q` (2352 passed) |
| 14 | G-2 | HIGH | `reverse_expander.py` | 배치 병렬 추출에서 `prev_state` 공유 | 완료 | `pytest tests/ -q` (2354 passed) |
| 15 | H-1 | HIGH | `base_guard.py` | 상태-행동 정당화 전역 매칭 | 완료 | `pytest tests/ -q` (2356 passed) |
| 16 | I-1 | HIGH | `continuity_arc.py` | `current_inventory` 선필터로 중복 획득 누락 | 완료 | `pytest tests/ -q` (2357 passed) |
| 17 | E-1 | HIGH | `director_continuity.py` | 단일 MAJOR 불연속도 PASS 처리 | 완료 | `pytest tests/ -q` (2358 passed) |
| 18 | A-1 | HIGH | `stage2_preflight.py` | ThreadPool timeout이 실질적으로 무력화 | 완료 | `pytest tests/ -q` (2359 passed) |
| 19 | B-2 | MEDIUM | `stage4_context_builder.py`, `stage4_interview_round.py` | Tier2 요약 파싱 불일치 | 완료 | `pytest tests/ -q` (2360 passed) |
| 20 | B-3 | MEDIUM | `context_advisor.py`, `stage4_context_builder.py` | `scene_breakdown` dict/list 계약 불일치 | 완료 | `pytest tests/ -q` (2362 passed) |
| 21 | F-3 | MEDIUM | `main_a.py` | rollback 취소/실패 시 `state_tracker=None` | 완료 | `pytest tests/ -q` (2364 passed) |
| 22 | K-3 | MEDIUM | `consistency_validator.py` | 3개 장르만 Guard 로드 | 완료 | `pytest tests/ -q` (2365 passed) |
| 23 | C-2 | MEDIUM | `db_manager.py`, `continuity_validator.py` | `npc_history` 정렬/비교 인덱스 불일치 | 완료 | `pytest tests/ -q` (2366 passed) |
| 24 | L-3 | MEDIUM | `stage4_orchestrator.py` | `director_max_attempts` 하드코딩 | 완료 | `pytest tests/ -q` (2367 passed) |
| 25 | G-3 | MEDIUM | `stage0/__init__.py` | `_genre` 누락 시 투자물 프리셋 강제 | 완료 | `pytest tests/ -q` (2368 passed) |
| 26 | A-2 | MEDIUM | `stage2_validation_pipeline.py` | structured feedback가 retry feedback에 미반영 | 완료 | `pytest tests/ -q` (2369 passed) |
| 27 | D-3 | MEDIUM | `context_advisor.py` | stage flag 기본값 fail-open | 완료 | `pytest tests/ -q` (2370 passed) |
| 28 | E-2 | MEDIUM | `director_ensemble.py` | REJECT 시 선택 후보 미전파 | 완료 | `pytest tests/ -q` (2370 passed) |
| 29 | H-2 | MEDIUM | `base_guard.py` | 미해결 갈등 검증이 NPC-local이 아님 | 완료 | `pytest tests/ -q` (2374 passed) |
| 30 | H-3 | MEDIUM | `base_guard.py` | 빌런 반응 검증이 일반 반응 전역 매칭 허용 | 완료 | `pytest tests/ -q` (2374 passed) |
| 31 | I-2 | MEDIUM | `continuity_blueprint.py` | grant/possession check 키워드 매칭 과탐 | 완료 | `pytest tests/ -q` (2375 passed) |
| 32 | I-3 | MEDIUM | `continuity_manuscript.py` | 부분 문자열 아이템 매칭 과탐 | 완료 | `pytest tests/ -q` (2377 passed) |

---

## 체크포인트

### CP-1 (1~5번 완료)

- 완료: `#1 B-1`, `#2 F-1`, `#3 F-2`, `#4 K-2`, `#5 K-1`
- BLOCKED: 없음
- 테스트: `passed=2344`, `failed=0`
- 시각: `2026-02-23 02:34:59`

### CP-2 (6~10번 완료)

- 완료: `#6 C-1`, `#7 J-1`, `#8 J-2`, `#9 L-1`, `#10 L-2`
- BLOCKED: 없음
- 테스트: `passed=2349`, `failed=0`
- 시각: `2026-02-23 02:49:11`

### CP-3 (11~15번 완료)

- 완료: `#11 D-1`, `#12 D-2`, `#13 G-1`, `#14 G-2`, `#15 H-1`
- BLOCKED: 없음
- 테스트: `passed=2356`, `failed=0`
- 시각: `2026-02-23 03:05:19`

### CP-4 (16~20번 완료)

- 완료: `#16 I-1`, `#17 E-1`, `#18 A-1`, `#19 B-2`, `#20 B-3`
- BLOCKED: 없음
- 테스트: `passed=2362`, `failed=0`
- 시각: `2026-02-23 03:22:26`

### CP-5 (21~25번 완료)

- 완료: `#21 F-3`, `#22 K-3`, `#23 C-2`, `#24 L-3`, `#25 G-3`
- BLOCKED: 없음
- 테스트: `passed=2368`, `failed=0`
- 시각: `2026-02-23 03:42:00`

### CP-6 (26~30번 완료)

- 완료: `#26 A-2`, `#27 D-3`, `#28 E-2`, `#29 H-2`, `#30 H-3`
- BLOCKED: 없음
- 테스트: `passed=2374`, `failed=0`
- 시각: `2026-02-23 03:58:00`

### CP-7 (31~32번 완료, 최종)

- 완료: `#31 I-2`, `#32 I-3`
- BLOCKED: 없음
- 최종 테스트: `passed=2377`, `failed=0`
- ruff: `violations=0`
- 시각: `2026-02-23 04:09:30`

---

## 컨텍스트 복구 절차

1. 이 문서 `docs/2026-02-23/opus_tf5_patch_order.md`를 처음부터 다시 읽는다.
2. 진행표에서 첫 `대기 중` 항목을 찾는다.
3. 아래 TF별 패치 지시에서 해당 ID의 패치 방향과 검증 대상을 확인한다.
4. 패치 완료 후 진행표와 체크포인트를 업데이트한다.
5. 다음 항목으로 이동한다.

---

## TF별 패치 지시

## TF-A Stage 2

출처: `git show 5e7f7c04:docs/2026-02-22/opus_tf5_stage2_debug_audit.md`

### `[A-1]` Preflight 타임아웃 무력화

- 파일: `modules/core/stage2_preflight.py`
- 패치 방향: `future.result(timeout=...)` 뒤 executor 종료 대기가 다시 block하지 않도록 timeout semantics를 fail-close로 고정한다.
- 검증: `tests/test_stage2_preflight.py`, 전체 `pytest tests/ -q`

### `[A-2]` structured feedback 미반영

- 파일: `modules/core/stage2_validation_pipeline.py`, `main_a.py`, `modules/core/feedback_system.py`
- 패치 방향: 연속성 구조화 피드백이 생성만 되고 버려지지 않도록 retry feedback 합성 경로에 병합한다.
- 검증: Stage2 retry 관련 테스트, 전체 `pytest tests/ -q`

## TF-B Stage 4

출처: `git show 5e7f7c04:docs/2026-02-22/opus_tf5_stage4_debug_audit.md`

### `[B-1]` Manager 정산 타임아웃 유실

- 파일: `modules/core/stage4_post_processor.py`
- 패치 방향: Manager future timeout/예외 시 동기 재시도 또는 명시적 실패 처리로 빈 `audit` 정상 커밋을 금지한다.
- 검증: `tests/test_stage4_post_processor.py`, 전체 `pytest tests/ -q`

### `[B-2]` Tier2 요약 파싱 불일치

- 파일: `modules/core/stage4_context_builder.py`, `modules/core/stage4_interview_round.py`
- 패치 방향: `]` 뒤 공백 또는 줄바꿈 모두 허용하도록 history parser를 완화해 11~30화 요약이 누락되지 않게 한다.
- 검증: `tests/test_stage4_context_builder.py`, `tests/test_stage4_interview_round.py`

### `[B-3]` `scene_breakdown` 계약 불일치

- 파일: `modules/models/blueprint.py`, `modules/core/context_advisor.py`, `modules/core/stage4_context_builder.py`
- 패치 방향: `scene_breakdown`을 dict/list 중 하나로 통일하고 retrieval/SC 경로가 같은 shape를 읽도록 맞춘다.
- 검증: `tests/test_context_advisor.py`, `tests/test_stage4_context_builder.py`

## TF-C NPC / State

출처: `git show 5e7f7c04:docs/2026-02-22/opus_tf5_npc_state_debug_audit.md`

### `[C-1]` rollback 시 `npc_history` stale 이력 잔존

- 파일: `modules/core/services/project_service.py`, `modules/core/db_manager.py`
- 패치 방향: episode rollback 경로에서 `npc_history`도 타깃 회차 기준으로 정리해 stale personality/state 주입을 차단한다.
- 검증: `tests/test_project_service.py`, `tests/test_continuity_validator.py`

### `[C-2]` `npc_history` 정렬/비교 인덱스 mismatch

- 파일: `modules/core/db_manager.py`, `modules/validation/continuity_validator.py`
- 패치 방향: 최신 엔트리를 비교하도록 정렬 방향과 접근 인덱스를 일치시킨다.
- 검증: `tests/test_continuity_validator.py`, `tests/test_db_manager.py`

## TF-D 인프라

출처: `git show 5e7f7c04:docs/2026-02-22/opus_tf5_infra_debug_audit.md`

### `[D-1]` ArcEnsemble 캐시 중복 전송

- 파일: `modules/domain/agents/arc_ensemble.py`, `modules/domain/agents/base_agent.py`
- 패치 방향: 캐시 hit 시 cached body와 prompt body가 이중 전송되지 않도록 prompt assembly를 분리한다.
- 검증: `tests/test_tier4_ensemble_caching.py`, 전체 `pytest tests/ -q`

### `[D-2]` BlueprintEnsemble 캐시 중복 전송

- 파일: `modules/domain/agents/blueprint_ensemble.py`, `modules/domain/agents/base_agent.py`
- 패치 방향: ArcEnsemble과 같은 캐시 전송 정책으로 정렬한다.
- 검증: `tests/test_tier4_ensemble_caching.py`, 전체 `pytest tests/ -q`

### `[D-3]` ContextAdvisor stage flag fail-open

- 파일: `modules/core/context_advisor.py`
- 패치 방향: config key 누락 시 활성으로 간주하지 말고 fail-close 기본값을 사용한다.
- 검증: `tests/test_context_advisor.py`

## TF-E Director

출처: `git show 5e7f7c04:docs/2026-02-22/opus_tf5_director_debug_audit.md`

### `[E-1]` 단일 MAJOR 불연속 PASS

- 파일: `modules/domain/agents/director_continuity.py`, `modules/domain/agents/three_phase_blueprint_generator.py`
- 패치 방향: MAJOR continuity hit가 하나만 있어도 PASS로 승격되지 않게 verdict rule을 수정한다.
- 검증: `tests/test_director_modules.py`

### `[E-2]` REJECT 시 선택 후보 미전파

- 파일: `modules/domain/agents/director_ensemble.py`, `modules/domain/agents/three_phase_blueprint_generator.py`
- 패치 방향: REJECT이더라도 선택된 blueprint를 patch target으로 유지해 후속 수정 전략이 빗나가지 않게 한다.
- 검증: `tests/test_director_modules.py`

## TF-F Integration

출처: `git show 5e7f7c04:docs/2026-02-22/opus_tf5_integration_debug_audit.md`

### `[F-1]` Stage2 reset commit failure 무시

- 파일: `modules/core/services/project_service.py`, `main_a.py`
- 패치 방향: `_safe_commit()` 실패 시 reset를 성공처럼 처리하지 말고 조기 중단한다.
- 검증: `tests/test_project_service.py`

### `[F-2]` rollback commit failure 후 파일/벡터 삭제

- 파일: `modules/core/services/project_service.py`, `main_a.py`
- 패치 방향: rollback commit 실패 시 draft/vector deletion을 진행하지 않고 즉시 복귀한다.
- 검증: `tests/test_project_service.py`, `tests/test_main_a_rollback.py`

### `[F-3]` rollback 실패 시 `state_tracker=None`

- 파일: `main_a.py`
- 패치 방향: rollback/reset 성공 시에만 tracker invalidation이 일어나도록 분기 순서를 수정한다.
- 검증: `tests/test_main_a_rollback.py`

## TF-G Stage 0 / 3

출처: `git show 5e7f7c04:docs/2026-02-22/opus_tf5_stage0_3_debug_audit.md`

### `[G-1]` Stage3 DI nullable violation

- 파일: `modules/core/stage3_orchestrator.py`, `modules/core/stage3_context.py`
- 패치 방향: optional callback에 `callable()` guard를 넣고 none-path를 안전하게 우회한다.
- 검증: `tests/test_stage3_orchestrator.py`

### `[G-2]` ReverseExpander `prev_state` 공유

- 파일: `modules/core/stage0/reverse_expander.py`
- 패치 방향: batch 병렬 경로에서 회차별 `prev_state`를 공유하지 않도록 순차화하거나 ep별 컨텍스트를 분리한다.
- 검증: `tests/test_reverse_expander_g2.py`

### `[G-3]` `_genre` 누락 시 투자물 프리셋 강제

- 파일: `modules/core/stage0/__init__.py`
- 패치 방향: `_genre` 누락을 투자물 fallback으로 고정하지 말고 명시적 genre resolution 또는 안전한 기본값을 사용한다.
- 검증: `tests/test_stage0_fixes.py`

## TF-H Genre Guards

출처: `git show 5e7f7c04:docs/2026-02-22/opus_tf5_genre_guards_debug_audit.md`

### `[H-1]` 정당화 판정 전역 매칭

- 파일: `modules/core/genre_guards/base_guard.py`, `modules/validation/consistency_validator.py`
- 패치 방향: 행동 정당화는 원고 전체 검색이 아니라 로컬 윈도우/문맥 근접성 기준으로 판정한다.
- 검증: `tests/test_genre_guard.py`, `tests/test_consistency_validator.py`

### `[H-2]` NPC-local 미해결 갈등 누락

- 파일: `modules/core/genre_guards/base_guard.py`
- 패치 방향: 해소 여부를 NPC 단위 지역 문맥에서 판단하도록 수정한다.
- 검증: `tests/test_genre_guard.py`

### `[H-3]` 빌런 반응 전역 매칭

- 파일: `modules/core/genre_guards/base_guard.py`
- 패치 방향: 빌런 반응은 빌런-local proximity가 있을 때만 유효하게 판정한다.
- 검증: `tests/test_genre_guard.py`

## TF-I Continuity

출처: `git show 5e7f7c04:docs/2026-02-22/opus_tf5_continuity_debug_audit.md`

### `[I-1]` `current_inventory` 선필터 과소검출

- 파일: `modules/domain/agents/continuity_arc.py`
- 패치 방향: duplicate acquisition 검사에서 `current_inventory`를 선필터로 쓰지 않거나 보조 신호로만 사용한다.
- 검증: `tests/test_continuity_modules.py`

### `[I-2]` grant/possession keyword matching

- 파일: `modules/domain/agents/continuity_blueprint.py`
- 패치 방향: 단순 keyword 대신 `_is_same_item` 수준의 item identity matching을 적용한다.
- 검증: `tests/test_continuity_modules.py`

### `[I-3]` 부분 문자열 item matching 과탐

- 파일: `modules/domain/agents/continuity_manuscript.py`
- 패치 방향: substring 허용 범위를 ratio/length 조건으로 좁혀 유사 문자열 오판을 줄인다.
- 검증: `tests/test_continuity_modules.py`

## TF-J Arc Generation

출처: `git show 5e7f7c04:docs/2026-02-22/opus_tf5_arc_gen_debug_audit.md`

### `[J-1]` `pre_collected_items` dict 직렬화 우회

- 파일: `modules/domain/agents/four_phase_arc_generator.py`, `modules/domain/agents/unified_arc_validator.py`
- 패치 방향: dict item을 문자열 직렬화로 흘리지 말고 validator가 이해하는 canonical item shape로 정규화한다.
- 검증: `tests/test_four_phase_arc_generator.py`

### `[J-2]` `pre_collected_grants` 타입 정규화 누락

- 파일: `modules/domain/agents/four_phase_arc_generator.py`, `modules/domain/agents/unified_arc_validator.py`
- 패치 방향: grants도 items와 같은 canonical shape로 normalize한 뒤 중복 수여 검사에 전달한다.
- 검증: `tests/test_four_phase_arc_generator.py`

## TF-K Validation

출처: `git show 5e7f7c04:docs/2026-02-22/opus_tf5_validation_debug_audit.md`

### `[K-1]` `required_scenes` 하드코딩

- 파일: `modules/validation/blocking_validator_scene_checks.py`
- 패치 방향: `min_required = min(4, scene_count)` 또는 equivalent rule로 small blueprint를 항상 REJECT하지 않게 한다.
- 검증: `tests/test_blocking_validator_submodules.py`

### `[K-2]` Stage4 validation context에 `blueprint` 누락

- 파일: `modules/core/stage4_interview_round.py`
- 패치 방향: `_cv_context`에 `blueprint`, `blueprint_text`를 주입해 scene blocking checks 4종을 다시 활성화한다.
- 검증: `tests/test_stage4_interview_round.py`

### `[K-3]` Guard loading 3장르 한정

- 파일: `modules/validation/consistency_validator.py`, `modules/domain/agents/director_auditor.py`
- 패치 방향: `create_genre_guard()` 기반 공통 로더로 통합해 운영 장르 전부를 로드한다.
- 검증: `tests/test_consistency_validator.py`, `tests/test_director_modules.py`

## TF-L Ops / Config

출처: `git show 5e7f7c04:docs/2026-02-22/opus_tf5_ops_config_debug_audit.md`

### `[L-1]` Stage4 QualityDashboard 미기록

- 파일: `modules/core/stage4_post_processor.py`, `main_a.py`, `modules/core/quality_dashboard.py`
- 패치 방향: Stage4 PASS/REJECT 결과를 `quality_dashboard.record_validation(..., stage=4)`에 기록한다.
- 검증: `tests/test_stage4_post_processor.py`

### `[L-2]` Stage2Optimizer item normalization asymmetry

- 파일: `modules/core/stage2_optimizer.py`, `modules/core/stage2_validation_pipeline.py`
- 패치 방향: `name`/`item` 포맷을 대칭 정규화해 dict item 우회 경로를 닫는다.
- 검증: `tests/test_stage2_optimizer.py`, `tests/test_stage2_validation_pipeline.py`

### `[L-3]` `director_max_attempts` 하드코딩

- 파일: `config/settings/validation.yaml`, `modules/core/stage4_orchestrator.py`
- 패치 방향: `validation.yaml.retry.director_max_attempts`를 Stage4 루프가 실제로 읽게 배선한다.
- 검증: `tests/test_stage4_orchestrator.py`

---

## Cross-TF 메모

- `[X-1]` Scene 계약 드리프트: `B-3`, `K-2`를 함께 수정해야 Stage4 scene gate가 완전히 복원된다.
- `[X-2]` Guard loader 분리: `H-*`, `K-3`는 장르 Guard 주입 경로를 공통 팩토리로 통합해야 한다.
- `[X-3]` 운영 관측 공회전: `L-1` 없이는 Stage4 품질 하락이 dashboard에서 보이지 않는다.

---

## 최종 검증

```bash
# 전체 회귀
pytest tests/ -q

# Ruff
python -m ruff check modules/ tests/ main_a.py
python -m ruff format --check modules/ tests/ main_a.py

# TF-5 핵심 교차 검증
pytest tests/test_context_advisor.py tests/test_stage2_preflight.py tests/test_stage4_interview_round.py tests/test_project_service.py -q
```

---

## 커밋 계획

- 5건 단위로 커밋
- 커밋 메시지 패턴: `fix(tf5): patch #{시작}~#{끝} - {요약}`
- 최종 커밋: `fix(tf5): TF-5 32건 패치 완료 + 전체 회귀 통과`

---

## 근거 소스

- `git show 5e7f7c04 --format=fuller --no-patch`
- `git show 5e7f7c04:docs/2026-02-22/opus_tf5_consolidated_debug_report.md`
- `git show 5e7f7c04:docs/2026-02-22/opus_tf5_stage2_debug_audit.md`
- `git show 5e7f7c04:docs/2026-02-22/opus_tf5_stage4_debug_audit.md`
- `git show 5e7f7c04:docs/2026-02-22/opus_tf5_npc_state_debug_audit.md`
- `git show 5e7f7c04:docs/2026-02-22/opus_tf5_infra_debug_audit.md`
- `git show 5e7f7c04:docs/2026-02-22/opus_tf5_director_debug_audit.md`
- `git show 5e7f7c04:docs/2026-02-22/opus_tf5_integration_debug_audit.md`
- `git show 5e7f7c04:docs/2026-02-22/opus_tf5_stage0_3_debug_audit.md`
- `git show 5e7f7c04:docs/2026-02-22/opus_tf5_genre_guards_debug_audit.md`
- `git show 5e7f7c04:docs/2026-02-22/opus_tf5_continuity_debug_audit.md`
- `git show 5e7f7c04:docs/2026-02-22/opus_tf5_arc_gen_debug_audit.md`
- `git show 5e7f7c04:docs/2026-02-22/opus_tf5_validation_debug_audit.md`
- `git show 5e7f7c04:docs/2026-02-22/opus_tf5_ops_config_debug_audit.md`

---

*Reconstructed on 2026-03-13 from preserved TF-5 audit evidence after mojibake corruption of the original file.*
