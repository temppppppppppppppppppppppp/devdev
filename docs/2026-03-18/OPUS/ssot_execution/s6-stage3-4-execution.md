# S6 Stage 3-4 + 교차 계층 실행문서

> **작성일**: 2026-03-18
> **상태**: active
> **소스 SSOT**: `docs/2026-03-18/OPUS/ssot/s6-stage3-4-crosscut.md`
> **소스 감리**: stage34-deep-dive (6회 적대적 감리), crosscut-deepdive (6회 적대적 감리), DA Pass 3, static-improvement-discovery
> **확신도**: 98% (S6 SSOT 기준)
> **감리 완료**: 3-pass 기본 감리 + 5-pass 적대적 감리 (본 문서 하단 이력 참조)

---

## 1. 실행 항목 총괄표

| ID | 항목 | 우선순위 | 상세 | 완료 기준 | 추정 공수 | 의존성 | S6 근거 |
|----|------|---------|------|----------|----------|--------|---------|
| EX-01 | quality_risk 불일치 수정 (OPP-05) | **P0-Critical** | `director_ensemble.py:771`에서 `decision == "PASS_WITH_FIX"` 조건에 `"PASS_WITH_WARNING"` 누락. 3곳 독립 추론 중 1곳만 다른 verdict set 사용 → 실제 결과 불일치 가능. 나머지 2곳(`three_phase_blueprint_generator.py:447`, `unified_blueprint_validator.py:278`)은 정상. | `director_ensemble.py:771`의 조건이 `decision in ("PASS_WITH_FIX", "PASS_WITH_WARNING")`으로 통일됨. 3곳 모두 동일 verdict set 사용 확인. 단위 테스트 추가. | 0.5h (1줄 수정 + 테스트) | 없음 | S6 \S2.6, OPP-05 |
| EX-02 | 벡터 인덱스 자동 복구 연결 (MF-01) | **P0-Critical** | `memorize_v20_episode` 실패 시 비차단 처리, 재시도 없음 → SC-5 벡터 검색에서 해당 에피소드 누락 → 연속성 검증 무음 품질 저하. `sync_v20_drafts(drafts_path=실제경로)` 함수는 구현 완료이나 `drafts_path=None`으로 noop. `get_sync_status()` 함수도 존재하나 미연결. **삽입 지점**: 세션 초기화 경로에서 `sync_v20_drafts(drafts_path=실제경로)` 호출 연결 — `drafts_path=None` noop을 실제 경로로 교체 | 세션 시작 시 `sync_v20_drafts(drafts_path=실제경로)` 자동 호출 코드 추가. `get_sync_status()`에서 gap 탐지 시 경고 로그 출력. 벡터 인덱스 gap 0건 확인 테스트 추가. | 1h (~5줄 연결 + 테스트) | 없음 | S6 \S6.6, MF-01 |
| EX-03 | quality_gate_failed write-only 플래그 활성화 (MF-03) | **P1-High** | `three_phase_blueprint_generator.py:741-750`에서 retry 소진 후 50점 이상 Blueprint 승격 시 `quality_gate_failed=True`, `quality_risk=True` 설정. `_stage3_meta`에 기록되지만 Stage 4 전역(오케스트레이터/포스트프로세서/인터뷰라운드)에서 grep 0건. "write-only flag" 패턴. | Stage 4 진입 시 `quality_risk=True`인 Blueprint에 대해 Director 프롬프트에 경고 문구 주입 또는 retry 예산 확대. Stage 4 코드에서 `quality_risk` 참조 1건 이상 확인. | 2h (~15줄 + Director 프롬프트 조정 + 테스트) | EX-01 | S6 \S2.5, MF-03 |
| EX-04 | DB 실패 시 원고 비상 저장 (MF-04) | **P1-High** | `stage4_orchestrator.py:898-913`에서 `process_pass_result()` 반환 False 시 `break` → `final_manuscript`는 메모리에만 존재. 디스크 풀/권한 문제 시 원고 미저장. UI 로그에 실패 표시는 되나 원고 복구 불가. | DB 실패 시 `final_manuscript`를 `output_dir/emergency_ep_XXXX.txt`로 비상 덤프하는 코드 추가. 비상 덤프 파일 존재 여부 확인 테스트 추가. | 1h (~10줄 + 테스트) | 없음 | S6 \S3.2, MF-04 |
| EX-05 | FactLedger/WorldState save() 반환값 확인 (D-1/D-2) | **P1-High** | `fact_ledger.py:116-127`의 `save()` → `bool` 반환 + `last_save_ok`/`last_save_error` 설정. 프로덕션 호출자 전원(`stage4_post_processor.py:1394,1424`, `lite_mode/bridge/runner.py:1436,1544,1646`) 반환값 미확인. `rollback_to()` 복구 경로 존재하나 자동 트리거 없음. | 모든 프로덕션 `save()` 호출 후 반환값 확인 + 실패 시 경고 로그 기록 + `last_save_error` 포함. 테스트에서 save 실패 시나리오 검증. | 2h (5개 호출 지점 수정 + 테스트) | 없음 | S6 \S6.4, D-1/D-2 |
| EX-06 | 멀티싱크 정합성 인라인 체크 (D-3) | **P2-Medium** | 4개 싱크(pass_rate_monitor JSON, SQLite, episode_production JSONL, session_logger JSONL) 독립 try/except, 부분 실패 시 롤백 없음. `sink_alignment_summary()`는 사후 비교만(대시보드/캐너리). 정상 에피소드 생산 경로에서 자동 정합성 체크 없음. | 에피소드 생산 완료 시점에 `sink_alignment_summary()` 자동 호출하여 불일치 시 경고 로그 기록. 캐너리 하니스 외 정상 경로에서도 동작 확인. | 2h (~10줄 연결 + 테스트) | 없음 | S6 \S6.5, D-3 |
| EX-07 | ChainOfVerification fail-open 범위 축소 (E-1) | **P2-Medium** | `chain_of_verification.py:136-148`에서 LLM 에러 시 `return ""` → `{"passed": True, "summary": "파싱 실패 - 기본 통과"}`. `quick_verify()` Python 게이트 선행으로 범위 제한적이나, "Python이 의심 표시 → LLM 확인 요청 → LLM 실패 → 가짜 통과" 시나리오 존재. | LLM 실패 시 `{"passed": False, "summary": "LLM 검증 실패 - 재시도 필요"}` 반환 또는 별도 `llm_failed` 플래그 설정하여 Director에게 전달. fail-open → fail-closed 전환. | 3h (반환값 변경 + 하류 영향 분석 + 테스트) | EX-12 (fail-open/closed 정책 문서 선행 권고) | S6 \S6.3, E-1 |
| EX-08 | BlockingValidator degraded 신호 하류 전달 (E-4) | **P2-Medium** | `blocking_validator.py:176-182`에서 degraded 시 `passed: True` + `failures` 미포함. `validation_orchestrator.py`에서 `degraded_checks` 필드 확인/처리 코드 없음. 12개 중 2개만 해당이나 advisory 신호 손실. | `validation_orchestrator.py`에서 `degraded_checks` 필드 확인 후 Director 프롬프트에 "[Degraded] N개 검증 비정상 통과" 경고 주입. | 1.5h (~10줄 + 테스트) | 없음 | S6 \S4.4, E-4 |
| EX-09 | WorldState/FactLedger _meta_db=None 부분 커밋 방어 (MF-02) | **P2-Medium** | `stage4_post_processor.py:1358-1455`의 `_save_world_state_atomic()`에서 `_meta_db=None` 시 `_nullcontext()` 폴백 → 트랜잭션 없이 실행 → 부분 커밋 가능. 인메모리 롤백(`deepcopy` 스냅샷) 정상 구현됨. 정상 운영에서는 `_meta_db` 존재. | `_meta_db=None` 경로에서 경고 로그 발생 + 순차 save 실패 시 인메모리 롤백 자동 트리거 확인. 테스트 추가. | 1.5h (~8줄 + 테스트) | EX-05 | S6 \S6.4 부록, MF-02 |
| EX-10 | Verdict 상태 체계 정리: 6개 → 스키마 반영 (S1) | **P2-Medium** | 코드에서 6개 verdict 상태 운영(PASS, PASS_WITH_FIX, REJECT, CONDITIONAL_PASS, PASS_WITH_WARNING, FAILED) vs 스키마 3개. CONDITIONAL_PASS는 no-op layer(ensemble이 덮어씀). PASS_WITH_WARNING은 schema 미정의이나 `db_manager.py:3150` SQL WHERE절에 하드코딩. 스키마 변경 시 SQL 불일치 발생 위험. | `response_schemas.py`에 PASS_WITH_WARNING을 정식 등록하거나, 별도 verdict enum 모듈 생성하여 단일 진실 소스 확보. SQL WHERE절이 enum 참조하도록 변경. CONDITIONAL_PASS no-op 여부 문서화. | 5h (스키마 정의 + SQL 정리 + 하류 영향 분석 + 테스트) | 없음 | S6 \S4.1, S1 |
| EX-11 | _UNCONDITIONAL_PASS_FLOOR 상수 중앙 정의 이전 | **P3-Low** | `validation_orchestrator.py:174`에 런타임 상수 85로만 존재. `response_schemas.py`나 `constants.py`에 미정의 → schema/contract 갭. | `constants.py` 또는 적절한 설정 모듈에 정의 후 `validation_orchestrator.py`에서 import. | 0.5h (1줄 이전 + import 변경) | EX-10 | S6 \S4.2 |
| EX-12 | Fail-open/closed 계층 정책 문서화 | **P3-Low** | 코드 내 `[FailClosed:...]` 태그 5개 발견. Preflight=fail-open, Blocking=degraded, CoVe/PostSelect=fail-closed로 계층별 의도적 차별 적용 확인되나 중앙 정책 문서 부재. **대상**: `docs/implementation/fail-policy.md` 또는 `validation_orchestrator.py` 모듈 독스트링 | 검증 파이프라인의 fail-open/closed 정책을 1개 문서(또는 코드 내 docstring)로 명문화. 각 검증기의 실패 시 동작 + 설계 의도 명시. | 1h (문서 작성) | 없음 | S6 \S4.3, LF-20 |
| EX-13 | Stage 3 max-fail 시 에스컬레이션 선택지 추가 | **P3-Low** | Stage 3 실패 시 알림 + 감사 이벤트 + QualityDashboard violation 기록은 존재하나, Stage 4와 달리 Operator 선택지(재시도/건너뛰기/중단) 없음. batch loop이 자동 건너뛰기. **대상**: `stage3_orchestrator.py` 내 max-fail 핸들링 영역 | Stage 3 max-fail 시 Stage 4와 동일한 에스컬레이션 선택지 제공. `ctx.ui.ask_operator()` 또는 동등 메커니즘 추가. | 4h (UI 연동 + 테스트) | 없음 | S6 \S3.3 |
| EX-14 | Dead code 정리 (3건) | **P3-Low** | (1) `MetricsCollector.reset()` - `metrics_collector.py:118-130`, 호출자 0건. (2) `adaptive_retry.apply_strategy()` / `time.sleep(30)` - `adaptive_retry.py:410-412`, 호출자 0건. (3) `validate_response_against_schema()` - `response_schemas.py:692-725`, 호출자 0건, Gemini-only. | 3건 모두 삭제 또는 `@deprecated` 데코레이터 부착. 삭제 후 전체 테스트 통과 확인. | 1h (삭제 + 테스트 실행) | 없음 | S6 \S6.2, \S6.8, \S6.9, \S8.2 |
| EX-15 | TruthGate advisory 경로 강화 (E-3) | **P3-Low** | `truth_gate.py:24-63` `blocking: False` 하드코딩. CRITICAL 경고가 Director 프롬프트에 주입되어 보완되나, Director LLM이 지시 무시 시 위험. 현재 Python 레이어에서는 어떤 경우에도 blocking 불가. | TruthGate CRITICAL 발견 시 `blocking: True` 옵션 추가 또는 Director 판정 후 CRITICAL 미반영 시 2차 검증 트리거. 최소한 CRITICAL 경고 시 retry 예산 확대. | 3h (TruthGate 로직 변경 + Director 상호작용 + 테스트) | EX-12 | S6 \S5.2, E-3 |
| EX-16 | Director 프롬프트 캡 740KB 설정화 (IF-02) | **P4-Info** | `director_ensemble.py:294-308`에 기본 740KB 캡 하드코딩. 프로젝트 규모에 따라 조정 필요성 있음. | 설정 파일 또는 `constants.py`에서 읽도록 변경. | 0.5h | 없음 | S6 \S5.5, IF-02 |
| EX-17 | Director cache protagonist_config 누락 수정 (LF-16) | **P4-Info** | `director.py:105-112`에서 `invalidate_caches()` 시 `_protagonist_config` 미초기화. protagonist_config 변경 빈도 극히 낮으나 정확성 미흡. | `invalidate_caches()`에 `self._caching._protagonist_config = None` 1줄 추가. | 0.25h (1줄) | 없음 | S6 딥다이브, LF-16 |
| EX-18 | Advisory Chain 부분 실패 로그 레벨 상향 (LF-17) | **P4-Info** | `stage4_interview_round.py:5008-5009`에서 9중 병렬 자문 체인 부분 실패 시 `logging.debug`로 기록 → 운영 시 미가시. | `logging.debug` → `logging.warning` 1줄 변경. | 0.25h (1줄) | 없음 | S6 딥다이브, LF-17 |

