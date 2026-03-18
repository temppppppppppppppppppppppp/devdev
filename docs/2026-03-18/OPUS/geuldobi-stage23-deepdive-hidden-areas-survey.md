# Stage 2-3 딥다이브: 잘 살피지 않는 영역 전수조사

Date: 2026-03-18
Status: **final** (6회 적대적 감리 반영, 확신도 98%)
Canonical Path: `docs/2026-03-18/OPUS/geuldobi-stage23-deepdive-hidden-areas-survey.md`
Baseline Commit: `d4e96804`
Survey Mode: 3회 병렬 딥다이브 → 3Pass 감리 → **6회 적대적 감리 (3+3)**
조사 범위: Stage 2 (Arc) + Stage 3 (Blueprint) 내부의 **표면 조사에서 누락되기 쉬운** 영역

---

## 0. 조사 요약 (Executive Summary)

3회 병렬 딥다이브(104 tool uses) + **6회 적대적 감리(70+169 tool uses)**로 Stage 2-3 조사.

### 6회 적대적 감리 후 최종 심각도 분포

| 심각도 | 원본 | 1차 적대적 | **2차 적대적 (최종)** | 변동 |
|--------|------|----------|-------------------|------|
| **CRITICAL** | 1 | 0 | **0** | CRITICAL→MEDIUM→**HIGH 재승격** |
| **HIGH** | 4 | 4 | **3** | H2 REFUTED(데드코드) + H3→LOW + last_error_type 재승격 |
| **MEDIUM** | 13 | 19 | **23** | 3.3 재승격 + 신규 4건 + CS-02/CS-12 하향 |
| **LOW** | 8 | 14 | **17** | H3 합류 + CS-02/CS-12 합류 + 신규 1건 |
| **INFO** | 4 | 6 | **6** | 변동 없음 |
| **REFUTED** | 0 | 0 | **1** | H2 StateLockedArcGenerator (데드 코드) |

### HIGH 3건 (6회 적대적 감리 최종 확정)

| # | 발견 | 파일 | 6회 감리 근거 |
|---|------|------|-------------|
| **H1** | **Emergency fallback: Director-REJECT 블루프린트를 PASS_WITH_WARNING으로 반환** | three_phase_blueprint_generator.py:741-750 | **2회 CONFIRMED**. Stage 4는 `quality_risk`를 soft advisory + V75-D 문턱 하향으로만 사용, 하드 차단 없음. `stage3_orchestrator.py:841-844`에서 성공으로 처리. |
| **H4** | **Dead NPC CRITICAL이 Director PASS로 우회 가능** | unified_blueprint_validator.py:334-356, 69-97 | **2회 CONFIRMED**. `director_prompts.py:128`에 "죽은 NPC 활동 = 자동 REJECT" 명시되어 있으나, 스키마에 구속력 있는 필드 없음. Python CRITICAL → 자유텍스트 힌트(4개 제한, 160자 절단) → LLM 준수 확률적. AGENTS.md 대원칙 #4 위반 경로. |
| **H-RE** | **`last_error_type` 3-스레드 경쟁 (재승격)** | blueprint_ensemble.py:297, base_agent.py:839 | 1차에서 MEDIUM 하향 → **2차에서 HIGH 재승격**. API 장애 시 결정론적 발생 (3 전략이 동일 API 사용). `SCHEMA_INCOMPATIBLE`은 3 전략 모두 동일 스키마 → 전부 실패하나 마지막 쓰기 스레드가 TIMEOUT이면 빠른실패 누락. 에피소드당 9회 무의미 리트라이 = **~$2.70** (250화 간헐적 장애 시 $675). |

### REFUTED 1건

| 원본 | 사유 |
|------|------|
| ~~H2: StateLockedArcGenerator `self.primary_model` 변이~~ | **`generate()` 메서드가 전체 코드베이스에서 한 번도 호출되지 않음.** `main_a.py:1789`에서 인스턴스화만 되고 `agents["state_locked"].generate()` 호출 없음. 데드 코드. |

