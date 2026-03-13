# TF-XC: 크로스컷 디테일 딥다이브 6트랙 통합 SSOT

> **생성일**: 2026-03-13
> **감사 유형**: 문서화 전용 (코드 수정 금지)
> **방법론**: 3-Pass 감리 (수집 → 교차검증 → 오탐 제거)
> **범위**: 6트랙 · 21타겟 · 다수 스테이지 관통 크로스컷 관심사

---

## 1. 총괄 결과

> 실행 기준 메모: 아래 `84건`은 **트랙 raw count**다. 교차 중복(XC-ADV-001 ↔ XC-MEM-T1-003 등)을 포함하므로 실제 실행 순서는 dedupe된 remediation unit 기준으로 잡아야 한다.

| 트랙 | 타겟 수 | P0 | P1 | P2 | P3 | 합계 | 산출물 수 |
|------|--------|----|----|----|----|------|----------|
| XC-LLM (LLM 추상화) | 3 | 0 | 0 | 2 | 10 | 12 | 6 |
| XC-DB (DB 트랜잭션) | 4 | 0 | 0 | 5 | 8 | 13 | 7 |
| XC-ADV (병렬 Advisory) | 4 | 0 | 1 | 7 | 8 | 16 | 7 |
| XC-ERR (에러 전파) | 3 | 0 | 2 | 7 | 14 | 23 | 6 |
| XC-MEM (메모리 안전) | 4 | 0 | 0 | 4 | 3 | 7 | 7 |
| XC-DI (Protocol 계약) | 3 | 0 | 0 | 2 | 11 | 13 | 6 |
| **합계** | **21** | **0** | **3** | **27** | **54** | **84** | **39** |

### 핵심 수치
- **P0 (데이터 손실)**: 0건 — 즉시 데이터 손실 경로 없음
- **P1 (무성 실패)**: 3건 — 운영 가시성/안전 즉시 개선 필요
- **P2 (품질 저하)**: 27건 — 멀티프로바이더 전환, 코드 일관성 개선 권장
- **P3 (코드 스멜)**: 54건 — 기술 부채, 장기 개선 대상

---

## 2. P1 Findings — 즉시 조치 권장 (3건)

### [XC-ADV-006] P1 | Advisory Executor Timeout 후 무기한 대기
| 필드 | 내용 |
|------|------|
| 트랙 | XC-ADV |
| 현상 요약 | `as_completed(timeout=300)` 만료 후 `ThreadPoolExecutor.__exit__`의 `shutdown(wait=True)`가 미완료 LLM API 호출을 무기한 대기 |
| 코드 근거 | `stage4_interview_round.py:3817-3832` |
| 영향 경계 | Stage 4 전체 — Advisory 체인 실행 시 시스템 행(hang) 가능 |
| 권장 조치 | `cancel_futures=True` 또는 명시적 `future.cancel()` 추가 |
| 공수 | 0.5h |

### [XC-ERR-012] P1 | Stage 2 → Stage 4 에러 디테일 미전달
| 필드 | 내용 |
|------|------|
| 트랙 | XC-ERR |
| 현상 요약 | Stage 2 validation 에러 디테일이 Stage 4 context builder에 전달되지 않음 (`stage_attempts` 참조 0건) |
| 코드 근거 | `stage4_context_builder.py` — `stage_attempts` 참조 0건 |
| 영향 경계 | Stage 4 Director가 Stage 2 실패 컨텍스트 없이 판단 |
| 권장 조치 | Stage 2 validation 에러를 Stage 4 context에 전달하는 경로 추가 |
| 공수 | 2h |

### [XC-ERR-016] P1 | _safe_commit() 실패 시 유령 트랜잭션
| 필드 | 내용 |
|------|------|
| 트랙 | XC-ERR |
| 현상 요약 | `project_service.py`의 `_safe_commit()` False 반환 시 `_rollback_open_transaction()` 미호출로 미커밋 트랜잭션 잔류 |
| 코드 근거 | `project_service.py` — `_safe_commit()` 실패 경로 |
| 영향 경계 | DB 일관성 — 후속 트랜잭션이 불완전 상태 위에 쌓일 수 있음 |
| 권장 조치 | `_safe_commit()` 실패 시 명시적 rollback 호출 추가 |
| 공수 | 0.5h |

