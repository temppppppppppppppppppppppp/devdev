# Opus TF3 Error Resilience Audit

**Date**: 2026-02-22
**Scope**: 에러 전파 경로 및 시스템 복원력 전면 조사
**Version**: V64+ (commit 5c762b6 기준)
**Author**: Claude Opus 4.6

---

## 1. LLM 전체 실패 (Gemini API 완전 장애)

### 1-1. BaseAgent.ask() 방어 체계

**파일**: `modules/domain/agents/base_agent.py` L250~732

BaseAgent.ask()는 다계층 방어를 구현한다:

```
Primary Model → Quota Fallback (model_stack) → Backup Model → 부분 응답 반환 → Error JSON 반환
```

**단계별 동작**:

1. **모델 스택 구축** (L279~285): `primary_model -> backup_model -> 추가 폴백`으로 최대 3개 모델 스택 구성. `MODEL_FALLBACK_CHAIN` 사전 기반.
2. **쿼터 소진 모델 필터링** (L288~307): `_quota_exhausted_models` 캐시(1시간 TTL)로 이미 실패한 모델 스킵.
3. **인라인 폴백** (L456~523): 429/quota 에러 시 `model_stack`의 다음 모델로 전환. Rate limit은 30초 백오프 3회까지.
4. **최종 백업** (L651~732): 모든 인라인 폴백 실패 후 `self.backup_model`로 마지막 시도.
5. **부분 응답 보존** (L646~728): 이전 응답이 있으면 `last_partial_response`로 보존, 검증 후 반환 또는 병합 시도.
6. **구조화된 에러 JSON** (L730~732): 모든 것이 실패하면 `_create_error_response()`로 `{"error": true, ...}` 반환. **절대 예외를 발생시키지 않는다.**

**판정: 무한 루프 가능성 없음**

- `MAX_CONTINUATIONS = 5` (L353): continuation 루프 최대 5회
- `MAX_QUOTA_RETRIES = len(model_stack)` (L357): 모델 수만큼만 폴백
- `MAX_RATE_LIMIT_RETRIES = 3` (L360): 같은 모델 rate limit 3회 한정
- 모든 경로가 유한 반복 후 종료

**위험 요소**:
- ask()는 **예외를 전파하지 않고** 에러 JSON을 반환한다. 호출부가 `result.get("error")` 체크를 하지 않으면 에러 응답이 정상 데이터처럼 처리될 수 있다.
- `_create_error_response()`의 결과에 `"content"` 키가 없으므로 content를 기대하는 호출부에서 빈 문자열이 될 수 있다.

### 1-2. Stage 2 (Arc 설계) 완전 실패 시

**파일**: `modules/core/stage2_orchestrator.py` L86~

- `asyncio.gather(*tasks, return_exceptions=True)` (L250): 병렬 농축 시 예외를 Exception 객체로 수집.
- 실패 항목은 `failed_indices`로 분리 후 순차 재시도 (L272~298).
- **재시도도 실패하면**: 해당 Arc 항목 누락 채 다음 Arc로 진행. 빈 enriched_batch면 Blueprint 앙상블이 `None` 반환 가능.

### 1-3. Stage 4 (원고 집필) 완전 실패 시

**파일**: `modules/core/stage4_orchestrator.py` L523~636

- 5라운드 면담 루프 (L539): 매 라운드 Chief Writer 앙상블 + Director 심사.
- **모든 후보 생성 실패** (L204~232): `candidates` 빈 배열 -> `_InterviewRoundResult(verdict="EMPTY")` 반환. 다음 면담으로 진행.
- **5회 모두 실패** (L600~629): 마지막 best_manuscript가 있으면 사용자 선택 제시 (1=사용, 2=건너뛰기). 없으면 "인간 검토 필요" 로그 후 종료.
- `max_loops` 가드 (L301~305): `min(..., 100)`으로 상한 100회. 무한 루프 불가.

**판정: Graceful degradation 적절함**. 5회 실패 시 명시적 중단 + 최선 결과물 선택지 제공.

---

## 2. 부분 실패 시나리오

### 2-1. 앙상블 3전략 중 1개만 실패

**파일**: `modules/domain/agents/blueprint_ensemble.py` L186~253

```python
with ThreadPoolExecutor(max_workers=3) as executor:
    for future in as_completed(futures, timeout=ENSEMBLE_TIMEOUT):
        try:
            result = future.result(timeout=SINGLE_CANDIDATE_TIMEOUT)
            candidates.append(result)
        except FutureTimeoutError:
            logging.warning(...)  # 개별 타임아웃
        except Exception as e:
            logging.warning(...)  # 개별 실패
```