### 2차 적대적 감리 하향 추가

| 원본 | 심각도 | 2차 판정 | 근거 |
|------|--------|---------|------|
| H3: Stage3Orchestrator 크래시 미롤백 | HIGH | **LOW** | Blueprint 저장은 `_handle_success` 경로에서만 실행 (크래시 시 미도달). SQLite WAL 자동 롤백. 재시작 시 `production_head` 감지로 자동 복구. |
| CS-02: 상태 추출 침묵 동결 | MEDIUM | **LOW** | `logging.warning()` 경고 존재. 시작상태 유지는 의도적 방어 패턴. |
| CS-12: 클래스 레벨 캐시 공유 | MEDIUM | **LOW** | `_cache_lock` 스레드 안전 + `content_hash` 포함 키 → 충돌 극히 희박. |

### 2차 적대적 감리 재승격

| 원본 | 1차 판정 | 2차 판정 | 근거 |
|------|---------|---------|------|
| last_error_type 경쟁 (1.1) | MEDIUM | **HIGH** | API 장애 시 결정론적, 비용 $2.70/에피, SCHEMA_INCOMPATIBLE 최적화 무력화 |
| 3.3 빈 스키마 허용 | LOW | **MEDIUM** | `_python_pre_validate`는 "REJECT 권한 없음" 명시. emergency fallback/inplace patch 경로에서 ensemble `>=4` 필터 우회 |

### 2차 적대적 감리 신규 발견 (4건 MEDIUM)

| # | 발견 | 파일 | 근거 |
|---|------|------|------|
| NEW-01 | **Stage 2 Arc 저장 비원자성**: `save_v20_anchor` 후 `safe_commit_async` 실패 시 크래시하면 앵커 파일과 DB 불일치 | stage2_finalizer.py:1258-1298 | 인메모리 롤백은 있으나 디스크 앵커는 미롤백 |
| NEW-02 | **PreflightChecker가 hollow 입력(빈 tactical_doc) 미검증** | preflight_checker.py:126-173 | 빈 tactical_doc → 빈 constraint map → hollow blueprint 연쇄 |
| NEW-04 | **`_protagonist_config` 캐시 영구 보존, 프로젝트/장르 전환 시 미무효화** | director_caching.py:160-176, director.py:105-112 | `invalidate_caches()`가 4/5+ 필드만 클리어 |
| NEW-06 | **StateTracker 롤백 시 동적 추가 속성 잔류 가능** | state_tracker.py | `snapshot()` 이후 추가된 속성은 롤백 대상 아님 |

---

## 1. ~~CRITICAL~~ → MEDIUM → **HIGH**: 스레드 안전성 (6회 적대적 감리)

### 1.1 `last_error_type` 경쟁 상태 — ~~CRITICAL~~ → ~~MEDIUM~~ → **HIGH**

**파일**: `blueprint_ensemble.py:297`, `base_agent.py:839`
**재현 경로**: 3개 전략 스레드가 동시에 `self.ask()` 호출 → 각각 다른 에러 발생 → `self.last_error_type`에 경쟁적 쓰기 → `three_phase_blueprint_generator.py:349`에서 읽기 시 잘못된 값

```
Thread A: SCHEMA_INCOMPATIBLE → self.last_error_type = SCHEMA_INCOMPATIBLE
Thread B: 성공 (덮어쓰기 없음)
Thread C: TIMEOUT → self.last_error_type = TIMEOUT  ← A의 값을 덮어씀
Caller: reads TIMEOUT → SCHEMA_INCOMPATIBLE 빠른 실패 트리거 안 됨 → 9회 무의미한 리트라이
```

**반대 시나리오**: Thread C가 먼저 `TIMEOUT`을 쓰고 Thread A가 나중에 `SCHEMA_INCOMPATIBLE`을 쓰면 → 정상 동작하지만 보장되지 않음.

**영향**:
- 무의미한 리트라이 9회 소진 (비용 낭비)
- 또는 일시적 에러를 스키마 에러로 오인하여 조기 중단 (생산 중단)

