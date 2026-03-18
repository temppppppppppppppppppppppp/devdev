# S6: Stage 3-4 + 교차 계층 SSOT

> 최종 갱신: 2026-03-18
> 소스: stage34-deep-dive, crosscut-deepdive, devils-advocate-pass3-audit
> 감리: Devil's Advocate 교정 적용 (6회 적대적 감리 + DA Pass 3)
> 확신도: 98%

---

## 1. 개관

| 계층 | 핵심 구성 | 역할 |
|------|----------|------|
| **Stage 3 Blueprint** | `three_phase_blueprint_generator` (오케스트레이터) + `blueprint_ensemble` (3전략 앙상블) | 에피소드 Blueprint 생성 |
| **Stage 4 Manuscript** | `chief_writer` (Writer) + `director_ensemble` (Director) + 6단 검증 파이프라인 | 원고 생성 + 품질 판정 |
| **교차 계층 (Crosscut)** | base_agent 락/캐시, MetricsCollector, 상태 저장, 멀티싱크 | 스테이지 횡단 숨겨진 이음매 |

**아키텍처 핵심 원칙**: "디렉터 주권주의(내각제)" -- Director LLM이 최종 PASS/REJECT/PASS_WITH_FIX 권한을 보유. 다른 모든 검증기는 advisory.

**교차 SSOT 참조**:
- ConstraintDB (아이템 제약 누적, 모순 탐지) → **S5 §4.1** 참조
- GenreGuards (장르별 검증 규칙, 무협 금지 용어/경지 체계) → **S5 §4.3** 참조
- PassRateMonitor (통과율 추적, AttemptRecord 33 필드) → **S7 §3** 참조
- response_schemas.py (anyOf 패턴, 스키마 타입) → **S4 §6** 참조 (본 문서는 verdict 상태만 기술)
- MetricsCollector (비용 추적, 스코프 스냅샷) → **S7 §2.2** 참조

---

## 2. Stage 3 Blueprint 생성

### 2.1 Three-phase blueprint generator (오케스트레이터)

3단계 순차 생성:
1. **Phase 1**: 제약 조건 블록 구축 (arc_data + prev_blueprint 기반)
2. **Phase 2**: Blueprint 초안 생성 (3전략 앙상블 호출)
3. **Phase 3**: Director 심사 → PASS/PASS_WITH_FIX/REJECT

재시도 루프 내에서 Phase 1 제약 블록(`cached_constraint_block`)은 retry > 0 시 재사용. DA Pass 3 검증: 제약 블록이 의존하는 `arc_data`/`prev_blueprint`는 재시도 루프 내에서 불변 -- 캐시 스테일 위험 없음(LOW).

### 2.2 Blueprint ensemble: 3전략 (action/emotion/dialogue)

| 전략 | 초점 | 후보 키 |
|------|------|---------|
| `action_focused` | 사건 밀도, 액션 비트 | `action` |
| `emotion_focused` | 감정 곡선, 내면 묘사 | `emotion` |
| `dialogue_focused` | 대사 비중, 캐릭터 음성 | `dialogue` |

3전략이 병렬 생성 후 Director 앙상블이 최종 후보를 선택. `candidate_key`로 PassRateMonitor에서 전략별 효율 추적 가능.

### 2.3 Scene count: 5 하드코딩 (range(1,6)) -- 의도적 설계

- `response_schemas.py:554`: `range(1, 6)` = scene_1 ~ scene_5
- 스키마 description(L560-563): `"Scene breakdown map keyed by scene_1..scene_5"` -- 의도적 설계 문서화
- Director 프롬프트가 5씬 강제, Gemini structured output이 스키마 키 강제
- 가변 씬 수가 필요하면 feature request이지, 결함이 아님
- **판정**: INFO (의도적 설계 제약)

### 2.4 PASS_WITH_FIX: 3회 패치 실패 시 → REJECT + 외부 재시도 (MEDIUM)

DA Pass 3 검증 결과:
- `three_phase_blueprint_generator.py:625-669`: `_fix_ok`가 False일 때
- L641: `verdict = "REJECT"` -- 명시적 REJECT 설정
- L642-644: 피드백 갱신 후 외부 재시도 루프 계속 진행
- **파이프라인이 미검증 Blueprint를 조용히 반환하지 않음**. REJECT로 처리하고 재시도.
- **심각도**: MEDIUM (재시도 소진 시 저품질 결과 가능성, 그러나 "미검증"은 아님)

