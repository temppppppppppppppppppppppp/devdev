# 기획 문서 유효성 검토 통합본

> 작성일: 2026-02-21 11:06 (rev.4 — Codex TF 3차 피드백 반영, 내부 서술 충돌 해소)
> 검토 대상: 7개 기획 문서
> 기준 커밋: `2a8a158` (2026-02-21, `feat(context): Gemini 컨텍스트 활용률 대폭 확대`)
> 테스트 기준: CI 최신 기준 (CLAUDE.md 기록: 2,114 passed + 68 xfailed)

---

## 1. 현재 상태 스냅샷

- **파이프라인**: Stage 0→2→4 정상 동작
- **디버깅**: 12차 스윕 + Opus TF 재감사(Phase 47, T1/T2 9건) 완료, 안정화 단계. 단, Truncation Manual Audit는 미완(§6 참조)
- **DI 전환**: Stage 2(**46**슬롯) + Stage 3(**20**슬롯) + Stage 4(**26**슬롯) 전량 완료
- **벡터 검색**: sqlite-vec 기반, multi-query + arc bonus + keyword fallback 구현
- **Director 분해**: God Object → 5개 전문 클래스 완료 (V64)
- **컨텍스트 예산**: 80,000자 중 ~38% 사용, 62% 여유

---

## 2. 즉시 실행 — SC-0

### P0-4: 검색 개수 상향 (미완)

- **출처**: `codex_memory_roi_boost_plan.md` §3 P0-4
- **상태**: 미완
- **작업**: `validation.yaml` L63-64 값 상향
  - `vector_max_results_s4`: 12 → 16
  - `vector_max_results_s2`: 8 → 12
- **리스크**: 낮음 (설정 플래그로 즉시 복구)
- **예상 공수**: 0.2일

### P0-3: 테스트 보강 (구현은 완료)

- **출처**: `codex_memory_roi_boost_plan.md` §3 P0-3
- **상태**: **코드 구현 완료** (`stage4_post_processor.py` L171-192에 4-slot 요약)
- **작업**: 엣지 케이스 테스트 추가 (빈 blueprint, entity 없음 등)
- **예상 공수**: 0.3일

---

## 3. 단기 실행 — Smart Context Retrieval (SC-1~6)

> 상세: `02211106_smart_context_retrieval_plan.md` 참조

| Phase | 작업 | 공수 | 관련 원본 문서 |
|-------|------|------|--------------|
| SC-1 | ContextAdvisor 코어 (하이브리드) | 1.5일 | Memory ROI D4, Hybrid Retrieval P4 |
| SC-2 | NPC-Aware Retrieval | 0.5일 | Canon OS D01, Stage Canon §Hard Fact |
| SC-3 | Stage 4 통합 | 1일 | Memory ROI D1, Hybrid Retrieval P4 |
| SC-4 | Stage 2 통합 | 0.5일 | — |
| SC-5 | Director 기존 경로 벡터 주입 | 0.5일 | Director Issues #4, Stage Canon §Runtime Flow |
| SC-6 | 관측성 + 피처 플래그 | 0.5일 | Memory ROI D2, Hybrid Retrieval P5 |

**총 예상**: ~5일

---

## 4. 중기 계획 — Hybrid Retrieval (SC 완료 후)

### 출처: `codex_hybrid_retrieval_refactor_plan.md`

| Phase | 작업 | 공수 | SC와의 관계 |
|-------|------|------|-----------|
| P0 | 베이스라인 고정 | 0.5일 | SC-6 관측성과 일부 겹침 |
| P1 | `retrieve_hybrid_context()` 추가 | 1일 | SC-3의 `_execute_retrieval_plan()`에서 1줄 전환 |
| P2 | Sparse FTS 축 도입 | 1~2일 | DB 스키마 변경 필요 |
| P3 | RRF Fusion 랭킹 | 1~2일 | 독립 |
| P4 | 호출부 전환 + 설정 플래그 | 1일 | SC에서 `smart_retrieval.*` 설정 섹션 준비 완료. `retrieval_mode` 키는 P4에서 추가 |
| P5 | 관측성/품질 게이트 | 1일 | SC-6 확장 |

**전제 조건**: SC 완료 후 지표 확인. dense-only 대비 recall 저하 없음 확인 후 진행.

**리스크**: DB 스키마 변경 (FTS 테이블), 마이그레이션 안정성. 설정 플래그로 점진 전환.

---

## 5. 장기 백로그

### 5-A. Canon OS v2 (18-Domain)