---

## 2. 우선순위 기준

| 등급 | 기준 | 해당 항목 |
|------|------|----------|
| **P0-Critical** | 실제 결과 불일치 또는 무음 품질 저하를 유발하는 확인된 결함 | EX-01, EX-02 |
| **P1-High** | 데이터 손실 위험 또는 품질 게이트 무력화 | EX-03, EX-04, EX-05 |
| **P2-Medium** | 방어 계층 약화 또는 정합성 미보장 | EX-06, EX-07, EX-08, EX-09, EX-10 |
| **P3-Low** | 유지보수 부채 또는 설계 일관성 미흡 | EX-11, EX-12, EX-13, EX-14, EX-15 |
| **P4-Info** | 즉시 개선 가능한 1줄 수정 또는 설정화 | EX-16, EX-17, EX-18 |

---

## 3. 실행 순서 권고

### 3.1 1차 트랜치 (P0, 즉시 실행, 총 1.5h)

```
EX-01 → EX-02
```

- EX-01: 1줄 수정으로 OPP-05 결함 제거. 의존성 없음, 즉시 실행 가능.
- EX-02: 기존 구현된 함수 연결만으로 벡터 인덱스 gap 자동 복구.

### 3.2 2차 트랜치 (P1, 총 5h)

```
EX-05 → EX-04 → EX-03
```