### 2.5 quality_gate_failed / quality_risk: write-only 플래그 (Stage 4 미참조)

- **위치**: `three_phase_blueprint_generator.py:741-750`
- retry 소진 후 50점 이상 Blueprint가 `PASS_WITH_WARNING`으로 승격될 때:
  - `quality_gate_failed = True`
  - `quality_risk = True`
- `_stage3_meta`에 기록되지만, **Stage 4 오케스트레이터/포스트프로세서/인터뷰라운드에서 이 플래그를 전혀 참조하지 않음** (grep 0건)
- "write-only flag" 패턴 -- 기록만 되고 행동으로 이어지지 않음
- **심각도**: MEDIUM (MF-03)
- **즉시 개선**: Stage 4 진입 시 `quality_risk=True` Blueprint에 대해 Director 경고 주입 또는 retry 예산 확대 (~15줄)

### 2.6 quality_risk 불일치: 3곳 독립 추론 (OPP-05 결함)

| 위치 | 조건 | PASS_WITH_WARNING 포함? |
|------|------|----------------------|
| `three_phase_blueprint_generator.py:447` | `verdict in ("PASS_WITH_FIX", "PASS_WITH_WARNING")` | O |
| `unified_blueprint_validator.py:278` | `verdict in ("PASS_WITH_FIX", "PASS_WITH_WARNING")` | O |
| `director_ensemble.py:771` | `decision == "PASS_WITH_FIX"` | **X -- PASS_WITH_WARNING 누락** |

3곳 중 1곳이 다른 verdict set 사용 → **실제 결과 불일치 가능** (적대적 코드 검증에서 확인된 실제 결함).

---

## 3. Stage 4 원고 생성

### 3.1 Rejection rate: 45.5% (5/11) from production logs

프로덕션 데이터 정밀 분석 (`projects/0_260316/logs/pass_rate_monitor.json`):

| 에피소드 | 시도 수 | 결과 시퀀스 | 핵심 사유 |
|---------|---------|-----------|----------|
| ep1 | 1 | PASS | -- |
| ep2 | 1 | PASS (is_patch=true) | -- |
| ep3 | 1 | PASS | -- |
| ep4 | 3 | R→R→P | NPC 이름 변경(한진호→한태준) |
| ep5 | 4 | R→R→R→P | 사무실 속성 변경(낡은 오피스→신축) |
| ep6 | 1 | PASS | -- |

- 총 11 attempts, 6 PASS, 5 REJECT = **45.5% rejection rate**
- Stage 3은 동일 프로젝트에서 11/11 PASS(100%)
- ep5에서 in-place patch가 동일 이슈를 3회 연속 미해결 → full regeneration으로만 해결: "패치의 근본적 한계"
- **주의**: 샘플 크기 1 프로젝트(6 episodes) -- 통계적 유의성 제한

### 3.2 DB 저장 실패: 원고는 메모리에 존재, 진정한 데이터 손실은 디스크 풀 시에만

- **위치**: `stage4_orchestrator.py:898-913`
- `process_pass_result()` 반환 False 시 `break` → `final_manuscript`는 메모리에만 존재
- Episode Bible 메타 실패 시에는 원고 자체는 이미 DB 커밋됨
- **DB 저장 자체가 실패하는 경우(디스크 풀/권한)**에만 원고 미저장
- UI 로그에 실패 표시되어 사용자 인지 가능
- SQLite DB 쓰기 실패 확률 극히 낮음
- **심각도**: MEDIUM (MF-04)
- **즉시 개선**: DB 실패 시 `final_manuscript`를 `output_dir/emergency_ep_XXXX.txt`로 비상 덤프 (~10줄)

### 3.3 Stage 3 max-fail: 알림 존재하나 에스컬레이션 선택지 부재 (Stage 4와 비대칭)

| 항목 | Stage 3 | Stage 4 |
|------|---------|---------|
| 실패 알림 | `ctx.ui.log("❌ Blueprint 생성 실패")` (L1965) | `ctx.ui.log("⛔ 인간 검토 필요")` (L1360) |
| 감사 이벤트 | audit_event "all_retries_exhausted" (L2145-2150) | 있음 |
| 품질 위반 기록 | QualityDashboard violation (L2184-2195) | 있음 |
| **Operator 선택지** | **없음** -- batch loop이 자동 건너뛰기 | **있음** -- 재시도/건너뛰기/중단 |

"silent failure" 는 아님(알림 존재). 핵심 차이는 **인간 에스컬레이션 선택지의 비대칭**.

