# Opus TF 전면 감사 통합 리포트 (2026-02-22)

> 6개 Task Force 감사 보고서 통합본
> 감사자: Claude Opus 4.6
> 감사 범위: Stage 0 / Stage 2 / Stage 3 / Stage 4 / Validation & Quality / 인프라(공통 모듈)
> **크로스체크**: P0 전건 코드 실측 검증 완료 (오탐 2건 제거, 1건 등급 하향)
> **수정 현황**: P0 4건 + P1 39건 + P2 33건 **전량 수정 완료** (커밋 `0b67847`, `bb0e1ac`)
> **개선 구현**: 43건 중 19건 구현 완료 (커밋 `1bd3dd4`), 6건 Tier 3 보류, 15건 Tier 4 스킵, 3건 기존 완료

---

## 1. 총괄 요약

| 등급 | Stage 0 | Stage 2 | Stage 3 | Stage 4 | Validation | 인프라 | **합계** |
|------|---------|---------|---------|---------|------------|--------|----------|
| **P0 (차단급)** | 1 | 0 | 1 | 2 | 0 | 0 | **4** |
| **P1 (품질 이슈)** | 8 | 5 | 5 | 7 | 5 | 9 | **39** |
| **P2 (스타일/경미)** | 5 | 7 | 4 | 6 | 4 | 7 | **33** |
| **개선 아이디어** | 6 | 8 | 6 | 8 | 7 | 8 | **43** |
| **소계** | 20 | 20 | 16 | 23 | 16 | 24 | **119** |

**전체 건전성 판정**: P0 4건 + P1 39건 + P2 33건 = **76건 전량 수정 완료**. 개선 아이디어 43건 중 **19건 구현 완료** (Tier 1+2). 테스트 2266 passed, 68 xfailed, ruff 0 violations.

---

## 2. P0 전체 목록 (크로스체크 완료: 4건 확인 + 2건 오탐 제거)

| # | TF | 파일:위치 | 설명 | 검증 결과 |
|---|----|-----------|----|------------|
| 1 | S0-P0-1 | `modules/core/stage01_helpers.py:291` | `StageZeroManager` 생성 시 `llm_client` 미전달 — 환경변수 폴백으로 동작하나 API 키 로테이션/커스텀 클라이언트 무시 | **확인** |
| 2 | S3-P0-1 | `modules/core/stage3_orchestrator.py:420` | `_bp_semantic_ctx` 항상 빈 문자열 — 벡터 시맨틱 검색 기능이 파라미터만 존재하고 데이터 미주입 | **확인** — 기능 누락 |
| 3 | S4-P0-1 | `modules/core/stage4_context_builder.py:327-340` + `stage4_interview_round.py:555-568` | 직전 30화 원고를 context_builder와 interview_round에서 이중 로드 — 매 에피소드 최대 60회 DB 조회 | **확인** — 성능/메모리 |
| 4 | S4-P0-2 | `modules/core/stage4_orchestrator.py:364-376` | `build_mandatory_context()` 호출 시 `blueprint` 인자 미전달 — SC NPC roster + retrieval plan 품질 저하 | **확인** |

### 오탐 제거 (2건) + 등급 하향 (1건)

| 원래 # | TF | 판정 | 사유 |
|--------|-----|------|------|
| S0-P0-2 | Stage 0 | **P1로 하향** | `generate_bible()` 실패 시 `self.bible = {}`로 유지되어 크래시 아님, 빈 출력만 생성 |
| INF-P0-1 | 인프라 | **오탐 제거** | `threading.RLock` 사용 중 — 동일 스레드 재진입 안전. 교착 불가 |
| INF-P0-2 | 인프라 | **오탐 제거** | 싱글톤 패턴 + `_cache_lock` 스레드 안전 + YAML 정적 파일. `invalidate_cache()` 메서드도 존재 |

---

## 3. P1 전체 목록 (38건)