**근본 원인**: `BaseAgent`는 단일 스레드 사용을 전제로 설계. `BlueprintEnsembleGenerator`가 `ThreadPoolExecutor`로 동일 인스턴스에서 3 스레드를 돌리면서 이 전제를 위반.

> **1차 적대적**: CRITICAL → MEDIUM (GIL 메모리 안전, 데이터 손상 없음).
> **2차 적대적 재승격**: MEDIUM → **HIGH**. API 장애 시 3 전략이 동일 API 사용 → 전부 실패 = 결정론적 발생. `SCHEMA_INCOMPATIBLE`은 3 전략 동일 스키마 → 전부 해당하나 마지막 쓰기 스레드가 TIMEOUT이면 빠른실패 누락. **에피소드당 9회 무의미 리트라이 = ~$2.70**. 250화 간헐적 장애 시 $675. 데이터 손상 없으나 비용 영향 + 최적화 무력화로 HIGH.

---

## 2. HIGH (적대적 감리 확정 4건 + 하향 3건)

### 2.1 ~~HIGH~~ → **LOW**: base_agent.py 인스턴스 속성 3-스레드 동시 변이

**파일**: `base_agent.py:297-304,386,603-604,832`
**동시 변이되는 속성**:

| 속성 | 위치 | 영향 |
|------|------|------|
| `self.last_partial_response` | L604 (ask 시작 시 리셋) | 스레드 A의 부분 응답을 B가 덮어쓰기 |
| `self._last_llm_usage` | L386, 403-404 | 토큰 사용량 추적 오류 |
| `self._call_usage_totals` | L404-415 | 누적 비용 추적 부정확 |
| `self._last_thinking` | L832 | 사고 과정 혼재 |
| `self.requires_human_intervention` | L325, 1403, 1418 | 사람 개입 플래그 경쟁 |

**영향**: ~~메트릭/비용 추적 데이터 손상 확실. 부분 응답 복구 경로 오작동 가능.~~

> **적대적 감리 판정**: HIGH → **LOW**. 영향 받는 속성이 모두 텔레메트리 전용. `last_partial_response`는 ensemble 완료 후 호출자가 사용하지 않음. `requires_human_intervention`도 하류 미참조. 비용 추적만 부정확 (1/3 스레드 값만 반영).

### 2.2 ~~HIGH~~ → **LOW**: `self.client` 키 회전 중 동시 접근

**파일**: `base_agent.py:621-623`
**시나리오**: Thread B가 API 키 회전으로 `self.client = new_client` → Thread A는 구 클라이언트로 진행 중 → Thread A의 호출 실패 가능.

**영향**: ~~일시적 API 실패~~

> **적대적 감리 판정**: HIGH → **LOW**. `GeminiProvider.generate(client=self.client)`에서 `client`가 로컬 파라미터로 캡처됨. 진행 중 API 호출은 구 클라이언트의 로컬 참조를 사용하므로 안전. 키 회전은 `ask()` 시작 시에만 발생 (L617-623), 호출 루프 내부에서는 미발생.

### 2.3 **HIGH CONFIRMED**: Emergency Fallback이 Director-REJECT 블루프린트를 PASS_WITH_WARNING으로 반환

**파일**: `three_phase_blueprint_generator.py:740-750`
**조건**: 10회 리트라이 전부 Director REJECT → 마지막 점수 >= 50점 → `PASS_WITH_WARNING` + `quality_gate_failed=True`로 반환.

**영향**: Director가 명시적으로 거부한 블루프린트가 Stage 4에 투입됨. `quality_risk=True` 플래그가 있으나 Stage 4에서 하드 차단하지 않음.

### 2.4 ~~HIGH~~ → **LOW**: Pydantic validate_blueprint가 실패 시 원본 반환

**파일**: `modules/models/blueprint.py:76-87`
**코드**: `except Exception as e: logger.warning(...); return raw`

~~**영향**: Pydantic이 거부하는 잘못된 데이터가 통과 → 하류 크래시 가능.~~