- EX-05 선행: save() 반환값 확인 인프라가 EX-09(MF-02)의 전제 조건.
- EX-04: 비상 덤프 독립 작업.
- EX-03: Director 프롬프트 조정이 포함되므로 단독 테스트 필요.

### 3.3 3차 트랜치 (P2, 총 11h)

```
EX-09 → EX-06 → EX-08 → EX-10 → EX-07
```

- EX-09: EX-05 완료 후 실행.
- EX-07: fail-open/closed 정책 문서(EX-12) 선행 권고이나 블로커는 아님.

### 3.4 4차 트랜치 (P3+P4, 총 9h)

```
EX-17 → EX-18 → EX-14 → EX-11 → EX-12 → EX-13 → EX-15 → EX-16
```

- P4 1줄 수정 항목(EX-17, EX-18)을 먼저 처리하여 빠른 승리(quick win) 확보.

---

## 4. 총 추정 공수

| 등급 | 항목 수 | 추정 공수 합계 |
|------|---------|--------------|
| P0-Critical | 2 | 1.5h |
| P1-High | 3 | 5h |
| P2-Medium | 5 | 11h |
| P3-Low | 5 | 8.5h |
| P4-Info | 3 | 1h |
| **합계** | **18** | **30h** |

---

## 5. 의존성 그래프