---

## 4. 6단 검증 파이프라인

### 4.1 Verdict 상태: 코드 6개 vs 스키마 3개

| Verdict | Schema 정의 | 실제 생산 | 최종 도달 |
|---------|------------|----------|----------|
| **PASS** | `response_schemas.py:132` | Director, Validator | 모든 sink |
| **PASS_WITH_FIX** | `response_schemas.py:132` | Director | 모든 sink |
| **REJECT** | `response_schemas.py:132` | Director | 모든 sink |
| CONDITIONAL_PASS | **없음** | validation_orchestrator, director_grading | **no-op** -- ensemble이 체계적으로 덮어씀 |
| PASS_WITH_WARNING | **없음** | three_phase_blueprint_generator | DB SQL WHERE절, failure_analyzer |
| FAILED | **없음** | pipeline result dict | 파이프라인 내부 국한 |

- CONDITIONAL_PASS: 코드 29건(modules/ 14 + tests/ 15) 존재하나 **최종 verdict에 0번 도달** -- no-op layer
- PASS_WITH_WARNING: schema 미정의지만 `db_manager.py:3150`에서 SQL WHERE절에 하드코딩

### 4.2 _UNCONDITIONAL_PASS_FLOOR = 85 (런타임 상수)

- `validation_orchestrator.py:174`에 런타임 상수로만 존재
- score >= 85 → PASS (무조건)
- score 70-84 → CONDITIONAL_PASS (ensemble에서 되돌림)
- `response_schemas.py`나 `constants.py`에 미정의 -- schema/contract 갭

### 4.3 Fail-open/closed 계층적 설계

| 검증기 | 실패 시 동작 | 설계 의도 |
|--------|------------|----------|
| **Preflight** | fail-open (PASS) | 전처리, 가용성 우선 |
| **BlockingValidator** | degraded (passed=True) | 12개 중 2개만 degradable, 나머지 10개 정상 |
| **Director LLM** | 주 판정 경로 | 최종 권한 |
| **ChainOfVerification** | fail-closed (REJECT) | LLM 에러 시에만 예외적 fail-open |
| **PostSelect** | fail-closed | 일시적 다운그레이드, 패치 모드 재시도 |

코드 내 `[FailClosed:...]` 태그 5개 발견. **계층별 의도적 차별 적용** 확인. 중앙 정책 문서만 부재.

### 4.4 BlockingValidator degraded mode: passed=True + failures 미포함

- `blocking_validator.py:176-182`: `except (ValueError, KeyError, RuntimeError)` → `{"passed": True, "degraded": True}`
- `ImportError`/`TypeError`/`AttributeError`는 명시적 재발생(L178-179, L187-188) -- 프로그래밍 에러 전파
- `degraded_checks` 리스트에 추가 + 경고 로그(L91-96) -- 추적 존재
- **그러나**: `passed: True` → `failures` 미포함. downstream `validation_orchestrator.py`에서 `degraded_checks` 필드 확인/처리 코드 없음
- 12개+ 검증 중 2개만 degradable. 나머지 10개(사망NPC/미소유아이템/파괴장소 등) 정상 동작.
- **심각도**: MEDIUM ("검증 통과 위장"보다 "advisory 신호 손실"이 정확한 표현)

---

## 5. Director 주권

### 5.1 Director = 최종 PASS/REJECT/PWF 권한 (내각제)

Director LLM이 모든 advisory 검증 결과를 수신한 뒤 최종 판정. Python 검증기는 advisory 신호를 수집하고, LLM이 판단하는 "Python 수집, LLM 판단" 아키텍처.

### 5.2 TruthGate: blocking=False (Python advisory), CRITICAL은 Director 프롬프트에 주입

- `truth_gate.py:24-63`: `blocking: False` 하드코딩(L45 early return, L62 정상 반환)
- `stage4_post_processor.py:845`: 경고 로그만 기록
- **2차 감리에서 발견된 핵심 완화 요소**:
  - `stage4_interview_round.py:5042-5078`: TruthGate는 9-way 병렬 자문 체인의 일부로 실행
  - L5071: 경고가 `"[TruthGate Advisory -- CRITICAL 경고 시 반드시 REJECT]"` 헤더와 함께 포맷
  - L2230-2238: `"[CRITICAL . TruthGate]"` 형식으로 Director 프롬프트에 직접 주입
  - `config/prompts/director.yaml:174,181,503,510`: `"CRITICAL(TruthGate: 사망 NPC 부활, 세계법칙 위반)만 자동 REJECT 사유입니다"` 명시