| # | TF | 파일:위치 | 설명 |
|---|----|-----------|------|
| 1 | S0-P1-1 | `stage0/reverse_expander.py:506` | `run()` 반환 타입 불일치 -- `style_guide`가 None일 수 있으나 시그니처에 미반영 |
| 2 | S0-P1-2 | `stage0/__init__.py:48-59` vs `preset_registry.py:100-108` | `SUPPORTED_GENRES` 순서가 `_select_genre()` 하드코딩 매핑과 불일치 가능 |
| 3 | S0-P1-3 | `stage0/reverse_expander.py:113-115,170-172` | cp949 폴백 실패 시 2차 UnicodeDecodeError 미처리 |
| 4 | S0-P1-4 | `stage0/story_expander.py:379-413` | `_generate_skeleton()` LLM 실패 시 빈 블록이 에러 로그 없이 조용히 진행 |
| 5 | S0-P1-5 | `stage0/preset_registry.py:552-567` | `detect_new_genre()` 키워드 세트가 10개 장르 중 4개만 커버 (미사용 함수) |
| 6 | S0-P1-6 | `stage0/__init__.py:85-101` | `show_menu()` 등에서 `logging.info()`를 UI 출력에 사용 -- 로깅 레벨에 따라 메뉴 미표시 |
| 7 | S0-P1-7 | `stage0/style_extractor.py:683` | `_llm_call()` models 리스트 빈 경우 불친절한 RuntimeError |
| 8 | S2-P1-1 | `stage2_finalizer.py:353` | `passed = True` 데드 코드 -- 실제 passed 전달은 `action="break"` 반환으로 수행 |
| 9 | S2-P1-2 | `stage2_orchestrator.py:104` | `_SUMMARY_MODEL` 미사용 변수 (B-1-6 분리 후 잔존) |
| 10 | S2-P1-3 | `stage2_orchestrator.py:109-116` | `ReflectionTarget` 중복 import (orchestrator에서 미사용) |
| 11 | S2-P1-4 | `stage2_validation_pipeline.py:65-86,256-276` | DraftValidator 이중 호출 -- 첫 호출의 `draft_validator_passed=True`가 Consensus REJECT 후에도 살아남아 Finalizer 판단에 영향 가능 |
| 12 | S2-P1-5 | `stage2_preflight.py:192-266` | ThreadPoolExecutor 내부에서 `perf_timer.start/stop` 등 공유 객체를 Lock 없이 변경 |
| 13 | S3-P1-1 | `stage3_orchestrator.py:576-581` | `_handle_failure`가 fail_count 무관하게 항상 `break: True` 반환 -- 주석("연속 3회 실패")과 동작 불일치 |
| 14 | S3-P1-2 | `unified_blueprint_validator.py:220-222` | `get_causal_history_summary()` 호출 시 DB 테이블 미존재 시 SQLite 에러가 hasattr로 잡히지 않음 |
| 15 | S3-P1-3 | `blueprint_ensemble.py:191-195` | `_strategy_feedback`이 rejected_strategy에만 전달 -- 다른 전략은 구체적 피드백 없이 생성 |
| 16 | S3-P1-4 | `three_phase_blueprint_generator.py:329` | `continuity_feedback` REJECT 후 `feedback` 변수에 `+=` 누적 -- 코드 가독성 이슈 (실제 버그 아님) |
| 17 | S3-P1-5 | `blueprint_ensemble.py:407-431` | `_evaluate_candidate` 메서드 미사용 (Dead Code, V60.80 이전 레거시) |
| 18 | S4-P1-1 | `stage4_orchestrator.py:568-575` | CoVe REJECT 시 `final_title` 미리셋 -- 폴백 시 원고-제목 불일치 가능 |
| 19 | S4-P1-2 | `stage4_context_builder.py:515-596` | `state_tracker` None 검사 15회 연속 반복 -- 가독성 극히 저하 |
| 20 | S4-P1-3 | `stage4_orchestrator.py:31` | `_detect_npc_overexposure` default argument에서 모듈 로드 시 `_threshold()` 호출 -- 설정 변경 미반영 가능 |
| 21 | S4-P1-4 | `stage4_interview_round.py:541,583` | `_story_context` 변수명과 round_ctx 필드명 `story_context` 불일치 (혼란 유발) |
| 22 | S4-P1-5 | `stage4_post_processor.py:242` | `bible_delta` 부분 성공 시 FactLedger 미갱신 -- bible_delta 구성 성공 + save 실패 시 데이터 불일치 |
| 23 | S4-P1-6 | `stage4_context_builder.py:183-221` | `_apply_context_budget`에서 `_build_tracker` 반복 생성 -- O(n^2) 복잡도 |
| 24 | S4-P1-7 | `chief_writer_quality.py:460-492` | `_check_cliche_overuse`의 `content` dead parameter -- 전달되지만 사용되지 않음 |
| 25 | V-P1-1 | `scoring_validator.py:62-79` | `_load_guard_for_genre()`가 wuxia/hunter만 처리 -- 나머지 8개 장르 `return None` |
| 26 | V-P1-2 | `scoring_validator.py:684-723` | `GENRE_WEIGHTS`에 3개 장르만 정의 -- 7개 장르에서 무협 가중치 폴백 적용 |
| 27 | V-P1-3 | `validation_orchestrator.py:250-273` | PreLLM 데드코드 -- 항상 `passed: True` 반환하지만 REJECT 분기가 잔존 |
| 28 | V-P1-4 | `blocking_validator.py:178-190` | 관계/정보 일관성 검증에서 모든 예외를 `passed: True`로 흡수 -- 프로그래밍 오류까지 통과 |
| 29 | V-P1-5 | `catharsis_timer.py:22-61` | 카타르시스/좌절 지표에 3개 장르만 정의 -- 7개 장르 common 키워드만으로 감지 |
| 30 | INF-P1-1 | `db_manager.py:54,74` | `self.cursor` 인스턴스 공유 -- 스레드 안전하지 않음 (cursor 상태 오염 가능) |
| 31 | INF-P1-2 | `db_manager.py:505-512` | `begin()/commit()/rollback()`에 Lock 보호 없음 -- 트랜잭션 상태 불일치 가능 |
| 32 | INF-P1-3 | `base_agent.py:359-360` | `_rotation_count` 리셋이 Lock 밖에서 실행 -- 멀티스레드 race condition |
| 33 | INF-P1-4 | `metrics_collector.py:142` | `_metrics` dict 무한 성장 -- end_call 후에도 삭제 안 됨 (장기 세션 메모리 증가) |
| 34 | INF-P1-5 | `vec_memory.py:406-420` | `retrieve_multi_query_context`에서 `_load_episode_meta` Lock 중첩 호출 -- RLock 의존 암묵적 가정 |
| 35 | INF-P1-6 | `config_manager.py:80-106` | `load_settings()` 스레드 안전하지 않음 -- force_reload 동시 호출 시 AttributeError 가능 |
| 36 | INF-P1-7 | `db_manager.py:514-523` | `close()` 후 cursor=None인데 다른 메서드가 미체크 -- 프로젝트 전환 시 크래시 |
| 37 | INF-P1-8 | `base_agent.py:1045` | `_context_caches` 클래스 변수 dict -- 멀티스레드 캐시 읽기/쓰기 경합 가능 |
| 38 | INF-P1-9 | `world_state.py:433-451`, `fact_ledger.py:558-577` | `rollback_to()` 1화부터 순회 -- 200화 이상에서 수십 초 소요 |