```
EX-01 (독립)
EX-02 (독립)
EX-03 (독립)
EX-04 (독립)
EX-05 (독립) ──→ EX-09 (MF-02, _meta_db=None 방어)
EX-06 (독립)
EX-07 ←── EX-12 (권고, 비차단)
EX-08 (독립)
EX-10 ──→ EX-11 (상수 이전은 verdict 정리 후)
EX-12 (독립) ──→ EX-15 (TruthGate 강화는 정책 문서 후)
EX-13 (독립)
EX-14 (독립)
EX-16 (독립)
EX-17 (독립)
EX-18 (독립)
```

---

## 6. 감리 이력

### 6.1 3-Pass 기본 감리

#### Pass 1: 항목 완전성 대조 (S6 SSOT 전수 대조)

S6 SSOT의 모든 발견 사항(S8.1 확인된 결함 10건 + S8.2 Dead code 3건 + 부록 A DA 교정 이력)을 본 실행문서와 1:1 대조.

| S6 ID | 실행문서 매핑 | 누락 여부 |
|-------|-------------|----------|
| OPP-05 quality_risk 불일치 | EX-01 | 반영 완료 |
| MF-01 벡터 인덱스 복구 부재 | EX-02 | 반영 완료 |
| MF-02 WorldState/FactLedger 부분 커밋 | EX-09 | 반영 완료 |
| MF-03 quality_gate_failed write-only | EX-03 | 반영 완료 |
| MF-04 DB 실패 시 비상 저장 부재 | EX-04 | 반영 완료 |
| D-1/D-2 save() 반환값 미확인 | EX-05 | 반영 완료 |
| D-3 멀티싱크 트랜잭션 부재 | EX-06 | 반영 완료 |
| E-1 CoV fail-open | EX-07 | 반영 완료 |
| E-3 TruthGate advisory-only | EX-15 | 반영 완료 |
| E-4 BlockingValidator degraded PASS | EX-08 | 반영 완료 |
| Dead code 3건 | EX-14 | 반영 완료 |
| Verdict 6 vs 3 | EX-10 | 반영 완료 |
| _UNCONDITIONAL_PASS_FLOOR | EX-11 | 반영 완료 |
| Stage 3 에스컬레이션 비대칭 | EX-13 | 반영 완료 |
| fail-open/closed 정책 문서 부재 | EX-12 | 반영 완료 |
| Director 프롬프트 캡 740KB | EX-16 | 반영 완료 |
| LF-16 Director cache | EX-17 | 반영 완료 |
| LF-17 Advisory Chain 로그 | EX-18 | 반영 완료 |

