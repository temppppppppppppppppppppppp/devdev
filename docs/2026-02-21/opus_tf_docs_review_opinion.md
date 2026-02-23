# Opus TF 문서 현황 의견서 (2026-02-21)

> **원안**: `codex_opus_document_overview.md` (17개 문서 분류)
> **Gemini 3.1 Pro 의견**: `codex_docs_update_recommendations.md` (4개 문서 수정 권고)
> **본 문서**: Opus TF 독립 의견 — 전 문서 실행 가능성 평가 + Gemini 의견 교차 검증

---

## 1. Gemini 3.1 Pro 의견에 대한 교차 검증

### 1-1. `codex_canon_os_v2_plan.md` — Gemini: "수정 필요 (Minor)"

**Opus TF 판정: 동의하되 범위 축소**

Gemini는 "Stage 0/1의 직접 `input()` 블로킹 리스크"를 근거로 비동기 추상화 조항 추가를 권고했다. 그러나:

- Stage 0/1의 `input()`은 **동기 함수 내부**에 있어 event loop 블로킹 문제가 아님 (일반 CLI 호출)
- 실제 async 블로킹 버그는 **Stage 2 전용**이었고, 이미 `e9065a8`에서 `asyncio.to_thread()` 래핑으로 수정 완료
- Canon OS v2 기획안 자체가 **미착수 상태**이므로, 문서 패치보다 착수 여부 결정이 선행

**권고**: 문서 패치 불요. 착수 시 async 패턴을 설계 원칙에 자연 반영하면 충분.

---

### 1-2. `codex_stage_canon_memory_plan.md` — Gemini: "수정 필요 (Major)"

**Opus TF 판정: 반대 — 근거 사실 오류**

Gemini는 "Stage 3 `_entity_cache_arc_idx`에서 Stale Cache 사용 위험(RISK-01) 발견"을 근거로 Context Compaction Guard에 강제 무효화 조항 추가를 권고했다.

그러나 **코드 검증 결과 이 리스크는 이미 해소**:
- `stage3_orchestrator.py` L366: 추출 실패 시 `self._entity_cache_arc_idx = -1`로 강제 리셋
- 다음 동일 arc_idx 호출 시 `L338: if self._entity_cache_arc_idx != arc_idx` → True → 재추출
- Sweep43에서 이미 수정된 사항 (`[Sweep43] 실패 시 arc_idx 캐싱 제거` 주석 존재)

**권고**: 문서 패치 불요. Gemini가 참조한 리스크는 오탐.

---

### 1-3. `codex_patch_retry_extension_plan.md` — Gemini: "수정 필요 (Critical)"

**Opus TF 판정: 부분 동의 — 다만 긴급도 하향**

Gemini는 "패치 재시도 루프 내 동기 `input()`이 시스템을 프리징시킨다"며 Critical 경고문 추가를 권고했다.

- 동기 `input()` 블로킹은 **`e9065a8`에서 수정 완료** — 해당 경고의 근거가 소멸
- 다만 기획안 자체의 **라인 번호 참조가 전면 실효** (R4/B-1/R5/Sweep 등 200건+ 수정으로 파일 구조 대폭 변경)
- `patch_arc_with_feedback()` 시그니처 미스매치 (`adversarial_self_play` 파라미터 누락) 버그는 여전히 라이브

**권고**: 경고문 추가 불요 (근거 소멸). 단, 착수 전 라인 번호 전면 재매핑 필수.

---

### 1-4. `codex_resume_replay_idempotency_sweep100_plan.md` — Gemini: "수정 필요 (Minor)"

**Opus TF 판정: 동의**

"Lazy Init 객체의 Resume 시점 복원 검증" 항목 추가 권고는 타당. DI 전환(Stage 2/3/4 전량)이 완료되었으므로, 이 검증 항목은 즉시 실행 가능하며 의미 있음.

**권고**: Phase 2에 검증 항목 1건 추가 동의.

---

## 2. Gemini가 다루지 않은 13개 문서에 대한 Opus TF 평가

### 카테고리 A: 즉시 실행 가능 (선행 의존 없음)

| 우선순위 | 문서 | 사유 |
|----------|------|------|
| **1** | `codex_memory_roi_boost_plan.md` | 4개 Quick Win (거리 기반 랭킹, 키워드 폴백, 요약 정규화, config 상향). 선행 의존 없음. ROI 가장 높음. 단, 라인 번호 재매핑 필요 (B-1 분할로 실효) |
| **2** | `codex_observability_rca_sweep100_plan.md` | 기존 코드만 검증. E-1/E-2/3-Obs 완료 상태라 기초 품질 확보됨. 가장 안전한 sweep |
| **3** | `codex_prompt_budget_fidelity_sweep100_plan.md` | 기존 truncation 로직 검증. I-09 수정 확인 가능. Truncation audit (Doc 16)와 상호 보완 |
| **4** | `codex_resume_replay_idempotency_sweep100_plan.md` | D-2 NPC 롤백, DB-SSOT 병합 등 기존 인프라 검증 |

### 카테고리 B: 실행 가능하나 라인 번호 재매핑 선행 필요