- **출처**: `codex_canon_os_v2_plan.md`
- **유효성**: **아이디어 유효, 구현은 불필요 (당분간)**
- **근거**:
  - NPC history (`npc_history` 테이블, Phase 3-5A) + ContextAdvisor NPC 쿼리로 D01(Character) 80% 커버
  - fact_ledger + continuity_validator로 D09(Event Ledger) 부분 커버
  - 18-Domain 전체 구현은 DB 스키마 대개편 + 8개 이상 통합 지점 수정 필요
  - 현재 안정화 단계에서 대규모 스키마 변경은 리스크 대비 ROI 낮음
- **유지할 아이디어**:
  - Alias/Normalization Layer (D04, §3.4): NPC/아이템 별칭 매칭 — 향후 entity_names 정밀도 개선 시 활용
  - Stage 계약 (§4): "Stage4만 Canon write" 원칙은 이미 시스템 원칙으로 작동 중
  - Context Compaction Guard (§9): 이미 DB-SSOT로 해결
- **폐기 사유**: Field Registry YAML 기반 시스템은 현재 DI + threshold_helper 패턴과 충돌. 과도한 추상화.

### 5-B. Stage Canon Memory

- **출처**: `codex_stage_canon_memory_plan.md`
- **유효성**: **부분 유효**
- **이미 구현된 부분**:
  - Director Sovereignty (§Core Policy): CLAUDE.md 대원칙 3
  - Warning-Only Python (§Validation Policy): 현재 pre_llm_validator 동작 방식
  - NPC history append-only (§Canon Events 유사): Phase 3-5A
  - Context Compaction Guard (§No-Stop): DB-SSOT (Phase DB-MERGE)
- **미구현 중 유효한 부분**:
  - **Stage4 canonical write gate** (§Rollout 1): `stage4_post_processor.py`에서 Director 승인 후에만 canon 커밋하는 명시적 게이트 — SC-5 Director 강화와 연계 가능
  - **Stale Cache 방어** (Gemini 3.1 Pro 권고): Director Override 시 Entity Registry 캐시 무효화 트리거 — 향후 과제
- **폐기 사유**: Hard Fact / Open Fact 분리 모델은 Canon OS v2와 중복. 별도 구현 불필요.

### 5-C. Patch Retry Extension

- **출처**: `codex_patch_retry_extension_plan.md`
- **유효성**: **부분 유효, 높은 리스크**
- **현재 상태**: Stage 2/3/4 모두 **최대 5회 재시도**이며, 패치는 **2회차 이후 점수/이전 산출물 조건 충족 시에만** 적용되고 실패 시 전면 재생성으로 폴백한다.
  - Stage 4: 5 interview rounds (`stage4_orchestrator.py` L533 `for interview_round in range(5)`), 각 라운드에서 score ≥ 50이면 패치, < 50이면 전면 재생성 (`stage4_interview_round.py` L127-134)
  - Stage 2: 5 attempts (`stage2_preflight.py` L180 `max_attempts = 5` + `stage2_orchestrator.py` L419 루프), score ≥ REWRITE(50)이면 패치 (`stage2_preflight.py` L481-485)
  - Stage 3: `max_retries=4` → 5 total attempts (`three_phase_blueprint_generator.py` L159), 동일 점수 조건
  - 패치 임계값: `PatchModeThresholds.REWRITE=50`, `PATCH=80` (`constants.py` L535-539)
- **유효한 부분**:
  - `adversarial_self_play` 파라미터 버그 (§2.6): `patch_arc_with_feedback` 시그니처 누락 — **독립 버그픽스로 처리 가능**
  - Stage 2 Director 주입 (§2.5): 패치 내부에 Director 판정 추가 — 현재 Python 단독 검증
- **보류 사유**:
  - **Event Loop Freezing 리스크** (§2.7, Gemini 3.1 Pro 권고): 동기식 `input()` → `aioconsole.ainput()` 전환 미완
  - **Stage 2 LLM 호출 40x 증가** (§2.7): 재시도 루프 중첩 시 최악 120회 → 안전장치 필요
  - 현재 패스율이 안정적이며 기존 재시도 체계가 작동 중이므로, 패치 재시도 확장은 패스율 문제 발생 시 재검토.

### 5-D. Director Issues

- **출처**: `codex_director_issues.md`
- **유효성**: **이슈 유효, 즉시 수정 불필요**

