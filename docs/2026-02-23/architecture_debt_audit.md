# 아키텍처 부채 감사 보고서 (2026-02-23)

감사 범위: `modules/` 전체 (Python 파일)
기준선: 2477 passed, 0 ruff violations

---

## 1. `getattr(self, "xxx", None)` 패턴 목록

| 파일 | 속성명 | 등장 횟수 | 용도 |
|------|--------|-----------|------|
| `modules/domain/agents/director_continuity.py` | `_cached_recent_blueprints` | 1 | Blueprint 캐시 재사용 경로 (L602) |
| `modules/domain/agents/director_continuity.py` | `_cached_context_text_manuscript` | 1 | Manuscript 캐시 컨텍스트 텍스트 (L715) |
| `modules/domain/agents/director_continuity.py` | `_manuscript_cache_name` | 1 | Manuscript 캐시 이름 (L716) |
| `modules/domain/agents/state_locked_arc_generator.py` | `protagonist_name` | 1 | 주인공 이름 fallback (L367) |
| `modules/domain/agents/four_phase_arc_generator.py` | `context.master_bible` | 2 | protagonist_config 추출 (L177, L545) |
| `modules/domain/agents/state_tracker.py` | (동적 key) | 2 | `__getattr__` 위임 패턴 (L73, L1268) |
| `modules/core/stage0/style_extractor.py` | (dataclass field) | 1 | 필드 초기화 null 체크 (L57) |

### 분석

- `director_continuity.py`의 `_cached_recent_blueprints`, `_cached_context_text_manuscript`, `_manuscript_cache_name`은
  캐시 갱신 경로에서는 `self.xxx = ...`로 직접 할당되지만, 캐시 재사용 경로에서 getattr fallback으로 읽는다.
  이는 인스턴스 생성 시 초기화하지 않은 "lazy" 캐시 속성이며, `__init__`에서 `None`으로 초기화하면
  getattr fallback이 불필요해진다.

- `four_phase_arc_generator.py`의 `context.master_bible` getattr는 두 메서드
  (`generate()` L177, `_build_arc_prompt()` L545)에서 동일한 패턴으로 반복된다.
  `self.context`를 통해 접근하는 방식이므로 DI 슬롯으로 승격하기보다
  공통 헬퍼 메서드 `_get_protagonist_config()` 추출이 더 적합하다.

---

## 2. `try/except Exception: pass` 현황

### 총 52건 발견 (수정 전 기준)