---

## 3. P2 Findings — 개선 권장 (27건)

### Track: XC-LLM (2건)

| ID | 제목 | 코드 근거 | 공수 |
|----|------|----------|------|
| XC-LLM-005 | `generate_content_via_router()` raw 응답이 Gemini 전용 `.text` 속성에 의존 | `llm_generate.py` + 호출자 15곳+ | 4h |
| XC-LLM-008 | `BaseAgent._generate_content()` 반환값이 Gemini native 객체, 멀티프로바이더 시 AttributeError | `base_agent.py` + 에이전트 12종 | 4h |

### Track: XC-DB (5건)

| ID | 제목 | 코드 근거 | 공수 |
|----|------|----------|------|
| XC-DB-T1 | 공유 커서(self.cursor) vs 로컬 커서 혼용 — deprecated 선언 후 미전환 | `db_manager.py:63`, `project_service.py` 18곳 | 5-6h |
| XC-DB-T2 | JSON 방어적 로드 비일관 — 일부 write 경로에서 `_safe_json_loads` 미사용 | `db_manager.py:79-84` | 2h |
| XC-DB-T3 | lock 외부 커서 접근 | `db_manager.py` | 1h |
| XC-DB-T4a | 외부 저장소(파일) 정합성 — DB 트랜잭션 원자성 외부 | 파일 쓰기 경로 | 2h |
| XC-DB-T4b | FTS 삭제 무시 | FTS 관련 코드 | 1h |

### Track: XC-ADV (7건)

| ID | 제목 | 코드 근거 | 공수 |
|----|------|----------|------|
| XC-ADV-001 | `validation_results` 병렬 `setdefault()` — CPython GIL 의존적 | `stage4_interview_round.py:3842-3859` | 1h |
| XC-ADV-005 | 6개 LLM advisory 동시 콜백 호출 — Context Caching 경쟁 | `_truth_gate_llm_ask` 콜백 | 2h |
| XC-ADV-007 | `as_completed` TimeoutError 미포착 — 부분 결과 유실 | `stage4_interview_round.py` | 0.5h |
| XC-ADV-009 | advisory `future.result()` 실패가 `logging.debug`로만 기록 | `stage4_interview_round.py` | 0.3h |
| XC-ADV-011 | 동일 티어 advisory 간 중복 경고 미억제 | 억제 로직 | 1h |
| XC-ADV-014 | 억제된 advisory 존재 사실이 Director에 미전달 | MC 주입 경로 | 0.5h |
| XC-ADV-018 | TruthGate 경고 10건 상한으로 CRITICAL 경고 truncation 가능 | `truth_gate.py` | 0.5h |

### Track: XC-ERR (7건)

| ID | 제목 | 코드 근거 | 공수 |
|----|------|----------|------|
| XC-ERR-019 | EmotionTracker/StateDeltaTracker rollback_to() 예외 미보호 (비대칭) | `project_service.py:84-92` | 0.5h |
| XC-ERR-001 | Stage3 오케스트레이터 telemetry setattr에서 `except Exception: pass` | `stage3_orchestrator.py` | 0.3h |
| XC-ERR-002 | Stage4 오케스트레이터 telemetry setattr에서 `except Exception: pass` | `stage4_orchestrator.py` | 0.3h |
| 기타 4건 | 다양한 exception 삼킴 패턴 | modules/ 전체 | 2h |

### Track: XC-MEM (4건)

| ID | 제목 | 코드 근거 | 공수 |
|----|------|----------|------|
| XC-MEM-T2-001 | 롤백/리셋/와이프 시 `BaseAgent._context_caches.clear()` 미호출 | `base_agent.py`, `project_service.py` | 0.5h |
| XC-MEM-T4-001 | 사망 NPC regex에 lookahead `(?![가-힣])` 부재 — 유사 이름 false positive | `truth_gate.py` | 1h |
| XC-MEM-T3-001 | world_state/fact_ledger 독립 롤백 시 부분 실패로 인메모리 상태 분기 | `project_service.py` | 1h |
| XC-MEM-T1-003 | advisory 병렬 실행 시 `validation_results` 공유 쓰기 — GIL 의존적 | `stage4_interview_round.py` | 2h |