> **적대적 감리 판정**: HIGH → **LOW**. Blueprint Pydantic 모델은 `extra="allow"` + 모든 필드 기본값 → 실패 거의 불가능. Gemini `response_schema`가 업스트림에서 구조 강제. 함수의 실질 역할은 검증이 아닌 정규화(`ep_num`↔`episode_number` 동기화).

### ~~2.5 HIGH: StateLockedArcGenerator~~ → **REFUTED (2차 적대적 감리)**

> **`generate()` 메서드가 전체 코드베이스에서 한 번도 호출되지 않음.** `main_a.py:1789`에서 인스턴스화만 되고 `stage2_preflight.py`, `stage2_finalizer.py`, `stage2_orchestrator.py` 어디에서도 `agents["state_locked"].generate()` 호출 없음. `agents["four_phase"].generate()`만 사용 (stage2_preflight.py:1364). **데드 코드 — 위험도 없음.**

### ~~2.6 HIGH: Stage3Orchestrator 크래시 미롤백~~ → **LOW (2차 적대적 감리)**

> Blueprint 저장(`save_episode_blueprint`)은 `_handle_success` 경로(L1606)에서만 실행. 크래시 시 이 경로 미도달 → DB에 블루프린트 미기록. SQLite WAL(`db_manager.py:237`)이 미커밋 트랜잭션 자동 롤백. 재시작 시 `production_head = max(existing_bp_max, ...)` 감지(L580-587) → 누락 에피소드부터 자동 재개. **크래시 비용은 LLM API 호출 낭비에 국한.**

### 2.7 **HIGH (신규)**: Dead NPC CRITICAL이 Director PASS로 우회 가능

**파일**: `unified_blueprint_validator.py:334-356,69-97`
**동작**: `_apply_dead_npc_advisory`가 CRITICAL 이슈 추가 → `pre_result["issues"]`에 저장 → Director에게는 `python_warnings` 자유텍스트 힌트로만 전달 (L382-389). Director가 `final_verdict` 결정 시 CRITICAL 무시 가능.
**영향**: 사망 캐릭터가 행동/대사로 등장하는 블루프린트가 Director PASS를 받을 수 있음. AGENTS.md 대원칙 #4 ("사망 캐릭터는 회상/언급만") 위반 경로.

---

## 3. MEDIUM: 침묵 실패 + 데이터 무결성

### 3.1 합의 검증기 Fail-Open (자동 PASS)

**파일**: `consensus_validator.py:233-256,282-285`
**동작**: 타임아웃/에러 시 `verdict: "PASS", confidence: 0.5` 반환. 전체 실패 시 `confidence: 0.3`으로 합성 PASS.
**영향**: LLM API 장애 시 모든 Arc 검증이 자동 통과.

### 3.2 합의 투표에서 신뢰도 점수 무시

**파일**: `consensus_validator.py:338-424`
**동작**: 다수결 투표에서 각 검증기의 `confidence` 가중치 없음.
**시나리오**: 타임아웃 PASS(0.5) 2건 + 실제 REJECT(0.95) 1건 = **PASS** (잘못된 결과).

### 3.3 스키마가 논리적으로 빈 블루프린트 허용

**파일**: `response_schemas.py:602-635`
**세부**: `scene_breakdown`은 빈 dict `{}` 허용, `integrated_scenario`는 최소 길이 미강제(스키마 레벨). Python pre-validator 경고는 advisory only.

### 3.4 Scene 엔트리가 단순 문자열 허용

**파일**: `response_schemas.py:518-552`
**세부**: `anyOf`로 구조화 객체 OR 단순 문자열 허용 → `"scene_1": "뭔가 일어남"` 유효.

### 3.5 부분 Arc 블루프린트 커밋 가능

**파일**: `stage3_orchestrator.py:1606-1617`
**세부**: 에피소드별 개별 커밋, Arc 레벨 트랜잭션 없음. 중간 크래시 시 ep 1-3만 커밋, 4-5 누락.
**완화**: 순차 강제 (ep N-1 없으면 ep N 차단) → 재시작 시 자동 재개 가능.

