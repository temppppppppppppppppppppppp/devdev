# Geuldobi V2 크로스컷 딥다이브: 잘 살피지 않는 이음매(Seam) 전수조사

Date: 2026-03-18
Status: **final** (3회 조사 → 6회 적대적 감리 완료, 확신도 82%)
Canonical Path: `docs/2026-03-18/OPUS/geuldobi-v2-crosscut-deepdive-hidden-seams-3pass-audit.md`
Baseline Commit: `d4e96804`
Survey Mode: 3회 병렬 딥다이브 → 6회 적대적 감리 (코드 직접 대조, 호출자 추적, 방어 메커니즘 확인)
조사 범위: **전체 스테이지 횡단 — 기존 조사에서 누락된 아키텍처 이음매(seam)**

---

## 0. Executive Summary

3회 병렬 조사 후 **6회** 적대적 감리로 코드 직접 대조.
초기 24건 → 1차 감리(3회) 7건 기각 → 2차 감리(3회) 추가 4건 기각/하향.

| 심각도 | 건수 | 발견 |
|--------|------|------|
| **MEDIUM** | 4 | E-1 CoV fail-open, D-1/D-2 save() 미확인, E-3 TruthGate advisory |
| **LOW** | 5 | A-2 싱글톤(dead), A-3 TOCTOU(무해), A-4 스냅샷(희귀), B-2 캐시(hash포함), C-2 Pydantic(이중실패) |
| **INFO** | 4 | B-4 메트릭정리, C-1 dead code, C-3 설계제약, E-5 가설적 |
| **REFUTED/삭제** | 11 | A-1, A-5, B-1, B-3, C-4, D-3 싱크목록부정확→유지(교정), E-2, E-6, E-7, E-8 |
| **합계 생존** | **13건** | (REFUTED 11건 제거) |

**최종 생존 핵심 발견:**
1. **E-1 ChainOfVerification fail-open** — LLM 에러 시 `{passed: True}` 반환. 단, `quick_verify()` Python 게이트 뒤에 위치하여 위험 범위 제한적 (**MEDIUM**)
2. **D-1/D-2 save() 반환값 미확인** — FactLedger/WorldState의 `save()`가 `bool` 반환하나 **프로덕션 호출자 전원이 반환값 무시**. `rollback_to()` 수동 복구 존재 (**MEDIUM**)
3. **E-3 TruthGate advisory-only** — `blocking: False` 하드코딩. 단, CRITICAL 경고가 Director 프롬프트에 `"CRITICAL만 자동 REJECT 사유"` 지시와 함께 주입됨 (**MEDIUM**)
4. **E-4 BlockingValidator degraded=passed:True** — 런타임 에러 시 `passed: True` 반환, `failures` 미포함 (**MEDIUM**)

---

## 이음매 A: 락 순서 & 싱글톤 경쟁

### A-1. [REFUTED] 3중 락 중첩 교착 위험

**파일**: `base_agent.py:217-241`
**판정**: 락 중첩은 존재하나 일관된 순서(rotation→quota→cache)가 유지됨. `_quota_lock` 보유 중 `_rotation_lock` 요청 경로 없음. **교착 불가.**

---

### A-2. [LOW] MetricsCollector 싱글톤 reset() 경쟁

**파일**: `metrics_collector.py:118-130`
**판정**: 경쟁 패턴 존재 확인. `reset()` 프로덕션 호출자 **0건** — dead code.

---

### A-3. [LOW] _key_rotation_pending TOCTOU

**파일**: `base_agent.py:618-621`
**판정**: TOCTOU 윈도우 존재. `_try_rotate_key()` 내부에서 `_rotation_lock` 재획득 + 모든 조건 재검증. 최악의 경우 중복 no-op 호출 1회. **무해.**

---

### A-4. ~~[MEDIUM]~~ → [LOW] Quota 스냅샷 즉시 스테일

**파일**: `base_agent.py:948-949`

```python
with BaseAgent._quota_lock:
    quota_snapshot = dict(BaseAgent._quota_exhausted_models)
```

**1차 감리**: 코드 일치 확인, CONFIRMED MEDIUM.
**2차 감리 교정**:
- 스냅샷은 직후 tight loop(2-3 모델)에서 **마이크로초 내 소비**
- `clear()`는 `_try_rotate_key()` 내에서만 호출 — 세션당 최대 N-1회 (API 키 수 - 1)
- 경합 시에도 `primary_model` 폴백(L960-965)이 정상 작동 → 429 리트라이 경로가 처리