| # | 심각도 | 이슈 | 현재 상태 | 조치 |
|---|--------|------|----------|------|
| 1 | Critical | `audit_manuscript()` 354줄 God Method | 미수정 | **장기 백로그** — 작동 중, 분할 시 고비용 |
| 2 | Medium | `assess_character_logic()` 인라인 프롬프트 50줄 | 미수정 | SC 후 프롬프트 YAML 이관 가능 |
| 3 | Medium | `validate_entity_consistency()` 인라인 프롬프트 44줄 | 미수정 | 동상 |
| 4 | Medium | 충돌 검사 3개 메서드 중복 로직 | 미수정 | `_classify_conflict_result()` 헬퍼 추출 — SC-5 작업 시 같이 처리 |
| 5 | Medium | Ensemble/Quick Judge 인라인 프롬프트 | 미수정 | 프롬프트 YAML 이관 가능 |
| 6 | Medium | `concurrent.futures` 함수 내부 import | 미수정 | **사소** — 성능 영향 미미 |
| 7 | Medium | 프롬프트 이중 re-export | 미수정 | 레거시 — 기능 무해 |
| 8-12 | Minor | re import, safe_int 중복, 매직 넘버, stub, thin wrapper | 미수정 | 개별 사소한 건 |

**SC-5 작업 시 함께 처리할 건**: #4 (`_classify_conflict_result()` 헬퍼), #8 (`import re` 상단 이동)

---

## 6. 감사 지시서 확인

### Opus Truncation Manual Audit

- **출처**: `opus_truncation_manual_audit_order_2026-02-20.md`
- **성격**: 실행 지시서 (코드 계획이 아님)
- **산출물**: `docs/opus_truncation_manual_audit_findings_2026-02-20.md`
- **상태**: 산출물 파일 미발견 — **미완료 가능성**
- **연관**: Opus TF 재감사 (Phase 47)에서 T1/T2 9건 수정 완료. 이 감사는 "선절삭/샘플 축소" 관점의 별도 감사.
- **조치**: 필요시 다음 Opus 세션에서 실행. SC-6 BudgetTracker가 향후 절삭 지점 자동 추적하므로 긴급성 낮음.

---

## 7. 원본 문서 대조표

| 원본 문서 | 총 항목 수 | 완료 | 흡수 (SC) | 유효 (백로그) | 폐기/보류 |
|----------|-----------|------|----------|-------------|----------|
| **codex_memory_roi_boost_plan.md** | P0-1~4 + D1~D5 + B1~B7 = 16 | P0-1,2,3 (3) | P0-4, D1,D2,D4 (4) | D3,D5, B1~B7 (9) | — |
| **codex_hybrid_retrieval_refactor_plan.md** | P0~P5 = 6 | — | P4,P5 일부 (2) | P0~P3 (4) | — |
| **codex_canon_os_v2_plan.md** | 13항목 체크리스트 + 4 Phase | — | — | Alias Layer (1) | 나머지 12+4 (16) |
| **codex_stage_canon_memory_plan.md** | 5 Rollout + 3 Core Policy = 8 | Core Policy 3 (3) | — | Write Gate, Stale Cache (2) | 나머지 3 |
| **codex_patch_retry_extension_plan.md** | Stage 2/3/4 + 상수 + 테스트 = 10 | — | — | adversarial 버그픽스 (1) | 나머지 9 |
| **opus_truncation_manual_audit_order_2026-02-20.md** | 감사 지시 1건 | — | — | 미완 시 실행 (1) | — |
| **codex_director_issues.md** | 12건 이슈 | — | SC-5에서 #4,#8 (2) | #1-3,5 (4) | #6,7,9-12 (6) |

### 집계

| 분류 | 건수 |
|------|------|
| **이미 완료** | 6건 |
| **SC로 흡수** | 8건 |
| **유효 (백로그)** | 21건 |
| **폐기/보류** | 34건 |
| **합계** | 69건 |

---

## 8. 실행 우선순위 요약

```
[즉시]  SC-0: P0-4 검색 상향 + P0-3 테스트 보강 (0.5일)
  ↓
[단기]  SC-1~6: Smart Context Retrieval (5일)
  ↓
[중기]  Hybrid Retrieval P0~P5 (6~8일, SC 지표 확인 후)
  ↓
[장기]  Canon OS v2 Alias Layer / Director God Method 분할 / Patch Retry
```

---

## 9. 폐기 결정 근거

| 폐기 항목 | 근거 |
|----------|------|
| Canon OS 18-Domain Field Registry | DI + threshold_helper 패턴과 충돌. NPC history로 80% 커버. |
| Canon OS Phase 0~4 롤아웃 | 대규모 스키마 변경 대비 ROI 낮음. 안정화 단계에서 리스크 과다. |
| Stage Canon Hard/Open Fact 분리 | Canon OS v2와 중복. 별도 구현 불필요. |
| Patch Retry Stage 2 Director 주입 | Event Loop Freezing 미해결 + LLM 40x 비용 증가. 현재 패스율 안정. |
| Director #6,7,9-12 사소 이슈 | 기능 무해, 성능 영향 미미. 코드 변경 대비 가치 낮음. |