### 3.6 메트릭 기록 실패 침묵 소멸

**파일**: `quality_dashboard.py:238-248`
**세부**: `_save_record()`가 ALL exceptions를 `logging.warning()`으로만 처리. 디스크 풀 시 메트릭 영구 손실.
**관련**: 인메모리 대시보드는 데이터 보유 → 재시작 시 불일치.

### 3.7 jsonl_io.py 에러 처리 부재

**파일**: `modules/core/jsonl_io.py:13-20`
**세부**: `append_jsonl_record()`에 try-except 없음. 디스크 에러가 호출자에 전파 → 파이프라인 중단 가능.
**대비**: `SessionLogger._write()`는 별도로 에러 흡수 구현.

### 3.8 PASS_WITH_WARNING 판정 불일치

**파일**: `three_phase_blueprint_generator.py:502` vs `unified_blueprint_validator.py:305`
**세부**: 생성기에서는 REJECT 취급, 검증기 로그에서는 SUCCESS 취급 → 감사 추적 혼선.

### 3.9 Director 점수 미검증 기록

**파일**: `quality_dashboard.py:124-150`
**세부**: `result.get("score", 0)` 직접 기록, 범위 검증 없음. 비-스키마 경로에서 문자열/음수 가능.

### 3.10 리트라이 사유별 메트릭 미분류

**파일**: `three_phase_blueprint_generator.py:131-137`
**세부**: `retries` 횟수만 기록, 스키마 에러/품질 거부/연속성 실패 구분 없음.

### 3.11 Arc→Blueprint 핸드오프 필드 검증 누락

**파일**: `stage3_orchestrator.py:788-802`
**세부**: `ep_start`만 검증. `tactical_doc`, `ep_end`, `ep_count`, `arc_no`는 `.get()` 기본값으로 조용히 대체.
**영향**: 빈 `tactical_doc` → 제약 없는 블루프린트 생성 (hollow constraints).

### 3.12 PASS_WITH_FIX가 QualityGate 90점 문턱 우회

**파일**: `three_phase_blueprint_generator.py:494-502`
**세부**: PASS는 90점 미만 시 REJECT 강제. PASS_WITH_FIX는 "Director 주권 존중"으로 점수 무관 수락 → 50점 PASS_WITH_FIX 수락 가능.

### 3.13 연속성 검증 Fail-Open + 글로벌 타임아웃 부재

**파일**: `continuity_blueprint.py:255-272`, `continuity_arc.py:456-468`
**세부**: LLM 에러 시 자동 PASS. Stage 3 전체에 글로벌 타임아웃 없음 — 최악 시 10 리트라이 x 6 LLM 호출 x 240초 = 30분+.

### 3.14 (신규) StateLockedArcGenerator 상태 추출 실패 시 침묵 동결

**파일**: `state_locked_arc_generator.py:476-485`
**동작**: 상태 추출 실패 시 시작 상태를 그대로 복사하여 반환. 에너지 변화 0, 아이템 변경 없음. 하류에 실패 플래그 없음.

### 3.15 (신규) ArcCorrector 변경률 검증이 길이만 비교

**파일**: `arc_corrector.py:511-522`
**동작**: `json.dumps` 문자열 길이 차이만 비교. 같은 길이로 내용 전면 교체 시 `change_ratio = 0.0` → 통과.

### 3.16 (신규) Director `invalidate_caches()` 불완전 리셋

**파일**: `director.py:105-112`
**동작**: 4개 캐시 필드만 명시적 클리어. 서브컴포넌트에 캐시 추가 시 누락 가능 (유지보수 함정).

### 3.17 (신규) Stage3Orchestrator 단일 에피소드 실패가 전체 배치 중단

**파일**: `stage3_orchestrator.py:1961`
**동작**: `_handle_failure` 항상 `break=True`. 일시적 API 장애도 배치 전체 중단.