**판정**: **DOWNGRADED (MEDIUM → LOW)** — 마이크로초 레이스 윈도우 + 희귀 트리거 + 정상 폴백 존재.

---

### A-5. [REFUTED] API 키 회전 경계 조건

초기 키(index 0) + N-1회 회전 = N개 키 전부 시도. 로직 정상.

---

## 이음매 B: 캐시 수명주기 & 무효화

### B-1. [REFUTED] Cumulative Bible 캐시 프로젝트 간 오염

`DBManager`는 프로젝트별 별도 인스턴스 (project_manager.py:72). 재사용 경로 없음.

---

### B-2. [LOW] Context Cache 버전 관리

**파일**: `base_agent.py:1895`
실제 코드: `cache_key = f"{cache_type}_{project_name}_{content_hash}"` — **content_hash 이미 포함.** 원래 주장(hash 미포함) 오류. 잔존 엔트리의 미미한 메모리 낭비만 해당.

---

### B-3. [REFUTED] Context Cache TTL 미강제

모든 `_context_caches` 읽기 경로가 `_get_or_create_context_cache()` 경유 또는 전체 클리어. TTL 우회 경로 없음.

---

### B-4. [INFO] MetricsCollector 스테일 메트릭 정리

`end_call()` (L272)에서 완료 메트릭 즉시 삭제. >50건 임계값은 고아 메트릭(end_call 미호출)만 대상. 합리적 가드.

---

## 이음매 C: 스키마 검증 우회 경로

### C-1. [INFO] validate_response_against_schema() — Dead Code

**파일**: `response_schemas.py:692-725`
함수 내용(필수 필드 존재만 체크) 확인. **호출자 0건.** 시스템은 Gemini-only (Anthropic/OpenAI 미존재). Dead code.

---

### C-2. ~~[HIGH]~~ → [LOW] Pydantic validate_blueprint fail-open + 얕은 복사 머지

**파일**: `models/blueprint.py:76-87`, `three_phase_blueprint_generator.py:838-851`

**1차 감리**: Pydantic fail-open + 얕은 복사 확인. PARTIALLY CONFIRMED HIGH.
**2차 감리 교정**:
- L851에서 `validate_blueprint(result)` 호출 → **성공 시** `model_dump()`가 새 dict 생성, 모든 얕은 참조 **단절**
- Blueprint 모델은 `extra="allow"` (L46) + 기본값 완비 → Pydantic 실패는 극히 드묾
- 얕은 복사 오염 발현 조건: LLM이 스키마 이탈 블루프린트 생성 **AND** Pydantic 검증도 실패하는 **이중 실패** 필요
- `_previous_best`는 이미 `validate_blueprint`을 통과한 결과물(L680) → 정상 경로에서는 항상 새 dict

**판정**: **DOWNGRADED (HIGH → LOW)** — fail-open 패턴 존재는 사실. 그러나 성공 경로(대부분)에서 `model_dump()`가 참조를 단절하고, 이중 실패 조건에서만 발현.

---

### C-3. ~~[MEDIUM]~~ → [INFO] Blueprint 씬 수 하드코딩 (5개 고정)

**파일**: `response_schemas.py:554`

**2차 감리 교정**:
- `range(1, 6)` = scene_1~scene_5 확인
- 스키마 description (L560-563): `"Scene breakdown map keyed by scene_1..scene_5"` — **의도적 설계 문서화**
- Director 프롬프트가 5씬 강제, Gemini structured output이 스키마 키 강제
- 가변 씬 수가 필요하면 feature request이지, 결함이 아님

**판정**: **DOWNGRADED (MEDIUM → INFO)** — 의도적 설계 제약. 결함이 아닌 설계 결정.

---

### C-4. ~~[MEDIUM]~~ → [REFUTED] fix_scope 빈 문자열 vs None 모호

**파일**: `three_phase_blueprint_generator.py:235-237`

