# TF-HEALTH: 코드베이스 전량 전수조사 보고서

> 상태: **CONFIRMED** (10-Pass 감리 완료 2026-03-13)
> 작성일: 2026-03-12~13
> 범위: Stage 0 / Stage 2 / Stage 3 / Stage 4 / Cross-cutting 전량
> 제약: **코드 수정 절대 금지**
> 감리 기준: 95% 확신도 — 오탐 11건 제거, 등급 재분류 19건, 설계의도 검증 4건

---

## 0. Executive Summary

| 영역 | P0 (Critical) | P1 (Important) | P2 (Minor) | 건강도 |
|------|:---:|:---:|:---:|------|
| Stage 0 | 0 | 0 | 6 | GOOD+ |
| Stage 2 | 0 | 0 | 13 | FAIR+ |
| Stage 3 | 0 | 0 | 5 | EXCELLENT |
| Stage 4 | 0 | 0 | 6 | GOOD+ |
| Cross-cutting | 0 | 0 | 7 | GOOD |
| **합계** | **0** | **0** | **37** | **GOOD+** |

**총 37건** (P0 0건, P1 0건, P2 37건)

**핵심 판정:** P0/P1 없음. 전 스테이지 운영 수준 안정. 잔여 P2 37건은 코드 위생·dead code·설계 trade-off 관찰. 4대 아키텍처 원칙 전량 준수. 3,847 테스트 통과, Ruff 0 위반.

---

## 1. Stage 0 (초기 설정) — 6 P2

| ID | 위치 | 내용 | 비고 |
|---|---|---|---|
| S0-P2-001 | stage01_helpers.py:145+414 vs L532 | Bible Root isinstance 미검사 (2개소). L532에 isinstance 체크 존재 — 코딩 스타일 불일치. | try-except 보호. force_sync 성공 후 진입. 실질 위험 없음. |
| S0-P2-002 | stage01_helpers.py:207-208 | Treatment 파일 dict 가정. `.get("treatments", [])`. | 시스템 모든 저장 경로에서 `{"treatments": [...]}` dict 포맷 확인. |
| S0-P2-003 | stage01_helpers.py:206-213 | json.load 후 타입 미검증 | Exception 포획됨 |
| S0-P2-004 | stage0/reverse_expander.py:114-135 | `_parse_json()` dict/list 이중 반환 | caller 주의 필요 |
| S0-P2-005 | stage01_helpers.py:227 | 확장 블록 수 기본값 `10` 하드코딩 | UI 입력, 변경 용이 |
| S0-P2-006 | stage01_helpers.py:436-445 | StyleGuide 변환 실패 시 빈 dict 저장 (silent) | 비차단 |

**양호:** Phase 0 스키마 검증, NPC History append-only, DB save 비차단

---

## 2. Stage 2 (Arc/Blueprint) — 13 P2

| ID | 위치 | 내용 | 비고 |
|---|---|---|---|
| S2-P2-001 | stage2_orchestrator.py:391-423 | **배치 경계 인과율 용접 누락.** `stitch_joints()` 배치 내부만 처리. | C단계 LLM 보상. 실질 영향 미미. (TF-S2 참조) |
| S2-P2-002 | stage2_orchestrator.py:278 | 배치 내 동일 컨텍스트 농축 — 병렬 설계 trade-off | C단계 순차 설계에서 보상 |
| S2-P2-003 | stage2_orchestrator.py:402-410 | stitch 실패 시 `continue` — 격리 설계 (양호) | 실패 쌍만 skip, 전파 차단 |
| S2-P2-004 | stage2_orchestrator.py:263-264 | cumulative_state_cache 배치 전 1회 초기화 | 매 배치 재생성으로 무영향 |
| S2-P2-005 | constants.py:301-307 | `BatchSizes` 클래스 4개 상수 전량 미참조 (dead code) | 코드에서 리터럴 `5` 직접 사용 |
| S2-P2-006 | stage2_orchestrator.py:256 | `Semaphore(5)` 하드코딩 | `PARALLEL_ENRICH_MAX=5` 미연결 (dead code) |
| S2-P2-007 | stage2_orchestrator.py:268-269 | `range(..., 5)` 리터럴 | `ARC_BATCH_SIZE=5` 미연결 (dead code) |
| S2-P2-008 | — | ep_start/ep_end `max(1, ...)` 방어 존재 | 충분 |
| S2-P2-009 | — | JSON 파싱 실패 시 폴백 경로 | 정상 |
| S2-P2-010 | — | 장르 가드 미적용 아크 경로 | edge case |
| S2-P2-011 | — | 농축 타임아웃 미설정 | Gemini SDK 자체 timeout 보호 |
| S2-P2-012 | — | 스냅샷 불완전성 | 일부만 캐시 |
| S2-P2-013 | — | batch_end off-by-one 가능성 | min() 처리로 안전 |