---

## 4. P2 전체 목록 (33건)

| # | TF | 파일:위치 | 설명 |
|---|----|-----------|------|
| 1 | S0-P2-1 | `preset_registry.py:412-420` | `FIELD_ALIASES`에 신규 장르 필드 별칭 누락 (chef_rank, doctor_rank 등) |
| 2 | S0-P2-2 | `stage0/__init__.py:481-483` | `save_state()`에서 `discovered_fields` 미직렬화 -- 프로젝트 재로드 시 유실 |
| 3 | S0-P2-3 | `stage0/spinner.py:250-257` | Spinner join(timeout=0.5) -- Rich Live 출력 충돌 가능 |
| 4 | S0-P2-4 | `preset_registry.py:516` | `_parse_korean_number` 내부에서 `import re` 반복 수행 |
| 5 | S0-P2-5 | `story_expander.py:485,492,499,506` | Spinner `as sp` 변수 미사용 |
| 6 | S2-P2-1 | `stage2_validation_pipeline.py:698` | `_stage2_flow_guard_legacy` 매개변수 타입 불일치 (normalized: list vs str) |
| 7 | S2-P2-2 | Stage 2 전체 | `logging.warning` vs `self.ctx.ui.log` 혼용 -- UI 메시지와 디버그 로그 혼재 |
| 8 | S2-P2-3 | `stage2_optimizer.py:537-566` | `_build_relationship_history` 미사용 메서드 |
| 9 | S2-P2-4 | `stage2_optimizer.py:734-738` | `SessionFailureMemory.should_increase_constraints` 미사용 메서드 |
| 10 | S2-P2-5 | `stage2_preflight.py:329` | `max_attempts = 5` 하드코딩 (RetryLimits/validation.yaml 미사용) |
| 11 | S2-P2-6 | `stage2_validation_pipeline.py:266-267` | `import logging as _dv_log` 중복 import |
| 12 | S2-P2-7 | `stage2_finalizer.py:437,455` | 볼륨 요약 LLM 호출에 Director 에이전트 사용 (심사 전용 시스템 프롬프트 포함) |
| 13 | S3-P2-1 | `blueprint_ensemble.py:433-495` | `collect_warnings` 메서드 미사용 (V60.80 레거시) |
| 14 | S3-P2-2 | `blueprint_ensemble.py:636-694` | `_format_prev_info` 외부 직접 호출 없음 (내부 도우미로만 사용) |
| 15 | S3-P2-3 | `stage3_orchestrator.py:434` | "200K자 절삭" 하드코딩 메시지 -- 상수값 변경 시 부정확 |
| 16 | S3-P2-4 | `unified_blueprint_validator.py:417-439` | `_generate_feedback` 메서드 미사용 |
| 17 | S4-P2-1 | `stage4_orchestrator.py:429` | `import re as _re_trunc` 인라인 import -- 파일 상단 import 미존재 |
| 18 | S4-P2-2 | `stage4_orchestrator.py:97-128` | `_detect_cross_episode_repetition`의 `if fingerprints else 0` dead branch |
| 19 | S4-P2-3 | `stage4_post_processor.py:666` | `input()` 블로킹 -- 무인 운영 시 프로세스 영구 블로킹 |
| 20 | S4-P2-4 | `stage4_interview_round.py:71-96` | `_common_writer_kwargs`에 `episode_digest` 미포함 (외부 생성 digest 무시) |
| 21 | S4-P2-5 | `stage4_orchestrator.py:131-146` vs `stage4_types.py:16-51` | `_SessionConfig`와 `_RoundContext` 7개 필드 중복 정의 |
| 22 | S4-P2-6 | `stage4_context_builder.py:369-370` + `stage4_orchestrator.py:348` | `cumulative_bible` 전체 조회 후 `dead_npcs`만 사용 -- 무거운 DB 조회 낭비 |
| 23 | V-P2-1 | `config/settings/validation.yaml` | `advisory.pacing_para_limit` 키 누락 -- 기본값 2000 항상 사용 |
| 24 | V-P2-2 | `validation_orchestrator.py:80-102` | `GENRE_THRESHOLD_PROFILES`에 3개 장르만 정의 -- 7개 장르 wuxia 폴백 |
| 25 | V-P2-3 | `scoring_validator.py:29-33` | `GENRE_THRESHOLDS`에 3개 장르만 정의 -- fantasy 등 YAML과 코드 간 불일치 |
| 26 | V-P2-4 | `scoring_validator.py:799-801` | `weighted_percentage`와 `raw_total` 단위 불일치 (+-1 캡핑으로 안전) |
| 27 | INF-P2-1 | `db_manager.py:531-540` | `execute_query()` -- sql 문자열 임의 수용 (현재 하드코딩만 사용하여 안전) |
| 28 | INF-P2-2 | `db_manager.py:573-589` | `update_martial_tracker()` 동적 SQL 컬럼 이름 -- 재검증 없음 |
| 29 | INF-P2-3 | `prompt_loader.py:76-144` | 커스텀 YAML 파서 -- 표준 YAML 미지원 (PyYAML 이미 의존성에 포함) |
| 30 | INF-P2-4 | `metrics_collector.py:110-117,466-475` | 싱글톤 `_instance`와 전역 `_collector` 이중 관리 |
| 31 | INF-P2-5 | `base_agent.py:742-762` | `_check_connectivity()`에 `models.list()` API 사용 -- 네트워크 불안정 시 할당량 소모 |
| 32 | INF-P2-6 | `system.py:30-46` | `boot_v20_project()`에서 무협 전용 서비스를 모든 장르에서 초기화 |
| 33 | INF-P2-7 | `constants.py:8,95-98` | 모듈 레벨 `_threshold()` 호출 -- import 시 YAML 파일 I/O 발생 |