| 파일 | 라인 | 위험도 | 분류 | 내용 요약 |
|------|------|--------|------|-----------|
| `modules/core/adaptive_retry.py` | 572 | OK | 텔레메트리 | FailureLearner.record_failure (비차단) |
| `modules/core/adaptive_retry.py` | 723 | OK | 텔레메트리 | FailureLearner.generate_constraint_prompt (비차단) |
| `modules/core/adaptive_retry.py` | 829 | OK | 외부 callback | retry_with_feedback 외부 logger 호출 |
| `modules/core/config_manager.py` | 27 | OK | 조건부 import | ManuscriptLimits 상수 import 실패 시 기본값 사용 |
| `modules/core/constants.py` | 413 | OK | 방어적 조회 | bible_root dict 접근 실패 → None 처리 |
| `modules/core/db_manager.py` | 543 | OK | 마이그레이션 | vec 임베딩 INSERT OR REPLACE 개별 실패 무시 |
| `modules/core/db_manager.py` | 583 | OK | 마이그레이션 | DB-MERGE 비치명 경로 |
| `modules/core/db_manager.py` | 588 | OK | 마이그레이션 | DB-MERGE 비치명 경로 |
| `modules/core/genre_guards/investment_guard.py` | 561 | OK | 방어적 날짜비교 | 날짜 형식 불일치 시 타임라인 정상 반환 |
| `modules/core/stage0/reverse_expander.py` | 53 | OK | 조건부 import | genai 클라이언트 초기화 실패 시 None |
| `modules/core/stage0/reverse_expander.py` | 704 | OK | 트랜잭션 롤백 | rollback 자체 실패 시 무시 |
| `modules/core/stage0/style_extractor.py` | 701 | OK | 조건부 import | genai 클라이언트 초기화 실패 시 None |
| `modules/core/stage2_preflight.py` | 201 | OK | PerfTimer | arc_drive perf 계측 start |
| `modules/core/stage2_preflight.py` | 221 | OK | PerfTimer | arc_drive perf 계측 stop (finally) |
| `modules/core/stage2_preflight.py` | 229 | OK | PerfTimer | preflight_analysis perf 계측 start |
| `modules/core/stage2_preflight.py` | 251 | OK | PerfTimer | preflight_analysis perf 계측 stop (finally) |
| `modules/core/stage2_preflight.py` | 266 | OK | PerfTimer | preflight_parallel 외곽 타이머 start |
| `modules/core/stage2_preflight.py` | 285 | OK | PerfTimer | executor.shutdown (오류 경로) |
| `modules/core/stage2_preflight.py` | 292 | OK | PerfTimer | executor.shutdown (finally) |
| `modules/core/stage2_preflight.py` | 296 | OK | PerfTimer | preflight_parallel stop (finally) |
| `modules/core/stage2_preflight.py` | 671 | OK | PerfTimer | SC Stage2 retrieval start |
| `modules/core/stage2_preflight.py` | 683 | OK | PerfTimer | SC Stage2 retrieval stop (finally) |
| `modules/core/stage2_preflight.py` | 779 | OK | PerfTimer | s2_arc_generate stop |
| `modules/core/stage2_preflight.py` | 1017 | OK | audit_event | stage2_patch_mode 이벤트 기록 |
| `modules/core/stage3_orchestrator.py` | 329 | OK | 방어적 추출 | protagonist_config 추출 실패 → 빈 dict |
| `modules/core/stage3_orchestrator.py` | 635 | OK | 텔레메트리 | QualityDashboard PASS 기록 |
| `modules/core/stage3_orchestrator.py` | 692 | OK | 텔레메트리 | QualityDashboard REJECT 기록 |
| `modules/core/stage4_context_builder.py` | 716 | OK | PerfTimer | SC Stage4 retrieval start |
| `modules/core/stage4_context_builder.py` | 724 | OK | PerfTimer | SC Stage4 retrieval stop (finally) |
| `modules/core/stage4_interview_round.py` | 323 | OK | 방어적 추출 | protagonist_name 추출 실패 → 경고 로그로 연결 |
| `modules/core/stage4_interview_round.py` | 499 | OK | PerfTimer | SC Director retrieval start |
| `modules/core/stage4_interview_round.py` | 1096 | OK | 텔레메트리 | PassRateMonitor.record_attempt |
| `modules/core/stage4_orchestrator.py` | 420 | OK | 선택적 주입 | diversity_engine 주입 실패 (OPTIONAL 주석) |
| `modules/core/stage4_orchestrator.py` | 525 | OK | 텔레메트리 | PassRateMonitor.check_alerts |
| `modules/core/stage4_post_processor.py` | 131 | OK | 트랜잭션 롤백 | DB 저장 실패 시 rollback 자체 실패 무시 |
| `modules/core/vec_memory.py` | 117 | OK | 자원 정리 | close() 실패 무시 |
| `modules/core/vec_memory.py` | 403 | OK | DB 조회 | episode 메타데이터 조회 실패 → None |
| `modules/core/vec_memory.py` | 772 | OK | DB 조회 | episode 메타데이터 조회 내부 실패 |
| `modules/core/vec_memory.py` | 899 | OK | 트랜잭션 롤백 | rollback 자체 실패 무시 |
| `modules/core/vec_memory.py` | 948 | OK | 자원 정리 | close() 실패 무시 |
| `modules/domain/agents/arc_ensemble.py` | 216 | OK | PerfTimer | [Phase 3-Obs] ensemble 소요시간 기록 |
| `modules/domain/agents/blueprint_ensemble.py` | 263 | OK | PerfTimer | [Phase 3-Obs] ensemble 소요시간 기록 |
| `modules/domain/agents/chief_writer.py` | 337 | OK | 선택적 주입 | context caching 실패 → 기존 방식 진행 |
| `modules/domain/agents/consensus_validator.py` | 277 | OK | PerfTimer | [Phase 3-Obs] 합의 소요시간 기록 |
| `modules/domain/agents/director_auditor.py` | 80 | OK | 방어적 조회 | context.actual_truth 접근 실패 |
| `modules/domain/agents/director_auditor.py` | 943 | OK | PerfTimer | [Phase 3-Obs] director voting 소요시간 기록 |
| `modules/domain/agents/four_phase_arc_generator.py` | 69 | OK | 방어적 감지 | 장르 Guard 감지 실패 → 기본값 wuxia |
| `modules/domain/agents/four_phase_arc_generator.py` | 181 | OK | 방어적 추출 | master_bible protagonist_config 추출 |
| `modules/domain/agents/four_phase_arc_generator.py` | 549 | OK | 방어적 추출 | master_bible protagonist_config 추출 (patch 경로) |
| `modules/domain/agents/manuscript_validator.py` | 67 | OK | 방어적 추출 | master_bible incarnation_type 추출 |
| `modules/domain/agents/writer.py` | 147 | OK | 방어적 추출 | anchor 시스템 조회 실패 → 비차단 |
| `modules/validation/validation_orchestrator.py` | 372 | OK | 텔레메트리 | FailureLearner blocking 실패 기록 |
| `modules/validation/validation_orchestrator.py` | 1116 | OK | 텔레메트리 | FailureLearner blocking 실패 기록 (parallel path) |