- Python `blocking: False`는 "Python 수집, LLM 판단" 아키텍처의 의도된 설계
- **심각도**: MEDIUM (Director LLM이 지시를 무시하는 경우로 위험 제한)

### 5.3 RetrospectiveValidator: advisory-only (4개 체크 + except auto-PASS)

- `retrospective_validator.py:82-241`: 4개 체크에서 `except Exception` → 자동 PASS
- **advisory 전용 보조 검증기** -- 점수 감점만 수행, PASS/REJECT 직접 결정 불가
- Director LLM + ContinuityValidator가 동일 이슈를 주 경로에서 검출
- **심각도**: LOW (LF-01)

### 5.4 ContinuityBlueprintValidator: Stage 3 프로덕션에서 NOT called

- `continuity_blueprint.py:237-272`: LLM 실패 시 PASS 반환
- **2차 감리에서 최초 발견**: `inspect()` 메서드가 현재 Stage 3 프로덕션 파이프라인에서 **호출되지 않음**
- 프로덕션 연속성 검증은 `director.check_blueprint_continuity_with_cache()` (순수 Python, LLM 무관)
- **심각도**: LOW (LF-02, 프로덕션 미사용)

### 5.5 Director 프롬프트 캡: 740KB 기본값

- `director_ensemble.py:294-308`: 기본 740KB 캡
- INFO (IF-02)

### 5.6 단일 후보 자동 REJECT (TF-36 의도적)

- `director_ensemble.py:894-901`: 후보가 1개뿐이면 자동 REJECT
- 앙상블 비교 없이 통과시키지 않는 품질 보호 장치
- INFO (IF-03, TF-36 의도적 설계)

---

## 6. 교차 계층 이음매

### 6.1 Lock ordering in base_agent: rotation → quota → cache (교착 없음)

- `base_agent.py:217-241`: 3중 락 중첩 존재
- 일관된 순서(rotation → quota → cache) 유지
- `_quota_lock` 보유 중 `_rotation_lock` 요청 경로 없음
- **판정**: REFUTED (교착 불가)

### 6.2 MetricsCollector reset(): 프로덕션 호출자 0건 (dead code)

- `metrics_collector.py:118-130`: `reset()` 경쟁 패턴 존재
- 프로덕션 호출자 **0건** -- dead code
- **심각도**: LOW (A-2)

### 6.3 ChainOfVerification fail-open: 좁은 교차 조건에서만 발현

- `chain_of_verification.py:136-148`: LLM 에러 시 `return ""` → `{"passed": True, ..., "summary": "파싱 실패 - 기본 통과"}`
- **핵심 완화 요소**: `quick_verify()` (Python-only, LLM 미사용)가 선행 실행
- LLM `verify()`는 `quick_verify` 실패 시에만 호출
- fail-open 발현 조건: **Python이 이미 의심을 표시한 상태**에서 LLM 확인만 누락되는 좁은 시나리오
- **심각도**: MEDIUM (E-1, "LLM 에러 AND quick_verify 실패" 교차 조건)

### 6.4 FactLedger/WorldState save() 반환값: 프로덕션 호출자 전원 무시

**FactLedger**:
- `fact_ledger.py:116-127`: `save()` → `bool` 반환 + `last_save_ok`/`last_save_error` 설정
- 프로덕션 호출자 전원(`stage4_post_processor.py:1394,1424`, `lite_mode/bridge/runner.py:1436,1544,1646`) 반환값 미확인
- 테스트 코드만 반환값 확인
- `rollback_to()` (L735-778): 에피소드 Bible 재생으로 전체 상태 재구축 + `save()` 호출 -- 진정한 복구 경로

**WorldState**: D-1과 동일 패턴, 동일 결론.

- **심각도**: MEDIUM (D-1/D-2, save() 반환값 미확인이나 rollback_to 복구 + SQLite 쓰기 실패 극히 드묾)

### 6.5 Multi-sink writes: 최대 4개 sink, 독립 try/except, 롤백 없음

실제 판정 기록 경로 (`stage4_interview_round.py`):

| Sink | 위치 | 대상 |
|------|------|------|
| 1 | L5933 | `pass_rate_monitor.record_attempt()` → JSON (조건부) |
| 2 | L5977 | `db.save_stage_attempt()` → SQLite |
| 3 | L5847 | `append_jsonl_record()` → JSONL |
| 4 | L2750/2912 | `session_logger.log_decision()` → JSONL |