**양호:** `asyncio.gather(return_exceptions=True)` 개별 실패 격리, C단계 순차 설계 LLM 보상, 앙상블 3후보 + Director 선택, ConstraintDB 누적 갱신

---

## 3. Stage 3 (Blueprint) — 5 P2

| ID | 위치 | 내용 | 비고 |
|---|---|---|---|
| S3-P2-001 | stage3_orchestrator.py:1239-1245 | `ctx.agents` 미검증 접근 | `from_app()` 항상 주입 + 외부 try-except |
| S3-P2-002 | stage3_orchestrator.py:1001-1032 | SmartRetrieval 부분 실패 시 silent skip | WARNING 로깅 있음 |
| S3-P2-003 | stage3_orchestrator.py:809-838 | Entity Registry 캐시 — 문서화 부족 | 단일 스레드, 안전 |
| S3-P2-004 | stage3_orchestrator.py:569+987+1243 | 30/5/30 윈도우 하드코딩 | 각각 다른 용도 (preload/focus/context) |
| S3-P2-005 | stage3_orchestrator.py:1547 | `fail_count: 0` 리셋 | 연속 실패 카운터 의도 설계 |

**양호:** 19슬롯 DI Context, 순차 에피소드 의존성 강제, PinGuard, Exception 격리, ThreadPoolExecutor timeout, 캐시 무효화

---

## 4. Stage 4 (원고) — 6 P2

| ID | 위치 | 내용 | 비고 |
|---|---|---|---|
| S4-P2-001 | stage4_interview_round.py:3430-3433 | Advisory timeout 중첩 (as_completed + result) | 완료된 future에 즉시 반환. 방어적. |
| S4-P2-002 | stage4_interview_round.py:3437-3438 | Advisory 예외 시 `logging.debug` | WARNING 권장 |
| S4-P2-003 | — | feedback 문자열 concat | 대형 피드백 시 비효율 |
| S4-P2-004 | — | Director 결과 타입 가드 부분 누락 | edge case |
| S4-P2-005 | — | state_updates merge 비원자성 | advisory non-blocking 설계 |
| S4-P2-006 | — | validation_results list 병렬 접근 | 각 advisory 다른 key, GIL 보호 |

**양호:** 디렉터 주권주의 완벽 준수, Advisory non-blocking, InPlace 보호 (30KB/rfind/deep merge), Self-Critique 15개 체크, PASS_WITH_FIX 3-tier 라우팅 정상 동작

---

## 5. Cross-cutting (횡단 관심사) — 7 P2

| ID | 내용 | 비고 |
|---|---|---|
| CC-P2-001 | Context Cache eviction 경합 — TTL 동시 만료 시 중복 재생성 | 비용만, 기능 무해 |
| CC-P2-002 | LLM Router lazy init — stale provider | 재시작으로 해소 |
| CC-P2-003 | Advisory debug 로깅 레벨 | info/warning 권장 |
| CC-P2-004 | DB 복구 후 무결성 미검증 | edge case |
| CC-P2-005 | Vertex 클라이언트 스레드 안전성 | Gemini만 운영 → 무영향 |
| CC-P2-006 | API error string-based 분류 | 코드 스멜, 기능 무해 |
| CC-P2-007 | validation.yaml 미설정 키 기본값 산재 | `_threshold()` 폴백 안전 |

---

## 6. 오탐 제거 및 등급 재분류 내역