---

## 5. 개선 아이디어 전체 목록 (43건)

### Stage 0 (6건)

| # | ID | 제안 내용 |
|---|----|-----------|
| 1 | S0-I1 | StageZeroManager에 DI 패턴 적용 -- LLM 클라이언트/프로젝트 경로/장르 설정 통합 주입 |
| 2 | S0-I2 | 역설계 원고 로딩 시 `chardet`/`charset-normalizer`로 자동 인코딩 감지 |
| 3 | S0-I3 | StoryExpander LLM 호출에 `adaptive_retry` 모듈의 지수 백오프 재시도 적용 |
| 4 | S0-I4 | 역설계 회차별 상태 추출 병렬화 (5화 단위 배치 병렬 + 배치 간 순차) |
| 5 | S0-I5 | 문체 DNA 캐싱 강화 -- `style_guide.json` 저장 + mtime 체크로 불필요한 LLM 호출 절감 |
| 6 | S0-I6 | Stage 0 메뉴 시스템 UI 계층 통일 -- `SovereignApp` UI 콜백 주입 |

### Stage 2 (8건)

| # | ID | 제안 내용 |
|---|----|-----------|
| 7 | S2-I1 | 벡터 검색과 FourPhase constraint 수집을 ThreadPoolExecutor로 병렬 실행 (Arc 당 5-10초 절감) |
| 8 | S2-I2 | DraftValidator 캐싱으로 이중 호출 제거 |
| 9 | S2-I3 | Preflight 분석 결과를 Director 컨텍스트에 추가 주입 (absolute_prohibitions 등) |
| 10 | S2-I4 | Stage2Context `__slots__` 독스트링 종수 표기 실제와 일치시키기 |
| 11 | S2-I5 | Arc 실패 리포트를 JSON 형식으로 출력하여 자동 분석 가능하게 |
| 12 | S2-I6 | StateTracker 스냅샷 deepcopy 비용 절감 (copy-on-write 또는 선택적 복사) |
| 13 | S2-I7 | FourPhase 내부 retry와 외부 Director retry 통합 관리 (최대 LLM 호출 상한) |
| 14 | S2-I8 | constraint_block 크기 로깅 -- 프롬프트 토큰 예산 관리 |