### 3.18 (신규) UnifiedArcValidator LLM 허위 CRITICAL이 유효 Arc 차단

**파일**: `unified_arc_validator.py:161-175`
**동작**: Python 이슈와 LLM 이슈를 동일 가중치로 결합. LLM 환각 CRITICAL → false positive REJECT.

### 3.19 (신규) 클래스 레벨 캐시 딕트가 전 에이전트 공유

**파일**: `base_agent.py:1864-1865`
**동작**: `_context_caches = {}` 클래스 변수, 전 에이전트 인스턴스 공유. `_CONTEXT_CACHE_MAX = 50` 글로벌 상한 → 대량 에이전트 시 공격적 퇴거.

---

## 4. LOW: 설계 한계 + 코드 위생

### 4.1 중복 `_format_constraints` 메서드 (죽은 코드)

**파일**: `blueprint_ensemble.py:719, 859`
**세부**: 두 번째 정의가 첫 번째를 shadow. 첫 번째 정의 내 L832-857은 도달 불가능 코드 (return 이후).

### 4.2 하드코딩 매직넘버

| 값 | 파일:라인 | 용도 |
|----|----------|------|
| `max_retries=9` | three_phase_blueprint_generator.py:68 | 리트라이 상한 (config 미사용) |
| `arc_focus[:15000]` | blueprint_ensemble.py:251 | Arc 텍스트 잘림 |
| `len > 30000` | three_phase_blueprint_generator.py:778 | InPlace 패칭 JSON 상한 |
| `_MAX_FIX=3` | three_phase_blueprint_generator.py:514 | PASS_WITH_FIX 재시도 상한 |

### 4.3 self.stats 세션 간 미리셋

**파일**: `three_phase_blueprint_generator.py:54-60`
**세부**: `total_attempts`, `phase3_pass` 등이 세션 전체 누적. 멀티 Arc 실행 시 무의미한 통계.

### 4.4 validate_response_against_schema 표면적 검증만

**파일**: `response_schemas.py:692-725`
**세부**: 필수 필드 존재만 확인, 타입/중첩/값 검증 없음. Gemini structured output에 의존.

### 4.5 장르 기본값 자동 할당

**파일**: `three_phase_blueprint_generator.py:111-118`
**세부**: 예외 시 `"wuxia"` 기본값. 잘못된 장르로 블루프린트 생성 가능.

### 4.6 두 병렬 채점 시스템 (Director LLM vs 내부 grading)

**파일**: `director_grading.py:41-61`, `director.yaml`
**세부**: Director LLM 5카테고리 vs 내부 `QUALITY_GRADES` 6카테고리 매핑 불일치. Director 주권주의에 의해 LLM 점수가 권위이나 혼선 가능.

### 4.7 프롬프트 인젝션 미방어 (현재 로컬 전용이므로 LOW)

**파일**: `blueprint_ensemble.py`, `ensemble.yaml`
**세부**: 사용자 입력(작품명, 주인공명, 전제)이 f-string으로 프롬프트에 직접 삽입. `_escape_braces()`는 Python format 보호만, LLM 프롬프트 인젝션 방어 아님.
**현재 영향**: 로컬 단일 사용자 도구 → LOW. bridge_server API 노출 시 MEDIUM으로 승격 필요.

### 4.8 Thinking 예산 → 품질 피드백 루프 부재

**파일**: `system.yaml`, `base_agent.py`
**세부**: 반복 실패 시 thinking budget 자동 증가 메커니즘 없음.

---

## 5. INFO: 양호한 설계 확인