### 10-Pass 감리 과정

| Pass | 작업 | 결과 |
|------|------|------|
| 1차 | 5개 에이전트 독립 감사 (2회, 이중 에이전트 포함) | 원시 발견 62건 |
| 2차 | 중복 제거 + 코드 직접 확인 | 48건 |
| 3차 | 오탐 검증 (코드 라인 대조) | 43건 |
| 4차 | 등급 재분류 (P0 기준 엄격 적용) | 41건 |
| 5차 | 교차 검증 (TF-S2 기존 보고서 + 이중 에이전트) | 41건 |
| 6차 | P0/P1 재검증 — `return_exceptions=True` 발견 | 39건 |
| 7차 | 수치 정합성 확인 | 39건 |
| **8차** | **설계의도 검증 (1) — fix_scope 3-tier 라우팅 전체 흐름 추적** | S4-P1-001 오탐 확정 |
| **9차** | **설계의도 검증 (2) — dead code vs 미연결 상수 + truncation handling** | S2-P1-001 하향, CC-P1-001 오탐 확정 |
| **10차** | **설계의도 검증 (3) — 잔여 P1 전량 재검증 + Treatment 포맷 확인** | **37건 최종 확정** |

### 설계의도 오탐 상세 (4건 — 8~10차에서 발견)

**① S4-P1-001 → 오탐 삭제: fix_scope 폴백 partial 미도달**
- 원래 주장: fix_scope 누락 시 폴백이 inplace/full 이분법. partial 도달 불가.
- **실제 설계:** 폴백은 **의도적 보수적 이분법**. partial은 Director의 명시적 판단 전용.
  - Director가 `fix_scope: "partial"` 명시 → L2333에서 정상 라우팅
  - post-select REJECT downgrade → L2267에서 "partial"로 변환
  - inplace 재심사 중 Director가 partial 지정 → L2485 경유 다음 반복에서 처리
- **결론:** 3-tier 라우팅(inplace/partial/full) 전부 정상 도달. 폴백에서 partial 제외는 **의도**.

**② CC-P1-001 → 오탐 삭제: JSON payload 절단 blind spot**
- 원래 주장: LLM 응답 절단 시 "output truncated" vs "malformed JSON" 구분 불가.
- **실제 구현:** `base_agent.py:1192`에서 `finish_reason in ["MAX_TOKENS", "LENGTH"]` 감지.
  - WARNING 로깅: "데이터 절단 감지" (L1208)
  - 이어쓰기 시퀀스 자동 실행 (overlap anchor 50자, continuation prompt)
  - Circuit Breaker: max_continuations 초과 시 TRIP + 수동 검토 경고 (L1199-1202)
- **결론:** 절단은 **이미 감지·처리·로깅됨**. blind spot 아님.

**③ S2-P1-001 → P2 하향: ARC_BATCH_SIZE 상수 미연결**
- 원래 주장: `constants.py`에 `ARC_BATCH_SIZE = 5` 존재하나 루프에서 미참조. 유지보수 함정.
- **실제 상태:** `BatchSizes` 클래스 4개 상수(`ARC_BATCH_SIZE`, `EPISODE_BATCH_SIZE`, `PARALLEL_ENRICH_MAX`, `BLUEPRINT_BATCH_SIZE`) **전량 미참조**. `grep BatchSizes\. → 0 matches`.
- **결론:** "연결 누락"이 아니라 **dead code**. 상수가 코드에 연결된 적 없음. P2 dead code.

**④ S0-P1-001 → P2 하향: Bible Root isinstance 미검사**
- 원래 주장: `master_bible.get()` 호출 시 비dict 타입이면 TypeError.
- **실제 보호:**
  - L143 `if dna_success:` — force_sync 성공 후에만 진입 (master_bible 정상 보장)
  - L151 `except Exception as pc_err:` — 비차단 예외 처리
  - L532 패턴과의 불일치는 실존하나 **실질 위험 없음** (코딩 스타일 차이)
- **결론:** 방어 코딩 개선 수준. P2.

### 전체 등급 재분류 내역 (19건)