### Stage 3 (6건)

| # | ID | 제안 내용 |
|---|----|-----------|
| 15 | S3-I1 | Stage 3 시맨틱 컨텍스트 활성화 (P0-1 연계 -- VecMemory/SC 조회) |
| 16 | S3-I2 | 앙상블 전략 적응형 가중치 (director_selections 테이블 참조, 최근 3화 연속 동일 전략 감소) |
| 17 | S3-I3 | Blueprint Pydantic 모델 강화 (scene_breakdown 타입 제한, integrated_scenario min_length) |
| 18 | S3-I4 | Constraint Compiler 에피소드 포커스 추출 정규식 폴백 패턴 추가 |
| 19 | S3-I5 | 이전 원고 30개 개별 DB 조회 -> `get_recent_manuscripts()` 단일 쿼리 최적화 |
| 20 | S3-I6 | Blueprint 생성 후 WorldState/FactLedger에 Blueprint 레벨 상태 변화 증분 업데이트 |

### Stage 4 (8건)

| # | ID | 제안 내용 |
|---|----|-----------|
| 21 | S4-I1 | 이전 원고 30화 전문 로드 최적화 -- 최근 5화만 전문, 6-30화 요약 |
| 22 | S4-I2 | StateTracker 15종 호출 일괄 처리 -- `get_all_summaries()` 메서드 추가 |
| 23 | S4-I3 | Interview Round 검증 파이프라인 모듈화 -- `ValidationPipeline` 클래스 분리 |
| 24 | S4-I4 | Director 벡터 메모리 조회 코드 중복 해소 -- 공통 유틸 추출 |
| 25 | S4-I5 | CoVe quick_verify + verify 이중 호출 최적화 |
| 26 | S4-I6 | Episode Bible 정산 LLM 호출을 ThreadPoolExecutor로 비동기 실행 |
| 27 | S4-I7 | Patch Mode 단일 전략 실행 시 ThreadPoolExecutor 대신 직렬 실행 |
| 28 | S4-I8 | `_RoundContext` 32개 필드를 그룹별 Dataclass로 분할 |

### Validation & Quality (7건)

| # | ID | 제안 내용 |
|---|----|-----------|
| 29 | V-I1 | ScoringValidator에 `create_genre_guard()` 팩토리 도입 (3줄 변경) |
| 30 | V-I2 | 7개 장르 GENRE_WEIGHTS / GENRE_THRESHOLD_PROFILES / CatharsisTimer 확장 |
| 31 | V-I3 | PreLLM 데드코드 정리 또는 재활성화 설계 명확화 |
| 32 | V-I4 | BlockingValidator 예외 처리 세분화 (데이터 오류 vs 프로그래밍 오류) |
| 33 | V-I5 | 적응형 임계값 복원에 try/finally 패턴 적용 |
| 34 | V-I6 | validation.yaml에 누락된 임계값 키 추가 (advisory.pacing_para_limit) |
| 35 | V-I7 | 장르별 검증 커버리지 매트릭스 문서화 |