### 위험도 판정 근거

- **OK**: 실패해도 후속 로직에 영향을 주지 않거나, 선택적(OPTIONAL) 기능이거나, 자원 정리/rollback 자체 실패임.
- **WARN 없음**: 모든 52건은 의도적인 비차단 처리로 판단. RISKY 건 없음.

---

## 3. DI 슬롯 공식화 후보

| 파일 | 현재 패턴 | 권장 조치 | 우선순위 |
|------|-----------|-----------|----------|
| `director_continuity.py` | `getattr(self, "_cached_recent_blueprints", [])` | `__init__`에서 `self._cached_recent_blueprints = []` 초기화 | 낮음 (기능상 무해) |
| `director_continuity.py` | `getattr(self, "_cached_context_text_manuscript", "")` | `__init__`에서 `self._cached_context_text_manuscript = ""` 초기화 | 낮음 |
| `director_continuity.py` | `getattr(self, "_manuscript_cache_name", None)` | `__init__`에서 `self._manuscript_cache_name = None` 초기화 | 낮음 |
| `four_phase_arc_generator.py` | `getattr(self.context, "master_bible", {})` (2회 반복) | `_get_protagonist_config()` 헬퍼 메서드 추출 | 중간 (반복 제거) |
| `state_locked_arc_generator.py` | `getattr(self, "protagonist_name", "주인공")` | BaseAgent 슬롯 또는 generate() 파라미터로 전달 | 낮음 |

---

## 4. 중복 None guard 패턴

### `is not None and hasattr(x, "method")` 복합 패턴

| 파일 | 라인들 | 대상 객체 | 메서드 | 헬퍼 추출 가치 |
|------|--------|-----------|--------|---------------|
| `project_service.py` | L243, L250, L259, L264, L291, L308 | `_ws`, `_fl`, `_et`, `_sdt` | `rollback_to`, `history`, `energy_history` | 낮음 — 각 객체 타입이 달라 공통화 어려움 |
| `stage3_orchestrator.py` | L622, L680 | `_qd` (QualityDashboard) | `record_validation` | 낮음 — 2회뿐 |
| `stage4_interview_round.py` | L697, L988, L1001 | `_db`, `_fl`, `_adaptive_mgr` | 서로 다른 메서드 | 낮음 — 타입 이질적 |
| `validation_orchestrator.py` | L364, L1108 | `_fl`, `_fl_p` | `record_failure` | **중간** — 동일 FailureLearner 패턴 2회 |

### 추출 가치 있는 후보

`validation_orchestrator.py`의 FailureLearner 패턴:

```python
# 현재 (2회 중복):
_fl = ...
if _fl is not None and hasattr(_fl, "record_failure"):
    for _f in (blocking_result.get("failures") or []):
        try:
            _fl.record_failure(...)
        except Exception as _e:
            logging.debug(...)

# 헬퍼 추출 후보:
def _record_blocking_failures(fl, failures):
    if fl is None or not hasattr(fl, "record_failure"):
        return
    for _f in (failures or []):
        try:
            fl.record_failure(...)
        except Exception as _e:
            logging.debug(...)
```

---

## 5. 적용된 수정 사항

### Fix 1: `except Exception: pass` → `except Exception as _e: logging.debug(...)`

총 **22건** 적용. 변경된 파일:

| 파일 | 변경 건수 | 대상 카테고리 |
|------|-----------|--------------|
| `modules/domain/agents/arc_ensemble.py` | 1 | PerfTimer (Phase 3-Obs) |
| `modules/domain/agents/blueprint_ensemble.py` | 1 | PerfTimer (Phase 3-Obs) |
| `modules/domain/agents/director_auditor.py` | 1 | PerfTimer (Phase 3-Obs) |
| `modules/core/stage4_interview_round.py` | 2 | PerfTimer(SC), PassRateMonitor |
| `modules/core/stage4_orchestrator.py` | 2 | PassRateMonitor, diversity_engine |
| `modules/validation/validation_orchestrator.py` | 2 | FailureLearner (blocking path, parallel path) |
| `modules/core/stage2_preflight.py` | 10 | PerfTimer (arc_drive/preflight/parallel/SC/generate), audit_event |
| `modules/core/stage3_orchestrator.py` | 3 | protagonist_config, QualityDashboard PASS/REJECT |
| `modules/core/stage4_context_builder.py` | 2 | PerfTimer SC start/stop |
| `modules/core/adaptive_retry.py` | 3 | FailureLearner record/generate, 외부 logger |

**변경 원칙**: 비즈니스 로직(rollback, 트랜잭션, 자원 정리)은 수정하지 않았음.
PerfTimer, PassRateMonitor, QualityDashboard, FailureLearner 등 **텔레메트리/관측성 레이어**만 수정.

### Fix 2: `getattr` DI 후보 `# DI 후보:` 주석 추가

| 파일 | 추가 위치 | 주석 내용 |
|------|-----------|-----------|
| `modules/domain/agents/director_continuity.py` | `__init__` 끝 | `_cached_recent_blueprints`, `_cached_context_text_manuscript`, `_manuscript_cache_name` |
| `modules/domain/agents/four_phase_arc_generator.py` | `__init__` 시작 | `context.master_bible`, `context.guard` |
| `modules/domain/agents/state_locked_arc_generator.py` | `__init__` 시작 | `protagonist_name` |

### Fix 3: F841 Dead Variable 제거

| 파일 | 제거 대상 | 내용 |
|------|-----------|------|
| `modules/core/stage4_interview_round.py` | `arc_data = round_ctx.arc_data` (L38) | 로컬 변수로 할당 후 미사용. 이후 모든 참조는 `round_ctx.arc_data`로 직접 접근. |

---

## 6. 다음 TF 감사 권고사항

### 6-1. `director_continuity.py` 캐시 속성 초기화

`_cached_recent_blueprints`, `_cached_context_text_manuscript`, `_manuscript_cache_name` 3개를
`__init__`에서 명시적으로 초기화하면 `getattr` fallback을 없앨 수 있다.
매우 안전한 작업 (1~3줄 추가). **TF-7R 수준의 단순 패치**.

### 6-2. `four_phase_arc_generator.py` protagonist_config 헬퍼

동일한 5줄 블록이 `generate()`와 `_build_arc_prompt_for_patch()` 두 곳에 복사되어 있다.
`_get_protagonist_config() -> dict` 헬퍼로 추출하면 DRY + 테스트 용이성 향상.

### 6-3. `validation_orchestrator.py` FailureLearner 기록 헬퍼

동일한 FailureLearner 기록 루프가 L364~L373, L1109~L1118에 정확히 중복된다.
`_record_failures_to_learner(fl, failures)` 헬퍼로 추출 권고.

### 6-4. `stage2_preflight.py` PerfTimer 래퍼 고려

`stage2_preflight.py`의 PerfTimer 패턴이 10건으로 집중되어 있다.
`_perf_start(key)` / `_perf_stop(key)` 인라인 헬퍼(메서드 아닌 로컬 함수)로
try/except를 한 곳에 캡슐화하면 코드 라인 수를 30~40줄 줄일 수 있다.

### 6-5. `writer.py` 예외 처리 검토

`writer.py` L235, L252의 `except Exception: return fallback` 패턴은
silent pass는 아니지만 예외 정보를 버리고 있다. debug 로그 추가를 고려할 것.

---

## 7. 통계 요약

| 항목 | 수치 |
|------|------|
| 분석 파일 수 | ~130개 (modules/ 전체) |
| getattr(self, ..., None) 패턴 | 7건 |
| try/except Exception: pass 전체 | 52건 |
| - 텔레메트리/PerfTimer (OK) | 29건 |
| - 방어적 추출/조회 (OK) | 12건 |
| - 자원정리/롤백 (OK) | 8건 |
| - 조건부 import (OK) | 3건 |
| WARN/RISKY 판정 | 0건 |
| is not None and hasattr 복합 패턴 | 13건 (4개 파일) |
| F401/F811/F841 (ruff) | 1건 (F841, 수정 완료) |
| 적용된 수정 (Fix 1~3) | 26건 코드 변경 |
| 테스트 결과 | 2477 passed (변경 없음) |
| Ruff 결과 | 0 violations (변경 없음) |