- 개별 전략 실패는 **경고만 출력**하고 나머지 후보로 계속 진행.
- `ENSEMBLE_TIMEOUT = 300초`, `SINGLE_CANDIDATE_TIMEOUT = 240초`.
- 모든 후보 실패 시: `return None, []` (L255~257).
- 최소 기준 미달 시: `return None, candidates` (L282~284) -- 디버깅용 원본 반환.

**판정: 적절함**. 1-2개 실패해도 나머지로 진행. 전멸 시 None 반환.

### 2-2. Director만 실패

Director 에이전트는 BaseAgent를 상속하므로 ask() 호출이 에러 JSON을 반환할 수 있다. `_extract_json_robust()`가 이를 파싱하면 `{"error": true, ...}` 딕셔너리가 된다.

**위험**: Director의 verdict 파싱 로직이 `error` 키를 확인하지 않으면 REJECT로 처리될 가능성이 높다 (PASS 조건 미충족). 이는 5라운드 소진 후 재시도 또는 중단으로 이어진다.

**판정: 암묵적 실패 -> 5회 소진 -> 사용자 선택**. 명시적 Director 실패 감지 경로는 없지만, 실질적으로 안전하게 중단된다.

### 2-3. Validator만 실패

**파일**: `modules/core/stage4_interview_round.py` L259~400

```python
except Exception as _cv_err:
    self.ctx.ui.log(f"...ConsistencyValidator 실행 실패: {str(_cv_err)[:60]}")
# BlockingValidator, ContinuityValidator도 동일 패턴
```

모든 Validator 실패는 **비차단(non-blocking)**. 경고 로그만 출력하고 검증 결과 없이 Director에게 전달된다. Director가 LLM 기반으로 자체 판단하므로 Python 검증 없이도 동작 가능.

**판정: 의도적 설계**. "판단은 LLM이" 원칙에 부합. Validator는 보조 역할.

---

## 3. DB 손상 및 마이그레이션

### 3-1. SQLite 파일 손상

**파일**: `modules/core/db_manager.py` L84~431

- **WAL 모드** (L92~96): `PRAGMA journal_mode=WAL` + `PRAGMA synchronous=NORMAL`. 크래시 복구 안전성 강화. WAL 설정 실패 시 경고만 출력, 기본 DELETE 모드로 계속.
- **연결 타임아웃** (L87): `timeout=30.0`으로 DB 잠금 대기 30초.
- **check_same_thread=False** (L87): 멀티스레드 접근 허용, `RLock`으로 보호.

**DB 파일이 물리적으로 손상된 경우**:
- `_boot_db()` 시점에 `sqlite3.connect()` 자체는 성공할 수 있으나, CREATE TABLE이나 PRAGMA 실행 시 `sqlite3.DatabaseError` 발생.
- 이 예외는 **catch되지 않고 프로그램 크래시**. `_boot_db()`에는 최외곽 try-except가 없다.
- **복구 메커니즘 없음**: 손상된 DB를 자동 재생성하거나 백업에서 복원하는 코드는 존재하지 않는다.

**심각도: HIGH** -- DB 손상 시 프로그램 시작 자체가 불가능.

### 3-2. 테이블/컬럼 누락

**마이그레이션 코드 존재**:

- `episode_bibles` 새 컬럼 (L312~318): `ALTER TABLE ... ADD COLUMN` + `already exists` 오류 무시.
- `state_logs.summary` 컬럼 (L160~175): `PRAGMA table_info()` 조회 후 누락 시 추가.
- `martial_tracker` 동적 컬럼 (L236~264): `MARTIAL_METRICS` 상수 기반 자동 동기화.

**한계**:
- 테이블 자체가 누락된 경우: `CREATE TABLE IF NOT EXISTS`로 자동 생성되므로 안전.
- 핵심 컬럼(ep_num, data 등)이 타입 불일치인 경우: 처리 코드 없음.
- **스키마 버전 관리 시스템 없음**: 정형화된 migration 테이블이나 version 추적이 없다. 모든 마이그레이션은 `_boot_db()` 안에 인라인으로 작성되어 있다.

### 3-3. 트랜잭션 원자성

**파일**: `modules/core/db_manager.py` L1199~1407