**2차 감리 교정**:
- Director 스키마 `response_schemas.py:134-138`: `fix_scope`는 **required** 필드 + `enum=["inplace", "partial", "full"]`
- Gemini structured output이 enum을 강제 → 빈 문자열 반환 불가
- `_prev_fix_scope = ""` (L158)는 초기 센티넬이며, 이 시점에서 `_previous_best is None` → 전체 조건이 `False`로 단락 → **빈 문자열 분기에 도달 불가**
- `not _prev_fix_scope` 폴백(L237)은 스키마 강제 실패 시의 방어 코드

**판정**: **REFUTED** — enum 필수 필드. 빈 문자열은 도달 불가능 분기.

---

## 이음매 D: 상태 트랜잭션 부재

### D-1. ~~[HIGH]~~ → [MEDIUM] FactLedger save() 반환값 미확인

**파일**: `fact_ledger.py:116-127 (save), 137 (update), 735-778 (rollback_to)`

**핵심 발견** (2차 감리에서 구체화):
- `save()` → `bool` 반환 + `last_save_ok`/`last_save_error` 설정 **확인**
- **프로덕션 호출자 전원이 반환값 무시**:
  - `stage4_post_processor.py:1394` — `self.ctx.fact_ledger.save()` 반환값 미확인
  - `stage4_post_processor.py:1424` — 동일
  - `lite_mode/bridge/runner.py:1436,1544,1646` — 동일
  - 테스트 코드(`test_fact_ledger.py:138,150`)만 반환값 확인
- `update_from_state_changes()` → `save()` 페어링은 **모든 호출자에서 존재** (L1380→L1394, L1418→L1424)
- `rollback_to()` (L735-778): 에피소드 Bible 재생으로 **전체 상태 재구축** + L778에서 `save()` 호출. 진정한 복구 경로.

**판정**: **DOWNGRADED (HIGH → MEDIUM)** — 실제 결함: save() 반환값 미확인. 그러나 (a) 데스크톱 앱에서 SQLite 쓰기 실패는 극히 드묾, (b) `rollback_to()` 전체 복구 가능, (c) `last_save_ok` 필드로 사후 감지 가능.

---

### D-2. ~~[HIGH]~~ → [MEDIUM] WorldStateManager 동일 패턴

**파일**: `world_state.py:129-139 (_load_or_init), 141-152 (save), 1262-1303 (rollback_to)`

D-1과 동일 패턴, 동일 결론. `rollback_to()` L1262-1303 확인. 프로덕션 호출자 반환값 미확인 확인.

---

### D-3. [MEDIUM] 멀티 Sink 쓰기에 트랜잭션 경계 부재

**2차 감리 교정**:
- 실제 판정 기록 경로 (`stage4_interview_round.py:5851-6009`, `_record_s4_attempt`):
  - **Sink 1**: `pass_rate_monitor.record_attempt()` (L5933) → `pass_rate_monitor.json`
  - **Sink 2**: `db.save_stage_attempt()` (L5977) → SQLite `stage_attempts`
  - **Sink 3**: `append_jsonl_record()` (L5847) → `episode_production.jsonl`
  - **Sink 4**: `session_logger.log_decision()` → `decisions.jsonl`
- 각 싱크 독립 `try/except` — 부분 실패 시 나머지 계속 진행, 롤백 없음 **확인**
- `sink_alignment_summary()`:
  - `bridge_server.py` — 대시보드 수동 호출 **확인**
  - `stage4_canary_tools.py:190-195` — 캐너리 하니스에서 자동 호출 (정상 파이프라인은 아님)
  - **정상 에피소드 생산 경로에서 자동 정합성 체크 없음** 확인
- **1차 문서 싱크 목록 오류 교정**: `runtime_audit.jsonl`은 판정 기록 시점의 별도 싱크가 아님. 정확한 목록은 위 4개.

**판정**: **CONFIRMED (MEDIUM)** — 트랜잭션 부재 확인. HIGH에서 MEDIUM으로 재조정: 데스크톱 앱의 디스크 풀은 극히 드물고, 캐너리 하니스가 준자동 정합성 체크 제공.

---

## 이음매 E: 검증 체인 단절

### E-1. ~~[CRITICAL]~~ → [MEDIUM] ChainOfVerification LLM 실패 시 가짜 "통과"

**파일**: `chain_of_verification.py:136-148 (_call_llm), 150-161 (_parse_result)`