- 각 싱크 독립 `try/except` -- 부분 실패 시 나머지 계속 진행, 롤백 없음
- `sink_alignment_summary()`: 사후(post-hoc) 비교만. write 시점 검증 없음.
- **심각도**: MEDIUM (D-3)

### 6.6 벡터 메모리 인덱스 실패: 비차단, 재시도 없음

- `stage4_post_processor.py:880-896`: `memorize_v20_episode` 실패 시 비차단 처리, 재시도 없음
- 유실되는 것은 벡터 인덱스이며 **원고 원본은 DB/파일에 별도 저장**
- `sync_v20_drafts(drafts_path=실제경로)` 함수가 구현되어 수동 복구 가능 (현재 `drafts_path=None`으로 noop)
- Gap detection용 `get_sync_status()` 함수도 존재하나 미연결
- **심각도**: MEDIUM (MF-01, SC-5 벡터 검색에서 해당 에피소드 누락)
- **즉시 개선**: 세션 시작 시 `sync_v20_drafts(drafts_path=실제경로)` 자동 호출 추가 (~5줄)

### 6.7 state_updates 화이트리스트: 알려진 키만 .get(), 미지 키 자동 무시

- `WorldState.update_from_state_changes()`가 **화이트리스트 방식** -- 알려진 키만 `.get()` 추출
- 알 수 없는 키는 자동 무시 -- 침투 시나리오 구조적 차단
- **판정**: LOW (LF-05, 구 H-06에서 하향)

### 6.8 adaptive_retry time.sleep(30): 프로덕션 호출자 0건 (dead code)

- `adaptive_retry.py:410-412`: `time.sleep(30)` 코드 존재
- `apply_strategy()` 프로덕션 호출자 **0건**. 테스트 코드만 호출.
- 프로덕션은 `record_failure()` + `get_retry_guidance()` + `get_injection_prompt()` 사용 -- sleep 미호출
- **판정**: INFO (dead code, E-2)

### 6.9 validate_response_against_schema(): 호출자 0건 (dead code)

- `response_schemas.py:692-725`: 필수 필드 존재만 체크하는 함수
- 호출자 **0건**. 시스템은 Gemini-only (Anthropic/OpenAI 미존재)
- **판정**: INFO (dead code, C-1)

---

## 7. 수치 요약표

| 지표 | 수치 |
|------|------|
| Stage 3 프로덕션 통과율 | 100% (11/11) |
| Stage 4 프로덕션 거부율 | 45.5% (5/11 attempts) |
| Stage 4 에피소드당 평균 시도 | 1.83회 |
| Blueprint 씬 수 | 5 (하드코딩, 의도적) |
| 6단 검증 Verdict 상태 | 코드 6개 / 스키마 3개 |
| _UNCONDITIONAL_PASS_FLOOR | 85점 |
| Director 프롬프트 캡 | 740KB |
| BlockingValidator degradable 검증 수 | 2/12+ |
| FactLedger/WorldState save() 반환값 확인 호출자 | 0 (프로덕션) |
| 멀티싱크 최대 수 | 4 (조건부 3) |
| Fail-open/closed 태그 | `[FailClosed:...]` 5개 |
| Dead code 항목 | 3 (reset, adaptive_retry sleep, validate_response_against_schema) |
| quality_risk 추론 위치 불일치 | 3곳 중 1곳 (OPP-05) |

---

## 8. 발견 사항

### 8.1 확인된 결함

| ID | 항목 | 심각도 | 설명 |
|----|------|--------|------|
| OPP-05 | quality_risk 불일치 | MEDIUM | 3곳 독립 추론 중 `director_ensemble.py:771`이 PASS_WITH_WARNING 누락 |
| MF-01 | 벡터 인덱스 자동 복구 부재 | MEDIUM | 비차단 실패 → SC-5 무음 품질 저하 |
| MF-02 | WorldState/FactLedger `_meta_db=None` 부분 커밋 | MEDIUM | 트랜잭션 없는 경로에서만 발현 |
| MF-03 | quality_gate_failed write-only 플래그 | MEDIUM | Stage 4에서 저품질 Blueprint 무차별 처리 |
| MF-04 | DB 실패 시 원고 비상 저장 부재 | MEDIUM | 디스크 풀 시에만 발현, 극히 드묾 |
| D-1/D-2 | save() 반환값 미확인 | MEDIUM | 호출자 전원 무시, rollback_to 복구 존재 |
| D-3 | 멀티싱크 트랜잭션 부재 | MEDIUM | 독립 try/except, 사후 정합성 체크만 |
| E-1 | CoV fail-open | MEDIUM | quick_verify 선행으로 범위 제한 |
| E-3 | TruthGate advisory-only | MEDIUM | Director REJECT 지시로 보완 |
| E-4 | BlockingValidator degraded PASS | MEDIUM | advisory 신호 손실, 2/12만 해당 |