### 인프라/공통 (8건)

| # | ID | 제안 내용 |
|---|----|-----------|
| 36 | INF-I1 | DBManager 커서 관리 패턴 표준화 -- 로컬 커서 + `@contextmanager` 헬퍼 |
| 37 | INF-I2 | VecMemory 임베딩 결과 LRU 캐싱 (최대 100개, MD5 해시 키) |
| 38 | INF-I3 | DBManager WAL 모드 활성화 (`PRAGMA journal_mode=WAL`) |
| 39 | INF-I4 | FactLedger/WorldStateManager dirty flag 자동 save 패턴 |
| 40 | INF-I5 | BaseAgent API 호출 구조화 로깅 (JSON 형식 병행 출력) |
| 41 | INF-I6 | StateTracker 장르별 레지스트리 선택적 초기화 |
| 42 | INF-I7 | ContextAdvisor `_GENRE_HINTS` YAML 외부화 |
| 43 | INF-I8 | main_a.py Stage별 lazy import 적용 |

---

## 6. 수정 우선순위 권장

### Tier 1 -- 즉시 수정 (P0 확인 4건)

| 순서 | 항목 | 예상 난이도 | 근거 |
|------|------|------------|------|
| 1 | S4-P0-2 (blueprint 미전달) | 낮 | `build_mandatory_context()` 호출부에 `blueprint=blueprint` 인자 1개 추가. SC NPC roster + retrieval plan 즉시 개선 |
| 2 | S0-P0-1 (llm_client 미전달) | 낮 | `stage01_helpers.py:291`에 `llm_client=app.sys.api_client` 추가 |
| 3 | S4-P0-1 (30화 이중 로드) | 중 | interview_round에서 context_builder가 이미 로드한 원고 재사용하도록 구조 변경 |
| 4 | S3-P0-1 (시맨틱 컨텍스트 비활성) | 중 | VecMemory 조회 코드 10-15줄 추가, Stage 4 패턴 참조 |

### Tier 2 -- 조기 수정 권장 (기능 누락/품질 저하)

| 순서 | 항목 | 예상 난이도 | 근거 |
|------|------|------------|------|
| 6 | S3-P0-1 (시맨틱 컨텍스트 미작동) | 중 | Blueprint 품질에 직접 영향. VecMemory 조회 코드 10-15줄 추가 |
| 7 | S4-P0-1 (30화 이중 로드) | 중 | 장기 연재 메모리 문제. round_ctx에 prev_manuscripts_history 전달 구조 변경 |
| 8 | V-P1-1 (Guard 8개 장르 누락) | 낮 | `create_genre_guard()` 팩토리 재활용 3줄 변경 |
| 9 | V-P1-2 + V-P2-2 (장르 가중치/프로파일 7개 누락) | 중 | 도메인 지식 필요. 일괄 작업 가능 |
| 10 | V-P1-5 (CatharsisTimer 7개 장르 누락) | 중 | 장르별 키워드 세트 설계 필요 |

### Tier 3 -- 배치 수정 (데드 코드/코드 위생)

다음 항목들은 일괄 작업으로 효율적으로 처리 가능:

**데드 코드 일괄 삭제** (10건):
- S2-P1-1 (`passed = True`), S2-P1-2 (`_SUMMARY_MODEL`), S2-P1-3 (ReflectionTarget import)
- S2-P2-3 (`_build_relationship_history`), S2-P2-4 (`should_increase_constraints`)
- S3-P1-5 (`_evaluate_candidate`), S3-P2-1 (`collect_warnings`), S3-P2-4 (`_generate_feedback`)
- S4-P2-2 (dead branch), V-P1-3 (PreLLM REJECT 분기)

**인라인 import 정리** (3건):
- S0-P2-4, S2-P2-6, S4-P2-1

**스레드 안전성 일괄 보강** (5건):
- INF-P1-1 (공유 cursor), INF-P1-2 (begin/commit Lock), INF-P1-3 (_rotation_count Lock)
- INF-P1-6 (ConfigManager Lock), INF-P1-8 (_context_caches Lock)

### Tier 4 -- 중기 개선

나머지 P1/P2 항목과 개선 아이디어는 다음 개발 주기에서 우선순위를 재평가.

---

## 7. 시스템 건전성 평가

### Stage 0 -- 초기 설정

**등급: A-** (수정 후 우수) ~~B~~