`commit_episode_factory()`는 원자적 트랜잭션을 보장한다:
- `BEGIN TRANSACTION` -> 원고/HUD/상태/인과/카르마/로어/복선 저장 -> `COMMIT`
- 실패 시 `ROLLBACK` + `False` 반환 또는 커스텀 예외 발생

`stage4_post_processor.process_pass_result()`도 별도 보호:
- DB 저장 실패 시 `rollback()` + `return False` (L127~134)
- 후속 작업(HUD, 파일, 벡터)은 DB 커밋 성공 후에만 실행

**판정: 적절함**. DB 저장의 원자성이 잘 보장됨.

### 3-4. VecMemory DB 마이그레이션

**파일**: `modules/core/db_manager.py` L434~527

`_migrate_vec_memory_db()`는 기존 `vec_memory.db`를 `project_data.db`로 1회성 마이그레이션:
- `ATTACH DATABASE` -> 데이터 복사 -> `DETACH` -> 원본 `.db.migrated` 리네임
- sqlite-vec 미설치 시 `.db.partial_migrated`로 보존, 재설치 후 자동 재시도 (L440~441)
- 전체 과정이 try-except로 감싸져 실패해도 "비치명" 경고만 출력 (L512~523)

**판정: 적절함**. 마이그레이션 실패가 시스템 동작을 차단하지 않음.

---

## 4. 메모리 압박 (200화+ 장기 연재)

### 4-1. 이전 원고 30화 전문 로드

**파일**: `modules/core/stage4_context_builder.py` L332~349

```python
for _prev_ep in range(max(1, next_ep - 30), next_ep):
    _prev_ms_data = self.ctx.current_project.db.get_manuscript(_prev_ep)
    _prev_manuscripts_parts.append(f"[제{_prev_ep}화]\n{_prev_content}")
```

**200화 시점에서**: 171~200화의 원고 30편을 메모리에 로드. 각 원고 ~5,000자 가정시 약 150KB. **메모리 문제 없음**.

그러나 이 텍스트가 LLM 프롬프트에 주입되면 토큰 수가 급증한다. `mandatory_context` 트렁케이션 (L431~466)이 80,000자 상한으로 잘라주지만, 30화 전문 + 기타 컨텍스트가 이 한도를 넘을 가능성이 높다.

### 4-2. VecMemory 임베딩 캐시

**파일**: `modules/core/vec_memory.py` L72~74

```python
self._embed_cache: OrderedDict[str, list] = OrderedDict()
self._embed_cache_max = 128
```

LRU 캐시 128개. 각 임베딩 3072-dim float -> 약 24KB. 총 ~3MB. **메모리 문제 없음**.

### 4-3. StateTracker 누적 데이터

**파일**: `modules/domain/agents/state_tracker.py`

- `self.states`: dict[ep_num -> EpisodeState]. Arc당 5~6개 에피소드. 200화 = ~200개 항목. 각 항목은 간단한 dataclass. **수 KB 수준**.
- `self.entity_name_registry`: OrderedDict, 최대 500개 (L135). LRU 정리.
- `self.npc_registry`: NPC 수에 비례. 일반적으로 50~200명. **수 KB 수준**.
- `self.resolved_plots`: 누적 리스트. **크기 제한 없음**. 200화에서 수백 개 가능하지만 각 항목이 작아 문제 없음.

### 4-4. Context Caching

**파일**: `modules/domain/agents/base_agent.py` L1091~1093

```python
_context_caches = {}  # 클래스 변수
_CONTEXT_CACHE_MAX = 50
```

50개 초과 시 오래된 것부터 삭제 (L1166~1170). **메모리 문제 없음**.

### 4-5. Adaptive Retry Manager

**파일**: `modules/core/adaptive_retry.py` L556~564

```python
if len(self._failures[ep_num]) > self.max_history:
    self._failures[ep_num] = self._failures[ep_num][-self.max_history:]
if len(self._failures) > self._max_episode_keys:
    oldest_eps = sorted(self._failures.keys())[:len(self._failures) - self._max_episode_keys]
```

에피소드 키 50개, 에피소드당 기록 20개 상한. **메모리 문제 없음**.

### 4-6. 누적 Bible 캐시

**파일**: `modules/core/db_manager.py` L754~795

```python
self._cumulative_bible_cache: dict = {}
```

`get_cumulative_bible(up_to_ep)` 호출 시 증분 캐시. **크기 제한 없음**. 200화에서 최대 200개 캐시 항목이 누적될 수 있으나, 각 항목이 아이템/NPC 목록이므로 수십 KB 수준.