| 문서 | 사유 |
|------|------|
| `codex_patch_retry_extension_plan.md` | 핵심 기능 확장이나 200건+ 수정으로 참조 라인 전면 실효. `adversarial_self_play` 시그니처 버그 라이브 |
| `opus_truncation_manual_audit_order_2026-02-20.md` | 미실행 상태. 출력 파일 미생성. Doc 10과 상호 보완 |
| `opus_tf_sweep4x10_execution_order_2026-02-20.md` | Sweep 1~12 비공식 선행. 기폐쇄 findings 제외 후 실행 가능 |

### 카테고리 C: 선행 의존 미충족 — 보류

| 문서 | 차단 사유 |
|------|----------|
| `codex_canon_os_v2_plan.md` | 대형 신규 시스템. `canon_fields.yaml`, `canon_facts/events` 테이블 미존재 |
| `codex_stage_canon_memory_plan.md` | Canon OS v2 부분 의존. 독립 실행 불가 |
| `codex_hybrid_retrieval_refactor_plan.md` | Memory ROI Quick Win (Doc 3) 선행 권장 |
| `codex_patch_retry_determinism_sweep100_plan.md` | Patch Retry Extension (Doc 5) 미구현 → sweep 대상 없음 |
| `codex_canon_field_integrity_sweep100_plan.md` | Canon OS v2 (Doc 1) 미구현 → sweep 대상 없음 |
| `codex_postpatch_sweep_expansion_plan.md` | 메타 계획. 하위 5개 sweep의 선행 조건 미충족 |

### 카테고리 D: 참조 문서 (실행 대상 아님)

| 문서 | 용도 |
|------|------|
| `codex_director_issues.md` | Director 리팩토링 백로그 (12건 미수정). `audit_manuscript()` God Method 354줄 잔존 |
| `codex_pydantic_abc_baseline_report_2026-02-20.md` | 측정 기준선. B-3 Protocol 완료 후에도 런타임 바인딩 미적용 상태 |
| `codex_major_agents_runtime_inventory_2026-02-20.md` | 에이전트 호출 체인 레퍼런스. 현행 정확 |
| `opus_tf_comprehensive_audit_2026-02-20.md` | R2~R4 마스터 감사 보고서. 55건 중 ~28건 수정, Tier 4 (C-08/C-12/C-13) 장기 보류 |

---

## 3. 종합 권고: 실행 로드맵

```
Phase 1 — Quick Win (선행 의존 없음, 즉시 착수)
  ├── Memory ROI Quick Win 4건 (codex_memory_roi_boost_plan.md)
  └── Observability RCA Sweep 100 (codex_observability_rca_sweep100_plan.md)

Phase 2 — 검증 Sweep (Phase 1과 병행 가능)
  ├── Prompt Budget Fidelity Sweep 100
  ├── Resume/Replay Idempotency Sweep 100
  └── Truncation Manual Audit

Phase 3 — 기능 확장 (Phase 1 완료 후)
  ├── Patch Retry Extension (라인 재매핑 후)
  ├── Hybrid Retrieval Refactor (Memory ROI 후)
  └── 4x10 Sweep Program (기폐쇄 제외 후)

Phase 4 — 대형 신규 시스템 (Phase 3 완료 후)
  ├── Canon OS v2
  ├── Stage Canon Memory
  └── Canon Field Integrity Sweep 100

배경 작업 (우선순위 무관, 점진적 처리)
  └── Director Issues 12건 리팩토링
```

---

## 4. 핵심 발견: Gemini 의견과의 차이점 요약

| 항목 | Gemini 3.1 Pro | Opus TF | 근거 |
|------|---------------|---------|------|
| Canon OS v2 async 경고 | 추가 필요 (Minor) | **불요** | Stage 0/1 input()은 동기 함수 내부 — event loop 무관 |
| Canon Memory 캐시 무효화 | 추가 필요 (Major) | **불요 (오탐)** | Sweep43에서 이미 수정, 코드 검증 완료 |
| Patch Retry async 경고 | 추가 필요 (Critical) | **불요** | `e9065a8`에서 async input 수정 완료 |
| Resume/Replay Lazy Init | 추가 필요 (Minor) | **동의** | DI 전환 완료로 즉시 검증 가능 |
| 17개 문서 중 즉시 실행 가능 | 미평가 | **4개** | Doc 3, 9, 10, 11 |
| 선행 의존 차단으로 보류 | 미평가 | **6개** | Doc 1, 4, 6, 7, 8, 메타계획 |

---

## 5. 결론

Gemini 3.1 Pro의 의견은 4개 문서에 집중했으나, **3건은 이미 해소된 이슈를 근거로 삼아 실효성이 낮다**. 17개 문서 전체를 보면, 현 시점에서 가장 ROI 높은 작업은 **Memory ROI Quick Win + Observability Sweep**이며, Canon OS v2 같은 대형 시스템은 Phase 3~4 이후로 미루는 것이 합리적이다.

문서 패치에 시간을 쓰기보다, **즉시 실행 가능한 4개 문서부터 착수**하는 것을 권고한다.