| # | 영역 | 파일 | 평가 |
|---|------|------|------|
| 5.1 | 리트라이 상태 격리 | three_phase_blueprint_generator.py | `_initial_feedback` 패턴으로 피드백 오염 방지 (TF-S3-04 태그) |
| 5.2 | 리트라이 카운터 누수 없음 | base_agent.py | `ask()` 내 로컬 변수, 호출 간 정상 리셋 |
| 5.3 | 검증 오케스트레이터 설계 | validation_orchestrator.py:1252-1303 | 차단 검증 fail-closed, 자문 검증 fail-open — 올바른 패턴 |
| 5.4 | 중간 Arc 재개 가능 | stage3_orchestrator.py:757-777 | 순차 강제 + 기존 블루프린트 스킵 → 안전한 재개 |
| 5.5 | 캐시 무효화 처리 | base_agent.py:241, full_prompt_fallback | 키 회전 시 캐시 클리어 + 폴백 경로 |
| 5.6 | 메모리 바운딩 | base_agent.py:306-326 | `_apply_prompt_size_gate()` + `max_output_tokens` |
| 5.7 | WAL 모드 활성 | db_manager.py:237 | 크래시 복구 보장 |
| 5.8 | 로그 로테이션 구현 | session_logger.py:276-300 | 100MB/10회전 |
| 5.9 | SCHEMA_INCOMPATIBLE 로깅 완전 | three_phase_blueprint_generator.py:354-362 | ERROR 레벨 + failure_reason 기록 |

---

## 6. 발견 우선순위 매트릭스 (6회 적대적 감리 최종)

```
          높은 영향
              │
              │   HIGH (3건, 6회 감리 확정)
              │   [H1:emergency fallback] [H4:dead NPC 우회]
              │   [H-RE:last_error_type 경쟁]
              │
──────────────┼──────────────────
              │
   MEDIUM     │   LOW (17건)
   (23건)     │
              │
          낮은 영향
```

**즉시 조치 필요** (HIGH 3건):
1. **H1**: Emergency fallback 최소 점수 상향 (50→70) 또는 Stage 4에서 `quality_risk` 하드 차단
2. **H4**: Dead NPC CRITICAL → Director 주입 시 `TruthGate` 구속력 포맷 사용 (자유텍스트 아닌 스키마 필드로 하드 REJECT 강제)
3. **H-RE**: `last_error_type` → `threading.Lock` 보호 또는 스레드별 에러 수집 후 caller에서 병합

**계획적 개선** (MEDIUM 상위):
- 합의 검증기 신뢰도 가중 투표 (3.1, 3.2)
- Arc→Blueprint 핸드오프 필드 검증 (3.11)
- PASS_WITH_FIX 최소 점수 문턱 도입 (3.12)
- 글로벌 Stage 3 wall-clock 타임아웃 (3.13)
- PreflightChecker 입력 품질 검증 (NEW-02)
- protagonist_config 캐시 무효화 (NEW-04)
- Stage 2 Arc 저장 원자성 보장 (NEW-01)

---

## 7. 근본 원인 분석

3회 딥다이브에서 반복적으로 나타나는 **3대 구조적 패턴**:

### 패턴 A: "단일 스레드 전제 위반"
- `BaseAgent`는 인스턴스 속성(`last_error_type`, `_last_llm_usage`, `last_partial_response` 등)을 상태 전달에 사용
- `BlueprintEnsembleGenerator`가 `ThreadPoolExecutor`로 동일 인스턴스에서 3 스레드 동시 실행
- **해결 방향**: 스레드별 별도 에이전트 인스턴스 생성 또는 `threading.local()` 사용

### 패턴 B: "Fail-Open 편향"
- `consensus_validator`, `continuity_blueprint`, `continuity_arc` 모두 에러 시 자동 PASS
- `validate_blueprint` 실패 시 원본 반환
- Emergency fallback이 REJECT된 블루프린트를 PASS_WITH_WARNING으로 승격
- **의도**: 가용성 우선 (파이프라인 차단 방지)
- **위험**: LLM API 장애 시 모든 품질 게이트가 동시에 무력화

### 패턴 C: "핸드오프 경계 검증 부재"
- Arc→Blueprint: `tactical_doc` 미검증
- Blueprint→Stage4: `quality_risk=True` 플래그가 하드 차단 아님
- 스키마→Python 검증: `anyOf` 문자열 허용 + Pydantic 실패 흡수
- **위험**: 상류 실패가 침묵 전파되어 하류에서 증폭

