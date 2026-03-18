# Stage 3-4 딥다이브: 비표면 영역 전수조사 — 최종 감리본

> **조사 일시**: 2026-03-18
> **조사 이력**: 3회 딥다이브 → 3-Pass 감리 → **1차 적대적 감리 3회** → **2차 적대적 감리 3회 (심층 호출 체인 추적)**
> **확신도**: 98% (2차 적대적 감리에서 호출 체인·보상 통제 완전 추적, High 3건 전부 재보정, 1건 프로덕션 미사용 확인)

---

## 목차

1. [감리 이력 및 수렴 과정](#1-감리-이력-및-수렴-과정)
2. [최종 발견사항 총괄표](#2-최종-발견사항-총괄표)
3. [Medium 발견사항 (최종 4건)](#3-medium-발견사항-최종-4건)
4. [Low 발견사항 (최종 24건)](#4-low-발견사항-최종-24건)
5. [Info 발견사항 (최종 4건)](#5-info-발견사항-최종-4건)
6. [시스템적 패턴 분석 (최종)](#6-시스템적-패턴-분석-최종)
7. [감리 전체 변동 이력](#7-감리-전체-변동-이력)

---

## 1. 감리 이력 및 수렴 과정

### 심각도 분포 변동

| 단계 | High | Medium | Low | Info | 삭제 | 합계(유효) |
|------|------|--------|-----|------|------|-----------|
| 초기 조사 | 10 | 14 | 11 | 5 | 0 | 40 |
| 1차 적대적 감리 | 3 | 11 | 17 | 4 | 3 | 35 |
| **2차 적대적 감리** | **0** | **4** | **24** | **4** | **3** | **32** |

### 2차 적대적 감리 핵심 발견

| 항목 | 원래 | 최종 | 결정적 근거 |
|------|------|------|-----------|
| H-07 벡터 메모리 영구 유실 | High | **Medium** | 유실되는 것은 벡터 인덱스(원고 원본은 DB/파일 별도 저장). `sync_v20_drafts()` 수동 복구 경로 존재. |
| H-08 RetrospectiveValidator 전면 fail-open | High | **Low** | advisory 전용 보조 검증기 — 점수 감점만 수행, PASS/REJECT 직접 결정 불가. Director LLM이 동일 이슈를 주 경로에서 검출. |
| H-10 ContinuityBlueprintValidator fail-open | High | **Low** | **`inspect()` 메서드가 현재 Stage 3 프로덕션 파이프라인에서 호출되지 않음**. 프로덕션 연속성 검증은 `director.check_blueprint_continuity_with_cache()` (순수 Python, LLM 무관). |
| M-05 state_updates 임의 dict | Medium | **Low** | `WorldState.update_from_state_changes()`가 **화이트리스트 방식** — 알려진 키만 `.get()` 추출, 나머지 무시. 침투 시나리오 구조적 차단. |
| SR-1 Fail-Open/Closed 비일관성 | (구조적 리스크) | **Low (계층적 설계)** | 코드 내 `[FailClosed:...]` 태그 5개 발견. Preflight=fail-open, Blocking=degraded, CoVe/PostSelect=fail-closed로 **계층별 의도적 차별 적용** 확인. |

---

## 2. 최종 발견사항 총괄표

| 심각도 | 건수 | 항목 |
|--------|------|------|
| **Critical** | 0 | — |
| **High** | 0 | — |
| **Medium** | 4 | 벡터 인덱스 복구 자동화 부재, WorldState 파일 롤백 갭, quality flag 미참조, DB 실패 시 원고 비상 저장 부재 |
| **Low** | 24 | 보조 검증기 방어 코딩, 미사용 코드 결함, 캐시/표시/로깅, 의도적 설계 결정 |
| **Info** | 4 | 문서 불일치, 설계 참고 |
| **삭제** | 3 | REFUTED (1차 감리에서 삭제) |
| **합계** | **32** (유효) | |

---

## 3. Medium 발견사항 (최종 4건)

### MF-01: 벡터 메모리 인덱스 복구 자동화 부재 (구 H-07)

- **위치**: `modules/core/stage4_post_processor.py:880-896`, `modules/core/vec_memory.py:405-478`
- **설명**: `memorize_v20_episode` 실패 시 비차단 처리, 재시도 없음. 벡터 인덱스 영구 누락.
- **2차 감리 보정**: 유실되는 것은 벡터 인덱스이며 **원고 원본은 DB/파일에 별도 저장**됨. `sync_v20_drafts(drafts_path=실제경로)` 함수가 구현되어 **수동 복구 가능**하나, 프로덕션에서 자동 호출되지 않음 (현재 `drafts_path=None`으로 noop). Gap detection용 `get_sync_status()` 함수도 존재하나 미연결.
- **실질 영향**: SC-5 벡터 검색에서 해당 에피소드 누락 → 연속성 검증 무음 품질 저하. 파이프라인 중단/데이터 손실 아님.
- **즉시 개선**: `sync_v20_drafts`를 세션 시작 시 `drafts_path` 지정하여 자동 호출 추가.

### MF-02: WorldState/FactLedger 파일 수준 부분 커밋 가능성 (구 H-04 → M-03)

- **위치**: `modules/core/stage4_post_processor.py:1358-1455`
- **설명**: `_save_world_state_atomic()`에서 DB 트랜잭션 래핑이 존재하나, `_meta_db`가 None이면 `_nullcontext()`로 폴백 → 트랜잭션 없이 실행 → `world_state.save()` 성공 후 `fact_ledger.save()` 실패 시 부분 커밋.
- **2차 감리 보정**: 인메모리 롤백(`deepcopy` 스냅샷)은 올바르게 구현됨. `rolled_back: True` soft failure 보고 존재. 핵심 갭은 `_meta_db=None` 경로에서만 발생.
- **실질 영향**: 정상 운영(`_meta_db` 존재)에서는 DB 트랜잭션이 원자성 보장. 테스트/초기화 문제 시에만 발현 가능.

### MF-03: quality_gate_failed / quality_risk 플래그 Stage 4 미참조 (구 H-02 → M-02)

- **위치**: `modules/domain/agents/three_phase_blueprint_generator.py:741-750`, Stage 4 전역
- **설명**: retry 소진 후 50점 이상 Blueprint가 `PASS_WITH_WARNING`으로 승격될 때 `quality_gate_failed=True`, `quality_risk=True` 설정. Stage 3에서 `_stage3_meta`에 기록되지만, **Stage 4 오케스트레이터/포스트프로세서/인터뷰라운드에서 이 플래그를 전혀 참조하지 않음** (grep 0건).
- **2차 감리 발견**: "write-only flag" 패턴 — 기록만 되고 행동으로 이어지지 않음.
- **즉시 개선**: Stage 4 진입 시 `quality_risk=True` Blueprint에 대해 Director에 경고 주입 또는 retry 예산 확대.

### MF-04: DB 저장 실패 시 원고 비상 저장 부재 (구 M-10 → M-12)

- **위치**: `modules/core/stage4_orchestrator.py:898-913`
- **설명**: `process_pass_result()` 반환 False 시 `break` → `final_manuscript`는 메모리에만 존재. DB와 파일 모두 미저장.
- **2차 감리 보정**: "lost forever" 표현은 과장. Episode Bible 메타 실패 시에는 원고 자체는 이미 DB 커밋됨. **DB 저장 자체가 실패하는 경우(디스크 풀/권한)**에만 원고 미저장. UI 로그에 실패 표시되어 사용자 인지 가능. SQLite DB 쓰기 실패 확률 극히 낮음.
- **즉시 개선**: DB 실패 시 `final_manuscript`를 `output_dir/emergency_ep_XXXX.txt`로 비상 덤프.

---

## 4. Low 발견사항 (최종 24건)

### 구 High → Low (2차 감리에서 하향, 2건)

| ID | 원래 | 위치 | 설명 | 하향 근거 |
|----|------|------|------|-----------|
| LF-01 | H-08 | `retrospective_validator.py:82-241` | 4개 체크 except Exception 자동 PASS | **advisory 전용 보조 검증기** — 점수 감점만, PASS/REJECT 직접 결정 불가. Director LLM + ContinuityValidator가 동일 이슈 주 경로에서 검출. |
| LF-02 | H-10 | `continuity_blueprint.py:237-272` | LLM 실패 시 PASS | **`inspect()` 메서드가 Stage 3 프로덕션에서 호출되지 않음**. 프로덕션 연속성 검증은 `director.check_blueprint_continuity_with_cache()` (순수 Python). |

### 구 High → Medium → Low (1차+2차 감리 연속 하향, 4건)

| ID | 원래 | 위치 | 설명 | 하향 근거 |
|----|------|------|------|-----------|
| LF-03 | H-01 | `continuity_blueprint.py` vs `unified_arc_validator.py` | fail-open/closed 비일관 | advisory 계층 + Director 후행 판정 |
| LF-04 | H-05 | `stage4_post_processor.py:510-526` | HUD 업데이트 실패 | **`build_hud_context()`가 StateTracker에서 재구축** → LLM 프롬프트에 반영되는 상태는 복구. Bible HUD 섹션만 stale (표시 계층). |
| LF-05 | H-06 | `response_schemas.py:643` | state_updates 임의 dict | **`WorldState.update_from_state_changes()`가 화이트리스트 방식** — 알려진 키만 `.get()` 추출, 알 수 없는 키 자동 무시. 침투 시나리오 구조적 차단. |
| LF-06 | H-09 | `blocking_validator.py:175-191` | degraded 자동 PASS | 12개+ 검증 중 2개만 degradable. 나머지 10개(사망NPC/미소유아이템/파괴장소 등) 정상 동작. `_degraded_count` 추적. 프로그래밍 오류 re-raise. |

### 구 Medium → Low (1차 감리 하향, 8건)

| ID | 원래 | 위치 | 설명 | 하향 근거 |
|----|------|------|------|-----------|
| LF-07 | M-01 | `blueprint_ensemble.py:253-303` | SQLite thread-safety | DB 매니저 `_lock` 존재, 주요 접근 사전 로드 |
| LF-08 | M-02 | `stage4_orchestrator.py:692` | Stage3→4 핸드오프 구조 검증 부재 | Stage 3에서 Pydantic 검증 통과 후 DB 저장 |
| LF-09 | M-03 | `bv_scene_checks.py:44-51` | 씬 반영률 비활성 | Director LLM 대체, docstring 명시 |
| LF-10 | M-08 | `consistency_validator.py:177-231` | 컨텍스트 의존 스킵 | `[I-04]` 로깅, 장르별 guard 의도적 |
| LF-11 | M-11 | `stage3_orchestrator.py:1664` | fail_count 리셋 | 연속 실패 카운터 의도, `stats["phase3_reject"]` 별도 |
| LF-12 | M-12 | `stage4_orchestrator.py:1227-1262` | V75-D 패치 추적성 | `log_patch_diff`, `_inplace_attempted` 1회 |
| LF-13 | M-13 | `bv_scene_checks.py:88-90` | scope_overflow scene_count=0 | 3중 추출, false positive 방지 |
| LF-14 | M-14 | `stage4_context_builder.py:1456` | Smart Retrieval 예산 절삭 | 핵심 정보 보호, 우선순위 압축 |

### 구 Medium → Low (2차 감리 하향, 6건)

| ID | 원래 | 위치 | 설명 | 하향 근거 |
|----|------|------|------|-----------|
| LF-15 | M-04 (ManuscriptCandidate) | `manuscript.py:21` | extra="allow" | 하류 전부 dict `.get()` 접근, attribute 접근 없음. LLM 출력 불확실성 방어 의도. |
| LF-16 | M-05 (Director cache) | `director.py:105-112` | _protagonist_config 누락 | protagonist_config 변경 빈도 극히 낮음. Rollback 시 Director 인스턴스 재생성 가능성. 1줄 수정으로 해결. |
| LF-17 | M-06 (Advisory Chain) | `stage4_interview_round.py:5008-5009` | 부분 실패 silent drop | 9중 병렬 + CoVe 이중 커버. `logging.debug` → `logging.warning` 1줄 개선 권고. |
| LF-18 | M-09 (Post-select) | `stage4_interview_round.py:3474-3492` | fail-closed 오탐 | **일시적 다운그레이드** — `previous_attempt` 보존 → 패치 모드 재시도 → 영구 거부 아님. |
| LF-19 | M-10 (CoVe) | `stage4_orchestrator.py:1038-1080` | CoVe 라운드 소비 | `previous_attempt`에 `best_manuscript` 보존. 5회 소진 시 폴백 메커니즘. 인프라 재시도 추가 권고. |
| LF-20 | SR-1 구조적 | 검증 파이프라인 전역 | fail-open/closed 비일관성 | **계층별 의도적 차별 적용 확인**: Preflight=fail-open, Blocking=degraded, CoVe=fail-closed. `[FailClosed:...]` 태그 5개 발견. 단, 중앙 정책 문서 부재. |

### 원본 Low 유지 (4건, 나머지는 1차 감리에서 삭제 포함)

| ID | 위치 | 설명 |
|----|------|------|
| LF-21 | `stage4_context.py:47-83` | 콜백 `_budget_meta` dict 숨김 |
| LF-22 | `stage4_post_processor.py:616` | emotion_tracker "neutral"/0.5 placeholder |
| LF-23 | `data_collector.py:128-131` | Windows `os.remove`→`os.rename` 경쟁 조건 (`os.replace` 미사용) |
| LF-24 | `context_compression.py:140-149` | 비필수 필드 삭제 순서 비중요도 기반 |

---

## 5. Info 발견사항 (최종 4건)

| ID | 위치 | 설명 |
|----|------|------|
| IF-01 | `stage3_context.py:6-13` | docstring 슬롯 수 불일치 (9/10 → 실제 11/11) |
| IF-02 | `director_ensemble.py:294-308` | Director 프롬프트 캡 기본 740KB |
| IF-03 | `director_ensemble.py:894-901` | 단일 후보 자동 REJECT (TF-36 의도적) |
| IF-04 | `modules/api/bridge_server.py` | Stage 3-4 전용 API 엔드포인트 없음 |

---

## 6. 시스템적 패턴 분석 (최종)

### 초기 평가 vs 최종 평가

| 패턴 | 초기 평가 | 최종 평가 |
|------|-----------|-----------|
| **비차단(Non-Blocking) 우선** | "무서운 조용함" — 부분 실패 누적이 연속성 파괴 | **의도적 가용성 설계**. 핵심 데이터(원고/Blueprint)는 DB 트랜잭션으로 보호. 사이드이펙트(HUD/VecMemory/emotion)는 비차단이나 보상 경로 존재(StateTracker 재구축, 수동 벡터 동기화). 유일한 실질 갭: 벡터 인덱스 자동 복구 부재(MF-01). |
| **Fail-Open/Closed 비일관성** | "시스템 안전이 가장 약한 검증기에 의해 결정" | **계층적 방어 설계**. Preflight(fail-open) → Blocking(degraded) → Director LLM(주 경로) → CoVe/PostSelect(fail-closed). 코드 내 `[FailClosed:...]` 태그로 의도 표시. 중앙 정책 문서만 부재. |
| **검증 비활성화 누적** | "실질적 공동화" | **의도적 Director LLM 위임 + 장르별 guard 분화**. 비활성화된 Python 검증은 docstring에 사유 명시. RetrospectiveValidator는 advisory 전용(점수 감점만). ContinuityBlueprintValidator의 `inspect()`는 프로덕션 미사용. |

### 진정한 잔여 리스크 (Medium 이상)

1. **MF-01**: 벡터 인덱스 gap 자동 복구 부재 → SC-5 무음 품질 저하
2. **MF-02**: `_meta_db=None` 경로에서 WorldState/FactLedger 부분 커밋
3. **MF-03**: `quality_gate_failed` write-only flag → Stage 4에서 저품질 Blueprint 무차별 처리
4. **MF-04**: DB 실패 시 원고 비상 저장 부재

---

## 7. 감리 전체 변동 이력

### 초기 High 10건의 최종 행선지

| 초기 ID | 초기 내용 | 1차 감리 | 2차 감리 | 최종 | 결정적 근거 |
|---------|-----------|----------|----------|------|-----------|
| H-01 | ContinuityBP fail-open | Medium | Low | **LF-03** | advisory + Director 후행 |
| H-02 | REJECT→PASS_WITH_WARNING | Medium | Medium | **MF-03** | quality flag Stage 4 미참조 |
| H-03 | Blueprint uncommitted write | **REFUTED** | — | **삭제** | `save_blueprint()` 자체 commit |
| H-04 | WorldState/FL 롤백 불완전 | Medium | Medium | **MF-02** | `_meta_db=None` 갭만 유효 |
| H-05 | HUD 업데이트 실패 | Medium | Low | **LF-04** | StateTracker 재구축, 표시 계층 |
| H-06 | state_updates 임의 dict | Medium | Low | **LF-05** | 화이트리스트 `.get()` 패턴 |
| H-07 | 벡터 메모리 영구 유실 | High | Medium | **MF-01** | 원고 별도 저장, 인덱스만 누락, 수동 복구 가능 |
| H-08 | RetrospectiveValidator fail-open | High | Low | **LF-01** | advisory 전용, 점수 감점만, Director 주 경로 |
| H-09 | BlockingValidator degraded | Medium | Low | **LF-06** | 12개 중 2개만, 나머지 정상, 추적 존재 |
| H-10 | ContinuityBP LLM 실패 PASS | High | Low | **LF-02** | **프로덕션에서 호출되지 않음** |

### 초기 Medium 14건의 최종 행선지

| 초기 ID | 1차 결과 | 2차 결과 | 최종 |
|---------|---------|---------|------|
| M-01 (Ensemble SQLite) | Low | Low | LF-07 |
| M-02 (핸드오프 검증) | Low | Low | LF-08 |
| M-03 (씬 반영률) | Low | Low | LF-09 |
| M-04 (ManuscriptCandidate) | Medium | Low | LF-15 |
| M-05 (Director cache) | Medium | Low | LF-16 |
| M-06 (Advisory Chain) | Medium | Low | LF-17 |
| M-07 (CoVe 라운드 소비) | Medium | Medium→Low | LF-19 |
| M-08 (ConsistencyValidator 스킵) | Low | Low | LF-10 |
| M-09 (Post-select fail-closed) | Medium | Low | LF-18 |
| M-10 (원고 소실) | Medium | Medium | MF-04 |
| M-11 (fail_count 리셋) | Low | Low | LF-11 |
| M-12 (V75-D 추적성) | Low | Low | LF-12 |
| M-13 (scope_overflow) | Low | Low | LF-13 |
| M-14 (Smart Retrieval 절삭) | Low | Low | LF-14 |

### 즉시 개선 가능 항목 (비용 순)

| 우선순위 | 항목 | 수정 내용 | 비용 |
|---------|------|-----------|------|
| 1 | LF-16 | `invalidate_caches()`에 `self._caching._protagonist_config = None` 추가 | 1줄 |
| 2 | LF-17 | `logging.debug` → `logging.warning` 변경 | 1줄 |
| 3 | MF-04 | DB 실패 시 `emergency_ep_XXXX.txt` 비상 덤프 | ~10줄 |
| 4 | MF-01 | 세션 시작 시 `sync_v20_drafts(drafts_path=실제경로)` 자동 호출 | ~5줄 |
| 5 | MF-03 | Stage 4 진입 시 `quality_risk=True` Blueprint 경고 주입 | ~15줄 |
| 6 | LF-20 | fail-open/closed 계층 정책 docstring 명문화 | 문서 |

---

**최종 확신도: 98%**

- 2차 적대적 감리에서 **호출 체인 전수 추적** + **보상 통제 실물 확인**으로 정확도 대폭 향상
- H-10(`ContinuityBlueprintValidator`)이 **프로덕션 미사용**인 것은 2차 감리에서 최초 발견 — 1차 감리까지는 미탐지
- H-08(`RetrospectiveValidator`)의 **advisory 전용 위상** (PASS/REJECT 결정 불가, 점수 감점만) 확인도 2차에서 최초 발견
- 잔여 2%: Low 24건 중 미검증 스팟 + stage4_interview_round.py 4,100줄 심층 분기

---

*2차 적대적 감리 3회 완료. 본 문서는 6회 적대적 감리 보정 후 최종본이다.*