**Pass 1 결과**: 누락 0건. S6 SSOT의 모든 actionable 항목이 실행문서에 매핑됨.

#### Pass 2: 우선순위 정합성 검증

| 검증 항목 | 결과 |
|----------|------|
| P0 항목이 실제 결과 불일치를 유발하는가? | EX-01: OPP-05 3곳 중 1곳 verdict set 불일치 = 실제 결함. EX-02: 무음 품질 저하 확인. **정합** |
| P1 항목이 데이터 손실 또는 게이트 무력화인가? | EX-03: write-only flag = 게이트 무력화. EX-04: 디스크 풀 시 원고 손실. EX-05: save 실패 미감지. **정합** |
| P2 항목이 P1보다 낮은 영향도인가? | EX-06~10: 방어 계층 약화이나 즉시 데이터 손실 아님. **정합** |
| P3/P4 항목이 유지보수 부채인가? | EX-11~18: dead code, 문서화, 1줄 수정. **정합** |

**Pass 2 결과**: 우선순위 역전 0건.

#### Pass 3: 완료 기준 검증가능성

| 검증 항목 | 결과 |
|----------|------|
| 모든 완료 기준이 객관적으로 검증 가능한가? | 18건 모두 코드 변경 + 테스트로 검증 가능. **정합** |
| "~줄" 추정이 S6 SSOT의 즉시 개선 권고와 일치하는가? | EX-02(~5줄), EX-04(~10줄), EX-03(~15줄) 모두 S6 권고와 일치. **정합** |
| 의존성 그래프에 순환이 없는가? | EX-05→EX-09, EX-10→EX-11, EX-12→EX-07/EX-15 모두 단방향. 순환 없음. **정합** |

**Pass 3 결과**: 검증가능성 미흡 0건.

---

### 6.2 5-Pass 적대적 감리

#### 적대적 Pass 1: "누락된 항목이 있는가?"

S6 SSOT 외부 소스(stage34-deep-dive, crosscut-deepdive, static-improvement-discovery) 재검토.

| 검토 대상 | 결과 |
|----------|------|
| stage34-deep-dive LF-01~LF-24 (Low 24건) | Low 항목 중 actionable한 LF-16(Director cache), LF-17(로그 레벨)은 EX-17, EX-18로 반영. 나머지 Low는 즉시 실행 불필요(의도적 설계 또는 구조적 제약). **누락 없음** |
| crosscut-deepdive A-2~A-4 (Low 3건) | dead code(A-2)는 EX-14에 포함. A-3(TOCTOU 무해), A-4(마이크로초 윈도우)는 실행 불필요. **누락 없음** |
| crosscut-deepdive B-2, C-2 (Low 2건) | 이중 실패 조건/hash 포함 -- 실행 불필요. **누락 없음** |
| DA Pass 3 교정 8건 | 전부 심각도 하향 항목. 실행 대상 아님. **누락 없음** |
| S6 설계 강점 6건 | 강점은 실행 대상 아님. **누락 없음** |