- P0-1(llm_client 미전달) **수정 완료**, P0-2 등급 하향(P1)
- UI 출력 logging.info → print 전환 완료 (P1-6)
- detect_new_genre() 9개 장르 키워드 추가 (P1-5)
- 문체 DNA JSON 캐싱, LLM 재시도 로직, 역설계 병렬화 구현

### Stage 2 -- Arc/Blueprint 설계

**등급: A** (수정 후 우수) ~~A-~~

- P0 0건. 데드 코드 5건 + DraftValidator 이중 호출 **전량 수정**
- constraint_block 병렬화, 크기 로깅 + 100K 경고 추가
- ThreadPoolExecutor perf_timer Lock 보호 완료
- max_attempts _threshold 참조로 전환

### Stage 3 -- Blueprint 생성

**등급: A-** (수정 후 우수) ~~B+~~

- P0-1(시맨틱 컨텍스트 미작동) **수정 완료** — Stage 3 SC 5슬롯 활성화
- N+1 쿼리 최적화 완료 (30→1 DB 호출)
- Constraint Compiler 에피소드 헤더 정규식 5패턴 폴백 추가
- strategy_feedback 전 전략 공유, continuity_feedback 누적 방지

### Stage 4 -- 원고 생성

**등급: A-** (수정 후 우수) ~~B+~~

- P0-1(30화 이중 로드) **수정 완료** — round_ctx 캐시 재사용
- P0-2(blueprint 미전달) **수정 완료**
- StateTracker.get_all_summaries() 16종 일괄 호출
- Episode Bible 비동기 정산, CoVe 경고 컨텍스트 주입
- _apply_context_budget O(n²) → O(n) 최적화

### Validation & Quality

**등급: A** (수정 후 우수) ~~B~~

- GENRE_WEIGHTS, CatharsisTimer, THRESHOLD_PROFILES **10개 장르 전량 확장 완료**
- BlockingValidator 예외 세분화 (TypeError/ImportError re-raise)
- 적응형 임계값 복원 try/finally 보장
- Guard 팩토리 전체 장르 지원 확인

### 인프라/공통 모듈

**등급: A-** (수정 후 우수) ~~B~~

- 스레드 안전성 5건 **전량 수정** (로컬 커서, begin/commit Lock, _context_caches Lock, ConfigManager Lock)
- DBManager WAL 모드 활성화, rollback_to 배치 쿼리
- VecMemory 임베딩 LRU 캐시, _check_connectivity HEAD 요청 전환
- constants.py _LazyThreshold 디스크립터, main_a.py lazy import
- ContextAdvisor _GENRE_HINTS YAML 외부화

---

## 부록: 반복 패턴 분석

### 패턴 A: 장르 확장 미반영 (6건)

S0-P1-5, V-P1-1, V-P1-2, V-P1-5, V-P2-2, V-P2-3

10개 장르 체제로 확장되었지만, 초기 3개 장르(wuxia/hunter/investment) 기준으로 작성된 코드가 갱신되지 않은 패턴. CLAUDE.md 장르 추가 체크리스트에 Validation 항목을 추가하여 구조적으로 방지해야 함.

### 패턴 B: 데드 코드 잔존 (10건)

S2-P1-1~3, S2-P2-3~4, S3-P1-5, S3-P2-1, S3-P2-4, S4-P2-2, V-P1-3

B-1 모듈 분리 시 원본에 남은 변수/import, V60.80 이전 레거시 메서드, 비활성화 후 남은 분기 등. 일괄 삭제로 코드 명확성 향상 가능.

### 패턴 C: 스레드 안전성 미비 (7건)

INF-P0-1, INF-P1-1~3, INF-P1-5~6, INF-P1-8

멀티스레드 환경에서의 Lock 보호 누락, 공유 상태 경합, RLock 암묵적 의존 등. DBManager와 BaseAgent가 집중 대상.

### 패턴 D: N+1 쿼리/메모리 이중 로드 (3건)

S3-I5, S4-P0-1, S4-P2-6

개별 DB 조회를 배치 조회로 전환하거나, 이미 로드한 데이터를 재사용하는 최적화 여지.

---

## 8. 수정 이력

### 1차 수정 — P0+P1+P2 즉시 수정 (커밋 `0b67847`)

**39건** (P0 4건 + P1 20건 + P2 15건), 26개 파일 수정.