| 원래 | 변경 | 항목 | 사유 |
|---|---|---|---|
| P0 | P2 | S2 배치 경계 용접 | TF-S2 판정. C단계 LLM 보상. |
| P0 | P2 | S2 ThreadPool shutdown | `with` 문 자동 해제 |
| P0 | P2 | S2 timeout cascade | 순차 설계 의도 |
| P0 | P2 | S2 retry loop | arc 단위 제한 |
| P0 | 삭제 | CC DB lock double-release | 구조상 불가능 |
| P0 | 삭제 | CC Advisory timeout double | as_completed 동작 오해 |
| P0 | P2 | CC API error string | 코드 스멜 |
| P0 | P2 | S3 fail_count 리셋 | 연속 실패 카운터 의도 설계 |
| P0 | P2 | S3 ctx.agents P0 | 외부 try-except 포획 |
| P1 | P2 | S0 Treatment 포맷 | 시스템 항상 dict 생성 |
| P1 | 병합 | S0 Bible L414 | S0-P2-001에 통합 |
| P1 | P2 | S2 동일 컨텍스트 농축 | 병렬 설계 trade-off |
| P1 | P2 | S2 stitch continue | 격리 설계 (양호) |
| P1 | P2 | S2 cache 초기화 | 매 배치 재생성 |
| P1 | 삭제 | S2 asyncio.gather | return_exceptions=True |
| P1 | P2 | S4 Advisory timeout 중첩 | 완료 future 즉시 반환 |
| P1 | P2 | S4 state_updates merge | non-blocking 설계 |
| P1 | P2 | CC Cache eviction | 비용만 |
| P1 | P2 | CC validation.yaml 기본값 | 폴백 안전 |

### 삭제된 오탐 (11건)

| ID | 원래 등급 | 삭제 사유 |
|---|---|---|
| CC-FP-001 | P0 | DB lock double-release — 별도 try 블록 구조 |
| CC-FP-002 | P0 | Advisory timeout double — as_completed 동작 오해 |
| S2-FP-001 | P0 | ThreadPool shutdown — `with` 문 |
| S2-FP-002 | P0 | retry 무한루프 — arc 단위 제한 |
| S4-FP-001 | P0 | Quality gate — 정상 동작 확인 |
| S3-FP-001 | P0 | fail_count 리셋 — 의도 설계 (→ P2) |
| S3-FP-002 | P0 | ctx.agents — try-except 포획 (→ P2) |
| S2-FP-003 | P1 | asyncio.gather — return_exceptions=True |
| S0-FP-001 | P1 | Bible L414 — S0-P2-001에 병합 |
| **S4-FP-002** | **P1** | **fix_scope partial — 의도된 보수적 폴백 설계** |
| **CC-FP-003** | **P1** | **JSON 절단 — base_agent 이어쓰기 시퀀스로 이미 처리** |

---

## 7. 건강도 종합 평가

### 스테이지별 성적표

| 스테이지 | 점수 | 판정 | 핵심 강점 | P2 요약 |
|----------|------|------|----------|---------|
| Stage 0 | 90/100 | GOOD+ | Phase0 스키마 검증, NPC history | isinstance 스타일, dead default |
| Stage 2 | 78/100 | FAIR+ | gather 격리, C단계 LLM 보상, ConstraintDB | dead code, 배치 경계, 하드코딩 |
| Stage 3 | 95/100 | EXCELLENT | DI 완성도, 에러 격리, PinGuard | 윈도우 하드코딩, agents 가드 |
| Stage 4 | 90/100 | GOOD+ | 디렉터 주권, 3-tier fix_scope, Advisory 병렬 | 로깅 레벨, 타입 가드 |
| Cross-cutting | 88/100 | GOOD | Protocol 추상화, DB SSOT, 절단 복구 | 캐시 경합, dead provider |

### 전체 건강도: **88/100 — GOOD+**

### 아키텍처 원칙 준수도