**종합 판정**: 메모리 압박은 200화 수준에서 문제 없음. 가장 큰 요소는 30화 원고 전문 로드(~150KB)와 LLM 프롬프트 크기(80,000자 트렁케이션으로 제어). `resolved_plots`와 `_cumulative_bible_cache`는 제한 없이 누적되지만 실질적 위험은 낮다.

---

## 5. 재진입 안전성 (중단 후 재시작)

### 5-1. 에피소드 생성 중단 시

**시나리오**: Stage 4에서 5라운드 면담 중 프로세스 종료.

**DB 상태**: 원고는 면담 통과 후 `process_pass_result()`에서 저장된다. 면담 중에는 DB에 아무것도 기록되지 않으므로, 중단 시 **마지막 커밋된 에피소드까지만 유효**.

**재시작 시**:
- `get_latest_episode_number()` (db_manager.py L1409~1413): `SELECT MAX(ep_num) FROM manuscripts` + 1
- `get_latest_episode_number()` (project_manager.py L631~661): DB와 물리 파일 중 최신 회차 비교

따라서 재시작 시 마지막 완료된 에피소드 다음부터 자동 재개. **반쪽 저장된 데이터 없음**.

### 5-2. DB 커밋 중 크래시

`commit_episode_factory()`는 `BEGIN TRANSACTION` -> 작업 -> `COMMIT`으로 구성. 중간에 크래시하면 SQLite WAL 모드가 자동 롤백. 다음 연결 시 일관된 상태 복원.

**다만 `process_pass_result()`의 2단계 저장에 주의**:
1. `save_manuscript()` + `update_martial_tracker()` + `conn.commit()` (L118~126)
2. 이후 Episode Bible, state_logs 등은 별도 저장 (L406~448)

1단계 커밋 성공 후 2단계에서 크래시하면: 원고는 저장되었으나 Episode Bible/state_logs가 누락. 다음 에피소드 생성 시 누적 Bible이 불완전할 수 있다. **그러나 Episode Bible은 보조 데이터이므로 치명적이지 않음.**

### 5-3. Blueprint 중단 시

Stage 2에서 Blueprint 생성 중 중단: Arc별로 개별 저장 (`save_arc_to_db`, `save_blueprint`). 부분적으로 저장된 Arc의 Blueprint가 있으면 Stage 4에서 해당 에피소드까지 진행 가능.

**Smart Skip** (L180~189): 기존 원고가 있으면 해당 Arc까지 자동 건너뛰기.

**판정: 재진입 안전성 양호**. 핵심 데이터(원고, Blueprint, Arc)는 원자적으로 저장되며, 보조 데이터 누락은 치명적이지 않다.

---

## 6. 타임아웃 설정

### 6-1. LLM API 타임아웃

**파일**: `modules/domain/agents/base_agent.py`, `config/system.yaml`

- `API_TIMEOUT = 90초` (system.yaml L17): **선언만 되고 실제 사용되지 않음**.
  - `self.client.models.generate_content()` 호출에 timeout 파라미터가 전달되지 않는다 (L368~369).
  - Gemini genai SDK의 기본 타임아웃에 의존. 이는 일반적으로 수분 이상.

**심각도: MEDIUM** -- `API_TIMEOUT = 90`이 system.yaml에 정의되어 있지만 코드에서 사용되지 않아 사실상 무효. LLM 호출은 SDK 기본 타임아웃(보통 300초+)까지 대기할 수 있다.

### 6-2. 네트워크 재시도 타임아웃

**파일**: `modules/domain/agents/base_agent.py` L382~416

```python
MAX_NETWORK_RETRIES = 22  # config/system.yaml
NETWORK_RETRY_DELAY_BASE = 10초
NETWORK_RETRY_DELAY_MAX = 30초
```

22회 재시도, 10~30초 간격. 최대 총 대기 시간: ~660초(11분). 야간 무인 운영에서 3~5분 인터넷 끊김 대응. **적절함**.

### 6-3. ThreadPoolExecutor 타임아웃

**Blueprint 앙상블** (blueprint_ensemble.py L101~103):
```python
ENSEMBLE_TIMEOUT = 300  # 5분
SINGLE_CANDIDATE_TIMEOUT = 240  # 4분
```
`as_completed(timeout=300)` + `future.result(timeout=240)`. **타임아웃 설정됨**.

**Validation Orchestrator** (validation_orchestrator.py L1104):
- `ThreadPoolExecutor`로 병렬 검증. **명시적 타임아웃 없음** -- `loop.run_in_executor()`는 타임아웃 지원 안 함.