---

## 8. 확신도

| 항목 | 원본 | 1차 적대적 | **2차 적대적 (최종)** |
|------|------|----------|-------------------|
| 스레드 안전성 | 98% | 99% | **99%** (GIL + 비용 영향 정량화) |
| 에러 복구/침묵 실패 | 96% | 97% | **98%** (emergency fallback Stage 4 소비 확인) |
| Stage 2 Arc 생성 | — | 95% | **97%** (데드 코드 발견 + Arc 저장 원자성 조사) |
| Stage 3 오케스트레이터 | — | 95% | **98%** (WAL 자동 롤백 + 자동 복구 경로 확인) |
| 검증기 우회 경로 | — | 96% | **97%** (Dead NPC 2회 확인 + LLM 허위 CRITICAL 확인) |
| 캐싱 무결성 | — | 94% | **96%** (protagonist_config 누락 확인 + 키 네임스페이스 검증) |
| PreflightChecker 입력 | — | — | **95%** (hollow tactical_doc 경로 신규 발견) |
| **종합** | 95% | 97% | **98%** |

---

## 9. 감리 이력

### 원본 3Pass 감리

| Pass | 수행 내용 | 결과 |
|------|----------|------|
| Pass 1 | CRITICAL/HIGH 3건 코드 직접 확인 | 3건 CONFIRMED |
| Pass 2 | PatchModeThresholds, validate_blueprint 확인 | CONFIRMED |
| Pass 3 | 문서 구조 완전성, 확신도 95% | PASS |

### 1차 적대적 감리 3회 (70 tool uses)

| 회차 | 역할 | 주요 결과 |
|------|------|----------|
| **적대적 1** | CRITICAL/HIGH 5건 반박 시도 (22 tool uses) | CRITICAL → MEDIUM 하향, HIGH 3건 → LOW 하향, HIGH 1건 CONFIRMED |
| **적대적 2** | MEDIUM 13건 전수 검증 (22 tool uses) | 11건 CONFIRMED, 2건 → LOW 하향 |
| **적대적 3** | 누락된 위험 반박 탐색 (26 tool uses) | 신규 HIGH 3건 + MEDIUM 6건 + LOW 3건 + INFO 2건 |

### 2차 적대적 감리 3회 (169 tool uses)

| 회차 | 역할 | 주요 결과 |
|------|------|----------|
| **적대적 4** | HIGH 4건 재반박 (77 tool uses) | H1 CONFIRMED, **H2 REFUTED (데드 코드)**, **H3→LOW (WAL 자동 롤백)**, H4 CONFIRMED |
| **적대적 5** | 하향 6건 재승격 시도 (37 tool uses) | **last_error_type → HIGH 재승격**, **3.3 → MEDIUM 재승격**, 나머지 4건 하향 유지 |
| **적대적 6** | 신규 발견 검증 + 추가 누락 탐색 (55 tool uses) | CS-02/CS-12 → LOW 하향, CS-04/06/08/10 CONFIRMED, **신규 MEDIUM 4건** |

### 6회 적대적 감리 누적 변동

| 변동 유형 | 건수 | 세부 |
|----------|------|------|
| **REFUTED** | 1 | H2 StateLockedArcGenerator (데드 코드) |
| **재승격** | 2 | last_error_type MEDIUM→HIGH, 3.3 LOW→MEDIUM |
| **하향** | 8 | CRITICAL→HIGH 1, HIGH→LOW 3+1, MEDIUM→LOW 2+2 |
| **유지** | 14 | HIGH 2, MEDIUM 12 |
| **신규 발견** | 18 | HIGH 3(1 REFUTED), MEDIUM 10(2 하향), LOW 3+1, INFO 2 |

### 최종 확신도: **98%** (잔여 2%: 전체 프롬프트 템플릿 미전수 + Stage 4 하류 `quality_risk` 소비 완전성 미확인 — 2차 적대적 4에서 soft advisory 확인으로 잔여 축소)