**코드 경로 확인 (6회 감리 전체에서 확정)**:
- `_call_llm`: exception → `return ""` **확인** (L146-148)
- `_parse_result`: `""` → `JSONDecodeError` → `{"passed": True, ..., "summary": "파싱 실패 - 기본 통과"}` **확인** (L161)
- `verify()`: `result.get("passed", True)` **확인** (L274)

**2차 감리 교정 — 문서가 누락한 핵심 완화 요소**:
- ChainOfVerification은 `stage4_orchestrator.py:993-1033`에서 호출
- **L1006**: `quick_verify()` (Python-only, LLM 미사용) **선행 실행**
- LLM `verify()`는 `quick_verify` **실패 시에만** 호출 (L1007-1012)
- fail-open 발현 조건: Python `quick_verify`가 문제 감지 → LLM 확인 요청 → LLM 실패 → 가짜 통과
- 즉, **Python이 이미 의심을 표시한 상태**에서 LLM 확인만 누락되는 좁은 시나리오

**판정**: **DOWNGRADED (CRITICAL → MEDIUM)** — fail-open 메커니즘은 의심 없이 확인됨. 그러나 `quick_verify()` Python 게이트가 선행하므로 무방비 상태가 아님. 위험 범위가 "LLM 에러 AND quick_verify 실패"인 좁은 교차 조건으로 제한.

---

### E-2. ~~[MEDIUM]~~ → [INFO] 동기 sleep()이 파이프라인 차단

**파일**: `adaptive_retry.py:410-412`

**2차 감리 교정**:
- `time.sleep(30)` 코드 존재 **확인** (L412)
- **그러나** `apply_strategy()` 프로덕션 호출자 **0건**. 테스트 코드(`tests/test_adaptive_retry.py:33`)만 호출.
- 프로덕션은 `AdaptiveRetryManager.record_failure()` + `get_retry_guidance()` + `get_injection_prompt()` 사용 — **이들은 `time.sleep()`을 호출하지 않음**

**판정**: **DOWNGRADED (MEDIUM → INFO)** — Dead code. 30초 sleep은 프로덕션에서 도달 불가.

---

### E-3. ~~[HIGH]~~ → [MEDIUM] TruthGate가 Advisory-Only

**파일**: `truth_gate.py:24-63`

**코드 확인 (6회 감리 전체에서 확정)**:
- `blocking: False` 하드코딩 (L45 early return, L62 정상 반환) **확인**
- `stage4_post_processor.py:845`: 경고 로그만 기록 **확인**

**2차 감리 교정 — 문서가 누락한 핵심 완화 요소**:
- `stage4_interview_round.py:5042-5078` (`_advisory_truth_gate`): TruthGate가 **9-way 병렬 자문 체인**의 일부로 실행
- L5071: 경고가 `"[TruthGate Advisory -- CRITICAL 경고 시 반드시 REJECT]"` 헤더와 함께 포맷
- L2230-2238: `"[CRITICAL . TruthGate]"` 형식으로 **Director 프롬프트에 직접 주입**
- `config/prompts/director.yaml:174,181,503,510`: **"CRITICAL(TruthGate: 사망 NPC 부활, 세계법칙 위반)만 자동 REJECT 사유입니다"** 명시
- 즉, Python 레이어는 advisory이나 **Director LLM에게는 CRITICAL = REJECT 지시**가 전달됨

**판정**: **DOWNGRADED (HIGH → MEDIUM)** — Python `blocking: False`는 사실이나, 이는 "Python 수집, LLM 판단" 아키텍처의 의도된 설계. CRITICAL 경고는 Director에게 강제 REJECT 지시와 함께 전달됨. 위험은 Director LLM이 지시를 무시하는 경우로 제한.

---

### E-4. [MEDIUM] BlockingValidator degraded=passed:True — CONFIRMED

**파일**: `blocking_validator.py:176-182, 187-191`