**Director Auditor 병렬 투표**:
- ThreadPoolExecutor 사용. 개별 future에 타임아웃 적용 여부는 director_auditor.py 내부 로직 의존.

**Manager Bible Future** (stage4_post_processor.py L299):
```python
raw_audit = _bible_future.result(timeout=120)  # 최대 2분 대기
```
**타임아웃 설정됨**.

### 6-4. 무한 대기 가능성

| 위치 | 타임아웃 | 무한 대기 가능성 |
|------|---------|--------------|
| BaseAgent.ask() LLM 호출 | **없음** (SDK 기본) | 가능 (SDK 기본 수분) |
| 네트워크 재시도 | 22회 x 30초 = 11분 | 불가 |
| Blueprint 앙상블 | 5분 | 불가 |
| Manager Future | 2분 | 불가 |
| Validation 병렬 | **없음** | 가능 (LLM 호출 포함 시) |
| Director 연속성 검사 | **없음** | 가능 (LLM 호출 포함 시) |

**가장 큰 위험**: `API_TIMEOUT = 90`이 선언만 되고 사용되지 않아, 모든 LLM 호출이 SDK 기본 타임아웃(수분)까지 블록될 수 있다. 야간 무인 운영에서 Gemini API 무응답 시 장시간 행이 발생할 수 있다.

---

## 7. 예외 삼킴 (Silent Swallow) 분석

### 7-1. 위험도 LOW (의도적 설계)

아래 패턴들은 보조 기능의 실패를 무시하는 **의도적 설계**:

| 위치 | 패턴 | 사유 |
|------|------|------|
| `base_agent.py` L347~349 | metrics startup pass | 메트릭 실패가 본 작업에 영향 주면 안 됨 |
| `base_agent.py` L598~600 | metrics end pass | 상동 |
| `adaptive_retry.py` L572~573 | FailureLearner pass | 학습 연동 실패는 비치명적 |
| `stage4_orchestrator.py` L420~421 | diversity injection pass | 다양성 엔진 실패 비차단 |
| `director_auditor.py` L904~905 | PerfTimer pass | 성능 로깅 실패 비차단 |
| `constants.py` L413~414 | protagonist name pass | 폴백 경로 존재 |

### 7-2. 위험도 MEDIUM

| 위치 | 패턴 | 위험 |
|------|------|------|
| `config_manager.py` L27~28 | ManuscriptLimits import pass | `_target_manuscript_length` 하드코딩 폴백(5000) 사용. 의도한 길이와 다를 수 있음 |
| `director_auditor.py` L80~81 | actual_truth 조회 pass | Guard deep validation에 current_state가 빈 dict로 전달. 오탐/미탐 가능 |
| `vec_memory.py` L88 | vec_episodes 테이블 체크 pass | `initialization_error` 설정으로 추후 체크 가능하나, 에러 원인이 로그에 남지 않음 |

### 7-3. 위험도 HIGH (잠재적 데이터 손실)

| 위치 | 패턴 | 위험 |
|------|------|------|
| `db_manager.py` L477~478 | `except Exception: pass` (vec_episodes 마이그레이션) | 벡터 데이터 개별 행 삽입 실패 시 무시. 마이그레이션 완료로 표시되지만 일부 벡터 누락 가능 |
| `db_manager.py` L517~518 | `except Exception: pass` (DETACH 후 rollback) | 마이그레이션 실패 후 정리 과정의 예외 무시. ATTACH된 DB가 분리되지 않을 수 있음 |
| `stage4_post_processor.py` L447~448 | Episode Bible 전체 블록 pass | Episode Bible 저장 전체 실패 시 비차단으로 진행. 누적 Bible 데이터 손실 |

### 7-4. 개선이 필요한 패턴들

1. **`db_manager.py` L477~478** -- vec_episodes 개별 행 삽입 실패 시 최소한 실패 건수를 카운트하고 로그에 남겨야 한다.

2. **`base_agent.py` API_TIMEOUT 미사용** -- `config/system.yaml`에 90초로 설정했지만 실제 SDK 호출에 전달하지 않는다. 이는 예외 삼킴은 아니지만, 설정값이 무시되는 "silent ignore" 패턴이다.

3. **`stage4_post_processor.py` L447~448** -- Episode Bible 저장 실패는 에피소드 진행을 차단하지 않지만, 이후 에피소드의 누적 Bible 계산에 영향을 미친다. 실패 시 재시도 또는 보상 메커니즘이 없다.