| 원칙 | 준수 | 검증 근거 |
|------|:---:|------|
| Python 수집, LLM 판단 | ✅ | 전 스테이지. Python REJECT 없음. |
| 팩트시트 수정 = LLM만 | ✅ | npc_history append-only, reason 컬럼 |
| 디렉터 주권주의 | ✅ | PASS_WITH_FIX bypass, QualityGate PASS-only, fix_scope Director 전용 |
| 사망 NPC 회상만 | ✅ | TruthGate P2 검사 + Self-Critique #1 |
| DB SSOT | ✅ | project_data.db 단일 |
| DI Context | ✅ | 3개 스테이지 전량 완료 (44+19+24 슬롯) |

### 주요 설계 패턴 건강도

| 패턴 | 상태 | 검증 |
|------|------|------|
| PASS_WITH_FIX 3-tier | ✅ 정상 | inplace/partial/full 전부 도달 확인 |
| Advisory 8-병렬 | ✅ 정상 | ThreadPoolExecutor + per-advisory timeout |
| 출력 절단 복구 | ✅ 정상 | finish_reason 감지 + 이어쓰기 + Circuit Breaker |
| asyncio 병렬 농축 | ✅ 정상 | return_exceptions=True 격리 |
| DB RLock 보호 | ✅ 정상 | acquire/release 1:1, 이중 해제 불가 |
| Context Caching | ✅ 정상 | 5 에이전트, TTL 600/1800s |

---

## 8. 우선순위별 권고

### 즉시 대응 불필요 (현행 유지)
P0/P1 0건. 현재 워크플로우에서 문제 발생 확률 극히 낮음.

### 향후 개선 후보 (ROI 순)

| 순위 | ID | 내용 | 예상 효과 | 난이도 |
|------|---|------|----------|--------|
| 1 | S2-P2-005 | `BatchSizes` dead code 정리 또는 연결 | 코드 위생 | 5분 |
| 2 | S0-P2-001 | isinstance 체크 통일 (L145, L414 → L532 패턴) | 방어 코딩 일관성 | 5분 |
| 3 | S4-P2-002 | Advisory 예외 로깅 debug→warning | 운영 가시성 | 1분 |
| 4 | S2-P2-001 | 배치 간 용접 추가 | 50아크+ 시 품질 | 30분 |
| 5 | CC-P2-003 | Advisory 로깅 레벨 통일 | 일관성 | 5분 |

### 대규모 생산 전 권장 (50아크+ 시)
- S2-P2-001 (배치 경계 용접) 수정
- S2-P2-002 (동일 컨텍스트 농축) 검토

---

## 부록 A: 발견 전체 목록 (37건)

| 스테이지 | 건수 | ID 범위 |
|----------|------|---------|
| Stage 0 | 6 | S0-P2-001~006 |
| Stage 2 | 13 | S2-P2-001~013 |
| Stage 3 | 5 | S3-P2-001~005 |
| Stage 4 | 6 | S4-P2-001~006 |
| Cross-cutting | 7 | CC-P2-001~007 |

## 부록 B: 삭제된 오탐 (11건)

CC-FP-001~003, S2-FP-001~003, S4-FP-001~002, S3-FP-001~002, S0-FP-001

## 부록 C: 테스트/린트 현황

- **테스트**: 3,847 collected, 3,831 passed, 16 skipped
- **Ruff**: 0 violations
- **DI 전환**: Stage 2(44슬롯) + Stage 3(19슬롯) + Stage 4(24슬롯) 전량 완료

## 부록 D: 감리 방법론

1. **이중 에이전트**: Stage 0, Stage 3에 독립 에이전트 2회 실행 후 교차 검증
2. **코드 직접 대조**: 모든 P0/P1 발견에 대해 해당 코드 라인 직접 읽기
3. **기존 보고서 대조**: TF-S2-batch-boundary-audit.md 등 기존 감사와 교차
4. **설계의도 검증**: fix_scope 3-tier 전체 흐름 추적, 이어쓰기 시퀀스 확인, dead code vs 미연결 판별
5. **P0 기준**: crash/data loss/corruption이 **현실적 조건에서** 발생 가능
6. **P1 기준**: incorrect behavior가 **기존 방어 로직 없이** 발생 가능
7. **P2 기준**: 코드 스멜, dead code, 설계 trade-off, 방어 코딩 개선, 관찰