**코드 확인 (6회 감리 전체에서 확정)**:
- `except (ValueError, KeyError, RuntimeError)` → `{"passed": True, "degraded": True}` **확인** (L182)
- `ImportError`/`TypeError`/`AttributeError`는 명시적 재발생 (L178-179, L187-188) — 프로그래밍 에러 전파
- `degraded_checks` 리스트에 추가 + 경고 로그 (L91-96) + 결과 dict에 포함 (L143-144) **확인**
- **그러나**: `passed: True` → `failures` 미포함 (L97-98). 전체 `passed` = `len(failures) == 0` (L137). degraded는 blocking에 영향 없음 **확인**
- `validation_orchestrator.py`에서 `degraded_checks` 필드 확인/처리 코드 **없음** 확인
- BlockingValidator 자체도 advisory 모드 (L454: "즉시 REJECT 대신 결과를 누적하여 후속 Director 판정에 위임")

**판정**: **CONFIRMED (MEDIUM)** — 이전 HIGH에서 재조정. `degraded` 추적 존재하나 downstream에서 미활용. BlockingValidator 자체가 advisory 역할이므로 "검증 통과 위장"보다는 "advisory 신호 손실"이 정확한 표현.

---

### E-5. [INFO] justification_patterns 모듈 부재 시 체크 우회

**파일**: `blocking_validator_consistency_checks.py:13-21`

**2차 감리 교정**:
- fail-open 패턴 확인 (L39-40)
- `justification_patterns.py` **존재** 확인
- 해당 모듈의 import: **순수 Python dict 리터럴 + 함수만**. 외부 의존성 0건. 정상 환경에서 import 실패 불가.

**판정**: **DOWNGRADED (MEDIUM → INFO)** — 모듈 존재 + 외부 의존성 없음. 파일 삭제/손상 시에만 발현하는 극단적 가설.

---

### E-6. [INFO] 리트라이 컨텍스트 중첩 — Dead Code

`AdaptiveRetryStrategy.should_retry()` 프로덕션 호출자 **0건**. 변수명도 `attempt` (단수).

---

### E-7. [INFO] required_scenes 비활성화

Python 체크 비활성화 확인. **Director(LLM)가 Blueprint 원문 대조로 수행** (코드 주석 L49). 의도된 대체.

---

### E-8. [REFUTED] 연속성 피드백 리트라이 간 오염

`_initial_feedback` 리셋(L186) + `_build_strategy_feedback()` 분리(L187) = 의도된 피드백 전파.

---

## 근본 원인 분석: 6회 감리 후 생존한 2대 패턴

### 패턴 1: "Fail-Open 편향" (E-1, E-3, E-4)

검증 계층의 에러 시 자동 PASS:
- **ChainOfVerification**: LLM 에러 → `{passed: True}` (E-1). **완화**: quick_verify Python 게이트 선행.
- **TruthGate**: `blocking: False` 하드코딩 (E-3). **완화**: CRITICAL은 Director에게 REJECT 지시와 함께 전달.
- **BlockingValidator**: degraded → `{passed: True}` (E-4). **완화**: ImportError 등은 재발생.

**구조적 원인**: "Python 수집, LLM 판단" 아키텍처에서 Python 검증은 의도적으로 advisory. **진정한 위험**은 (a) LLM 자체가 실패하는 경우(E-1), (b) Director LLM이 advisory 무시하는 경우(E-3).

### 패턴 2: "save() 반환값 미확인" (D-1, D-2)

`FactLedger`/`WorldStateManager`의 `save()` → `bool` 반환하나 **프로덕션 호출자 전원 무시**:
- `stage4_post_processor.py:1394, 1424` — 미확인
- `lite_mode/bridge/runner.py:1436, 1544, 1646` — 미확인

**완화**: `rollback_to()` 전체 복구 + `last_save_ok` 사후 감지 + SQLite 쓰기 실패는 데스크톱에서 극히 드묾.

---

## 확신도 (6회 적대적 감리 후 최종)

| 이음매 | 초기 | 1차 감리 후 | 2차 감리 후 | 변동 이유 |
|--------|------|-----------|-----------|----------|
| A. 락/싱글톤 | 98% | 60% | **55%** | A-4 추가 하향 (마이크로초 윈도우) |
| B. 캐시 | 95% | 40% | **40%** | 변동 없음 |
| C. 스키마 | 97% | 75% | **50%** | C-2 이중실패 조건, C-3 설계제약, C-4 REFUTED |
| D. 트랜잭션 | 96% | 80% | **75%** | D-1/D-2 하향, D-3 싱크목록 교정 |
| E. 검증 | 94% | 78% | **72%** | E-1 quick_verify 게이트, E-2 dead code, E-3 Director REJECT 지시 |
| **종합** | **96%** | **67%** | **59%** | 2차 감리에서 호출자 추적 + 완화 메커니즘 발견이 추가 교정 요인 |