### 8.2 Dead code 인벤토리

| 항목 | 위치 | 근거 |
|------|------|------|
| `MetricsCollector.reset()` | `metrics_collector.py:118-130` | 프로덕션 호출자 0건 |
| `adaptive_retry.apply_strategy()` / `time.sleep(30)` | `adaptive_retry.py:410-412` | 프로덕션 호출자 0건 |
| `validate_response_against_schema()` | `response_schemas.py:692-725` | 호출자 0건, Gemini-only |

### 8.3 설계 강점

| 강점 | 설명 |
|------|------|
| Director 주권(내각제) | 모든 검증기가 advisory, Director LLM이 최종 판정 |
| 계층적 fail-open/closed | Preflight(open) → Blocking(degraded) → CoVe/PostSelect(closed), 코드 태그로 의도 표시 |
| 3전략 앙상블 + 단일 후보 REJECT | 최소 2개 이상 후보 비교 보장 |
| 화이트리스트 state_updates | 미지 키 자동 무시로 침투 구조적 차단 |
| 일관된 락 순서 | rotation → quota → cache, 교착 불가 |
| rollback_to() 전체 복구 | FactLedger/WorldState 에피소드 Bible 재생으로 완전 재구축 |

---

## [부록 A] Devil's Advocate 교정 이력

DA Pass 3에서 검증된 핵심 교정:

| 원래 심각도 | 교정 후 | 항목 | 결정적 근거 |
|------------|---------|------|-----------|
| CRITICAL | **MEDIUM** | Cache key genre fallback | content_hash가 2차 격리 제공, "none" 반환 주장은 오류(실제 `""` 반환) |
| CRITICAL | **HIGH** | anyOf schema string/object | 기존 isinstance 가드가 존재, 문자열 반복 주장은 FALSE |
| CRITICAL | **LOW** | protagonist_name injection | 자가 호스팅 도구, 사용자=공격자, f-string 포맷 불일치일 뿐 |
| CRITICAL | **LOW** | _last_thinking stale | 진단 로그에만 영향, 생성 로직 무관 |
| CRITICAL | **LOW** | json.loads strict=False | Gemini JSON 모드가 NaN/Infinity 방지, repair 경로 전용 |
| HIGH | **LOW** | Fallback chain circular (flash→flash) | model_stack 중복 제거 + retry bounds가 무한 루프 방지 |
| HIGH | **MEDIUM** | PASS_WITH_FIX 3회 실패 | 코드가 REJECT + 재시도로 올바르게 처리 |
| 10건 High | 0건 High | Stage 3-4 딥다이브 전체 | 6회 적대적 감리로 전부 MEDIUM 이하로 재보정 |

**핵심 교훈**: 초기 조사의 5건 CRITICAL은 전부 하향. 기존 방어 메커니즘(isinstance 가드, content_hash, model_stack dedup, REJECT+retry)이 체계적으로 누락되어 있었음.

## [부록 B] 근거 파일

| 소스 문서 | 경로 | 역할 |
|----------|------|------|
| Stage 3-4 딥다이브 | `docs/2026-03-18/OPUS/stage34-deep-dive-underexplored-areas-3pass-audit.md` | MF-01~04, LF-01~24 |
| 크로스컷 딥다이브 | `docs/2026-03-18/OPUS/geuldobi-v2-crosscut-deepdive-hidden-seams-3pass-audit.md` | A-1~E-8, D-1~D-3 |
| DA Pass 3 | `docs/2026-03-18/OPUS/geuldobi-v2-devils-advocate-pass3-audit.md` | CRITICAL→LOW/MEDIUM 교정, FALSE finding 2건 |
| 정적 개선 조사 | `docs/2026-03-18/OPUS/geuldobi-v2-static-improvement-discovery-3pass-audit.md` | OPP-05 quality_risk 불일치 |

---

*S6 SSOT -- Stage 3-4 + 교차 계층 통합. 6회 적대적 감리 + DA Pass 3 교정 적용.*
*최종 확신도: 98%*