### Track: XC-DI (2건)

| ID | 제목 | 코드 근거 | 공수 |
|----|------|----------|------|
| XC-DI-005 | Stage3 오케스트레이터가 `self.app`에 직접 속성 할당 — DI 컨텍스트 우회 | `stage3_orchestrator.py` | 2h |
| XC-DI-013 | Stage3 `from_app()`만 `getattr()` 사용 — Stage2/4는 `_safe_getattr()` (패턴 불일치) | `stage3_context.py` | 1h |

---

## 4. P3 Findings — 기술 부채 (54건)

> 상세는 각 트랙별 `consolidated-findings-3pass-reaudit.md` 참조

| 트랙 | P3 건수 | 주요 패턴 |
|------|--------|----------|
| XC-LLM | 10 | 모델 설정 이중 경로, import-time 캐시, YAML I/O 매 호출 |
| XC-DB | 8 | WAL 체크포인트, nested transaction 경고, 커서 패턴 |
| XC-ADV | 8 | advisory 결과 타입 분산, 라운드간 누출 방어, 로깅 레벨 |
| XC-ERR | 14 | 957개 `except Exception` 패턴 (대부분 합리적), soft_failure 갭 |
| XC-MEM | 3 | TruthGate 방어적 복사 불필요 확인, 캐시 키 충돌 이론적 |
| XC-DI | 11 | 콜백 None 가드 불일치, Orphan 슬롯 2개, Protocol isinstance 0건 |

---

## 5. 크로스 트랙 교차 분석

### 5.1 트랙간 중복 Finding

| Finding A | Finding B | 관계 |
|-----------|-----------|------|
| XC-ADV-001 (병렬 공유 쓰기) | XC-MEM-T1-003 (validation_results 공유) | **동일 근본 원인** — advisory 병렬 실행 시 공유 dict 쓰기 |
| XC-ADV-005 (콜백 경쟁) | XC-MEM-T2-001 (캐시 무효화) | **관련** — 병렬 LLM 호출의 캐시 안전성 |
| XC-ERR-019 (롤백 비대칭) | XC-MEM-T3-001 (상태 분기) | **관련** — 롤백 실패 시 인메모리 상태 불일치 |
| XC-DB-T1 (공유 커서) | XC-ADV (8스레드 DB 접근) | **관련** — 멀티스레드 DB 접근 안전 |

### 5.2 기존 262+ Finding과의 중복

- XC-DB 트랙에서 기존 finding과 6건 중복 확인 → 순수 신규 11건
- 나머지 트랙은 크로스컷 관점이므로 대부분 기존 단일 모듈 감사에서 미발견

### 5.3 시스템 전반 평가

| 관심사 | 평가 |
|--------|------|
| **스레드 안전** | CPython GIL 의존적으로 현재 안전. 멀티프로세스 전환 시 재검토 필요 |
| **DB 트랜잭션** | RLock + WAL + nested transaction 인지로 양호. 공유 커서 전환이 주요 기술 부채 |
| **에러 전파** | bare except 0건 (전량 제거 완료). `except Exception` 957건 중 대부분 합리적 |
| **메모리 안전** | TruthGate 읽기 전용 확인. 캐시 무효화 훅 부재가 유일한 갭 |
| **DI 계약** | 3개 스테이지 DI 전환 완료. Stage3 `self.app` 직접 할당이 잔여 레거시 |
| **LLM 추상화** | Gemini-only 운영에서 안전. 멀티프로바이더 전환이 P2 2건의 트리거 |

---

## 6. 권장 우선순위 로드맵

### Tier 1: 즉시 (P1 3건, 총 3h)
1. **XC-ADV-006**: `cancel_futures=True` 추가 → 0.5h
2. **XC-ERR-016**: `_safe_commit()` 실패 시 명시적 rollback → 0.5h
3. **XC-ERR-012**: Stage 2 → Stage 4 에러 디테일 전달 경로 → 2h