---

## 6회 적대적 감리 이력

| Pass | 검증 범위 | 핵심 결과 |
|------|----------|----------|
| **1차 (A+B)** | A 5건 + B 4건 | A-1 교착 REFUTED, B-1 캐시 REFUTED, B-2 hash 포함 발견 |
| **2차 (C+D)** | C 4건 + D 3건 | C-1 dead code, D-1/D-2 rollback_to() 발견 |
| **3차 (E)** | E 8건 | E-7 Director 대체 발견, E-8 의도된 설계 확인 |
| **4차 (D 재검증)** | D 3건 | save() 호출자 전수 추적 — **전원 반환값 미확인** 확인. D-3 캐너리 하니스 호출 발견 |
| **5차 (E 재검증)** | E 5건 | E-1 quick_verify 선행 게이트 발견. E-2 apply_strategy() 호출자 0건. E-3 Director REJECT 지시 발견 (director.yaml:174,503) |
| **6차 (A+C 재검증)** | A-4 + C 4건 | A-4 마이크로초 윈도우 확인. C-2 model_dump 참조 단절. C-3 의도적 설계. C-4 enum 필수→빈 문자열 도달 불가 |

---

## 최종 발견 요약 (6회 적대적 감리 후)

| # | 발견 | 최종 심각도 | 판정 | 핵심 근거 |
|---|------|-----------|------|----------|
| A-1 | 3중 락 교착 | — | **REFUTED** | 교착 경로 없음 |
| A-2 | 싱글톤 reset | LOW | dead code | reset() 호출자 0건 |
| A-3 | TOCTOU pending | LOW | 무해 | 내부 재검증 |
| A-4 | Quota 스냅샷 | LOW | 희귀 | μs 윈도우 + 정상 폴백 |
| A-5 | 키 회전 경계 | — | **REFUTED** | N-1 회전 = N개 시도 정상 |
| B-1 | Bible 캐시 | — | **REFUTED** | DBManager 프로젝트별 |
| B-2 | Context 캐시 | LOW | hash 포함 | L1895 content_hash 확인 |
| B-3 | TTL 미강제 | — | **REFUTED** | 전경로 강제 확인 |
| B-4 | 메트릭 정리 | INFO | 고아만 | end_call 즉시 삭제 |
| C-1 | 스키마 검증 | INFO | dead code | 호출자 0건 + Gemini-only |
| C-2 | Pydantic+얕은복사 | LOW | 이중실패 | model_dump 참조 단절 |
| C-3 | 씬 수 5고정 | INFO | 설계제약 | 의도적 + 문서화 |
| C-4 | fix_scope 모호 | — | **REFUTED** | enum 필수, 도달 불가 |
| D-1 | FactLedger save | **MEDIUM** | 반환값 미확인 | 호출자 전원 무시 + rollback_to 존재 |
| D-2 | WorldState save | **MEDIUM** | 동일 | D-1과 동일 |
| D-3 | 멀티싱크 | **MEDIUM** | 트랜잭션 부재 | 캐너리 준자동, 인라인 없음 |
| E-1 | CoV fail-open | **MEDIUM** | 좁은 범위 | quick_verify 선행 |
| E-2 | 동기 sleep | INFO | dead code | apply_strategy 호출자 0건 |
| E-3 | TruthGate | **MEDIUM** | Director 보완 | CRITICAL→REJECT 지시 전달 |
| E-4 | degraded PASS | **MEDIUM** | advisory 손실 | passed:True, failures 미포함 |
| E-5 | justification | INFO | 가설적 | 모듈 존재 + 외부 의존성 0 |
| E-6 | 리트라이 중첩 | INFO | dead code | should_retry 호출자 0건 |
| E-7 | required_scenes | INFO | Director 대체 | docstring L49 |
| E-8 | 피드백 오염 | — | **REFUTED** | 의도된 설계 |

**최종**: MEDIUM **4건** + LOW **5건** + INFO **4건** = 13건 생존. REFUTED 11건 제거.

**CRITICAL 0건** — 6회 감리를 거친 결과, 초기 CRITICAL 7건은 전부 하향 또는 기각됨.