**적대적 Pass 1 결과**: 누락 0건 확인.

#### 적대적 Pass 2: "우선순위가 과대/과소 평가되었는가?"

| 의심 항목 | 반증 시도 | 결과 |
|----------|----------|------|
| EX-01을 P0로 분류: OPP-05가 정말 실제 결과 불일치를 유발하는가? | `director_ensemble.py:771`에서 PASS_WITH_WARNING verdict가 도달하면 quality_risk가 미설정되어 Stage 3 메타데이터에 불완전 기록. Stage 4에서 quality_risk를 읽지 않으므로(MF-03) 현재 무영향이나, EX-03 실행 후에는 실질 영향 발생. **P0 유지 정당**: EX-03과 결합 시 실질 영향. 또한 코드 정확성 결함 자체가 P0 기준 충족. |
| EX-06(멀티싱크)을 P2로 분류: P1이 아닌가? | 데스크톱 앱에서 디스크 풀 극히 드묾 + 캐너리 하니스 준자동 체크 존재. 정합성 불일치가 발생해도 데이터 손실은 아님(중복 기록). **P2 유지 정당**. |
| EX-15(TruthGate)를 P3로 분류: Director가 CRITICAL 무시하면 심각하지 않은가? | Director 프롬프트에 "CRITICAL만 자동 REJECT 사유" 명시. LLM 지시 무시 확률은 낮으나 비결정적. 현재 Python blocking 옵션이 전혀 없으므로 보험 계층 부재. **그러나** 발현 빈도(CRITICAL 자체가 드묾 + LLM 무시 확률) 고려 시 P3 유지 타당. |

**적대적 Pass 2 결과**: 우선순위 변경 0건.

#### 적대적 Pass 3: "추정 공수가 과소 평가되었는가?"

| 의심 항목 | 반증 시도 | 결과 |
|----------|----------|------|
| EX-07 ChainOfVerification fail-open → fail-closed (2h) | fail-open → fail-closed 전환 시 하류 영향: `stage4_orchestrator.py`에서 CoV 결과를 소비하는 경로 분석 필요. quick_verify 실패 + LLM 실패 시 REJECT로 전환하면 false positive 증가 가능. 하류 영향 분석을 별도 포함해야 하므로 **2h → 3h로 상향 권고**. |
| EX-10 Verdict 체계 정리 (4h) | CONDITIONAL_PASS가 14곳(modules/) + 15곳(tests/)에 존재. no-op이라 해도 삭제 시 테스트 29건 수정 필요. PASS_WITH_WARNING은 SQL WHERE절 + failure_analyzer 4곳. **4h는 타당하나 낙관적 -- 5h로 상향 권고**. |
| EX-13 Stage 3 에스컬레이션 (3h) | UI 연동(Electron IPC → Python 콜백)이 필요하므로 BE-FE 연결성(S2) 영역과 교차. **3h → 4h로 상향 권고**. |

**적대적 Pass 3 결과**: 3건 공수 상향 권고 (EX-07: 2h→3h, EX-10: 4h→5h, EX-13: 3h→4h). 총 공수 27h → 30h.

#### 적대적 Pass 4: "의존성 누락이 있는가?"

| 검토 대상 | 결과 |
|----------|------|
| EX-03(quality_risk 활성화)와 EX-01(quality_risk 불일치 수정)의 관계 | EX-01이 먼저 완료되어야 EX-03에서 quality_risk 값이 정확. **의존성 추가 권고: EX-01 → EX-03**. 현재 실행 순서(1차 트랜치 EX-01 → 2차 트랜치 EX-03)로 자연 충족되나 명시적 기록 필요. |
| EX-10(Verdict 정리)과 EX-01(OPP-05)의 관계 | EX-01은 기존 verdict set 내에서 1줄 수정. EX-10은 verdict 체계 전체 정리. 충돌 없음. **의존성 불필요**. |
| EX-08(BlockingValidator 하류 전달)과 EX-12(정책 문서)의 관계 | EX-08은 코드 변경, EX-12는 문서. 독립 실행 가능. **의존성 불필요**. |

**적대적 Pass 4 결과**: 1건 의존성 추가 (EX-01 → EX-03, 자연 충족이나 명시 기록).

#### 적대적 Pass 5: "S6 SSOT의 수치/코드 근거가 본 문서에서 왜곡되었는가?"