### Tier 2: 단기 (P2 핵심 10건, 총 ~12h)
1. **XC-MEM-T2-001**: 롤백 시 캐시 무효화 훅 → 0.5h
2. **XC-ADV-007/009**: Timeout 예외 포착 + 로깅 레벨 상향 → 0.8h
3. **XC-MEM-T4-001**: 사망 NPC regex lookahead 추가 → 1h
4. **XC-MEM-T3-001 + XC-ERR-019**: 롤백 원자성 + 비대칭 해소 → 1.5h
5. **XC-ADV-001 + XC-MEM-T1-003**: validation_results 스레드 안전 → 2h (중복 — 1건 해결)
6. **XC-DI-005**: Stage3 `self.app` 직접 할당 제거 → 2h
7. **XC-ADV-018**: TruthGate 경고 상한 CRITICAL 보호 → 0.5h

### Tier 3: 중기 (멀티프로바이더 전환 시, ~8h)
1. **XC-LLM-005/008**: raw 응답 추상화 계층 도입 → 8h

### Tier 4: 장기 (P3 기술 부채, ~30h+)
- 공유 커서 전량 전환: 5-6h
- Exception 패턴 정리: 5h+
- Protocol isinstance 검증: 2h
- Orphan 슬롯 정리: 1h
- 기타 P3 항목: 16h+

---

## 7. 산출물 인덱스 (39개 파일)

### XC-LLM (6개)
- `XC-LLM-detail-full-survey-audit-order.md`
- `XC-LLM-T1-shared-router-singleton-thread-safety-findings.md`
- `XC-LLM-T2-provider-response-type-dispersion-findings.md`
- `XC-LLM-T3-model-config-runtime-immutability-findings.md`
- `XC-LLM-consolidated-findings.md`
- `XC-LLM-consolidated-findings-3pass-reaudit.md`

### XC-DB (7개)
- `XC-DB-detail-full-survey-audit-order.md`
- `XC-DB-T1-legacy-cursor-local-cursor-conflict-findings.md`
- `XC-DB-T2-json-column-corruption-resilience-findings.md`
- `XC-DB-T3-transaction-boundary-partial-rollback-findings.md`
- `XC-DB-T4-wal-check-same-thread-interaction-findings.md`
- `XC-DB-consolidated-findings.md`
- `XC-DB-consolidated-findings-3pass-reaudit.md`

### XC-ADV (7개)
- `XC-ADV-detail-full-survey-audit-order.md`
- `XC-ADV-T1-parallel-shared-state-mutation-findings.md`
- `XC-ADV-T2-timeout-cascade-exception-swallow-findings.md`
- `XC-ADV-T3-advisory-conflict-suppression-findings.md`
- `XC-ADV-T4-advisory-director-mc-injection-findings.md`
- `XC-ADV-consolidated-findings.md`
- `XC-ADV-consolidated-findings-3pass-reaudit.md`

### XC-ERR (6개)
- `XC-ERR-detail-full-survey-audit-order.md`
- `XC-ERR-T1-silent-exception-swallow-findings.md`
- `XC-ERR-T2-error-category-cross-stage-compression-findings.md`
- `XC-ERR-T3-rollback-handler-compensation-gap-findings.md`
- `XC-ERR-consolidated-findings.md`
- `XC-ERR-consolidated-findings-3pass-reaudit.md`

### XC-MEM (7개)
- `XC-MEM-detail-full-survey-audit-order.md`
- `XC-MEM-T1-truthgate-defensive-copy-gap-findings.md`
- `XC-MEM-T2-context-caching-invalidation-cross-stage-findings.md`
- `XC-MEM-T3-rollback-state-snapshot-divergence-findings.md`
- `XC-MEM-T4-deceased-npc-regex-edge-case-findings.md`
- `XC-MEM-consolidated-findings.md`
- `XC-MEM-consolidated-findings-3pass-reaudit.md`

### XC-DI (6개)
- `XC-DI-detail-full-survey-audit-order.md`
- `XC-DI-T1-context-slot-completeness-consumption-findings.md`
- `XC-DI-T2-closure-type-safety-di-callback-findings.md`
- `XC-DI-T3-protocol-registration-gap-findings.md`
- `XC-DI-consolidated-findings.md`
- `XC-DI-consolidated-findings-3pass-reaudit.md`

### 통합
- `XC-6track-merged-remediation-execution-ssot.md` ← **본 문서**

---

*TF-XC 크로스컷 전수조사 완료. 총 84건 (P0:0, P1:3, P2:27, P3:54). 즉시 조치 3건 공수 3h.*