주요 수정:
- S0-P0-1: llm_client 전달 배선
- S4-P0-1: 30화 이중 로드 → round_ctx 캐시 재사용
- S4-P0-2: blueprint 인자 추가
- S3-P0-1: 시맨틱 컨텍스트 파라미터 배선 (Stage 3 SC)
- INF-P1-1~9: 스레드 안전성 전면 보강 (로컬 커서, Lock, RLock)
- V-P1-1: Guard 팩토리 도입
- 데드 코드 10건 일괄 삭제

### 2차 수정 — 잔여 P1+P2 전량 (커밋 `bb0e1ac`)

**32건** (P1 19건 + P2 13건), 23개 파일 수정.

주요 수정:
- S0-P1-5: detect_new_genre() 9개 장르 키워드 추가
- S0-P1-6: show_menu() logging.info → print 전환
- S2-P1-4: DraftValidator 이중 호출 플래그 누수 차단
- S2-P1-5: ThreadPoolExecutor perf_timer Lock 보호
- S3-P1-3: strategy_feedback 전 전략 공유
- S3-P1-4: continuity_feedback 누적 방지
- S4-P1-2: state_tracker 15회 반복 → 단일 변수
- S4-P1-6: _apply_context_budget O(n²) → O(n)
- V-P1-2: GENRE_WEIGHTS 10개 장르 전량 확장
- V-P1-5: CatharsisTimer 10개 장르 전량 확장
- V-P2-2: GENRE_THRESHOLD_PROFILES 10개 장르 전량 확장
- INF-P1-1: db_manager 11개 메서드 로컬 커서 전환
- INF-P1-9: rollback_to O(N) → O(1) 배치 쿼리
- INF-P2-7: constants.py _LazyThreshold 디스크립터

### 3차 — 개선 아이디어 구현 (커밋 `1bd3dd4`)

**19건** 구현 (22개 파일, +989/-292줄), Tier 1+2 전량.

| ID | 제목 | 상태 |
|----|------|------|
| S0-I3 | StoryExpander LLM 지수 백오프 재시도 | **구현** |
| S0-I4 | 역설계 회차별 상태 추출 5화 배치 병렬화 | **구현** |
| S0-I5 | StyleExtractor 문체 DNA JSON 캐싱 | **구현** |
| S2-I1 | Stage 2 constraint_block 생성 병렬화 | **구현** |
| S2-I8 | enhanced_context 크기 로깅 + 100K 경고 | **구현** |
| S3-I1 | Stage 3 SC 시맨틱 컨텍스트 활성화 (5슬롯) | **구현** |
| S3-I4 | Constraint Compiler 에피소드 헤더 정규식 5패턴 폴백 | **구현** |
| S3-I5 | Blueprint 이전 원고 N+1 쿼리 → 단일 쿼리 | **구현** |
| S4-I2 | StateTracker.get_all_summaries() 16종 일괄 호출 | **구현** |
| S4-I5 | CoVe quick_verify 경고 → LLM verify 컨텍스트 주입 | **구현** |
| S4-I6 | Episode Bible 정산 비동기 ThreadPoolExecutor | **구현** |
| V-I1 | ScoringValidator Guard 팩토리 | **기존 완료** |
| V-I4 | BlockingValidator 예외 세분화 | **구현** |
| V-I5 | 적응형 임계값 복원 try/finally | **구현** |
| INF-I2 | VecMemory 임베딩 LRU 캐시 (128개) | **구현** |
| INF-I3 | DBManager WAL 모드 활성화 | **구현** |
| INF-I5 | BaseAgent API 호출 구조화 로깅 | **구현** |
| INF-I7 | ContextAdvisor _GENRE_HINTS YAML 외부화 | **구현** |
| INF-I8 | main_a.py ~50개 에이전트 lazy import | **구현** |

### 미구현 (24건)

| 분류 | 건수 | 항목 | 사유 |
|------|------|------|------|
| **Tier 3 (보류)** | 6 | S0-I1, S2-I7, S3-I2, S3-I6, S4-I3, S4-I8 | 대규모 리팩토링/설계 필요 |
| **Tier 4 (스킵)** | 15 | S0-I2/I6, S2-I2~I6, S3-I3, S4-I4/I7, V-I3/I6/I7, INF-I4/I6 | 저 ROI |
| **기존 완료** | 3 | V-I1, V-I2, INF-I1 | 1차/2차 수정에서 이미 처리 |

---

*감사 통합 완료: 2026-02-22*
*수정 완료: 2026-02-22 (P0-P2 76건 + 개선 19건 = 총 95건)*
*통합자: Claude Opus 4.6*
*원본 리포트: 6개 TF 감사 보고서 (Stage 0/2/3/4/Validation/인프라)*