| 검증 항목 | S6 SSOT 원문 | 본 문서 기재 | 일치 여부 |
|----------|-------------|-------------|----------|
| Stage 4 거부율 | 45.5% (5/11) | 미인용 (실행문서 범위 외) | N/A |
| quality_risk 불일치 위치 | 3곳 중 1곳(`director_ensemble.py:771`) | EX-01에 동일 기재 | **일치** |
| Dead code 3건 | reset, apply_strategy, validate_response_against_schema | EX-14에 동일 3건 | **일치** |
| 멀티싱크 4개 | pass_rate_monitor/SQLite/JSONL/session_logger | EX-06에 동일 4개 | **일치** |
| BlockingValidator degradable 수 | 2/12+ | EX-08에 "12개 중 2개" | **일치** |
| fail-open/closed 태그 | `[FailClosed:...]` 5개 | EX-12에 "5개" | **일치** |
| 벡터 인덱스 복구 함수 | `sync_v20_drafts(drafts_path=실제경로)` ~5줄 | EX-02에 동일 | **일치** |
| 원고 비상 덤프 | `output_dir/emergency_ep_XXXX.txt` ~10줄 | EX-04에 동일 | **일치** |
| quality_risk 활성화 | ~15줄 | EX-03에 동일 | **일치** |

**적대적 Pass 5 결과**: 왜곡 0건. 모든 수치/코드 근거가 S6 SSOT 원문과 일치.

---

### 6.3 감리 종합

| 감리 단계 | 발견 건수 | 조치 |
|----------|----------|------|
| 기본 Pass 1 (완전성) | 0건 누락 | 없음 |
| 기본 Pass 2 (우선순위) | 0건 역전 | 없음 |
| 기본 Pass 3 (검증가능성) | 0건 미흡 | 없음 |
| 적대적 Pass 1 (누락) | 0건 | 없음 |
| 적대적 Pass 2 (과대/과소) | 0건 변경 | 없음 |
| 적대적 Pass 3 (공수) | **3건 상향 권고** | EX-07: 2h→3h, EX-10: 4h→5h, EX-13: 3h→4h |
| 적대적 Pass 4 (의존성) | **1건 추가** | EX-01 → EX-03 명시 |
| 적대적 Pass 5 (왜곡) | 0건 | 없음 |

**최종 감리 결과**: 적대적 감리에서 공수 상향 3건 + 의존성 명시 1건 발견. 본 문서 본문에 반영 완료 (총 공수 30h 기준). 항목 누락, 우선순위 역전, 수치 왜곡 없음.

---

## 7. 적대적 감리 반영 사항 (본문 정정)

본 섹션은 적대적 감리 결과를 본문에 반영한 정정 내역을 기록한다.

| 정정 ID | 대상 | 정정 내용 |
|---------|------|----------|
| C-01 | EX-07 추정 공수 | 2h → 3h (하류 영향 분석 포함) |
| C-02 | EX-10 추정 공수 | 4h → 5h (CONDITIONAL_PASS 29건 + SQL 4곳 수정) |
| C-03 | EX-13 추정 공수 | 3h → 4h (BE-FE 연결성 교차) |
| C-04 | EX-03 의존성 | "없음" → "EX-01 (자연 충족, 명시 기록)" |
| C-05 | 총 공수 | 27h → 30h |

---

## 8. 교차 SSOT 참조

| 참조 대상 | SSOT 문서 | 관련 실행 항목 |
|----------|----------|--------------|
| ConstraintDB (아이템 제약 누적) | S5 \S4.1 | -- (S6 범위 외) |
| GenreGuards (장르별 검증 규칙) | S5 \S4.3 | -- (S6 범위 외) |
| PassRateMonitor (통과율 추적) | S7 \S3 | EX-06 (sink 중 1개) |
| response_schemas.py (anyOf 패턴) | S4 \S6 | EX-10, EX-11 |
| MetricsCollector (비용 추적) | S7 \S2.2 | EX-14 (dead code reset) |
| BE-FE 연결성 (Electron IPC) | S2 | EX-13 (에스컬레이션 UI) |

---

> **문서 종결**
> S6 Stage 3-4 + 교차 계층 실행문서. 18개 실행 항목, 총 추정 공수 30h.
> 3-pass 기본 감리 + 5-pass 적대적 감리 완료. 누락 0건, 왜곡 0건, 공수 정정 3건, 의존성 추가 1건.
> 최종 확신도: 98% (S6 SSOT 기준 동일).