---

## 8. 종합 평가

### 8-1. 강점

| 영역 | 평가 |
|------|------|
| LLM 폴백 체계 | **A+** -- 3단계 모델 폴백 + 부분 응답 보존 + 키 순환 |
| 네트워크 복원력 | **A** -- 22회 백오프 재시도 + 연결 체크 + 하트비트 |
| DB 트랜잭션 원자성 | **A** -- WAL 모드 + 원자적 커밋 + 실패 시 롤백 |
| 무한 루프 방지 | **A** -- 모든 루프에 상한 (5회 면담, 100회 에피소드, 5회 continuation) |
| 재진입 안전성 | **A-** -- 핵심 데이터 원자적 저장, 보조 데이터 누락 가능 |
| 부분 실패 처리 | **A-** -- Validator 실패 비차단, 앙상블 부분 실패 허용 |

### 8-2. 약점

| 영역 | 평가 | 설명 |
|------|------|------|
| DB 손상 복구 | **D** | 자동 복구/백업 메커니즘 없음. 손상 시 수동 복구 필요 |
| API 타임아웃 | **C** | `API_TIMEOUT=90` 선언만, 실제 미사용. 무한 대기 가능 |
| 스키마 버전 관리 | **C** | 정형화된 마이그레이션 시스템 없음. 인라인 ALTER TABLE |
| 에러 응답 구분 | **C+** | ask()가 에러 JSON 반환 시 호출부 구분 미흡 가능 |
| 장기 누적 데이터 | **B** | resolved_plots, cumulative_bible_cache 크기 제한 없음 (실질 위험 낮음) |

### 8-3. 권장 조치 (우선순위순)

1. **[P1] API 타임아웃 활성화**: `self.client.models.generate_content()` 호출에 `config/system.yaml`의 `api.timeout` 값을 실제로 전달. Gemini SDK의 `httpx_client` 타임아웃 설정 또는 `signal.alarm` 래퍼.

2. **[P2] DB 손상 감지 및 복구**: `_boot_db()` 시작 시 `PRAGMA integrity_check` 실행. 실패 시 `.db.corrupt` 리네임 + 빈 DB 재생성 + 사용자 알림.

3. **[P3] 에러 응답 마커 표준화**: BaseAgent.ask()의 에러 응답에 `"_agent_error": True` 같은 표준 마커 추가. 호출부에서 일관적으로 체크 가능하도록.

4. **[P4] vec_episodes 마이그레이션 로깅**: `except Exception: pass` -> `except Exception as e: logging.warning(...)` + 실패 카운터.

5. **[P5] 스키마 버전 테이블 도입**: `schema_version` 테이블 추가. `_boot_db()`에서 현재 버전 확인 후 순차 마이그레이션 실행.

---

## 부록: 에러 전파 경로 다이어그램

```
User Input
  |
  v
Stage 0 (Bible/NPC)  -- DB 저장 실패 -> 프로그램 중단
  |
  v
Stage 2 (Arc/Blueprint)
  |-- Analyst.enrich (asyncio.gather)  -- 부분 실패 -> 재시도 -> 누락 허용
  |-- BlueprintEnsemble (ThreadPool)   -- 부분 실패 -> 나머지로 진행
  |-- Director 선택                    -- LLM 실패 -> 에러 JSON -> None 반환
  |-- Validation Pipeline              -- 실패 -> 비차단 경고
  |
  v
Stage 4 (원고 집필)
  |-- ChiefWriter 앙상블 (3전략)       -- 부분 실패 -> 나머지로 진행
  |-- Python 검증 (4종)                -- 실패 -> 비차단 경고
  |-- Director 심사                    -- LLM 실패 -> REJECT 처리 -> 재시도
  |-- CoVe 사후검증                    -- 실패 -> 비차단 경고
  |-- 5라운드 소진                     -- 최선 결과물 선택 또는 중단
  |
  v
DB 저장 (process_pass_result)
  |-- 원고 + HUD 저장                  -- 실패 -> 롤백 -> 에피소드 중단
  |-- Episode Bible                    -- 실패 -> 비차단 (누적 데이터 손실 가능)
  |-- 벡터 메모리                      -- 실패 -> 비차단 (검색 품질 저하)
  |-- 파일 저장                        -- 실패 -> 비차단 (DB에 원본 보존)
```

---

*End of Opus TF3 Error Resilience Audit*
